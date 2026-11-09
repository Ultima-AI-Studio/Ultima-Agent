"""Tests for the shared table parsers (``scripts/gorch_contract.py``).

Both tables used to be read four times — once in dispatch, once in freeze, once in
audit, once more in freeze for the gate set — and each copy skipped what it could
not parse. These tests hold the single parser to the rule that made the copies
unsafe: an unreadable row is a refusal, not a row that quietly disappears.
"""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "gorch_contract.py"


def _load():
    spec = importlib.util.spec_from_file_location("gorch_contract_t", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    sys.modules["gorch_contract"] = module
    spec.loader.exec_module(module)
    return module


def test_cards_are_collected_across_tables_and_counted_once_per_table():
    """`wo-s1-host-shell` lists each card in the task table and again in the write scopes.

    Two tables naming one card for two purposes is not two tasks competing for one
    artifact, so it is merged; the same card twice *inside* one table is refused.
    """

    contract = _load()
    text = (
        "| 任务 ID | 标题 | 验收门 |\n|---|---|---|\n"
        "| T1 s1-host-envcheck | 环境 | 门 |\n"
        "| T2 s1-host-winui3 | 初始化 | 门 |\n"
        "\n**写入域**\n\n"
        "| 任务 | 写入域 |\n|---|---|\n"
        "| T1 s1-host-envcheck | `logs/` |\n"
        "| T2 s1-host-winui3 | `src/` |\n"
    )
    assert contract.order_cards(text) == ["s1-host-envcheck", "s1-host-winui3"]


def test_a_repeated_card_inside_one_table_is_refused():
    contract = _load()
    text = "| 任务 | 文件 |\n|---|---|\n| T1 orb-w9-a | x |\n| T2 orb-w9-a | y |\n"
    try:
        contract.order_cards(text)
    except ValueError as exc:
        assert "more than once" in str(exc)
    else:
        raise AssertionError("a duplicate card inside one table was accepted")


def test_a_row_that_looks_like_a_card_reference_must_parse():
    """`s1-FOO` opens like a card id; dropping it would silently shrink the set."""

    contract = _load()
    text = "| 任务 | 文件 |\n|---|---|\n| T1 s1-FOO | x |\n"
    try:
        contract.order_cards(text)
    except ValueError as exc:
        assert "not one" in str(exc)
    else:
        raise AssertionError("a malformed card reference was skipped")


def test_a_task_row_without_a_card_reference_is_not_a_card():
    """Most orders have ordinary task tables; those rows name files, not cards."""

    contract = _load()
    text = ("| 任务 | 文件 | 验收门 |\n|---|---|---|\n"
            "| T0 | `src/x.py` | builds |\n"
            "| T1 | 实现网络模块 | 全绿 |\n")
    assert contract.order_cards(text) == []


def test_acceptance_rows_need_three_filled_cells():
    contract = _load()
    good = ("| 判据 | 合格判定 | 做法 |\n|---|---|---|\n"
            "| ACC-1 | 文件存在 | `test -f` |\n"
            "| ACC-2 | 模型复核通过 | 读回执 |\n")
    assert [row["id"] for row in contract.acc_rows(good)] == ["ACC-1", "ACC-2"]

    for bad, expected in (
        ("| ACC-1 | 只有两列 |\n", "fewer than three"),
        ("| ACC-1 |  | `x` |\n", "empty criterion"),
        ("| ACC-1 | 有 | `x` |\n| ACC-1 | 又 | `y` |\n", "reuses gate ids"),
    ):
        try:
            contract.acc_rows(bad)
        except ValueError as exc:
            assert expected in str(exc), (bad, str(exc))
        else:
            raise AssertionError(f"an unreadable acceptance row was accepted: {bad}")


def test_a_gate_mentioned_in_prose_is_not_a_gate():
    """`范围：不做 ACC-4` is prose; only a table cell opens a row."""

    contract = _load()
    text = ("范围：不做 ACC-4 的范围外检查。\n\n"
            "| 判据 | 合格判定 | 做法 |\n|---|---|---|\n| ACC-1 | 存在 | `x` |\n")
    assert [row["id"] for row in contract.acc_rows(text)] == ["ACC-1"]
