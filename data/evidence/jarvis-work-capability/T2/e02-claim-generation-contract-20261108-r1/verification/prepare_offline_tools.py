"""Adapt accepted offline runners without widening their runtime authority."""
from pathlib import Path
import ast,hashlib,json
N=Path(__file__).resolve().parents[1];T=N.parent
B=T/'e02-output-structure-diagnostics-20261108-r2'
J=T/'e02-native-pattern-json-20261107-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
copies={}
for src,dst in [(B/'verification/compatibility_checks.py',N/'verification/compatibility_checks.py'),
                (J/'verification/grammar_checks.py',N/'verification/grammar_checks.py')]:
    with dst.open('xb') as f:f.write(src.read_bytes())
    copies[str(src)]=dict(destination=str(dst),sha256=sha(src))
for sub,names in [('upstream',['json_schema_to_grammar.py','json-schema-to-grammar.cpp','grammars-README.md','provenance.json']),
                  ('native-log-supplement',['unvalidated-output.txt','capture.json'])]:
    (N/'inputs'/sub).mkdir()
    for name in names:
        src=J/'inputs'/sub/name;dst=N/'inputs'/sub/name
        with dst.open('xb') as f:f.write(src.read_bytes())
        copies[str(src)]=dict(destination=str(dst),sha256=sha(src))
runner=N/'verification/run_product_checks.py';text=runner.read_text('utf8')
text=text.replace("GROUPS={'structure-red':", "GROUPS={'contract-red':['test_work_claim_generation_contract.py'],'contract-green':['test_work_claim_generation_contract.py'],'baseline-json':['test_work_sampler_json_strings.py'],'structure-red':",1)
old="paths += [N/'inputs/accepted-dependency-pins.json',N/'verification/compatibility_checks.py']"
assert text.count(old)==1
text=text.replace(old,"paths += [N/'inputs/accepted-dependency-pins.json',N/'verification/compatibility_checks.py',N/'verification/grammar_checks.py',N/'inputs/upstream/json_schema_to_grammar.py']")
ast.parse(text);runner.write_text(text,encoding='utf8',newline='\n')
batch_source=B/'verification/run_final_regressions.py';batch=batch_source.read_text('utf8')
batch=batch.replace("GROUPS=['structure-green'", "GROUPS=['contract-green','grammar','structure-green'",1)
ast.parse(batch)
with (N/'verification/run_final_regressions.py').open('x',encoding='utf8',newline='\n') as f:f.write(batch)
with (N/'inputs/offline-tool-bindings.json').open('x',encoding='utf8',newline='\n') as f:json.dump(dict(copies=copies,batch_source_sha256=sha(batch_source),runner_sha256=sha(runner),guard_sha256=sha(N/'verification/product_pytest.py'),scope='Exact existing guards, 90-second groups, two workers, no model/network/service authority; add focused contract and reference grammar groups'),f,indent=2)
print(json.dumps(dict(copied=len(copies),product_changes=0,runner='READY_OFFLINE_ONLY')))
