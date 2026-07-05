"""提示词模板与兜底内容模板

存放所有 LLM system prompt 以及 TemplateProvider 所需的结构化内容模板。
TemplateProvider 基于本模块的规则与模板生成真实可用的 SEO 内容，不依赖任何外部 API。

设计要点：
    - system_prompt 中嵌入任务标记 [TASK:XXX]，TemplateProvider 据此路由生成逻辑。
    - 关键词扩展使用前缀 / 后缀组合规则，覆盖 informational / transactional / commercial 意图。
    - 段落模板包含主题句 + 支撑句 + 关键词自然嵌入，保证内容质量与可读性。
"""
from __future__ import annotations

# =============================================================================
# 任务标记常量（嵌入 system_prompt，供 TemplateProvider 路由识别）
# =============================================================================
TASK_KEYWORD = "[TASK:KEYWORD_ANALYSIS]"
TASK_OUTLINE = "[TASK:OUTLINE_GENERATION]"
TASK_CONTENT = "[TASK:CONTENT_WRITING]"

# =============================================================================
# System Prompts（同时供真实 LLM 与 TemplateProvider 使用）
# =============================================================================

SYSTEM_PROMPT_KEYWORD = f"""You are a senior SEO keyword analyst. {TASK_KEYWORD}
Given a seed keyword and target language, produce a structured keyword analysis.
Return ONLY valid JSON with keys:
- primary_keyword: the refined main keyword
- secondary_keywords: 5-8 closely related keywords
- long_tail: 10-15 long-tail keyword variations
- search_intent: one of informational / commercial / transactional / navigational
Respond in the same language as the seed keyword."""

SYSTEM_PROMPT_OUTLINE = f"""You are an expert SEO content strategist. {TASK_OUTLINE}
Given a keyword analysis, produce a blog post outline.
Return ONLY valid JSON with keys:
- h1: the main article title (must contain the primary keyword)
- sections: list of 5-7 objects each with:
    - h2: section heading (contain keyword or related term where natural)
    - h3_list: list of 2-3 subheadings
Respond in the requested language."""

SYSTEM_PROMPT_CONTENT = f"""You are a professional SEO copywriter. {TASK_CONTENT}
Given an outline and keyword analysis, write the full article body in Markdown.
Requirements:
- Use # for H1, ## for H2, ### for H3 exactly as in the outline.
- Each H2 section 200-350 words; total >= 1500 words.
- Primary keyword density 1-2% (natural distribution, no stuffing).
- Include 3-5 internal link suggestions as Markdown: [anchor text](/related-path).
Return ONLY the Markdown body, no commentary."""

# =============================================================================
# 关键词扩展规则数据
# =============================================================================

# 前缀：覆盖 how-to / listicle / guide / beginner 等搜索意图
KEYWORD_PREFIXES_EN = [
    "how to",
    "best",
    "top",
    "ultimate guide to",
    "beginner's guide to",
    "complete guide to",
    "advanced",
    "simple",
    "proven",
    "essential",
]

# 后缀：覆盖时效性 / 工具 / 误区 / 示例等长尾意图
KEYWORD_SUFFIXES_EN = [
    "for beginners",
    "in 2026",
    "tips",
    "strategies",
    "mistakes to avoid",
    "examples",
    "tools",
    "software",
    "best practices",
    "step by step",
    "for small business",
    "that actually work",
    "checklist",
    "templates",
    "vs alternatives",
]

# 次要关键词修饰词（用于生成相关词）
SECONDARY_MODIFIERS_EN = [
    "strategy",
    "guide",
    "tutorial",
    "examples",
    "tips",
    "tools",
    "best practices",
    "checklist",
    "framework",
    "metrics",
    "automation",
    "optimization",
]

