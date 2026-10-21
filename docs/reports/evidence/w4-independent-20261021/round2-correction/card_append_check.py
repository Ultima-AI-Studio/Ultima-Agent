import difflib,json
from pathlib import Path
ROOT=Path(r'H:\UltimaAI\UltimaAgent')
OUT=Path(__file__).resolve().parent
OLD=ROOT/'docs/reports/evidence/text-loop-development-20261021/round1/source'
result={};diff=[]
for tid in ('s1-task-intent-parse','s1-task-queue-source','s1-task-aggregate-report'):
    old=(OLD/'tasks/cards'/tid/'task.md').read_text(encoding='utf-8')
    new=(ROOT/'tasks/cards'/tid/'task.md').read_text(encoding='utf-8')
    result[tid]={'normalized_text_prefix':new.startswith(old)}
    diff.extend(difflib.unified_diff(old.splitlines(True),new.splitlines(True),fromfile='old/'+tid,tofile='current/'+tid))
with (OUT/'card-append-diff.txt').open('x',encoding='utf-8') as f:f.write(''.join(diff))
with (OUT/'card-append-check.json').open('x',encoding='utf-8') as f:json.dump(result,f,ensure_ascii=False,indent=2)
print(json.dumps(result))
