"""执行参数契约（TD-05 落地实现 · s4-brain-loop）。

对齐 docs/specs/execution-param-contract.md v0.1-draft：
- 同一契约两种实例化（开发时静态工单 / 运行时调用）；
- 下发带参数 + 返回带参数明细，缺任何一侧=违反标准；
- 参数基线（单一权威）：max_turns / temperature / max_tokens / output_protocol
  / tools_allowlist / permission_scope / acceptance_gate；
- 返回明细（execution_report）：model / actual_turns / tokens / trace
  / self_check / over_limits。

写域：本目录位于 H:\\UltimaAI\\UltimaAgent\\ 写域内。
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any, Optional

# ---------------------------------------------------------------------------
# 参数基线（冻结，与 docs/specs/execution-param-contract.md §2 一致）
# ---------------------------------------------------------------------------
PARAM_KEYS = (
    "max_turns",
    "temperature",
    "max_tokens",
    "output_protocol",
    "tools_allowlist",
    "permission_scope",
    "acceptance_gate",
)

OUTPUT_PROTOCOL_SEGMENTS = ("THOUGHT", "ACTION", "OBSERVE", "FINAL")

PERMISSION_SCOPES = ("cap", "dev", "cred")

REPORT_KEYS = (
    "model",
    "actual_turns",
    "tokens",
    "trace",
    "self_check",
    "over_limits",
)


@dataclass(frozen=True, slots=True)
class ExecutionParams:
    """下发到执行端（外部大模型/开发端）的完整执行参数。"""

    max_turns: int = 5
    temperature: float = 0.3
    max_tokens: int = 8192
    output_protocol: str = "THOUGHT/ACTION/OBSERVE/FINAL"
    tools_allowlist: tuple[str, ...] = ()
    permission_scope: tuple[str, ...] = ("cap", "dev")
    acceptance_gate: dict[str, Any] = field(default_factory=dict)

    def as_dict(self) -> dict[str, Any]:
        return {
            "max_turns": self.max_turns,
            "temperature": self.temperature,
            "max_tokens": self.max_tokens,
            "output_protocol": self.output_protocol,
            "tools_allowlist": list(self.tools_allowlist),
            "permission_scope": list(self.permission_scope),
            "acceptance_gate": dict(self.acceptance_gate),
        }

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "ExecutionParams":
        return cls(
            max_turns=int(data.get("max_turns", 5)),
            temperature=float(data.get("temperature", 0.3)),
            max_tokens=int(data.get("max_tokens", 8192)),
            output_protocol=str(data.get("output_protocol", "THOUGHT/ACTION/OBSERVE/FINAL")),
            tools_allowlist=tuple(data.get("tools_allowlist", ())),
            permission_scope=tuple(data.get("permission_scope", ("cap", "dev"))),
            acceptance_gate=dict(data.get("acceptance_gate", {})),
        )


# ---------------------------------------------------------------------------
# 校验（缺参 = 结构不合格 = 打回）
# ---------------------------------------------------------------------------
class ParamContractError(ValueError):
    """执行参数契约校验失败。"""


def validate_params(params: dict[str, Any]) -> list[str]:
    """下发参数完整性校验：七字段必须全部存在。返回缺失字段列表。"""
    missing = [key for key in PARAM_KEYS if key not in params]
    if "permission_scope" in params:
        bad = [s for s in params["permission_scope"] if s not in PERMISSION_SCOPES]
        if bad:
            raise ParamContractError(f"permission_scope 含非法 scope: {bad}")
    if "output_protocol" in params:
        segments = [s.strip() for s in params["output_protocol"].split("/") if s.strip()]
        unknown = [s for s in segments if s not in OUTPUT_PROTOCOL_SEGMENTS]
        if unknown:
            raise ParamContractError(f"output_protocol 含非法段: {unknown}")
    return missing


def validate_report(report: dict[str, Any]) -> list[str]:
    """返回明细完整性校验：六字段必须全部存在。返回缺失字段列表。"""
    missing = [key for key in REPORT_KEYS if key not in report]
    if "trace" in report and isinstance(report["trace"], list):
        for step in report["trace"]:
            if not isinstance(step, dict) or "segment" not in step:
                return ["trace.segment"]
    return missing
