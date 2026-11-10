"""Archive the reviewed diagnostic failure and continue only its authorized repair scope."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo');A=N/'actual/E02-controlled-1';D=N/'review/result-inputs'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True,encoding='utf8').strip()
reviewpath=N/'review/independent-result-review.json';review=load(reviewpath);rm=load(D/'result-manifest.json')
assert review['reviewer']=='root-independent' and review['verdict']=='FAIL_CONFIRMED'
assert review['result_manifest_sha256']==sha(D/'result-manifest.json')=='083bdd6aea562acf27276b3896a6931284588ee51664580c2b61129301ffc02d'
for manifest in (rm,load(N/'manifest.json')):
    for name,h in manifest['files'].items():assert sha(N/name)==h,name
for name,h in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==h,name
for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
assert not git(R,'diff','--cached','--name-only') and not git(M,'diff','--cached','--name-only')
p=load(A/'product-result.json');t=load(A/'terminal.json');o=load(N/'release/root-outcome.json');run=load(N/'release/tool-execution-receipt.json');readonly=load(D/'readonly-closeout.json')
d=load(A/'trusted-failure-diagnostic.raw');export=load(A/'trusted-failure-diagnostic.export.json')
assert o['status']=='FAIL' and not list(A.rglob('research.md')) and run['invocations']==1
assert export['status']=='SAVED' and export['sha256']==sha(A/'trusted-failure-diagnostic.raw')
count=lambda name:sum(x.get('tool_name')==name and x.get('success') is True for x in p['tool_results'])
reads=sum(x['confirmed'] is True for x in d['pages'])
assert reads==6 and d['branch']=='action' and p['research_failure']['reason_code']=='INVALID_SOURCE_SECTION'
registration=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',purpose='diagnostic',run_id=t['run_id'],candidate=load(N/'manifest.json')['candidate'],
    model='qwen3-8b-uncensored',question_id=run['question_id'],result='FAIL',independent_review=review['verdict'],review_path=str(reviewpath),review_sha256=sha(reviewpath),
    result_manifest_sha256=sha(D/'result-manifest.json'),terminal_sha256=sha(A/'terminal.json'),product_result_sha256=sha(A/'product-result.json'),
    entry_invocations=1,work_cli_attempts=t['work_cli_attempts'],controlled_search_success=count('ultima_work_web_search'),controlled_GET_success=count('ultima_work_http_get'),
    confirmed_inspect_pages=reads,public_successful_inspect_records=count('ultima_work_research_inspect'),inspect_count_basis='trusted failure diagnostic confirmed pages, not the incomplete public tool_results list',
    write_attempts=sum(x.get('tool_name')=='ultima_work_research_write' for x in p['tool_results']),successful_write_count=count('ultima_work_research_write'),
    application_native_POST_attempts=t['application_native_POST_attempts'],actual_native_start_count=None,research_artifacts=0,outer_elapsed_seconds=run['outer_elapsed_seconds'],
    cleanup=t['cleanup']['status'],root_witness_eligible=o['outcome']['witness']['eligible'],product_error=p['error'],research_failure=p['research_failure'],
    failure_diagnostic_sha256=sha(A/'trusted-failure-diagnostic.raw'),branch=d['branch'],eligible_source_ids=d['eligible_source_ids'],
    selected_pages=[dict(source_id=x['source_id'],start=x['requested_start'],range=x['range']) for x in d['pages']],budget=d['budget'],write_confirmed=False,ack_confirmed=False,
    facts='NOT_ASSESSABLE_NO_ARTIFACT',original_question_coverage='NOT_ASSESSABLE_NO_ARTIFACT',
    protected_at_recorded_boundaries=(sha(A/'boundary-before.json')==sha(A/'boundary-after.json')),protected_after_readonly=readonly['protected_all_equal'],continuous_liveness_measured=False,
    acceptance_credit=0,controlled_passed=0,controlled_required=3,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,retry=0,next_case_released=False,
    E02='NOT_PASSED',T2='NOT_PASSED',Owner='NOT_PASSED',old_credit_transferred=False,remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(N/'review/result-registration.json',registration)
report=R/'docs/reports/jarvis-work-t2-e02-failure-state-result-20261107.md';assert not report.exists()
report.write_text(f'''# E02 失败终态诊断单例结果

诊断能力已实现并在实际失败中保存证据，研究交付仍失败。候选22653fb77445bad4f5b9d9ae789cd35972dcc984，唯一运行{t['run_id']}，独立结果复核FAIL_CONFIRMED。当前候选受控0/3；E02/T2/Owner未通过。

产品631、harness275唯一、接口59，共965项离线检查及独立准备审查通过。当前8B的一例诊断于北京时间15:20:36至15:21:34运行，外层{run['outer_elapsed_seconds']:.7f}秒。原题、四来源和预算保持，没有UI、音频或生产服务控制。

## 新取得的证据

搜索1、GET4；可信诊断确认六页已读取并向模型可见：S1的26–49、53–76、92–115、121–144，S2的20–43，S3的25–48。合格来源S1/S2/S3，S4未读。public tool_results没有inspect记录是失败投影的记录范围，不能误算为实际零读取。

最后可信分支为action，随后一次research_write失败；没有final_answer、写入确认、ACK或research.md。product error为Unlinked or failed END；更具体的research_failure为INVALID_SOURCE_SECTION，错误长度35及摘要匹配源码固定字串Duplicate or unknown source section。应用观察7次原生POST已完成，失败快照余量229.489735秒。该记录不支持把本例归因为“读取后提前final”或超时；更不回填N9历史原因。

私有诊断5188字节，SHA256 {sha(A/'trusted-failure-diagnostic.raw')}；有限结构、公开摘要和原失败隔离已通过实际导出及独立复核。诊断保存成功不是产品验收通过。原写入参数没有留存，不能指出具体重复的来源ID或原文。

## 可修复缺口与下一步

当前phase对每章独立绑定来源及证据，却允许同一source_id出现多章；writer坚持每来源一章。这是代码可证明的契约不一致。按最新授权继续执行jarvis-work-e02-unique-source-sections-plan-20261107.md：在后继候选把来源唯一性前移到生成schema，保留writer/事实/引用门，经离线和独立准备PASS后，最多一例补修后验证。当前候选冻结，本诊断例不重跑。原参数缺失的归因限制保持。

六次读取中四次用于README的现象已记录；该分配与语义覆盖是否足够不能从无文稿直接判PASS。新补修不会自动选择题目答案、合并模型产物或放宽事实检查。失败记录与旧E01/E03信用保持各自候选归属。

清理{t['cleanup']['status']}；七保护身份在记录边界及后续只读观察相符，本例已知进程身份退出、隔离端口关闭。没有连续存活测量。事实与原题覆盖NOT_ASSESSABLE，root witness仍false。

准备manifest {sha(N/'manifest.json')}，1058成员；结果manifest {sha(D/'result-manifest.json')}，50成员；独审SHA256 {sha(reviewpath)}。诊断一次运行和一次复核已消费，当前根剩余0；后继验证仍受新候选独审门约束，尚未分配。

本地提交/tag及UltimaDocs镜像后保存逐字节读回。远端push此前自动审批blocked by policy，本轮没有重试或换通道。
''',encoding='utf8')
statepath=N.parent/'current-run.json';save(N/'verification/current-run-before-closeout.json',load(statepath))
summary='E02候选22653fb：965项离线/准备PASS；唯一诊断58.362秒FAIL，六页已确认后写入遭INVALID_SOURCE_SECTION拒绝，独审FAIL_CONFIRMED；保持0/3，继续已授权来源章节契约最小修复。'
py=R/'tools/venv-openjarvis/Scripts/python.exe'
subprocess.run([str(py),'-I','-B','-X','utf8',str(N/'verification/register_progress.py'),'result','EVIDENCE_BASED_REPAIR_PREPARATION',summary],check=True,stdout=subprocess.DEVNULL)
proposal=R/'docs/plans/jarvis-work-e02-unique-source-sections-plan-20261107.md'
state=load(statepath);state.update(active_report=str(report),active_candidate=registration['candidate'],active_review_agent=None,updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    last_actual_result=registration,e02_failure_state_execution=registration,e02_failure_state_result_registration=str(N/'review/result-registration.json'),
    e02_failure_state_result_registration_sha256=sha(N/'review/result-registration.json'),
    active_result_review=dict(verdict=review['verdict'],path=str(reviewpath),sha256=sha(reviewpath)),
    next_action_scope=dict(authorized=True,decision=str(N/'inputs/direct-user-decision.json'),diagnostic_consumed=True,diagnostic_result_review_consumed=True,
        scope='Evidence-based unique source sections repair, necessary independent reviews and one conditional post-repair verification in a successor candidate',
        diagnostic_remaining=0,conditional_post_repair_cases=1,actual_case_allocation_remaining=0,retry=0,proposal=str(proposal)),
    next_work='Independently review unique-source-section repair plan, implement minimal generation/replay contract alignment in a new candidate, then one conditional verification.')
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
subprocess.run([str(py),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],check=True,stdout=subprocess.DEVNULL)
base=M/'docs/shared/research/ultimaagent-work-capability';mirrors=[]
for src,dst in [(report,base/'reports'/report.name),(proposal,base/'plans'/proposal.name)]:
    assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());assert sha(src)==sha(dst)
    mirrors.append(dict(source=str(src),mirror=str(dst),sha256=sha(src)))
save(N/'verification/result-mirror-readback.json',dict(mirrors=mirrors,remote_synced=False))
paths={N/name for name in rm['files']};paths.update([D/'result-manifest.json',D/'byte-readback.json',reviewpath,N/'review/result-registration.json',report,proposal,statepath,
    R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'])
paths.update(p for p in (N/'verification').iterdir() if p.is_file() and p.name!='preparation-pathspec.txt')
sources={p.relative_to(R).as_posix():sha(p) for p in paths};pathlist=N/'verification/result-pathspec.txt'
pathlist.write_bytes(b'\0'.join(p.encode() for p in sorted(sources))+b'\0')
subprocess.run(['git','-C',str(R),'-c','core.autocrlf=false','add','-f','--pathspec-from-file='+str(pathlist),'--pathspec-file-nul'],check=True)
assert set(git(R,'diff','--cached','--name-only','-z').strip('\0').split('\0'))<=set(sources)
subprocess.run(['git','-C',str(R),'commit','-m','Record failure-state diagnosis and evidence-based handoff repair scope'],check=True,stdout=subprocess.DEVNULL)
main=git(R,'rev-parse','HEAD');tag='ultimaagent-e02-failure-state-result-20261107';subprocess.run(['git','-C',str(R),'tag',tag,main],check=True)
mirrorpaths=[Path(x['mirror']).relative_to(M).as_posix() for x in mirrors]
subprocess.run(['git','-C',str(M),'-c','core.autocrlf=false','add','--',*mirrorpaths],check=True)
assert set(git(M,'diff','--cached','--name-only','-z').strip('\0').split('\0'))==set(mirrorpaths)
subprocess.run(['git','-C',str(M),'commit','-m','Mirror diagnostic failure evidence and unique source sections repair plan'],check=True,stdout=subprocess.DEVNULL)
mirror=git(M,'rev-parse','HEAD');subprocess.run(['git','-C',str(M),'tag',tag,mirror],check=True)
for name,h in sources.items():assert hashlib.sha256(subprocess.check_output(['git','-C',str(R),'show',main+':'+name])).hexdigest()==h,name
for item,name in zip(mirrors,mirrorpaths):assert hashlib.sha256(subprocess.check_output(['git','-C',str(M),'show',mirror+':'+name])).hexdigest()==item['sha256']
for manifest in (rm,load(N/'manifest.json')):
    for name,h in manifest['files'].items():assert sha(N/name)==h,name
for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
result=dict(verdict='PASS_LOCAL_DIAGNOSTIC_FAILURE_PUBLICATION_NOT_ACCEPTANCE',project_commit=main,mirror_commit=mirror,tag=tag,members=len(sources),
    result_manifest_sha256=sha(D/'result-manifest.json'),review_sha256=sha(reviewpath),controlled_passed=0,E02='NOT_PASSED',T2='NOT_PASSED',
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,conditional_post_repair_case_remaining=1,remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(N/'verification/final-result-readback.json',result);print(json.dumps(result))
