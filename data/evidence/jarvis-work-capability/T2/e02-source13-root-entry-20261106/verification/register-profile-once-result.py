"""Record the single failed invocation and independent evidence review; no retry."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
E=Path(__file__).resolve().parents[1];REPO=E.parents[4];MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
TAG='ultimaagent-t2-e02-source13-profile-once-fail-20261106'
BASE='585ee3d1110e0303ec59f2ad9bd70978bf81780f'
tree=ast.parse((E/'verification/checkpoint-task1.py').read_bytes())
exec(compile(ast.Module(body=[node for node in tree.body if isinstance(node,ast.FunctionDef)],type_ignores=[]),'checkpoint-functions','exec'))
def replace(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf-8',newline='\n')
review_path=E/'review/independent-profile-once-result-review.json';review=load(review_path)
manifest=load(E/'execution/result-manifest.json');readback=load(E/'execution/root-result-readback.json');run=E/'runs'/manifest['run_id']
assert review['reviewer']=='root-independent' and review['scope']=='e02-source13-profile-once-result'
assert review['verdict']=='PASS_FAILED_RESULT_PRESERVATION' and review['execution_verdict']=='FAIL'
assert review['run_id']==manifest['run_id'] and review['result_manifest_sha256']==sha(E/'execution/result-manifest.json')
for row in manifest['files']:assert sha(E/row['path'])==row['sha256'] and (E/row['path']).stat().st_size==row['bytes'],row['path']
assert load(run/'control/terminal.json')['status']=='FAIL' and load(E/'release/consumed.json')['consumed']==1
assert load(E/'execution/result-review-allocation.json')['consumed']==1
assert gt(REPO,'rev-parse','HEAD')==BASE
candidate=Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent')
assert gt(candidate,'rev-parse','HEAD')=='269aca511d88412dbb9c15d23911138469a37aa2'
assert not gt(candidate,'status','--porcelain','--untracked-files=no')
registration=E/'execution/result-registration.json'
save_new(registration,dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),run_id=manifest['run_id'],
    scope='ONE_ORIGINAL_CORPUS_ZERO_INFERENCE_PROFILE',user_question_id='call_e2d3b965cd22479087e7a5b013e77e65',
    execution_verdict='FAIL',independent_review_verdict=review['verdict'],
    result_manifest_sha256=sha(E/'execution/result-manifest.json'),review_sha256=sha(review_path),
    profile_invocations=1,root_invocations=1,reader_invocations=0,independent_result_reviews=1,
    remaining_invocations=0,remaining_result_reviews=0,retry=0,artifact_delivery='NOT_PRODUCED',
    model_inference_reached=False,model_counter_basis='traceback and reviewed pre-submission control flow; no complete profile counters',
    native_DNS_calls=None,OS_packets=None,cleanup='PASS_POINT_IN_TIME',protected_identity_matches=7,
    acceptance_credit=False,E02='NOT_PASSED',T2='NOT_PASSED',later_stages_released=False,
    independent_review_cannot_upgrade_failed_execution=True,next_runtime_authority=False,
    preflight_false_rejection='Auxiliary exact-CIM comparison corrected to unchanged original <=20 tick predicate before sole actual invocation; original source/failure retained.',
    next_scope='Proposed isolated SDK cold-import compatibility repair, new independent preparation review and separately allocated one-shot verification'))
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-profile-once-result-20261106.md'
report.write_text(f'''# E02 原资料零推理接线单例结果

原单 `wo-ultimaagent-20261101-0021`，T2。北京时间 2026-11-06 18:58，用户授权的单次接线验证已执行并结束：**FAIL**，约 **{readback['root_elapsed_seconds']:.2f} 秒**，没有重试。独立结果复核为 **{review['verdict']}**，仅确认失败证据与解释可信，不能把本例改记为通过。

## 实际执行与原因

- run_id：`{manifest['run_id']}`。root 入口 1 次、原 `run_profile` 1 次、reader 0 次、独立结果复核 1 次；本授权的运行与复核额度均已用完。
- 父进程错误：`Worker exited before complete independent progress`。worker 原始栈显示：Ollama 包导入时建立默认 `Client()`，User-Agent 调用 `platform.machine()`，Windows `platform.uname()` 读取 `socket.gethostname()`，被原 `WorkerAudit` 的广泛 socket 事件拒绝规则阻断。
- 失败发生在原 `private_scope` 尚未 yield 的初始化阶段。`run_profile` 此时原样抛出异常，因此没有 `service-first-result.json`、`profile-first-result.json`、reader 或 `research.md`。研究提交和模型推理没有到达；没有完整 profile 计数收据，不能把路径判断写成 OS 网络测量。
- 本例没有证明 8B 研究能力，也没有证明 SDK 研究写入与读回已接通。产品 source13 候选与原 profile/SDK、38 项运行输入字节均保持；此次不是 HELLO 清理余量再次不足。

## 清理、保护身份和限制

原入口清理记录 PASS：两个 worker 成员和一个只观察的控制台均消失，日志已关闭。root 后续只读核验确认这三个原身份及 root 原生身份均已不在；七个保护进程的原生创建时间、程序路径、父 PID 和命令摘要全部匹配。只证明观察时点；不扩大为持续可用、语音声学效果或整台电脑无其他活动。

没有 UI、音频或服务变更，没有模型/研究提交。原生 DNS 次数与 OS 包数未测量，保持未知。本例正常 SSRF 的允许范围原为 `raw.githubusercontent.com` 受限 DNS，但实际在更早的导入阶段退出。

预检曾因辅助脚本把 CIM 创建时间按全精度相等比较而误拒。随后核验发现七个原生身份均匹配，改为复用已审查入口原有的 `snapshot_identity_matches`（最多 20 个 FILETIME tick 的 CIM 精度差），预检通过后才执行唯一实跑。原误拒输出和脚本保留；没有放宽封存入口的生产身份规则。

## 独立复核与证据

证据根：`{E}`。

- 原始失败：`runs/{manifest['run_id']}/control/terminal.json`、`process/worker.stderr`。
- release/consumed、root 启动与退出、前后核验：`release/`、`execution/`。
- 结果包：`execution/result-manifest.json`，36 项，SHA-256 `{sha(E/'execution/result-manifest.json')}`。
- 独立结果报告：`review/independent-profile-once-result-review.json`，SHA-256 `{sha(review_path)}`。reviewer 仅只读审查，没有重跑测试、用例或原生查询。
- root 登记：`execution/result-registration.json`。准备 PASS 和原 89 项离线检查保持其原范围，不能代替本次实际 FAIL。

E01 固定 3/3、E03 同候选三正一负仍保留原通过记录；E02 真实研究、T2 出口、T3–T5 与 Owner 仍未通过。

## 下一步具体范围

见 `docs/plans/jarvis-work-e02-source13-sdk-cold-import-fix-plan-20261106.md`。建议在新隔离候选修复 SDK 冷导入兼容，精确处理本机 hostname 事件，保留其他网络拒绝与原所有权/关闭检查；先增加真实新进程冷导入回归，独立准备复核通过后才分配一次新单例和结果复核。原包及本次失败完整保留，未修改 frozen profile，未开展补修或第二次实跑。

本地项目/镜像 commit 与 tag 见 `execution/result-checkpoint.json`。远端 push 仍受此前自动审批 `blocked by policy` 阻断，本轮未重试或绕过。
''',encoding='utf-8',newline='\n')
prep=REPO/'docs/reports/jarvis-work-t2-e02-source13-root-entry-preparation-20261106.md'
with prep.open('a',encoding='utf-8',newline='\n') as stream:
    stream.write('\n## 2026-11-06 后续授权单例结果\n\n准备完成后，用户另行授权的一次原资料零推理接线验证已实际 FAIL：原 SDK 冷导入调用 socket.gethostname 被 profile 审计拒绝，尚未交付 research.md；清理和七个保护身份点时核验通过。独立结果复核仅确认失败保全，不代表执行通过。详见 `jarvis-work-t2-e02-source13-profile-once-result-20261106.md`。运行和结果复核额度均已用完，不重试。\n')
plan=REPO/'docs/plans/jarvis-work-e02-source13-sdk-cold-import-fix-plan-20261106.md'
mirrors=[]
for source in (report,prep,plan):
    dest=MIRROR/'docs/shared/research/ultimaagent-work-capability'/source.parent.name/source.name
    dest.write_bytes(source.read_bytes());assert sha(dest)==sha(source)
    mirrors.append(dict(source=str(source),mirror=str(dest),sha256=sha(source)))
save_new(E/'execution/result-document-readback.json',dict(mirrors=mirrors,exact=True,remote_synced=False))
statepath=E.parent/'current-run.json';state=load(statepath)
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE13_E02_PROFILE_ONCE_FAILED_COLD_IMPORT',
    active_report=str(report),active_review_agent=None,e02_execution_released=False,e02_zero_inference_result='FAIL',
    e02_zero_inference_result_review=review['verdict'],e02_zero_inference_result_registration=str(registration),
    e02_zero_inference_result_registration_sha256=sha(registration),e02_zero_inference_result_review_path=str(review_path),
    e02_zero_inference_result_review_sha256=sha(review_path),
    next_work='New bounded SDK cold-import compatibility repair proposal ready; previous one-shot execution and result review consumed; no retry.')
state['next_action_scope']=dict(scope='sdk_cold_import_repair_proposal_ready',approved=False,proposal=str(plan),
    actual_case_allocation=0,actual_result_review_allocation=0,authority_issued=False,retry=0,model_calls=0,audio_actions=0)
replace(statepath,state)
summary='E01固定3/3、E03三正一负PASS；E02原资料零推理单例FAIL，原SDK冷导入hostname被profile审计拒绝，未交付；失败证据独立复核通过，清理及七保护身份点时PASS。单例/复核额度均耗尽，不重试，冷导入补修提案待授权；E02/T2未过。'
cards=[REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md']
for path in cards:
    raw=path.read_bytes();ending='\r\n' if b'\r\n' in raw else '\n'
    if path==cards[0]:
        lines=raw.decode().splitlines(keepends=True)
        for i,line in enumerate(lines):
            if line.startswith('- 状态：'):lines[i]='- 状态：'+summary+ending;break
        raw=''.join(lines).encode()
    path.write_bytes(raw+('\n## 2026-11-06 E02原资料单例实际失败并独立复核保全\n\n'+summary+'\n').replace('\n',ending).encode())
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');lines=registry.read_bytes().decode().splitlines(keepends=True);matches=0
for i,line in enumerate(lines):
    if line.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |'):
        lines[i]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+summary+' |'+('\r\n' if line.endswith('\r\n') else '\n');matches+=1
assert matches==1;registry.write_bytes(''.join(lines).encode())
q=subprocess.run([str(REPO/'tools/venv-openjarvis/Scripts/python.exe'),'-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True)
for name,body in (('queue-result.stdout',q.stdout),('queue-result.stderr',q.stderr)):
    with (E/'execution'/name).open('xb') as stream:stream.write(body)
assert q.returncode==0
members={E/row['path'] for row in manifest['files']}
members.update(p for p in (E/'execution').iterdir() if p.is_file())
members.update({review_path,Path(__file__),report,prep,plan,statepath,*cards,
    E/'verification/handoff-pass-checkpoint.json',E/'verification/verify-handoff-publication.py',
    E/'verification/handoff-completion-ledger.md',E/'verification/handoff-final-readback.json',
    E/'verification/runtime-allocation-blocked-audit-20261106.json'})
foreign={name:sha(REPO/name) for name in gt(REPO,'diff','--name-only').splitlines() if REPO/name not in members}
assert foreign==load(E/'verification/handoff-pass-checkpoint.json')['unrelated_files_preserved']
main=checkpoint(REPO,members,BASE,'Preserve failed E02 zero-inference profile result and independent review')
mirror=checkpoint(MIRROR,{Path(row['mirror']) for row in mirrors},'dc2d82aeda1a98c447b4b6bd6a0dc1c2cd1ee154','Mirror E02 failed cold-import result and bounded repair proposal')
for name,digest in foreign.items():assert sha(REPO/name)==digest
for row in manifest['files']:assert sha(E/row['path'])==row['sha256'],row['path']
final=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),main=main,mirror=mirror,tag=TAG,
    run_id=manifest['run_id'],execution='FAIL',result_review=review['verdict'],
    result_manifest_sha256=sha(E/'execution/result-manifest.json'),review_sha256=sha(review_path),
    registration_sha256=sha(registration),mirrors=mirrors,unrelated_files_preserved=foreign,
    root_invocations=1,profile_invocations=1,reader_invocations=0,result_reviews=1,remaining_runtime=0,remaining_review=0,
    E02='NOT_PASSED',T2='NOT_PASSED',new_push_attempted=False,remote_synced=False)
save_new(E/'execution/result-checkpoint.json',final)
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,execution='FAIL',
    result_review=review['verdict'],root_invocations=1,retry=False,remote_synced=False)))
