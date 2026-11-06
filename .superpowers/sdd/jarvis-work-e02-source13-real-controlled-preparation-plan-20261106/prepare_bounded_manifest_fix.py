from pathlib import Path
import datetime as dt,hashlib,json
R=Path(r'H:\UltimaAI\UltimaAgent');T=R/'data/evidence/jarvis-work-capability/T2'
OLD=T/'e02-source13-real-controlled-preparation-20261106';NEW=T/'e02-source13-real-controlled-preparation-20261107-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
def load(p):return json.loads(p.read_bytes())
manifest=load(OLD/'manifest.json');review=load(OLD/'review/independent-preparation-review.json')
assert review['verdict']=='NEEDS_FIXES' and len(review['findings'])==1 and review['manifest_sha256']==sha(OLD/'manifest.json')
assert sha(OLD/'review/independent-preparation-review.json')=='5dbb5c54eb38b5c8e4b04cb7e280cf7d5c9dd2e057dedeea20eac1999da4220f'
for name,digest in manifest['files'].items():assert sha(OLD/name)==digest,name
NEW.mkdir(exist_ok=False)
for name,digest in manifest['files'].items():
    dest=NEW/name;dest.parent.mkdir(parents=True,exist_ok=True);dest.write_bytes((OLD/name).read_bytes());assert sha(dest)==digest
(NEW/'revision').mkdir()
(NEW/'revision/previous-manifest.json').write_bytes((OLD/'manifest.json').read_bytes())
(NEW/'revision/previous-independent-review.json').write_bytes((OLD/'review/independent-preparation-review.json').read_bytes())
record=dict(scope='One bounded PREP-I01 manifest serialization correction; no product or runtime change',
    previous_root=str(OLD),current_root=str(NEW),previous_manifest_sha256=sha(OLD/'manifest.json'),previous_review_sha256=sha(OLD/'review/independent-preparation-review.json'),
    copied_members=len(manifest['files']),actual_case_allocation=0,result_review_allocation=0,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat())
(NEW/'revision/scope.json').write_text(json.dumps(record,indent=2),encoding='utf8')
ledger=Path(__file__).parent/'progress.md'
with ledger.open('a',encoding='utf8') as f:
    f.write('\nFinal: Important PREP-I01 accepted: the actual Windows manifest serializes backslashes while entry requires slash member names. Preserve the reviewed 172-member candidate and NEEDS_FIXES report byte-for-byte; fix only the serializer and add an actual-producer regression in sibling e02-source13-real-controlled-preparation-20261107-r1. No product, model, budget or actual allocation changes.\n')
    f.write('Final: Ruling: checksum-bound independent PASS is an existing runtime admission requirement; a root-only fix disposition cannot mint that PASS. After one bounded correction and its RED/GREEN, use the same reviewer only for the changed serializer/test and new binding readback, not another whole-branch rereview. Cost: one additional read-only confirmation; no product or model work.\n')
print(json.dumps(record))
