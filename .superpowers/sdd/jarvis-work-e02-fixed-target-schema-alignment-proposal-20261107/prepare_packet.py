"""Prepare immutable review inputs without releasing an actual case."""
from pathlib import Path
import json,hashlib
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-native-write-diagnostics-20261107-r1';N=T/'e02-fixed-target-schema-20261107-r1'
OL=R/'.superpowers/sdd/jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107'
L=R/'.superpowers/sdd/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107'
candidate=json.loads((N/'inputs/candidate-transition.json').read_bytes())['candidate']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def new(p,text):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
def rep(text,old,value):
    assert old in text,old
    return text.replace(old,value)
text=(OLD/'verification/verify_preparation.py').read_text('utf8')
for old,value in [('e02-source13-native-metadata-20261107-r1',OLD.name),('jarvis-e02-write-diagnostics','jarvis-e02-fixed-target-schema'),
    ("['src\\\\brain\\\\work_service.py']","['src\\\\brain\\\\work_navigation.py']"),
    ("('diagnostics-green','metadata-green'","('target-green','diagnostics-green','metadata-green'"),
    ('PASS_OFFLINE_WRITE_DIAGNOSTICS_PREPARATION_ONLY','PASS_OFFLINE_FIXED_TARGET_SCHEMA_PREPARATION_ONLY'),
    ('WorkService bounded diagnostic from first failed trusted ledger writer only','v3_writer_schema.path exact research.md enum only')]:text=rep(text,old,value)
start=text.index("    assert len(sets['diagnostics-green'])==17");end=text.index("    current={",start)
text=text[:start]+'''    assert len(sets['diagnostics-green'])==17 and len(sets['target-green'])==19
    red=N/'offline/target-red-20261107T035611709106Z'
    redcases=list(ET.parse(red/'junit.xml').iter('testcase'))
    failed=[c for c in redcases if c.find('failure') is not None]
    assert len(redcases)==19 and len(failed)==12
    assert all(c.get('name').startswith(('test_schema_rejects_targets_', 'test_native_wrong_target_', 'test_native_format_and_strict_')) for c in failed)
    assert sha(red/'snapshot/src/brain/work_navigation.py')==load(N/'inputs/diagnosis-readback.json')['current_schema_sha256']
'''+text[end:]
new(N/'verification/verify_preparation.py',text)
text=(OLD/'verification/prepare_review.py').read_text('utf8')
text=rep(text,'e02-source13-native-metadata-20261107-r1',OLD.name)
text=rep(text,OL.name+'.md',L.name+'.md')
new(N/'verification/prepare_review.py',text)
replacements={OLD.name:N.name,'6cb9284c9f2bf60f2538d7cb34a124cc0bbf3696':candidate,
    'call_948abbc3ba2948a9b3441d57051d9b27':'call_409cc146033c4184879042b1abac6383',
    'SOURCE15_E02_WRITE_DIAGNOSTICS_AUTHORIZED_SINGLE_EXECUTION':'SOURCE16_E02_FIXED_TARGET_SCHEMA_AUTHORIZED_SINGLE_EXECUTION'}
text=(OL/'run_authorized_case.ps1').read_text('utf8')
for old,value in replacements.items():text=rep(text,old,value)
new(L/'run_authorized_case.ps1',text)
new(N/'inputs/execution-wrapper.json',json.dumps(dict(path=str(L/'run_authorized_case.ps1'),retry=0,conditional_max=1,question_id='call_409cc146033c4184879042b1abac6383',sha256=sha(L/'run_authorized_case.ps1'),invocations=0),indent=2))
for name in ('final_ready_readback.py','close_result_readback.py'):
    text=(OL/name).read_text('utf8').replace(OLD.name,N.name).replace('call_948abbc3ba2948a9b3441d57051d9b27','call_409cc146033c4184879042b1abac6383')
    new(L/name,text)
for name in ('protected-preparation-readback.json','worktree-registration-recovery.json'):
    (N/'inputs'/name).write_bytes((L/name).read_bytes())
