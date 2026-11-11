#!/usr/bin/env python3
"""机制变更验收器：元工单 / 改造类工单专用。

`verify-order.py` 验的是「一次派发 run 的 done.json 与交付树」的回执契约。
元工单不是通过某次派发 run 交付的，拿这套契约去验它，得到的六项失败全在
描述契约错配，而不是描述「机制到底生效了没有」——所以它对这个 profile
结构性不可达（L116/L117）。

本脚本给这类改动一条独立、可机检、且不放宽的验收路径：

  1. card_resolved            卡可解析
  2. head_matches_origin      交付已推送（HEAD 与 origin/<branch> 同一提交）
  3. files_committed          声明的改动真的进了 HEAD 的树，不是只改了工作区
  4. full_regression_green    全量回归在**干净检出**上跑绿（不是脏工作区的结果）
  5. dispatch_gate_regression 新机检真的在拦（对真实卡跑派发门，断言退出码与关键串）
  6. lesson_logged            教训已登记（lessons-log 含指定编号）

判据比「跑一次 pytest 就过」更严：第 4 条在干净 checkout 上跑，避免工作区
残留把失败测试顶成绿；第 5 条要求拦截真实发生，而不是看配置里写了什么。
退出码：0 通过 / 2 未通过 / 3 参数或环境不足。
"""

from __future__ import annotations

import argparse
import importlib.util
import json
import os
import subprocess
import sys
import tempfile
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT / "scripts"))

from order_naming import resolve_card_path  # noqa: E402


def _load_verify_order():
    """按文件路径加载 verify-order.py：文件名带连字符，不能直接 import。"""

    path = ROOT / "scripts" / "verify-order.py"
    spec = importlib.util.spec_from_file_location("verify_order_support", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)  # type: ignore[union-attr]
    return module


vo = _load_verify_order()


def _card(order: str, card_arg: str | None) -> tuple[bool, str, Path | None]:
    if card_arg:
        path = Path(card_arg)
        if not path.is_absolute():
            path = ROOT / path
        return path.is_file(), str(path), path
    try:
        path = resolve_card_path(order, ROOT / "tasks/queue")
    except ValueError as exc:
        return False, str(exc), None
    return True, str(path), path


def _pushed() -> tuple[bool, str]:
    head = (vo._git("rev-parse", "HEAD").stdout or "").strip()
    if not head:
        return False, "git rev-parse HEAD failed; the delivered commit is unknown"
    branch = (vo._git("rev-parse", "--abbrev-ref", "HEAD").stdout or "").strip()
    if not branch or branch == "HEAD":
        return False, f"detached HEAD {head[:12]}; there is no origin branch to compare against"
    # `git rev-parse` on a missing ref succeeds by echoing the input, so the
    # return code is what separates "not fetched" from "points elsewhere".
    probe = vo._git("rev-parse", "--verify", f"origin/{branch}")
    origin = (probe.stdout or "").strip() if probe.returncode == 0 else ""
    if not origin:
        return False, f"origin/{branch} is not available; the work cannot be shown to be pushed"
    if origin != head:
        return False, f"HEAD {head[:12]} differs from origin/{branch} {origin[:12]}; push first"
    return True, f"HEAD == origin/{branch} == {head[:12]}"


def _files(files: list[str]) -> tuple[bool, str]:
    if not files:
        return False, "no --file given; a mechanism change must name what it delivered"
    head = (vo._git("rev-parse", "HEAD").stdout or "").strip()
    if not head:
        return False, "git rev-parse HEAD failed; nothing can be proven committed"
    problems: list[str] = []
    for raw in files:
        rel = raw.replace("\\", "/")
        if not (ROOT / rel).is_file():
            problems.append(f"{rel} is absent on disk")
            continue
        tree = vo._git("ls-tree", "-r", head, "--", rel)
        if tree.returncode != 0 or not (tree.stdout or "").strip():
            problems.append(f"{rel} is not in the {head[:12]} tree (uncommitted change)")
            continue
        # Presence in the tree is not delivery: the file can be in HEAD from an older
        # commit while this change sits uncommitted in the working tree.
        diff = vo._git("diff", "--name-only", head, "--", rel)
        if (diff.stdout or "").strip():
            problems.append(f"{rel} has uncommitted changes")
    if problems:
        return False, "; ".join(problems)
    return True, f"{len(files)} declared files are committed at {head[:12]}"


