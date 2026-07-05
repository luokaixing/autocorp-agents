# 基于实时数据重建第一桶金路径 Spec

## Why

AI 公司运营 3 天零真实收入，暴露两个致命问题：(1) 旧 spec `earn-first-crypto-income` 假设 Binance L&E 课程可用，实际课程已全部结束，导致用户注册+KYC 后白折腾；(2) AI 推荐基于 2025 年 8 月前的记忆，加密活动时效性以小时/天计，记忆型推荐必然失效。需要建立"实时数据验证优先"的新方法论，并立即启动 3 天内能产生首笔真实收入的双轨路径。

## What Changes

- **新增** `engine/crypto/realtime_opportunity_scanner.py` —— 实时机会扫描器，强制要求每个推荐机会必须有当日可访问的 URL 数据源
- **新增** `engine/content/publish0x_batch_publisher.py` —— Publish0x 批量发布器（内容打赏即时到账路径）
- **新增** `engine/crypto/layer3_task_monitor.py` —— Layer3 任务监控器（Liquid Rewards 即时到账路径）
- **新增** `scripts/scan_realtime_opportunities.py` —— CLI 入口，每次运行产出当日机会报告
- **修改** `company/knowledge/playbooks/first-income-playbook.md` —— 用实时验证后的路径替换过时的 Binance L&E 主路径
- **修改** `engine/crypto/opportunity_radar.py` —— 新增 `verify_realtime()` 方法，未通过实时验证的机会标记为"不可用"
- **新增** `company/knowledge/playbooks/user-binance-verification-guide.md` —— 用户登录 Binance 确认 L&E 实际状态的指引
- **新增** `company/decisions/crisis-first-income-2026-06-30.md` —— 危机决策记录

## Impact

- Affected specs: `earn-first-crypto-income`（标记为 deprecated，保留历史）
- Affected code:
  - `engine/crypto/opportunity_radar.py` —— 增加实时验证层
  - `engine/content/` —— 新增 publish0x 模块
  - `company/knowledge/playbooks/first-income-playbook.md` —— 重写
  - `scripts/` —— 新增实时扫描脚本
- Affected operations: 每日 08:00 晨会新增"实时机会验证"环节，未通过验证的机会不进入 task_queue

## ADDED Requirements

### Requirement: 实时数据验证优先

AI 公司所有赚钱机会推荐 SHALL 基于当日可访问的 URL 数据源验证，不允许凭记忆推荐。

#### Scenario: 推荐机会前的实时验证
- **WHEN** AI 公司向用户推荐任何赚钱机会
- **THEN** 必须先调用 `RealtimeOpportunityScanner.verify(url)` 验证该机会当日是否真实可用
- **AND** 验证失败的机会标记为"未验证"或"已失效"，不进入 task_queue

#### Scenario: 机会报告生成
- **WHEN** 用户运行 `py main.py scan-opportunities` 或 08:00 晨会触发
- **THEN** 系统产出 `company/knowledge/opportunities/realtime-scan-YYYY-MM-DD.md`
- **AND** 报告每个机会必须包含：验证时间戳、数据源 URL、当前状态、预期收益、启动门槛

### Requirement: Publish0x 内容打赏双轨路径

AI 公司 SHALL 建立 Publish0x 批量内容生产能力，作为 3 天内产生首笔收入的主路径之一。

#### Scenario: 批量文章发布
- **WHEN** AI 公司执行每日内容产出任务
- **THEN** 生成至少 1 篇基于实时数据的专业文章
- **AND** 文章格式适配 Publish0x（Markdown + 打赏地址）
- **AND** 文章保存到 `company/projects/seo-content-generator/articles/publish0x/` 目录

#### Scenario: 打赏到账追踪
- **WHEN** Publish0x 文章产生打赏
- **THEN** 用户在 Publish0x 后台查看余额并截图反馈
- **AND** AI 公司记录到 `company/config/ledger.yaml` 的 `is_real=true` 交易

### Requirement: Layer3 任务即时到账路径

AI 公司 SHALL 监控 Layer3 平台新任务上架，作为 3 天内产生首笔收入的另一主路径。

#### Scenario: 任务监控
- **WHEN** 08:00/12:00/16:00 调度触发或用户手动运行 `py main.py layer3-monitor`
- **THEN** 抓取 `https://app.layer3.xyz/discover` 当前活跃任务
- **AND** 筛选 Liquid Rewards 类型任务（即时到账）
- **AND** 产出任务清单保存到 `company/knowledge/layer3/tasks-YYYY-MM-DD.md`

#### Scenario: 任务执行指引
- **WHEN** 发现高价值 Liquid Rewards 任务
- **THEN** 生成用户操作指引（步骤 + 截图位置 + 预期到账金额）
- **AND** 指引保存到 `company/knowledge/layer3/task-guide-<task-id>.md`

### Requirement: Binance L&E 用户验证闭环

AI 公司 SHALL 提供明确的用户操作指引，让用户登录 Binance 后确认 L&E 课程实际状态，而非 AI 凭记忆推荐。

#### Scenario: 用户验证流程
- **WHEN** 用户完成 Binance 注册 + KYC
- **THEN** AI 公司输出验证指引文档
- **AND** 指引包含：登录 URL、L&E 页面路径、需截图确认的 3 个要素（课程列表、奖励金额、是否可点 Start）
- **AND** 用户反馈截图后，AI 公司基于实际可见课程生成答题指南

## MODIFIED Requirements

### Requirement: 第一桶金执行手册

原手册以 Binance L&E 为 P0 主路径，现修改为基于实时验证的三轨并行：

- **P0-A（即时到账，零成本）**: Layer3 Liquid Rewards 任务
- **P0-B（即时到账，零成本）**: Publish0x 内容批量打赏
- **P0-C（待用户验证）**: Binance L&E（用户登录确认实际课程状态后再决定是否投入）
- **P1（1-4 周）**: Airdrops.io 已确认空投（Mantle/Aether/NEAR 等 6 个 Confirmed）
- **P2（需本金）**: DefiLlama 高 APY 流动性挖矿

## REMOVED Requirements

### Requirement: Binance L&E 批量答题指南自动产出

**Reason**: Binance L&E 课程已全部结束（用户 2026-06-30 登录确认），原假设失效。且 AI 无法远程抓取 Binance 页面验证课程状态，继续保留会导致重复白折腾。
**Migration**: 改为"用户验证驱动"模式——用户登录后截图反馈，AI 基于实际可见课程生成指南。未验证前不产出任何 Binance L&E 相关内容。
