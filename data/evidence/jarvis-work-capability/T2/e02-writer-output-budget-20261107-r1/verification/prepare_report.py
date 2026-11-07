from pathlib import Path
import hashlib,json,subprocess
N=Path(__file__).resolve().parents[1];C=Path(json.loads((N/'inputs/worktree.json').read_bytes())['root'])
v=json.loads((N/'verification/offline-readback.json').read_bytes())
assert v['verdict']=='PASS_FRESH_OFFLINE_CURRENT_BYTES'
head=subprocess.check_output(['git','-C',str(C),'rev-parse','HEAD'],creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
assert head!=v['base']
rows='\n'.join('| '+k+' | '+str(x['passed'])+' |' for k,x in v['selected'].items())
text=f'''# E02 写入输出预算对齐：离线准备报告

状态：PASS_FRESH_OFFLINE_CURRENT_BYTES；独立准备审查待完成。

原单wo-ultimaagent-20261101-0021 / T2。父d860b2ab4e4d9974e33c96472e4ea15abb807280；候选{head}；路径{C}。
tag：ultimaagent-e02-output-budget-candidate-20261107。精确五文件变更，其中三个生产文件、两个测试文件；全量绑定76项源码。

共享v3_research_phase增加必填output_tokens，拒绝bool、非整数或1..2048之外值。生成传入已经算出的实际limit；独立重放传入通过原options校验的num_predict。提示说明整份JSON的实际预算并引导紧凑JSON、简短标题、精确原子事实、保留原题信息与引用、完成完整对象；不改schema、事实数量、来源门或任何实际预算。ACK原指令不变。

本次RED为18项失败、0 collection/setup error；修改后18项通过。最终同一源码新鲜检查{v['tests']}项，其中产品{v['product_tests']}、兼容{v['compatibility_tests']}；JUnit身份重复0。较小allowance32、默认256/2048、8192封顶都通过实际SDK MockTransport请求核对和独立重放；被修改/移除预算句且重算实体摘要的prewrite仍被拒绝。

| 组 | 通过数 |
| --- | ---: |
{rows}

既有length拒绝、写前“未交付”、写后ACK失败保留已写入效果、v3/v4诊断、来源覆盖/引用/事实/schema、严格重放均通过适用回归。每片90秒、最多2并行；保留test_http_work_legacy_and_cli及test_reparse_rejected两项既有排除。Python操作审计不等于系统抓包；无真实模型、UI、音频或服务操作。

父唯一实际72d7d71b-39a9-455a-b0b4-8823b3f24c00仍为FAIL_CONFIRMED：第7次HTTP200，done_reason=length、eval_count=max_tokens=2048、无research.md/write/ACK。完整响应正文未封存，因此不能确定具体内容如何耗尽token。本补修是否改善当前8B真实交付仍未知，不授予实际信用。

父准备159/结果56/实际seal31、完整输入1590及更早失败保留；15个无关已改文件不动。七保护身份只在保存的核对点一致，未测连续存活。原生0.32.15、qwen3-8b-uncensored及6d7230a9…9330摘要保持。CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315、context16384与输出256/2048不变。

原始计划NEEDS_FIXES及修订PASS_PLAN_ONLY均保留：两处已有grounding测试纳入写域并显式传2048，未删除原断言。产品准备独审完成后继续已授权Task2入口准备；本包actual/model/result-review allocation均0。E02仍0/3，旧E01/E03信用不迁移，T2/Owner未通过。

远端push此前被自动审批blocked by policy，本轮不重试；本地提交/tag/镜像由publication-readback独立记录。当前goal工具仍返回blocked，登记时明确为历史注册状态；本轮授权离线工作继续推进，不假称已恢复或完成全项目目标。
'''
with (N/'preparation-report.md').open('x',encoding='utf8',newline='\n') as f:f.write(text)
with (N/'progress.md').open('a',encoding='utf8') as f:f.write('\nTask1: product five-file change frozen '+head+'; final fresh '+str(v['tests'])+' checks PASS; independent preparation review next. Task2 remains pending.\n')
with (N/'verification/ledger-before-review.md').open('xb') as f:f.write((N/'progress.md').read_bytes())
print(json.dumps(dict(candidate=head,tests=v['tests'],report_sha256=hashlib.sha256((N/'preparation-report.md').read_bytes()).hexdigest())))
