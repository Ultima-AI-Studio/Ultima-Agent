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
import shutil
import subprocess
import sys
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


@pytest.fixture(scope="session")
def venv_template(tmp_path_factory):
    """A real virtualenv to stand in for the registered interpreter.

    The gate pins every run to `tools/venv-openjarvis/Scripts`, so a fixture cannot
    fake a runner any more: it has to be one. `--system-site-packages` is what
    makes pytest importable here without installing anything.
    """
    base = tmp_path_factory.mktemp("venvtpl")
    subprocess.run([sys.executable, "-m", "venv", "--system-site-packages",
                    str(base / "v")], check=True, capture_output=True)
    return base / "v"


@pytest.fixture
def repo(tmp_path, monkeypatch, cli, venv_template):
    root = tmp_path / "repo"
    root.mkdir()
    git = cli._git_exe()
    for argv in (["init", "-b", "main"], ["config", "user.name", "t"], ["config", "user.email", "t@t"]):
        subprocess.run([git, *argv], cwd=root, check=True, capture_output=True)
    (root / "a.txt").write_text("one\n", encoding="utf-8")
    # The interpreter lives inside the repository but outside the commit, exactly as
    # it does in the real tree; ignoring it keeps the tree clean for the gate.
    (root / ".gitignore").write_text("tools/\n", encoding="utf-8")
    (root / "tests").mkdir()
    (root / "tests" / "test_ok.py").write_text("def test_ok():\n    assert True\n", encoding="utf-8")
    subprocess.run([git, "add", "a.txt", ".gitignore", "tests"], cwd=root, check=True, capture_output=True)
    subprocess.run([git, "commit", "-m", "init"], cwd=root, check=True, capture_output=True)
    (root / "tools").mkdir()
    shutil.copytree(venv_template, root / "tools" / "venv-openjarvis")
    # A delivery commit on top of the dispatch commit. The gate now requires the
    # delivered content to be committed, because a tag names a commit: freezing a
    # dirty tree certified a state the tag did not contain.
    (root / "a.txt").write_text("two\n", encoding="utf-8")
    subprocess.run([git, "commit", "-am", "deliver"], cwd=root, check=True, capture_output=True)
    monkeypatch.setattr(cli, "ROOT", root)
    return root


