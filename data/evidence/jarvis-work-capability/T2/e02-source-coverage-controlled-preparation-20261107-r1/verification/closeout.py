"""Bind independent preparation PASS and record readiness, without actual allocation."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,re
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-coverage/UltimaAgent')
HEAD='e40a55b40c223181040dbb6a09d0c4d2da5026cf'
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
assert verification['tests']==342
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
report_path=R/'docs/reports/jarvis-work-t2-e02-source-coverage-controlled-preparation-20261107.md'
plan_path=R/'docs/plans/jarvis-work-e02-source-coverage-controlled-entry-plan-20261107.md'
runtime=json.loads((N/'verification/runtime-readiness.json').read_bytes())
member_count=len(json.loads((N/'manifest.json').read_bytes())['files'])
text=f"""# E02 e40a55b 受控入口准备完成

本轮接续原单 wo-ultimaagent-20261101-0021/T2 的持续目标，已完成新候选受控入口、绑定、离线检查与独立准备审查。当前实际分配0、结果复核分配0、模型调用0；E02仍0/3，T2/Owner未通过。当前候选{HEAD}冻结且干净，旧候选E01/E03信用不迁移；最终候选的E01—E03原门仍须满足后才能进入T3—T5。

## 本轮完成

复用N13已审查入口，entry、bindings、adapter全部函数/类AST保持一致，只重绑路径、候选和摘要。完整源码/契约清单73项、输入1575项，check_inputs包含入口绑定共1578项。起初把36项顶层源码快照当成完整清单，遗漏37个继承路径；在任何实际运行前已发现、保存草稿与RED，再改为旧68项映射和当前冻结快照的并集。73项全部由N14/current-inputs独立固定，最终回归使用完整清单。

公开固定“本次研究未交付。”是合法用户文案；旧测试“不含任何FINAL文本”改为验证公开content精确匹配，同时不暴露私有final_answer对象，原16KiB、绑定/摘要、无写入及零信用断言保持。新增三例通过adapter.install_trusted_exports和真实SDK MockTransport：第五次同源请求只耗四读即被拒；合法六读后明确未交付；虚假已保存文本不被校验、不能进入可信私有final。逐例核对真实构造的请求实体SHA/大小、HTTP状态、代次、页面可见性、服务首回执和导出文件，而非手工拼造诊断包。

## 验证及独审

本轮342项去重离线PASS：标准库入口34/绑定16/边界11，以及adapter281（五组原始283、重复2）。两次RED各1断言失败/9通过/errors0均保留；后一次RED已使用完整1575输入。原审计守卫及90秒分片保持，测试未触发真实网络/进程/模型动作；不冒称OS抓包。产品N14的746项为已封存基线，只核验字节，不当作本轮新执行。

精确计划独审PASS_PLAN_ONLY；当前准备包PASS_PREPARATION_ONLY。manifest {MANIFEST}，{member_count}成员；独审SHA256 {sha(review_path)}。只代表准备的harness-approval已经绑定独审，read_ready通过，无grant时read_release拒绝；run_once未调用，未创建release/actual/controller-authority/native-preflight。

## 保护与后续

只读核对点{runtime['recorded_at']}：七保护身份、Ollama0.32.15、当前qwen3-8b-uncensored摘要及隔离端口18799空闲相符，仅代表该核对点。N14/N13/N12/N11、上一真实FAIL_CONFIRMED与九个无关文件保全。上一实际91406fa9-5952-4e3a-99af-a94c8857c8d3没有research.md/write/ACK，历史失败不覆盖，不重试。

原题四来源、当前8B、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒和原上下文/字节/输出预算保持。产品来源覆盖联动及明确未交付行为来自冻结候选；验收器不替模型选页/写报告。真实8B语义、原生grammar和旧写入相位HTTP500尚未得到新实际证明。

下一步仅待明确分配一次原题四来源的当前8B受控研究及一次只读独立结果复核；具体命令、预算与写域见本根execution-proposal.md。准备完成不产生该分配，旧授权不复制，失败不自动重跑。无UI/音频或生产服务操作，无需暂停键鼠。项目计划/报告/提案与UltimaDocs本地commit/tag/readback完成后再申请该单例；此前远端push被自动审批以blocked by policy拒绝，本轮不重试。

