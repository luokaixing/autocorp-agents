# AutoCorp 运行基线（Runbook）

## 1. 概述

### 1.1 目的

本 Runbook 定义 AutoCorp（AI 虚拟自治公司）的标准运行基线，覆盖启动、停止、降级、故障恢复、紧急人工介入等全流程，确保公司能在无人值守的情况下按 SOP 标准化运行，并在异常发生时具备可执行的恢复路径。

### 1.2 适用范围

- **对象**：AutoCorp 全部 7 个虚拟角色（CEO / CTO / COO / Architect / Programmer / Tester / PM）、6 条核心工作流（WF-RESEARCH / WF-DESIGN / WF-BUILD / WF-PROMOTE / WF-SERVICE / WF-REVIEW）、6 个日常 Phase（Phase-Morning / Phase-Research / Phase-Design / Phase-Build / Phase-Promote / Phase-Review）+ 1 个按需 Phase（Phase-Service）。
- **使用者**：项目负责人、值班人员、AI 公司自身（通过 human_loop 自助读取）。
- **触发场景**：首次部署、日常启停、故障排查、健康警报响应、决策门禁触发。

### 1.3 版本

| 版本 | 日期 | 变更说明 |
|------|------|----------|
| v1.0 | 2026-06-29 | 初版，对齐 Spec `standardize-ai-company-ops` Phase 2 Task 6 |

### 1.4 关键文件索引

| 路径 | 用途 |
|------|------|
| `main.py` | CLI 入口 |
| `.env` | LLM 后端与环境变量配置 |
| `.env.example` | 配置模板 |
| `.secrets/` | 密钥明文隔离目录（secrets.json） |
| `company/config/ledger.yaml` | 财务账本（is_real 字段区分真实/模拟收入） |
| `company/config/decision-gates.yaml` | 决策门禁配置 |
| `company/config/task_queue.yaml` | 任务队列 |
| `company/sop/` | SOP 文档（7 角色 + 6 工作流） |
| `company/messages/` | 共享消息池（按日切分 jsonl） |
| `company/health/` | 健康报告（health-YYYY-MM-DD.md） |
| `company/human-requests/` | 人工请求留痕 |
| `company/logs/` | 运行日志 |
| `company/safety/incidents.md` | 事故记录 |

---

## 2. 公司健康运行定义

"公司健康运行"由以下 5 项量化指标定义。任一指标不达标，对应健康报告（`company/health/health-YYYY-MM-DD.md`）中标记为 🟡（黄色警示）或 🔴（红色警报）。

### 2.1 每日产出指标

| 指标 | 阈值 | 计算口径 |
|------|------|----------|
| 每日文件产出 | ≥ 1 个 | `company/articles/` / `company/marketing/` / `company/knowledge/` 三个目录下当日（Asia/Shanghai）新增的 `.md` 文件数 ≥ 1 |

**检查命令**（PowerShell）：
```powershell
$date = Get-Date -Format "yyyy-MM-dd"
(Get-ChildItem -Path company\articles,company\marketing,company\knowledge -Filter "*$date*.md" -Recurse -ErrorAction SilentlyContinue | Measure-Object).Count
```

### 2.2 收入指标

| 指标 | 阈值 | 计算口径 |
|------|------|----------|
| 每周真实收入 | ≥ 1 笔 | `company/config/ledger.yaml` 中 `is_real=true` 的交易，按自然周（周一至周日）累计 ≥ 1 笔 |

**说明**：金额不限，只看真实性。`is_real=false` 的测试/模拟收入不计入。

### 2.3 Phase 完整执行率

| 指标 | 阈值 | 计算口径 |
|------|------|----------|
| Phase 完整执行率 | ≥ 80% | 每日 6 个 Phase（Morning/Research/Design/Build/Promote/Review）中至少 5 个达到 `done` 状态（不含 `skipped` / `timeout`） |

### 2.4 任务队列健康

| 指标 | 阈值 | 计算口径 |
|------|------|----------|
| pending 任务数 | < 30 | `company/config/task_queue.yaml` 中 `status=pending` 的任务数 |
| 任务失败率 | < 50% | 当日 `status=failed` 任务数 / 当日已结束任务数（done + failed） |

