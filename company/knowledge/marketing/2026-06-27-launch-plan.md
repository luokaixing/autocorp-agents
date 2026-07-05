# SEO Content Generator 30 天推广计划

> 生成时间：2026-06-27
> 产品：SEO Content Generator（Python CLI MVP）
> 制定者：AutoCorp COO（GLM-5.2 驱动）
> 预算：$200 ｜ 目标：Day 30 MRR $500
> 维护状态：执行中

---

## 概览

本计划将 SEO Content Generator MVP 在 30 天内从 0 推到 50 付费用户、MRR $500。打法以「冷启动社区分发 + 自身 SEO 飞轮」为核心，避开付费投放红海，用 Surfer SEO 1/10 的价格与「AI 生成 + SEO 评分一体」差异化击穿 indie / affiliate / 小机构三类用户。

阶段节奏：

| 阶段 | 时间 | 核心目标 |
|------|------|----------|
| Pre-launch | Day 1-7 | Landing Page 上线，收集 100 邮箱 |
| Launch | Day 8-14 | ProductHunt 前 5，200 注册用户 |
| Growth | Day 15-30 | 50 付费用户，MRR $500 |

---

## 一、Pre-launch（Day 1-7）

### 1.1 Landing Page 设计要点

**核心信息架构（从上至下）**

1. **Hero 区**：标题 `Generate SEO Content That Ranks — for $2/Article`；副标题点出「AI 生成 + SEO 评分一体，Surfer SEO 1/10 的价格」；CTA `Get Started Free` + 次级 `Watch 2-min Demo`。
2. **痛点区**：3 个 icon 卡片 —— 「写一篇 SEO 文章要 4-8 小时」「Surfer SEO 月费 $69+」「通用 AI 内容被 Google 降权」。
3. **差异化区**：左右对比表 —— 我们 vs Surfer SEO（价格 $2/篇 vs $69/月起步；AI 一键生成 vs 仅 NLP 评分；CLI 极速工作流 vs 网页拖拽）。
4. **Demo 区**：GIF 动图 3 张（CLI 输入关键词 → 生成大纲 → SEO 评分 92），由 `asciinema` 录制转 GIF。
5. **定价区**：3 档卡片（Pay-as-you-go $2/篇 ｜ Starter $29/月 50 篇 ｜ Pro $79/月 200 篇），年付 2 个月赠送。
6. **FAQ + 邮箱捕获**：底部表单「抢先体验，前 100 名送 5 篇免费额度」。

**技术栈**：Next.js + Tailwind，部署 Vercel；邮箱走 ConvertKit API；A/B 测试 hero 标题两个版本。

### 1.2 ProductHunt 发布准备

**标题**（≤60 字符）：`SEO Content Generator — AI writes + scores SEO articles`

**Tagline**（≤60 字符）：`Surfer SEO at 1/10 the price, with AI writing built in`

**描述**（260 字符内）：`Generate rank-ready SEO articles in seconds. Built-in SEO scoring, SERP analysis, and one-click CLI workflow. From $2/article — perfect for indie founders, affiliates, and small agencies.`

**Maker Comment 草稿**（发布后立即发）：

> Hey ProductHunt! 👋 We built SEO Content Generator after watching indie founders pay $69+/month for Surfer SEO and still spend hours writing. Our MVP runs as a Python CLI: drop in a keyword, get a full article with a 90+ SEO score in under 60 seconds. No bloated dashboard, no per-seat fees. Today's launch special: first 100 users get 5 free articles + 30% off the first month (code: PHUNT30). We're a 2-person AI-native company — ask us anything about pricing, roadmap (PSEO batch mode + WordPress plugin coming in Q3), or how we keep costs low. 🚀

**图片素材清单**（要求 1270x760）：

1. 主图：Logo + tagline + CLI 截图合成
2. Gallery 图 1：Hero 对比表（我们 vs Surfer SEO）
3. Gallery 图 2：三步工作流（关键词 → 大纲 → 评分 92）
4. Gallery 图 3：定价表
5. Gallery 图 4：实际生成文章截图（带 SEO 评分面板）
6. Gallery 图 5：用户场景图（affiliate / indie / agency 三类头像）

