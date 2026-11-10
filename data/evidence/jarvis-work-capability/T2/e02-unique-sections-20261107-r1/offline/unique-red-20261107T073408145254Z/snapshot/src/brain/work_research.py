"""Bounded research collection/rendering around installed SDK tools, not an Agent."""
from dataclasses import dataclass
import ast
import hashlib
import io
import json
from pathlib import PurePosixPath
import re
import time
import tokenize
from urllib.parse import urlsplit, urlunsplit
import uuid


def canonical_url(value):
    from openjarvis.security.ssrf import check_ssrf
    if not isinstance(value,str) or not value or len(value)>2048:
        raise ValueError('Source URL must be a nonempty string <=2048 characters')
    p=urlsplit(value)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or p.fragment:
        raise ValueError('Source candidate must be a public HTTP(S) URL without credentials/fragment')
    error=check_ssrf(value)
    if error: raise ValueError(error)
    host=p.hostname.lower()
    if ':' in host: host='['+host+']'
    port=p.port
    if port not in (None,80 if p.scheme=='http' else 443): host+=':'+str(port)
    return urlunsplit((p.scheme.lower(),host,p.path or '/',p.query,''))


URL_PATTERN=re.compile(r'https?://[^\s<>"\x27，。；：！？、）】》」』”’]+')


def candidate_inputs(query,source_urls):
    if not isinstance(source_urls,list) or len(source_urls)>5:
        raise ValueError('source_urls must be a list of at most five candidate strings')
    raw=list(source_urls)+[m.group(0).rstrip('.,;:!?，。；：！？）)]}') for m in URL_PATTERN.finditer(query)]
    urls=[]
    for value in raw:
        normalized=canonical_url(value)
        if normalized not in urls: urls.append(normalized)
    if len(urls)>5: raise ValueError('At most five distinct source candidates are allowed')
    search_query=URL_PATTERN.sub(' ',query)
    search_query=' '.join(search_query.split())[:2000]
    if not search_query:
        search_query=' '.join(urlsplit(u).hostname+' '+urlsplit(u).path for u in urls)[:2000]
    if not search_query: raise ValueError('Research query is empty')
    return search_query,urls


@dataclass(frozen=True)
class ResearchCollection:
    catalogue_json: str
    trace_json: str
    attempts_json: str
    ignored_failure_ids: tuple[str,...]
    search_query: str


class ResearchCollectionError(ValueError):
    def __init__(self,message,trace,attempts,sources):
        super().__init__(message)
        self.trace=json.loads(json.dumps(trace))
        self.attempts=json.loads(json.dumps(attempts))
        self.sources=json.loads(json.dumps(sources))


def collect_research(query,source_urls,*,binding,ledger,capabilities):
    from openjarvis.core.registry import ToolRegistry
    from openjarvis.core.events import EventBus,EventType
    from openjarvis.core.types import ToolCall
    from openjarvis.tools._stubs import ToolExecutor
    search_query,candidates=candidate_inputs(query,source_urls)
    bus=EventBus()
    trace=[]; attempts=[]; sources=[]; ignored=[]
    deadline=time.monotonic()+120
    identities={k:getattr(binding,k) for k in ('request_id','session_id','task_id')}

    def fail(message):
        raise ResearchCollectionError(message,trace,attempts,sources)

    def invoke(name,params,optional):
        if time.monotonic()>=deadline: fail('Research prerequisite deadline reached before next read')
        sdk_id=str(uuid.uuid4())
        def event_record(event):
            trace.append(dict(phase='research.preflight',type=event.event_type.value,timestamp=event.timestamp,
                              data=json.loads(json.dumps(event.data)),sdk_call_id=sdk_id,**identities))
        kinds=(EventType.TOOL_CALL_START,EventType.TOOL_CALL_END,EventType.TOOL_TIMEOUT)
        for kind in kinds: bus.subscribe(kind,event_record)
        try:
            # Tool construction stays on the request-bound caller thread.
            executor=ToolExecutor([ToolRegistry.create(name)],bus=bus,agent_id=binding.task_id)
            result=executor.execute(ToolCall(id=sdk_id,name=name,arguments=json.dumps(params)))
        finally:
            for kind in kinds: bus.unsubscribe(kind,event_record)
        adapter_id=(result.metadata or {}).get('call_id')
        matching=[r for r in ledger.snapshot() if r.get('call_id')==adapter_id
                  and r.get('tool_name')==name and all(r.get(k)==v for k,v in identities.items())]
        timeout=any(e['sdk_call_id']==sdk_id and e['type']=='tool_timeout' for e in trace)
        record=matching[0] if len(matching)==1 else None
        attempt=dict(sdk_call_id=sdk_id,adapter_call_id=adapter_id,tool_name=name,optional=optional,
                     success=bool(result.success),deadline_monotonic=deadline,**identities)
        if not result.success:
            attempt['error']=result.content
            attempt['error_type']=record.get('error_type') if record else None
        attempts.append(attempt)
        if timeout: fail('SDK research read timed out; composition was not started')
        if record is None: fail('Research executor result has no exact request ledger linkage')
        if not result.success:
            if optional and record['success'] is False and record.get('error_type') in ('ValueError','OSError','ConnectionError','TimeoutError'):
                ignored.append(adapter_id)
                return None
            fail(('Mandatory research search failed: ' if not optional else 'Unexpected prerequisite adapter failure: ')+result.content)
        if not record.get('success'): fail('Research SDK/adapter result mismatch')
        return record['result']

    search=invoke('ultima_work_web_search',dict(query=search_query,max_results=5),False)
    if len(candidates)<3:
        for hint in search.get('results',[]):
            try: url=canonical_url(hint.get('url'))
            except (ValueError,TypeError): continue
            if url not in candidates: candidates.append(url)
            if len(candidates)==5: break
    for url in candidates:
        source=invoke('ultima_work_http_get',dict(url=url),True)
        if source is None: continue
        if hashlib.sha256(source['body'].encode('utf8')).hexdigest()!=source['decoded_body_sha256']:
            fail('Fetched body provenance hash mismatch')
        if any(s['dedupe_url']==source['dedupe_url'] or s['decoded_body_sha256']==source['decoded_body_sha256'] for s in sources):
            attempts[-1]['duplicate_source']=True
            continue
        source=dict(source,adapter_source_id=source['source_id'],source_id='S'+str(len(sources)+1),
                    read_call_id=attempts[-1]['adapter_call_id'],**identities)
        sources.append(source)
    if len(sources)<3: fail('Research needs at least three distinct fetched source URLs and bodies before composition')
    return ResearchCollection(json.dumps(sources,ensure_ascii=False),json.dumps(trace,ensure_ascii=False),
                              json.dumps(attempts,ensure_ascii=False),tuple(ignored),search_query)


