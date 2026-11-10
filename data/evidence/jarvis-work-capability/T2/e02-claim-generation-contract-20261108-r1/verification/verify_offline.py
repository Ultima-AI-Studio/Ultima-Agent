"""Verify fresh offline evidence, exact scope and immutable predecessors."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent')
OLD=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure-r2/UltimaAgent')
P=T/'e02-output-structure-controlled-preparation-20261108-r1'
B=T/'e02-output-structure-diagnostics-20261108-r2'
BASE='bf7f7a9cf0e4ba559c29daa388c00379d12d345a'
ALLOWED=('src/brain/agent_server.py','src/brain/work_navigation.py',
         'src/brain/tests/test_work_sampler_json_strings.py','src/brain/tests/test_work_claim_generation_contract.py')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
def members(root,path):
    files=load(path)['files']
    for name,h in files.items():assert sha(root/name)==h,name
    return len(files)
def verify():
    assert load(N/'inputs/scope.json')['question_id']=='call_5411de619a6c4de0bab414126a228c7d'
    assert sha(N/'plan.md')=='1e26155fc2bf9a256d9cd4ed694a3537ad9deca6f7915381f2412ad41d09c0ea'
    assert sha(N/'review/independent-plan-review.json')=='7ea4b91b21285088f05e1219303d2d39a47cf8d402fc08306e3377ccc0d44a2c'
    assert sha(P/'manifest.json')=='ea078190d78a340d3db06092bb050662a4a59e37e2f327c595199073b195eb1f'
    assert sha(P/'review/result-inputs/result-manifest.json')=='2c12627ea8cb8a78a6359d57f30825d3cd4c5ab5be91957f7d3627815105a0c0'
    assert sha(P/'review/independent-result-review.json')=='119133eb103755f972ef006d1f6381b95001e026a29daf4f973e14c5c840ab58'
    counts=dict(previous_preparation=members(P,P/'manifest.json'),previous_result=members(P,P/'review/result-inputs/result-manifest.json'),previous_seal=members(P/'actual/E02-controlled-1',P/'actual/E02-controlled-1/seal-index.json'),product_preparation=members(B,B/'manifest.json'))
    inputs=load(P/'inputs/input-manifest.json')
    for name,h in inputs['files'].items():assert sha(Path(name))==h,name
    pins=load(N/'inputs/accepted-dependency-pins.json')['files']
    for name,h in pins.items():assert sha(Path(name))==h,name
    foreign=load(N/'inputs/unrelated-working-tree.json')['files']
    for name,h in foreign.items():assert sha(R/name)==h,name
    assert git(OLD,'rev-parse','HEAD').decode().strip()==BASE and not git(OLD,'status','--porcelain').strip()
    changed=set(git(C,'diff','--name-only',BASE).decode().splitlines())
    changed.update(git(C,'ls-files','--others','--exclude-standard').decode().splitlines())
    assert changed==set(ALLOWED),changed
    for filename,changed_function in [('src/brain/agent_server.py','_research_code_claim_sampler_pattern'),('src/brain/work_navigation.py','v3_research_phase')]:
        before=ast.parse(git(C,'show',BASE+':'+filename));after=ast.parse((C/filename).read_bytes())
        def remainder(tree):return [ast.dump(x,include_attributes=False) for x in tree.body if getattr(x,'name',None)!=changed_function]
        assert remainder(before)==remainder(after),filename
    batch=load(N/'verification/final-regression-batch.json')
    assert len(batch['groups'])==22 and batch['same_source_bytes']
    assert batch['totals']['failures']==batch['totals']['errors']==batch['totals']['skipped']==0
    assert batch['totals']['tests']==batch['distinct_cases']==1004
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
    assert len(all_ids)==len(set(all_ids))==1004
    grammar=Path(batch['groups']['grammar']['receipt']).parent/'reference-conversion.json'
    reference=load(grammar);assert reference['compiled_native_validator_run'] is False and reference['native_model_calls']==0
    state=load(T/'current-run.json');previous=load(N/'inputs/previous-current-run.json')
    assert state['last_actual_result']==previous['last_actual_result']
    assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
    assert not state['live_gate_released'] and not state['next_stage_released']
    assert not any((N/name).exists() for name in ('actual','release','controller-authority'))
    return dict(verdict='PASS_OFFLINE_ONLY',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
        parent=BASE,tests=1004,product_tests=994,compatibility_tests=4,reference_conversion_tests=6,
        groups=22,distinct_cases=1004,source_sha256=batch['source_sha256'],changed_files=sorted(changed),
        parent_clean=True,preserved=counts,previous_input_pins=len(inputs['files']),dependency_pins=len(pins),foreign_files=len(foreign),
        last_actual_preserved=True,reference_conversion=reference,actual_cases=0,model_calls=0,
        actual_case_allocation=0,result_review_allocation=0,acceptance_credit=0,E02='NOT_PASSED_0_OF_3',T2='NOT_PASSED')
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False))
