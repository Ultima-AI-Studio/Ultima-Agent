from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
red=load(N/'cold-evidence/red-1/receipt.json');green=load(N/'cold-evidence/green-1/receipt.json')
assert red['counts']==dict(tests=4,failures=2,errors=0,skipped=0) and red['sources_unchanged']
assert green['counts']==dict(tests=4,failures=0,errors=0,skipped=0) and green['sources_unchanged']
assert {r['result']['role'] for r in red['probe_results']}=={'worker','reader'}
for row in red['probe_results']:
    r=row['result'];assert r['outcome']=='FAIL' and r['error']=='Unexpected audited operation' and r['audit_events']==['socket.gethostname']
for row in green['probe_results']:
    r=row['result'];assert r['outcome']=='PASS' and r['eager_audit']['eager']['clean'] and r['eager_audit']['eager']['closed'] and not r['refused_io']
assert sha(N/'profile-preparation/profile.py')==green['after'][str(N/'profile-preparation/profile.py')]
baseline=load(N/'inputs/preserved-before.json')['files']
assert all(sha(Path(p))==v for p,v in baseline.items())
print(json.dumps(dict(result='PASS',red_failed_roles=2,green_passed_roles=2,old_bindings_unchanged=len(baseline),actual_profile_runs=0)))
