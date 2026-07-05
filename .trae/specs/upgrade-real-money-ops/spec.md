# AutoCorp 真实变现运营升级（Real-Money Ops）规格说明

## Why（为什么做）

当前 AutoCorp 已具备「模拟一日闭环」能力，但账本仍是虚拟数字、LLM 调用仍需用户提供 API_KEY、变现路径停留在市场分析阶段。用户希望让这家 AI 公司真正自治运转并挣到实际的钱：由 TRAE 内置大模型驱动运营、对接 PayPal 收款、季度战略同步方向、不限定场景（含加密货币机会分析）、并在合法合规与隐私安全前提下自主执行。本升级将 AutoCorp 从「演示原型」推进为「真实运营的 AI 公司」。

## What Changes（变更内容）

- **MODIFIED** LLM 客户端：默认使用 TRAE 内置模型端点，无需用户提供 API_KEY 即可运营公司
- **ADDED** Secrets 安全管理器：支付 key、私钥、API 凭证等敏感数据隔离存储，绝不进入代码/Prompt/日志
- **ADDED** PayPal 收款对接：支持创建收款订单、查询支付状态、Webhook 入账
- **ADDED** 季度战略会：CEO 每季度初同步方向、机会、重大事项公告
- **ADDED** 加密货币机会分析模块：市场分析 + 钱包注册 + 接收存款（出币需人工确认）
- **ADDED** 外付款安全审批闸门：任何往外付款必须经过风险评估 + 人工确认
- **ADDED** 人工协助请求机制：需要域名/服务器/人工操作时通过 AskUserQuestion 询问用户
- **MODIFIED** Orchestrator：在 run-day 中接入真实收入入账（PayPal/加密货币），区分虚拟收入与真实收入
- **ADDED** 合规与安全红线：明确禁止事项（欺诈、市场操纵、洗钱、自主转出大额资金）

## Impact（影响范围）

- **影响已有 spec**：build-ai-virtual-company（LLM 客户端、账本、编排器、角色职责）
- **修改代码**：
  - `engine/llm_client.py`（默认走 TRAE 端点）
  - `engine/ledger.py`（区分 virtual/real 收入）
  - `engine/orchestrator.py`（接入真实收入）
  - `main.py`（新增子命令）
- **新增代码**：
  - `engine/secrets.py`（密钥管理）
  - `engine/payments/paypal.py`（PayPal 对接）
  - `engine/agents/strategy_ceo.py` 或扩展 CEO（季度战略）
  - `engine/crypto/market_analyzer.py`、`engine/crypto/wallet.py`
  - `engine/safety/payment_gate.py`（外付款审批闸门）
  - `engine/human_loop.py`（人工协助请求）
- **新增配置**：
  - `company/config/secrets.yaml`（仅存密钥引用，不存明文）
  - `company/config/business.yaml`（业务配置：收款渠道、白名单等）
  - `company/strategy/`（季度战略文档目录）

---

## ADDED Requirements（新增需求）

### Requirement: TRAE 内置模型默认接入

系统 SHALL 默认使用 TRAE 内置大模型端点驱动所有虚拟员工，使用户无需自备 API_KEY 即可启动公司运营。

#### Scenario: 无 API_KEY 启动
- **GIVEN** 用户未配置 OPENAI_API_KEY
- **WHEN** 执行 `python main.py run-day`
- **THEN** 系统自动回退到 TRAE 内置模型端点
- **AND** 在日志中记录「使用 TRAE 内置模型」
- **AND** 不因缺少 API_KEY 而中断运营

#### Scenario: 显式指定模型
- **WHEN** 用户在 .env 中设置 `LLM_BACKEND=trae|openai|custom`
- **THEN** 系统按指定后端调用 LLM

### Requirement: Secrets 安全管理器

系统 SHALL 提供独立的 Secrets 管理器，所有敏感凭证（PayPal key、加密货币私钥、第三方 API key）必须经此管理，且满足：

1. 明文密钥仅存于 `.secrets/` 目录（gitignore，权限 600）
2. `company/config/secrets.yaml` 仅存「引用名」，不存明文
3. 任何 LLM Prompt、日志、日报、会议纪要中**严禁出现**明文密钥
4. 智能体访问密钥时通过 `secrets.get("paypal_client_secret")` 间接获取，返回值不进入 Prompt

#### Scenario: 密钥存储隔离
- **GIVEN** 首次初始化或用户执行 `python main.py secrets set paypal_client_secret xxx`
- **WHEN** 密钥写入
- **THEN** 明文存于 `.secrets/paypal.env`（或 .secrets/secrets.json）
- **AND** `company/config/secrets.yaml` 仅记录 `paypal_client_secret: ref://.secrets/paypal.env#PAYPAL_CLIENT_SECRET`
- **AND** `.gitignore` 包含 `.secrets/`

