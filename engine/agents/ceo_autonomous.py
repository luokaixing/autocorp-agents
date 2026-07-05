"""CEO 自主决策模块 - 让 CEO 具备自主立项/砍项/调整优先级能力。

设计原则：
1. 不修改现有 CEO 类，通过继承扩展。
2. 决策基于规则（CoinGecko 行情 + 历史打赏率），不依赖 LLM。
3. 优雅降级：CoinGecko 拉取失败返回空清单，content-ledger 读取失败用默认值。
"""
from __future__ import annotations

from datetime import datetime
from typing import List, Optional, Tuple

from engine.agents.ceo import CEO
from engine.crypto.market_analyzer import CryptoMarketAnalyzer
from engine.crypto.wallet import WalletManager
from engine.task_queue import TaskQueue


# ROI 评估默认值（历史数据不足时使用）
_DEFAULT_TIP_RATE = 0.05
_DEFAULT_VIEWS = 50
_DEFAULT_TIP_AMOUNT = 0.5

# 自动入队的 ROI 阈值
_ROI_THRESHOLD = 0.5

# 砍项阈值：expected_revenue 低于此值且长期未执行
_KILL_REVENUE_THRESHOLD = 1.0
_KILL_STALE_DAYS = 7


class AutonomousCEO(CEO):
    """CEO 自主决策模块 - 让 CEO 具备自主立项/砍项/调整优先级能力。"""

    # ------------------------------------------------------------------
    # 机会扫描
    # ------------------------------------------------------------------
    def scan_opportunities(self) -> list:
        """扫描市场机会，返回机会清单。

        数据源：
        1. CoinGecko 涨幅榜（用 CryptoMarketAnalyzer.fetch_market_data()）
        2. 已发布文章历史数据（读 content-ledger.yaml 获取浏览量/打赏数据）

        机会判断规则（无需 LLM，纯规则）：
        - 涨幅 >10% 的币 → 写教程蹭热度（type=code, expected_revenue=$3）
        - 涨幅 >5% 的币 → 写简讯（type=research, expected_revenue=$1）
        - 历史文章中浏览量 >100 的关键词 → 复刻续集（type=code, expected_revenue=$5）
        - 当前加密钱包余额为 0 → 高优先级任务：推进 BitDegree Missions
          （type=promote, priority=P0, expected_revenue=$0.5）

        任何数据源异常均优雅降级，返回已能确定的机会清单。
        """
        opportunities: List[dict] = []

        # 1. CoinGecko 涨幅榜
        opportunities.extend(self._scan_coin_pump_opportunities())

        # 2. 历史文章高浏览关键词 → 复刻续集
        opportunities.extend(self._scan_history_view_opportunities())

        # 3. 钱包余额为 0 → 推进 BitDegree Missions
        opportunities.extend(self._scan_wallet_empty_opportunity())

        return opportunities

    def _scan_coin_pump_opportunities(self) -> List[dict]:
        """扫描 CoinGecko 涨幅榜，生成教程/简讯机会。失败返回空清单。"""
        result: List[dict] = []
        try:
            analyzer = CryptoMarketAnalyzer(self.workspace)
            market = analyzer.fetch_market_data()
        except Exception as e:  # noqa: BLE001 - 数据源异常统一兜底
            print(f"[ceo_autonomous] CoinGecko 行情拉取失败，跳过涨幅机会: {e}")
            return result

        if not market or not market.get("coins"):
            return result

        for coin in market["coins"]:
            change = coin.get("price_change_percentage_24h")
            if not isinstance(change, (int, float)):
                continue
            symbol = (coin.get("symbol") or "").upper()
            name = coin.get("name") or symbol
            # 涨幅 >10% → 写教程蹭热度（优先于简讯规则）
            if change > 10:
                result.append(
                    {
                        "title": f"写 {name}({symbol}) 教程蹭热度",
                        "description": (
                            f"币种 {name}({symbol}) 24h 涨幅 {change:.2f}%，"
                            f"写技术教程吸引搜索流量，蹭热度变现。"
                        ),
                        "type": "code",
                        "expected_revenue": 3.0,
                        "priority": "P2",
                        "source_signal": "coin_pump_10",
                        "keyword": f"{name} {symbol}".lower(),
                    }
                )
            # 涨幅 >5% 且 ≤10% → 写简讯
            elif change > 5:
                result.append(
                    {
                        "title": f"写 {name}({symbol}) 涨幅简讯",
                        "description": (
                            f"币种 {name}({symbol}) 24h 涨幅 {change:.2f}%，"
                            f"发简讯抢占时效流量。"
                        ),
                        "type": "research",
                        "expected_revenue": 1.0,
                        "priority": "P2",
                        "source_signal": "coin_pump_5",
                        "keyword": f"{name} {symbol}".lower(),
                    }
                )
        return result

    def _scan_history_view_opportunities(self) -> List[dict]:
        """扫描历史文章浏览量，浏览量 >100 的关键词复刻续集。失败返回空清单。"""
        result: List[dict] = []
        try:
            history = self._load_content_history()
        except Exception as e:  # noqa: BLE001
            print(f"[ceo_autonomous] 历史文章读取失败，跳过续集机会: {e}")
            return result

        # 关键词去重，避免同一关键词重复立项
        seen_keywords: set = set()
        for article in history:
            views = article.get("views") or 0
            if views <= 100:
                continue
            keyword = (article.get("keyword") or "").strip()
            if not keyword or keyword in seen_keywords:
                continue
            seen_keywords.add(keyword)
            result.append(
                {
                    "title": f"复刻热门关键词续集: {keyword}",
                    "description": (
                        f"历史文章关键词「{keyword}」浏览量 {views}，"
                        f"复刻续集延续搜索流量。"
                    ),
                    "type": "code",
                    "expected_revenue": 5.0,
                    "priority": "P2",
                    "source_signal": "history_views",
                    "keyword": keyword,
                }
            )
        return result

    def _scan_wallet_empty_opportunity(self) -> List[dict]:
        """钱包余额为 0 时生成 BitDegree Missions 推进机会。"""
        try:
            if not self._is_wallet_empty():
                return []
        except Exception as e:  # noqa: BLE001
            print(f"[ceo_autonomous] 钱包余额检查失败，跳过 BitDegree 机会: {e}")
            return []

        return [
            {
                "title": "推进 BitDegree Missions 获取空投",
                "description": (
                    "当前加密钱包余额为 0，推进 BitDegree Missions 任务，"
                    "完成链上交互获取空投收益。"
                ),
                "type": "promote",
                "expected_revenue": 0.5,
                "priority": "P0",
                "source_signal": "wallet_empty",
                "keyword": "bitdegree",
            }
        ]

    # ------------------------------------------------------------------
    # ROI 评估
    # ------------------------------------------------------------------
    def evaluate_roi(self, opportunity: dict) -> dict:
        """评估机会的预期收益。

        规则：
        - 历史平均打赏率 × 预期浏览量 × 平均打赏金额
        - 历史数据不足时用默认值：打赏率 5%, 浏览量 50, 平均打赏 $0.5
        - 返回 {expected_revenue: float, confidence: "high"|"medium"|"low", reason: str}
        """
        tip_rate, avg_views, avg_tip, sample_size = self._compute_history_metrics()

        # 历史数据不足时用默认值
        if tip_rate is None:
            tip_rate = _DEFAULT_TIP_RATE
        if avg_views is None:
            avg_views = _DEFAULT_VIEWS
        if avg_tip is None:
            avg_tip = _DEFAULT_TIP_AMOUNT

        expected_revenue = tip_rate * avg_views * avg_tip

        # 置信度基于有效样本数
        if sample_size >= 5:
            confidence = "high"
        elif sample_size >= 1:
            confidence = "medium"
        else:
            confidence = "low"

        reason = (
            f"打赏率={tip_rate:.2%} × 预期浏览量={avg_views:.0f} × "
            f"平均打赏=${avg_tip:.2f} = ${expected_revenue:.4f}"
            f"（样本数 {sample_size}，置信度 {confidence}）"
        )

        return {
            "expected_revenue": round(expected_revenue, 4),
            "confidence": confidence,
            "reason": reason,
        }

    def _compute_history_metrics(self) -> Tuple[Optional[float], Optional[float], Optional[float], int]:
        """从内容账本计算历史打赏率/平均浏览量/平均打赏金额。

        有效样本 = 有浏览量数据（views > 0）的文章。
        数据不足（无有效样本）时全部返回 None，由调用方使用默认值。

        Returns:
            (tip_rate, avg_views, avg_tip, sample_size)
            - tip_rate: 有打赏文章占比 = 有打赏文章数 / 有效样本数
            - avg_views: 有效样本的平均浏览量
            - avg_tip: 有打赏文章的平均打赏金额（无打赏文章时返回 None 用默认值）
            - sample_size: 有效样本数
        """
        history = self._load_content_history()
        if not history:
            return None, None, None, 0

        # 只有有浏览量数据的文章才算有效样本
        with_views = [h for h in history if h.get("views") and h["views"] > 0]
        if not with_views:
            return None, None, None, 0

        sample_size = len(with_views)
        total_views = sum(h["views"] for h in with_views)
        total_tips = sum(h.get("tips_usd", 0.0) for h in with_views)
        tipped = [h for h in with_views if h.get("tips_usd", 0.0) > 0]

        avg_views = total_views / sample_size
        # 有打赏文章才计算平均打赏，否则返回 None 由调用方用默认值
        avg_tip = (total_tips / len(tipped)) if tipped else None
        tip_rate = len(tipped) / sample_size

        return tip_rate, avg_views, avg_tip, sample_size

    # ------------------------------------------------------------------
    # 自动立项
    # ------------------------------------------------------------------
    def auto_initiate_task(self) -> list:
        """扫描机会 + ROI 评估 + 自动入队。

        ROI 阈值：expected_revenue >= $0.5 才入队
        source 字段标记为 "ceo_autonomous"
        返回创建的任务列表
        """
        opportunities = self.scan_opportunities()
        queue = TaskQueue(self.workspace)
        created: List[dict] = []

        for opp in opportunities:
            try:
                roi = self.evaluate_roi(opp)
            except Exception as e:  # noqa: BLE001 - ROI 评估失败跳过该机会
                print(f"[ceo_autonomous] ROI 评估异常，跳过机会「{opp.get('title','')}」: {e}")
                continue

            # ROI 阈值过滤
            if roi["expected_revenue"] < _ROI_THRESHOLD:
                continue

            # 任务 expected_revenue 取预设值与 ROI 评估值的较大者，
            # 既尊重规则预设下限，又允许历史数据向上修正
            preset_rev = opp.get("expected_revenue", 0.0) or 0.0
            final_rev = max(preset_rev, roi["expected_revenue"])

            # SubTask 3.3: DecisionGate 立项门禁检查
            # 命中触发条件（预计成本 > $20 或预计周期 > 3 天）时调用 human_loop 请求人工确认；
            # 用户拒绝或超时 cancel 则跳过该立项，publish decision.gate.product_initiate 消息。
            # DecisionGate 异常不阻塞主流程（try/except 优雅降级，默认放行）。
            expected_cost_usd = final_rev  # 用 expected_revenue 作为保守上限代理值
            duration_map = {"code": 2, "research": 1, "promote": 1}
            expected_duration_days = duration_map.get(opp.get("type", ""), 1)
            gate_approved = True
            gate_reason = ""
            try:
                from engine.decision_gate import DecisionGate
                gate = DecisionGate(self.workspace)
                gate_context = {
                    "expected_cost_usd": expected_cost_usd,
                    "expected_duration_days": expected_duration_days,
                    "title": opp.get("title", ""),
                    "type": opp.get("type", ""),
                }
                check_result = gate.check("product_initiate", gate_context)
                if check_result.get("gate_hit"):
                    gate_reason = check_result.get("reason", "")
                    approved = gate.confirm("product_initiate", gate_context)
                    # True=用户确认 / False=用户拒绝 / None=超时
                    if approved is False:
                        gate_approved = False
                    elif approved is None:
                        # 超时按 timeout_action 处理：cancel 跳过，defer/escalate 放行
                        if check_result.get("timeout_action", "defer") == "cancel":
                            gate_approved = False
            except Exception as gate_err:  # noqa: BLE001 - DecisionGate 失败不阻塞
                print(f"[ceo_autonomous] DecisionGate 检查异常，默认放行: {gate_err}")
                gate_approved = True

            # publish 决策门禁结果到消息池供审计（SubTask 3.6）
            try:
                self.publish(
                    "decision.gate.product_initiate",
                    {
                        "title": opp.get("title", ""),
                        "approved": gate_approved,
                        "rejected": not gate_approved,
                        "reason": gate_reason,
                    },
                )
            except Exception as pub_err:  # noqa: BLE001
                print(f"[ceo_autonomous] publish decision.gate.product_initiate 失败: {pub_err}")

            # 用户拒绝或超时 cancel → 跳过该立项，处理下一个机会
            if not gate_approved:
                continue

            task = queue.add_task(
                title=opp["title"],
                description=opp["description"],
                type=opp["type"],
                priority=opp.get("priority", "P2"),
                expected_revenue=final_rev,
                source="ceo_autonomous",
            )
            created.append(task)
            # 立项决策完成后发布 decision.initiate 消息到共享消息池。
            # self.publish 内部已 try/except 兜底，失败不阻塞主流程。
            try:
                self.publish(
                    "decision.initiate",
                    {
                        "task_id": task.get("id", ""),
                        "title": task.get("title", ""),
                        "expected_revenue": task.get("expected_revenue", 0.0),
                    },
                )
            except Exception as pub_err:  # noqa: BLE001 - publish 失败不阻塞决策
                print(f"[ceo_autonomous] publish decision.initiate 失败: {pub_err}")

        return created

    # ------------------------------------------------------------------
    # 砍低 ROI 任务
    # ------------------------------------------------------------------
    def kill_low_roi_tasks(self) -> list:
        """砍掉低 ROI 且长期未执行的任务。

        规则：
        - status=pending 且 expected_revenue < 1.0 且 created_at 超过 7 天
        - 标记 killed，kill_reason="低 ROI 且长期未执行"
        - 返回被砍任务列表
        """
        queue = TaskQueue(self.workspace)
        pending = queue.list_pending()
        now = datetime.now()
        killed: List[dict] = []

        for task in pending:
            rev = task.get("expected_revenue", 0.0) or 0.0
            if rev >= _KILL_REVENUE_THRESHOLD:
                continue

            created_at = task.get("created_at")
            if not created_at:
                continue
            try:
                created_dt = datetime.fromisoformat(created_at)
            except (ValueError, TypeError):
                # created_at 非法时无法判断时效，跳过避免误杀
                continue

            if (now - created_dt).days < _KILL_STALE_DAYS:
                continue

            queue.kill_task(task.get("id", ""), "低 ROI 且长期未执行")
            # 记录 kill_reason 到返回的任务字典
            task["kill_reason"] = "低 ROI 且长期未执行"
            killed.append(task)
            # 砍项决策完成后发布 decision.kill 消息到共享消息池。
            # self.publish 内部已 try/except 兜底，失败不阻塞主流程。
            try:
                self.publish(
                    "decision.kill",
                    {
                        "task_id": task.get("id", ""),
                        "reason": task.get("kill_reason", "低 ROI 且长期未执行"),
                    },
                )
            except Exception as pub_err:  # noqa: BLE001 - publish 失败不阻塞决策
                print(f"[ceo_autonomous] publish decision.kill 失败: {pub_err}")

        return killed

    # ------------------------------------------------------------------
    # 优先级调整
    # ------------------------------------------------------------------
    def reprioritize(self, channel: str = None, boost: bool = True) -> int:
        """调整任务优先级。

        规则：
        - channel 指定时，调整所有 type=promote 且 description 含 channel 的任务
        - boost=True 升一级（P3→P2→P1→P0，P0 不变），boost=False 降一级
        - channel=None 时调整全部 pending 任务（按 expected_revenue 降序排前 3 升一级）
        - 返回调整的任务数
        """
        queue = TaskQueue(self.workspace)

        if channel is not None:
            # 指定渠道：调整 type=promote 且 description 含 channel 的任务
            def filter_fn(t: dict) -> bool:
                if t.get("type") != "promote":
                    return False
                desc = t.get("description") or ""
                return channel in desc

            count = queue.reprioritize(filter_fn, boost=boost)
        else:
            # channel=None：按 expected_revenue 降序取前 3 个 pending 任务
            pending = queue.list_pending()
            pending.sort(
                key=lambda t: -(t.get("expected_revenue", 0.0) or 0.0)
            )
            top_ids = {t.get("id") for t in pending[:3]}

            def filter_top(t: dict) -> bool:
                return t.get("id") in top_ids

            count = queue.reprioritize(filter_top, boost=boost)

        # 优先级调整完成后发布 decision.reprioritize 消息到共享消息池。
        # self.publish 内部已 try/except 兜底，失败不阻塞主流程。
        try:
            self.publish(
                "decision.reprioritize",
                {
                    "count": count,
                    "channel": channel if channel is not None else "",
                },
            )
        except Exception as pub_err:  # noqa: BLE001 - publish 失败不阻塞决策
            print(f"[ceo_autonomous] publish decision.reprioritize 失败: {pub_err}")

        return count

    # ------------------------------------------------------------------
    # 每日决策主流程
    # ------------------------------------------------------------------
    def run_daily_decision(self) -> dict:
        """每日 CEO 决策主流程。

        1. scan_opportunities + auto_initiate_task
        2. kill_low_roi_tasks
        3. 写决策日志到 company/decisions/ceo-YYYY-MM-DD.md
        返回 {initiated: int, killed: int, reprioritized: int, log_path: str}
        """
        # 1. 扫描机会 + 自动入队
        initiated = self.auto_initiate_task()

        # 2. 砍低 ROI 任务
        killed = self.kill_low_roi_tasks()

        # 3. 调整优先级（默认提升高收益 pending 任务）
        reprioritized = self.reprioritize()

        decisions = {
            "initiated": initiated,
            "killed": killed,
            "reprioritized": reprioritized,
        }
        log_path = self._write_decision_log(decisions)

        return {
            "initiated": len(initiated),
            "killed": len(killed),
            "reprioritized": reprioritized,
            "log_path": log_path,
        }

    # ------------------------------------------------------------------
    # 执行 decision 类型任务
    # ------------------------------------------------------------------
    def execute_task(self, task: dict) -> dict:
        """执行 decision 类型任务（CEO 自身的 execute_task 实现）。

        调用 make_decision(task['description'])，产出决策文档。
        返回 {status: "done"|"failed", result_path: str, error_reason: str}
        """
        try:
            description = task.get("description", "") or ""
            # 将任务描述拆分为选项列表（按换行或中英文分号），便于 make_decision 抉择
            raw_options = description.replace("；", "\n").replace(";", "\n").split("\n")
            options = [o.strip() for o in raw_options if o.strip()]
            if not options:
                options = [description or "（无描述，请 CEO 自行决策）"]

            # 调用父类 make_decision 产出决策文档并落盘
            self.make_decision(options, context="CEO 自主决策任务执行")

            # make_decision 落盘到固定路径：knowledge/decisions/ceo-decision-<root>.md
            result_path = str(
                (
                    self.workspace.decisions_dir
                    / f"ceo-decision-{self.workspace.root_dir.name}.md"
                ).resolve()
            )
            return {
                "status": "done",
                "result_path": result_path,
                "error_reason": "",
            }
        except Exception as e:  # noqa: BLE001 - LLM 调用失败等异常统一兜底
            return {
                "status": "failed",
                "result_path": "",
                "error_reason": str(e),
            }

    # ------------------------------------------------------------------
    # 决策日志
    # ------------------------------------------------------------------
    def _write_decision_log(self, decisions: dict) -> str:
        """写决策日志到 company/decisions/ceo-YYYY-MM-DD.md。

        格式：markdown，含 立项清单/砍项清单/优先级调整/今日复盘 四节。
        返回文件路径。
        """
        today = datetime.now().strftime("%Y-%m-%d")
        log_dir = self.workspace.root_dir / "decisions"
        log_dir.mkdir(parents=True, exist_ok=True)
        log_path = log_dir / f"ceo-{today}.md"

        initiated = decisions.get("initiated", []) or []
        killed = decisions.get("killed", []) or []
        reprioritized = decisions.get("reprioritized", 0) or 0

        lines: List[str] = []
        lines.append(f"# CEO 自主决策日志 {today}")
        lines.append("")
        lines.append(f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}")
        lines.append("")

        # 一、立项清单
        lines.append("## 一、立项清单")
        lines.append("")
        if initiated:
            lines.append("| 任务ID | 标题 | 类型 | 优先级 | 预期收益 |")
            lines.append("|--------|------|------|--------|----------|")
            for t in initiated:
                lines.append(
                    f"| {t.get('id', '')} | {t.get('title', '')} | "
                    f"{t.get('type', '')} | {t.get('priority', '')} | "
                    f"${t.get('expected_revenue', 0):.2f} |"
                )
        else:
            lines.append("> 今日无新增立项。")
        lines.append("")

        # 二、砍项清单
        lines.append("## 二、砍项清单")
        lines.append("")
        if killed:
            lines.append("| 任务ID | 标题 | 预期收益 | 创建时间 | 砍项原因 |")
            lines.append("|--------|------|----------|----------|----------|")
            for t in killed:
                lines.append(
                    f"| {t.get('id', '')} | {t.get('title', '')} | "
                    f"${t.get('expected_revenue', 0):.2f} | "
                    f"{t.get('created_at', '')} | "
                    f"{t.get('kill_reason', '低 ROI 且长期未执行')} |"
                )
        else:
            lines.append("> 今日无砍项。")
        lines.append("")

        # 三、优先级调整
        lines.append("## 三、优先级调整")
        lines.append("")
        lines.append(f"- 本次调整任务数：{reprioritized}")
        lines.append("")

        # 四、今日复盘
        lines.append("## 四、今日复盘")
        lines.append("")
        lines.append(f"- 立项数：{len(initiated)}")
        lines.append(f"- 砍项数：{len(killed)}")
        lines.append(f"- 优先级调整数：{reprioritized}")
        lines.append("")
        if initiated:
            lines.append(
                f"- 抓住 {len(initiated)} 个市场机会自动立项，"
                f"来源标记 ceo_autonomous。"
            )
        if killed:
            lines.append(
                f"- 清理 {len(killed)} 个低 ROI 长期未执行任务，释放队列资源。"
            )
        if reprioritized:
            lines.append(f"- 提升 {reprioritized} 个高收益任务的优先级。")
        if not (initiated or killed or reprioritized):
            lines.append("- 今日无重大决策，市场平稳。")
        lines.append("")

        content = "\n".join(lines)
        log_path.write_text(content, encoding="utf-8")
        return str(log_path.resolve())

    # ==================================================================
    # 私有辅助方法
    # ==================================================================
    def _load_content_history(self) -> List[dict]:
        """读取 content-ledger.yaml，返回每篇文章的 keyword/views/tips_usd/status。

        views 取该文章所有平台中最大的 views_24h（回退 views_7d）。
        tips_usd 取所有平台 tips_received_usd 之和。
        """
        ledger_path = self.workspace.root_dir / "config" / "content-ledger.yaml"
        data = self.workspace.read_yaml(ledger_path)
        if not data or not isinstance(data, dict):
            return []

        articles = data.get("articles") or []
        history: List[dict] = []
        for art in articles:
            keyword = art.get("keyword", "") or ""
            # 取所有平台中最大浏览量
            views = 0
            tips = 0.0
            for plat in (art.get("platforms") or []):
                v = plat.get("views_24h")
                if v is None:
                    v = plat.get("views_7d")
                if isinstance(v, (int, float)) and v > views:
                    views = int(v)
                t = plat.get("tips_received_usd")
                if isinstance(t, (int, float)):
                    tips += t
            history.append(
                {
                    "keyword": keyword,
                    "views": views,
                    "tips_usd": tips,
                    "status": art.get("status", ""),
                }
            )
        return history

    def _is_wallet_empty(self) -> bool:
        """判断加密钱包余额是否为 0。

        - 无钱包注册视为余额 0（触发 BitDegree 推进任务）
        - 任一钱包余额 > 0 即返回 False
        - 所有钱包余额为 0 或查询失败（None）视为余额 0
        """
        wm = WalletManager(self.workspace)
        wallets = wm.list_wallets()
        if not wallets:
            return True

        for w in wallets:
            chain = w.get("chain", "")
            address = w.get("address", "")
            if not chain or not address:
                continue
            try:
                bal_result = wm.check_balance(address, chain)
            except Exception as e:  # noqa: BLE001 - 单个钱包查询失败不阻断整体判断
                print(f"[ceo_autonomous] 钱包 {chain}:{address} 余额查询失败: {e}")
                continue
            bal = bal_result.get("balance")
            if isinstance(bal, (int, float)) and bal > 0:
                return False
        return True

    # ==================================================================
    # CEO 主动掌控模块（2026-06-28 升级）
    # 让 CEO 不再只是晨会被动决策，而是全天主动监控进度、挖掘市场、推送建议
    # ==================================================================

    def generate_dashboard(self) -> dict:
        """生成全局进度看板 - CEO 的"驾驶舱"。

        汇总：
        1. 资产：钱包余额、内容资产（已发布/待发布/打赏收入）
        2. 任务：队列状态（pending/in_progress/done/failed/killed 计数）
        3. 执行：今日已完成任务、失败任务、阻塞任务
        4. 市场：Top3 涨幅币、Top3 热门关键词
        5. 风险：长期 pending 任务、登录态失效、合规告警

        Returns:
            {assets, tasks, execution, market, risks, dashboard_path}
        """
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")

        # 1. 资产概览
        assets = self._collect_assets()

        # 2. 任务队列状态
        tasks = self._collect_task_status()

        # 3. 今日执行情况
        execution = self._collect_execution_status(today)

        # 4. 市场情报（Top3 涨幅）
        market = self._collect_market_snapshot()

        # 5. 风险扫描
        risks = self._scan_risks(today)

        # 写入看板文件
        dashboard_path = self._write_dashboard(
            today, assets, tasks, execution, market, risks
        )

        return {
            "assets": assets,
            "tasks": tasks,
            "execution": execution,
            "market": market,
            "risks": risks,
            "dashboard_path": dashboard_path,
        }

    def propose_actions(self, dashboard: dict = None) -> list:
        """基于看板主动推送 CEO 建议行动清单。

        规则（无需 LLM，纯规则触发）：
        - 有失败任务 → 立即排查
        - 长期 pending 任务（>3 天）→ 砍掉或升优先级
        - 钱包余额为 0 且无新增 → 推进 BitDegree / 空投
        - 高涨幅币（>10%）无对应内容 → 立即立项蹭热度
        - 文章发布 >24h 无打赏 → 推 Twitter/Reddit 引流

        Returns:
            建议行动清单 [{priority, action, reason, expected_revenue}]
        """
        if dashboard is None:
            dashboard = self.generate_dashboard()

        actions: List[dict] = []
        tasks = dashboard.get("tasks", {}) or {}
        execution = dashboard.get("execution", {}) or {}
        assets = dashboard.get("assets", {}) or {}
        market = dashboard.get("market", {}) or {}
        risks = dashboard.get("risks", []) or []

        # 1. 失败任务立即排查
        failed_count = execution.get("failed_today", 0)
        if failed_count > 0:
            actions.append({
                "priority": "P0",
                "action": f"排查 {failed_count} 个今日失败任务",
                "reason": "失败任务阻塞产出，需立即定位原因（API 超时/登录态失效/LLM 错误）",
                "expected_revenue": 0.0,
            })

        # 2. 长期 pending 任务清理
        stale_pending = tasks.get("stale_pending", 0)
        if stale_pending > 0:
            actions.append({
                "priority": "P1",
                "action": f"清理 {stale_pending} 个长期 pending 任务（>3 天未执行）",
                "reason": "占用队列资源，需砍掉或提升优先级",
                "expected_revenue": 0.0,
            })

        # 3. 钱包余额为 0 且无新增
        wallet_balance = assets.get("wallet_balance_eth", 0) or 0
        total_tips = assets.get("total_tips_usd", 0) or 0
        if wallet_balance == 0 and total_tips == 0:
            actions.append({
                "priority": "P0",
                "action": "推进 BitDegree Missions + 空投任务获取首笔收入",
                "reason": "钱包余额为 0，公司无任何现金流，必须立即行动赚钱",
                "expected_revenue": 0.5,
            })

        # 4. 高涨幅币无对应内容
        top_coins = market.get("top_gainers", []) or []
        history_keywords = {h.get("keyword", "").lower() for h in self._load_content_history()}
        for coin in top_coins[:3]:
            symbol = (coin.get("symbol") or "").lower()
            name = (coin.get("name") or "").lower()
            if symbol and symbol not in history_keywords and name not in history_keywords:
                actions.append({
                    "priority": "P1",
                    "action": f"为 {coin.get('name')}({coin.get('symbol')}) 撰写教程蹭热度",
                    "reason": f"24h 涨幅 {coin.get('change', 0):.2f}%，无对应内容资产，错失搜索流量",
                    "expected_revenue": 3.0,
                })
                break  # 只建议一个，避免刷屏

        # 5. 文章发布 >24h 无打赏
        published_no_tips = assets.get("published_no_tips", 0) or 0
        if published_no_tips > 0:
            actions.append({
                "priority": "P2",
                "action": f"为 {published_no_tips} 篇无打赏文章推 Twitter/Reddit 引流",
                "reason": "文章发布后无打赏，需主动引流增加曝光",
                "expected_revenue": 1.0,
            })

        # 6. 风险告警
        for risk in risks[:2]:  # 只取前 2 个高优风险
            actions.append({
                "priority": risk.get("level", "P2"),
                "action": f"处理风险: {risk.get('title', '未知风险')}",
                "reason": risk.get("description", ""),
                "expected_revenue": 0.0,
            })

        return actions

    def run_strategic_review(self) -> dict:
        """执行中段（noon）CEO 战略复盘 - 检查进度偏差。

        在 noon 批次执行后调用，对比晨会计划与实际执行：
        1. 生成看板
        2. 推送建议行动
        3. 写复盘日志到 company/decisions/ceo-review-YYYY-MM-DD.md

        Returns:
            {dashboard_path, actions, review_path}
        """
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")

        # 1. 生成看板
        dashboard = self.generate_dashboard()

        # 2. 推送建议
        actions = self.propose_actions(dashboard)

        # 3. 写复盘日志
        review_path = self._write_strategic_review(today, dashboard, actions)

        return {
            "dashboard_path": dashboard.get("dashboard_path", ""),
            "actions": actions,
            "review_path": review_path,
        }

    # ------------------------------------------------------------------
    # 看板数据采集私有方法
    # ------------------------------------------------------------------
    def _collect_assets(self) -> dict:
        """采集资产数据：钱包余额、内容资产。"""
        # 钱包余额
        wallet_balance_eth = 0.0
        try:
            wm = WalletManager(self.workspace)
            for w in wm.list_wallets():
                address = w.get("address", "")
                chain = w.get("chain", "")
                if not address or not chain:
                    continue
                try:
                    result = wm.check_balance(address, chain)
                    bal = result.get("balance", 0)
                    if isinstance(bal, (int, float)):
                        wallet_balance_eth += bal
                except Exception:  # noqa: BLE001
                    continue
        except Exception as e:  # noqa: BLE001
            print(f"[ceo_autonomous] 钱包余额采集失败: {e}")

        # 内容资产
        published = 0
        pending = 0
        total_tips_usd = 0.0
        published_no_tips = 0
        try:
            history = self._load_content_history()
            for h in history:
                status = h.get("status", "")
                tips = h.get("tips_usd", 0.0) or 0.0
                if status == "published":
                    published += 1
                    total_tips_usd += tips
                    if tips == 0:
                        published_no_tips += 1
                elif status in ("ready_to_publish", "draft", "pending"):
                    pending += 1
        except Exception as e:  # noqa: BLE001
            print(f"[ceo_autonomous] 内容资产采集失败: {e}")

        return {
            "wallet_balance_eth": round(wallet_balance_eth, 6),
            "published_articles": published,
            "pending_articles": pending,
            "total_tips_usd": round(total_tips_usd, 2),
            "published_no_tips": published_no_tips,
        }

    def _collect_task_status(self) -> dict:
        """采集任务队列状态。"""
        try:
            queue = TaskQueue(self.workspace)
            pending = queue.list_pending()
            stale_pending = 0
            now = datetime.now()
            for t in pending:
                created_at = t.get("created_at")
                if not created_at:
                    continue
                try:
                    created_dt = datetime.fromisoformat(created_at)
                    if (now - created_dt).days >= 3:
                        stale_pending += 1
                except (ValueError, TypeError):
                    continue

            all_tasks = queue.list_all() if hasattr(queue, "list_all") else []
            in_progress = sum(1 for t in all_tasks if t.get("status") == "in_progress")
            done = sum(1 for t in all_tasks if t.get("status") == "done")
            failed = sum(1 for t in all_tasks if t.get("status") == "failed")
            killed = sum(1 for t in all_tasks if t.get("status") == "killed")

            return {
                "pending": len(pending),
                "stale_pending": stale_pending,
                "in_progress": in_progress,
                "done": done,
                "failed": failed,
                "killed": killed,
            }
        except Exception as e:  # noqa: BLE001
            print(f"[ceo_autonomous] 任务状态采集失败: {e}")
            return {"pending": 0, "stale_pending": 0, "in_progress": 0, "done": 0, "failed": 0, "killed": 0}

    def _collect_execution_status(self, today: str) -> dict:
        """采集今日执行情况。"""
        try:
            queue = TaskQueue(self.workspace)
            all_tasks = queue.list_all() if hasattr(queue, "list_all") else []
            done_today = 0
            failed_today = 0
            for t in all_tasks:
                updated = (t.get("updated_at") or t.get("completed_at") or "")[:10]
                if updated != today:
                    continue
                status = t.get("status", "")
                if status == "done":
                    done_today += 1
                elif status == "failed":
                    failed_today += 1
            return {"done_today": done_today, "failed_today": failed_today}
        except Exception as e:  # noqa: BLE001
            print(f"[ceo_autonomous] 执行状态采集失败: {e}")
            return {"done_today": 0, "failed_today": 0}

    def _collect_market_snapshot(self) -> dict:
        """采集市场快照：Top3 涨幅币。"""
        try:
            analyzer = CryptoMarketAnalyzer(self.workspace)
            market = analyzer.fetch_market_data()
            coins = market.get("coins", []) if market else []
            # 按涨幅降序排前 3
            gainers = sorted(
                coins,
                key=lambda c: c.get("price_change_percentage_24h", 0) or 0,
                reverse=True,
            )[:3]
            top_gainers = [
                {
                    "name": c.get("name", ""),
                    "symbol": c.get("symbol", ""),
                    "change": c.get("price_change_percentage_24h", 0) or 0,
                    "price": c.get("current_price", 0) or 0,
                }
                for c in gainers
            ]
            return {"top_gainers": top_gainers}
        except Exception as e:  # noqa: BLE001
            print(f"[ceo_autonomous] 市场快照采集失败: {e}")
            return {"top_gainers": []}

    def _scan_risks(self, today: str) -> list:
        """扫描风险：长期 pending、登录态失效、合规告警。"""
        risks: List[dict] = []
        try:
            # 长期 pending 任务
            tasks = self._collect_task_status()
            if tasks.get("stale_pending", 0) > 0:
                risks.append({
                    "level": "P1",
                    "title": f"{tasks['stale_pending']} 个任务长期 pending",
                    "description": "超过 3 天未执行，占用队列资源",
                })

            # 失败任务堆积
            if tasks.get("failed", 0) > 3:
                risks.append({
                    "level": "P0",
                    "title": f"{tasks['failed']} 个失败任务堆积",
                    "description": "失败任务过多，可能存在系统性问题（API/登录态/LLM）",
                })

            # 钱包余额为 0
            assets = self._collect_assets()
            if assets.get("wallet_balance_eth", 0) == 0 and assets.get("total_tips_usd", 0) == 0:
                risks.append({
                    "level": "P0",
                    "title": "公司零现金流",
                    "description": "钱包余额为 0，无任何打赏收入，需立即推进赚钱任务",
                })
        except Exception as e:  # noqa: BLE001
            print(f"[ceo_autonomous] 风险扫描失败: {e}")

        return risks

    def _write_dashboard(
        self, today: str, assets: dict, tasks: dict, execution: dict, market: dict, risks: list
    ) -> str:
        """写 CEO 驾驶舱看板到 company/dashboard/YYYY-MM-DD.md。"""
        dashboard_dir = self.workspace.root_dir / "dashboard"
        dashboard_dir.mkdir(parents=True, exist_ok=True)
        path = dashboard_dir / f"{today}.md"

        lines: List[str] = []
        lines.append(f"# CEO 驾驶舱 - {today}")
        lines.append("")
        lines.append(f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}")
        lines.append("")

        # 资产
        lines.append("## 一、资产概览")
        lines.append("")
        lines.append(f"- 钱包余额: **{assets.get('wallet_balance_eth', 0)} ETH**")
        lines.append(f"- 已发布文章: **{assets.get('published_articles', 0)}** 篇")
        lines.append(f"- 待发布文章: **{assets.get('pending_articles', 0)}** 篇")
        lines.append(f"- 累计打赏: **${assets.get('total_tips_usd', 0)}**")
        lines.append(f"- 无打赏文章: **{assets.get('published_no_tips', 0)}** 篇")
        lines.append("")

        # 任务
        lines.append("## 二、任务队列")
        lines.append("")
        lines.append(f"- Pending: **{tasks.get('pending', 0)}**（其中长期未执行 {tasks.get('stale_pending', 0)}）")
        lines.append(f"- In Progress: {tasks.get('in_progress', 0)}")
        lines.append(f"- Done: {tasks.get('done', 0)}")
        lines.append(f"- Failed: {tasks.get('failed', 0)}")
        lines.append(f"- Killed: {tasks.get('killed', 0)}")
        lines.append("")

        # 执行
        lines.append("## 三、今日执行")
        lines.append("")
        lines.append(f"- 今日完成: **{execution.get('done_today', 0)}**")
        lines.append(f"- 今日失败: **{execution.get('failed_today', 0)}**")
        lines.append("")

        # 市场
        lines.append("## 四、市场快照（Top3 涨幅）")
        lines.append("")
        top_gainers = market.get("top_gainers", []) or []
        if top_gainers:
            lines.append("| 币种 | Symbol | 24h 涨幅 | 价格 |")
            lines.append("|------|--------|---------|------|")
            for c in top_gainers:
                lines.append(
                    f"| {c.get('name', '')} | {c.get('symbol', '')} | "
                    f"{c.get('change', 0):.2f}% | ${c.get('price', 0)} |"
                )
        else:
            lines.append("> 市场数据获取失败")
        lines.append("")

        # 风险
        lines.append("## 五、风险告警")
        lines.append("")
        if risks:
            for r in risks:
                lines.append(f"- **[{r.get('level', 'P2')}]** {r.get('title', '')}: {r.get('description', '')}")
        else:
            lines.append("> 无风险告警")
        lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path.resolve())

    def _write_strategic_review(self, today: str, dashboard: dict, actions: list) -> str:
        """写 CEO 战略复盘到 company/decisions/ceo-review-YYYY-MM-DD.md。"""
        review_dir = self.workspace.root_dir / "decisions"
        review_dir.mkdir(parents=True, exist_ok=True)
        path = review_dir / f"ceo-review-{today}.md"

        lines: List[str] = []
        lines.append(f"# CEO 战略复盘 - {today}")
        lines.append("")
        lines.append(f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}")
        lines.append("")
        lines.append("## 看板摘要")
        lines.append("")
        assets = dashboard.get("assets", {}) or {}
        tasks = dashboard.get("tasks", {}) or {}
        execution = dashboard.get("execution", {}) or {}
        lines.append(f"- 钱包: {assets.get('wallet_balance_eth', 0)} ETH")
        lines.append(f"- 打赏: ${assets.get('total_tips_usd', 0)}")
        lines.append(f"- 文章: 已发 {assets.get('published_articles', 0)} / 待发 {assets.get('pending_articles', 0)}")
        lines.append(f"- 任务: pending {tasks.get('pending', 0)} / 今日完成 {execution.get('done_today', 0)} / 今日失败 {execution.get('failed_today', 0)}")
        lines.append("")

        lines.append("## CEO 建议行动清单")
        lines.append("")
        if actions:
            lines.append("| 优先级 | 行动 | 理由 | 预期收益 |")
            lines.append("|--------|------|------|---------|")
            for a in actions:
                lines.append(
                    f"| {a.get('priority', '')} | {a.get('action', '')} | "
                    f"{a.get('reason', '')} | ${a.get('expected_revenue', 0)} |"
                )
        else:
            lines.append("> 当前无紧急行动建议，公司运行平稳。")
        lines.append("")

        path.write_text("\n".join(lines), encoding="utf-8")
        return str(path.resolve())
