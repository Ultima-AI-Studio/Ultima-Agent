"""Tests for the deterministic verifier, against a real temporary repository.

The earlier version of this file ran assertions against the project's own working
tree and only exercised "receipt names a wrong SHA" and "receipt names the exact
current SHA". Both were true of the old implementation and neither touched the
attack the check was supposed to stop. Review named that gap, so every test here
builds a disposable git repo and asks the verifier the awkward questions: the file
was edited after the receipt, the run was blocked, the work order declared nothing.
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "verify-order.py"


def _load():
    spec = importlib.util.spec_from_file_location("verify_order_t", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cli(monkeypatch):
    module = _load()
    yield module


@pytest.fixture
def repo(tmp_path, monkeypatch, cli):
    """A tiny real repository, with the module's ROOT pointed at it."""
    root = tmp_path / "repo"
    root.mkdir()
    git = cli._git_exe()
    subprocess.run([git, "init", "-b", "main"], cwd=root, check=True, capture_output=True)
    subprocess.run([git, "config", "user.name", "t"], cwd=root, check=True, capture_output=True)
    subprocess.run([git, "config", "user.email", "t@t"], cwd=root, check=True, capture_output=True)
    (root / "a.txt").write_text("one\n", encoding="utf-8")
    subprocess.run([git, "add", "a.txt"], cwd=root, check=True, capture_output=True)
    subprocess.run([git, "commit", "-m", "init"], cwd=root, check=True, capture_output=True)
    monkeypatch.setattr(cli, "ROOT", root)
    return root


def _snapshot(cli) -> dict:
    """The event-time snapshot the dispatcher records after a worker finishes."""
    exe = cli._git_exe()

    def run(*args: str) -> str:
        return subprocess.run([exe, *args], cwd=str(cli.ROOT),
                              capture_output=True, text=True).stdout.strip()

    head = run("rev-parse", "HEAD")
    tree = run("rev-parse", "HEAD^{tree}")
    # Unstripped: porcelain's first column is a space for unstaged changes.
    status = subprocess.run([exe, "status", "--porcelain", "--untracked-files=no"],
                            cwd=str(cli.ROOT), capture_output=True, text=True,
                            encoding="utf-8", errors="replace").stdout
    import hashlib
    entries, manifest = [], []
    for line in [l for l in status.splitlines() if l.strip()]:
        code, name = line[:2], line[3:].strip()
        entries.append({"code": code, "path": name})
        path = Path(cli.ROOT) / name
        manifest.append({"path": name, "code": code,
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None})
    return {"end_sha": head, "tree_oid": tree, "status_entries": entries,
            "changed_files": manifest, "worktree_dirty": len(entries)}


def _done(run_dir: Path, **fields) -> Path:
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {"exit_code": 0, "receipt_valid": True, "state": "audit",
               "audit_slot_busy": False, "parent_lost": False}
    payload.update(fields)
    path = run_dir / "done.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _card(repo: Path, work_order: str, paths: list[str]) -> None:
    """A minimal card declaring the files this order touches."""
    card_dir = repo / "tasks" / "queue"
    card_dir.mkdir(parents=True, exist_ok=True)
    body = "# t\n\n## 2. 任务明细\n\n### T1 · x\n**文件**：" + "、".join(f"`{p}`" for p in paths) + "\n"
    (card_dir / f"{work_order}.md").write_text(body, encoding="utf-8")


def test_missing_done_json_is_not_verified(tmp_path, cli):
    payload = cli.verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert payload["blocking_failures"] == ["done_json_readable"]


def test_receipt_without_a_commit_is_not_trusted(tmp_path, repo, cli):
    _done(tmp_path)
    payload = cli.verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert "receipt_bound_to_a_commit" in payload["blocking_failures"]


