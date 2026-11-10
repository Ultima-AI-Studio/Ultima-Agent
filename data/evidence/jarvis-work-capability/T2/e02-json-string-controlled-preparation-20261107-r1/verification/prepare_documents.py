"""Prepare the concrete proposal and local closeout scripts, never execute a case."""
from pathlib import Path
import json
N=Path(__file__).resolve().parents[1]
OLD=N.parent/'e02-source-coverage-controlled-preparation-20261107-r1'
HEAD='6d758d9c3961f156a062e349ec4a949e2ee7a9a9'
def write(path,text):
    with path.open('x',encoding='utf8',newline='\n') as f:f.write(text)
def replace(text,before,after):
    assert before in text,before
    return text.replace(before,after)
text=(OLD/'execution-proposal.md').read_text('utf8')
text=text.replace('e40a55b40c223181040dbb6a09d0c4d2da5026cf',HEAD).replace('e40a55b',HEAD[:7]).replace(OLD.name,N.name)
text=replace(text,'当前产品采用读取预算/来源覆盖联动与固定“本次研究未交付。”终态；入口不改该行为、不为模型选页或代写。',
    '当前产品保留读取预算/来源覆盖联动与固定“本次研究未交付。”终态，并将代码事实的原生采样约束投影为合法 JSON 字符串语法；解码后的严格约束保持。入口不为模型选页或代写。')
text=replace(text,'上一N13失败与N14离线通过均不迁移成当前实际信用。',
    '上一 N15 的 5e6ea89c-8e47-43a6-9480-7a11d72cabf5 失败与 N16 的 781 项离线通过均不迁移成当前实际信用。原生二进制和真实 8B 对新投影的行为尚未实际验证。')
write(N/'execution-proposal.md',text)
text=(OLD/'closeout.py').read_text('utf8') if (OLD/'closeout.py').exists() else (OLD/'verification/closeout.py').read_text('utf8')
text=text.replace('jarvis-e02-source-coverage','jarvis-e02-json-string-projection')
text=text.replace('e40a55b40c223181040dbb6a09d0c4d2da5026cf',HEAD).replace('e40a55b',HEAD[:7])
text=text.replace('source-coverage-controlled','json-string-controlled').replace('source-coverage-controlled-entry','json-string-controlled-entry')
text=text.replace('342','344').replace('SOURCE25_E02_COVERAGE_CONTROLLED','SOURCE27_E02_JSON_STRING_CONTROLLED')
start=text.index('text=f"""');end=text.index('for p in (report_path',start)
text=text[:start]+'''text=f"""# E02 6d758d9 受控入口准备完成

原工单 wo-ultimaagent-20261101-0021 / T2。冻结产品候选 {HEAD} 已接入现有受控入口，本轮实际用例0、结果复核分配0、模型调用0。E02仍0/3，T2/Owner未通过；旧候选E01/E03信用不迁移。

复用 N15 的 entry、bindings、adapter，全部函数与类 AST 保持一致，仅重绑候选、路径和摘要。完整源码74项、输入1579项，check_inputs含三项入口绑定共1582项。清单由N15继承73项与N16顶层37项映射并集产生，逐项匹配N16 current-inputs及当前磁盘。产品HEAD/tag与工作区clean已核对。

新增两项安装原导出观察器的SDK MockTransport联合验证：合法中文、引号及反斜杠代码事实完成工具写入、文件摘要读回、ACK和导出包严格重放；raw sampler允许但解码后违反操作名边界的内容被严格校验拒绝，无research.md或完整runtime/END，公开明确未交付。两项均核对实际构造的HTTP实体摘要与可信回执；没有真实模型或事实验收信用。

本轮344项去重离线PASS：adapter五组原始285项、去重283项，以及入口34/绑定16/边界11共61项。原90秒分片及离线审计守卫保持，源码快照/回执/审计/JUnit均核验。产品N16的781项（775产品+6参考）仅为冻结历史基线，本轮未重跑或重新累计。新入口未实现新的产品行为，也未重复制造旧RED。

精确计划PASS_PLAN_ONLY，整包PASS_PREPARATION_ONLY。manifest {MANIFEST}，{member_count}成员；独立准备审查SHA256 {sha(review_path)}。harness-approval仅绑定准备审查；read_ready通过，缺少grant时read_release拒绝，run_once未调用。准备根没有release/actual/controller-authority/native-preflight。

只读检查点 {runtime['recorded_at']}：七保护身份、Ollama0.32.15、当前qwen3-8b-uncensored摘要及18799空闲相符，仅代表该时点。N16封存956成员/输入1576项、N15封存准备189/结果56及旧输入1575项、九个无关文件均保持。上一实际5e6ea89c-8e47-43a6-9480-7a11d72cabf5的HTTP500和未交付仍为FAIL_CONFIRMED，不改写或复用额度。

当前8B、原题四来源、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒以及上下文/字节/输出预算均保持。真实8B交付、原生GBNF二进制行为、三来源事实/原题覆盖和连续存活尚未获本候选实际证明。

下一步按 execution-proposal.md 明确分配一例当前8B原题四来源受控研究及一次只读独立结果复核后，才生成短时且一次消费的grant。失败不重试；无UI/音频/生产服务操作。项目/UltimaDocs本地提交、tag及逐文件读回由 verification/publication-readback.json 记录；此前远端push被自动审批以blocked by policy拒绝，本轮不重试。

证据根：{N.as_posix()}
"""
''' + text[end:]
text=replace(text,"61 entry/binding/boundary + 281 deduplicated adapter; N14 product746 frozen baseline not rerun",
    "61 entry/binding/boundary + 283 deduplicated adapter; N16 product781 frozen baseline not rerun")
text=text.replace('e02_source_coverage_controlled_preparation=dict','e02_json_string_controlled_preparation=dict')
text=text.replace('C13 frozen','C14 frozen').replace('source coverage controlled preparation complete','JSON string controlled preparation complete')
text=replace(text,"assert state['last_actual_result']==last_actual", "state.update(active_candidate=HEAD, next_work='Explicitly allocate one case and one result review on the concrete proposal before actual execution')\nstate['source27_preparation']=dict(status='READY_AWAITING_EXPLICIT_ONE_CASE_ALLOCATION',candidate=HEAD,tests=344,manifest_sha256=MANIFEST,review_sha256=sha(review_path),actual_case_allocation=0,result_review_allocation=0)\nassert state['last_actual_result']==last_actual")
write(N/'verification/closeout.py',text)
text=(OLD/'verification/publish.py').read_text('utf8')
text=text.replace('jarvis-e02-source-coverage','jarvis-e02-json-string-projection').replace('source-coverage-controlled','json-string-controlled')
text=text.replace('cc7e6e9f5514dfc9721e0249ff68ed6fb3d160b1','a9f24dd4985c2270a84c763af4e7371dd7991350')
text=text.replace('e357b7acde8cabf9bef6d68fd03da2c91aa87f7a','d913cec262316d8c0ddc6998ac21c3097484dd88')
text=text.replace('source coverage candidate','JSON-string candidate').replace('source coverage controlled entry','JSON-string controlled entry')
write(N/'verification/publish.py',text)
print(json.dumps(dict(documents_prepared=True,actual_allocation=0)))
