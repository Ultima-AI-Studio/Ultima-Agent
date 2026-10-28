"""s1-remote-update-trigger 三触发 + 更新状态机（T2 · RU-05~RU-08）。

- 启动自检（RU-05）：启动时查 latest，有新版按策略提示/静默更新。
- 手动检查（RU-06）：设置页"检查更新"按钮触发。
- 静默强制（RU-07）：服务端 force_update=true 且版本更高 → 无条件后台更新。
- 更新 UI（RU-08）：状态（空闲/检查中/下载中/可更新/更新中/完成/失败）展示。
全程零弹窗（N7）；查询失败/无网络静默降级（N6：不打扰、记日志、不误报新版）。
"""
from __future__ import annotations

import json
import logging
import time
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

from .channel import UpdateChannel, UpdateInfo, UpdateResult

logger = logging.getLogger("ultima.update.triggers")

# 状态机（RU-08 UI 展示用）
IDLE = "idle"
CHECKING = "checking"
DOWNLOADING = "downloading"
AVAILABLE = "available"
UPDATING = "updating"
UPDATED = "updated"
FAILED = "failed"


@dataclass
class UpdateState:
    status: str = IDLE
    current_version: str | None = None
    target_version: str | None = None
    force: bool = False
    error: str | None = None
    last_checked_at: float | None = None
    events: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "status": self.status,
            "current_version": self.current_version,
            "target_version": self.target_version,
            "force": self.force,
            "error": self.error,
            "last_checked_at": self.last_checked_at,
        }


class UpdateTriggerEngine:
    """三触发引擎：统一收敛到 check/apply，按 force 位决定是否静默强制。"""

    def __init__(
        self,
        channel: UpdateChannel,
        *,
        current_version_provider: Callable[[], str],
        target_path: Path,
        state_file: Path,
        launcher_args: list[str] | None = None,
        on_event: Callable[[str], None] | None = None,
    ) -> None:
        self.channel = channel
        self.current_version_provider = current_version_provider
        self.target_path = target_path
        self.state_file = state_file
        self.launcher_args = launcher_args
        self.on_event = on_event or (lambda _msg: None)
        self.state = self._load_state()

    # ---------- 状态持久化（供 UI 读取） ----------
    def _load_state(self) -> UpdateState:
        st = UpdateState()
        if self.state_file.is_file():
            try:
                data = json.loads(self.state_file.read_text(encoding="utf-8"))
                st.status = data.get("status", IDLE)
                st.current_version = data.get("current_version")
                st.target_version = data.get("target_version")
                st.force = data.get("force", False)
                st.error = data.get("error")
                st.last_checked_at = data.get("last_checked_at")
            except (json.JSONDecodeError, OSError):
                pass
        return st

    def _save_state(self) -> None:
        self.state_file.parent.mkdir(parents=True, exist_ok=True)
        self.state_file.write_text(
            json.dumps(self.state.to_dict(), ensure_ascii=False, indent=2) + "\n",
            encoding="utf-8",
        )

    def _safe_check(self, current: str) -> UpdateInfo | None:
        """查询失败兜底：引擎层不因通道异常中断（N6 静默降级）。"""
        try:
            return self.channel.check_for_update(current)
        except Exception as exc:  # noqa: BLE001
            logger.info("update check failed silently: %s", exc)
            self._log(f"check failed (silent): {exc}")
            return None

    def _log(self, event: str) -> None:
        logger.info("update event: %s", event)
        self.state.events.append(event)
        self.state.events = self.state.events[-50:]
        self.on_event(event)

    # ---------- RU-05 启动自检 ----------
    def startup_check(self) -> UpdateResult | None:
        """启动时调用：查 latest。有新版 → force 则立即更新，否则标记 AVAILABLE。"""
        current = self.current_version_provider()
        self.state.current_version = current
        self.state.status = CHECKING
        self.state.error = None
        self._save_state()
        self._log(f"startup check (current={current})")

        info = self._safe_check(current)
        if info is None:
            # 无新版/失败：回到空闲，不误报（N6）
            self.state.status = IDLE
            self.state.last_checked_at = time.time()
            self._save_state()
            return None

        self.state.target_version = info.version
        self.state.force = info.force_update
        if info.force_update:
            self._log(f"force update to {info.version}")
            result = self.apply(info)
            return result

        self.state.status = AVAILABLE
        self.state.last_checked_at = time.time()
        self._save_state()
        self._log(f"update available: {info.version}")
        return None

    # ---------- RU-06 手动检查 ----------
    def manual_check(self) -> UpdateResult | None:
        """设置页"检查更新"按钮触发：与启动自检同逻辑（结果供 UI 展示）。"""
        current = self.current_version_provider()
        self.state.current_version = current
        self.state.status = CHECKING
        self.state.error = None
        self._save_state()
        self._log(f"manual check (current={current})")

        info = self._safe_check(current)
        if info is None:
            self.state.status = IDLE
            self.state.last_checked_at = time.time()
            self._save_state()
            return None

        self.state.target_version = info.version
        self.state.force = info.force_update
        if info.force_update:
            return self.apply(info)

        self.state.status = AVAILABLE
        self.state.last_checked_at = time.time()
        self._save_state()
        return None

    # ---------- RU-07 静默强制 ----------
    def apply(self, info: UpdateInfo | None = None) -> UpdateResult:
        """执行更新（强制位为 true 时无条件后台执行）。"""
        current = self.current_version_provider()
        if info is None:
            info = self._safe_check(current)
            if info is None:
                self.state.status = IDLE
                self._save_state()
                return UpdateResult(checked=True, old_version=current)

        self.state.status = UPDATING
        self._save_state()
        self._log(f"applying update: {info.version} (force={info.force_update})")

        result = self.channel.apply_update(
            info,
            target_path=self.target_path,
            current_version=current,
            launcher_args=self.launcher_args,
        )
        if result.updated:
            self.state.status = UPDATED
            self.state.current_version = info.version
            self.state.error = None
            self._log(f"updated to {info.version}")
        elif result.rolled_back:
            self.state.status = FAILED
            self.state.error = f"rolled back: {result.error}"
            self._log(self.state.error)
        else:
            self.state.status = FAILED
            self.state.error = result.error or "unknown update failure"
            self._log(self.state.error)
        self.state.last_checked_at = time.time()
        self._save_state()
        return result
