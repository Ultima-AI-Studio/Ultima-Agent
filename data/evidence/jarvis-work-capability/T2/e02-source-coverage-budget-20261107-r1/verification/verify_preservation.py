"""Verify frozen predecessor, dependency pins and unrelated files without runtime actions."""
from pathlib import Path
import datetime as dt, hashlib, importlib.util, json, sys

N=Path(__file__).resolve().parents[1]
P=N.parent/'e02-native-http-controlled-preparation-20261107-r1'

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()

def verify():
    pred=json.loads((N/'inputs/predecessor.json').read_bytes())
    manifests={'manifest.json':'manifest_sha256',
               'review/result-inputs/result-manifest.json':'result_manifest_sha256'}
    counts={}
    for name,key in manifests.items():
        assert sha(P/name)==pred[key],name
        files=json.loads((P/name).read_bytes())['files']
        for member,digest in files.items():assert sha(P/member)==digest,member
        counts[name]=len(files)
    for name,key in [('review/independent-result-review.json','result_review_sha256'),
                     ('verification/result-publication-readback.json','publication_sha256')]:
        assert sha(P/name)==pred[key],name
    pins=json.loads((N/'inputs/accepted-dependency-pins.json').read_bytes())['files']
    for name,digest in pins.items():assert sha(Path(name))==digest,name
    spec=importlib.util.spec_from_file_location('frozen_predecessor_preservation',P/'verification/verify_preservation.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old)
    prior=old.verify()
    return dict(verdict='PASS_FROZEN_PRESERVATION',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                predecessor_manifests=counts,dependency_pins=len(pins),prior=prior,
                actual_cases=0,model_calls=0)

if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('before','after')
    value=verify()
    with (N/'verification'/('preservation-'+sys.argv[1]+'.json')).open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
    print(json.dumps({k:v for k,v in value.items() if k!='prior'}))
