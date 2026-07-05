"""单元测试：ContentWriter 的 seo-blog-writer Skill 集成

覆盖 spec integrate-p0-github-tools Task 2 要求的用例：
    - test_write_with_skill_returns_markdown：write_with_skill 返回 Markdown
    - test_generate_use_skill_false_uses_template：use_skill=False 向后兼容（走模板流程）
    - test_generate_use_skill_true_without_source_raises：缺 source/keyword 抛 ValueError
    - test_skill_prompt_avoids_ai_phrases：输出避免 AI 套话
"""
from __future__ import annotations

import re
import unittest
from pathlib import Path

from seo_generator.content_writer import ContentWriter
from seo_generator.llm_provider import TemplateProvider, get_provider


SKILL_PATH = (Path(__file__).resolve().parent.parent
              / ".claude" / "skills" / "seo-blog-writer" / "SKILL.md")


class TestContentWriterSkill(unittest.TestCase):
    """ContentWriter Skill 集成测试。"""

    def setUp(self):
        """使用 TemplateProvider（无外部 API 依赖）。"""
        self.provider = get_provider("template")
        self.assertIsInstance(self.provider, TemplateProvider)
        self.writer = ContentWriter(provider=self.provider)

    # ------------------------------------------------------------------
    # SKILL.md 存在性与结构
    # ------------------------------------------------------------------

    def test_skill_md_exists_and_has_prompt_template(self):
        """SKILL.md 应存在且含提示词模板与禁用句式清单。"""
        self.assertTrue(SKILL_PATH.exists(), f"SKILL.md 不存在：{SKILL_PATH}")
        text = SKILL_PATH.read_text(encoding="utf-8")
        self.assertIn("seo-blog-writer", text)
        self.assertIn("提示词模板", text)
        self.assertIn("反 AI 味清单", text)
        # frontmatter name 字段
        self.assertRegex(text, r"^---\s*\nname:\s*seo-blog-writer")

    # ------------------------------------------------------------------
    # write_with_skill
    # ------------------------------------------------------------------

    def test_write_with_skill_returns_markdown(self):
        """write_with_skill 应返回非空 Markdown，含 H1/H2 结构。"""
        article = self.writer.write_with_skill(
            source="Aave 借贷协议入门笔记",
            keyword="aave guide",
            tone="professional",
            length=1500,
        )
        self.assertIsInstance(article, str)
        self.assertGreater(len(article.strip()), 200)
        # 含 H1
        self.assertTrue(re.search(r"^#\s+.+", article, re.MULTILINE))
        # 含至少一个 H2
        self.assertTrue(re.search(r"^##\s+.+", article, re.MULTILINE))

    # ------------------------------------------------------------------
    # generate 向后兼容
    # ------------------------------------------------------------------

    def test_generate_use_skill_false_uses_template(self):
        """use_skill=False 走原有模板流程，返回 body_markdown 字符串。"""
        from seo_generator.keyword_analyzer import KeywordAnalyzer
        from seo_generator.outline_generator import OutlineGenerator

        analyzer = KeywordAnalyzer(provider=self.provider)
        analysis = analyzer.analyze("email marketing", language="en")
        outliner = OutlineGenerator(provider=self.provider)
        outline = outliner.generate(analysis, language="en")

        article = self.writer.generate(
            outline=outline, keyword_analysis=analysis,
            language="en", use_skill=False,
        )
        self.assertIsInstance(article, str)
        self.assertGreater(len(article.strip()), 200)
        # 模板流程产物应含 H1
        self.assertTrue(re.search(r"^#\s+.+", article, re.MULTILINE))

    # ------------------------------------------------------------------
    # generate use_skill=True 校验
    # ------------------------------------------------------------------

    def test_generate_use_skill_true_without_source_raises(self):
        """use_skill=True 但缺 source/keyword 应抛 ValueError。"""
        with self.assertRaises(ValueError):
            self.writer.generate(use_skill=True, source=None, keyword="aave guide")
        with self.assertRaises(ValueError):
            self.writer.generate(use_skill=True, source="some notes", keyword=None)
        with self.assertRaises(ValueError):
            self.writer.generate(use_skill=True, source="", keyword="")

    def test_generate_use_skill_true_routes_to_skill(self):
        """use_skill=True 且参数齐全应走 skill 流程并返回 Markdown。"""
        article = self.writer.generate(
            use_skill=True,
            source="Solana 生态速览笔记",
            keyword="solana ecosystem",
        )
        self.assertIsInstance(article, str)
        self.assertGreater(len(article.strip()), 200)
        self.assertTrue(re.search(r"^#\s+.+", article, re.MULTILINE))

    # ------------------------------------------------------------------
    # 反 AI 味
    # ------------------------------------------------------------------

    def test_skill_prompt_avoids_ai_phrases(self):
        """输出应避免 AI 套话（在当今/综上所述/值得注意的是 等）。"""
        article = self.writer.write_with_skill(
            source="以太坊钱包安全实践笔记",
            keyword="ethereum wallet",
            tone="expert",
            length=1500,
        )
        banned = [
            "在当今",
            "的背景下",
            "综上所述",
            "总而言之",
            "值得注意的是",
            "需要指出的是",
            "让我们一探究竟",
            "让我们深入了解",
            "本文将介绍",
            "In today's world",
            "It's important to note",
            "In conclusion",
            "Let's dive into",
            "delve into",
        ]
        for phrase in banned:
            self.assertNotIn(
                phrase, article,
                msg=f"输出中检测到 AI 套话：{phrase}",
            )


if __name__ == "__main__":
    unittest.main()
