# dev.to 内容策略 —— AutoCorp AI 公司首批技术文章发布计划

> 文档负责人：内容总监（AutoCorp AI）
> 创建日期：2026-06-30
> 文档目的：把已有内容资产（art_001 / art_004）+ 真实研究过程改写为 dev.to 技术文章，解锁后立即发布，建立"技术文章 + Paragraph ETH 打赏"闭环。
> 数据来源：本策略所有平台结论基于 `company/knowledge/strategic-research/us-market-revenue-research-2026-06-30.md`（2026-06-30 当日 WebFetch 实时验证），文章内容基于 `company/projects/seo-content-generator/articles/` 下的真实文章资产 + `scripts/fetch_defi_realtime.py` 真实研究过程。

---

## 一、dev.to 平台特点分析（基于美国市场研究报告实时验证）

### 1.1 平台实时验证结论（2026-06-30）

来源：`company/knowledge/strategic-research/us-market-revenue-research-2026-06-30.md` 第四章赛道 3，实时 WebFetch 验证。

| 维度 | 验证结论 | 验证方式 |
|---|---|---|
| 平台可访问性 | ✅ 2026-06-30 当日可访问（https://dev.to/） | WebFetch 实时抓取 |
| 社区活跃度 | 首页实时显示"DEV Takeovers - The Daily Context: First Edition"，DEV 与 Major League Hacking (MLH) 合作覆盖 AI Engineer World's Fair | WebFetch 抓取首页内容 |
| 注册门槛 | 低 —— 免费注册，邮箱验证 / GitHub 登录 | 研究报告确认 |
| 直接变现机制 | ❌ 无 Partner Program、无付费墙 | 研究报告确认 |
| 间接变现路径 | (1) 文章底部挂 sponsor 链接（需 1K followers）；(2) Forest Protocol ETH 打赏；(3) 导流至 Paragraph ETH 打赏闭环 | 研究报告确认 |
| 新作者曝光 | dev.to 算法对新作者友好，首篇 100-500 浏览为常见区间 | 研究报告确认 |
| 30 天打赏预期 | $0-15（保守，零粉丝期） | 研究报告确认 |

### 1.2 平台特点对内容策略的约束

1. **dev.to 是导流通道，非独立变现渠道**。CEO 竞争力预筛结论："有条件通过（3 项通过 + 2 项弱通过），作为导流通道非独立变现"。因此所有 dev.to 文章的最终目标都是把读者引导到 Paragraph 打赏地址 `${ETH_TIPPING_ADDRESS}`，而不是指望 dev.to 自身付费。
2. **dev.to 偏好"真实开发者经验 + 代码示例"**。纯 AI 生成、无代码块、无 API 调用、无合约交互的文章易被识别为低质。因此改写策略是：每篇必须含可运行/可验证的代码块或数据表，并把"实时研究过程"本身作为内容卖点（art_004 的 DefiLlama + CoinGecko 实时抓取正是这种资产）。
3. **Markdown 原生支持**。dev.to 文章用 Markdown + front matter（`title` / `published` / `tags` / `cover_image` / `canonical_url`），最多 4 个标签。这让公司可以无成本复用已有 Paragraph 文章的 Markdown 资产，只需加代码块和标签。
4. **新作者友好但粉丝积累慢**（followers 积累周期 3-6 个月）。因此首批 3 篇是"质量压舱石"，不求量，求每篇都被算法判定为高质以获取初始 followers。

### 1.3 与其他平台的对比（为什么不选 Hashnode / Medium）

来源：同上研究报告赛道 3 小结。

| 平台 | 2026-06-30 状态 | 是否采用 | 原因 |
|---|---|---|---|
| dev.to | ✅ 可访问，社区活跃 | ✅ 主通道 | 算法对新作者友好，Markdown 原生，无身份/Stripe 阻塞 |
| Hashnode | ❌ /prizes 返回 404 | ❌ 不采用 | 奖金赛页面已下线，当前无活跃变现路径，状态不确定 |
| Medium 技术专栏 | ❌ 结构性阻塞 | ❌ 不采用 | Medium Partner Program 不接受中国大陆身份（MPP 申请页国家选项无 China），与 dev.to 不同 |

**结论**：dev.to 是美国开发者社区赛道中 2026-06-30 唯一通过 CEO 竞争力预筛、且无 Stripe/身份结构性阻塞的平台。它是中国大陆主体唯一可立即启动的技术文章导流通道。

---

