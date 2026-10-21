from __future__ import annotations

import hashlib
import json
import os
import subprocess
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[3]
sys.path.insert(0, str(PROJECT_ROOT))

EXPECTED_COMMIT = "43ce13021f16f191bb36615ebb6c68465bf201fa"
EXPECTED_TASKS_HASH = "37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570"
MANIFEST_PATH = PROJECT_ROOT / "docs/reports/evidence/v01-freeze-20261021/source-manifest.json"


def sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def main() -> int:
    manifest = json.loads(MANIFEST_PATH.read_text(encoding="utf-8-sig"))
    mismatches = []
    for raw_path, expected in manifest.items():
        path = Path(raw_path)
        actual = sha256(path) if path.is_file() else None
        if actual != expected:
            mismatches.append(
                {"path": str(path), "expected": expected, "actual": actual}
            )

    result = subprocess.run(
        ["git", "-C", str(PROJECT_ROOT), "rev-list", "-n", "1", "v0.1-frozen"],
        capture_output=True,
        text=True,
        timeout=10,
        creationflags=0x08000000 if os.name == "nt" else 0,
        check=False,
    )
    tag_commit = result.stdout.strip() if result.returncode == 0 else None
    tasks_hash = sha256(PROJECT_ROOT / "tasks/tasks.json")
    passed = (
        len(manifest) == 36
        and not mismatches
        and tag_commit == EXPECTED_COMMIT
        and tasks_hash == EXPECTED_TASKS_HASH
    )
    print(
        json.dumps(
            {
                "status": "PASS" if passed else "FAIL",
                "v0.1_tag_commit": tag_commit,
                "expected_commit": EXPECTED_COMMIT,
                "manifest_items": len(manifest),
                "manifest_matching": len(manifest) - len(mismatches),
                "manifest_mismatches": mismatches,
                "production_tasks_sha256": tasks_hash,
                "production_tasks_unchanged": tasks_hash == EXPECTED_TASKS_HASH,
            },
            ensure_ascii=False,
            indent=2,
        )
    )
    return 0 if passed else 1


if __name__ == "__main__":
    raise SystemExit(main())
