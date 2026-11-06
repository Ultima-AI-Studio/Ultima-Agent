from pathlib import Path
import hashlib,importlib.util,json
N=Path(__file__).resolve().parents[1];R=N.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
spec=importlib.util.spec_from_file_location('real_bindings_readback',N/'code/bindings.py')
b=importlib.util.module_from_spec(spec);spec.loader.exec_module(b)
inputs=b.load_inputs(N/'inputs/input-manifest.json')
red=load(N/'offline/bindings-red/receipt.json');green=load(N/'offline/bindings-green/receipt.json')
assert red['exit_code']==1 and red['result']['errors']>0 and not red['result']['denied']
assert 'NotImplementedError' in (N/'offline/bindings-red/stderr.log').read_text('utf-8')
assert green['exit_code']==0 and green['result']['tests']==14 and green['result']['success'] is True
assert not green['result']['denied'] and green['sources_unchanged'] is True
for p,digest in green['sources'].items():assert sha(Path(p))==digest,p
for p,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/p)==digest,p
assert not (N/'actual').exists() and not (N/'release').exists()
audit=load(N/'inputs/reuse-audit.json')
assert audit['old_test_function_count']==len(audit['old_harness_test_function_ids'])==71
assert sum(row['changed'] for row in audit['source_comparisons'])==5
print(json.dumps(dict(verdict='PASS_CURRENT8B_INPUT_BINDING_ONLY',input_bindings=len(inputs['files']),product_files=len(inputs['source_files']),
    tests=14,old_test_functions_preserved=71,actual_product_runs=0,model_calls=0,actual_authority=False)))
