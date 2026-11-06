"""Publish independently reviewed offline evidence without issuing a runtime grant."""
from pathlib import Path
import ast, datetime as dt, hashlib, json, subprocess

REPO=Path(r'H:\UltimaAI\UltimaAgent')
MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
T=REPO/'data/evidence/jarvis-work-capability/T2'
Q=T/'e02-source13-exact-probe-20261106'
D=T/'e02-source13-closeout-handoff-20261106'
E=T/'e02-source13-root-entry-20261106'
TAG='ultimaagent-t2-e02-source13-exact-probe-ready-20261106'
HEAD='9d2b5eae90507edec70f13ebe43578aba628aec6'
MIRROR_HEAD='5cc368f834e74c118b6ee43ce6fd769c3d624c55'
names={'sha','load','save_new','git','gt','checkpoint'}
tree=ast.parse((E/'verification/checkpoint-task1.py').read_bytes())
nodes=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(nodes)==len(names)
exec(compile(ast.Module(body=nodes,type_ignores=[]),'retained-checkpoint-functions','exec'),globals())

review_path=Q/'review/independent-preparation-review.json'
review=load(review_path)
assert review['verdict']=='PASS' and review['reviewer']=='root-independent'
assert review['scope']=='e02-source13-root-entry-preparation' and review['runtime_authority'] is False
assert review['manifest_sha256']==sha(Q/'entry-manifest.json')
assert review['package_manifest_sha256']==sha(Q/'manifest.json')
assert not any(str(f.get('severity','')).lower() in ('critical','important','p0','p1') and str(f.get('status','open')).lower() not in ('resolved','closed') for f in review.get('findings',[]))
for row in load(Q/'manifest.json')['files']:
    assert sha(Q/row['path'])==row['sha256'],row['path']
for rel in ('entry-manifest.json','profile-preparation/manifest.json'):
    for p,digest in load(Q/rel)['files'].items():assert sha(Path(p))==digest,p
for row in load(D/'snapshot-manifest.json')['files']:
    assert sha(D/row['snapshot'])==sha(Path(row['source']))==row['sha256'],row['source']
foreign=load(D/'inputs/unrelated-working-tree.json')['files']
for name,digest in foreign.items():assert sha(REPO/name)==digest,name
assert not (Q/'release').exists() and not (Q/'runs').exists()
assert load(Q/'verification/offline-readback.json')['verdict']=='PASS_OFFLINE_PREPARATION_ONLY'
assert gt(REPO,'rev-parse','HEAD')==HEAD and gt(MIRROR,'rev-parse','HEAD')==MIRROR_HEAD
for repo in (REPO,MIRROR):
    assert not gt(repo,'diff','--cached','--name-only') and not gt(repo,'tag','--list',TAG)
candidate=Path(load(Q/'profile-preparation/manifest.json')['candidate_root'])
assert gt(candidate,'rev-parse','HEAD')=='269aca511d88412dbb9c15d23911138469a37aa2'
assert not gt(candidate,'status','--porcelain','--untracked-files=no')
stamp=dt.datetime.now(dt.timezone.utc).isoformat()
gate=dict(recorded_at=stamp,verdict='PASS_PREPARATION_ONLY',manifest_sha256=sha(Q/'entry-manifest.json'),
    package_manifest_sha256=sha(Q/'manifest.json'),review_sha256=sha(review_path),actual_authority=False,
    profile_tests=584,root_tests=89,actual_profile_allocation=0,result_review_allocation=0)
save_new(Q/'verification/code-preparation-gate.json',gate)
save_new(Q/'verification/root-review-disposition.json',dict(recorded_at=stamp,verdict='ACCEPT_PREPARATION_PASS',
    report_sha256=sha(review_path),findings_disposition=review.get('findings',[]),
    limits='Offline preparation only. Prior external self-review remains diagnostic; old consumed allocations remain consumed. A new actual case and independent result review require a new explicit allocation.',
    reviewed_manifest_unchanged=True,actual_authority=False,E02='NOT_PASSED',T2='NOT_PASSED'))

