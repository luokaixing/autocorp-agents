"""Phase Chain 编排器（参考 ChatDev Chat Chain）

将一个工作日按 7 个标准 Phase 串行编排，每个 Phase 有明确的入口条件、参与角色、
退出标准与最大时长。Phase 间通过共享消息池传递产物，单 Phase 失败/超时不阻塞
后续 Phase（优雅降级）。

7 个标准 Phase：
    - Phase-Morning  : 08:00 晨会决策（CEO 主持）
    - Phase-Research : 08:30 PM 市场调研与选题
    - Phase-Design   : 10:00 Architect 架构设计与模块拆分
    - Phase-Build    : 12:00 Programmer 编码 + Tester 测试
    - Phase-Promote  : 15:00 COO 内容发布与渠道推广
    - Phase-Review   : 18:00 日终复盘 + KPI 看板 + CEO 战略调整
    - Phase-Service  : 按需触发，外部客户订单专属 Phase（独立于日常循环）

设计原则：
1. 优雅降级：任一 Phase 失败/超时不阻塞后续 Phase，整体 try/except 包裹
2. 可观测性：每个 Phase 完成后 publish ``phase.done.<name>`` / ``phase.skipped.<name>``
   / ``phase.timeout.<name>`` 消息到共享消息池
3. 复用现有模块：Phase 分派到 Meeting / PM / Architect / TaskExecutor / COO /
   KPITracker / DailyOps / HealthMonitor 等已实现的类
4. 向后兼容：AutonomousLoop 的 run_morning / run_noon / run_evening 内部调用
   PhaseChain，保留原接口签名
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List, Optional

from engine.message_pool import MessagePool
from engine.sop_loader import SOPLoader
from engine.workspace import WorkspaceManager


# ----------------------------------------------------------------------
# 7 个 Phase 元数据常量（dict 形式）
# ----------------------------------------------------------------------
PHASE_METADATA: Dict[str, Dict[str, Any]] = {
    "Phase-Morning": {
        "name": "Phase-Morning",
        "entry_condition": "每日 08:00 触发；无前置 Phase 依赖",
        "participants": ["ceo", "product_manager", "cto", "architect"],
        "exit_criteria": "产出当日立项清单与会议纪要；CEO 自主决策完成",
        "max_duration_minutes": 30,
        "fallback": "Meeting 失败时仅记录 CEO 决策；CEO 决策失败时仅召开会议",
    },
    "Phase-Research": {
        "name": "Phase-Research",
        "entry_condition": "Phase-Morning 完成或当日晨会决策清单已产出",
        "participants": ["product_manager"],
        "exit_criteria": "产出市场扫描报告（pm-scan-YYYY-MM-DD.md）与选题建议",
        "max_duration_minutes": 60,
        "fallback": "PM 扫描失败时沿用昨日选题方向；LLM 失败时基于规则产出基础报告",
    },
    "Phase-Design": {
        "name": "Phase-Design",
        "entry_condition": "Phase-Research 完成；PM 选题清单或 PRD 已产出",
        "participants": ["architect", "cto"],
        "exit_criteria": "产出模块设计文档（architecture.md 或 architecture-<task_id>.md）",
        "max_duration_minutes": 90,
        "fallback": "Architect 失败时复用昨日架构模板；LLM 失败时产出骨架设计文档",
    },
    "Phase-Build": {
        "name": "Phase-Build",
        "entry_condition": "Phase-Design 必须产出 architecture.md 或模块设计文档",
        "participants": ["programmer", "tester"],
        "exit_criteria": "TaskExecutor.run_batch 执行完成；至少 1 个任务状态变更",
        "max_duration_minutes": 180,
        "fallback": "architecture 缺失时跳过本 Phase；超时未完成任务标记 failed reason=phase_timeout",
    },
    "Phase-Promote": {
        "name": "Phase-Promote",
        "entry_condition": "Phase-Build 完成；存在可推广的产物（文章/代码/产品）",
        "participants": ["coo"],
        "exit_criteria": "COO 产出至少 1 份推广物料或 TaskExecutor 完成 promote 任务",
        "max_duration_minutes": 60,
        "fallback": "无推广产物时跳过；LLM 失败时使用模板物料；DecisionGate 拒绝时跳过该次发布",
    },
    "Phase-Review": {
        "name": "Phase-Review",
        "entry_condition": "当日 Phase-Build / Phase-Promote 已执行（失败/跳过也算）",
        "participants": ["ceo", "全员"],
        "exit_criteria": "产出 KPI 看板 + 运营日报 + 复盘日志；HealthMonitor 生成健康报告（如已实现）",
        "max_duration_minutes": 30,
        "fallback": "KPI 失败时仅写运营日报；HealthMonitor 未实现时跳过健康检查",
    },
    "Phase-Service": {
        "name": "Phase-Service",
        "entry_condition": "订单状态为 confirmed；order_id 已知",
        "participants": ["product_manager", "architect", "programmer", "tester"],
        "exit_criteria": "订单交付目录产出标准化交付包（README/PRD/source/test-report/acceptance）",
        "max_duration_minutes": 240,
        "fallback": "OrderManager 未实现时调用 TaskExecutor 跑 service 任务；超时未完成项标记 phase_timeout",
    },
}


class PhaseChain:
    """Phase Chain 编排器 - 按 7 个标准 Phase 串行编排工作日。

    通过 ``run_morning_chain`` / ``run_noon_chain`` / ``run_evening_chain`` /
    ``run_service_chain`` 触发不同时段的 Phase 链。每个 Phase 单独 try/except
    包裹，失败不阻塞后续 Phase，并 publish 对应消息到共享消息池供审计。
    """

    def __init__(
        self,
        workspace: Optional[WorkspaceManager] = None,
        llm_client: Any = None,
    ) -> None:
        """初始化 Phase Chain 编排器。

        Args:
            workspace: WorkspaceManager 实例；为 None 时使用默认工作区。
            llm_client: LLM 客户端实例；为 None 时由各角色使用默认客户端。
        """
        self.workspace: WorkspaceManager = workspace or WorkspaceManager()
        self.llm_client = llm_client
        self.message_pool: MessagePool = MessagePool(self.workspace)
        self.sop_loader: SOPLoader = SOPLoader(self.workspace)
        # 上一 Phase 产出（用于入口条件校验与下游 Phase 输入）
        self._last_outputs: Dict[str, Any] = {}
        # 已执行 Phase 的结果汇总（phase_name -> result dict）
        self._phase_results: Dict[str, Dict[str, Any]] = {}

    # ==================================================================
    # 单 Phase 执行
    # ==================================================================
    def run_phase(
        self,
        phase_name: str,
        context: Optional[dict] = None,
    ) -> Dict[str, Any]:
        """执行单个 Phase：校验入口条件 → 分派角色执行 → 校验退出标准 → publish 消息。

        单 Phase 失败不阻塞，整体 try/except 包裹，任一异常都转化为
        ``status="failed"`` 返回，并 publish ``phase.failed.<name>`` 消息。

        Args:
            phase_name: Phase 名称，需为 PHASE_METADATA 中的键（如 ``Phase-Morning``）。
            context: Phase 上下文，含入口条件校验所需字段与执行参数。

        Returns:
            ``{phase, status, outputs, errors}`` 字典：
                - ``phase``: Phase 名称
                - ``status``: ``done`` / ``skipped`` / ``timeout`` / ``failed``
                - ``outputs``: 该 Phase 产出物的字典
                - ``errors``: 异常/警告字符串列表
        """
        ctx = dict(context or {})
        result: Dict[str, Any] = {
            "phase": phase_name,
            "status": "failed",
            "outputs": {},
            "errors": [],
        }

        meta = PHASE_METADATA.get(phase_name)
        if meta is None:
            result["errors"].append(f"未知 Phase: {phase_name}")
            return result

        # 1. 入口条件校验（基于 context 与上一 Phase 产出）
        try:
            ok, reason = self._check_entry_condition(phase_name, ctx)
            if not ok:
                result["status"] = "skipped"
                result["errors"].append(f"入口条件不满足: {reason}")
                self._publish_phase_event(
                    phase_name, "skipped", reason=reason, context=ctx
                )
                self._phase_results[phase_name] = result
                return result
        except Exception as e:  # noqa: BLE001 - 入口条件校验失败不阻塞
            result["errors"].append(f"入口条件校验异常: {e}")

        # 2. 分派到对应角色执行（核心步骤，整体 try/except）
        try:
            outputs, errors, status = self._dispatch(phase_name, ctx)
            result["outputs"] = outputs or {}
            result["errors"].extend(errors or [])
            result["status"] = status or "done"
        except Exception as e:  # noqa: BLE001 - 单 Phase 失败不阻塞
            result["status"] = "failed"
            result["errors"].append(f"Phase 执行异常: {e}")

        # 3. 退出标准校验（仅在 status=done 时检查，失败/跳过不校验）
        if result["status"] == "done":
            try:
                ok, reason = self._check_exit_criteria(phase_name, result["outputs"])
                if not ok:
                    # 退出标准未达标仍记为 done（不阻塞），但记录警告
                    result["errors"].append(f"退出标准未完全满足: {reason}")
            except Exception as e:  # noqa: BLE001
                result["errors"].append(f"退出标准校验异常: {e}")

        # 4. publish phase 消息（done / failed / skipped / timeout）
        self._publish_phase_event(
            phase_name,
            result["status"],
            outputs=result["outputs"],
            errors=result["errors"],
            context=ctx,
        )

        # 5. 更新 last_outputs 与 phase_results
        self._last_outputs = {**self._last_outputs, **result["outputs"]}
        self._last_outputs["_last_phase"] = phase_name
        self._last_outputs["_last_status"] = result["status"]
        self._phase_results[phase_name] = result
        return result

    # ==================================================================
    # 时段链式编排
    # ==================================================================
    def run_morning_chain(self) -> Dict[str, Any]:
        """晨间链：依次执行 Phase-Morning → Phase-Research → Phase-Design。

        每个 Phase 失败/超时不阻塞后续。返回各 Phase 结果汇总。

        Returns:
            ``{phases: {...}, errors: [...]}`` 字典，phases 按 Phase 名分组。
        """
        results: Dict[str, Dict[str, Any]] = {}
        errors: List[str] = []

        for phase in ("Phase-Morning", "Phase-Research", "Phase-Design"):
            try:
                r = self.run_phase(phase, context={"chain": "morning"})
                results[phase] = r
                if r.get("errors"):
                    errors.extend(r["errors"])
            except Exception as e:  # noqa: BLE001 - 单 Phase 异常不阻塞链
                results[phase] = {
                    "phase": phase,
                    "status": "failed",
                    "outputs": {},
                    "errors": [f"chain 异常: {e}"],
                }
                errors.append(f"{phase}: {e}")

        return {"phases": results, "errors": errors}

    def run_noon_chain(self) -> Dict[str, Any]:
        """午间链：串联 Phase-Build → Phase-Promote。

        每个 Phase 失败/超时不阻塞后续。返回各 Phase 结果汇总。

        Returns:
            ``{phases: {...}, errors: [...]}`` 字典。
        """
        results: Dict[str, Dict[str, Any]] = {}
        errors: List[str] = []

        for phase in ("Phase-Build", "Phase-Promote"):
            try:
                r = self.run_phase(phase, context={"chain": "noon"})
                results[phase] = r
                if r.get("errors"):
                    errors.extend(r["errors"])
            except Exception as e:  # noqa: BLE001
                results[phase] = {
                    "phase": phase,
                    "status": "failed",
                    "outputs": {},
                    "errors": [f"chain 异常: {e}"],
                }
                errors.append(f"{phase}: {e}")

        return {"phases": results, "errors": errors}

    def run_evening_chain(self) -> Dict[str, Any]:
        """晚间链：执行 Phase-Review（含 HealthMonitor 调用，延迟导入）。

        HealthMonitor 类若尚未实现，延迟导入并 try/except 优雅降级。

        Returns:
            ``{phases: {...}, errors: [...]}`` 字典。
        """
        results: Dict[str, Dict[str, Any]] = {}
        errors: List[str] = []

        try:
            r = self.run_phase("Phase-Review", context={"chain": "evening"})
            results["Phase-Review"] = r
            if r.get("errors"):
                errors.extend(r["errors"])
        except Exception as e:  # noqa: BLE001
            results["Phase-Review"] = {
                "phase": "Phase-Review",
                "status": "failed",
                "outputs": {},
                "errors": [f"chain 异常: {e}"],
            }
            errors.append(f"Phase-Review: {e}")

        return {"phases": results, "errors": errors}

    def run_service_chain(self, order_id: str) -> Dict[str, Any]:
        """服务链：独立执行 Phase-Service（订单驱动）。

        OrderManager 若已实现则调用其交付流程；否则降级为 TaskExecutor 跑
        service 类型任务。Phase-Service 独立于日常循环，由订单事件触发。

        Args:
            order_id: 外部客户订单 ID。

        Returns:
            ``{phases: {...}, errors: [...]}`` 字典。
        """
        results: Dict[str, Dict[str, Any]] = {}
        errors: List[str] = []

        try:
            r = self.run_phase(
                "Phase-Service",
                context={"chain": "service", "order_id": order_id},
            )
            results["Phase-Service"] = r
            if r.get("errors"):
                errors.extend(r["errors"])
        except Exception as e:  # noqa: BLE001
            results["Phase-Service"] = {
                "phase": "Phase-Service",
                "status": "failed",
                "outputs": {},
                "errors": [f"chain 异常: {e}"],
            }
            errors.append(f"Phase-Service: {e}")

        return {"phases": results, "errors": errors}

    # ==================================================================
    # Phase 分派（核心）
    # ==================================================================
    def _dispatch(
        self, phase_name: str, context: Dict[str, Any]
    ) -> tuple:
        """根据 phase_name 分派到对应角色执行逻辑。

        Returns:
            ``(outputs, errors, status)`` 三元组：
                - outputs: 产出物字典
                - errors: 异常/警告字符串列表
                - status: ``done`` / ``skipped`` / ``timeout`` / ``failed``
        """
        outputs: Dict[str, Any] = {}
        errors: List[str] = []

        if phase_name == "Phase-Morning":
            outputs, errs = self._run_phase_morning(context)
            errors.extend(errs)
            return outputs, errors, "done"

        if phase_name == "Phase-Research":
            outputs, errs = self._run_phase_research(context)
            errors.extend(errs)
            return outputs, errors, "done"

        if phase_name == "Phase-Design":
            outputs, errs = self._run_phase_design(context)
            errors.extend(errs)
            return outputs, errors, "done"

        if phase_name == "Phase-Build":
            outputs, errs = self._run_phase_build(context)
            errors.extend(errs)
            return outputs, errors, "done"

        if phase_name == "Phase-Promote":
            outputs, errs = self._run_phase_promote(context)
            errors.extend(errs)
            return outputs, errors, "done"

        if phase_name == "Phase-Review":
            outputs, errs = self._run_phase_review(context)
            errors.extend(errs)
            return outputs, errors, "done"

        if phase_name == "Phase-Service":
            outputs, errs = self._run_phase_service(context)
            errors.extend(errs)
            return outputs, errors, "done"

        errors.append(f"未实现分派逻辑: {phase_name}")
        return outputs, errors, "failed"

    # ------------------------------------------------------------------
    # Phase-Morning: Meeting.run() + AutonomousCEO.run_daily_decision()
    # ------------------------------------------------------------------
    def _run_phase_morning(self, context: Dict[str, Any]) -> tuple:
        """晨会决策 Phase：召开会议 + CEO 自主决策。"""
        outputs: Dict[str, Any] = {}
        errors: List[str] = []

        # 1. 召开产研同步会
        try:
            from engine.meeting import Meeting

            meeting = Meeting(self.workspace, self.llm_client)
            outputs["meeting_path"] = meeting.run()
        except Exception as e:  # noqa: BLE001
            errors.append(f"meeting 失败: {e}")

        # 2. CEO 自主决策（立项/砍项/调优先级）
        try:
            from engine.agents.ceo_autonomous import AutonomousCEO

            ceo = AutonomousCEO(self.workspace, self.llm_client)
            outputs["ceo_decisions"] = ceo.run_daily_decision()
        except Exception as e:  # noqa: BLE001
            errors.append(f"ceo_daily_decision 失败: {e}")

        # 3. 扫描 company/orders/received/ 下未报价订单，自动初步报价
        #    启发式定价：$10 + 每百字 $5
        try:
            from engine.service_order import OrderManager  # type: ignore

            manager = OrderManager(self.workspace, self.message_pool)
            received_orders = manager.list_orders(status="received")
            scanned_ids: List[str] = []
            for od in received_orders:
                # 仅处理 quoted_price 为空的未报价订单
                if od.get("quoted_price") is not None:
                    continue
                oid = od.get("order_id", "")
                req = od.get("requirement", "") or ""
                # 启发式估算：$10 + 每百字 $5
                est_price = round(10.0 + (len(req) / 100.0) * 5.0, 2)
                try:
                    manager.quote(oid, price=est_price, actor="ceo")
                    scanned_ids.append(oid)
                except Exception as e:  # noqa: BLE001 - 单订单报价失败不阻塞
                    errors.append(f"订单 {oid} 自动报价失败: {e}")
            outputs["order_scan_count"] = len(scanned_ids)
            outputs["order_scanned_ids"] = scanned_ids
            # publish order.scan_completed 消息
            try:
                self.message_pool.publish(
                    topic="order.scan_completed",
                    payload={
                        "scanned_count": len(scanned_ids),
                        "order_ids": scanned_ids,
                    },
                    from_role="phase_chain",
                    to_role=None,
                )
            except Exception as e:  # noqa: BLE001 - publish 失败不阻塞
                errors.append(f"publish order.scan_completed 失败: {e}")
        except ImportError:
            # OrderManager 未实现：跳过订单扫描（不视为错误）
            outputs["order_scan_count"] = 0
        except Exception as e:  # noqa: BLE001 - 订单扫描整体失败不阻塞主流程
            errors.append(f"order_scan 失败: {e}")
            outputs["order_scan_count"] = 0

        return outputs, errors

    # ------------------------------------------------------------------
    # Phase-Research: ProductManager.scan_market()
    # ------------------------------------------------------------------
    def _run_phase_research(self, context: Dict[str, Any]) -> tuple:
        """PM 市场调研 Phase：扫描市场 + 落盘报告。"""
        outputs: Dict[str, Any] = {}
        errors: List[str] = []

        try:
            from engine.agents import ProductManager

            pm = ProductManager(self.workspace, self.llm_client)
            scan = pm.scan_market()
            report = scan.get("report", "") if isinstance(scan, dict) else ""
            today = datetime.now().strftime("%Y-%m-%d")
            scan_path = self.workspace.market_research_dir / f"pm-scan-{today}.md"
            self.workspace.write_text(scan_path, report or "# PM 市场扫描报告\n\n（空报告）\n")
            outputs["pm_scan_path"] = str(scan_path.resolve())
            outputs["top_gainers"] = scan.get("top_gainers", []) if isinstance(scan, dict) else []
            outputs["suggestion"] = scan.get("suggestion", "") if isinstance(scan, dict) else ""
        except Exception as e:  # noqa: BLE001
            errors.append(f"pm_scan 失败: {e}")

        return outputs, errors

    # ------------------------------------------------------------------
    # Phase-Design: Architect.design_module()
    # ------------------------------------------------------------------
    def _run_phase_design(self, context: Dict[str, Any]) -> tuple:
        """架构设计 Phase：Architect 产出模块设计文档。"""
        outputs: Dict[str, Any] = {}
        errors: List[str] = []

        try:
            from engine.agents import Architect

            architect = Architect(self.workspace, self.llm_client)
            # 构造简化任务上下文（design_module 接收 task dict）
            task = {
                "title": context.get("design_title", "autoCorp-daily 架构设计"),
                "description": context.get(
                    "design_description",
                    "基于当日 PM 选题与 CEO 决策，产出模块设计文档（含模块拆分/接口定义/技术规范）。",
                ),
                "keyword": context.get("design_keyword", "autoCorp-daily"),
            }
            doc = architect.design_module(task)
            # 落盘到 projects/<product>/architecture.md（满足退出标准）
            product = context.get("product", "autoCorp-daily")
            safe_product = Architect._sanitize_filename(str(product))
            project_dir = self.workspace.projects_dir / safe_product
            self.workspace.ensure_dir(project_dir)
            arch_path = project_dir / "architecture.md"
            self.workspace.write_text(arch_path, doc)
            outputs["architecture_path"] = str(arch_path.resolve())
            outputs["design_doc"] = doc
        except Exception as e:  # noqa: BLE001
            errors.append(f"architect_design 失败: {e}")

        return outputs, errors

    # ------------------------------------------------------------------
    # Phase-Build: TaskExecutor.run_batch(max_tasks=10)
    # ------------------------------------------------------------------
    def _run_phase_build(self, context: Dict[str, Any]) -> tuple:
        """编码与测试 Phase：TaskExecutor 批次执行。"""
        outputs: Dict[str, Any] = {}
        errors: List[str] = []

        try:
            from engine.task_executor import TaskExecutor

            executor = TaskExecutor(self.workspace, self.llm_client)
            max_tasks = int(context.get("max_tasks", 10))
            batch = executor.run_batch(max_tasks=max_tasks)
            outputs["batch"] = batch
            outputs["success_count"] = batch.get("success", 0) if isinstance(batch, dict) else 0
            outputs["failed_count"] = batch.get("failed", 0) if isinstance(batch, dict) else 0
        except Exception as e:  # noqa: BLE001
            errors.append(f"task_executor 失败: {e}")

        return outputs, errors

    # ------------------------------------------------------------------
    # Phase-Promote: COO.execute_promotion() 或扫 promote 任务
    # ------------------------------------------------------------------
    def _run_phase_promote(self, context: Dict[str, Any]) -> tuple:
        """渠道推广 Phase：COO 产出推广物料，或 TaskExecutor 跑 promote 任务。"""
        outputs: Dict[str, Any] = {}
        errors: List[str] = []
        promo_paths: List[str] = []

        # 1. 优先：扫描 pending 的 promote 任务，逐个调用 COO.execute_promotion
        try:
            from engine.agents import COO
            from engine.task_queue import TaskQueue

            queue = TaskQueue(self.workspace)
            coo = COO(self.workspace, self.llm_client)
            pending_promotes = [
                t for t in queue.list_pending()
                if t.get("type") == "promote"
            ]
            for task in pending_promotes[:5]:  # 单 Phase 最多处理 5 个推广任务
                try:
                    queue.update_status(task.get("id", ""), "in_progress")
                    promo = coo.execute_promotion(task)
                    # 落盘到 marketing 目录
                    today = datetime.now().strftime("%Y-%m-%d")
                    marketing_dir = self.workspace.knowledge_dir / "marketing"
                    target_path = marketing_dir / f"promo-{today}-{task.get('id', '')}.md"
                    self.workspace.write_text(target_path, promo)
                    promo_paths.append(str(target_path.resolve()))
                    queue.update_status(
                        task.get("id", ""),
                        "done",
                        result_path=str(target_path.resolve()),
                        completed_at=datetime.now().isoformat(timespec="seconds"),
                    )
                except Exception as e:  # noqa: BLE001 - 单任务失败不阻塞
                    errors.append(f"promote 任务 {task.get('id')} 失败: {e}")
        except Exception as e:  # noqa: BLE001
            errors.append(f"coo_promote 失败: {e}")

        # 2. 兜底：若 COO 路径未产出任何物料，调用 TaskExecutor 跑批次
        if not promo_paths:
            try:
                from engine.task_executor import TaskExecutor

                executor = TaskExecutor(self.workspace, self.llm_client)
                batch = executor.run_batch(max_tasks=5)
                outputs["batch"] = batch
            except Exception as e:  # noqa: BLE001
                errors.append(f"task_executor 兜底失败: {e}")

        outputs["promo_paths"] = promo_paths
        return outputs, errors

    # ------------------------------------------------------------------
    # Phase-Review: KPI + DailyOps + HealthMonitor（延迟导入）
    # ------------------------------------------------------------------
    def _run_phase_review(self, context: Dict[str, Any]) -> tuple:
        """日终复盘 Phase：KPI 看板 + 运营日报 + HealthMonitor（如已实现）。"""
        outputs: Dict[str, Any] = {}
        errors: List[str] = []

        # 1. KPI 看板
        try:
            from engine.agents.role_kpi import KPITracker

            tracker = KPITracker(self.workspace)
            outputs["kpi_dashboard"] = tracker.generate_kpi_dashboard()
        except Exception as e:  # noqa: BLE001
            errors.append(f"kpi_dashboard 失败: {e}")

        # 2. 运营日报
        try:
            from engine.daily_ops import DailyOps

            ops = DailyOps(self.workspace)
            outputs["daily_ops_path"] = ops.run()
        except Exception as e:  # noqa: BLE001
            errors.append(f"daily_ops 失败: {e}")

        # 3. HealthMonitor（延迟导入；类可能尚未实现，try/except 优雅降级）
        try:
            from engine.health_monitor import HealthMonitor  # type: ignore

            monitor = HealthMonitor(self.workspace)
            if hasattr(monitor, "run_daily_check"):
                outputs["health_report"] = monitor.run_daily_check()
        except ImportError:
            # HealthMonitor 未实现：跳过健康检查（不视为错误）
            outputs["health_report"] = None
        except Exception as e:  # noqa: BLE001
            errors.append(f"health_monitor 失败（已降级）: {e}")
            outputs["health_report"] = None

        return outputs, errors

    # ------------------------------------------------------------------
    # Phase-Service: OrderManager（如已实现）或 TaskExecutor 跑 service 任务
    # ------------------------------------------------------------------
    def _run_phase_service(self, context: Dict[str, Any]) -> tuple:
        """订单交付 Phase：OrderManager 交付流程，或 TaskExecutor 跑 service 任务。"""
        outputs: Dict[str, Any] = {}
        errors: List[str] = []
        order_id = context.get("order_id", "")

        # 1. 优先尝试 OrderManager（如已实现）
        order_handled = False
        try:
            from engine.service_order import OrderManager  # type: ignore

            manager = OrderManager(self.workspace)
            if hasattr(manager, "deliver"):
                outputs["order_deliver"] = manager.deliver(order_id)
                order_handled = True
        except ImportError:
            # OrderManager 未实现：降级到 TaskExecutor 跑 service 任务
            pass
        except Exception as e:  # noqa: BLE001
            errors.append(f"OrderManager.deliver 失败: {e}")

        # 2. 兜底：调用 TaskExecutor 跑 service 类型任务
        if not order_handled:
            try:
                from engine.task_executor import TaskExecutor

                executor = TaskExecutor(self.workspace, self.llm_client)
                batch = executor.run_batch(max_tasks=10)
                outputs["batch"] = batch
                outputs["note"] = (
                    "OrderManager 未实现，已降级为 TaskExecutor 跑 service 任务"
                )
            except Exception as e:  # noqa: BLE001
                errors.append(f"task_executor 兜底失败: {e}")

        outputs["order_id"] = order_id
        return outputs, errors

    # ==================================================================
    # 入口条件 / 退出标准校验
    # ==================================================================
    def _check_entry_condition(
        self, phase_name: str, context: Dict[str, Any]
    ) -> tuple:
        """校验 Phase 入口条件。

        Args:
            phase_name: Phase 名称。
            context: 上下文（含上一 Phase 产出与执行参数）。

        Returns:
            ``(ok, reason)``：ok=True 表示入口条件满足；reason 为说明。
        """
        last_phase = self._last_outputs.get("_last_phase", "")
        last_status = self._last_outputs.get("_last_status", "")

        # Phase-Morning 与 Phase-Service：无前置依赖
        if phase_name in ("Phase-Morning", "Phase-Service"):
            return True, ""

        # 其余 Phase：上一 Phase 必须已执行（任何状态都允许继续，失败/跳过也算）
        # 这里采用宽松策略：只要 chain 串行调用即可，不强校验产出文件存在
        # 仅在显式标记链未启动时拦截
        if not last_phase and phase_name not in ("Phase-Morning",):
            # 单独触发非首 Phase 时允许执行（context 可手动传入产物路径）
            return True, "无前置 Phase 但允许独立触发"

        # Phase-Build：如显式传入 design_outputs.path 不存在则跳过
        if phase_name == "Phase-Build":
            design_path = (self._last_outputs.get("architecture_path")
                           or context.get("architecture_path"))
            if design_path:
                from pathlib import Path
                if not Path(str(design_path)).exists():
                    return False, f"architecture_path 不存在: {design_path}"

        return True, ""

    def _check_exit_criteria(
        self, phase_name: str, outputs: Dict[str, Any]
    ) -> tuple:
        """校验 Phase 退出标准（宽松策略：仅记录未达标项，不强制阻塞）。

        Args:
            phase_name: Phase 名称。
            outputs: 该 Phase 的产出物字典。

        Returns:
            ``(ok, reason)``：ok=True 表示退出标准满足；reason 为未达标说明。
        """
        from pathlib import Path

        if phase_name == "Phase-Morning":
            if not outputs.get("meeting_path") and not outputs.get("ceo_decisions"):
                return False, "未产出会议纪要或 CEO 决策"
            return True, ""

        if phase_name == "Phase-Research":
            if not outputs.get("pm_scan_path"):
                return False, "未产出 PM 扫描报告"
            return True, ""

        if phase_name == "Phase-Design":
            if not outputs.get("architecture_path"):
                return False, "未产出架构设计文档"
            return True, ""

        if phase_name == "Phase-Build":
            batch = outputs.get("batch") or {}
            if not isinstance(batch, dict):
                return True, "batch 无返回值"
            total = (batch.get("success", 0) + batch.get("failed", 0)
                     + batch.get("skipped", 0))
            if total == 0:
                return False, "TaskExecutor 未执行任何任务"
            return True, ""

        if phase_name == "Phase-Promote":
            if not outputs.get("promo_paths") and not outputs.get("batch"):
                return False, "未产出推广物料且 TaskExecutor 未执行"
            return True, ""

        if phase_name == "Phase-Review":
            if not outputs.get("kpi_dashboard") and not outputs.get("daily_ops_path"):
                return False, "未产出 KPI 看板或运营日报"
            return True, ""

        if phase_name == "Phase-Service":
            if not outputs.get("order_deliver") and not outputs.get("batch"):
                return False, "OrderManager 未交付且 TaskExecutor 未执行"
            return True, ""

        return True, ""

    # ==================================================================
    # 消息池事件 publish
    # ==================================================================
    def _publish_phase_event(
        self,
        phase_name: str,
        status: str,
        outputs: Optional[Dict[str, Any]] = None,
        errors: Optional[List[str]] = None,
        reason: str = "",
        context: Optional[Dict[str, Any]] = None,
    ) -> None:
        """publish phase 事件消息到共享消息池。

        topic 命名规则：
            - 完成: ``phase.done.<short_name>``
            - 跳过: ``phase.skipped.<short_name>``
            - 超时: ``phase.timeout.<short_name>``
            - 失败: ``phase.failed.<short_name>``

        Args:
            phase_name: Phase 全名（如 ``Phase-Morning``）。
            status: ``done`` / ``skipped`` / ``timeout`` / ``failed``。
            outputs: Phase 产出物（写入 payload）。
            errors: 异常/警告列表（写入 payload）。
            reason: 跳过/失败原因（写入 payload）。
            context: 上下文（写入 payload，含 chain / order_id 等）。
        """
        # short_name: Phase-Morning -> morning
        short = phase_name.replace("Phase-", "").lower()
        topic = f"phase.{status}.{short}"

        payload: Dict[str, Any] = {
            "phase": phase_name,
            "status": status,
            "outputs": outputs or {},
            "errors": list(errors or []),
        }
        if reason:
            payload["reason"] = reason
        if context:
            # 仅保留可序列化的关键字段
            payload["context"] = {
                k: v for k, v in context.items()
                if isinstance(v, (str, int, float, bool, list, dict, type(None)))
            }

        try:
            self.message_pool.publish(
                topic=topic,
                payload=payload,
                from_role="phase_chain",
                to_role=None,  # 广播
            )
        except Exception as e:  # noqa: BLE001 - publish 失败不阻塞主流程
            print(f"[phase_chain] publish {topic} 失败: {e}")