def bound_sources(sources_json,binding=None):
    sources=json.loads(sources_json or '[]')
    if len(sources)<3: raise ValueError('No bound research source catalogue')
    if binding and any(any(s.get(k)!=getattr(binding,k) for k in ('request_id','session_id','task_id')) for s in sources):
        raise ValueError('Cross-request research catalogue')
    if len({s['source_id'] for s in sources})!=len(sources): raise ValueError('Duplicate source identities')
    return {s['source_id']:s for s in sources}


def _text(value,limit):
    if not isinstance(value,str) or not value.strip() or len(value)>limit or any(ord(c)<32 for c in value):
        raise ValueError('Report text must be a nonempty bounded single-line paragraph')
    if re.search(r'\b(?:[a-z][a-z0-9+.-]*://|www\.)|\]\s*\(|<[^>]+>',value,re.I):
        raise ValueError('Report text cannot supply extra URLs, Markdown links or HTML citations')
    return value


def _escape(text):
    return re.sub(r'([\\`*_{}\[\]<>#])',r'\\\1',text)


@dataclass(frozen=True)
class RenderedReport:
    content: str
    cited_source_ids: tuple[str,...]
    evidence: tuple[dict,...]


def _compact(value):
    return json.dumps(value, ensure_ascii=False, separators=(',', ':'))


