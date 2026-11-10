"""Read fresh Task2 evidence and current bytes; never starts a product case."""
from pathlib import Path
import ast,hashlib,importlib.util,json,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1];R=N.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
spec=importlib.util.spec_from_file_location('task2_readback_bindings',N/'code/bindings.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
inputs=b.load_inputs(N/'inputs/input-manifest.json')
current=load(N/'harness/manifest.json')
assert current['runtime_authority'] is False
for name,digest in current['files'].items():assert sha(N/'harness'/name)==digest,name
functions=[node.name for node in ast.parse((N/'harness/test_adapter.py').read_bytes()).body if isinstance(node,ast.FunctionDef) and node.name.startswith('test_')]
old=load(N/'inputs/reuse-audit.json')['old_harness_test_function_ids']
assert set(functions)==set(old) and len(functions)==71
runs=sorted((N/'code').glob('harness-preparation-*'))
run=runs[-1];receipt=load(run/'receipt.json');audit=load(run/'offline-audit.json')
assert receipt['exit_code']==receipt['pytest_exit_code']==0 and receipt['harness_unchanged'] and receipt['inputs_unchanged']
suite=ET.parse(run/'harness/adapter.xml').getroot().find('testsuite')
assert suite.attrib['tests']=='219' and suite.attrib['failures']==suite.attrib['errors']=='0'
ids=[item.attrib['name'] for item in suite.findall('testcase')]
first=ET.parse(runs[0]/'harness/adapter.xml').getroot().find('testsuite')
assert sorted(ids)==sorted(item.attrib['name'] for item in first.findall('testcase'))
for name in current['files']:assert sha(run/'harness-source'/name)==sha(N/'harness'/name),name
assert sha(run/'harness-source/offline_pytest.py')==sha(N/'verification/offline_pytest.py')
assert not audit['denied'] and audit['expected_probe_closed'] and audit['eager']['eager']['clean']
boundary=load(N/'offline/boundary-final/receipt.json')
assert boundary['exit_code']==0 and boundary['result']['tests']==10 and not boundary['result']['denied']
for name,digest in boundary['sources'].items():assert sha(Path(name))==digest,name
replay=sorted((N/'offline').glob('plumbing-replay-*'))[-1]
replay_receipt=load(replay/'receipt.json');replay_audit=load(replay/'offline-audit.json');replay_data=load(replay/'plumbing-replay.json')
assert replay_receipt['exit_code']==0 and replay_receipt['sources_unchanged']
for name,digest in replay_receipt['sources'].items():assert sha(Path(name))==digest,name
assert not replay_audit['denied'] and replay_audit['eager']['eager']['clean']
case=N.parent/'e02-source13-exact-probe-20261106/runs/a47c74c4-58e7-4a63-ad7d-f63be9c17a51/worker/case'
for name,digest in replay_data['evidence_files_unchanged'].items():assert sha(case/name)==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
assert not (N/'actual').exists() and not (N/'release').exists()
print(json.dumps(dict(verdict='PASS_SOURCE13_REAL_HARNESS_OFFLINE_ONLY',tests=230,original_harness_cases=219,
    protected_and_transport_checks=10,read_only_sdk_replay=1,original_test_functions=71,
    bound_files=len(inputs['files']),harness_manifest_sha256=sha(N/'harness/manifest.json'),
    full_suite=str(run),replay=str(replay),actual_product_runs=0,model_calls=0,actual_authority=False)))
