#!/usr/bin/env python
"""Work-order card consistency checker.

Two error classes this exists to catch, both observed repeatedly in this repo:

C1  Three-section drift. ``§1 范围冻结`` / ``§2 任务清单`` / ``§3 任务明细``
    must agree on which files a work order touches. They drift when the author
    revises §3 after §1 and never goes back (lessons-log L174).

C2  Parameter contract guesswork. A card that prescribes a downstream script
    CLI switch must match that script's *real* argparse surface. The reference
    incident: a card told the implementer to pass ``--skip-freeze`` and
    ``--evidence`` to a new entry point while ``verify-order.py`` and
    ``audit-work-order.py`` only bind ``--run-dir`` for their read/write paths,
    so the prescribed command could never have worked.

C3  Phantom paths. Every python path a card names is either on disk (searched
    across the whole repo, not just the repo root) or explicitly declared new.

What this CANNOT catch, and does not pretend to: a card whose switch names are
all real but whose *semantics* are wrong — e.g. claiming ``--evidence`` can
replace ``--run-dir`` as an input source. That class is reported as C4 for a
human to read, never as an automated pass.

Exit 0 = no FAIL findings. Exit 2 = at least one FAIL.
"""

from __future__ import annotations

import argparse
import json
import os
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

SWITCH_RE = re.compile(r"--[a-z][a-z0-9-]*")
# Any python path with at least one directory component. Matches
# scripts/x.py, tests/x.py, src/brain/tests/x.py alike.
PATH_RE = re.compile(r"[A-Za-z0-9_./\-]+/[A-Za-z0-9_.\-]+\.py")
ARGDECL_RE = re.compile(r"add_argument\(\s*[\"'](--[a-z][a-z0-9-]*)[\"']")
DECL_LINE_RE = re.compile(r"参数\s*[：:]\s*(.*)")
TASKROW_RE = re.compile(r"^\|\s*(T\d+[a-z]?)\s*\|(.*)\|\s*$")
HEADING2_RE = re.compile(r"^##\s+(\d+)\..*$")
H2_TASKRE = re.compile(r"^###\s+(T\d+[a-z]?)\s*·")
FILELINE_RE = re.compile(r"^\*\*文件\*\*[:：]\s*(.+)$")

# Phrases that assert behaviour of a downstream script and therefore need a
# human to confirm the semantics, not just the switch spelling.
SEMANTIC_HINT_RE = re.compile(
    r"(只从|都绑|绑定|读\s*<|写\s*<|读取|写入|替代|作为输入|不复制|必须复制)"
)

_NEW_MARKERS = ("新建", "新增", "待建", "创建")


def _lines(text: str) -> list[str]:
    return text.splitlines()


def _section_bounds(lines: list[str], index: int) -> tuple[int, int]:
    start = None
    for i, line in enumerate(lines):
        m = HEADING2_RE.match(line.strip())
        if m and int(m.group(1)) == index:
            start = i
            break
    if start is None:
        return (-1, -1)
    for j in range(start + 1, len(lines)):
        if HEADING2_RE.match(lines[j].strip()):
            return (start, j)
    return (start, len(lines))


def _paths_in(chunk: str) -> set[str]:
    found = set()
    for raw in PATH_RE.findall(chunk):
        clean = raw.lstrip("./")
        # Skip things that are clearly not repo paths (URLs, template names).
        if "://" in raw or raw.startswith("http"):
            continue
        found.add(clean)
    return found


def _repo_py_names() -> set[str]:
    """Basenames of every .py under the code roots we actually care about.

    Deliberately bounded: walking the whole repo times out on this tree
    (hundreds of untracked files under src/brain, plus vendored trees).
    """
    names: set[str] = set()
    roots = ("scripts", "tests", "src", "tools")
    skip = {"__pycache__", "node_modules", ".venv", "venv-openjarvis", ".git"}
    for root in roots:
        base = ROOT / root
        if not base.is_dir():
            continue
        for dirpath, dirnames, filenames in os.walk(base):
            dirnames[:] = [d for d in dirnames if d not in skip]
            for fn in filenames:
                if fn.endswith(".py"):
                    names.add(fn)
    return names


