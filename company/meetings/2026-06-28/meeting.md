# 产研同步会纪要 - 2026-06-28

## 会议时间
2026-06-28 08:00 (Asia/Shanghai)

## 参会人员
ProductManager, CTO, Architect, CEO

## 1. 需求汇报（ProductManager）
【市场调研】
# 市场调研报告：可变现产品需求候选（2026 H2）

基于市场情报，识别出 4 个可变现产品需求候选：

## 候选 1：Crypto SEO 内容自动化生成器（推荐立即立项）
- **痛点**：加密内容创作者每周 10-15h 研究代币+写教程；Web3 项目方缺内容运营
- **目标用户**：Web3 项目方、加密媒体、个人 KOL（1-10万粉）
- **竞品**：Jasper AI（不懂加密）、Copy.ai（模板化）
- **差异化**：内置链上数据/空投日历，生成可执行操作步骤
- **变现**：$29-299/月 SaaS 订阅 + 打赏分成 5%
- **MRR**：$5,000-12,000（6个月）
- **推荐理由**：现有代码 70% 可复用，1 周出 MVP

## 候选 2：空投任务自动化助手（二期）
- **痛点**：空投猎人每天 2-3h 重复完成任务，新手易错损失 gas
- **目标用户**：空投猎人、Web3 新手、投研团队
- **竞品**：Airdrops.io（纯信息）、Layer3（单一平台）
- **差异化**：跨平台聚合 + 浏览器自动化执行 + 到账追踪
- **变现**：$19/月 + 任务佣金 $0.5-2
- **MRR**：$3,000-8,000

## 候选 3：DeFi 收益率优化雷达（三期）
- **痛点**：DeFi 用户每天对比 10+ 协议收益率，跨链套利稍纵即逝
- **目标用户**：DeFi 散户（TVL $10k+）、收益农场管理者
- **竞品**：DeFiLlama（无建议）、Zapper（优化弱）
- **差异化**：LLM 策略推荐 + 自动再平衡
- **变现**：$49/月 + AUM 1% 年化

## 候选 4：Web3 求职简历优化（低优先级）
- **变现**：$19/次 + $99/月辅导

## 决策建议
1. **立即**：候选 1（Crypto SEO 生成器）- 技术栈 70% 复用
2. **二期**：候选 2（空投助手）- agent-browser 已就绪
3. **资源**：域名 $10 + Vercel 免费 + Stripe/PayPal 收款

【需求清单】
# AutoCorp 需求清单（2026 Q3）

基于市场情报和产品矩阵，搜集以下需求：

| 编号 | 用户痛点 | 优先级 | 预估开发量 |
|------|----------|--------|------------|
| REQ-001 | 加密内容创作者手动研究代币耗时（每周 10-15h） | P0 | 3 天 |
| REQ-002 | Web3 项目方缺多平台内容分发能力 | P0 | 2 天 |
| REQ-003 | 文章发布后无打赏入口（读者不知道怎么打赏） | P0 | 0.5 天 |
| REQ-004 | 空投猎人需跨平台追踪任务进度 | P1 | 5 天 |
| REQ-005 | DeFi 用户无法快速对比多协议收益率 | P1 | 4 天 |
| REQ-006 | 加密新手不知道如何完成链上操作（钱包/签名/桥接） | P1 | 2 天 |
| REQ-007 | 内容创作者无法追踪打赏收入来源 | P2 | 1 天 |
| REQ-008 | Landing Page 转化率低（缺付费入口） | P2 | 1 天 |

## 近期需求详细说明

### REQ-001：Crypto SEO 内容自动化生成器
- **痛点**：加密内容创作需要深入研究代币机制、链上数据、市场动态，手动撰写一篇 2000 字教程需 4-8 小时
- **目标用户**：Web3 项目方、加密媒体、个人 KOL
- **优先级**：P0（直接变现路径）
- **开发量**：3 天（复用现有 keyword_analyzer + content_writer）

### REQ-002：多平台内容发布管道
- **痛点**：一篇内容需手动发布到 Paragraph/Mirror/Publish0x/Twitter/Reddit 5+ 平台
- **目标用户**：所有内容创作者
- **优先级**：P0（发布效率 = 内容产出量）
- **开发量**：2 天（agent-browser 已就绪）

### REQ-003：打赏入口嵌入
- **痛点**：现有文章未在显眼位置展示钱包地址，读者不知道如何打赏
- **目标用户**：所有已发布文章
- **优先级**：P0（影响首笔收入）
- **开发量**：0.5 天（模板修改）

## 2. 技术方向（CTO）
# AutoCorp 技术方向

# AutoCorp 技术选型决策（2026 Q3）

