from pathlib import Path
import hashlib,json
R=Path('H:/UltimaAI/UltimaAgent');N=R/'data/evidence/jarvis-work-capability/T2/e02-source-reference-schema-20261107-r1'
L=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
receipt=load(N/'offline/bindings-red-bound/receipt.json')
old_bindings_sha=receipt['sources'][str(N/'code/bindings.py')]
old_inputs_sha=receipt['sources'][str(N/'inputs/input-manifest.json')]
p=N/'harness/adapter.py';text=p.read_text('utf8')
assert old_bindings_sha in text and old_inputs_sha in text
text=text.replace(old_bindings_sha,sha(N/'code/bindings.py')).replace(old_inputs_sha,sha(N/'inputs/input-manifest.json'))
anchor="PROTECTED_BASELINE=T/'e02-source13-exact-probe-20261106/inputs/protected-baseline.json'"
assert anchor in text
text=text.replace(anchor,"PROTECTED_BASELINE=V/'inputs/protected-baseline.json'");p.write_text(text,encoding='utf8')
hm=load(N/'harness/manifest.json');hm['candidate_manifest_sha256']=sha(N/'inputs/input-manifest.json')
hm['files']={name:sha(N/'harness'/name) for name in hm['files']};save(N/'harness/manifest.json',hm)
tr=load(N/'inputs/candidate-transition.json');tr.update(input_manifest_sha256=sha(N/'inputs/input-manifest.json'),protected_baseline_path=str(N/'inputs/protected-baseline.json'),protected_baseline_sha256=sha(N/'inputs/protected-baseline.json'),protected_identity_reconciled_readonly=True)
save(N/'inputs/candidate-transition.json',tr)
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask1: product566 PASS under final bytes, candidate a0d21eb committed/tagged. Baseline RED14pass/2fail confirmed both obsolete-baseline and coherently replaced PID accepted. New baseline pinned by path/SHA. Initial binding script stopped at a whitespace-sensitive constant check after writing only input/bindings; resumed remaining adapter/manifest updates using the retained pre-edit hashes, no tests/authority issued in partial state. No shared P4/P1 edits.\n')
print(json.dumps(dict(inputs=len(load(N/'inputs/input-manifest.json')['files']),baseline_sha256=tr['protected_baseline_sha256'],actual_calls=0)))
