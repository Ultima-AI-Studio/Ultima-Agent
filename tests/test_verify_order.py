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
import sys
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
    # The dispatcher reads `--porcelain=v1 -z`; the fixture must produce the same
    # shape or it cannot catch anything the real snapshot would record.
    status = subprocess.run([exe, "status", "--porcelain=v1", "-z", "--untracked-files=no"],
                            cwd=str(cli.ROOT), capture_output=True, text=True,
                            encoding="utf-8", errors="replace").stdout
    import hashlib
    entries, manifest = [], []
    entries = cli._parse_status_z(status)
    for entry in entries:
        path = Path(cli.ROOT) / entry["path"]
        manifest.append({"path": entry["path"], "code": entry["code"],
                         "orig": entry.get("orig"),
                         "sha256": hashlib.sha256(path.read_bytes()).hexdigest() if path.is_file() else None})
    return {"end_sha": head, "tree_oid": tree, "status_entries": entries,
            "changed_files": manifest, "worktree_dirty": len(entries)}


def _done(run_dir: Path, work_order: str = "wo-x", **fields) -> Path:
    """A receipt. It names its own order and run: the gate refuses one that does
    not, because otherwise a receipt from order A reads as valid under order B."""
    run_dir.mkdir(parents=True, exist_ok=True)
    payload = {"work_order": work_order, "run_id": run_dir.name,
               "exit_code": 0, "receipt_valid": True, "state": "audit",
               "audit_slot_busy": False, "parent_lost": False}
    payload.update(fields)
    path = run_dir / "done.json"
    path.write_text(json.dumps(payload), encoding="utf-8")
    return path


