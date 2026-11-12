"""主脑教学 Phase 2 多轮澄清与防误伤测试。"""

import inspect
import time
from unittest.mock import patch

import pytest

from src.brain import agent_server


@pytest.fixture(autouse=True)
def _restore_pending_clarify_state():
    old_pending = getattr(agent_server, "_PENDING_CLARIFY", None)
    if hasattr(agent_server, "_PENDING_CLARIFY"):
        agent_server._PENDING_CLARIFY = None
    try:
        yield
    finally:
        if hasattr(agent_server, "_PENDING_CLARIFY"):
            agent_server._PENDING_CLARIFY = old_pending


@pytest.mark.parametrize(
    ("query", "expected"),
    (
        pytest.param("帮我把那个弄一下", "referent", id="F1-pure-referent"),
        pytest.param("打开", "object", id="F2-missing-object"),
        pytest.param("呃那个嗯", "noise", id="F3-noise-utterance"),
        pytest.param("把文件发给他", "object", id="F5-generic-object"),
        pytest.param("嗯", "noise", id="F6-short-noise"),
        pytest.param("那个东西还是不行", "referent", id="F7-unclear-referent"),
        pytest.param(
            "帮我查一下天气然后整理桌面",
            None,
            id="F4-no-tool-compound-request",
        ),
        pytest.param(
            "帮我把桌面的日志整理一下",
            None,
            id="R1-specific-qualified-object",
        ),
        pytest.param(
            r"帮我把 D:\logs\a.log 重命名成 b.log",
            None,
            id="R2-specific-path-object",
        ),
        pytest.param("1+1等于几", None, id="R3-arithmetic-query"),
        pytest.param("什么是市盈率", None, id="R4-definition-query"),
    ),
)
def test_slot_gate_classifies_only_missing_slots(query, expected):
    assert agent_server._slot_gate(query) == expected


@pytest.mark.parametrize(
    ("slot", "expected"),
    (
        pytest.param(
            "object",
            "你要我处理哪个？给我个具体名字，比如文件名或路径。",
            id="object-template",
        ),
        pytest.param(
            "referent",
            "你说的「那个」是指哪一个？说一下名字我就能动。",
            id="referent-template",
        ),
        pytest.param(
            "noise",
            "没听清，再说一遍要做什么。",
            id="noise-template",
        ),
    ),
)
def test_clarify_reply_uses_fixed_directional_template(slot, expected):
    reply = agent_server._clarify_reply(slot)

    assert reply == expected
    assert "需要我" not in reply


def test_clarify_reply_unknown_slot_falls_back_to_noise_template():
    assert agent_server._clarify_reply("unknown") == "没听清，再说一遍要做什么。"


def test_clean_content_replaces_pushback_with_directional_reply():
    assert agent_server._clean_content("你再说一遍？") == agent_server._PUSHBACK_REPLY


def test_clean_content_replaces_only_pushback_sentence():
    content = "市盈率是股价除以每股收益。如果没听清，你再说一遍？"

    assert agent_server._clean_content(content) == (
        f"市盈率是股价除以每股收益。{agent_server._PUSHBACK_REPLY}"
    )


def test_clean_content_keeps_quoted_pushback_phrase_unchanged():
    content = "“你再说一遍”这句话不够具体。"

    assert agent_server._clean_content(content) == content


def test_clean_content_keeps_unrelated_short_answer_unchanged():
    content = "1+1等于2。"

    assert agent_server._clean_content(content) == content


@pytest.mark.parametrize(
    ("content", "expected"),
    (
        pytest.param(
            "您有什么可以帮您？",
            "您有什么可以帮您？",
            id="phase1-degenerate-servile-output",
        ),
        pytest.param(
            "您问的是贾维斯，Ultima Agent主脑。有什么可以帮您？",
            "您问的是贾维斯，Ultima Agent主脑。",
            id="phase1-strip-servile-tail",
        ),
        pytest.param(
            "grounded:false 不确定。",
            "不确定。",
            id="phase1-strip-grounded-marker",
        ),
    ),
)
def test_clean_content_preserves_phase1_contracts(content, expected):
    assert agent_server._clean_content(content) == expected