**检查命令**：
```powershell
py main.py task-queue list --status pending
py main.py task-queue list --status failed
```

### 2.5 角色激活率

| 指标 | 阈值 | 计算口径 |
|------|------|----------|
| 角色激活率 | ≥ 85% | 7 个角色（CEO / CTO / COO / Architect / Programmer / Tester / PM）中至少 6 个当日有任务认领（claim_at 当日）或产出消息（from_role 命中） |

### 2.6 健康状态分级

| 颜色 | 含义 | 触发条件 |
|------|------|----------|
| 🟢 绿色 | 健康 | 5 项指标全部达标 |
| 🟡 黄色 | 警示 | 1~2 项指标未达标 |
| 🔴 红色 | 警报 | ≥ 3 项指标未达标，或财务健康指标连续 3 天亮红 |

---

## 3. 启动流程

### 3.1 首次启动（新部署）

按以下顺序执行，缺一不可：

```powershell
# 步骤 1：初始化工作区（创建 company/ 目录结构与必要配置文件）
py main.py init

# 步骤 2：配置 .env（基于模板复制后修改）
Copy-Item .env.example .env
# 编辑 .env，确认 LLM_BACKEND=trae（默认无需 API_KEY）
# 如使用 OpenAI：LLM_BACKEND=openai 并填写 OPENAI_API_KEY

# 步骤 3：配置密钥（明文隔离于 .secrets/，不入 git）
py main.py secrets set PAYPAL_CLIENT_ID "你的PayPal客户端ID"
py main.py secrets set PAYPAL_CLIENT_SECRET "你的PayPal客户端密钥"
py main.py secrets set TWITTER_COOKIE "可选：Twitter 登录 Cookie"
py main.py secrets set MIRROR_TOKEN "可选：Mirror.xyz 发布令牌"
py main.py secrets list   # 校验密钥名（不显示值）

# 步骤 4：启动调度器（前台运行，每日 08:00 Asia/Shanghai 自动触发）
py main.py schedule --start
```

### 3.2 日常启动（已初始化）

每日只需启动调度器即可，调度器会在 08:00 / 12:00 / 18:00 自动触发对应批次：

```powershell
py main.py schedule --start
```

调度器阻塞运行，可放入独立终端窗口或后台进程。日志输出到 `company/logs/`。

### 3.3 手动触发完整工作日

用于调试、补跑或紧急推进：

```powershell
# 方式 1：完整工作日（morning + noon + evening 三批次）
py main.py run-day

# 方式 2：完整自主日（与 run-day 等价的自主循环入口）
py main.py autonomous-run
```

### 3.4 手动触发单批次

```powershell
# 只跑晨会循环（Phase-Morning + Phase-Research + Phase-Design）
py main.py autonomous-run --morning

# 只跑执行批次（Phase-Build + Phase-Promote）
py main.py autonomous-run --noon

# 只跑复盘循环（Phase-Review，生成健康报告）
py main.py autonomous-run --evening
```

### 3.5 启动后自检

启动 5 分钟内执行以下自检，确认无异常：

```powershell
py main.py status                       # 检查公司状态与 LLM 连通性
py main.py task-queue list              # 确认任务队列已加载
type company\logs\2026-06-29-errors.log # 查看当日错误日志（日期替换为今日）
```

---

## 4. 停止流程

### 4.1 正常停止

调度器在前台运行时，直接按 `Ctrl+C` 即可正常停止。调度器会在当前批次结束后退出，未完成的任务保留在 `pending` 状态，下次启动继续执行。

```powershell
# 在调度器所在终端窗口按 Ctrl+C
# 等待出现 "调度器已停止" 或进程退出提示
```

### 4.2 紧急停止

调度器无响应或进程僵死时使用：

```powershell
# 步骤 1：查找并终止调度器进程（PowerShell）
Get-Process python | Where-Object { $_.MainWindowTitle -like "*schedule*" -or $_.CommandLine -like "*schedule*" }
Stop-Process -Name python -Force   # 谨慎：会杀掉所有 Python 进程

# 步骤 2：清理 lock 文件（如有）
Remove-Item -Path .scheduler.lock, .autonomous_loop.lock -Force -ErrorAction SilentlyContinue

# 步骤 3：确认进程已退出
Get-Process python -ErrorAction SilentlyContinue
```

