# Checklist - 美国市场实时创收渠道深度研究

## Phase 1: CEO 竞争力预筛方法论

### 预筛方法论文档
- [x] `company/knowledge/strategic-research/ceo-competitiveness-prescreen.md` 已创建
- [x] 定义了"推荐前必答的 5 个问题"（壁垒/需求/流量/付费意愿/现有资源匹配）
- [x] 定义了预筛通过/不通过的判定规则（任一答"否"或"不确定"则不通过）
- [x] 定义了预筛记录保存流程

### 闲鱼方案事后预筛复盘
- [x] 用 5 个问题对闲鱼方案做了事后预筛
- [x] 记录了复盘结果（壁垒/流量/付费意愿三项不通过）
- [x] 复盘结果作为方法论首个反面案例保存

## Phase 2: 现有资源与美国市场机会映射

### 资源映射表
- [x] `company/knowledge/strategic-research/us-market-existing-resource-map.md` 已创建
- [x] 列出 9 项现有资源（英文内容/Twitter/Reddit/Paragraph/Binance KYC/MetaMask/浏览器自动化/多agent编排/实时Web研究）
- [x] 每项资源包含 6 要素（描述/状态/美国市场场景/转化路径/预期收益/所需补充资源）
- [x] 标注了已验证可用 vs 待验证资源
- [x] 识别了资源组合的协同机会

## Phase 3: 美国市场实时创收渠道深度研究

### 多赛道研究报告
- [x] `company/knowledge/strategic-research/us-market-revenue-research-2026-06-30.md` 已创建
- [x] 赛道 1（美国自由职业）已实时验证 Upwork / Fiverr / Contra / Toptal 入门
- [x] 赛道 2（美国内容创作）已实时验证 Medium Partner Program / Substack / Vocal.media / HubPages / NewsBreak
- [x] 赛道 3（美国开发者社区）已实时验证 dev.to / Hashnode / Medium 技术专栏
- [x] 赛道 4（美国数字产品）已实时验证 Gumroad / Etsy 数字产品 / Notion 模板 / Teachers Pay Teachers
- [x] 赛道 5（美国测试/调研/微任务）已实时验证 UserTesting / Prolific / MTurk / Clickworker / Branded Surveys
- [x] 赛道 6（美国联盟营销）已实时验证 Amazon Associates US / Impact / ShareASale US
- [x] 赛道 7（美国加密，可选）已实时验证 Coinbase Earn / Layer3 US / Galxe US
- [x] 每条赛道包含 9 要素（含竞争力壁垒分析 + 付费意愿评估）
- [x] 每条赛道通过 CEO 竞争力预筛 5 个问题
- [x] 未通过预筛的赛道已标记并说明原因
- [x] 报告末尾给出"3 天内最可能产生首笔收入的 Top 3 美国市场路径"排序

### 实时验证强制
- [x] 所有推荐赛道均有当日 WebSearch（限定 2026 年）+ WebFetch 验证记录
- [x] 验证失败的平台标记为"未验证"，不推荐
- [x] 无任何凭 AI 记忆（2025 年 8 月前信息）的推荐

## Phase 4: 决策修订与系统更新

### 战略重分析决策记录修订
- [x] `company/decisions/strategic-reanalysis-2026-06-30.md` 已追加决策修订
- [x] 记录修订事实：闲鱼方案被用户否决（无竞争力 + 国内付费意愿低）
- [x] 记录修订决策：转向美国市场 + 新增 CEO 竞争力预筛机制
- [x] 记录新的 P0 路径（引用美国市场研究报告结论）
- [x] 记录方法论改进：推荐前必答 5 个问题

### 第一桶金执行手册重写 v4.0
- [x] `company/knowledge/playbooks/first-income-playbook.md` 已升级到 v4.0
- [x] P0 路径改为美国市场实时创收路径
- [x] P1 路径改为美国市场养号窗口期并行执行
- [x] P2 路径标注为"国内 fallback（闲鱼/猪八戒），无竞争力，仅 fallback"
- [x] 新增"CEO 竞争力预筛"章节
- [x] 旧 v3.0 国内多赛道版标记为 deprecated

### 实时机会扫描器升级
- [x] `engine/crypto/realtime_opportunity_scanner.py` 新增 `scan_us_market_tracks()` 方法
- [x] `scan_all()` 方法聚合加密 + 国内非加密 + 美国市场扫描结果
- [x] 报告新增"市场区域"字段（us / cn / global）
- [x] 报告新增"竞争力预筛状态"字段（passed / failed / not_screened）

## 核心原则验证

- [x] 所有推荐方案均已通过 CEO 竞争力预筛 5 个问题
- [x] 每条推荐方案都有明确的竞争力壁垒说明（为什么 AI 公司能做而随便一个人用 AI 做不了）
- [x] 每条推荐方案都有美国市场付费意愿评估（非国内付费意愿低的假设）
- [x] 每条推荐方案都有流量获取说明（避免零咨询访问量）
- [x] 闲鱼/猪八戒国内方案已降级为 fallback，不再作为主路径
- [x] AI CEO 在推荐前自行判断竞争力，不再把判断责任推给用户
- [x] 现有资源（英文内容/Twitter/Reddit/Paragraph/Binance KYC/MetaMask）已映射到美国市场机会
- [x] 所有推荐基于 2026 年当日实时验证，非 AI 记忆
