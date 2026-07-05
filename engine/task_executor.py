"""任务执行器

TaskExecutor 自动从全局任务队列领取任务并分派给对应角色执行。
单批次最多执行 max_tasks 个任务，单任务失败自动重试一次，单任务异常不中断批次。
"""
from __future__ import annotations

from typing import Optional

from engine.task_queue import TaskQueue


class TaskExecutor:
    """任务执行器 - 自动从队列领取任务并分派给角色执行。"""

    # 角色名 → Agent 类名（与 engine/agents 包导出一致）
    ROLE_CLASSES = {
        "ceo": "CEO",
        "cto": "CTO",
        "coo": "COO",
        "architect": "Architect",
        "programmer": "Programmer",
        "tester": "Tester",
        "product_manager": "ProductManager",
    }

    def __init__(self, workspace=None, llm_client=None):
        from engine.workspace import WorkspaceManager
        from engine.llm_client import default_client
        self.workspace = workspace or WorkspaceManager()
        self.llm_client = llm_client or default_client
        self.queue = TaskQueue(self.workspace)

    # ------------------------------------------------------------------
    # Agent 实例化
    # ------------------------------------------------------------------
    def _make_agent(self, role: str):
        """按角色名实例化对应 Agent，复用传入的 workspace 与 llm_client。"""
        from engine.agents import (
            CEO, CTO, COO, Architect, Programmer, Tester, ProductManager,
        )
        cls_map = {
            "CEO": CEO,
            "CTO": CTO,
            "COO": COO,
            "Architect": Architect,
            "Programmer": Programmer,
            "Tester": Tester,
            "ProductManager": ProductManager,
        }
        cls = cls_map[self.ROLE_CLASSES[role]]
        return cls(self.workspace, self.llm_client)

    # ------------------------------------------------------------------
    # 失败处理
    # ------------------------------------------------------------------
    def _handle_task_failure(self, agent, task: dict, reason: str) -> str:
        """处理任务执行失败。

        - 首次失败（retry_count==0）：状态重置为 pending，retry_count 置 1，等待下次认领。
        - 再次失败：调用 report_failed 终态标记。

        Returns:
            ``"retry"``（已重新入队待重试）或 ``"failed"``（终态失败）。
        """
        retry_count = task.get("retry_count", 0) or 0
        if retry_count == 0:
            self.queue.update_status(task["id"], "pending", retry_count=1)
            return "retry"
        try:
            agent.report_failed(task["id"], reason)
        except Exception as e:
            # report_failed 自身失败不掩盖原始错误原因，仅记录
            print(f"[task_executor] report_failed 也失败：{e}")
        return "failed"

    # ------------------------------------------------------------------
    # 批次执行
    # ------------------------------------------------------------------
    def run_batch(self, max_tasks: int = 5) -> dict:
        """执行一批任务，最多 max_tasks 个。

        流程：
            1. 循环最多 max_tasks 次有效执行
            2. 每轮遍历 7 个角色，每个角色尝试 claim_task()
            3. 认领成功则状态改 in_progress，实例化 Agent 调用 execute_task
            4. 成功 → report_done；失败 → 首次重置 pending+retry_count，再次 report_failed
            5. 单任务 try/except 不中断批次
            6. 一轮全角色均未认领到任务则提前结束

        Returns:
            ``{success: int, failed: int, skipped: int, details: [...]}``
        """
        success = failed = skipped = 0
        executed = 0
        details = []
        # 复用 Agent 实例，避免重复加载配置
        agent_cache: dict = {}

        while executed < max_tasks:
            progress = False
            for role in self.ROLE_CLASSES:
                if executed >= max_tasks:
                    break

                # 1. 实例化 Agent（缓存）并认领任务
                try:
                    if role not in agent_cache:
                        agent_cache[role] = self._make_agent(role)
                    agent = agent_cache[role]
                    task = agent.claim_task()
                except Exception as e:
                    details.append({
                        "role": role, "status": "skip",
                        "error": f"认领阶段异常：{e}",
                    })
                    continue

                if not task:
                    continue

                progress = True
                executed += 1

                # 2. 标记 in_progress
                try:
                    self.queue.update_status(task["id"], "in_progress")
                except Exception as e:
                    details.append({
                        "role": role, "task_id": task.get("id"), "status": "skip",
                        "error": f"标记 in_progress 失败：{e}",
                    })
                    skipped += 1
                    continue

                # 3. 执行任务（独立 try/except，单任务失败不中断批次）
                try:
                    result = agent.execute_task(task)
                    if isinstance(result, dict) and result.get("status") == "done":
                        warning = ""
                        try:
                            agent.report_done(task["id"], result.get("result_path", ""))
                        except Exception as rd_err:
                            # 任务确实完成但持久化失败，仍计为成功并记录告警
                            warning = f"report_done 持久化失败：{rd_err}"
                        # 任务完成后发布 task.done.<type> 消息到共享消息池。
                        # agent.publish 内部已 try/except 兜底，失败不阻塞主流程。
                        try:
                            agent.publish(
                                f"task.done.{task.get('type', 'unknown')}",
                                {
                                    "task_id": task["id"],
                                    "result_path": result.get("result_path", ""),
                                },
                            )
                        except Exception as pub_err:  # noqa: BLE001 - publish 失败不阻塞
                            warning = (warning + "; " if warning else "") + \
                                f"publish task.done 失败：{pub_err}"
                        # 任务完成后触发钩子：自动创建下一阶段任务、恢复被阻塞任务。
                        # 失败任务（report_failed 分支）不触发后续。
                        try:
                            self.queue.on_task_done(task["id"])
                        except Exception as otd_err:  # noqa: BLE001 - 钩子失败不掩盖完成
                            warning = (warning + "; " if warning else "") + \
                                f"on_task_done 钩子失败：{otd_err}"
                        success += 1
                        details.append({
                            "role": role, "task_id": task.get("id"), "status": "done",
                            "result_path": result.get("result_path", ""), "warning": warning,
                        })
                    else:
                        err = (result.get("error_reason") if isinstance(result, dict) else None) \
                            or "execute_task 未返回 done 状态"
                        outcome = self._handle_task_failure(agent, task, err)
                        if outcome == "retry":
                            skipped += 1
                            # 任务重试发布 task.retrying 消息，retry_count 固定为 1
                            try:
                                agent.publish(
                                    "task.retrying",
                                    {"task_id": task["id"], "retry_count": 1},
                                )
                            except Exception as pub_err:  # noqa: BLE001 - publish 失败不阻塞
                                print(f"[task_executor] publish task.retrying 失败：{pub_err}")
                        else:
                            failed += 1
                            # 任务终态失败发布 task.failed 消息
                            try:
                                agent.publish(
                                    "task.failed",
                                    {"task_id": task["id"], "reason": err},
                                )
                            except Exception as pub_err:  # noqa: BLE001 - publish 失败不阻塞
                                print(f"[task_executor] publish task.failed 失败：{pub_err}")
                        details.append({
                            "role": role, "task_id": task.get("id"),
                            "status": outcome, "error": err,
                        })
                except Exception as e:
                    outcome = self._handle_task_failure(agent, task, str(e))
                    if outcome == "retry":
                        skipped += 1
                        # 异常分支重试也发布 task.retrying 消息
                        try:
                            agent.publish(
                                "task.retrying",
                                {"task_id": task["id"], "retry_count": 1},
                            )
                        except Exception as pub_err:  # noqa: BLE001 - publish 失败不阻塞
                            print(f"[task_executor] publish task.retrying 失败：{pub_err}")
                    else:
                        failed += 1
                        # 异常分支终态失败也发布 task.failed 消息
                        try:
                            agent.publish(
                                "task.failed",
                                {"task_id": task["id"], "reason": str(e)},
                            )
                        except Exception as pub_err:  # noqa: BLE001 - publish 失败不阻塞
                            print(f"[task_executor] publish task.failed 失败：{pub_err}")
                    details.append({
                        "role": role, "task_id": task.get("id"),
                        "status": outcome, "error": str(e),
                    })

            # 一轮全角色均未认领到任务，队列已无可执行项，提前结束
            if not progress:
                break

        return {
            "success": success,
            "failed": failed,
            "skipped": skipped,
            "details": details,
        }
