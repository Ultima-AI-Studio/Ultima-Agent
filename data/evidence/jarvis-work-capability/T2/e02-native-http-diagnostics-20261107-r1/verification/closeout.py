"""Record offline completion only after the exact candidate's independent PASS."""
from pathlib import Path
import datetime as dt,hashlib,json,re,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent')
HEAD='ee1bef61f04169c64978538dbc4ba799ef7be6c0'
MANIFEST='26977820632f6dbac4bafa286533c48eb883907129ae6a2bb04e5beb7d2c3298'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
review_path=N/'review/independent-preparation-review.json'
review=json.loads(review_path.read_bytes())
assert review['verdict']=='PASS_PREPARATION_ONLY' and review['candidate']==HEAD and review['manifest_sha256']==MANIFEST
assert sha(N/'manifest.json')==MANIFEST
for name,digest in json.loads((N/'manifest.json').read_bytes())['files'].items():assert sha(N/name)==digest,name
for name,digest in json.loads((N/'inputs/current-inputs.json').read_bytes())['files'].items():assert sha(Path(name))==digest,name
assert not any((N/name).exists() for name in ('actual','release','controller-authority'))
assert not subprocess.check_output(['git','-C',str(C),'status','--porcelain'],creationflags=subprocess.CREATE_NO_WINDOW).strip()
report_path=R/'docs/reports/jarvis-work-t2-e02-native-http-diagnostics-preparation-20261107.md'
research_path=R/'docs/research/jarvis-work-e02-native-response-compatibility-20261107.md'
plan_path=R/'docs/plans/jarvis-work-e02-native-http-diagnostics-plan-20261107.md'
text=f"""# E02 原生响应兼容性与 HTTP 失败诊断离线收口

本轮按用户“保持当前8B和原预算，先核对原生响应兼容性、补齐受限HTTP失败回执，再依据确证问题做最小修改”执行。离线补修及必要独审完成；E02仍0/3，T2/Owner未通过，没有新实际用例或模型调用。

## 完成的修改

当前候选 {HEAD}，父版本2b42b3e19516154a26cbc895a3d9e69fabb07ab2；新隔离分支codex/jarvis-e02-http-diagnostics；代码tag ultimaagent-e02-native-http-diagnostics-candidate-20261107。仅一个产品文件src/brain/work_research_diagnostics.py及两份测试文件变动。

私有失败诊断升级v3，新增last_http：可信代次、固定路由、HTTP整数状态、请求SHA/大小、发包预留标记和有界计数。通过timeline唯一事件及wire代次/实体摘要绑定；实际状态与secured响应验证分开。支持发包前拒绝、无响应、500、200后坏JSON/schema/扫描失败、metadata失败等情况。正文、任意URL和异常文本不导出；原错误、扫描、冻结一次、16KiB上限和零验收信用保持。传输/请求构造、schema/重放、模型/预算、写入和事实门均未改。

## 兼容性核对与根因界限

当前GGUF模板支持enable_thinking=false，产品已传think=false、stream=false、temperature=0。固定版Ollama源码存在相应参数与JSON schema映射；没有确证需要重复设置参数、改采样格式或提高token上限。官方来源与本地元数据摘要见同名兼容性研究记录及证据根research/upstream/provenance.json。

前例500与原生peg-native解析告警有强时间/内容关联，仍非请求绑定回执。具体模板/schema/parser原因未确证，原生解析问题没有在本轮被宣告修好；没有从截断内容拼文稿。本次补齐的是源码已证明的诊断导出遗漏，尚无新真实HTTP回执。

## 验证及独审

38项新增测试在旧代码RED失败，未覆盖旧证据；当前字节700项产品回归（含43项HTTP诊断）与6项原受限导出helper兼容测试，共706项去重PASS。原两项HTTP/junction排除保持；未重跑整套现场harness或实际原生推理。受限Python审计记录均清洁，但不冒称OS抓包。

计划独审PASS；本候选准备独审PASS_PREPARATION_ONLY。准备manifest SHA256 {MANIFEST}，808成员；当前绑定1568项。独审回执SHA256 {sha(review_path)}。提交后源码逐字节与测试快照匹配，候选工作区干净。报告不将离线测试/准备审查当成E02交付通过。

## 保护及后继状态

2026-11-07 16:29:29与16:44:12（北京时间）两次只读核对中，七保护身份、Ollama0.32.15与当前qwen3-8b-uncensored摘要6d7230a9…c7f9330相符；不主张连续存活。前例2501准备成员、49结果成员、4补充成员、1563原输入和9无关文件核验保持。

上一实际例be79869f-10e5-4c0d-96a9-144cd5967c12仍为FAIL_CONFIRMED，119.564秒，无research.md、write/ACK，清理PASS、retry0；该实际结果没有被覆盖。历史E01/E03不迁移到本候选。

当前CLI/search/GET/inspect/write/ACK/nativePOST以及service260/client300/root275/cleanup310/seal315秒预算全部保持；只用当前8B，永不14B。本轮actual_cases=0/model_calls=0/service_operations=0；无UI/音频。没有创建新实际harness、authority或release，当前单例分配0。后续先为新候选准备并核验接线/绑定与原预算，只有取得明确单例分配后才实跑；首个真实回执再决定原生兼容修复，失败不重试。事实、引用、覆盖、写入读回、ACK和清理仍须分别验收。

项目文档及UltimaDocs镜像按本地提交/tag收口；远端push此前被自动审批以blocked by policy拒绝，本轮未重试，remote_synced=false。

证据根：{N.as_posix()}
"""
for p in (report_path,N/'completion-report.md'):
    assert not p.exists();p.write_text(text,encoding='utf8',newline='\n')
