"""Readonly aggregation of current source and saved guarded test receipts."""
from pathlib import Path
import ast,hashlib,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
OLD=N.parent/'e02-source13-real-controlled-preparation-20261107-r1'
R=N.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def junit(p):
    cases=list(ET.parse(p).iter('testcase'))
    assert cases and not any(c.find('failure') is not None or c.find('error') is not None or c.find('skipped') is not None for c in cases),p
    return {c.get('name') for c in cases}
def verify():
    assert not (N/'release').exists() and not (N/'actual').exists()
    predecessor=load(N/'inputs/predecessor.json')
    assert sha(OLD/'manifest.json')==predecessor['manifest_sha256']
    assert sha(OLD/'review/result-inputs/result-manifest.json')==predecessor['result_manifest_sha256']
    assert sha(OLD/'review/independent-result-review.json')==predecessor['result_review_sha256']
    for manifest in (OLD/'manifest.json',OLD/'review/result-inputs/result-manifest.json'):
        for name,digest in load(manifest)['files'].items():assert sha(OLD/name)==digest,name
    inputs=load(N/'inputs/input-manifest.json')
    for name,digest in inputs['files'].items():assert sha(Path(name))==digest,name
    for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
    for name in ('entry.py','bindings.py'):assert sha(N/'code'/name)==sha(OLD/'code'/name),name
    trees=[ast.parse((root/'harness/adapter.py').read_bytes()) for root in (OLD,N)]
    funcs=[{n.name:ast.dump(n,include_attributes=False) for n in t.body if isinstance(n,(ast.FunctionDef,ast.ClassDef))} for t in trees]
    changed={name for name in set(funcs[0])|set(funcs[1]) if funcs[0].get(name)!=funcs[1].get(name)}
    assert changed=={'check_native_baseline','validate_protected_members','validate_protected_native_members','admit','inert_admit'},changed
    tests=[{n.name for n in ast.parse((root/'harness/test_adapter.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')} for root in (OLD,N)]
    assert len(tests[0])==71 and tests[0]<=tests[1] and len(tests[1]-tests[0])==3
    current={p.name:sha(p) for p in (N/'harness').iterdir() if p.is_file()}
    chosen={};sets={}
    for group in ('recovery','base-a','base-b'):
        receipts=[p for p in sorted((N/'code').glob('harness-preparation-*/receipt.json')) if load(p).get('group')==group and load(p)['exit_code']==0]
        assert receipts,group
        path=receipts[-1];receipt=load(path)
        assert receipt['harness_before']==receipt['harness_after']==current
        assert receipt['inputs_unchanged'] and receipt['harness_unchanged'] and not receipt['timed_out']
        audit=load(path.parent/'offline-audit.json')
        assert audit['python_operations_clean'] and not audit['denied'] and audit['expected_probe_closed']
        sets[group]=junit(path.parent/'harness/adapter.xml')
        chosen[group]=str(path)
    historical=junit(OLD/'code/harness-preparation-20261106T162116319429Z/harness/adapter.xml')
    assert len(historical)==219 and not sets['base-a']&sets['base-b']
    assert sets['base-a']|sets['base-b']==historical
    assert len(sets['recovery'])==17 and not sets['recovery']&historical
    red=N/'code/harness-preparation-20261106T172319441476Z'
    red_cases=list(ET.parse(red/'harness/adapter.xml').iter('testcase'))
    failed=[c for c in red_cases if c.find('failure') is not None]
    assert len(red_cases)==17 and len(failed)==1
    assert failed[0].get('name')=='test_recovery_full_admit_observation_role[child-no-subprocess]'
    assert 'child admission attempted a subprocess-backed process snapshot' in failed[0].find('failure').get('message','')
    assert sha(red/'harness-source/adapter.py')==sha(OLD/'harness/adapter.py')
    for group,count in (('boundary',10),('entry',26)):
        receipt=load(N/'offline'/f'{group}-green/receipt.json')
        assert receipt['exit_code']==0 and receipt['sources_unchanged']
        assert receipt['result']['tests']==count and receipt['result']['success'] and not receipt['result']['denied']
        for name,digest in receipt['sources'].items():assert sha(Path(name))==digest,name
    grant=load(N/'inputs/granted-scope.json')
    assert grant['question_id']=='call_42e3d2dd124f406cb3ccebd14a9b1c0f' and grant['conditional_actual_case_allocation']==1 and grant['retry']==0
    return dict(verdict='PASS_OFFLINE_CHILD_ADMISSION_RECOVERY_ONLY',tests=272,
        original_harness_tests=219,new_admission_tests=17,boundary_tests=10,entry_tests=26,
        exact_original_case_ids_preserved=True,original_test_functions=71,bound_inputs=len(inputs['files']),
        runtime_changed_functions=sorted(changed),entry_and_product_unchanged=True,
        runs=chosen,red_run=str(red),retained_incomplete_timeout='harness-preparation-20261106T171740700189Z',
        retained_fixture_setup_failure='harness-preparation-20261106T172125286094Z',
        actual_calls=0,model_calls=0,E02='NOT_PASSED',T2='NOT_PASSED')
if __name__=='__main__':print(json.dumps(verify()))
