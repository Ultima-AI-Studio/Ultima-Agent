"""Bind independent preparation PASS and record readiness, without actual allocation."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,re
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent')
HEAD='6d758d9c3961f156a062e349ec4a949e2ee7a9a9'
MANIFEST=None
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
MANIFEST=sha(N/'manifest.json')
review_path=N/'review/independent-preparation-review.json';review=json.loads(review_path.read_bytes())
assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PREPARATION_ONLY'
assert review['candidate']==HEAD and review['manifest_sha256']==MANIFEST and review['actual_run_authorized'] is False
assert sha(N/'manifest.json')==MANIFEST
verification=module('current_closeout_verification',N/'verification/verify_preparation.py').verify()
assert verification['tests']==344
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
report_path=R/'docs/reports/jarvis-work-t2-e02-json-string-controlled-preparation-20261107.md'
plan_path=R/'docs/plans/jarvis-work-e02-json-string-controlled-entry-plan-20261107.md'
runtime=json.loads((N/'verification/runtime-readiness.json').read_bytes())
member_count=len(json.loads((N/'manifest.json').read_bytes())['files'])
text=f"""# E02 6d758d9 受控入口准备完成

原工单 wo-ultimaagent-20261101-0021 / T2。冻结产品候选 {HEAD} 已接入现有受控入口，本轮实际用例0、结果复核分配0、模型调用0。E02仍0/3，T2/Owner未通过；旧候选E01/E03信用不迁移。

复用 N15 的 entry、bindings、adapter，全部函数与类 AST 保持一致，仅重绑候选、路径和摘要。完整源码74项、输入1579项，check_inputs含三项入口绑定共1582项。清单由N15继承73项与N16顶层37项映射并集产生，逐项匹配N16 current-inputs及当前磁盘。产品HEAD/tag与工作区clean已核对。

新增两项安装原导出观察器的SDK MockTransport联合验证：合法中文、引号及反斜杠代码事实完成工具写入、文件摘要读回、ACK和导出包严格重放；raw sampler允许但解码后违反操作名边界的内容被严格校验拒绝，无research.md或完整runtime/END，公开明确未交付。两项均核对实际构造的HTTP实体摘要与可信回执；没有真实模型或事实验收信用。

本轮344项去重离线PASS：adapter五组原始285项、去重283项，以及入口34/绑定16/边界11共61项。原90秒分片及离线审计守卫保持，源码快照/回执/审计/JUnit均核验。首次新增正例把原始反斜杠与Markdown转义后的文本直接比较，出现1项测试断言失败；产品当时已成功写入。首次五组回执完整保留，修正测试为同时验证原始语义和转义后的文档文本，再对最终harness字节重跑五组；通过的三组标准库源码不变，未重复运行或累计。产品N16的781项（775产品+6参考）仅为冻结历史基线，本轮未重跑或重新累计。新入口未实现新的产品行为，也未重复制造旧RED。

精确计划PASS_PLAN_ONLY，整包PASS_PREPARATION_ONLY。manifest {MANIFEST}，{member_count}成员；独立准备审查SHA256 {sha(review_path)}。harness-approval仅绑定准备审查；read_ready通过，缺少grant时read_release拒绝，run_once未调用。准备根没有release/actual/controller-authority/native-preflight。

只读检查点 {runtime['recorded_at']}：七保护身份、Ollama0.32.15、当前qwen3-8b-uncensored摘要及18799空闲相符，仅代表该时点。N16封存956成员/输入1576项、N15封存准备189/结果56及旧输入1575项、九个无关文件均保持。上一实际5e6ea89c-8e47-43a6-9480-7a11d72cabf5的HTTP500和未交付仍为FAIL_CONFIRMED，不改写或复用额度。

当前8B、原题四来源、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒以及上下文/字节/输出预算均保持。真实8B交付、原生GBNF二进制行为、三来源事实/原题覆盖和连续存活尚未获本候选实际证明。

下一步按 execution-proposal.md 明确分配一例当前8B原题四来源受控研究及一次只读独立结果复核后，才生成短时且一次消费的grant。失败不重试；无UI/音频/生产服务操作。项目/UltimaDocs本地提交、tag及逐文件读回由 verification/publication-readback.json 记录；此前远端push被自动审批以blocked by policy拒绝，本轮不重试。