def test_receipt_without_tree_identity_is_not_trusted(tmp_path, repo, cli):
    """The old version accepted a receipt that named only a commit."""
    snap = _snapshot(cli)
    _done(tmp_path, end_sha=snap["end_sha"], status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert "tree_identity_recorded" in payload["blocking_failures"]


def test_file_edited_after_the_receipt_is_caught(tmp_path, repo, cli):
    """The failure the check exists for: the tested tree is not the tagged tree."""

    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    snap = _snapshot(cli)
    _done(tmp_path, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    (repo / "a.txt").write_text("three\n", encoding="utf-8")   # edited after the run
    payload = cli.verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert "tree_unchanged" in payload["blocking_failures"]
    unchanged = [c for c in payload["checks"] if c["check"] == "tree_unchanged"][0]
    assert "a.txt" in unchanged["detail"]


def test_receipt_on_an_unedited_tree_passes(tmp_path, repo, cli):
    (repo / "a.txt").write_text("two\n", encoding="utf-8")
    snap = _snapshot(cli)
    _done(tmp_path, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "tree_unchanged" not in payload["blocking_failures"]


def test_blocked_run_may_not_be_frozen(tmp_path, repo, cli):
    """A run that lost its audit slot still carries exit_code 0 and a valid receipt."""

    snap = _snapshot(cli)
    _done(tmp_path, state="blocked", end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert "terminal_state_legal" in payload["blocking_failures"]


def test_slot_busy_run_may_not_be_frozen(tmp_path, repo, cli):
    snap = _snapshot(cli)
    _done(tmp_path, audit_slot_busy=True, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert "no_slot_block" in payload["blocking_failures"]


def test_nonzero_exit_code_blocks(tmp_path, repo, cli):
    snap = _snapshot(cli)
    _done(tmp_path, exit_code=1, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "exit_code_zero" in payload["blocking_failures"]


def test_invalid_receipt_blocks(tmp_path, repo, cli):
    snap = _snapshot(cli)
    _done(tmp_path, receipt_valid=False, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "receipt_valid" in payload["blocking_failures"]


def test_undeclared_files_are_a_failure(tmp_path, repo, cli):
    """Unknown is not verified: no file list means the output cannot be located."""

    snap = _snapshot(cli)
    _done(tmp_path, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-nocard-0000", tmp_path)
    landed = [c for c in payload["checks"] if c["check"] == "declared_files_landed"][0]
    assert landed["passed"] is False
    assert "declared_files_landed" in payload["blocking_failures"]


def test_declared_file_that_never_changed_is_caught(tmp_path, repo, cli):
    """Existence is not delivery: the declared file must differ from the base commit."""

    _card(repo, "wo-x", ["a.txt"])
    snap = _snapshot(cli)                      # a.txt untouched since the commit
    _done(tmp_path, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert payload["verified"] is False
    assert "declared_files_landed" in payload["blocking_failures"]


def test_every_check_carries_its_evidence(tmp_path, repo, cli):
    """Someone who was not present must be able to re-derive each verdict."""

    snap = _snapshot(cli)
    _done(tmp_path, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    for check in payload["checks"]:
        assert {"check", "passed", "detail", "command"} <= set(check)
    tree = [c for c in payload["checks"] if c["check"] == "tree_unchanged"][0]
    assert "sha256" in tree["command"] or "tree" in tree["command"]


def test_an_mechanical_gate_is_actually_checked(tmp_path, repo, cli):
    """'no more than 12 lines' was previously only the reviewer's assertion."""

    card_dir = repo / "tasks" / "queue"
    card_dir.mkdir(parents=True, exist_ok=True)
    (card_dir / "wo-x.md").write_text(
        "**文件**：`docs/report.md`\n\n**验收（Gate T1）**：\n"
        "- ACC-1 `docs/report.md` 文件存在且非空\n"
        "- ACC-2 内容不超过 12 行\n"
        "**禁止**：x\n", encoding="utf-8")
    (repo / "docs").mkdir(exist_ok=True)
    (repo / "docs" / "report.md").write_text("\n".join(f"line {i}" for i in range(20)), encoding="utf-8")

    snap = _snapshot(cli)
    _done(tmp_path, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "declared_checks_pass" in payload["blocking_failures"]


def test_a_declared_command_that_fails_blocks(tmp_path, repo, cli):
    card_dir = repo / "tasks" / "queue"
    card_dir.mkdir(parents=True, exist_ok=True)
    (card_dir / "wo-x.md").write_text("**机检**：pytest --definitely-not-a-flag\n", encoding="utf-8")

    snap = _snapshot(cli)
    _done(tmp_path, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert any("declared_command_pass" in b for b in payload["blocking_failures"])
