"""M29 登记控制面验收测试。"""

from __future__ import annotations

import json
import re
from pathlib import Path
from unittest.mock import patch

import pytest

from src.brain.orchestration.queue import (
    GlobalQueueRegistrar,
    OrchestratorError,
    TaskQueue,
)


GLOBAL_TABLE = """# test global queue

<!-- queue-summary:start -->
| 项目 | 工单数 | 待派发 | 登记执行中 | 待审计 | 阻塞 | 已完成/闭环 |
|---|---|---|---|---|---|---|
| UltimaConsole | 1 | 0 | 1 | 0 | 0 | 0 |
| 合计 | 1 | 0 | 1 | 0 | 0 | 0 |
<!-- queue-summary:end -->

<!-- queue-items:start -->
| 项目 | 工单 | 状态 | 依据/说明 |
|---|---|---|---|
| UltimaConsole | wo-console-20261029-0001 | executing | fixture |
<!-- queue-items:end -->
"""


def make_registrar(tmp_path: Path, text: str = GLOBAL_TABLE) -> tuple[GlobalQueueRegistrar, Path]:
    tmp_path.mkdir(parents=True, exist_ok=True)
    path = tmp_path / "global-queue-index.md"
    path.write_text(text, encoding="utf-8")
    return GlobalQueueRegistrar(path, allowed_root=tmp_path), path


def table_with_items(*items: str) -> str:
    body = "\n".join(items)
    return f"""# test global queue

<!-- queue-summary:start -->
| 项目 | 工单数 | 待派发 | 登记执行中 | 待审计 | 阻塞 | 已完成/闭环 |
|---|---|---|---|---|---|---|
<!-- queue-summary:end -->

<!-- queue-items:start -->
| 项目 | 工单 | 状态 | 依据/说明 |
|---|---|---|---|
{body}
<!-- queue-items:end -->
"""


def test_work_order_numbers_increment_same_day(tmp_path):
    with patch("src.brain.orchestration.queue._shanghai_date", return_value="20261029"):
        queue = TaskQueue(tmp_path)
        ids = [queue.create(f"task-{index}").task_id for index in range(3)]

    assert ids == [
        "wo-ultimaagent-20261029-0001",
        "wo-ultimaagent-20261029-0002",
        "wo-ultimaagent-20261029-0003",
    ]


def test_work_order_number_resets_on_next_day(tmp_path):
    queue = TaskQueue(tmp_path)
    with patch("src.brain.orchestration.queue._shanghai_date", return_value="20261029"):
        first = queue.create("first")
    with patch("src.brain.orchestration.queue._shanghai_date", return_value="20261030"):
        next_day = queue.create("next-day")

    assert first.task_id == "wo-ultimaagent-20261029-0001"
    assert next_day.task_id == "wo-ultimaagent-20261030-0001"


def test_work_order_number_matches_standard_format(tmp_path):
    task = TaskQueue(tmp_path).create("format")

    assert re.fullmatch(r"wo-[a-z]+-\d{8}-\d{4}", task.task_id)


def test_historical_uuid_task_id_remains_readable(tmp_path):
    historical_id = "a1b2c3d4e5f6"
    (tmp_path / "task-queue.json").write_text(
        json.dumps(
            {
                historical_id: {
                    "task_id": historical_id,
                    "title": "legacy",
                    "phase": "立项",
                }
            },
            ensure_ascii=False,
        ),
        encoding="utf-8",
    )

    queue = TaskQueue(tmp_path)

    assert queue.view()[0]["task_id"] == historical_id


def test_enqueue_updates_project_summary_and_detail(tmp_path):
    registrar, global_path = make_registrar(tmp_path / "shared-queue")
    queue = TaskQueue(tmp_path / "local", registrar=registrar)
    with patch("src.brain.orchestration.queue._shanghai_date", return_value="20261029"):
        task = queue.create("register")

    queue.enqueue(task.task_id)

    text = global_path.read_text(encoding="utf-8")
    assert "| UltimaAgent | 1 | 1 | 0 | 0 | 0 | 0 |" in text
    assert f"| UltimaAgent | {task.task_id} | pending |" in text


