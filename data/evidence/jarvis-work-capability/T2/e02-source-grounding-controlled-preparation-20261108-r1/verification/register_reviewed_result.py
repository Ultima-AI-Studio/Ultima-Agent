"""Close exactly one independently failed case without new code or run authority."""
from pathlib import Path
import datetime as dt,hashlib,json,re
N=Path(__file__).resolve().parents[1];R=N.parents[4];A=N/'actual/E02-controlled-1'
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
HEAD='43da3f014a763b8ea3963872a8f1ce8ebea77531';RUN='d0109d12-520f-4f92-88a3-938e69905ba2'
QUESTION='call_7004c6eafaca48e3a6f19dd87f59d024'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
rp=N/'review/independent-result-review.json';review=load(rp);review_sha=sha(rp)
assert review['reviewer']=='root-independent' and review['verdict']=='FAIL_CONFIRMED' and review['acceptance_credit']==0
assert review['candidate']==HEAD and review['run_id']==RUN and review['actual_run_authorized'] is False
claim_reviews=review.get('claim_reviews',review.get('factual_review'))
assert claim_reviews and review['findings']
rm=N/'review/result-inputs/result-manifest.json';assert review['result_manifest_sha256']==sha(rm)=='87e267c51e8fb9397258ab0e9dfd26db828ff74fcdbd173ce78bffea6842a66f'
for rel,h in load(rm)['files'].items():assert sha(N/rel)==h,rel
execution=load(N/'release/tool-execution-receipt.json');outcome=load(N/'release/root-outcome.json')
terminal=load(A/'terminal.json');product=load(A/'product-result.json');runtime=load(A/'trusted-runtime.raw');readback=load(N/'review/result-inputs/readonly-closeout.json')
effects=load(A/'accepted-effects.json');assert len(effects)==1
artifact=Path(effects[0]['path']);assert sha(artifact)==effects[0]['sha256']=='974feebdd606d0670185108a2b964a810b412ab5702696287b5253a3341c57df'
assert execution['invocations']==1 and execution['retry']==0 and runtime['transport']['posts']==runtime['transport']['completed']==7
assert product['status']=='succeeded' and terminal['cleanup']['status']=='PASS' and readback['protected_all_equal'] and readback['protected_count']==7
assert outcome['outcome']['witness']['eligible'] is True and terminal['timing_eligibility']=='UNOBSERVED_NEVER_TIMED_PASS'
assert not readback['isolated_port_owners'] and all(not x['matching_identity_present'] for x in readback['owned_after'])
writer=next(w for w in runtime['wires'] if w['raw_envelope'].get('action')=='ultima_work_research_write');ack=runtime['wires'][-1]
assert writer['raw']['done_reason']==ack['raw']['done_reason']=='stop' and writer['raw']['eval_count']==601 and ack['raw']['eval_count']==39
assert len(writer['raw_envelope']['action_input']['sections'])==3
raw_writes=sum(x.get('tool_name')=='ultima_work_research_write' and x.get('success') is True for x in product['tool_results']);assert raw_writes==2
report=R/'docs/reports/jarvis-work-t2-e02-source-grounding-controlled-result-20261108.md'
proposal=R/'docs/plans/jarvis-work-e02-write-eligibility-and-evidence-scope-proposal-20261108.md'
assert proposal.is_file()
paths=[N.parent/'current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),N/'progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])])
assert state['last_actual_result']['run_id']=='1496a844-668d-407a-a91b-89be246ba05b' and state['pending_actual_result']['run_id']==RUN
assert state['current_one_case_allocation']['question_id']==QUESTION
assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
for p in (report,M/'reports'/report.name,M/'plans'/proposal.name,N/'verification/result-closeout-registration.json',N/'review/result-final-registration.json'):
    assert not p.exists(),p
