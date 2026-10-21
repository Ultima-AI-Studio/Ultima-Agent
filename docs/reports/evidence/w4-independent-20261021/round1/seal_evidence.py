import hashlib, json
from pathlib import Path
ROOT=Path(r'H:\UltimaAI\UltimaAgent')
OUT=Path(__file__).resolve().parent
mapping={
 'logs/queue-engine-regression-2026-10-21.txt':'original-queue-engine-first-failure.txt',
 'logs/queue-engine-regression-targeted-retry-2026-10-21.txt':'original-queue-engine-targeted-retry.txt',
 'logs/queue-engine-regression-retry-2026-10-21.txt':'original-queue-engine-full-retry.txt',
 'logs/execution-reports/wo-s1-task-text-loop/summary.json':'original-developer-summary.json'}
for src,dst in mapping.items():
    with (OUT/dst).open('xb') as f:f.write((ROOT/src).read_bytes())
files={str(p.relative_to(OUT)):hashlib.sha256(p.read_bytes()).hexdigest() for p in OUT.rglob('*') if p.is_file()}
with (OUT/'evidence-sha256.json').open('x',encoding='utf-8') as f:json.dump(files,f,indent=2)
print(json.dumps({'sealed_files':len(files),'manifest':'evidence-sha256.json'}))
