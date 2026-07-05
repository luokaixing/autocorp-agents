"""健康监控系统 (HealthMonitor)

定义 5 类健康指标采集器与每日健康报告生成器，对应 Spec E 节：
1. 任务健康：当日 pending 任务数、平均完成时长、失败率、重试率
2. 角色健康：每个角色当日是否激活、产出文件数、KPI 达成率
3. 财务健康：钱包余额、当日真实收入、危机警报阈值
4. 协作健康：消息池活跃度、跨角色转交次数、Phase 完整执行率
5. 服务健康：未完成订单数、订单平均交付周期、客户验收一次通过率

设计原则：
- 文件即数据库：阈值配置 health-thresholds.yaml，报告 Markdown 落盘
- 优雅降级：单类指标采集失败不阻塞整体报告生成
- 延迟实例化：message_pool / human_loop 为空时延迟创建
- 三色仪表盘：每项指标 green/yellow/red，任一红色触发 health.alert.red
"""
from __future__ import annotations

import sys
from datetime import date, datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

# 标准角色列表（与 company/config/employees.yaml 的 role 字段一致）
ROLES: List[str] = [
    "ceo",
    "cto",
    "coo",
    "architect",
    "programmer",
    "tester",
    "product_manager",
]

# 预期 Phase 完成数（Spec 中 6 个标准 Phase：Morning/Research/Design/Build/Promote/Review）
# 注：Phase-Service 按需触发，不计入每日预期
EXPECTED_PHASE_COUNT: int = 6

# 状态枚举常量
STATUS_GREEN: str = "green"
STATUS_YELLOW: str = "yellow"
STATUS_RED: str = "red"

# 状态到 emoji 的映射（仪表盘表格用）
STATUS_EMOJI: Dict[str, str] = {
    STATUS_GREEN: "🟢",
    STATUS_YELLOW: "🟡",
    STATUS_RED: "🔴",
}

# 状态严重度排序（用于取最差值）
_STATUS_SEVERITY: Dict[str, int] = {
    STATUS_GREEN: 0,
    STATUS_YELLOW: 1,
    STATUS_RED: 2,
}

# 默认阈值（company/config/health-thresholds.yaml 缺失时使用）
_DEFAULT_THRESHOLDS: Dict[str, Dict[str, Any]] = {
    "task_health": {
        "pending_count_yellow": 10,
        "pending_count_red": 30,
        "avg_complete_minutes_yellow": 60,
        "avg_complete_minutes_red": 180,
        "fail_rate_percent_yellow": 20,
        "fail_rate_percent_red": 50,
        "retry_rate_percent_yellow": 30,
        "retry_rate_percent_red": 60,
    },
    "role_health": {
        "inactive_days_yellow": 1,
        "inactive_days_red": 3,
        "output_files_daily_yellow": 0,
        "output_files_daily_red": 0,  # 当日 0 产出为黄，连续 2 天 0 产出为红
        "kpi_achievement_percent_yellow": 50,
        "kpi_achievement_percent_red": 20,
    },
    "finance_health": {
        "wallet_balance_usd_yellow": 10,
        "wallet_balance_usd_red": 1,
        "zero_income_days_yellow": 2,
        "zero_income_days_red": 3,
    },
    "collab_health": {
        "message_pool_daily_yellow": 5,
        "message_pool_daily_red": 1,
        "handoff_count_daily_yellow": 5,
        "handoff_count_daily_red": 10,
        "phase_completion_rate_percent_yellow": 60,
        "phase_completion_rate_percent_red": 30,
    },
    "service_health": {
        "pending_orders_yellow": 3,
        "pending_orders_red": 8,
        "avg_delivery_days_yellow": 3,
        "avg_delivery_days_red": 7,
        "first_acceptance_rate_percent_yellow": 60,
        "first_acceptance_rate_percent_red": 30,
    },
}

# 角色 -> 主要产出目录映射（相对 company/ 根，用于统计各角色当日产出文件数）
_ROLE_OUTPUT_DIRS: Dict[str, List[str]] = {
    "ceo": ["decisions", "operations"],
    "cto": ["knowledge/decisions"],
    "coo": ["marketing", "knowledge/airdrops", "knowledge/marketing"],
    "architect": ["projects", "knowledge/decisions"],
    "programmer": ["projects"],
    "tester": ["reports"],
    "product_manager": ["knowledge/market-research", "knowledge/opportunities"],
}


def _worst_status(statuses: List[str]) -> str:
    """从状态列表中取最严重的状态。

    Args:
        statuses: 状态字符串列表（green/yellow/red）。

    Returns:
        最严重的状态；空列表返回 green。
    """
    if not statuses:
        return STATUS_GREEN
    return max(statuses, key=lambda s: _STATUS_SEVERITY.get(s, 0))


