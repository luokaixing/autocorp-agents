"""AutoCorp - AI 虚拟自治公司操作系统"""
from __future__ import annotations

from typing import Optional

import click


@click.group()
def cli():
    """AutoCorp - AI 虚拟自治公司操作系统"""
    pass


@cli.command()
def init():
    """初始化公司工作区（首次使用必执行）"""
    from engine.workspace import WorkspaceManager
    ws = WorkspaceManager()
    ws.initialize()
    click.echo("公司工作区初始化完成。")


@cli.command()
@click.option('--now', is_flag=True, help='立即触发一次会议（调试用）')
def meeting(now):
    """召开产研同步会"""
    from engine.scheduler import Scheduler
    if now:
        click.echo("立即触发产研同步会...")
        Scheduler().trigger_now()
    else:
        click.echo("启动会议调度器...")
        Scheduler().start()


@cli.command(name='run-day')
def run_day():
    """执行一个完整工作日（晨会→执行→复盘）

    优先使用 AutonomousLoop.run_full_day()（3 批次自主运营循环），
    失败时回退到 Orchestrator.run_day()（7 阶段商业闭环）。
    """
    click.echo("启动自主运营循环（完整工作日）...")
    try:
        from engine.autonomous_loop import AutonomousLoop
        loop = AutonomousLoop()
        result = loop.run_full_day()
        morning = result.get("morning", {}) or {}
        noon = result.get("noon", {}) or {}
        evening = result.get("evening", {}) or {}
        batch = noon.get("batch", {}) or {}
        click.echo(
            f"完成。各批次结果："
            f"morning 异常 {len(morning.get('errors', []))} 个; "
            f"noon success={batch.get('success', 0)} failed={batch.get('failed', 0)}; "
            f"evening 异常 {len(evening.get('errors', []))} 个; "
            f"批次异常 {len(result.get('errors', []))} 个"
        )
    except Exception as e:
        # fallback：回退到 Orchestrator
        click.echo(f"AutonomousLoop 失败，回退到 Orchestrator：{e}")
        from engine.orchestrator import Orchestrator
        o = Orchestrator()
        o.run_day()


@cli.command(name='daily-ops')
@click.option('--dry-run', is_flag=True, help='只生成报告不写文件')
def daily_ops(dry_run):
    """AI 公司每日自主运营循环

    自动：检查钱包/审计内容/扫描市场/产出决策清单/写意识流
    """
    click.echo("启动 AI 公司每日自主运营循环...")
    from engine.daily_ops import DailyOps
    ops = DailyOps()
    result = ops.run(dry_run=dry_run)
    if dry_run:
        click.echo(result)
    else:
        click.echo(f"运营日报已生成: {result}")


@cli.command(name='autonomous-run')
@click.option('--morning', is_flag=True, help='只跑晨会循环')
@click.option('--noon', is_flag=True, help='只跑执行批次')
@click.option('--evening', is_flag=True, help='只跑复盘循环')
def autonomous_run(morning, noon, evening):
    """AI 公司自主运营循环

    默认跑完整自主日（morning + noon + evening）。
    """
    from engine.autonomous_loop import AutonomousLoop
    loop = AutonomousLoop()
    if morning:
        result = loop.run_morning()
        click.echo(
            f"晨会循环完成：会议纪要={result.get('meeting_path','')}; "
            f"CEO 决策={result.get('ceo_decisions', {})}; "
            f"PM 扫描={result.get('pm_scan_path','')}; "
            f"决策清单={result.get('decisions_path','')}; "
            f"异常数={len(result.get('errors', []))}"
        )
    elif noon:
        result = loop.run_noon()
        batch = result.get("batch", {}) or {}
        click.echo(
            f"执行批次完成：success={batch.get('success', 0)}, "
            f"failed={batch.get('failed', 0)}, skipped={batch.get('skipped', 0)}; "
            f"异常数={len(result.get('errors', []))}"
        )
    elif evening:
        result = loop.run_evening()
        click.echo(
            f"复盘循环完成：复盘日志={result.get('review_path','')}; "
            f"运营日报={result.get('daily_ops_path','')}; "
            f"今日自主产出={len(result.get('produced_files', []))} 个文件; "
            f"异常数={len(result.get('errors', []))}"
        )
    else:
        result = loop.run_full_day()
        morning_errs = len((result.get("morning") or {}).get("errors", []))
        noon_errs = len((result.get("noon") or {}).get("errors", []))
        evening_errs = len((result.get("evening") or {}).get("errors", []))
        batch_errs = len(result.get("errors", []))
        click.echo(
            f"完整自主日完成：morning 异常 {morning_errs} 个; "
            f"noon 异常 {noon_errs} 个; evening 异常 {evening_errs} 个; "
            f"批次异常 {batch_errs} 个"
        )


@cli.group(name='task-queue')
def task_queue():
    """任务队列管理"""
    pass


@task_queue.command(name='list')
@click.option('--status', default=None, help='按状态筛选')
def task_queue_list(status):
    """列出任务"""
    from engine.task_queue import TaskQueue
    q = TaskQueue()
    tasks = q.list_by_status(status) if status else q.list_all()
    if not tasks:
        click.echo("任务队列为空")
        return
    for t in tasks:
        click.echo(
            f"[{t['id']}] {t['status']} | {t['priority']} | {t['type']} | "
            f"{t.get('title', '')[:50]}"
        )


