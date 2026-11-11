from __future__ import annotations

import importlib.util
import json
import subprocess
import time
from pathlib import Path

import pytest

from src.brain.interaction import InteractionLoop
from src.brain import voice_loop
from src.brain.voice import voice_profile
from src.brain.voice_loop import VoiceInteractionLoop, WakewordChangeCoordinator


def _cli_result(argv, *, ok: bool = True, error: str = ""):
    payload = {
        "action": "replace",
        "hot_reload": {
            "requested": True,
            "success": ok,
            "pid_before": 24680,
            "pid_after": 24680,
            "log_pid": 24680 if ok else None,
            "same_pid": ok,
            "error": error,
        },
    }
    return subprocess.CompletedProcess(
        argv,
        0 if ok else 3,
        json.dumps(payload, ensure_ascii=False),
        "",
    )


def _wait_completion(coordinator: WakewordChangeCoordinator) -> dict:
    deadline = time.monotonic() + 3
    while time.monotonic() < deadline:
        completion = coordinator.poll_completion()
        if completion is not None:
            return completion
        time.sleep(0.01)
    raise AssertionError("wakeword transaction did not complete")


@pytest.mark.parametrize(
    "utterance",
    [
        "把唤醒词改成星期五",
        "唤醒词换成星期五",
        "以后叫星期五唤醒我",
        "把唤新词改为星期五",
        "花新词换成星期五",
        "把叫醒词改成星期五",
    ],
)
def test_wakeword_command_submits_without_waiting(
    tmp_path: Path, utterance: str
) -> None:
    submitted = []
    loop = InteractionLoop(
        tmp_path,
        wakeword_change_submitter=lambda custom: submitted.append(custom) is None,
    )

    response = loop.handle(utterance)

    assert submitted == ["星期五"]
    assert response.handled is True
    assert response.ok is True
    assert response.text == ""
    assert response.reason == "唤醒词修改已提交"


@pytest.mark.parametrize(
    "utterance",
    [
        "唤醒词改成什么",
        "把唤醒词换成哪个？",
        "把唤醒词改成星期五可以吗",
        "星期五可以吗",
    ],
)
def test_ambiguous_or_interrogative_input_is_rejected(
    tmp_path: Path, utterance: str
) -> None:
    submitted = []
    response = InteractionLoop(
        tmp_path,
        wakeword_change_submitter=lambda custom: submitted.append(custom) is None,
    ).handle(utterance)

    assert submitted == []
    assert response.handled is True
    assert response.ok is False
    assert response.reason == "唤醒词指令不明确"
    assert "请明确说" in response.text


