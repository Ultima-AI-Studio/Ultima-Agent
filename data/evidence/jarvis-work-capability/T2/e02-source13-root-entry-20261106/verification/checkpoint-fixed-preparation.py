"""Final local fixed-source checkpoint; exact allowlists, no runtime/push."""
from pathlib import Path
import ast
import datetime as dt
import hashlib
import json
import subprocess
E=Path(__file__).resolve().parents[1];REPO=Path(r'H:\UltimaAI\UltimaAgent');MIRROR=Path(r'H:\UltimaAI\ultima-docs-repo')
TAG='ultimaagent-t2-e02-source13-root-entry-fix1-20261106'
tree=ast.parse((E/'verification/checkpoint-task1.py').read_bytes())
ns=dict(Path=Path,dt=dt,hashlib=hashlib,json=json,subprocess=subprocess,TAG=TAG)
exec(compile(ast.Module(body=[n for n in tree.body if isinstance(n,ast.FunctionDef)],type_ignores=[]),'accepted-checkpoint-functions','exec'),ns)
sha,load,gt,git,checkpoint,save_new=[ns[k] for k in ('sha','load','gt','git','checkpoint','save_new')]
manifest=load(E/'manifest.json')
for row in manifest['files']:assert sha(E/row['path'])==row['sha256']
for name,value in load(E/'entry-manifest.json')['files'].items():assert sha(Path(name))==value
assert load(E/'verification/code-preparation-gate.json')['verdict']=='NOT_READY_PENDING_FIXED_SOURCE_REVIEW'
assert load(E/'offline/review-r1-full-green/receipt.json')['counts']==dict(tests=83,failures=0,errors=0,skipped=0)
candidate=Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent')
assert gt(candidate,'rev-parse','HEAD')=='269aca511d88412dbb9c15d23911138469a37aa2' and not gt(candidate,'status','--porcelain','--untracked-files=no')
diff=git(REPO,'diff','83312d5f9573ff9cce2a9e331ce70e84e483888c','--',*(str(E/'code'/name) for name in ('entry.py','native_observation.py','test_entry.py')))
with (E/'review/r1-source.diff').open('xb') as f:f.write(diff)
request=f'''# Current fixed-source read-only review request (not allocated)

Current package manifest {sha(E/'manifest.json')}; current entry manifest {sha(E/'entry-manifest.json')}.
Prior review verdict NEEDS_FIXES, SHA {sha(E/'review/independent-preparation-review.json')}; it covers commit83312d5, not this fixed source.
Only R1 changed: existing cleanup reserve in native_observation.py; startup/qualification/wait admission in entry.py; real PrivateIO/Owned synthetic stall contracts in test_entry.py.
Read r1-source.diff, current code, inputs/review-r1-cleanup-ruling.json, verification/review-r1-fix-readback.json, execution-proposal.md and prior report. Check practical reduced waiting windows, unchanged original315 bound, existing helpers and no new killer; compare current83 vs prior81 tests and two actual RED-to-GREEN stall cases.
Keep source/model/profile/native gates unchanged. This request is only one read-only preparation review; no tests, actual worker/profile/model/network/UI/audio/service actions or actual result review.
IF01 original interface line32 requires a repaired concrete integration to be re-reviewed before runtime. Prior review/fix allocation is consumed; this file does not allocate a new one.
Desired output once separately allocated: review/independent-fixed-source-review.json, exact current hashes, findings and declined judgments; no self-authored independent PASS.
'''
(E/'review/fixed-source-review-input.md').write_text(request,encoding='utf-8',newline='\n')
files={E/row['path'] for row in manifest['files']}|{E/'manifest.json',E/'entry-manifest.json',E/'review/r1-source.diff',E/'review/fixed-source-review-input.md'}
files.update(p for p in (E/'verification').iterdir() if p.is_file())
history=E/'history/reviewed-83312d5';old=load(history/'manifest.json')
files.update(history/row['path'] for row in old['files'])
files.update(history/name for name in ('manifest.json','entry-manifest.json','independent-preparation-review.json'))
mirrors=load(E/'verification/fixed-document-mirror-readback.json')['mirrors']
for row in mirrors:assert sha(Path(row['source']))==sha(Path(row['mirror']))==row['sha256']
files.update(Path(row['source']) for row in mirrors)
files.update([E.parent/'current-run.json',REPO/'tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md',
    REPO/'tasks/queue/stages/wo-ultimaagent-20261101-0021/t2.md'])
mirror_files={Path(row['mirror']) for row in mirrors}
owned={REPO:files,MIRROR:mirror_files};heads={str(repo):gt(repo,'rev-parse','HEAD') for repo in owned};foreign={}
for repo,members in owned.items():
    assert not gt(repo,'diff','--cached','--name-only') and not gt(repo,'tag','--list',TAG)
    names={p.relative_to(repo).as_posix() for p in members}
    foreign[str(repo)]={p:sha(repo/p) for p in gt(repo,'diff','--name-only').splitlines() if p not in names}
receipt=dict(recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),manifest_sha256=sha(E/'manifest.json'),
    entry_manifest_sha256=sha(E/'entry-manifest.json'),tests=83,independent_verdict='NEEDS_FIXES_PRE_FIX_SOURCE',
    gate='NOT_READY_PENDING_FIXED_SOURCE_REVIEW',runtime_authority=False,actual_case_allocation=0,actual_result_review_allocation=0,
    mirrors=mirrors,unrelated_files_preserved=foreign,remote_synced=False,new_push_attempted=False)
save_new(E/'verification/fixed-precommit-readback.json',receipt);files.add(E/'verification/fixed-precommit-readback.json')
main=checkpoint(REPO,files,heads[str(REPO)],'Fix E02 cleanup reservation and retain closed preparation gate')
mirror=checkpoint(MIRROR,mirror_files,heads[str(MIRROR)],'Mirror E02 fixed-entry evidence and pending review scope')
for row in manifest['files']:assert sha(E/row['path'])==row['sha256']
for repo,items in foreign.items():
    for p,value in items.items():assert sha(Path(repo)/p)==value
receipt.update(main=main,mirror=mirror,tag=TAG)
save_new(E/'verification/fixed-local-checkpoint.json',receipt)
print(json.dumps(dict(main=main['commit'],main_files=len(main['files']),mirror=mirror['commit'],mirror_files=len(mirror['files']),tag=TAG,
    tests=83,gate=receipt['gate'],runtime_authority=False,remote_synced=False)))
