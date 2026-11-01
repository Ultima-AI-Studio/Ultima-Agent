"""Offline worker protocol and file-only Windows speech checks; no microphone."""

from __future__ import annotations

import importlib.util
import io
import json
import os
import shutil
import subprocess
import sys
import wave
from pathlib import Path

import pytest


WORKER_FILE = Path(__file__).with_name("turn_worker.py")
SAPI_FILE = Path(__file__).with_name("sapi.ps1")


def load_worker():
    assert WORKER_FILE.is_file(), "persistent voice worker is not implemented"
    spec = importlib.util.spec_from_file_location("voice_next_turn_worker", WORKER_FILE)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def make_wav(path: Path) -> Path:
    path.parent.mkdir(parents=True, exist_ok=True)
    with wave.open(str(path), "wb") as output:
        output.setparams((1, 2, 16000, 0, "NONE", "not compressed"))
        output.writeframes(b"\x00\x00" * 320)
    return path


def json_lines(*rows) -> io.StringIO:
    return io.StringIO("".join(json.dumps(row) + "\n" for row in rows))


def test_persistent_protocol_flushes_started_and_preserves_existing_result(tmp_path, capsys):
    worker = load_worker()
    wav = make_wav(tmp_path / "data" / "turn.wav")
    output = io.StringIO()

    class Loop:
        def handle_audio(self, path, *, reply_timeout):
            assert path == wav
            assert reply_timeout == 30
            assert json.loads(output.getvalue().splitlines()[-1]) == {
                "type": "started", "id": "turn-001"
            }
            print("ASR library diagnostic")
            return {"ok": True, "stage": "tts", "text": "现在几点", "reply_wav": "answer.wav"}

    def load(root):
        assert root == tmp_path
        print("prewarm diagnostic")
        return Loop()

    status = worker.serve(
        json_lines({"id": "turn-001", "wav": str(wav)}, {"op": "shutdown"}, {"id": "ignored", "wav": str(wav)}),
        output,
        root=tmp_path,
        loop_factory=load,
    )
    rows = [json.loads(line) for line in output.getvalue().splitlines()]
    assert status == 0
    assert rows[0] == {
        "type": "ready", "asr_ready": True, "pid": os.getpid(),
        "tts_backend": "windows-sapi-fallback",
    }
    assert rows[1] == {"type": "started", "id": "turn-001"}
    assert rows[2] == {
        "type": "result", "id": "turn-001",
        "result": {"ok": True, "stage": "tts", "text": "现在几点", "reply_wav": "answer.wav"},
    }
    assert len(rows) == 3
    assert output.getvalue().isascii()
    captured = capsys.readouterr()
    assert captured.out == ""
    assert "prewarm diagnostic" in captured.err
    assert "ASR library diagnostic" in captured.err


@pytest.mark.parametrize("payload", [
    [],
    {"id": "../unsafe", "wav": "data/turn.wav"},
    {"id": "safe", "wav": "../outside.wav"},
    {"id": "safe", "wav": "data/missing.wav"},
    {"id": "safe", "wav": "data/turn.txt"},
    {"op": "execute", "id": "safe", "wav": "data/turn.wav"},
])
def test_invalid_requests_cannot_reach_voice_loop(tmp_path, payload):
    worker = load_worker()
    make_wav(tmp_path / "data" / "turn.wav")
    make_wav(tmp_path.parent / "outside.wav")
    (tmp_path / "data" / "turn.txt").write_text("not audio", encoding="utf-8")

    class Loop:
        def handle_audio(self, *args, **kwargs):
            pytest.fail("invalid input reached ASR")

    output = io.StringIO()
    assert worker.serve(json_lines(payload), output, root=tmp_path, loop_factory=lambda root: Loop()) == 0
    rows = [json.loads(line) for line in output.getvalue().splitlines()]
    assert [row["type"] for row in rows] == ["ready", "result"]
    assert rows[1]["result"]["ok"] is False
    assert rows[1]["result"]["stage"] == "input"
    assert rows[1]["result"]["error"]


