"""Bind independent preparation PASS and record readiness, without actual allocation."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,re
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent')
HEAD='ee1bef61f04169c64978538dbc4ba799ef7be6c0'
MANIFEST='01d1c12f63e19d7ea72020a28fad3f2a4ba1496aaa31ccbd6112a245919ec7cb'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
review_path=N/'review/independent-preparation-review.json';review=json.loads(review_path.read_bytes())
assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PREPARATION_ONLY'
assert review['candidate']==HEAD and review['manifest_sha256']==MANIFEST and review['actual_run_authorized'] is False
assert sha(N/'manifest.json')==MANIFEST
verification=module('current_closeout_verification',N/'verification/verify_preparation.py').verify()
assert verification['tests']==339
approval=dict(reviewer='root-independent',overall='PASS',manifest_sha256=sha(N/'harness/manifest.json'),review_sha256=sha(review_path),preparation_manifest_sha256=MANIFEST)
save(N/'harness-approval.json',approval)
e=module('current_prepared_entry',N/'code/entry.py');package=e.read_ready(N)
try:e.read_release(N,package,dt.datetime.now(dt.timezone.utc))
except FileNotFoundError:missing_grant_rejected=True
else:raise AssertionError('No actual grant may exist at preparation closeout')
save(N/'verification/ready-readback.json',dict(verdict='PASS_READY_WITHOUT_ACTUAL_ALLOCATION',candidate=HEAD,package=package,
    missing_grant_rejected=missing_grant_rejected,read_release_only=True,run_once_called=False,
    verification=verification,actual_cases=0,model_calls=0,actual_case_allocation=0,result_review_allocation=0,
    recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
report_path=R/'docs/reports/jarvis-work-t2-e02-native-http-controlled-preparation-20261107.md'
plan_path=R/'docs/plans/jarvis-work-e02-native-http-controlled-entry-plan-20261107.md'
text=f"""# E02 ee1bef6 受控入口准备完成

本轮按用户“为新候选准备受控入口和绑定；明确分配单例后，再取得真实请求回执，据此决定原生兼容修复”执行。准备工作、离线检查及独立准备审查已完成。当前实际分配0、实际运行0、模型调用0；真实请求回执尚未取得，E02仍0/3，T2/Owner未通过。

产品候选 {HEAD} 保持冻结且工作树干净。本轮复用N11受控入口，重绑68个当前源文件、1567个输入文件，完整check_inputs核对1570项。原题/四来源、当前qwen3-8b-uncensored摘要6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330、七保护身份、原时钟和清理保持。

入口增加已证实必要的范围检查：直接用户消息必须明确分配严格整数actual1/review1/retry0。原实现在准备消息被包装成grant时未验证其范围，RED产生25个预期失败断言；补修后准备消息在消费前被拒绝、不触及run_released，明确授权的合成正例保留。只修改entry的这一条件，adapter/bindings函数与类AST保持，产品源码未改。

当前新执行339项去重离线检查PASS：入口34、绑定16、边界11、adapter278（五组原始280、重复2）。完整SDK MockTransport与原导出入口覆盖HTTP500、200坏JSON和扫描拒绝：请求摘要、代次、路由和v3私有回执相符；500不读取正文，200失败不误标validated；原首个错误、16KiB上限、write/ACK及零验收信用保持。N12的706项只是已封存产品基线，未计为本轮新执行。模拟回执不算真实原生请求证明。

计划审查PASS_PLAN_ONLY；整包独审PASS_PREPARATION_ONLY。manifest SHA256 {MANIFEST}（149成员）；独审SHA256 {sha(review_path)}。harness-approval仅绑定准备审查，read_ready已读回；read_release在无grant时拒绝。本轮无release、actual或controller-authority目录，无UI/音频/生产服务操作。

北京时间2026-11-07 17:06:53只读核对七个保护身份一致、Ollama0.32.15、当前8B摘要一致、18799空闲；只代表该核对点。N12/N11封存、前例失败及9无关文件逐字节保全，旧PASS信用不迁移。前例be79869f…仍FAIL_CONFIRMED，无research.md，清理PASS、retry0。

