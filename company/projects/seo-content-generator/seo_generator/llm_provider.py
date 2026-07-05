"""LLM 抽象层：支持多后端生成

提供统一的 LLMProvider 接口，支持：
    - TemplateProvider：兜底实现，基于关键词和模板生成结构化内容，不依赖任何外部 API。
    - OpenAICompatibleProvider：可选实现，调用 OpenAI 兼容接口（后续接入真实 LLM 时使用）。

TemplateProvider 是核心：通过 system_prompt 中的任务标记路由到对应生成逻辑，
基于 templates.py 的规则与模板产出真实可用的 SEO 内容（关键词分析 / 大纲 / 正文）。

设计要点：
    - 模块解耦：各生成环节通过统一的 generate(system_prompt, user_message) 接口调用。
    - 优雅降级：真实 LLM 不可用时，TemplateProvider 兜底生成结构化内容。
    - user_message 采用半结构化文本，既能被真实 LLM 理解，也便于 TemplateProvider 解析。
"""
from __future__ import annotations

import json
import re
from abc import ABC, abstractmethod
from typing import Any

from . import templates as T


# =============================================================================
# 抽象基类
# =============================================================================

class LLMProvider(ABC):
    """LLM 提供方抽象基类。

    所有后端必须实现 generate(system_prompt, user_message) -> str。
    返回值约定：
        - 关键词分析 / 大纲任务：返回 JSON 字符串。
        - 内容写作任务：返回 Markdown 正文。
    """

    @abstractmethod
    def generate(self, system_prompt: str, user_message: str) -> str:
        """基于 system prompt 与 user message 生成文本。

        Args:
            system_prompt: 系统提示词，定义角色与任务（含任务标记）。
            user_message: 用户消息，携带输入数据（半结构化文本或 JSON）。

        Returns:
            生成的文本内容（JSON 字符串或 Markdown）。
        """
        raise NotImplementedError


# =============================================================================
# TemplateProvider：兜底实现（核心）
# =============================================================================

