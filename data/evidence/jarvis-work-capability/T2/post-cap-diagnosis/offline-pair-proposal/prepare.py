"""Offline materializer. Reads archived bodies and Git blobs, invokes no SDK/model/tool."""
from pathlib import Path
from urllib.parse import urlsplit
import ast, hashlib, io, json, re, subprocess, sys, tokenize

HERE = Path(__file__).resolve().parent
ROOT = Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent')
OLD = HERE.parents[1] / '20261102-b6ab85b/e02-round-1'
DONOR = Path(r'H:\UltimaAI\UltimaAgent\libs\base\openjarvis')
REV = '0eb7811df96cf139e6bd6d7fcc9b5cc4ff1418ff'
sys.path.insert(0, str(ROOT / 'src/brain'))
import work_research as wr  # pure projector and syntax predicates only
from pygments.lexers.javascript import JavascriptLexer, TypeScriptLexer
from pygments.token import Comment, Name

def compact(x):
    return json.dumps(x, ensure_ascii=False, separators=(',', ':'))

def save(name, value):
    (HERE / name).write_bytes(json.dumps(value, ensure_ascii=False, indent=2).encode())

def candidates(source, visible):
    body = source['body']
    suffix = Path(urlsplit(source['final_url']).path).suffix
    rows = body.splitlines()
    if suffix == '.py':
        for node in ast.walk(ast.parse(body)):
            if isinstance(node, ast.Raise):
                yield node.lineno, node.end_lineno, 'limitation', ''
            elif isinstance(node, (ast.Assign, ast.AnnAssign, ast.Expr, ast.Return)):
                call = node.value
                if isinstance(call, ast.Await):
                    call = call.value
                if isinstance(call, ast.Call):
                    sym = ast.unparse(call.func)
                    if re.fullmatch(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*', sym):
                        yield node.lineno, node.end_lineno, 'code', sym
                        if sym.split('.')[-1] in ('warning','warn'):
                            yield node.lineno, node.end_lineno, 'limitation', ''
        for t in tokenize.generate_tokens(io.StringIO(body).readline):
            if t.type == tokenize.COMMENT and re.search(r'\b(TODO|FIXME|unimplemented)\b', t.string,re.I):
                yield t.start[0],t.end[0],'limitation',''
    elif suffix in ('.ts','.js','.mjs','.cjs'):
        lexer = TypeScriptLexer() if suffix == '.ts' else JavascriptLexer()
        tokens = list(lexer.get_tokens_unprocessed(body))
        for n, (offset, family, value) in enumerate(tokens):
            first = body.count('\n', 0, offset) + 1
            if family in Comment and re.search(r'\b(TODO|FIXME|unimplemented)\b',value,re.I):
                yield first,first+value.count('\n'),'limitation',''
            if family not in Name or n+1 >= len(tokens) or tokens[n+1][2]!='(':
                continue
            start=n
            while start >= 2 and tokens[start-1][2]=='.' and re.fullmatch(r'[\w$]+',tokens[start-2][2]):
                start-=2
            sym=''.join(t[2] for t in tokens[start:n+1])
            for last in range(first,min(first+8,len(rows)+1)):
                if wr._js_support(body,first,last,'code',sym,suffix):
                    yield first,last,'code',sym
                    if sym.split('.')[-1] in ('warn','warning'):
                        yield first,last,'limitation',''
                    break
    else:
        chunk=[]
        for i,line in visible.items():
            if chunk and (not line.strip() or i!=chunk[-1]+1 or len(chunk)==4):
                yield chunk[0],chunk[-1],'documented',''
                chunk=[]
            if line.strip():
                chunk.append(i)
        if chunk:
            yield chunk[0],chunk[-1],'documented',''

def card_view(sources):
    result=[]
    for s in sources:
        vis=dict(wr._source_view(s,len(sources))['lines'])
        possible=sorted({c for c in candidates(s,vis) if c[1]-c[0]<8 and all(i in vis for i in range(c[0],c[1]+1))})
        # Keep negative witnesses first; then sample across the full visible extent.
        priority=sorted(c for c in possible if c[2]=='limitation')
        remaining=[c for c in possible if c not in priority]
        def spread(items):
            if len(items)<=2:return items
            buckets=[items[1:-1]]
            out=[items[0],items[-1]]
            while buckets:
                b=buckets.pop(0)
                if b:
                    mid=len(b)//2
                    out.append(b[mid])
                    buckets.extend((b[:mid],b[mid+1:]))
            return out
        view=dict(source_id=s['source_id'],identity=s['final_url'],cards=[],context_lines=[])
        accepted=[]
        for c in priority+spread(remaining):
            first,last,kind,symbol=c
            fact=dict(first_line=first,last_line=last,kind=kind,claim=symbol or 'witness')
            if symbol: fact['symbol']=symbol
            wr._fact_evidence(fact,s,vis)
            card=dict(id=f"{s['source_id']}.{possible.index(c)+1}",kind=kind,lines=[first,last])
            if symbol:card['symbol']=symbol
            trial=accepted+[card]
            line_ids=sorted({i for t in trial for i in range(t['lines'][0]-2,t['lines'][1]+3) if i in vis})
            updated=dict(view,cards=sorted(trial,key=lambda t:t['lines']),context_lines=[[i,vis[i]] for i in line_ids])
            if len(compact(updated))<=min(8000,(24000-len(sources)-1)//len(sources)):
                view=updated
                accepted=trial
        result.append(view)
    if len(compact(result))>24000:raise ValueError('card pack overflow')
    return result

def main():
    r=json.loads((OLD/'receipt.json').read_bytes())
    argv=json.loads((OLD/'argv.json').read_bytes())
    e02=r['available_sources']
    held=[]
    for i,name in enumerate(('file_utils.py','file_policy.py','signing.py'),1):
        path='src/openjarvis/security/'+name
        blob=subprocess.check_output(['git','-C',str(DONOR),'show',REV+':'+path])
        url=f'https://raw.githubusercontent.com/open-jarvis/OpenJarvis/{REV}/{path}'
        body=blob.decode()
        held.append(dict(source_id=f'S{i}',final_url=url,dedupe_url=url,text=body,body=body,
                         decoded_body_sha256=hashlib.sha256(blob).hexdigest(),content_type='text/plain',
                         read_call_id=f'git-blob:{REV}:{path}',request_id='heldout',session_id='heldout',task_id='heldout'))
    for name,query,sources in [('e02',argv['cli'][-1],e02),('heldout','根据这些已取得的 OpenJarvis 源码，整理文件安全写入、敏感路径判断和签名验证的行为与失败分支，带来源保存为 research.md。',held)]:
        for s in sources:
            if hashlib.sha256(s['body'].encode()).hexdigest()!=s['decoded_body_sha256']:raise ValueError('body hash')
        saved=dict(query=query,sources=sources,original=wr.source_pack(sources),handles=card_view(sources))
        save(name+'.json',saved)
        print(name, len(saved['original']), len(compact(saved['handles'])), [(s['source_id'],len(s['cards'])) for s in saved['handles']])
if __name__=='__main__':main()
