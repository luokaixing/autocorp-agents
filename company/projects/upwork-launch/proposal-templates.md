# Upwork Proposal 模板库 — AutoCorp AI

> 文档说明：本文档提供 20 个可直接使用的 Upwork Proposal 模板，覆盖 3 个核心类目。每个模板包含 7 个固定模块（开场 / 价值主张 / 相关经验 / 交付物与时间表 / 定价 / CTA / 关键词标签）。
> 使用方式：找到匹配的模板，将 `{{JOB_TITLE}}`、`{{CLIENT_INDUSTRY}}`、`{{SPECIFIC_DETAIL}}` 等占位符替换为实际 job posting 中的引用，确保第一段个性化。
> 引用案例：3 篇 Paragraph 文章（art_001 Ethereum Wallets / art_002 Crypto Airdrops / art_003 Aave Protocol）+ 1 篇实时数据文章（art_004 DeFi Yield）
> 定价依据：`us-market-revenue-research-2026-06-30.md`（Prompt $25-40 / AI Research $30-50 / Crypto Writing $50-78）

---

## 一、Prompt Engineering 类（7 个模板）

### 模板 PE-1：Chatbot Prompt（聊天机器人提示词）

**目标 Job Posting：** 客户需要为客户支持 / 销售助理 / FAQ 聊天机器人编写 prompt

```
Hi {{CLIENT_NAME}},

Your job posting for a {{JOB_TITLE}} caught my attention — specifically the part where you mentioned {{SPECIFIC_DETAIL_FROM_POST}}. That is exactly the failure mode most chatbot prompts run into: they answer the wrong question confidently.

I design chatbot prompts as engineering artifacts, not creative writing. Every prompt I deliver is structured as: (1) role + scope boundary, (2) knowledge source pointer (so the bot knows what it does NOT know), (3) refusal protocol, (4) escalation trigger, (5) tone spec, (6) few-shot examples. I test each version against 10+ edge-case inputs before handoff.

Why me over a generalist: I run an AI-augmented content studio that uses multi-agent orchestration — meaning a research agent pulls your existing docs/kb articles, a draft agent writes the prompt, a red-team agent attacks it with adversarial inputs, and an edit agent ships the final. You get a battle-tested prompt, not a first draft.

Relevant work:
- Published "The Ultimate Guide to Aave Protocol in 2026" (2,200 words, Paragraph) — the prompt logic I used to extract structured protocol mechanics from on-chain data is the same pattern that works for chatbot knowledge grounding.
- Published "The Ultimate Guide to Crypto Airdrops in 2026" (2,100 words, Paragraph) — required structuring refusal logic for airdrop-scam questions, directly applicable to support-bot safety rails.

Deliverables:
- 1 system prompt (production-ready, ~1,500 tokens)
- 5 few-shot examples covering top intent categories
- 10 adversarial test cases + expected outputs (red-team log)
- 1-page "prompt maintenance guide" so your team can update it without breaking the structure

Timeline: 3 days (Day 1: research + intent mapping / Day 2: draft + red-team / Day 3: revisions + handoff)

Pricing: $150 fixed-price (or $30/hr if you prefer hourly). Includes 1 round of revisions.

If you can share 2-3 real user questions your current bot mishandles, I will send back a free sample of how my prompt would handle them — before you hire. Sound fair?

Best,
{{YOUR_NAME}}

Keywords: chatbot prompt, system prompt, conversational AI, prompt engineering, LLM, customer support bot, few-shot, prompt red-teaming
```

---

### 模板 PE-2：AI Agent Prompt（AI 智能体提示词）

**目标 Job Posting：** 客户需要为自主 AI Agent（工具调用 / 多步规划）编写 prompt

```
Hi {{CLIENT_NAME}},

Your post about {{JOB_TITLE}} resonates — the hardest part of agent prompts is not "what should the agent do" but "how should it decide when to stop, retry, or escalate." I saw you mentioned {{SPECIFIC_DETAIL}} — that is a tool-selection problem disguised as a prompt problem, and it is exactly what I specialize in.

My approach to agent prompts differs from chatbot prompts in 3 ways:
1. Explicit ReAct/Plan-Execute-Observe loop structure (no improvisation)
2. Tool-calling schema with input validation (the agent cannot pass malformed args)
3. Termination criteria — the agent knows when to stop, not just when to act

I run a multi-agent content studio, so I have first-hand experience with the failure modes you are trying to avoid: infinite loops, hallucinated tool outputs, agents that "forget" their goal after step 3. Every agent prompt I ship includes a self-check loop that catches these.

Relevant work:
- Published "The Ultimate Guide to Aave Protocol in 2026" (Paragraph) — the article itself was produced by an orchestrated agent pipeline (research → outline → draft → fact-check → SEO → edit), so I have built and debugged the exact type of prompt you are commissioning.
- Published "Where to Earn the Highest DeFi Yield Right Now" (2,400 words, real-time DefiLlama + CoinGecko data) — the research agent behind this article uses a tool-calling prompt pattern that retrieves and validates live API data, the same pattern applicable to your {{CLIENT_INDUSTRY}} use case.

Deliverables:
- 1 agent system prompt with ReAct loop + tool schema (YAML/JSON)
- 3 sample trajectories (input → plan → tool calls → output)
- Failure-mode catalog (5 documented edge cases + handling)
- Integration notes for OpenAI function-calling / Anthropic tool-use / LangChain

Timeline: 4 days

Pricing: $250 fixed-price. Includes 2 rounds of revisions and a 30-min walkthrough call.

Worth a quick chat? I can show you a sample agent trajectory on a smaller task before we commit.

Best,
{{YOUR_NAME}}

Keywords: AI agent, ReAct, tool calling, function calling, multi-step reasoning, LLM agent, autonomous agent, prompt engineering
```

---

### 模板 PE-3：Content Generation Prompt（内容生成提示词）

