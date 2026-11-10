#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""续跑派发 wo-ultimaagent-20261103-0025（resume：T2/T3 续跑，T0/T1 已 PASS 勿重做）到 Codex（静默后台）
用法: python dispatch-wo-ultimaagent-20261103-0025-resume-now.py
产出: runs/wo-ultimaagent-20261103-0025/<ts>/ 运行目录 + PID 打印 + 全局登记 executing
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"H:\UltimaAI\UltimaAgent")
SHARED = Path(r"H:\UltimaAI\_shared\queue")
ORDER = "wo-ultimaagent-20261103-0025"
PROMPT_FILE = ROOT / "tasks" / "queue" / "dispatch-wo-ultimaagent-20261103-0025-resume-prompt.txt"
RUNS_ROOT = ROOT / "tasks" / "queue" / "runs"
CODEX = r"C:\Users\Administrator\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe"
REGISTRY = SHARED / "global-queue-index.md"


def refresh_registry(state: str, note: str) -> None:
    registry = REGISTRY
    raw = registry.read_bytes()
    lines = raw.splitlines(keepends=True)
    selected = [i for i, line in enumerate(lines) if ('| '+ORDER+' |').encode() in line]
    assert len(selected) == 1, f'登记行异常: {len(selected)}'
    newline = b'\r\n' if lines[selected[0]].endswith(b'\r\n') else b'\n'
    lines[selected[0]] = (f'| UltimaAgent | {ORDER} | {state} | {note} |').encode('utf-8') + newline
    temporary = registry.with_name(registry.name + '.middleware.tmp')
    temporary.write_bytes(b''.join(lines)); temporary.replace(registry)
    assert ('| '+ORDER+' | '+state+' |').encode('utf-8') in registry.read_bytes(), '登记回读核对失败'


def main() -> int:
    if not PROMPT_FILE.is_file():
        print(json.dumps({'blocked': True, 'reason': '续跑派发载荷缺失'}, ensure_ascii=False))
        return 2
    if (ROOT / 'tasks/.pause-dispatch').exists() or (SHARED / '.pause-dispatch').exists():
        print(json.dumps({'blocked': True, 'reason': '派发暂停标记存在'}, ensure_ascii=False))
        return 2
    run_dir = RUNS_ROOT / ORDER / datetime.now(timezone.utc).strftime("%Y%m%dT%H%M%S%fZ")
    run_dir.mkdir(parents=True, exist_ok=True)

    prompt = PROMPT_FILE.read_text(encoding="utf-8")
    out_log = run_dir / "dispatch.out.log"
    err_log = run_dir / "dispatch.err.log"
    final = run_dir / "final-message.json"

    cmd = [
        CODEX, "-a", "never",
        "-c", 'model_reasoning_effort="high"',
        "exec", "-m", "gpt-5.6-sol",
        "-C", str(ROOT),
        "--sandbox", "danger-full-access",
        "--skip-git-repo-check",
        "--json", "--color", "never",
        "--output-last-message", str(final),
        "-",
    ]

    # 启动前登记 executing（幂等、回读核对）
    refresh_registry('executing', f'0025 续跑派发 {run_dir.name}（T0/T1 已 PASS，续跑 T2 完整门+T3 回执；首轮 T2 38% 会话中断）')

    with open(out_log, "wb") as fo, open(err_log, "wb") as fe:
        p = subprocess.Popen(
            cmd, stdin=subprocess.PIPE, stdout=fo, stderr=fe,
            creationflags=subprocess.CREATE_NO_WINDOW,
        )
        p.stdin.write(prompt.encode("utf-8"))
        p.stdin.close()

    record = {
        "order": ORDER,
        "dispatch_ts": datetime.now(timezone.utc).isoformat(),
        "pid": p.pid,
        "model": "gpt-5.6-sol",
        "run_dir": str(run_dir),
        "prompt_file": str(PROMPT_FILE),
        "final_message": str(final),
        "resume_of": "20261104T023556251345Z",
    }
    (run_dir / "dispatch-record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