def _regression(timeout: int) -> tuple[bool, str]:
    head = (vo._git("rev-parse", "HEAD").stdout or "").strip()
    if not head:
        return False, "git rev-parse HEAD failed"
    # The gate builds pytest's own options; adding flags here would be read as a
    # target path and rejected ("-o is not in the delivered tree").
    argv = [sys.executable, "-m", "pytest", "scripts/tests"]
    proc, why, counts = vo._run_in_clean_worktree(head, argv, timeout)
    if proc is None:
        return False, f"the clean checkout could not run the suite: {why}"
    if proc.returncode != 0:
        tail = ((proc.stdout or "").strip().splitlines() or [""])[-1][:180]
        return False, f"pytest exited {proc.returncode} on a clean checkout: {tail}"
    if counts is None:
        return False, "the run produced no test report; nothing proves a test executed"
    executed = counts["tests"] - counts["skipped"]
    if executed <= 0:
        return False, f"report counts {executed} executed tests"
    if counts["failures"] or counts["errors"]:
        return False, (f"{executed} executed, {counts['failures']} failed, "
                       f"{counts['errors']} errored")
    return True, f"{executed} tests passed, {counts['skipped']} skipped on a clean checkout of {head[:12]}"


def _gate(order: str, card: Path | None, expect_exit: int, contains: list[str],
          timeout: int) -> tuple[bool, str]:
    if card is None:
        return False, "the card is unresolved; the dispatch gate cannot be exercised"
    handle, name = tempfile.mkstemp(prefix="mechanism-gate-", suffix=".txt")
    # mkstemp hands back an open descriptor; leaving it open makes the unlink below
    # fail with WinError 32 on this platform and masks the real gate result.
    os.close(handle)
    prompt = Path(name)
    try:
        prompt.write_text(f"docs/INDEX.md {order}", encoding="utf-8")
        proc = subprocess.run(
            [sys.executable, str(ROOT / "scripts" / "dispatch-work-order.py"),
             "--order", order, "--prompt", str(prompt), "--card", str(card), "--dry-run-dor"],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
            cwd=str(ROOT), timeout=timeout,
        )
    except subprocess.TimeoutExpired:
        return False, f"the dispatch gate timed out after {timeout}s"
    finally:
        try:
            prompt.unlink(missing_ok=True)
        except OSError:
            pass
    out = (proc.stdout or "") + (proc.stderr or "")
    missing = [s for s in contains if s not in out]
    if proc.returncode != expect_exit:
        return False, f"dispatch gate exited {proc.returncode}, expected {expect_exit}"
    if missing:
        return False, "dispatch gate output is missing: " + ", ".join(missing)
    return True, f"dispatch gate exited {expect_exit} and reported {', '.join(contains)}"


def _lesson(marker: str) -> tuple[bool, str]:
    if not marker:
        return False, "no --require-lesson given; an unrecorded lesson is not a closed one"
    log = ROOT / "docs" / "references" / "lessons-log.md"
    if not log.is_file():
        return False, "docs/references/lessons-log.md is missing"
    text = log.read_text(encoding="utf-8", errors="replace")
    if marker not in text:
        return False, f"lessons-log.md does not mention {marker}"
    return True, f"lessons-log.md mentions {marker}"


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__,
                                     formatter_class=argparse.RawDescriptionHelpFormatter)
    parser.add_argument("--order", required=True, help="元工单 id")
    parser.add_argument("--card", help="卡路径；缺省按 order 解析")
    parser.add_argument("--file", action="append", default=[], help="本次交付的文件，可重复")
    parser.add_argument("--require-lesson", default="", help="lessons-log 必须包含的编号，如 L121")
    parser.add_argument("--gate-exit", type=int, default=2, help="派发门期望退出码")
    parser.add_argument("--gate-contains", action="append", default=[],
                        help="派发门输出必须包含的串，可重复")
    parser.add_argument("--suite-timeout", type=int, default=600)
    parser.add_argument("--gate-timeout", type=int, default=180)
    parser.add_argument("--out", type=Path, help="结果写到这里；缺省打印到 stdout")
    return parser


def main(argv: list[str] | None = None) -> int:
    args = _parser().parse_args(argv)
    checks: list[dict] = []

    def add(name: str, outcome: tuple[bool, str]) -> None:
        checks.append({"check": name, "passed": outcome[0], "detail": outcome[1]})

    card_ok, card_detail, card_path = _card(args.order, args.card)
    add("card_resolved", (card_ok, card_detail))
    add("head_matches_origin", _pushed())
    add("files_committed", _files(args.file))
    add("full_regression_green", _regression(args.suite_timeout))
    add("dispatch_gate_regression",
        _gate(args.order, card_path, args.gate_exit, args.gate_contains, args.gate_timeout))
    add("lesson_logged", _lesson(args.require_lesson))

    blocking = [c["check"] for c in checks if not c["passed"]]
    payload = {
        "work_order": args.order,
        "profile": "mechanism-change",
        "verified": not blocking,
        "blocking_failures": blocking,
        "checks": checks,
        "head": (vo._git("rev-parse", "HEAD").stdout or "").strip(),
        "verified_at": datetime.now(timezone.utc).isoformat(),
    }
    text = json.dumps(payload, ensure_ascii=False, indent=2) + "\n"
    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(text, encoding="utf-8")
        print(json.dumps({"verified": payload["verified"],
                          "blocking_failures": blocking,
                          "out": str(args.out)}, ensure_ascii=False))
    else:
        print(text)
    return 0 if payload["verified"] else 2


if __name__ == "__main__":
    raise SystemExit(main())
