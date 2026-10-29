"""队列编排与子代理调度（s3-orchestrator · M10/M11）。

对齐 codex-task-queue-spec + jarvis-reverse-architecture §4.2 域④：
1. 任务闭环状态机：立项→排队→派发→执行→自检→审计→回执；
2. 子代理权限继承受控：子任务权限必须是主任务权限子集，越权拒绝；
3. 失败重规划：触发+留痕（有预算上限）；
4. 队列视图与宿主端一致（task_id/state/priority 只读视图）；
5. 7 环范式前置检查串接（复用 L10 ParadigmGate，不另造体系）。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import logging
import os
import re
from collections import Counter, defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timedelta, timezone
from pathlib import Path
from typing import Any, Optional

try:
    from ..events import emit_event
except ImportError:  # pragma: no cover - 顶层 orchestration 的既有兼容入口
    from events import emit_event
from ..guardrails.paradigm import ParadigmGate, FLOW_RINGS

PHASES = ("立项", "排队", "派发", "执行", "自检", "审计", "回执")
SHANGHAI_TZ = timezone(timedelta(hours=8))
PROJECT_KEY_RE = re.compile(r"^[a-z]+$")
DEFAULT_GLOBAL_QUEUE_PATH = Path(r"H:\UltimaAI\_shared\queue\global-queue-index.md")
QUEUE_STATES = ("frozen", "pending", "executing", "audit", "blocked", "cancelled")
LOGGER = logging.getLogger(__name__)


def _emit_safely(event_type: str, data: dict[str, Any]) -> None:
    try:
        emit_event(event_type, data)
    except Exception as exc:  # noqa: BLE001 - 可观测性不得阻断队列流转
        LOGGER.warning("event emission failed: %s", exc)


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


def _shanghai_date() -> str:
    return datetime.now(SHANGHAI_TZ).strftime("%Y%m%d")


class OrchestratorError(Exception):
    """编排拒绝。"""


class GlobalQueueRegistrar:
    """全局队列主表的单一写回入口。"""

    def __init__(
        self,
        path: str | Path = DEFAULT_GLOBAL_QUEUE_PATH,
        *,
        allowed_root: str | Path | None = None,
    ) -> None:
        self.path = Path(path).resolve()
        root = Path(allowed_root).resolve() if allowed_root is not None else DEFAULT_GLOBAL_QUEUE_PATH.parent.resolve()
        if self.path != root and root not in self.path.parents:
            raise OrchestratorError(f"全局主表路径越界 {self.path}")
        self.allowed_root = root

    @staticmethod
    def project_name(project_key: str) -> str:
        if project_key.startswith("ultima"):
            return "Ultima" + project_key[len("ultima"):].capitalize()
        return project_key.capitalize()

    @staticmethod
    def state_for_phase(phase: str) -> str:
        if phase in ("排队", "派发"):
            return "pending"
        if phase in ("执行", "自检"):
            return "executing"
        if phase in ("审计", "回执"):
            return "audit"
        if phase == "冻结":
            return "frozen"
        raise OrchestratorError(f"不支持的全局登记阶段 {phase}")

    def _read_text(self) -> str:
        return self.path.read_text(encoding="utf-8-sig")

    @staticmethod
    def _item_lines(text: str) -> tuple[str, str, str]:
        begin, end = "<!-- queue-items:start -->", "<!-- queue-items:end -->"
        if begin not in text or end not in text:
            raise OrchestratorError("全局主表缺少 queue-items 边界标记")
        before, rest = text.split(begin, 1)
        body, after = rest.split(end, 1)
        return before + begin, body, end + after

    @staticmethod
    def _parse_items(body: str) -> list[tuple[str, str, str, str]]:
        items = []
        for line in body.splitlines():
            if not line.startswith("| Ultima"):
                continue
            cells = [cell.strip() for cell in line.strip("|").split("|")]
            if len(cells) == 4 and cells[2] in QUEUE_STATES:
                items.append((cells[0], cells[1], cells[2], cells[3]))
        return items

    @staticmethod
    def _replace_summary(text: str, items: list[tuple[str, str, str, str]]) -> str:
        begin, end = "<!-- queue-summary:start -->", "<!-- queue-summary:end -->"
        if begin not in text or end not in text:
            raise OrchestratorError("全局主表缺少 queue-summary 边界标记")
        project_order = list(dict.fromkeys(project for project, *_ in items))
        grouped: dict[str, Counter[str]] = defaultdict(Counter)
        for project, _, state, _ in items:
            grouped[project][state] += 1
        rows = [
            "| 项目 | 工单数 | 待派发 | 登记执行中 | 待审计 | 阻塞 | 已完成/闭环 |",
            "|---|---|---|---|---|---|---|",
        ]
        for project in project_order + ["合计"]:
            counts = Counter(state for _, _, state, _ in items) if project == "合计" else grouped[project]
            total = sum(counts.values())
            rows.append(
                f"| {project} | {total} | {counts['pending']} | {counts['executing']} | "
                f"{counts['audit']} | {counts['blocked']} | {counts['frozen']} |"
            )
        before, rest = text.split(begin, 1)
        _, after = rest.split(end, 1)
        return before + begin + "\n" + "\n".join(rows) + "\n" + end + after

    def record(self, task: "TaskRecord", phase: str, note: str = "运行时状态聚合") -> bool:
        state = self.state_for_phase(phase)
        project = self.project_name(task.project_key)
        try:
            text = self._read_text()
            before, body, after = self._item_lines(text)
            items = self._parse_items(body)
            replacement = f"| {project} | {task.task_id} | {state} | {note} |"
            lines = body.splitlines()
            found = False
            for index, line in enumerate(lines):
                cells = [cell.strip() for cell in line.strip("|").split("|")]
                if len(cells) == 4 and cells[0] == project and cells[1] == task.task_id:
                    lines[index] = replacement
                    found = True
                    break
            if not found:
                while lines and not lines[-1].strip():
                    lines.pop()
                lines.append(replacement)
            updated = before + "\n" + "\n".join(lines) + "\n" + after
            updated_body = self._item_lines(updated)[1]
            updated = self._replace_summary(updated, self._parse_items(updated_body))
            self.path.write_text(updated, encoding="utf-8")
            return True
        except (OSError, OrchestratorError) as exc:
            LOGGER.warning("全局队列主表写回失败 %s: %s", self.path, exc)
            return False

    def check_wip(
        self,
        project_key: str,
        target_phase: str,
        *,
        task_id: str | None = None,
    ) -> dict[str, Any]:
        project = self.project_name(project_key)
        maximum = 1 if target_phase == "审计" else 3
        try:
            body = self._item_lines(self._read_text())[1]
            items = [item for item in self._parse_items(body) if item[1] != task_id]
        except (OSError, OrchestratorError) as exc:
            LOGGER.warning("全局 WIP 容量读取失败 %s: %s", self.path, exc)
            return {
                "allowed": True,
                "reason": "全局主表暂不可用，WIP 检查 fail-open",
                "current_executing": 0,
                "max_executing": maximum,
            }

        global_executing = sum(state == "executing" for _, _, state, _ in items)
        project_executing = sum(
            item_project == project and state == "executing"
            for item_project, _, state, _ in items
        )
        global_audit = sum(state == "audit" for _, _, state, _ in items)
        if target_phase == "审计":
            allowed = global_audit < 1
            reason = "审计 WIP 可用" if allowed else "全项目审计中已达上限 1"
            return {
                "allowed": allowed,
                "reason": reason,
                "current_executing": global_audit,
                "max_executing": 1,
            }
        if global_executing >= 3:
            return {
                "allowed": False,
                "reason": "全项目执行中已达上限 3",
                "current_executing": global_executing,
                "max_executing": 3,
            }
        if project_executing >= 1:
            return {
                "allowed": False,
                "reason": f"{project} 执行中已达上限 1",
                "current_executing": project_executing,
                "max_executing": 1,
            }
        return {
            "allowed": True,
            "reason": "WIP 容量可用",
            "current_executing": global_executing,
            "max_executing": 3,
        }


@dataclass
class TaskRecord:
    task_id: str
    title: str
    phase: str = "立项"
    priority: int = 0
    permissions: tuple[str, ...] = ()
    parent_task: Optional[str] = None
    created_at: str = field(default_factory=_now_iso)
    updated_at: str = field(default_factory=_now_iso)
    replan_count: int = 0
    history: list[dict[str, Any]] = field(default_factory=list)
    receipt: Optional[dict[str, Any]] = None
    project_key: str = "ultimaagent"

    def as_dict(self) -> dict[str, Any]:
        return {
            "task_id": self.task_id, "title": self.title, "phase": self.phase,
            "priority": self.priority, "permissions": list(self.permissions),
            "parent_task": self.parent_task, "created_at": self.created_at,
            "updated_at": self.updated_at, "replan_count": self.replan_count,
            "history": self.history, "receipt": self.receipt,
            "project_key": self.project_key,
        }


class TaskQueue:
    """任务队列：闭环状态机 + 视图。"""

    def __init__(self, data_dir: str | Path, *, registrar: Optional[GlobalQueueRegistrar] = None) -> None:
        self.data_dir = Path(data_dir)
        self.queue_path = self.data_dir / "task-queue.json"
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._tasks: dict[str, TaskRecord] = {}
        self.registrar = registrar
        self._load()

    def _load(self) -> None:
        if self.queue_path.exists():
            try:
                data = json.loads(self.queue_path.read_text(encoding="utf-8"))
                for tid, obj in data.items():
                    self._tasks[tid] = TaskRecord(**obj)
            except (json.JSONDecodeError, TypeError):
                pass

    def _save(self) -> None:
        self.queue_path.write_text(
            json.dumps({k: v.as_dict() for k, v in self._tasks.items()},
                       ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    def _touch(self, rec: TaskRecord) -> None:
        rec.updated_at = _now_iso()
        self._save()

    # -- 立项/排队 ----------------------------------------------------------

    def create(
        self,
        title: str,
        *,
        priority: int = 0,
        permissions: tuple[str, ...] = (),
        parent_task: Optional[str] = None,
        project_key: str = "ultimaagent",
    ) -> TaskRecord:
        if not PROJECT_KEY_RE.fullmatch(project_key):
            raise OrchestratorError(f"非法 project_key {project_key!r}")
        lock_path = self.queue_path.with_suffix(".numbering.lock")
        try:
            lock_fd = os.open(lock_path, os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        except FileExistsError as exc:
            raise OrchestratorError("工单编号核发冲突：另一个进程正在抢号") from exc
        try:
            os.close(lock_fd)
            self._load()
            registered_date = _shanghai_date()
            prefix = f"wo-{project_key}-{registered_date}-"
            used = []
            for task_id in self._tasks:
                if task_id.startswith(prefix) and task_id[len(prefix):].isdigit():
                    used.append(int(task_id[len(prefix):]))
            sequence = max(used, default=0) + 1
            if sequence > 9999:
                raise OrchestratorError(f"工单编号已耗尽 {prefix}NNNN")
            task_id = f"{prefix}{sequence:04d}"
            if task_id in self._tasks:
                raise OrchestratorError(f"工单编号核发冲突 {task_id}")
            rec = TaskRecord(
                task_id=task_id,
                title=title,
                phase="立项",
                priority=priority,
                permissions=permissions,
                parent_task=parent_task,
                project_key=project_key,
            )
            rec.history.append({"ts": _now_iso(), "phase": "立项", "note": "任务登记"})
            self._tasks[rec.task_id] = rec
            self._save()
            return rec
        finally:
            lock_path.unlink(missing_ok=True)

    def enqueue(self, task_id: str) -> None:
        rec = self._require(task_id)
        self._assert_wip(rec, "排队")
        rec.phase = "排队"
        rec.history.append({"ts": _now_iso(), "phase": "排队"})
        self._touch(rec)
        self._register(rec, "排队")

    def advance(self, task_id: str, phase: str) -> None:
        if phase not in PHASES:
            raise OrchestratorError(f"非法阶段 {phase}")
        rec = self._require(task_id)
        expected = PHASES[PHASES.index(rec.phase) + 1] if PHASES.index(rec.phase) + 1 < len(PHASES) else None
        if phase != expected:
            raise OrchestratorError(f"阶段跳迁：{rec.phase} → {phase}（应为 {expected}）")
        if phase in ("派发", "执行", "审计"):
            self._assert_wip(rec, phase)
        rec.phase = phase
        rec.history.append({"ts": _now_iso(), "phase": phase})
        self._touch(rec)
        self._register(rec, phase)
        _emit_safely("task_advance", rec.as_dict())

    def _register(self, rec: TaskRecord, phase: str) -> None:
        if self.registrar is not None:
            self.registrar.record(rec, phase)

    def check_wip(self, task_id: str, target_phase: str) -> dict[str, Any]:
        rec = self._require(task_id)
        if self.registrar is None:
            maximum = 1 if target_phase == "审计" else 3
            return {
                "allowed": True,
                "reason": "未配置全局主表，WIP 检查 fail-open",
                "current_executing": 0,
                "max_executing": maximum,
            }
        return self.registrar.check_wip(
            rec.project_key,
            target_phase,
            task_id=rec.task_id,
        )

    def _assert_wip(self, rec: TaskRecord, target_phase: str) -> None:
        result = self.check_wip(rec.task_id, target_phase)
        if not result["allowed"]:
            raise OrchestratorError(result["reason"])

    def _require(self, task_id: str) -> TaskRecord:
        rec = self._tasks.get(task_id)
        if rec is None:
            raise OrchestratorError(f"任务不存在 {task_id}")
        return rec

    # -- 子代理权限继承 -----------------------------------------------------

    def dispatch_subtask(
        self,
        parent_task_id: str,
        title: str,
        permissions: tuple[str, ...],
    ) -> TaskRecord:
        """派发子任务：权限必须是主任务权限子集，越权拒绝。"""
        parent = self._require(parent_task_id)
        inherited = set(permissions)
        parent_perm = set(parent.permissions)
        if not inherited.issubset(parent_perm):
            raise OrchestratorError(
                f"子任务越权：{sorted(inherited - parent_perm)} 超出主任务权限"
            )
        sub = self.create(title, priority=parent.priority,
                          permissions=permissions, parent_task=parent_task_id,
                          project_key=parent.project_key)
        sub.phase = "排队"
        sub.history.append({"ts": _now_iso(), "phase": "排队", "note": f"子任务派发（父 {parent_task_id}）"})
        self._save()
        return sub

    # -- 失败重规划 ---------------------------------------------------------

    def replan(self, task_id: str, note: str = "", max_replans: int = 3) -> dict[str, Any]:
        rec = self._require(task_id)
        if rec.replan_count >= max_replans:
            return {"replanned": False, "reason": f"重规划超预算（{max_replans}）", "task_id": task_id}
        rec.replan_count += 1
        rec.phase = "排队"
        rec.history.append({"ts": _now_iso(), "phase": "排队", "note": f"失败重规划[{rec.replan_count}]: {note}"})
        self._touch(rec)
        self._register(rec, "排队")
        return {"replanned": True, "replan_count": rec.replan_count, "task_id": task_id}

    # -- 回执 ---------------------------------------------------------------

    def complete(self, task_id: str, receipt: dict[str, Any]) -> None:
        rec = self._require(task_id)
        rec.receipt = receipt
        rec.phase = "回执"
        rec.history.append({"ts": _now_iso(), "phase": "回执", "note": "回执落盘"})
        self._touch(rec)
        self._register(rec, "冻结")

    # -- 视图 ---------------------------------------------------------------

    def view(self) -> list[dict[str, Any]]:
        """队列视图（宿主端一致）：task_id/state/priority/title。"""
        rows = []
        for rec in self._tasks.values():
            rows.append({
                "task_id": rec.task_id, "state": rec.phase, "priority": rec.priority,
                "title": rec.title, "parent_task": rec.parent_task,
            })
        rows.sort(key=lambda r: (-r["priority"], r["task_id"]))
        return rows


class SevenRingCheck:
    """7 环范式前置检查串接（复用 L10 ParadigmGate）。"""

    def __init__(self, gate: Optional[ParadigmGate] = None) -> None:
        self._gate = gate or ParadigmGate()

    def pre_dispatch(self, task_id: str, target: str) -> dict[str, Any]:
        decision = self._gate.assert_complete(task_id, target=target)
        return {"allowed": decision.allowed, "completed": decision.completed,
                "missing": None if decision.completed else FLOW_RINGS[len(decision.passed_rings)]}


__all__ = [
    "TaskQueue", "TaskRecord", "GlobalQueueRegistrar", "OrchestratorError",
    "SevenRingCheck", "PHASES",
]