china=dt.timezone(dt.timedelta(hours=8));start=dt.datetime.fromisoformat(execution['started_utc']).astimezone(china);end=dt.datetime.fromisoformat(execution['finished_utc']).astimezone(china)
text=f'''# E02 证据优先与来源读取候选：单例结果和独立复核

原工单 wo-ultimaagent-20261101-0021 / T2；冻结候选 {HEAD}。本例确已生成 research.md、完成写入读回与 ACK；独立结果 **FAIL_CONFIRMED**：事实与引用及完整原题覆盖未通过。9 条陈述仅第7–9条得到所选锚点直接支持。E02仍0/3，T2/Owner未通过；保留实际产物，不误报“未生成文件”。

## 本次实际完成情况

用户 {QUESTION} 明确分配一例研究与一次独立结果复核，retry0；run {RUN}。北京时间 {start.isoformat()} 至 {end.isoformat()}，外层耗时 {execution['outer_elapsed_seconds']:.6f} 秒。固定当前 qwen3-8b-uncensored，原题、四来源和原预算保持。仅调用原入口一次、CLI一次、search1/GET4、inspect5；应用原生POST7且完成7。服务端实际生成启动总数未测量，保持null。

第6次 writer 正常 stop，601/2048 tokens；第7次 ACK stop，39/256 tokens。七次均正常 stop。本例9个事实对象均实际先输出 evidence_id，再输出 claim；这是本例响应证据，不代表自然语言事实已经正确或稳定性已经通过。

实际文件写入和接受副作用各1；product status=succeeded。tool_results 中两条 research_write 成功行是不同层级的记录，不能计为两次物理写入。可信runtime、文件字节读回、ACK的逐项判断见独审。

- [实际 research.md（事实验收未通过）]({artifact.as_posix()})，{artifact.stat().st_size}字节，3节9条陈述；SHA256 {sha(artifact)}。
- [独立逐事实复核]({(N/'review/independent-result-review.md').as_posix()})，JSON SHA256 {review_sha}。
- [原始结果清单]({rm.as_posix()})，66成员，SHA256 {sha(rm)}。

## 已确证的内容缺口

1、2、4使用的标题或局部声明不能直接支持所写的更广泛事实。第3条还将Whisper/Parakeet转录模型与LLM混淆。第5条把TODO内容扩展成当前provider支持状态，未读到同一来源48–51行已构造GeminiProvider的实现。第6条把console.log与锚点之外的Logger.info合成一条陈述。只有第7–9条的日志或计时局部陈述与所选锚点匹配。引用不通过不等于每条事实在所有资料中均为假，具体标准是该陈述能否由它选择的锚点直接支持。

页面顺序为S1三页（26–49、50–73、74–97）、S2一页（20–43）、S3一页（25–48）。S4已GET但inspect0。第6次请求仍提供仅可选择S4的inspect分支，同时允许write；模型在还有一次读取机会时提前写入。三来源资格已满足，原题要求的架构关系、工具执行路径和现有开源底座接入没有完整回答；日志和产品宣传不能替代这些内容。

## 原时限、清理与保全

CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒，context16384、messages+schema32768/entity49152字节、输出2048及较小阶段上限保持。未重试、换模型或扩预算，无UI、音频和生产服务操作。

原terminal的PENDING_ROOT_INDEPENDENT_REVIEW及timing_eligibility=UNOBSERVED_NEVER_TIMED_PASS不改写。root witness eligible=true；独审根据绑定本run的时钟、terminal/seal摘要和观察事件核对原时限，不能只由67秒外层耗时推出TIMED_PASS。清理PASS，本例身份在保存的收尾观察中消失、隔离端口关闭；七个保护身份在保存的核对点相符，未证明连续存活或报告时实时状态。

179准备成员、79产品源pin、1606输入及旧失败保持；1022产品相关与350入口离线检查是此前准备证据，本次没有重跑或转为实际信用。一个非输入tracker HTML按已独审的动态观察例外保留，其他14个无关文件严格核对。本次一例与一次结果复核已消费，剩余0。

## 下一步与归档

[后续提案]({proposal.as_posix()})先审查写入资格与任务证据覆盖的衔接，再审查逐证据原子事实表达。提案未实施、未独审，不产生修复或下一单例授权。当前8B、原预算和完整原题验收保持，不以字段顺序或重复提示代替语义证据。

[根controller只读补充分析]({(N/'verification/result-source-analysis.json').as_posix()})独立署名，不冒充原66成员结果manifest或独审。结果报告与后续提案镜像至UltimaDocs，本地commit/tag及Git/disk读回由result-publication-readback.json、result-final-readback.json证明。

全局汇总刷新本轮因另一工单0026使用生成器不接受的completed状态失败；本工单canonical登记照常更新，13:31旧汇总明确标为非新鲜，没有改其他工单或弱化生成器。独立补充审查允许继续本地归档，不等于汇总刷新成功。远端push此前被自动审批以blocked by policy拒绝，本轮没有重试或换通道。
'''
with report.open('x',encoding='utf8',newline='\n') as f:f.write(text)
mirror=[]
for source,target in ((report,M/'reports'/report.name),(proposal,M/'plans'/proposal.name)):
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(source.read_bytes())
    assert target.read_bytes()==source.read_bytes()
    mirror.append(dict(source=str(source),target=str(target),sha256=sha(source)))