class HealthMonitor:
    """健康监控系统 - 采集 5 类健康指标并生成每日健康报告。

    配置：``company/config/health-thresholds.yaml``（缺失时使用内置默认阈值）
    报告：``company/health/health-YYYY-MM-DD.md``（含三色仪表盘表格）
    告警：任一指标红色时 publish ``health.alert.red`` + 调用 human_loop 通知

    典型用法::

        monitor = HealthMonitor()
        result = monitor.run_daily_check()
        # result: {report_path, red_count, yellow_count, green_count, alerts: [...]}
    """

    def __init__(
        self,
        workspace=None,
        llm_client=None,
        message_pool=None,
        human_loop=None,
    ) -> None:
        """初始化健康监控器。

        Args:
            workspace: WorkspaceManager 实例；为空则延迟实例化（默认工作区）。
            llm_client: LLM 客户端（保留参数，当前实现不强制使用）。
            message_pool: MessagePool 实例；为空则延迟实例化。
            human_loop: HumanLoop 实例；为空则延迟实例化。
        """
        self.workspace = workspace
        self.llm_client = llm_client
        self.message_pool = message_pool
        self.human_loop = human_loop
        # 阈值配置缓存（避免每次采集都重新读盘）
        self._thresholds_cache: Optional[Dict[str, Any]] = None

    # ------------------------------------------------------------------
    # 延迟实例化辅助
    # ------------------------------------------------------------------
    def _get_workspace(self):
        """延迟实例化 WorkspaceManager。"""
        if self.workspace is None:
            from engine.workspace import WorkspaceManager
            self.workspace = WorkspaceManager()
        return self.workspace

    def _get_message_pool(self):
        """延迟实例化 MessagePool；失败返回 None（不阻塞主流程）。"""
        if self.message_pool is None:
            try:
                from engine.message_pool import MessagePool
                self.message_pool = MessagePool(self._get_workspace())
            except Exception as e:  # noqa: BLE001 - 实例化失败优雅降级
                print(f"[health_monitor] MessagePool 实例化失败: {e}", file=sys.stderr)
                return None
        return self.message_pool

    def _get_human_loop(self):
        """延迟实例化 HumanLoop；失败返回 None（不阻塞主流程）。"""
        if self.human_loop is None:
            try:
                from engine.human_loop import HumanLoop
                self.human_loop = HumanLoop(self._get_workspace())
            except Exception as e:  # noqa: BLE001
                print(f"[health_monitor] HumanLoop 实例化失败: {e}", file=sys.stderr)
                return None
        return self.human_loop

    # ------------------------------------------------------------------
    # 阈值加载
    # ------------------------------------------------------------------
    @property
    def thresholds_path(self) -> Path:
        """health-thresholds.yaml 配置文件路径：``company/config/health-thresholds.yaml``"""
        return self._get_workspace().config_dir / "health-thresholds.yaml"

    def _load_thresholds(self) -> Dict[str, Any]:
        """加载 health-thresholds.yaml 阈值配置。

        配置文件缺失或读取异常时优雅降级为内置默认阈值。
        采用深合并策略：用户配置覆盖默认值的同名字段，未指定字段保留默认。

        Returns:
            5 类指标阈值字典。
        """
        if self._thresholds_cache is not None:
            return self._thresholds_cache

        try:
            data = self._get_workspace().read_yaml(self.thresholds_path)
        except Exception as e:  # noqa: BLE001
            print(f"[health_monitor] 阈值配置读取失败: {e}，使用默认值", file=sys.stderr)
            data = None

        if not data or not isinstance(data, dict):
            self._thresholds_cache = _DEFAULT_THRESHOLDS
            return self._thresholds_cache

        # 深合并：以默认值为基，用户配置覆盖
        merged: Dict[str, Any] = {}
        for category, defaults in _DEFAULT_THRESHOLDS.items():
            user_vals = data.get(category, {}) or {}
            merged_category = dict(defaults)
            if isinstance(user_vals, dict):
                merged_category.update(user_vals)
            merged[category] = merged_category
        # 保留用户配置中可能新增的额外类别
        for k, v in data.items():
            if k not in merged and isinstance(v, dict):
                merged[k] = v
        self._thresholds_cache = merged
        return merged

    # ------------------------------------------------------------------
    # 通用辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _today_str() -> str:
        """返回今日 ``YYYY-MM-DD`` 字符串。"""
        return date.today().isoformat()

    @staticmethod
    def _now_iso() -> str:
        """返回当前时间 ISO 8601 seconds 精度。"""
        return datetime.now().isoformat(timespec="seconds")

    @staticmethod
    def _parse_iso(ts: Optional[str]) -> Optional[datetime]:
        """解析 ISO 8601 时间字符串。

        Args:
            ts: 时间字符串，如 ``2026-06-29T11:00:10``。

        Returns:
            datetime 对象；输入为空或格式异常返回 None。
        """
        if not ts or not isinstance(ts, str):
            return None
        try:
            return datetime.fromisoformat(ts)
        except (ValueError, TypeError):
            return None

    def _determine_status(
        self,
        value: Any,
        yellow_threshold: Any,
        red_threshold: Any,
        mode: str = "lower_is_worse",
    ) -> str:
        """根据阈值判断 green/yellow/red。

        Args:
            value: 实际值（数值或 None）。
            yellow_threshold: 黄色阈值。
            red_threshold: 红色阈值。
            mode: 判断模式：
                - ``"lower_is_worse"``：值越低越糟（如余额、达成率）。
                  ``value <= red_threshold`` => red
                  ``value <= yellow_threshold`` => yellow
                  否则 green
                - ``"higher_is_worse"``：值越高越糟（如失败率、pending 数）。
                  ``value >= red_threshold`` => red
                  ``value >= yellow_threshold`` => yellow
                  否则 green

        Returns:
            状态字符串 green/yellow/red；value 为 None 时返回 green（数据缺失不告警）。
        """
        if value is None:
            return STATUS_GREEN
        try:
            v = float(value)
            yt = float(yellow_threshold)
            rt = float(red_threshold)
        except (TypeError, ValueError):
            return STATUS_GREEN

        if mode == "higher_is_worse":
            if v >= rt:
                return STATUS_RED
            if v >= yt:
                return STATUS_YELLOW
            return STATUS_GREEN
        # 默认 lower_is_worse
        if v <= rt:
            return STATUS_RED
        if v <= yt:
            return STATUS_YELLOW
        return STATUS_GREEN

    # ------------------------------------------------------------------
    # 1. 任务健康
    # ------------------------------------------------------------------
    def collect_task_health(self) -> dict:
        """采集任务健康指标。

        从 ``engine.task_queue.TaskQueue`` 读取任务数据，计算：
        - pending 任务数
        - 当日完成任务的平均完成时长（``completed_at - claimed_at``，分钟）
        - 失败率（``failed / (done+failed) * 100%``）
        - 重试率（``retry_count>0`` 的任务占比）

        Returns:
            ``{status, value: {pending, avg_complete_minutes, fail_rate, retry_rate},
            threshold, detail}``
        """
        threshold = self._load_thresholds().get("task_health", {})
        today_str = self._today_str()
        default_value = {
            "pending": 0,
            "avg_complete_minutes": 0,
            "fail_rate": 0,
            "retry_rate": 0,
        }
        try:
            from engine.task_queue import TaskQueue
            tq = TaskQueue(self._get_workspace())
            tasks = tq.list_all()
        except Exception as e:  # noqa: BLE001 - 任务队列读取失败优雅降级
            return {
                "status": STATUS_GREEN,
                "value": default_value,
                "threshold": threshold,
                "detail": f"任务队列读取失败：{e}",
            }

        pending_count = sum(1 for t in tasks if t.get("status") == "pending")

        # 当日完成任务的平均完成时长
        complete_minutes: List[float] = []
        for t in tasks:
            if t.get("status") != "done":
                continue
            completed = self._parse_iso(t.get("completed_at"))
            claimed = self._parse_iso(t.get("claimed_at"))
            if completed and claimed:
                # 仅统计当日完成的任务
                if completed.date().isoformat() == today_str:
                    delta_min = (completed - claimed).total_seconds() / 60.0
                    if delta_min >= 0:
                        complete_minutes.append(delta_min)
        avg_complete = (
            sum(complete_minutes) / len(complete_minutes)
            if complete_minutes
            else 0.0
        )

        # 失败率 = failed / (done + failed) * 100
        done_count = sum(1 for t in tasks if t.get("status") == "done")
        failed_count = sum(1 for t in tasks if t.get("status") == "failed")
        denominator = done_count + failed_count
        fail_rate = (failed_count / denominator * 100.0) if denominator > 0 else 0.0

        # 重试率 = retry_count > 0 的任务占比
        retry_count = sum(1 for t in tasks if (t.get("retry_count") or 0) > 0)
        retry_rate = (retry_count / len(tasks) * 100.0) if tasks else 0.0

        value = {
            "pending": pending_count,
            "avg_complete_minutes": round(avg_complete, 1),
            "fail_rate": round(fail_rate, 1),
            "retry_rate": round(retry_rate, 1),
        }

        # 各子项状态取最严重
        statuses = [
            self._determine_status(
                pending_count,
                threshold.get("pending_count_yellow", 10),
                threshold.get("pending_count_red", 30),
                mode="higher_is_worse",
            ),
            self._determine_status(
                avg_complete,
                threshold.get("avg_complete_minutes_yellow", 60),
                threshold.get("avg_complete_minutes_red", 180),
                mode="higher_is_worse",
            ),
            self._determine_status(
                fail_rate,
                threshold.get("fail_rate_percent_yellow", 20),
                threshold.get("fail_rate_percent_red", 50),
                mode="higher_is_worse",
            ),
            self._determine_status(
                retry_rate,
                threshold.get("retry_rate_percent_yellow", 30),
                threshold.get("retry_rate_percent_red", 60),
                mode="higher_is_worse",
            ),
        ]
        status = _worst_status(statuses)

        detail_parts = [
            f"pending={pending_count}",
            f"平均完成={avg_complete:.1f}min",
            f"失败率={fail_rate:.1f}%",
            f"重试率={retry_rate:.1f}%",
        ]
        if status == STATUS_GREEN:
            detail = "健康运行（" + "，".join(detail_parts) + "）"
        elif status == STATUS_YELLOW:
            detail = "需关注（" + "，".join(detail_parts) + "）"
        else:
            detail = "异常告警（" + "，".join(detail_parts) + "）"

        return {
            "status": status,
            "value": value,
            "threshold": threshold,
            "detail": detail,
        }

    # ------------------------------------------------------------------
    # 2. 角色健康
    # ------------------------------------------------------------------
    def collect_role_health(self) -> dict:
        """采集角色健康指标。

        检查 7 个角色当日激活状态（看 task_queue 中 claimed_at 为今日的任务），
        统计各角色产出文件数（扫描 company/projects/ / company/knowledge/
        / company/marketing/ 等目录今日新增 .md 文件），
        返回每个角色的健康状态 + 总体状态。

        Returns:
            ``{status, value: {active_roles, total_roles, output_files_today, roles: [...]},
            threshold, detail}``
        """
        threshold = self._load_thresholds().get("role_health", {})
        today = date.today()

        try:
            from engine.task_queue import TaskQueue
            tq = TaskQueue(self._get_workspace())
            tasks = tq.list_all()
        except Exception as e:  # noqa: BLE001
            return {
                "status": STATUS_GREEN,
                "value": {
                    "active_roles": 0,
                    "total_roles": len(ROLES),
                    "output_files_today": 0,
                    "roles": [],
                },
                "threshold": threshold,
                "detail": f"任务队列读取失败：{e}",
            }

        # 各角色最后激活日期与今日产出文件数
        role_info: Dict[str, dict] = {}
        for role in ROLES:
            # 找出该角色所有有 claimed_at 的任务，取最新一次
            claimed_dates: List[date] = []
            for t in tasks:
                if t.get("assignee") != role:
                    continue
                claimed = self._parse_iso(t.get("claimed_at"))
                if claimed:
                    claimed_dates.append(claimed.date())
            last_active = max(claimed_dates) if claimed_dates else None
            # 未激活天数：从未激活视为很大（999）
            inactive_days = (today - last_active).days if last_active else 999

            # 当日产出文件数（扫描该角色主要产出目录今日新增 .md）
            output_files = self._count_role_files_today(role, today)

            role_info[role] = {
                "last_active": last_active.isoformat() if last_active else None,
                "inactive_days": inactive_days if last_active else None,
                "output_files_today": output_files,
                "activated_today": last_active == today,
            }

        # 判断每个角色状态（inactive_days + output_files_daily）
        role_statuses: Dict[str, str] = {}
        for role, info in role_info.items():
            inactive = info["inactive_days"]
            output = info["output_files_today"]

            # inactive_days：higher_is_worse（从未激活视为 999）
            s_inactive = self._determine_status(
                inactive if inactive is not None else 999,
                threshold.get("inactive_days_yellow", 1),
                threshold.get("inactive_days_red", 3),
                mode="higher_is_worse",
            )
            # output_files_daily 特殊语义：当日 0 产出为黄，连续 2 天 0 产出为红
            if output > 0:
                s_output = STATUS_GREEN
            else:
                # 当日 0 产出
                if (inactive is not None and inactive >= 2) or inactive is None:
                    s_output = STATUS_RED
                else:
                    s_output = STATUS_YELLOW
            role_statuses[role] = _worst_status([s_inactive, s_output])

        active_count = sum(1 for r in role_info.values() if r["activated_today"])
        total_files = sum(r["output_files_today"] for r in role_info.values())

        overall_status = _worst_status(list(role_statuses.values()))

        # 生成 detail
        inactive_role_names = [
            r for r in ROLES if not role_info[r]["activated_today"]
        ]
        if inactive_role_names:
            detail_inactive = f"未激活角色: {', '.join(inactive_role_names)}"
        else:
            detail_inactive = "全部角色已激活"
        detail = (
            f"{active_count}/{len(ROLES)} 角色激活，产出 {total_files} 文件；"
            f"{detail_inactive}"
        )

        return {
            "status": overall_status,
            "value": {
                "active_roles": active_count,
                "total_roles": len(ROLES),
                "output_files_today": total_files,
                "roles": [
                    {"role": r, "status": role_statuses[r], **role_info[r]}
                    for r in ROLES
                ],
            },
            "threshold": threshold,
            "detail": detail,
        }

    def _count_role_files_today(self, role: str, today: date) -> int:
        """统计指定角色主要产出目录中今日新增的 .md 文件数。

        Args:
            role: 角色名（如 programmer / coo）。
            today: 今日日期对象。

        Returns:
            今日新增 .md 文件数；目录不存在返回 0。
        """
        workspace = self._get_workspace()
        dirs_rel = _ROLE_OUTPUT_DIRS.get(role, [])
        count = 0
        for rel in dirs_rel:
            target_dir = workspace.root_dir / rel
            if not target_dir.exists():
                continue
            try:
                for p in target_dir.rglob("*.md"):
                    try:
                        mtime = datetime.fromtimestamp(p.stat().st_mtime).date()
                        if mtime == today:
                            count += 1
                    except OSError:
                        continue
            except Exception:  # noqa: BLE001 - 单目录扫描失败不阻塞
                continue
        return count

    # ------------------------------------------------------------------
    # 3. 财务健康
    # ------------------------------------------------------------------
    def collect_finance_health(self) -> dict:
        """采集财务健康指标。

        - 调用 ``engine.crypto.wallet.WalletManager`` 查询钱包余额
          （失败则降级读 ``company/config/wallet_balance_state.yaml``）
        - 统计当日真实收入（读 ledger.yaml 中 is_real=true 且 date=今日的交易）
        - 判断连续 0 收入天数（扫描最近 N 天 ledger 交易）

        Returns:
            ``{status, value: {balance, today_income, zero_income_days},
            threshold, detail}``
        """
        threshold = self._load_thresholds().get("finance_health", {})
        today_str = self._today_str()

        # 1. 钱包余额查询：优先 WalletManager，失败降级 wallet_balance_state.yaml
        balance: Optional[float] = None
        balance_source = "未知"
        try:
            from engine.crypto.wallet import WalletManager
            wm = WalletManager(self._get_workspace())
            wallets = wm.list_wallets()
            if wallets:
                # 多钱包场景取最大值作为可用余额
                max_balance = 0.0
                got = False
                for w in wallets:
                    addr = w.get("address", "")
                    chain = w.get("chain", "")
                    if not addr or not chain:
                        continue
                    res = wm.check_balance(addr, chain)
                    bal = res.get("balance") if isinstance(res, dict) else None
                    if bal is not None and isinstance(bal, (int, float)):
                        max_balance = max(max_balance, float(bal))
                        got = True
                if got:
                    balance = max_balance
                    balance_source = "WalletManager 在线查询"
        except Exception as e:  # noqa: BLE001 - WalletManager 失败优雅降级
            print(f"[health_monitor] WalletManager 查询失败: {e}", file=sys.stderr)

        # 降级：读 wallet_balance_state.yaml
        if balance is None:
            try:
                state_path = (
                    self._get_workspace().config_dir / "wallet_balance_state.yaml"
                )
                state = self._get_workspace().read_yaml(state_path)
                if state and isinstance(state, dict):
                    last_balance = state.get("last_balance")
                    if isinstance(last_balance, (int, float)):
                        balance = float(last_balance)
                        balance_source = "wallet_balance_state.yaml（离线缓存）"
            except Exception as e:  # noqa: BLE001
                print(f"[health_monitor] 余额状态读取失败: {e}", file=sys.stderr)

        if balance is None:
            balance = 0.0
            balance_source = "无法获取（默认 0）"

        # 2. 当日真实收入 + 连续 0 收入天数
        today_income = 0.0
        zero_income_days = 0
        try:
            ledger_path = self._get_workspace().config_dir / "ledger.yaml"
            data = self._get_workspace().read_yaml(ledger_path)
            transactions = (data or {}).get("transactions", []) or []
            # 真实收入按日期分组：{date_str: total_real_income}
            daily_real_income: Dict[str, float] = {}
            for tx in transactions:
                if not isinstance(tx, dict):
                    continue
                if tx.get("type") != "income":
                    continue
                if not tx.get("is_real", False):
                    continue
                ts = tx.get("timestamp", "")
                # ISO 8601 字符串前 10 位是日期
                tx_date = ts[:10] if isinstance(ts, str) and len(ts) >= 10 else ""
                if not tx_date:
                    continue
                try:
                    amount = float(tx.get("amount", 0) or 0)
                except (TypeError, ValueError):
                    amount = 0.0
                daily_real_income[tx_date] = (
                    daily_real_income.get(tx_date, 0.0) + amount
                )

            today_income = daily_real_income.get(today_str, 0.0)

            # 计算连续 0 收入天数（从今日往前扫描，遇到有真实收入的日期即停）
            today_date = date.today()
            for i in range(0, 31):  # 最多扫描 30 天，避免无交易时无限累加
                check_date = (today_date - timedelta(days=i)).isoformat()
                if (
                    check_date in daily_real_income
                    and daily_real_income[check_date] > 0
                ):
                    break
                zero_income_days = i + 1
        except Exception as e:  # noqa: BLE001
            print(f"[health_monitor] Ledger 读取失败: {e}", file=sys.stderr)

        value = {
            "balance": round(balance, 4),
            "today_income": round(today_income, 4),
            "zero_income_days": zero_income_days,
        }

        # 子项状态
        s_balance = self._determine_status(
            balance,
            threshold.get("wallet_balance_usd_yellow", 10),
            threshold.get("wallet_balance_usd_red", 1),
            mode="lower_is_worse",
        )
        s_zero_income = self._determine_status(
            zero_income_days,
            threshold.get("zero_income_days_yellow", 2),
            threshold.get("zero_income_days_red", 3),
            mode="higher_is_worse",
        )
        status = _worst_status([s_balance, s_zero_income])

        if status == STATUS_RED:
            detail = (
                f"触发危机警报（余额=${balance:.2f}，连续 {zero_income_days} 天 0 收入，"
                f"来源：{balance_source}）"
            )
        elif status == STATUS_YELLOW:
            detail = (
                f"财务预警（余额=${balance:.2f}，连续 {zero_income_days} 天 0 收入，"
                f"来源：{balance_source}）"
            )
        else:
            detail = (
                f"财务健康（余额=${balance:.2f}，今日真实收入=${today_income:.2f}，"
                f"来源：{balance_source}）"
            )

        return {
            "status": status,
            "value": value,
            "threshold": threshold,
            "detail": detail,
        }

    # ------------------------------------------------------------------
    # 4. 协作健康
    # ------------------------------------------------------------------
    def collect_collab_health(self) -> dict:
        """采集协作健康指标。

        - 调用 ``MessagePool.list_all_today()`` 统计消息数
        - 扫描 task_queue 中 status=blocked 的任务数（跨角色转交）
        - 统计今日 Phase 完成情况（读 ``company/messages/`` 中
          ``phase.done.*`` 消息数 vs 预期 Phase 数 6）

        Returns:
            ``{status, value: {message_count, handoff_count, phase_completion_rate},
            threshold, detail}``
        """
        threshold = self._load_thresholds().get("collab_health", {})

        # 1. 今日消息数 + Phase 完成消息数
        message_count = 0
        phase_done_count = 0
        try:
            mp = self._get_message_pool()
            if mp is not None:
                messages = mp.list_all_today() or []
                message_count = len(messages)
                # 统计 phase.done.* 消息数
                for m in messages:
                    topic = m.get("topic", "") if isinstance(m, dict) else ""
                    if isinstance(topic, str) and topic.startswith("phase.done."):
                        phase_done_count += 1
        except Exception as e:  # noqa: BLE001
            print(f"[health_monitor] 消息池读取失败: {e}", file=sys.stderr)

        # 2. 跨角色转交数（status=blocked 任务数）
        handoff_count = 0
        try:
            from engine.task_queue import TaskQueue
            tq = TaskQueue(self._get_workspace())
            blocked = tq.list_by_status("blocked")
            handoff_count = len(blocked)
        except Exception as e:  # noqa: BLE001
            print(f"[health_monitor] 任务队列读取失败: {e}", file=sys.stderr)

        # 3. Phase 完成率
        phase_completion_rate = (
            (phase_done_count / EXPECTED_PHASE_COUNT) * 100.0
            if EXPECTED_PHASE_COUNT > 0
            else 0.0
        )

        value = {
            "message_count": message_count,
            "handoff_count": handoff_count,
            "phase_completion_rate": round(phase_completion_rate, 1),
        }

        # 子项状态
        s_message = self._determine_status(
            message_count,
            threshold.get("message_pool_daily_yellow", 5),
            threshold.get("message_pool_daily_red", 1),
            mode="lower_is_worse",
        )
        s_handoff = self._determine_status(
            handoff_count,
            threshold.get("handoff_count_daily_yellow", 5),
            threshold.get("handoff_count_daily_red", 10),
            mode="higher_is_worse",
        )
        s_phase = self._determine_status(
            phase_completion_rate,
            threshold.get("phase_completion_rate_percent_yellow", 60),
            threshold.get("phase_completion_rate_percent_red", 30),
            mode="lower_is_worse",
        )
        status = _worst_status([s_message, s_handoff, s_phase])

        if status == STATUS_GREEN:
            detail = (
                f"协作顺畅（消息 {message_count} 条，转交 {handoff_count} 次，"
                f"Phase 完成率 {phase_completion_rate:.1f}%）"
            )
        elif status == STATUS_YELLOW:
            detail = (
                f"协作预警（消息 {message_count} 条，转交 {handoff_count} 次，"
                f"Phase 完成率 {phase_completion_rate:.1f}%）"
            )
        else:
            detail = (
                f"协作异常（消息 {message_count} 条，转交 {handoff_count} 次，"
                f"Phase 完成率 {phase_completion_rate:.1f}%）"
            )

        return {
            "status": status,
            "value": value,
            "threshold": threshold,
            "detail": detail,
        }

    # ------------------------------------------------------------------
    # 5. 服务健康
    # ------------------------------------------------------------------
    def collect_service_health(self) -> dict:
        """采集服务健康指标。

        - 扫描 ``company/orders/`` 下各状态子目录的订单数
        - 计算平均交付周期（``accepted_at - created_at`` 的天数均值）
        - 统计一次验收通过率（accepted 中无 rework 标记的比例）
        - 无订单时返回绿色默认值

        Returns:
            ``{status, value: {pending, avg_delivery_days, first_acceptance_rate},
            threshold, detail}``
        """
        threshold = self._load_thresholds().get("service_health", {})
        default_value = {
            "pending": 0,
            "avg_delivery_days": 0,
            "first_acceptance_rate": 100,
        }

        orders_dir = self._get_workspace().root_dir / "orders"
        if not orders_dir.exists():
            return {
                "status": STATUS_GREEN,
                "value": default_value,
                "threshold": threshold,
                "detail": "无订单数据（orders/ 目录不存在）",
            }

        # 状态子目录：未完成订单（pending = received/quoted/confirmed/in_progress/delivered）
        pending_statuses = ["received", "quoted", "confirmed", "in_progress", "delivered"]
        accepted_statuses = ["accepted", "paid", "closed"]
        pending_count = 0
        accepted_orders: List[dict] = []

        try:
            for status_name in pending_statuses + accepted_statuses:
                status_dir = orders_dir / status_name
                if not status_dir.exists():
                    continue
                for p in status_dir.glob("*.yaml"):
                    try:
                        order = self._get_workspace().read_yaml(p)
                        if not isinstance(order, dict):
                            continue
                        order.setdefault("_status", status_name)
                        if status_name in pending_statuses:
                            pending_count += 1
                        else:
                            accepted_orders.append(order)
                    except Exception:  # noqa: BLE001 - 单订单读取失败跳过
                        continue
        except Exception as e:  # noqa: BLE001
            return {
                "status": STATUS_GREEN,
                "value": default_value,
                "threshold": threshold,
                "detail": f"订单扫描失败：{e}",
            }

        # 无订单时绿色返回
        total_orders = pending_count + len(accepted_orders)
        if total_orders == 0:
            return {
                "status": STATUS_GREEN,
                "value": default_value,
                "threshold": threshold,
                "detail": "无订单数据",
            }

        # 平均交付周期：accepted_at - created_at 的天数均值
        delivery_days: List[float] = []
        for order in accepted_orders:
            created = self._parse_iso(order.get("created_at"))
            # accepted_at 可能在 events[] 里，也可能直接是字段
            accepted_at = order.get("accepted_at")
            if not accepted_at:
                # 从 events[] 中找 to_status=accepted 的事件 timestamp
                for ev in order.get("events", []) or []:
                    if isinstance(ev, dict) and ev.get("to_status") == "accepted":
                        accepted_at = ev.get("timestamp")
                        break
            accepted_dt = self._parse_iso(accepted_at)
            if created and accepted_dt:
                delta_days = (accepted_dt - created).total_seconds() / 86400.0
                if delta_days >= 0:
                    delivery_days.append(delta_days)
        avg_delivery = (
            sum(delivery_days) / len(delivery_days) if delivery_days else 0.0
        )

        # 一次验收通过率：accepted 中无 rework 标记的比例
        first_accept_count = 0
        for order in accepted_orders:
            has_rework = False
            # 检查 events[] 中是否有 rework 相关标记
            for ev in order.get("events", []) or []:
                if not isinstance(ev, dict):
                    continue
                ev_status = (
                    str(ev.get("to_status", "")) + str(ev.get("from_status", ""))
                )
                if "rework" in ev_status.lower():
                    has_rework = True
                    break
            # 也检查显式 rework_count 字段
            if (order.get("rework_count") or 0) > 0:
                has_rework = True
            if not has_rework:
                first_accept_count += 1
        first_acceptance_rate = (
            (first_accept_count / len(accepted_orders) * 100.0)
            if accepted_orders
            else 100.0
        )

        value = {
            "pending": pending_count,
            "avg_delivery_days": round(avg_delivery, 2),
            "first_acceptance_rate": round(first_acceptance_rate, 1),
        }

        # 子项状态
        s_pending = self._determine_status(
            pending_count,
            threshold.get("pending_orders_yellow", 3),
            threshold.get("pending_orders_red", 8),
            mode="higher_is_worse",
        )
        s_delivery = self._determine_status(
            avg_delivery,
            threshold.get("avg_delivery_days_yellow", 3),
            threshold.get("avg_delivery_days_red", 7),
            mode="higher_is_worse",
        )
        s_acceptance = self._determine_status(
            first_acceptance_rate,
            threshold.get("first_acceptance_rate_percent_yellow", 60),
            threshold.get("first_acceptance_rate_percent_red", 30),
            mode="lower_is_worse",
        )
        status = _worst_status([s_pending, s_delivery, s_acceptance])

        if status == STATUS_GREEN:
            detail = (
                f"服务健康（待交付 {pending_count} 单，平均交付 {avg_delivery:.1f} 天，"
                f"一次验收率 {first_acceptance_rate:.1f}%）"
            )
        elif status == STATUS_YELLOW:
            detail = (
                f"服务预警（待交付 {pending_count} 单，平均交付 {avg_delivery:.1f} 天，"
                f"一次验收率 {first_acceptance_rate:.1f}%）"
            )
        else:
            detail = (
                f"服务异常（待交付 {pending_count} 单，平均交付 {avg_delivery:.1f} 天，"
                f"一次验收率 {first_acceptance_rate:.1f}%）"
            )

        return {
            "status": status,
            "value": value,
            "threshold": threshold,
            "detail": detail,
        }

    # ------------------------------------------------------------------
    # 主入口：每日检查 + 报告生成
    # ------------------------------------------------------------------
    def run_daily_check(self) -> dict:
        """汇总 5 类健康指标，生成每日健康报告。

        - 任一指标红色时 publish ``health.alert.red`` 消息到消息池
        - 任一指标红色时调用 human_loop 通知用户
        - 报告落盘到 ``company/health/health-YYYY-MM-DD.md``
        - 任一采集方法失败不阻塞整体报告生成（用降级占位填充）

        Returns:
            ``{report_path, red_count, yellow_count, green_count, alerts: [...]}``
        """
        # 各类指标采集（独立 try/except，单类失败不阻塞）
        collectors: List[tuple] = [
            ("任务健康", "task", self.collect_task_health),
            ("角色健康", "role", self.collect_role_health),
            ("财务健康", "finance", self.collect_finance_health),
            ("协作健康", "collab", self.collect_collab_health),
            ("服务健康", "service", self.collect_service_health),
        ]
        results: Dict[str, dict] = {}
        alerts: List[str] = []
        for label, key, fn in collectors:
            try:
                results[key] = fn()
            except Exception as e:  # noqa: BLE001 - 单类采集失败优雅降级
                results[key] = {
                    "status": STATUS_GREEN,
                    "value": {},
                    "threshold": {},
                    "detail": f"采集异常（{label}）：{e}",
                }
                alerts.append(f"{label}采集异常：{e}")

        # 统计三色数量
        red_count = sum(1 for r in results.values() if r.get("status") == STATUS_RED)
        yellow_count = sum(
            1 for r in results.values() if r.get("status") == STATUS_YELLOW
        )
        green_count = sum(
            1 for r in results.values() if r.get("status") == STATUS_GREEN
        )

        # 生成报告
        today_str = self._today_str()
        report_path = (
            self._get_workspace().root_dir / "health" / f"health-{today_str}.md"
        )
        try:
            report_content = self._render_report(results, today_str)
            report_path.parent.mkdir(parents=True, exist_ok=True)
            report_path.write_text(report_content, encoding="utf-8")
        except Exception as e:  # noqa: BLE001
            alerts.append(f"报告生成失败：{e}")
            print(f"[health_monitor] 报告生成失败: {e}", file=sys.stderr)

        # 红色警报：publish + human_loop 通知
        if red_count > 0:
            # 收集红色项详情
            red_items = [
                {"category": label, "detail": results[key].get("detail", "")}
                for label, key, _ in collectors
                if results[key].get("status") == STATUS_RED
            ]
            alert_payload = {
                "red_count": red_count,
                "yellow_count": yellow_count,
                "green_count": green_count,
                "red_items": red_items,
                "report_path": str(report_path) if report_path.exists() else "",
                "generated_at": self._now_iso(),
            }
            # publish health.alert.red
            try:
                mp = self._get_message_pool()
                if mp is not None:
                    mp.publish(
                        topic="health.alert.red",
                        payload=alert_payload,
                        from_role="health_monitor",
                        to_role=None,
                    )
            except Exception as e:  # noqa: BLE001
                alerts.append(f"消息池 publish 失败：{e}")

            # human_loop 通知用户
            try:
                hl = self._get_human_loop()
                if hl is not None:
                    msg_lines = [f"健康监控红色警报：共 {red_count} 项指标亮红"]
                    for item in red_items:
                        msg_lines.append(f"- {item['category']}：{item['detail']}")
                    msg_lines.append("")
                    msg_lines.append(f"报告路径：{report_path}")
                    hl.request_assistance(
                        message="\n".join(msg_lines),
                        options=["已知悉", "立即处理", "稍后处理"],
                        context="health_monitor.run_daily_check",
                    )
            except Exception as e:  # noqa: BLE001
                alerts.append(f"human_loop 通知失败：{e}")

        return {
            "report_path": str(report_path) if report_path.exists() else "",
            "red_count": red_count,
            "yellow_count": yellow_count,
            "green_count": green_count,
            "alerts": alerts,
        }

    # ------------------------------------------------------------------
    # 报告渲染
    # ------------------------------------------------------------------
    def _render_report(self, results: Dict[str, dict], today_str: str) -> str:
        """渲染 Markdown 健康报告。

        Args:
            results: 5 类指标的采集结果，key 为 task/role/finance/collab/service。
            today_str: 今日 ``YYYY-MM-DD`` 字符串。

        Returns:
            Markdown 报告字符串（UTF-8）。
        """
        lines: List[str] = []
        lines.append(f"# AI 公司健康报告 - {today_str}")
        lines.append("")
        lines.append(f"> 生成时间：{self._now_iso()}")
        lines.append("")
        lines.append("## 健康仪表盘")
        lines.append("")
        lines.append("| 类别 | 状态 | 关键指标 | 详情 |")
        lines.append("|------|------|----------|------|")

        # 仪表盘行
        dash_rows: List[tuple] = [
            ("任务健康", "task", self._format_task_summary),
            ("角色健康", "role", self._format_role_summary),
            ("财务健康", "finance", self._format_finance_summary),
            ("协作健康", "collab", self._format_collab_summary),
            ("服务健康", "service", self._format_service_summary),
        ]
        for label, key, formatter in dash_rows:
            r = results.get(key, {})
            status = r.get("status", STATUS_GREEN)
            emoji = STATUS_EMOJI.get(status, "🟢")
            metrics = formatter(r.get("value", {}))
            detail = r.get("detail", "")
            lines.append(f"| {label} | {emoji} | {metrics} | {detail} |")

        lines.append("")
        lines.append("## 详细指标")
        lines.append("")

        # 详细指标：每类一个子节
        for label, key, _ in dash_rows:
            r = results.get(key, {})
            lines.append(f"### {label}")
            lines.append("")
            lines.append(
                f"- 状态：{STATUS_EMOJI.get(r.get('status', STATUS_GREEN), '🟢')} "
                f"{r.get('status', STATUS_GREEN)}"
            )
            lines.append(f"- 详情：{r.get('detail', '')}")
            value = r.get("value", {})
            if isinstance(value, dict) and value:
                lines.append("- 指标：")
                for k, v in value.items():
                    # 跳过 roles 列表（单独渲染）
                    if k == "roles":
                        continue
                    lines.append(f"  - {k}: {v}")
                # 角色健康含 roles 列表，单独渲染表格
                if key == "role" and isinstance(value.get("roles"), list):
                    lines.append("")
                    lines.append(
                        "| 角色 | 状态 | 当日激活 | 当日产出文件 | 上次激活 | 不活跃天数 |"
                    )
                    lines.append("|------|------|----------|--------------|----------|-----------|")
                    for role_info in value["roles"]:
                        r_emoji = STATUS_EMOJI.get(
                            role_info.get("status", STATUS_GREEN), "🟢"
                        )
                        last_active = role_info.get("last_active") or "无"
                        inactive = role_info.get("inactive_days")
                        if inactive is None:
                            inactive_str = "从未"
                        else:
                            inactive_str = str(inactive)
                        lines.append(
                            f"| {role_info.get('role', '')} | {r_emoji} "
                            f"| {'是' if role_info.get('activated_today') else '否'} "
                            f"| {role_info.get('output_files_today', 0)} "
                            f"| {last_active} | {inactive_str} |"
                        )
            # 阈值（如有）
            threshold = r.get("threshold")
            if isinstance(threshold, dict) and threshold:
                lines.append("")
                lines.append("- 阈值配置：")
                for k, v in threshold.items():
                    lines.append(f"  - `{k}`: {v}")
            lines.append("")

        # 红色警报汇总
        red_items = [
            (label, results[key])
            for label, key, _ in dash_rows
            if results.get(key, {}).get("status") == STATUS_RED
        ]
        lines.append("## 红色警报")
        lines.append("")
        if red_items:
            for label, r in red_items:
                lines.append(f"- **{label}**：{r.get('detail', '')}")
        else:
            lines.append("（无红色警报）")
        lines.append("")

        # 黄色提示
        yellow_items = [
            (label, results[key])
            for label, key, _ in dash_rows
            if results.get(key, {}).get("status") == STATUS_YELLOW
        ]
        if yellow_items:
            lines.append("## 黄色提示")
            lines.append("")
            for label, r in yellow_items:
                lines.append(f"- **{label}**：{r.get('detail', '')}")
            lines.append("")

        # 采集异常
        if any("采集异常" in (r.get("detail") or "") for r in results.values()):
            lines.append("## 采集异常")
            lines.append("")
            for label, key, _ in dash_rows:
                r = results.get(key, {})
                if "采集异常" in (r.get("detail") or ""):
                    lines.append(f"- **{label}**：{r.get('detail', '')}")
            lines.append("")

        lines.append("---")
        lines.append("")
        lines.append(
            f"*本报告由 HealthMonitor.run_daily_check() 自动生成于 {self._now_iso()}*"
        )
        lines.append("")
        return "\n".join(lines)

    # ------------------------------------------------------------------
    # 仪表盘摘要格式化
    # ------------------------------------------------------------------
    @staticmethod
    def _format_task_summary(value: dict) -> str:
        """任务健康摘要。"""
        if not value:
            return "-"
        return (
            f"pending={value.get('pending', 0)}, "
            f"平均完成={value.get('avg_complete_minutes', 0)}min, "
            f"失败率={value.get('fail_rate', 0)}%, "
            f"重试率={value.get('retry_rate', 0)}%"
        )

    @staticmethod
    def _format_role_summary(value: dict) -> str:
        """角色健康摘要。"""
        if not value:
            return "-"
        return (
            f"{value.get('active_roles', 0)}/{value.get('total_roles', 0)} 角色激活，"
            f"产出 {value.get('output_files_today', 0)} 文件"
        )

    @staticmethod
    def _format_finance_summary(value: dict) -> str:
        """财务健康摘要。"""
        if not value:
            return "-"
        return (
            f"余额=${value.get('balance', 0)}, "
            f"今日收入=${value.get('today_income', 0)}, "
            f"连续 {value.get('zero_income_days', 0)} 天 0 收入"
        )

    @staticmethod
    def _format_collab_summary(value: dict) -> str:
        """协作健康摘要。"""
        if not value:
            return "-"
        return (
            f"消息 {value.get('message_count', 0)} 条, "
            f"转交 {value.get('handoff_count', 0)} 次, "
            f"Phase 完成率 {value.get('phase_completion_rate', 0)}%"
        )

    @staticmethod
    def _format_service_summary(value: dict) -> str:
        """服务健康摘要。"""
        if not value:
            return "-"
        return (
            f"待交付 {value.get('pending', 0)} 单, "
            f"平均交付 {value.get('avg_delivery_days', 0)} 天, "
            f"一次验收率 {value.get('first_acceptance_rate', 100)}%"
        )
