"""正文写作模块

基于大纲与关键词分析生成完整 Markdown 正文，含 H1/H2/H3 结构、内链建议、
meta description。正文 ≥1500 字，关键词密度 1-2%。
"""
from __future__ import annotations

import re
from pathlib import Path
from typing import Any, Optional

from .llm_provider import (
    LLMProvider,
    TemplateProvider,
    count_words,
    get_provider,
    optimize_keyword_density,
    safe_json_loads,
)
from .templates import (
    INTERNAL_LINK_TEMPLATES_EN,
    INTERNAL_LINK_TEMPLATES_ZH,
    SYSTEM_PROMPT_CONTENT,
)


class ContentWriter:
    """正文写作者：基于大纲生成完整 Markdown 正文与元信息。"""

    def __init__(self, provider: LLMProvider = None):
        self.provider = provider or get_provider("template")

    def write(self, outline: dict, keyword_analysis: dict,
              language: str = "en", pdf_path: Optional[str] = None) -> dict:
        """基于大纲与关键词分析撰写正文。

        Args:
            outline: OutlineGenerator.generate() 的输出。
            keyword_analysis: KeywordAnalyzer.analyze() 的输出。
            language: 目标语言，'en' 或 'zh'。
            pdf_path: 可选 PDF 白皮书路径，提供时先转 MD 并引用真实数据作为
                E-E-A-T 证据（提升专业度与可信度）。

        Returns:
            dict：{meta_description, body_markdown, internal_links, word_count,
                   whitepaper_md_path}
        """
        import json

        whitepaper_content = ""
        whitepaper_md_path = None
        if pdf_path:
            try:
                # 延迟导入避免 content_miner 在未安装 PDF 依赖时影响模块加载
                from engine.content_miner import ContentMiner
                miner = ContentMiner()
                whitepaper_md_path = miner.pdf_to_markdown(pdf_path)
                # 截取前 5000 字作为 prompt 证据，避免超长
                whitepaper_content = Path(whitepaper_md_path).read_text(
                    encoding="utf-8")[:5000]
            except Exception as e:
                # 白皮书引用为增强项，失败不应阻断主流程
                import logging
                logging.getLogger(__name__).warning(
                    "PDF 白皮书引用失败，跳过: %s", e)

        payload = {
            "outline": outline,
            "keyword_analysis": keyword_analysis,
            "language": language,
        }
        if whitepaper_content:
            payload["whitepaper_evidence"] = whitepaper_content

        user_message = json.dumps(payload, ensure_ascii=False)

        body_markdown = ""
        try:
            body_markdown = self.provider.generate(SYSTEM_PROMPT_CONTENT, user_message)
            if not body_markdown or len(body_markdown.strip()) < 200:
                raise ValueError("provider 返回的正文过短")
        except Exception:
            # 兜底：直接用 TemplateProvider 重新生成
            fallback = TemplateProvider()
            body_markdown = fallback.generate(SYSTEM_PROMPT_CONTENT, user_message)

        primary = keyword_analysis.get("primary_keyword", "SEO")
        is_zh = language.lower().startswith("zh") or _has_chinese(primary)

        # 确保正文达到字数要求（兜底补充）
        body_markdown = self._ensure_min_length(body_markdown, primary, is_zh)

        # 字数补充后重新优化关键词密度（防止 FAQ 段落引入过多关键词）
        body_markdown = optimize_keyword_density(body_markdown, primary, is_zh)

        # 生成 meta description（≤155 字符，含主关键词）
        meta_description = self._build_meta_description(outline, primary, is_zh)

        # 提取 / 生成内链建议
        internal_links = self._extract_internal_links(body_markdown)
        if len(internal_links) < 3:
            internal_links = self._build_internal_links(primary, is_zh)

        word_count = count_words(body_markdown, is_zh)

        return {
            "meta_description": meta_description,
            "body_markdown": body_markdown,
            "internal_links": internal_links,
            "word_count": word_count,
            "whitepaper_md_path": whitepaper_md_path,
        }

    # ------------------------------------------------------------------
    # SubTask 1.5: 基于 claude-seo schema-markup-generator 生成 JSON-LD
    # 设计要点：
    # - 加载 schema-markup-generator skill 获取字段定义（仅参考）
    # - 基于字段定义在代码中确定性构造 JSON-LD，不依赖 LLM
    # - 返回合法 JSON 字符串，含 @context / @type / headline / author 等
    # ------------------------------------------------------------------
    def generate_schema_markup(self, article: dict) -> str:
        """生成 JSON-LD schema 标记。

        基于 claude-seo schema-markup-generator 的字段定义，构造 Article 类型的
        JSON-LD 结构化数据，含 @context / @type / headline / description / author /
        datePublished / mainEntityOfPage。返回可直接嵌入 HTML 的 JSON 字符串。

        Args:
            article: 文章字典，支持字段（缺字段使用安全默认值）：
                title / h1 - 文章标题
                description / meta_description - 文章摘要
                author - 作者名称
                date_published / date - 发布日期（ISO 8601）
                url - 文章 canonical URL
                article_body - 正文内容（可选）
                image - 图片 URL（可选）

        Returns:
            合法的 JSON-LD 字符串（未包裹 script 标签，便于调用方自行嵌入）。
        """
        import json

        from engine.llm_client import load_seo_skills

        # 加载 skill 获取字段指引（失败不影响生成）
        try:
            load_seo_skills()
        except FileNotFoundError:
            pass

        title = article.get("title") or article.get("h1") or "Untitled Article"
        description = (
            article.get("description") or article.get("meta_description") or ""
        )
        author = article.get("author") or "AutoCorp"
        date_published = (
            article.get("date_published") or article.get("date") or ""
        )
        url = article.get("url") or ""

        schema = {
            "@context": "https://schema.org",
            "@type": "Article",
            "headline": title,
            "description": description,
            "author": {
                "@type": "Person",
                "name": author,
            },
            "publisher": {
                "@type": "Organization",
                "name": "AutoCorp",
            },
            "mainEntityOfPage": {
                "@type": "WebPage",
                "@id": url,
            },
        }
        if date_published:
            schema["datePublished"] = date_published
        if article.get("article_body"):
            schema["articleBody"] = article["article_body"]
        if article.get("image"):
            schema["image"] = article["image"]

        return json.dumps(schema, ensure_ascii=False, indent=2)

    # ------------------------------------------------------------------
    # Skill 写作（seo-blog-writer）
    # ------------------------------------------------------------------

    # SKILL.md 路径：seo_generator/../.claude/skills/seo-blog-writer/SKILL.md
    _SKILL_PATH = Path(__file__).resolve().parent.parent / ".claude" / "skills" / "seo-blog-writer" / "SKILL.md"

    def write_with_skill(self, source: str, keyword: str,
                         tone: str = "professional", length: int = 1500) -> str:
        """使用 seo-blog-writer Skill 写作。

        加载 SKILL.md 作为 system prompt，填入 source/keyword/tone/length 后调用 LLM；
        TemplateProvider 兜底时基于 keyword 走 write() 流程生成正文。
        最后用 SKILL.md 中的禁用句式列表做反 AI 味清洗。

        Args:
            source: URL/笔记路径/主题文本。
            keyword: 目标 SEO 关键词。
            tone: 写作语气（professional/casual/expert）。
            length: 目标字数。

        Returns:
            Markdown 文章字符串。

        Raises:
            FileNotFoundError: SKILL.md 不存在时抛出。
        """
        system_prompt = self._load_skill_prompt(self._SKILL_PATH)
        if not system_prompt:
            raise FileNotFoundError(f"未找到 SKILL.md：{self._SKILL_PATH}")

        # 格式化 prompt 填入 source/keyword/tone/length
        system_prompt = self._format_skill_prompt(
            system_prompt, source, keyword, tone, length)

        # 构造 user message（半结构化，便于真实 LLM 与兜底解析）
        user_message = (
            f"source: {source}\n"
            f"keyword: {keyword}\n"
            f"tone: {tone}\n"
            f"length: {length}\n"
        )

        # 调用 LLM 生成
        article = ""
        try:
            article = self.provider.generate(system_prompt, user_message)
            if not article or len(article.strip()) < 200:
                raise ValueError("provider 返回的正文过短")
        except Exception:
            # 兜底：TemplateProvider 不含任务标记时仅回显 user_message，
            # 此时基于 keyword 构建大纲+关键词分析，走 write() 流程生成正文
            article = self._fallback_skill_article(keyword, source)

        # 字数兜底（先补足再清洗，保证清洗后仍够字数）
        is_zh = _has_chinese(keyword) or _has_chinese(source)
        article = self._ensure_min_length(article, keyword, is_zh)

        # 反 AI 味清洗：用 SKILL.md 中的禁用句式列表后处理
        banned = self._parse_banned_phrases(self._SKILL_PATH)
        article = self._scrub_ai_phrases(article, banned)

        return article

    # ------------------------------------------------------------------
    # 统一入口 generate（向后兼容）
    # ------------------------------------------------------------------

    def generate(self, outline: dict = None, keyword_analysis: dict = None,
                 language: str = "en", use_skill: bool = False,
                 source: str = None, keyword: str = None) -> str:
        """生成 SEO 文章（统一入口）。

        Args:
            outline: 大纲（use_skill=False 时使用，OutlineGenerator.generate() 输出）。
            keyword_analysis: 关键词分析（use_skill=False 时使用）。
            language: 目标语言，'en' 或 'zh'。
            use_skill: 是否使用 seo-blog-writer Skill。默认 False，走原有模板流程。
            source: 当 use_skill=True 时必填，URL/笔记/主题。
            keyword: 当 use_skill=True 时必填，目标关键词。

        Returns:
            Markdown 文章字符串。

        Raises:
            ValueError: use_skill=True 但缺 source/keyword 时抛出；
                use_skill=False 但缺 outline/keyword_analysis 时抛出。
        """
        if use_skill:
            if not source or not keyword:
                raise ValueError("use_skill=True 时必须提供 source 和 keyword")
            return self.write_with_skill(source, keyword)
        # 原有逻辑：基于大纲与关键词分析生成正文，返回 body_markdown 字符串
        if not outline or not keyword_analysis:
            raise ValueError("use_skill=False 时必须提供 outline 和 keyword_analysis")
        content = self.write(outline, keyword_analysis, language=language)
        return content.get("body_markdown", "")

    # ------------------------------------------------------------------
    # 内部方法
    # ------------------------------------------------------------------

    def _build_meta_description(self, outline: dict, primary: str,
                                is_zh: bool) -> str:
        """构建 ≤155 字符的 meta description，含主关键词。"""
        h1 = outline.get("h1", "")
        if is_zh:
            desc = (
                f"全面解析{primary}：从基础概念到高级战术，含分步指南、最佳实践与常见误区。"
                f"2026 年最实用的{primary}实战手册，助你快速提升效果。"
            )
        else:
            desc = (
                f"The complete {primary} guide for 2026: definitions, benefits, "
                f"step-by-step tactics, best practices, and common mistakes to avoid. "
                f"Start mastering {primary} today."
            )
        # 截断到 155 字符（尽量在词边界截断）
        if len(desc) > 155:
            desc = desc[:154].rsplit(" ", 1)[0] if not is_zh else desc[:155]
        return desc

    def _extract_internal_links(self, body: str) -> list[str]:
        """从正文中提取内链 Markdown 列表。"""
        # 匹配 [text](/path) 形式，仅保留站内路径（以 / 开头）
        pattern = re.compile(r"\[([^\]]+)\]\((/[^\)]+)\)")
        return [f"[{m.group(1)}]({m.group(2)})" for m in pattern.finditer(body)]

    def _build_internal_links(self, primary: str, is_zh: bool) -> list[str]:
        """基于模板生成内链建议（3-5 个）。"""
        templates = INTERNAL_LINK_TEMPLATES_ZH if is_zh else INTERNAL_LINK_TEMPLATES_EN
        kw_slug = re.sub(r"[^\w\-]+", "-", primary.lower()).strip("-") or "topic"
        links: list[str] = []
        for anchor_tpl, url_tpl in templates:
            if len(links) >= 5:
                break
            anchor = anchor_tpl.replace("{kw}", primary)
            url = url_tpl.replace("{kw_slug}", kw_slug)
            links.append(f"[{anchor}]({url})")
        return links[:5]

    def _ensure_min_length(self, body: str, primary: str,
                           is_zh: bool) -> str:
        """确保正文达到 1500 字，不足时补充 FAQ 段落。"""
        target = 1500
        attempts = 0
        while count_words(body, is_zh) < target and attempts < 5:
            attempts += 1
            if is_zh:
                extra = (
                    f"\n## 关于{primary}的补充说明\n\n"
                    f"### 为什么{primary}在 2026 年尤其重要\n\n"
                    f"市场环境正在快速变化，{primary}的重要性比以往任何时候都更突出。"
                    f"用户行为、算法更新与竞争格局都在重塑{primary}的执行方式。"
                    f"掌握最新的{primary}方法，意味着你能比竞争对手更快抓住机会。"
                    f"建议每季度复盘一次{primary}策略，确保与行业趋势同步。\n\n"
                    f"### {primary}的长期价值\n\n"
                    f"坚持{primary}的团队往往能在 6 到 12 个月后看到显著回报。"
                    f"这与复利效应类似：早期投入看似缓慢，但一旦动量建立，"
                    f"{primary}带来的增长会越来越稳定。把{primary}视为长期资产，"
                    f"而非一次性项目，是取得持续成功的关键。\n"
                )
            else:
                extra = (
                    f"\n## Additional Insights on {primary}\n\n"
                    f"### Why {primary} matters more than ever in 2026\n\n"
                    f"The market is shifting rapidly, and {primary} has become more "
                    f"important than ever. User behavior, algorithm updates, and the "
                    f"competitive landscape are reshaping how {primary} should be "
                    f"executed. Teams that master the latest {primary} methods can "
                    f"seize opportunities faster than their competitors. Review your "
                    f"{primary} strategy every quarter to stay aligned with industry "
                    f"trends.\n\n"
                    f"### The long-term value of {primary}\n\n"
                    f"Teams that commit to {primary} typically see significant returns "
                    f"within 6 to 12 months. It works like compound interest: early "
                    f"effort feels slow, but once momentum builds, the growth from "
                    f"{primary} becomes increasingly stable. Treating {primary} as a "
                    f"long-term asset rather than a one-off project is the key to "
                    f"sustained success.\n"
                )
            body += extra
        return body

    # ------------------------------------------------------------------
    # Skill 辅助方法
    # ------------------------------------------------------------------

    def _load_skill_prompt(self, skill_path: Path) -> str:
        """加载 SKILL.md 并提取"提示词模板"章节内容作为 system prompt。

        解析流程：
            1. 去除 YAML frontmatter（--- 包裹）。
            2. 提取 "## 提示词模板" 到下一个 "## " 之间的正文。
            3. 兜底：返回去除 frontmatter 后的全部正文。
        """
        if not skill_path.exists():
            return ""
        text = skill_path.read_text(encoding="utf-8")
        # 去除 frontmatter
        if text.startswith("---"):
            parts = text.split("---", 2)
            if len(parts) >= 3:
                text = parts[2]
        # 提取"提示词模板"章节（到下一个 H2 之前，H3 不截断）
        match = re.search(r"## 提示词模板\s*\n(.*?)(?=\n## |\Z)", text, re.DOTALL)
        if match:
            return match.group(1).strip()
        return text.strip()

    def _format_skill_prompt(self, template: str, source: str,
                             keyword: str, tone: str, length: int) -> str:
        """格式化 SKILL.md 提示词模板，填入 source/keyword/tone/length。

        优先用 str.format；若模板含未识别占位符则退化为手动 replace，保证健壮性。
        """
        try:
            return template.format(
                source=source, keyword=keyword, tone=tone, length=length,
            )
        except (KeyError, IndexError, ValueError):
            return (template
                    .replace("{source}", str(source))
                    .replace("{keyword}", str(keyword))
                    .replace("{tone}", str(tone))
                    .replace("{length}", str(length)))

    def _parse_banned_phrases(self, skill_path: Path) -> list[str]:
        """从 SKILL.md 的"反 AI 味清单（禁用句式）"章节解析禁用句式列表。

        解析以 "- " 开头的列表项，支持 .* 通配（正则）。
        """
        if not skill_path.exists():
            return []
        text = skill_path.read_text(encoding="utf-8")
        match = re.search(
            r"## 反 AI 味清单[^\n]*\n(.*?)(?=\n## |\Z)", text, re.DOTALL,
        )
        if not match:
            return []
        section = match.group(1)
        phrases: list[str] = []
        for line in section.splitlines():
            line = line.strip()
            if line.startswith("- "):
                phrase = line[2:].strip()
                if phrase:
                    phrases.append(phrase)
        return phrases

    def _scrub_ai_phrases(self, article: str, banned: list[str]) -> str:
        """用禁用句式列表清洗文章：移除命中禁用句式的句子（保留标题/列表/代码行）。

        逐行处理：标题（#）、列表（- ）、代码围栏（```）原样保留；
        段落行按句切分，剔除命中禁用句式的句子。
        """
        if not article or not banned:
            return article
        # 预编译禁用模式（支持 .* 通配；非法正则退化为字面匹配）
        patterns: list[re.Pattern] = []
        for phrase in banned:
            try:
                patterns.append(re.compile(phrase))
            except re.error:
                patterns.append(re.compile(re.escape(phrase)))

        out_lines: list[str] = []
        for line in article.split("\n"):
            stripped = line.lstrip()
            # 标题 / 列表 / 代码行原样保留
            if (stripped.startswith("#")
                    or stripped.startswith("- ")
                    or stripped.startswith("```")):
                out_lines.append(line)
                continue
            # 按句切分（中英文句末标点）并过滤命中禁用句式的句子
            sentences = re.split(r"(?<=[。！？!?])", line)
            kept = []
            for sent in sentences:
                if not sent.strip():
                    kept.append(sent)
                    continue
                if not any(p.search(sent) for p in patterns):
                    kept.append(sent)
            out_lines.append("".join(kept))
        result = "\n".join(out_lines)
        # 压缩多余空行
        result = re.sub(r"\n{3,}", "\n\n", result)
        return result

    def _fallback_skill_article(self, keyword: str, source: str) -> str:
        """TemplateProvider 兜底：基于 keyword 构建大纲与关键词分析，走 write() 生成正文。

        当 provider 为 TemplateProvider 且 system prompt 不含任务标记时，
        provider.generate 仅回显 user_message，此时用既有大纲+关键词分析流程兜底。
        """
        # 延迟导入避免循环依赖
        from .keyword_analyzer import KeywordAnalyzer
        from .outline_generator import OutlineGenerator

        is_zh = _has_chinese(keyword) or _has_chinese(source)
        language = "zh" if is_zh else "en"

        analyzer = KeywordAnalyzer(provider=self.provider)
        analysis = analyzer.analyze(keyword, language=language)
        outliner = OutlineGenerator(provider=self.provider)
        outline = outliner.generate(analysis, language=language)
        content = self.write(outline, analysis, language=language)
        return content.get("body_markdown", "")


def _has_chinese(text: str) -> bool:
    """判断文本是否含中文字符。"""
    return bool(text and re.search(r"[\u4e00-\u9fff]", text))
