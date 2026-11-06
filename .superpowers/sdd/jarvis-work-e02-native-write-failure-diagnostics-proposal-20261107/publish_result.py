"""Publish the reviewed failed case and an unimplemented target-contract proposal."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');M=Path('H:/UltimaAI/ultima-docs-repo')
N=R/'data/evidence/jarvis-work-capability/T2/e02-native-write-diagnostics-20261107-r1';F=N/'actual/E02-controlled-1'
L=R/'.superpowers/sdd/jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107'
TAG='ultimaagent-t2-e02-write-diagnostics-result-failed-20261107'
names={'sha','load','save_new','git','gt','checkpoint'}
tree=ast.parse((N.parent/'e02-source13-root-entry-20261106/verification/checkpoint-task1.py').read_bytes())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
ready=load(N/'verification/ready-checkpoint.json');base=ready['main']['commit'];mbase=ready['mirror']['commit']
assert gt(R,'rev-parse','HEAD')==base and gt(M,'rev-parse','HEAD')==mbase
reviewpath=N/'review/independent-result-review.json';review=load(reviewpath)
assert review['reviewer']=='root-independent' and review['verdict']=='FAIL_CONFIRMED'
assert review['tests_run']==review['runtime_calls']==0 and review['actual_run_authorized'] is False and review['acceptance_credit'] is False
manifestpath=N/'review/result-inputs/result-manifest.json';manifest=load(manifestpath)
assert sha(manifestpath)=='831775760a93d02b39250f1044964dfa149ae79d01a43e898c8f1731cb34bf47'
assert review['result_manifest_sha256']==sha(manifestpath) and review['run_id']==manifest['run_id']
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
assert sha(Path(manifest['readonly_script_path']))==manifest['readonly_script_sha256']
for name,digest in load(N/'manifest.json')['files'].items():assert sha(N/name)==digest,name
for name,digest in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
t=load(F/'terminal.json');p=load(F/'product-result.json');receipt=load(N/'release/tool-execution-receipt.json');b=load(N/'review/result-inputs/byte-readback.json')
assert t['overall']=='FAIL' and t['cleanup']['status']=='PASS' and t['work_cli_attempts']==1 and t['application_native_POST_attempts']==5 and t['actual_native_start_count'] is None
assert p['status']=='failed' and p['error']=='Unlinked or failed END' and not list(F.glob('outputs/**/research.md')) and not p['artifacts']
diag=p['research_failure'];assert diag==b['research_failure']==load(F/'service-first-result.json')['research_failure']
assert diag['reason_code']=='INVALID_TARGET' and diag['error_type']=='ValueError' and diag['error_text_length']==35
assert diag['error_text_sha256']==hashlib.sha256(b'Research target must be research.md').hexdigest()
assert receipt['invocations']==1 and receipt['retry']==0 and load(N/'review/result-review-allocation.json')['consumed']==1
old=Path(load(N/'inputs/predecessor.json')['root']);previous=load(old/'review/result-registration.json')
history=previous['previous_real_attempts_preserved']+[dict(run_id=previous['run_id'],candidate=previous['candidate'],result=previous['result'],cleanup=previous['cleanup'],work_cli_attempts=previous['work_cli_attempts'],application_native_POST_attempts=previous['application_native_POST_attempts'])]
registration=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',run_id=t['run_id'],candidate=b['candidate'],model=b['model'],question_id=receipt['question_id'],
    result='FAIL',independent_review='FAIL_CONFIRMED',review_path=str(reviewpath),review_sha256=sha(reviewpath),result_manifest_sha256=sha(manifestpath),
    terminal_sha256=sha(F/'terminal.json'),product_result_sha256=sha(F/'product-result.json'),entry_invocations=1,work_cli_attempts=t['work_cli_attempts'],controlled_search_success=b['controlled_search_success'],controlled_GET_success=b['controlled_GET_success'],available_controlled_sources=b['available_sources'],
    application_native_POST_attempts=t['application_native_POST_attempts'],actual_native_start_count=t['actual_native_start_count'],research_artifacts=0,outer_elapsed_seconds=receipt['outer_elapsed_seconds'],cleanup='PASS',root_witness_eligible=False,
    product_error=p['error'],failed_tool='ultima_work_research_write',failed_tool_error_type='ValueError',research_failure=diag,specific_write_refusal_reason='path parameter is not the exact literal research.md',exact_submitted_path='UNKNOWN_NOT_EXPORTED',
    attribution_limit='Current diagnostic proves the target equality rejection; no raw submitted path, old-run cause, or research fact quality is inferred.',
    protected_at_recorded_boundaries='SEVEN_EQUAL',readonly_after='SEVEN_EQUAL_AND_NO_KNOWN_CASE_IDENTITIES',continuous_liveness_measured=False,
    previous_real_attempts_preserved=history,current_controlled_passed=0,current_controlled_required=3,
    real_controlled_entry_attempts_in_sequence=previous['real_controlled_entry_attempts_in_sequence']+1,real_controlled_CLI_attempts_in_sequence=previous['real_controlled_CLI_attempts_in_sequence']+t['work_cli_attempts'],
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,acceptance_credit=False,old_E01_E03_credit_transferred=False,retry=0,next_case_released=False,
    E02='NOT_PASSED',T2='NOT_PASSED',remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save_new(N/'review/result-registration.json',registration)
report=R/'docs/reports/jarvis-work-t2-e02-write-diagnostics-result-20261107.md'
proposal=R/'docs/plans/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107.md'
proposed=load(N/'verification/next-proposal-readback.json');assert sha(proposal)==proposed['sha256'] and proposed['implemented'] is False
text=f'''# E02诊断单例：定位固定文件目标不匹配，研究仍未通过

原工单wo-ultimaagent-20261101-0021 / T2。用户call_948abbc3ba2948a9b3441d57051d9b27授权的诊断补修、必要独审、单例研究及一次结果复核均已完成。本次FAIL，经独立复核FAIL_CONFIRMED；没有research.md，E02受控0/3，T2仍未通过，未重试。

## 已交付的诊断修复

候选{b['candidate']}基于0a57d50，隔离工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-write-diagnostics/UltimaAgent。只改work_service.py与诊断测试：从可信ledger首个失败writer记录导出固定原因码、阶段、类型、长度与受限哈希。未知文本不导出；不从SDK/model tool_results取诊断。原status/error及END/事实/引用/文件核验门保持。

有效RED14失败/3通过，GREEN17；产品518项加harness/入口/输入/边界289项，共807项离线检查通过。两项本地HTTP/junction集成不在本离线范围、不计通过；首次Unicode用例预期纠正及两份RED证据保留。准备manifest {sha(N/'manifest.json')}（410成员），独审 {sha(N/'review/independent-preparation-review.json')} PASS。准备项目{base}，镜像{mbase}，tag {ready['main']['tag']}；已提交后读回才签发单例。

## 唯一实际结果与原因

run {t['run_id']}；UTC {receipt['started_utc']} 至 {receipt['finished_utc']}，外层{receipt['outer_elapsed_seconds']}秒、exit1。CLI1，受控search1/GET4成功，4份来源可用。应用native POST尝试5，真实原生总推理计数未测量、保持null。

产品status=failed，主错误仍为Unlinked or failed END，未报告完成。新诊断research_failure.reason_code=INVALID_TARGET、stage=research.write、error_type=ValueError；长度35、SHA256 {diag['error_text_sha256']}与源码固定消息Research target must be research.md一致。它定位到work_tools.py::WorkResearchWriteTool.run中params.get('path')!='research.md'，发生在resolve_v3引用/事实解析之前。

实际传入path字节未导出，不能称其为绝对路径或猜测值；前轮91fb07e8的具体原因仍未知，不能追溯认定相同。没有研究文件/完整runtime packet，不能评价事实质量已经合格或笼统归因为8B能力不足。当前只证实本次文件目标拒绝。

只读源码另确认接口不一致：v3_writer_schema向模型声明path为任意非空、最长2048字符string，writer却只接受字面值research.md。阶段提示已说Write only research.md once。下一步最小修复是收紧现有JSON Schema path enum为[research.md]，与原writer目标一致；不放宽路径授权、不改写模型输出或原生证据。本轮未实施该改动，具体提案{proposal}。

## 清理、复核和信用边界

原cleanup PASS；后续只读核对七个保护身份native/CIM/parent/命令摘要相符，本例已登记原生身份均不再存在；18799无监听，11434仍PID5708。点观察不等于连续存活监测，不追溯提升任何旧失败。记录范围无UI、音频或生产服务操作；没有切换模型或使用14B。

结果manifest {sha(manifestpath)}（44成员），独立结果复核 {sha(reviewpath)}，FAIL_CONFIRMED。实际/结果复核额度均0。此前三次实际失败完整保留；该序列累计入口4、CLI3均来自各次登记，不将清理或离线通过算研究成功。旧候选269aca5的E01/E03信用不转移到新候选。

原时限与CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8保持。后续schema补修和新单例需新明确范围；当前序列已结束，原项目目标仍未完成。远端push仍受此前自动审批blocked by policy阻断，本轮仅本地commit/tag和UltimaDocs镜像，无重试或绕行。
'''
with report.open('x',encoding='utf8',newline='\n') as f:f.write(text)
status='E02诊断候选6cb9284/807项/准备独审PASS；唯一8B例FAIL，定位INVALID_TARGET（path非字面research.md），cleanupPASS/结果独审FAIL_CONFIRMED，无交付/0/3；额度耗尽，schema对齐提案待新范围，旧信用不转移。'
order=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('- 状态：')];assert len(ix)==1;lines[ix[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 诊断单例：固定文件目标拒绝\n\n'+status+'\n报告：docs/reports/'+report.name+'。新范围提案：docs/plans/'+proposal.name+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
statepath=N.parent/'current-run.json';s=load(statepath);s.update(phase='SOURCE15_E02_WRITE_DIAGNOSTICS_INVALID_TARGET_REVIEWED',workflow_status='single_case_stopped_target_schema_proposal_pending',stage_queue_state='BLOCKED',active_review_agent=None,active_report=str(report),goal_status='active',e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    current_e02_controlled_passed=0,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,last_actual_result=registration,next_action_scope=dict(proposal=str(proposal),authorized=False,actual_case_allocation=0,result_review_allocation=0,scope='new candidate fixed-target schema alignment; not issued'))
statepath.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
queue=Path('H:/UltimaAI/_shared/queue/global-queue-index.md');lines=queue.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(ix)==1
lines[ix[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+status+' |\n';queue.write_text(''.join(lines),encoding='utf8')
res=subprocess.run([str(R/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(N/'verification/queue-result.stdout').write_bytes(res.stdout+res.stderr);assert res.returncode==0
mirrors=[]
for src,folder in ((report,'reports'),(proposal,'plans')):
    dst=M/'docs/shared/research/ultimaagent-work-capability'/folder/src.name;assert not dst.exists();dst.write_bytes(src.read_bytes());assert sha(dst)==sha(src)
    mirrors.append(dict(source=str(src),mirror=str(dst),sha256=sha(src)))
save_new(N/'verification/result-mirror-readback.json',dict(mirrors=mirrors,remote_synced=False))
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask 2 result: '+status+' Review '+sha(reviewpath)+'.\n')
    f.write('Final: Ruling: observed target rejection is established by matching source code, public/service result and fixed-message hash; actual submitted path, old cause and fact quality remain unknown. Cost if wrong: no path/value/quality claim or research credit beyond available evidence.\n')
    f.write('Final: Ruling: accept readonly reviewer limits on global native count, continuous protected liveness, OS-level absence, and new E01/E03 or full E02/T2 acceptance. Preserve null/unpassed and point-observation attribution; no additional run. Cost if wrong: cannot claim product acceptance from incomplete evidence.\n')
paths={N/name for name in manifest['files']};paths.update({manifestpath,reviewpath,N/'review/result-review-allocation.json',N/'review/result-registration.json',N/'verification/result-mirror-readback.json',N/'verification/queue-result.stdout',N/'verification/ready-checkpoint.json',N/'verification/final-ready-readback.json',N/'verification/target-contract-readback.json',N/'verification/next-proposal-readback.json',report,proposal,order,stage,statepath})
paths.update(p for p in L.iterdir() if p.is_file())
main=checkpoint(R,paths,base,'chore(e02): preserve reviewed invalid-target failure and schema alignment proposal')
mirror=checkpoint(M,[Path(row['mirror']) for row in mirrors],mbase,'docs(e02): mirror writer diagnostics result and fixed-target proposal')
save_new(N/'verification/result-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,result_manifest_sha256=sha(manifestpath),review_sha256=sha(reviewpath),remote_synced=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,result='FAIL_CONFIRMED',actual_remaining=0,review_remaining=0)))
