from __future__ import annotations

import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import sys

import pytest


REPO = Path(__file__).resolve().parents[2]
HISTORICAL_SEMANTIC_TAGS = [
    ("wo-ultimaagent-20261101-0013", "ultimaagent-mainbrain-qwen3-8b-cleanup-20261101"),
    ("wo-ultimaagent-20261101-0014", "ultimaagent-kws-user-entry-20261101"),
    ("wo-ultimaagent-20261101-0015", "ultimaagent-asr-correction-20261101"),
    ("wo-ultimaagent-20261101-0016", "ultimaagent-reply-constraint-routing-20261101"),
    ("wo-ultimaagent-20261101-0017", "ultimaagent-reply-constraint-structured-20261101"),
    ("wo-ultimaagent-20261101-0019", "ultimaagent-wekws-offline-proof-20261101"),
    ("wo-ultimaagent-20261101-0020", "ultimaagent-voice-next-live-pass-20261101"),
    ("wo-ultimaagent-20261103-0022", "ultimaagent-middleware-v1-20261103"),
    ("wo-ultimaagent-20261103-0023", "ultimaagent-jarvis-p0-20261103"),
    ("wo-ultimaagent-20261108-0026", "ultimaagent-audit-hardening-20261108"),
]


@pytest.fixture
def doctor(tmp_path, monkeypatch):
    name = f"queue_doctor_test_{tmp_path.name}"
    spec = importlib.util.spec_from_file_location(name, REPO / "scripts" / "queue-doctor.py")
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)

    queue = tmp_path / "tasks" / "queue"
    runs = queue / "runs"
    runs.mkdir(parents=True)
    monkeypatch.setattr(module, "ROOT", tmp_path)
    monkeypatch.setattr(module, "QUEUE_DIR", queue)
    monkeypatch.setattr(module, "STATUS_FILE", queue / "queue-status.json")
    monkeypatch.setattr(module, "RUNS_DIR", runs)
    monkeypatch.setattr(module, "_tracked_cards", lambda: set())
    monkeypatch.setattr(module, "_tags", lambda: [])
    monkeypatch.setattr(
        module.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"differences": []}),
            stderr="",
        ),
    )
    return module


def _record(order: str, state: str = "pending", *, legacy: bool = False, note: str = "") -> dict:
    return {
        "project": "UltimaAgent",
        "work_order": order,
        "state": state,
        "legacy": legacy,
        "audit_run": None,
        "note": note,
    }


def _status(doctor, records: list[dict]) -> None:
    doctor.STATUS_FILE.write_text(
        json.dumps({"records": records}, ensure_ascii=False),
        encoding="utf-8",
    )


def _card(doctor, monkeypatch, order: str, *, tracked: bool = True) -> Path:
    path = doctor.QUEUE_DIR / f"{order}--fixture.md"
    path.write_text(f"# fixture\n\nwork_order: `{order}`\n", encoding="utf-8")
    rel = path.relative_to(doctor.ROOT).as_posix().casefold()
    monkeypatch.setattr(doctor, "_tracked_cards", lambda: {rel} if tracked else set())
    return path


def _dispatch(doctor, run_name: str, order: str) -> Path:
    path = doctor.RUNS_DIR / run_name / "dispatch-record.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"order": order}), encoding="utf-8")
    return path


def _tag_receipt(doctor, run_name: str, order: str, tag: str) -> Path:
    path = doctor.RUNS_DIR / run_name / "session.json"
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps({"order": order, "tag": tag}), encoding="utf-8")
    return path


def _codes(result: dict) -> list[str]:
    return [finding["code"] for finding in result["findings"]]


def test_card_missing_positive_and_negative_through_diagnose(doctor, monkeypatch):
    order = "wo-fixture-20261111-0001"
    _status(doctor, [_record(order)])
    assert "CARD_MISSING" in _codes(doctor.diagnose())

    _card(doctor, monkeypatch, order)
    assert "CARD_MISSING" not in _codes(doctor.diagnose())


def test_card_untracked_positive_and_head_tracked_negative(doctor, monkeypatch):
    order = "wo-fixture-20261111-0002"
    _status(doctor, [_record(order)])
    _card(doctor, monkeypatch, order, tracked=False)
    assert "CARD_UNTRACKED" in _codes(doctor.diagnose())

    _card(doctor, monkeypatch, order, tracked=True)
    assert "CARD_UNTRACKED" not in _codes(doctor.diagnose())


