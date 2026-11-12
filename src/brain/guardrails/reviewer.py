"""独立复核框架（s3-audit-trail · ACCEPT-3）。

对齐 sequencing §3「审计（独立视角，dev 不自证清白）」：
- 复核角色固定 eng.audit / eng.security，开发执行器（dev）实例化被拒；
- 结论分级 blocker / major / minor；
- gate：blocker 存在 → 不进入交付门（FAIL）；清零 → 通过（PASS，可携带观察项）。
"""

from __future__ import annotations

import json
import re
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable

AUDIT_ROLES = ("eng.audit", "eng.security")
SEVERITIES = ("blocker", "major", "minor")


@dataclass
class Finding:
    role: str
    severity: str
    item: str
    detail: str = ""

    def as_dict(self) -> dict[str, str]:
        return {"role": self.role, "severity": self.severity, "item": self.item, "detail": self.detail}


@dataclass
class ReviewResult:
    ok: bool
    role: str
    findings: list[Finding] = field(default_factory=list)
    checked: list[str] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "role": self.role,
            "blocker": sum(1 for f in self.findings if f.severity == "blocker"),
            "major": sum(1 for f in self.findings if f.severity == "major"),
            "minor": sum(1 for f in self.findings if f.severity == "minor"),
            "checked": self.checked,
            "findings": [f.as_dict() for f in self.findings],
        }


class ReviewError(Exception):
    """复核框架使用错误（角色越权等）。"""


class IndependentReviewer:
    """独立复核器：只有审计/安全角色可创建，blocker 清零才过交付门。"""

    def __init__(self, role: str) -> None:
        if role not in AUDIT_ROLES:
            raise ReviewError(f"独立复核仅限 {AUDIT_ROLES}，收到: {role}")
        self.role = role
        self.findings: list[Finding] = []
        self.checked: list[str] = []

    # -- 结论登记 -----------------------------------------------------------

    def add_finding(self, severity: str, item: str, detail: str = "") -> None:
        if severity not in SEVERITIES:
            raise ReviewError(f"结论分级仅限 {SEVERITIES}，收到: {severity}")
        self.findings.append(Finding(self.role, severity, item, detail))

    # -- 内置检查 -----------------------------------------------------------

    def check_files_exist(self, paths: list[str | Path], base: str | Path | None = None) -> None:
        """清单文件存在性检查（缺文件=blocker）。"""
        base_path = Path(base) if base else None
        for p in paths:
            resolved = Path(p)
            if not resolved.is_absolute() and base_path:
                resolved = base_path / resolved
            if not resolved.exists():
                self.add_finding("blocker", f"file-exists:{p}", "文件不存在")
            else:
                self.checked.append(f"file-exists:{p}")

    def check_no_plaintext(self, files: list[str | Path], patterns: list[str],
                           base: str | Path | None = None) -> None:
        """明文泄露扫描：命中敏感模式=blocker（对齐 security-spec 脱敏纪律）。"""
        base_path = Path(base) if base else None
        for p in files:
            resolved = Path(p)
            if not resolved.is_absolute() and base_path:
                resolved = base_path / resolved
            if not resolved.exists():
                continue
            text = resolved.read_text(encoding="utf-8", errors="ignore")
            for pat in patterns:
                if re.search(pat, text, re.IGNORECASE):
                    self.add_finding("blocker", f"plaintext:{p}", f"命中敏感模式 {pat}")
            self.checked.append(f"no-plaintext:{p}")

    def check_json_valid(self, files: list[str | Path], base: str | Path | None = None) -> None:
        base_path = Path(base) if base else None
        for p in files:
            resolved = Path(p)
            if not resolved.is_absolute() and base_path:
                resolved = base_path / resolved
            if not resolved.exists():
                continue
            try:
                json.loads(resolved.read_text(encoding="utf-8-sig"))
                self.checked.append(f"json-valid:{p}")
            except json.JSONDecodeError as exc:
                self.add_finding("blocker", f"json:{p}", f"非法 JSON: {exc}")

    # -- 交付门 -------------------------------------------------------------

    def gate(self) -> ReviewResult:
        """交付门：blocker > 0 → FAIL（不进交付门）；清零 → PASS（观察项随附）。"""
        blockers = [f for f in self.findings if f.severity == "blocker"]
        return ReviewResult(not blockers, self.role, self.findings, self.checked)
