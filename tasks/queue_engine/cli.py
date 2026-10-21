"""Minimal command-line entry points required by the queue specification."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

if __package__ in {None, ""}:
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from tasks.queue_engine.priority_deps import QueuePlanner
from tasks.queue_engine.storage import QueueStorage
from tasks.queue_engine.dispatcher import Dispatcher
from tasks.queue_engine.audit import RecoveryManager
from tasks.queue_engine.card_contract import validate_card


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(prog="queue-engine")
    parser.add_argument(
        "--root",
        type=Path,
        default=Path(__file__).resolve().parents[1],
        help="task library root (defaults to the project tasks directory)",
    )
    commands = parser.add_subparsers(dest="command", required=True)
    requeue = commands.add_parser("requeue")
    requeue.add_argument("task_id")
    requeue.add_argument("--before", required=True, dest="target_id")
    requeue.add_argument("--actor", default="human")
    requeue.add_argument("--reason", required=True)
    commands.add_parser('status')
    enqueue = commands.add_parser('enqueue')
    enqueue.add_argument('record', type=Path)
    run = commands.add_parser('run')
    run.add_argument('task_id')
    run.add_argument('argv', nargs=argparse.REMAINDER)
    recover = commands.add_parser('recover')
    recover.add_argument('task_id')
    correction = commands.add_parser('correct')
    correction.add_argument('task_id')
    correction.add_argument('--actor', required=True, choices=['human', 'brain'])
    correction.add_argument('--reason', required=True)
    return parser


def main(argv: list[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    if args.command != 'requeue':
        try:
            return execute(args)
        except (ValueError, OSError, RuntimeError) as exc:
            print(json.dumps({'status': 'error', 'reason': str(exc)}, ensure_ascii=False))
            return 2
    if args.command == "requeue":
        planner = QueuePlanner(QueueStorage(args.root))
        planner.requeue_before(
            args.task_id,
            args.target_id,
            actor=args.actor,
            reason=args.reason,
        )
        print(
            json.dumps(
                {
                    "status": "ok",
                    "operation": "requeue",
                    "task_id": args.task_id,
                    "before": args.target_id,
                },
                ensure_ascii=False,
            )
        )
        return 0
    raise AssertionError(f"unhandled command: {args.command}")


def execute(args: argparse.Namespace) -> int:
    storage = QueueStorage(args.root)
    if args.command == 'correct':
        task = RecoveryManager(storage).create_correction(args.task_id, actor=args.actor, reason=args.reason)
        print(json.dumps(task, ensure_ascii=False))
        return 0 if task['state'] == 'QUEUED' else 2
    if args.command == 'status':
        tasks = storage.load_tasks()
        print(json.dumps({'tasks': tasks, 'counts': {
            state: sum(t['state'] == state for t in tasks)
            for state in sorted({t['state'] for t in tasks})
        }}, ensure_ascii=False, indent=2))
        return 0
    if args.command == 'enqueue':
        task = json.loads(args.record.read_text(encoding='utf-8-sig'))
        storage.validate_index_record(task)
        if task['state'] != 'QUEUED':
            raise ValueError('enqueue 只允许 QUEUED，不得导入未经审计的完成状态')
        card = Path(task['card_path'])
        if not card.is_absolute():
            card = storage.root / card
        if not card.is_file():
            raise ValueError(f'任务卡不存在：{card}')
        task['card_path'] = str(card.resolve())
        validate_card(task, storage.root)
        QueuePlanner(storage).enqueue(task)
        print(json.dumps({'status': 'queued', 'task_id': task['task_id']}))
        return 0
    if args.command == 'run':
        command = args.argv[1:] if args.argv[:1] == ['--'] else args.argv
        if not command:
            raise ValueError('run 必须提供 -- 后的执行命令')
        task = next((item for item in storage.load_tasks() if item['task_id'] == args.task_id), None)
        if task is None:
            raise ValueError('任务不存在')
        validate_card(task, storage.root, runtime=True)
        dispatcher = Dispatcher(storage)
        decision = dispatcher.dispatch(args.task_id, command)
        if not decision.dispatched:
            print(json.dumps({'status': 'waiting', 'reason': decision.reason}, ensure_ascii=False))
            return 2
        dispatcher.take_process(decision.pid).wait()
    if args.command in {'run', 'recover'}:
        recovery = RecoveryManager(storage)
        task, reason = recovery.recover_finished_run(args.task_id)
        if task['state'] == 'SELF-CHECK':
            task = recovery.finish_self_check_from_run(args.task_id)
        print(json.dumps({'task_id': args.task_id, 'state': task['state'],
                          'reason': task['terminal_reason'] or reason}, ensure_ascii=False))
        return 0 if task['state'] in {'AUDIT', 'COMPLETED'} else 2
    raise ValueError(f'未知命令：{args.command}')


if __name__ == "__main__":
    raise SystemExit(main())
