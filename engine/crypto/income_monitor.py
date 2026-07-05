"""加密货币到账监控器

实时监控 ETH 钱包余额变化，到账即触发「账本记录 + KPI 更新 + 推广强化」闭环。

设计要点：
- 复用 WalletManager 的 Blockscout 余额查询与 record_inbound 入账接口，不重新实现链上交互
- 文件即数据库：上次余额持久化到 company/config/wallet_balance_state.yaml
- 真实到账优先：仅记录链上余额「增加」产生的 delta，不模拟不预估
- 幂等性：每次检查后同步更新 last_balance 状态文件，同一笔到账不会被重复入账
- 优雅降级：每个步骤独立 try/except，余额查询失败不阻断后续流程
- 首次到账判定：last_balance 为 None 或 0 且 current > 0 → 触发里程碑写入

监控频率：每 4 小时一次（08:00 / 12:00 / 16:00 / 20:00），由 AutonomousLoop 调度。
"""
from __future__ import annotations

import datetime
from typing import Any, Dict, Optional

from engine.workspace import WorkspaceManager


# 公司打赏钱包地址（spec 中定义的 ETH 主地址）
# 优先从 wallets.yaml 读取已注册的 ethereum 钱包；未注册时回退到此默认地址
_DEFAULT_TIPPING_ADDRESS = "${ETH_TIPPING_ADDRESS}"


