"""CEO 智能体 - 首席执行官

对成本、市场、最终决策负责。所有决策必须基于数据（账本余额、市场情报、预期 ROI）。
"""
from __future__ import annotations

from datetime import datetime, timedelta
from typing import Any, Dict, List

from engine.agents.base import BaseAgent
from engine.workspace import WorkspaceManager
from engine.ledger import Ledger
from engine.llm_client import LLMClient


class CEO(BaseAgent):
    """首席执行官：负责立项、预算审批、终止等最终决策。"""

    def __init__(self, workspace: WorkspaceManager, llm_client: LLMClient = None):
        super().__init__("ceo", workspace, llm_client)
        # CEO 决策需要读取账本余额做成本判断
        self.ledger = Ledger(workspace)

    def review_proposal(self, proposal: dict) -> dict:
        """评审产品立项方案，返回 {decision, reason, budget_impact, raw_response}。

        决策前先读取账本余额，连同方案一并交给 LLM 评估。
        """
        balance = self.ledger.balance()
        audit = self.ledger.audit()
        user_message = (
            f"请评审以下立项方案并给出决策（approve/reject/revise）。\n"
            f"当前账本余额：{balance} {audit.get('currency', 'USD')}，"
            f"累计收入 {audit.get('total_income', 0)}，累计支出 {audit.get('total_expense', 0)}。\n"
            f"方案内容：\n{proposal}"
        )
        raw = self.call_llm(user_message, context="任务：立项评审与预算审批")
        # 启发式提取决策关键词
        decision = "unknown"
        for keyword in ("approve", "reject", "revise"):
            if keyword in raw.lower():
                decision = keyword
                break
        return {
            "decision": decision,
            "reason": raw,
            "budget_impact": None,
            "raw_response": raw,
        }

    def cost_control_check(self, amount: float, balance: float = None) -> dict:
        """成本控制检查：amount 超余额 30% 需审批。

        Args:
            amount: 待支出金额。
            balance: 当前余额，未提供则从 ledger 读取。
        """
        if balance is None:
            balance = self.ledger.balance()
        ratio = amount / balance if balance > 0 else 1.0
        needs_approval = ratio > 0.3
        user_message = (
            f"请做成本控制检查：拟支出 {amount}，当前余额 {balance}，"
            f"占比 {ratio:.1%}，是否{'需要' if needs_approval else '无需'}二次审批？"
        )
        raw = self.call_llm(user_message, context="任务：成本分析与预算审批")
        return {
            "needs_approval": needs_approval,
            "amount": amount,
            "balance": balance,
            "ratio": ratio,
            "raw_response": raw,
        }

    def make_decision(self, options, context: str = "") -> dict:
        """决策方法（支持两种调用形式）。

        - 传入 list：从多个选项中做选择，返回 {selected, reason, raw_response}（原有行为）。
        - 传入 dict（任务）：基于任务描述产出决策文档，返回 {decision_doc, raw_response}
          （execute_task 调用此分支，与 quarterly_strategy 不同）。
        """
        # 任务 dict 分支：execute_task 调用
        if isinstance(options, dict):
            return self._make_decision_for_task(options)
        # 原有 options-based 决策逻辑
        options_text = "\n".join(f"- 选项{i+1}: {opt}" for i, opt in enumerate(options))
        user_message = (
            f"请基于数据从以下选项中做出决策，并说明理由。\n"
            f"选项列表：\n{options_text}\n"
            f"补充上下文：{context or '无'}"
        )
        raw = self.call_llm(user_message, context="任务：立项决策与资源分配")
        # 启发式提取选中项
        selected = None
        for i, _ in enumerate(options):
            if f"选项{i+1}" in raw or f"option {i+1}" in raw.lower():
                selected = options[i]
                break
        # 持久化决策记录
        self.save_output(
            f"# CEO 决策记录\n\n选项：\n{options_text}\n\n决策结果：\n{raw}",
            category="decision",
            filename=f"ceo-decision-{self.workspace.root_dir.name}.md",
        )
        return {
            "selected": selected,
            "reason": raw,
            "raw_response": raw,
        }

    # ------------------------------------------------------------------
    # 季度战略会
    # ------------------------------------------------------------------
    def quarterly_strategy(self) -> dict:
        """季度战略会 - 输出方向/机会/公告

        每季度初由 CEO 召开，整合上季度经营数据、市场情报与人工请求，
        生成全员本季度决策上下文，落盘到 company/strategy/YYYY-Qn.md。

        流程：
          1. 读取上季度经营数据（ledger.audit）
          2. 读取市场情报（market-research 下最新 .md）
          3. 读取人工请求（company/human-requests/ 最近一季度的）
          4. 调用 LLM 生成战略
          5. 写入 company/strategy/YYYY-Qn.md

        LLM 调用失败时优雅降级，仍生成结构化文档（含占位内容）。

        Returns:
            包含 strategy_doc（文件路径）/ quarter（如 '2026-Q3'）/ raw_response 的字典。
        """
        # 1. 计算当前季度标识（用于文档命名与触发判断）
        now = datetime.now()
        year = now.year
        quarter = (now.month - 1) // 3 + 1  # 1~4
        quarter_label = f"{year}-Q{quarter}"

        # 2. 读取上季度经营数据
        audit = self.ledger.audit()

        # 3. 读取市场情报：market-research 目录下最近修改的 .md
        market_intel = ""
        market_research_dir = self.workspace.market_research_dir
        if market_research_dir.exists():
            md_files = sorted(
                [p for p in market_research_dir.glob("*.md")],
                key=lambda p: p.stat().st_mtime,
                reverse=True,
            )
            if md_files:
                market_intel = self.workspace.read_text(md_files[0])

        # 4. 读取人工请求：最近一季度的文件（按 mtime 过滤近 90 天）
        human_requests = ""
        human_requests_dir = self.workspace.root_dir / "human-requests"
        if human_requests_dir.exists():
            cutoff = now - timedelta(days=90)
            req_files = []
            for p in human_requests_dir.glob("*.md"):
                mtime = datetime.fromtimestamp(p.stat().st_mtime)
                if mtime >= cutoff:
                    req_files.append((mtime, p))
            # 按时间倒序，最新在前
            req_files.sort(key=lambda x: x[0], reverse=True)
            if req_files:
                lines = []
                for mtime, p in req_files:
                    lines.append(
                        f"### {p.name}（{mtime.strftime('%Y-%m-%d')}）\n\n"
                        f"{self.workspace.read_text(p)}"
                    )
                human_requests = "\n\n".join(lines)

        # 5. 调用 LLM 生成战略
        user_message = (
            f"请基于以下信息生成 {year} 年第 {quarter} 季度战略文档，"
            f"包含「上季度复盘」「下季度战略方向」「重点机会清单」「重大事项公告」四部分。\n\n"
            f"## 上季度经营数据\n"
            f"- 当前余额：{audit.get('balance', 0)} {audit.get('currency', 'USD')}\n"
            f"- 累计收入：{audit.get('total_income', 0)}\n"
            f"- 累计支出：{audit.get('total_expense', 0)}\n"
            f"- 交易笔数：{audit.get('transaction_count', 0)}\n\n"
            f"## 市场情报\n{market_intel or '（暂无）'}\n\n"
            f"## 人工请求\n{human_requests or '（暂无）'}\n"
        )

        raw = ""
        try:
            raw = self.call_llm(user_message, context=f"任务：{year} 年第 {quarter} 季度战略会")
        except Exception as e:
            print(f"[ceo] 季度战略会 LLM 调用失败，使用占位内容降级生成：{e}")
            raw = ""

        # 6. 组装战略文档；LLM 失败时用占位内容保证结构完整
        doc_content = self._build_strategy_doc(
            year=year,
            quarter=quarter,
            audit=audit,
            llm_output=raw,
        )

        # 7. 写入 company/strategy/YYYY-Qn.md
        strategy_dir = self.workspace.root_dir / "strategy"
        self.workspace.ensure_dir(strategy_dir)
        doc_path = strategy_dir / f"{quarter_label}.md"
        self.workspace.write_text(doc_path, doc_content)

        return {
            "strategy_doc": str(doc_path.resolve()),
            "quarter": quarter_label,
            "raw_response": raw,
        }

    def _build_strategy_doc(
        self,
        year: int,
        quarter: int,
        audit: dict,
        llm_output: str,
    ) -> str:
        """根据 LLM 输出与经营数据组装最终战略文档。

        LLM 输出非空且包含核心章节时直接采用；否则用结构化占位内容兜底，
        确保文档始终包含「上季度复盘 / 下季度战略方向 / 重点机会清单 / 重大事项公告」四部分。
        """
        currency = audit.get("currency", "USD")
        balance = audit.get("balance", 0)
        total_income = audit.get("total_income", 0)
        total_expense = audit.get("total_expense", 0)
        title = f"# {year} 年第 {quarter} 季度战略"
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

        # LLM 输出包含核心章节时，采用 LLM 输出作为正文
        if llm_output and "战略方向" in llm_output:
            return f"{title}\n\n> 生成时间：{timestamp}\n\n{llm_output}\n"

        # 降级：用占位内容生成结构化文档
        placeholder = [
            title,
            "",
            f"> 生成时间：{timestamp}（降级模式：LLM 调用失败或返回不完整）",
            "",
            "## 上季度复盘",
            f"- 真实收入: $0（账本暂未区分真实/虚拟收入，累计收入 ${total_income} {currency}）",
            f"- 虚拟收入: $0（账本暂未区分真实/虚拟收入）",
            f"- 真实支出: $0（账本暂未区分真实/虚拟支出，累计支出 ${total_expense} {currency}）",
            f"- 当前余额: ${balance} {currency}",
            "- 关键成就: （待 LLM 补充）",
            "- 教训: （待 LLM 补充）",
            "",
            "## 下季度战略方向",
            "1. 方向一：（待补充，参考市场情报与上季度复盘）",
            "2. 方向二：（待补充）",
            "3. 方向三：（待补充）",
            "",
            "## 重点机会清单",
            "| 机会 | 预期 ROI | 所需资源 | 风险 |",
            "|------|---------|---------|------|",
            "| （待补充） | （待补充） | （待补充） | （待补充） |",
            "",
            "## 重大事项公告",
            "- （待补充；本次为降级生成）",
            "",
        ]
        return "\n".join(placeholder)

    # ------------------------------------------------------------------
    # 任务级决策（execute_task 调用，与 quarterly_strategy 不同）
    # ------------------------------------------------------------------
    def _make_decision_for_task(self, task: dict) -> dict:
        """基于任务描述产出 CEO 决策文档。

        构造决策 prompt（CEO 系统提示词 + 决策要求 + 当前公司状态摘要）；
        LLM 调用失败时降级为规则决策（含「砍」「kill」→ 砍项；含「立项」「新」→ 立项）。

        Returns:
            ``{decision_doc: str, raw_response: str}``
        """
        title = task.get("title", "决策事项") if isinstance(task, dict) else "决策事项"
        description = task.get("description", "") if isinstance(task, dict) else str(task)

        # 公司状态摘要
        try:
            balance = self.ledger.balance()
            audit = self.ledger.audit()
        except Exception as e:  # noqa: BLE001
            print(f"[ceo] 读取账本失败，使用占位状态：{e}")
            balance = 0
            audit = {}
        status_summary = (
            f"当前余额：{balance}；累计收入：{audit.get('total_income', 0)}；"
            f"累计支出：{audit.get('total_expense', 0)}；交易笔数：{audit.get('transaction_count', 0)}"
        )

        user_message = (
            f"请基于以下事项给出明确 CEO 决策（approve/reject/revise），"
            f"并说明理由与预算影响。\n"
            f"事项标题：{title}\n"
            f"事项描述：{description}\n"
            f"当前公司状态：{status_summary}\n"
            f"输出格式：\n  决策: approve/reject/revise\n  理由: ...\n  预算影响: ..."
        )
        try:
            raw = self.call_llm(user_message, context="任务：立项决策与资源分配")
        except Exception as e:  # noqa: BLE001 - LLM 失败降级
            print(f"[ceo] make_decision LLM 调用失败，降级为规则决策：{e}")
            raw = ""

        if raw and len(raw.strip()) > 30:
            decision_doc = f"# CEO 决策记录：{title}\n\n> 公司状态：{status_summary}\n\n{raw}\n"
        else:
            decision_doc = self._build_decision_template(title, description, status_summary)

        return {
            "decision_doc": decision_doc,
            "raw_response": raw,
        }

    def _build_decision_template(self, title: str, description: str, status_summary: str) -> str:
        """生成规则决策文档（LLM 降级时使用）。"""
        from datetime import datetime

        desc_lower = (description or "").lower()
        if "砍" in (description or "") or "kill" in desc_lower or "终止" in (description or ""):
            decision = "reject"
            action = "砍项 / 终止"
            reason = (
                "事项描述中包含砍项/终止信号（「砍」「kill」「终止」），基于成本控制原则终止该事项，"
                "停止后续资源投入，归档相关产出。"
            )
        elif "立项" in (description or "") or "新" in (description or "") or "launch" in desc_lower:
            decision = "approve"
            action = "立项 / 启动"
            reason = (
                "事项描述中包含立项/新建信号（「立项」「新」「launch」），符合增长导向，"
                "原则上 approve，建议小步快跑、设定可量化里程碑与预算上限。"
            )
        else:
            decision = "revise"
            action = "修订后再议"
            reason = "事项描述未含明确砍项或立项信号，需补充预期 ROI、预算与里程碑后再决策。"

        return (
            f"# CEO 决策记录：{title}\n\n"
            f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}（降级模式：LLM 调用失败，规则决策）\n\n"
            f"## 公司状态\n{status_summary}\n\n"
            f"## 事项\n{description or '（无描述）'}\n\n"
            f"## 决策\n- 决策: **{decision}**\n- 动作: {action}\n\n"
            f"## 理由\n{reason}\n\n"
            f"## 预算影响\n- 待人工补充量化预算影响；单笔支出超余额 30% 需二次审批。\n"
        )

    # ------------------------------------------------------------------
    # 任务执行
    # ------------------------------------------------------------------
    def execute_task(self, task: dict) -> dict:
        """执行 decision 类任务：产出 CEO 决策文档并落盘。

        Returns:
            ``{status: "done"|"failed", result_path: str, error_reason: str}``
        """
        from engine.task_queue import TaskQueue

        task_id = task.get("id", "") if isinstance(task, dict) else ""
        try:
            queue = TaskQueue(self.workspace)
            queue.update_status(task_id, "in_progress")

            # 1. 产出决策文档（make_decision 接受 dict 触发任务分支）
            result = self.make_decision(task)
            decision_doc = result.get("decision_doc") or result.get("reason", "")

            # 2. 写入 company/knowledge/decisions/decision-<task_id>.md
            target_path = self.workspace.decisions_dir / f"decision-{task_id}.md"
            self.workspace.write_text(target_path, decision_doc)
            result_path = str(target_path.resolve())

            # 3. 汇报完成
            self.report_done(task_id, result_path)
            return {"status": "done", "result_path": result_path, "error_reason": ""}
        except Exception as e:  # noqa: BLE001 - 顶层兜底
            self.report_failed(task_id, str(e))
            return {"status": "failed", "result_path": "", "error_reason": str(e)}
