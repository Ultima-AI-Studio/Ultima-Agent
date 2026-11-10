"""Validate ``tasks/queue/wo-*.md`` work-order cards without side effects."""

from __future__ import annotations

import argparse
from dataclasses import asdict, dataclass
import json
from pathlib import Path
import re
import sys
from typing import Any

import jsonschema


ROOT = Path(__file__).resolve().parents[1]
DEFAULT_SCHEMA = ROOT / "docs" / "specs" / "work-order.schema.json"

E_READ_ERROR = "E_READ_ERROR"
E_MISSING_SECTION = "E_MISSING_SECTION"
E_MISSING_DETAIL_FIELD = "E_MISSING_DETAIL_FIELD"
E_T_SET_MISMATCH = "E_T_SET_MISMATCH"
E_T_NUMBER_GAP = "E_T_NUMBER_GAP"
E_GATE_WEAK = "E_GATE_WEAK"
E_NO_FORBIDDEN = "E_NO_FORBIDDEN"
E_FILE_PATH_WEAK = "E_FILE_PATH_WEAK"
E_STATUS_NOT_DISPATCHABLE = "E_STATUS_NOT_DISPATCHABLE"
E_REVISION_FORMAT = "E_REVISION_FORMAT"
E_NO_PLAN_REF = "E_NO_PLAN_REF"
E_SCHEMA = "E_SCHEMA"
E_GATE_CONTRADICTION = "E_GATE_CONTRADICTION"
E_STRICT_WARNING = "E_STRICT_WARNING"
W_LEGACY_PROFILE = "W_LEGACY_PROFILE"

ALLOWED_STATUSES = {"可开工", "排队中", "待开工", "已冻结", "已完成"}
DISPATCHABLE_STATUSES = {"可开工", "排队中"}
GATE_TERMS = re.compile(
    r"pytest|命令|==|!=|差异|PASS|输出|全绿|exit|存在|一致|为空|非空|未新增|"
    r"前后|可被|定位|张数|计数|覆盖|含|grep|干净|相同|拒绝|记录|出现|≥|≤|>=|<=",
    re.IGNORECASE,
)
PATH_FEATURE = re.compile(r"[\\/]|\.(?:py|md|json)(?:\b|`)", re.IGNORECASE)

# Enumerated structural contradictions. Keep these rules narrow: each entry names
# two assertions that cannot both describe one final Gate state. The validator
# reports the conflict but never rewrites the card.
GATE_CONTRADICTION_RULES = (
    {
        "name": "porcelain-delta-count-after-commit",
        "left": re.compile(r"Compare-Object[\s\S]*?(?:恰好|恰)\s*\d+\s*条\s*`?=>", re.IGNORECASE),
        "right": re.compile(r"\bgit(?:\s+-C\s+\S+)?\s+commit\b[\s\S]*?show\s+--stat", re.IGNORECASE),
        "message": "状态差分条数断言与完成提交断言互斥：提交会从 porcelain 差分中移除已提交路径",
    },
)


@dataclass(frozen=True)
class Report:
    status: str
    card: str
    order: str
    errors: list[dict[str, Any]]
    warnings: list[dict[str, Any]]
    schema: str

    def to_dict(self) -> dict[str, Any]:
        return asdict(self)


def _issue(code: str, line: int | None, message: str) -> dict[str, Any]:
    return {"code": code, "line": line, "message": message}


def _order_from_path(path: Path) -> str:
    return path.stem.split("--", 1)[0]


def _metadata(lines: list[str], stop: int) -> tuple[dict[str, str], dict[str, int]]:
    text = "\n".join(lines[:stop])
    values: dict[str, str] = {}
    line_numbers: dict[str, int] = {}

    patterns = {
        "version": r"版本：\s*([^｜\n]+)",
        "status": r"状态：\s*([^｜（\n]+)",
        "tool": r"适用工具：\s*([^｜\n]+)",
        "link": r"链路：\s*`([^`]+)`",
        "plan_ref": r"方案依据：\s*`([^`]+)`",
        "workdir": r"工作目录锁定：\s*`([^`]+)`",
        "revision": r"锁定 revision：(?:commit\s*)?`([^`]+)`",
        "runtime": r"执行端：\s*(.+)$",
        "usage": r"用法：\s*(.+)$",
        "prereq": r"前置：\s*([^）\n]+)",
    }
    for key, pattern in patterns.items():
        flags = re.MULTILINE
        match = re.search(pattern, text, flags)
        if match:
            values[key] = match.group(1).strip()
            line_numbers[key] = text[: match.start()].count("\n") + 1
    return values, line_numbers


