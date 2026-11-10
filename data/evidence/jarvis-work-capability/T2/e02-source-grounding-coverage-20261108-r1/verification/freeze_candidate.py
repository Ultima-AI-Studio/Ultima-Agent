"""Commit only the eight scoped paths after fresh offline verification."""
from pathlib import Path
import importlib.util,json
N=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('offline_checks',N/'verification/verify_offline.py')
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
checked=v.verify();v.save(N/'verification/offline-precommit-readback.json',checked)
assert v.git(v.C,'rev-parse','HEAD').decode().strip()==v.BASE
assert not v.git(v.C,'diff','--cached','--name-only').strip()
v.git(v.C,'diff','--check','--',*v.ALLOWED)
v.git(v.C,'add','--',*v.ALLOWED)
assert set(v.git(v.C,'diff','--cached','--name-only').decode().splitlines())==set(v.ALLOWED)
v.git(v.C,'commit','-m','fix(research): select evidence before claims and reserve unread sources')
tag='ultimaagent-e02-source-grounding-candidate-20261108-r1';v.git(v.C,'tag',tag)
head=v.git(v.C,'rev-parse','HEAD').decode().strip()
assert v.git(v.C,'rev-parse','HEAD^').decode().strip()==v.BASE and not v.git(v.C,'status','--porcelain').strip()
v.save(N/'verification/candidate-freeze.json',dict(candidate=head,parent=v.BASE,tag=tag,tests=checked['tests'],paths=list(v.ALLOWED),source_sha256={p:v.sha(v.C/p) for p in v.ALLOWED},actual_authority=False))
print(json.dumps(dict(candidate=head,parent=v.BASE,tag=tag,tests=checked['tests'],actual_allocation=0)))