def _only_do_bounds(lines: list[str], r1: tuple[int, int]) -> tuple[int, int]:
    """Narrow §1 to its 「本单只做」 half, so 「不做」 paths are not counted."""
    if r1[0] < 0:
        return (-1, -1)
    start = r1[0]
    end = r1[1]
    for i in range(r1[0], r1[1]):
        if re.search(r"本单不做|Non-goals|不做", lines[i]):
            end = i
            break
    for i in range(r1[0], r1[1]):
        if re.search(r"本单只做|只做", lines[i]):
            start = i
            break
    return (start, end)


def check_section_drift(lines: list[str]) -> list[dict]:
    findings: list[dict] = []
    r1 = _section_bounds(lines, 1)
    r2 = _section_bounds(lines, 2)
    r3 = _section_bounds(lines, 3)
    r1d = _only_do_bounds(lines, r1)

    s1_paths = _paths_in("\n".join(lines[r1d[0]:r1d[1]])) if r1d[0] >= 0 else set()
    s2_paths: set[str] = set()
    s2_task_files: dict[str, set[str]] = {}
    if r2[0] >= 0:
        for i in range(r2[0], r2[1]):
            m = TASKROW_RE.match(lines[i].strip())
            if not m:
                continue
            cells = [c.strip() for c in m.group(2).split("|")]
            found: set[str] = set()
            for cell in cells:
                found |= _paths_in(cell)
            s2_task_files[m.group(1)] = found
            s2_paths |= found

    s3_paths: set[str] = set()
    s3_task_files: dict[str, set[str]] = {}
    if r3[0] >= 0:
        current = None
        for i in range(r3[0], r3[1]):
            hm = H2_TASKRE.match(lines[i].strip())
            if hm:
                current = hm.group(1)
                s3_task_files.setdefault(current, set())
                continue
            fm = FILELINE_RE.match(lines[i].strip())
            if fm and current:
                found = _paths_in(fm.group(1))
                s3_task_files[current] |= found
                s3_paths |= found

    for path in sorted(s1_paths - (s2_paths | s3_paths)):
        findings.append({
            "code": "C1a", "severity": "fail",
            "detail": f"§1 范围冻结点名 {path}，但 §2 与 §3 都没有安排它",
        })
    for path in sorted(s2_paths - s3_paths):
        findings.append({
            "code": "C1b", "severity": "fail",
            "detail": f"§2 任务表安排 {path}，但 §3 没有任何一条「文件：」写它",
        })
    for task in sorted(set(s2_task_files) & set(s3_task_files)):
        only2 = s2_task_files[task] - s3_task_files[task]
        only3 = s3_task_files[task] - s2_task_files[task]
        if only2 or only3:
            findings.append({
                "code": "C1c", "severity": "fail",
                "detail": (f"{task} 的 §2/§3 文件集合不一致："
                           f"仅§2={sorted(only2) or '无'}；仅§3={sorted(only3) or '无'}"),
            })
    return findings


def check_downstream_cli(lines: list[str], path_cache: dict[str, set[str]]) -> list[dict]:
    """C2b: a switch attributed to a real script must exist in that script."""
    findings: list[dict] = []
    for i, line in enumerate(lines):
        scripts_here = [p for p in _paths_in(line) if p.endswith(".py")]
        switches_here = set(SWITCH_RE.findall(line))
        if not scripts_here or not switches_here:
            continue
        for script_rel in scripts_here:
            real = ROOT / script_rel
            if not real.is_file():
                continue
            if script_rel not in path_cache:
                text = real.read_text(encoding="utf-8", errors="replace")
                path_cache[script_rel] = set(ARGDECL_RE.findall(text))
            real_switches = path_cache[script_rel]
            if not real_switches:
                continue  # script has no CLI of its own
            unknown = switches_here - real_switches
            if unknown:
                findings.append({
                    "code": "C2b", "severity": "fail",
                    "detail": (f"L{i + 1} 给 {script_rel} 用了它不存在的参数 "
                               f"{sorted(unknown)}（真实参数：{', '.join(sorted(real_switches))}）"),
                })
    return findings


