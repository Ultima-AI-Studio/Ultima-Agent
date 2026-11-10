#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""派发 wo-ultimaagent-20261030-0007 到 Codex（静默后台，对齐 0005 先例）
用法: python dispatch-wo-0007-now.py
产出: runs/wo-ultimaagent-20261030-0007/<ts>/ 运行目录 + PID 打印
"""
import json
import subprocess
from datetime import datetime
from pathlib import Path

ROOT = Path(r"H:\UltimaAI\UltimaAgent")
ORDER = "wo-ultimaagent-20261030-0007"
PROMPT_FILE = ROOT / "tasks" / "queue" / "dispatch-wo-ultimaagent-20261030-0007-prompt.txt"
RUNS_ROOT = ROOT / "tasks" / "queue" / "runs"
CODEX = r"C:\Users\Administrator\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe"

run_dir = RUNS_ROOT / f"{ORDER}" / datetime.now().strftime("%Y%m%dT%H%M%S%fZ")
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

with open(out_log, "wb") as fo, open(err_log, "wb") as fe:
    p = subprocess.Popen(
        cmd, stdin=subprocess.PIPE, stdout=fo, stderr=fe,
        creationflags=subprocess.CREATE_NO_WINDOW,
    )
    p.stdin.write(prompt.encode("utf-8"))
    p.stdin.close()

record = {
    "order": ORDER,
    "dispatch_ts": datetime.now().isoformat(),
    "pid": p.pid,
    "model": "gpt-5.6-sol",
    "run_dir": str(run_dir),
    "prompt_file": str(PROMPT_FILE),
    "final_message": str(final),
}
(run_dir / "dispatch-record.json").write_text(json.dumps(record, ensure_ascii=False, indent=2), encoding="utf-8")
print(json.dumps(record, ensure_ascii=False))
