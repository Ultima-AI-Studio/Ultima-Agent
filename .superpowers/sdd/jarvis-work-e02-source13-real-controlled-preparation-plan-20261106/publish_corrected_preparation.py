"""Publish only an independently passed preparation, never live authority."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,subprocess
REPO=Path(r'H:\UltimaAI\UltimaAgent');MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
N=REPO/'data/evidence/jarvis-work-capability/T2/e02-source13-real-controlled-preparation-20261107-r1'
E=N.parent/'e02-source13-root-entry-20261106';TAG='ultimaagent-t2-e02-source13-real-ready-20261107'
OLD=N.parent/'e02-source13-real-controlled-preparation-20261106'
names={'sha','load','save_new','git','gt','checkpoint'}
nodes=[n for n in ast.parse((E/'verification/checkpoint-task1.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
base='7e986e5fefa0ad9d19dd8268cffea519b5fc26e0';mbase='daf3d2e34f882c492e6f896fad8f41fcdff9e3d4'
assert gt(REPO,'rev-parse','HEAD')==base and gt(MIRROR,'rev-parse','HEAD')==mbase
manifest=load(N/'manifest.json');review_path=N/'review/independent-preparation-review.json';review=load(review_path)
assert review['verdict']=='PASS_PREPARATION_ONLY' and review['reviewer']=='root-independent'
assert review['manifest_sha256']==sha(N/'manifest.json') and not review['actual_run_authorized'] and not review['acceptance_credit']
assert not review.get('findings') and review['tests_run']==review['runtime_calls']==0
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
assert not (N/'release').exists() and not (N/'actual').exists()
save_new(N/'harness-approval.json',dict(reviewer='root-independent',overall='PASS',manifest_sha256=sha(N/'harness/manifest.json'),
    review_sha256=sha(review_path),preparation_manifest_sha256=sha(N/'manifest.json')))
PY=REPO/'tools/venv-openjarvis/Scripts/python.exe'
verified=subprocess.run([str(PY),'-I','-B','-X','utf8',str(Path(__file__).parent/'final_corrected_readback.py')],capture_output=True,check=True)
readback=json.loads(verified.stdout);save_new(N/'verification/final-preparation-readback.json',readback)
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-real-controlled-ready-20261107.md'
with report.open('x',encoding='utf8') as f:f.write(f'''# 当前8B真实受控研究首例：准备通过，等待新单例分配

原单wo-ultimaagent-20261101-0021 / T2。零推理接线及其独立结果复核已通过并消耗完原单例额度。当前已完成真正使用当前8B的首例准备：270项离线检查、整个准备包的独立只读审查和当前字节读回通过。没有运行本例，E02/T2仍未通过。

产品固定269aca511d88412dbb9c15d23911138469a37aa2；模型qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题、四来源、8次native POST上限及275/310/315秒保留，KWS/语音/生产配置未改。

## 已完成

- 输入绑定14项；原harness219项（71测试函数全部保留）；七身份/真实transport边界10项；先前SDK原始产物只读复放1项；一次性入口26项，合计270。5次完整适配回归的失败与最终PASS分别保存，未删除或挪用验收信用。
- 入口只接受本manifest绑定的新显式用户分配，先独占消费，再建立原RootInvocation父时钟并做实时七身份和模型准入；接入已有产品CLI、SourceNavigation及原生SDK模型调用。失败不重试。
- 原独审发现PREP-I01：Windows清单路径与入口必需项表示不一致。原172成员包及NEEDS_FIXES报告保持原字节；本候选只统一实际清单生产函数为正斜杠，补充直接使用该函数的RED→GREEN回归，并用完整新封存包在临时夹具做只读准入验证。入口及全部harness运行源码与原独审字节相同。
- 独审修正确认：{review_path}，SHA256 {sha(review_path)}。结论PASS_PREPARATION_ONLY，承接原整包审查并核对本次有界修正及新绑定；审查者未调用模型或产品、未追加测试。当前无待处理问题。
- 准备manifest {sha(N/'manifest.json')}，190个成员；harness manifest {sha(N/'harness/manifest.json')}。本地tag {TAG}只标记准备就绪。

## 明确的验证限制与裁定

离线SDK单测采用SDK的Python SSRF检查和固定DNS，避免RustDNS绕过Python网络审计；实际child保留原SDK行为。固定测试熵只用于可重复的离线SDK夹具，并显式生成合法UUID4，真实随机UUID、扫描器与外部读回规则未改。测试不证明真实模型的事实质量、原生RustDNS行为或生产随机ID质量；未来必须按原门实跑。

每项裁定及失败根因见harness准备报告与计划ledger。未测系统包数保持null，未把Mock六次POST计为真实推理。零推理包和全部1544绑定输入在最终读回中保持原字节。

## 下一步

按[{(N/'execution-proposal.md').name}]({N/'execution-proposal.md'})申请一例当前8B的E02-controlled-1和一次只读独立结果复核。此例无UI或音频操作；最多一次，失败停住。机械通过必须再审查research.md事实、来源归属和引用，才可能计为受控1/3；之后还需其余受控例与真实联网验收。当前分配与结果复核额度均0，harness-approval不替代用户分配。

E01当前候选3/3、E03三正一负PASS保留。远端同步仍受此前自动审批blocked by policy阻断，本次未重试；仅报告本地提交/tag及UltimaDocs字节镜像完成，不声称GitHub已同步。
''')
status='E01同候选3/3、E03三正一负PASS；E02真实8B首例准备270项离线检查、独立审查及读回PASS，等待新真实单例/结果独审分配。没有实跑，E02/T2未过。'
order=REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);indexes=[i for i,s in enumerate(lines) if s.startswith('- 状态：')];assert len(indexes)==1
lines[indexes[0]]='- 状态：'+status+'\n';append='\n## 2026-11-07 当前8B真实首例准备就绪\n\n'+status+'\n报告：docs/reports/'+report.name+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
statepath=N.parent/'current-run.json';state=load(statepath)
state.update(phase='SOURCE13_E02_REAL_CONTROLLED_READY_PENDING_USER_ALLOCATION',workflow_status='awaiting_explicit_real_case_allocation',
    preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',active_review_agent=None,
    preparation_test_count=270,preparation_tests_passed=270,preparation_test_scope='14 inputs + 219 retained harness + 10 boundary + 1 readonly SDK replay + 26 entry',
    preparation_review_receipt=str(review_path),preparation_review_path=str(review_path),preparation_review_sha256=sha(review_path),
    e02_preparation_review='PASS_PREPARATION_ONLY',e02_preparation_review_path=str(review_path),e02_preparation_review_sha256=sha(review_path),
    e02_preparation_manifest_sha256=sha(N/'manifest.json'),e02_preparation_reviewed_manifest_sha256=sha(N/'manifest.json'),
    e02_preparation_checkpoint_tag=TAG,e02_preparation_checkpoint_receipt=str(N/'verification/reviewed-preparation-checkpoint.json'),
    e02_preparation_tests=270,e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    e02_real_controlled_preparation=dict(root=str(N),status='PASS_PREPARATION_ONLY',manifest_sha256=sha(N/'manifest.json'),review_sha256=sha(review_path),tests=270,actual_case_allocation=0,result_review_allocation=0,actual_runs=0,real_inference_calls=0),
    next_action_scope=dict(scope='AWAIT_ONE_CURRENT8B_REAL_CONTROLLED_CASE_AND_RESULT_REVIEW',proposal=str(N/'execution-proposal.md'),actual_case_allocation=0,actual_result_review_allocation=0,authority_issued=False,model_calls=0),
    next_action='Await a new explicit real-current8B controlled1 grant; then fresh runtime preflight and exactly one case plus independent result review, no retry.',
    source13_next_live_admission='REQUIRES_NEW_USER_GRANT_AND_FRESH_RUNTIME_PREFLIGHT',next_offline_plan=None,
    next_work='Request one real current8B controlled research case and independent result review using the reviewed proposal',active_report=str(report),updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');raw=registry.read_bytes();lines=raw.decode('utf-8-sig').splitlines(keepends=True)
indexes=[i for i,s in enumerate(lines) if s.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(indexes)==1
lines[indexes[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | pending | '+status+' |\r\n'
registry.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+''.join(lines).encode('utf8'))
generated=subprocess.run([str(PY),'-I','-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True,check=True)
(N/'verification/queue-ready.stdout').write_bytes(generated.stdout)
mirrors=[]
for source,sub in [(report,'reports'),(N/'execution-proposal.md','execution-proposals')]:
    name=source.name if source==report else 'e02-source13-real-controlled-first-case-20261107.md'
    dest=MIRROR/'docs/shared/research/ultimaagent-work-capability'/sub/name
    assert not dest.exists();dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes());assert sha(dest)==sha(source)
    mirrors.append(dict(source=str(source),mirror=str(dest),sha256=sha(source)))
save_new(N/'verification/ready-document-readback.json',dict(mirrors=mirrors))
members={N/name for name in manifest['files']}|{N/'manifest.json',OLD/'review/independent-preparation-review.json',OLD/'verification/task3-preparation-checkpoint.json',
    N/'revision/changed-members.json',review_path,N/'harness-approval.json',N/'verification/final-preparation-readback.json',
    N/'verification/ready-document-readback.json',N/'verification/queue-ready.stdout',report,order,stage,statepath,Path(__file__),Path(__file__).parent/'final_corrected_readback.py',Path(__file__).parent/'progress.md',
    Path(__file__).parent/'prepare_bounded_manifest_fix.py',Path(__file__).parent/'seal_bounded_manifest_fix.py'}
members.update((N/'offline').glob('sealed-readiness-*/receipt.json'))
main=checkpoint(REPO,members,base,'prep(e02): accept independent real research preparation and retain unreleased live gate')
mirror=checkpoint(MIRROR,{Path(row['mirror']) for row in mirrors},mbase,'docs: mirror independently reviewed current8B real research first-case proposal')
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(REPO/name)==digest,name
save_new(N/'verification/reviewed-preparation-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,mirrors=mirrors,manifest_sha256=sha(N/'manifest.json'),
    review_sha256=sha(review_path),runtime_authority=False,actual_case_allocation=0,result_review_allocation=0,remote_synced=False,new_push_attempted=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,verdict='PASS_PREPARATION_ONLY',manifest_sha256=sha(N/'manifest.json'))))