def test_malformed_line_and_handler_error_do_not_stop_next_turn(tmp_path):
    worker = load_worker()
    wav = make_wav(tmp_path / "data" / "turn.wav")
    output = io.StringIO()

    class Loop:
        def __init__(self):
            self.calls = 0

        def handle_audio(self, path, *, reply_timeout):
            self.calls += 1
            if self.calls == 1:
                raise RuntimeError("local ASR failed")
            return {"ok": False, "stage": "tts", "tts": {"ok": False, "error": "TTS unavailable"}}

    source = io.StringIO("not JSON\n" + json_lines(
        {"id": "first", "wav": str(wav)},
        {"id": "second", "wav": str(wav)},
    ).getvalue())
    assert worker.serve(source, output, root=tmp_path, loop_factory=lambda root: Loop()) == 0
    rows = [json.loads(line) for line in output.getvalue().splitlines()]
    assert [row["type"] for row in rows] == ["ready", "result", "started", "result", "started", "result"]
    assert rows[1]["id"] is None
    assert rows[1]["result"]["stage"] == "input"
    assert rows[3]["id"] == "first"
    assert rows[3]["result"] == {"ok": False, "stage": "worker", "error": "local ASR failed"}
    assert rows[5]["id"] == "second"
    assert rows[5]["result"]["stage"] == "tts"
    assert rows[5]["result"]["error"] == "TTS unavailable"


def test_startup_failure_never_announces_ready(tmp_path):
    worker = load_worker()
    def fail(root):
        raise RuntimeError("SenseVoice cache is missing")

    output = io.StringIO()
    assert worker.serve(io.StringIO(), output, root=tmp_path, loop_factory=fail) == 1
    rows = [json.loads(line) for line in output.getvalue().splitlines()]
    assert rows == [{
        "type": "result", "id": None,
        "result": {"ok": False, "stage": "startup", "error": "SenseVoice cache is missing"},
    }]


def test_real_loop_uses_new_reply_directory_and_cannot_change_old_wakeword(tmp_path, monkeypatch):
    worker = load_worker()
    root = Path(__file__).resolve().parents[2]
    monkeypatch.syspath_prepend(str(root))
    from src.brain.voice import asr
    from src.brain import voice_loop

    warmed = []
    monkeypatch.setattr(asr, "_load_sherpa_asr", lambda: warmed.append(True))

    def forbidden(*args, **kwargs):
        pytest.fail("new listener attempted an old wakeword transaction")

    monkeypatch.setattr(voice_loop.WakewordChangeCoordinator, "submit", forbidden)
    monkeypatch.setattr(voice_loop, "save_user_override", forbidden)
    # build_loop binds a process-local backend; restore the shared test process.
    monkeypatch.setattr(voice_loop, "tts_synthesize", voice_loop.tts_synthesize)
    loop = worker.build_loop(tmp_path)
    assert warmed == [True]
    assert loop.reply_dir == tmp_path / "data" / "voice-next" / "replies"
    assert loop.pusher.command_file == tmp_path / "data" / "host" / "orb_command.json"
    assert loop.bridge.loop.queue_root == tmp_path / "tasks"
    assert loop.bridge.loop._wakeword_change_submitter is None
    response = loop.bridge.handle("把唤醒词改成星期五。")
    assert response.handled is True
    assert response.ok is True
    assert "你好问问" in response.text
    assert "固定" in response.text
    assert not (tmp_path / "data" / "host" / "orb_command.json").exists()


