"""经营日报生成器

从工作区状态汇总生成经营日报，并支持 CLI 状态查询。
Reporter 是只读工具，不修改工作区数据（除写入日报文件外）。
工作区可能为空（未运行过 run-day），所有读取均优雅处理缺失文件。

升级：区分真实收入/支出（实际到账）与虚拟收入/支出（模拟/估算），
日报「账本近期变动」用 💰 标记真实交易、（虚拟）标记虚拟交易。
"""
from __future__ import annotations

from datetime import date
from pathlib import Path
from typing import Any, Dict, List


class Reporter:
    """经营日报生成器 - 从工作区状态汇总生成报告"""

    def __init__(self, workspace=None):
        from engine.workspace import WorkspaceManager
        self.workspace = workspace or WorkspaceManager()
        from engine.ledger import Ledger
        self.ledger = Ledger(self.workspace)

    # ------------------------------------------------------------------
    # 结构化数据
    # ------------------------------------------------------------------
    def generate_summary(self) -> dict:
        """返回结构化状态数据 dict，供其他模块调用。"""
        # 账本审计（工作区为空或账本缺失时降级为零值）
        try:
            audit = self.ledger.audit()
        except Exception:
            audit = {
                "balance": 0.0,
                "currency": "USD",
                "total_income": 0.0,
                "total_expense": 0.0,
                "real_total_income": 0.0,
                "real_total_expense": 0.0,
                "virtual_total_income": 0.0,
                "virtual_total_expense": 0.0,
                "transaction_count": 0,
                "recent_transactions": [],
            }

        # 进行中项目列表
        try:
            projects = self.workspace.list_projects()
        except Exception:
            projects = []

        # 今日会议纪要
        meeting_md = self._read_today_meeting()

        today = date.today().isoformat()
        report_path = self.workspace.today_report_path()
        return {
            "date": today,
            "balance": float(audit.get("balance", 0.0)),
            "currency": audit.get("currency", "USD"),
            "total_income": float(audit.get("total_income", 0.0)),
            "total_expense": float(audit.get("total_expense", 0.0)),
            "real_total_income": float(audit.get("real_total_income", 0.0)),
            "real_total_expense": float(audit.get("real_total_expense", 0.0)),
            "virtual_total_income": float(audit.get("virtual_total_income", 0.0)),
            "virtual_total_expense": float(audit.get("virtual_total_expense", 0.0)),
            "transaction_count": int(audit.get("transaction_count", 0)),
            "recent_transactions": audit.get("recent_transactions", []) or [],
            "projects": projects,
            "meeting_md": meeting_md,
            "meeting_held": bool(meeting_md.strip()),
            "report_path": str(report_path.resolve()),
        }

    # ------------------------------------------------------------------
    # 日报生成
    # ------------------------------------------------------------------
    def generate_daily_report(self) -> str:
        """生成经营日报，写入 today_report_path()，返回报告文件路径。

        读取当日会议纪要、账本审计、进行中项目，汇总生成日报 markdown。
        """
        summary = self.generate_summary()
        content = self._render_report(summary)
        report_path = self.workspace.today_report_path()
        self.workspace.write_text(report_path, content)
        return str(report_path.resolve())

    def _render_report(self, s: dict) -> str:
        """根据摘要数据渲染日报 markdown。"""
        # 会议纪要摘要
        meeting_md = (s.get("meeting_md") or "").strip()
        meeting_section = meeting_md if meeting_md else "今日无会议记录"

        # 进行中项目
        projects: List[str] = s.get("projects", [])
        if projects:
            project_section = "\n".join(f"- {p}" for p in projects)
        else:
            project_section = "暂无进行中项目"

        # 账本近期变动（最近5笔交易）
        recent: List[Dict[str, Any]] = s.get("recent_transactions", [])
        if recent:
            tx_lines = []
            for t in recent:
                tx_id = t.get("id", "?")
                ttype = t.get("type", "?")
                amount = float(t.get("amount", 0.0))
                source = t.get("source", "")
                ts = self._fmt_timestamp(t.get("timestamp", ""))
                sign = "+" if ttype == "income" else "-"
                # 真实交易用 💰 标记，虚拟交易用（虚拟）标记
                is_real = bool(t.get("is_real", False))
                real_mark = "💰" if is_real else "（虚拟）"
                tx_lines.append(
                    f"- [{tx_id}] {ts} {ttype}: {sign}${amount:.2f} ({source}) {real_mark}"
                )
            tx_section = "\n".join(tx_lines)
        else:
            tx_section = "暂无交易记录"

        return (
            f"# AutoCorp 经营日报 - {s['date']}\n"
            f"\n"
            f"## 公司状态概览\n"
            f"- 账本余额: ${s['balance']:.2f}\n"
            f"- 累计收入: ${s['total_income']:.2f}\n"
            f"- 累计支出: ${s['total_expense']:.2f}\n"
            f"- 交易笔数: {s['transaction_count']}\n"
            f"- 进行中项目: {len(projects)}\n"
            f"\n"
            f"## 今日会议\n"
            f"{meeting_section}\n"
            f"\n"
            f"## 进行中项目\n"
            f"{project_section}\n"
            f"\n"
            f"## 账本近期变动\n"
            f"{tx_section}\n"
            f"\n"
            f"## 明日计划\n"
            f"基于今日进展自动规划（待补充）\n"
        )

    # ------------------------------------------------------------------
    # CLI 状态摘要
    # ------------------------------------------------------------------
    def status(self) -> str:
        """生成简短的状态摘要（用于 CLI 输出）。"""
        s = self.generate_summary()
        if s["meeting_held"]:
            meeting_line = f"今日会议: 已召开 ({s['date']})"
        else:
            meeting_line = "今日会议: 未召开"
        report_display = self._rel_path(s["report_path"])
        lines = [
            "AutoCorp 公司状态",
            "==================",
            f"账本余额: ${s['balance']:.2f}",
            f"累计收入: ${s['total_income']:.2f}",
            f"累计支出: ${s['total_expense']:.2f}",
            f"真实收入: ${s['real_total_income']:.2f}",
            f"真实支出: ${s['real_total_expense']:.2f}",
            f"交易笔数: {s['transaction_count']}",
            f"进行中项目: {len(s['projects'])} 个",
            meeting_line,
            f"今日日报: {report_display}",
        ]
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 辅助方法
    # ------------------------------------------------------------------
    def _read_today_meeting(self) -> str:
        """读取今日会议纪要 meeting.md，不存在返回空字符串。"""
        meeting_file = self.workspace.today_meeting_dir() / "meeting.md"
        return self.workspace.read_text(meeting_file)

    @staticmethod
    def _fmt_timestamp(ts: str) -> str:
        """格式化时间戳为 YYYY-MM-DD HH:MM:SS，无法解析则原样截断返回。"""
        if not ts:
            return ""
        # 取 ISO 字符串前 19 位并将 T 替换为空格
        return ts[:19].replace("T", " ")

    def _rel_path(self, abs_path: str) -> str:
        """将绝对路径转为相对项目根的 POSIX 路径用于展示，转换失败则原样返回。"""
        try:
            # 项目根 = workspace 根的上一级（如 d:\autoCompany）
            project_root = self.workspace.root_dir.parent
            rel = Path(abs_path).relative_to(project_root)
            return rel.as_posix()
        except Exception:
            return abs_path
