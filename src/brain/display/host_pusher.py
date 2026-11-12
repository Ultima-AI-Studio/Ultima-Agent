"""L4 A2 组合窗口上壳：brain → 壳指令落盘（orb.render 常驻事件循环输入）。

设计（对齐 product-plan L4 A2 与 HS-005 orb.render 契约）：
- brain 侧不再直接持有 WebView2 句柄；通过写域文件 IPC 推送渲染指令：
  `data/host/orb_command.json`（单文件、seq 递增、幂等覆盖最新指令）；
- 壳侧（OrbLiveRenderer）轮询该文件，seq 变化即 PostWebMessageAsString
  推给悬浮球页面（WebGL2 venom orb）；
- 指令格式 = OrbStateMachine.render_command() 扩展（追加 seq/prompt），
  页面 applyCommand 已支持 prompt 显示通道（L7 悬浮球载体成果）；
- 空指令/非法输入不落盘；写失败抛错留痕（审计用）。

写域：仅 H:\\UltimaAI\\UltimaAgent\\ 内。
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))


class HostOrbPusher:
    """向壳侧常驻悬浮球推送 orb.render 渲染指令（seq 递增 + 幂等覆盖）。"""

    def __init__(self, command_file: str | Path) -> None:
        self.command_file = Path(command_file)
        self.command_file.parent.mkdir(parents=True, exist_ok=True)

    def _current_seq(self) -> int:
        """读当前文件 seq（文件不存在/损坏按 0）。"""
        try:
            data = json.loads(self.command_file.read_text(encoding="utf-8"))
            seq = data.get("seq")
            if isinstance(seq, int):
                return seq
        except (OSError, ValueError):
            pass
        return 0

    def push(self, command: dict) -> dict:
        """推送一条 orb.render 指令（含 prompt 通道）。返回落盘后的完整指令。

        - 空/非法指令（缺 kind/state）抛 ValueError；
        - seq 自动递增（基于当前文件）；
        - 覆盖写最新指令（壳侧只消费最新状态，幂等）。
        """
        if not command or not isinstance(command, dict):
            raise ValueError("指令为空")
        if command.get("kind") != "orb.render":
            raise ValueError(f"仅支持 orb.render，实际 {command.get('kind')!r}")
        state = command.get("state")
        if not isinstance(state, str) or not state:
            raise ValueError("缺少 state")

        payload = dict(command)
        payload["seq"] = self._current_seq() + 1
        # 幂等覆盖：同一 seq 重复推不递增（壳按 seq 消费）
        self.command_file.write_text(
            json.dumps(payload, ensure_ascii=False, separators=(",", ":")),
            encoding="utf-8",
        )
        return payload

    def current(self) -> dict:
        """读取当前落盘指令（壳侧同源口径）。"""
        try:
            return json.loads(self.command_file.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return {}


__all__ = ["HostOrbPusher"]
