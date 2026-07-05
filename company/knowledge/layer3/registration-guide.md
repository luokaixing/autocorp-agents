# Layer3 注册与首任务指引

**面向角色**: AutoCorp 加密货币工程师 / 新入职运营 / 受邀用户
**适用场景**: 首次在 Layer3 平台注册智能钱包、绑定现有钱包地址、完成第一个任务、提币到主钱包
**最后验证**: 2026-06-30（WebFetch 实测 app.layer3.xyz/discover 活跃，Liquid Rewards 系统正常运行）

---

## 1. Layer3 平台介绍

### 1.1 平台定位

Layer3 是一个**链上任务聚合平台**，覆盖 40+ 链、500+ 应用、3 百万+ 用户。核心机制是让用户通过完成链上交互（swap / bridge / mint / 体验新协议）获得代币奖励，**最快路径为 Liquid Rewards（即时到账）**。

平台首页主标语（2026-06-30 实测）：

> "Get Paid to Play with Layer3 / Earn every day / Complete actions, get tokens instantly in your wallet with Liquid Rewards"

### 1.2 Layer3 的 4 大赚钱机制

| 机制 | 奖励类型 | 到账速度 | 适合人群 |
|------|----------|----------|----------|
| **Liquid Rewards** | 代币即时入账 | 即时（同交易块） | 想最快拿到第一笔收入的所有人 |
| **Curated Activations** | CUBE NFT（空投权重） | NFT 即时 mint，代币需等空投 | 长期布局空投的用户 |
| **Streaks** | Streak Bonus（叠加奖励） | 完成当日任务后即时累加 | 能每日登录的活跃用户 |
| **L3 Staking** | 质押 APY + 治理权 | 持续累计（按区块） | 已持有 L3 代币的用户 |

### 1.3 为什么 AutoCorp 选择 Layer3 作为 P0 路径

根据 `company/knowledge/market-research/realtime-opportunity-scan-2026-06-30.md` 第 1.1 节实测数据：

- **即时到账**: Liquid Rewards 任务完成后代币在同一个交易块入账，无需 TGE 等待
- **零成本启动**: 一键智能钱包，无 gas 预付、无浏览器插件、无 KYC
- **收益区间合理**: 单任务 $0.5–$20，日做 3-5 任务预期 $2–$30
- **平台活跃**: 2026-06-30 WebFetch 实测页面活跃，3 百万+ 用户
- **L3 代币已上线**: 现价约 $0.0064（24h +10%），可即时变现

### 1.4 平台核心规则（务必遵守）

| 规则 | 说明 | 违反后果 |
|------|------|----------|
| 一钱包一账号 | Layer3 智能钱包与链上地址绑定，禁止多账号女巫 | 账号封禁 + 空投资格取消 |
| 真实交互 | 任务交互必须是真实链上行为，禁止脚本刷量 | 任务作废 + 账号降权 |
| Streak 连续 | Streaks 每日至少完成 1 任务，中断归零 | 仅影响个人 Streak 奖励 |
| CUBE 不可转让 | CUBE NFT 为 soulbound 风格，记录参与历史 | 转让不可行，无后果 |

---

## 2. 注册步骤（创建 Layer3 智能钱包）

> **核心优势**: Layer3 智能钱包是**一键创建的智能合约钱包**，无需 MetaMask 插件、无需预付 gas、无需 KYC。整个流程 2 分钟内完成。

### Step 1: 访问 Layer3 官网

打开浏览器，访问：**https://app.layer3.xyz**

> 建议使用 Chrome 浏览器 + 项目 chrome-profile（位于 `d:\autoCompany\chrome-profile`），便于后续自动化。

### Step 2: 点击 "Create Wallet"

页面右上角或中央会显示 **Create Wallet** / **Get Started** 按钮，点击进入钱包创建流程。

### Step 3: 一键创建智能钱包（无 gas、无插件）

Layer3 会自动为你创建一个**智能合约钱包**（account abstraction 钱包），流程：

1. 系统生成一个新的钱包地址（无需手动记录私钥，由 Layer3 智能合约托管）
2. **无需安装 MetaMask 或任何浏览器插件**
3. **无需预付 ETH 作为 gas**（gasless 体验，gas 由任务方/平台补贴）
4. 设置恢复方式（强烈建议绑定邮箱作为恢复凭证）

### Step 4: 绑定恢复邮箱（推荐）

