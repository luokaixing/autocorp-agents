"""Architect 智能体 - 架构师

为项目整体质量把关，从 PRD 出发做模块拆分、接口定义、技术规范。
"""
from __future__ import annotations

from typing import Any, Dict

from engine.agents.base import BaseAgent
from engine.workspace import WorkspaceManager
from engine.llm_client import LLMClient


class Architect(BaseAgent):
    """架构师：负责架构设计、模块拆分、接口定义、代码评审。"""

    def __init__(self, workspace: WorkspaceManager, llm_client: LLMClient = None):
        super().__init__("architect", workspace, llm_client)

    def design_architecture(self, prd: dict) -> dict:
        """架构设计，返回 {modules, interfaces, specs, raw_response}。

        将架构文档保存到 projects/<product>/architecture.md。
        """
        product_name = prd.get("title", "unnamed-product") if isinstance(prd, dict) else "unnamed-product"
        user_message = (
            f"请基于以下 PRD 进行架构设计，输出模块拆分清单、接口定义、技术规范。\n"
            f"PRD 内容：\n{prd}"
        )
        raw = self.call_llm(user_message, context="任务：架构设计与模块拆分")
        # 保存到 projects/<product>/architecture.md
        project_dir = self.workspace.projects_dir / product_name
        arch_path = project_dir / "architecture.md"
        self.workspace.write_text(
            arch_path,
            f"# {product_name} 架构设计\n\n{raw}",
        )
        return {
            "modules": None,
            "interfaces": None,
            "specs": None,
            "architecture_path": str(arch_path.resolve()),
            "raw_response": raw,
        }

    def review_code(self, module_path: str) -> dict:
        """代码评审，返回 {quality_score, issues, suggestions, raw_response}。"""
        # 读取模块代码内容
        code_content = self.workspace.read_text(module_path)
        user_message = (
            f"请对以下模块代码进行评审，给出质量评分（0-100）、问题清单与改进建议。\n"
            f"模块路径：{module_path}\n代码内容：\n{code_content or '（空或未找到文件）'}"
        )
        raw = self.call_llm(user_message, context="任务：代码评审与质量把控")
        return {
            "quality_score": None,
            "issues": None,
            "suggestions": None,
            "raw_response": raw,
        }

    # ------------------------------------------------------------------
    # 模块设计（execute_task 调用）
    # ------------------------------------------------------------------
    def design_module(self, task: dict) -> str:
        """基于任务描述产出模块设计文档（markdown）。

        LLM 调用失败时降级为模板设计文档（含模块名/接口定义占位/技术栈建议）。

        Returns:
            markdown 设计文档文本。
        """
        title = task.get("title", "未命名模块") if isinstance(task, dict) else "未命名模块"
        description = task.get("description", "") if isinstance(task, dict) else str(task)
        keyword = task.get("keyword", "") if isinstance(task, dict) else ""

        user_message = (
            f"请基于以下任务产出模块设计文档，必须包含：模块名、职责说明、"
            f"接口定义（请求/响应 schema）、依赖关系、技术栈建议、目录结构、测试要求。\n"
            f"任务标题：{title}\n"
            f"任务描述：{description}\n"
            f"关键词：{keyword or '无'}\n"
            f"请用 markdown 输出。"
        )
        try:
            raw = self.call_llm(user_message, context="任务：架构设计与模块拆分")
        except Exception as e:  # noqa: BLE001 - LLM 失败降级
            print(f"[architect] design_module LLM 调用失败，降级为模板设计文档：{e}")
            raw = ""

        if raw and len(raw.strip()) > 80:
            return f"# 模块设计文档：{title}\n\n{raw}\n"

        # 降级：模板设计文档
        return self._build_design_template(title, description, keyword)

    def _build_design_template(self, title: str, description: str, keyword: str) -> str:
        """生成模板设计文档（LLM 降级时使用）。"""
        from datetime import datetime

        return (
            f"# 模块设计文档：{title}\n\n"
            f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}（降级模式：LLM 调用失败）\n\n"
            f"## 模块名\n{title}\n\n"
            f"## 职责\n{description or '（待补充：模块核心职责与边界）'}\n\n"
            f"## 接口定义（占位）\n"
            f"```\n"
            f"// TODO: 定义关键 API 的请求/响应 schema\n"
            f"// 示例：\n"
            f"// POST /api/v1/{keyword or 'module'}/action\n"
            f"// Request:  {{ ... }}\n"
            f"// Response: {{ ... }}\n"
            f"```\n\n"
            f"## 依赖关系\n- （待补充：上游/下游依赖模块）\n\n"
            f"## 技术栈建议\n- 语言：Python 3.11\n"
            f"- 框架：Click（CLI）/ FastAPI（HTTP）\n"
            f"- 持久化：YAML / JSON 文件（与 AutoCorp 文件即数据库风格一致）\n"
            f"- 测试：pytest\n\n"
            f"## 目录结构\n"
            f"```\n"
            f"projects/<product>/\n"
            f"  ├── src/{keyword or 'module'}/\n"
            f"  │   ├── __init__.py\n"
            f"  │   └── main.py\n"
            f"  └── tests/\n"
            f"      └── test_{keyword or 'module'}.py\n"
            f"```\n\n"
            f"## 测试要求\n- 模块职责单一且可独立测试；\n"
            f"- 覆盖正常/边界/异常用例；\n"
            f"- 接口优先 RESTful 或简单 JSON RPC。\n"
        )

    @staticmethod
    def _sanitize_filename(name: str) -> str:
        """清理文件名：非字母数字字符替换为连字符，避免特殊字符。"""
        import re

        safe = re.sub(r"[^\w\-.]+", "-", name).strip("-")
        return safe or "default"

    # ------------------------------------------------------------------
    # 任务执行
    # ------------------------------------------------------------------
    def execute_task(self, task: dict) -> dict:
        """执行 design 类任务：产出模块设计文档并落盘。

        Returns:
            ``{status: "done"|"failed", result_path: str, error_reason: str}``
        """
        from engine.task_queue import TaskQueue

        task_id = task.get("id", "") if isinstance(task, dict) else ""
        try:
            queue = TaskQueue(self.workspace)
            queue.update_status(task_id, "in_progress")

            # 1. 产出设计文档
            doc = self.design_module(task)

            # 2. 写入 company/projects/<product>/architecture-<task_id>.md
            product = "default"
            if isinstance(task, dict):
                product = task.get("product") or task.get("keyword") or "default"
            safe_product = self._sanitize_filename(str(product))
            project_dir = self.workspace.projects_dir / safe_product
            self.workspace.ensure_dir(project_dir)
            target_path = project_dir / f"architecture-{task_id}.md"
            self.workspace.write_text(target_path, doc)
            result_path = str(target_path.resolve())

            # 3. 汇报完成
            self.report_done(task_id, result_path)
            return {"status": "done", "result_path": result_path, "error_reason": ""}
        except Exception as e:  # noqa: BLE001 - 顶层兜底
            self.report_failed(task_id, str(e))
            return {"status": "failed", "result_path": "", "error_reason": str(e)}
