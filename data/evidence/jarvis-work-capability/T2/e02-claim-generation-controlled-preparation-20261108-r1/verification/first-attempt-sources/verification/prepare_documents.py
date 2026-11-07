"""Prepare proposal, honest offline report and local closeout programs before sealing."""
from pathlib import Path
import ast,importlib.util,json
N=Path(__file__).resolve().parents[1];O=N.parent/'e02-output-structure-controlled-preparation-20261108-r1'
B=N.parent/'e02-claim-generation-contract-20261108-r1'
HEAD='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b';OLD='bf7f7a9cf0e4ba559c29daa388c00379d12d345a'
def write(p,s):
    if p.suffix=='.py':ast.parse(s)
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(s)
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
def common(s):
    return (s.replace('jarvis-e02-output-structure-r2','jarvis-e02-claim-generation-r1')
        .replace('e02-output-structure-diagnostics-20261108-r2',B.name)
        .replace('ultimaagent-e02-output-structure-candidate-20261108-r2','ultimaagent-e02-claim-generation-candidate-20261108-r1')
        .replace('ultimaagent-e02-output-structure-controlled-ready-20261108','ultimaagent-e02-claim-generation-controlled-ready-20261108-r1')
        .replace('jarvis-work-e02-output-structure-controlled-entry-plan-20261108','jarvis-work-e02-claim-generation-controlled-entry-plan-20261108')
        .replace('jarvis-work-t2-e02-output-structure-controlled-preparation-20261108','jarvis-work-t2-e02-claim-generation-controlled-preparation-20261108')
        .replace('e02-output-structure-controlled-20261108.md','e02-claim-generation-controlled-20261108.md')
        .replace(OLD,HEAD).replace('bf7f7a9','d8f8d97'))
