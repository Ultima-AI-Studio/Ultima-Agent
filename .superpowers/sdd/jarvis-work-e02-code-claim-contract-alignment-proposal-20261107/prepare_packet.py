"""Freeze N8 review inputs and wrappers without allocating an actual run."""
from pathlib import Path
import hashlib,json,re
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-source-reference-schema-20261107-r1';N=T/'e02-code-claim-schema-20261107-r1'
OL=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107';L=Path(__file__).parent
candidate=json.loads((N/'inputs/candidate-transition.json').read_bytes())['candidate']
inputs=json.loads((N/'inputs/input-manifest.json').read_bytes())

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def new(p,text):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
def swap(text, changes):
    return re.sub('|'.join(re.escape(k) for k in changes), lambda m:changes[m[0]], text)

text=(OLD/'verification/verify_preparation.py').read_text('utf8')
text=swap(text,{'e02-fixed-target-schema-20261107-r1':OLD.name,
    'jarvis-e02-source-reference/UltimaAgent':'jarvis-e02-code-claim/UltimaAgent',
    ",'src\\\\brain\\\\tests\\\\test_work_write_diagnostics.py'":'',
    "('reference-green','target-green'":"('claim-green','grammar','reference-green','target-green'",
    "else Path('verification')/q.name":"else q.relative_to(N)",
    "if q.is_relative_to(C):assert sha(q)==digest,name":"if q.is_relative_to(C) or q.is_relative_to(N/'verification'):assert sha(q)==digest,name",
    'PASS_OFFLINE_SOURCE_REFERENCE_SCHEMA_PREPARATION_ONLY':'PASS_OFFLINE_CODE_CLAIM_SCHEMA_PREPARATION_ONLY',
    'Trusted visible source/evidence correlation in generation and independently rebuilt runtime schema; original writer gates retained':
    'Evidence-specific exact operation constraints in generation and independently rebuilt runtime schema; original writer and fact gates retained'})
start=text.index("    assert len(sets['reference-green'])==29")
end=text.index('    current={',start)
text=text[:start]+'''    assert len(sets['reference-green'])==29 and len(sets['claim-green'])==28 and len(sets['grammar'])==3
    red=N/'offline/claim-red-20261107T053117082072Z'
    redcases=list(ET.parse(red/'junit.xml').iter('testcase'))
    assert len(redcases)==27 and sum(c.find('failure') is not None for c in redcases)==26
    assert not any(c.find('error') is not None for c in redcases)
    assert sha(red/'snapshot/src/brain/work_navigation.py')==load(N/'inputs/diagnosis-readback.json')['current_schema_sha256']
    baseline=OLD/'inputs/protected-baseline.json'
    assert sha(baseline)==transition['protected_baseline_sha256']=='1b7e945e9ce52e44b8b384fc5e3911b77b7da4d80beeba615f341bf3e923fce5'
    inputs=load(N/'inputs/input-manifest.json')
    assert inputs['protected_baseline_path']==str(baseline) and len(inputs['source_files'])==63
    assert inputs['files'][str(baseline)]==sha(baseline)
    # No changes to the independent writer facts/text gates.
    before=ast.parse((red/'snapshot/src/brain/work_research.py').read_bytes())
    after=ast.parse((C/'src/brain/work_research.py').read_bytes())
    for name in ('_fact_evidence','_text'):
        assert ast.dump(next(n for n in before.body if isinstance(n,ast.FunctionDef) and n.name==name))==ast.dump(next(n for n in after.body if isinstance(n,ast.FunctionDef) and n.name==name))
    upstream=N/'verification/upstream'
    for row in load(upstream/'provenance.json')['files']:
        raw=(upstream/row['file']).read_bytes()
        assert hashlib.sha1(b'blob '+str(len(raw)).encode()+b'\\0'+raw).hexdigest()==row['git_blob_sha1']
'''+text[end:]
new(N/'verification/verify_preparation.py',text)
text=swap((OLD/'verification/prepare_review.py').read_text('utf8'),{
    'e02-fixed-target-schema-20261107-r1':OLD.name,OL.name+'.md':L.name+'.md',
    "('plan.md','execution-proposal.md','preparation-report.md')":"('plan.md','execution-proposal.md','preparation-report.md','contract-inventory.md')"})