def test_full_interaction_path_converges_after_profile_watcher_before_second_cli(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    wav = tmp_path / "command.wav"
    wav.write_bytes(b"test")
    state = {"custom": None, "keywords": "initial"}
    sequence = []
    coordinator_holder = {}

    def fake_load_profile():
        return {"wakeword": {"custom": state["custom"]}}

    def fake_save(overrides):
        custom = overrides["wakeword"]["custom"]
        state["custom"] = custom
        sequence.append(("profile-save", custom))
        state["keywords"] = f"watcher:{custom}"
        sequence.append(("watcher-write", custom))
        coordinator_holder["value"].notify_daemon_reload(
            {
                "type": "profile_applied",
                "success": True,
                "pid": 24680,
                "custom": custom,
            }
        )
        return True

    def fake_run(argv, **_kwargs):
        words = list(argv)[list(argv).index("--replace") + 1 :]
        custom = words[-1] if len(words) > 1 else None
        state["keywords"] = f"cli:{custom}"
        sequence.append(("cli-write", custom))
        return _cli_result(argv)

    def fake_tts(text, output, **_kwargs):
        Path(output).write_bytes(b"RIFF")
        return {"ok": True, "text": text}

    monkeypatch.setattr(voice_loop, "load_profile", fake_load_profile)
    monkeypatch.setattr(voice_loop, "save_user_override", fake_save)
    monkeypatch.setattr(voice_loop, "_run_process", fake_run)
    monkeypatch.setattr(voice_loop, "tts_synthesize", fake_tts)
    monkeypatch.setattr(
        voice_loop,
        "asr_transcribe",
        lambda _wav: {"ok": True, "text": "把唤醒词改成星期五"},
    )

    loop = VoiceInteractionLoop(
        queue_root=tmp_path / "tasks",
        command_file=tmp_path / "orb-command.json",
        reply_dir=tmp_path / "replies",
    )
    coordinator_holder["value"] = loop.wakeword_changes

    result = loop.handle_audio(wav)
    completion = _wait_completion(loop.wakeword_changes)

    assert result["response"]["reason"] == "唤醒词修改已提交"
    assert completion["ok"] is True
    assert completion["text"] == "唤醒词已改为星期五。"
    assert completion["tts"]["ok"] is True
    assert state == {"custom": "星期五", "keywords": "cli:星期五"}
    assert sequence == [
        ("cli-write", "星期五"),
        ("profile-save", "星期五"),
        ("watcher-write", "星期五"),
        ("cli-write", "星期五"),
    ]


@pytest.mark.parametrize("failure_stage", ["first_cli", "profile_save", "second_cli"])
def test_each_partial_failure_rolls_back_and_announces_failure(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
    failure_stage: str,
) -> None:
    state = {"custom": "星期四", "keywords": "cli:星期四"}
    calls = {"target_cli": 0}
    coordinator_holder = {}

    monkeypatch.setattr(
        voice_loop,
        "load_profile",
        lambda: {"wakeword": {"custom": state["custom"]}},
    )

    def fake_save(overrides):
        custom = overrides["wakeword"]["custom"]
        state["custom"] = custom
        coordinator_holder["value"].notify_daemon_reload(
            {
                "type": "profile_applied",
                "success": True,
                "pid": 24680,
                "custom": custom,
            }
        )
        return not (failure_stage == "profile_save" and custom == "星期五")

    def fake_run(argv, **_kwargs):
        words = list(argv)[list(argv).index("--replace") + 1 :]
        custom = words[-1] if len(words) > 1 else None
        if custom == "星期五":
            calls["target_cli"] += 1
            should_fail = (
                failure_stage == "first_cli" and calls["target_cli"] == 1
            ) or (
                failure_stage == "second_cli" and calls["target_cli"] == 2
            )
            if should_fail:
                state["keywords"] = "partial:星期五"
                return _cli_result(argv, ok=False, error=failure_stage)
        state["keywords"] = f"cli:{custom}"
        return _cli_result(argv)

    def fake_tts(text, output, **_kwargs):
        Path(output).write_bytes(b"RIFF")
        return {"ok": True, "text": text}

    monkeypatch.setattr(voice_loop, "save_user_override", fake_save)
    monkeypatch.setattr(voice_loop, "_run_process", fake_run)
    monkeypatch.setattr(voice_loop, "tts_synthesize", fake_tts)
    coordinator = WakewordChangeCoordinator(tmp_path, profile_wait_timeout=0.2)
    coordinator_holder["value"] = coordinator

    assert coordinator.submit("星期五")
    completion = _wait_completion(coordinator)

    assert completion["ok"] is False
    assert completion["rollback_ok"] is True
    assert completion["text"] == "唤醒词修改失败，请稍后再试。"
    assert state == {"custom": "星期四", "keywords": "cli:星期四"}


def test_profile_watcher_timeout_rolls_back(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    state = {"custom": None}
    monkeypatch.setattr(
        voice_loop,
        "load_profile",
        lambda: {"wakeword": {"custom": state["custom"]}},
    )
    monkeypatch.setattr(
        voice_loop,
        "save_user_override",
        lambda overrides: state.update(custom=overrides["wakeword"]["custom"]) is None,
    )
    monkeypatch.setattr(
        voice_loop,
        "_run_process",
        lambda argv, **_kwargs: _cli_result(argv),
    )
    monkeypatch.setattr(
        voice_loop,
        "tts_synthesize",
        lambda *_args, **_kwargs: {"ok": True},
    )
    coordinator = WakewordChangeCoordinator(tmp_path, profile_wait_timeout=0.02)

    assert coordinator.submit("星期五")
    completion = _wait_completion(coordinator)

    assert completion["ok"] is False
    assert "watcher" in completion["error"]
    assert state["custom"] is None


def _load_daemon_module():
    path = voice_profile.ROOT / "data" / "logs" / "voice-listen-daemon.py"
    spec = importlib.util.spec_from_file_location("voice_listen_daemon_entry_test", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_daemon_emits_profile_and_keyword_reload_completion(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    daemon = _load_daemon_module()
    keywords = tmp_path / "keywords.txt"
    profile = tmp_path / "voice-profile.json"
    keywords.write_text("old @OLD\n", encoding="utf-8")
    profile.write_text("{}", encoding="utf-8")
    monkeypatch.setattr(daemon, "KWS_KEYWORDS", keywords)
    monkeypatch.setattr(daemon, "VOICE_PROFILE", profile)
    monkeypatch.setattr(voice_profile, "apply_to_daemon", lambda _profile: True)
    monkeypatch.setattr(voice_profile, "load_profile", lambda: voice_profile.DEFAULT_PROFILE)

    class FakeSpotter:
        def create_stream(self):
            return object()

    manager = daemon.HotReloadSpotter(FakeSpotter)
    time.sleep(0.01)
    profile.write_text('{"wakeword": {}}', encoding="utf-8")
    keywords.write_text("new @NEW\n", encoding="utf-8")

    manager.maybe_reload()
    events = manager.drain_reload_events()

    assert [event["type"] for event in events] == [
        "profile_applied",
        "keywords_reloaded",
    ]
    assert all(event["success"] is True for event in events)
