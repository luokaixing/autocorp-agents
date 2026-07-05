# 美国市场实时创收渠道深度研究 Spec

## Why

前一轮 spec `strategic-reanalysis-viable-path` 推荐的闲鱼虚拟产品挂单方案存在两个用户已指出的致命缺陷：(1) **无竞争力**——"随便一个人使用 AI 都能完成"，挂上去可能零咨询访问量；(2) **国内用户付费意愿低**。更深层的问题是 AI 公司虚拟 CEO 在推荐前未自行判断方案的竞争力与可行性，把无竞争力方案推给了用户。需要转向**美国市场**，深入研究实时的、能利用现有资源（英文内容生产能力、已发布 3 篇 Paragraph 文章、Twitter/Reddit 养号账号、Binance KYC、MetaMask 钱包）获得收入的创收渠道，并在方法论上新增"CEO 竞争力预筛"环节，避免再次推荐无壁垒方案。

## What Changes

- **新增** `company/knowledge/strategic-research/us-market-revenue-research-2026-06-30.md` —— 美国市场实时创收渠道深度研究报告，强制覆盖至少 6 个美国市场赛道，每条赛道必须有竞争力分析与"为什么 AI 公司能做而随便一个人用 AI 做不了"的壁垒说明
- **新增** `company/knowledge/strategic-research/ceo-competitiveness-prescreen.md` —— CEO 竞争力预筛方法论，定义"推荐前必答的 5 个问题"，任何方案未通过预筛不得推荐给用户
- **新增** `company/knowledge/strategic-research/us-market-existing-resource-map.md` —— 现有资源与美国市场机会映射表，明确每项现有资源如何转化为美国市场收入
- **修改** `company/knowledge/playbooks/first-income-playbook.md` —— 从"国内多赛道（闲鱼/猪八戒/Fiverr）"改为"美国市场优先 + 竞争力预筛"，国内方案降级为 fallback
- **修改** `company/decisions/strategic-reanalysis-2026-06-30.md` —— 追加决策修订：承认闲鱼方案无竞争力错误，转向美国市场
- **修改** `engine/crypto/realtime_opportunity_scanner.py` —— 新增 `scan_us_market_tracks()` 方法，扫描美国市场 6+ 赛道

## Impact

- Affected specs:
  - `strategic-reanalysis-viable-path` —— 其推荐的闲鱼/猪八戒国内方案被否决，标记为 deprecated，仅保留 Fiverr（已属美国市场）
  - `rebuild-first-income-with-realtime-data` —— 已 deprecated
  - `seo-product-launch` —— 英文内容生产能力是美国市场的核心资产，复用
- Affected code:
  - `engine/crypto/realtime_opportunity_scanner.py` —— 新增美国市场扫描方法
- Affected operations:
  - 每日 08:00 晨会的"全赛道机会扫描"环节新增"美国市场扫描"子环节
  - 任何新方案推荐前必须通过 CEO 竞争力预筛（5 个问题）
- Affected user experience: 用户不再被推荐无竞争力的国内方案，转向付费意愿更高的美国市场；AI CEO 在推荐前自行判断竞争力，不再把判断责任推给用户

## ADDED Requirements

### Requirement: CEO 竞争力预筛方法论

AI 公司 SHALL 在推荐任何创收方案前，由虚拟 CEO 自行完成竞争力预筛，未通过预筛的方案不得推荐给用户。

#### Scenario: 推荐前的竞争力预筛
- **WHEN** AI 公司准备向用户推荐任何创收方案
- **THEN** 虚拟 CEO 必须先回答以下 5 个问题并记录到方案文档
  1. **壁垒问题**：这个方案为什么 AI 公司能做，而随便一个人用 AI 做不了？（如答不出壁垒，方案作废）
  2. **需求问题**：这个方案在目标市场有真实付费需求吗？（需引用实时验证数据，非记忆）
  3. **流量问题**：方案挂出去后如何获得咨询/访问量？零流量=零收入
  4. **付费意愿问题**：目标市场用户的付费意愿如何？（避免重蹈"国内付费意愿低"覆辙）
  5. **现有资源匹配问题**：方案能否利用 AI 公司现有资源（英文内容能力/Twitter/Reddit/Paragraph/Binance KYC/MetaMask），还是需要从零开始？
- **AND** 5 个问题任一答"否"或"不确定"，方案标记为"未通过预筛"，不推荐
- **AND** 预筛记录保存到 `company/knowledge/strategic-research/ceo-competitiveness-prescreen.md`

#### Scenario: 闲鱼方案的事后预筛复盘
- **WHEN** 本 spec 实施时
- **THEN** 用 5 个问题对已推荐的闲鱼方案做事后预筛
- **AND** 记录复盘结果（预期：壁垒问题答不出、流量问题答不出、付费意愿问题答"低"——三项不通过）
- **AND** 复盘结果作为方法论首个案例保存

### Requirement: 美国市场实时创收渠道深度研究

AI 公司 SHALL 进行一次专注于美国市场的实时创收渠道深度研究，强制覆盖至少 6 个赛道，每条赛道需实时验证。

