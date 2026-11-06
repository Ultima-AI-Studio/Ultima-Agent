"""Read back the just-completed test/checkpoint evidence; never run a product."""
from pathlib import Path
import hashlib
import json
E=Path(__file__).resolve().parents[1]
def load(p):return json.loads(p.read_bytes())
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
checkpoint=load(E/'verification/handoff-review-checkpoint.json')
assert sha(E/'manifest.json')==checkpoint['manifest_sha256']
assert sha(E/'entry-manifest.json')==checkpoint['entry_manifest_sha256']
for row in load(E/'manifest.json')['files']:assert sha(E/row['path'])==row['sha256'],row['path']
for path,digest in load(E/'entry-manifest.json')['files'].items():assert sha(Path(path))==digest,path
receipt=load(E/'offline/handoff-full-green/receipt.json')
assert receipt['exit_code']==0 and receipt['counts']==dict(tests=89,failures=0,errors=0,skipped=0)
assert {p.name:sha(p) for p in (E/'code').glob('*.py')}==receipt['package_after']
old=set(load(E/'offline/review-r1-full-green/inventory.json'));new=set(load(E/'offline/handoff-full-green/inventory.json'))
assert len(old)==83 and len(new)==89 and old.issubset(new)
assert not (E/'release').exists() and not (E/'runs').exists()
print('PASS: exact sealed checkpoint; fresh full89 receipt; all prior83 test IDs retained; zero runtime release')
