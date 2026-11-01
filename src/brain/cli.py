"""Command-line entry point for the offline task-status text loop (L0) and
the L7 interaction loop (征询闭环 / 队列调整 / 异步三拍)."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
sys.path.insert(0, str(PROJECT_ROOT))

from src.brain.interaction import InteractionLoop
from src.brain.reporter import respond_to_text


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="UltimaAgent 任务状态文字查询 / L7 交互循环")
    parser.add_argument("text", nargs="?", default="", help="用户文字输入")
    parser.add_argument(
        "--root",
        type=Path,
        default=PROJECT_ROOT / "tasks",
        help="任务库根目录",
    )
    parser.add_argument("--task-id", help="明确下钻的任务 ID")
    parser.add_argument(
        "--loop",
        action="store_true",
        help="启用 L7 交互循环（征询/调整/三拍）",
    )
    parser.add_argument(
        "--agent",
        action="store_true",
        help="文字试点：走本地 Agent 循环（agent_server，14B 自主回答/调工具）",
    )
    parser.add_argument('--work', action='store_true')
    parser.add_argument('--request-id')
    parser.add_argument('--session-id')
    parser.add_argument('--server-url', default='http://127.0.0.1:8756')
    parser.add_argument('--json', action='store_true')
    arguments = parser.parse_args(argv)
    if arguments.work:
        import json
        from src.brain.agent_client import ask_work
        if arguments.agent or arguments.loop or not arguments.request_id or not arguments.session_id or not arguments.text.strip():
            parser.error('--work requires text, --request-id and --session-id and cannot combine with --agent/--loop')
        try:
            result = ask_work(arguments.text, request_id=arguments.request_id, session_id=arguments.session_id, server_url=arguments.server_url)
        except Exception as exc:
            result = dict(status='failed', error=str(exc), artifacts=[], content='')
        print(json.dumps(result, ensure_ascii=False) if arguments.json else result.get('content') or result.get('error'))
        return 0 if result.get('status') == 'succeeded' else 2

    if arguments.agent:
        from src.brain.agent_client import ask_agent

        if not arguments.text.strip():
            print("请提供要问的内容，例如：python -m src.brain.cli --agent \"查一下任务状态\"")
            return 2
        try:
            content = ask_agent(arguments.text)
        except Exception as exc:  # 服务器未启动/异常：给可读提示，不抛 traceback
            print(f"Agent 服务器调用失败：{exc}")
            return 2
        if content:
            print(content)
        return 0

    if arguments.loop:
        session = InteractionLoop(arguments.root)
        response = session.handle(arguments.text, detail_task_id=arguments.task_id)
        if response.text:
            print(response.text)
        return 0 if response.ok else 2

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
