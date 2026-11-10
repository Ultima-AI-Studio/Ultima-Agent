"""Read exact current bytes and fresh receipts; never infer a research PASS."""
from pathlib import Path
import ast,datetime as dt,hashlib,importlib.util,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
OLD=N.parent/'e02-output-structure-controlled-preparation-20261108-r1'
B=N.parent/'e02-claim-generation-contract-20261108-r1'
CANDIDATE='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
def functions(path):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
def verify():
    for folder in ('actual','release','controller-authority','native-preflight','controller-ledger.json'):assert not (N/folder).exists(),folder
    decision=load(N/'inputs/direct-user-decision.json');scope=load(N/'inputs/scope.json')
    assert decision['actual_case_allocation']==decision['result_review_allocation']==scope['actual_case_allocation']==scope['result_review_allocation']==0
    assert scope['model_calls']==scope['network_requests']==0 and decision['identifier_is_platform_message_id'] is False
    assert decision['source_question_id']=='call_5411de619a6c4de0bab414126a228c7d' and decision['answer']=='授权离线补修、必要独审与入口准备（推荐）'
    assert decision['decision_id']==decision['question_id']=='user-message:sha256:'+hashlib.sha256(decision['answer'].encode('utf8')).hexdigest()
    recovery=load(N/'verification/preparation-binding-recovery.json')
    assert recovery['decision_sha256']==sha(N/'inputs/direct-user-decision.json') and recovery['core_AST_unchanged'] and recovery['product_changed'] is False
    review=load(N/'review/independent-plan-review.json')
    assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PLAN_ONLY' and review['plan_sha256']==sha(N/'plan.md')
    a=module('current_entry_check_adapter',N/'harness/adapter.py');pins=a.check_inputs()
    current=load(N/'inputs/input-manifest.json');old=load(OLD/'inputs/input-manifest.json')
    assert current['candidate']==CANDIDATE and current['actual_released'] is False
    changed={'candidate','candidate_root','source_files','files'}
    assert {k:v for k,v in current.items() if k not in changed}=={k:v for k,v in old.items() if k not in changed}
    for file in ('harness/adapter.py','code/bindings.py','code/entry.py'):assert functions(N/file)==functions(OLD/file),file
    base=load(B/'inputs/current-inputs.json');assert current['source_files']==base['source_files'] and len(current['source_files'])==78
    for p,digest in current['source_files'].items():
        assert Path(p).is_relative_to(Path(current['candidate_root'])) and base['files'][p]==digest==sha(Path(p)),p
    hm=load(N/'harness/manifest.json')
    assert {p.name for p in (N/'harness').iterdir() if p.is_file()}==set(hm['files'])|{'manifest.json'}
    for name,digest in hm['files'].items():assert sha(N/'harness'/name)==digest,name
    historical=load(N/'verification/first-attempt-index.json')
    for name,h in historical['files'].items():assert sha(Path(name))==h,name
    assert historical['failures']==3 and {k for k,v in historical['batch'].items() if v}=={'entry','export-green'}
    groups={};identities=set();raw_count=0;red=[]
    for path in sorted((N/'code').glob('harness-preparation-*/receipt.json')):
        if str(path) in historical['harness_receipts']:continue
        receipt=load(path);group=receipt['group']
        assert not receipt['timed_out'] and receipt['inputs_unchanged'] and receipt['harness_unchanged'] and receipt['snapshot_after_error'] is None
        assert receipt['actual'] is False and receipt['model_calls']==receipt['product_launches']==0
        for name,digest in receipt['harness_before'].items():
            assert sha(path.parent/'harness-source'/name)==digest,name
            assert sha(N/'harness'/name)==digest,name
        assert sha(path.parent/'harness-source/offline_pytest.py')==sha(N/'verification/offline_pytest.py')
        source=load(path.parent/'source-before.json');assert source==load(path.parent/'source-after.json')
        for name,digest in source.items():assert sha(Path(name))==digest,name
        audit=load(path.parent/'offline-audit.json')
        assert audit['error'] is None and not audit['denied'] and not audit['denied_sites']
        assert audit['expected_probe_closed'] and audit['python_operations_clean'] and audit['eager']['eager']['clean']
        tree=ET.parse(path.parent/'harness/adapter.xml');cases=tree.findall('.//testcase')
        assert cases and not tree.findall('.//error') and not tree.findall('.//skipped')
        failures=[x for x in cases if x.find('failure') is not None]
        assert group in ('base-a','base-b','recovery','export-green','failure-export-green') and group not in groups
        assert receipt['exit_code']==receipt['pytest_exit_code']==audit['pytest_exit_code']==0 and not failures
        for case in cases:identities.add((case.attrib['classname'],case.attrib['name']))
        raw_count+=len(cases);groups[group]=dict(tests=len(cases),receipt=str(path),sha256=sha(path))
    assert not red and set(groups)=={'base-a','base-b','recovery','export-green','failure-export-green'}
    assert groups['failure-export-green']['tests']==13
    stdlib={}
    for stage in ('bindings-recovery-green','entry-recovery-green','boundary-recovery-green'):
        path=N/'offline'/stage/'receipt.json';receipt=load(path);result=load(path.parent/'test-result.json')
        assert result==receipt['result'] and result['success'] and result['failures']==result['errors']==0 and not result['denied']
        assert receipt['exit_code']==0 and receipt['sources_unchanged'] and receipt['actual_product_runs']==receipt['model_calls']==0
        for name,digest in receipt['sources'].items():assert sha(Path(name))==sha(path.parent/'snapshot'/Path(name).name)==digest,name
        stdlib[stage]=dict(tests=result['tests'],receipt=str(path),sha256=sha(path))
    assert set(load(N/'verification/recovery-batch-checks.json').values())=={0}
    preservation=module('current_preservation',N/'verification/verify_preservation.py').verify()
    runtime=load(N/'verification/runtime-readiness-pending.json')
    assert runtime['status']=='PENDING_FRESH_ACTUAL_PREFLIGHT' and runtime['candidate']==CANDIDATE
    assert runtime['current_runtime_verified'] is False and runtime['actual_preflight_unchanged'] is True
    assert runtime['model_calls']==runtime['network_requests']==runtime['service_operations']==0
    for name,digest in runtime['historical_files'].items():assert sha(Path(name))==digest,name
    assert runtime['historical_evidence_is_current_proof'] is False
    state=load(N.parent/'current-run.json');prior_state=load(N/'inputs/previous-current-run.json')
    assert state['last_actual_result']==prior_state['last_actual_result'] and {'T2','t2'}<=set(state)
    assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
    assert state['active_candidate']==CANDIDATE and state['live_runtime_readiness']=='PENDING_FRESH_ACTUAL_PREFLIGHT'
    tests=len(identities)+sum(r['tests'] for r in stdlib.values())
    assert tests==350 and len(identities)==289 and {k:v['tests'] for k,v in stdlib.items()}=={'bindings-recovery-green':16,'entry-recovery-green':34,'boundary-recovery-green':11}
    return dict(verdict='PASS_OFFLINE_PREPARATION',candidate=CANDIDATE,tests=tests,harness_unique=len(identities),harness_raw=raw_count,
        duplicated_harness_cases=raw_count-len(identities),harness_groups=groups,stdlib=stdlib,red_runs=red,red_failures=0,first_attempt_failures_preserved=3,first_attempt_index_sha256=sha(N/'verification/first-attempt-index.json'),product_sources_changed=False,
        input_pins=len(pins),source_pins=len(current['source_files']),product_baseline_tests=1004,product_baseline_rerun=False,
        source_change='Path/hash and content-derived preparation binding; two sampler fixture expressions migrated, purposes retained; core entry/adapter/bindings functions unchanged',
        actual_cases=0,model_calls=0,acceptance_credit=0,actual_case_allocation=0,result_review_allocation=0,
        E02='NOT_PASSED',T2='NOT_PASSED',preservation=preservation,runtime_readiness_sha256=sha(N/'verification/runtime-readiness-pending.json'),live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT',
        recorded_at=dt.datetime.now(dt.timezone.utc).isoformat())
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
