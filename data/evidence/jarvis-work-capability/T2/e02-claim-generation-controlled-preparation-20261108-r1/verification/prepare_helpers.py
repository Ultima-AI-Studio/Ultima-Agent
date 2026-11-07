"""Generate minimal path/hash rebind and preparation-only bookkeeping from the previous entry."""
from pathlib import Path
import ast,json
N=Path(__file__).resolve().parents[1];O=N.parent/'e02-output-structure-controlled-preparation-20261108-r1'
OLD='bf7f7a9cf0e4ba559c29daa388c00379d12d345a';HEAD='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b'
review=json.loads((N/'review/independent-plan-review.json').read_bytes())
assert review['verdict']=='PASS_PLAN_ONLY' and review['plan_sha256']=='0f8e4dc44e65ec89aa47d4ebacdbbe2001ea9c2ebd58fc266973a78188f38d98'
def write(name,s):
    ast.parse(s)
    with (N/'verification'/name).open('x',encoding='utf8',newline='\n') as f:f.write(s)
def once(s,a,b):
    assert s.count(a)==1,(a,s.count(a));return s.replace(a,b,1)
def common(s):
    return (s.replace('jarvis-e02-output-structure-r2','jarvis-e02-claim-generation-r1')
        .replace('jarvis-e02-output-budget','jarvis-e02-output-structure-r2')
        .replace('e02-output-structure-diagnostics-20261108-r2','e02-claim-generation-contract-20261108-r1')
        .replace('e02-output-budget-controlled-preparation-20261107-r1',O.name)
        .replace('jarvis-work-e02-output-structure-controlled-entry-plan-20261108.md','jarvis-work-e02-claim-generation-controlled-entry-plan-20261108.md')
        .replace('ultimaagent-e02-output-structure-candidate-20261108-r2','ultimaagent-e02-claim-generation-candidate-20261108-r1')
        .replace(OLD,HEAD))
