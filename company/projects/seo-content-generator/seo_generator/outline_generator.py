"""大纲生成模块

基于关键词分析生成文章大纲，输出 H1 + 多个 H2 章节（每节含 H3 子标题）。
失败时走本地规则兜底。
"""
from __future__ import annotations

from typing import Any

from .llm_provider import LLMProvider, TemplateProvider, get_provider, safe_json_loads
from .templates import SYSTEM_PROMPT_OUTLINE


class OutlineGenerator:
    """大纲生成器：基于关键词分析产出 H1/H2/H3 结构。"""

    def __init__(self, provider: LLMProvider = None):
        self.provider = provider or get_provider("template")

    def generate(self, keyword_analysis: dict, language: str = "en") -> dict:
        """基于关键词分析生成大纲。

        Args:
            keyword_analysis: KeywordAnalyzer.analyze() 的输出。
            language: 目标语言，'en' 或 'zh'。

        Returns:
            dict：{h1, sections: [{h2, h3_list: []}]}
        """
        user_message = (
            f"Keyword analysis:\n"
            f"{_to_json(keyword_analysis)}\n"
            f"Language: {language}"
        )

        try:
            raw = self.provider.generate(SYSTEM_PROMPT_OUTLINE, user_message)
            result = self._parse(raw, keyword_analysis, language)
            if self._validate(result):
                return result
        except Exception:
            pass

        # 兜底：直接用 TemplateProvider 重新生成
        fallback = TemplateProvider()
        raw = fallback.generate(SYSTEM_PROMPT_OUTLINE, user_message)
        return self._parse(raw, keyword_analysis, language)

    def _parse(self, raw: str, keyword_analysis: dict, language: str) -> dict:
        """解析 provider 输出为大纲字典。"""
        data = safe_json_loads(raw, default=None)
        if isinstance(data, dict) and self._validate(data):
            primary = keyword_analysis.get("primary_keyword", "SEO")
            # 确保 H1 含主关键词
            h1 = data.get("h1", "") or primary
            if primary.lower() not in h1.lower():
                h1 = f"{h1}: {primary}" if h1 else str(primary)
            sections = []
            for sec in data.get("sections", []):
                if isinstance(sec, dict):
                    sections.append({
                        "h2": sec.get("h2", ""),
                        "h3_list": list(sec.get("h3_list", [])),
                    })
            return {"h1": h1, "sections": sections}

        # 解析失败：构造最小可用结果
        primary = keyword_analysis.get("primary_keyword", "SEO")
        return {"h1": primary, "sections": []}

    @staticmethod
    def _validate(result: Any) -> bool:
        """校验大纲是否满足基本结构要求。"""
        if not isinstance(result, dict):
            return False
        if not result.get("h1"):
            return False
        sections = result.get("sections")
        if not isinstance(sections, list) or len(sections) < 3:
            return False
        return True


def _to_json(data: dict) -> str:
    """安全序列化字典为 JSON 字符串。"""
    import json
    try:
        return json.dumps(data, ensure_ascii=False)
    except (TypeError, ValueError):
        return str(data)
