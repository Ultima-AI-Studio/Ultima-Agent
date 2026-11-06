from pathlib import Path
import datetime as dt,hashlib,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-source13-native-metadata-20261107-r1';N=T/'e02-native-write-diagnostics-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-write-diagnostics/UltimaAgent');PY=R/'tools/venv-openjarvis/Scripts/python.exe'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(json.dumps(v,ensure_ascii=False,indent=2)+'\n')
assert not N.exists() and subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip()=='0a57d50f226df70542838c05fb8a21e025e19447'
assert not subprocess.check_output(['git','status','--porcelain'],cwd=C)
subprocess.run(['git','switch','-c','codex/jarvis-e02-write-diagnostics'],cwd=C,check=True)
for name in ('inputs','harness','code','tests','verification','offline','review'):(N/name).mkdir(parents=True,exist_ok=False)
files=['harness/'+p.name for p in (OLD/'harness').iterdir() if p.is_file()]
files+=['code/'+x for x in ('entry.py','bindings.py')]
files+=['tests/'+p.name for p in (OLD/'tests').glob('*.py')]
files+=['inputs/'+x for x in ('input-manifest.json','scope.json','unrelated-working-tree.json')]
files+=['verification/'+x for x in ('offline_pytest.py','run_entry_checks.py','run_boundary_checks.py','run_binding_checks.py','product_pytest.py','run_product_checks.py')]
for name in files:
    raw=(OLD/name).read_bytes()
    if name in ('verification/product_pytest.py','verification/run_product_checks.py'):
        raw=raw.replace(b'jarvis-e02-native-metadata',b'jarvis-e02-write-diagnostics')
    (N/name).write_bytes(raw)
save(N/'inputs/copy-origin.json',dict(source=str(OLD),files={name:sha(OLD/name) for name in files}))
save(N/'inputs/granted-scope.json',dict(source='user_explicit',question_id='call_948abbc3ba2948a9b3441d57051d9b27',answer='授权诊断补修、独审，通过后单例研究并复核（推荐）',
    conditional_actual_case_allocation=1,result_review_allocation=1,retry=0,preparation_review='necessary_independent',product_base='0a57d50f226df70542838c05fb8a21e025e19447',product_root=str(C),
    model='qwen3-8b-uncensored',no_UI=True,no_audio=True,no_production_service_operations=True,old_credit_transferred=False,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat()))
save(N/'inputs/predecessor.json',dict(root=str(OLD),manifest_sha256=sha(OLD/'manifest.json'),result_manifest_sha256=sha(OLD/'review/result-inputs/result-manifest.json'),
    result_review_sha256=sha(OLD/'review/independent-result-review.json'),three_failures_preserved=['7530ef7f-ad0b-4151-bf2f-800c54ac9449','81c77cfd-9339-48b8-bae1-f67ec7d05cb4','91fb07e8-91dd-4ffb-9389-fea9c02bf285']))
save(N/'inputs/state-before.json',json.loads((T/'current-run.json').read_bytes()))
save(N/'inputs/diagnosis-readback.json',dict(source_files={str(C/'src/brain'/name):sha(C/'src/brain'/name) for name in ('work_tools.py','work_service.py')},
    observed_failed_tool='ultima_work_research_write',observed_error_type='ValueError',specific_historical_cause='UNKNOWN',
    corrected_mechanism='_CapabilityTool.execute records error and error_type in WorkLedger; WorkService final research projection keeps only error_type and drops error.',
    proposed_minimum='Expose a fixed bounded diagnostic from the first failed trusted research-write record before final projection; no END or first_failure control-flow changes.',new_runtime_calls=0,new_tests=0))
