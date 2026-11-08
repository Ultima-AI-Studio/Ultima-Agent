"""Read exact current bytes and fresh receipts; never infer a research PASS."""
from pathlib import Path
import ast,datetime as dt,hashlib,importlib.util,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
OLD=N.parent/'e02-claim-generation-controlled-preparation-20261108-r1'
B=N.parent/'e02-source-grounding-coverage-20261108-r2'
CANDIDATE='43da3f014a763b8ea3963872a8f1ce8ebea77531'
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
    assert decision['source_question_id']=='call_3d33440cc40c401ea7a2cf11c8bc2bcf' and decision['answer']=='授权离线审查、最小补修、必要独审与入口准备（推荐）'
    assert decision['decision_id']==decision['question_id']=='user-message:sha256:'+hashlib.sha256(decision['answer'].encode('utf8')).hexdigest()
    review=load(N/'review/independent-plan-review.json')
    assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PLAN_ONLY' and review['plan_sha256']==sha(N/'plan.md')
    a=module('current_entry_check_adapter',N/'harness/adapter.py');pins=a.check_inputs()
    current=load(N/'inputs/input-manifest.json');old=load(OLD/'inputs/input-manifest.json')
    assert current['candidate']==CANDIDATE and current['actual_released'] is False
    changed={'candidate','candidate_root','source_files','files'}
    assert {k:v for k,v in current.items() if k not in changed}=={k:v for k,v in old.items() if k not in changed}
    for file in ('harness/adapter.py','code/bindings.py','code/entry.py'):assert functions(N/file)==functions(OLD/file),file
    base=load(B/'inputs/current-inputs.json');assert current['source_files']==base['source_files'] and len(current['source_files'])==79
    for p,digest in current['source_files'].items():
        assert Path(p).is_relative_to(Path(current['candidate_root'])) and base['files'][p]==digest==sha(Path(p)),p
    hm=load(N/'harness/manifest.json')
    assert {p.name for p in (N/'harness').iterdir() if p.is_file()}==set(hm['files'])|{'manifest.json'}
    for name,digest in hm['files'].items():assert sha(N/'harness'/name)==digest,name
    recovery=load(N/'verification/base-b-recovery-result.json')
    assert recovery['exit_code']==0 and recovery['original_timeout_seconds']==90
    assert recovery['actual_cases']==recovery['model_calls']==recovery['acceptance_credit']==0
    failed=Path(recovery['failed_receipt']);recovered=Path(recovery['recovery_receipt'])
    assert failed==N/'code/harness-preparation-20261108T055251046439Z/receipt.json'
    assert recovered.is_relative_to(N/'code') and recovered!=failed
    assert sha(failed)==recovery['failed_sha256'] and sha(recovered)==recovery['recovery_sha256']
    initial=load(N/'verification/final-batch-checks.json')
    assert initial=={'base-a':0,'recovery':0,'base-b':124,'failure-export-green':0,'bindings':0,'entry':0,'export-green':0,'boundary':0}
    failed_value=load(failed);recovered_value=load(recovered)
    assert failed_value['selected_test_functions']==recovered_value['selected_test_functions']
    assert failed_value['harness_before']==recovered_value['harness_before']
    assert failed_value['timeout_seconds']==recovered_value['timeout_seconds']==90
    observation=N/'verification/base-b-timeout-process-observation.json'
    observed=json.loads(observation.read_text('utf-8-sig'))
    start=load(N/'verification/base-b-recovery-start.json')
    assert observed['matching_count']==0 and observed['read_only'] is True
    assert start['process_observation_sha256']==sha(observation) and start['failed_sha256']==sha(failed)
    groups={};identities=set();raw_count=0;red=[];interrupted=[]
    for path in sorted((N/'code').glob('harness-preparation-*/receipt.json')):
        receipt=load(path);group=receipt['group']
        assert receipt['inputs_unchanged'] and receipt['harness_unchanged'] and receipt['snapshot_after_error'] is None
        assert receipt['actual'] is False and receipt['model_calls']==receipt['product_launches']==0
        for name,digest in receipt['harness_before'].items():
            assert sha(path.parent/'harness-source'/name)==digest,name
            assert sha(N/'harness'/name)==digest,name
        assert sha(path.parent/'harness-source/offline_pytest.py')==sha(N/'verification/offline_pytest.py')
        source=load(path.parent/'source-before.json');assert source==load(path.parent/'source-after.json')
        for name,digest in source.items():assert sha(Path(name))==digest,name
        if path==failed:
            assert group=='base-b' and receipt['timed_out'] and receipt['exit_code']==receipt['pytest_exit_code']==124
            assert not (path.parent/'harness/adapter.xml').exists() and not (path.parent/'offline-audit.json').exists()
            interrupted.append(dict(receipt=str(path),sha256=sha(path),exit_code=124,timeout_seconds=90,
                credit=0,audit_completion_available=False,partial_progress_is_not_pass=True))
            continue
        assert not receipt['timed_out']
        if group=='base-b':assert path==recovered
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
    for stage in ('bindings-final-green','entry-final-green','boundary-final-green'):
        path=N/'offline'/stage/'receipt.json';receipt=load(path);result=load(path.parent/'test-result.json')
        assert result==receipt['result'] and result['success'] and result['failures']==result['errors']==0 and not result['denied']
        assert receipt['exit_code']==0 and receipt['sources_unchanged'] and receipt['actual_product_runs']==receipt['model_calls']==0
        for name,digest in receipt['sources'].items():assert sha(Path(name))==sha(path.parent/'snapshot'/Path(name).name)==digest,name
        stdlib[stage]=dict(tests=result['tests'],receipt=str(path),sha256=sha(path))
    assert len(interrupted)==1 and len(groups)==5
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
    assert tests==350 and len(identities)==289 and {k:v['tests'] for k,v in stdlib.items()}=={'bindings-final-green':16,'entry-final-green':34,'boundary-final-green':11}
    return dict(verdict='PASS_OFFLINE_PREPARATION',candidate=CANDIDATE,tests=tests,harness_unique=len(identities),harness_raw=raw_count,
        duplicated_harness_cases=raw_count-len(identities),harness_groups=groups,stdlib=stdlib,red_runs=red,red_failures=0,
        interrupted_runs=interrupted,offline_recovery_result_sha256=sha(N/'verification/base-b-recovery-result.json'),product_sources_changed=False,
        input_pins=len(pins),source_pins=len(current['source_files']),product_baseline_tests=1022,product_baseline_rerun=False,
        source_change='Path/hash and content-derived preparation binding; reserved-read export fixture counts migrated, purposes retained; core entry/adapter/bindings functions unchanged',
        actual_cases=0,model_calls=0,acceptance_credit=0,actual_case_allocation=0,result_review_allocation=0,
        E02='NOT_PASSED',T2='NOT_PASSED',preservation=preservation,runtime_readiness_sha256=sha(N/'verification/runtime-readiness-pending.json'),live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT',
        recorded_at=dt.datetime.now(dt.timezone.utc).isoformat())
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
