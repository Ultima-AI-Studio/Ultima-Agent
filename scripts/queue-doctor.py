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

ROOT = Path(__file__).resolve().parents[1]
QUEUE_DIR = ROOT / "tasks" / "queue"
STATUS_FILE = QUEUE_DIR / "queue-status.json"
RUNS_DIR = QUEUE_DIR / "runs"

sys.path.insert(0, str(ROOT / "scripts"))
import order_naming  # noqa: E402

# blocked 的 note 里出现这些词，说明理由可能是「当时的状态」，需要复核
STALE_BLOCKER_MARKERS = (
    "未提交改动",
    "clean-tree",
    "562 条",
    "审计名额",
    "不再占用审计名额",
)


def _git(*args: str) -> str:
    exe = "git"
    for candidate in (
        r"C:\Program Files\Git\cmd\git.exe",
        "/usr/bin/git",
    ):
        if Path(candidate).exists():
            exe = candidate
            break
    out = subprocess.run(
        [exe, *args],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    return out.stdout


def _tracked_cards() -> set[str]:
    raw = _git("ls-files", "--", "tasks/queue")
    return {line.strip().replace("\\", "/") for line in raw.splitlines() if line.strip()}


def _tags() -> list[str]:
    raw = _git("tag", "--list")
    return [line.strip() for line in raw.splitlines() if line.strip()]


def _run_dirs() -> list[str]:
    if not RUNS_DIR.is_dir():
        return []
    return [p.name for p in RUNS_DIR.iterdir() if p.is_dir()]


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


def diagnose() -> dict:
    if not STATUS_FILE.is_file():
        raise SystemExit(f"缺少权威状态文件: {STATUS_FILE}")
    data = json.loads(STATUS_FILE.read_text(encoding="utf-8"))
    records = data.get("records", [])
    tracked = _tracked_cards()
    tags = _tags()
    runs = _run_dirs()

    findings: list[dict] = []
    seen_orders: set[str] = set()
    # legacy 单（s2/s3/ORB 系列、2026-10 及更早）已按 C 口径裁定「历史不追溯」。
    # 它们的问题依然要看得见，但不该继续占 P0——否则每次体检都被历史噪声淹没，
    # 真正活跃的问题反而被埋掉。
    state_flag = {"legacy": False}

    def add(level: str, code: str, order: str, detail: str, project: str) -> None:
        if state_flag["legacy"] and level == "P0":
            level = "P1"
            code = "LEGACY_" + code
        findings.append(
            {
                "level": level,
                "code": code,
                "project": project,
                "work_order": order,
                "detail": detail,
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
        state_flag["legacy"] = bool(rec.get("legacy"))

        # 只有 UltimaAgent 的卡落在本仓 tasks/queue，别的项目不在这个工作区
        if project != "UltimaAgent":
            continue

        card = _card_for(order)
        if card is None:
            add("P0", "CARD_MISSING", order, "队列有记录，磁盘找不到卡文件", project)
        else:
            rel = str(card.relative_to(ROOT)).replace("\\", "/")
            if rel not in tracked:
                add("P1", "CARD_UNTRACKED", order, f"卡存在但未入库: {rel}", project)

        # tag 认三种证据：以工单号开头、note 里登记过且真实存在、run 目录里有 tag 记录
        tag_set = set(tags)
        note_tags = sorted(t for t in _tag_tokens(note) if t in tag_set)
        has_tag = any(t.startswith(order) for t in tag_set) or bool(note_tags)
        has_run = any(r.startswith(order) for r in runs)

        if state == "frozen":
            if not has_tag:
                add("P0", "FROZEN_WITHOUT_TAG", order, "state=frozen 但没有任何以该单开头的 tag", project)
            if not has_run:
                add("P1", "FROZEN_WITHOUT_RUN", order, "state=frozen 但 runs/ 下没有该单的 run 目录", project)

        if state == "audit":
            audit_run = str(rec.get("audit_run") or "").strip()
            # 独立审计不一定由派发器发起，所以「没填 audit_run」不等于「没审」。
            # 只有 note 里也拿不出任何审计结论时，才当成链路断了。
            has_verdict = bool(re.search(r"PASS|通过|审计完成|独立审计", note))
            if not audit_run:
                level = "P1" if has_verdict else "P0"
                add(level, "AUDIT_WITHOUT_RUN", order, "state=audit 但 audit_run 为空" + ("（note 已有审计结论）" if has_verdict else ""), project)
            elif not (RUNS_DIR / Path(audit_run).name).exists() and not any(
                r.startswith(Path(audit_run).name[:20]) for r in runs
            ):
                add("P0", "AUDIT_WITHOUT_RUN", order, f"state=audit 但目录不存在: {audit_run}", project)

        if state == "blocked":
            hit = [m for m in STALE_BLOCKER_MARKERS if m in note]
            if hit:
                add("P1", "STALE_BLOCKER", order, "blocked 理由含可能过期的措辞: " + "、".join(hit), project)

    # run 目录在磁盘但队列里没有对应单
    state_flag["legacy"] = False
    for r in runs:
        if not any(r.startswith(o) for o in seen_orders):
            add("P1", "ORPHAN_RUN", "(无记录)", f"runs/ 下有目录但无对应单: {r}", "UltimaAgent")

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
        if out.returncode != 0:
            add("P0", "VIEW_DRIFT", "(全局)", (out.stdout or out.stderr).strip()[:400] or "render --check 失败", "(全局)")
    except Exception as exc:  # noqa: BLE001
        add("P1", "VIEW_DRIFT", "(全局)", f"无法执行 render --check: {exc}", "(全局)")

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
    }


def main() -> int:
    parser = argparse.ArgumentParser(description="队列体检：对账状态与磁盘现实")
    parser.add_argument("--json", action="store_true", help="输出 JSON")
    parser.add_argument("--strict", action="store_true", help="有 P0 时 exit 2")
    parser.add_argument("--out", help="把 JSON 结果落盘")
    args = parser.parse_args()

    result = diagnose()

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
                print(f"  - {it['work_order']}: {it['detail']}")
            if len(items) > 12:
                print(f"  … 另 {len(items) - 12} 条")

    if args.strict and result["p0"] > 0:
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
