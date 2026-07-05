"""合规红线检查器

AutoCorp 即将对接真实支付与加密货币，本模块内置 6 条合规红线，
防止 AI 做出违法或高风险行为。命中红线即拒绝/升级人工确认，
并写告警到 company/safety/incidents.md。
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List

from engine.workspace import WorkspaceManager


class ComplianceChecker:
    """合规红线检查器 - 6 条红线不得突破"""

    REDLINES = [
        "fraud",            # 欺诈：虚假宣传、刷单、评论操纵
        "manipulation",     # 市场操纵：拉盘砸盘、wash trading
        "laundering",       # 洗钱：来路不明资金转移
        "large_outflow",    # 大额出款：单笔超 $100 需人工确认
        "privacy_leak",     # 隐私泄露：密钥进 Prompt/日志
        "illegal_content",  # 违法内容
    ]

    # 各红线的命中关键词（小写比对）
    FRAUD_KEYWORDS = (
        "刷单", "好评返现", "虚假评论", "刷量", "虚假宣传",
        # 金融欺诈
        "保本保息", "高收益", "稳赚", "保收益", "无风险", "零风险",
        "保证收益", "保本理财", "庞氏", "资金盘", "拉人头", "传销",
        "100%保本", "百分百保本", "稳赚不赔", "零投资零风险",
    )
    MANIPULATION_KEYWORDS = ("拉盘", "砸盘", "wash trading", "pump dump", "操纵价格")
    LAUNDERING_KEYWORDS = ("混币", "来路不明", "匿名转移", "洗钱")
    ILLEGAL_CONTENT_KEYWORDS = ("赌博", "色情", "毒品", "武器", "伪造证件")

    def __init__(self, workspace=None):
        self.workspace = workspace or WorkspaceManager()

    # ------------------------------------------------------------------
    # 主入口
    # ------------------------------------------------------------------
    def check_compliance(self, action: Dict[str, Any]) -> Dict[str, Any]:
        """逐条检查 6 条红线。

        action 字段：
          - type: decision/content/payment/outflow
          - content: 文本/描述（首选字段）
          - description: 文本/描述（content 缺失时的兼容字段）
          - amount: 金额（可选）
          - prompt: LLM prompt（可选）

        返回 {passed, violations, details}：
          - passed: True 表示通过所有检查
          - violations: 命中的红线名称列表
          - details: 文字说明
        """
        # 兼容 content 与 description 字段：优先 content，缺失时回退 description
        content = action.get("content") or action.get("description") or ""
        amount = action.get("amount")
        prompt = action.get("prompt") or ""

        violations: List[str] = []
        details_parts: List[str] = []

        # 1. 欺诈
        if not self._check_fraud(content):
            violations.append("fraud")
            details_parts.append("命中欺诈红线（虚假宣传/刷单/评论操纵）")

        # 2. 市场操纵
        if not self._check_manipulation(content):
            violations.append("manipulation")
            details_parts.append("命中市场操纵红线（拉盘砸盘/wash trading）")

        # 3. 洗钱
        if not self._check_laundering(content):
            violations.append("laundering")
            details_parts.append("命中洗钱红线（来路不明资金转移）")

        # 4. 大额出款（仅在存在 amount 时检查）
        if amount is not None and not self._check_large_outflow(amount):
            violations.append("large_outflow")
            details_parts.append(f"大额出款 ${amount} 超 $100，需人工确认（非拒绝）")

        # 5. 隐私泄露：扫描 content + prompt 合并文本，覆盖 description 含敏感数据场景
        all_text = f"{content} {prompt}".strip()
        if not self._check_privacy_leak(all_text):
            violations.append("privacy_leak")
            details_parts.append("命中隐私泄露红线（密钥/敏感信息进入 Prompt）")

        # 6. 违法内容
        if not self._check_illegal_content(content):
            violations.append("illegal_content")
            details_parts.append("命中违法内容红线（赌博/色情/毒品/武器/伪造证件）")

        passed = len(violations) == 0
        details = "通过所有合规检查" if passed else "；".join(details_parts)

        # 命中红线即写告警
        for redline in violations:
            self.log_incident(redline, action, details)

        return {
            "passed": passed,
            "violations": violations,
            "details": details,
        }

    # ------------------------------------------------------------------
    # 各红线检查（返回 True=通过，False=违规）
    # ------------------------------------------------------------------
    def _check_fraud(self, content: str) -> bool:
        """欺诈：虚假宣传、刷单、评论操纵。命中返回 False。"""
        return not self._contains_any(content, self.FRAUD_KEYWORDS)

    def _check_manipulation(self, content: str) -> bool:
        """市场操纵：拉盘砸盘、wash trading、pump dump、操纵价格。命中返回 False。"""
        return not self._contains_any(content, self.MANIPULATION_KEYWORDS)

    def _check_laundering(self, content: str) -> bool:
        """洗钱：混币、来路不明、匿名转移、洗钱。命中返回 False。"""
        return not self._contains_any(content, self.LAUNDERING_KEYWORDS)

    def _check_large_outflow(self, amount) -> bool:
        """大额出款：amount > 100 返回 False（需人工确认，非拒绝）。"""
        try:
            value = float(amount)
        except (TypeError, ValueError):
            return True
        return value <= 100

    def _check_privacy_leak(self, prompt) -> bool:
        """隐私泄露：调用 SecretsManager.scan_prompt 检测敏感模式。命中返回 False。

        若无 prompt 字段，跳过此检查（返回 True）。
        """
        if not prompt:
            return True
        # 优先使用 SecretsManager.scan_prompt（来自 engine.secrets）
        try:
            from engine.secrets import SecretsManager
            sm = SecretsManager()
            result = sm.scan_prompt(prompt)
            # scan_prompt 可能返回：敏感模式列表 / 布尔值 / 脱敏后的字符串
            if isinstance(result, str):
                # 脱敏字符串：与原文不同即存在泄露
                if result != prompt:
                    return False
            elif result:
                # 非空列表或 True 即存在泄露
                return False
            return True
        except ImportError:
            # SecretsManager 尚未实现时，使用内置兜底敏感模式
            fallback_patterns = ("sk-", "paypal:", "client_secret", "mnemonic", "private_key")
            lower = prompt.lower()
            for pat in fallback_patterns:
                if pat in lower:
                    return False
            return True

    def _check_illegal_content(self, content: str) -> bool:
        """违法内容：赌博、色情、毒品、武器、伪造证件。命中返回 False。"""
        return not self._contains_any(content, self.ILLEGAL_CONTENT_KEYWORDS)

    # ------------------------------------------------------------------
    # 告警
    # ------------------------------------------------------------------
    def log_incident(self, redline: str, action: Dict[str, Any], details: str) -> str:
        """命中红线时写告警到 company/safety/incidents.md，返回文件路径。

        格式：时间戳 / 红线类型 / 动作描述 / 详情
        """
        path = self.workspace.root_dir / "safety" / "incidents.md"
        self.workspace.ensure_dir(path.parent)

        timestamp = datetime.datetime.now().isoformat(timespec="seconds")
        action_desc = self._describe_action(action)
        entry = (
            f"\n## {timestamp} | {redline}\n"
            f"- 动作: {action_desc}\n"
            f"- 详情: {details}\n"
        )
        with path.open("a", encoding="utf-8") as f:
            f.write(entry)
        return str(path)

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _contains_any(text: str, keywords) -> bool:
        """简单字符串包含匹配（关键词小写比对）。"""
        if not text:
            return False
        lower = text.lower()
        return any(kw.lower() in lower for kw in keywords)

    @staticmethod
    def _describe_action(action: Dict[str, Any]) -> str:
        """把 action dict 压缩成单行描述（脱敏，避免把 prompt 全文写进告警）。"""
        if not isinstance(action, dict):
            return str(action)
        parts: List[str] = []
        if action.get("type"):
            parts.append(f"type={action['type']}")
        if action.get("content"):
            content = str(action["content"])
            parts.append(f"content={content[:80]}")
        if action.get("amount") is not None:
            parts.append(f"amount={action['amount']}")
        if action.get("prompt"):
            parts.append("prompt=<redacted>")
        return " ".join(parts) if parts else "<empty>"
