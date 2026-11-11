"""Resident adapter for the existing voice loop, with JSON-lines IPC only.

Run with tools/venv-asr/Scripts/python.exe. This process synthesizes replies
but never captures microphone input or plays audio.
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
import wave
from pathlib import Path
from typing import Callable, TextIO


ROOT = Path(__file__).resolve().parents[2]
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_FIXED_WAKEWORD_REPLY = "当前新语音入口固定使用你好问问，暂不支持修改唤醒词。"
_TTS_BACKEND = "windows-sapi-fallback"
_TTS_FALLBACK_REASON = "legacy_cv3_cold_start_budget"

# ── CV3 零样本音色克隆（常驻 daemon，本进程是唯一宿主）──────────────────
# 与旧链路的 VoiceDaemon("tts") 分开命名，避免互相抢全局单实例锁：旧链路若先
# 拉起 "tts"，本进程的 ensure_started() 会因 _global_holder_alive() 直接返回
# False，于是永远走 SAPI 兜底——那正是「CV3 音色没换上」的结构性原因之一。
# 冷启动（加载 CosyVoice3）实测约 256s，因此后台预热，未就绪期间继续用 SAPI。
_CV3_DAEMON_NAME = "tts-voice-next"
_CV3_DAEMON = None
_CV3_LOCK = threading.Lock()
_CV3_STATE = {"ready": False, "backend": _TTS_BACKEND, "error": None, "warm_seconds": None}
_CV3_FAILURES = 0
_CV3_MAX_FAILURES = 3


def _cv3_daemon():
    """独立命名的 CV3 常驻 daemon（行协议，模型只在内存里加载一次）。"""
    global _CV3_DAEMON
    if _CV3_DAEMON is None:
        sys.path.insert(0, str(ROOT))
        from src.brain.voice.daemon import VoiceDaemon, _TTS_DAEMON_SCRIPT
        from src.brain.voice.resources import COSYVOICE_SOURCE, CV3_MODEL_ROOT, CV3_RUNTIME_PYTHON
        from src.brain.voice.tts import _VENDOR_DIR

        script = _TTS_DAEMON_SCRIPT.replace("{source}", str(COSYVOICE_SOURCE))
        script = script.replace("{model}", str(CV3_MODEL_ROOT))
        _CV3_DAEMON = VoiceDaemon(
            _CV3_DAEMON_NAME, script, CV3_RUNTIME_PYTHON, [],
            env={"PYTHONPATH": str(_VENDOR_DIR)}, ready_timeout=900.0,
        )
    return _CV3_DAEMON


def cv3_synthesize(text: str, out_wav: str | Path, timeout: int | float = 300) -> dict:
    """用 voice-profile 挂的参考音频做零样本克隆；输出 24kHz，play() 会重采样。"""
    output = Path(out_wav).resolve()
    result = {"ok": False, "engine": "cv3", "wav": str(output)}
    try:
        sys.path.insert(0, str(ROOT))
        from src.brain.voice.tts import resolve_prompt_pair
        from src.brain.voice.voice_profile import load_profile

        daemon = _cv3_daemon()
        if not daemon.ensure_started():
            raise RuntimeError("CV3 daemon not ready (load failed or another host holds the lock)")
        prompt_wav, prompt_text = resolve_prompt_pair(load_profile())
        output.parent.mkdir(parents=True, exist_ok=True)
        reply = daemon.request(
            {"op": "synthesize", "text": text, "out": str(output),
             "prompt_wav": str(prompt_wav), "prompt_text": prompt_text},
            timeout=min(900.0, max(1.0, float(timeout))),
        )
        if not reply.get("ok"):
            raise RuntimeError(reply.get("error") or "CV3 returned not-ok")
        result.update(ok=True, rate=reply.get("rate"), seconds=reply.get("seconds"),
                      device=reply.get("device"), daemon=True)
    except Exception as exc:
        result["error"] = str(exc)
    return result


def synthesize_reply(text: str, out_wav: str | Path, timeout: int | float = 300) -> dict:
    """CV3 优先、SAPI 兜底。返回的 engine 字段必须反映这次真实用的引擎。"""
    global _CV3_FAILURES
    with _CV3_LOCK:
        ready = _CV3_STATE["ready"]
    if ready:
        cv3 = cv3_synthesize(text, out_wav, timeout)
        if cv3.get("ok"):
            with _CV3_LOCK:
                _CV3_FAILURES = 0
            return cv3
        with _CV3_LOCK:
            _CV3_FAILURES += 1
            failures = _CV3_FAILURES
            if failures >= _CV3_MAX_FAILURES:
                _CV3_STATE.update(ready=False, backend=_TTS_BACKEND,
                                  error=f"cv3 disabled after {failures} failures: {cv3.get('error')}")
        fallback = sapi_synthesize(text, out_wav, timeout=timeout)
        fallback["fallback_from"] = "cv3"
        fallback["cv3_error"] = cv3.get("error")
        return fallback
    return sapi_synthesize(text, out_wav, timeout=timeout)


def rewrite_prompts() -> dict:
    """预热完成后用克隆音色重写四句提示音；原子替换，正在播的旧文件不被截断。"""
    cfg = json.loads((ROOT / "config" / "voice-next" / "live.json").read_text(encoding="utf-8-sig"))
    texts = cfg.get("prompts") or {}
    out_dir = ROOT / "data" / "voice-next" / "prompts"
    out_dir.mkdir(parents=True, exist_ok=True)
    done: dict[str, bool] = {}
    for name in ("wake", "empty", "ready", "error"):
        text = texts.get(name)
        if not text:
            done[name] = False
            continue
        tmp = out_dir / f".{name}.cv3.wav"
        try:
            if synthesize_reply(text, tmp, timeout=120).get("ok"):
                os.replace(tmp, out_dir / f"{name}.wav")
                done[name] = True
            else:
                tmp.unlink(missing_ok=True)
                done[name] = False
        except OSError:
            tmp.unlink(missing_ok=True)
            done[name] = False
    return done


def prewarm_cv3(emit: Callable[[dict], None] | None = None) -> dict:
    """后台加载 CV3 并做一次真实合成；成功后把 TTS 切到 CV3。"""
    started = time.monotonic()
    probe = ROOT / "data" / "voice-next" / "cv3-prewarm.wav"
    outcome = cv3_synthesize("语音入口正在加载中文音色。", probe, timeout=900)
    elapsed = round(time.monotonic() - started, 1)
    ok = bool(outcome.get("ok"))
    with _CV3_LOCK:
        _CV3_STATE.update(
            ready=ok,
            backend="cv3" if ok else _TTS_BACKEND,
            warm_seconds=elapsed,
            error=None if ok else outcome.get("error"),
        )
    prompts = rewrite_prompts() if ok else {}
    row = {"type": "tts_ready", "tts_backend": _CV3_STATE["backend"], "cv3_ready": ok,
           "warm_seconds": elapsed, "prompts": prompts, "error": _CV3_STATE["error"]}
    if emit is not None:
        emit(row)
    return row


def sapi_synthesize(text: str, out_wav: str | Path, timeout: int | float = 30) -> dict:
    """Bounded file-only fallback; never probe or start the legacy CV3 daemon."""
    output = Path(out_wav).resolve()
    result = {
        "ok": False,
        "engine": _TTS_BACKEND,
        "fallback_reason": _TTS_FALLBACK_REASON,
        "wav": str(output),
    }
    request_path = None
    try:
        pwsh = shutil.which("pwsh.exe") or shutil.which("pwsh")
        if not pwsh:
            raise RuntimeError("PowerShell 7 (pwsh.exe) is required for the SAPI fallback")
        output.parent.mkdir(parents=True, exist_ok=True)
        with tempfile.NamedTemporaryFile(
            mode="w", encoding="utf-8", prefix=".sapi-", suffix=".json",
            dir=output.parent, delete=False,
        ) as request:
            request_path = Path(request.name)
            json.dump({"text": text, "output": str(output)}, request, ensure_ascii=True)
        child = subprocess.run(
            [pwsh, "-NoProfile", "-NonInteractive", "-File", str(Path(__file__).with_name("sapi.ps1")),
             "-Request", str(request_path)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            timeout=min(30.0, max(0.1, float(timeout))),
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        if child.returncode:
            raise RuntimeError(child.stderr.strip() or f"SAPI exited {child.returncode}")
        receipt = json.loads(child.stdout)
        if not receipt.get("ok") or Path(receipt.get("wav", "")).resolve() != output:
            raise RuntimeError("SAPI returned an invalid WAV receipt")
        with wave.open(str(output), "rb") as audio:
            if (audio.getnchannels(), audio.getsampwidth(), audio.getframerate(), audio.getcomptype()) != (1, 2, 16000, "NONE"):
                raise RuntimeError("SAPI output must be mono PCM16 at 16000 Hz")
            seconds = audio.getnframes() / audio.getframerate()
            if seconds <= 0:
                raise RuntimeError("SAPI returned an empty WAV")
        result.update(ok=True, rate=16000, seconds=seconds, voice=receipt.get("voice"))
    except Exception as exc:
        result["error"] = str(exc)
    finally:
        if request_path is not None:
            request_path.unlink(missing_ok=True)
    return result


def build_loop(root: Path):
    """Load the existing algorithms and prewarm the local SenseVoice cache."""
    sys.path.insert(0, str(ROOT))
    with contextlib.redirect_stdout(sys.stderr):
        from src.brain.interaction import _extract_wakeword_change, _is_ambiguous_wakeword_change
        from src.brain.voice.asr import _load_sherpa_asr
        from src.brain import voice_loop

        # CV3 优先（预热完成后自动切换），SAPI 只作冷启动/失败兜底。旧模块与
        # 旧 profile 上的 TTS 不动，本进程内的替换只影响这个专用入口进程。
        voice_loop.tts_synthesize = synthesize_reply
        loop = voice_loop.VoiceInteractionLoop(
            root / "tasks",
            root / "data" / "host" / "orb_command.json",
            root / "data" / "voice-next" / "replies",
        )
        interaction = loop.bridge.loop
        interaction.set_wakeword_change_submitter(None)

        # Per-instance adaptation only: the legacy listener/profile stay intact.
        # Let the existing handle_audio pipeline speak this explanation normally.
        def fixed_wakeword_change(text: str):
            if _extract_wakeword_change(text) is not None or _is_ambiguous_wakeword_change(text):
                return interaction._respond(
                    True, True, _FIXED_WAKEWORD_REPLY, "新入口固定唤醒词", interaction.phase
                )
            return None

        interaction._try_wakeword_change = fixed_wakeword_change
        _load_sherpa_asr()
        return loop


def _safe_id(payload) -> str | None:
    value = payload.get("id") if isinstance(payload, dict) else None
    return value if isinstance(value, str) and _SAFE_ID.fullmatch(value) else None


def _input_wav(payload, root: Path) -> tuple[str, Path]:
    if not isinstance(payload, dict):
        raise ValueError("request must be a JSON object")
    if "op" in payload:
        raise ValueError("unsupported operation")
    request_id = _safe_id(payload)
    if request_id is None:
        raise ValueError("id must contain 1-128 safe ASCII letters, digits, dot, underscore or hyphen")
    name = payload.get("wav")
    if not isinstance(name, str) or not name.strip():
        raise ValueError("wav must be a non-empty path")
    wav = Path(name)
    if not wav.is_absolute():
        wav = root / wav
    wav = wav.resolve(strict=True)
    if not wav.is_relative_to((root / "data").resolve()):
        raise ValueError("wav must stay under the project data directory")
    if not wav.is_file() or wav.suffix.lower() != ".wav":
        raise ValueError("wav must be an existing WAV file")
    return request_id, wav


_EMIT_LOCK = threading.Lock()


def _emit(output: TextIO, row: dict) -> None:
    # 预热线程会在主线程处理回合时汇报 tts_ready，必须串行化 stdout 写入。
    with _EMIT_LOCK:
        output.write(json.dumps(row, ensure_ascii=True, allow_nan=False) + "\n")
        output.flush()


def _failure(stage: str, error: Exception | str) -> dict:
    return {"ok": False, "stage": stage, "error": str(error)}


def serve(
    requests: TextIO,
    output: TextIO,
    *,
    root: Path | None = None,
    loop_factory: Callable | None = None,
    prewarm: bool = True,
) -> int:
    """Process one turn at a time; malformed turns do not poison later turns.

    ``prewarm=False`` keeps the protocol testable without loading the CV3 model.
    """
    root = (root or ROOT).resolve()
    factory = loop_factory or build_loop
    with contextlib.redirect_stdout(sys.stderr):
        try:
            loop = factory(root)
        except Exception as exc:
            _emit(output, {"type": "result", "id": None, "result": _failure("startup", exc)})
            return 1
        _emit(output, {
            "type": "ready", "asr_ready": True, "pid": os.getpid(),
            "tts_backend": _CV3_STATE["backend"],
            "tts_cv3_pending": not _CV3_STATE["ready"],
        })
        # 模型加载约 4 分钟，放到后台：就绪前用 SAPI 保证能说话，就绪后自动换回克隆音色。
        if prewarm:
            threading.Thread(
                target=prewarm_cv3,
                args=(lambda row: _emit(output, row),),
                name="cv3-prewarm", daemon=True,
            ).start()
        for line in requests:
            payload = None
            try:
                payload = json.loads(line)
                if isinstance(payload, dict) and payload.get("op") == "shutdown":
                    return 0
                request_id, wav = _input_wav(payload, root)
            except (OSError, ValueError, TypeError) as exc:
                _emit(output, {"type": "result", "id": _safe_id(payload), "result": _failure("input", exc)})
                continue

            _emit(output, {"type": "started", "id": request_id})
            try:
                result = loop.handle_audio(wav, reply_timeout=30)
                if not isinstance(result, dict):
                    raise TypeError("VoiceInteractionLoop returned a non-object result")
                if not result.get("ok") and not result.get("error"):
                    # The old loop keeps some errors in nested TTS/bridge fields.
                    result = dict(result)
                    tts = result.get("tts") or {}
                    response = result.get("response") or {}
                    result["error"] = tts.get("error") or response.get("reason") or "voice turn failed"
            except Exception as exc:
                result = _failure("worker", exc)
            _emit(output, {"type": "result", "id": request_id, "result": result})
    return 0


def _protocol_output() -> TextIO:
    """Reserve the IPC pipe, then send Python and native library stdout to stderr."""
    sys.stdout.flush()
    output = os.fdopen(os.dup(sys.stdout.fileno()), "w", encoding="utf-8", buffering=1)
    os.dup2(sys.stderr.fileno(), sys.stdout.fileno())
    sys.stdout = sys.stderr
    if os.name == "nt":
        import ctypes
        import msvcrt

        set_handle = ctypes.windll.kernel32.SetStdHandle
        set_handle.argtypes = (ctypes.c_uint32, ctypes.c_void_p)
        set_handle.restype = ctypes.c_int
        if not set_handle(-11 & 0xFFFFFFFF, msvcrt.get_osfhandle(sys.stderr.fileno())):
            raise ctypes.WinError()
    return output


def main(argv: list[str] | None = None) -> int:
    output = _protocol_output()
    try:
        parser = argparse.ArgumentParser(description=__doc__)
        parser.add_argument("--wav", type=Path, help="Process one saved WAV and exit using the same JSON protocol")
        args = parser.parse_args(argv)
        if args.wav is not None:
            source = io.StringIO(json.dumps({"id": "offline", "wav": str(args.wav)}) + "\n")
        else:
            source = sys.stdin
        return serve(source, output, root=ROOT)
    finally:
        output.close()


if __name__ == "__main__":
    raise SystemExit(main())
