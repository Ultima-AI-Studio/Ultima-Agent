"""Publish independently reviewed preparation; never allocate or run a case."""
from pathlib import Path
import ast,datetime as dt,hashlib,importlib.util,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');M=Path('H:/UltimaAI/ultima-docs-repo')
N=R/'data/evidence/jarvis-work-capability/T2/e02-source-reference-schema-20261107-r1'
L=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-reference/UltimaAgent')
TAG='ultimaagent-t2-e02-source-reference-ready-20261107'
MAIN='4653f923b66346fbfa81eb738d0a7db941b0dd64';MIRROR='f079ab8bf1a4929075c333ae278b880b9835cf1f'
names={'sha','load','save_new','git','gt','checkpoint'}
tree=ast.parse((N.parent/'e02-source13-root-entry-20261106/verification/checkpoint-task1.py').read_bytes())
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names],type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
assert gt(R,'rev-parse','HEAD')==MAIN and gt(M,'rev-parse','HEAD')==MIRROR
reviewpath=N/'review/independent-preparation-review.json';review=load(reviewpath)
assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PREPARATION_ONLY'
assert review['manifest_sha256']==sha(N/'manifest.json') and review['actual_run_authorized'] is False
assert review['tests_run']==review['runtime_calls']==0 and not review['findings']
manifest=load(N/'manifest.json');assert manifest['test_count']==857
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
for name,digest in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
wrapper=load(N/'inputs/execution-wrapper.json');assert sha(Path(wrapper['path']))==wrapper['sha256']
assert gt(C,'rev-parse','HEAD')==load(N/'inputs/candidate-transition.json')['candidate'] and not gt(C,'status','--porcelain')
save_new(N/'harness-approval.json',dict(reviewer='root-independent',overall='PASS',manifest_sha256=sha(N/'harness/manifest.json'),review_sha256=sha(reviewpath),preparation_manifest_sha256=sha(N/'manifest.json')))
spec=importlib.util.spec_from_file_location('ready_readback',N/'code/entry.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
ready=entry.read_ready(N)
save_new(N/'verification/pre-execution-readback.json',dict(verdict='PASS_READINESS_ONLY',**ready,actual_released=False,actual_invocations=0,candidate=entry.CANDIDATE,read_at=dt.datetime.now(dt.timezone.utc).isoformat()))
plan=R/'docs/plans/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107.md'
report=R/'docs/reports/jarvis-work-t2-e02-source-reference-preparation-20261107.md'
with report.open('x',encoding='utf8',newline='\n') as f:
    f.write((N/'preparation-report.md').read_text('utf8')+'\n## 独立准备审查结果\n\nPASS_PREPARATION_ONLY；manifest '+sha(N/'manifest.json')+'（'+str(len(manifest['files']))+'成员），review SHA256 '+sha(reviewpath)+'。857项离线检查、1557绑定输入与62来源读回；实际入口尚未调用，按既有完整授权继续一例。\n')
status='E02来源与证据schema候选'+entry.CANDIDATE[:7]+'准备完成，857项离线检查/独立准备PASS；全部旧失败保留，按已授权范围待一次当前8B原题四来源及结果复核。E02/T2未过；旧E01/E03信用不转移。'
order=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,s in enumerate(lines) if s.startswith('- 状态：')];assert len(ix)==1;lines[ix[0]]='- 状态：'+status+'\n'
append='\n## 2026-11-07 来源与证据schema准备PASS\n\n'+status+'\n报告：docs/reports/'+report.name+'。提案：'+str(N/'execution-proposal.md')+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
statepath=N.parent/'current-run.json';s=load(statepath)
s.update(phase='SOURCE17_E02_SOURCE_REFERENCE_SCHEMA_REVIEWED_READY',workflow_status='ready_for_authorized_single_case',stage_queue_state='EXECUTING',active_review_agent=None,active_report=str(report),active_evidence=str(N),active_candidate=entry.CANDIDATE,e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    current_e02_controlled_passed=0,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    next_action_scope=dict(question_id=wrapper['question_id'],candidate=entry.CANDIDATE,conditional_actual_case_allocation=1,conditional_result_review_allocation=1,authority_issued=False,retry=0,scope='single original-question four-source current8B case after independent preparation PASS'))
statepath.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
queue=Path('H:/UltimaAI/_shared/queue/global-queue-index.md');lines=queue.read_text('utf8').splitlines(keepends=True);ix=[i for i,v in enumerate(lines) if v.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(ix)==1
lines[ix[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+status+' |\n';queue.write_text(''.join(lines),encoding='utf8')
p=subprocess.run([str(R/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
(N/'verification/queue-ready.stdout').write_bytes(p.stdout+p.stderr);assert p.returncode==0
mirrors=[]
for src,folder in [(plan,'plans'),(report,'reports'),(N/'execution-proposal.md','execution-proposals')]:
    name=src.name if folder!='execution-proposals' else 'e02-source-reference-schema-20261107-r1.md'
    dst=M/'docs/shared/research/ultimaagent-work-capability'/folder/name;dst.parent.mkdir(parents=True,exist_ok=True)
    if dst.exists():assert src==plan and sha(dst)==hashlib.sha256(git(M,'show','HEAD:'+dst.relative_to(M).as_posix())).hexdigest()
    dst.write_bytes(src.read_bytes());assert sha(dst)==sha(src)
    mirrors.append(dict(source=str(src),mirror=str(dst),sha256=sha(src)))
save_new(N/'verification/ready-mirror-readback.json',dict(mirrors=mirrors,remote_synced=False))
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask 1: independent preparation PASS, review '+sha(reviewpath)+'. Final: Ruling: live model output/facts, protected-state continuity and cleanup remain for the authorized case and result review; static preparation grants no acceptance credit. Cost if wrong: no E02 PASS without observed output. No unresolved findings.\n')
paths={N/name for name in manifest['files']}
paths.update({N/'manifest.json',reviewpath,N/'harness-approval.json',N/'verification/pre-execution-readback.json',N/'verification/ready-mirror-readback.json',N/'verification/queue-ready.stdout',report,plan,order,stage,statepath})
paths.update(p for p in L.iterdir() if p.is_file())
main=checkpoint(R,paths,MAIN,'chore(e02): seal source-reference schema and reconciled identity readiness')
mirror=checkpoint(M,[Path(row['mirror']) for row in mirrors],MIRROR,'docs(e02): mirror source-reference schema preparation')
save_new(N/'verification/ready-checkpoint.json',dict(main=main,mirror=mirror,product=load(N/'verification/product-checkpoint.json')['commit'],manifest_sha256=sha(N/'manifest.json'),review_sha256=sha(reviewpath),remote_synced=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,ready=True,actual_released=False)))