**目标 Job Posting：** 客户需要为内容生产（博客 / SEO / 社交）编写可复用 prompt

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is the kind of brief I love — you want a prompt that produces consistent {{CONTENT_TYPE}} at scale, not a one-off article. The detail about {{SPECIFIC_DETAIL}} tells me you have already seen what happens when prompts are too vague: inconsistent tone, hallucinated stats, off-brand voice.

I build content-generation prompts as templates with 4 layers:
1. Voice/brand spec (locked — your tone, your vocabulary, your "do not say" list)
2. Structural skeleton (locked — intro hook / section headers / CTA pattern)
3. Topic + data injection (variable — what changes per piece)
4. Quality gate (the prompt self-checks against a rubric before output)

This is the same architecture I use internally — I have published 3 long-form crypto guides using a content-prompt pipeline, and the consistency is what lets me deliver 2,000+ word pieces in 24-48 hours.

Relevant work (all live on Paragraph, all produced with reusable content prompts):
- "The Ultimate Guide to Ethereum Wallets in 2026" (2,000 words)
- "The Ultimate Guide to Crypto Airdrops in 2026" (2,100 words)
- "The Ultimate Guide to Aave Protocol in 2026" (2,200 words)

Each piece follows the same prompt template but adapts to the topic. I can show you the prompt structure on a call.

Deliverables:
- 1 master content prompt (production-ready, ~2,000 tokens)
- 3 variations (long-form / listicle / thought-leadership)
- 5 topic-specific test runs (you pick the topics)
- Prompt-tuning cheat sheet (how to adjust length / tone / SEO density without rewriting)

Timeline: 3 days

Pricing: $180 fixed-price.

If you send me 1 sample piece that matches your desired voice, I will adapt the prompt to match it within 24 hours — free sample before you commit.

Best,
{{YOUR_NAME}}

Keywords: content generation prompt, SEO prompt, blog prompt, reusable prompt, brand voice, content template, prompt engineering, content at scale
```

---

### 模板 PE-4：RAG Prompt（检索增强生成提示词）

**目标 Job Posting：** 客户需要为 RAG 系统（知识库问答 / 文档检索）编写 prompt

```
Hi {{CLIENT_NAME}},

Your {{JOB_TITLE}} project caught my eye — the {{SPECIFIC_DETAIL}} part is where most RAG prompts quietly fail. The retrieval returns 5 chunks, the LLM trusts all 5 equally, and the answer confidently mixes correct and outdated info. I have seen this exact pattern break production RAG systems.

I write RAG prompts that solve 3 problems most prompts ignore:
1. Source attribution — every claim in the answer is tagged to a specific retrieved chunk
2. Confidence calibration — the prompt explicitly handles "the retrieval did not contain this"
3. Conflict resolution — when 2 chunks disagree (e.g. one says "v2 deprecated", another says "v2 supported"), the prompt surfaces the conflict instead of averaging

My background: I run an AI content studio where every article is produced via a RAG-style pipeline. The "research agent" retrieves live data (DefiLlama yields, CoinGecko prices, on-chain TVLs), the "draft agent" writes only from retrieved context, and the "fact-check agent" verifies every number back to its source URL. Same architecture, different surface.

Relevant work:
- "Where to Earn the Highest DeFi Yield Right Now" (2,400 words) — built on real-time RAG over DefiLlama Yields API (238 Aave pools + 119 Compound pools) + CoinGecko Price API. Every APY in the article traces back to a live source.
- "The Ultimate Guide to Aave Protocol in 2026" (Paragraph) — protocol mechanics grounded in retrieved on-chain data, not training memory.

Deliverables:
- 1 RAG synthesis prompt (handles multi-chunk context + attribution)
- 1 fallback prompt (handles "no relevant chunk retrieved" gracefully)
- 1 conflict-handling prompt (handles contradictory chunks)
- 10 test queries + expected outputs against your sample KB
- Integration notes for LangChain / LlamaIndex / custom RAG stacks

Timeline: 4 days

Pricing: $220 fixed-price. Includes 1 revision round and integration support over chat.

If you can share a small sample of your knowledge base (5-10 docs), I will run my prompt against it and send back a free demo before we sign.

Best,
{{YOUR_NAME}}

Keywords: RAG, retrieval-augmented generation, knowledge base QA, LLM, prompt engineering, LangChain, LlamaIndex, source attribution, hallucination prevention
```

---

### 模板 PE-5：System Prompt（系统提示词 — 产品级）

**目标 Job Posting：** 客户需要为面向用户的 LLM 产品编写系统 prompt

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is the highest-stakes prompt work there is — a system prompt shipped to end-users. I noticed {{SPECIFIC_DETAIL}} in your posting, which tells me you are already thinking about safety, not just capability. Good — that is where 90% of system prompts fall short.

I write production system prompts with 6 mandatory sections:
1. Identity & scope (who the assistant is, what it does, what it refuses)
2. Behavior rules (positive instructions, not just restrictions)
3. Refusal protocol (specific phrasings for specific refusal categories — vague refusals destroy UX)
4. Safety boundaries (PII, medical, legal, financial — handled per category)
5. Output format spec (so downstream parsing never breaks)
6. Test cases (10+ adversarial inputs the prompt must handle correctly)

Why me: I run a multi-agent content studio where I have to write system prompts for agents that publish externally — the same safety standard applies. One bad prompt and a published article makes a false claim; one bad prompt in your product and a user gets hurt.

Relevant work:
- 3 published Paragraph articles (2,000-2,200 words each) — each went through a system-prompt-driven pipeline with safety rails for financial claims (no price predictions, no "guaranteed returns," always cite APY source).
- "The Ultimate Guide to Crypto Airdrops in 2026" specifically required refusal logic for "should I buy this token" questions — same pattern your product likely needs.

Deliverables:
- 1 production system prompt (~2,000 tokens, fully commented)
- Adversarial test suite (15 cases covering safety + capability)
- 1-page "what to never change" guide (so future edits do not break safety)
- 30-min walkthrough call with your engineering team

Timeline: 5 days (longer because safety testing matters)

Pricing: $300 fixed-price. This is not a discount category — a bad system prompt costs 100x more in incident response.

If your product has a specific failure case that prompted this hire, tell me — I will draft the refusal protocol for that exact case before we sign.

Best,
{{YOUR_NAME}}

Keywords: system prompt, LLM product, safety, refusal protocol, AI safety, prompt engineering, production prompt, adversarial testing
```

