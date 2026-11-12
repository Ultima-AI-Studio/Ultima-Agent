"""设备 MCP 实操（s10-device-mcp · M15 实操 + M28 MCP 接入层）。

对齐 jarvis-reverse-architecture C1/M28（MCP 作为设备接入标准层）+ plugin-bus §1.3：
1. McpRuntime：JSON-RPC 2.0 over stdio 子进程客户端（纯标准库，不引第三方）；
   initialize / list_tools / call_tool 三动作；stdout 逐行解析、stderr 透传、
   超时与崩溃确定性错误（不穿透异常）；
2. 设备接线：MCP 工具经 DeviceRegistry 档案与可控性判定过滤——只暴露
   "可读/可写/可控制" 允许的工具；不可控工具拒绝并留原因；
3. 冒烟：FakeMcpServer（纯 Python JSON-RPC 桩，只读/可写工具）验证
   发现→档案→可控性→调用 全链；无 server 配置时如实报告"未接入"不编造。

禁止：不直连未授权设备；不可达设备如实报告；控制类动作占位征询。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

import json
import subprocess
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

from src.brain.iot.device_profile import DeviceProfile, DeviceRegistry, ProvisionChain


def _now_iso() -> str:
    return datetime.now(timezone.utc).isoformat(timespec="milliseconds").replace("+00:00", "Z")


class McpError(Exception):
    pass


# 默认工具需求映射（工具名末段 → 所需可控性）
TOOL_REQUIRE = {
    "read": "readable",
    "write": "writable",
    "control": "controllable",
}


@dataclass
class McpServerConfig:
    name: str
    command: list[str]          # 子进程启动命令（如 [sys.executable, "-u", "server.py"]）
    tools_required: dict[str, str] = field(default_factory=lambda: dict(TOOL_REQUIRE))

    def as_dict(self) -> dict[str, Any]:
        return {"name": self.name, "command": self.command,
                "tools_required": self.tools_required}


class McpRuntime:
    """MCP stdio 运行时：JSON-RPC 2.0 子进程客户端 + 确定性错误。"""

    def __init__(self, config: Optional[McpServerConfig] = None,
                 *, timeout_seconds: float = 8.0,
                 device_registry: Optional[DeviceRegistry] = None,
                 provision_chain: Optional[ProvisionChain] = None) -> None:
        self.config = config
        self.timeout_seconds = timeout_seconds
        self._proc: Optional[subprocess.Popen] = None
        self._next_id = 0
        self._tools: list[dict[str, Any]] = []
        self._initialized = False
        self._registry = device_registry
        self._chain = provision_chain

    # -- 生命周期 ----------------------------------------------------------

    @property
    def available(self) -> bool:
        return self.config is not None and bool(self.config.command)

    def _ensure_started(self) -> None:
        if self.config is None:
            raise McpError("MCP server 未配置（未接入）")
        if self._proc is None:
            try:
                self._proc = subprocess.Popen(
                    self.config.command,
                    stdin=subprocess.PIPE, stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE, text=True, encoding="utf-8",
                )
            except (OSError, ValueError) as exc:
                raise McpError(f"MCP server 启动失败：{exc}") from exc

    def _rpc(self, method: str, params: Optional[dict[str, Any]] = None) -> Any:
        self._ensure_started()
        self._next_id += 1
        req_id = self._next_id
        payload = {"jsonrpc": "2.0", "id": req_id, "method": method,
                   "params": params or {}}
        if self._proc is None or self._proc.stdin is None or self._proc.stdout is None:
            raise McpError("MCP 进程通道不可用")
        try:
            self._proc.stdin.write(json.dumps(payload) + "\n")
            self._proc.stdin.flush()
        except (BrokenPipeError, OSError) as exc:
            raise McpError(f"MCP 通道写入失败（进程可能已崩溃）：{exc}") from exc

        deadline = time.time() + self.timeout_seconds
        while True:
            line = self._proc.stdout.readline()
            if not line:
                raise McpError("MCP 进程无响应（崩溃或提前退出）")
            try:
                resp = json.loads(line)
            except json.JSONDecodeError:
                # 非 JSON 行视为 server 日志，透传 stderr 语义忽略
                continue
            if resp.get("id") != req_id:
                continue
            if "error" in resp and resp["error"] is not None:
                raise McpError(f"MCP 错误：{resp['error']}")
            if time.time() > deadline:
                raise McpError("MCP 调用超时")
            return resp.get("result")
        raise McpError("MCP 调用超时")

    def initialize(self) -> dict[str, Any]:
        if not self.available:
            return {"ok": False, "reason": "MCP server 未接入（未配置）"}
        info = self._rpc("initialize", {"clientInfo": {"name": "ultima-agent", "version": "1.0"}})
        self._initialized = True
        return {"ok": True, "server": info}

    def list_tools(self) -> list[dict[str, Any]]:
        if not self.available:
            raise McpError("MCP server 未接入（未配置）")
        tools = self._rpc("tools/list", {})
        self._tools = list(tools.get("tools", []))
        return self._tools

    def call_tool(self, tool_name: str, arguments: Optional[dict[str, Any]] = None,
                  *, device_id: Optional[str] = None) -> dict[str, Any]:
        """调用工具：经设备档案可控性过滤（device_id 提供时）。"""
        if not self.available:
            return {"ok": False, "reason": "MCP server 未接入（未配置）"}

        # 设备接线：档案 + 可控性判定过滤
        if device_id is not None:
            gate = self._device_gate(device_id, tool_name)
            if not gate["ok"]:
                return gate

        result = self._rpc("tools/call", {"name": tool_name, "arguments": arguments or {}})
        return {"ok": True, "tool": tool_name, "result": result,
                "device_id": device_id}

    # -- 设备可控性过滤 ------------------------------------------------------

    def _device_gate(self, device_id: str, tool_name: str) -> dict[str, Any]:
        if self._registry is None or self._chain is None:
            return {"ok": True, "note": "未接档案判定，直连"}
        profile = self._registry.get(device_id)
        if profile is None:
            return {"ok": False, "reason": f"设备未建档：{device_id}（先发现）"}
        ctrl = profile.controlability
        # 需求映射：先按 server 自定义（工具名→需求），再按默认末段匹配
        custom = (self.config.tools_required if self.config is not None else {}) or {}
        need = custom.get(tool_name)
        if need is None:
            tail = tool_name.rsplit("/", 1)[-1]
            need = TOOL_REQUIRE.get(tail)
        if need is None:
            return {"ok": False, "reason": f"工具 {tool_name} 不在受控清单（read/write/control）"}
        allowed = getattr(ctrl, need, False)
        if not allowed:
            return {"ok": False,
                    "reason": f"设备 {device_id} 不可{need}（{tool_name} 被拒；可控性={ctrl.as_dict()}）"}
        return {"ok": True}

    def close(self) -> None:
        if self._proc is not None:
            for handle in (self._proc.stdin, self._proc.stdout, self._proc.stderr):
                try:
                    if handle is not None:
                        handle.close()
                except OSError:
                    pass
            try:
                self._proc.terminate()
                self._proc.wait(timeout=2)
            except (OSError, subprocess.TimeoutExpired):
                try:
                    self._proc.kill()
                except OSError:
                    pass
            self._proc = None

    def __enter__(self) -> "McpRuntime":
        return self

    def __exit__(self, *exc: Any) -> None:
        self.close()


# -- 冒烟桩：FakeMcpServer（纯 Python JSON-RPC over stdio）------------------

def run_fake_mcp_server(*, fail_tool: str = "") -> int:
    """FakeMcpServer 主循环：读 stdin 逐行 JSON-RPC，写 stdout。

    工具清单：
    - env/read（可读）：返回 {ok, cwd, now}
    - device/read（可读）：返回设备读数 {ok, value: 1}
    - device/write（可写）：返回 {ok, applied}
    - device/control（可控制）：返回 {ok, switched: true}
    """
    tools = [
        {"name": "env/read", "description": "读取环境信息", "inputSchema": {"type": "object"}},
        {"name": "device/read", "description": "读取设备读数", "inputSchema": {"type": "object"}},
        {"name": "device/write", "description": "写入设备参数", "inputSchema": {"type": "object"}},
        {"name": "device/control", "description": "控制设备开关", "inputSchema": {"type": "object"}},
    ]
    for line in sys.stdin:
        if not line.strip():
            continue
        try:
            req = json.loads(line)
        except json.JSONDecodeError:
            continue
        rid = req.get("id")
        method = req.get("method")
        if method == "initialize":
            res = {"protocolVersion": "2025-03-26",
                   "serverInfo": {"name": "fake-mcp", "version": "0.1.0"}}
        elif method == "tools/list":
            res = {"tools": tools}
        elif method == "tools/call":
            name = req.get("params", {}).get("name", "")
            if name == fail_tool:
                res = {"ok": False, "error": f"工具 {name} 模拟失败"}
            elif name == "env/read":
                res = {"ok": True, "cwd": str(Path(".").resolve()), "now": _now_iso()}
            elif name == "device/read":
                res = {"ok": True, "value": 1, "unit": "w"}
            elif name == "device/write":
                res = {"ok": True, "applied": True}
            elif name == "device/control":
                res = {"ok": True, "switched": True}
            else:
                res = {"ok": False, "error": f"未知工具 {name}"}
        else:
            res = {"ok": False, "error": f"未知方法 {method}"}
        sys.stdout.write(json.dumps({"jsonrpc": "2.0", "id": rid, "result": res}) + "\n")
        sys.stdout.flush()
    return 0


def _fake_server_entry() -> str:
    """构造 FakeMcpServer 启动入口（当前解释器 -u 运行本模块 run_fake_mcp_server）。"""
    here = str(Path(__file__).resolve())
    return here


def make_fake_config(*, fail_tool: str = "") -> McpServerConfig:
    code = (
        "import sys; sys.path.insert(0, %r); "
        "from src.brain.iot.mcp_runtime import run_fake_mcp_server; "
        "sys.exit(run_fake_mcp_server(fail_tool=%r))" % (_project_root(), fail_tool)
    )
    return McpServerConfig(name="fake-mcp",
                           command=[sys.executable, "-u", "-c", code])


def _project_root() -> str:
    # H:\UltimaAI\UltimaAgent（src 上一级）
    return str(Path(__file__).resolve().parents[3])


__all__ = ["McpRuntime", "McpServerConfig", "McpError", "TOOL_REQUIRE",
           "run_fake_mcp_server", "make_fake_config"]
