"""Render deterministic review results as the unified Markdown audit report."""

from __future__ import annotations

from dataclasses import dataclass, field
from pathlib import Path

from .reviewer import ReviewResult, SEVERITIES


class AuditReportError(ValueError):
    """Raised when required report metadata is incomplete."""


@dataclass(slots=True)
class AuditEvidence:
    evidence_id: str
    path: str
    kind: str
    summary: str


@dataclass(slots=True)
class RetestRecord:
    command: str
    result: str
    evidence: str


@dataclass(slots=True)
class AuditReportData:
    work_order: str
    report_id: str
    generated_at: str
    audit_session_id: str
    source: str
    review: ReviewResult
    scope: tuple[str, ...] = field(default_factory=tuple)
    methods: tuple[str, ...] = field(default_factory=tuple)
    evidence: tuple[AuditEvidence, ...] = field(default_factory=tuple)
    retests: tuple[RetestRecord, ...] = field(default_factory=tuple)


def _cell(value: object) -> str:
    return str(value).replace("|", r"\|").replace("\r\n", "<br>").replace("\n", "<br>").replace("\r", "<br>")


def _require_text(value: object, field_name: str) -> str:
    if not isinstance(value, str) or not value.strip():
        raise AuditReportError(f"{field_name} must be non-empty text")
    return value.strip()


def _validate(data: AuditReportData) -> None:
    for name in ("work_order", "report_id", "generated_at", "audit_session_id", "source"):
        _require_text(getattr(data, name), name)
    if not isinstance(data.review, ReviewResult):
        raise AuditReportError("review must be ReviewResult")
    for index, item in enumerate(data.evidence):
        for name in ("evidence_id", "path", "kind", "summary"):
            _require_text(getattr(item, name), f"evidence[{index}].{name}")
    for index, item in enumerate(data.retests):
        for name in ("command", "result", "evidence"):
            _require_text(getattr(item, name), f"retests[{index}].{name}")


def _gate(data: AuditReportData) -> tuple[str, str]:
    if not data.review.ok:
        return "FAIL", "失败（deterministic reviewer blocker 未清零）"
    if not data.evidence:
        return "HOLD", "EVIDENCE_REQUIRED（无证据，禁止给出肯定交付结论）"
    return "PASS", "通过"


def render_audit_report(data: AuditReportData) -> str:
    """Render the seven-section report; evidence is mandatory for PASS."""
    _validate(data)
    summary = data.review.as_dict()
    gate, conclusion = _gate(data)
    lines = [
        "# 统一审计报告",
        "",
        "## 报告头元信息",
        "",
        "| 字段 | 值 |",
        "|---|---|",
        f"| work_order | {_cell(data.work_order)} |",
        f"| report_id | {_cell(data.report_id)} |",
        f"| generated_at | {_cell(data.generated_at)} |",
        f"| reviewer_role | {_cell(data.review.role)} |",
        f"| audit_session_id | {_cell(data.audit_session_id)} |",
        f"| source | {_cell(data.source)} |",
        "",
        "## 审计范围与方法",
        "",
        "### 范围",
        "",
    ]
    lines.extend(f"- {_cell(item)}" for item in data.scope)
    if not data.scope:
        lines.append("- 未声明")
    lines.extend(["", "### 方法", ""])
    lines.extend(f"- {_cell(item)}" for item in data.methods)
    if not data.methods:
        lines.append("- 未声明")

    lines.extend([
        "",
        "## 分级汇总",
        "",
        "| severity | count |",
        "|---|---:|",
    ])
    lines.extend(f"| {severity} | {summary[severity]} |" for severity in SEVERITIES)

    lines.extend([
        "",
        "## 逐项发现",
        "",
        "| # | severity | item | detail |",
        "|---:|---|---|---|",
    ])
    for index, finding in enumerate(data.review.findings, 1):
        lines.append(
            f"| {index} | {_cell(finding.severity)} | {_cell(finding.item)} | {_cell(finding.detail)} |"
        )
    if not data.review.findings:
        lines.append("| - | - | 无发现 | - |")

    lines.extend([
        "",
        "## 交付门结论",
        "",
        f"- Gate: **{gate}**",
        f"- 结论：**{conclusion}**",
        "- 交付门依据：现有 `ReviewResult.ok` 与证据索引；LLM 声明不覆盖确定性 gate。",
        "",
        "## 证据索引",
        "",
        "| evidence_id | path | kind | summary |",
        "|---|---|---|---|",
    ])
    for item in data.evidence:
        lines.append(
            f"| {_cell(item.evidence_id)} | {_cell(item.path)} | {_cell(item.kind)} | {_cell(item.summary)} |"
        )
    if not data.evidence:
        lines.append("| - | - | - | 无证据 |")

    lines.extend([
        "",
        "## 复测记录",
        "",
        "| command | result | evidence |",
        "|---|---|---|",
    ])
    for item in data.retests:
        lines.append(
            f"| {_cell(item.command)} | {_cell(item.result)} | {_cell(item.evidence)} |"
        )
    if not data.retests:
        lines.append("| - | 未复测 | - |")
    return "\n".join(lines) + "\n"


def write_audit_report(path: str | Path, data: AuditReportData) -> Path:
    """Render and write one UTF-8 Markdown report, returning its path."""
    report_path = Path(path)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.write_text(render_audit_report(data), encoding="utf-8", newline="\n")
    return report_path


__all__ = [
    "AuditEvidence",
    "AuditReportData",
    "AuditReportError",
    "RetestRecord",
    "render_audit_report",
    "write_audit_report",
]