class TemplateProvider(LLMProvider):
    """基于模板与规则的兜底 LLM 实现。

    不调用任何外部 API，通过 system_prompt 中的任务标记路由到对应生成方法：
        - [TASK:KEYWORD_ANALYSIS] -> 关键词分析（前缀/后缀扩展 + 意图推断）
        - [TASK:OUTLINE_GENERATION] -> 大纲生成（H1 + H2 + H3 结构）
        - [TASK:CONTENT_WRITING] -> 正文生成（基于大纲与段落模板）

    生成的内容真实可用，满足 MVP 验收标准（≥1500 字、关键词密度 1-2%、H1/H2/H3 结构）。
    """

    def generate(self, system_prompt: str, user_message: str) -> str:
        """根据 system_prompt 中的任务标记路由到对应生成方法。

        Args:
            system_prompt: 含任务标记的系统提示词。
            user_message: 半结构化输入数据。

        Returns:
            JSON 字符串（关键词分析 / 大纲）或 Markdown 正文（内容写作）。

        Raises:
            ValueError: system_prompt 不含已知任务标记时抛出。
        """
        if T.TASK_KEYWORD in system_prompt:
            return self._generate_keyword_analysis(user_message)
        if T.TASK_OUTLINE in system_prompt:
            return self._generate_outline(user_message)
        if T.TASK_CONTENT in system_message_safe(system_prompt):
            return self._generate_content(user_message)
        # 未知任务：返回 user_message 的简单回显，保证不抛异常
        return user_message

    # --------------------------------------------------------------------------
    # 关键词分析
    # --------------------------------------------------------------------------

    def _generate_keyword_analysis(self, user_message: str) -> str:
        """基于种子关键词生成关键词分析 JSON。

        user_message 格式约定：
            "Seed keyword: <kw>\nLanguage: <lang>"
            或 JSON {"seed_keyword": ..., "language": ...}

        Returns:
            JSON 字符串：{primary_keyword, secondary_keywords, long_tail, search_intent}
        """
        seed, language = parse_seed_input(user_message)
        is_zh = language.lower().startswith("zh")

        if is_zh:
            prefixes = T.KEYWORD_PREFIXES_ZH
            suffixes = T.KEYWORD_SUFFIXES_ZH
            modifiers = T.SECONDARY_MODIFIERS_ZH
        else:
            prefixes = T.KEYWORD_PREFIXES_EN
            suffixes = T.KEYWORD_SUFFIXES_EN
            modifiers = T.SECONDARY_MODIFIERS_EN

        # 主关键词：规范化为小写（英文）
        primary = seed.strip()
        if not is_zh:
            primary = primary.lower()

        # 次要关键词：seed + 修饰词组合（去重，取 6 个）
        secondary: list[str] = []
        seen = {primary}
        for mod in modifiers:
            if len(secondary) >= 8:
                break
            candidate = f"{primary} {mod}" if not is_zh else f"{primary}{mod}"
            if candidate not in seen:
                seen.add(candidate)
                secondary.append(candidate)
        # 不足 5 个时用前缀补充
        for prefix in prefixes:
            if len(secondary) >= 6:
                break
            candidate = f"{prefix} {primary}" if not is_zh else f"{prefix}{primary}"
            if candidate not in seen:
                seen.add(candidate)
                secondary.append(candidate)

        # 长尾词：前缀 + seed + 后缀 组合，取 12 个
        long_tail: list[str] = []
        for prefix in prefixes:
            for suffix in suffixes:
                if len(long_tail) >= 12:
                    break
                candidate = f"{prefix} {primary} {suffix}" if not is_zh else f"{prefix}{primary}{suffix}"
                if candidate not in seen:
                    seen.add(candidate)
                    long_tail.append(candidate)
            if len(long_tail) >= 12:
                break
        # 不足时用 seed + 后缀补充
        for suffix in suffixes:
            if len(long_tail) >= 10:
                break
            candidate = f"{primary} {suffix}" if not is_zh else f"{primary}{suffix}"
            if candidate not in seen:
                seen.add(candidate)
                long_tail.append(candidate)

        # 搜索意图推断
        intent = infer_search_intent(primary)

        return json.dumps({
            "primary_keyword": primary,
            "secondary_keywords": secondary,
            "long_tail": long_tail,
            "search_intent": intent,
        }, ensure_ascii=False)

    # --------------------------------------------------------------------------
    # 大纲生成
    # --------------------------------------------------------------------------

    def _generate_outline(self, user_message: str) -> str:
        """基于关键词分析生成大纲 JSON。

        user_message 为关键词分析 JSON 字符串。

        Returns:
            JSON 字符串：{h1, sections: [{h2, h3_list}]}
        """
        analysis = safe_json_loads(user_message, default={})
        primary = analysis.get("primary_keyword", "SEO")
        is_zh = _is_chinese(primary) or _input_language_is_zh(user_message)

        template = T.OUTLINE_TEMPLATE_ZH if is_zh else T.OUTLINE_TEMPLATE_EN
        kw_cap = primary[:1].upper() + primary[1:] if primary else primary

        sections: list[dict[str, Any]] = []
        for h2_tpl, h3_list_tpl in template:
            h2 = h2_tpl.format(kw=primary, kw_cap=kw_cap)
            h3_list = [h3.format(kw=primary, kw_cap=kw_cap) for h3 in h3_list_tpl]
            sections.append({"h2": h2, "h3_list": h3_list})

        if is_zh:
            h1 = f"{primary}完全指南：2026 年实战策略与最佳实践"
        else:
            h1 = f"The Ultimate Guide to {kw_cap} in 2026: Strategies, Tips & Best Practices"

        return json.dumps({"h1": h1, "sections": sections}, ensure_ascii=False)

    # --------------------------------------------------------------------------
    # 正文生成
    # --------------------------------------------------------------------------

    def _generate_content(self, user_message: str) -> str:
        """基于大纲与关键词分析生成完整 Markdown 正文。

        user_message 为 JSON 字符串：{outline, keyword_analysis}

        Returns:
            Markdown 正文字符串（含 H1/H2/H3，≥1500 字）。
        """
        data = safe_json_loads(user_message, default={})
        outline = data.get("outline", {})
        analysis = data.get("keyword_analysis", {})
        primary = analysis.get("primary_keyword", "SEO")
        secondary = analysis.get("secondary_keywords", [])
        long_tail = analysis.get("long_tail", [])
        is_zh = _is_chinese(primary) or _input_language_is_zh(user_message)

        paragraphs_map = T.SECTION_PARAGRAPHS_ZH if is_zh else T.SECTION_PARAGRAPHS_EN
        link_templates = T.INTERNAL_LINK_TEMPLATES_ZH if is_zh else T.INTERNAL_LINK_TEMPLATES_EN

        h1 = outline.get("h1", primary)
        sections = outline.get("sections", [])

        kw_slug = re.sub(r"[^\w\-]+", "-", primary.lower()).strip("-") or "topic"

        lines: list[str] = []
        lines.append(f"# {h1}\n")

        # 关键词计数与字数追踪
        kw_count = {"count": 0}

        def render_with_kw(text: str) -> str:
            """渲染段落模板并统计关键词出现次数。"""
            rendered = text.replace("{kw}", primary)
            # 统计关键词出现次数（不区分大小写，英文按词边界）
            if is_zh:
                kw_count["count"] += rendered.count(primary)
            else:
                kw_count["count"] += len(re.findall(r"\b" + re.escape(primary) + r"\b", rendered, re.IGNORECASE))
            return rendered

        # 遍历大纲章节生成正文
        for section in sections:
            h2 = section.get("h2", "")
            h3_list = section.get("h3_list", [])
            lines.append(f"## {h2}\n")

            section_type = T.match_section_type(h2)
            paragraphs = paragraphs_map.get(section_type, paragraphs_map["what is"])

            # 渲染该章节的主题段落（全部使用，保证字数）
            for para_tpl in paragraphs:
                lines.append(render_with_kw(para_tpl))
                lines.append("")

            # 为每个 H3 生成简短引导段落（增加结构深度与字数）
            # 交替使用主关键词 / 代词，控制全文关键词密度在 1-2% 区间
            # 注：H3 段落使用通用引导句，不直接嵌入 H3 标题文本（避免语法不通）
            h3_para_variants_zh = [
                "这一小节聚焦于把{kw}融入日常工作流的核心要点。很多团队正是因为忽略了这一环节，导致整体效果大打折扣。接下来我们看具体如何落实，让投入真正产生价值。",
                "这里的关键在于建立可复用的执行节奏。许多团队失败，正是因为缺少这一步的标准化。下面我们看具体如何操作，让每一步都落到实处。",
                "深入理解这一点，能帮助你把{kw}的潜力充分发挥出来。多数成功团队都会在此投入额外精力，把它变成可衡量的日常动作。我们接着看具体的落地方式。",
            ]
            h3_para_variants_en = [
                "This subsection focuses on weaving {kw} into your daily workflow. Many teams stumble precisely because they overlook this step. Let's look at how to put it into practice so the work delivers real, measurable value.",
                "The key here is building a repeatable execution rhythm. Many teams miss results simply because they skip standardizing this step. Here is how to operationalize it so every action counts toward your goals.",
                "Understanding this point helps you unlock the full potential of your efforts. Most successful teams invest extra attention here, turning it into a measurable daily action. Let's examine the concrete steps that make it stick.",
            ]
            variants = h3_para_variants_zh if is_zh else h3_para_variants_en
            for h3_idx, h3 in enumerate(h3_list):
                lines.append(f"### {h3}\n")
                # 偶数索引使用含 {kw} 的变体，奇数索引使用代词变体
                variant_idx = h3_idx % len(variants)
                h3_para = variants[variant_idx]
                lines.append(render_with_kw(h3_para))
                lines.append("")

        # 内链建议（含 H3 子标题，保证层级完整）
        links_heading = "相关资源推荐" if is_zh else "Related Resources"
        links_h3 = f"深入阅读{primary}相关内容" if is_zh else f"Explore more {primary} resources"
        lines.append(f"## {links_heading}\n")
        lines.append(f"### {links_h3}\n")
        link_count = 0
        for anchor_tpl, url_tpl in link_templates:
            if link_count >= 5:
                break
            anchor = anchor_tpl.replace("{kw}", primary)
            url = url_tpl.replace("{kw_slug}", kw_slug)
            lines.append(f"- [{anchor}]({url})")
            link_count += 1
        lines.append("")

        body = "\n".join(lines)

        # 字数与密度校准：若字数不足 1500，补充扩展段落
        body = self._ensure_word_count(body, primary, is_zh, kw_count)

        # 关键词密度优化：保留标题中的关键词，稀释正文中超出的关键词为代词变体
        body = optimize_keyword_density(body, primary, is_zh, target_density=0.016)

        return body

    # --------------------------------------------------------------------------
    # 字数与密度校准
    # --------------------------------------------------------------------------

    def _ensure_word_count(self, body: str, primary: str, is_zh: bool,
                           kw_count: dict) -> str:
        """确保正文达到 1500 字以上，必要时补充扩展段落。

        Args:
            body: 当前 Markdown 正文。
            primary: 主关键词。
            is_zh: 是否中文。
            kw_count: 关键词计数容器（dict 用于可变引用）。

        Returns:
            校准后的正文（≥1500 字）。
        """
        target = 1500
        max_attempts = 6
        for _ in range(max_attempts):
            word_count = count_words(body, is_zh)
            if word_count >= target:
                break
            # 追加一个扩展段落（FAQ 风格），自然嵌入关键词
            if is_zh:
                extra = (
                    f"\n## 关于{primary}的常见问题\n\n"
                    f"### {primary}真的适合小团队吗？\n\n"
                    f"答案是肯定的。{primary}并不需要庞大预算，关键在于系统化执行。"
                    f"小团队反而更能快速迭代{primary}策略，因为决策链路短、试错成本低。"
                    f"只要选对指标，{primary}同样能为小团队带来可观回报。\n\n"
                    f"### 多久能看到{primary}的效果？\n\n"
                    f"通常 4 到 8 周可以观察到{primary}的初步成效，但完整收益需要持续优化。"
                    f"{primary}不是一夜暴富的捷径，而是一套复利系统：越早开始、越坚持，"
                    f"回报越显著。建议为{primary}设定 90 天评估周期。\n"
                )
            else:
                extra = (
                    f"\n## Frequently Asked Questions About {primary}\n\n"
                    f"### Is {primary} suitable for small teams?\n\n"
                    f"Absolutely. {primary} does not require a massive budget; the key is systematic "
                    f"execution. Small teams can often iterate on {primary} faster because they have "
                    f"shorter decision cycles and lower costs to experiment. Pick the right metrics, "
                    f"and {primary} can deliver meaningful returns for teams of any size.\n\n"
                    f"### How long until I see results from {primary}?\n\n"
                    f"Most teams notice initial signals from {primary} within 4 to 8 weeks, but the "
                    f"full payoff comes from sustained optimization. {primary} is not a get-rich-quick "
                    f"scheme; it is a compounding system. The earlier you start and the longer you "
                    f"persist, the more pronounced the returns. A 90-day review window is a good "
                    f"benchmark for evaluating {primary}.\n"
                )
            # 统计补充段落的关键词
            if is_zh:
                kw_count["count"] += extra.count(primary)
            else:
                kw_count["count"] += len(re.findall(r"\b" + re.escape(primary) + r"\b", extra, re.IGNORECASE))
            body += extra
        return body