assert not research_path.exists();research_path.write_bytes((N/'research/compatibility-findings.md').read_bytes())
pairs=[(plan_path,M/'plans'/plan_path.name),(report_path,M/'reports'/report_path.name),(research_path,M/'research'/research_path.name)]
for source,target in pairs:
    target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
    target.write_bytes(source.read_bytes());assert source.read_bytes()==target.read_bytes()
paths=[R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),R/'.superpowers/sdd/jarvis-work-e02-native-http-diagnostics-plan-20261107/progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])]);last_actual=state['last_actual_result']
summary='E02原生HTTP诊断离线补修完成：候选ee1bef6，706项当前字节检查及独立准备PASS；8B/原预算保持，实际例与模型调用0；原生解析根因未确证，上一FAIL保留，E02仍0/3。'
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE22_E02_NATIVE_HTTP_OFFLINE_COMPLETE',workflow_status='blocked',stage_queue_state='BLOCKED',active_evidence=str(N),active_preparation_root=str(N),active_report=str(report_path),active_plan=str(plan_path),active_product_candidate=HEAD,active_product_root=str(C),active_review_agent=None,preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',preparation_test_count=706,preparation_test_scope='700 product + 6 restricted exporter compatibility; offline only',e02_execution_released=False,live_gate_released=False,next_stage_released=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,active_preparation=dict(root=str(N),candidate=HEAD,status='PASS_PREPARATION_ONLY',tests=706,manifest_sha256=MANIFEST,review_sha256=sha(review_path),actual_authority=False),active_candidate_acceptance=dict(E01='NOT_REVALIDATED_ON_THIS_CANDIDATE',E03='NOT_REVALIDATED_ON_THIS_CANDIDATE',E02_controlled_passed=0,required=3,old_credit_transferred=False),next_action_scope=dict(authorized=True,source=str(N/'inputs/direct-user-decision.json'),scope='Offline compatibility and bounded HTTP diagnostics',status='COMPLETED',actual_case_allocation=0,model_calls=0,service_operations=0),e02_native_http_offline=dict(candidate=HEAD,completed=True,review='PASS_PREPARATION_ONLY',tests=706,actual_cases=0,model_calls=0,service_operations=0,protected_at_readonly_points=True,native_parser_cause_proven=False,old_credit_transferred=False,remote_synced=False))
assert state['last_actual_result']==last_actual
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-07 E02 native HTTP offline completion\n\n'+summary+'\n报告：'+str(report_path)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
queue,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=queue
texts[str(paths[4])]=f"""# E02 native HTTP diagnostics progress

- Scope: user-authorized offline investigation and evidence-proven diagnostic repair; actual allocation 0; model calls 0.
- Task 1 COMPLETE: fixed-version native compatibility + current GGUF metadata readback; plan review PASS; one product file and two test files; RED38; current product700 + export6 =706 PASS.
- Task 2 REVIEW PASS: candidate {HEAD}; manifest {MANIFEST}; prior failures and unrelated files unchanged. Local publication is tracked separately by verification/publication-readback.json; no remote push claimed.
- Runtime points: seven protected identities and current8B matched at 2026-11-07T08:29:29Z and 08:44:12Z.
- Last actual: N11 FAIL_CONFIRMED, no research.md, retry0, cleanupPASS. Current E02 0/3; T2/Owner NOT_PASSED; native parser cause unresolved.
"""
snap=N/'verification/closeout-before';snap.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(snap/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/closeout-registration.json',dict(summary=summary,candidate=HEAD,manifest_sha256=MANIFEST,review_sha256=sha(review_path),before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],last_actual_preserved=True,actual_cases=0,model_calls=0,remote_synced=False))
print(json.dumps(dict(summary=summary,report=str(report_path),mirror_files=len(pairs)),ensure_ascii=False))
