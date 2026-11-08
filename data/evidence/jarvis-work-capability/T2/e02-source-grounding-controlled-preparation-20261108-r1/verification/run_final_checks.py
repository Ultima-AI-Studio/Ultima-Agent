"""Run independent original guarded offline groups, two at a time, with no retries."""
from concurrent.futures import ThreadPoolExecutor,as_completed
from pathlib import Path
import json,subprocess,sys
N=Path(__file__).resolve().parents[1]
JOBS=[('base-a','harness/run_checks.py','base-a'),('base-b','harness/run_checks.py','base-b'),
      ('recovery','harness/run_checks.py','recovery'),('export-green','harness/run_checks.py','export-green'),
      ('failure-export-green','harness/run_checks.py','failure-export-green'),
      ('bindings','verification/run_binding_checks.py','final-green'),('entry','verification/run_entry_checks.py','final-green'),
      ('boundary','verification/run_boundary_checks.py','final-green')]
def run(job):
    name,file,stage=job
    r=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(N/file),stage],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
    with (N/'verification'/('final-batch-'+name+'.log')).open('xb') as f:f.write(r.stdout+r.stderr)
    return name,r.returncode
with ThreadPoolExecutor(max_workers=2) as pool:
    results={}
    for future in as_completed([pool.submit(run,job) for job in JOBS]):
        name,code=future.result();results[name]=code;print(json.dumps(dict(group=name,exit_code=code)),flush=True)
with (N/'verification/final-batch-checks.json').open('x',encoding='utf8') as f:json.dump(results,f,indent=2)
raise SystemExit(int(any(results.values())))
