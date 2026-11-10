"""Publish the independently reviewed first outcome without reopening the spent case."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import re
import subprocess
import sys

N=Path(__file__).resolve().parents[1]; R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
CANDIDATE='d860b2ab4e4d9974e33c96472e4ea15abb807280'
RUN='72d7d71b-39a9-455a-b0b4-8823b3f24c00'
QUESTION='call_92c748ab12e24ba7a135ebd26783263f'
RESULT_MANIFEST='9cc9e1c9c38a5f23b9e5a0d72b52bd2558a720c99abea8b11148abde483523d6'

def sha(p): return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p): return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f: json.dump(v,f,ensure_ascii=False,indent=2)

review_path=N/'review/independent-result-review.json'; review=load(review_path)
assert review['reviewer']=='root-independent' and review['verdict']=='FAIL_CONFIRMED'
assert review['candidate']==CANDIDATE and review['run_id']==RUN and review['acceptance_credit']==0
manifest_path=N/'review/result-inputs/result-manifest.json'
assert sha(manifest_path)==RESULT_MANIFEST==review['result_manifest_sha256']
for name,digest in load(manifest_path)['files'].items(): assert sha(N/name)==digest,name
A=N/'actual/E02-controlled-1'
product=load(A/'product-result.json'); diagnostic=load(A/'trusted-failure-diagnostic.raw')
terminal=load(A/'terminal.json'); execution=load(N/'release/tool-execution-receipt.json')
witness=load(N/'release/root-outcome.json')['outcome']['witness']
rb=load(N/'review/result-inputs/byte-readback.json'); last=diagnostic['last_http']; native=diagnostic['native_response']
assert execution['question_id']==QUESTION and execution['invocations']==1 and execution['retry']==0
assert terminal['run_id']==RUN and terminal['overall']=='FAIL' and terminal['cleanup']['status']=='PASS'
assert product['status']=='failed' and product['content']=='本次研究未交付。' and product['error']=='Invalid native research response'
assert diagnostic['kind']=='research_failure_diagnostic_v4' and diagnostic['branch']=='unvalidated_response'
assert last['status']==200 and last['validated_response'] is False
assert native['reason']=='done_reason' and native['done_reason']=='length' and native['done'] is True
assert native['eval_count']==native['max_tokens']==2048 and native['prompt_eval_count']==8888
assert native['generation']==last['generation']==7 and native['receipt_index']==last['receipt_index']==20
assert native['request_sha256']==last['request_sha256']=='bc2299bb736f1c1b425c4289f454c47da1bb97d2621624f9a10ce4f03e74bb58'
assert native['response_bytes']==last['admitted']==9663 and last['request_bytes']==33395
assert len(diagnostic['pages'])==6 and diagnostic['eligible_source_ids']==['S1','S2','S3']
assert diagnostic['final_answer'] is None and not diagnostic['write_confirmed'] and not diagnostic['ack_confirmed']
assert rb['research_files']==0 and rb['owned_identities_absent'] and rb['isolated_port_free']
report=R/'docs/reports/jarvis-work-t2-e02-native-rejection-controlled-result-20261107.md'
proposal=R/'docs/plans/jarvis-work-e02-writer-output-budget-alignment-proposal-20261107.md'
assert proposal.is_file()
china=dt.timezone(dt.timedelta(hours=8))
started=dt.datetime.fromisoformat(execution['started_utc']).astimezone(china).isoformat()
finished=dt.datetime.fromisoformat(execution['finished_utc']).astimezone(china).isoformat()
text=f'''# E02 原生拒绝诊断候选：唯一实际结果与独立复核

候选 {CANDIDATE} 的唯一当前8B原题四来源研究结束，独立结果 **FAIL_CONFIRMED**。本次没有交付research.md，E02仍0/3，T2/Owner未通过。诊断已确证本例首个拒绝条件为done_reason=length，eval_count达到该请求2048 token上限；诊断成功不计交付通过。

## 结果与确证范围

公开回复“本次研究未交付。”，status=failed，error=Invalid native research response。search1/GET4成功；私有诊断确认六次读取，前五页visible=true，第六页confirmed=true但visible=false。S1/S2/S3有证据资格，读取起行依次26、50、74、98、20、25。上层tool_results的inspect0和私有诊断六读分别记录；三来源资格不证明原题覆盖。write0、ACK0、research.md0，没有成功runtime/END或事实、引用交付。

第7次/chat请求HTTP200，v4诊断记录reason=done_reason、done=true、done_reason=length、eval_count=max_tokens=2048、prompt_eval_count=8888、content_chars=3798。当前checked_native_response在done_reason必须为stop的分支拒绝该响应。请求和响应摘要与同一generation7、receipt20绑定；这确证本例触发的首个拒绝谓词，没有放宽或绕过原校验。

完整响应正文未保存；content_chars和token计数不能证明具体字段、思考、重复、转义或JSON结构消耗了额度，也不能证明后续校验一定通过。不能追认N17旧失败同因。下一步不凭空修补或截取正文，不接受length为成功。

## 时间、回执和保护

run {RUN}；明确用户分配 {QUESTION}。唯一entry1、work CLI1、retry0；北京时间{started}至{finished}，外层{execution['outer_elapsed_seconds']:.6f}秒。应用native POST7/完成7，服务端实际生成启动总数未测量。root witness的eligible=false、observation_error={witness.get('observation_error')}；时限资格仍为{terminal['timing_eligibility']}，不能把耗时小于上限的失败用例升级成计时PASS。

请求{last['request_bytes']}字节，SHA256 {last['request_sha256']}；响应接收{native['response_bytes']}字节，SHA256 {native['response_sha256']}；这些摘要不等于保留了完整正文。失败诊断{(A/'trusted-failure-diagnostic.raw').stat().st_size}字节，SHA256 {sha(A/'trusted-failure-diagnostic.raw')}，kind=v4，complete=false/END=false/acceptance_credit0。预算快照reads6/6、nativePOST7/8、剩{diagnostic['budget']['deadline_remaining_microseconds']/1000000:.6f}秒，原预算未改变。

原cleanup PASS，登记的六个本例进程身份消失、18799关闭、日志关闭；之后只读核对再次确认本例身份不在。七个保护进程在运行边界及之后核对点身份相符，仅代表这些核对点，不宣称连续存活。本轮无UI、音频或生产服务操作，只用原qwen3-8b-uncensored摘要，未安装、下载或更换模型。

## 独立复核及接续

结果manifest {RESULT_MANIFEST}，56成员；独立结果复核SHA256 {sha(review_path)}。无产物，事实、引用和原题覆盖未通过，接受信用0。当前准备346项及6项登记修复检查没有重跑或转为实际信用；旧候选E01/E03信用不迁移，全部旧失败保持。

本次实际1与独立结果复核1已消费，剩余0。后续提案：{proposal.as_posix()}。先在新隔离候选中把实际输出预算传入共享写入阶段提示，保持原题和完整JSON、事实/引用、来源/证据、写入/ACK及原时限要求；离线验证和独审完成后，另行明确分配新单例。此有限提示对齐尚未证明能让当前8B在原预算内交付，本次不自动补修或重跑。

本地项目与UltimaDocs的commit/tag及逐字节读回见verification/result-publication-readback.json。此前Git push被自动审批以blocked by policy拒绝，本轮没有重试。证据根：{N.as_posix()}。
'''
with report.open('x',encoding='utf8',newline='\n') as f: f.write(text)
pairs=[(report,M/'reports'/report.name),(proposal,M/'plans'/proposal.name)]
for source,target in pairs:
    assert not target.exists(); target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f: f.write(source.read_bytes())
    assert sha(source)==sha(target)
paths=[N.parent/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),N/'progress.md']
before={str(p):p.read_bytes() for p in paths}; state=json.loads(before[str(paths[0])])
assert state['current_one_case_allocation']['question_id']==QUESTION
last_actual=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',
    purpose='native_response_rejection_diagnostics_one_case',run_id=RUN,candidate=CANDIDATE,model='qwen3-8b-uncensored',
    model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',question_id=QUESTION,
    result='FAIL',independent_review='FAIL_CONFIRMED',review_path=str(review_path),review_sha256=sha(review_path),
    result_manifest_sha256=RESULT_MANIFEST,terminal_sha256=sha(A/'terminal.json'),product_result_sha256=sha(A/'product-result.json'),
    entry_invocations=1,work_cli_attempts=terminal['work_cli_attempts'],controlled_search_success=1,controlled_GET_success=4,
    confirmed_inspect_pages=rb['failure_diagnostic']['confirmed_pages'],visible_inspect_pages=rb['failure_diagnostic']['visible_pages'],
    top_level_successful_inspect_results=rb['counts']['ultima_work_research_inspect'],write_attempts=0,successful_write_count=0,research_artifacts=0,
    application_native_POST_attempts=rb['application_native_POST_attempts'],completed_native_posts=rb['completed_native_posts'],actual_native_start_count=None,
    outer_elapsed_seconds=execution['outer_elapsed_seconds'],timing_eligibility=terminal['timing_eligibility'],cleanup='PASS',root_witness_eligible=False,
    root_witness_observation_error=witness.get('observation_error'),
    public_content=product['content'],product_error=product['error'],failure_diagnostic_sha256=sha(A/'trusted-failure-diagnostic.raw'),
    failure_diagnostic_bytes=(A/'trusted-failure-diagnostic.raw').stat().st_size,branch=diagnostic['branch'],eligible_source_ids=diagnostic['eligible_source_ids'],
    last_http=last,native_response=native,selected_pages=[dict(source_id=p['source_id'],start=p['requested_start'],range=p['range'],confirmed=p['confirmed'],visible=p['visible']) for p in diagnostic['pages']],
    budget=diagnostic['budget'],write_confirmed=False,ack_confirmed=False,final_answer_preserved=False,
    facts='NOT_ASSESSABLE_NO_ARTIFACT',original_question_coverage='NOT_PASSED_NO_ARTIFACT',non_delivery_reply_observed=True,
    protected_at_recorded_boundaries=True,protected_after_readonly=True,continuous_liveness_measured=False,
    acceptance_credit=0,controlled_passed=0,controlled_required=3,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,retry=0,
    next_case_released=False,E02='NOT_PASSED',T2='NOT_PASSED',Owner='NOT_PASSED',old_credit_transferred=False,remote_synced=False,
    cause='Generation7 HTTP200 rejected on done_reason=length; eval_count=max_tokens=2048',native_rejection_predicate_proven=True,
    native_compatibility_limit='Bounded projection proves this first refusal only; full response body unavailable; prior failure cause not inferred',
    previous_actual_preserved_at=str(N/'verification/result-closeout-before/0-current-run.json'),recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
state['previous_actual_result']=state['last_actual_result']
next_work='Review the concrete offline writer-output budget alignment proposal; no new product modification or actual case allocated by the completed single-case grant'
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE29_E02_NATIVE_REJECTION_CONTROLLED_FAIL_REVIEWED',
    workflow_status='blocked',stage_queue_state='BLOCKED',active_review_agent=None,active_evidence=str(N),active_candidate=CANDIDATE,
    active_product_candidate=CANDIDATE,active_report=str(report),active_plan=str(proposal),last_actual_result=last_actual,
    latest_actual_candidate=CANDIDATE,active_result_review=dict(verdict='FAIL_CONFIRMED',path=str(review_path),sha256=sha(review_path),scope='LATEST_ACTUAL_CURRENT_CANDIDATE_D860'),
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    E02='NOT_PASSED',T2='NOT_PASSED',e02='NOT_PASSED',t2='NOT_PASSED',owner_gate='NOT_PASSED',current_e02_controlled_passed=0,
    e02_native_rejection_result=last_actual,
    current_one_case_allocation=dict(question_id=QUESTION,candidate=CANDIDATE,status='CONSUMED_FAIL_REVIEWED',remaining=0,result_review_remaining=0,retry=0),
    current_actual_execution=dict(question_id=QUESTION,candidate=CANDIDATE,run_id=RUN,status='COMPLETE_FAIL_REVIEWED',entry_invocations=1,retry=0),
    new_live_cases_this_execution=1,new_work_cli_submissions_this_execution=1,new_completed_inference_events_this_execution=None,
    new_completed_native_posts_this_execution=7,new_native_total_start_count_this_execution=None,
    new_model_calls_counter_basis='Seven completed native HTTP POST receipts; no successful trusted runtime/END or measured server-side total generation count',
    explicit_user_execution_status='COMPLETE_NATIVE_REJECTION_ONE_CASE_AND_RESULT_REVIEW_FAIL',goal_turn_outcome='PROGRESS_ONE_CASE_REJECTION_PREDICATE_CONFIRMED',
    latest_readonly_runtime_receipt=str(N/'review/result-inputs/readonly-closeout.json'),latest_readonly_runtime_sha256=sha(N/'review/result-inputs/readonly-closeout.json'),
    next_action_scope=dict(authorized=False,scope='Proposed offline writer-output budget alignment; no new actual allocation',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    next_proposal=dict(path=str(proposal),status='PROPOSAL_ONLY_NOT_IMPLEMENTED',actual_case_allocation=0,result_review_allocation=0),
    next_work=next_work,next_action=next_work,next_offline_plan=str(proposal))
state['source29_preparation']['status']='COMPLETED_USED_BY_ONE_ACTUAL'
state['active_preparation']['status']='COMPLETED_ACTUAL_CONSUMED'
state.pop('pending_actual_result',None)
summary='E02 d860b2a唯一实际FAIL_CONFIRMED：第7次响应done_reason=length、eval_count=2048达原上限，无research.md/写入/ACK；清理与保护核对PASS，单例/独审已消费，不重试。'
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1); assert count==1
append='\n\n## 2026-11-07 E02 native rejection controlled result\n\n'+summary+'\n报告：'+str(report)+'\n后续提案：'+str(proposal)+'\n'
texts[str(paths[1])]=wo+append; texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$',
    '| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8')); assert count==1
texts[str(paths[3])]=index
texts[str(paths[4])]=before[str(paths[4])].decode('utf8')+f'\n- Explicit {QUESTION} actual1/review1 completed; run {RUN} FAIL_CONFIRMED. Native done_reason=length/eval_count2048 at original cap; no write/ACK/artifact. No retry.\n- Result manifest {RESULT_MANIFEST}, independent review {sha(review_path)}. Model unchanged, actual/review remaining0, E02/T2/Owner not passed.\n'
backup=N/'verification/result-closeout-before'; backup.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)]; (backup/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths: p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/result-closeout-registration.json',dict(summary=summary,review_sha256=sha(review_path),result_manifest_sha256=RESULT_MANIFEST,
    before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},
    mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],actual_remaining=0,result_review_remaining=0,acceptance_credit=0))
q=Path('H:/UltimaAI/_shared/queue')
assert sha(q/'queue-status-gen.py')=='da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
run=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(q/'queue-status-gen.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
save(N/'verification/result-queue-refresh.json',dict(exit_code=run.returncode,stdout=run.stdout.decode('utf8'),stderr=run.stderr.decode('utf8'),
    generator_sha256=sha(q/'queue-status-gen.py'),queue_sha256=sha(q/'queue-status.json'),semantic_registration_only=True))
assert run.returncode==0
with (N/'verification/result-queue-status.json').open('xb') as f: f.write((q/'queue-status.json').read_bytes())
print(json.dumps(dict(result='FAIL_CONFIRMED',report=str(report),mirror_files=2,allocations=0),ensure_ascii=False))
