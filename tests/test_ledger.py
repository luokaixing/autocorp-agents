"""Ledger 单元测试

使用标准库 unittest，可直接 `python -m unittest tests.test_ledger` 运行。
也兼容 pytest 风格。
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.workspace import WorkspaceManager
from engine.ledger import Ledger


class TestLedger(unittest.TestCase):
    """Ledger 测试套件。"""

    def setUp(self) -> None:
        # 每个测试用例使用独立的临时目录作为工作区根目录
        self.tmp_root = Path(tempfile.mkdtemp(prefix="autocorp_ledger_"))
        self.ws = WorkspaceManager(root_dir=self.tmp_root)
        self.ws.initialize()
        self.ledger = Ledger(self.ws)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    # ------------------------------------------------------------------
    # 初始余额
    # ------------------------------------------------------------------
    def test_initial_balance(self) -> None:
        """初始余额应为 $10,000。"""
        self.assertEqual(self.ledger.balance(), 10000.0)

    def test_initial_capital_compat(self) -> None:
        """WorkspaceManager 创建的账本无 initial_capital，Ledger 应兼容补齐。"""
        data = self.ws.read_yaml(self.ws.ledger_config_path)
        self.assertIn("initial_capital", data)
        self.assertEqual(data["initial_capital"], 10000.0)

    # ------------------------------------------------------------------
    # income
    # ------------------------------------------------------------------
    def test_income_increases_balance(self) -> None:
        """income 应正确增加余额并记录交易。"""
        tx_id = self.ledger.income(500.0, "product_sales", "首个产品首日收入")

        self.assertEqual(self.ledger.balance(), 10500.0)
        self.assertEqual(tx_id, "tx_001")

        txns = self.ledger.list_transactions()
        self.assertEqual(len(txns), 1)
        tx = txns[0]
        self.assertEqual(tx["id"], "tx_001")
        self.assertEqual(tx["type"], "income")
        self.assertEqual(tx["amount"], 500.0)
        self.assertEqual(tx["source"], "product_sales")
        self.assertEqual(tx["description"], "首个产品首日收入")
        self.assertIsNone(tx["decision_ref"])
        self.assertIn("timestamp", tx)

    # ------------------------------------------------------------------
    # expense
    # ------------------------------------------------------------------
    def test_expense_decreases_balance(self) -> None:
        """expense 应正确扣减余额并记录交易。"""
        tx_id = self.ledger.expense(300.0, "api_quota", "购买 API 额度")

        self.assertEqual(self.ledger.balance(), 9700.0)
        self.assertEqual(tx_id, "tx_001")

        txns = self.ledger.list_transactions()
        self.assertEqual(len(txns), 1)
        tx = txns[0]
        self.assertEqual(tx["id"], "tx_001")
        self.assertEqual(tx["type"], "expense")
        self.assertEqual(tx["amount"], 300.0)
        self.assertEqual(tx["source"], "api_quota")

    def test_expense_records_decision_ref(self) -> None:
        """再投资支出应记录 decision_ref。"""
        tx_id = self.ledger.expense(
            1000.0,
            "marketing",
            "营销预算",
            decision_ref="2026-06-27-reinvest-marketing.md",
        )

        txns = self.ledger.list_transactions()
        self.assertEqual(txns[0]["decision_ref"], "2026-06-27-reinvest-marketing.md")
        self.assertEqual(tx_id, "tx_001")

    def test_expense_insufficient_balance_raises(self) -> None:
        """余额不足时 expense 应抛出 ValueError。"""
        # 初始余额 10000，支出 10001 必然不足
        with self.assertRaises(ValueError):
            self.ledger.expense(10001.0, "overspend")

        # 余额未变
        self.assertEqual(self.ledger.balance(), 10000.0)
        # 未写入交易记录
        self.assertEqual(self.ledger.list_transactions(), [])

    # ------------------------------------------------------------------
    # audit
    # ------------------------------------------------------------------
    def test_audit_summary(self) -> None:
        """audit 应返回正确的摘要。"""
        self.ledger.income(500.0, "product_sales")
        self.ledger.expense(300.0, "api_quota")
        self.ledger.income(200.0, "consulting")

        summary = self.ledger.audit()
        # 余额 = 10000 + 500 - 300 + 200 = 10400
        self.assertEqual(summary["balance"], 10400.0)
        self.assertEqual(summary["currency"], "USD")
        self.assertEqual(summary["initial_capital"], 10000.0)
        self.assertEqual(summary["total_income"], 700.0)
        self.assertEqual(summary["total_expense"], 300.0)
        self.assertEqual(summary["transaction_count"], 3)
        # 最近5笔（此处共3笔，倒序：最新在前）
        self.assertEqual(len(summary["recent_transactions"]), 3)
        self.assertEqual(summary["recent_transactions"][0]["id"], "tx_003")

    def test_audit_empty_ledger(self) -> None:
        """空账本的 audit 摘要应为零值。"""
        summary = self.ledger.audit()
        self.assertEqual(summary["balance"], 10000.0)
        self.assertEqual(summary["total_income"], 0)
        self.assertEqual(summary["total_expense"], 0)
        self.assertEqual(summary["transaction_count"], 0)
        self.assertEqual(summary["recent_transactions"], [])

    # ------------------------------------------------------------------
    # 交易 id 自增
    # ------------------------------------------------------------------
    def test_transaction_id_auto_increment(self) -> None:
        """交易 id 应自增：tx_001, tx_002, tx_003..."""
        id1 = self.ledger.income(100.0, "s1")
        id2 = self.ledger.expense(50.0, "e1")
        id3 = self.ledger.income(200.0, "s2")

        self.assertEqual(id1, "tx_001")
        self.assertEqual(id2, "tx_002")
        self.assertEqual(id3, "tx_003")

    # ------------------------------------------------------------------
    # can_afford
    # ------------------------------------------------------------------
    def test_can_afford(self) -> None:
        """can_afford 应正确判断余额是否足够。"""
        self.assertTrue(self.ledger.can_afford(10000.0))
        self.assertTrue(self.ledger.can_afford(5000.0))
        self.assertFalse(self.ledger.can_afford(10000.01))

    # ------------------------------------------------------------------
    # list_transactions
    # ------------------------------------------------------------------
    def test_list_transactions_limit(self) -> None:
        """list_transactions 应按倒序返回最近 N 笔交易。"""
        for i in range(7):
            self.ledger.income(10.0 * (i + 1), f"src_{i}")

        # 默认 limit=10，但只有 7 笔
        all_tx = self.ledger.list_transactions()
        self.assertEqual(len(all_tx), 7)
        # 最新在前：第一笔应为 tx_007
        self.assertEqual(all_tx[0]["id"], "tx_007")
        self.assertEqual(all_tx[-1]["id"], "tx_001")

        # limit=3：最近 3 笔，倒序
        recent3 = self.ledger.list_transactions(limit=3)
        self.assertEqual(len(recent3), 3)
        self.assertEqual([t["id"] for t in recent3], ["tx_007", "tx_006", "tx_005"])

    # ------------------------------------------------------------------
    # 持久化
    # ------------------------------------------------------------------
    def test_persistence_across_instances(self) -> None:
        """新实例应读取到已持久化的余额与交易。"""
        self.ledger.income(500.0, "product_sales")
        self.assertEqual(self.ledger.balance(), 10500.0)

        # 用同一 workspace 重新实例化
        new_ledger = Ledger(self.ws)
        self.assertEqual(new_ledger.balance(), 10500.0)
        self.assertEqual(len(new_ledger.list_transactions()), 1)


if __name__ == "__main__":
    unittest.main()
