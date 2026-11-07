"""Record the independently confirmed first result; do not reopen its allocation."""
from pathlib import Path
import datetime as dt,hashlib,json,re,subprocess,sys
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
HEAD='0421a54cab572be013c3f7ad562e86406bfe8e52';RUN='9dbe192a-3bc1-4a4d-a218-581846d5f654';QUESTION='call_8b7f20b59b8d4855b50e36d5ccc115ba'
RESULT='3ebd6811702ed9eb09beb1c2d2efe418a491bd9f0078b9ea51db507c38b47f61'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
review_path=N/'review/independent-result-review.json';review=load(review_path)
assert review['reviewer']=='root-independent' and review['verdict']=='FAIL_CONFIRMED' and review['acceptance_credit']==0
assert review['candidate']==HEAD and review['run_id']==RUN and review['result_manifest_sha256']==RESULT
manifest=N/'review/result-inputs/result-manifest.json';assert sha(manifest)==RESULT
for name,h in load(manifest)['files'].items():assert sha(N/name)==h,name
A=N/'actual/E02-controlled-1';product=load(A/'product-result.json');d=load(A/'trusted-failure-diagnostic.raw');terminal=load(A/'terminal.json')
execution=load(N/'release/tool-execution-receipt.json');rb=load(N/'review/result-inputs/byte-readback.json');observed=load(N/'review/result-inputs/readonly-closeout.json');witness=load(N/'release/root-outcome.json')['outcome']['witness']
native=d['native_response'];http=d['last_http']
assert execution['question_id']==QUESTION and execution['invocations']==1 and execution['retry']==0
assert terminal['run_id']==RUN and terminal['overall']=='FAIL' and terminal['cleanup']['status']=='PASS'
assert product['status']=='failed' and product['content']=='本次研究未交付。' and product['error']=='Invalid native research response'
assert native['reason']=='done_reason' and native['done_reason']=='length' and native['eval_count']==native['max_tokens']==2048
assert native['generation']==http['generation']==7 and native['receipt_index']==http['receipt_index']==20 and http['status']==200
assert native['request_sha256']==http['request_sha256']=='8d7524386e508dd356b3a394fd389061b31512d40317e8e88ae2db942a9c1d53'
assert http['request_bytes']==33716 and native['response_bytes']==10418 and native['prompt_eval_count']==8932
assert rb['research_files']==0 and not d['write_confirmed'] and not d['ack_confirmed'] and d['final_answer'] is None
assert rb['owned_identities_absent'] and rb['isolated_port_free'] and observed['protected_count']==7 and observed['protected_all_equal']
report=R/'docs/reports/jarvis-work-t2-e02-output-budget-controlled-result-20261107.md'
china=dt.timezone(dt.timedelta(hours=8));started=dt.datetime.fromisoformat(execution['started_utc']).astimezone(china).isoformat();finished=dt.datetime.fromisoformat(execution['finished_utc']).astimezone(china).isoformat()
text=f'''# E02 输出预算对齐候选：单例结果与独立复核

候选{HEAD}的唯一当前8B原题四来源研究已结束，独立结论 **FAIL_CONFIRMED**。没有交付research.md，E02仍0/3，T2/Owner未通过。本例表明将实际输出预算写入共享提示仍未解决这次交付失败；不能据此认定8B在原预算下绝对不可能，也不能把离线通过转为产品验收。

## 本次完成与结果

离线补修只改三个生产文件与两个测试文件，产品927项（924产品+3兼容）、入口346项及计划/产品/入口独审已完成。入口曾有decision_id缺项造成33通过/1错误，失败保留后修正绑定，受影响34项通过；原函数AST与额度门不改。准备项目7ee6b08、镜像06b138c及冻结候选tag均保留。

用户{QUESTION}明确分配actual1/结果独审1/retry0。唯一entry1/CLI1实际运行：北京时间{started}至{finished}，外层{execution['outer_elapsed_seconds']:.6f}秒。公开回复“本次研究未交付。”，status=failed，error=Invalid native research response；research.md0、write0、ACK0。

search1/GET4成功；私有记录六次确认读取、五页visible，S1起行26/50/74/98、S2起20、S3起25。三来源证据资格已打开写入，但不等于原题覆盖；S4未inspect。顶层tool_results的inspect0与私有六读按各自观察层保留，没有将二者混算。

## 原生响应及证据边界

第7次原生请求HTTP200，首个拒绝谓词reason=done_reason，记录done=true、done_reason=length、eval_count=max_tokens=2048、prompt_eval_count=8932、content_chars=4349。generation7/receipt20绑定同一请求/响应。请求{http['request_bytes']}字节，SHA256 {http['request_sha256']}；响应计数{native['response_bytes']}字节，SHA256 {native['response_sha256']}。

失败诊断v4为{(A/'trusted-failure-diagnostic.raw').stat().st_size}字节，SHA256 {sha(A/'trusted-failure-diagnostic.raw')}；complete=false/END=false/acceptance_credit0。完整响应正文未封存，不能确定具体字段、重复、思考、转义或JSON结构如何耗尽额度；响应字节数/字符数不证明内容。该候选的提示预算对齐在本次没有产生交付，不能推断后续校验本来会通过。

父d860b2a的72d7d71b-39a9-455a-b0b4-8823b3f24c00同样第7响应length/2048，无文件。两例完整失败均保留；它们不是当前候选两次重试，也不构成通过率或延迟基准。相同读取起点可以从各自诊断核对，根因范围仅限各自确证的首个拒绝谓词。

## 清理、时间与保护

应用native POST7、完成7；服务端真实生成启动总数未测量。原时限和预算不变：CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/root275/cleanup310/seal315；context16384；阶段256/2048。只用原qwen3-8b-uncensored及原摘要，无14B、UI/音频或生产服务操作。

原cleanup PASS：六个本例身份不在、18799关闭、日志闭合，事后只读核对相符。七保护身份在保存的运行边界及事后核对点一致，不声称连续存活。root witness eligible=false、observation_error={witness.get('observation_error')}，时限资格保持{terminal['timing_eligibility']}；58.4秒这个观测不能升级为时限成功。

结果manifest {RESULT}（{len(load(manifest)['files'])}成员），独立结果审查SHA256 {sha(review_path)}。无产物，事实、引用及原题覆盖未通过，接受信用0。准备169成员、76源码、1594输入和旧实际seal保留；15个无关文件不变。

## 当前边界与建议顺序

本次已分配的唯一实际和唯一独立复核均完成，剩余0，失败后结束本次序列，没有重试或新产品修改。建议下一步先审查输出结构诊断与交付方式：以这两份固定失败为输入，列明当前2048输出契约的必须字段、现有受限记录能够回答及不能回答的问题，再提出足以定位截断位置的最小观察方案；需要新的产品修改或真实回执时另行明确范围。本结果不授权下一例，也不提出扩大token预算、更换8B或放宽原题验收。

本地项目/UltimaDocs提交、tag及读回由verification/result-publication-readback.json与result-final-readback.json记录。此前远端push被自动审批以blocked by policy拒绝，本轮未重试。证据根：{N.as_posix()}。
'''
with report.open('x',encoding='utf8',newline='\n') as f:f.write(text)
target=M/'reports'/report.name;target.parent.mkdir(parents=True,exist_ok=True)
with target.open('xb') as f:f.write(report.read_bytes())
paths=[N.parent/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),N/'progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])]);assert state['current_one_case_allocation']['question_id']==QUESTION
actual=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',purpose='output_budget_alignment_one_case',run_id=RUN,candidate=HEAD,model='qwen3-8b-uncensored',model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',question_id=QUESTION,result='FAIL',independent_review='FAIL_CONFIRMED',review_path=str(review_path),review_sha256=sha(review_path),result_manifest_sha256=RESULT,terminal_sha256=sha(A/'terminal.json'),product_result_sha256=sha(A/'product-result.json'),entry_invocations=1,work_cli_attempts=terminal['work_cli_attempts'],controlled_search_success=1,controlled_GET_success=4,confirmed_inspect_pages=6,visible_inspect_pages=5,top_level_successful_inspect_results=0,write_attempts=0,successful_write_count=0,research_artifacts=0,application_native_POST_attempts=7,completed_native_posts=7,actual_native_start_count=None,outer_elapsed_seconds=execution['outer_elapsed_seconds'],timing_eligibility=terminal['timing_eligibility'],cleanup='PASS',root_witness_eligible=False,root_witness_observation_error=witness.get('observation_error'),public_content=product['content'],product_error=product['error'],failure_diagnostic_sha256=sha(A/'trusted-failure-diagnostic.raw'),failure_diagnostic_bytes=(A/'trusted-failure-diagnostic.raw').stat().st_size,branch=d['branch'],eligible_source_ids=d['eligible_source_ids'],last_http=http,native_response=native,selected_pages=[dict(source_id=p['source_id'],start=p['requested_start'],range=p['range'],confirmed=p['confirmed'],visible=p['visible']) for p in d['pages']],budget=d['budget'],write_confirmed=False,ack_confirmed=False,final_answer_preserved=False,facts='NOT_ASSESSABLE_NO_ARTIFACT',original_question_coverage='NOT_PASSED_NO_ARTIFACT',non_delivery_reply_observed=True,protected_at_recorded_boundaries=True,protected_after_readonly=True,continuous_liveness_measured=False,acceptance_credit=0,controlled_passed=0,controlled_required=3,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,retry=0,next_case_released=False,E02='NOT_PASSED',T2='NOT_PASSED',Owner='NOT_PASSED',old_credit_transferred=False,remote_synced=False,cause='Generation7 HTTP200 rejected on done_reason=length; eval_count=max_tokens2048 after output-budget guidance alignment',native_rejection_predicate_proven=True,real_delivery_improvement_proven=False,native_compatibility_limit='Bounded first-refusal projection only; full response body unavailable; no inference of the truncated internal content or universal8B capability',previous_actual_preserved_at=str(N/'verification/result-closeout-before/0-current-run.json'),recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
state['previous_actual_result']=state['last_actual_result']
next_work='Review the output-structure observation and delivery design using the two preserved failures; no further product modification or actual case allocated'
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE31_E02_OUTPUT_BUDGET_CONTROLLED_FAIL_REVIEWED',workflow_status='blocked',stage_queue_state='BLOCKED',active_review_agent=None,active_evidence=str(N),active_candidate=HEAD,active_product_candidate=HEAD,active_report=str(report),active_plan=str(N/'execution-proposal.md'),last_actual_result=actual,latest_actual_candidate=HEAD,active_result_review=dict(verdict='FAIL_CONFIRMED',path=str(review_path),sha256=sha(review_path),scope='LATEST_ACTUAL_CURRENT_CANDIDATE_0421A54'),actual_case_allocation_remaining=0,result_review_allocation_remaining=0,e02_execution_released=False,live_gate_released=False,next_stage_released=False,E02='NOT_PASSED',T2='NOT_PASSED',e02='NOT_PASSED',t2='NOT_PASSED',owner_gate='NOT_PASSED',current_e02_controlled_passed=0,e02_output_budget_result=actual,current_one_case_allocation=dict(question_id=QUESTION,candidate=HEAD,status='CONSUMED_FAIL_REVIEWED',remaining=0,result_review_remaining=0,retry=0),current_actual_execution=dict(question_id=QUESTION,candidate=HEAD,run_id=RUN,status='COMPLETE_FAIL_REVIEWED',entry_invocations=1,retry=0),new_live_cases_this_execution=1,new_work_cli_submissions_this_execution=1,new_completed_inference_events_this_execution=None,new_completed_native_posts_this_execution=7,new_native_total_start_count_this_execution=None,new_model_calls_counter_basis='Seven completed native HTTP POST receipts; server-side total starts not measured',explicit_user_execution_status='COMPLETE_OUTPUT_BUDGET_ONE_CASE_AND_RESULT_REVIEW_FAIL',goal_turn_outcome='ONE_CASE_COMPLETED_BUDGET_GUIDANCE_DID_NOT_DELIVER',latest_readonly_runtime_receipt=str(N/'review/result-inputs/readonly-closeout.json'),latest_readonly_runtime_sha256=sha(N/'review/result-inputs/readonly-closeout.json'),next_action_scope=dict(authorized=False,scope='Recommended output-structure diagnosis and delivery-design review; no new actual allocation',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),next_proposal=dict(path=str(report),kind='RESULT_WITH_RECOMMENDED_NEXT_SCOPE',status='NO_NEW_CASE_OR_PRODUCT_CHANGE_ALLOCATED',actual_case_allocation=0,result_review_allocation=0),next_work=next_work,next_action=next_work,next_offline_plan=None)
state['source31_preparation']['status']='COMPLETED_USED_BY_ONE_ACTUAL';state['active_preparation']['status']='COMPLETED_ACTUAL_CONSUMED';state.pop('pending_actual_result',None)
summary='E02 0421a54唯一实际FAIL_CONFIRMED：第7响应仍length/2048，无research.md/写入/ACK；清理与保护核对PASS，单例与独审均消费，不重试。'
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-07 E02 output budget controlled result\n\n'+summary+'\n报告：'+str(report)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1;texts[str(paths[3])]=index
texts[str(paths[4])]=before[str(paths[4])].decode('utf8')+f'\n- Explicit {QUESTION} actual1/review1 completed; run {RUN} FAIL_CONFIRMED, no delivery/write/ACK. No retry; remaining0.\n- Result manifest {RESULT}; independent result review {sha(review_path)}. Offline preparation passed; actual E02 remains0/3, T2/Owner not passed.\n'
backup=N/'verification/result-closeout-before';backup.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(backup/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/result-closeout-registration.json',dict(summary=summary,review_sha256=sha(review_path),result_manifest_sha256=RESULT,before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},mirror=[dict(source=str(report),target=str(target),sha256=sha(report))],actual_remaining=0,result_review_remaining=0,acceptance_credit=0))
q=Path('H:/UltimaAI/_shared/queue');assert sha(q/'queue-status-gen.py')=='da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
run=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(q/'queue-status-gen.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
save(N/'verification/result-queue-refresh.json',dict(exit_code=run.returncode,stdout=run.stdout.decode('utf8'),stderr=run.stderr.decode('utf8'),generator_sha256=sha(q/'queue-status-gen.py'),queue_sha256=sha(q/'queue-status.json'),semantic_registration_only=True));assert run.returncode==0
with (N/'verification/result-queue-status.json').open('xb') as f:f.write((q/'queue-status.json').read_bytes())
print(json.dumps(dict(result='FAIL_CONFIRMED',report=str(report),mirror_files=1,allocations=0),ensure_ascii=False))
