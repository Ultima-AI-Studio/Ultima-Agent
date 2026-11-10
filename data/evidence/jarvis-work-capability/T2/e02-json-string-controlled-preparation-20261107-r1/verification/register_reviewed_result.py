"""Register the independently confirmed first outcome, preserving failed evidence and exhausted quotas."""
from pathlib import Path
import datetime as dt,hashlib,json,re,subprocess,sys
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
CANDIDATE='6d758d9c3961f156a062e349ec4a949e2ee7a9a9'
RUN='bc216374-f59c-4967-99f2-ded53a4ea49d'
QUESTION='call_6f04750fa3644cc39ce356ff25b1ca6b'
RESULT_MANIFEST='3a3bda952dbbfaf6c10537e3634549a9321248fcf2eb62bb2875001b538aca3b'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,value):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2)
review_path=N/'review/independent-result-review.json';review=load(review_path)
assert review['reviewer']=='root-independent' and review['verdict']=='FAIL_CONFIRMED'
assert review['candidate']==CANDIDATE and review['run_id']==RUN and review['acceptance_credit']==0
manifest_path=N/'review/result-inputs/result-manifest.json'
assert sha(manifest_path)==RESULT_MANIFEST==review['result_manifest_sha256']
for path,h in load(manifest_path)['files'].items():assert sha(N/path)==h,path
A=N/'actual/E02-controlled-1';product=load(A/'product-result.json');diagnostic=load(A/'trusted-failure-diagnostic.raw')
terminal=load(A/'terminal.json');execution=load(N/'release/tool-execution-receipt.json')
rb=load(N/'review/result-inputs/byte-readback.json');last=diagnostic['last_http']
assert execution['question_id']==QUESTION and execution['invocations']==1 and execution['retry']==0
assert terminal['run_id']==RUN and terminal['overall']=='FAIL' and terminal['cleanup']['status']=='PASS'
assert product['status']=='failed' and product['content']=='本次研究未交付。' and product['error']=='Invalid native research response'
assert diagnostic['branch']=='unvalidated_response' and last['status']==200 and last['validated_response'] is False
assert last['request_sha256']=='5df7beb8defa890600d66d64a0b438b32dfa85bd0bea2f2c3ca52379188a6da4' and last['request_bytes']==33390
assert len(diagnostic['pages'])==6 and diagnostic['eligible_source_ids']==['S1','S2','S3']
assert diagnostic['final_answer'] is None and not diagnostic['write_confirmed'] and not diagnostic['ack_confirmed']
assert rb['research_files']==0 and rb['owned_identities_absent'] and rb['isolated_port_free']
report=R/'docs/reports/jarvis-work-t2-e02-json-string-controlled-result-20261107.md'
proposal=R/'docs/plans/jarvis-work-e02-native-response-rejection-diagnostics-proposal-20261107.md'
text=f'''# E02 JSON 字符串候选：唯一实际结果与独立复核

候选 {CANDIDATE} 的一例当前8B受控研究已经结束，独立结果 **FAIL_CONFIRMED**。本次未交付research.md，E02仍0/3，T2/Owner未通过。本次第7次原生请求返回HTTP200，随后被原生响应校验拒绝；这只说明本次未重现上一例HTTP500，不能宣称整体兼容已修复。

## 结果与确证边界

公开content为“本次研究未交付。”，status=failed，error=Invalid native research response。没有写入、ACK或可信成功runtime proof。六次确认读取依次为S1起行26/50/74/98、S2起行20、S3起行25；S1/S2/S3具备证据资格，前五页visible=true，第六页confirmed=true但visible=false。三来源资格不等于原题覆盖或事实交付；上层tool_results只返回search1/GET4，inspect0与私有诊断的六读分别记录，不相互替代。

源码已把稳定错误定位到src/brain/work_research.py:561-572的checked_native_response。该函数对字段集合、模型身份、done/done_reason、message结构/角色/内容、token计数、时长及created_at使用同一拒绝标签。现有证据不能判定具体触发了哪项；不能直接称为length截断、内部JSON、工具schema或模型能力问题。响应接收计数8328字节，不等于结果包保存了可复核的完整响应正文；失败私有诊断没有原生拒绝项。

## 请求、时限与保护

run {RUN}；用户明确分配 {QUESTION}。唯一入口调用1，retry0；{execution['started_utc']}至{execution['finished_utc']}，外层{execution['outer_elapsed_seconds']:.6f}秒。应用native POST7，完成7，服务器实际生成启动总数未测量。

最后generation7/chat/status200，send_reserved=true，transport_failed=false，validated_response=false。请求33390字节，SHA256 {last['request_sha256']}；downloaded/inspected/admitted/retained均8328。诊断5494字节，SHA256 {sha(A/'trusted-failure-diagnostic.raw')}。预算快照reads6/6、nativePOST7/8、剩209.818649秒，不能据此把失败用例升为计时PASS。原预算、当前qwen3-8b-uncensored及摘要、原题四来源保持。

原cleanup PASS，登记六个本例进程身份消失，18799关闭，日志关闭。七个保护身份在运行边界及之后只读核对点相符，仅代表核对点；不宣称连续存活。没有UI、音频或生产服务操作。旧N15 run5e6ea89c-8e47-43a6-9480-7a11d72cabf5的HTTP500失败和全部依赖封存保留，当前失败也不改写。

## 独立复核与接续

结果manifest {RESULT_MANIFEST}，56成员；独立结果复核SHA256 {sha(review_path)}。无产物，事实/引用/原题覆盖不能通过；接受信用0。准备344项及历史N16的781项不重复运行，不替代实际验收，旧候选E01/E03信用不迁移。

本次实际1与只读独立复核1均已消费，剩余0，不重试。后续提案jarvis-work-e02-native-response-rejection-diagnostics-proposal-20261107.md：先离线补原生响应拒绝的固定原因码和受限标量/摘要，再按确证原因做最小修改。冻结产品本轮不再修改，不放宽done_reason/token/事实/预算门，不换14B，不自动补发模型调用。新候选若需实际，仍须完成准备后明确分配单例。

项目与UltimaDocs的本地commit/tag和逐字节读回由verification/result-publication-readback.json记录。远端push此前遭自动审批blocked by policy，本轮不重试。证据根：{N.as_posix()}。
'''
with report.open('x',encoding='utf8',newline='\n') as f:f.write(text)
pairs=[(report,M/'reports'/report.name),(proposal,M/'plans'/proposal.name)]
for source,target in pairs:
    assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(source.read_bytes())
    assert sha(source)==sha(target)
