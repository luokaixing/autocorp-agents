"""LLM 客户端抽象层

封装 OpenAI 兼容接口（chat/completions），支持 TRAE 内置模型 / OpenAI / 其他兼容端点。
所有虚拟员工智能体统一通过此客户端调用 LLM，屏蔽底层 SDK 差异并提供错误重试。

配置来源（优先级从高到低）：
    1. 环境变量直接覆盖（无需 .env 文件即可工作）
    2. .env 文件中的配置（由 python-dotenv 加载）
    3. 内置默认值

后端选择：
    通过环境变量 LLM_BACKEND 指定，取值 trae | openai | custom，默认 trae。
    - trae：使用 TRAE 内置模型端点，无需自备 API_KEY 即可调用（端点自行决定是否鉴权）。
    - openai：使用 OpenAI 兼容接口，需要 OPENAI_API_KEY；缺失时自动回退到 trae。
    - custom：用户自定义 BASE_URL / API_KEY / MODEL；缺失 BASE_URL 时回退到 trae。

降级链（2026-06-28 升级）：
    TRAE API 调用失败（404/超时）→ 自动降级到 TraeBridge 文件队列
    TraeBridge 通过文件让 TRAE IDE 内置 AI（GLM-5.2）处理请求，无需 API key
"""
import os
import time

from dotenv import load_dotenv
from openai import OpenAI, APIError, APIConnectionError, RateLimitError


