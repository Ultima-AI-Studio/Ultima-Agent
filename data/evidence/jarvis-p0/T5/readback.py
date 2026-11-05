"""Independent structured readback for work order 0023 receipts."""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUTPUT = Path(__file__).with_name("readback.json")
EXPECTED = {"T0": "GREEN", "T1": "GREEN", "T2": "GREEN", "T3": "GREEN", "T4": "BLOCKED"}


def main() -> int:
    gates = {}
    for stage, expected in EXPECTED.items():
        path = ROOT / stage / "gate.json"
        payload = json.loads(path.read_text(encoding="utf-8"))
        gates[stage] = {
            "status": payload["status"],
            "expected": expected,
            "matches": payload["status"] == expected,
            "path": str(path.relative_to(ROOT.parent)).replace("\\", "/"),
        }
    receipt = json.loads((ROOT / "T5" / "receipt.json").read_text(encoding="utf-8"))
    expected_fields = ("链路号", "执行端", "完成状态", "根因结论", "产出路径", "验收证据", "越界声明", "环境声明")
    result = {
        "work_order": "wo-ultimaagent-20261103-0023",
        "gates": gates,
        "all_gate_statuses_match": all(item["matches"] for item in gates.values()),
        "receipt_fields": list(receipt),
        "eight_fields_exact": tuple(receipt) == expected_fields,
        "honest_terminal_status": receipt["完成状态"].startswith("BLOCKED / REVISE"),
    }
    result["pass"] = result["all_gate_statuses_match"] and result["eight_fields_exact"] and result["honest_terminal_status"]
    OUTPUT.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result["pass"] else 1


if __name__ == "__main__":
    raise SystemExit(main())
