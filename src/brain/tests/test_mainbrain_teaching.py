"""主脑教学 Phase 1 四类病与反向判据的防回归测试。"""

from types import SimpleNamespace
from unittest.mock import patch

from src.brain import agent_server


class _TaskVerdictProvider:
    def chat(self, **_kwargs):
        return SimpleNamespace(content="动手")


class _CapturingDiagnoseProvider:
    def __init__(self, content="先重启电脑并记录蓝屏代码。"):
        self.system_prompt = ""
        self.content = content

    def chat(self, **kwargs):
        self.system_prompt = kwargs["system_prompt"]
        return SimpleNamespace(content=self.content, usage={})


class _CapturingQueryProvider:
    def __init__(self, content):
        self.system_prompt = ""
        self.content = content

    def chat(self, **kwargs):
        self.system_prompt = kwargs["system_prompt"]
        return SimpleNamespace(content=self.content, usage={})


def test_p1_claim_clean_rewrites_false_completion_claim():
    cleaned = agent_server._claim_clean("好的，先生，已按时间顺序整理桌面日志。")

    assert "已按时间顺序整理" not in cleaned
    assert "做不到" in cleaned or "执行类" in cleaned


def test_p2_diagnose_pattern_recognizes_blue_screen_request():
    assert agent_server._DIAGNOSE_PATTERNS.search("我电脑蓝屏了怎么办")


def test_diagnose_branch_contract_and_system_rules():
    # 用规则表未覆盖的故障词，确保这条走的是模型路径（蓝屏等常见故障走规则表直答）。
    provider = _CapturingDiagnoseProvider()

    with patch.object(agent_server, "provider_for", return_value=provider):
        result = agent_server._ask_diagnose_branch("数据库连接池怎么解决")

    assert "禁止" in provider.system_prompt or "不许" in provider.system_prompt
    assert {"content", "reply_text", "intent", "grounded"} <= result.keys()
    assert result["intent"] == "query"


def test_diagnose_branch_common_fault_answers_from_rule_table():
    # 常见故障必须走规则表：不调模型、0 秒直答、且给出可执行排查方向。
    provider = _CapturingDiagnoseProvider()

    with patch.object(agent_server, "provider_for", return_value=provider):
        result = agent_server._ask_diagnose_branch("我电脑蓝屏了怎么办")

    assert provider.system_prompt == ""
    assert {"content", "reply_text", "intent", "grounded"} <= result.keys()
    assert result["intent"] == "query"
    assert "先" in result["content"] or "检查" in result["content"]


def test_diagnose_branch_replaces_question_only_reply_with_direction():
    provider = _CapturingDiagnoseProvider("你再说一遍？蓝屏时有错误代码吗？")

    with patch.object(agent_server, "provider_for", return_value=provider):
        result = agent_server._ask_diagnose_branch("我电脑蓝屏了怎么办")

    assert "你再说一遍" not in result["content"]
    assert "？" not in result["content"]
    assert "先" in result["content"] or "检查" in result["content"]


def test_ask_once_routes_query_diagnosis_before_query_branch():
    expected = {
        "content": "诊断分支",
        "reply_text": "诊断分支",
        "intent": "query",
        "grounded": True,
    }

    with (
        patch.object(agent_server, "_classify_intent", return_value="query"),
        patch.object(agent_server, "_ask_diagnose_branch", return_value=expected) as branch,
        patch.object(agent_server, "_ask_query_branch") as query_branch,
    ):
        result = agent_server.ask_once("我电脑蓝屏了怎么办")

    assert result == expected
    branch.assert_called_once_with("我电脑蓝屏了怎么办", None)
    query_branch.assert_not_called()


def test_p3_method_ask_recognizes_how_to_fix_request():
    query = "这个接口报500错误怎么修"

    assert agent_server._METHOD_ASK.search(query)
    with patch.object(agent_server, "provider_for", return_value=_TaskVerdictProvider()):
        assert agent_server._classify_intent(query) == "query"


def test_p4_servile_tail_pattern_recognizes_service_question():
    assert agent_server._SERVILE_TAIL_PATTERN.search(
        "先生，1加1等于2。需要我帮您做其他事吗？"
    )


