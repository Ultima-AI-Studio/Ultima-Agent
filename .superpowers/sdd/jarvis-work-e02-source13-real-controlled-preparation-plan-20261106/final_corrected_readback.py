"""Read only after the independent preparation report; never consumes runtime."""
from pathlib import Path
import hashlib,importlib.util,json,subprocess
R=Path(r'H:\UltimaAI\UltimaAgent');M=Path(r'H:\UltimaAI\ultima-docs-repo')
N=R/'data/evidence/jarvis-work-capability/T2/e02-source13-real-controlled-preparation-20261107-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
spec=importlib.util.spec_from_file_location('source13_preparation_readback',N/'code/entry.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
package=entry.read_ready(N)
old=N.parent/'e02-source13-real-controlled-preparation-20261106'
assert sha(old/'manifest.json')=='9f7ffce882e07861fd83c043e85ffdaa586b37dfb1041135d12c688996388964'
assert sha(old/'review/independent-preparation-review.json')=='5dbb5c54eb38b5c8e4b04cb7e280cf7d5c9dd2e057dedeea20eac1999da4220f'
for name,digest in load(old/'manifest.json')['files'].items():assert sha(old/name)==digest,name
for name in ('entry.py','bindings.py'):assert sha(N/'code'/name)==sha(old/'code'/name),name
for p in (N/'harness').iterdir():assert sha(p)==sha(old/'harness'/p.name),p
smoke=load(sorted((N/'offline').glob('sealed-readiness-*/receipt.json'))[-1])
assert smoke['verdict']=='PASS_SEALED_READINESS_FIXTURE_ONLY' and smoke['manifest_sha256']==sha(N/'manifest.json')
assert smoke['members']==190 and not smoke['allocation_created'] and not smoke['run_once_called'] and not smoke['denied']
assert not (N/'release').exists() and not (N/'actual').exists()
for p,digest in load(N/'manifest.json')['files'].items():assert sha(N/p)==digest,p
for p,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/p)==digest,p
review=load(N/'review/independent-preparation-review.json')
assert review['verdict']=='PASS_PREPARATION_ONLY' and not review['actual_run_authorized'] and not review['acceptance_credit']
assert not review.get('findings') and review['tests_run']==review['runtime_calls']==0
bound=load(N/'inputs/input-manifest.json')
for p,digest in bound['files'].items():assert sha(Path(p))==digest,p
assert load(N/'offline/entry-review-green/receipt.json')['result']['tests']==26
C=Path(bound['candidate_root'])
assert subprocess.check_output(['git','-C',str(C),'rev-parse','HEAD'],text=True).strip()==bound['candidate']
assert not subprocess.check_output(['git','-C',str(C),'status','--porcelain','--untracked-files=no'],text=True).strip()
print(json.dumps(dict(verdict='PASS_PREPARATION_ONLY',package=package,tests=270,independent_review=True,
    current_candidate=bound['candidate'],current_model=bound['model'],actual_case_allocation=0,result_review_allocation=0,
    actual_product_runs_this_preparation=0,model_calls_this_preparation=0,E02='NOT_PASSED',T2='NOT_PASSED',remote_synced=False)))
