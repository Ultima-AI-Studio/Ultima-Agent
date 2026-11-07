from pathlib import Path
import ast,importlib.util,json
N=Path(__file__).resolve().parents[1]
for p in (N/'verification').glob('*.py'):ast.parse(p.read_bytes())
spec=importlib.util.spec_from_file_location('n19_current_verification',N/'verification/verify_preparation.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v);result=v.verify()
assert result['tests']==346 and result['harness_unique']==285 and result['harness_raw']==287 and result['source_pins']==75
runtime=json.loads((N/'verification/runtime-readiness.json').read_bytes());inputs=json.loads((N/'inputs/input-manifest.json').read_bytes())
text=f'''# E02 原生拒绝诊断候选受控入口

状态：待独立准备审查。

原单wo-ultimaagent-20261101-0021/T2，冻结产品{result['candidate']}。本轮准备当前候选的受控入口，实际用例、模型调用、结果复核分配均0。E02仍0/3，旧E01/E03信用不迁移，T2/Owner未通过。

复用N17的entry/bindings/adapter，全部函数与类AST一致，仅重绑路径、候选及摘要。完整源码75项，由N17完整74项映射与N18完整75项/顶层38项并集产生；每项匹配冻结当前输入。输入{len(inputs['files'])}项，check_inputs含三项入口绑定共{result['input_pins']}项。原题四来源、当前8B摘要、预算、保护基线和previous_plumbing保持。

新增两项观察器联合验证均先安装当前adapter.install_trusted_exports，再调用真实SDK MockTransport。six_reads在第7次POST的2048相位故意返回done_reason=length：failed、明确未交付、六次读取/三来源、没有research.md/write/ACK。ack_after_write在第5次POST的256相位返回同一拒绝：needs_attention、write_without_ack、已写入文件和效果保留、未ACK。两项核对导出v4原字节与ledger相同、公开摘要、实际构造请求/响应SHA及字节数、generation/receipt_index，export为SAVED但complete=false/END=false/credit0。未提供或代写任何真实模型回答。

本轮{result['tests']}项去重离线通过：harness五组raw {result['harness_raw']}，unique {result['harness_unique']}；标准库bindings16/entry34/boundary11。90秒、最多2并行和原审计守卫保持，源码/快照/审计/JUnit一致。原quoted_write/escaped_boundary、HTTP500及失败导出负例保留。当前产出kind的一个旧断言由v3对齐为v4；产品源码没有变化，没有伪造新的产品RED。N18的909及N17的344为历史，未重跑/累计。本次Python操作审计不等于网络抓包证明。

只读环境核对点{runtime['recorded_at']}确认七保护身份、Ollama0.32.15、当前qwen3-8b-uncensored摘要与18799空闲，仅代表该点。C15 HEAD/tag/clean、N18封存953成员/输入1580/75源码和两项已审收口补充及执行回执、N17准备234/结果56/输入1579及旧失败链保全；15项其他已改文件按基线保留且排除暂存。

N17唯一实际bc216374-f59c-4967-99f2-ded53a4ea49d的HTTP200外层校验拒绝仍为FAIL_CONFIRMED，无research.md，具体拒绝谓词未知。本轮原生拒绝模拟只验证导出协议，不能认定旧失败的根因或真实8B已能交付。

当前仅8B，CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384/messages+strict32768/entity49152、输出256/2048均保持。原actual1/review1/retry0与120秒grant门不变。准备根无actual/release/controller-authority/native-preflight/controller-ledger；持续目标决定actual0，不得作为grant。

独审PASS后才写准备harness-approval并读回read_ready；缺少grant时read_release必须拒绝，run_once不调用。按execution-proposal.md明确分配单例及独立结果复核后，才允许真实请求。成功仍须原题事实/引用、写入读回、ACK、原时限、清理及独审全部通过。

收口报告使用LF，原单/current-run通用准备指针与当前包一致，last_actual_result保留。项目与UltimaDocs本地commit/tag及逐字节读回另有回执；closeout/publish/refresh_queue审查前只是脚本，不冒充已完成发布。此前远端push自动审批blocked by policy，本轮不重试。

执行裁定：沿用Windows原生ledger、冻结产品与旧证据；入口重绑定不制造产品RED，不安装或清理旧工作区。
'''
with (N/'preparation-report.md').open('x',encoding='utf8',newline='\n') as f:f.write(text)
print(json.dumps({k:result[k] for k in ('verdict','candidate','tests','harness_unique','harness_raw','input_pins','source_pins','actual_cases','model_calls')}))
