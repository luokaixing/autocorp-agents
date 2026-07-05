# 战略重分析：AI 公司出路深度重新评估 Spec

## Why

AI 公司连续 3+ 天零真实收入，在加密单赛道上反复"吊着"。前一个 spec `rebuild-first-income-with-realtime-data` 提出的 Layer3 + Publish0x 双轨路径**也已全面失效**：

- **Publish0x**：账号注册后仍在审核中，文章无法发布，打赏路径阻塞
- **Layer3**：`tasks-2026-06-30.md` 是基于扫描报告降级生成的通用任务模板（Bridge/Swap/Mint 类别），并非真实抓取到的当前可做任务；用户实际登录后发现任务不可用或需本金
- **Binance L&E**：用户验证课程全部结束，路径确认失效
- **Reddit / x.com**：养号第 2 天，主流版块发帖需账号年龄 ≥ 7 天，未来 5 天引流路径全阻塞
- **用户已注册 10+ 账号**，无一能在当下实时走通产生收入

用户原话："感觉目前 AI 公司这在一条死路上一直吊着不走，然后还没有任何收益"。需要跳出"加密赚币"单赛道思维，在 5 天养号窗口期内深度重新分析 AI 公司的真实出路，**不一定是加密货币赛道，那只是一条路**。

## What Changes

- **新增** `company/decisions/strategic-reanalysis-2026-06-30.md` —— 战略重分析决策记录，承认加密单赛道策略失败，启动多赛道并行探索
- **新增** `company/knowledge/strategic-research/current-block-status-2026-06-30.md` —— 当前阻塞状态全景记录（10+ 账号状态、各路径阻塞原因、预计解锁时间）
- **新增** `company/knowledge/strategic-research/multi-track-opportunity-reanalysis-2026-06-30.md` —— 全赛道实时机会深度重分析报告（不限于加密，强制覆盖至少 5 个非加密赛道）
- **新增** `company/knowledge/strategic-research/nurturing-window-plan-2026-06-30.md` —— 5 天养号窗口期利用计划（每日具体任务，确保窗口期不空转）
- **新增** `company/knowledge/strategic-research/account-asset-inventory-2026-06-30.md` —— 10+ 账号资产盘点与处置决策（每个账号：用途、状态、是否值得保留、变现路径）
- **新增** `company/knowledge/strategic-research/ai-company-capability-boundary.md` —— AI 公司能力边界与可行变现模式战略反思
- **修改** `company/knowledge/playbooks/first-income-playbook.md` —— 从"加密双轨"扩展为"多赛道并行探索"，加密路径降级为可选支线之一
- **修改** `engine/crypto/realtime_opportunity_scanner.py` —— 扫描范围扩展到非加密赛道（新增 scan_non_crypto_tracks 方法）

## Impact

- Affected specs:
  - `rebuild-first-income-with-realtime-data` —— 其结论（Layer3 + Publish0x 双轨）已失效，标记为 deprecated
  - `earn-first-crypto-income` —— 已 deprecated（前一轮）
  - `seo-product-launch` —— 内容生产能力可复用于非加密赛道
- Affected code:
  - `engine/crypto/realtime_opportunity_scanner.py` —— 新增非加密赛道扫描
  - `engine/crypto/opportunity_radar.py` —— 雷达范围扩展
- Affected operations:
  - 每日 08:00 晨会新增"全赛道机会扫描"环节（替代纯加密扫描）
  - 5 天养号窗口期内每日新增"窗口期任务执行"环节
- Affected user experience: 用户不再被要求注册新的加密账号，转向利用已有账号资产 + 探索无需养号的即时变现路径

## ADDED Requirements

### Requirement: 当前阻塞状态全景记录

AI 公司 SHALL 生成一份全景阻塞状态文档，诚实记录所有已尝试路径的当前状态，不得隐瞒失效。

#### Scenario: 阻塞状态记录
- **WHEN** 战略重分析启动
- **THEN** 生成 `company/knowledge/strategic-research/current-block-status-2026-06-30.md`
- **AND** 文档必须逐条记录：Publish0x（审核中）、Layer3（任务失效/需本金）、Binance L&E（课程结束）、Reddit（养号第 2 天/需 5 天）、x.com（养号第 2 天/需 5 天）、Mirror.xyz（已转型）、其他已注册账号状态
- **AND** 每条记录包含：账号/平台名、注册日期、当前状态、阻塞原因、预计解锁时间、是否值得继续等待

### Requirement: 全赛道实时机会深度重分析

AI 公司 SHALL 进行一次不限于加密货币的全赛道实时机会深度重分析，强制覆盖至少 5 个非加密赛道。

#### Scenario: 多赛道扫描
- **WHEN** 战略重分析启动
- **THEN** 生成 `company/knowledge/strategic-research/multi-track-opportunity-reanalysis-2026-06-30.md`
- **AND** 报告必须覆盖以下非加密赛道（每条赛道需实时验证，非记忆推荐）：
  - 赛道 1：AI 内容服务外包（Fiverr / Upwork / 猪八戒 / 闲鱼）—— 写文章、SEO、翻译、文案
  - 赛道 2：技术写作与开发者社区打赏（dev.to / Hashnode / Medium Partner Program）
  - 赛道 3：联盟营销（Amazon Associates / ShareASale / 国内淘宝联盟）—— 无需养号
  - 赛道 4：数字产品销售（Notion 模板 / Obsidian 插件 / Gumroad 电子书）
  - 赛道 5：AI 自动化代运营服务（小红书 / 公众号 / 抖音代运营）
  - 赛道 6（可选）：加密赛道保留评估 —— 诚实评估是否值得继续，还是彻底暂停
