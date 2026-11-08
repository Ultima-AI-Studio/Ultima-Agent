from __future__ import annotations

import importlib.util
import json
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest


ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "dispatch-work-order.py"


def _load_dispatch():
    spec = importlib.util.spec_from_file_location("dispatch_work_order_cli", SCRIPT)
    assert spec is not None and spec.loader is not None
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _row(order: str, reason: str = "", state: str = "audit") -> str:
    return f"| UltimaAgent | {order} | {state} | {reason} |"


def _registry(*rows: str, head: str = "| UltimaAgent | wo-self | audit | mine |") -> str:
    return "\n".join(
        ["<!-- queue-items:start -->", head, *rows, "<!-- queue-items:end -->"]
    )


def _write_run(runs: Path, order: str, finished_at: datetime) -> None:
    run = runs / f"{order}-20260101T000000000000Z"
    run.mkdir(parents=True, exist_ok=True)
    (run / "done.json").write_text(
        json.dumps({"exit_code": 0, "finished_at": finished_at.isoformat()}), encoding="utf-8"
    )


NOW = datetime(2026, 11, 9, 12, 0, tzinfo=timezone.utc)


def test_recent_audit_order_keeps_occupying(tmp_path):
    cli = _load_dispatch()
    _write_run(tmp_path, "wo-recent", NOW - timedelta(hours=3))
    blocking, disregarded = cli.audit_slot_holders(
        _registry(_row("wo-recent", "waiting")), "wo-self", now=NOW, runs_root=tmp_path
    )
    assert blocking == ["wo-recent"]
    assert disregarded == []


def test_stale_audit_order_stops_occupying(tmp_path):
    cli = _load_dispatch()
    _write_run(tmp_path, "wo-old", NOW - timedelta(days=9))
    blocking, disregarded = cli.audit_slot_holders(
        _registry(_row("wo-old", "waiting")), "wo-self", now=NOW, runs_root=tmp_path
    )
    assert blocking == []
    assert disregarded[0]["order"] == "wo-old"
    assert "exceeds" in disregarded[0]["why"]


def test_order_without_any_timestamp_is_still_an_occupant(tmp_path):
    """A missing timestamp is not proof of staleness; do not evict on it."""

    cli = _load_dispatch()
    blocking, disregarded = cli.audit_slot_holders(
        _registry(_row("wo-notime", "no dates anywhere")), "wo-self", now=NOW, runs_root=tmp_path
    )
    assert blocking == ["wo-notime"]
    assert disregarded == []


def test_frozen_reason_stops_occupying_regardless_of_age(tmp_path):
    cli = _load_dispatch()
    _write_run(tmp_path, "wo-frozen", NOW - timedelta(hours=2))
    blocking, disregarded = cli.audit_slot_holders(
        _registry(_row("wo-frozen", "范围外冻结 2026-11-08；阶段全部完成，待用户验收")),
        "wo-self", now=NOW, runs_root=tmp_path,
    )
    assert blocking == []
    assert disregarded[0]["why"].startswith("reason records it as frozen")


def test_registry_date_is_used_when_no_run_exists(tmp_path):
    """Hand-registered orders have no run dir; fall back to the dated reason."""

    cli = _load_dispatch()
    blocking, disregarded = cli.audit_slot_holders(
        _registry(_row("wo-handonly", "2026-10-31 回填：阶段报告 PASS 待 Owner 打冻结 tag")),
        "wo-self", now=NOW, runs_root=tmp_path,
    )
    assert blocking == []
    assert disregarded[0]["order"] == "wo-handonly"


def test_run_timestamp_wins_over_older_date_in_reason(tmp_path):
    """The newest evidence decides; an old date in prose must not evict a live order."""

    cli = _load_dispatch()
    _write_run(tmp_path, "wo-fresh", NOW - timedelta(hours=1))
    blocking, disregarded = cli.audit_slot_holders(
        _registry(_row("wo-fresh", "2026-10-01 旧记录；刚重新派发")),
        "wo-self", now=NOW, runs_root=tmp_path,
    )
    assert blocking == ["wo-fresh"]
    assert disregarded == []


def test_self_is_never_counted_against_itself(tmp_path):
    cli = _load_dispatch()
    blocking, disregarded = cli.audit_slot_holders(
        _registry(head=_row("wo-self", "waiting")), "wo-self", now=NOW, runs_root=tmp_path
    )
    assert blocking == []


def test_window_is_configurable_by_env(monkeypatch, tmp_path):
    cli = _load_dispatch()
    monkeypatch.setenv("ULTIMA_AUDIT_SLOT_MAX_AGE_DAYS", "1")
    cli = _load_dispatch()
    _write_run(tmp_path, "wo-two-days", NOW - timedelta(days=2))
    blocking, disregarded = cli.audit_slot_holders(
        _registry(_row("wo-two-days", "waiting")), "wo-self", now=NOW, runs_root=tmp_path
    )
    assert blocking == []
    assert disregarded and "exceeds 1" in disregarded[0]["why"]
