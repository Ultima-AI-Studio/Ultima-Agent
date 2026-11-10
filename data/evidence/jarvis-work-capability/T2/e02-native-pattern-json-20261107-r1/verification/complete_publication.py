"""Resume the exact local publication after an unsealed report EOL correction."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,runpy
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def git(root,*args):return subprocess.check_output(['git','-C',str(root),*args],creationflags=subprocess.CREATE_NO_WINDOW)
A=N/'verification/publication-attempt1';A.mkdir(exist_ok=False)
close=N/'verification/closeout-registration.json';prior=json.loads(close.read_bytes())
with (A/'closeout-registration.json').open('xb') as f:f.write(close.read_bytes())
r=subprocess.run(['git','-C',str(R),'diff','--cached','--check','--',
    *[Path(v['source']).relative_to(R).as_posix() for v in prior['mirror']]],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert r.returncode==2
with (A/'whitespace-check.log').open('xb') as f:f.write(r.stdout+r.stderr)
assert git(R,'rev-parse','HEAD').decode().strip()=='65f5b747b8e726801b1251dc79f201d62643edd7'
assert git(M,'rev-parse','HEAD').decode().strip()=='0a9c67c8932c090b93d8332caaa35b6a17c98044'
changes=[]
# Only the new, post-seal completion report and its public/mirror copies change.
report=R/'docs/reports/jarvis-work-t2-e02-json-string-sampler-preparation-20261107.md'
mirror=M/'docs/shared/research/ultimaagent-work-capability/reports'/report.name
for i,p in enumerate([N/'completion-report.md',report,mirror]):
    raw=p.read_bytes();assert b'\r\n' in raw
    with (A/f'report-{i}.raw').open('xb') as f:f.write(raw)
    normalized=raw.replace(b'\r\n',b'\n')
    assert normalized.decode('utf8').splitlines()==raw.decode('utf8').splitlines()
    p.write_bytes(normalized)
    changes.append(dict(path=str(p),before=hashlib.sha256(raw).hexdigest(),after=sha(p),only_crlf_to_lf=True))
for entry in prior['mirror']:
    assert sha(Path(entry['source']))==sha(Path(entry['target']))
    entry['sha256']=sha(Path(entry['source']))
close.write_text(json.dumps(prior,ensure_ascii=False,indent=2)+'\n',encoding='utf8',newline='\n')
with (A/'recovery.json').open('x',encoding='utf8') as f:json.dump(dict(
    reason='New unsealed completion report used CRLF; repo treats CR as trailing whitespace.',
    initial_publication_exit=1,whitespace_exit=2,commits_created_before_failure=0,changes=changes,
    sealed_plan_product_manifest_unchanged=True,actual_cases=0,model_calls=0,
    recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat()),f,ensure_ascii=False,indent=2)
source=(N/'verification/publish.py').read_text(encoding='utf8')
source=source.replace("assert not git(R,'diff','--cached','--name-only').strip() and not git(M,'diff','--cached','--name-only').strip()",
    "assert not git(M,'diff','--cached','--name-only').strip()")
source=source.replace("project.update(Path(v['source']) for v in closeout['mirror'])",
    "project.update(Path(v['source']) for v in closeout['mirror'])\nproject.update(p for p in (N/'verification/publication-attempt1').iterdir() if p.is_file())\nproject.update([N/'verification/publish.py',N/'verification/complete_publication.py',N/'verification/publication-pathspec.txt'])")
source=source.replace("pathspec=N/'verification/publication-pathspec.txt'", "pathspec=N/'verification/publication-pathspec-resume.txt'")
source=source.replace("git(R,'add','-f','--pathspec-from-file='+str(pathspec))",
    "assert set(git(R,'diff','--cached','--name-only').decode().splitlines()) <= {p.relative_to(R).as_posix() for p in project}\ngit(R,'add','-f','--pathspec-from-file='+str(pathspec))")
resume=N/'verification/publish_resume.py'
with resume.open('x',encoding='utf8',newline='\n') as f:f.write(source)
runpy.run_path(str(resume),run_name='__main__')