# 中文关键词扩展规则
KEYWORD_PREFIXES_ZH = ["如何", "最好的", "新手", "完整", "高效", "实用"]
KEYWORD_SUFFIXES_ZH = ["入门", "技巧", "工具", "误区", "案例", "步骤", "最佳实践", "指南", "教程", "2026"]
SECONDARY_MODIFIERS_ZH = ["策略", "指南", "教程", "案例", "技巧", "工具", "最佳实践", "方法", "指标", "优化"]

# 搜索意图推断关键词
INTENT_SIGNALS_INFORMATIONAL = ["how to", "what is", "guide", "tutorial", "examples", "如何", "什么是"]
INTENT_SIGNALS_COMMERCIAL = ["best", "top", "vs", "review", "comparison", "最好的", "对比"]
INTENT_SIGNALS_TRANSACTIONAL = ["buy", "price", "deal", "discount", "pricing", "购买", "价格"]

# =============================================================================
# 大纲模板（英文 / 中文）
# =============================================================================

# 大纲章节模板：每项 (h2 模板, h3 列表模板)，{kw} 占位符替换为主关键词或相关词
OUTLINE_TEMPLATE_EN = [
    ("Introduction to {kw}", ["What is {kw}?", "Why {kw} matters in 2026"]),
    ("What Is {kw}? A Clear Definition", ["Core components of {kw}", "How {kw} works"]),
    ("Key Benefits of {kw}", ["Save time with {kw}", "Grow revenue using {kw}", "Reduce costs through {kw}"]),
    ("How to {kw_cap}: Step-by-Step Guide", ["Step 1: Plan your {kw} strategy", "Step 2: Execute {kw} tactics", "Step 3: Measure {kw} results"]),
    ("Best Practices for {kw}", ["Align {kw} with business goals", "Use data to guide {kw}"]),
    ("Common {kw} Mistakes to Avoid", ["Ignoring {kw} analytics", "Overcomplicating your {kw} workflow"]),
    ("Conclusion: Start {kw} Today", ["Key takeaways on {kw}", "Next steps for {kw} success"]),
]

OUTLINE_TEMPLATE_ZH = [
    ("{kw}简介", ["什么是{kw}", "为什么{kw}在2026年很重要"]),
    ("什么是{kw}？清晰定义", ["{kw}的核心要素", "{kw}的工作原理"]),
    ("{kw}的核心优势", ["用{kw}节省时间", "用{kw}提升收入", "通过{kw}降低成本"]),
    ("如何做{kw}：分步指南", ["第一步：制定{kw}策略", "第二步：执行{kw}战术", "第三步：衡量{kw}效果"]),
    ("{kw}的最佳实践", ["让{kw}对齐业务目标", "用数据指导{kw}"]),
    ("{kw}常见误区与规避", ["忽视{kw}数据分析", "把{kw}流程搞得太复杂"]),
    ("总结：立即开始{kw}", ["{kw}核心要点", "{kw}后续行动建议"]),
]

# =============================================================================
# 段落内容模板（英文）
# 每个模板对应一个大纲章节，含主题句 + 支撑句，{kw} 自然嵌入
# =============================================================================

