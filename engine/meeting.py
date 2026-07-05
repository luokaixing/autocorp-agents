"""每日产研同步会

每天 08:00 召开，PM / CTO / Architect / CEO 四个角色依次汇报：
  1. PM 汇报需求（市场调研 + 需求清单）
  2. CTO 同步技术方向
  3. Architect 拆解任务（模块清单）
  4. CEO 决策确认（approve / reject / revise）

会议纪要写入 workspace.today_meeting_dir() / "meeting.md"。
即使 LLM 调用失败（无 API_KEY），也会优雅降级生成结构化纪要。
"""
from __future__ import annotations

import re
from datetime import datetime
from typing import Any, Dict, List

from engine.workspace import WorkspaceManager
from engine.llm_client import LLMClient, default_client


class Meeting:
    """每日产研同步会 - 每天 08:00 召开。"""

    # 会议固定时间与时区
    MEETING_TIME = "08:00"
    TIMEZONE = "Asia/Shanghai"

    def __init__(self, workspace: WorkspaceManager = None, llm_client: LLMClient = None):
        from engine.agents import ProductManager, CTO, Architect, CEO

        self.workspace = workspace or WorkspaceManager()
        self.llm_client = llm_client or default_client
        # 实例化参会角色
        self.pm = ProductManager(self.workspace, self.llm_client)
        self.cto = CTO(self.workspace, self.llm_client)
        self.architect = Architect(self.workspace, self.llm_client)
        self.ceo = CEO(self.workspace, self.llm_client)
        # 缓存当日任务清单（run() 执行后填充）
        self._tasks: List[Dict[str, Any]] = []

    # ------------------------------------------------------------------
    # 会议主流程
    # ------------------------------------------------------------------
    def run(self) -> str:
        """执行完整会议流程，返回会议纪要文件绝对路径。

        顺序：PM 汇报 → CTO 同步 → Architect 拆解 → CEO 决策 → 写纪要。
        每步独立 try/except，任一步失败均记录错误并继续，保证纪要必生成。
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 1. PM 汇报需求：市场调研 + 需求清单
        pm_report = self._step_pm_report()

        # 2. CTO 基于 PM 汇报同步技术方向
        cto_direction = self._step_cto_sync(pm_report)

        # 3. Architect 基于 PM 需求 + CTO 方向拆解模块
        arch_result = self._step_architect_design(pm_report, cto_direction)

        # 4. CEO 评审架构方案并做最终决策
        ceo_decision = self._step_ceo_decide(arch_result)

        # 从架构拆解 + CEO 决策中提取当日任务清单
        self._tasks = self._extract_tasks(arch_result, ceo_decision)

        # 写入会议纪要
        return self._write_minutes(today, pm_report, cto_direction, arch_result, ceo_decision)

    # ------------------------------------------------------------------
    # 各步骤封装（含异常降级）
    # ------------------------------------------------------------------
    def _step_pm_report(self) -> str:
        """PM 汇报：市场调研 + 需求清单。失败时返回占位文本。"""
        try:
            research = self.pm.research_market()
            requirements = self.pm.collect_requirements()
            req_text = requirements[0].get("raw_response", "") if requirements else ""
            return (
                f"【市场调研】\n{research.get('raw_response', '')}\n\n"
                f"【需求清单】\n{req_text}"
            )
        except Exception as e:
            return (
                f"（PM 汇报失败：{e}，本次使用占位内容）\n"
                f"待补充市场调研与需求清单。"
            )

    def _step_cto_sync(self, pm_report: str) -> str:
        """CTO 基于 PM 汇报设定技术方向。失败时返回占位文本。"""
        try:
            saved_path = self.cto.set_tech_direction(context=pm_report)
            # 读取已保存的技术方向文件内容
            content = self.workspace.read_text(saved_path) if saved_path else ""
            return content or "（CTO 未输出技术方向）"
        except Exception as e:
            return f"（CTO 同步失败：{e}，本次使用占位内容）\n待补充技术方向。"

    def _step_architect_design(self, pm_report: str, cto_direction: str) -> dict:
        """Architect 基于 PRD + 技术方向做架构设计。失败时返回占位结构。"""
        # 构造简化 PRD 上下文（合并 PM 汇报与 CTO 方向）
        prd = {
            "title": "autoCorp-daily",
            "problem": pm_report,
            "tech_direction": cto_direction,
        }
        try:
            return self.architect.design_architecture(prd)
        except Exception as e:
            return {
                "modules": None,
                "raw_response": (
                    f"（架构设计失败：{e}，本次使用占位内容）\n"
                    f"待补充模块拆分清单。"
                ),
                "architecture_path": "",
            }

    def _step_ceo_decide(self, arch_result: dict) -> dict:
        """CEO 评审架构方案并做最终决策。失败时返回占位结构。"""
        proposal = {
            "architecture": arch_result.get("raw_response", ""),
            "modules": arch_result.get("modules"),
        }
        try:
            return self.ceo.review_proposal(proposal)
        except Exception as e:
            return {
                "decision": "unknown",
                "reason": f"（CEO 决策失败：{e}，本次使用占位内容）\n待人工复核。",
                "raw_response": f"（CEO 决策失败：{e}）",
            }

    # ------------------------------------------------------------------
    # 任务清单提取
    # ------------------------------------------------------------------
    def _extract_tasks(self, arch_result: dict, ceo_decision: dict) -> List[Dict[str, Any]]:
        """从架构师模块清单 + CEO 决策中提取当日任务清单。

        简单实现：从架构师 raw_response 中按行匹配「- / * / 数字.」开头的任务项；
        若提取不到则生成默认任务；最后根据 CEO 决策追加一条复核任务。
        """
        tasks: List[Dict[str, Any]] = []
        raw = arch_result.get("raw_response", "") or ""

        # 匹配形如 "- xxx" / "* xxx" / "1. xxx" / "1、xxx" 的行（中文顿号后可无空格）
        for line in raw.splitlines():
            stripped = line.strip()
            if not re.match(r"^([-*]|\d+[.、)])\s*\S", stripped):
                continue
            # 去掉前缀符号，取任务描述
            desc = re.sub(r"^([-*]|\d+[.、)])\s*", "", stripped).strip()
            if not desc:
                continue
            tasks.append({
                "id": f"task-{len(tasks) + 1:03d}",
                "description": desc,
                "assignee": self._guess_assignee(desc),
                "priority": self._guess_priority(desc),
            })

        # 兜底：若一条都没提取到，给一个默认任务
        if not tasks:
            tasks.append({
                "id": "task-001",
                "description": "根据架构设计文档拆解具体开发任务",
                "assignee": "programmer",
                "priority": "high",
            })

        # 根据 CEO 决策追加一条复核任务
        decision = (ceo_decision.get("decision") or "unknown").lower()
        followup_map = {
            "approve": ("按既定方案推进开发", "programmer", "high"),
            "reject": ("根据否决意见重新调研需求", "product_manager", "medium"),
            "revise": ("根据 CEO 意见修订方案", "architect", "high"),
            "unknown": ("人工复核 CEO 决策结果", "ceo", "high"),
        }
        if decision in followup_map:
            desc, assignee, priority = followup_map[decision]
            tasks.append({
                "id": f"task-{len(tasks) + 1:03d}",
                "description": desc,
                "assignee": assignee,
                "priority": priority,
            })

        return tasks

    @staticmethod
    def _guess_assignee(desc: str) -> str:
        """根据任务描述关键词猜测负责角色。"""
        text = desc.lower()
        if "测试" in desc or "test" in text or "qa" in text:
            return "tester"
        if "运营" in desc or "推广" in desc or "营销" in desc or "growth" in text:
            return "coo"
        if "架构" in desc or "接口" in desc or "设计" in desc:
            return "architect"
        return "programmer"

    @staticmethod
    def _guess_priority(desc: str) -> str:
        """根据任务描述关键词猜测优先级。"""
        text = desc.lower()
        if "高" in desc or "紧急" in desc or "high" in text or "p0" in text or "核心" in desc:
            return "high"
        if "低" in desc or "low" in text or "p2" in text or "次要" in desc:
            return "low"
        return "medium"

    # ------------------------------------------------------------------
    # 会议纪要写入
    # ------------------------------------------------------------------
    def _write_minutes(
        self,
        today: str,
        pm_report: str,
        cto_direction: str,
        arch_result: dict,
        ceo_decision: dict,
    ) -> str:
        """生成会议纪要 markdown 并写入今日会议目录，返回文件绝对路径。"""
        meeting_dir = self.workspace.today_meeting_dir()
        meeting_path = meeting_dir / "meeting.md"

        # 拼接当日任务清单文本
        task_lines = [
            f"- [ ] {t['id']}: {t['description']} → 负责人: {t['assignee']}（{t['priority']}）"
            for t in self._tasks
        ]
        tasks_section = "\n".join(task_lines) if task_lines else "（无任务）"

        # 营收驾驶舱 - 每日自动复盘
        revenue_section = self._build_revenue_cockpit()

        # 最挣钱行业动态扫描 - 2026-06-30 战略转向后新增环节
        industry_scan_section = self._build_industry_scan()

        # 战略层任务进度（P0）- 2026-06-30 战略转向后新增摘要
        strategic_progress_section = self._build_strategic_progress()

        # 价值链切入点执行进度 - 2026-06-30 战略转向后新增独立章节
        value_chain_progress_section = self._build_value_chain_progress()

        # 可持续产品开发进度 - 2026-06-30 战略转向后新增独立章节
        sustainable_product_progress_section = self._build_sustainable_product_progress()

        content = f"""# 产研同步会纪要 - {today}