- **AND** 每条赛道必须包含：实时验证 URL、AI 公司能做什么、用户需要做什么、预期收益、启动门槛、到账速度、是否需要养号
- **AND** 优先标注"无需养号、即时可启动"的路径

#### Scenario: 实时验证强制
- **WHEN** 推荐任何赛道
- **THEN** 必须用 WebSearch + WebFetch 验证平台当日可访问性与变现机制真实存在
- **AND** 验证失败的平台标记为"未验证"，不推荐
- **AND** 禁止凭 AI 记忆推荐（2025 年 8 月前的信息已过时）

### Requirement: 5 天养号窗口期利用计划

AI 公司 SHALL 制定 5 天养号窗口期的每日利用计划，确保窗口期不空转。

#### Scenario: 窗口期计划
- **WHEN** 战略重分析启动
- **THEN** 生成 `company/knowledge/strategic-research/nurturing-window-plan-2026-06-30.md`
- **AND** 计划覆盖 2026-06-30 至 2026-07-04 共 5 天
- **AND** 每日包含：养号任务（Reddit/x.com 互动维持）、即时变现任务（无需养号的赛道）、产出目标
- **AND** 优先安排无需养号即可启动的变现路径在窗口期内先行执行
- **AND** 第 5 天（2026-07-04）设定账号解锁后的引流启动检查点

### Requirement: 账号资产盘点与处置

AI 公司 SHALL 对用户已注册的 10+ 账号进行盘点，给出每个账号的处置决策。

#### Scenario: 账号盘点
- **WHEN** 战略重分析启动
- **THEN** 生成 `company/knowledge/strategic-research/account-asset-inventory-2026-06-30.md`
- **AND** 文档列出所有已知账号：Paragraph、Twitter、Reddit、Binance、Publish0x、Layer3、Mirror、MetaMask、Galxe、Airdrops.io 相关、其他
- **AND** 每个账号记录：用途、注册日期、当前状态、是否产生过收入、是否值得保留、保留理由或放弃理由
- **AND** 对放弃的账号给出"沉没成本承认"声明，不再继续投入时间

### Requirement: AI 公司能力边界与变现模式战略反思

AI 公司 SHALL 进行一次诚实的战略反思，明确自身能力边界与可行变现模式。

#### Scenario: 战略反思
- **WHEN** 战略重分析启动
- **THEN** 生成 `company/knowledge/strategic-research/ai-company-capability-boundary.md`
- **AND** 文档必须回答以下问题（不得回避）：
  - AI 公司真正能做什么（已验证的能力，非假设）
  - AI 公司不能做什么（已验证的局限）
  - 哪些能力已产生过真实价值（哪怕是潜在的）
  - 哪些路径已被证伪（列出全部失败路径）
  - 用户的时间和注意力应聚焦在哪里（而非分散到 10+ 账号）
  - 是否应该暂停加密赛道，转向纯内容/服务赛道
- **AND** 反思必须基于过去 3+ 天的真实运营数据，而非假设

## MODIFIED Requirements

### Requirement: 第一桶金执行手册

原手册以"Layer3 + Publish0x 加密双轨"为主路径，现修改为"多赛道并行探索，加密降级为可选支线"：

- **P0（无需养号，即时可启动）**: 非加密赛道即时变现路径（由多赛道重分析报告确定，如 AI 内容外包、联盟营销、数字产品销售）
- **P1（养号窗口期并行）**: Reddit/x.com 养号 + 即时赛道执行
- **P2（养号解锁后）**: 账号解锁后启动引流（原加密引流路径降级到此层）
- **P3（可选支线，待用户决定是否继续）**: 加密赛道（Layer3/Publish0x/Binance L&E）—— 标注"已多次失效，仅在有实时验证机会时投入"

### Requirement: 实时机会扫描器

原扫描器仅覆盖加密平台，现扩展到非加密赛道。

- 新增 `scan_non_crypto_tracks()` 方法，扫描 AI 内容外包平台、技术写作社区、联盟营销平台、数字产品销售平台
- `scan_all()` 方法聚合加密 + 非加密扫描结果
- 报告新增"赛道类别"字段（crypto / content-service / affiliate / digital-product / automation-service）

## REMOVED Requirements

### Requirement: Layer3 + Publish0x 双轨为第一桶金主路径

**Reason**: 该双轨路径已全面失效。Publish0x 审核中无法发布；Layer3 任务清单为降级生成的通用模板，非真实可做任务。继续作为主路径会让 AI 公司在死路上继续吊着。
**Migration**: 降级为 P3 可选支线，仅在有实时验证的真实可做任务时投入。主路径改为多赛道并行探索，由本次战略重分析报告确定新的 P0 路径。

### Requirement: 持续要求用户注册新的加密平台账号

**Reason**: 用户已注册 10+ 账号无一实时走通，继续要求注册新账号是沉没成本陷阱。用户的注意力应聚焦而非分散。
**Migration**: 暂停所有新账号注册请求。已有账号按"账号资产盘点"处置决策处理。新赛道探索优先选择无需注册新账号或可用已有账号的路径。
