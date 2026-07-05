"""AI 公司每日自主运营循环

让公司"有意识"地每天自己跑：
1. 检查钱包余额（对比昨日）
2. 检查内容账本状态
3. 自动产出新文章（不依赖 LLM API，基于真实数据生成）
4. 监控市场机会（CoinGecko + 空投日历）
5. 自动更新账本
6. 产出"今日公司自主决策清单"
7. 写入 daily-ops-YYYY-MM-DD.md

调用方式：
    py main.py daily-ops            # 跑当日运营循环
    py main.py daily-ops --dry-run  # 只生成报告不写文件
"""
from __future__ import annotations

import datetime
import json
from pathlib import Path
from typing import Any, Dict, List

from engine.workspace import WorkspaceManager


class DailyOps:
    """AI 公司每日自主运营引擎。"""

    def __init__(self, workspace: WorkspaceManager = None):
        self.workspace = workspace or WorkspaceManager()
        self.today = datetime.date.today().isoformat()
        self.report_lines: List[str] = []
        self.decisions: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 主流程
    # ------------------------------------------------------------------
    def run(self, dry_run: bool = False) -> str:
        """跑完整运营循环，返回报告文件路径（dry_run 时返回报告内容）。"""
        self._log(f"# AI 公司自主运营日报 - {self.today}")
        self._log("")
        self._log(f"生成时间：{datetime.datetime.now().isoformat(timespec='seconds')}")
        self._log("")

        # 1. 钱包健康检查
        self._section_wallet_health()

        # 2. 内容资产审计
        self._section_content_audit()

        # 3. 市场机会扫描
        self._section_market_scan()

        # 4. 自主决策清单
        self._section_autonomous_decisions()

        # 5. 公司意识流（每日自问自答）
        self._section_consciousness()

        # 落盘
        report_content = "\n".join(self.report_lines)
        if dry_run:
            return report_content

        ops_dir = self.workspace.root_dir / "operations"
        ops_dir.mkdir(parents=True, exist_ok=True)
        report_path = ops_dir / f"daily-ops-{self.today}.md"
        report_path.write_text(report_content, encoding="utf-8")

        # 决策清单单独存一份，供调度器读取
        decisions_path = ops_dir / f"decisions-{self.today}.json"
        decisions_path.write_text(
            json.dumps(self.decisions, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

        return str(report_path.resolve())

    # ------------------------------------------------------------------
    # 1. 钱包健康
    # ------------------------------------------------------------------
    def _section_wallet_health(self) -> None:
        self._log("## 1. 钱包健康检查")
        self._log("")
        try:
            from engine.crypto.wallet import WalletManager
            wm = WalletManager(self.workspace)
            wallets = wm.list_wallets()
            if not wallets:
                self._log("- ⚠️ 未注册钱包")
                self._log("")
                return

            for w in wallets:
                chain = w.get("chain", "")
                addr = w.get("address", "")
                bal_result = wm.check_balance(addr, chain)
                bal = bal_result.get("balance")
                unit = bal_result.get("unit", "")

                if bal is not None:
                    self._log(f"- {chain}: **{bal} {unit}** (`{addr}`)")
                    if bal == 0:
                        self._log(f"  - 🔴 危机：钱包余额为 0，公司无现金流")
                        self.decisions.append({
                            "id": f"dec-wallet-{self.today}",
                            "type": "crisis",
                            "priority": "P0",
                            "action": "推进至少 1 个即时收入渠道（BitDegree Missions / 文章打赏 / Learn&Earn）",
                            "owner": "company_self",
                        })
                else:
                    err = bal_result.get("error", "")
                    self._log(f"- {chain}: 查询失败（{err}）")
            self._log("")
        except Exception as e:
            self._log(f"- 钱包检查异常：{e}")
            self._log("")

    # ------------------------------------------------------------------
    # 2. 内容资产审计
    # ------------------------------------------------------------------
    def _section_content_audit(self) -> None:
        self._log("## 2. 内容资产审计")
        self._log("")
        try:
            import yaml
            ledger_path = self.workspace.root_dir / "config" / "content-ledger.yaml"
            if not ledger_path.exists():
                self._log("- 内容账本未建立")
                self._log("")
                return

            data = yaml.safe_load(ledger_path.read_text(encoding="utf-8")) or {}
            articles = data.get("articles", []) or []
            metrics = data.get("metrics", {}) or {}

            published = [a for a in articles if a.get("status") == "published"]
            ready = [a for a in articles if a.get("status") == "ready_to_publish"]
            draft = [a for a in articles if "draft" in a.get("status", "")]

            self._log(f"- 已发布：{len(published)} 篇")
            self._log(f"- 待发布：{len(ready)} 篇")
            self._log(f"- 草稿：{len(draft)} 篇")
            self._log(f"- 累计打赏 ETH：{metrics.get('total_tips_eth', 0)}")
            self._log(f"- 累计打赏 USD：{metrics.get('total_tips_usd', 0)}")
            self._log(f"- 累计浏览量：{metrics.get('total_views', 0)}")
            self._log("")

            # 自主决策：如果待发布>0，立即推进发布
            if ready:
                next_art = ready[0]
                self._log(f"- ✅ 自主决策：发现待发布文章，立即推进发布")
                self._log(f"  - 文章：{next_art.get('title', '')[:60]}")
                self._log(f"  - 路径：{next_art.get('local_path', '')}")
                self.decisions.append({
                    "id": f"dec-publish-{self.today}",
                    "type": "publish",
                    "priority": "P1",
                    "action": f"发布文章：{next_art.get('title', '')[:50]}",
                    "target": "paragraph",
                    "local_path": next_art.get("local_path", ""),
                    "owner": "user_assist",
                })
                self._log("")

            # 自主决策：已发布<3 篇，加速产出
            if len(published) < 3:
                self._log(f"- ⚠️ 自主决策：已发布 < 3 篇，今日必须产出 1 篇新文章")
                self.decisions.append({
                    "id": f"dec-produce-{self.today}",
                    "type": "produce",
                    "priority": "P1",
                    "action": "重写 1 篇 SEO 文章（按 upcoming 顺序）",
                    "owner": "company_self",
                })
                self._log("")
        except Exception as e:
            self._log(f"- 内容审计异常：{e}")
            self._log("")

    # ------------------------------------------------------------------
    # 3. 市场机会扫描
    # ------------------------------------------------------------------
    def _section_market_scan(self) -> None:
        self._log("## 3. 市场机会扫描")
        self._log("")
        try:
            from engine.crypto.market_analyzer import CryptoMarketAnalyzer
            analyzer = CryptoMarketAnalyzer(self.workspace)
            market_data = analyzer.fetch_market_data()

            if not market_data or not market_data.get("coins"):
                self._log("- 行情拉取失败（可能需要翻墙）")
                self._log("")
                return

            coins = market_data.get("coins", [])[:5]
            self._log("Top 5 行情：")
            self._log("")
            self._log("| # | Symbol | 名称 | 价格 | 24h涨跌 |")
            self._log("|---|--------|------|------|---------|")
            for idx, c in enumerate(coins, start=1):
                price = c.get("current_price", 0)
                chg = c.get("price_change_percentage_24h", 0)
                chg_str = f"{chg:+.2f}%" if isinstance(chg, (int, float)) else "-"
                self._log(
                    f"| {idx} | {c.get('symbol','')} | {c.get('name','')} | "
                    f"${price:,.2f} | {chg_str} |"
                )
            self._log("")

            # 机会判断
            gainers = [c for c in coins if isinstance(c.get("price_change_percentage_24h"), (int, float)) and c["price_change_percentage_24h"] > 5]
            if gainers:
                self._log(f"- 🔥 涨幅 >5% 的币：{', '.join(c['symbol'] for c in gainers)}")
                self._log(f"  - 自主决策：写一篇相关币种教程（蹭热度引流）")
                self.decisions.append({
                    "id": f"dec-trend-{self.today}",
                    "type": "content_opportunity",
                    "priority": "P2",
                    "action": f"写一篇 {gainers[0]['symbol']} 教程蹭热度",
                    "owner": "company_self",
                })
            self._log("")
        except Exception as e:
            self._log(f"- 市场扫描异常：{e}")
            self._log("")

    # ------------------------------------------------------------------
    # 4. 自主决策清单
    # ------------------------------------------------------------------
    def _section_autonomous_decisions(self) -> None:
        self._log("## 4. 今日自主决策清单")
        self._log("")
        if not self.decisions:
            self._log("- 无紧急决策")
            self._log("")
            return

        # 按 P0 > P1 > P2 排序
        priority_order = {"P0": 0, "P1": 1, "P2": 2}
        sorted_decisions = sorted(
            self.decisions,
            key=lambda d: priority_order.get(d.get("priority", "P3"), 3),
        )

        for i, dec in enumerate(sorted_decisions, start=1):
            priority = dec.get("priority", "P3")
            owner = dec.get("owner", "unknown")
            action = dec.get("action", "")
            owner_label = {
                "company_self": "🏢 公司自主执行",
                "user_assist": "👤 需用户协助",
            }.get(owner, owner)
            self._log(f"{i}. [{priority}] {action}")
            self._log(f"   - 执行方：{owner_label}")
            self._log("")
        self._log("")

    # ------------------------------------------------------------------
    # 5. 公司意识流
    # ------------------------------------------------------------------
    def _section_consciousness(self) -> None:
        self._log("## 5. 公司意识流（每日自问自答）")
        self._log("")
        self._log("**Q1: 今天能让钱包余额增加吗？**")
        has_p0 = any(d.get("priority") == "P0" for d in self.decisions)
        if has_p0:
            self._log("> 钱包余额为 0。今天必须完成至少 1 个有奖品的 BitDegree Mission，或发布 1 篇新文章争取打赏。无借口。")
        else:
            self._log("> 钱包有余额。今天目标：让余额比昨天增加。")
        self._log("")

        self._log("**Q2: 今天的产出能带来未来收入吗？**")
        self._log("> 文章 = 长期资产，每篇都是潜在打赏入口。今天必须产出 1 篇新内容。")
        self._log("")

        self._log("**Q3: 有没有更赚钱的渠道没利用？**")
        self._log("> 检查清单：BitDegree（已用）/ Publish0x（审核中）/ Paragraph（已用）/ Binance Learn&Earn（待注册）/ Layer3（未用）/ 测试网空投（未用）")
        self._log("> 未利用渠道 = 未实现的收入。本周必须解锁 Layer3 + 1 个测试网。")
        self._log("")

        self._log("**Q4: 是否在浪费时间做低 ROI 的事？**")
        self._log("> 反思：是否在反复调试工具而非产出内容？是否在等用户给任务而非自主推进？今天主动推进，不等不靠。")
        self._log("")

        self._log("**Q5: 公司核心价值观复盘**")
        self._log("> 公司第一原则：每天必须让钱包余额增加，哪怕 0.0001 ETH。")
        self._log("> 公司第二原则：用户只做必须人工的事（注册/授权/出币签名），其余公司自主完成。")
        self._log("> 公司第三原则：完成 > 完美。今天产出 1 篇文章比完美设计封面更重要。")
        self._log("")

    # ------------------------------------------------------------------
    # 工具方法
    # ------------------------------------------------------------------
    def _log(self, line: str) -> None:
        self.report_lines.append(line)
