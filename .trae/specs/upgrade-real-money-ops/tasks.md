# Tasks - AutoCorp 真实变现运营升级（Real-Money Ops）

> 原则：安全优先、人工在环、渐进式落地。先打通 TRAE 模型 + Secrets 管理 + PayPal 收款核心闭环，再扩展季度战略与加密货币。
> 依赖：基于已完成的 build-ai-virtual-company（7 角色 + 工作区 + 账本 + 编排器已就绪）。

## 阶段一：基础设施升级（TRAE 模型 + Secrets 管理）

- [x] Task 1: LLM 客户端升级为默认 TRAE 后端
  - [x] SubTask 1.1: 修改 `engine/llm_client.py`，新增 LLM_BACKEND 配置项（trae|openai|custom）
  - [x] SubTask 1.2: 实现 TRAE 内置模型端点自动探测（环境变量优先，否则默认端点）
  - [x] SubTask 1.3: 无 OPENAI_API_KEY 时自动回退到 TRAE 后端，不报错
  - [x] SubTask 1.4: 更新 `.env.example` 增加 LLM_BACKEND / TRAE_BASE_URL / TRAE_MODEL 说明
  - [x] SubTask 1.5: 编写测试验证后端切换逻辑

- [x] Task 2: Secrets 安全管理器
  - [x] SubTask 2.1: 实现 `engine/secrets.py`，提供 set/get/list/delete API
  - [x] SubTask 2.2: 明文存于 `.secrets/secrets.json`（权限 600），`company/config/secrets.yaml` 仅存引用 `ref://.secrets/secrets.json#KEY`
  - [x] SubTask 2.3: 实现 `get_for_log(key)` 返回 `[REDACTED:key]` 占位符
  - [x] SubTask 2.4: 实现 `scan_prompt(prompt)` 检测敏感模式（sk-、paypal:、助记词）并脱敏
  - [x] SubTask 2.5: 在 `.gitignore` 添加 `.secrets/`
  - [x] SubTask 2.6: 新增 `python main.py secrets set/get/list` 子命令
  - [x] SubTask 2.7: 编写单元测试（存储隔离、脱敏、引用解析）

## 阶段二：账本升级与真实收入支持

- [x] Task 3: 账本支持真实/虚拟收入分离
  - [x] SubTask 3.1: 修改 `engine/ledger.py`，新增 `income_real(amount, source, tx_ref, description)` 方法（标记 is_real=true）
  - [x] SubTask 3.2: 新增 `expense_real(amount, purpose, tx_ref, description, decision_ref)` 方法
  - [x] SubTask 3.3: `audit()` 返回结果区分 real_total_income / real_total_expense / virtual_total_income / virtual_total_expense
  - [x] SubTask 3.4: 兼容已有 ledger.yaml（老交易默认 is_real=false）
  - [x] SubTask 3.5: 更新 Reporter 在日报/状态中分别展示真实与虚拟收支
  - [x] SubTask 3.6: 编写单元测试

## 阶段三：PayPal 收款对接

- [x] Task 4: PayPal 支付模块
  - [x] SubTask 4.1: 创建 `engine/payments/__init__.py` 和 `engine/payments/paypal.py`
  - [x] SubTask 4.2: 实现 PayPalClient 类，从 secrets 读取 client_id / client_secret（不进 Prompt）
  - [x] SubTask 4.3: 实现 `create_order(amount, currency, description)` 返回 {order_id, approve_url}
  - [x] SubTask 4.4: 实现 `capture_order(order_id)` 验证支付并返回 {status, amount}
  - [x] SubTask 4.5: 实现 `check_order(order_id)` 查询订单状态
  - [x] SubTask 4.6: 创建订单写入 `company/orders/pending/`，支付成功移至 `company/orders/paid/`
  - [x] SubTask 4.7: 支付成功时调用 `ledger.income_real()` 入账
  - [x] SubTask 4.8: 新增 `python main.py payment create/check <order_id>` 子命令
  - [x] SubTask 4.9: 编写单元测试（mock PayPal API 响应）

## 阶段四：安全闸门与人工协助