# 章节段落模板：键为章节类型（h2 关键词片段），值为段落列表（每段 3-5 句）
# 注：每段 {kw} 出现 1-2 次，其余用代词（it / this strategy / the approach）替代，
# 保证全文关键词密度落在 1-2% 区间，避免过度优化。
SECTION_PARAGRAPHS_EN: dict[str, list[str]] = {
    "introduction": [
        "In today's competitive digital landscape, {kw} has become an essential strategy for businesses looking to grow their online presence. Whether you run a small blog or manage marketing for a large brand, understanding this approach can mean the difference between thriving and merely surviving. This guide breaks down everything you need to know about {kw} in 2026, from foundational concepts to advanced tactics you can apply today. By the end, you will have a clear, actionable roadmap for making it work for your specific goals.",
        "Many marketers struggle with {kw} because they treat it as a one-time task rather than an ongoing process. The truth is, effective execution requires consistent effort, measurement, and refinement. Throughout this article, you will discover practical frameworks, real examples, and proven best practices that turn a vague concept into a reliable growth engine. Let's start by exploring what this strategy really means and why it matters now more than ever.",
    ],
    "what is": [
        "At its core, this method refers to the systematic approach of optimizing and leveraging specific tactics to achieve measurable business outcomes. Unlike fragmented efforts that produce inconsistent results, it brings structure and repeatability to your workflow. When implemented correctly, {kw} aligns your resources with your highest-value objectives, ensuring every action contributes to a larger strategy.",
        "The mechanics rely on a few core components: clear goal definition, data-driven decision making, and continuous iteration. Each component reinforces the others, creating a feedback loop that improves performance over time. For example, when you track the right metrics within your {kw} process, you can quickly identify what works, double down on winning tactics, and cut what wastes budget. This is why a structured approach consistently outperforms ad-hoc methods in both efficiency and ROI.",
    ],
    "benefits": [
        "One of the most compelling reasons to invest in {kw} is the time it saves across your team. By standardizing how you approach this work, you eliminate the guesswork and redundant effort that slows projects down. Teams that adopt a structured workflow report completing campaigns faster and with fewer revisions, freeing them to focus on creative and strategic tasks.",
        "Beyond efficiency, this strategy has a direct impact on revenue. When your {kw} efforts target the right audience with the right message, conversion rates climb and customer acquisition costs drop. Many businesses find that refining their approach delivers compounding returns: early wins fund further optimization, creating a growth flywheel that scales with your ambitions.",
        "Cost reduction is another major benefit. By identifying and removing inefficiencies, {kw} helps you spend less on underperforming channels and more on what actually drives results. Over a full quarter, the savings from a well-run program often exceed the cost of implementation, making it one of the highest-ROI investments a modern marketing team can make.",
    ],
    "how to": [
        "Getting started with {kw} is easier than most people assume. The first step is to plan your strategy by defining clear, measurable goals and mapping them to your overall business objectives. Without this foundation, even the most sophisticated tactics will lack direction. Write down what success looks like, choose the metrics that matter, and commit to reviewing them weekly.",
        "With your plan in place, the next step is to execute your {kw} tactics. Break your strategy into small, testable actions rather than attempting a massive rollout all at once. This iterative approach lets you learn quickly, adapt to what the data tells you, and avoid costly mistakes. Document each step so your team can repeat what works and refine what does not.",
        "The final step is to measure your results and optimize continuously. Set up dashboards that track your key {kw} metrics in real time, and schedule regular reviews to interpret the data. Remember that this work is never truly finished: markets shift, audiences evolve, and new tools emerge. Treat measurement as the starting point for your next cycle of improvement, not the end of the process.",
    ],
    "best practices": [
        "To get the most from {kw}, always align your efforts with broader business goals. It is easy to get lost in tactical details and lose sight of why you started in the first place. Before launching any new initiative, ask how it supports revenue, retention, or brand growth. This discipline keeps your work focused on outcomes that actually move the needle.",
        "Another best practice is to let data guide every decision you make. Intuition has its place, but the most successful teams treat {kw} as an empirical discipline: hypothesize, test, measure, and repeat. When you build this habit into your workflow, you stop guessing and start optimizing based on what your audience actually responds to.",
    ],
    "mistakes": [
        "One of the most common {kw} mistakes is ignoring analytics altogether. Without data, you are flying blind and relying on assumptions that may be completely wrong. Teams that skip measurement often repeat the same errors for months, wasting budget and missing opportunities that a simple dashboard would have revealed.",
        "Another frequent pitfall is overcomplicating your workflow. Adding too many tools, steps, or stakeholders creates friction that slows execution and dilutes accountability. The best {kw} systems are deliberately simple: a clear goal, a lean process, and a tight feedback loop. If your setup requires a flowchart to understand, it is time to simplify.",
    ],
    "conclusion": [
        "Throughout this guide, we have explored what {kw} is, why it matters, and how to put it into practice. The key takeaways are clear: this work rewards structure, demands measurement, and compounds over time when applied consistently. There is no shortcut, but there is a proven path, and you now have the blueprint to follow it.",
        "Your next step is to take action. Pick one {kw} tactic from this guide, implement it this week, and measure the result. Momentum builds quickly once you start, and each small win lays the groundwork for larger gains. Start your journey today, and you will be surprised how far you can go in just a few months.",
    ],
}

