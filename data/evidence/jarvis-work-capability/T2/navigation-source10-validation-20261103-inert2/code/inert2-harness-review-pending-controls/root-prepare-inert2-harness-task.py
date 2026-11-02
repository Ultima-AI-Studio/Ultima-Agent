"""ROOT data preparation and queue registration only; no native/model execution."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import os
import subprocess

C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
H=Path('H:/UltimaAI/UltimaAgent')
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101'
T=H/'data/evidence/jarvis-work-capability/T2'
OLD=T/'navigation-source10-validation-20261102'
V=T/'navigation-source10-validation-20261103-inert2'
NAMES=['adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md','manifest.json']
PY=H/'tools/venv-openjarvis/Scripts/python.exe'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def new(path,raw):
    path.parent.mkdir(parents=True,exist_ok=True)
    with path.open('xb') as f:
        f.write(raw); f.flush(); os.fsync(f.fileno())
    assert path.read_bytes()==raw
def obj(path,data): new(path,(json.dumps(data,indent=2,ensure_ascii=False)+'\n').encode('utf8'))
def append(path,text):
    with path.open('ab') as f: f.write(('\n'+text+'\n').encode('utf8')); f.flush(); os.fsync(f.fileno())
assert subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip()=='118ba152b007c30d358c8bc44c51aabe8ae820f0'
assert subprocess.call(['git','diff','--quiet'],cwd=C)==0
assert subprocess.call(['git','diff','--cached','--quiet'],cwd=C)==0
assert not V.exists(), 'Fresh namespace required; inspect any partial result before resuming'
now=dt.datetime.now(dt.timezone.utc).isoformat()
candidate=(OLD/'source10-candidate-manifest.json').read_bytes()
deadline=(OLD/'harness-deadline-design/root-decision.json').read_bytes()
assert sha(candidate)=='cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50'
assert sha(deadline)=='144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'
assert sha((OLD/'harness/manifest.json').read_bytes())=='935b3e3b1f42790c6bd3d7ebd88164f4cc47a9de9a1703557f5da0c59806bcb5'
assert sha((W/'inert-root-caller-manifest.json').read_bytes())=='d4b73f6cf7731e149323d016c590a27656eefdd54d2fcf426d9b037e592168af'
ruling=W/'task-4-inert2-port-proof-ruling.md'
plan=W/'task-4-inert2-implementation-plan.md'
assert sha(ruling.read_bytes())=='295ca3be9a9040967e826341af084a369d90606c595306ec62b62c912d62c209'
assert sha(plan.read_bytes())=='ab556bf6dd13783f19cb28a51d783b3eb457269d6b255697c4a390e121fa8b61'
fixture=OLD/'code/harness-preparation-20261102T215807022506Z/temp/test_fix1_genuine_synthetic_ex0'
assert sha((fixture/'trusted-export.json').read_bytes())=='a19afa70e6c580b1f9b0976fb2922cdd85080f1d50b2cd693195c478f1d72b95'
assert sha((fixture/'runtime-inputs.json').read_bytes())=='d46a24a07a2d92fb02108e586ca514f6b47d146084b8b1682549614f6bf1c911'
protected_paths=[OLD/'harness'/n for n in NAMES]+[W/n for n in ['root-inert-invocation.py','test_root_inert_invocation.py','inert-root-release-template.json','inert-root-caller-manifest.json','run-inert-root-caller-checks.py']]
protected_paths += [p for p in fixture.rglob('*') if p.is_file()]
for n in ['harness-approval.json','inert-root-launch-allocation.json','inert-root-live-hello.json','inert-root-dispatch.json','inert-root-release.json','inert-actual1-root-readback.json','inert-post-case-port-diagnostic.json']:
    p=OLD/n
    if p.exists(): protected_paths.append(p)
case=OLD/'inert/1cd7559d-0af9-455a-8c2b-cdecd5970197'
protected_paths += [p for p in case.rglob('*') if p.is_file()]
old_pins={str(p):sha(p.read_bytes()) for p in protected_paths}
new(V/'source10-candidate-manifest.json',candidate)
new(V/'harness-deadline-design/root-decision.json',deadline)
authority=json.loads((OLD/'harness-preparation-authority.json').read_text('utf8'))
authority.update(issued_utc=now,root_authorization='user continuous original workorder; T4-PORT-REV2 preparation only',candidate_manifest=str(V/'source10-candidate-manifest.json'),allowed_new_files=[str(V/'harness'/n) for n in NAMES],allowed_test_receipt_parent=str(V/'code'),readonly_process_observation_allowed=False,port_proof_ruling=str(ruling),port_proof_ruling_sha256=sha(ruling.read_bytes()),revision='inert2',prior_failed_allocation_preserved=True,prior_failed_allocation_remaining=0)
obj(V/'harness-preparation-authority.json',authority)
prep_sha=sha((V/'harness-preparation-authority.json').read_bytes())
obj(V/'code/root-preparation-inputs-before.json',dict(issued_utc=now,old_pins=old_pins,candidate_sha256=sha(candidate),deadline_sha256=sha(deadline),port_ruling_sha256=sha(ruling.read_bytes()),preparation_authority_sha256=prep_sha,model_calls=0,actual=False,inert=False))
brief=f'''# Task4-PORT-REV2 Task1 — fresh harness, mocked preparation ONLY

Read this first: this file is your exact task requirements. Original order wo-ultimaagent-20261101-0021, E02/T2 NOT_PASSED; this is a narrow technical continuation. No subagents, no Git commits/pushes; ROOT handles evidence publication. One writer only.

## Goal / allowed writes
Create exactly six ordinary files under {V}/harness: {', '.join(NAMES)}; copy their reviewed counterparts from {OLD}/harness, then make only the port-proof/path/pin revision below. New mocked run receipts only {V}/code/harness-preparation-*. Report ONLY {W}/task-4-inert2-harness-report.md. Do not write original C product sources or old V/W files, original fixture, controls, reports, or output dirs. Never copy operational authority/approval/baseline/dispatch/release/launch/results into V2. Source HEAD fixed118ba152b007c30d358c8bc44c51aabe8ae820f0 and tracked/index clean.

## Exact inputs / decisions
- ROOT ruling {ruling}, SHA295ca3be9a9040967e826341af084a369d90606c595306ec62b62c912d62c209; read it FULL. Diagnosis {W}/task-4-inert-port-native-diagnosis-report.md SHA3557e4d5c9fe95ec6481266a396981539d5b91b637963dca2ad5d7d5da0300e4 may clarify existing sites, not supersede shared-mode ruling.
- Old manifest935b3e3b1f42790c6bd3d7ebd88164f4cc47a9de9a1703557f5da0c59806bcb5, all173 old full JUnit IDs in {OLD}/code/harness-preparation-20261102T221401644962Z/harness/adapter.xml. Retain each ID; new tests are additive. Existing21 independently closed findings held unless changed diff causes a concrete regression. Do not reimplement old gates or broad-review C.
- New prep authority {V}/harness-preparation-authority.json SHA{prep_sha}. Bind this in new adapter.PREPARATION_SHA, run_checks.snapshot and manifest. Candidate manifest rawcdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50 and T4-D315-01 raw144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47 already copied by ROOT. They intentionally retain OLD immutable source/review locations; don't rewrite them.
- Exactly ONE frozen genuine reviewer fixture remains READONLY {fixture}; pin its existing declared members/byte hashes before/after in the driver. test_adapter.py's prior a.V-relative lookup must be bound explicitly to this OLD location. trusted-export a19afa70e6c580b1f9b0976fb2922cdd85080f1d50b2cd693195c478f1d72b95 and runtime-inputs d46a24a07a2d92fb02108e586ca514f6b47d146084b8b1682549614f6bf1c911. Do not regenerate/relocate/change fixture bytes. New temp outputs only new V2.
- Fixed interpreter for ALL Python: & '{PY}' -B -X utf8. No system/python/Cvenv, dependencies, sockets, native processes/queries, model/HTTP, actual/inert/profile/UI/audio, environment-wide monkeypatches or global config changes. Native/P4/P1/SDK imports may only execute existing safely guarded definitions; OS boundaries mocked.

## Behavior / RED→GREEN
The existing private single-connect proof cap changes1→3s in BOTH inert AND future actual modes, at BOTH real originalP4.cleanup and substantive validate_observed_package proof sites. This is shared private behavior, no mode/port/config option. One connect at each existing site, never poll/retry. Original P4 settimeout(1) hint stays in immutable source; reviewed PrivateIO connect-time raw setter may supersede it up to private3 clipped at socket allocation and again immediately before connect. Both prior bottlenecks SocketIO.socket b.clip(1) AND Probe.connect_ex b.clip(min(1,allowance)) must be addressed. Deadline remaining clips3; time spent constructing/socket setup reduces allowance, expiry forbids further IO, exactcutoff return alone admits no next IO. Keep definitive ECONNREFUSED/10061 only;10035/10060/0/other/error/missing/late10061 unknown/fail. Close and restoration, source pins/ownership, firstcause/permanent eligibility unchanged.

Add meaningful delayed-refusal tests using fake clock/socket delay2.0139454s: wait advances min(allowance,delay), returns10035 if incomplete,10061 iff sufficiently waited. Exercise real original P4 cleanup with OS mocked (show original P4's any-nonzero verdict vs adapter strict verdict), and REAL substantive observer via existing sealed mocked fixture. Focused RED under old1s must fail expected eligible outcomes at both sites; GREEN under cap3 succeeds with exactly one connect and correct effective timing. Avoid constant10061 fake or stubbing the evaluator under test. Cover unknown/open/error/late, sufficient-v-clipped remaining, setup time, zero before connect, both modes sharedbehavior, rawsocketclose/private restoration. Existing relevant deadline controls may be reused when they substantively cover these; no mirror assertions.

Keep work275/cleanup310/seal+trustedobservation315,260service/300client/315outer/0retry, original earliest preadmission monotonic_ns; no reserve/renewal or physical OS/all-failure preemption claim. Optional existing port event may record configured/effective timeout and start/end only if useful; no telemetry framework.

## Verification / report
Use new run_checks.py with exact controlled environment and new raw6 snapshots/source-before/after/JUnit/receipt. Focused RED→GREEN then ONE full unselected new harness run; report exact argv, exit, IDs retained, receipts/hashes, changedfiles, what remains unqualified. Do not rerun unchanged product479+compat8 or caller84. No actual case allocation or Root release. The old actual1 remains PERMANENT_FAIL1/1 consumed/0remaining and model0. Report status DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED; include any failures honestly. Return only status, report path, one-line test summary, concerns; ROOT independently reads raw evidence and dispatches review.
'''
new(W/'task-4-inert2-harness-brief.md',brief.encode('utf8'))
preflight='''T4-PORT-REV2 preflight:
| Pair/task | Produces/consumes | Scan |
| Task1 self | six fresh harness files, delayed-refusal RED/GREEN, old173 IDs | consistent; no native allowance |
| Task2 self | five fresh caller files, retained84 and new hashes | consistent; waits Task1 CODE review |
| Task1→Task2 | V2 manifest/review/gate/prep hashes consumed by W2 | sequential; no active shared writer |
Ruling: shared fixed3s at both private proof sites/modes — qualify same proof later actual will use — costs bounded extra wait or conservative fail if remaining insufficient. ROOT ruling295ca3be; unchanged275/310/315 and10061 truth. Old actual1 immutablePERMANENT_FAIL, no allocation issued. Task4 original not complete; no historical loop/budget reset.
'''
append(W/'progress.md',preflight)
statepath=T/'current-run.json'
state_raw=statepath.read_bytes(); new(W/'current-run-before-inert2-harness-prep.json',state_raw)
state=json.loads(state_raw)
state.update(phase='E02_NAVIGATION_SOURCE10_INERT2_HARNESS_PREPARATION',active_diagnostic_agent=None,active_implementation_agent=None,source10_inert2_validation_root=str(V),source10_inert2_harness_preparation_authority_sha256=prep_sha,source10_inert2_harness_brief_sha256=sha(brief.encode('utf8')),source10_inert2_port_ruling_sha256=sha(ruling.read_bytes()),source10_inert2_allocation_released=False,source10_inert2_actual=False,source10_inert2_model_calls=0)
statepath.write_text(json.dumps(state,indent=2,ensure_ascii=False)+'\n',encoding='utf8')
globalpath=Path('H:/UltimaAI/_shared/queue/global-queue-index.md')
queue_raw=globalpath.read_bytes(); new(W/'global-queue-before-inert2-harness-prep.md',queue_raw)
lines=queue_raw.decode('utf8').splitlines(keepends=True)
matches=[i for i,line in enumerate(lines) if line.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')]
assert len(matches)==1
i=matches[0]; ending='\r\n' if lines[i].endswith('\r\n') else '\n'
lines[i]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | 仅当前8B；保留惰性1/1失败，正在新目录修正端口证明3秒上限并模拟验证；模型/实际/T3未放行 |'+ending
globalpath.write_bytes(''.join(lines).encode('utf8'))
append(H/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md','T4-PORT-REV2 Task1 registered: freshV2 harness mock-only; shared private3s definitive10061 proof,275/310/315unchanged; original actual1PERMANENT_FAIL1/1 preserved/model0. Rootruling295ca3be and freshprepauthority; Task2/W2/native allocation not dispatched.')
append(W/'resume-current.md',f'T4-PORT-REV2 rootdata READY; V2 {V} created onlycandidate/deadline/NEWprepauthority{prep_sha}/beforepins. Brief task-4-inert2-harness-brief.md SHA{sha(brief.encode("utf8"))}; freshsingleimplementer next. AlloldV6/W5/frozenfixture/nativecase22 pinned in V2/code/root-preparation-inputs-before.json, no codecopiedbyROOT. Old1/1FAIL0remaining, no native2allocation/model/profile/actual/T3. GoalACTIVE.')
assert old_pins=={str(p):sha(p.read_bytes()) for p in protected_paths}
print(json.dumps(dict(V=str(V),preparation_sha256=prep_sha,brief_sha256=sha(brief.encode('utf8')),old_protected_files=len(old_pins),actual=False,model_calls=0),indent=2))
