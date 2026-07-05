# 产研同步会纪要 - 2026-07-04

## 会议时间
2026-07-04 08:00 (Asia/Shanghai)

## 参会人员
ProductManager, CTO, Architect, CEO

## 0. 战略层任务进度（P0，2026-06-30 战略转向后置顶）
| 任务类型 | 任务名 | 状态 | 进度 | 预期收益 |
|---------|-------|------|------|---------|
| 价值链切入 P0-A | SaaS 选型指南英文长文系列 | 待启动（Day 1: 2026-07-04） | 0% | $5-20 affiliate/篇 |
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
【市场调研】
# 可变现产品需求候选清单（基于 2026 种子情报）

结合 AutoCorp 现有 Agent 编排能力与「现金流优先」战略，识别 4 个候选，按优先级排序：

## 候选 1：程序化 SEO 长尾内容工厂（P0，首选立即立项）
- **痛点**：独立站长/小企业主做 SEO 内容慢（4-8h/篇）；关键词研究门槛高（Ahrefs $100+/月）；通用 AI 生成内容同质化被 Google 算法打压，需 EEOP 信号
- **目标用户**：独立站长、Affiliate 从业者、本地服务/电商独立站小企业主、SEO 机构、SaaS 内容营销团队
- **竞品**：Surfer SEO（$69-249/月，偏 NLP 需人工写作）、Frase（被收购路线不稳）、Byword.ai/Koala.sh（批量生成价格战激烈，质量波动）
- **差异化**：SERP 实时分析 + 实体图谱 + 程序化 SEO（PSEO）批量站点生成；Agent 自主完成「关键词聚类→大纲→成稿→内链→CMS 发布」全流程
- **变现路径**：按篇 $1-5（试水漏斗顶）→ 订阅 $29/月（50 篇）/ $79/月（200 篇）/ $99/月（无限制+PSEO）；附加关键词额度包、内链自动化插件
- **MRR 目标**：$8,000-20,000（假设客单价 $49/月，160-400 付费用户）
- **技术栈**：SERP 抓取+代理池 / LLM 结构化生成 / WordPress+Webflow 发布集成
- **MVP 周期**：2-3 周
- **推荐**：★★★★★（现金流最快、技术栈复用度最高、与 Agent 能力天然契合）

## 候选 2：长内容→多平台短内容改写工具（P0，与候选 1 并行启动）
- **痛点**：内容创作者每周花 5-10h 手工拆解长内容为多平台短内容；跨平台格式差异大（TikTok 钩子/LinkedIn 专业口吻/Twitter 短链）；现有工具只转录切片，不「理解语义后重新生成」
- **目标用户**：YouTube 博主（1万-50万订阅）、Newsletter 作者、中小企业营销团队（2-10人）、Podcast 主理人
- **竞品**：Repurpose.io（分发强但改写弱）、Opus Clip（短视频头部但中文支持一般且贵）、Castmagic/Deciphr（播客方向再创作有限）
- **差异化**：多模态理解（音视频+字幕）+ 风格化改写（模仿创作者个人语调）
- **变现路径**：SaaS 订阅 $19/月（Starter 单平台）/ $39/月（Pro 多平台）/ $49/月（Business 团队席位）；年付优惠 2 个月；可叠加按分钟计费渲染额度包
- **MRR 目标**：$5,000-15,000（假设客单价 $35/月，150-430 付费用户）
- **技术栈**：Whisper/Deepgram ASR + LLM 改写；MVP 先做纯文本脚本输出规避视频渲染工程量
- **MVP 周期**：3-4 周（纯文本脚本版）
- **推荐**：★★★★☆（与候选 1 技术栈高度复用，可并行启动）

## 候选 3：ATS 简历优化 + JD 匹配工具（P1，季节性现金流补充）
- **痛点**：求职者不懂 ATS 关键词匹配投递石沉大海；面试准备无方向；2026 科技行业回暖求职者付费意愿强
- **目标用户**：美国市场求职者（应届生、转行者、被裁科技从业者）、H1B/绿卡申请者、大学就业指导中心（B2B）
- **竞品**：Teal（$9-29/月用户基数大）、Rezi（$3-29/月韩国出海）、Jobscan（$49.95/月老牌）
- **差异化**：AI 模拟面试（语音）+ 简历动态优化 + Offer 谈判辅导全链路
- **变现路径**：Freemium（免费简历分析）→ Pro $9/月（简历无限+JD 匹配）/ $29/月（含模拟面试）；一次性简历精修 $49-99；B2B 大学/训练营批量授权
- **MRR 目标**：$4,000-10,000（假设客单价 $15/月，270-670 付费用户；季节性强校招季峰值）
- **技术栈**：PDF/Word 简历解析 + JD 关键词提取匹配 + LLM 改写；可选 Whisper+TTS 模拟面试；ATS 兼容 PDF 渲染是细节难点
- **MVP 周期**：3-4 周（不含语音模拟面试）
- **推荐**：★★★☆☆（季节性强；通用 LLM 下沉风险较高，需快速建数据护城河）