s=common((O/'verification/rebind.py').read_text('utf8'))
start=s.index("answer='审查");end=s.index("worker=load",start)
s=s[:start]+'''answer='授权离线补修、必要独审与入口准备（推荐）'
decision_id='call_5411de619a6c4de0bab414126a228c7d'
save(N/'inputs/direct-user-decision.json',dict(source='user_question_reply',question_id=decision_id,decision_id=decision_id,identifier_is_platform_message_id=True,decision_id_note='Actual preparation question id; grants no actual case or result review',answer=answer,plan_sha256=sha(PLAN),scope='Already authorized Task3 offline controlled entry preparation only; explicit new actual allocation still required',actual_case_allocation=0,result_review_allocation=0,model_calls=0,network_requests=0,service_operations=0,retry=0,UI=False,audio=False))
save(N/'inputs/scope.json',dict(source='call_5411de619a6c4de0bab414126a228c7d',scope='Frozen operation-first claim candidate controlled entry preparation, offline only',actual_case_allocation=0,result_review_allocation=0,model_calls=0,network_requests=0,UI=False,audio=False,service_operations=False))
''' + s[end:]
s=s.replace(",'read_runtime.py'",'')
s=s.replace('len(sources)==77','len(sources)==78').replace('FROZEN_N24_PASS_PREPARATION_ONLY','FROZEN_N34_PASS_PREPARATION_ONLY').replace('final_code_tests=979','final_code_tests=1004')
s=s.replace('N24 frozen975 product plus4 compatibility; not rerun inN25','N34 frozen994 product plus4 compatibility plus6 official reference; not rerun in entry preparation')
s=s.replace('Frozen output structure evidence only; controlled entry preparation','Frozen operation-first code claim candidate; offline controlled entry preparation')
s=once(s,"(N/'harness/README.md').write_text('# Frozen output-structure entry\\n\\nProduct '+HEAD+'; current8B, original corpus/budgets/cleanup unchanged. Actual/model0. v5 export migration pending guarded compatibility RED.\\n',encoding='utf8',newline='\\n')", "(N/'harness/README.md').write_text('# Frozen claim-generation entry\\n\\nProduct '+HEAD+'; current8B, original corpus/budgets/cleanup unchanged. Actual/model/network requests0. Existing v5 export unchanged. Live runtime freshness pending original actual preflight.\\n',encoding='utf8',newline='\\n')")
s=s.replace('frozen bf7f7a9, 77 sources bound','frozen d8f8d97, 78 sources bound')
s+= '''\nstate=load(T/'current-run.json');assert state['last_actual_result']==load(N/'inputs/previous-current-run.json')['last_actual_result']
state.update(active_review_agent=None,phase='SOURCE35_E02_CLAIM_GENERATION_ENTRY_OFFLINE_CHECKS')
(T/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\\n',encoding='utf8',newline='\\n')
'''
write('rebind.py',s)
s=common((O/'verification/verify_preservation.py').read_text('utf8')).replace("prior['tests']==979","prior['tests']==1004")
write('verify_preservation.py',s)
s=common((O/'verification/verify_preparation.py').read_text('utf8'))
s=once(s,"assert scope['model_calls']==0 and decision['identifier_is_platform_message_id'] is False", "assert scope['model_calls']==scope['network_requests']==0 and decision['identifier_is_platform_message_id'] is True")
s=once(s,"assert decision['decision_id']=='user-message:sha256:'+hashlib.sha256(decision['answer'].encode('utf8')).hexdigest()", "assert decision['decision_id']==decision['question_id']=='call_5411de619a6c4de0bab414126a228c7d' and decision['answer']=='授权离线补修、必要独审与入口准备（推荐）'")
s=s.replace("len(current['source_files'])==77","len(current['source_files'])==78")
s=s.replace("if group!='export-red':assert sha(N/'harness'/name)==digest,name","assert sha(N/'harness'/name)==digest,name")
a=s.index("        if group=='export-red':");b=s.index('        assert group in',a);s=s[:a]+s[b:]
s=s.replace("assert len(red)==1 and set(groups)==","assert not red and set(groups)==")
a=s.index("    runtime=load(N/'verification/runtime-readiness-final.json')");b=s.index('    tests=len(identities)',a)
s=s[:a]+'''    runtime=load(N/'verification/runtime-readiness-pending.json')
    assert runtime['status']=='PENDING_FRESH_ACTUAL_PREFLIGHT' and runtime['candidate']==CANDIDATE
    assert runtime['current_runtime_verified'] is False and runtime['actual_preflight_unchanged'] is True
    assert runtime['model_calls']==runtime['network_requests']==runtime['service_operations']==0
    for name,digest in runtime['historical_files'].items():assert sha(Path(name))==digest,name
    assert runtime['historical_evidence_is_current_proof'] is False
    state=load(N.parent/'current-run.json');prior_state=load(N/'inputs/previous-current-run.json')
    assert state['last_actual_result']==prior_state['last_actual_result'] and {'T2','t2'}<=set(state)
    assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
    assert state['active_candidate']==CANDIDATE and state['live_runtime_readiness']=='PENDING_FRESH_ACTUAL_PREFLIGHT'
''' + s[b:]
s=s.replace("red_failures=2","red_failures=0").replace('product_baseline_tests=979','product_baseline_tests=1004')
s=s.replace("'Path/candidate/hash bindings and export tests only; entry/adapter/bindings functions unchanged'","'Path/candidate/hash bindings only; existing v5 tests and entry/adapter/bindings functions unchanged'")
s=s.replace("runtime_readiness_sha256=sha(N/'verification/runtime-readiness-final.json')","runtime_readiness_sha256=sha(N/'verification/runtime-readiness-pending.json'),live_runtime_readiness='PENDING_FRESH_ACTUAL_PREFLIGHT'")
s=once(s,"    return dict(verdict='PASS_OFFLINE_PREPARATION'", "    assert tests==350 and len(identities)==289 and {k:v['tests'] for k,v in stdlib.items()}=={'bindings-green':16,'entry-final':34,'boundary-green':11}\n    return dict(verdict='PASS_OFFLINE_PREPARATION'")
write('verify_preparation.py',s)
print(json.dumps(dict(status='PREPARATION_HELPERS_CREATED',product_changed=False,actual=0,model_calls=0)))
