# Gumroad 产品上架规划 - 《2026 H2 加密三大主线深度报告》PDF（task-20260704-103）

> Track C 被动收入入口
> 目标：30 天内首单成交，月被动收入 $50-200
> 战略依据：company/decisions/strategic-pivot-no-domain-no-stripe-2026-07-04.md

---

## 一、产品定位

### 1.1 核心产品
《**The Three Crypto Mainlines That Will Define H2 2026: RWA, DePIN, and the Agentic Web**》
基于 task-101 的 Mirror 文章扩展为完整 PDF 报告（30-40 页）

### 1.2 定价策略
| 版本 | 价格 | 内容 | 目标客户 |
|------|------|------|---------|
| Single Report | $9 | Mirror 文章 + Top 10 协议对比表 | 散户投资者、独立研究员 |
| Pro Bundle | $19 | 上述 + 链上数据截图 + 30 天催化剂日历 + 风险分析附录 | 小型基金、DAO 投委会 |
| Quarterly Subscription | $49/季 | 每季度更新报告 + 邮件订阅 + 季度直播复盘 | 持续关注的机构 |

**首月推荐定价**：$12（介于 $9-19 之间，建立"非便宜非昂贵"的 anchor）
**Launch 优惠**：首周 30% off → $8.4（建立首批客户）

### 1.3 收款方式
- Gumroad 支持 **Stripe** 和 **PayPal**
- 用户约束：不用 Stripe → **仅启用 PayPal**
- 个人身份可申请 Gumroad 账户（不需要公司资质）
- 提现：PayPal → 国内银行账户

---

## 二、产品内容大纲（30-40 页 PDF）

### 第 1 章：执行摘要（1-2 页）
- 三大主线综述
- 核心结论
- 阅读指南

### 第 2 章：RWA - 真实世界资产代币化（8-10 页）
- 2.1 行业驱动力（3 页）
  - 美联储利率周期与 RWA 收益率关系
  - TradFi 机构入场时间线
  - 监管框架演进
- 2.2 Top 10 RWA 协议深度对比（4 页，对比表）
  - Ondo、BlackRock BUIDL、Centrifuge、Maple、MakerDAO、Chainlink、Goldfinch、Backed、RealT、Securitize
  - 对比维度：TVL、收益率、底层资产、流动性、合规等级、监管风险
- 2.3 参与路径与风险（2-3 页）
  - 零售投资者入场路径
  - 默认率历史数据
  - 监管突发风险案例

### 第 3 章：DePIN - 去中心化物理基础设施（8-10 页）
- 3.1 行业驱动力（3 页）
  - AI 算力短缺与 DePIN 兴起
  - 与 AWS/GCP/Azure 的成本对比
  - 需求侧真实收入 vs 代币通胀补贴
- 3.2 Top 10 DePIN 网络对比（4 页，对比表）
  - Render、Akash、Filecoin、Helium、io.net、Aethir、Livepeer、Arweave、Theta、Storj
  - 对比维度：网络规模、月活收入、节点数、需求侧集中度、tokenomics 健康度
- 3.3 参与路径与风险（2-3 页）
  - 硬件运营商入场（GPU/存储/带宽）
  - 算力收益率计算器
  - 硬件折旧与 tokenomics 悬崖风险

### 第 4 章：AI Agent + Web3 - 智能体经济（8-10 页）
- 4.1 行业驱动力（3 页）
  - GitHub Trending 数据
  - Messari 25% 预测的逻辑
  - 链上 AI Agent 支付场景
- 4.2 三层架构对比（4 页）
  - 基础设施层：Bittensor、Ritual、Allora、Akash、Render
  - 框架层（开源）：obra/superpowers、CopilotKit、open-notebook、AutoGen、CrewAI、LangGraph
  - 应用层：自治金库、Agentic Commerce、AI 治理代理
- 4.3 参与路径与风险（2-3 页）
  - 开发者机会（开源框架 → GitHub Sponsors）
  - 咨询服务机会（Fiverr/Upwork AI Agent 接单）
  - 监管未决风险

### 第 5 章：三大主线的交叉机会（3-5 页）
- RWA × DePIN：硬件收益代币化
- RWA × Agents：自治金库
- DePIN × Agents：AI 算力市场自治
- 三者交集：代币化 AI 算力 RWA + 自治市场做市

### 第 6 章：独立操作者行动手册（2-3 页）
- 选 1 个主线作为深度 beat
- 部署发布层（Mirror + Paragraph）
- 产品化研究（Gumroad）
- 开源工具（GitHub Sponsors）
- 服务接单（Fiverr/Upwork）

### 附录 A：30 天催化剂日历
### 附录 B：术语表
### 附录 C：数据来源与方法论
### 附录 D：免责声明

---

## 三、生产流程

### 3.1 内容生产（基于现有素材）
- **基础内容**：复用 Mirror 文章（task-101 已产出）的 2500 词
- **扩展内容**：补充 4 倍 → 10000+ 词（约 30-40 页 PDF）
- **数据补充**：联网搜索各协议 Q2 2026 真实数据（DefiLlama、CoinGecko）
- **图表生成**：用 Python Pillow + matplotlib 生成对比图（绕开 text_to_image 占位符问题）

