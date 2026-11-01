"""本机执行通道（s4-local-exec · M12）：桌面控制 + 闸门前置 + 只读默认。

对齐产品对齐报告缺口 N2（product-alignment-20261027）：
1. 动作分类闸门：list/read/observe 只读动作放行；write/exec/control 控制
   动作需白名单登记 + 高危征询，未授权一律拒绝（带 reason）；
2. 桌面窗口只读探测：ctypes user32 枚举顶层窗口/进程/可读属性（无第三方依赖）；
3. 进程只读通道：复用 environment_upgrade.scan_processes（Get-Process 只读）；
   控制动作默认禁用（dynamic control 注册点预留，第三方可用时才启用）；
4. 操作后重新观察接口：perform → re-observe 循环（每次动作后强制新快照）；
5. 全部动作过审计留痕（拒绝动作带 reason）。

禁止：绕过闸门执行控制动作；引入未审批第三方依赖（pywinauto 仅预留注册点）；
向 fileDomain 之外写文件。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import ctypes
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable, Optional

from ..environment_upgrade import scan_processes

READ_ACTIONS = ("list", "read", "observe")
CTRL_ACTIONS = ("write", "exec", "control")
HIGH_RISK_CTRL = {"exec", "control"}


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


@dataclass(frozen=True, slots=True)
class ExecDecision:
    """一次本机动作授权判定。"""

    allowed: bool
    action: str
    reason: str
    verdict: str = "allow"  # allow | deny

    def as_dict(self) -> dict[str, Any]:
        return {"allowed": self.allowed, "action": self.action,
                "reason": self.reason, "verdict": self.verdict}


class LocalExecChannel:
    """本机执行通道：闸门前置（只读默认）→ 动作 → 操作后重新观察 → 审计留痕。

    dynamic control 注册点：register_control(name, fn) 登记后才可执行控制动作
    （pywinauto/UIA 等第三方能力可用时在此接入；本批次默认空=控制禁用）。
    """

    def __init__(
        self,
        *,
        audit: Any = None,
        allowed_controls: Optional[set[str]] = None,
        require_confirm: bool = True,
        data_dir: Optional[str | Any] = None,
        observer: Optional[Callable[[], dict[str, Any]]] = None,
    ) -> None:
        self.audit = audit
        self.allowed_controls: set[str] = set(allowed_controls or set())
        self.require_confirm = require_confirm
        self._controls: dict[str, Callable[..., dict[str, Any]]] = {}
        self._data_dir = data_dir
        self._observer = observer

    # -- 审计 --------------------------------------------------------------

    def _audit(self, event: str, payload: dict[str, Any]) -> None:
        if self.audit is None:
            return
        try:
            self.audit.append(event, "ultima.brain.exec", payload, session_id="local-exec")
        except Exception:  # noqa: BLE001 - 审计失败不阻断通道
            pass

    # -- 动作分类与闸门 -----------------------------------------------------

    @staticmethod
    def classify(action: str) -> tuple[str, str]:
        """动作分类：read（list/read/observe）| control（write/exec/control）。"""
        act = (action or "").strip().lower()
        if not act:
            return "control", "unknown"
        if act in READ_ACTIONS:
            return "read", act
        return "control", act

    def authorize(self, action: str, *, confirmed: bool = False) -> ExecDecision:
        """闸门前置：只读放行；控制需白名单 + 征询；未授权一律拒绝。"""
        kind, act = self.classify(action)
        if kind == "read":
            return ExecDecision(True, act, "只读动作放行")
        if act not in self.allowed_controls:
            return ExecDecision(False, act, f"控制动作 '{act}' 未登记白名单，拒绝执行（只读默认）", "deny")
        if self.require_confirm and not confirmed:
            return ExecDecision(False, act, f"控制动作 '{act}' 需高危征询确认，未确认拒绝", "deny")
        if act not in self._controls:
            return ExecDecision(False, act, f"控制动作 '{act}' 已登记但未注册实现（dynamic control 预留点），拒绝执行", "deny")
        return ExecDecision(True, act, f"控制动作 '{act}' 白名单+征询通过", "allow")

    # -- 只读探测（桌面窗口 / 进程） ----------------------------------------

    def list_windows(self) -> list[dict[str, Any]]:
        """枚举可见顶层窗口：hwnd / title / pid（ctypes user32，无第三方依赖）。"""
        out: list[dict[str, Any]] = []
        try:
            user32 = ctypes.windll.user32
            wintypes = ctypes.wintypes

            @ctypes.WINFUNCTYPE(wintypes.BOOL, wintypes.HWND, wintypes.LPARAM)
            def _cb(hwnd, _lparam):  # noqa: ANN001
                if not user32.IsWindowVisible(hwnd):
                    return True
                length = user32.GetWindowTextLengthW(hwnd)
                buf = ctypes.create_unicode_buffer(max(length + 1, 1))
                user32.GetWindowTextW(hwnd, buf, length + 1)
                pid = wintypes.DWORD()
                user32.GetWindowThreadProcessId(hwnd, ctypes.byref(pid))
                out.append({
                    "hwnd": int(hwnd), "title": buf.value,
                    "pid": int(pid.value), "visible": True,
                })
                return True

            user32.EnumWindows(_cb, 0)
        except (AttributeError, OSError):  # 非 Windows 环境降级为空列表
            return []
        return out

    def list_processes(self, top_n: int = 15) -> list[dict[str, Any]]:
        """只读进程扫描（复用 environment_upgrade.scan_processes）。"""
        try:
            return [p.to_dict() if hasattr(p, "to_dict") else p.__dict__
                    for p in scan_processes(top_n=top_n)]
        except Exception as exc:  # noqa: BLE001 - 探测失败不阻断
            return [{"error": str(exc)}]

    def re_observe(self) -> dict[str, Any]:
        """操作后重新观察：强制返回新快照（动作后必调）。"""
        if self._observer is not None:
            return self._observer()
        return {
            "ts": _now_iso(),
            "window_count": len(self.list_windows()),
            "process_count": len(self.list_processes()),
            "snapshot": "fresh",
        }

    # -- dynamic control 注册点（第三方可用时接入，默认空） ------------------

    def register_control(self, name: str, fn: Callable[..., dict[str, Any]]) -> None:
        """登记控制动作实现（pywinauto/UIA 预留接线点；登记后仍需白名单+征询）。"""
        self._controls[name] = fn

    # -- 执行入口 -----------------------------------------------------------

    def perform(
        self,
        action: str,
        *,
        target: Any = None,
        confirmed: bool = False,
    ) -> dict[str, Any]:
        """闸门 → 动作 → 操作后重新观察 → 审计留痕。拒绝动作带 reason。"""
        decision = self.authorize(action, confirmed=confirmed)
        payload: dict[str, Any] = {"action": action, "target": target,
                                    "decision": decision.as_dict()}
        if not decision.allowed:
            payload["outcome"] = "denied"
            payload["reason"] = decision.reason
            self._audit("exec.denied", payload)
            return payload

        kind, act = self.classify(action)
        if kind == "read":
            if act == "list":
                result = {"windows": self.list_windows(),
                          "processes": self.list_processes()}
            elif act == "read":
                result = {"windows": self.list_windows(),
                          "target": target,
                          "processes": self.list_processes()}
            else:  # observe
                result = self.re_observe()
        else:
            fn = self._controls.get(act)
            result = fn(target) if fn is not None else {"outcome": "not-registered"}

        # 操作后重新观察（强制）
        re_obs = self.re_observe()
        payload["outcome"] = "executed"
        payload["result"] = result
        payload["re_observe"] = re_obs
        self._audit("exec.executed", payload)
        return payload


__all__ = ["LocalExecChannel", "ExecDecision", "READ_ACTIONS", "CTRL_ACTIONS"]