@task_queue.command(name='add')
@click.option('--title', required=True)
@click.option('--description', required=True)
@click.option('--type', 'task_type', required=True,
              type=click.Choice(['research', 'design', 'code', 'test', 'promote', 'decision']))
@click.option('--assignee', default=None)
@click.option('--priority', default='P2', type=click.Choice(['P0', 'P1', 'P2', 'P3']))
@click.option('--revenue', type=float, default=0.0, help='预期收益 USD')
def task_queue_add(title, description, task_type, assignee, priority, revenue):
    """添加任务"""
    from engine.task_queue import TaskQueue
    q = TaskQueue()
    t = q.add_task(
        title=title, description=description, type=task_type,
        assignee=assignee, priority=priority, expected_revenue=revenue,
    )
    click.echo(f"任务已创建：{t['id']}")


@task_queue.command(name='claim')
@click.argument('role')
def task_queue_claim(role):
    """手动认领任务"""
    from engine.task_queue import TaskQueue
    q = TaskQueue()
    t = q.claim_task(role)
    if t:
        click.echo(f"认领成功：{t['id']} - {t.get('title', '')}")
    else:
        click.echo(f"{role} 无可认领任务")


@cli.command()
def status():
    """查看公司当前状态"""
    from engine.reporter import Reporter
    r = Reporter()
    click.echo(r.status())


@cli.command()
@click.option('--start', is_flag=True, help='启动后台调度')
def schedule(start):
    """管理定时调度"""
    if start:
        click.echo("启动后台调度器（每日 08:00 Asia/Shanghai 触发会议）...")
        from engine.scheduler import Scheduler
        s = Scheduler()
        s.start_blocking()


@cli.command()
@click.option('--now', is_flag=True, help='立即触发战略会')
def strategy(now):
    """季度战略会"""
    if now:
        from engine.agents.ceo import CEO
        from engine.workspace import WorkspaceManager
        ws = WorkspaceManager()
        ceo = CEO(ws)
        result = ceo.quarterly_strategy()
        click.echo(f"战略文档已生成: {result.get('strategy_doc', '')}")
    else:
        click.echo("使用 schedule --start 启动调度器，季度初自动触发战略会")


@cli.group()
def secrets():
    """密钥安全管理"""
    pass


@secrets.command()
@click.argument('key')
@click.argument('value')
def set(key, value):
    """设置密钥"""
    from engine.secrets import SecretsManager
    sm = SecretsManager()
    sm.set(key, value)
    click.echo(f"密钥 {key} 已存储（明文隔离于 .secrets/）")


@secrets.command()
@click.argument('key')
def get(key):
    """获取密钥明文（谨慎使用，会输出到终端）"""
    from engine.secrets import SecretsManager
    sm = SecretsManager()
    val = sm.get(key)
    click.echo(val if val else f"密钥 {key} 不存在")


@secrets.command(name='list')
def list_keys():
    """列出所有密钥名（不显示值）"""
    from engine.secrets import SecretsManager
    sm = SecretsManager()
    for k in sm.list():
        click.echo(k)


@cli.group()
def crypto():
    """加密货币工具"""
    pass


@crypto.command()
@click.option('--focus', '-f', multiple=True,
              type=click.Choice(
                  ['arbitrage', 'airdrop', 'staking', 'onchain_data', 'stablecoin_yield'],
                  case_sensitive=False),
              help='机会类型聚焦（可重复指定）：arbitrage/airdrop/staking/onchain_data/stablecoin_yield')
def analyze(focus):
    """市场分析 - 输出机会/风险/合规边界报告"""
    from engine.crypto.market_analyzer import CryptoMarketAnalyzer
    analyzer = CryptoMarketAnalyzer()
    focus_list = [f.lower() for f in focus] if focus else None
    result = analyzer.run_full_analysis() if focus_list is None else _analyze_with_focus(analyzer, focus_list)
    click.echo(f"分析完成，报告: {result.get('report_path', '')}")
    click.echo(f"机会数量: {result.get('opportunities_count', 0)}")
    click.echo(f"状态: {result.get('status', '')}")


def _analyze_with_focus(analyzer, focus_list):
    """带机会聚焦的分析流程封装（run_full_analysis 不接受参数，单独包装）。"""
    try:
        result = analyzer.analyze(opportunities_focus=focus_list)
        report_path = analyzer.save_report(result['report'])
        return {
            'report_path': report_path,
            'opportunities_count': len(result['opportunities']),
            'status': 'ok',
        }
    except Exception as e:  # noqa: BLE001
        print(f"[crypto] 分析流程异常: {e}")
        return {
            'report_path': '',
            'opportunities_count': 0,
            'status': f'error: {e}',
        }


@crypto.command(name='register-wallet')
@click.option('--chain', required=True,
              type=click.Choice(['bitcoin', 'ethereum', 'tron', 'solana']))
def register_wallet(chain):
    """注册新钱包"""
    from engine.crypto.wallet import WalletManager
    wm = WalletManager()
    result = wm.register_wallet(chain)
    click.echo(f"钱包已创建: {result['chain']} - {result['address']}")
    click.echo("私钥已安全存于 .secrets/，请妥善备份")


