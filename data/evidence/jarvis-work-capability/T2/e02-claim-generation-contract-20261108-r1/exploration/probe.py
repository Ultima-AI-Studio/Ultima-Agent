"""No-model characterization of operation-first and finite reference grammars."""
from pathlib import Path
import ast, hashlib, json, re, runpy, sys, time
N=Path(__file__).resolve().parents[1];T=N.parent;R=N.parents[4]
C=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent')
UP=T/'e02-native-pattern-json-20261107-r1/inputs/upstream'
ACT=T/'e02-output-structure-controlled-preparation-20261108-r1/actual/E02-controlled-1/trusted-failure-diagnostic.raw'
def sha(p):return hashlib.sha256(p.read_bytes()).hexdigest()
denied=[]
def guard(event,args):
    if event.startswith(('socket.','subprocess.','os.system','os.startfile','ctypes.')):
        denied.append(event);raise RuntimeError('Offline probe denies '+event)
sys.addaudithook(guard)
tree=ast.parse((C/'src/brain/agent_server.py').read_bytes())
function=next(x for x in tree.body if isinstance(x,ast.FunctionDef) and x.name=='_research_code_claim_sampler_pattern')
ns={};exec(compile(ast.Module(body=[function],type_ignores=[]),'frozen_function_extract','exec'),ns)
reference=runpy.run_path(str(UP/'json_schema_to_grammar.py'),run_name='offline_reference_probe')
diagnostic=json.loads(ACT.read_bytes());captured=diagnostic['output_structure']['evidence']
assert captured['mode']=='FULL' and captured['omitted_chars']==0
content=captured['fragments'][0]['text']
assert hashlib.sha256(content.encode()).hexdigest()=='1f6b669b10cd3418e3ea6279a0c5253ec239184a6eab2efa1642d47963cec4de'
data=[]
for operation in ('Logger.info','Date.now','$run','a中.bé'):
    strict=r'^(.*[^A-Za-z0-9_$.])?'+re.escape(operation)+r'([^A-Za-z0-9_$.].*|\.([^A-Za-z_$].*)?)?$'
    old=ns['_research_code_claim_sampler_pattern'](strict)
    escape=r'[\\](["\\bfnrt/]|u[0-9a-fA-F]{4})'
    char=r'([^"\\\x00-\x1f]|'+escape+')'
    boundary=r'([^"\\\x00-\x1fA-Za-z0-9_$.]|'+escape+')'
    after_dot=r'([^"\\\x00-\x1fA-Za-z_$]|'+escape+')'
    prefix=re.escape(operation)+'('+boundary+char+'*|\\.('+after_dot+char+'*)?)?'
    first='^'+prefix+'$'
    finite='^'+re.escape(operation)+'('+boundary+char+'{0,'+str(1999-len(operation))+'}|\\.('+after_dot+char+'{0,'+str(1998-len(operation))+'})?)?$'
    witness='概述。'+operation+' 记录一个已见调用。'
    overlong=operation+' '+('字'*2000)
    assert re.fullmatch(old,witness) and not re.fullmatch(first,witness)
    assert re.fullmatch(old,overlong) and re.fullmatch(first,overlong) and not re.fullmatch(finite,overlong)
    positive=operation+' 记录 "中文" 与反斜杠 \\。'
    raw=json.dumps(positive,ensure_ascii=False)[1:-1]
    assert all(re.fullmatch(p,raw) for p in (old,first,finite))
    assert re.fullmatch(strict,positive)
    shapes=[]
    for label,p in [('old',old),('operation_first',first),('operation_first_finite2000',finite)]:
        start=time.perf_counter();converter=reference['SchemaConverter'](prop_order={},allow_fetch=False,dotall=False,raw_pattern=False)
        converter.visit(dict(type='string',pattern=p),'');grammar=converter.format_grammar()
        shapes.append(dict(kind=label,pattern_bytes=len(p.encode()),grammar_bytes=len(grammar.encode()),reference_seconds=time.perf_counter()-start,grammar_sha256=hashlib.sha256(grammar.encode()).hexdigest()))
    data.append(dict(operation=operation,old_accepts_unbounded_prefix=True,operation_first_rejects_prefix=True,
        operation_first_still_allows_overlength_tail=True,finite_reference_rejects_over2000=True,conversions=shapes))
legacy=R/'docs/plans/jarvis-work-native-schema-compatibility-addendum-20261102.md'
value=dict(kind='OFFLINE_EXPRESSION_CHARACTERIZATION',candidate='bf7f7a9cf0e4ba559c29daa388c00379d12d345a',
    inputs={str(p):sha(p) for p in (ACT,C/'src/brain/agent_server.py',UP/'json_schema_to_grammar.py',UP/'json-schema-to-grammar.cpp',legacy)},
    rows=data,denied=denied,model_calls=0,actual_cases=0,product_changes=0,
    finite_native_binary_compatibility_proven=False,
    interpretation='Operation-first removes the exact unbounded prefix path. It does not bound the suffix or prove semantic delivery. Finite2000 converts in the Python reference only; historical native repeat-complexity failure forbids treating this as native compatibility proof.',
    recommendation='Minimal operation-first projection and matching shared prompt; retain original decoded length and factual gates, record unbounded tails/noncode fields as unresolved actual risks rather than reintroducing unqualified finite repeats.')
with (N/'exploration/receipt.json').open('x',encoding='utf8',newline='\n') as f:json.dump(value,f,ensure_ascii=False,indent=2)
print(json.dumps(dict(operations=len(data),reference_conversions=sum(len(x['conversions']) for x in data),model_calls=0,native_binary_compatibility_proven=False,unbounded_suffix_retained=True)))