- [x] Task 5: 外付款安全审批闸门
  - [x] SubTask 5.1: 实现 `engine/safety/payment_gate.py`
  - [x] SubTask 5.2: 实现 `assess(payment_request)` 评估函数：白名单/预算/战略对齐/可疑模式
  - [x] SubTask 5.3: 评估结果分级：allow / high_risk / block
  - [x] SubTask 5.4: high_risk 必须人工确认，block 拒绝并写告警
  - [x] SubTask 5.5: 白名单存储 `company/config/payees.yaml`，支持 `python main.py payee whitelist add/list`
  - [x] SubTask 5.6: 告警写入 `company/safety/incidents.md`

- [x] Task 6: 人工协助请求机制
  - [x] SubTask 6.1: 实现 `engine/human_loop.py`
  - [x] SubTask 6.2: `request_assistance(message, options)` 通过 AskUserQuestion 工具询问用户
  - [x] SubTask 6.3: `request_approval(decision_context)` 用于高风险决策确认
  - [x] SubTask 6.4: 用户响应记录到 `company/human-requests/YYYY-MM-DD.md`
  - [x] SubTask 6.5: 在 CLI 模式下退化为终端交互提示（非阻塞模式时跳过并记录）

- [x] Task 7: 合规红线检查器
  - [x] SubTask 7.1: 实现 `engine/safety/compliance.py`
  - [x] SubTask 7.2: `check_compliance(action)` 检查 6 条红线（欺诈/操纵/洗钱/大额出款/隐私泄露/违法内容）
  - [x] SubTask 7.3: 命中红线拒绝执行并写告警到 `company/safety/incidents.md`
  - [x] SubTask 7.4: 单笔超 $100 出款强制人工确认
  - [x] SubTask 7.5: 编写单元测试

## 阶段五：季度战略会

- [x] Task 8: 季度战略会机制
  - [x] SubTask 8.1: 扩展 CEO 角色，新增 `quarterly_strategy()` 方法
  - [x] SubTask 8.2: 基于上季度 audit + 市场情报 + 人工请求，输出方向/机会/公告
  - [x] SubTask 8.3: 战略文档写入 `company/strategy/YYYY-Qn.md`
  - [x] SubTask 8.4: 全员智能体 build_prompt 自动注入最新战略文档作为上下文
  - [x] SubTask 8.5: 调度器新增季度触发（1/4/7/10 月 1 日 09:00）
  - [x] SubTask 8.6: 新增 `python main.py strategy --now` 子命令

## 阶段六：加密货币机会分析

- [x] Task 9: 加密货币市场分析模块
  - [x] SubTask 9.1: 创建 `engine/crypto/__init__.py` 和 `engine/crypto/market_analyzer.py`
  - [x] SubTask 9.2: 调用 CoinGecko 公开 API 获取行情数据（无 key）
  - [x] SubTask 9.3: 输出分析报告：机会/风险/合规边界，写入 `company/knowledge/market-research/crypto-YYYY-MM-DD.md`
  - [x] SubTask 9.4: 新增 `python main.py crypto analyze` 子命令

- [x] Task 10: 加密货币钱包管理
  - [x] SubTask 10.1: 实现 `engine/crypto/wallet.py`
  - [x] SubTask 10.2: `register_wallet(chain)` 生成地址（公钥存 `company/config/wallets.yaml`，私钥存 `.secrets/`）
  - [x] SubTask 10.3: `list_wallets()` 列出公钥地址
  - [x] SubTask 10.4: `check_balance(address)` 查询余额（公开 API）
  - [x] SubTask 10.5: 到账时调用 `ledger.income_real(source="crypto_<chain>")`
  - [x] SubTask 10.6: 新增 `python main.py crypto register-wallet/list/balance` 子命令

- [x] Task 11: 加密货币出币安全红线
  - [x] SubTask 11.1: 出币操作强制调用 `human_loop.request_approval()`
  - [x] SubTask 11.2: AI 不持有私钥签名权限，签名操作由用户监督完成
  - [x] SubTask 11.3: 出币记录写入 `company/safety/crypto-outflows.md`
  - [x] SubTask 11.4: 单元测试验证出币必触发人工确认

