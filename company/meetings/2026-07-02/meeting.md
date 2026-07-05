# 产研同步会纪要 - 2026-07-02

## 会议时间
2026-07-02 08:00 (Asia/Shanghai)

## 参会人员
ProductManager, CTO, Architect, CEO

## 0. 战略层任务进度（P0，2026-06-30 战略转向后置顶）
| 任务类型 | 任务名 | 状态 | 进度 | 预期收益 |
|---------|-------|------|------|---------|
| 价值链切入 P0-A | SaaS 选型指南英文长文系列 | 待启动（Day 1: 2026-07-02） | 0% | $5-20 affiliate/篇 |
| 价值链切入 P0-A | Shopify 独立站 SEO 指南系列 | 待启动（Day 2） | 0% | $5-20 affiliate/篇 |
| 价值链切入 P0-A | 跨境支付方案对比系列 | 待启动（Day 3） | 0% | $30-150 affiliate |
| 价值链切入 P0-A | Claude/GPT-5/Gemini 实测对比系列 | 待启动（Day 3） | 0% | $5-20 affiliate |
| 价值链切入 P0-A | 独立站博客 SEO 内容代运营 | 待启动（Day 3） | 0% | $200-500/月 |
| 可持续产品 P0-B | AI 工具横向评测周报 Newsletter | MVP 待启动 | 0% | $9/月订阅 + $5-20 affiliate |
| 可持续产品 P0-B | CVE 漏洞周报订阅 | MVP 待启动 | 0% | $19/月订阅 |
| 可持续产品 P0-B | 跨境支付对比站（压缩版 MVP） | MVP 待启动 | 0% | $30-150 affiliate + $10-30 广告 |
| 旧路径 P1（降级） | 美国市场 Upwork/Fiverr AI 服务接单 | P1 支撑层 | - | 仅作分发渠道，不再 P0 |
| 旧路径 P1（降级） | Layer3 / Publish0x / 闲鱼 / 猪八戒 | 黑名单（已证伪） | - | 不再投入资源 |

> 旧战略 P0 任务已降级为 P1 支撑层；详见战略转向决策：company/decisions/strategic-pivot-to-value-chain-entry-2026-06-30.md
> 后续接入 task_queue.yaml 后此表自动填充进度（TODO 标注见 _build_strategic_progress 源码）。


## 1. 需求汇报（ProductManager）
（PM 汇报失败：<html>

<head><title>404 Not Found</title></head>

<body>

<center><h1>404 Not Found</h1></center>

<hr><center>TLB</center>

</body>

</html>，本次使用占位内容）
待补充市场调研与需求清单。

## 2. 技术方向（CTO）
（CTO 同步失败：<html>

<head><title>404 Not Found</title></head>

<body>

<center><h1>404 Not Found</h1></center>

<hr><center>TLB</center>

</body>

</html>，本次使用占位内容）
待补充技术方向。

## 3. 任务拆解（Architect）
# AutoSEO 架构设计与模块拆分

基于市场情报首推方向（SEO 内容自动化 SaaS）与 CTO 技术选型，进行架构设计。

---

## 一、模块拆分清单

| 模块 | 职责 | 负责人 | 优先级 |
|------|------|--------|--------|
| `api-gateway` | FastAPI 网关：鉴权/限流/计费/路由 | 程序员 | P0 |
| `auth` | 用户注册/登录/JWT/Stripe 关联 | 程序员 | P0 |
| `billing` | Stripe Checkout/Webhook/订阅状态机 | 程序员 | P0 |
| `keyword-engine` | 关键词研究：SerpAPI 集成/难度评估/聚类 | 程序员 | P0 |
| `content-pipeline` | 内容生成管线：大纲→正文→SEO 元信息（复用 engine/） | 程序员 | P0 |
| `seo-optimizer` | EEOP 信号注入/内链/Schema.org 结构化数据 | 程序员 | P1 |
| `exporter` | Markdown/HTML/WordPress/Webflow 导出 | 程序员 | P1 |
| `frontend` | Next.js 编辑器/用户面板/付费页 | 程序员 | P0 |
| `scheduler` | APScheduler 异步任务（批量生成/定时发布） | 程序员 | P1 |
| `ledger-bridge` | 与 AutoCorp ledger 对接，记录真实收入 | 程序员 | P1 |

