from pathlib import Path
import importlib.util
spec=importlib.util.spec_from_file_location('offline_readback',Path(__file__).with_name('verify_offline.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
N,C,BASE,ALLOWED,git,sha,save,verify=v.N,v.C,v.BASE,v.ALLOWED,v.git,v.sha,v.save,v.verify
parent='47ac3a464ca15e01311d5739eda53b2a32d8783c'
repair=['src/brain/work_research_diagnostics.py','src/brain/tests/test_work_output_structure_diagnostics.py']
assert git(C,'rev-parse','HEAD').decode().strip()==parent and not git(C,'diff','--cached','--name-only').strip()
checked=verify();save(N/'verification/offline-precommit-readback.json',checked)
assert set(git(C,'diff','--name-only',parent).decode().splitlines())==set(repair)
assert not git(C,'ls-files','--others','--exclude-standard').strip()
before={name:sha(C/name) for name in repair}
git(C,'--literal-pathspecs','add','--',*repair)
assert set(git(C,'diff','--cached','--name-only').decode().splitlines())==set(repair)
git(C,'diff','--cached','--check');git(C,'commit','-m','fix: enforce native diagnostic content state relationships')
head=git(C,'rev-parse','HEAD').decode().strip();tag='ultimaagent-e02-output-structure-candidate-20261108-r2'
assert not git(C,'tag','--list',tag).strip();git(C,'tag',tag)
for name,h in before.items():assert sha(C/name)==h and git(C,'show',head+':'+name)==(C/name).read_bytes()
assert not git(C,'status','--porcelain').strip()
save(N/'verification/candidate-freeze.json',dict(candidate=head,parent=parent,original_base=BASE,tag=tag,root=str(C),
    changed_files=repair,full_change_scope=ALLOWED,source_sha256=checked['source_sha256'],exact_committed_changed_bytes=True,
    working_tree_clean=True,actual_cases=0,model_calls=0))
print(head+' '+tag)
