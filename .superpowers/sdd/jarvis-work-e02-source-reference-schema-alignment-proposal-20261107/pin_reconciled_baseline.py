"""Pin a readonly observed identity, never replace a protected process."""
from pathlib import Path
import hashlib,json
R=Path('H:/UltimaAI/UltimaAgent');N=R/'data/evidence/jarvis-work-capability/T2/e02-source-reference-schema-20261107-r1'
L=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
red=load(N/'offline/bindings-red-bound/receipt.json')
assert red['result']==dict(tests=16,failures=2,errors=0,denied=[],success=False) and red['sources_unchanged']
baseline=N/'inputs/protected-baseline.json';reconcile=N/'inputs/protected-reconciliation.json'
b=load(baseline);old=Path(b['predecessor_baseline']);ob=load(old);rc=load(reconcile)
assert sha(old)==b['predecessor_baseline_sha256']==rc['previous_baseline_sha256']
assert sha(reconcile)==b['runtime_reconciliation_sha256']
assert b['protected5'][1:]==ob['protected5'][1:] and b['protected_listener_pair']==ob['protected_listener_pair']
assert b['protected5'][0]['pid']==11464 and ob['protected5'][0]['pid']==5708
assert rc['service_operations']==rc['termination_calls']==rc['model_calls']==rc['new_case_calls']==0
assert rc['unchanged_other_six'] and rc['same_executable'] and rc['same_parent_pid'] and rc['same_command_sha256']
assert not rc['continuous_liveness_claim']
inputs_path=N/'inputs/input-manifest.json';old_inputs_sha=sha(inputs_path);inputs=load(inputs_path)
assert inputs['protected_baseline_path']==str(old)
inputs['protected_baseline_path']=str(baseline)
sidecars=[baseline,reconcile,N/'inputs/ollama-app-start-excerpt.json',N/'verification/native-drift-metadata.json']
for p in sidecars:inputs['files'][str(p)]=sha(p)
save(inputs_path,inputs)
p=N/'code/bindings.py';old_bindings_sha=sha(p);text=p.read_text('utf8')
anchor="CANDIDATE_MANIFEST=N/'inputs/candidate-runtime-manifest.json'"
assert anchor in text and 'PROTECTED_BASELINE_SHA' not in text
text=text.replace(anchor,"PROTECTED_BASELINE=N/'inputs/protected-baseline.json'\nPROTECTED_BASELINE_SHA="+repr(sha(baseline))+'\n'+anchor)
text=text.replace("value['protected_baseline_path']==str(Q/'inputs/protected-baseline.json')","value['protected_baseline_path']==str(PROTECTED_BASELINE)")
text=text.replace("required={str(CANDIDATE_MANIFEST):CANDIDATE_MANIFEST_SHA", "required={str(PROTECTED_BASELINE):PROTECTED_BASELINE_SHA,str(CANDIDATE_MANIFEST):CANDIDATE_MANIFEST_SHA")
p.write_text(text,encoding='utf8')
p=N/'harness/adapter.py';text=p.read_text('utf8')
assert old_bindings_sha in text and old_inputs_sha in text
text=text.replace(old_bindings_sha,sha(N/'code/bindings.py')).replace(old_inputs_sha,sha(inputs_path))
anchor="PROTECTED_BASELINE=T/'e02-source13-exact-probe-20261106/inputs/protected-baseline.json'"
assert anchor in text, 'Baseline constant differs'
text=text.replace(anchor,"PROTECTED_BASELINE=V/'inputs/protected-baseline.json'")
p.write_text(text,encoding='utf8')
hm=load(N/'harness/manifest.json');hm['candidate_manifest_sha256']=sha(inputs_path)
hm['files']={name:sha(N/'harness'/name) for name in hm['files']};save(N/'harness/manifest.json',hm)
tr=load(N/'inputs/candidate-transition.json');tr.update(input_manifest_sha256=sha(inputs_path),protected_baseline_path=str(baseline),protected_baseline_sha256=sha(baseline),protected_identity_reconciled_readonly=True)
save(N/'inputs/candidate-transition.json',tr)
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask1: product566 PASS under final candidate bytes, committed/tagged a0d21eb. Valid baseline RED:14pass/2fail, old-baseline and coherently substituted PID both incorrectly accepted. Pin new exact baseline path/SHA and update harness constant only; preserve old baseline binding. No shared P4/P1 functions changed.\n')
print(json.dumps(dict(inputs=len(inputs['files']),baseline_sha256=sha(baseline),actual_calls=0)))