## 会议时间
{today} {self.MEETING_TIME} ({self.TIMEZONE})

## 参会人员
ProductManager, CTO, Architect, CEO

## 0. 战略层任务进度（P0，2026-06-30 战略转向后置顶）
{strategic_progress_section}

## 1. 需求汇报（ProductManager）
{pm_report}

## 2. 技术方向（CTO）
{cto_direction}

## 3. 任务拆解（Architect）
{arch_result.get('raw_response', '（无）')}

## 4. 最终决策（CEO）
决策：{ceo_decision.get('decision', 'unknown')}
理由：
{ceo_decision.get('reason', '（无）')}

## 5. 营收驾驶舱（每日必看）
{revenue_section}

## 6. 最挣钱行业动态扫描（2026-06-30 新增）
{industry_scan_section}

## 7. 价值链切入点执行进度（2026-06-30 新增）
{value_chain_progress_section}

## 8. 可持续产品开发进度（2026-06-30 新增）
{sustainable_product_progress_section}

## 当日任务清单
{tasks_section}
"""
        self.workspace.write_text(meeting_path, content)
        return str(meeting_path.resolve())

    # ------------------------------------------------------------------
    # 对外接口：返回当日任务清单
    # ------------------------------------------------------------------
    def get_tasks(self) -> list:
        """返回当日任务清单，供编排器分发。

        Returns:
            任务字典列表，每项含 id / description / assignee / priority。
            若 run() 尚未执行，返回空列表。
        """
        return list(self._tasks)

    # ------------------------------------------------------------------
    # 营收驾驶舱 - 每日自动生成营收复盘
    # ------------------------------------------------------------------
    def _build_revenue_cockpit(self) -> str:
        """生成营收驾驶舱 markdown 段落。

        包含：钱包余额、内容账本统计、当日赚钱任务建议、危机自检。
        任何子模块失败均降级为占位文本，保证会议纪要必生成。
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 1. 钱包余额查询
        wallet_line = self._fetch_wallet_balance()

        # 2. 内容账本统计
        content_stats = self._fetch_content_stats()

        # 3. 当日赚钱任务建议
        daily_tasks = self._suggest_revenue_tasks()

        # 4. 危机自检
        crisis_check = self._crisis_self_check(wallet_line, content_stats)

        return f"""### 钱包余额（{today}）
{wallet_line}

### 内容资产统计
{content_stats}

### 当日赚钱任务建议（按 ROI 排序）
{daily_tasks}

### 危机自检
{crisis_check}

> 公司第一原则：每天必须让钱包余额增加。详细策略见 company/knowledge/daily-revenue-cockpit.md
"""

    def _fetch_wallet_balance(self) -> str:
        """查询公司钱包余额。失败时返回占位文本。"""
        try:
            from engine.crypto.wallet import WalletManager
            wm = WalletManager(self.workspace)
            wallets = wm.list_wallets()
            if not wallets:
                return "（未注册钱包，无法查询余额）"

            lines = []
            for w in wallets:
                chain = w.get("chain", "")
                addr = w.get("address", "")
                bal_result = wm.check_balance(addr, chain)
                bal = bal_result.get("balance")
                unit = bal_result.get("unit", "")
                err = bal_result.get("error")
                if bal is not None:
                    lines.append(f"- {chain}: {bal} {unit} (`{addr}`)")
                else:
                    lines.append(f"- {chain}: 余额查询失败（{err}）(`{addr}`)")
            return "\n".join(lines) if lines else "（无钱包数据）"
        except Exception as e:
            return f"（钱包余额查询异常：{e}）"

    def _fetch_content_stats(self) -> str:
        """读取内容账本统计。失败时返回占位文本。"""
        try:
            import yaml
            ledger_path = self.workspace.root_dir / "config" / "content-ledger.yaml"
            if not ledger_path.exists():
                return "（内容账本未建立）"

            data = yaml.safe_load(ledger_path.read_text(encoding="utf-8")) or {}
            articles = data.get("articles", []) or []
            metrics = data.get("metrics", {}) or {}

            published = sum(1 for a in articles if a.get("status") == "published")
            ready = sum(1 for a in articles if a.get("status") == "ready_to_publish")
            draft = sum(1 for a in articles if "draft" in a.get("status", ""))

            return (
                f"- 已发布：{published} 篇\n"
                f"- 待发布：{ready} 篇\n"
                f"- 草稿：{draft} 篇\n"
                f"- 累计打赏 ETH：{metrics.get('total_tips_eth', 0)}\n"
                f"- 累计打赏 USD：{metrics.get('total_tips_usd', 0)}\n"
                f"- 累计浏览量：{metrics.get('total_views', 0)}"
            )
        except Exception as e:
            return f"（内容账本读取异常：{e}）"

    def _suggest_revenue_tasks(self) -> str:
        """生成当日赚钱任务建议清单（按 P0-P4 优先级排序）。

        2026-06-30 战略转向后重组优先级（参考 playbook v5.0）：
          - P0 战略层：价值链切入点 + 可持续产品（最优先展示）
          - P1 战术层：美国市场即时变现（原 P0 降级，仅作分发渠道）
          - P2 养号层：社交媒体账号培育，服务于 P0 产品分发
          - P3 fallback 层：低优先级兜底，资源空闲时推进
          - P4 加密支线：已证伪路径，禁止主动投入资源
        """
        today = datetime.now().strftime("%Y-%m-%d")
        return (
            f"**P0 战略层（价值链切入点 + 可持续产品，参考 playbook v5.0）**\n"
            f"- [ ] Day 1（{today}）：SaaS 选型指南英文长文系列（CRM/Help Desk/PM 三类各 1 篇，2000-2400 词，注册 G2/Capterra affiliate）\n"
            f"- [ ] Day 1（{today}）：AI 工具横向评测周报 Newsletter MVP（10 评测任务 + 多 agent 跑批 + beehiiv 上架）\n"
            f"- [ ] Day 2：Shopify 独立站 SEO 优化指南系列（技术 SEO / 内容 SEO / Page Speed 各 1 篇，注册 Shopify/Ahrefs affiliate）\n"
            f"- [ ] Day 2：CVE 漏洞周报订阅（5 agent 抓 Microsoft/Apple/Google/Adobe/Oracle CVE，beehiiv 摘要 + Gumroad 付费 $19/月）\n"
            f"- [ ] Day 3：跨境支付方案对比系列（Airwallex/Wise/Stripe/PayPal 实时费率抓取 + 3 篇对比长文）\n"
            f"- [ ] Day 3：Claude vs GPT-5 vs Gemini 实测对比系列（多 agent 跑同任务集，输出结构化对比）\n"
            f"- [ ] Day 3：独立站博客 SEO 内容代运营（service 模式，仅作 P0 兜底过渡）\n"
            f"- [ ] Day 3：跨境支付对比站 MVP（8 篇 Best X for Y 对比长文 + 周度费率抓取静态表，Vercel + Hashnode 部署）\n\n"
            f"**P1 战术层（美国市场即时变现，原 P0 降级）**\n"
            f"- [ ] Upwork/Fiverr AI 服务接单：不再作为主路径，仅用于 Newsletter/对比站流量分发\n"
            f"- [ ] 美国市场 SEO 长文残余流量变现：服务于 P0 产品导流\n\n"
            f"**P2 养号层（社交媒体账号培育，服务于 P0 产品分发）**\n"
            f"- [ ] Twitter 养号引流：每日 1-2 条推文，服务于 P0-A/P0-B 产品分发\n"
            f"- [ ] Reddit 养号引流：账号 2026-07-04 解锁后启动 r/SaaS + r/cybersecurity + r/LocalLLaMA 分发\n"
            f"- [ ] LinkedIn 企业号养号：服务于 SaaS 选型指南 B2B 分发\n\n"
            f"**P3 fallback 层（低优先级兜底，资源空闲时推进）**\n"
            f"- [ ] Paragraph 文章打赏残余流量：3 篇已发布文章持续引流，不主动投入资源\n"
            f"- [ ] Hashnode/Medium 联合发布：复用 P0-A 内容，零边际成本分发\n\n"
            f"**P4 加密支线（已证伪路径，禁止主动投入资源）**\n"
            f"- [x] Layer3 / Galxe / Binance L&E / Publish0x / Mirror.xyz / 闲鱼 / 猪八戒（详见 disproven-paths-blacklist.md）\n\n"
            f"> 战略转向依据：company/decisions/strategic-pivot-to-value-chain-entry-2026-06-30.md"
        )

    def _crisis_self_check(self, wallet_line: str, content_stats: str) -> str:
        """基于钱包+内容数据做危机自检。"""
        alerts = []

        # 钱包余额为 0 或查询失败 → 红色警报
        if "0 ETH" in wallet_line or "查询失败" in wallet_line or "异常" in wallet_line:
            alerts.append("⚠️ **钱包余额为 0 或查询失败** - 公司无现金流，今日必须推进至少 1 个即时收入渠道")

        # 已发布文章 < 3 → 黄色警报
        if "已发布：0" in content_stats or "已发布：1" in content_stats or "已发布：2" in content_stats:
            alerts.append("⚠️ **已发布文章 < 3 篇** - 内容资产不足，需加速产出")

        # 累计打赏为 0 → 提醒
        if "累计打赏 ETH：0" in content_stats:
            alerts.append("ℹ️ **累计打赏为 0** - 推广力度需加强（Twitter/Reddit）")

        if not alerts:
            alerts.append("✅ 当前无重大危机，继续推进既定计划")

        return "\n".join(alerts)

    # ------------------------------------------------------------------
    # 最挣钱行业动态扫描 - 2026-06-30 战略转向后新增环节
    # ------------------------------------------------------------------
    def _build_industry_scan(self) -> str:
        """生成"最挣钱行业动态扫描"环节 markdown。

        置于"营收驾驶舱"之后。优先调用 scanner 模块的扫描方法：
          - scanner.scan_most_profitable_industries() → Top 5 行业动态
          - scanner.scan_value_chain_entry_opportunities() → 黄金切入点 + 竞争力检查

        当 scanner 模块不可用时，降级为读取战略研究文件并检查新行业/竞争力。
        任一子步骤失败均降级为占位文本，保证会议纪要必生成。
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 1. 调用 scanner.scan_most_profitable_industries() 获取 Top 5 行业动态
        industries_result = self._scan_most_profitable_industries()

        # 2. 调用 scanner.scan_value_chain_entry_opportunities() 获取黄金切入点
        entry_result = self._scan_value_chain_entry_opportunities()

        # 3. 检查是否有新的高利润行业出现
        new_industry_alert = self._check_new_high_profit_industries(industries_result)

        # 4. 检查现有切入点是否仍有竞争力
        competitiveness_alert = self._check_entry_point_competitiveness(entry_result)

        return f"""### Top 5 最挣钱行业动态（scanner.scan_most_profitable_industries）
{industries_result}

