"""Prepare offline verification and review packet; never allocates a case."""
from pathlib import Path
import hashlib,json
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
N=T/'e02-native-write-diagnostics-20261107-r1';OLD=T/'e02-source13-native-metadata-20261107-r1'
L=R/'.superpowers/sdd/jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107'
OL=R/'.superpowers/sdd/jarvis-work-e02-source13-native-metadata-compat-proposal-20261107'
candidate=json.loads((N/'inputs/candidate-transition.json').read_bytes())['candidate']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def new(p,text):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
def replace(text,old,value):
    assert old in text,old
    return text.replace(old,value)
text=(OLD/'verification/verify_preparation.py').read_text('utf8')
for old,value in [('e02-source13-child-admission-20261107-r1',OLD.name),('jarvis-e02-native-metadata','jarvis-e02-write-diagnostics'),
    ("['src\\\\brain\\\\work_research.py']","['src\\\\brain\\\\work_service.py']"),
    ("('metadata-green','research-a'","('diagnostics-green','metadata-green','research-a'"),
    ("'PASS_OFFLINE_METADATA_COMPAT_PREPARATION_ONLY'","'PASS_OFFLINE_WRITE_DIAGNOSTICS_PREPARATION_ONLY'"),
    ("'checked_native_identity optional string-array capabilities only'","'WorkService bounded diagnostic from first failed trusted ledger writer only'")]:text=replace(text,old,value)
text=replace(text,"    for row in load(N/'inputs/copied-frozen-dependencies.json'):assert sha(Path(row['source']))==sha(Path(row['destination']))==row['sha256']\n",'')
start=text.index("    red=N/'offline/metadata-red-");end=text.index("    current={",start)
text=text[:start]+'''    assert len(sets['diagnostics-green'])==17
    red=N/'offline/diagnostics-red-20261106T183734991978Z'
    redcases=list(ET.parse(red/'junit.xml').iter('testcase'))
    failures=[c.find('failure') for c in redcases if c.find('failure') is not None]
    assert len(redcases)==17 and len(failures)==14
    assert all("'research_failure'" in f.get('message','') for f in failures)
    assert sha(red/'snapshot/src/brain/work_service.py')=='206fe17ddf8d78b64018fda01a03228e97d6e74014da3c6d21e9dc7eee860449'
'''+text[end:]
start=text.index("        if group=='recovery':");end=text.index("        selected['harness-'",start)
text=text[:start]+"        assert cases==old_cases\n"+text[end:]
text=replace(text,"    assert 'candidate_environment' in changed and len(changed)==2,changed","    assert not changed,changed")
text=text.replace('# Pin all runtime changes: data rebinding and exactly the environment adapter.','# Runtime harness functions are unchanged; only candidate/hash constants are rebound.')
new(N/'verification/verify_preparation.py',text)
text=(OLD/'verification/prepare_review.py').read_text('utf8')
text=replace(text,'e02-source13-child-admission-20261107-r1',OLD.name)
text=replace(text,'jarvis-work-e02-source13-native-metadata-compat-proposal-20261107.md','jarvis-work-e02-native-write-failure-diagnostics-proposal-20261107.md')
new(N/'verification/prepare_review.py',text)
text=(OL/'run_authorized_case.ps1').read_text('utf8')
for old,value in [(OLD.name,N.name),('0a57d50f226df70542838c05fb8a21e025e19447',candidate),
    ('call_3471155e77c74b8db30c1278112c74d2','call_948abbc3ba2948a9b3441d57051d9b27'),
    ('SOURCE14_E02_METADATA_AUTHORIZED_SINGLE_EXECUTION','SOURCE15_E02_WRITE_DIAGNOSTICS_AUTHORIZED_SINGLE_EXECUTION')]:text=replace(text,old,value)