证据根：{N.as_posix()}
"""
for p in (report_path,N/'completion-report.md'):
    assert not p.exists();p.write_text(text,encoding='utf8',newline='\n')
pairs=[(plan_path,M/'plans'/plan_path.name),(report_path,M/'reports'/report_path.name),
       (N/'execution-proposal.md',M/'execution-proposals/e02-json-string-controlled-20261107.md')]
for source,target in pairs:
    target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
    target.write_bytes(source.read_bytes());assert source.read_bytes()==target.read_bytes()
paths=[R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),
    R/'.superpowers/sdd/jarvis-work-e02-json-string-controlled-entry-plan-20261107/progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])]);last_actual=state['last_actual_result']
summary='E02受控入口就绪：6d758d9冻结，344项离线检查及独立准备PASS；当前8B/原预算保持，待明确单例分配；实际与模型0，E02仍0/3。'
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE27_E02_JSON_STRING_CONTROLLED_READY_AWAITING_ALLOCATION',
    workflow_status='blocked',stage_queue_state='BLOCKED',active_evidence=str(N),active_preparation_root=str(N),active_report=str(report_path),
    active_plan=str(plan_path),active_product_candidate=HEAD,active_product_root=str(C),active_review_agent=None,
    preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',preparation_test_count=344,
    preparation_test_scope='61 entry/binding/boundary + 283 deduplicated adapter; N16 product781 frozen baseline not rerun',
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    active_preparation=dict(root=str(N),candidate=HEAD,status='READY_AWAITING_EXPLICIT_ONE_CASE_ALLOCATION',tests=344,
        manifest_sha256=MANIFEST,review_sha256=sha(review_path),harness_approval_sha256=sha(N/'harness-approval.json'),actual_authority=False),
    next_action_scope=dict(authorized=True,source=str(N/'inputs/direct-user-decision.json'),scope='Controlled entry and input preparation',
        status='COMPLETED',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    e02_json_string_controlled_preparation=dict(candidate=HEAD,completed=True,review='PASS_PREPARATION_ONLY',tests=344,
        actual_cases=0,model_calls=0,protected_at_readonly_points=True,native_parser_cause_proven=False,remote_synced=False))
state['next_proposal']=dict(path=str(N/'execution-proposal.md'),status='PENDING_EXPLICIT_ONE_CASE_ALLOCATION',actual_case_allocation=0,result_review_allocation=0)
state.update(active_candidate=HEAD, preparation_review_receipt=str(review_path), preparation_review_sha256=sha(review_path),
    preparation_manifest_sha256=MANIFEST,
    next_work='Explicitly allocate one case and one result review on the concrete proposal before actual execution')
state['source27_preparation']=dict(status='READY_AWAITING_EXPLICIT_ONE_CASE_ALLOCATION',candidate=HEAD,tests=344,manifest_sha256=MANIFEST,review_sha256=sha(review_path),actual_case_allocation=0,result_review_allocation=0)
assert state['last_actual_result']==last_actual
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-07 E02 JSON string controlled preparation complete\n\n'+summary+'\n报告：'+str(report_path)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
queue,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=queue
ledger=before[str(paths[4])].decode('utf8')
ledger=re.sub(r'(?m)^- Task 1: IN_PROGRESS.*$', '- Task 1: COMPLETE; independent plan PASS, C14 frozen, complete source-only binding and current public/private export contract verified.',ledger)
ledger=re.sub(r'(?m)^- Task 2: PENDING.*$', '- Task 2: COMPLETE; current offline344 and independent preparation PASS; local publication tracked separately.',ledger)
texts[str(paths[4])]=ledger+f'\n- Task 1 COMPLETE; Task 2 offline344 and independent preparation PASS. Manifest {MANIFEST}.\n- read_ready PASS; missing grant rejected by read_release; run_once not called. Actual/model0, E02 0/3.\n- Local publication tracked separately in verification/publication-readback.json; remote push not attempted.\n'
snap=N/'verification/closeout-before';snap.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(snap/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/closeout-registration.json',dict(summary=summary,candidate=HEAD,manifest_sha256=MANIFEST,review_sha256=sha(review_path),
    before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},
    mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],last_actual_preserved=True,actual_cases=0,model_calls=0,remote_synced=False))
print(json.dumps(dict(summary=summary,report=str(report_path),mirror_files=len(pairs)),ensure_ascii=False))