## 阶段七：编排器集成

- [x] Task 12: Orchestrator 接入真实收入与安全闸门
  - [x] SubTask 12.1: 收入结算阶段优先检查 PayPal 订单与加密货币到账
  - [x] SubTask 12.2: 无真实收入时才用虚拟模拟（保留原有行为）
  - [x] SubTask 12.3: 任何支出阶段调用 `payment_gate.assess()` 前置校验
  - [x] SubTask 12.4: 日报新增「真实收入」「真实支出」「安全事件」字段
  - [x] SubTask 12.5: run-day 失败时记录是否涉及安全闸门拦截

## 阶段八：端到端验证

- [x] Task 13: 端到端验证
  - [x] SubTask 13.1: 配置 TRAE 后端，验证无 API_KEY 时 run-day 正常运行 ✅
  - [x] SubTask 13.2: 配置 PayPal 沙箱 key，验证创建订单 → 模拟支付 → 入账闭环 ⚠️（mock 单测 16/16 通过；真实 API 闭环待用户提供真实 PayPal 沙箱 key）
  - [x] SubTask 13.3: 验证 secrets 脱敏：日志/日报/Prompt 中无明文 key ✅
  - [x] SubTask 13.4: 验证外付款闸门：白名单外收款方触发 high_risk ✅
  - [x] SubTask 13.5: 验证季度战略会手动触发生成战略文档 ✅
  - [x] SubTask 13.6: 验证加密货币市场分析输出报告 ✅
  - [x] SubTask 13.7: 验证合规红线：模拟违法内容决策被拦截 ⚠️（单测 8/8 通过；发现 FRAUD_KEYWORDS 缺金融欺诈词，需 Task 14 修复）
  - [x] SubTask 13.8: 更新 README.md 增加 Real-Money Ops 章节 ✅

## 阶段九：验证发现的问题修复

- [x] Task 14: 修复合规检查器的字段兼容与金融欺诈关键词覆盖
  - [x] SubTask 14.1: `ComplianceChecker.check_compliance` 同时读取 `description` 与 `content` 字段（向后兼容）
  - [x] SubTask 14.2: `_check_privacy_leak` 同时扫描 `prompt`/`content`/`description` 中的敏感模式
  - [x] SubTask 14.3: `FRAUD_KEYWORDS` 补充金融欺诈关键词（保本保息/高收益/稳赚/保收益/无风险/零风险/保证收益/保本理财/庞氏/资金盘/拉人头/传销）
  - [x] SubTask 14.4: 新增单元测试覆盖金融欺诈场景与 description 字段场景
  - [x] SubTask 14.5: 运行 `py -m unittest tests.test_compliance -v` 全部通过（11/11 + 85 回归无问题）

# Task Dependencies（任务依赖）

- Task 1（TRAE 接入）独立，最高优先级
- Task 2（Secrets 管理）独立，可与 Task 1 并行
- Task 3（账本升级）依赖 Task 2（real 收入需 secrets 关联决策）
- Task 4（PayPal）依赖 Task 2、Task 3
- Task 5（付款闸门）依赖 Task 2
- Task 6（人工协助）独立，可与 Task 4/5 并行
- Task 7（合规红线）独立，可与 Task 5/6 并行
- Task 8（季度战略）依赖 Task 1（需 TRAE 模型驱动 CEO）
- Task 9（加密货币分析）依赖 Task 1
- Task 10（钱包管理）依赖 Task 2、Task 3
- Task 11（出币红线）依赖 Task 6、Task 10
- Task 12（编排器集成）依赖 Task 3、4、5、7
- Task 13（端到端验证）依赖 Task 1-12

# 并行化建议

- 第一波并行：Task 1 + Task 2 + Task 6 + Task 7（互不依赖）
- 第二波并行：Task 3 + Task 5 + Task 8 + Task 9（Task 3/5 依赖 Task 2，Task 8/9 依赖 Task 1）
- 第三波并行：Task 4 + Task 10 + Task 11（依赖前两波）
- 第四波：Task 12 → Task 13