- 在钱包创建流程中系统会提示绑定邮箱
- 使用 AutoCorp 公共内容邮箱（向 COO 申请分配，不使用个人邮箱）
- 邮箱仅用于钱包恢复，不做营销推送
- 收到验证邮件后点击验证链接完成绑定

### Step 5: 进入 Discover 页确认钱包已激活

1. 创建完成后自动跳转到 **app.layer3.xyz/discover**
2. 页面右上角应显示你的新钱包地址（前 6 位 + 后 4 位，如 `0x1234...5678`）
3. 浏览任务列表，确认能看到任务卡片（说明钱包已激活并可参与任务）

> **此时钱包内余额为 0 是正常的**——完成 Liquid Rewards 任务后才会进账。

---

## 3. 绑定现有钱包地址 `${ETH_TIPPING_ADDRESS}` 的步骤

### 3.1 为什么要绑定现有钱包地址

`${ETH_TIPPING_ADDRESS}` 是 AutoCorp 公司公共 Receive 钱包（与 Publish0x 打赏地址一致），所有 Layer3 收益统一汇入此地址便于对账。

Layer3 智能钱包本身是独立的合约钱包，但**收益提币时需要指定接收地址**。绑定流程分两种方式：

### 3.2 方式 A：在 Layer3 提币设置中绑定（推荐）

1. 登录 Layer3 智能钱包 → 点击右上角钱包地址 → **Settings**（设置）
2. 进入 **Withdrawal Address** / **Payout Address** 标签页
3. 在输入框中粘贴 AutoCorp 公共钱包地址：
   ```
   ${ETH_TIPPING_ADDRESS}
   ```
4. 点击 **Save** / **Confirm**
5. 系统可能要求邮箱二次确认——打开邮箱点击确认链接完成绑定
6. 返回 Settings 页确认地址显示正确且无 "Pending Verification" 标识

### 3.3 方式 B：每次提币时手动指定（备选）

若 Settings 中无固定提币地址选项，则每次提币时在提币表单中填入：

```
${ETH_TIPPING_ADDRESS}
```

> **重要**: 提币前务必核对此地址，错填一个字符资金将永久丢失。建议将此地址存入浏览器自动填充或密码管理器。

### 3.4 绑定外部 EOA 钱包（可选，用于 CUBE 空投快照）

部分 Layer3 空投快照会基于绑定的 EOA 钱包地址（如 MetaMask 地址）：

1. 在 Layer3 Settings → **Connected Wallets**
2. 点击 **Connect Wallet** → 选择 MetaMask（或对应 EOA 钱包）
3. 在 MetaMask 中确认连接
4. 连接后该 EOA 地址将与 Layer3 账号关联，参与空投快照

> 若要使用 AutoCorp 主 EOA 钱包（`${ETH_TIPPING_ADDRESS}`）参与空投快照，需在 MetaMask 中导入此地址对应的私钥（私钥存放在 `d:\autoCompany\.secrets\private_key_for_import.txt`，仅 COO 有访问权限）。

### 3.5 验证绑定成功

1. 返回 Settings 页面，确认 AutoCorp 地址显示在 Withdrawal Address 字段
2. 完成首个 Liquid Rewards 任务后，提币时核对默认收款地址是否为 AutoCorp 地址
3. 通过 `engine/crypto/wallet.py` 查询 `${ETH_TIPPING_ADDRESS}` 余额变化以验证到账

---

## 4. 完成第一个任务的步骤

### 4.1 任务选择建议

**首个任务推荐**: DEX Swap 任务（Liquid Rewards）

- 难度最低，操作最简单
- 预期收益 $0.5–$5
- 即时到账，能立即验证整个流程是否跑通
- 不需要大额本金（约 $1-10 等值资产即可）

### 4.2 详细操作步骤

#### Step 1: 进入 Discover 页筛选任务

1. 登录 Layer3 智能钱包 → 进入 **app.layer3.xyz/discover**
2. 在筛选栏选择：
   - **Reward Type**: Liquid Rewards（即时到账）
   - **Chain**: 选择低 gas 链（推荐 Base 或 Optimism，gas 约 $0.01）
   - **Task Type**: Swap
3. 浏览任务列表，选择一个标记 **Liquid Rewards** 的 swap 任务

#### Step 2: 阅读任务要求

点击任务卡片进入任务详情页，记录：

