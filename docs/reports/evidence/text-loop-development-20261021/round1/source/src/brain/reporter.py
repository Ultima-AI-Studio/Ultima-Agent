"""Text orchestration and Chinese aggregate reporting for task status."""

from __future__ import annotations

import re
from dataclasses import dataclass
from pathlib import Path

from .intent import parse_task_status_intent
from .queue_source import QueueSnapshot, TaskStatus, read_queue_status


_TASK_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9._~-]*$")


@dataclass(frozen=True, slots=True)
class TextResponse:
    handled: bool
    ok: bool
    text: str


def respond_to_text(
    text: str | None,
    *,
    queue_root: str | Path,
    detail_task_id: str | None = None,
) -> TextResponse:
    """Handle an explicit task-status query; unmatched text performs no read."""
    intent = parse_task_status_intent(text)
    if not intent.matched:
        return TextResponse(False, True, "")
    if detail_task_id is not None and not _TASK_ID.fullmatch(detail_task_id):
        return TextResponse(True, False, "任务 ID 非法，已拒绝读取。")

    snapshot = read_queue_status(queue_root)
    if not snapshot.ok:
        return TextResponse(True, False, snapshot.message)
    if detail_task_id is not None:
        return _detail(snapshot, detail_task_id)
    return TextResponse(True, True, _aggregate(snapshot))


def _aggregate(snapshot: QueueSnapshot) -> str:
    if snapshot.total == 0:
        return "当前任务库为空，共 0 个任务，没有当前异常。"
    anomaly_count = len(snapshot.anomalies)
    if not anomaly_count:
        nonzero = [
            f"{_state_label(state)} {count} 个"
            for state, count in snapshot.counts.items()
            if count
        ]
        return "\n".join(
            (
                f"当前共 {snapshot.total} 个任务，没有当前异常。",
                "当前状态汇总：" + "，".join(nonzero) + "。",
            )
        )

    lines = [f"当前共 {snapshot.total} 个任务，有 {anomaly_count} 个异常。"]
    lines.extend(_anomaly_line(task) for task in snapshot.anomalies)
    normal_count = (snapshot.total or 0) - anomaly_count
    if normal_count:
        lines.append(f"其余 {normal_count} 个任务当前无失败或冻结，已聚合省略。")
    return "\n".join(lines)


def _detail(snapshot: QueueSnapshot, task_id: str) -> TextResponse:
    task = next((item for item in snapshot.tasks if item.task_id == task_id), None)
    if task is None:
        return TextResponse(True, False, f"未找到任务 ID：{task_id}。")
    reason = task.terminal_reason or "未记录终态原因"
    text = (
        f"任务 {task.task_id}（{task.title_zh}）：{task.state_zh}；"
        f"优先级 {task.priority}；耗时 {task.duration}；终态原因：{reason}。"
    )
    return TextResponse(True, True, text)


def _anomaly_line(task: TaskStatus) -> str:
    reason = task.terminal_reason or "未记录原因"
    return (
        f"{task.state_zh}任务 {task.task_id}（{task.title_zh}），"
        f"优先级 {task.priority}，耗时 {task.duration}，原因：{reason}。"
    )


def _state_label(state: str) -> str:
    labels = {
        "QUEUED": "排队中",
        "EXECUTING": "执行中",
        "SELF-CHECK": "自检中",
        "AUDIT": "审计中",
        "COMPLETED": "已完成（通过）",
        "FAILED": "失败",
        "BLOCKED": "冻结",
        "CANCELLED": "已取消",
    }
    return labels[state]
