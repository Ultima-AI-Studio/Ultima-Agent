"""The one list of what a local checkout needs to run, and what to do about it.

Every environment gap this repo hit during 0051 was handled where it was noticed:
`libs/` got a junction hardcoded inside `verify-order.py`, `ollama` got a skip inside
one test file, the interpreter got an absolute path inside `_pin_runner()`. Three
places, three rules, and nothing that could answer "is this checkout ready?" — so a
fresh clone still failed to collect and each failure was re-diagnosed from scratch.

This module is the single list. It states, per dependency: whether the repo must have
it, how to tell whether it is present, and — when it is absent — what that actually
costs. Callers that already know one of these facts (the verifier, the skip gate)
read it here instead of restating it, so a dependency added once is visible everywhere.

Three kinds, because the remedy differs:

  mount       absent from git, must be linked into a checkout (``libs/``)
  reference   absent from git, used by absolute path from the main repo (the venv)
  external    not part of the repo at all (``ollama``, API credentials)

Required entries block: without them the declared test command cannot even collect.
Optional entries degrade: their absence removes coverage, and each one names the
specific thing that stops working so the cost is stated rather than discovered.
"""

from __future__ import annotations

import argparse
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path
from typing import Callable

ROOT = Path(__file__).resolve().parents[1]


class Asset:
    """One thing a checkout needs, and the honest cost of not having it."""

    __slots__ = ("id", "kind", "required", "probe", "reason", "absent_effect",
                 "mount_name", "mount_target")

    def __init__(self, id: str, kind: str, required: bool, probe: Callable[[Path], bool],
                 reason: str, absent_effect: str = "",
                 mount_name: str = "", mount_target: str = ""):
        self.id = id
        self.kind = kind
        self.required = required
        self.probe = probe
        self.reason = reason
        self.absent_effect = absent_effect
        self.mount_name = mount_name
        self.mount_target = mount_target


def _libs_usable(root: Path) -> bool:
    """`libs/` present *and* carrying the file the server actually reads.

    A bare directory named `libs` proves only that someone created a directory. The
    real dependency is the persona prompt `agent_server.py` reads at startup plus the
    `openjarvis` import root, so presence is judged by the prompt file being readable.
    """
    prompt = root / "libs/base/openjarvis/configs/openjarvis/prompts/personas/jarvis.md"
    return prompt.is_file() and prompt.stat().st_size > 0


def _runner_present(root: Path) -> bool:
    return (root / "tools/venv-openjarvis/Scripts/python.exe").is_file()


def _secrets_present(root: Path) -> bool:
    return (root / "config/.env").is_file()


def _ollama_present(_root: Path) -> bool:
    return shutil.which("ollama") is not None


ASSETS: tuple[Asset, ...] = (
    Asset(
        id="libs",
        kind="mount",
        required=True,
        probe=_libs_usable,
        reason="openjarvis import root and the main-brain persona prompt",
        absent_effect="the declared test command cannot collect, so every order "
                      "reports an environment failure instead of a delivery result",
        mount_name="libs",
        mount_target="libs",
    ),
    Asset(
        id="runner",
        kind="reference",
        required=True,
        probe=_runner_present,
        reason="the acceptance interpreter (Python 3.13.16, tools/venv-openjarvis)",
        absent_effect="nothing runs: it is the interpreter every declared command uses",
    ),
    Asset(
        id="secrets",
        kind="external",
        required=False,
        probe=_secrets_present,
        reason="DeepSeek API credentials in config/.env",
        absent_effect="audit-work-order.py cannot call the reviewer; verify is unaffected",
    ),
    Asset(
        id="ollama",
        kind="external",
        required=False,
        probe=_ollama_present,
        reason="local model inventory used by one connectivity test",
        absent_effect="that one test skips; no coverage is lost elsewhere",
    ),
)

MOUNTABLE = tuple(a for a in ASSETS if a.kind == "mount")


def status(root: Path = ROOT) -> list[dict]:
    """Every asset with its current state. Read-only: this never changes anything."""
    rows = []
    for asset in ASSETS:
        try:
            present = bool(asset.probe(root))
        except OSError:
            present = False
        rows.append({
            "id": asset.id,
            "kind": asset.kind,
            "required": asset.required,
            "present": present,
            "reason": asset.reason,
            "absent_effect": asset.absent_effect,
            "blocking": asset.required and not present,
        })
    return rows


def blocking(rows: list[dict]) -> list[dict]:
    return [row for row in rows if row["blocking"]]


def mount_names() -> tuple[str, ...]:
    """The directories a checkout has to be given, for callers that used to hardcode."""
    return tuple(a.mount_name for a in MOUNTABLE)


