"""Register this one plumbing result after independent review; no new runtime."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
REPO=Path(r'H:\UltimaAI\UltimaAgent');MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
T=REPO/'data/evidence/jarvis-work-capability/T2';Q=T/'e02-source13-exact-probe-20261106'
D=T/'e02-source13-closeout-handoff-20261106';E=T/'e02-source13-root-entry-20261106'
TAG='ultimaagent-t2-e02-source13-exact-probe-pass-20261106'
RUN='a47c74c4-58e7-4a63-ad7d-f63be9c17a51'
names={'sha','load','save_new','git','gt','checkpoint'}
nodes=[n for n in ast.parse((E/'verification/checkpoint-task1.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(nodes)==len(names)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
review_path=Q/'review/independent-exact-probe-result-review.json';review=load(review_path)
assert review['reviewer']=='root-independent' and review['verdict']=='PASS_ZERO_INFERENCE_PLUMBING_ONLY'
assert review['run_id']==RUN and review['runtime_authority'] is False and review['real_research_acceptance_credit'] is False
assert review['result_manifest_sha256']==sha(Q/'execution/result-manifest.json')
result_manifest=load(Q/'execution/result-manifest.json')
for row in result_manifest['files']:assert sha(Q/row['path'])==row['sha256'],row['path']
for row in load(Q/'manifest.json')['files']:assert sha(Q/row['path'])==row['sha256'],row['path']
for rel in ('entry-manifest.json','profile-preparation/manifest.json'):
    for p,digest in load(Q/rel)['files'].items():assert sha(Path(p))==digest,p
for row in load(D/'snapshot-manifest.json')['files']:
    assert sha(D/row['snapshot'])==sha(Path(row['source']))==row['sha256'],row['source']
prep=load(Q/'verification/preparation-checkpoint.json');foreign=prep['unrelated_files_preserved']
for name,digest in foreign.items():assert sha(REPO/name)==digest,name
assert gt(REPO,'rev-parse','HEAD')==prep['main']['commit'] and gt(MIRROR,'rev-parse','HEAD')==prep['mirror']['commit']
for repo in (REPO,MIRROR):assert not gt(repo,'diff','--cached','--name-only') and not gt(repo,'tag','--list',TAG)
run=Q/'runs'/RUN;terminal=load(run/'control/terminal.json');first=load(run/'worker/case/profile-first-result.json')
reader=load(run/'control/reader-result.json');audit=load(run/'worker/case/audit-expected-events.json')
post=load(Q/'execution/postcheck.json');readback=load(Q/'execution/root-result-readback.json')
assert terminal['status']=='PENDING_RESULT_REVIEW' and terminal['mechanical']=='PASS' and terminal['acceptance_credit'] is False
assert load(Q/'execution/root-exit.json')['exit_code']==0 and load(Q/'release/consumed.json')['consumed']==1
assert load(Q/'execution/scope-approval.json')['question_id']=='call_e9e5dd014d9b43f4b529f09bd2487d52'
assert first['product_status']=='succeeded' and first['status']=='candidate'
assert all(first['counters'][k] is True for k in ('audit_clean','scope_clean','eager_clean','clients_closed'))
assert audit['clean'] is True and audit['expected_probe_closed'] is True
assert audit['expected']=={'socket.__new__':1,'socket.bind':1}
assert reader['result']['status']=='candidate_mechanical_verified' and reader['result']['ack_verified'] is True
assert len(reader['observations'])==2
assert post['status']=='PASS_POINT_IN_TIME_POSTCHECK' and len(post['protected'])==len(post['owned'])==7
assert len(readback['research_artifacts'])==1
artifact=readback['research_artifacts'][0]
assert sha(Q/artifact['path'])==artifact['sha256'] and (Q/artifact['path']).stat().st_size==artifact['bytes']==711
assert load(Q/'execution/result-review-allocation.json')['review_allocation_consumed']==1
stamp=dt.datetime.now(dt.timezone.utc).isoformat();elapsed=(terminal['observed_at_ns']-terminal['origin_ns'])/1e9
registration=dict(recorded_at=stamp,run_id=RUN,execution='PASS_ZERO_INFERENCE_PLUMBING_ONLY',mechanical='PASS',
    original_terminal_status=terminal['status'],original_terminal_unchanged=True,independent_result_review=review['verdict'],
    review_path=str(review_path),review_sha256=sha(review_path),result_manifest_sha256=sha(Q/'execution/result-manifest.json'),
    root_invocations=1,profile_invocations=1,reader_invocations=1,original_readbacks=2,retry=0,
    remaining_root_invocations=0,remaining_result_reviews=0,product_status=first['product_status'],profile_status=first['status'],
    sdk_writer_successes=first['counters']['writer_successes'],mock_posts=first['counters']['native_posts'],
    mock_completions=first['counters']['native_completed'],mock_metadata_requests=first['counters']['native_metadata'],
    audit_clean=True,expected_local_probe_closed=True,artifact=artifact,root_elapsed_seconds=elapsed,
    native_DNS_calls=None,native_packet_count=None,real_model_inferences=0,actual_research_credit=0,
    cleanup='PASS',protected_point_in_time_matches=7,owned_plus_root_absent=7,
    E01='PASS_3_OF_3',E03='PASS_3_POSITIVE_AND_1_NEGATIVE',E02='NOT_PASSED',T2='NOT_PASSED',next_runtime_authority=False)
save_new(Q/'execution/result-registration.json',registration)
save_new(Q/'execution/root-result-review-disposition.json',dict(recorded_at=stamp,verdict='ACCEPT_ZERO_INFERENCE_PLUMBING_PASS',
    review_sha256=sha(review_path),result_manifest_sha256=sha(Q/'execution/result-manifest.json'),
    limitations='Mock responses establish plumbing only; real8B quality, real online research and E02/T2 remain unproven. Native DNS and OS packets unmeasured. Identity claims point-in-time.',
    runtime_authority=False,remaining_case=0,remaining_result_review=0))
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-exact-probe-result-20261106.md'
assert not report.exists()
report.write_text(f'''# E02 精确导入补修后的单例接线结果

结论：本次零推理接线验证及独立结果复核通过。一次运行、一次复核均已完成，没有重试。E02 的真实 8B 研究能力和 T2 总体验收仍未通过。

## 本次已经证明

原工单 wo-ultimaagent-20261101-0021，run {RUN}，用户授权来源 call_e9e5dd014d9b43f4b529f09bd2487d52。使用准备提交 {prep['main']['commit']}，镜像 {prep['mirror']['commit']}；673 项准备回归和独立准备 PASS 后才启动此单例。产品候选269aca5和当前社区8B保持。

根入口用时 {elapsed:.7f} 秒，退出码0、机械 PASS。原 terminal 的 PENDING_RESULT_REVIEW 和 acceptance_credit=false 保留原字节；最终接线结论另记于 result-registration.json，不修改原始结果。

- 原 SDK 实际完成一次文件写入；隔离产物 research.md 为 {artifact['bytes']} 字节，SHA-256 {artifact['sha256']}。路径：{Q/artifact['path']}。
- 启动了新的 reader，完成两次原始读回，写入、END/ACK 和产物摘要一致；reader 结果 candidate_mechanical_verified，ACK 核验通过。
- 审计干净、scope 干净、eager 干净、SDK 客户端关闭均通过。记录恰好一次本机 IPv6 socket 创建和绑定，探测 socket 已关闭；仍保留其他操作拒绝规则。
- 清理 PASS。本例6个已登记进程和根进程的原身份均在独立后检时不在；七个保护进程创建身份、exe、parent 和命令摘要匹配。该结论是点时核验，不声称持续可用性或声学复测。

## 结果复核与证据

独立报告：{review_path}，SHA-256 {sha(review_path)}，结论 PASS_ZERO_INFERENCE_PLUMBING_ONLY。

结果 manifest：{sha(Q/'execution/result-manifest.json')}，61个成员。准备 manifest 仍为 {sha(Q/'manifest.json')}，126个成员；入口47个绑定与profile的1499个依赖未漂移。旧失败和外部诊断原件全部保持，外部自审没有被追认为独立先审。

6次POST/完成、12次metadata是固定 MockTransport 的记录，真实模型推理为0。四来源由原受控资料提供；它们不能证明8B会独立研究或正确引用。原生DNS和OS全局数据包未测量，保持null。

## 下一步

按 docs/plans/jarvis-work-e02-source13-reentry-plan-20261106.md 第5步，准备当前8B的原题受控研究首例：固定题目、原四来源及候选，复用现有 SourceNavigation 和真实SDK，使用真实模型输出检查事实、引用、写入与读回。新实际推理需具体执行包和新分配，不复用本次已耗尽额度。

随后同候选受控三轮及一次真实联网流程（至少三条去重来源）按原合同完成，才可登记E02。E01三轮、E03三正一负PASS保持；T2、T3—T5及Owner门分别保留。继续仅当前8B，不采用14B或更大模型。

本地结果tag：{TAG}。项目docs与UltimaDocs镜像按同一字节提交并读回。远端push仍保留此前自动审批blocked by policy；本轮没有重试推送或改用其他通道。
''',encoding='utf-8')
status='E01固定3/3、E03三正一负PASS；E02零推理接线单例及独立复核PASS，SDK写入、新reader与两次读回闭合，22.63秒，清理及七保护身份点时PASS。单例/复核用完；下一步仅准备当前8B真实研究首例，E02/T2未过。'
order=REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
statepath=T/'current-run.json'
save_new(Q/'execution/pre-result-state.json',dict(recorded_at=stamp,current_run_sha256=sha(statepath),current_run=load(statepath)))
lines=order.read_text('utf-8').splitlines(keepends=True);matches=[i for i,s in enumerate(lines) if s.startswith('- 状态：')];assert len(matches)==1
lines[matches[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-06 精确导入单例接线和独立结果复核通过\n\n'+status+'\n报告：docs/reports/'+report.name+'。\n'
order.write_text(''.join(lines)+append,encoding='utf-8');stage.write_text(stage.read_text('utf-8')+append,encoding='utf-8')
state=load(statepath)
if 'e02_result_review' in state:state['historical_external_diagnostic_review']=state['e02_result_review']
state.update(phase='SOURCE13_E02_ZERO_INFERENCE_PLUMBING_REVIEWED_PASS',workflow_status='offline_research_preparation',stage_queue_state='EXECUTING',
    active_report=str(report),active_review_agent=None,e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    e02_zero_inference_run_id=RUN,e02_zero_inference_result='PASS_ZERO_INFERENCE_PLUMBING_ONLY',e02_zero_inference_status='PASS_ZERO_INFERENCE_PLUMBING_ONLY',
    e02_zero_inference_result_review=review['verdict'],e02_zero_inference_result_review_path=str(review_path),
    e02_zero_inference_result_review_sha256=sha(review_path),e02_zero_inference_result_registration=str(Q/'execution/result-registration.json'),
    e02_zero_inference_result_registration_sha256=sha(Q/'execution/result-registration.json'),
    e02_result_review=dict(run_id=RUN,verdict=review['verdict'],review_path=str(review_path),review_sha256=sha(review_path),real_research_acceptance_credit=False),
    e02_exact_probe_actual_runs=1,e02_exact_probe_profile_allocation=0,e02_exact_probe_result_review_allocation=0,
    e02_zero_inference_reader_invocations=1,e02_zero_inference_readbacks=2,e02='NOT_PASSED',t2='NOT_PASSED',updated_utc=stamp,
    next_work='Prepare current8B real controlled research first case under original reentry plan step5; no new actual allocation')
state['next_action_scope']=dict(scope='CURRENT8B_REAL_RESEARCH_FIRST_CASE_OFFLINE_PREPARATION',
    plan=str(REPO/'docs/plans/jarvis-work-e02-source13-reentry-plan-20261106.md'),
    actual_case_allocation=0,actual_result_review_allocation=0,authority_issued=False,model_calls=0)
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');raw=registry.read_bytes();lines=raw.decode('utf-8-sig').splitlines(keepends=True)
matches=[i for i,s in enumerate(lines) if s.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(matches)==1
lines[matches[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+status+' |\r\n'
registry.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+''.join(lines).encode('utf-8'))
generated=subprocess.run([str(REPO/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True)
for name,data in (('queue-result.stdout',generated.stdout),('queue-result.stderr',generated.stderr)):
    with (Q/'execution'/name).open('xb') as f:f.write(data)
assert generated.returncode==0
target=MIRROR/'docs/shared/research/ultimaagent-work-capability/reports'/report.name
assert not target.exists();target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(report.read_bytes());assert sha(target)==sha(report)
mirrors=[dict(source=str(report),mirror=str(target),sha256=sha(report))]
save_new(Q/'execution/result-document-readback.json',dict(mirrors=mirrors))
members={Q/r['path'] for r in result_manifest['files']}
members.update(p for p in (Q/'execution').iterdir() if p.is_file())
members.update({review_path,report,order,stage,statepath,Q/'verification/preparation-checkpoint.json',Path(__file__),
    Path(__file__).with_name('prepare_authorized_case.py'),Path(__file__).with_name('verify_result_checkpoint.py')})
main=checkpoint(REPO,members,prep['main']['commit'],'docs(e02): record independently verified zero-inference plumbing pass')
mirror=checkpoint(MIRROR,{target},prep['mirror']['commit'],'docs: mirror E02 exact-probe plumbing result')
for name,digest in foreign.items():assert sha(REPO/name)==digest,name
save_new(Q/'execution/result-checkpoint.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),main=main,mirror=mirror,tag=TAG,
    run_id=RUN,result_manifest_sha256=sha(Q/'execution/result-manifest.json'),review_sha256=sha(review_path),
    registration_sha256=sha(Q/'execution/result-registration.json'),mirrors=mirrors,unrelated_files_preserved=foreign,
    execution=registration['execution'],remaining_runtime=0,remaining_review=0,E02='NOT_PASSED',T2='NOT_PASSED',
    new_push_attempted=False,remote_synced=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,execution=registration['execution'],runtime_remaining=0)))
