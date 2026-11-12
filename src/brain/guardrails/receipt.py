"""回执证据校验（s3-audit-trail · ACCEPT-2）。

对齐 sequencing §3「收尾（回执+归档）」：每交付回执携带
reviewReason / stdoutText / evidence / acceptance 四字段；
本模块机检四字段完整性与证据路径存在性，防止空壳回执。
"""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

REQUIRED_FIELDS = ("reviewReason", "stdoutText", "evidence", "acceptance")
REQUIRED_TOP = ("work_order", "status")
EVIDENCE_KINDS = {"report", "manifest", "code", "config", "test", "log", "data"}


@dataclass
class ReceiptIssue:
    field: str
    problem: str

    def as_dict(self) -> dict[str, str]:
        return {"field": self.field, "problem": self.problem}


@dataclass
class ReceiptResult:
    ok: bool
    path: str
    issues: list[ReceiptIssue] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "ok": self.ok,
            "path": self.path,
            "issue_count": len(self.issues),
            "issues": [i.as_dict() for i in self.issues],
        }


class ReceiptValidator:
    """校验回执 JSON：顶层字段 + 四字段 + evidence 路径存在性（相对路径以 base 为基准）。"""

    def __init__(self, base: str | Path | None = None) -> None:
        self.base = Path(base) if base else None

    def validate(self, receipt_path: str | Path) -> ReceiptResult:
        path = Path(receipt_path)
        issues: list[ReceiptIssue] = []
        if not path.exists():
            return ReceiptResult(False, str(path), [ReceiptIssue("file", "回执文件不存在")])
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
        except json.JSONDecodeError as exc:
            return ReceiptResult(False, str(path), [ReceiptIssue("json", f"非法 JSON: {exc}")])
        if not isinstance(data, dict):
            return ReceiptResult(False, str(path), [ReceiptIssue("root", "根必须是对象")])
        for f in REQUIRED_TOP:
            if f not in data or not str(data.get(f, "")).strip():
                issues.append(ReceiptIssue(f, "缺失顶层字段"))
        for f in REQUIRED_FIELDS:
            if f not in data:
                issues.append(ReceiptIssue(f, "缺失四字段之一"))
        # evidence 逐项核对
        evidence = data.get("evidence")
        if isinstance(evidence, list):
            for idx, item in enumerate(evidence):
                if not isinstance(item, dict):
                    issues.append(ReceiptIssue(f"evidence[{idx}]", "非对象"))
                    continue
                ev_path = item.get("path", "")
                if not ev_path:
                    issues.append(ReceiptIssue(f"evidence[{idx}]", "缺 path"))
                else:
                    resolved = (self.base / ev_path) if self.base else (
                        path.parent.parent / ev_path
                    )
                    if not resolved.exists():
                        issues.append(ReceiptIssue(f"evidence[{idx}].path", f"证据不存在: {ev_path}"))
                kind = item.get("kind", "")
                if kind and kind not in EVIDENCE_KINDS:
                    issues.append(ReceiptIssue(f"evidence[{idx}].kind", f"未知 kind: {kind}"))
                if not str(item.get("summary", "")).strip():
                    issues.append(ReceiptIssue(f"evidence[{idx}].summary", "缺 summary"))
        # acceptance 逐项核对
        acceptance = data.get("acceptance")
        if isinstance(acceptance, list):
            for idx, item in enumerate(acceptance):
                if not isinstance(item, dict):
                    issues.append(ReceiptIssue(f"acceptance[{idx}]", "非对象"))
                    continue
                for f in ("id", "result", "evidence"):
                    if not str(item.get(f, "")).strip():
                        issues.append(ReceiptIssue(f"acceptance[{idx}].{f}", f"缺 {f}"))
                if item.get("result") not in ("PASS", "FAIL"):
                    issues.append(ReceiptIssue(f"acceptance[{idx}].result", "result 必须 PASS/FAIL"))
        return ReceiptResult(not issues, str(path), issues)
