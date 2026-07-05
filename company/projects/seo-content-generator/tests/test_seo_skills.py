"""claude-seo Skill 套件接入单元测试（SubTask 1.6）

覆盖：
- load_seo_skills() 返回结构正确的 dict
- ProductManager.generate_content_brief 基于 content-brief-generator 产出 brief
- SEOScorer.audit_with_skill 对低质文章阻断发布（block_publish=True）
- ContentWriter.generate_schema_markup 输出合法 JSON-LD

说明：
- 不依赖外部 LLM API：PM 用 MagicMock 替换 LLMClient，SEOScorer / ContentWriter
  的被测方法均基于规则 / 确定性构造。
- 顶部 sys.path 注入确保 engine 与 seo_generator 两个包均可导入（无 conftest 时自包含）。
"""
from __future__ import annotations

import json
import os
import sys
import tempfile
import unittest
from unittest.mock import MagicMock

# ---------------------------------------------------------------------------
# sys.path 自包含注入：确保 engine（项目根）与 seo_generator（seo-content-generator）
# 两个包均可导入，无论测试从哪个 cwd 启动。
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_SEO_GEN_ROOT = os.path.dirname(_HERE)  # seo-content-generator/
_PROJECT_ROOT = os.path.dirname(os.path.dirname(os.path.dirname(_SEO_GEN_ROOT)))  # autoCompany/
for _p in (_PROJECT_ROOT, _SEO_GEN_ROOT):
    if _p not in sys.path:
        sys.path.insert(0, _p)

from engine.llm_client import load_seo_skills  # noqa: E402
from engine.workspace import WorkspaceManager  # noqa: E402
from engine.agents.product_manager import ProductManager  # noqa: E402
from seo_generator.content_writer import ContentWriter  # noqa: E402
from seo_generator.seo_scorer import SEOScorer  # noqa: E402


class TestLoadSeoSkills(unittest.TestCase):
    """load_seo_skills 加载与解析测试。"""

    def test_load_seo_skills_returns_dict(self):
        """加载 claude-seo 套件，返回 dict 且包含 4 个核心 skill。"""
        skills = load_seo_skills()
        self.assertIsInstance(skills, dict)

        expected = {
            "content-brief-generator",
            "technical-seo-auditor",
            "schema-markup-generator",
            "backlink-prospector",
        }
        self.assertTrue(
            expected.issubset(skills.keys()),
            f"缺少 skill：{expected - set(skills.keys())}",
        )

        # 每个 skill 含 description / prompt / path 三个字段
        for name, info in skills.items():
            self.assertIn("description", info, f"{name} 缺少 description")
            self.assertIn("prompt", info, f"{name} 缺少 prompt")
            self.assertIn("path", info, f"{name} 缺少 path")
            self.assertIsInstance(info["prompt"], str)
            self.assertTrue(info["prompt"], f"{name} 的 prompt 为空")
            self.assertTrue(
                os.path.isfile(info["path"]),
                f"{name} 的 path 指向不存在的文件：{info['path']}",
            )

    def test_load_seo_skills_raises_when_dir_missing(self):
        """目录不存在时抛 FileNotFoundError。"""
        with self.assertRaises(FileNotFoundError):
            load_seo_skills(skills_dir="/nonexistent/path/claude-seo")

    def test_skill_prompts_are_format_safe(self):
        """各 skill 的 prompt 模板可被 .format() 安全渲染（占位符替换不报错）。"""
        skills = load_seo_skills()
        # content-brief-generator: {keyword} {audience}
        brief_prompt = skills["content-brief-generator"]["prompt"]
        rendered = brief_prompt.format(keyword="ethereum wallet", audience="crypto")
        self.assertIn("ethereum wallet", rendered)
        self.assertIn("crypto", rendered)

        # technical-seo-auditor: {article_path}
        audit_prompt = skills["technical-seo-auditor"]["prompt"]
        rendered = audit_prompt.format(article_path="/tmp/article.md")
        self.assertIn("/tmp/article.md", rendered)

        # schema-markup-generator: 5 个占位符
        schema_prompt = skills["schema-markup-generator"]["prompt"]
        rendered = schema_prompt.format(
            title="T", description="D", author="A",
            date_published="2026-06-28", url="https://example.com/x",
        )
        self.assertIn("2026-06-28", rendered)

        # backlink-prospector: {keyword} {topic}
        backlink_prompt = skills["backlink-prospector"]["prompt"]
        rendered = backlink_prompt.format(keyword="ethereum wallet", topic="crypto")
        self.assertIn("ethereum wallet", rendered)


