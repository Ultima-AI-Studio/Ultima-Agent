"""Prepare exact execution proposal and publication program before sealing."""
from pathlib import Path
import ast,hashlib,importlib.util,json
N=Path(__file__).resolve().parents[1];O=N.parent/'e02-output-budget-controlled-preparation-20261107-r1'
B=N.parent/'e02-output-structure-diagnostics-20261108-r2'
HEAD='bf7f7a9cf0e4ba559c29daa388c00379d12d345a'
def write(p,s):
    if p.suffix=='.py':ast.parse(s)
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(s)
def replace_once(s,old,new):
    assert s.count(old)==1,(old,s.count(old));return s.replace(old,new,1)
s=(O/'execution-proposal.md').read_text('utf8')
s=s.replace('0421a54cab572be013c3f7ad562e86406bfe8e52',HEAD).replace('0421a54','bf7f7a9').replace(O.name,N.name)
s=replace_once(s,'本轮按用户明确授权的输出预算补修计划Task2准备新候选入口','本轮按输出结构诊断提案及持续原工单目标准备冻结诊断候选入口')
old='当前产品输出v4私有失败诊断。保留原last_http回执；仅原生外层校验拒绝时新增固定原因、受限计数、请求/响应SHA及字节数，绑定同一generation与receipt。500正文不读取；坏JSON/schema/扫描失败不得冒充原生拒绝。私有回执经原adapter观察器导出，写后ACK拒绝保留已写入事实；诊断不等于完整runtime、END或交付。'
new='当前候选在原生拒绝处可输出闭合v5私有诊断：同请求flags/options及strict/sampler摘要、content/thinking类型和长度摘要、完整content严格JSON状态和受限错误位置、完整JSON的schema/结构计数。thinking和未知字段值不留正文；安全扫描后优先FULL，原16384字节诊断上限不足时使用带偏移和省略计数的EXCERPTS，策略拒绝则OMITTED_POLICY。编码预算或诊断异常时保留原v4，不删除旧证据；v3/v4仍可读。所有字段绑定同一实际请求和原始响应字节SHA/长度。length仍拒绝，不修复残缺JSON，不从片段执行工具。原响应65536字节上限、公共摘要、500正文不读取及原失败语义保持；本诊断只覆盖已能解析外层JSON的原生拒绝。私有回执经原adapter观察器导出，写后ACK拒绝保留已写入事实；诊断不等于完整runtime、END或交付。'
s=replace_once(s,old,new)
old='上一N19的72d7d71b-39a9-455a-b0b4-8823b3f24c00仍为FAIL_CONFIRMED：第7次HTTP200后的done_reason=length，eval_count=max_tokens=2048，无research.md/write/ACK。完整响应正文未保存，不推断内部内容或token分配。N20的927项离线检查不转为实际信用；本例仍按原题完整交付验收，不能只看响应不截断或诊断成功。'
new='上一N21的9dbe192a-3bc1-4a4d-a218-581846d5f654及N19旧例均保留FAIL_CONFIRMED：第7次HTTP200后的done_reason=length，eval_count=max_tokens=2048，无research.md/write/ACK。旧包未保存正文，不能据此判定JSON是否残缺或推断token分配。N24的979项产品/兼容检查和本入口350项检查不转为实际信用；本例仍按原题完整交付验收，不能只看诊断是否捕获。获得实际证据后才决定后续结构、终止兼容或事实导航的最小修复，不先重写交付事务。'
s=replace_once(s,old,new)
write(N/'execution-proposal.md',s)
s=(O/'verification/publish.py').read_text('utf8')
s=s.replace('jarvis-e02-output-budget','jarvis-e02-output-structure-r2').replace('ultimaagent-e02-output-budget-controlled-ready-20261107','ultimaagent-e02-output-structure-controlled-ready-20261108').replace('e02-writer-output-budget-20261107-r1',B.name).replace('bind output budget candidate','bind output structure diagnostic candidate').replace('mirror output budget controlled entry','mirror output structure controlled entry')
write(N/'verification/publish.py',s)
spec=importlib.util.spec_from_file_location('entry_document_readback',N/'verification/verify_preparation.py');m=importlib.util.module_from_spec(spec);spec.loader.exec_module(m);v=m.verify()
assert v['tests']==350 and v['harness_unique']==289
report='''# E02 输出结构诊断受控入口准备

状态：待独立准备审查。

原单 wo-ultimaagent-20261101-0021 / T2；冻结产品候选 `bf7f7a9cf0e4ba559c29daa388c00379d12d345a`。当前实际研究、模型调用及独立结果复核分配均为0；E02仍0/3，T2/Owner未通过。准备通过不能替代完整原题交付。

审查结论：现有交付链已经完成结构化事实、来源绑定、Markdown渲染、单次写入/读回及ACK。旧N19/N21的length/2048拒绝未保存正文，尚不能认定JSON必定截断或定位字段。本轮产品不再修改；仅把已冻结v5诊断绑定到原受控入口，为取得确证问题所需的实际回执做准备。

新鲜离线入口检查350项通过：289项去重adapter检查，16项binding、34项entry、11项boundary。五组harness原始291项有2项原有交叉覆盖，按身份去重；八个最终组均PASS、无失败/错误/跳过、同源码字节，最多2组并发。新增四项原导出器检查覆盖FULL、EXCERPTS、OMITTED_POLICY及矛盾保留状态拒绝，验证原16384字节总上限、实际原始字节摘要、完整性/END/验收信用为零。首次export-red的2项失败只是旧v4版本断言，32项通过；失败回执保留，确认为obsolete测试后仅更新该断言。没有把它们称为产品缺陷。N24原979项产品/兼容检查为已冻结证据，本轮未重跑、未加进350。

入口entry、bindings和adapter的全部函数/class AST与N21完全一致，仅候选/路径/hash常量和导出测试更新。完整77个当前源文件、1598项输入摘要已绑定。准备decision为明确标记的内容派生ID，实际/结果复核额度0，不是平台call id或执行grant。未复制旧release、actual、controller authority或任何旧额度。

只读运行环境核对：Ollama0.32.15，当前qwen3-8b-uncensored摘要6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330，七个保护身份在本次核对点一致，18799空闲；只读取/version与/tags，没有推理或服务操作。观察点不代表连续存活保证。N24准备1192成员、N19/N21历史失败、r1 NEEDS_FIXES及1567依赖/输入、15个无关改动均由原只读校验重新核验。所有旧实际失败保持，新候选不承接旧E01/E03通过信用。

当前8B、原题四来源、全部事实/引用/覆盖/文件门保持。原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8，service260/client300/rootwork275/cleanup310/seal315秒，输出writer2048/read和ACK256、上下文及各字节上限不变，失败不重试。无UI、音频或生产服务操作，不安装/下载。未获得真实输出正文，未证明研究交付已改善。

准备独审PASS后只能签发harness准备回执并证明缺少grant时原入口拒绝；新研究仍须明确分配单例及一次独立结果复核。执行范围见本目录execution-proposal.md。先据真实回执判定结构截断、终止兼容或事实覆盖问题，再决定代码功能修改。

本地提交、tag、镜像由publication-readback与final-readback分别证明；这些后置回执不声称属于此前manifest。此前远端push与忽略scratch清理被自动审批blocked by policy，当前不重试/不换通道；scratch仅复制归档。
'''
write(N/'preparation-report.md',report)
print(json.dumps(dict(proposal=str(N/'execution-proposal.md'),tests=v['tests'],actual_allocation=0)))