## 二、接口定义（核心 API）

```
POST /api/auth/register     {email, password} → {token, user}
POST /api/auth/login        {email, password} → {token, user}

POST /api/billing/checkout  {plan} → {checkout_url}
POST /api/billing/webhook   Stripe event → 200
GET  /api/billing/status    → {plan, quota, used}

POST /api/keywords/research {seed_keyword, market='US'} → {keywords[], difficulty, volume}
POST /api/content/generate  {keyword, outline?, tone, length} → {article_id}
GET  /api/content/:id       → {title, body, meta, status}
GET  /api/content/list      → {articles[]}
POST /api/content/:id/export {format} → {download_url}

GET  /api/quota             → {plan, used, limit}
```

## 三、内容生成管线接口（内部，复用 engine/）

```
KeywordAnalyzer.analyze(seed) → KeywordCluster
OutlineGenerator.generate(keyword, cluster) → Outline
ContentWriter.write(outline, tone, length) → DraftArticle
SEOOptimizer.optimize(draft) → {article, meta_title, meta_desc, schema, internal_links}
```

各模块已实现优雅降级：LLM 失败 → TemplateProvider 兜底，不阻断管线。

## 四、技术规范（强制）

1. **API 规范**：全部 REST + JSON，统一响应包 `{code, msg, data}`，错误码 4xx 业务/5xx 系统。
2. **鉴权**：JWT（access 1h + refresh 7d），Stripe customer_id 与 user 绑定。
3. **限流**：免费用户 10 次/日，Pro 200 次/日，按 user_id + endpoint 维度限流。
4. **幂等**：Webhook 用 Stripe event_id 去重；内容生成用 idempotency_key。
5. **数据隔离**：用户内容按 user_id 隔离，禁止跨用户读取。
6. **密钥管理**：Stripe key / SerpAPI key 一律走 SecretsManager（.secrets/ 隔离），禁止入库/硬编码。
7. **测试**：每个模块单测覆盖率 ≥ 70%，测试员 gate 不通过禁止合并。
8. **日志**：结构化 JSON 日志，敏感字段脱敏（email/phone/token）。

## 五、数据模型（核心表）

```
users(id, email, password_hash, stripe_customer_id, plan, created_at)
articles(id, user_id, keyword, title, body, meta_json, status, created_at)
keywords(id, user_id, seed, cluster_json, difficulty, volume, created_at)
quota_usage(id, user_id, date, used_count, limit_count)
exports(id, article_id, format, download_url, expires_at)
```

MVP 阶段用 SQLite + 文件，schema 与 Postgres 兼容，便于二期迁移。

## 六、部署拓扑

```
Vercel (Next.js SSR/SSG) ←→ Railway (FastAPI) ←→ SQLite/Redis
                                  ↓
                            engine/ (Agent 编排)
                                  ↓
                            LLM (trae_bridge / OpenAI)
```

## 七、里程碑对齐

- W1：api-gateway + auth + billing 骨架
- W2：keyword-engine + content-pipeline（复用 engine/）
- W3：frontend 编辑器 + 导出
- W4：seo-optimizer + 内测

## 4. 最终决策（CEO）
决策：approve
理由：
# CEO 立项评审决策：AutoSEO

## 决策：approve（附条件）

---

## 一、决策理由

**支持立项**：
1. **现金流优先**：AutoSEO（SEO 内容自动化）MRR 区间 $8k-20k，技术栈与 AutoCorp 现有 engine/ 高度复用，是当前 6 个赛道中「回报/投入比」最高的方向。
2. **零成本启动可行**：MVP 阶段所有核心资源均有免费额度——Vercel/Fly.io 免费层、GLM-5.2 零成本 LLM、SQLite 无需数据库费、SerpAPI 每月 100 次免费搜索。账本余额 $0 不构成阻断。
3. **市场窗口存在**：Google 2025 算法打击低质 AI 内容后，强调 EEOP 信号的差异化产品反而有窗口期，先发优势有价值。
4. **与战略契合**：project_memory 已明确「内容变现路径已跑通（市场分析→SEO 教程→Twitter/Reddit 引流→Paragraph 打赏）」，AutoSEO 是该路径的产品化升级。