## 候选 4：Shopify 电商客服垂直 AI Agent（P2，二期切入，预留 6 个月 runway）
- **痛点**：垂直场景下通用 AI 不专业（不懂行业术语/无法接入业务系统/缺合规校验）；中小企业自建缺技术能力，外包定制 $20k+ 起步
- **目标用户**：中小企业（电商、SaaS、本地服务）客服团队；Shopify 电商卖家优先
- **竞品**：Intercom Fin（$0.99/次解决，偏中大型）、Harvey（法律独角兽只服务大所）、Sierra（企业级融资巨量）
- **差异化**：面向 SMB 的「开箱即用+可定制」Agent，价格仅头部 1/5，聚焦 Shopify 电商客服单一垂直
- **变现路径**：按席位 $49/月（标准）/ $199/月（高级含自定义知识库+API）；按对话量前 1000 次/月免费超出 $0.1/次；实施费一次性 $500-2000
- **MRR 目标**：$10,000-30,000（假设客单价 $99/月，100-300 付费席位；客单价高、流失率低、LTV 极佳）
- **技术栈**：RAG 知识库 + 工具调用（Shopify/Zendesk/Slack）+ 多轮对话状态管理 + 人工接管 + 合规审计日志
- **MVP 周期**：4-6 周（单一垂直）；销售周期 2-8 周
- **推荐**：★★★★☆（客单价高 LTV 佳，但销售周期长需预留 runway，建议二期切入）

## 决策建议（供 CEO 评审）
1. **首期 0-3 个月**：并行启动候选 1 + 候选 2，目标合计 MRR $8,000（技术栈复用 LLM+Web+Stripe，Agent 自主完成全流程）
2. **二期 3-6 个月**：复用候选 1/2 的 RAG 与 Agent 编排能力切入候选 4（Shopify 电商客服），新增 MRR $10,000
3. **候选 3** 作为季节性现金流补充（校招季峰值启动）
4. **风险提示**：候选 3/4 通用 LLM 下沉风险高，需快速建立数据/工作流护城河；所有赛道关注 GDPR/CCPA 合规，尤其用户内容类（1、2、3）

## 立项优先级
- **P0 立即立项**：候选 1（程序化 SEO 长尾内容工厂）
- **P0 并行立项**：候选 2（长内容改写工具）
- **P1 季节性启动**：候选 3（ATS 简历工具）
- **P2 二期切入**：候选 4（Shopify 电商客服 Agent）

【需求清单】
# AutoCorp 需求清单（基于市场情报与产品矩阵）

> 来源：2026 种子情报 + 4 个产品候选矩阵（PSEO 内容工厂 / 长内容改写 / ATS 简历 / Shopify 客服 Agent）
> 维度：编号 / 用户痛点 / 优先级 / 预估开发量

## 一、程序化 SEO 内容工厂（P0 首选）

| 编号 | 用户痛点 | 优先级 | 预估开发量 |
|------|----------|--------|------------|
| REQ-001 | 独立站长不懂如何发现低竞争长尾关键词，Ahrefs/SEMrush 月费 $100+ 门槛高 | P0 | 3-5 人日（SERP 抓取 + 关键词难度评估模型） |
| REQ-002 | 一篇高质量 SEO 长文从关键词到大纲到成稿需 4-8 小时，产出慢 | P0 | 5-7 人日（关键词聚类 → LLM 大纲 → 分段生成 → 内链自动化） |
| REQ-003 | 通用 AI 生成内容同质化，被 Google 算法打压，缺 EEOP 信号 | P0 | 4-6 人日（实体图谱注入 + 引用来源标注 + 作者署名模板） |
| REQ-004 | 程序化 SEO（PSEO）批量站点生成工程量大，小团队无力搭建 | P1 | 7-10 人日（模板引擎 + 大规模静态站点生成 + Cloudflare Pages 部署） |
| REQ-005 | 发布到 WordPress/Webflow 需手动复制粘贴，无法批量自动发布 | P1 | 3-4 人日（CMS 发布集成 + REST API 对接） |
| REQ-006 | 缺少内链自动化，SEO 内部链接策略落地难 | P2 | 2-3 人日（内链图谱 + 自动插入插件） |

## 二、长内容→多平台短内容改写工具（P0 并行）

| 编号 | 用户痛点 | 优先级 | 预估开发量 |
|------|----------|--------|------------|
| REQ-007 | YouTube/Podcast 长内容手工拆解为多平台短内容每周花 5-10 小时 | P0 | 4-5 人日（Whisper/Deepgram ASR + 字幕解析） |
| REQ-008 | 跨平台格式差异大（TikTok 钩子 / LinkedIn 专业口吻 / Twitter 短链），人工适配易出错 | P0 | 5-7 人日（平台风格模板 + LLM 风格化改写） |
| REQ-009 | 现有工具只转录切片，不「理解语义后重新生成」，内容质量参差 | P0 | 4-6 人日（语义分段 + 主题提取 + 重写引擎） |
| REQ-010 | 创作者希望保持个人语调，但通用 AI 改写后风格丢失 | P1 | 5-8 人日（few-shot 风格学习 + 创作者语调样本库） |
| REQ-011 | 视频渲染管线工程量大，MVP 阶段需规避 | P2 | 7-12 人日（ffmpeg + 云函数渲染，二期再做） |

## 三、ATS 简历优化 + JD 匹配工具（P1 季节性）

| 编号 | 用户痛点 | 优先级 | 预估开发量 |
|------|----------|--------|------------|
| REQ-012 | 求职者不懂 ATS 关键词匹配，简历投递石沉大海 | P1 | 3-4 人日（PDF/Word 简历解析 + JD 关键词提取匹配） |
| REQ-013 | 简历改写需保留专业经历又优化 ATS 兼容性 | P1 | 3-5 人日（LLM 改写 + ATS 兼容 PDF 渲染） |
| REQ-014 | 面试准备无方向，缺针对 JD 的模拟面试 | P2 | 6-8 人日（Whisper+TTS 语音模拟面试 + 反馈） |
| REQ-015 | Offer 谈判辅导缺失，求职者吃亏 | P2 | 2-3 人日（谈判话术库 + 场景模拟） |

## 四、Shopify 电商客服垂直 AI Agent（P2 二期）

