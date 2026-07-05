"""加密货币市场分析模块

输出机会 / 风险 / 合规边界报告，作为 AutoCorp 在加密货币赛道的市场分析能力。
- 数据来源：CoinGecko 公开 API（无需 key）
- 分析能力：基于 LLM 生成结构化报告，LLM 失败时降级为基于统计的报告
- 合规边界：明确禁止市场操纵、禁止洗钱、出币需人工确认
"""
from __future__ import annotations

import datetime
import json
from typing import Any, Dict, List, Optional

# 优先使用 requests（若已安装），否则回退到标准库 urllib.request
try:
    import requests  # type: ignore

    _HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error

    _HAS_REQUESTS = False


# CoinGecko 公开行情接口（无需 API key，国内偶发超时需翻墙）
_COINGECKO_MARKETS_URL = (
    "https://api.coingecko.com/api/v3/coins/markets"
    "?vs_currency=usd&order=market_cap_desc&per_page=20&page=1"
)

# DexScreener 公开接口（无需 API key，国内可访问，作为 CoinGecko 限流/超时降级）
# 文档：https://docs.dexscreener.com/api/reference
# 搜索接口返回各 DEX 交易对（含价格、24h 变化、流动性、交易量）
_DEXSCREENER_SEARCH_URL = "https://api.dexscreener.com/latest/dex/search?q={query}"

# DexScreener 热门搜索词（覆盖 Top 20 加密货币的主流交易对）
# 每个关键词返回多个链上的交易对，我们按流动性 + 交易量去重后取最优价格
_DEXSCREENER_TOP_QUERIES = (
    "BTC", "ETH", "USDT", "BNB", "SOL", "USDC", "XRP", "DOGE",
    "ADA", "AVAX", "TRX", "SHIB", "LINK", "DOT", "MATIC",
    "TON", "LTC", "BCH", "UNI", "ATOM",
)

# CoinGlass 公开端点（部分免 key，作为第三级降级；完整数据需注册 API key）
# 留接口位，待申请 key 后启用
_COINGLASS_API_BASE = "https://open-api-v3.coinglass.com/api"

# 机会类型白名单
_OPPORTUNITY_TYPES = (
    "arbitrage",
    "airdrop",
    "staking",
    "onchain_data",
    "stablecoin_yield",
)


