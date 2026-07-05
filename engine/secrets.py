"""密钥安全管理器

敏感凭证（PayPal client_secret、加密货币私钥等）隔离存储：
- 明文存于项目根的 .secrets/secrets.json（物理隔离于 company/ 工作区）
- company/config/secrets.yaml 仅存引用 ref://.secrets/secrets.json#KEY
- 永不进入 Prompt / 日志 / 日报
"""
from __future__ import annotations

import json
import os
import re
import subprocess
from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

from engine.workspace import WorkspaceManager


class SecretsManager:
    """密钥安全管理器 - 敏感凭证隔离存储，永不进入 Prompt/日志"""

    def __init__(self, workspace: WorkspaceManager | None = None) -> None:
        # 工作区管理器（默认实例指向 d:\autoCompany\company）
        self.workspace = workspace or WorkspaceManager()
        # .secrets/ 位于项目根目录（company/ 的上一级），与 company/ 工作区物理隔离
        self.project_root: Path = self.workspace.root_dir.parent
        self.secrets_dir: Path = self.project_root / ".secrets"
        # 明文存储路径
        self.secrets_json_path: Path = self.secrets_dir / "secrets.json"
        # 引用存储路径（位于工作区 config 目录，可被智能体读取以知晓有哪些密钥）
        self.secrets_yaml_path: Path = self.workspace.config_dir / "secrets.yaml"
        # 确保目录与文件就绪
        self._ensure()

    # ------------------------------------------------------------------
    # 内部辅助方法
    # ------------------------------------------------------------------
    def _ensure(self) -> None:
        """确保 .secrets/ 目录与明文文件存在，并收紧目录权限。"""
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        if not self.secrets_json_path.exists():
            self._write_json({})
        # 尝试收紧目录权限（Windows 用 icacls，失败不报错）
        self._restrict_permissions()

    def _restrict_permissions(self) -> None:
        """收紧 .secrets/ 目录权限；Windows 下用 icacls，失败静默忽略。"""
        if os.name != "nt":
            # 非 Windows：尝试 chmod 600
            try:
                self.secrets_dir.chmod(0o600)
            except OSError:
                pass
            return
        try:
            user = os.environ.get("USERNAME") or os.environ.get("USER") or ""
            # 移除继承权限，仅保留当前用户完全控制
            cmd = ["icacls", str(self.secrets_dir), "/inheritance:r"]
            if user:
                cmd = ["icacls", str(self.secrets_dir), "/inheritance:r",
                       "/grant:r", f"{user}:(OI)(CI)F"]
            subprocess.run(cmd, capture_output=True, check=False)
        except (OSError, subprocess.SubprocessError):
            # 权限设置失败不报错，保持运行
            pass

    def _read_json(self) -> Dict[str, Any]:
        """读取明文密钥 JSON；文件不存在或损坏时返回空字典。"""
        if not self.secrets_json_path.exists():
            return {}
        try:
            with self.secrets_json_path.open("r", encoding="utf-8") as f:
                data = json.load(f)
            return data if isinstance(data, dict) else {}
        except (json.JSONDecodeError, OSError):
            return {}

    def _write_json(self, data: Dict[str, Any]) -> None:
        """写入明文密钥 JSON。"""
        self.secrets_dir.mkdir(parents=True, exist_ok=True)
        with self.secrets_json_path.open("w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)

    def _read_yaml(self) -> Dict[str, Any]:
        """读取引用 YAML；不存在返回空字典。"""
        if not self.secrets_yaml_path.exists():
            return {}
        try:
            with self.secrets_yaml_path.open("r", encoding="utf-8") as f:
                data = yaml.safe_load(f)
            return data if isinstance(data, dict) else {}
        except (yaml.YAMLError, OSError):
            return {}

    def _write_yaml(self, data: Dict[str, Any]) -> None:
        """写入引用 YAML。"""
        self.workspace.ensure_dir(self.secrets_yaml_path.parent)
        with self.secrets_yaml_path.open("w", encoding="utf-8") as f:
            yaml.safe_dump(data, f, allow_unicode=True, sort_keys=False)

    def _ref(self, key: str) -> str:
        """生成 secrets.yaml 中对明文密钥的引用字符串。"""
        return f"ref://.secrets/secrets.json#{key}"

    # ------------------------------------------------------------------
    # 核心 API
    # ------------------------------------------------------------------
    def set(self, key: str, value: str) -> None:
        """写入明文到 .secrets/secrets.json，并更新 secrets.yaml 引用。"""
        data = self._read_json()
        data[key] = value
        self._write_json(data)
        # 同步引用（仅存引用，不含明文）
        refs = self._read_yaml()
        refs[key] = self._ref(key)
        self._write_yaml(refs)

    def get(self, key: str) -> Optional[str]:
        """返回真实值（供 SDK 使用，不供日志）。不存在返回 None。"""
        data = self._read_json()
        return data.get(key)

    def get_for_log(self, key: str) -> str:
        """返回脱敏占位符 [REDACTED:key]，永远不暴露明文（供日志/日报）。"""
        return f"[REDACTED:{key}]"

    def list(self) -> List[str]:
        """返回所有密钥名（不含值）。"""
        data = self._read_json()
        return list(data.keys())

    def delete(self, key: str) -> bool:
        """删除密钥。返回是否删除成功。"""
        data = self._read_json()
        if key not in data:
            return False
        del data[key]
        self._write_json(data)
        # 同步删除引用
        refs = self._read_yaml()
        refs.pop(key, None)
        self._write_yaml(refs)
        return True

    def exists(self, key: str) -> bool:
        """检查密钥是否存在。"""
        data = self._read_json()
        return key in data

    # ------------------------------------------------------------------
    # Prompt 脱敏扫描
    # ------------------------------------------------------------------
    # 敏感模式：
    #   - OpenAI key: sk- 后跟 20 个以上字母数字
    #   - PayPal 标记: paypal: 后跟非空字符（大小写不敏感）
    #   - 加密私钥: 0x 后跟 64 位十六进制
    #   - 助记词: 12 或 24 个由空格分隔的小写单词
    _PATTERN_OPENAI = re.compile(r"sk-[a-zA-Z0-9]{20,}")
    _PATTERN_PAYPAL = re.compile(r"(?i)paypal:\S+")
    _PATTERN_PRIVKEY = re.compile(r"0x[a-fA-F0-9]{64}")
    # 24 词优先匹配（避免被 12 词模式部分截断）
    _PATTERN_MNEMONIC = re.compile(
        r"\b(?:(?:[a-z]{3,8}\s+){23}[a-z]{3,8}|(?:[a-z]{3,8}\s+){11}[a-z]{3,8})\b"
    )

    @staticmethod
    def scan_prompt(prompt: str) -> str:
        """扫描文本中是否含敏感模式。

        发现敏感模式时返回脱敏后的文本（敏感片段替换为 [REDACTED]）；
        未发现则返回原文。
        """
        if not prompt:
            return prompt
        text = prompt
        text = SecretsManager._PATTERN_OPENAI.sub("[REDACTED]", text)
        text = SecretsManager._PATTERN_PAYPAL.sub("[REDACTED]", text)
        text = SecretsManager._PATTERN_PRIVKEY.sub("[REDACTED]", text)
        text = SecretsManager._PATTERN_MNEMONIC.sub("[REDACTED]", text)
        return text
