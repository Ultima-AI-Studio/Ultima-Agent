"""Capture a bounded, case-correlated supplement without changing the case."""
from pathlib import Path
import datetime as dt, hashlib, json, re
N=Path(__file__).resolve().parents[1]
T=N.parent
PREV=T/'e02-source-coverage-controlled-preparation-20261107-r1'
P=Path('C:/Users/Administrator/AppData/Local/Ollama/server.log')
D=N/'inputs/native-log-supplement'
def sha(raw): return hashlib.sha256(raw).hexdigest()
def save(p,obj):
    p.parent.mkdir(parents=True,exist_ok=True)
    with p.open('x',encoding='utf8') as f: json.dump(obj,f,ensure_ascii=False,indent=2)
raw=P.read_bytes()
assert len(raw)<16*1024*1024
lines=raw.splitlines(keepends=True)
end=next(i for i,line in enumerate(lines) if line.startswith(b'[GIN] 2026/11/07 - 18:53:48 | 500 |') and b'"/api/chat"' in line)
start=max(i for i,line in enumerate(lines[:end]) if b'slot launch_slot_' in line and b'| task 260 |' in line)
chunk=b''.join(lines[start:end+1]); assert len(chunk)<131072
marker=b'common_chat_peg_parse: unparsed peg-native output: '
assert marker in chunk and b'/   840 tokens' in chunk and b'truncated = 0' in chunk
status=[(i+1,line) for i,line in enumerate(lines[:end+1]) if line.startswith(b'[GIN] 2026/11/07 - 18:53:') and b'POST' in line and b'"/api/chat"' in line]
assert len(status)==7 and sum(b'| 200 |' in line for _,line in status)==6 and b'| 500 |' in status[-1][1]
output=chunk.split(marker,1)[1].split(b'srv  cancel_tasks:',1)[0].rstrip()
# The shared log contains untrusted model text; it is diagnostic only.
try:
    json.loads(output)
except json.JSONDecodeError as exc:
    error=dict(type=type(exc).__name__,line=exc.lineno,column=exc.colno,position=exc.pos,message=exc.msg)
else: raise AssertionError('Expected malformed logged JSON')
packet=json.loads((PREV/'actual/E02-controlled-1/trusted-failure-diagnostic.raw').read_bytes())
ids={c['id'] for page in packet['pages'] for c in page['cards']}
matching=sorted(v for v in ids if v.encode() in output)
assert matching
D.mkdir(exist_ok=False)
for name,data in [('native-last-generation.log',chunk),('native-status-lines.log',b''.join(v for _,v in status)),('unvalidated-output.txt',output)]:
    with (D/name).open('xb') as f:f.write(data)
save(D/'capture.json',dict(kind='READONLY_CASE_CORRELATED_LOG_SUPPLEMENT',captured_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
    run_id='5e6ea89c-8e47-43a6-9480-7a11d72cabf5',source=str(P),source_observed_bytes=len(raw),source_observed_sha256=sha(raw),
    first_line=start+1,last_line=end+1,status_line_numbers=[i for i,_ in status],matching_case_evidence_ids=matching,
    case_result_manifest_sha256=sha((PREV/'review/result-inputs/result-manifest.json').read_bytes()),
    status_counts={'200':6,'500':1},logged_generation_tokens=840,logged_truncated=0,strict_json_error=error,
    trusted_product_response=False,request_bound=False,acceptance_credit=0,
    limitations=['Shared native log correlated by local time, status sequence and evidence IDs; IDs can recur between cases.',
      'No request body was retained in the failed product case; the log is not an immutable request-bound receipt.',
      'Logged model text is unvalidated and is neither a research artifact nor factual evidence.'],
    actual_calls=0,model_calls=0,service_operations=0,process_operations=0))
save(D/'manifest.json',dict(kind='SUPPLEMENT_ONLY',files={p.relative_to(N).as_posix():sha(p.read_bytes()) for p in [*D.iterdir(),Path(__file__)]}))
print(json.dumps(dict(selected_bytes=len(chunk),last_generation_tokens=840,json_error=error,manifest_sha256=sha((D/'manifest.json').read_bytes())),ensure_ascii=False))
