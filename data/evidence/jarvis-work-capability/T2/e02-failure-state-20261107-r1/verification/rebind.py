"""Bind the new candidate without changing any original input or runtime gate."""
from pathlib import Path
import hashlib,json,re,subprocess
N=Path(__file__).resolve().parents[1];OLD=N.parent/'e02-grounded-export-20261107-r1'
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-failure-state/UltimaAgent')
P=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-grounded-export/UltimaAgent')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
def save(p,v):p.write_text(json.dumps(v,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
head=subprocess.check_output(['git','-C',str(C),'rev-parse','HEAD'],text=True).strip()
old=load(OLD/'inputs/input-manifest.json'); sources={str(C/Path(p).relative_to(P)):sha(C/Path(p).relative_to(P)) for p in old['source_files']}
for relative in ('src/brain/work_research_diagnostics.py','src/brain/tests/test_work_failure_diagnostics.py'):
    extra=C/relative
    if extra.exists():sources[str(extra)]=sha(extra)
runtime=load(OLD/'inputs/candidate-runtime-manifest.json')
runtime.update(candidate=head,candidate_root=str(C),branch='codex/jarvis-e02-failure-state',source_files=sources,
    scope='Bounded private final-branch and selected-page failure diagnostics',code_gate='PENDING_CURRENT_PREPARATION_REVIEW',
    final_code_tests=None,source_revision=head,actual_cases=0,actual_release=False,acceptance_credit=False)
save(N/'inputs/candidate-runtime-manifest.json',runtime)
files={p:h for p,h in old['files'].items() if not Path(p).is_relative_to(P) and p!=str(OLD/'inputs/candidate-runtime-manifest.json')}
files.update(sources);files[str(N/'inputs/candidate-runtime-manifest.json')]=sha(N/'inputs/candidate-runtime-manifest.json')
value=dict(old,candidate=head,candidate_root=str(C),source_files=sources,files=files)
save(N/'inputs/input-manifest.json',value)
binding=N/'code/bindings.py';text=binding.read_text('utf8')
for name,value in {'CANDIDATE':head,'CANDIDATE_MANIFEST_SHA':sha(N/'inputs/candidate-runtime-manifest.json')}.items():
    text,n=re.subn(r"(?m)^"+name+r"='[^']*'",name+'='+repr(value),text);assert n==1
binding.write_text(text,encoding='utf8')
adapter=N/'harness/adapter.py';text=adapter.read_text('utf8')
new_sha=sha(N/'inputs/input-manifest.json')
replacements={'CANDIDATE':head,'MANIFEST_SHA':new_sha,'BINDINGS_SHA':sha(binding),'PREPARATION_SHA':sha(N/'inputs/scope.json')}
old_values={}
for name,value in replacements.items():
    match=re.search(r"(?m)^"+name+r"='([^']*)'",text);assert match;old_values[name]=match[1]
    text,n=re.subn(r"(?m)^"+name+r"='[^']*'",name+'='+repr(value),text);assert n==1
adapter.write_text(text,encoding='utf8')
entry=N/'code/entry.py';text=entry.read_text('utf8');text,n=re.subn(r"(?m)^CANDIDATE='[^']*'",'CANDIDATE='+repr(head),text);assert n==1;entry.write_text(text,encoding='utf8')
for p in [N/'harness/test_adapter.py',N/'tests/test_live_boundary.py']:
    text=p.read_text('utf8').replace(old_values['CANDIDATE'],head).replace(old_values['MANIFEST_SHA'],new_sha)
    p.write_text(text,encoding='utf8')
hm=load(N/'harness/manifest.json');hm.update(candidate=head,candidate_manifest_sha256=new_sha,
    files={p.name:sha(p) for p in (N/'harness').iterdir() if p.is_file() and p.name!='manifest.json'})
save(N/'harness/manifest.json',hm)
save(N/'inputs/candidate-transition.json',dict(base=old['candidate'],candidate=head,old_root=str(P),new_root=str(C),
    current_sources=len(sources),protected_baseline_sha256=files[old['protected_baseline_path']],
    changed_existing_sources=[str(Path(p).relative_to(C)) for p,h in sources.items() if (P/Path(p).relative_to(C)).exists() and sha(P/Path(p).relative_to(C))!=h],
    prior_E01_E03_credit='Historical 269aca5 only',model_or_budget_changed=False,shared_P4_P1_changed=False))
print(json.dumps(dict(candidate=head,sources=len(sources),inputs=len(files),input_sha256=new_sha)))
