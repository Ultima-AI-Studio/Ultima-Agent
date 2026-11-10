"""Rebind new candidate paths and hashes; preserve all old actual evidence."""
from pathlib import Path
import hashlib,json,subprocess
R=Path('H:/UltimaAI/UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
N=T/'e02-source-reference-schema-20261107-r1';OLD=T/'e02-fixed-target-schema-20261107-r1'
BASE='900b944165c0175b91492e3fe5b31d96aabdcd5c'
OC=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-fixed-target-schema/UltimaAgent')
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-reference/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
candidate=subprocess.check_output(['git','rev-parse','HEAD'],cwd=C,text=True).strip()
assert candidate!=BASE and subprocess.check_output(['git','rev-parse','HEAD^'],cwd=C,text=True).strip()==BASE
assert not subprocess.check_output(['git','status','--porcelain'],cwd=C)
assert not (N/'inputs/candidate-runtime-manifest.json').exists()
manifest=load(OLD/'inputs/candidate-runtime-manifest.json');before=dict(manifest['source_files'])
manifest.update(candidate=candidate,candidate_root=str(C),branch='codex/jarvis-e02-source-reference',scope='Visible source/evidence schema in generation and independent replay; original writer/fact/END gates retained')
manifest['source_files']={str(C/Path(p).relative_to(OC)):sha(C/Path(p).relative_to(OC)) for p in before}
manifest['source_files'][str(C/'src/brain/tests/test_work_source_reference_schema.py')]=sha(C/'src/brain/tests/test_work_source_reference_schema.py')
save(N/'inputs/candidate-runtime-manifest.json',manifest)
inputs=load(N/'inputs/input-manifest.json');inputs.update(candidate=candidate,candidate_root=str(C),source_files=manifest['source_files'])
files={}
for p,digest in inputs['files'].items():
    path=Path(p)
    if path.is_relative_to(OC):path=C/path.relative_to(OC);digest=sha(path)
    files[str(path)]=digest
files.update(manifest['source_files']);files[str(N/'inputs/candidate-runtime-manifest.json')]=sha(N/'inputs/candidate-runtime-manifest.json')
inputs['files']=files;save(N/'inputs/input-manifest.json',inputs)
replacements={BASE:candidate,'jarvis-e02-fixed-target-schema':'jarvis-e02-source-reference',
    sha(OLD/'inputs/candidate-runtime-manifest.json'):sha(N/'inputs/candidate-runtime-manifest.json'),
    sha(OLD/'inputs/input-manifest.json'):sha(N/'inputs/input-manifest.json')}
changed_files=[]
for directory in ('code','harness','tests'):
    for p in (N/directory).glob('*.py'):
        text=p.read_text('utf8');original=text
        for old,new in replacements.items():text=text.replace(old,new)
        if text!=original:p.write_text(text,encoding='utf8');changed_files.append(p.relative_to(N).as_posix())
p=N/'harness/adapter.py';text=p.read_text('utf8');old=sha(OLD/'code/bindings.py');assert old in text
p.write_text(text.replace(old,sha(N/'code/bindings.py')),encoding='utf8')
hm=load(N/'harness/manifest.json');hm.update(candidate=candidate,candidate_manifest_sha256=sha(N/'inputs/input-manifest.json'))
hm['files']={name:sha(N/'harness'/name) for name in hm['files']};save(N/'harness/manifest.json',hm)
changed=[str(Path(p).relative_to(OC)) for p,d in before.items() if manifest['source_files'][str(C/Path(p).relative_to(OC))]!=d]
assert set(changed)=={'src\\brain\\agent_server.py','src\\brain\\work_navigation.py','src\\brain\\work_research.py','src\\brain\\tests\\test_work_write_diagnostics.py'},changed
save(N/'inputs/candidate-transition.json',dict(base=BASE,candidate=candidate,old_root=str(OC),new_root=str(C),previous_runtime_sources=len(before),current_sources=len(manifest['source_files']),
    changed_existing_sources=changed,added_tests=['src/brain/tests/test_work_source_reference_schema.py'],input_manifest_sha256=sha(N/'inputs/input-manifest.json'),
    rebound_files=changed_files,prior_E01_E03_credit='old 269aca5 candidate only; new candidate actual E01/E03 not run',shared_P4_P1_changed=False,model_or_budget_changed=False))
s=load(T/'current-run.json');s.update(active_candidate=candidate,active_candidate_root=str(C));save(T/'current-run.json',s)
print(json.dumps(dict(candidate=candidate,sources=len(manifest['source_files']),inputs=len(files),changed=changed)))
