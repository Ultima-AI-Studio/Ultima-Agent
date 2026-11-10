"""Seal the exact product preparation and retain acceptance counterexamples."""
from pathlib import Path
import datetime as dt,importlib.util,json,re
N=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checks',N/'verification/verify_offline.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
R,T,C,P=v.R,v.T,v.C,v.P
frozen=v.load(N/'verification/candidate-freeze.json');head=frozen['candidate']
assert head=='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b' and v.git(C,'rev-parse','HEAD').decode().strip()==head
assert not v.git(C,'status','--porcelain').strip()
checked=v.verify();v.save(N/'verification/offline-postcommit-readback.json',checked)
protected=v.load(N/'verification/protected-seven-after.json');assert protected['all_match'] and protected['count']==7
old=v.load(P/'inputs/input-manifest.json');files={}
for name,h in old['files'].items():
    p=Path(name);assert v.sha(p)==h,name
    target=C/p.relative_to(v.OLD) if p.is_relative_to(v.OLD) else p
    files[str(target)]=v.sha(target)
for name,h in checked['source_sha256'].items():
    if Path(name).is_relative_to(C):files[name]=h
sources={name:h for name,h in files.items() if Path(name).is_relative_to(C)}
assert len(sources)==len(old['source_files'])+1==78
v.save(N/'inputs/current-inputs.json',dict(kind='OFFLINE_CLAIM_GENERATION_CANDIDATE',candidate=head,root=str(C),source_files=sources,files=files,model=old['model'],model_digest=old['model_digest'],budgets=old['budgets'],corpus_path=old['corpus_path'],protected_baseline_path=old['protected_baseline_path'],actual_authority=False))
previous_review=v.load(P/'review/independent-result-review.json')
v.save(N/'inputs/semantic-negative-cases.json',dict(kind='ACTUAL_DIAGNOSTIC_COUNTEREXAMPLES_NOT_GENERATED_ANSWERS',run_id=previous_review['run_id'],result_manifest_sha256=previous_review['result_manifest_sha256'],review_sha256=v.sha(P/'review/independent-result-review.json'),observations=previous_review['facts']['diagnostic_observations'],expected='Do not accept generic integration/maintainability/effect claims merely because an issued source/card ID is valid; independent original-question fact and citation review remains necessary',automated_semantic_entailment_claimed=False,actual_acceptance_credit=0))
ledger=C/'.superpowers/sdd/jarvis-work-e02-claim-generation-contract-plan-20261108/progress.md'
(N/'verification/ledger-before-review.md').write_bytes(ledger.read_bytes())
workspace=ledger.parent
packages=list(workspace.glob('*review*'))
for p in packages:
    if p.is_file():
        target=N/'review'/('skill-'+p.name)
        with target.open('xb') as f:f.write(p.read_bytes())
