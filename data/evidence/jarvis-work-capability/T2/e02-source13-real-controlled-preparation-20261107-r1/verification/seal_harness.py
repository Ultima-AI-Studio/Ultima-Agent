"""Seal tested harness sources only; no approval or runtime allocation."""
from pathlib import Path
import hashlib,json,difflib
N=Path(__file__).resolve().parents[1];H=N/'harness'
OLD=N.parent/'navigation-source10-validation-20261103-inert2/harness'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
path=H/'manifest.json';previous=path.read_bytes()
with (N/'verification/harness-manifest-before-final.json').open('xb') as stream:stream.write(previous)
manifest=json.loads(previous)
manifest['files']={name:sha(H/name) for name in manifest['files']}
path.write_text(json.dumps(manifest,ensure_ascii=False,indent=2)+'\n',encoding='utf8')
diff=[]
for name in ('adapter.py','test_adapter.py','run_checks.py','headless_proof.py','README.md'):
    diff.extend(difflib.unified_diff((OLD/name).read_text('utf8').splitlines(True),(H/name).read_text('utf8').splitlines(True),fromfile='accepted-old/'+name,tofile='current-source13/'+name))
with (N/'verification/harness-final.diff').open('x',encoding='utf8') as stream:stream.write(''.join(diff))
print(json.dumps(dict(manifest_sha256=sha(path),runtime_authority=False)))
