from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
REPO=Path(r'H:\UltimaAI\UltimaAgent');MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
T=REPO/'data/evidence/jarvis-work-capability/T2';N=T/'e02-source13-real-controlled-preparation-20261106'
E=T/'e02-source13-root-entry-20261106';TAG='ultimaagent-t2-e02-source13-real-inputs-20261106'
names={'sha','load','save_new','git','gt','checkpoint'}
nodes=[n for n in ast.parse((E/'verification/checkpoint-task1.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
assert gt(REPO,'rev-parse','HEAD')=='a969e35bbd1a54c3fd7e4dc5306804901ccb7560'
assert gt(MIRROR,'rev-parse','HEAD')=='ff973bcbd24234084e5cf2d8cbce412c4d8b3df3'
assert not (N/'actual').exists() and not (N/'release').exists()
PY=REPO/'tools/venv-openjarvis/Scripts/python.exe'
verified=subprocess.run([str(PY),'-I','-B','-X','utf8',str(N/'verification/verify_task1.py')],capture_output=True,check=True)
readback=json.loads(verified.stdout);assert readback['verdict']=='PASS_CURRENT8B_INPUT_BINDING_ONLY'
save_new(N/'verification/task1-readback.json',readback)
foreign=load(N/'inputs/unrelated-working-tree.json')['files']
for p,digest in foreign.items():assert sha(REPO/p)==digest,p
plan=REPO/'docs/plans/jarvis-work-e02-source13-real-controlled-preparation-plan-20261106.md'
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-real-controlled-inputs-20261106.md'
assert not report.exists()
report.write_text(f'''# 当前8B真实研究首例：输入绑定检查点

原单 wo-ultimaagent-20261101-0021 / T2。上一轮零推理接线单例及独立结果复核PASS已完成。当前已完成真实研究首例准备的Task1：输入绑定与复用对账；真实运行入口和独立准备审查尚未完成，没有实跑或模型调用额度。E02/T2仍未通过。

## 本次完成

- 新输入清单绑定1544个文件，含当前候选269aca5的57份产品文件、当前8B摘要、原题四来源、E01/E03正式登记、七保护身份、零推理结果和独审，以及原真实研究harness和deadline ruling。
- 旧实际harness的31个产品文件与当前候选逐项对照，5个不同：work_context.py、work_service.py及三份相关测试。研究入口和SourceNavigation已经存在，不需要重写产品Agent。
- 旧harness有71个测试函数身份，已登记待保留；它仍指向旧候选且只核验5个保护身份，不能原样实跑。当前E01 helper具备7身份、parent/命令摘要与CIM精度规则，下一任务复用它。
- 14项输入绑定检查通过；RED的37个错误来自尚未实现的绑定接口（含参数子例），原日志保留。GREEN只导入标准库，没有SDK、产品、网络或子进程操作；固定测试runner自身只启动一个隔离测试解释器。
- 拒绝错误候选/工作区、官方或其他8B/14B、摘要漂移、改变原corpus、放宽预算、布尔冒充整数、缺失/变化文件、相对路径、五身份基线或把Mock接线计作真实研究。

输入manifest SHA-256：{sha(N/'inputs/input-manifest.json')}。证据目录：{N}。本地tag：{TAG}，仅标记输入检查点，绝非实际运行准入。

## 下一步

按计划Task2在新目录适配原实际研究harness，保持真实模型transport，只替换原受控搜索/GET，并用已有SDK产物做离线读回兼容验证。随后Task3连接原RootInvocation、完成离线负例与独立准备审查，再提出可审阅的真实8B单例执行包。保持原275/310/315秒时限、8次native POST上限及失败不重试。

E01同候选3/3和E03三正一负PASS保留。当前KWS、语音、生产服务及模型默认值未改；没有使用新实际运行/结果复核分配。远端push仍受此前自动审批blocked by policy阻断，本轮不重试或绕行。
''',encoding='utf-8')
status='E01固定3/3、E03三正一负PASS；E02零推理接线及独审PASS后，当前8B真实研究首例完成1544输入绑定与14项检查。实际harness仍待适配及独审，无模型调用/实跑分配，E02/T2未过。'
order=REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf-8').splitlines(keepends=True);indexes=[i for i,s in enumerate(lines) if s.startswith('- 状态：')];assert len(indexes)==1
lines[indexes[0]]='- 状态：'+status+'\n';append='\n## 2026-11-06 当前8B真实研究输入检查点\n\n'+status+'\n报告：docs/reports/'+report.name+'。\n'
order.write_text(''.join(lines)+append,encoding='utf-8');stage.write_text(stage.read_text('utf-8')+append,encoding='utf-8')
statepath=T/'current-run.json';state=load(statepath)
state.update(active_report=str(report),preparation_test_count=14,preparation_test_scope='Input binding contract only; live harness preparation incomplete',
    e02_preparation_review='PENDING',e02_preparation_review_path=None,e02_preparation_review_sha256=None,
    e02_preparation_manifest_sha256=None,e02_preparation_tests=14,
    next_work='Task2: adapt existing actual research harness and replay current SDK export offline; no live allocation',
    updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf-8')
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');raw=registry.read_bytes();lines=raw.decode('utf-8-sig').splitlines(keepends=True)
indexes=[i for i,s in enumerate(lines) if s.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(indexes)==1
lines[indexes[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+status+' |\r\n'
registry.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+''.join(lines).encode('utf-8'))
generated=subprocess.run([str(PY),'-I','-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True,check=True)
with (N/'verification/queue-inputs.stdout').open('xb') as f:f.write(generated.stdout)
mirrors=[]
for source in (plan,report):
    dest=MIRROR/'docs/shared/research/ultimaagent-work-capability'/source.parent.name/source.name
    assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes());assert sha(source)==sha(dest)
    mirrors.append(dict(source=str(source),mirror=str(dest),sha256=sha(source)))
save_new(N/'verification/input-document-readback.json',dict(mirrors=mirrors))
members={p for p in N.rglob('*') if p.is_file()}
assert not any('__pycache__' in p.parts for p in members)
members.update({plan,report,order,stage,statepath,Path(__file__)})
manifest=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),scope='TASK1_INPUT_CHECKPOINT_ONLY',runtime_authority=False,
    files=[dict(path=str(p),sha256=sha(p)) for p in sorted(members)])
save_new(N/'verification/task1-checkpoint-manifest.json',manifest);members.add(N/'verification/task1-checkpoint-manifest.json')
main=checkpoint(REPO,members,'a969e35bbd1a54c3fd7e4dc5306804901ccb7560','prep(e02): bind current8B real research inputs and preserve original gates')
mirror=checkpoint(MIRROR,{Path(r['mirror']) for r in mirrors},'ff973bcbd24234084e5cf2d8cbce412c4d8b3df3','docs: mirror current8B real research input checkpoint')
for p,digest in foreign.items():assert sha(REPO/p)==digest,p
save_new(N/'verification/task1-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,mirrors=mirrors,unrelated_files_preserved=foreign,
    runtime_authority=False,actual_model_calls=0,actual_product_runs=0,manifest_sha256=sha(N/'verification/task1-checkpoint-manifest.json'),
    remote_synced=False,new_push_attempted=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,task1='PASS_INPUTS_ONLY',runtime_authority=False)))