#### Scenario: Prompt 脱敏
- **WHEN** 任何智能体构造 LLM Prompt
- **THEN** Prompt 文本中不含任何 `sk-`、`paypal:`、私钥助记词等敏感模式
- **AND** 若误传入密钥，secrets 管理器在 `get()` 时返回 `[REDACTED:paypal_client_secret]` 占位符供日志使用，真实值仅传给支付 SDK

### Requirement: PayPal 收款对接

系统 SHALL 通过 PayPal REST API 实现收款能力，支持创建订单、查询状态、Webhook 自动入账。

#### Scenario: 创建收款订单
- **GIVEN** 产品定价 $19/月，用户购买
- **WHEN** 调用 `paypal.create_order(amount=19.00, currency="USD", description="Pro plan")`
- **THEN** 返回 PayPal approve URL 与 order_id
- **AND** 订单写入 `company/orders/pending/`

#### Scenario: 确认支付并入账
- **GIVEN** PayPal Webhook 回调支付成功（或手动 `python main.py payment check <order_id>`）
- **WHEN** 系统验证支付状态为 COMPLETED
- **THEN** 调用 `ledger.income_real(amount, source="paypal", tx_ref=order_id)` 入真实收入
- **AND** 订单移至 `company/orders/paid/`
- **AND** 日报中「真实收入」字段更新

### Requirement: 季度战略会

CEO SHALL 每季度初（1/4/7/10 月 1 日 09:00）召开战略会，输出方向、机会、重大事项公告。

#### Scenario: 季度战略会触发
- **WHEN** 到达季度初触发时间
- **THEN** CEO 基于上季度经营数据 + 市场情报 + 用户反馈，输出：
  - 下季度战略方向（3-5 条）
  - 重点机会清单（含预期 ROI）
  - 重大事项公告（组织调整、新业务、风险提示）
- **AND** 战略文档写入 `company/strategy/YYYY-Qn.md`
- **AND** 全员智能体可读取该文档作为本季度决策上下文

#### Scenario: 手动触发战略会
- **WHEN** 用户执行 `python main.py strategy --now`
- **THEN** 立即召开一次战略会

### Requirement: 加密货币机会分析

系统 SHALL 提供加密货币市场分析能力，作为可选的变现赛道探索方向。

#### Scenario: 市场分析
- **WHEN** CEO/PM 决策探索加密货币赛道
- **THEN** 系统调用市场数据 API（如 CoinGecko 公开接口）获取行情
- **AND** 输出分析报告：机会（套利/链上数据/空投/稳定币理财）、风险、合规边界
- **AND** 报告写入 `company/knowledge/market-research/crypto-YYYY-MM-DD.md`

#### Scenario: 钱包注册与接收存款
- **GIVEN** 分析结论可行且 CEO 批准
- **WHEN** 执行 `python main.py crypto register-wallet --chain <chain>`
- **THEN** 系统生成新钱包地址（公钥存于 `company/config/wallets.yaml`，私钥/助记词存于 `.secrets/`）
- **AND** 公钥地址可对外公布用于接收存款
- **AND** 入账时调用 `ledger.income_real(amount, source="crypto_<chain>", tx_ref=tx_hash)`

### Requirement: 加密货币出币安全红线

系统 SHALL 禁止 AI 自主转出加密货币资产，任何出币操作必须经人工确认。

#### Scenario: 出币需人工确认
- **GIVEN** AI 评估某机会需转出加密货币（如参与流动性挖矿）
- **WHEN** 触发出币流程
- **THEN** 系统暂停并调用 `human_loop.request_approval()` 询问用户
- **AND** 用户明确确认后才执行
- **AND** 私钥签名操作必须在用户监督下完成，AI 不持有签名权限

### Requirement: 外付款安全审批闸门

系统 SHALL 在所有往外付款操作前执行安全审批闸门，防止被其他 AI 或钓鱼攻击骗走资金。

#### Scenario: 外付款风险评估
- **GIVEN** 某任务需要往外付款（如购买 API 额度、广告投放、外包服务）
- **WHEN** 触发付款
- **THEN** 系统执行 `payment_gate.assess(payment_request)`，评估：
  - 收款方是否在白名单
  - 金额是否超出该类别预算
  - 是否符合季度战略方向
  - 是否有可疑模式（紧急催促、变更收款地址等）
- **AND** 评估结果为 `high_risk` 时必须人工确认
- **AND** 评估结果为 `block` 时拒绝付款并记录告警

