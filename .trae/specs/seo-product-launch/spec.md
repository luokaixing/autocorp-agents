# SEO Product Launch Spec

## Why
首日 MVP 已完成 SEO 文章生成核心能力，但缺乏用户获取入口与收款能力。需要：
1. 开发 Landing Page（本地预览版）让产品可视化，用户能看到价值主张、定价、Demo
2. 集成 PayPal 沙盒收款，验证"用户访问 → 付费 → 生成文章"完整商业闭环
3. 设计按篇 + 订阅混合变现模型（试水用户 + 长期用户双轨）

## What Changes

### ADDED Requirements

#### Requirement: Landing Page 本地预览
- 静态 HTML + 内嵌 CSS/JS，无构建依赖
- 含 Hero / Features / Pricing / Demo / FAQ / CTA 六个区块
- 内嵌 PayPal JS SDK 按钮（按篇 + 订阅两档）
- 本地预览服务器（Python http.server 或 Flask），端口 8000
- 移动端响应式

#### Requirement: PayPal 沙盒集成
- 复用 `engine/payments/paypal.py` 现有 PayPalClient（沙盒默认）
- 新增 `create_subscription(plan_id)` 创建订阅
- 新增 `check_subscription(subscription_id)` 查询订阅状态
- 订阅计划预定义：$29/月（50 篇）/ $79/月（200 篇）
- 按篇订单：$2/篇（用户付款后生成 1 篇文章）

#### Requirement: 订阅额度管理
- 新增 `seo_generator/subscription.py`
- 用户订阅成功后记录到 `company/projects/seo-content-generator/data/subscriptions.json`
- 每次生成文章扣减额度，额度耗尽提示续费
- 订阅状态：active / expired / cancelled
- 支持按 email 识别用户

#### Requirement: E2E 商业闭环
- 用户访问 Landing Page → 选择套餐 → PayPal 沙盒支付 → 回调生成文章
- 完整流程：浏览 → 付费 → 输入关键词 → 生成 → 输出文章
- 沙盒模式下用 PayPal 测试账号完成支付

### MODIFIED Requirements

#### Requirement: PayPalClient 扩展订阅能力
现有 `engine/payments/paypal.py` 仅支持单次订单。扩展为：
- 保留 `create_order` / `capture_order` / `check_order`（按篇用）
- 新增 `create_subscription(plan_id, subscriber_email)` 返回 {subscription_id, approve_url}
- 新增 `check_subscription(subscription_id)` 返回订阅状态
- 沙盒模式默认开启，真实模式需 `--live` flag

## Impact
- **新增代码**:
  - `company/projects/seo-content-generator/landing/index.html`（Landing Page）
  - `company/projects/seo-content-generator/landing/server.py`（本地预览服务器）
  - `company/projects/seo-content-generator/landing/thank-you.html`（支付成功页）
  - `company/projects/seo-content-generator/seo_generator/subscription.py`（订阅管理）
  - `company/projects/seo-content-generator/seo_generator/payment_bridge.py`（PayPal 与产品 CLI 的桥接）
  - `company/projects/seo-content-generator/tests/test_subscription.py`
  - `company/projects/seo-content-generator/tests/test_payment_bridge.py`
- **修改代码**:
  - `engine/payments/paypal.py`（新增 create_subscription / check_subscription）
  - `company/projects/seo-content-generator/seo_generator/cli.py`（新增 subscribe / generate-paid 命令）
- **数据存储**:
  - `company/projects/seo-content-generator/data/subscriptions.json`（订阅记录）
  - `company/projects/seo-content-generator/data/orders.json`（按篇订单记录）
- **不影响**: AutoCorp 核心引擎（engine/agents/*、engine/orchestrator.py 等）

## 设计约束

1. **沙盒优先**: 当前所有 PayPal 调用走沙盒，过两天切换到真实 key 时仅需改 secrets 配置，不改代码
2. **本地预览**: Landing Page 不部署到公网，本地 `py landing/server.py` 启动预览
3. **零外部依赖**: 不引入 Flask/Django 等 Web 框架，用标准库 http.server
4. **额度即信任**: 沙盒模式下用户额度记录在本地 JSON，真实模式需对接数据库（后续阶段）
5. **安全隔离**: PayPal client_id 可暴露在前端（公开标识），client_secret 仅存 `.secrets/`
6. **可扩展**: 支付桥接层抽象化，后续可接入 Stripe 而不重写业务逻辑

## 商业模型设计（基于市场分析）

### 定价策略（结合 seed-2026.md 赛道 2 分析）
| 套餐 | 价格 | 额度 | 目标用户 | 转化漏斗 |
|------|------|------|----------|----------|
| 按篇试水 | $2 | 1 篇 | 试水用户 | 顶部流量 |
| Starter | $29/月 | 50 篇 | 独立站长 | 中部转化 |
| Pro | $79/月 | 200 篇 | SEO 机构 | 底部高客单 |

### 转化路径
1. Landing Page 浏览 → 点击"Try Free Demo"（无付费，生成 1 篇示例）
2. 满意后点"Buy 1 Article $2"（PayPal 沙盒支付）
3. 支付成功 → 输入关键词 → 生成文章 → 展示结果
4. 引导订阅 $29/月（首次订阅送 10 篇额外额度）

### KPI（30 天）
- Landing Page 访问 → Demo 转化率：30%
- Demo → 按篇付费转化率：10%
- 按篇 → 订阅转化率：20%
- 目标：50 付费用户，MRR $500
