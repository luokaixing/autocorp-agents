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