| 编号 | 用户痛点 | 优先级 | 预估开发量 |
|------|----------|--------|------------|
| REQ-016 | 通用 AI 不懂电商行业术语，无法接入 Shopify 订单/库存系统 | P2 | 7-10 人日（RAG 知识库 + Shopify API 工具调用） |
| REQ-017 | 中小企业自建客服 Agent 缺技术能力，外包定制 $20k+ 起步 | P2 | 5-7 人日（开箱即用模板 + 一键部署） |
| REQ-018 | 多轮对话状态管理复杂，转人工时机难把控 | P2 | 4-6 人日（对话状态机 + 人工接管触发器） |
| REQ-019 | 客服合规审计日志缺失，无法追溯 | P2 | 2-3 人日（审计日志 + 合规检查） |

## 五、通用基础设施需求（跨产品复用）

| 编号 | 用户痛点 | 优先级 | 预估开发量 |
|------|----------|--------|------------|
| REQ-020 | 多产品共用支付/订阅管理，重复开发 | P0 | 3-4 人日（Stripe 统一封装 + 订阅计费中心） |
| REQ-021 | 用户身份与多产品授权割裂 | P1 | 3-5 人日（SSO + 产品矩阵授权） |
| REQ-022 | 缺统一数据分析后台，无法追踪各产品 MRR/流失率 | P1 | 4-6 人日（数据看板 + 事件埋点） |

## 优先级汇总
- **P0（立即启动，0-3 个月）**：REQ-001~003、007~009、020（合计约 27-39 人日）
- **P1（3-6 个月）**：REQ-004~005、010、012~013、021~022（合计约 25-35 人日）
- **P2（6-12 个月或季节性）**：REQ-006、011、014~015、016~019（合计约 30-45 人日）

## 决策建议
1. 首期聚焦 P0 共 9 条需求，目标 4-6 周内交付候选 1+2 的 MVP
2. REQ-020（统一支付）作为基础设施先行，避免后续重复开发
3. REQ-011（视频渲染）和 REQ-014（语音模拟面试）作为高工程量项延后
4. 建议立项后由架构师拆分为 2 周一个 Sprint 的迭代计划

## 2. 技术方向（CTO）
# AutoCorp 技术方向

# AutoCorp 近期技术方向（基于 PM 调研与需求清单）

> 决策原则：现金流优先 + 技术栈最大化复用 + 简洁高效厌恶过度工程
> 范围：首期 P0（候选 1 PSEO 内容工厂 + 候选 2 长内容改写 + REQ-020 统一支付）

## 一、整体技术选型决策

### 1. 前端：Next.js 14（App Router）+ TailwindCSS + shadcn/ui
- **理由**：SSR/SSG 天然适配 SEO 内容站（候选 1 核心需求）；shadcn/ui 复制即用避免重型组件库依赖；TailwindCSS 加速迭代
- **复用**：候选 1 内容站 + 候选 2 用户后台 + 候选 3 简历工具前端共用同一组件库
- **风险**：App Router 仍在演进，部分生态库（如富文本编辑器）兼容性需验证；缓解：核心页面用 Server Components，复杂交互隔离到 Client Components

### 2. 后端：Python FastAPI + Pydantic v2
- **理由**：AutoCorp 现有 Agent 编排能力（engine/）全部 Python 实现，直接复用；FastAPI 异步性能足够支撑 MVP；Pydantic v2 类型安全
- **复用**：LLM 调用、SERP 抓取、ASR 改写全在 Python 侧，与前端通过 REST API 解耦
- **风险**：Python 部署相比 Node.js 略重；缓解：用 Docker + Uvicorn workers 横向扩展

### 3. LLM：OpenAI 兼容协议 + 多模型路由（不绑死单一供应商）
- **理由**：OpenAI 兼容已成事实标准，便于切换 GPT/Claude/国产模型；AutoCorp 已有 LLMClient 抽象层
- **选型**：
  - SEO 长文生成：Claude 3.5 Sonnet（长上下文 + 写作质量优）
  - 长内容改写：GPT-4o-mini（成本可控 + 多模态理解）
  - 关键词聚类/实体提取：GPT-4o-mini（结构化输出稳定）
- **风险**：API 成本随用户量上升；缓解：结果缓存 + 分级调用（简单任务走小模型）+ 用户自带 key 模式

### 4. ASR：Deepgram（首选）+ Whisper API（降级）
- **理由**：Deepgram 实时性 + 价格（$0.0043/分钟）优于 OpenAI Whisper（$0.006/分钟）；中文支持两者相当
- **风险**：Deepgram 国内访问需代理；缓解：用户上传场景走 Whisper API 作为降级

### 5. 数据库：PostgreSQL（Supabase 托管）
- **理由**：关系型 + JSONB 混合存储适配多变的产品需求；Supabase 自带 Auth/Storage/Realtime 减少 MVP 工程量
- **复用**：候选 1/2/3 共用同一 Supabase 项目，按 schema 隔离
- **风险**：单一 Supabase 项目后续可能成瓶颈；缓解：MVP 阶段足够，规模化后拆分

### 6. 支付：Stripe Checkout + Customer Portal（REQ-020）
- **理由**：Checkout 无需前端处理 PCI 合规；Customer Portal 让用户自助管理订阅，减少客服负担
- **复用**：统一支付中心封装为独立服务，候选 1/2/3 共用
- **风险**：Stripe 不支持部分国家；缓解：MVP 聚焦美国市场，后续按需接 PayPal

