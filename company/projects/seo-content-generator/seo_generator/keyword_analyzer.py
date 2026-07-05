"""关键词分析模块

基于 LLMProvider 生成关键词分析结果，失败时走本地规则兜底。
输出结构：{primary_keyword, secondary_keywords[5-8], long_tail[10-15], search_intent}
"""
from __future__ import annotations

from typing import Any

from .llm_provider import LLMProvider, TemplateProvider, get_provider, safe_json_loads
from .templates import SYSTEM_PROMPT_KEYWORD


class KeywordAnalyzer:
    """关键词分析器：扩展种子关键词，输出主词 / 次要词 / 长尾词 / 搜索意图。

    优先调用 provider 生成结构化结果；解析失败时回退到 TemplateProvider 兜底。
    """

    def __init__(self, provider: LLMProvider = None):
        self.provider = provider or get_provider("template")

    def analyze(self, seed_keyword: str, language: str = "en") -> dict:
        """分析种子关键词，返回关键词分析字典。

        Args:
            seed_keyword: 种子关键词，例如 "email marketing"。
            language: 目标语言，'en' 或 'zh'。

        Returns:
            dict：{primary_keyword, secondary_keywords, long_tail, search_intent}
        """
        user_message = (
            f"Seed keyword: {seed_keyword}\n"
            f"Language: {language}"
        )

        try:
            raw = self.provider.generate(SYSTEM_PROMPT_KEYWORD, user_message)
            result = self._parse(raw, seed_keyword, language)
            if self._validate(result):
                return result
        except Exception:
            pass

        # 兜底：直接用 TemplateProvider 重新生成
        fallback = TemplateProvider()
        raw = fallback.generate(SYSTEM_PROMPT_KEYWORD, user_message)
        return self._parse(raw, seed_keyword, language)

    def _parse(self, raw: str, seed_keyword: str, language: str) -> dict:
        """解析 provider 输出为关键词分析字典。"""
        data = safe_json_loads(raw, default=None)
        if isinstance(data, dict) and self._validate(data):
            return {
                "primary_keyword": data.get("primary_keyword", seed_keyword),
                "secondary_keywords": list(data.get("secondary_keywords", [])),
                "long_tail": list(data.get("long_tail", [])),
                "search_intent": data.get("search_intent", "informational"),
            }
        # 解析失败：构造最小可用结果
        primary = seed_keyword.strip().lower() if language.lower().startswith("en") else seed_keyword.strip()
        return {
            "primary_keyword": primary,
            "secondary_keywords": [],
            "long_tail": [],
            "search_intent": "informational",
        }

    @staticmethod
    def _validate(result: Any) -> bool:
        """校验关键词分析结果是否满足基本结构要求。"""
        if not isinstance(result, dict):
            return False
        if not result.get("primary_keyword"):
            return False
        if not isinstance(result.get("secondary_keywords"), list):
            return False
        if not isinstance(result.get("long_tail"), list):
            return False
        return True
