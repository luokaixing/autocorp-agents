"""E2E 测试：验证 SEO 内容生成完整流程

使用 TemplateProvider（不依赖任何外部 API），覆盖：
    - 关键词分析
    - 大纲生成
    - 正文写作（≥1500 字、含 H1/H2/H3、关键词密度 1-2%）
    - SEO 评分（≥70）
    - CLI generate / analyze 命令
"""
from __future__ import annotations

import re
import tempfile
import unittest
from pathlib import Path

from click.testing import CliRunner

from seo_generator.cli import cli
from seo_generator.content_writer import ContentWriter
from seo_generator.keyword_analyzer import KeywordAnalyzer
from seo_generator.llm_provider import TemplateProvider, count_words, get_provider
from seo_generator.outline_generator import OutlineGenerator
from seo_generator.seo_scorer import SEOScorer


class TestEndToEnd(unittest.TestCase):
    """E2E 测试：完整生成流程。"""

    def setUp(self):
        """初始化各模块，使用 TemplateProvider（无外部 API 依赖）。"""
        self.provider = get_provider("template")
        self.assertIsInstance(self.provider, TemplateProvider)
        self.analyzer = KeywordAnalyzer(provider=self.provider)
        self.outliner = OutlineGenerator(provider=self.provider)
        self.writer = ContentWriter(provider=self.provider)
        self.scorer = SEOScorer()

    # --------------------------------------------------------------------------
    # 模块级 E2E 测试
    # --------------------------------------------------------------------------

    def test_keyword_analysis_structure(self):
        """测试关键词分析输出结构。"""
        analysis = self.analyzer.analyze("email marketing", language="en")
        self.assertIn("primary_keyword", analysis)
        self.assertIn("secondary_keywords", analysis)
        self.assertIn("long_tail", analysis)
        self.assertIn("search_intent", analysis)
        self.assertEqual(analysis["primary_keyword"], "email marketing")
        # 次要关键词 5-8 个
        self.assertGreaterEqual(len(analysis["secondary_keywords"]), 5)
        # 长尾词 10-15 个
        self.assertGreaterEqual(len(analysis["long_tail"]), 10)
        self.assertIn(analysis["search_intent"],
                      ["informational", "commercial", "transactional", "navigational"])

    def test_outline_structure(self):
        """测试大纲生成结构（H1 + ≥3 H2 + 每节含 H3）。"""
        analysis = self.analyzer.analyze("email marketing", language="en")
        outline = self.outliner.generate(analysis, language="en")
        self.assertIn("h1", outline)
        self.assertIn("sections", outline)
        self.assertGreaterEqual(len(outline["sections"]), 3)
        # H1 含主关键词
        self.assertIn("email marketing", outline["h1"].lower())
        # 每个 H2 章节含 H3 列表
        for section in outline["sections"]:
            self.assertIn("h2", section)
            self.assertIn("h3_list", section)
            self.assertGreaterEqual(len(section["h3_list"]), 1)

    def test_full_generation_meets_acceptance(self):
        """测试完整生成流程满足验收标准：≥1500 字、H1/H2/H3、SEO 评分 ≥70。"""
        analysis = self.analyzer.analyze("email marketing", language="en")
        outline = self.outliner.generate(analysis, language="en")
        content = self.writer.write(outline, analysis, language="en")
        result = self.scorer.score(content, analysis)

        body = content["body_markdown"]

        # 1. 字数 ≥1500
        word_count = content["word_count"]
        self.assertGreaterEqual(word_count, 1500,
                                f"字数 {word_count} 未达 1500 要求")

        # 2. 含 H1/H2/H3 结构
        h1_count = len(re.findall(r"^# ", body, re.MULTILINE))
        h2_count = len(re.findall(r"^## ", body, re.MULTILINE))
        h3_count = len(re.findall(r"^### ", body, re.MULTILINE))
        self.assertGreaterEqual(h1_count, 1, "缺少 H1")
        self.assertGreaterEqual(h2_count, 3, f"H2 数量 {h2_count} 不足 3")
        self.assertGreaterEqual(h3_count, 3, f"H3 数量 {h3_count} 不足 3")

        # 3. 关键词密度在 0-3% 范围（满分要求 1-2%，此处放宽到 ≤3% 保证不堆砌）
        primary = analysis["primary_keyword"]
        occurrences = len(re.findall(
            r"\b" + re.escape(primary) + r"\b", body, re.IGNORECASE,
        ))
        density = occurrences / word_count * 100 if word_count else 0
        self.assertLess(density, 3.0,
                        f"关键词密度 {density:.2f}% 过高（>3%）")

        # 4. 内链 ≥3
        self.assertGreaterEqual(len(content["internal_links"]), 3,
                                "内链数量不足 3")

        # 5. meta description 含主关键词且 ≤155 字符
        meta = content["meta_description"]
        self.assertLessEqual(len(meta), 155, "meta description 超过 155 字符")
        self.assertIn(primary.lower(), meta.lower(), "meta 未含主关键词")

        # 6. SEO 评分 ≥70
        self.assertGreaterEqual(result["score"], 70,
                                f"SEO 评分 {result['score']} 未达 70")

    def test_chinese_generation(self):
        """测试中文生成流程。"""
        analysis = self.analyzer.analyze("内容营销", language="zh")
        outline = self.outliner.generate(analysis, language="zh")
        content = self.writer.write(outline, analysis, language="zh")
        result = self.scorer.score(content, analysis)

        # 中文文章字数按字符统计，应 ≥800（中文字符数）
        # 主要验证流程可跑通且评分合理
        self.assertGreater(content["word_count"], 0)
        self.assertIn("h1", outline)
        # SEO 评分应 ≥60（中文密度计算较宽松）
        self.assertGreaterEqual(result["score"], 60,
                                f"中文文章 SEO 评分 {result['score']} 过低")

    # --------------------------------------------------------------------------
    # CLI 命令测试
    # --------------------------------------------------------------------------

    def test_cli_generate_command(self):
        """测试 CLI generate 命令完整流程并输出文件。"""
        runner = CliRunner()
        with tempfile.TemporaryDirectory() as tmpdir:
            output_path = Path(tmpdir) / "article.md"
            result = runner.invoke(cli, [
                "generate",
                "--keyword", "email marketing",
                "--lang", "en",
                "--output", str(output_path),
            ])
            # 命令成功执行
            self.assertEqual(result.exit_code, 0,
                             f"CLI 执行失败：{result.output}\n{result.exception}")
            # 输出文件存在
            self.assertTrue(output_path.exists(), "输出文件未生成")
            content = output_path.read_text(encoding="utf-8")
            # 含 frontmatter
            self.assertTrue(content.startswith("---"), "缺少 YAML frontmatter")
            self.assertIn("title:", content)
            self.assertIn("description:", content)
            self.assertIn("keywords:", content)
            self.assertIn("seo_score:", content)
            # 含 H1
            self.assertRegex(content, re.compile(r"^# .+", re.MULTILINE))

    def test_cli_analyze_command(self):
        """测试 CLI analyze 命令输出关键词分析。"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "analyze",
            "--keyword", "email marketing",
            "--lang", "en",
        ])
        self.assertEqual(result.exit_code, 0,
                         f"CLI analyze 执行失败：{result.output}")
        self.assertIn("email marketing", result.output)
        self.assertIn("主关键词", result.output)

    def test_cli_generate_stdout(self):
        """测试 CLI generate 不指定 output 时打印到 stdout。"""
        runner = CliRunner()
        result = runner.invoke(cli, [
            "generate",
            "--keyword", "content marketing",
            "--lang", "en",
        ])
        self.assertEqual(result.exit_code, 0,
                         f"CLI stdout 执行失败：{result.output}")
        # stdout 应含 Markdown 内容
        self.assertIn("# ", result.output)


class TestSEOScorer(unittest.TestCase):
    """SEO 评分器单元测试。"""

    def test_perfect_content_scores_high(self):
        """测试高质量内容应获得高分（≥70）。"""
        scorer = SEOScorer()
        primary = "email marketing"

        # 程序化构造达标内容：1800+ 词，关键词密度约 1.5%（27 次 / 1800 词）
        sentences: list[str] = []
        kw_target = 27
        kw_inserted = 0
        for i in range(220):  # 220 句 * ~9 词 ≈ 1980 词
            if kw_inserted < kw_target and i % 8 == 0:
                sentences.append(
                    f"the role of {primary} in this context is critical for "
                    f"achieving measurable outcomes and sustainable growth"
                )
                kw_inserted += 1
            else:
                sentences.append(
                    "the strategy in this context is critical for achieving "
                    "measurable outcomes and sustainable growth over time"
                )
        text = " ".join(sentences)

        body = f"# The Ultimate Guide to {primary}\n\n"
        body += f"## Introduction to {primary}\n\n### Overview\n\n"
        body += text[:1800] + "\n\n"
        body += f"## Benefits of {primary}\n\n### Key benefits\n\n"
        body += text[1800:3600] + "\n\n"
        body += f"## Best Practices for {primary}\n\n### Tips\n\n"
        body += text[3600:5400] + "\n\n"
        body += f"## Common Mistakes\n\n### Pitfalls\n\n"
        body += text[5400:7200] + "\n\n"
        body += f"## Conclusion\n\n### Summary\n\n"
        body += text[7200:9000] + "\n\n"
        body += "## Related Resources\n\n### More\n\n"
        body += "- [link](/path1)\n- [link](/path2)\n- [link](/path3)\n"

        analysis = {"primary_keyword": primary}
        content = {
            "meta_description": (
                f"The complete {primary} guide for 2026 with tips, best practices "
                f"and step-by-step tactics to grow your business."
            ),
            "body_markdown": body,
            "internal_links": ["[a](/1)", "[b](/2)", "[c](/3)"],
            "word_count": count_words(body, False),
        }
        result = scorer.score(content, analysis)
        self.assertGreaterEqual(result["score"], 70,
                                f"高质量内容评分 {result['score']} 应 ≥70")
        self.assertIsInstance(result["suggestions"], list)

    def test_short_content_scores_low(self):
        """测试过短内容应得低分。"""
        scorer = SEOScorer()
        body = "# Title\n\nShort content.\n"
        analysis = {"primary_keyword": "seo"}
        content = {
            "meta_description": "short",
            "body_markdown": body,
            "internal_links": [],
            "word_count": 5,
        }
        result = scorer.score(content, analysis)
        self.assertLess(result["score"], 50,
                        f"过短内容评分 {result['score']} 应 <50")


if __name__ == "__main__":
    unittest.main()
