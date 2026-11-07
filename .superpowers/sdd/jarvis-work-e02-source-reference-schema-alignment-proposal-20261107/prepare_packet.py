"""Prepare final review inputs and single-case wrappers; no runtime allocation."""
from pathlib import Path
import json,hashlib
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-fixed-target-schema-20261107-r1';N=T/'e02-source-reference-schema-20261107-r1'
OL=R/'.superpowers/sdd/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107'
L=R/'.superpowers/sdd/jarvis-work-e02-source-reference-schema-alignment-proposal-20261107'
candidate=json.loads((N/'inputs/candidate-transition.json').read_bytes())['candidate']
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def new(p,text):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
def rep(text,old,value):
    assert old in text,old
    return text.replace(old,value)
text=(OLD/'verification/verify_preparation.py').read_text('utf8')
for old,value in [('e02-native-write-diagnostics-20261107-r1',OLD.name),('jarvis-e02-fixed-target-schema/UltimaAgent','jarvis-e02-source-reference/UltimaAgent'),
    ("assert transition['changed_existing_sources']==['src\\\\brain\\\\work_navigation.py']","assert set(transition['changed_existing_sources'])=={'src\\\\brain\\\\agent_server.py','src\\\\brain\\\\work_navigation.py','src\\\\brain\\\\work_research.py','src\\\\brain\\\\tests\\\\test_work_write_diagnostics.py'}"),
    ("('target-green','diagnostics-green'","('reference-green','target-green','diagnostics-green'"),
    ("('bindings',14)","('bindings',16)"),
    ("p=N/'offline'/f'{group}-green/receipt.json';v=load(p)","p=N/'offline'/f'{group}-{\"final\" if group==\"entry\" else \"green\"}/receipt.json';v=load(p)"),
    ('PASS_OFFLINE_FIXED_TARGET_SCHEMA_PREPARATION_ONLY','PASS_OFFLINE_SOURCE_REFERENCE_SCHEMA_PREPARATION_ONLY'),
    ('v3_writer_schema.path exact research.md enum only','Trusted visible source/evidence correlation in generation and independently rebuilt runtime schema; original writer gates retained')]:text=rep(text,old,value)
start=text.index("    red=N/'offline/target-red-");end=text.index('    current={',start)
text=text[:start]+'''    assert len(sets['reference-green'])==29
    red=N/'offline/reference-red-20261107T042935781849Z'
    redcases=list(ET.parse(red/'junit.xml').iter('testcase'))
    assert len(redcases)==28 and all(c.find('failure') is not None for c in redcases)
    assert sha(red/'snapshot/src/brain/work_navigation.py')==load(N/'inputs/diagnosis-readback.json')['current_schema_sha256']
    binding_red=load(N/'offline/bindings-red-bound/receipt.json')
    assert binding_red['result']==dict(tests=16,failures=2,errors=0,denied=[],success=False) and binding_red['sources_unchanged']
    red_log=(N/'offline/bindings-red-bound/stderr.log').read_text('utf8')
    for name in ('test_rejects_previous_protection_baseline','test_rejects_coherently_replaced_protected_identity'):
        assert 'FAIL: '+name in red_log
    baseline=N/'inputs/protected-baseline.json';b=load(baseline);rc=load(N/'inputs/protected-reconciliation.json')
    ob=load(Path(b['predecessor_baseline']))
    assert sha(Path(b['predecessor_baseline']))==b['predecessor_baseline_sha256']==rc['previous_baseline_sha256']
    assert sha(N/'inputs/protected-reconciliation.json')==b['runtime_reconciliation_sha256']
    assert sha(N/'verification/native-drift-metadata.json')==rc['native_metadata_sha256']
    assert sha(N/'inputs/ollama-app-start-excerpt.json')==rc['app_excerpt_sha256']
    assert b['protected5'][1:]==ob['protected5'][1:] and b['protected_listener_pair']==ob['protected_listener_pair']
    assert b['protected5'][0]['pid']==11464 and ob['protected5'][0]['pid']==5708
    assert rc['service_operations']==rc['termination_calls']==rc['model_calls']==rc['new_case_calls']==0
    assert rc['unchanged_other_six'] and not rc['continuous_liveness_claim']
    assert transition['protected_baseline_sha256']==sha(baseline)
    inputs=load(N/'inputs/input-manifest.json')
    assert inputs['protected_baseline_path']==str(baseline) and len(inputs['source_files'])==62 and len(inputs['files'])==1557
    assert inputs['files'][str(baseline)]==sha(baseline)
'''+text[end:]
text=text.replace('# Runtime harness functions are unchanged; only candidate/hash constants are rebound.','# Runtime harness functions are unchanged; candidate/hash and exact baseline constants are rebound.')
new(N/'verification/verify_preparation.py',text)
text=(OLD/'verification/prepare_review.py').read_text('utf8').replace('e02-native-write-diagnostics-20261107-r1',OLD.name).replace(OL.name+'.md',L.name+'.md')
new(N/'verification/prepare_review.py',text)
replacements={OLD.name:N.name,'900b944165c0175b91492e3fe5b31d96aabdcd5c':candidate,
    'call_409cc146033c4184879042b1abac6383':'call_33506a697ec545c6b2a396ff83086672',
    'SOURCE16_E02_FIXED_TARGET_SCHEMA_AUTHORIZED_SINGLE_EXECUTION':'SOURCE17_E02_SOURCE_REFERENCE_SCHEMA_AUTHORIZED_SINGLE_EXECUTION'}
