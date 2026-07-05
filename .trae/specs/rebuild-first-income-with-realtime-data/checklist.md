# Checklist - 基于实时数据重建第一桶金路径

## Phase 1: 3 天首笔收入双轨路径

### Publish0x 内容批量发布路径
- [x] `engine/content/publish0x_batch_publisher.py` 文件已创建
- [x] `Publish0xBatchPublisher` 类包含 `generate_article_from_realtime_data()` 方法
- [x] `format_for_publish0x()` 方法正确输出 Markdown + 打赏地址 + tags
- [x] `company/projects/seo-content-generator/articles/publish0x/` 目录已创建
- [x] 已生成 3 篇基于实时数据的 Publish0x 文章
- [x] 每篇文章包含打赏地址 `${ETH_TIPPING_ADDRESS}`
- [x] `company/knowledge/publish0x/registration-guide.md` 用户注册指引已创建
- [x] `company/knowledge/publish0x/batch-upload-checklist.md` 批量发布清单已创建

### Layer3 任务监控路径
- [x] `engine/crypto/layer3_task_monitor.py` 文件已创建
- [x] `Layer3TaskMonitor` 类包含 `fetch_active_tasks()` 方法
- [x] `filter_liquid_rewards()` 方法能筛选即时到账任务
- [x] `generate_task_guide()` 方法能生成用户操作指引
- [x] `company/knowledge/layer3/` 目录已创建
- [x] `company/knowledge/layer3/tasks-2026-06-30.md` 当日任务清单已产出
- [x] `company/knowledge/layer3/registration-guide.md` 用户注册指引已创建

### Binance L&E 用户验证闭环
- [x] `company/knowledge/playbooks/user-binance-verification-guide.md` 已创建
- [x] 指引包含登录 URL 和 L&E 页面路径
- [x] 指引列出需截图确认的 3 个要素（课程列表/奖励金额/是否可点 Start）
- [x] 指引包含 3 种可能结果的应对策略
- [x] `company/human-requests/2026-06-30-binance-le-verification.md` 人工请求文档已创建

## Phase 2: 实时数据验证系统能力

### 实时机会扫描器
- [x] `engine/crypto/realtime_opportunity_scanner.py` 文件已创建
- [x] `RealtimeOpportunityScanner` 类包含 `verify(url)` 方法
- [x] `scan_all()` 方法聚合 5 个平台实时状态
- [x] `generate_report()` 方法产出 markdown 报告
- [x] 报告包含：验证时间戳、数据源 URL、当前状态、预期收益、启动门槛
- [x] `scripts/scan_realtime_opportunities.py` CLI 入口已创建

### 机会雷达升级
- [x] `engine/crypto/opportunity_radar.py` 新增 `verify_realtime()` 方法
- [x] `scan_binance_learn_earn()` 远程抓取失败时标记"需用户验证"
- [x] 未通过实时验证的机会不进入 `auto_enqueue_high_priority()`
- [x] `generate_radar_report()` 报告新增"实时验证状态"列

### CLI 集成
- [x] `py main.py scan-opportunities` 命令可用
- [x] `py main.py layer3-monitor` 命令可用
- [x] `py main.py publish0x-batch` 命令可用
- [x] AutonomousLoop.run_morning 集成实时扫描环节

## Phase 3: 决策记录与手册更新

### 危机决策记录
- [x] `company/decisions/crisis-first-income-2026-06-30.md` 已创建
- [x] 记录危机事实：3 天零收入 + Binance L&E 失效 + 信息滞后
- [x] 记录决策：转向实时数据驱动 + Layer3/Publish0x 双轨
- [x] 记录预期：3 天内产生首笔 $0.01+ 真实收入

### 手册更新
- [x] `company/knowledge/playbooks/first-income-playbook.md` 已修改
- [x] P0-A 路径改为 Layer3 Liquid Rewards
- [x] P0-B 路径改为 Publish0x 内容批量打赏
- [x] P0-C 路径改为 Binance L&E 用户验证闭环
- [x] 旧 P0 Binance L&E 批量答题路径标记为 deprecated

## 核心原则验证

- [x] 所有新推荐机会都有当日可访问的 URL 数据源
- [x] 没有任何推荐基于 AI 记忆（2025 年 8 月前的信息）
- [x] Binance L&E 相关内容全部标注"需用户验证"
- [x] 用户操作指引明确说明每一步需要做什么
- [x] AI 公司能做的事情和用户需要做的事情分工清晰