### 4.3 停止后状态确认

```powershell
# 任务队列状态（应保留未完成任务为 pending）
py main.py task-queue list --status pending

# 财务账本未被损坏
py main.py status
```

---

## 5. 降级策略

降级原则：**SOP 缺失、外部依赖失败、Phase 超时等场景均不阻塞主流程**，自动降级到现有行为，并在消息池留痕。

### 5.1 LLM 后端失败 → 自动降级到模板/规则

- **触发**：TRAE API 返回 404 / OpenAI API timeout / 调用连续失败
- **降级行为**：`engine/llm_client.py` 已实现 graceful degradation，自动回退到模板化内容生成（如 SEO 文章使用预设模板填充）
- **恢复**：修复 LLM 后端后，下个批次自动恢复 LLM 调用

### 5.2 外部 API 失败 → 切换到国内可访问替代端点

- **触发**：CoinGecko / etherscan / Blockscout 等返回 401 / 403 / 超时
- **降级行为**：`engine/crypto/market_analyzer.py` 切换到国内可访问替代端点
  - CoinGecko → DexScreener（`https://api.dexscreener.com`）
  - etherscan → Blockscout（如已配置国内可用 RPC）
- **恢复**：恢复翻墙或更换 API key 后自动恢复原端点

### 5.3 翻墙缺失 → 通过 human_loop 请求用户开启 VPN

- **触发**：访问 Twitter / Reddit / Mirror / Binance 等被墙服务失败
- **降级行为**：通过 `engine/human_loop.py` 写入 `company/human-requests/YYYY-MM-DD.md`，请求用户开启 VPN
- **降级兜底**：用户未响应时，对应渠道的发布任务标记为 `deferred`，下次循环再试

### 5.4 Chrome 自动化失败 → 混合模式

- **触发**：Playwright 启动失败 / Chrome 调试端口 9222 无法开启 / Chrome profile 被锁
- **降级行为**：切换到混合模式——AI 生成内容（写入 `company/marketing/` 或 `company/knowledge/marketing/`），人工执行最终发布动作
- **恢复**：修复 Chrome（见 §6.4）后自动恢复全自动发布

### 5.5 Phase 连续失败 → 跳过该 Phase

- **触发**：某个 Phase 入口条件不满足 / 超时（如 Phase-Build 已运行 180 分钟仍未完成）
- **降级行为**：`PhaseChain` 强制结束当前 Phase，已完成任务保留产出，未完成任务标记 `failed`（reason 含 `phase_timeout`），publish `phase.timeout.<name>` 或 `phase.skipped.<name>` 消息，继续执行下一个 Phase（不阻塞）
- **恢复**：见 §6.5

---

## 6. 故障恢复路径

### 6.1 场景 1：LLM 后端失败

**症状**：
- `company/logs/YYYY-MM-DD-errors.log` 出现 `TRAE API 404` / `OpenAI API timeout` / `[llm_client] 调用失败`
- 任务批量 `failed`，error_reason 含 LLM 相关字样

**排查**：
```powershell
# 1. 检查 LLM 连通性与后端配置
py main.py status

# 2. 检查 .env 的 LLM_BACKEND 配置
type .env | Select-String "LLM_BACKEND"

# 3. 查看错误日志详情
type company\logs\2026-06-29-errors.log | Select-String "llm_client|TRAE|OpenAI"
```

**恢复**：
```powershell
# 方案 A：切换到 OpenAI 后端（如有可用 API_KEY）
# 编辑 .env：LLM_BACKEND=openai，并填写 OPENAI_API_KEY
# 重启调度器

# 方案 B：修复 TRAE 端点（默认端点 https://api.trae.cn/v1，确认网络可达）
curl -I https://api.trae.cn/v1

# 方案 C：手动重跑失败的晨会批次
py main.py autonomous-run --morning
```

### 6.2 场景 2：外部 API 失败

**症状**：
- 错误日志出现 `CoinGecko timeout` / `Blockscout 401` / `etherscan rate limit`
- `company/knowledge/market-research/` 当日未产出 pm-scan 文件