- **任务名称**（如 "Swap on Uniswap V3"）
- **奖励代币**（如 USDC / ETH / L3）
- **奖励金额**（如 $2）
- **要求操作**（如 "Swap at least $5 worth of any token on Uniswap V3"）
- **截止时间**（如有）

#### Step 3: 准备少量本金（如需要）

DEX Swap 任务通常需要少量本金：

1. 若 Layer3 智能钱包内无资产：从外部钱包（如 AutoCorp 主钱包或交易所）转入少量 ETH（$5-10 即可）到 Layer3 智能钱包地址
2. 转入后等待 1-2 个区块确认（约 30 秒-1 分钟）
3. 在 Layer3 钱包余额页面确认到账

> **NFT Mint 任务无需本金**——若想完全零成本启动，可选 NFT Mint 任务作为首个任务。

#### Step 4: 执行任务链上交互

1. 在任务详情页点击 **Start Task** / **Go to App** 按钮
2. Layer3 会跳转到目标 DEX（如 Uniswap）并自动连接你的 Layer3 智能钱包
3. 在 DEX 上完成要求的 swap 操作：
   - 输入 swap 数额（达到任务要求的最小金额）
   - 确认滑点容忍度（建议 0.5%-1%）
   - 点击 Swap → 在 Layer3 钱包弹窗中确认交易
4. 等待交易上链确认（通常 10-30 秒）

#### Step 5: 返回 Layer3 确认任务完成

1. 交易上链后返回 app.layer3.xyz 任务详情页
2. 页面应自动显示 **Task Completed** / **Verified** 状态
3. **Liquid Rewards 代币即时入账**——在 Layer3 钱包余额页面可立即看到新增代币
4. CUBE 任务则 mint 出 CUBE NFT，在钱包 NFT 标签页可查看

#### Step 6: 截图存档

完成任务后立即截图保存：

- 任务完成状态截图
- Layer3 钱包余额截图（显示新增代币）
- 链上交易 hash（复制保存）

截图存入 `company/knowledge/layer3/screenshots/` 目录（按日期+任务名命名），用于后续对账。

### 4.3 首任务常见问题排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 任务页不显示完成 | 链上交易未确认 | 等待 1-2 分钟刷新；查看 Etherscan 交易状态 |
| Liquid Rewards 未到账 | 任务方延迟发放（罕见） | 等待 5-10 分钟；联系 Layer3 Discord 客服 |
| Swap 交易失败 | gas 不足或滑点过低 | 增加 gas；调高滑点至 1%-2% |
| 钱包连接失败 | 浏览器拦截弹窗 | 允许 app.layer3.xyz 弹窗权限 |
| 任务卡片显示 "Coming Soon" | 任务未开放 | 选择其他已开放任务 |

---

## 5. Liquid Rewards 到账机制说明

### 5.1 什么是 Liquid Rewards

Liquid Rewards 是 Layer3 的**即时到账奖励机制**，与传统的空投等待模式根本不同：

| 维度 | Liquid Rewards | 传统空投 / CUBE |
|------|----------------|------------------|
| 到账时间 | 同一交易块即时入账 | TGE 后数周-数月 |
| 资金来源 | 任务方当下出资 | 项目方未来发币分配 |
| 确定性 | 100% 确定拿到 | 不确定（可能 TGE 失败、可能份额小） |
| 价值 | 当下可变现 | 未来才知价值 |

### 5.2 到账流程（技术细节）

1. 用户完成任务链上交互（如 swap）
2. Layer3 后端监听链上事件，验证任务完成
3. 触发 Liquid Rewards 智能合约，向用户 Layer3 钱包转账奖励代币
4. 转账与任务完成在同一交易块内（或下一区块）执行
5. 用户 Layer3 钱包余额即时增加

整个过程**无需用户手动 Claim**（部分任务可能需点击 Claim 按钮，但大多数 Liquid Rewards 是自动发放）。

### 5.3 奖励代币类型

Liquid Rewards 奖励代币由任务方决定，常见类型：

- **稳定币**: USDC / USDT / DAI（价值稳定，最适合新手）
- **主流币**: ETH / MATIC / OP（价值随市场波动）
- **L3 代币**: Layer3 平台代币（现价约 $0.0064，24h +10%）
- **任务方代币**: 新协议的代币（波动大，建议尽快变现）

### 5.4 到账金额如何核对

