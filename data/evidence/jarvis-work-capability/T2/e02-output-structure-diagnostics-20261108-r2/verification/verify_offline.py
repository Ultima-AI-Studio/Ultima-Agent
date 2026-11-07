"""Read recorded offline evidence and exact files; never import product code."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,sys,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1];R=N.parents[4];T=N.parent
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-structure-r2/UltimaAgent')
OLD=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-output-budget/UltimaAgent')
BASE='0421a54cab572be013c3f7ad562e86406bfe8e52'
ALLOWED=['src/brain/agent_server.py','src/brain/work_research_diagnostics.py',
    'src/brain/tests/test_work_native_response_diagnostics.py','src/brain/tests/test_work_output_structure_diagnostics.py']
def sha(p):return hashlib.sha256(Path(p).read_bytes()).hexdigest()
def load(p):return json.loads(Path(p).read_bytes())
def save(p,v):
    with Path(p).open('x',encoding='utf8') as f:json.dump(v,f,ensure_ascii=False,indent=2)
def git(root,*args):
    return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW,stderr=subprocess.PIPE)
def verify():
    batch=load(N/'verification/final-regression-batch.json');assert len(batch['groups'])==20
    assert batch['totals']['failures']==batch['totals']['errors']==batch['totals']['skipped']==0
    cases=[]
    for group,r in batch['groups'].items():
        p=Path(r['receipt']);assert sha(p)==r['receipt_sha256'] and r['exit_code']==0
        receipt=load(p);audit=load(p.parent/'offline-audit.json')
        assert receipt['sources_unchanged'] and receipt['source_sha256']==batch['source_sha256']
        assert audit['pytest_exit_code']==0 and audit['error'] is None and not audit['denied'] and audit['python_operations_clean']
        for name,h in receipt['source_sha256'].items():assert sha(name)==h,name
        xml=ET.parse(p.parent/'junit.xml').getroot()
        assert not list(xml.iter('failure')) and not list(xml.iter('error')) and not list(xml.iter('skipped'))
        cases.extend((x.attrib.get('classname',''),x.attrib['name']) for x in xml.iter('testcase'))
    assert len(cases)==len(set(cases))==batch['totals']['tests']
    preserved={}
    for name,expected in [
        ('e02-native-rejection-controlled-preparation-20261107-r1','9cc9e1c9c38a5f23b9e5a0d72b52bd2558a720c99abea8b11148abde483523d6'),
        ('e02-output-budget-controlled-preparation-20261107-r1','3ebd6811702ed9eb09beb1c2d2efe418a491bd9f0078b9ea51db507c38b47f61')]:
        prior=T/name;manifest=prior/'review/result-inputs/result-manifest.json';assert sha(manifest)==expected
        counts={}
        for filename,root in [('manifest.json',prior),('review/result-inputs/result-manifest.json',prior),
            ('actual/E02-controlled-1/seal-index.json',prior/'actual/E02-controlled-1')]:
            members=load(prior/filename)['files']
            for member,h in members.items():assert sha(root/member)==h,member
            counts[filename]=len(members)
        preserved[name]=counts
    predecessor=load(N/'inputs/predecessor.json');prior=Path(predecessor['root'])
    assert sha(prior/'manifest.json')==predecessor['manifest_sha256']
    assert sha(prior/'review/independent-preparation-review.json')==predecessor['review_sha256']
    for name,h in load(prior/'manifest.json')['files'].items():assert sha(prior/name)==h,name
    for name,h in load(prior/'inputs/current-inputs.json')['files'].items():assert sha(name)==h,name
    frozen_root=Path(predecessor['root_candidate'])
    assert git(frozen_root,'rev-parse','HEAD').decode().strip()==predecessor['candidate']
    assert not git(frozen_root,'status','--porcelain').strip()
    pins=load(N/'inputs/accepted-dependency-pins.json')['files']
    for path,h in pins.items():assert sha(path)==h,path
    foreign=load(N/'inputs/unrelated-working-tree.json')['files']
    for path,h in foreign.items():assert sha(R/path)==h,path
    assert git(OLD,'rev-parse','HEAD').decode().strip()==BASE
    assert not git(OLD,'status','--porcelain','--untracked-files=no').strip()
    state=load(T/'current-run.json');before=load(N/'inputs/registration-before/0')
    assert state['last_actual_result']==before['last_actual_result']
    assert state['actual_case_allocation_remaining']==state['result_review_allocation_remaining']==0
    return dict(status='PASS_OFFLINE_READBACK',tests=len(cases),groups=20,compatibility_tests=batch['groups']['compatibility']['tests'],
        product_tests=len(cases)-batch['groups']['compatibility']['tests'],same_source_bytes=True,
        preserved=preserved,dependency_pins=len(pins),foreign_tracked_files=len(foreign),parent_preserved=True,
        last_actual_result_unchanged=True,actual_cases=0,model_calls=0,acceptance_credit=0,
        source_sha256=batch['source_sha256'],recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat())
if __name__=='__main__':
    assert len(sys.argv)==2 and sys.argv[1] in ('precommit','postcommit','final')
    value=verify();save(N/'verification'/('offline-'+sys.argv[1]+'-readback.json'),value)
    print(json.dumps({k:v for k,v in value.items() if k not in ('source_sha256','preserved')}))
