"""Tests for the freeze gate's binding checks, against a disposable repository.

Review found the freeze step only read two booleans: it never checked that the
evidence described *this* work order, never noticed the receipt being swapped
after verification, and created the tag at whatever HEAD was at that instant
rather than at the verified commit. Each of those is a test below.
"""

from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
from pathlib import Path

import pytest

ROOT = Path(__file__).resolve().parents[1]
SCRIPT = ROOT / "scripts" / "freeze-work-order.py"


def _load():
    spec = importlib.util.spec_from_file_location("freeze_wo_t", SCRIPT)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.fixture
def cli(monkeypatch):
    module = _load()
    yield module


@pytest.fixture
def repo(tmp_path, monkeypatch, cli):
    root = tmp_path / "repo"
    root.mkdir()
    git = cli._git_exe()
    for argv in (["init", "-b", "main"], ["config", "user.name", "t"], ["config", "user.email", "t@t"]):
        subprocess.run([git, *argv], cwd=root, check=True, capture_output=True)
    (root / "a.txt").write_text("one\n", encoding="utf-8")
    subprocess.run([git, "add", "a.txt"], cwd=root, check=True, capture_output=True)
    subprocess.run([git, "commit", "-m", "init"], cwd=root, check=True, capture_output=True)
    monkeypatch.setattr(cli, "ROOT", root)
    return root


def _git(cli, *args: str, cwd=None) -> str:
    proc = subprocess.run([cli._git_exe(), *args], cwd=str(cwd or cli.ROOT),
                          capture_output=True, text=True)
    return (proc.stdout or "").strip()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_run(run_dir: Path, cli, work_order: str = "wo-t",
               card: Path | None = None, tamper: dict | None = None) -> None:
    run_dir.mkdir(parents=True, exist_ok=True)
    status_text = subprocess.run(
        [cli._git_exe(), "status", "--porcelain", "--untracked-files=no"],
        cwd=str(cli.ROOT), capture_output=True, text=True,
        encoding="utf-8", errors="replace").stdout
    entries = [{"code": l[:2], "path": l[3:].strip()}
               for l in status_text.splitlines() if l.strip()]
    done = {"exit_code": 0, "receipt_valid": True, "state": "audit",
            "audit_slot_busy": False, "parent_lost": False,
            "end_sha": _git(cli, "rev-parse", "HEAD"),
            "tree_oid": _git(cli, "rev-parse", "HEAD^{tree}"),
            "status_entries": entries, "changed_files": []}
    if tamper:
        done.update(tamper)
    (run_dir / "done.json").write_text(json.dumps(done), encoding="utf-8")

    verify = {"work_order": work_order, "verified": True, "blocking_failures": [],
              "head": _git(cli, "rev-parse", "HEAD"),
              "tree_oid": done["tree_oid"],
              "status_entries": done["status_entries"],
              "changed_files": done["changed_files"],
              "done_sha256": _sha(run_dir / "done.json")}
    (run_dir / "verify.json").write_text(json.dumps(verify), encoding="utf-8")

    audit = {"work_order": work_order, "audit_passed": True}
    if card is not None:
        audit["card"] = str(card)
        audit["card_meta"] = {"path": str(card), "sha256": _sha(card), "complete": True}
    (run_dir / "audit.json").write_text(json.dumps(audit), encoding="utf-8")


def test_a_clean_run_freezes_and_tags_the_verified_commit(tmp_path, repo, cli, monkeypatch):
    card = tmp_path / "card.md"
    card.write_text("| ACC-1 | x | y |\n", encoding="utf-8")
    run = tmp_path / "run"
    _write_run(run, cli, card=card)
    head = _git(cli, "rev-parse", "HEAD")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 0
    tags = _git(cli, "tag", "--list", "wo-t-freeze-*")
    assert tags
    assert _git(cli, "rev-parse", f"{tags}^{{}}") == head


def test_one_orders_verification_cannot_freeze_another(tmp_path, repo, cli):
    """A pass earned by wo-a must not authorise wo-b."""

    run = tmp_path / "run"
    _write_run(run, cli, work_order="wo-a")
    code = cli.main(["--work-order", "wo-b", "--run-dir", str(run)])
    assert code == 2
    assert not _git(cli, "tag", "--list", "wo-b-freeze-*")


def test_a_swapped_receipt_is_refused(tmp_path, repo, cli):
    """verify.json recorded a hash of done.json; a later edit breaks that."""

    run = tmp_path / "run"
    _write_run(run, cli)
    done = json.loads((run / "done.json").read_text(encoding="utf-8"))
    done["exit_code"] = 0
    done["state"] = "audit"
    done["note"] = "rewritten after verification"
    (run / "done.json").write_text(json.dumps(done), encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert not _git(cli, "tag", "--list", "wo-t-freeze-*")


def test_a_tree_edited_after_verification_is_refused(tmp_path, repo, cli):
    run = tmp_path / "run"
    _write_run(run, cli)
    verify = json.loads((run / "verify.json").read_text(encoding="utf-8"))

    (repo / "a.txt").write_text("changed\n", encoding="utf-8")
    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert not _git(cli, "tag", "--list", "wo-t-freeze-*")


def test_an_audit_for_another_order_is_refused(tmp_path, repo, cli):
    run = tmp_path / "run"
    _write_run(run, cli, work_order="wo-t")
    audit = json.loads((run / "audit.json").read_text(encoding="utf-8"))
    audit["work_order"] = "wo-other"
    (run / "audit.json").write_text(json.dumps(audit), encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2


def test_a_card_edited_after_the_audit_is_refused(tmp_path, repo, cli):
    card = tmp_path / "card.md"
    card.write_text("| ACC-1 | x | y |\n", encoding="utf-8")
    run = tmp_path / "run"
    _write_run(run, cli, card=card)
    card.write_text("| ACC-1 | relaxed criterion | y |\n", encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert not _git(cli, "tag", "--list", "wo-t-freeze-*")


def test_an_audit_on_truncated_material_is_refused(tmp_path, repo, cli):
    run = tmp_path / "run"
    _write_run(run, cli)
    audit = json.loads((run / "audit.json").read_text(encoding="utf-8"))
    audit["incomplete_inputs"] = ["big.log (huge)"]
    (run / "audit.json").write_text(json.dumps(audit), encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2


def test_head_moving_before_the_tag_is_refused(tmp_path, repo, cli):
    run = tmp_path / "run"
    _write_run(run, cli)
    (repo / "b.txt").write_text("new\n", encoding="utf-8")
    subprocess.run([cli._git_exe(), "add", "b.txt"], cwd=repo, check=True, capture_output=True)
    subprocess.run([cli._git_exe(), "commit", "-m", "move"], cwd=repo, check=True, capture_output=True)

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert not _git(cli, "tag", "--list", "wo-t-freeze-*")
