from pathlib import Path
import hashlib,importlib.util,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');M=Path('H:/UltimaAI/ultima-docs-repo')
N=R/'data/evidence/jarvis-work-capability/T2/e02-source-reference-schema-20261107-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args])
checkpoint=load(N/'verification/ready-checkpoint.json')
for repo,key in ((R,'main'),(M,'mirror')):
    rec=checkpoint[key]
    assert git(repo,'rev-parse','HEAD').decode().strip()==rec['commit']
    assert git(repo,'rev-parse','refs/tags/'+rec['tag']+'^{commit}').decode().strip()==rec['commit']
    for name in rec['files']:assert git(repo,'show',rec['commit']+':'+name)==(repo/name).read_bytes(),name
for row in load(N/'verification/ready-mirror-readback.json')['mirrors']:assert sha(Path(row['source']))==sha(Path(row['mirror']))==row['sha256']
for name,digest in load(N/'manifest.json')['files'].items():assert sha(N/name)==digest,name
for name,digest in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
spec=importlib.util.spec_from_file_location('final_ready_entry',N/'code/entry.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
ready=entry.read_ready(N)
assert not (N/'release').exists() and not (N/'actual').exists()
value=dict(verdict='PASS_COMMITTED_PREPARATION_READBACK_ONLY',main=checkpoint['main']['commit'],mirror=checkpoint['mirror']['commit'],**ready,actual_released=False,tests_repeated=0)
with (N/'verification/final-ready-readback.json').open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
print(json.dumps(value))
