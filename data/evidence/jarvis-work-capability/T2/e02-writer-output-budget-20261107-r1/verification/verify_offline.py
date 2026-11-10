"""Read back only fresh guarded evidence for the current source bytes."""
from pathlib import Path
import datetime as dt,hashlib,importlib.util,json,subprocess,sys,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-budget/UltimaAgent')
BASE='d860b2ab4e4d9974e33c96472e4ea15abb807280'
GROUPS=['budget-green','json-green','native-green','compatibility','coverage-green','http-green','failure-green','metadata-green','diagnostics-green','target-green','reference-green','claim-green','unique-green','grounding-green','research-a','research-b','navigation','transport','delivery']
ALLOWED={'src/brain/work_research.py', 'src/brain/tests/test_work_output_budget_guidance.py', 'src/brain/agent_server.py', 'src/brain/tests/test_work_grounding_context.py', 'src/brain/work_navigation.py'}
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(path,value):
    with path.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],creationflags=subprocess.CREATE_NO_WINDOW,text=True).strip()
def verify():
    review=json.loads((N/'review/independent-plan-review.json').read_bytes())
    assert review['verdict']=='PASS_PLAN_ONLY' and review['plan_sha256']==sha(N/'plan.md')
    assert (N/'plan.md').read_bytes()==(N.parents[4]/'docs/plans/jarvis-work-e02-writer-output-budget-alignment-plan-20261107.md').read_bytes()
    changed=set(git('diff','--name-only',BASE).splitlines())|set(git('ls-files','--others','--exclude-standard').splitlines())
    assert changed==ALLOWED,changed
    subprocess.run(['git','-C',str(C),'diff','--check',BASE],check=True,creationflags=subprocess.CREATE_NO_WINDOW)
    selected={};test_ids=set();total=0
    for group in GROUPS:
        dirs=sorted((N/'offline').glob(group+'-*'))
        assert dirs,group
        run=dirs[-1];receipt=json.loads((run/'receipt.json').read_bytes());audit=json.loads((run/'offline-audit.json').read_bytes())
        assert receipt['group']==group and receipt['exit_code']==0 and receipt['sources_unchanged']
        assert receipt['actual'] is False and receipt['model_calls']==0 and receipt['product_launches']==0
        assert audit['pytest_exit_code']==0 and audit['error'] is None and not audit['denied'] and audit['python_operations_clean'] and audit['expected_probe_closed'] and audit['eager']['eager']['clean']
        for name,digest in receipt['source_sha256'].items():
            p=Path(name);assert sha(p)==digest,name
            archived=run/'snapshot'/(p.relative_to(C) if p.is_relative_to(C) else p.relative_to(N))
            assert sha(archived)==digest,str(archived)
        cases=list(ET.parse(run/'junit.xml').getroot().iter('testcase'))
        assert cases and all(not list(c) for c in cases),group
        ids={(c.get('classname'),c.get('name')) for c in cases}
        assert len(ids)==len(cases) and not test_ids.intersection(ids),group
        test_ids.update(ids);total+=len(cases)
        selected[group]=dict(run=str(run),passed=len(cases),receipt_sha256=sha(run/'receipt.json'),junit_sha256=sha(run/'junit.xml'),audit_sha256=sha(run/'offline-audit.json'))
    red=sorted((N/'offline').glob('budget-red-*'))
    assert len(red)==1
    red_receipt=json.loads((red[0]/'receipt.json').read_bytes());red_audit=json.loads((red[0]/'offline-audit.json').read_bytes())
    assert red_receipt['exit_code']==1 and red_receipt['sources_unchanged'] and red_audit['python_operations_clean'] and not red_audit['denied']
    red_xml=ET.parse(red[0]/'junit.xml').getroot()
    assert len(list(red_xml.iter('failure')))>0 and not list(red_xml.iter('error'))
    return dict(verdict='PASS_FRESH_OFFLINE_CURRENT_BYTES',recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),candidate_root=str(C),candidate_head=git('rev-parse','HEAD'),base=BASE,changed_files=sorted(changed),selected=selected,tests=total,product_tests=total-selected['compatibility']['passed'],compatibility_tests=selected['compatibility']['passed'],reference_converter_tests=0,duplicate_tests=0,red_failures=len(list(red_xml.iter("failure"))),red_receipt_sha256=sha(red[0]/'receipt.json'),actual_cases=0,model_calls=0,service_operations=0,acceptance_credit=0,os_packets_measured=False,exclusions=['test_http_work_legacy_and_cli','test_reparse_rejected'],coverage_limit='No actual harness/authority/UI/native binary grammar/model/semantic acceptance; Python audit is not a packet sniffer')
if __name__=='__main__':
    value=verify();save(N/'verification/offline-readback.json',value)
    print(json.dumps({k:v for k,v in value.items() if k!='selected'},ensure_ascii=False))