# 中文段落模板（每段 {kw} 出现 1-2 次，其余用代词替代，控制关键词密度）
SECTION_PARAGRAPHS_ZH: dict[str, list[str]] = {
    "introduction": [
        "在当今竞争激烈的数字环境中，{kw}已成为企业提升线上影响力的核心策略。无论你是经营个人博客，还是负责大型品牌的市场工作，掌握这套方法往往决定了你是蓬勃发展还是勉强维持。本指南将系统讲解2026年的方方面面，从基础概念到可立即落地的高级战术。读完本文，你将拥有一套清晰、可执行的路线图。",
        "许多营销者在{kw}上遇到困难，是因为把它当成一次性任务，而非持续过程。事实上，有效的执行需要持续投入、衡量与优化。本文将提供实用框架、真实案例与经过验证的最佳实践，让模糊的概念变成可靠的增长引擎。我们先从它的本质讲起。",
    ],
    "what is": [
        "从本质上讲，这套方法是指通过系统化方式优化特定战术，以实现可衡量的业务成果。与零散的努力不同，它为你的工作流程带来结构与可重复性。正确实施时，{kw}能让资源与高价值目标对齐，确保每个动作都服务于更大的战略。",
        "其运作依赖几个核心要素：清晰的目标定义、数据驱动的决策以及持续迭代。这些要素相互强化，形成不断提升性能的反馈循环。例如，当你在{kw}过程中追踪正确的指标，就能快速识别有效做法，加大投入赢取战术，并削减浪费预算的部分。这正是结构化方法在效率与ROI上始终优于临时方案的原因。",
    ],
    "benefits": [
        "投资{kw}最 compelling 的理由之一，是它能为团队节省大量时间。通过标准化执行方式，你消除了拖慢项目的猜测与重复劳动。采用结构化流程的团队反馈，他们完成活动更快、返工更少，从而能专注于创意与战略工作。",
        "除了效率，这套策略对收入有直接影响。当你的{kw}动作用正确信息触达正确受众时，转化率上升、获客成本下降。许多企业发现，持续优化能带来复利回报：早期收益资助进一步迭代，形成与雄心同步增长的增长飞轮。",
        "降低成本是另一大优势。通过识别并消除低效环节，{kw}帮助你减少对表现不佳渠道的投入，把资源集中在真正出效果的地方。整个季度下来，运行良好的项目节省的费用往往超过实施成本，使其成为现代营销团队ROI最高的投资之一。",
    ],
    "how to": [
        "开始{kw}比大多数人想象的要简单。第一步是制定策略：定义清晰、可衡量的目标，并将其映射到整体业务目标上。没有这个基础，再精巧的战术也会失去方向。写下成功长什么样，选择关键指标，并承诺每周复盘。",
        "计划就绪后，下一步是执行{kw}战术。把战略拆解为小而可测试的动作，而不是一次性大规模铺开。这种迭代方式让你快速学习、根据数据调整，并避免昂贵错误。记录每一步，让团队能复用有效做法、改进不足之处。",
        "最后一步是衡量结果并持续优化。搭建实时追踪关键指标的看板，并定期复盘数据。记住，{kw}永远没有终点：市场在变、受众在演进、新工具不断涌现。把衡量视为下一轮改进的起点，而不是流程的终点。",
    ],
    "best practices": [
        "要让{kw}发挥最大价值，始终把努力与更广泛的业务目标对齐。很容易陷入战术细节，而忘了当初为何开始。在启动任何新举措前，先问它如何支撑收入、留存或品牌增长。这种纪律能让你的工作聚焦于真正能撬动结果的方向。",
        "另一条最佳实践是：让数据指导每一个决策。直觉有其位置，但最成功的团队把{kw}当作实证学科：假设、测试、衡量、重复。当这种习惯融入流程，你便不再猜测，而是基于受众真实反应进行优化。",
    ],
    "mistakes": [
        "{kw}最常见的错误之一是完全忽视数据分析。没有数据，你就像盲飞，依赖的假设可能完全错误。跳过衡量的团队常常重复同样的错误长达数月，浪费预算，错过简单看板就能揭示的机会。",
        "另一个常见陷阱是把流程搞得过于复杂。堆砌过多工具、步骤或干系人会产生摩擦，拖慢执行并稀释责任。最好的{kw}系统刻意保持简单：清晰的目标、精简的流程、紧密的反馈循环。如果你的设置需要流程图才能看懂，那就是时候简化了。",
    ],
    "conclusion": [
        "在本指南中，我们系统讲解了{kw}是什么、为何重要，以及如何落地。核心要点很清晰：这套方法奖励结构化、依赖衡量，并在持续应用时产生复利效应。没有捷径，但有被验证的路径，而你现在就拥有这份蓝图。",
        "你的下一步是行动。从本文中挑选一个{kw}战术，本周就实施，并衡量结果。一旦开始，动量会迅速累积，每个小胜都为更大收获奠定基础。今天就开始你的旅程，几个月后你会惊讶于自己走得多远。",
    ],
}

