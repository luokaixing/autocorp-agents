"""加密货币钱包管理模块

公钥对外公布，私钥隔离存于 .secrets/。
- 公钥（地址、创建时间）存 company/config/wallets.yaml
- 私钥通过 SecretsManager 存 .secrets/secrets.json（永不进入 wallets.yaml / 日志 / Prompt）
- 地址生成采用简化实现（hashlib + secrets 标准库），不引入 web3 等重依赖

注意：地址派生为简化实现，不适用于真实资金托管；真实托管需接入硬件钱包 / HSM。
"""
from __future__ import annotations

import datetime
import hashlib
import json
import secrets as _secrets
from typing import Any, Dict, List, Tuple

# 优先使用 requests（若已安装），否则回退到标准库 urllib.request
try:
    import requests  # type: ignore

    _HAS_REQUESTS = True
except ImportError:
    import urllib.request
    import urllib.error

    _HAS_REQUESTS = False


# 支持的链
_SUPPORTED_CHAINS = ("bitcoin", "ethereum", "tron", "solana")


class WalletManager:
    """加密货币钱包管理 - 公钥对外，私钥隔离"""

    def __init__(self, workspace=None):
        from engine.workspace import WorkspaceManager
        from engine.secrets import SecretsManager
        self.workspace = workspace or WorkspaceManager()
        self.secrets = SecretsManager(self.workspace)
        self.wallets_path = self.workspace.config_dir / "wallets.yaml"

    # ------------------------------------------------------------------
    # 钱包注册
    # ------------------------------------------------------------------
    def register_wallet(self, chain: str) -> Dict[str, Any]:
        """注册新钱包：生成密钥对，公钥写 wallets.yaml，私钥写 .secrets/。

        Args:
            chain: 链名 bitcoin/ethereum/tron/solana

        Returns:
            {chain, address, created_at}（不返回私钥，私钥仅存 secrets）
        """
        if chain not in _SUPPORTED_CHAINS:
            raise ValueError(
                f"不支持的链: {chain}，支持: {', '.join(_SUPPORTED_CHAINS)}"
            )

        private_key, address = self._generate_keypair(chain)
        created_at = datetime.datetime.now().isoformat(timespec="seconds")

        # 1. 公钥信息写入 wallets.yaml
        data = self._load_wallets()
        wallets: List[Dict[str, Any]] = data.get("wallets") or []
        wallets.append(
            {
                "chain": chain,
                "address": address,
                "created_at": created_at,
            }
        )
        self.workspace.write_yaml(self.wallets_path, {"wallets": wallets})

        # 2. 私钥写入 .secrets/（通过 SecretsManager，永不进入 wallets.yaml）
        # 用地址片段作为 secret key 后缀，便于与公钥记录对应
        addr_short = self._addr_short(address)
        secret_key = f"wallet_{chain}_{addr_short}_priv"
        self.secrets.set(secret_key, private_key)

        # 私钥绝不返回
        return {
            "chain": chain,
            "address": address,
            "created_at": created_at,
        }

    # ------------------------------------------------------------------
    # 钱包列表
    # ------------------------------------------------------------------
    def list_wallets(self) -> List[Dict[str, Any]]:
        """返回所有钱包公钥信息（chain, address, created_at），不返回私钥。"""
        data = self._load_wallets()
        wallets = data.get("wallets") or []
        # 仅返回公钥字段，确保不泄露任何敏感信息
        return [
            {
                "chain": w.get("chain", ""),
                "address": w.get("address", ""),
                "created_at": w.get("created_at", ""),
            }
            for w in wallets
        ]

    # ------------------------------------------------------------------
    # 余额查询
    # ------------------------------------------------------------------
    def check_balance(self, address: str, chain: str) -> Dict[str, Any]:
        """调用公开区块链浏览器 API 查询余额。

        - ethereum: etherscan 免费基础查询
        - bitcoin: blockchain.info q 接口
        - 网络失败返回 {balance: None, error: "..."}
        - 返回 {chain, address, balance, unit}
        """
        if chain == "ethereum":
            return self._balance_ethereum(address)
        if chain == "bitcoin":
            return self._balance_bitcoin(address)
        # tron / solana 未接入公开 API
        return {
            "chain": chain,
            "address": address,
            "balance": None,
            "unit": "",
            "error": f"{chain} 余额查询暂未实现",
        }

    def _balance_ethereum(self, address: str) -> Dict[str, Any]:
        """查询以太坊地址余额。

        优先用 etherscan 免费接口，被限流时降级到 Blockscout（无需 key）。
        新地址余额为 0 也正常返回，不当作错误。
        """
        # 先尝试 etherscan
        url = (
            "https://api.etherscan.io/api"
            "?module=account&action=balance"
            f"&address={address}&tag=latest"
        )
        try:
            payload = self._http_get_json(url)
        except Exception as e:  # noqa: BLE001 - 网络层异常统一兜底
            return self._balance_ethereum_blockscout(address, f"etherscan 请求失败: {e}")

        if not isinstance(payload, dict):
            return self._balance_ethereum_blockscout(address, "etherscan 响应解析失败")

        # etherscan 返回 {status, message, result}，result 为 Wei 字符串
        # status="0" + message="NOTOK" 通常是限流（无 API key），降级到 blockscout
        if payload.get("status") != "1":
            msg = payload.get("message", "")
            if "NOTOK" in str(msg).upper() or "rate" in str(msg).lower():
                return self._balance_ethereum_blockscout(address, f"etherscan 限流: {msg}")
            # 真实业务错误（如地址无效）才返回失败
            return {
                "chain": "ethereum",
                "address": address,
                "balance": None,
                "unit": "ETH",
                "error": msg or "查询失败",
            }
        try:
            wei = int(payload.get("result", "0"))
            eth = wei / 10**18
        except (TypeError, ValueError):
            return {
                "chain": "ethereum",
                "address": address,
                "balance": None,
                "unit": "ETH",
                "error": "余额解析失败",
            }
        return {
            "chain": "ethereum",
            "address": address,
            "balance": eth,
            "unit": "ETH",
        }

    def _balance_ethereum_blockscout(self, address: str, fallback_reason: str = "") -> Dict[str, Any]:
        """Blockscout 免 key 接口作为 etherscan 降级方案。

        使用 Blockscout v1 JSON-RPC 风格 API（兼容 Etherscan 格式但免 key）：
        https://eth.blockscout.com/api?module=account&action=balance&address=xxx
        返回 {status, message, result}，result 为 Wei 字符串。
        """
        url = (
            "https://eth.blockscout.com/api"
            "?module=account&action=balance"
            f"&address={address}&tag=latest"
        )
        try:
            payload = self._http_get_json(url)
        except Exception as e:  # noqa: BLE001
            return {
                "chain": "ethereum",
                "address": address,
                "balance": None,
                "unit": "ETH",
                "error": f"Blockscout 请求失败（{fallback_reason}）: {e}",
            }

        if not isinstance(payload, dict):
            return {
                "chain": "ethereum",
                "address": address,
                "balance": None,
                "unit": "ETH",
                "error": f"Blockscout 响应解析失败（{fallback_reason}）",
            }

        # Blockscout v1 返回 {status, message, result}
        if payload.get("status") != "1":
            msg = payload.get("message", "")
            return {
                "chain": "ethereum",
                "address": address,
                "balance": None,
                "unit": "ETH",
                "error": f"Blockscout 查询失败（{fallback_reason}）: {msg}",
            }
        try:
            wei_str = payload.get("result", "0")
            # 可能是字符串或数字，统一处理
            wei_str = str(wei_str).split(".")[0]
            wei = int(wei_str)
            eth = wei / 10**18
            return {
                "chain": "ethereum",
                "address": address,
                "balance": eth,
                "unit": "ETH",
            }
        except (TypeError, ValueError):
            return {
                "chain": "ethereum",
                "address": address,
                "balance": None,
                "unit": "ETH",
                "error": f"Blockscout 余额解析失败（{fallback_reason}）",
            }

    def _balance_bitcoin(self, address: str) -> Dict[str, Any]:
        url = f"https://blockchain.info/q/addressbalance/{address}"
        try:
            text = self._http_get_text(url)
        except Exception as e:  # noqa: BLE001 - 网络层异常统一兜底
            return {
                "chain": "bitcoin",
                "address": address,
                "balance": None,
                "unit": "BTC",
                "error": f"网络请求失败: {e}",
            }
        try:
            satoshi = int(text.strip())
            btc = satoshi / 10**8
        except (TypeError, ValueError):
            return {
                "chain": "bitcoin",
                "address": address,
                "balance": None,
                "unit": "BTC",
                "error": "余额解析失败",
            }
        return {
            "chain": "bitcoin",
            "address": address,
            "balance": btc,
            "unit": "BTC",
        }

    # ------------------------------------------------------------------
    # 入账记录
    # ------------------------------------------------------------------
    def record_inbound(
        self, chain: str, address: str, amount: float, tx_hash: str
    ) -> str:
        """记录加密货币入账到真实账本。

        调用 Ledger.income_real 入真实账，返回交易 id。
        """
        from engine.ledger import Ledger
        ledger = Ledger(self.workspace)
        tx_id = ledger.income_real(
            amount=amount,
            source=f"crypto_{chain}",
            tx_ref=tx_hash,
            description=f"加密货币入账 {chain}",
        )
        return tx_id

    # ==================================================================
    # 私有辅助方法
    # ==================================================================
    def _load_wallets(self) -> Dict[str, Any]:
        """读取 wallets.yaml；不存在返回空结构。"""
        data = self.workspace.read_yaml(self.wallets_path)
        if not data or not isinstance(data, dict):
            return {"wallets": []}
        if "wallets" not in data:
            data["wallets"] = []
        return data

    @staticmethod
    def _addr_short(address: str) -> str:
        """从地址提取短标识用于 secret key 命名（去掉链前缀，取 8 位 hex）。"""
        cleaned = address.lower()
        for prefix in ("0x", "t"):
            if cleaned.startswith(prefix):
                cleaned = cleaned[len(prefix):]
        return cleaned[:8]

    @staticmethod
    def _generate_keypair(chain: str) -> Tuple[str, str]:
        """生成真实可用的密钥对（私钥, 地址）。

        ethereum / tron: 使用 eth-account 官方库（keccak256 派生真实地址）
        bitcoin / solana: 暂用 hashlib 派生（仅演示，不能真实收款）

        Args:
            chain: 链名 bitcoin/ethereum/tron/solana

        Returns:
            (private_key_hex, address)

        Raises:
            ValueError: 不支持的链
        """
        if chain == "ethereum":
            # 真实 ETH 钱包：eth-account 官方库
            # 私钥 → secp256k1 公钥 → keccak256 → 取后 20 字节 → 0x 前缀
            try:
                from eth_account import Account
                acct = Account.create()
                private_key = acct.key.hex()
                address = acct.address
                return private_key, address
            except ImportError:
                raise RuntimeError(
                    "ETH 钱包生成需要 eth-account 库，请运行: pip install eth-account"
                )

        if chain == "tron":
            # Tron 地址 = ETH 地址前缀替换（20 字节地址 → base58 编码 + T 前缀）
            # 真实实现需要 base58 check 编码，这里用 eth-account 生成后转换
            try:
                from eth_account import Account
                import base58
                acct = Account.create()
                private_key = acct.key.hex()
                # Tron 地址：0x41 前缀 + 20 字节地址 + 4 字节校验码，base58 编码
                eth_addr_bytes = bytes.fromhex(acct.address[2:])
                tron_addr_bytes = b'\x41' + eth_addr_bytes
                # 计算校验码（双 sha256 前 4 字节）
                checksum = hashlib.sha256(hashlib.sha256(tron_addr_bytes).digest()).digest()[:4]
                address = base58.b58encode(tron_addr_bytes + checksum).decode('utf-8')
                return private_key, address
            except ImportError:
                raise RuntimeError(
                    "Tron 钱包生成需要 eth-account + base58 库，请运行: pip install eth-account base58"
                )

        # bitcoin / solana: 暂用简化派生（仅演示，不可真实收款）
        # TODO: 接入 bitcoinlib / py-solana-sdk 实现真实地址
        private_key = _secrets.token_hex(32)
        if chain == "bitcoin":
            digest = hashlib.sha256(bytes.fromhex(private_key)).hexdigest()
            address = "1" + digest[:50]
        elif chain == "solana":
            digest = hashlib.sha256(bytes.fromhex(private_key)).hexdigest()
            address = digest[:64]
        else:
            raise ValueError(f"不支持的链: {chain}")

        return private_key, address

    @staticmethod
    def _http_get_json(url: str) -> Any:
        """GET 请求并解析 JSON。优先 requests，回退 urllib。"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutoCorp-WalletManager/1.0",
            "Accept": "application/json",
        }
        if _HAS_REQUESTS:
            resp = requests.get(url, timeout=15, headers=headers)
            resp.raise_for_status()
            return resp.json()
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return json.loads(resp.read().decode("utf-8"))

    @staticmethod
    def _http_get_text(url: str) -> str:
        """GET 请求并返回文本。"""
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AutoCorp-WalletManager/1.0",
        }
        if _HAS_REQUESTS:
            resp = requests.get(url, timeout=15, headers=headers)
            resp.raise_for_status()
            return resp.text
        req = urllib.request.Request(url, headers=headers)
        with urllib.request.urlopen(req, timeout=15) as resp:
            return resp.read().decode("utf-8")
