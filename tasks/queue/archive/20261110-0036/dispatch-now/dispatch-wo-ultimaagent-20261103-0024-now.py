#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""派发 wo-ultimaagent-20261103-0024（全盘理解 P0 索引链路）到 Codex（静默后台，对齐 0022 先例）
用法: python dispatch-wo-ultimaagent-20261103-0024-now.py
产出: runs/wo-ultimaagent-20261103-0024/<ts>/ 运行目录 + PID 打印 + 全局登记 executing
"""
import json
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(r"H:\UltimaAI\UltimaAgent")
SHARED = Path(r"H:\UltimaAI\_shared\queue")
ORDER = "wo-ultimaagent-20261103-0024"
PROMPT_FILE = ROOT / "tasks" / "queue" / "dispatch-wo-ultimaagent-20261103-0024-prompt.txt"
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
        print(json.dumps({'blocked': True, 'reason': '派发载荷缺失'}, ensure_ascii=False))
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
    refresh_registry('executing', f'真实工单派发 {run_dir.name}，一单一进程；Codex 自行分析方案并执行；尚未验收；规划 docs/plans/full-disk-understanding-delivery-plan-20261103.md')

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
    }
    (run_dir / "dispatch-record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(record, ensure_ascii=False))
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
