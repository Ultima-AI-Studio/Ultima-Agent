"""Record the explicit current answer on the existing work order; no new case here."""
from pathlib import Path
import datetime as dt,hashlib,json,re,subprocess,sys
N=Path(__file__).resolve().parents[1];R=N.parents[4]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
question='候选 bf7f7a9 的证据采集入口已完成 350 项新鲜检查、独立准备审查和本地提交/tag/镜像读回（项目 dff378f，镜像 17b53ac）。是否按[执行提案](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-output-structure-controlled-preparation-20261108-r1/execution-proposal.md)，明确分配一例当前 8B 的原题四来源研究及一次只读独立结果复核？保持原预算和完整原题验收，失败不重试；无 UI、音频或生产服务操作。需要此次分配，因为你此前要求“明确分配单例后”才实跑，当前额度为 0。'
decision=dict(source='explicit_user_question_reply_in_current_conversation',question_id='call_5c06d21b59b8475b873814f857990cc3',question=question,
    answer='明确分配一例当前 8B 研究及一次独立结果复核（推荐）',actual_case_allocation=1,result_review_allocation=1,retry=0,
    candidate='bf7f7a9cf0e4ba559c29daa388c00379d12d345a',model='qwen3-8b-uncensored',
    manifest_sha256=sha(N/'manifest.json'),review_sha256=sha(N/'review/independent-preparation-review.json'),
    execution_proposal_sha256=sha(N/'execution-proposal.md'),recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
assert decision['manifest_sha256']=='ea078190d78a340d3db06092bb050662a4a59e37e2f327c595199073b195eb1f'
assert decision['review_sha256']=='85dc915c2712f6af7132456904dfa4d429e97b7a85aff4de2bb762fa80c22fe4'
assert not any((N/name).exists() for name in ('actual','release','controller-authority'))
save(N/'verification/allocated-user-decision.json',decision)
paths=[R/'data/evidence/jarvis-work-capability/T2/current-run.json',R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md',Path('H:/UltimaAI/_shared/queue/global-queue-index.md'),
    N/'progress.md']
before={str(p):p.read_bytes() for p in paths};state=json.loads(before[str(paths[0])])
assert state['active_evidence']==str(N) and state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
state.update(phase='SOURCE33_E02_OUTPUT_STRUCTURE_CONTROLLED_ALLOCATED',workflow_status='executing',stage_queue_state='EXECUTING',
    actual_case_allocation_remaining=1,result_review_allocation_remaining=1,e02_execution_released=True,live_gate_released=True,
    next_stage_released=False,updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    next_action_scope=dict(authorized=True,source=str(N/'verification/allocated-user-decision.json'),scope='One current8B controlled E02 case and one read-only independent result review',
        actual_case_allocation=1,result_review_allocation=1,retry=0,service_operations=0),
    current_one_case_allocation=dict(question_id=decision['question_id'],candidate=decision['candidate'],status='ALLOCATED_NOT_INVOKED',
        remaining=1,result_review_remaining=1,retry=0))
state['source33_preparation']['status']='ALLOCATED_FOR_ONE_ACTUAL_CASE'
state['active_preparation']['status']='ALLOCATED_FOR_ONE_ACTUAL_CASE'
state['next_proposal']['status']='EXPLICIT_ONE_CASE_ALLOCATED'
state['next_proposal']['actual_case_allocation']=1
state['next_proposal']['result_review_allocation']=1
state['next_action']=state['next_work']='Run the explicitly allocated current8B case once, then independently review its first result; no retry'
summary='E02 bf7f7a9已明确分配一例当前8B研究及一次结果独审；原预算、失败不重试；正在只读准入后执行，尚无接受信用。'
texts={str(paths[0]):json.dumps(state,ensure_ascii=False,indent=2)+'\n'}
wo,count=re.subn(r'(?m)^- 状态：.*$','- 状态：'+summary,before[str(paths[1])].decode('utf8'),count=1);assert count==1
append='\n\n## 2026-11-08 E02 output structure controlled one-case allocation\n\n'+summary+'\n用户答复：'+decision['question_id']+'；提案：'+str(N/'execution-proposal.md')+'\n'
texts[str(paths[1])]=wo+append;texts[str(paths[2])]=before[str(paths[2])].decode('utf8')+append
queue,count=re.subn(r'(?m)^\| UltimaAgent \| wo-ultimaagent-20261101-0021 \|.*$','| UltimaAgent | wo-ultimaagent-20261101-0021 | executing | '+summary+' |',before[str(paths[3])].decode('utf8'));assert count==1
texts[str(paths[3])]=queue
texts[str(paths[4])]=before[str(paths[4])].decode('utf8')+'\n- Authorized execution continuation: explicit call_5c06d21b59b8475b873814f857990cc3, actual1/result-review1/retry0; execute the frozen entry once, then seal and independently review the first result. No product changes or repeated tests.\n'
snap=N/'verification/allocation-before';snap.mkdir(exist_ok=False)
for i,p in enumerate(paths):
    assert p.read_bytes()==before[str(p)];(snap/(str(i)+'-'+p.name)).write_bytes(before[str(p)])
for p in paths:p.write_text(texts[str(p)],encoding='utf8',newline='\n')
save(N/'verification/allocation-registration.json',dict(decision_sha256=sha(N/'verification/allocated-user-decision.json'),
    before={p:hashlib.sha256(b).hexdigest() for p,b in before.items()},after={str(p):sha(p) for p in paths},actual_invocations=0))
q=Path('H:/UltimaAI/_shared/queue');result=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(q/'queue-status-gen.py')],capture_output=True,text=True,check=True,creationflags=subprocess.CREATE_NO_WINDOW)
save(N/'verification/allocation-queue-refresh.json',dict(exit_code=result.returncode,stdout=result.stdout,stderr=result.stderr,queue_sha256=sha(q/'queue-status.json'),semantic_registration_only=True))
print(json.dumps(dict(question_id=decision['question_id'],actual_allocated=1,review_allocated=1,invoked=0,queue=result.stdout.strip()),ensure_ascii=False))