### 7. 部署：Vercel（前端）+ Fly.io（Python 后端）+ Cloudflare Pages（PSEO 静态站点）
- **理由**：Vercel 与 Next.js 原生集成；Fly.io 全球部署 Python 服务且支持按需扩容；Cloudflare Pages 适配候选 1 的 PSEO 批量静态站点场景
- **风险**：多平台部署增加运维复杂度；缓解：CI/CD 统一用 GitHub Actions

### 8. SERP 抓取：Bright Data（首选）+ 自建代理池（降级）
- **理由**：Bright Data 反爬能力强且合规；自建代理池工程量大且不稳定
- **风险**：Bright Data 成本 $500+/月起；缓解：MVP 阶段用 SerpAPI（$75/月起）验证 PMF，规模化后切换

## 二、架构方向（一期 MVP）

```
┌─────────────────────────────────────────────┐
│ Vercel (Next.js 前端)                       │
│  - 内容站 SSG (候选 1)                       │
│  - 用户后台 (候选 1/2/3)                     │
└─────────────────────────────────────────────┘
                  │ REST API
┌─────────────────────────────────────────────┐
│ Fly.io (FastAPI 后端)                       │
│  - Agent 编排层 (复用 engine/)               │
│  - LLM 路由 (LLMClient)                     │
│  - ASR 调度 (Deepgram/Whisper)              │
│  - SERP 抓取调度                            │
└─────────────────────────────────────────────┘
        │                   │              │
┌──────────────┐  ┌──────────────┐  ┌──────────────┐
│ Supabase     │  │ Stripe       │  │ Cloudflare   │
│ (PG+Auth)    │  │ (支付中心)   │  │ Pages (PSEO) │
└──────────────┘  └──────────────┘  └──────────────┘
```

## 三、技术规范

1. **API 规范**：RESTful + OpenAPI 3.0 schema 自动生成（FastAPI 原生支持）
2. **类型安全**：前端 TypeScript strict mode + 后端 Pydantic v2
3. **测试**：pytest（后端）+ Vitest（前端）+ Playwright（E2E）；覆盖率门槛 70%
4. **CI/CD**：GitHub Actions，PR 必须通过 lint+test+build 才能合并
5. **密钥管理**：复用 AutoCorp SecretsManager 模式（.secrets/ 物理隔离 + ref:// 引用），禁止密钥进 git
6. **可观测性**：Sentry（错误监控）+ PostHog（产品分析，REQ-022 复用）

## 四、风险点与缓解

| 风险 | 等级 | 缓解措施 |
|------|------|----------|
| LLM API 成本随用户量爆发 | 高 | 结果缓存 + 分级模型路由 + 用户自带 key 模式 |
| SERP 抓取被反爬封锁 | 高 | MVP 用 SerpAPI 验证 PMF，规模化后切 Bright Data |
| Google 算法更新打压 AI 内容 | 中 | EEOP 信号建设（引用来源 + 作者署名 + 实体图谱） |
| Deepgram 国内访问受限 | 中 | Whisper API 降级方案 |
| 多产品并行导致工程分散 | 中 | 统一组件库 + 统一支付中心 + 2 周 Sprint 节奏 |
| Supabase 单项目瓶颈 | 低 | MVP 阶段足够，规模化后按产品拆分 schema/项目 |

## 五、立项建议

1. **立即立项**：候选 1（PSEO 内容工厂）+ 候选 2（长内容改写）+ REQ-020（统一支付中心）
2. **技术栈复用度**：前端 Next.js + 后端 FastAPI + DB Supabase + 支付 Stripe，候选 1/2/3 共用 90%
3. **MVP 周期**：4-6 周（候选 1 的 2-3 周 + 候选 2 的 3-4 周 + 支付中心 3-4 日，并行）
4. **架构师下一步**：拆分模块清单 + 接口定义 + 目录结构 + Sprint 计划

## 六、不做什么（避免过度工程）

- **不做**微服务拆分（MVP 阶段单体 FastAPI 足够）
- **不做**自建 K8s（用 Fly.io + Vercel 托管）
- **不做**自建 ASR 模型（直接调 API）
- **不做**自建代理池（用第三方服务）
- **不做**视频渲染（候选 2 MVP 纯文本脚本）
- **不做**语音模拟面试（候选 3 延后）

## 3. 任务拆解（Architect）
# 架构设计文档：autoCorp-daily（首期 P0 双产品 + 统一支付中心）

> 基于 PM 调研 + 需求清单 + CTO 技术方向
> 范围：候选 1（PSEO 内容工厂）+ 候选 2（长内容改写）+ REQ-020（统一支付中心）
> 原则：单体 FastAPI + 模块化包结构，避免微服务过度工程

## 一、模块拆分清单

### 后端（FastAPI 单体，按包隔离）

| 模块 | 职责 | 依赖 | 负责人 | 估时 |
|------|------|------|--------|------|
| `app/core/config` | 配置管理（环境变量、密钥 ref://） | - | 程序员 | 0.5 人日 |
| `app/core/security` | JWT 鉴权、CORS、限流 | Supabase Auth | 程序员 | 1 人日 |
| `app/db/supabase_client` | Supabase 客户端封装 + 仓储基类 | Supabase | 程序员 | 1 人日 |
| `app/modules/auth` | 用户注册/登录/SSO（REQ-021 基础） | Supabase Auth | 程序员 | 1.5 人日 |
| `app/modules/payment` | Stripe 统一支付中心（REQ-020） | Stripe API | 程序员 | 3-4 人日 |
| `app/modules/seo_content` | PSEO 内容工厂核心（REQ-001~006） | LLMClient, SerpAPI | 程序员 | 8-10 人日 |
| `app/modules/content_rewriter` | 长内容改写核心（REQ-007~011） | LLMClient, Deepgram/Whisper | 程序员 | 8-10 人日 |
| `app/modules/llm_router` | LLM 多模型路由 + 缓存 + 降级 | LLMClient | 程序员 | 2 人日 |
| `app/modules/serp_fetcher` | SERP 抓取调度（SerpAPI 封装） | SerpAPI | 程序员 | 1.5 人日 |
| `app/modules/asr_dispatcher` | ASR 调度（Deepgram 主 + Whisper 降级） | Deepgram, OpenAI | 程序员 | 1.5 人日 |
| `app/modules/cms_publisher` | CMS 发布集成（WordPress/Webflow） | 各 CMS REST API | 程序员 | 2 人日 |
| `app/modules/billing_webhook` | Stripe Webhook 处理 | Stripe | 程序员 | 1 人日 |
| `app/schemas/` | Pydantic v2 请求/响应 schema | - | 程序员 | 2 人日 |
| `app/api/v1/` | REST 路由层（OpenAPI 自动生成） | 各 module | 程序员 | 2 人日 |

