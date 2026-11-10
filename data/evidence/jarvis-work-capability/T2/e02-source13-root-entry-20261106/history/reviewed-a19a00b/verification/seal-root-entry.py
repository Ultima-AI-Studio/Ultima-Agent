"""Seal the completed offline entry for one preparation review; no actual authority."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import xml.etree.ElementTree as ET

E=Path(__file__).resolve().parents[1]
T=E.parent
B=T/'e02-source13-profile-binding-20261106'
H=T/'e01-source13-round3-20261106'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')

for row in load(E/'inputs/source-bindings.json')['files']:
    assert sha(Path(row['path']))==row['sha256'],row['path']
base=B/'profile-preparation/manifest.json';pins=load(base)
for name,value in pins['files'].items():assert sha(Path(name))==value,name
baseline=E/'inputs/protected-baseline.json'
with baseline.open('xb') as f:f.write((H/'inputs/protected-baseline.json').read_bytes())
code=sorted((E/'code').glob('*.py'))
assert len(code)==8
runtime={Path(row['path']) for row in load(E/'inputs/source-bindings.json')['files']}|set(code)|{baseline,base}
runtime.update(H/'code'/name for name in ('source_candidate_guard.py','fixture_adapter.py','fixture_manual_start.py','fixture_input_origin.py'))
manifest=dict(schema=1,kind='SOURCE13_PROFILE_ROOT_PREPARATION',runtime_released=False,
    candidate='269aca511d88412dbb9c15d23911138469a37aa2',model_digest=pins['model_digest'],
    base_profile_manifest_path=str(base),base_profile_manifest_sha256=sha(base),
    import_path=[str(base.parent),*pins['import_path'][1:]],protected_baseline_path=str(baseline),
    files={str(p):sha(p) for p in sorted(runtime)})
save(E/'entry-manifest.json',manifest)
stages=[];members=set(code)|{E/'plan.md',E/'entry-manifest.json',E/'execution-proposal.md',Path(__file__)}
members.update(p for p in (E/'inputs').iterdir() if p.is_file())
for folder in sorted((E/'offline').iterdir()):
    r=load(folder/'receipt.json')
    assert r['sources_unchanged'] and r['package_unchanged'] and not r['denied_python_io']
    assert r['original_profile_runs']==r['model_calls']==0 and not r['runtime_authority']
    cases=ET.parse(folder/'junit.xml').findall('.//testcase')
    counts=dict(tests=len(cases),failures=sum(x.find('failure') is not None for x in cases),
        errors=sum(x.find('error') is not None for x in cases),skipped=sum(x.find('skipped') is not None for x in cases))
    assert counts==r['counts'] and len(load(folder/'inventory.json'))==counts['tests']
    for name,value in r['raw_sha256'].items():assert sha(folder/name)==value
    for name,value in r['package_before'].items():assert sha(folder/'snapshot'/name)==value
    members.update(p for p in folder.iterdir() if p.is_file())
    members.update((folder/'snapshot').glob('*.py'))
    stages.append(dict(stage=folder.name,receipt_sha256=sha(folder/'receipt.json'),exit_code=r['exit_code'],**counts))
final=load(E/'offline/full-entry-green/receipt.json')
assert final['counts']==dict(tests=81,failures=0,errors=0,skipped=0) and final['exit_code']==0
assert final['package_after']=={p.name:sha(p) for p in code}
save(E/'verification/task2-readback.json',dict(verdict='PASS_OFFLINE_SYNTHETIC_CONTRACTS_ONLY',stages=stages,
    final_tests=81,entry_manifest_sha256=sha(E/'entry-manifest.json'),runtime_authority=False,
    actual_profile_runs=0,actual_model_calls=0,OS_native_activity=None,base_dependency_count=len(pins['files']),
    base_unchanged=True,source_binding_count=len(load(E/'inputs/source-bindings.json')['files'])))
members.add(E/'verification/task2-readback.json')
for name in ('task1-local-checkpoint.json','fixed-runner-readback.json','compatibility-observations.json'):
    members.add(E/'verification'/name)
save(E/'manifest.json',dict(schema=1,scope='e02-source13-root-entry-preparation',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    runtime_authority=False,entry_manifest_sha256=sha(E/'entry-manifest.json'),
    files=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(members)]))
(E/'review').mkdir(exist_ok=True)
text=f'''# Whole entry preparation review input

Package manifest SHA256: {sha(E/'manifest.json')}
Runtime entry manifest SHA256: {sha(E/'entry-manifest.json')}
Review root: {E}
Task2: completed offline81/81. No actual profile/native worker/model/DNS/HTTP/UI/audio/service run.
Frozen product candidate269aca511d88412dbb9c15d23911138469a37aa2 and original B profile untouched.
Read plan.md, execution-proposal.md, inputs/implementation-rulings.json and inputs/progress-observation-ruling.json.
Read all8 current code files and actual reuse sources bound by entry-manifest.json. Do not use historical E01/source10/B PASS as current integration proof.
Inspect full retained RED/GREEN receipts, raw JUnit/test IDs and source snapshots; only final full81 is the current complete suite.
Root IF01/IF02B/IF02C are in inputs/source-bindings.json. Pay particular attention to earliest clock, venv launcher vs actual native role, retained handle, exact7 identities, immutable original profile, derived import path, child startup clean environment, first work/cleanup observations, two readbacks,315 finalexit/cleanup, release denial and one consumed allocation.
Ruling: cleanup completion proof is conservative and may reject late-visible seal even if internal cleanup met310. Scoped normal DNS must be disclosed in future approval; no completely network-free claim.
No subprocess/profile/SDK runtime/test/native/HTTP/DNS/UI/audio/service operations for reviewer; file read/hash/AST/git readback only.
No implementer or further reviewer delegation. One final report only, saved at review/independent-preparation-review.json; this is the only allowed report write.
Required report fields: reviewer=root-independent,scope=e02-source13-root-entry-preparation,verdict=PASS or NEEDS_FIXES,manifest_sha256=(runtime entry manifest above),package_manifest_sha256=(package above),runtime_authority=false,findings(list with severity/path/line/effect/remedy),declined_to_judge(list),evidence,limitations.
The report is preparation only and cannot authorize actual execution or actual result review.
'''
(E/'review/review-input.md').write_text(text,encoding='utf-8',newline='\n')
print(json.dumps(dict(files=len(members),entry_files=len(runtime),stages=len(stages),tests=81,manifest=sha(E/'manifest.json'),entry_manifest=sha(E/'entry-manifest.json'))))