(N/'review/product.diff').write_bytes(v.git(C,'diff','--no-ext-diff',v.BASE,head,'--',*v.ALLOWED))
report=f'''# E02 代码事实生成起点：离线准备

原单wo-ultimaagent-20261101-0021 / T2；候选{head}，父{v.BASE}。本轮按用户call_5411de619a6c4de0bab414126a228c7d授权完成离线最小修复、验证和准备；本报告封存时独立准备审核待办。实际研究/结果复核额度均0，E02仍0/3，T2/Owner未通过。

## 最小变化与作用

仅四个候选文件变化：agent_server.py把既有JSON安全代码claim pattern的精确operation移到字段开头，去除其前面的可选无界文本；work_navigation.py的共享阶段提示同步要求操作名开头；新增contract测试并迁移原JSON测试的生成格式期望。严格schema、卡发行、source/ref绑定、导航、writer、读回/ACK和原预算保持。两个生产文件其余顶层AST均与父候选一致。

该变化尽早满足语法必须包含operation的条件，排除“任意长泛述之后再补操作名”的生成路径。没有证据证明它是本次模型重复的唯一内部原因，也未证明真实研究交付已改善。尾部和非代码自由字符串仍可能过长；历史有限重复原生解析失败保留，因此不机械恢复2000有限重复、不任意减小事实容量。所有返回值仍经原严格解码/长度/边界/事实和交付门。

## 新鲜验证

父代码35项JSON基线通过。新增19项中，原代码14项按预期失败、5项正向边界通过；修改后19项通过，原JSON35项用途保持。旧可先说明后operation的表达仍为strict合法，但新采样拒绝其前缀；序列化引号、反斜杠、中文、美元/Unicode操作名与解码后边界拒绝均保留。旧提示指令即使连贯重算请求摘要，也被共享阶段重放拒绝。

最终22组同一份源码，共1004项去重检查通过，0失败/错误/跳过：994项产品、4项保存诊断/导出兼容、6项固定官方参考转换。沿用delivery两项不适用排除，无新增跳过。原90秒分组、两个测试worker及cold-import审计守卫保持；Python层禁用行为记录为空、必要导入探针闭合。MockTransport与临时测试文件不计实际研究信用。

固定llama.cpp b10488 Python参考转换可处理实际新pattern和writer envelope，没有新增有限大重复或raw JSON通配缺口。此前exploration对4种操作名/3种表达的12次参考转换为设计观察，不另加测试总数；有限2000表达能参考转换不证明原生二进制兼容。未运行native validator或模型，不声称实际推理时延、生成速度或2048 token完整适配已通过。

## 保留的实际缺口

父候选c4caa739-c466-44f3-866b-0c57ea8c5e40仍FAIL_CONFIRMED：FULL3818字符在未闭合claim中重复两句50/49次后length/2048终止，无research.md/write/ACK。独审记录融资背景卡、TODO卡与泛述不匹配，以及日志/时间戳不能证明效率体验效果。本包inputs/semantic-negative-cases.json保留三条原观察；不是自动语义判定器或代写答案。S4未inspect、完整原题覆盖及真实联网门仍未闭合，来源数量或operation匹配均不能代替事实验收。

## 保全和后续

冻结父worktree未变；原准备175成员、结果56成员、实际seal31成员与父产品准备1192成员逐字节复验；1598个上一入口输入、1567依赖及15个无关文件保持。新候选输入映射为78个产品源，完整输入数量{len(files)}。保存的七保护基线与本轮只读核对点匹配，不测量连续存活。本轮没有模型请求、网络请求、UI/音频或生产服务操作。

精确计划已独审PASS_PLAN_ONLY。当前独立准备审核必须绑定此manifest、候选与完整证据，PASS后继续已授权Task3的受控入口准备。新单例仍另行明确分配，不能复用上一例或由准备PASS生成实际权。

计划细化裁定：Task2“5个文件”为文字计数误差，实际按Task1四个明确路径执行，无第五个修改。已完成的TDD用例以源码绑定回执完成ledger验证，未仅为登记再重复执行；随后1004项覆盖是新鲜完整运行。技能工作区保留并归档，先前自动审批拒绝的删除和远端push均不重试。

本地提交/tag/镜像与读回在独审完成后另有回执。真实E02/T2/Owner不通过，原8B/原题/预算和全部历史失败保持。
'''
(N/'preparation-report.md').write_text(report,encoding='utf8',newline='\n')
members=set()
for folder in ('inputs','verification','review','exploration'):
    members.update(p for p in (N/folder).rglob('*') if p.is_file() and '__pycache__' not in p.parts)
for run in (N/'offline').iterdir():
    if run.is_dir():
        members.update(p for p in run.iterdir() if p.is_file())
        members.update(p for p in (run/'snapshot').rglob('*') if p.is_file())
members.update([N/'plan.md',N/'preparation-report.md'])
assert not any((N/name).exists() for name in ('actual','release','controller-authority'))
v.save(N/'manifest.json',dict(kind='OFFLINE_CLAIM_GENERATION_PREPARATION',candidate=head,parent=v.BASE,tests=1004,actual_cases=0,model_calls=0,acceptance_credit=0,actual_authority=False,plan_sha256=v.sha(N/'plan.md'),spec_sha256=v.load(N/'inputs/scope.json')['spec_sha256'],files={p.relative_to(N).as_posix():v.sha(p) for p in sorted(members)},created_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
state_path=T/'current-run.json';state=v.load(state_path)
state.update(phase='SOURCE34_E02_CLAIM_GENERATION_PREPARATION_REVIEW',workflow_status='audit',stage_queue_state='AUDIT',active_review_agent='/root/review_e02_claim_generation_preparation')
state['source34_offline']=dict(root=str(N),status='FROZEN_PENDING_INDEPENDENT_PREPARATION',candidate=head,parent=v.BASE,tests=1004,manifest_sha256=v.sha(N/'manifest.json'),actual_case_allocation=0,result_review_allocation=0,model_calls=0)
state_path.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
index=Path('H:/UltimaAI/_shared/queue/global-queue-index.md');text,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | audit | E02候选'+head[:7]+'完成1004项离线检查，封存后独立准备审核；actual/model0，旧失败及原验收保持。 |',index.read_text('utf8'));assert count==1;index.write_text(text,encoding='utf8',newline='\n')
print(json.dumps(dict(candidate=head,manifest_sha256=v.sha(N/'manifest.json'),members=len(members),source_pins=len(sources),input_pins=len(files),tests=1004,actual=0)))