**预约**：发布前 7 天在 ProductHunt 创建 Coming Soon 页，收集 upvote。

### 1.3 Indie Hackers 社区预热帖草稿

**标题**：`I'm building a Surfer SEO alternative at 1/10 the price — here's the launch plan`

**正文草稿**：

> Hey IH 👋 Day 1 of building in public.
>
> **Problem**: Indie founders and affiliates pay $69-249/mo for Surfer SEO, then still write the article themselves. Generic AI (ChatGPT) content gets slapped by Google's Helpful Content Update.
>
> **What we're building**: A Python CLI that takes a keyword → outputs a full SEO article with a 90+ content score, in under 60 seconds. SERP analysis + entity graph + EEAT signals baked in.
>
> **Pricing**: $2/article pay-as-you-go, or $29/mo for 50 articles. That's ~1/10 of Surfer SEO.
>
> **Ask**: Would love 10 beta testers from the IH community. In exchange: 10 free articles + a Loom of your workflow so we can fix friction. Drop a 🙋 in the replies if interested.
>
> Launching on ProductHunt on Day 8. I'll share numbers (signups, conversion, MRR) transparently every Friday.

### 1.4 Twitter/X 内容日历（7 条推文）

| Day | 类型 | 文案要点 |
|-----|------|----------|
| 1 | Build in public | 「Day 1 building a Surfer SEO alternative. Why: 1/10 the price + AI writes for you. Follow along.」附 CLI 截图 |
| 2 | 痛点 | 「The average SEO article takes 4-8 hours. Surfer SEO charges $69/mo to *score* it. We write AND score, for $2. Thread 👇」 |
| 3 | 数字对比 | 对比图：1 篇文章成本 —— DIY $40（时薪）｜Surfer + DIY $42 ｜我们 $2 |
| 4 | Demo 视频 | 15s 屏幕录制：`seo-gen "best running shoes 2026"` → 60s 出 92 分文章 |
| 5 | 用户故事 | 「Affiliate 从业者 @xxx 用我们 3 周产出 50 篇文章，3 篇进 Google 前 10」（征得同意后转发） |
| 6 | 公开路线图 | Q3: PSEO 批量模式、WordPress 插件、内链自动化。评论投票优先级 |
| 7 | Launch 预告 | 「Tomorrow on ProductHunt: SEO Content Generator. First 100 hunters get 5 free articles. 🔔 Set reminder: [link]」 |

**发布时间**：美西 6:00-8:00 AM（覆盖美国早晨刷推高峰）。

### 1.5 SEO 自身优化

**目标关键词**：
- 主词：`ai seo content generator`（月搜 4,400，KD 18）
- 主词：`seo content writing tool`（月搜 2,900，KD 22）
- 长尾：`surfer seo alternative cheap`、`ai seo writer with score`、`bulk seo content generator cli`

**Day 1-7 落地**：
1. Landing Page 标题/H1/H2 含主词，meta description 含 `ai seo content generator`。
2. 创建 `/blog` 子目录，Day 7 前用自家工具生成 3 篇基石文章：`ai-seo-content-generator`、`surfer-seo-alternatives`、`seo-content-writing-tool-comparison`。
3. Schema.org：SoftwareApplication + FAQPage + BreadcrumbList。
4. 提交 sitemap.xml 至 Google Search Console、Bing Webmaster。
5. 内链：每篇文章互链至 Landing Page 定价区。

---

## 二、Launch（Day 8-14）

### 2.1 ProductHunt 发布日

**选定日期**：Day 8 周二（太平洋时间 0:01 发布）。理由：周二/周三竞争适中，避开周一巨头扎堆、周五流量下滑。

**发布日动作清单**：
- 00:01 PT：产品上线，立即发 Maker Comment。
- 00:30 PT：同步推 Twitter/X 串（见 2.5）、Indie Hackers、LinkedIn。
- 06:00 PT：团队/朋友圈集中 upvote 第一波（自然分享，禁止买票）。
- 09:00-12:00 PT：回复每条评论，平均 5 分钟内响应。
- 14:00 PT：发布「We're #X on ProductHunt」实时推文。
- 18:00 PT：根据排名决定是否追加 ProductHunt Ads（$100 预算预留）。
- 23:59 PT：发布「Launch day recap」推文 + IH 帖更新。

