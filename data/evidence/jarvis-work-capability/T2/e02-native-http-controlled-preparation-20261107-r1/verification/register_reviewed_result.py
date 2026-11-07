"""Record the independently confirmed first result; never repair or rerun product."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,re
N=Path(__file__).resolve().parents[1];R=N.parents[4];A=N/'actual/E02-controlled-1';D=N/'review/result-inputs'
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def module(name,path):
    spec=importlib.util.spec_from_file_location(name,path);v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);return v
review_path=N/'review/independent-result-review.json';review=load(review_path)
assert review['reviewer']=='root-independent' and review['verdict']=='FAIL_CONFIRMED'
assert review['candidate']=='ee1bef61f04169c64978538dbc4ba799ef7be6c0'
assert review['run_id']=='91406fa9-5952-4e3a-99af-a94c8857c8d3'
assert review['result_manifest_sha256']==sha(D/'result-manifest.json')=='8d1b3920f1b15e3deec3c0b380eeb9476a2701454a0aa4f7f8c34fe79c43641e'
for name,digest in load(D/'result-manifest.json')['files'].items():assert sha(N/name)==digest,name
entry=module('result_registration_entry',N/'code/entry.py');entry.read_ready(N)
preservation=module('result_registration_preservation',N/'verification/verify_preservation.py').verify()
b=load(D/'byte-readback.json');t=load(A/'terminal.json');p=load(A/'product-result.json');packet=load(A/'trusted-failure-diagnostic.raw')
assert b['original_status']=='FAIL' and b['entry_invocations']==1 and b['retry']==0
assert b['research_files']==0 and not list(A.rglob('research.md')) and b['cleanup']=='PASS'
assert b['failure_diagnostic']['confirmed_pages']==b['failure_diagnostic']['visible_pages']==6
assert packet['eligible_source_ids']==['S1','S2'] and packet['last_http']['status']==200 and packet['last_http']['validated_response']
assert packet['branch']=='final_before_write' and not packet['write_confirmed'] and not packet['ack_confirmed']
assert packet['budget']['native_posts']==packet['budget']['completed_posts']==7
registration=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',
    purpose='native_http_diagnostic_one_case',run_id=t['run_id'],candidate=review['candidate'],model=entry.MODEL,model_digest=entry.DIGEST,
    question_id='call_7ea1218e1bc347188fc72c160c50097a',result='FAIL',independent_review=review['verdict'],review_path=str(review_path),
    review_sha256=sha(review_path),result_manifest_sha256=sha(D/'result-manifest.json'),terminal_sha256=sha(A/'terminal.json'),
    product_result_sha256=sha(A/'product-result.json'),entry_invocations=1,work_cli_attempts=t['work_cli_attempts'],
    controlled_search_success=b['counts']['ultima_work_web_search'],controlled_GET_success=b['counts']['ultima_work_http_get'],
    confirmed_inspect_pages=6,visible_inspect_pages=6,write_attempts=0,successful_write_count=0,research_artifacts=0,
    application_native_POST_attempts=7,completed_native_posts=7,actual_native_start_count=None,
    outer_elapsed_seconds=b['outer_elapsed_seconds'],cleanup=b['cleanup'],root_witness_eligible=False,
    product_error=p['error'],failure_diagnostic_sha256=sha(A/'trusted-failure-diagnostic.raw'),failure_diagnostic_bytes=6158,
    branch=packet['branch'],eligible_source_ids=packet['eligible_source_ids'],last_http=packet['last_http'],
    selected_pages=[dict(source_id=v['source_id'],start=v['requested_start'],range=v['range'],confirmed=v['confirmed'],visible=v['visible']) for v in packet['pages']],
    budget=packet['budget'],write_confirmed=False,ack_confirmed=False,final_answer_preserved=True,
    false_completion_claim_preserved=True,facts='NOT_ASSESSABLE_NO_ARTIFACT',original_question_coverage='NOT_PASSED_NO_ARTIFACT',
    protected_at_recorded_boundaries=sha(A/'boundary-before.json')==sha(A/'boundary-after.json'),protected_after_readonly=True,
    continuous_liveness_measured=False,acceptance_credit=0,controlled_passed=0,controlled_required=3,
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,retry=0,next_case_released=False,
    E02='NOT_PASSED',T2='NOT_PASSED',Owner='NOT_PASSED',old_credit_transferred=False,remote_synced=False,
    cause='Read quota exhausted with only two card-bearing sources; final phase has no inspect/write branch and model falsely claims delivery',
    native_compatibility_limit='HTTP200 on final-only/<=256 phase does not resolve prior eligible-write/2048 HTTP500',
    recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(N/'review/result-registration.json',registration)
report=R/'docs/reports/jarvis-work-t2-e02-native-http-controlled-result-20261107.md'
proposal=R/'docs/plans/jarvis-work-e02-source-coverage-budget-proposal-20261107.md'
assert not report.exists() and proposal.exists()
report.write_text(f'''# E02 真实 HTTP 回执与研究单例结果

本轮已按明确分配完成一次当前8B受控研究和一次只读独立结果复核。研究交付FAIL，独审FAIL_CONFIRMED；新HTTP诊断链路取得真实回执。当前E02仍0/3，T2/Owner未通过，原失败及累计预算保留。

候选{registration['candidate']}，run_id {t['run_id']}，用户分配call_7ea1218e1bc347188fc72c160c50097a。入口只调用一次，外部耗时{b['outer_elapsed_seconds']:.3f}秒，retry0。原search1/GET4成功，inspect6均confirmed且visible，write0、ACK0、research.md不存在。原错误是Missing nonempty immutable runtime proof，产品没有把模型的完成话术算成交付。root witness eligible=false，短耗时不代表限时交付门通过；没有成果可逐事实和引用核验，不能记为事实审查通过。

## 本次请求回执与限制

私有v3诊断6158字节，SHA256 {sha(A/'trusted-failure-diagnostic.raw')}，公开摘要和导出摘要一致，并以原raw+request/session/task绑定校验。最后HTTP回执：第7代、第20索引、chat、HTTP200、validated_response=true、transport_failed=false；请求21600字节，SHA256 {packet['last_http']['request_sha256']}；响应有界计数441字节。共7个已完成native POST；不把应用计数冒充独立观测的原生启动次数。

按冻结源码和受信状态重建，本次最后一代处于final-only、输出上限256的相位；没有复现上一N11复杂写入相位/2048上限下的HTTP500。它证明这一次返回200并被校验，不能证明历史原生解析问题已修复或永不复现。本轮没有变更Ollama模板、请求协议、8B权重或预算。

## 可由证据与冻结源码解释的失败

六次选页为S1:26、50、74、98、122，以及S2:20，即README五页和AgentManager一页；实际只积累两个有卡来源。三来源门未满足，读取额度已用完。agent_server.py在read_count达到6后关闭inspect，在eligible不足3时不开放writer，因此依据本次状态重建出的最终schema只有拒绝用final_answer。模型在这一自由文本分支声称“已整理Jarvis.ceo桌面端的任务架构与现有开源接入的带来源文档，保存为research.md。”该说法与文件/写入回执不符；外层正确拒绝完成。

诊断时仍余247.183454秒，写入时间准入开放。当前直接可处理的缺口是选页额度没有为最少不同来源覆盖预留，以及未写入时拒绝分支仍容许不真实的完成文字。第一个缺口阻止进入写入，第二个缺口影响失败语义；两者不能靠放宽三来源门、替模型写文件或增加预算解决。来源覆盖数本身也不等于原题事实覆盖通过。

## 清理、封存与独立复核

原清理PASS、隔离端口关闭，已确认本例创建的身份不再匹配。只读后核对点2026-11-07 17:18:37–40北京时间七保护身份一致；不声称连续监测。候选工作区干净，N12/N11封存与9个无关文件逐字节保全。

结果清单60成员，SHA256 {sha(D/'result-manifest.json')}；独立结果审查SHA256 {sha(review_path)}。主会话的事后封存helper首次参数调用不符，错误源码/回执已保留，随后使用现有校验接口的raw+binding正确完成只读封存；没有重跑产品、修改实际输出或消耗第二例。独审自身不执行测试、模型或现场操作。上轮339/706离线项没有冒充本轮新测试。

## 后继处理

具体后继提案：docs/plans/{proposal.name}。优先在原SDK/JSON schema对接中联动剩余读取额度与未覆盖来源；让未交付终态明确拒绝；生成与重放保持一致。当前提案尚未实施、尚未独立计划审查，不授予新的实跑额度。仍只用当前8B，保留全部预算、三来源/事实/引用/写入/ACK门及保护进程。

本次一次运行和一次独立复核额度均已消费。没有第二例、没有自动修复或重试，未做UI/音频/生产服务操作。项目与镜像按本地提交/tag/读回收口；远端push此前被自动审批以blocked by policy拒绝，本轮不重试，remote_synced=false。

证据根：{N.as_posix()}
''',encoding='utf8',newline='\n')
pairs=[(report,M/'reports'/report.name),(proposal,M/'plans'/proposal.name)]
for source,target in pairs:
    target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists();target.write_bytes(source.read_bytes())
paths=[R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),
    R/'.superpowers/sdd/jarvis-work-e02-native-http-controlled-entry-plan-20261107/progress.md']
before={str(path):path.read_bytes() for path in paths};state=json.loads(before[str(paths[0])]);prior=state['last_actual_result']
assert prior['run_id']=='be79869f-10e5-4c0d-96a9-144cd5967c12'
state.update(phase='SOURCE23_E02_HTTP_CONTROLLED_RESULT_CONFIRMED',workflow_status='blocked',stage_queue_state='BLOCKED',
    updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),active_report=str(report),active_review_agent=None,
    last_actual_result=registration,previous_actual_result=prior,e02_native_http_controlled_execution=registration,
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    current_actual_execution=dict(run_id=t['run_id'],result='FAIL_CONFIRMED',root=str(N),entry_invocations=1,retry=0,actual_remaining=0,result_review_remaining=0),
    current_one_case_allocation=dict(question_id=registration['question_id'],candidate=registration['candidate'],status='CONSUMED_AND_REVIEWED',remaining=0,result_review_remaining=0,retry=0),
    next_action_scope=dict(authorized=True,source=str(N/'verification/allocated-user-decision.json'),scope='One current8B controlled case and one result review',status='COMPLETED',
        actual_case_allocation=0,result_review_allocation=0,retry=0),next_proposal=dict(path=str(proposal),status='PROPOSED_NOT_IMPLEMENTED',product_changes_authorized=False,actual_case_allocation=0))
summary='E02 ee1bef6单例FAIL_CONFIRMED：最后HTTP200；六页仅覆盖2来源，未开放写入，无research.md；清理PASS，单例与独审已消费，未重试，仍0/3。'
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-07 E02 HTTP controlled result confirmed\n\n'+summary+'\n报告：'+str(report)+'\n后继提案（未实施）：'+str(proposal)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
q,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=q
texts[str(paths[4])]=before[str(paths[4])].decode('utf8')+'\n- Authorized continuation COMPLETE: actual one case FAIL_CONFIRMED, one independent result review consumed, retry0, E02 0/3. Native HTTP200 in final-only phase; coverage budget exhausted at two sources. No new product changes or run authority.\n'
snap=N/'verification/result-closeout-before';snap.mkdir(exist_ok=False)
for i,path in enumerate(paths):assert path.read_bytes()==before[str(path)];(snap/(str(i)+'-'+path.name)).write_bytes(before[str(path)])
for path in paths:path.write_text(texts[str(path)],encoding='utf8',newline='\n')
save(N/'verification/result-closeout-registration.json',dict(run_id=t['run_id'],candidate=registration['candidate'],summary=summary,
    before={p:hashlib.sha256(v).hexdigest() for p,v in before.items()},after={str(p):sha(p) for p in paths},
    mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],preservation=preservation,
    result_manifest_sha256=sha(D/'result-manifest.json'),review_sha256=sha(review_path),actual_remaining=0,review_remaining=0))
print(json.dumps(dict(result='FAIL_CONFIRMED',run_id=t['run_id'],report=str(report),proposal=str(proposal),actual_remaining=0,review_remaining=0),ensure_ascii=False))