plan=R/'docs/plans/jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107.md'
with plan.open('a',encoding='utf8',newline='\n') as f:f.write('''
## 2026-11-07 已授权接续与归因纠正

用户call_948abbc3ba2948a9b3441d57051d9b27已授权本补修、必要独审、通过后一例研究及一次结果复核，失败不重试。当前不再请求同一范围。

只读复核进一步明确：_CapabilityTool.execute已将error及error_type写入WorkLedger.record；真正丢失详细原因的位置是WorkService最终研究回执的字段裁剪。上份结果报告“文本只进入ToolResult”不准确，已追加勘误；旧实际失败及SHA不改。优先只改work_service.py输出有限原因码，尽量不改work_tools/END校验。

## Task 1: 有限写入诊断与离线准备

新隔离候选基于0a57d50。真实SDK离线fixture复现writer拒绝后仅剩通用END错误；从可信ledger首个失败writer记录导出封闭原因码/阶段/有限类型，未知文本不直接落盘。与旧status/error/END拒绝行为并存，不放宽成功门，不相信SDK/model伪造的tool_results诊断。验证最早原因、后续END遮蔽、未知/敏感文本不泄漏、合法路径和拒绝门；相关离线回归、候选重绑、封存独审及本地commit/tag/镜像。

## Task 2: 审查通过后的单例与结果复核

准备独审PASS和提交读回后签发一次TTL120秒分配，原题四来源当前8B跑一例，失败不重试。保留实际首结果/有限原因码/证据/清理及保护身份，做一次只读独立复核，按实情登记研究信用并提交/tag/镜像。原E02/T2与同候选其他现场门不得借用旧信用。

## Review Focus

只从可信ledger选择最早writer失败；稳定诊断与任意异常/模型文本严格隔离；新增数据不能成为成功判据或改变END拒绝顺序；原schema/API成功与失败行为、模型/预算/时限/保护身份不变；新候选来源绑定与旧失败完整保留。
''')
prior_report=R/'docs/reports/jarvis-work-t2-e02-native-metadata-result-20261107.md'
with prior_report.open('a',encoding='utf8',newline='\n') as f:f.write('''
## 2026-11-07 后续只读勘误（不改原运行结论）

原文“具体异常文本只进入ToolResult”表述不准确。_CapabilityTool.execute同时将error字符串和error_type写入ledger记录；WorkService.submit_work在最终研究回执中仅保留error_type，裁剪掉error。现存落盘材料仍不能还原具体write拒绝原因。该纠正只说明丢失位置，FAIL/清理PASS/POST尝试5/null原生总数及独审结论不变。
''')
status='原T2/E02：已授权新候选补有限writer失败诊断；丢失点定位为最终回执字段裁剪，旧三次失败保留。准备独审PASS后仅一例当前8B原题四来源及结果复核，当前未释放。'
order=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('- 状态：')];assert len(ix)==1;lines[ix[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 writer有限诊断授权接续\n\n'+status+'\n方案：docs/plans/'+plan.name+'。证据：'+str(N)+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
s=json.loads((T/'current-run.json').read_bytes());s.update(phase='SOURCE15_E02_WRITE_DIAGNOSTICS_OFFLINE_PREPARATION',workflow_status='authorized_bounded_write_diagnostics_preparation',stage_queue_state='EXECUTING',active_review_agent=None,goal_status='active',e02_execution_released=False,live_gate_released=False,next_stage_released=False,active_evidence=str(N),active_plan=str(plan),active_candidate_root=str(C),actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    next_action_scope=dict(question_id='call_948abbc3ba2948a9b3441d57051d9b27',conditional_actual_case_allocation=1,conditional_result_review_allocation=1,authority_issued=False,retry=0))
(T/'current-run.json').write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
queue=Path('H:/UltimaAI/_shared/queue/global-queue-index.md');lines=queue.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(ix)==1
lines[ix[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+status+' |\n';queue.write_text(''.join(lines),encoding='utf8')
r=subprocess.run([str(PY),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(N/'verification/queue-preparation.stdout').write_bytes(r.stdout+r.stderr);assert r.returncode==0
print(json.dumps(dict(new_root=str(N),product_root=str(C),copied=len(files),registered=True),ensure_ascii=False))
