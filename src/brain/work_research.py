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
            if (kind == 'limitation' and first <= line and end <= last
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
                return callee == symbol if kind == 'code' else throwing or callee.split('.')[-1] in ('warn','warning')
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
                for last in range(first, first+8):
                    if last not in visible:
                        break
                    if _js_support(body,first,last,'code',op,suffix,rows):
                        yield first, last, 'code', op
                        if op.split('.')[-1] in ('warn','warning'):
                            yield first, last, 'limitation', ''
                        break
                    if _js_support(body,first,last,'limitation',None,suffix,rows):
                        yield first, last, 'limitation', ''
                        break


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


def verify_research_artifacts(binding,artifacts,report_records,sources_json,*,require_reference=False):
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
        payload = json.loads(result['payload_json'])
        if 'protocol_version' in result or require_reference:
            if type(result.get('protocol_version')) is not int or result['protocol_version'] != 2:
                raise ValueError('Unsupported research reference protocol')
            resolved, bindings = resolve_references(json.loads(result['submitted_json']),reference_cards(sources_json),sources_json)
            if resolved != payload or bindings != result['bindings'] or checked_path(binding,payload['path']) != checked_path(binding,artifact['path']):
                raise ValueError('Research reference readback mismatch')
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
