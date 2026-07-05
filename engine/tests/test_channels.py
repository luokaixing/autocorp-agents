"""COO 渠道选择与 channels.yaml 数据文件单元测试。

使用标准库 unittest，可直接 `python -m unittest engine.tests.test_channels` 运行，
也兼容 pytest 风格。

覆盖（SubTask 3.5）：
- test_channels_yaml_has_300_plus_entries：真实 channels.yaml 渠道数 ≥ 300 且字段完整
- test_select_channels_filters_by_category：按 category 过滤
- test_select_channels_filters_by_audience：按 audience 过滤
- test_select_channels_sorts_by_priority：按 priority 升序排序
- test_select_channels_returns_default_on_missing_file：文件缺失时返回默认渠道
- test_select_channels_combined_filter：组合过滤（SubTask 3.4 验证）
"""
import shutil
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import MagicMock

# 让 tests 包可导入 engine 包（上级目录）
sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

import yaml  # noqa: E402

from engine.workspace import WorkspaceManager  # noqa: E402
from engine.agents.coo import COO  # noqa: E402

# 真实 channels.yaml 路径：d:\autoCompany\company\knowledge\marketing\channels.yaml
PROJECT_ROOT = Path(__file__).resolve().parents[2]
REAL_CHANNELS_YAML = PROJECT_ROOT / "company" / "knowledge" / "marketing" / "channels.yaml"


class TestChannelsYamlData(unittest.TestCase):
    """channels.yaml 数据文件测试。"""

    def test_channels_yaml_has_300_plus_entries(self) -> None:
        """真实 channels.yaml 应包含 ≥ 300 条渠道，且每条字段完整。"""
        self.assertTrue(REAL_CHANNELS_YAML.exists(), f"channels.yaml 不存在：{REAL_CHANNELS_YAML}")
        with REAL_CHANNELS_YAML.open("r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        channels = data.get("channels", [])
        self.assertGreaterEqual(
            len(channels), 300,
            f"渠道数 {len(channels)} 不足 300",
        )
        # 抽样校验字段完整性（首/中/尾各一条）
        for idx in (0, len(channels) // 2, len(channels) - 1):
            c = channels[idx]
            for field in ("name", "url", "category", "audience", "cost", "priority"):
                self.assertIn(field, c, f"第 {idx} 条渠道缺少字段 {field}")
            self.assertIsInstance(c["category"], list, "category 应为列表")
            self.assertIsInstance(c["audience"], list, "audience 应为列表")
            self.assertIsInstance(c["priority"], int, "priority 应为整数")
            self.assertTrue(1 <= c["priority"] <= 5, "priority 应在 1-5 范围")


class TestSelectChannels(unittest.TestCase):
    """COO.select_channels 方法测试（使用临时工作区 + 已知小数据集）。"""

    def setUp(self) -> None:
        # 每个用例独立临时工作区
        self.tmp_root = Path(tempfile.mkdtemp(prefix="autocorp_channels_"))
        self.ws = WorkspaceManager(root_dir=self.tmp_root)
        self.ws.initialize()

        # 写入已知 channels.yaml（含不同 category/audience/cost/priority 便于断言）
        marketing_dir = self.ws.knowledge_dir / "marketing"
        marketing_dir.mkdir(parents=True, exist_ok=True)
        sample = {
            "channels": [
                {
                    "name": "Forum A",
                    "url": "https://a.example.com",
                    "category": ["free", "foreign", "forum"],
                    "audience": ["developer"],
                    "cost": "free",
                    "priority": 2,
                    "description": "开发者论坛 A",
                },
                {
                    "name": "Crypto B",
                    "url": "https://b.example.com",
                    "category": ["free", "foreign", "social"],
                    "audience": ["crypto"],
                    "cost": "free",
                    "priority": 1,
                    "description": "加密社交 B",
                },
                {
                    "name": "Paid C",
                    "url": "https://c.example.com",
                    "category": ["paid", "foreign", "directory"],
                    "audience": ["tech", "crypto"],
                    "cost": "paid",
                    "priority": 3,
                    "description": "付费目录 C",
                },
                {
                    "name": "Forum D Crypto",
                    "url": "https://d.example.com",
                    "category": ["free", "foreign", "forum"],
                    "audience": ["crypto", "developer"],
                    "cost": "free",
                    "priority": 1,
                    "description": "加密开发者论坛 D",
                },
            ]
        }
        self.ws.write_yaml(marketing_dir / "channels.yaml", sample)

        # Mock LLM，避免真实网络调用
        self.mock_llm = MagicMock()
        self.coo = COO(workspace=self.ws, llm_client=self.mock_llm)

    def tearDown(self) -> None:
        shutil.rmtree(self.tmp_root, ignore_errors=True)

    def test_select_channels_filters_by_category(self) -> None:
        """按 category='forum' 过滤，结果应全部含 forum 且仅含 forum 类渠道。"""
        result = self.coo.select_channels(category="forum", limit=10)
        self.assertEqual(len(result), 2, "应有 2 条 forum 渠道")
        for c in result:
            self.assertIn("forum", c["category"])
        names = {c["name"] for c in result}
        self.assertEqual(names, {"Forum A", "Forum D Crypto"})

    def test_select_channels_filters_by_audience(self) -> None:
        """按 audience='crypto' 过滤，结果应全部含 crypto 受众。"""
        result = self.coo.select_channels(audience="crypto", limit=10)
        # Crypto B / Paid C / Forum D Crypto 三条含 crypto
        self.assertEqual(len(result), 3)
        for c in result:
            self.assertIn("crypto", c["audience"])

    def test_select_channels_sorts_by_priority(self) -> None:
        """返回结果应按 priority 升序排列（1 最高优先在前）。"""
        result = self.coo.select_channels(limit=10)
        priorities = [c["priority"] for c in result]
        self.assertEqual(priorities, sorted(priorities), f"未按升序排序：{priorities}")
        # 验证 priority=1 的渠道排在最前
        self.assertEqual(priorities[0], 1)

    def test_select_channels_returns_default_on_missing_file(self) -> None:
        """channels.yaml 不存在时应返回默认渠道（Twitter/Reddit/Paragraph）。"""
        # 使用一个新的临时工作区，不写入 channels.yaml
        empty_root = Path(tempfile.mkdtemp(prefix="autocorp_empty_"))
        try:
            empty_ws = WorkspaceManager(root_dir=empty_root)
            empty_ws.initialize()
            coo = COO(workspace=empty_ws, llm_client=MagicMock())
            result = coo.select_channels(limit=10)
            # 默认渠道为 3 条
            self.assertEqual(len(result), 3)
            names = {c["name"] for c in result}
            self.assertIn("Twitter / X", names)
            self.assertIn("Reddit", names)
            self.assertIn("Paragraph", names)
        finally:
            shutil.rmtree(empty_root, ignore_errors=True)

    def test_select_channels_combined_filter(self) -> None:
        """组合过滤：category='forum' AND audience='crypto' 应只返回同时满足的渠道。"""
        result = self.coo.select_channels(category="forum", audience="crypto", limit=10)
        # 仅 Forum D Crypto 同时含 forum 分类与 crypto 受众
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0]["name"], "Forum D Crypto")
        self.assertIn("forum", result[0]["category"])
        self.assertIn("crypto", result[0]["audience"])


if __name__ == "__main__":
    unittest.main()