new(L/'run_authorized_case.ps1',text)
new(N/'inputs/execution-wrapper.json',json.dumps(dict(path=str(L/'run_authorized_case.ps1'),retry=0,conditional_max=1,question_id='call_948abbc3ba2948a9b3441d57051d9b27',sha256=sha(L/'run_authorized_case.ps1'),invocations=0),indent=2))
text=replace((OL/'final_ready_readback.py').read_text('utf8'),OLD.name,N.name)
new(L/'final_ready_readback.py',text)
query=json.loads((T/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_bytes())['query']
new(N/'preparation-report.md',f'''# E02研究写入失败诊断：新候选准备

原工单wo-ultimaagent-20261101-0021 / T2。用户call_948abbc3ba2948a9b3441d57051d9b27已授权有限诊断补修、必要独审、PASS后一例当前8B研究及一次只读独立结果复核；失败不重试。候选{candidate}基于0a57d50，工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-write-diagnostics/UltimaAgent。

## 定位与改动

旧实际91fb07e8的writer报ValueError，但具体原因没有落盘，仍为UNKNOWN。静态读回纠正前份报告：_CapabilityTool.execute已在请求内ledger存入error/error_type，丢失位置是WorkService公开回执裁剪，不能据此反推旧具体原因。原失败和独审材料保持原SHA；项目结果报告只追加勘误并镜像。

唯一已有产品文件变动work_service.py。研究模式在最终裁剪前从可信ledger outcome snapshot的首个失败ultima_work_research_write记录生成research_failure。30个精确固定ValueError消息映射封闭原因码；不做子串或前缀猜测。阶段固定research.write，类型为固定白名单；未知原因UNKNOWN。任意异常原文不新增导出，只保存长度以及最多4096字符的SHA-256（surrogatepass，超长hash为null）。原公共error和tool_results行为保持；新增诊断不是成功判据，不改变writer/END/事实/引用/身份/文件字节/ACK/截止门。

诊断只读records，不读SDK/model提供的tool_results；最早原因不被后续通用END/后续writer记录替换。没有修改模型、参数、来源、预算、默认路径、UI/语音或生产服务。旧269aca5的E01/E03信用保持在旧候选，新候选没有现场信用。

## 离线证明与边界

有效RED为14失败/3通过，失败均为缺research_failure；一次早期测试对Unicode孤代理字符错误误期望通用END，已按实际已有UTF-8错误纠正，不修改产品异常控制流，该早期失败保留。GREEN诊断17，包含实际SDK/executor/writer/END合成原生传输流程、未签发/跨来源引用、重复来源、多行claim、未知/超长/Unicode异常、类型白名单、SDK伪造、最早原因和合法交付。

产品检查518：诊断17+metadata43+研究178+navigation90+transport104+交付上下文86。延续两项原离线排除：本地HTTP集成与cmd junction，不计通过。测试native传输/GET为离线fixture，无真实模型调用。原Python审计guard与SSRF离线fixture不改；不把Python审计当作OS全流量测量。

验收harness原函数保持，只重绑新候选、路径及哈希；共享P4/P1不变。原238 harness案例与51入口/边界/输入检查必须在新绑定上通过，封存readback给出最终807项。60来源及1549输入绑定由生成清单核实。全部旧失败保持，新例在准备PASS前未释放。

## Review Focus

只从可信ledger选择最早writer失败；稳定诊断与任意异常/模型文本严格隔离；新增数据不能成为成功判据或改变END拒绝顺序；原schema/API成功与失败行为、模型/预算/时限/保护身份不变；新候选来源绑定与旧失败完整保留。

准备完成不代表E02通过。真实单例仍须SDK packet、research.md、ACK、两次外部字节读回、事实引用及原清理/时限。E02/T2当前NOT_PASSED。远端push仍受此前自动审批blocked by policy阻断，不重试或绕行。
''')
new(N/'execution-proposal.md',f'''# 已授权的研究失败诊断候选单例

原工单wo-ultimaagent-20261101-0021 / T2，候选{candidate}。用户call_948abbc3ba2948a9b3441d57051d9b27授权诊断补修、必要独审、PASS后单例研究及一次结果复核。准备独审PASS、本地commit/tag/镜像读回后签发TTL120秒分配，一例+一次复核，retry0；不再重复请求该范围。

模型仅qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题：{query}

原四份完整资料corpus SHA256 9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002；浏览器search/GET只用原控制资料fixture，模型通过原SDK/HTTPX真实调用，不能替换原生回答。原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/rootwork275/cleanup310/seal315秒保持。原正常SSRF可能对raw.githubusercontent.com做受限DNS。

唯一入口{N/'code/entry.py'}，由已封存root wrapper一次调用。写域仅本证据根release/controller-authority/controller-ledger/native-preflight/actual/E02-controlled-1以及结果review/verification。失败保留首结果与新增有限原因码，不重试。只清理本例已核验身份的进程，七个生产保护身份及未知后代拒绝清理门保持。无UI、音频或生产服务操作。

成功仍需原SDK packet/研究文件/ACK/两次外部读回/逐事实引用/时限/清理与一次独立事实复核，最多登记本新候选受控1/3；后续两例、真实联网和同候选E01/E03等门仍保留。旧失败、旧候选信用不转移。应用native POST尝试与原生推理次数区分，未测量保持null。远端同步blocked by policy，不重试。
''')
with (L/'progress.md').open('a',encoding='utf8') as f:f.write('\nTask 1: genuine SDK offline diagnostic RED 14 failed/3 passed -> GREEN 17 passed; Unicode test expectation corrected to preserve pre-existing encoder failure. Product518 PASS, exact two-file candidate '+candidate+' committed/tagged. Harness rebinding is data-only; no actual calls or authority issued.\n')
print('Review packet scripts/documents prepared; no runtime authority')