### 前端（Next.js 14 App Router）

| 模块 | 职责 | 估时 |
|------|------|------|
| `apps/web/app/(marketing)` | 落地页、定价页（SSG） | 2 人日 |
| `apps/web/app/(auth)` | 登录/注册页 | 1 人日 |
| `apps/web/app/(dashboard)/seo` | PSEO 内容工厂用户后台 | 4 人日 |
| `apps/web/app/(dashboard)/rewriter` | 长内容改写用户后台 | 4 人日 |
| `apps/web/app/(dashboard)/billing` | 订阅管理（嵌入 Stripe Portal） | 1 人日 |
| `apps/web/components/ui` | shadcn/ui 组件库 | 1 人日 |
| `apps/web/lib/api` | API 客户端封装（类型安全） | 1 人日 |

### 复用 AutoCorp 现有能力

| 模块 | 复用方式 |
|------|----------|
| `engine/llm_client.py` | 直接 import 作为 LLM 调用层 |
| `engine/secrets.py` | SecretsManager 复用密钥管理 |
| `engine/agents/` | Agent 编排能力作为 seo_content / content_rewriter 的内部引擎 |

## 二、接口定义（核心 API）

### 2.1 PSEO 内容工厂

#### `POST /api/v1/seo/keywords/research`
```json
// Request
{ "seed_keyword": "ethereum wallet", "country": "us", "limit": 50 }
// Response 200
{ "keywords": [
  { "keyword": "best ethereum wallet 2026", "difficulty": 28, "volume": 1200, "cpc": 2.4, "intent": "commercial" }
], "cluster_groups": [["...", "..."]] }
```

#### `POST /api/v1/seo/articles/generate`
```json
// Request
{ "keyword": "...", "word_count": 1500, "tone": "professional", "include_citations": true }
// Response 202（异步任务）
{ "task_id": "task_abc123", "status": "queued", "poll_url": "/api/v1/tasks/task_abc123" }
```

#### `POST /api/v1/seo/articles/publish`
```json
// Request
{ "article_id": "art_001", "cms": "wordpress", "site_url": "...", "credentials_ref": "ref://wp_creds_001" }
// Response 200
{ "published_url": "https://...", "post_id": 1234 }
```

### 2.2 长内容改写

#### `POST /api/v1/rewriter/transcribe`
```json
// Request（multipart/form-data）
file: <audio/video binary>, language: "auto"
// Response 200
{ "transcript_id": "tr_001", "segments": [{ "start": 0, "end": 12.3, "text": "..." }] }
```

#### `POST /api/v1/rewriter/repurpose`
```json
// Request
{ "transcript_id": "tr_001", "platforms": ["tiktok", "linkedin", "twitter"], "style_sample": "optional_ref" }
// Response 200
{ "outputs": [
  { "platform": "tiktok", "content": "...", "hook": "...", "hashtags": ["..."] }
] }
```

### 2.3 统一支付中心

#### `POST /api/v1/billing/checkout`
```json
// Request
{ "product": "seo_pro" | "rewriter_pro" | "...", "billing_cycle": "monthly" | "yearly", "success_url": "...", "cancel_url": "..." }
// Response 200
{ "checkout_url": "https://checkout.stripe.com/...", "session_id": "cs_test_..." }
```

#### `POST /api/v1/billing/webhook`（Stripe Webhook）
```json
// Request（Stripe 签名头）
{ "event_type": "checkout.session.completed", "customer": "cus_...", "amount": 2900 }
// Response 200
{ "received": true }
```

### 2.4 通用

- `GET /api/v1/health` → `{ "status": "ok", "version": "..." }`
- `GET /api/v1/tasks/{task_id}` → 异步任务状态轮询
- `GET /api/v1/me` → 当前用户信息（JWT 鉴权）

## 三、数据库 Schema（PostgreSQL via Supabase）

```sql
-- 用户（Supabase Auth 管理，仅扩展表）
CREATE TABLE profiles (
  id UUID PRIMARY KEY REFERENCES auth.users,
  email TEXT, plan TEXT DEFAULT 'free', created_at TIMESTAMPTZ DEFAULT now()
);

-- 订阅
CREATE TABLE subscriptions (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID REFERENCES profiles(id),
  product TEXT NOT NULL,  -- 'seo_pro' | 'rewriter_pro'
  stripe_customer_id TEXT, stripe_subscription_id TEXT,
  status TEXT, current_period_end TIMESTAMPTZ, created_at TIMESTAMPTZ DEFAULT now()
);

-- SEO 文章
CREATE TABLE seo_articles (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID, keyword TEXT, title TEXT, content TEXT,
  word_count INT, citations JSONB, status TEXT DEFAULT 'draft',
  created_at TIMESTAMPTZ DEFAULT now()
);

-- 关键词研究缓存
CREATE TABLE keyword_cache (
  keyword TEXT PRIMARY KEY, difficulty INT, volume INT, cpc NUMERIC,
  intent TEXT, fetched_at TIMESTAMPTZ DEFAULT now()
);

-- 改写任务
CREATE TABLE rewriter_tasks (
  id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  user_id UUID, source_type TEXT, transcript_id TEXT,
  outputs JSONB, status TEXT DEFAULT 'queued',
  created_at TIMESTAMPTZ DEFAULT now()
);
```

