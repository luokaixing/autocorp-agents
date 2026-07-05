# Tasks - SEO Product Launch

> 原则：本地可验证优先，沙盒模式跑通完整商业闭环，过两天切换真实 key 时零代码改动。
> 依赖：基于已完成的 SEO Content Generator MVP（`company/projects/seo-content-generator/`）。

## 阶段一：PayPal 沙盒订阅能力扩展

- [x] Task 1: 扩展 PayPalClient 支持订阅 ✅
  - [x] SubTask 1.1: 在 `engine/payments/paypal.py` 新增 `create_subscription(plan_id, subscriber_email)` 方法
  - [x] SubTask 1.2: 新增 `check_subscription(subscription_id)` 方法查询订阅状态
  - [x] SubTask 1.3: 预定义订阅计划（STARTER_MONTHLY $29/50篇、PRO_MONTHLY $79/200篇）
  - [x] SubTask 1.4: 沙盒模式下用 PayPal Billing API（/v1/billing/subscriptions）
  - [x] SubTask 1.5: 编写单元测试覆盖订阅创建与查询（mock API）— 15 个测试通过
  - [x] SubTask 1.6: 验证真实 key 切换路径：仅改 `.secrets/secrets.json` 即可切换沙盒/正式

## 阶段二：订阅额度管理

- [x] Task 2: 实现订阅额度管理器 ✅
  - [x] SubTask 2.1: 创建 `seo_generator/subscription.py`，实现 SubscriptionManager 类
  - [x] SubTask 2.2: 订阅记录存储 `data/subscriptions.json`（email / plan / quota / used / status / started_at）
  - [x] SubTask 2.3: `add_subscription(email, plan_id, subscription_id)` 新增订阅
  - [x] SubTask 2.4: `consume_quota(email)` 扣减额度，返回剩余
  - [x] SubTask 2.5: `check_quota(email)` 查询剩余额度
  - [x] SubTask 2.6: `is_active(email)` 判断订阅是否有效（未过期且 status=active）
  - [x] SubTask 2.7: 编写单元测试（新增/扣减/额度耗尽/过期）— 13 个测试通过

## 阶段三：支付桥接层

- [x] Task 3: 实现支付与产品的桥接 ✅
  - [x] SubTask 3.1: 创建 `seo_generator/payment_bridge.py`，实现 PaymentBridge 类
  - [x] SubTask 3.2: `create_article_order(email, keyword, lang)` 创建按篇订单（$2）
  - [x] SubTask 3.3: `create_subscription_order(email, plan_id)` 创建订阅订单
  - [x] SubTask 3.4: `handle_payment_success(order_id)` 支付成功回调：按篇→生成文章；订阅→加额度
  - [x] SubTask 3.5: `generate_for_paid_user(email, keyword, lang)` 付费用户生成文章（校验额度）
  - [x] SubTask 3.6: 编写单元测试（按篇流程、订阅流程、额度耗尽场景）— 18 个测试通过

## 阶段四：Landing Page 开发

- [x] Task 4: 开发 Landing Page 静态页面 ✅
  - [x] SubTask 4.1: 创建 `landing/index.html`，含 6 个区块（Hero / Features / Pricing / Demo / FAQ / CTA）
  - [x] SubTask 4.2: Hero 区：产品名 + 一句话价值主张 + "Try Free Demo" CTA
  - [x] SubTask 4.3: Features 区：3 个核心功能（关键词分析 / 文章生成 / SEO 评分）
  - [x] SubTask 4.4: Pricing 区：3 个套餐卡片（按篇 $2 / Starter $29 / Pro $79），含 PayPal 按钮占位
  - [x] SubTask 4.5: Demo 区：内嵌表单（关键词输入），提交后调用本地 API 生成示例文章片段
  - [x] SubTask 4.6: FAQ 区：6 个常见问题（什么是 SEO 评分 / 支持哪些语言 / 如何付费 / 退款政策 / 数据隐私 / 与 Surfer SEO 区别）
  - [x] SubTask 4.7: 响应式 CSS（移动端适配），无外部框架（纯 CSS）
  - [x] SubTask 4.8: 内嵌 PayPal JS SDK（沙盒），按篇按钮 + 订阅按钮

## 阶段五：本地预览服务器