#### Scenario: 美国市场多赛道扫描
- **WHEN** 本 spec 实施
- **THEN** 生成 `company/knowledge/strategic-research/us-market-revenue-research-2026-06-30.md`
- **AND** 报告必须覆盖以下美国市场赛道（每条赛道需 WebSearch + WebFetch 实时验证 2026 年当日状态）：
  - 赛道 1：美国自由职业平台（Upwork / Fiverr / Contra / Toptal 入门）—— 英文接单
  - 赛道 2：美国内容创作变现（Medium Partner Program / Substack / Vocal.media / HubPages / NewsBreak）
  - 赛道 3：美国开发者/技术社区变现（dev.to / Hashnode / Medium Partner Program 技术专栏）
  - 赛道 4：美国数字产品市场（Gumroad / Etsy 数字产品 / Notion 模板 / Teachers Pay Teachers）
  - 赛道 5：美国测试/调研/微任务平台（UserTesting / Prolific / MTurk / Clickworker / Branded Surveys）
  - 赛道 6：美国联盟营销（Amazon Associates US / Impact / ShareASale US）
  - 赛道 7（可选）：美国加密市场保留评估（Coinbase Earn / Layer3 / Galxe US 可用部分）
- **AND** 每条赛道必须包含 9 要素：
  1. 实时验证 URL（WebFetch 实际访问的 URL + 验证时间戳）
  2. AI 公司能做什么（基于已验证能力）
  3. 用户需要做什么
  4. 预期收益（诚实预估，引用平台真实数据）
  5. 启动门槛
  6. 到账速度
  7. 是否需要养号
  8. **竞争力壁垒分析**（为什么 AI 公司能做而随便一个人用 AI 做不了）
  9. **付费意愿评估**（美国市场用户付费意愿，引用实时数据）
- **AND** 每条赛道必须通过 CEO 竞争力预筛 5 个问题，未通过的不推荐
- **AND** 报告末尾给出"3 天内最可能产生首笔收入的 Top 3 美国市场路径"排序

#### Scenario: 实时验证强制
- **WHEN** 推荐任何美国市场赛道
- **THEN** 必须用 WebSearch（限定 2026 年）+ WebFetch 验证平台当日可访问性与变现机制真实存在
- **AND** 验证失败的平台标记为"未验证"，不推荐
- **AND** 禁止凭 AI 记忆推荐（知识截止 2025 年 8 月）

### Requirement: 现有资源与美国市场机会映射

AI 公司 SHALL 生成现有资源与美国市场机会的映射表，明确每项现有资源如何转化为美国市场收入。

#### Scenario: 资源映射
- **WHEN** 本 spec 实施
- **THEN** 生成 `company/knowledge/strategic-research/us-market-existing-resource-map.md`
- **AND** 映射表必须覆盖以下现有资源：
  - 英文内容生产能力（3 篇已发布 Paragraph 文章 + 1 篇待发 art_004 + 3 篇 Publish0x 待发）
  - Twitter 账号 @LUOKAIXING（养号中，已发 1 条推文）
  - Reddit 账号（养号中，2026-07-04 解锁）
  - Paragraph 账号（已发 3 篇，零打赏）
  - Binance 账号（KYC 已过）
  - MetaMask 钱包（${ETH_SHORT}，余额 0）
  - 浏览器自动化能力（agent-browser session=autocorp）
  - 多 agent 编排能力（CEO/CTO/COO）
  - 实时 Web 研究能力（realtime_opportunity_scanner）
- **AND** 每项资源给出：资源描述、当前状态、美国市场可应用场景、转化路径、预期收益、所需补充资源

## MODIFIED Requirements

### Requirement: 第一桶金执行手册

原手册（v3.0）以"国内多赛道（闲鱼/猪八戒/Fiverr）"为主路径，现修改为"美国市场优先 + 竞争力预筛"：

- **P0（美国市场，需通过竞争力预筛）**: 美国市场实时创收路径（由美国市场研究报告确定）
- **P1（美国市场，养号窗口期并行）**: Reddit/x.com 养号 + 美国市场即时赛道执行
- **P2（fallback，仅当美国市场全部受阻时）**: 国内方案（闲鱼/猪八戒）—— 标注"无竞争力，仅作 fallback"
- **P3（可选支线）**: 加密赛道（已多次失效，仅在实时验证机会时投入）
- **新增约束**: 任何方案推荐前必须通过 CEO 竞争力预筛 5 个问题

### Requirement: 实时机会扫描器

原扫描器（v2）覆盖加密 + 国内非加密赛道，现新增美国市场扫描。

- 新增 `scan_us_market_tracks()` 方法，扫描美国自由职业/内容创作/数字产品/测试调研/联盟营销平台
- `scan_all()` 方法聚合加密 + 国内非加密 + 美国市场扫描结果
- 报告新增"市场区域"字段（us / cn / global）
- 新增"竞争力预筛状态"字段（passed / failed / not_screened）

## REMOVED Requirements

### Requirement: 闲鱼虚拟产品挂单为 P0 主路径

**Reason**: 用户明确否决。闲鱼方案无竞争力（"随便一个人使用 AI 都能完成"），挂上去可能零咨询访问量，且国内用户付费意愿低。AI 公司虚拟 CEO 未在推荐前判断竞争力，方法论失误。
**Migration**: 降级为 P2 fallback（仅当美国市场全部受阻时考虑），并作为 CEO 竞争力预筛方法论的首个反面案例。主路径改为美国市场实时创收渠道，由本次研究确定。

### Requirement: 猪八戒翻译/文案接单为 P1 路径

**Reason**: 与闲鱼相同的国内付费意愿低问题，且翻译/文案竞争激烈无壁垒。
**Migration**: 降级为 P2 fallback。美国市场 Upwork/Fiverr 英文接单替代此路径。
