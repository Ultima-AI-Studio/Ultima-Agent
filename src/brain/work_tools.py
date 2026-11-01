"""Request-scoped adapters around the SDK file tools; no standalone registry."""
from __future__ import annotations
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import dataclass, field
from pathlib import Path
import stat
import threading
import uuid
from openjarvis.core.registry import ToolRegistry
from openjarvis.core.types import ToolResult
from openjarvis.tools._stubs import BaseTool, ToolSpec
from openjarvis.tools.file_write import FileWriteTool
from openjarvis.tools.file_read import FileReadTool

WORK_TOOLS = ['calculator', 'think', 'ultima_work_file_write', 'ultima_work_file_read']

@dataclass(frozen=True)
class WorkBinding:
    root: Path
    request_id: str
    session_id: str
    task_id: str

class WorkLedger:
    def __init__(self):
        self._lock = threading.RLock()
        self._records = []

    def record(self, item):
        with self._lock:
            self._records.append(dict(item))

    def snapshot(self):
        with self._lock:
            return [dict(x) for x in self._records]

_ACTIVE = ContextVar('ultima_work_binding', default=None)

@contextmanager
def bind_work(binding, ledger):
    token = _ACTIVE.set((binding, ledger))
    try:
        yield
    finally:
        _ACTIVE.reset(token)


def checked_path(binding, value):
    if not isinstance(value, str) or not value or '\x00' in value:
        raise ValueError('A file path is required')
    path = Path(value)
    if '..' in path.parts or (':' in value and not path.is_absolute()):
        raise ValueError('Traversal or alternate stream path refused')
    if ':' in value[2:]:
        raise ValueError('Alternate stream path refused')
    raw = path if path.is_absolute() else binding.root / path
    # Inspect unresolved ancestors too: resolve alone hides junctions/symlinks.
    for part in (raw, *raw.parents):
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        if stat.S_ISLNK(info.st_mode) or getattr(info, 'st_file_attributes', 0) & 0x400:
            raise ValueError('Reparse points are not authorized')
    resolved = raw.resolve()
    if resolved == binding.root or not resolved.is_relative_to(binding.root):
        raise ValueError('Path outside this request directory')
    return resolved

class _WorkFileTool(BaseTool):
    writing = False

    def __init__(self):
        captured = _ACTIVE.get()
        self._binding, self._ledger = captured if captured else (None, None)

    @property
    def spec(self):
        sdk = FileWriteTool() if self.writing else FileReadTool()
        return ToolSpec(name=self.tool_id, description=sdk.spec.description + ' Only paths within the current work request directory are authorized. Relative paths use that directory.', parameters=sdk.spec.parameters, category='filesystem')

    def execute(self, **params):
        call_id = str(uuid.uuid4())
        record = {'call_id': call_id, 'tool_name': self.tool_id, 'success': False}
        try:
            if self._binding is None:
                raise ValueError('No trusted work binding')
            allowed = {'path', 'content', 'mode', 'create_dirs'} if self.writing else {'path', 'max_lines'}
            if set(params) - allowed:
                raise ValueError('Unknown or authority-bearing tool parameters')
            path = checked_path(self._binding, params.get('path'))
            if self.writing and params.get('mode', 'write') != 'write':
                raise ValueError('Only write mode is supported')
            sdk = FileWriteTool(allowed_dirs=[str(self._binding.root)]) if self.writing else FileReadTool(allowed_dirs=[str(self._binding.root)])
            args = dict(params, path=str(path))
            result = sdk.execute(**args)
            record.update(path=str(path), content=params.get('content'), success=bool(result.success), result=result.content,
                          request_id=self._binding.request_id, session_id=self._binding.session_id, task_id=self._binding.task_id)
            return ToolResult(tool_name=self.tool_id, success=result.success, content=result.content, metadata=dict(record))
        except Exception as exc:
            record['result'] = str(exc)
            return ToolResult(tool_name=self.tool_id, success=False, content=str(exc))
        finally:
            if self._ledger is not None:
                self._ledger.record(record)

@ToolRegistry.register('ultima_work_file_write')
class WorkWriteTool(_WorkFileTool):
    tool_id = 'ultima_work_file_write'
    writing = True

@ToolRegistry.register('ultima_work_file_read')
class WorkReadTool(_WorkFileTool):
    tool_id = 'ultima_work_file_read'