**排查**：
```powershell
# 1. 检查翻墙状态
curl -I --max-time 10 https://api.coingecko.com

# 2. 检查 API key 是否过期
py main.py secrets list
py main.py secrets get ETHERSCAN_API_KEY   # 谨慎：会输出明文

# 3. 查看错误日志
type company\logs\2026-06-29-errors.log | Select-String "CoinGecko|Blockscout|etherscan"
```

**恢复**：
```powershell
# 方案 A：开启 VPN（用户手动）
# 重试：py main.py autonomous-run --morning

# 方案 B：切换到国内可访问替代端点（代码已内置，删除失败端点的 API key 即可触发降级）
py main.py secrets set ETHERSCAN_API_KEY ""

# 方案 C：跳过市场分析，手动入队一个不依赖外部 API 的任务
py main.py task-queue add --title "人工选题" --description "外部 API 失败，改用知识库选题" --type research --priority P1
```

### 6.3 场景 3：翻墙缺失

**症状**：
- 访问 Twitter / Reddit / Mirror / Binance 失败
- COO 发布任务连续 `failed`，error_reason 含 `ConnectionError` / `SSLError`
- `company/human-requests/YYYY-MM-DD.md` 出现 VPN 开启请求

**排查**：
```powershell
# 1. 测试连通性
curl -I --max-time 10 https://twitter.com
curl -I --max-time 10 https://www.binance.com

# 2. 查看人工请求
type company\human-requests\2026-06-29.md
```

**恢复**：
```powershell
# 方案 A：开启 VPN（用户手动）
# 重试发布：py main.py autonomous-run --noon

# 方案 B：降级为"AI 生成内容 + 人工执行发布"模式
# AI 已将内容写入 company/marketing/，用户手动复制到目标渠道
# 完成后手动标记任务 done：
#   编辑 company/config/task_queue.yaml，将对应任务的 status 改为 done
```

### 6.4 场景 4：Chrome 自动化失败

**症状**：
- Playwright 启动失败：`browser launch failed` / `Executable doesn't exist`
- Chrome 调试端口 9222 无法开启：`netstat | findstr :9222` 无输出
- Chrome profile 被锁：`exit_type=Crashed`

**排查**：
```powershell
# 1. 检查 9222 端口
netstat -ano | findstr :9222

# 2. 检查 Chrome profile 锁状态（默认用户数据目录）
# 查找 Default/Preferences 文件，检查 exit_type 字段
# 路径示例：C:\Users\<用户名>\AppData\Local\Google\Chrome\User Data\Default\Preferences

# 3. 检查 agent-browser 是否安装
pip show agent-browser 2>$null
```

**恢复**：
```powershell
# 方案 A：从 Chrome 菜单正常退出一次（修复 exit_type=Crashed）
# 手动打开 Chrome → 菜单 → 退出 → 重新启动调度器

# 方案 B：重置 Chrome profile 锁
# 关闭所有 Chrome 进程
Get-Process chrome -ErrorAction SilentlyContinue | Stop-Process -Force
# 删除 SingletonLock / SingletonCookie 等锁文件（路径见排查步骤 2）

# 方案 C：切换到混合模式（见 §5.4）
# AI 生成内容到 company/marketing/，人工执行发布
```

### 6.5 场景 5：Phase 连续失败

**症状**：
- `company/messages/` 中当日 jsonl 文件出现连续多个 `phase.timeout.*` 或 `phase.skipped.*` 消息
- `company/health/health-YYYY-MM-DD.md` 中 Phase 完整执行率 < 80%（红色）
- 当日 `company/articles/` / `company/marketing/` / `company/knowledge/` 无新增文件

**排查**：
```powershell
# 1. 查看健康报告红色指标
type company\health\health-2026-06-29.md

# 2. 查看当日消息池
findstr /C:"phase.timeout" /C:"phase.skipped" company\messages\message-pool-2026-06-29.jsonl

# 3. 查看错误日志
type company\logs\2026-06-29-errors.log
```

