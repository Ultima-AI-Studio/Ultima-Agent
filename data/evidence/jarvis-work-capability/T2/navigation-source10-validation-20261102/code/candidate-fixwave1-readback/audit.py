import ast,hashlib,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
C=Path.cwd(); R=Path(__file__).resolve().parent; V=R.parent
W=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101'
J=lambda p:json.loads(p.read_bytes())
H=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
git=lambda *a:subprocess.check_output(['git',*a]).decode().strip()
base='6b1e07c8318a334ee1f2218863eb84254e38f526'
allowed=['src/brain/agent_server.py','src/brain/tests/test_work_navigation_transport.py','src/brain/work_service.py']
assert git('rev-parse','HEAD')==base and git('diff','--name-only').splitlines()==allowed and not git('diff','--cached','--name-only')
git('diff','--check')
old=J(V/'unit23-fix2-covering/receipt.json')['source_inputs_after']
current={p:H(C/p) for p in old}
assert len(current)==31 and [p for p in sorted(old) if old[p]!=current[p]]==allowed
receipts={}
for stage,total,fails in [('c1-red',3,2),('c1-green',135,0),('c2-red',1,1),('c2-green',136,0),('covering',479,0),('compat',8,0)]:
    d=V/('candidate-fixwave1-'+stage); receipt=J(d/'receipt.json')
    assert receipt['counts']==dict(tests=total,failures=fails,errors=0,skipped=0)
    assert receipt['exit_code']==int(fails>0) and receipt['source_inputs_before']==receipt['source_inputs_after']
    assert all(H(d/k)==v for k,v in receipt['files'].items())
    if stage!='compat':
        assert J(d/'loaded-paths.json')['unexpected']=={}
        assert all(H(d/'source-inputs'/p)==sha for p,sha in receipt['source_inputs_before'].items())
        assert receipt['runner_sha256']==H(V/'run_code_tests_v2.py')=='60f6ea3d157969dcaa4eebef474a62642da6f02963cb8a87b405217f788ac32c'
    if stage in ('covering','compat'): assert receipt['source_inputs_before']==current
    receipts[stage]=dict(path=str(d/'receipt.json'),sha256=H(d/'receipt.json'),argv=receipt['argv'],files=receipt['files'],counts=receipt['counts'])
ids=lambda p:{(e.attrib['classname'],e.attrib['name']) for e in ET.parse(p).findall('.//testcase')}
priorids=ids(V/'unit23-fix2-covering/junit.xml'); latest=ids(V/'candidate-fixwave1-covering/junit.xml')
assert len(priorids)==475 and len(latest)==479 and priorids<=latest
assert ids(V/'unit23-fix2-compat/compat.xml')==ids(V/'candidate-fixwave1-compat/compat.xml')
assert len([n for n in ast.parse((C/'src/brain/tests/test_work_research.py').read_bytes()).body if isinstance(n,ast.FunctionDef) and n.name.startswith('test_')])==65
ctl=J(W/'task-2-navigation-candidate-review-inputs.json');pins=J(V/'unit23-fix2-readback/sdk-sources.json')['sha256']
protected={**ctl['frozen5'],**ctl['approved_plan_and_spec'],**ctl['evidence'],ctl['v3_protocol_path']:ctl['v3_protocol_sha256'],str(W/'task-2-navigation-candidate-review-report.md'):'acebd119a317b9a8ecc51a8d9160e86febd9b249f58dc0488a2204ce5b71b6b6'}
assert len(pins)==22 and all(H(Path(p))==sha for p,sha in {**pins,**protected}.items())
assert set(current)-set(git('ls-files').splitlines())=={ctl['preexisting_untracked_byte_bound_test']}
proofs=[]
for path in (V/'candidate-fixwave1-covering/temp').rglob('service-deadline.json'):
    obj=J(path); assert H(Path(obj['effect']['path']))==obj['artifact']['sha256']==obj['intent']['sha256']
    proofs.append(obj)
assert len(proofs)==3
out=dict(base=base,allowed_paths=allowed,source_inputs=current,protected=protected,sdk_pins=pins,receipts=receipts,
    old475_preserved=True,original65_unchanged=True,untracked_browser=ctl['preexisting_untracked_byte_bound_test'],
    c1_readback=proofs,external=H(R/'external-verification.json'),fractional=H(R/'fractional-verification.json'))
(R/'readback.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print('31 inputs, 475 identities, 65 original methods, 22 SDK and frozen pins, six receipts and three deadline readbacks verified')