query=json.loads((T/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_bytes())['query']
new(N/'preparation-report.md',f'''# E02固定目标schema对齐：新候选准备

原工单wo-ultimaagent-20261101-0021 / T2。用户call_409cc146033c4184879042b1abac6383授权最小schema补修、必要独审、通过后一例当前8B原题四来源及一次结果复核；失败不重试。候选{candidate}，基于6cb9284，独立工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-fixed-target-schema/UltimaAgent。

## 唯一产品改动

work_navigation.py::v3_writer_schema只改一行：path保留type:string/minLength1/maxLength2048，增加enum:[research.md]。原writer只接受research.md的条件不变，所有路径/引用/事实/扫描/END/ACK/读回/预算/时限和主错误行为不变。没有改写模型响应、扩大目录授权、改模型、提示或另建框架。

_research_sampler_schema原来只移除maxLength，会保留enum。新测试检查真实SDK mock transport发出的native format、strict_schema和sampler_schema三者均含同一个path enum；坏路径在native envelope验证处被拒，未派发writer，无文件或effect；合法research.md完整写入、ACK、外部SHA及来源读回成功。这里native响应为离线fixture，不是真实模型验收。

有效RED12失败/7通过：8个原schema接受的不可执行路径、3个原本到writer才失败的原生回复，以及缺失native enum；GREEN19。产品回归537=目标19+原诊断17+metadata43+研究178+navigation90+transport104+交付上下文86。保留两个原离线排除项：本地HTTP服务与cmd junction，均不计通过。原guard/Python SSRF离线fixture不变，OS包未测量。

新候选harness函数不变，仅重绑路径/候选/哈希。原238 harness用例和入口26/边界11/绑定14必须在新绑定通过，最终826项以封存readback为准。61来源、1551输入绑定。原P4/P1、保护基线、语料、模型manifest和旧失败保持；旧E01/E03信用仍属269aca5，新候选未实际回归。

## 工作区与保护核对

首次原生创建使用主仓库为source后停在creating，现有checkout虽可只读验证，但附加接口拒绝核验归属；该目录未写入或删除。改用当前已附加C5工作区为source创建独立名称，原生operation1953bae8-e0c5-42d7-a462-8194e1599757已completed且registrationError=null，才开始产品修改。原始operation0d662b62的登记问题不被伪称修复，资料保留。

北京时间2026-11-07 11:53的只读点核对，七个保护身份native/CIM/parent/命令摘要均与原基线一致；没有服务操作或模型调用。此观察不能替代实际入口的保护前后核验或连续存活证据。

## Review Focus

schema与writer都只允许research.md；native sampler和strict replay使用同一enum且没有改写响应；错误参数在派发前拒绝、合法完整链路保留；唯一现有产品源文件变化限于schema；原8B/语料/预算/时限/保护/清理门和所有历史失败不变。

当前没有actual authority或真实研究运行。E02/T2 NOT_PASSED。远端push仍受此前自动审批blocked by policy阻断，不重试或绕行。
''')
new(N/'execution-proposal.md',f'''# 已授权的固定目标schema候选单例

原工单wo-ultimaagent-20261101-0021 / T2，候选{candidate}。用户call_409cc146033c4184879042b1abac6383已授权补修、必要独审、PASS后一例研究和一次结果复核；不重复询问此范围。准备独审PASS、本地commit/tag/镜像读回后才签发TTL120秒分配，一例、一复核、retry0。

只用当前qwen3-8b-uncensored，digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题：{query}

原四完整来源corpus SHA9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002；浏览器search/GET仅原控制资料fixture，模型通过原SDK/HTTPX真实调用，不能替换回答。原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/rootwork275/cleanup310/seal315秒。原正常SSRF可能对raw.githubusercontent.com做受限DNS。

唯一入口{N/'code/entry.py'}，由封存wrapper一次调用。写域仅本证据根release/controller-authority/controller-ledger/native-preflight/actual/E02-controlled-1及后续review/verification。失败保存首结果与安全诊断，不重试。只清理本例已核验身份的新进程，七生产保护身份及未知后代拒绝清理门不变。无UI、音频或生产服务操作。

成功必须满足原SDK packet、research.md、ACK、两次外部读回、逐事实引用、时限/清理及独立复核；最多为新候选受控1/3，后续同候选连续两例、真实联网及E01/E03门仍保留。本授权不含那些现场例。旧四次失败和旧候选信用不转移，未测原生总推理次数为null。
''')
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask1: exact schema RED12failed/7passed -> GREEN19. Product537 PASS, candidate '+candidate+' committed/tagged. Native worktree corrected-source creation completed; failed-ownership checkout remains untouched. Shared harness functions and original gates unchanged; no case authority.\n')
print('Preparation documents and readonly/result wrappers ready; no actual allocation')
