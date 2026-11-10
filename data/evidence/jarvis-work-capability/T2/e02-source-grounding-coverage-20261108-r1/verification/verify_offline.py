"""Verify fresh offline evidence, exact scope and immutable predecessors."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent')
OLD=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent')
P=T/'e02-claim-generation-controlled-preparation-20261108-r1'
B=T/'e02-claim-generation-contract-20261108-r1'
BASE='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b'
ALLOWED=('src/brain/agent_server.py','src/brain/work_navigation.py',
         'src/brain/tests/test_work_sampler_json_strings.py','src/brain/tests/test_work_evidence_first_generation.py',
         'src/brain/tests/test_work_source_coverage_budget.py','src/brain/tests/test_work_research.py',
         'src/brain/tests/test_work_failure_diagnostics.py','src/brain/tests/test_work_source_reference_schema.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
def members(root,path):
    files=load(path)['files']
    for name,h in files.items():assert sha(root/name)==h,name
    return len(files)
def foreign_readback():
    original=load(N/'inputs/unrelated-working-tree.json')['files']
    observation=load(N/'inputs/unrelated-change-observation.json')
    assert observation['baseline_manifest_sha256']==sha(N/'inputs/unrelated-working-tree.json')
    changes=observation['observed_changes'];assert set(changes)=={'docs/tracker/北极星上线任务清单.html'}
    for name,h in original.items():
        if name in changes:
            data=changes[name];assert h==data['baseline_sha256']
            assert sha(R/name)==sha(Path(data['snapshot']))==data['observed_sha256']
        else:assert sha(R/name)==h,name
    return dict(files=len(original),baseline_unchanged=14,out_of_scope_observed=1,observed_bytes_preserved=True)
def verify():
    assert load(N/'inputs/scope.json')['question_id']=='call_3d33440cc40c401ea7a2cf11c8bc2bcf'
    assert sha(N/'plan.md')=='223d97202583e7a7a5475c0822547339ed178cb7e3b2345d72db7e97ca5f8490'
    assert sha(N/'review/independent-plan-review.json')=='82b7d2213526760e097563a775bc23210f26124ca93d9186818dcefcebebb14f'
    assert sha(P/'manifest.json')=='c36908a9a99f290889cb420613a93d70611386ace39765e8b970f55f5ea1f16a'
    assert sha(P/'review/result-inputs/result-manifest.json')=='ab388abe9d994ee56b985c14183d14e2af3530a499de4cfe116a8c1a2315dddf'
    assert sha(P/'review/independent-result-review.json')=='065d3f6fa910976672f01c02850d0c52f1f34567ccaa295451e427efbe0bb9af'
    counts=dict(previous_preparation=members(P,P/'manifest.json'),previous_result=members(P,P/'review/result-inputs/result-manifest.json'),previous_seal=members(P/'actual/E02-controlled-1',P/'actual/E02-controlled-1/seal-index.json'),product_preparation=members(B,B/'manifest.json'))
    inputs=load(P/'inputs/input-manifest.json')
    for name,h in inputs['files'].items():assert sha(Path(name))==h,name
    pins=load(N/'inputs/accepted-dependency-pins.json')['files']
    for name,h in pins.items():assert sha(Path(name))==h,name
    parents=load(N/'inputs/plan-reviewed-parent-snapshots.json')['files']
    for name,data in parents.items():
        assert sha(Path(data['snapshot']))==data['sha256']
        assert git(C,'show',BASE+':'+Path(name).relative_to(C).as_posix())==Path(data['snapshot']).read_bytes()
    for name,h in load(N/'review/plan-inputs.json')['files'].items():
        p=Path(parents[name]['snapshot']) if name in parents else Path(name)
        assert sha(p)==h,name
    foreign=load(N/'inputs/unrelated-working-tree.json')['files']
    foreign_state=foreign_readback()
    assert git(OLD,'rev-parse','HEAD').decode().strip()==BASE and not git(OLD,'status','--porcelain').strip()
    changed=set(git(C,'diff','--name-only',BASE).decode().splitlines())
    changed.update(git(C,'ls-files','--others','--exclude-standard').decode().splitlines())
    assert changed==set(ALLOWED),changed
    for filename,changed_function in [('src/brain/agent_server.py',{'_research_sampler_schema'}),('src/brain/work_navigation.py',{'v3_research_phase','v3_phase_inspect_schema'})]:
        before=ast.parse(git(C,'show',BASE+':'+filename));after=ast.parse((C/filename).read_bytes())
        def remainder(tree):return [ast.dump(x,include_attributes=False) for x in tree.body if getattr(x,'name',None) not in changed_function]
        assert remainder(before)==remainder(after),filename
    batch=load(N/'verification/final-regression-batch-r3.json')
    assert len(batch['groups'])==23 and batch['same_source_bytes']
    assert batch['totals']['failures']==batch['totals']['errors']==batch['totals']['skipped']==0
    assert batch['totals']['tests']==batch['distinct_cases']==1022
    assert batch['actual_cases']==batch['model_calls']==batch['acceptance_credit']==0
    for name,h in batch['source_sha256'].items():assert sha(Path(name))==h,name
    all_ids=[]
    for group,data in batch['groups'].items():
        receipt=Path(data['receipt']);assert sha(receipt)==data['receipt_sha256']
        r=load(receipt);a=load(receipt.parent/'offline-audit.json')
        assert r['sources_unchanged'] and r['source_sha256']==batch['source_sha256'] and r['exit_code']==0
        assert a['python_operations_clean'] and not a['denied'] and a['expected_probe_closed']
        assert r['actual'] is False and r['model_calls']==r['product_launches']==0
        xml=ET.parse(receipt.parent/'junit.xml').getroot()
        assert not list(xml.iter('failure')) and not list(xml.iter('error')) and not list(xml.iter('skipped'))
        all_ids.extend((x.attrib.get('classname',''),x.attrib['name']) for x in xml.iter('testcase'))
    assert len(all_ids)==len(set(all_ids))==1022
    grammar=Path(batch['groups']['grammar']['receipt']).parent/'reference-conversion.json'
    reference=load(grammar);assert reference['compiled_native_validator_run'] is False and reference['native_model_calls']==0
    state=load(T/'current-run.json');previous=load(N/'inputs/previous-current-run.json')
    assert state['last_actual_result']==previous['last_actual_result']
    assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
    assert not state['live_gate_released'] and not state['next_stage_released']
    assert not any((N/name).exists() for name in ('actual','release','controller-authority'))
    return dict(verdict='PASS_OFFLINE_ONLY',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        parent=BASE,tests=1022,product_tests=1008,compatibility_tests=4,reference_conversion_tests=10,
        groups=23,distinct_cases=1022,source_sha256=batch['source_sha256'],changed_files=sorted(changed),
        parent_clean=True,preserved=counts,previous_input_pins=len(inputs['files']),dependency_pins=len(pins),foreign_files=len(foreign),
        last_actual_preserved=True,foreign_readback=foreign_state,reference_conversion=reference,actual_cases=0,model_calls=0,
        actual_case_allocation=0,result_review_allocation=0,acceptance_credit=0,E02='NOT_PASSED_0_OF_3',T2='NOT_PASSED')
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False))
