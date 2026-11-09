"""状态词适配层与 waiver 解析的契约用例。

两组被测对象：

* `scripts/gorch/status_map.py` —— 只做状态词归一，不是判定权威。
* `scripts/gorch_contract.py` 的 `gate_waivers` —— 豁免的读取口，畸形即整体拒绝。

这里只钉"读得对不对、拒不拒"。waiver 在冻结门上的效果（无门不许冻、豁免必须
被两轮判到、替代目标要真跑过）在 `test_freeze_binding.py` 里用真实仓库验证。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))
sys.path.insert(0, str(ROOT / "scripts" / "gorch"))

import gorch_contract as gc          # noqa: E402
import status_map as sm             # noqa: E402


def _manifest(**fields) -> str:
    return "<!-- gorch-manifest\n" + json.dumps(fields, ensure_ascii=False) + "\n-->\n"


# --- status_map ----------------------------------------------------------------


@pytest.mark.parametrize("raw,expected", [
    ("open", "open"),
    ("in-progress", "in-progress"),
    ("closed", "closed"),
    ("in_progress", "in-progress"),
    ("completed", "closed"),
    ("done", "closed"),
])
def test_every_status_word_the_tree_uses_normalizes(raw, expected):
    assert sm.normalize_status(raw) == expected


@pytest.mark.parametrize("raw", ["blocked", "failed", "", "  ", None, 0, "Open", "OPEN"])
def test_unknown_status_is_refused_rather_than_guessed(raw):
    """`blocked` belongs to `result`, not to `status`; case is not a licence."""
    assert sm.normalize_status(raw) is None


def test_status_words_covers_exactly_the_six_spellings():
    assert sm.STATUS_WORDS == {"open", "in-progress", "closed",
                               "in_progress", "completed", "done"}


def test_result_is_a_separate_domain_with_only_live_values():
    assert sm.normalize_result("done") == "done"
    assert sm.normalize_result("blocked") == "blocked"
    # No emitter produces `failed` yet; registering it would be an empty contract.
    assert sm.normalize_result("failed") is None
    assert sm.RESULT_CANON == ("done", "blocked")


def test_ccpm_parity_helpers_agree_with_the_original_shell_functions():
    assert sm.is_done_status("done") and sm.is_done_status("completed")
    assert not sm.is_done_status("open")
    assert sm.is_active_status("in_progress") and sm.is_active_status("in-progress")
    assert not sm.is_active_status("closed")


# --- gate_waivers --------------------------------------------------------------


@pytest.mark.parametrize("instead", [
    "tests",
    "tests/test_ok.py",
    "tests/gorch/test_api.py::test_x",
    "tests/gorch/test_api.py::TestK::test_x",
])
def test_an_acceptable_target_is_a_tests_path_or_an_exact_node(instead):
    text = _manifest(gate_waivers=[{"card": "orb-w1-init", "because": "no table",
                                    "instead": instead}])
    assert gc.gate_waivers(text)[0]["instead"] == instead


def test_an_order_without_a_manifest_or_without_waivers_declares_none():
    assert gc.gate_waivers("# plain order\n") == []
    assert gc.gate_waivers(_manifest(files=["a.txt"])) == []


@pytest.mark.parametrize("text,label", [
    (_manifest(gate_waivers=[{"card": "orb-w1-init", "because": "b",
                              "instead": "tests -k smoke"}]), "keyword_expression"),
    (_manifest(gate_waivers=[{"card": "orb-w1-init", "because": "b",
                              "instead": "-m pytest tests"}]), "bare_options"),
    (_manifest(gate_waivers=[{"card": "orb-w1-init", "because": "b",
                              "instead": "../tests/test_ok.py"}]), "path_escape"),
    (_manifest(gate_waivers=[{"card": "orb-w1-init", "because": "b",
                              "instead": "src/x.py"}]), "not_a_tests_target"),
    (_manifest(gate_waivers=[{"card": "orb-w1-init", "because": " ",
                              "instead": "tests/test_ok.py"}]), "empty_because"),
    (_manifest(gate_waivers=[{"card": "orb-w1-init", "because": "b",
                              "instead": ""}]), "empty_instead"),
    (_manifest(gate_waivers=[{"card": "nope", "because": "b",
                              "instead": "tests/test_ok.py"}]), "bad_card_id"),
    (_manifest(gate_waivers=[{"card": "orb-w1-init", "because": "b",
                              "instead": "tests/test_ok.py", "note": "x"}]), "extra_field"),
    (_manifest(gate_waivers="tests"), "not_a_list"),
    ("<!-- gorch-manifest\n{\n-->\n", "malformed_json"),
])
def test_a_malformed_waiver_is_refused_whole(text, label):
    """A bad waiver stops the document, it does not degrade to "no waiver"."""
    with pytest.raises(ValueError):
        gc.gate_waivers(text)
