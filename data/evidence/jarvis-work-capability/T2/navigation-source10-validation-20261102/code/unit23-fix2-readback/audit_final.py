import ast,datetime,hashlib,json,subprocess,xml.etree.ElementTree as ET
from pathlib import Path
HERE=Path(__file__).resolve().parent;ROOT=HERE.parent
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
BASE='facd68d8f94b4adcfd136e489e9ff81580d2dc0d'
ALLOWED=['src/brain/tests/test_work_navigation_transport.py','src/brain/work_research.py']
H=lambda raw:hashlib.sha256(raw).hexdigest()
git=lambda *args:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0','-c','core.autocrlf=false',*args],cwd=C)
assert git('rev-parse','HEAD').decode().strip()==BASE
assert not git('diff','--cached','--name-only').strip()
assert sorted(git('diff','--name-only').decode().splitlines())==ALLOWED
git('diff','--check')
full=json.loads((ROOT/'unit23-fix2-covering/receipt.json').read_bytes());compat=json.loads((ROOT/'unit23-fix2-compat/receipt.json').read_bytes())
assert full['counts']==dict(tests=475,failures=0,errors=0,skipped=0) and compat['counts']==dict(tests=8,failures=0,errors=0,skipped=0)
assert full['exit_code']==compat['exit_code']==0 and full['source_unchanged'] and compat['source_unchanged']
current={p:H((C/p).read_bytes()) for p in full['source_inputs_after']}
assert current==full['source_inputs_before']==full['source_inputs_after']==compat['source_inputs_before']==compat['source_inputs_after']
old=json.loads((ROOT/'unit23-fix1-covering/receipt.json').read_bytes())['source_inputs_after']
assert all(current[p]==sha for p,sha in old.items() if p not in ALLOWED)
assert json.loads((ROOT/'unit23-fix2-covering/loaded-paths.json').read_bytes())['unexpected']=={}
ids=lambda path:{(n.attrib['classname'],n.attrib['name']) for n in ET.parse(path).getroot().findall('.//testcase')}
assert len(ids(ROOT/'unit23-fix1-covering/junit.xml'))==449
assert ids(ROOT/'unit23-fix1-covering/junit.xml')<=ids(ROOT/'unit23-fix2-covering/junit.xml')
names=lambda data:{n.name for n in ast.parse(data).body if isinstance(n,(ast.FunctionDef,ast.AsyncFunctionDef)) and n.name.startswith('test_')}
baseline=git('show',BASE+':src/brain/tests/test_work_research.py')
assert baseline==(C/'src/brain/tests/test_work_research.py').read_bytes() and len(names(baseline))==65
pins=json.loads((ROOT/'unit23-delivery-readback/sdk-sources.json').read_bytes())
assert len(pins['sha256'])==22 and all(H(Path(p).read_bytes())==sha for p,sha in pins['sha256'].items())
(HERE/'sdk-sources.json').write_text(json.dumps(pins,indent=2),encoding='utf8')
report=C/'.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101/task-2-navigation-code-unit2-report.md'
prefix=report.read_bytes();archive=(ROOT/'unit23-author-fix1/report.md').read_bytes()
assert prefix==archive and len(prefix)==68833 and H(prefix)=='c43401ecead57c66e875d3d98e4087f42c0b157ed85ef15473acbdab58958871'
(HERE/'report-prefix.md').write_bytes(prefix)
for p in current:
    target=HERE/'source-inputs'/p;target.parent.mkdir(parents=True,exist_ok=True);target.write_bytes((C/p).read_bytes())
out=dict(base=BASE,allowed_paths=ALLOWED,changed_paths=ALLOWED,source_inputs=current,protected_input_changes=[],
    sdk22_unchanged=True,original65_names_and_bytes_preserved=True,original449_junit_preserved=True,
    loaded_paths_unexpected={},index_empty_before=True,whitespace_clean=True,report_prefix_bytes=len(prefix),report_prefix_sha256=H(prefix),
    full_receipt_sha256=H((ROOT/'unit23-fix2-covering/receipt.json').read_bytes()),compat_receipt_sha256=H((ROOT/'unit23-fix2-compat/receipt.json').read_bytes()),
    external_sha256=H((HERE/'external-verification.json').read_bytes()),fractional_sha256=H((HERE/'fractional-verification.json').read_bytes()),
    utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(HERE/'readback.json').write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(dict(protected_inputs_unchanged=True,original449_ids=True,original65_exact_bytes=True,index_empty=True,report_prefix_preserved=True,source_inputs=len(current))))