@crypto.command(name='list-wallets')
def list_wallets():
    """列出所有钱包"""
    from engine.crypto.wallet import WalletManager
    wm = WalletManager()
    wallets = wm.list_wallets()
    if not wallets:
        click.echo("暂无钱包，使用 crypto register-wallet --chain <chain> 创建")
        return
    for w in wallets:
        click.echo(f"{w['chain']}: {w['address']} (创建于 {w.get('created_at', '')})")


@crypto.command()
@click.option('--address', required=True)
@click.option('--chain', required=True,
              type=click.Choice(['bitcoin', 'ethereum', 'tron', 'solana']))
def balance(address, chain):
    """查询余额"""
    from engine.crypto.wallet import WalletManager
    wm = WalletManager()
    result = wm.check_balance(address, chain)
    if result.get('balance') is None:
        click.echo(f"{chain} {address}: 查询失败 - {result.get('error', '未知错误')}")
    else:
        click.echo(f"{chain} {address}: {result.get('balance')} {result.get('unit', '')}")


@cli.group()
def payee():
    """收款方白名单管理"""
    pass


@payee.command()
@click.argument('payee_address')
@click.argument('category')
def add(payee_address, category):
    """添加白名单"""
    from engine.safety.payment_gate import PaymentGate
    gate = PaymentGate()
    gate.add_to_whitelist(payee_address, category)
    click.echo(f"已添加 {payee_address} 到白名单（类别: {category}）")


@payee.command(name='list')
def list_payees():
    """列出白名单"""
    from engine.safety.payment_gate import PaymentGate
    gate = PaymentGate()
    for item in gate.list_whitelist():
        click.echo(f"{item['payee']} ({item['category']})")


@cli.group()
def payment():
    """PayPal 支付管理"""
    pass


@payment.command()
@click.option('--amount', type=float, required=True)
@click.option('--currency', default='USD')
@click.option('--description', default='')
@click.option('--live', is_flag=True, help='使用正式环境（默认沙箱）')
def create(amount, currency, description, live):
    """创建收款订单"""
    from engine.payments.paypal import PayPalClient, PayPalError
    client = PayPalClient(sandbox=not live)
    if not client.client_id:
        click.echo("错误：未配置 paypal_client_id，请先执行 main.py secrets set paypal_client_id xxx")
        return
    try:
        result = client.create_order(amount, currency, description)
    except PayPalError as e:
        click.echo(f"创建订单失败：{e}")
        return
    click.echo(f"订单已创建: {result.get('order_id', '')}")
    click.echo(f"支付链接: {result.get('approve_url', '')}")


@payment.command()
@click.argument('order_id')
@click.option('--live', is_flag=True, help='使用正式环境')
def check(order_id, live):
    """检查订单状态并入账"""
    from engine.payments.paypal import PayPalClient, PayPalError
    client = PayPalClient(sandbox=not live)
    try:
        result = client.capture_order(order_id)
    except PayPalError as e:
        click.echo(f"捕获订单失败：{e}")
        return
    click.echo(f"状态: {result.get('status', '')}")
    click.echo(f"金额: {result.get('amount', '')} {result.get('currency', '')}")
    click.echo(f"交易号: {result.get('transaction_id', '')}")


# ====================================================================
# 第一桶金相关命令（Task 8：CLI 命令集成）
# 5 个命令分别对应 5 个 SubTask：
#   opportunity-radar  → SubTask 8.1 手动触发机会扫描
#   learn-earn         → SubTask 8.2/8.3 答题指南（单课程 / 批量）
#   income-check       → SubTask 8.4 钱包到账检查
#   airdrop-tracker    → SubTask 8.5 空投进度看板
# 约束：延迟导入、优雅降级（失败仅打印错误，exit code 0）、注释用中文
# ====================================================================


@cli.command(name='opportunity-radar')
def opportunity_radar() -> None:
    """手动触发第一桶金机会扫描

    扫描 4 个零成本赚币渠道（Binance L&E / CMC Earn / Layer3 / DeFi Llama Airdrops），
    评估排序后输出 Top 10 机会清单，并写入
    company/knowledge/opportunities/radar-YYYY-MM-DD.md。
    """
    click.echo("启动第一桶金机会雷达扫描...")
    try:
        import datetime as _dt

        from engine.crypto.opportunity_radar import OpportunityRadar
        from engine.workspace import WorkspaceManager

        ws = WorkspaceManager()
        radar = OpportunityRadar(ws)
        # scan_all_channels 内部已调用 generate_radar_report 与 auto_enqueue_high_priority
        top_10 = radar.scan_all_channels() or []

        click.echo(f"扫描完成，Top 10 机会清单（共 {len(top_10)} 条）：")
        if not top_10:
            click.echo("  （未扫描到机会，可能各数据源页面为 SPA 渲染或网络异常）")
        else:
            for i, opp in enumerate(top_10, 1):
                click.echo(
                    f"  {i}. [{opp.get('priority', 'P2')}] "
                    f"{opp.get('channel', '')} - {opp.get('title', '')} "
                    f"| 速度={opp.get('speed', '')} 确定性={opp.get('certainty', '')} "
                    f"| 收益={opp.get('reward_min', 0)}-{opp.get('reward_max', 0)} USD"
                )

        # 报告文件路径：scan_all_channels 内部已落盘到 radar-YYYY-MM-DD.md
        report_path = (
            radar.opportunities_dir
            / f"radar-{_dt.date.today().isoformat()}.md"
        )
        if report_path.exists():
            click.echo(f"报告文件路径：{report_path}")
        else:
            click.echo(f"报告文件路径：{report_path}（生成失败，文件不存在）")
    except Exception as e:  # noqa: BLE001 - 优雅降级：失败仅打印错误，exit code 0
        click.echo(f"[opportunity-radar] 执行失败：{e}")


