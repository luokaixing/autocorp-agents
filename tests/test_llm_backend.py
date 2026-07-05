"""LLM 客户端多后端解析单元测试

使用标准库 unittest，可直接 `python -m unittest tests.test_llm_backend` 运行。
也兼容 pytest 风格。

测试覆盖（SubTask 1.5）：
- LLM_BACKEND=trae 时使用 TRAE 端点配置（默认值 / 环境变量覆盖）
- LLM_BACKEND=openai 且无 API_KEY 时自动回退 trae
- LLM_BACKEND=openai 且有 API_KEY 时使用 OpenAI 配置
- LLM_BACKEND=custom 时使用自定义配置；缺失 BASE_URL 时回退 trae
- 未设置 LLM_BACKEND 时默认 trae
- 未知 LLM_BACKEND 值回退 trae
- 各后端的 base_url / model / api_key 正确解析
- _ensure_client：trae 后端无 key 不抛错；openai/custom 后端无 key 抛 RuntimeError
- 大小写不敏感（LLM_BACKEND=OpenAI 等价于 openai）
- 向后兼容：DEFAULT_BASE_URL / DEFAULT_MODEL 别名仍可用
"""
import os
import unittest
from contextlib import contextmanager
from unittest.mock import patch

from engine.llm_client import LLMClient


# 所有与 LLM 后端解析相关的环境变量键，测试期间需要隔离
LLM_ENV_KEYS = [
    "LLM_BACKEND",
    "TRAE_BASE_URL", "TRAE_MODEL", "TRAE_API_KEY",
    "OPENAI_API_KEY", "OPENAI_BASE_URL", "MODEL_NAME",
    "CUSTOM_BASE_URL", "CUSTOM_API_KEY", "CUSTOM_MODEL",
]


@contextmanager
def env_vars(**kwargs):
    """临时设置 LLM 相关环境变量，测试结束后恢复原状。

    未在 kwargs 中显式给出的 LLM_* 键会被删除，确保每个用例都在
    干净的环境下运行，不受宿主环境残留变量干扰。
    """
    saved = {}
    for key in LLM_ENV_KEYS:
        saved[key] = os.environ.get(key)
        # 先全部清除，再按 kwargs 重新设置
        if key in os.environ:
            del os.environ[key]
    for key, val in kwargs.items():
        if val is not None:
            os.environ[key] = val
    try:
        yield
    finally:
        for key in LLM_ENV_KEYS:
            if saved[key] is not None:
                os.environ[key] = saved[key]
            elif key in os.environ:
                del os.environ[key]


class TestLLMBackendTrae(unittest.TestCase):
    """LLM_BACKEND=trae 的配置解析测试。"""

    def test_trae_uses_default_endpoint_when_no_env(self) -> None:
        """未覆盖任何 TRAE_* 变量时使用内置默认 base_url / model。"""
        with env_vars(LLM_BACKEND="trae"):
            client = LLMClient()
        self.assertEqual(client.backend, "trae")
        self.assertEqual(client.base_url, "https://api.trae.cn/v1")
        self.assertEqual(client.model, "trae-model")
        # 未提供 TRAE_API_KEY 时 api_key 应为 None
        self.assertIsNone(client.api_key)

    def test_trae_respects_env_overrides(self) -> None:
        """TRAE_BASE_URL / TRAE_MODEL / TRAE_API_KEY 应被正确读取。"""
        with env_vars(
            LLM_BACKEND="trae",
            TRAE_BASE_URL="https://custom-trae.example.com/v1",
            TRAE_MODEL="trae-pro",
            TRAE_API_KEY="trae-secret",
        ):
            client = LLMClient()
        self.assertEqual(client.backend, "trae")
        self.assertEqual(client.base_url, "https://custom-trae.example.com/v1")
        self.assertEqual(client.model, "trae-pro")
        self.assertEqual(client.api_key, "trae-secret")

    def test_trae_empty_api_key_treated_as_none(self) -> None:
        """TRAE_API_KEY 设为空字符串时等同于未设置（api_key=None）。"""
        with env_vars(LLM_BACKEND="trae", TRAE_API_KEY=""):
            client = LLMClient()
        self.assertIsNone(client.api_key)

    def test_default_backend_when_llm_backend_unset(self) -> None:
        """未设置 LLM_BACKEND 时默认走 trae 后端。"""
        with env_vars():  # 不传任何变量
            client = LLMClient()
        self.assertEqual(client.backend, "trae")
        self.assertEqual(client.base_url, "https://api.trae.cn/v1")
        self.assertEqual(client.model, "trae-model")

    def test_unknown_backend_falls_back_to_trae(self) -> None:
        """未知 LLM_BACKEND 值应回退到 trae。"""
        with env_vars(LLM_BACKEND="azure"):
            client = LLMClient()
        self.assertEqual(client.backend, "trae")
        self.assertEqual(client.base_url, "https://api.trae.cn/v1")

    def test_backend_is_case_insensitive(self) -> None:
        """LLM_BACKEND 取值应忽略大小写。"""
        with env_vars(LLM_BACKEND="TRAE"):
            client = LLMClient()
        self.assertEqual(client.backend, "trae")


