"""加密货币出币安全闸门

AutoCorp 禁止 AI 自主转出加密货币。任何出币操作必须经人工确认，
AI 不持有私钥签名权限。本模块仅负责：
1. 构造出币请求的决策上下文，交给 HumanLoop 请求人工确认
2. 记录所有出币请求（无论批准与否）到 company/safety/crypto-outflows.md
3. 在用户批准后，返回手动签名指引（实际签名由用户在钱包软件中完成）

关键安全约束：本模块永不读取、永不持有、永不使用私钥；
approved=True 仅表示用户同意出币，AI 不会执行任何签名或广播动作。
"""
from __future__ import annotations

import datetime
from typing import Any, Dict


class CryptoOutflowGate:
    """加密货币出币安全闸门 - 禁止 AI 自主转出，必须人工确认"""

    def __init__(self, workspace=None, human_loop=None):
        from engine.workspace import WorkspaceManager
        from engine.human_loop import HumanLoop

        self.workspace = workspace or WorkspaceManager()
        # 复用传入的 HumanLoop，确保 handler 桥接（如 AskUserQuestion）能生效
        self.human_loop = human_loop or HumanLoop(self.workspace)

    # ------------------------------------------------------------------
    # 对外 API
    # ------------------------------------------------------------------
    def request_outflow(self, outflow_request: Dict[str, Any]) -> Dict[str, Any]:
        """请求出币 - 强制走人工确认，AI 不执行签名。

        Args:
            outflow_request: 出币请求，字段：
                - chain: 链名（如 Ethereum / Bitcoin / Tron）
                - from_address: 发起地址
                - to_address: 收款地址
                - amount: 出币金额
                - asset: 资产符号（ETH / BTC / USDT 等）
                - reason: 出币原因（如「参与流动性挖矿」）

        Returns:
            {approved, reason, human_response, request}
            - approved: True 仅表示用户同意出币，AI 仍不执行签名；
                        实际签名需用户在钱包软件中手动完成
        """
        # 1. 构造给用户看的决策上下文（含风险提示）
        decision_context = self._build_decision_context(outflow_request)

        # 2. 强制调用人工确认（无论金额大小都必须确认）
        approval = self.human_loop.request_approval(decision_context=decision_context)
        human_response = approval.get("response", "")

        # 3. 仅当用户明确选择「批准」才视为同意；其他响应均视为未批准
        approved = human_response == "批准"
        reason = "用户批准出币" if approved else f"用户未批准（响应：{human_response}）"

        # 4. 记录出币请求（无论批准与否都留痕）
        status = "approved" if approved else "rejected"
        self.log_outflow({
            "timestamp": approval.get("timestamp", self._now_ts()),
            "chain": outflow_request.get("chain", ""),
            "from_address": outflow_request.get("from_address", ""),
            "to_address": outflow_request.get("to_address", ""),
            "amount": outflow_request.get("amount", ""),
            "asset": outflow_request.get("asset", ""),
            "reason": outflow_request.get("reason", ""),
            "human_response": human_response,
            "status": status,
        })

        # 5. 关键：AI 不执行任何签名动作，仅返回审批结果
        return {
            "approved": approved,
            "reason": reason,
            "human_response": human_response,
            "request": outflow_request,
        }

    def _build_decision_context(self, outflow_request: Dict[str, Any]) -> str:
        """构造给用户看的决策上下文（含风险提示）。"""
        chain = outflow_request.get("chain", "")
        from_address = outflow_request.get("from_address", "")
        to_address = outflow_request.get("to_address", "")
        amount = outflow_request.get("amount", "")
        asset = outflow_request.get("asset", "")
        reason = outflow_request.get("reason", "")

        return (
            "⚠️ 加密货币出币请求\n"
            f"链: {chain}\n"
            f"从: {from_address}\n"
            f"到: {to_address}\n"
            f"金额: {amount} {asset}\n"
            f"原因: {reason}\n"
            "\n"
            "风险提示:\n"
            "- 请核实收款地址正确\n"
            "- 确认交易费合理\n"
            "- 此操作不可逆\n"
            "\n"
            "AI 不持有私钥，签名需您在钱包软件中手动完成。"
        )

    def log_outflow(self, record: Dict[str, Any]) -> str:
        """将出币请求记录追加到 company/safety/crypto-outflows.md。

        所有出币请求（无论批准与否）均留痕。
        格式：时间戳 / 链 / 从 / 到 / 金额 / 资产 / 原因 / 用户响应 / 状态

        Returns:
            日志文件绝对路径。
        """
        log_path = self.workspace.root_dir / "safety" / "crypto-outflows.md"
        self.workspace.ensure_dir(log_path.parent)

        timestamp = record.get("timestamp", self._now_ts())
        chain = record.get("chain", "")
        from_address = record.get("from_address", "")
        to_address = record.get("to_address", "")
        amount = record.get("amount", "")
        asset = record.get("asset", "")
        reason = record.get("reason", "")
        human_response = record.get("human_response", "")
        status = record.get("status", "")

        entry = (
            f"\n## {timestamp} | {status}\n"
            f"- 链: {chain}\n"
            f"- 从: {from_address}\n"
            f"- 到: {to_address}\n"
            f"- 金额: {amount} {asset}\n"
            f"- 原因: {reason}\n"
            f"- 用户响应: {human_response}\n"
            f"- 状态: {status}\n"
        )

        # 追加写入：文件不存在则带标题创建，已存在则追加
        existing = self.workspace.read_text(log_path)
        if not existing.strip():
            content = "# 加密货币出币请求日志\n" + entry
        else:
            content = existing.rstrip() + "\n" + entry

        self.workspace.write_text(log_path, content)
        return str(log_path.resolve())

    def get_signature_instructions(self, outflow_request: Dict[str, Any]) -> str:
        """返回给用户的手动签名指引（AI 不执行签名）。

        用户批准出币后，按本指引在钱包软件中手动完成签名与广播。
        """
        chain = outflow_request.get("chain", "")
        from_address = outflow_request.get("from_address", "")
        to_address = outflow_request.get("to_address", "")
        amount = outflow_request.get("amount", "")
        asset = outflow_request.get("asset", "")

        return (
            "用户确认后，请按以下步骤手动签名：\n"
            f"1. 打开您的 {chain} 钱包软件\n"
            "2. 导入对应私钥（私钥存于 .secrets/，可用 main.py secrets get wallet_xxx_priv 获取）\n"
            f"3. 构造交易：from {from_address} to {to_address} amount {amount} {asset}\n"
            "4. 签名并广播\n"
            "5. 将 tx_hash 回填：python main.py crypto record-outflow --tx-hash xxx"
        )

    # ------------------------------------------------------------------
    # 辅助
    # ------------------------------------------------------------------
    @staticmethod
    def _now_ts() -> str:
        """返回当前时间戳字符串 YYYY-MM-DD HH:MM:SS。"""
        return datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