**恢复**：
```powershell
# 步骤 1：识别瓶颈 Phase（如 Phase-Build 连续超时）

# 步骤 2：检查该 Phase 参与角色的 execute_task（如 Programmer）
#   - Programmer 是否因 LLM 失败？（见 §6.1）
#   - 是否因前置产物缺失？（检查 architecture.md 是否存在）
#   - 是否因 SOP 违规拦截？（检查消息池 task.blocked）

# 步骤 3：修复根因后，单独重跑该 Phase
py main.py phase run Phase-Build

# 步骤 4：如 phase 命令不可用（Phase 4 之前），重跑整个批次
py main.py autonomous-run --noon
```

---

## 7. 紧急人工介入场景

以下场景强制触发人工介入。DecisionGate 命中后通过 `engine/human_loop.py` 写入 `company/human-requests/YYYY-MM-DD.md`，等待用户回复。

### 7.1 财务红色警报

| 触发条件 | 介入动作 | 配置来源 |
|----------|----------|----------|
| 钱包余额连续 3 天为 0 | 立即通知用户，次日 Phase-Morning 把"变现突破"列为 P0 任务 | `company/config/health-thresholds.yaml` |

### 7.2 运营红色警报

| 触发条件 | 介入动作 |
|----------|----------|
| Phase 连续 2 天完整执行率 < 50% | 通知用户介入排查，参考 §6.5 |

### 7.3 决策门禁强制确认

以下决策点由 `company/config/decision-gates.yaml` 定义，命中即拦截等待人工确认：

| 决策点 | 触发条件 | 确认人 | 超时策略 |
|--------|----------|--------|----------|
| 真实出款 | 任意金额 | user | cancel |
| 出币操作 | 任意金额 | user | cancel |
| 对外报价 | 报价 > $50 或折扣 > 20% | user | defer |
| 首次发布到新渠道 | first_time_channel=true | coo | defer |
| 战略方向调整 | 季度战略会关键决策点 | ceo | escalate |
| 产品立项 | 预计成本 > $20 或周期 > 3 天 | user | defer |
| 订单接收/拒绝 | 金额 > $100 或客户首次合作 | user | defer |

### 7.4 人工介入响应流程

1. 用户收到通知（终端输出 / `company/human-requests/` 新文件）
2. 用户阅读请求内容，决策（同意 / 拒绝 / 修改）
3. 用户通过 CLI 或编辑 yaml 文件回复
4. 系统收到回复后继续执行或取消任务

---

## 8. 常见错误排查清单

按错误关键词索引，快速定位故障场景与恢复路径：

| 错误关键词 | 故障场景 | 恢复路径 |
|------------|----------|----------|
| `TRAE API 404` | LLM 后端失败 | 见 §6.1 场景 1 |
| `OpenAI API timeout` | LLM 后端失败 | 见 §6.1 场景 1 |
| `[llm_client] 调用失败` | LLM 后端失败 | 见 §6.1 场景 1 |
| `CoinGecko timeout` | 外部 API 失败 | 见 §6.2 场景 2 |
| `Blockscout timeout` | 外部 API 失败 | 见 §6.2 场景 2 |
| `etherscan rate limit` | 外部 API 失败 | 见 §6.2 场景 2 |
| `ConnectionError` / `SSLError`（访问 Twitter/Reddit/Mirror/Binance） | 翻墙缺失 | 见 §6.3 场景 3 |
| `Chrome exit_type Crashed` | Chrome 自动化失败 | 见 §6.4 场景 4 |
| `browser launch failed` | Chrome 自动化失败 | 见 §6.4 场景 4 |
| `:9222 无法开启` | Chrome 自动化失败 | 见 §6.4 场景 4 |
| `Phase skipped` | Phase 连续失败 | 见 §6.5 场景 5 |
| `phase.timeout.*` | Phase 连续失败 | 见 §6.5 场景 5 |
| `task failed with phase_timeout` | Phase 连续失败 | 见 §6.5 场景 5 |
| `DecisionGate triggered` | 正常行为 | 查看 `company/human-requests/YYYY-MM-DD.md`，按 §7 响应 |
| `sop.missing` | 正常行为（SOP 缺失降级） | 任务标记 `sop_compliance: degraded`，可补 SOP 文件到 `company/sop/` |
| `task.blocked` | SOP 违规拦截 | 检查消息池 `reason` 字段（如 `missing_prd`），补齐前置产物后重跑 |
| `decision.timeout` | 决策门禁超时 | 按 `timeout_action` 策略处理（cancel/defer/escalate） |
| `health.alert.red` | 健康红色警报 | 查看 `company/health/health-YYYY-MM-DD.md`，按对应指标恢复 |

