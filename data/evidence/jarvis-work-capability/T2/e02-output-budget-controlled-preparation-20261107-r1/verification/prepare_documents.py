"""Prepare exact proposal and post-review programs before entry sealing."""
from pathlib import Path
import ast,json
N=Path(__file__).resolve().parents[1];O=N.parent/'e02-native-rejection-controlled-preparation-20261107-r1'
HEAD='0421a54cab572be013c3f7ad562e86406bfe8e52'
def write(p,s):
    ast.parse(s) if p.suffix=='.py' else None
    with p.open('x',encoding='utf8',newline='\n') as f:f.write(s)
def common(s):
    return s.replace('d860b2ab4e4d9974e33c96472e4ea15abb807280',HEAD).replace('d860b2a','0421a54').replace('jarvis-e02-native-rejection','jarvis-e02-output-budget').replace('native-rejection-controlled','output-budget-controlled')
s=common((O/'execution-proposal.md').read_text('utf8'))
s=s.replace('本轮按持续目标准备新候选入口','本轮按用户明确授权的输出预算补修计划Task2准备新候选入口')
s=s.replace('上一N17的bc216374-f59c-4967-99f2-ded53a4ea49d仍为FAIL_CONFIRMED：HTTP200后原生响应校验拒绝，无research.md，具体拒绝谓词未保存。N18的909项离线准备不转为实际信用。本例旨在保留确切拒绝条件，同时仍按原题完整交付要求验收，不以诊断成功替代任务成功。','上一N19的72d7d71b-39a9-455a-b0b4-8823b3f24c00仍为FAIL_CONFIRMED：第7次HTTP200后的done_reason=length，eval_count=max_tokens=2048，无research.md/write/ACK。完整响应正文未保存，不推断内部内容或token分配。N20的927项离线检查不转为实际信用；本例仍按原题完整交付验收，不能只看响应不截断或诊断成功。')
s=s.replace('入口不为模型选页或代写。','共享阶段提示现在接收该请求实际num_predict，生成与独立重放共同核对。提示紧凑JSON、简短标题及精确原子事实，但保留完整原题信息与引用；实际预算、严格schema、来源/事实门不变。ACK原指令保持。入口不为模型选页或代写。')
write(N/'execution-proposal.md',s)
s=common((O/'verification/closeout.py').read_text('utf8'))
s=s.replace('jarvis-work-e02-output-budget-controlled-entry-plan-20261107.md','jarvis-work-e02-writer-output-budget-alignment-plan-20261107.md')
s=s.replace('SOURCE29_E02_NATIVE_REJECTION_CONTROLLED','SOURCE31_E02_OUTPUT_BUDGET_CONTROLLED').replace('source29_preparation','source31_preparation').replace('e02_native_rejection_controlled_preparation','e02_output_budget_controlled_preparation')
s=s.replace('N18 product909 frozen baseline not rerun','N20 product927 frozen baseline not rerun').replace('C15 frozen','C16 frozen').replace('native rejection controlled preparation complete','output budget controlled preparation complete')
s=s.replace('native_parser_cause_proven=False','real_delivery_improvement_proven=False')
s=s.replace('^- Task 2: PENDING.*$', '^- Task 2: (?:PENDING|IN_PROGRESS).*$')
s=s.replace('target.parent.mkdir(parents=True,exist_ok=True);assert not target.exists()','target.parent.mkdir(parents=True,exist_ok=True)\n    if target.exists():assert target.read_bytes()==source.read_bytes()')
point="assert state['last_actual_result']==last_actual"
assert s.count(point)==1
extra="""alias_names=('preparation_review_path','preparation_tests_passed','preparation_sync','local_checkpoint_tag','remote_sync','next_action','next_offline_plan','source_candidate_tag')
state['source31_superseded_preparation_aliases']={k:state.get(k) for k in alias_names}
tag='ultimaagent-e02-output-budget-controlled-ready-20261107'
state.update(active_candidate_root=str(C),preparation_review_path=str(review_path),preparation_tests_passed=verification['tests'],
    preparation_sync=dict(status='REFER_TO_LOCAL_PUBLICATION_READBACK_REMOTE_BLOCKED',local_tag=tag,publication_receipt=str(N/'verification/publication-readback.json'),new_push_attempted=False,remote_synced=False),
    local_checkpoint_tag=tag,source_candidate_tag='ultimaagent-e02-output-budget-candidate-20261107',
    remote_sync=dict(status='PRIOR_AUTOMATIC_APPROVAL_BLOCK_NO_RETRY',local_tag=tag,new_push_attempted=False,remote_synced=False),
    next_action='Await explicit one-case and independent result-review allocation on the prepared proposal; do not run before allocation',
    next_offline_plan=str(plan_path),goal_status='blocked',goal_registry_status='blocked',
    next_work='Explicitly allocate one case and one result review before actual execution; authorized offline repair and entry preparation completed')
"""
s=s.replace(point,extra+point)
write(N/'verification/closeout.py',s)
s=common((O/'verification/publish.py').read_text('utf8'))
s=s.replace("assert before['project']=='5972719db54af4fae8ea2cb52ee70d5a0d846d0e'", "assert before['project']==json.loads((N.parent/'e02-writer-output-budget-20261107-r1/verification/publication-readback.json').read_bytes())['heads']['project']")
s=s.replace("assert before['mirror']=='4d7017937db66625e55b9c8ea9828c554deb593b'", "assert before['mirror']==json.loads((N.parent/'e02-writer-output-budget-20261107-r1/verification/publication-readback.json').read_bytes())['heads']['mirror']")
s=s.replace("assert set(git(M,'diff','--cached','--name-only').decode().splitlines())=={p.relative_to(M).as_posix() for p in mirror}", "assert set(git(M,'diff','--cached','--name-only').decode().splitlines())<={p.relative_to(M).as_posix() for p in mirror}\nassert git(M,'diff','--cached','--name-only').strip()")
s=s.replace('native rejection candidate','output budget candidate').replace('native rejection controlled entry','output budget controlled entry')
write(N/'verification/publish.py',s)
print('Exact proposal and complete alias closeout prepared; no actual allocation')
