"""Exact local review-input checkpoint; retains unrelated work, no push."""
from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import subprocess
E=Path(__file__).resolve().parents[1]
REPO=Path(r'H:\UltimaAI\UltimaAgent')
TAG='ultimaagent-t2-e02-source13-root-entry-review-20261106'
tree=ast.parse((E/'verification/checkpoint-task1.py').read_bytes())
ns=dict(Path=Path,dt=dt,hashlib=hashlib,json=json,subprocess=subprocess,TAG=TAG)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'accepted-checkpoint-functions','exec'),ns)
sha,load,gt,checkpoint,save_new=[ns[k] for k in ('sha','load','gt','checkpoint','save_new')]
files={E/row['path'] for row in load(E/'manifest.json')['files']}
files|={E/'manifest.json',E/'review/review-input.md',Path(__file__)}
for row in load(E/'manifest.json')['files']:assert sha(E/row['path'])==row['sha256']
before=gt(REPO,'rev-parse','HEAD');assert not gt(REPO,'diff','--cached','--name-only') and not gt(REPO,'tag','--list',TAG)
names={p.relative_to(REPO).as_posix() for p in files}
foreign={p:sha(REPO/p) for p in gt(REPO,'diff','--name-only').splitlines() if p not in names}
result=checkpoint(REPO,files,before,'Prepare concrete E02 root entry and 81 offline contracts for review')
for p,value in foreign.items():assert sha(REPO/p)==value
save_new(E/'verification/review-input-checkpoint.json',dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),
    **result,manifest_sha256=sha(E/'manifest.json'),entry_manifest_sha256=sha(E/'entry-manifest.json'),
    unrelated_files_preserved=foreign,runtime_authority=False,remote_synced=False,new_push_attempted=False))
print(json.dumps(dict(commit=result['commit'],files=len(result['files']),tag=TAG,runtime_authority=False)))