## 二、预算审批

| 项目 | 预算 | 说明 |
|------|------|------|
| 初始投入 | **$0** | 全部使用免费额度，账本余额 $0 期间禁止任何真实支出 |
| 域名 | 延后 | MVP 用 Vercel 子域名（autoseo.vercel.app），首笔收入到位后再购域名（约 $10/年，需人工确认） |
| SerpAPI | $0 | 用免费 100 次/月，MVP 阶段足够 |
| Stripe | $0 | 仅按交易抽成，无月费 |
| LLM | $0 | GLM-5.2 经 TRAE 后端零成本 |

**硬约束**：首笔真实收入入账前，PaymentGate 对所有 >$0 真实支出直接 block。

## 三、附加条件（revise 要点）

1. **MVP 范围压缩**：架构师的 10 个模块中，P0 仅保留 6 个（api-gateway/auth/billing/keyword-engine/content-pipeline/frontend），P1 模块（seo-optimizer/exporter/scheduler/ledger-bridge）延后到首笔收入后。
2. **变现验证前置**：W2 结束前必须完成一次「手动端到端变现验证」——用 AutoSEO 生成一篇 SEO 文章，发布到 Paragraph/Twitter，验证能否带来打赏/付费转化，再继续 W3-W4。
3. **合规底线**：内容生成必须强制 EEOP 信号（引用源/事实校验），禁止生成虚假/误导性内容，合规检查写入 content-pipeline。
4. **人工在环节点**：Stripe live key 接入、域名购买、首笔提现——这三个节点必须走 human_loop 请求用户协助。

## 四、资源分配

| 角色 | 分配任务 | 工期 |
|------|----------|------|
| 程序员 | W1 api-gateway+auth+billing 骨架 | 1 周 |
| 程序员 | W2 keyword-engine + content-pipeline（复用 engine/） | 1 周 |
| 测试 | W1-W2 并行编写单测，覆盖率 ≥70% | 持续 |
| COO | W2 变现验证：准备 Paragraph/Twitter 引流物料 | 1 周 |
| CEO | W2 末评审变现验证结果，决定是否继续 W3-W4 | - |

## 五、终止条件（提前 terminate）

- W2 末变现验证零转化 → 暂停 W3-W4，复盘后决定 pivot 或 terminate。
- 任何合规红线命中 → 立即终止相关功能。
- LLM 成本失控（若 GLM-5.2 不可用需切付费模型）→ 暂停评估单位经济模型。

## 六、下一步

1. 本决策写入 company/decisions/ceo-2026-07-02.md。
2. 程序员领取 W1 任务，进入 Phase-Design → Phase-Code。
3. COO 启动变现验证物料准备。

注意：此任务可能超出 ceo 职责范围，建议转交对应角色。

## 5. 营收驾驶舱（每日必看）
### 钱包余额（2026-07-02）
- ethereum: 0.0 ETH (`${ETH_TIPPING_ADDRESS}`)

### 内容资产统计
- 已发布：3 篇
- 待发布：1 篇
- 草稿：0 篇
- 累计打赏 ETH：0.0
- 累计打赏 USD：0.0
- 累计浏览量：0

