"""COO 智能体 - 首席运营官

对产品推广和收入负责，从渠道、定价、追踪指标、时间线四个维度制定增长计划。
"""
from __future__ import annotations

from typing import Any, Dict

from engine.agents.base import BaseAgent
from engine.workspace import WorkspaceManager
from engine.ledger import Ledger
from engine.llm_client import LLMClient


class COO(BaseAgent):
    """首席运营官：负责推广运营、渠道策略、定价、收入回款。"""

    def __init__(self, workspace: WorkspaceManager, llm_client: LLMClient = None):
        super().__init__("coo", workspace, llm_client)
        # 运营决策需要参考账本预算
        self.ledger = Ledger(workspace)

    def create_marketing_plan(self, product_info: dict) -> dict:
        """制定推广计划，返回 {channels, pricing, metrics, timeline, raw_response}。"""
        balance = self.ledger.balance()
        user_message = (
            f"请为以下产品制定 0-90 天推广计划，必须包含渠道、定价、追踪指标、时间线。\n"
            f"可用营销预算上限：{balance * 0.3}（账本余额的 30%）。\n"
            f"产品信息：\n{product_info}"
        )
        raw = self.call_llm(user_message, context="任务：推广运营与渠道策略")
        return {
            "channels": None,
            "pricing": None,
            "metrics": None,
            "timeline": None,
            "raw_response": raw,
        }

    def track_revenue(self) -> dict:
        """追踪收入，从 ledger 读取并交 LLM 给出运营建议。"""
        audit = self.ledger.audit()
        user_message = (
            f"请基于以下账本数据做收入追踪分析，给出增长建议。\n"
            f"账本摘要：{audit}"
        )
        raw = self.call_llm(user_message, context="任务：收入回款与用户跟踪")
        # 持久化为运营报告
        self.save_output(
            f"# 收入追踪报告\n\n## 账本摘要\n{audit}\n\n## 运营建议\n{raw}",
            category="report",
            filename="coo-revenue-tracking.md",
        )
        return {
            "audit": audit,
            "advice": raw,
            "raw_response": raw,
        }

    # ------------------------------------------------------------------
    # SubTask 5.7: 竞品社交监控（Agent-Reach 集成）
    # ------------------------------------------------------------------
    def monitor_competitors(self, competitors: list = None) -> dict:
        """监控竞品社交互动数据，作为引流效果对照

        通过 engine.social_reach.SocialReach 抓取竞品 Twitter 账号最近帖子，
        计算 avg_engagement 作为竞品互动基线，供 COO 评估自家引流效果。

        参数:
            competitors: 竞品 Twitter 账号列表，如 ["@aave", "@CompoundFinance"]。
                默认 ["@aave", "@CompoundFinance", "@LidoFinance"]。

        返回:
            ``{competitor: {"posts": [...], "avg_engagement": float}}`` 字典。
            posts 为标准化帖子列表（含 engagement.likes 等字段）；抓取失败时
            posts 为空列表，avg_engagement 为 0。
        """
        from engine.social_reach import SocialReach

        competitors = competitors or [
            "@aave", "@CompoundFinance", "@LidoFinance"
        ]
        reach = SocialReach()
        result: dict = {}
        for c in competitors:
            try:
                posts = reach.fetch_competitor("twitter", c, limit=10)
                total_likes = sum(
                    p.get("engagement", {}).get("likes", 0) for p in posts
                )
                avg_eng = total_likes / max(len(posts), 1)
                result[c] = {
                    "posts": posts,
                    "avg_engagement": round(avg_eng, 2),
                }
                print(
                    f"[coo] 监控 {c} 成功：{len(posts)} 条，"
                    f"平均互动 {avg_eng:.2f}"
                )
            except Exception as e:  # noqa: BLE001 - 单竞品失败不阻断
                print(f"[coo] 监控 {c} 失败：{e}")
                result[c] = {"posts": [], "avg_engagement": 0}
        return result

    # ------------------------------------------------------------------
    # 渠道选择（基于 channels.yaml 清单筛选引流渠道）
    # ------------------------------------------------------------------
    def select_channels(self, category: str = None, audience: str = None, cost: str = None, limit: int = 10) -> list:
        """按条件筛选引流渠道。

        从 company/knowledge/marketing/channels.yaml 读取渠道清单，
        支持按分类/受众/成本组合过滤，并按 priority 升序返回 Top N。
        文件不存在或为空时降级返回默认渠道（Twitter/Reddit/Paragraph）。

        参数:
            category: 按分类过滤（free/paid/domestic/foreign/social/forum/directory/aggregator）。
            audience: 按受众过滤（tech/developer/crypto/ai/indie_hacker/early_adopter/general）。
            cost: 按成本过滤（free/freemium/paid）。
            limit: 返回数量上限。

        返回:
            list[dict]: 按 priority 升序排序的渠道列表，每项含
                name/url/category/audience/cost/priority/description。
        """
        channels_path = self.workspace.knowledge_dir / "marketing" / "channels.yaml"
        data = self.workspace.read_yaml(channels_path)
        if not data:
            print("[coo] channels.yaml 不存在或为空，返回默认渠道")
            return self._default_channels(limit)

        channels = data.get("channels", []) or []
        # 组合过滤：分类/受众/成本同时满足
        if category:
            channels = [c for c in channels if category in (c.get("category") or [])]
        if audience:
            channels = [c for c in channels if audience in (c.get("audience") or [])]
        if cost:
            channels = [c for c in channels if c.get("cost") == cost]

        # 按 priority 升序（1 为最高优先），同级保持原顺序
        channels.sort(key=lambda c: c.get("priority", 5))
        return channels[:limit]

    @staticmethod
    def _default_channels(limit: int = 10) -> list:
        """channels.yaml 缺失时的默认渠道兜底（Twitter/Reddit/Paragraph）。"""
        defaults = [
            {
                "name": "Twitter / X",
                "url": "https://twitter.com",
                "category": ["free", "foreign", "social"],
                "audience": ["tech", "early_adopter"],
                "cost": "free",
                "priority": 1,
                "description": "全球实时短文社交平台，技术/AI 话题传播主阵地",
            },
            {
                "name": "Reddit",
                "url": "https://www.reddit.com",
                "category": ["free", "foreign", "forum", "social"],
                "audience": ["tech", "developer", "indie_hacker"],
                "cost": "free",
                "priority": 1,
                "description": "海外最大社区论坛，按子版块精准触达开发者/创业者",
            },
            {
                "name": "Paragraph",
                "url": "https://paragraph.xyz",
                "category": ["free", "foreign", "social"],
                "audience": ["crypto", "tech"],
                "cost": "freemium",
                "priority": 2,
                "description": "Web3 新闻订阅平台，支持钱包订阅，适合 Newsletter 引流",
            },
        ]
        return defaults[:limit]

    # ------------------------------------------------------------------
    # 推广物料产出（execute_task 调用，与 create_marketing_plan 不同）
    # ------------------------------------------------------------------
    def execute_promotion(self, task: dict) -> str:
        """产出 3 个推广物料（Twitter / Reddit / Telegram）。

        读取任务关联文章与 content-ledger.yaml 中已发布文章 URL，构造推广文案。
        LLM 调用失败时降级为模板物料（含固定 hashtag + URL 占位）。

        Returns:
            markdown 推广物料文本。
        """
        from datetime import datetime
        from engine.secrets import SecretsManager

        # 从密钥管理器读取打赏地址（不再硬编码）
        try:
            _secrets = SecretsManager()
            TIPPING_ADDRESS = _secrets.get("tipping_address_eth") or "[配置后显示]"
        except Exception:
            TIPPING_ADDRESS = "[配置后显示]"

        # 1. 读取任务关联文章
        article_path = task.get("result_path", "") if isinstance(task, dict) else ""
        article_content = self.workspace.read_text(article_path) if article_path else ""
        if not article_content:
            # 兜底：取 articles 目录下最新文章
            articles_dir = self.workspace.projects_dir / "seo-content-generator" / "articles"
            if articles_dir.exists():
                md_files = [p for p in articles_dir.glob("*.md")]
                if md_files:
                    latest = max(md_files, key=lambda p: p.stat().st_mtime)
                    article_path = str(latest)
                    article_content = self.workspace.read_text(latest)

        # 2. 读取 content-ledger.yaml 获取已发布文章 URL
        article_url = ""
        try:
            ledger_data = self.workspace.read_yaml(
                self.workspace.config_dir / "content-ledger.yaml"
            ) or {}
            for art in ledger_data.get("articles", []) or []:
                for p in art.get("platforms", []) or []:
                    url = p.get("url", "")
                    if url:
                        article_url = url
                        break
                if article_url:
                    break
        except Exception as e:  # noqa: BLE001
            print(f"[coo] 读取 content-ledger 失败：{e}")

        title = task.get("title", "新文章发布") if isinstance(task, dict) else "新文章发布"
        url = article_url or "[文章链接待补]"
        # 从文章提取首行标题（若有）
        article_title = title
        if article_content:
            for line in article_content.splitlines():
                if line.strip().startswith("# "):
                    article_title = line.strip().lstrip("# ").strip() or article_title
                    break

        # SubTask 3.4: DecisionGate 对外发布门禁检查
        # 命中触发条件（首次发布到新渠道或含敏感话题）时调用 human_loop 请求人工确认；
        # 用户拒绝或超时 cancel 则跳过发布，返回占位文本并 publish decision.gate.external_publish。
        # DecisionGate 异常不阻塞主流程（try/except 优雅降级，默认放行）。
        gate_approved = True
        gate_reason = ""
        try:
            from engine.decision_gate import DecisionGate
            # 检测首次发布到新渠道：marketing 目录下无历史 promo 文件视为首次
            marketing_dir = self.workspace.knowledge_dir / "marketing"
            promo_files = (
                list(marketing_dir.glob("promo-*.md"))
                if marketing_dir.exists() else []
            )
            first_time_channel = len(promo_files) == 0
            # 检测敏感话题：标题命中政治/监管/争议等关键词
            sensitive_keywords = [
                "政治", "politics", "监管", "regulation", "争议", "controversy",
                "选举", "election", "政策", "policy", "政府", "government",
            ]
            title_lower = (article_title or "").lower()
            sensitive_topic = any(
                kw.lower() in title_lower for kw in sensitive_keywords
            )

            gate = DecisionGate(self.workspace)
            gate_context = {
                "first_time_channel": first_time_channel,
                "sensitive_topic": sensitive_topic,
                "title": article_title,
                "task_id": task.get("id", "") if isinstance(task, dict) else "",
            }
            check_result = gate.check("external_publish", gate_context)
            if check_result.get("gate_hit"):
                gate_reason = check_result.get("reason", "")
                approved = gate.confirm("external_publish", gate_context)
                # True=用户确认 / False=用户拒绝 / None=超时
                if approved is False:
                    gate_approved = False
                elif approved is None:
                    # 超时按 timeout_action 处理：cancel 跳过，defer/escalate 放行
                    if check_result.get("timeout_action", "defer") == "cancel":
                        gate_approved = False
        except Exception as gate_err:  # noqa: BLE001 - DecisionGate 失败不阻塞
            print(f"[coo] DecisionGate 检查异常，默认放行: {gate_err}")
            gate_approved = True

        # publish 决策门禁结果到消息池供审计（SubTask 3.6）
        try:
            self.publish(
                "decision.gate.external_publish",
                {
                    "title": article_title,
                    "approved": gate_approved,
                    "rejected": not gate_approved,
                    "reason": gate_reason,
                },
            )
        except Exception as pub_err:  # noqa: BLE001
            print(f"[coo] publish decision.gate.external_publish 失败: {pub_err}")

        # 用户拒绝或超时 cancel → 跳过发布，返回占位文本
        if not gate_approved:
            return (
                f"# 推广物料（已跳过）：{article_title}\n\n"
                f"> 决策门禁 external_publish 未通过人工确认，本次发布已跳过。\n"
                f"> 原因：{gate_reason or '用户拒绝'}\n"
                f"> 物料未生成，可在用户确认后重新触发执行。\n"
            )

        # 3. 调用 LLM 生成 3 个物料
        user_message = (
            f"请为以下文章产出 3 份推广物料，必须包含三个独立章节：\n"
            f"## Twitter 推文（≤280 字符，含 URL + 打赏地址 + 3 个 hashtag）\n"
            f"## Reddit 帖子（深度讨论版，500+ 字）\n"
            f"## Telegram 广播文案（简短带 emoji）\n\n"
            f"文章标题：{article_title}\n"
            f"文章 URL：{url}\n"
            f"打赏地址：{TIPPING_ADDRESS}\n"
            f"文章摘要（前 800 字）：\n{article_content[:800] or '（无内容）'}"
        )
        try:
            raw = self.call_llm(user_message, context="任务：推广运营与渠道策略")
        except Exception as e:  # noqa: BLE001 - LLM 失败降级
            print(f"[coo] execute_promotion LLM 调用失败，降级为模板物料：{e}")
            raw = ""

        # LLM 输出包含三个章节标记则采用
        if raw and "twitter" in raw.lower() and "reddit" in raw.lower() and "telegram" in raw.lower():
            return f"# 推广物料：{article_title}\n\n{raw}\n"

        # 降级：模板物料
        return self._build_promo_template(article_title, url, TIPPING_ADDRESS)

    def _build_promo_template(self, title: str, url: str, tipping_address: str) -> str:
        """生成模板推广物料（LLM 降级时使用），含 Twitter/Reddit/Telegram 三节。"""
        from datetime import datetime

        twitter = self._build_twitter(title, url, tipping_address)
        # Reddit 帖子（500+ 字）
        reddit = (
            f"## {title}\n\n"
            f"I just published a deep dive on this topic and wanted to share it with the community. "
            f"Link: {url}\n\n"
            f"### Why this matters\n"
            f"Crypto moves fast, and most guides out there are either outdated or too shallow. "
            f"This article aims to give a complete, practical walkthrough that a newcomer can follow "
            f"and an intermediate user can still learn from. I cover the core concepts, a step-by-step "
            f"workflow, the most common mistakes people make, and the risks you should be aware of before "
            f"you put any real money on the line.\n\n"
            f"### What's inside\n"
            f"- A clear explanation of the fundamentals\n"
            f"- A repeatable workflow you can apply today\n"
            f"- The mistakes I see over and over again\n"
            f"- Honest risk assessment and mitigation tips\n"
            f"- Advanced tips for once you are comfortable\n\n"
            f"### How to use it\n"
            f"Read the guide end to end first. Then pick one small action from the step-by-step section "
            f"and execute it on a testnet before you touch mainnet. Document what happens. Compare your "
            f"results against the benchmarks in the article. If something goes wrong, the common mistakes "
            f"section likely explains why.\n\n"
            f"### A request\n"
            f"If this is useful, consider tipping the author at {tipping_address}. "
            f"Tips make it possible to keep producing free, in-depth guides like this one. "
            f"Feedback and corrections are very welcome in the comments — I will incorporate the best "
            f"suggestions into the next revision. Thanks for reading!\n"
        )
        # Telegram 广播文案（简短带 emoji）
        telegram = (
            f"🚀 New guide published!\n\n"
            f"📚 {title}\n"
            f"🔗 {url}\n\n"
            f"💸 Tip the author: `{tipping_address}`\n"
            f"💬 Discussion welcome"
        )

        lines: list[str] = []
        lines.append(f"# 推广物料：{title}")
        lines.append("")
        lines.append(f"> 生成时间：{datetime.now().isoformat(timespec='seconds')}（降级模式：LLM 调用失败，模板生成）")
        lines.append("")
        lines.append("## Twitter 推文")
        lines.append("")
        lines.append(twitter)
        lines.append("")
        lines.append(f"> 字符数：{len(twitter)}（限制 280）")
        lines.append("")
        lines.append("## Reddit 帖子")
        lines.append("")
        lines.append(reddit)
        lines.append("")
        lines.append("## Telegram 广播文案")
        lines.append("")
        lines.append(telegram)
        lines.append("")
        return "\n".join(lines)

    @staticmethod
    def _build_twitter(title: str, url: str, tipping_address: str) -> str:
        """构造 ≤280 字符的 Twitter 推文，超长则截断标题。"""
        hashtag_line = "#Crypto #Web3 #DeFi"
        head = "New guide: "
        tail = f" 📚\nRead free: {url}\n\n{hashtag_line}\n\n💸 Tip: {tipping_address}"
        max_title_len = 280 - len(head) - len(tail)
        use_title = title
        if max_title_len < 8:
            # URL+地址已接近上限，标题仅保留极短占位
            use_title = "guide"
        elif len(title) > max_title_len:
            use_title = title[: max(8, max_title_len - 1)].rstrip() + "…"
        return f"{head}{use_title}{tail}"

    # ------------------------------------------------------------------
    # 任务执行
    # ------------------------------------------------------------------
    def execute_task(self, task: dict) -> dict:
        """执行 promote 类任务：产出推广物料并落盘。

        Returns:
            ``{status: "done"|"failed", result_path: str, error_reason: str}``
        """
        from datetime import datetime
        from engine.task_queue import TaskQueue

        task_id = task.get("id", "") if isinstance(task, dict) else ""
        try:
            queue = TaskQueue(self.workspace)
            queue.update_status(task_id, "in_progress")

            # 1. 产出推广物料
            promo = self.execute_promotion(task)

            # 2. 写入 company/knowledge/marketing/promo-YYYY-MM-DD-<task_id>.md
            today = datetime.now().strftime("%Y-%m-%d")
            marketing_dir = self.workspace.knowledge_dir / "marketing"
            target_path = marketing_dir / f"promo-{today}-{task_id}.md"
            self.workspace.write_text(target_path, promo)
            result_path = str(target_path.resolve())

            # 3. 汇报完成
            self.report_done(task_id, result_path)
            return {"status": "done", "result_path": result_path, "error_reason": ""}
        except Exception as e:  # noqa: BLE001 - 顶层兜底
            self.report_failed(task_id, str(e))
            return {"status": "failed", "result_path": "", "error_reason": str(e)}
