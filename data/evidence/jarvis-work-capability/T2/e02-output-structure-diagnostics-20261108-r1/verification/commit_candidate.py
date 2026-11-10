"""Commit only the four reviewed-scope files after fresh offline readback."""
from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('offline_readback',Path(__file__).with_name('verify_offline.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
N,C,BASE,ALLOWED,git,sha,save,verify=v.N,v.C,v.BASE,v.ALLOWED,v.git,v.sha,v.save,v.verify
assert git(C,'rev-parse','HEAD').decode().strip()==BASE
assert not git(C,'diff','--cached','--name-only').strip()
checked=verify()
save(N/'verification/offline-precommit-readback.json',checked)
changed=set(git(C,'diff','--name-only',BASE).decode().splitlines())
untracked=set(git(C,'ls-files','--others','--exclude-standard').decode().splitlines())
assert changed|untracked==set(ALLOWED),(changed,untracked)
before={name:sha(C/name) for name in ALLOWED}
git(C,'--literal-pathspecs','add','--',*ALLOWED)
assert set(git(C,'diff','--cached','--name-only').decode().splitlines())==set(ALLOWED)
git(C,'diff','--cached','--check')
git(C,'commit','-m','fix: retain bounded structure evidence for native research refusals')
head=git(C,'rev-parse','HEAD').decode().strip();tag='ultimaagent-e02-output-structure-candidate-20261108'
assert not git(C,'tag','--list',tag).strip();git(C,'tag',tag)
for name,h in before.items():assert sha(C/name)==h and git(C,'show',head+':'+name)==(C/name).read_bytes()
assert not git(C,'status','--porcelain').strip()
save(N/'verification/candidate-freeze.json',dict(candidate=head,parent=BASE,tag=tag,root=str(C),
    changed_files=ALLOWED,source_sha256=checked['source_sha256'],exact_committed_changed_bytes=True,
    working_tree_clean=True,actual_cases=0,model_calls=0))
print(head+' '+tag)
