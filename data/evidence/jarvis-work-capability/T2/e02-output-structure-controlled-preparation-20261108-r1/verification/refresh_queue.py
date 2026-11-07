"""Regenerate aggregate queue status from registered rows without dispatching work."""
from pathlib import Path
import datetime as dt,hashlib,json,subprocess,sys
N=Path(__file__).resolve().parents[1]
Q=Path('H:/UltimaAI/_shared/queue')
generator=Q/'queue-status-gen.py';index=Q/'global-queue-index.md';status=Q/'queue-status.json'
sha=lambda p:hashlib.sha256(p.read_bytes()).hexdigest()
assert sha(generator)=='da440b378af5d38e6a6d727fd342cd64287e130fccdeecb5a619634a36ad6a3d'
before_index=index.read_bytes();before_status=status.read_bytes()
def registrations(raw):
    text=raw.decode('utf8');part=text.split('<!-- queue-items:start -->')[1].split('<!-- queue-items:end -->')[0]
    return [line.strip() for line in part.splitlines() if line.strip()]
r=subprocess.run([sys.executable,'-I','-B','-X','utf8',str(generator)],capture_output=True,creationflags=subprocess.CREATE_NO_WINDOW)
assert r.returncode==0,(r.returncode,r.stderr.decode('utf8'))
assert registrations(before_index)==registrations(index.read_bytes())
value=json.loads(status.read_bytes())
with (N/'verification/queue-status-after.json').open('xb') as f:f.write(status.read_bytes())
receipt=dict(recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),generator_sha256=sha(generator),exit_code=r.returncode,
    stdout=r.stdout.decode('utf8'),stderr=r.stderr.decode('utf8'),before_sha256=hashlib.sha256(before_status).hexdigest(),
    after_sha256=sha(status),global_before_sha256=hashlib.sha256(before_index).hexdigest(),global_after_sha256=sha(index),
    registration_rows_unchanged=True,scope='Registration only; not actual process or acceptance evidence',summary=value.get('summary'))
with (N/'verification/queue-refresh.json').open('x',encoding='utf8',newline='\n') as f:json.dump(receipt,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(exit_code=0,registrations_unchanged=True,summary=value.get('summary'))))