def _section_headings(lines: list[str]) -> list[tuple[int, str]]:
    headings = []
    for index, line in enumerate(lines):
        match = re.match(r"^##\s+(.+?)\s*$", line)
        if match:
            headings.append((index, match.group(1)))
    return headings


def _section_bounds(
    headings: list[tuple[int, str]], predicate
) -> tuple[int, int] | None:
    for position, (start, heading) in enumerate(headings):
        if predicate(heading):
            end = headings[position + 1][0] if position + 1 < len(headings) else 10**9
            return start, end
    return None


def _content_items(lines: list[str], start: int, end: int) -> list[str]:
    items = []
    for line in lines[start:end]:
        value = line.strip()
        if not value or value == "---":
            continue
        value = re.sub(r"^(?:[-*]|\d+\.)\s*", "", value).strip()
        if value:
            items.append(value)
    return items


def _scope(
    lines: list[str], bounds: tuple[int, int] | None, errors: list[dict[str, Any]]
) -> tuple[list[str], list[str]]:
    if bounds is None:
        errors.append(_issue(E_MISSING_SECTION, None, "缺少范围冻结章节"))
        return [], []
    start, end = bounds
    end = min(end, len(lines))
    do_marker = None
    not_marker = None
    for index in range(start + 1, end):
        value = lines[index]
        if re.match(r"^\*\*.*只做.*\*\*", value):
            do_marker = index
        elif re.match(r"^\*\*.*(?:不做|Non-goals).*\*\*", value, re.IGNORECASE):
            not_marker = index
    if do_marker is None:
        errors.append(_issue(E_MISSING_SECTION, start + 1, "范围冻结缺少“只做”清单"))
    if not_marker is None:
        errors.append(_issue(E_NO_FORBIDDEN, start + 1, "范围冻结缺少“不做”清单"))

    scope_do = _content_items(lines, do_marker + 1, not_marker) if do_marker is not None and not_marker is not None else []
    scope_not_do = _content_items(lines, not_marker + 1, end) if not_marker is not None else []
    if not scope_not_do and not any(item["code"] == E_NO_FORBIDDEN for item in errors):
        errors.append(_issue(E_NO_FORBIDDEN, (not_marker or start) + 1, "范围冻结“不做”清单为空"))
    return scope_do, scope_not_do


