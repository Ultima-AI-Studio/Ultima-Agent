"""Repair only an unsealed preparation-message identity binding, never its allowance."""
from pathlib import Path
import ast,datetime as dt,hashlib,json,re
N=Path(__file__).resolve().parents[1]
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('x',encoding='utf8',newline='\n') as f:json.dump(v,f,ensure_ascii=False,indent=2)
assert not (N/'manifest.json').exists()
failed=N/'offline/entry-final';result=json.loads((failed/'test-result.json').read_bytes())
assert result['tests']==34 and result['failures']==0 and result['errors']==1 and not result['denied']
assert "KeyError: 'decision_id'" in (failed/'stderr.log').read_text('utf8')
decision_path=N/'inputs/direct-user-decision.json';entry=N/'code/entry.py'
before={str(p):sha(p) for p in (decision_path,entry)}
snapshot=N/'verification/decision-binding-before';snapshot.mkdir(exist_ok=False)
for p in (decision_path,entry):
    with (snapshot/p.name).open('xb') as f:f.write(p.read_bytes())
d=json.loads(decision_path.read_bytes());original=dict(d)
assert 'decision_id' not in d and d['actual_case_allocation']==d['result_review_allocation']==d['model_calls']==0
d.update(decision_id='user-message:sha256:'+hashlib.sha256(d['answer'].encode('utf8')).hexdigest(),identifier_is_platform_message_id=False,decision_id_note='Content-derived identifier for the existing direct-message gate; question_id retains the actual user reply identity; allocation remains zero')
assert {k:d[k] for k in original}==original
decision_path.write_text(json.dumps(d,ensure_ascii=False,indent=2),encoding='utf8',newline='\n')
s=entry.read_text('utf8');s,count=re.subn(r"(?m)^DIRECT_USER_DECISION_SHA='[^']*'",'DIRECT_USER_DECISION_SHA='+repr(sha(decision_path)),s);assert count==1
entry.write_text(s,encoding='utf8',newline='\n')
functions=lambda p:{n.name:ast.dump(n,include_attributes=False) for n in ast.parse(p.read_bytes()).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef,ast.ClassDef))}
assert functions(entry)==functions(snapshot/'entry.py')
for name in ('read_runtime.py','verify_preparation.py','write_preparation_report.py','closeout.py'):
    p=N/'verification'/name;s=p.read_text('utf8').replace('runtime-readiness.json','runtime-readiness-final.json')
    if name=='verify_preparation.py':
        s=s.replace("'entry-final'","'entry-review-green'").replace('initial_validation_failed_cases=0','initial_validation_failed_cases=1')
        point='    stdlib={}'
        assert point in s
        s=s.replace(point,"    initial=load(N/'offline/entry-final/test-result.json')\n    assert initial['tests']==34 and initial['errors']==1 and initial['failures']==0 and not initial['denied']\n    assert \"KeyError: 'decision_id'\" in (N/'offline/entry-final/stderr.log').read_text('utf8')\n"+point)
    p.write_text(s,encoding='utf8',newline='\n')
save(N/'inputs/decision-binding-fix.json',dict(recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),cause='Initial preparation decision lacks existing direct-message decision_id; one KeyError in entry fixture',before=before,after={str(p):sha(p) for p in (decision_path,entry)},failure_receipt_sha256=sha(failed/'receipt.json'),initial_result_sha256=sha(failed/'test-result.json'),question_id=d['question_id'],answer_unchanged=True,scope_unchanged=True,core_functions_unchanged=True,actual_allocation=0,result_review_allocation=0,model_calls=0,rerun_scope='Only affected entry34 on new stage; fresh metadata snapshot for changed entry constant; other seven unchanged passing groups retained'))
print(json.dumps(dict(core_functions_unchanged=True,actual_allocation=0,old_failure_preserved=True,decision_sha256=sha(decision_path))))
