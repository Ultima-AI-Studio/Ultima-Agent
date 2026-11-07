"""Read an existing local provider log once; preserve a narrow case-correlated supplement."""
from pathlib import Path
import datetime as dt,hashlib,json
N=Path(__file__).resolve().parents[1]
P=Path('C:/Users/Administrator/AppData/Local/Ollama/server.log')
D=N/'review/native-log-supplement'
def sha(raw):return hashlib.sha256(raw).hexdigest()
def save(p,value):
    with p.open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
raw=P.read_bytes();assert len(raw)<16*1024*1024
lines=raw.splitlines(keepends=True)
ending=b'[GIN] 2026/11/07 - 16:10:30 | 500 |'
end=[i for i,line in enumerate(lines) if line.startswith(ending) and b'"/api/chat"' in line][-1]
start=[i for i,line in enumerate(lines[:end]) if b'slot launch_slot_' in line and b'| task 261 |' in line][-1]
chunk=b''.join(lines[start:end+1]);assert len(chunk)<131072
assert b'common_chat_peg_parse: unparsed peg-native output:' in chunk
assert b'/  2048 tokens' in chunk
status=[(i+1,line) for i,line in enumerate(lines[:end+1]) if line.startswith((b'[GIN] 2026/11/07 - 16:09:',b'[GIN] 2026/11/07 - 16:10:')) and b'POST' in line and b'"/api/chat"' in line]
assert len(status)==7 and sum(b'| 200 |' in line for _,line in status)==6 and b'| 500 |' in status[-1][1]
packet=json.loads((N/'actual/E02-controlled-1/trusted-failure-diagnostic.raw').read_bytes())
ids={card['id'] for page in packet['pages'] for card in page['cards']}
matching=sorted(value for value in ids if value.encode() in chunk);assert matching
prior=json.loads((N/'verification/fixtures/predecessor-failure-diagnostic.json').read_bytes())
priorids={card['id'] for page in prior['pages'] for card in page['cards']}
D.mkdir(exist_ok=False)
with (D/'native-last-generation.log').open('xb') as f:f.write(chunk)
with (D/'native-status-lines.log').open('xb') as f:f.write(b''.join(line for _,line in status))
receipt=dict(kind='READONLY_CASE_CORRELATED_PROVIDER_LOG_SUPPLEMENT',captured_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    run_id='be79869f-10e5-4c0d-96a9-144cd5967c12',source=str(P),source_observed_bytes=len(raw),source_observed_sha256=sha(raw),
    selected_first_line=start+1,selected_last_line=end+1,status_line_numbers=[i for i,_ in status],
    matching_case_evidence_ids=matching,matching_prior_case_evidence_ids=sorted(set(matching)&priorids),
    case_result_manifest_sha256=sha((N/'review/result-inputs/result-manifest.json').read_bytes()),
    status_counts={'200':6,'500':1},last_logged_generation_tokens=2048,parser_message='unparsed peg-native output',
    trusted_product_response_body=False,immutable_runtime_proof=False,acceptance_credit=0,
    limitations=['Existing shared service log correlated by time and evidence IDs; not an exported request-bound transport receipt.',
        'Provider partial output is unvalidated and is not a research artifact or factual acceptance evidence.',
        'This does not prove why native grammar/parser failed or that source uniqueness is fixed in actual execution.'],
    actual_calls=0,model_calls=0,service_operations=0,process_operations=0)
save(D/'capture.json',receipt)
members=[D/'native-last-generation.log',D/'native-status-lines.log',D/'capture.json',Path(__file__)]
save(D/'manifest.json',dict(kind='SUPPLEMENT_NOT_REWRITTEN_CASE_RESULT',files={p.relative_to(N).as_posix():sha(p.read_bytes()) for p in members}))
print(json.dumps(dict(manifest_sha256=sha((D/'manifest.json').read_bytes()),selected_bytes=len(chunk),matching_case_ids=len(matching),
    matching_prior_case_ids=len(set(matching)&priorids),status_counts=receipt['status_counts'],last_logged_generation_tokens=2048)))