### 黄金切入点扫描（scanner.scan_value_chain_entry_opportunities）
{entry_result}

### 新高利润行业检查
{new_industry_alert}

### 现有切入点竞争力检查
{competitiveness_alert}

数据源（2026-06-30 战略转向后必读）：
- `company/knowledge/strategic-research/most-profitable-industries-2026.md`
- `company/knowledge/strategic-research/industry-profit-pool-analysis.md`
- `company/knowledge/strategic-research/value-chain-entry-opportunities.md`
- `company/knowledge/strategic-research/sustainable-revenue-product-ideas.md`

输出：当日战略任务建议（P0 优先，价值链切入 → 可持续产品 → P1 战术 → P2 养号 → P3 fallback → P4 加密支线）
> 扫描日期：{today} | 战略转向决策：company/decisions/strategic-pivot-to-value-chain-entry-2026-06-30.md
"""

    def _scan_most_profitable_industries(self) -> str:
        """调用 scanner.scan_most_profitable_industries() 获取 Top 5 行业动态。

        优先尝试导入 engine.scanner 模块调用 scan_most_profitable_industries()；
        当 scanner 模块不存在时降级为读取 most-profitable-industries-2026.md 提取摘要。
        """
        # 优先尝试调用 scanner 模块
        try:
            from engine import scanner  # type: ignore
            if hasattr(scanner, "scan_most_profitable_industries"):
                result = scanner.scan_most_profitable_industries()
                if result:
                    return str(result)
        except Exception:
            pass  # scanner 模块不可用，降级为文件读取

        # 降级：读取战略研究文件提取 Top 5 行业
        try:
            research_dir = (
                self.workspace.root_dir
                / "knowledge"
                / "strategic-research"
            )
            file_path = research_dir / "most-profitable-industries-2026.md"
            if not file_path.exists():
                return "（最挣钱行业研究文件未找到，待补充）"

            content = file_path.read_text(encoding="utf-8")
            # 提取 Top 5 行业摘要（按已知结构匹配表格行）
            lines = []
            for line in content.splitlines():
                stripped = line.strip()
                # 匹配 Top 5 行业表格中的排名行（| 1 |、| 2 | 等）
                if stripped.startswith("| ") and any(
                    stripped.startswith(f"| {i} |") for i in range(1, 6)
                ):
                    lines.append(stripped)
            if lines:
                header = "| 排名 | 行业 | 利润率 | 增长率 | AI 可切入性 | 综合评分 |\n|------|------|--------|--------|-------------|----------|"
                return header + "\n" + "\n".join(lines)
            return "（Top 5 行业数据未提取到，请查阅 most-profitable-industries-2026.md）"
        except Exception as e:
            return f"（最挣钱行业扫描异常：{e}）"

    def _scan_value_chain_entry_opportunities(self) -> str:
        """调用 scanner.scan_value_chain_entry_opportunities() 获取黄金切入点。

        优先尝试导入 engine.scanner 模块调用 scan_value_chain_entry_opportunities()；
        当 scanner 模块不存在时降级为读取 value-chain-entry-opportunities.md 提取摘要。
        """
        # 优先尝试调用 scanner 模块
        try:
            from engine import scanner  # type: ignore
            if hasattr(scanner, "scan_value_chain_entry_opportunities"):
                result = scanner.scan_value_chain_entry_opportunities()
                if result:
                    return str(result)
        except Exception:
            pass  # scanner 模块不可用，降级为文件读取

        # 降级：读取价值链切入机会矩阵文件提取 Top 5 切入点
        try:
            research_dir = (
                self.workspace.root_dir
                / "knowledge"
                / "strategic-research"
            )
            file_path = research_dir / "value-chain-entry-opportunities.md"
            if not file_path.exists():
                return "（价值链切入机会研究文件未找到，待补充）"

            content = file_path.read_text(encoding="utf-8")
            # 提取 Top 5 切入点（按已知结构匹配）
            lines = []
            capture = False
            for line in content.splitlines():
                stripped = line.strip()
                # 定位"Top 5 切入点排序"章节
                if "Top 5" in stripped and "切入点" in stripped and "排序" in stripped:
                    capture = True
                    continue
                if capture:
                    # 匹配表格排名行
                    if stripped.startswith("| ") and any(
                        stripped.startswith(f"| {i} |") for i in range(1, 6)
                    ):
                        lines.append(stripped)
                    elif stripped.startswith("## ") and lines:
                        break  # 进入下一章节，停止捕获
            if lines:
                header = "| 排名 | 切入点 | 行业 | 启动成本 | 到账速度 |\n|------|--------|------|---------|---------|"
                return header + "\n" + "\n".join(lines)
            return "（黄金切入点数据未提取到，请查阅 value-chain-entry-opportunities.md）"
        except Exception as e:
            return f"（价值链切入机会扫描异常：{e}）"

    def _check_new_high_profit_industries(self, industries_result: str) -> str:
        """检查是否有新的高利润行业出现。

        对比当前扫描结果与已知 Top 5 行业清单，识别新出现的高利润行业。
        当无法判断时返回占位文本，保证会议纪要必生成。
        """
        known_top5 = ["SaaS", "电商跨境", "AI 应用层", "网络安全", "金融科技"]
        try:
            new_found = []
            for industry in known_top5:
                if industry not in industries_result:
                    new_found.append(f"- ⚠️ 已知行业 {industry} 未在扫描结果中，需复核")
            # 检查是否有新行业关键词出现（简化检查：含"新行业"或未在 known_top5 中的高利润关键词）
            if "新行业" in industries_result or "新兴" in industries_result:
                new_found.append("- ℹ️ 扫描结果中检测到新行业关键词，需 COO 评估是否调整 Top 5")
            if not new_found:
                return "✅ 当前 Top 5 高利润行业（SaaS / 电商跨境 / AI 应用层 / 网络安全 / 金融科技）未发生变化，无新行业出现"
            return "\n".join(new_found)
        except Exception:
            return "（新高利润行业检查降级：待 COO 在会上口述当日变化）"

    def _check_entry_point_competitiveness(self, entry_result: str) -> str:
        """检查现有切入点是否仍有竞争力。

        基于 value-chain-entry-opportunities.md 的 Top 5 切入点，检查当日是否有竞争力变化信号。
        当无法判断时返回占位文本，保证会议纪要必生成。
        """
        top5_entries = [
            "SaaS 选型指南",
            "Shopify 独立站 SEO",
            "跨境支付方案对比",
            "Claude vs",
            "独立站博客 SEO",
        ]
        try:
            missing = []
            for entry in top5_entries:
                if entry not in entry_result:
                    missing.append(f"- ⚠️ 切入点「{entry}」未在扫描结果中，需复核竞争力")
            if not missing:
                return (
                    "✅ Top 5 切入点（SaaS 选型 / Shopify SEO / 跨境支付 / AI 对比 / 独立站代运营）"
                    "均在扫描结果中，竞争力暂无重大变化信号"
                )
            return "\n".join(missing)
        except Exception:
            return "（切入点竞争力检查降级：待 COO 在会上口述当日变化）"

    # ------------------------------------------------------------------
    # 战略层任务进度（P0）- 2026-06-30 战略转向后置顶摘要
    # ------------------------------------------------------------------
    def _build_strategic_progress(self) -> str:
        """生成"战略层任务进度（P0）"摘要 markdown，置于会议纪要开头。

        优先展示价值链切入 Top 5 与可持续产品 Top 3 的进度；
        原美国市场 Upwork/Fiverr 路径降级为 P1 支撑层。
        当无进度数据可读时降级为表格占位结构，保证会议纪要必生成。
        """
        today = datetime.now().strftime("%Y-%m-%d")
        # 进度数据为手工维护（暂未接入 task_queue），先给出结构化占位 + TODO 标注
        # TODO(strategic-pivot): 后续接入 company/config/task_queue.yaml 读取
        # task_type=value_chain_entry / sustainable_product / us_market 的实时进度。
        return f"""| 任务类型 | 任务名 | 状态 | 进度 | 预期收益 |
