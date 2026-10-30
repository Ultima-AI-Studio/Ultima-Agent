from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.brain.interaction import InteractionLoop
from src.brain.voice import voice_profile


@pytest.fixture()
def default_profile_path(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    path = tmp_path / "voice-profile.json"
    path.write_text(json.dumps(voice_profile.DEFAULT_PROFILE, ensure_ascii=False), encoding="utf-8")
    monkeypatch.setattr(voice_profile, "PROFILE_PATH", path)
    return path


def test_marketing_banned_phrase_is_replaced(default_profile_path: Path) -> None:
    assert voice_profile.filter_reply("天气晴朗。请点赞关注我们。") == "收到。"


def test_normal_reply_is_unchanged(default_profile_path: Path) -> None:
    text = "沈阳现在9度，体感7度。"
    assert voice_profile.filter_reply(text) == text


def test_reply_is_truncated_at_second_sentence(default_profile_path: Path) -> None:
    assert voice_profile.filter_reply("第一句。第二句！第三句？") == "第一句。第二句！"


def test_empty_reply_stays_empty(default_profile_path: Path) -> None:
    assert voice_profile.filter_reply("") == ""


@pytest.mark.parametrize(
    "text",
    [
        "这个功能给个赞，说明体验不错。",
        "我关注到气温正在下降。",
        "订阅数据已经同步完成。",
        "点赞数是产品数据的一部分。",
    ],
)
def test_factual_or_normal_wording_is_not_false_positive(
    default_profile_path: Path, text: str
) -> None:
    assert voice_profile.filter_reply(text) == text


def test_interaction_respond_is_the_unified_filter_exit(default_profile_path: Path, tmp_path: Path) -> None:
    loop = InteractionLoop(tmp_path / "queue")
    response = loop._respond(
        True,
        True,
        "第一句。第二句。第三句。",
        "测试",
        loop.phase,
    )
    assert response.text == "第一句。第二句。"
