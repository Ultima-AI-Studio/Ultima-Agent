from __future__ import annotations

import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
SOURCE = (
    ROOT
    / "docs"
    / "reports"
    / "evidence"
    / "w4-independent-20261021"
    / "round1"
    / "review_checks.py"
)
OUT = Path(__file__).resolve().parent / "independent-review-rerun"
sys.path.insert(0, str(ROOT))


def main() -> int:
    OUT.mkdir(exist_ok=False)
    source = SOURCE.read_text(encoding="utf-8")
    namespace = {
        "__file__": str(OUT / "review_checks.py"),
        "__name__": "__main__",
    }
    exec(compile(source, str(SOURCE), "exec"), namespace)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
