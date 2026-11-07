"""Read frozen diagnostic product and all retained failures; no product execution."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess,sys
N=Path(__file__).resolve().parents[1]
P=N.parent/'e02-output-structure-diagnostics-20261108-r2'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure-r2/UltimaAgent')
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def verify():
    pred=load(N/'inputs/predecessor.json')
    for name,key in [('manifest.json','manifest_sha256'),('review/independent-preparation-review.json','review_sha256'),('verification/publication-readback.json','publication_sha256')]:
        assert sha(P/name)==pred[key],name
    members=load(P/'manifest.json')['files']
    for name,digest in members.items():assert sha(P/name)==digest,name
    current=load(P/'inputs/current-inputs.json')['files']
    for name,digest in current.items():assert sha(name)==digest,name
    for name,h in load(N/'inputs/product-closeout-supplements.json')['files'].items():assert sha(name)==h,name
    for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(N.parents[4]/name)==h,name
    old=Path(pred['entry_predecessor'])
    for name,key in [('manifest.json','entry_manifest_sha256'),('review/result-inputs/result-manifest.json','last_result_manifest_sha256'),('review/independent-result-review.json','last_result_review_sha256')]:assert sha(old/name)==pred[key]
    spec=importlib.util.spec_from_file_location('frozen_product_readback',P/'verification/verify_offline.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module);prior=module.verify()
    assert prior['tests']==979 and prior['compatibility_tests']==4
    git=lambda *args:subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()
    assert git('rev-parse','HEAD')==git('rev-parse','ultimaagent-e02-output-structure-candidate-20261108-r2')==pred['candidate']
    assert not git('status','--porcelain')
    return dict(verdict='PASS_PRODUCT_AND_PREDECESSOR_PRESERVATION',candidate=pred['candidate'],product_clean=True,
                product_preparation_members=len(members),current_input_pins=len(current),prior={k:v for k,v in prior.items() if k!='source_sha256'},
                actual_cases=0,model_calls=0,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('before','after')
    value=verify()
    with (N/'verification'/('preservation-'+sys.argv[1]+'.json')).open('x',encoding='utf8') as f:json.dump(value,f,indent=2)
    print(json.dumps({k:v for k,v in value.items() if k!='prior'}))