@cli.command(name='learn-earn')
@click.option('--course', 'course_url', default=None,
              help='生成指定课程答题指南（课程页面 URL）')
@click.option('--batch', is_flag=True,
              help='批量生成所有 Binance L&E 课程答题指南')
def learn_earn(course_url: Optional[str], batch: bool) -> None:
    """Learn & Earn 答题助手

    生成 Binance / CoinMarketCap Learn & Earn 课程的答题指南，
    帮助快速完成课程获取奖励（单课程 $2-20，1-3 天到账，确定性高）。

    --course <url>：生成指定课程答题指南
    --batch：批量生成所有 Binance L&E 课程答题指南
    """
    if not course_url and not batch:
        click.echo("错误：必须指定 --course <url> 或 --batch 之一")
        return
    if course_url and batch:
        click.echo("错误：--course 与 --batch 不可同时使用")
        return

    try:
        from engine.crypto.learn_earn_assistant import LearnEarnAssistant
        from engine.workspace import WorkspaceManager

        ws = WorkspaceManager()
        assistant = LearnEarnAssistant(ws)

        if batch:
            # SubTask 8.3：批量生成所有 Binance L&E 指南
            click.echo("批量生成所有 Binance L&E 课程答题指南...")
            results = assistant.batch_generate() or []
            ok_count = sum(1 for r in results if r.get("status") == "ok")
            err_count = sum(1 for r in results if r.get("status") == "error")
            skip_count = sum(1 for r in results if r.get("status") == "skipped")
            click.echo(
                f"批量生成完成：共 {len(results)} 门课程，"
                f"成功 {ok_count}，失败 {err_count}，跳过 {skip_count}"
            )
            for r in results:
                status = r.get("status", "")
                name = r.get("course_name", "")
                guide_path = (r.get("result") or {}).get("guide_path", "")
                if status == "ok":
                    click.echo(f"  [成功] {name} -> {guide_path}")
                elif status == "skipped":
                    click.echo(f"  [跳过] {name}（{r.get('error', '')}）")
                else:
                    click.echo(f"  [失败] {name}（{r.get('error', '')}）")
        else:
            # SubTask 8.2：生成指定课程答题指南
            click.echo(f"生成答题指南：{course_url}")
            result = assistant.generate_guide(course_url) or {}
            click.echo(f"课程名：{result.get('course_name', '')}")
            click.echo(f"内容长度：{result.get('content_length', 0)} 字符")
            click.echo(f"题目数量：{result.get('question_count', 0)}")
            click.echo(f"总体置信度：{result.get('confidence_overall', 'low')}")
            click.echo(f"是否降级：{'是' if result.get('degraded') else '否'}")
            click.echo(f"指南文件路径：{result.get('guide_path', '')}")
    except Exception as e:  # noqa: BLE001 - 优雅降级：失败仅打印错误，exit code 0
        click.echo(f"[learn-earn] 执行失败：{e}")


@cli.command(name='income-check')
def income_check() -> None:
    """手动触发钱包到账检查

    调用 Blockscout API 查询公司 ETH 钱包当前余额，与上次记录对比，
    检测到账 delta。到账时自动：入真实账本 + 更新 COO 周打赏 KPI +
    首次到账写 company/decisions/first-income-milestone.md。
    """
    click.echo("启动钱包到账检查...")
    try:
        from engine.crypto.income_monitor import IncomeMonitor
        from engine.workspace import WorkspaceManager

        ws = WorkspaceManager()
        monitor = IncomeMonitor(ws)
        result = monitor.check_inbound() or {}

        current = result.get("current")
        last = result.get("last")
        delta = result.get("delta", 0.0)
        is_first = result.get("is_first_income", False)
        milestone = result.get("milestone_path", "")

        # 当前余额
        if current is None:
            click.echo("当前余额：查询失败")
        else:
            click.echo(f"当前余额：{current} ETH")
        # 上次余额
        if last is None:
            click.echo("上次余额：无记录")
        else:
            click.echo(f"上次余额：{last} ETH")
        click.echo(f"本次到账 delta：{delta} ETH")
        click.echo(f"是否首次到账：{'是' if is_first else '否'}")

        if milestone:
            click.echo(f"里程碑文件：{milestone}")
        if current is None:
            click.echo("（余额查询失败，可能是 Blockscout API 不可达或钱包地址未注册）")
        elif delta > 0:
            click.echo(f"✓ 检测到新到账 {delta} ETH，已入真实账本并更新 COO KPI")
        else:
            click.echo("（无新到账，余额未增加）")
    except Exception as e:  # noqa: BLE001 - 优雅降级：失败仅打印错误，exit code 0
        click.echo(f"[income-check] 执行失败：{e}")


@cli.command(name='airdrop-tracker')
@click.option('--seed', is_flag=True,
              help='初始化 5 个默认空投项目（Monad/Berachain/Layer3/Scroll/Espresso，幂等）')
