"""Local agent_server plus interaction persona/response probe."""

from __future__ import annotations

import json
import re
import sys
import tempfile
from pathlib import Path

ROOT = Path(__file__).resolve().parents[4]
sys.path.insert(0, str(ROOT))

from src.brain.agent_client import agent_healthy
from src.brain.interaction import InteractionLoop
from src.brain.voice.voice_profile import load_profile


def main() -> None:
    if not agent_healthy():
        raise SystemExit("agent_server health check failed")
    with tempfile.TemporaryDirectory() as temporary:
        loop = InteractionLoop(Path(temporary) / "queue")
        response = loop._try_agent_fallback(
            "这是本地回答链路实测，不要调用工具。用户问：查天气。"
            "当前没有天气数据，只说明数据未提供，不要编造。"
        )
    if response is None:
        raise SystemExit("interaction returned no agent response")
    text = response.text
    sentence_count = len(re.findall(r"[^。！？!?]+[。！？!?]?", text)) if text else 0
    banned_hits = [
        phrase for phrase in load_profile()["style"]["banned_phrases"] if phrase in text
    ]
    result = {
        "ok": bool(text) and sentence_count <= 2 and not banned_hits,
        "transport": "127.0.0.1 local agent_server",
        "reason": response.reason,
        "reply": text,
        "sentence_count": sentence_count,
        "banned_hits": banned_hits,
    }
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if not result["ok"]:
        raise SystemExit(1)


if __name__ == "__main__":
    main()
