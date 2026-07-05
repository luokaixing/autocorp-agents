"""角色 KPI 追踪模块

记录、汇总各角色 KPI 数据，生成 KPI 看板。
持久化到 company/config/kpi_records.yaml，配置读取 company/config/role_kpi.yaml。

设计要点：
- 所有读写均通过 WorkspaceManager 落盘，跨进程可见。
- record 失败应由调用方自行 try/except，本模块自身不做静默吞异常，
  但 report_done 已包裹 try/except，保证 KPI 失败不影响主流程。
- weekly_summary 返回 {role: {metric: {target, actual, achievement_rate, samples}}}
- generate_kpi_dashboard 输出 markdown 表格，供 18:00 复盘循环调用。
"""
from __future__ import annotations

from datetime import date, datetime, timedelta
from typing import List, Optional


class KPITracker:
    """角色 KPI 追踪器 - 记录、汇总、生成周报。"""

    def __init__(self, workspace=None):
        from engine.workspace import WorkspaceManager
        self.workspace = workspace or WorkspaceManager()
        self.kpi_config_path = self.workspace.root_dir / "config" / "role_kpi.yaml"
        self.records_path = self.workspace.root_dir / "config" / "kpi_records.yaml"

    # ------------------------------------------------------------------
    # 记录
    # ------------------------------------------------------------------
    def record(self, role: str, metric: str, value: float, date: str = None) -> None:
        """记录一条 KPI 数据。date 默认今日。持久化到 kpi_records.yaml。

        Args:
            role: 角色名（programmer / tester / ...）。
            metric: 指标名（与 role_kpi.yaml 中的 metric 字段一致）。
            value: 本次记录的数值（累加到周汇总）。
            date: 日期字符串 YYYY-MM-DD，默认今日。
        """
        records = self._load_records()
        record = {
            "role": role,
            "metric": metric,
            "value": float(value),
            "date": date or datetime.now().strftime("%Y-%m-%d"),
            "recorded_at": datetime.now().isoformat(timespec="seconds"),
        }
        records.append(record)
        self._save_records(records)

    # ------------------------------------------------------------------
    # 汇总
    # ------------------------------------------------------------------
    def weekly_summary(self, role: str = None) -> dict:
        """返回本周（最近 7 天）KPI 汇总。

        role=None 时返回所有角色；指定 role 时只返回该角色。
        返回 {role: {metric: {target, actual, achievement_rate, samples: [...]}}}

        Args:
            role: 可选角色名过滤。

        Returns:
            按角色 → 指标嵌套的汇总字典；无数据时对应字段缺失。
        """
        today = date.today()
        week_ago = today - timedelta(days=7)
        records = self._load_records()
        kpi_config = self._load_kpi_config()

        # 筛选本周记录（含端点）
        week_records: List[dict] = []
        for r in records:
            rdate = self._parse_date(r.get("date", ""))
            if rdate is None:
                continue
            if not (week_ago <= rdate <= today):
                continue
            if role and r.get("role") != role:
                continue
            week_records.append(r)

        # 按 role + metric 分组聚合 actual，并保留 samples
        summary: dict = {}
        for r in week_records:
            r_role = r.get("role")
            r_metric = r.get("metric")
            summary.setdefault(r_role, {}).setdefault(
                r_metric, {"actual": 0.0, "samples": []}
            )
            summary[r_role][r_metric]["actual"] += float(r.get("value", 0.0) or 0.0)
            summary[r_role][r_metric]["samples"].append(r)

        # 对照配置补全 target 与 achievement_rate
        for kpi in kpi_config:
            k_role = kpi.get("role")
            k_metric = kpi.get("metric")
            target = float(kpi.get("target", 0.0) or 0.0)
            if k_role in summary and k_metric in summary[k_role]:
                entry = summary[k_role][k_metric]
                entry["target"] = target
                actual = entry.get("actual", 0.0)
                rate = (actual / target * 100.0) if target > 0 else 0.0
                entry["achievement_rate"] = round(rate, 2)

        return summary

    def daily_summary(self, role: str = None, date: str = None) -> dict:
        """返回某日各角色 KPI 完成情况。

        Args:
            role: 可选角色名过滤。
            date: 日期字符串 YYYY-MM-DD，默认今日。

        Returns:
            {role: {metric: {actual, samples}}}；无数据返回空 dict。
        """
        target_date = date or datetime.now().strftime("%Y-%m-%d")
        records = self._load_records()

        daily: dict = {}
        for r in records:
            if r.get("date") != target_date:
                continue
            if role and r.get("role") != role:
                continue
            r_role = r.get("role")
            r_metric = r.get("metric")
            daily.setdefault(r_role, {}).setdefault(
                r_metric, {"actual": 0.0, "samples": []}
            )
            daily[r_role][r_metric]["actual"] += float(r.get("value", 0.0) or 0.0)
            daily[r_role][r_metric]["samples"].append(r)
        return daily

    # ------------------------------------------------------------------
    # 看板
    # ------------------------------------------------------------------
    def generate_kpi_dashboard(self) -> str:
        """生成 markdown 格式的 KPI 看板表格。

        格式：
        | 角色 | 指标 | 今日值 | 周累计 | 目标 | 达成率 |

        Returns:
            markdown 字符串。
        """
        today_str = datetime.now().strftime("%Y-%m-%d")
        daily = self.daily_summary()
        weekly = self.weekly_summary()
        kpi_config = self._load_kpi_config()

        lines = [
            f"# AutoCorp 角色 KPI 看板 - {today_str}",
            "",
            "| 角色 | 指标 | 今日值 | 周累计 | 目标 | 达成率 |",
            "|------|------|--------|--------|------|--------|",
        ]

        for kpi in kpi_config:
            k_role = kpi.get("role", "")
            k_metric = kpi.get("metric", "")
            target = kpi.get("target", 0.0)
            unit = kpi.get("unit", "")

            today_value = 0.0
            week_value = 0.0
            rate = 0.0

            if k_role in daily and k_metric in daily[k_role]:
                today_value = float(
                    daily[k_role][k_metric].get("actual", 0.0) or 0.0
                )
            if k_role in weekly and k_metric in weekly[k_role]:
                week_value = float(
                    weekly[k_role][k_metric].get("actual", 0.0) or 0.0
                )
                rate = float(
                    weekly[k_role][k_metric].get("achievement_rate", 0.0) or 0.0
                )

            lines.append(
                f"| {k_role} | {k_metric} | {today_value:.2f}{unit} | "
                f"{week_value:.2f}{unit} | {target}{unit} | {rate:.1f}% |"
            )

        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 持久化读写
    # ------------------------------------------------------------------
    def _load_kpi_config(self) -> list:
        """读取 role_kpi.yaml 返回 kpis 列表。"""
        data = self.workspace.read_yaml(self.kpi_config_path)
        if not data:
            return []
        return data.get("kpis", []) or []

    def _load_records(self) -> list:
        """读取 kpi_records.yaml 返回记录列表。"""
        data = self.workspace.read_yaml(self.records_path)
        if not data:
            return []
        # 兼容两种结构：{"records": [...]} 或顶层列表
        if isinstance(data, dict):
            return data.get("records", []) or []
        if isinstance(data, list):
            return data
        return []

    def _save_records(self, records: list) -> None:
        """写入 kpi_records.yaml。"""
        self.workspace.write_yaml(self.records_path, {"records": records})

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _parse_date(s: str) -> Optional[date]:
        """解析 YYYY-MM-DD 字符串为 date 对象，失败返回 None。"""
        if not s:
            return None
        try:
            return datetime.strptime(str(s), "%Y-%m-%d").date()
        except (ValueError, TypeError):
            return None