class IncomeMonitor:
    """钱包到账监控器：每 4 小时检查 ETH 余额，到账即触发账本+KPI+推广闭环。"""

    def __init__(self, workspace=None, llm_client=None):
        # 延迟导入避免循环依赖，与 WalletManager 自身的导入模式保持一致
        from engine.crypto.wallet import WalletManager

        self.workspace = workspace or WorkspaceManager()
        # llm_client 预留接口（spec 提及智谱 GLM 用于来源推测），当前实现不依赖 LLM
        self.llm_client = llm_client
        # 复用现有 Blockscout 余额查询与 record_inbound 入账接口
        self.wallet_manager = WalletManager(self.workspace)
        # 状态文件：company/config/wallet_balance_state.yaml
        self.state_path = self.workspace.config_dir / "wallet_balance_state.yaml"
        # 里程碑文件：company/decisions/first-income-milestone.md
        # 注意：spec 指定路径为 company/decisions/（非 company/knowledge/decisions/）
        self.milestone_path = self.workspace.root_dir / "decisions" / "first-income-milestone.md"

    # ==================================================================
    # SubTask 3.1: 主流程
    # ==================================================================
    def check_inbound(self) -> Dict[str, Any]:
        """完整到账检查流程（每 4 小时调用一次）。

        流程：
        1. 查询当前链上余额（失败优雅降级，本次直接返回）
        2. 读取上次记录的余额
        3. 计算 delta（current > last 才算收入）
        4. 判定是否首次到账（last 为 None/0 且 current > 0）
        5. 真实到账时：入账 + 更新 KPI + 首次到账写里程碑
        6. 同步状态文件（幂等：保证同一笔到账下次不再被记）

        Returns:
            {delta, current, last, is_first_income, milestone_path}
            - delta: 本次新增到账金额（ETH），无到账为 0.0
            - current: 当前链上余额（ETH），查询失败为 None
            - last: 上次记录的余额（ETH），首次运行为 None
            - is_first_income: 是否首次到账
            - milestone_path: 里程碑文件路径（仅首次到账写入，否则为空字符串）
        """
        result: Dict[str, Any] = {
            "delta": 0.0,
            "current": None,
            "last": None,
            "is_first_income": False,
            "milestone_path": "",
        }

        # 1. 查询当前链上余额（失败优雅降级，不阻断）
        current = self.fetch_current_balance()
        result["current"] = current
        if current is None:
            # 余额查询失败：本次不更新状态也不入账，等待下次轮询
            return result

        # 2. 读取上次记录余额
        last = self.load_last_balance()
        result["last"] = last

        # 3. 检测到账 delta
        delta = self.detect_inbound(current, last)
        result["delta"] = delta

        # 4. 首次到账判定（last 为 None 或 0，current > 0）
        is_first_income = (last is None or last == 0) and current > 0
        result["is_first_income"] = is_first_income

        # 5. 真实到账：入账 + KPI + 里程碑（各步骤独立降级）
        if delta > 0:
            try:
                self.record_income(delta)
            except Exception as e:  # noqa: BLE001 - 入账失败不阻断 KPI 与里程碑
                print(f"[income_monitor] record_income 失败：{e}")
            try:
                self.trigger_kpi_update(delta)
            except Exception as e:  # noqa: BLE001 - KPI 失败不阻断里程碑
                print(f"[income_monitor] trigger_kpi_update 失败：{e}")
            if is_first_income:
                try:
                    milestone = self.check_first_income_milestone(delta, current)
                    result["milestone_path"] = milestone
                except Exception as e:  # noqa: BLE001 - 里程碑失败不阻断状态更新
                    print(f"[income_monitor] check_first_income_milestone 失败：{e}")

        # 6. 更新状态文件（无论是否到账都同步最新余额，保证下次 delta 计算正确 + 幂等去重）
        try:
            self.save_last_balance(current)
        except Exception as e:  # noqa: BLE001 - 状态写入失败打印警告但不抛出
            print(f"[income_monitor] save_last_balance 失败：{e}")

        return result

    # ==================================================================
    # SubTask 3.2: 余额查询（复用 WalletManager.check_balance 的 Blockscout 实现）
    # ==================================================================
    def fetch_current_balance(self) -> Optional[float]:
        """调用 WalletManager.check_balance 查询当前 ETH 余额。

        复用现有 Blockscout（etherscan 降级）实现，不重新发起 HTTP 请求。
        失败时返回 None 并打印警告，由调用方决定是否阻断流程。

        Returns:
            余额（ETH, float）；查询失败返回 None。
        """
        address = self._get_wallet_address()
        try:
            result = self.wallet_manager.check_balance(address, "ethereum")
        except Exception as e:  # noqa: BLE001 - 网络层异常统一兜底
            print(f"[income_monitor] 余额查询异常：{e}")
            return None
        if not isinstance(result, dict) or result.get("balance") is None:
            err = result.get("error", "未知错误") if isinstance(result, dict) else "响应格式异常"
            print(f"[income_monitor] 余额查询失败：{err}")
            return None
        try:
            return float(result["balance"])
        except (TypeError, ValueError):
            print(f"[income_monitor] 余额解析失败：{result.get('balance')}")
            return None

    # ==================================================================
    # SubTask 3.3: 状态持久化（文件即数据库）
    # ==================================================================
    def load_last_balance(self) -> Optional[float]:
        """读取上次记录的余额。

        文件不存在或字段缺失返回 None（视为首次运行）。
        """
        data = self.workspace.read_yaml(self.state_path)
        if not data or not isinstance(data, dict):
            return None
        balance = data.get("last_balance")
        if balance is None:
            return None
        try:
            return float(balance)
        except (TypeError, ValueError):
            return None

    def save_last_balance(self, balance: float) -> None:
        """持久化当前余额到 company/config/wallet_balance_state.yaml。

        幂等：覆盖写入，包含 last_balance + updated_at + 钱包元信息，
        供下次 delta 计算去重，避免同一笔到账被重复入账。
        """
        data = {
            "last_balance": float(balance) if balance is not None else None,
            "chain": "ethereum",
            "address": self._get_wallet_address(),
            "updated_at": datetime.datetime.now().isoformat(timespec="seconds"),
        }
        self.workspace.write_yaml(self.state_path, data)

    # ==================================================================
    # SubTask 3.4: 到账检测
    # ==================================================================
    def detect_inbound(self, current: Optional[float], last: Optional[float]) -> float:
        """检测到账 delta。

        - current > last → 返回 delta（ETH，保留 8 位小数避免浮点误差）
        - current <= last → 返回 0.0（余额减少或不变均不视为收入）
        - last=None（首次记录）→ 返回 0.0（避免误把历史余额当作本次收入）

        Args:
            current: 当前链上余额
            last: 上次记录余额（None 表示首次运行）

        Returns:
            到账 delta（ETH），无到账返回 0.0
        """
        if current is None:
            return 0.0
        # 首次记录不视为收入（避免把已存在的余额误记为本次到账）
        if last is None:
            return 0.0
        if current > last:
            return round(current - last, 8)
        return 0.0

    # ==================================================================
    # SubTask 3.5: 入真实账本
    # ==================================================================
    def record_income(self, delta: float) -> str:
        """调用 WalletManager.record_inbound 将到账金额入真实账本。

        复用 WalletManager.record_inbound(chain, address, amount, tx_hash) 接口，
        内部调用 Ledger.income_real 标记 is_real=True，source 固定为 crypto_ethereum。

        Args:
            delta: 到账金额（ETH）

        Returns:
            账本交易 id（如 tx_001）；delta<=0 返回空字符串。
        """
        if delta <= 0:
            return ""
        address = self._get_wallet_address()
        # 余额检查拿不到链上 tx_hash，用时间戳合成唯一 tx_ref
        # （Ledger.income_real 要求 tx_ref 非空，否则抛 ValueError）
        tx_hash = f"blockscout-delta-{datetime.datetime.now().isoformat(timespec='seconds')}"
        tx_id = self.wallet_manager.record_inbound(
            chain="ethereum",
            address=address,
            amount=float(delta),
            tx_hash=tx_hash,
        )
        return tx_id

    # ==================================================================
    # SubTask 3.6: KPI 更新
    # ==================================================================
    def trigger_kpi_update(self, delta: float) -> None:
        """更新 COO 周打赏 KPI。

        role_kpi.yaml 中 coo 的 metric 为 ``weekly_tips_total``（目标 10.0$，
        tracking_source=ledger）。到账一笔即累加 1 次打赏计数；
        金额维度的真实到账已由 Ledger.income_real 记录，KPI 侧用笔数近似周打赏活跃度。

        Args:
            delta: 到账金额（ETH），delta<=0 时不记录
        """
        if delta <= 0:
            return
        from engine.agents.role_kpi import KPITracker

        tracker = KPITracker(self.workspace)
        tracker.record("coo", "weekly_tips_total", 1)

    # ==================================================================
    # SubTask 3.7: 首次到账里程碑
    # ==================================================================
    def check_first_income_milestone(self, delta: float, current: float) -> str:
        """首次到账时写 company/decisions/first-income-milestone.md。

        内容含：到账时间 / 金额 / 来源推测 / 公司第一桶金达成声明 / 后续战略调整建议。
        该文件只写一次（由 check_inbound 的 is_first_income 分支保证）。

        Args:
            delta: 到账 delta（ETH）
            current: 到账后余额（ETH）

        Returns:
            里程碑文件绝对路径字符串
        """
        now = datetime.datetime.now()
        address = self._get_wallet_address()
        source_guess = self._guess_income_source(delta)

        content = (
            f"# 第一桶金里程碑\n\n"
            f"> 公司 ETH 钱包首次收到链上打赏，标志着零成本获客闭环跑通。\n\n"
            f"## 到账信息\n\n"
            f"| 项目 | 内容 |\n"
            f"|------|------|\n"
            f"| 到账时间 | {now.isoformat(timespec='seconds')} |\n"
            f"| 钱包地址 | `{address}` |\n"
            f"| 到账金额 | {delta:.8f} ETH |\n"
            f"| 到账后余额 | {current:.8f} ETH |\n"
            f"| 来源推测 | {source_guess} |\n\n"
            f"## 公司第一桶金达成声明\n\n"
            f"自 {now.strftime('%Y-%m-%d')} 起，AutoCorp 正式获得首笔链上真实收入。\n"
            f"这证明「内容创作 + 多渠道分发 + 打赏地址引流」的零成本获客模式在 Web3 场景下成立，\n"
            f"公司从「纯虚拟运营」阶段正式迈入「真实收入回款」阶段。\n\n"
            f"## 后续战略调整建议\n\n"
            f"1. **加倍投入首发渠道**：复盘本次到账最可能的来源渠道"
            f"（Paragraph / Mirror / Twitter 引流），将该渠道内容产出频率从「每日 1 篇」"
            f"提升至「每日 2 篇」，并复用其选题模板。\n"
            f"2. **强化打赏引导**：在所有已发布文章顶部/底部固定打赏地址与感谢话术，"
            f"提升转化率。\n"
            f"3. **扩大分发面**：将同篇内容同步到 Mirror.xyz / Publish0x / Read.cash / Hive.blog，"
            f"把单点打赏升级为多点打赏矩阵。\n"
            f"4. **追踪复购**：建立打赏用户画像（地址 → 历史打赏次数 / 金额），"
            f"对重复打赏用户重点运营。\n"
            f"5. **启动空投并行赛道**：第一桶金验证了「零成本获客」可行，立即并行启动"
            f"Monad / Berachain / Layer3 测试网空投任务，把单笔打赏收入与潜在空投收益叠加。\n\n"
            f"## 后续监控\n\n"
            f"- 钱包到账监控器（`engine/crypto/income_monitor.py`）将每 4 小时检查一次余额，\n"
            f"  后续每笔到账会自动入真实账本并更新 COO 周打赏 KPI（`weekly_tips_total`）。\n"
            f"- 本里程碑文件只写一次，作为公司「从 0 到 1」的永久记录。\n"
        )

        self.workspace.write_text(self.milestone_path, content)
        return str(self.milestone_path.resolve())

    # ==================================================================
    # SubTask 3.8: 感谢打赏推文模板
    # ==================================================================
    def generate_thank_you_tweet(self, amount: float) -> str:
        """生成「感谢打赏」Twitter 推文模板。

        Args:
            amount: 到账金额（ETH）

        Returns:
            推文字符串模板
        """
        return (
            f"🎉 收到 {amount} ETH 打赏！"
            f"感谢支持，继续产出优质 Web3 内容。"
            f"#Ethereum #Web3"
        )

    # ==================================================================
    # 私有辅助方法
    # ==================================================================
    def _get_wallet_address(self) -> str:
        """获取被监控的 ETH 钱包地址。

        优先从 wallets.yaml 读取已注册的 ethereum 钱包地址；
        若未注册任何 ETH 钱包或读取失败，回退到 spec 中定义的打赏地址。
        """
        try:
            wallets = self.wallet_manager.list_wallets()
            for w in wallets:
                if w.get("chain") == "ethereum" and w.get("address"):
                    return w["address"]
        except Exception as e:  # noqa: BLE001 - 读取失败降级到默认地址
            print(f"[income_monitor] 读取 wallets.yaml 失败，使用默认地址：{e}")
        return _DEFAULT_TIPPING_ADDRESS

    @staticmethod
    def _guess_income_source(delta: float) -> str:
        """根据到账金额粗略推测来源渠道（无链上交易明细时的兜底）。

        真实来源需后续接入 Etherscan tx 明细 API 确认；当前仅按金额阈值粗分。
        """
        if delta < 0.001:
            return "测试打赏 / 空投微额（可能是 Learn & Earn 或测试网残留）"
        if delta < 0.01:
            return "内容创作打赏（Paragraph / Mirror / Publish0x 等平台）"
        if delta < 0.1:
            return "中等额打赏（可能是文章读者或社群支持者）"
        return "大额打赏 / 空投领取（建议核查 Etherscan 交易明细确认来源）"
