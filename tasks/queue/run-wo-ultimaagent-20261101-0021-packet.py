"""Run an evidence-packet review without enabling tools or opening a window."""
import json
import os
import subprocess
import sys
from pathlib import Path

root = Path(r'H:/UltimaAI/UltimaAgent')
packet = Path(sys.argv[1]).resolve()
final = Path(sys.argv[2]).resolve()
assert packet.is_relative_to(root / 'data/evidence/jarvis-work-capability/T0')
assert final.is_relative_to(root / 'tasks/queue/runs/wo-ultimaagent-20261101-0021')
environment = dict(os.environ)
environment.update(CODEX_HOME=r'C:\Users\Administrator\.codex-cli',
                   HTTP_PROXY='http://127.0.0.1:7897',
                   HTTPS_PROXY='http://127.0.0.1:7897',
                   NO_PROXY='127.0.0.1,localhost,::1')
command = [r'C:\Users\Administrator\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe',
           '-a', 'never', '--disable', 'apps', '--disable', 'plugins',
           '-c', 'model_reasoning_effort="high"',
           'exec', '-m', 'gpt-5.6-sol', '-C', str(root),
           '--sandbox', 'read-only', '--json', '--color', 'never',
           '--output-last-message', str(final), '-']
with packet.open('rb') as stream:
    process = subprocess.Popen(command, stdin=stream, stdout=sys.stdout.buffer,
                               stderr=sys.stderr.buffer, env=environment,
                               shell=False, creationflags=0x08000000)
    raise SystemExit(process.wait())
