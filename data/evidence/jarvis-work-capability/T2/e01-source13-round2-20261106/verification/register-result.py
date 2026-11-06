"""Register the independently reviewed second positive without altering raw evidence."""
from pathlib import Path
import datetime as dt
import hashlib
import json
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
REPO=Path(r'H:\UltimaAI\UltimaAgent')
MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo\docs\shared\research\ultimaagent-work-capability')
NOW=dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):return hashlib.sha256(path.read_bytes()).hexdigest()
def load(path):return json.loads(path.read_bytes())
def save(path,data):
    with path.open('x',encoding='utf-8') as f:
        json.dump(data,f,ensure_ascii=False,indent=2);f.write('\n')


a=ROOT/'actual/e01-round2';t=load(a/'terminal.json');r=load(ROOT/'review/independent-result-review.json')
prior=load(ROOT/'inputs/prior-e01-round1/registration.json');res=load(a/'product-result.json')
artifact=Path(res['artifacts'][0]['path']);readback=load(ROOT/'verification/result-content-readback.json')
post=load(ROOT/'verification/result-protected-readback.json')
rh=sha(ROOT/'review/independent-result-review.json');th=sha(a/'terminal.json')
assert rh=='a8761d3d16c434e932a9d70afd0e654534e55f4157882b92e3202cd72addd4f6'
assert r['scope']=='e01-round2-result-review' and r['case']=='e01-round2' and r['candidate']==t['candidate']
assert r['reviewer']=='root-independent' and r['independent_from_preparation_reviewer'] is True and r['findings']==[]
assert all(r[k]=='PASS' for k in ('verdict','evidence_verdict','case_verdict','mechanical_verdict','facts_verdict','file_verdict','final_claim_verdict','cleanup_verdict','environment_verdict'))
assert r['target_verdict']=='NOT_APPLICABLE' and r['ui_target_scope']=='NOT_APPLICABLE_E01_NO_UI'
assert r['terminal_sha256']==th and r['product_result_sha256']==sha(a/'product-result.json')
assert r['preparation_manifest_sha256']==sha(ROOT/'manifest.json') and r['result_evidence_manifest_sha256']==sha(ROOT/'verification/result-evidence-manifest.json')
assert r['artifact_sha256']==readback['artifact_sha256']==sha(artifact)
assert r['no_new_facts']['verdict']=='PASS' and r['recommendation']['acceptance_credit_recommended'] is True
assert r['recommendation']['current_case_positive_credit']==1 and r['recommendation']['eligible_cumulative_e01_positives_after_root_registration']==2
assert r['execution']['task_id']==res['task_id'] and r['execution']['work_cli_launches']==1
assert r['execution']['completed_inference_end_events']==2 and r['execution']['automatic_retry_recorded'] is False
assert t['overall']=='PENDING_FACT_REVIEW' and t['acceptance_credit'] is False and t['errors']==[]
assert post['status']=='PASS_POINT_IN_TIME_POSTCHECK'
assert prior['positive_passed']==1 and prior['candidate']==t['candidate'] and prior['facts']=='PASS'
assert prior['task_id']!=res['task_id']
old=prior['same_candidate_e01_terminal_bindings'];assert len(old)==1
assert dt.datetime.fromisoformat(old[0]['finished_at'])<dt.datetime.fromisoformat(t['finished_at'])
for name in ('manifest.json','verification/result-evidence-manifest.json'):
    for row in load(ROOT/name)['files']:
        p=ROOT/row['path'];assert sha(p)==row['sha256'] and p.stat().st_size==row['bytes'],str(p)
binding=dict(case='e01-round2',candidate=t['candidate'],terminal_sha256=th,review_sha256=rh,task_id=res['task_id'],
    finished_at=t['finished_at'],case_verdict='PASS',work_cli_count=1,completed_inference_events=2,artifact_sha256=sha(artifact))
