"""SEO Content Generator 包

AutoCorp 首个商业化产品 MVP：SEO 内容自动化生成器。
基于 LLM 抽象层（TemplateProvider 兜底 / OpenAI 兼容后端）生成 SEO 优化的长文。

模块组成：
    - llm_provider: LLM 抽象层与 TemplateProvider 兜底实现。
    - keyword_analyzer: 关键词分析与长尾词扩展。
    - outline_generator: 文章大纲生成（H1/H2/H3 结构）。
    - content_writer: 正文写作与 meta / 内链生成。
    - seo_scorer: 多维度 SEO 评分。
    - cli: Click CLI 入口。
"""
from __future__ import annotations

__version__ = "0.1.0"
__all__ = ["__version__"]
