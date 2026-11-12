"""主脑教学 Phase 3 确定性前置层测试。"""

from unittest.mock import patch

import pytest

from src.brain import agent_server


_LOCAL_DELEGATED = (
    "帮我把桌面的日志整理一下",
    "帮我把日志清理一下",
    "帮我把那个文件删掉",
    "打开浏览器",
)

_DELIVERABLE_TASKS_PRECLASSIFIED = (
    "帮我写一份周报",
    "帮我起草一份技术方案",
)

_DELIVERABLE_TASKS_VIA_CLASSIFIER = (
    "帮我把这段代码优化一下",
)

_DELIVERABLE_TASKS = (
    _DELIVERABLE_TASKS_PRECLASSIFIED + _DELIVERABLE_TASKS_VIA_CLASSIFIER
)

_LOCAL_QUERY_FALLBACKS = tuple(
    query for query in _LOCAL_DELEGATED if query != "帮我把那个文件删掉"
)


@pytest.fixture(autouse=True)
def _restore_pending_clarify_state():
    old_pending = agent_server._PENDING_CLARIFY
    agent_server._PENDING_CLARIFY = None
    try:
        yield
    finally:
        agent_server._PENDING_CLARIFY = old_pending


@pytest.mark.parametrize("repeat", range(3))
@pytest.mark.parametrize("query", _LOCAL_DELEGATED)
def test_preclassify_local_consistently_blocks_local_state_changes(query, repeat):
    del repeat

    assert agent_server._preclassify_local(query) == "local_delegated"


@pytest.mark.parametrize("repeat", range(3))
@pytest.mark.parametrize("query", _DELIVERABLE_TASKS)
def test_preclassify_local_consistently_preserves_deliverable_tasks(query, repeat):
    del repeat

    assert agent_server._preclassify_local(query) is None


@pytest.mark.parametrize("query", _LOCAL_QUERY_FALLBACKS)
def test_ask_once_short_circuits_classifier_for_local_state_changes(query):
    with (
        patch.object(agent_server, "_classify_intent") as classify,
        patch.object(agent_server.EVENT_BUS, "emit_event"),
    ):
        result = agent_server.ask_once(query)

    assert result["intent"] == "query"
    assert result["content"] == "这个我做不到，这需要真的去执行，属于执行类任务。"
    classify.assert_not_called()


def test_ask_once_keeps_risk_gate_ahead_of_local_preclassification():
    with (
        patch.object(agent_server, "_classify_intent") as classify,
        patch.object(agent_server.EVENT_BUS, "emit_event"),
    ):
        result = agent_server.ask_once("帮我把那个文件删掉")

    assert result["intent"] == "refused"
    classify.assert_not_called()


@pytest.mark.parametrize("query", _DELIVERABLE_TASKS_PRECLASSIFIED)
def test_ask_once_preclassifies_deliverables_without_classifier(query):
    task_result = {
        "content": "正常派单",
        "reply_text": "正常派单",
        "intent": "task",
        "tool_results": [],
    }

    with (
        patch.object(agent_server, "_classify_intent", return_value="task") as classify,
        patch.object(agent_server, "_ask_task_branch", return_value=task_result) as branch,
        patch.object(agent_server.EVENT_BUS, "emit_event"),
    ):
        result = agent_server.ask_once(query)

    assert result == task_result
    classify.assert_not_called()
    branch.assert_called_once_with(query)


@pytest.mark.parametrize("query", _DELIVERABLE_TASKS_VIA_CLASSIFIER)
def test_ask_once_preserves_classifier_and_task_branch_for_deliverables(query):
    task_result = {
        "content": "正常派单",
        "reply_text": "正常派单",
        "intent": "task",
        "tool_results": [],
    }

    with (
        patch.object(agent_server, "_classify_intent", return_value="task") as classify,
        patch.object(agent_server, "_ask_task_branch", return_value=task_result) as branch,
        patch.object(agent_server.EVENT_BUS, "emit_event"),
    ):
        result = agent_server.ask_once(query)

    assert result == task_result
    classify.assert_called_once_with(query)
    branch.assert_called_once_with(query)


def test_crosstalk_s1_complete_new_request_discards_pending_clarification():
    task_result = {
        "content": "不应派单",
        "reply_text": "不应派单",
        "intent": "task",
        "tool_results": [],
    }

    with (
        patch.object(agent_server, "_classify_intent", return_value="task") as classify,
        patch.object(
            agent_server, "_ask_task_branch", return_value=task_result
        ) as branch,
        patch.object(agent_server.EVENT_BUS, "emit_event"),
    ):
        first = agent_server.ask_once("帮我把那个弄一下")
        second = agent_server.ask_once("帮我把桌面的日志整理一下")

    assert first["intent"] == "clarify"
    assert second["intent"] == "query"
    assert second["content"] == "这个我做不到，这需要真的去执行，属于执行类任务。"
    assert agent_server._PENDING_CLARIFY is None
    classify.assert_called_once_with("帮我把那个弄一下")
    branch.assert_not_called()


def test_crosstalk_s2_short_referent_still_fills_pending_clarification():
    task_result = {
        "content": "已进入正常任务分支",
        "reply_text": "已进入正常任务分支",
        "intent": "task",
        "tool_results": [],
    }

    with (
        patch.object(agent_server, "_classify_intent", return_value="task"),
        patch.object(
            agent_server, "_ask_task_branch", return_value=task_result
        ) as branch,
        patch.object(agent_server.EVENT_BUS, "emit_event"),
    ):
        first = agent_server.ask_once("帮我把那个弄一下")
        second = agent_server.ask_once("就是桌面那个日志文件")

    assert first["intent"] == "clarify"
    assert second["intent"] == "task"
    branch.assert_called_once_with("帮我把那个弄一下（补充：就是桌面那个日志文件）")


def test_crosstalk_s3_short_object_still_uses_phase2_fill_behavior():
    task_result = {
        "content": "已进入正常任务分支",
        "reply_text": "已进入正常任务分支",
        "intent": "task",
        "tool_results": [],
    }

    with (
        patch.object(agent_server, "_classify_intent", side_effect=("query", "task")),
        patch.object(
            agent_server, "_ask_task_branch", return_value=task_result
        ) as branch,
        patch.object(agent_server.EVENT_BUS, "emit_event"),
    ):
        first = agent_server.ask_once("打开")
        second = agent_server.ask_once("应用")

    assert first["intent"] == "clarify"
    assert second == task_result
    branch.assert_called_once_with("打开（补充：应用）")


@pytest.mark.parametrize(
    "promise",
    (
        "我马上安排。",
        "我将把这件事派给外脑。",
        "派给策划部。",
        "我们这边立刻跟进。",
    ),
)
def test_future_promise_sentences_are_removed_without_touching_other_text(promise):
    content = f"这是执行类任务。{promise}请先保留当前窗口。"

    assert agent_server._clean_content(content) == (
        "这是执行类任务。请先保留当前窗口。"
    )


def test_future_promise_open_browser_result_contains_no_dispatch_commitment():
    with (
        patch.object(agent_server, "_classify_intent") as classify,
        patch.object(agent_server.EVENT_BUS, "emit_event"),
    ):
        result = agent_server.ask_once("打开浏览器")

    assert result["intent"] == "query"
    assert "派给" not in result["content"]
    assert "我马上安排" not in result["content"]
    assert "派给外脑" not in result["content"]
    classify.assert_not_called()


def test_future_promise_filter_does_not_change_completed_claim_cleaning():
    assert agent_server._claim_clean("已经帮你整理好了。") == (
        "这个我做不到，需要真的去执行。"
    )
