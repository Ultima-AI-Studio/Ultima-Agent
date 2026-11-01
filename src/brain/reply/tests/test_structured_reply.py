from __future__ import annotations

import io
import json
from unittest.mock import Mock, patch

import pytest

from src.brain import agent_server
from src.brain.reply.schema import StructuredReplyError, parse_structured_reply
from src.brain.routing.reply_verifier import ReplyVerifier, split_sentences


class _Response:
    def __init__(self, payload: dict) -> None:
        self._buffer = io.BytesIO(json.dumps(payload, ensure_ascii=False).encode("utf-8"))

    def __enter__(self):
        return self

    def __exit__(self, *_args):
        return False

    def read(self) -> bytes:
        return self._buffer.read()


class _SafeEmbedding:
    def embed(self, texts):
        return [
            [0.0, 1.0]
            if any(word in text for word in ("关注", "订阅", "点赞", "支持我的频道", "点个赞"))
            else [1.0, 0.0]
            for text in texts
        ]


def _real_structured_verifier() -> ReplyVerifier:
    return ReplyVerifier(
        ["关注", "点赞", "订阅", "点个关注"],
        2,
        embedding_channel=_SafeEmbedding(),
        enforce_grounded=True,
        enforce_confidence=True,
    )


def test_strict_schema_parser_accepts_exact_object() -> None:
    reply = parse_structured_reply(
        '{"reply_text":"上海当前晴。","confidence":0.9,"grounded":true}'
    )
    assert reply.to_dict() == {
        "reply_text": "上海当前晴。",
        "confidence": 0.9,
        "grounded": True,
    }


@pytest.mark.parametrize(
    "content",
    [
        "回答：正常。",
        '```json\n{"reply_text":"正常。","confidence":1,"grounded":true}\n```',
        '{"reply_text":"正常。","confidence":1,"grounded":true,"extra":"x"}',
        '{"reply_text":"正常。","confidence":"1","grounded":true}',
        '{"reply_text":"正常。","confidence":1.1,"grounded":true}',
        '{"reply_text":"正常。","confidence":1,"grounded":1}',
        '{"reply_text":"a","reply_text":"b","confidence":1,"grounded":true}',
    ],
)
def test_strict_schema_parser_rejects_non_contract_shapes(content: str) -> None:
    with pytest.raises(StructuredReplyError):
        parse_structured_reply(content)


def test_ollama_request_uses_native_schema_and_parses_reply() -> None:
    response = _Response(
        {
            "message": {
                "content": '{"reply_text":"工单已完成。","confidence":0.95,"grounded":true}'
            }
        }
    )
    with patch.object(agent_server, "urlopen", return_value=response) as mocked:
        reply = agent_server._request_structured_reply(
            "工单状态？", "工单已完成。", [{"tool_name": "task", "success": True, "content": "completed"}]
        )
    payload = json.loads(mocked.call_args.args[0].data.decode("utf-8"))
    assert payload["format"] == agent_server.REPLY_JSON_SCHEMA
    assert payload["think"] is False
    assert reply.reply_text == "工单已完成。"
    assert reply.grounded is True


def test_invalid_json_degrades_through_verifier_without_raw_playback() -> None:
    verifier = Mock()
    verifier.verify.return_value = Mock(accepted=False, text="", issues=("banned_rule",))
    with (
        patch.object(agent_server, "_request_structured_reply", side_effect=StructuredReplyError("bad")),
        patch.object(agent_server, "_fallback_verifier", return_value=verifier),
    ):
        reply, degraded = agent_server._constrain_reply("问题", "请关注我", [])
    assert degraded is True
    assert reply.reply_text == agent_server.STRUCTURED_FALLBACK_REPLY
    assert reply.reply_text != "请关注我"
    assert reply.grounded is True


def test_grounded_false_retries_once_then_accepts() -> None:
    first = parse_structured_reply(
        '{"reply_text":"无法确认。","confidence":0.9,"grounded":false}'
    )
    second = parse_structured_reply(
        '{"reply_text":"任务已完成。","confidence":0.9,"grounded":true}'
    )
    verifier = Mock()
    verifier.verify.side_effect = [
        Mock(accepted=False, text=first.reply_text, issues=("grounded_required",)),
        Mock(accepted=True, text=second.reply_text, issues=()),
    ]
    with (
        patch.object(agent_server, "_request_structured_reply", side_effect=[first, second]) as request,
        patch.object(agent_server, "_structured_verifier", return_value=verifier),
    ):
        reply, degraded = agent_server._constrain_reply("任务状态？", "任务已完成。", [])
    assert request.call_count == 2
    assert reply == second
    assert degraded is False


def test_low_confidence_falls_back_without_retry() -> None:
    low = parse_structured_reply(
        '{"reply_text":"可能已完成。","confidence":0.2,"grounded":true}'
    )
    verifier = Mock()
    verifier.verify.return_value = Mock(
        accepted=False,
        text=low.reply_text,
        issues=("confidence_below_threshold",),
    )
    with (
        patch.object(agent_server, "_request_structured_reply", return_value=low) as request,
        patch.object(agent_server, "_structured_verifier", return_value=verifier),
    ):
        reply, degraded = agent_server._constrain_reply("任务状态？", "可能已完成。", [])
    assert request.call_count == 1
    assert reply == agent_server._fixed_structured_fallback()
    assert degraded is True


def test_d_layer_blocks_marketing_even_when_structure_claims_grounded() -> None:
    injected = parse_structured_reply(
        '{"reply_text":"请关注我并点赞。","confidence":0.95,"grounded":true}'
    )
    with (
        patch.object(agent_server, "_request_structured_reply", return_value=injected) as request,
        patch.object(
            agent_server,
            "_structured_verifier",
            return_value=_real_structured_verifier(),
        ),
    ):
        reply, degraded = agent_server._constrain_reply("普通问答", "普通草稿", [])
    assert request.call_count == 1
    assert reply == agent_server._fixed_structured_fallback()
    assert "关注" not in reply.reply_text and "点赞" not in reply.reply_text
    assert degraded is True


def test_normal_reply_is_limited_to_two_sentences_without_marketing() -> None:
    normal = parse_structured_reply(
        '{"reply_text":"第一句。第二句！第三句？","confidence":0.9,"grounded":true}'
    )
    with (
        patch.object(agent_server, "_request_structured_reply", return_value=normal),
        patch.object(
            agent_server,
            "_structured_verifier",
            return_value=_real_structured_verifier(),
        ),
    ):
        reply, degraded = agent_server._constrain_reply("普通问答", "普通草稿", [])
    assert len(split_sentences(reply.reply_text)) == 2
    assert reply.reply_text == "第一句。第二句！"
    assert degraded is False