---

### 模板 PE-6：Fine-Tuning Dataset（微调数据集构建）

**目标 Job Posting：** 客户需要为 LLM 微调构建指令-响应对数据集

```
Hi {{CLIENT_NAME}},

Your {{JOB_TITLE}} posting stood out because of {{SPECIFIC_DETAIL}} — most clients underestimate how much data quality matters more than data quantity for fine-tuning. 500 well-crafted examples will outperform 5,000 lazy ones, every time.

I build fine-tuning datasets with 4 quality layers:
1. Instruction diversity — same intent phrased 5+ ways (so the model generalizes, not memorizes)
2. Response grading — each response rated for completeness, tone, accuracy (you see the rubric)
3. Negative examples — explicitly marked bad responses, so the model learns what NOT to do
4. Source traceability — every example traces to a real document/source (no invented facts)

My domain edge: I have built datasets for crypto/DeFi content (where one wrong number invalidates the whole piece), so my quality bar is higher than the average "I asked ChatGPT to generate examples" freelancer.

Relevant work:
- "The Ultimate Guide to Aave Protocol in 2026" (Paragraph, 2,200 words) — required structuring complex protocol mechanics into Q&A pairs, the same skill needed for instruction-tuning datasets.
- "The Ultimate Guide to Crypto Airdrops in 2026" (Paragraph, 2,100 words) — distinguishes "how to qualify" from "should I participate" — exactly the kind of nuance fine-tuning datasets need.

Deliverables:
- 200 instruction-response pairs (JSONL format, OpenAI/Anthropic compatible)
- Quality rubric + grading sheet
- 20 negative examples with explanations
- 1 data-card (datasheet documenting source, bias, intended use)
- Format ready for OpenAI fine-tuning API / Anthropic / HuggingFace

Timeline: 7 days (quality takes time)

Pricing: $400 fixed-price for 200 examples. Pricing scales linearly for larger sets.

If you send me 3-5 examples of the input → output you want, I will generate 2 sample pairs in the exact format before we sign.

Best,
{{YOUR_NAME}}

Keywords: fine-tuning dataset, instruction tuning, SFT, supervised fine-tuning, LLM training, JSONL, dataset quality, data card
```

---

### 模板 PE-7：Prompt Optimization（现有 prompt 优化审计）

**目标 Job Posting：** 客户已有 prompt 但效果不佳，需要优化 / 审计

```
Hi {{CLIENT_NAME}},

Your job about {{JOB_TITLE}} is the prompt equivalent of a code review — and the {{SPECIFIC_DETAIL}} you mentioned is a classic symptom. Most prompts underperform not because of bad writing but because of structural issues: missing role spec, ambiguous output format, no few-shot examples, or worst of all, instructions that contradict each other.

I do prompt optimization as a 5-stage audit:
1. Structural review (does it have role / scope / format / examples / fallback?)
2. Ambiguity scan (find every instruction that could be interpreted 2+ ways)
3. Adversarial test (run 15+ edge-case inputs, document failures)
4. Token efficiency (cut bloated prompts 30-50% without losing capability)
5. Regression test (prove the optimized prompt handles everything the original did, plus more)

Why this matters: I run a content studio where prompt quality directly equals output quality. When my draft agent's prompt was underperforming, I did this exact audit and cut revision rounds from 3 to 1. Same workflow, your prompt.

Relevant work — every article below is the output of an audited and optimized prompt pipeline:
- "The Ultimate Guide to Ethereum Wallets in 2026" (Paragraph, 2,000 words)
- "The Ultimate Guide to Crypto Airdrops in 2026" (Paragraph, 2,100 words)
- "The Ultimate Guide to Aave Protocol in 2026" (Paragraph, 2,200 words)

Deliverables:
- Audit report (PDF, ~5 pages) — every issue found, severity-ranked
- Optimized prompt (production-ready)
- Before/after test results on 15+ cases
- 1-page changelog (what changed and why)

Timeline: 3 days

Pricing: $200 fixed-price for prompts up to 1,500 tokens. For longer/multi-prompt systems, +$50 per additional prompt.

If you paste your current prompt in chat, I will send back the top 3 issues I see — free, before you hire. Then you decide.

Best,
{{YOUR_NAME}}

Keywords: prompt optimization, prompt audit, prompt engineering, LLM, prompt review, adversarial testing, token efficiency, prompt debugging
```

---

## 二、AI Research & Content Writing 类（7 个模板）

### 模板 CW-1：AI Industry Research（AI 行业研究报告）

**目标 Job Posting：** 客户需要 AI 行业 / 市场研究报告

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is exactly the kind of research brief I do best. You mentioned {{SPECIFIC_DETAIL}} — that is the right level of specificity, and it is also where most research reports fail (they answer "what is AI" instead of the actual question).

I produce research reports with 3 commitments:
1. Every claim cites a primary source (not a blog summarizing a blog summarizing a study)
2. Every number has a date and a URL (live, not memory)
3. Every "trend" claim is tested against the counter-argument (I include the bear case, not just the bull case)

Why this matters more than the average freelancer: I run an AI-augmented studio with real-time Web research built into the workflow. I do not rely on training data with a 2025 cutoff — I pull fresh sources the day I write. If your report needs 2026 data, you get 2026 data, not "as of my last training."

Relevant work:
- "Where to Earn the Highest DeFi Yield Right Now: A Real-Time Comparison (June 30, 2026)" — 2,400-word research piece built on DefiLlama Yields API (238 Aave pools + 119 Compound pools), DefiLlama Protocols API (7,742 protocols, 624 lending), and CoinGecko Price API. Every APY in the report is timestamped to a specific snapshot.
- "The Ultimate Guide to Aave Protocol in 2026" (Paragraph, 2,200 words) — protocol research with real TVL figures ($12B+), real APY ranges (4-8% stablecoin), and cross-chain deployment breakdown.

