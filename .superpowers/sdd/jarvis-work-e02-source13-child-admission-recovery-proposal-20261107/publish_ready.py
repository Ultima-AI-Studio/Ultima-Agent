"""Publish the reviewed recovery; existing conditional grant remains unused."""
from pathlib import Path
import ast,datetime as dt,hashlib,importlib.util,json,subprocess
REPO=Path(r'H:\UltimaAI\UltimaAgent');MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
N=REPO/'data/evidence/jarvis-work-capability/T2/e02-source13-child-admission-20261107-r1'
OLD=N.parent/'e02-source13-real-controlled-preparation-20261107-r1'
E=N.parent/'e02-source13-root-entry-20261106'
TAG='ultimaagent-t2-e02-source13-child-admission-ready-20261107'
names={'sha','load','save_new','git','gt','checkpoint'}
nodes=[n for n in ast.parse((E/'verification/checkpoint-task1.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name in names]
exec(compile(ast.Module(body=nodes,type_ignores=[]),'retained-checkpoint-functions','exec'),globals())
base='70c994f3ae9d49a6b20018512204108931fbf798';mbase='794725453453949b70779f3cafd256614a2ac17d'
assert gt(REPO,'rev-parse','HEAD')==base and gt(MIRROR,'rev-parse','HEAD')==mbase
assert sha(N/'manifest.json')=='ae432a96ae7ede18da792d89dfe75fc3d3d7887e51761508aa03ce3f2e255353'
review_path=N/'review/independent-preparation-review.json';review=load(review_path)
assert review['reviewer']=='root-independent' and review['verdict']=='PASS_PREPARATION_ONLY'
assert review['manifest_sha256']==sha(N/'manifest.json') and review['actual_run_authorized'] is False and review['acceptance_credit'] is False
assert not review.get('findings') and review['tests_run']==review['runtime_calls']==0
save_new(N/'harness-approval.json',dict(reviewer='root-independent',overall='PASS',manifest_sha256=sha(N/'harness/manifest.json'),
    review_sha256=sha(review_path),preparation_manifest_sha256=sha(N/'manifest.json')))
spec=importlib.util.spec_from_file_location('recovery_entry_readiness',N/'code/entry.py');entry=importlib.util.module_from_spec(spec);spec.loader.exec_module(entry)
ready=entry.read_ready(N)
spec=importlib.util.spec_from_file_location('readonly_recovery_verify',N/'verification/verify_recovery.py');verify=importlib.util.module_from_spec(spec);spec.loader.exec_module(verify)
checks=verify.verify()
assert gt(Path(load(N/'inputs/input-manifest.json')['candidate_root']),'rev-parse','HEAD')==entry.CANDIDATE
save_new(N/'verification/preparation-final-readback.json',dict(verdict='PASS_PREPARATION_ONLY',package=ready,
    tests=checks['tests'],source_and_prior_failure_unchanged=True,actual_allocation_issued=False,actual_calls=0,model_calls=0,E02='NOT_PASSED',T2='NOT_PASSED'))
report=REPO/'docs/reports/jarvis-work-t2-e02-source13-child-admission-ready-20261107.md'
text='# E02子进程准入补修：离线与独立准备审查通过\n\n原单wo-ultimaagent-20261101-0021 / T2，当前8B与产品269aca5。272项离线检查、独立准备审查及封存字节读回通过。用户call_42e3d2dd124f406cb3ccebd14a9b1c0f已授权审查通过后一例真实研究及一次结果复核，当前尚未签发/消费运行记录。\n\n'
text+='准备manifest '+sha(N/'manifest.json')+'（130成员）；独审 '+str(review_path)+'，SHA256 '+sha(review_path)+'。\n\n'
text+=(N/'preparation-report.md').read_text('utf8')+'\n实际执行提案：'+str(N/'execution-proposal.md')+'。新包仅修验收框架准入职责，未改产品。当前E02/T2仍未通过；准备PASS不增加研究信用。远端push仍受既有自动审批blocked by policy阻断，本次仅本地提交/tag与镜像。\n'
with report.open('x',encoding='utf8',newline='\n') as f:f.write(text)
plan=REPO/'docs/plans/jarvis-work-e02-source13-child-admission-recovery-proposal-20261107.md'
status='E01同候选3/3、E03三正一负PASS；E02子进程准入补修272项离线检查与独立准备审查PASS，旧实际FAIL保留，按现有授权进入新一例当前8B研究及结果独审；E02/T2未过。'
order=REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md';stage=REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
lines=order.read_text('utf8').splitlines(keepends=True);ix=[i for i,s in enumerate(lines) if s.startswith('- 状态：')];assert len(ix)==1
lines[ix[0]]='- 状态：'+status+'\n';append='\n## 2026-11-07 子进程准入恢复准备通过\n\n'+status+'\n报告：docs/reports/'+report.name+'。\n'
order.write_text(''.join(lines)+append,encoding='utf8');stage.write_text(stage.read_text('utf8')+append,encoding='utf8')
statepath=N.parent/'current-run.json';s=load(statepath)
s.update(phase='SOURCE13_E02_CHILD_ADMISSION_READY_AUTHORIZED_SINGLE_CASE',workflow_status='authorized_case_ready',
    active_review_agent=None,active_preparation_root=str(N),active_report=str(report),preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',
    preparation_test_count=272,preparation_tests_passed=272,preparation_test_scope='219 retained exact cases + 17 full admit regression + 10 boundary + 26 entry',
    e02_preparation_review='PASS_PREPARATION_ONLY',e02_preparation_review_path=str(review_path),e02_preparation_review_sha256=sha(review_path),
    e02_preparation_manifest_sha256=sha(N/'manifest.json'),e02_preparation_reviewed_manifest_sha256=sha(N/'manifest.json'),
    e02_preparation_checkpoint_tag=TAG,e02_preparation_checkpoint_receipt=str(N/'verification/ready-checkpoint.json'),
    e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    next_action_scope=dict(scope='ALREADY_AUTHORIZED_ONE_RECOVERY_CASE_AND_RESULT_REVIEW',question_id='call_42e3d2dd124f406cb3ccebd14a9b1c0f',
        actual_case_allocation=1,actual_result_review_allocation=1,authority_issued=False,retry=0),
    next_action='Issue one fresh exact-bound grant from the existing user authorization; execute once and independently review result; no retry.',
    next_work='Run authorized current8B controlled recovery once after fresh protected identity/model preflight.',updated_utc=dt.datetime.now(dt.timezone.utc).isoformat())
statepath.write_text(json.dumps(s,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
registry=Path(r'H:\UltimaAI\_shared\queue\global-queue-index.md');raw=registry.read_bytes();lines=raw.decode('utf-8-sig').splitlines(keepends=True)
ix=[i for i,s in enumerate(lines) if s.startswith('| UltimaAgent | wo-ultimaagent-20261101-0021 |')];assert len(ix)==1
lines[ix[0]]='| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+status+' |\r\n'
registry.write_bytes((b'\xef\xbb\xbf' if raw.startswith(b'\xef\xbb\xbf') else b'')+''.join(lines).encode('utf8'))
res=subprocess.run([str(REPO/'tools/venv-openjarvis/Scripts/python.exe'),'-I','-B','-X','utf8',r'H:\UltimaAI\_shared\queue\queue-status-gen.py'],capture_output=True,check=True)
with (N/'verification/queue-ready.stdout').open('xb') as f:f.write(res.stdout)
mirrors=[]
for source,sub,name in ((report,'reports',report.name),(plan,'plans',plan.name),(N/'execution-proposal.md','execution-proposals','e02-source13-child-admission-single-case-20261107.md')):
    dest=MIRROR/'docs/shared/research/ultimaagent-work-capability'/sub/name
    if dest.exists():
        prior=next(row for row in load(OLD/'verification/real-result-checkpoint.json')['mirrors'] if row['mirror']==str(dest))
        assert sha(dest)==prior['sha256']
    dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes(source.read_bytes());assert sha(dest)==sha(source)
    mirrors.append(dict(source=str(source),mirror=str(dest),sha256=sha(source)))
save_new(N/'verification/ready-mirror-readback.json',dict(mirrors=mirrors))
members={N/name for name in load(N/'manifest.json')['files']}|{N/'manifest.json',review_path,N/'harness-approval.json',
    N/'verification/preparation-final-readback.json',N/'verification/queue-ready.stdout',N/'verification/ready-mirror-readback.json',
    report,plan,order,stage,statepath,Path(__file__),OLD/'verification/real-result-checkpoint.json',OLD/'verification/final-real-result-readback.json'}
members.update((N/'offline').glob('sealed-readiness-*/receipt.json'))
members.update(p for p in Path(__file__).parent.iterdir() if p.is_file())
main=checkpoint(REPO,members,base,'fix(e02): keep child admission native-only while retaining full parent identity checks')
mirror=checkpoint(MIRROR,{Path(row['mirror']) for row in mirrors},mbase,'docs: mirror reviewed E02 child admission recovery and authorized single-case proposal')
save_new(N/'verification/ready-checkpoint.json',dict(main=main,mirror=mirror,tag=TAG,mirrors=mirrors,
    manifest_sha256=sha(N/'manifest.json'),review_sha256=sha(review_path),actual_allocation_issued=False,
    user_conditional_grant='call_42e3d2dd124f406cb3ccebd14a9b1c0f',remote_synced=False,new_push_attempted=False))
print(json.dumps(dict(main=main['commit'],mirror=mirror['commit'],tag=TAG,ready=ready,tests=272,actual_allocation_issued=False)))
