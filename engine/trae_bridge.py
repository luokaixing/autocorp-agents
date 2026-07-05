"""TRAE Bridge - 通过文件队列让 TRAE IDE 内置 AI 充当 LLM

工作机制：
1. AI 公司代码调用 LLM 时，如果 TRAE API 失败（404/超时），
   把请求写入 company/llm-queue/req-<id>.json
2. 代码等待 resp-<id>.json 出现（轮询，超时 5 分钟）
3. TRAE IDE 里的 AI（我）看到队列有请求时，读取 prompt，
   用 GLM-5.2 生成回复，写回 resp-<id>.json
4. 代码读取回复，继续执行

这样无需 API key 就能用 TRAE 内置的 GLM-5.2 模型。

文件格式：
  req-<id>.json: {"id": "...", "system_prompt": "...", "user_message": "...", "max_tokens": 2000}
  resp-<id>.json: {"id": "...", "content": "...", "status": "ok"|"error"}
"""
from __future__ import annotations

import json
import time
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


# 队列目录
QUEUE_DIR = Path("company/llm-queue")
QUEUE_DIR.mkdir(parents=True, exist_ok=True)

# 轮询间隔（秒）
POLL_INTERVAL = 10

# 默认超时（秒）- 5 分钟
DEFAULT_TIMEOUT = 300


def submit_request(
    system_prompt: str,
    user_message: str,
    max_tokens: int = 2000,
    timeout: int = DEFAULT_TIMEOUT,
) -> Optional[str]:
    """提交 LLM 请求到 TRAE Bridge 队列，等待回复。

    Args:
        system_prompt: 系统提示词
        user_message: 用户消息
        max_tokens: 最大生成 token 数
        timeout: 等待回复的超时秒数

    Returns:
        LLM 生成的文本内容，超时返回 None
    """
    req_id = f"{int(time.time())}-{uuid.uuid4().hex[:8]}"
    req_data = {
        "id": req_id,
        "system_prompt": system_prompt,
        "user_message": user_message,
        "max_tokens": max_tokens,
        "submitted_at": datetime.now().isoformat(timespec="seconds"),
    }

    # 写入请求文件
    req_path = QUEUE_DIR / f"req-{req_id}.json"
    req_path.write_text(json.dumps(req_data, ensure_ascii=False, indent=2), encoding="utf-8")
    print(f"[trae_bridge] 请求已提交: {req_path.name}（等待 TRAE AI 处理，超时 {timeout}s）")

    # 轮询等待回复
    resp_path = QUEUE_DIR / f"resp-{req_id}.json"
    start_time = time.time()
    while time.time() - start_time < timeout:
        if resp_path.exists():
            try:
                resp_data = json.loads(resp_path.read_text(encoding="utf-8"))
                # 清理请求和响应文件
                req_path.unlink(missing_ok=True)
                resp_path.unlink(missing_ok=True)
                if resp_data.get("status") == "ok":
                    print(f"[trae_bridge] 收到回复: {req_id}")
                    return resp_data.get("content", "")
                else:
                    print(f"[trae_bridge] 回复错误: {resp_data.get('error', '未知')}")
                    return None
            except Exception as e:  # noqa: BLE001
                print(f"[trae_bridge] 回复解析失败: {e}")
                return None
        time.sleep(POLL_INTERVAL)

    # 超时
    print(f"[trae_bridge] 等待超时（{timeout}s），无回复")
    # 保留请求文件，让 TRAE AI 仍可处理（如果它后来看到的话）
    return None


def list_pending_requests() -> list:
    """列出所有待处理的 LLM 请求。

    TRAE AI 调用此方法查看是否有请求需要处理。

    Returns:
        待处理请求列表 [{id, system_prompt, user_message, max_tokens, req_path}]
    """
    pending = []
    for req_path in QUEUE_DIR.glob("req-*.json"):
        try:
            data = json.loads(req_path.read_text(encoding="utf-8"))
            # 检查是否已有对应响应
            resp_path = QUEUE_DIR / f"resp-{data.get('id', '')}.json"
            if not resp_path.exists():
                data["req_path"] = str(req_path)
                pending.append(data)
        except Exception:  # noqa: BLE001
            continue
    return pending


def submit_response(req_id: str, content: str, status: str = "ok") -> bool:
    """提交 LLM 回复到队列。

    TRAE AI 处理完请求后调用此方法写回回复。

    Args:
        req_id: 请求 ID
        content: LLM 生成的文本内容
        status: "ok" 或 "error"

    Returns:
        是否成功写入
    """
    resp_data = {
        "id": req_id,
        "content": content,
        "status": status,
        "responded_at": datetime.now().isoformat(timespec="seconds"),
    }
    resp_path = QUEUE_DIR / f"resp-{req_id}.json"
    try:
        resp_path.write_text(json.dumps(resp_data, ensure_ascii=False, indent=2), encoding="utf-8")
        print(f"[trae_bridge] 回复已写入: {resp_path.name}")
        return True
    except Exception as e:  # noqa: BLE001
        print(f"[trae_bridge] 回复写入失败: {e}")
        return False


if __name__ == "__main__":
    # 查看待处理请求
    pending = list_pending_requests()
    if not pending:
        print("无待处理请求")
    else:
        print(f"待处理请求 {len(pending)} 个:")
        for p in pending:
            print(f"  ID: {p.get('id')}")
            print(f"  路径: {p.get('req_path')}")
            print(f"  系统: {p.get('system_prompt', '')[:100]}")
            print(f"  用户: {p.get('user_message', '')[:100]}")
            print()
