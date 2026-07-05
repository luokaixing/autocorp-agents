"""AI 公司每日 3 次自主运营循环

将一天拆为 3 个独立批次：
- 08:00 晨会循环（meeting + CEO 自主决策 + PM 市场扫描）
- 12:00 执行批次（TaskExecutor.run_batch）
- 18:00 复盘循环（KPI 看板 + 运营日报 + 复盘日志）

每批次独立 try/except，单批次失败不阻断后续批次；
批次内部各步骤也独立 try/except，保证单步失败不中断整批。

Phase 2 升级（standardize-ai-company-ops Task 4）：内部改为调用 PhaseChain
编排器，保留 ``run_morning`` / ``run_noon`` / ``run_evening`` / ``run_full_day``
方法签名向后兼容。PhaseChain 负责按 7 个标准 Phase 串行编排并 publish
``phase.done.*`` 消息，本类负责追加各批次的扩展逻辑（机会雷达 / Learn&Earn /
AirdropTracker / CEO 战略复盘 / IncomeMonitor 等）。

调用方式：
    py main.py autonomous-run                # 跑完整自主日
    py main.py autonomous-run --morning      # 只跑晨会循环
    py main.py autonomous-run --noon         # 只跑执行批次
    py main.py autonomous-run --evening      # 只跑复盘循环
"""
from __future__ import annotations

from datetime import datetime
from pathlib import Path
from typing import List

from engine.workspace import WorkspaceManager


