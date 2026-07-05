"""智能体基类

所有虚拟员工智能体（CEO / CTO / COO / Architect / Programmer / Tester / ProductManager）
继承自 BaseAgent，复用配置加载、提示词构造、LLM 调用、产出落盘、职责边界校验等通用能力。
子类通常只需覆盖 build_prompt 或新增特定业务方法即可。
"""
from __future__ import annotations

from datetime import datetime
from typing import Optional

from engine.workspace import WorkspaceManager
from engine.llm_client import LLMClient, default_client


class BaseAgent:
    """所有虚拟员工智能体的基类。"""

    def __init__(self, role: str, workspace: WorkspaceManager, llm_client: LLMClient = None):
        """
        Args:
            role: 角色标识，如 'ceo'、'cto'、'programmer' 等。
            workspace: 工作区管理器实例。
            llm_client: LLM 客户端，默认使用全局 default_client。
        """
        self.role = role
        self.workspace = workspace
        self.llm_client = llm_client or default_client
        # 加载本角色配置（含 name / role / persona / responsibilities / tools / system_prompt）
        self.config = self.load_config()
        # 注入共享消息池（延迟导入避免循环依赖）
        from engine.message_pool import MessagePool
        self.message_pool = MessagePool(workspace)

    # ------------------------------------------------------------------
    # 配置加载
    # ------------------------------------------------------------------
    def load_config(self) -> dict:
        """从工作区 config/employees.yaml 读取本角色配置。

        根据 self.role 在 employees 列表中匹配对应配置项。

        Returns:
            包含 name / role / persona / responsibilities / tools / system_prompt
            的配置字典；若未找到匹配角色，返回仅含 role 的最小字典。
        """
        data = self.workspace.read_yaml(self.workspace.employees_config_path)
        if not data:
            return {"role": self.role}

        for entry in data.get("employees", []):
            if entry.get("role") == self.role:
                return entry

        return {"role": self.role}

    # ------------------------------------------------------------------
    # 提示词构造
    # ------------------------------------------------------------------
    def build_prompt(self, context: str = "") -> str:
        """构造系统提示词。

        结构：persona → responsibilities → 可用工具说明 → 本季度战略方向 → 约束 → context。

        若 company/strategy/ 下存在最新战略文档，则注入其「下季度战略方向」摘要，
        作为全员本季度决策上下文；不存在时跳过，不影响现有行为。

        Args:
            context: 上下文信息（如当前任务、相关文档摘要），追加到提示词末尾。

        Returns:
            完整的 system prompt 字符串。
        """
        persona = self.config.get("persona", "")
        responsibilities = self.config.get("responsibilities", []) or []
        tools = self.config.get("tools", []) or []

        sections = []

        if persona:
            sections.append(f"【角色人格】\n{persona}")

        if responsibilities:
            resp_text = "\n".join(f"- {r}" for r in responsibilities)
            sections.append(f"【职责范围】\n{resp_text}")

        if tools:
            tools_text = "\n".join(f"- {t}" for t in tools)
            sections.append(f"【可用工具】\n{tools_text}")

        # 注入本季度战略方向（若存在最新战略文档）
        strategy_summary = self._load_strategy_summary()
        if strategy_summary:
            sections.append(f"【本季度战略方向】\n{strategy_summary}")

        sections.append(
            "【约束】\n"
            "- 严格遵循上述职责范围，超出职责的任务应建议转交对应角色。\n"
            "- 输出需结构化、可执行，避免空泛套话。\n"
            "- 涉及决策/支出/立项时，必须给出明确理由。"
        )

        if context:
            sections.append(f"【上下文】\n{context}")

        return "\n\n".join(sections)

    def _load_strategy_summary(self) -> str:
        """读取最新的季度战略文档，提取「下季度战略方向」作为摘要。

        扫描 company/strategy/ 目录下 YYYY-Qn.md 文件，按文件名倒序取最新季度，
        提取其中「下季度战略方向」章节内容注入全员 prompt。

        Returns:
            战略方向摘要文本；文档不存在或无对应章节时返回空字符串（跳过注入）。
        """
        strategy_dir = self.workspace.root_dir / "strategy"
        if not strategy_dir.exists():
            return ""
        # 按 YYYY-Qn 文件名排序，倒序后第一个即最新季度
        md_files = sorted(
            strategy_dir.glob("*-Q[1-4].md"),
            key=lambda p: p.name,
            reverse=True,
        )
        if not md_files:
            return ""
        content = self.workspace.read_text(md_files[0])
        if not content:
            return ""
        # 提取「下季度战略方向」章节（到下一个二级标题为止）
        section = self._extract_markdown_section(content, "下季度战略方向")
        if section:
            return section
        # 兜底：章节未匹配时返回文档前 2000 字符，保证至少有上下文
        return content[:2000]

    def _extract_markdown_section(self, content: str, title: str) -> str:
        """从 markdown 文档中提取指定二级标题（## title）下的内容。

        提取范围从该标题下一行到下一个二级标题（## ）之前。

        Args:
            content: markdown 文档全文。
            title: 二级标题文本（不含 ## 前缀）。

        Returns:
            章节正文文本；未找到时返回空字符串。
        """
        lines = content.splitlines()
        target = f"## {title}"
        start = None
        for i, line in enumerate(lines):
            if line.strip().startswith(target):
                start = i + 1
                break
        if start is None:
            return ""
        end = len(lines)
        for j in range(start, len(lines)):
            if lines[j].strip().startswith("## "):
                end = j
                break
        return "\n".join(lines[start:end]).strip()

    # ------------------------------------------------------------------
    # LLM 调用
    # ------------------------------------------------------------------
    def call_llm(self, user_message: str, context: str = "") -> str:
        """调用 LLM 完成单轮对话。

        在调用前启发式校验职责边界：若任务疑似超出本角色职责，
        不直接拒绝（启发式判断可能误判），而在响应末尾附加转交建议警告。

        Args:
            user_message: 用户消息（任务描述）。
            context: 上下文信息，会传入 build_prompt。

        Returns:
            LLM 响应文本；若疑似越界则附加职责警告。
        """
        system_prompt = self.build_prompt(context)
        response = self.llm_client.chat(system_prompt, user_message)

        # 职责边界启发式校验：不直接拒绝，仅在输出中附加警告
        if not self.check_responsibility(user_message):
            warning = f"\n\n注意：此任务可能超出 {self.role} 职责范围，建议转交对应角色。"
            response = response + warning

        return response

    # ------------------------------------------------------------------
    # 产出落盘
    # ------------------------------------------------------------------
    def save_output(self, content: str, category: str, filename: str = None) -> str:
        """将智能体输出保存到工作区对应目录。

        Args:
            content: 输出内容。
            category: 产出类别，决定保存位置：
                'decision' → knowledge/decisions/
                'research' → knowledge/market-research/
                'report'   → reports/
                'meeting'  → meetings/
                'project'  → projects/
            filename: 文件名（不含路径）。为空则自动生成：时间戳 + 角色名.md。

        Returns:
            保存文件的绝对路径。
        """
        category_dirs = {
            "decision": self.workspace.decisions_dir,
            "research": self.workspace.market_research_dir,
            "report": self.workspace.reports_dir,
            "meeting": self.workspace.meetings_dir,
            "project": self.workspace.projects_dir,
        }
        target_dir = category_dirs.get(category, self.workspace.reports_dir)

        if not filename:
            timestamp = datetime.now().strftime("%Y%m%d-%H%M%S")
            filename = f"{timestamp}-{self.role}.md"

        target_path = target_dir / filename
        self.workspace.write_text(target_path, content)
        return str(target_path.resolve())

    # ------------------------------------------------------------------
    # 职责边界校验
    # ------------------------------------------------------------------
    def check_responsibility(self, task_description: str) -> bool:
        """启发式职责匹配：检查任务描述是否包含职责关键词。

        将 self.config['responsibilities'] 中的每一项作为关键词，
        检查是否出现在 task_description 中（忽略大小写）。

        Args:
            task_description: 任务描述文本。

        Returns:
            命中任意职责关键词返回 True；全部未命中返回 False，并打印转交建议。
            若未定义职责，默认放行返回 True。
        """
        responsibilities = self.config.get("responsibilities", []) or []
        if not responsibilities:
            # 未定义职责时默认放行
            return True

        task_lower = task_description.lower()
        for resp in responsibilities:
            if resp and resp.lower() in task_lower:
                return True

        print(f"[{self.role}] 任务「{task_description}」疑似超出职责范围，建议转交对应角色。")
        return False

    # ------------------------------------------------------------------
    # 任务队列协作（自主认领 / 执行 / 汇报 / 转交）
    # ------------------------------------------------------------------
    def claim_task(self) -> Optional[dict]:
        """从全局任务队列认领一个本角色可执行的任务。

        委托给 TaskQueue.claim_task(self.role)，返回任务 dict 或 None。
        """
        from engine.task_queue import TaskQueue
        queue = TaskQueue(self.workspace)
        return queue.claim_task(self.role)

    def execute_task(self, task: dict) -> dict:
        """执行认领的任务。子类必须实现。

        Returns:
            ``{status: "done"|"failed", result_path: str, error_reason: str}``
        """
        raise NotImplementedError(f"{self.role} 未实现 execute_task")

    def execute_by_sop(self, task: dict, sop: Optional[dict]) -> dict:
        """按 SOP 标准化执行任务（SubTask 1.5）。

        SOP 标准化执行流程（参考 MetaGPT SOP 模式）：
            1. ``sop`` 为 None：直接调用 ``execute_task``，标记 ``sop_compliance="degraded"``，
               并 publish ``sop.missing`` 消息到共享消息池供健康监控统计
            2. ``sop`` 不为 None：
                a. 用 ``SOPLoader.validate_inputs(sop, task_context)`` 校验前置产物，
                   不通过则 ``report_failed`` 并返回 ``{status: "failed",
                   error_reason: "missing inputs: ..."}``
                b. 调用 ``self.execute_task(task)``（子类实现，完成实际执行）
                c. 用 ``SOPLoader.check_acceptance(sop, output)`` 自检产出，
                   不通过则 ``report_failed`` 并返回 ``{status: "failed",
                   error_reason: "acceptance failed: ..."}``
                d. 通过则返回 ``{status: "done", result_path: ...,
                   sop_compliance: "passed"}``

        Args:
            task: 任务字典（含 id / title / description / type 等字段）。
            sop: ``SOPLoader.load`` 返回的结构化 SOP 字典；为 None 表示该任务无 SOP 约束。

        Returns:
            执行结果字典：
                - 成功: ``{status: "done", result_path: str, sop_compliance: "passed"}``
                - 失败: ``{status: "failed", result_path: str, error_reason: str,
                  sop_compliance: "failed"}``
                - SOP 缺失降级: ``{status: <execute_task 返回>,
                  sop_compliance: "degraded"}``
        """
        task_id = task.get("id", "") if isinstance(task, dict) else ""

        # 1. SOP 为 None：降级到 execute_task，标记 degraded，publish sop.missing
        if sop is None:
            try:
                self.publish(
                    "sop.missing",
                    {
                        "task_id": task_id,
                        "role": self.role,
                        "reason": "task has no sop_id or sop file not found",
                    },
                )
            except Exception as pub_err:  # noqa: BLE001 - publish 失败不阻塞
                print(f"[{self.role}] publish sop.missing 失败: {pub_err}")

            result = self.execute_task(task)
            # 在 execute_task 返回值基础上追加 sop_compliance 标记
            if isinstance(result, dict):
                result.setdefault("sop_compliance", "degraded")
            return result

        # 2. SOP 不为 None：先校验 inputs
        try:
            from engine.sop_loader import SOPLoader
            loader = SOPLoader(self.workspace)
            # task_context 由 task 关键字段构造，便于 validate_inputs 匹配
            task_context = {
                "task_id": task_id,
                "title": task.get("title", "") if isinstance(task, dict) else "",
                "description": task.get("description", "") if isinstance(task, dict) else "",
                "type": task.get("type", "") if isinstance(task, dict) else "",
                "result_path": task.get("result_path", "") if isinstance(task, dict) else "",
            }
            # 合并 task.metadata（如有）作为额外上下文
            if isinstance(task, dict) and isinstance(task.get("metadata"), dict):
                task_context.update(task["metadata"])
            passed, missing = loader.validate_inputs(sop, task_context)
            if not passed:
                err_msg = f"missing inputs: {', '.join(missing)}"
                if task_id:
                    try:
                        self.report_failed(task_id, err_msg)
                    except Exception as rf_err:  # noqa: BLE001
                        print(f"[{self.role}] report_failed 失败: {rf_err}")
                # publish task.blocked 消息（参考 SOP 违规拦截场景）
                try:
                    self.publish(
                        "task.blocked",
                        {
                            "task_id": task_id,
                            "role": self.role,
                            "reason": "missing_inputs",
                            "missing": missing,
                        },
                    )
                except Exception as pub_err:  # noqa: BLE001
                    print(f"[{self.role}] publish task.blocked 失败: {pub_err}")
                return {
                    "status": "failed",
                    "result_path": "",
                    "error_reason": err_msg,
                    "sop_compliance": "failed",
                }
        except Exception as e:  # noqa: BLE001 - SOP 校验失败降级到 execute_task
            print(f"[{self.role}] SOP validate_inputs 异常，降级执行: {e}")
            result = self.execute_task(task)
            if isinstance(result, dict):
                result.setdefault("sop_compliance", "degraded")
            return result

        # 3. 调用 execute_task 执行实际任务
        try:
            exec_result = self.execute_task(task)
        except Exception as e:  # noqa: BLE001 - execute_task 异常
            err_msg = f"execute_task 异常: {e}"
            if task_id:
                try:
                    self.report_failed(task_id, err_msg)
                except Exception:  # noqa: BLE001
                    pass
            return {
                "status": "failed",
                "result_path": "",
                "error_reason": err_msg,
                "sop_compliance": "failed",
            }

        # 4. 自检 acceptance_criteria
        try:
            # output 字典：以 execute_task 的 result_path 为关键产物标识
            output = {}
            if isinstance(exec_result, dict):
                output = dict(exec_result)
            output.setdefault("task_id", task_id)
            passed, failed_criteria = loader.check_acceptance(sop, output)
            if not passed:
                err_msg = f"acceptance failed: {', '.join(failed_criteria)}"
                if task_id:
                    try:
                        self.report_failed(task_id, err_msg)
                    except Exception:  # noqa: BLE001
                        pass
                # publish task.blocked 消息
                try:
                    self.publish(
                        "task.blocked",
                        {
                            "task_id": task_id,
                            "role": self.role,
                            "reason": "acceptance_failed",
                            "failed_criteria": failed_criteria,
                        },
                    )
                except Exception:  # noqa: BLE001
                    pass
                if isinstance(exec_result, dict):
                    exec_result["sop_compliance"] = "failed"
                    exec_result["error_reason"] = err_msg
                    exec_result["status"] = "failed"
                return exec_result if isinstance(exec_result, dict) else {
                    "status": "failed",
                    "result_path": "",
                    "error_reason": err_msg,
                    "sop_compliance": "failed",
                }
        except Exception as e:  # noqa: BLE001 - acceptance 校验异常不阻塞
            print(f"[{self.role}] SOP check_acceptance 异常: {e}")

        # 5. 全部通过
        if isinstance(exec_result, dict):
            exec_result["sop_compliance"] = "passed"
        return exec_result

    def report_done(self, task_id: str, result_path: str = "") -> None:
        """标记任务完成。

        在更新任务状态后，自动调用 KPITracker.record() 记录一次 KPI（按角色推断 metric）。
        为避免 execute_task 内部与 TaskExecutor 外部双重调用导致重复计数，
        仅在任务首次由非 done 状态变为 done 时记录 KPI。
        KPI 记录失败不影响任务完成（try/except 优雅降级）。
        """
        from engine.task_queue import TaskQueue
        queue = TaskQueue(self.workspace)
        # 先读取当前状态，判断是否已完成过（幂等防重复 KPI 计数）
        existing = queue.get_task(task_id)
        already_done = bool(existing and existing.get("status") == "done")
        queue.update_status(
            task_id,
            "done",
            result_path=result_path,
            completed_at=datetime.now().isoformat(timespec="seconds"),
        )
        if already_done:
            return
        # 自动记录 KPI（失败不影响任务完成）
        try:
            self._record_kpi_on_done()
        except Exception as e:  # noqa: BLE001 - KPI 失败不阻断主流程
            print(f"[{self.role}] KPI 记录失败：{e}")

    def _record_kpi_on_done(self) -> None:
        """任务完成时按角色记录对应 KPI。

        metric 映射：
            programmer  → weekly_delivery_count
            tester      → weekly_test_count
            architect   → weekly_design_docs
            product_manager → weekly_topics
            coo         → weekly_promo_count（未在 role_kpi.yaml 中则跳过）
            ceo/cto     → weekly_decision_count（未在 role_kpi.yaml 中则跳过）

        若推断出的 metric 未在 role_kpi.yaml 中为本角色定义，则跳过记录。
        """
        from engine.agents.role_kpi import KPITracker
        role_metric_map = {
            "programmer": "weekly_delivery_count",
            "tester": "weekly_test_count",
            "architect": "weekly_design_docs",
            "product_manager": "weekly_topics",
            "coo": "weekly_promo_count",
            "ceo": "weekly_decision_count",
            "cto": "weekly_decision_count",
        }
        metric = role_metric_map.get(self.role)
        if not metric:
            return
        tracker = KPITracker(self.workspace)
        # 仅当 metric 在本角色 KPI 配置中时才记录，否则跳过（如 coo/ceo/cto 的推断 metric）
        configured = {
            k.get("metric")
            for k in tracker._load_kpi_config()
            if k.get("role") == self.role
        }
        if metric not in configured:
            return
        tracker.record(self.role, metric, 1)

    def report_failed(self, task_id: str, reason: str) -> None:
        """标记任务失败。"""
        from engine.task_queue import TaskQueue
        queue = TaskQueue(self.workspace)
        queue.update_status(
            task_id,
            "failed",
            error_reason=reason,
            completed_at=datetime.now().isoformat(timespec="seconds"),
        )

    def request_handoff(self, task_id: str, to_role: str, reason: str) -> str:
        """跨角色转交：原任务标 blocked，创建新 decision 任务给目标角色。

        增强点：新任务 metadata 中记录 ``unblock_task_id=原任务id``，便于决策完成后
        通过 TaskQueue.unblock_tasks / on_task_done 自动恢复原任务为 pending。

        Args:
            task_id: 当前任务 id。
            to_role: 转交目标角色名。
            reason: 转交原因。

        Returns:
            新建 decision 任务的 id。
        """
        from engine.task_queue import TaskQueue
        queue = TaskQueue(self.workspace)
        queue.update_status(task_id, "blocked", block_reason=reason, blocked_for=to_role)
        new_task = queue.add_task(
            title=f"handoff from {self.role}",
            description=reason,
            type="decision",
            assignee=to_role,
            priority="P1",
            source=f"handoff_{self.role}",
            metadata={"unblock_task_id": task_id},
        )
        return new_task["id"]

    # ------------------------------------------------------------------
    # 共享消息池协作（publish / read_unread）
    # ------------------------------------------------------------------
    def publish(self, topic: str, payload: dict, to_role: Optional[str] = None) -> None:
        """向共享消息池发布一条消息。

        以本角色 ``self.role`` 作为 ``from_role``，调用 ``MessagePool.publish``
        持久化到 ``company/messages/message-pool-YYYY-MM-DD.jsonl``。

        publish 失败不应阻塞主流程，整体 try/except 兜底。

        Args:
            topic: 消息主题，如 ``task.done.code`` / ``decision.initiate``。
            payload: 消息负载字典。
            to_role: 接收方角色名；为空表示广播。
        """
        try:
            self.message_pool.publish(topic, payload, self.role, to_role)
        except Exception as e:  # noqa: BLE001 - publish 失败不阻塞主流程
            print(f"[{self.role}] publish 消息失败 topic={topic}: {e}")

    def read_unread(self, topic_filter: Optional[str] = None) -> list[dict]:
        """读取本角色在共享消息池中的未读消息。

        委托给 ``MessagePool.read_unread(self.role, topic_filter)``，命中后
        会自动把 ``self.role`` 加入消息的 ``read_by`` 列表并写回文件。

        Args:
            topic_filter: 主题前缀过滤（如 ``task.done.*``）；为空则不过滤。

        Returns:
            未读消息列表；读取失败时返回空列表（不抛异常）。
        """
        try:
            return self.message_pool.read_unread(self.role, topic_filter)
        except Exception as e:  # noqa: BLE001 - 读取失败不阻塞主流程
            print(f"[{self.role}] read_unread 消息失败: {e}")
            return []
