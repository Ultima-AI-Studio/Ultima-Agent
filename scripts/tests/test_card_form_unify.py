from __future__ import annotations

import importlib.util
import hashlib
from pathlib import Path
import sys

import pytest


ROOT = Path(__file__).resolve().parents[2]


def _load(name: str, relative: str):
    script = ROOT / relative
    spec = importlib.util.spec_from_file_location(name, script)
    module = importlib.util.module_from_spec(spec)
    sys.modules[name] = module
    spec.loader.exec_module(module)
    return module


def test_stage_gates_reads_all_real_0030_gates_without_changing_acc_rows():
    contract = _load("gorch_contract_unify", "scripts/gorch_contract.py")
    card = (ROOT / "tasks/queue/wo-ultimaagent-20261108-0030--m4-orchestration-ledger.md").read_text(
        encoding="utf-8-sig"
    )

    gates = contract.stage_gates(card)

    assert [gate["id"] for gate in gates] == [f"Gate T{index}" for index in range(8)]
    assert all(gate["criterion"] for gate in gates)
    assert {gate["how"] for gate in gates} == {"作者在阶段报告里逐条自证"}
    assert contract.acc_rows(card) == []


def test_stage_gates_sorts_numerically_and_stops_at_the_end_of_each_bullet_block():
    contract = _load("gorch_contract_unify_blocks", "scripts/gorch_contract.py")
    card = (
        "**验收（Gate T10）**：\n"
        "- tenth-a\n"
        "- tenth-b\n\n"
        "**禁止**：must not join the criterion\n\n"
        "**验收（Gate T2）**：\n"
        "- second\n"
    )

    assert contract.stage_gates(card) == [
        {"id": "Gate T2", "criterion": "second", "how": "作者在阶段报告里逐条自证"},
        {
            "id": "Gate T10",
            "criterion": "tenth-a；tenth-b",
            "how": "作者在阶段报告里逐条自证",
        },
    ]


def test_stage_gates_refuses_a_duplicate_stage_id():
    contract = _load("gorch_contract_unify_duplicates", "scripts/gorch_contract.py")
    card = "**验收（Gate T1）**：\n- first\n\n**验收（Gate T1）**：\n- second\n"

    with pytest.raises(ValueError, match="reuses stage gate ids"):
        contract.stage_gates(card)


def test_audit_gates_falls_back_to_stage_sections_for_the_real_0030_card():
    audit = _load("audit_work_order_unify_gates", "scripts/audit-work-order.py")
    card = (ROOT / "tasks/queue/wo-ultimaagent-20261108-0030--m4-orchestration-ledger.md").read_text(
        encoding="utf-8-sig"
    )

    assert [gate["id"] for gate in audit.gates(card)] == [f"Gate T{index}" for index in range(8)]


def test_audit_card_id_accepts_queue_stem_and_preserves_legacy_card_id():
    audit = _load("audit_work_order_unify_id", "scripts/audit-work-order.py")

    assert audit._card_id(
        "tasks/queue/wo-ultimaagent-20261108-0030--m4-orchestration-ledger.md"
    ) == "wo-ultimaagent-20261108-0030--m4-orchestration-ledger"
    assert audit._card_id("tasks/cards/s1-unit/task.md") == "s1-unit"


def test_audit_queue_card_uses_stage_verdicts_and_the_raised_injection_windows(tmp_path, monkeypatch):
    audit = _load("audit_work_order_unify_main", "scripts/audit-work-order.py")
    queue = tmp_path / "tasks" / "queue"
    queue.mkdir(parents=True)
    card = queue / "wo-ultimaagent-20261110-0099--queue-card.md"
    card.write_text(
        "# queue card\n\n**验收（Gate T0）**：\n- parser works\n\n" + ("c" * 5000),
        encoding="utf-8",
    )
    evidence = tmp_path / "evidence.md"
    evidence.write_text("e" * 7000, encoding="utf-8")
    run_dir = tmp_path / "run"
    response = "Gate T0: PASS - parser and evidence were supplied\nAUDIT: PASS"
    monkeypatch.setattr(
        audit,
        "call_deepseek",
        lambda _system, _user: {"response": response, "model": "stub-model", "tokens": 1},
    )

    code = audit.main([
        "--work-order", "wo-ultimaagent-20261110-0099",
        "--card", str(card),
        "--run-dir", str(run_dir),
        "--evidence", str(evidence),
    ])

    assert code == 0
    payload = __import__("json").loads((run_dir / "audit.json").read_text(encoding="utf-8"))
    assert payload["audit_passed"] is True
    assert payload["gates"] == ["Gate T0"]
    assert payload["incomplete_inputs"] == []
    assert payload["card_meta"]["complete"] is True
    assert payload["evidence_meta"][0]["complete"] is True
    assert payload["evidence_meta"][0]["shown_chars"] == 7000


