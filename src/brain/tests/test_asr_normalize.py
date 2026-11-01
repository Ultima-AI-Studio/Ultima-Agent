from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest

from src.brain.interaction import (
    InteractionLoop,
    _DEFAULT_ASR_NEAR_HOMOPHONE,
    _load_asr_near_homophones,
    _normalize_utterance,
)
from src.brain.voice.asr import _INLINE_FASTER_SCRIPT


def test_initial_prompt_contains_bounded_high_frequency_terms() -> None:
    prompt = _INLINE_FASTER_SCRIPT.split('initial_prompt="', 1)[1].split('",', 1)[0]
    for term in ("天气", "明天", "今天", "几点", "温度", "风", "雨", "雪", "上海", "时间", "日程", "任务", "进度"):
        assert term in prompt
    assert len(prompt) <= 120


@pytest.mark.parametrize(
    ("raw", "expected"),
    [
        ("查一下明天的水量天听", "查一下明天的天气"),
        ("明天上海的水天", "明天上海的天气"),
        ("请介绍水田种植技术", "请介绍水田种植技术"),
        ("水天一色是一句成语", "水天一色是一句成语"),
        ("看看水天一色", "看看水天一色"),
        ("请问水天一色是什么意思", "请问水天一色是什么意思"),
        ("今天看到水天一色", "今天看到水天一色"),
    ],
)
def test_literal_phrase_normalization(raw: str, expected: str) -> None:
    assert _normalize_utterance(raw) == expected


def test_config_contains_metadata_and_forbids_single_character_entries() -> None:
    payload = json.loads(
        (Path(__file__).resolve().parents[3] / "config" / "asr-normalize.json").read_text(
            encoding="utf-8"
        )
    )
    assert payload["matching"] == "literal_phrase"
    assert all(len(row["from"]) >= 2 for row in payload["mappings"])
    assert all(row["source"] and row["verification"] for row in payload["mappings"])


@pytest.mark.parametrize("content", [None, "{broken json", '{"mappings": []}'])
def test_missing_or_invalid_config_falls_back(tmp_path, content: str | None) -> None:
    path = tmp_path / "asr-normalize.json"
    if content is not None:
        path.write_text(content, encoding="utf-8")
    assert _load_asr_near_homophones(path) == _DEFAULT_ASR_NEAR_HOMOPHONE


@pytest.mark.parametrize(
    "raw",
    ["查一下明天的水量天听", "明天上海的水天"],
)
def test_contextual_correction_reaches_weather_intent(tmp_path, raw: str) -> None:
    with patch("src.brain.weather.query_weather", return_value="上海明天晴，气温18度。") as weather:
        reply = InteractionLoop(tmp_path / "queue").handle(raw)
    assert reply.reason == "天气查询"
    assert reply.text == "上海明天晴，气温18度。"
    weather.assert_called_once()


@pytest.mark.parametrize(
    "raw",
    ["看看水天一色", "请问水天一色是什么意思", "今天看到水天一色"],
)
def test_idiom_with_query_words_does_not_reach_weather(tmp_path, raw: str) -> None:
    with patch("src.brain.weather.query_weather", return_value="不应调用") as weather, patch(
        "src.brain.agent_client.agent_healthy", return_value=False
    ):
        reply = InteractionLoop(tmp_path / "queue").handle(raw)
    assert reply.reason != "天气查询"
    weather.assert_not_called()