# =============================================================================
# OpenAICompatibleProvider：可选实现（后续接入真实 LLM）
# =============================================================================

class OpenAICompatibleProvider(LLMProvider):
    """调用 OpenAI 兼容接口的 LLM 实现。

    后续接入真实 LLM（智谱 GLM-4 / OpenAI / Anthropic）时使用，
    需提供 base_url / api_key / model。当前 MVP 阶段默认不启用。
    """

    def __init__(self, base_url: str, api_key: str, model: str,
                 temperature: float = 0.7, max_tokens: int = 4000):
        self.base_url = base_url
        self.api_key = api_key
        self.model = model
        self.temperature = temperature
        self.max_tokens = max_tokens

    def generate(self, system_prompt: str, user_message: str) -> str:
        """调用 OpenAI 兼容 chat/completions 接口生成文本。

        延迟导入 openai，避免未安装时影响 TemplateProvider 正常工作。
        """
        from openai import OpenAI  # 延迟导入

        client = OpenAI(api_key=self.api_key, base_url=self.base_url)
        response = client.chat.completions.create(
            model=self.model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_message},
            ],
            temperature=self.temperature,
            max_tokens=self.max_tokens,
        )
        return response.choices[0].message.content or ""


# =============================================================================
# 工厂函数
# =============================================================================

