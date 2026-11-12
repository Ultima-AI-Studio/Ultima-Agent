"""记忆写入闸门（s3-memory-base · ACCEPT-4）。

原则（对齐 ADR-008 与 security-spec 脱敏纪律）：
- 不可信内容不直接进长期记忆（declarative / procedural / 档案层）；
- 事实与建议分离标注（kind=fact | suggestion）；
- 来源分级：user 明确陈述 / tool 结果 / 总线内部 = 可信；
  外部抓取 / 模型草稿 / 网页 = 不可信，只允许进 working 暂存（pending）或拒绝；
- 敏感内容（key/凭证明文）一律拒绝入库。
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from typing import Any, Optional

TRUSTED_SOURCES = {"user", "tool", "bus.internal", "system", "engine"}
UNTRUSTED_SOURCES = {"external", "model.draft", "web", "mcp.unverified"}
LONGTERM_LAYERS = ("declarative", "procedural", "device_profile", "env_profile")

_SENSITIVE_RE = re.compile(
    r"(sk-[A-Za-z0-9]{8,}|password[\"']?\s*[:=]\s*[\"'][^\"']+"
    r"|api[_-]?key[\"']?\s*[:=]\s*[\"'][^\"']+"
    r"|secret[\"']?\s*[:=]\s*[\"'][^\"']+)",
    re.IGNORECASE,
)
_SUGGESTION_RE = re.compile(r"(建议|应该|应当|可以试试|最好|推荐|提醒|注意)", re.IGNORECASE)


@dataclass
class GateDecision:
    allow: bool                # 是否允许写入目标层
    target_layer: str          # 实际落层（不可信→working）
    kind: str                  # fact | suggestion | reflection | pending
    reason: str                # 判定理由
    sensitive: bool            # 是否命中敏感内容

    def as_dict(self) -> dict[str, Any]:
        return {
            "allow": self.allow, "target_layer": self.target_layer, "kind": self.kind,
            "reason": self.reason, "sensitive": self.sensitive,
        }


class MemoryWriteGate:
    """写入闸门：来源可信判定 + 事实/建议分离 + 敏感拦截。"""

    def assess(
        self,
        content: str,
        *,
        source: str,
        requested_layer: str,
        kind: Optional[str] = None,
    ) -> GateDecision:
        sensitive = bool(_SENSITIVE_RE.search(content))
        if sensitive:
            return GateDecision(False, "working", "pending",
                                "命中敏感模式（key/凭证明文），拒绝入库", True)
        if kind is None:
            kind = "suggestion" if _SUGGESTION_RE.search(content) else "fact"
        if source in TRUSTED_SOURCES:
            if requested_layer in LONGTERM_LAYERS:
                return GateDecision(True, requested_layer, kind, "来源可信，直入长期层", False)
            return GateDecision(True, requested_layer, kind, "来源可信，按请求层写入", False)
        if source in UNTRUSTED_SOURCES:
            if requested_layer in LONGTERM_LAYERS:
                return GateDecision(False, "working", "pending",
                                    "来源不可信，拒绝直入长期层，降级 working 暂存", False)
            return GateDecision(True, "working", "pending",
                                "来源不可信，仅限 working 暂存", False)
        return GateDecision(False, "working", "pending",
                            f"未知来源 {source}，保守拒绝长期写入", False)


__all__ = ["MemoryWriteGate", "GateDecision", "TRUSTED_SOURCES", "UNTRUSTED_SOURCES"]
