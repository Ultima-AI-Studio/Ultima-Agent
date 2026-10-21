from __future__ import annotations

import argparse
import os
import subprocess
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[2]
OUT = Path(__file__).resolve().parent
PYTHON = ROOT / "tools" / "python31313" / "python.exe"
sys.path.insert(0, str(ROOT))


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("output")
    parser.add_argument("command", nargs=argparse.REMAINDER)
    arguments = parser.parse_args()
    if not arguments.command:
        parser.error("a Python command is required")

    output = (OUT / arguments.output).resolve()
    if not output.is_relative_to(OUT) or output.exists():
        parser.error("output must be a new file inside the repair evidence directory")

    environment = dict(
        os.environ,
        PYTHONDONTWRITEBYTECODE="1",
        PYTHONPATH=str(ROOT),
    )
    command = [str(PYTHON), "-B", "-X", "utf8", *arguments.command]
    completed = subprocess.run(
        command,
        cwd=ROOT,
        env=environment,
        capture_output=True,
        text=True,
        encoding="utf-8",
        timeout=240,
        creationflags=subprocess.CREATE_NO_WINDOW,
        check=False,
    )
    transcript = "\n".join(
        (
            "COMMAND " + subprocess.list2cmdline(command),
            f"RETURN_CODE {completed.returncode}",
            "STDOUT",
            completed.stdout,
            "STDERR",
            completed.stderr,
        )
    )
    output.write_text(transcript, encoding="utf-8", newline="\n")
    sys.stdout.write(transcript)
    return completed.returncode


if __name__ == "__main__":
    raise SystemExit(main())
