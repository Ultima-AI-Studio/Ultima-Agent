"""Command-line entry point for the offline task-status text loop."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.brain.reporter import respond_to_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UltimaAgent 任务状态文字查询")
    parser.add_argument("text", nargs="?", default="", help="用户文字输入")
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT / "tasks",
        help="任务库根目录",
    )
    parser.add_argument("--task-id", help="明确下钻的任务 ID")
    arguments = parser.parse_args(argv)
    response = respond_to_text(
        arguments.text,
        queue_root=arguments.root,
        detail_task_id=arguments.task_id,
    )
    if response.text:
        print(response.text)
    return 0 if response.ok else 2


if __name__ == "__main__":
    raise SystemExit(main())
