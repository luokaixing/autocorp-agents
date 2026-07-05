"""外付款安全审批闸门

AutoCorp 即将对接真实支付，任何往外付款必须经过安全审批，
防止被其他 AI 或钓鱼攻击骗走资金。

评估分级：
- allow       允许，走快速通道
- high_risk   高风险，必须人工确认
- block       拒绝
"""
from __future__ import annotations

from datetime import date
from typing import Any, Dict, List

from engine.safety.compliance import ComplianceChecker


# 默认各类别预算阈值（单笔，美元）
DEFAULT_BUDGETS = {
    "api_cost": 50,
    "marketing": 100,
    "outsourcing": 200,
    "server": 80,
    "other": 30,
}


class PaymentGate:
    """外付款安全审批闸门 - 防止资金被骗"""

    # 评估结果分级
    LEVEL_ALLOW = "allow"          # 允许，走快速通道
    LEVEL_HIGH_RISK = "high_risk"  # 高风险，必须人工确认
    LEVEL_BLOCK = "block"          # 拒绝

    def __init__(self, workspace=None, human_loop=None):
        from engine.workspace import WorkspaceManager
        from engine.human_loop import HumanLoop
        self.workspace = workspace or WorkspaceManager()
        self.human_loop = human_loop or HumanLoop(self.workspace)
        self.compliance = ComplianceChecker(self.workspace)
        # 首次初始化时创建空模板（若不存在）
        self._ensure_payees_config()

    # ------------------------------------------------------------------
    # 路径与初始化
    # ------------------------------------------------------------------
    @property
    def payees_config_path(self):
        """payees.yaml 配置文件路径：company/config/payees.yaml"""
        return self.workspace.config_dir / "payees.yaml"

    def _ensure_payees_config(self) -> None:
        """若 payees.yaml 不存在，创建空模板（含默认预算阈值）。"""
        if not self.payees_config_path.exists():
            self.workspace.write_yaml(
                self.payees_config_path,
                {
                    "whitelist": [],
                    "budgets": dict(DEFAULT_BUDGETS),
                },
            )

    # ------------------------------------------------------------------
    # 主入口：评估
    # ------------------------------------------------------------------
    def assess(self, payment_request: Dict[str, Any]) -> Dict[str, Any]:
        """评估付款请求风险等级。

        payment_request 字段：
          - payee       收款方（地址/账号/邮箱）
          - amount      金额
          - currency    货币，默认 USD
          - category    类别：api_cost/marketing/outsourcing/server/other
          - description 描述
          - strategy_alignment  是否符合季度战略（bool，可选，默认 True）

        返回 {level, reasons, requires_human}。
        """
        payee = payment_request.get("payee", "") or ""
        amount = payment_request.get("amount", 0)
        category = payment_request.get("category", "other") or "other"
        strategy_alignment = payment_request.get("strategy_alignment", True)

        reasons: List[str] = []
        level = self.LEVEL_ALLOW

        in_whitelist = self._check_whitelist(payee)

        # 1. 可疑模式检查（最高优先级）
        suspicious = self._check_suspicious(payment_request)
        if suspicious:
            reasons.extend(suspicious)
            # 大额非白名单 → block
            if "大额非白名单" in suspicious:
                level = self.LEVEL_BLOCK
            # 紧急催促 + 收款方变更 同时出现 → block（典型钓鱼模式）
            elif "紧急催促" in suspicious and "收款方变更" in suspicious:
                level = self.LEVEL_BLOCK
            elif level != self.LEVEL_BLOCK:
                level = self.LEVEL_HIGH_RISK

        # 2. 预算检查：超出该类别预算阈值 → high_risk
        if not self._check_budget(amount, category):
            if level != self.LEVEL_BLOCK:
                level = self.LEVEL_HIGH_RISK
            reasons.append(f"金额 {amount} 超出 {category} 类别预算阈值")

        # 3. 战略对齐：不符合战略 → high_risk
        if not strategy_alignment:
            if level != self.LEVEL_BLOCK:
                level = self.LEVEL_HIGH_RISK
            reasons.append("不符合季度战略")

        # 4. 白名单加分（仅记录，不降低已升级的等级）
        if in_whitelist:
            if level == self.LEVEL_ALLOW:
                reasons.append("收款方在白名单，走快速通道")
            else:
                reasons.append("收款方在白名单（但存在其他风险）")

        requires_human = level == self.LEVEL_HIGH_RISK

        return {
            "level": level,
            "reasons": reasons,
            "requires_human": requires_human,
        }

    # ------------------------------------------------------------------
    # 主入口：执行
    # ------------------------------------------------------------------
    def execute(self, payment_request: Dict[str, Any]) -> Dict[str, Any]:
        """完整执行流程：assess → 根据 level 决策。"""
        assessment = self.assess(payment_request)
        level = assessment["level"]
        reasons = assessment["reasons"]

        # allow：直接放行
        if level == self.LEVEL_ALLOW:
            return {
                "approved": True,
                "level": level,
                "reasons": reasons,
            }

        # high_risk：请求人工确认
        if level == self.LEVEL_HIGH_RISK:
            payee = payment_request.get("payee", "")
            amount = payment_request.get("amount", 0)
            category = payment_request.get("category", "other")
            description = payment_request.get("description", "")
            currency = payment_request.get("currency", "USD")
            decision_context = (
                f"外付款审批\n"
                f"收款方: {payee}\n"
                f"金额: {amount} {currency}\n"
                f"类别: {category}\n"
                f"描述: {description}\n"
                f"风险原因: {', '.join(reasons)}"
            )
            approval = self.human_loop.request_approval(decision_context)
            approved = approval.get("response") == "批准"
            return {
                "approved": approved,
                "level": level,
                "reasons": reasons,
                "human_approved": approved,
            }

        # block：拒绝并写告警到 incidents.md
        if level == self.LEVEL_BLOCK:
            self.compliance.log_incident(
                "payment_blocked",
                {
                    "type": "payment",
                    "content": payment_request.get("description", ""),
                    "amount": payment_request.get("amount"),
                },
                f"外付款被拒绝: {', '.join(reasons)}",
            )
            return {
                "approved": False,
                "level": level,
                "reasons": reasons,
            }

        # 兜底（理论上不会到达）
        return {"approved": False, "level": level, "reasons": reasons}

    # ------------------------------------------------------------------
    # 子检查
    # ------------------------------------------------------------------
    def _check_whitelist(self, payee: str) -> bool:
        """读取 payees.yaml 白名单，返回收款方是否在白名单。"""
        if not payee:
            return False
        data = self.workspace.read_yaml(self.payees_config_path) or {}
        whitelist = data.get("whitelist") or []
        for item in whitelist:
            if isinstance(item, dict) and item.get("payee") == payee:
                return True
        return False

    def _check_budget(self, amount, category: str) -> bool:
        """检查金额是否在类别预算阈值内。超出返回 False。

        阈值优先取 payees.yaml 中 budgets 配置，否则用默认值。
        """
        try:
            amt = float(amount)
        except (TypeError, ValueError):
            amt = 0
        data = self.workspace.read_yaml(self.payees_config_path) or {}
        budgets = data.get("budgets") or {}
        threshold = budgets.get(category, DEFAULT_BUDGETS.get(category, 30))
        try:
            thr = float(threshold)
        except (TypeError, ValueError):
            thr = 30
        return amt <= thr

    def _check_suspicious(self, payment_request: Dict[str, Any]) -> List[str]:
        """检测可疑模式，返回可疑原因列表。

        - 金额 > $500 且非白名单 → "大额非白名单"
        - description 含「紧急」「立即」「马上」 → "紧急催促"
        - payee 含「变更」「更新」 → "收款方变更"
        - 单笔 > $100 → 触发合规红线（调用 ComplianceChecker）
        """
        suspicious: List[str] = []
        payee = payment_request.get("payee", "") or ""
        amount = payment_request.get("amount", 0)
        description = payment_request.get("description", "") or ""

        try:
            amt = float(amount)
        except (TypeError, ValueError):
            amt = 0

        in_whitelist = self._check_whitelist(payee)

        # 金额 > $500 且非白名单
        if amt > 500 and not in_whitelist:
            suspicious.append("大额非白名单")

        # description 含紧急/立即/马上
        if any(kw in description for kw in ("紧急", "立即", "马上")):
            suspicious.append("紧急催促")

        # payee 含变更/更新
        if any(kw in payee for kw in ("变更", "更新")):
            suspicious.append("收款方变更")

        # 单笔 > $100 → 触发合规红线
        if amt > 100:
            result = self.compliance.check_compliance({
                "type": "payment",
                "content": description,
                "amount": amt,
            })
            if not result.get("passed"):
                for v in result.get("violations", []):
                    suspicious.append(f"合规红线: {v}")

        return suspicious

    # ------------------------------------------------------------------
    # 白名单管理
    # ------------------------------------------------------------------
    def add_to_whitelist(self, payee: str, category: str) -> None:
        """添加收款方到白名单。已存在则跳过。"""
        self._ensure_payees_config()
        data = self.workspace.read_yaml(self.payees_config_path) or {}
        whitelist = data.get("whitelist") or []
        # 已存在则跳过
        for item in whitelist:
            if isinstance(item, dict) and item.get("payee") == payee:
                return
        whitelist.append({
            "payee": payee,
            "category": category,
            "added": date.today().isoformat(),
        })
        data["whitelist"] = whitelist
        self.workspace.write_yaml(self.payees_config_path, data)

    def list_whitelist(self) -> List[Dict[str, Any]]:
        """返回白名单列表。"""
        self._ensure_payees_config()
        data = self.workspace.read_yaml(self.payees_config_path) or {}
        whitelist = data.get("whitelist") or []
        return [item for item in whitelist if isinstance(item, dict)]