- [x] Task 5: 实现本地预览服务器 ✅
  - [x] SubTask 5.1: 创建 `landing/server.py`，基于 http.server.BaseHTTPRequestHandler
  - [x] SubTask 5.2: 路由：GET / 返回 index.html；GET /thank-you.html 返回支付成功页
  - [x] SubTask 5.3: API 路由：POST /api/demo 接收关键词，调用 SEO Generator 生成文章片段（前 500 字）
  - [x] SubTask 5.4: API 路由：POST /api/paypal/create-order 创建按篇订单
  - [x] SubTask 5.5: API 路由：POST /api/paypal/capture 捕获订单并触发文章生成
  - [x] SubTask 5.6: API 路由：POST /api/paypal/create-subscription 创建订阅
  - [x] SubTask 5.7: 静态资源服务（CSS/JS/图片）
  - [x] SubTask 5.8: 启动后打印访问地址 `http://localhost:8000`

## 阶段六：支付成功页与完整闭环

- [x] Task 6: 开发支付成功页与闭环验证 ✅
  - [x] SubTask 6.1: 创建 `landing/thank-you.html`，展示支付成功 + 文章生成入口
  - [x] SubTask 6.2: 支付成功后跳转到文章生成表单（输入关键词）
  - [x] SubTask 6.3: 生成完成后展示完整 SEO 文章 + 评分 + 下载链接
  - [x] SubTask 6.4: 按篇支付闭环：浏览 → 付费 $2 → 输入关键词 → 生成 → 下载
  - [x] SubTask 6.5: 订阅支付闭环：浏览 → 订阅 $29 → 输入关键词 → 扣额度 → 生成 → 下载

## 阶段七：CLI 集成

- [x] Task 7: 扩展 CLI 支持付费生成 ✅
  - [x] SubTask 7.1: `cli.py` 新增 `subscribe` 命令（创建订阅）
  - [x] SubTask 7.2: `cli.py` 新增 `generate-paid` 命令（校验额度后生成）
  - [x] SubTask 7.3: `cli.py` 新增 `quota` 命令（查询剩余额度）
  - [x] SubTask 7.4: `cli.py` 新增 `landing` 命令（启动本地预览服务器）
  - [x] SubTask 7.5: 验证所有命令在沙盒模式下可用

## 阶段八：端到端验证

- [x] Task 8: 端到端验证 ✅
  - [x] SubTask 8.1: 单元测试全部通过（PayPal 15 + Subscription 13 + PaymentBridge 18 = 46 个新测试，主项目 31 个测试）
  - [x] SubTask 8.2: 启动本地服务器 `py -m seo_generator landing`，访问 http://127.0.0.1:8000
  - [x] SubTask 8.3: Landing Page 6 区块渲染正确，响应式正常
  - [x] SubTask 8.4: Demo 表单提交生成示例文章片段（SEO 评分 100，1701 字）
  - [x] SubTask 8.5: PayPal 沙盒按钮跳转支付页（沙盒测试账号登录）
  - [x] SubTask 8.6: 沙盒支付成功 → 回调 → 生成完整文章 → 下载
  - [x] SubTask 8.7: 订阅支付成功 → 额度记录 → 多次生成扣减额度
  - [x] SubTask 8.8: 真实 key 切换验证：仅改 secrets 配置，代码无改动

> checklist.md 69/69 检查点全部通过 ✅

# Task Dependencies

- Task 1（PayPal 订阅扩展）独立，最高优先级
- Task 2（订阅额度管理）独立，可与 Task 1 并行
- Task 3（支付桥接层）依赖 Task 1、Task 2
- Task 4（Landing Page）独立，可与 Task 1-3 并行
- Task 5（本地服务器）依赖 Task 3、Task 4
- Task 6（支付成功页）依赖 Task 5
- Task 7（CLI 集成）依赖 Task 3、Task 5
- Task 8（端到端验证）依赖 Task 1-7

# 并行化建议

- 第一波并行：Task 1 + Task 2 + Task 4（互不依赖）
- 第二波：Task 3（依赖 Task 1+2）
- 第三波：Task 5 + Task 7（依赖 Task 3+4）
- 第四波：Task 6（依赖 Task 5）
- 第五波：Task 8（依赖全部）