## 一、技术栈选型

### 后端
- Python 3.11（现有框架稳定）
- FastAPI（未来 SaaS API）
- 现有 TaskQueue（YAML）足够，>100 任务/天时升级 Redis+RQ

### 前端
- Next.js 14 + Tailwind CSS
- Vercel 免费档部署

### LLM 层
- 主力：GLM-5.2（国内可用、低成本）
- 降级链：TRAE API → TraeBridge 文件队列 → TemplateProvider
- 未来：GLM-4-Flash（免费）作为低优先级任务模型

### 浏览器自动化
- agent-browser + CDP 连接（已跑通日常 profile 复用）

### 数据存储
- 当前：YAML 文件
- 升级时机：文章数 >100 或用户 >10 时迁移 SQLite
- 长期：PostgreSQL + pgvector

## 二、架构方向

### 阶段 1（0-3 月）：内容工厂 + 打赏变现
- SEO 内容生成 → 多平台发布 → 打赏地址嵌入

### 阶段 2（3-6 月）：SaaS 化
- FastAPI + Next.js + Stripe/PayPal + Clerk 认证

### 阶段 3（6-12 月）：多 Agent 协作平台
- LangGraph 编排 + 更多数据源

## 三、风险点与对策

| 风险 | 对策 |
|------|------|
| LLM API 不稳定 | TraeBridge 降级链 |
| 浏览器登录态失效 | check_vpn() 集成晨会 |
| 域名/服务器成本 | Vercel + GitHub Pages 免费档 |
| 加密市场下行 | 多赛道布局 |

## 四、近期技术任务
1. [P0] 完善 TraeBridge 自动轮询
2. [P0] Crypto SEO 生成器 MVP
3. [P1] agent-browser 截图视觉校验
4. [P2] 评估 LangGraph 替换 Orchestrator

## 3. 任务拆解（Architect）
# AutoCorp 架构设计

## 一、模块拆分清单

### 核心层 engine/
- llm_client.py（LLM 客户端+降级链）
- trae_bridge.py（文件队列）
- workspace.py / autonomous_loop.py / orchestrator.py

### Agent 层 engine/agents/
- ceo_autonomous.py / cto.py / architect.py / pm.py / programmer.py / tester.py

### 工具层
- browser/agent_browser.py（CDP 连接）
- crypto/（market_analyzer, opportunity_radar, learn_earn_assistant）
- tools/（web_searcher, web_fetcher）
- safety/（compliance, payment_gate）
- human_loop.py（含 check_vpn）

### 内容层 engine/content/
- keyword_analyzer / outline_generator / content_writer / template_provider

### 业务层 engine/business/（新增）
- seo_generator.py / airdrop_assistant.py / publish_pipeline.py / tipping_tracker.py

## 二、接口定义

```python
# LLM
class LLMClient:
    def chat(system_prompt, user_message, temperature=0.7, max_tokens=2000) -> str
    def chat_messages(messages, ...) -> str

# 浏览器
class AgentBrowser:
    def open(url, wait_networkidle=True) -> bool
    def eval_js(js) -> Optional[str]
    def snapshot() -> str
    def click(ref) -> bool
    def fill(ref, value) -> bool
    def close() -> bool

# 内容生成
class SEOGenerator:
    def generate_article(keyword, word_count=2000) -> Article
    def generate_batch(keywords) -> list[Article]
    def publish_to_platforms(article, platforms) -> dict

# 任务队列
class TaskQueue:
    def enqueue(task) -> str
    def dequeue() -> Optional[Task]
    def mark_done(task_id, result)
    def mark_failed(task_id, error)
```

## 三、技术规范

1. **错误处理**：外部调用必须 try/except，降级链：主→备→模板
2. **数据持久化**：YAML 配置 + Markdown 产出 + JSON 队列
3. **命名**：文件 kebab-case，类 PascalCase，函数 snake_case
4. **测试**：新增模块必须有 test_*.py，降级链必须有故障注入测试

## 四、近期任务
1. [P0] 创建 engine/business/ 目录
2. [P0] seo_generator.py MVP
3. [P1] 降级链测试覆盖

## 4. 最终决策（CEO）
决策：approve
理由：
# CEO 立项评审决策

## 决策：**APPROVE（有条件批准）**

## 评审理由

### 财务可行性 ✅
- 账本余额 $10,148.12（充足）
- 累计收入 $153.12 > 支出 $5.0（正向现金流）
- 本方案零额外支出，ROI 风险极低

### 技术可行性 ✅
- 架构合理，模块边界清晰
- 核心模块已验证
- 新增业务层依赖现有能力

