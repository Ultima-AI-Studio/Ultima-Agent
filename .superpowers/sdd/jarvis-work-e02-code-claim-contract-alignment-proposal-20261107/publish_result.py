"""Publish only the independently reviewed single result. No runtime or retry."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');M=Path('H:/UltimaAI/ultima-docs-repo')
N=R/'data/evidence/jarvis-work-capability/T2/e02-code-claim-schema-20261107-r1';F=N/'actual/E02-controlled-1'
L=R/'.superpowers/sdd/jarvis-work-e02-code-claim-contract-alignment-proposal-20261107'
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
service_path=N/'verification/service-result-readback.json';service=load(service_path)
assert service['result_manifest_sha256']==sha(manifestpath) and service['run_id']==b['run_id']
for name,digest in service['source_files'].items():assert sha(Path(name))==digest,name
search_count=service['service_search_success'];get_count=service['service_GET_success']
available_count=service['service_available_sources'];native_posts=service['saved_export_failure_native_POST_attempts']
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
TAG='ultimaagent-t2-e02-code-claim-result-'+('pass1' if accepted else 'failed')+'-20261107'
registration=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',run_id=b['run_id'],candidate=b['candidate'],model=b['model'],question_id=receipt['question_id'],
    result='PASS_CONTROLLED_CASE' if accepted else 'FAIL',original_terminal=b['actual_status'],independent_review=review['verdict'],review_path=str(reviewpath),review_sha256=sha(reviewpath),result_manifest_sha256=sha(manifestpath),
    terminal_sha256=sha(F/'terminal.json') if t else None,product_result_sha256=sha(F/'product-result.json') if p else None,entry_invocations=1,work_cli_attempts=b['work_cli_attempts'],controlled_search_success=search_count,controlled_GET_success=get_count,available_controlled_sources=available_count,
    application_native_POST_attempts=native_posts,terminal_application_native_POST_attempts=b['application_native_POST_attempts'],actual_native_start_count=b['actual_native_start_count'],research_artifacts=len(b['artifacts']),outer_elapsed_seconds=b['outer_elapsed_seconds'],cleanup=b['cleanup_status'],root_witness_eligible=b['root_witness_eligible'],
    service_status=service['service_status'],service_error=service['service_error'],service_result_observation_path=str(service_path),service_result_observation_sha256=sha(service_path),
    activity_count_source='sealed service-first-result and trusted-export.failure observer; CLI error envelope omissions are not zero observed activity',
    product_status=b['product_status'],product_error=b['product_error'],research_failure=b['research_failure'],
    attribution_limit='Only current sealed bytes and independent review; no assumed causes, unpublished model arguments, global native counts or continuous liveness.',
    readonly_protected_equal=b['protected_current_equal'],readonly_known_original_identities_remaining=b['known_original_identities_remaining'],continuous_liveness_measured=False,
    previous_real_attempts_preserved=history,current_controlled_passed=int(accepted),current_controlled_required=3,
    real_controlled_entry_attempts_in_sequence=previous['real_controlled_entry_attempts_in_sequence']+1,real_controlled_CLI_attempts_in_sequence=previous['real_controlled_CLI_attempts_in_sequence']+(b['work_cli_attempts'] or 0),
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,acceptance_credit=accepted,credit_scope='this candidate controlled case only',old_E01_E03_credit_transferred=False,retry=0,next_case_released=False,
    E02='NOT_PASSED',T2='NOT_PASSED',remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save_new(N/'review/result-registration.json',registration)
report=R/'docs/reports/jarvis-work-t2-e02-code-claim-result-20261107.md'
outcome='本例受控研究通过，当前候选1/3' if accepted else '本例未通过，当前候选0/3'
artifacts=(('本例经复核的交付：\n' if accepted else '已落盘的候选文稿（本例失败，不作为验收交付）：\n')+'\n'.join('- '+row['path']+'；SHA256 '+row['sha256'] for row in b['artifacts'])) if b['artifacts'] else '没有 research.md 交付。'
analysis=N/'verification/result-analysis.md'
analysis_text=analysis.read_text('utf8') if analysis.exists() else '结果结论以独立复核原文为准；没有为缺失的运行信息补造归因。'
next_path=N/'verification/next-proposal-readback.json';proposal=None
if next_path.exists():
    proposed=load(next_path);proposal=Path(proposed['path']);assert proposed['implemented'] is False and sha(proposal)==proposed['sha256']
next_text=('已准备未实施后续提案：'+str(proposal)+'；没有分配新实际例。') if proposal else ('后续顺序为同候选剩余受控验证、真实联网及当前候选E01/E03与T2出口；本次授权未含下一例。' if accepted else '本例失败后当前序列结束；后续修复或新例需另行明确范围，不在本次额度内重跑。')
text=f'''# E02代码事实契约对齐：单例结果

原工单wo-ultimaagent-20261101-0021 / T2。用户call_99e734b15417466b92af3e8e85fdc3ea授权的补修、必要独审、一例当前8B原题四来源研究和一次只读独立结果复核均已完成。{outcome}；独审{review['verdict']}。E02/T2仍未通过，单例已结束，无重试和下一例分配。

## 实现与准备

候选{b['candidate']}，基于冻结a0d21eb。可信可见卡片按source/evidence/operation生成精确代码事实约束，generation和独立runtime replay重建相同schema/phase；不提前promotion、不改写模型回答。原research.md、事实/代码证据/重复来源、END/ACK/两次读回与时限门保留。新增28项产品回归，另3项使用官方b10488参考转换器核对兼容性；参考转换不代替实际原生采样证明。准备详情见jarvis-work-t2-e02-code-claim-preparation-20261107.md。

最终888项离线检查：产品594及官方转换3、harness238、绑定16/入口26/边界11。两项HTTP/junction离线排除不计通过，全部先前失败和中途测试失败保留。准备manifest {sha(N/'manifest.json')}；独审PASS后完成项目{base}/镜像{mbase}本地提交、tag和读回，才签发唯一实际例。

## 实际结果

run {b['run_id']}；UTC {receipt['started_utc']} 至 {receipt['finished_utc']}，外层{b['outer_elapsed_seconds']}秒。原终态{b['actual_status']}，CLI status={b['product_status']}，error={b['product_error']}。首次服务结果status={service['service_status']}，error={service['service_error']}。CLI尝试{b['work_cli_attempts']}；服务保存的受控search成功{search_count}、GET成功{get_count}、可用来源{available_count}；export失败观察器记录应用native POST尝试{native_posts}。原生总启动计数未测量，保存为{b['actual_native_start_count']}。

原byte-readback只读取CLI错误包，缺字段导致search/GET/available派生为0、nativePOST为null；这些不能解释为没有工作。原文件保持不变，补充只读核对service-result-readback.json（SHA{sha(service_path)}）明确两层观察并用已封存服务/导出记录纠正汇总。原终态不升级。

有限writer诊断：{json.dumps(b['research_failure'],ensure_ascii=False)}。

{analysis_text}

{artifacts}

结果manifest {sha(manifestpath)}（{len(manifest['files'])}成员）；独审{reviewpath}，SHA256 {sha(reviewpath)}。审查未运行新测试、产品或模型。

## 保护与边界

本例直接复用上一候选已独审的七身份基线，固定路径和SHA不变。本轮准备及实际前后只读核验现有身份；Ollama11464在上一轮已替代5708，启动来源仍未知，不归因于用户或本轮，也未进行服务控制。

原cleanup={b['cleanup_status']}，事后七保护身份相符={b['protected_current_equal']}，已登记本例原生身份仍存在数={b['known_original_identities_remaining']}。点观察不能证明连续存活，不提升旧终态。无UI、音频、14B、下载或生产服务操作；默认模型不变。

原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8，service260/client300/rootwork275/cleanup310/seal315秒保持。当前候选受控{int(accepted)}/3；旧269aca5的E01/E03信用不转移。当前一次运行和一次结果复核额度均0，不能宣告E02/T2/Owner总验收。

{next_text}

本轮执行裁决：保留旧候选、工作区和证据（代价为存储）；用官方支持的分组/字符类/分支表达原operation边界，既有事实门保持（长输入可能仍被原预算拒绝，不扩限）；离线准备不计真实研究信用；全局原生计数、持续存活、OS全流量及E02/T2总体验收保持未测量或未通过。初始RED、官方格式断言失败与离线命令拼写错误均保留，不计最终通过数。

远端push此前自动审批拒绝blocked by policy；本轮未重试或绕行。
'''
with report.open('x',encoding='utf8',newline='\n') as f:f.write(text)
status='E02代码事实候选'+b['candidate'][:7]+'：888项离线/准备PASS；唯一8B例'+registration['result']+'，已落盘文稿'+str(len(b['artifacts']))+'份，独审'+review['verdict']+'，当前受控'+str(int(accepted))+'/3；本范围完成、额度0；E02/T2未过、旧信用不转移。'
order=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('- 状态：')];assert len(ix)==1;lines[ix[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 代码事实契约单例及复核完成\n\n'+status+'\n报告：docs/reports/'+report.name+'。'+next_text+'\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
statepath=N.parent/'current-run.json';s=load(statepath)
s.update(phase='SOURCE18_E02_CODE_CLAIM_REVIEWED_RESULT',workflow_status='authorized_single_case_scope_completed',stage_queue_state='BLOCKED',active_review_agent=None,active_report=str(report),e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    current_e02_controlled_passed=int(accepted),actual_case_allocation_remaining=0,result_review_allocation_remaining=0,last_actual_result=registration,next_action_scope=dict(proposal=str(proposal) if proposal else None,authorized=False,actual_case_allocation=0,result_review_allocation=0,scope=next_text))
statepath.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
queue=Path('H:/UltimaAI/_shared/queue/global-queue-index.md');lines=queue.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(ix)==1
lines[ix[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+status+' |\n';queue.write_text(''.join(lines),encoding='utf8')
res=subprocess.run([str(R/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(N/'verification/queue-result.stdout').write_bytes(res.stdout+res.stderr);assert res.returncode==0
mirrors=[]
for source,folder in [(report,'reports')]+([(proposal,'plans')] if proposal else []):
    dst=M/'docs/shared/research/ultimaagent-work-capability'/folder/source.name;assert not dst.exists();dst.write_bytes(source.read_bytes());assert sha(dst)==sha(source)
    mirrors.append(dict(source=str(source),mirror=str(dst),sha256=sha(source)))
save_new(N/'verification/result-mirror-readback.json',dict(mirrors=mirrors,remote_synced=False))
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask 2 result: '+status+' Review '+sha(reviewpath)+'.\n')
    f.write('Final: Ruling: only sealed current case receives its independently reviewed credit; global native counts, continuous liveness, OS packets and E02/T2 total acceptance remain unmeasured/unpassed. Cost if wrong: no acceptance claim from missing evidence. No extra run.\n')
paths={N/name for name in manifest['files']};paths.update({manifestpath,reviewpath,N/'review/result-review-allocation.json',N/'review/result-registration.json',N/'verification/result-mirror-readback.json',N/'verification/queue-result.stdout',N/'verification/ready-checkpoint.json',N/'verification/final-ready-readback.json',report,order,stage,statepath})
paths.add(service_path)
if analysis.exists():paths.add(analysis)
proof=N/'verification/code-operation-contract-readback.json'
if proof.exists():
    static=load(proof);assert static['result_manifest_sha256']==sha(manifestpath) and static['run_id']==b['run_id']
    for name,digest in static['source_files'].items():assert sha(Path(name))==digest,name
    paths.add(proof)
if proposal:paths.update({proposal,next_path})
paths.update(p for p in L.iterdir() if p.is_file())
main=checkpoint(R,paths,base,'chore(e02): preserve reviewed code-claim single-case result')
mirror=checkpoint(M,[Path(row['mirror']) for row in mirrors],mbase,'docs(e02): mirror code-claim single-case result')
save_new(N/'verification/result-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,result_manifest_sha256=sha(manifestpath),review_sha256=sha(reviewpath),remote_synced=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,result=review['verdict'],actual_remaining=0,review_remaining=0)))
