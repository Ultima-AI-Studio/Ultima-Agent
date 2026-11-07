"""Read-only preservation checks, reusable before and after implementation."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,sys
N=Path(__file__).resolve().parents[1];R=N.parents[4]
P=N.parent/'e02-unique-sections-20261107-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    refs=json.loads((N/'inputs/predecessor.json').read_bytes())
    manifests=[(P/'manifest.json',refs['manifest_sha256']),(P/'review/result-inputs/result-manifest.json',refs['result_manifest_sha256']),(P/'review/native-log-supplement/manifest.json',refs['supplemental_manifest_sha256'])]
    counts={}
    for path,expected in manifests:
        assert sha(path)==expected,str(path)
        files=json.loads(path.read_bytes())['files']
        for name,digest in files.items():assert sha(P/name)==digest,name
        counts[str(path)]=len(files)
    assert sha(P/'review/independent-result-review.json')==refs['result_review_sha256']
    pins=json.loads((N/'inputs/accepted-dependency-pins.json').read_bytes())
    for name,digest in pins['files'].items():assert sha(Path(name))==digest,name
    foreign=json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files']
    for name,digest in foreign.items():assert sha(R/name)==digest,name
    old=Path(refs['candidate_root'])
    proc=lambda *args:subprocess.check_output(['git','-C',str(old),*args],creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()
    assert proc('rev-parse','HEAD')==refs['candidate']
    assert not proc('status','--porcelain')
    return dict(verdict='PASS_PRESERVATION',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),manifests=counts,old_inputs=len(pins['files']),foreign_files=len(foreign),old_candidate=refs['candidate'],old_candidate_clean=True,actual_cases=0,model_calls=0)
if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('before','after')
    value=verify();path=N/'verification'/('preservation-'+sys.argv[1]+'.json')
    with path.open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
    print(json.dumps(value))