actual=dict(run_id=RUN,candidate=HEAD,question_id=QUESTION,result='FAIL',independent_review='FAIL_CONFIRMED',review_sha256=review_sha,
    result_manifest_sha256=sha(rm),report=str(report),evidence=str(A),artifact_path=str(artifact),artifact_sha256=sha(artifact),artifact_bytes=artifact.stat().st_size,
    entry_invocations=1,retry=0,application_native_POST_attempts=7,completed_native_posts=7,actual_native_start_count=None,inspect_pages=5,
    research_artifacts=1,successful_write_count=1,raw_research_write_success_rows=raw_writes,write_confirmed=True,ack_confirmed=True,product_status=product['status'],product_error=product['error'],
    outer_elapsed_seconds=execution['outer_elapsed_seconds'],timing_eligibility=terminal['timing_eligibility'],root_witness_eligible=True,cleanup='PASS_AT_RECORDED_OBSERVATIONS',
    protected_at_recorded_boundaries=True,protected_after_readonly=True,continuous_liveness_measured=False,
    writer_done_reason='stop',writer_eval_count=601,ack_done_reason='stop',ack_eval_count=39,writer_evidence_first_fact_count=9,
    facts='FAIL',original_question_coverage='FAIL',claim_reviews=claim_reviews,findings=review['findings'],
    fully_supported_claims=[7,8,9],acceptance_credit=0,controlled_passed=0,controlled_required=3,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    next_case_released=False,E02='NOT_PASSED',T2='NOT_PASSED',Owner='NOT_PASSED',old_credit_transferred=False,remote_synced=False,
    cause='Physical delivery completed; selected-anchor factual support and full original-question coverage failed',mechanical_delivery_observed=True,acceptable_research_delivery_proven=False,stability_proven=False,
    previous_actual_preserved_at=str(N/'verification/result-closeout-before/0-current-run.json'),recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
assert actual['claim_reviews']
state['previous_actual_result']=state['last_actual_result']
next_work='Review the offline write-eligibility and evidence-scope proposal; no new repair or actual case allocated'
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE37_E02_SOURCE_GROUNDING_CONTROLLED_FAIL_REVIEWED',workflow_status='blocked',stage_queue_state='BLOCKED',active_review_agent=None,
    active_evidence=str(N),active_candidate=HEAD,active_product_candidate=HEAD,active_report=str(report),active_plan=str(N/'execution-proposal.md'),last_actual_result=actual,latest_actual_candidate=HEAD,
    active_result_review=dict(verdict='FAIL_CONFIRMED',path=str(rp),sha256=review_sha,scope='LATEST_ACTUAL_CURRENT_CANDIDATE_43DA3F0'),actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,E02='NOT_PASSED',T2='NOT_PASSED',e02='NOT_PASSED',t2='NOT_PASSED',owner_gate='NOT_PASSED',current_e02_controlled_passed=0,e02_source_grounding_result=actual,
    current_one_case_allocation=dict(question_id=QUESTION,candidate=HEAD,status='CONSUMED_FAIL_REVIEWED',remaining=0,result_review_remaining=0,retry=0),current_actual_execution=dict(question_id=QUESTION,candidate=HEAD,run_id=RUN,status='COMPLETE_FAIL_REVIEWED',entry_invocations=1,retry=0),
    new_live_cases_this_execution=1,new_work_cli_submissions_this_execution=1,new_completed_inference_events_this_execution=None,new_completed_native_posts_this_execution=7,new_native_total_start_count_this_execution=None,
    new_model_calls_counter_basis='Seven completed native HTTP POST receipts; server-side total starts not measured',explicit_user_execution_status='COMPLETE_SOURCE_GROUNDING_ONE_CASE_AND_RESULT_REVIEW_FAIL',
    goal_turn_outcome='ONE_CASE_AND_REVIEW_COMPLETED_DELIVERY_OBSERVED_FACTS_AND_COVERAGE_FAILED',goal_status='none',goal_registry_status='cleared_by_user',goal_registry_note='User cleared goal; no goal created or resumed. Explicit one-case scope completed.',
    latest_readonly_runtime_receipt=str(N/'review/result-inputs/readonly-closeout.json'),latest_readonly_runtime_sha256=sha(N/'review/result-inputs/readonly-closeout.json'),live_runtime_readiness='PASSED_AT_SAVED_CASE_PREFLIGHT_NOT_A_CURRENT_LIVENESS_CLAIM',
    next_action_scope=dict(authorized=False,scope='Proposed offline write eligibility and evidence scope review; future actual allocation separate',actual_case_allocation=0,result_review_allocation=0,model_calls=0,service_operations=0),
    next_proposal=dict(path=str(proposal),kind='EVIDENCE_LED_OFFLINE_WRITE_ELIGIBILITY_AND_EVIDENCE_SCOPE',status='PROPOSED_NOT_IMPLEMENTED_OR_REVIEWED',actual_case_allocation=0,result_review_allocation=0),next_work=next_work,next_action=next_work,next_offline_plan=str(proposal))