def airdrop_tracker(seed: bool) -> None:
    """查看空投进度看板

    生成空投任务进度看板表格，写入
    company/knowledge/airdrops/tracker-YYYY-MM-DD.md。

    可选 --seed：初始化 5 个默认项目（Monad/Berachain/Layer3/Scroll/Espresso），
    幂等，已存在的项目会跳过。
    """
    try:
        from pathlib import Path

        from engine.crypto.airdrop_tracker import AirdropTracker
        from engine.workspace import WorkspaceManager

        ws = WorkspaceManager()
        tracker = AirdropTracker(ws)

        if seed:
            click.echo("初始化 5 个默认空投项目...")
            seeded = tracker.seed_initial_projects() or []
            click.echo(f"已初始化/已存在 {len(seeded)} 个项目：")
            for p in seeded:
                click.echo(
                    f"  - {p.get('name', '')} "
                    f"(预期空投: {p.get('expected_airdrop', '')})"
                )

        click.echo("生成空投进度看板...")
        report_path = tracker.generate_tracker_report()
        click.echo(f"看板文件路径：{report_path}")

        # 打印看板表格内容
        try:
            content = Path(report_path).read_text(encoding="utf-8")
            click.echo("")
            click.echo("===== 看板内容预览 =====")
            click.echo(content)
        except Exception as e:  # noqa: BLE001 - 内容读取失败不阻断
            click.echo(f"（看板内容读取失败：{e}）")
    except Exception as e:  # noqa: BLE001 - 优雅降级：失败仅打印错误，exit code 0
        click.echo(f"[airdrop-tracker] 执行失败：{e}")


# ====================================================================
# 实时数据第一桶金 CLI（Task 6：CLI 集成）
# 3 个命令分别对应 3 个 SubTask：
#   scan-opportunities  → SubTask 6.1 触发实时机会扫描
#   layer3-monitor      → SubTask 6.2 触发 Layer3 任务监控
#   publish0x-batch     → SubTask 6.3 批量生成 Publish0x 文章
# 约束：延迟导入、优雅降级（模块导入失败/执行失败仅打印错误，exit code 0）
# ====================================================================


@cli.command(name='scan-opportunities')
def scan_opportunities() -> None:
    """触发实时机会扫描

    调用 RealtimeOpportunityScanner 扫描 5 个平台（Layer3/Galxe/Airdrops.io/
    Publish0x/DefiLlama Yields）当日可访问性，并产出 markdown 报告到
    company/knowledge/opportunities/realtime-scan-YYYY-MM-DD.md。
    """
    click.echo("启动实时机会扫描...")
    try:
        from engine.crypto.realtime_opportunity_scanner import RealtimeOpportunityScanner

        scanner = RealtimeOpportunityScanner()
        # scan_all 内部对每个平台独立 try/except，单个失败不影响其他平台
        click.echo("正在验证 5 个平台可访问性（Layer3/Galxe/Airdrops.io/Publish0x/DefiLlama）...")
        results = scanner.scan_all() or []

        accessible = sum(1 for r in results if r.get("accessible"))
        click.echo(f"扫描完成：共 {len(results)} 个平台，可访问 {accessible} 个")
        for r in results:
            status_label = r.get("status", "")
            platform = r.get("platform", "")
            status_code = r.get("status_code", 0)
            fetch_time = r.get("fetch_time", 0)
            click.echo(
                f"  - {platform}: {status_label} "
                f"(HTTP {status_code}, {fetch_time}s)"
            )

        report_path = scanner.generate_report()
        click.echo(f"报告文件路径：{report_path}")
    except Exception as e:  # noqa: BLE001 - 优雅降级：失败仅打印错误，exit code 0
        click.echo(f"[scan-opportunities] 执行失败：{e}")


@cli.command(name='layer3-monitor')
def layer3_monitor() -> None:
    """触发 Layer3 任务监控

    调用 Layer3TaskMonitor 抓取 app.layer3.xyz/discover 当前任务列表，
    筛选 Liquid Rewards 即时到账任务，并产出当日任务清单到
    company/knowledge/layer3/tasks-YYYY-MM-DD.md。
    """
    click.echo("启动 Layer3 任务监控...")
    try:
        from engine.crypto.layer3_task_monitor import Layer3TaskMonitor

        monitor = Layer3TaskMonitor()
        click.echo("正在抓取 Layer3 discover 页任务列表...")
        tasks = monitor.fetch_active_tasks() or []
        liquid = monitor.filter_liquid_rewards(tasks)
        click.echo(
            f"抓取完成：共 {len(tasks)} 个任务/机制，"
            f"其中 Liquid Rewards 即时到账任务 {len(liquid)} 个"
        )
        for i, t in enumerate(tasks, 1):
            click.echo(
                f"  {i}. [{t.get('category', '')}] {t.get('name', '')} "
                f"| 奖励={t.get('reward_type', '')} "
                f"| 收益={t.get('payout_range', '')} "
                f"| 到账={t.get('payout_speed', '')}"
            )

        report_path = monitor.generate_daily_report()
        click.echo(f"报告文件路径：{report_path}")
    except Exception as e:  # noqa: BLE001 - 优雅降级：失败仅打印错误，exit code 0
        click.echo(f"[layer3-monitor] 执行失败：{e}")