class CryptoMarketAnalyzer:
    """加密货币市场分析 - 输出机会/风险/合规边界报告"""

    def __init__(self, workspace=None, llm_client=None):
        from engine.workspace import WorkspaceManager
        from engine.llm_client import default_client

        self.workspace = workspace or WorkspaceManager()
        self.llm_client = llm_client or default_client

    # ------------------------------------------------------------------
    # 数据获取（三级降级链：CoinGecko → DexScreener → 空，由上层走统计降级）
    # ------------------------------------------------------------------
    def fetch_market_data(self) -> dict:
        """拉取 Top 20 加密货币行情（三级降级）。

        降级链：
        1. CoinGecko（首选，国内偶发超时需翻墙）
        2. DexScreener（国内可访问、免 key，覆盖主流币种）
        3. 返回空 dict → 上层 _compose_report 走统计降级模式

        返回字段：symbol / name / current_price / market_cap /
                  price_change_percentage_24h / market_cap_rank / source
        """
        # Level 1: CoinGecko
        data = self._fetch_from_coingecko()
        if data and data.get("coins"):
            data["source"] = "CoinGecko"
            return data

        # Level 2: DexScreener 降级
        print("[crypto] CoinGecko 失败，降级到 DexScreener")
        data = self._fetch_from_dexscreener()
        if data and data.get("coins"):
            data["source"] = "DexScreener"
            return data

        # Level 3: 全部失败
        print("[crypto] 所有数据源均失败，将走统计降级模式")
        return {}

    def _fetch_from_coingecko(self) -> dict:
        """CoinGecko 行情（首选数据源）。失败返回 {}。"""
        try:
            if _HAS_REQUESTS:
                resp = requests.get(_COINGECKO_MARKETS_URL, timeout=15)
                resp.raise_for_status()
                raw_list: List[dict] = resp.json()
            else:
                req = urllib.request.Request(
                    _COINGECKO_MARKETS_URL,
                    headers={"User-Agent": "AutoCorp-CryptoAnalyzer/1.0"},
                )
                with urllib.request.urlopen(req, timeout=15) as resp:
                    raw_list = json.loads(resp.read().decode("utf-8"))
        except Exception as e:  # noqa: BLE001 - 网络层异常统一兜底
            print(f"[crypto] 拉取 CoinGecko 行情失败: {e}")
            return {}

        coins: List[dict] = []
        for item in raw_list[:20]:
            coins.append(
                {
                    "symbol": (item.get("symbol") or "").upper(),
                    "name": item.get("name", ""),
                    "current_price": item.get("current_price"),
                    "market_cap": item.get("market_cap"),
                    "price_change_percentage_24h": item.get(
                        "price_change_percentage_24h"
                    ),
                    "market_cap_rank": item.get("market_cap_rank"),
                }
            )
        return {
            "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "count": len(coins),
            "coins": coins,
        }

    def _fetch_from_dexscreener(self) -> dict:
        """DexScreener 行情（降级数据源，国内可访问、免 key）。

        通过搜索 BTC/ETH/SOL 等主流币种，按流动性 + 交易量去重后
        取每个 symbol 最优交易对的价格与 24h 变化。

        返回字段与 CoinGecko 保持一致（market_cap 用 fdv 估算）。
        """
        # symbol → 最优交易对（流动性最高）
        best_pairs: Dict[str, dict] = {}

        for query in _DEXSCREENER_TOP_QUERIES:
            try:
                url = _DEXSCREENER_SEARCH_URL.format(query=query)
                if _HAS_REQUESTS:
                    resp = requests.get(url, timeout=10)
                    resp.raise_for_status()
                    payload = resp.json()
                else:
                    req = urllib.request.Request(
                        url,
                        headers={"User-Agent": "AutoCorp-CryptoAnalyzer/1.0"},
                    )
                    with urllib.request.urlopen(req, timeout=10) as resp:
                        payload = json.loads(resp.read().decode("utf-8"))
            except Exception as e:  # noqa: BLE001 - 单个查询失败不阻断
                print(f"[crypto] DexScreener 查询 {query} 失败: {e}")
                continue

            pairs = payload.get("pairs") or []
            for p in pairs:
                try:
                    base = p.get("baseToken", {}) or {}
                    symbol = (base.get("symbol") or "").upper()
                    if not symbol:
                        continue

                    # 同 symbol 取流动性最高的交易对
                    liquidity_usd = (p.get("liquidity") or {}).get("usd", 0) or 0
                    if symbol in best_pairs:
                        existing_liq = best_pairs[symbol].get("liquidity_usd", 0) or 0
                        if liquidity_usd <= existing_liq:
                            continue

                    price_usd = p.get("priceUsd")
                    price_change = p.get("priceChange") or {}
                    chg_24h = price_change.get("h24")
                    volume_24h = (p.get("volume") or {}).get("h24", 0) or 0
                    fdv = p.get("fdv") or p.get("marketCap") or None

                    # 过滤明显异常数据（价格为 0 或流动性极低）
                    if not price_usd or liquidity_usd < 100000:
                        continue

                    best_pairs[symbol] = {
                        "symbol": symbol,
                        "name": base.get("name", symbol),
                        "current_price": float(price_usd),
                        "market_cap": fdv,
                        "price_change_percentage_24h": chg_24h,
                        "market_cap_rank": None,
                        "liquidity_usd": liquidity_usd,
                        "volume_24h": volume_24h,
                    }
                except Exception:  # noqa: BLE001 - 单条解析失败跳过
                    continue

            # 收集够 20 个就停止（避免请求过多）
            if len(best_pairs) >= 20:
                break

        coins = list(best_pairs.values())[:20]
        return {
            "fetched_at": datetime.datetime.now().isoformat(timespec="seconds"),
            "count": len(coins),
            "coins": coins,
        }

    # ------------------------------------------------------------------
    # 分析
    # ------------------------------------------------------------------
    def analyze(self, opportunities_focus: Optional[List[str]] = None) -> dict:
        """调用 LLM 分析市场数据，输出机会/风险/合规边界报告。

        Args:
            opportunities_focus: 机会类型白名单，可选值见 _OPPORTUNITY_TYPES。
                None 表示全部类型。

        Returns:
            {report: str, opportunities: list, raw_response: str}
        """
        market_data = self.fetch_market_data()

        # 规范化 opportunities_focus
        focus = self._normalize_focus(opportunities_focus)

        # 构造 LLM 请求
        system_prompt = self._build_system_prompt()
        user_message = self._build_user_message(market_data, focus)

        raw_response = ""
        try:
            raw_response = self.llm_client.chat(
                system_prompt, user_message, temperature=0.4, max_tokens=2500
            )
        except Exception as e:  # noqa: BLE001 - LLM 调用失败时优雅降级
            print(f"[crypto] LLM 调用失败，降级为统计报告: {e}")
            raw_response = ""

        # 解析机会清单（即使为空也继续生成报告）
        opportunities = self._extract_opportunities(raw_response, focus)

        # 生成最终报告：LLM 输出 + 合规边界 + 数据表格
        report = self._compose_report(
            market_data=market_data,
            raw_response=raw_response,
            opportunities=opportunities,
            focus=focus,
        )

        return {
            "report": report,
            "opportunities": opportunities,
            "raw_response": raw_response,
        }

    # ------------------------------------------------------------------
    # 报告落盘
    # ------------------------------------------------------------------
    def save_report(self, report: str) -> str:
        """保存报告到 company/knowledge/market-research/crypto-YYYY-MM-DD.md。

        Returns:
            文件绝对路径。
        """
        date_str = datetime.date.today().isoformat()
        filename = f"crypto-{date_str}.md"
        target_path = self.workspace.market_research_dir / filename
        self.workspace.write_text(target_path, report)
        return str(target_path.resolve())

    # ------------------------------------------------------------------
    # 完整流程
    # ------------------------------------------------------------------
    def run_full_analysis(self) -> dict:
        """完整流程：fetch_market_data → analyze → save_report。

        Returns:
            {report_path, opportunities_count, status}
        """
        try:
            result = self.analyze()
            report_path = self.save_report(result["report"])
            return {
                "report_path": report_path,
                "opportunities_count": len(result["opportunities"]),
                "status": "ok",
            }
        except Exception as e:  # noqa: BLE001 - 顶层兜底，避免 CLI 崩溃
            print(f"[crypto] 完整分析流程异常: {e}")
            return {
                "report_path": "",
                "opportunities_count": 0,
                "status": f"error: {e}",
            }

    # ==================================================================
    # 私有辅助方法
    # ==================================================================
    @staticmethod
    def _normalize_focus(focus: Optional[List[str]]) -> List[str]:
        """规范化机会聚焦列表：过滤未知类型，None 返回全部。"""
        if focus is None:
            return list(_OPPORTUNITY_TYPES)
        return [f for f in focus if f in _OPPORTUNITY_TYPES]

    def _build_system_prompt(self) -> str:
        """构造 LLM 系统提示词：角色 + 输出格式 + 合规约束。"""
        return (
            "你是 AutoCorp 的加密货币市场分析师。基于 CoinGecko 实时行情，"
            "输出机会清单、市场总览、风险提示与合规边界。\n\n"
            "【输出要求】\n"
            "1. 机会清单：每个机会包含 类型 / 描述 / 预期收益 / 风险 / 合规边界 五个字段；\n"
            "2. 市场总览：BTC、ETH 趋势与总市值变化；\n"
            "3. 风险提示：列出主要市场风险；\n"
            "4. 合规边界：明确哪些能做、哪些不能做。\n\n"
            "【合规红线 - 不可突破】\n"
            "- 禁止市场操纵：拉盘砸盘、wash trading、pump dump、价格操纵；\n"
            "- 禁止洗钱：混币、来路不明资金转移、匿名转账；\n"
            "- 出币需人工确认：任何提币/转账动作必须由人工二次确认。\n\n"
            "【输出格式】\n"
            "请用 markdown 输出。机会清单用如下 JSON 数组包裹在 ```json``` 代码块中，"
            "便于程序解析：\n"
            "```json\n"
            "[\n"
            "  {\n"
            '    "type": "arbitrage",\n'
            '    "description": "...",\n'
            '    "expected_return": "...",\n'
            '    "risk": "...",\n'
            '    "compliance_boundary": "..."\n'
            "  }\n"
            "]\n"
            "```\n"
            "随后用 markdown 正文输出市场总览、风险提示、合规边界三节。"
        )

    def _build_user_message(self, market_data: dict, focus: List[str]) -> str:
        """构造 LLM 用户消息：市场数据 + 机会聚焦。"""
        if not market_data or not market_data.get("coins"):
            return (
                "CoinGecko 行情拉取失败，无可用市场数据。"
                "请基于一般性认知输出当前主流加密货币市场的机会与风险，"
                f"机会类型聚焦：{', '.join(focus) or '全部'}。"
            )

        coins = market_data["coins"]
        # 行情表格化，便于 LLM 解析
        lines = []
        for c in coins:
            price = c.get("current_price")
            mcap = c.get("market_cap")
            chg = c.get("price_change_percentage_24h")
            lines.append(
                f"- {c.get('symbol','')} ({c.get('name','')}): "
                f"price=${price}, market_cap=${mcap}, 24h_change={chg}%"
            )
        coins_text = "\n".join(lines)

        return (
            f"【市场数据】抓取时间：{market_data.get('fetched_at','')}\n"
            f"Top {market_data.get('count', 0)} 加密货币行情：\n{coins_text}\n\n"
            f"【机会聚焦】{', '.join(focus) if focus else '全部类型'}\n\n"
            "请基于上述数据输出分析报告。"
        )

    def _extract_opportunities(
        self, raw_response: str, focus: List[str]
    ) -> List[dict]:
        """从 LLM 响应中解析 ```json``` 代码块里的机会清单。

        解析失败时返回空列表（不阻断主流程）。
        """
        if not raw_response:
            return []

        # 抓取第一个 ```json ... ``` 代码块
        start = raw_response.find("```json")
        if start == -1:
            # 兜底：尝试普通 ``` 代码块
            start = raw_response.find("```")
            if start == -1:
                return []
            end = raw_response.find("```", start + 3)
            block = raw_response[start + 3 : end] if end != -1 else ""
        else:
            end = raw_response.find("```", start + 7)
            block = raw_response[start + 7 : end] if end != -1 else ""

        block = block.strip()
        if not block:
            return []

        try:
            parsed = json.loads(block)
        except json.JSONDecodeError as e:
            print(f"[crypto] 机会清单 JSON 解析失败: {e}")
            return []

        if not isinstance(parsed, list):
            return []

        # 仅保留聚焦类型的机会；若未指定聚焦则保留全部
        opportunities: List[dict] = []
        for item in parsed:
            if not isinstance(item, dict):
                continue
            opp_type = item.get("type", "")
            if focus and opp_type not in focus:
                continue
            opportunities.append(
                {
                    "type": opp_type,
                    "description": item.get("description", ""),
                    "expected_return": item.get("expected_return", ""),
                    "risk": item.get("risk", ""),
                    "compliance_boundary": item.get("compliance_boundary", ""),
                }
            )
        return opportunities

    def _compose_report(
        self,
        market_data: dict,
        raw_response: str,
        opportunities: List[dict],
        focus: List[str],
    ) -> str:
        """组装最终 markdown 报告。

        结构：标题 + 元信息 + 行情表格 + LLM 分析（或降级统计）+ 机会清单 + 合规边界。
        """
        date_str = datetime.date.today().isoformat()
        lines: List[str] = []

        # 数据源标识（fetch_market_data 会写入 source 字段，None 表示空数据）
        source_label = market_data.get("source", "无") if market_data else "无"

        lines.append(f"# 加密货币市场分析报告 {date_str}")
        lines.append("")
        lines.append(
            f"- 生成时间：{datetime.datetime.now().isoformat(timespec='seconds')}"
        )
        lines.append(f"- 数据来源：{source_label}（三级降级：CoinGecko → DexScreener → 统计）")
        lines.append(f"- 机会聚焦：{', '.join(focus) if focus else '全部'}")
        lines.append("")

        # 行情表格
        coins = market_data.get("coins", []) if market_data else []
        if coins:
            lines.append("## Top 20 行情快照")
            lines.append("")
            lines.append("| # | Symbol | 名称 | 价格(USD) | 市值(USD) | 24h涨跌(%) |")
            lines.append("|---|--------|------|-----------|-----------|------------|")
            for idx, c in enumerate(coins, start=1):
                price = c.get("current_price")
                mcap = c.get("market_cap")
                chg = c.get("price_change_percentage_24h")
                price_str = f"{price:,.4f}" if isinstance(price, (int, float)) else "-"
                mcap_str = f"{mcap:,.0f}" if isinstance(mcap, (int, float)) else "-"
                chg_str = f"{chg:+.2f}" if isinstance(chg, (int, float)) else "-"
                lines.append(
                    f"| {idx} | {c.get('symbol','')} | {c.get('name','')} | "
                    f"{price_str} | {mcap_str} | {chg_str} |"
                )
            lines.append("")
        else:
            lines.append("## Top 20 行情快照")
            lines.append("")
            lines.append("> 行情数据获取失败，以下分析基于一般性认知。")
            lines.append("")

        # LLM 分析正文（若有）
        if raw_response:
            # 去掉已被抽取的 json 代码块，避免正文重复
            cleaned = raw_response
            start = cleaned.find("```json")
            if start != -1:
                end = cleaned.find("```", start + 7)
                if end != -1:
                    cleaned = cleaned[:start] + cleaned[end + 3 :]
            else:
                start = cleaned.find("```")
                if start != -1:
                    end = cleaned.find("```", start + 3)
                    if end != -1:
                        cleaned = cleaned[:start] + cleaned[end + 3 :]
            cleaned = cleaned.strip()
            if cleaned:
                lines.append("## LLM 分析")
                lines.append("")
                lines.append(cleaned)
                lines.append("")
        else:
            # 降级：基于数据的统计摘要
            lines.append("## 市场统计（LLM 降级模式）")
            lines.append("")
            stats = self._compute_stats(coins)
            lines.append(f"- 采样币种数：{stats['count']}")
            lines.append(
                f"- 24h 上涨数：{stats['gainers']} / 下跌数：{stats['losers']} / 平：{stats['flat']}"
            )
            lines.append(
                f"- 24h 最大涨幅：{stats['top_gainer']['symbol']} "
                f"({stats['top_gainer']['change']:+.2f}%)"
            )
            lines.append(
                f"- 24h 最大跌幅：{stats['top_loser']['symbol']} "
                f"({stats['top_loser']['change']:+.2f}%)"
            )
            btc = stats.get("btc")
            eth = stats.get("eth")
            if btc:
                lines.append(
                    f"- BTC：${btc['price']:,.2f}，24h {btc['change']:+.2f}%"
                )
            if eth:
                lines.append(
                    f"- ETH：${eth['price']:,.2f}，24h {eth['change']:+.2f}%"
                )
            lines.append("")
            lines.append("> ⚠️ LLM 调用失败，以上为基于行情的统计摘要，未做深度解读。")
            lines.append("")

        # 机会清单表格
        lines.append("## 机会清单")
        lines.append("")
        if opportunities:
            lines.append(
                "| 类型 | 描述 | 预期收益 | 风险 | 合规边界 |"
            )
            lines.append("|------|------|----------|------|----------|")
            for opp in opportunities:
                desc = str(opp.get("description", "")).replace("\n", " ")
                ret = str(opp.get("expected_return", "")).replace("\n", " ")
                risk = str(opp.get("risk", "")).replace("\n", " ")
                cb = str(opp.get("compliance_boundary", "")).replace("\n", " ")
                lines.append(
                    f"| {opp.get('type','')} | {desc} | {ret} | {risk} | {cb} |"
                )
            lines.append("")
        else:
            lines.append("> 暂无解析出的机会条目。")
            lines.append("")

        # 合规边界（强制写入，无论 LLM 是否输出）
        lines.append("## 合规边界（AutoCorp 强制约束）")
        lines.append("")
        lines.append("### ✅ 允许")
        lines.append("- 基于公开行情的市场研究与情报分析；")
        lines.append("- 参与合规交易所的现货交易、staking、空投申领；")
        lines.append("- 链上数据公开分析（不含隐私攻击）；")
        lines.append("- 稳定币收益类低风险策略评估。")
        lines.append("")
        lines.append("### ❌ 禁止")
        lines.append("- 市场操纵：拉盘砸盘、wash trading、pump dump、价格操纵；")
        lines.append("- 洗钱：混币、来路不明资金转移、匿名转账分层；")
        lines.append("- 欺诈：虚假宣传、刷量、评论操纵；")
        lines.append("- 任何涉及赌博/色情/毒品/武器/伪造证件的关联业务。")
        lines.append("")
        lines.append("### ⚠️ 需人工确认")
        lines.append("- 任何出币、提币、跨链转账动作（无论金额大小）；")
        lines.append("- 单笔出款超过 $100 的资金外流；")
        lines.append("- 新增交易所账户、托管账户或外部钱包绑定；")
        lines.append("- 任何 DeFi 合约交互（授权/质押/提取）首次执行。")
        lines.append("")

        return "\n".join(lines)

    @staticmethod
    def _compute_stats(coins: List[dict]) -> dict:
        """基于行情计算统计指标（LLM 降级时使用）。"""
        stats: Dict[str, Any] = {
            "count": len(coins),
            "gainers": 0,
            "losers": 0,
            "flat": 0,
            "top_gainer": {"symbol": "-", "change": 0.0},
            "top_loser": {"symbol": "-", "change": 0.0},
        }
        if not coins:
            return stats

        max_change = None
        min_change = None
        for c in coins:
            chg = c.get("price_change_percentage_24h")
            if not isinstance(chg, (int, float)):
                stats["flat"] += 1
                continue
            if chg > 0:
                stats["gainers"] += 1
            elif chg < 0:
                stats["losers"] += 1
            else:
                stats["flat"] += 1

            if max_change is None or chg > max_change:
                max_change = chg
                stats["top_gainer"] = {"symbol": c.get("symbol", "-"), "change": chg}
            if min_change is None or chg < min_change:
                min_change = chg
                stats["top_loser"] = {"symbol": c.get("symbol", "-"), "change": chg}

        # BTC / ETH 单独提取
        for c in coins:
            sym = (c.get("symbol") or "").upper()
            if sym == "BTC":
                stats["btc"] = {
                    "price": c.get("current_price") or 0.0,
                    "change": c.get("price_change_percentage_24h") or 0.0,
                }
            elif sym == "ETH":
                stats["eth"] = {
                    "price": c.get("current_price") or 0.0,
                    "change": c.get("price_change_percentage_24h") or 0.0,
                }
        return stats
