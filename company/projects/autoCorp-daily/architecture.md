# 模块设计文档：autoCorp-daily 架构设计

# 模块设计文档：autoCorp-daily

> 基于 PM 选题 + CEO 修订决策（PRJ-2026-07-04-001，REVISE→待 APPROVED）
> 原则：单体 FastAPI + 模块化包结构，零成本启动（Phase 0-3 仅域名 $15）

## 一、模块清单与职责说明

### M1. `app.core.config` — 配置中心
- **职责**：环境变量加载、密钥 ref:// 解析、特性开关
- **依赖**：AutoCorp `engine/secrets.py`（SecretsManager 复用）
- **技术栈**：pydantic-settings

### M2. `app.core.security` — 安全与限流
- **职责**：JWT 校验（Supabase Auth 签发）、CORS、内存限流（免费 10/min，付费 100/min）
- **依赖**：Supabase Auth JWT 公钥、M1
- **技术栈**：fastapi-security、slowapi（限流）

### M3. `app.db.supabase_client` — 数据访问层
- **职责**：Supabase 客户端单例、仓储基类（CRUD 泛型）、事务封装
- **依赖**：supabase-py、M1

### M4. `app.modules.auth` — 用户与授权
- **职责**：注册/登录/登出、JWT 刷新、产品矩阵授权（REQ-021 基础）
- **依赖**：Supabase Auth、M2、M3

### M5. `app.modules.payment` — 统一支付中心（REQ-020，P0 基础设施）
- **职责**：Stripe Checkout 创建、订阅管理、Webhook 签名校验、订阅状态同步到 `subscriptions` 表
- **依赖**：Stripe SDK、M3、M1（密钥 ref://）
- **预算约束**：Stripe 抽成 2.9%+$0.30/笔，无月费；sandbox 优先

### M6. `app.modules.llm_router` — LLM 多模型路由（含预算计数器，CEO 修订点 3）
- **职责**：
  - 多模型路由（Claude 3.5 写作 / GPT-4o-mini 改写与结构化）
  - 结果缓存（Redis，MVP 内存降级）
  - **预算计数器**：MVP 月度上限 $30，规模化 ≤ 当月 MRR 30%，超限自动降级或拒绝
  - BYOK 模式（用户自带 key 优先，不计入预算）
- **依赖**：AutoCorp `engine/llm_client.py`（LLMClient 复用）、M3（预算持久化）
- **接口**：
  ```python
  class LLMRouter:
      async def chat(self, messages, model_tier="default", user_id=None) -> LLMResponse
      async def get_budget_usage(self, user_id=None) -> BudgetUsage
  ```

### M7. `app.modules.serp_fetcher` — SERP 抓取调度
- **职责**：SerpAPI 封装（免费档 100 次/月）、结果缓存到 `keyword_cache` 表、自建抓取降级
- **依赖**：SerpAPI SDK、M3、M1（密钥 ref://）
- **预算约束**：Phase 0-3 仅用免费档；Phase 4 后用真实收入 $50/月扩容

### M8. `app.modules.seo_content` — PSEO 内容工厂核心（REQ-001~006）
- **职责**：关键词聚类 → LLM 大纲 → 分段生成 → 实体图谱注入 → 引用来源标注 → 内链自动化
- **依赖**：M6（LLM 路由）、M7（SERP）、M3（持久化）、AutoCorp `engine/agents/`
- **核心接口**：
  ```python
  class SEOContentService:
      async def research_keywords(self, seed: str, limit: int=50) -> KeywordResearchResp
      async def generate_article(self, req: ArticleGenReq) -> TaskId  # 异步
      async def publish_article(self, article_id, cms, creds_ref) -> PublishResp
  ```

### M9. `app.modules.asr_dispatcher` — ASR 调度
- **职责**：Deepgram 主（$0.0043/分钟）+ Whisper API 降级；音频/视频上传转写
- **依赖**：Deepgram SDK、OpenAI Whisper、M1（密钥）、M3（持久化 transcript）
- **预算约束**：MVP 用 Whisper 免费额度；规模化后切 Deepgram

### M10. `app.modules.content_rewriter` — 长内容改写核心（REQ-007~011）
- **职责**：语义分段 → 主题提取 → 平台风格化改写（TikTok/LinkedIn/Twitter）→ 风格学习（few-shot）
- **依赖**：M9（ASR）、M6（LLM 路由）、M3、AutoCorp `engine/agents/`
- **核心接口**：
  ```python
  class RewriterService:
      async def transcribe(self, file: UploadFile, lang="auto") -> TranscriptResp
      async def repurpose(self, transcript_id, platforms, style_sample=None) -> list[RepurposeOutput]
  ```

### M11. `app.modules.cms_publisher` — CMS 发布集成（REQ-005）
- **职责**：WordPress REST API / Webflow API 发布、凭证 ref:// 管理
- **依赖**：httpx、M1（密钥）

### M12. `app.modules.billing_webhook` — Stripe Webhook
- **职责**：接收 Stripe 事件、签名校验、订阅状态同步、真实收入入账（调用 `ledger.income_real`）
- **依赖**：Stripe SDK、M3、AutoCorp `engine/ledger.py`