1. 任务详情页显示的奖励金额（如 "$2"）是**任务方承诺的法币等值**
2. 实际到账的是代币，数量 = 承诺金额 / 代币当时价格
3. 例如承诺 $2，奖励代币为 L3（$0.0064），则到账约 312.5 L3
4. 代币价格波动期间，到账后代币价值可能涨跌

### 5.5 即时到账验证

完成任务后立即验证到账：

1. Layer3 钱包余额页面刷新，查看代币余额
2. 在对应链的区块浏览器（如 basescan.org）查看 Layer3 钱包地址的最新交易
3. 应能看到一笔来自 Layer3 Rewards 合约的代币转账
4. 通过 `engine/crypto/wallet.py` 查询 Layer3 钱包余额变化

---

## 6. 提币到主钱包的步骤

### 6.1 为什么要提币到主钱包

- **统一对账**: AutoCorp 所有加密收入汇入 `${ETH_TIPPING_ADDRESS}`，由 COO 每周对账
- **安全保管**: Layer3 智能钱包为操作钱包，余额不宜长期累积
- **便于变现**: 主钱包连接交易所账户，可随时变现为法币

### 6.2 提币前准备

1. 确认 Layer3 智能钱包内有可提现代币余额
2. 确认第 3 节的提币地址已绑定为 `${ETH_TIPPING_ADDRESS}`
3. 确认 Layer3 智能钱包内有足够 gas 支付提币交易（部分链 Layer3 提供 gasless 提币）

### 6.3 提币操作步骤

#### Step 1: 进入 Layer3 钱包页面

1. 登录 app.layer3.xyz
2. 点击右上角钱包地址 → **Wallet** / **Portfolio**

#### Step 2: 选择要提币的代币

1. 在钱包余额列表中找到要提的代币（如 L3 / USDC / ETH）
2. 点击代币右侧的 **Withdraw** / **Send** 按钮

#### Step 3: 填写提币信息

1. **收款地址**: 粘贴 AutoCorp 主钱包地址
   ```
   ${ETH_TIPPING_ADDRESS}
   ```
2. **金额**: 输入要提的数量（可选 Max 全部提取）
3. **核对网络**: 确认提币所在链（如 Ethereum 主网 / Base / Optimism）

> **关键检查**: 收款地址必须以 `${ETH_PREFIX}789` 开头并以 `D86942` 结尾。错一个字符资金永久丢失。

#### Step 4: 确认提币交易

1. 点击 **Confirm** / **Withdraw**
2. Layer3 智能钱包弹窗显示交易详情（金额 + gas）
3. 再次核对收款地址正确
4. 点击确认发送交易

#### Step 5: 等待到账并验证

1. 提币交易通常 1-10 分钟上链确认（视链的拥堵程度）
2. 复制交易 hash 到对应区块浏览器查看确认状态
3. 到账后通过 `engine/crypto/wallet.py` 查询主钱包 `${ETH_TIPPING_ADDRESS}` 余额变化
4. 在 `company/config/wallet_balance_state.yaml` 记录本次提币：
   ```yaml
   - date: 2026-06-30
     source: layer3
     token: L3
     amount: 312.5
     tx_hash: 0x...
     status: confirmed
   ```

### 6.4 提币成本优化

- **优先在低 gas 链提币**: Base / Optimism / Mantle 的 gas 约 $0.01-0.05，远低于 Ethereum 主网（$2-15）
- **累积后批量提币**: 单次提币金额过小不划算（gas 占比高），建议累积到等值 $10-20 后再提
- **利用 gasless 提币**: Layer3 对部分链提供 gasless 提币体验（gas 由平台补贴），优先选择这类链提币
- **跨链提币谨慎**: 若 Layer3 钱包在 Base 链而主钱包期望在 Ethereum 主网收到，需先跨链——这会增加成本与复杂度，建议直接在原链提币，主钱包支持多链接收

### 6.5 提币失败排查

| 问题 | 原因 | 解决方案 |
|------|------|----------|
| 提币交易 pending 过久 | gas 设置过低 | 在钱包中加速交易（Speed Up） |
| 提币交易失败 | gas 不足或合约错误 | 补充 gas 后重试；联系 Layer3 客服 |
| 主钱包未收到 | 收款地址填错 | 立即核对交易 hash；错填无法找回 |
| 主钱包收到但金额不符 | 代币价格波动 / gas 扣除 | 这是正常的，区块浏览器可查净额 |
| L3 代币无法提币 | L3 合约限制 | 部分 L3 可能有解锁期，查看任务详情页说明 |

