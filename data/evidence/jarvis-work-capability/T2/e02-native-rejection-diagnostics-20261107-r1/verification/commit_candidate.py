from pathlib import Path
import hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];C=Path(json.loads((N/'inputs/worktree.json').read_bytes())['root'])
checked=json.loads((N/'verification/offline-readback.json').read_bytes());files=checked['changed_files']
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW)
assert checked['tests']==909 and checked['verdict']=='PASS_FRESH_OFFLINE_CURRENT_BYTES'
assert git('rev-parse','HEAD').decode().strip()==checked['base']
assert not git('diff','--cached','--name-only').strip()
git('diff','--check');git('add','--',*files)
assert set(git('diff','--cached','--name-only').decode().splitlines())==set(files)
git('diff','--cached','--check')
git('commit','-m','fix(research): retain bounded request-bound native refusal reasons')
tag='ultimaagent-e02-native-rejection-candidate-20261107';git('tag',tag)
head=git('rev-parse','HEAD').decode().strip()
assert not git('status','--porcelain').strip() and git('rev-parse',tag).decode().strip()==head
for name in files:assert git('show',head+':'+name)==(C/name).read_bytes()
with (N/'verification/candidate-commit.json').open('x',encoding='utf8') as f:json.dump(dict(candidate=head,parent=checked['base'],tag=tag,files=files,exact_committed_bytes=True),f,indent=2)
print(json.dumps(dict(candidate=head,tag=tag,files=len(files))))
