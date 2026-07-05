"""CryptoOutflowGate 单元测试

使用标准库 unittest，可直接 `python -m unittest tests.test_crypto_outflow` 运行。
也兼容 pytest 风格。

核心安全约束验证：
- request_outflow 强制调用 human_loop.request_approval
- 未批准时 approved=False
- 批准时 approved=True 但仍不执行签名（仅返回指引）
- 所有出币请求留痕到 crypto-outflows.md
- 决策上下文包含风险提示
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.crypto.outflow_gate import CryptoOutflowGate
from engine.workspace import WorkspaceManager


class _FakeHumanLoop:
    """伪造的 HumanLoop - 用于控制和观察 request_approval 的调用。

    不依赖 stdin/终端，避免非交互环境下被自动跳过。
    """

    def __init__(self, response: str = "批准"):
        self.response = response
        self.approval_calls = []  # 记录每次 request_approval 的入参

    def request_approval(self, decision_context=None, options=None):
        self.approval_calls.append({
            "decision_context": decision_context,
            "options": list(options) if options else None,
        })
        return {
            "type": "approval",
            "question": f"【决策确认】{decision_context}",
            "options": list(options) if options else ["批准", "拒绝", "需要更多信息"],
            "response": self.response,
            "timestamp": "2026-01-01 00:00:00",
            "context": "",
            "decision_context": decision_context,
            "log_path": "",
        }


class TestCryptoOutflowGate(unittest.TestCase):
    """CryptoOutflowGate 测试套件。"""

    def setUp(self) -> None:
        # 每个测试用例使用独立的临时目录作为工作区根目录，避免污染真实 company/
        self.tmp_root = Path(tempfile.mkdtemp(prefix="autocorp_outflow_"))
        self.ws = WorkspaceManager(root_dir=self.tmp_root)

        # 样例出币请求
        self.sample_request = {
            "chain": "Ethereum",
            "from_address": "0xFROMAAA",
            "to_address": "0xTOBBBBB",
            "amount": 0.5,
            "asset": "ETH",
            "reason": "参与流动性挖矿",
        }

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    # ------------------------------------------------------------------
    # request_outflow 强制调用 human_loop.request_approval
    # ------------------------------------------------------------------
    def test_request_outflow_calls_human_approval(self) -> None:
        fake_hl = _FakeHumanLoop(response="批准")
        gate = CryptoOutflowGate(workspace=self.ws, human_loop=fake_hl)

        gate.request_outflow(self.sample_request)

        # 必须调用一次 request_approval，且传入非空 decision_context
        self.assertEqual(len(fake_hl.approval_calls), 1)
        ctx = fake_hl.approval_calls[0]["decision_context"]
        self.assertTrue(ctx)
        self.assertIn("加密货币出币请求", ctx)

    # ------------------------------------------------------------------
    # 未批准时 approved=False
    # ------------------------------------------------------------------
    def test_not_approved_when_user_rejects(self) -> None:
        fake_hl = _FakeHumanLoop(response="拒绝")
        gate = CryptoOutflowGate(workspace=self.ws, human_loop=fake_hl)

        result = gate.request_outflow(self.sample_request)

        self.assertFalse(result["approved"])
        self.assertEqual(result["human_response"], "拒绝")
        self.assertIn("request", result)
        # 未批准时返回结构中不应出现签名相关字段
        self.assertNotIn("tx_hash", result)
        self.assertNotIn("signed", result)

    # ------------------------------------------------------------------
    # 「需要更多信息」也算未批准
    # ------------------------------------------------------------------
    def test_not_approved_when_needs_more_info(self) -> None:
        fake_hl = _FakeHumanLoop(response="需要更多信息")
        gate = CryptoOutflowGate(workspace=self.ws, human_loop=fake_hl)

        result = gate.request_outflow(self.sample_request)

        self.assertFalse(result["approved"])
        self.assertEqual(result["human_response"], "需要更多信息")

    # ------------------------------------------------------------------
    # 批准时 approved=True 但仍不执行签名（返回指引）
    # ------------------------------------------------------------------
    def test_approved_but_no_signing(self) -> None:
        fake_hl = _FakeHumanLoop(response="批准")
        gate = CryptoOutflowGate(workspace=self.ws, human_loop=fake_hl)

        result = gate.request_outflow(self.sample_request)

        # 用户批准
        self.assertTrue(result["approved"])
        self.assertEqual(result["human_response"], "批准")

        # 关键：返回结构中不含任何签名/广播/tx_hash 字段 - AI 没有执行签名
        self.assertNotIn("tx_hash", result)
        self.assertNotIn("signed", result)
        self.assertNotIn("broadcast", result)

        # 仅返回手动签名指引（不执行签名），指引包含钱包软件步骤
        instructions = gate.get_signature_instructions(self.sample_request)
        self.assertIn("手动签名", instructions)
        self.assertIn("Ethereum", instructions)
        self.assertIn("0xFROMAAA", instructions)
        self.assertIn("0xTOBBBBB", instructions)
        self.assertIn("record-outflow", instructions)

    # ------------------------------------------------------------------
    # log_outflow 写入 crypto-outflows.md
    # ------------------------------------------------------------------
    def test_log_outflow_writes_file(self) -> None:
        gate = CryptoOutflowGate(workspace=self.ws)
        record = {
            "timestamp": "2026-01-01 00:00:00",
            "chain": "Ethereum",
            "from_address": "0xFROMAAA",
            "to_address": "0xTOBBBBB",
            "amount": 0.5,
            "asset": "ETH",
            "reason": "参与流动性挖矿",
            "human_response": "批准",
            "status": "approved",
        }

        log_path = gate.log_outflow(record)

        # 路径正确：company/safety/crypto-outflows.md
        expected_path = self.tmp_root / "safety" / "crypto-outflows.md"
        self.assertEqual(Path(log_path), expected_path.resolve())
        self.assertTrue(expected_path.exists())

        text = expected_path.read_text(encoding="utf-8")
        # 标题
        self.assertIn("加密货币出币请求日志", text)
        # 各字段均写入
        self.assertIn("Ethereum", text)
        self.assertIn("0xFROMAAA", text)
        self.assertIn("0xTOBBBBB", text)
        self.assertIn("0.5", text)
        self.assertIn("ETH", text)
        self.assertIn("参与流动性挖矿", text)
        self.assertIn("批准", text)
        self.assertIn("approved", text)

    # ------------------------------------------------------------------
    # request_outflow 流程中自动留痕（批准与拒绝均留痕）
    # ------------------------------------------------------------------
    def test_request_outflow_logs_regardless_of_decision(self) -> None:
        log_path = self.tmp_root / "safety" / "crypto-outflows.md"

        # 批准
        gate_ok = CryptoOutflowGate(
            workspace=self.ws, human_loop=_FakeHumanLoop(response="批准")
        )
        gate_ok.request_outflow(self.sample_request)
        self.assertTrue(log_path.exists())
        text1 = log_path.read_text(encoding="utf-8")
        self.assertIn("approved", text1)

        # 拒绝（追加写入，不覆盖）
        gate_no = CryptoOutflowGate(
            workspace=self.ws, human_loop=_FakeHumanLoop(response="拒绝")
        )
        gate_no.request_outflow(self.sample_request)
        text2 = log_path.read_text(encoding="utf-8")
        # 两条记录都在
        self.assertIn("approved", text2)
        self.assertIn("rejected", text2)
        # 追加而非覆盖：approved 记录仍在
        self.assertGreater(len(text2), len(text1))

    # ------------------------------------------------------------------
    # _build_decision_context 包含风险提示
    # ------------------------------------------------------------------
    def test_decision_context_contains_risk_warnings(self) -> None:
        gate = CryptoOutflowGate(workspace=self.ws)
        ctx = gate._build_decision_context(self.sample_request)

        # 关键字段
        self.assertIn("Ethereum", ctx)
        self.assertIn("0xFROMAAA", ctx)
        self.assertIn("0xTOBBBBB", ctx)
        self.assertIn("0.5", ctx)
        self.assertIn("ETH", ctx)
        self.assertIn("参与流动性挖矿", ctx)
        # 风险提示
        self.assertIn("风险提示", ctx)
        self.assertIn("请核实收款地址正确", ctx)
        self.assertIn("确认交易费合理", ctx)
        self.assertIn("此操作不可逆", ctx)
        # AI 不持有私钥的声明
        self.assertIn("AI 不持有私钥", ctx)


if __name__ == "__main__":
    unittest.main()
