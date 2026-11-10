"""Register this root read-only audit; no product imports, dispatch, or network."""
from pathlib import Path
import datetime, hashlib, json

R=Path('H:/UltimaAI/UltimaAgent')
T=R/'data/evidence/jarvis-work-capability/T2'
N=T/'e02-output-structure-review-20261107-r1'
PLAN=R/'docs/plans/jarvis-work-e02-output-structure-review-plan-20261107.md'
G=Path('H:/UltimaAI/_shared/queue/global-queue-index.md')
WO=R/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md'
STAGE=R/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'
STATE=T/'current-run.json'
NOW=datetime.datetime.now(datetime.timezone.utc).isoformat()
def digest(b): return hashlib.sha256(b).hexdigest()
def write_json(path,obj):
    with path.open('x',encoding='utf8',newline='\n') as f:
        f.write(json.dumps(obj,ensure_ascii=False,indent=2)+'\n')
N.mkdir(exist_ok=True)
(N/'history').mkdir(exist_ok=False)
before={}
for label,path in [('global',G),('work-order',WO),('stage',STAGE),('current-run',STATE)]:
    data=path.read_bytes()
    (N/'history'/f'{label}-before{path.suffix}').write_bytes(data)
    before[str(path)]=digest(data)
scope=dict(recorded_utc=NOW,original_order='wo-ultimaagent-20261101-0021',
    user_instruction='审查输出结构与交付方式，明确需要补充的截断证据，再确定代码改动；继续保持当前 8B、原预算和完整原题验收要求。',
    activity='ROOT_READONLY_STRUCTURE_AUDIT',independent_review=False,
    plan=str(PLAN),plan_sha256=digest(PLAN.read_bytes()),candidate='0421a54cab572be013c3f7ad562e86406bfe8e52',
    product_changes=0,actual_case_allocation=0,model_calls=0,independent_review_allocation=0,retry=0,
    original_budget_and_acceptance_preserved=True,registration_before=before)
write_json(N/'scope.json',scope)
state=json.loads(STATE.read_bytes())
assert state['phase']=='SOURCE31_E02_OUTPUT_BUDGET_CONTROLLED_FAIL_REVIEWED'
state.update(updated_utc=NOW,phase='SOURCE31_E02_OUTPUT_STRUCTURE_READONLY_REVIEW',
    active_readonly_review_root=str(N),readonly_review=dict(status='IN_PROGRESS',scope=str(N/'scope.json'),independent=False),
    next_work='Read-only output structure and delivery review; identify missing truncation evidence before selecting product changes; no new actual case allocated')
STATE.write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
status='E02 输出结构/交付方式只读审查：核对两次 length 失败，先确定截断证据缺口；0421a54冻结、当前8B/原预算/原题保持，产品与实跑新增0。'
for path in (WO,STAGE):
    raw=path.read_bytes()
    addition='\n\n## 2026-11-07 E02 output structure read-only review\n\n'+status+'\n计划：'+str(PLAN)+'\n'
    path.write_bytes(raw+addition.encode('utf8'))
raw=G.read_bytes();lines=raw.splitlines(keepends=True)
hits=[i for i,l in enumerate(lines) if l.startswith(b'| UltimaAgent | wo-ultimaagent-20261101-0021 |')]
assert len(hits)==1
i=hits[0];newline=b'\r\n' if lines[i].endswith(b'\r\n') else b'\n'
lines[i]=('| UltimaAgent | wo-ultimaagent-20261101-0021 | blocked | '+status+' |').encode('utf8')+newline
G.write_bytes(b''.join(lines))
write_json(N/'registration.json',dict(recorded_utc=NOW,status='REGISTERED_READONLY_NO_DISPATCH',
    files={str(p):digest(p.read_bytes()) for p in (PLAN,STATE,WO,STAGE,G)},product_or_actual_released=False))
print(json.dumps(dict(status='REGISTERED_READONLY_NO_DISPATCH',root=str(N)),ensure_ascii=False))
