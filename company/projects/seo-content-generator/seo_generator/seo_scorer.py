"""SEO 评分模块

基于规则对生成内容进行多维度 SEO 评分，输出 0-100 分与优化建议。
评分维度与权重：
    - 关键词密度 (20%): 1-2% 满分，0% 或 >3% 零分，中间线性插值。
    - 标题结构 (20%): 含 H1+H2+H3 满分，缺一扣分。
    - 字数 (15%): ≥1500 满分，<800 零分，中间线性插值。
    - H2/H3 层级 (15%): ≥3 个 H2 且每个 H2 下有 H3 满分。
    - 内链 (15%): ≥3 个满分，按比例评分。
    - meta (15%): 长度 120-155 字符且含主关键词满分。
"""
from __future__ import annotations

import re
from typing import Any

from .llm_provider import count_words


class SEOScorer:
    """SEO 评分器：基于规则对内容进行多维度评分。"""

    def score(self, content: dict, keyword_analysis: dict) -> dict:
        """对生成内容进行 SEO 评分。

        Args:
            content: ContentWriter.write() 的输出，含
                {meta_description, body_markdown, internal_links, word_count}。
            keyword_analysis: KeywordAnalyzer.analyze() 的输出。

        Returns:
            dict：{score(0-100), suggestions[]}
        """
        body = content.get("body_markdown", "") or ""
        meta = content.get("meta_description", "") or ""
        internal_links = content.get("internal_links", []) or []
        word_count = content.get("word_count") or count_words(body, _has_chinese(body))
        primary = (keyword_analysis.get("primary_keyword") or "").strip()

        # 各维度评分（0-1 比例分）
        density_ratio, density_note = self._score_keyword_density(body, primary)
        structure_ratio, structure_note = self._score_heading_structure(body)
        wordcount_ratio, wordcount_note = self._score_word_count(word_count)
        hierarchy_ratio, hierarchy_note = self._score_h2h3_hierarchy(body)
        links_ratio, links_note = self._score_internal_links(internal_links)
        meta_ratio, meta_note = self._score_meta(meta, primary)

        # 加权总分（各维度权重之和为 1.0）
        total = (
            density_ratio * 0.20
            + structure_ratio * 0.20
            + wordcount_ratio * 0.15
            + hierarchy_ratio * 0.15
            + links_ratio * 0.15
            + meta_ratio * 0.15
        )
        score = round(total * 100)

        # 汇总优化建议
        suggestions: list[str] = []
        for note in (density_note, structure_note, wordcount_note,
                     hierarchy_note, links_note, meta_note):
            if note:
                suggestions.append(note)

        return {"score": score, "suggestions": suggestions}

    # ------------------------------------------------------------------
    # 各维度评分
    # ------------------------------------------------------------------

    def _score_keyword_density(self, body: str, primary: str) -> tuple[float, str]:
        """关键词密度评分：1-2% 满分，0% 或 >3% 零分。"""
        if not primary:
            return 0.0, "未检测到主关键词，无法评估关键词密度。"
        is_zh = _has_chinese(primary)
        words = count_words(body, is_zh)
        if words == 0:
            return 0.0, "正文为空，无法计算关键词密度。"

        if is_zh:
            occurrences = body.count(primary)
            # 中文密度 = 关键词字符出现次数 / 总字数
            density = occurrences / words if words else 0.0
        else:
            occurrences = len(re.findall(
                r"\b" + re.escape(primary) + r"\b", body, re.IGNORECASE,
            ))
            density = occurrences / words if words else 0.0

        pct = density * 100

        # 评分规则：1-2% 满分；0% 或 >3% 零分；中间线性插值
        if pct == 0:
            return 0.0, f"关键词密度为 0%，主关键词 '{primary}' 未在正文中出现。"
        if pct > 3:
            return 0.0, f"关键词密度 {pct:.2f}% 过高（>3%），存在过度优化风险，请减少关键词堆砌。"
        if 1 <= pct <= 2:
            return 1.0, ""
        if pct < 1:
            # 0-1% 线性插值
            ratio = pct / 1.0
            return ratio, f"关键词密度 {pct:.2f}% 偏低（建议 1-2%），可适当增加 '{primary}' 的自然出现。"
        # 2-3% 线性递减
        ratio = (3.0 - pct) / 1.0
        return ratio, f"关键词密度 {pct:.2f}% 略高（建议 1-2%），可适当减少 '{primary}' 的出现频次。"

    def _score_heading_structure(self, body: str) -> tuple[float, str]:
        """标题结构评分：含 H1+H2+H3 满分。"""
        has_h1 = bool(re.search(r"^#\s+\S", body, re.MULTILINE))
        has_h2 = bool(re.search(r"^##\s+\S", body, re.MULTILINE))
        has_h3 = bool(re.search(r"^###\s+\S", body, re.MULTILINE))

        present = sum([has_h1, has_h2, has_h3])
        ratio = present / 3.0

        missing = []
        if not has_h1:
            missing.append("H1")
        if not has_h2:
            missing.append("H2")
        if not has_h3:
            missing.append("H3")
        note = f"标题结构缺少：{', '.join(missing)}。" if missing else ""
        return ratio, note

    def _score_word_count(self, word_count: int) -> tuple[float, str]:
        """字数评分：≥1500 满分，<800 零分，中间线性插值。"""
        if word_count >= 1500:
            return 1.0, ""
        if word_count < 800:
            return 0.0, f"字数 {word_count} 过少（<800），SEO 长文建议 ≥1500 字。"
        # 800-1500 线性插值
        ratio = (word_count - 800) / (1500 - 800)
        return ratio, f"字数 {word_count} 偏少（建议 ≥1500），可补充更多实质性内容。"

    def _score_h2h3_hierarchy(self, body: str) -> tuple[float, str]:
        """H2/H3 层级评分：≥3 个 H2 且每个 H2 下有 H3 满分。"""
        lines = body.splitlines()
        h2_indices: list[int] = []
        h3_count_after: list[int] = []  # 每个 H2 后到下一个 H2 之前的 H3 数

        # 收集所有 H2 行索引（排除 H3：用 ^## 但不是 ^###）
        for idx, line in enumerate(lines):
            if re.match(r"^##\s+\S", line) and not re.match(r"^###\s+\S", line):
                h2_indices.append(idx)

        if not h2_indices:
            return 0.0, "未检测到 H2 标题，建议添加 3-5 个 H2 章节。"

        # 统计每个 H2 后的 H3 数量
        for i, start in enumerate(h2_indices):
            end = h2_indices[i + 1] if i + 1 < len(h2_indices) else len(lines)
            h3_in_section = sum(
                1 for ln in lines[start + 1:end] if re.match(r"^###\s+\S", ln)
            )
            h3_count_after.append(h3_in_section)

        h2_count = len(h2_indices)
        sections_with_h3 = sum(1 for c in h3_count_after if c > 0)

        # 评分：H2 数量达标（≥3）且每个 H2 下有 H3 满分
        h2_ok = h2_count >= 3
        all_have_h3 = sections_with_h3 == h2_count and sections_with_h3 > 0

        ratio = 0.0
        if h2_ok:
            ratio += 0.5
        else:
            ratio += (h2_count / 3.0) * 0.5
        if all_have_h3:
            ratio += 0.5
        else:
            ratio += (sections_with_h3 / max(h2_count, 1)) * 0.5

        notes = []
        if h2_count < 3:
            notes.append(f"H2 数量 {h2_count} 偏少（建议 ≥3）")
        if sections_with_h3 < h2_count:
            notes.append(f"有 {h2_count - sections_with_h3} 个 H2 章节缺少 H3 子标题")
        note = "；".join(notes) + "。" if notes else ""
        return min(ratio, 1.0), note

    def _score_internal_links(self, internal_links: list) -> tuple[float, str]:
        """内链评分：≥3 个满分，按比例评分。"""
        count = len(internal_links)
        if count >= 3:
            return 1.0, ""
        ratio = count / 3.0
        return ratio, f"内链数量 {count} 偏少（建议 ≥3），可增加相关文章链接。"

    def _score_meta(self, meta: str, primary: str) -> tuple[float, str]:
        """meta description 评分：长度 120-155 字符且含主关键词满分。"""
        length = len(meta)
        has_kw = bool(primary) and (primary.lower() in meta.lower())

        # 长度评分：120-155 满分，过短/过长递减
        if 120 <= length <= 155:
            length_ratio = 1.0
        elif length < 120:
            length_ratio = length / 120.0 if length > 0 else 0.0
        else:
            # >155 递减，到 200 时为 0
            length_ratio = max(0.0, (200 - length) / 45.0)

        # 关键词占 40% 权重，长度占 60%
        kw_ratio = 1.0 if has_kw else 0.0
        ratio = length_ratio * 0.6 + kw_ratio * 0.4

        notes = []
        if length < 120:
            notes.append(f"meta 长度 {length} 偏短（建议 120-155 字符）")
        elif length > 155:
            notes.append(f"meta 长度 {length} 偏长（建议 120-155 字符）")
        if not has_kw and primary:
            notes.append(f"meta 未包含主关键词 '{primary}'")
        note = "；".join(notes) + "。" if notes else ""
        return ratio, note

    # ------------------------------------------------------------------
    # SubTask 1.4: 基于 claude-seo technical-seo-auditor 的上线前体检
    # 设计要点：
    # - 加载 technical-seo-auditor skill 获取维度定义（仅参考，评分基于规则）
    # - 规则体检：标题 / 元描述 / Heading 层级 / 内链 / 图片 alt / 速度预估
    # - 返回 score（0-100）与 block_publish（score < 70），作为发布门禁
    # ------------------------------------------------------------------
    def audit_with_skill(self, article_path: str) -> dict:
        """使用 claude-seo technical-seo-auditor 做上线前体检。

        基于 SKILL 描述的维度（标题 / 元描述 / Heading 层级 / 内链 / 图片 alt /
        速度预估）对文章做规则体检，输出评分与建议。

        Args:
            article_path: 待体检文章的 Markdown 文件路径。

        Returns:
            ``{"score": int, "suggestions": [str], "block_publish": bool}``
            block_publish = score < 70
        """
        from engine.llm_client import load_seo_skills

        # 读取文章内容（失败则按 0 分阻断发布处理）
        try:
            with open(article_path, "r", encoding="utf-8") as f:
                article_text = f.read()
        except OSError:
            return {
                "score": 0,
                "suggestions": [f"无法读取文章：{article_path}"],
                "block_publish": True,
            }

        # 加载 skill 获取维度定义（仅用于参考；prompt 含 {article_path} 占位符，
        # 可在 LLM 可用时格式化调用；此处评分基于规则，不依赖 LLM）
        try:
            skills = load_seo_skills()
            auditor = skills.get("technical-seo-auditor")
            if auditor:
                # 验证 prompt 模板可格式化（保留扩展点，不阻断流程）
                try:
                    auditor.get("prompt", "").format(article_path=article_path)
                except Exception:
                    pass
        except FileNotFoundError:
            pass

        suggestions: list[str] = []

        # 1. 标题：H1 唯一、长度 20-70 字符
        h1_matches = re.findall(r"^#\s+(.+)$", article_text, re.MULTILINE)
        if not h1_matches:
            suggestions.append("缺少 H1 标题，SEO 文章必须包含唯一 H1。")
        elif len(h1_matches) > 1:
            suggestions.append(f"检测到 {len(h1_matches)} 个 H1，应仅保留 1 个。")
        else:
            h1 = h1_matches[0].strip()
            if len(h1) < 20 or len(h1) > 70:
                suggestions.append(f"H1 长度 {len(h1)} 不在 20-70 字符推荐区间。")

        # 2. 元描述：frontmatter 中的 description 字段，长度 120-155 字符
        meta = _extract_frontmatter_field(article_text, "description")
        if not meta:
            suggestions.append("未找到 meta description（frontmatter 缺少 description 字段）。")
        elif len(meta) < 120 or len(meta) > 155:
            suggestions.append(
                f"meta description 长度 {len(meta)} 不在 120-155 字符区间。"
            )

        # 3. Heading 层级：H2≥3 且有 H3
        h2_count = len(re.findall(r"^##\s+\S", article_text, re.MULTILINE))
        h3_count = len(re.findall(r"^###\s+\S", article_text, re.MULTILINE))
        if h2_count < 3:
            suggestions.append(f"H2 数量 {h2_count} 偏少（建议 ≥3）。")
        if h3_count < 1:
            suggestions.append("未检测到 H3 子标题，建议增加层级深度。")

        # 4. 内链：≥3 个站内链接（[text](/path) 形式）
        internal_links = re.findall(r"\[[^\]]+\]\(/[^\)]+\)", article_text)
        if len(internal_links) < 3:
            suggestions.append(f"内链数量 {len(internal_links)} 偏少（建议 ≥3）。")

        # 5. 图片 alt：所有图片应有描述性 alt
        images = re.findall(r"!\[([^\]]*)\]\([^)]+\)", article_text)
        for alt in images:
            if not alt.strip():
                suggestions.append("存在缺失 alt 文本的图片，请补充描述性 alt。")
                break

        # 6. 加载速度预估：图片数量启发式
        img_count = len(images)
        if img_count > 10:
            suggestions.append(f"图片数量 {img_count} 较多，可能影响加载速度，建议优化。")

        # 评分：扣分制，满分 100
        score = 100
        if not h1_matches or len(h1_matches) > 1:
            score -= 20
        elif h1_matches and not (20 <= len(h1_matches[0].strip()) <= 70):
            score -= 10
        if not meta:
            score -= 15
        elif not (120 <= len(meta) <= 155):
            score -= 8
        if h2_count < 3:
            score -= 20
        if h3_count < 1:
            score -= 15
        if len(internal_links) < 3:
            score -= 15
        if images and any(not a.strip() for a in images):
            score -= 10
        if img_count > 10:
            score -= 20
        score = max(0, min(100, score))

        if not suggestions:
            suggestions.append("各项 SEO 维度均达标，可发布。")

        return {
            "score": score,
            "suggestions": suggestions,
            "block_publish": score < 70,
        }


def _has_chinese(text: str) -> bool:
    """判断文本是否含中文字符。"""
    return bool(text and re.search(r"[\u4e00-\u9fff]", text))


def _extract_frontmatter_field(text: str, field: str) -> str:
    """从 Markdown frontmatter 中提取指定字段值（简单行解析）。

    Args:
        text: Markdown 全文。
        field: 待提取的字段名（如 "description"）。

    Returns:
        字段值字符串；未找到 frontmatter 或字段时返回空字符串。
    """
    match = re.match(r"^---\s*\n(.*?)\n---", text, re.DOTALL)
    if not match:
        return ""
    for line in match.group(1).splitlines():
        stripped = line.strip()
        if stripped.startswith(f"{field}:"):
            value = line.split(":", 1)[1].strip()
            # 去除首尾引号
            if len(value) >= 2 and value[0] in ('"', "'") and value[-1] == value[0]:
                value = value[1:-1]
            return value
    return ""