## 四、技术规范

1. **API 版本**：URL 路径版本 `/api/v1/`，破坏性变更走 v2
2. **错误格式**：统一 `{ "error": { "code": "...", "message": "...", "details": {} } }`
3. **鉴权**：JWT Bearer（Supabase Auth 签发），`GET /me` 必须鉴权
4. **限流**：免费用户 10 req/min，付费 100 req/min（基于 Redis 计数器，MVP 用内存降级）
5. **异步任务**：长耗时操作（文章生成、ASR）走任务队列，返回 task_id 轮询；MVP 用 Redis + RQ，规模化换 Celery
6. **密钥**：复用 AutoCorp SecretsManager，Stripe webhook secret、SerpAPI key、Deepgram key 全部 ref:// 引用，禁止入码
7. **测试**：pytest + httpx（API 集成）+ pytest-cov（覆盖率 ≥70%）；前端 Vitest + Playwright E2E
8. **CI/CD**：GitHub Actions → lint(ruff/black) → test → build → deploy(Fly.io)；前端 Vercel 自动部署
9. **日志**：structlog 结构化日志，请求 ID 贯穿；Sentry 错误监控

## 五、目录结构

```
autoCorp-daily/
├── apps/
│   └── web/                    # Next.js 14 前端
│       ├── app/(marketing)/
│       ├── app/(auth)/
│       ├── app/(dashboard)/
│       └── components/ui/
├── services/
│   └── api/                    # FastAPI 后端
│       ├── app/
│       │   ├── core/           # config, security
│       │   ├── db/             # supabase_client
│       │   ├── modules/        # auth, payment, seo_content, content_rewriter, llm_router, ...
│       │   ├── schemas/        # Pydantic v2
│       │   └── api/v1/         # 路由
│       ├── tests/
│       └── pyproject.toml
├── packages/
│   └── shared-types/          # 前后端共享 TS 类型（从 OpenAPI 生成）
├── engine/                     # 复用 AutoCorp 现有 Agent 编排
├── .github/workflows/
└── docker-compose.yml          # 本地开发（Postgres + Redis）
```

## 六、Sprint 计划（2 周一个 Sprint）

- **Sprint 1（W1-2）**：core/config + auth + payment 基础 + 前端骨架
- **Sprint 2（W3-4）**：seo_content 关键词研究 + 文章生成 MVP（REQ-001~003）
- **Sprint 3（W5-6）**：content_rewriter ASR + 改写 MVP（REQ-007~009）+ Stripe 订阅上线
- **Sprint 4（W7-8）**：CMS 发布集成（REQ-005）+ 内链自动化（REQ-006）+ 风格化改写（REQ-010）

## 七、质量门禁

- PR 必须通过：ruff + black + pytest（覆盖率 ≥70%）+ build
- 接口必须有 OpenAPI schema（FastAPI 强制）
- 关键路径（支付、文章生成）必须有 E2E 测试
- 密钥扫描（git-secrets）阻断敏感信息提交

## 4. 最终决策（CEO）
决策：approve
理由：
# CEO 立项评审决策

## 决策结果：**REVISE（有条件批准，需修订后执行）**

> 方案技术方向正确，但当前账本余额 **$0.00**，无法承担方案中的外部服务月费支出。需修订为「零成本启动 + 验证后追加投入」的分阶段计划。

## 一、评审理由

### ✅ 通过项
1. **战略对齐**：现金流优先 + 技术栈复用 90%，与公司「真实变现」目标一致
2. **架构合理**：单体 FastAPI + 模块化包结构，避免微服务过度工程，符合 CTO「简洁高效」原则
3. **复用现有资产**：直接 import `engine/llm_client.py` / `engine/secrets.py` / `engine/agents/`，不重复造轮子
4. **MVP 周期合理**：4-6 周交付双产品 MVP，节奏可控
5. **质量门禁完备**：PR lint+test+build、OpenAPI 强制、密钥扫描

### ❌ 需修订项
1. **资金缺口**：账本 $0，但方案隐含月费支出：
   - SerpAPI $75/月（最低档）
   - Supabase $25/月（Pro 档，免费档仅 500MB）
   - Vercel Pro $20/月（免费档商用受限）
   - Fly.io 按量（约 $10-30/月）
   - Deepgram 按 分钟计费
   - Stripe 抽成 2.9%+$0.30/笔（无月费但随交易）
   - 域名约 $10-15/年
   - **预估首月最低支出：$130-170**
2. **止损点缺失**：方案未定义「MVP 失败后的退出机制」
3. **ROI 预期未量化**：MRR $8,000 目标缺乏获客成本与转化漏斗假设
4. **LLM API 成本无预算上限**：Claude 3.5 + GPT-4o-mini 调用成本随用户量爆发，方案虽有「分级路由+缓存」缓解但未给硬性预算上限

## 二、修订要求（必须满足方可进入 Sprint 1）

### 修订点 1：分阶段预算授权