def _task_table(lines: list[str], bounds: tuple[int, int] | None, errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if bounds is None:
        errors.append(_issue(E_MISSING_SECTION, None, "缺少任务清单章节"))
        return []
    start, end = bounds
    result = []
    for index in range(start + 1, min(end, len(lines))):
        line = lines[index]
        if not re.match(r"^\|\s*T\d+\s*\|", line):
            continue
        columns = [column.strip() for column in line.strip().strip("|").split("|")]
        if len(columns) >= 3:
            result.append({"id": columns[0], "files": columns[1], "gate": columns[2], "line": index + 1})
    if not result:
        errors.append(_issue(E_MISSING_SECTION, start + 1, "任务清单没有可解析的 T 行"))
    return result


def _field_name(label: str) -> str | None:
    if label == "文件":
        return "files"
    if label == "写什么":
        return "writes"
    if label.startswith("验收"):
        return "gate"
    if label == "禁止":
        return "forbidden"
    return None


def _task_details(lines: list[str], bounds: tuple[int, int] | None, errors: list[dict[str, Any]]) -> list[dict[str, Any]]:
    if bounds is None:
        errors.append(_issue(E_MISSING_SECTION, None, "缺少任务明细章节"))
        return []
    section_start, section_end = bounds
    section_end = min(section_end, len(lines))
    starts: list[tuple[int, re.Match[str]]] = []
    for index in range(section_start + 1, section_end):
        match = re.match(r"^###\s+(T\d+)\s*(?:·\s*)?(.+?)\s*$", lines[index])
        if match:
            starts.append((index, match))

    details = []
    for position, (start, match) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else section_end
        fields: dict[str, list[str]] = {}
        field_lines: dict[str, int] = {}
        markers: list[tuple[int, str, str]] = []
        for index in range(start + 1, end):
            marker = re.match(r"^\*\*(文件|写什么|验收(?:（Gate T\d+）)?|禁止)\*\*\s*[:：]?\s*(.*)$", lines[index])
            if marker:
                name = _field_name(marker.group(1))
                if name:
                    markers.append((index, name, marker.group(2).strip()))
        for marker_position, (index, name, inline) in enumerate(markers):
            content_end = markers[marker_position + 1][0] if marker_position + 1 < len(markers) else end
            content = ([inline] if inline else []) + _content_items(lines, index + 1, content_end)
            fields[name] = content
            field_lines[name] = index + 1
        task_id = match.group(1)
        for required in ("files", "writes", "gate", "forbidden"):
            if not fields.get(required):
                errors.append(
                    _issue(
                        E_MISSING_DETAIL_FIELD,
                        start + 1,
                        f"{task_id} 缺少或清空 {required} 段",
                    )
                )
                fields.setdefault(required, [])
                field_lines.setdefault(required, start + 1)
        details.append(
            {
                "id": task_id,
                "title": match.group(2).strip(),
                "line": start + 1,
                "files": fields["files"],
                "writes": fields["writes"],
                "gate": fields["gate"],
                "forbidden": fields["forbidden"],
                "field_lines": field_lines,
            }
        )
    if not details:
        errors.append(_issue(E_MISSING_SECTION, section_start + 1, "任务明细没有可解析的 T 块"))
    return details


def _gate_contradictions(lines: list[str]) -> list[dict[str, Any]]:
    """Find enumerated contradictions inside one acceptance Gate block."""

    starts: list[tuple[int, str]] = []
    for index, line in enumerate(lines):
        match = re.match(r"^\*\*验收（Gate\s+(T\d+)[^）]*）\*\*", line)
        if match:
            starts.append((index, match.group(1)))

    issues: list[dict[str, Any]] = []
    for position, (start, gate_id) in enumerate(starts):
        end = starts[position + 1][0] if position + 1 < len(starts) else len(lines)
        for index in range(start + 1, end):
            if re.match(r"^###\s+T\d+\b", lines[index]):
                end = index
                break
        block = "\n".join(lines[start:end])
        for rule in GATE_CONTRADICTION_RULES:
            if rule["left"].search(block) and rule["right"].search(block):
                issues.append(
                    _issue(
                        E_GATE_CONTRADICTION,
                        start + 1,
                        f"{gate_id} [{rule['name']}]: {rule['message']}",
                    )
                )
    return issues


def _schema_errors(document: dict[str, Any], schema: dict[str, Any], fallback_line: int | None) -> list[dict[str, Any]]:
    issues = []
    validator = jsonschema.Draft202012Validator(schema)
    for item in sorted(validator.iter_errors(document), key=lambda error: list(error.absolute_path)):
        path = ".".join(str(part) for part in item.absolute_path) or "document"
        issues.append(_issue(E_SCHEMA, fallback_line, f"schema {path}: {item.message}"))
    return issues


def _validate_structured(
    lines: list[str],
    headings: list[tuple[int, str]],
    schema: dict[str, Any],
    dispatch_status: bool,
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    errors: list[dict[str, Any]] = []
    metadata, metadata_lines = _metadata(lines, headings[0][0] if headings else len(lines))
    scope_bounds = _section_bounds(headings, lambda heading: "范围冻结" in heading)
    table_bounds = _section_bounds(headings, lambda heading: "任务清单" in heading)
    detail_bounds = _section_bounds(headings, lambda heading: "任务明细" in heading)
    scope_do, scope_not_do = _scope(lines, scope_bounds, errors)
    task_table = _task_table(lines, table_bounds, errors)
    task_details = _task_details(lines, detail_bounds, errors)

    status = metadata.get("status", "")
    if status not in ALLOWED_STATUSES or (dispatch_status and status not in DISPATCHABLE_STATUSES):
        errors.append(
            _issue(
                E_STATUS_NOT_DISPATCHABLE,
                metadata_lines.get("status"),
                f"status={status or '<missing>'} 不满足当前派发态要求",
            )
        )
    revision = metadata.get("revision", "")
    if not re.fullmatch(r"[0-9a-f]{7,40}", revision):
        errors.append(_issue(E_REVISION_FORMAT, metadata_lines.get("revision"), "revision 必须为 7-40 位小写十六进制"))
    if not metadata.get("plan_ref"):
        errors.append(_issue(E_NO_PLAN_REF, None, "缺少方案依据 plan_ref"))

    table_ids = {item["id"] for item in task_table}
    detail_ids = {item["id"] for item in task_details}
    if table_ids != detail_ids:
        only_table = sorted(table_ids - detail_ids)
        only_details = sorted(detail_ids - table_ids)
        mismatch_line = next((item["line"] for item in task_table if item["id"] in table_ids - detail_ids), None)
        errors.append(
            _issue(
                E_T_SET_MISMATCH,
                mismatch_line or (table_bounds[0] + 1 if table_bounds else None),
                f"任务集合不一致：仅清单={only_table}，仅明细={only_details}",
            )
        )
    ids = sorted(table_ids | detail_ids, key=lambda value: int(value[1:]))
    expected = [f"T{index}" for index in range(len(ids))]
    if ids != expected:
        errors.append(_issue(E_T_NUMBER_GAP, task_table[0]["line"] if task_table else None, f"T 编号应连续为 {expected}，实际为 {ids}"))

    for detail in task_details:
        for item in detail["gate"]:
            if not GATE_TERMS.search(item):
                errors.append(
                    _issue(
                        E_GATE_WEAK,
                        detail["field_lines"]["gate"],
                        f"{detail['id']} Gate 缺少可验证动词：{item}",
                    )
                )
        for item in detail["files"]:
            if not PATH_FEATURE.search(item):
                errors.append(
                    _issue(
                        E_FILE_PATH_WEAK,
                        detail["field_lines"]["files"],
                        f"{detail['id']} files 条目缺少路径特征：{item}",
                    )
                )

    document = {
        "profile": "structured-v1",
        "title": lines[0].strip() if lines else "",
        "version": metadata.get("version", ""),
        "status": status,
        "tool": metadata.get("tool", ""),
        "link": metadata.get("link", ""),
        "prereq": metadata.get("prereq", ""),
        "workdir": metadata.get("workdir", ""),
        "revision": revision,
        "usage": metadata.get("usage", ""),
        "plan_ref": metadata.get("plan_ref", ""),
        "runtime": metadata.get("runtime", ""),
        "scope_do": scope_do,
        "scope_not_do": scope_not_do,
        "task_table": task_table,
        "task_details": task_details,
    }
    errors.extend(_schema_errors(document, schema, 1))
    return errors, []


def validate(
    card_path: str | Path,
    *,
    strict: bool = False,
    schema_path: str | Path | None = None,
    dispatch_status: bool = True,
) -> Report:
    """Validate one work-order card and return a closed PASS/FAIL report."""

    card = Path(card_path)
    order = _order_from_path(card)
    schema_file = Path(schema_path) if schema_path is not None else DEFAULT_SCHEMA
    errors: list[dict[str, Any]] = []
    warnings: list[dict[str, Any]] = []
    try:
        lines = card.read_text(encoding="utf-8-sig").splitlines()
        schema = json.loads(schema_file.read_text(encoding="utf-8"))
    except (OSError, UnicodeError, json.JSONDecodeError) as exc:
        errors.append(_issue(E_READ_ERROR, None, str(exc)))
        return Report("FAIL", str(card), order, errors, warnings, str(schema_file))

    headings = _section_headings(lines)
    title = lines[0].strip() if lines else ""
    metadata, _ = _metadata(lines, headings[0][0] if headings else len(lines))
    structured = title.startswith("# Codex 工单 · ") and any(
        metadata.get(key) for key in ("link", "workdir", "revision")
    )

    if structured:
        errors, warnings = _validate_structured(lines, headings, schema, dispatch_status)
    else:
        if not title.startswith("# "):
            errors.append(_issue(E_MISSING_SECTION, 1 if lines else None, "存量卡也必须包含一级标题"))
        document = {
            "profile": "legacy-queue",
            "title": title,
            "body_line_count": len([line for line in lines if line.strip()]),
            "legacy_sections": [{"heading": heading, "line": index + 1} for index, heading in headings],
        }
        raw_status = metadata.get("status")
        if raw_status:
            document["raw_status"] = raw_status
        errors.extend(_schema_errors(document, schema, 1))
        warnings.append(_issue(W_LEGACY_PROFILE, 1, "存量卡使用 legacy-queue 兼容 profile"))

    errors.extend(_gate_contradictions(lines))
    if strict and warnings:
        errors.extend(_issue(E_STRICT_WARNING, item["line"], f"{item['code']}: {item['message']}") for item in warnings)
    return Report("FAIL" if errors else "PASS", str(card), order, errors, warnings, str(schema_file))


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("card", type=Path)
    parser.add_argument("--json", action="store_true", dest="as_json")
    parser.add_argument("--strict", action="store_true")
    parser.add_argument("--schema", type=Path)
    parser.add_argument("--no-dispatch-status", action="store_true")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    report = validate(
        args.card,
        strict=args.strict,
        schema_path=args.schema,
        dispatch_status=not args.no_dispatch_status,
    )
    if args.as_json:
        print(json.dumps(report.to_dict(), ensure_ascii=False, indent=2))
    else:
        print(f"{report.status}: {report.card}")
        for item in report.errors:
            location = f"line {item['line']}" if item["line"] is not None else "line ?"
            print(f"  {item['code']} {location}: {item['message']}")
        for item in report.warnings:
            location = f"line {item['line']}" if item["line"] is not None else "line ?"
            print(f"  WARNING {item['code']} {location}: {item['message']}", file=sys.stderr)
    return 0 if report.status == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
