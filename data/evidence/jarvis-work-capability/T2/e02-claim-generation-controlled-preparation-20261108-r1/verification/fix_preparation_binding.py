"""One bounded recovery of preparation identity and two migrated sampler fixtures; preserve first failures."""
from pathlib import Path
import ast,hashlib,json,re
N=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def write(p,s):
    if p.suffix=='.py':ast.parse(s)
    p.write_text(s,encoding='utf8',newline='\n')
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
def funcs(p):return {n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
before=N/'verification/first-attempt-sources';before.mkdir()
names=['inputs/direct-user-decision.json','code/entry.py','harness/test_adapter.py','harness/manifest.json','verification/verify_preparation.py','verification/prepare_documents.py','verification/prepare_review.py','verification/run_binding_checks.py','verification/run_entry_checks.py','verification/run_boundary_checks.py']
files={}
for name in names:
    source=N/name;target=before/name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(source.read_bytes())
    files[str(target)]=sha(target)
harness=sorted((N/'code').glob('harness-preparation-*/receipt.json'));assert len(harness)==5
offline=[N/'offline'/x for x in ('bindings-green','entry-final','boundary-green')]
for folder in [p.parent for p in harness]+offline:
    for p in folder.iterdir():
        if p.is_file():files[str(p)]=sha(p)
    for name in ('snapshot','harness-source','harness'):
        for p in (folder/name).rglob('*'):
            if p.is_file():files[str(p)]=sha(p)
files[str(N/'verification/batch-checks.json')]=sha(N/'verification/batch-checks.json')
batch=load(N/'verification/batch-checks.json');assert {k for k,v in batch.items() if v}=={'entry','export-green'}
assert load(N/'offline/entry-final/test-result.json')['failures']==1
save(N/'verification/first-attempt-index.json',dict(harness_receipts=[str(p) for p in harness],files=files,batch=batch,failures=3,actual_cases=0,root_cause=['Platform call id bypasses content-derived zero-allocation predicate in unchanged entry','Two sampler fixtures still use the removed arbitrary prefix'],preserved=True))
core=funcs(N/'code/entry.py')
p=N/'inputs/direct-user-decision.json';d=load(p)
d.update(source_question_id=d['question_id'],decision_id='user-message:sha256:'+hashlib.sha256(d['answer'].encode('utf8')).hexdigest(),identifier_is_platform_message_id=False,
    decision_id_note='Content-derived preparation binding, not a platform id; source_question_id records the actual offline authorization. Original direct-message predicate must reject zero actual/review counts.')
d['question_id']=d['decision_id'];write(p,json.dumps(d,ensure_ascii=False,indent=2)+'\n')
p=N/'code/entry.py';s=p.read_text('utf8');s,count=re.subn(r"(?m)^DIRECT_USER_DECISION_SHA='[^']*'","DIRECT_USER_DECISION_SHA='"+sha(N/'inputs/direct-user-decision.json')+"'",s);assert count==1;write(p,s)
assert funcs(p)==core
p=N/'harness/test_adapter.py';s=p.read_text('utf8');s=once(s,"claim='可见 client.run 调用，参数含", "claim='client.run 调用，参数含")
s=once(s,"raw_boundary=r'\\u0061client.run'","raw_boundary=r'client.run\\u0061'")
s=s.replace('aclient.run','client.runa');write(p,s)
p=N/'harness/manifest.json';h=load(p);h['files']={name:sha(N/'harness'/name) for name in h['files']};write(p,json.dumps(h,ensure_ascii=False,indent=2)+'\n')
for name in ('binding','entry','boundary'):
    p=N/'verification'/('run_'+name+'_checks.py');s=p.read_text('utf8')
    a="sys.argv[1] in (";start=s.index(a)+len(a);s=s[:start]+"'recovery-green',"+s[start:];write(p,s)
p=N/'verification/prepare_review.py';s=p.read_text('utf8');s=once(s,"('plan.md','execution-proposal.md','preparation-report.md')","('plan.md','execution-proposal.md','preparation-report.md','execution-rulings.md')");write(p,s)
p=N/'verification/verify_preparation.py';s=p.read_text('utf8')
s=once(s,"decision['identifier_is_platform_message_id'] is True","decision['identifier_is_platform_message_id'] is False")
s=once(s,"assert decision['decision_id']==decision['question_id']=='call_5411de619a6c4de0bab414126a228c7d' and decision['answer']=='授权离线补修、必要独审与入口准备（推荐）'", "assert decision['source_question_id']=='call_5411de619a6c4de0bab414126a228c7d' and decision['answer']=='授权离线补修、必要独审与入口准备（推荐）'\n    assert decision['decision_id']==decision['question_id']=='user-message:sha256:'+hashlib.sha256(decision['answer'].encode('utf8')).hexdigest()")
s=once(s,"    groups={};identities=set();raw_count=0;red=[]", "    historical=load(N/'verification/first-attempt-index.json')\n    for name,h in historical['files'].items():assert sha(Path(name))==h,name\n    assert historical['failures']==3 and {k for k,v in historical['batch'].items() if v}=={'entry','export-green'}\n    groups={};identities=set();raw_count=0;red=[]")
s=once(s,"        receipt=load(path);group=receipt['group']", "        if str(path) in historical['harness_receipts']:continue\n        receipt=load(path);group=receipt['group']")
s=s.replace("('bindings-green','entry-final','boundary-green')","('bindings-recovery-green','entry-recovery-green','boundary-recovery-green')")
s=s.replace("N/'verification/batch-checks.json'","N/'verification/recovery-batch-checks.json'")
s=s.replace("{'bindings-green':16,'entry-final':34,'boundary-green':11}","{'bindings-recovery-green':16,'entry-recovery-green':34,'boundary-recovery-green':11}")
s=s.replace("'Path/candidate/hash bindings only; existing v5 tests and entry/adapter/bindings functions unchanged'", "'Path/hash and content-derived preparation binding; two sampler fixture expressions migrated, purposes retained; core entry/adapter/bindings functions unchanged'")
s=s.replace("red_failures=0,product_sources_changed=False","red_failures=0,first_attempt_failures_preserved=3,first_attempt_index_sha256=sha(N/'verification/first-attempt-index.json'),product_sources_changed=False")
write(p,s)
s=(N/'verification/run_preparation_checks.py').read_text('utf8')
s=s.replace("'verification/run_binding_checks.py','green'","'verification/run_binding_checks.py','recovery-green'").replace("'verification/run_entry_checks.py','final'","'verification/run_entry_checks.py','recovery-green'").replace("'verification/run_boundary_checks.py','green'","'verification/run_boundary_checks.py','recovery-green'")
s=s.replace("('batch-'+name+'.log')","('recovery-batch-'+name+'.log')").replace("'batch-checks.json'","'recovery-batch-checks.json'")
with (N/'verification/run_recovery_checks.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
p=N/'verification/prepare_documents.py';s=p.read_text('utf8')
s=s.replace('八组最终检查同源码，失败/错误/跳过均0','有界恢复轮次的八组最终检查同源码，失败/错误/跳过均0；首轮3项失败保留：1项准备ID拒绝门、2项旧采样表达')
s=s.replace('原平台准备答复已准确记录为call_5411de619a6c4de0bab414126a228c7d，actual/result-review均0，不能签成actual1。','原平台准备答复在source_question_id准确记录为call_5411de619a6c4de0bab414126a228c7d；执行绑定decision_id为明确标记的内容派生ID。actual/result-review均0，原direct谓词验证其不可升格actual1。两个导出fixture改成operation开头与右侧Unicode伪装边界，保留原成功写回/严格拒绝用途；不删除失败断言或改协议。')
write(p,s)
save(N/'verification/preparation-binding-recovery.json',dict(status='BOUNDED_RECOVERY_APPLIED_AWAITING_CHECKS',core_AST_unchanged=True,product_changed=False,first_attempt_index_sha256=sha(N/'verification/first-attempt-index.json'),decision_sha256=sha(N/'inputs/direct-user-decision.json'),scope='Preparation binding and two test expressions only',actual_cases=0,model_calls=0))
print(json.dumps(dict(status='BOUNDED_RECOVERY_APPLIED',first_failures_preserved=3,core_functions_unchanged=True,actual=0)))