| 阶段 | 里程碑 | 预算上限 | 资金来源 |
|------|--------|----------|----------|
| Phase 0（W0） | 域名 + 免费档基础设施搭建 | **$15**（仅域名） | 用户提供（需 human_loop 确认） |
| Phase 1（W1-2） | auth + payment 骨架 + 前端骨架，全部用免费档（Supabase Free / Vercel Free / Fly.io 免费额度） | **$0** | 无 |
| Phase 2（W3-4） | seo_content MVP，SerpAPI 免费档 100 次/月 + 自建 SERP 抓取降级 | **$0** | 无 |
| Phase 3（W5-6） | content_rewriter MVP，Whisper API 免费额度 + Stripe 沙箱测试 | **$0** | 无 |
| Phase 4 | 首个付费用户到账后，用真实收入 $50 注入 SerpAPI 付费档 + Supabase Pro | **$50**（来自真实收入） | 真实收入再投资 |
| Phase 5 | MRR 达 $500 后，追加 Vercel Pro + Fly.io 扩容 | **$50/月** | 真实收入 |

**硬约束**：Phase 0-3 总支出 ≤ $15（仅域名）；Phase 4 前不得动用任何外部付费服务（除 Stripe 抽成随交易）。

### 修订点 2：止损机制

- **Sprint 2 结束（W4）**：若 seo_content MVP 无内测用户注册 → 暂停，重新评估 PMF
- **Sprint 4 结束（W8）**：若无付费用户（MRR = $0）→ 触发终止决策评审，考虑 pivot 或止损
- **MRR $0 持续 12 周**：强制终止项目，回收资源

### 修订点 3：LLM 成本硬上限

- **MVP 阶段**：LLM 月度调用预算上限 **$30**（用户自带 key 模式优先，BYOK）
- **规模化阶段**：LLM 成本不得超过当月 MRR 的 30%
- 实现：在 `llm_router` 模块加入预算计数器，超限自动降级到更便宜的模型或拒绝调用

### 修订点 4：获客成本与转化漏斗假设

- **获客渠道**（零成本优先）：
  1. Twitter/X 内容营销（AutoCorp 已有能力，每日产出推文）
  2. Reddit r/SaaS r/SEO r/Entrepreneur 社区运营
  3. ProductHunt 发布（一次性）
  4. SEO 自举：用候选 1 的产品为自己的内容站做 SEO
- **转化漏斗假设**（需 PM 在 Sprint 2 前补齐）：
  - 访客 → 注册：5%
  - 注册 → 试用：30%
  - 试用 → 付费：5%
  - 目标：4 周内 1000 访客 → 50 注册 → 15 试用 → 1 付费（验证 PMF）

## 三、资源分配决策

| 角色 | 分配 | 工时占比 |
|------|------|----------|
| 程序员 | 主力开发（后端 + 前端） | 80% |
| 架构师 | Sprint 1 评审 + 关键接口设计 | 10% |
| CTO | 技术选型终审 + 风险把控 | 5% |
| PM | Sprint 2 前补齐转化漏斗假设 + 用户调研 | 5% |
| COO | Phase 4 前准备零成本获客物料（Twitter/Reddit） | 并行 |
| CEO | Phase 4 注资决策 + 止损评审 | 关键节点 |

## 四、需用户确认的事项（human_loop 触发）

1. **域名注册**（Phase 0，约 $10-15/年）：需用户协助注册并指向 Vercel
2. **Stripe 账户注册**（Phase 1）：需用户提供真实 Stripe 凭证（sandbox 可先用）
3. **Supabase 账户**（Phase 1）：免费档可由 AI 自主注册，但需用户邮箱验证
4. **Phase 4 注资决策**：首个付费用户到账后，是否将 $50 真实收入再投入

## 五、立项编号与下一步

- **立项编号**：PRJ-2026-07-04-001
- **状态**：REVISE → 待架构师/PM 补齐修订点 2/3/4 后转 APPROVED
- **下一步**：
  1. 架构师：在 `app/modules/llm_router` 增加 LLM 预算计数器设计
  2. PM：补齐转化漏斗假设与获客 KPI（Sprint 2 前）
  3. 程序员：按修订后预算启动 Sprint 1（全部免费档）
  4. COO：并行准备 Twitter/Reddit 引流物料（零成本）

## 六、不批准的事项

- **不批准**任何超过 $15 的 Phase 0-3 支出
- **不批准**自建代理池（用 SerpAPI 免费档 + 自建降级）
- **不批准**Bright Data（$500/月，远超预算，二期再议）
- **不批准**视频渲染（REQ-011，二期）
- **不批准**语音模拟面试（REQ-014，二期）

---
**CEO 签批**：修订点 1-4 满足后自动转 APPROVED，无需再次评审。

注意：此任务可能超出 ceo 职责范围，建议转交对应角色。

## 5. 营收驾驶舱（每日必看）
### 钱包余额（2026-07-04）
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
- [ ] Day 1（2026-07-04）：SaaS 选型指南英文长文系列（CRM/Help Desk/PM 三类各 1 篇，2000-2400 词，注册 G2/Capterra affiliate）
- [ ] Day 1（2026-07-04）：AI 工具横向评测周报 Newsletter MVP（10 评测任务 + 多 agent 跑批 + beehiiv 上架）
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
> 扫描日期：2026-07-04 | 战略转向决策：company/decisions/strategic-pivot-to-value-chain-entry-2026-06-30.md


