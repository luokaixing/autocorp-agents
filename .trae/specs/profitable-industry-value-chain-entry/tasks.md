# Tasks

- [x] Task 1: 最挣钱行业实时数据扫描与识别（10 个行业，25 次 WebSearch + 9 次 WebFetch，Top 5: SaaS/电商/AI应用/网络安全/金融科技）
  - [ ] SubTask 1.1: 用 WebSearch（限定 2026 年）扫描 8+ 候选行业（AI 基础设施、AI 应用、加密、医疗生物、金融科技、半导体、网络安全、绿色能源、电商、企业 SaaS）的利润规模、利润率、增长率
  - [ ] SubTask 1.2: 对每个行业用 WebFetch 验证至少 2 个独立来源（McKinsey/BCG/Statista/行业报告）
  - [ ] SubTask 1.3: 生成 `company/knowledge/strategic-research/most-profitable-industries-2026.md`，每个行业包含 8 要素（利润规模/利润率/增长率/利润池分布/进入壁垒/AI 可否切入/3 个机会点/风险）
  - [ ] SubTask 1.4: 按利润率 × 增长率 × AI 可切入性排序，输出 Top 5 最挣钱且可切入的行业

- [x] Task 2: 行业利润池拆解分析（5 行业 × 6 环节 = 30 环节，识别 12 个黄金切入点，Top 3: SaaS选型/Shopify SEO/跨境支付对比）
  - [ ] SubTask 2.1: 对 Task 1 识别的 Top 5 行业，各自拆解价值链至少 5 个环节
  - [ ] SubTask 2.2: 每个环节标注利润占比、进入壁垒、是否适合 AI 公司切入
  - [ ] SubTask 2.3: 标注"高利润 + 低壁垒 + AI 可切入"的环节为"黄金切入点"
  - [ ] SubTask 2.4: 生成 `company/knowledge/strategic-research/industry-profit-pool-analysis.md`

- [x] Task 3: 价值链切入机会矩阵生成（36 个机会点，27 通过预筛，9 未通过，Top 5: SaaS选型/Shopify SEO/跨境支付/AI对比/独立站代运营）
  - [ ] SubTask 3.1: 对 Top 5 行业的"黄金切入点"环节，每个生成至少 3 个具体切入机会点
  - [ ] SubTask 3.2: 切入点类型至少覆盖 5 类中的 3 类（效率工具/内容支持/数据服务/自动化/营销支持）
  - [ ] SubTask 3.3: 每个切入点完成 8 要素分析（描述/目标客户/价值主张/壁垒/启动成本/到账速度/可持续性/现有资源匹配）
  - [ ] SubTask 3.4: 对每个切入点跑 CEO 竞争力预筛 6 个问题（含新增的第 6 题"是否切入最挣钱行业"）
  - [ ] SubTask 3.5: 生成 `company/knowledge/strategic-research/value-chain-entry-opportunities.md`，末尾给出"3 天可启动 + 7 天可能首笔收入"的 Top 5 切入点排序

- [x] Task 4: 可持续收益产品创意库生成（12 个创意，6 类全覆盖，9 通过预筛，Top 3: AI工具周报/CVE漏洞周报/跨境支付对比站）
  - [ ] SubTask 4.1: 头脑风暴至少 10 个产品创意，覆盖 6 类产品类型中的至少 4 类（内容资产/工具/数据/模板数字产品/自动化/聚合）
  - [ ] SubTask 4.2: 每个创意完成 10 要素分析（描述/目标用户/收益模式/可持续性/壁垒/启动成本/行业关联/MVP/首笔收入路径/风险）
  - [ ] SubTask 4.3: 对每个创意跑 CEO 竞争力预筛 6 个问题
  - [ ] SubTask 4.4: 生成 `company/knowledge/strategic-research/sustainable-revenue-product-ideas.md`，末尾给出"3 天可出 MVP + 30 天可能首笔收入"的 Top 3 产品排序

- [x] Task 5: 战略转向决策记录（8 章节，立即行动项 Day1-3-7-30，6 个 spec 处置决策，本 spec 升级 P0 主路径）
  - [ ] SubTask 5.1: 生成 `company/decisions/strategic-pivot-to-value-chain-entry-2026-06-30.md`
  - [ ] SubTask 5.2: 记录旧战略失败原因、新战略核心逻辑、执行原则、与前几轮 spec 关系、验证标准
  - [ ] SubTask 5.3: 在决策记录中明确：前几轮 spec 的"自身能力正推"路径降级为 P1 支撑层

- [x] Task 6: 现有文档与方法论同步更新（4 文档已更新：playbook v5.0/prescreen v2.0/blacklist+2条/capability v2.0，无破坏性变更）
  - [ ] SubTask 6.1: 修改 `company/knowledge/playbooks/first-income-playbook.md`，新增 P0 战略层（价值链切入 + 可持续产品），原 P0 降级为 P1
  - [ ] SubTask 6.2: 修改 `company/knowledge/strategic-research/ceo-competitiveness-prescreen.md`，新增第 6 个预筛问题"是否切入最挣钱行业"
  - [ ] SubTask 6.3: 修改 `company/knowledge/strategic-research/disproven-paths-blacklist.md`，将"从自身能力正推的低附加值方案"列为结构性失效模式
  - [ ] SubTask 6.4: 更新 `company/knowledge/strategic-research/ai-company-capability-boundary.md`，新增"产品化能力"维度评估

- [x] Task 7: 实时机会扫描器代码扩展（新增 scan_most_profitable_industries + scan_value_chain_entry_opportunities + scan_all 排序，27 个单元测试通过，无破坏性变更）
  - [ ] SubTask 7.1: 在 `engine/crypto/realtime_opportunity_scanner.py`（或新建 `engine/strategy/industry_profit_pool_analyzer.py`）中新增 `scan_most_profitable_industries()` 方法
  - [ ] SubTask 7.2: 新增 `scan_value_chain_entry_opportunities()` 方法
  - [ ] SubTask 7.3: 修改 `scan_all()` 聚合所有扫描结果，按"是否切入最挣钱行业"优先排序
  - [ ] SubTask 7.4: 报告输出新增"行业利润池定位"字段（high-profit-chain / mid / low-red-ocean）
  - [ ] SubTask 7.5: 编写单元测试验证扫描器扩展功能

- [x] Task 8: 晨会流程更新（meeting.yaml + meeting.py + meeting.md 三文件更新，新增 4 个扫描方法 + 2 个进度章节 + P0-P4 五级优先级，无破坏性变更）
  - [ ] SubTask 8.1: 修改晨会模板，新增"最挣钱行业动态扫描"环节
  - [ ] SubTask 8.2: 修改晨会报告生成逻辑，在"当日赚钱任务建议"中优先展示价值链切入与产品化路径
  - [ ] SubTask 8.3: 更新 `company/meetings/2026-06-30/meeting.md` 记录本次战略转向决议

# Task Dependencies

- Task 2 依赖 Task 1（利润池拆解需先有行业清单）
- Task 3 依赖 Task 2（切入点需基于利润池分析的"黄金切入点"）
- Task 4 可与 Task 3 并行（产品创意库与切入点矩阵思路相近但独立）
- Task 5 依赖 Task 1-4（决策记录需汇总所有分析结果）
- Task 6 依赖 Task 5（文档更新需先有战略转向决策）
- Task 7 可与 Task 1-4 并行（代码扩展不依赖分析结论，仅依赖接口定义）
- Task 8 依赖 Task 5-6（晨会流程更新需先有新战略与方法论）
