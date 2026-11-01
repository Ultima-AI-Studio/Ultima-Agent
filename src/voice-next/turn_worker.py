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
import wave
from pathlib import Path
from typing import Callable, TextIO


ROOT = Path(__file__).resolve().parents[2]
_SAFE_ID = re.compile(r"[A-Za-z0-9][A-Za-z0-9._-]{0,127}")
_FIXED_WAKEWORD_REPLY = "当前新语音入口固定使用你好问问，暂不支持修改唤醒词。"
_TTS_BACKEND = "windows-sapi-fallback"
_TTS_FALLBACK_REASON = "legacy_cv3_cold_start_budget"


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

        # This dedicated process uses a declared cold-start fallback. The old
        # module/profile on disk and other processes retain their original TTS.
        voice_loop.tts_synthesize = sapi_synthesize
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


def _emit(output: TextIO, row: dict) -> None:
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
) -> int:
    """Process one turn at a time; malformed turns do not poison later turns."""
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
            "tts_backend": _TTS_BACKEND,
        })
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