#### Scenario: 白名单管理
- **WHEN** 用户执行 `python main.py payee whitelist add <address> <category>`
- **THEN** 收款方加入白名单，后续付款可走快速通道

### Requirement: 人工协助请求机制

系统在执行过程中遇到需要用户协助的场景时，SHALL 通过 AskUserQuestion 机制主动询问用户，而非静默失败。

#### Scenario: 需要资源协助
- **GIVEN** COO 评估某产品需独立域名和服务器才能上线
- **WHEN** 系统检测到部署需求
- **THEN** 调用 `human_loop.request_assistance("需要域名和服务器部署产品 X")`
- **AND** 通过 AskUserQuestion 向用户提问，选项包括「已提供」「跳过」「稍后」
- **AND** 用户响应写入 `company/human-requests/` 跟踪

#### Scenario: 需要决策协助
- **GIVEN** CEO 面临高风险高回报决策（如大额投资）
- **WHEN** 风险评估为 high_risk
- **THEN** 暂停决策，通过 AskUserQuestion 请求用户拍板

### Requirement: 真实收入与虚拟收入分离

账本 SHALL 区分「真实收入」（PayPal/加密货币实际到账）与「虚拟收入」（模拟/估算），报表分别展示。

#### Scenario: 真实收入入账
- **WHEN** PayPal 或加密货币实际到账
- **THEN** 调用 `ledger.income_real()`，交易记录标记 `is_real: true`
- **AND** 日报中「真实收入」与「虚拟收入」分列展示

#### Scenario: 真实支出入账
- **WHEN** 真实付款发生（如 PayPal 手续费、服务器费用）
- **THEN** 调用 `ledger.expense_real()`，交易记录标记 `is_real: true`

### Requirement: 合规与安全红线

系统 SHALL 内置合规红线，任何智能体决策不得突破：

1. **禁止欺诈**：不做虚假宣传、刷单、评论操纵
2. **禁止市场操纵**：不参与加密货币拉盘/砸盘、wash trading
3. **禁止洗钱**：不对来路不明资金提供转移通道
4. **禁止自主转出大额资金**：单笔超 $100 的出款必须人工确认
5. **禁止泄露隐私**：支付 key、私钥、用户数据不得进入 Prompt/日志/外部 API
6. **禁止违法内容**：不生成违法内容产品

#### Scenario: 红线校验
- **WHEN** 任何智能体产出决策/内容
- **THEN** 通过 `safety.check_compliance(action)` 校验
- **AND** 命中红线时拒绝执行并记录告警
- **AND** 告警写入 `company/safety/incidents.md`

---

## MODIFIED Requirements（修改需求）

### Requirement: LLM 客户端（原 build-ai-virtual-company）

[原内容：封装 OpenAI 兼容接口，从 .env 读取 API_KEY/BASE_URL/MODEL]

**修改为**：
- 默认后端切换为 TRAE 内置模型（无需用户提供 API_KEY）
- 支持 `LLM_BACKEND=trae|openai|custom` 切换
- TRAE 端点配置通过环境变量或自动探测
- 保留 OpenAI 兼容接口作为 fallback

### Requirement: 虚拟资产账本（原 build-ai-virtual-company）

[原内容：维护虚拟美元账本]

**修改为**：
- 新增 `income_real()` / `expense_real()` 方法，标记 `is_real: true`
- 原 `income()` / `expense()` 保留用于虚拟/估算交易
- `audit()` 返回结果区分 real/virtual 汇总
- 日报中真实收入与虚拟收入分别展示

### Requirement: 商业闭环编排器（原 build-ai-virtual-company）

[原内容：编排一日流程]

**修改为**：
- 收入结算阶段：优先检查真实收入（PayPal 订单、加密货币到账），无真实收入时才用虚拟模拟
- 新增「季度战略会」作为顶层周期任务
- 各阶段接入安全闸门校验

---

## REMOVED Requirements（移除需求）

无。本升级为增量，不移除已有能力。

---

## 设计约束

1. **安全优先**：任何涉及资金/密钥/出款的功能，安全审批闸门优先于便利性
2. **人工在环**：高风险决策、大额出款、私钥操作必须人工确认
3. **隐私隔离**：敏感数据物理隔离于 `.secrets/`，永不进入 LLM 上下文
4. **渐进式落地**：先实现 TRAE 模型接入 + Secrets 管理 + PayPal 收款，再加季度战略与加密货币
5. **合规底线**：内置红线检查，违法场景一律拒绝
6. **可观测**：所有真实资金流动、人工确认、安全事件均留痕可审计
