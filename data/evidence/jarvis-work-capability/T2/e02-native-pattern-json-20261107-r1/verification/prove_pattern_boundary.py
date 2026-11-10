"""Offline reference conversion and raw-string reproducer, not a native run."""
from pathlib import Path
import hashlib,itertools,json,re,runpy,sys
N=Path(__file__).resolve().parents[1]
out=N/'diagnosis';out.mkdir(exist_ok=False)
def guard(event,args):
    if event.startswith(('socket.','subprocess.','ctypes.')) or event in ('os.system','os.startfile','os.kill'):
        raise RuntimeError('Offline reference proof denied '+event)
sys.addaudithook(guard)
module=runpy.run_path(str(N/'inputs/upstream/json_schema_to_grammar.py'),run_name='pinned_reference_converter')
Converter=module['SchemaConverter']
def grammar(pattern):
    c=Converter(prop_order={},allow_fetch=False,dotall=False,raw_pattern=False)
    c.visit(dict(type='string',pattern=pattern),'')
    return c.format_grammar()
# This is a design prototype, NOT production code or accepted response validation.
char=r'([^"\\\x00-\x1f]|[\\](["\\bfnrt/]|u[0-9a-fA-F]{4}))'
edge=r'([^"\\\x00-\x1fA-Za-z0-9_$.]|[\\](["\\bfnrt/]|u[0-9a-fA-F]{4}))'
after_dot=r'([^"\\\x00-\x1fA-Za-z_$]|[\\](["\\bfnrt/]|u[0-9a-fA-F]{4}))'
def old(op):return r'^(.*[^A-Za-z0-9_$.])?'+re.escape(op)+r'([^A-Za-z0-9_$.].*|\.([^A-Za-z_$].*)?)?$'
def safe(op):return '^('+char+'*'+edge+')?'+re.escape(op)+'('+edge+char+'*|\\.('+after_dot+char+'*)?)?$'
rows=[]
lines=(N/'inputs/native-log-supplement/unvalidated-output.txt').read_text(encoding='utf8').splitlines()
for i,line in enumerate(lines):
    if line.startswith(('Logger.info(','Date.now(')):
        op=line.split('(',1)[0]
        body=lines[i-1].split('"claim": "',1)[1]+'\n'+line[:-2]
        try:json.loads('"'+body+'"');valid=True
        except json.JSONDecodeError:valid=False
        before=bool(re.fullmatch(old(op),body));after=bool(re.fullmatch(safe(op),body))
        assert before and not after and not valid
        rows.append(dict(operation=op,old_raw_pattern_accepts=before,new_raw_pattern_accepts=after,json_valid=valid,body_sha256=hashlib.sha256(body.encode()).hexdigest()))
assert len(rows)==3
for name,p in [('old',old('Logger.info')),('projected',safe('Logger.info'))]:
    (out/(name+'.gbnf')).write_text(grammar(p),encoding='utf8')
accepted=0
edges=['',' ','(',')','中','é','"','\\','\t','\n','\r','\x00','\x1f','\x7f','.9','..']
for op,left,right in itertools.product(['Logger.info','Date.now','$run','a中.bé'],edges,edges):
    claim=left+op+right
    # Strict policy is still applied to DECODED text; the projected regex is wire-only.
    if not re.fullmatch(old(op),claim):continue
    encoded=json.dumps(claim,ensure_ascii=False)[1:-1]
    assert re.fullmatch(safe(op),encoded),(op,repr(claim))
    assert json.loads('"'+encoded+'"')==claim
    accepted+=1
receipt=dict(kind='OFFLINE_REFERENCE_CONVERTER_PROOF',cases=rows,valid_strict_claim_serializations=accepted,
    upstream_revision='ggml-org/llama.cpp b10488',reference_python_only=True,compiled_native_validator_run=False,
    known_difference='C++ supports noncapturing groups; prototype uses capturing groups shared by both converters.',
    limitation='Reference grammar output and raw-pattern probes confirm a schema compatibility gap; a new actual native run is still required to verify the repair.',
    actual_calls=0,model_calls=0,network_calls=0)
(out/'proof.json').write_text(json.dumps(receipt,ensure_ascii=False,indent=2),encoding='utf8')
print(json.dumps(receipt,ensure_ascii=False))