def _card(repo: Path, work_order: str, paths: list[str]) -> None:
    """A minimal card: prose section plus the manifest the gate now requires.

    The prose is kept because a real order still reads like an order; the manifest
    is what verify actually trusts.
    """
    card_dir = repo / "tasks" / "queue"
    card_dir.mkdir(parents=True, exist_ok=True)
    manifest = {"files": paths,
                "acc": [{"id": f"ACC-{i + 1}", "check": "exists_nonempty", "path": p}
                        for i, p in enumerate(paths)],
                "commands": []}
    body = ("# t\n\n<!-- gorch-manifest\n"
            + json.dumps(manifest, ensure_ascii=False)
            + "\n-->\n\n## 2. 任务明细\n\n### T1 · x\n**文件**："
            + "、".join(f"`{p}`" for p in paths) + "\n")
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
    _done(tmp_path, base_sha=snap["end_sha"], end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
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
    # The runner now has to be the registered interpreter, so the command names it
    # explicitly rather than relying on whatever `pytest` PATH happens to resolve to.
    python = cli.ROOT / "tools" / "venv-openjarvis" / "Scripts" / "python.exe"
    python.parent.mkdir(parents=True, exist_ok=True)
    python.write_text("", encoding="utf-8")
    real_python = Path(sys.executable)
    python.write_bytes(real_python.read_bytes())
    card_dir = repo / "tasks" / "queue"
    card_dir.mkdir(parents=True, exist_ok=True)
    (card_dir / "wo-x.md").write_text(
        f"**机检**：{python} -m pytest tests\n", encoding="utf-8")

    snap = _snapshot(cli)
    _done(tmp_path, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert any("declared_command_pass" in b for b in payload["blocking_failures"])


def test_a_receipt_that_does_not_name_its_own_order_is_refused(tmp_path, repo, cli):
    """Order A's receipt must not read as valid under order B.

    The only thing naming the order used to be the argument the caller passed,
    so a receipt copied out of another run directory satisfied every check.
    """

    _card(repo, "wo-b", ["a.txt"])
    snap = _snapshot(cli)
    _done(tmp_path, work_order="wo-a", base_sha=snap["end_sha"], end_sha=snap["end_sha"],
          tree_oid=snap["tree_oid"], status_entries=snap["status_entries"],
          changed_files=snap["changed_files"])
    payload = cli.verify("wo-b", tmp_path)
    assert payload["verified"] is False
    assert "receipt_names_itself" in payload["blocking_failures"]


def test_a_receipt_without_a_run_id_is_refused(tmp_path, repo, cli):
    """Without a run id the receipt cannot be tied to the run directory it sits in."""

    _card(repo, "wo-x", ["a.txt"])
    snap = _snapshot(cli)
    _done(tmp_path, base_sha=snap["end_sha"], end_sha=snap["end_sha"],
          tree_oid=snap["tree_oid"], status_entries=snap["status_entries"],
          changed_files=snap["changed_files"], run_id=None)
    payload = cli.verify("wo-x", tmp_path)
    assert "receipt_names_itself" in payload["blocking_failures"]


def test_a_renamed_file_keeps_both_paths(cli):
    """Root-level state entries parse from -z, where a rename carries two paths.

    Line-based parsing mangled `R  old -> new` into a single bogus path, which let
    the new side be edited after verification while the recorded entry stayed the
    same.
    """

    raw = "R  new.txt\x00old.txt\x00 M kept.txt\x00"
    entries = cli._parse_status_z(raw)
    assert entries == [{"code": "R ", "path": "new.txt", "orig": "old.txt"},
                       {"code": " M", "path": "kept.txt"}]


def _order(repo: Path, body: str) -> None:
    path = repo / "tasks" / "queue" / "wo-x.md"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(body, encoding="utf-8")


def test_a_python_c_payload_is_not_a_test_run(tmp_path, repo, cli):
    """`python -c "..." -m pytest` is an inline script that happens to mention pytest."""

    import sys
    _order(repo, f"**机检**：{sys.executable} -c \"print(1)\" -m pytest\n")
    snap = _snapshot(cli)
    _done(tmp_path, base_sha=snap["end_sha"], end_sha=snap["end_sha"],
          tree_oid=snap["tree_oid"], status_entries=snap["status_entries"],
          changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "declared_command_plan" in payload["blocking_failures"]


def test_a_machine_check_line_that_cannot_be_parsed_fails(tmp_path, repo, cli):
    """Silently dropping an unusable command makes a skip look like a pass."""

    _order(repo, "**机检**：pytest & del /f /q C:\\Windows\\win.ini\n")
    snap = _snapshot(cli)
    _done(tmp_path, base_sha=snap["end_sha"], end_sha=snap["end_sha"],
          tree_oid=snap["tree_oid"], status_entries=snap["status_entries"],
          changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "declared_command_plan" in payload["blocking_failures"]


def test_a_glued_inline_payload_is_refused(tmp_path, repo, cli):
    """`-cprint(1)` is the same bypass as `-c print(1)`, glued into one token."""

    import sys
    _order(repo, f"**机检**：{sys.executable} -cprint(1) -m pytest\n")
    snap = _snapshot(cli)
    _done(tmp_path, base_sha=snap["end_sha"], end_sha=snap["end_sha"],
          tree_oid=snap["tree_oid"], status_entries=snap["status_entries"],
          changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "declared_command_plan" in payload["blocking_failures"]


def test_a_marker_without_a_command_cannot_hide_beside_a_valid_one(tmp_path, repo, cli):
    """A broken marker used to be skipped, so one good command covered for it."""

    _order(repo, "**机检**：pytest -q a_missing_test.py\n**机检** pytest -q b_missing_test.py\n")
    snap = _snapshot(cli)
    _done(tmp_path, base_sha=snap["end_sha"], end_sha=snap["end_sha"],
          tree_oid=snap["tree_oid"], status_entries=snap["status_entries"],
          changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "declared_command_plan" in payload["blocking_failures"]


def test_an_untracked_file_in_the_write_scope_fails(tmp_path, repo, cli):
    """A file that took part in the run but is in no commit cannot be frozen."""

    _card(repo, "wo-x", ["new.txt"])
    (repo / "new.txt").write_text("delivered\n", encoding="utf-8")
    snap = _snapshot(cli)
    _done(tmp_path, base_sha=snap["end_sha"], end_sha=snap["end_sha"],
          tree_oid=snap["tree_oid"], status_entries=snap["status_entries"],
          changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "no_untracked_in_write_scope" in payload["blocking_failures"]


def test_a_runner_planted_in_the_workspace_is_refused(repo, cli):
    """`tools/pytest.exe` copied from cmd.exe has the right name and is not pytest.

    The basename check cannot carry this: any program can be given that name. What
    separates a runner from a plant is where it lives.
    """

    planted = cli.ROOT / "tools" / "pytest.exe"
    planted.parent.mkdir(parents=True, exist_ok=True)
    planted.write_text("", encoding="utf-8")
    reason = cli._command_is_a_test_run([str(planted)])
    assert "registered interpreter" in reason

    # A path shape that merely resembles the project virtualenv is not a registered
    # tool either, and a path that does not exist cannot be a runner at all.
    lookalike = cli.ROOT / "tools" / "venv-anything" / "Scripts" / "pytest.exe"
    lookalike.parent.mkdir(parents=True, exist_ok=True)
    lookalike.write_text("", encoding="utf-8")
    assert "registered" in cli._command_is_a_test_run([str(lookalike)])
    (cli.ROOT / "tools" / "venv-nope" / "Scripts").mkdir(parents=True, exist_ok=True)
    assert "does not exist" in cli._command_is_a_test_run(
        [str(cli.ROOT / "tools" / "venv-nope" / "Scripts" / "python.exe")])


def test_argument_limits_apply_whatever_the_entry_point(repo, cli):
    """The limits used to sit after the "plain pytest" early return.

    A command that named pytest directly skipped every argument check, so
    ``--rootdir`` or a separated ``-o`` changed where and how the run happened
    while the gate still reported the command as acceptable.
    """

    venv = cli.ROOT / "tools" / "venv-openjarvis" / "Scripts"
    venv.mkdir(parents=True, exist_ok=True)
    (venv / "pytest.exe").write_text("", encoding="utf-8")
    (venv / "python.exe").write_text("", encoding="utf-8")
    pytest_exe = str(venv / "pytest.exe")

    assert cli._command_is_a_test_run([pytest_exe, "tests/queue_engine"]) == ""
    # Every one of these decides what gets collected or whether anything runs at
    # all, and the gate now refuses the whole class rather than naming them.
    for extra in (["--rootdir=.."], ["-p", "anyio"], ["-o", "addopts=-q"],
                  ["-o", "addopts="], ["--collect-only"], ["-m", "slow"],
                  ["--ignore-glob=*"], ["-kcache"], ["@args.txt"]):
        assert "test targets" in cli._command_is_a_test_run([pytest_exe, *extra])

    # The gate builds the run. On the console script `-m` is pytest's marker filter,
    # so the fixed form must not add `-m pytest` there — that collects nothing.
    assert cli._gate_argv([pytest_exe, "tests/queue_engine"]) == [
        pytest_exe, "-o", "addopts=", f"--junitxml={cli._JUNIT_NAME}", "tests/queue_engine"]
    assert cli._gate_argv([str(venv / "python.exe"), "-m", "pytest", "tests/queue_engine"]) == [
        str(venv / "python.exe"), "-m", "pytest", "-o", "addopts=",
        f"--junitxml={cli._JUNIT_NAME}", "tests/queue_engine"]


def test_an_interpreter_outside_the_registered_venv_is_refused(tmp_path, cli):
    """Any python.exe can host pytest. Identity is the registered location, not the name."""

    outside = tmp_path / "python.exe"
    outside.write_text("", encoding="utf-8")
    assert "registered interpreter" in cli._command_is_a_test_run(
        [str(outside), "-m", "pytest", "tests"])


def test_an_untracked_conftest_is_refused(tmp_path, repo, cli):
    """pytest loads conftest.py without anyone declaring it, so it must be tracked."""

    _card(repo, "wo-x", ["a.txt"])
    (repo / "tests").mkdir(exist_ok=True)
    (repo / "tests" / "conftest.py").write_text(
        "import pytest\npytest.skip('injected', allow_module_level=True)\n", encoding="utf-8")
    snap = _snapshot(cli)
    _done(tmp_path, base_sha=snap["end_sha"], end_sha=snap["end_sha"],
          tree_oid=snap["tree_oid"], status_entries=snap["status_entries"],
          changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "no_untracked_test_inputs" in payload["blocking_failures"]


def test_a_declared_file_without_a_dispatch_commit_does_not_pass(tmp_path, repo, cli):
    """Existence without a base commit proves nothing about delivery."""

    _card(repo, "wo-x", ["a.txt"])
    snap = _snapshot(cli)
    _done(tmp_path, end_sha=snap["end_sha"], tree_oid=snap["tree_oid"],
          status_entries=snap["status_entries"], changed_files=snap["changed_files"])
    payload = cli.verify("wo-x", tmp_path)
    assert "declared_files_landed" in payload["blocking_failures"]
