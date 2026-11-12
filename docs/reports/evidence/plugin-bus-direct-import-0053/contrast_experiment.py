from __future__ import annotations

import json
import sys
from pathlib import Path


REPO_ROOT = Path(__file__).resolve().parents[4]
TEST_ROOT = REPO_ROOT / "execution" / "server" / "tests"
if str(TEST_ROOT) not in sys.path:
    sys.path.insert(0, str(TEST_ROOT))

from test_ultima_bus import BusTestCase
from ultima_bus.errors import PermissionDenied


def run_sample(label: str, imported_name: str, expect_denied: bool) -> None:
    case = BusTestCase()
    case.setUp()
    try:
        provider = case.create_plugin()
        assert case.kernel.register_manifest(provider)["ok"]
        case.kernel.load("ultima.intent.test")

        consumer = case.create_plugin(
            module_id="ultima.memory.test",
            domain="L9",
            exposes=["memory.read"],
            entry_suffix=label,
        )
        manifest = json.loads(consumer.read_text(encoding="utf-8"))
        source = consumer.parent / manifest["entry"].split(".")[0] / "main.py"
        source.write_text(
            f"import {imported_name}\n" + source.read_text(encoding="utf-8"),
            encoding="utf-8",
        )
        assert case.kernel.register_manifest(consumer)["ok"]

        try:
            case.kernel.load("ultima.memory.test")
            outcome = "ALLOWED"
            detail = "load completed"
            audit_package = "n/a"
        except PermissionDenied as exc:
            outcome = "DENIED"
            detail = str(exc)
            events = [
                json.loads(line)
                for line in (case.base / "runtime.jsonl").read_text(encoding="utf-8").splitlines()
            ]
            audit_event = next(
                event
                for event in reversed(events)
                if event["event_type"] == "audit.plugin.direct-import.denied"
            )
            audit_package = repr(audit_event["payload"]["package"])

        expected = "DENIED" if expect_denied else "ALLOWED"
        print(
            f"{label}: import {imported_name} -> {outcome} (expected {expected}); "
            f"audit_package={audit_package}; {detail}"
        )
        if outcome != expected:
            raise AssertionError(f"{label}: expected {expected}, got {outcome}")
    finally:
        case.tearDown()


if __name__ == "__main__":
    run_sample("real_package_name", "plugin_ultima_intent_test_0_1_0", True)
    run_sample("module_id_form", "ultima.intent.test", True)
    run_sample("stdlib_control", "os", False)
    print("CONTRAST_RESULT=PASS")