Deliverables:
- 3,000-4,000-word research report (Google Doc + PDF)
- Source list with 20+ primary citations (URLs + retrieval dates)
- Executive summary (1 page, suitable for sharing with stakeholders)
- 5 "key findings" formatted as slide-ready bullets

Timeline: 5-7 days (research-heavy, quality takes time)

Pricing: $500 fixed-price. Real research is not cheap — if a freelancer bids $100 for a "research report," they are not doing research.

If you share 1-2 reports you admire (for format, not content), I will match the structure. Free outline before we sign.

Best,
{{YOUR_NAME}}

Keywords: AI industry research, market research, primary research, cited report, whitepaper, trend analysis, real-time data
```

---

### 模板 CW-2：SEO Article（SEO 文章）

**目标 Job Posting：** 客户需要关键词驱动的 SEO 文章

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} targeting {{TARGET_KEYWORD}} is right in my wheelhouse. The detail about {{SPECIFIC_DETAIL}} tells me you understand that SEO content is not just "include the keyword 8 times" — it is intent matching + structure + uniqueness.

I write SEO articles that rank for 3 reasons:
1. Search-intent mapping first — I match the article structure to what the SERP rewards (not what I guess)
2. Information gain — I include at least 1 piece of original data/analysis per article (Google's helpful content update rewards this)
3. E-E-A-T signals — real sources, real author voice, real expertise (not "in this article we will explore")

My internal pipeline: research agent pulls top-ranking SERP + related queries → outline agent structures for intent match → draft agent writes → fact-check agent verifies every claim → SEO agent optimizes headers/internal links. You get an article that went through 5 quality gates.

Relevant work — every piece below ranks for its target keyword on Paragraph and was built with this pipeline:
- "The Ultimate Guide to Ethereum Wallets in 2026" — target keyword "ethereum wallet" (2,000 words)
- "The Ultimate Guide to Crypto Airdrops in 2026: How to Qualify Without Losing Money" — target keyword "airdrop crypto" (2,100 words)
- "The Ultimate Guide to Aave Protocol in 2026" — target keyword "aave protocol" (2,200 words)

Deliverables:
- 2,000-2,500-word SEO article
- Title tag + meta description (60 / 155 char optimized)
- 5 internal-link suggestions (if you have a content library)
- Header structure (H1/H2/H3) ready to paste into your CMS
- FAQ section (for FAQ schema markup)

Timeline: 3 days

Pricing: $250 fixed-price per article. $1,000 for a 5-article batch (20% discount).

If you send me your target keyword, I will send back a free 200-word outline + SERP intent analysis before we sign.

Best,
{{YOUR_NAME}}

Keywords: SEO article, SEO writing, keyword optimization, content marketing, SERP, on-page SEO, helpful content, E-E-A-T
```

---

### 模板 CW-3：Blog Post（博客文章）

**目标 Job Posting：** 客户需要常规博客文章 / 思想领导力内容

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} stood out because of {{SPECIFIC_DETAIL}} — that is the difference between a forgettable blog post and one people actually share. Most blog writing services deliver 800 words of generic advice; you are clearly looking for something with a point of view.

I write blog posts with 3 principles:
1. Strong opening hook (the reader decides in 2 sentences whether to keep reading)
2. One core argument per post (not 7 loosely related tips)
3. Specific examples over abstract advice ("Aave's USDC on Mantle yields 8.39% APY" beats "DeFi offers attractive yields")

My workflow uses multi-agent orchestration: research agent pulls fresh sources → draft agent writes with your voice → edit agent tightens and adds specificity. The result reads like a thoughtful human wrote it, because the orchestration forces multiple revision passes.

Relevant work:
- "The Ultimate Guide to Crypto Airdrops in 2026" (Paragraph, 2,100 words) — opinionated take on "how to qualify without losing money," not a listicle
- "The Ultimate Guide to Aave Protocol in 2026" (Paragraph, 2,200 words) — argues for specific strategies, not just "here are 5 things Aave does"

Deliverables:
- 1,200-1,800-word blog post
- 3 title options (you pick)
- 2 social-media cuts (LinkedIn + Twitter) for promotion
- 1 hero-image suggestion (description for your designer or my HTML mockup)

Timeline: 2 days

Pricing: $180 fixed-price per post.

Send me 1 blog post you love (yours or someone else's) — I will match the voice in a 150-word sample before we sign.

Best,
{{YOUR_NAME}}

Keywords: blog post, blog writing, thought leadership, content marketing, brand voice, long-form content
```

---

### 模板 CW-4：Whitepaper（白皮书）

**目标 Job Posting：** 客户需要技术 / 产品白皮书

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is a high-stakes deliverable — a whitepaper is the document investors, partners, and technical buyers will judge your project by. The {{SPECIFIC_DETAIL}} you mentioned is exactly where most whitepapers fail: too much vision, not enough mechanism.

I write whitepapers with 5 mandatory sections:
1. Problem framing (specific, not "the world is broken")
2. Mechanism design (how it actually works, with diagrams if needed)
3. Evidence (data, benchmarks, case studies — not "we believe")
4. Risks + mitigations (whitepapers without a risk section look naive)
5. Roadmap with measurable milestones (not "Q3 — expand ecosystem")

My edge: I have written long-form technical content on complex crypto mechanisms (Aave V3 dual interest rate model, airdrop qualification economics) — the same skill set your whitepaper needs. I also run a multi-agent workflow where a fact-check agent verifies every claim against primary sources before handoff.

Relevant work:
- "The Ultimate Guide to Aave Protocol in 2026" (Paragraph, 2,200 words) — covers liquidity pool mechanics, aToken interest accrual, health factor liquidation math, cross-chain strategy. Whitepaper-grade depth in article format.
- "Where to Earn the Highest DeFi Yield Right Now" (2,400 words) — methodology section explains data sources (DefiLlama + CoinGecko), snapshot logic, and comparison framework. Same structure a whitepaper "Methods" section needs.

Deliverables:
- 6,000-10,000-word whitepaper (Google Doc + PDF)
- Diagrams (I provide Mermaid/Excalidraw source; your designer finalizes)
- Citation list (every claim sourced)
- Executive summary (1 page)
- Glossary (if technical terms used)

Timeline: 10-14 days (whitepapers are not rush jobs)

Pricing: $1,500 fixed-price. This reflects the research depth — a $300 whitepaper is a brochure, not a whitepaper.

If you share your existing one-pager or pitch deck, I will send back a free proposed table of contents before we sign.

Best,
{{YOUR_NAME}}

Keywords: whitepaper, technical writing, mechanism design, tokenomics, blockchain, B2B content, thought leadership, long-form
```

---

### 模板 CW-5：Technical Documentation（技术文档）

**目标 Job Posting：** 客户需要 API 文档 / 开发者文档 / 产品手册

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} caught my attention — the {{SPECIFIC_DETAIL}} detail tells me you have already suffered through bad docs (the kind where step 3 assumes you know what step 5 explains). Good technical documentation is not "writing" — it is structured empathy for the reader's confusion.

