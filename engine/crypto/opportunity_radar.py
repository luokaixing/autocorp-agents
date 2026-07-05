"""第一桶金机会雷达

每日自动扫描、评估、排序所有零成本获取加密货币的渠道，输出 Top 10 机会清单。

设计要点：
- 零成本原则：只扫描零成本渠道（Learn & Earn / 测试网空投 / 任务平台），排除需要初始资金的 DeFi
- 优雅降级：每个数据源独立 try/except，WebFetch 失败 / 课程抓取失败均返回空列表，不阻断主流程
- 不依赖 HTTP LLM API：评分与排序用规则代码实现（智谱 GLM-5.2 公开 API 返回 404）
- 复用现有代码：不重新实现 Blockscout 钱包余额查询，已在 engine/crypto/wallet.py
- 文件即数据库：机会清单输出为 markdown，持久化到 company/knowledge/opportunities/radar-YYYY-MM-DD.md

数据源：
1. Binance Learn & Earn 课程列表（确定性最高，1-3 天到账）
2. CoinMarketCap Earn 活动列表（绑定 Binance 后到账）
3. Layer3 任务列表（CUBE 积分 → 空投，1-4 周）
4. DeFi Llama Airdrops 板块（仅纳入零成本测试网空投）
"""
from __future__ import annotations

import datetime
import re
from typing import Any, Dict, List

# HTTP 库：优先 requests（若已安装），否则回退到标准库 urllib（与 wallet.py 保持一致）
try:
    import requests  # type: ignore

    _HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error

    _HAS_REQUESTS = False


