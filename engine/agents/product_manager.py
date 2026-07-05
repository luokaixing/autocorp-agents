"""ProductManager 智能体 - 产品经理

对产品市场契合度（PMF）负责，从市场情报出发产出 PRD。
"""
from __future__ import annotations

from typing import Any, Dict, List

from engine.agents.base import BaseAgent
from engine.workspace import WorkspaceManager
from engine.llm_client import LLMClient


class ProductManager(BaseAgent):
    """产品经理：负责市场调研、需求搜集、PRD 撰写。"""

    # 市场情报种子文件
    SEED_RESEARCH_PATH = "knowledge/market-research/seed-2026.md"

    # SubTask 4.2: 高打赏率主题白名单
    # 基于历史数据：钱包教程 / 空投指南 / DeFi 入门 / Learn & Earn 攻略 / 测试网教程等
    # 主题命中白名单的选题在评分中获得 +30 加权
    HIGH_TIP_RATE_TOPICS = [
        "ethereum wallet", "crypto airdrop", "defi beginner",
        "learn and earn", "testnet guide", "metamask tutorial",
        "crypto security", "layer2", "smart contract", "nft guide",
    ]

    # 内容账本路径（相对 root_dir）：用于历史打赏/浏览数据加权
    CONTENT_LEDGER_PATH = "config/content-ledger.yaml"

    def __init__(self, workspace: WorkspaceManager, llm_client: LLMClient = None):
        super().__init__("product_manager", workspace, llm_client)

    def research_market(self, topic: str = "") -> dict:
        """市场调研，读取 seed-2026.md 作为输入，输出需求候选。

        Returns:
            含 candidates / raw_response 的字典。
        """
        # 读取市场情报种子文件
        seed_path = self.workspace.root_dir / self.SEED_RESEARCH_PATH
        seed_content = self.workspace.read_text(seed_path)
        user_message = (
            f"请基于以下市场情报进行调研，识别可变现的产品需求候选"
            f"{'（聚焦主题：' + topic + '）' if topic else ''}，"
            f"每个候选需含痛点、目标用户、竞品、变现路径。\n"
            f"市场情报：\n{seed_content or '（未找到 seed-2026.md）'}"
        )
        raw = self.call_llm(user_message, context="任务：市场调研与竞品分析")
        # 持久化调研结果
        self.save_output(
            f"# 市场调研报告\n\n{raw}",
            category="research",
            filename="pm-market-research.md",
        )
        return {
            "candidates": None,
            "seed_used": str(seed_path.resolve()),
            "raw_response": raw,
        }

    def collect_requirements(self) -> list:
        """搜集需求清单，返回需求列表。"""
        user_message = (
            "请基于 AutoCorp 当前市场情报与产品矩阵，搜集并输出需求清单，"
            "每条需求含编号、用户痛点、优先级、预估开发量。"
        )
        raw = self.call_llm(user_message, context="任务：需求搜集与用户痛点")
        return [{
            "id": "req_001",
            "pain_point": "见 raw_response",
            "priority": "TBD",
            "effort": "TBD",
            "raw_response": raw,
        }]

    def write_prd(self, idea: dict) -> dict:
        """撰写 PRD，返回 {title, problem, users, features, mvp_scope, monetization, raw_response}。"""
        user_message = (
            f"请基于以下产品想法撰写完整 PRD，必须包含：标题、痛点、目标用户、"
            f"功能清单、MVP 范围、变现路径。\n产品想法：\n{idea}"
        )
        raw = self.call_llm(user_message, context="任务：PRD 撰写与变现路径")
        # 持久化 PRD 到 projects 目录
        title = idea.get("title", "unnamed-prd") if isinstance(idea, dict) else "unnamed-prd"
        prd_path = self.workspace.projects_dir / f"{title}-prd.md"
        self.workspace.write_text(prd_path, f"# PRD: {title}\n\n{raw}")
        return {
            "title": title,
            "problem": None,
            "users": None,
            "features": None,
            "mvp_scope": None,
            "monetization": None,
            "prd_path": str(prd_path.resolve()),
            "raw_response": raw,
        }

    # ------------------------------------------------------------------
    # SubTask 5.6: 晨会抓取社交平台热门话题（Agent-Reach 集成）
    # ------------------------------------------------------------------
    def fetch_social_trends(self, platforms: list = None) -> dict:
        """晨会抓取社交平台热门话题，作为选题源

        通过 engine.social_reach.SocialReach 抓取多平台 DeFi 热门帖子，
        作为 PM 选题阶段社交信号输入。失败优雅降级为空列表，不阻断晨会。

        Args:
            platforms: 平台列表，默认 ["reddit", "bilibili"]（国内可访问，
                无需翻墙）。如需抓 twitter/youtube 需用户先开翻墙。

        Returns:
            ``{platform: [posts]}`` 字典，posts 为标准化帖子列表，每条含
            title/url/content/snippet/engagement/author/fetched_at。
        """
        from engine.social_reach import SocialReach

        platforms = platforms or ["reddit", "bilibili"]
        reach = SocialReach()
        result: dict = {}
        for p in platforms:
            try:
                posts = reach.fetch_trending(p, keyword="DeFi", limit=20)
                result[p] = posts
                print(f"[product_manager] 抓取 {p} 成功：{len(posts)} 条")
            except Exception as e:  # noqa: BLE001 - 单平台失败不阻断
                print(f"[product_manager] 抓取 {p} 失败：{e}")
                result[p] = []
        return result

    # ------------------------------------------------------------------
    # 市场扫描（execute_task 调用）
    # ------------------------------------------------------------------
    def scan_market(self) -> dict:
        """扫描加密货币市场，产出研究报告（含 top 5 涨幅币 + 选题建议）。

        数据来源：CryptoMarketAnalyzer.fetch_market_data()（CoinGecko 公开 API）。
        数据获取失败时降级为一般性 crypto 市场描述，保证报告始终可产出。

        Returns:
            ``{"report": str, "top_gainers": list[dict], "suggestion": str}``
        """
        from engine.crypto.market_analyzer import CryptoMarketAnalyzer

        analyzer = CryptoMarketAnalyzer(self.workspace, self.llm_client)
        try:
            market_data = analyzer.fetch_market_data()
        except Exception as e:  # noqa: BLE001 - 数据获取失败时降级
            print(f"[product_manager] fetch_market_data 异常，降级处理：{e}")
            market_data = {}

        coins = (market_data or {}).get("coins", [])
        fetched_at = (market_data or {}).get("fetched_at", "")

        # 计算 top 5 涨幅币（按 24h 涨跌幅降序）
        top_gainers: list[dict] = []
        if coins:
            top_gainers = sorted(
                coins,
                key=lambda c: c.get("price_change_percentage_24h") or 0,
                reverse=True,
            )[:5]

        report = self._build_market_scan_report(coins, top_gainers, fetched_at)
        suggestion = self._derive_topic_suggestion(top_gainers)

        # SubTask 4.6: 调用爆款选题引擎，附加 viral_topics 字段
        # 爆款引擎失败不阻断市场扫描主流程（优雅降级为空列表）
        try:
            viral_topics = self.generate_viral_topics()
        except Exception as e:  # noqa: BLE001 - 爆款引擎异常降级
            print(f"[product_manager] 爆款选题引擎异常（已降级为空列表）：{e}")
            viral_topics = []

        return {
            "report": report,
            "top_gainers": top_gainers,
            "suggestion": suggestion,
            "viral_topics": viral_topics,
        }

    def _build_market_scan_report(
        self, coins: list, top_gainers: list, fetched_at: str
    ) -> str:
        """组装市场扫描 markdown 报告：元信息 + top 5 涨幅表 + 市场总览 + 选题建议。"""
        from datetime import datetime

        today = datetime.now().strftime("%Y-%m-%d")
        lines: list[str] = []
        lines.append(f"# PM 市场扫描报告 {today}")
        lines.append("")
        lines.append(f"- 生成时间：{datetime.now().isoformat(timespec='seconds')}")
        lines.append("- 数据来源：CoinGecko 公开 API（fetch_market_data）")
        lines.append(f"- 数据抓取时间：{fetched_at or '（抓取失败，已降级）'}")
        lines.append("")

        # Top 5 涨幅币表格
        lines.append("## Top 5 涨幅币（24h）")
        lines.append("")
        if top_gainers:
            lines.append("| # | Symbol | 名称 | 价格(USD) | 24h涨跌(%) |")
            lines.append("|---|--------|------|-----------|------------|")
            for idx, c in enumerate(top_gainers, start=1):
                price = c.get("current_price")
                chg = c.get("price_change_percentage_24h")
                price_str = f"{price:,.4f}" if isinstance(price, (int, float)) else "-"
                chg_str = f"{chg:+.2f}" if isinstance(chg, (int, float)) else "-"
                lines.append(
                    f"| {idx} | {c.get('symbol','')} | {c.get('name','')} | "
                    f"{price_str} | {chg_str} |"
                )
            lines.append("")
        else:
            lines.append("> 行情数据获取失败，以下为一般性 crypto 市场描述。")
            lines.append("")

        # 市场总览
        lines.append("## 市场总览")
        lines.append("")
        if coins:
            gainers = sum(1 for c in coins if (c.get("price_change_percentage_24h") or 0) > 0)
            losers = sum(1 for c in coins if (c.get("price_change_percentage_24h") or 0) < 0)
            lines.append(f"- 采样币种数：{len(coins)}")
            lines.append(f"- 24h 上涨：{gainers} / 下跌：{losers}")
            for marker in ("BTC", "ETH"):
                for c in coins:
                    if (c.get("symbol") or "").upper() == marker:
                        price = c.get("current_price")
                        chg = c.get("price_change_percentage_24h")
                        price_str = f"${price:,.2f}" if isinstance(price, (int, float)) else "-"
                        extra = f"，24h {chg:+.2f}%" if isinstance(chg, (int, float)) else ""
                        lines.append(f"- {marker}：{price_str}{extra}")
                        break
            lines.append("")
        else:
            lines.append(
                "当前加密货币市场整体处于活跃状态。BTC 与 ETH 仍是市场风向标，"
                "DeFi、Layer2、RWA、稳定币收益等赛道持续有新机会涌现。"
                "建议关注：空投（airdrop）、质押（staking）、链上数据分析（onchain_data）、"
                "稳定币收益（stablecoin_yield）四类低门槛机会。"
            )
            lines.append("")

        # 选题建议
        suggestion = self._derive_topic_suggestion(top_gainers)
        lines.append("## 选题建议")
        lines.append("")
        lines.append(f"- {suggestion}")
        lines.append("- 结合 AutoCorp SEO 内容产品矩阵，建议将选题转化为 1500+ 字 SEO 文章产出。")
        lines.append("")

        return "\n".join(lines)

    def _derive_topic_suggestion(self, top_gainers: list) -> str:
        """基于 top 涨幅币推导选题建议；无数据时返回默认选题。"""
        if top_gainers:
            top = top_gainers[0]
            sym = top.get("symbol", "")
            name = top.get("name", sym)
            return f"撰写「{name}（{sym}）深度解析」SEO 文章，覆盖项目机制、参与方式与风险提示"
        return "撰写「2026 加密货币新手入门指南」SEO 文章，覆盖钱包、空投、质押与防骗"

    # ------------------------------------------------------------------
    # SubTask 4.1-4.5: 爆款内容选题引擎
    # 设计要点：
    # - 不依赖 HTTP LLM API（智谱 GLM-5.2 公开 API 404），用规则代码（白名单+加权）实现
    # - 优雅降级：CoinGecko 拉取失败 / 历史账本读取失败均不阻断主流程
    # - 复用 TaskQueue：Top 1 选题入队 source=pm_viral_topic
    # ------------------------------------------------------------------
    def generate_viral_topics(self, count: int = 5) -> list[dict]:
        """生成爆款内容选题清单（SubTask 4.1）。

        基于规则代码（白名单 + 加权）评估选题，不依赖 HTTP LLM API。

        评分规则（SubTask 4.3）：
        - 白名单匹配（+30 分）：选题主题命中 HIGH_TIP_RATE_TOPICS
        - CoinGecko 涨幅榜前 10 币种相关主题加权（+20 分，可 try/except 跳过）
        - 历史文章中浏览量 / 打赏数据加权（+10 分，从 content-ledger.yaml 读取）

        Args:
            count: 返回的选题数量，默认 5。

        Returns:
            选题字典列表，按 topic_score 降序排列。每个选题含字段（SubTask 4.4）：
            - title_draft: 标题草稿
            - keywords: 关键词列表
            - expected_tip_probability: 预期打赏概率（0-1）
            - seo_score: SEO 评分预估（0-100）
            - topic_score: 综合选题评分
        """
        # 1. 构造候选选题池：白名单 + CoinGecko 涨幅榜扩展
        candidates: list[dict] = []

        # 1.1 从白名单构造基础候选（每个白名单主题均 +30 起步）
        for topic in self.HIGH_TIP_RATE_TOPICS:
            candidates.append({
                "title_draft": self._draft_title(topic),
                "keywords": self._extract_keywords(topic),
                "_source_topic": topic.lower(),
                "_from_whitelist": True,
                "_coin": None,
            })

        # 1.2 尝试从 CoinGecko 涨幅榜获取 Top 10 币种，扩展候选
        # 失败则跳过，不影响白名单候选（优雅降级）
        top_gainers: list[dict] = []
        try:
            from engine.crypto.market_analyzer import CryptoMarketAnalyzer

            analyzer = CryptoMarketAnalyzer(self.workspace, self.llm_client)
            market_data = analyzer.fetch_market_data() or {}
            coins = market_data.get("coins", [])
            if coins:
                top_gainers = sorted(
                    coins,
                    key=lambda c: c.get("price_change_percentage_24h") or 0,
                    reverse=True,
                )[:10]
                for coin in top_gainers:
                    name = coin.get("name", "") or ""
                    sym = (coin.get("symbol") or "").upper()
                    if not name:
                        continue
                    candidates.append({
                        "title_draft": (
                            f"{name} ({sym}) Price Surge 2026: "
                            f"Mechanism, Rally Drivers & How to Participate"
                        ),
                        "keywords": [name.lower(), sym.lower(), "price prediction", "crypto"],
                        "_source_topic": name.lower(),
                        "_from_whitelist": False,
                        "_coin": coin,
                    })
        except Exception as e:  # noqa: BLE001 - CoinGecko 拉取失败降级
            print(f"[product_manager] CoinGecko 涨幅榜拉取失败（已跳过加权）：{e}")

        # 1.3 读取历史打赏数据（content-ledger.yaml），失败返回空字典
        history_map = self._load_history_stats()

        # 2. 评分（SubTask 4.3）
        scored: list[dict] = []
        for cand in candidates:
            score = 0.0
            source_topic = cand.get("_source_topic", "") or ""

            # 2.1 白名单匹配 +30 分
            if cand.get("_from_whitelist"):
                score += 30
            else:
                # 非白名单候选：检查主题是否与白名单词项相关
                for w in self.HIGH_TIP_RATE_TOPICS:
                    if w in source_topic or source_topic in w:
                        score += 30
                        break

            # 2.2 CoinGecko 涨幅榜前 10 币种相关 +20 分
            if top_gainers:
                if cand.get("_coin") is not None:
                    # 候选本身即来自涨幅榜
                    score += 20
                else:
                    # 检查候选主题是否提及涨幅榜币种
                    for g in top_gainers:
                        gname = (g.get("name") or "").lower()
                        gsym = (g.get("symbol") or "").lower()
                        if gname and (gname in source_topic or source_topic in gname):
                            score += 20
                            break
                        if gsym and len(gsym) >= 3 and gsym in source_topic:
                            score += 20
                            break

            # 2.3 历史文章浏览量 / 打赏数据加权 +10 分
            for kw, stats in history_map.items():
                if not kw:
                    continue
                if kw in source_topic or source_topic in kw:
                    if stats.get("tips_usd", 0) > 0 or stats.get("views", 0) > 0:
                        score += 10
                    break

            # 2.4 计算 expected_tip_probability 与 seo_score（基于评分映射）
            prob = min(0.9, 0.2 + score / 100.0)
            seo_score = min(100, int(40 + score))

            scored.append({
                "title_draft": cand["title_draft"],
                "keywords": cand["keywords"],
                "expected_tip_probability": round(prob, 2),
                "seo_score": seo_score,
                "topic_score": round(score, 2),
            })

        # 3. 按 topic_score 降序排序，取 Top N
        scored.sort(key=lambda t: t["topic_score"], reverse=True)
        top_topics = scored[:count]

        # 4. SubTask 4.5: Top 1 选题自动入队 task_queue
        # 入队失败不阻断主流程（优雅降级）
        if top_topics:
            try:
                self._enqueue_viral_topic(top_topics[0])
            except Exception as e:  # noqa: BLE001 - 入队失败降级
                print(f"[product_manager] 爆款选题 Top1 入队失败（不阻断主流程）：{e}")

        return top_topics

    def _draft_title(self, topic: str) -> str:
        """根据主题关键词草拟文章标题（规则模板，不依赖 LLM）。"""
        return (
            f"The Ultimate Guide to {topic.title()} in 2026: "
            f"Tips, Tricks & Best Practices"
        )

    def _extract_keywords(self, topic: str) -> list[str]:
        """从主题字符串提取关键词列表。"""
        return [p.strip() for p in topic.split() if p.strip()]

    def _load_history_stats(self) -> dict:
        """从 content-ledger.yaml 读取历史文章的浏览 / 打赏数据。

        Returns:
            ``{keyword: {tips_usd, views}}`` 字典；读取失败返回空字典（优雅降级）。
        """
        try:
            ledger_path = self.workspace.root_dir / self.CONTENT_LEDGER_PATH
            data = self.workspace.read_yaml(ledger_path) or {}
            result: dict = {}
            for art in data.get("articles", []) or []:
                kw = (art.get("keyword") or "").lower().strip()
                if not kw:
                    continue
                tips = 0.0
                views = 0
                for plat in art.get("platforms", []) or []:
                    try:
                        tips += float(plat.get("tips_received_usd") or 0)
                    except (TypeError, ValueError):
                        pass
                    try:
                        v = plat.get("views_24h")
                        if v is None:
                            v = plat.get("views_7d") or 0
                        views += int(v or 0)
                    except (TypeError, ValueError):
                        pass
                result[kw] = {"tips_usd": tips, "views": views}
            return result
        except Exception as e:  # noqa: BLE001 - 历史账本读取失败降级
            print(f"[product_manager] 历史账本读取失败（已跳过加权）：{e}")
            return {}

    def _enqueue_viral_topic(self, topic: dict) -> dict:
        """SubTask 4.5: Top 1 选题自动入队 task_queue。

        调用 TaskQueue.add_task(type="code", assignee="programmer",
        priority="P1", source="pm_viral_topic", metadata={...})。
        """
        from engine.task_queue import TaskQueue

        queue = TaskQueue(self.workspace)
        title = topic.get("title_draft", "")
        keywords = topic.get("keywords", []) or []
        description = (
            f"PM 爆款选题引擎产出的高打赏概率选题任务。\n"
            f"- 标题草稿：{title}\n"
            f"- 关键词：{', '.join(keywords)}\n"
            f"- 预期打赏概率：{topic.get('expected_tip_probability', 0)}\n"
            f"- SEO 评分：{topic.get('seo_score', 0)}\n"
            f"- 综合选题评分：{topic.get('topic_score', 0)}\n"
            f"请基于此选题产出 1500+ 字 SEO 文章并多渠道分发。"
        )
        metadata = {
            "keywords": keywords,
            "expected_tip_probability": topic.get("expected_tip_probability", 0),
            "seo_score": topic.get("seo_score", 0),
            "topic_score": topic.get("topic_score", 0),
        }
        return queue.add_task(
            title=title,
            description=description,
            type="code",
            assignee="programmer",
            priority="P1",
            source="pm_viral_topic",
            metadata=metadata,
        )

    # ------------------------------------------------------------------
    # SubTask 1.3: 基于 claude-seo content-brief-generator 生成结构化 brief
    # 设计要点：
    # - 优先加载 claude-seo skill 套件，格式化 prompt 后调用 LLM
    # - skill 未加载 / LLM 调用失败时优雅降级到模板生成（不阻断主流程）
    # ------------------------------------------------------------------
    def generate_content_brief(self, keyword: str, audience: str = "crypto") -> dict:
        """使用 claude-seo content-brief-generator 生成结构化 brief。

        Args:
            keyword: 主目标关键词。
            audience: 目标受众标识，默认 "crypto"。

        Returns:
            brief 字典，含 keyword / audience / brief_md / source 字段。
            source 为 "content-brief-generator"（LLM 生成）或
            "template-fallback"（skill 缺失或 LLM 失败时降级）。
        """
        from engine.llm_client import load_seo_skills

        # 1. 加载 SEO skill 套件
        try:
            skills = load_seo_skills()
        except FileNotFoundError as e:
            print(f"[product_manager] SEO Skill 套件未加载，降级到模板 brief：{e}")
            return self._template_brief(keyword, audience)

        if "content-brief-generator" not in skills:
            print("[product_manager] content-brief-generator skill 未加载，降级到模板")
            return self._template_brief(keyword, audience)

        # 2. 格式化 prompt 并调用 LLM
        skill = skills["content-brief-generator"]
        try:
            prompt = skill["prompt"].format(keyword=keyword, audience=audience)
            brief_md = self.call_llm(
                prompt, context="任务：基于 claude-seo content-brief-generator 生成内容 brief"
            )
        except Exception as e:  # noqa: BLE001 - LLM 调用失败降级
            print(f"[product_manager] content-brief-generator LLM 调用失败，降级到模板：{e}")
            return self._template_brief(keyword, audience)

        return {
            "keyword": keyword,
            "audience": audience,
            "brief_md": brief_md,
            "source": "content-brief-generator",
        }

    def _template_brief(self, keyword: str, audience: str) -> dict:
        """skill 不可用或 LLM 失败时的模板降级 brief（规则生成，不依赖 LLM）。"""
        secondary = [
            f"{keyword} guide", f"{keyword} tutorial",
            f"{keyword} tips", f"best {keyword}",
        ]
        long_tail = [
            f"how to use {keyword}", f"{keyword} for beginners",
            f"{keyword} in 2026", f"is {keyword} safe",
            f"{keyword} vs alternatives",
        ]
        brief_md = (
            f"# 内容 Brief: {keyword}\n\n"
            f"## 目标关键词\n"
            f"- 主关键词：{keyword}\n"
            f"- 次要关键词：{', '.join(secondary)}\n"
            f"- 长尾词：{', '.join(long_tail)}\n\n"
            f"## 受众画像\n"
            f"- 受众：{audience}\n"
            f"- 核心痛点：缺乏系统化的 {keyword} 实战指引\n"
            f"- 阅读动机：快速上手并规避常见坑\n\n"
            f"## 搜索意图\n"
            f"- informational\n\n"
            f"## 大纲建议\n"
            f"- H1: The Ultimate Guide to {keyword} in 2026\n"
            f"- H2: What is {keyword}\n"
            f"- H2: Why {keyword} matters\n"
            f"- H2: How to get started with {keyword}\n"
            f"- H2: Best practices for {keyword}\n"
            f"- H2: Common mistakes and FAQ\n\n"
            f"## 竞品分析\n"
            f"- 竞品角度 1：基础概念科普\n"
            f"- 竞品角度 2：操作步骤教程\n"
            f"- 差异化切入：结合 2026 最新趋势与实战案例\n\n"
            f"## 字数建议\n"
            f"- 1500-2000 字\n"
        )
        return {
            "keyword": keyword,
            "audience": audience,
            "brief_md": brief_md,
            "source": "template-fallback",
        }

    # ------------------------------------------------------------------
    # 任务执行
    # ------------------------------------------------------------------
    def execute_task(self, task: dict) -> dict:
        """执行 research 类任务：扫描市场 → 产出研究报告 → 入队选题任务。

        Returns:
            ``{status: "done"|"failed", result_path: str, error_reason: str}``
        """
        from datetime import datetime
        from engine.task_queue import TaskQueue

        task_id = task.get("id", "") if isinstance(task, dict) else ""
        try:
            queue = TaskQueue(self.workspace)
            queue.update_status(task_id, "in_progress")

            # 1. 扫描市场产出研究报告
            result = self.scan_market()
            report = result.get("report", "")
            suggestion = result.get("suggestion", "")

            # 2. 写入 company/knowledge/market-research/pm-scan-YYYY-MM-DD.md
            today = datetime.now().strftime("%Y-%m-%d")
            target_path = self.workspace.market_research_dir / f"pm-scan-{today}.md"
            self.workspace.write_text(target_path, report)
            result_path = str(target_path.resolve())

            # 3. 根据研究报告产出 1 个新选题任务入队（type=code, source=pm_scan）
            try:
                queue.add_task(
                    title=suggestion or f"PM 扫描选题 {today}",
                    description=(
                        f"基于 {today} PM 市场扫描报告产出的选题任务。"
                        f"选题方向：{suggestion}。"
                        f"研究报告：{result_path}"
                    ),
                    type="code",
                    assignee="programmer",
                    priority="P2",
                    source="pm_scan",
                )
            except Exception as e:  # noqa: BLE001 - 入队失败不阻断主流程
                print(f"[product_manager] 入队选题任务失败（不影响主流程）：{e}")

            # 4. 汇报完成
            self.report_done(task_id, result_path)
            return {"status": "done", "result_path": result_path, "error_reason": ""}
        except Exception as e:  # noqa: BLE001 - 顶层兜底
            self.report_failed(task_id, str(e))
            return {"status": "failed", "result_path": "", "error_reason": str(e)}