class TestLLMBackendOpenAI(unittest.TestCase):
    """LLM_BACKEND=openai 的配置解析与回退测试。"""

    def test_openai_without_api_key_falls_back_to_trae(self) -> None:
        """LLM_BACKEND=openai 但无 OPENAI_API_KEY 时自动回退 trae。"""
        with env_vars(LLM_BACKEND="openai"):  # 未设置 OPENAI_API_KEY
            client = LLMClient()
        self.assertEqual(client.backend, "trae")
        self.assertEqual(client.base_url, "https://api.trae.cn/v1")
        self.assertEqual(client.model, "trae-model")
        self.assertIsNone(client.api_key)

    def test_openai_with_api_key_uses_openai_config(self) -> None:
        """LLM_BACKEND=openai 且配置了 OPENAI_API_KEY 时使用 OpenAI 配置。"""
        with env_vars(
            LLM_BACKEND="openai",
            OPENAI_API_KEY="sk-test-123",
            OPENAI_BASE_URL="https://api.openai.com/v1",
            MODEL_NAME="gpt-4o-mini",
        ):
            client = LLMClient()
        self.assertEqual(client.backend, "openai")
        self.assertEqual(client.base_url, "https://api.openai.com/v1")
        self.assertEqual(client.model, "gpt-4o-mini")
        self.assertEqual(client.api_key, "sk-test-123")

    def test_openai_uses_default_base_url_when_unset(self) -> None:
        """OPENAI_BASE_URL 未设置时回退到 OpenAI 默认端点。"""
        with env_vars(LLM_BACKEND="openai", OPENAI_API_KEY="sk-test"):
            client = LLMClient()
        self.assertEqual(client.backend, "openai")
        self.assertEqual(client.base_url, "https://api.openai.com/v1")
        self.assertEqual(client.model, "gpt-4o-mini")  # MODEL_NAME 也未设，用默认

    def test_openai_empty_api_key_falls_back_to_trae(self) -> None:
        """OPENAI_API_KEY 为空字符串时同样触发回退。"""
        with env_vars(LLM_BACKEND="openai", OPENAI_API_KEY=""):
            client = LLMClient()
        self.assertEqual(client.backend, "trae")
        self.assertEqual(client.base_url, "https://api.trae.cn/v1")

    def test_openai_respects_custom_base_url_and_model(self) -> None:
        """OPENAI_BASE_URL / MODEL_NAME 可指向任意 OpenAI 兼容端点。"""
        with env_vars(
            LLM_BACKEND="openai",
            OPENAI_API_KEY="sk-test",
            OPENAI_BASE_URL="https://my-proxy.example.com/v1",
            MODEL_NAME="deepseek-chat",
        ):
            client = LLMClient()
        self.assertEqual(client.backend, "openai")
        self.assertEqual(client.base_url, "https://my-proxy.example.com/v1")
        self.assertEqual(client.model, "deepseek-chat")


class TestLLMBackendCustom(unittest.TestCase):
    """LLM_BACKEND=custom 的配置解析与回退测试。"""

    def test_custom_uses_custom_config(self) -> None:
        """custom 后端应读取 CUSTOM_BASE_URL / CUSTOM_API_KEY / CUSTOM_MODEL。"""
        with env_vars(
            LLM_BACKEND="custom",
            CUSTOM_BASE_URL="https://my-llm.example.com/v1",
            CUSTOM_API_KEY="custom-key",
            CUSTOM_MODEL="my-model",
        ):
            client = LLMClient()
        self.assertEqual(client.backend, "custom")
        self.assertEqual(client.base_url, "https://my-llm.example.com/v1")
        self.assertEqual(client.model, "my-model")
        self.assertEqual(client.api_key, "custom-key")

    def test_custom_without_base_url_falls_back_to_trae(self) -> None:
        """LLM_BACKEND=custom 但未配置 CUSTOM_BASE_URL 时回退 trae。"""
        with env_vars(LLM_BACKEND="custom", CUSTOM_API_KEY="k", CUSTOM_MODEL="m"):
            client = LLMClient()
        self.assertEqual(client.backend, "trae")
        self.assertEqual(client.base_url, "https://api.trae.cn/v1")

    def test_custom_api_key_optional(self) -> None:
        """custom 后端允许不提供 API_KEY（api_key=None）。"""
        with env_vars(
            LLM_BACKEND="custom",
            CUSTOM_BASE_URL="https://my-llm.example.com/v1",
            CUSTOM_MODEL="my-model",
        ):
            client = LLMClient()
        self.assertEqual(client.backend, "custom")
        self.assertIsNone(client.api_key)