plan=REPO/'docs/plans/jarvis-work-e02-source13-exact-probe-repair-plan-20261106.md'
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-exact-probe-preparation-20261106.md'
assert not report.exists()
report.write_text(f'''# E02 精确 IPv6 导入兼容补修：准备通过

原工单 wo-ultimaagent-20261101-0021，T2。当前状态：离线修复与独立准备审查 PASS；新的完整接线验证尚未运行。E01 同候选固定样本 3/3、E03 三正一负通过记录保留，E02 真实研究和 T2 仍未通过。模型继续只用当前社区 8B，产品候选仍为 269aca511d88412dbb9c15d23911138469a37aa2。

## 实际改动

已确认原 SDK 依赖 urllib3 在首次导入时调用 _has_ipv6("::1")。新的验证 profile 只允许固定源码、真实函数和模块初始化调用链中的 AF_INET6 / SOCK_STREAM / protocol 0 创建，随后允许同一 socket 一次绑定到 (::1, 0)。其他来源、地址、端口、重复创建/绑定、connect 等仍拒绝并留下记录；未完成关闭不能判为干净退出。SDK/vendor 和产品源码未改。

保留外部诊断中有效的 SDK 事件 JSON 键序修正和写入/读回事实。外部包 c794f6fd-3c87-4965-a612-4617d9f64783 虽有机械 PASS，但执行者自审、外层清单 8 项漂移，不能追认独立先审或计作 E02 研究验收。71 份原件已逐项快照核对；外部报告承认删除过早期离线失败目录，本次只记录缺口，不声称已恢复。新的 RED 和全部失败记录均保留。

## 验证和审查

- profile 584/584，原 566 个测试身份全部保留，新增 18 项精确探测检查；其中两条原宽泛例外测试按精确契约更新。
- 根入口 89/89，原测试身份及 275/310/315 秒截止、保护身份和清理规则保留。合计 673 项，定向子集不重复计数。
- RED 真实暴露 16 项缺口；全新进程的原 urllib3 探测验证关闭前不干净、关闭后干净。原 SDK worker/reader 两条真实冷导入回归保留。
- 独立准备审查：PASS，报告 {review_path}，SHA-256 {sha(review_path)}。
- entry manifest：{sha(Q/'entry-manifest.json')}，47 个绑定。
- profile 依赖清单：{sha(Q/'profile-preparation/manifest.json')}，1499 个绑定，包含安装版本 urllib3 的 36 个 Python 源文件。
- 稳定准备包 manifest：{sha(Q/'manifest.json')}，126 个成员；审查、发布、运行结果与缓存另存，未改封存包。独审后逐项读回零漂移。

## 下一例与授权边界

具体命令和范围见 {Q/'execution-proposal.md'}。下一例保留原题、四来源、零推理 MockTransport、限定 SSRF DNS、原截止及七个保护身份核验；不操作 UI、音频或服务。仅一例，失败不重试，随后一次只读独立结果复核。当前候选尚无 release/runs，实际调用和结果复核分配均为 0。

用户 call_c6b188dbc9514611ad330bb3b8829619 所授权的一例已用于旧候选 run 726b5883-f57c-4693-899e-17c9d1719b22，该例 FAIL 且独立失败保全复核已完成。本次准备没有复用该单例或外部诊断分配。下一次完整接线验证需新的明确分配。

零推理通过也只证明接线，不能代替当前 8B 的真实研究与真实联网验收。T3—T5 和 Owner 门不提前放行。

本地准备 tag：{TAG}。项目及 UltimaDocs 镜像将按同一文本提交并读回。远端 push 仍受此前自动审批 blocked by policy 阻断，本轮没有重试或改用其他通道。
''',encoding='utf-8')
status='E01固定3/3、E03三正一负PASS；E02精确IPv6导入补修完成，584项profile和89项入口检查及独立准备审查PASS。旧失败及外部自审诊断保留；新单例与结果复核待分配，E02/T2未过。'
order=REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md'
stage=REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
statepath=T/'current-run.json'
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md')
before={str(p):dict(sha256=sha(p),text=p.read_text('utf-8-sig')) for p in (order,stage,statepath,registry)}
save_new(Q/'verification/pre-publication-state.json',before)
append='\n## 2026-11-06 精确 IPv6 导入补修独立准备通过\n\n'+status+'\n报告：docs/reports/'+report.name+'。具体新单例提案：'+str(Q/'execution-proposal.md')+'。\n'
lines=order.read_text('utf-8').splitlines(keepends=True)
matches=[i for i,s in enumerate(lines) if s.startswith('- 状态：')]
assert len(matches)==1
lines[matches[0]]='- 状态：'+status+'\n'
order.write_text(''.join(lines)+append,encoding='utf-8')
stage.write_text(stage.read_text('utf-8')+append,encoding='utf-8')
state=load(statepath)
state.update(phase='SOURCE13_E02_EXACT_PROBE_PREPARATION_PASS_AWAIT_NEW_ALLOCATION',
    active_report=str(report),active_preparation_root=str(Q),active_review_agent=None,
    preparation_status='PASS_PREPARATION_ONLY',preparation_review='PASS',preparation_test_count=673,
    preparation_test_scope='584 profile contracts, retaining566 identities, plus original89 root contracts',
    e02_preparation_manifest_sha256=sha(Q/'manifest.json'),e02_preparation_tests=584,
    e02_preparation_review='PASS',e02_preparation_review_path=str(review_path),e02_preparation_review_sha256=sha(review_path),
    e02_root_entry_manifest_sha256=sha(Q/'entry-manifest.json'),e02_root_entry_current_source_review='PASS',
    e02_root_entry_current_review_sha256=sha(review_path),e02_preparation_checkpoint_tag=TAG,
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    e02_exact_probe_actual_runs=0,e02_exact_probe_result_review_allocation=0,e02_exact_probe_profile_allocation=0,
    e02='NOT_PASSED',t2='NOT_PASSED',workflow_status='waiting_new_single_case_allocation',
    next_work='New explicit one-case allocation for exact-probe zero-inference plumbing and independent result review; old grants remain consumed',
    updated_utc=stamp)
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
raw=registry.read_bytes();lines=raw.decode('utf-8-sig').splitlines(keepends=True)
matches=[i for i,s in enumerate(lines) if s.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')]
assert len(matches)==1
lines[matches[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+status+' |\r\n'
registry.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+''.join(lines).encode('utf-8'))
mirrors=[]
for source in (plan,report):
    target=MIRROR/'docs/shared/research/ultimaagent-work-capability'/source.parent.name/source.name
    assert not target.exists()
    target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes(source.read_bytes())
    assert sha(source)==sha(target)
    mirrors.append(dict(source=str(source),mirror=str(target),sha256=sha(source)))
save_new(Q/'verification/preparation-document-readback.json',dict(mirrors=mirrors))
members={Q/r['path'] for r in load(Q/'manifest.json')['files']}
members.update({Q/'manifest.json',review_path,Q/'verification/code-preparation-gate.json',
    Q/'verification/root-review-disposition.json',Q/'verification/pre-publication-state.json',
    Q/'verification/preparation-document-readback.json',plan,report,order,stage,statepath})
members.update(D/r['snapshot'] for r in load(D/'snapshot-manifest.json')['files'])
members.update(p for p in D.iterdir() if p.is_file())
members.update(p for p in (D/'inputs').iterdir() if p.is_file())
members.update({Path(__file__),Path(__file__).with_name('verify_checkpoint.py')})
main=checkpoint(REPO,members,HEAD,'fix(e02): bind import probe to exact local IPv6 capability check')
mirror=checkpoint(MIRROR,{Path(r['mirror']) for r in mirrors},MIRROR_HEAD,'docs: mirror independently reviewed E02 exact probe preparation')
for name,digest in foreign.items():assert sha(REPO/name)==digest,name
save_new(Q/'verification/preparation-checkpoint.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    main=main,mirror=mirror,tag=TAG,mirrors=mirrors,unrelated_files_preserved=foreign,
    entry_manifest_sha256=sha(Q/'entry-manifest.json'),package_manifest_sha256=sha(Q/'manifest.json'),review_sha256=sha(review_path),
    tests=673,actual_profile_runs=0,actual_profile_allocation=0,result_review_allocation=0,runtime_authority=False,
    new_push_attempted=False,remote_synced=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,preparation='PASS',runtime_authority=False)))