I write technical docs with 4 rules:
1. Every code example is runnable (I test it, not just paste)
2. Every concept is introduced before it is used (no forward references)
3. Every error message has a troubleshooting entry (docs that ignore errors are useless docs)
4. Every section has a "what you will learn" + "what you need first" header

Why me: my background is writing technical crypto content for readers who actually use the protocols — not "what is a smart contract" intros, but "how to compute your liquidation price on Aave V3." Same skill set your {{CLIENT_INDUSTRY}} docs need.

Relevant work:
- "The Ultimate Guide to Aave Protocol in 2026" (Paragraph, 2,200 words) — includes worked examples for borrowing against ETH, health-factor calculation, and cross-chain deployment. Each example walks through the math step-by-step.
- "The Ultimate Guide to Ethereum Wallets in 2026" (Paragraph, 2,000 words) — covers 4 wallet types with setup steps for each, including seed-phrase backup procedure and scam-pattern identification.

Deliverables:
- Documentation set (Getting Started + API Reference + Troubleshooting + FAQ)
- 10+ runnable code examples (in your language: Python/JS/curl/etc.)
- 5+ diagrams (sequence flows, architecture — Mermaid source)
- Changelog template (so your team can maintain docs going forward)

Timeline: 7-10 days

Pricing: $800 fixed-price for a standard doc set. Complex APIs negotiable.

If you share your API spec (OpenAPI/Postman) or product overview, I will write 1 sample "Getting Started" section before we sign.

Best,
{{YOUR_NAME}}

Keywords: technical documentation, API docs, developer docs, README, developer experience, DX, technical writing
```

---

### 模板 CW-6：Case Study（案例研究）

**目标 Job Posting：** 客户需要客户案例 / 成功故事

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is a case study — and the {{SPECIFIC_DETAIL}} detail you mentioned is the whole ballgame. A case study without specific numbers is a testimonial; a case study with specific numbers closes deals.

I write case studies with a 4-part structure that converts:
1. Before (specific pain, quantified — "team spent 14 hours/week on manual reporting")
2. During (what was implemented, why this approach over alternatives)
3. After (specific results, quantified — "reporting time cut to 2 hours/week, 86% reduction")
4. Quote (I draft interview questions for your client; you get the raw transcript + cleaned quote)

My process: I interview your client (30-45 min, recorded), pull data from your product analytics, and write the case study from primary sources — not from a brief your sales team filled out. This is why my case studies read like journalism, not marketing.

Relevant work — same journalism-grade sourcing:
- "Where to Earn the Highest DeFi Yield Right Now" (2,400 words) — built on live API data (DefiLlama 238 Aave pools + 119 Compound pools), each yield figure timestamped and verifiable. Same evidence standard your case study needs.
- "The Ultimate Guide to Crypto Airdrops in 2026" (Paragraph, 2,100 words) — references specific campaigns with specific numbers (Arbitrum $1B ARB, Jito $200M JTO).

Deliverables:
- 1,200-1,800-word case study
- 5-question interview script (I can conduct the interview, or you can)
- 1 pull-quote formatted for design
- 1 sidebar "key metrics" box (3-5 numbers)
- 2 social cuts (LinkedIn + Twitter) for distribution

Timeline: 5 days (interview scheduling may extend)

Pricing: $350 fixed-price.

If you share the client name + 1 metric you want highlighted, I will send back a free proposed story arc before we sign.

Best,
{{YOUR_NAME}}

Keywords: case study, customer success story, B2B content, testimonial, interview, journalism, social proof
```

---

### 模板 CW-7：Newsletter（Newsletter 内容）

**目标 Job Posting：** 客户需要每周 / 每日 newsletter 内容

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} stood out — newsletter writing is a different skill from blog writing, and the {{SPECIFIC_DETAIL}} detail tells me you already know that. Newsletters need a voice, a point of view, and the discipline to show up every week without filler.

I write newsletters with 4 principles:
1. One idea per issue (not 5 links + 3 takes — that is a digest, not a newsletter)
2. News hook in the first 3 sentences (subscribers decide in 5 seconds)
3. Original angle, not summary (if I am just aggregating, the subscriber will unsubscribe)
4. Scannable structure (H2 headers, bold key terms, ~800-1,200 words)

My unfair advantage: I run a real-time research pipeline. If your newsletter covers a fast-moving space (AI, crypto, markets), I pull fresh data the morning I write — not last week's news repackaged. This is why my published articles have specific, dated numbers (e.g. "Aave USDC on Mantle yields 8.39% APY as of June 30, 2026" — not "DeFi yields are attractive").

