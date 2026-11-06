"""Publish a reviewed failed attempt without running or repairing the frozen case."""
from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import subprocess

REPO=Path(r'H:\UltimaAI\UltimaAgent')
MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
N=REPO/'data/evidence/jarvis-work-capability/T2/e02-source13-real-controlled-preparation-20261107-r1'
E=N.parent/'e02-source13-root-entry-20261106'
F=N/'actual/E02-controlled-1'
TAG='ultimaagent-t2-e02-source13-real1-failed-20261107'
names={'sha','load','save_new','git','gt','checkpoint'}
nodes=[n for n in ast.parse((E/'verification/checkpoint-task1.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'retained-checkpoint-functions','exec'),globals())

base='c9d16550aaaf477991c06c1cab8ec7c74921ffb0'
mbase='6b4f701d51fc03284447bbd7dbec8bd02dbd1f7e'
assert gt(REPO,'rev-parse','HEAD')==base and gt(MIRROR,'rev-parse','HEAD')==mbase
review_path=N/'review/independent-result-review.json'
review=load(review_path)
assert review['reviewer']=='root-independent'
assert sha(review_path)=='0b21020dc84468c6fe93366756826c6c4e911bd38a10b30fd79d3ae1e9377d98'
assert review['actual_result']['overall']=='FAIL' and review['verdict']=='FAIL_CONFIRMED'
assert review['tests_run']==review['runtime_calls']==0
assert review['acceptance_credit'] is False and review['actual_run_authorized'] is False
result_path=N/'review/result-inputs/result-manifest.json'
result=load(result_path)
assert sha(result_path)=='3620d929324ef1b496e407e655e991852bb077862909efc58216e7e1c63908c0'
assert review['bindinghashes']['result_manifest']==sha(result_path)
assert review['run_id']==result['run_id']
for name,digest in result['files'].items(): assert sha(N/name)==digest,name
assert sha(Path(result['readonly_script_path']))==result['readonly_script_sha256']
for name,digest in load(N/'manifest.json')['files'].items(): assert sha(N/name)==digest,name
for name,digest in load(N/'inputs/input-manifest.json')['files'].items(): assert sha(Path(name))==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items(): assert sha(REPO/name)==digest,name
terminal=load(F/'terminal.json'); receipt=load(N/'release/tool-execution-receipt.json')
assert terminal['overall']==terminal['cleanup']['status']=='FAIL' and terminal['work_cli_attempts']==0
assert receipt['invocations']==1 and receipt['retry']==0 and receipt['exit_code']==1
assert load(N/'review/result-review-allocation.json')['consumed']==1
observation=load(N/'review/result-inputs/readonly-closeout.json')
assert observation['protected_all_equal'] and observation['listeners']=={'18799':[],'11434':[5708]}
registration_path=N/'review/result-registration.json'
registration=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',
    run_id=terminal['run_id'],candidate='269aca511d88412dbb9c15d23911138469a37aa2',model='qwen3-8b-uncensored',
    question_id=receipt['question_id'],case_result='FAIL',independent_review=review['verdict'],
    independent_review_path=str(review_path),independent_review_sha256=sha(review_path),
    result_manifest_sha256=sha(result_path),original_terminal_sha256=sha(F/'terminal.json'),
    root_outcome_sha256=sha(N/'release/root-outcome.json'),entry_invocations=1,isolated_server_launches=1,
    work_cli_attempts=0,application_native_POST_attempts=None,actual_native_start_count=None,
    research_files=0,outer_elapsed_seconds=receipt['outer_elapsed_seconds'],cleanup_status='FAIL',timing_eligible=False,
    seven_protected_equal_at_recorded_boundaries=True,seven_protected_equal_at_later_observation=True,
    continuous_protection_measured=False,retrospective_cleanup_upgrade=False,
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,retry=0,
    acceptance_credit=False,controlled_passed=0,controlled_required=3,E02='NOT_PASSED',T2='NOT_PASSED',
    next_case_released=False,remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
registration['review_disposition'] = dict(
    high_findings='Accepted as actual failure blockers; original FAIL and zero acceptance retained. No runtime repair or retry.',
    informational_findings='Later PID instance has no retrospective ownership or termination authority.',
    declined_to_judge='Absent artifact facts, transient process attribution, original descendant ownership and unmeasured inference totals remain unresolved.',
    boundary='Publication records failure only; it does not close technical blockers or release another case.')
save_new(registration_path,registration)

report=REPO/'docs/reports/jarvis-work-t2-e02-source13-real-controlled-first-result-20261107.md'
plan=REPO/'docs/plans/jarvis-work-e02-source13-child-admission-recovery-proposal-20261107.md'
report_text=f'''# E02真实研究首例：启动阶段失败，独立复核确认

原工单wo-ultimaagent-20261101-0021 / T2，产品候选269aca511d88412dbb9c15d23911138469a37aa2，仅当前qwen3-8b-uncensored。用户授权call_b6e0642029e54a15a9ca4e3452940d0a的一次入口及一次结果复核均已完成；没有重跑。E02受控通过数仍0/3，E02/T2、后续阶段与Owner均未通过；E01同候选3/3及E03三正一负已通过记录保留。

## 本次实际发生了什么

- 运行号{terminal['run_id']}；北京时间2026-11-07 00:57:22.3185703—00:57:36.6360901，外层耗时{receipt['outer_elapsed_seconds']}秒，入口退出码1。
- 已通过当前8B摘要、七个保护身份与端口准入，并启动一组隔离server的Python启动器/原生解释器。研究CLI提交次数0；没有product-result.json或research.md。因此尚未形成可交付的真实8B研究，也没有可以逐条复核的研究事实。
- 原始terminal与root-outcome均为FAIL；first_failure为clearance original discovery: Owned discovery ambiguity。首次研究调用之前，进程核验遇到PID27096的QueryFullProcessImageNameW错误31；精确PID复查时已消失，原快照却仍有其后代PID38020，故保留未知身份并拒绝继续。
- 清理结果原样保留FAIL。已登记的启动器25540、原生解释器34368及仅观察的conhost27788在清理记录中已不存在，18799关闭；这不能消除未确认后代造成的清理失败。
- 原始application_native_POST_attempts、actual_native_start_count均为null，未擅改为0。未采集全系统网络或连续存活证据。14.3秒结束不等于时限门通过，root witness eligible=false。

## 保护与独立复核

运行前后boundary字节相同，七个原生身份一致；后续只读快照再次确认原生创建时间、exe、CIM身份、parent及命令摘要一致，Ollama端口11434仍属于PID5708，本例已确认身份均无残留。后来观测到PID38020对应的Codex node_repl.exe创建于本例结束之后，属于新的PID实例，未获得本例清理权，未被结束。后续观察不追改原清理FAIL，也不声称连续监测。

独立报告：{review_path}，SHA256 {sha(review_path)}，结论{review['verdict']}。审查实际产物与证据，不另跑测试或模型；结果信用为false。

结果manifest：{result_path}，SHA256 {sha(result_path)}；准备190成员、依赖1544成员、原失败准备172成员及9项无关工作区文件读回均保持原字节。原始运行记录与独审分别保留，旧准备PASS不替代本次实际FAIL。结果登记：{registration_path}。

## 下一步及边界

下一步应处理验收框架的子进程准入/观察顺序。静态源码中，actual child在consume_clearance前调用admit→check_native_baseline→validate_protected_members→process_snapshot，后者会创建PowerShell查询；父端Owned又会拒绝原生解释器下面未登记的后代。该路径是需定点验证的设计冲突；因为本例没有保存短暂PID27096的完整身份，不能断言它就是这条PowerShell查询，也不能将问题归因于模型、音频或用户操作。

具体恢复提案见{plan}。提案不修改本封存包、不签发新实际调用；后续只能在新隔离候选补修，保持原门和全部失败。一次实跑与一次结果复核额度均0，不复用本授权。

执行端：当前root主会话；独审独立上下文。环境：原Windows、当前8B、本地受控四来源；无UI、音频或生产服务操作。只清理本例已确认的新身份；未知身份未获终止权。远端push仍受此前自动审批blocked by policy阻断，本次不重试、不绕行；仅本地提交/tag及UltimaDocs逐字镜像。
'''
with report.open('x',encoding='utf8',newline='\n') as stream: stream.write(report_text)
plan_text=f'''# E02子进程准入恢复提案（尚未分配运行权）

原单wo-ultimaagent-20261101-0021 / T2。前一轮{terminal['run_id']}的FAIL和清理FAIL、原始null计数及独审报告永久保留。本提案由真实失败及静态调用链导出，不表示补修已经完成。

## 目标和已知缺口

让当前8B受控研究能到达原产品CLI和SDK调用，并仍要求所有原验收证据。当前harness的actual child在领取父端clearance前运行进程快照辅助命令，可能与父端拒绝未知后代的规则冲突。原短暂PID缺少完整身份，具体因果仍待有界验证，不按进程名字或消失与否豁免。

## 建议的一轮有界工作

1. 创建新隔离证据候选，逐字绑定当前产品269aca5、当前8B摘要、原题四来源、原P4/P1清理helper和7保护身份；本次失败目录及全部旧记录不动。
2. 把准入责任明确分开：父端负责实时七身份、parent/命令摘要与CIM核验；actual child在clearance前仅做不生成子进程的原生身份、文件哈希、authority/clock/manifest绑定核验。子端使用父端绑定证明且仍复查当前原生身份，父端在实际CLI提交前再次核对完整保护记录。优先复用现有原生身份函数，不增加产品功能或新管理器。
3. 保留Owned对未知后代、PID复用、过期证明、漂移和清理未闭合的拒绝；不放宽身份要求，不按PowerShell/conhost名字放行，不通过加等待或删断言掩盖竞态，不延长275/310/315秒。
4. 先离线复现实际child调用链会触发额外快照命令，修正后验证准入前无subprocess；再验证同一候选/七身份、parent或命令漂移、过期/伪造clearance、PID复用、未知后代和清理失败仍拒绝。保留原测试身份，只运行受影响与必要回归；不借测试追加模型或产品实跑。
5. 源码及证据封存，做必要独立准备审查。只有新的明确范围包含实跑且审查通过时，才使用新一次性授权运行一例E02-controlled-1并做一次只读独立结果复核。失败不重试，也不更换模型或原题。

## 写域与不变量

仅新候选内harness、其离线回归、入口绑定及结果文档/原单登记/UltimaDocs镜像；冻结产品、共享P4/P1及所有旧证据不改。模型仅qwen3-8b-uncensored，14B及其他权重禁止。CLI1、search1、GET4、inspect6、write1、ACK1、nativePOST8及原时限保持，无UI、音频、生产服务操作。

## 完成判据

准备通过不能算真实研究通过。新单例必须到达真实产品首结果、原四来源及引用、SDK packet、research.md写入/ACK与两次读回、同父时钟和Owned清理，再由独审逐条核验事实。最多只增加受控1/3；其余受控及真实联网门保留。若不能以最小改动保留这些要求，停止并报告具体缺口，不扩大修复或重试。

本文件仅具体提案；当前一次实跑和一次结果独审额度已耗尽，新补修/必要独审/下一例需按用户新的明确范围推进。
'''
with plan.open('x',encoding='utf8',newline='\n') as stream: stream.write(plan_text)

status='E01同候选3/3、E03三正一负PASS；E02真实首例启动阶段FAIL，CLI0/无研究文档，清理FAIL，独立结果复核FAIL_CONFIRMED；单例与独审额度已耗尽，E02/T2未过，等待子进程准入恢复范围。'
order=REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md'
stage=REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True)
indexes=[i for i,s in enumerate(lines) if s.startswith('- 状态：')]; assert len(indexes)==1
lines[indexes[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 当前8B真实研究首例结果\n\n'+status+'\n结果报告：docs/reports/'+report.name+'。恢复提案：docs/plans/'+plan.name+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8')
stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
statepath=N.parent/'current-run.json'; state=load(statepath)
state.update(phase='SOURCE13_E02_REAL_CONTROLLED_FIRST_FAILED_REVIEWED',stage_queue_state='BLOCKED',
    workflow_status='single_case_stopped_recovery_scope_pending',goal_status='active',active_review_agent=None,
    active_preparation_root=str(N),active_report=str(report),e02='NOT_PASSED',t2='NOT_PASSED',T2='NOT_PASSED',
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    e02_real_controlled_execution=registration,e02_real_controlled_result_registration=str(registration_path),
    e02_real_controlled_result_registration_sha256=sha(registration_path),
    explicit_user_execution_status='COMPLETE_ONE_REAL_E02_ATTEMPT_AND_ONE_RESULT_REVIEW_FAIL',
    latest_readonly_runtime_receipt=str(N/'review/result-inputs/readonly-closeout.json'),
    next_action_scope=dict(scope='AWAIT_BOUNDED_CHILD_ADMISSION_RECOVERY',proposal=str(plan),
        actual_case_allocation=0,actual_result_review_allocation=0,authority_issued=False,retry=0),
    source13_next_live_admission='REQUIRES_NEW_CANDIDATE_PREPARATION_PASS_AND_USER_GRANT',
    next_action='Preserve failed case; await bounded child-admission recovery scope. No rerun under consumed allocation.',
    next_work='Repair child admission observation ordering in a separate candidate before any new real E02 case.',
    next_offline_plan=str(plan),updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
# Keep preparation-time counters historical and explicit; runtime belongs to the separate record above.
state['e02_real_controlled_preparation']['counter_scope']='Preparation only; actual execution recorded separately in e02_real_controlled_execution'
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md')
raw=registry.read_bytes(); lines=raw.decode('utf-8-sig').splitlines(keepends=True)
indexes=[i for i,s in enumerate(lines) if s.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')]; assert len(indexes)==1
lines[indexes[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+status+' |\r\n'
registry.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+''.join(lines).encode('utf8'))
generated=subprocess.run([str(REPO/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8',
    r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True,check=True)
with (N/'verification/queue-real-result.stdout').open('xb') as stream: stream.write(generated.stdout)
mirrors=[]
for source,sub in ((report,'reports'),(plan,'plans')):
    dest=MIRROR/'docs/shared/research/ultimaagent-work-capability'/sub/source.name
    assert not dest.exists(); dest.parent.mkdir(parents=True,exist_ok=True); dest.write_bytes(source.read_bytes())
    assert sha(dest)==sha(source)
    mirrors.append(dict(source=str(source),mirror=str(dest),sha256=sha(source)))
save_new(N/'verification/real-result-document-readback.json',dict(mirrors=mirrors))
ledger=Path(__file__).parent/'progress.md'
with ledger.open('a',encoding='utf8') as stream:
    stream.write('\nActual E02-controlled-1: user call_b6e0642029e54a15a9ca4e3452940d0a consumed once; run '+terminal['run_id']+' FAIL before CLI, cleanup FAIL, native counts null; independent result '+review['verdict']+' '+sha(review_path)+'. No retry. All original evidence kept; next child-admission recovery proposal is not authority.\n')
members={N/name for name in result['files']} | {result_path,review_path,registration_path,N/'review/result-review-allocation.json',
    N/'verification/reviewed-preparation-checkpoint.json',N/'verification/queue-real-result.stdout',N/'verification/real-result-document-readback.json',
    report,plan,order,stage,statepath,Path(__file__),Path(result['readonly_script_path']),ledger}
main=checkpoint(REPO,members,base,'evidence(e02): preserve failed real research attempt and independent result review')
mirror=checkpoint(MIRROR,{Path(row['mirror']) for row in mirrors},mbase,'docs: mirror E02 real-case failure and bounded recovery proposal')
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items(): assert sha(REPO/name)==digest,name
save_new(N/'verification/real-result-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,mirrors=mirrors,
    result_manifest_sha256=sha(result_path),result_review_sha256=sha(review_path),result_registration_sha256=sha(registration_path),
    actual_result='FAIL',acceptance_credit=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    runtime_authority=False,remote_synced=False,new_push_attempted=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,actual_result='FAIL',
    independent_result=review['verdict'],E02='NOT_PASSED',T2='NOT_PASSED',remote_synced=False)))
