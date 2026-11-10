"""Seal the one allowed review fix; preserve NEEDS_FIXES and deny runtime."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import xml.etree.ElementTree as ET
E=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
def replace(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
review=load(E/'review/independent-preparation-review.json')
assert review['verdict']=='NEEDS_FIXES' and [f['id'] for f in review['findings']]==['R1']
assert sha(E/'review/independent-preparation-review.json')=='c3a9977b7374e36b4bbaba21b4e1d794af84520523174f70237f2aa5ffa4c042'
before=load(E/'history/reviewed-83312d5/manifest.json')
for row in before['files']:assert sha(E/'history/reviewed-83312d5'/row['path'])==row['sha256']
for row in load(E/'inputs/source-bindings.json')['files']:assert sha(Path(row['path']))==row['sha256']
code={p.name:sha(p) for p in (E/'code').glob('*.py')};assert len(code)==8
final=load(E/'offline/review-r1-full-green/receipt.json')
assert final['exit_code']==0 and final['counts']==dict(tests=83,failures=0,errors=0,skipped=0)
assert final['package_after']==code and final['package_before']==code and final['sources_unchanged']
stages=[]
for folder in sorted((E/'offline').iterdir()):
    receipt=load(folder/'receipt.json');cases=ET.parse(folder/'junit.xml').findall('.//testcase')
    counts=dict(tests=len(cases),failures=sum(n.find('failure') is not None for n in cases),
        errors=sum(n.find('error') is not None for n in cases),skipped=sum(n.find('skipped') is not None for n in cases))
    assert counts==receipt['counts'] and receipt['sources_unchanged'] and receipt['package_unchanged'] and not receipt['denied_python_io']
    for name,value in receipt['raw_sha256'].items():assert sha(folder/name)==value
    stages.append(dict(stage=folder.name,receipt_sha256=sha(folder/'receipt.json'),**counts))
entry=load(E/'entry-manifest.json')
entry['files']={name:sha(Path(name)) for name in entry['files']}
ruling=E/'inputs/review-r1-cleanup-ruling.json';entry['files'][str(ruling)]=sha(ruling)
replace(E/'entry-manifest.json',entry)
fix=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),scope='ONE_BOUNDED_ROOT_ENTRY_REVIEW_FIX',finding='R1',
    root_status='PASS_OFFLINE_FIX_VERIFICATION_ONLY',independent_verdict='NEEDS_FIXES_PRE_FIX_SOURCE',
    review_sha256=sha(E/'review/independent-preparation-review.json'),entry_manifest_sha256=sha(E/'entry-manifest.json'),
    reviewed_entry_manifest_sha256=review['manifest_sha256'],targeted_red=dict(tests=2,failures=2),targeted_green=dict(tests=2,failures=0),
    full_green=dict(tests=83,failures=0,errors=0,skipped=0),stages=stages,code=code,
    original_profile_runs=0,model_calls=0,actual_case_allocation=0,actual_result_review_allocation=0,runtime_authority=False,
    independent_review_covers_current_source=False,next_scope='fresh_readonly_review_of_fixed_source_required')
save(E/'verification/review-r1-fix-readback.json',fix)
dispositions=[]
for item in review['declined_to_judge']:
    dispositions.append(dict(item=item,root_ruling='Accepted unproven limit; no runtime, model-quality, OS-wide or acceptance claim is derived from this preparation.',
        cost_if_wrong='An actual later gate may fail; current E02/T2 and runtime release remain denied.'))
save(E/'verification/root-review-disposition.json',dict(controller='root',independent_verdict='NEEDS_FIXES',
    review_sha256=fix['review_sha256'],finding='R1',root_fix_verification=fix['root_status'],
    fix_receipt_sha256=sha(E/'verification/review-r1-fix-readback.json'),entry_manifest_sha256=fix['entry_manifest_sha256'],
    runtime_authority=False,preparation_verdict='NOT_READY_PENDING_FIXED_SOURCE_REVIEW',declined_judgment_dispositions=dispositions,
    outstanding_gate='Independent exact-source review after repair, required by original IF01; no author self-signature.'))
save(E/'verification/code-preparation-gate.json',dict(verdict='NOT_READY_PENDING_FIXED_SOURCE_REVIEW',
    manifest_sha256=sha(E/'entry-manifest.json'),review_sha256=fix['review_sha256'],actual_authority=False,
    independent_review_verdict='NEEDS_FIXES',current_source_covered=False,full_offline_tests=83))
members={E/row['path'] for row in before['files']}
members.update([E/'review/independent-preparation-review.json',E/'verification/review-r1-fix-readback.json',
    E/'verification/root-review-disposition.json',E/'verification/code-preparation-gate.json',ruling,Path(__file__)])
for stage in ('review-r1-red','review-r1-green','review-r1-full-green'):
    folder=E/'offline'/stage
    members.update(p for p in folder.iterdir() if p.is_file());members.update((folder/'snapshot').glob('*.py'))
replace(E/'manifest.json',dict(schema=2,scope='e02-source13-root-entry-repaired-preparation',
    recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),runtime_authority=False,
    reviewed_predecessor_manifest_sha256=review['package_manifest_sha256'],entry_manifest_sha256=sha(E/'entry-manifest.json'),
    independent_review='PENDING_CURRENT_SOURCE',files=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(members)]))
save(E/'verification/fixed-source-review-request.json',dict(scope='one_readonly_fixed_source_independent_review',
    requested=False,allocated=False,consumed=False,prior_review_consumed=True,
    manifest_sha256=sha(E/'manifest.json'),entry_manifest_sha256=sha(E/'entry-manifest.json'),
    actual_case_allocation=0,actual_result_review_allocation=0,runtime_authority=False,
    report_path=str(E/'review/independent-fixed-source-review.json')))
print(json.dumps(dict(files=len(members),entry_files=len(entry['files']),tests=83,manifest=sha(E/'manifest.json'),entry_manifest=sha(E/'entry-manifest.json'),gate='NOT_READY_PENDING_FIXED_SOURCE_REVIEW')))