## 二、内容定位（AI + Crypto + Developer 教育交叉领域）

### 2.1 定位三角

AutoCorp AI 公司在 dev.to 的内容定位是三个领域的交叉点：

```
            AI（实时 Web 研究 + 多 agent 编排 + 内容生产）
             /
            /
           / 
          X ────── Developer 教育（代码示例 + API 调用 + 合约交互 + 安全实践）
          \
           \
            \
             Crypto（DeFi 收益 + 钱包安全 + 空投 + Web3 入门）
```

这个交叉点的判断依据：
- dev.to 用户主体是开发者，纯 Crypto 内容（无代码）会被算法和读者双重降权；
- 但纯开发者教程（无 Crypto）竞争红海，AI 公司无差异化；
- AI + Crypto + Developer 教育交叉领域是 dev.to 上相对蓝海：既有代码深度，又有 Crypto 话题热度，又能展示 AI 公司"实时 Web 研究"的独家能力。

### 2.2 内容差异化卖点（AI 公司组合壁垒）

研究报告明确指出 dev.to 单点壁垒"弱"——任何开发者用 AI 都能写技术博客。AI 公司的组合壁垒体现在"三个能力的串联"，而不是单一能力：

1. **实时 Web 研究**：通过 `scripts/fetch_defi_realtime.py` 调用 DefiLlama Yields API（238 Aave pools + 119 Compound pools）+ DefiLlama Protocols API（7742 protocols，624 lending）+ CoinGecko Price API，抓取当下真实数据。这是任何"用 ChatGPT 写一篇 DeFi 文章"的人做不到的——他们只能引用过期数字。
2. **多 agent 编排**：可并行执行"数据抓取 → 数据校验 → 文章撰写 → 标签优化 → 发布"流水线，单人串行只能一次做一篇。
3. **内容生产**：英文技术写作能力（已验证 3 篇 Paragraph 文章）。

**卖点表述**（用于文章中反复强化）：*"Every number in this article was pulled live from DefiLlama and CoinGecko APIs at a verifiable timestamp — not from memory, not from a stale guide."*

### 2.3 内容红线

- ❌ 不编造数据。所有 APY / TVL / 价格必须来自 `defi-yield-snapshot-2026-06-30.json` 或可重跑的脚本。
- ❌ 不发纯 AI 生成、无代码块的文章。
- ❌ 不在 dev.to 文章里直接放募资/推销语言；CTA 只引导到 Paragraph 打赏。
- ✅ 每篇文章必须包含可验证的代码块、数据表或 API 调用示例。

---

## 三、首批 3 篇文章发布计划

发布策略：3 篇间隔 2-3 天发布，让每篇有 48-72 小时算法曝光窗口，避免互相稀释。

| 序号 | 文章标题（英文） | 本地文件 | 发布日期（建议） | 预期标签（≤4） | 字数 | 内容来源 |
|---|---|---|---|---|---|---|
| 01 | How an AI Company Does Real-Time Crypto Market Research | `article-01-ai-powered-crypto-research.md` | 2026-07-02（周四） | `#ai` `#crypto` `#web3` `#tutorial` | 1500-2000 | 全新撰写，引用 art_004 真实研究过程 |
| 02 | Where to Earn the Highest DeFi Yield Right Now: A Real-Time Comparison | `article-02-defi-yield-comparison.md` | 2026-07-05（周日） | `#defi` `#crypto` `#blockchain` `#tutorial` | 2000-2500 | 基于 art_004 改写为技术深度版 |
| 03 | The Developer's Guide to Ethereum Wallets in 2026: Architecture, APIs & Security | `article-03-ethereum-wallet-guide.md` | 2026-07-08（周三） | `#ethereum` `#web3` `#security` `#tutorial` | ~2000 | 基于 art_001 改写为开发者向技术版 |

### 3.1 发布顺序逻辑

1. **首篇发 art_01（AI 公司如何做实时加密研究）**：这是公司能力宣言，建立"我们是基于实时数据的研究者"的人设，为后续两篇的可信度背书。首发选周四——dev.to 工作日流量更稳。
2. **第二篇发 art_02（DeFi 收益对比）**：在首篇建立了"实时数据"信任后，用 art_004 的硬数据展示研究能力。这是 3 篇中数据最硬、最可能被算法判定为高质的一篇。
3. **第三篇发 art_03（以太坊钱包指南）**：经典长青教程，标签 `#ethereum` `#security` `#beginners` 在 dev.to 流量稳定，作为收尾把 followers 沉淀下来。

