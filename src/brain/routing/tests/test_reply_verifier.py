from __future__ import annotations

from unittest.mock import Mock, patch

from src.brain.interaction import InteractionLoop
from src.brain.routing.reply_verifier import ReplySchema, ReplyVerifier


class FakeEmbeddingChannel:
    def embed(self, texts):
        result = []
        for text in texts:
            if text == "劳烦持续留意这个账号":
                result.append([0.0, 1.0])
            elif any(word in text for word in ("关注", "点赞", "订阅", "支持我的频道", "点个赞")):
                result.append([0.0, 1.0])
            else:
                result.append([1.0, 0.0])
        return result


def make_verifier(*, enforce_grounded: bool = False) -> ReplyVerifier:
    return ReplyVerifier(
        ["关注", "点赞", "订阅", "点个关注"],
        2,
        embedding_channel=FakeEmbeddingChannel(),
        enforce_grounded=enforce_grounded,
    )


def test_rule_banned_phrase_is_rejected() -> None:
    result = make_verifier().verify("天气晴朗。请关注我。")
    assert not result.accepted
    assert "banned_rule" in result.issues


def test_semantic_banned_phrase_is_rejected() -> None:
    result = make_verifier().verify("劳烦持续留意这个账号")
    assert not result.accepted
    assert "banned_semantic" in result.issues


def test_sentence_limit_is_hard_truncated() -> None:
    result = make_verifier().verify("第一句。第二句！第三句？")
    assert result.accepted
    assert result.text == "第一句。第二句！"
    assert result.issues == ("sentence_limit_truncated",)


def test_grounded_schema_is_reserved_but_disabled_by_default() -> None:
    schema = ReplySchema("有依据的回答。", confidence=0.8, grounded=False)
    assert make_verifier().verify(schema).accepted
    enforced = make_verifier(enforce_grounded=True).verify(schema)
    assert not enforced.accepted
    assert "grounded_required" in enforced.issues


def test_interaction_retries_once_then_accepts(tmp_path) -> None:
    verifier = make_verifier()
    ask = Mock(side_effect=["请关注我。", "天气晴朗。"])
    with patch("src.brain.agent_client.agent_healthy", return_value=True), patch(
        "src.brain.agent_client.ask_agent", ask
    ), patch("src.brain.interaction.get_reply_verifier", return_value=verifier):
        reply = InteractionLoop(tmp_path / "queue")._try_agent_fallback("聊聊天")
    assert reply is not None
    assert reply.text == "天气晴朗。"
    assert reply.reason == "Agent 回答重试"
    assert ask.call_count == 2


def test_interaction_retries_once_then_falls_back(tmp_path) -> None:
    verifier = make_verifier()
    ask = Mock(side_effect=["请关注我。", "请订阅我。"])
    with patch("src.brain.agent_client.agent_healthy", return_value=True), patch(
        "src.brain.agent_client.ask_agent", ask
    ), patch("src.brain.interaction.get_reply_verifier", return_value=verifier):
        reply = InteractionLoop(tmp_path / "queue")._try_agent_fallback("聊聊天")
    assert reply is not None
    assert reply.text == "收到。"
    assert reply.reason == "Agent 回答兜底"
    assert ask.call_count == 2
