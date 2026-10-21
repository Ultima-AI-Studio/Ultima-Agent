from __future__ import annotations

import hashlib
import json
from pathlib import Path


OUT = Path(__file__).resolve().parent
TARGET = OUT / "evidence-sha256.json"


def main() -> int:
    if TARGET.exists():
        raise FileExistsError(TARGET)
    manifest = {
        path.relative_to(OUT).as_posix(): hashlib.sha256(path.read_bytes()).hexdigest()
        for path in sorted(OUT.rglob("*"))
        if path.is_file() and path != TARGET
    }
    TARGET.write_text(
        json.dumps(manifest, ensure_ascii=False, indent=2) + "\n",
        encoding="utf-8",
    )
    print(json.dumps({"status": "PASS", "sealed_files": len(manifest)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
