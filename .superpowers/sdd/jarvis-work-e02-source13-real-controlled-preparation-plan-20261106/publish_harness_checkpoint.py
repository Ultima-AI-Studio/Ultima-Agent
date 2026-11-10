from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
REPO=Path(r'H:\UltimaAI\UltimaAgent');MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
T=REPO/'data/evidence/jarvis-work-capability/T2';N=T/'e02-source13-real-controlled-preparation-20261106'
E=T/'e02-source13-root-entry-20261106';TAG='ultimaagent-t2-e02-source13-real-harness-20261107'
names={'sha','load','save_new','git','gt','checkpoint'}
nodes=[n for n in ast.parse((E/'verification/checkpoint-task1.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
assert len(nodes)==len(names);exec(compile(ast.Module(body=nodes,type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
base='0803cdb3df3fdb7d1b1d6f5ce92b142f631f4b25';mirror_base='b1de9b98b40cb52f3d33f5c1882375370ca85db2'
assert gt(REPO,'rev-parse','HEAD')==base and gt(MIRROR,'rev-parse','HEAD')==mirror_base
PY=REPO/'tools/venv-openjarvis/Scripts/python.exe'
verified=subprocess.run([str(PY),'-I','-B','-X','utf8',str(N/'verification/verify_task2.py')],capture_output=True,check=True)
readback=json.loads(verified.stdout);assert readback['verdict']=='PASS_SOURCE13_REAL_HARNESS_OFFLINE_ONLY'
save_new(N/'verification/task2-readback.json',readback)
foreign=load(N/'inputs/unrelated-working-tree.json')['files']
for p,digest in foreign.items():assert sha(REPO/p)==digest,p
plan=REPO/'docs/plans/jarvis-work-e02-source13-real-controlled-preparation-plan-20261106.md'
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-real-harness-preparation-20261107.md'
with report.open('x',encoding='utf8') as stream:stream.write(f'''# 当前8B真实研究：原harness离线适配完成

原单 wo-ultimaagent-20261101-0021 / T2。Task2已完成，真实入口和整体独立准备审查尚待Task3。当前没有新的模型、现场用例或结果复核分配；E02/T2仍未通过。

- 使用当前候选269aca5与当前社区8B摘要，复用既有实际研究harness、SourceNavigation及官方SDK。没有改动冻结产品、模型默认配置或已通过的零推理包。
- 旧五身份改为七身份，校验原生创建时间、父PID、命令摘要和CIM身份；精确适配已接受P4快照中的CreationFileTime字段。实际child仍只安装原四来源搜索/GET夹具及导出观察器，HTTPX模型Client/send/transport保持原实现。
- 原71个测试函数、219个参数化用例身份全部保留。最后一轮219/219通过；新增10项身份及真实调用路径检查通过，已有SDK完整产物只读复放1项通过。本步骤230项，加Task1的14项输入检查，共244项离线检查；不是244次产品验收。
- SDK复放读取a47c74c4-58e7-4a63-ad7d-f63be9c17a51的原始packet、原四来源、最终ACK、引用绑定和research.md（711字节，SHA256 a7e7e5906654d1981efb48a3e8006de0d45270f27db0adfee5ee02513c549df2）。文件逐项哈希保持，历史6次Mock POST计数未计为真实推理。
- 本轮完整回归原始结果依次135/219、204/219、218/219、214/219、219/219，失败及每轮源码快照保留。最后一轮：{readback['full_suite']}。

## 测试适配裁定与限制

1. SDK的Rust SSRF可绕过Python DNS替身；离线单测显式使用SDK自身Python检查并固定DNS。沿用已通过的精确IPv6冷导入审计和未使用Ollama客户端关闭机制。审计无拒绝事件，唯一冷导入探针已关闭；没有模型或产品启动。原生系统包数量未测，不能宣称抓包证明。
2. 旧harness漏导入产品既有稳定熵夹具，一次随机来源ID触发真实PII扫描。复用稳定熵并仅将测试UUID固定为合法version4，以符合真实外部读回器；没有放宽扫描器或UUID检查。此测试不证明生产随机ID质量，真实研究仍须按原门实际验证。

准备manifest：{sha(N/'harness/manifest.json')}。本地检查点tag：{TAG}，不构成运行批准。下一步按既有计划Task3连接RootInvocation、一次性分配和整体独立审查，保留275/310/315秒及8次POST上限，再提出真实8B单例。

E01同候选3/3和E03三正一负PASS保留。KWS/语音、生产服务未操作。远端push仍受此前自动审批blocked by policy阻断，本轮未重试或绕行。
''')
status='E01固定3/3、E03三正一负PASS；E02真实8B研究harness离线适配完成（219原回归+10边界+1SDK复放），连同输入检查244项通过；Task3入口/整体独审待完成，无实跑额度，E02/T2未过。'
order=REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);indexes=[i for i,s in enumerate(lines) if s.startswith('- 状态：')];assert len(indexes)==1
lines[indexes[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 当前8B真实研究harness检查点\n\n'+status+'\n报告：docs/reports/'+report.name+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
statepath=T/'current-run.json';state=load(statepath)
state.update(active_report=str(report),preparation_test_count=244,preparation_test_scope='14 input + 219 retained harness + 10 boundary + 1 immutable SDK replay; root entry pending',
    e02_preparation_review='PENDING',e02_preparation_review_path=None,e02_preparation_review_sha256=None,e02_preparation_tests=244,
    next_work='Task3: one-case root entry, offline admission tests and whole-package independent preparation review; no live allocation',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');raw=registry.read_bytes();lines=raw.decode('utf-8-sig').splitlines(keepends=True)
indexes=[i for i,s in enumerate(lines) if s.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(indexes)==1
lines[indexes[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+status+' |\r\n'
registry.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+''.join(lines).encode('utf8'))
generated=subprocess.run([str(PY),'-I','-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True,check=True)
(N/'verification/queue-harness.stdout').write_bytes(generated.stdout)
dest=MIRROR/'docs/shared/research/ultimaagent-work-capability/reports'/report.name
assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(report.read_bytes())
assert sha(dest)==sha(report)
members={p for sub in ('inputs','tests','verification','harness') for p in (N/sub).rglob('*') if p.is_file()}
members.update(p for p in (N/'code').iterdir() if p.is_file())
for run in (N/'code').glob('harness-preparation-*'):
    members.update(p for p in run.iterdir() if p.is_file())
    for sub in ('harness','harness-source'):members.update(p for p in (run/sub).iterdir() if p.is_file())
for run in (N/'offline').iterdir():
    members.update(p for p in run.iterdir() if p.is_file())
    if (run/'snapshot').exists():members.update(p for p in (run/'snapshot').iterdir() if p.is_file())
members.update({report,order,stage,statepath,Path(__file__),Path(__file__).parent/'progress.md'})
assert not any('__pycache__' in p.parts for p in members)
main=checkpoint(REPO,members,base,'prep(e02): adapt real research harness to source13 and verify immutable SDK replay')
mirror=checkpoint(MIRROR,{dest},mirror_base,'docs: mirror source13 real research harness offline checkpoint')
for p,digest in foreign.items():assert sha(REPO/p)==digest,p
save_new(N/'verification/task2-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,report=str(report),mirror_path=str(dest),report_sha256=sha(report),
    unrelated_files_preserved=foreign,runtime_authority=False,actual_model_calls=0,actual_product_runs=0,remote_synced=False,new_push_attempted=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,task2='PASS_OFFLINE_ONLY',runtime_authority=False)))