@pytest.mark.parametrize(
    ("original", "supplement", "slot"),
    (
        pytest.param(
            "帮我把那个弄一下",
            "就是桌面那个日志文件",
            "referent",
            id="G1-fill-referent",
        ),
        pytest.param("打开", "应用", "object", id="G2-fill-object"),
    ),
)
def test_ask_once_fills_pending_query_before_classification(original, supplement, slot):
    agent_server._pending_set(original, slot)
    task_result = {
        "content": "已进入正常任务分支",
        "reply_text": "已进入正常任务分支",
        "intent": "task",
        "tool_results": [],
    }

    with (
        patch.object(agent_server, "_classify_intent", return_value="task"),
        patch.object(agent_server, "_ask_task_branch", return_value=task_result) as branch,
    ):
        result = agent_server.ask_once(supplement)

    assert result["intent"] == "task"
    branch.assert_called_once_with(f"{original}（补充：{supplement}）")
    assert agent_server._PENDING_CLARIFY is None


def test_ask_once_discards_expired_pending_with_fixed_reply():
    agent_server._pending_set("嗯", "noise")
    agent_server._PENDING_CLARIFY["at"] = time.time() - 60

    with patch.object(agent_server, "_classify_intent") as classify:
        result = agent_server.ask_once("帮我整理日志")

    assert result["intent"] == "clarify"
    assert result["content"] == "先不弄了，需要的时候再叫我。"
    assert agent_server._PENDING_CLARIFY is None
    classify.assert_not_called()


def test_ask_once_gives_up_when_same_request_reaches_max_asks():
    agent_server._pending_set("打开", "object")
    agent_server._pending_set("打开", "object")

    with patch.object(agent_server, "_classify_intent") as classify:
        result = agent_server.ask_once("应用")

    assert result["intent"] == "clarify"
    assert result["content"] == "先不弄了，需要的时候再叫我。"
    assert agent_server._PENDING_CLARIFY is None
    classify.assert_not_called()


def test_ask_once_counts_real_clarification_turns_and_then_gives_up():
    with (
        patch.object(agent_server, "_classify_intent", return_value="task"),
        patch.object(agent_server, "_ask_task_branch") as task_branch,
    ):
        first = agent_server.ask_once("帮我把那个弄一下")
        second = agent_server.ask_once("那个")
        third = agent_server.ask_once("那个")

    assert first["intent"] == "clarify"
    assert second["intent"] == "clarify"
    assert third["intent"] == "clarify"
    assert third["content"] == "先不弄了，需要的时候再叫我。"
    task_branch.assert_not_called()


def test_ask_once_does_not_accept_noise_as_object_supplement():
    with (
        patch.object(agent_server, "_classify_intent", return_value="task"),
        patch.object(agent_server, "_ask_task_branch") as task_branch,
    ):
        first = agent_server.ask_once("打开")
        second = agent_server.ask_once("嗯")

    assert first["intent"] == "clarify"
    assert second["intent"] == "clarify"
    task_branch.assert_not_called()


def test_ask_once_rechecks_risk_gate_after_pending_merge():
    with (
        patch.object(agent_server, "_classify_intent", return_value="task"),
        patch.object(agent_server, "_ask_task_branch") as task_branch,
    ):
        first = agent_server.ask_once("删除")
        second = agent_server.ask_once("D盘")

    assert first["intent"] == "clarify"
    assert second["intent"] == "refused"
    assert second["content"] == (
        "这个我不做，也不会派出去。刚才那句我理解的是越界操作，不再展开。"
    )
    task_branch.assert_not_called()


def test_ask_once_signature_remains_compatible():
    assert str(inspect.signature(agent_server.ask_once)) == (
        "(query: 'str', max_tokens: 'int | None' = None) -> 'dict[str, Any]'"
    )


@pytest.mark.parametrize(
    ("query", "classifier_verdict", "expected_fragment"),
    (
        pytest.param("帮我把那个弄一下", "task", "名字", id="F1-task-referent"),
        pytest.param("打开", "query", "文件名或路径", id="F2-query-object"),
        pytest.param("呃那个嗯", "query", "要做什么", id="F3-query-noise"),
        pytest.param("把文件发给他", "task", "文件名或路径", id="F5-task-object"),
        pytest.param("嗯", "query", "要做什么", id="F6-query-noise"),
        pytest.param("那个东西还是不行", "query", "哪一个", id="F7-query-referent"),
    ),
)
def test_ask_once_routes_missing_slots_to_clarify(
    query, classifier_verdict, expected_fragment
):
    with (
        patch.object(agent_server, "_classify_intent", return_value=classifier_verdict),
        patch.object(agent_server, "_ask_task_branch") as task_branch,
        patch.object(agent_server, "_ask_query_branch") as query_branch,
    ):
        result = agent_server.ask_once(query)

    assert result["intent"] == "clarify"
    assert expected_fragment in result["content"]
    assert "已派给" not in result["content"]
    assert "你再说一遍" not in result["content"]
    assert {
        "content",
        "reply_text",
        "confidence",
        "grounded",
        "intent",
        "tool_results",
        "usage",
    } <= result.keys()
    task_branch.assert_not_called()
    query_branch.assert_not_called()