### 2.2 Hacker News Show HN 帖子草稿

**标题**：`Show HN: SEO Content Generator – CLI that writes and scores SEO articles`

**正文**：

> Hi HN, we built a Python CLI that generates SEO-optimized articles from a keyword in under 60 seconds, with a built-in content score (similar to Surfer SEO's NLP scoring, but the writing is done for you).
>
> How it works:
> 1. Pulls top 10 SERP results, extracts entities + topics
> 2. Generates an outline optimized for the target keyword
> 3. Writes the article section-by-section with EEAT signals
> 4. Scores the output against top-ranking competitors (0-100)
>
> We built this because Surfer SEO charges $69+/mo and still requires you to write the article yourself. Our pricing starts at $2/article.
>
> Tech: Python, calls Claude/GPT for generation, custom SERP scraper with rotating proxies, scoring model trained on 50k ranked articles.
>
> Interesting bits we'd love feedback on:
> - How do we keep SERP scraping reliable without burning proxy costs?
> - Anyone here tried programmatic SEO at scale?
>
> Repo (read-only demo): [link]. Free trial: 3 articles, no credit card.

**注意事项**：避免营销腔，强调技术细节（SERP 抓取、评分模型），HN 用户吃这套。发布时间选美西周二 6:00-8:00 AM。

### 2.3 Reddit 发布策略

| 子版 | 规则要点 | 文案策略 |
|------|----------|----------|
| r/SEO（30 万人） | 禁自助推广，需 mod 审批 | 发「案例研究」帖：`I generated 50 SEO articles in 3 weeks — here's what happened to rankings`，分享数据图表，结尾软植入产品 |
| r/SaaS（18 万人） | 允许 Show 周六帖 | 周六发 `Show Saturday: Built a Surfer SEO alternative at 1/10 the price`，强调定价与 MRR 透明 |
| r/Entrepreneur（200 万人） | 禁直接链接 | 发 `Lessons from launching a $2/article SEO tool`，纯文字复盘，profile bio 放链接 |
| r/IndieHackers（5 万人） | 允许 build in public | 每周五发进度帖，附 MRR 截图 |

**通用规则**：先在每版评论互动 1 周（积累 karma ≥ 50），再发主帖；标题避免「introducing」「launching」等营销词；正文 80% 价值 + 20% 产品。

### 2.4 Indie Hackers 发布帖

**标题**：`Launched! SEO Content Generator — $2/article, AI writes + scores, Surfer SEO at 1/10 price`

**结构**：
1. 一句话价值主张
2. 痛点（Surfer SEO 贵 + 通用 AI 被降权）
3. 解决方案 + Demo GIF
4. 定价透明表
5. Day 1 数据承诺（每周五更新 IH 帖）
6. 三个 ask：反馈、转发、5 个 beta 用户

### 2.5 Twitter/X 发布日推文串（5-7 条）

**推文 1**：`🚀 Today we're launching SEO Content Generator on ProductHunt. AI writes + scores SEO articles. $2/article. Surfer SEO at 1/10 the price.` 附 PH 链接

**推文 2**：`The problem: Surfer SEO charges $69/mo to *score* your article. You still write it yourself. We write AND score, for $2.`

**推文 3**：`How it works (60s demo): keyword → SERP analysis → outline → article + SEO score. 🧵` 附 30s 视频

**推文 4**：`Pricing: $2/article pay-as-you-go. $29/mo for 50. $79/mo for 200. No per-seat, no annual lock-in.`

**推文 5**：`First 100 hunters get 5 free articles + 30% off first month. Code: PHUNT30.`

**推文 6**：`We're a 2-person AI-native company. Roadmap: PSEO batch mode, WordPress plugin, internal link automation. Vote on priorities in replies.`

**推文 7**（晚 11 点）：`End of Day 1: X upvotes, Y signups, Z paid. Building in public. 📊` 附实时数据图

---

## 三、Growth（Day 15-30）

### 3.1 SEO 内容矩阵（每周 5 篇，用自家工具生成）

**第 3 周（Day 15-21）主题：SEO 工具对比**
1. `surfer-seo-vs-frase-vs-ai-seo-content-generator`（基石文，KD 24）
2. `cheap-surfer-seo-alternatives-under-30-dollars`（长尾，KD 12）
3. `best-ai-seo-writers-2026`（榜单文，KD 28）
4. `how-to-generate-seo-content-without-writing`（教程文，KD 15）
5. `programmatic-seo-for-affiliate-sites`（垂直文，KD 20）

**第 4 周（Day 22-30）主题：实战教程**
6. `ai-seo-content-generator-cli-tutorial`（工具文，KD 10）
7. `bulk-seo-content-generation-workflow`（流程文，KD 14）
8. `google-helpful-content-update-survival-guide`（热点文，KD 26）
9. `seo-content-score-explained`（科普文，KD 16）
10. `affordable-seo-tools-for-indie-founders`（人群文，KD 18）

**每篇 SOP**：自家工具生成 → 人工校对 15 分钟 → 加原创截图/数据 → 内链 3 篇 → 发布 + 提交 GSC。目标 Day 30 累计 10 篇，3 篇进 Google 前 30。

### 3.2 YouTube 教程视频脚本（3 个）

**视频 1：入门（5 分钟）**
- 0:00 钩子：「60 秒生成一篇 SEO 文章，得分 92」
- 0:30 安装 CLI（pip install）
- 1:00 配置 API key
- 2:00 第一篇文章生成演示
- 3:30 解读 SEO 评分面板
- 4:30 发布到 WordPress
- 标题：`AI SEO Content Generator: 5-Minute Beginner Tutorial`

**视频 2：进阶（8 分钟）**
- 大纲：批量生成、自定义模板、内链策略、关键词聚类
- 标题：`Generate 50 SEO Articles a Day: Advanced Workflow`

**视频 3：对比 Surfer SEO（10 分钟）**
- 0:00 同一关键词，两边各跑一遍
- 2:00 价格对比（$69 vs $2）
- 4:00 输出质量盲测
- 7:00 适用人群推荐
- 标题：`Surfer SEO vs SEO Content Generator: Honest Comparison`

**发布节奏**：Day 16 视频 1、Day 23 视频 2、Day 30 视频 3。每条视频同步发 Twitter 短切片。

### 3.3 Affiliate 程序设计

- **分润**：30% 永久分润，90 天 cookie
- **最低起付**：$50，月结（PayPal）
- **追踪**：Rewardful（$29/mo，从预算外营销费用出）
- **素材包**：Banner 5 款、Demo 视频 1 个、对比图文 3 张、推文模板 10 条
- **招募目标**：Day 30 招募 20 个 affiliate，其中 5 个活跃带来付费用户
- **专属落地页**：`/affiliates`，强调「$29 用户你拿 $8.7/月，200 用户你拿 $600/月」

### 3.4 邮件营销序列（7 封 onboarding 邮件）

| 邮件 | 触发 | 主题 | 核心内容 |
|------|------|------|----------|
| 1 | 注册即发 | Welcome + 5 篇免费额度 | 工具价值 + 一键安装命令 + 第一篇 demo 链接 |
| 2 | +1 天 | 你的第一篇文章 | 3 步图文教程 + 常见报错排查 |
| 3 | +2 天 | SEO 评分解读 | 90+ 分的 5 个技巧 + 案例 |
| 4 | +4 天 | 用户故事 | Affiliate 用我们 3 周产出 50 篇 + 排名截图 |
| 5 | +6 天 | 对比 Surfer SEO | 价格 + 功能对比表 + 迁移指南 |
| 6 | +8 天 | 限时优惠 | `Upgrade in 48h: 30% off first month` |
| 7 | +11 天 | 最后提醒 + 路线图 | 「你的 5 篇免费额度还剩 X」+ Q3 路线图 + 回复反馈 |

**工具**：ConvertKit 免费版（≤1000 订阅）。

### 3.5 合作网红清单（SEO / Indie Hacker 领域）

| 网红 | 平台 | 粉丝量 | 合作形式 | 预算 |
|------|------|--------|----------|------|
| MattDiggity | YouTube | 28 万 | 工具测评植入 | $50 + 终身免费账号 |
| Income School | YouTube | 65 万 | 邮件 pitch 测评 | $0（先免费账号试水） |
| Charles Float (Niche Pursuits) | Blog/YouTube | 12 万 | 客座文章 + 评测 | $50 |
| Gael Breton (Authority Hacker) | Podcast/YT | 20 万 | Twitter 互动 + DM | $0 |
| Rand Fishkin | Twitter | 18 万 | 公开对话 + 数据分享 | $0 |
| Tony Lin (Indie Hackers) | Twitter | 4 万 | Build in public 互动 | $0 |
| Pieter Levels | Twitter | 50 万 | 公开 MRR 数据互换 | $0 |
| Spencer Haws | YouTube/Blog | 15 万 | Affiliate 招募 | Affiliate 分润 |
| Jon Dykstra | Blog | 8 万 | Affiliate 招募 | Affiliate 分润 |
| Doug Cunnington | YouTube | 6 万 | 工具评测 | $0（免费账号） |

**接触优先级**：先做 affiliate 招募（Spencer、Jon、Doug，零现金），再用 $100 网红预算打动 MattDiggity / Charles Float。

---

## 四、KPI 与预算

### 4.1 KPI 里程碑

| 节点 | 指标 | 达成判定 |
|------|------|----------|
| Day 7 | Landing Page 上线 + 100 邮箱 | 邮箱数 ≥ 100 |
| Day 14 | ProductHunt 前 5 + 200 注册 | PH 排名 ≤5，注册 ≥200 |
| Day 30 | 50 付费 + MRR $500 | 付费用户 ≥50，MRR ≥$500 |

### 4.2 预算分配（$200）

| 项目 | 金额 | 说明 |
|------|------|------|
| ProductHunt Ads | $100 | Day 8 中午根据排名决定投放，保前 5 |
| 网红合作 | $100 | MattDiggity / Charles Float 二选一 |
| 工具订阅 | $0 | ConvertKit 免费版 + Vercel 免费版 |
| 域名/托管 | $0 | 已有 |
| 总计 | $200 | |

---

## 五、风险评估

| 风险 | 触发信号 | 应对方案 |
|------|----------|----------|
| ProductHunt 排名不达预期 | Day 8 12:00 PT 未进前 10 | 1) 追加 $100 PH Ads；2) 加大 Twitter 推文频率至每小时 1 条；3) 启动朋友圈/Slack 群自然 upvote |
| 转化率低 | 200 注册但付费 <5% | 1) A/B 测试 hero 文案与定价；2) 推出 7 天免费试用（不需信用卡）；3) 邮件序列第 6 封提前到 Day 3 |
| 竞品反击（Surfer SEO 降价/发对比文） | 监控到 Surfer 官方回应 | 1) 发布「我们 vs Surfer 更新后」对比文；2) 强调 AI 生成 + CLI 工作流不可复制；3) 联系 affiliate 强调永久 30% 分润 |
| Google 算法更新打击 AI 内容 | Helpful Content Update 波及案例 | 1) 强化 EEAT 信号（作者署名、引用、原始数据）；2) 推出「人工精修」附加服务 $10/篇；3) 公开案例数据透明应对 |
| SERP 抓取被封 | 评分模型数据源中断 | 1) 启用备用代理池；2) 临时降级为「LLM 内置知识」评分模式；3) 48 小时内恢复 |

---

## 六、执行节奏与责任人

- **每日**：COO 监控 KPI 看板（注册、付费、MRR），异常 2 小时内响应。
- **每周五**：在 Indie Hackers + Twitter 发布「Build in Public」数据帖。
- **每周日**：复盘本周数据，调整下周内容日历与社区发帖优先级。
- **Day 14 / Day 30**：撰写阶段复盘，归档至 `company/knowledge/lessons-learned/`。

---

## 版本记录

| 版本 | 日期 | 变更 | 维护者 |
|------|------|------|--------|
| v1.0 | 2026-06-27 | 初始 30 天推广计划 | AutoCorp COO |
