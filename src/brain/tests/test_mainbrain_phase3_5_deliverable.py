"""主脑教学 Phase 3.5 产出物确定性判定测试。"""

import pytest

from src.brain import agent_server


_DELIVERABLE_TASK = (
    "帮我写一份周报",
    "帮我起草一份技术方案",
    "帮我翻译这段英文",
    "帮我总结一下今天的会议内容",
    "帮我输出一份测试计划",
    "帮我写一段产品介绍",
)

_NOT_TASK = (
    "怎么写周报",
    "什么是市盈率",
    "你会写代码吗",
    "帮我看看这份报告有什么问题",
    "帮我做个决定",
    "周报一般写什么",
)


@pytest.fixture(autouse=True)
def _restore_pending_clarify_state():
    old_pending = agent_server._PENDING_CLARIFY
    agent_server._PENDING_CLARIFY = None
    try:
        yield
    finally:
        agent_server._PENDING_CLARIFY = old_pending


@pytest.mark.parametrize("query", _DELIVERABLE_TASK)
def test_preclassify_deliverable_marks_creation_requests(query):
    assert agent_server._preclassify_deliverable(query) == "task"


@pytest.mark.parametrize("query", _NOT_TASK)
def test_preclassify_deliverable_ignores_method_questions(query):
    assert agent_server._preclassify_deliverable(query) is None


def test_preclassify_local_passes_engineering_objects():
    assert agent_server._preclassify_local("帮我修复这个接口的错误") is None


def test_preclassify_local_still_blocks_desktop_logs():
    assert (
        agent_server._preclassify_local("帮我把桌面的日志整理一下")
        == "local_delegated"
    )


def test_pending_short_command_starts_new_request():
    agent_server._pending_set("帮我把那个弄一下", "referent")

    assert agent_server._pending_fill("打开") is None
    assert agent_server._PENDING_CLARIFY is None


def test_pending_referent_answer_still_fills():
    agent_server._pending_set("帮我把那个弄一下", "referent")

    assert agent_server._pending_fill("应用") == "帮我把那个弄一下（补充：应用）"

