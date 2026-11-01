from pathlib import Path
import hashlib,json
e=Path(__file__).parent
p=e.parent/'20261102-610005e/e02-round-1'
data=json.loads((p/'invalid-arguments-evidence.json').read_bytes())
print(data.keys())
text=data['first_composer_inference_end']['data']['content']
arg=text.split('Action Input:',1)[1].strip()
try: json.loads(arg); raise AssertionError('expected malformed arguments')
except json.JSONDecodeError as x: error=dict(message=x.msg,col=x.colno,pos=x.pos)
receipt=json.loads((p/'receipt.json').read_bytes())
sources=[dict(id=s['source_id'],url=s['final_url'],body_hash=hashlib.sha256(s['body'].encode()).hexdigest(),chars=len(s['text']),run_offset=s['text'].find('def run('),dispatch_offset=s['text'].find('self._executor.execute')) for s in receipt['available_sources']]
assert len(sources)==3 and error['pos']==2029
(e/'readonly-reproduction.json').write_text(json.dumps(dict(decoder=error,arg_sha256=hashlib.sha256(arg.encode()).hexdigest(),sources=sources,tool_error=data['first_failed_report_result']),indent=2),encoding='utf8')
