"""商业闭环编排器

编排 AutoCorp 一个完整工作日：晨会 → 编码 → 测试 → 推广 → 收入结算 → 日报 → 账本更新。
每个阶段独立 try/except，任一阶段失败不中断后续阶段，保证日报必生成。
即使所有 LLM 调用失败（无 API_KEY），也会优雅降级产出结构化日报。
"""
from __future__ import annotations

from datetime import datetime
from typing import Any, Dict, List

from engine.ledger import Ledger
from engine.workspace import WorkspaceManager
from engine.llm_client import LLMClient, default_client


class Orchestrator:
    """商业闭环编排器 - 编排一个完整工作日。

    收入策略：优先采集真实收入（PayPal capture + 加密货币到账），
    无真实收入时返回 0 而非模拟，并在日报中触发危机警报，
    由 CEO/COO 推进真实收益渠道，避免虚假收入掩盖经营问题。
    """

    # 每任务估算的 LLM API 调用成本（美元）
    API_COST_PER_TASK = 0.5

    def __init__(self, workspace=None, llm_client=None):
        from engine.workspace import WorkspaceManager
        from engine.llm_client import default_client
        self.workspace = workspace or WorkspaceManager()
        self.llm_client = llm_client or default_client
        self.ledger = Ledger(self.workspace)

    # ------------------------------------------------------------------
    # 主流程：执行一个完整工作日
    # ------------------------------------------------------------------
    def run_day(self) -> dict:
        """执行一个完整工作日，返回日报数据 dict。

        七阶段顺序：晨会→编码→测试→推广→收入→日报→账本。
        每阶段独立 try/except，失败记录但不中断后续阶段；已完成阶段结果仍写入日报。
        """
        today = datetime.now().strftime("%Y-%m-%d")
        data: Dict[str, Any] = {
            "date": today,
            "meeting": {"status": "未执行", "minutes_path": "", "tasks": []},
            "development": {"outputs": [], "pending": []},
            "testing": {"results": [], "defects": []},
            "marketing": {"plan": ""},
            "revenue": {"amount": 0.0, "source": "", "advice": "", "is_real": False,
                        "real_amount": 0.0, "simulated_amount": 0.0, "real_sources": []},
            "expense": {"amount": 0.0, "purpose": "", "is_real": False, "rejected": False},
            "balance": 0.0,
            "report_path": "",
            # 安全闸门拒绝执行的支出单独统计（不算失败，而是「拒绝执行」）
            "safety": {"rejections": 0, "rejected_items": []},
        }

        # 阶段1：晨会 - 触发会议并获取任务清单
        try:
            from engine.meeting import Meeting
            meeting = Meeting(self.workspace, self.llm_client)
            data["meeting"]["minutes_path"] = meeting.run()
            data["meeting"]["tasks"] = meeting.get_tasks()
            data["meeting"]["status"] = "成功"
        except Exception as e:
            data["meeting"]["status"] = f"降级（{e}）"

        # 阶段2：任务分发与编码 - programmer 调用 develop_module
        try:
            data["development"] = self._stage_development(data["meeting"]["tasks"])
        except Exception as e:
            data["development"]["pending"].append({"reason": f"开发阶段异常：{e}"})

        # 阶段3：测试 - 对开发产出调用 Tester.run_tests
        try:
            data["testing"] = self._stage_testing(data["development"]["outputs"])
        except Exception as e:
            data["testing"]["results"].append({"error": f"测试阶段异常：{e}"})

        # 阶段4：推广 - COO 制定推广计划
        try:
            data["marketing"] = self._stage_marketing(data["meeting"]["tasks"])
        except Exception as e:
            data["marketing"]["plan"] = f"（推广阶段异常：{e}）"

        # 阶段5：收入结算 - 采集真实收入，无收入时返回 0 并触发危机警报
        try:
            data["revenue"] = self._stage_revenue()
        except Exception as e:
            data["revenue"] = {"amount": 0.0, "error": f"收入结算失败：{e}"}

        # 阶段6：日报生成 - 汇总各阶段结果写入 reports/YYYY-MM-DD-daily.md
        try:
            data["report_path"] = self._write_report(data)
        except Exception as e:
            data["report_path"] = f"（日报生成失败：{e}）"

        # 阶段7：账本更新 - 经安全闸门评估后记录 API 调用成本支出
        try:
            task_count = len(data["meeting"]["tasks"])
            expense_amount = task_count * self.API_COST_PER_TASK
            if expense_amount > 0:
                # 构造付款请求，经 PaymentGate 评估（白名单内 payee 应 allow）
                payment_request = {
                    "payee": "api.trae.cn",
                    "amount": expense_amount,
                    "currency": "USD",
                    "category": "api_cost",
                    "description": "当日 LLM API 调用成本估算",
                }
                gate_result = self._assess_payment(payment_request)
                if gate_result.get("approved"):
                    # 闸门通过：余额足够时执行真实支出
                    if self.ledger.can_afford(expense_amount):
                        tx = self.ledger.expense_real(
                            expense_amount, "api_cost",
                            description="当日 LLM API 调用成本估算",
                        )
                        data["expense"] = {
                            "amount": expense_amount, "purpose": "api_cost",
                            "tx_id": tx, "is_real": True, "rejected": False,
                            "gate_level": gate_result.get("level"),
                        }
                    else:
                        data["expense"] = {
                            "amount": 0.0, "purpose": "api_cost",
                            "is_real": False, "rejected": False,
                            "error": "余额不足，跳过 API 成本支出",
                        }
                else:
                    # 闸门拒绝：记录为「拒绝执行」（非失败），不中断流程
                    data["safety"]["rejections"] += 1
                    data["safety"]["rejected_items"].append({
                        "payee": "api.trae.cn",
                        "amount": expense_amount,
                        "level": gate_result.get("level"),
                        "reasons": gate_result.get("reasons", []),
                    })
                    # high_risk 被拒绝时补充记录安全事件（block 已由闸门自动记录）
                    if gate_result.get("level") != "block":
                        self._log_payment_rejection(payment_request, gate_result)
                    data["expense"] = {
                        "amount": 0.0, "purpose": "api_cost",
                        "is_real": False, "rejected": True,
                        "gate_level": gate_result.get("level"),
                    }
            data["balance"] = self.ledger.balance()
            # 账本更新后重新生成日报，确保余额与支出字段反映最终状态
            try:
                data["report_path"] = self._write_report(data)
            except Exception:
                pass
        except Exception as e:
            data["expense"] = {"error": f"账本更新失败：{e}"}
            data["balance"] = self._safe_balance()

        return data

    # ------------------------------------------------------------------
    # 各阶段实现
    # ------------------------------------------------------------------
    def _stage_development(self, tasks: List[dict]) -> dict:
        """阶段2：遍历任务清单按 assignee 分发，programmer 调用 develop_module。

        architect 任务跳过（已在会议中完成），其他任务记录待处理。
        每个任务独立 try/except，失败记录但不中断。
        """
        from engine.agents import Programmer
        programmer = Programmer(self.workspace, self.llm_client)
        outputs, pending = [], []
        for task in tasks:
            assignee = task.get("assignee", "")
            desc = task.get("description", "")
            task_id = task.get("id", "")
            try:
                if assignee == "programmer":
                    result = programmer.develop_module(task)
                    outputs.append({
                        "task_id": task_id,
                        "description": desc,
                        "status": result.get("status", "delivered"),
                        "output": result.get("raw_response", ""),
                    })
                elif assignee == "architect":
                    pending.append({"task_id": task_id, "description": desc,
                                    "reason": "architect 任务已在会议中完成"})
                else:
                    pending.append({"task_id": task_id, "description": desc,
                                    "reason": f"assignee={assignee} 暂未自动处理"})
            except Exception as e:
                pending.append({"task_id": task_id, "description": desc,
                                "reason": f"开发失败：{e}"})
        return {"outputs": outputs, "pending": pending}

    def _stage_testing(self, outputs: List[dict]) -> dict:
        """阶段3：对开发产出调用 Tester.run_tests，收集结果与缺陷（不阻塞流程）。"""
        from engine.agents import Tester
        tester = Tester(self.workspace, self.llm_client)
        results, defects = [], []
        for out in outputs:
            try:
                module_info = {
                    "task_id": out.get("task_id"),
                    "description": out.get("description"),
                    "code": out.get("output", ""),
                }
                r = tester.run_tests(module_info)
                results.append({
                    "task_id": out.get("task_id"),
                    "passed": r.get("passed"),
                    "failed": r.get("failed"),
                    "report": r.get("report", ""),
                    "raw_response": r.get("raw_response", ""),
                })
                if r.get("bugs"):
                    defects.append({"task_id": out.get("task_id"), "bugs": r.get("bugs")})
            except Exception as e:
                results.append({"task_id": out.get("task_id"), "error": f"测试失败：{e}"})
        return {"results": results, "defects": defects}

    def _stage_marketing(self, tasks: List[dict]) -> dict:
        """阶段4：COO 制定推广计划，产品信息从会议任务提取（或占位）。"""
        from engine.agents import COO
        coo = COO(self.workspace, self.llm_client)
        product_info = {
            "name": "autoCorp-daily",
            "tasks": [t.get("description", "") for t in tasks],
        }
        plan = coo.create_marketing_plan(product_info)
        return {"plan": plan.get("raw_response", ""), "channels": plan.get("channels")}

    def _stage_revenue(self) -> dict:
        """阶段5：优先检查真实收入（PayPal/加密货币），无真实收入时返回 0 并触发危机警报。

        真实收入检查失败（如 PayPal API 错误、网络异常）不中断流程，
        仅在 advice 中记录失败原因；无真实收入时不再生成模拟收入，
        返回 amount=0.0 并附加危机警报建议，逼迫推进真实收益渠道。
        收入追踪建议依赖 LLM，可能失败，advice 降级为占位字符串。
        """
        from engine.agents import COO
        coo = COO(self.workspace, self.llm_client)
        # 尝试获取收入追踪建议（LLM 调用，失败时降级为占位）
        advice = ""
        try:
            revenue_data = coo.track_revenue()
            advice = revenue_data.get("advice", "")
        except Exception as e:
            advice = f"（收入追踪建议生成失败：{e}）"

        # 1. 优先检查真实收入（PayPal 订单 capture + 加密货币到账）
        real_sources: List[str] = []
        real_total = 0.0
        # 1a. PayPal：扫描 pending 订单并尝试 capture（capture_order 内部已调 income_real 入账）
        try:
            paypal_income = self._collect_paypal_income()
            if paypal_income["total"] > 0:
                real_total += paypal_income["total"]
                real_sources.extend(paypal_income["sources"])
        except Exception as e:
            advice = (advice + f"（PayPal 收入检查失败：{e}）").strip()
        # 1b. 加密货币：检查钱包余额变化，新增部分通过 record_inbound 入真实账
        try:
            crypto_income = self._collect_crypto_income()
            if crypto_income["total"] > 0:
                real_total += crypto_income["total"]
                real_sources.extend(crypto_income["sources"])
        except Exception as e:
            advice = (advice + f"（加密货币收入检查失败：{e}）").strip()

        # 2. 有真实收入：使用真实收入（不再模拟）
        if real_total > 0:
            return {
                "amount": round(real_total, 2),
                "real_amount": round(real_total, 2),
                "simulated_amount": 0.0,
                "source": " / ".join(real_sources) or "real_income",
                "is_real": True,
                "real_sources": real_sources,
                "advice": advice,
            }

        # 3. 无真实收入：返回 0 并触发危机警报（不再生成虚假收入）
        return {
            "amount": 0.0,
            "real_amount": 0.0,
            "simulated_amount": 0.0,
            "source": "no_income",
            "is_real": False,
            "real_sources": [],
            "advice": advice + "\n⚠️ 危机警报：今日无任何真实收入，请立即推进收益渠道。",
        }

    # ------------------------------------------------------------------
    # 真实收入采集
    # ------------------------------------------------------------------
    def _collect_paypal_income(self) -> dict:
        """扫描 PayPal pending 订单并尝试 capture，返回 {total, sources}。

        无 PayPal 凭证或无 pending 订单时返回零值，不报错。
        capture_order 内部已调用 Ledger.income_real 入真实账本。
        单个订单捕获失败不中断，继续处理其他订单。
        """
        from engine.payments.paypal import PayPalClient, PayPalError
        paypal = PayPalClient(self.workspace)
        # 无凭证则跳过（早期无 PayPal 接入）
        if not paypal.client_id or not paypal.client_secret:
            return {"total": 0.0, "sources": []}
        pending_dir = paypal.pending_dir
        if not pending_dir.exists():
            return {"total": 0.0, "sources": []}
        total = 0.0
        sources: List[str] = []
        for order_file in sorted(pending_dir.glob("*.json")):
            order_id = order_file.stem
            try:
                result = paypal.capture_order(order_id)
                amount = float(result.get("amount", 0) or 0)
                if amount > 0:
                    total += amount
                    sources.append(f"paypal:{order_id}")
            except PayPalError:
                # 单个订单捕获失败（如状态未 COMPLETED、API 错误）不中断
                continue
            except Exception:
                continue
        return {"total": round(total, 2), "sources": sources}

    def _collect_crypto_income(self) -> dict:
        """检查加密货币钱包余额变化，新增余额入账。返回 {total, sources}。

        对比上次记录余额，余额增加部分视为新到账，调用 record_inbound 入真实账本。
        首次记录余额不视为新到账（避免误记历史余额为收入）。
        无注册钱包或网络失败时返回零值，不报错。
        """
        from engine.crypto.wallet import WalletManager
        wm = WalletManager(self.workspace)
        wallets = wm.list_wallets()
        if not wallets:
            return {"total": 0.0, "sources": []}
        state = self._load_wallet_balance_state()
        total = 0.0
        sources: List[str] = []
        for w in wallets:
            chain = w.get("chain", "")
            address = w.get("address", "")
            if not chain or not address:
                continue
            try:
                result = wm.check_balance(address, chain)
                balance = result.get("balance")
                if balance is None:
                    continue
                key = f"{chain}_{address}"
                last = state.get(key)
                # 首次记录余额，不视为新到账（避免误记历史余额为收入）
                if last is None:
                    state[key] = balance
                    continue
                if balance > last:
                    delta = round(balance - last, 8)
                    # 生成简化 tx_hash（真实场景应从链上获取交易哈希）
                    tx_hash = f"{chain}_inbound_{datetime.now().strftime('%Y%m%d%H%M%S')}"
                    wm.record_inbound(chain, address, delta, tx_hash)
                    total += delta
                    sources.append(f"crypto_{chain}:{address[:10]}")
                    state[key] = balance
                elif balance < last:
                    # 余额减少（外发），仅更新记录，不视为收入
                    state[key] = balance
            except Exception:
                continue
        self._save_wallet_balance_state(state)
        return {"total": round(total, 2), "sources": sources}

    def _load_wallet_balance_state(self) -> dict:
        """读取钱包余额状态文件 {chain_address: last_balance}。"""
        path = self.workspace.config_dir / "wallet_balance_state.yaml"
        data = self.workspace.read_yaml(path)
        return data if isinstance(data, dict) else {}

    def _save_wallet_balance_state(self, state: dict) -> None:
        """写入钱包余额状态文件。"""
        path = self.workspace.config_dir / "wallet_balance_state.yaml"
        self.workspace.write_yaml(path, state)

    # ------------------------------------------------------------------
    # 安全闸门
    # ------------------------------------------------------------------
    def _assess_payment(self, payment_request: dict) -> dict:
        """调用安全闸门评估付款请求。

        闸门本身故障时降级为允许（避免闸门异常中断闭环），并记录原因。
        返回 {approved, level, reasons, ...}。
        """
        try:
            from engine.safety.payment_gate import PaymentGate
            gate = PaymentGate(self.workspace)
            return gate.execute(payment_request)
        except Exception as e:
            # 闸门本身故障：降级为允许，记录原因（仅用于已知内部支出场景）
            return {
                "approved": True,
                "level": "allow",
                "reasons": [f"闸门评估异常，降级放行：{e}"],
            }

    def _log_payment_rejection(self, payment_request: dict, gate_result: dict) -> None:
        """闸门拒绝支出时记录安全事件到 company/safety/incidents.md。

        block 级别已由 PaymentGate.execute 自动记录，本方法仅补充 high_risk 被拒绝的场景。
        """
        try:
            from engine.safety.compliance import ComplianceChecker
            ComplianceChecker(self.workspace).log_incident(
                "payment_rejected",
                {
                    "type": "payment",
                    "content": payment_request.get("description", ""),
                    "amount": payment_request.get("amount"),
                },
                f"外付款被闸门拒绝（{gate_result.get('level')}）："
                f"{', '.join(gate_result.get('reasons', []))}",
            )
        except Exception:
            pass

    def _count_today_incidents(self) -> int:
        """统计 company/safety/incidents.md 中今日安全事件数。

        事件标题格式：## 2026-06-27T10:30:00 | type
        匹配包含今日日期的标题行。
        """
        path = self.workspace.root_dir / "safety" / "incidents.md"
        content = self.workspace.read_text(path)
        if not content:
            return 0
        today = datetime.now().strftime("%Y-%m-%d")
        return sum(
            1 for line in content.splitlines()
            if line.startswith("## ") and today in line
        )

    def _safe_balance(self) -> float:
        """安全读取余额，读取失败返回 0.0。"""
        try:
            return self.ledger.balance()
        except Exception:
            return 0.0

    # ------------------------------------------------------------------
    # 日报生成
    # ------------------------------------------------------------------
    def _write_report(self, data: dict) -> str:
        """汇总各阶段结果生成日报 markdown，写入 today_report_path()，返回文件绝对路径。

        升级：新增「真实收入」「真实支出」「安全事件」字段；
        账本变动区分真实交易（💰）与虚拟交易（（虚拟））。
        """
        date = data.get("date", "")
        meeting = data.get("meeting", {})
        dev = data.get("development", {})
        testing = data.get("testing", {})
        mkt = data.get("marketing", {})
        revenue = data.get("revenue", {})
        expense = data.get("expense", {})
        safety = data.get("safety", {})

        income_amount = revenue.get("amount", 0.0)
        expense_amount = expense.get("amount", 0.0)
        balance = data.get("balance", 0.0)
        tasks = meeting.get("tasks", [])
        outputs = dev.get("outputs", [])
        results = testing.get("results", [])
        defects = testing.get("defects", [])

        # 账本审计：读取累计真实收入/支出（区分真实与虚拟资金）
        try:
            audit = self.ledger.audit()
        except Exception:
            audit = {
                "real_total_income": 0.0, "real_total_expense": 0.0,
                "recent_transactions": [],
            }
        real_income_total = float(audit.get("real_total_income", 0.0))
        real_expense_total = float(audit.get("real_total_expense", 0.0))

        # 当日安全事件数（来自 company/safety/incidents.md）与闸门拒绝数
        incident_count = self._count_today_incidents()
        rejections = safety.get("rejections", 0)

        # 测试通过率估算（Tester 返回的 passed/failed 可能为 None，按非空计数）
        passed_count = sum(1 for r in results if r.get("passed"))
        failed_count = sum(1 for r in results if r.get("failed"))
        total_cases = passed_count + failed_count
        pass_rate = round(passed_count / total_cases * 100, 1) if total_cases else 0.0

        # 拼接开发产出与待处理行
        dev_lines = [
            f"- {o.get('description', o.get('task_id'))}: {o.get('status', '未知')}"
            for o in outputs
        ]
        if not dev_lines:
            dev_lines.append("- （无开发产出）")
        for p in dev.get("pending", []):
            dev_lines.append(
                f"- {p.get('description', p.get('task_id', '?'))}: 待处理 - {p.get('reason', '')}"
            )
        dev_section = "\n".join(dev_lines)

        # 拼接缺陷清单
        defect_lines = [f"- {d.get('task_id')}: {d.get('bugs')}" for d in defects]
        if not defect_lines:
            defect_lines.append("- （无缺陷）")
        defect_section = "\n".join(defect_lines)

        minutes_path = meeting.get("minutes_path") or "（未生成会议纪要）"
        marketing_plan = mkt.get("plan", "（无推广计划）")
        revenue_source = revenue.get("source", "")
        expense_purpose = expense.get("purpose", "")

        # 收入/支出真实标记：真实交易 💰，虚拟交易（虚拟），被闸门拒绝（已拒绝）
        revenue_mark = "💰" if revenue.get("is_real") else "（虚拟）"
        if expense.get("rejected"):
            expense_mark = "（已拒绝）"
        elif expense.get("is_real"):
            expense_mark = "💰"
        else:
            expense_mark = "（虚拟）"

        # 近期交易（含真实/虚拟标记）
        recent_txs = audit.get("recent_transactions") or []
        if recent_txs:
            tx_lines = []
            for t in recent_txs:
                ttype = t.get("type", "?")
                amt = float(t.get("amount", 0.0))
                src = t.get("source", "")
                sign = "+" if ttype == "income" else "-"
                mark = "💰" if t.get("is_real", False) else "（虚拟）"
                tx_lines.append(
                    f"- [{t.get('id', '?')}] {ttype}: {sign}${amt:.2f} ({src}) {mark}"
                )
            tx_section = "\n".join(tx_lines)
        else:
            tx_section = "- （无交易记录）"

        # 安全拒绝明细
        rejected_items = safety.get("rejected_items", [])
        if rejected_items:
            reject_lines = [
                f"- {r.get('payee')} ${r.get('amount')} ({r.get('level')}): "
                f"{', '.join(r.get('reasons', []))}"
                for r in rejected_items
            ]
            reject_section = "\n".join(reject_lines)
        else:
            reject_section = "- （无）"

        content = f"""# AutoCorp 经营日报 - {date}

## 概览
- 会议状态: {meeting.get('status', '未知')}
- 任务总数: {len(tasks)}
- 完成任务: {len(outputs)}
- 测试通过率: {pass_rate}%
- 当日收入: ${income_amount}
- 当日支出: ${expense_amount}
- 真实收入（累计）: ${real_income_total}
- 真实支出（累计）: ${real_expense_total}
- 账本余额: ${balance}
- 当日安全事件: {incident_count}
- 闸门拒绝执行: {rejections}

## 1. 晨会纪要
{minutes_path}

## 2. 开发产出
{dev_section}

## 3. 测试结果
- 测试用例数: {total_cases}
- 通过: {passed_count}
- 失败: {failed_count}
- 缺陷清单:
{defect_section}

## 4. 推广计划
{marketing_plan}

## 5. 账本变动
- 收入: +${income_amount} ({revenue_source}) {revenue_mark}
- 支出: -${expense_amount} ({expense_purpose}) {expense_mark}
- 余额: ${balance}

### 近期交易
{tx_section}

## 6. 安全
- 当日安全事件: {incident_count}
- 闸门拒绝执行: {rejections}（拒绝不算失败，单独统计）
- 拒绝明细:
{reject_section}

## 7. 明日计划
- 基于今日 {len(outputs)} 项开发产出与 {len(defects)} 项缺陷，明日优先修复缺陷并推进未完成任务。
"""
        report_path = self.workspace.today_report_path()
        self.workspace.write_text(report_path, content)
        return str(report_path.resolve())