|---------|-------|------|------|---------|
| 价值链切入 P0-A | SaaS 选型指南英文长文系列 | 待启动（Day 1: {today}） | 0% | $5-20 affiliate/篇 |
| 价值链切入 P0-A | Shopify 独立站 SEO 指南系列 | 待启动（Day 2） | 0% | $5-20 affiliate/篇 |
| 价值链切入 P0-A | 跨境支付方案对比系列 | 待启动（Day 3） | 0% | $30-150 affiliate |
| 价值链切入 P0-A | Claude/GPT-5/Gemini 实测对比系列 | 待启动（Day 3） | 0% | $5-20 affiliate |
| 价值链切入 P0-A | 独立站博客 SEO 内容代运营 | 待启动（Day 3） | 0% | $200-500/月 |
| 可持续产品 P0-B | AI 工具横向评测周报 Newsletter | MVP 待启动 | 0% | $9/月订阅 + $5-20 affiliate |
| 可持续产品 P0-B | CVE 漏洞周报订阅 | MVP 待启动 | 0% | $19/月订阅 |
| 可持续产品 P0-B | 跨境支付对比站（压缩版 MVP） | MVP 待启动 | 0% | $30-150 affiliate + $10-30 广告 |
| 旧路径 P1（降级） | 美国市场 Upwork/Fiverr AI 服务接单 | P1 支撑层 | - | 仅作分发渠道，不再 P0 |
| 旧路径 P1（降级） | Layer3 / Publish0x / 闲鱼 / 猪八戒 | 黑名单（已证伪） | - | 不再投入资源 |