### 市场时机 ✅
- Crypto SEO 赛道与现有 2 篇文章验证了内容能力
- 加密市场回暖，内容投放需求上升

## 批准条件

1. **分期推进**：本周仅启动 seo_generator.py MVP
2. **成本上限**：本季度总支出 ≤$50
3. **收益里程碑**：30 天内至少 1 篇文章获打赏；90 天内 SaaS MVP 上线

## 资源分配

| 资源 | 分配 |
|------|------|
| CEO 驾驶舱 | 每日 8:00 + 12:00 |
| CTO 评审 | 每周一 |
| Programmer | 专注 SEO MVP |
| Tester | 每个 PR 必须有降级链测试 |

## 下一步
1. [立即] 创建 engine/business/ 目录
2. [今日] seo_generator.py MVP
3. [本周] 发布 2 篇 SEO 文章

注意：此任务可能超出 ceo 职责范围，建议转交对应角色。

## 5. 营收驾驶舱（每日必看）
### 钱包余额（2026-06-28）
- ethereum: 0.0 ETH (`${ETH_TIPPING_ADDRESS}`)

### 内容资产统计
- 已发布：2 篇
- 待发布：1 篇
- 草稿：0 篇
- 累计打赏 ETH：0.0
- 累计打赏 USD：0.0
- 累计浏览量：0

### 当日赚钱任务建议（按 ROI 排序）
**即时收入类**（当日可见收益）
- [ ] 完成 3 个 BitDegree Missions（预期 +150-1500 Bits → 兑换加密货币）
- [ ] 重写 1 篇 SEO 文章并发布到 Paragraph（解锁打赏入口）

**资产积累类**（长效收益）
- [ ] 完成 1 个 Layer3 任务（积累 CUBE 积分，空投乘数）
- [ ] 参与一个新测试网（Monad/Berachain/Scroll 之一）

**渠道解锁类**（解锁未来收入）
- [ ] 追踪 Publish0x 作者审核状态（24-72h）
- [ ] 提醒用户提供 Binance 注册进度
- [ ] 提醒用户提供 PayPal 真实 Key（解锁产品销售）

### 危机自检
⚠️ **钱包余额为 0 或查询失败** - 公司无现金流，今日必须推进至少 1 个即时收入渠道
⚠️ **已发布文章 < 3 篇** - 内容资产不足，需加速产出
ℹ️ **累计打赏为 0** - 推广力度需加强（Twitter/Reddit）

> 公司第一原则：每天必须让钱包余额增加。详细策略见 company/knowledge/daily-revenue-cockpit.md


## 当日任务清单
- [ ] task-001: llm_client.py（LLM 客户端+降级链） → 负责人: programmer（medium）
- [ ] task-002: trae_bridge.py（文件队列） → 负责人: programmer（medium）
- [ ] task-003: workspace.py / autonomous_loop.py / orchestrator.py → 负责人: programmer（medium）
- [ ] task-004: ceo_autonomous.py / cto.py / architect.py / pm.py / programmer.py / tester.py → 负责人: tester（medium）
- [ ] task-005: browser/agent_browser.py（CDP 连接） → 负责人: programmer（medium）
- [ ] task-006: crypto/（market_analyzer, opportunity_radar, learn_earn_assistant） → 负责人: programmer（medium）
- [ ] task-007: tools/（web_searcher, web_fetcher） → 负责人: programmer（medium）
- [ ] task-008: safety/（compliance, payment_gate） → 负责人: programmer（medium）
- [ ] task-009: human_loop.py（含 check_vpn） → 负责人: programmer（medium）
- [ ] task-010: keyword_analyzer / outline_generator / content_writer / template_provider → 负责人: programmer（medium）
- [ ] task-011: seo_generator.py / airdrop_assistant.py / publish_pipeline.py / tipping_tracker.py → 负责人: programmer（medium）
- [ ] task-012: **错误处理**：外部调用必须 try/except，降级链：主→备→模板 → 负责人: programmer（medium）
- [ ] task-013: **数据持久化**：YAML 配置 + Markdown 产出 + JSON 队列 → 负责人: programmer（medium）
- [ ] task-014: **命名**：文件 kebab-case，类 PascalCase，函数 snake_case → 负责人: programmer（medium）
- [ ] task-015: **测试**：新增模块必须有 test_*.py，降级链必须有故障注入测试 → 负责人: tester（medium）
- [ ] task-016: [P0] 创建 engine/business/ 目录 → 负责人: programmer（high）
- [ ] task-017: [P0] seo_generator.py MVP → 负责人: programmer（high）
- [ ] task-018: [P1] 降级链测试覆盖 → 负责人: tester（medium）
- [ ] task-019: 按既定方案推进开发 → 负责人: programmer（high）
