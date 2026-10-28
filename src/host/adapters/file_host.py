"""Windows 宿主适配器（S13 · 现有壳零行为倒退）。

实现 HostIO / HostRenderer / HostEvents 三组抽象接口，后端复用既有契约：
- 渲染：文件 IPC（HostOrbPusher 同构：data/host/orb_command.json，seq 递增）；
- IO 文本输出：追加到 data/host/outbox.jsonl（能力层回执落盘）；
- 事件：data/host/events.json（覆盖写 + seq 递增，供征询等同步场景）。

跨平台预留：本适配器仅依赖文件系统 + 标准库，不调用 Windows API——
因此同一套适配器也可在 Linux/macOS 上以相同文件契约运行（换壳不换码）。
"""

from __future__ import annotations

import json
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class FileHostIO:
    """文件契约 IO 适配：send_text/send_voice 追加 outbox，receive_input 读 inbox。"""

    def __init__(self, host_dir: str | Path) -> None:
        self.host_dir = Path(host_dir)
        self.outbox_path = self.host_dir / "outbox.jsonl"
        self.inbox_path = self.host_dir / "inbox.jsonl"
        self.host_dir.mkdir(parents=True, exist_ok=True)

    def send_text(self, text: str) -> dict[str, Any]:
        if not text or not str(text).strip():
            raise ValueError("输出文本为空")
        row = {"kind": "text", "ts": _now_iso(), "text": str(text)}
        with self.outbox_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        return {"kind": "text", "ts": row["ts"], "outbox": str(self.outbox_path)}

    def send_voice(self, text: str, *, voice: str = "") -> dict[str, Any]:
        if not text or not str(text).strip():
            raise ValueError("播报文本为空")
        row = {"kind": "voice", "ts": _now_iso(), "text": str(text), "voice": voice}
        with self.outbox_path.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(row, ensure_ascii=False, separators=(",", ":")) + "\n")
        return dict(row, outbox=str(self.outbox_path))

    def receive_input(self) -> list[dict[str, Any]]:
        if not self.inbox_path.exists():
            return []
        out: list[dict[str, Any]] = []
        for line in self.inbox_path.read_text(encoding="utf-8").splitlines():
            if not line.strip():
                continue
            try:
                obj = json.loads(line)
            except json.JSONDecodeError:
                continue
            if isinstance(obj, dict):
                out.append(obj)
        return out


class FileHostRenderer:
    """文件契约渲染适配：render_canvas 复用 orb_command.json（HostOrbPusher 同构）。"""

    def __init__(self, host_dir: str | Path) -> None:
        self.host_dir = Path(host_dir)
        self.orb_file = self.host_dir / "orb_command.json"
        self.window_file = self.host_dir / "window_tree.json"
        self.host_dir.mkdir(parents=True, exist_ok=True)

    def _current_seq(self, path: Path) -> int:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            seq = data.get("seq")
            if isinstance(seq, int):
                return seq
        except (OSError, ValueError):
            pass
        return 0

    def render_canvas(self, command: dict[str, Any]) -> dict[str, Any]:
        if not command or not isinstance(command, dict):
            raise ValueError("渲染指令为空")
        if command.get("kind") != "orb.render":
            raise ValueError(f"仅支持 orb.render，实际 {command.get('kind')!r}")
        if not isinstance(command.get("state"), str) or not command.get("state"):
            raise ValueError("缺少 state")
        payload = dict(command)
        payload["seq"] = self._current_seq(self.orb_file) + 1
        self.orb_file.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        return payload

    def render_window(self, component_tree: dict[str, Any]) -> dict[str, Any]:
        if not component_tree or not isinstance(component_tree, dict):
            raise ValueError("组件树为空")
        payload = {"kind": "window.render", "seq": self._current_seq(self.window_file) + 1,
                   "ts": _now_iso(), "tree": component_tree}
        self.window_file.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        return payload


class FileHostEvents:
    """文件契约事件适配：poll_events 读 events.json，wait_event 阻塞轮询。"""

    def __init__(self, host_dir: str | Path) -> None:
        self.host_dir = Path(host_dir)
        self.events_file = self.host_dir / "events.json"
        self.host_dir.mkdir(parents=True, exist_ok=True)

    def _read_events(self) -> list[dict[str, Any]]:
        if not self.events_file.exists():
            return []
        try:
            data = json.loads(self.events_file.read_text(encoding="utf-8"))
            if isinstance(data, list):
                return [e for e in data if isinstance(e, dict)]
        except (OSError, ValueError):
            pass
        return []

    def poll_events(self, *, timeout_ms: int = 0) -> list[dict[str, Any]]:
        return self._read_events()

    def wait_event(self, *, timeout_ms: int = 0) -> dict[str, Any] | None:
        """阻塞轮询（间隔 50ms）；超时返回 None。timeout_ms<=0 视为不等待。"""
        import time

        deadline = None if timeout_ms <= 0 else time.time() + timeout_ms / 1000.0
        while True:
            events = self._read_events()
            if events:
                return events[0]
            if deadline is not None and time.time() >= deadline:
                return None
            time.sleep(0.05)


def build_file_host(host_dir: str | Path) -> "CompositeHost":
    """组装文件契约组合宿主（IO + 渲染 + 事件 全接入）。"""
    from ..abstraction import CompositeHost

    return CompositeHost(
        io=FileHostIO(host_dir),
        renderer=FileHostRenderer(host_dir),
        events=FileHostEvents(host_dir),
    )


__all__ = [
    "FileHostIO", "FileHostRenderer", "FileHostEvents", "build_file_host",
]