paths=[N.parent/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),
    R/'.superpowers/sdd/jarvis-work-e02-json-string-controlled-entry-plan-20261107/progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])])
assert state['current_one_case_allocation']['question_id']==QUESTION
last_actual=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',
    purpose='native_json_string_contract_one_case',run_id=RUN,candidate=CANDIDATE,model='qwen3-8b-uncensored',
    model_digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330',question_id=QUESTION,
    result='FAIL',independent_review='FAIL_CONFIRMED',review_path=str(review_path),review_sha256=sha(review_path),
    result_manifest_sha256=RESULT_MANIFEST,terminal_sha256=sha(A/'terminal.json'),product_result_sha256=sha(A/'product-result.json'),
    entry_invocations=1,work_cli_attempts=terminal['work_cli_attempts'],controlled_search_success=rb['counts']['ultima_work_web_search'],
    controlled_GET_success=rb['counts']['ultima_work_http_get'],confirmed_inspect_pages=rb['failure_diagnostic']['confirmed_pages'],
    visible_inspect_pages=rb['failure_diagnostic']['visible_pages'],top_level_successful_inspect_results=rb['counts']['ultima_work_research_inspect'],
    write_attempts=0,successful_write_count=0,research_artifacts=0,application_native_POST_attempts=rb['application_native_POST_attempts'],
    completed_native_posts=rb['completed_native_posts'],actual_native_start_count=None,outer_elapsed_seconds=execution['outer_elapsed_seconds'],
    timing_eligibility=terminal['timing_eligibility'],cleanup='PASS',root_witness_eligible=False,public_content=product['content'],product_error=product['error'],
    failure_diagnostic_sha256=sha(A/'trusted-failure-diagnostic.raw'),failure_diagnostic_bytes=(A/'trusted-failure-diagnostic.raw').stat().st_size,
    branch=diagnostic['branch'],eligible_source_ids=diagnostic['eligible_source_ids'],last_http=last,
    selected_pages=[dict(source_id=p['source_id'],start=p['requested_start'],range=p['range'],confirmed=p['confirmed'],visible=p['visible']) for p in diagnostic['pages']],
    budget=diagnostic['budget'],write_confirmed=False,ack_confirmed=False,final_answer_preserved=False,false_completion_claim_preserved=False,
    facts='NOT_ASSESSABLE_NO_ARTIFACT',original_question_coverage='NOT_PASSED_NO_ARTIFACT',coverage_budget_link_observed=True,
    sixth_page_response_confirmed=False,non_delivery_reply_observed=True,protected_at_recorded_boundaries=True,protected_after_readonly=True,
    continuous_liveness_measured=False,acceptance_credit=0,controlled_passed=0,controlled_required=3,actual_case_allocation_remaining=0,
    result_review_allocation_remaining=0,retry=0,next_case_released=False,E02='NOT_PASSED',T2='NOT_PASSED',Owner='NOT_PASSED',
    old_credit_transferred=False,remote_synced=False,cause='Generation7 HTTP200 rejected by checked_native_response; exact combined guard not captured',
    native_compatibility_limit='HTTP200 on this case is not whole compatibility acceptance; response byte counters are not retained full body; no exact rejection predicate',
    previous_actual_preserved_at=str(N/'verification/result-closeout-before/0-current-run.json'),recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE27_E02_JSON_STRING_CONTROLLED_FAIL_REVIEWED',
    workflow_status='blocked',stage_queue_state='BLOCKED',active_review_agent=None,active_evidence=str(N),active_candidate=CANDIDATE,
    active_product_candidate=CANDIDATE,active_report=str(report),active_plan=str(proposal),last_actual_result=last_actual,
    active_result_review=dict(verdict='FAIL_CONFIRMED',path=str(review_path),sha256=sha(review_path),scope='LATEST_ACTUAL_CURRENT_CANDIDATE_6D'),
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,e02_execution_released=False,live_gate_released=False,
    next_stage_released=False,E02='NOT_PASSED',T2='NOT_PASSED',e02_json_string_result=last_actual,
    current_one_case_allocation=dict(question_id=QUESTION,candidate=CANDIDATE,status='CONSUMED_FAIL_REVIEWED',remaining=0,result_review_remaining=0,retry=0),
    next_action_scope=dict(authorized=False,scope='Follow-up bounded rejection diagnosis proposal; no new product modification or model request allocated by this case',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    next_proposal=dict(path=str(proposal),status='PROPOSAL_ONLY',actual_case_allocation=0,result_review_allocation=0),
    next_work='Offline bounded native response rejection diagnosis proposal; exact failed guard not established, no new actual allocation')
