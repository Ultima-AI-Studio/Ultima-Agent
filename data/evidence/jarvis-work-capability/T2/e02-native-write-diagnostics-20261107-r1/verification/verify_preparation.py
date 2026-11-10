"""Read-only proof of the current candidate and completed offline checks."""
from pathlib import Path
import ast,hashlib,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1];R=N.parents[4]
OLD=N.parent/'e02-source13-native-metadata-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-write-diagnostics/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def junit(path):
    tests=list(ET.parse(path).iter('testcase'))
    assert tests and not any(x.find(tag) is not None for x in tests for tag in ('failure','error','skipped')),path
    return {(x.get('classname'),x.get('name')) for x in tests}
def verify():
    assert not (N/'release').exists() and not (N/'actual').exists()
    pred=load(N/'inputs/predecessor.json')
    for path,expected in [(OLD/'manifest.json',pred['manifest_sha256']),
        (OLD/'review/result-inputs/result-manifest.json',pred['result_manifest_sha256']),
        (OLD/'review/independent-result-review.json',pred['result_review_sha256'])]:assert sha(path)==expected,path
    for path in (OLD/'manifest.json',OLD/'review/result-inputs/result-manifest.json'):
        for name,digest in load(path)['files'].items():assert sha(OLD/name)==digest,name
    for path,digest in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(path))==digest,path
    for path,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/path)==digest,path
    transition=load(N/'inputs/candidate-transition.json')
    assert transition['changed_existing_sources']==['src\\brain\\work_service.py']
    # Every successful test receipt binds the actual product bytes and its own
    # archived guard revision. Earlier guard/setup failures get no pass credit.
    selected={};sets={}
    for group in ('diagnostics-green','metadata-green','research-a','research-b','navigation','transport','delivery'):
        paths=[p for p in sorted((N/'offline').glob(group+'-*/receipt.json')) if load(p)['exit_code']==0 and load(p)['sources_unchanged']]
        assert paths,group
        p=paths[-1];receipt=load(p);sets[group]=junit(p.parent/'junit.xml')
        audit=load(p.parent/'offline-audit.json');assert audit['python_operations_clean'] and not audit['denied'] and audit['expected_probe_closed']
        for name,digest in receipt['source_sha256'].items():
            q=Path(name)
            snapshot=p.parent/'snapshot'/(q.relative_to(C) if q.is_relative_to(C) else Path('verification')/q.name)
            assert sha(snapshot)==digest,name
            if q.is_relative_to(C):assert sha(q)==digest,name
        selected[group]=dict(path=str(p),tests=len(sets[group]))
    assert len(sets['metadata-green'])==43 and len(sets['navigation'])==90 and len(sets['transport'])==104 and len(sets['delivery'])==86
    assert not sets['research-a']&sets['research-b']
    names={n.name for n in ast.parse((C/'src/brain/tests/test_work_research.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')}
    tested={name.split('[')[0] for _,name in sets['research-a']|sets['research-b']}
    assert names==tested,(names-tested,tested-names)
    assert len(sets['diagnostics-green'])==17
    red=N/'offline/diagnostics-red-20261106T183734991978Z'
    redcases=list(ET.parse(red/'junit.xml').iter('testcase'))
    failures=[c.find('failure') for c in redcases if c.find('failure') is not None]
    assert len(redcases)==17 and len(failures)==14
    assert all("'research_failure'" in f.get('message','') for f in failures)
    assert sha(red/'snapshot/src/brain/work_service.py')=='206fe17ddf8d78b64018fda01a03228e97d6e74014da3c6d21e9dc7eee860449'
    current={p.name:sha(p) for p in (N/'harness').iterdir() if p.is_file()}
    for group,count in (('base-a',79),('base-b',140),('recovery',19)):
        paths=[p for p in sorted((N/'code').glob('harness-preparation-*/receipt.json')) if load(p).get('group')==group and load(p)['exit_code']==0]
        assert paths,group
        p=paths[-1];receipt=load(p);assert receipt['harness_before']==receipt['harness_after']==current
        assert receipt['inputs_unchanged'] and receipt['harness_unchanged'] and not receipt['timed_out']
        audit=load(p.parent/'offline-audit.json');assert audit['python_operations_clean'] and not audit['denied']
        cases=junit(p.parent/'harness/adapter.xml');assert len(cases)==count
        historical=[x for x in sorted((OLD/'code').glob('harness-preparation-*/receipt.json')) if load(x).get('group')==group and load(x)['exit_code']==0][-1]
        old_cases=junit(historical.parent/'harness/adapter.xml')
        assert cases==old_cases
        selected['harness-'+group]=dict(path=str(p),tests=count)
    for group,count in (('boundary',11),('entry',26),('bindings',14)):
        p=N/'offline'/f'{group}-green/receipt.json';v=load(p)
        assert v['exit_code']==0 and v['sources_unchanged'] and v['result']['success'] and not v['result']['denied']
        assert v['result']['tests']==count,(group,v['result'])
        for name,digest in v['sources'].items():assert sha(Path(name))==digest,name
        selected[group]=dict(path=str(p),tests=count)
    # Runtime harness functions are unchanged; only candidate/hash constants are rebound.
    functions=[]
    for root in (OLD,N):functions.append({n.name:ast.dump(n,include_attributes=False) for n in ast.parse((root/'harness/adapter.py').read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.ClassDef))})
    changed={name for name in set(functions[0])|set(functions[1]) if functions[0].get(name)!=functions[1].get(name)}
    assert not changed,changed
    result=dict(verdict='PASS_OFFLINE_WRITE_DIAGNOSTICS_PREPARATION_ONLY',candidate=transition['candidate'],tests=sum(x['tests'] for x in selected.values()),runs=selected,
        changed_harness_functions=sorted(changed),existing_runtime_change='WorkService bounded diagnostic from first failed trusted ledger writer only',
        product_live_tests_excluded=['test_http_work_legacy_and_cli','test_reparse_rejected'],actual_product_calls=0,model_calls=0,
        old_candidate_credit_transferred=False,E02='NOT_PASSED',T2='NOT_PASSED')
    return result
if __name__=='__main__':print(json.dumps(verify()))
