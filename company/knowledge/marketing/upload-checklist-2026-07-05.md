# Fiverr + Gumroad 上架操作清单（PayPal Live 已就绪）

> 日期：2026-07-05
> PayPal Live：✅ 已通（access_token + 创建订单 + 查询订单全部 OK）
> 战略依据：company/decisions/strategic-pivot-no-domain-no-stripe-2026-07-04.md
> 上架物料：✅ 全部就绪（9 张图 + 1 份 PDF + 2 份 gig 文案）

---

## 一、已就绪的上架物料

### 1.1 Fiverr Gig 1：加密市场深度分析报告
- 文案：[company/knowledge/marketing/fiverr-gig-crypto-analysis-2026-07-04.md](file:///d:\autoCompany\company\knowledge\marketing\fiverr-gig-crypto-analysis-2026-07-04.md)
- 产品图：
  - 封面：[images/fiverr_crypto_cover.jpg](file:///d:\autoCompany\company\knowledge\marketing\images\fiverr_crypto_cover.jpg)
  - 内页 1（三档定价）：[images/fiverr_crypto_inner_1.jpg](file:///d:\autoCompany\company\knowledge\marketing\images\fiverr_crypto_inner_1.jpg)
  - 内页 2（可覆盖赛道）：[images/fiverr_crypto_inner_2.jpg](file:///d:\autoCompany\company\knowledge\marketing\images\fiverr_crypto_inner_2.jpg)

### 1.2 Fiverr Gig 2：AI Agent 开发咨询
- 文案：[company/knowledge/marketing/fiverr-gig-ai-agent-consulting-2026-07-04.md](file:///d:\autoCompany\company\knowledge\marketing\fiverr-gig-ai-agent-consulting-2026-07-04.md)
- 产品图：
  - 封面：[images/fiverr_agent_cover.jpg](file:///d:\autoCompany\company\knowledge\marketing\images\fiverr_agent_cover.jpg)
  - 内页 1（技术栈）：[images/fiverr_agent_inner_1.jpg](file:///d:\autoCompany\company\knowledge\marketing\images\fiverr_agent_inner_1.jpg)
  - 内页 2（交付案例）：[images/fiverr_agent_inner_2.jpg](file:///d:\autoCompany\company\knowledge\marketing\images\fiverr_agent_inner_2.jpg)

### 1.3 Gumroad PDF 产品
- 产品规划：[company/knowledge/marketing/gumroad-product-plan-2026-07-04.md](file:///d:\autoCompany\company\knowledge\marketing\gumroad-product-plan-2026-07-04.md)
- PDF 报告：[company/products/gumroad/2026-H2-crypto-three-mainlines.pdf](file:///d:\autoCompany\company\products\gumroad\2026-H2-crypto-three-mainlines.pdf)（157.6 KB）
- 产品图：
  - 封面：[images/gumroad_pdf_cover.jpg](file:///d:\autoCompany\company\knowledge\marketing\images\gumroad_pdf_cover.jpg)
  - 内页预览 1（协议对比表）：[images/gumroad_preview_1.jpg](file:///d:\autoCompany\company\knowledge\marketing\images\gumroad_preview_1.jpg)
  - 内页预览 2（三大主线概览）：[images/gumroad_preview_2.jpg](file:///d:\autoCompany\company\knowledge\marketing\images\gumroad_preview_2.jpg)

### 1.4 PayPal Live 凭证（已验证可用）
- Client ID：`${PAYPAL_CLIENT_ID}`（存于 `.secrets/secrets.json`，不公开）
- Client Secret：[REDACTED]
- 测试结果：access_token 97 字符 + 订单 `6H707311BH815501H` 创建成功 + 查询订单 OK
- CLI 验证脚本：[scripts/test_paypal_live.py](file:///d:\autoCompany\scripts\test_paypal_live.py)

---

## 二、Fiverr 上架操作步骤（你需要手动操作）

### 步骤 1：注册 Fiverr 账号
- 访问：https://www.fiverr.com/join
- 用 PayPal 邮箱注册（重要：与 PayPal 同邮箱，方便后续提现）
- 完成邮箱验证 + 手机号验证
- 选择身份：**Seller**（卖家）

### 步骤 2：完善卖家 Profile
- 上传头像（建议专业一些的头像或 Logo）
- 填写简介：
  ```
  Independent AI research desk operator. I run AutoCorp, an autonomous AI company that publishes weekly crypto market research on Mirror.xyz and Paragraph. My reports are non-marketing, research-grade, and read by DAOs, small funds, and individual operators.

  I also architect production AI Agent systems using CrewAI, AutoGen, and LangGraph - not theory, real shipped code.

  Languages: English (native), Mandarin (fluent)
  ```
- 关联 PayPal：在 Settings → Billing → PayPal 关联你的 PayPal 账号

### 步骤 3：创建 Gig 1（加密市场分析）
1. 点击 "Start Selling" → "Create New Gig"
2. **Overview**：
   - Category：Writing → Articles & Blog Posts → Business Writing
   - Service Type：Writing
   - Gig Title：`I will write a deep analysis report on crypto market narratives RWA DePIN AI Agent`
   - Tags：`crypto analysis, market research, defi, rwa, depin`
3. **Pricing**（3 档）：
   - Basic：$50 / 2 days / 5-page report / 1 revision
   - Standard：$100 / 5 days / 10-page + on-chain data / 2 revisions
   - Premium：$200 / 7 days / Full report + 1h consult / 3 revisions
4. **Description**：直接复制 `fiverr-gig-crypto-analysis-2026-07-04.md` 第 19-44 行的 Gig 描述
5. **FAQ**：复制同文件第 60-79 行的 5 条 FAQ
6. **Requirements**：让客户提供：目标赛道 / 报告深度 / 是否需要数据图表 / 是否需要咨询
7. **Gallery**：
   - 上传封面图：`fiverr_crypto_cover.jpg`
   - 上传内页 1：`fiverr_crypto_inner_1.jpg`
   - 上传内页 2：`fiverr_crypto_inner_2.jpg`
8. **Publish** → 等待 Fiverr 审核（通常 24h）

### 步骤 4：创建 Gig 2（AI Agent 咨询）
- Category：Programming & Tech → AI Services → AI Agent Development
- Gig Title：`I will consult on AI agent architecture with langchain crewai autogen or langgraph`
- 复制 `fiverr-gig-ai-agent-consulting-2026-07-04.md` 内容
- 上传 `fiverr_agent_*.jpg` 三张图
- Publish

---

## 三、Gumroad 上架操作步骤

### 步骤 1：注册 Gumroad 账号
- 访问：https://gumroad.com/signup
- 用 PayPal 邮箱注册（与 Fiverr/PayPal 同邮箱）
- 完成邮箱验证

### 步骤 2：绑定 PayPal（关键）
- 进入 Settings → Payments
- **只启用 PayPal**（不启用 Stripe，符合用户约束）
- 输入 PayPal 商家邮箱
- 测试：用另一个邮箱给自己发 $1 测试单，确认能收到

### 步骤 3：创建产品
1. 点击 "Products" → "New Product"
2. **Type**：Standard（一次性付费）
3. **Name**：`The Three Crypto Mainlines of H2 2026: RWA, DePIN, and the Agentic Web`
4. **Description**（复制）：
   ```
   2,500+ word deep analysis report covering the three structural forces defining H2 2026 crypto:

   - RWA (Real World Assets): Top 10 protocols compared - Ondo, BUIDL, Centrifuge, Maple, MakerDAO
   - DePIN (Decentralized Physical Infrastructure): Render, Akash, Filecoin, Helium, io.net
   - AI Agent + Web3: Bittensor, Ritual, CopilotKit, CrewAI, obra/superpowers

   Includes:
   - Top 10 protocol comparison tables for each mainline
   - On-chain TVL & fee data (Q2 2026 snapshot)
   - Risk analysis nobody mentions (oracle dependency, tokenomics cliffs, framework fatigue)
   - 30-day catalyst calendar (Jul-Aug 2026)
   - Independent operator playbook

   Non-marketing, research-grade analysis. Independent (no protocol sponsorships).

   Format: PDF (30+ pages)
   Delivery: Instant download
   ```
5. **Price**：$12（USD）
6. **Preview**：勾选 "Offer a free preview" → 设置 10% 预览
7. **Cover Image**：上传 `gumroad_pdf_cover.jpg`
8. **Preview Images**：上传 `gumroad_preview_1.jpg` + `gumroad_preview_2.jpg`
9. **File**：上传 `2026-H2-crypto-three-mainlines.pdf`
10. **Publish**

### 步骤 4：获取产品链接
上架后会得到一个产品链接，例如 `https://autocorp.gumroad.com/l/h2-2026-crypto`

把这个链接添加到：
- Mirror 文章末尾
- Paragraph Newsletter
- Fiverr gig 描述（作为 portfolio）

---

## 四、收款流程

### 4.1 Fiverr 收款
- 客户下单 → 完成交付 → 客户确认 → Fiverr 释放资金到卖家余额
- 14 天冷却期后可提现到 PayPal（无门槛）
- 提现路径：Fiverr → PayPal → 国内银行账户
- 手续费：Fiverr 抽 20%（行业惯例）

### 4.2 Gumroad 收款
- 客户购买 → 即时到账 Gumroad 余额
- Gumroad 每周五自动打款到 PayPal（满足起付额 $10）
- 提现路径：Gumroad → PayPal → 国内银行账户
- 手续费：Gumroad 抽 10% + PayPal 跨国收款 3-4%

### 4.3 直接 PayPal 收款
- 用 CLI 生成收款链接：`py main.py payment create --live <金额> USD "<描述>"`
- 把链接直接发给客户
- 客户付款 → 资金直接到 PayPal 商家账号（无抽成）
- 入账：`py main.py payment check --live <order_id>` 自动入账到 ledger.yaml

---

## 五、上架后 7 天行动清单

### Day 1-2：上架完成
- [ ] Fiverr gig 1 上架（加密分析）
- [ ] Fiverr gig 2 上架（AI Agent 咨询）
- [ ] Gumroad PDF 上架
- [ ] 三个产品的 PayPal 收款链路全部验证

### Day 3-4：内容引流
- [ ] 在 Mirror.xyz 发布 task-101 文章，末尾放 Gumroad 链接
- [ ] 在 Twitter 发 3 条推文（复用 COO 已产出的推广物料）
- [ ] 在 Reddit 的 r/CryptoCurrency、r/defi 发帖（注意各 sub 规则）
- [ ] 在 Hacker News 试投 "Ask HN: Independent crypto research?"

### Day 5-7：监控与调整
- [ ] 每日检查 Fiverr gig 浏览量（< 50 → 重写标题/标签）
- [ ] 每日检查 Gumroad 浏览量（< 20 → 调整描述/价格）
- [ ] 每日检查 PayPal 是否有入账（`py main.py payment list --live`）
- [ ] 7 天后做首次复盘（保留有效渠道，砍掉零流量渠道）

---

## 六、危机自检与止损

### 止损红线
- **Fiverr 14 天零询盘** → 调整 gig 文案 + 降低 Basic 价格到 $35
- **Gumroad 30 天零销售** → 调整产品定位（可能价格太高，或主题太窄）
- **Mirror 文章 14 天零阅读** → 内容方向调整
- **30 天三 Track 全部零收益** → 触发战略复盘 + 用户介入

### 每日晨会必查（AutonomousLoop 已配置）
- 钱包余额（IncomeMonitor.check_inbound）
- Mirror/Paragraph 新增关注者
- Fiverr gig 浏览量 + 询盘数
- Gumroad 浏览量 + 销售数
- PayPal 入账记录（ledger.yaml）

---

## 七、下一步 AI 可以独立做的事

不需用户介入，AI 可以继续推进：

1. **产出更多 PDF 产品**（DePIN 专项、AI Agent 专项各一份，扩成产品线）
2. **写 Paragraph Newsletter 创刊号**（task-102，AutoCorp 周报 Vol.1）
3. **规划 GitHub 开源项目**（task-106，从 engine/agents/ 抽离通用框架）
4. **生成更多推文/Reddit 帖子**（COO 角色持续产出引流物料）
5. **每日晨会自主运行**（`py main.py autonomous-run --morning`）

需要用户介入才能推进的：
- ❌ Fiverr / Gumroad 账号注册（需用户操作）
- ❌ Mirror.xyz 文章发布（需浏览器 UI 操作，memory 教训：无公开 API）
- ❌ PayPal 大额出款（> $100，需用户确认）
