"""Priority ordering, explicit requeue, and dependency DAG validation."""

from __future__ import annotations

from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Iterable

from .state_machine import QueueState, StateMachine
from .storage import QueueStorage, queue_transaction


class QueuePlanningError(ValueError):
    pass


class DependencyCycle(QueuePlanningError):
    def __init__(self, path: list[str]) -> None:
        self.path = path
        super().__init__("dependency cycle: " + " -> ".join(path))


class QueuePlanner:
    def __init__(self, storage: QueueStorage) -> None:
        self.storage = storage
        self.order_path = storage.queue_dir / "queue.md"

    def ordered_tasks(self, tasks: Iterable[dict[str, Any]] | None = None) -> list[dict[str, Any]]:
        records = list(tasks) if tasks is not None else self.storage.load_tasks()
        queued = [task for task in records if task["state"] == QueueState.QUEUED.value]
        persisted = self._read_order()
        rank = {task_id: position for position, task_id in enumerate(persisted)}
        fallback = len(rank)
        return sorted(
            queued,
            key=lambda task: (
                -self._priority(task),
                rank.get(task["task_id"], fallback),
                task["created_at"],
                task["task_id"],
            ),
        )

    @queue_transaction
    def adjust_priority(self, task_id: str, priority: int, *, actor: str, reason: str) -> None:
        self._validate_priority(priority)
        tasks = self.storage.load_tasks()
        task = self._task(tasks, task_id)
        self._require_queued(task)
        previous = task["priority"]
        task["priority"] = priority
        task["updated_at"] = datetime.now(UTC).isoformat()
        self.storage.append_event(
            task_id,
            self._audit_event(
                task,
                f"调整优先级 {previous} -> {priority}：{reason}",
                actor,
            ),
        )
        self.storage.save_tasks(tasks)
        self._write_order([task["task_id"] for task in self.ordered_tasks(tasks)])

    @queue_transaction
    def requeue_before(self, task_id: str, target_id: str, *, actor: str, reason: str) -> None:
        if task_id == target_id:
            raise QueuePlanningError("task cannot be requeued before itself")
        tasks = self.storage.load_tasks()
        task = self._task(tasks, task_id)
        target = self._task(tasks, target_id)
        self._require_queued(task)
        self._require_queued(target)
        task["priority"] = target["priority"]
        task["updated_at"] = datetime.now(UTC).isoformat()
        ordered_ids = [item["task_id"] for item in self.ordered_tasks(tasks)]
        ordered_ids.remove(task_id)
        ordered_ids.insert(ordered_ids.index(target_id), task_id)
        self.storage.append_event(
            task_id,
            self._audit_event(task, f"插队到 {target_id} 之前：{reason}", actor),
        )
        self.storage.save_tasks(tasks)
        self._write_order(ordered_ids)

    @queue_transaction
    def enqueue(self, task: dict[str, Any]) -> None:
        self.storage.validate_index_record(task)
        self._validate_priority(task["priority"])
        tasks = self.storage.load_tasks()
        if any(existing["task_id"] == task["task_id"] for existing in tasks):
            raise QueuePlanningError(f"duplicate task_id: {task['task_id']}")
        candidate_tasks = [*tasks, dict(task)]
        self.validate_acyclic(candidate_tasks)
        self.storage.save_tasks(candidate_tasks)
        self._write_order([item["task_id"] for item in self.ordered_tasks(candidate_tasks)])

    @staticmethod
    def validate_acyclic(tasks: Iterable[dict[str, Any]]) -> None:
        graph = {task["task_id"]: list(task.get("dependsOn", [])) for task in tasks}
        visiting: set[str] = set()
        visited: set[str] = set()
        stack: list[str] = []

        def visit(node: str) -> None:
            if node in visiting:
                start = stack.index(node)
                raise DependencyCycle([*stack[start:], node])
            if node in visited:
                return
            visiting.add(node)
            stack.append(node)
            for dependency in graph.get(node, []):
                if dependency in graph:
                    visit(dependency)
            stack.pop()
            visiting.remove(node)
            visited.add(node)

        for task_id in graph:
            visit(task_id)

    @staticmethod
    def dependency_gate(
        task: dict[str, Any], tasks: list[dict[str, Any]], machine: StateMachine
    ) -> tuple[bool, str]:
        by_id = {item["task_id"]: item for item in tasks}
        missing = [dependency for dependency in task.get("dependsOn", []) if dependency not in by_id]
        if missing:
            return False, f"依赖不存在：{missing[0]}"
        failed = [
            dependency
            for dependency in task.get("dependsOn", [])
            if by_id[dependency]["state"] in {QueueState.FAILED.value, QueueState.BLOCKED.value}
        ]
        if failed:
            machine.block_failed_dependents(tasks)
            return False, f"依赖 {failed[0]} 未完成，任务已冻结"
        waiting = [
            dependency
            for dependency in task.get("dependsOn", [])
            if by_id[dependency]["state"] != QueueState.COMPLETED.value
        ]
        if waiting:
            return False, f"等待依赖 {waiting[0]} 完成"
        return True, "依赖全部完成"

    def _read_order(self) -> list[str]:
        if not self.order_path.exists():
            return []
        order: list[str] = []
        for line in self.order_path.read_text(encoding="utf-8").splitlines():
            if line.startswith("- "):
                order.append(line[2:].strip())
        return order

    def _write_order(self, task_ids: list[str]) -> None:
        self.storage.ensure_layout()
        content = "# Runtime dispatch order\n\n" + "".join(f"- {task_id}\n" for task_id in task_ids)
        temporary = self.order_path.with_suffix(".md.tmp")
        temporary.write_text(content, encoding="utf-8", newline="\n")
        temporary.replace(self.order_path)

    @staticmethod
    def _priority(task: dict[str, Any]) -> int:
        value = task.get("priority", 50)
        QueuePlanner._validate_priority(value)
        return value

    @staticmethod
    def _validate_priority(value: Any) -> None:
        if not isinstance(value, int) or isinstance(value, bool) or not 0 <= value <= 100:
            raise QueuePlanningError(f"priority must be an integer from 0 to 100: {value!r}")

    @staticmethod
    def _task(tasks: list[dict[str, Any]], task_id: str) -> dict[str, Any]:
        try:
            return next(task for task in tasks if task["task_id"] == task_id)
        except StopIteration as exc:
            raise QueuePlanningError(f"task not found: {task_id}") from exc

    @staticmethod
    def _require_queued(task: dict[str, Any]) -> None:
        if task["state"] != QueueState.QUEUED.value:
            raise QueuePlanningError(f"only QUEUED tasks may be adjusted: {task['task_id']}")

    @staticmethod
    def _audit_event(task: dict[str, Any], reason: str, actor: str) -> dict[str, str]:
        if not actor or not reason:
            raise QueuePlanningError("actor and reason are required")
        return {
            "ts": datetime.now(UTC).isoformat(),
            "from": task["state"],
            "to": task["state"],
            "reason": reason,
            "actor": actor,
        }
