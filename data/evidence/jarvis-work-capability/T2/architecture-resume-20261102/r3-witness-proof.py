from pathlib import Path
import ast, hashlib, json
from pygments.lexers.javascript import TypeScriptLexer
e=Path(__file__).parent
donor=Path('H:/UltimaAI/UltimaAgent/docs/research/sources/jarvis-ceo/src/agents/unified-agent.ts')
raw=donor.read_bytes(); text=raw.decode()
sha=hashlib.sha256(raw).hexdigest()
assert sha=='fbb004ce8a8cccb74f687e6829a2e2fd62d3b160204eeaef74152de80497ef89'
project={'source_id':'S3','lines':list(enumerate(text.splitlines(),1)),'omitted':False}
count=len(json.dumps(project,ensure_ascii=False,separators=(',',':')))
assert count<=5998
tokens=[(text.count('\n',0,i)+1,str(kind),val) for i,kind,val in TypeScriptLexer().get_tokens_unprocessed(text) if val.strip() and 71<=text.count('\n',0,i)+1<=74]
assert any(v=='execute' for _,_,v in tokens)
py=(e.parent/'20261102-610005e/e02-round-1/S3.decoded-body.txt').read_bytes().decode()
nodes=[n for n in ast.walk(ast.parse(py)) if isinstance(n,ast.Assign) and isinstance(n.value,ast.Call) and ast.unparse(n.value.func)=='self._executor.execute']
assert len(nodes)==1
node=nodes[0]; lines=py.splitlines()
tail={'source_id':'S4','lines':[[i,lines[i-1]] for i in range(node.lineno,len(lines)+1)],'omitted':True}
tail_size=len(json.dumps(tail,separators=(',',':'),ensure_ascii=False))
assert tail_size<2999
out=dict(donor_sha256=sha,donor_chars=count,allowed_chars=5998,typescript_span=tokens,python_executor=dict(lines=[node.lineno,node.end_lineno],text=lines[node.lineno-1:node.end_lineno],through_end_serialized_chars=tail_size),evidence_type='offline existing donor and recorded body only')
(e/'r3-witness-proof.json').write_text(json.dumps(out,ensure_ascii=False,indent=2),encoding='utf8')
print(count,node.lineno,node.end_lineno,tail_size)