state['source27_preparation']['status']='COMPLETED_USED_BY_ONE_ACTUAL'
state['active_preparation']['status']='COMPLETED_ACTUAL_CONSUMED'
state.pop('pending_actual_result',None)
summary='E02 6d758d9唯一实际FAIL_CONFIRMED：第7次原生HTTP200被响应校验拒绝，无research.md/写入/ACK；清理及保护核对PASS，实际与独审额度已耗尽，不重试。'
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-07 E02 JSON string controlled result\n\n'+summary+'\n报告：'+str(report)+'\n后续提案：'+str(proposal)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$',
    '| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=index
texts[str(paths[4])]=before[str(paths[4])].decode('utf8')+f'\n- Explicit {QUESTION} actual1/review1 completed; run {RUN} FAIL_CONFIRMED. HTTP200 reached checked_native_response, exact rejected predicate unproven. No retry or acceptance credit.\n- Result manifest {RESULT_MANIFEST}, review {sha(review_path)}. Current allocations0; E02/T2/Owner not passed.\n'
backup=N/'verification/result-closeout-before';backup.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(backup/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/result-closeout-registration.json',dict(summary=summary,review_sha256=sha(review_path),result_manifest_sha256=RESULT_MANIFEST,
    before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},
    mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],actual_remaining=0,result_review_remaining=0,acceptance_credit=0))
q=Path('H:/UltimaAI/_shared/queue')
assert sha(q/'queue-status-gen.py')=='da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
run=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(q/'queue-status-gen.py')],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
save(N/'verification/result-queue-refresh.json',dict(exit_code=run.returncode,stdout=run.stdout.decode('utf8'),stderr=run.stderr.decode('utf8'),
    generator_sha256=sha(q/'queue-status-gen.py'),queue_sha256=sha(q/'queue-status.json'),semantic_registration_only=True))
assert run.returncode==0
with (N/'verification/result-queue-status.json').open('xb') as f:f.write((q/'queue-status.json').read_bytes())
print(json.dumps(dict(result='FAIL_CONFIRMED',report=str(report),mirror_files=2,allocations=0),ensure_ascii=False))