> 旧战略 P0 任务已降级为 P1 支撑层；详见战略转向决策：company/decisions/strategic-pivot-to-value-chain-entry-2026-06-30.md
> 后续接入 task_queue.yaml 后此表自动填充进度（TODO 标注见 _build_strategic_progress 源码）。
"""

    # ------------------------------------------------------------------
    # 价值链切入点执行进度 - 2026-06-30 战略转向后新增独立章节
    # ------------------------------------------------------------------
    def _build_value_chain_progress(self) -> str:
        """生成"价值链切入点执行进度"独立章节 markdown。

        跟踪 Task 3 Top 5 切入点的执行状态：
          1. SaaS 选型指南英文长文系列
          2. Shopify 独立站 SEO 优化指南系列
          3. 跨境支付方案对比系列
          4. Claude vs GPT-5 vs Gemini 实测对比系列
          5. 独立站博客 SEO 内容代运营

        优先尝试从 task_queue.yaml 读取匹配任务的状态；
        当无匹配数据时降级为占位表格，保证会议纪要必生成。
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 尝试从 task_queue.yaml 读取匹配任务状态
        task_status = self._fetch_value_chain_task_status()

        return f"""| 排名 | 切入点 | 行业 | 启动日 | 状态 | 进度 | 预期收益 |
|------|--------|------|--------|------|------|---------|
| 1 | SaaS 选型指南英文长文系列 | SaaS | Day 1 ({today}) | {task_status.get('saas_selection', '待启动')} | 0% | $5-20 affiliate/篇 |
| 2 | Shopify 独立站 SEO 优化指南系列 | 电商跨境 | Day 2 | {task_status.get('shopify_seo', '待启动')} | 0% | $5-20 affiliate/篇 |
| 3 | 跨境支付方案对比系列 | 金融科技 | Day 3 | {task_status.get('cross_border_payment', '待启动')} | 0% | $30-150 affiliate |
| 4 | Claude vs GPT-5 vs Gemini 实测对比系列 | AI 应用层 | Day 3 | {task_status.get('ai_comparison', '待启动')} | 0% | $5-20 affiliate |
| 5 | 独立站博客 SEO 内容代运营 | 电商跨境 | Day 3 | {task_status.get('seo_operations', '待启动')} | 0% | $200-500/月 |

> 数据源：task_queue.yaml（task_type=value_chain_entry）+ value-chain-entry-opportunities.md Top 5 排序
> 首笔收入检查节点：Day 7（{today} + 7 天）
"""

    def _fetch_value_chain_task_status(self) -> dict:
        """从 task_queue.yaml 读取价值链切入点相关任务状态。

        匹配规则：任务标题/描述包含切入点关键词。
        当 task_queue.yaml 不存在或无匹配时返回空字典（调用方降级为"待启动"）。
        """
        try:
            import yaml
            queue_path = self.workspace.root_dir / "config" / "task_queue.yaml"
            if not queue_path.exists():
                return {}

            data = yaml.safe_load(queue_path.read_text(encoding="utf-8")) or {}
            tasks = data.get("tasks", []) or []

            # 关键词映射：切入点 → task_queue 匹配关键词
            keyword_map = {
                "saas_selection": ["SaaS 选型", "SaaS selection", "CRM"],
                "shopify_seo": ["Shopify", "SEO 优化指南"],
                "cross_border_payment": ["跨境支付", "cross-border payment", "Airwallex"],
                "ai_comparison": ["Claude vs", "GPT-5", "Gemini 实测", "AI 对比"],
                "seo_operations": ["独立站博客", "SEO 内容代运营", "SEO operations"],
            }

            status_map = {}
            for key, keywords in keyword_map.items():
                for task in tasks:
                    title = (task.get("title") or "").lower()
                    desc = (task.get("description") or "").lower()
                    if any(kw.lower() in title or kw.lower() in desc for kw in keywords):
                        status_map[key] = task.get("status", "待启动")
                        break  # 取第一个匹配

            return status_map
        except Exception:
            return {}  # 降级：返回空字典，调用方使用"待启动"占位

    # ------------------------------------------------------------------
    # 可持续产品开发进度 - 2026-06-30 战略转向后新增独立章节
    # ------------------------------------------------------------------
    def _build_sustainable_product_progress(self) -> str:
        """生成"可持续产品开发进度"独立章节 markdown。

        跟踪 Task 4 Top 3 产品的开发状态：
          1. AI 工具横向评测周报 Newsletter
          2. CVE 漏洞周报订阅
          3. 跨境支付对比站 MVP

        优先尝试从 task_queue.yaml 读取匹配任务的状态；
        当无匹配数据时降级为占位表格，保证会议纪要必生成。
        """
        today = datetime.now().strftime("%Y-%m-%d")

        # 尝试从 task_queue.yaml 读取匹配任务状态
        task_status = self._fetch_sustainable_product_task_status()

        return f"""| 排名 | 产品 | 类型 | 切入行业 | MVP 启动日 | 状态 | 进度 | 预期收益 |
|------|------|------|---------|-----------|------|------|---------|
| 1 | AI 工具横向评测周报 Newsletter | 内容资产 | AI 应用层 | Day 1 ({today}) | {task_status.get('ai_weekly', 'MVP 待启动')} | 0% | $9/月订阅 + $5-20 affiliate |
| 2 | CVE 漏洞周报订阅 | 内容资产 | 网络安全 | Day 2 | {task_status.get('cve_weekly', 'MVP 待启动')} | 0% | $19/月订阅 |
| 3 | 跨境支付对比站（压缩版 MVP） | 聚合 | 金融科技 | Day 3 | {task_status.get('payment_compare_site', 'MVP 待启动')} | 0% | $30-150 affiliate + $10-30 广告 |

> 数据源：task_queue.yaml（task_type=sustainable_product）+ sustainable-revenue-product-ideas.md Top 3 排序
> 首笔收入检查节点：Day 30（{today} + 30 天）
"""

    def _fetch_sustainable_product_task_status(self) -> dict:
        """从 task_queue.yaml 读取可持续产品相关任务状态。

        匹配规则：任务标题/描述包含产品关键词。
        当 task_queue.yaml 不存在或无匹配时返回空字典（调用方降级为"MVP 待启动"）。
        """
        try:
            import yaml
            queue_path = self.workspace.root_dir / "config" / "task_queue.yaml"
            if not queue_path.exists():
                return {}

            data = yaml.safe_load(queue_path.read_text(encoding="utf-8")) or {}
            tasks = data.get("tasks", []) or []

            # 关键词映射：产品 → task_queue 匹配关键词
            keyword_map = {
                "ai_weekly": ["AI 工具", "AI weekly", "评测周报", "Newsletter", "beehiiv"],
                "cve_weekly": ["CVE", "漏洞周报", "vulnerability weekly", "Gumroad"],
                "payment_compare_site": ["跨境支付对比站", "payment compare", "Vercel", "Hashnode"],
            }

            status_map = {}
            for key, keywords in keyword_map.items():
                for task in tasks:
                    title = (task.get("title") or "").lower()
                    desc = (task.get("description") or "").lower()
                    if any(kw.lower() in title or kw.lower() in desc for kw in keywords):
                        status_map[key] = task.get("status", "MVP 待启动")
                        break  # 取第一个匹配

            return status_map
        except Exception:
            return {}  # 降级：返回空字典，调用方使用"MVP 待启动"占位