证据根：{N.as_posix()}
"""
for p in (report_path,N/'completion-report.md'):
    assert not p.exists();p.write_text(text,encoding='utf8',newline='\n')
pairs=[(plan_path,M/'plans'/plan_path.name),(report_path,M/'reports'/report_path.name),
       (N/'execution-proposal.md',M/'execution-proposals/e02-source-coverage-controlled-20261107.md')]
for source,target in pairs:
    target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()
    target.write_bytes(source.read_bytes());assert source.read_bytes()==target.read_bytes()
paths=[R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),
    R/'.superpowers/sdd/jarvis-work-e02-source-coverage-controlled-entry-plan-20261107/progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])]);last_actual=state['last_actual_result']
summary='E02受控入口就绪：e40a55b冻结，342项离线检查及独立准备PASS；当前8B/原预算保持，待明确单例分配；实际与模型0，E02仍0/3。'
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE25_E02_COVERAGE_CONTROLLED_READY_AWAITING_ALLOCATION',
    workflow_status='blocked',stage_queue_state='BLOCKED',active_evidence=str(N),active_preparation_root=str(N),active_report=str(report_path),
    active_plan=str(plan_path),active_product_candidate=HEAD,active_product_root=str(C),active_review_agent=None,
    preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',preparation_test_count=342,
    preparation_test_scope='61 entry/binding/boundary + 281 deduplicated adapter; N14 product746 frozen baseline not rerun',
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    active_preparation=dict(root=str(N),candidate=HEAD,status='READY_AWAITING_EXPLICIT_ONE_CASE_ALLOCATION',tests=342,
        manifest_sha256=MANIFEST,review_sha256=sha(review_path),harness_approval_sha256=sha(N/'harness-approval.json'),actual_authority=False),
    next_action_scope=dict(authorized=True,source=str(N/'inputs/direct-user-decision.json'),scope='Controlled entry and input preparation',
        status='COMPLETED',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    e02_source_coverage_controlled_preparation=dict(candidate=HEAD,completed=True,review='PASS_PREPARATION_ONLY',tests=342,
        actual_cases=0,model_calls=0,protected_at_readonly_points=True,native_parser_cause_proven=False,remote_synced=False))
state['next_proposal']=dict(path=str(N/'execution-proposal.md'),status='PENDING_EXPLICIT_ONE_CASE_ALLOCATION',actual_case_allocation=0,result_review_allocation=0)
assert state['last_actual_result']==last_actual
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-07 E02 source coverage controlled preparation complete\n\n'+summary+'\n报告：'+str(report_path)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
queue,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=queue
ledger=before[str(paths[4])].decode('utf8')
ledger=re.sub(r'(?m)^- Task 1:.*$', '- Task 1: COMPLETE; independent plan PASS, C13 frozen, complete source-only binding and current public/private export contract verified.',ledger)
ledger=re.sub(r'(?m)^- Task 2:.*$', '- Task 2: COMPLETE; current offline342 and independent preparation PASS; local publication tracked separately.',ledger)
texts[str(paths[4])]=ledger+f'\n- Task 1 COMPLETE; Task 2 offline342 and independent preparation PASS. Manifest {MANIFEST}.\n- read_ready PASS; missing grant rejected by read_release; run_once not called. Actual/model0, E02 0/3.\n- Local publication tracked separately in verification/publication-readback.json; remote push not attempted.\n'
snap=N/'verification/closeout-before';snap.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(snap/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/closeout-registration.json',dict(summary=summary,candidate=HEAD,manifest_sha256=MANIFEST,review_sha256=sha(review_path),
    before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},
    mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],last_actual_preserved=True,actual_cases=0,model_calls=0,remote_synced=False))
print(json.dumps(dict(summary=summary,report=str(report_path),mirror_files=len(pairs)),ensure_ascii=False))
