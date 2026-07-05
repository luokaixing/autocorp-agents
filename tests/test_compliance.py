"""ComplianceChecker 单元测试

使用标准库 unittest，可直接 `python -m unittest tests.test_compliance` 运行。
也兼容 pytest 风格。
"""
import shutil
import tempfile
import unittest
from pathlib import Path

from engine.safety.compliance import ComplianceChecker
from engine.workspace import WorkspaceManager


class TestComplianceChecker(unittest.TestCase):
    """ComplianceChecker 测试套件。"""

    def setUp(self) -> None:
        # 每个测试用例使用独立的临时目录作为工作区根目录，避免污染真实 company/
        self.tmp_root = Path(tempfile.mkdtemp(prefix="autocorp_compliance_"))
        self.ws = WorkspaceManager(root_dir=self.tmp_root)
        self.checker = ComplianceChecker(workspace=self.ws)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    # ------------------------------------------------------------------
    # 欺诈内容被拦截
    # ------------------------------------------------------------------
    def test_fraud_blocked(self) -> None:
        result = self.checker.check_compliance({
            "type": "content",
            "content": "我们来做刷单活动，好评返现提升排名",
        })
        self.assertFalse(result["passed"])
        self.assertIn("fraud", result["violations"])

    # ------------------------------------------------------------------
    # 市场操纵被拦截
    # ------------------------------------------------------------------
    def test_manipulation_blocked(self) -> None:
        result = self.checker.check_compliance({
            "type": "decision",
            "content": "通过拉盘砸盘操控币价，做一波 pump dump",
        })
        self.assertFalse(result["passed"])
        self.assertIn("manipulation", result["violations"])

    # ------------------------------------------------------------------
    # 洗钱被拦截
    # ------------------------------------------------------------------
    def test_laundering_blocked(self) -> None:
        result = self.checker.check_compliance({
            "type": "payment",
            "content": "将这笔来路不明的资金通过混币匿名转移",
        })
        self.assertFalse(result["passed"])
        self.assertIn("laundering", result["violations"])

    # ------------------------------------------------------------------
    # 单笔 $150 出款触发 large_outflow
    # ------------------------------------------------------------------
    def test_large_outflow_triggered(self) -> None:
        result = self.checker.check_compliance({
            "type": "outflow",
            "content": "支付供应商货款",
            "amount": 150,
        })
        self.assertIn("large_outflow", result["violations"])
        self.assertFalse(result["passed"])

    # ------------------------------------------------------------------
    # 单笔 $50 出款通过
    # ------------------------------------------------------------------
    def test_small_outflow_passes(self) -> None:
        result = self.checker.check_compliance({
            "type": "outflow",
            "content": "支付小额服务费",
            "amount": 50,
        })
        self.assertTrue(result["passed"])
        self.assertNotIn("large_outflow", result["violations"])

    # ------------------------------------------------------------------
    # Prompt 含 sk-xxx 被拦截
    # ------------------------------------------------------------------
    def test_privacy_leak_blocked(self) -> None:
        result = self.checker.check_compliance({
            "type": "decision",
            "content": "调用模型生成文案",
            # sk- 后需 20+ 位字母数字才会被 SecretsManager 判为 OpenAI key
            "prompt": "请用以下 key 调用 API: sk-abc123def456ghi789jkl012mno345",
        })
        self.assertFalse(result["passed"])
        self.assertIn("privacy_leak", result["violations"])

    # ------------------------------------------------------------------
    # 正常内容通过
    # ------------------------------------------------------------------
    def test_normal_content_passes(self) -> None:
        result = self.checker.check_compliance({
            "type": "content",
            "content": "发布产品更新公告，介绍新功能与定价方案",
        })
        self.assertTrue(result["passed"])
        self.assertEqual(result["violations"], [])

    # ------------------------------------------------------------------
    # 告警写入 incidents.md
    # ------------------------------------------------------------------
    def test_incident_logged(self) -> None:
        result = self.checker.check_compliance({
            "type": "content",
            "content": "组织刷单提升销量",
        })
        self.assertIn("fraud", result["violations"])

        incidents_path = self.tmp_root / "safety" / "incidents.md"
        self.assertTrue(incidents_path.exists())
        text = incidents_path.read_text(encoding="utf-8")
        self.assertIn("fraud", text)

    # ------------------------------------------------------------------
    # 金融欺诈关键词被拦截（保本保息/高收益/100%保本等）
    # ------------------------------------------------------------------
    def test_financial_fraud_detected(self) -> None:
        result = self.checker.check_compliance({
            "type": "content",
            "description": "向用户承诺100%保本保息高收益投资回报",
        })
        self.assertFalse(result["passed"])
        self.assertIn("fraud", result["violations"])

    # ------------------------------------------------------------------
    # description 字段兼容：仅提供 description 也能触发 fraud
    # ------------------------------------------------------------------
    def test_description_field_compatible(self) -> None:
        result = self.checker.check_compliance({
            "type": "content",
            "description": "刷单",
        })
        self.assertFalse(result["passed"])
        self.assertIn("fraud", result["violations"])

    # ------------------------------------------------------------------
    # description 中含敏感模式（sk-）触发 privacy_leak
    # ------------------------------------------------------------------
    def test_privacy_leak_in_description(self) -> None:
        result = self.checker.check_compliance({
            "type": "content",
            "description": "导出 PayPal client_secret: sk-abc123def456ghi789jkl012mno345",
        })
        self.assertFalse(result["passed"])
        self.assertIn("privacy_leak", result["violations"])


if __name__ == "__main__":
    unittest.main()