---

## 四、长期内容节奏

### 4.1 启动期（第 1-4 周）

- 节奏：每周 2-3 篇（研究报告建议"每周 1-2 篇"，本策略上调至 2-3 篇以快速建立初始 followers，因为已有 4 篇 Paragraph 资产可改写复用）
- 来源：复用 art_002（空投指南）+ art_003（Aave 协议）+ 实时研究快照
- 目标：4 周内累计 8-12 篇，单篇 100-500 浏览，累计 followers 50-200

### 4.2 稳定期（第 2-3 个月）

- 节奏：每周 2 篇
- 内容方向：
  - 每周 1 篇实时数据快照（重跑 `fetch_defi_realtime.py`，更新 APY 对比）
  - 每周 1 篇技术教程（钱包安全 / 合约交互 / 空投参与 / Layer3 任务）
- 目标：单篇稳定 300-1000 浏览，followers 累计 200-500，开始有 sponsor 链接资格（1K followers 门槛的 20-50%）

### 4.3 内容资产复用矩阵

一篇 dev.to 文章 = 一篇 Paragraph 文章的"技术向改写版"，实现一次研究、多平台分发：

```
实时研究脚本 (fetch_defi_realtime.py)
        │
        ▼
   原始数据快照 (JSON)
        │
        ├─→ Paragraph 文章（面向加密读者，重叙事 + CTA 打赏）
        ├─→ dev.to 文章（面向开发者，重代码 + 数据表 + CTA 打赏）
        └─→ Twitter 推文（5 条推文串，引流到两个长文）
```

---

## 五、引流策略（dev.to → Paragraph 打赏 + Twitter 引流）

### 5.1 引流闭环

```
dev.to 技术文章（带代码 + 数据表，建立信任）
        │
        ▼ 文章末尾 CTA
Paragraph 文章页（ETH 打赏按钮）
        │
        ▼ 读者打赏
MetaMask 收款（地址 ${ETH_TIPPING_ADDRESS}）
        ▲
        │
Twitter 推文串（@LUOKAIXING 账号，5 条推文，引流到 dev.to + Paragraph）
```

### 5.2 CTA 模板（每篇文章末尾固定使用）

每篇 dev.to 文章末尾必须包含以下结构（英文，与文章语言一致）：

```markdown
---

## Support This Research

If this real-time, data-driven analysis helped you, consider tipping the author.
Every tip funds the next API snapshot and more free, verifiable research.

💸 **ETH tipping address**: `${ETH_TIPPING_ADDRESS}`

You can also tip directly on the Paragraph mirror of this article,
where ETH tips support ongoing AI-powered crypto research:

🔗 Paragraph: https://paragraph.com/@autocorp-insights

Follow on Twitter for real-time findings: [@LUOKAIXING](https://x.com/LUOKAIXING)
```

### 5.3 Twitter 引流策略

每篇 dev.to 文章发布后，同步发 1 条推文串（5 条）：

1. 推文 1：文章标题 + dev.to 链接 + 1 个关键数据点（如"Aave USDC on Mantle 8.39% APY — pulled live from DefiLlama"）
2. 推文 2-4：文章中 2-3 个核心图表/数据表的截图
3. 推文 5：CTA —— "Full article on dev.to + ETH tip jar: ${ETH_TIPPING_ADDRESS}"

Twitter 账号 `@LUOKAIXING` 已有 art_003 推文（https://x.com/LUOKAIXING/status/2071607658143211721），处于养号期，dev.to 文章为养号提供高质量内容素材。

### 5.4 dev.to 站内引流

- 每篇文章末尾的"About the Author"区块挂 Paragraph 链接
- 在 `#discuss` 标签下参与相关讨论，自然带出公司文章
- 4 周内不主动求 follow，靠文章质量触发算法推荐

---

## 六、标签策略

### 6.1 dev.to 标签规则

- 每篇文章最多 4 个标签
- 标签必须是 dev.to 已有的社区标签（不能自创）
- 标签顺序影响算法权重（第一个标签权重最高）

### 6.2 标签池（按主题）

| 主题 | 主标签（高权重，放第 1 位） | 辅标签（放第 2-4 位） |
|---|---|---|
| AI 研究 | `#ai` | `#productivity` `#tutorial` `#machinelearning` |
| DeFi 收益 | `#defi` | `#crypto` `#blockchain` `#finance` `#tutorial` |
| 钱包安全 | `#ethereum` | `#web3` `#security` `#beginners` `#tutorial` |
| 空投参与 | `#crypto` | `#web3` `#blockchain` `#tutorial` `#beginners` |
| 协议机制 | `#blockchain` | `#defi` `#crypto` `#tutorial` |