def test_clean_content_strips_three_servile_tail_variants():
    cases = (
        "先生，1加1等于2。需要我帮您做其他事吗？",
        "答案是2。要不要我继续解释吗？",
        "答案是2。还需要我补充么?",
    )

    for content in cases:
        cleaned = agent_server._clean_content(content)
        assert cleaned in {"先生，1加1等于2。", "答案是2。"}


def test_clean_content_strips_question_mark_servile_variants():
    """冒号后无「吗/么」、纯问号收尾的服务性变体也要剥掉。"""
    cases = {
        "您问的是贾维斯，Ultima Agent主脑。有什么可以帮您？": "您问的是贾维斯，Ultima Agent主脑。",
        "市盈率是股价除以每股收益。有什么需要我做的吗？": "市盈率是股价除以每股收益。",
        "1+1等于2。还需要什么帮助？": "1+1等于2。",
    }

    for content, expected in cases.items():
        assert agent_server._clean_content(content) == expected


def test_clean_content_keeps_non_servile_statements():
    """对照组：陈述句不得被服务性反问规则误伤。"""
    cases = (
        "这个需要我确认一下。",
        "删除文件前要先备份。",
        "先看服务端日志里那条完整堆栈。",
    )

    for content in cases:
        assert agent_server._clean_content(content) == content


def test_servile_strip_keeps_body_when_result_too_short():
    """退化生成「您有什么可以帮您？」时，强剥只剩「您」，必须保留原文。"""
    degenerate = "您有什么可以帮您？"
    first_sentence = "您问的是贾维斯，Ultima Agent主脑。有什么可以帮您？"

    # 只剩反问句的退化输出：不剥，避免产出单字残句
    assert agent_server._clean_content(degenerate) == degenerate
    # 正常带主体的：照常剥掉反问，保留主体
    assert agent_server._clean_content(first_sentence) == "您问的是贾维斯，Ultima Agent主脑。"


def test_is_too_short_guards_against_fragment_output():
    """实质字符不足 2 视为单字残句，交由分支出口走兜底话术。"""
    assert agent_server._is_too_short("您")
    assert not agent_server._is_too_short("ab")
    assert not agent_server._is_too_short("1+1等于2。")
    assert not agent_server._is_too_short("市盈率是股价除以每股收益。")


def test_clean_content_still_strips_grounded_marker():
    assert agent_server._clean_content("grounded:false   不确定。") == "不确定。"


def test_query_branch_appends_capability_and_claim_cleaning():
    provider = _CapturingQueryProvider("好的，已按时间顺序整理桌面日志。")

    with patch.object(agent_server, "provider_for", return_value=provider):
        result = agent_server._ask_query_branch("帮我把桌面的日志整理一下")

    assert "没有手" in provider.system_prompt or "不能打开" in provider.system_prompt
    assert "已按时间顺序整理" not in result["content"]


def test_query_branch_reports_boundary_for_delegated_file_action():
    provider = _CapturingQueryProvider("您是指哪个桌面的日志？")

    with patch.object(agent_server, "provider_for", return_value=provider):
        result = agent_server._ask_query_branch("帮我把桌面的日志整理一下")

    assert "做不到" in result["content"] or "执行类" in result["content"]
    assert "？" not in result["content"]


def test_claim_clean_keeps_plain_advice_unchanged():
    content = "删除文件前要先备份。"

    assert agent_server._claim_clean(content) == content


def test_claim_clean_keeps_completion_question_unchanged():
    content = "这个方案已经改好了吗"

    assert agent_server._claim_clean(content) == content


def test_delegate_hint_excludes_delegated_method_request():
    query = "帮我把这个怎么弄一下"

    assert agent_server._METHOD_ASK.search(query)
    assert agent_server._DELEGATE_HINT.search(query)
    with patch.object(agent_server, "provider_for", return_value=_TaskVerdictProvider()):
        assert agent_server._classify_intent(query) == "task"


def test_method_ask_accepts_pure_how_to_request():
    query = "如何备份数据库"

    assert agent_server._METHOD_ASK.search(query)
    assert not agent_server._DELEGATE_HINT.search(query)
    with patch.object(agent_server, "provider_for", return_value=_TaskVerdictProvider()):
        assert agent_server._classify_intent(query) == "query"