def _junction(link: Path, target: Path) -> str:
    """Link a checkout to the real bytes. Returns "" on success, a reason otherwise.

    `mklink /J` creates a directory junction: same bytes, no copy, nothing added to
    git. `os.symlink` is not usable here — on Windows a directory symlink needs either
    Developer Mode or an elevated token, and it failed with WinError 183 in a sandbox
    that has neither. `cmd` is invoked through `ComSpec` because it is not on PATH in
    every shell this runs under.
    """
    if not target.is_dir():
        return f"{target.name}/ 不存在，无从挂载"
    if os.path.lexists(link):
        return ""
    if os.name == "nt":
        proc = subprocess.run(
            [os.environ.get("ComSpec") or "cmd.exe", "/c", "mklink", "/J",
             str(link), str(target)],
            capture_output=True, text=True, encoding="utf-8", errors="replace",
        )
        if proc.returncode != 0:
            return f"不能挂载 {link.name}/：{((proc.stderr or proc.stdout or '')[:140]).strip()}"
    else:
        try:
            os.symlink(str(target), str(link), target_is_directory=True)
        except OSError as exc:
            return f"不能挂载 {link.name}/：{exc}"
    return "" if link.is_dir() else f"{link.name}/ 挂载后仍不可读"


def apply(worktree: Path, source: Path = ROOT) -> list[dict]:
    """Give a checkout the assets it cannot contain. Idempotent."""
    done = []
    for asset in MOUNTABLE:
        link = worktree / asset.mount_name
        target = source / asset.mount_target
        problem = _junction(link, target)
        done.append({"id": asset.id, "link": str(link),
                     "ok": not problem, "detail": problem or "mounted"})
    return done


def release(worktree: Path) -> list[dict]:
    """Remove the links without touching the bytes they point at.

    `shutil.rmtree` follows a junction on Windows and deletes the real target's
    contents; `os.rmdir` removes only the link. That asymmetry is why this is a
    function rather than a line inside a cleanup handler.
    """
    done = []
    for asset in MOUNTABLE:
        link = worktree / asset.mount_name
        if not os.path.lexists(link):
            done.append({"id": asset.id, "link": str(link), "ok": True,
                         "detail": "absent"})
            continue
        try:
            os.rmdir(link)
            done.append({"id": asset.id, "link": str(link), "ok": True, "detail": "unlinked"})
        except OSError as exc:
            done.append({"id": asset.id, "link": str(link), "ok": False, "detail": str(exc)})
    return done


def describe(rows: list[dict]) -> str:
    lines = []
    for row in rows:
        state = "ready" if row["present"] else ("MISSING" if row["required"] else "absent")
        mark = {"ready": "[ok]  ", "MISSING": "[STOP]", "absent": "[opt] "}[state]
        lines.append(f"{mark} {row['id']:<9} {row['kind']:<10} {row['reason']}")
        if not row["present"] and row["absent_effect"]:
            lines.append(f"        -> {row['absent_effect']}")
    bad = blocking(rows)
    lines.append("")
    lines.append(f"{len(rows)} 项，{len(bad)} 项阻断" if bad else f"{len(rows)} 项，无阻断项")
    for row in bad:
        lines.append(f"  阻断：{row['id']} —— {row['absent_effect']}")
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(
        description="本地运行环境的单一清单：检查、补齐、复用")
    parser.add_argument("--check", action="store_true",
                        help="只读检查当前检出（默认行为）")
    parser.add_argument("--apply", metavar="WORKTREE", default="",
                        help="把需要的资产挂进指定检出")
    parser.add_argument("--release", metavar="WORKTREE", default="",
                        help="卸除指定检出里的挂载（不碰原字节）")
    parser.add_argument("--root", default=str(ROOT),
                        help="被检查的仓库根（默认本仓库）")
    parser.add_argument("--json", action="store_true", help="机器可读输出")
    args = parser.parse_args(argv)

    root = Path(args.root).resolve()

    if args.release:
        rows = release(Path(args.release).resolve())
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            for row in rows:
                print(f"{'[ok]' if row['ok'] else '[ERR]'} {row['id']}: {row['detail']}")
        return 0 if all(row["ok"] for row in rows) else 1

    if args.apply:
        rows = apply(Path(args.apply).resolve(), root)
        if args.json:
            print(json.dumps(rows, ensure_ascii=False, indent=1))
        else:
            for row in rows:
                print(f"{'[ok]' if row['ok'] else '[ERR]'} {row['id']}: {row['detail']}")
        return 0 if all(row["ok"] for row in rows) else 1

    rows = status(root)
    if args.json:
        print(json.dumps(rows, ensure_ascii=False, indent=1))
    else:
        print(describe(rows))
    return 2 if blocking(rows) else 0


if __name__ == "__main__":
    sys.exit(main())
