from pathlib import Path
import datetime, hashlib, json

C=Path(r'C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
H=Path(r'H:/UltimaAI/UltimaAgent')
M=Path(r'H:/UltimaAI/ultima-docs-repo')
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101'
T=H/'data/evidence/jarvis-work-capability/T2'
V=T/'navigation-source10-validation-20261102'
SOURCE='118ba152b007c30d358c8bc44c51aabe8ae820f0'
BASE='84b85517f7aafe985d0c33a354ba3b5f9736ecb64f6e52d9da6eb9520a7bdcc3'
HEAD='935b3e3b1f42790c6bd3d7ebd88164f4cc47a9de9a1703557f5da0c59806bcb5'
REPORT='b8fb39ee75d9753a4189c50126cb514647c1a7768e1cb6390ef506fbf4bfadbc'
NAMES=['adapter.py','headless_proof.py','manifest.json','README.md','run_checks.py','test_adapter.py']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def read(p):return json.loads(p.read_bytes())
def new(p,data):
 with p.open('xb') as f:f.write(data)
def newjson(p,d):new(p,(json.dumps(d,ensure_ascii=False,indent=2)+'\n').encode())
assert sha(V/'harness/manifest.json')==HEAD
assert sha(W/'task-4-navigation-adapter-report.md')==REPORT
assert sha(V/'code/root-harness-fix4-before-review.json')=='f2169bd92abaa05cb18ca87e79baf38e2526410d2f6c419fc3faea0f08fc7b89'
archive=V/'harness-preparation-author-r6';archive.mkdir()
for n in NAMES:new(archive/n,(V/'harness'/n).read_bytes())
new(archive/'report.md',(W/'task-4-navigation-adapter-report.md').read_bytes())
brief=W/'task-4-navigation-harness-fix4-rereview-brief.md'
text=f'''# Task4 formal fix4 scoped re-review — SAME original reviewer

Resume the existing Task4 fix loop, not a fresh broad review. C={C}; H={H}; V={V}; W={W}. Python is H/tools/venv-openjarvis/Scripts/python.exe -B -X utf8. Product source stays {SOURCE}.

Read W/task-4-navigation-harness-fix4-brief.md (requirements), W/task-4-harness-fix4-findings-verbatim.md (complete verbatim review4, human0ac789eb and verdictc8bddf17), and SAME W/task-4-navigation-adapter-report.md full appendix after byte94969. Current report108075bytes SHA{REPORT}, preserving entire previous94969/51cd prefix. Author DONE is unverified disposition.

FixBASE manifest{BASE}, exact6 in V/harness-preparation-author-r5; FixHEAD manifest{HEAD}, currentV/harness and archiveauthor-r6. Read ONCE W/task-4-navigation-harness-fix4-review-package.txt (27139bytes SHA349b7baf885f326be87e2c836f4599ee670f5cd2f45f12c3bcdcb6d2a3efe518), exact84b8→935b six-file contextual diff. No Git commands, fresh broad crawl or changed-file reread unless a named cutoff/coupling requires it.

Verdict the SINGLE Important F1-N01 ADDRESSED/NOT_ADDRESSED with actual line evidence. Scope includes producer-declared types before generic scanner numeric/bool/null/container exemptions, genuine SDK/native metadata/transcript representations touched by this fix, and new breakage IN THE FIX DIFF. Hold20 closed H01-H15/F1-N02/F1-N03/F2-N01/F2-N02/F2-N03 except concrete fix-caused regression. Entirely untouched observations separate nonblocking. Explicit SPEC and QUALITY required. No broad repeat.

Original reviewer scalar/object counterexamples must remain original-replay-positive and publication-negative; text result must stay text. Do not treat stringification or field-name heuristics as type validation. Check legitimate SDK/file-write/latency/native family/details and peer-byte null contracts against actual named producer code if needed. Ordinary prose stays prose, strict duplicate decoding only at actual serialized boundaries, legitimate free Observation ACK and genuine raw export/readback stay valid. Existing original timestamp, decoded-envelope, bounded raw caps, native ownership, first-cause/effect/clearance/deadline guards remain binding. Any new rejection of producer-valid values or acceptance of malformed in-scope data introduced by these additions is a fix regression.

Root FULL appendix read + V/code/root-harness-fix4-before-review.json SHA f2169bd92abaa05cb18ca87e79baf38e2526410d2f6c419fc3faea0f08fc7b89 verifies6new closed stages, final173/no-k/all162previousIDs, current6/copies/beforeafter,64pins/C31/Git30+1/SDK22/7deps/modelpolicy and reportprefix. Finalstage code/harness-preparation-20261102T221401644962Z receiptec46aab75080e727654dabc0010aee7f0f1762ec8a72a6571ace6cb30a489523/JUnitc0ff7d03e62bb7e2f1601f45d9c6ae434d178ff55f0cf33c992dfac3a43abc67, stdout173passed35.92sec, empty stderr. Read raw covering command/output/JUnit/snapshots, do not rerun suite. Initial latency setup serialization error and corrected genuine RED are explicitly retained, not falsely counted as behavioral reproduction.

All original global constraints: exclusively current8B digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330, no otherweights/default/fallback/download; same mainbrain/SDK/registry; originalquery/fourbodies/caps and pinnedC/SDK/P4/P1/helper unchanged; original native retained/reopened ownership/targets/protected exclusions; no new controller; privateIO only. Same monotonic_ns preadmission275/310/315, trusted earlier origin wins, inclusive fully observedclose and missing/late/unknown permanentfail; no physicalpreemption guarantee,260/300/315/zero retry unchanged. Safe bounded4MiB raw members, no unsafe or partial export.

Read-only harness/source/test/SDK/index/Git/model/default/prod. No subagents. No actualOwned/helper/server/CLI/inert/profile/native11434/external/model/UI/audio/kill/recovery/rootcaller/authority/baseline/approval. Pure focused preparation check only for a specific unanswered risk, using sealed synthetic fixture and denied side effects; no package-wide repeat. Root alone owns publication/admission/witness/release. Output ONLY NEW V/harness-review-5/review.md + verdict.json and identical W/task-4-navigation-harness-fix4-rereview-report.md. JSONschema1 includes scope,candidate,base_manifest_sha256,harness_manifest_sha256,spec_verdict,quality_verdict,finding_verdicts,new_findings,out_of_scope,checks,execution_released=false,T2=NOT_PASSED. Return short verdict/reportpaths/hashes.
'''
new(brief,text.encode())
paths=[brief,W/'task-4-navigation-harness-fix4-review-package.txt',W/'task-4-navigation-adapter-report.md',W/'task-4-navigation-harness-fix4-brief.md',W/'task-4-harness-fix4-findings-verbatim.md',V/'harness-review-4/verdict.json',V/'harness-review-4/review.md',V/'harness-preparation-author-r5/report.md',V/'code/root-harness-fix4-before-review.json',V/'harness/manifest.json',V/'code/harness-preparation-20261102T221401644962Z/receipt.json']
inputs=W/'task-4-navigation-harness-fix4-review-inputs.json'
newjson(inputs,dict(utc=datetime.datetime.now(datetime.timezone.utc).isoformat(),candidate=SOURCE,scope='TASK4_FIX4_SCOPED_REREVIEW',base_manifest_sha256=BASE,harness_manifest_sha256=HEAD,files={str(p):sha(p) for p in paths},six_files={str(V/'harness'/n):sha(V/'harness'/n) for n in NAMES},review_output=str(V/'harness-review-5'),actual_inert_profile_model_released=False))
statepath=T/'current-run.json';state=read(statepath)
state.update(phase='E02_NAVIGATION_SOURCE10_HARNESS_FIX4_REVIEW',active_implementation_agent=None,active_review_agent='/root/review_navigation_harness_source10',source10_harness_author_status='DONE_FIX4_PENDING_SCOPED_REVIEW',source10_harness_current_unit_tests=173,source10_harness_manifest_sha256=HEAD,source10_harness_report_sha256=REPORT,source10_harness_review_ready=True,source10_harness_review_status='FIX4_SCOPED_REVIEW_PENDING',source10_harness_review_dir=str(V/'harness-review-5'),source10_harness_root_readback_sha256=sha(V/'code/root-harness-fix4-before-review.json'),source10_harness_fix4_review_brief_sha256=sha(brief))
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
q=Path(r'H:/UltimaAI/_shared/queue/global-queue-index.md');old=q.read_bytes();lines=old.splitlines(keepends=True)
hits=[i for i,l in enumerate(lines) if b'| UltimaAgent | wo-ultimaagent-20261101-0021 |' in l];assert len(hits)==1;i=hits[0]
new(W/'global-queue-before-harness-fix4-review.md',old)
end=b'\r\n' if lines[i].endswith(b'\r\n') else b'\n'
newrow='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | 仅当前8B；源10产品代码PASS，Task4第4轮173测试已读回，20项已关/唯一F1-N01独审中；惰性/模型/实际/T3未放行 |'.encode()+end
before_row=lines[i];lines[i]=newrow;q.write_bytes(b''.join(lines));assert q.read_bytes().replace(newrow,b'',1)==old.replace(before_row,b'',1)
newjson(V/'global-own-row-harness-fix4-review.json',dict(before_sha256=hashlib.sha256(old).hexdigest(),after_sha256=sha(q),own_row_only=True,old_row=before_row.decode().rstrip(),new_row=newrow.decode().rstrip()))
report=H/'docs/reports/jarvis-work-t2-e02-reassessment-20261102.md';text=report.read_text(encoding='utf-8');parts=text.splitlines(keepends=True);assert parts[2].startswith('当前阶段：')
parts[2]='当前阶段：**source10产品代码118ba152独审通过；Task4第4轮173项完整测试已独立读回，20项已关、唯一F1-N01待原审查者复审；惰性/模型/实际验收未放行，E02/T2未通过。** 原工单 `wo-ultimaagent-20261101-0021` 继续执行。\n'
text=''.join(parts)+'\nTask4 fix4：新工程代理按实际SDK/产品字段声明补充导出前类型校验。完整173项通过，原162项全部保留；6份源快照/64固定输入及94969字节旧报告前缀均已独立读回。整数/对象反例通过原重放后被拒于写盘前；初始延迟夹具序列化错误及纠正后的真实RED均保留。作者报告b8fb39ee、manifest935b3e3b，root读回f2169bd9。仍由原审查者只复审F1-N01和本次修复新增风险，不据测试宣布运行或研究验收通过。\n'
report.write_text(text,encoding='utf-8',newline='\n')
(M/'docs/shared/research/ultimaagent-work-capability/reports'/report.name).write_bytes(report.read_bytes())
with (H/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md').open('a',encoding='utf-8',newline='\n') as f:f.write('\nTask4 fix4 preparation complete,173 tests/all162priorIDs/raw64pins verified. SAME reviewer scoped F1-N01 + fix-caused risks;20 closed held. No actual/inert/profile/model/T3 release; E02/T2 NOT_PASSED.\n')
note='\nTask4 FIX4 authorDONE173/all162IDs retained; final221401644962Z receipt ec46aab7/JUnit c0ff7d03/manifest935b3e3b/reportb8fb39ee108075B. RootFULLappendread +f2169bd9 verifies6newstages/current6/64pins/C31SDK22/Git30+1/no-k/prefix94969 exact. Scoped84b8→935b diff27139B349b7baf; archiveauthor-r6 current6/report. SAMEreviewer next via fix4rereviewbrief + inputs, ONLYF1-N01/newdiffregressions; hold20closed. No actual/inert/profile/model/rootcaller/authority/approval/baseline. E02T2NOTPASSED/goalACTIVE.\n'
for n in ['progress.md','resume-current.md']:
 with (W/n).open('a',encoding='utf-8',newline='\n') as f:f.write(note)
print(json.dumps(dict(brief=str(brief),brief_sha256=sha(brief),inputs=str(inputs),inputs_sha256=sha(inputs),archive=str(archive))))