def get_provider(name: str = "template", **kwargs: Any) -> LLMProvider:
    """根据名称返回对应的 LLMProvider 实例。

    Args:
        name: 提供方名称，'template' 返回 TemplateProvider（默认），
              'openai' 返回 OpenAICompatibleProvider（需传 base_url/api_key/model）。
        **kwargs: 传递给对应 provider 的构造参数。

    Returns:
        LLMProvider 实例。

    Raises:
        ValueError: 未知提供方名称时抛出。
    """
    name = (name or "template").strip().lower()
    if name == "template":
        return TemplateProvider()
    if name == "openai":
        return OpenAICompatibleProvider(
            base_url=kwargs.get("base_url", ""),
            api_key=kwargs.get("api_key", ""),
            model=kwargs.get("model", "gpt-4o-mini"),
            temperature=kwargs.get("temperature", 0.7),
            max_tokens=kwargs.get("max_tokens", 4000),
        )
    raise ValueError(f"未知 LLM 提供方：{name}（支持: template, openai）")


# =============================================================================
# 辅助函数
# =============================================================================

def system_message_safe(text: str) -> str:
    """返回系统提示词的安全副本（保留任务标记用于匹配）。"""
    return text or ""


def parse_seed_input(user_message: str) -> tuple[str, str]:
    """从 user_message 解析种子关键词与语言。

    支持两种格式：
        1. JSON：{"seed_keyword": "...", "language": "..."}
        2. 半结构化文本：
           "Seed keyword: email marketing\nLanguage: en"
           或 "种子关键词：邮件营销\n语言：zh"

    Returns:
        (seed_keyword, language) 二元组，language 默认 'en'。
    """
    if not user_message:
        return "SEO", "en"

    # 尝试 JSON 解析
    data = safe_json_loads(user_message, default=None)
    if isinstance(data, dict):
        seed = data.get("seed_keyword") or data.get("keyword") or data.get("primary_keyword") or "SEO"
        language = data.get("language") or data.get("lang") or "en"
        return str(seed), str(language)

    # 半结构化文本解析
    text = user_message
    seed = "SEO"
    language = "en"

    # 关键词
    seed_match = re.search(
        r"(?:seed\s*keyword|keyword|种子关键词|关键词)\s*[:：]\s*(.+)",
        text, re.IGNORECASE,
    )
    if seed_match:
        seed = seed_match.group(1).strip().split("\n")[0].strip()
    else:
        # 兜底：取第一行非空文本作为关键词
        first_line = next((ln.strip() for ln in text.splitlines() if ln.strip()), "SEO")
        seed = first_line

    # 语言
    lang_match = re.search(
        r"(?:language|lang|语言)\s*[:：]\s*(\w+)",
        text, re.IGNORECASE,
    )
    if lang_match:
        language = lang_match.group(1).strip().lower()

    return seed, language


