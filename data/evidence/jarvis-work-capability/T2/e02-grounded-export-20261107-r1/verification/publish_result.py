"""Register the independently reviewed first failure; no execution authority."""
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
assert review['result_manifest_sha256']==sha(D/'result-manifest.json')=='dcbabe28aa84766eca9e959f2f51713962b9e775e653263f8e47f05b7699ec77'
for name,h in rm['files'].items():assert sha(N/name)==h,name
for name,h in load(N/'manifest.json')['files'].items():assert sha(N/name)==h,name
for name,h in load(N/'inputs/input-manifest.json')['files'].items():assert sha(Path(name))==h,name
for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
assert not git(R,'diff','--cached','--name-only') and not git(M,'diff','--cached','--name-only')
p=load(A/'product-result.json');t=load(A/'terminal.json');o=load(N/'release/root-outcome.json');run=load(N/'release/tool-execution-receipt.json');readonly=load(D/'readonly-closeout.json')
assert o['status']=='FAIL' and not list(A.rglob('research.md')) and run['invocations']==1
count=lambda name:sum(x.get('tool_name')==name and x.get('success') is True for x in p['tool_results'])
registration=dict(schema=1,work_order='wo-ultimaagent-20261101-0021',stage='T2',case='E02-controlled-1',run_id=t['run_id'],candidate=load(N/'manifest.json')['candidate'],model='qwen3-8b-uncensored',
    question_id=run['question_id'],result='FAIL',original_terminal=t['overall'],independent_review=review['verdict'],review_path=str(reviewpath),review_sha256=sha(reviewpath),
    result_manifest_sha256=sha(D/'result-manifest.json'),terminal_sha256=sha(A/'terminal.json'),product_result_sha256=sha(A/'product-result.json'),
    entry_invocations=1,work_cli_attempts=t['work_cli_attempts'],controlled_search_success=count('ultima_work_web_search'),controlled_GET_success=count('ultima_work_http_get'),
    successful_inspect_count=count('ultima_work_research_inspect'),successful_write_count=count('ultima_work_research_write'),application_native_POST_attempts=t['application_native_POST_attempts'],actual_native_start_count=None,
    research_artifacts=0,outer_elapsed_seconds=run['outer_elapsed_seconds'],cleanup=t['cleanup']['status'],root_witness_eligible=o['outcome']['witness']['eligible'],product_error=p['error'],
    facts='NOT_ASSESSABLE_NO_ARTIFACT',original_question_coverage='NOT_ASSESSABLE_NO_ARTIFACT',export_success_path_live_validated=False,
    protected_at_recorded_boundaries=(sha(A/'boundary-before.json')==sha(A/'boundary-after.json')),protected_after_readonly=readonly['protected_all_equal'],continuous_liveness_measured=False,
    acceptance_credit=0,controlled_passed=0,controlled_required=3,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,retry=0,next_case_released=False,
    E02='NOT_PASSED',T2='NOT_PASSED',Owner='NOT_PASSED',old_credit_transferred=False,remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(N/'review/result-registration.json',registration)
report=R/'docs/reports/jarvis-work-t2-e02-grounded-export-result-20261107.md';assert not report.exists()
report.write_text(f'''# E02 grounded-export 单例与独立复核结果

本轮约定范围已完成，产品验收仍失败。候选 `{registration['candidate']}`；唯一运行 `{t['run_id']}`；独立结果复核 **FAIL_CONFIRMED**。当前候选受控 **0/3**，E02/T2/Owner 均未通过。

## 实际完成

- 有限导出诊断、两个官方 ModelDetails 整数字段兼容、通用文档目录标签和研究依据说明已实现。产品608、harness268唯一、接口59，共935项离线检查通过；原两项排除仍保留。准备独审PASS，产品候选与项目/镜像本地提交和tag已保存。
- 用户本会话直接授权绑定后，仅调用一次原入口。北京时间14:43:52至14:44:34，外层记录 {run['outer_elapsed_seconds']:.7f} 秒；不是超时失败，原时限未放宽。
- 原题四来源：search {registration['controlled_search_success']}、GET {registration['controlled_GET_success']}、inspect {registration['successful_inspect_count']} 成功；应用观察原生POST {registration['application_native_POST_attempts']}。全局原生推理次数未知，不将事件数冒充全局调用数。

## 未完成及证据边界

产品报 `{p['error']}`。没有 research_write、research.md 或交付ACK；原始失败和首个结果原位保留，未重跑。没有文稿可做逐事实及任务覆盖评估，相关结果是 NOT_ASSESSABLE，不能因没有发现错误而记为通过。

源码允许在写入前返回 final_answer，只有写入后的ACK会封存最终 runtime proof；失败处理又覆盖原回复。控制流支持“读取后提前结束”的解释，但最后回答原文与具体选页轨迹没有保存，不能断言拒绝原因或模型动机，也不能声称已复现并解决它。新的导出成功路径本次未到达，因此元数据兼容修复只有离线证据，没有本例真实成功证明。

清理 **{t['cleanup']['status']}**，本例六个进程身份在清理回执和后续只读观察均已退出，隔离18799端口关闭。七个保护身份在记录边界及后续观察相符；没有连续存活测量，不升级为全程保证。没有UI、音频或生产服务控制。

## 封存与下一步

准备manifest SHA256 `{sha(N/'manifest.json')}`，1013成员；结果manifest SHA256 `{sha(D/'result-manifest.json')}`，46成员；结果独审 SHA256 `{sha(reviewpath)}`。旧N8失败、旧候选和无关工作文件读回保持；旧269aca5的E01/E03通过不转移到本候选。

本轮一次运行和一次结果独审均已消费，剩余0；失败后本序列结束。下一步先按 `docs/plans/jarvis-work-e02-early-final-diagnostic-proposal-20261107.md` 定义失败时的有限最终分支/选页诊断，确认原因后再做最小修复；该文件仅提案，没有新代码、测试或实际分配。仍只使用当前社区8B，不使用14B，不提前进入T3–T5。

本结果及提案完成本地提交、tag和UltimaDocs镜像后另存字节读回。远端推送未完成：此前自动审批以 blocked by policy 拒绝，本轮未重试或换通道。
''',encoding='utf8')
statepath=N.parent/'current-run.json';save(N/'verification/current-run-before-closeout.json',load(statepath))
summary='E02候选9e2716a：935项离线/准备PASS；唯一8B例42.287秒FAIL，search1/GET4/inspect6、无文稿，独审FAIL_CONFIRMED，受控0/3；本范围完成额度0，E02/T2未过。'
py=R/'tools/venv-openjarvis/Scripts/python.exe'
subprocess.run([str(py),'-I','-B','-X','utf8',str(N/'verification/register_progress.py'),'result','blocked',summary],check=True,stdout=subprocess.DEVNULL)
state=load(statepath);state.update(active_candidate=registration['candidate'],workflow_status='AUTHORIZED_SEQUENCE_COMPLETE_E02_FAILED',active_review_agent=None,
    current_e02_controlled_passed=0,e02_execution_released=False,live_gate_released=False,next_stage_released=False,
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,
    e02_grounded_export_execution=registration,e02_grounded_export_result_registration=str(N/'review/result-registration.json'),
    e02_grounded_export_result_registration_sha256=sha(N/'review/result-registration.json'),
    active_result_review=dict(verdict=review['verdict'],path=str(reviewpath),sha256=sha(reviewpath)),
    next_action_scope=dict(authorized=False,previous_scope_completed=True,previous_single_case_consumed=True,previous_single_result_review_consumed=True,
        actual_case_allocation=0,result_review_allocation=0,retry=0,proposal=str(R/'docs/plans/jarvis-work-e02-early-final-diagnostic-proposal-20261107.md')))
statepath.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
subprocess.run([str(py),'-I','-B','-X','utf8','H:/UltimaAI/_shared/queue/queue-status-gen.py'],check=True,stdout=subprocess.DEVNULL)
base=M/'docs/shared/research/ultimaagent-work-capability';mirrors=[]
proposal=R/'docs/plans/jarvis-work-e02-early-final-diagnostic-proposal-20261107.md'
for src,dst in [(report,base/'reports'/report.name),(proposal,base/'plans'/proposal.name)]:
    assert not dst.exists();dst.parent.mkdir(parents=True,exist_ok=True);dst.write_bytes(src.read_bytes());assert sha(src)==sha(dst)
    mirrors.append(dict(source=str(src),mirror=str(dst),sha256=sha(src)))
save(N/'verification/result-mirror-readback.json',dict(mirrors=mirrors,remote_synced=False))
paths={N/name for name in rm['files']};paths.update([D/'result-manifest.json',D/'byte-readback.json',reviewpath,N/'review/result-registration.json',report,proposal,statepath,
    R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'])
paths.update(p for p in (N/'verification').iterdir() if p.is_file() and p.name!='preparation-pathspec.txt')
sources={p.relative_to(R).as_posix():sha(p) for p in paths}
pathlist=N/'verification/result-pathspec.txt';pathlist.write_bytes(b'\0'.join(p.encode() for p in sorted(sources))+b'\0')
subprocess.run(['git','-C',str(R),'-c','core.autocrlf=false','add','-f','--pathspec-from-file='+str(pathlist),'--pathspec-file-nul'],check=True)
assert set(git(R,'diff','--cached','--name-only','-z').strip('\0').split('\0'))<=set(sources)
subprocess.run(['git','-C',str(R),'commit','-m','Record grounded export single-case failure and independent review'],check=True,stdout=subprocess.DEVNULL)
main=git(R,'rev-parse','HEAD');tag='ultimaagent-e02-grounded-export-result-20261107';subprocess.run(['git','-C',str(R),'tag',tag,main],check=True)
mirrorpaths=[Path(x['mirror']).relative_to(M).as_posix() for x in mirrors]
subprocess.run(['git','-C',str(M),'-c','core.autocrlf=false','add','--',*mirrorpaths],check=True)
assert set(git(M,'diff','--cached','--name-only','-z').strip('\0').split('\0'))==set(mirrorpaths)
subprocess.run(['git','-C',str(M),'commit','-m','Mirror grounded export result and bounded diagnostic proposal'],check=True,stdout=subprocess.DEVNULL)
mirror=git(M,'rev-parse','HEAD');subprocess.run(['git','-C',str(M),'tag',tag,mirror],check=True)
for name,h in sources.items():assert hashlib.sha256(subprocess.check_output(['git','-C',str(R),'show',main+':'+name])).hexdigest()==h,name
for item,name in zip(mirrors,mirrorpaths):assert hashlib.sha256(subprocess.check_output(['git','-C',str(M),'show',mirror+':'+name])).hexdigest()==item['sha256']
for name,h in rm['files'].items():assert sha(N/name)==h,name
for name,h in load(N/'manifest.json')['files'].items():assert sha(N/name)==h,name
for name,h in load(N/'inputs/unrelated-working-tree.json')['files'].items():assert sha(R/name)==h,name
result=dict(verdict='PASS_LOCAL_FAILURE_PUBLICATION_NOT_ACCEPTANCE',project_commit=main,mirror_commit=mirror,tag=tag,members=len(sources),
    result_manifest_sha256=sha(D/'result-manifest.json'),review_sha256=sha(reviewpath),controlled_passed=0,E02='NOT_PASSED',T2='NOT_PASSED',
    actual_case_allocation_remaining=0,result_review_allocation_remaining=0,remote_synced=False,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
save(N/'verification/final-result-readback.json',result);print(json.dumps(result))
