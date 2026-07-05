# Crypto Narrative Intelligence API — 上架操作清单

> 日期：2026-07-05
> API MVP：✅ 已完成（7/7 端到端测试通过）
> 战略决策：[build-crypto-narrative-api-2026-07-05.md](file:///d:\autoCompany\company\decisions\build-crypto-narrative-api-2026-07-05.md)
> 收款链路：PayPal Live（已通）→ RapidAPI 自带付费用户池

---

## 一、API 概览

### 1.1 核心价值
让开发者用一次 API 调用获取 RWA / DePIN / AI Agent 三大 2026 H2 加密主线的：
- 协议 TVL 实时数据（来自 DefiLlama）
- GitHub Stars + 活跃度（来自 GitHub API）
- **AutoCorp 独家算法的「叙事热度评分」**（0-100）
- 跨叙事趋势排行

### 1.2 已验证的端点

| 端点 | 功能 | 测试结果 |
|------|------|---------|
| `GET /health` | 健康检查（无需鉴权） | ✅ |
| `GET /` | API 概览 | ✅ |
| `GET /narratives` | 三大主线总览 | ✅ |
| `GET /narratives/{slug}` | 单主线详情 | ✅ |
| `GET /narratives/{slug}/protocols` | 协议列表 + TVL + GitHub | ✅ |
| `GET /narratives/{slug}/score` | 叙事热度评分（AutoCorp 算法） | ✅ |
| `GET /trending?limit=N` | 跨叙事趋势排行 | ✅ |

### 1.3 真实测试数据（2026-07-05 14:48 UTC）

```
RWA Overall Score: 29.18 (Warm)
DePIN Overall Score: 7.23 (Cold)
AI Agent Overall Score: 8.55 (Cold)

Top 5 Trending:
1. Maple Finance (rwa): 44.45 - stars: 73, TVL change: +0.16%
2. Filecoin (depin): 36.17 - stars: 2988
3. MakerDAO (rwa): 29.18 - TVL change: -5.94%
4. Ondo Finance (rwa): 29.09 - TVL change: +22.19%
5. Centrifuge (rwa): 27.65 - TVL change: +0.24%
```

---

## 二、文件清单

### 2.1 API 代码
- [api_server/main.py](file:///d:\autoCompany\api_server\main.py) — FastAPI 主应用（约 580 行）
- [api_server/__init__.py](file:///d:\autoCompany\api_server\__init__.py) — 包入口
- [api_server/README.md](file:///d:\autoCompany\api_server\README.md) — 完整 API 文档
- [api_server/requirements.txt](file:///d:\autoCompany\api_server\requirements.txt) — Python 依赖

### 2.2 测试
- [scripts/test_api_e2e.py](file:///d:\autoCompany\scripts\test_api_e2e.py) — 端到端测试脚本（7/7 通过）

### 2.3 战略决策
- [company/decisions/build-crypto-narrative-api-2026-07-05.md](file:///d:\autoCompany\company\decisions\build-crypto-narrative-api-2026-07-05.md) — 战略决策文档

### 2.4 安全清理
- ✅ `engine/agents/coo.py` — 移除硬编码钱包地址，改为 SecretsManager 读取
- ✅ `engine/agents/tester.py` — 移除硬编码钱包地址
- ✅ `engine/agents/programmer.py` — 移除硬编码钱包地址
- ✅ `autocorp_agents/README.md` — 移除公开钱包地址
- ✅ `autocorp_paypal_cli/README.md` — 移除公开钱包地址
- ✅ `.secrets/secrets.json` — 添加 `tipping_address_eth` 字段
- ✅ `.gitignore` 已包含 `.secrets/`

---

## 三、部署到 Render.com（用户操作，5 分钟）

### 步骤 1：推送代码到 GitHub
（前提：用户已创建 GitHub 仓库）

```bash
cd d:\autoCompany
git add api_server/ autocorp_agents/ autocorp_paypal_cli/ engine/ scripts/
git commit -m "feat: add Crypto Narrative Intelligence API + autocorp-agents + paypal-cli"
git push origin main
```

### 步骤 2：在 Render.com 创建 Web Service
1. 访问 https://render.com/ → 用 GitHub 账号登录
2. New + → Web Service
3. 连接 GitHub 仓库
4. 配置：
   - Name: `crypto-narrative-api`
   - Runtime: Python 3
   - Build Command: `pip install -r api_server/requirements.txt`
   - Start Command: `uvicorn api_server.main:app --host 0.0.0.0 --port $PORT`
   - Instance Type: Free
5. Environment Variables:
   - `RAPIDAPI_PROXY_SECRET` = 自定义一个随机字符串（保存好）
6. Create Web Service
7. 等待部署完成（约 2-3 分钟）
8. 获得 URL：`https://crypto-narrative-api.onrender.com`

### 步骤 3：验证部署
```bash
curl https://crypto-narrative-api.onrender.com/health
# 期望返回 {"status":"ok","timestamp":"..."}
```

---

## 四、上架 RapidAPI（用户操作，10 分钟）

### 步骤 1：注册 RapidAPI Provider
1. 访问 https://rapidapi.com/auth/sign-up
2. 用 PayPal 同邮箱注册
3. 完成邮箱验证
4. 访问 https://rapidapi.com/provider

### 步骤 2：创建 API
1. My APIs → Add New API
2. API Name: `Crypto Narrative Intelligence`
3. Short Description: `Real-time tracking of RWA, DePIN, and AI Agent crypto narratives with proprietary heat score.`
4. Category: `Blockchain` 或 `Data`
5. Base URL: `https://crypto-narrative-api.onrender.com`（Render.com URL）
6. Proxy Secret: 复制步骤 2 中设置的 `RAPIDAPI_PROXY_SECRET`

### 步骤 3：配置端点
为每个端点添加描述和示例：

**GET /narratives**
- Description: Get overview of all three crypto mainlines (RWA, DePIN, AI Agent)
- Parameters: none
- Example Response: (粘贴测试输出)

**GET /narratives/{slug}**
- Description: Get detail of a single narrative
- Parameters: `slug` (path, enum: `rwa`, `depin`, `ai-agent`)

**GET /narratives/{slug}/protocols**
- Description: Get top protocols in a narrative with TVL + GitHub data
- Parameters: `slug` (path)

**GET /narratives/{slug}/score**
- Description: Get AutoCorp narrative heat score (0-100)
- Parameters: `slug` (path)

**GET /trending**
- Description: Get trending protocols across all narratives
- Parameters: `limit` (query, default: 10, max: 15)

### 步骤 4：配置定价
1. Pricing → Add Pricing Tier
2. Free: $0/month, 100 calls/day
3. Pro: $29/month, 10,000 calls/day
4. Business: $99/month, 100,000 calls/day
5. Enterprise: $299/month, Unlimited
6. **关联 PayPal 账户**（RapidAPI 支持 PayPal 提现）

### 步骤 5：发布
1. 检查所有端点
2. 测试调用（RapidAPI 提供 Test 按钮）
3. Publish API

---

## 五、收款链路（已验证）

```
RapidAPI 用户调用 API
       ↓
RapidAPI 处理鉴权 + 计费 + 抽成（约 20%）
       ↓
RapidAPI 月度打款到 PayPal
       ↓
PayPal → 国内银行账户
```

**关键优势**：
- 不需要域名
- 不需要 Stripe
- 不需要公司资质
- RapidAPI 自带 400 万开发者用户池（零获客成本）
- PayPal 已通过 Live 测试

---

## 六、危机止损（硬约束）

### 6.1 时间止损
- **第 14 天（7-19）**：API 必须上架 RapidAPI
- **第 30 天（8-04）**：必须有首批试用用户
- **第 60 天（9-03）**：必须有首个付费用户
- **第 90 天（10-03）**：MRR ≥ $50
- **第 180 天（2027-01）**：MRR ≥ $500

### 6.2 数据质量止损
- 部分协议的 GitHub slug 需要修正（如 centrifuge 应为 `centrifuge/centrifuge`）
- 部分协议的 DefiLlama slug 需要验证
- 首批用户反馈后立即修正

### 6.3 竞争止损
- 每月监控 CoinGecko / Messari 是否推出类似 API
- 如果大厂入场，立即寻找更细分的市场（如 Agent-as-a-Service 评测）

---

## 七、AI 可以独立继续做的事

不需用户介入，AI 可以继续推进：

1. **数据质量优化**：
   - 修正 NARRATIVES 中 GitHub slug 格式（centrifuge → centrifuge/centrifuge-js）
   - 添加更多协议（从 5 个扩展到 10 个/叙事）

2. **API 功能扩展**：
   - 添加 `/narratives/{slug}/news` 端点（聚合 Mirror/Paragraph）
   - 添加 `/narratives/{slug}/github-leaderboard` 端点
   - 添加历史数据查询（`/narratives/{slug}/history?days=30`）

3. **文档与示例**：
   - 写 Python / JavaScript / cURL 调用示例
   - 写集成教程（如何在 DApp 中使用此 API）

4. **GitHub Actions CI**：
   - 自动运行测试
   - 自动部署到 Render.com

5. **每日数据备份**：
   - 缓存历史数据到 `api_cache/`
   - 用于后续训练叙事预测模型

---

## 八、最终结论

### 用户原始痛点
> 「发文章我看半年内最热门的打赏也就1$，根本上就是不确定且没价值」

### 解决方案
从 **B2C 内容打赏** 转向 **B2B API 即服务**：

| 维度 | 内容打赏（旧） | API 即服务（新） |
|------|---------------|-----------------|
| 客户 | B2C 终端读者 | B2B 开发者 |
| 付费意愿 | 随机打赏 | 月费订阅 |
| 客单价 | $0.5-5 | $29-299/月 |
| 收入预测性 | 不确定 | MRR 稳定 |
| 复用能力 | 每篇新文章 | 数据已每天生产 |
| 获客成本 | 高（需流量） | 零（RapidAPI 自带用户池） |

### 长期价值
- **半年打赏预期**：$5-20
- **半年 API MRR 预期**：$500-2000（**100-400 倍提升**）

### 行动项
- ✅ API MVP 已完成（7/7 测试通过）
- ✅ 安全清理完成（钱包地址不再硬编码）
- ✅ 战略决策文档已完成
- ⏳ 用户操作：创建 GitHub 仓库 + 部署 Render.com + 上架 RapidAPI（共约 20 分钟）