### 当日赚钱任务建议（按 ROI 排序）
**P0 战略层（价值链切入点 + 可持续产品，参考 playbook v5.0）**
- [ ] Day 1（2026-07-02）：SaaS 选型指南英文长文系列（CRM/Help Desk/PM 三类各 1 篇，2000-2400 词，注册 G2/Capterra affiliate）
- [ ] Day 1（2026-07-02）：AI 工具横向评测周报 Newsletter MVP（10 评测任务 + 多 agent 跑批 + beehiiv 上架）
- [ ] Day 2：Shopify 独立站 SEO 优化指南系列（技术 SEO / 内容 SEO / Page Speed 各 1 篇，注册 Shopify/Ahrefs affiliate）
- [ ] Day 2：CVE 漏洞周报订阅（5 agent 抓 Microsoft/Apple/Google/Adobe/Oracle CVE，beehiiv 摘要 + Gumroad 付费 $19/月）
- [ ] Day 3：跨境支付方案对比系列（Airwallex/Wise/Stripe/PayPal 实时费率抓取 + 3 篇对比长文）
- [ ] Day 3：Claude vs GPT-5 vs Gemini 实测对比系列（多 agent 跑同任务集，输出结构化对比）
- [ ] Day 3：独立站博客 SEO 内容代运营（service 模式，仅作 P0 兜底过渡）
- [ ] Day 3：跨境支付对比站 MVP（8 篇 Best X for Y 对比长文 + 周度费率抓取静态表，Vercel + Hashnode 部署）

**P1 战术层（美国市场即时变现，原 P0 降级）**
- [ ] Upwork/Fiverr AI 服务接单：不再作为主路径，仅用于 Newsletter/对比站流量分发
- [ ] 美国市场 SEO 长文残余流量变现：服务于 P0 产品导流

**P2 养号层（社交媒体账号培育，服务于 P0 产品分发）**
- [ ] Twitter 养号引流：每日 1-2 条推文，服务于 P0-A/P0-B 产品分发
- [ ] Reddit 养号引流：账号 2026-07-04 解锁后启动 r/SaaS + r/cybersecurity + r/LocalLLaMA 分发
- [ ] LinkedIn 企业号养号：服务于 SaaS 选型指南 B2B 分发

**P3 fallback 层（低优先级兜底，资源空闲时推进）**
- [ ] Paragraph 文章打赏残余流量：3 篇已发布文章持续引流，不主动投入资源
- [ ] Hashnode/Medium 联合发布：复用 P0-A 内容，零边际成本分发

**P4 加密支线（已证伪路径，禁止主动投入资源）**
- [x] Layer3 / Galxe / Binance L&E / Publish0x / Mirror.xyz / 闲鱼 / 猪八戒（详见 disproven-paths-blacklist.md）

> 战略转向依据：company/decisions/strategic-pivot-to-value-chain-entry-2026-06-30.md

### 危机自检
⚠️ **钱包余额为 0 或查询失败** - 公司无现金流，今日必须推进至少 1 个即时收入渠道
ℹ️ **累计打赏为 0** - 推广力度需加强（Twitter/Reddit）

> 公司第一原则：每天必须让钱包余额增加。详细策略见 company/knowledge/daily-revenue-cockpit.md


## 6. 最挣钱行业动态扫描（2026-06-30 新增）
### Top 5 最挣钱行业动态（scanner.scan_most_profitable_industries）
| 排名 | 行业 | 利润率 | 增长率 | AI 可切入性 | 综合评分 |
|------|------|--------|--------|-------------|----------|
| 1 | 企业服务 SaaS（含 AI Agent / Coding 工具内容） | 高（70%+ 毛利） | 高（35%+ CAGR） | 中高（4 分） | **4.3** | 内容 + 工具双线，已验证能力高度匹配 |
| 2 | 电商与跨境贸易（独立站内容 / 选品工具） | 中（30-50% 毛利） | 高（25-30%） | 中（4 分） | **4.0** | SEO 内容 + Listing 工具，匹配已发布文章能力 |
| 3 | AI 应用层（AI 工具评测 / 教程内容） | 中（60-75% 毛利，扣推理后 10-30% 净利） | 极高（ARR 翻倍） | 中（3.5 分） | **3.8** | 工具评测内容，需持续投入对抗 OpenAI/Anthropic 生态 |
| 4 | 网络安全（选型指南 / 漏洞周报内容） | 高（70%+ 毛利） | 中高（12-15%） | 低（2.5 分） | **3.3** | 仅内容侧可行，工具侧不可行 |
| 5 | 金融科技（跨境支付对比 / 监管周报内容） | 中（15-25% 净利） | 中高（25-35%） | 低（2.5 分） | **3.2** | 仅内容侧可行，核心支付 / 保险不可行 |
| 1 | https://finance.sina.com.cn/stock/usstock/summary/2026-06-30/doc-inifczzy1672658.shtml | CrowdStrike FY27 Q1 ARR 55.1 亿美元 +24% YoY，富国银行目标价上调 80% 至 900 美元 | 网络安全 |
| 2 | http://m.toutiao.com/group/7637544993925743104/ | Coinbase Q1 2026 总营收 14.13 亿美元 -31%，净亏 3.94 亿美元，现货市场份额 8.6% 创新高，衍生品 +169% | 加密货币 |
| 3 | http://m.toutiao.com/group/7656673944660902409/ | NVIDIA Q1 FY26 营收 816.15 亿美元 +85%，净利 583.21 亿美元 +211%；Broadcom Q2 FY26 营收 221.87 亿美元 +48%；AMD Q1 102.53 亿美元 +38%；高通 Q2 105.99 亿美元 | 半导体 + AI 基础设施 |
| 4 | http://m.toutiao.com/group/7615483237485347347/ | 宁德时代野村 2026 净利预测 920-950 亿元，2027 年 1140-1180 亿元，全球市占率 39.2% 连续 9 年第一 | 绿色能源 |
| 5 | http://m.toutiao.com/group/7657033185527595535/ | 2026 年全球 GLP-1 市场规模预计突破 1000 亿美元，偏向型 GLP-1（先维盈®）SLIMMER Ⅲ期数据：48 周体重下降 15.4% | 医疗生物 |

