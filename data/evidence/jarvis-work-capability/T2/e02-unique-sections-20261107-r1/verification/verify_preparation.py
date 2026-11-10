"""Read current bytes and saved checks; never call a model or product."""
from pathlib import Path
import ast,hashlib,json,subprocess,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1];R=N.parents[4];OLD=N.parent/'e02-failure-state-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-unique-sections/UltimaAgent')
P=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-failure-state/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def cases(p):
    nodes=list(ET.parse(p).iter('testcase'))
    assert nodes and not any(x.find(t) is not None for x in nodes for t in ('failure','error','skipped')),p
    return {(x.get('classname'),x.get('name')) for x in nodes}
def body(p,name):
    return ast.dump(next(n for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name==name))
def verify():
    inputs=load(N/'inputs/input-manifest.json');candidate=inputs['candidate']
    assert candidate==subprocess.check_output(['git','-C',str(C),'rev-parse','HEAD'],text=True).strip()
    assert not subprocess.check_output(['git','-C',str(C),'status','--porcelain'],text=True).strip()
    assert not (N/'actual').exists() and not (N/'release').exists()
    for p,h in inputs['files'].items():assert sha(Path(p))==h,p
    for p,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/p)==h,p
    pred=load(N/'inputs/predecessor.json')
    for name,key in [('manifest.json','manifest_sha256'),('review/result-inputs/result-manifest.json','result_manifest_sha256'),('review/independent-result-review.json','result_review_sha256')]:assert sha(OLD/name)==pred[key]
    for name in ('manifest.json','review/result-inputs/result-manifest.json'):
        for p,h in load(OLD/name)['files'].items():assert sha(OLD/p)==h,p
    for p,h in load(OLD/'inputs/input-manifest.json')['source_files'].items():assert sha(Path(p))==h,p
    assert sha(R/'docs/plans/jarvis-work-e02-unique-source-sections-plan-20261107.md')=='231ee464f173831de9ebc5d47b49c5427e4a611818e226b7ef7ae9f208343ffa'
    for name in ('independent-plan-review.json','independent-clock-plan-review.json'):assert load(N/'review'/name)['verdict']=='PASS_PLAN_ONLY'
    runs={};product=set();harness=set()
    expected={'unique-green':21,'failure-green':31,'grounding-green':11,'claim-green':28,'metadata-green':43,'diagnostics-green':17,'target-green':19,'reference-green':29,'research-a':68,'research-b':110,'navigation':90,'transport':104,'delivery':86,'grammar':7}
    for group,count in expected.items():
        choices=[p for p in sorted((N/'offline').glob(group+'-*/receipt.json')) if load(p)['exit_code']==0]
        assert choices,group
        p=choices[-1];r=load(p);assert r['sources_unchanged']
        audit=load(p.parent/'offline-audit.json');assert audit['python_operations_clean'] and not audit['denied'] and audit['expected_probe_closed']
        for name,h in r['source_sha256'].items():
            q=Path(name);assert sha(q)==h,name
            archived=p.parent/'snapshot'/(q.relative_to(C) if q.is_relative_to(C) else q.relative_to(N));assert sha(archived)==h,name
        observed=cases(p.parent/'junit.xml');assert len(observed)==count,(group,len(observed))
        assert not product&observed,group
        product|=observed;runs[group]=dict(path=str(p),tests=count)
    current={p.name:sha(p) for p in (N/'harness').iterdir() if p.is_file()}
    for group,count in [('base-a',79),('base-b',140),('recovery',19),('export-green',32),('failure-export-green',7)]:
        choices=[p for p in sorted((N/'code').glob('harness-preparation-*/receipt.json')) if load(p).get('group')==group and load(p)['exit_code']==0 and load(p)['harness_before']==current]
        assert choices,group
        p=choices[-1];r=load(p);assert r['inputs_unchanged'] and r['harness_unchanged'] and not r['timed_out']
        assert r['harness_before']==r['harness_after']==current
        audit=load(p.parent/'offline-audit.json');assert audit['python_operations_clean'] and not audit['denied']
        observed=cases(p.parent/'harness/adapter.xml');assert len(observed)==count,(group,len(observed))
        harness|=observed;runs['harness-'+group]=dict(path=str(p),tests=count)
    assert len(harness)==275
    other=0
    for group,count in [('bindings',16),('entry',32),('boundary',11)]:
        p=N/'offline'/(group+('-final' if group=='entry' else '-green'))/'receipt.json';r=load(p)
        assert r['exit_code']==0 and r['sources_unchanged'] and r['result']['success'] and not r['result']['denied']
        assert r['result']['tests']==count
        for name,h in r['sources'].items():assert sha(Path(name))==h,name
        runs[group]=dict(path=str(p),tests=count);other+=count
    for name in ('_fact_evidence','_text'):assert body(P/'src/brain/work_research.py',name)==body(C/'src/brain/work_research.py',name)
    for name in ('v3_writer_schema','resolve_v3','render_v3','build_page'):assert body(P/'src/brain/work_navigation.py',name)==body(C/'src/brain/work_navigation.py',name)
    assert sha(N/'verification/upstream/ollama-v0.32.15-api-types.go')=='032fe8c044429afd42fd9f898c6bbd6efc5977ffeeec4dd3c5a04035e9c3d0b1'
    assert sha(N/'inputs/direct-user-decision.json')=='cca923a3e62692d45728e9ec1bea8da3eb05763a72499eb44480dc6ae8878e7e'
    defs=lambda p:{n.name:ast.dump(n) for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))}
    before=defs(OLD/'harness/adapter.py');after=defs(N/'harness/adapter.py')
    changed={name for name in set(before)|set(after) if before.get(name)!=after.get(name)}
    assert not changed,changed
    assert sha(N/'diagnostic-clock-amendment.md')=='00bb17ad44bf7caacd487d086b34555472df7b3007636efbeefdbcbecc897e97'
    return dict(verdict='PASS_OFFLINE_UNIQUE_SOURCE_SECTIONS_PREPARATION_ONLY',candidate=candidate,tests=len(product)+len(harness)+other,
        product_tests=len(product),harness_unique_tests=len(harness),interface_tests=other,runs=runs,changed_harness_functions=sorted(changed),
        excluded=['test_http_work_legacy_and_cli','test_reparse_rejected'],actual_calls=0,model_calls=0,old_credit_transferred=False,E02='NOT_PASSED',T2='NOT_PASSED')
if __name__=='__main__':print(json.dumps(verify()))