待明确分配的单例见同证据根execution-proposal.md：当前8B原题四来源一次受控研究，加一次只读独立结果复核，失败不重试。CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒；context16384、messages+schema32768/entity49152字节、输出上限2048保持。无需暂停键鼠。只在真实答复后生成与本manifest/独审绑定、TTL<=120秒的一次grant。

后续先封存首个真实请求和结果，独立复核状态、证据和交付；再依据确证问题决定原生兼容修复。未确证原因前不改模型/请求协议/预算，也不把准备通过当作E02通过。

项目与UltimaDocs以本地提交/tag及publication-readback.json读回收口。远端push此前被自动审批以blocked by policy拒绝，本轮不重试；remote_synced=false。

证据根：{N.as_posix()}
"""
for p in (report_path,N/'completion-report.md'):
    assert not p.exists();p.write_text(text,encoding='utf8',newline='\n')
pairs=[(plan_path,M/'plans'/plan_path.name),(report_path,M/'reports'/report_path.name),
       (N/'execution-proposal.md',M/'execution-proposals/e02-native-http-controlled-20261107.md')]
for source,target in pairs:
    target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
    target.write_bytes(source.read_bytes());assert source.read_bytes()==target.read_bytes()
paths=[R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),
    R/'.superpowers/sdd/jarvis-work-e02-native-http-controlled-entry-plan-20261107/progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])]);last_actual=state['last_actual_result']
summary='E02受控入口就绪：ee1bef6冻结，339项离线检查及独立准备PASS；当前8B/原预算保持，待明确单例分配；实际与模型0，E02仍0/3。'
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE23_E02_HTTP_CONTROLLED_READY_AWAITING_ALLOCATION',
    workflow_status='blocked',stage_queue_state='BLOCKED',active_evidence=str(N),active_preparation_root=str(N),active_report=str(report_path),
    active_plan=str(plan_path),active_product_candidate=HEAD,active_product_root=str(C),active_review_agent=None,
    preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',preparation_test_count=339,
    preparation_test_scope='61 entry/binding/boundary + 278 deduplicated adapter; N12 product706 frozen baseline not rerun',
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    active_preparation=dict(root=str(N),candidate=HEAD,status='READY_AWAITING_EXPLICIT_ONE_CASE_ALLOCATION',tests=339,
        manifest_sha256=MANIFEST,review_sha256=sha(review_path),harness_approval_sha256=sha(N/'harness-approval.json'),actual_authority=False),
    next_action_scope=dict(authorized=True,source=str(N/'inputs/direct-user-decision.json'),scope='Controlled entry and input preparation',
        status='COMPLETED',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    e02_native_http_controlled_preparation=dict(candidate=HEAD,completed=True,review='PASS_PREPARATION_ONLY',tests=339,
        actual_cases=0,model_calls=0,protected_at_readonly_points=True,native_parser_cause_proven=False,remote_synced=False))
assert state['last_actual_result']==last_actual
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-07 E02 HTTP controlled preparation complete\n\n'+summary+'\n报告：'+str(report_path)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
queue,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=queue
ledger=before[str(paths[4])].decode('utf8')
ledger=re.sub(r'(?m)^- Task 1:.*$', '- Task 1: COMPLETE; independent plan PASS, C12 frozen, source-only binding and direct decision scope guard verified.',ledger)
ledger=re.sub(r'(?m)^- Task 2:.*$', '- Task 2: COMPLETE; current offline339 and independent preparation PASS; local publication tracked separately.',ledger)
texts[str(paths[4])]=ledger+f'\n- Task 1 COMPLETE; Task 2 offline339 and independent preparation PASS. Manifest {MANIFEST}.\n- read_ready PASS; missing grant rejected by read_release; run_once not called. Actual/model0, E02 0/3.\n- Local publication tracked separately in verification/publication-readback.json; remote push not attempted.\n'
snap=N/'verification/closeout-before';snap.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(snap/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/closeout-registration.json',dict(summary=summary,candidate=HEAD,manifest_sha256=MANIFEST,review_sha256=sha(review_path),
    before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},
    mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],last_actual_preserved=True,actual_cases=0,model_calls=0,remote_synced=False))
print(json.dumps(dict(summary=summary,report=str(report_path),mirror_files=len(pairs)),ensure_ascii=False))
