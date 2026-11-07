"""Close the authorized offline repair after exact-candidate independent review."""
from pathlib import Path
import datetime as dt, hashlib, json, re

N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo/docs/shared/research/ultimaagent-work-capability')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-coverage/UltimaAgent')

def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)

manifest=json.loads((N/'manifest.json').read_bytes());HEAD=manifest['candidate'];MANIFEST=sha(N/'manifest.json')
review_path=N/'review/independent-preparation-review.json'
review=json.loads(review_path.read_bytes())
assert review['verdict']=='PASS_PREPARATION_ONLY' and review['manifest_sha256']==MANIFEST and review['candidate']==HEAD
assert review['actual_run_authorized'] is False
for name,digest in manifest['files'].items():assert sha(N/name)==digest,name
for name,digest in json.loads((N/'inputs/current-inputs.json').read_bytes())['files'].items():assert sha(Path(name))==digest,name
checks=json.loads((N/'verification/offline-post-commit-readback.json').read_bytes())
before_runtime=json.loads((N/'verification/runtime-readiness.json').read_bytes())
after_runtime=json.loads((N/'verification/runtime-after.json').read_bytes())
assert before_runtime['verdict']==after_runtime['verdict']=='PASS_READONLY_RUNTIME_IDENTITY'
plan=R/'docs/plans/jarvis-work-e02-source-coverage-budget-plan-20261107.md'
report=R/'docs/reports/jarvis-work-t2-e02-source-coverage-budget-repair-20261107.md'
text=f'''# E02 读取预算与来源覆盖联动补修完成

原单 wo-ultimaagent-20261101-0021 / T2；完成范围为本轮授权的两项产品修复、离线验证和独立准备审查。产品候选 {HEAD}，基线 ee1bef61f04169c64978538dbc4ba799ef7be6c0。当前 E02 仍 0/3，T2/Owner 未通过，没有新实际研究分配。

## 实际修改

六次读取额度联动至少三来源覆盖。生成与独立重放共用相位 schema：仅从可信 catalogue 取可用来源，只认已确认的非空证据卡；已发行页和待提升的确认页按原顺序计入一次。当剩余读取数正好等于缺少的来源数时，inspect 的 source_id 只能选择尚未覆盖的可用来源。有余量或已覆盖三来源时，仍可同源补读；剩余额度或可用来源不足时关闭 inspect。页起点、来源相关性、事实和写作仍由当前 8B 决定。

未写入时 final_answer 的合法内容固定为“本次研究未交付。”；任意“已保存 research.md”不再是合法拒绝分支。只有通过原写入、读回和 proof 门的 ACK 相位才保留自由确认文字。研究失败的公开回复同样明确“未交付”；若存在写入效果则补充“部分操作可能已生效，请核对结果”，不虚称文件必定不存在。非研究失败文案保持。

复用既有 OpenJarvis inspect/write、native_react、JSON schema、ledger 和重放，没有引入新 planner、拼写事实或替模型生成报告。仅四个产品模块和三个测试文件变化；原生传输、响应解析、HTTP 诊断、默认模型和既有事实/引用/写入/ACK 门未改。

## 当前验证

旧代码新增测试 RED：39 个断言失败、1 通过、errors=0，真实 SDK mock 复现第五次同源仍消耗读取额度、虚假完成文本进入 final。修复后当前字节去重 {checks['tests']} 项 PASS，其中产品 {checks['product_tests']}、原受限导出兼容 {checks['export_interface_tests']}；新增目标测试 40 项。完整 SDK MockTransport 实际完成六次读取（S1 四次、S2/S3 各一次）、write、ACK、文件读回和独立重放，共八个模拟 POST；扩大第五次读取 schema 的一致性篡改也被重放拒绝。

初次传输回归 103 通过/1 失败保留：旧 blank_final 断言期待较晚的空白检查，新固定 enum 正确提前拒绝。仅更新该错误预期，保留无写入、无 ACK、确认页未提升等全部断言。合法拒绝 fixture 更新为固定文本；1000 字符私有诊断边界移至合法 ACK 后的独立 artifact 校验失败场景，保留敏感、超长、伪造和迟变更负例。最终所有分片重新按当前源码快照执行，旧执行不重复计数。

原审计守卫、90 秒分片和两个既有 live/HTTP/junction 排除保持。审计回执清洁，不冒称操作系统抓包；实际模型调用、实际用例、UI/音频及服务操作均为 0。计划独审 PASS，封存准备包独审 PASS_PREPARATION_ONLY。Manifest SHA256 {MANIFEST}；review SHA256 {sha(review_path)}。

## 保全和交付边界

只读核对点 {before_runtime['recorded_at']}、{after_runtime['recorded_at']} 的七个保护进程身份、Ollama 0.32.15 和当前 qwen3-8b-uncensored 摘要相符；不声称连续存活。N13/N12/N11 旧失败、冻结候选、依赖清单和九个无关文件逐字节保全。上一实际例 91406fa9-5952-4e3a-99af-a94c8857c8d3 仍为 FAIL_CONFIRMED，六读只覆盖两来源，无 research.md/write/ACK，无重试。旧 E01/E03 通过记录不迁移为本候选信用。

原题四来源、至少三来源门、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8，service260/client300/root275/cleanup310/seal315 秒和上下文/实体/输出预算保持。只用当前 8B；不使用 14B。本轮证明离线约束和对接正确，不证明真实模型能完成原题；旧写入相位 HTTP500 的原生兼容原因仍未确证。

下一步先为本候选准备新的受控入口及源码/依赖绑定，更新受限测试中公开固定未交付文案与私有 final 对象的区分，不能照搬旧 candidate/manifest/authority。之后明确分配单例才能取得真实 8B 请求回执；事实、覆盖、写入和 ACK 仍按原门验收。本轮没有创建实际入口、authority、release 或模型重试。

本地产品候选保留在隔离分支 codex/jarvis-e02-source-coverage，不覆盖已封存的旧工作区。项目文档和 UltimaDocs 镜像按本地 commit/tag/readback 收口。此前 GitHub push 被自动审批以 blocked by policy 拒绝，本轮未重试，remote_synced=false。

证据根：{N.as_posix()}
'''
for p in (report,N/'completion-report.md'):
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(text)
pairs=[(plan,M/'plans'/plan.name),(report,M/'reports'/report.name)]
for source,target in pairs:
    target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(source.read_bytes())
    assert sha(source)==sha(target)
