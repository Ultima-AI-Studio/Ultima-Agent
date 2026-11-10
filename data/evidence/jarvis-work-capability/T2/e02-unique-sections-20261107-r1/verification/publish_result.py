"""Publish the independently reviewed first failure without a new run allocation."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];R=N.parents[4];M=Path('H:/UltimaAI/ultima-docs-repo')
A=N/'actual/E02-controlled-1';D=N/'review/result-inputs';S=N/'review/native-log-supplement'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,value):
    with p.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
def git(repo,*args):return subprocess.check_output(['git','-C',str(repo),*args],text=True,encoding='utf8').strip()
reviewpath=N/'review/independent-result-review.json';review=load(reviewpath)
assert review['reviewer']=='root-independent' and review['verdict']=='FAIL_CONFIRMED'
assert review['result_manifest_sha256']==sha(D/'result-manifest.json')=='c00e597832d5b739043b75ee051ee46265a3d5c9b7c43505fa05e7722bd31bfd'
assert review['actual_run_authorized'] is False and review['acceptance_credit']==0 and review['new_run_allowance']==0
assert sha(S/'manifest.json')=='9e542f61da51f16a4d5625650e2d2fa38a5c4d597cec4859612cf051e6295db0'
assert review['supplemental_manifest_sha256']==sha(S/'manifest.json')
assert review['preparation_manifest_sha256']==sha(N/'manifest.json')
assert review['candidate']==load(N/'manifest.json')['candidate']
manifests=[load(N/'manifest.json'),load(D/'result-manifest.json'),load(S/'manifest.json')]
for manifest in manifests:
    for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
for name,digest in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
assert not git(R,'diff','--cached','--name-only') and not git(M,'diff','--cached','--name-only')
p=load(A/'product-result.json');t=load(A/'terminal.json');o=load(N/'release/root-outcome.json')
run=load(N/'release/tool-execution-receipt.json');d=load(A/'trusted-failure-diagnostic.raw')
readonly=load(D/'readonly-closeout.json');native=load(S/'capture.json');candidate=load(N/'manifest.json')['candidate']
assert t['run_id']==review['run_id']=='be79869f-10e5-4c0d-96a9-144cd5967c12'
assert o['status']=='FAIL' and p['status']=='failed' and p['error']=='Research HTTP status'
assert not p['artifacts'] and not list(A.rglob('research.md')) and run['invocations']==1 and run['retry']==0
assert sha(A/'trusted-failure-diagnostic.raw')=='26768a6d45180251f5532eaebfd72688052a7ad3af50f6b203ae3ac1ecf8b297'
confirmed=sum(x['confirmed'] is True for x in d['pages']);visible=sum(x['visible'] is True for x in d['pages'])
assert (confirmed,visible,d['branch'])==(6,5,'unvalidated_response')
assert not d['write_confirmed'] and not d['ack_confirmed'] and d['final_answer'] is None
assert d['budget']['native_posts']==7 and d['budget']['completed_posts']==6
count=lambda name:sum(x.get('tool_name')==name and x.get('success') is True for x in p['tool_results'])
registration=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',purpose='post_repair_verification',
    run_id=t['run_id'],candidate=candidate,model='qwen3-8b-uncensored',question_id=run['question_id'],result='FAIL',
    independent_review=review['verdict'],review_path=str(reviewpath),review_sha256=sha(reviewpath),
    result_manifest_sha256=sha(D/'result-manifest.json'),supplemental_manifest_sha256=sha(S/'manifest.json'),
    terminal_sha256=sha(A/'terminal.json'),product_result_sha256=sha(A/'product-result.json'),
    entry_invocations=1,work_cli_attempts=t['work_cli_attempts'],controlled_search_success=count('ultima_work_web_search'),controlled_GET_success=count('ultima_work_http_get'),
    confirmed_inspect_pages=confirmed,visible_inspect_pages=visible,public_successful_inspect_records=count('ultima_work_research_inspect'),
    inspect_count_basis='trusted failure diagnostic confirmed and visible states, not incomplete public tool_results',
    write_attempts=sum(x.get('tool_name')=='ultima_work_research_write' for x in p['tool_results']),successful_write_count=count('ultima_work_research_write'),
    application_native_POST_attempts=t['application_native_POST_attempts'],completed_native_posts=d['budget']['completed_posts'],actual_native_start_count=None,
    research_artifacts=0,outer_elapsed_seconds=run['outer_elapsed_seconds'],cleanup=t['cleanup']['status'],root_witness_eligible=o['outcome']['witness']['eligible'],
    product_error=p['error'],failure_diagnostic_sha256=sha(A/'trusted-failure-diagnostic.raw'),failure_diagnostic_bytes=(A/'trusted-failure-diagnostic.raw').stat().st_size,
    branch=d['branch'],eligible_source_ids=d['eligible_source_ids'],eligibility_basis='confirmed card-bearing pages; does not imply all pages visible',
    selected_pages=[dict(source_id=x['source_id'],start=x['requested_start'],range=x['range'],confirmed=x['confirmed'],visible=x['visible']) for x in d['pages']],
    budget=d['budget'],write_confirmed=False,ack_confirmed=False,final_answer_preserved=False,
    supplemental_provider_observation=dict(status_counts=native['status_counts'],last_generation_tokens=2048,parser_message=native['parser_message'],
        matched_case_ids=len(native['matching_case_evidence_ids']),trusted_transport_receipt=False,precise_cause_proven=False),
    facts='NOT_ASSESSABLE_NO_ARTIFACT',original_question_coverage='NOT_ASSESSABLE_NO_ARTIFACT',actual_source_uniqueness_verified=False,
    protected_at_recorded_boundaries=sha(A/'boundary-before.json')==sha(A/'boundary-after.json'),protected_after_readonly=readonly['protected_all_equal'],continuous_liveness_measured=False,
    acceptance_credit=0,controlled_passed=0,controlled_required=3,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    diagnostic_remaining=0,post_repair_case_remaining=0,retry=0,next_case_released=False,E02='NOT_PASSED',T2='NOT_PASSED',Owner='NOT_PASSED',
    old_credit_transferred=False,remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(N/'review/result-registration.json',registration)
proposal=R/'docs/plans/jarvis-work-e02-native-response-compatibility-followup-20261107.md'
report=R/'docs/reports/jarvis-work-t2-e02-unique-sections-result-20261107.md';assert not report.exists()
report.write_text(f'''# E02 读取到交付补修后的单例结果

失败诊断和来源章节契约补修已落盘，但真实研究仍未交付。候选{candidate}，运行{t['run_id']}，独立结果复核FAIL_CONFIRMED。当前候选受控0/3；E02/T2/Owner仍未通过。

## 已完成的工程工作

前一诊断候选22653fb实际保存了六页选择和action分支，暴露phase允许重复来源章节而writer拒绝的契约不一致。原写入参数没有留存，具体重复来源和unknown分支的归因限制保留。

后继2b42b3e把一来源一章节的规则前移到生成schema，保留合法3至5来源子集及同源多页事实；生成与重放共用本地引用绑定，重放先核对可信schema再解析引用。原writer、事实、operation、文件事务、预算均保留。另修复内部计时字符串误中PII手机号规则，使用v2整数微秒诊断投影，实际时钟和55秒准入不变。664产品、275去重harness、59接口，共998项当前字节检查及独立准备审查通过。

## 这次真实结果

唯一实跑于北京时间16:08:39至16:10:39，外层{run['outer_elapsed_seconds']:.7f}秒，使用当前社区8B和原题四来源。搜索1、GET4；可信诊断确认六页：S1的26–49、53–76、92–115、121–144，S2的20–43，S3的25–48。五页visible，最后S3页已confirmed但visible=false，不能将两个状态合并。公开tool_results无inspect行不等于没有读取。

第七次原生请求报Research HTTP status，产品状态failed；诊断分支unvalidated_response，七次POST中六次完成。没有有效final_answer、写入调用、ACK或research.md。失败时余量167.775139秒，原55秒准入仍开放；本例不能归因为总时限耗尽。诊断v2实际导出5197字节，SHA256 {sha(A/'trusted-failure-diagnostic.raw')}；诊断成功只证明失败可观测性，不给交付信用。来源章节修复尚未实际到达writer验证。

## 原生日志补充与限度

只读截取既有Ollama日志并独立封存，未调用新模型或操作服务。同时间段六次/api/chat返回200，最后一次在16:10:30返回500；最后一代记录2048 tokens和unparsed peg-native output。截取中五个证据ID匹配本例、与前例不匹配。日志显示未解析的局部输出及重复关闭思考标签，但这些文本不是受信响应或文稿，不能用于拼接交付或验收事实。

这是时间和内容相关的服务日志补充，不是请求绑定的完整transport receipt。尚不能确定具体模板、schema或原生解析器缺陷，也不证明提高token上限就会解决。下一步应先核对当前8B的原生结构化响应兼容性和HTTP失败回执，按已有证据形成最小修复；具体范围见jarvis-work-e02-native-response-compatibility-followup-20261107.md。该提案不分配新实跑。

## 保护与验收状态

清理{t['cleanup']['status']}；本例受管进程在记录和只读观察时已退出，隔离端口关闭。七保护身份在前后记录及后续只读观察相符，没有连续存活测量。原题、四来源、8B摘要、时限和调用预算保持；无UI、音频、生产服务操作或14B。

没有文稿，事实和原题覆盖NOT_ASSESSABLE；root witness=false；受控0/3，旧E01/E03信用不迁移。诊断一次和补修后一次均已使用，失败没有重试，本序列实际额度及结果复核额度均为0。

准备manifest {sha(N/'manifest.json')}（2501成员）；结果manifest {sha(D/'result-manifest.json')}（49成员）；补充manifest {sha(S/'manifest.json')}；独立结果复核SHA256 {sha(reviewpath)}。全部保存原始结果，本地提交/tag及UltimaDocs镜像后逐字节读回。远端push此前被自动审批blocked by policy，本轮不重试或换通道。
''',encoding='utf8')
statepath=N.parent/'current-run.json';save(N/'verification/current-run-before-closeout.json',load(statepath))
summary='E02候选2b42b3e：998项离线/准备PASS；补修后单例119.564秒FAIL，六页confirmed/五页visible后原生HTTP失败，无文稿；独审FAIL_CONFIRMED，0/3，本序列额度耗尽；下一步原生响应兼容性排查。'
py=R/'tools/venv-openjarvis/Scripts/python.exe'
subprocess.run([str(py),'-I','-B','-X','utf8',str(N/'verification/register_progress.py'),'result','blocked',summary],check=True,stdout=subprocess.DEVNULL)
state=load(statepath);state.update(active_report=str(report),active_candidate=candidate,active_review_agent=None,updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    last_actual_result=registration,e02_unique_sections_execution=registration,e02_unique_sections_result_registration=str(N/'review/result-registration.json'),
    e02_unique_sections_result_registration_sha256=sha(N/'review/result-registration.json'),current_e02_controlled_passed=0,
    active_result_review=dict(verdict=review['verdict'],path=str(reviewpath),sha256=sha(reviewpath)),
    next_action_scope=dict(authorized=False,scope='No further actual case allocated in completed diagnostic and repair sequence',diagnostic_consumed=True,
        post_repair_consumed=True,diagnostic_remaining=0,conditional_post_repair_cases=0,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,retry=0,proposal=str(proposal)),
    next_work='Read-only/offline native-response compatibility diagnosis as proposed; new actual case is not allocated.',
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,e02_execution_released=False,live_gate_released=False,next_stage_released=False)
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
subprocess.run([str(py),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],check=True,stdout=subprocess.DEVNULL)
base=M/'docs/shared/research/ultimaagent-work-capability';mirrors=[]
for src,dst in [(report,base/'reports'/report.name),(proposal,base/'plans'/proposal.name)]:
    assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());assert sha(src)==sha(dst)
    mirrors.append(dict(source=str(src),mirror=str(dst),sha256=sha(src)))
save(N/'verification/result-mirror-readback.json',dict(mirrors=mirrors,remote_synced=False))
paths={N/name for manifest in manifests[1:] for name in manifest['files']}
paths.update([D/'result-manifest.json',D/'byte-readback.json',S/'manifest.json',reviewpath,N/'review/result-registration.json',report,proposal,statepath,
    R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',N/'preparation-publication.log'])
paths.update(p for p in (N/'verification').iterdir() if p.is_file() and p.name!='preparation-pathspec.txt')
sources={p.relative_to(R).as_posix():sha(p) for p in paths};pathlist=N/'verification/result-pathspec.txt'
pathlist.write_bytes(b'\0'.join(p.encode() for p in sorted(sources))+b'\0')
subprocess.run(['git','-C',str(R),'-c','core.autocrlf=false','add','-f','--pathspec-from-file='+str(pathlist),'--pathspec-file-nul'],check=True)
assert set(git(R,'diff','--cached','--name-only','-z').strip('\0').split('\0'))<=set(sources)
subprocess.run(['git','-C',str(R),'commit','-m','Record bounded handoff repair failure and native parser evidence'],check=True,stdout=subprocess.DEVNULL)
main=git(R,'rev-parse','HEAD');tag='ultimaagent-e02-unique-sections-result-20261107';subprocess.run(['git','-C',str(R),'tag',tag,main],check=True)
mirrorpaths=[Path(x['mirror']).relative_to(M).as_posix() for x in mirrors]
subprocess.run(['git','-C',str(M),'-c','core.autocrlf=false','add','--',*mirrorpaths],check=True)
assert set(git(M,'diff','--cached','--name-only','-z').strip('\0').split('\0'))==set(mirrorpaths)
subprocess.run(['git','-C',str(M),'commit','-m','Mirror handoff repair result and native response followup'],check=True,stdout=subprocess.DEVNULL)
mirror=git(M,'rev-parse','HEAD');subprocess.run(['git','-C',str(M),'tag',tag,mirror],check=True)
for name,digest in sources.items():assert hashlib.sha256(subprocess.check_output(['git','-C',str(R),'show',main+':'+name])).hexdigest()==digest,name
for item,name in zip(mirrors,mirrorpaths):assert hashlib.sha256(subprocess.check_output(['git','-C',str(M),'show',mirror+':'+name])).hexdigest()==item['sha256']
for manifest in manifests:
    for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
for name,digest in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==digest,name
result=dict(verdict='PASS_LOCAL_RESULT_PUBLICATION_NOT_ACCEPTANCE',project_commit=main,mirror_commit=mirror,tag=tag,members=len(sources),
    result_manifest_sha256=sha(D/'result-manifest.json'),supplemental_manifest_sha256=sha(S/'manifest.json'),review_sha256=sha(reviewpath),
    controlled_passed=0,E02='NOT_PASSED',T2='NOT_PASSED',actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    conditional_post_repair_case_remaining=0,remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(N/'verification/final-result-readback.json',result);print(json.dumps(result))