registration=dict(recorded_at=NOW,controller='root',scope='E01_CURRENT_CANDIDATE_POSITIVE_CHAIN',case='e01-round2',
    candidate=t['candidate'],candidate_manifest_sha256=r['candidate_runtime_manifest_sha256'],
    preparation_manifest_sha256=r['preparation_manifest_sha256'],result_manifest_sha256=r['result_evidence_manifest_sha256'],
    terminal_sha256=th,result_review_sha256=rh,product_result_sha256=r['product_result_sha256'],
    artifact_sha256=sha(artifact),artifact_path=str(artifact),task_id=res['task_id'],case_verdict='PASS',facts='PASS',
    delivery='PASS',final_claim='PASS',cleanup='PASS',environment='PASS_AT_SAVED_CASE_BOUNDARY_AND_POSTCHECK',
    target='NOT_APPLICABLE_NO_UI',acceptance_credit=True,E01_credit=1,positive_passed=2,positive_required=3,
    same_candidate_e01_terminals=2,cumulative_work_cli_count=2,current_case_work_cli_count=1,
    cumulative_completed_inference_events=4,current_case_completed_inference_events=2,actual_native_start_count=None,
    same_candidate_e01_terminal_bindings=old+[binding],
    predecessor_registration_sha256=sha(ROOT/'inputs/prior-e01-round1/registration.json'),
    consecutive_positive_cases=['e01-round1','e01-round2'],E01='PARTIAL_2_OF_3',E03='PASS_CURRENT_CANDIDATE_FIXED_CORPUS',
    E03_prerequisite_registration_sha256=prior['E03_prerequisite_registration_sha256'],qualified_E03_work_cli_count=3,
    qualified_E03_completed_inference_events=9,raw_terminal_overall=t['overall'],raw_terminal_acceptance_credit=False,
    actual_case_count=1,independent_result_reviews=1,remaining_actual_case_cap=0,remaining_result_review_cap=0,
    next_live_authority_issued=False,T2='NOT_PASSED',E02='NOT_PASSED',goal_complete=False)
save(ROOT/'verification/result-registration.json',registration)
save(ROOT/'verification/result-review-disposition.json',dict(recorded_at=NOW,controller='root',
    decision='ACCEPT_CURRENT_CASE_PASS_REGISTER_E01_2_OF_3',review_sha256=rh,regrading={'Critical':0,'Important':0,'Minor':0},
    decline_dispositions=[dict(item=x,ruling='ACCEPT_SCOPE_LIMIT',effect='No broader acceptance or future/runtime claim') for x in r['declined_to_judge']],
    original_terminal_unchanged=True,next_execution_authorized=False,T2='NOT_PASSED'))
save(ROOT/'verification/result-review-completion.json',dict(recorded_at=NOW,agent=r['agent_identity'],review_sha256=rh,
    case='e01-round2',allocated=1,completed=1,remaining=0,verdict='PASS',next_review_authorized=False))
report=REPO/'docs/reports/jarvis-work-t2-e01-source13-round2-result-20261106.md'
assert not report.exists()
report.write_text(f'''# E01 source13 round2实际文件交付结果

原工单wo-ultimaagent-20261101-0021；冻结候选{t['candidate']}。用户授权的一次E01 round2和一次只读独立结果复核均已完成，当前8B保持。实际交付、独立事实/文件/最终声明/清理复核PASS，无发现，已登记E01同候选连续正例2/3；E01整体及T2尚未通过。

任务ID：{res['task_id']}。本轮实际文件：{artifact}；85字节，SHA-256 {sha(artifact)}。全文为三段原材料，分别说明项目代号松林、交付形式Markdown文档、截止日期2026年11月8日。独审确认三事实完整且无新增事实；版式与前轮不同符合原契约。实际SDK写入、服务端读回、外部读回和当前原始字节一致，最终回复给出本轮真实绝对路径。

本轮一次真实工作CLI、一次成功SDK文件写入、两条完成的inference_end事件，无重试。原生总启动数/未完成数保持null，断连后是否继续生成保持unknown；两条tool_results是同一调用的SDK摘要和ledger，不能计两次写入。没有窗口、音频或真实记忆操作。

原proof60秒/authority120秒和CLI300/SDK1800/controller315保持。独审根据原生FILETIME核对CLI提交时proof年龄21.1872549秒、authority年龄21.0629219秒。本次入口耗时约46.69秒，包含检查及清理，不作为开放任务或语音延迟指标。

机械终态{t['finished_at']}；cleanup/audit/boundaries均PASS。root只读后查{post['recorded_at']}至{post['finished_at']}确认6本例原身份消失、隔离端口49988关闭、7保护身份匹配、Ollama0.32.15与当前8B摘要匹配、官方语音ready/fresh及原身份/run_id一致。仅为保存时点证据，不代表连续/未来可用或音频功能验收；未重启服务或额外推理。

准备manifest69文件SHA {r['preparation_manifest_sha256']}；结果manifest44文件SHA {r['result_evidence_manifest_sha256']}。原terminal SHA {th}；product-result SHA {r['product_result_sha256']}；独立reviewer {r['agent_identity']}，review SHA {rh}；root登记SHA {sha(ROOT/'verification/result-registration.json')}。原terminal仍保持PENDING_FACT_REVIEW、facts=PENDING_ROOT_INDEPENDENT_REVIEW和credit=false，事实复核及credit在独立收据与root登记中另记。

252项离线检查仅为此前准备证据，实际后未重跑；产品57源码/7依赖/1346 SDK绑定保持。前轮E01与E03原记录、旧实际失败、旧环境故障和所有离线RED均保留。6项未裁定范围由root接受，无新增实际或结果复核额度。

下一步仅按docs/plans/jarvis-work-e01-source13-round3-plan-20261106.md继续同候选第3轮离线准备；不授予第3轮实跑或结果复核，E02/T2出口/T3—T5/Owner原门保持。项目与UltimaDocs本地结果tag为ultimaagent-t2-e01-source13-round2-result-20261106；精确提交及字节读回见verification/result-local-checkpoint.json。

远端push此前被自动审批以blocked by policy拒绝，本轮未重试或换通道；本地留档和实际验收不等于远端同步。
''',encoding='utf-8')
plan=REPO/'docs/plans/jarvis-work-e01-source13-round3-plan-20261106.md';assert plan.is_file()
mirrors=[]
for p,folder in ((report,'reports'),(plan,'plans')):
    target=MIRROR/folder/p.name
    if target.exists():assert target.read_bytes()==p.read_bytes()
    else:target.write_bytes(p.read_bytes())
    mirrors.append(dict(source=str(p),mirror=str(target),sha256=sha(p)))
