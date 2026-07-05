# 战略转向决策记录：从"SaaS 订阅（需域名+Stripe）"到"个人创作者经济（PayPal+Web3 钱包）"

> 决策日期：2026-07-04
> 决策方：AutoCorp AI 公司 CEO（GLM-5.2 直接执行）
> 触发原因：用户明确约束变更——无域名 / 无 Stripe / 无公司资质；同时要求"建立长期变现渠道"
> 决策性质：战略级转向（覆盖 2026-07-04 之前的 CEO REVISE 决策）
> 生效时间：立即

---

## 一、约束变更（覆盖原假设）

### 1.1 原 CEO REVISE 决策的核心假设（已失效）
| 假设 | 状态 |
|------|------|
| 注册域名（$15/年）搭建独立站 | ❌ 用户未注册域名 |
| Stripe 收款（SaaS 订阅 + 一次性付费） | ❌ 用户无公司资质、明确不弄 Stripe |
| PSEO 内容工厂 + 长内容改写 SaaS 双产品并行 | ❌ 商业模式不成立 |
| ATS 简历工具（季节性现金流） | ❌ 依赖 Stripe |
| Shopify 客服 Agent（B2B 销售） | ❌ 依赖 Stripe + 销售周期长 |

### 1.2 新约束（用户 2026-07-04 明确）
- ✅ 翻墙：已开启（可访问海外 API）
- ✅ PayPal：用户熟悉，个人身份可用
- ✅ 加密钱包：用户管私钥（AI 不能持私钥）
- ✅ AutonomousLoop + engine/ 模块：可用
- ✅ GLM-5.2 LLM：直接由对话调用
- ❌ 域名：无
- ❌ Stripe：不用
- ❌ 公司资质：无
- ❌ AI 持私钥：禁止

---

## 二、市场行情复盘（2026-07-04 联网搜索）

### 2.1 2026 H2 三大加密主线赛道
| 赛道 | 驱动力 | 代表项目 | 变现机会 |
|------|--------|---------|---------|
| **AI Agent + Web3（智能体经济）** | GitHub Trending 屠榜（obra/superpowers 单周 +19921 stars，CopilotKit 单日 +613 stars）；Messari 预测链上 AI Agent 支付占比达 25% | Bittensor (TAO)、Render、Akash、CopilotKit、open-notebook | AI Agent 框架开源 → GitHub Sponsors；AI Agent 开发咨询接单；行业深度报告订阅 |
| **RWA（真实世界资产代币化）** | Messari 2026 主线；TradFi 大规模入场 | Ondo、Chainlink、MakerDAO、Centrifuge | RWA 资产分析报告；合规解读 Newsletter |
| **DePIN（去中心化物理基础设施）** | 加密从投机转向系统级集成 | Helium、Filecoin、Render、Akash | DePIN 项目横向对比报告；参与指南付费内容 |

### 2.2 个人创作者变现路径（不依赖域名+Stripe）
| 平台 | 收款方式 | 门槛 | 变现模式 |
|------|---------|------|---------|
| **Mirror.xyz** | Web3 钱包（ETH 打赏） | 0 成本 | 加密深度文章 → ETH 打赏 |
| **Paragraph** | Web3 钱包 + Stripe（可绕过） | 0 成本 | Newsletter 订阅 + 打赏 |
| **Gumroad** | PayPal + Stripe（个人 PayPal 可用） | 个人身份即可 | 数字产品一次上架持续收入 |
| **Fiverr** | PayPal 提现 | 个人身份即可 | AI 服务接单（写作/分析/Agent 开发咨询） |
| **GitHub Sponsors** | PayPal / 银行账户 | 开源项目 | 开源 AI Agent 工具吸引赞助 |
| **Twitter/X Premium** | Stripe（不可用）/ 创作者激励 | $8/月订阅 | 暂缓 |

---

## 三、新战略：三轨并行建立长期变现

### Track A：Web3 内容资产 → ETH 打赏 + 订阅（0-3 天启动）
- **目标平台**：Mirror.xyz（主） + Paragraph（次）
- **内容主题**：聚焦 2026 H2 三大主线（RWA / DePIN / AI Agent）
- **节奏**：每周 3 篇深度分析（每篇 2000+ 词，含链上数据 + 项目对比 + 操作指南）
- **变现**：ETH 打赏 + Paragraph 订阅费（Web3 钱包收款，绕过 Stripe）
- **预期**：30 天内积累首批 100 关注者，月打赏 0.05-0.2 ETH

### Track B：Fiverr/Upwork 服务接单 → PayPal 现金流（0-7 天启动）
- **服务方向**：
  1. **加密货币市场深度分析报告**（高壁垒，复用 engine/crypto/ 能力）
  2. **AI Agent 开发咨询**（高客单价 $50-200/h，复用 engine/agents/ 能力）
  3. **SEO 长文代写**（现金流兜底 $30-100/篇）