def infer_search_intent(keyword: str) -> str:
    """根据关键词文本推断搜索意图。

    Args:
        keyword: 主关键词。

    Returns:
        意图字符串：informational / commercial / transactional / navigational。
    """
    text = keyword.lower()
    if any(sig in text for sig in T.INTENT_SIGNALS_TRANSACTIONAL):
        return "transactional"
    if any(sig in text for sig in T.INTENT_SIGNALS_COMMERCIAL):
        return "commercial"
    if any(sig in text for sig in T.INTENT_SIGNALS_INFORMATIONAL):
        return "informational"
    return "informational"


def safe_json_loads(text: str, default: Any = None) -> Any:
    """安全解析 JSON，失败时返回 default。"""
    if not text:
        return default
    try:
        # 尝试提取首个 JSON 对象（容忍前后多余文本）
        match = re.search(r"\{.*\}", text, re.DOTALL)
        if match:
            return json.loads(match.group(0))
        return json.loads(text)
    except (json.JSONDecodeError, ValueError):
        return default


def _is_chinese(text: str) -> bool:
    """判断文本是否包含中文字符。"""
    if not text:
        return False
    return bool(re.search(r"[\u4e00-\u9fff]", text))


def _input_language_is_zh(user_message: str) -> bool:
    """判断输入消息是否指示中文语言。"""
    if not user_message:
        return False
    # 检查 JSON 中的 language 字段
    data = safe_json_loads(user_message, default=None)
    if isinstance(data, dict):
        lang = str(data.get("language") or data.get("lang") or "").lower()
        if lang.startswith("zh"):
            return True
        if lang.startswith("en"):
            return False
    # 检查文本中的语言标记
    lang_match = re.search(r"(?:language|lang|语言)\s*[:：]\s*(\w+)", user_message, re.IGNORECASE)
    if lang_match and lang_match.group(1).lower().startswith("zh"):
        return True
    return False


