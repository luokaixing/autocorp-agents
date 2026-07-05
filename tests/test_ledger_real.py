"""Ledger 真实/虚拟收入分离 单元测试

验证 income_real / expense_real / audit 升级 / 老数据兼容 / tx_ref 记录。
使用标准库 unittest，可直接 `python -m unittest tests.test_ledger_real` 运行。
也兼容 pytest 风格。
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.workspace import WorkspaceManager
from engine.ledger import Ledger


class TestLedgerReal(unittest.TestCase):
    """真实/虚拟收入分离测试套件。"""

    def setUp(self) -> None:
        # 每个测试用例使用独立的临时目录作为工作区根目录
        self.tmp_root = Path(tempfile.mkdtemp(prefix="autocorp_ledger_real_"))
        self.ws = WorkspaceManager(root_dir=self.tmp_root)
        self.ws.initialize()
        self.ledger = Ledger(self.ws)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    # ------------------------------------------------------------------
    # income_real
    # ------------------------------------------------------------------
    def test_income_real_marks_is_real_true(self) -> None:
        """income_real 应标记 is_real=true 并记录 tx_ref。"""
        tx_id = self.ledger.income_real(
            500.0, "paypal", "PAYPAL-ORDER-12345", "PayPal 收款"
        )

        self.assertEqual(self.ledger.balance(), 10500.0)
        self.assertEqual(tx_id, "tx_001")

        txns = self.ledger.list_transactions()
        self.assertEqual(len(txns), 1)
        tx = txns[0]
        self.assertTrue(tx["is_real"])
        self.assertEqual(tx["tx_ref"], "PAYPAL-ORDER-12345")
        self.assertEqual(tx["type"], "income")
        self.assertEqual(tx["amount"], 500.0)
        self.assertEqual(tx["source"], "paypal")

    def test_income_real_requires_tx_ref(self) -> None:
        """income_real 缺少 tx_ref 应抛 ValueError。"""
        with self.assertRaises(ValueError):
            self.ledger.income_real(100.0, "paypal", "")

    def test_income_real_invalid_amount(self) -> None:
        """income_real 非正金额应抛 ValueError。"""
        with self.assertRaises(ValueError):
            self.ledger.income_real(0.0, "paypal", "tx-1")

    # ------------------------------------------------------------------
    # expense_real
    # ------------------------------------------------------------------
    def test_expense_real_marks_is_real_true(self) -> None:
        """expense_real 应标记 is_real=true 并记录 tx_ref、decision_ref。"""
        tx_id = self.ledger.expense_real(
            300.0,
            "crypto_payment",
            tx_ref="0xabc123",
            description="链上付款",
            decision_ref="2026-06-27-reinvest-crypto.md",
        )

        self.assertEqual(self.ledger.balance(), 9700.0)
        self.assertEqual(tx_id, "tx_001")

        txns = self.ledger.list_transactions()
        self.assertEqual(len(txns), 1)
        tx = txns[0]
        self.assertTrue(tx["is_real"])
        self.assertEqual(tx["tx_ref"], "0xabc123")
        self.assertEqual(tx["decision_ref"], "2026-06-27-reinvest-crypto.md")
        self.assertEqual(tx["type"], "expense")
        self.assertEqual(tx["amount"], 300.0)

    def test_expense_real_insufficient_balance_raises(self) -> None:
        """余额不足时 expense_real 应抛出 ValueError。"""
        with self.assertRaises(ValueError):
            self.ledger.expense_real(10001.0, "overspend", tx_ref="tx-x")
        # 余额未变，未写入交易
        self.assertEqual(self.ledger.balance(), 10000.0)
        self.assertEqual(self.ledger.list_transactions(), [])

    def test_expense_real_tx_ref_optional(self) -> None:
        """expense_real 的 tx_ref 可选（默认空串）。"""
        self.ledger.expense_real(100.0, "cash")
        tx = self.ledger.list_transactions()[0]
        self.assertTrue(tx["is_real"])
        self.assertEqual(tx["tx_ref"], "")

    # ------------------------------------------------------------------
    # 老方法 income / expense 默认虚拟
    # ------------------------------------------------------------------
    def test_income_marks_is_real_false(self) -> None:
        """老方法 income 应标记 is_real=false。"""
        self.ledger.income(500.0, "product_sales", "模拟收入")

        tx = self.ledger.list_transactions()[0]
        self.assertFalse(tx["is_real"])
        self.assertEqual(tx.get("tx_ref"), "")

    def test_expense_marks_is_real_false(self) -> None:
        """老方法 expense 应标记 is_real=false。"""
        self.ledger.expense(300.0, "api_quota", "购买 API 额度")

        tx = self.ledger.list_transactions()[0]
        self.assertFalse(tx["is_real"])
        self.assertEqual(tx.get("tx_ref"), "")

    # ------------------------------------------------------------------
    # audit 区分 real / virtual
    # ------------------------------------------------------------------
    def test_audit_separates_real_and_virtual(self) -> None:
        """audit 应正确区分真实/虚拟收入与支出汇总。"""
        # 虚拟：income 500, expense 300
        self.ledger.income(500.0, "product_sales")
        self.ledger.expense(300.0, "api_quota")
        # 真实：income_real 1000, expense_real 200
        self.ledger.income_real(1000.0, "paypal", "PAYPAL-ORDER-1")
        self.ledger.expense_real(200.0, "crypto", tx_ref="0x1")

        summary = self.ledger.audit()
        # 余额 = 10000 + 500 - 300 + 1000 - 200 = 11000
        self.assertEqual(summary["balance"], 11000.0)
        # 总计
        self.assertEqual(summary["total_income"], 1500.0)
        self.assertEqual(summary["total_expense"], 500.0)
        # 真实
        self.assertEqual(summary["real_total_income"], 1000.0)
        self.assertEqual(summary["real_total_expense"], 200.0)
        # 虚拟
        self.assertEqual(summary["virtual_total_income"], 500.0)
        self.assertEqual(summary["virtual_total_expense"], 300.0)
        # 交易笔数
        self.assertEqual(summary["transaction_count"], 4)
        # recent_transactions 每条含 is_real 字段
        for t in summary["recent_transactions"]:
            self.assertIn("is_real", t)

    def test_audit_real_zero_when_all_virtual(self) -> None:
        """全部虚拟交易时，真实汇总应为 0。"""
        self.ledger.income(500.0, "sim")
        self.ledger.expense(100.0, "sim")

        summary = self.ledger.audit()
        self.assertEqual(summary["real_total_income"], 0.0)
        self.assertEqual(summary["real_total_expense"], 0.0)
        self.assertEqual(summary["virtual_total_income"], 500.0)
        self.assertEqual(summary["virtual_total_expense"], 100.0)

    def test_audit_virtual_zero_when_all_real(self) -> None:
        """全部真实交易时，虚拟汇总应为 0。"""
        self.ledger.income_real(500.0, "paypal", "tx-1")
        self.ledger.expense_real(100.0, "crypto", tx_ref="0x1")

        summary = self.ledger.audit()
        self.assertEqual(summary["real_total_income"], 500.0)
        self.assertEqual(summary["real_total_expense"], 100.0)
        self.assertEqual(summary["virtual_total_income"], 0.0)
        self.assertEqual(summary["virtual_total_expense"], 0.0)

    def test_audit_recent_transactions_contain_is_real(self) -> None:
        """audit 返回的 recent_transactions 每条应含 is_real 字段。"""
        # 先虚拟、后真实：倒序后真实交易排在最前（最新在前）
        self.ledger.income(200.0, "sim")
        self.ledger.income_real(100.0, "paypal", "tx-1")

        summary = self.ledger.audit()
        self.assertEqual(len(summary["recent_transactions"]), 2)
        # 真实交易在前（倒序，最新在前），is_real=True
        self.assertTrue(summary["recent_transactions"][0]["is_real"])
        self.assertFalse(summary["recent_transactions"][1]["is_real"])

    def test_audit_preserves_legacy_fields(self) -> None:
        """audit 升级后应保留原有 balance / total_income / total_expense 等字段。"""
        self.ledger.income(100.0, "s")
        summary = self.ledger.audit()
        for key in (
            "balance",
            "currency",
            "initial_capital",
            "total_income",
            "total_expense",
            "transaction_count",
            "recent_transactions",
        ):
            self.assertIn(key, summary)

    # ------------------------------------------------------------------
    # 兼容老 ledger.yaml（无 is_real 字段）
    # ------------------------------------------------------------------
    def test_compat_old_ledger_without_is_real(self) -> None:
        """老 ledger.yaml 中无 is_real 字段的交易，加载后应默认为 false（虚拟）。"""
        # 手工写入一份老格式账本（无 is_real / tx_ref 字段）
        old_data = {
            "balance": 9500.0,
            "currency": "USD",
            "initial_capital": 10000.0,
            "transactions": [
                {
                    "id": "tx_001",
                    "type": "income",
                    "amount": 500.0,
                    "timestamp": "2026-06-26T10:00:00",
                    "source": "legacy_sales",
                    "description": "老数据收入",
                    "decision_ref": None,
                },
                {
                    "id": "tx_002",
                    "type": "expense",
                    "amount": 1000.0,
                    "timestamp": "2026-06-26T11:00:00",
                    "source": "legacy_cost",
                    "description": "老数据支出",
                    "decision_ref": None,
                },
            ],
        }
        self.ws.write_yaml(self.ws.ledger_config_path, old_data)

        # 重新实例化 Ledger，触发 _ensure_ledger 兼容迁移
        ledger = Ledger(self.ws)

        txns = ledger.list_transactions()
        self.assertEqual(len(txns), 2)
        for t in txns:
            self.assertFalse(t["is_real"])
            self.assertEqual(t["tx_ref"], "")

        # audit 应将老交易归入虚拟汇总
        summary = ledger.audit()
        self.assertEqual(summary["real_total_income"], 0.0)
        self.assertEqual(summary["real_total_expense"], 0.0)
        self.assertEqual(summary["virtual_total_income"], 500.0)
        self.assertEqual(summary["virtual_total_expense"], 1000.0)
        self.assertEqual(summary["balance"], 9500.0)

    # ------------------------------------------------------------------
    # tx_ref 正确记录
    # ------------------------------------------------------------------
    def test_tx_ref_recorded_correctly(self) -> None:
        """tx_ref 应正确记录外部交易号（PayPal order_id / 区块链 tx_hash）。"""
        # PayPal order_id
        paypal_id = self.ledger.income_real(50.0, "paypal", "PAYPAL-ORDER-ABC123")
        paypal_tx = self.ledger.list_transactions()[0]
        self.assertEqual(paypal_id, "tx_001")
        self.assertEqual(paypal_tx["tx_ref"], "PAYPAL-ORDER-ABC123")

        # 区块链 tx_hash（倒序，最新在前）
        self.ledger.income_real(0.05, "crypto_usdt", "0xdeadbeef1234567890")
        crypto_tx = self.ledger.list_transactions()[0]
        self.assertEqual(crypto_tx["tx_ref"], "0xdeadbeef1234567890")

    def test_tx_ref_distinct_from_decision_ref(self) -> None:
        """tx_ref（外部交易号）与 decision_ref（决策日志）应分别独立记录。"""
        self.ledger.expense_real(
            150.0,
            "marketing",
            tx_ref="PAYPAL-PAYOUT-XYZ",
            decision_ref="2026-06-27-reinvest-marketing.md",
        )
        tx = self.ledger.list_transactions()[0]
        self.assertEqual(tx["tx_ref"], "PAYPAL-PAYOUT-XYZ")
        self.assertEqual(tx["decision_ref"], "2026-06-27-reinvest-marketing.md")


if __name__ == "__main__":
    unittest.main()