@pytest.mark.parametrize("one_shot", [False, True])
def test_cli_keeps_native_and_python_logs_off_json_stdout(tmp_path, one_shot):
    load_worker()
    wav = make_wav(tmp_path / "data" / "turn.wav")
    code = r'''
import importlib.util, os, sys
from pathlib import Path
spec = importlib.util.spec_from_file_location("worker", sys.argv[1])
worker = importlib.util.module_from_spec(spec)
spec.loader.exec_module(worker)
worker.ROOT = Path(sys.argv[2])
class Loop:
    def handle_audio(self, path, *, reply_timeout):
        os.write(1, b"native ASR diagnostic\n")
        print("Python ASR diagnostic")
        return {"ok": True, "text": "现在几点", "stage": "tts"}
def load(root):
    os.write(1, b"native import diagnostic\n")
    print("Python prewarm diagnostic")
    return Loop()
worker.build_loop = load
raise SystemExit(worker.main(sys.argv[3:]))
'''
    args = [sys.executable, "-X", "utf8", "-c", code, str(WORKER_FILE), str(tmp_path)]
    if one_shot:
        args.extend(["--wav", str(wav)])
    child = subprocess.run(
        args,
        input=json_lines({"id": "cli-turn", "wav": str(wav)}, {"op": "shutdown"}).getvalue(),
        capture_output=True, text=True, encoding="utf-8", timeout=20,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert child.returncode == 0, child.stderr
    assert child.stdout.isascii()
    rows = [json.loads(line) for line in child.stdout.splitlines()]
    assert [row["type"] for row in rows] == ["ready", "started", "result"]
    assert rows[0]["asr_ready"] is True
    assert rows[0]["tts_backend"] == "windows-sapi-fallback"
    assert rows[2]["result"]["text"] == "现在几点"
    assert "native import diagnostic" in child.stderr
    assert "native ASR diagnostic" in child.stderr
    assert "Python prewarm diagnostic" in child.stderr
    assert "Python ASR diagnostic" in child.stderr


@pytest.mark.skipif(os.name != "nt" or not shutil.which("pwsh"), reason="Windows PowerShell 7 required")
def test_existing_loop_uses_sapi_without_entering_legacy_cold_start(tmp_path, monkeypatch):
    worker = load_worker()
    monkeypatch.syspath_prepend(str(Path(__file__).resolve().parents[2]))
    from src.brain import voice_loop
    from src.brain.voice import asr

    def forbidden(*args, **kwargs):
        raise AssertionError("legacy TTS must never start in the fast new entry")

    monkeypatch.setattr(voice_loop, "tts_synthesize", forbidden)
    monkeypatch.setattr(asr, "_load_sherpa_asr", lambda: None)
    monkeypatch.setattr(voice_loop, "asr_transcribe", lambda path: {
        "ok": True, "text": "把唤醒词改成星期五。", "model": "offline-test",
    })
    loop = worker.build_loop(tmp_path)
    result = loop.handle_audio(make_wav(tmp_path / "data" / "turn.wav"), reply_timeout=30)
    assert result["ok"] is True, result
    tts = result["tts"]
    assert tts["engine"] == "windows-sapi-fallback"
    assert tts["fallback_reason"] == "legacy_cv3_cold_start_budget"
    assert tts["wav"] == result["reply_wav"]
    assert tts["rate"] == 16000
    with wave.open(result["reply_wav"], "rb") as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, 16000)
        assert tts["seconds"] == audio.getnframes() / 16000
        assert audio.getnframes() > 1600
    assert not list(loop.reply_dir.glob(".sapi-*.json"))


def test_sapi_adapter_caps_process_budget_and_returns_timeout_error(tmp_path, monkeypatch):
    worker = load_worker()

    def time_out(command, **kwargs):
        assert Path(command[0]).name.lower() in {"pwsh", "pwsh.exe"}
        assert kwargs["timeout"] == 30
        raise subprocess.TimeoutExpired(command, kwargs["timeout"])

    monkeypatch.setattr(subprocess, "run", time_out)
    result = worker.sapi_synthesize("你好。", tmp_path / "reply.wav", timeout=300)
    assert result["ok"] is False
    assert result["engine"] == "windows-sapi-fallback"
    assert result["fallback_reason"] == "legacy_cv3_cold_start_budget"
    assert "timed out" in result["error"]
    assert not list(tmp_path.glob(".sapi-*.json"))


@pytest.mark.skipif(os.name != "nt" or not shutil.which("pwsh"), reason="Windows PowerShell 7 required")
def test_sapi_generates_only_pcm16_mono_16k_wav_from_json(tmp_path):
    assert SAPI_FILE.is_file(), "file-only SAPI renderer is not implemented"
    output = tmp_path / "答复 with spaces.wav"
    request = tmp_path / "request.json"
    request.write_text(json.dumps({"text": "你好问问。$(throw 'text must not execute')", "output": str(output)}, ensure_ascii=False), encoding="utf-8")
    child = subprocess.run(
        [shutil.which("pwsh"), "-NoProfile", "-NonInteractive", "-File", str(SAPI_FILE), "-Request", str(request)],
        capture_output=True, text=True, encoding="utf-8", errors="replace", timeout=30,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    assert child.returncode == 0, child.stderr
    assert json.loads(child.stdout)["wav"] == str(output)
    with wave.open(str(output), "rb") as audio:
        assert (audio.getnchannels(), audio.getsampwidth(), audio.getframerate()) == (1, 2, 16000)
        assert audio.getnframes() > 1600
        assert audio.getcomptype() == "NONE"
