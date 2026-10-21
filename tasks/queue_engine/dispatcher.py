"""Fail-closed, idempotent, windowless task dispatcher."""

from __future__ import annotations

import ctypes
import json
import os
import subprocess
import sys
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any, Callable, Sequence

from .state_machine import QueueState, StateMachine
from .storage import QueueStorage


CREATE_NO_WINDOW = 0x08000000
DETACHED_PROCESS = 0x00000008
BACKGROUND_CREATION_FLAGS = CREATE_NO_WINDOW | DETACHED_PROCESS if os.name == "nt" else 0


@dataclass(frozen=True)
class DispatchDecision:
    dispatched: bool
    reason: str
    task_id: str
    pid: int | None = None
    run_paths: dict[str, Path] | None = None


class DispatchLock:
    """A non-blocking OS file lock; the file itself is not treated as ownership."""

    def __init__(self, path: Path) -> None:
        self.path = path
        self._stream: Any = None

    def acquire(self) -> bool:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        self._stream = self.path.open("a+b")
        self._stream.seek(0, os.SEEK_END)
        if self._stream.tell() == 0:
            self._stream.write(b"\0")
            self._stream.flush()
        self._stream.seek(0)
        try:
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._stream.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            self._stream.close()
            self._stream = None
            return False
        return True

    def release(self) -> None:
        if self._stream is None:
            return
        try:
            self._stream.seek(0)
            if os.name == "nt":
                import msvcrt

                msvcrt.locking(self._stream.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl

                fcntl.flock(self._stream.fileno(), fcntl.LOCK_UN)
        finally:
            self._stream.close()
            self._stream = None

    def __enter__(self) -> "DispatchLock":
        if not self.acquire():
            raise RuntimeError("dispatch lock is busy")
        return self

    def __exit__(self, *_: object) -> None:
        self.release()


class DispatchedProcess:
    def __init__(
        self,
        process: subprocess.Popen[bytes],
        run_paths: dict[str, Path],
        stdout_stream: Any,
        stderr_stream: Any,
        guardian: subprocess.Popen[bytes] | None = None,
    ) -> None:
        self.process = process
        self.run_paths = run_paths
        self._stdout_stream = stdout_stream
        self._stderr_stream = stderr_stream
        self.guardian = guardian

    def wait(self, timeout: float | None = None) -> int:
        exit_code = self.process.wait(timeout=timeout)
        self._stdout_stream.close()
        self._stderr_stream.close()
        if not self.run_paths['done'].stat().st_size:
            raise RuntimeError('durable supervisor terminated without a completion receipt')
        if self.guardian is not None:
            self.guardian.wait(timeout=5)
        return exit_code


def spawn_hidden(
    command: Sequence[str],
    *,
    stdout: Any = subprocess.DEVNULL,
    stderr: Any = subprocess.DEVNULL,
    cwd: str | Path | None = None,
) -> subprocess.Popen[bytes]:
    if not command or not all(isinstance(part, str) and part for part in command):
        raise ValueError("command must be a non-empty sequence of strings")
    return subprocess.Popen(
        list(command),
        cwd=str(cwd) if cwd is not None else None,
        stdin=subprocess.DEVNULL,
        stdout=stdout,
        stderr=stderr,
        shell=False,
        creationflags=BACKGROUND_CREATION_FLAGS,
        close_fds=True,
    )


def visible_window_handles(pid: int) -> list[int]:
    """Return visible top-level windows owned by pid (Windows runtime evidence)."""
    if os.name != "nt":
        return []
    handles: list[int] = []
    user32 = ctypes.windll.user32
    callback_type = ctypes.WINFUNCTYPE(ctypes.c_bool, ctypes.c_void_p, ctypes.c_void_p)

    def callback(hwnd: int, _: int) -> bool:
        process_id = ctypes.c_ulong()
        user32.GetWindowThreadProcessId(hwnd, ctypes.byref(process_id))
        if process_id.value == pid and user32.IsWindowVisible(hwnd):
            handles.append(int(hwnd))
        return True

    user32.EnumWindows(callback_type(callback), 0)
    return handles


class Dispatcher:
    def __init__(
        self,
        storage: QueueStorage,
        *,
        process_probe: Callable[[str], bool] | None = None,
        session_probe: Callable[[str], bool] | None = None,
        active_run_probe: Callable[[str], bool] | None = None,
        developer_id: str | None = None,
    ) -> None:
        self.storage = storage
        self.machine = StateMachine(storage)
        self.lock_path = storage.root / ".dispatch.lock"
        self.process_probe = process_probe or (lambda _task_id: False)
        self.session_probe = session_probe or self._session_running
        self.active_run_probe = active_run_probe or self._active_run
        self.processes: dict[int, DispatchedProcess] = {}
        self.developer_id = developer_id or f'process:{os.getpid()}:{process_identity(os.getpid())}'

    def dispatch(self, task_id: str, command: Sequence[str]) -> DispatchDecision:
        if (self.storage.root / ".pause-dispatch").exists():
            return self._wait(task_id, "暂停标记存在，只读审计不派发")

        lock = DispatchLock(self.lock_path)
        if not lock.acquire():
            return self._wait(task_id, "派发进程锁竞争：本轮按忙处理")
        try:
            busy_reason = self._idempotency_busy_reason(task_id)
            if busy_reason is not None:
                return self._wait(task_id, busy_reason)

            tasks = self.storage.load_tasks()
            task = next((item for item in tasks if item["task_id"] == task_id), None)
            if task is None:
                return DispatchDecision(False, "任务不存在", task_id)
            if task["state"] != QueueState.QUEUED.value:
                return DispatchDecision(False, f"任务当前状态不是排队中：{task['state']}", task_id)
            from .card_contract import check_version_gates
            try:
                check_version_gates(task, self.storage.root)
            except (OSError, ValueError, KeyError, TypeError, subprocess.SubprocessError) as exc:
                return self._wait(task_id, f'工单版本门未通过：{exc}')
            from .priority_deps import QueuePlanner

            dependencies_ready, dependency_reason = QueuePlanner.dependency_gate(
                task, tasks, self.machine
            )
            if not dependencies_ready:
                self.storage.save_tasks(tasks)
                return self._wait(task_id, dependency_reason)
            capacity_reason = self._capacity_reason(task, tasks)
            if capacity_reason is not None:
                return self._wait(task_id, capacity_reason)

            run_paths = self.storage.create_run_artifacts(task_id)
            run_paths["before"].write_text(
                json.dumps({**task, 'developer_id': self.developer_id}, ensure_ascii=False, indent=2) + "\n", encoding="utf-8"
            )
            stdout_stream = run_paths["out"].open("wb")
            stderr_stream = run_paths["err"].open("wb")
            run_paths['progress'].write_text(json.dumps({
                'command':list(command),'cwd':str(self.storage.root),'done':str(run_paths['done'])
            }),encoding='utf-8')
            try:
                process = spawn_hidden(
                    [sys.executable,str(Path(__file__).with_name('run_worker.py')),str(run_paths['progress'])],
                    stdout=stdout_stream,
                    stderr=stderr_stream,
                    cwd=self.storage.root,
                )
            except BaseException:
                stdout_stream.close()
                stderr_stream.close()
                raise
            run_paths["session"].write_text(
                json.dumps(
                    {"pid": process.pid, "started_at": datetime.now(UTC).isoformat(),
                     "process_identity": process_identity(process.pid)},
                    ensure_ascii=False,
                    indent=2,
                )
                + "\n",
                encoding="utf-8",
            )
            guardian = spawn_hidden([
                sys.executable, str(Path(__file__).with_name('guardian.py')),
                str(os.getpid()), str(process_identity(os.getpid())),
                str(self.storage.root / '.pause-dispatch'), str(run_paths['done'])], cwd=self.storage.root)
            updated, _ = self.machine.transition(
                task,
                QueueState.EXECUTING,
                actor="dispatcher",
                reason="通过派发闸门并启动隐藏子进程",
            )
            self.storage.save_tasks(updated if item is task else item for item in tasks)
            handle = DispatchedProcess(process, run_paths, stdout_stream, stderr_stream, guardian)
            self.processes[process.pid] = handle
            return DispatchDecision(True, "已派发", task_id, process.pid, run_paths)
        finally:
            lock.release()

    def take_process(self, pid: int) -> DispatchedProcess:
        return self.processes.pop(pid)

    def _idempotency_busy_reason(self, task_id: str) -> str | None:
        probes = (
            ("派发进程在跑", self.process_probe),
            ("执行会话在跑", self.session_probe),
            ("存在活跃 run", self.active_run_probe),
        )
        for label, probe in probes:
            try:
                if probe(task_id):
                    return f"幂等保护：{label}"
            except Exception as exc:
                return f"幂等探测失败，按忙处理：{label}：{type(exc).__name__}"
        return None

    @staticmethod
    def _capacity_reason(candidate: dict[str, Any], tasks: list[dict[str, Any]]) -> str | None:
        executing = [task for task in tasks if task["state"] == QueueState.EXECUTING.value]
        if not executing:
            return None
        group = candidate.get("parallelGroup")
        if not group:
            return "串行闸门已有执行中任务"
        if len(executing) >= 2:
            return "并行组全队列执行中任务已达 2"
        if any(task.get("parallelGroup") != group for task in executing):
            return "并行组不一致，按串行闸门等待"
        return None

    def _wait(self, task_id: str, reason: str) -> DispatchDecision:
        try:
            tasks = self.storage.load_tasks()
            task = next((item for item in tasks if item["task_id"] == task_id), None)
            if task is not None:
                self.storage.append_event(
                    task_id,
                    {
                        "ts": datetime.now(UTC).isoformat(),
                        "from": task["state"],
                        "to": task["state"],
                        "reason": reason,
                        "actor": "dispatcher",
                    },
                )
        except Exception:
            pass
        return DispatchDecision(False, reason, task_id)

    def _session_running(self, task_id: str) -> bool:
        task_run_dir = self.storage.runs_dir / task_id
        if not task_run_dir.exists():
            return False
        for path in sorted(task_run_dir.glob(f"{task_id}.*.session"), reverse=True):
            payload = json.loads(path.read_text(encoding="utf-8"))
            current = process_identity(payload['pid'])
            if current is None:
                continue
            expected = payload.get('process_identity')
            if expected is None:
                if path.with_suffix('.done').stat().st_size:
                    continue
                raise ValueError('Legacy live PID has no process creation identity')
            if current == expected:
                return True
        return False

    def _active_run(self, task_id: str) -> bool:
        task_run_dir = self.storage.runs_dir / task_id
        if not task_run_dir.exists():
            return False
        return any(path.stat().st_size == 0 for path in task_run_dir.glob(f"{task_id}.*.done"))


def guardian_parent_lost(parent_pid: int, marker_path: str | Path) -> bool:
    """Mark parent loss so a guardian can switch read-only and exit gracefully."""
    if _pid_exists(parent_pid):
        return False
    Path(marker_path).write_text(
        json.dumps(
            {"parent_pid": parent_pid, "mode": "read-only", "action": "graceful-exit"},
            ensure_ascii=False,
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )
    return True


def _pid_exists(pid: int) -> bool:
    return process_identity(pid) is not None


def process_identity(pid: int) -> str | None:
    """Use OS creation identity and liveness, never PID existence alone."""
    if not isinstance(pid, int) or pid <= 0:
        return None
    if os.name == "nt":
        from ctypes import wintypes
        kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        kernel.OpenProcess.argtypes = [wintypes.DWORD, wintypes.BOOL, wintypes.DWORD]
        kernel.OpenProcess.restype = wintypes.HANDLE
        kernel.GetProcessTimes.argtypes = [wintypes.HANDLE] + [ctypes.POINTER(wintypes.FILETIME)] * 4
        kernel.GetProcessTimes.restype = wintypes.BOOL
        kernel.GetExitCodeProcess.argtypes = [wintypes.HANDLE, ctypes.POINTER(wintypes.DWORD)]
        kernel.CloseHandle.argtypes = [wintypes.HANDLE]
        handle = kernel.OpenProcess(0x1000, False, pid)
        if not handle:
            if ctypes.get_last_error() == 87:
                return None
            raise ctypes.WinError(ctypes.get_last_error())
        try:
            code = wintypes.DWORD()
            if not kernel.GetExitCodeProcess(handle, ctypes.byref(code)):
                raise ctypes.WinError(ctypes.get_last_error())
            if code.value != 259:
                return None
            times = [wintypes.FILETIME() for _ in range(4)]
            if not kernel.GetProcessTimes(handle, *(ctypes.byref(t) for t in times)):
                raise ctypes.WinError(ctypes.get_last_error())
            return str((times[0].dwHighDateTime << 32) | times[0].dwLowDateTime)
        finally:
            kernel.CloseHandle(handle)
    try:
        fields = Path(f'/proc/{pid}/stat').read_text().rsplit(')',1)[1].split()
        return None if fields[0]=='Z' else fields[19]
    except FileNotFoundError:
        return None
