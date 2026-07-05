---
name: backlink-prospector
description: 识别外链建设机会，挖掘可投稿站点、资源页与竞品外链来源
---

# Backlink Prospector

## 用途
基于目标关键词与主题，识别外链建设机会，输出可执行的外链获取清单，
覆盖 guest post 投稿站点、资源页、竞品外链来源与 broken link 机会。
作为 claude-seo 套件的一部分，供后续外链建设流程调用。

## 输入
- keyword: str - 目标关键词
- topic: str - 内容主题 / 行业领域

## 输出格式
Markdown 清单，含以下字段（以列表形式呈现，不使用 JSON 字面量）：
- 投稿站点：5-10 个可 guest post 的站点，含域名、DA 预估、投稿入口
- 资源页机会：5 个可申请收录的资源页
- 竞品外链来源：3-5 个竞品获取外链的站点
- Broken link 机会：3 个可替换的失效外链
- 优先级排序：按 DA 与相关性综合排序

## 提示词模板
你是一名外链建设专家。请基于以下输入识别外链建设机会。

目标关键词：{keyword}
内容主题：{topic}

要求：
1. 列出 5-10 个接受 guest post 的站点，标注 DA 与投稿方式。
2. 找出 5 个可申请收录的资源页。
3. 分析 3-5 个竞品外链来源站点。
4. 识别 3 个 broken link 替换机会。
5. 按 DA 与相关性对全部机会排序。

## 调用示例
python:
    from engine.llm_client import load_seo_skills
    skills = load_seo_skills()
    skill = skills["backlink-prospector"]
    prompt = skill["prompt"].format(keyword="ethereum wallet", topic="crypto")
    # 将 prompt 作为 system prompt 调用 LLM 识别外链机会
