"""Preserve the predecessor evidence and dependencies without runtime changes."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,sys
N=Path(__file__).resolve().parents[1];R=N.parents[4]
P=N.parent/'e02-source-coverage-controlled-preparation-20261107-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    pin=json.loads((N/'inputs/predecessor.json').read_bytes())
    counts={}
    for name,key in [('manifest.json','manifest_sha256'),('review/result-inputs/result-manifest.json','result_manifest_sha256')]:
        assert sha(P/name)==pin[key],name
        files=json.loads((P/name).read_bytes())['files']
        for member,h in files.items():assert sha(P/member)==h,member
        counts[name]=len(files)
    for name,key in [('review/independent-result-review.json','result_review_sha256'),('verification/result-publication-readback.json','publication_sha256')]:
        assert sha(P/name)==pin[key],name
    inputs=json.loads((P/'inputs/input-manifest.json').read_bytes())['files']
    for name,h in inputs.items():assert sha(Path(name))==h,name
    for name,h in json.loads((N/'inputs/accepted-dependency-pins.json').read_bytes())['files'].items():
        assert sha(Path(name))==h,name
    foreign=json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files']
    for name,h in foreign.items():assert sha(R/name)==h,name
    c=pin['frozen_product']
    argv=['git','-C',c]
    head=subprocess.check_output(argv+['rev-parse','HEAD'],creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
    assert head==pin['candidate']
    assert not subprocess.check_output(argv+['status','--porcelain','--untracked-files=no'],creationflags=subprocess.CREATE_NO_WINDOW).strip()
    return dict(verdict='PASS_FROZEN_PREDECESSOR_AND_FOREIGN_PRESERVATION',counts=counts,
        predecessor_inputs=len(inputs),foreign_files=len(foreign),frozen_candidate=head,
        recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),model_calls=0,actual_calls=0)
if __name__=='__main__':
    value=verify()
    with (N/'verification/preservation-after.json').open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
    print(json.dumps(value))
