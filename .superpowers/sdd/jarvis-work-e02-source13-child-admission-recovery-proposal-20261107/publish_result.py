"""Close the authorized recovery as a reviewed failure; never retries it."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
REPO=Path(r'H:\UltimaAI\UltimaAgent');MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
N=REPO/'data/evidence/jarvis-work-capability/T2/e02-source13-child-admission-20261107-r1'
E=N.parent/'e02-source13-root-entry-20261106';F=N/'actual/E02-controlled-1'
TAG='ultimaagent-t2-e02-source13-child-result-failed-20261107'
names={'sha','load','save_new','git','gt','checkpoint'}
nodes=[n for n in ast.parse((E/'verification/checkpoint-task1.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
base='2b1b8feda6b019078aec36507274e55a59d7195e';mbase='4fc0e4c43048c381e0711ca5b0e829f992228619'
assert gt(REPO,'rev-parse','HEAD')==base and gt(MIRROR,'rev-parse','HEAD')==mbase
review_path=N/'review/independent-result-review.json';review=load(review_path)
assert sha(review_path)=='3de5f47bb2e79540e46e93677610f55be4122b640e6b6552afed0fee5ef1fef4'
assert review['reviewer']=='root-independent' and review['verdict']=='FAIL_CONFIRMED'
assert review['tests_run']==review['runtime_calls']==0 and review['acceptance_credit'] is False and review['actual_run_authorized'] is False
manifest_path=N/'review/result-inputs/result-manifest.json';manifest=load(manifest_path)
assert sha(manifest_path)=='054b73280f79fb0669161442b2ee7f8e2c4c1ca4502ad6d86ac6e0aec5a69108'
assert review['result_manifest_sha256']==sha(manifest_path) and review['run_id']==manifest['run_id']
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
assert sha(Path(manifest['readonly_script_path']))==manifest['readonly_script_sha256']
for name,digest in load(N/'manifest.json')['files'].items():assert sha(N/name)==digest,name
for name,digest in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(REPO/name)==digest,name
t=load(F/'terminal.json');p=load(F/'product-result.json');receipt=load(N/'release/tool-execution-receipt.json')
assert t['overall']=='FAIL' and t['cleanup']['status']=='PASS' and t['work_cli_attempts']==1 and t['application_native_POST_attempts']==0 and t['actual_native_start_count'] is None
assert p['status']=='failed' and p['error']=='Invalid native model metadata' and not list(F.glob('outputs/**/research.md'))
assert receipt['invocations']==1 and receipt['retry']==0
assert load(N/'review/result-review-allocation.json')['consumed']==1
registration_path=N/'review/result-registration.json'
registration=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',run_id=t['run_id'],
    candidate='269aca511d88412dbb9c15d23911138469a37aa2',model='qwen3-8b-uncensored',question_id=receipt['question_id'],
    result='FAIL',independent_review='FAIL_CONFIRMED',review_path=str(review_path),review_sha256=sha(review_path),
    result_manifest_sha256=sha(manifest_path),terminal_sha256=sha(F/'terminal.json'),product_result_sha256=sha(F/'product-result.json'),
    entry_invocations=1,work_cli_attempts=1,controlled_search_success=1,controlled_GET_success=4,available_controlled_sources=4,
    application_native_POST_attempts=0,actual_native_start_count=None,research_artifacts=0,
    outer_elapsed_seconds=receipt['outer_elapsed_seconds'],cleanup='PASS',root_witness_eligible=False,
    protected_at_recorded_boundaries='SEVEN_EQUAL',readonly_after='SEVEN_EQUAL_AND_NO_KNOWN_CASE_IDENTITIES',continuous_liveness_measured=False,
    product_error=p['error'],metadata_evidence_limit='Saved root preflight has unsupported capabilities; exact product metadata GET body not exported.',
    previous_real_attempts_preserved=[dict(run_id='7530ef7f-ad0b-4151-bf2f-800c54ac9449',result='FAIL',cleanup='FAIL',work_cli_attempts=0,application_native_POST_attempts=None)],
    real_controlled_entry_attempts_in_this_two_round_sequence=2,real_controlled_CLI_attempts_in_this_two_round_sequence=1,
    current_controlled_passed=0,current_controlled_required=3,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    acceptance_credit=False,retry=0,next_case_released=False,E02='NOT_PASSED',T2='NOT_PASSED',remote_synced=False,
    review_disposition='Accept failure blockers and attribution limits; archive FAIL without retry, inference-credit or fact-credit.',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save_new(registration_path,registration)
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-child-admission-result-20261107.md'
plan=REPO/'docs/plans/jarvis-work-e02-source13-native-metadata-compat-proposal-20261107.md'
report_text=f'''# E02子进程准入恢复：启动问题已跨过，模型元数据校验失败

原单wo-ultimaagent-20261101-0021 / T2；产品269aca511d88412dbb9c15d23911138469a37aa2与当前qwen3-8b-uncensored保持。用户call_42e3d2dd124f406cb3ccebd14a9b1c0f授权的最小补修、272项离线检查、独立准备审查、一次实跑和一次独立结果复核均已完成。结果FAIL，不重跑。

## 修复及实际进展

子进程准入已拆分为子端纯原生身份核验、父端完整native/CIM/parent/命令核验；原Owned未知后代与清理规则、产品/入口及实际时限均未改。独立准备PASS已记录于ready tag，272项包括原219用例、定点17项、身份/transport10项、入口26项；完整测试超时、fixture setup失败与有效RED均保留。

新运行{t['run_id']}，北京时间2026-11-07 01:37:47.5697909—01:38:10.9598243，耗时{receipt['outer_elapsed_seconds']}秒，入口退出1。此次child-clearance已签发并唯一消费，原生成员与listener已核对，实际提交研究CLI一次。产品完成原受控search1与GET4，四来源均可用；这是受控资料流程，不是真实联网验收。

## 失败与证据边界

产品首结果status=failed，error=`Invalid native model metadata`。原始terminal FAIL，first_failure=`work: CLI nonzero; no retry`。没有research.md或交付artifact，因而没有可做逐事实引用复核的研究内容，E02信用仍0/3。

trusted-export记录application native POST attempts=0，actual native start count=null；trace中的inference_start只是业务阶段标记，不能宣称模型实际推理过。本轮尚不能评价8B研究质量。模型、默认配置与权重均未更换。

已保存的root preflight `/api/tags`中模型记录含`capabilities`；冻结产品`src/brain/work_research.py::checked_native_identity`只接受name/model/modified_at/size/digest/details，额外字段会触发同一错误。这构成可复核的静态兼容缺口。产品自己的metadata GET原始返回体未导出，因此不声称与root preflight逐字相同；具体比较见review/result-inputs/metadata-shape-readback.json。

清理PASS：四个已登记Python身份与两个仅观察conhost均已消失，18799关闭、日志关闭、无Owned歧义。运行前后七个保护身份与源文件pins相同；后续只读核对native/CIM/parent/命令摘要仍相同，11434为原Ollama PID5708。点观察不等于连续监测。root witness仍eligible=false，不用短耗时/清理PASS升级整体结果。

## 独立复核与落盘

独立结果报告{review_path}，SHA256 {sha(review_path)}，结论FAIL_CONFIRMED。结果manifest {sha(manifest_path)}（45成员）；准备130成员、1544绑定输入、前轮190准备与27结果、再前172准备保留，9项无关工作区文件保持。结果登记{registration_path}。前轮7530ef7f...的FAIL/清理FAIL绝未改写；两轮入口2、实际CLI累计1，不把前轮未提交当成功。

E01同候选3/3、E03三正一负PASS保持原归属；E02/T2、后续阶段及Owner均未通过。本轮实际与结果复核剩余额度均0。

下一步应在新产品隔离候选处理严格metadata字段兼容，具体提案{plan}。不改本冻结产品或已封存harness，不剥除真实返回字段来制造通过，不放宽模型摘要/版本/未知字段校验。新候选不得自动借用旧候选E01/E03信用。

执行端为当前root，审查为独立上下文。无UI、音频或生产服务操作，仅原题四来源与本机当前8B；没有使用14B。远端push仍受先前自动审批blocked by policy阻断，本轮仅本地提交/tag与UltimaDocs逐字镜像，无重试绕行。
'''
with report.open('x',encoding='utf8',newline='\n') as f:f.write(report_text)
plan_text='''# E02原生模型元数据兼容补修提案

原工单wo-ultimaagent-20261101-0021 / T2。子进程准入恢复例81c77cfd-9339-48b8-bae1-f67ec7d05cb4已到达产品研究CLI，受控search1/GET4通过，但在原生模型metadata校验失败。该例及前例失败保留，当前授权单例和结果复核均已完成。

## 已知缺口与目标

本次保存的root native metadata在models记录里含capabilities，产品checked_native_identity的闭合字段集合不接受它。尚未保存产品GET的原始体，不能完整归因。下一步以现有原始响应、安装版本类型定义和冻结函数为依据，完成最小严格兼容，不换模型、版本、默认配置或资料，也不在测试harness里删除真实字段来绕过产品问题。

## 有界步骤

1. 保持旧269aca5产品和全部运行记录不变，从该产品建立新隔离候选；保存当前两个失败和本轮metadata响应哈希。先对已保存响应做纯离线复现，确认具体拒绝条件，不发模型推理或运行新用例。
2. 仅在work_research.checked_native_identity及其必要测试中增加已确认的capabilities兼容，核对安装版本类型定义；保留闭合结构，错误字段类型、未知字段、错误版本、当前8B名称/摘要及本地manifest漂移仍拒绝。可增加有界、无敏感信息的诊断记录以保存失败字段名/原始体哈希，避免下次只有泛化错误；不得另建通用框架。
3. 用保存metadata的RED→GREEN以及字段/类型/摘要/版本负例验证；跑受影响的离线研究/transport回归和旧入口兼容检查。新的产品候选需重新绑定source与harness；原E01/E03信用保留在旧候选，先做影响分析与离线回归，不自动挪用，不擅自追加现场例。
4. 完成封存与必要独立准备审查、本地提交/tag及文档镜像。仅在用户新范围明确包含运行、且准备审查PASS后，实际运行一例当前8B的原题四来源受控研究，并做一次只读独立结果复核。失败不重试。

## 不变量与出口

模型仅qwen3-8b-uncensored，禁止14B及其他权重；原四来源和完整正文、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/work275/cleanup310/seal315秒、7保护身份与清理门保留。无UI、音频或生产服务操作。原生POST计数和实际推理计数分开，未测量值保持null。

只有真实首结果、SDK packet、research.md写入/ACK、两次文件读回、事实/引用逐条独审及原时限/清理全部满足，才能为新候选登记一例研究信用。E02/T2不因离线通过或metadata兼容而通过；后续受控连续三例、真实联网和同候选回归仍按原门办理。

当前文件是具体恢复提案，尚未实施产品修复，也未签发新的运行或结果复核额度。
'''
with plan.open('x',encoding='utf8',newline='\n') as f:f.write(plan_text)
status='E01同候选3/3、E03三正一负PASS；E02子进程准入补修272项/独审PASS后单例到达CLI1、受控search1/GET4，metadata校验FAIL；清理PASS、结果独审FAIL_CONFIRMED、研究0/3，原两轮失败保留，额度耗尽。'
order=REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,s in enumerate(lines) if s.startswith('- 状态：')];assert len(ix)==1
lines[ix[0]]='- 状态：'+status+'\n';append='\n## 2026-11-07 子进程恢复单例：metadata校验失败\n\n'+status+'\n报告：docs/reports/'+report.name+'。下一步：docs/plans/'+plan.name+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
statepath=N.parent/'current-run.json';s=load(statepath)
s.update(phase='SOURCE13_E02_CHILD_RECOVERY_FAILED_NATIVE_METADATA_REVIEWED',workflow_status='single_case_stopped_metadata_recovery_pending',stage_queue_state='BLOCKED',
    active_review_agent=None,active_report=str(report),goal_status='active',e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    e02='NOT_PASSED',t2='NOT_PASSED',T2='NOT_PASSED',e02_child_admission_execution=registration,
    e02_child_admission_result_registration=str(registration_path),e02_child_admission_result_registration_sha256=sha(registration_path),
    explicit_user_execution_status='COMPLETE_CHILD_ADMISSION_RECOVERY_ONE_CASE_AND_RESULT_REVIEW_FAIL',
    latest_readonly_runtime_receipt=str(N/'review/result-inputs/readonly-closeout.json'),
    next_action_scope=dict(scope='AWAIT_NATIVE_METADATA_COMPATIBILITY_RECOVERY',proposal=str(plan),actual_case_allocation=0,actual_result_review_allocation=0,authority_issued=False,retry=0),
    next_offline_plan=str(plan),next_action='Preserve both failures; prepare isolated product metadata compatibility only under next bounded recovery scope; no retry.',
    next_work='Resolve strict native metadata compatibility before evaluating current8B research generation.',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
statepath.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');raw=registry.read_bytes();lines=raw.decode('utf-8-sig').splitlines(keepends=True)
ix=[i for i,s in enumerate(lines) if s.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(ix)==1
lines[ix[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+status+' |\r\n'
registry.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+''.join(lines).encode('utf8'))
g=subprocess.run([str(REPO/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True,check=True)
with (N/'verification/queue-result.stdout').open('xb') as f:f.write(g.stdout)
mirrors=[]
for source,sub in ((report,'reports'),(plan,'plans')):
    dest=MIRROR/'docs/shared/research/ultimaagent-work-capability'/sub/source.name;assert not dest.exists()
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes());assert sha(dest)==sha(source)
    mirrors.append(dict(source=str(source),mirror=str(dest),sha256=sha(source)))
save_new(N/'verification/result-mirror-readback.json',dict(mirrors=mirrors))
ledger=Path(__file__).parent/'progress.md'
with ledger.open('a',encoding='utf8') as f:f.write('\nTask 2 result: run '+t['run_id']+' FAIL after CLI1 and controlled search1/GET4; metadata error, application POST0/native count null, cleanup PASS. Result reviewer '+sha(review_path)+' confirms FAIL. Preserve all prior failures. Current grant runtime/result allocations exhausted; no retry. Metadata product compatibility is a new proposed scope.\n')
members={N/name for name in manifest['files']}|{manifest_path,review_path,registration_path,N/'review/result-review-allocation.json',
    N/'verification/ready-checkpoint.json',N/'verification/pre-execution-readback.json',N/'verification/queue-result.stdout',N/'verification/result-mirror-readback.json',
    report,plan,order,stage,statepath,ledger,Path(__file__),Path(manifest['readonly_script_path'])}
main=checkpoint(REPO,members,base,'evidence(e02): preserve metadata rejection after successful child admission and cleanup')
mirror=checkpoint(MIRROR,{Path(row['mirror']) for row in mirrors},mbase,'docs: mirror E02 metadata failure and strict compatibility recovery proposal')
save_new(N/'verification/result-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,mirrors=mirrors,
    manifest_sha256=sha(manifest_path),review_sha256=sha(review_path),registration_sha256=sha(registration_path),
    actual_result='FAIL',cleanup='PASS',acceptance_credit=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,remote_synced=False,new_push_attempted=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,actual_result='FAIL',cleanup='PASS',application_POST_attempts=0,actual_native_start_count=None,E02='NOT_PASSED',T2='NOT_PASSED')))
