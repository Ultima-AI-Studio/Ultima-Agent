from pathlib import Path
import hashlib, json, datetime

root = Path(__file__).resolve().parents[4]
out = Path(__file__).resolve().parent
paths = [
 'docs/INDEX.md', 'docs/specs/environment-spec.md',
 'tasks/queue/wo-s1-host-shell.md',
 'logs/environment-check-2026-10-21.md',
 'logs/host-shell-repair-20261021T061613/result.json',
 'logs/host-shell-repair-20261021T061613/t2-build.log',
 'logs/host-shell-repair-20261021T061613/t3-webview.json',
 'logs/host-shell-repair-20261021T061613/webview-render.png',
 'logs/host-shell-repair-20261021T061613/t3-webview-render.png',
 'logs/host-shell-reviewfix-20261021T065131/final-report.md',
 'logs/host-shell-reviewfix-20261021T065131/final-receipt-v2.json',
 'logs/w1-native-2026-10-21T02-26-42-926Z/native-window.png',
 'logs/w1-native-2026-10-21T02-26-42-926Z/native-window.json',
]
paths += [str(p.relative_to(root)).replace('\\','/') for p in (root/'tasks/cards').glob('s1-host-shell-*/task.md')]
manifest = {}
for rel in paths:
    data = (root/rel).read_bytes()
    dest = out/'round1'/rel
    dest.parent.mkdir(parents=True, exist_ok=True)
    dest.write_bytes(data)
    manifest[rel] = {'sha256':hashlib.sha256(data).hexdigest(), 'bytes':len(data)}
result = {'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),
 'auditor':'/root/w1_acceptance','round':1,'mode':'read-only precheck of existing evidence',
 'U01':'PASS_HOST_STAGE_ENVIRONMENT_GATE','W1':'PENDING_FINAL_RUNTIME_DPI_AND_BUILD',
 'ran_build':False,'launched_app':False,'controlled_window':False,'stopped_process':False,
 'sources':manifest}
(out/'round1/result.json').write_text(json.dumps(result,ensure_ascii=False,indent=2),encoding='utf-8')
print(json.dumps({'U01':result['U01'],'W1':result['W1'],'source_count':len(manifest)},ensure_ascii=False))