save(ROOT/'verification/result-document-mirror-readback.json',dict(recorded_at=NOW,mirrors=mirrors,byte_identical=True))
state=ROOT.parent/'current-run.json';s=load(state)
s.update(phase='SOURCE13_E01_ROUND2_COMPLETE_ROUND3_OFFLINE_PLAN_READY',updated_at=NOW,active_review_agent=None,
    active_report=str(report),e01_current_candidate_positive_passed=2,e01_current_result_review='PASS',
    e01_current_review_path=str(ROOT/'review/independent-result-review.json'),e01_current_review_sha256=rh,
    e01_current_result_registration=str(ROOT/'verification/result-registration.json'),
    e01_current_result_registration_sha256=sha(ROOT/'verification/result-registration.json'),
    e01_current_result_review_remaining=0,e01_execution_released=False,live_gate_released=False,next_stage_released=False,
    explicit_user_execution_status='COMPLETE_E01_ROUND2_AND_ONE_RESULT_REVIEW',blocking_condition=None,
    next_offline_plan=str(plan),e01_last_completed_case='e01-round2',
    latest_readonly_runtime_receipt=str(ROOT/'verification/result-protected-readback.json'),
    latest_readonly_runtime_sha256=sha(ROOT/'verification/result-protected-readback.json'))
s['next_action_scope']=dict(scope='same-candidate-e01-round3-offline-preparation',actual_case_allocation=0,
    actual_result_review_allocation=0,authority_issued=False,product_model_calls=0,audio_actions=0,
    candidate=t['candidate'],plan=str(plan))
state.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
status='当前269aca5与当前8B的E03三正例3/3及负例1/1已PASS；E01 round2实际文件交付和独立事实复核PASS，同候选连续正例2/3。本次CLI1/完成推理事件2/SDK写入1，6本例身份清理与7保护身份保存后查通过；单例与一次复核已耗尽，下一步round3离线准备，T2/E02及后续原门保持。'
wo=REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';lines=wo.read_text(encoding='utf-8').splitlines()
assert sum(x.startswith('- 状态：') for x in lines)==1
append=f'\n\n## 2026-11-06 E01 round2实际与独立事实复核PASS\n\n{status}\n\n报告：docs/reports/{report.name}。独审SHA {rh}；登记SHA {sha(ROOT/"verification/result-registration.json")}。下一步计划docs/plans/{plan.name}仅允许离线准备；原始terminal及全部旧失败保持。\n'
wo.write_text('\n'.join('- 状态：'+status if x.startswith('- 状态：') else x for x in lines).rstrip()+append,encoding='utf-8')
stage=REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md';stage.write_text(stage.read_text(encoding='utf-8').rstrip()+append,encoding='utf-8')
queue=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');ql=queue.read_text(encoding='utf-8').splitlines();needle='| UltimaAgent | wo-ultimaagent-20261101-0021 |'
assert sum(x.startswith(needle) for x in ql)==1
queue.write_text('\n'.join(needle+' executing | '+status+' |' if x.startswith(needle) else x for x in ql)+'\n',encoding='utf-8')
q=subprocess.run([sys.executable,'-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True,text=True,encoding='utf-8')
save(ROOT/'verification/result-queue-refresh.json',dict(recorded_at=NOW,exit_code=q.returncode,stdout=q.stdout,stderr=q.stderr,scope='Original0021 only; generated aggregate is registration, not live count'))
assert q.returncode==0
assert sha(a/'terminal.json')==th
print(json.dumps({'registration_sha256':sha(ROOT/'verification/result-registration.json'),'E01':'2/3','review':'PASS','mirrors':len(mirrors),'next_actual_allocation':0,'T2':'NOT_PASSED'}))
