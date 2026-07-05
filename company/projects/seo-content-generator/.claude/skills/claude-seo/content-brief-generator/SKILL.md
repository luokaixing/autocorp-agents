---
name: content-brief-generator
description: 生成结构化 SEO 内容 brief，含目标关键词、受众画像、大纲建议与竞品分析
---

# Content Brief Generator

## 用途
基于主关键词与目标受众，产出结构化的内容 brief，指导后续大纲生成与正文写作。
brief 覆盖：目标关键词簇、受众画像、搜索意图、大纲建议、竞品分析、差异化角度与字数建议。
作为 AutoCorp SEO 内容生成管线的入口环节，由 ProductManager 在选题阶段调用。

## 输入
- keyword: str - 主目标关键词，例如 "ethereum wallet"
- audience: str - 目标受众标识，例如 "crypto" / "beginner" / "defi"

## 输出格式
Markdown 文档，包含以下字段（以列表形式呈现，不使用 JSON 字面量）：
- 目标关键词：主关键词 + 3-5 个次要关键词 + 5-10 个长尾词
- 受众画像：核心痛点、阅读动机、决策路径
- 搜索意图：informational / commercial / transactional / navigational
- 大纲建议：H1 + 3-5 个 H2 + 每个 H2 下 2-3 个 H3
- 竞品分析：3 个竞品角度 + 1 个差异化切入点
- 字数建议：建议正文字数范围（如 1500-2000 字）

## 提示词模板
你是一名资深 SEO 内容策略师。请基于以下输入生成结构化内容 brief。

主目标关键词：{keyword}
目标受众：{audience}

要求：
1. 围绕「{keyword}」扩展关键词簇，覆盖次要关键词与长尾词。
2. 针对「{audience}」受众画像，分析核心痛点与阅读动机。
3. 推断搜索意图，并据此调整大纲深度。
4. 给出 H1 + 3-5 个 H2 的大纲建议，每个 H2 下含 2-3 个 H3。
5. 提供 3 个竞品角度与 1 个差异化切入点。
6. 全程使用中文输出（关键词保留英文原文）。

## 调用示例
python:
    from engine.llm_client import load_seo_skills
    skills = load_seo_skills()
    skill = skills["content-brief-generator"]
    prompt = skill["prompt"].format(keyword="ethereum wallet", audience="crypto")
    # 将 prompt 作为 system prompt 调用 LLM 生成 brief
