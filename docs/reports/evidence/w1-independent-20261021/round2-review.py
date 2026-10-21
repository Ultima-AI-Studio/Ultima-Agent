from pathlib import Path
import datetime, hashlib, json
root=Path(__file__).resolve().parents[4]
out=Path(__file__).resolve().parent/'round2-preliminary'
sources=list((root/'src/host-shell/UltimaAgent.HostShell').glob('*.cs'))
base=root/'logs/w1-host-resume-20261021T024845Z'
for directory in ['t2-initial-reproduction-attempt3','t3-final-build','t3-final-build-attempt2','t3-dpi-final','t3-webview']:
    sources.extend(p for p in (base/directory).glob('*') if p.is_file())
manifest={}
for p in sources:
    rel=p.relative_to(root)
    data=p.read_bytes()
    dest=out/rel
    dest.parent.mkdir(parents=True,exist_ok=True)
    dest.write_bytes(data)
    manifest[str(rel)]={'sha256':hashlib.sha256(data).hexdigest(),'bytes':len(data)}
(out/'result.json').write_text(json.dumps({'at_utc':datetime.datetime.now(datetime.timezone.utc).isoformat(),'scope':'read-only preliminary source and evidence review; NOT final W1','auditor':'/root/w1_acceptance','sources':manifest},ensure_ascii=False,indent=2),encoding='utf-8')
print(len(manifest))
