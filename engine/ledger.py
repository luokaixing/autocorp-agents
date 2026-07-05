"""虚拟资产账本

追踪 AI 虚拟公司 AutoCorp 的美元余额、收入、支出与交易记录。
账本文件持久化于 company/config/ledger.yaml，通过 WorkspaceManager 读写。

升级：支持真实收入（实际到账，如 PayPal / 加密货币）与虚拟收入（模拟/估算）分离。
交易记录新增 is_real (bool) / tx_ref (str) 字段；audit 分别汇总 real / virtual。
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, List, Optional

from engine.workspace import WorkspaceManager


class Ledger:
    """虚拟资产账本 - 追踪美元余额、收入、支出、交易记录"""

    # 默认初始资本（与 WorkspaceManager.initialize 保持一致）
    DEFAULT_INITIAL_CAPITAL = 10000.0

    def __init__(self, workspace: WorkspaceManager) -> None:
        self.workspace = workspace
        self.ledger_path = workspace.config_dir / "ledger.yaml"
        # 初始化时确保账本存在且字段格式兼容
        self._ensure_ledger()

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------
    def _load(self) -> Dict[str, Any]:
        """读取账本数据；文件不存在时返回默认结构。"""
        data = self.workspace.read_yaml(self.ledger_path)
        if data is None:
            data = {
                "balance": self.DEFAULT_INITIAL_CAPITAL,
                "currency": "USD",
                "initial_capital": self.DEFAULT_INITIAL_CAPITAL,
                "transactions": [],
            }
        return data

    def _save(self, data: Dict[str, Any]) -> None:
        """写入账本数据。"""
        self.workspace.write_yaml(self.ledger_path, data)

    def _ensure_ledger(self) -> None:
        """兼容处理：确保账本含 initial_capital / currency / transactions 字段。

        WorkspaceManager.initialize() 创建的初始账本无 initial_capital 字段，
        在此补齐，使账本格式统一。

        升级：老交易记录无 is_real / tx_ref 字段时，默认补齐为虚拟（is_real=false）。
        """
        data = self._load()
        changed = False
        if "initial_capital" not in data:
            # 老格式无 initial_capital，用当前余额（或默认值）补齐
            data["initial_capital"] = float(data.get("balance", self.DEFAULT_INITIAL_CAPITAL))
            changed = True
        if "currency" not in data:
            data["currency"] = "USD"
            changed = True
        if not data.get("transactions"):
            data["transactions"] = []
            changed = True
        # 兼容老交易记录：补齐 is_real / tx_ref 字段（无 is_real 默认为虚拟）
        for t in data.get("transactions", []) or []:
            if "is_real" not in t:
                t["is_real"] = False
                changed = True
            if "tx_ref" not in t:
                t["tx_ref"] = ""
                changed = True
        if changed:
            self._save(data)

    def _next_tx_id(self, transactions: List[Dict[str, Any]]) -> str:
        """根据现有交易数生成下一个交易 id：tx_001, tx_002..."""
        seq = len(transactions) + 1
        return f"tx_{seq:03d}"

    # ------------------------------------------------------------------
    # 核心接口
    # ------------------------------------------------------------------
    def balance(self) -> float:
        """返回当前余额。"""
        return float(self._load()["balance"])

    def income(self, amount: float, source: str, description: str = "") -> str:
        """记录一笔收入（虚拟），增加余额并写入交易记录。返回交易 id。

        老接口保持向后兼容：记录的交易 is_real=false。
        """
        if amount <= 0:
            raise ValueError("收入金额必须为正数")
        data = self._load()
        tx_id = self._next_tx_id(data["transactions"])
        data["balance"] = float(data["balance"]) + amount
        data["transactions"].append({
            "id": tx_id,
            "type": "income",
            "amount": float(amount),
            "timestamp": datetime.datetime.now().isoformat(),
            "source": source,
            "description": description,
            "decision_ref": None,
            "is_real": False,
            "tx_ref": "",
        })
        self._save(data)
        return tx_id

    def expense(
        self,
        amount: float,
        purpose: str,
        description: str = "",
        decision_ref: Optional[str] = None,
    ) -> str:
        """记录一笔支出（虚拟），扣减余额并写入交易记录。返回交易 id。

        - 余额不足时抛 ValueError
        - 若金额超过当前余额 30%，打印「大额支出，建议 CEO 审批」警告
        - decision_ref 用于关联再投资（如购买 API 额度、营销预算）的决策日志文件名
        - 老接口保持向后兼容：记录的交易 is_real=false
        """
        if amount <= 0:
            raise ValueError("支出金额必须为正数")
        data = self._load()
        current_balance = float(data["balance"])
        if amount > current_balance:
            raise ValueError(f"余额不足：当前余额 {current_balance}，需支出 {amount}")
        # 大额支出警告
        if amount > current_balance * 0.3:
            print("警告：大额支出，建议 CEO 审批")
        tx_id = self._next_tx_id(data["transactions"])
        data["balance"] = current_balance - amount
        data["transactions"].append({
            "id": tx_id,
            "type": "expense",
            "amount": float(amount),
            "timestamp": datetime.datetime.now().isoformat(),
            "source": purpose,
            "description": description,
            "decision_ref": decision_ref,
            "is_real": False,
            "tx_ref": "",
        })
        self._save(data)
        return tx_id

    # ------------------------------------------------------------------
    # 真实收入 / 真实支出（对接外部支付通道，如 PayPal / 加密货币）
    # ------------------------------------------------------------------
    def income_real(self, amount: float, source: str, tx_ref: str, description: str = "") -> str:
        """记录一笔真实收入（实际到账），增加余额并写入交易记录。返回交易 id。

        - 交易记录标记 is_real=true，附带 tx_ref（外部交易号，如 PayPal order_id 或区块链 tx_hash）
        """
        if amount <= 0:
            raise ValueError("收入金额必须为正数")
        if not tx_ref:
            raise ValueError("真实收入必须提供 tx_ref（外部交易号）")
        data = self._load()
        tx_id = self._next_tx_id(data["transactions"])
        data["balance"] = float(data["balance"]) + amount
        data["transactions"].append({
            "id": tx_id,
            "type": "income",
            "amount": float(amount),
            "timestamp": datetime.datetime.now().isoformat(),
            "source": source,
            "description": description,
            "decision_ref": None,
            "is_real": True,
            "tx_ref": tx_ref,
        })
        self._save(data)
        return tx_id

    def expense_real(
        self,
        amount: float,
        purpose: str,
        tx_ref: str = "",
        description: str = "",
        decision_ref: Optional[str] = None,
    ) -> str:
        """记录一笔真实支出（实际付款），扣减余额并写入交易记录。返回交易 id。

        - 余额不足时抛 ValueError
        - 若金额超过当前余额 30%，打印「大额支出，建议 CEO 审批」警告
        - 交易记录标记 is_real=true，附带 tx_ref、decision_ref（关联决策日志）
        """
        if amount <= 0:
            raise ValueError("支出金额必须为正数")
        data = self._load()
        current_balance = float(data["balance"])
        if amount > current_balance:
            raise ValueError(f"余额不足：当前余额 {current_balance}，需支出 {amount}")
        # 大额支出警告
        if amount > current_balance * 0.3:
            print("警告：大额支出，建议 CEO 审批")
        tx_id = self._next_tx_id(data["transactions"])
        data["balance"] = current_balance - amount
        data["transactions"].append({
            "id": tx_id,
            "type": "expense",
            "amount": float(amount),
            "timestamp": datetime.datetime.now().isoformat(),
            "source": purpose,
            "description": description,
            "decision_ref": decision_ref,
            "is_real": True,
            "tx_ref": tx_ref,
        })
        self._save(data)
        return tx_id

    def audit(self) -> Dict[str, Any]:
        """返回账本摘要：余额、总收入、总支出、交易笔数、最近5笔交易。

        升级：新增 real_total_income / real_total_expense / virtual_total_income /
        virtual_total_expense 字段区分真实与虚拟资金；recent_transactions 每条含 is_real。
        保留原有 balance / total_income / total_expense / transaction_count 字段。
        """
        data = self._load()
        transactions = data.get("transactions", []) or []
        total_income = sum(t["amount"] for t in transactions if t.get("type") == "income")
        total_expense = sum(t["amount"] for t in transactions if t.get("type") == "expense")
        # 真实收入/支出汇总（老交易无 is_real 字段默认为虚拟）
        real_total_income = sum(
            t["amount"] for t in transactions
            if t.get("type") == "income" and t.get("is_real", False)
        )
        real_total_expense = sum(
            t["amount"] for t in transactions
            if t.get("type") == "expense" and t.get("is_real", False)
        )
        # 虚拟 = 总计 - 真实
        virtual_total_income = total_income - real_total_income
        virtual_total_expense = total_expense - real_total_expense
        # 最近5笔，按时间倒序（最新在前）
        recent = list(reversed(transactions[-5:]))
        # 确保 recent 每条含 is_real 字段（兼容未迁移数据）
        for t in recent:
            t.setdefault("is_real", False)
        return {
            "balance": float(data["balance"]),
            "currency": data.get("currency", "USD"),
            "initial_capital": float(data.get("initial_capital", self.DEFAULT_INITIAL_CAPITAL)),
            "total_income": total_income,
            "total_expense": total_expense,
            "real_total_income": real_total_income,
            "real_total_expense": real_total_expense,
            "virtual_total_income": virtual_total_income,
            "virtual_total_expense": virtual_total_expense,
            "transaction_count": len(transactions),
            "recent_transactions": recent,
        }

    def list_transactions(self, limit: int = 10) -> List[Dict[str, Any]]:
        """返回最近 N 笔交易（按时间倒序，最新在前）。"""
        data = self._load()
        transactions = data.get("transactions", []) or []
        if limit <= 0:
            return []
        recent = transactions[-limit:]
        return list(reversed(recent))

    def can_afford(self, amount: float) -> bool:
        """判断当前余额是否足够支付指定金额。"""
        return self.balance() >= amount
