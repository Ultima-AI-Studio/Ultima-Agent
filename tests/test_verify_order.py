"""Tests for the deterministic verifier.

These concentrate on the failure this step exists to catch: a receipt that was
green on a tree which is no longer the tree being tagged. That is the one failure
mode that looks fine from the outside, so it gets the most coverage.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-order.py"


def _load():
    spec = importlib.util.spec_from_file_location("verify_order", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _head() -> str:
    """Resolve git the same way the script does; a bare `git` is not always on PATH."""
    cli = _load()
    return subprocess.run([cli._git_exe(), "rev-parse", "HEAD"], cwd=str(ROOT),
                          capture_output=True, text=True).stdout.strip()


def _done(run_dir: Path, **fields) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {"exit_code": 0, "receipt_valid": True, "state": "audit"}
    payload.update(fields)
    path = run_dir / "done.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def test_missing_done_json_is_not_verified(tmp_path):
    cli = _load()
    payload = cli.verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert payload["blocking_failures"] == ["done_json_readable"]


def test_receipt_without_base_sha_is_not_trusted(tmp_path):
    """A green with unknown provenance cannot be invalidated, so it cannot be trusted."""

    _done(tmp_path)
    payload = _load().verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert "receipt_bound_to_a_commit" in payload["blocking_failures"]


def test_stale_receipt_is_caught(tmp_path):
    """base_sha no longer on HEAD means the receipt describes a different tree."""

    _done(tmp_path, base_sha="0" * 40)
    payload = _load().verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert "not_stale" in payload["blocking_failures"]


def test_current_head_is_not_stale(tmp_path):
    _done(tmp_path, base_sha=_head())
    payload = _load().verify("wo-x", tmp_path)
    assert payload["verified"] is True
    assert payload["blocking_failures"] == []


def test_nonzero_exit_code_blocks(tmp_path):
    _done(tmp_path, exit_code=1, base_sha=_head())
    payload = _load().verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert "exit_code_zero" in payload["blocking_failures"]


def test_invalid_receipt_blocks(tmp_path):
    _done(tmp_path, receipt_valid=False, base_sha=_head())
    payload = _load().verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert "receipt_valid" in payload["blocking_failures"]


def test_every_check_carries_its_evidence(tmp_path):
    """Someone who was not present must be able to re-derive each verdict."""

    _done(tmp_path, base_sha="0" * 40)
    payload = _load().verify("wo-x", tmp_path)
    for check in payload["checks"]:
        assert "check" in check and "passed" in check and "detail" in check
    stale = [c for c in payload["checks"] if c["check"] == "not_stale"][0]
    assert "merge-base" in stale["command"]


def test_undeclared_files_are_not_a_failure(tmp_path):
    """No declared file list means nothing to check; that is unknown, not a pass."""

    _done(tmp_path, base_sha=_head())
    payload = _load().verify("wo-ultimaagent-20991231-0000", tmp_path)
    undeclared = [c for c in payload["checks"] if c["check"] == "declared_files_landed"][0]
    assert undeclared["passed"] is None
    assert payload["verified"] is True
