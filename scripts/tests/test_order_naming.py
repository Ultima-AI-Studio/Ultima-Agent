from __future__ import annotations

import importlib
from pathlib import Path
import re

import pytest


def _naming():
    try:
        return importlib.import_module("scripts.order_naming")
    except ModuleNotFoundError as exc:
        if exc.name == "scripts.order_naming":
            assert False, "scripts.order_naming is missing"
        raise


def test_authority_exports_a_compiled_pattern():
    naming = _naming()
    assert isinstance(naming.ORDER_ID_PATTERN, re.Pattern)


@pytest.mark.parametrize(
    "order",
    [
        "wo-orb-w1",
        "wo-s1-host-shell",
        "wo-agent-audit-s1",
        "wo-s7-memory-temperature",
        "wo-ultimaagent-20261108-0030",
    ],
)
def test_representative_stock_order_ids_are_valid(order):
    naming = _naming()
    assert naming.is_valid_order(order) is True


@pytest.mark.parametrize(
    "order",
    [
        "wo-",
        "",
        "WO-S1-X",
        "wo_s1_x",
        "wo s1 x",
        "wo-s1-",
        "wo s1",
        "wo- ",
        "wo--s1",
    ],
)
def test_malformed_order_ids_are_rejected(order):
    naming = _naming()
    assert naming.is_valid_order(order) is False


def test_every_checked_in_queue_card_has_a_valid_order_id():
    naming = _naming()
    queue_dir = Path(__file__).resolve().parents[2] / "tasks" / "queue"
    cards = sorted(queue_dir.glob("wo-*.md"))

    assert cards
    assert [
        path.name
        for path in cards
        if not naming.is_valid_order(path.stem.split("--", 1)[0])
    ] == []


def test_resolve_card_path_supports_exact_filename(tmp_path):
    naming = _naming()
    card = tmp_path / "wo-s1-host-shell.md"
    card.write_text("direct", encoding="utf-8")

    assert naming.resolve_card_path("wo-s1-host-shell", tmp_path) == card


def test_resolve_card_path_supports_slugged_filename(tmp_path):
    naming = _naming()
    card = tmp_path / "wo-ultimaagent-20261108-0030--m4-orchestration-ledger.md"
    card.write_text("slugged", encoding="utf-8")

    assert naming.resolve_card_path("wo-ultimaagent-20261108-0030", tmp_path) == card


def test_resolve_card_path_reports_zero_matches(tmp_path):
    naming = _naming()
    with pytest.raises(ValueError) as caught:
        naming.resolve_card_path("wo-s1-missing", tmp_path)

    assert "实际命中 0 张" in str(caught.value)
    assert "[]" in str(caught.value)


def test_resolve_card_path_reports_every_ambiguous_match(tmp_path):
    naming = _naming()
    direct = tmp_path / "wo-s1-host-shell.md"
    slugged = tmp_path / "wo-s1-host-shell--desktop.md"
    direct.write_text("direct", encoding="utf-8")
    slugged.write_text("slugged", encoding="utf-8")

    with pytest.raises(ValueError) as caught:
        naming.resolve_card_path("wo-s1-host-shell", tmp_path)

    message = str(caught.value)
    assert "实际命中 2 张" in message
    assert direct.name in message
    assert slugged.name in message


def test_resolve_card_path_does_not_claim_a_neighboring_order(tmp_path):
    naming = _naming()
    (tmp_path / "wo-orb-w8-prompt.md").write_text("other order", encoding="utf-8")

    with pytest.raises(ValueError, match="实际命中 0 张"):
        naming.resolve_card_path("wo-orb-w8", tmp_path)


def test_resolve_card_path_requires_exact_filename_case(tmp_path):
    naming = _naming()
    (tmp_path / "WO-S1-HOST-SHELL.md").write_text("mixed case", encoding="utf-8")

    with pytest.raises(ValueError, match="实际命中 0 张"):
        naming.resolve_card_path("wo-s1-host-shell", tmp_path)


def test_resolve_card_path_rejects_invalid_id_before_lookup(tmp_path):
    naming = _naming()
    with pytest.raises(ValueError, match="工单号不符合命名契约"):
        naming.resolve_card_path("wo-s1-", tmp_path)