def count_words(text: str, is_zh: bool = False) -> int:
    """统计字数。

    中文按字符数统计（去除空格与标点），英文按单词数统计。

    Args:
        text: 待统计文本。
        is_zh: 是否中文。

    Returns:
        字数 / 词数。
    """
    if is_zh:
        # 中文：统计中文字符 + 英文单词数
        chinese_chars = len(re.findall(r"[\u4e00-\u9fff]", text))
        english_words = len(re.findall(r"[a-zA-Z]+", text))
        return chinese_chars + english_words
    # 英文：按空白分词
    # 先去除 Markdown 标记符号，避免把 # ## 当作单词
    cleaned = re.sub(r"[#*\-\[\]\(\)>]", " ", text)
    words = [w for w in cleaned.split() if w and any(c.isalpha() for c in w)]
    return len(words)


# 代词变体池：用于稀释正文中过高的关键词密度（英文）
_PRONOUN_VARIANTS = [
    "this strategy",
    "this approach",
    "this method",
    "the framework",
    "this tactic",
    "this discipline",
    "the process",
]

# 关键词后跟这些名词时不替换（避免破坏 "email marketing strategy" 等复合词）
_KEYWORD_MODIFIER_NOUNS = (
    "strategy", "tactics", "process", "workflow", "efforts", "metrics",
    "mistakes", "systems", "journey", "approach", "guide", "tutorial",
    "examples", "tips", "tools", "software", "campaigns", "program",
    "results", "analytics", "resources", "checklist", "framework",
    "discipline", "best", "tactic", "plan",
)


