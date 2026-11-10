"""Retain recovery evidence, align its remaining expected artifact literal and use a fresh batch receipt."""
from pathlib import Path
import ast,hashlib,json
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
first=load(N/'verification/first-attempt-index.json');rows=[p for p in sorted((N/'code').glob('harness-preparation-*/receipt.json')) if str(p) not in first['harness_receipts']];assert len(rows)==5
assert [(load(p)['group'],load(p)['exit_code']) for p in rows if load(p)['exit_code']]==[('export-green',1)]
before=N/'verification/second-attempt-sources';before.mkdir();files={}
for name in ('harness/test_adapter.py','harness/manifest.json','verification/run_recovery_checks.py','verification/run_binding_checks.py','verification/run_entry_checks.py','verification/run_boundary_checks.py','verification/verify_preparation.py','verification/prepare_documents.py'):
    p=N/name;target=before/name;target.parent.mkdir(parents=True,exist_ok=True)
    with target.open('xb') as f:f.write(p.read_bytes())
    files[str(target)]=sha(target)
for folder in [p.parent for p in rows]+[N/'offline'/x for x in ('bindings-recovery-green','entry-recovery-green','boundary-recovery-green')]:
    for p in folder.iterdir():
        if p.is_file():files[str(p)]=sha(p)
    for name in ('snapshot','harness-source','harness'):
        for p in (folder/name).rglob('*'):
            if p.is_file():files[str(p)]=sha(p)
save(N/'verification/second-attempt-index.json',dict(harness_receipts=[str(p) for p in rows],files=files,failures=1,root_cause='The quoted_write artifact expectation still contained the removed prefix; product write/readback/ACK and escaped-boundary rejection already passed',batch_aggregation_failure='FileExistsError on existing verification/batch-checks.json; eight child receipts retained; no original receipt overwritten',actual_cases=0))
p=N/'harness/test_adapter.py';s=p.read_text('utf8');s=once(s,"assert '可见 client.run 调用，参数含", "assert 'client.run 调用，参数含");assert '可见 client.run' not in s and 'aclient.run' not in s;write(p,s)
p=N/'harness/manifest.json';h=load(p);h['files']={name:sha(N/'harness'/name) for name in h['files']};write(p,json.dumps(h,ensure_ascii=False,indent=2)+'\n')
for name in ('binding','entry','boundary'):
    p=N/'verification'/('run_'+name+'_checks.py');s=p.read_text('utf8');s=once(s,"sys.argv[1] in (","sys.argv[1] in ('final-green',");write(p,s)
p=N/'verification/verify_preparation.py';s=p.read_text('utf8')
s=once(s,"    groups={};identities=set();raw_count=0;red=[]", "    second=load(N/'verification/second-attempt-index.json')\n    for name,h in second['files'].items():assert sha(Path(name))==h,name\n    assert second['failures']==1\n    groups={};identities=set();raw_count=0;red=[]")
s=once(s,"if str(path) in historical['harness_receipts']:continue", "if str(path) in historical['harness_receipts']+second['harness_receipts']:continue")
s=s.replace('bindings-recovery-green','bindings-final-green').replace('entry-recovery-green','entry-final-green').replace('boundary-recovery-green','boundary-final-green')
s=s.replace("N/'verification/recovery-batch-checks.json'","N/'verification/final-batch-checks.json'")
s=s.replace('first_attempt_failures_preserved=3,','first_attempt_failures_preserved=3,second_attempt_failure_preserved=1,')
write(p,s)
s=(N/'verification/run_preparation_checks.py').read_text('utf8')
s=once(s,"'verification/run_binding_checks.py','green'","'verification/run_binding_checks.py','final-green'")
s=once(s,"'verification/run_entry_checks.py','final'","'verification/run_entry_checks.py','final-green'")
s=once(s,"'verification/run_boundary_checks.py','green'","'verification/run_boundary_checks.py','final-green'")
s=once(s,"('batch-'+name+'.log')","('final-batch-'+name+'.log')")
s=once(s,"N/'verification/batch-checks.json'","N/'verification/final-batch-checks.json'")
with (N/'verification/run_final_checks.py').open('x',encoding='utf8',newline='\n') as f:f.write(s)
p=N/'verification/prepare_documents.py';s=p.read_text('utf8');s=s.replace('有界恢复轮次的八组最终检查','最终受限轮次的八组检查')
s=s.replace('1项准备ID拒绝门、2项旧采样表达','1项准备ID拒绝门、2项旧采样表达；随后恢复轮次剩1项成品文本期望漏迁移，独立回执保留，另保留批次汇总独占文件名冲突。最终修正剩余期望并使用新汇总文件，不覆写任何旧回执')
write(p,s)
print(json.dumps(dict(status='REMAINING_FIXTURE_EXPECTATION_ALIGNED',retained_test_failures=4,product_changed=False,actual=0)))
