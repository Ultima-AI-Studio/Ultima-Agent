import datetime,hashlib,json,subprocess,sys
from pathlib import Path
HERE=Path(__file__).resolve().parent;C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
git=lambda *args:subprocess.check_output(['git','-c','maintenance.auto=false','-c','gc.auto=0','-c','core.autocrlf=false',*args],cwd=C)
H=lambda raw:hashlib.sha256(raw).hexdigest()
audit=json.loads((HERE/'readback.json').read_bytes());mode=sys.argv[1]
if mode=='staged':
    changed=sorted(git('diff','--cached','--name-only').decode().splitlines());ref=':'
    assert changed==audit['allowed_paths'];git('diff','--cached','--check')
else:
    head=git('rev-parse','HEAD').decode().strip();ref=head+':'
    changed=sorted(git('diff','--name-only',audit['base'],head).decode().splitlines())
    assert changed==audit['allowed_paths'] and not git('diff','--cached','--name-only').strip() and not git('diff','--name-only').strip()
    assert git('rev-parse','HEAD^').decode().strip()==audit['base']
actual={p:H(git('show',ref+p)) for p in audit['source_inputs'] if p in audit['allowed_paths']}
assert all(sha==audit['source_inputs'][p]==H((C/p).read_bytes()) for p,sha in actual.items())
if mode!='staged':
    tracked=set(git('ls-files').decode().splitlines())
    assert all(H(git('show',ref+p))==sha for p,sha in audit['source_inputs'].items() if p in tracked)
    assert all(H((C/p).read_bytes())==sha for p,sha in audit['source_inputs'].items())
out=dict(mode=mode,base=audit['base'],head=None if mode=='staged' else head,changed_paths=changed,blob_sha256=actual,
    all_final_source_inputs_equal=mode!='staged',tracked_source_paths=sorted(p for p in audit['source_inputs'] if p in tracked) if mode!='staged' else [],untracked_source_paths=sorted(p for p in audit['source_inputs'] if p not in tracked) if mode!='staged' else [],utc=datetime.datetime.now(datetime.timezone.utc).isoformat())
(HERE/('staged-check.json' if mode=='staged' else 'post-commit.json')).write_text(json.dumps(out,indent=2),encoding='utf8')
print(json.dumps(out))
