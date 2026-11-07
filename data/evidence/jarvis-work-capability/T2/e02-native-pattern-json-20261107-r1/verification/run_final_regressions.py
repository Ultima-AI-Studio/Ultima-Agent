"""Two independent guarded offline shards at a time; never retry a shard."""
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import json, subprocess, sys

N=Path(__file__).resolve().parents[1]
GROUPS=['json-green','grammar','coverage-green','failure-green','http-green','unique-green','grounding-green','metadata-green','claim-green',
        'reference-green','target-green','diagnostics-green','research-a','research-b',
        'navigation','transport','delivery']

def run(group):
    p=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(N/'verification/run_product_checks.py'),group],
        capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    with (N/'verification'/('final-batch-'+group+'.log')).open('xb') as f:f.write(p.stdout+p.stderr)
    return group,p.returncode

with ThreadPoolExecutor(max_workers=2) as pool:
    futures=[pool.submit(run,g) for g in GROUPS]
    results={}
    for future in as_completed(futures):
        group,code=future.result();results[group]=code
        print(json.dumps(dict(group=group,exit_code=code)),flush=True)
with (N/'verification/final-regression-batch.json').open('x',encoding='utf8') as f:json.dump(results,f,indent=2)
raise SystemExit(int(any(results.values())))