### 6.6 收入对账流程

每周一上午，COO 执行：

1. 调用 `engine/crypto/wallet.py` 查询 `${ETH_TIPPING_ADDRESS}` 的余额变化
2. 与 Layer3 平台的提币记录比对
3. 与 `company/config/wallet_balance_state.yaml` 中本周 Layer3 提币条目比对
4. 差异 > $0.50 时启动人工排查
5. 记录到 `company/config/content-ledger.yaml`

---

## 附录 A：当日任务清单参考

完整当日任务清单见：`company/knowledge/layer3/tasks-2026-06-30.md`

任务清单包含：
- 平台当前状态
- 7 个活跃任务/机制
- 4 个 Liquid Rewards 即时到账任务
- 每个任务的预期收益区间
- 当日执行计划

## 附录 B：相关文档与工具

| 文档/工具 | 路径 | 用途 |
|-----------|------|------|
| 实时扫描报告 | `company/knowledge/market-research/realtime-opportunity-scan-2026-06-30.md` | Layer3 平台活跃性验证数据源 |
| 当日任务清单 | `company/knowledge/layer3/tasks-2026-06-30.md` | 当日可执行任务列表 |
| Layer3 监控器 | `engine/crypto/layer3_task_monitor.py` | 自动抓取任务 + 生成清单 |
| 钱包余额查询 | `engine/crypto/wallet.py` | 查询主钱包与 Layer3 钱包余额 |
| 收益监控 | `engine/crypto/income_monitor.py` | 监控加密收入到账 |
| 余额状态 | `company/config/wallet_balance_state.yaml` | 提币记录与余额状态 |
| 内容账本 | `company/config/content-ledger.yaml` | 每周收入对账 |
| Publish0x 注册指引 | `company/knowledge/publish0x/registration-guide.md` | 同地址用于 Publish0x 打赏（双轨并行） |

## 附录 C：常见问题 FAQ

**Q1: Layer3 智能钱包和 MetaMask 有什么区别？**
A: Layer3 智能钱包是智能合约钱包（account abstraction），无需浏览器插件、无需预付 gas、无需管理私钥（由 Layer3 托管+邮箱恢复）。MetaMask 是 EOA 钱包，需安装插件、手动管理私钥、需自付 gas。Layer3 智能钱包更适合任务交互，MetaMask 更适合长期资产保管。

**Q2: 完成任务获得的 L3 代币应该立刻变现吗？**
A: 当前 L3 现价 $0.0064 且 24h +10% 波动较大。建议：必需现金流时即时变现；可承受波动的情况下可持有观察。但不要 all-in 长期持有——L3 是 utility token，价格大幅波动常见。

**Q3: 一个 Layer3 账号可以绑定多个钱包地址吗？**
A: 一个 Layer3 账号对应一个 Layer3 智能钱包地址，但可在 Settings → Connected Wallets 中连接多个 EOA 钱包（如 MetaMask）用于空投快照。AutoCorp 政策：每个 Layer3 账号仅绑定 AutoCorp 主 EOA 钱包 `${ETH_TIPPING_ADDRESS}`，禁止多账号女巫行为。

**Q4: Layer3 任务可以用脚本自动化吗？**
A: Layer3 明确禁止脚本刷量，违反会封号。AutoCorp 政策：仅用 `engine/browser/agent_browser.py` 自动化**任务发现与监控**（浏览 Discover 页、记录任务列表），**链上交互必须由人工点击确认**。未来若 Layer3 开放官方 API，可考虑合规自动化。

**Q5: 如果 Layer3 平台被黑或跑路怎么办？**
A: Layer3 智能钱包是独立智能合约，即使 Layer3 前端宕机，钱包资产仍属于你（可通过其他钱包客户端访问合约）。但 Liquid Rewards 代币若在 Layer3 钱包内未及时提币，理论上存在风险。建议：**收到 Liquid Rewards 后 24 小时内提币到主钱包**，不要在 Layer3 钱包长期累积。

---

**文档维护**: 加密货币工程师
**最后更新**: 2026-06-30
**数据来源**: `company/knowledge/market-research/realtime-opportunity-scan-2026-06-30.md` §1.1 实测验证
**主钱包地址**: `${ETH_TIPPING_ADDRESS}`