### 黄金切入点扫描（scanner.scan_value_chain_entry_opportunities）
| 排名 | 切入点 | 行业 | 启动成本 | 到账速度 |
|------|--------|------|---------|---------|
| 1 | SaaS 选型指南英文长文系列（1.1.1） | SaaS | 低（3 天） | 7-14 天 | 通过 | 与已发布 Paragraph 文章能力完全同源，Day 1 即可启动，Google Ads + affiliate 双变现，SaaS GPM 70-80% 利润池最厚 |
| 2 | Shopify 独立站 SEO 优化指南系列（2.1.1） | 电商跨境 | 低（3 天） | 7-14 天 | 通过 | 与已发布文章能力同源，Shopify affiliate + Google Ads，电商市场规模最大 |
| 3 | 跨境支付方案对比系列（5.1.1） | 金融科技 | 低（3 天） | 7-14 天 | 通过 | 金融 Google Ads CPM 最高（$15-50），Airwallex 估值 110 亿热度高，浏览器自动化实时费率抓取差异化 |
| 4 | Claude vs ChatGPT vs Gemini 实测对比系列（3.1.1） | AI 应用层 | 低（3 天） | 7-14 天 | 通过 | 多 agent 并行实测是 AI 公司独家能力（壁垒最高），AI 应用 ARR 翻倍市场热度爆炸，HackerNews 流量大 |
| 5 | 独立站博客 SEO 内容代运营（2.1.3） | 电商跨境 | 低（3 天） | 7-14 天 | 通过 | 月度订阅制（service 但可持续），多 agent 编排流水线规模化交付，DTC 卖家付费意愿高 |

### 新高利润行业检查
- ⚠️ 已知行业 电商跨境 未在扫描结果中，需复核

### 现有切入点竞争力检查
✅ Top 5 切入点（SaaS 选型 / Shopify SEO / 跨境支付 / AI 对比 / 独立站代运营）均在扫描结果中，竞争力暂无重大变化信号

数据源（2026-06-30 战略转向后必读）：
- `company/knowledge/strategic-research/most-profitable-industries-2026.md`
- `company/knowledge/strategic-research/industry-profit-pool-analysis.md`
- `company/knowledge/strategic-research/value-chain-entry-opportunities.md`
- `company/knowledge/strategic-research/sustainable-revenue-product-ideas.md`

输出：当日战略任务建议（P0 优先，价值链切入 → 可持续产品 → P1 战术 → P2 养号 → P3 fallback → P4 加密支线）
> 扫描日期：2026-07-02 | 战略转向决策：company/decisions/strategic-pivot-to-value-chain-entry-2026-06-30.md