@cli.command(name='publish0x-batch')
def publish0x_batch() -> None:
    """批量生成 Publish0x 文章

    调用 Publish0xBatchPublisher 基于 defi-yield-snapshot-2026-06-30.json +
    realtime-opportunity-scan-2026-06-30.md 实时数据快照生成 3 篇适配
    Publish0x 风格的加密社区向文章（DeFi 收益对比 / Layer3 任务攻略 /
    空投参与指南），落盘到 company/projects/seo-content-generator/articles/publish0x/。
    """
    click.echo("启动 Publish0x 批量文章生成...")
    try:
        from engine.content.publish0x_batch_publisher import Publish0xBatchPublisher

        publisher = Publish0xBatchPublisher()
        topics = ['defi-yield', 'layer3-tasks', 'airdrop-guide']
        click.echo(f"正在生成 {len(topics)} 篇文章（主题：{', '.join(topics)}）...")
        results = publisher.batch_generate(topics) or {}

        ok_count = sum(1 for v in results.values() if not str(v).startswith("ERROR:"))
        err_count = sum(1 for v in results.values() if str(v).startswith("ERROR:"))
        click.echo(f"生成完成：共 {len(results)} 篇，成功 {ok_count}，失败 {err_count}")
        for topic, path in results.items():
            if str(path).startswith("ERROR:"):
                click.echo(f"  [失败] {topic}（{path}）")
            else:
                click.echo(f"  [成功] {topic} -> {path}")
    except Exception as e:  # noqa: BLE001 - 优雅降级：失败仅打印错误，exit code 0
        click.echo(f"[publish0x-batch] 执行失败：{e}")


# ====================================================================
# 服务订单管理（Task 7：服务订单流程 CLI）
# 命令组：order receive / quote / confirm / list / accept / pay / show
# 约束：延迟导入 OrderManager、优雅降级（失败仅打印错误，exit code 0）
# ====================================================================


@cli.group(name='order')
def order():
    """服务订单管理"""
    pass


@order.command(name='receive')
@click.option('--client', required=True, help='客户名称')
@click.option('--requirement', required=True, help='客户需求描述')
@click.option('--channel', default='manual', help='接单渠道（manual/email/twitter）')
@click.option('--contact', default='', help='客户联系方式（邮箱等）')
@click.option('--expected-delivery', default='', help='期望交付日期')
def order_receive(client, requirement, channel, contact, expected_delivery):
    """接收一个外部客户订单"""
    try:
        from engine.service_order import OrderManager
        manager = OrderManager()
        order = manager.receive(
            client_name=client,
            requirement=requirement,
            channel=channel,
            client_contact=contact,
            expected_delivery=expected_delivery,
        )
        click.echo(f"订单已接收：{order['order_id']}")
        click.echo(f"  客户：{order['client_name']}")
        click.echo(f"  渠道：{order['channel']}")
        click.echo(f"  状态：{order['status']}")
    except Exception as e:  # noqa: BLE001 - 优雅降级：失败仅打印错误，exit code 0
        click.echo(f"[order receive] 执行失败：{e}")


@order.command(name='quote')
@click.argument('order_id')
@click.option('--price', type=float, required=True, help='报价金额')
@click.option('--currency', default='USD', help='货币（默认 USD）')
def order_quote(order_id, price, currency):
    """对订单进行报价（> $50 触发人工确认）"""
    try:
        from engine.service_order import OrderManager
        manager = OrderManager()
        order = manager.quote(order_id, price=price, currency=currency)
        if order.get('status') == 'closed' and order.get('rejected'):
            click.echo(f"订单 {order_id} 报价被拒绝，已关闭")
        else:
            click.echo(f"订单 {order_id} 报价完成：{order.get('quoted_price')} {order.get('currency')}")
            click.echo(f"  状态：{order['status']}")
    except Exception as e:  # noqa: BLE001
        click.echo(f"[order quote] 执行失败：{e}")


@order.command(name='confirm')
@click.argument('order_id')
def order_confirm(order_id):
    """客户确认报价，订单流转到 confirmed"""
    try:
        from engine.service_order import OrderManager
        manager = OrderManager()
        order = manager.confirm(order_id)
        click.echo(f"订单 {order_id} 已确认，状态：{order['status']}")
        click.echo(f"  已入队 service 任务（sop_id=WF-SERVICE）")
    except Exception as e:  # noqa: BLE001
        click.echo(f"[order confirm] 执行失败：{e}")


@order.command(name='list')
@click.option('--status', default=None, help='按状态筛选（received/quoted/confirmed/in_progress/delivered/accepted/paid/closed）')
def order_list(status):
    """列出订单"""
    try:
        from engine.service_order import OrderManager
        manager = OrderManager()
        orders = manager.list_orders(status=status)
        if not orders:
            click.echo("无订单" + (f"（状态={status}）" if status else ""))
            return
        click.echo(f"共 {len(orders)} 个订单" + (f"（状态={status}）" if status else "（全部）") + "：")
        for o in orders:
            price_str = (
                f"{o.get('quoted_price', '')} {o.get('currency', '')}"
                if o.get('quoted_price') is not None else "未报价"
            )
            click.echo(
                f"  [{o['order_id']}] {o['status']} | {price_str} | "
                f"{o.get('client_name', '')} | {o.get('requirement', '')[:40]}"
            )
    except Exception as e:  # noqa: BLE001
        click.echo(f"[order list] 执行失败：{e}")