def _git(cli, *args: str, cwd=None) -> str:
    proc = subprocess.run([cli._git_exe(), *args], cwd=str(cwd or cli.ROOT),
                          capture_output=True, text=True)
    return (proc.stdout or "").strip()


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _write_run(run_dir: Path, cli, work_order: str = "wo-t",
               card: Path | None = None, tamper: dict | None = None,
               extra_cards: list[dict] | None = None,
               order_text: str | None = None) -> None:
    """Build a run the gate should accept, by running the checks for real.

    The earlier version hand-wrote ``verified: true``, which is exactly the forgery
    the gate now refuses: it re-runs the checks itself, so a hand-written verdict
    is caught rather than believed.
    ``card`` is the *content* of the card: the fixture always places it where the
    dispatcher would, because freeze recomputes that path from the order.
    """
    card_arg = card
    run_dir.mkdir(parents=True, exist_ok=True)

    # The order points at a card by table row, and the dispatcher resolves it under
    # tasks/cards. Freeze now recomputes that set from the order, so the fixture has
    # to build the real layout rather than a card somewhere convenient.
    card_id = "orb-w1-t"
    order_path = cli.ROOT / "tasks/queue" / f"{work_order}.md"
    card_dir = cli.ROOT / "tasks/cards" / card_id
    card_dir.mkdir(parents=True, exist_ok=True)
    card = card_dir / "task.md"
    card_text = "| ACC-1 | a.txt exists | ok |\n"
    if card_arg is not None:
        card_text = card_arg.read_text(encoding="utf-8-sig")
    card.write_text(card_text, encoding="utf-8")

    if order_text is not None:
        order_path.parent.mkdir(parents=True, exist_ok=True)
        order_path.write_text(order_text, encoding="utf-8")
    elif not order_path.is_file():
        order_path.parent.mkdir(parents=True, exist_ok=True)
        # An order with no mechanical check proves nothing and cannot freeze any more,
        # so the fixture declares the one command the gate accepts: the registered
        # interpreter against a committed test target.
        run_cmd = f"{cli.ROOT / 'tools/venv-openjarvis/Scripts/python.exe'} -m pytest tests"
        manifest = {"files": ["a.txt"],
                    "acc": [{"id": "ACC-1", "check": "exists_nonempty", "path": "a.txt"}],
                    "commands": [run_cmd]}
        order_path.write_text(
            "# t\n\n<!-- gorch-manifest\n" + json.dumps(manifest) + "\n-->\n\n"
            f"| T1 {card_id} | a.txt | ACC-1 |\n\n"
            f"**机检**：{run_cmd}\n\n"
            "**文件**：`a.txt`\n\n**验收（Gate T1）**\n- ACC-1 `a.txt` 存在且非空\n",
            encoding="utf-8")
    elif f"| T1 {card_id} |" not in order_path.read_text(encoding="utf-8-sig"):
        order_path.write_text(
            order_path.read_text(encoding="utf-8-sig").replace(
                "**文件**：", f"| T1 {card_id} | a.txt | ACC-1 |\n\n**文件**："),
            encoding="utf-8")

    done = {"work_order": work_order, "run_id": run_dir.name,
            # The card is fixed at dispatch, and freeze compares the audited card
            # against this hash rather than against whatever it is handed.
            "card": str(card), "card_sha256": _sha(card),
            # Every card the order names is fixed at dispatch, not only the audited one.
            "cards": ([{"path": str(card), "sha256": _sha(card)}] + (extra_cards or [])),
            "exit_code": 0, "receipt_valid": True, "state": "audit",
            "audit_slot_busy": False, "parent_lost": False,
            "base_sha": _git(cli, "rev-parse", "HEAD~1"),
            "end_sha": _git(cli, "rev-parse", "HEAD"),
            "tree_oid": _git(cli, "rev-parse", "HEAD^{tree}"),
            "status_entries": [], "changed_files": []}
    if tamper:
        done.update(tamper)
    (run_dir / "done.json").write_text(json.dumps(done), encoding="utf-8")

    verifier = cli._load_verifier()
    result = verifier.verify(work_order, run_dir)
    (run_dir / "verify.json").write_text(json.dumps(result), encoding="utf-8")

    evidence = run_dir / "evidence.txt"
    evidence.write_text("ACC-1: PASS - a.txt exists and is not empty\n", encoding="utf-8")

    audit = {"work_order": work_order, "audit_passed": True, "incomplete_inputs": [],
             # Bound to this run and these artifacts, which is what freeze checks.
             # The two-round bodies are stubs here: this file tests the freeze gate,
             # not the model review, and calling DeepSeek from a unit test is not
             # something a test may do.
             "run_id": run_dir.name,
             "verify_sha256": _sha(run_dir / "verify.json"),
             "done_sha256": _sha(run_dir / "done.json"),
             "round1": {"passed": True, "per_gate": {"ACC-1": "PASS"},
                        "overall": "PASS", "model": "stub", "tokens": 0, "response": "AUDIT: PASS"},
             "round2": {"passed": True, "per_gate": {"ACC-1": "PASS"},
                        "overall": "PASS", "model": "stub", "tokens": 0, "response": "AUDIT: PASS"},
             "gates": {"ACC-1": "PASS"},
             "card": str(card),
             "card_meta": {"path": str(card), "sha256": _sha(card),
                           "bytes": Path(card).stat().st_size, "complete": True},
             "evidence": [str(evidence)],
             "evidence_meta": [{"path": str(evidence), "sha256": _sha(evidence),
                                "bytes": evidence.stat().st_size, "shown_chars": 64,
                                "complete": True}]}
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
    # The card the order points at, i.e. the one the audit actually read.
    (cli.ROOT / "tasks/cards/orb-w1-t/task.md").write_text(
        "| ACC-1 | relaxed criterion | y |\n", encoding="utf-8")

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


