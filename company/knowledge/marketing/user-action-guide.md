# 用户操作指引 - 加密货币零成本赚钱全套流程

> 生成时间：2026-06-27
> 收款钱包：`${ETH_TIPPING_ADDRESS}` (Ethereum)
> 预期收益：第 1 月 $65-270

---

## 🔑 关键前置：获取你的钱包私钥

**为什么需要私钥**：Mirror.xyz 等平台需要用钱包登录，部分平台提现也需要钱包签名。

### 操作步骤
1. 打开文件资源管理器，导航到：`d:\autoCompany\.secrets\`
2. 用**记事本**打开 `secrets.json` 文件
3. 找到这一行（在文件中）：
   ```
   "wallet_ethereum_c0f3789c_priv": "一长串十六进制字符"
   ```
4. 复制双引号内的那一长串字符（64 位十六进制，不含 `0x` 前缀）
5. 这就是你的**钱包私钥**，请妥善保管，**不要发给我、不要发到任何网站、不要截图分享**

### ⚠️ 私钥安全警告
- ✅ 可以粘贴到 MetaMask 导入钱包
- ✅ 可以本地保存备份
- ❌ **绝不**粘贴到任何聊天工具、邮件、网站表单（MetaMask 官网除外）
- ❌ **绝不**发给我（AI）
- ❌ **绝不**截图发到社交媒体
- 丢失私钥 = 丢失钱包里所有资金

---

## 📋 平台 1：MetaMask 钱包安装（10 分钟）

**用途**：连接 Mirror.xyz、接收打赏、签名交易
**前置**：已完成「获取钱包私钥」

### 步骤 1：安装 MetaMask 浏览器扩展
1. 打开 Chrome 或 Edge 浏览器
2. 访问官方网址：https://metamask.io/
3. 点击「Download」→「Install MetaMask for Chrome」
4. 在 Chrome Web Store 点击「添加至 Chrome」
5. 浏览器右上角会出现 MetaMask 狐狸图标

### 步骤 2：导入已有钱包（用我们的私钥）
1. 点击浏览器右上角的 MetaMask 狐狸图标
2. 点击「Get Started」
3. 选择「Import wallet」（导入钱包）**不要选 Create Wallet**
4. 勾选「I agree」
5. 在「Enter your Secret Recovery Phrase」框中粘贴你的私钥
   - ⚠️ 粘贴 64 位十六进制私钥（不含 0x 前缀）
   - 如果提示格式不对，试试加 `0x` 前缀
6. 设置一个新密码（8 位以上，含数字+字母）
7. 点击「All Done」

### 步骤 3：验证钱包已导入
1. MetaMask 主界面顶部应显示地址：`${ETH_PREFIX}789C...86942`
2. 余额应显示 0 ETH
3. 网络默认是「Ethereum Mainnet」（以太坊主网）

### 步骤 4：添加 BSC 网络（可选，用于 Binance 提现）
1. 点击 MetaMask 顶部的网络选择器「Ethereum Mainnet」
2. 点击「Add Network」
3. 手动填写：
   - 网络名称：BSC
   - RPC URL：https://bsc-dataseed.binance.org
   - 链 ID：56
   - 货币符号：BNB
   - 区块浏览器：https://bscscan.com
4. 保存

✅ **完成标志**：MetaMask 显示地址 `${ETH_PREFIX}789C...86942`

---

## 📋 平台 2：BitDegree Learn & Earn（30 分钟，立即可赚）

**用途**：做任务赚 Bits → 换 token
**预期收益**：$5-15（首日）
**网址**：https://www.bitdegree.org/missions

### 步骤 1：注册账号
1. 访问 https://www.bitdegree.org/missions
2. 点击右上角「Sign Up」
3. 用邮箱注册（Gmail 推荐）
4. 验证邮箱（查收邮件，点击验证链接）

### 步骤 2：完成首批 Mission（赚 1500 Bits）
1. 登录后进入「Missions」页面
2. 找到标记「Free」的 Mission（不需要付费的）
3. 推荐先做这 3 个：
   - **Binance Mission**：学习 Binance 知识 + quiz，约 500 Bits
   - **Ledger Mission**：硬件钱包知识，约 500 Bits
   - **Kraken Mission**：交易所知识，约 500 Bits
4. 每个 Mission 包含：
   - 看一段视频或阅读材料（5-10 分钟）
   - 回答 5-10 道 quiz 题
   - 全部答对获得 Bits

### 步骤 3：兑换 Bits 为 token
1. 累积到 1000+ Bits 后
2. 进入「Rewards」页面
3. 选择 USDT 或 USDC（稳定币，1 token = $1）
4. 点击「Claim」
5. 系统会要求你提供 ETH 钱包地址
6. 粘贴：`${ETH_TIPPING_ADDRESS}`
7. 确认收款地址

### 步骤 4：邀请朋友（每邀请 1 人 +500 Bits）
1. 进入「Refer Friends」页面
2. 复制你的专属邀请链接
3. 分享到朋友圈/推特/Telegram

✅ **完成标志**：账号已注册，至少完成 1 个 Mission，Bits 余额 > 500

---

## 📋 平台 3：Publish0x 内容创作（15 分钟设置 + 持续发布）

**用途**：发布文章赚打赏（平台补贴，读者免费打赏）
**预期收益**：$2-10/月（10 篇文章）
**网址**：https://www.publish0x.com

### 步骤 1：注册账号
1. 访问 https://www.publish0x.com
2. 点击右上角「Sign Up」
3. 用邮箱注册
4. 验证邮箱

### 步骤 2：设置提现地址
1. 登录后点击右上角头像 →「Settings」
2. 找到「Tip Wallet Address」或「Withdrawal Address」
3. 粘贴 ETH 钱包地址：`${ETH_TIPPING_ADDRESS}`
4. 保存

### 步骤 3：发布第 1 篇文章（我已准备好内容）
1. 进入文章目录：`d:\autoCompany\company\projects\seo-content-generator\articles\`
2. 用记事本打开 `01-airdrop-guide.md`
3. 复制全部内容
4. 回到 Publish0x，点击「New Story」
5. 粘贴内容到编辑器
6. 设置标题：「The Ultimate Guide to Airdrop Crypto in 2026」
7. 添加标签：crypto, airdrop, blockchain, tutorial
8. 添加封面图（可选，从 Unsplash 找一张 crypto 主题图）
9. 点击「Publish」
10. 等待审核（通常 24 小时内）

### 步骤 4：批量发布剩余 9 篇
- 每天发 1-2 篇（避免被判定为 spam）
- 发布顺序见文件：`publish0x-upload-list.md`

✅ **完成标志**：账号已注册，至少 1 篇文章已提交发布

---

## 📋 平台 4：Mirror.xyz 内容创作（20 分钟设置，高收益）

**用途**：发布文章赚 ETH 打赏
**预期收益**：$10-200/月（优质文章）
**网址**：https://mirror.xyz
**前置**：已完成「MetaMask 钱包安装」

### 步骤 1：用钱包登录
1. 访问 https://mirror.xyz
2. 点击右上角「Connect Wallet」
3. 浏览器弹出 MetaMask，点击「Connect」
4. 签名验证（MetaMask 弹出签名请求，点击「Sign」）
5. 登录成功

### 步骤 2：创建作者主页
1. 点击「Create Entry」或「New Entry」
2. 设置用户名（建议：AutoCorp Insights）
3. 设置头像（可选）
4. 设置简介：「AI-generated crypto insights & tutorials」

### 步骤 3：发布第 1 篇文章
1. 进入文章目录：`d:\autoCompany\company\projects\seo-content-generator\articles\`
2. 打开 `04-ethereum-wallet-guide.md`，复制全部内容
3. 回到 Mirror，点击「New Entry」
4. 粘贴内容（Mirror 支持 Markdown）
5. 设置标题：「The Ultimate Guide to Ethereum Wallet in 2026」
6. 在文章末尾添加打赏说明：
   ```
   ---
   If you found this guide helpful, consider tipping the author at:
   ${ETH_TIPPING_ADDRESS}
   ```
7. 点击「Publish」
8. MetaMask 弹出签名请求，点击「Sign」（发布需要签名，**不需要 gas 费**，因为是写入 Arweave）

### 步骤 4：设置收款地址
1. 进入「Settings」
2. 找到「Earnings Address」或「Payout Address」
3. 确认地址为：`${ETH_TIPPING_ADDRESS}`
4. 保存

✅ **完成标志**：钱包已连接，至少 1 篇文章已发布

---

## 📋 平台 5：Binance Learn & Earn（30 分钟，需 KYC）

**用途**：看视频 + 答 quiz → 获得 token
**预期收益**：$2-20/次
**网址**：https://www.binance.com

### 步骤 1：注册 Binance 账号
1. 访问 https://www.binance.com
2. 点击「Register」
3. 用邮箱注册 + 设置强密码
4. 输入邀请码（可选，跳过）
5. 完成邮箱验证

### 步骤 2：完成 KYC 实名认证（必须）
1. 登录后点击右上角头像 →「Identification」
2. 选择「Personal Verification」
3. 选择国家：China（或你所在国家）
4. 上传身份证正反面照片
5. 进行人脸识别（用摄像头）
6. 等待审核（通常 1-24 小时）

### 步骤 3：进入 Learn & Earn
1. KYC 通过后，访问：https://www.binance.com/zh-CN/activity/marketing/learn-and-earn
2. 查看当前可用的 Learn & Earn 活动
3. 每个活动包含：
   - 1-3 个教学视频（每个 3-10 分钟）
   - 一组 quiz 题（5-10 道选择题）

### 步骤 4：答题技巧
- 看视频时做笔记（答案都在视频里）
- quiz 可以重做（答错不扣分）
- 我已准备答案参考文档：`binance-quiz-answers.md`
- 每个活动奖励 $2-20 不等

### 步骤 5：提现到钱包
1. 获得的 token 进入 Binance 现货账户
2. 点击「Withdraw」→「Withdraw Crypto」
3. 选择要提现的币种（如 USDT）
4. 网络：选择「ERC20」（以太坊主网）
5. 收款地址：`${ETH_TIPPING_ADDRESS}`
6. ⚠️ **注意**：提现需要 gas 费（ERC20 约 $5-15）
   - 建议：攒到 $50+ 再提现，分摊手续费
   - 或者：选择 BSC 网络提现（gas 费 $0.1）

✅ **完成标志**：账号已注册 + KYC 已通过 + 至少完成 1 个活动

---

## 📋 平台 6：CoinMarketCap Learn & Earn（10 分钟）

**用途**：看视频 + 答 quiz → 获得 token
**预期收益**：$2-15/次
**网址**：https://coinmarketcap.com
**前置**：已有 Binance 账号（CMC 奖励发到 Binance）

### 步骤 1：注册 CMC 账号
1. 访问 https://coinmarketcap.com
2. 点击右上角「Log In」→「Sign Up」
3. 用邮箱注册
4. 验证邮箱

### 步骤 2：关联 Binance 账号
1. 登录后点击头像 →「Settings」
2. 找到「Binance Account」或「Linked Accounts」
3. 点击「Connect Binance」
4. 跳转到 Binance 授权页面
5. 点击「Authorize」

### 步骤 3：进入 Earn 页面
1. 访问 https://coinmarketcap.com/earn/
2. 查看当前可用的活动
3. 完成视频 + quiz
4. 奖励自动发到关联的 Binance 账户

✅ **完成标志**：账号已注册 + Binance 已关联

---

## 📱 社交推广（关键！流量 = 收益）

### Twitter 推广（30 分钟设置）
1. 注册 Twitter 账号（建议新建专用账号）
2. 用户名建议：@AutoCorpInsights
3. 简介写：「AI-powered crypto insights & tutorials | Tipping: ${ETH_TIPPING_ADDRESS}」
4. 我已准备 10 条推广推文：见 `twitter-promotion.md`
5. 每发 1 篇文章，配套发 1 条推文

### Reddit 推广
1. 注册 Reddit 账号
2. 我已准备 2 篇推广文案：见 `reddit-promotion.md`
3. 发布到：
   - r/CryptoCurrency（1700 万订阅）
   - r/Ethereum
   - r/defi
4. ⚠️ **注意**：Reddit 反 spam 严格，建议先在社区互动 1 周再发链接

---

## 📊 执行优先级与时间表

### 今天（Day 1，预计 2 小时）

| 顺序 | 任务 | 时间 | 预期收益 |
|------|------|------|----------|
| 1 | 获取私钥 + 安装 MetaMask | 15 min | 前置 |
| 2 | 注册 BitDegree + 完成 3 个 Mission | 30 min | $5-15 |
| 3 | 注册 Publish0x + 发布第 1 篇 | 15 min | $1-3 |
| 4 | Mirror.xyz 连接钱包 + 发布第 1 篇 | 20 min | $0-20 |
| 5 | 注册 Binance + 开始 KYC | 10 min | 解锁后续 |
| 6 | 注册 CoinMarketCap + 关联 Binance | 5 min | 解锁后续 |

### 本周（Day 2-7）

| 任务 | 时间 | 预期收益 |
|------|------|----------|
| 每天发 1-2 篇 Publish0x 文章 | 30 min/天 | $5-20 |
| 每天发 1-2 篇 Mirror 文章 | 30 min/天 | $10-50 |
| Binance KYC 通过 + 完成 2 个活动 | 1 小时 | $4-40 |
| CMC 完成 2 个活动 | 1 小时 | $4-30 |
| Twitter 每天发 2 条推文 | 15 min/天 | 流量 |

### 下周（Day 8-14）

| 任务 | 预期收益 |
|------|----------|
| Reddit 发布推广文案 | 流量 |
| BitDegree 持续做任务 | $10-30 |
| 评估第一周收益 | — |

---

## ✅ 每完成一项，告诉我

完成每个平台后，告诉我：
- 「BitDegree 完成」→ 我记录到账本
- 「Publish0x 发布 3 篇」→ 我追踪曝光
- 「Mirror 发布 5 篇」→ 我追踪打赏
- 「Binance KYC 通过」→ 我准备 quiz 答案
- 「收到 0.001 ETH 打赏」→ 我记录到账本

我会：
1. 实时更新公司账本（标记 is_real=true）
2. 每日生成收益日报
3. 调整内容策略（哪类文章收益高就多写）
4. 监控钱包余额变化

---

## 🆘 遇到问题

### 常见问题

**Q：MetaMask 导入私钥失败**
A：尝试加 `0x` 前缀；或检查私钥长度（应该是 64 位）

**Q：Mirror 发布时提示签名失败**
A：检查 MetaMask 网络是否为 Ethereum Mainnet；刷新页面重试

**Q：Binance KYC 被拒**
A：检查身份证照片是否清晰；光线是否充足；尝试重新提交

**Q：Publish0x 文章审核不通过**
A：检查内容是否原创；是否包含推广链接；调整后再发

**Q：BitDegree quiz 答错**
A：可以重做，不扣分；多看几遍视频

### 需要我协助
- 任何步骤卡住，告诉我具体哪一步
- 收到任何加密货币，告诉我金额 + 币种 + tx_hash
- 我会实时更新账本和日报

---

## 📁 我已准备好的文件

| 文件 | 用途 |
|------|------|
| `user-action-guide.md`（本文件） | 完整操作指引 |
| `publish0x-upload-list.md` | Publish0x 发布清单 + 文章标题 |
| `mirror-upload-list.md` | Mirror 发布清单 + 文章标题 |
| `twitter-promotion.md` | 10 条 Twitter 推广推文 |
| `reddit-promotion.md` | Reddit 推广文案 |
| `binance-quiz-answers.md` | Binance quiz 答案参考 |

所有文件位于：`d:\autoCompany\company\knowledge\marketing\`

---

开始执行吧！按上面 Day 1 的顺序来，每完成一项告诉我。
