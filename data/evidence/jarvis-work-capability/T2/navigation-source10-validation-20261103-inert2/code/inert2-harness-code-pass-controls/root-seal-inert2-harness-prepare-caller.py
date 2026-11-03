"""ROOT code-only gate and next-task control data. Run only after independent PASS."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import sys

C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101'
W2=W/'inert-revision2'
H=Path('H:/UltimaAI/UltimaAgent')
T=H/'data/evidence/jarvis-work-capability/T2'
OLD=T/'navigation-source10-validation-20261102'
V=T/'navigation-source10-validation-20261103-inert2'
PY=H/'tools/venv-openjarvis/Scripts/python.exe'
SOURCE='118ba152b007c30d358c8bc44c51aabe8ae820f0'
CALLER_NAMES=['root-inert-invocation.py','test_root_inert_invocation.py','inert-root-release-template.json','inert-root-caller-manifest.json','run-inert-root-caller-checks.py']
def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p): return json.loads(p.read_bytes())
def new(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(raw);f.flush();os.fsync(f.fileno())
def out(p,d):new(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
def append(p,text):
    with p.open('ab') as f:f.write(('\n'+text+'\n').encode('utf8'))
round_name=sys.argv[1] if len(sys.argv)>1 else 'initial'
assert round_name in {'initial','fix1'}
review=V/('harness-review-2' if round_name=='fix1' else 'harness-review-1')/'verdict.json';human=review.with_name('review.md')
proofpath=V/'code'/('root-inert2-harness-fix1-before-review.json' if round_name=='fix1' else 'root-inert2-harness-before-review.json')
companion=W/('task-4-inert2-harness-fix1-review-inputs.json' if round_name=='fix1' else 'task-4-inert2-harness-review-inputs.json')
human_copy=W/('task-4-inert2-harness-fix1-review-report.md' if round_name=='fix1' else 'task-4-inert2-harness-review-report.md')
r=read(review);m=read(V/'harness/manifest.json');proof=read(proofpath)
assert r['candidate']==SOURCE and r['spec']==r['spec_verdict']=='PASS' and r['quality']==r['quality_verdict']=='APPROVED'
assert r['execution_released'] is False and r['T2']=='NOT_PASSED' and r['findings']==[]
expected_base='a5b16aed8d8386d2e2018262a6e75677f00b958cb3553154af987a6658fe376d' if round_name=='fix1' else '935b3e3b1f42790c6bd3d7ebd88164f4cc47a9de9a1703557f5da0c59806bcb5'
assert r['base_manifest_sha256']==expected_base
if round_name=='fix1':
    assert {x['id']:x['verdict'] for x in r['finding_verdicts']}=={'PORT2-I01':'ADDRESSED'}
assert r['harness_manifest_sha256']==sha(V/'harness/manifest.json')==proof['manifest_sha256']
assert human.read_bytes()==human_copy.read_bytes()
for n,h in m['files'].items():assert sha(V/'harness'/n)==h
for p,h in read(companion)['inputs'].items():assert sha(Path(p))==h,p
for p,h in read(V/'code/root-preparation-inputs-before.json')['old_pins'].items():assert sha(Path(p))==h,p
oldclosed=set(read(OLD/'harness-code-gate.json')['closed_findings'])
assert len(oldclosed)==21 and set(r['held_closed'])==oldclosed
gate=V/'harness-code-gate.json'
out(gate,dict(schema_version=1,utc=dt.datetime.now(dt.timezone.utc).isoformat(),candidate=SOURCE,manifest_sha256=sha(V/'harness/manifest.json'),review=str(review),review_sha256=sha(review),report_sha256=sha(human),spec='PASS',quality='APPROVED',closed_findings=sorted(oldclosed),revision_closed_findings=['PORT2-I01'] if round_name=='fix1' else [],open_findings=[],covering_tests=proof['tests'],all_prior173_retained=True,root_readback_sha256=sha(proofpath),scope='SIX_FILE_PREPARATION_HARNESS_ONLY',concrete_enclosing_caller_reviewed=False,execution_released=False,actual=False,inert=False,profile=False,model=False,T2='NOT_PASSED',port_proof_cap_seconds=3,port_proof_ruling_sha256='295ca3be9a9040967e826341af084a369d90606c595306ec62b62c912d62c209'))
assert not W2.exists(),'Inspect any partial fresh W2 before proceeding'
authority=read(OLD/'inert-root-caller-preparation-authority.json')
authority.update(harness_manifest_sha256=sha(V/'harness/manifest.json'),harness_code_gate_sha256=sha(gate),write_paths=[str(W2/n) for n in CALLER_NAMES]+[str(W/'task-4-inert2-caller-report.md')],unit_evidence_new_prefix=str(V/'code/inert-root-caller-preparation-'),revision='inert2',issued_utc=dt.datetime.now(dt.timezone.utc).isoformat())
ap=V/'inert-root-caller-preparation-authority.json';out(ap,authority)
brief=f'''# Task4-PORT-REV2 Task2 — fresh concrete caller binding, preparation only

Read this first, your single exact task brief. Original order wo-ultimaagent-20261101-0021 remains E02/T2 NOT_PASSED. ROOT will register before dispatch. No subagents, commits, refs or push. Never run actual caller/main/HELLO/P4/native/model/profile/UI/audio/kill. Only deterministic mocked tests with fixed & '{PY}' -B -X utf8.

## Goal / exact allowed writes
Copy old reviewed caller manifestd4b73f6cf7731e149323d016c590a27656eefdd54d2fcf426d9b037e592168af and its other4 files from {W} into fresh {W2}. Exactly five ordinary files {', '.join(CALLER_NAMES)}. New unit receipts only {V}/code/inert-root-caller-preparation-*. Report only {W}/task-4-inert2-caller-report.md. Old5/report/controls/cases/fixture and NEW accepted harness6 immutable. No product source/default/config/SDK/P4/P1 edits; no dependency adds. SourceC118 and protected5/KWS/Hproduction0a31 remain fixed. Current qwen3-8b-uncensored digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330 only, no14B/larger/otherweights/fallback/download.

## Fresh bindings (use exact values)
V={V}; W2={W2}. Bind caller/driver V and test REAL_V, W derived from __file__.parent. New prep authority {ap} SHA{sha(ap)}; new harness manifest{sha(V/'harness/manifest.json')}; harness codegate{sha(gate)}; review {review} SHA{sha(review)}; human review{sha(human)}. Manifest depends on all six new harness files, their authority/candidate/deadline controls, new codegate/review, and new caller prep authority. Retain immutable old candidate source/dependency receipts and rootprotocol rulings at their existing OLD paths. Never blindly rebase the entire old candidate manifest's OLDV source/review dependencies. New candidate manifest rawcdfb and deadline144b intentionally retain historical references. New port ruling {W}/task-4-inert2-port-proof-ruling.md SHA295ca3be9a9040967e826341af084a369d90606c595306ec62b62c912d62c209 may be pinned as needed. Existing rootprotocol8c6b2d82 and publicationd45cc1a7 unchanged.

Future caller independent review path EXACT {V}/inert-root-caller-review-1/verdict.json; bind check_controls and all tests accordingly. No such review/approval/release/dispatch/launch/baseline/result exists/allowed now. Preserve pre-open absence contract at fresh V2. Fixed port18765 remains proposed target; no fallback/native probe in preparation, later ROOT must prove unused at fresh admission.

## Preserve behavior / verification
Only required namespace/dependency/hash metadata changes. Keep reviewed HELLO/livepid+nonce+earliestENTRY_NS, one-entryguard, ROOTdurablypreconsumedlaunch+dispatch beforeGO; private adapter.load exact2canonicalpaths same-issued-bytes guard BEFORE ORIGINAL admission nativequeries and post-admitstate checks; restored hooks; firstcause; one freshUUID; strict originalP4ownership; one serializedresult buffer→fsync/CLOSEpending→atomic no-replacement link→canonical bytes comparison BEFORE eligibleexit. No new controller/lock/auth mechanism or runtime target flexibility. All9RC01..09 independently closed protections retained. The shared private3s proof is already in accepted harness; caller must neither duplicate nor change it. Keep275/310/315,260/300/315/0retry and10061onlytruth; no origin renewal or physicalallfailure guarantee.

Retain ALL84 original JUnit classname::name IDs from {OLD}/code/inert-root-caller-preparation-20261102T230116820186Z/junit.xml (inspect actual existing JUnit filename if needed). Original per-file genuine fixtures stay readonly; new test outputs in V2. Add only meaningful pure binding negatives/positive if needed; run focus then ONE complete unselected new caller driver. Preserve exactargv/stdout/stderr/JUnit/source-before/after and raw source copies for every stage. Do not repeat old173 or unchanged product479+8. Save all failures honestly; no constant-positive mocks of evaluator. No actual main/CLI/runtime grant. Oldactual1 remains permanentFAIL1/1closed0remaining; newinert2 is still unallocated, model0.

Report DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED; include changedfiles, finalmanifest/report/receipt/JUnit SHA/count, prior84IDs retained, controlabsence, limits. Full report above; return compact status/path/tests/concerns only. Independent review follows ROOT readback; no auto native/profile/model/actual/T3/Owner release.
'''
bp=W/'task-4-inert2-caller-brief.md';new(bp,brief.encode('utf8'))
statepath=T/'current-run.json';s=read(statepath)
assert s['source10_inert_actual_result']=='PERMANENT_FAIL' and s['source10_inert_remaining_launches']==0
s.update(phase='E02_NAVIGATION_SOURCE10_INERT2_CALLER_PREPARATION',active_implementation_agent=None,active_review_agent=None,source10_inert2_harness_manifest_sha256=sha(V/'harness/manifest.json'),source10_inert2_harness_code_gate_sha256=sha(gate),source10_inert2_harness_review_sha256=sha(review),source10_inert2_harness_review_report_sha256=sha(human),source10_inert2_harness_status='CODE_PASS_PREPARATION_ONLY',source10_inert2_caller_preparation_authority_sha256=sha(ap),source10_inert2_caller_brief_sha256=sha(bp))
statepath.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
note=f'T4-PORT-REV2 Task1 CODE complete only: manifest{sha(V/"harness/manifest.json")},review{sha(review)},{proof["tests"]}tests/all173held/21closuresheld. NEWcaller prep authority{sha(ap)} and brief{sha(bp)} prepared; W2code notcreated/no allocation issued. Old1/1PERMANENTFAIL/model0/T2NOTPASSED.'
for p in [W/'progress.md',W/'resume-current.md',H/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md']:append(p,note)
print(json.dumps(dict(gate_sha256=sha(gate),caller_authority_sha256=sha(ap),caller_brief_sha256=sha(bp),model_calls=0,native_allocation=False)))
