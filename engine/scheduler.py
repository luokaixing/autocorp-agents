"""定时调度器

每日 08:00 (Asia/Shanghai) 触发产研同步会，并在 12:00 / 18:00 触发
AI 公司每日 3 次自主运营循环（AutonomousLoop）。

提供两种启动方式：
  - start()：非阻塞，仅注册定时任务，由调用方自行驱动事件循环。
  - start_blocking()：注册任务后进入阻塞循环，持续运行调度。

另外提供 trigger_now() 供命令行立即触发一次会议（调试用），
trigger_full_day_now() 立即跑一次完整自主日。
"""
from __future__ import annotations

import schedule
import time
from datetime import datetime
from typing import Optional

from engine.workspace import WorkspaceManager


class Scheduler:
    """定时调度器 - 每日 3 次自主运营循环 + 季度战略会。"""

    # 会议固定时间与时区
    MEETING_TIME = "08:00"
    TIMEZONE = "Asia/Shanghai"
    # 每日自主运营循环时间（会议后 5 分钟）
    # 保留 08:05 的 daily_ops 与 08:00 的 meeting 仅作兼容，
    # 实际可被 08:00 的 morning loop 替代（morning loop 内部已包含 Meeting.run）
    DAILY_OPS_TIME = "08:05"
    # 12:00 执行批次
    NOON_TIME = "12:00"
    # 18:00 复盘循环
    EVENING_TIME = "18:00"
    # 16:00 钱包到账额外检查批次（SubTask 7.4）
    # spec 要求监控频率 08/12/16/20 时；08/12/18 已在 morning/noon/evening 三批次内，
    # 此处新增 16:00 额外触发点，由 IncomeMonitor.check_inbound() 执行
    WALLET_CHECK_TIME = "16:00"
    # 季度战略会固定时间与触发月份
    STRATEGY_TIME = "09:00"
    STRATEGY_MONTHS = (1, 4, 7, 10)  # 季度初月份

    def __init__(self, workspace: Optional[WorkspaceManager] = None):
        from engine.workspace import WorkspaceManager
        self.workspace = workspace or WorkspaceManager()

    # ------------------------------------------------------------------
    # 启动方式
    # ------------------------------------------------------------------
    def start(self) -> None:
        """非阻塞启动：注册每日定时任务，方法立即返回。

        注册 6 类任务：
          - 每日 08:00 触发产研同步会（兼容保留，可被 morning loop 替代）
          - 每日 08:00 触发晨会循环（AutonomousLoop.run_morning）
          - 每日 08:05 触发 daily_ops（兼容保留，可被 morning loop 替代）
          - 每日 09:00 检查是否为季度初（1/4/7/10 月 1 日），是则触发季度战略会
          - 每日 12:00 触发执行批次（AutonomousLoop.run_noon）
          - 每日 16:00 触发钱包到账额外检查（IncomeMonitor.check_inbound，SubTask 7.4）
          - 每日 18:00 触发复盘循环（AutonomousLoop.run_evening）

        注意：本方法仅注册任务，不进入调度循环。调用方需自行调用
        schedule.run_pending() 或改用 start_blocking()。
        """
        # 兼容保留：08:00 meeting + 08:05 daily_ops
        # 实际可被下面的 _run_morning_loop 替代（morning loop 内部已调用 Meeting.run + DailyOps）
        schedule.every().day.at(self.MEETING_TIME).do(self._run_meeting)
        schedule.every().day.at(self.DAILY_OPS_TIME).do(self._run_daily_ops)
        # 新增：08:00 / 12:00 / 18:00 三次自主运营循环
        schedule.every().day.at(self.MEETING_TIME).do(self._run_morning_loop)
        schedule.every().day.at(self.NOON_TIME).do(self._run_noon_loop)
        schedule.every().day.at(self.EVENING_TIME).do(self._run_evening_loop)
        # 第一桶金：16:00 钱包到账额外检查批次（SubTask 7.4）
        # spec 要求监控频率 08/12/16/20 时；16:00 为独立触发点
        schedule.every().day.at(self.WALLET_CHECK_TIME).do(self._run_wallet_check)
        # 季度战略会
        schedule.every().day.at(self.STRATEGY_TIME).do(self._check_quarterly_strategy)
        print(
            f"调度器已启动：每日 {self.MEETING_TIME} 触发晨会循环；"
            f"每日 {self.NOON_TIME} 触发执行批次；"
            f"每日 {self.EVENING_TIME} 触发复盘循环；"
            f"每日 {self.WALLET_CHECK_TIME} 触发钱包到账检查；"
            f"（兼容保留 {self.MEETING_TIME} meeting + {self.DAILY_OPS_TIME} daily_ops）；"
            f"季度初（{self.STRATEGY_MONTHS} 月 1 日 {self.STRATEGY_TIME}）触发战略会"
        )

    def start_blocking(self) -> None:
        """启动并阻塞：注册任务后持续运行调度循环。

        每 60 秒检查一次待执行任务；捕获 KeyboardInterrupt 优雅退出。
        """
        self.start()
        print("进入调度循环，按 Ctrl+C 退出...")
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            print("\n调度器已停止。")

    # ------------------------------------------------------------------
    # 会议执行
    # ------------------------------------------------------------------
    def _run_meeting(self) -> None:
        """实际执行会议：实例化 Meeting 并运行，同时记录日志到 reports/。"""
        from engine.meeting import Meeting

        start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{start_ts}] 开始执行产研同步会...")

        try:
            meeting = Meeting(workspace=self.workspace)
            minutes_path = meeting.run()
            self._log(f"{start_ts} 会议完成，纪要：{minutes_path}")
            print(f"会议纪要已生成：{minutes_path}")
        except Exception as e:
            self._log(f"{start_ts} 会议执行失败：{e}")
            print(f"会议执行失败：{e}")

    def trigger_now(self) -> None:
        """立即触发一次会议（供 main.py meeting --now 调用）。"""
        self._run_meeting()

    # ------------------------------------------------------------------
    # 每日自主运营循环
    # ------------------------------------------------------------------
    def _run_daily_ops(self) -> None:
        """每日自主运营循环：钱包/内容/市场扫描 + 决策清单 + 意识流。"""
        from engine.daily_ops import DailyOps

        start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{start_ts}] 开始执行每日自主运营循环...")

        try:
            ops = DailyOps(workspace=self.workspace)
            report_path = ops.run()
            self._log(f"{start_ts} 自主运营循环完成，报告：{report_path}")
            print(f"运营日报已生成：{report_path}")
        except Exception as e:
            self._log(f"{start_ts} 自主运营循环失败：{e}")
            print(f"自主运营循环失败：{e}")

    def trigger_daily_ops_now(self) -> None:
        """立即触发一次自主运营循环。"""
        self._run_daily_ops()

    # ------------------------------------------------------------------
    # 自主运营循环（AutonomousLoop 三批次）
    # ------------------------------------------------------------------
    def _run_morning_loop(self) -> None:
        """08:00 晨会循环：meeting + CEO 自主决策 + PM 市场扫描。"""
        from engine.autonomous_loop import AutonomousLoop

        start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{start_ts}] 开始执行晨会循环（AutonomousLoop.run_morning）...")
        try:
            loop = AutonomousLoop(self.workspace)
            result = loop.run_morning()
            self._log(
                f"{start_ts} 晨会循环完成：meeting={result.get('meeting_path','')}, "
                f"pm_scan={result.get('pm_scan_path','')}, "
                f"decisions={result.get('decisions_path','')}, "
                f"errors={len(result.get('errors', []))}"
            )
            print(
                f"晨会循环完成：会议纪要={result.get('meeting_path','')}; "
                f"决策清单={result.get('decisions_path','')}; "
                f"异常数={len(result.get('errors', []))}"
            )
        except Exception as e:  # noqa: BLE001 - 失败记录不阻断调度
            self._log(f"{start_ts} 晨会循环失败：{e}")
            print(f"晨会循环失败：{e}")

    def _run_noon_loop(self) -> None:
        """12:00 执行批次：TaskExecutor.run_batch。"""
        from engine.autonomous_loop import AutonomousLoop

        start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{start_ts}] 开始执行执行批次（AutonomousLoop.run_noon）...")
        try:
            loop = AutonomousLoop(self.workspace)
            result = loop.run_noon()
            batch = result.get("batch", {}) or {}
            self._log(
                f"{start_ts} 执行批次完成：success={batch.get('success', 0)}, "
                f"failed={batch.get('failed', 0)}, skipped={batch.get('skipped', 0)}, "
                f"errors={len(result.get('errors', []))}"
            )
            print(
                f"执行批次完成：success={batch.get('success', 0)}, "
                f"failed={batch.get('failed', 0)}, skipped={batch.get('skipped', 0)}"
            )
        except Exception as e:  # noqa: BLE001
            self._log(f"{start_ts} 执行批次失败：{e}")
            print(f"执行批次失败：{e}")

    def _run_evening_loop(self) -> None:
        """18:00 复盘循环：KPI 看板 + 运营日报 + 复盘日志。"""
        from engine.autonomous_loop import AutonomousLoop

        start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{start_ts}] 开始执行复盘循环（AutonomousLoop.run_evening）...")
        try:
            loop = AutonomousLoop(self.workspace)
            result = loop.run_evening()
            self._log(
                f"{start_ts} 复盘循环完成：review={result.get('review_path','')}, "
                f"daily_ops={result.get('daily_ops_path','')}, "
                f"produced={len(result.get('produced_files', []))}, "
                f"errors={len(result.get('errors', []))}"
            )
            print(
                f"复盘循环完成：复盘日志={result.get('review_path','')}; "
                f"今日自主产出={len(result.get('produced_files', []))} 个文件"
            )
        except Exception as e:  # noqa: BLE001
            self._log(f"{start_ts} 复盘循环失败：{e}")
            print(f"复盘循环失败：{e}")

    def _run_wallet_check(self) -> None:
        """16:00 钱包到账额外检查批次（SubTask 7.4）。

        调用 IncomeMonitor.check_inbound() 检查 ETH 钱包余额变化，
        到账即触发账本记录 + KPI 更新 + 里程碑写入。

        spec 要求监控频率 08/12/16/20 时；08/12/18 已在 morning/noon/evening
        三批次内执行，此处为 16:00 独立触发点，确保每 4 小时一次的监控密度。
        """
        from engine.crypto.income_monitor import IncomeMonitor

        start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{start_ts}] 开始执行钱包到账检查（IncomeMonitor.check_inbound）...")
        try:
            monitor = IncomeMonitor(self.workspace)
            result = monitor.check_inbound() or {}
            delta = result.get("delta", 0.0)
            current = result.get("current")
            is_first = result.get("is_first_income", False)
            self._log(
                f"{start_ts} 钱包到账检查完成：current={current}, "
                f"delta={delta}, is_first_income={is_first}"
            )
            if delta and delta > 0:
                print(
                    f"钱包到账检查完成：本次到账 {delta} ETH，"
                    f"当前余额 {current} ETH"
                )
            else:
                print(f"钱包到账检查完成：当前余额 {current} ETH，本次无新到账")
        except Exception as e:  # noqa: BLE001 - 失败记录不阻断调度
            self._log(f"{start_ts} 钱包到账检查失败：{e}")
            print(f"钱包到账检查失败：{e}")

    def trigger_full_day_now(self) -> None:
        """立即跑一次完整自主日（morning → noon → evening），供 CLI 调用。"""
        from engine.autonomous_loop import AutonomousLoop

        start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{start_ts}] 立即触发完整自主日...")
        try:
            loop = AutonomousLoop(self.workspace)
            result = loop.run_full_day()
            self._log(
                f"{start_ts} 完整自主日完成："
                f"morning_errors={len(result.get('morning', {}).get('errors', []))}, "
                f"noon_errors={len(result.get('noon', {}).get('errors', []))}, "
                f"evening_errors={len(result.get('evening', {}).get('errors', []))}, "
                f"batch_errors={len(result.get('errors', []))}"
            )
            print("完整自主日完成。")
        except Exception as e:  # noqa: BLE001
            self._log(f"{start_ts} 完整自主日失败：{e}")
            print(f"完整自主日失败：{e}")

    # ------------------------------------------------------------------
    # 季度战略会
    # ------------------------------------------------------------------
    def _check_quarterly_strategy(self) -> None:
        """检查今日是否为季度初（1/4/7/10 月 1 日），是则触发季度战略会。"""
        today = datetime.now()
        if today.day == 1 and today.month in self.STRATEGY_MONTHS:
            self._run_quarterly_strategy()

    def _run_quarterly_strategy(self) -> None:
        """实际执行季度战略会：实例化 CEO 并调用 quarterly_strategy()。"""
        from engine.agents.ceo import CEO

        start_ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        print(f"[{start_ts}] 开始执行季度战略会...")

        try:
            ceo = CEO(self.workspace)
            result = ceo.quarterly_strategy()
            doc = result.get("strategy_doc", "")
            self._log(f"{start_ts} 季度战略会完成，文档：{doc}")
            print(f"战略文档已生成：{doc}")
        except Exception as e:
            self._log(f"{start_ts} 季度战略会执行失败：{e}")
            print(f"季度战略会执行失败：{e}")

    def trigger_strategy_now(self) -> None:
        """立即触发一次季度战略会（供 main.py strategy --now 调用）。"""
        self._run_quarterly_strategy()

    # ------------------------------------------------------------------
    # 日志
    # ------------------------------------------------------------------
    def _log(self, message: str) -> None:
        """将一行日志追加写入 reports/scheduler.log。"""
        log_path = self.workspace.reports_dir / "scheduler.log"
        self.workspace.ensure_dir(self.workspace.reports_dir)
        # 追加写入，自动换行
        with log_path.open("a", encoding="utf-8") as f:
            f.write(message + "\n")
