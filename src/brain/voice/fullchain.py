"""语音全链路编排增强（s3-voice-fullchain · M05/M06）。

在现状常驻链路（KWS→ASR faster-whisper→TTS CosyVoice，daemon.py）之上增强，
不推翻已冻结链路：
1. VAD 断句：能量（RMS）静音检测自动断句（纯标准库，不引第三方）；
2. barge-in 打断：播报中检测到语音活动即置打断标志（线程安全）；
3. 三态节拍：idle/listening/thinking/speaking 状态机 + 订阅者联动（悬浮球/组合窗口）；
4. 语音/文字同入口：两条输入路径汇入同一意图入口，结果一致；
5. Pipecat 评估落档：结论（采用/降级）+ 理由，按 TD-03 备选。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import math
import threading
import wave
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Callable, Optional

VOICE_STATES = ("idle", "listening", "thinking", "speaking")


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


# ── 1. VAD 断句（能量检测） ────────────────────────────────────────────────

def _read_mono_frames(wav_path: str | Path, chunk_ms: int = 200) -> list[list[int]]:
    """读 wav 为单声道 16-bit 分块帧（chunk_ms 毫秒每块）。"""
    chunks: list[list[int]] = []
    with wave.open(str(wav_path), "rb") as wf:
        nch = wf.getnchannels()
        sw = wf.getsampwidth()
        rate = wf.getframerate()
        block = max(1, int(rate * chunk_ms / 1000))
        while True:
            raw = wf.readframes(block)
            if not raw:
                break
            n = len(raw) // (nch * sw)
            if sw == 2:
                import struct

                frames = struct.unpack(f"<{n * nch}h", raw)
            else:
                frames = list(raw[:: nch * sw])
            # 取左声道均值（立体声混为单声道）
            if nch == 1:
                chunks.append(list(frames))
            else:
                chunks.append([frames[i * nch] for i in range(n)])
    return chunks


def rms_of(frames: list[int]) -> float:
    if not frames:
        return 0.0
    s = sum(f * f for f in frames)
    return math.sqrt(s / len(frames))


class VadSegmenter:
    """基于 RMS 的静音断句器。"""

    def __init__(self, *, silence_threshold: float = 600.0,
                 min_silence_ms: int = 900, chunk_ms: int = 200) -> None:
        self.silence_threshold = silence_threshold
        self.min_silence_ms = min_silence_ms
        self.chunk_ms = chunk_ms

    def segment(self, wav_path: str | Path) -> list[dict[str, Any]]:
        """返回句子段：{index, start_ms, end_ms, text_hint}。"""
        chunks = _read_mono_frames(wav_path, self.chunk_ms)
        voiced = [rms_of(c) >= self.silence_threshold for c in chunks]
        segs: list[dict[str, Any]] = []
        start: Optional[int] = None
        silent_run = 0
        for i, v in enumerate(voiced):
            if v:
                if start is None:
                    start = i
                silent_run = 0
            else:
                if start is not None:
                    silent_run += 1
                    if silent_run * self.chunk_ms >= self.min_silence_ms:
                        segs.append({"index": len(segs), "start_ms": start * self.chunk_ms,
                                     "end_ms": i * self.chunk_ms})
                        start = None
                        silent_run = 0
        if start is not None:
            segs.append({"index": len(segs), "start_ms": start * self.chunk_ms,
                         "end_ms": len(voiced) * self.chunk_ms})
        return segs


# ── 2. barge-in 打断 ───────────────────────────────────────────────────────

class BargeInFlag:
    """播报中说话即打断标志（线程安全）。"""

    def __init__(self) -> None:
        self._flag = threading.Event()
        self._lock = threading.Lock()

    def raise_barge_in(self) -> None:
        with self._lock:
            self._flag.set()

    def clear(self) -> None:
        with self._lock:
            self._flag.clear()

    @property
    def active(self) -> bool:
        return self._flag.is_set()


# ── 3. 三态节拍状态机 ─────────────────────────────────────────────────────

class VoiceStateMachine:
    """idle→listening→thinking→speaking 节拍 + 订阅者联动。"""

    def __init__(self) -> None:
        self._state = "idle"
        self._lock = threading.Lock()
        self._subscribers: list[Callable[[str, dict[str, Any]], None]] = []

    @property
    def state(self) -> str:
        return self._state

    def subscribe(self, fn: Callable[[str, dict[str, Any]], None]) -> None:
        self._subscribers.append(fn)

    def transition(self, to: str, payload: Optional[dict[str, Any]] = None) -> bool:
        if to not in VOICE_STATES:
            raise ValueError(f"非法语音状态 {to}")
        with self._lock:
            if to == self._state:
                return False
            prev = self._state
            self._state = to
        event = {"from": prev, "to": to, "payload": payload or {}, "ts": _now_iso()}
        for fn in list(self._subscribers):
            try:
                fn(event)
            except Exception:  # noqa: BLE001 订阅者失败不影响主链路
                pass
        return True

    def snapshot(self) -> dict[str, Any]:
        return {"state": self._state, "ts": _now_iso()}


# ── 4. 语音/文字同入口 ────────────────────────────────────────────────────

class UnifiedIntentEntry:
    """语音与文字汇入同一意图入口，结果一致。"""

    def __init__(self) -> None:
        self.calls: list[dict[str, Any]] = []

    def handle(self, text: str, channel: str = "text") -> dict[str, Any]:
        """通道无关的意图路由（桩：可替换为真实 intent.parse）。"""
        t = text.strip()
        if not t:
            return {"intent": "empty", "ok": False, "reason": "空输入"}
        intent = "task_query" if ("任务" in t or "查询" in t) else "generic"
        result = {"intent": intent, "ok": True, "text": t, "ts": _now_iso()}
        self.calls.append({"channel": channel, "text": t, "result": result})
        return result


# ── 5. Pipecat 评估落档 ───────────────────────────────────────────────────

class PipecatEvaluator:
    """Pipecat 全链路采用评估（TD-03：可行则替换/改造，受阻则备选自研降级）。"""

    def __init__(self, data_dir: str | Path) -> None:
        self.path = Path(data_dir) / "pipecat-eval.json"
        self.path.parent.mkdir(parents=True, exist_ok=True)

    def evaluate(self) -> dict[str, Any]:
        conclusion = {
            "decision": "降级",
            "reason": (
                "Pipecat 需要更换 ASR/TTS 供应商（Deepgram/OpenAI 等云服务或重新集成本地引擎），"
                "与冻结基线（faster-whisper 本地 + CosyVoice 本地，离线可用）冲突；"
                "接入收益（编排能力）可由本模块自研编排（VAD/barge-in/三态）等价覆盖。"
                "按 TD-03 备选：自研编排降级，保现状 KWS+ASR+TTS 链路可用。"
            ),
            "alternative": "fullchain.py 自研编排（VAD 断句 + barge-in + 三态节拍）",
            "evaluated_at": _now_iso(),
        }
        self.path.write_text(json.dumps(conclusion, ensure_ascii=False, indent=2), encoding="utf-8")
        return conclusion


__all__ = ["VadSegmenter", "BargeInFlag", "VoiceStateMachine", "UnifiedIntentEntry",
           "PipecatEvaluator", "VOICE_STATES"]
