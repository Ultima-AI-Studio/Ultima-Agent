from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
REPO=Path(r'H:\UltimaAI\UltimaAgent');MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
N=REPO/'data/evidence/jarvis-work-capability/T2/e02-source13-real-controlled-preparation-20261106'
E=N.parent/'e02-source13-root-entry-20261106';TAG='ultimaagent-t2-e02-source13-real-root-prep-20261107'
names={'sha','load','save_new','git','gt','checkpoint'}
nodes=[n for n in ast.parse((E/'verification/checkpoint-task1.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
base='938ca1d893dd41fd1928b24825fcb49e79dd7ec2';mbase='265aa5a765f66b403e8e38bee4ee822de9a87279'
assert gt(REPO,'rev-parse','HEAD')==base and gt(MIRROR,'rev-parse','HEAD')==mbase
manifest=load(N/'manifest.json')
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
foreign=load(N/'inputs/unrelated-working-tree.json')['files']
for name,digest in foreign.items():assert sha(REPO/name)==digest,name
assert not (N/'actual').exists() and not (N/'release').exists()
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-real-root-preparation-20261107.md'
with report.open('x',encoding='utf8') as f:f.write(f'''# 当前8B真实研究入口准备：待整体独审

原单wo-ultimaagent-20261101-0021 / T2。当前候选269aca5、当前社区8B，保留原题四来源及275/310/315秒门。输入绑定、原harness适配、SDK产物只读复放、一次性root入口已实现；共269项离线检查通过。172个成员准备manifest SHA256为{sha(N/'manifest.json')}，独立审查尚未进行，没有新实际运行或结果复核额度，E02/T2仍未通过。

入口先校验准备包、独审、当前候选与模型，再独占消费新的用户分配，随后建立原RootInvocation同一父时钟，读取实时七身份和固定本地元数据，签发原单例authority，调用既有run_case。原始terminal保持，外层结果独立裁定；事实复核完成前不发验收信用。无授权或重复消费不会进入产品。

代码：{N / 'code/entry.py'}。条件提案：{N / 'execution-proposal.md'}。本地准备tag：{TAG}，不是运行批准。下一步独立准备review；通过后本地提交/tag与镜像并请求新的真实8B单例。准备过程未调用模型、产品、UI、音频或生产服务；不会把已通过的零推理单例再次消费。远端同步仍受此前自动审批blocked by policy阻断，未重试。
''')
statepath=N.parent/'current-run.json';state=load(statepath)
state.update(active_report=str(report),preparation_test_count=269,e02_preparation_tests=269,e02_preparation_manifest_sha256=sha(N/'manifest.json'),
    e02_preparation_review='PENDING',e02_preparation_review_path=None,e02_preparation_review_sha256=None,
    next_work='Whole-package independent preparation review; current root entry not released',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
dest=MIRROR/'docs/shared/research/ultimaagent-work-capability/reports'/report.name
assert not dest.exists();dest.write_bytes(report.read_bytes())
members={N/name for name in manifest['files']}|{N/'manifest.json',report,statepath,Path(__file__),Path(__file__).parent/'progress.md',N/'verification/task2-checkpoint.json'}
main=checkpoint(REPO,members,base,'prep(e02): seal current8B one-case root entry for independent review')
mirror=checkpoint(MIRROR,{dest},mbase,'docs: mirror real research root preparation pending independent review')
for name,digest in foreign.items():assert sha(REPO/name)==digest,name
save_new(N/'verification/task3-preparation-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,manifest_sha256=sha(N/'manifest.json'),
    report_sha256=sha(report),mirror_path=str(dest),actual_released=False,remote_synced=False,new_push_attempted=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,manifest_sha256=sha(N/'manifest.json'))))
