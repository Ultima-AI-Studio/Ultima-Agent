from pathlib import Path
import hashlib, json, re, sys
from urllib.parse import urlsplit
import pygments
from pygments.lexers.javascript import JavascriptLexer, TypeScriptLexer
from pygments.token import Comment, String, Name
sys.path.insert(0,str(Path.cwd()))
from src.brain.work_research import URL_PATTERN
e=Path(__file__).parent
prior=e.parent/'20261102-610005e/e02-round-1'
def rows(lexer,src):
    return [(src.count('\n',0,at)+1,str(kind),v.strip()) for at,kind,v in lexer.get_tokens_unprocessed(src) if v.strip()]
sample='// new Phantom()\nconst str = "new Phantom()";\nconst pattern = /Phantom\\(/;\nlet writer = new Writer();\nwriter.publish(record);\nconst tpl = `new Phantom()`;\n'
cases={}
for lexer in (JavascriptLexer(),TypeScriptLexer()):
    entries=rows(lexer,sample)
    for line in [1,2,3,6]:
        assert not any(n==line and t.startswith('Token.Name') and v=='Phantom' for n,t,v in entries)
    assert any(n==4 and t.startswith('Token.Name') and v=='Writer' for n,t,v in entries)
    assert any(n==5 and t.startswith('Token.Name') and v=='publish' for n,t,v in entries)
    cases[type(lexer).__name__]=entries
body=(prior/'S2.decoded-body.txt').read_bytes().decode()
live=[x for x in rows(TypeScriptLexer(),body) if x[0] in (39,44,51,54,55,60)]
old=json.loads((prior/'argv.json').read_bytes())['cli'][-1]
# Evidence-only lexical pattern difference; no DNS, GET, model or CLI.
proposed=re.compile(URL_PATTERN.pattern[:-2]+'，。；：！？、）】》」』”’]+')
old_values=[m.group(0).rstrip('.,;:!?，。；：！？）)]}') for m in URL_PATTERN.finditer(old)]
values=[m.group(0).rstrip('.,;:!?，。；：！？）)]}') for m in proposed.finditer(old)]
assert len(values)==4 and values[2].endswith('/src/agents/unified-agent.ts') and old_values[2]!=values[2]
assert '以及现有执行底座' in proposed.sub(' ',old)
example='看 https://example.test/资料/a%EF%BC%8Cb.ts，随后与 https://example.test/b?q=a,b&x=1。'
assert [m.group(0) for m in proposed.finditer(example)]==['https://example.test/资料/a%EF%BC%8Cb.ts','https://example.test/b?q=a,b&x=1']
output=dict(pygments=pygments.__version__,lexer_source=str(Path(pygments.__file__).resolve()),sample=sample,synthetic_tokens=cases,recorded_body_hash=hashlib.sha256(body.encode()).hexdigest(),recorded_tokens=live,old_urls=old_values,expected_urls=values,search_text_after_removal=proposed.sub(' ',old),unrelated=example)
(e/'lex-and-url-proof.json').write_text(json.dumps(output,ensure_ascii=False,indent=2),encoding='utf8')
