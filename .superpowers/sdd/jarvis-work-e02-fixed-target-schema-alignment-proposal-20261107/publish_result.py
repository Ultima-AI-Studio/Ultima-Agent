"""Publish the single reviewed result; never execute a case or infer a pass."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');M=Path('H:/UltimaAI/ultima-docs-repo')
N=R/'data/evidence/jarvis-work-capability/T2/e02-fixed-target-schema-20261107-r1';F=N/'actual/E02-controlled-1'
L=R/'.superpowers/sdd/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107'
names={'sha','load','save_new','git','gt','checkpoint'}
tree=ast.parse((N.parent/'e02-source13-root-entry-20261106/verification/checkpoint-task1.py').read_bytes())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
ready=load(N/'verification/ready-checkpoint.json');base=ready['main']['commit'];mbase=ready['mirror']['commit']
assert gt(R,'rev-parse','HEAD')==base and gt(M,'rev-parse','HEAD')==mbase
reviewpath=N/'review/independent-result-review.json';review=load(reviewpath)
assert review['reviewer']=='root-independent' and review['verdict'] in ('PASS_CONTROLLED_CASE','FAIL_CONFIRMED')
assert review['tests_run']==review['runtime_calls']==0 and review['actual_run_authorized'] is False
accepted=review['verdict']=='PASS_CONTROLLED_CASE'
assert review['acceptance_credit'] is accepted and review['controlled_passed']==int(accepted)
manifestpath=N/'review/result-inputs/result-manifest.json';manifest=load(manifestpath)
assert review['result_manifest_sha256']==sha(manifestpath) and review['run_id']==manifest['run_id']
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
assert sha(Path(manifest['readonly_script_path']))==manifest['readonly_script_sha256']
for name,digest in load(N/'manifest.json')['files'].items():assert sha(N/name)==digest,name
for name,digest in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
b=load(N/'review/result-inputs/byte-readback.json');receipt=load(N/'release/tool-execution-receipt.json')
t=load(F/'terminal.json') if (F/'terminal.json').exists() else None
p=load(F/'product-result.json') if (F/'product-result.json').exists() else None
assert receipt['invocations']==1 and receipt['retry']==0
assert load(N/'review/result-review-allocation.json')['consumed']==1
if accepted:
    assert b['actual_status']=='PENDING_ROOT_INDEPENDENT_REVIEW' and b['root_witness_eligible'] is True
    assert b['product_status']=='succeeded' and b['cleanup_status']=='PASS' and len(b['artifacts'])==1
    assert b['protected_current_equal'] and b['known_original_identities_remaining']==0
    assert b['trusted_export_complete'] is True
old=Path(load(N/'inputs/predecessor.json')['root']);previous=load(old/'review/result-registration.json')
history=previous['previous_real_attempts_preserved']+[dict(run_id=previous['run_id'],candidate=previous['candidate'],result=previous['result'],cleanup=previous['cleanup'],work_cli_attempts=previous['work_cli_attempts'],application_native_POST_attempts=previous['application_native_POST_attempts'])]
TAG='ultimaagent-t2-e02-fixed-target-result-'+('pass1' if accepted else 'failed')+'-20261107'
registration=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',run_id=b['run_id'],candidate=b['candidate'],model=b['model'],question_id=receipt['question_id'],
    result='PASS_CONTROLLED_CASE' if accepted else 'FAIL',original_terminal=b['actual_status'],independent_review=review['verdict'],review_path=str(reviewpath),review_sha256=sha(reviewpath),result_manifest_sha256=sha(manifestpath),
    terminal_sha256=sha(F/'terminal.json') if t else None,product_result_sha256=sha(F/'product-result.json') if p else None,entry_invocations=1,work_cli_attempts=b['work_cli_attempts'],controlled_search_success=b['controlled_search_success'],controlled_GET_success=b['controlled_GET_success'],available_controlled_sources=b['available_sources'],
    application_native_POST_attempts=b['application_native_POST_attempts'],actual_native_start_count=b['actual_native_start_count'],research_artifacts=len(b['artifacts']),outer_elapsed_seconds=b['outer_elapsed_seconds'],cleanup=b['cleanup_status'],root_witness_eligible=b['root_witness_eligible'],
    product_status=b['product_status'],product_error=b['product_error'],research_failure=b['research_failure'],
    attribution_limit='Only the sealed current result and independent review are credited; no inference of old causes, unpublished model parameters, global native counts or continuous liveness.',
    readonly_protected_equal=b['protected_current_equal'],readonly_known_original_identities_remaining=b['known_original_identities_remaining'],continuous_liveness_measured=False,
    previous_real_attempts_preserved=history,current_controlled_passed=int(accepted),current_controlled_required=3,
    real_controlled_entry_attempts_in_sequence=previous['real_controlled_entry_attempts_in_sequence']+1,real_controlled_CLI_attempts_in_sequence=previous['real_controlled_CLI_attempts_in_sequence']+(b['work_cli_attempts'] or 0),
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,acceptance_credit=accepted,credit_scope='this candidate controlled case only',old_E01_E03_credit_transferred=False,retry=0,next_case_released=False,
    E02='NOT_PASSED',T2='NOT_PASSED',remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save_new(N/'review/result-registration.json',registration)
report=R/'docs/reports/jarvis-work-t2-e02-fixed-target-result-20261107.md'
outcome='本例受控研究通过，当前候选1/3' if accepted else '本例未通过，当前候选0/3'
diagnostic=json.dumps(b['research_failure'],ensure_ascii=False)
artifact_text='\n'.join('- '+row['path']+'；SHA256 '+row['sha256'] for row in b['artifacts']) or '没有 research.md 交付。'
text=f'''# E02固定目标schema对齐：单例结果

原工单wo-ultimaagent-20261101-0021 / T2。用户call_409cc146033c4184879042b1abac6383授权的最小补修、必要独审、一例当前8B原题四来源研究和一次独立结果复核均已完成。{outcome}；独审{review['verdict']}。E02/T2仍未通过。原单例已结束，未重试、未分配下一例。

## 交付的最小修复

候选{b['candidate']}，基于6cb9284。work_navigation.py只改一行：path保留string长度约束，增加enum:[research.md]。原writer精确目标检查及引用、事实、END、ACK、读回、目录权限和时限不变；没有改写模型响应或扩大目录授权。新增19项测试：旧schema RED12失败/7通过，新schema GREEN19，验证SDK传入native format与strict replay同一enum、错误参数派发前拒绝、合法写入/ACK/读回完整。

826项离线检查通过：产品537、harness238、输入/入口/边界51。两项原HTTP/junction集成排除不计通过。transport首轮90秒超时证据保留，原源码和原90秒上限隔离复核104通过，pytest64.48秒；不改实际研究截止。准备manifest {sha(N/'manifest.json')}，独审PASS，项目{base} / 镜像{mbase}，本地提交/tag/读回后才签发本例。

## 唯一实跑与独立复核

run {b['run_id']}；UTC {receipt['started_utc']} 至 {receipt['finished_utc']}，外层{b['outer_elapsed_seconds']}秒。原终态{b['actual_status']}，产品status={b['product_status']}，error={b['product_error']}。CLI尝试{b['work_cli_attempts']}，受控search成功{b['controlled_search_success']}、GET成功{b['controlled_GET_success']}、可用来源{b['available_sources']}；应用native POST尝试{b['application_native_POST_attempts']}。真实原生总启动计数未测量，保存为{b['actual_native_start_count']}。

安全writer诊断：{diagnostic}。不能仅凭旧失败或缺失字段推断当前/历史错误原因，具体事实和可交付性以独立结果审查为准。

{artifact_text}

结果manifest {sha(manifestpath)}（{len(manifest['files'])}成员），独审SHA256 {sha(reviewpath)}。审查原文位于{reviewpath}；审查未新增测试或产品/模型调用。

## 保护、清理和信用边界

原cleanup={b['cleanup_status']}，只读核对七个保护身份相符={b['protected_current_equal']}，已登记本例原生身份仍存在数={b['known_original_identities_remaining']}。点观察不等于连续存活；后续观察不提升原终态或旧失败。没有UI、音频或生产服务操作，没有14B、下载或更改默认模型。

原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/rootwork275/cleanup310/seal315秒保持。全部旧失败留存，旧候选269aca5的E01/E03信用不转移。当前候选受控通过{int(accepted)}/3，仍需后续同候选规定例数、真实联网及当前候选E01/E03和T2出口门；本例不等于产品总验收。

当前一次实际例及一次复核额度均0；本授权范围完成。后续例或超出本schema补修的变更没有分配。本地提交/tag及UltimaDocs镜像；远端push此前自动审批拒绝blocked by policy，本轮没有重试或绕行。
'''
with report.open('x',encoding='utf8',newline='\n') as f:f.write(text)
status='E02固定目标候选'+b['candidate'][:7]+'：826项离线/准备PASS；唯一8B例'+registration['result']+'，独审'+review['verdict']+'，当前受控'+str(int(accepted))+'/3；本范围已完成、额度0；E02/T2未过、旧信用不转移。'
order=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('- 状态：')];assert len(ix)==1;lines[ix[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 固定目标schema单例及复核完成\n\n'+status+'\n报告：docs/reports/'+report.name+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
statepath=N.parent/'current-run.json';s=load(statepath)
s.update(phase='SOURCE16_E02_FIXED_TARGET_REVIEWED_RESULT',workflow_status='authorized_single_case_scope_completed',stage_queue_state='BLOCKED',active_review_agent=None,active_report=str(report),e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    current_e02_controlled_passed=int(accepted),actual_case_allocation_remaining=0,result_review_allocation_remaining=0,last_actual_result=registration,next_action_scope=dict(authorized=False,actual_case_allocation=0,result_review_allocation=0,scope='next case or further product change not allocated'))
statepath.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
queue=Path('H:/UltimaAI/_shared/queue/global-queue-index.md');lines=queue.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(ix)==1
lines[ix[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+status+' |\n';queue.write_text(''.join(lines),encoding='utf8')
res=subprocess.run([str(R/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(N/'verification/queue-result.stdout').write_bytes(res.stdout+res.stderr);assert res.returncode==0
dst=M/'docs/shared/research/ultimaagent-work-capability/reports'/report.name;assert not dst.exists();dst.write_bytes(report.read_bytes());assert sha(dst)==sha(report)
mirrors=[dict(source=str(report),mirror=str(dst),sha256=sha(report))]
save_new(N/'verification/result-mirror-readback.json',dict(mirrors=mirrors,remote_synced=False))
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask 2 result: '+status+' Review '+sha(reviewpath)+'.\n')
    f.write('Final: Ruling: preserve reviewer limits on unmeasured global native starts, continuous protected liveness, OS packets and whole E02/T2 or transferred E01/E03 credit. Only the sealed current case is assessed; no extra run. Cost if wrong: no acceptance claim from missing evidence.\n')
paths={N/name for name in manifest['files']};paths.update({manifestpath,reviewpath,N/'review/result-review-allocation.json',N/'review/result-registration.json',N/'verification/result-mirror-readback.json',N/'verification/queue-result.stdout',N/'verification/ready-checkpoint.json',N/'verification/final-ready-readback.json',report,order,stage,statepath})
paths.update(p for p in L.iterdir() if p.is_file())
main=checkpoint(R,paths,base,'chore(e02): preserve reviewed fixed-target single-case result')
mirror=checkpoint(M,[dst],mbase,'docs(e02): mirror fixed-target single-case result')
save_new(N/'verification/result-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,result_manifest_sha256=sha(manifestpath),review_sha256=sha(reviewpath),remote_synced=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,result=review['verdict'],actual_remaining=0,review_remaining=0)))
