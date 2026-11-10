from pathlib import Path
import hashlib,json,subprocess,sys
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
C=Path(sys.argv[1]).resolve();OLD=T/'e02-native-pattern-json-20261107-r1'
BASE='6d758d9c3961f156a062e349ec4a949e2ee7a9a9'
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW).decode().strip()
def save(p,v):
    with p.open('x',encoding='utf8') as f:json.dump(v,f,indent=2)
review=json.loads((N/'review/independent-plan-review.json').read_bytes())
assert review['verdict']=='PASS_PLAN_ONLY' and review['plan_sha256']==hashlib.sha256((N/'plan.md').read_bytes()).hexdigest()
assert git('rev-parse','HEAD')==BASE and not git('status','--porcelain')
git('switch','-c','codex/jarvis-e02-native-rejection')
save(N/'inputs/worktree.json',dict(root=str(C),base=BASE,branch=git('branch','--show-current'),native_created=True,review_sha256=hashlib.sha256((N/'review/independent-plan-review.json').read_bytes()).hexdigest()))
for name in ('product_pytest.py','run_product_checks.py','run_final_regressions.py','verify_offline.py','seal_preparation.py','read_runtime_after.py'):
    s=(OLD/'verification'/name).read_text(encoding='utf8')
    s=s.replace('C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent',C.as_posix())
    if name in ('run_final_regressions.py','verify_offline.py'):
        s=s.replace("'grammar',", "'native-green','compatibility',")
    if name=='run_product_checks.py':
        s=s.replace("GROUPS={", "GROUPS={'native-red':['test_work_native_response_diagnostics.py'],'native-green':['test_work_native_response_diagnostics.py'],'compatibility':[str(N/'verification/compatibility_checks.py')],")
        s=s.replace("paths += [N/'inputs/accepted-dependency-pins.json',N/'verification/grammar_checks.py',N/'inputs/upstream/json_schema_to_grammar.py']", "paths += [N/'inputs/accepted-dependency-pins.json',N/'verification/compatibility_checks.py']")
    if name=='verify_offline.py':
        s=s.replace('e40a55b40c223181040dbb6a09d0c4d2da5026cf',BASE)
        s=s.replace("ALLOWED={'src/brain/agent_server.py','src/brain/tests/test_work_code_claim_schema.py','src/brain/tests/test_work_sampler_json_strings.py'}", "ALLOWED={'src/brain/agent_server.py','src/brain/work_research.py','src/brain/work_research_diagnostics.py','src/brain/tests/test_work_failure_diagnostics.py','src/brain/tests/test_work_native_response_diagnostics.py'}")
        s=s.replace('jarvis-work-e02-json-string-sampler-plan-20261107.md','jarvis-work-e02-native-response-rejection-diagnostics-plan-20261107.md').replace("glob('json-red-*')","glob('native-red-*')")
        s=s.replace("==29 and not list(red_xml.iter('error'))", ">0 and not list(red_xml.iter('error'))")
        s=s.replace("total-selected['grammar']['passed']", "total-selected['compatibility']['passed']").replace("reference_converter_tests=selected['grammar']['passed']", "compatibility_tests=selected['compatibility']['passed'],reference_converter_tests=0")
        s=s.replace('red_failures=29','red_failures=len(list(red_xml.iter("failure")))')
    if name=='seal_preparation.py':
        s=s.replace('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-coverage/UltimaAgent','C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent')
        s=s.replace('e02-source-coverage-controlled-preparation-20261107-r1','e02-json-string-controlled-preparation-20261107-r1').replace('e40a55b40c223181040dbb6a09d0c4d2da5026cf',BASE)
        s=s.replace('ultimaagent-e02-json-string-candidate-20261107','ultimaagent-e02-native-rejection-candidate-20261107').replace('NATIVE_JSON_STRING','NATIVE_REJECTION_DIAGNOSTICS').replace('JSON_STRING_COMPATIBILITY','NATIVE_REJECTION_DIAGNOSTICS')
        s=s.replace("N/'plan.md',N/'preparation-report.md'", "N/'progress.md',N/'plan.md',N/'preparation-report.md'")
    with (N/'verification'/name).open('x',encoding='utf8') as f:f.write(s)
state=json.loads((T/'current-run.json').read_bytes());state.update(active_review_agent=None,phase='SOURCE28_E02_NATIVE_REJECTION_IMPLEMENTATION',active_implementation_root=str(C))
(T/'current-run.json').write_text(json.dumps(state,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
with (N/'progress.md').open('a',encoding='utf8') as f:f.write('\nTask 1: start at '+BASE+'; exact plan PASS; product implementation root '+str(C)+'; actual/model allowance remains zero.\n')
print(json.dumps(dict(root=str(C),base=BASE,branch=git('branch','--show-current'))))