@order.command(name='accept')
@click.argument('order_id')
def order_accept(order_id):
    """客户验收通过，创建 PayPal 收款订单"""
    try:
        from engine.service_order import OrderManager
        manager = OrderManager()
        order = manager.accept(order_id)
        click.echo(f"订单 {order_id} 验收通过，状态：{order['status']}")
        pp_id = order.get('paypal_order_id', '')
        if pp_id:
            click.echo(f"  PayPal 订单已创建：{pp_id}")
        else:
            click.echo(f"  PayPal 订单创建失败或未配置凭证（订单仍已流转到 accepted）")
    except Exception as e:  # noqa: BLE001
        click.echo(f"[order accept] 执行失败：{e}")


@order.command(name='pay')
@click.argument('order_id')
@click.option('--paypal-order-id', default=None, help='PayPal 订单 id（为空时从订单字段读取）')
def order_pay(order_id, paypal_order_id):
    """捕获付款并入账，订单流转到 paid"""
    try:
        from engine.service_order import OrderManager
        manager = OrderManager()
        order = manager.pay(order_id, paypal_order_id=paypal_order_id)
        click.echo(f"订单 {order_id} 收款完成，状态：{order['status']}")
        click.echo(f"  金额：{order.get('quoted_price', '')} {order.get('currency', '')}")
    except Exception as e:  # noqa: BLE001
        click.echo(f"[order pay] 执行失败：{e}")


@order.command(name='show')
@click.argument('order_id')
def order_show(order_id):
    """查看订单详情"""
    try:
        from engine.service_order import OrderManager
        manager = OrderManager()
        order = manager.get_order(order_id)
        if order is None:
            click.echo(f"订单 {order_id} 不存在")
            return
        click.echo(f"订单 ID：{order.get('order_id', '')}")
        click.echo(f"  客户：{order.get('client_name', '')}")
        click.echo(f"  联系方式：{order.get('client_contact', '')}")
        click.echo(f"  渠道：{order.get('channel', '')}")
        click.echo(f"  需求：{order.get('requirement', '')}")
        click.echo(f"  SOP：{order.get('sop_id', '')}")
        click.echo(f"  报价：{order.get('quoted_price', '')} {order.get('currency', '')}")
        click.echo(f"  期望交付：{order.get('expected_delivery', '')}")
        click.echo(f"  状态：{order.get('status', '')}")
        click.echo(f"  PayPal 订单：{order.get('paypal_order_id', '')}")
        click.echo(f"  创建时间：{order.get('created_at', '')}")
        click.echo(f"  更新时间：{order.get('updated_at', '')}")
        events = order.get('events', []) or []
        if events:
            click.echo(f"  事件流转（{len(events)} 条）：")
            for ev in events:
                click.echo(
                    f"    - {ev.get('timestamp', '')} "
                    f"{ev.get('from_status', '')} → {ev.get('to_status', '')} "
                    f"({ev.get('actor', '')}): {ev.get('note', '')}"
                )
    except Exception as e:  # noqa: BLE001
        click.echo(f"[order show] 执行失败：{e}")


# ====================================================================
# SOP 查询（Task 9.1：SOP CLI）
# 命令组：sop list / sop show
# 约束：延迟导入 SOPLoader、优雅降级（失败仅打印错误，exit code 0）
# ====================================================================


@cli.group(name='sop')
def sop():
    """SOP 查询"""
    pass


@sop.command(name='list')
def sop_list():
    """列出所有 SOP（id / name / owner_role / trigger）"""
    try:
        from engine.sop_loader import SOPLoader
        loader = SOPLoader()
        all_sops = loader.list_all()
        if not all_sops:
            click.echo("无 SOP")
            return
        click.echo(f"共 {len(all_sops)} 个 SOP：")
        for s in all_sops:
            click.echo(
                f"  [{s.get('id', '')}] {s.get('name', '')} | "
                f"owner={s.get('owner_role', '')} | trigger={s.get('trigger', '')}"
            )
    except Exception as e:  # noqa: BLE001 - 优雅降级：失败仅打印错误，exit code 0
        click.echo(f"[sop list] 执行失败：{e}")


@sop.command(name='show')
@click.argument('sop_id')
def sop_show(sop_id):
    """查看指定 SOP 的完整详情（frontmatter + 正文）"""
    try:
        from engine.sop_loader import SOPLoader
        loader = SOPLoader()
        sop = loader.load(sop_id)
        if sop is None:
            click.echo(f"SOP {sop_id} 不存在")
            return
        click.echo(f"id: {sop.get('id', '')}")
        click.echo(f"name: {sop.get('name', '')}")
        click.echo(f"trigger: {sop.get('trigger', '')}")
        click.echo(f"owner_role: {sop.get('owner_role', '')}")
        click.echo(f"sla_minutes: {sop.get('sla_minutes', 0)}")
        click.echo(f"fallback: {sop.get('fallback', '')}")
        inputs = sop.get('inputs', []) or []
        outputs = sop.get('outputs', []) or []
        criteria = sop.get('acceptance_criteria', []) or []
        click.echo(f"inputs ({len(inputs)}):")
        for item in inputs:
            click.echo(f"  - {item}")
        click.echo(f"outputs ({len(outputs)}):")
        for item in outputs:
            click.echo(f"  - {item}")
        click.echo(f"acceptance_criteria ({len(criteria)}):")
        for item in criteria:
            click.echo(f"  - {item}")
        click.echo(f"file_path: {sop.get('_path', '')}")
        click.echo("---- body ----")
        click.echo(sop.get('actions', '') or '')
    except Exception as e:  # noqa: BLE001
        click.echo(f"[sop show] 执行失败：{e}")


