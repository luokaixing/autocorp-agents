# Publish0x 批量上传清单

**面向角色**: AutoCorp 内容工程师
**适用场景**: 一次性将 3 篇基于实时数据的 Publish0x 文章发布到平台
**最后验证**: 2026-06-30
**关联文档**: `registration-guide.md`（首次使用前必读）

---

## 1. 3 篇文章发布顺序建议

### 1.1 推荐发布顺序

| 顺序 | 文件名 | 主题 | 推荐发布时段 | 理由 |
|---|---|---|---|---|
| **第 1 篇** | `01-defi-yield-comparison-2026-06-30.md` | DeFi 收益对比 | Day 1 上午 10:00-11:00 | 加密社区最关注 DeFi 收益；表格型内容易读；为后续文章建立账号"专业形象" |
| **第 2 篇** | `02-layer3-earning-guide-2026-06-30.md` | Layer3 赚钱攻略 | Day 2 下午 14:00-15:00 | "赚钱攻略"类内容在 Layer3 用户活跃时段（下午）打赏率更高；与第 1 篇间隔 ≥ 24h |
| **第 3 篇** | `03-airdrop-participation-guide-2026-06-30.md` | 空投参与指南 | Day 3 晚上 19:00-21:00 | 空投话题在晚间（用户下班后浏览）打赏率最高；6 个 Confirmed 空投列表是时效性内容，越早发越好但需避开 spam 判定 |

### 1.2 顺序选择的 3 个原则

1. **时效性优先**：DeFi 收益快照数字每小时变，越早发越有"实时"价值
2. **话题梯度**：先发硬核数据（DeFi）→ 再发攻略（Layer3）→ 最后发列表（空投），逐步降低读者门槛
3. **避开 spam**：同一账号 24 小时内发布 ≥ 3 篇会被平台算法降权，**必须分 3 天发布**

### 1.3 不推荐的顺序

- ❌ 先发空投指南：时效性最低（6 个 Confirmed 状态不会快速变化），浪费首发流量红利
- ❌ 一天发 3 篇：必然触发 spam 判定，3 篇文章全部被隐藏
- ❌ 同时在多个账号发：Publish0x 检测同 IP 多账号，可能封禁全部账号

---

## 2. 每篇文章的 tags 推荐

Publish0x 每篇文章最多 6 个 tags，逗号分隔。tags 决定文章被推荐给哪类读者，直接影响打赏率。

### 2.1 文章 1: DeFi 收益对比

**文件**: `01-defi-yield-comparison-2026-06-30.md`

**推荐 tags**:
```
DeFi, Aave, Compound, Yield Farming, Stablecoin
```

**tags 选择理由**:
- `DeFi` — 平台大流量 tag，覆盖目标读者
- `Aave` / `Compound` — 文章核心对比对象，精准触达协议用户
- `Yield Farming` — 行为意图 tag，触达"在找收益"的活跃读者
- `Stablecoin` — 文章主要讨论 USDC/USDT/DAI 收益，过滤出偏好低风险读者

**备选 tags**（若上述已被占用）: `Ethereum`, `Mantle`, `Lending`

### 2.2 文章 2: Layer3 赚钱攻略

**文件**: `02-layer3-earning-guide-2026-06-30.md`

**推荐 tags**:
```
Layer3, Airdrop, Learn and Earn, Web3, Crypto
```

**tags 选择理由**:
- `Layer3` — 平台精准流量，触达已在用 Layer3 的用户
- `Airdrop` — 大流量 tag，触达"找免费 token"的读者
- `Learn and Earn` — 行为意图 tag，与 Binance L&E 同类读者重叠
- `Web3` — 泛流量 tag，扩大曝光
- `Crypto` — 兜底 tag，确保最低曝光

**备选 tags**: `Quest`, `Onchain`, `L3`

### 2.3 文章 3: 空投参与指南

**文件**: `03-airdrop-participation-guide-2026-06-30.md`

**推荐 tags**:
```
Airdrop, Free Crypto, NEAR, Web3, Crypto
```