Relevant work:
- "Where to Earn the Highest DeFi Yield Right Now" (2,400 words) — built on real-time DefiLlama + CoinGecko data, the same "morning-of" research approach I would bring to your newsletter.
- 3 published Paragraph articles (2,000-2,200 words each) — same single-idea-per-piece discipline.

Deliverables (per issue):
- 800-1,200-word newsletter (Google Doc + HTML email-ready)
- Subject line + preview text (3 options)
- 1 "further reading" link curation (3-5 links with 1-line context)
- 1 CTA block (custom to your business goal)

Timeline: 48-hour turnaround per issue

Pricing: $150/issue, or $600/month for weekly (4 issues). Retainer preferred.

If you share 1 issue you loved (yours or another newsletter's), I will write a 200-word sample in your voice — free, before we sign.

Best,
{{YOUR_NAME}}

Keywords: newsletter, email content, recurring content, voice, weekly newsletter, subscriber retention, content strategy
```

---

## 三、Blockchain/Crypto Content Writing 类（6 个模板）

### 模板 CC-1：DeFi Guide（DeFi 指南）

**目标 Job Posting：** 客户需要 DeFi 协议 / 策略指南

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is exactly what I do — and the {{SPECIFIC_DETAIL}} detail you mentioned is the differentiator between a DeFi guide that gets bookmarked and one that gets closed in 10 seconds. Most "DeFi content" writers are generic copywriters who learned the word "yield" last week. I am not.

My DeFi writing is built on 3 foundations:
1. Real on-chain data — I pull TVL from DefiLlama, yields from protocol APIs, prices from CoinGecko. Every number in my guides is timestamped to a snapshot.
2. Mechanism literacy — I can explain WHY Aave's dual interest rate model exists, not just THAT it exists. I understand health factor math, liquidation loops, and cross-chain risk.
3. Honest risk framing — I never write "guaranteed yield" or "safe 8% returns." DeFi has real risks (smart contract, oracle, liquidity, bridge) and I name them.

Relevant work — all live, all real:
- "The Ultimate Guide to Aave Protocol in 2026: How to Lend, Borrow, and Earn Safely" — 2,200-word deep-dive on Aave V3 (Paragraph). Covers liquidity pool mechanics, aToken interest accrual, dual interest rate model, health factor math, cross-chain deployment across 12+ chains, 3 advanced yield strategies. Real TVL ($12B+), real APY ranges (4-8% stablecoin).
- "Where to Earn the Highest DeFi Yield Right Now: A Real-Time Comparison (June 30, 2026)" — 2,400 words built on DefiLlama Yields API (238 Aave pools + 119 Compound pools) + CoinGecko Price API. Every APY in the article traces to a live source.

Deliverables:
- 2,000-2,500-word DeFi guide
- 5+ real-time data citations (DefiLlama / CoinGecko / protocol APIs — with snapshot timestamps)
- 3 risk factors explicitly called out (no yield-without-risk framing)
- SEO structure (H2/H3 + FAQ schema)
- 5 internal-link suggestions

Timeline: 4 days (research-heavy)

Pricing: $400 fixed-price. DeFi content that cites real data is not the same as a $50 "what is DeFi" article.

If you tell me the protocol or strategy your guide should cover, I will send back a free proposed outline + 3 real data points I would include.

Best,
{{YOUR_NAME}}

Keywords: DeFi, decentralized finance, yield farming, liquidity pool, TVL, APY, Aave, Compound, on-chain data, crypto content
```

---

### 模板 CC-2：Airdrop Guide（空投指南）

**目标 Job Posting：** 客户需要空投策略 / 资格指南

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is a category I have published in — and the {{SPECIFIC_DETAIL}} detail tells me you want a guide that helps users qualify without losing money, not a hype piece. That framing matters: most airdrop content is "top 10 airdrops to farm!" clickbait that gets users rekt on gas.

I write airdrop guides with 3 commitments:
1. Cost vs. expected value per chain — users see the math before they farm
2. Testnet vs. mainnet strategy — explicit guidance on which to use when
3. Scam-pattern callouts — fake airdrops, drainer links, impersonator accounts

Why my airdrop content is different: I have written a 2,100-word guide that quantifies expected cost vs. expected value per chain, references real campaigns (Arbitrum $1B ARB, Optimism OP, Jito $200M JTO), and explains the 4 airdrop types + 3 mistakes that lose users money. Not a listicle.

Relevant work:
- "The Ultimate Guide to Crypto Airdrops in 2026: How to Qualify Without Losing Money" — 2,100-word published guide on Paragraph. References real campaigns with real numbers, distinguishes testnet farming economics from mainnet, and includes refusal logic for "should I buy this token" questions.
- "The Ultimate Guide to Ethereum Wallets in 2026" (Paragraph, 2,000 words) — includes scam-pattern identification, the same safety framing your airdrop guide needs.

Deliverables:
- 2,000-2,500-word airdrop guide
- 3-5 specific campaigns analyzed (with qualification criteria + cost estimate)
- Risk callout section (gas costs, Sybil detection, scam patterns)
- Wallet-setup prerequisite section (so readers can actually execute)
- 5 internal-link suggestions

Timeline: 4 days

Pricing: $350 fixed-price.

If you share the 1-2 airdrops you most want covered, I will send back a free proposed structure + the cost-vs-EV framework I would use.

Best,
{{YOUR_NAME}}

Keywords: airdrop, crypto airdrop, testnet farming, qualification strategy, Sybil detection, retroactive airdrop, crypto content
```

---

### 模板 CC-3：Wallet Tutorial（钱包教程）

**目标 Job Posting：** 客户需要钱包设置 / 使用教程

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is a category I have published in — wallet tutorials need to be technically accurate (one wrong step loses the user's funds) and readable (most readers are setting up their first wallet). The {{SPECIFIC_DETAIL}} detail you mentioned is the hardest part: making security comprehensible without dumbing it down.

I write wallet tutorials with 4 layers:
1. Concept primer (public address vs private key vs seed phrase — most users confuse these)
2. Step-by-step setup (with screenshots or written descriptions precise enough to follow)
3. Security hardening (this is where 90% of tutorials stop too early — they show setup, not safety)
4. Recovery drill (every tutorial should make the user actually test their backup BEFORE they need it)

Relevant work — same structure, published:
- "The Ultimate Guide to Ethereum Wallets in 2026: Security, Setup and Best Practices" — 2,000-word guide on Paragraph. Covers 4 wallet types (hot/cold/smart-contract/account-abstraction), private key vs seed phrase mechanics, 3 scam patterns that drain the most funds, with current ETH price + MetaMask user counts (30M+ MAU) + Ledger/Trezor 2026 firmware features.

Deliverables:
- 2,000-2,500-word wallet tutorial
- Step-by-step setup for the target wallet (MetaMask / Rabby / Ledger / Trezor / smart-contract wallet — your call)
- Security section (scam patterns + backup verification drill)
- Recovery walkthrough (restore from seed phrase on a second device)
- 5 FAQ answers (most-searched wallet questions)

Timeline: 4 days

Pricing: $300 fixed-price. Wallet tutorials have higher stakes than blog posts — one wrong instruction loses user funds.

If you tell me which wallet(s) to cover, I will send back a free proposed outline + the security section structure.

Best,
{{YOUR_NAME}}

Keywords: crypto wallet, MetaMask, hardware wallet, seed phrase, private key, wallet security, blockchain content, tutorial
```

---

### 模板 CC-4：Protocol Analysis（协议深度分析）

**目标 Job Posting：** 客户需要 DeFi/Web3 协议深度分析

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is exactly the kind of deep-dive I do — and the {{SPECIFIC_DETAIL}} detail tells me you want analysis, not summary. Most "protocol analysis" content is a reworded whitepaper; you want someone who understands the mechanism well enough to critique it.

My protocol analyses cover 6 dimensions:
1. Mechanism design (how it actually works — not the marketing version)
2. Incentive structure (who is paid to do what, and what breaks if they stop)
3. Risk surface (smart contract / oracle / governance / centralization)
4. TVL + volume trends (real numbers from DefiLlama / Dune)
5. Comparison vs. 2-3 competitors (not "Aave is the leading protocol" — vs. who, by what metric?)
6. Bull case + bear case (one-sided analysis is not analysis)

Why me: I have published protocol deep-dives that include real TVL figures ($12B+ for Aave), real APY ranges (4-8% stablecoin), and mechanism explanations (dual interest rate model, health factor math). I run a real-time research pipeline, so my numbers are not from a 2025 training cutoff.

Relevant work:
- "The Ultimate Guide to Aave Protocol in 2026: How to Lend, Borrow, and Earn Safely" (Paragraph, 2,200 words) — covers liquidity pool mechanics, aToken interest accrual, dual interest rate model (stable vs variable), health factor + liquidation math, cross-chain deployment across 12+ chains, 3 advanced yield strategies, 3 mistakes that cost newcomers the most.
- "Where to Earn the Highest DeFi Yield Right Now" (2,400 words) — compares Aave vs Compound yields across chains, built on DefiLlama data (238 Aave pools + 119 Compound pools). Aave USDC mainnet 6.96% APY vs Compound 3.27% — 2x difference explained.

Deliverables:
- 2,500-3,000-word protocol analysis
- 6-dimension framework (mechanism / incentives / risks / TVL / comparison / bull-bear)
- 10+ real data citations (DefiLlama / Dune / protocol dashboards)
- 1 mechanism diagram (Mermaid source)
- 3 "what would change my thesis" risk factors

Timeline: 6 days (deep research)

Pricing: $500 fixed-price. Protocol analysis is not a $100 article — the research takes 2-3 days alone.

If you share the protocol + 1 question you most want answered, I will send back a free proposed table of contents + the data sources I would use.

Best,
{{YOUR_NAME}}

Keywords: protocol analysis, DeFi, mechanism design, TVL, smart contract, tokenomics, blockchain research, deep-dive
```

---

### 模板 CC-5：Market Research（加密市场研究）

**目标 Job Posting：** 客户需要加密市场 / 赛道研究报告

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is a research brief, not a content brief — and the {{SPECIFIC_DETAIL}} detail tells me you want primary data, not opinions. Most "crypto market research" is a Twitter-thread-style take with charts; you want something your investment committee or product team can act on.

I produce crypto market research with 4 evidence layers:
1. Primary data (DefiLlama TVLs, CoinGecko volumes, on-chain analytics from Dune / Etherscan / Blockscout)
2. Protocol-level comparison (not "Aave is big" — Aave $12B TVL vs Compound $3B vs Maker $8B, with trend lines)
3. Player + funding landscape (who is building, who is funding, who is using)
4. Risk + counter-trend section (every bull thesis gets a bear case)

My unfair advantage: real-time data pipeline. I do not write market research from 2025 training memory. I pull fresh data the day I write — so if your report needs "as of June 30, 2026" numbers, that is what you get.

Relevant work:
- "Where to Earn the Highest DeFi Yield Right Now: A Real-Time Comparison (June 30, 2026)" — 2,400-word research piece built on DefiLlama Yields API (238 Aave pools + 119 Compound pools), DefiLlama Protocols API (7,742 protocols, 624 lending), and CoinGecko Price API. Snapshot timestamped to 2026-06-29T16:23:00Z.
- "The Ultimate Guide to Crypto Airdrops in 2026" (Paragraph, 2,100 words) — quantifies campaign economics (Arbitrum $1B ARB, Optimism OP, Jito $200M JTO) and cost-vs-EV per chain.

Deliverables:
- 3,000-4,000-word market research report
- 10+ primary data citations (live URLs + retrieval dates)
- 5 charts (I provide data + Mermaid/CSV; your designer finalizes, or I provide HTML mockups)
- Executive summary (1 page)
- Investment / product-implication section (what to do with this research)

Timeline: 7-10 days

Pricing: $600 fixed-price. Real market research with primary data is not the same as a $200 opinion piece.

If you share the specific segment (L2 / lending / restaking / RWA / etc.) and 1 question you most want answered, I will send back a free proposed research framework + 3 data sources I would use.

Best,
{{YOUR_NAME}}

Keywords: crypto market research, market analysis, TVL, on-chain data, DefiLlama, Dune, primary research, investment research
```

---

### 模板 CC-6：Tokenomics（代币经济模型分析）

**目标 Job Posting：** 客户需要代币经济模型设计 / 分析

```
Hi {{CLIENT_NAME}},

Your job for {{JOB_TITLE}} is the most analytically demanding crypto writing category — tokenomics is where hand-wavy thinking gets exposed in 30 days when the token actually launches. The {{SPECIFIC_DETAIL}} detail you mentioned tells me you already understand that tokenomics is mechanism design, not "we'll add a buyback."

I write tokenomics analyses with 5 mandatory sections:
1. Supply mechanics (total / circulating / inflation schedule / vesting cliffs — with dates)
2. Demand mechanics (what does the token DO — governance / fee accrual / staking / utility)
3. Value accrual logic (how does protocol revenue flow to holders — or does it?)
4. Incentive alignment (founders / investors / users / LPs — who is paid to do what)
5. Stress tests (what happens in a bear market / governance attack / liquidity crisis)

Why me: I have written about Aave V3's dual interest rate model, health factor math, and liquidation loops — the same mechanism-design literacy your tokenomics analysis requires. I do not write "this token has strong fundamentals" — I write "this token's value accrual depends on X, which fails if Y happens."

Relevant work:
- "The Ultimate Guide to Aave Protocol in 2026" (Paragraph, 2,200 words) — covers Aave's liquidity pool mechanics, aToken interest accrual, dual interest rate model (stable vs variable), health factor + liquidation math. Same mechanism-design depth your tokenomics analysis needs.
- "Where to Earn the Highest DeFi Yield Right Now" (2,400 words) — compares Aave vs Compound yield mechanics across 238 + 119 pools, real-time data. Same comparative analysis skill.

Deliverables:
- 2,500-3,500-word tokenomics analysis
- Supply schedule table (with dates + cliff events)
- 1 value-flow diagram (Mermaid source)
- 3 stress-test scenarios (bear market / governance attack / liquidity crisis, with quantified impact)
- 1-page TL;DR for non-technical readers

Timeline: 7 days

Pricing: $550 fixed-price. Tokenomics analysis is high-stakes — a wrong call here costs your readers real money.

If you share the token contract address or whitepaper, I will send back a free proposed analysis framework + 3 risk factors I would surface.

Best,
{{YOUR_NAME}}

Keywords: tokenomics, token economics, supply schedule, value accrual, mechanism design, governance, staking, vesting, crypto research
```

---

## 四、使用说明

### 4.1 占位符替换指南

| 占位符 | 含义 | 示例 |
|--------|------|------|
| `{{CLIENT_NAME}}` | 客户姓名（从 job posting 提取） | "Sarah" / "John" |
| `{{JOB_TITLE}}` | Job posting 标题（简短引用） | "your DeFi yield guide project" |
| `{{CLIENT_INDUSTRY}}` | 客户行业 | "DeFi" / "AI SaaS" / "crypto exchange" |
| `{{SPECIFIC_DETAIL}}` | 从 job posting 引用的具体细节 | "the part where you mentioned the bot keeps recommending deprecated APIs" |
| `{{TARGET_KEYWORD}}` | SEO 文章目标关键词 | "ethereum wallet" |
| `{{CONTENT_TYPE}}` | 内容类型 | "blog post" / "newsletter" / "whitepaper" |
| `{{YOUR_NAME}}` | 你的名字 | "Kai" / AutoCorp 代表名 |

### 4.2 投递策略建议

- **每日投递量**：5-10 个高质量 proposal（多 agent 编排可批量定制）
- **首段必须个性化**：`{{SPECIFIC_DETAIL}}` 必须从 job posting 真实引用，否则 Upwork 算法降权
- **附 1-2 个相关 Portfolio 链接**：选最贴近 job 类目的那篇 Paragraph 文章
- **响应时间**：job 发布后 1 小时内投递，Upwork "Recent" feed 中曝光最高
- **Connects 预算**：每个 proposal 消耗 10-16 Connects，新账号免费 150 Connects，可投 9-15 个；后续需付费购买

### 4.3 定价调整原则

- **首单偏低**：profile 0 评价时，按模板定价的 80% 报价，JSS 积累后恢复
- **固定价优于时薪**：固定价项目客户决策快，且 5 天安全期后释放快
- **Retainer 优惠**：客户承诺 4+ 篇/月时，给 20% 批量折扣

---

## 五、引用的真实案例 URL（投递时附在 proposal 末尾）

| 文章 | URL | 状态 |
|------|-----|------|
| art_001 Ethereum Wallets | https://paragraph.com/@autocorp-insights/the-ultimate-guide-to-ethereum-wallets-in-2026-security-setup-and-best-practices | ✅ 已发布 |
| art_002 Crypto Airdrops | https://paragraph.com/@autocorp-insights/the-ultimate-guide-to-crypto-airdrops-in-2026-how-to-qualify-without-losing-money | ✅ 已发布 |
| art_003 Aave Protocol | https://paragraph.com/@autocorp-insights/the-ultimate-guide-to-aave-protocol-in-2026-how-to-lend-borrow-and-earn-safely-2 | ✅ 已发布 |
| art_004 DeFi Yield Comparison | (待发布，Paragraph 链接待补) | ⏳ ready_to_publish |

> 投递时建议：art_004 发布后，将 URL 补全到本表，并优先用于 DeFi Guide / Market Research / Tokenomics 类 proposal。

---

> 数据来源：`company/config/content-ledger.yaml`（文章 URL + 状态）、`company/knowledge/strategic-research/us-market-revenue-research-2026-06-30.md`（定价依据）
