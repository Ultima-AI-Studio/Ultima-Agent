"""Seal offline evidence for a fresh read-only preparation reviewer."""
from pathlib import Path
import datetime as dt,importlib.util,json
spec=importlib.util.spec_from_file_location('offline_readback',Path(__file__).with_name('verify_offline.py'))
v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
N,R,T,C,OLD,BASE,ALLOWED,git,sha,load,save,verify=v.N,v.R,v.T,v.C,v.OLD,v.BASE,v.ALLOWED,v.git,v.sha,v.load,v.save,v.verify
head=git(C,'rev-parse','HEAD').decode().strip();frozen=load(N/'verification/candidate-freeze.json')
assert head==frozen['candidate'] and git(C,'rev-parse','HEAD^').decode().strip()=='47ac3a464ca15e01311d5739eda53b2a32d8783c'
assert not git(C,'status','--porcelain').strip()
checked=verify();save(N/'verification/offline-postcommit-readback.json',checked)
protected=load(N/'verification/protected-seven-after.json');assert protected['all_match'] and protected['count']==7
plan=R/'docs/plans/jarvis-work-e02-output-structure-diagnostics-plan-20261108.md'
proposal=R/'docs/plans/jarvis-work-e02-output-structure-diagnostics-proposal-20261107.md'
assert sha(plan)==sha(N/'plan.md')==load(N/'review/independent-plan-review-closure.json')['plan_sha256']
assert sha(proposal)==load(N/'inputs/scope.json')['spec_sha256']
prior=T/'e02-output-budget-controlled-preparation-20261107-r1'
old=load(prior/'inputs/input-manifest.json');files={}
for name,h in old['files'].items():
    p=Path(name);assert sha(p)==h,name
    target=C/p.relative_to(OLD) if p.is_relative_to(OLD) else p
    files[str(target)]=sha(target)
files.update({name:h for name,h in checked['source_sha256'].items() if Path(name).is_relative_to(C)})
sources={name:h for name,h in files.items() if Path(name).is_relative_to(C)}
assert len(sources)==len(old['source_files'])+1==77
save(N/'inputs/current-inputs.json',dict(kind='OFFLINE_OUTPUT_STRUCTURE_DIAGNOSTICS_CANDIDATE',candidate=head,
    root=str(C),source_files=sources,files=files,model=old['model'],model_digest=old['model_digest'],budgets=old['budgets'],
    corpus_path=old['corpus_path'],protected_baseline_path=old['protected_baseline_path'],actual_authority=False))