class TestContentBriefGenerator(unittest.TestCase):
    """ProductManager.generate_content_brief 测试。"""

    def setUp(self):
        """用 MagicMock 替换 LLMClient，避免依赖外部 API。"""
        self.workspace = WorkspaceManager()
        self.mock_llm = MagicMock()
        self.pm = ProductManager(self.workspace, llm_client=self.mock_llm)

    def test_content_brief_generator_produces_valid_brief(self):
        """content-brief-generator 经 LLM 产出结构化 brief。"""
        canned_brief = (
            "# 内容 Brief: ethereum wallet\n\n"
            "## 目标关键词\n- 主关键词：ethereum wallet\n"
            "## 受众画像\n- 受众：crypto\n"
            "## 大纲建议\n- H1: Ethereum Wallet Guide\n"
        )
        self.mock_llm.chat.return_value = canned_brief

        result = self.pm.generate_content_brief("ethereum wallet", "crypto")

        self.assertIsInstance(result, dict)
        self.assertEqual(result["keyword"], "ethereum wallet")
        self.assertEqual(result["audience"], "crypto")
        self.assertEqual(result["source"], "content-brief-generator")
        self.assertIn("ethereum wallet", result["brief_md"])
        # LLM 被调用过
        self.mock_llm.chat.assert_called_once()

    def test_content_brief_falls_back_on_llm_failure(self):
        """LLM 调用失败时降级到模板 brief，source 标记为 template-fallback。"""
        self.mock_llm.chat.side_effect = RuntimeError("LLM 不可用")

        result = self.pm.generate_content_brief("ethereum wallet", "crypto")

        self.assertEqual(result["source"], "template-fallback")
        self.assertIn("ethereum wallet", result["brief_md"])
        self.assertIn("内容 Brief", result["brief_md"])