class AutonomousLoop:
    """AI 公司每日 3 次自主运营循环。"""

    def __init__(self, workspace=None, llm_client=None):
        from engine.llm_client import default_client
        self.workspace = workspace or WorkspaceManager()
        self.llm_client = llm_client or default_client
        # Phase 2：注入 PhaseChain 编排器（延迟实例化避免循环依赖）
        try:
            from engine.phase_chain import PhaseChain
            self.phase_chain = PhaseChain(self.workspace, self.llm_client)
        except Exception as e:  # noqa: BLE001 - PhaseChain 初始化失败降级到原逻辑
            print(f"[autonomous_loop] PhaseChain 初始化失败，降级到原逻辑: {e}")
            self.phase_chain = None

    # ==================================================================
    # 08:00 晨会循环
    # ==================================================================
    def run_morning(self) -> dict:
        """08:00 晨会循环。

        Phase 2 升级：内部改为调用 ``PhaseChain.run_morning_chain()`` 串联
        Phase-Morning → Phase-Research → Phase-Design，再追加机会雷达 /
        Learn & Earn 等已有扩展逻辑（保留 SubTask 7.1 等扩展）。

        依次执行：
        1. PhaseChain.run_morning_chain()（含 Meeting + CEO 决策 + PM 扫描 + Architect 设计）
        2. 生成晨会决策清单（_write_morning_decisions）
        3. 第一桶金机会雷达扫描（OpportunityRadar.scan_all_channels）
        4. Learn & Earn 答题指南批量产出（LearnEarnAssistant.batch_generate）
        5. 实时机会扫描（RealtimeOpportunityScanner.generate_report）

        每步独立 try/except，单步失败不阻断后续。
        返回 {meeting_path, ceo_decisions, pm_scan_path, decisions_path,
              radar_opportunities, learn_earn_guides, realtime_scan_path,
              errors: [...]}
        """
        result = {
            "meeting_path": "",
            "ceo_decisions": {},
            "pm_scan_path": "",
            "decisions_path": "",
            # 第一桶金相关新增字段（SubTask 7.1）
            "radar_opportunities": [],
            "learn_earn_guides": [],
            # 实时机会扫描报告路径（Task 6.4：晨会新增实时机会扫描）
            "realtime_scan_path": "",
            "errors": [],
        }
        today = datetime.now().strftime("%Y-%m-%d")

        # 1. PhaseChain 晨间链：Phase-Morning → Phase-Research → Phase-Design
        # PhaseChain 内部已调用 Meeting / AutonomousCEO / ProductManager / Architect
        # 失败降级到原逐个调用逻辑（保证向后兼容）
        phase_results: dict = {}
        if self.phase_chain is not None:
            try:
                phase_results = self.phase_chain.run_morning_chain()
                # 提取各 Phase 产出
                morning_out = (
                    phase_results.get("phases", {}).get("Phase-Morning", {}).get("outputs", {})
                )
                research_out = (
                    phase_results.get("phases", {}).get("Phase-Research", {}).get("outputs", {})
                )
                design_out = (
                    phase_results.get("phases", {}).get("Phase-Design", {}).get("outputs", {})
                )
                if morning_out.get("meeting_path"):
                    result["meeting_path"] = morning_out["meeting_path"]
                if morning_out.get("ceo_decisions"):
                    result["ceo_decisions"] = morning_out["ceo_decisions"]
                if research_out.get("pm_scan_path"):
                    result["pm_scan_path"] = research_out["pm_scan_path"]
                if design_out.get("architecture_path"):
                    result["architecture_path"] = design_out["architecture_path"]
                # 合并 PhaseChain 的 errors
                for err in (phase_results.get("errors") or []):
                    result["errors"].append(err)
            except Exception as e:  # noqa: BLE001 - PhaseChain 失败降级到原逻辑
                print(f"[autonomous_loop] PhaseChain 晨间链异常，降级到原逻辑: {e}")
                result["errors"].append(f"phase_chain_morning: {e}")
                phase_results = {}

        # 1.1 降级路径：PhaseChain 不可用或失败时，按原逻辑逐个调用
        if not result["meeting_path"]:
            try:
                from engine.meeting import Meeting
                meeting = Meeting(self.workspace, self.llm_client)
                result["meeting_path"] = meeting.run()
            except Exception as e:  # noqa: BLE001 - 单步失败不阻断
                result["errors"].append(f"meeting: {e}")

        if not result["ceo_decisions"]:
            try:
                from engine.agents.ceo_autonomous import AutonomousCEO
                ceo = AutonomousCEO(self.workspace, self.llm_client)
                result["ceo_decisions"] = ceo.run_daily_decision()
            except Exception as e:  # noqa: BLE001
                result["errors"].append(f"ceo_daily_decision: {e}")

        if not result["pm_scan_path"]:
            try:
                from engine.agents import ProductManager
                pm = ProductManager(self.workspace, self.llm_client)
                scan = pm.scan_market()
                # 落盘报告到 knowledge/market-research/pm-scan-YYYY-MM-DD.md
                report = scan.get("report", "")
                scan_path = self.workspace.market_research_dir / f"pm-scan-{today}.md"
                self.workspace.write_text(scan_path, report)
                result["pm_scan_path"] = str(scan_path.resolve())
            except Exception as e:  # noqa: BLE001
                result["errors"].append(f"pm_scan: {e}")

        # 2. 生成晨会决策清单（汇总当日 CEO 立项 + 队列 pending 任务）
        try:
            result["decisions_path"] = self._write_morning_decisions(today, result)
        except Exception as e:  # noqa: BLE001
            result["errors"].append(f"morning_decisions: {e}")

        # 3. 第一桶金机会雷达扫描（SubTask 7.1）
        # 延迟导入避免循环依赖；失败仅打印警告不阻断主流程
        try:
            from engine.crypto.opportunity_radar import OpportunityRadar

            radar = OpportunityRadar(self.workspace, self.llm_client)
            result["radar_opportunities"] = radar.scan_all_channels() or []
        except Exception as e:  # noqa: BLE001 - 优雅降级
            print(f"[autonomous_loop] 机会雷达扫描失败：{e}")
            result["errors"].append(f"opportunity_radar: {e}")

        # 4. Learn & Earn 答题指南批量产出（SubTask 7.1）
        # 复用 OpportunityRadar 课程列表，逐课程生成答题指南；失败不阻断
        try:
            from engine.crypto.learn_earn_assistant import LearnEarnAssistant

            assistant = LearnEarnAssistant(self.workspace, self.llm_client)
            result["learn_earn_guides"] = assistant.batch_generate() or []
        except Exception as e:  # noqa: BLE001 - 优雅降级
            print(f"[autonomous_loop] Learn & Earn 答题指南产出失败：{e}")
            result["errors"].append(f"learn_earn_assistant: {e}")

        # 5. 实时机会扫描（Task 6.4：晨会新增实时机会扫描）
        # 验证 5 个平台当日可访问性并产出报告；失败仅打印警告不阻断晨会其他环节
        try:
            from engine.crypto.realtime_opportunity_scanner import RealtimeOpportunityScanner

            scanner = RealtimeOpportunityScanner()
            result["realtime_scan_path"] = scanner.generate_report() or ""
        except Exception as e:  # noqa: BLE001 - 优雅降级：失败不影响晨会其他环节
            print(f"[autonomous_loop] 实时机会扫描失败：{e}")
            result["errors"].append(f"realtime_opportunity_scanner: {e}")

        return result

    # ==================================================================
    # 12:00 执行批次
    # ==================================================================
    def run_noon(self) -> dict:
        """12:00 执行批次。

        Phase 2 升级：内部改为调用 ``PhaseChain.run_noon_chain()`` 串联
        Phase-Build → Phase-Promote，再追加 AirdropTracker / CEO 战略复盘等
        已有扩展逻辑。

        调用 TaskExecutor.run_batch(max_tasks=10)。
        TaskExecutor 内部会自动认领/执行/钩子触发，Programmer/COO 等
        角色的 execute_task 会调用 develop_from_task / execute_promotion
        产出文章与推广物料。

        随后追加第一桶金相关环节（SubTask 7.2）：
        - AirdropTracker.generate_tracker_report() 更新空投进度看板

        每个新增环节独立 try/except，失败仅打印警告不阻断主流程。
        返回 executor 的返回值 + 空投看板路径 + 任何错误。
        """
        result = {"batch": {}, "airdrop_tracker_report": "", "errors": []}

        # 1. PhaseChain 午间链：Phase-Build → Phase-Promote
        # PhaseChain 内部已调用 TaskExecutor.run_batch 与 COO 推广任务
        phase_executed = False
        if self.phase_chain is not None:
            try:
                phase_results = self.phase_chain.run_noon_chain()
                build_out = (
                    phase_results.get("phases", {}).get("Phase-Build", {}).get("outputs", {})
                )
                promote_out = (
                    phase_results.get("phases", {}).get("Phase-Promote", {}).get("outputs", {})
                )
                if build_out.get("batch"):
                    result["batch"] = build_out["batch"]
                    phase_executed = True
                if promote_out.get("promo_paths"):
                    result["promo_paths"] = promote_out["promo_paths"]
                if promote_out.get("batch"):
                    # Phase-Promote 兜底 TaskExecutor 的批次也合并
                    if not result["batch"]:
                        result["batch"] = promote_out["batch"]
                # 合并 PhaseChain 的 errors
                for err in (phase_results.get("errors") or []):
                    result["errors"].append(err)
            except Exception as e:  # noqa: BLE001 - PhaseChain 失败降级到原逻辑
                print(f"[autonomous_loop] PhaseChain 午间链异常，降级到原逻辑: {e}")
                result["errors"].append(f"phase_chain_noon: {e}")

        # 1.1 降级路径：PhaseChain 不可用或未执行 batch 时，按原逻辑调用 TaskExecutor
        if not phase_executed or not result["batch"]:
            try:
                from engine.task_executor import TaskExecutor
                executor = TaskExecutor(self.workspace, self.llm_client)
                result["batch"] = executor.run_batch(max_tasks=10)
            except Exception as e:  # noqa: BLE001
                result["errors"].append(f"task_executor: {e}")

        # 2. 第一桶金：空投任务进度看板更新（SubTask 7.2）
        # 延迟导入避免循环依赖；失败仅打印警告不阻断主流程
        try:
            from engine.crypto.airdrop_tracker import AirdropTracker

            tracker = AirdropTracker(self.workspace, self.llm_client)
            result["airdrop_tracker_report"] = tracker.generate_tracker_report() or ""
        except Exception as e:  # noqa: BLE001 - 优雅降级
            print(f"[autonomous_loop] 空投进度看板更新失败：{e}")
            result["errors"].append(f"airdrop_tracker: {e}")

        # 3. CEO 战略复盘（2026-06-28 升级）
        # 执行批次后让 CEO 主动生成看板 + 推送建议行动清单
        try:
            from engine.agents.ceo_autonomous import AutonomousCEO
            ceo = AutonomousCEO(self.workspace, self.llm_client)
            review = ceo.run_strategic_review()
            result["ceo_review"] = review
            actions = review.get("actions", []) or []
            if actions:
                print(f"[autonomous_loop] CEO 推送 {len(actions)} 条建议行动:")
                for a in actions[:3]:  # 只打印前 3 条
                    print(f"  [{a.get('priority', '')}] {a.get('action', '')}")
        except Exception as e:  # noqa: BLE001 - 优雅降级
            print(f"[autonomous_loop] CEO 战略复盘失败：{e}")
            result["errors"].append(f"ceo_strategic_review: {e}")

        return result

    # ==================================================================
    # 18:00 复盘循环
    # ==================================================================
    def run_evening(self) -> dict:
        """18:00 复盘循环。

        Phase 2 升级：内部改为调用 ``PhaseChain.run_evening_chain()`` 执行
        Phase-Review（含 KPI 看板 + 运营日报 + HealthMonitor），再追加
        _scan_today_productions / _write_evening_review / IncomeMonitor 等已有
        扩展逻辑。

        依次执行：
        1. PhaseChain.run_evening_chain()（含 KPI + DailyOps + HealthMonitor）
        2. 扫描今日自主产出（_scan_today_productions）
        3. 写复盘日志到 company/operations/evening-review-YYYY-MM-DD.md
        4. 钱包到账检查（IncomeMonitor.check_inbound）+ 第一桶金进度报告（SubTask 7.3）

        返回 {kpi_dashboard, daily_ops_path, review_path, produced_files,
              income_check, errors: [...]}
        """
        result = {
            "kpi_dashboard": "",
            "daily_ops_path": "",
            "review_path": "",
            "produced_files": [],
            # 第一桶金相关新增字段（SubTask 7.3）
            "income_check": {},
            "errors": [],
        }
        today = datetime.now().strftime("%Y-%m-%d")

        # 1. PhaseChain 晚间链：Phase-Review（KPI + DailyOps + HealthMonitor）
        if self.phase_chain is not None:
            try:
                phase_results = self.phase_chain.run_evening_chain()
                review_out = (
                    phase_results.get("phases", {}).get("Phase-Review", {}).get("outputs", {})
                )
                if review_out.get("kpi_dashboard"):
                    result["kpi_dashboard"] = review_out["kpi_dashboard"]
                if review_out.get("daily_ops_path"):
                    result["daily_ops_path"] = review_out["daily_ops_path"]
                if review_out.get("health_report"):
                    result["health_report"] = review_out["health_report"]
                # 合并 PhaseChain 的 errors
                for err in (phase_results.get("errors") or []):
                    result["errors"].append(err)
            except Exception as e:  # noqa: BLE001 - PhaseChain 失败降级到原逻辑
                print(f"[autonomous_loop] PhaseChain 晚间链异常，降级到原逻辑: {e}")
                result["errors"].append(f"phase_chain_evening: {e}")

        # 1.1 降级路径：PhaseChain 不可用或未产出 KPI 看板时，按原逻辑调用
        if not result["kpi_dashboard"]:
            try:
                from engine.agents.role_kpi import KPITracker
                tracker = KPITracker(self.workspace)
                result["kpi_dashboard"] = tracker.generate_kpi_dashboard()
            except Exception as e:  # noqa: BLE001
                result["errors"].append(f"kpi_dashboard: {e}")

        if not result["daily_ops_path"]:
            try:
                from engine.daily_ops import DailyOps
                ops = DailyOps(self.workspace)
                result["daily_ops_path"] = ops.run()
            except Exception as e:  # noqa: BLE001
                result["errors"].append(f"daily_ops: {e}")

        # 2. 扫描今日自主产出（articles/ + marketing/ 目录的今日新增文件）
        result["produced_files"] = self._scan_today_productions()

        # 3. 写复盘日志
        try:
            result["review_path"] = self._write_evening_review(today, result)
        except Exception as e:  # noqa: BLE001
            result["errors"].append(f"evening_review: {e}")

        # 4. 钱包到账检查 + 第一桶金进度报告（SubTask 7.3）
        # 延迟导入避免循环依赖；失败仅打印警告不阻断主流程
        try:
            from engine.crypto.income_monitor import IncomeMonitor

            monitor = IncomeMonitor(self.workspace, self.llm_client)
            income_result = monitor.check_inbound() or {}
            result["income_check"] = income_result
            # 输出第一桶金进度报告（简单打印关键指标）
            self._print_first_income_progress(income_result)
        except Exception as e:  # noqa: BLE001 - 优雅降级
            print(f"[autonomous_loop] 钱包到账检查失败：{e}")
            result["errors"].append(f"income_monitor: {e}")

        return result

    # ==================================================================
    # 完整自主日（顺序执行 morning → noon → evening）
    # ==================================================================
    def run_full_day(self) -> dict:
        """顺序执行 morning → noon → evening，供手动触发。

        每批次独立 try/except，单批次失败不阻断后续。
        返回 {morning: ..., noon: ..., evening: ..., errors: [...]}
        """
        result = {"morning": {}, "noon": {}, "evening": {}, "errors": []}

        try:
            result["morning"] = self.run_morning()
        except Exception as e:  # noqa: BLE001
            result["errors"].append(f"morning_batch: {e}")

        try:
            result["noon"] = self.run_noon()
        except Exception as e:  # noqa: BLE001
            result["errors"].append(f"noon_batch: {e}")

        try:
            result["evening"] = self.run_evening()
        except Exception as e:  # noqa: BLE001
            result["errors"].append(f"evening_batch: {e}")

        return result

    # ==================================================================
    # 内部辅助
    # ==================================================================
    def _write_morning_decisions(self, today: str, morning_result: dict) -> str:
        """生成晨会决策清单，写入 company/operations/morning-decisions-YYYY-MM-DD.md。

        汇总 CEO 当日立项数/砍项数/优先级调整数 + 当前队列 pending 任务清单。
        返回文件绝对路径。
        """
        from engine.task_queue import TaskQueue

        ops_dir = self.workspace.root_dir / "operations"
        ops_dir.mkdir(parents=True, exist_ok=True)
        target_path = ops_dir / f"morning-decisions-{today}.md"

        ceo = morning_result.get("ceo_decisions", {}) or {}
        initiated = ceo.get("initiated", 0)
        killed = ceo.get("killed", 0)
        reprioritized = ceo.get("reprioritized", 0)
        ceo_log = ceo.get("log_path", "")

        # 当前队列 pending 任务清单
        try:
            queue = TaskQueue(self.workspace)
            pending = queue.list_pending()
        except Exception:
            pending = []

        lines: List[str] = []
        lines.append(f"# 晨会决策清单 - {today}")
        lines.append("")
        lines.append(f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}")
        lines.append("")
        lines.append("## CEO 自主决策摘要")
        lines.append("")
        lines.append(f"- 新立项任务数：{initiated}")
        lines.append(f"- 砍项数：{killed}")
        lines.append(f"- 优先级调整任务数：{reprioritized}")
        if ceo_log:
            lines.append(f"- CEO 决策日志：{ceo_log}")
        lines.append("")
        lines.append("## 当前队列待执行任务（pending）")
        lines.append("")
        if pending:
            lines.append("| 任务ID | 优先级 | 类型 | 指派 | 标题 |")
            lines.append("|--------|--------|------|------|------|")
            for t in pending:
                lines.append(
                    f"| {t.get('id','')} | {t.get('priority','')} | "
                    f"{t.get('type','')} | {t.get('assignee') or '-'} | "
                    f"{(t.get('title') or '')[:50]} |"
                )
        else:
            lines.append("> （无 pending 任务）")
        lines.append("")
        lines.append("## 会议纪要")
        lines.append("")
        lines.append(morning_result.get("meeting_path") or "（未生成）")
        lines.append("")
        lines.append("## PM 市场扫描")
        lines.append("")
        lines.append(morning_result.get("pm_scan_path") or "（未生成）")
        lines.append("")

        if morning_result.get("errors"):
            lines.append("## 异常")
            lines.append("")
            for err in morning_result["errors"]:
                lines.append(f"- {err}")
            lines.append("")

        self.workspace.write_text(target_path, "\n".join(lines))
        return str(target_path.resolve())

    def _scan_today_productions(self) -> list:
        """扫描 articles/ 与 marketing/ 目录的今日新增文件。

        判断规则：文件 mtime 日期 == 今日。

        Returns:
            今日新增文件绝对路径列表（按 mtime 降序）。
        """
        today = datetime.now().strftime("%Y-%m-%d")
        candidates: list[Path] = []

        articles_dir = (
            self.workspace.projects_dir / "seo-content-generator" / "articles"
        )
        marketing_dir = self.workspace.knowledge_dir / "marketing"

        for directory in (articles_dir, marketing_dir):
            if not directory.exists():
                continue
            try:
                for p in directory.glob("*.md"):
                    try:
                        mtime = datetime.fromtimestamp(p.stat().st_mtime)
                    except Exception:
                        continue
                    if mtime.strftime("%Y-%m-%d") == today:
                        candidates.append(p)
            except Exception:
                continue

        # 按 mtime 降序排列（新文件在前）
        candidates.sort(key=lambda p: p.stat().st_mtime, reverse=True)
        return [str(p.resolve()) for p in candidates]

    def _write_evening_review(self, today: str, evening_result: dict) -> str:
        """写复盘日志到 company/operations/evening-review-YYYY-MM-DD.md。

        含 KPI 看板 + 今日任务统计 + 今日自主产出清单 + CEO 复盘。
        返回文件绝对路径。
        """
        from engine.task_queue import TaskQueue

        ops_dir = self.workspace.root_dir / "operations"
        ops_dir.mkdir(parents=True, exist_ok=True)
        target_path = ops_dir / f"evening-review-{today}.md"

        # 今日任务统计（按状态分组）
        try:
            queue = TaskQueue(self.workspace)
            all_tasks = queue.list_all()
            today_tasks = [
                t for t in all_tasks
                if (t.get("created_at") or "").startswith(today)
                or (t.get("completed_at") or "").startswith(today)
                or (t.get("claimed_at") or "").startswith(today)
            ]
        except Exception:
            today_tasks = []

        # 状态分组统计
        status_count: dict = {}
        for t in today_tasks:
            s = t.get("status", "unknown")
            status_count[s] = status_count.get(s, 0) + 1

        # 读取 CEO 决策日志内容（若存在）
        ceo_review = "（无 CEO 决策日志）"
        ceo_log_path = self.workspace.root_dir / "decisions" / f"ceo-{today}.md"
        if ceo_log_path.exists():
            try:
                ceo_review = ceo_log_path.read_text(encoding="utf-8")
            except Exception:
                pass

        produced_files = evening_result.get("produced_files", []) or []

        lines: List[str] = []
        lines.append(f"# AI 公司每日复盘 - {today}")
        lines.append("")
        lines.append(f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}")
        lines.append("")
        lines.append("## 一、KPI 看板")
        lines.append("")
        lines.append(evening_result.get("kpi_dashboard") or "（KPI 看板生成失败）")
        lines.append("")
        lines.append("## 二、今日任务统计")
        lines.append("")
        if status_count:
            lines.append("| 状态 | 数量 |")
            lines.append("|------|------|")
            for s, c in sorted(status_count.items()):
                lines.append(f"| {s} | {c} |")
        else:
            lines.append("> 今日无任务活动")
        lines.append("")
        lines.append(f"今日涉及任务总数：{len(today_tasks)}")
        lines.append("")
        lines.append("## 三、今日自主产出")
        lines.append("")
        if produced_files:
            lines.append(f"今日共自主产出 {len(produced_files)} 个文件：")
            lines.append("")
            for f in produced_files:
                lines.append(f"- {f}")
        else:
            lines.append("> 今日无新增文章/推广物料产出")
        lines.append("")
        lines.append("## 四、运营日报")
        lines.append("")
        lines.append(evening_result.get("daily_ops_path") or "（运营日报生成失败）")
        lines.append("")
        lines.append("## 五、CEO 复盘")
        lines.append("")
        lines.append(ceo_review)
        lines.append("")

        if evening_result.get("errors"):
            lines.append("## 六、异常")
            lines.append("")
            for err in evening_result["errors"]:
                lines.append(f"- {err}")
            lines.append("")

        self.workspace.write_text(target_path, "\n".join(lines))
        return str(target_path.resolve())

    def _print_first_income_progress(self, income_result: dict) -> None:
        """打印第一桶金进度报告关键指标（SubTask 7.3）。

        简单打印到 stdout，含：当前余额 / 本次 delta / 上次余额 /
        是否首次到账 / 里程碑文件路径。累计到账见真实账本。

        Args:
            income_result: IncomeMonitor.check_inbound() 返回的结果字典。
        """
        if not income_result:
            print("[第一桶金进度报告] 无到账检查结果")
            return

        current = income_result.get("current")
        delta = income_result.get("delta", 0.0)
        last = income_result.get("last")
        is_first = income_result.get("is_first_income", False)
        milestone = income_result.get("milestone_path", "")

        print("-" * 60)
        print("[第一桶金进度报告]")
        print(f"  当前 ETH 余额：{current}")
        print(f"  本次到账 delta：{delta} ETH")
        print(f"  上次记录余额：{last}")
        if is_first:
            print(f"  🎉 首次到账！里程碑文件：{milestone}")
        print("  累计到账：见真实账本（company/finance/ledger.yaml）")
        print("-" * 60)
