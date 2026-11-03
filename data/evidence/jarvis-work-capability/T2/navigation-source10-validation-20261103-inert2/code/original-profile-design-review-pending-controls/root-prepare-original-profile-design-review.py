"""ROOT documentation/hash review packet only; no profile/import/native action."""
from pathlib import Path
import datetime as dt
import difflib
import hashlib
import json

C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101'
H=Path('H:/UltimaAI/UltimaAgent');T=H/'data/evidence/jarvis-work-capability/T2';V=T/'navigation-source10-validation-20261103-inert2'
expected={'task-4-original-corpus-profile-design.md':'ae077cc902a708e9068184a8e9b7c19125edcdacfdfd2e55fd996cf6f81191d9','task-4-original-corpus-profile-implementation-plan.md':'beb9ea6b2a24563b0dba4072a7ab36559a43360d57f9fb528da1cab81773dd60','task-4-original-corpus-profile-design-report.md':'b371c4138cc875d824e556d25f0a9ab1c6dbf2463d95e9f037a8cdec6068b6da'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def new(p,raw):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('xb') as f:f.write(raw)
def out(p,d):new(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
for n,h in expected.items():assert sha(W/n)==h,n
report=(W/'task-4-original-corpus-profile-design-report.md').read_bytes()
assert report[:8408]==(V/'code/original-profile-design-r2/task-4-original-corpus-profile-design-report.md').read_bytes()
assert hashlib.sha256(report[:4914]).hexdigest()=='8fa9aaa7df4c971f086bced2bfcb346b96a5d6b5dc84fb15530625df52e32cd4'
archive=V/'code/original-profile-design-r3';archive.mkdir(exist_ok=False)
for n in expected:new(archive/n,(W/n).read_bytes())
out(archive/'seal.json',expected)
package=W/'task-4-original-corpus-profile-design-review-package.txt'
text='Original Task4 next profile R3 design review. Product C118 unchanged; documentation-only complete candidate package. No executable implementation or runtime grant.\n'
for n in expected:
    p=W/n;text+='\nFILE '+str(p)+' SHA256 '+sha(p)+' bytes '+str(p.stat().st_size)+'\n'
    text+=''.join(difflib.unified_diff([],p.read_text('utf8').splitlines(keepends=True),fromfile='new-design/'+n,tofile=str(p),n=3))
new(package,text.encode('utf8'))
paths=[W/'task-4-original-corpus-profile-design-brief.md',W/'task-4-original-corpus-profile-requirements-draft.md',W/'task-4-original-corpus-profile-boundary-ruling-1.md',W/'task-4-original-corpus-profile-dns-ruling-2.md',package,V/'source10-candidate-manifest.json',V/'harness/manifest.json',V/'inert-actual2-root-readback.json',W/'inert-revision2/inert-root-caller-manifest.json',W/'task-4-inert2-harness-fix1-concern-note.md']+[W/n for n in expected]
inputs=W/'task-4-original-corpus-profile-design-review-inputs.json'
out(inputs,dict(utc=dt.datetime.now(dt.timezone.utc).isoformat(),kind='ORIGINAL_PROFILE_R3_DESIGN_REVIEW_INPUTS',files={str(p):sha(p) for p in paths},report_prefix8408_exact=True,report_prefix4914_exact=True,code_preparation_released=False,runtime_released=False,model_calls=0,T2='NOT_PASSED'))
brief=W/'task-4-original-corpus-profile-design-review-brief.md'
body=f'''# Original Task4 profile R3 independent design review

Read requirements {W}/task-4-original-corpus-profile-design-brief.md and binding ROOT rulings {W}/task-4-original-corpus-profile-boundary-ruling-1.md + task-4-original-corpus-profile-dns-ruling-2.md. Original requirements draft is linked there. Complete candidate spec/plan/report in ONE package {package}; read once, not three duplicate rereads. Companion raw hashes {inputs}. This is FIRST independent design review, not code/runtime acceptance; no implementation exists. Product C118/SDK/harness/caller frozen. Reviewer never implements or dispatches subagents.

Verify design/spec compliance AND implementability/quality against pinned source: real isolated get_jarvis/persona2479 and scanner/config/wrapper path, module-local health facade before every construction, original BrowserChannel/source receipts and real SSRF/DNS guard aliases, visible-only script fitting true schemas/observations, metadata TOTAL16 includingbootstrap1 with correct before-reservation accounting, independent RuntimeInputs/export safety, actual SDK file_write→END→ACK→reopen and honest failed-write evidence. Separate profile submission/exit from original native CLI/listener witness. Check named API couplings in relevant pinned functions; state concrete risk and path:line for each source read. No broad source review. Any missing field/interface or impossible contract is a finding; plan authorship does not excuse it. No requirement may be silently declared verified by a future test.

Global constraints: only current8B digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330; no14B/larger/otherweights/fallback/download/default change. SourceC118/SDK22/source31/P4/P1/harness3d0b/caller0e915/KWS/protected5/H0a31 immutable. Original query774/fourbodies7236/3252/4643/13559 and true persona/scanners remain; no entropy/time reseed or shorter inputs. No actual HTTP/11434/inference in future profile, normal DNS solely under real SSRF on fouroriginalURLs allowed perDNS02, unmeasurednativeDNS/cache/packet counters null. Trusted pinned known-path coverage + process-local audit/private transports; no host OS sandbox/firewall/DNS/ACL change or universal native-escape guarantee. Original16metadata TOTAL inclbootstrap1,8POST/6inspect/1write1ACK and all original byte/token/deadline caps;275/310/315,260/300/315,0retry. One separately consumed worker and independent timed root closed observation required before runtime. PreviousmockENDcauseunknown and all old failures preserved. Original actual8B slot/T2/T3/Owner/prod unreleased.

Read-only checkout/index/refs. No imports, tests, native/DNS/socket/HTTP/model/profile/process/UI/audio/Git mutations. Source/text/hash reads only; no new audit helper agents. Evaluate narrow selected calls and evidence from source without executing it. Report gaps as gaps. Code preparation/review and separate Root control/one runtime allocation remain future stages regardless of design verdict.

Write NEW {V}/original-profile-design-review-1/review.md + verdict.json, identical human copy {W}/task-4-original-corpus-profile-design-review-report.md. Human spec PASS/FAIL,quality APPROVED/NEEDS_FIXES, strengths, Critical/Important/Minor findings exactfile:line + reason/fix, named source checks, cannot-verify items and runtime limits. Machine schema_version1,scopeORIGINAL_PROFILE_R3_DESIGN_REVIEW,candidate,design_sha256,plan_sha256,report_sha256,spec,quality,spec_verdict=spec,quality_verdict=quality,findings[] id OP-D01.../severity/file/line/detail/evidence,reviewed_hashes,code_preparation_released=false,runtime_released=false,model_calls=0,T2=NOT_PASSED. No selfhash or execution approval. Return compact verdict/findings/paths/hashes.
'''
new(brief,body.encode('utf8'))
print(json.dumps(dict(archive=str(archive),package_sha256=sha(package),package_bytes=package.stat().st_size,inputs_sha256=sha(inputs),brief_sha256=sha(brief),code_or_runtime_released=False)))