# ====================================================================
# Phase Chain 编排（Task 9.2：Phase CLI）
# 命令组：phase list / phase run
# 约束：延迟导入 PhaseChain / PHASE_METADATA、优雅降级（exit code 0）
# ====================================================================


@cli.group(name='phase')
def phase():
    """Phase Chain 编排"""
    pass


@phase.command(name='list')
def phase_list():
    """列出 7 个标准 Phase 元数据"""
    try:
        from engine.phase_chain import PHASE_METADATA
        if not PHASE_METADATA:
            click.echo("无 Phase 元数据")
            return
        click.echo(f"共 {len(PHASE_METADATA)} 个 Phase：")
        for name, meta in PHASE_METADATA.items():
            participants = meta.get('participants', []) or []
            click.echo(
                f"  [{name}] participants={','.join(participants)} | "
                f"max_duration_minutes={meta.get('max_duration_minutes', 0)} | "
                f"fallback={meta.get('fallback', '')}"
            )
    except Exception as e:  # noqa: BLE001
        click.echo(f"[phase list] 执行失败：{e}")


@phase.command(name='run')
@click.argument('phase_name')
def phase_run(phase_name):
    """执行单个 Phase（如 Phase-Morning）"""
    try:
        from engine.phase_chain import PhaseChain, PHASE_METADATA
        if phase_name not in PHASE_METADATA:
            click.echo(
                f"未知 Phase: {phase_name}（可选：{', '.join(PHASE_METADATA.keys())}）"
            )
            return
        chain = PhaseChain()
        result = chain.run_phase(phase_name)
        click.echo(f"Phase: {result.get('phase', phase_name)}")
        click.echo(f"状态: {result.get('status', '')}")
        errors = result.get('errors', []) or []
        if errors:
            click.echo(f"错误/警告（{len(errors)} 条）：")
            for err in errors:
                click.echo(f"  - {err}")
        else:
            click.echo("无错误/警告")
    except Exception as e:  # noqa: BLE001
        click.echo(f"[phase run] 执行失败：{e}")


# ====================================================================
# 健康监控（Task 9.3：Health CLI）
# 命令：health
# 约束：延迟导入 HealthMonitor、优雅降级（exit code 0）
# ====================================================================


@cli.command(name='health')
def health():
    """执行每日健康检查并生成报告"""
    try:
        from engine.health_monitor import HealthMonitor
        hm = HealthMonitor()
        result = hm.run_daily_check()
        click.echo(f"健康检查完成，状态：{result.get('status', 'unknown')}")
        click.echo(f"报告路径：{result.get('report_path', '')}")
        red = result.get('red_count', 0)
        yellow = result.get('yellow_count', 0)
        green = result.get('green_count', 0)
        click.echo(f"统计：red={red} yellow={yellow} green={green}")
        alerts = result.get('alerts', []) or []
        if alerts:
            click.echo(f"告警（{len(alerts)} 条）：")
            for a in alerts:
                click.echo(f"  - {a}")
    except Exception as e:  # noqa: BLE001
        click.echo(f"[health] 执行失败：{e}")


# ====================================================================
# 消息池查询（Task 9.4：Message CLI）
# 命令组：message list [--topic <topic>] [--date <date>]
# 约束：延迟导入 MessagePool、优雅降级（exit code 0）
# ====================================================================


@cli.group(name='message')
def message():
    """消息池查询"""
    pass


@message.command(name='list')
@click.option('--topic', default=None, help='按 topic 完全匹配筛选')
@click.option('--date', default=None, help='按日期筛选（YYYY-MM-DD）')
def message_list(topic, date):
    """列出消息（--date 优先；其次 --topic；默认今日全部）"""
    try:
        from engine.message_pool import MessagePool
        mp = MessagePool()
        if date:
            msgs = mp.list_by_date(date_str=date)
            scope = f"date={date}"
        elif topic:
            msgs = mp.list_by_topic(topic=topic)
            scope = f"topic={topic}"
        else:
            msgs = mp.list_all_today()
            scope = "today"
        if not msgs:
            click.echo(f"无消息（{scope}）")
            return
        click.echo(f"共 {len(msgs)} 条消息（{scope}）：")
        for m in msgs:
            created_at = m.get('created_at', '')
            from_role = m.get('from_role', '') or ''
            to_role = m.get('to_role', '') or 'ALL'
            msg_topic = m.get('topic', '')
            payload = m.get('payload', '')
            payload_str = str(payload)[:200]
            click.echo(
                f"  [{created_at}] {from_role} → {to_role} | {msg_topic} | {payload_str}"
            )
    except Exception as e:  # noqa: BLE001
        click.echo(f"[message list] 执行失败：{e}")


if __name__ == '__main__':
    cli()
