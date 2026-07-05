# Tasks - 基于实时数据重建第一桶金路径

按依赖顺序排列。Phase 1 是立即可执行的 3 天首笔收入路径，Phase 2 是系统能力建设，Phase 3 是手册与决策记录。

## Phase 1: 3 天首笔收入双轨路径（立即执行，最高优先级）

- [x] Task 1: Publish0x 内容批量发布路径
  - [x] SubTask 1.1: 创建 `engine/content/publish0x_batch_publisher.py`，包含 `Publish0xBatchPublisher` 类
  - [x] SubTask 1.2: 实现 `generate_article_from_realtime_data(topic)` 方法 —— 基于 `defi-yield-snapshot-2026-06-30.json` 生成文章
  - [x] SubTask 1.3: 实现 `format_for_publish0x(article)` 方法 —— 适配 Publish0x 格式（Markdown + 打赏地址 + tags）
  - [x] SubTask 1.4: 创建 `company/projects/seo-content-generator/articles/publish0x/` 目录
  - [x] SubTask 1.5: 生成 3 篇基于实时数据的 Publish0x 文章（主题：DeFi 收益对比 / Layer3 任务攻略 / 空投参与指南）
  - [x] SubTask 1.6: 创建 `company/knowledge/publish0x/registration-guide.md` 用户注册指引
  - [x] SubTask 1.7: 创建 `company/knowledge/publish0x/batch-upload-checklist.md` 批量发布清单

- [x] Task 2: Layer3 任务监控与指引路径
  - [x] SubTask 2.1: 创建 `engine/crypto/layer3_task_monitor.py`，包含 `Layer3TaskMonitor` 类
  - [x] SubTask 2.2: 实现 `fetch_active_tasks()` 方法 —— WebFetch `https://app.layer3.xyz/discover` 解析当前任务
  - [x] SubTask 2.3: 实现 `filter_liquid_rewards(tasks)` 方法 —— 筛选即时到账任务
  - [x] SubTask 2.4: 实现 `generate_task_guide(task)` 方法 —— 生成用户操作指引
  - [x] SubTask 2.5: 创建 `company/knowledge/layer3/` 目录
  - [x] SubTask 2.6: 产出当日任务清单 `company/knowledge/layer3/tasks-2026-06-30.md`
  - [x] SubTask 2.7: 创建 `company/knowledge/layer3/registration-guide.md` 用户注册指引

- [x] Task 3: Binance L&E 用户验证闭环
  - [x] SubTask 3.1: 创建 `company/knowledge/playbooks/user-binance-verification-guide.md`
  - [x] SubTask 3.2: 指引包含：登录 URL、L&E 页面路径、需截图确认的 3 个要素
  - [x] SubTask 3.3: 指引包含：3 种可能结果的应对策略（有课程/无课程/地区限制）
  - [x] SubTask 3.4: 创建 `company/human-requests/2026-06-30-binance-le-verification.md` 人工请求文档

## Phase 2: 实时数据验证系统能力（Phase 1 完成后）

- [x] Task 4: 实时机会扫描器
  - [x] SubTask 4.1: 创建 `engine/crypto/realtime_opportunity_scanner.py`，包含 `RealtimeOpportunityScanner` 类
  - [x] SubTask 4.2: 实现 `verify(url)` 方法 —— WebFetch 验证 URL 当日可访问性
  - [x] SubTask 4.3: 实现 `scan_all()` 方法 —— 聚合 Layer3/Galxe/Airdrops.io/Publish0x/DefiLlama 实时状态
  - [x] SubTask 4.4: 实现 `generate_report()` 方法 —— 产出 markdown 报告到 `company/knowledge/opportunities/realtime-scan-YYYY-MM-DD.md`
  - [x] SubTask 4.5: 报告必须包含：验证时间戳、数据源 URL、当前状态、预期收益、启动门槛

- [x] Task 5: 机会雷达实时验证层升级
  - [x] SubTask 5.1: 修改 `engine/crypto/opportunity_radar.py` 新增 `verify_realtime(opportunity)` 方法
  - [x] SubTask 5.2: `scan_binance_learn_earn()` 方法增加"远程抓取失败时标记为'需用户验证'"逻辑
  - [x] SubTask 5.3: 未通过实时验证的机会不进入 `auto_enqueue_high_priority()`
  - [x] SubTask 5.4: `generate_radar_report()` 报告新增"实时验证状态"列

- [x] Task 6: CLI 集成
  - [x] SubTask 6.1: 新增 `py main.py scan-opportunities` 命令 —— 触发实时机会扫描
  - [x] SubTask 6.2: 新增 `py main.py layer3-monitor` 命令 —— 触发 Layer3 任务监控
  - [x] SubTask 6.3: 新增 `py main.py publish0x-batch` 命令 —— 批量生成 Publish0x 文章
  - [x] SubTask 6.4: 集成到 AutonomousLoop.run_morning 晨会循环

## Phase 3: 决策记录与手册更新（Phase 1+2 完成后）

- [ ] Task 7: 危机决策记录
  - [x] SubTask 7.1: 创建 `company/decisions/crisis-first-income-2026-06-30.md`
  - [x] SubTask 7.2: 记录危机事实：3 天零收入 + Binance L&E 失效 + 信息滞后问题
  - [x] SubTask 7.3: 记录决策：转向实时数据驱动 + Layer3/Publish0x 双轨
  - [x] SubTask 7.4: 记录预期：3 天内 Layer3 或 Publish0x 产生首笔 $0.01+ 真实收入

- [x] Task 8: 第一桶金执行手册重写
  - [x] SubTask 8.1: 修改 `company/knowledge/playbooks/first-income-playbook.md`
  - [x] SubTask 8.2: P0-A 路径改为 Layer3 Liquid Rewards（即时到账）
  - [x] SubTask 8.3: P0-B 路径改为 Publish0x 内容批量打赏
  - [x] SubTask 8.4: P0-C 路径改为 Binance L&E 用户验证闭环
  - [x] SubTask 8.5: 旧 P0 Binance L&E 批量答题路径标记为 deprecated

---

# Task Dependencies

- Task 2 依赖 Task 1（双轨并行启动，但 Publish0x 内容可复用 Layer3 任务数据）
- Task 3 独立（用户验证闭环不依赖系统实现）
- Task 4 依赖 Task 1+2（扫描器复用 Layer3 monitor 和 Publish0x publisher 的逻辑）
- Task 5 依赖 Task 4（机会雷达升级需要扫描器组件）
- Task 6 依赖 Task 4+5（CLI 集成需要后端能力就绪）
- Task 7 独立（决策记录可立即写）
- Task 8 依赖 Task 1+2+3（手册汇总所有路径）

## Parallelizable Work

- Task 1（Publish0x）‖ Task 2（Layer3）‖ Task 3（Binance 验证）可并行
- Task 7（决策记录）可立即并行启动
- Task 4+5+6 串行依赖（扫描器 → 雷达升级 → CLI）
- Task 8 依赖前面所有路径完成
