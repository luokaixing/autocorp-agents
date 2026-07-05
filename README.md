# AutoCorp - AI 虚拟自治公司操作系统

AutoCorp 是一个在本地电脑上自治运转的 AI 虚拟公司操作系统。由 7 个虚拟员工智能体（CEO / CTO / COO / 架构师 / 程序员 / 测试 / 产品）分工协作，每日定时开会、研发、测试、推广，产出可商业化的产品，服务美国市场赚取美元，并通过虚拟账户资产管理实现自我迭代。

## 核心特性

- **7 个虚拟员工角色自治协作**：CEO、CTO、COO、架构师、程序员、测试、产品经理，各司其职
- **每日 8:00 产研同步会**：定时触发晨会，同步进展、拆解任务、做出决策
- **完整商业闭环**：调研 → 决策 → 研发 → 测试 → 推广 → 回款 → 再投资
- **虚拟美元账本与资产管理**：内置 ledger 跟踪余额、收入、支出与历史交易
- **文件即数据库**：所有数据（账本、决策、知识、会议纪要、日报）均以文件持久化，无需额外依赖

## 快速开始

```bash
# 安装依赖
pip install -r requirements.txt

# 配置 LLM
cp .env.example .env
# 编辑 .env 填入 OPENAI_API_KEY

# 初始化公司
python main.py init

# 召开首次晨会
python main.py meeting --now

# 执行一个完整工作日
python main.py run-day

# 查看公司状态
python main.py status

# 启动每日定时调度（每天 08:00 自动开会）
python main.py schedule --start
```

## 命令说明

| 命令 | 用途 |
|------|------|
| `python main.py init` | 初始化公司工作区（首次使用必执行） |
| `python main.py meeting --now` | 立即触发一次产研同步会（调试用） |
| `python main.py meeting` | 启动会议调度器 |
| `python main.py run-day` | 执行一个完整工作日（晨会→编码→测试→推广→结算→日报） |
| `python main.py status` | 查看公司当前状态 |
| `python main.py schedule --start` | 启动后台定时调度（每日 08:00 Asia/Shanghai 触发会议） |

## 架构说明

```
autoCompany/
├── main.py                      # CLI 入口（基于 click）
├── requirements.txt             # Python 依赖
├── .env.example                 # 环境变量模板
├── engine/                      # 编排引擎
│   ├── __init__.py
│   ├── workspace.py             # 工作区初始化与目录管理
│   ├── llm_client.py            # OpenAI 兼容 LLM 客户端封装
│   ├── ledger.py                # 虚拟美元账本（余额/交易记录）
│   ├── meeting.py               # 产研同步会编排
│   ├── scheduler.py             # 定时调度器（基于 schedule 库）
│   ├── orchestrator.py          # 工作日编排器（串联完整闭环）
│   ├── reporter.py              # 日报与公司状态报告
│   └── agents/                  # 7 个角色智能体
│       ├── __init__.py
│       ├── base.py              # BaseAgent 基类（加载配置/构造 prompt）
│       ├── ceo.py
│       ├── cto.py
│       ├── coo.py
│       ├── architect.py
│       ├── programmer.py
│       ├── tester.py
│       └── product_manager.py
├── company/                     # 公司工作区（数据持久化）
│   ├── config/                  # 配置
│   │   ├── employees.yaml       # 角色定义
│   │   ├── ledger.yaml          # 账本初始状态
│   │   └── meeting.yaml         # 会议调度配置
│   ├── knowledge/               # 公司知识库
│   │   ├── market-research/     # 市场情报
│   │   ├── competitors/         # 竞品分析
│   │   ├── decisions/           # 决策日志
│   │   └── lessons-learned/     # 经验沉淀
│   ├── meetings/                # 会议纪要（按日期归档）
│   └── reports/                 # 日报与调度日志
└── tests/                       # 单元测试
```

### 模块说明

