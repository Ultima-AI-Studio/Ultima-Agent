"""Preserve first-round text sources before a separately reviewed correction."""
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / 'docs/reports/evidence/text-loop-development-20261021/round1'
OUT.mkdir(parents=True, exist_ok=False)
paths = [p for p in (ROOT / 'src/brain').rglob('*') if p.is_file() and p.suffix in {'.py', '.md'}]
for card in ['s1-task-intent-parse', 's1-task-queue-source', 's1-task-aggregate-report']:
    paths += list((ROOT / 'tasks/cards' / card).glob('*.md'))
manifest = {}
for path in paths:
    relative = path.relative_to(ROOT)
    content = path.read_bytes()
    target = OUT / 'source' / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(content)
    digest = hashlib.sha256(content).hexdigest()
    assert hashlib.sha256(target.read_bytes()).hexdigest() == digest
    manifest[str(relative)] = digest
with (OUT / 'source-manifest.json').open('x', encoding='utf-8') as stream:
    json.dump(manifest, stream, ensure_ascii=False, indent=2)
print(json.dumps({'files': len(manifest), 'snapshot': str(OUT)}, ensure_ascii=False))
