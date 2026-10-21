import hashlib,json
from pathlib import Path
OUT=Path(__file__).resolve().parent
with (OUT/'result-final.json').open('xb') as f:f.write((OUT/'result.json').read_bytes())
(OUT/'result.json').write_bytes((OUT/'preliminary-byte-prefix-result.json').read_bytes())
assert (OUT/'result.json').read_bytes()==(OUT/'preliminary-byte-prefix-result.json').read_bytes()
files={p.name:hashlib.sha256(p.read_bytes()).hexdigest() for p in sorted(OUT.iterdir()) if p.is_file()}
with (OUT/'evidence-sha256.json').open('x',encoding='utf-8') as f:json.dump(files,f,indent=2)
bad=[n for n,h in files.items() if hashlib.sha256((OUT/n).read_bytes()).hexdigest()!=h]
print(json.dumps({'sealed_files':len(files),'mismatches':bad,'final_verdict':json.loads((OUT/'result-final.json').read_text())['verdict'],
 'initial_result_restored':files['result.json']==files['preliminary-byte-prefix-result.json']}))