class LLMClient:
    """LLM 客户端：封装 OpenAI 兼容 chat/completions 接口。

    设计要点：
        - 模块加载 / 实例化时不强制要求 API_KEY，延迟到 chat() 调用时才检查，
          以便在未配置密钥的环境下也能正常导入本模块。
        - OpenAI 客户端延迟创建，避免无密钥时产生告警。
        - 网络错误 / API 错误自动重试，递增间隔退避。
        - 默认走 TRAE 内置模型端点，无需自备 API_KEY 即可运营公司。
    """

    # 后端类型常量
    BACKEND_TRAE = "trae"
    BACKEND_OPENAI = "openai"
    BACKEND_CUSTOM = "custom"

    # TRAE 后端默认配置（内置模型端点，通常无需修改）
    TRAE_DEFAULT_BASE_URL = "https://api.trae.cn/v1"
    # 默认模型：GLM-5.2（由用户在公司工作约定中指定）
    TRAE_DEFAULT_MODEL = "glm-5.2"

    # OpenAI 后端默认配置
    OPENAI_DEFAULT_BASE_URL = "https://api.openai.com/v1"
    OPENAI_DEFAULT_MODEL = "gpt-4o-mini"

    # 向后兼容别名：保留旧属性名，避免外部脚本引用断裂
    DEFAULT_BASE_URL = OPENAI_DEFAULT_BASE_URL
    DEFAULT_MODEL = OPENAI_DEFAULT_MODEL

    # 重试配置：1 次初始尝试 + 3 次重试，间隔递增（1s, 2s, 4s）
    MAX_RETRIES = 3
    RETRY_BACKOFF = [1, 2, 4]  # 每次重试前的等待秒数

    def __init__(self):
        # 加载 .env 文件（若存在）；override=False 表示不覆盖已存在的环境变量，
        # 从而支持通过环境变量直接覆盖 .env 中的配置。
        load_dotenv(override=False)
        # 解析后端配置：选择实际使用的后端及对应的 base_url / model / api_key
        self.backend, self.base_url, self.model, self.api_key = self._resolve_backend()
        # OpenAI 客户端延迟创建
        self._client = None

    def _resolve_backend(self):
        """根据环境变量解析后端配置，并处理自动回退逻辑。

        回退规则：
            - LLM_BACKEND=openai 但未配置 OPENAI_API_KEY → 回退 trae
            - LLM_BACKEND=custom 但未配置 CUSTOM_BASE_URL → 回退 trae
            - 未知 LLM_BACKEND 值 → 视为 trae

        Returns:
            Tuple[backend, base_url, model, api_key]：实际使用的后端配置。
        """
        backend = (os.getenv("LLM_BACKEND") or self.BACKEND_TRAE).strip().lower()

        if backend == self.BACKEND_OPENAI:
            api_key = os.getenv("OPENAI_API_KEY")
            # OpenAI 后端缺失 API_KEY 时自动回退到 trae，避免无法调用
            if not api_key:
                print("[llm_client] LLM_BACKEND=openai 但未配置 OPENAI_API_KEY，自动回退到 trae 后端")
                return self._resolve_trae()
            base_url = os.getenv("OPENAI_BASE_URL") or self.OPENAI_DEFAULT_BASE_URL
            model = os.getenv("MODEL_NAME") or self.OPENAI_DEFAULT_MODEL
            print(f"[llm_client] 使用 OpenAI 后端：base_url={base_url}, model={model}")
            return backend, base_url, model, api_key

        if backend == self.BACKEND_CUSTOM:
            base_url = os.getenv("CUSTOM_BASE_URL")
            api_key = os.getenv("CUSTOM_API_KEY")
            model = os.getenv("CUSTOM_MODEL")
            # custom 后端缺失 BASE_URL 时回退到 trae
            if not base_url:
                print("[llm_client] LLM_BACKEND=custom 但未配置 CUSTOM_BASE_URL，自动回退到 trae 后端")
                return self._resolve_trae()
            print(f"[llm_client] 使用 custom 后端：base_url={base_url}, model={model}")
            return backend, base_url, model, api_key

        # 默认 trae 后端（未知值也走 trae）
        if backend != self.BACKEND_TRAE:
            print(f"[llm_client] 未知 LLM_BACKEND='{backend}'，使用默认 trae 后端")
        return self._resolve_trae()

    def _resolve_trae(self):
        """解析 TRAE 后端配置。TRAE 内置模型端点允许无 API_KEY 调用。"""
        base_url = os.getenv("TRAE_BASE_URL") or self.TRAE_DEFAULT_BASE_URL
        model = os.getenv("TRAE_MODEL") or self.TRAE_DEFAULT_MODEL
        api_key = os.getenv("TRAE_API_KEY") or None
        print(f"[llm_client] 使用 TRAE 后端：base_url={base_url}, model={model}")
        return self.BACKEND_TRAE, base_url, model, api_key

    def _ensure_client(self) -> OpenAI:
        """延迟创建 OpenAI 客户端。

        - trae 后端：不强制要求 API_KEY，由端点决定是否鉴权；无 key 时使用占位值
          以满足 OpenAI SDK 的非空校验，实际请求由 TRAE 端点处理鉴权。
        - openai / custom 后端：要求 API_KEY，否则抛出清晰错误（正常流程中
          openai 无 key 已在 _resolve_backend 中回退到 trae，此处仅为防御性校验）。

        Raises:
            RuntimeError: openai/custom 后端且未配置 API_KEY 时抛出。
        """
        if self.backend == self.BACKEND_TRAE:
            # TRAE 内置模型端点允许无 key 调用；api_key 为 None 时传占位字符串避免 SDK 报错
            api_key = self.api_key or "trae-no-key"
        elif not self.api_key:
            raise RuntimeError(
                f"未配置 {self.backend.upper()}_API_KEY。请在 .env 文件中设置对应的 API_KEY，"
                f"或切换 LLM_BACKEND=trae 使用 TRAE 内置模型端点（无需 API_KEY）。"
            )
        else:
            api_key = self.api_key

        if self._client is None:
            self._client = OpenAI(
                api_key=api_key,
                base_url=self.base_url,
            )
        return self._client

    def chat(self, system_prompt: str, user_message: str,
             temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """单轮对话：基于 system prompt + user message 调用 LLM。

        Args:
            system_prompt: 系统提示词，定义角色与行为约束。
            user_message: 用户消息内容。
            temperature: 采样温度，控制输出随机性，默认 0.7。
            max_tokens: 最大生成 token 数，默认 2000。

        Returns:
            LLM 生成的文本内容。
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_message},
        ]
        return self.chat_messages(messages, temperature=temperature, max_tokens=max_tokens)

    def chat_messages(self, messages: list,
                      temperature: float = 0.7, max_tokens: int = 2000) -> str:
        """多轮对话：接受完整的 messages 列表调用 LLM。

        Args:
            messages: OpenAI 格式的消息列表，例如：
                [{"role": "system", "content": "..."},
                 {"role": "user", "content": "..."},
                 {"role": "assistant", "content": "..."}]
            temperature: 采样温度，默认 0.7。
            max_tokens: 最大生成 token 数，默认 2000。

        Returns:
            LLM 生成的文本内容（response.choices[0].message.content）。

        Notes:
            遇到 openai.APIError / APIConnectionError / RateLimitError 时
            自动重试最多 3 次，间隔递增（1s, 2s, 4s）；
            重试耗尽后降级到 TraeBridge 文件队列（由 TRAE IDE 内置 AI 处理）。
        """
        client = self._ensure_client()
        last_error = None
        # 总尝试次数 = 1 次初始 + MAX_RETRIES 次重试
        total_attempts = self.MAX_RETRIES + 1
        for attempt in range(total_attempts):
            try:
                response = client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=temperature,
                    max_tokens=max_tokens,
                )
                return response.choices[0].message.content
            except (APIError, APIConnectionError, RateLimitError) as e:
                last_error = e
                # 非最后一次尝试时，按递增间隔等待后重试
                if attempt < total_attempts - 1:
                    time.sleep(self.RETRY_BACKOFF[attempt])

        # API 重试耗尽，降级到 TraeBridge 文件队列
        print(f"[llm_client] API 重试耗尽（{last_error}），降级到 TraeBridge 文件队列")
        try:
            from engine.trae_bridge import submit_request
            # 把 messages 列表拼成 system_prompt + user_message
            system_prompt = ""
            user_message = ""
            for msg in messages:
                if msg.get("role") == "system":
                    system_prompt += msg.get("content", "") + "\n"
                elif msg.get("role") == "user":
                    user_message += msg.get("content", "") + "\n"
                elif msg.get("role") == "assistant":
                    # 多轮对话历史
                    user_message += f"\n[历史回复] {msg.get('content', '')}\n"

            result = submit_request(
                system_prompt=system_prompt.strip(),
                user_message=user_message.strip(),
                max_tokens=max_tokens,
                timeout=300,  # 5 分钟超时
            )
            if result:
                return result
            # TraeBridge 也失败，抛出原始异常
            raise last_error
        except ImportError:
            print("[llm_client] TraeBridge 模块不可用，抛出原始异常")
            raise last_error


# 模块级默认客户端实例，便于全局复用（智能体可直接 import 后使用）
default_client = LLMClient()


# =============================================================================
# SEO Skill 套件加载（接入 AgriciDaniel/claude-seo）
# =============================================================================
def load_seo_skills(skills_dir: str = None) -> dict:
    """加载 SEO Skill 套件。

    扫描 skills_dir 下的子目录，读取每个子目录中的 SKILL.md，
    解析 YAML frontmatter（name / description）与正文（作为 prompt 模板），
    返回 {skill_name: {"description": str, "prompt": str, "path": str}}。

    参数:
        skills_dir: Skill 目录路径，默认为
            seo-content-generator/.claude/skills/claude-seo/

    返回:
        dict: {skill_name: {"description": str, "prompt": str, "path": str}}
        prompt 为 SKILL.md 正文（含 {variable} 占位符，可直接 .format()）。

    异常:
        FileNotFoundError: Skill 目录不存在时抛出。
    """
    import re

    if skills_dir is None:
        # 默认路径：相对 engine 包定位项目根目录
        _engine_dir = os.path.dirname(os.path.abspath(__file__))
        _project_root = os.path.dirname(_engine_dir)
        skills_dir = os.path.join(
            _project_root,
            "company", "projects", "seo-content-generator",
            ".claude", "skills", "claude-seo",
        )

    if not os.path.isdir(skills_dir):
        raise FileNotFoundError(f"SEO Skill 目录不存在：{skills_dir}")

    result: dict = {}
    for entry in sorted(os.listdir(skills_dir)):
        skill_md = os.path.join(skills_dir, entry, "SKILL.md")
        if not os.path.isfile(skill_md):
            continue
        try:
            with open(skill_md, "r", encoding="utf-8") as f:
                content = f.read()
        except OSError as e:
            print(f"[llm_client] 读取 SKILL.md 失败（{skill_md}）：{e}")
            continue
        meta, body = _parse_skill_md(content)
        name = meta.get("name") or entry
        result[name] = {
            "description": meta.get("description") or "",
            "prompt": body,
            "path": skill_md,
        }
    return result


def _parse_skill_md(content: str):
    """解析 SKILL.md 的 YAML frontmatter 与正文。

    frontmatter 位于文件首尾的 ``---`` 分隔符之间。解析失败时返回空 meta
    与原文正文。优先使用 PyYAML；未安装时降级为简单行解析（仅 name/description）。

    Returns:
        (meta_dict, body_str) 二元组。
    """
    import re

    match = re.match(r"^---\s*\n(.*?)\n---\s*\n?(.*)", content, re.DOTALL)
    if not match:
        return {}, content
    fm_text = match.group(1)
    body = match.group(2).strip()
    try:
        import yaml
        meta = yaml.safe_load(fm_text) or {}
        if not isinstance(meta, dict):
            meta = {}
    except ImportError:
        meta = _parse_simple_frontmatter(fm_text)
    return meta, body


def _parse_simple_frontmatter(fm_text: str) -> dict:
    """无 PyYAML 时的简单 frontmatter 解析（仅支持 name / description 单行字段）。"""
    meta: dict = {}
    for line in fm_text.splitlines():
        if ":" not in line:
            continue
        key, _, value = line.partition(":")
        key = key.strip()
        value = value.strip()
        if key in ("name", "description"):
            meta[key] = value
    return meta
