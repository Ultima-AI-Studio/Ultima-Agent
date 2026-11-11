"""主脑职责提议入口（/mainbrain 专用，不污染 /ask 语音链路）。

设计约束：
- 只读主脑职责规则基线（docs/specs/mainbrain-duty-rules-baseline.md），
  与 /ask 使用的应答规则（mainbrain-rules-baseline.md）严格分家；
- 阶段 1 只提议：输出"建议派给谁 + 理由 + 预计产物"，不真派发、不写队列；
- 直接调本机 ollama，复用 agent_server 的模型与地址常量语义，但不 import
  agent_server，避免循环导入。
"""

from __future__ import annotations

import json
import re
import time
import urllib.request
from pathlib import Path
from typing import Any

PROJECT_ROOT = Path(__file__).resolve().parents[2]
DUTY_RULES_PATH = PROJECT_ROOT / "docs" / "specs" / "mainbrain-duty-rules-baseline.md"
OLLAMA_CHAT_URL = "http://127.0.0.1:11434/api/chat"
MODEL = "qwen3-8b-uncensored"
PROPOSE_TIMEOUT_SECONDS = 120.0
PROPOSE_NUM_PREDICT = 500
PROPOSE_TEMPERATURE = 0.2


def _load_rule_block() -> tuple[str, str]:
    """返回 (规则块, 版本号)。版本号从标题里取出，供调用方核对。"""
    try:
        text = DUTY_RULES_PATH.read_text(encoding="utf-8")
    except OSError as exc:
        raise RuntimeError(f"主脑职责规则不可用：{DUTY_RULES_PATH}") from exc
    found = re.search(r"```\s*\r?\n(.*?)\r?\n```", text, re.DOTALL)
    if found is None or not found.group(1).strip():
        raise RuntimeError("主脑职责规则文件里没有可嵌入块")
    title = re.search(r"（v(\d+\.\d+)）", text)
    return found.group(1).strip(), (f"v{title.group(1)}" if title else "unknown")


def propose(query: str, *, timeout: float = PROPOSE_TIMEOUT_SECONDS) -> dict[str, Any]:
    """让 8B 按职责规则给出一条提议。阶段 1 只出建议，不执行任何动作。"""
    query = (query or "").strip()
    if not query:
        raise ValueError("query 不能为空")

    block, version = _load_rule_block()
    body = {
        "model": MODEL,
        "messages": [
            {"role": "system", "content": block},
            {"role": "user", "content": query},
        ],
        "stream": False,
        "options": {
            "temperature": PROPOSE_TEMPERATURE,
            "num_predict": PROPOSE_NUM_PREDICT,
        },
    }
    request = urllib.request.Request(
        OLLAMA_CHAT_URL,
        data=json.dumps(body, ensure_ascii=False).encode("utf-8"),
        headers={"Content-Type": "application/json"},
    )
    started = time.time()
    with urllib.request.urlopen(request, timeout=timeout) as response:
        payload = json.loads(response.read().decode("utf-8"))
    elapsed = round(time.time() - started, 2)
    proposal = ((payload.get("message") or {}).get("content") or "").strip()
    if not proposal:
        raise RuntimeError("8B 返回空提议")

    return {
        "mode": "propose",
        "stage": 1,
        "rule_version": version,
        "model": MODEL,
        "query": query,
        "proposal": proposal,
        "elapsed_seconds": elapsed,
        "executed": False,
        "note": "阶段 1：只给提议，未派发、未写队列、未签冻结。",
    }


__all__ = ["propose", "DUTY_RULES_PATH"]