- **变现**：PayPal 提现（个人身份可用）
- **预期**：14 天内首单成交，月收入 $200-500

### Track C：Gumroad 数字产品 → 被动收入（1-2 周启动）
- **首批产品**：
  1. 《2026 H2 加密市场三大主线深度报告》PDF（定价 $9-19）
  2. 《AI Agent 开发实战 Prompt 库》Notion 模板（定价 $19-29）
  3. 《DePIN 项目参与指南》PDF（定价 $5-9）
- **变现**：PayPal 收款（Gumroad 支持个人）
- **预期**：30 天内首单成交，月被动收入 $50-200

---

## 四、砍项清单（清理低 ROI 循环任务）

以下任务标记为 `killed`，释放队列资源：

| 任务 ID | 标题 | 砍项原因 |
|--------|------|---------|
| task-20260629-007 | 服务订单 ord-20260629-001 交付 | 测试需求，无真实收益 |
| task-20260630-001 | BitDegree Missions（重复第 6 次） | 黑名单，零实际收益 |
| task-20260630-002 | Ethereum Wallet Guide（重复第 8 次） | 内容同质化无壁垒 |
| task-20260701-001 | BitDegree Missions（重复第 7 次） | 黑名单 |
| task-20260701-002 | Ethereum Wallet Guide（重复第 9 次） | 同质化 |
| task-20260702-001 | Zcash 涨幅简讯 | 已过时（7-02 的简讯到 7-04 已无时效价值） |
| task-20260702-002 | BitDegree Missions（重复第 8 次） | 黑名单 |
| task-20260702-003 | Ethereum Wallet Guide（重复第 10 次） | 同质化 |
| task-20260704-002 | BitDegree Missions（重复第 9 次） | 黑名单 |
| task-20260704-003 | Ethereum Wallet Guide（重复第 11 次） | 同质化 |

**保留**：task-20260704-001（Cardano ADA 涨幅简讯，今日时效流量，保留）

---

## 五、新立项清单（围绕三轨战略）

| 任务 ID | 标题 | 类型 | 优先级 | 预期收益 | Track |
|--------|------|------|--------|---------|-------|
| task-20260704-101 | Mirror.xyz 深度文章：2026 H2 加密三大主线（RWA+DePIN+AI Agent） | code | P0 | 0.05-0.2 ETH 打赏 | A |
| task-20260704-102 | Paragraph Newsletter 创刊号：AutoCorp 周报 Vol.1 | code | P0 | Web3 订阅 | A |
| task-20260704-103 | Gumroad 产品上架：《2026 H2 加密三大主线深度报告》PDF | code | P1 | $9-19/份 | C |
| task-20260704-104 | Fiverr gig 文案：加密市场深度分析报告服务 | code | P1 | $50-150/单 | B |
| task-20260704-105 | Fiverr gig 文案：AI Agent 开发咨询服务 | code | P1 | $50-200/h | B |
| task-20260704-106 | GitHub 开源项目规划：从 engine/agents/ 抽离通用 AI Agent 框架 | research | P2 | GitHub Sponsors | B |

---

## 六、危机自检与止损机制

### 6.1 成本意识（用户原话："AI 公司每天都有电费和大模型成本的"）
- 虽然我作为 GLM-5.2 由 TRAE 直接调用，无额外 API 成本
- 但每次 AutonomousLoop 循环消耗计算资源 + 时间
- **止损红线**：若 30 天内三条 Track 全部零收益 → 触发战略复盘 + 用户介入

### 6.2 危机预警机制
- Track A（Mirror）：14 天内零阅读量 → 内容方向调整
- Track B（Fiverr）：21 天内零询盘 → gig 文案/定价调整
- Track C（Gumroad）：30 天内零销售 → 产品定位调整

### 6.3 每日晨会必查
- 钱包余额（IncomeMonitor.check_inbound）
- Mirror/Paragraph 新增关注者
- Fiverr gig 浏览量 + 询盘数
- Gumroad 浏览量 + 销售数

---

## 七、本决策与传统约束的关系

- 本决策不改变 memory 中已记录的硬约束（密钥隔离、合规要求、AI 不持私钥等）
- 本决策覆盖 2026-07-04 之前的 CEO REVISE 决策中"立项 PSEO 工厂 + SaaS 订阅"部分
- 本决策与 2026-06-30 战略转向决策（价值链切入 P0-A）的关系：将原 P0-A 的"独立站长 affiliate 长文"调整为"Mirror/Paragraph 加密深度文"，绕开域名依赖

---

## 八、立即执行动作

1. 追加 task-20260704-101~106 到 task_queue.yaml
2. 启动 noon 执行批次（py main.py autonomous-run --noon）
3. GLM-5.2 直接产出 task-101 的旗舰 Mirror 文章（不等 LLM 队列）
4. 同时由 noon 批次的 TaskExecutor 处理 task-102~106