---

## 9. 维护周期

### 9.1 每日（自动）

| 时间 | 任务 | 触发方式 | 产物 |
|------|------|----------|------|
| 08:00 | Phase-Morning 晨会决策 | 调度器自动触发 | 立项清单 |
| 12:00 | Phase-Build + Phase-Promote | 调度器自动触发 | 代码 + 推广物料 |
| 18:00 | Phase-Review 复盘 + 健康报告 | 调度器自动触发 | `company/health/health-YYYY-MM-DD.md` |

### 9.2 每周（自动）

| 任务 | 触发方式 | 产物 |
|------|----------|------|
| CEO 周复盘 | Phase-Review 在每周日触发 | 周报写入 `company/operations/` |
| 真实收入核对 | 自动统计 `ledger.yaml` 中本周 `is_real=true` 交易 | 健康报告中"每周真实收入"指标 |

### 9.3 每月（人工 + 自动）

| 任务 | 触发方式 | 说明 |
|------|----------|------|
| 检查 `.secrets/` 密钥有效性 | 人工 | 校验 PayPal / Twitter / Mirror 等密钥是否过期，必要时通过 `py main.py secrets set <key> <value>` 更新 |
| 月度运营复盘 | 自动 | 月末 Phase-Review 生成月度汇总 |

### 9.4 每季度（自动触发 + 人工确认）

| 任务 | 触发方式 | 产物 |
|------|----------|------|
| 季度战略会 | 调度器在季度初自动触发，或手动 `py main.py strategy --now` | `company/strategy/YYYY-QN.md` |
| 战略方向调整确认 | DecisionGate `strategy_adjust` 命中 | 通过 human_loop 请求 CEO 确认 |

---

## 10. 联系与升级

### 10.1 AI 公司自助升级路径

AI 公司遇到无法自愈的故障时，按以下顺序升级：

1. **自动降级**：按 §5 降级策略自动降级，不阻塞主流程
2. **消息池留痕**：publish `health.alert.red` / `task.blocked` / `phase.timeout.*` 等消息到 `company/messages/`
3. **人工请求**：写入 `company/human-requests/YYYY-MM-DD.md`，等待用户介入
4. **紧急通知**：紧急情况（如财务红色警报）直接通过 human_loop 通知用户

### 10.2 用户介入入口

| 入口 | 用途 |
|------|------|
| `company/human-requests/YYYY-MM-DD.md` | 查看当日所有人工请求 |
| `company/health/health-YYYY-MM-DD.md` | 查看当日健康报告 |
| `company/safety/incidents.md` | 查看事故记录 |
| `py main.py status` | 查看公司当前状态 |
| `py main.py task-queue list` | 查看任务队列 |

### 10.3 升级阈值

| 阈值 | 升级动作 |
|------|----------|
| 单个故障 24 小时未恢复 | 写入 `company/safety/incidents.md` |
| 红色警报连续 3 天 | 暂停自主运营，等待用户介入 |
| 决策门禁超时 | 按 `timeout_action` 处理（cancel/defer/escalate） |

---

## 附录：Runbook 自验证清单

用户阅读本 Runbook 后，应能独立完成以下操作（对应 SubTask 6.4）：

- [ ] 首次启动：`init` → 配置 `.env` → 配置 secrets → `schedule --start`
- [ ] 日常启动：`py main.py schedule --start`
- [ ] 正常停止：`Ctrl+C`
- [ ] 紧急停止：`Stop-Process` + 清理 lock 文件
- [ ] 手动触发完整工作日：`py main.py run-day`
- [ ] 手动触发单批次：`py main.py autonomous-run --morning`
- [ ] 故障排查：根据错误关键词查 §8，定位到 §6 对应场景执行恢复
- [ ] 响应人工介入：阅读 `company/human-requests/` 并回复
- [ ] 查看健康状态：阅读 `company/health/health-YYYY-MM-DD.md`