spec=importlib.util.spec_from_file_location('claim_entry_readback',N/'verification/verify_preparation.py');v=importlib.util.module_from_spec(spec);spec.loader.exec_module(v)
r=v.verify();assert r['tests']==350 and r['harness_unique']==289
s=common((O/'execution-proposal.md').read_text('utf8')).replace(O.name,N.name)
s=s.replace('本轮按输出结构诊断提案及持续原工单目标准备冻结诊断候选入口','本轮按用户call_5411de619a6c4de0bab414126a228c7d明确授权的离线补修计划Task3准备冻结候选入口')
old='上一N21的9dbe192a-3bc1-4a4d-a218-581846d5f654及N19旧例均保留FAIL_CONFIRMED：第7次HTTP200后的done_reason=length，eval_count=max_tokens=2048，无research.md/write/ACK。旧包未保存正文，不能据此判定JSON是否残缺或推断token分配。N24的979项产品/兼容检查和本入口350项检查不转为实际信用；本例仍按原题完整交付验收，不能只看诊断是否捕获。获得实际证据后才决定后续结构、终止兼容或事实导航的最小修复，不先重写交付事务。'
new='上一实际c4caa739-c466-44f3-866b-0c57ea8c5e40保持FAIL_CONFIRMED：第7次HTTP200，done_reason=length、eval_count=max_tokens=2048，未交付research.md/write/ACK/runtime END。完整3818字符正文证实两个短句重复50/49次，JSON在pos1339处未闭合，并存在独审发现的引用错配与未读S4风险。新候选仅要求代码claim先输出精确operation再描述该语句可支持的事实，移除operation之前的任意长前缀。严格schema、writer、引用/事实/覆盖门和原预算保持；后缀及非代码字符串仍可能重复，不能推断已解决截断或保证2048内完成。N34的1004项离线检查和本入口350项检查不转为实际信用；本例仍按完整原题交付验收。'
s=once(s,old,new)
s+='\n## 本轮离线边界与待核验项\n\n本轮准备没有模型调用、网络请求、UI/音频或生产服务操作。运行态为PENDING_FRESH_ACTUAL_PREFLIGHT；保存的旧原生版本、模型及七保护身份回执仅供历史追溯，不能证明当前运行态。只有明确分配本例后，原run_released才在同一原始时钟内重新核对全部保护身份、原生监听归属和元数据/模型摘要，以及原adapter隔离端口门。任一检查失败即终止本次单例，不绕过、不重试、不操作受保护进程。现有默认模型及语音链路不因本提案修改。\n'
write(N/'execution-proposal.md',s)
s=common((O/'verification/closeout.py').read_text('utf8'))
s=s.replace('source33','source35').replace('SOURCE33_E02_OUTPUT_STRUCTURE','SOURCE35_E02_CLAIM_GENERATION')
s=s.replace("goal_status='active',goal_registry_status='active'","goal_status='blocked',goal_registry_status='blocked'")
s=s.replace('N24 product979 frozen evidence not rerun','N34 product994 plus compatibility4 and official reference6 frozen evidence, not rerun')
s=s.replace('Frozen diagnostic controlled entry preparation','Authorized offline claim-generation controlled entry preparation')
s=s.replace('e02_output_structure_controlled_preparation','e02_claim_generation_controlled_preparation')
s=s.replace('protected_at_readonly_point=True,real_output_structure_not_yet_captured=True','current_runtime_verified=False,live_runtime_readiness=\'PENDING_FRESH_ACTUAL_PREFLIGHT\',new_candidate_actual_output_not_yet_captured=True')
s=s.replace("status='READY_AWAITING_EXPLICIT_ONE_CASE_ALLOCATION'","status='READY_OFFLINE_AWAITING_EXPLICIT_ALLOCATION_AND_FRESH_PREFLIGHT'")
s=s.replace("phase='SOURCE35_E02_CLAIM_GENERATION_CONTROLLED_READY_AWAITING_ALLOCATION'","phase='SOURCE35_E02_CLAIM_GENERATION_CONTROLLED_READY_AWAITING_ALLOCATION',live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT'")
s=s.replace("verification=verification,actual_cases=0","verification=verification,live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT',current_runtime_verified=False,actual_cases=0")
s=s.replace('E02 output structure controlled preparation complete','E02 claim generation controlled preparation reviewed')
s=s.replace('Explicit one-case allocation is required to capture actual output structure evidence','Explicit one-case allocation is required; original fresh runtime preflight must pass before model work')
s=s.replace("'- Task 2: COMPLETE; independent preparation PASS and missing-grant refusal; local publication recorded separately.'", "'- Task 2: PREPARATION_REVIEW_COMPLETE; independent preparation PASS and missing-grant refusal; publication/final readback recorded in later receipts.'")
write(N/'verification/closeout.py',s)
s=common((O/'verification/publish.py').read_text('utf8')).replace('bind output structure diagnostic candidate','bind operation-first claim candidate').replace('mirror output structure controlled entry','mirror claim generation controlled entry')
write(N/'verification/publish.py',s)
s=common((O/'verification/final_readback.py').read_text('utf8')).replace("state['goal_status']==state['goal_registry_status']=='active'","state['goal_status']==state['goal_registry_status']=='blocked'")
s=s.replace("'- Task 2: COMPLETE;'","'- Task 2: PREPARATION_REVIEW_COMPLETE;'").replace('product_checks=979','product_checks=1004')
s=once(s,"assert ready['missing_grant_rejected'] and not ready['run_once_called']", "assert ready['missing_grant_rejected'] and not ready['run_once_called']\nassert ready['live_runtime_readiness']==state['live_runtime_readiness']=='PENDING_FRESH_ACTUAL_PREFLIGHT' and ready['current_runtime_verified'] is False")
s=s.replace("current_aliases_match=True,last_actual_preserved=True", "current_aliases_match=True,live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT',current_runtime_verified=False,last_actual_preserved=True")
write(N/'verification/final_readback.py',s)
report='''# E02 代码事实生成起点候选：受控入口准备

状态：待独立准备审查。

原工单wo-ultimaagent-20261101-0021 / T2。产品候选d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b，独立产品准备PASS，精确1434成员已封存；本地产品准备提交915ecdf5，镜像c2d34b9，最终读回PASS。本入口只绑定已冻结产品，不再改产品代码。

本轮用户授权离线补修、必要独审和入口准备，实际研究及独立结果复核分配均0；模型调用0，网络请求0，无UI/音频/生产服务操作。E02仍0/3，T2/Owner未通过。旧E01/E03通过不移作本候选信用。目标工具登记仍blocked，和本轮已授权的离线工作分开记录。

本候选改动只移除代码claim中精确operation之前的任意前缀，并使共享生成/重放提示要求operation开头。原strict、writer、来源/引用、事实、覆盖、预算、写入/读回及ACK保持。原真实正文重复50/49次、引用错配和未读S4证据保留；后缀与非代码自由字符串仍能耗尽预算，不能说实际研究交付已修好。

新鲜入口检查350项通过：adapter按JUnit身份去重289项，binding16、entry34、boundary11。五组adapter原始291项含2个既有交叉身份；八组最终检查同源码，失败/错误/跳过均0，最多2组并发。继续覆盖v3/v4/v5导出、FULL/EXCERPTS/OMITTED_POLICY、原16384字节上限、矛盾状态拒绝和零验收信用。原obsolete-v4 RED仅保留历史，不伪造新失败。产品1004项（994产品/4兼容/6官方参考转换）是本轮先前已封存证据，没有重跑或加进350。审计denied为空、预期冷导入探针已关闭；操作审计不等于OS抓包，OS数据包数量未测量。

完整78个产品源码、1602项输入文件摘要绑定当前冻结根；check_inputs另核对其输入manifest、bindings和scope三文件，不能混淆两种计数。entry/bindings/adapter的全部函数/class AST与上一入口一致。原question、四来源corpus、current8B摘要、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/rootwork275/cleanup310/seal315、writer2048/read-ACK256及所有字节上限保持。

运行态明确PENDING_FRESH_ACTUAL_PREFLIGHT。准备期未运行旧read_runtime.py，也未读取/api/version或/api/tags。旧原生/保护身份快照只作为历史摘要引用；不声称当前七保护身份或端口状态已通过。另行明确分配后，原run_released与adapter仍须在原同一时钟内执行全部新鲜身份、监听/隔离端口和模型摘要门，失败消耗单例、不得绕过或重试。

旧产品与入口、实际FAIL、依赖、15个无关文件均保全；新根没有release、controller-authority、native-preflight、actual或实际ledger。原平台准备答复已准确记录为call_5411de619a6c4de0bab414126a228c7d，actual/result-review均0，不能签成actual1。

准备登记期间root误用PowerShell ConvertFrom-Json，遇到T2/t2异大小写键后继续执行，曾将current-run写为空值。已保留坏字节并从此前本轮快照恢复全部原键和last_actual，重放仅本轮注册字段，Python读回PASS。后续状态使用Python JSON。旧registration回执是历史时点，最终检查独立核对现态；该失误不是产品测试失败，也不被删除或包装为全过程无错误。

独审PASS后只创建harness准备审批并调用read_ready/read_release证明缺少grant会拒绝；不调用run_once或run_released。新单例提案见同目录execution-proposal.md，完整原题、原8B、原预算、失败不重试与独立事实复核门全部保留。

本地提交/tag、三份镜像和最终读回由后置独立回执证明，不伪称属于先前封存manifest。先前远端push和scratch删除被自动审批blocked by policy拦截，本轮不重试、不换通道，保留技能ledger副本。
'''
write(N/'preparation-report.md',report)
print(json.dumps(dict(status='DOCUMENTS_AND_CLOSEOUT_PREPARED',tests=r['tests'],sources=78,input_files=1602,actual=0,live_runtime='PENDING_FRESH_ACTUAL_PREFLIGHT')))
