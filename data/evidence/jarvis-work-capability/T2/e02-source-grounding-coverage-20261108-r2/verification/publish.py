"""Exact-path local publication; do not retry a previously blocked remote push."""
from pathlib import Path
import datetime as dt,importlib.util,json
N=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checks',N/'verification/verify_offline.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
R,C=v.R,v.C;M=Path('H:/UltimaAI/ultima-docs-repo');TAG='ultimaagent-e02-source-grounding-ready-20261108-r1'
manifest=v.load(N/'manifest.json');close=v.load(N/'verification/closeout-registration.json');review=v.load(N/'review/independent-preparation-review.json')
assert close['manifest_sha256']==review['manifest_sha256']==v.sha(N/'manifest.json')
assert close['review_sha256']==v.sha(N/'review/independent-preparation-review.json') and review['verdict']=='PASS_PREPARATION_ONLY'
for name,h in manifest['files'].items():assert v.sha(N/name)==h,name
v.verify();assert not v.git(C,'status','--porcelain').strip()
assert not v.git(R,'diff','--cached','--name-only').strip() and not v.git(M,'diff','--cached','--name-only').strip()
project={N/name for name in manifest['files']}
prior_root=N.parent/'e02-source-grounding-coverage-20261108-r1'
prior_manifest=v.load(prior_root/'manifest.json')
for name,h in prior_manifest['files'].items():assert v.sha(prior_root/name)==h,name
project.update(prior_root/name for name in prior_manifest['files'])
project.update(prior_root/name for name in ('manifest.json','review/independent-preparation-review.json','review/independent-preparation-review.md','progress.md'))
project.update(N/name for name in ('manifest.json','review/independent-preparation-review.json','review/independent-preparation-review.md','verification/closeout-registration.json','verification/queue-refresh.json','verification/queue-status-after.json','progress.md'))
project.update((N/'verification/closeout-before').iterdir())
project.update([R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'])
project.update(Path(x['source']) for x in close['mirror']);mirror={Path(x['target']) for x in close['mirror']}
for x in close['mirror']:assert v.sha(Path(x['source']))==v.sha(Path(x['target']))==x['sha256']
pathspec=N/'verification/publication-pathspec.txt';project.add(pathspec)
with pathspec.open('x',encoding='utf8',newline='\n') as f:f.write('\n'.join(sorted(p.relative_to(R).as_posix() for p in project))+'\n')
before=dict(project=v.git(R,'rev-parse','HEAD').decode().strip(),mirror=v.git(M,'rev-parse','HEAD').decode().strip())
assert before==dict(project='9ab8d0c6a064cd2bda557cf1f4e887e181ec9c57',mirror='db6d02f8a787780b1d0a8a9d41eb9bf6e3b36ab1')
hashes={str(p):v.sha(p) for p in project|mirror}
v.git(R,'add','-f','--pathspec-from-file='+str(pathspec))
assert set(v.git(R,'diff','--cached','--name-only').decode().splitlines())<={p.relative_to(R).as_posix() for p in project}
v.git(R,'diff','--cached','--check','--',*[Path(x['source']).relative_to(R).as_posix() for x in close['mirror']])
v.git(R,'commit','-m','docs(e02): seal evidence-first and source-reserve preparation');v.git(R,'tag',TAG)
v.git(M,'add','--',*[p.relative_to(M).as_posix() for p in sorted(mirror)])
assert set(v.git(M,'diff','--cached','--name-only').decode().splitlines())=={p.relative_to(M).as_posix() for p in mirror}
v.git(M,'diff','--cached','--check');v.git(M,'commit','-m','docs(e02): mirror source grounding offline preparation');v.git(M,'tag',TAG)
heads=dict(project=v.git(R,'rev-parse','HEAD').decode().strip(),mirror=v.git(M,'rev-parse','HEAD').decode().strip(),candidate=v.git(C,'rev-parse','HEAD').decode().strip())
for root,paths,key in ((R,project,'project'),(M,mirror,'mirror')):
    assert v.git(root,'rev-parse',TAG).decode().strip()==heads[key]
    for p in paths:assert v.sha(p)==hashes[str(p)] and v.git(root,'show',heads[key]+':'+p.relative_to(root).as_posix())==p.read_bytes(),str(p)
foreign=v.foreign_readback()
v.save(N/'verification/publication-readback.json',dict(verdict='PASS_LOCAL_PUBLICATION_READBACK',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),heads=heads,previous_heads=before,tag=TAG,project_members=len(project),mirror_members=len(mirror),file_sha256=hashes,manifest_sha256=v.sha(N/'manifest.json'),review_sha256=v.sha(N/'review/independent-preparation-review.json'),candidate_clean=True,foreign_files_unchanged=14,foreign_readback=foreign,actual_cases=0,model_calls=0,actual_allocation=0,remote_synced=False,remote_reason='Prior automatic approval rejected push: blocked by policy; no retry'))
print(json.dumps(dict(verdict='PASS_LOCAL_PUBLICATION_READBACK',heads=heads,tag=TAG,project_members=len(project),actual=0,remote_synced=False)))
