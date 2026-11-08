"""Seal the evidence-first candidate with complete offline receipts and prior failures."""
from pathlib import Path
import datetime as dt,importlib.util,json
N=Path(__file__).resolve().parents[1]
spec=importlib.util.spec_from_file_location('checks',N/'verification/verify_offline.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
R,T,C,P=v.R,v.T,v.C,v.P
checked=v.verify();head=v.load(N/'verification/candidate-freeze.json')['candidate']
assert v.git(C,'rev-parse','HEAD').decode().strip()==head and not v.git(C,'status','--porcelain').strip()
v.save(N/'verification/offline-postcommit-readback.json',checked)
old=v.load(P/'inputs/input-manifest.json');files={}
for name,h in old['files'].items():
    p=Path(name);assert v.sha(p)==h,name
    target=C/p.relative_to(v.OLD) if p.is_relative_to(v.OLD) else p
    files[str(target)]=v.sha(target)
for name,h in checked['source_sha256'].items():
    if Path(name).is_relative_to(C):files[name]=h
sources={p:h for p,h in files.items() if Path(p).is_relative_to(C)}
assert len(sources)==len(old['source_files'])+1==79
v.save(N/'inputs/current-inputs.json',dict(kind='OFFLINE_EVIDENCE_FIRST_AND_SOURCE_RESERVE_CANDIDATE',candidate=head,root=str(C),source_files=sources,files=files,model=old['model'],model_digest=old['model_digest'],budgets=old['budgets'],corpus_path=old['corpus_path'],protected_baseline_path=old['protected_baseline_path'],actual_authority=False))
ledger=R/'.superpowers/sdd/jarvis-work-e02-source-grounding-coverage-plan-20261108/progress.md'
with ledger.open('a',encoding='utf8') as f:f.write('\n- Task1 complete: RED 12 assertion failures/2 passes; GREEN and final 1022 checks pass. Two production functions plus shared prompt changed; five existing test files migrated and one new test file.\n- Ruling: full regression exposed old sampler-property assumptions in source-reference tests and a six-read diagnostic fixture that reselected covered sources. Their narrow migration is within the approved offline repair; errors and previous batch retained. No test purpose or rejection gate removed.\n- Task2: frozen '+head+'; final preparation independent review pending; Task3 pending.\n')
(N/'verification/ledger-before-review.md').write_bytes(ledger.read_bytes())
(N/'review/product.diff').write_bytes(v.git(C,'diff','--no-ext-diff',v.BASE,head,'--',*v.ALLOWED))
report=f'''# E02 逐来源证据表达与读取覆盖：离线准备

原单wo-ultimaagent-20261101-0021 / T2。候选{head}，父{v.BASE}。按用户call_3d33440cc40c401ea7a2cf11c8bc2bcf完成离线修复与验证；本报告封存时准备独审待办。当前8B、原题、四来源和全部原预算保持，actual/model0，E02 0/3、T2/Owner未通过。

## 修改与边界

仅两生产文件变化：agent_server.py在已有schema关键字遍历中，仅将恰含claim/evidence_id的封闭事实对象投影成官方allOf有序组件；work_navigation.py在remaining<=unseen时为尚未读到证据的来源保留读取机会，并同步共享阶段提示。strict schema、J3序列化、writer参数/渲染、证据发行、原三来源最低写入资格、读回/ACK和原生拒绝门均保持。其余顶层AST逐项相同。

allOf数组经过J3排序仍保留顺序，官方参考转换先发evidence_id再发claim。两项required与maxProperties=2保持标准schema封闭语义；现有ID枚举、JSON安全operation pattern、严格解码校验不变。只遍历schema关键字，不改const/default/examples业务字面量或扩展对象。此顺序不保证自然语言真实；没有按原题硬编码答案或自动判真。

六读预算保持。四个非空来源前三读重复同一来源后，为另外三个保留机会；五来源两次重复后即限制。页号仍由模型选择，三来源可写/可拒绝，不强制每份报告引用所有来源。完整原题覆盖仍需独审。

## 验证

父源码基线75项通过。新14项在父源码12失败/2通过，修改后全部通过。首轮全量10项失败和次轮8项失败、局部旧fixture失败均原样保留；迁移字段提取和阶段预算断言，诊断夹具显式限定原三来源而保持六读及全部错误断言。五个既有测试文件的用途未改变，新建一个事实顺序测试文件；没有新增跳过。

最终23组共1022个去重检查全部通过：1008产品、4保存包兼容、10官方参考。每组90秒，最多两个worker，守卫记录无拒绝操作，预期导入探针闭合；MockTransport不计实际研究调用。沿用delivery两项历史排除。

完整真实保存writer请求通过生产投影和官方参考：8条事实规则均证据优先，语法仍14502字节，请求32699到33371字节，小于49152；2048输出上限保持。这是离线固定参考证明，不是已安装原生二进制或实际模型质量通过。次轮诊断夹具读取五个密集来源后，触发原32768字节strict prompt拒绝门；这个失败被保留，没有扩大上限。三来源诊断用例和独立四/五来源覆盖用例各保留原用途，密集多来源请求体积风险仍待真实单例核验。

## 历史失败与交付边界

上一实际1496a844-668d-407a-a91b-89be246ba05b已write/END/读回/ACK，但9条事实仅第7条同时满足事实及所选引用，S4没有inspect，完整原题未覆盖，保持FAIL_CONFIRMED。完整文档、9条判定和来源缺口已保全，不能把合法ID、schema或来源数量当作事实信用。

原准备394成员、结果67成员、seal38成员与父产品准备1434成员逐字节读回；依赖保持。15个无关文件中14个与开工快照相同，北极星上线任务清单.html在本轮未写入的情况下于05:07 UTC发生变化，来源未判定；原摘要保留，当前字节另有快照，后续严格核对该观察值，不回写、不纳入提交。父工作树干净，新候选79个源文件绑定。未做新生产服务/保护进程探测，旧七身份只作历史基线；新实际入口仍需新鲜核验。

精确计划独审PASS_PLAN_ONLY；本包等待必要准备独审后继续已授权Task3入口准备。没有实际、release、controller-authority；后续实跑及结果复核另行明确分配。远端push此前自动审批blocked by policy，本轮不重试；本地提交/tag/镜像及最终读回另有回执。
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
v.save(N/'manifest.json',dict(kind='OFFLINE_SOURCE_GROUNDING_COVERAGE_PREPARATION',candidate=head,parent=v.BASE,tests=1022,actual_cases=0,model_calls=0,acceptance_credit=0,actual_authority=False,plan_sha256=v.sha(N/'plan.md'),spec_sha256=v.load(N/'inputs/scope.json')['spec_sha256'],files={p.relative_to(N).as_posix():v.sha(p) for p in sorted(members)},created_utc=dt.datetime.now(dt.timezone.utc).isoformat()))
state=v.load(T/'current-run.json');state.update(phase='SOURCE36_E02_SOURCE_GROUNDING_PREPARATION_REVIEW',workflow_status='audit',stage_queue_state='AUDIT',active_review_agent='/root/review_e02_source_grounding_preparation')
state['source36_offline']=dict(root=str(N),status='FROZEN_PENDING_INDEPENDENT_PREPARATION',candidate=head,parent=v.BASE,tests=1022,manifest_sha256=v.sha(N/'manifest.json'),actual_case_allocation=0,result_review_allocation=0,model_calls=0)
(T/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
print(json.dumps(dict(candidate=head,members=len(members),manifest_sha256=v.sha(N/'manifest.json'),tests=1022,actual=0)))
