"""CTO 智能体 - 首席技术官

对技术方向负最终责任，偏好简单可维护的技术栈，反对过度工程。
"""
from __future__ import annotations

from typing import Any, Dict, List

from engine.agents.base import BaseAgent
from engine.workspace import WorkspaceManager
from engine.llm_client import LLMClient


class CTO(BaseAgent):
    """首席技术官：负责技术选型、架构方向、技术评审。"""

    def __init__(self, workspace: WorkspaceManager, llm_client: LLMClient = None):
        super().__init__("cto", workspace, llm_client)

    def review_tech_stack(self, options: list, context: str = "") -> dict:
        """技术选型评审，返回 {selected, reason, risks, raw_response}。

        从可维护性、招聘成本、生态成熟度、AI 自主开发可行性四个维度评估。
        """
        options_text = "\n".join(f"- 方案{i+1}: {opt}" for i, opt in enumerate(options))
        user_message = (
            f"请从可维护性、招聘成本、生态成熟度、AI 自主开发可行性四个维度，"
            f"评审以下技术选型方案并给出最终选择。\n"
            f"方案列表：\n{options_text}\n"
            f"补充上下文：{context or '无'}"
        )
        raw = self.call_llm(user_message, context="任务：技术选型与技术评审")
        # 启发式提取选中方案
        selected = None
        for i, _ in enumerate(options):
            if f"方案{i+1}" in raw:
                selected = options[i]
                break
        return {
            "selected": selected,
            "reason": raw,
            "risks": None,
            "raw_response": raw,
        }

    def set_tech_direction(self, context: str = "") -> str:
        """设定技术方向，输出到 decisions/ 目录，返回保存的文件路径。"""
        user_message = (
            f"请基于以下上下文设定 AutoCorp 近期技术方向，"
            f"包含技术选型决策、理由与风险点。\n上下文：{context or '通用 SaaS 产品开发'}"
        )
        raw = self.call_llm(user_message, context="任务：技术选型与架构方向")
        saved_path = self.save_output(
            f"# AutoCorp 技术方向\n\n{raw}",
            category="decision",
            filename="cto-tech-direction.md",
        )
        return saved_path

    # ------------------------------------------------------------------
    # 技术评审（execute_task 调用）
    # ------------------------------------------------------------------
    def tech_review(self, task: dict) -> str:
        """产出技术评审文档（markdown）。

        构造 LLM prompt（CTO 系统提示词 + 技术评审要求）；LLM 调用失败时降级为
        模板评审（含技术栈建议/架构风险/性能考量三节）。

        Returns:
            markdown 评审文档文本。
        """
        title = task.get("title", "技术评审事项") if isinstance(task, dict) else "技术评审事项"
        description = task.get("description", "") if isinstance(task, dict) else str(task)

        user_message = (
            f"请基于以下事项做技术评审，输出 markdown 文档，包含三节："
            f"技术栈建议、架构风险、性能考量。每节给出具体结论与建议。\n"
            f"事项标题：{title}\n"
            f"事项描述：{description}\n"
        )
        try:
            raw = self.call_llm(user_message, context="任务：技术选型与技术评审")
        except Exception as e:  # noqa: BLE001 - LLM 失败降级
            print(f"[cto] tech_review LLM 调用失败，降级为模板评审：{e}")
            raw = ""

        if raw and len(raw.strip()) > 80:
            return f"# 技术评审：{title}\n\n{raw}\n"

        # 降级：模板评审
        return self._build_tech_review_template(title, description)

    def _build_tech_review_template(self, title: str, description: str) -> str:
        """生成模板技术评审文档（LLM 降级时使用）。"""
        from datetime import datetime

        return (
            f"# 技术评审：{title}\n\n"
            f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}（降级模式：LLM 调用失败，模板生成）\n\n"
            f"## 评审事项\n{description or '（无描述）'}\n\n"
            f"## 技术栈建议\n"
            f"- 优先复用 AutoCorp 现有技术资产（Python / Click / 文件持久化）。\n"
            f"- 新依赖须有稳定版发布，禁止选用 beta/RC 版本。\n"
            f"- 偏好简单可维护方案，反对过度工程；能文件持久化则不引入数据库。\n"
            f"- 涉及外部 API 调用须封装抽象层并支持优雅降级。\n\n"
            f"## 架构风险\n"
            f"- 单点：核心模块需评估单点故障与降级路径。\n"
            f"- 耦合：模块间优先松耦合，避免循环依赖。\n"
            f"- 数据一致性：文件持久化需注意并发写风险，必要时加锁或单写者模式。\n"
            f"- 安全：密钥/钱包相关操作须走 .secrets/ 隔离与人工确认。\n\n"
            f"## 性能考量\n"
            f"- LLM 调用须限制 max_tokens 与重试次数，避免成本失控。\n"
            f"- 网络 IO 须设超时（建议 15s）与重试退避。\n"
            f"- 大文件读写采用流式或分批，避免内存峰值。\n"
            f"- 关键路径建议加缓存与指标埋点，便于后续优化。\n"
        )

    # ------------------------------------------------------------------
    # 任务执行
    # ------------------------------------------------------------------
    def execute_task(self, task: dict) -> dict:
        """执行 decision/design 类任务：产出技术评审文档并落盘。

        Returns:
            ``{status: "done"|"failed", result_path: str, error_reason: str}``
        """
        from engine.task_queue import TaskQueue

        task_id = task.get("id", "") if isinstance(task, dict) else ""
        try:
            queue = TaskQueue(self.workspace)
            queue.update_status(task_id, "in_progress")

            # 1. 产出技术评审文档
            doc = self.tech_review(task)

            # 2. 写入 company/reports/tech-review-<task_id>.md
            target_path = self.workspace.reports_dir / f"tech-review-{task_id}.md"
            self.workspace.write_text(target_path, doc)
            result_path = str(target_path.resolve())

            # 3. 汇报完成
            self.report_done(task_id, result_path)
            return {"status": "done", "result_path": result_path, "error_reason": ""}
        except Exception as e:  # noqa: BLE001 - 顶层兜底
            self.report_failed(task_id, str(e))
            return {"status": "failed", "result_path": "", "error_reason": str(e)}