## 7. 价值链切入点执行进度（2026-06-30 新增）
| 排名 | 切入点 | 行业 | 启动日 | 状态 | 进度 | 预期收益 |
|------|--------|------|--------|------|------|---------|
| 1 | SaaS 选型指南英文长文系列 | SaaS | Day 1 (2026-07-02) | 待启动 | 0% | $5-20 affiliate/篇 |
| 2 | Shopify 独立站 SEO 优化指南系列 | 电商跨境 | Day 2 | 待启动 | 0% | $5-20 affiliate/篇 |
| 3 | 跨境支付方案对比系列 | 金融科技 | Day 3 | 待启动 | 0% | $30-150 affiliate |
| 4 | Claude vs GPT-5 vs Gemini 实测对比系列 | AI 应用层 | Day 3 | 待启动 | 0% | $5-20 affiliate |
| 5 | 独立站博客 SEO 内容代运营 | 电商跨境 | Day 3 | 待启动 | 0% | $200-500/月 |

> 数据源：task_queue.yaml（task_type=value_chain_entry）+ value-chain-entry-opportunities.md Top 5 排序
> 首笔收入检查节点：Day 7（2026-07-02 + 7 天）


## 8. 可持续产品开发进度（2026-06-30 新增）
| 排名 | 产品 | 类型 | 切入行业 | MVP 启动日 | 状态 | 进度 | 预期收益 |
|------|------|------|---------|-----------|------|------|---------|
| 1 | AI 工具横向评测周报 Newsletter | 内容资产 | AI 应用层 | Day 1 (2026-07-02) | MVP 待启动 | 0% | $9/月订阅 + $5-20 affiliate |
| 2 | CVE 漏洞周报订阅 | 内容资产 | 网络安全 | Day 2 | MVP 待启动 | 0% | $19/月订阅 |
| 3 | 跨境支付对比站（压缩版 MVP） | 聚合 | 金融科技 | Day 3 | MVP 待启动 | 0% | $30-150 affiliate + $10-30 广告 |

> 数据源：task_queue.yaml（task_type=sustainable_product）+ sustainable-revenue-product-ideas.md Top 3 排序
> 首笔收入检查节点：Day 30（2026-07-02 + 30 天）


## 当日任务清单
- [ ] task-001: -- → 负责人: programmer（medium）
- [ ] task-002: **API 规范**：全部 REST + JSON，统一响应包 `{code, msg, data}`，错误码 4xx 业务/5xx 系统。 → 负责人: programmer（medium）
- [ ] task-003: **鉴权**：JWT（access 1h + refresh 7d），Stripe customer_id 与 user 绑定。 → 负责人: programmer（medium）
- [ ] task-004: **限流**：免费用户 10 次/日，Pro 200 次/日，按 user_id + endpoint 维度限流。 → 负责人: programmer（medium）
- [ ] task-005: **幂等**：Webhook 用 Stripe event_id 去重；内容生成用 idempotency_key。 → 负责人: programmer（medium）
- [ ] task-006: **数据隔离**：用户内容按 user_id 隔离，禁止跨用户读取。 → 负责人: programmer（medium）
- [ ] task-007: **密钥管理**：Stripe key / SerpAPI key 一律走 SecretsManager（.secrets/ 隔离），禁止入库/硬编码。 → 负责人: programmer（medium）
- [ ] task-008: **测试**：每个模块单测覆盖率 ≥ 70%，测试员 gate 不通过禁止合并。 → 负责人: tester（medium）
- [ ] task-009: **日志**：结构化 JSON 日志，敏感字段脱敏（email/phone/token）。 → 负责人: programmer（medium）
- [ ] task-010: W1：api-gateway + auth + billing 骨架 → 负责人: programmer（medium）
- [ ] task-011: W2：keyword-engine + content-pipeline（复用 engine/） → 负责人: programmer（medium）
- [ ] task-012: W3：frontend 编辑器 + 导出 → 负责人: programmer（medium）
- [ ] task-013: W4：seo-optimizer + 内测 → 负责人: programmer（medium）
- [ ] task-014: 按既定方案推进开发 → 负责人: programmer（high）