def check_switch_declared(lines: list[str]) -> list[dict]:
    """C2a: a switch the card prescribes must appear in the card's own surface."""
    findings: list[dict] = []
    declared: set[str] = set()
    for line in lines:
        m = DECL_LINE_RE.search(line)
        if m:
            declared |= set(SWITCH_RE.findall(m.group(1)))
        for dm in ARGDECL_RE.finditer(line):
            declared.add(dm.group(1))

    prescribed: dict[str, int] = {}
    for i, line in enumerate(lines):
        # Only the card's OWN new entry point counts. Switches belonging to
        # existing downstream scripts (--dry-run-dor, --execute, --profile)
        # are their business, not something this card must declare.
        if "run-pipeline.py" in line:
            for sw in SWITCH_RE.findall(line):
                prescribed.setdefault(sw, i + 1)

    if not declared:
        findings.append({
            "code": "C2a", "severity": "warn",
            "detail": "卡片没有「参数：」清单行，无法机械核对参数契约",
        })
        return findings

    for sw, lineno in sorted(prescribed.items()):
        if sw not in declared:
            findings.append({
                "code": "C2a", "severity": "fail",
                "detail": (f"L{lineno} 的命令里用了 {sw}，但卡片参数清单未声明"
                           f"（已声明 {len(declared)} 个）"),
            })
    return findings


def check_phantom_paths(lines: list[str], repo_names: set[str]) -> list[dict]:
    """C3: a named python path exists somewhere, or the card declares it new."""
    findings: list[dict] = []
    seen: set[str] = set()
    for i, line in enumerate(lines):
        for path in _paths_in(line):
            if path in seen:
                continue
            if (ROOT / path).exists() or Path(path).name in repo_names:
                continue
            window = " ".join(lines[max(0, i - 2):i + 3])
            if any(marker in window for marker in _NEW_MARKERS):
                seen.add(path)
                continue
            seen.add(path)
            findings.append({
                "code": "C3", "severity": "warn",
                "detail": f"L{i + 1} 点名 {path}，全仓库找不到同名文件，附近也无「新建/新增/待建」",
            })
    return findings


def check_semantic_claims(lines: list[str]) -> list[dict]:
    """C4: behaviour statements about downstream scripts need a human read."""
    findings: list[dict] = []
    for i, line in enumerate(lines):
        if not SEMANTIC_HINT_RE.search(line):
            continue
        if not re.search(r"[A-Za-z0-9_\-]+\.py", line):
            continue
        findings.append({
            "code": "C4", "severity": "warn",
            "detail": f"L{i + 1} 对下游脚本的行为做了语义断言，机器无法验证，需人工核接口实现",
        })
    return findings


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--card", required=True)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    card = Path(args.card)
    if not card.is_file():
        print(json.dumps({"ok": False, "reason": f"card not found: {card}"}, ensure_ascii=False))
        return 2

    text = card.read_text(encoding="utf-8-sig", errors="replace")
    lines = _lines(text)
    repo_names = _repo_py_names()
    cache: dict[str, set[str]] = {}

    findings: list[dict] = []
    findings += check_section_drift(lines)
    findings += check_downstream_cli(lines, cache)
    findings += check_switch_declared(lines)
    findings += check_phantom_paths(lines, repo_names)
    findings += check_semantic_claims(lines)

    fails = [f for f in findings if f["severity"] == "fail"]
    warns = [f for f in findings if f["severity"] == "warn"]
    payload = {
        "ok": not fails, "card": str(card),
        "fail_count": len(fails), "warn_count": len(warns),
        "findings": findings,
    }

    if args.json:
        print(json.dumps(payload, ensure_ascii=False, indent=2))
    else:
        print(f"card: {card}")
        print(f"FAIL {len(fails)} / WARN {len(warns)}")
        for f in findings:
            print(f"  [{f['severity'].upper():4s}] {f['code']}  {f['detail']}")
        print("VERDICT:", "PASS" if not fails else "FAIL")
    return 0 if not fails else 2


if __name__ == "__main__":
    raise SystemExit(main())
