from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.brain.voice import voice_profile


@pytest.fixture()
def profile_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "config" / "voice-profile.json"
    monkeypatch.setattr(voice_profile, "PROFILE_PATH", path)
    return path


def _write(path: Path, value: object) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(value, ensure_ascii=False), encoding="utf-8")


def test_missing_file_returns_l1_defaults(profile_path: Path) -> None:
    assert voice_profile.load_profile() == voice_profile.DEFAULT_PROFILE


def test_broken_json_returns_l1_defaults(profile_path: Path) -> None:
    profile_path.parent.mkdir(parents=True)
    profile_path.write_text("{broken", encoding="utf-8")
    assert voice_profile.load_profile() == voice_profile.DEFAULT_PROFILE


def test_l2_override_is_applied(profile_path: Path) -> None:
    _write(profile_path, {"persona": {"override": "config/custom-persona.md"}})
    loaded = voice_profile.load_profile()
    assert loaded["persona"]["override"] == "config/custom-persona.md"
    assert loaded["persona"]["name"] == "jarvis"


def test_l3_wins_over_l2(profile_path: Path) -> None:
    _write(profile_path, {"style": {"max_sentences": 4}})
    loaded = voice_profile.load_profile({"style": {"max_sentences": 1}})
    assert loaded["style"]["max_sentences"] == 1


def test_save_then_reload_preserves_other_fields(profile_path: Path) -> None:
    _write(
        profile_path,
        {
            "persona": {"name": "jarvis", "override": None},
            "wakeword": {"words": ["custom token @保留"], "custom": None},
            "style": {"mode": "efficient-jarvis", "banned_phrases": ["关注"], "max_sentences": 2},
            "input": {"mode": "auto", "device_index": None, "prefer_wasapi48k": True},
        },
    )
    assert voice_profile.save_user_override({"input": {"device_index": 7}})
    loaded = voice_profile.load_profile()
    assert loaded["input"]["device_index"] == 7
    assert loaded["wakeword"]["words"] == ["custom token @保留"]


def test_missing_fields_fall_back_individually(profile_path: Path) -> None:
    _write(profile_path, {"style": {"max_sentences": 1}})
    loaded = voice_profile.load_profile()
    assert loaded["style"]["max_sentences"] == 1
    assert loaded["style"]["mode"] == "efficient-jarvis"
    assert loaded["input"]["prefer_wasapi48k"] is True


def test_invalid_values_fall_back_to_defaults(profile_path: Path) -> None:
    _write(
        profile_path,
        {
            "style": {"max_sentences": 0, "banned_phrases": "点赞"},
            "input": {"mode": "cloud", "device_index": -1, "prefer_wasapi48k": "yes"},
        },
    )
    loaded = voice_profile.load_profile()
    assert loaded["style"] == voice_profile.DEFAULT_PROFILE["style"]
    assert loaded["input"] == voice_profile.DEFAULT_PROFILE["input"]


def test_save_ignores_non_l2_fields(profile_path: Path) -> None:
    assert voice_profile.save_user_override(
        {"persona": {"name": "other"}, "wakeword": {"words": ["changed"]}}
    )
    loaded = voice_profile.load_profile()
    assert loaded["persona"]["name"] == "jarvis"
    assert loaded["wakeword"]["words"] == voice_profile.DEFAULT_PROFILE["wakeword"]["words"]
