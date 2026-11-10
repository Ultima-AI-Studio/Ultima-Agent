"""Read exact current bytes and fresh receipts; never infer a research PASS."""
from pathlib import Path
import ast,datetime as dt,hashlib,importlib.util,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
OLD=N.parent/'e02-output-budget-controlled-preparation-20261107-r1'
B=N.parent/'e02-output-structure-diagnostics-20261108-r2'
CANDIDATE='bf7f7a9cf0e4ba559c29daa388c00379d12d345a'
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
    assert scope['model_calls']==0 and decision['identifier_is_platform_message_id'] is False
    assert decision['decision_id']=='user-message:sha256:'+hashlib.sha256(decision['answer'].encode('utf8')).hexdigest()
    review=load(N/'review/independent-plan-review.json')
    assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PLAN_ONLY' and review['plan_sha256']==sha(N/'plan.md')
    a=module('current_entry_check_adapter',N/'harness/adapter.py');pins=a.check_inputs()
    current=load(N/'inputs/input-manifest.json');old=load(OLD/'inputs/input-manifest.json')
    assert current['candidate']==CANDIDATE and current['actual_released'] is False
    changed={'candidate','candidate_root','source_files','files'}
    assert {k:v for k,v in current.items() if k not in changed}=={k:v for k,v in old.items() if k not in changed}
    for file in ('harness/adapter.py','code/bindings.py','code/entry.py'):assert functions(N/file)==functions(OLD/file),file
    base=load(B/'inputs/current-inputs.json');assert current['source_files']==base['source_files'] and len(current['source_files'])==77
    for p,digest in current['source_files'].items():
        assert Path(p).is_relative_to(Path(current['candidate_root'])) and base['files'][p]==digest==sha(Path(p)),p
    hm=load(N/'harness/manifest.json')
    assert {p.name for p in (N/'harness').iterdir() if p.is_file()}==set(hm['files'])|{'manifest.json'}
    for name,digest in hm['files'].items():assert sha(N/'harness'/name)==digest,name
    groups={};identities=set();raw_count=0;red=[]
    for path in sorted((N/'code').glob('harness-preparation-*/receipt.json')):
        receipt=load(path);group=receipt['group']
        assert not receipt['timed_out'] and receipt['inputs_unchanged'] and receipt['harness_unchanged'] and receipt['snapshot_after_error'] is None
        assert receipt['actual'] is False and receipt['model_calls']==receipt['product_launches']==0
        for name,digest in receipt['harness_before'].items():
            assert sha(path.parent/'harness-source'/name)==digest,name
            if group!='export-red':assert sha(N/'harness'/name)==digest,name
        assert sha(path.parent/'harness-source/offline_pytest.py')==sha(N/'verification/offline_pytest.py')
        source=load(path.parent/'source-before.json');assert source==load(path.parent/'source-after.json')
        for name,digest in source.items():assert sha(Path(name))==digest,name
        audit=load(path.parent/'offline-audit.json')
        assert audit['error'] is None and not audit['denied'] and not audit['denied_sites']
        assert audit['expected_probe_closed'] and audit['python_operations_clean'] and audit['eager']['eager']['clean']
        tree=ET.parse(path.parent/'harness/adapter.xml');cases=tree.findall('.//testcase')
        assert cases and not tree.findall('.//error') and not tree.findall('.//skipped')
        failures=[x for x in cases if x.find('failure') is not None]
        if group=='export-red':
            assert receipt['exit_code']==receipt['pytest_exit_code']==audit['pytest_exit_code']==1 and len(failures)==2
            assert {x.attrib['name'] for x in failures}=={'test_export_diagnostics_current_native_refusal[six_reads]','test_export_diagnostics_current_native_refusal[ack_after_write]'}
            for x in failures:
                text=x.find('failure').text;assert 'research_failure_diagnostic_v5' in text and 'research_failure_diagnostic_v4' in text
            red.append(dict(receipt=str(path),sha256=sha(path),tests=len(cases),failures=2,classification='Obsolete version assertion; not a product failure'));continue
        assert group in ('base-a','base-b','recovery','export-green','failure-export-green') and group not in groups
        assert receipt['exit_code']==receipt['pytest_exit_code']==audit['pytest_exit_code']==0 and not failures
        for case in cases:identities.add((case.attrib['classname'],case.attrib['name']))
        raw_count+=len(cases);groups[group]=dict(tests=len(cases),receipt=str(path),sha256=sha(path))
    assert len(red)==1 and set(groups)=={'base-a','base-b','recovery','export-green','failure-export-green'}
    assert groups['failure-export-green']['tests']==13
    stdlib={}
    for stage in ('bindings-green','entry-final','boundary-green'):
        path=N/'offline'/stage/'receipt.json';receipt=load(path);result=load(path.parent/'test-result.json')
        assert result==receipt['result'] and result['success'] and result['failures']==result['errors']==0 and not result['denied']
        assert receipt['exit_code']==0 and receipt['sources_unchanged'] and receipt['actual_product_runs']==receipt['model_calls']==0
        for name,digest in receipt['sources'].items():assert sha(Path(name))==sha(path.parent/'snapshot'/Path(name).name)==digest,name
        stdlib[stage]=dict(tests=result['tests'],receipt=str(path),sha256=sha(path))
    assert set(load(N/'verification/batch-checks.json').values())=={0}
    preservation=module('current_preservation',N/'verification/verify_preservation.py').verify()
    runtime=load(N/'verification/runtime-readiness-final.json')
    assert runtime['verdict']=='PASS_READONLY_RUNTIME_IDENTITY' and runtime['candidate_base']==CANDIDATE
    assert len(runtime['protected'])==7 and runtime['isolated_port_free'] and runtime['model_calls']==runtime['service_operations']==0
    for name,digest in runtime['checker_sources'].items():assert sha(Path(name))==digest
    tests=len(identities)+sum(r['tests'] for r in stdlib.values())
    return dict(verdict='PASS_OFFLINE_PREPARATION',candidate=CANDIDATE,tests=tests,harness_unique=len(identities),harness_raw=raw_count,
        duplicated_harness_cases=raw_count-len(identities),harness_groups=groups,stdlib=stdlib,red_runs=red,red_failures=2,product_sources_changed=False,
        input_pins=len(pins),source_pins=len(current['source_files']),product_baseline_tests=979,product_baseline_rerun=False,
        source_change='Path/candidate/hash bindings and export tests only; entry/adapter/bindings functions unchanged',
        actual_cases=0,model_calls=0,acceptance_credit=0,actual_case_allocation=0,result_review_allocation=0,
        E02='NOT_PASSED',T2='NOT_PASSED',preservation=preservation,runtime_readiness_sha256=sha(N/'verification/runtime-readiness-final.json'),
        recorded_at=dt.datetime.now(dt.timezone.utc).isoformat())
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