class TestEnsureClient(unittest.TestCase):
    """_ensure_client 的鉴权/占位逻辑测试。"""

    def test_trae_without_key_does_not_raise(self) -> None:
        """trae 后端无 API_KEY 时 _ensure_client 不应抛错。"""
        with env_vars(LLM_BACKEND="trae"):
            client = LLMClient()
        # 不应抛出 RuntimeError
        openai_client = client._ensure_client()
        self.assertIsNotNone(openai_client)

    def test_trae_with_key_does_not_raise(self) -> None:
        """trae 后端配置了 TRAE_API_KEY 时 _ensure_client 正常返回。"""
        with env_vars(LLM_BACKEND="trae", TRAE_API_KEY="trae-key"):
            client = LLMClient()
        openai_client = client._ensure_client()
        self.assertIsNotNone(openai_client)

    def test_openai_without_key_raises_after_fallback_is_trae(self) -> None:
        """openai 无 key 已在 __init__ 回退为 trae，_ensure_client 不会抛错。"""
        with env_vars(LLM_BACKEND="openai"):  # 无 OPENAI_API_KEY
            client = LLMClient()
        # 已回退到 trae，_ensure_client 应正常工作
        self.assertEqual(client.backend, "trae")
        openai_client = client._ensure_client()
        self.assertIsNotNone(openai_client)

    def test_openai_with_key_does_not_raise(self) -> None:
        """openai 后端配置了 API_KEY 时 _ensure_client 正常返回。"""
        with env_vars(LLM_BACKEND="openai", OPENAI_API_KEY="sk-test"):
            client = LLMClient()
        openai_client = client._ensure_client()
        self.assertIsNotNone(openai_client)

    def test_custom_without_key_raises(self) -> None:
        """custom 后端无 API_KEY 时 _ensure_client 应抛 RuntimeError。"""
        with env_vars(
            LLM_BACKEND="custom",
            CUSTOM_BASE_URL="https://my-llm.example.com/v1",
            CUSTOM_MODEL="my-model",
        ):
            client = LLMClient()
        with self.assertRaises(RuntimeError) as ctx:
            client._ensure_client()
        self.assertIn("API_KEY", str(ctx.exception))

    def test_ensure_client_caches_instance(self) -> None:
        """_ensure_client 应缓存 OpenAI 实例，多次调用返回同一对象。"""
        with env_vars(LLM_BACKEND="trae"):
            client = LLMClient()
        first = client._ensure_client()
        second = client._ensure_client()
        self.assertIs(first, second)


class TestBackwardCompat(unittest.TestCase):
    """向后兼容性测试。"""

    def test_default_base_url_alias_preserved(self) -> None:
        """DEFAULT_BASE_URL 旧属性名应仍可用（指向 OpenAI 默认端点）。"""
        self.assertEqual(LLMClient.DEFAULT_BASE_URL, "https://api.openai.com/v1")

    def test_default_model_alias_preserved(self) -> None:
        """DEFAULT_MODEL 旧属性名应仍可用（指向 gpt-4o-mini）。"""
        self.assertEqual(LLMClient.DEFAULT_MODEL, "gpt-4o-mini")

    def test_chat_interface_unchanged(self) -> None:
        """chat(system_prompt, user_message) 接口签名保持兼容。"""
        with env_vars(LLM_BACKEND="trae"):
            client = LLMClient()
        # 用 Mock 替换 _ensure_client 返回值，避免真实网络调用
        mock_response = type(
            "R", (),
            {"choices": [type("C", (), {"message": type("M", (), {"content": "ok"})()})()]}
        )()
        with patch.object(client, "_ensure_client", return_value=type(
            "Client", (),
            {"chat": type("Chat", (), {
                "completions": type("Comp", (), {
                    "create": staticmethod(lambda **kw: mock_response)
                })()
            })()}
        )()):
            result = client.chat("system", "user")
        self.assertEqual(result, "ok")

    def test_chat_messages_interface_unchanged(self) -> None:
        """chat_messages(messages, ...) 接口签名保持兼容。"""
        with env_vars(LLM_BACKEND="trae"):
            client = LLMClient()
        mock_response = type(
            "R", (),
            {"choices": [type("C", (), {"message": type("M", (), {"content": "ok2"})()})()]}
        )()
        with patch.object(client, "_ensure_client", return_value=type(
            "Client", (),
            {"chat": type("Chat", (), {
                "completions": type("Comp", (), {
                    "create": staticmethod(lambda **kw: mock_response)
                })()
            })()}
        )()):
            result = client.chat_messages([{"role": "user", "content": "hi"}])
        self.assertEqual(result, "ok2")


if __name__ == "__main__":
    unittest.main()
