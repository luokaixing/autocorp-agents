---
name: schema-markup-generator
description: 生成 JSON-LD 结构化数据，支持 Article / BreadcrumbList / FAQPage 类型
---

# Schema Markup Generator

## 用途
为文章生成 JSON-LD 结构化数据标记，帮助搜索引擎理解内容并获取富媒体摘要。
支持三种类型：Article（文章）、BreadcrumbList（面包屑）、FAQPage（常见问题）。
由 ContentWriter.generate_schema_markup 调用，产出可嵌入 HTML 的结构化数据。

## 输入
- title: str - 文章标题
- description: str - 文章摘要 / meta description
- author: str - 作者名称
- date_published: str - 发布日期（ISO 8601，如 2026-06-28）
- url: str - 文章 canonical URL

## 输出格式
合法的 JSON-LD 字符串，使用 schema.org 词汇表，包含以下类型：
- Article：@context / @type / headline / description / author / datePublished / mainEntityOfPage
- BreadcrumbList：@context / @type / itemListElement（首页 → 分类 → 文章）
- FAQPage：@context / @type / mainEntity（含 3-5 个 Q&A）

Article 类型字段说明（以列表描述，不在此处展开 JSON 字面量）：
- @context：固定为 https://schema.org
- @type：Article
- headline：文章标题
- description：文章摘要
- author：作者对象，含 @type=Person 与 name
- datePublished：ISO 8601 发布日期
- mainEntityOfPage：文章 URL

## 提示词模板
你是一名结构化数据专家。请基于以下输入生成 JSON-LD 标记。

文章标题：{title}
文章摘要：{description}
作者：{author}
发布日期：{date_published}
文章 URL：{url}

要求：
1. 生成 Article 类型的 JSON-LD，字段完整且合法。
2. 生成 BreadcrumbList，路径为 首页 → 分类页 → 文章页。
3. 若文章含 FAQ，额外生成 FAQPage 类型。
4. 输出可直接嵌入 HTML 的 script 标签块。
5. 所有日期使用 ISO 8601 格式。

## 调用示例
python:
    from engine.llm_client import load_seo_skills
    skills = load_seo_skills()
    skill = skills["schema-markup-generator"]
    prompt = skill["prompt"].format(
        title="Ethereum Wallet Guide",
        description="Complete guide to Ethereum wallets in 2026.",
        author="AutoCorp",
        date_published="2026-06-28",
        url="https://example.com/ethereum-wallet-guide",
    )
    # ContentWriter.generate_schema_markup 基于该 skill 字段定义构造 JSON-LD
