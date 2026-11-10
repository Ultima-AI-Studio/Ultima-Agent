"""Read frozen product/predecessor bytes; never run a model or actual case."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess,sys
N=Path(__file__).resolve().parents[1]
P=N.parent/'e02-writer-output-budget-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-budget/UltimaAgent')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def verify():
    pred=json.loads((N/'inputs/predecessor.json').read_bytes())
    for name,key in [('manifest.json','manifest_sha256'),('review/independent-preparation-review.json','review_sha256'),('verification/publication-readback.json','publication_sha256')]:
        assert sha(P/name)==pred[key],name
    members=json.loads((P/'manifest.json').read_bytes())['files']
    for name,digest in members.items():assert sha(P/name)==digest,name
    current=json.loads((P/'inputs/current-inputs.json').read_bytes())['files']
    for name,digest in current.items():assert sha(Path(name))==digest,name
    for name,h in json.loads((N/'inputs/product-closeout-supplements.json').read_bytes())['files'].items():assert sha(Path(name))==h,name
    for name,h in json.loads((N/'inputs/unrelated-working-tree.json').read_bytes())['files'].items():assert sha(N.parents[4]/name)==h,name
    spec=importlib.util.spec_from_file_location('frozen_prior_preservation',P/'verification/verify_preservation.py')
    old=importlib.util.module_from_spec(spec);spec.loader.exec_module(old);prior=old.verify()
    git=lambda *args:subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()
    assert git('rev-parse','HEAD')==git('rev-parse','ultimaagent-e02-output-budget-candidate-20261107')==pred['candidate']
    assert not git('status','--porcelain')
    return dict(verdict='PASS_PRODUCT_AND_PREDECESSOR_PRESERVATION',candidate=pred['candidate'],product_clean=True,
                product_preparation_members=len(members),current_input_pins=len(current),prior=prior,
                actual_cases=0,model_calls=0,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('before','after')
    value=verify()
    with (N/'verification'/('preservation-'+sys.argv[1]+'.json')).open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
    print(json.dumps({k:v for k,v in value.items() if k!='prior'}))
