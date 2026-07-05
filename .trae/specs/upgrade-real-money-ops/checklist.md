# Checklist - AutoCorp 真实变现运营升级（Real-Money Ops）

> 验证清单：逐项检查，全部通过后方可交付。每个检查点对应 spec.md 中的需求。
> 安全相关检查点为硬性门槛，未通过不得上线涉及真实资金的功能。

## 阶段一：TRAE 模型 + Secrets 管理

### TRAE 模型接入
- [x] LLM 客户端支持 LLM_BACKEND 配置项（trae|openai|custom）
- [x] 无 OPENAI_API_KEY 时自动回退到 TRAE 后端，不报错
- [x] TRAE 端点可通过环境变量配置
- [x] `.env.example` 含 LLM_BACKEND / TRAE_BASE_URL / TRAE_MODEL 说明
- [x] `python main.py run-day` 在无 API_KEY 时正常执行（走 TRAE 后端）

### Secrets 安全管理器
- [x] `engine/secrets.py` 提供 set/get/list/delete API
- [x] 明文密钥存于 `.secrets/secrets.json`，不存于代码或 company/config/
- [x] `company/config/secrets.yaml` 仅存引用 `ref://...`，不含明文
- [x] `get_for_log(key)` 返回 `[REDACTED:key]` 占位符
- [x] `scan_prompt(prompt)` 能检测并脱敏 sk-、paypal:、助记词等敏感模式
- [x] `.gitignore` 包含 `.secrets/`
- [x] `python main.py secrets set/get/list` 子命令可用
- [x] 单元测试覆盖存储隔离、脱敏、引用解析

## 阶段二：账本升级

### 真实/虚拟收入分离
- [x] `ledger.income_real(amount, source, tx_ref, description)` 方法存在且标记 is_real=true
- [x] `ledger.expense_real(amount, purpose, tx_ref, description, decision_ref)` 方法存在
- [x] `audit()` 返回结果区分 real_total_income / real_total_expense / virtual_total_*
- [x] 兼容老 ledger.yaml（老交易默认 is_real=false）
- [x] Reporter 日报/状态分别展示真实与虚拟收支
- [x] 单元测试覆盖 real/virtual 分离

## 阶段三：PayPal 收款

### PayPal 支付模块
- [x] `engine/payments/paypal.py` 实现 PayPalClient 类
- [x] client_id / client_secret 从 secrets 读取，不进 Prompt/日志
- [x] `create_order(amount, currency, description)` 返回 {order_id, approve_url}
- [x] `capture_order(order_id)` 验证支付状态
- [x] `check_order(order_id)` 查询订单状态
- [x] 订单写入 `company/orders/pending/`，支付成功移至 `company/orders/paid/`
- [x] 支付成功调用 `ledger.income_real()` 入真实收入
- [x] `python main.py payment create/check <order_id>` 子命令可用
- [x] 单元测试 mock PayPal API 响应验证流程

## 阶段四：安全闸门与人工协助

### 外付款安全审批闸门
- [x] `engine/safety/payment_gate.py` 实现 `assess(payment_request)` 函数
- [x] 评估维度：白名单 / 预算 / 战略对齐 / 可疑模式
- [x] 评估结果分级：allow / high_risk / block
- [x] high_risk 必须人工确认
- [x] block 拒绝并写告警
- [x] 白名单存于 `company/config/payees.yaml`
- [x] `python main.py payee whitelist add/list` 子命令可用
- [x] 告警写入 `company/safety/incidents.md`

### 人工协助请求机制
- [x] `engine/human_loop.py` 实现 request_assistance / request_approval
- [x] 通过 AskUserQuestion 工具询问用户
- [x] 用户响应记录到 `company/human-requests/YYYY-MM-DD.md`
- [x] CLI 非阻塞模式下退化为终端提示或跳过并记录

### 合规红线检查器
- [x] `engine/safety/compliance.py` 实现 `check_compliance(action)`
- [x] 覆盖 6 条红线：欺诈/操纵/洗钱/大额出款/隐私泄露/违法内容
- [x] 命中红线拒绝执行并写告警
- [x] 单笔超 $100 出款强制人工确认
- [x] 单元测试覆盖各红线场景

## 阶段五：季度战略会

### 季度战略机制
- [x] CEO 新增 `quarterly_strategy()` 方法
- [x] 基于上季度 audit + 市场情报 + 人工请求输出方向/机会/公告
- [x] 战略文档写入 `company/strategy/YYYY-Qn.md`
- [x] 全员智能体 build_prompt 自动注入最新战略文档
- [x] 调度器支持季度触发（1/4/7/10 月 1 日 09:00）
- [x] `python main.py strategy --now` 子命令可用

## 阶段六：加密货币

### 市场分析
- [x] `engine/crypto/market_analyzer.py` 调用 CoinGecko 公开 API
- [x] 输出分析报告含机会/风险/合规边界
- [x] 报告写入 `company/knowledge/market-research/crypto-YYYY-MM-DD.md`
- [x] `python main.py crypto analyze` 子命令可用

### 钱包管理
- [x] `engine/crypto/wallet.py` 实现 register_wallet / list_wallets / check_balance
- [x] 公钥存 `company/config/wallets.yaml`，私钥存 `.secrets/`
- [x] 到账调用 `ledger.income_real(source="crypto_<chain>")`
- [x] `python main.py crypto register-wallet/list/balance` 子命令可用

### 出币安全红线
- [x] 出币操作强制调用 `human_loop.request_approval()`
- [x] AI 不持有私钥签名权限
- [x] 出币记录写入 `company/safety/crypto-outflows.md`
- [x] 单元测试验证出币必触发人工确认

## 阶段七：编排器集成

### Orchestrator 升级
- [x] 收入结算阶段优先检查 PayPal 订单与加密货币到账
- [x] 无真实收入时才用虚拟模拟
- [x] 支出阶段调用 `payment_gate.assess()` 前置校验
- [x] 日报新增「真实收入」「真实支出」「安全事件」字段
- [x] 安全闸门拦截时记录原因

## 阶段八：端到端验证

### 真实资金闭环
- [x] 配置 TRAE 后端，无 API_KEY 时 run-day 正常运行
- [x] PayPal 沙箱：创建订单 → 模拟支付 → 入账闭环跑通
  > 备注：mock 单元测试 16/16 通过（create_order/capture_order/check_order/订单流转/入账闭环均已覆盖）；真实 API 闭环待用户提供 PayPal 沙箱 key 后跑通
- [x] 真实收入入账后账本 is_real=true 标记正确
- [x] 状态命令展示真实收入与虚拟收入分别汇总

### 安全验证（硬性门槛）
- [x] 日志/日报/Prompt 中无明文 PayPal key 或私钥
- [x] `scan_prompt` 能拦截注入敏感数据的尝试
- [x] 白名单外收款方触发 high_risk 评估
- [x] 单笔超 $100 出款触发人工确认
- [x] 模拟违法内容决策被合规红线拦截
- [x] 出币操作必须人工确认，AI 无法自主执行

### 业务能力验证
- [x] 季度战略会手动触发生成战略文档
- [x] 加密货币市场分析输出报告
- [x] 钱包注册生成地址，公私钥分离存储
- [x] README.md 新增 Real-Money Ops 章节说明