new(N/'verification/prepare_review.py',text)
changes={OLD.name:N.name,'a0d21ebf167c41a76410075f7a92f1680926213f':candidate,
    'call_33506a697ec545c6b2a396ff83086672':'call_99e734b15417466b92af3e8e85fdc3ea',
    'SOURCE17_E02_SOURCE_REFERENCE_SCHEMA_AUTHORIZED_SINGLE_EXECUTION':'SOURCE18_E02_CODE_CLAIM_SCHEMA_AUTHORIZED_SINGLE_EXECUTION'}
new(L/'run_authorized_case.ps1',swap((OL/'run_authorized_case.ps1').read_text('utf8'),changes))
new(N/'inputs/execution-wrapper.json',json.dumps(dict(path=str(L/'run_authorized_case.ps1'),retry=0,conditional_max=1,
    question_id='call_99e734b15417466b92af3e8e85fdc3ea',sha256=sha(L/'run_authorized_case.ps1'),invocations=0),indent=2))
for name in ('final_ready_readback.py','close_result_readback.py'):
    new(L/name,swap((OL/name).read_text('utf8'),changes))
new(N/'inputs/protected-preparation-readback.json',(L/'protected-preparation-readback.json').read_text('utf8'))
query=json.loads((T/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_bytes())['query']
new(N/'preparation-report.md',f'''# E02代码事实契约对齐准备

原工单wo-ultimaagent-20261101-0021 / T2。用户call_99e734b15417466b92af3e8e85fdc3ea已授权补修、必要独审、PASS后一例当前8B原题四来源研究和一次结果复核；失败不重试。候选{candidate}，基于冻结a0d21eb，隔离工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-code-claim/UltimaAgent。

先完成contract-inventory.md：结构和可信卡片、文字规则、来源去重、AST/词法证据、END/ACK/SHA/两次读回、语义事实复核分别列明。实现只触及三个产品文件及一个新测试文件：新增v3_phase_writer_schema从已确认可见卡片派生operation约束；生成和独立runtime重放均调用它。卡片按同源同operation分组，evidence_id枚举保留；代码claim使用受支持的锚点、字符类、分组与分支表达原精确边界，operation按原格式/200字符规则拒绝非法值。非code原规则保留，无生成后补字或响应改写，无新增模型轮次。

28项新产品测试包括原schema接受/原writer拒绝的RED、同源其他operation/近似名称/前后边界/无效operation、空页、完整SDK mock第三pending页、format/strict/sampler/phase一致、文件/ACK/SHA、修复全部自报hash和native entity后的重放拒绝，以及原writer仍拒绝被篡改事实。初始RED26失败1通过（既有phase拒绝）；第一次两个缺失pattern以StopIteration暴露，第二次改为明确断言。所有记录保留。

另3项离线转换检查使用官方llama.cpp b10488参考转换器；Ollama v0.32.15源码固定此标签。抓取字节经Git blob hash核验，保留MIT许可证；最初主机DNS失败所留空文件未执行。Python格式器会拆分相邻字符串字面量，初次两条格式断言失败，修正仅相邻字面量表示检查后3项通过。最大6页48卡/5来源完整保留；48个不同200字符操作名的完整契约会越过原32768字节门，应拒绝，不扩大原49152实体上限。已保存官方转换GBNF与体积记录；这不等于已验证本机原生采样行为。

最终产品与参考转换检查597项，原执行框架238项、绑定16、入口26、边界11，总计888项，以封存readback为准。原本地HTTP服务/junction两个离线排除项不计通过；无OS抓包断言。原事实、源去重、writer、END、ACK、外部读回、时间和次数门不变。来源{len(inputs['source_files'])}份，绑定输入{len(inputs['files'])}份。

保护基线直接复用N7已审查的七身份：{inputs['protected_baseline_path']}，SHA1b7e945e9ce52e44b8b384fc5e3911b77b7da4d80beeba615f341bf3e923fce5。本轮准备只读核对七个native/CIM/parent/command身份一致，不重新定义基线、不推断连续存活。原Ollama启动来源未知的结论保留；无UI、音频或服务操作。实际前仍执行原新鲜身份核验。

旧候选/旧失败全保留；旧269aca5 E01/E03信用不转移。当前E02/T2/Owner NOT_PASSED，尚未签发单例authority。远端push受此前自动审批blocked by policy阻断，不重试或绕行。

审查重点：可信可见卡片、code证据与operation一一绑定、边界表达等价、非code不改、独立重放、原预算与事实门；同时核对保留未编码的正文/语义条件和未验证原生采样的明确限制。
''')
new(N/'execution-proposal.md',f'''# 已授权代码事实契约候选单例

原工单wo-ultimaagent-20261101-0021 / T2，候选{candidate}。用户call_99e734b15417466b92af3e8e85fdc3ea已批准补修、独审、PASS后一例及一次独立结果复核；不重复询问。准备审查PASS和本地commit/tag/镜像读回后才分配TTL120秒authority，retry0。

仅当前qwen3-8b-uncensored，digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题：{query}

原四完整来源corpus SHA9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002。source search/GET仍用原受控资料，模型经原SDK/HTTPX实际调用，回答不可替换。CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/rootwork275/cleanup310/seal315秒保持。正常SSRF可能对raw.githubusercontent.com做受限DNS。

唯一入口{N/'code/entry.py'}，wrapper仅一次；失败保存首结果及诊断，不重试。写域为本根release/controller-authority/controller-ledger/native-preflight/actual/E02-controlled-1及后续review/verification。仅清理本例核实的新进程，原七保护角色与未知后代拒绝规则保持。复用{inputs['protected_baseline_path']}与固定SHA，无UI/音频/生产服务操作。

成功要求research.md、可信SDK packet、ACK、两次外部读回、逐事实引用、原时限、清理及独立结果复核，最多本新候选受控1/3。后续同候选两例、实际联网、E01/E03及T2/Owner出口未授权或未通过；旧信用不转移；未测原生总推理次数为null。
''')
text=swap((OL/'publish_ready.py').read_text('utf8'),{
    OLD.name:N.name,OL.name:L.name,'jarvis-e02-source-reference/UltimaAgent':'jarvis-e02-code-claim/UltimaAgent',
    'ultimaagent-t2-e02-source-reference-ready-20261107':'ultimaagent-t2-e02-code-claim-ready-20261107',
    '4653f923b66346fbfa81eb738d0a7db941b0dd64':'1335b0f8cf60834d2fda31463efd9097c139a7bb',
    'f079ab8bf1a4929075c333ae278b880b9835cf1f':'342bd01323e475479e4125c4b1fa4ecb26c242d0',
    '857':'888','1557':str(len(inputs['files'])),'62来源':str(len(inputs['source_files']))+'来源',
    'jarvis-work-t2-e02-source-reference-preparation-20261107.md':'jarvis-work-t2-e02-code-claim-preparation-20261107.md',
    '来源与证据schema':'代码事实契约',
    'SOURCE17_E02_SOURCE_REFERENCE_SCHEMA_REVIEWED_READY':'SOURCE18_E02_CODE_CLAIM_SCHEMA_REVIEWED_READY',
    'chore(e02): seal source-reference schema and reconciled identity readiness':'chore(e02): seal reviewed code-claim contract readiness',
    'docs(e02): mirror source-reference schema preparation':'docs(e02): mirror code-claim contract preparation'})
new(L/'publish_ready.py',text)
print('N8 review packet documents and conditional wrapper prepared; no authority issued')
