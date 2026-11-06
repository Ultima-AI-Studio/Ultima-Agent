from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import subprocess

E=Path(__file__).resolve().parents[1];REPO=E.parents[4];MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
TAG='ultimaagent-t2-e02-source13-handoff-review-20261106'
BASE='a19a00b6d8cceb9784330a4b973d16942b851988'
# Reuse the previously verified exact-allowlist checkpoint functions, not its actions.
tree=ast.parse((E/'verification/checkpoint-task1.py').read_bytes())
exec(compile(ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef)],type_ignores=[]),'checkpoint-functions','exec'))
def replace(path,value):path.write_text(json.dumps(value,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
assert gt(REPO,'rev-parse','HEAD')==BASE
manifest=load(E/'manifest.json')
for row in manifest['files']:assert sha(E/row['path'])==row['sha256'],row['path']
proposal=E/'execution-proposal.md';raw=proposal.read_text(encoding='utf-8')
start=raw.index('当前状态：');end=raw.index('\n\n',start)
raw=raw[:start]+'当前状态：HELLO 清理余量交接补修已完成，89 项完整离线检查通过，正在等待当前精确源码的独立准备复核。两份旧 NEEDS_FIXES 报告保留。本提案尚无实际运行分配。'+raw[end:]
start=raw.index('- R1 修复另');end=raw.index('\n- 保留原正常 SSRF',start)
raw=raw[:start]+('- R1-followup 修复持续保留尚未登记的角色成员与未执行身份查询：启动前按预计两成员、一启动器及三次各 15 秒查询计算；启动后 HELLO 全程保留两次查询，随后逐次扣除已完成调用。原生资格确认前后均检查，实际成员增加时按更保守余量拒绝。尚待发现的控制台另预留 18 秒。已确认且无控制台的两个／四个成员仍预留 132／214 秒；新角色启动预留 195／277 秒，典型 reader 必须在 origin 后 38 秒前准入；HELLO 待确认时余量为 180／262 秒，因此通常须在 origin 后 135／53 秒前完成等待。这些更早截止可能拒绝本来内部及时的运行，不能称为完整可用的 275／310 秒。原 315 秒最大时限不变。未知树、OS 调用或文件 I/O 异常仍按失败记录，不承诺所有故障都能清理成功。')+raw[end:]
proposal.write_text(raw,encoding='utf-8',newline='\n')
for row in manifest['files']:
    if row['path']=='execution-proposal.md':row.update(bytes=proposal.stat().st_size,sha256=sha(proposal))
manifest['recorded_at']=dt.datetime.now(dt.timezone.utc).isoformat();replace(E/'manifest.json',manifest)
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-root-entry-preparation-20261106.md'
report.write_text(f'''# E02 source13 外层入口准备记录

原工单 `wo-ultimaagent-20261101-0021`，T2。当前 E01 固定样本 3/3、E03 同候选三正一负已通过；E02 真实研究、T2 出口与后续门仍未通过。

## 当前结论

用户在 `call_e84ac425972c431b843164937a72fe99` 授权同一 R1-followup 缺口的最小补修、离线验证及必要独立准备复核。补修已完成，完整离线检查 **89/89 PASS**，44.77 秒；当前精确源码独立复核待完成，准备门为 `NOT_READY_PENDING_HANDOFF_SOURCE_REVIEW`。实际 profile、模型与结果复核分配均为零。

产品候选固定 `269aca511d88412dbb9c15d23911138469a37aa2`；仅当前 `qwen3-8b-uncensored`，摘要 `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`。冻结产品工作树本次只读核验仍干净；B profile/SDK 与原 1,461 项依赖保持。当前七个保护身份仅有历史基线，本次未查询其生产运行状态。

## 补修行为与证据

此前等待循环只预留当前已知成员的清理成本。HELLO 晚到后再花两次各 15 秒身份查询，可能使余量不足；查询中才发现的解释器又会扩大清理范围。现在从启动前到资格确认完成，持续保留预计成员、启动器、未执行查询和可能的控制台观察成本。

- 原 `entry.start` 和 `NativeBackend.start/qualify` 在启动、HELLO 等待、HELLO 验证后、每次身份查询前后及句柄取得后检查余量。只有实际成员身份和只读句柄确认后才解除待确认状态。
- `Owned.cleanup`、原 `Deadline/PrivateIO` 与 275／310／315 秒截止保持；没有新增终止器。已确认无控制台的两个／四个成员仍预留 132／214 秒；新角色准入预留 195／277 秒，典型 reader 须在 origin 后 38 秒前准入。HELLO 等待保留 180／262 秒，典型等待在 origin 后 135／53 秒前结束。更保守窗口可能拒绝原本及时的消费者，不代表完整享有 275／310 秒消费时间。
- 新增 6 个 worker/reader 边界用例：安全到达、迟到、HELLO 校验期间越过边界。使用生产 start/qualify、原清理源码与真实 Deadline/PrivateIO；仅 OS 效果和时钟为合成替身。两次资格查询确实各消耗 15 秒，解释器在启动快照后才登记。检查成员消失、日志关闭、完整 10 秒终止准入及原 315 秒内最终证明。
- RED：6 项中 4 项失败、2 个安全路径通过；失败实际复现清理查询余量耗尽以及应拒绝时仍发生两次查询。修复后定向 6/6、完整 89/89。原 83 项均保留，原固定 B runner 557 项是另一份历史证据，不合并为产品验收数量。
- 本轮没有执行原生 worker/profile、模型、DNS/HTTP、窗口、音频或服务操作。离线 runner 的 Python I/O 拒绝记录为空；这不是整台电脑 OS 活动测量。任意 OS、文件阻塞或未知进程树下的无条件清理仍未获证明，5 秒文件余量只是保守余量。

## 封存及审查入口

证据根：`{E}`。

- 当前包 {len(manifest['files'])} 项，manifest SHA-256 `{sha(E/'manifest.json')}`。
- 当前运行输入 38 项，entry manifest SHA-256 `{sha(E/'entry-manifest.json')}`。
- 定向与完整收据：`offline/handoff-red`、`offline/handoff-green`、`offline/handoff-full-green`；汇总 `verification/handoff-fix-readback.json`。
- 新权限记录：`verification/handoff-fix-authorization.json`。具体成本裁定：`inputs/handoff-cleanup-ruling.json`。
- 旧 227 项、284 项包与失败报告分别完整保存在 `history/reviewed-83312d5`、`history/reviewed-a19a00b`；两份旧 NEEDS_FIXES 仍有效描述其原源码，未删除或升级为通过。
- 当前精确源码交给新 reviewer 只读审查。审查 PASS 也仅允许准备门通过；实际原资料零推理接线验证仍须按 `execution-proposal.md` 另行明确分配。它可能进行原正常 SSRF 的受限 DNS，不调用模型；即使成功也不计入 E02 真实 8B 研究三轮。

本地 commit/tag 与 UltimaDocs 镜像将在检查点收据记录。远端 push 保留此前自动审批 `blocked by policy` 阻断，本轮不重试或绕过，不宣称已同步。
''',encoding='utf-8',newline='\n')
proposal_doc=REPO/'docs/plans/jarvis-work-e02-source13-root-entry-execution-proposal-20261106.md'
proposal_doc.write_bytes(proposal.read_bytes())
plan=REPO/'docs/plans/jarvis-work-e02-source13-cleanup-handoff-fix-plan-20261106.md'
mirrors=[]
for source in (report,proposal_doc,plan):
    dest=MIRROR/'docs/shared/research/ultimaagent-work-capability'/source.parent.name/source.name
    dest.write_bytes(source.read_bytes());assert sha(source)==sha(dest)
    mirrors.append(dict(source=str(source),mirror=str(dest),sha256=sha(source)))
save_new(E/'verification/handoff-review-document-readback.json',dict(mirrors=mirrors,exact=True,remote_synced=False))
state=E.parent/'current-run.json';data=load(state)
data.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE13_E02_HANDOFF_FIXED_PREPARATION_REVIEW_PENDING',
    active_report=str(report),active_review_agent=None,preparation_status='NOT_READY_PENDING_HANDOFF_SOURCE_REVIEW',
    preparation_review='PENDING',preparation_test_count=89,e02_root_entry_tests=89,
    e02_root_entry_current_source_review='PENDING',e02_root_entry_fix='R1_FOLLOWUP_OFFLINE_VERIFIED',
    e02_root_entry_manifest_sha256=sha(E/'manifest.json'),e02_root_entry_runtime_manifest_sha256=sha(E/'entry-manifest.json'),
    next_offline_plan=str(plan),e02_execution_released=False,
    next_work='Authorized fresh independent read-only review of the sealed handoff repair; actual runtime allocation remains zero.')
data['next_action_scope']=dict(scope='authorized_same_defect_offline_repair_and_necessary_preparation_review',approved=True,
    approval_source='call_e84ac425972c431b843164937a72fe99',actual_case_allocation=0,actual_result_review_allocation=0,
    authority_issued=False,model=data['model'],audio_actions=0)
replace(state,data)
save_new(E/'review/handoff-review-assignment.json',dict(scope='e02-source13-root-entry-preparation',reviewer='root-independent',
    authority_sha256=sha(E/'verification/handoff-fix-authorization.json'),manifest_sha256=sha(E/'entry-manifest.json'),
    package_manifest_sha256=sha(E/'manifest.json'),review_limit='one fresh review for this fix; further necessary same-defect review only within explicit user scope',
    code_mutations=False,tests=False,profile=False,network=False,native_operations=False,UI=False,audio=False,
    runtime_authority=False,report_path=str(E/'review/independent-handoff-source-review.json')))
summary='E01固定3/3及E03三正一负PASS；E02 HELLO清理余量交接补修完成，89项离线检查通过，当前源码待已授权只读独立准备复核。实际profile/模型/结果复核额度0，E02/T2仍未通过。'
cards=[REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md']
for path in cards:
    raw=path.read_bytes();ending='\r\n' if b'\r\n' in raw else '\n'
    path.write_bytes(raw+('\n## 2026-11-06 E02交接补修待独立准备复核\n\n'+summary+'\n').replace('\n',ending).encode())
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');lines=registry.read_bytes().decode().splitlines(keepends=True);matches=0
for i,line in enumerate(lines):
    if line.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |'):
        lines[i]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+summary+' |'+('\r\n' if line.endswith('\r\n') else '\n');matches+=1
assert matches==1;registry.write_bytes(''.join(lines).encode())
result=subprocess.run([str(REPO/'tools/venv-openjarvis/Scripts/python.exe'),'-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True)
for suffix,body in (('stdout',result.stdout),('stderr',result.stderr)):
    with (E/f'verification/handoff-review-queue.{suffix}').open('xb') as stream:stream.write(body)
assert result.returncode==0
members={E/row['path'] for row in manifest['files']}|{E/'manifest.json',E/'entry-manifest.json',Path(__file__),
    E/'verification/handoff-review-document-readback.json',E/'review/handoff-review-assignment.json',
    E/'verification/handoff-review-queue.stdout',E/'verification/handoff-review-queue.stderr',
    E/'verification/fixed-source-review-result-checkpoint.json',state,report,proposal_doc,plan,*cards}
history=E/'history/reviewed-a19a00b'
members.update(history/row['path'] for row in load(history/'manifest.json')['files'])
members.update(history/name for name in ('manifest.json','entry-manifest.json','review/independent-fixed-source-review.json','verification/fixed-source-review-disposition.json'))
foreign={name:sha(REPO/name) for name in gt(REPO,'diff','--name-only').splitlines() if REPO/name not in members}
assert set(foreign)=={'docs/reports/jarvis-work-t2-current8b-interface-resume-20261102.md','tasks/events/wo-ultimaagent-20261101-0021-t2.jsonl','tasks/tasks.json'}
main=checkpoint(REPO,members,BASE,'Fix E02 pending qualification cleanup reservation and retain boundary evidence')
mirror=checkpoint(MIRROR,{Path(row['mirror']) for row in mirrors},'22d701c28f4bd24bb6ce43bcf78d0bfa4b5adfcc','Mirror E02 handoff repair preparation and execution boundary')
for name,digest in foreign.items():assert sha(REPO/name)==digest
for row in manifest['files']:assert sha(E/row['path'])==row['sha256']
receipt=dict(main=main,mirror=mirror,tag=TAG,manifest_sha256=sha(E/'manifest.json'),entry_manifest_sha256=sha(E/'entry-manifest.json'),
    unrelated_files_preserved=foreign,mirrors=mirrors,tests=89,actual_authority=False,remote_synced=False,new_push_attempted=False)
save_new(E/'verification/handoff-review-checkpoint.json',receipt)
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,package_files=len(manifest['files']),
    manifest=sha(E/'manifest.json'),entry_manifest=sha(E/'entry-manifest.json'),tests=89,runtime_authority=False)))