# =============================================================================
# 内链锚文本模板
# =============================================================================

INTERNAL_LINK_TEMPLATES_EN = [
    ("{kw} strategy guide", "/blog/{kw_slug}-strategy"),
    ("best {kw} tools", "/tools/{kw_slug}"),
    ("{kw} case studies", "/case-studies/{kw_slug}"),
    ("{kw} templates", "/templates/{kw_slug}"),
    ("advanced {kw} tactics", "/blog/advanced-{kw_slug}"),
    ("{kw} checklist", "/resources/{kw_slug}-checklist"),
    ("{kw} for beginners", "/guides/{kw_slug}-beginners"),
]

INTERNAL_LINK_TEMPLATES_ZH = [
    ("{kw}策略指南", "/blog/{kw_slug}-strategy"),
    ("最好的{kw}工具", "/tools/{kw_slug}"),
    ("{kw}案例分析", "/case-studies/{kw_slug}"),
    ("{kw}模板下载", "/templates/{kw_slug}"),
    ("高级{kw}战术", "/blog/advanced-{kw_slug}"),
    ("{kw}检查清单", "/resources/{kw_slug}-checklist"),
]

# =============================================================================
# 章节类型识别关键词（用于将 h2 映射到段落模板）
# =============================================================================

SECTION_TYPE_SIGNALS = [
    ("introduction", ["introduction", "简介"]),
    ("what is", ["what is", "definition", "什么是"]),
    ("benefits", ["benefit", "advantage", "优势", "好处"]),
    ("how to", ["how to", "step", "如何", "分步"]),
    ("best practices", ["best practice", "最佳实践"]),
    ("mistakes", ["mistake", "avoid", "误区", "避免"]),
    ("conclusion", ["conclusion", "总结", "结论"]),
]


def match_section_type(h2: str) -> str:
    """根据 H2 标题文本匹配章节类型，返回段落模板键。

    Args:
        h2: H2 标题文本。

    Returns:
        章节类型字符串（如 'introduction' / 'what is' / 'benefits'），
        未匹配时返回 'what is' 作为默认主题段落。
    """
    text = h2.lower()
    for section_type, signals in SECTION_TYPE_SIGNALS:
        if any(signal in text for signal in signals):
            return section_type
    return "what is"