def _sha(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _queue_order(tmp_path: Path) -> tuple[str, Path]:
    order = "wo-ultimaagent-20261110-0099"
    queue = tmp_path / "tasks" / "queue"
    queue.mkdir(parents=True)
    card = queue / f"{order}--queue-card.md"
    card.write_text("# queue\n\n**验收（Gate T0）**：\n- works\n", encoding="utf-8")
    return order, card


def test_freeze_binds_the_resolved_queue_card_when_done_cards_are_empty(tmp_path, monkeypatch):
    freeze = _load("freeze_work_order_unify_empty", "scripts/freeze-work-order.py")
    monkeypatch.setattr(freeze, "ROOT", tmp_path)
    order, card = _queue_order(tmp_path)

    binding = freeze._resolve_order_binding(order, [], card)

    assert binding["queue_style"] is True
    assert binding["order_cards"] == []
    assert binding["recorded_ids"] == [card.stem]
    assert binding["receipt_cards"] == [{"path": str(card), "sha256": _sha(card)}]


def test_freeze_accepts_an_explicit_receipt_for_the_same_resolved_queue_card(tmp_path, monkeypatch):
    freeze = _load("freeze_work_order_unify_recorded", "scripts/freeze-work-order.py")
    monkeypatch.setattr(freeze, "ROOT", tmp_path)
    order, card = _queue_order(tmp_path)
    receipt_cards = [{"path": str(card), "sha256": _sha(card)}]

    binding = freeze._resolve_order_binding(order, receipt_cards, card)

    assert binding["queue_style"] is True
    assert binding["receipt_cards"] == receipt_cards


def test_freeze_rejects_a_different_audited_path_for_a_zero_card_order(tmp_path, monkeypatch):
    freeze = _load("freeze_work_order_unify_mismatch", "scripts/freeze-work-order.py")
    monkeypatch.setattr(freeze, "ROOT", tmp_path)
    order, _card = _queue_order(tmp_path)
    other = tmp_path / "elsewhere.md"
    other.write_text("same shape, wrong path", encoding="utf-8")

    with pytest.raises(ValueError, match="resolved queue card"):
        freeze._resolve_order_binding(order, [], other)


def test_freeze_preserves_the_legacy_tasks_cards_binding(tmp_path, monkeypatch):
    freeze = _load("freeze_work_order_unify_legacy", "scripts/freeze-work-order.py")
    monkeypatch.setattr(freeze, "ROOT", tmp_path)
    queue = tmp_path / "tasks" / "queue"
    queue.mkdir(parents=True)
    (queue / "wo-s1-test.md").write_text("| T1 s1-unit | file | gate |\n", encoding="utf-8")
    card = tmp_path / "tasks" / "cards" / "s1-unit" / "task.md"
    card.parent.mkdir(parents=True)
    card.write_text("| ACC-1 | exists | inspect |\n", encoding="utf-8")
    receipt_cards = [{"path": str(card), "sha256": _sha(card)}]

    binding = freeze._resolve_order_binding("wo-s1-test", receipt_cards, card)

    assert binding["queue_style"] is False
    assert binding["order_cards"] == ["s1-unit"]
    assert binding["recorded_ids"] == ["s1-unit"]
    assert binding["receipt_cards"] == receipt_cards
