"""Register the reviewed failed single case and the concrete next diagnostic scope."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');M=Path('H:/UltimaAI/ultima-docs-repo')
N=R/'data/evidence/jarvis-work-capability/T2/e02-source13-native-metadata-20261107-r1';F=N/'actual/E02-controlled-1'
L=R/'.superpowers/sdd/jarvis-work-e02-source13-native-metadata-compat-proposal-20261107'
TAG='ultimaagent-t2-e02-native-metadata-result-failed-20261107'
names={'sha','load','save_new','git','gt','checkpoint'}
tree=ast.parse((N.parent/'e02-source13-root-entry-20261106/verification/checkpoint-task1.py').read_bytes())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
ready=load(N/'verification/ready-checkpoint.json');base=ready['main']['commit'];mbase=ready['mirror']['commit']
assert gt(R,'rev-parse','HEAD')==base and gt(M,'rev-parse','HEAD')==mbase
reviewpath=N/'review/independent-result-review.json';review=load(reviewpath)
assert review['reviewer']=='root-independent' and review['verdict']=='FAIL_CONFIRMED'
assert review['tests_run']==review['runtime_calls']==0 and review['actual_run_authorized'] is False and review['acceptance_credit'] is False
manifestpath=N/'review/result-inputs/result-manifest.json';manifest=load(manifestpath)
assert sha(manifestpath)=='4af5d17fbd6dc56a41628744b437cc6739da4a21b00c6f11ceecbdfd4f11f8f0'
assert review['result_manifest_sha256']==sha(manifestpath) and review['run_id']==manifest['run_id']
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
assert sha(Path(manifest['readonly_script_path']))==manifest['readonly_script_sha256']
for name,digest in load(N/'manifest.json')['files'].items():assert sha(N/name)==digest,name
for name,digest in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
t=load(F/'terminal.json');p=load(F/'product-result.json');receipt=load(N/'release/tool-execution-receipt.json');b=load(N/'review/result-inputs/byte-readback.json')
assert t['overall']=='FAIL' and t['cleanup']['status']=='PASS' and t['work_cli_attempts']==1 and t['application_native_POST_attempts']==5 and t['actual_native_start_count'] is None
assert p['status']=='failed' and p['error']=='Unlinked or failed END' and not list(F.glob('outputs/**/research.md')) and not p['artifacts']
failed=[row for row in p['tool_results'] if row.get('success') is False]
assert len(failed)==1 and failed[0]['tool_name']=='ultima_work_research_write' and failed[0]['error_type']=='ValueError'
assert receipt['invocations']==1 and receipt['retry']==0 and load(N/'review/result-review-allocation.json')['consumed']==1
history=[dict(run_id='7530ef7f-ad0b-4151-bf2f-800c54ac9449',candidate='269aca5',result='FAIL',cleanup='FAIL',work_cli_attempts=0,application_native_POST_attempts=None),
    dict(run_id='81c77cfd-9339-48b8-bae1-f67ec7d05cb4',candidate='269aca5',result='FAIL',cleanup='PASS',work_cli_attempts=1,application_native_POST_attempts=0)]
registration=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',run_id=t['run_id'],candidate=b['candidate'],model=b['model'],question_id=receipt['question_id'],
    result='FAIL',independent_review='FAIL_CONFIRMED',review_path=str(reviewpath),review_sha256=sha(reviewpath),result_manifest_sha256=sha(manifestpath),
    terminal_sha256=sha(F/'terminal.json'),product_result_sha256=sha(F/'product-result.json'),entry_invocations=1,work_cli_attempts=1,controlled_search_success=1,controlled_GET_success=4,available_controlled_sources=4,
    application_native_POST_attempts=5,actual_native_start_count=None,research_artifacts=0,outer_elapsed_seconds=receipt['outer_elapsed_seconds'],cleanup='PASS',root_witness_eligible=False,
    product_error=p['error'],failed_tool='ultima_work_research_write',failed_tool_error_type='ValueError',specific_write_refusal_reason='NOT_PRESERVED',
    attribution_limit='The combined END validation error does not identify the original write ValueError or establish 8B fact quality.',
    protected_at_recorded_boundaries='SEVEN_EQUAL',readonly_after='SEVEN_EQUAL_AND_NO_KNOWN_CASE_IDENTITIES',continuous_liveness_measured=False,
    previous_real_attempts_preserved=history,current_controlled_passed=0,current_controlled_required=3,real_controlled_entry_attempts_in_sequence=3,real_controlled_CLI_attempts_in_sequence=2,
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,acceptance_credit=False,old_E01_E03_credit_transferred=False,retry=0,next_case_released=False,
    E02='NOT_PASSED',T2='NOT_PASSED',remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save_new(N/'review/result-registration.json',registration)
report=R/'docs/reports/jarvis-work-t2-e02-native-metadata-result-20261107.md'
proposal=R/'docs/plans/jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107.md'
reporttext=f'''# E02元数据兼容单例：已到研究写入，写入失败

原工单wo-ultimaagent-20261101-0021 / T2。用户call_3471155e77c74b8db30c1278112c74d2授权的补修、790项离线检查、独立准备审查、一次当前8B实跑和一次只读独立结果复核已经完成。单例FAIL，不重试；E02受控0/3、T2未过。

## 已完成的修复

产品候选0a57d50f226df70542838c05fb8a21e025e19447（269aca5后继），仅既有work_research.checked_native_identity增加可省略且严格list[str]的capabilities；其余版本/名称/摘要/未知字段等检查不变。四个旧依赖按冻结哈希复制并入提交，旧候选不变。产品501项与harness/入口/边界/输入289项共790通过；准备manifest {sha(N/'manifest.json')}，690成员，独审 {sha(N/'review/independent-preparation-review.json')} PASS。两个需要本地服务/子进程的旧集成测试未计通过；早期guard/DNS/timeout及fixture失败保留。

准备已本地提交/tag及镜像：项目{base}，镜像{mbase}，tag {ready['main']['tag']}。执行前读回通过后只签发并消费一次分配，没有重复请求同一授权。

## 唯一实际结果

run {t['run_id']}；UTC {receipt['started_utc']} 至 {receipt['finished_utc']}，外层{receipt['outer_elapsed_seconds']}秒，exit1。产品CLI提交1次，原受控search1、GET4全部成功，四份完整来源可用。旧Invalid native model metadata未再出现；记录了应用层native POST attempts=5，实际原生推理总次数仍null。业务trace有五组compose inference/tool事件；这些不能替代完整原生成功计数或完整证据包。

产品首结果status=failed，error=`Unlinked or failed END`，content=`本次任务未完成。`。tool_results明确包含ultima_work_research_write的success=false、error_type=ValueError。无research.md或artifact；trusted-export complete=false、END=false。因此没有可做逐事实/引用验收的研究交付，不评价8B事实质量已达标。

只读代码定位：work_tools.py::_CapabilityTool.execute保存错误类型，但具体异常文本只进入ToolResult；随后WorkLedger.confirm_end同时检查线程、permit/seq、staged、工具成功、agent、结果和metadata，失败统一记录Unlinked or failed END。当前输出折叠了compose事件细节，也未导出失败的完整runtime packet，因此不能判断原始write ValueError具体来自字段、引用、扫描、路径或其他规则。不能凭通用错误判定模型能力或直接放宽END门。

## 清理、复核与信用边界

原始cleanup PASS；新端口18799关闭，所有本例已登记原生身份消失，无新增清理歧义。后续只读核验七个保护身份的native/CIM/parent/命令摘要全部一致，11434仍为Ollama PID5708。点观察不是连续监控；root witness eligible=false与overall FAIL保持。

结果manifest {sha(manifestpath)}（44成员）；独立结果复核{sha(reviewpath)}，FAIL_CONFIRMED。报告{reviewpath}。结果登记{N/'review/result-registration.json'}；当前实际/结果复核剩余均0。两次旧真实失败及其清理结论原样保留；此三轮入口累计3、CLI累计2，不把未提交或清理通过当成功。

旧候选269aca5的E01三轮与E03三正一负通过记录保持原归属，新候选没有这些现场回归信用。仅当前qwen3-8b-uncensored，未使用14B；没有UI、音频或生产服务操作。声线参考文件缺失提示是隔离服务导入时配置日志，不是播放/录音或修改语音服务的证据。

下一步具体方案：{proposal}。优先补齐研究write首次拒绝原因的安全有限诊断，保持END/事实门，避免继续盲跑；本轮不修改该冻结候选，也不再调用模型。

远端push仍受此前自动审批blocked by policy阻断；本轮仅本地commit/tag和UltimaDocs逐字镜像，没有重试或绕行。
'''
proposaltext='''# E02研究写入失败：有限诊断补修提案

原工单wo-ultimaagent-20261101-0021 / T2。最新0a57d50候选的唯一运行91fb07e8-91dd-4ffb-9389-fea9c02bf285已结束并经独立复核FAIL。metadata校验已跨过，原四来源预取通过，应用native POST尝试5次；研究write报ValueError，随后被通用Unlinked or failed END覆盖。没有research.md，原始具体拒绝条件未保存。此前一次运行与结果复核额度均已用完，失败不重试。

## 目标与最小写域

从0a57d50建立新隔离候选，只处理work_tools.py/work_service.py现有失败回执与必要测试，必要时在原harness的失败导出位置对接。保留writer第一次拒绝的稳定原因码、阶段与受限字段/条件状态，使一次失败足够判断具体拒绝原因；不另建研究框架、通用日志框架或重试调度。

先用当前已保存首结果和源码列出可区分失败点，用纯离线合成失败事件复现“原始writer ValueError被通用END遮蔽”。原始未知异常文本、模型完整prompt/response、来源全文或敏感字段不得直接作为新增诊断写出；采用明确允许的静态原因码、长度/类型和哈希，未知原因仍保留unknown。原始具体拒绝原因如果确实不可从旧证据还原，要明确写未知，不编造。

诊断只增加可解释的拒绝回执，不把失败END改成成功，不修改任何事实/引用/身份/字节读回门、模型参数、CLI及搜索GET/inspect/write/ACK/POST预算、原时限和保护规则。离线覆盖：writer拒绝保留最早原因、后续END通用错误不覆盖、合法END仍通过、假END/未授权/不匹配仍拒绝、敏感或任意异常文本不泄漏；保留全部旧失败和旧候选信用归属。

## 执行顺序与需要的新范围

1. 新候选内有限诊断补修，RED→GREEN及受影响离线回归，完整绑定来源。
2. 必要独立准备审查、封存、本地commit/tag及镜像。仅此准备不算研究通过。
3. 只有新授权明确包含运行且独审PASS，才再运行一次当前8B、原题、原四来源研究，并一次只读独立结果复核；失败不重试。成功仍须原SDK packet、research.md写入/ACK/两次读回、逐事实引用和原清理/时间门。

本提案尚未实施、未分配新模型调用。无UI、音频或生产服务操作，禁止14B。原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒不变。E02/T2未通过；当前新候选受控0/3，后续真实联网及同候选E01/E03等原门保留。
'''
for path,value in ((report,reporttext),(proposal,proposaltext)):
    with path.open('x',encoding='utf8',newline='\n') as f:f.write(value)
status='E02新候选0a57d50 metadata兼容已修复/790项/准备独审PASS；唯一8B例CLI1、预取search1/GET4、native POST尝试5，研究write ValueError/END失败，cleanupPASS/独审FAIL_CONFIRMED，无研究交付，0/3；本次额度耗尽，旧信用不转移。'
order=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('- 状态：')];assert len(ix)==1;lines[ix[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 metadata后继单例：write/END失败\n\n'+status+'\n结果报告：docs/reports/'+report.name+'。新范围提案：docs/plans/'+proposal.name+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
statepath=N.parent/'current-run.json';s=load(statepath);s.update(phase='SOURCE14_E02_METADATA_CASE_WRITE_FAILURE_REVIEWED',workflow_status='single_case_stopped_write_diagnostics_pending',stage_queue_state='BLOCKED',active_review_agent=None,active_report=str(report),goal_status='active',e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    current_e02_controlled_passed=0,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,last_actual_result=registration,next_action_scope=dict(proposal=str(proposal),authorized=False,actual_case_allocation=0,result_review_allocation=0,scope='new candidate bounded write failure diagnosis; not issued'))
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
    f.write('\nTask 2 result: '+status+' Review '+sha(reviewpath)+'. Root accepts FAIL_CONFIRMED and all attribution limits: original write cause not preserved, no facts artifact, no global native count or continuous liveness, no new E01/E03 credit. New diagnostic proposal is unimplemented/unreleased.\n')
paths={N/name for name in manifest['files']};paths.update({manifestpath,reviewpath,N/'review/result-review-allocation.json',N/'review/result-registration.json',N/'verification/result-mirror-readback.json',N/'verification/queue-result.stdout',N/'verification/ready-checkpoint.json',N/'verification/final-ready-readback.json',report,proposal,order,stage,statepath})
paths.update(p for p in L.iterdir() if p.is_file())
main=checkpoint(R,paths,base,'chore(e02): preserve reviewed write failure after native metadata fix')
mirror=checkpoint(M,[Path(row['mirror']) for row in mirrors],mbase,'docs(e02): mirror native metadata result and bounded write diagnostics proposal')
save_new(N/'verification/result-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,result_manifest_sha256=sha(manifestpath),review_sha256=sha(reviewpath),remote_synced=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,result='FAIL_CONFIRMED',actual_remaining=0,review_remaining=0)))