### 6.3 首批 3 篇标签分配

| 文章 | 标签（顺序即权重） | 选择理由 |
|---|---|---|
| art_01 AI 研究方法 | `#ai` `#crypto` `#web3` `#tutorial` | `#ai` 放首位突出 AI 公司身份；`#crypto` `#web3` 锁定目标读者；`#tutorial` 提升算法友好度 |
| art_02 DeFi 收益对比 | `#defi` `#crypto` `#blockchain` `#tutorial` | `#defi` 精准命中 DeFi 开发者；3 个 crypto 相关标签扩大覆盖；`#tutorial` 提升曝光 |
| art_03 钱包指南 | `#ethereum` `#web3` `#security` `#tutorial` | `#ethereum` 主标签流量大；`#security` 锁定安全敏感开发者；`#tutorial` + `#beginners` 二选一（本篇定位开发者向，选 `#tutorial`） |

### 6.4 标签纪律

- ❌ 不蹭无关热门标签（如 `#javascript` `#python` 出现在纯 crypto 文章里）——会被算法降权
- ❌ 不用超过 4 个标签
- ✅ 每篇至少 1 个 `#tutorial` 或 `#beginners`（提升新作者曝光）
- ✅ 主标签必须与文章核心主题精确匹配

---

## 七、成功指标与验收

| 指标 | 30 天目标 | 90 天目标 | 验收方式 |
|---|---|---|---|
| dev.to 发布文章数 | 8-12 篇 | 20-30 篇 | dev.to 作者页 URL 可查 |
| 单篇浏览量 | 100-500 | 300-1000 | dev.to 后台数据 |
| dev.to followers | 50-200 | 200-500 | dev.to 作者页可查 |
| Paragraph 打赏（ETH） | $0-15 | $15-80 | MetaMask 地址 ${ETH_TIPPING_ADDRESS} 链上交易可查 |
| Twitter 引流推文 | 8-12 条串 | 20-30 条串 | @LUOKAIXING 账号可查 |

**诚实声明**（沿用研究报告口径）：dev.to + Paragraph 闭环在零粉丝期打赏概率极低，30 天目标为"启动分发 + 验证闭环"，非法币收入。首笔打赏现实预期为 30-90 天后 $0-15 ETH。

---

## 八、关联文档与资产

- 内容发布追踪账本：`company/config/content-ledger.yaml`
- 美国市场研究报告（实时验证依据）：`company/knowledge/strategic-research/us-market-revenue-research-2026-06-30.md`
- 战略重分析（P2 路径定义）：`company/decisions/strategic-reanalysis-2026-06-30.md`
- 首笔收入 playbook：`company/knowledge/playbooks/first-income-playbook.md`
- art_001 原文（钱包指南）：`company/projects/seo-content-generator/articles/04-ethereum-wallet-guide-v2.md`
- art_004 原文（DeFi 收益对比）：`company/projects/seo-content-generator/articles/04-defi-yield-comparison-2026-06-30.md`
- 实时数据抓取脚本：`scripts/fetch_defi_realtime.py`
- DeFi 数据快照：`company/knowledge/market-research/defi-yield-snapshot-2026-06-30.json`
- Paragraph 打赏地址：`${ETH_TIPPING_ADDRESS}`（MetaMask）

---

## 九、发布前检查清单（每篇 dev.to 文章发布前过一遍）

- [ ] front matter 含 `title` / `published: true` / `tags`（≤4）/ `cover_image`
- [ ] `canonical_url` 指向 Paragraph 原文（避免重复内容惩罚）
- [ ] 至少 1 个可运行/可验证的代码块或数据表
- [ ] 文章末尾含固定 CTA（ETH 打赏地址 + Paragraph 链接 + Twitter）
- [ ] 标签顺序符合本策略第六章规则
- [ ] 字数达标（art_01: 1500-2000；art_02: 2000-2500；art_03: ~2000）
- [ ] 所有数据来自 `defi-yield-snapshot-2026-06-30.json` 或可重跑脚本，无编造
- [ ] 英文撰写（dev.to 是美国开发者社区）
- [ ] 发布后 1 小时内发 Twitter 推文串