- **engine/**：编排引擎核心，负责工作区管理、LLM 调用、账本维护、会议编排、定时调度、工作日串联与状态报告
- **engine/agents/**：7 个角色智能体，均继承自 `BaseAgent`，通过 `load_config()` 读取 `employees.yaml` 并构造系统提示词
- **company/**：公司工作区，所有数据以文件持久化（配置、知识、会议、报告）
- **main.py**：CLI 入口，基于 `click` 提供 init / meeting / run-day / status / schedule 命令

## 虚拟员工角色

| 角色 | 代号 | 职责 |
|------|------|------|
| 首席执行官 | `ceo` | 成本分析、市场判断、立项决策、终止决策、预算审批、战略方向、资源分配 |
| 首席技术官 | `cto` | 技术选型、架构方向、技术评审、风险把控、技术规范 |
| 首席运营官 | `coo` | 推广运营、渠道策略、定价、用户跟踪、收入回款、增长 |
| 架构师 | `architect` | 架构设计、模块拆分、接口定义、技术规范、代码评审、质量把控 |
| 程序员 | `programmer` | 模块开发、编码实现、代码交付、bug 修复、子模块 |
| 测试员 | `tester` | 测试、验证、缺陷报告、回归测试、质量把关 |
| 产品经理 | `product_manager` | 市场调研、需求搜集、PRD、用户痛点、竞品分析、变现路径、PMF |

每个角色的 `persona`、`responsibilities`、`tools`、`system_prompt` 均在 `company/config/employees.yaml` 中定义，由 `BaseAgent.load_config()` 加载。

## 工作流程

一个完整工作日（`run-day`）的流程如下：

```
晨会
 ├── 产品经理：汇报市场调研与需求
 ├── CTO：同步技术方向与风险
 ├── 架构师：拆解任务与模块
 └── CEO：基于账本/情报做出决策
        │
        ▼
任务分发（按角色与模块拆分）
        │
        ▼
程序员编码实现
        │
        ▼
测试员验证（含正常/边界/异常用例）
        │
        ▼
COO 推广（渠道、定价、追踪指标）
        │
        ▼
收入结算（回款写入账本）
        │
        ▼
日报生成（reports/ 下按日期归档）
        │
        ▼
账本更新（ledger.yaml 余额与交易）
```

## 配置说明

### .env 配置项

| 变量 | 说明 | 示例 |
|------|------|------|
| `OPENAI_API_KEY` | LLM API 密钥（必填） | `sk-...` |
| `OPENAI_BASE_URL` | OpenAI 兼容接口地址 | `https://api.openai.com/v1` |
| `MODEL_NAME` | 使用的模型名 | `gpt-4o-mini` |

> 也可使用 TRAE 内置模型端点：`OPENAI_BASE_URL=https://api.trae.cn/v1`

### employees.yaml 角色配置

每个角色包含以下字段：

- `name`：角色显示名（如「首席执行官」）
- `role`：代号（如 `ceo`，用于代码层匹配）
- `persona`：人格设定
- `responsibilities`：职责清单
- `tools`：可访问的工具集（如 `ledger` / `market_research` / `projects`）
- `system_prompt`：系统提示词，约束输出格式与决策规则

### ledger.yaml 账本说明

```yaml
balance: 10000.0            # 当前余额（USD）
currency: USD               # 结算货币
initial_capital: 10000.0    # 初始资本
transactions: []            # 历史交易记录
```

所有收入回款与支出均通过 `engine/ledger.py` 写入 `transactions`，并实时更新 `balance`。CEO 决策时强制读取账本数据，单笔支出超余额 30% 需显式标注「需二次审批」。

### meeting.yaml 会议配置

```yaml
schedule: 0 8 * * *     # 每日 08:00 触发（cron 表达式）
timezone: Asia/Shanghai # 时区
participants: []        # 参与者列表（运行时填充）
```

## 扩展指南

### 添加新角色

1. **在 `company/config/employees.yaml` 添加角色配置**，包含 `name` / `role` / `persona` / `responsibilities` / `tools` / `system_prompt` 字段
2. **在 `engine/agents/` 创建新类**，继承 `BaseAgent`：

   ```python
   from engine.agents.base import BaseAgent

   class NewRoleAgent(BaseAgent):
       def __init__(self):
           super().__init__(role="new_role")
   ```
3. **在 `engine/agents/__init__.py` 导出**，以便编排引擎统一引用

## 市场情报

`company/knowledge/market-research/seed-2026.md` 是公司决策的种子情报库，覆盖 6 个面向美国市场、以美元结算的高变现赛道：

| 排名 | 赛道 | 预期 MRR 区间 | 推荐指数 |
|------|------|--------------|----------|
| 1 | 垂直行业 AI Agent | $10,000-30,000 | ★★★★★ |
| 2 | SEO 内容自动化生成 | $8,000-20,000 | ★★★★★ |
| 3 | AI 内容再利用工具 | $5,000-15,000 | ★★★★☆ |
| 4 | Landing Page 生成器 | $5,000-12,000 | ★★★★☆ |
| 5 | AI 简历/求职工具 | $4,000-10,000 | ★★★★☆ |
| 6 | AI Chrome 扩展（生产力） | $3,000-10,000 | ★★★☆☆ |

每个赛道从「痛点 → 用户 → 竞品 → 变现 → MRR → 技术可行性 → 推荐指数」七个维度评估。CEO 与产品经理基于此情报做出立项决策：

- **第一阶段（0-3 个月）**：以「SEO 内容自动化」+「AI 内容再利用」双赛道启动，现金流快、技术栈复用度高
- **第二阶段（3-6 个月）**：切入「垂直行业 AI Agent（电商客服方向）」拉高客单价与护城河
- **第三阶段（6-12 个月）**：按需扩展 Landing Page 或求职工具作为流量入口或季节性现金流补充

后续市场情报会由市场情报 Agent 持续更新并沉淀到 `company/knowledge/` 下对应目录。

## Real-Money Ops（真实变现运营）

AutoCorp 已从「虚拟公司」升级为「真实变现运营」阶段：在保留虚拟账本与角色协作的基础上，新增真实收款（PayPal / 加密货币）、真实支出安全闸门、密钥物理隔离、合规红线、人工在环与季度战略会等能力，形成可对外提供真实商品与服务、回收真实美元的闭环。本章节描述真实变现相关模块的设计原则、架构、配置与 CLI 使用方式。

### 设计原则

| 原则 | 含义 |
|------|------|
| 安全优先 | 真实出款前置闸门（PaymentGate）+ 合规红线（Compliance），任何高风险动作默认拒绝而非默认放行 |
| 人工在环 | 出币、大额出款、敏感操作强制人工确认；AI 不持有签名权限与最终放款权 |
| 隐私隔离 | 明文密钥物理隔离于 `.secrets/`（gitignored + 文件权限 600），仓库内仅存 `ref://` 引用，prompt 自动脱敏 |
| 渐进式落地 | 虚拟账本与真实账本共存，老交易兼容默认 `is_real=false`，新真实交易显式标记 `is_real=true` |
| 合规底线 | 6 条红线（欺诈/操纵/洗钱/大额出款/隐私泄露/违法内容）任何命中即拒绝并写 `incidents.md` |
| 可观测性 | 日报新增真实收支与安全事件字段；订单流转 `pending/` → `paid/`；战略与市场报告文件化归档 |

### 架构图

```
┌─────────────────────────────────────────────────────────────────────┐
│                        Secrets 物理隔离层                            │
│   .secrets/secrets.json (明文, 600, gitignored)                      │
│   company/config/secrets.yaml (仅 ref:// 引用)                       │
│   prompt 注入前自动脱敏 → 任何 LLM 调用均不接触明文密钥              │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                       真实收入闭环（入账方向）                       │
│                                                                      │
│   PayPal Client (sandbox 默认)        Crypto Wallet (只读地址)       │
│        │                                    │                        │
│        ▼                                    ▼                        │
│   创建订单 → 用户支付 → capture        外部转账 → 链上到账           │
│        │                                    │                        │
│        └──────────────┬─────────────────────┘                        │
│                       ▼                                              │
│           ledger.income_real(is_real=true)                           │
│           订单流转: orders/pending/ → orders/paid/                   │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                    真实支出安全闸门（出账方向）                      │
│                                                                      │
│   发起付款请求                                                        │
│        │                                                             │
│        ▼                                                             │
│   PaymentGate 评估:                                                  │
│     1) 白名单匹配   2) 预算余量   3) 战略对齐   4) 可疑模式           │
│        │                                                             │
│        ├── allow      → 正常放行                                     │
│        ├── high_risk  → 强制人工确认 (human_loop)                    │
│        └── block      → 直接拒绝 (>$500 非白名单自动 block)          │
│        │                                                             │
│        ▼                                                             │
│   Compliance 红线检查 (6 条)                                         │
│     命中 → 拒绝 + 写 company/incidents.md                            │
│     未命中 → ledger.expense_real(is_real=true)                       │
└─────────────────────────────────────────────────────────────────────┘
                                  │
                                  ▼
┌─────────────────────────────────────────────────────────────────────┐
│                      季度战略 + 知识沉淀                              │
│   CEO.quarterly_strategy()  每季度 1/4/7/10 月 1 日 09:00            │
│     → company/strategy/YYYY-Qn.md                                    │
│   CryptoMarketAnalyzer (CoinGecko 公开 API)                          │
│     → company/knowledge/market-research/crypto-YYYY-MM-DD.md         │
│   全员 prompt 自动注入最新战略与市场情报                             │
└─────────────────────────────────────────────────────────────────────┘
```

### 配置说明

#### .env 关键变量

| 变量 | 说明 | 默认值 |
|------|------|--------|
| `LLM_BACKEND` | LLM 后端选择：`trae` / `openai` / `custom` | `trae` |
| `TRAE_BASE_URL` | TRAE 内置模型端点 | `https://api.trae.cn/v1` |
| `TRAE_MODEL` | TRAE 模型名 | `trae-model` |
| `TRAE_API_KEY` | TRAE API Key（内置后端通常留空即可） | 空 |

> 默认 `LLM_BACKEND=trae` 时无需自备 API_KEY 即可运行；切换到 `openai` 或 `custom` 需补充对应密钥。

#### PayPal 与加密货币密钥（通过 secrets CLI 写入）

| Key | 用途 |
|-----|------|
| `paypal_client_id` | PayPal 客户端 ID |
| `paypal_client_secret` | PayPal 客户端密钥 |
| `paypal_webhook_id` | PayPal Webhook ID（可选） |
| `coingecko_api_key` | CoinGecko API Key（可选，公开 API 也可用） |

### CLI 命令清单

#### Secrets 管理

| 命令 | 用途 |
|------|------|
| `python main.py secrets set <key> <value>` | 写入密钥（明文存于 `.secrets/`） |
| `python main.py secrets get <key>` | 读取密钥明文（谨慎使用，会输出到终端） |
| `python main.py secrets list` | 列出所有密钥名（不显示值） |

#### PayPal 收款

| 命令 | 用途 |
|------|------|
| `python main.py payment create --amount 19.99 --currency USD --description "..."` | 创建收款订单（默认沙箱，`--live` 切正式环境） |
| `python main.py payment check <order_id>` | 检查订单状态并 capture 入账（默认沙箱，`--live` 切正式环境） |

订单流转路径：`orders/pending/<order_id>.json` → `orders/paid/<order_id>.json`，capture 成功后自动调用 `ledger.income_real()`。

#### 安全闸门（收款方白名单）

| 命令 | 用途 |
|------|------|
| `python main.py payee add <payee_address> <category>` | 添加白名单（category 如 `infra` / `marketing` / `salary`） |
| `python main.py payee list` | 列出当前白名单 |

非白名单收款方单笔 >$500 自动 block；白名单内仍需通过预算与战略对齐校验。

#### 加密货币

| 命令 | 用途 |
|------|------|
| `python main.py crypto analyze [-f arbitrage/airdrop/staking/onchain_data/stablecoin_yield]` | 市场分析，输出报告到 `company/knowledge/market-research/crypto-YYYY-MM-DD.md` |
| `python main.py crypto register-wallet --chain <bitcoin/ethereum/tron/solana>` | 注册新钱包（公钥存 `wallets.yaml`，私钥存 `.secrets/`） |
| `python main.py crypto list-wallets` | 列出所有钱包地址 |
| `python main.py crypto balance --address <addr> --chain <chain>` | 查询指定地址余额 |

> AI 不持有签名权限，出币操作由用户监督完成；`engine/crypto/outflow_gate.py` 强制人工确认。

#### 季度战略

| 命令 | 用途 |
|------|------|
| `python main.py strategy --now` | 立即触发季度战略会，输出 `company/strategy/YYYY-Qn.md` |
| `python main.py strategy` | 提示通过 `schedule --start` 启动调度器（季度初 1/4/7/10 月 1 日 09:00 自动触发） |

### 安全机制

#### 合规红线（6 条）

`engine/safety/compliance.py` 在每次真实出款前检查以下红线，命中即拒绝并写入 `company/incidents.md`：

1. **欺诈**：虚假交易、套现、伪造订单
2. **市场操纵**：刷量、虚假评论、价格操纵
3. **洗钱**：异常资金流转、结构化拆分、可疑地址
4. **大额出款**：单笔 > $100 需人工确认，>$500 非白名单直接 block
5. **隐私泄露**：向外传输用户隐私数据、明文存储敏感信息
6. **违法内容**：涉及违法、侵权、违规内容的服务或商品

#### 人工确认场景

`engine/human_loop.py` 通过 `AskUserQuestion` 询问用户，CLI 模式退化为终端输入，触发场景包括：

- 出币操作（强制确认，签名由用户监督完成）
- 单笔 > $100 的真实出款
- PaymentGate 评估为 `high_risk` 的付款请求
- 非白名单收款方首次交易
- 战略方向重大调整（季度战略会关键决策点）

### 使用流程示例

#### 1. 首次配置

```bash
# 安装依赖
pip install -r requirements.txt

# 复制环境变量模板（默认 trae 后端，无需 API_KEY）
cp .env.example .env

# 初始化公司工作区
python main.py init

# 写入 PayPal 凭据（明文隔离于 .secrets/，不进 git）
python main.py secrets set paypal_client_id YOUR_CLIENT_ID
python main.py secrets set paypal_client_secret YOUR_CLIENT_SECRET

# 验证密钥已隔离
python main.py secrets list
```

#### 2. 真实收入闭环（PayPal 沙箱）

```bash
# 创建收款订单（默认沙箱）
python main.py payment create --amount 19.99 --currency USD --description "Pro Plan Monthly"

# 输出支付链接发给客户，客户完成支付后
python main.py payment check <order_id>
# → capture 成功 → ledger.income_real() 入账 → 订单流转到 paid/
```

#### 3. 真实支出安全闸门

```bash
# 预先把常用收款方加入白名单
python main.py payee add vendor@example.com infra

# run-day 时 Orchestrator 会自动对真实支出走 PaymentGate + Compliance 前置校验
python main.py run-day
# 日报中包含真实收支与安全事件字段
```

#### 4. 季度战略会

```bash
# 立即生成本季度战略文档
python main.py strategy --now
# → company/strategy/2026-Q2.md

# 或启动调度器，季度初自动触发
python main.py schedule --start
```

#### 5. 加密货币市场分析与钱包

```bash
# 拉取 CoinGecko 公开数据生成市场分析报告
python main.py crypto analyze -f arbitrage -f staking
# → company/knowledge/market-research/crypto-2026-06-27.md

# 注册以太坊钱包（私钥自动存 .secrets/，AI 不持有签名权限）
python main.py crypto register-wallet --chain ethereum

# 查询余额
python main.py crypto balance --address 0x... --chain ethereum

# 出币操作：outflow_gate 强制人工确认，签名由用户监督完成
```

### 相关文件索引

| 路径 | 用途 |
|------|------|
| `engine/secrets.py` | SecretsManager：明文隔离 + ref:// 引用 + prompt 脱敏 |
| `engine/payments/paypal.py` | PayPalClient：sandbox/正式、create_order/capture_order |
| `engine/safety/payment_gate.py` | PaymentGate：白名单 + 预算 + 战略对齐 + 分级 allow/high_risk/block |
| `engine/safety/compliance.py` | Compliance：6 条红线检查 + incidents.md 写入 |
| `engine/human_loop.py` | HumanLoop：AskUserQuestion / CLI 退化输入 |
| `engine/crypto/market_analyzer.py` | CryptoMarketAnalyzer：CoinGecko 报告生成 |
| `engine/crypto/wallet.py` | WalletManager：钱包注册 / 余额查询 |
| `engine/crypto/outflow_gate.py` | 出币红线：强制人工确认 |
| `engine/agents/ceo.py` | `quarterly_strategy()` 季度战略文档生成 |
| `engine/orchestrator.py` | run-day：真实收入采集 + 支出闸门 + 日报安全字段 |
| `company/strategy/YYYY-Qn.md` | 季度战略文档（自动生成） |
| `company/incidents.md` | 安全事件记录（红线命中自动写入） |
| `.secrets/secrets.json` | 明文密钥存储（gitignored, 600） |
