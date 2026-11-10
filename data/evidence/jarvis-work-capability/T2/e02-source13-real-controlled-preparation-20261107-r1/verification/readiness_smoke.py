"""Read actual sealed bytes in a disposable fixture; never grant live authority."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,sys
N=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
denied=[]
def audit(event,args):
    if event.startswith(('socket.','subprocess.')) or event in ('os.system','os.startfile','os.spawn','os.posix_spawn'):
        denied.append(event);raise RuntimeError('Readiness fixture forbids real operations')
sys.addaudithook(audit)
manifest=json.loads((N/'manifest.json').read_bytes());before={name:sha(N/name) for name in manifest['files']}
assert before==manifest['files']
run=N/'offline'/('sealed-readiness-'+dt.datetime.now(dt.timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
fixture=run/'fixture';fixture.mkdir(parents=True,exist_ok=False)
for name in manifest['files']:
    target=fixture/name;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((N/name).read_bytes())
(fixture/'manifest.json').write_bytes((N/'manifest.json').read_bytes())
save(fixture/'review/independent-preparation-review.json',dict(reviewer='root-independent',verdict='PASS_PREPARATION_ONLY',
    manifest_sha256=sha(fixture/'manifest.json'),actual_run_authorized=False,fixture_only=True))
save(fixture/'harness-approval.json',dict(reviewer='root-independent',overall='PASS',manifest_sha256=sha(fixture/'harness/manifest.json'),
    review_sha256=sha(fixture/'review/independent-preparation-review.json'),preparation_manifest_sha256=sha(fixture/'manifest.json')))
spec=importlib.util.spec_from_file_location('fixture_readiness_only',N/'code/entry.py')
entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
entry.N=fixture
result=entry.read_ready(fixture)
assert result['manifest_sha256']==sha(N/'manifest.json')
assert not (fixture/'release').exists() and not (N/'release').exists() and not (N/'actual').exists()
assert before=={name:sha(N/name) for name in manifest['files']} and not denied
receipt=dict(verdict='PASS_SEALED_READINESS_FIXTURE_ONLY',manifest_sha256=sha(N/'manifest.json'),members=len(before),
    source_bytes_unchanged=True,synthetic_review_only_inside=str(fixture),official_review_created=False,
    allocation_created=False,run_once_called=False,model_calls=0,product_calls=0,denied=denied)
save(run/'receipt.json',receipt)
print(json.dumps(dict(receipt=str(run/'receipt.json'),**receipt)))