class TestTechnicalSeoAuditor(unittest.TestCase):
    """SEOScorer.audit_with_skill 测试。"""

    def setUp(self):
        self.scorer = SEOScorer()

    def _write_temp_article(self, content: str) -> str:
        """将文章内容写入临时文件并返回路径。"""
        fd, path = tempfile.mkstemp(suffix=".md", prefix="audit_test_")
        os.close(fd)
        with open(path, "w", encoding="utf-8") as f:
            f.write(content)
        return path

    def test_technical_seo_auditor_blocks_low_score(self):
        """低质文章（无 H1/无 meta/无 H2/无内链）应被阻断发布。"""
        poor_article = (
            "This is a short article with no SEO structure at all.\n\n"
            "Just plain text without any headings or links.\n"
        )
        path = self._write_temp_article(poor_article)

        try:
            result = self.scorer.audit_with_skill(path)
        finally:
            os.unlink(path)

        self.assertIn("score", result)
        self.assertIn("suggestions", result)
        self.assertIn("block_publish", result)
        self.assertIsInstance(result["score"], int)
        self.assertLess(result["score"], 70,
                        f"低质文章评分 {result['score']} 应 < 70")
        self.assertTrue(result["block_publish"],
                        "低质文章应阻断发布")
        self.assertTrue(result["suggestions"], "应给出优化建议")

    def test_technical_seo_auditor_passes_high_quality(self):
        """高质量文章不应阻断发布。"""
        meta_desc = (
            "The complete ethereum wallet guide for 2026 with tips, best "
            "practices and step-by-step tactics to secure your assets. "
            "Learn how to choose and use ethereum wallets safely today."
        )
        good_article = (
            "---\n"
            f"description: {meta_desc}\n"
            "---\n\n"
            "# The Ultimate Guide to Ethereum Wallet in 2026\n\n"
            "## What is an Ethereum Wallet\n\n### Overview\n\n"
            "An ethereum wallet lets you securely manage your assets.\n\n"
            "## Why Ethereum Wallet Matters\n\n### Security\n\n"
            "Security is critical for any ethereum wallet user.\n\n"
            "## Best Practices for Ethereum Wallet\n\n### Tips\n\n"
            "Always back up your ethereum wallet seed phrase.\n\n"
            "## Related Resources\n\n### More\n\n"
            "- [guide](/ethereum-wallet-guide)\n"
            "- [tips](/ethereum-wallet-tips)\n"
            "- [security](/ethereum-wallet-security)\n"
        )
        path = self._write_temp_article(good_article)

        try:
            result = self.scorer.audit_with_skill(path)
        finally:
            os.unlink(path)

        self.assertGreaterEqual(result["score"], 70,
                                f"高质量文章评分 {result['score']} 应 ≥ 70")
        self.assertFalse(result["block_publish"],
                         "高质量文章不应阻断发布")

    def test_technical_seo_auditor_missing_file(self):
        """文件不存在时返回 0 分并阻断发布。"""
        result = self.scorer.audit_with_skill("/nonexistent/article.md")
        self.assertEqual(result["score"], 0)
        self.assertTrue(result["block_publish"])


class TestSchemaMarkupGenerator(unittest.TestCase):
    """ContentWriter.generate_schema_markup 测试。"""

    def setUp(self):
        self.writer = ContentWriter()

    def test_schema_markup_generator_outputs_valid_jsonld(self):
        """generate_schema_markup 输出合法 JSON-LD（Article 类型）。"""
        article = {
            "title": "Ethereum Wallet Guide 2026",
            "description": "A complete guide to Ethereum wallets in 2026.",
            "author": "AutoCorp",
            "date_published": "2026-06-28",
            "url": "https://example.com/ethereum-wallet-guide",
            "article_body": "Ethereum wallets let you manage your assets securely.",
        }

        output = self.writer.generate_schema_markup(article)

        self.assertIsInstance(output, str)
        # 输出为合法 JSON
        schema = json.loads(output)
        self.assertIsInstance(schema, dict)

        # 核心字段
        self.assertEqual(schema["@context"], "https://schema.org")
        self.assertEqual(schema["@type"], "Article")
        self.assertEqual(schema["headline"], "Ethereum Wallet Guide 2026")
        self.assertEqual(schema["description"],
                         "A complete guide to Ethereum wallets in 2026.")
        self.assertEqual(schema["author"]["@type"], "Person")
        self.assertEqual(schema["author"]["name"], "AutoCorp")
        self.assertEqual(schema["datePublished"], "2026-06-28")
        self.assertEqual(schema["mainEntityOfPage"]["@id"],
                         "https://example.com/ethereum-wallet-guide")
        self.assertEqual(schema["articleBody"],
                         "Ethereum wallets let you manage your assets securely.")

    def test_schema_markup_uses_safe_defaults(self):
        """缺失字段时使用安全默认值，仍输出合法 JSON-LD。"""
        output = self.writer.generate_schema_markup({})
        schema = json.loads(output)
        self.assertEqual(schema["@type"], "Article")
        self.assertEqual(schema["headline"], "Untitled Article")
        self.assertEqual(schema["author"]["name"], "AutoCorp")
        # 无 date_published 时不应出现 datePublished 字段
        self.assertNotIn("datePublished", schema)


if __name__ == "__main__":
    unittest.main()