**tags 选择理由**:
- `Airdrop` — 核心 tag，本篇主打
- `Free Crypto` — 高点击率 tag，触达"白嫖党"读者
- `NEAR` — 文章重点空投之一是 NEAR Protocol，精准触达 NEAR 社区
- `Web3` — 泛流量
- `Crypto` — 兜底

**备选 tags**: `Airdrops`, `Token`, `TGE`

### 2.4 Tags 使用禁忌

- ❌ 不要用无关 tag（如用 `Bitcoin` 标 DeFi 收益文章）——会被读者踩，降低打赏率
- ❌ 不要超过 6 个——平台报错
- ❌ 不要用空 tag（如 `, ,`）——会被判垃圾内容
- ✅ 优先用平台已有热门 tag（输入时下拉提示的）

---

## 3. 发布间隔建议（避免 spam 判定）

### 3.1 硬性间隔规则

| 场景 | 最小间隔 | 违反后果 |
|---|---|---|
| 同一账号两篇文章 | **≥ 2 小时** | 文章被隐藏 |
| 同一账号三篇文章 | **≥ 24 小时**（首篇到末篇） | 账号降权 |
| 同一账号一天发文上限 | **≤ 3 篇** | 第 4 篇起自动隐藏 |
| 同一 IP 多账号发布 | **禁止** | 全部账号封禁 |

### 3.2 推荐发布节奏（3 天计划）

#### Day 1（2026-06-30）
- **10:00** 发布第 1 篇 `01-defi-yield-comparison-2026-06-30.md`
- 10:30 自检：URL 可访问、Tip 按钮可见
- 11:00 用当日免费 tipping 额度给自己打赏一次（测试到账）
- 全天观察打赏数据，记录到 `company/config/content-ledger.yaml`

#### Day 2（2026-07-01）
- **14:00** 发布第 2 篇 `02-layer3-earning-guide-2026-06-30.md`
- 14:30 自检
- 全天观察两篇文章累计打赏

#### Day 3（2026-07-02）
- **19:00** 发布第 3 篇 `03-airdrop-participation-guide-2026-06-30.md`
- 19:30 自检
- Day 3 结束时统计 3 篇文章累计打赏，与 `realtime-opportunity-scan-2026-06-30.md` 第 1.4 节的预期范围对比

### 3.3 时段选择的理由

| 时段 | 推荐度 | 理由 |
|---|---|---|
| 上午 10:00-11:00 | ⭐⭐⭐⭐⭐ | 读者刚上班摸鱼浏览，打赏额度新鲜 |
| 下午 14:00-15:00 | ⭐⭐⭐⭐ | 午休后第二个浏览高峰 |
| 晚上 19:00-21:00 | ⭐⭐⭐⭐⭐ | 加密社区黄金时段（欧美叠加亚洲） |
| 凌晨 0:00-6:00 | ⭐ | 读者少，打赏额度已用完 |
| 饭点（12:00、18:00） | ⭐⭐ | 读者在吃饭，不刷平台 |

### 3.4 紧急情况处理

**情况 1: 文章发布后被隐藏**
- 原因：间隔过短或内容触发风控
- 处理：等待 24 小时，编辑文章（哪怕只改一个字）重新发布；若仍被隐藏，联系 Publish0x 支持

**情况 2: 发布时提示 "tag already in use" 或类似**
- 处理：换用备选 tags

**情况 3: 打赏按钮不可见**
- 处理：钱包未绑定成功，重做 `registration-guide.md` 第 3 节

---

## 4. 打赏到账后的反馈流程

### 4.1 即时反馈（每次打赏触发）

Publish0x 每次被读者打赏时会发送站内通知 + 邮件通知。收到通知后：

1. 登录 Publish0x → 查看通知中心
2. 记录打赏金额、币种、时间到 `company/config/content-ledger.yaml`：
   ```yaml
   - date: 2026-06-30
     platform: publish0x
     article: 01-defi-yield-comparison-2026-06-30
     tip_amount: 0.0008
     tip_token: ETH
     tip_usd_value: 1.26
     tipper: anonymous
   ```
3. 累计 5 次打赏后，分析打赏者行为模式（时段、文章段落），优化下一篇内容