def _source_view(source, count):
    lines = list(enumerate(source['text'].splitlines(), 1))
    view = dict(source_id=source['source_id'], lines=lines, omitted=False)
    budget = min(8000, (24000 - count - 1) // count)
    if len(_compact(view)) <= budget:
        return view
    view.update(lines=[], omitted=True)
    half = (budget - len(_compact(view))) // 2

    def take(rows):
        used = 0
        selected = []
        for row in rows:
            used += len(_compact(row)) + 1
            if used > half:
                break
            selected.append(row)
        return selected

    view['lines'] = take(lines) + list(reversed(take(reversed(lines))))
    return view


def source_pack(sources):
    return _compact([_source_view(source, len(sources)) for source in sources])


def _python_support(body, first, last, kind, symbol, witnesses=None):
    return any(first <= a <= b <= last and k == kind and op == (symbol or '')
               for a, b, k, op in (_python_witnesses(body) if witnesses is None else witnesses))


def _python_witnesses(body):
    for token in tokenize.generate_tokens(io.StringIO(body).readline):
        if token.type == tokenize.COMMENT and re.search(r'\b(?:TODO|FIXME|unimplemented)\b', token.string, re.I):
            yield token.start[0], token.end[0], 'limitation', ''
    for node in ast.walk(ast.parse(body)):
        if isinstance(node, ast.Raise):
            yield node.lineno, node.end_lineno, 'limitation', ''
        if isinstance(node, (ast.Assign, ast.AnnAssign, ast.Expr, ast.Return)):
            call = node.value
            if isinstance(call, ast.Await):
                call = call.value
            if isinstance(call, ast.Call):
                op = ast.unparse(call.func)
                if len(op) <= 200 and re.fullmatch(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*', op):
                    yield node.lineno, node.end_lineno, 'code', op
                if op.split('.')[-1] in ('warn', 'warning'):
                    yield node.lineno, node.end_lineno, 'limitation', ''


def _js_tokens(body, suffix):
    from pygments.lexers.javascript import JavascriptLexer, TypeScriptLexer
    from pygments.token import Comment
    lexer = TypeScriptLexer() if suffix == '.ts' else JavascriptLexer()
    line = 1
    rows = []
    for _, family, value in lexer.get_tokens_unprocessed(body):
        end = line + value.count('\n')
        if value.strip():
            rows.append((line, end, family, value))
        line = end
    return rows


def _js_support(body, first, last, kind, symbol, suffix, rows=None):
    from bisect import bisect_left
    from pygments.token import Comment, Error, Name, String
    rows = _js_tokens(body, suffix) if rows is None else rows
    start = bisect_left(rows, first, key=lambda row: row[1])
    previous = following = None
    for i in range(start-1, -1, -1):
        if rows[i][2] not in Comment:
            previous = rows[i][3]
            break
    tokens = []
    for i in range(start, len(rows)):
        line, end, family, value = rows[i]
        if line > last:
            if family not in Comment:
                following = value
                break
            continue
        if family in Comment:
            if (kind == 'limitation' and symbol is None and first <= line and end <= last
                    and re.search(r'\b(?:TODO|FIXME|unimplemented)\b', value, re.I)):
                return True
        elif family in Error or line < first or end > last:
            return False
        else:
            tokens.append(('@literal' if family in String else value, family))
    # Match only a single complete call statement. Token offsets and classes
    # come from the full source, so text in literals cannot become a callee.
    words = [v for v, _ in tokens]
    if previous not in (None, ';', '{', '}'):
        return False
    throwing = kind == 'limitation' and words[:2] == ['throw','new']
    if throwing:
        words = words[1:]
        tokens = tokens[1:]
    header = re.fullmatch(
        r'(?:(?:return |(?:(?:const|let|var) )?(?:[\w$]+ \. )*[\w$]+ = ))?'
        r'(?:await )?(?:new )?(?P<callee>[\w$]+(?: \. [\w$]+)*)',
        ' '.join(words[:words.index('(')]) if '(' in words else '')
    if not header:
        return False
    opening = words.index('(')
    callee = header['callee'].replace(' ', '')
    # An unqualified bare expression can also be a TS interface signature.
    if suffix == '.ts' and '.' not in callee and opening == 1:
        return False
    if tokens[opening-1][1] not in Name:
        return False
    stack = []
    for i, word in enumerate(words[opening:], opening):
        if word in ('(', '[', '{'):
            stack.append(word)
        elif word in (')', ']', '}'):
            if not stack or stack.pop() != {')':'(', ']':'[', '}':'{'}[word]:
                return False
            if not stack:
                if words[i+1:] not in ([], [';']):
                    return False
                # Without an explicit terminator the next significant token
                # may open a method body or extend the operand (e.g. .then).
                if i == len(words)-1 and following not in (
                        None, ';', '}', 'return', 'throw', 'const', 'let', 'var', 'if'):
                    return False
                if kind == 'code':
                    return callee == symbol
                return (symbol is None or callee == symbol) and (throwing or callee.split('.')[-1] in ('warn','warning'))
    return False


def _fact_evidence(fact, source, visible, syntax=None):
    if not isinstance(fact, dict):
        raise ValueError('A fact needs a claim, evidence kind and visible line range')
    kind = fact.get('kind')
    fields = {'claim','kind','first_line','last_line'}
    if kind == 'code':
        fields.add('symbol')
    if set(fact) != fields or kind not in ('documented','code','limitation'):
        raise ValueError('Invalid fact fields or kind')
    claim = _text(fact['claim'], 2000)
    first, last = fact['first_line'], fact['last_line']
    if (type(first) is not int or type(last) is not int or not 1 <= first <= last < first+8
            or any(i not in visible for i in range(first,last+1))):
        raise ValueError('Invalid or omitted evidence lines')
    excerpt = '\n'.join(visible[i] for i in range(first,last+1))
    if not excerpt.strip():
        raise ValueError('Empty evidence span')
    suffix = PurePosixPath(urlsplit(source['final_url']).path).suffix.lower()
    if kind == 'documented':
        if suffix not in ('','.md','.rst','.txt','.htm','.html','.adoc'):
            raise ValueError('Code cannot serve as documentation of implemented behavior')
    else:
        symbol = fact.get('symbol')
        if kind == 'code' and (not isinstance(symbol,str) or len(symbol)>200 or
                not re.fullmatch(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*',symbol) or
                not re.search(r'(?<![A-Za-z0-9_$.])'+re.escape(symbol)+r'(?![A-Za-z0-9_$]|\.[A-Za-z_$])',claim)):
            raise ValueError('A code claim must name its exact operation')
        body = source['body']
        # splitlines(), the AST and the lexer agree on LF/CRLF coordinates.
        # Other separators or extracted HTML cannot supply raw code positions.
        if (source['text'] != body or 'html' in source.get('content_type', '')
                or re.search(r'\r(?!\n)|[\v\f\x1c-\x1e\x85\u2028\u2029]', body)):
            raise ValueError('Unsupported code projection or line separator')
        if suffix == '.py':
            supported = _python_support(body,first,last,kind,symbol,syntax)
        elif suffix in ('.js','.ts','.mjs','.cjs'):
            supported = _js_support(body,first,last,kind,symbol,suffix,syntax)
        else:
            supported = False
        if not supported:
            raise ValueError('Selected code span does not witness this operation or limitation')
    keys = ('source_id','final_url','decoded_body_sha256','read_call_id','request_id','session_id','task_id')
    return dict(fact, text=excerpt, **{k:source[k] for k in keys})


def _js_statement_anchor(body, callee_line, operation, suffix, rows, visible):
    # A prefix (assignment, return/await, throw/new) may precede the callee.
    # Start nearest the callee and stop at the first complete visible statement.
    for first in range(callee_line,max(0,callee_line-8),-1):
        if first not in visible:
            break
        for last in range(callee_line,first+8):
            if last not in visible:
                break
            if _js_support(body,first,last,'code',operation,suffix,rows):
                return first,last,'code',operation
            if _js_support(body,first,last,'limitation',operation,suffix,rows):
                return first,last,'limitation',''
    return None


def _anchors(source, visible, syntax):
    suffix = PurePosixPath(urlsplit(source['final_url']).path).suffix.lower()
    body = source['body']
    if suffix in ('', '.md', '.rst', '.txt', '.htm', '.html', '.adoc'):
        chunk = []
        for line, value in visible.items():
            if chunk and (not value.strip() or line != chunk[-1]+1 or len(chunk) == 4):
                yield chunk[0], chunk[-1], 'documented', ''
                chunk = []
            if value.strip():
                chunk.append(line)
        if chunk:
            yield chunk[0], chunk[-1], 'documented', ''
    elif (source['text'] == body and 'html' not in source.get('content_type', '')
          and not re.search(r'\r(?!\n)|[\v\f\x1c-\x1e\x85\u2028\u2029]', body)):
        if suffix == '.py':
            yield from syntax
        elif suffix in ('.ts', '.js', '.mjs', '.cjs'):
            from pygments.token import Comment, Name
            rows = syntax
            for idx, (first, end, family, value) in enumerate(rows):
                if first not in visible:
                    continue
                if family in Comment and re.search(r'\b(?:TODO|FIXME|unimplemented)\b',value,re.I):
                    yield first, end, 'limitation', ''
                if family not in Name or idx+1 == len(rows) or rows[idx+1][3] != '(':
                    continue
                begin = idx
                while begin >= 2 and rows[begin-1][3] == '.' and rows[begin-2][2] in Name:
                    begin -= 2
                op = ''.join(row[3] for row in rows[begin:idx+1])
                if len(op) > 200 or not re.fullmatch(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*', op):
                    continue
                anchor = _js_statement_anchor(body,first,op,suffix,rows,visible)
                if anchor:
                    yield anchor
                    if anchor[2]=='code' and op.split('.')[-1] in ('warn','warning'):
                        yield anchor[0],anchor[1],'limitation',''


def reference_cards(catalogue):
    sources = bound_sources(catalogue)
    table = {}
    for sid, source in sources.items():
        if hashlib.sha256(source['body'].encode()).hexdigest() != source['decoded_body_sha256']:
            raise ValueError('Source body identity mismatch')
        visible = dict(_source_view(source,len(sources))['lines'])
        suffix = PurePosixPath(urlsplit(source['final_url']).path).suffix.lower()
        syntax = None
        if suffix == '.py':
            try:
                syntax = list(_python_witnesses(source['body']))
            except (SyntaxError, ValueError, tokenize.TokenError):
                syntax = []
        elif suffix in ('.ts','.js','.mjs','.cjs'):
            syntax = _js_tokens(source['body'],suffix)
        anchors = sorted({a for a in _anchors(source,visible,syntax) if a[1]-a[0]<8
                          and all(i in visible for i in range(a[0],a[1]+1))})
        identity = {k:source[k] for k in ('source_id','final_url','decoded_body_sha256','read_call_id',
                                          'request_id','session_id','task_id')}
        prefix = hashlib.sha256(_compact(identity).encode()).hexdigest()[:12]
        numbered = list(enumerate(anchors, 1))
        selected = []
        for limitations in (True, False):
            group = [row for row in numbered if (row[1][2]=='limitation') == limitations]
            n = min(len(group), 48-len(selected))
            selected.extend(group[round(i*(len(group)-1)/max(n-1,1))] for i in range(n))
        for number, (first,last,kind,op) in sorted(selected):
            # Extend only through visible neighboring lines, never across the projection gap.
            left, right = first,last
            padding = 7-(last-first)
            for _ in range(padding//2):
                if left-1 not in visible: break
                left -= 1
            for _ in range(padding-padding//2):
                if right+1 not in visible: break
                right += 1
            witness = dict(kind=kind,claim=op or 'witness',first_line=first,last_line=last)
            if kind == 'code':
                witness['symbol'] = op
            _fact_evidence(witness,source,visible,syntax)
            key = f'{prefix}.{number}'
            table[key] = dict(identity,kind=kind,symbol=op,first_line=first,last_line=last,
                              citation_first=left,citation_last=right)
    return table


def reference_schema(table):
    def obj(**props):
        return dict(type='object',additionalProperties=False,properties=props,required=list(props))
    def text(limit):
        return dict(type='string',minLength=1,maxLength=limit)
    def array(items,low,high):
        return dict(type='array',items=items,minItems=low,maxItems=high)
    alternatives = []
    for sid in dict.fromkeys(card['source_id'] for card in table.values()):
        ids = [key for key,card in table.items() if card['source_id']==sid]
        fact = obj(claim=text(2000),evidence_id=dict(type='string',enum=ids))
        alternatives.append(obj(source_id=dict(type='string',enum=[sid]),heading=text(200),facts=array(fact,1,6)))
    return obj(path=text(2048),title=text(200),sections=array(dict(anyOf=alternatives),3,5))


def resolve_references(payload, table, catalogue):
    from jsonschema import Draft7Validator
    Draft7Validator(reference_schema(table)).validate(payload)
    resolved = json.loads(_compact(payload))
    bindings = []
    sources = bound_sources(catalogue)
    for section in resolved['sections']:
        sid = section['source_id']
        visible = dict(_source_view(sources[sid],len(sources))['lines'])
        for fact in section['facts']:
            key = fact.pop('evidence_id')
            card = table[key]
            if card['source_id'] != sid:
                raise ValueError('Foreign reference')
            fact.update(kind=card['kind'],first_line=card['first_line'],last_line=card['last_line'])
            if card['kind']=='code':
                fact['symbol'] = card['symbol']
            _fact_evidence(fact,sources[sid],visible)
            bindings.append(dict(card,evidence_id=key))
    return resolved, bindings


def render_research_report(payload,sources_json,*,bindings=None):
    if not isinstance(payload,dict) or set(payload)!={'path','title','sections'}:
        raise ValueError('Report requires only path, title and sections')
    sources=bound_sources(sources_json)
    title=_text(payload['title'],200)
    sections=payload['sections']
    if not isinstance(sections,list) or not 3<=len(sections)<=5:
        raise ValueError('Report needs three to five source sections')
    lines=['# '+_escape(title),'']; cited=[]
    evidence = []
    for section in sections:
        if not isinstance(section,dict) or set(section)!={'source_id','heading','facts'}:
            raise ValueError('A source section requires only source_id, heading and facts')
        source_id=section['source_id']
        if not isinstance(source_id,str) or source_id not in sources or source_id in cited:
            raise ValueError('Unknown, duplicate or unbound source ID')
        facts=section['facts']
        if not isinstance(facts,list) or not 1<=len(facts)<=6: raise ValueError('Source section requires one to six facts')
        lines+=['## '+_escape(_text(section['heading'],200)),sources[source_id]['final_url'],'']
        visible = dict(_source_view(sources[source_id],len(sources))['lines'])
        for fact in facts:
            support = _fact_evidence(fact, sources[source_id], visible)
            citation = f"L{support['first_line']}–L{support['last_line']}"
            if bindings is not None:
                card = bindings[len(evidence)]
                left, right = card['citation_first'], card['citation_last']
                support.update(citation_first=left,citation_last=right,
                               citation_text='\n'.join(visible[i] for i in range(left,right+1)))
                citation = f'L{left}–L{right}，依据 {citation}'
            evidence.append(support)
            label = {'documented':'文档说明','code':'代码观察','limitation':'该处标注'}[support['kind']]
            lines.append(f"- {label}（{citation}）"+_escape(support['claim']))
        lines.append(''); cited.append(source_id)
    if len({sources[s]['dedupe_url'] for s in cited})<3 or len({sources[s]['decoded_body_sha256'] for s in cited})<3:
        raise ValueError('Report requires three distinct cited source URL/body identities')
    return RenderedReport('\n'.join(lines),tuple(cited),tuple(evidence))


def prepare_navigation(collection,binding,scanners,*,get_records_json:bytes,deadline:float):
    from .work_navigation import prepare_navigation as prepare
    return prepare(collection,binding,scanners,get_records_json=get_records_json,deadline=deadline)


def resolve_v3(submitted,issued_snapshot,collection):
    from .work_navigation import resolve_v3 as resolve
    return resolve(submitted,issued_snapshot,collection)


def checked_native_identity(version_bytes,tags_bytes,manifest_digest):
    from .agent_server import _strict_json,_RESEARCH_MODEL,_RESEARCH_DIGEST
    if not all(type(b) is bytes and 0<len(b)<=32768 for b in (version_bytes,tags_bytes)):
        raise ValueError('Invalid metadata identity bytes')
    version=_strict_json(version_bytes.decode()); tags=_strict_json(tags_bytes.decode())
    if version!={'version':'0.32.15'} or set(tags)!={'models'} or not isinstance(tags['models'],list):
        raise ValueError('Unsupported native metadata identity')
    matches=[]
    for model in tags['models']:
        if (not isinstance(model,dict) or set(model)-{'name','model','modified_at','size','digest','details','capabilities'}
                or not all(type(model.get(k)) is str for k in ('name','digest'))
                or ('size' in model and (type(model['size']) is not int or not 0<=model['size']<2**63))
                or ('capabilities' in model and (type(model['capabilities']) is not list
                    or not all(type(value) is str for value in model['capabilities'])))
                or ('model' in model and model['model']!=model['name'])):
            raise ValueError('Invalid native model metadata')
        if model['name'] in (_RESEARCH_MODEL,_RESEARCH_MODEL+':latest'): matches.append(model['digest'])
    if matches!=[_RESEARCH_DIGEST] or manifest_digest!=_RESEARCH_DIGEST:
        raise ValueError('Unexpected research manifest identity')
    return version,tags


def checked_native_response(raw,max_tokens):
    from .agent_server import _RESEARCH_MODEL
    allowed={'model','created_at','done','done_reason','total_duration','load_duration','prompt_eval_count',
        'prompt_eval_duration','eval_count','eval_duration','message'}
    message=raw.get('message'); counts=raw.get('prompt_eval_count'),raw.get('eval_count')
    if (set(raw)-allowed or raw.get('model') not in (_RESEARCH_MODEL,_RESEARCH_MODEL+':latest') or raw.get('done') is not True
            or raw.get('done_reason')!='stop' or not isinstance(message,dict) or set(message)!={'role','content'}
            or message['role']!='assistant' or type(message['content']) is not str or not message['content'].strip()
            or any(type(n) is not int or n<1 for n in counts) or counts[1]>max_tokens or sum(counts)>16384
            or any(type(raw[k]) is not int or not 0<=raw[k]<2**63 for k in ('total_duration','load_duration','prompt_eval_duration','eval_duration') if k in raw)
            or ('created_at' in raw and type(raw['created_at']) is not str)):
        raise ValueError('Invalid native research response')


def _verify_runtime_order(packet,reads,written,require_ack,runtime_inputs):
    from math import isfinite
    import uuid
    from .work_navigation import canonical_v3
    if packet['clock_domain']!='work_tools.monotonic;ledger-sequence-v1': raise ValueError('Runtime clock domain drift')
    timeline=packet['timeline']; cursor=0; previous=None
    def take(kind,**fields):
        nonlocal cursor,previous
        if cursor>=len(timeline): raise ValueError('Missing runtime admission order')
        node=timeline[cursor]; cursor+=1
        if (set(node)!={'order','kind','at','deadline',*fields} or node['order']!=cursor or node['kind']!=kind
                or any(node[k]!=v for k,v in fields.items()) or node['deadline']!=runtime_inputs.deadline):
            raise ValueError('Runtime admission order drift')
        try:
            if type(node['at']) is not str or type(node['deadline']) is not str: raise ValueError('Clock representation')
            now=float(node['at']);deadline=float(node['deadline']);remaining=deadline-now
        except (ValueError,TypeError,OverflowError): raise ValueError('Invalid runtime clock') from None
        if not all(isfinite(n) for n in (now,deadline,remaining)) or (previous is not None and now<previous):
            raise ValueError('Runtime monotonic clock drift')
        previous=now
        if remaining<=0: raise ValueError('Runtime deadline exceeded')
        return node,remaining
    for index,wire in enumerate(packet['wires']):
        ack=index==len(reads)+1
        take('generation',generation=index+1)
        for receipt_index in range(index*3,index*3+3):
            _,remaining=take('send',generation=index+1,receipt_index=receipt_index)
            if not ack and remaining<=55: raise ValueError('Runtime send reserve exhausted')
            receipt=packet['transport']['receipts'][receipt_index]
            budget=remaining if ack else remaining-55
            # Recorded repr strings round-trip the live binary64 samples. Keep
            # its subtraction order so boundary timeouts have identical caps.
            base=min(25,budget); read=min(25 if ack else 180,budget)
            if receipt['kind']=='metadata': read=min(25,read)
            timeout=json.loads(receipt['timeout_json'])
            def admitted(value,limit):
                try: return type(value) in (int,float) and isfinite(value) and 0<value<=limit
                except OverflowError: return False
            if (receipt['send_reserved'] is not True or receipt['admission_error'] is not None
                    or set(timeout)!={'connect','read','write','pool'}
                    or any(not admitted(timeout[k],limit) for k,limit in
                        (('connect',base),('read',read),('write',base),('pool',base)))):
                raise ValueError('Runtime final timeout admission drift')
            take('return',generation=index+1,receipt_index=receipt_index)
        _,remaining=take('secured',generation=index+1)
        if not ack and remaining<55: raise ValueError('Runtime secured reserve exhausted')
        if index and index<=len(reads): take('promote',seq=index,wire_hash=reads[index-1]['wire_sha256'])
        if ack: continue
        action=wire['secured_envelope']; seq=index+1
        take('expect',seq=seq,name=action['action'],args_hash=hashlib.sha256(canonical_v3(action['action_input'])).hexdigest())
        take('sdk_start',seq=seq,event_index=index*2)
        if index<len(reads): key=reads[index]['key']
        elif written: key=packet['execution']['intent']
        else:
            if cursor>=len(timeline): raise ValueError('Missing writer claim')
            key=timeline[cursor]
        for field in ('dispatch_uuid','adapter_uuid'):
            try:
                if str(uuid.UUID(key[field]))!=key[field]: raise ValueError('Invalid claim UUID')
            except (TypeError,KeyError): raise ValueError('Invalid claim UUID') from None
        take('claim',seq=seq,dispatch_uuid=key['dispatch_uuid'],adapter_uuid=key['adapter_uuid'])
        if index<len(reads): take('sdk_end',seq=seq,event_index=index*2+1)
        else:
            take('freeze',seq=seq)
            if written:
                _,remaining=take('intent',seq=seq,file_call_id=key['file_call_id'])
                if remaining<55: raise ValueError('Runtime intent reserve exhausted')
                take('file_end',file_call_id=key['file_call_id'])
                take('sdk_end',seq=seq,event_index=index*2+1)
    if cursor!=len(timeline): raise ValueError('Unexpected runtime terminal order')


def verify_runtime_packet(binding, snapshot, collection, raw, *, require_ack=False,runtime_inputs=None):
    """Reconstruct native entities, history and read/event links independently."""
    from .work_navigation import canonical_v3,v3_writer_schema,v3_phase_writer_schema
    from .work_tools import WorkInspectTool,WorkResearchWriteTool
    from openjarvis.tools._stubs import ToolSpec,build_tool_descriptions
    from types import SimpleNamespace
    from .agent_server import _strict_json,_research_sampler_schema,_RESEARCH_MODEL,MAINBRAIN_SYSTEM_PROMPT
    from openjarvis.agents.native_react import REACT_SYSTEM_PROMPT
    from jsonschema import Draft7Validator
    from openjarvis.security.scanner import SecretScanner,PIIScanner
    from .work_navigation import make_scan_policy
    sealed_policy=json.loads(snapshot.replay_json)['policy']
    factories={c.__module__+'.'+c.__qualname__:c for c in (SecretScanner,PIIScanner)}
    policy=make_scan_policy(tuple(factories[d['name']]() for d in sealed_policy['scanners']),sealed_policy['mode'])
    if json.loads(policy.policy_json)!=sealed_policy: raise ValueError('Runtime scanner policy drift')
    def scan_strings(value):
        if isinstance(value,str):
            if any(not s.scan(value).clean for s in policy.scanners): raise ValueError('Unsafe native evidence string')
        elif isinstance(value,list):
            for child in value: scan_strings(child)
        elif isinstance(value,dict):
            for key,child in value.items(): scan_strings(key);scan_strings(child)
    if type(raw) is not bytes or not raw: raise ValueError('Nonempty immutable runtime bytes required')
    packet=json.loads(raw)
    digest=lambda value:hashlib.sha256(value).hexdigest()
    if (runtime_inputs is None or packet['prompt']!=runtime_inputs.prompt or runtime_inputs.binding_key!=snapshot.binding_key
            or runtime_inputs.root!=str(binding.root)):
        raise ValueError('Runtime independently frozen input drift')
    if (canonical_v3(packet)!=raw or packet['v']!=3 or packet['binding']!=list(snapshot.binding_key)
            or tuple(getattr(binding,k) for k in ('request_id','session_id','task_id'))!=snapshot.binding_key
            or packet['nonce']!=snapshot.nonce or packet['issued_manifest']!=snapshot.manifest_sha256
            or packet['views_sha256']!=digest(snapshot.views_json)):
        raise ValueError('Runtime snapshot linkage drift')
    original=packet['system_original']
    specs=[ToolSpec(name=WorkInspectTool.tool_id,description=WorkInspectTool.description,parameters=WorkInspectTool.parameters,category='work',timeout_seconds=5),
        ToolSpec(name=WorkResearchWriteTool.tool_id,description=WorkResearchWriteTool.description,parameters=v3_writer_schema(),category='work',timeout_seconds=30,required_capabilities=['file:write'])]
    expected_original=(REACT_SYSTEM_PROMPT+'\n\n'+MAINBRAIN_SYSTEM_PROMPT).format(skill_examples='',tool_descriptions=build_tool_descriptions([SimpleNamespace(spec=s) for s in specs]))
    prefix=REACT_SYSTEM_PROMPT.split('# Using Skills',1)[0]
    if (original!=expected_original or original.count(prefix)!=1 or not original.endswith(MAINBRAIN_SYSTEM_PROMPT)
            or any(name not in original for name in ('ultima_work_research_inspect','ultima_work_research_write'))):
        raise ValueError('Runtime SDK policy drift')
    replacement=('Return exactly one JSON object matching the phase schema. Use action and object action_input '
        'for one permitted SDK tool, or final_answer for refusal or the authorized final acknowledgement. '
        'Write prose style applies inside user-facing text only.\n\n')
    replaced=original.replace(prefix,replacement,1)
    events=[_strict_json(e) for e in packet['events']]
    starts=[e['data'] for e in events if e['type']=='tool_call_start']
    ends=[e['data'] for e in events if e['type']=='tool_call_end']
    reads=json.loads(snapshot.replay_json)['reads']
    wires=packet['wires']
    if not len(reads)+1<=len(wires)<=8: raise ValueError('Runtime generation count')
    written=packet['execution']['intent'] is not None
    if len(starts)!=len(reads)+1 or len(ends)!=len(reads)+int(written):
        raise ValueError('Runtime event count')
    expected_types=['tool_call_start','tool_call_end']*len(reads)+['tool_call_start']+(['tool_call_end'] if written else [])
    if [e['type'] for e in events]!=expected_types: raise ValueError('Runtime ordered transcript drift')
    submitted_writer=wires[len(reads)]['secured_envelope']['action_input']
    if starts[-1]!=dict(tool='ultima_work_research_write',agent='native_react',arguments=submitted_writer):
        raise ValueError('Runtime writer START identity drift')
    _verify_runtime_order(packet,reads,written,require_ack,runtime_inputs)
    prewrite=packet.get('prewrite_packet')
    if prewrite is not None:
        if type(prewrite) is not str or digest(prewrite.encode())!=packet['prewrite_sha256']:
            raise ValueError('Runtime sealed prewrite hash drift')
        if json.loads(prewrite).get('prewrite_packet') is not None: raise ValueError('Nested prewrite packet')
        prefix_packet=verify_runtime_packet(binding,snapshot,collection,prewrite.encode(),runtime_inputs=runtime_inputs)
        if prefix_packet.get('prewrite_packet') is not None or prefix_packet['execution']!=dict(intent=None,files=[],effects=[]):
            raise ValueError('Runtime invalid prewrite prefix')
        for key in ('v','binding','nonce','issued_manifest','views_sha256','prompt','system_original','clock_domain'):
            if packet[key]!=prefix_packet[key]: raise ValueError('Runtime prewrite binding drift')
        for key in ('wires','events','timeline'):
            if packet[key][:len(prefix_packet[key])]!=prefix_packet[key]: raise ValueError('Runtime prewrite transcript drift')
        receipts_prefix=prefix_packet['transport']['receipts']
        if packet['transport']['receipts'][:len(receipts_prefix)]!=receipts_prefix: raise ValueError('Runtime prewrite sends drift')
    elif written or packet.get('prewrite_sha256') is not None: raise ValueError('Missing sealed prewrite packet')
    for index,read in enumerate(reads):
        start=starts[index]; end=ends[index]; key=read['key']
        args=dict(source_id=read['source_id'],start_line=read['start'])
        metadata=dict(seq=key['seq'],generation=key['generation'],dispatch_uuid=key['dispatch_uuid'],
            adapter_uuid=key['adapter_uuid'],binding=list(snapshot.binding_key),arguments=args)
        if (start!=dict(tool='ultima_work_research_inspect',agent='native_react',arguments=args)
                or end.get('tool')!=start['tool'] or end.get('agent')!='native_react' or end.get('success') is not True
                or end.get('metadata')!=metadata or end.get('result')!=canonical_v3(read['wire']).decode()):
            raise ValueError('Runtime read dispatch linkage drift')
        if read['wire_sha256']!=digest(end['result'].encode()): raise ValueError('Runtime read bytes drift')
    previous=None
    transport=packet['transport']; receipts=transport['receipts']
    if (transport['generations']!=len(wires) or transport['gets']!=2*len(wires) or transport['posts']!=len(wires)
            or transport['completed']!=len(wires) or len(receipts)!=3*len(wires)
            or transport['post_bytes']!=sum(len(w['entity'].encode()) for w in wires) or transport['post_bytes']>393216):
        raise ValueError('Runtime transport reservations drift')
    for kind,cap in (('metadata',32768),('chat',65536)):
        group=[r for r in receipts if r['kind']==kind]
        if (transport['admitted'][kind]!=sum(r['admitted'] for r in group) or transport['admitted'][kind]>524288
                or any(r['error'] is not None or not 200<=r['status']<300 or r['admitted']>cap
                    or r['admitted']!=r['retained'] or r['inspected']!=r['admitted']
                    or (r['downloaded'] is not None and r['downloaded']<r['admitted']) for r in group)):
            raise ValueError('Runtime response accounting drift')
    for index,wire in enumerate(wires):
        entity=wire['entity'].encode(); request=_strict_json(wire['entity'])
        if canonical_v3(request)!=entity or wire['generation']!=index+1: raise ValueError('Runtime entity drift')
        if wire['hashes']!={k:digest(v) for k,v in dict(messages=canonical_v3(wire['secured_messages']),
                strict=canonical_v3(wire['strict_schema']),sampler=canonical_v3(wire['sampler_schema']),entity=entity).items()}:
            raise ValueError('Runtime four-hash drift')
        if (request['messages']!=wire['secured_messages'] or request['format']!=_research_sampler_schema(wire['strict_schema'])
                or request['format']!=wire['sampler_schema'] or request['model']!=_RESEARCH_MODEL
                or any(request.get(k) is not False for k in ('think','stream','truncate','shift')) or request.get('tools')!=[]
                or request['options']['num_ctx']!=16384 or request['options']['temperature']!=0
                or set(request)!={'model','messages','format','tools','think','stream','truncate','shift','options'}):
            raise ValueError('Runtime native policy drift')
        messages=request['messages']
        if any(set(m)!={'role','content'} for m in messages): raise ValueError('Runtime optional message field drift')
        if (not messages[0]['content'].startswith(replaced+'\n\n') or messages[0]['role']!='system'
                or messages[1]!=dict(role='user',content=packet['prompt'])):
            raise ValueError('Runtime system or query drift')
        if previous is None:
            if len(messages)!=2: raise ValueError('Unexpected initial history')
        else:
            expected=[messages[0],*previous['secured_messages'][1:],dict(role='assistant',content=previous['raw']['message']['content']),
                dict(role='user',content='Observation: '+ends[index-1]['result'])]
            if messages!=expected: raise ValueError('Runtime observation history drift')
        outer=wire['raw']; envelope=_strict_json(outer['message']['content'])
        response=wire['raw_response'].encode()
        chunk=receipts[index*3:index*3+3]
        identity=wire['identity']
        version,tags=checked_native_identity(identity['version_response'].encode(),identity['tags_response'].encode(),identity['local_manifest_sha256'])
        scan_strings(version);scan_strings(tags);scan_strings(outer)
        for receipt,body in zip(chunk[:2],(identity['version_response'],identity['tags_response'])):
            if (receipt['response_sha256']!=digest(body.encode()) or receipt['admitted']!=len(body.encode())
                    or receipt['entity_bytes']!=0 or receipt['entity_sha256']!=digest(b'')):
                raise ValueError('Runtime metadata response hash drift')
        if ([(r['method'],r['path'],r['kind']) for r in chunk]!=[('GET','/api/version','metadata'),('GET','/api/tags','metadata'),('POST','/api/chat','chat')]
                or _strict_json(wire['raw_response'])!=outer or chunk[-1]['response_sha256']!=digest(response)
                or chunk[-1]['admitted']!=len(response) or chunk[-1]['entity_sha256']!=digest(entity)
                or chunk[-1]['entity_bytes']!=len(entity)):
            raise ValueError('Runtime raw response or send receipt drift')
        if envelope!=wire['raw_envelope'] or envelope!=wire['secured_envelope']:
            raise ValueError('Runtime secured envelope drift')
        scan_strings(envelope)
        if isinstance(envelope,dict) and isinstance(envelope.get('final_answer'),str) and not envelope['final_answer'].strip():
            raise ValueError('Empty research final answer')
        Draft7Validator(wire['strict_schema']).validate(envelope)
        final=dict(type='object',additionalProperties=False,required=['final_answer'],
            properties=dict(final_answer=dict(type='string',minLength=1,maxLength=1000)))
        ack=index==len(reads)+1
        allowed=[]
        def action(name,params):
            return dict(type='object',additionalProperties=False,required=['action','action_input'],properties=dict(action=dict(enum=[name]),action_input=params))
        visible=reads[:index]
        eligible=len({r['source_id'] for r in visible if r['wire']['cards']})>=3
        report_schema=v3_phase_writer_schema(tuple(
            (r['source_id'],canonical_v3(r['wire']['cards'])) for r in visible)) if eligible else v3_writer_schema()
        if not ack:
            if index<6: allowed.append(action('ultima_work_research_inspect',WorkInspectTool.parameters))
            if eligible: allowed.append(action('ultima_work_research_write',report_schema))
        from .work_navigation import v3_research_envelope
        expected_schema=final if ack else v3_research_envelope([*allowed,final])
        output_cap=256 if ack or not eligible else 2048
        if (wire['strict_schema']!=expected_schema or type(request['options']['num_predict']) is not int
                or not 0<request['options']['num_predict']<=output_cap):
            raise ValueError('Runtime phase schema or output budget drift')
        if (type(runtime_inputs.allowance) is not int or runtime_inputs.allowance<=0 or request['options']!=dict(
                num_ctx=16384,temperature=0,num_predict=min(runtime_inputs.allowance,output_cap))
                or type(request['options']['num_ctx']) is not int or type(request['options']['temperature']) is not int):
            raise ValueError('Runtime exact native options drift')
        checked_native_response(outer,request['options']['num_predict'])
        from .agent_server import _research_budget
        from openjarvis.core.types import Message,Role
        _research_budget([Message(role=Role(m['role']),content=m['content']) for m in messages],wire['strict_schema'],request['options']['num_predict'])
        from .work_navigation import v3_research_phase
        phase=('Acknowledge the verified research.md file. No further action is authorized.' if ack else
            v3_research_phase(report_schema))
        if messages[0]['content']!=replaced+'\n\n'+phase: raise ValueError('Runtime exact phase system drift')
        if 'action' in envelope:
            start=starts[index]
            if envelope['action']!=start['tool'] or envelope['action_input']!=start['arguments']:
                raise ValueError('Runtime action-to-dispatch drift')
        elif index!=len(wires)-1 or not require_ack: raise ValueError('Runtime premature final')
        if (outer.get('done') is not True or outer.get('done_reason')!='stop'
                or type(outer.get('eval_count')) is not int or not 0<outer['eval_count']<=request['options']['num_predict']
                or len(canonical_v3([messages,wire['strict_schema']]))>32768 or len(entity)>49152):
            raise ValueError('Runtime response or request admission drift')
        previous=wire
    last=wires[-1]['secured_envelope']
    if (require_ack and set(last)!={'final_answer'}) or (not require_ack and last.get('action')!='ultima_work_research_write'):
        raise ValueError('Runtime terminal phase drift')
    if written:
        end=ends[-1]
        if (end.get('success') is not True or end.get('tool')!='ultima_work_research_write'
                or end.get('agent')!='native_react'): raise ValueError('Runtime writer END identity drift')
        receipt=_strict_json(end['result'])
        metadata=end.get('metadata',{})
        submitted=wires[-2 if require_ack else -1]['secured_envelope']['action_input']
        if (metadata!=dict(receipt,arguments=submitted) or receipt.get('binding')!=list(snapshot.binding_key)
                or receipt.get('replay_sha256')!=snapshot.manifest_sha256
                or receipt.get('seq')!=snapshot.generation or receipt.get('protocol_version')!=3
                or receipt.get('runtime_sha256')!=packet.get('prewrite_sha256')):
            raise ValueError('Runtime writer receipt linkage drift')
        from .work_tools import checked_path
        intent=packet['execution']['intent']; files=packet['execution']['files']; effects=packet['execution']['effects']
        if len(files)!=1 or len(effects)!=1: raise ValueError('Runtime intent/file count drift')
        file=files[0]; effect=effects[0]
        if (receipt['path']!=str(checked_path(binding,'research.md')) or intent['path']!=receipt['path']
                or file.get('path')!=receipt['path'] or file.get('call_id')!=receipt['file_call_id']
                or file.get('tool_name')!='ultima_work_file_write' or file.get('report_call_id')!=receipt['report_call_id']
                or file.get('dispatch_uuid')!=receipt['dispatch_uuid'] or effect.get('dispatch_id')!=receipt['dispatch_uuid']
                or receipt.get('generation')!=snapshot.generation
                or any(file.get(k)!=v or effect.get(k)!=v for k,v in zip(('request_id','session_id','task_id'),snapshot.binding_key))
                or file.get('success') is not True or effect.get('state')!='completed'
                or effect.get('path')!=receipt['path'] or effect.get('file_call_id')!=receipt['file_call_id']
                or effect.get('report_call_id')!=receipt['report_call_id']
                or any(intent.get(k)!=receipt.get(k) for k in ('report_call_id','file_call_id','dispatch_uuid','adapter_uuid','seq','binding','sha256'))
                or intent['args_hash']!=digest(canonical_v3(submitted)) or intent['binding']!=list(snapshot.binding_key)
                or digest(file['content'].encode())!=receipt['sha256'] or intent['bytes']!=len(file['content'].encode())):
            raise ValueError('Runtime writer intent/file receipt drift')
    return packet


def verify_issued_research_artifacts(binding,artifacts,report_records,sources_json,*,issued_snapshot):
    """Explicit pure-data U1 helper; establishes no SDK runtime or ACK authority."""
    return _verify_artifact_data(binding,artifacts,report_records,sources_json,required_version=3,issued_snapshot=issued_snapshot)


def verify_research_artifacts(binding,artifacts,report_records,sources_json,*,require_reference=False,
                              required_version=None,issued_snapshot=None,runtime_packet=None,require_ack=False,runtime_inputs=None):
    """Historical v2 readback or strict fresh v3 runtime/file verification."""
    from .work_navigation import canonical_v3
    fresh=(required_version==3 or require_ack or runtime_packet is not None
        or any(r.get('result',{}).get('protocol_version')==3 for r in report_records))
    if fresh:
        if issued_snapshot is None or any(type(r.get('result',{}).get('protocol_version')) is not int
                or r['result']['protocol_version']!=3 for r in report_records):
            raise ValueError('Fresh protocol version 3 and snapshot required')
        if type(runtime_packet) is not bytes or not runtime_packet:
            raise ValueError('Nonempty immutable runtime bytes required')
        runtime=verify_runtime_packet(binding,issued_snapshot,None,runtime_packet,require_ack=require_ack,runtime_inputs=runtime_inputs)
        if runtime['execution']['intent'] is None: raise ValueError('Fresh runtime lacks file intent')
        reports={r['result']['file_call_id']:r for r in report_records}
        receipt=json.loads(json.loads(runtime['events'][-1])['data']['result'])
        submitted=runtime['wires'][-2 if require_ack else -1]['secured_envelope']['action_input']
        for artifact in artifacts:
            record=reports.get(artifact['call_id'])
            if record is None: raise ValueError('Missing runtime report adapter')
            result=record['result']
            if canonical_v3(json.loads(result['submitted_json']))!=canonical_v3(submitted):
                raise ValueError('Runtime authored submission drift')
            if (result.get('runtime_sha256')!=runtime['prewrite_sha256']
                    or result.get('replay_sha256')!=issued_snapshot.manifest_sha256 or result.get('sha256')!=artifact['sha256']):
                raise ValueError('Report runtime manifest linkage drift')
            if (receipt['report_call_id']!=record['call_id'] or receipt['file_call_id']!=result['file_call_id']
                    or receipt['dispatch_uuid']!=result['dispatch_uuid'] or receipt['adapter_uuid']!=result['adapter_uuid']
                    or receipt['path']!=artifact['path'] or result['path']!=receipt['path'] or receipt['sha256']!=artifact['sha256']):
                raise ValueError('Report runtime writer receipt drift')
            if any((record['call_id'] if key=='report_call_id' else result.get(key))!=value for key,value in receipt.items()):
                raise ValueError('Report original visible receipt field drift')
        required_version=3
    return _verify_artifact_data(binding,artifacts,report_records,sources_json,require_reference=require_reference,
        required_version=required_version,issued_snapshot=issued_snapshot)


def _verify_artifact_data(binding,artifacts,report_records,sources_json,*,require_reference=False,
                          required_version=None,issued_snapshot=None):
    from .work_tools import checked_path
    source_map=bound_sources(sources_json,binding)
    if not report_records: raise ValueError('No successful bound research report write')
    reports={r['result']['file_call_id']:r for r in report_records}
    cited=set()
    for artifact in artifacts:
        record=reports.get(artifact['call_id'])
        if not record or any(record.get(k)!=getattr(binding,k) for k in ('request_id','session_id','task_id')):
            raise ValueError('Research artifact has no current report-to-file call linkage')
        result = record['result']
        version=result.get('protocol_version')
        if required_version not in (None,3) or (version is not None and (type(version) is not int or version not in (2,3))):
            raise ValueError('Unsupported research protocol version')
        if required_version==3 and (version!=3 or issued_snapshot is None):
            raise ValueError('Fresh research requires protocol version 3 and snapshot')
        payload = json.loads(result['payload_json'])
        if version==3:
            from .work_navigation import resolve_v3, render_v3
            if issued_snapshot is None: raise ValueError('Missing v3 issued snapshot')
            packet=json.loads(issued_snapshot.replay_json)
            original=packet['collection']
            collection=ResearchCollection(original['catalogue_json'],original['trace_json'],original['attempts_json'],
                tuple(original['ignored_failure_ids']),original['search_query'])
            if json.loads(collection.catalogue_json)!=json.loads(sources_json): raise ValueError('Original v3 sources drift')
            resolved,bindings=resolve_v3(json.loads(result['submitted_json']),issued_snapshot,collection)
            if resolved!=payload or bindings!=result['bindings'] or checked_path(binding,payload['path'])!=checked_path(binding,artifact['path']):
                raise ValueError('Research v3 reference readback mismatch')
            rendered=render_v3(payload,sources_json,bindings=bindings)
        elif 'protocol_version' in result or require_reference:
            if type(result.get('protocol_version')) is not int or result['protocol_version'] != 2:
                raise ValueError('Unsupported research reference protocol')
            resolved, bindings = resolve_references(json.loads(result['submitted_json']),reference_cards(sources_json),sources_json)
            if resolved != payload or bindings != result['bindings'] or checked_path(binding,payload['path']) != checked_path(binding,artifact['path']):
                raise ValueError('Research reference readback mismatch')
            rendered=render_research_report(payload,sources_json,bindings=result.get("bindings"))
        else:
            rendered=render_research_report(payload,sources_json,bindings=result.get("bindings"))
        raw=checked_path(binding,artifact['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=artifact['sha256'] or raw.decode('utf8').replace('\r\n','\n')!=rendered.content.replace('\r\n','\n'):
            raise ValueError('Research rendered report independent readback mismatch')
        if list(rendered.cited_source_ids)!=record['result']['cited_source_ids']:
            raise ValueError('Research citation receipt mismatch')
        if list(rendered.evidence)!=record['result']['evidence']:
            raise ValueError('Research fact evidence mismatch')
        cited.update(rendered.cited_source_ids)
    if len(cited)<3: raise ValueError('Research has fewer than three actually cited fetched sources')
    return [source_map[s] for s in source_map if s in cited]
