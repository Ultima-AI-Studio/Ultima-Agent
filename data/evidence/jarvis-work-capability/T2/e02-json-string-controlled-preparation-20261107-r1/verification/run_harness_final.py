"""Verify final harness bytes after one test expectation correction; no actual cases."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import hashlib,json,subprocess,sys
N=Path(__file__).resolve().parents[1]
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
p=N/'harness/manifest.json';value=json.loads(p.read_bytes())
value['files']={p.name:sha(p) for p in (N/'harness').iterdir() if p.is_file() and p.name!='manifest.json'}
p.write_text(json.dumps(value,indent=2),encoding='utf8',newline='\n')
def run(group):
    r=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(N/'harness/run_checks.py'),group],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    with (N/'verification'/('final-batch-'+group+'.log')).open('xb') as f:f.write(r.stdout+r.stderr)
    return group,r.returncode
with ThreadPoolExecutor(max_workers=2) as pool:
    results={}
    for future in as_completed([pool.submit(run,g) for g in ('base-a','base-b','recovery','export-green','failure-export-green')]):
        group,code=future.result();results[group]=code;print(json.dumps(dict(group=group,exit_code=code)),flush=True)
with (N/'verification/final-batch-checks.json').open('x',encoding='utf8',newline='\n') as f:json.dump(results,f,indent=2)
raise SystemExit(int(any(results.values())))
