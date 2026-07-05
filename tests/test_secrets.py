"""SecretsManager 单元测试

使用标准库 unittest，可直接 `python -m unittest tests.test_secrets` 运行。
也兼容 pytest 风格。
"""
import json
import shutil
import tempfile
import unittest
from pathlib import Path

import yaml

from engine.workspace import WorkspaceManager
from engine.secrets import SecretsManager


class TestSecretsManager(unittest.TestCase):
    """SecretsManager 测试套件。"""

    def setUp(self) -> None:
        # 临时项目根：内含 company/ 工作区与 .secrets/ 目录，便于整体清理
        self.tmp_project = Path(tempfile.mkdtemp(prefix="autocorp_secrets_"))
        self.workspace = WorkspaceManager(root_dir=self.tmp_project / "company")
        self.workspace.initialize()
        self.sm = SecretsManager(workspace=self.workspace)

    def tearDown(self) -> None:
        # 清理整个临时项目根（含 .secrets/ 与 company/）
        shutil.rmtree(self.tmp_project, ignore_errors=True)

    # ------------------------------------------------------------------
    # set/get 往返
    # ------------------------------------------------------------------
    def test_set_get_roundtrip(self) -> None:
        """set 后 get 应返回相同明文。"""
        self.sm.set("paypal_client_secret", "super-secret-value-123")
        self.assertEqual(self.sm.get("paypal_client_secret"), "super-secret-value-123")

    def test_get_missing_key_returns_none(self) -> None:
        """不存在的 key 应返回 None。"""
        self.assertIsNone(self.sm.get("does_not_exist"))

    def test_set_overwrites_existing(self) -> None:
        """重复 set 同一 key 应覆盖旧值。"""
        self.sm.set("api_key", "old-value")
        self.sm.set("api_key", "new-value")
        self.assertEqual(self.sm.get("api_key"), "new-value")

    # ------------------------------------------------------------------
    # 存储隔离：明文在 .secrets/secrets.json，引用在 secrets.yaml
    # ------------------------------------------------------------------
    def test_plaintext_stored_in_secrets_json(self) -> None:
        """明文应存于 .secrets/secrets.json。"""
        secret_value = "plaintext-paypal-secret-xyz"
        self.sm.set("paypal_secret", secret_value)

        # .secrets/secrets.json 应位于项目根（company/ 的上一级），且含明文
        secrets_json = self.tmp_project / ".secrets" / "secrets.json"
        self.assertTrue(secrets_json.exists(), "明文应存于 .secrets/secrets.json")
        with secrets_json.open("r", encoding="utf-8") as f:
            data = json.load(f)
        self.assertEqual(data.get("paypal_secret"), secret_value)

    def test_secrets_yaml_stores_only_reference(self) -> None:
        """secrets.yaml 仅存引用，不含明文。"""
        secret_value = "plaintext-paypal-secret-xyz"
        self.sm.set("paypal_secret", secret_value)

        # secrets.yaml 应位于 company/config/
        secrets_yaml = self.tmp_project / "company" / "config" / "secrets.yaml"
        self.assertTrue(secrets_yaml.exists(), "secrets.yaml 应位于 company/config/")
        with secrets_yaml.open("r", encoding="utf-8") as f:
            content = f.read()

        # 应含引用字符串
        self.assertIn("ref://.secrets/secrets.json#paypal_secret", content)
        # 不应含明文
        self.assertNotIn(secret_value, content)

    def test_secrets_dir_is_physical_isolated_from_company(self) -> None:
        """ .secrets/ 目录应在 company/ 之外，物理隔离。"""
        secrets_dir = self.tmp_project / ".secrets"
        company_dir = self.tmp_project / "company"
        self.assertTrue(secrets_dir.exists())
        self.assertTrue(company_dir.exists())
        # .secrets/ 不应是 company/ 的子目录
        self.assertFalse(secrets_dir.is_relative_to(company_dir))

    # ------------------------------------------------------------------
    # get_for_log 脱敏
    # ------------------------------------------------------------------
    def test_get_for_log_returns_redacted_placeholder(self) -> None:
        """get_for_log 应返回 [REDACTED:key] 占位符，永远不暴露明文。"""
        self.sm.set("paypal_secret", "plaintext-paypal-secret-xyz")
        redacted = self.sm.get_for_log("paypal_secret")
        self.assertEqual(redacted, "[REDACTED:paypal_secret]")
        # 不含明文
        self.assertNotIn("plaintext-paypal-secret-xyz", redacted)

    def test_get_for_log_works_for_missing_key(self) -> None:
        """即使 key 不存在，get_for_log 也应返回脱敏占位符。"""
        self.assertEqual(self.sm.get_for_log("nonexistent"), "[REDACTED:nonexistent]")

    # ------------------------------------------------------------------
    # scan_prompt 脱敏扫描
    # ------------------------------------------------------------------
    def test_scan_prompt_detects_openai_key(self) -> None:
        """应检测 sk- 开头的 OpenAI key 并脱敏。"""
        prompt = "请用密钥 sk-abcdefghijklmnopqrstuvwxyz1234567890 调用 API"
        result = SecretsManager.scan_prompt(prompt)
        self.assertNotIn("sk-abcdefghijklmnopqrstuvwxyz1234567890", result)
        self.assertIn("[REDACTED]", result)

    def test_scan_prompt_detects_paypal(self) -> None:
        """应检测 paypal: 标记并脱敏。"""
        prompt = "配置为 paypal:client_secret_here"
        result = SecretsManager.scan_prompt(prompt)
        self.assertNotIn("client_secret_here", result)
        self.assertIn("[REDACTED]", result)

    def test_scan_prompt_detects_private_key(self) -> None:
        """应检测 0x 开头的 64 位十六进制私钥并脱敏。"""
        privkey = "0x" + "a" * 64
        prompt = f"钱包私钥：{privkey}"
        result = SecretsManager.scan_prompt(prompt)
        self.assertNotIn(privkey, result)
        self.assertIn("[REDACTED]", result)

    def test_scan_prompt_detects_mnemonic_12_words(self) -> None:
        """应检测 12 词助记词并脱敏。"""
        mnemonic = " ".join(["apple"] * 12)
        prompt = f"助记词：{mnemonic}"
        result = SecretsManager.scan_prompt(prompt)
        self.assertNotIn(mnemonic, result)
        self.assertIn("[REDACTED]", result)

    def test_scan_prompt_detects_mnemonic_24_words(self) -> None:
        """应检测 24 词助记词并脱敏。"""
        mnemonic = " ".join(["apple"] * 24)
        prompt = f"助记词：{mnemonic}"
        result = SecretsManager.scan_prompt(prompt)
        self.assertNotIn(mnemonic, result)
        self.assertIn("[REDACTED]", result)

    def test_scan_prompt_returns_original_when_clean(self) -> None:
        """无敏感模式时应返回原文。"""
        prompt = "今天天气不错，我们去公园散步吧。"
        self.assertEqual(SecretsManager.scan_prompt(prompt), prompt)

    def test_scan_prompt_handles_empty_string(self) -> None:
        """空字符串应原样返回。"""
        self.assertEqual(SecretsManager.scan_prompt(""), "")

    # ------------------------------------------------------------------
    # delete
    # ------------------------------------------------------------------
    def test_delete_removes_key(self) -> None:
        """delete 后 get 应返回 None。"""
        self.sm.set("to_delete", "some-value")
        self.assertEqual(self.sm.get("to_delete"), "some-value")

        deleted = self.sm.delete("to_delete")
        self.assertTrue(deleted)
        self.assertIsNone(self.sm.get("to_delete"))

    def test_delete_missing_key_returns_false(self) -> None:
        """删除不存在的 key 应返回 False。"""
        self.assertFalse(self.sm.delete("never_existed"))

    def test_delete_removes_reference_from_yaml(self) -> None:
        """delete 后 secrets.yaml 中的引用也应删除。"""
        self.sm.set("temp_key", "temp-value")
        secrets_yaml = self.tmp_project / "company" / "config" / "secrets.yaml"
        with secrets_yaml.open("r", encoding="utf-8") as f:
            self.assertIn("temp_key", yaml.safe_load(f))

        self.sm.delete("temp_key")

        with secrets_yaml.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f) or {}
        self.assertNotIn("temp_key", data)

    # ------------------------------------------------------------------
    # list 只返回 key 名，不含值
    # ------------------------------------------------------------------
    def test_list_returns_only_key_names(self) -> None:
        """list 应返回所有 key 名，不含值。"""
        self.sm.set("key_a", "value_a")
        self.sm.set("key_b", "value_b")

        keys = self.sm.list()
        self.assertIn("key_a", keys)
        self.assertIn("key_b", keys)
        # 不应包含任何值
        self.assertNotIn("value_a", keys)
        self.assertNotIn("value_b", keys)

    def test_list_empty_when_no_secrets(self) -> None:
        """无密钥时 list 应返回空列表。"""
        self.assertEqual(self.sm.list(), [])

    # ------------------------------------------------------------------
    # exists
    # ------------------------------------------------------------------
    def test_exists(self) -> None:
        """exists 应正确反映密钥是否存在。"""
        self.assertFalse(self.sm.exists("api_key"))
        self.sm.set("api_key", "val")
        self.assertTrue(self.sm.exists("api_key"))
        self.sm.delete("api_key")
        self.assertFalse(self.sm.exists("api_key"))

    # ------------------------------------------------------------------
    # 持久化：跨实例
    # ------------------------------------------------------------------
    def test_persistence_across_instances(self) -> None:
        """新实例应读取到已持久化的密钥。"""
        self.sm.set("persistent_key", "persistent-value")

        # 用同一 workspace 重新实例化
        new_sm = SecretsManager(workspace=self.workspace)
        self.assertEqual(new_sm.get("persistent_key"), "persistent-value")
        self.assertIn("persistent_key", new_sm.list())


if __name__ == "__main__":
    unittest.main()