## 7. 价值链切入点执行进度（2026-06-30 新增）
| 排名 | 切入点 | 行业 | 启动日 | 状态 | 进度 | 预期收益 |
|------|--------|------|--------|------|------|---------|
| 1 | SaaS 选型指南英文长文系列 | SaaS | Day 1 (2026-07-04) | 待启动 | 0% | $5-20 affiliate/篇 |
| 2 | Shopify 独立站 SEO 优化指南系列 | 电商跨境 | Day 2 | 待启动 | 0% | $5-20 affiliate/篇 |
| 3 | 跨境支付方案对比系列 | 金融科技 | Day 3 | 待启动 | 0% | $30-150 affiliate |
| 4 | Claude vs GPT-5 vs Gemini 实测对比系列 | AI 应用层 | Day 3 | 待启动 | 0% | $5-20 affiliate |
| 5 | 独立站博客 SEO 内容代运营 | 电商跨境 | Day 3 | 待启动 | 0% | $200-500/月 |

> 数据源：task_queue.yaml（task_type=value_chain_entry）+ value-chain-entry-opportunities.md Top 5 排序
> 首笔收入检查节点：Day 7（2026-07-04 + 7 天）


## 8. 可持续产品开发进度（2026-06-30 新增）
| 排名 | 产品 | 类型 | 切入行业 | MVP 启动日 | 状态 | 进度 | 预期收益 |
|------|------|------|---------|-----------|------|------|---------|
| 1 | AI 工具横向评测周报 Newsletter | 内容资产 | AI 应用层 | Day 1 (2026-07-04) | MVP 待启动 | 0% | $9/月订阅 + $5-20 affiliate |
| 2 | CVE 漏洞周报订阅 | 内容资产 | 网络安全 | Day 2 | MVP 待启动 | 0% | $19/月订阅 |
| 3 | 跨境支付对比站（压缩版 MVP） | 聚合 | 金融科技 | Day 3 | MVP 待启动 | 0% | $30-150 affiliate + $10-30 广告 |

> 数据源：task_queue.yaml（task_type=sustainable_product）+ sustainable-revenue-product-ideas.md Top 3 排序
> 首笔收入检查节点：Day 30（2026-07-04 + 30 天）


## 当日任务清单
- [ ] task-001: `GET /api/v1/health` → `{ "status": "ok", "version": "..." }` → 负责人: programmer（medium）
- [ ] task-002: `GET /api/v1/tasks/{task_id}` → 异步任务状态轮询 → 负责人: programmer（medium）
- [ ] task-003: `GET /api/v1/me` → 当前用户信息（JWT 鉴权） → 负责人: programmer（medium）
- [ ] task-004: - 用户（Supabase Auth 管理，仅扩展表） → 负责人: programmer（medium）
- [ ] task-005: - 订阅 → 负责人: programmer（medium）
- [ ] task-006: - SEO 文章 → 负责人: programmer（medium）
- [ ] task-007: - 关键词研究缓存 → 负责人: programmer（medium）
- [ ] task-008: - 改写任务 → 负责人: programmer（medium）
- [ ] task-009: **API 版本**：URL 路径版本 `/api/v1/`，破坏性变更走 v2 → 负责人: programmer（medium）
- [ ] task-010: **错误格式**：统一 `{ "error": { "code": "...", "message": "...", "details": {} } }` → 负责人: programmer（medium）
- [ ] task-011: **鉴权**：JWT Bearer（Supabase Auth 签发），`GET /me` 必须鉴权 → 负责人: programmer（medium）
- [ ] task-012: **限流**：免费用户 10 req/min，付费 100 req/min（基于 Redis 计数器，MVP 用内存降级） → 负责人: programmer（medium）
- [ ] task-013: **异步任务**：长耗时操作（文章生成、ASR）走任务队列，返回 task_id 轮询；MVP 用 Redis + RQ，规模化换 Celery → 负责人: programmer（medium）
- [ ] task-014: **密钥**：复用 AutoCorp SecretsManager，Stripe webhook secret、SerpAPI key、Deepgram key 全部 ref:// 引用，禁止入码 → 负责人: programmer（medium）
- [ ] task-015: **测试**：pytest + httpx（API 集成）+ pytest-cov（覆盖率 ≥70%）；前端 Vitest + Playwright E2E → 负责人: tester（medium）
- [ ] task-016: **CI/CD**：GitHub Actions → lint(ruff/black) → test → build → deploy(Fly.io)；前端 Vercel 自动部署 → 负责人: tester（medium）
- [ ] task-017: **日志**：structlog 结构化日志，请求 ID 贯穿；Sentry 错误监控 → 负责人: programmer（medium）
- [ ] task-018: **Sprint 1（W1-2）**：core/config + auth + payment 基础 + 前端骨架 → 负责人: programmer（medium）
- [ ] task-019: **Sprint 2（W3-4）**：seo_content 关键词研究 + 文章生成 MVP（REQ-001~003） → 负责人: programmer（medium）
- [ ] task-020: **Sprint 3（W5-6）**：content_rewriter ASR + 改写 MVP（REQ-007~009）+ Stripe 订阅上线 → 负责人: programmer（medium）
- [ ] task-021: **Sprint 4（W7-8）**：CMS 发布集成（REQ-005）+ 内链自动化（REQ-006）+ 风格化改写（REQ-010） → 负责人: programmer（medium）
- [ ] task-022: PR 必须通过：ruff + black + pytest（覆盖率 ≥70%）+ build → 负责人: tester（medium）
- [ ] task-023: 接口必须有 OpenAPI schema（FastAPI 强制） → 负责人: architect（medium）
- [ ] task-024: 关键路径（支付、文章生成）必须有 E2E 测试 → 负责人: tester（medium）
- [ ] task-025: 密钥扫描（git-secrets）阻断敏感信息提交 → 负责人: programmer（medium）
- [ ] task-026: 按既定方案推进开发 → 负责人: programmer（high）
