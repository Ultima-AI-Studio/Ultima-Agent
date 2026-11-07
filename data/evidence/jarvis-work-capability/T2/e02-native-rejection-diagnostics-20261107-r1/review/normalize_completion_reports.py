"""Normalize only new post-review report outputs; preserve sealed inputs verbatim."""
from pathlib import Path
import datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1];R=N.parents[4]
M=Path('H:/UltimaAI/ultima-docs-repo')
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def save(p,v):
    with p.open('xb') as f:f.write((json.dumps(v,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
assert sha(N/'manifest.json')=='5ecc68ffa1e4828c81d778a02e1ae9664bd692efbbd7073c9bc4ef13481fbf4b'
assert json.loads((N/'review/independent-preparation-review.json').read_bytes())['verdict']=='PASS_PREPARATION_ONLY'
binding=json.loads((N/'review/output-normalization-supplement.json').read_bytes())
assert sha(Path(__file__))==binding['normalizer_sha256']
report=R/'docs/reports/jarvis-work-t2-e02-native-response-rejection-diagnostics-preparation-20261107.md'
mirror=M/'docs/shared/research/ultimaagent-work-capability/reports'/report.name
paths=[N/'completion-report.md',report,mirror]
reg=N/'verification/closeout-registration.json';registration=json.loads(reg.read_bytes())
assert paths[0].read_bytes()==report.read_bytes()==mirror.read_bytes()
for entry in registration['mirror']:
    assert sha(Path(entry['source']))==sha(Path(entry['target']))==entry['sha256']
changes=[]
for i,p in enumerate([*paths,reg]):
    with (N/'review'/('normalization-before-'+str(i)+'.raw')).open('xb') as f:f.write(p.read_bytes())
for p in paths:
    raw=p.read_bytes();normalized=raw.replace(b'\r\n',b'\n')
    assert normalized.decode('utf8').splitlines()==raw.decode('utf8').splitlines()
    p.write_bytes(normalized)
    changes.append(dict(path=str(p),before=hashlib.sha256(raw).hexdigest(),after=sha(p),only_crlf_to_lf=True))
for entry in registration['mirror']:
    assert sha(Path(entry['source']))==sha(Path(entry['target']))
    entry['sha256']=sha(Path(entry['source']))
reg.write_bytes((json.dumps(registration,ensure_ascii=False,indent=2)+'\n').encode('utf8'))
manifest=json.loads((N/'manifest.json').read_bytes())
for name,h in manifest['files'].items():assert sha(N/name)==h,name
save(N/'review/output-normalization-receipt.json',dict(verdict='PASS_NEW_REPORT_LINE_ENDINGS_ONLY',
    supplement_sha256=sha(N/'review/output-normalization-supplement.json'),changes=changes,
    manifest_unchanged=True,recorded_utc=dt.datetime.now(dt.timezone.utc).isoformat(),actual_calls=0,model_calls=0))
print(json.dumps(dict(normalized_reports=3,sealed_members_preserved=len(manifest['files']),actual_calls=0)))
