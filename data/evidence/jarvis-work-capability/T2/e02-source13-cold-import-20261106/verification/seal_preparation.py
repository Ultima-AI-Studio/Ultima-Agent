from pathlib import Path
import datetime as dt,difflib,hashlib,json
N=Path(__file__).resolve().parents[1];T=N.parent;repo=N.parents[4]
B=T/'e02-source13-profile-binding-20261106';E=T/'e02-source13-root-entry-20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,d):
    with p.open('x',encoding='utf-8') as f:json.dump(d,f,ensure_ascii=False,indent=2)
assert load(N/'verification/offline-readback.json')['verdict']=='PASS_OFFLINE_PREPARATION_ONLY'
assert not (N/'manifest.json').exists() and not (N/'release').exists() and not (N/'runs').exists()
plan=repo/'docs/plans/jarvis-work-e02-source13-sdk-cold-import-fix-plan-20261106.md'
(N/'plan.md').write_bytes(plan.read_bytes())
parts=[]
for old,new in [(B/'profile-preparation/profile.py',N/'profile-preparation/profile.py'),(B/'profile-preparation/test_profile.py',N/'profile-preparation/test_profile.py')]+[(E/'code'/n,N/'code'/n) for n in ('controls.py','entry.py')]+[(E/'verification'/n,N/'verification'/n) for n in ('execute-profile-once.py','profile-once-preflight.py','profile-once-postcheck.py')]:
    parts.extend(difflib.unified_diff(old.read_text('utf-8').splitlines(True),new.read_text('utf-8').splitlines(True),fromfile=str(old),tofile=str(new)))
(N/'verification/scoped-source.diff').write_text(''.join(parts),encoding='utf-8')
members={p for sub in ('inputs','verification','profile-preparation','cold') for p in (N/sub).iterdir() if p.is_file()}
members.update(p for p in (N/'code').glob('*.py'))
members.update(N/name for name in ('README.md','execution-proposal.md','plan.md','entry-manifest.json','profile-adapter.py'))
for base,pattern in [(N/'cold-evidence','*'),(N/'offline','*'),(N/'code','profile-preparation-contracts-*')]:
    for stage in base.glob(pattern):
        if not stage.is_dir():continue
        members.update(p for p in stage.iterdir() if p.is_file())
        if (stage/'snapshot').is_dir():members.update(p for p in (stage/'snapshot').iterdir() if p.is_file())
        if (stage/'temp').exists():
            for p in (stage/'temp').rglob('result.json'):
                if p.parent.name.startswith('test_real_sdk_cold_import'):
                    members.add(p);members.update(q for q in p.parent.iterdir() if q.is_file() and q.name in ('stdout.txt','stderr.txt'))
files=[dict(path=p.relative_to(N).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(members)]
save(N/'manifest.json',dict(schema=1,scope='SOURCE13_E02_COLD_IMPORT_PREPARATION',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    runtime_authority=False,entry_manifest_sha256=sha(N/'entry-manifest.json'),files=files))
print(json.dumps(dict(package_manifest_sha256=sha(N/'manifest.json'),entry_manifest_sha256=sha(N/'entry-manifest.json'),members=len(files))))
