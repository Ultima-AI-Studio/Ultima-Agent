from pathlib import Path
import datetime as dt
import hashlib
import json
E=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf-8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2);f.write('\n')
assert sha(E/'manifest.json')=='2975e0f947be408baaa4222f8dd9fd4fbd1cb481adf005f38ea1bc4d8b91c3aa'
assert sha(E/'entry-manifest.json')=='6658149a128fe10c50f4b197a9a7cef8133bb16434e1ada4897b523def31bba8'
for row in load(E/'manifest.json')['files']:assert sha(E/row['path'])==row['sha256']
value=dict(schema=1,kind='USER_PREPARATION_REVIEW_ONLY',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    source='user_reply',question_call='call_7761d0ac06d34e8c9e128f2b15819826',answer='授权一次修复包只读独立复核（推荐）',
    approved=True,scope='one_readonly_fixed_source_independent_review',review_cap=1,
    manifest_sha256=sha(E/'manifest.json'),entry_manifest_sha256=sha(E/'entry-manifest.json'),
    actual_case_allocation=0,actual_result_review_allocation=0,model=0,profile=0,UI=0,audio=0,service_actions=0)
save(E/'review/fixed-source-review-approval.json',value)
save(E/'review/fixed-source-review-consumed.json',dict(scope=value['scope'],consumed=1,remaining=0,
    approval_sha256=sha(E/'review/fixed-source-review-approval.json'),reviewer='/root/review_e02_source13_root_entry_fix1',
    actual_authority=False,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat()))
state=E.parent/'current-run.json';s=load(state)
s.update(updated_utc=dt.datetime.now(dt.timezone.utc).isoformat(),phase='SOURCE13_E02_ROOT_ENTRY_FIXED_SOURCE_REVIEW',
    active_review_agent='/root/review_e02_source13_root_entry_fix1',e02_root_entry_current_source_review='IN_PROGRESS_AUTHORIZED_ONCE')
s['next_action_scope']=dict(scope=value['scope'],actual_case_allocation=0,actual_result_review_allocation=0,
    preparation_review_consumed=1,preparation_review_remaining=0,authority_issued=False)
state.write_bytes((json.dumps(s,ensure_ascii=False,indent=2)+'\n').replace('\n','\r\n').encode())
print('One user-authorized fixed-source read-only review consumed; actual allocations remain zero.')
