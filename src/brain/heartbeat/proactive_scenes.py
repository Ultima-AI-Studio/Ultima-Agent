"""主动调度铺开（s8-proactive-scenes · M27 场景做实）。

对齐 jarvis-reverse-architecture M27 + G6（规则巡检+历史偏差告警，不做预测性结论）：
1. 主动提醒：定时提醒条目（一次性 at / 周期 interval），到点产出"主动发声"提案；
2. 异常上报：关注异常条目（任务失败/进程异常等），规则巡检产出异常提案；
3. 与 HeartbeatTicker 衔接：Ticker 负责发声时机（空闲/抢占/预算），场景引擎负责"说什么"。

设计约束（对齐既有基线）：
- 条目 JSON 文件持久化，重启可恢复；
- 单条目单周期一次（防重复轰炸）；
- 不做预测性结论；不无限自转。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def _now_ts() -> float:
    return time.time()


class ProactiveError(Exception):
    pass


@dataclass
class ReminderEntry:
    """定时提醒条目：一次性 at_ts（epoch 秒）或周期 interval（秒）。"""
    entry_id: str
    kind: str                  # reminder
    text: str
    at_ts: Optional[float] = None     # 一次性到期时刻
    interval: Optional[float] = None  # 周期（秒），None=一次性
    last_fired_ts: Optional[float] = None
    created_at: str = field(default_factory=_now_iso)

    def as_dict(self) -> dict[str, Any]:
        return {"entry_id": self.entry_id, "kind": self.kind, "text": self.text,
                "at_ts": self.at_ts, "interval": self.interval,
                "last_fired_ts": self.last_fired_ts, "created_at": self.created_at}


@dataclass
class WatchEntry:
    """异常关注条目：规则巡检用（name + 检查函数返回 (ok, detail)）。"""
    entry_id: str
    name: str
    text: str
    check: Any                       # callable() -> tuple[bool, str]（True=正常）
    last_fired_ts: Optional[float] = None
    created_at: str = field(default_factory=_now_iso)

    def as_dict(self) -> dict[str, Any]:
        return {"entry_id": self.entry_id, "name": self.name, "text": self.text,
                "last_fired_ts": self.last_fired_ts, "created_at": self.created_at}


class ProactiveSceneEngine:
    """主动场景引擎：定时提醒 + 异常巡检 → 主动发声提案（纯内存+JSON 持久化）。"""

    def __init__(self, data_dir: str | Path) -> None:
        self.data_dir = Path(data_dir)
        self.data_dir.mkdir(parents=True, exist_ok=True)
        self._reminders: dict[str, ReminderEntry] = {}
        self._watches: dict[str, WatchEntry] = {}
        self._fired: list[dict[str, Any]] = []
        self._load()

    # -- 持久化 ----------------------------------------------------------

    def _load(self) -> None:
        p = self.data_dir / "proactive-scenes.json"
        if not p.exists():
            return
        try:
            d = json.loads(p.read_text(encoding="utf-8"))
            for e in d.get("reminders", []):
                self._reminders[e["entry_id"]] = ReminderEntry(**e)
            for e in d.get("watches", []):
                # check 为函数不可序列化：watch 重建时由调用方重新注册
                self._watches[e["entry_id"]] = WatchEntry(
                    entry_id=e["entry_id"], name=e.get("name", e["entry_id"]),
                    text=e.get("text", ""), check=None,
                    last_fired_ts=e.get("last_fired_ts"), created_at=e.get("created_at", _now_iso()))
            self._fired = d.get("fired", [])
        except (json.JSONDecodeError, TypeError, KeyError):
            pass

    def _save(self) -> None:
        (self.data_dir / "proactive-scenes.json").write_text(
            json.dumps({
                "reminders": [r.as_dict() for r in self._reminders.values()],
                "watches": [w.as_dict() for w in self._watches.values()],
                "fired": self._fired[-200:],
            }, ensure_ascii=False, indent=2),
            encoding="utf-8",
        )

    # -- 定时提醒 ----------------------------------------------------------

    def register_reminder(self, entry_id: str, text: str, *,
                          at_ts: Optional[float] = None,
                          interval: Optional[float] = None) -> None:
        if not text or not str(text).strip():
            raise ProactiveError("提醒内容不能为空")
        if at_ts is None and interval is None:
            raise ProactiveError("提醒需给出 at_ts（一次性）或 interval（周期）之一")
        if interval is not None and interval <= 0:
            raise ProactiveError("周期必须大于 0")
        self._reminders[entry_id] = ReminderEntry(
            entry_id=entry_id, kind="reminder", text=str(text).strip(),
            at_ts=at_ts, interval=interval)
        self._save()

    def cancel_reminder(self, entry_id: str) -> bool:
        removed = self._reminders.pop(entry_id, None)
        if removed is not None:
            self._save()
            return True
        return False

    # -- 异常巡检 ----------------------------------------------------------

    def register_watch(self, entry_id: str, name: str, text: str,
                       check: Any) -> None:
        if not callable(check):
            raise ProactiveError("watch 检查函数必须可调用")
        self._watches[entry_id] = WatchEntry(
            entry_id=entry_id, name=name, text=text, check=check)
        self._save()

    def cancel_watch(self, entry_id: str) -> bool:
        removed = self._watches.pop(entry_id, None)
        if removed is not None:
            self._save()
            return True
        return False

    # -- 巡检 ----------------------------------------------------------

    def collect(self, *, now_ts: Optional[float] = None,
                fire_interval_seconds: float = 300.0) -> list[dict[str, Any]]:
        """收集到期提案（防重复轰炸：单条目单周期一次）。

        fire_interval_seconds：watch 巡检防重轰炸窗口（默认 300s），
        同一异常在窗口内只上报一次；reminder 一次性到期只报一次。
        """
        now = now_ts if now_ts is not None else _now_ts()
        out: list[dict[str, Any]] = []

        # 定时提醒：一次性 at_ts 到期即报（不重复）；周期按 last_fired + interval
        for eid, r in list(self._reminders.items()):
            due = False
            if r.interval is None:
                due = (r.at_ts is not None and now >= r.at_ts and r.last_fired_ts is None)
            else:
                base = r.last_fired_ts if r.last_fired_ts is not None else (r.at_ts or 0.0)
                due = now >= base + r.interval
            if due:
                r.last_fired_ts = now
                proposal = {"kind": "reminder", "entry_id": eid, "text": r.text,
                            "at": _now_iso()}
                out.append(proposal)
                self._fired.append(proposal)

        # 异常巡检：check() 返回 (ok, detail)；异常且距上次上报超窗口才报
        for eid, w in list(self._watches.items()):
            if w.check is None:
                continue
            try:
                ok, detail = w.check()
            except Exception as exc:  # 检查函数自身异常视为异常态
                ok, detail = False, f"检查执行异常：{exc}"
            if not ok:
                last = w.last_fired_ts
                # 从未上报（None）立即报；已上报过则按防重轰炸窗口判定
                if last is None or now - last >= fire_interval_seconds:
                    w.last_fired_ts = now
                    proposal = {"kind": "watch", "entry_id": eid, "name": w.name,
                                "text": f"{w.text}（{detail}）", "at": _now_iso()}
                    out.append(proposal)
                    self._fired.append(proposal)
            else:
                w.last_fired_ts = None   # 恢复正常，解除防重轰炸窗口

        if out:
            self._save()
        return out

    def snapshot(self) -> dict[str, Any]:
        return {
            "reminders": [r.as_dict() for r in self._reminders.values()],
            "watches": [{"entry_id": w.entry_id, "name": w.name, "text": w.text,
                         "last_fired_ts": w.last_fired_ts} for w in self._watches.values()],
            "fired_count": len(self._fired),
        }


__all__ = ["ProactiveSceneEngine", "ReminderEntry", "WatchEntry", "ProactiveError"]
