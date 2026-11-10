"""Fail-closed stage gate for independently reviewed work-order stages."""

from __future__ import annotations

import json
from dataclasses import dataclass
from pathlib import Path
from typing import Any

from .receipt import ReceiptValidator
from .reviewer import AUDIT_ROLES, SEVERITIES, Finding, ReviewResult


REVIEW_FIELDS = (
    "ok",
    "role",
    "blocker",
    "major",
    "minor",
    "checked",
    "findings",
)
REQUIRED_CHECKS = ("测试复跑", "写域核对")


@dataclass(frozen=True)
class StageGateResult:
    """Machine-readable stage decision with explicit refusal reasons."""

    passed: bool
    reasons: list[str]


def _fail(*reasons: str) -> StageGateResult:
    return StageGateResult(False, list(reasons))


def _is_count(value: Any) -> bool:
    return isinstance(value, int) and not isinstance(value, bool) and value >= 0


def check_stage(
    work_order: str,
    stage: str,
    evidence_root: str | Path,
) -> StageGateResult:
    """Allow a stage only when its independent review is complete and clean.

    Evidence paths inside ``independent-review.json`` are resolved relative to
    ``evidence_root`` so the existing :class:`ReceiptValidator` can validate
    the review receipt without introducing a second receipt format.
    """

    root = Path(evidence_root)
    review_path = root / work_order / stage / "independent-review.json"
    try:
        receipt_result = ReceiptValidator(base=root).validate(review_path)
    except (OSError, UnicodeError) as exc:
        return _fail(f"复核结论读取失败: {exc}")
    if not receipt_result.ok:
        return _fail(
            *(f"{issue.field}: {issue.problem}" for issue in receipt_result.issues)
        )

    try:
        data = json.loads(review_path.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        return _fail(f"复核结论无法解析: {exc}")
    if not isinstance(data, dict):
        return _fail("复核结论根必须是对象")

    reasons: list[str] = []
    missing = [field for field in REVIEW_FIELDS if field not in data]
    if missing:
        reasons.append(f"复核结论缺字段: {', '.join(missing)}")

    if data.get("work_order") != work_order:
        reasons.append("复核结论 work_order 与待放行工单不一致")

    role = data.get("role")
    if role not in AUDIT_ROLES:
        reasons.append(f"复核角色必须是 {AUDIT_ROLES}，收到: {role}")

    checked_value = data.get("checked")
    checked: list[str] = []
    if not isinstance(checked_value, list) or not checked_value:
        reasons.append("checked 必须是非空列表")
    elif not all(isinstance(item, str) and item.strip() for item in checked_value):
        reasons.append("checked 每项必须是非空字符串")
    else:
        checked = checked_value
        for required in REQUIRED_CHECKS:
            if not any(required in item for item in checked):
                reasons.append(f"checked 缺少{required}")

    findings_value = data.get("findings")
    findings: list[Finding] = []
    if not isinstance(findings_value, list):
        reasons.append("findings 必须是列表")
    else:
        for index, item in enumerate(findings_value):
            if not isinstance(item, dict):
                reasons.append(f"findings[{index}] 必须是对象")
                continue
            finding_role = item.get("role")
            severity = item.get("severity")
            finding_item = item.get("item")
            detail = item.get("detail", "")
            if finding_role != role:
                reasons.append(f"findings[{index}].role 与复核角色不一致")
            if severity not in SEVERITIES:
                reasons.append(f"findings[{index}].severity 非法: {severity}")
            if not isinstance(finding_item, str) or not finding_item.strip():
                reasons.append(f"findings[{index}].item 必须是非空字符串")
            if not isinstance(detail, str):
                reasons.append(f"findings[{index}].detail 必须是字符串")
            if (
                finding_role == role
                and severity in SEVERITIES
                and isinstance(finding_item, str)
                and finding_item.strip()
                and isinstance(detail, str)
            ):
                findings.append(Finding(role, severity, finding_item, detail))

    ok_value = data.get("ok")
    if not isinstance(ok_value, bool):
        reasons.append("ok 必须是布尔值")

    declared_counts: dict[str, int] = {}
    for severity in SEVERITIES:
        value = data.get(severity)
        if not _is_count(value):
            reasons.append(f"{severity} 必须是非负整数")
        else:
            declared_counts[severity] = value

    review_result = ReviewResult(
        ok=ok_value if isinstance(ok_value, bool) else False,
        role=role if isinstance(role, str) else "",
        findings=findings,
        checked=checked,
    )
    computed = review_result.as_dict()
    for severity, declared in declared_counts.items():
        if declared != computed[severity]:
            reasons.append(
                f"{severity} 计数与 ReviewResult 不一致: "
                f"声明 {declared}，计算 {computed[severity]}"
            )

    if computed["blocker"] > 0 or declared_counts.get("blocker", 0) > 0:
        reasons.append("blocker 未清零")
    expected_ok = computed["blocker"] == 0
    if isinstance(ok_value, bool) and ok_value != expected_ok:
        reasons.append("ok 与 ReviewResult 的 blocker 语义不一致")
    if ok_value is not True:
        reasons.append("独立复核结论未判定通过")

    return StageGateResult(not reasons, reasons)