text=(OL/'run_authorized_case.ps1').read_text('utf8')
for old,value in replacements.items():text=rep(text,old,value)
new(L/'run_authorized_case.ps1',text)
new(N/'inputs/execution-wrapper.json',json.dumps(dict(path=str(L/'run_authorized_case.ps1'),retry=0,conditional_max=1,question_id='call_33506a697ec545c6b2a396ff83086672',sha256=sha(L/'run_authorized_case.ps1'),invocations=0),indent=2))
for name in ('final_ready_readback.py','close_result_readback.py'):
    text=(OL/name).read_text('utf8').replace(OLD.name,N.name).replace('call_409cc146033c4184879042b1abac6383','call_33506a697ec545c6b2a396ff83086672')
    new(L/name,text)
new(N/'inputs/protected-preparation-readback.json',(L/'protected-preparation-readback.json').read_text('utf8'))
p=N/'verification/run_entry_checks.py';text=p.read_text('utf8')
text=rep(text,"sources=[N/'code/entry.py',N/'tests/test_entry.py',Path(__file__)]","sources=[N/'code/entry.py',N/'tests/test_entry.py',Path(__file__),N/'verification/prepare_review.py']")
p.write_text(text,encoding='utf8')
query=json.loads((T/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_bytes())['query']
new(N/'preparation-report.md',f'''# E02来源与证据schema对齐：新候选准备

原工单wo-ultimaagent-20261101-0021 / T2。用户call_33506a697ec545c6b2a396ff83086672已授权补修、必要独审、PASS后一例当前8B原题四来源研究及一次只读结果复核，失败不重试。候选{candidate}，基于900b944，独立工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-reference/UltimaAgent。

## 实现和范围

三个产品文件：work_navigation.v3_source_reference_map只投影本请求可信可见卡片，拒绝坏格式和ID碰撞；v3_writer_schema可选映射按source_id生成章节anyOf，各分支只给该来源的evidence_id enum。agent_server沿用已issued加当前confirmed未promoted view构造唯一report_schema，供native format和phase使用；work_research由已验证reads切片独立重建同一映射/schema/phase，不信任模型自报集合。静态工具注册继续通用schema，实际可写阶段强制配对。没有响应改写、提前promotion或增加模型轮次。

原research.md目标、resolve_v3归属/事实/重复来源、writer/END/ACK/外部读回门、字节/输出预算和清理时限均保留。现有诊断测试4处因新schema更早拒绝坏引用而需调整：有效输入进入writer后在测试resolver边界注入故障，继续检验真实resolver和最早错误留存；重复来源使用正确配对的ref。此故障注入只在测试，生产不改写参数。

新增29项测试覆盖同源合法/异源与未发行和外请求ID拒绝、空卡片/碰撞、多页合并、第三个confirmed pending页、三份来源前无writer选项、真实SDK mock format/strict/sampler一致、文件/ACK/SHA和runtime重放，以及修复全部自报hash与native entity后的schema/phase伪造拒绝。最大6页48卡、5来源schema小于32768字节，原token估算拒绝过大上下文；原transport回归保留strict/entity 32768/49152字节门，超限失败关闭，不宣称任意长真实上下文可装下。

有效产品RED初始28失败；后续混合键检查暴露TypeError并修复，重放负例改用真实prewrite包以跨过更早的嵌套一致性门。所有失败保留。最终566项产品回归通过：新29+目标19+诊断17+metadata43+研究178+navigation90+transport104+交付上下文86。原本地HTTP服务与cmd junction两个离线排除项不计通过，OS网络包未测量。

## 保护基线和验证范围

Ollama原PID5708已退出，现有PID11464于北京时间12:18:38启动；父进程24608、可执行文件、命令摘要、版本0.32.15、8B摘要相同，其余六个精确身份一致。用户说明没有主动关闭、重启或更新。应用日志记录启动与旧PID清理，启动来源未知。旧基线保留；只读建立新七身份基线，仅用于本候选，路径和SHA固定。native/CIM/parent/command/端口所有原检查仍执行；没有服务操作、终止或模型调用，不推断连续存活。

新基线负例有效RED14通过/2失败，修复后16通过，拒绝旧基线路径及同时替换PID和manifest摘要的伪造。首次bindings-red因候选重绑尚未完成产生2个正例错误，不算有效RED；入口首轮因尚未生成prepare_review.py而有1个依赖错误，保留后以完整包复测。原238 harness和入口26/边界11/绑定16最终总数为857，以封存readback为准。62来源、1557绑定输入。运行harness函数与共享P4/P1不变；只变候选/哈希/基线常量，bindings.validate增加固定基线SHA。

原生工作区operation6ba6a53b-e91b-4c90-9ab6-388a82ea2ed9已completed、registrationError=null。旧候选和旧失败均保留，旧269aca5 E01/E03信用不转移。本候选尚无真实研究、E01/E03或实际联网验证。

## Review Focus

按plan.md五项逐一审查来源配对、pending时序、本请求映射隔离、独立重放、字节/次数/事实门。另审查readonly身份变化记录和固定baseline绑定、原七角色保护力度、诊断fixture是否保留原覆盖、原时限/清理与单次权限，不能把离线成功或新服务存在当作实际研究通过。

当前actual authority尚未签发，E02/T2/Owner NOT_PASSED。远端push仍受此前自动审批blocked by policy阻断，不重试或绕行。
''')
new(N/'execution-proposal.md',f'''# 已授权的来源与证据schema候选单例

原工单wo-ultimaagent-20261101-0021 / T2，候选{candidate}。用户call_33506a697ec545c6b2a396ff83086672已授权补修、必要独审、PASS后一例研究及一次结果复核；不重复询问此范围。准备独审PASS、本地commit/tag/镜像读回后才签发TTL120秒分配，一例、一复核、retry0。

仅qwen3-8b-uncensored，digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题：{query}

原四完整来源corpus SHA9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002；浏览器search/GET仅原控制资料fixture，模型经原SDK/HTTPX真实调用，回答不可替换。CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/rootwork275/cleanup310/seal315秒保持。原正常SSRF可能对raw.githubusercontent.com做受限DNS。

唯一入口{N/'code/entry.py'}，封存wrapper单次调用。写域限本证据根release/controller-authority/controller-ledger/native-preflight/actual/E02-controlled-1及后续review/verification。失败保存首结果和有限诊断，不重试；仅清理本例精确核验的新进程，七生产保护身份及未知后代拒绝清理门保持。保护基线固定为本根inputs/protected-baseline.json及SHA{sha(N/'inputs/protected-baseline.json')}，仅Ollama已运行身份由5708更新为11464，不控制服务。无UI或音频操作。

成功要求原SDK packet、research.md、ACK、两次外部读回、逐事实引用、时限/清理和独立复核；最多新候选受控1/3。后续同候选连续两例、真实联网及E01/E03门保留，本授权不含那些现场例。旧失败/旧候选信用不转移，未测原生总推理次数保持null。
''')
with (L/'progress.md').open('a',encoding='utf8') as f:
    f.write('\nTask1: entry-green25pass/1error was an ordering/setup error: prepare_review.py not generated yet. Preserve receipt; generate full package, bind producer source in runner, and run entry-final26 without changing any test or runtime entry behavior.\n')
print('Review scripts/documents/wrapper prepared, no actual release')