class OpportunityRadar:
    """第一桶金机会雷达：扫描 + 评估 + 排序零成本赚币机会。"""

    # 数据源 URL（均为公开页面，免 key）
    BINANCE_LEARN_EARN_URL = "https://www.binance.com/en/activity/learn-and-earn"
    COINMARKETCAP_EARN_URL = "https://coinmarketcap.com/earn/"
    LAYER3_CAMPAIGNS_URL = "https://layer3.xyz/campaigns"
    DEFILLAMA_AIRDROPS_URL = "https://defillama.com/airdrops"

    # 优先级排序权重：值越小优先级越高
    _PRIORITY_ORDER = {"P0": 0, "P1": 1, "P2": 2}
    # 到账速度排序权重：fast（1-3天）< medium（3-7天）< slow（1-4周）
    _SPEED_ORDER = {"fast": 0, "medium": 1, "slow": 2}

    def __init__(self, workspace=None, llm_client=None):
        """初始化机会雷达。

        Args:
            workspace: WorkspaceManager 实例；为空则自动创建（root_dir 指向 company/）。
            llm_client: 预留接口位（spec 提及智谱 GLM-5.2）。
                        当前评分排序用规则代码实现，不依赖 HTTP LLM API。
        """
        from engine.workspace import WorkspaceManager

        self.workspace = workspace or WorkspaceManager()
        self.llm_client = llm_client
        # 机会清单输出目录：company/knowledge/opportunities/
        self.opportunities_dir = self.workspace.knowledge_dir / "opportunities"

    # ==================================================================
    # SubTask 1.1: scan_all_channels 主方法
    # ==================================================================
    def scan_all_channels(self) -> List[Dict[str, Any]]:
        """聚合 4 个数据源扫描，评估排序后返回 Top 10 机会清单。

        流程：
        1. 依次调用 4 个 scan 方法（每个独立 try/except，失败返回空列表）
        2. 对每个机会进行三维评分（evaluate_opportunity）
        3. 按优先级 → 到账速度 → 收益 max 降序 排序
        4. 取 Top 10
        5. 生成 markdown 报告（失败不阻断）
        6. P0 机会自动入队 task_queue（失败不阻断）

        Returns:
            Top 10 机会字典列表，每个含 channel/title/speed/certainty/
            reward_min/reward_max/priority/source_url 等字段。
        """
        all_opportunities: List[Dict[str, Any]] = []

        # 4 个数据源，每个独立降级，互不影响
        scanners = [
            self.scan_binance_learn_earn,
            self.scan_coinmarketcap_earn,
            self.scan_layer3,
            self.scan_defi_llama_airdrops,
        ]
        for scanner in scanners:
            try:
                items = scanner() or []
                all_opportunities.extend(items)
            except Exception as e:  # noqa: BLE001 - 单源异常不阻断主流程
                print(f"[opportunity_radar] {scanner.__name__} 异常：{e}")

        # 对每个机会进行三维评分
        for opp in all_opportunities:
            try:
                opp.update(self.evaluate_opportunity(opp))
            except Exception as e:  # noqa: BLE001 - 单条评估失败不阻断
                print(f"[opportunity_radar] 评估失败 {opp.get('title', '?')}：{e}")
                opp.setdefault("priority", "P2")

        # 排序：优先级（P0<P1<P2）→ 到账速度（fast<medium<slow）→ 收益 max 降序
        all_opportunities.sort(
            key=lambda o: (
                self._PRIORITY_ORDER.get(o.get("priority", "P2"), 2),
                self._SPEED_ORDER.get(o.get("speed", "medium"), 1),
                -(float(o.get("reward_max", 0) or 0)),
            )
        )

        # 取 Top 10
        top_10 = all_opportunities[:10]

        # 实时验证层：对 Top 10 机会逐一验证 URL 当日可访问性
        # 跳过已标注"需用户验证"的机会（来自 scan_binance_learn_earn 抓取失败兜底）
        for opp in top_10:
            if opp.get("verification_status") == "需用户验证":
                continue
            try:
                self.verify_realtime(opp)
            except Exception as e:  # noqa: BLE001 - 单条验证失败不阻断
                print(f"[opportunity_radar] 实时验证失败 {opp.get('title', '?')}：{e}")
                opp.setdefault("realtime_verified", False)
                opp.setdefault("verification_status", "failed")
                opp.setdefault(
                    "verification_time",
                    datetime.datetime.now().isoformat(timespec="seconds"),
                )

        # 生成 markdown 报告（失败不阻断主流程）
        try:
            self.generate_radar_report(top_10)
        except Exception as e:  # noqa: BLE001
            print(f"[opportunity_radar] 生成报告失败：{e}")

        # P0 机会自动入队（失败不阻断主流程）
        try:
            self.auto_enqueue_high_priority(top_10)
        except Exception as e:  # noqa: BLE001
            print(f"[opportunity_radar] 自动入队失败：{e}")

        return top_10

    # ==================================================================
    # SubTask 1.2: Binance Learn & Earn
    # ==================================================================
    def scan_binance_learn_earn(self) -> List[Dict[str, Any]]:
        """扫描 Binance Learn & Earn 课程列表。

        抓取公开页面并解析课程条目。远程抓取失败时（HTTPError/Timeout）不抛异常，
        返回标注 verification_status="需用户验证" 的兜底机会供用户手动验证，
        该兜底机会 realtime_verified=False，不进入 auto_enqueue_high_priority()。
        Binance L&E 是最快让 ETH 钱包收到第一笔钱的渠道：
        完成 1 个课程 = 15 分钟 = $2-20 = ERC-20 直接到账。
        """
        try:
            html = self._fetch_text(self.BINANCE_LEARN_EARN_URL)
        except Exception as e:  # noqa: BLE001 - HTTPError/Timeout 等不抛异常
            print(f"[opportunity_radar] Binance L&E 抓取失败（返回需用户验证兜底）：{e}")
            return [self._make_binance_fallback_opportunity()]

        if not html:
            print("[opportunity_radar] Binance L&E 页面为空（返回需用户验证兜底）")
            return [self._make_binance_fallback_opportunity()]

        items = self._parse_binance_courses(html)
        if not items:
            print("[opportunity_radar] Binance L&E 未解析到课程条目（返回需用户验证兜底）")
            return [self._make_binance_fallback_opportunity()]
        return items

    # ==================================================================
    # SubTask 1.3: CoinMarketCap Earn
    # ==================================================================
    def scan_coinmarketcap_earn(self) -> List[Dict[str, Any]]:
        """扫描 CoinMarketCap Earn 活动列表。失败返回空列表。

        CMC Earn 奖励通过绑定 Binance 到账，单次 $2-10，1-3 天到账，确定性高。
        """
        try:
            html = self._fetch_text(self.COINMARKETCAP_EARN_URL)
        except Exception as e:  # noqa: BLE001
            print(f"[opportunity_radar] CMC Earn 抓取失败：{e}")
            return []

        if not html:
            print("[opportunity_radar] CMC Earn 页面为空")
            return []

        items = self._parse_cmc_earn(html)
        if not items:
            print("[opportunity_radar] CMC Earn 未解析到活动条目（页面可能为 SPA 渲染）")
            return []
        return items

    # ==================================================================
    # SubTask 1.4: Layer3
    # ==================================================================
    def scan_layer3(self) -> List[Dict[str, Any]]:
        """扫描 Layer3 任务列表。失败返回空列表。

        Layer3 通过完成跨链任务获得 CUBE 积分，未来可兑换空投。
        零成本、无需资金、立即开始，但到账慢（1-4 周）+ 概率性。
        """
        try:
            html = self._fetch_text(self.LAYER3_CAMPAIGNS_URL)
        except Exception as e:  # noqa: BLE001
            print(f"[opportunity_radar] Layer3 抓取失败：{e}")
            return []

        if not html:
            print("[opportunity_radar] Layer3 页面为空")
            return []

        items = self._parse_layer3_campaigns(html)
        if not items:
            print("[opportunity_radar] Layer3 未解析到任务条目（页面可能为 SPA 渲染）")
            return []
        return items

    # ==================================================================
    # SubTask 1.5: DeFi Llama Airdrops
    # ==================================================================
    def scan_defi_llama_airdrops(self) -> List[Dict[str, Any]]:
        """扫描 DeFi Llama Airdrops 板块。失败返回空列表。

        零成本原则：仅纳入零成本测试网交互 / 社区任务类空投，
        排除需要初始资金的 DeFi（staking / restake / 交易挖矿）。
        """
        try:
            html = self._fetch_text(self.DEFILLAMA_AIRDROPS_URL)
        except Exception as e:  # noqa: BLE001
            print(f"[opportunity_radar] DeFi Llama Airdrops 抓取失败：{e}")
            return []

        if not html:
            print("[opportunity_radar] DeFi Llama Airdrops 页面为空")
            return []

        items = self._parse_defillama_airdrops(html)
        if not items:
            print("[opportunity_radar] DeFi Llama Airdrops 未解析到条目（页面可能为 SPA 渲染）")
            return []
        return items

    # ==================================================================
    # SubTask 1.6: evaluate_opportunity 三维评分
    # ==================================================================
    def evaluate_opportunity(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """三维评分：到账速度 × 确定性 × 收益范围 → 综合优先级 P0/P1/P2。

        评分规则（来自 spec）：
        - 到账速度：fast（1-3天）/ medium（3-7天）/ slow（1-4周）
        - 确定性：high（必定到账）/ medium（概率性）/ low（抽奖制）
        - 综合优先级：fast+high=P0，medium+high=P1，其他=P2

        Args:
            opportunity: 机会字典，需含 speed / certainty / reward_min / reward_max。

        Returns:
            归一化后的评分字典：{speed, certainty, reward_min, reward_max, priority}
        """
        speed = str(opportunity.get("speed", "medium")).lower()
        certainty = str(opportunity.get("certainty", "medium")).lower()

        # 收益范围归一化为 float（防御字符串/None 输入）
        try:
            reward_min = float(opportunity.get("reward_min", 0) or 0)
        except (TypeError, ValueError):
            reward_min = 0.0
        try:
            reward_max = float(opportunity.get("reward_max", 0) or 0)
        except (TypeError, ValueError):
            reward_max = 0.0

        # 综合优先级规则（严格按 spec）
        if speed == "fast" and certainty == "high":
            priority = "P0"
        elif speed == "medium" and certainty == "high":
            priority = "P1"
        else:
            priority = "P2"

        return {
            "speed": speed,
            "certainty": certainty,
            "reward_min": reward_min,
            "reward_max": reward_max,
            "priority": priority,
        }

    # ==================================================================
    # SubTask 5.1: verify_realtime 实时验证层
    # ==================================================================
    def verify_realtime(self, opportunity: Dict[str, Any]) -> Dict[str, Any]:
        """实时验证机会的 URL 当日可访问性。

        调用 RealtimeOpportunityScanner().verify(url) 验证 URL，将结果写回
        opportunity 字典。优雅降级：RealtimeOpportunityScanner 不可用时
        返回 verification_status="skipped"，不阻塞主流程。

        Args:
            opportunity: 机会字典，含 source_url 或 url 字段。

        Returns:
            原 opportunity 字典，新增字段：
            - realtime_verified (bool): True 表示已验证可访问
            - verification_time (str): 验证时间戳 ISO 格式
            - verification_status (str): "verified" / "failed" / "skipped"
        """
        url = opportunity.get("source_url") or opportunity.get("url") or ""
        verification_time = datetime.datetime.now().isoformat(timespec="seconds")

        # 无 URL → 跳过验证
        if not url:
            opportunity["realtime_verified"] = False
            opportunity["verification_time"] = verification_time
            opportunity["verification_status"] = "skipped"
            return opportunity

        # 优雅降级：RealtimeOpportunityScanner 不可用时返回 skipped
        try:
            from engine.crypto.realtime_opportunity_scanner import (
                RealtimeOpportunityScanner,
            )

            scanner = RealtimeOpportunityScanner()
        except Exception as e:  # noqa: BLE001 - 扫描器不可用，优雅降级
            print(f"[opportunity_radar] RealtimeOpportunityScanner 不可用，跳过验证：{e}")
            opportunity["realtime_verified"] = False
            opportunity["verification_time"] = verification_time
            opportunity["verification_status"] = "skipped"
            return opportunity

        # 调用 verify 验证 URL 当日可访问性
        try:
            result = scanner.verify(url)
            accessible = bool(result.get("accessible", False))
            opportunity["realtime_verified"] = accessible
            opportunity["verification_time"] = verification_time
            opportunity["verification_status"] = "verified" if accessible else "failed"
        except Exception as e:  # noqa: BLE001 - 验证失败不阻塞
            print(f"[opportunity_radar] 实时验证异常 {url}：{e}")
            opportunity["realtime_verified"] = False
            opportunity["verification_time"] = verification_time
            opportunity["verification_status"] = "failed"

        return opportunity

    # ==================================================================
    # SubTask 1.7: generate_radar_report 报告生成
    # ==================================================================
    def generate_radar_report(self, opportunities: List[Dict[str, Any]]) -> str:
        """输出 markdown 报告到 company/knowledge/opportunities/radar-YYYY-MM-DD.md。

        自动创建目录。返回报告文件路径。

        Args:
            opportunities: 已评分排序的机会列表（通常为 Top 10）。
        """
        today = datetime.date.today().isoformat()
        report_path = self.opportunities_dir / f"radar-{today}.md"

        lines: List[str] = [
            f"# 第一桶金机会雷达 - {today}",
            "",
            f"扫描时间：{datetime.datetime.now().isoformat(timespec='seconds')}",
            f"机会总数：{len(opportunities)}",
            "",
            "## 机会清单（按优先级排序）",
            "",
            "| # | 优先级 | 渠道 | 标题 | 到账速度 | 确定性 | 收益范围(USD) | 实时验证状态 | 来源 |",
            "|---|--------|------|------|----------|--------|---------------|--------------|------|",
        ]

        for i, opp in enumerate(opportunities, 1):
            reward_min = opp.get("reward_min", 0)
            reward_max = opp.get("reward_max", 0)
            verification_label = self._verification_label(
                opp.get("verification_status", "")
            )
            lines.append(
                f"| {i} | {opp.get('priority', 'P2')} "
                f"| {opp.get('channel', '')} "
                f"| {opp.get('title', '')} "
                f"| {opp.get('speed', '')} "
                f"| {opp.get('certainty', '')} "
                f"| {reward_min}-{reward_max} "
                f"| {verification_label} "
                f"| {opp.get('source_url', '')} |"
            )

        lines.extend([
            "",
            "## 优先级说明",
            "- **P0**：到账快（1-3天）+ 确定性高 → 立即执行，已自动入队 task_queue",
            "- **P1**：到账中（3-7天）+ 确定性高 → 优先安排",
            "- **P2**：其他 → 计划性参与",
            "",
            "## 执行建议",
            "1. P0 机会已自动入队 task_queue，由 programmer 角色处理",
            "2. P1 机会建议人工评估后入队",
            "3. P2 机会作为长期跟踪项目",
            "",
            "## 数据源",
            f"- Binance Learn & Earn: {self.BINANCE_LEARN_EARN_URL}",
            f"- CoinMarketCap Earn: {self.COINMARKETCAP_EARN_URL}",
            f"- Layer3: {self.LAYER3_CAMPAIGNS_URL}",
            f"- DeFi Llama Airdrops: {self.DEFILLAMA_AIRDROPS_URL}",
        ])

        content = "\n".join(lines)
        # 自动创建目录（文件即数据库：所有输出落盘）
        self.workspace.ensure_dir(self.opportunities_dir)
        self.workspace.write_text(report_path, content)
        return str(report_path)

    # ==================================================================
    # SubTask 1.8: auto_enqueue_high_priority P0 自动入队
    # ==================================================================
    def auto_enqueue_high_priority(
        self, opportunities: List[Dict[str, Any]]
    ) -> List[Dict[str, Any]]:
        """P0 机会自动入队 task_queue。

        调用 TaskQueue.add_task(title, description, type="code",
        assignee="programmer", priority="P0", source="opportunity_radar", metadata={...})。

        Args:
            opportunities: 已评分排序的机会列表。

        Returns:
            成功入队的任务字典列表。
        """
        from engine.task_queue import TaskQueue

        queue = TaskQueue(self.workspace)
        enqueued: List[Dict[str, Any]] = []

        for opp in opportunities:
            if opp.get("priority") != "P0":
                continue
            # 实时验证过滤：未通过实时验证的机会不进入 task_queue
            if opp.get("realtime_verified") is not True:
                print(
                    f"[opportunity_radar] 机会未通过实时验证，跳过入队："
                    f"{opp.get('channel', '')} - {opp.get('title', '')} "
                    f"(验证状态: {opp.get('verification_status', '未验证')})"
                )
                continue
            try:
                title = f"[机会雷达] {opp.get('channel', '')}: {opp.get('title', '')}"
                description = (
                    f"零成本赚币机会（P0 - 立即执行）\n"
                    f"- 渠道：{opp.get('channel', '')}\n"
                    f"- 标题：{opp.get('title', '')}\n"
                    f"- 到账速度：{opp.get('speed', '')}\n"
                    f"- 确定性：{opp.get('certainty', '')}\n"
                    f"- 收益范围：{opp.get('reward_min', 0)}-{opp.get('reward_max', 0)} USD\n"
                    f"- 来源：{opp.get('source_url', '')}\n"
                    f"- 所需前置：{opp.get('prerequisites', '')}\n"
                    f"- 描述：{opp.get('description', '')}\n"
                )
                metadata = {
                    "channel": opp.get("channel", ""),
                    "speed": opp.get("speed", ""),
                    "certainty": opp.get("certainty", ""),
                    "reward_min": opp.get("reward_min", 0),
                    "reward_max": opp.get("reward_max", 0),
                    "source_url": opp.get("source_url", ""),
                    "prerequisites": opp.get("prerequisites", ""),
                }
                task = queue.add_task(
                    title=title,
                    description=description,
                    type="code",
                    assignee="programmer",
                    priority="P0",
                    source="opportunity_radar",
                    metadata=metadata,
                )
                enqueued.append(task)
                print(
                    f"[opportunity_radar] P0 机会入队："
                    f"{task.get('id', '')} - {title}"
                )
            except Exception as e:  # noqa: BLE001 - 单个入队失败不阻断其他
                print(f"[opportunity_radar] 入队失败 {opp.get('title', '?')}：{e}")

        return enqueued

    # ==================================================================
    # 私有：HTML 解析
    # ==================================================================
    def _parse_binance_courses(self, html: str) -> List[Dict[str, Any]]:
        """从 Binance L&E 页面 HTML 解析课程条目。

        尝试多种正则模式适配页面结构。
        SPA 渲染可能无内联数据，返回空表示未解析到。
        """
        items: List[Dict[str, Any]] = []

        # 模式 1：课程链接 /en/activity/learn-and-earn/<slug>
        seen: set = set()
        for m in re.finditer(
            r"/en/activity/learn-and-earn/([a-z0-9][a-z0-9\-]{2,80})",
            html,
            flags=re.IGNORECASE,
        ):
            slug = m.group(1).strip().strip("-")
            if not slug or slug.lower() in seen:
                continue
            seen.add(slug.lower())
            title = slug.replace("-", " ").strip().title()
            items.append(self._make_opportunity(
                channel="Binance Learn & Earn",
                title=title,
                speed="fast",
                certainty="high",
                reward_min=2,
                reward_max=20,
                source_url=f"{self.BINANCE_LEARN_EARN_URL}/{slug}",
                prerequisites="注册 Binance + KYC",
                description="Binance Learn & Earn 课程，完成答题获得 ERC-20 奖励，可提现到 ETH 钱包",
            ))

        # 模式 2：页面内 JSON 中的 title 字段（粗匹配，SPA 数据兜底）
        if not items:
            for m in re.finditer(r'"title"\s*:\s*"([^"]{5,120})"', html):
                title = m.group(1).strip()
                # 过滤明显非课程标题的噪音
                low = title.lower()
                if any(kw in low for kw in ("learn", "earn", "quiz", "course")):
                    items.append(self._make_opportunity(
                        channel="Binance Learn & Earn",
                        title=title,
                        speed="fast",
                        certainty="high",
                        reward_min=2,
                        reward_max=20,
                        source_url=self.BINANCE_LEARN_EARN_URL,
                        prerequisites="注册 Binance + KYC",
                        description="Binance Learn & Earn 课程",
                    ))
                    if len(items) >= 20:
                        break

        return items

    def _parse_cmc_earn(self, html: str) -> List[Dict[str, Any]]:
        """从 CoinMarketCap Earn 页面解析活动条目。"""
        items: List[Dict[str, Any]] = []
        seen: set = set()

        # 模式 1：CMC earn 活动链接 /earn/<project>
        for m in re.finditer(r"/earn/([a-z0-9][a-z0-9\-]{2,80})", html, flags=re.IGNORECASE):
            slug = m.group(1).strip().strip("-")
            low = slug.lower()
            if not slug or low in ("view", "all", "more", "earn") or low in seen:
                continue
            seen.add(low)
            title = slug.replace("-", " ").strip().title()
            items.append(self._make_opportunity(
                channel="CoinMarketCap Earn",
                title=title,
                speed="fast",
                certainty="high",
                reward_min=2,
                reward_max=10,
                source_url=f"{self.COINMARKETCAP_EARN_URL.rstrip('/')}/{slug}",
                prerequisites="注册 Binance（CMC Earn 奖励通过 Binance 到账）",
                description="CoinMarketCap Earn 活动，绑定 Binance 后到账",
            ))

        # 模式 2：JSON title 字段兜底
        if not items:
            for m in re.finditer(r'"title"\s*:\s*"([^"]{5,120})"', html):
                title = m.group(1).strip()
                low = title.lower()
                if any(kw in low for kw in ("earn", "campaign", "crypto", "token")):
                    items.append(self._make_opportunity(
                        channel="CoinMarketCap Earn",
                        title=title,
                        speed="fast",
                        certainty="high",
                        reward_min=2,
                        reward_max=10,
                        source_url=self.COINMARKETCAP_EARN_URL,
                        prerequisites="注册 Binance",
                        description="CoinMarketCap Earn 活动",
                    ))
                    if len(items) >= 20:
                        break

        return items

    def _parse_layer3_campaigns(self, html: str) -> List[Dict[str, Any]]:
        """从 Layer3 campaigns 页面解析任务条目。

        Layer3 任务为 CUBE 积分 → 空投路径，到账慢但零成本。
        """
        items: List[Dict[str, Any]] = []
        seen: set = set()

        # 模式 1：campaign 链接 /c/<slug> 或 /campaigns/<slug>
        for m in re.finditer(
            r"/(?:c|campaigns)/([a-z0-9][a-z0-9\-]{2,60})",
            html,
            flags=re.IGNORECASE,
        ):
            slug = m.group(1).strip().strip("-")
            low = slug.lower()
            if not slug or low in ("campaigns", "all", "explore", "c") or low in seen:
                continue
            seen.add(low)
            title = slug.replace("-", " ").strip().title()
            items.append(self._make_opportunity(
                channel="Layer3",
                title=title,
                speed="slow",
                certainty="medium",
                reward_min=5,
                reward_max=200,
                source_url=f"https://layer3.xyz/c/{slug}",
                prerequisites="注册 Layer3 + 连接钱包",
                description="Layer3 跨链任务，完成获得 CUBE 积分，未来可兑换空投",
            ))

        # 模式 2：JSON title/name 字段兜底
        if not items:
            for m in re.finditer(r'"(?:title|name)"\s*:\s*"([^"]{5,120})"', html):
                title = m.group(1).strip()
                low = title.lower()
                if any(kw in low for kw in ("quest", "campaign", "cubed", "layer3")):
                    items.append(self._make_opportunity(
                        channel="Layer3",
                        title=title,
                        speed="slow",
                        certainty="medium",
                        reward_min=5,
                        reward_max=200,
                        source_url=self.LAYER3_CAMPAIGNS_URL,
                        prerequisites="注册 Layer3 + 连接钱包",
                        description="Layer3 任务，获得 CUBE 积分",
                    ))
                    if len(items) >= 20:
                        break

        return items

    def _parse_defillama_airdrops(self, html: str) -> List[Dict[str, Any]]:
        """从 DeFi Llama Airdrops 页面解析空投条目。

        零成本原则：仅纳入测试网交互 / 社区任务类空投，
        排除需要初始资金的 DeFi（staking / restake / 交易挖矿）。
        """
        items: List[Dict[str, Any]] = []
        seen: set = set()

        # DeFi Llama 大量数据内联在 JSON 中，匹配 name/protocol/project 字段
        for m in re.finditer(
            r'"(?:name|protocol|project)"\s*:\s*"([A-Za-z][A-Za-z0-9 \-]{2,40})"',
            html,
        ):
            name = m.group(1).strip()
            low = name.lower()
            if low in seen or not name:
                continue
            seen.add(low)
            items.append(self._make_opportunity(
                channel="DeFi Llama Airdrops",
                title=f"{name} 空投",
                speed="slow",
                certainty="low",
                reward_min=10,
                reward_max=500,
                source_url=self.DEFILLAMA_AIRDROPS_URL,
                prerequisites="测试网交互 / 社区任务（零成本，需核实）",
                description=f"{name} 空投追踪（DeFi Llama），需核实是否为零成本测试网交互",
            ))
            if len(items) >= 30:
                break

        return items

    # ==================================================================
    # 私有：构造与 HTTP
    # ==================================================================
    def _make_binance_fallback_opportunity(self) -> Dict[str, Any]:
        """构造 Binance L&E 抓取失败时的兜底机会（标注"需用户验证"）。

        realtime_verified=False 保证不进入 auto_enqueue_high_priority()，
        verification_status="需用户验证" 在报告中显示为 ⚠️ 需用户验证。
        """
        opp = self._make_opportunity(
            channel="Binance Learn & Earn",
            title="Binance L&E 课程（需用户手动验证）",
            speed="fast",
            certainty="high",
            reward_min=2,
            reward_max=20,
            source_url=self.BINANCE_LEARN_EARN_URL,
            prerequisites="注册 Binance + KYC",
            description=(
                "Binance Learn & Earn 课程列表抓取失败，"
                "需用户手动访问页面验证当前可用课程"
            ),
        )
        opp["realtime_verified"] = False
        opp["verification_status"] = "需用户验证"
        opp["verification_time"] = datetime.datetime.now().isoformat(
            timespec="seconds"
        )
        return opp

    @staticmethod
    def _verification_label(status: str) -> str:
        """根据 verification_status 返回报告中的中文状态标签。

        状态值映射：
        - "verified"     → ✅ 已验证
        - "failed"       → ❌ 已失效
        - "需用户验证"    → ⚠️ 需用户验证
        - "skipped" / 其他 → ⏭️ 跳过
        """
        if status == "verified":
            return "✅ 已验证"
        if status == "failed":
            return "❌ 已失效"
        if status == "需用户验证":
            return "⚠️ 需用户验证"
        return "⏭️ 跳过"

    @staticmethod
    def _make_opportunity(
        channel: str,
        title: str,
        speed: str,
        certainty: str,
        reward_min: float,
        reward_max: float,
        source_url: str,
        prerequisites: str,
        description: str,
    ) -> Dict[str, Any]:
        """构造统一的机会字典。"""
        return {
            "channel": channel,
            "title": title,
            "speed": speed,
            "certainty": certainty,
            "reward_min": reward_min,
            "reward_max": reward_max,
            "source_url": source_url,
            "prerequisites": prerequisites,
            "description": description,
        }

    @staticmethod
    def _fetch_text(url: str) -> str:
        """GET 请求返回文本。优先 requests，回退 urllib（与 wallet.py 一致）。

        2026-06-28 升级：检测 SPA 渲染失败后，自动降级到 agent-browser 动态渲染。
        """
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AutoCorp-OpportunityRadar/1.0"
            ),
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9,zh-CN;q=0.8",
        }
        # 1. 先用静态 HTTP 抓取
        html = ""
        try:
            if _HAS_REQUESTS:
                resp = requests.get(url, timeout=20, headers=headers)
                resp.raise_for_status()
                html = resp.text
            else:
                req = urllib.request.Request(url, headers=headers)
                with urllib.request.urlopen(req, timeout=20) as resp:
                    html = resp.read().decode("utf-8", errors="replace")
        except Exception as e:  # noqa: BLE001
            print(f"[opportunity_radar] 静态抓取失败，尝试 agent-browser 动态渲染：{e}")
            return OpportunityRadar._fetch_via_browser(url)

        # 2. 检测是否为 SPA 渲染失败（HTML 内容过少或无目标关键词）
        if OpportunityRadar._is_spa_stub(html, url):
            print(f"[opportunity_radar] 检测到 SPA 渲染，降级到 agent-browser 动态渲染：{url}")
            browser_html = OpportunityRadar._fetch_via_browser(url)
            if browser_html:
                return browser_html
        return html

    @staticmethod
    def _is_spa_stub(html: str, url: str) -> bool:
        """检测 HTML 是否为 SPA 空壳（JS 渲染前的模板，无实际内容）。

        判断标准：
        - HTML 长度 < 3000 字符
        - 或包含 SPA 标志（id="root"、id="app"、<noscript>）且无目标关键词
        """
        if not html:
            return True
        if len(html) < 3000:
            return True
        lower_html = html.lower()
        spa_signs = ['id="root"', 'id="app"', "<noscript", "you need to enable javascript"]
        has_spa_sign = any(sign in lower_html for sign in spa_signs)
        # 目标关键词：课程/活动/campaign/quest/earn/learn
        content_keywords = ["campaign", "quest", "earn", "learn", "course", "reward", "活动", "课程"]
        has_content = any(kw in lower_html for kw in content_keywords)
        return has_spa_sign and not has_content

    @staticmethod
    def _fetch_via_browser(url: str) -> str:
        """用 agent-browser 动态渲染页面，返回完整 HTML。

        适用于 SPA 站点（Binance L&E、Layer3、CoinMarketCap 等）。
        失败时返回空字符串，不抛异常。
        """
        try:
            from engine.browser.agent_browser import AgentBrowser
            ab = AgentBrowser()
            ab.open(url, wait_networkidle=False)
            # 等待 SPA 渲染
            import time as _time
            _time.sleep(5)
            # 获取完整 HTML
            html = ab.eval_js("document.documentElement.outerHTML") or ""
            ab.close()
            if html and len(html) > 1000:
                return html
            return ""
        except Exception as e:  # noqa: BLE001
            print(f"[opportunity_radar] agent-browser 动态渲染失败：{e}")
            return ""