def test_frozen_tag_positive_and_receipt_fact_negative(doctor, monkeypatch):
    order = "wo-fixture-20261111-0003"
    tag = "semantic-freeze-20261111"
    _status(doctor, [_record(order, "frozen")])
    _card(doctor, monkeypatch, order)
    _dispatch(doctor, "semantic-run", order)
    assert "FROZEN_WITHOUT_TAG" in _codes(doctor.diagnose())

    _tag_receipt(doctor, "semantic-run", order, tag)
    monkeypatch.setattr(doctor, "_tags", lambda: [tag])
    result = doctor.diagnose()
    assert "FROZEN_WITHOUT_TAG" not in _codes(result)
    check = next(item for item in result["checks"] if item["code"] == "FROZEN_TAG")
    assert check["tag"] == tag
    assert check["confidence"] == "high"


def test_note_tag_fallback_is_explicitly_low_confidence(doctor, monkeypatch):
    order = "wo-fixture-20261111-0004"
    tag = "semantic-note-freeze-20261111"
    _status(doctor, [_record(order, "frozen", note=f"冻结 tag {tag}")])
    _card(doctor, monkeypatch, order)
    _dispatch(doctor, "dispatch", order)
    monkeypatch.setattr(doctor, "_tags", lambda: [tag])

    result = doctor.diagnose()

    assert "FROZEN_WITHOUT_TAG" not in _codes(result)
    check = next(item for item in result["checks"] if item["code"] == "FROZEN_TAG")
    assert check["confidence"] == "low"
    assert tag in check["evidence"]


def test_frozen_run_positive_and_dispatch_record_negative(doctor, monkeypatch):
    order = "wo-fixture-20261111-0005"
    tag = "semantic-run-freeze-20261111"
    _status(doctor, [_record(order, "frozen")])
    _card(doctor, monkeypatch, order)
    _tag_receipt(doctor, "session-only", order, tag)
    monkeypatch.setattr(doctor, "_tags", lambda: [tag])
    assert "FROZEN_WITHOUT_RUN" in _codes(doctor.diagnose())

    _dispatch(doctor, "content-identified-run", order)
    assert "FROZEN_WITHOUT_RUN" not in _codes(doctor.diagnose())


def test_audit_run_positive_and_content_identity_negative(doctor, monkeypatch):
    order = "wo-fixture-20261111-0006"
    _status(doctor, [_record(order, "audit", note="独立审计 PASS")])
    _card(doctor, monkeypatch, order)
    assert "AUDIT_WITHOUT_RUN" in _codes(doctor.diagnose())

    _dispatch(doctor, "not-named-after-the-order", order)
    assert "AUDIT_WITHOUT_RUN" not in _codes(doctor.diagnose())


def test_stale_blocker_uses_current_probe_for_positive_and_negative(doctor, monkeypatch):
    order = "wo-fixture-20261111-0007"
    _status(doctor, [_record(order, "blocked", note="等待 clean-tree，未提交改动需清理")])
    _card(doctor, monkeypatch, order)
    monkeypatch.setattr(
        doctor,
        "_git_result",
        lambda *args: SimpleNamespace(returncode=0, stdout="", stderr=""),
    )
    result = doctor.diagnose()
    finding = next(item for item in result["findings"] if item["code"] == "STALE_BLOCKER")
    assert finding["classification"] == "issue"
    assert "0 non-empty lines" in finding["evidence"]

    monkeypatch.setattr(
        doctor,
        "_git_result",
        lambda *args: SimpleNamespace(returncode=0, stdout="?? live-change\n", stderr=""),
    )
    assert "STALE_BLOCKER" not in _codes(doctor.diagnose())


def test_unmeasurable_blocker_is_unverifiable_not_guessed_stale(doctor, monkeypatch):
    order = "wo-fixture-20261111-0008"
    _status(doctor, [_record(order, "blocked", note="等待外部 Owner 的语义裁决")])
    _card(doctor, monkeypatch, order)

    finding = next(item for item in doctor.diagnose()["findings"] if item["code"] == "STALE_BLOCKER")

    assert finding["classification"] == "unverifiable"
    assert finding["confidence"] == "none"
    assert "not guessed" in finding["evidence"]


def test_orphan_run_positive_and_known_dispatch_identity_negative(doctor, monkeypatch):
    known = "wo-fixture-20261111-0009"
    unknown = "wo-fixture-20261111-9999"
    _status(doctor, [_record(known)])
    _card(doctor, monkeypatch, known)
    dispatch = _dispatch(doctor, "semantic-run", unknown)
    assert "ORPHAN_RUN" in _codes(doctor.diagnose())

    dispatch.write_text(json.dumps({"order": known}), encoding="utf-8")
    assert "ORPHAN_RUN" not in _codes(doctor.diagnose())


