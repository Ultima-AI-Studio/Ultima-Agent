"""Record an out-of-scope change without touching its file or accepting source drift."""
from pathlib import Path
import datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1];R=N.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
original=json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files']
changed={name:sha(R/name) for name,h in original.items() if sha(R/name)!=h}
assert set(changed)=={'docs/tracker/北极星上线任务清单.html'}
snap=N/'inputs/unrelated-observed';snap.mkdir(exist_ok=False)
records={}
for name,h in changed.items():
    p=R/name;target=snap/p.name;raw=p.read_bytes();assert hashlib.sha256(raw).hexdigest()==h
    with target.open('xb') as f:f.write(raw)
    assert sha(p)==h
    records[name]=dict(baseline_sha256=original[name],observed_sha256=h,snapshot=str(target),mtime_ns=p.stat().st_mtime_ns,bytes=len(raw))
value=dict(kind='OUT_OF_SCOPE_FILE_CHANGE_OBSERVED_NOT_OWNED',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),baseline_manifest_sha256=sha(N/'inputs/unrelated-working-tree.json'),baseline_matches=14,observed_changes=records,source='Detected by precommit preservation guard; no tool in this repair wrote this path',attribution='UNDETERMINED',policy='Keep original baseline immutable and current bytes untouched; only this exact unowned file may match its separately recorded observed hash; all product/dependency/failure pins stay strict',actual_cases=0)
with (N/'inputs/unrelated-change-observation.json').open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(baseline_matches=14,observed=records),ensure_ascii=False))