### 4.2 日报反馈（每天结束）

每天 22:00 前，内容工程师填写 `company/daily-reports/YYYY-MM-DD-evening.md`，包含：

- 当日发布文章数
- 当日累计打赏次数
- 当日累计打赏 USD 价值
- 与预期对比（见 `registration-guide.md` 第 5.6 节）
- 异常情况（文章被隐藏、打赏异常低等）

### 4.3 提币反馈（达到提币门槛时）

当 Publish0x 平台钱包余额达到最低提币门槛时：

1. **提币前**：
   - 截图 Publish0x 钱包余额页面
   - 截图提币确认弹窗（含收款地址 `${ETH_TIPPING_ADDRESS}`）
   - 提交 COO 审批

2. **提币操作**：按 `registration-guide.md` 第 5.4 节执行

3. **提币后**：
   - 记录提币时间、金额、tx hash 到 `company/config/content-ledger.yaml`
   - 1-24 小时后通过 `engine/crypto/wallet.py` 查询到账情况
   - 到账后将链上 tx hash 与 Publish0x 提币记录关联

4. **到账确认**：
   - 链上余额增加 = 提币金额（允许 ±5% 波动，因 gas 扣除）
   - 差异 > 5% 时启动排查

### 4.4 周报反馈（每周一上午）

COO 每周一上午执行：

1. 汇总上周 Publish0x 总收入（USD）
2. 与 `realtime-opportunity-scan-2026-06-30.md` 第 1.4 节预期对比：
   - 日更 2-3 篇预期月入 $5-$30，周预期 $1.2-$7.5
3. 计算单位产出 ROI（每篇文章平均打赏）
4. 决策点：
   - 周收入 ≥ $5：保持节奏，考虑扩产
   - 周收入 $1-$5：优化标题与 tags，观察 1 周
   - 周收入 < $1：暂停发布，分析原因（账号降权？话题不对？时段不对？）
5. 决策记录到 `company/decisions/ceo-YYYY-MM-DD.md`

### 4.5 月度复盘（每月 1 日）

内容工程师 + COO 联合执行：

1. 统计上月 Publish0x 总收入、文章数、平均单篇打赏
2. 标记 Top 3 文章（打赏最高）和 Bottom 3 文章
3. 分析 Top 3 共性：话题？tags？时段？文章长度？
4. 输出本月内容策略调整建议，更新到 `company/knowledge/publish0x/batch-upload-checklist.md`（本文档）

---

## 5. 总检查清单（发布前对照）

发布每篇文章前，逐项打勾：

- [ ] 文章文件存在于 `articles/publish0x/` 目录
- [ ] 文章末尾包含 `## 支持作者 💜` 块
- [ ] 文章末尾包含 ETH 地址 `${ETH_TIPPING_ADDRESS}`
- [ ] 文章末尾包含"推荐 tags"行
- [ ] 距离上一篇发布时间 ≥ 2 小时（同日）或 ≥ 24 小时（跨日第 3 篇）
- [ ] 当前账号当日发布数 < 3
- [ ] 已准备好 5-6 个 tags（不超过 6 个）
- [ ] 已选择推荐时段（10:00-11:00 / 14:00-15:00 / 19:00-21:00）
- [ ] 编辑器切换为 Markdown 模式
- [ ] Preview 检查表格渲染正常
- [ ] Preview 检查打赏地址块显示正常
- [ ] 准备好记录打赏数据的 yaml 模板

发布后立即：
- [ ] incognito 窗口访问文章 URL，确认匿名可读
- [ ] 检查 Tip 按钮可见
- [ ] 用当日免费 tipping 额度给自己打赏一次（测试到账）
- [ ] 记录文章 URL 到 `company/config/content-ledger.yaml`

---

**文档维护**: 内容工程师
**最后更新**: 2026-06-30
**关联文件**:
- `registration-guide.md`（注册与首发）
- `company/projects/seo-content-generator/articles/publish0x/*.md`（3 篇文章）
- `company/knowledge/market-research/realtime-opportunity-scan-2026-06-30.md`（预期收入数据来源）
- `company/config/content-ledger.yaml`（收入记录）