def optimize_keyword_density(body: str, primary: str, is_zh: bool,
                             target_density: float = 0.014) -> str:
    """优化关键词密度：保留标题中的关键词，稀释正文中超出的关键词为代词变体。

    仅处理英文（中文不自动稀释，因其密度计算方式不同）。
    保留标题行（# 开头）与内链行（- [ 开头）中的关键词，仅替换正文段落。

    两阶段替换：
        1. 替换独立关键词为代词变体（this strategy / this approach ...）。
        2. 若仍超标，替换 "primary + 名词" 复合词为 "限定词 + 名词"
           （如 "email marketing strategy" → "your strategy"）。

    Args:
        body: Markdown 正文。
        primary: 主关键词。
        is_zh: 是否中文。
        target_density: 目标关键词密度（默认 1.4%，留余量避免触及 2% 上限）。

    Returns:
        优化后的 Markdown 正文。
    """
    if is_zh or not primary:
        return body

    words = count_words(body, is_zh=False)
    if words == 0:
        return body

    occurrences = len(re.findall(
        r"\b" + re.escape(primary) + r"\b", body, re.IGNORECASE,
    ))
    target_count = max(1, int(words * target_density))
    if occurrences <= target_count:
        return body

    to_replace = occurrences - target_count

    new_lines: list[str] = body.split("\n")

    # 阶段 1：替换独立关键词（后不跟修饰名词）为代词变体
    skip_after = r"(?!\s+(?:" + "|".join(_KEYWORD_MODIFIER_NOUNS) + r")\b)"
    standalone_pattern = re.compile(
        r"\b" + re.escape(primary) + r"\b" + skip_after, re.IGNORECASE,
    )

    replaced = 0

    def _make_standalone_replacer(line: str):
        def _replace(m: re.Match) -> str:
            nonlocal replaced
            if replaced >= to_replace:
                return m.group(0)
            prefix = line[: m.start()].rstrip()
            is_sentence_start = (
                not prefix or prefix.endswith((".", "!", "?", ":", ";"))
            )
            pronoun = _PRONOUN_VARIANTS[replaced % len(_PRONOUN_VARIANTS)]
            if is_sentence_start:
                pronoun = pronoun[:1].upper() + pronoun[1:]
            replaced += 1
            return pronoun
        return _replace

    for i, line in enumerate(new_lines):
        if replaced >= to_replace:
            break
        stripped = line.lstrip()
        if stripped.startswith("#") or stripped.startswith("- ["):
            continue
        new_lines[i] = standalone_pattern.sub(_make_standalone_replacer(line), line)

    # 阶段 2：替换复合词 "primary + 名词" 为 "限定词 + 名词"
    # 检测可选的前置限定词：若已存在则保留，避免产生 "your your efforts"
    if replaced < to_replace:
        determiners = ["the", "your", "this", "its", "our", "their"]
        # 匹配 (可选前置限定词) + primary + 名词
        compound_pattern = re.compile(
            r"(\b(?:the|your|this|its|our|their|a|an)\s+)?"
            + re.escape(primary) + r"\s+("
            + "|".join(_KEYWORD_MODIFIER_NOUNS) + r")\b",
            re.IGNORECASE,
        )

        def _replace_compound(m: re.Match) -> str:
            nonlocal replaced
            if replaced >= to_replace:
                return m.group(0)
            existing_det = m.group(1)  # 可能为 None
            noun = m.group(2)
            if existing_det:
                # 前面已有限定词，保留它（"your primary noun" → "your noun"）
                det = existing_det.strip()
                replaced += 1
                return f"{det} {noun}"
            # 无前置限定词：直接去掉关键词保留名词（"key primary metrics" → "key metrics"）
            replaced += 1
            return noun

        for i, line in enumerate(new_lines):
            if replaced >= to_replace:
                break
            stripped = line.lstrip()
            if stripped.startswith("#") or stripped.startswith("- ["):
                continue
            new_lines[i] = compound_pattern.sub(_replace_compound, line)

    return "\n".join(new_lines)