ledger=C/'.superpowers/sdd/jarvis-work-e02-output-structure-diagnostics-plan-20261108/progress.md'
(N/'verification/ledger-before-review.md').write_bytes(ledger.read_bytes())
(N/'review/product.diff').write_bytes(git(C,'diff','--no-ext-diff',BASE,head,'--',*ALLOWED))
batch=load(N/'verification/final-regression-batch.json')
report=f'''# E02 输出结构诊断离线准备

原单 wo-ultimaagent-20261101-0021 / T2；候选 `{head}`，父 `47ac3a464ca15e01311d5739eda53b2a32d8783c`，原基线 `{BASE}`。本包仅补充失败诊断，E02/T2/Owner 均未通过，真实研究与结果复核额度为0。

已确认的缺口：原两例第7次HTTP200响应均因length被拒绝，eval_count=max_tokens=2048；旧包没有正文，不能据此认定JSON必定截断或定位到某个字段。既有程序已负责将事实结构绑定来源、生成Markdown并完成单次写入/读回/ACK；本轮没有更换这条交付链。

新增闭合v5保留同请求的实际flags/options、strict/sampler摘要、来源/引用数量；message字段与content/thinking类型/长度/SHA；完整content的严格JSON状态、受限错误位置及完整JSON的schema/结构统计。thinking和未知字段值不留正文。安全扫描后优先FULL，最终编码超出16KiB时保留带偏移的头尾/错误附近片段；不能容纳或诊断异常则保留原v4。原请求、schema、工具权限、length拒绝、写入/ACK和公共未交付回复保持。

离线结果：{checked['tests']}项去重检查通过，其中{checked['product_tests']}项产品检查、{checked['compatibility_tests']}项保存包/原导出器兼容；20组同源码字节，0失败/错误/跳过。仅沿用原delivery两项不适用排除。r1的27项初始RED、6项补充RED及NEEDS_FIXES均保留；本r2对PREP-STATE-01新增9项状态关联负例及1项解析器失败注入正例。首跑10项失败中9项确证校验缺口；另1项是测试错误假定1500层JSON必触发解析递归异常，实际能解析，已改为确定性失败注入。51项结构检查覆盖完整/残缺JSON、严格解析、类型混淆、实际raw_bytes绑定、片段编码膨胀、错误位置、原v4回退、畸形Unicode及16384恰好/超一字节边界；合成片段/大小及故障注入不是实际模型输出。

测试样例纠正：最初以JSON属性形式写的password未命中原开源扫描器的assignment规则。核对原规则后将样例改为它确实支持的password赋值表达式；扫描器和准入策略不改，不宣称新增了任意密钥识别能力。原131项native检查用途均保留，仅升级v5版本断言和legacy去扩展构造。旧failure共享helper没有修改。

保全：N19/N21实际失败清单、封存索引及准备包逐文件复验；{checked['dependency_pins']}项原依赖/输入摘要、{checked['foreign_tracked_files']}个无关改动保持。父候选仍冻结。前后核对点7个保护进程的PID/创建时间/路径均一致；没有测量连续存活或运行性能。

本轮actual/model/UI/audio/service操作均为0。当前8B、原题四来源、完整事实/引用/覆盖/文件要求，以及原调用、输出、时间和字节预算保持。旧E01/E03不计入新候选。独立准备审查尚待精确本包复核，下一步只有其PASS后才准备新入口；新真实研究仍需用户明确分配。旧push自动审批阻断保持，本轮不重试远端。
'''
(N/'preparation-report.md').write_text(report,encoding='utf8',newline='\n')
members=set()
for folder in ('inputs','verification','review'):
    members.update(p for p in (N/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for run in (N/'offline').iterdir():
    if not run.is_dir():continue
    members.update(p for p in run.iterdir() if p.is_file())
    members.update(p for p in (run/'snapshot').rglob('*') if p.is_file())
members.update([N/'plan.md',N/'preparation-report.md',N/'review-fix-plan.md'])
assert not any((N/name).exists() for name in ('actual','release','controller-authority'))
save(N/'manifest.json',dict(kind='OFFLINE_OUTPUT_STRUCTURE_DIAGNOSTICS_PREPARATION',candidate=head,parent='47ac3a464ca15e01311d5739eda53b2a32d8783c',
    tests=checked['tests'],actual_cases=0,model_calls=0,acceptance_credit=0,actual_authority=False,
    plan_sha256=sha(plan),spec_sha256=sha(proposal),created_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    files={p.relative_to(N).as_posix():sha(p) for p in sorted(members)}))
state=load(T/'current-run.json');state.update(phase='SOURCE32_R2_E02_OUTPUT_STRUCTURE_PREPARATION_REVIEW',
    active_review_agent='/root/review_e02_output_structure_preparation',source32_offline=dict(status='FROZEN_PENDING_INDEPENDENT_PREPARATION',
    candidate=head,parent='47ac3a464ca15e01311d5739eda53b2a32d8783c',tests=checked['tests'],manifest_sha256=sha(N/'manifest.json'),actual_case_allocation=0,result_review_allocation=0,model_calls=0))
(T/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(candidate=head,manifest_sha256=sha(N/'manifest.json'),members=len(members),tests=checked['tests'],actual_allocation=0)))
