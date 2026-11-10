"""Seal offline handoff repair inputs; no profile or runtime authorization."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import xml.etree.ElementTree as ET

E=Path(__file__).resolve().parents[1];repo=E.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as stream:stream.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
def replace(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')

old=E/'history/reviewed-a19a00b'
assert sha(old/'manifest.json')=='2975e0f947be408baaa4222f8dd9fd4fbd1cb481adf005f38ea1bc4d8b91c3aa'
for row in load(old/'manifest.json')['files']:assert sha(old/row['path'])==row['sha256'],row['path']
for row in load(E/'inputs/source-bindings.json')['files']:assert sha(Path(row['path']))==row['sha256'],row['path']
code={p.name:sha(p) for p in (E/'code').glob('*.py')}
final=load(E/'offline/handoff-full-green/receipt.json')
assert final['counts']==dict(tests=89,failures=0,errors=0,skipped=0) and final['exit_code']==0
assert final['package_before']==final['package_after']==code
stages=[]
for name in ('handoff-red','handoff-green','handoff-full-green'):
    folder=E/'offline'/name;receipt=load(folder/'receipt.json')
    cases=ET.parse(folder/'junit.xml').findall('.//testcase')
    counts=dict(tests=len(cases),failures=sum(c.find('failure') is not None for c in cases),
        errors=sum(c.find('error') is not None for c in cases),skipped=sum(c.find('skipped') is not None for c in cases))
    assert counts==receipt['counts'] and receipt['sources_unchanged'] and receipt['package_unchanged'] and not receipt['denied_python_io']
    for file,digest in receipt['raw_sha256'].items():assert sha(folder/file)==digest
    for file,digest in receipt['package_before'].items():assert sha(folder/'snapshot'/file)==digest
    stages.append(dict(stage=name,receipt_sha256=sha(folder/'receipt.json'),**counts))
assert stages[0]['failures']==4 and stages[1]['failures']==0
assert not (E/'release').exists() and not (E/'runs').exists()
ruling=E/'inputs/handoff-cleanup-ruling.json'
save(ruling,dict(scope='R1-followup pending launch and qualification reserve',
    user_approval_sha256=sha(E/'verification/handoff-fix-authorization.json'),
    original_cutoffs_seconds=dict(work=275,profile_cleanup=310,seal=315),origin_renewed=False,
    calculation='15*(2*members+3)+10*members+2*launchers+(18 if console or prospective/pending role else 0)+5+15*remaining_queries',
    pending_members='max(actual known, prelaunch known + 2)',pending_launchers='max(actual launchers, prelaunch launchers + 1)',
    pending_queries='3 before launch; 2 after launch; 1 after discover; 0 after exact CIM query; cleared only after exact membership and retained handle checks',
    guard_locations=['before native launch','through HELLO wait','after HELLO validation','before discovery','after discovery/before exact query','after exact query','after retained handle acquisition'],
    usual_no_console_established_reserves_seconds=[132,214],prospective_role_reserves_seconds=[195,277],
    normal_reader_launch_before_origin_seconds=38,pending_hello_reserves_seconds=[180,262],
    pending_hello_latest_origin_seconds=[135,53],
    tradeoff='Conservative admission can reject an otherwise timely consumer; it does not grant the full275/310 as useful waiting time.',
    limits=['Synthetic query/process/clock effects only; original cleanup/deadline wrappers exercised.',
        'Extra actual known members increase reservation before further queries; arbitrary unknown trees/native/filesystem failures are not a cleanup guarantee.',
        'Five seconds is a local proof margin, not a hard bound on arbitrary I/O.'],runtime_authority=False))
entry=load(E/'entry-manifest.json')
for path,old_sha in entry['files'].items():
    if Path(path).parent!=E/'code':assert sha(Path(path))==old_sha,path
entry['files']={path:sha(Path(path)) for path in entry['files']};entry['files'][str(ruling)]=sha(ruling)
replace(E/'entry-manifest.json',entry)
save(E/'verification/handoff-fix-readback.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    verdict='PASS_OFFLINE_HANDOFF_REPAIR_ONLY',finding='R1-followup',stages=stages,code=code,
    entry_manifest_sha256=sha(E/'entry-manifest.json'),independent_current_source_review='PENDING',
    original_profile_runs=0,model_calls=0,native_workers=0,runtime_authority=False,
    old_review_sha256=sha(E/'review/independent-fixed-source-review.json'),original_83_tests_retained=True))
replace(E/'verification/code-preparation-gate.json',dict(verdict='NOT_READY_PENDING_HANDOFF_SOURCE_REVIEW',
    manifest_sha256=sha(E/'entry-manifest.json'),actual_authority=False,current_source_covered=False,full_offline_tests=89,
    previous_review_sha256=sha(E/'review/independent-fixed-source-review.json')))
plan=repo/'docs/plans/jarvis-work-e02-source13-cleanup-handoff-fix-plan-20261106.md'
with (E/'handoff-plan.md').open('xb') as stream:stream.write(plan.read_bytes())
ledger=repo/'.superpowers/sdd/jarvis-work-e02-source13-cleanup-handoff-fix-plan-20261106/progress.md'
with (E/'verification/handoff-implementation-ledger.md').open('xb') as stream:stream.write(ledger.read_bytes())
members={E/row['path'] for row in load(old/'manifest.json')['files']}
members.update([E/'review/independent-fixed-source-review.json',E/'verification/fixed-source-review-disposition.json',
    E/'verification/handoff-fix-authorization.json',E/'verification/handoff-fix-readback.json',E/'handoff-plan.md',
    E/'verification/handoff-implementation-ledger.md',E/'verification/begin-handoff-fix.py',Path(__file__),ruling])
for stage in stages:
    folder=E/'offline'/stage['stage']
    members.update(p for p in folder.iterdir() if p.is_file());members.update((folder/'snapshot').glob('*.py'))
replace(E/'manifest.json',dict(schema=2,scope='e02-source13-root-entry-handoff-repair-preparation',
    recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),runtime_authority=False,
    reviewed_predecessor_manifest_sha256=sha(old/'manifest.json'),entry_manifest_sha256=sha(E/'entry-manifest.json'),
    independent_review='PENDING_CURRENT_SOURCE',files=[dict(path=p.relative_to(E).as_posix(),bytes=p.stat().st_size,sha256=sha(p)) for p in sorted(members)]))
print(json.dumps(dict(package_files=len(members),runtime_bindings=len(entry['files']),tests=89,
    manifest=sha(E/'manifest.json'),entry_manifest=sha(E/'entry-manifest.json'),runtime_authority=False)))
