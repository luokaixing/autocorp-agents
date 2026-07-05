---
name: technical-seo-auditor
description: 文章上线前 SEO 体检，检查标题/元描述/Heading 层级/内链/图片 alt/速度等维度并给出评分
---

# Technical SEO Auditor

## 用途
在文章发布前执行技术 SEO 体检，识别影响排名与用户体验的问题，
输出 0-100 分与可执行优化建议，分数低于 70 时建议阻断发布。
由 SEOScorer.audit_with_skill 调用，作为发布门禁。

## 输入
- article_path: str - 待体检文章的 Markdown 文件路径

## 输出格式
结构化结果（以列表形式描述字段，不使用 JSON 字面量）：
- score: int - 0-100 总分
- suggestions: list - 问题清单与优化建议，按严重程度排序
- block_publish: bool - 是否阻断发布（score < 70 时为 True）

体检维度与权重：
- 标题（20%）：H1 唯一、含主关键词、长度 20-70 字符
- 元描述（15%）：长度 120-155 字符、含主关键词
- Heading 层级（20%）：H1+H2+H3 结构完整、H2≥3、层级无跳级
- 内链（15%）：≥3 个站内链接
- 图片 alt（10%）：图片均有描述性 alt 文本
- 加载速度预估（20%）：图片数量合理、无冗余

## 提示词模板
你是一名技术 SEO 审核专家。请对以下文章执行上线前 SEO 体检。

文章路径：{article_path}

体检维度与评分权重：
1. 标题（20%）：H1 唯一、含主关键词、长度 20-70 字符
2. 元描述（15%）：长度 120-155 字符、含主关键词、有行动号召
3. Heading 层级（20%）：H1+H2+H3 结构完整、H2≥3、层级无跳级
4. 内链（15%）：≥3 个站内链接、锚文本相关
5. 图片 alt（10%）：图片均有描述性 alt 文本
6. 加载速度预估（20%）：图片体积、代码精简度、无阻塞资源

评分规则：总分 = 各维度加权得分之和；总分 < 70 → 阻断发布。

## 调用示例
python:
    from engine.llm_client import load_seo_skills
    skills = load_seo_skills()
    skill = skills["technical-seo-auditor"]
    prompt = skill["prompt"].format(article_path="/path/to/article.md")
    # SEOScorer.audit_with_skill 基于该 skill 维度做规则体检