def test_state_transitions_update_canonical_global_state(tmp_path):
    registrar, global_path = make_registrar(tmp_path / "shared-queue")
    queue = TaskQueue(tmp_path / "local", registrar=registrar)
    task = queue.create("flow")
    queue.enqueue(task.task_id)
    queue.advance(task.task_id, "派发")
    queue.advance(task.task_id, "执行")
    assert f"| UltimaAgent | {task.task_id} | executing |" in global_path.read_text(encoding="utf-8")

    queue.advance(task.task_id, "自检")
    queue.advance(task.task_id, "审计")
    assert f"| UltimaAgent | {task.task_id} | audit |" in global_path.read_text(encoding="utf-8")

    queue.complete(task.task_id, {"ok": True})
    text = global_path.read_text(encoding="utf-8")
    assert f"| UltimaAgent | {task.task_id} | frozen |" in text
    assert "| UltimaAgent | 1 | 0 | 0 | 0 | 0 | 1 |" in text


def test_registrar_rejects_path_outside_authorized_queue_root(tmp_path):
    allowed = tmp_path / "shared-queue"
    outside = tmp_path / "outside" / "global-queue-index.md"

    with pytest.raises(OrchestratorError, match="路径越界"):
        GlobalQueueRegistrar(outside, allowed_root=allowed)


def test_missing_global_table_warns_without_blocking_task_state(tmp_path, caplog):
    allowed = tmp_path / "shared-queue"
    registrar = GlobalQueueRegistrar(allowed / "missing.md", allowed_root=allowed)
    queue = TaskQueue(tmp_path / "local", registrar=registrar)
    task = queue.create("warning")

    queue.enqueue(task.task_id)

    assert task.phase == "排队"
    assert "全局队列主表写回失败" in caplog.text


def test_global_fourth_executing_task_is_rejected(tmp_path):
    table = table_with_items(
        "| UltimaConsole | wo-console-1 | executing | fixture |",
        "| UltimaSentinel | wo-sentinel-1 | executing | fixture |",
        "| UltimaAdmin | wo-admin-1 | executing | fixture |",
    )
    registrar, _ = make_registrar(tmp_path / "shared-queue", table)
    queue = TaskQueue(tmp_path / "local", registrar=registrar)
    task = queue.create("fourth")

    with pytest.raises(OrchestratorError, match="全项目执行中已达上限 3"):
        queue.enqueue(task.task_id)
    assert task.phase == "立项"


def test_second_executing_task_in_same_project_is_rejected(tmp_path):
    table = table_with_items(
        "| UltimaAgent | wo-ultimaagent-20261029-0999 | executing | fixture |",
    )
    registrar, _ = make_registrar(tmp_path / "shared-queue", table)
    queue = TaskQueue(tmp_path / "local", registrar=registrar)
    task = queue.create("second")

    result = queue.check_wip(task.task_id, "执行")

    assert result == {
        "allowed": False,
        "reason": "UltimaAgent 执行中已达上限 1",
        "current_executing": 1,
        "max_executing": 1,
    }
    with pytest.raises(OrchestratorError, match="UltimaAgent 执行中已达上限 1"):
        queue.enqueue(task.task_id)


def test_second_global_audit_is_rejected(tmp_path):
    table = table_with_items(
        "| UltimaConsole | wo-console-audit | audit | fixture |",
    )
    registrar, _ = make_registrar(tmp_path / "shared-queue", table)
    queue = TaskQueue(tmp_path / "local", registrar=registrar)
    task = queue.create("audit")
    queue.enqueue(task.task_id)
    queue.advance(task.task_id, "派发")
    queue.advance(task.task_id, "执行")
    queue.advance(task.task_id, "自检")

    with pytest.raises(OrchestratorError, match="全项目审计中已达上限 1"):
        queue.advance(task.task_id, "审计")
    assert task.phase == "自检"


def test_wip_allows_task_below_limits(tmp_path):
    table = table_with_items(
        "| UltimaConsole | wo-console-1 | executing | fixture |",
    )
    registrar, _ = make_registrar(tmp_path / "shared-queue", table)
    queue = TaskQueue(tmp_path / "local", registrar=registrar)
    task = queue.create("allowed")

    result = queue.check_wip(task.task_id, "执行")

    assert result == {
        "allowed": True,
        "reason": "WIP 容量可用",
        "current_executing": 1,
        "max_executing": 3,
    }