### M13. `app.api.v1` — REST 路由层
- **职责**：OpenAPI schema 自动生成、路由聚合、依赖注入
- **依赖**：所有 modules

## 二、接口定义（请求/响应 schema 摘要）

### 2.1 关键词研究
```
POST /api/v1/seo/keywords/research
Request: { seed_keyword: str, country: str="us", limit: int=50 }
Response 200: { keywords: [{keyword, difficulty, volume, cpc, intent}], cluster_groups: [[str]] }
```

### 2.2 文章生成（异步）
```
POST /api/v1/seo/articles/generate
Request: { keyword, word_count=1500, tone="professional", include_citations=true }
Response 202: { task_id, status="queued", poll_url="/api/v1/tasks/{task_id}" }
```

### 2.3 ASR 转写
```
POST /api/v1/rewriter/transcribe (multipart/form-data)
Request: file=<binary>, language="auto"
Response 200: { transcript_id, segments:[{start, end, text}] }
```

### 2.4 多平台改写
```
POST /api/v1/rewriter/repurpose
Request: { transcript_id, platforms:["tiktok","linkedin","twitter"], style_sample=null }
Response 200: { outputs:[{platform, content, hook, hashtags[]}] }
```

### 2.5 Stripe Checkout
```
POST /api/v1/billing/checkout
Request: { product:"seo_pro"|"rewriter_pro", billing_cycle:"monthly"|"yearly", success_url, cancel_url }
Response 200: { checkout_url, session_id }
```

### 2.6 通用
```
GET /api/v1/health → { status, version }
GET /api/v1/tasks/{task_id} → { task_id, status, result? }
GET /api/v1/me → { user_id, email, plan }  (JWT)
```

## 三、依赖关系图

```
M1 config ─┬─ M2 security ─ M4 auth ─┐
          ├─ M3 db ─────────────────┤
          └─ M5 payment ─ M12 webhook ─ ledger

M6 llm_router ─┬─ M8 seo_content ─ M7 serp_fetcher
              └─ M10 content_rewriter ─ M9 asr_dispatcher

M11 cms_publisher ← M8
M13 api/v1 ← 所有 modules
```

## 四、技术栈建议

| 层 | 选型 | 理由 |
|----|------|------|
| 前端 | Next.js 14 + TailwindCSS + shadcn/ui | SSG 适配 SEO 内容站 |
| 后端 | FastAPI + Pydantic v2 | 复用 engine/ Python 资产 |
| DB | Supabase（PostgreSQL） | 免费档足够 MVP |
| LLM | OpenAI 兼容 + 多模型路由 | 不绑死供应商 |
| ASR | Deepgram + Whisper 降级 | 成本与实时性平衡 |
| SERP | SerpAPI 免费档 | 零成本启动 |
| 支付 | Stripe Checkout + Portal | PCI 合规免处理 |
| 部署 | Vercel + Fly.io + Cloudflare Pages | 免费档启动 |
| 密钥 | AutoCorp SecretsManager（ref://） | 物理隔离 |

## 五、目录结构

```
autoCorp-daily/
├── apps/web/                  # Next.js
│   ├── app/(marketing)/
│   ├── app/(auth)/
│   ├── app/(dashboard)/{seo,rewriter,billing}/
│   └── components/ui/
├── services/api/              # FastAPI
│   ├── app/{core,db,modules,schemas,api/v1}/
│   ├── tests/
│   └── pyproject.toml
├── packages/shared-types/     # 从 OpenAPI 生成 TS 类型
├── engine/                    # 复用 AutoCorp Agent 编排
├── .github/workflows/
└── docker-compose.yml
```

## 六、测试要求

| 层 | 工具 | 覆盖率 |
|----|------|--------|
| 后端单元 | pytest + pytest-cov | ≥70% |
| 后端集成 | httpx + pytest | 关键路径必测 |
| 前端单元 | Vitest | ≥60% |
| E2E | Playwright | 支付+文章生成+改写关键路径 |
| 契约 | OpenAPI schema 校验 | 强制 |
| 密钥扫描 | git-secrets | 阻断提交 |

## 七、CEO 修订决策的落地点

| 修订点 | 落地模块 |
|--------|----------|
| 零成本启动（Phase 0-3） | M7 SerpAPI 免费档 + M9 Whisper 免费额度 + 全部用 Vercel/Supabase/Fly 免费档 |
| LLM 预算计数器 | M6 `llm_router` 内置 BudgetCounter，超限降级 |
| BYOK 模式 | M6 支持 user 自带 key（不计预算） |
| 止损机制 | Sprint 2/4 评审节点（COO 输出 KPI 触发评审） |
| 真实收入再投资 | M12 webhook 入账后，Phase 4 解锁付费档 |

## 八、Sprint 分解

- **Sprint 1（W1-2）**：M1+M2+M3+M4+M5 骨架 + M13 路由 + 前端骨架
- **Sprint 2（W3-4）**：M7+M8（REQ-001~003）+ M6 预算计数器
- **Sprint 3（W5-6）**：M9+M10（REQ-007~009）+ Stripe 订阅上线
- **Sprint 4（W7-8）**：M11（REQ-005）+ 内链（REQ-006）+ 风格化（REQ-010）
