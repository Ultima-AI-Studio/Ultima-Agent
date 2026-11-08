"""Offline official-reference spike: no product import, network or native/model run."""
from pathlib import Path
from copy import deepcopy
import hashlib,json,runpy,sys,time
N=Path(__file__).resolve().parents[1]
P=N.parent/'e02-claim-generation-controlled-preparation-20261108-r1'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
denied=[]
def audit(event,args):
    if event.startswith('socket.') or event in ('subprocess.Popen','os.system','os.startfile','ctypes.dlopen'):
        denied.append(event);raise RuntimeError('Offline reference only: '+event)
sys.addaudithook(audit)
upstream=N/'inputs/upstream/json_schema_to_grammar.py'
module=runpy.run_path(str(upstream),run_name='offline_order_reference')
old=json.loads((P/'actual/E02-controlled-1/trusted-runtime.raw').read_bytes())['wires'][6]
old_request=json.loads(old['entity']);original=deepcopy(old_request['format'])
def transform(node):
    if isinstance(node,list):return [transform(x) for x in node]
    if not isinstance(node,dict):return node
    new={k:transform(v) for k,v in node.items()}
    if (new.get('type')=='object' and new.get('additionalProperties') is False
            and set(new.get('properties',{}))=={'claim','evidence_id'}
            and set(new.get('required',[]))=={'claim','evidence_id'}):
        return dict(type='object',required=['evidence_id','claim'],minProperties=2,maxProperties=2,
            allOf=[dict(properties={key:new['properties'][key]},required=[key]) for key in ('evidence_id','claim')])
    return new
projected=transform(original)
def convert(schema,label):
    schema=json.loads(json.dumps(schema,sort_keys=True,ensure_ascii=False,separators=(',',':')))
    converter=module['SchemaConverter'](prop_order={},allow_fetch=False,dotall=False,raw_pattern=False)
    start=time.monotonic();converter.visit(converter.resolve_refs(schema,'file://offline-order.json'),'')
    grammar=converter.format_grammar();elapsed=time.monotonic()-start
    out=N/'exploration'/(label+'.gbnf')
    with out.open('x',encoding='utf8',newline='\n') as f:f.write(grammar)
    rules=[line for line in grammar.splitlines() if 'claim-kv' in line and 'evidence-id-kv' in line]
    assert rules
    return dict(label=label,grammar_sha256=sha(out),grammar_bytes=len(grammar.encode()),seconds=elapsed,
        fact_rule_count=len(rules),evidence_before_claim=all(line.index('evidence-id-kv')<line.index('claim-kv') for line in rules),
        claim_before_evidence=all(line.index('claim-kv')<line.index('evidence-id-kv') for line in rules),rules=rules)
results=[convert(original,'original-writer'),convert(projected,'ordered-writer')]
assert results[0]['claim_before_evidence'] and results[1]['evidence_before_claim']
old_request['format']=projected
entity=json.dumps(old_request,sort_keys=True,ensure_ascii=False,separators=(',',':')).encode()
assert len(entity)<=49152
with (N/'exploration/ordered-sampler-schema.json').open('x',encoding='utf8') as f:json.dump(projected,f,ensure_ascii=False,indent=2)
value=dict(kind='OFFLINE_PINNED_REFERENCE_ONLY',parent='d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b',
    result_manifest_sha256=sha(P/'review/result-inputs/result-manifest.json'),source_runtime_sha256=sha(P/'actual/E02-controlled-1/trusted-runtime.raw'),
    upstream_python_sha256=sha(upstream),upstream_cpp_sha256=sha(N/'inputs/upstream/json-schema-to-grammar.cpp'),
    results=results,original_entity_bytes=len(old['entity'].encode()),projected_entity_bytes=len(entity),
    canonical_roundtrip_preserves_allof_sequence=True,strict_schema_changed=False,product_changed=False,
    calls=dict(native=0,model=0,network=0),denied=denied,
    limit='Official reference conversion proves property emission order only. No semantic entailment, model efficacy or installed native binary compatibility claim. JSON schema equivalence and guarded SDK/replay remain required tests.')
with (N/'exploration/receipt.json').open('x',encoding='utf8') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps({k:value[k] for k in ('kind','original_entity_bytes','projected_entity_bytes','calls','denied')}))
print(json.dumps([{k:r[k] for k in ('label','grammar_bytes','fact_rule_count','evidence_before_claim','claim_before_evidence')} for r in results]))
