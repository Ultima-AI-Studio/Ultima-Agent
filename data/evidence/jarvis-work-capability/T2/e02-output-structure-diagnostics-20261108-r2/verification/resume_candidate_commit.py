"""Resume a pre-stage stop after initializing the skill's self-ignored workspace."""
from pathlib import Path
import hashlib,json
N=Path(__file__).resolve().parents[1];original=N/'verification/commit_candidate.py'
record=dict(status='PRE_STAGE_STOP_RESOLVED',original_script_sha256=hashlib.sha256(original.read_bytes()).hexdigest(),
    initial_error='AssertionError: untracked .superpowers/sdd plan progress.md',
    initial_product_commit=False,initial_index_mutated=False,
    resolution='Run canonical sdd-workspace to create its self-ignoring .gitignore; no tracked/source changes',
    actual_cases=0,model_calls=0)
with (N/'verification/commit-preflight-failure.json').open('x',encoding='utf8') as f:json.dump(record,f,indent=2)
text=original.read_text('utf8').replace('offline-precommit-readback.json','offline-precommit-resumed-readback.json')
exec(compile(text,str(original),'exec'),dict(__name__='__main__',__file__=str(original)))