### 3.2 PDF 制作
- 用 Python markdown → PDF 转换（建议 weasyprint 或 reportlab）
- 模板：Cover + TOC + Body + Appendix
- 排版要求：
  - 字号 11pt 正文 / 14pt 标题 / 9pt 表格
  - 字体：英文用 Inter / Source Sans Pro
  - 页眉页脚：AutoCorp Research Desk + 报告日期

### 3.3 上架 Gumroad
- 注册 Gumroad 账户（个人身份）
- 仅启用 PayPal（不启用 Stripe）
- 产品图：3 张（封面图 + 内容预览 + 目录预览）
- 描述：300-500 字，强调"non-marketing research-grade analysis"
- 标签：crypto research, RWA, DePIN, AI agent, market analysis

---

## 四、营销与销售

### 4.1 引流策略
1. **Mirror 文章引流**：Mirror 文章末尾放 Gumroad 链接（"完整 PDF 报告 $12"）
2. **Paragraph Newsletter 引流**：创刊号提及完整报告
3. **Twitter 推文**：3 条推文/周，每条带 Gumroad 链接（不依赖 Premium，自然流量）
4. **Reddit 帖子**：r/CryptoCurrency、r/defi、r/ethtrader 各发 1 帖（遵守各 sub 规则）
5. **Hacker News**：投递"Ask HN: Independent crypto research?"类帖（试水）

### 4.2 转化优化
- 首页免费预览：第 1 章 + 第 5 章前两段（建立信任）
- "30% OFF 首周"启动优惠
- 客户邮箱收集：购买后 opt-in 加入 AutoCorp Newsletter（升级 Track A）
- 7 天未购回访：通过 Gumroad 邮件工具发 1 次提醒

### 4.3 定价实验
- 第 1 月：$12（首周 30% off）
- 第 2 月：$15（根据销售数据调整）
- 第 3 月：$19 + 推出 $49 季度订阅

---

## 五、收入预测

| 时间窗 | 单价 | 销量 | 收入 | Gumroad 抽成（10%） | PayPal 手续费（约 3%） | 净收入 |
|--------|------|------|------|---------------------|----------------------|--------|
| 第 1 月 | $8.4-12 | 5-15 份 | $42-180 | $4-18 | $1-5 | $37-157 |
| 第 2 月 | $15 | 10-25 份 | $150-375 | $15-37 | $5-11 | $130-327 |
| 第 3 月 | $19 + $49 订阅 | 15-30 份 + 3-5 订阅 | $285-570 + $147-245 | $43-82 | $13-24 | $376-709 |

**3 个月累计净收入预期**：$543-1193

---

## 六、风险与缓解

| 风险 | 概率 | 影响 | 缓解 |
|------|------|------|------|
| Gumroad 账户审核失败 | 低 | 高 | 备选：Gumroad 失败则用 Payhip / Lemon Squeezy（同样支持个人 PayPal） |
| PayPal 个人账户收款受限 | 中 | 高 | 提前测试 $1 内部转账验证；必要时升级 PayPal 商户账户 |
| 销量低于预期 | 高 | 中 | 第 2 月开始 A/B 测试定价 + 标题 |
| 内容被复制盗用 | 中 | 低 | PDF 加 watermark + 客户邮箱；DMCA 维权 |
| 客户要求退款 | 低 | 低 | Gumroad 退款政策明确：购买后 7 天内可退 |

---

## 七、立即执行清单

- [ ] 基于 task-101 Mirror 文章扩展为 PDF（预计 4-6 小时工作量）
- [ ] 用 Python Pillow 生成 3 张产品图（封面、内容预览、目录预览）
- [ ] 注册 Gumroad 账户（个人身份，仅启用 PayPal）
- [ ] 上架产品（定价 $12，首周 30% off）
- [ ] 在 Mirror 文章末尾追加 Gumroad 链接
- [ ] 在 Paragraph Newsletter 创刊号提及产品
- [ ] 7 天后复盘：浏览量、加购量、销售量

---

## 八、扩展产品线（90 天后）

如果首月 PDF 销售良好，扩展产品线：

1. **《AI Agent 开发实战 Prompt 库》Notion 模板**（$19-29）
   - 含 50+ 精心调优的 Prompt
   - 覆盖：架构设计、调试、性能优化、Agent 编排模式
   - 跟 task-106 GitHub 开源项目联动

2. **《DePIN 项目参与指南》PDF**（$5-9）
   - 入门级教程
   - 各网络参与成本 vs 收益对比
   - 硬件采购清单

3. **《State of the Agentic Web》季度订阅报告**（$49/季）
   - 季度更新
   - 链上 AI Agent 支付数据追踪
   - GitHub 项目动态
   - 投融资事件回顾

4. **AutoCorp Newsletter Premium 订阅**（$9/月）
   - 每周 1 篇深度文章
   - 邮件直送
   - 客户专属 Discord 频道