paths=[R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),R/'.superpowers/sdd/jarvis-work-e02-source-coverage-budget-plan-20261107/progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])]);last_actual=state['last_actual_result']
summary=f"E02读取预算/来源覆盖与明确未交付补修完成：候选{HEAD[:7]}，{checks['tests']}项当前字节检查及独立准备PASS；8B/原预算保持，实际例与模型调用0；上一FAIL保留，E02仍0/3，待新候选受控绑定。"
state.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE24_E02_COVERAGE_OFFLINE_COMPLETE',workflow_status='blocked',stage_queue_state='BLOCKED',active_evidence=str(N),active_preparation_root=str(N),active_report=str(report),active_plan=str(plan),active_product_candidate=HEAD,active_product_root=str(C),active_review_agent=None,preparation_status='PASS_OFFLINE_AND_INDEPENDENT_REVIEW',preparation_review='PASS_PREPARATION_ONLY',preparation_test_count=checks['tests'],preparation_test_scope=f"{checks['product_tests']} product + {checks['export_interface_tests']} restricted exporter; offline only",e02_execution_released=False,live_gate_released=False,next_stage_released=False,actual_case_allocation_remaining=0,result_review_allocation_remaining=0,active_preparation=dict(root=str(N),candidate=HEAD,status='PASS_PREPARATION_ONLY',tests=checks['tests'],manifest_sha256=MANIFEST,review_sha256=sha(review_path),actual_authority=False),active_candidate_acceptance=dict(E01='NOT_REVALIDATED_ON_THIS_CANDIDATE',E03='NOT_REVALIDATED_ON_THIS_CANDIDATE',E02_controlled_passed=0,required=3,old_credit_transferred=False),next_action_scope=dict(authorized=True,source=str(N/'inputs/direct-user-decision.json'),scope='Coverage-budget and explicit non-delivery offline repair',status='COMPLETED',actual_case_allocation=0,model_calls=0,service_operations=0),next_proposal=dict(path=str(plan),status='IMPLEMENTED_OFFLINE_NEXT_CONTROLLED_BINDING',product_changes_authorized=True,actual_case_allocation=0),e02_source_coverage_offline=dict(candidate=HEAD,completed=True,tests=checks['tests'],review='PASS_PREPARATION_ONLY',actual_cases=0,model_calls=0,service_operations=0,protected_at_readonly_points=True,native_parser_cause_proven=False,remote_synced=False))
assert state['last_actual_result']==last_actual
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-07 E02 source coverage repair completion\n\n'+summary+'\n报告：'+str(report)+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
queue,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=queue
texts[str(paths[4])]=before[str(paths[4])].decode('utf8')+f'\n- Task 1: complete, candidate {HEAD}, final guarded source checks {checks["tests"]} PASS.\n- Task 2: complete, shared prewrite final and public non-delivery/partial-effects behavior verified; independent preparation PASS {sha(review_path)}.\n- Final review: PASS_PREPARATION_ONLY, no actual release; old failures and protected identities preserved at recorded points.\n- Ruling: retain isolated candidate and evidence under the approved plan; no merge/cleanup menu because production integration is outside this offline stage.\n'
snap=N/'verification/closeout-before';snap.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(snap/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/closeout-registration.json',dict(summary=summary,candidate=HEAD,manifest_sha256=MANIFEST,review_sha256=sha(review_path),before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},mirror=[dict(source=str(s),target=str(t),sha256=sha(s)) for s,t in pairs],last_actual_preserved=True,actual_cases=0,model_calls=0,remote_synced=False))
print(json.dumps(dict(summary=summary,report=str(report),mirror_files=len(pairs)),ensure_ascii=False))