def test_view_drift_positive_and_equal_views_negative(doctor, monkeypatch):
    _status(doctor, [])
    monkeypatch.setattr(
        doctor.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=1,
            stdout=json.dumps({"differences": ["tasks/queue/index.md"]}),
            stderr="",
        ),
    )
    assert "VIEW_DRIFT" in _codes(doctor.diagnose())

    monkeypatch.setattr(
        doctor.subprocess,
        "run",
        lambda *args, **kwargs: SimpleNamespace(
            returncode=0,
            stdout=json.dumps({"differences": []}),
            stderr="",
        ),
    )
    assert "VIEW_DRIFT" not in _codes(doctor.diagnose())


@pytest.mark.parametrize(
    ("state", "target"),
    [
        ("pending", "LEGACY_CARD_MISSING"),
        ("frozen", "LEGACY_FROZEN_WITHOUT_TAG"),
        ("audit", "LEGACY_AUDIT_WITHOUT_RUN"),
    ],
)
def test_legacy_p0_codes_downgrade_and_keep_prefix(doctor, monkeypatch, state, target):
    order = "wo-fixture-20261111-0010"
    _status(doctor, [_record(order, state, legacy=True)])
    if state != "pending":
        _card(doctor, monkeypatch, order)

    finding = next(item for item in doctor.diagnose()["findings"] if item["code"] == target)

    assert finding["level"] == "P1"
    assert finding["evidence"]


@pytest.mark.parametrize(("order", "tag"), HISTORICAL_SEMANTIC_TAGS)
def test_ten_historical_semantic_tag_false_positives_are_regressions(
    doctor, monkeypatch, order, tag
):
    _status(doctor, [_record(order, "frozen")])
    _card(doctor, monkeypatch, order)
    _dispatch(doctor, "semantic-dispatch", order)
    _tag_receipt(doctor, "semantic-dispatch", order, tag)
    monkeypatch.setattr(doctor, "_tags", lambda: [tag])

    result = doctor.diagnose()

    assert "FROZEN_WITHOUT_TAG" not in _codes(result)
    check = next(item for item in result["checks"] if item["code"] == "FROZEN_TAG")
    assert check["tag"] == tag
    assert tag in check["evidence"]


def test_prefix_collision_does_not_hide_missing_tag_or_run(doctor, monkeypatch):
    order = "wo-fixture-20261111-0011"
    decoy = f"{order}-decoy"
    _status(doctor, [_record(order, "frozen")])
    _card(doctor, monkeypatch, order)
    _dispatch(doctor, "prefix-looking-run", decoy)
    monkeypatch.setattr(doctor, "_tags", lambda: [decoy])

    result = doctor.diagnose()

    assert "FROZEN_WITHOUT_TAG" in _codes(result)
    assert "FROZEN_WITHOUT_RUN" in _codes(result)


def test_every_issue_has_nonempty_evidence(doctor, monkeypatch):
    missing = "wo-fixture-20261111-0012"
    blocked = "wo-fixture-20261111-0013"
    _status(
        doctor,
        [
            _record(missing, "frozen"),
            _record(blocked, "blocked", note="外部状态无法本机验证"),
        ],
    )
    _dispatch(doctor, "orphan", "wo-fixture-20261111-9998")

    result = doctor.diagnose()

    assert result["findings"]
    assert all(str(item.get("evidence", "")).strip() for item in result["findings"])


def test_strict_exit_codes_for_p0_and_no_p0(doctor, monkeypatch):
    monkeypatch.setattr(doctor.sys, "argv", ["queue-doctor.py", "--strict", "--json"])
    monkeypatch.setattr(
        doctor,
        "diagnose",
        lambda: {"p0": 1, "p1": 0, "findings": [], "checks": []},
    )
    assert doctor.main() == 2

    monkeypatch.setattr(
        doctor,
        "diagnose",
        lambda: {"p0": 0, "p1": 1, "findings": [], "checks": []},
    )
    assert doctor.main() == 0


def test_runtime_error_exit_code_is_one(doctor, monkeypatch, capsys):
    monkeypatch.setattr(doctor.sys, "argv", ["queue-doctor.py", "--strict"])

    def fail():
        raise RuntimeError("fixture boom")

    monkeypatch.setattr(doctor, "diagnose", fail)

    assert doctor.main() == 1
    assert "fixture boom" in capsys.readouterr().err
