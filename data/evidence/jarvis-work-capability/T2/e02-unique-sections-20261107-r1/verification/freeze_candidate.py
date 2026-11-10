"""Freeze only the reviewed repair paths after reading current saved test evidence."""
from pathlib import Path
import hashlib,json,subprocess,xml.etree.ElementTree as ET
N=Path(__file__).resolve().parents[1]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-unique-sections/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):return subprocess.check_output(['git','-C',str(C),*args],text=True,encoding='utf8').strip()
paths=['src/brain/'+name for name in ('agent_server.py','work_navigation.py','work_research.py','work_research_diagnostics.py',
    'tests/test_work_code_claim_schema.py','tests/test_work_failure_diagnostics.py','tests/test_work_source_reference_schema.py',
    'tests/test_work_write_diagnostics.py','tests/test_work_unique_source_sections.py')]
assert git('rev-parse','HEAD')=='22653fb77445bad4f5b9d9ae789cd35972dcc984'
assert not git('diff','--cached','--name-only')
status=subprocess.check_output(['git','-C',str(C),'status','--porcelain'],text=True,encoding='utf8')
assert {line[3:] for line in status.splitlines()}==set(paths)
expected={'unique-green':21,'failure-green':31,'grounding-green':11,'claim-green':28,'metadata-green':43,
    'diagnostics-green':17,'target-green':19,'reference-green':29,'research-a':68,'research-b':110,
    'navigation':90,'transport':104,'delivery':86,'grammar':7}
allcases=set();receipts={}
for group,count in expected.items():
    p=sorted((N/'offline').glob(group+'-*/receipt.json'))[-1];r=json.loads(p.read_bytes())
    assert r['exit_code']==0 and r['sources_unchanged']
    for name,digest in r['source_sha256'].items():assert sha(Path(name))==digest,name
    audit=json.loads((p.parent/'offline-audit.json').read_bytes())
    assert audit['python_operations_clean'] and audit['expected_probe_closed'] and not audit['denied']
    nodes=list(ET.parse(p.parent/'junit.xml').iter('testcase'))
    assert not any(x.find(t) is not None for x in nodes for t in ('failure','error','skipped'))
    cases={(x.get('classname'),x.get('name')) for x in nodes}
    assert len(cases)==count and not allcases&cases
    allcases|=cases;receipts[group]=str(p)
assert len(allcases)==664
subprocess.run(['git','-C',str(C),'diff','--check'],check=True)
before={p:sha(C/p) for p in paths}
subprocess.run(['git','-C',str(C),'-c','core.autocrlf=false','add','--',*paths],check=True)
assert set(git('diff','--cached','--name-only').splitlines())==set(paths)
subprocess.run(['git','-C',str(C),'commit','-m','Align research source sections and retain bounded failure diagnostics'],check=True)
head=git('rev-parse','HEAD');tag='ultimaagent-e02-unique-sections-candidate-20261107'
subprocess.run(['git','-C',str(C),'tag',tag,head],check=True)
assert not git('status','--porcelain')
for name,digest in before.items():
    assert sha(C/name)==digest
    assert hashlib.sha256(subprocess.check_output(['git','-C',str(C),'show',head+':'+name])).hexdigest()==digest
result=dict(candidate=head,parent='22653fb77445bad4f5b9d9ae789cd35972dcc984',tag=tag,
    files=before,product_tests=664,receipts=receipts,actual_calls=0,model_calls=0)
with (N/'verification/candidate-freeze.json').open('x',encoding='utf8') as f:json.dump(result,f,indent=2)
print(json.dumps(dict(candidate=head,tag=tag,product_tests=664,files=len(paths))))