def test_a_handwritten_verify_json_cannot_freeze(tmp_path, repo, cli):
    """A JSON file saying `verified: true` is a claim, not evidence.

    Review reproduced exactly this: write two JSON files by hand, run freeze, get
    exit 0 and a tag. The gate now re-runs the checks itself.
    """

    run = tmp_path / "run"
    _write_run(run, cli)
    live = json.loads((run / "verify.json").read_text(encoding="utf-8"))
    forged = dict(live, verified=True, blocking_failures=[])
    # The stored verdict is consistent with itself, but the checks disagree: the
    # receipt no longer exists after it was written, so a fresh run fails.
    (run / "done.json").write_text("{}\n", encoding="utf-8")
    (run / "verify.json").write_text(json.dumps(forged), encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert not _git(cli, "tag", "--list", "wo-t-freeze-*")


def test_an_audit_from_another_run_cannot_freeze(tmp_path, repo, cli):
    """A pass earned in run A must not be replayed into run B."""

    run = tmp_path / "run"
    _write_run(run, cli)
    audit = json.loads((run / "audit.json").read_text(encoding="utf-8"))
    audit["run_id"] = "run-earlier"
    (run / "audit.json").write_text(json.dumps(audit), encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert not _git(cli, "tag", "--list", "wo-t-freeze-*")


def test_an_audit_without_bindings_cannot_freeze(tmp_path, repo, cli):
    """A bare `audit_passed: true` is a flag, not a review of these artifacts."""

    run = tmp_path / "run"
    _write_run(run, cli)
    audit = json.loads((run / "audit.json").read_text(encoding="utf-8"))
    for key in ("verify_sha256", "done_sha256", "round1", "round2"):
        audit.pop(key, None)
    (run / "audit.json").write_text(json.dumps(audit), encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert not _git(cli, "tag", "--list", "wo-t-freeze-*")


def test_the_tag_carries_the_receipt_it_was_frozen_on(tmp_path, repo, cli):
    """The tag must be readable without the run directory that produced it."""

    card = tmp_path / "card.md"
    card.write_text("| ACC-1 | x | y |\n", encoding="utf-8")
    run = tmp_path / "run"
    _write_run(run, cli, card=card)

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 0
    tags = _git(cli, "tag", "--list", "wo-t-freeze-*")
    body = _git(cli, "tag", "-l", "--format=%(contents)", tags)
    assert "── freeze receipt ──" in body
    assert "head: " in body
    assert "card as reviewed" in body
    assert "| ACC-1 | x | y |" in body


def test_rounds_that_failed_cannot_be_frozen_by_the_top_level_flag(tmp_path, repo, cli):
    """Both rounds say FAIL; only the boolean says true. The boolean must lose."""

    card = tmp_path / "card.md"
    card.write_text("| ACC-1 | x | y |\n", encoding="utf-8")
    run = tmp_path / "run"
    _write_run(run, cli, card=card)

    audit_path = run / "audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
    for key in ("round1", "round2"):
        audit[key] = {"passed": False, "per_gate": {"ACC-1": "FAIL"},
                      "overall": "FAIL", "model": "stub", "tokens": 0,
                      "response": "ACC-1: FAIL - broken\nAUDIT: FAIL"}
    audit["audit_passed"] = True
    audit_path.write_text(json.dumps(audit), encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") == ""


def test_a_gate_the_audit_never_judged_blocks_the_freeze(tmp_path, repo, cli):
    """The card declares two gates; both audit rounds report one. The missing gate
    must stop the freeze even though every recorded value says PASS."""

    card = tmp_path / "card.md"
    card.write_text("| ACC-1 | a.txt exists | ok |\n| ACC-2 | a.txt is stable | ok |\n",
                    encoding="utf-8")
    run = tmp_path / "run"
    _write_run(run, cli, card=card)

    audit_path = run / "audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8-sig"))
    assert audit["round1"]["per_gate"] == {"ACC-1": "PASS"}

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") == ""


def test_a_secondary_card_changed_after_dispatch_blocks_the_freeze(tmp_path, repo, cli):
    """An order may name several cards. Only the audited one is compared by content;
    every other one is fixed by its dispatch hash."""

    # Second card, in the layout the dispatcher uses, referenced by the order.
    other_id = "orb-w2-x"
    other = cli.ROOT / "tasks/cards" / other_id / "task.md"
    other.parent.mkdir(parents=True, exist_ok=True)
    other.write_text("| ACC-9 | unrelated | ok |\n", encoding="utf-8")
    dispatched = _sha(other)

    card = tmp_path / "card.md"
    card.write_text("| ACC-1 | a.txt exists | ok |\n", encoding="utf-8")
    run = tmp_path / "run"
    _write_run(run, cli, card=card,
               extra_cards=[{"path": str(other), "sha256": dispatched}])

    # The order named it, then the card changed under the same path.
    order = cli.ROOT / "tasks/queue" / "wo-t.md"
    order.write_text(order.read_text(encoding="utf-8-sig").replace(
        "| T1 orb-w1-t | a.txt | ACC-1 |",
        f"| T1 orb-w1-t | a.txt | ACC-1 |\n| T2 {other_id} | a.txt | ACC-9 |"),
        encoding="utf-8")
    other.write_text("| ACC-9 | swapped after dispatch | ok |\n", encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") == ""


def test_a_receipt_that_names_none_of_the_orders_cards_blocks_the_freeze(tmp_path, repo, cli):
    """An old receipt carries no ``cards`` at all. The loop used to skip it entirely."""

    card = tmp_path / "card.md"
    card.write_text("| ACC-1 | a.txt exists | ok |\n", encoding="utf-8")
    run = tmp_path / "run"
    _write_run(run, cli, card=card, tamper={"cards": []})

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") == ""


def test_a_dirty_tree_cannot_be_frozen(tmp_path, repo, cli):
    """The tag names a commit, so uncommitted work is not in the frozen content."""

    run = tmp_path / "run"
    _write_run(run, cli)
    (repo / "a.txt").write_text("three\n", encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert not _git(cli, "tag", "--list", "wo-t-freeze-*")


def test_an_order_with_no_mechanical_check_verifies_nothing(tmp_path, repo, cli):
    """Zero commands used to satisfy every loop and verify green. It proves nothing."""

    order = ("# t\n\n<!-- gorch-manifest\n"
             + json.dumps({"files": ["a.txt"], "commands": [],
                           "acc": [{"id": "ACC-1", "check": "exists_nonempty", "path": "a.txt"}]})
             + "\n-->\n\n| T1 orb-w1-t | a.txt | ACC-1 |\n\n**文件**：`a.txt`\n")
    run = tmp_path / "run"
    _write_run(run, cli, order_text=order)

    payload = json.loads((run / "verify.json").read_text(encoding="utf-8"))
    assert payload["verified"] is False
    assert "declared_command_plan" in payload["blocking_failures"]

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") == ""


def test_a_card_outside_tasks_cards_is_refused(tmp_path, repo, cli):
    """A receipt can name any path; only tasks/cards/<id>/task.md is the card."""

    order = ("# t\n\n| T1 orb-w1-t | a.txt | ACC-1 |\n\n**文件**：`a.txt`\n")
    stray = tmp_path / "elsewhere" / "task.md"
    stray.parent.mkdir()
    stray.write_text("| ACC-1 | a.txt exists | ok |\n", encoding="utf-8")
    run = tmp_path / "run"
    _write_run(run, cli, order_text=order,
               tamper={"cards": [{"path": str(stray), "sha256": _sha(stray)}],
                       "card": str(stray), "card_sha256": _sha(stray)})

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") == ""


def test_a_card_at_a_non_canonical_name_is_refused(tmp_path, repo, cli):
    """A directory called <id> is not the card; the file has to be task.md."""

    order = ("# t\n\n| T1 orb-w1-t | a.txt | ACC-1 |\n\n**文件**：`a.txt`\n")
    card_dir = repo / "tasks" / "cards" / "orb-w1-t"
    card_dir.mkdir(parents=True)
    lookalike = card_dir / "notes.md"
    lookalike.write_text("| ACC-1 | a.txt exists | ok |\n", encoding="utf-8")
    run = tmp_path / "run"
    _write_run(run, cli, order_text=order,
               tamper={"cards": [{"path": str(lookalike), "sha256": _sha(lookalike)}],
                       "card": str(lookalike), "card_sha256": _sha(lookalike)})

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") == ""


def test_a_receipt_naming_only_some_cards_is_refused(tmp_path, repo, cli):
    """The order names two cards; a receipt that drops one was never complete."""

    order = ("# t\n\n| T1 orb-w1-t | a.txt | ACC-1 |\n"
             "| T2 orb-w1-u | a.txt | ACC-1 |\n\n**文件**：`a.txt`\n")
    for name in ("orb-w1-t", "orb-w1-u"):
        (repo / "tasks" / "cards" / name).mkdir(parents=True, exist_ok=True)
        (repo / "tasks" / "cards" / name / "task.md").write_text(
            "| ACC-1 | a.txt exists | ok |\n", encoding="utf-8")
    run = tmp_path / "run"
    _write_run(run, cli, order_text=order)

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") == ""


# -------------------------------------------------------------------------------
# 空 ACC 门表：冻结门这一环原来不设防
#
# `freeze-work-order.py` 以前写的是 `if gate_ids and (declared != gate_ids or ...)`，
# 于是一张没有 ACC 表的卡根本不进集合比较：三处都写 PASS 也没有任何东西被比较。
# 上游审计会先挡住空表，但那条挡板要靠"走正常审计链"才生效——旧回执或手工回执
# 能绕过去。下面三条钉住新的判据：无门就只认 waiver，而 waiver 必须被两轮审计
# 判过、并且它的替代目标在 verifier 回执里真的跑过。
# -------------------------------------------------------------------------------


def _gate_free_card(tmp_path: Path) -> Path:
    """A card that states a criterion but declares no `ACC-<n>` row at all."""
    card = tmp_path / "card.md"
    card.write_text("| T1 | a.txt | 分层结构符合方案 §4.1 |\n", encoding="utf-8")
    return card


def _waiver_order(cli, card_id: str = "orb-w1-t") -> tuple[str, str]:
    """An order that waives the card's gates with a target the verifier really runs."""
    run_cmd = f"{cli.ROOT / 'tools/venv-openjarvis/Scripts/python.exe'} -m pytest tests"
    manifest = {
        "files": ["a.txt"],
        "acc": [{"id": "ACC-1", "check": "exists_nonempty", "path": "a.txt"}],
        "commands": [run_cmd],
        "gate_waivers": [{
            "card": card_id,
            "because": "the card states a criterion but has no ACC table to enumerate it",
            "instead": "tests",
        }],
    }
    order = ("# t\n\n<!-- gorch-manifest\n" + json.dumps(manifest, ensure_ascii=False)
             + "\n-->\n\n"
             f"| T1 {card_id} | a.txt | ACC-1 |\n\n"
             f"**机检**：{run_cmd}\n\n**文件**：`a.txt`\n")
    return order, f"WAIVER:{card_id}"


def test_a_gate_free_card_cannot_freeze_on_three_forged_passes(tmp_path, repo, cli):
    """No gate, no waiver: three PASS claims must not buy a tag.

    The audit is forged the way the old hole allowed — `audit_passed: true`, the
    top-level gate map, and both rounds all say PASS — but the card declares no
    gate, so there is no verdict that any of those PASS lines could belong to.
    """

    run = tmp_path / "run"
    _write_run(run, cli, card=_gate_free_card(tmp_path))

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") == ""


def test_a_waiver_is_not_enough_when_the_audit_judged_another_key(tmp_path, repo, cli):
    """The waiver is the only auditable key; two ACC PASS lines do not replace it."""

    order, _ = _waiver_order(cli)
    run = tmp_path / "run"
    _write_run(run, cli, card=_gate_free_card(tmp_path), order_text=order)

    # `_write_run` records an ACC-1 audit. Freeze has to refuse it: with no ACC
    # table the only key that could be judged is WAIVER:<card>.
    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 2
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") == ""


def test_a_waiver_judged_by_both_rounds_freezes(tmp_path, repo, cli):
    """A declared waiver, judged in both rounds, with a run behind it, does freeze."""

    order, key = _waiver_order(cli)
    run = tmp_path / "run"
    _write_run(run, cli, card=_gate_free_card(tmp_path), order_text=order)

    audit_path = run / "audit.json"
    audit = json.loads(audit_path.read_text(encoding="utf-8"))
    audit["gates"] = {key: "PASS"}
    audit["round1"]["per_gate"] = {key: "PASS"}
    audit["round2"]["per_gate"] = {key: "PASS"}
    audit_path.write_text(json.dumps(audit, ensure_ascii=False), encoding="utf-8")

    code = cli.main(["--work-order", "wo-t", "--run-dir", str(run)])
    assert code == 0
    assert _git(cli, "tag", "--list", "wo-t-freeze-*") != ""
