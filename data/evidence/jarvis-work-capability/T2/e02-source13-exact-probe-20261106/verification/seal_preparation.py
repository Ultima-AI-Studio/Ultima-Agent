from pathlib import Path
import datetime as dt,difflib,hashlib,json
Q=Path(__file__).resolve().parents[1];T=Q.parent;R=Q.parents[4];S=T/'e02-source13-audit-closeout-20261106';B=T/'e02-source13-cold-import-20261106';D=T/'e02-source13-closeout-handoff-20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
assert load(Q/'verification/offline-readback.json')['verdict']=='PASS_OFFLINE_PREPARATION_ONLY'
assert not (Q/'manifest.json').exists() and not (Q/'release').exists() and not (Q/'runs').exists()
(Q/'plan.md').write_bytes((R/'docs/plans/jarvis-work-e02-source13-exact-probe-repair-plan-20261106.md').read_bytes())
(Q/'inputs/independent-handoff-review.json').write_bytes((D/'independent-handoff-review.json').read_bytes())
(Q/'inputs/external-manifest-audit.json').write_bytes((D/'inputs/manifest-audit.json').read_bytes())
chunks=[]
for old,new in [(S/'profile-preparation/profile.py',Q/'profile-preparation/profile.py'),(S/'profile-preparation/test_profile.py',Q/'profile-preparation/test_profile.py')]+[(B/'code'/n,Q/'code'/n) for n in ('entry.py','controls.py')]:
    chunks.extend(difflib.unified_diff(old.read_text('utf-8').splitlines(True),new.read_text('utf-8').splitlines(True),fromfile=str(old),tofile=str(new)))
(Q/'verification/scoped-source.diff').write_text(''.join(chunks),encoding='utf-8')
members={p for sub in ('inputs','profile-preparation','verification','cold') for p in (Q/sub).iterdir() if p.is_file()}
members.update(Q/name for name in ('entry-manifest.json','README.md','execution-proposal.md','profile-adapter.py','plan.md'))
members.update(p for p in (Q/'code').glob('*.py'))
for base,pattern in [(Q/'offline','*'),(Q/'code','profile-preparation-contracts-*')]:
    for stage in base.glob(pattern):
        if not stage.is_dir():continue
        members.update(p for p in stage.iterdir() if p.is_file())
        if (stage/'snapshot').exists():members.update(p for p in (stage/'snapshot').iterdir() if p.is_file())
        if (stage/'temp').exists():
            for name in ('result.json','probe.json'):
                for p in (stage/'temp').rglob(name):
                    if p.parent.name.startswith(('test_real_sdk_cold_import','test_real_urllib3_probe')):
                        members.add(p);members.update(q for q in p.parent.iterdir() if q.is_file() and q.name in ('stdout.txt','stderr.txt'))
value=dict(schema=1,scope='SOURCE13_E02_EXACT_IPV6_PROBE_PREPARATION',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),runtime_authority=False,
    entry_manifest_sha256=sha(Q/'entry-manifest.json'),files=[dict(path=p.relative_to(Q).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(members)])
with (Q/'manifest.json').open('x',encoding='utf-8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(manifest_sha256=sha(Q/'manifest.json'),entry_manifest_sha256=value['entry_manifest_sha256'],members=len(members))))
