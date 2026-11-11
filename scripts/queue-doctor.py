#!/usr/bin/env python3
"""队列体检：把「队列说的」和「磁盘上真实存在的」逐条对账。

设计目的
--------
队列之所以会变成一团乱麻，不是因为单张卡写错，而是因为**同一件事存在多个
自称权威的来源**：queue-status.json 说 frozen、卡文件可能根本没入库、tag 可能
从没打过、run 目录可能早被删掉。人工每次靠印象判断，就会越梳理越乱。

这个脚本把每一类不一致变成一条可复现的判据，谁跑都得到同样的清单。
它只读，不改任何状态；修不修、怎么修由人决定。

判据分级
--------
P0（链路断了，必须处理）：
  CARD_MISSING        队列有记录，磁盘找不到卡        → 派不了也审不了
  FROZEN_WITHOUT_TAG  状态说 frozen，但没有任何冻结 tag → 「已冻结」是自称
  VIEW_DRIFT          md 视图与 JSON 渲染结果不一致     → 两个权威源
  AUDIT_WITHOUT_RUN   状态说 audit，但 audit_run 目录不存在

P1（能跑但会失真）：
  CARD_UNTRACKED      卡文件存在但没进版本控制        → 干净部署读不齐
  FROZEN_WITHOUT_RUN  状态说 frozen，但找不到 run 证据
  STALE_BLOCKER       blocked 的理由指向已过期的条件   → 假阻塞
  ORPHAN_RUN          run 目录在磁盘，队列里没有对应单

用法
----
    python scripts/queue-doctor.py            # 人类可读摘要
    python scripts/queue-doctor.py --json     # 机器可读
    python scripts/queue-doctor.py --strict   # 有 P0 时 exit 2

退出码：0 无 P0；2 有 P0（--strict 时）；1 运行错误。
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parents[1]
QUEUE_DIR = ROOT / "tasks" / "queue"
STATUS_FILE = QUEUE_DIR / "queue-status.json"
RUNS_DIR = QUEUE_DIR / "runs"

sys.path.insert(0, str(ROOT / "scripts"))
import order_naming  # noqa: E402

ORDER_KEYS = {"order", "work_order", "work_order_id", "original_work_order_id"}
TAG_KEYS = {"tag", "tag_name", "freeze_tag", "frozen_tag"}
RECEIPT_NAMES = {"dispatch-record.json", "session.json", "receipt.json"}


def _git_result(*args: str) -> subprocess.CompletedProcess[str]:
    exe = "git"
    for candidate in (
        r"C:\Program Files\Git\cmd\git.exe",
        "/usr/bin/git",
    ):
        if Path(candidate).exists():
            exe = candidate
            break
    return subprocess.run(
        [exe, *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )


def _git(*args: str) -> str:
    result = _git_result(*args)
    if result.returncode != 0:
        summary = (result.stderr or result.stdout).strip()[:400]
        raise RuntimeError(f"git {' '.join(args)} failed ({result.returncode}): {summary}")
    return result.stdout


def _tracked_cards() -> set[str]:
    # HEAD 可取得才算「已入库」。git ls-files 读取 index，会把 staged-only/intent-to-add
    # 的新卡误当成干净检出可用。
    raw = _git("ls-tree", "-r", "--name-only", "HEAD", "--", "tasks/queue")
    return {
        line.strip().replace("\\", "/").casefold()
        for line in raw.splitlines()
        if line.strip()
    }


def _tags() -> list[str]:
    raw = _git("tag", "--list")
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _run_dirs() -> list[str]:
    if not RUNS_DIR.is_dir():
        return []
    return sorted(p.name for p in RUNS_DIR.iterdir() if p.is_dir())


def _read_json(path: Path) -> dict[str, Any] | None:
    try:
        value = json.loads(path.read_text(encoding="utf-8-sig"))
    except (OSError, UnicodeError, json.JSONDecodeError):
        return None
    return value if isinstance(value, dict) else None


def _strings_for_keys(value: Any, keys: set[str]) -> set[str]:
    found: set[str] = set()
    if isinstance(value, dict):
        for key, item in value.items():
            normalized = str(key).casefold()
            if normalized in keys:
                if isinstance(item, str) and item.strip():
                    found.add(item.strip())
                elif isinstance(item, dict):
                    name = item.get("name")
                    if isinstance(name, str) and name.strip():
                        found.add(name.strip())
            found.update(_strings_for_keys(item, keys))
    elif isinstance(value, list):
        for item in value:
            found.update(_strings_for_keys(item, keys))
    return found


def _receipt_paths() -> list[Path]:
    if not RUNS_DIR.is_dir():
        return []
    paths: set[Path] = set()
    for path in RUNS_DIR.rglob("*.json"):
        name = path.name.casefold()
        if (
            name in RECEIPT_NAMES
            or name.startswith("push-status")
            or name.startswith("freeze-")
            or name == "freeze.json"
        ):
            paths.add(path)
    return sorted(paths, key=lambda path: path.as_posix())


def _run_evidence() -> list[dict[str, Any]]:
    evidence: list[dict[str, Any]] = []
    for path in _receipt_paths():
        payload = _read_json(path)
        relative = path.relative_to(ROOT).as_posix()
        top_dir = path.relative_to(RUNS_DIR).parts[0]
        if payload is None:
            evidence.append(
                {
                    "path": relative,
                    "top_dir": top_dir,
                    "kind": path.name.casefold(),
                    "orders": set(),
                    "tags": set(),
                    "readable": False,
                }
            )
            continue
        evidence.append(
            {
                "path": relative,
                "top_dir": top_dir,
                "kind": path.name.casefold(),
                "orders": _strings_for_keys(payload, ORDER_KEYS),
                "tags": _strings_for_keys(payload, TAG_KEYS),
                "readable": True,
            }
        )
    return evidence


def _card_for(order: str) -> Path | None:
    try:
        path = order_naming.resolve_card_path(order, QUEUE_DIR)
    except Exception:
        return None
    return path if path and Path(path).exists() else None


def _tag_tokens(note: str) -> set[str]:
    """从 note 里抓可能的 tag 名。

    本仓的冻结 tag 命名并不统一：有的以工单号开头，更多的是
    `ultimaagent-<功能>-<日期>` 这种语义名。只按工单号前缀匹配会把
    「tag 真的打了」误报成「frozen 无 tag」，凭空造出一批假缺口。
    """
    import re

    return set(re.findall(r"[A-Za-z0-9][A-Za-z0-9._-]{5,}", note))


def _matching_dispatch_records(order: str, evidence: list[dict[str, Any]]) -> list[dict[str, Any]]:
    return [
        item
        for item in evidence
        if item["kind"] == "dispatch-record.json" and order in item["orders"]
    ]


def _tag_check(
    order: str,
    note: str,
    tags: set[str],
    evidence: list[dict[str, Any]],
) -> dict[str, str]:
    receipt_hits: list[tuple[str, str]] = []
    for item in evidence:
        if order not in item["orders"]:
            continue
        for tag in sorted(item["tags"] & tags):
            receipt_hits.append((tag, item["path"]))
    if receipt_hits:
        tag, path = receipt_hits[0]
        return {
            "status": "verified",
            "confidence": "high",
            "tag": tag,
            "evidence": f"run receipt {path} records tag={tag}; git tag --list exact match",
        }

    # note-token 只作低置信兜底。它证明 note 引用了一个真实 tag，但不能证明
    # 引用关系由派发/冻结回执生成。
    note_hits = sorted(_tag_tokens(note) & tags)
    if note_hits:
        tag = note_hits[0]
        return {
            "status": "verified",
            "confidence": "low",
            "tag": tag,
            "evidence": f"queue note token tag={tag}; git tag --list exact match; no run receipt mapping",
        }
    return {
        "status": "unverifiable",
        "confidence": "none",
        "tag": "",
        "evidence": (
            f"no run receipt maps an existing tag to {order}; note has no exact existing tag token; "
            f"scanned_receipts={len(evidence)} git_tags={len(tags)}"
        ),
    }


def _blocker_probe(note: str, records: list[dict[str, Any]]) -> dict[str, str]:
    # 关键词只选择可执行探针，绝不直接决定“过期”。
    tree_claim = bool(re.search(r"未提交改动|clean-tree|工作树|仓库.{0,4}(?:脏|整洁)", note, re.I))
    if tree_claim:
        result = _git_result("status", "--porcelain", "--untracked-files=all")
        if result.returncode != 0:
            summary = (result.stderr or result.stdout).strip()[:300]
            return {
                "status": "unverifiable",
                "evidence": f"git status probe failed ({result.returncode}): {summary}",
            }
        dirty_lines = [line for line in result.stdout.splitlines() if line.strip()]
        return {
            "status": "current" if dirty_lines else "stale",
            "evidence": (
                "git status --porcelain --untracked-files=all "
                f"returned {len(dirty_lines)} non-empty lines"
            ),
        }

    audit_claim = "审计名额" in note or "audit" in note.casefold()
    if audit_claim:
        audit_orders = sorted(
            str(record.get("work_order") or "")
            for record in records
            if str(record.get("state") or "").strip() == "audit"
        )
        return {
            "status": "unverifiable",
            "evidence": (
                "queue snapshot audit-state orders="
                + (", ".join(audit_orders) if audit_orders else "(none)")
                + "; no machine-readable slot limit/reason binding proves this blocker current or stale"
            ),
        }

    return {
        "status": "unverifiable",
        "evidence": "blocked note has no supported current-state probe; reason was not guessed from text",
    }


def diagnose() -> dict:
    if not STATUS_FILE.is_file():
        raise FileNotFoundError(f"缺少权威状态文件: {STATUS_FILE}")
    data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    records = data.get("records", [])
    tracked = _tracked_cards()
    tags = set(_tags())
    runs = _run_dirs()
    run_evidence = _run_evidence()

    findings: list[dict] = []
    checks: list[dict] = []
    seen_orders: set[str] = set()
    # legacy 单（s2/s3/ORB 系列、2026-10 及更早）已按 C 口径裁定「历史不追溯」。
    # 它们的问题依然要看得见，但不该继续占 P0——否则每次体检都被历史噪声淹没，
    # 真正活跃的问题反而被埋掉。
    def add(
        level: str,
        code: str,
        order: str,
        detail: str,
        project: str,
        evidence: str,
        *,
        legacy: bool = False,
        classification: str = "issue",
        confidence: str = "high",
    ) -> None:
        if not evidence.strip():
            raise ValueError(f"{code} evidence must not be empty")
        if legacy and level == "P0":
            level = "P1"
            code = "LEGACY_" + code
        findings.append(
            {
                "level": level,
                "code": code,
                "project": project,
                "work_order": order,
                "detail": detail,
                "classification": classification,
                "confidence": confidence,
                "evidence": evidence,
            }
        )

    for rec in records:
        order = str(rec.get("work_order") or "").strip()
        state = str(rec.get("state") or "").strip()
        project = str(rec.get("project") or "").strip()
        note = str(rec.get("note") or "")
        if not order:
            continue
        seen_orders.add(order)
        legacy = bool(rec.get("legacy"))

        # 只有 UltimaAgent 的卡落在本仓 tasks/queue，别的项目不在这个工作区
        if project != "UltimaAgent":
            continue

        card = _card_for(order)
        if card is None:
            add(
                "P0",
                "CARD_MISSING",
                order,
                "队列有记录，磁盘找不到唯一可解析的卡文件",
                project,
                f"order_naming.resolve_card_path found no unique existing card under {QUEUE_DIR}",
                legacy=legacy,
            )
        else:
            rel = str(card.relative_to(ROOT)).replace("\\", "/")
            if rel.casefold() not in tracked:
                add(
                    "P1",
                    "CARD_UNTRACKED",
                    order,
                    f"卡存在但 HEAD 不可取得: {rel}",
                    project,
                    f"git ls-tree -r --name-only HEAD -- tasks/queue has no case-folded exact path {rel}",
                    legacy=legacy,
                )

        dispatch_records = _matching_dispatch_records(order, run_evidence)

        if state == "frozen":
            tag_check = _tag_check(order, note, tags, run_evidence)
            checks.append(
                {
                    "code": "FROZEN_TAG",
                    "project": project,
                    "work_order": order,
                    **tag_check,
                }
            )
            if tag_check["status"] != "verified":
                add(
                    "P0",
                    "FROZEN_WITHOUT_TAG",
                    order,
                    "state=frozen，但现有事实源无法证明存在归属于该单的冻结 tag",
                    project,
                    tag_check["evidence"],
                    legacy=legacy,
                    classification="unverifiable",
                    confidence="none",
                )
            if not dispatch_records:
                add(
                    "P1",
                    "FROZEN_WITHOUT_RUN",
                    order,
                    "state=frozen，但没有内容身份匹配该单的 dispatch-record.json",
                    project,
                    (
                        f"scanned {sum(item['kind'] == 'dispatch-record.json' for item in run_evidence)} "
                        f"dispatch records under {RUNS_DIR}; exact content order={order} matches=0"
                    ),
                    legacy=legacy,
                )

        if state == "audit":
            audit_run = str(rec.get("audit_run") or "").strip()
            if not dispatch_records:
                add(
                    "P0",
                    "AUDIT_WITHOUT_RUN",
                    order,
                    "state=audit，但没有内容身份匹配该单的 dispatch-record.json",
                    project,
                    (
                        f"audit_run field={audit_run or '(empty)'}; note verdict text was not used as run proof; "
                        f"exact dispatch-record content order={order} matches=0"
                    ),
                    legacy=legacy,
                    classification="unverifiable",
                    confidence="none",
                )

        if state == "blocked":
            probe = _blocker_probe(note, records)
            if probe["status"] == "stale":
                add(
                    "P1",
                    "STALE_BLOCKER",
                    order,
                    "blocked 理由声称的当前条件已被实测否定",
                    project,
                    probe["evidence"],
                    legacy=legacy,
                )
            elif probe["status"] == "unverifiable":
                add(
                    "P1",
                    "STALE_BLOCKER",
                    order,
                    "blocked 理由当前是否仍成立不可机器验证",
                    project,
                    probe["evidence"],
                    legacy=legacy,
                    classification="unverifiable",
                    confidence="none",
                )
            else:
                checks.append(
                    {
                        "code": "BLOCKER_CURRENT",
                        "project": project,
                        "work_order": order,
                        "status": "verified",
                        "confidence": "high",
                        "evidence": probe["evidence"],
                    }
                )

    # run 归属只读 dispatch-record.json 的内容身份，不再猜目录名前缀。
    for r in runs:
        records_in_dir = [
            item
            for item in run_evidence
            if item["top_dir"] == r and item["kind"] == "dispatch-record.json"
        ]
        if not records_in_dir:
            add(
                "P1",
                "ORPHAN_RUN",
                "(不可判定)",
                f"run 目录没有 dispatch-record.json，无法证明归属: {r}",
                "UltimaAgent",
                f"directory={RUNS_DIR / r}; dispatch-record.json count=0",
                classification="unverifiable",
                confidence="none",
            )
            continue
        identities = sorted({order for item in records_in_dir for order in item["orders"]})
        if not identities:
            add(
                "P1",
                "ORPHAN_RUN",
                "(不可判定)",
                f"dispatch-record.json 不含可识别工单身份: {r}",
                "UltimaAgent",
                "records=" + ", ".join(item["path"] for item in records_in_dir),
                classification="unverifiable",
                confidence="none",
            )
            continue
        missing = [order for order in identities if order not in seen_orders]
        if missing:
            add(
                "P1",
                "ORPHAN_RUN",
                ",".join(missing),
                f"run 证据指向队列中不存在的工单: {r}",
                "UltimaAgent",
                (
                    "dispatch records="
                    + ", ".join(item["path"] for item in records_in_dir)
                    + "; content identities="
                    + ", ".join(identities)
                ),
            )

    # 视图漂移
    try:
        out = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "render-queue-views.py"), "--check"],
            cwd=str(ROOT),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        summary = (out.stdout or out.stderr).strip()[:400]
        try:
            payload = json.loads(out.stdout) if out.stdout.strip() else None
        except json.JSONDecodeError:
            payload = None
        differences = payload.get("differences") if isinstance(payload, dict) else None
        if isinstance(differences, list) and differences:
            add(
                "P0",
                "VIEW_DRIFT",
                "(全局)",
                "render --check 发现派生视图与 JSON 不一致",
                "(全局)",
                f"command exit={out.returncode}; differences={differences}",
            )
        elif out.returncode != 0 or not isinstance(differences, list):
            add(
                "P1",
                "VIEW_DRIFT",
                "(全局)",
                "render --check 未产生可验证的 differences 结果",
                "(全局)",
                f"command exit={out.returncode}; output={summary or '(empty)'}",
                classification="unverifiable",
                confidence="none",
            )
    except Exception as exc:  # noqa: BLE001
        add(
            "P1",
            "VIEW_DRIFT",
            "(全局)",
            "无法执行 render --check",
            "(全局)",
            f"{type(exc).__name__}: {exc}",
            classification="unverifiable",
            confidence="none",
        )

    p0 = [f for f in findings if f["level"] == "P0"]
    p1 = [f for f in findings if f["level"] == "P1"]
    return {
        "records": len(records),
        "cards_on_disk": len(list(QUEUE_DIR.glob("wo-*.md"))),
        "run_dirs": len(runs),
        "tags": len(tags),
        "p0": len(p0),
        "p1": len(p1),
        "findings": findings,
        "checks": checks,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="队列体检：对账状态与磁盘现实")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--strict", action="store_true", help="有 P0 时 exit 2")
    parser.add_argument("--out", help="把 JSON 结果落盘")
    args = parser.parse_args()

    try:
        result = diagnose()
    except Exception as exc:  # noqa: BLE001
        print(f"queue-doctor 运行错误: {type(exc).__name__}: {exc}", file=sys.stderr)
        return 1

    if args.out:
        Path(args.out).write_text(json.dumps(result, ensure_ascii=False, indent=2), encoding="utf-8")

    if args.json:
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        print(f"队列记录 {result['records']} 条 ｜ 磁盘卡 {result['cards_on_disk']} 张 ｜ run 目录 {result['run_dirs']} 个 ｜ tag {result['tags']} 个")
        print(f"P0 {result['p0']} 条 ｜ P1 {result['p1']} 条")
        by_code: dict[str, list[dict]] = {}
        for f in result["findings"]:
            by_code.setdefault(f["code"], []).append(f)
        for code, items in sorted(by_code.items(), key=lambda kv: (kv[1][0]["level"], kv[0])):
            level = items[0]["level"]
            print(f"\n[{level}] {code}（{len(items)}）")
            for it in items[:12]:
                print(
                    f"  - {it['work_order']}: {it['detail']} "
                    f"[classification={it['classification']} confidence={it['confidence']}]"
                )
                print(f"    evidence: {it['evidence']}")
            if len(items) > 12:
                print(f"  … 另 {len(items) - 12} 条")
        low_checks = [check for check in result["checks"] if check["confidence"] == "low"]
        if low_checks:
            print(f"\n[LOW] 低置信通过证据（{len(low_checks)}）")
            for check in low_checks[:12]:
                print(f"  - {check['work_order']}: {check['evidence']}")

    if args.strict and result["p0"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
