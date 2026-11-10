"""Read current bytes and fresh offline receipts; never infer an actual pass."""
from pathlib import Path
import ast,datetime as dt,hashlib,importlib.util,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
OLD=N.parent/'e02-native-rejection-controlled-preparation-20261107-r1'
CANDIDATE='0421a54cab572be013c3f7ad562e86406bfe8e52'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
def functions(path):
    return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(path.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
def verify():
    for folder in ('actual','release','controller-authority','native-preflight'):
        assert not (N/folder).exists(),folder
    assert not (N/'controller-ledger.json').exists()
    decision=load(N/'inputs/direct-user-decision.json');scope=load(N/'inputs/scope.json')
    assert decision['actual_case_allocation']==decision['result_review_allocation']==scope['actual_case_allocation']==scope['result_review_allocation']==0
    assert scope['model_calls']==0
    review=load(N/'review/independent-plan-review.json')
    assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PLAN_ONLY' and review['plan_sha256']==sha(N/'plan.md')
    a=module('n13_check_adapter',N/'harness/adapter.py');pins=a.check_inputs()
    current=load(N/'inputs/input-manifest.json');old=load(OLD/'inputs/input-manifest.json')
    assert current['candidate']==CANDIDATE and current['actual_released'] is False
    changed={'candidate','candidate_root','source_files','files'}
    assert {k:v for k,v in current.items() if k not in changed}=={k:v for k,v in old.items() if k not in changed}
    for file in ('harness/adapter.py','code/bindings.py','code/entry.py'):
        assert functions(N/file)==functions(OLD/file),file
    old_root=Path(old['candidate_root']);current_root=Path(current['candidate_root'])
    inherited={str(current_root/Path(p).relative_to(old_root)) for p in old['source_files']}
    frozen=load(N.parent/'e02-writer-output-budget-20261107-r1/verification/candidate-freeze.json')['source_sha256']
    assert set(current['source_files'])==inherited|set(frozen)
    expected_pins=load(N.parent/'e02-writer-output-budget-20261107-r1/inputs/current-inputs.json')['files']
    for p,digest in current['source_files'].items():assert expected_pins[p]==digest==sha(Path(p)),p
    hm=load(N/'harness/manifest.json')
    assert {p.name for p in (N/'harness').iterdir() if p.is_file()}==set(hm['files'])|{'manifest.json'}
    for name,digest in hm['files'].items():assert sha(N/'harness'/name)==digest,name
    # No new product behavior: prior RED/GREEN and prior failed validation remain under their old roots.
    historical=set()
    groups={};identities=set();raw_count=0
    for path in sorted((N/'code').glob('harness-preparation-*/receipt.json')):
        if path.relative_to(N).as_posix() in historical:continue
        receipt=load(path);group=receipt['group']
        if group=='failure-export-red':continue
        assert group in ('base-a','base-b','recovery','export-green','failure-export-green') and group not in groups
        assert receipt['exit_code']==receipt['pytest_exit_code']==0 and not receipt['timed_out']
        assert receipt['inputs_unchanged'] and receipt['harness_unchanged'] and receipt['snapshot_after_error'] is None
        assert receipt['actual'] is False and receipt['model_calls']==receipt['product_launches']==0
        for name,digest in receipt['harness_before'].items():
            assert sha(N/'harness'/name)==sha(path.parent/'harness-source'/name)==digest,name
        assert sha(path.parent/'harness-source/offline_pytest.py')==sha(N/'verification/offline_pytest.py')
        source=load(path.parent/'source-before.json');assert source==load(path.parent/'source-after.json')
        for name,digest in source.items():assert sha(Path(name))==digest,name
        audit=load(path.parent/'offline-audit.json')
        assert audit['pytest_exit_code']==0 and audit['error'] is None and not audit['denied'] and not audit['denied_sites']
        assert audit['expected_probe_closed'] and audit['python_operations_clean'] and audit['eager']['eager']['clean']
        tree=ET.parse(path.parent/'harness/adapter.xml');cases=tree.findall('.//testcase')
        assert cases and not tree.findall('.//failure') and not tree.findall('.//error') and not tree.findall('.//skipped')
        for case in cases:identities.add((case.attrib['classname'],case.attrib['name']))
        raw_count+=len(cases);groups[group]=dict(tests=len(cases),receipt=str(path),sha256=sha(path))
    assert set(groups)=={'base-a','base-b','recovery','export-green','failure-export-green'}
    assert groups['failure-export-green']['tests']==13
    initial=load(N/'offline/entry-final/test-result.json')
    assert initial['tests']==34 and initial['errors']==1 and initial['failures']==0 and not initial['denied']
    assert "KeyError: 'decision_id'" in (N/'offline/entry-final/stderr.log').read_text('utf8')
    stdlib={}
    for stage in ('bindings-green','entry-review-green','boundary-green'):
        path=N/'offline'/stage/'receipt.json';receipt=load(path);result=load(path.parent/'test-result.json')
        assert result==receipt['result'] and result['success'] and result['failures']==result['errors']==0 and not result['denied']
        assert receipt['exit_code']==0 and receipt['sources_unchanged'] and receipt['actual_product_runs']==receipt['model_calls']==0
        for name,digest in receipt['sources'].items():assert sha(Path(name))==sha(path.parent/'snapshot'/Path(name).name)==digest,name
        stdlib[stage]=dict(tests=result['tests'],receipt=str(path),sha256=sha(path))
    # Frozen product already has preserved RED/GREEN; this turn only rebinds and verifies.
    preservation=module('n13_preservation',N/'verification/verify_preservation.py').verify()
    runtime=load(N/'verification/runtime-readiness-final.json')
    assert runtime['verdict']=='PASS_READONLY_RUNTIME_IDENTITY' and runtime['candidate_base']==CANDIDATE
    assert len(runtime['protected'])==7 and runtime['isolated_port_free'] and runtime['model_calls']==runtime['service_operations']==0
    for name,digest in runtime['checker_sources'].items():assert sha(Path(name))==digest
    tests=len(identities)+sum(r['tests'] for r in stdlib.values())
    return dict(verdict='PASS_OFFLINE_PREPARATION',candidate=CANDIDATE,tests=tests,harness_unique=len(identities),harness_raw=raw_count,
        duplicated_harness_cases=raw_count-len(identities),harness_groups=groups,stdlib=stdlib,red_runs=[],red_failures=0,product_sources_changed=False,
        initial_validation_failed_cases=1,initial_validation_preserved=True,
        input_pins=len(pins),source_pins=len(current['source_files']),product_baseline_tests=927,product_baseline_rerun=False,
        source_change='Only path/candidate/hash bindings and export tests changed; entry/adapter/bindings functions unchanged',
        actual_cases=0,model_calls=0,acceptance_credit=0,actual_case_allocation=0,result_review_allocation=0,
        E02='NOT_PASSED',T2='NOT_PASSED',preservation=preservation,runtime_readiness_sha256=sha(N/'verification/runtime-readiness-final.json'),
        recorded_at=dt.datetime.now(dt.timezone.utc).isoformat())
if __name__=='__main__':print(json.dumps(verify(),ensure_ascii=False,indent=2))