state['source37_preparation']['status']='COMPLETED_USED_BY_ONE_ACTUAL';state['active_preparation']['status']='COMPLETED_ACTUAL_CONSUMED'
state['e02_source_grounding_controlled_preparation'].update(status='COMPLETED_USED_BY_ONE_ACTUAL',scope='Historical offline preparation; latest result in e02_source_grounding_result',new_candidate_actual_output_not_yet_captured=False,actual_result_run_id=RUN,mechanical_delivery_observed=True,acceptable_research_delivery_proven=False)
state.pop('pending_actual_result',None)
summary='E02 43da3f0唯一实际已写research.md并读回/ACK；独审FAIL_CONFIRMED：9条中3条锚点支持通过，事实引用与原题覆盖失败，仍0/3。POST7/完成7，67.108秒；一例与一次复核耗尽，不重试。'
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-08 E02 source grounding controlled result\n\n'+summary+'\n报告：'+str(report)+'\n下一提案（未实施）：'+str(proposal)+'\n'
index,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n',str(paths[1]):wo+append,str(paths[2]):before[str(paths[2])].decode('utf8')+append,str(paths[3]):index,str(paths[4]):before[str(paths[4])].decode('utf8')+'\n- Explicit '+QUESTION+' actual1/review1 completed: '+RUN+' FAIL_CONFIRMED; remaining0/retry0. Physical delivery/ACK observed; facts and full coverage fail, acceptance0. Result archive/final readback follows.\n'}
backup=N/'verification/result-closeout-before';backup.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)],p
    (backup/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/result-closeout-registration.json',dict(summary=summary,run_id=RUN,candidate=HEAD,review_sha256=review_sha,review_markdown_sha256=sha(N/'review/independent-result-review.md'),result_manifest_sha256=sha(rm),result='FAIL_CONFIRMED',before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},mirror=mirror,actual_remaining=0,result_review_remaining=0,acceptance_credit=0))
save(N/'review/result-final-registration.json',dict(status='FAIL_CONFIRMED',run_id=RUN,candidate=HEAD,supersedes_pending_registration_sha256=sha(N/'review/result-registration.json'),review_sha256=review_sha,result_manifest_sha256=sha(rm),actual_remaining=0,result_review_remaining=0,research_files=1,write_confirmed=True,ack_confirmed=True,facts='FAIL',coverage='FAIL',acceptance_credit=0,next_case_authorized=False,retry=False))
save(N/'verification/result-queue-refresh.json',dict(status='NOT_RERUN_KNOWN_INVALID_OTHER_ORDER_STATE',aggregate_regenerated=False,prior_failure_sha256=sha(N/'verification/queue-refresh.json'),canonical_registration_updated=True))
print(json.dumps(dict(result='FAIL_CONFIRMED',report=str(report),proposal=str(proposal),mirror_files=2,actual_remaining=0,review_remaining=0,research_files=1,acceptance_credit=0),ensure_ascii=False))