def test_ask_once_keeps_no_tool_compound_request_unchanged():
    with patch.object(agent_server, "_classify_intent") as classify:
        result = agent_server.ask_once("帮我查一下天气然后整理桌面")

    assert result["intent"] == "no_tool"
    classify.assert_not_called()


def test_slot_gate_blocks_action_before_generic_object():
    assert agent_server._slot_gate("打开文件") == "object"


@pytest.mark.parametrize(
    "query",
    (
        pytest.param("东西方文化有什么差异", id="word-containing-dongxi"),
        pytest.param("解释这些概念：封装、继承、多态", id="listed-concepts"),
        pytest.param("帮我打开那个计算器", id="named-referent-object"),
    ),
)
def test_slot_gate_keeps_complete_normal_requests(query):
    assert agent_server._slot_gate(query) is None


@pytest.mark.parametrize(
    ("original", "supplement", "first_verdict"),
    (
        pytest.param(
            "帮我把那个弄一下",
            "就是桌面那个日志文件",
            "task",
            id="G1-two-turn-referent-fill",
        ),
        pytest.param("打开", "应用", "query", id="G2-two-turn-object-fill"),
    ),
)
def test_ask_once_two_turn_clarification_reaches_normal_task_branch(
    original, supplement, first_verdict
):
    task_result = {
        "content": "已进入正常任务分支",
        "reply_text": "已进入正常任务分支",
        "intent": "task",
        "tool_results": [],
    }

    with (
        patch.object(
            agent_server,
            "_classify_intent",
            side_effect=(first_verdict, "task"),
        ),
        patch.object(agent_server, "_ask_task_branch", return_value=task_result) as branch,
    ):
        first = agent_server.ask_once(original)
        second = agent_server.ask_once(supplement)

    assert first["intent"] == "clarify"
    assert second["intent"] == "task"
    branch.assert_called_once_with(f"{original}（补充：{supplement}）")


@pytest.mark.parametrize(
    "query",
    (
        pytest.param("帮我把桌面的日志整理一下", id="R1-qualified-object"),
        pytest.param(
            r"帮我把 D:\logs\a.log 重命名成 b.log",
            id="R2-path-object",
        ),
    ),
)
def test_ask_once_does_not_block_specific_tasks(query):
    task_result = {
        "content": "正常派单",
        "reply_text": "正常派单",
        "intent": "task",
        "tool_results": [],
    }

    with (
        patch.object(agent_server, "_classify_intent", return_value="task"),
        patch.object(agent_server, "_ask_task_branch", return_value=task_result) as branch,
    ):
        result = agent_server.ask_once(query)

    assert result["intent"] == "task"
    branch.assert_called_once_with(query)


def test_ask_once_preserves_phase1_deictic_file_task_probe():
    query = "帮我把这个文件重命名，可以吗"
    task_result = {
        "content": "正常派单",
        "reply_text": "正常派单",
        "intent": "task",
        "tool_results": [],
    }

    with (
        patch.object(agent_server, "_classify_intent", return_value="task"),
        patch.object(agent_server, "_ask_task_branch", return_value=task_result) as branch,
    ):
        result = agent_server.ask_once(query)

    assert agent_server._slot_gate(query) is None
    assert result["intent"] == "task"
    branch.assert_called_once_with(query)


def test_ask_once_preserves_phase1_specific_interface_diagnosis_probe():
    query = "这个接口报500错误怎么修"

    with patch.object(agent_server, "_classify_intent", return_value="query"):
        result = agent_server.ask_once(query)

    assert agent_server._slot_gate(query) is None
    assert result["intent"] == "query"
    assert "服务端日志" in result["content"]


@pytest.mark.parametrize(
    ("query", "answer"),
    (
        pytest.param("1+1等于几", "1+1等于2。", id="R3-arithmetic-query"),
        pytest.param(
            "什么是市盈率",
            "市盈率是股价除以每股收益。",
            id="R4-definition-query",
        ),
    ),
)
def test_ask_once_does_not_block_answerable_queries(query, answer):
    query_result = {
        "content": answer,
        "reply_text": answer,
        "confidence": 1.0,
        "grounded": True,
        "intent": "query",
        "tool_results": [],
        "usage": {},
    }

    with (
        patch.object(agent_server, "_classify_intent", return_value="query"),
        patch.object(agent_server, "_ask_query_branch", return_value=query_result) as branch,
    ):
        result = agent_server.ask_once(query)

    assert result == query_result
    branch.assert_called_once_with(query, None)
