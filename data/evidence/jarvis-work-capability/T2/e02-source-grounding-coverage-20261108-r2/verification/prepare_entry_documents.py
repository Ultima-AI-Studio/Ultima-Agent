"""Prepare reviewable entry documents after fresh guarded entry verification."""
from pathlib import Path
import importlib.util,json
B=Path(__file__).resolve().parents[1];T=B.parent;R=B.parents[4]
N=T/'e02-source-grounding-controlled-preparation-20261108-r1'
O=T/'e02-claim-generation-controlled-preparation-20261108-r1'
head=json.loads((B/'verification/candidate-freeze.json').read_bytes())['candidate']
spec=importlib.util.spec_from_file_location('entry_readback',N/'verification/verify_preparation.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
checked=v.verify();assert checked['tests']==350
s=(O/'execution-proposal.md').read_text('utf8')
for a,b in {'d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b':head,'d8f8d97':head[:7],O.name:N.name,'call_5411de619a6c4de0bab414126a228c7d':'call_3d33440cc40c401ea7a2cf11c8bc2bcf'}.items():s=s.replace(a,b)
a=s.index('上一实际c4caa739');b=s.index('\n\n## 准备状态',a)
s=s[:a]+'''上一实际1496a844-668d-407a-a91b-89be246ba05b保持FAIL_CONFIRMED：research.md确已写入/END/读回/ACK，9条事实只有第7条同时满足事实与所选引用；S4未inspect，原题任务架构/接入覆盖未通过。新候选用官方allOf有序组件让evidence_id先于claim生成，并在六读内为未读来源保留机会。原strict、writer参数、三来源最低写入资格、完整原题和所有预算保持。字段顺序不是事实蕴含证明，模型仍可能选错页、过早写入或写出不受引用支持的事实；密集多来源卡片可能触发原32768字节strict prompt拒绝。1022项产品/兼容/参考与350项入口离线检查都不转为实际信用。本例须按完整原题验收。''' +s[b:]
s+='\n## 保全说明\n\n准备期间一个不属于产品/模型/依赖输入的看板HTML持续变化；原始与观察快照及首份NEEDS_FIXES审查均保留。此文件不写入或暂存，只报告变化；其他14个无关文件和全部产品/依赖/历史证据保持严格摘要核对。该例外不改变运行态核验、模型输入或验收标准。\n'
with (N/'execution-proposal.md').open('x',encoding='utf8',newline='\n') as f:f.write(s)
report=f'''# E02 证据优先与来源读取候选：受控入口准备

状态：待独立准备审查。

原单wo-ultimaagent-20261101-0021 / T2；候选{head}。产品准备r2已独立PASS并本地提交/tag/镜像/读回；本入口仅绑定冻结候选，产品没有再次修改。当前8B、完整原题、四来源与原预算保持；actual/model/network/UI/audio/生产服务操作均0，E02仍0/3，T2/Owner未通过。

## 已完成的准备

八组新鲜入口检查350项通过，0失败/错误/跳过：289个去重adapter身份、16bindings、34entry、11boundary；原始adapter291项有2个既有交叉身份。所有最终源码摘要一致，审计无拒绝操作，原预期导入探针闭合。产品1022项是本轮已封存的1008产品/4兼容/10参考检查，没有为入口重跑或加入350。

完整79产品源及输入清单绑定候选根。entry/bindings/adapter函数和类AST与上一入口完全相同；仅候选/路径/摘要绑定变化。准备答复在source_question_id保留真实call_3d33440cc40c401ea7a2cf11c8bc2bcf，执行绑定使用明确标记的内容派生ID，actual/result-review均0，原拒绝门禁止把准备答复升格单例权。

一处导出fixture同步新来源保留规则：第三次重复读即拒绝，reads/posts从4/5改为2/3、页数4改为2，所有失败状态、字节摘要、未写入和无信用断言保持。其他350项用途不变；v3/v4/v5、FULL/EXCERPTS/OMITTED_POLICY、严格错误/边界/写后ACK失败继续覆盖。

## 尚未证明

候选仅修复证据字段先发与读取机会；不保证自然语言蕴含、正确页选择或完整任务覆盖。上一例文件已交付但事实/引用和原题覆盖失败，完整文档及9条审查保留。没有新增实际模型结果。密集多来源prompt仍可能触发原字节门，未增预算。

运行态PENDING_FRESH_ACTUAL_PREFLIGHT；没有准备期模型或原生metadata请求。旧七身份与版本快照仅为历史基线。另行明确分配后，原入口在原时钟内重新核对保护进程、监听归属、模型摘要及隔离端口，任一失败停止单例、不重试、不操作保护进程。

## 保全及发布边界

r1产品准备独审发现无关北极星HTML在冻结后持续变化；保留NEEDS_FIXES及完整4293成员，新r2仅将此非输入文件改为动态观察。原与观察快照不可变，原HTML不写入/暂存；其他14个无关文件、所有源码/依赖和旧结果严格保全。本入口沿用该明确例外，不用当前HTML的变化阻断无关产品准备，也不将其纳入产品或实际准入。

新根没有actual/release/controller-authority/native-preflight或实际ledger。独审PASS后仅创建harness准备审批，read_ready通过且缺grant时read_release拒绝；不调用run_once或run_released。用户已清除goal登记，不重建goal；本次显式授权的离线工单范围继续完成。

本地提交/tag/镜像和最终Git/disk读回由后置回执证明。远端push此前被自动审批blocked by policy拒绝，本轮不重试。实际单例及结果复核需按execution-proposal.md另行明确分配。
'''
with (N/'preparation-report.md').open('x',encoding='utf8',newline='\n') as f:f.write(report)
rulings='''# Entry preparation rulings

- Root implements the already approved Task3. Product remains frozen. No actual/model/network or service operation.
- Use the predecessor's correct content-derived zero-allocation preparation binding from inception, with actual source_question_id retained; core AST unchanged.
- Migrate only reserved-read export fixture counts2/3 and two confirmed pages; keep every negative assertion. No new test deletion or exclusion.
- The unrelated changing HTML is never written or staged. Preserve original and observed snapshots; report its current drift without treating it as a product input. All other14 files and all product/dependency/failure hashes remain strict.
- New entry has no actual grant. Original fresh runtime preflight and full original-question facts/citations/coverage/timing/cleanup acceptance remain mandatory after a separately allocated case.
- User cleared the goal registry; do not recreate one. Local offline task completion is distinct from E02/T2 acceptance.
'''
with (N/'execution-rulings.md').open('x',encoding='utf8',newline='\n') as f:f.write(rulings)
ledger=R/'.superpowers/sdd/jarvis-work-e02-source-grounding-controlled-entry-plan-20261108/progress.md';ledger.parent.mkdir(parents=True,exist_ok=True)
with ledger.open('x',encoding='utf8') as f:f.write('# Authorized entry plan ledger\n\n- Root inline, plan independently PASS. Frozen79-source candidate.\n- Task1:350 fresh checks PASS; pending live preflight, actual/model0.\n- Task2: preparation independent review pending; then local publication/readback.\n- Explicit scope and necessary review authorization supersede redundant routine handoff. No install, remote push or deletion.\n')
(N/'verification/skill-controlled-entry-ledger-before-review.md').write_bytes(ledger.read_bytes())
print(json.dumps(dict(candidate=head,entry_checks=350,status='ENTRY_DOCUMENTS_PREPARED',actual=0)))
