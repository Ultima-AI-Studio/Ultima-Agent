"""Safe immutable navigation data and restricted replay; no runtime authority."""
from dataclasses import dataclass, asdict, replace
import hashlib
from html.parser import HTMLParser
import inspect
import json
from pathlib import Path, PurePosixPath
import platform
import re
import secrets
import time
import tokenize
from urllib.parse import urlsplit, urlunsplit
import uuid

BindingKey = tuple[str, str, str]
EXTRACTOR_SHA256 = '9d7cab4749f27dbc08f1b246e03c8a6f8a059acb74692802a1326216e00ef86d'
DOC_SUFFIXES = ('', '.md', '.rst', '.txt', '.htm', '.html', '.adoc')


def canonical_v3(value: object) -> bytes:
    def check(v):
        if v is None or type(v) in (bool, int): return
        if type(v) is str:
            if any(0xd800 <= ord(c) <= 0xdfff for c in v): raise ValueError('Surrogate in canonical JSON')
            return
        if type(v) is list:
            for item in v: check(item)
            return
        if type(v) is dict and all(type(k) is str for k in v):
            for k, item in v.items(): check(k); check(item)
            return
        raise ValueError('Unsupported canonical JSON type')
    check(value)
    return json.dumps(value, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode('utf8')


def _h(raw):
    return hashlib.sha256(raw).hexdigest()


def _load(raw):
    obj = json.loads(raw)
    if canonical_v3(obj) != raw: raise ValueError('Noncanonical sealed JSON')
    return obj


def _uuid(value):
    if type(value) is not str or str(uuid.UUID(value)) != value: raise ValueError('Noncanonical UUID')
    return value


@dataclass(frozen=True)
class ScanPolicy:
    scanners: tuple[object, ...]
    mode: str
    policy_json: bytes
    policy_sha256: str


@dataclass(frozen=True)
class SourceV3:
    source_id: str
    identity_json: bytes
    domain: str
    suffix: str
    total_lines: int
    safe_line_pairs: tuple[tuple[int, str], ...]
    omissions: tuple[tuple[int, int, str], ...]
    anchors_json: bytes
    available: bool
    reason: str


@dataclass(frozen=True)
class CatalogueV3:
    binding_key: BindingKey
    nonce: str
    policy_sha256: str
    sources: tuple[SourceV3, ...]
    catalogue_json: bytes
    catalogue_sha256: str


@dataclass(frozen=True)
class PageKey:
    generation: int
    seq: int
    dispatch_uuid: str
    adapter_uuid: str


@dataclass(frozen=True)
class ViewV3:
    view_id: str
    source_id: str
    start: int
    end: int
    wire_json: bytes
    wire_sha256: str
    cards_json: bytes


@dataclass(frozen=True)
class IssuedSnapshotV3:
    binding_key: BindingKey
    nonce: str
    catalogue_sha256: str
    generation: int
    views_json: bytes
    replay_json: bytes
    manifest_sha256: str


def _policy_data(scanners, mode):
    if type(scanners) is not tuple or not scanners or mode not in ('block', 'warn', 'redact'):
        raise ValueError('Missing configured scanner policy')
    extractor_path=Path(__file__).with_name('browser')/'channel.py'
    if _h(extractor_path.read_bytes())!=EXTRACTOR_SHA256:
        raise ValueError('Pinned BrowserChannel extractor drift')
    descriptors=[]
    for scanner in scanners:
        cls=type(scanner)
        if not callable(getattr(scanner,'scan',None)) or not callable(getattr(scanner,'redact',None)):
            raise ValueError('Invalid scanner')
        path=inspect.getsourcefile(cls)
        if not path: raise ValueError('Scanner source identity unavailable')
        backend=getattr(scanner,'_rust_impl',None)
        backend_module=inspect.getmodule(type(backend)) if backend is not None else None
        backend_path=getattr(backend_module,'__file__',None)
        descriptors.append(dict(name=cls.__module__+'.'+cls.__qualname__,source_sha256=_h(Path(path).read_bytes()),
            backend=type(backend).__module__+'.'+type(backend).__qualname__,
            backend_sha256=_h(Path(backend_path).read_bytes()) if backend_path else None,
            patterns=repr(getattr(scanner,'PATTERNS',None))))
    return dict(v=3,scanners=descriptors,mode=mode,extractor=EXTRACTOR_SHA256,
        navigation_sha256=_h(Path(__file__).read_bytes()),
        witness_sha256=_h(Path(__file__).with_name('work_research.py').read_bytes()),
        python=platform.python_version(),htmlparser=_h(Path(inspect.getsourcefile(HTMLParser)).read_bytes()),
        witness='source9-unchanged',serialization='J3',paging=[262144,1024,4096,3072,24,8,8],render='issued-page-v3')


def make_scan_policy(scanners: tuple[object, ...], mode: str) -> ScanPolicy:
    raw=canonical_v3(_policy_data(scanners,mode))
    return ScanPolicy(scanners,mode,raw,_h(raw))


def validate_scan_policy(policy: ScanPolicy, expected: ScanPolicy | None = None):
    raw=canonical_v3(_policy_data(policy.scanners,policy.mode))
    if raw!=policy.policy_json or _h(raw)!=policy.policy_sha256: raise ValueError('Scanner policy drift')
    if expected is not None and (policy.policy_json!=expected.policy_json or len(policy.scanners)!=len(expected.scanners)
            or any(a is not b for a,b in zip(policy.scanners,expected.scanners))):
        raise ValueError('Scanner object/order drift')


def _findings(text, policy):
    return any(not s.scan(text).clean for s in policy.scanners)


def _redact(text, policy):
    for scanner in policy.scanners: text=scanner.redact(text)
    return text


def scan_view(view: ViewV3, policy: ScanPolicy) -> ViewV3:
    """Mandatory final observation check by the trusted inspector before return."""
    validate_scan_policy(policy)
    def unsafe(value):
        if isinstance(value,str): return _findings(value,policy)
        if isinstance(value,list): return any(unsafe(v) for v in value)
        if isinstance(value,dict): return any(unsafe(k) or unsafe(v) for k,v in value.items())
        return False
    if (_h(view.wire_json)!=view.wire_sha256 or _findings(view.wire_json.decode('utf8'),policy)
            or unsafe(_load(view.wire_json))):
        raise ValueError('Unsafe complete observation')
    return view


def _projection(body, kind):
    if 'html' not in kind: return body
    class Text(HTMLParser):
        def __init__(self): super().__init__(); self.parts=[]; self.skip=0
        def handle_starttag(self,tag,attrs):
            if tag in ('script','style'): self.skip+=1
        def handle_endtag(self,tag):
            if tag in ('script','style'): self.skip=max(0,self.skip-1)
        def handle_data(self,data):
            if not self.skip: self.parts.append(data)
    parser=Text(); parser.feed(body)
    return ' '.join(parser.parts)


def _normalize(url):
    p=urlsplit(url)
    if p.scheme not in ('http','https') or not p.hostname or p.username or p.password or p.fragment:
        raise ValueError('Unsafe source identity')
    host=p.hostname.lower()
    if ':' in host: host='['+host+']'
    if p.port not in (None,80 if p.scheme=='http' else 443): host+=':'+str(p.port)
    return urlunsplit((p.scheme.lower(),host,p.path or '/',p.query,''))


def _runs(omitted):
    runs=[]
    for line,reason in sorted(omitted.items()):
        if runs and runs[-1][1]+1==line and runs[-1][2]==reason: runs[-1][1]=line
        else: runs.append([line,line,reason])
    return runs


def _linked_sources(collection, binding, records):
    from .work_research import bound_sources
    sources=list(bound_sources(collection.catalogue_json,binding).values())
    if len(sources)>5: raise ValueError('Too many sources')
    attempts=json.loads(collection.attempts_json); trace=json.loads(collection.trace_json)
    for index,source in enumerate(sources,1):
        if source['source_id']!='S'+str(index): raise ValueError('Invalid source labels')
        call=_uuid(source['read_call_id'])
        matching=[r for r in records if r.get('call_id')==call]
        if len(matching)!=1: raise ValueError('GET ledger mismatch')
        record=matching[0]
        ids={k:getattr(binding,k) for k in ('request_id','session_id','task_id')}
        if record.get('tool_name')!='ultima_work_http_get' or record.get('success') is not True or any(record.get(k)!=v for k,v in ids.items()):
            raise ValueError('GET binding mismatch')
        original={k:v for k,v in source.items() if k not in (*ids,'read_call_id','adapter_source_id')}
        original['source_id']=source['adapter_source_id']
        if record.get('result')!=original: raise ValueError('GET original result mismatch')
        matches=[a for a in attempts if a.get('adapter_call_id')==call and a.get('tool_name')=='ultima_work_http_get']
        if len(matches)!=1 or matches[0].get('success') is not True or any(matches[0].get(k)!=v for k,v in ids.items()):
            raise ValueError('GET attempt linkage mismatch')
        sdk=_uuid(matches[0]['sdk_call_id'])
        events=[e for e in trace if e.get('sdk_call_id')==sdk]
        if [e.get('type') for e in events]!=['tool_call_start','tool_call_end'] or any(any(e.get(k)!=v for k,v in ids.items()) or e.get('data',{}).get('tool')!='ultima_work_http_get' for e in events):
            raise ValueError('GET event linkage mismatch')
        start,end=events[0]['data'],events[1]['data']
        metadata=end.get('metadata',{})
        if (start.get('arguments')!={'url':source['requested_url']} or end.get('success') is not True
                or metadata.get('call_id')!=call or metadata.get('result')!=record['result']
                or metadata.get('success') is not True or any(metadata.get(k)!=v for k,v in ids.items())):
            raise ValueError('GET START/END result linkage mismatch')
        if _h(source['body'].encode('utf8'))!=source['decoded_body_sha256']: raise ValueError('Body hash drift')
        if _normalize(source['final_url'])!=source['dedupe_url']: raise ValueError('Normalized URL mismatch')
        if _projection(source['body'],source.get('content_type',''))!=source['text']: raise ValueError('Projection hash drift')
    if len({s['dedupe_url'] for s in sources})!=len(sources) or len({s['decoded_body_sha256'] for s in sources})!=len(sources):
        raise ValueError('Duplicate source URL/body')
    return sources


def _safe_source(source, policy):
    from .work_research import _anchors, _python_witnesses, _js_tokens, _fact_evidence
    body,text=source['body'],source['text']
    domain='extracted-text' if 'html' in source.get('content_type','') else 'raw'
    suffix=PurePosixPath(urlsplit(source['final_url']).path).suffix.lower()
    identity=[source['source_id'],source['final_url'],source['dedupe_url'],source['read_call_id'],
              source['decoded_body_sha256'],_h(text.encode('utf8')),domain,policy.policy_sha256]
    if any(_findings(value,policy) for value in identity) or _findings(canonical_v3(identity).decode(),policy):
        raise ValueError('Unsafe source provenance identity')
    rows=text.splitlines(); reason=''; safe=[]; omitted={}; anchors=[]
    if source.get('truncated'): reason='get-truncated'
    elif len(body.encode('utf8'))>262144 or len(text.encode('utf8'))>262144: reason='source-size'
    elif len(body.splitlines())>1024 or len(rows)>1024: reason='source-lines'
    elif any(re.search(r'\r(?!\n)|[\v\f\x1c-\x1e\x85\u2028\u2029]',v) for v in (body,text)): reason='unsupported-coordinates'
    elif domain=='extracted-text' and _findings(body,policy): reason='unsafe-html'
    elif domain=='extracted-text' and suffix not in DOC_SUFFIXES: reason='unsupported-suffix'
    elif policy.mode=='block' and _findings(text,policy): reason='security-block'
    else:
        segments=text.splitlines(keepends=True)
        redacted=_redact(text,policy)
        if redacted!=''.join(_redact(line,policy) for line in segments) or _findings(redacted,policy):
            reason='security-map'
        else:
            for i,line in enumerate(rows,1):
                if _findings(line,policy) or _redact(line,policy)!=line: omitted[i]='security'
                else: safe.append((i,line))
            visible=dict(safe); syntax=None
            try:
                if suffix=='.py': syntax=list(_python_witnesses(body))
                elif suffix in ('.js','.ts','.mjs','.cjs'): syntax=_js_tokens(body,suffix)
                for a,z,kind,op in sorted(set(_anchors(source,visible,syntax))):
                    if not 1<=a<=z<a+8 or any(i not in visible for i in range(a,z+1)): continue
                    witness=dict(claim=op or 'witness',kind=kind,first_line=a,last_line=z)
                    if kind=='code': witness['symbol']=op
                    _fact_evidence(witness,source,visible,syntax)
                    if not _findings(op,policy): anchors.append([a,z,kind,op])
            except (SyntaxError,ValueError,tokenize.TokenError):
                anchors=[]
    return SourceV3(source['source_id'],canonical_v3(identity),domain,suffix,len(rows),tuple(safe),
                    tuple(tuple(r) for r in _runs(omitted)),canonical_v3(anchors),not bool(reason),reason)


def build_page(catalogue: CatalogueV3, source_id: str, start_line: int, key: PageKey) -> ViewV3:
    if not re.fullmatch('[0-9a-f]{32}',catalogue.nonce): raise ValueError('Invalid nonce')
    if len(catalogue.binding_key)!=3 or any(type(x) is not str or not x for x in catalogue.binding_key): raise ValueError('Invalid binding')
    for n in (key.generation,key.seq):
        if type(n) is not int or not 1<=n<=2147483647: raise ValueError('Invalid page sequence')
    _uuid(key.dispatch_uuid); _uuid(key.adapter_uuid)
    source=next((s for s in catalogue.sources if s.source_id==source_id),None)
    if source is None or not source.available: raise ValueError('Unavailable source')
    if type(start_line) is not int or not 1<=start_line<=source.total_lines: raise ValueError('Invalid start line')
    end=min(source.total_lines,start_line+23)
    view_id=_h(canonical_v3(['view3',catalogue.nonce,list(catalogue.binding_key),json.loads(source.identity_json),
                           start_line,end,key.seq,key.dispatch_uuid,key.adapter_uuid]))
    safe=dict(source.safe_line_pairs)
    omitted={i:reason for a,z,reason in source.omissions for i in range(max(a,start_line),min(z,end)+1)}
    wire=dict(v=3,source_id=source_id,view_id=view_id,start=start_line,end=end,total_lines=source.total_lines,
              lines=[],cards=[],omissions=[],omitted_cards=0,next_start=end+1 if end<source.total_lines else None)
    def encoded():
        wire['omissions']=_runs(omitted)
        return canonical_v3(wire)
    for line in range(start_line,end+1):
        if line not in safe: omitted.setdefault(line,'security')
        else: omitted[line]='size'
    if len(encoded())>3072: raise ValueError('Page metadata exceeds cap')
    for line in range(start_line,end+1):
        if line not in safe: continue
        wire['lines'].append([line,safe[line]]); omitted.pop(line,None)
        if len(encoded())>3072:
            wire['lines'].pop(); omitted[line]='size'
    visible=dict(wire['lines']); candidates=[]
    for a,z,kind,op in json.loads(source.anchors_json):
        if not start_line<=a<=z<=end or any(i not in visible for i in range(a,z+1)): continue
        left,right=a,z; padding=7-(z-a)
        for _ in range(padding//2):
            if left-1 not in visible: break
            left-=1
        for _ in range(padding-padding//2):
            if right+1 not in visible: break
            right+=1
        ap=[[i,visible[i]] for i in range(a,z+1)]; cp=[[i,visible[i]] for i in range(left,right+1)]
        ref='N3.'+_h(canonical_v3(['card3',view_id,kind,op,a,z,left,right,_h(canonical_v3(ap)),_h(canonical_v3(cp))]))[:16]
        card=[ref,kind,op,a,z,left,right]
        if any(old[0]==ref for old in candidates): raise ValueError('Reference collision')
        candidates.append(card)
    wire['omitted_cards']=len(candidates)
    # Metadata digit growth can require dropping trailing lines; never cut a line.
    while len(encoded())>3072 and wire['lines']:
        line,_=wire['lines'].pop(); omitted[line]='size'
    visible=dict(wire['lines'])
    candidates=[c for c in candidates if all(i in visible for i in range(c[5],c[6]+1))]
    total=len(candidates)
    wire['omitted_cards']=total
    for card in candidates:
        if len(wire['cards'])==8: break
        wire['cards'].append(card); wire['omitted_cards']=total-len(wire['cards'])
        if len(encoded())>3072:
            wire['cards'].pop(); wire['omitted_cards']=total-len(wire['cards']); break
    raw=encoded()
    if len(raw)>3072: raise ValueError('Page fit failure')
    return ViewV3(view_id,source_id,start_line,end,raw,_h(raw),canonical_v3(wire['cards']))


def _document_landmarks(source, anchors):
    """Navigation hints from already safe source lines; no new evidence rights."""
    safe=dict(source.safe_line_pairs)
    def heading(anchor):
        return next((safe[i].strip() for i in range(anchor[0],anchor[1]+1)
            if re.match(r'^(?:#{1,6}|={1,6})[ \t]+\S',safe.get(i,''))), '')
    def sample(values,limit):
        if len(values)<=limit:return values
        if limit==1:return values[:1]
        return [values[round(i*(len(values)-1)/(limit-1))] for i in range(limit)]
    titles=[anchor for anchor in anchors if heading(anchor)]
    selected=sample(titles,8)
    if len(selected)<8:
        selected+=sample([anchor for anchor in anchors if anchor not in titles],8-len(selected))
    return [[a,z,(heading(anchor) or ' '.join(safe[i].strip() for i in range(a,z+1)))[:120]]
            for anchor in selected for a,z in [anchor[:2]]]


def prepare_navigation(collection, binding, scanners: ScanPolicy, *, get_records_json: bytes, deadline: float) -> CatalogueV3:
    if time.monotonic()>=deadline: raise ValueError('Navigation preparation deadline')
    validate_scan_policy(scanners)
    records=json.loads(get_records_json)
    originals=_linked_sources(collection,binding,records)
    sources=tuple(_safe_source(s,scanners) for s in originals)
    b=tuple(getattr(binding,k) for k in ('request_id','session_id','task_id'))
    nonce=secrets.token_hex(16)
    cat=CatalogueV3(b,nonce,scanners.policy_sha256,sources,b'', '')
    available=[]
    for source in sources:
        fits=False
        if source.available:
            for start in range(1,source.total_lines+1):
                if time.monotonic()>=deadline: raise ValueError('Navigation preparation deadline')
                view=build_page(cat,source.source_id,start,PageKey(1,2147483647,str(uuid.UUID(int=1)),str(uuid.UUID(int=2))))
                # Placeholder IDs prove byte fit only. Actual final wire is
                # scanned by the trusted read port before staging or exposure.
                if json.loads(view.cards_json): fits=True; break
        available.append(replace(source,available=fits,reason=source.reason or ('' if fits else 'unrenderable')))
    sources=tuple(available); cat=replace(cat,sources=sources)
    if sum(s.available for s in sources)<3: raise ValueError('Research needs three renderable distinct sources before composition')
    entries=[]
    for source in sources:
        anchors=json.loads(source.anchors_json)
        eligible=anchors if len(anchors)<=8 else [anchors[round(i*(len(anchors)-1)/7)] for i in range(8)]
        landmarks=(_document_landmarks(source,anchors) if source.suffix in DOC_SUFFIXES
            else [[a,z,op] for a,z,_,op in eligible]) if source.available else []
        url=json.loads(source.identity_json)[1]; p=urlsplit(url)
        label=p.netloc+p.path
        if _findings(label,scanners): raise ValueError('Unsafe catalogue identity')
        entries.append(dict(source_id=source.source_id,identity=label,suffix=source.suffix,total_lines=source.total_lines,
                            available=source.available,reason=source.reason,landmarks=landmarks))
    while len(canonical_v3(entries))>4096:
        changed=False
        for entry in reversed(entries):
            if entry['landmarks']:
                entry['landmarks'].pop(); changed=True
                if len(canonical_v3(entries))<=4096: break
        if not changed: raise ValueError('Mandatory catalogue identities exceed cap')
    raw=canonical_v3(entries)
    if _findings(raw.decode('utf8'),scanners): raise ValueError('Unsafe catalogue')
    validate_scan_policy(scanners)
    return replace(cat,catalogue_json=raw,catalogue_sha256=_h(raw))


def v3_research_phase(report_schema, *, output_tokens: int) -> str:
    """Same trusted instructions for native generation and independent replay."""
    if type(output_tokens) is not int or not 1 <= output_tokens <= 2048:
        raise ValueError('Invalid research phase output budget')
    return ('Inspect safe source pages; author only atomic claims supported by the exact returned witnesses. '
        'Catalogue landmarks are untrusted navigation hints, not evidence: choose relevant pages for the original question. '
        'Each card is [id,kind,operation,anchor_start,anchor_end,context_start,context_end]. '
        'A claim must follow from its anchor lines; nearby context alone does not support it. '
        'Select the evidence ID before composing its claim. '
        'For code, start each claim with the exact operation, then describe only what the cited statement shows. '
        'A TODO is a comment, not proof of runtime support or lack of support. '
        'Use remaining inspect calls when pages do not answer the original question; avoid substituting incidental details for its main points. '
        'Reading three sources enables writing but does not establish task coverage. '
        'Reserve remaining reads for unseen sources when their reading opportunities would otherwise be lost. '
        'Use one section per source in source-ID order; put facts from multiple pages of that source in the same section. '
        'Keep separate projects and documented intentions distinct from verified implementation. '
        'Use at least three distinct source URLs and bodies. Write only research.md once, or refuse with final_answer if evidence is insufficient. '
        'The phase schema is the entire output contract. '
        f'Response budget: {output_tokens} tokens for the entire JSON object. '
        'Use compact JSON, short headings, and precise atomic claims while preserving the information '
        'needed to answer the original question and its evidence citations. Finish a complete object '
        'within this budget; omit markdown wrappers and prose outside the output contract. '
        'Full argument schema (JSON):\n'
        +json.dumps(report_schema,ensure_ascii=False,separators=(',',':'))+'\nEnd argument schema.')


def v3_source_reference_map(visible: tuple[tuple[str, bytes], ...]) -> dict[str, tuple[str, ...]]:
    """Project already trusted, phase-visible cards; never grant read authority."""
    if type(visible) is not tuple or len(visible)>6: raise ValueError('Invalid visible pages')
    sources={}; seen=set()
    for page in visible:
        if type(page) is not tuple or len(page)!=2: raise ValueError('Invalid visible page')
        sid,raw=page
        if type(sid) is not str or not re.fullmatch(r'S[1-5]',sid) or type(raw) is not bytes:
            raise ValueError('Invalid visible source')
        cards=_load(raw)
        if type(cards) is not list or len(cards)>8: raise ValueError('Invalid visible cards')
        for card in cards:
            if (type(card) is not list or len(card)!=7 or type(card[0]) is not str
                    or not re.fullmatch(r'N3\.[0-9a-f]{16}',card[0])
                    or card[1] not in ('documented','code','limitation') or type(card[2]) is not str
                    or any(type(n) is not int for n in card[3:])
                    or not 1<=card[5]<=card[3]<=card[4]<=card[6]):
                raise ValueError('Invalid visible card')
            if card[0] in seen: raise ValueError('Reference collision')
            seen.add(card[0]); sources.setdefault(sid,[]).append(card[0])
    return {sid:tuple(sorted(sources[sid])) for sid in sorted(sources)}


def v3_phase_inspect_schema(base: dict, available: tuple[str, ...],
                            visible: tuple[tuple[str, bytes], ...], used: int) -> dict | None:
    """Reserve reads for missing sources using only trusted, confirmed pages."""
    from copy import deepcopy
    if type(used) is not int or not 0<=used<=6:
        raise ValueError('Invalid read budget')
    permitted=base['properties']['source_id']['enum']
    if (type(available) is not tuple or len(available)>5
            or any(type(sid) is not str or not re.fullmatch(r'S[1-5]',sid)
                   or sid not in permitted for sid in available)
            or len(set(available))!=len(available)):
        raise ValueError('Invalid available sources')
    covered=v3_source_reference_map(visible)
    if len(visible)>used or any(sid not in available for sid,_ in visible):
        raise ValueError('Visible source or read budget drift')
    remaining=6-used; missing=max(0,3-len(covered))
    unseen=[sid for sid in available if sid not in covered]
    if remaining==0 or remaining<missing or len(unseen)<missing:
        return None
    choices=unseen if unseen and remaining<=len(unseen) else list(available)
    schema=deepcopy(base)
    schema['properties']['source_id']['enum']=choices
    return schema


RESEARCH_NOT_DELIVERED='本次研究未交付。'


def v3_research_final_schema(*, ack: bool = False) -> dict:
    """Only a verified write may receive a free-form acknowledgement."""
    if type(ack) is not bool: raise ValueError('Invalid acknowledgement phase')
    text=dict(type='string',minLength=1,maxLength=1000)
    if not ack: text['enum']=[RESEARCH_NOT_DELIVERED]
    return dict(type='object',additionalProperties=False,required=['final_answer'],
                properties=dict(final_answer=text))


def v3_writer_schema(source_refs: dict[str, tuple[str, ...]] | None = None) -> dict:
    def obj(**props): return dict(type='object',additionalProperties=False,properties=props,required=list(props))
    def text(n): return dict(type='string',minLength=1,maxLength=n)
    def array(items,a,z): return dict(type='array',items=items,minItems=a,maxItems=z)
    fact=obj(claim=text(2000),evidence_id=dict(type='string',pattern=r'^N3\.[0-9a-f]{16}$',minLength=19,maxLength=19))
    section=obj(source_id=dict(type='string',pattern=r'^S[1-5]$',minLength=2,maxLength=2),heading=text(200),facts=array(fact,1,6))
    if source_refs is not None:
        if (type(source_refs) is not dict or not 3<=len(source_refs)<=5
                or any(type(sid) is not str for sid in source_refs)):
            raise ValueError('Three visible reference sources required')
        branches=[]; seen=set()
        for sid,refs in sorted(source_refs.items()):
            if (type(sid) is not str or not re.fullmatch(r'S[1-5]',sid) or type(refs) is not tuple
                    or not refs or len(refs)>48 or any(type(ref) is not str or not re.fullmatch(r'N3\.[0-9a-f]{16}',ref) for ref in refs)
                    or len(set(refs))!=len(refs) or seen.intersection(refs)):
                raise ValueError('Invalid source reference mapping')
            seen.update(refs)
            bound_fact=obj(claim=text(2000),evidence_id=dict(fact['properties']['evidence_id'],enum=sorted(refs)))
            branches.append(obj(source_id=dict(section['properties']['source_id'],enum=[sid]),heading=text(200),facts=array(bound_fact,1,6)))
        if len(seen)>48: raise ValueError('Visible reference count exceeds cap')
        section=dict(anyOf=branches)
    return obj(path=dict(text(2048),enum=['research.md']),title=text(200),sections=array(section,3,5))


def v3_phase_writer_schema(visible: tuple[tuple[str, bytes], ...]) -> dict:
    """Bind each code fact to its trusted operation using the sampler dialect."""
    from itertools import combinations
    schema=v3_writer_schema(v3_source_reference_map(visible))
    constraints={}
    for _,raw in visible:
        for ref,kind,op,*_ in _load(raw):
            pattern=None
            if kind=='code':
                if len(op)>200 or not re.fullmatch(r'[A-Za-z_$][\w$]*(?:\.[A-Za-z_$][\w$]*)*',op):
                    raise ValueError('Invalid visible code operation')
                # Equivalent to the writer's exact-operation lookarounds for
                # valid single-line claims, using only supported GBNF syntax.
                pattern=(r'^(.*[^A-Za-z0-9_$.])?'+re.escape(op)
                    +r'([^A-Za-z0-9_$.].*|\.([^A-Za-z_$].*)?)?$')
            constraints[ref]=pattern
    for section in schema['properties']['sections']['items']['anyOf']:
        items=section['properties']['facts']
        base=items['items']; groups={}
        for ref in base['properties']['evidence_id']['enum']:
            groups.setdefault(constraints[ref],[]).append(ref)
        alternatives=[]
        for pattern,refs in groups.items():
            claim=dict(base['properties']['claim'])
            if pattern is not None: claim['pattern']=pattern
            alternatives.append(dict(base,properties=dict(claim=claim,
                evidence_id=dict(base['properties']['evidence_id'],enum=refs))))
        items['items']=alternatives[0] if len(alternatives)==1 else dict(anyOf=alternatives)
    sections=schema['properties']['sections']['items']['anyOf']
    definitions={'research_source_'+s['properties']['source_id']['enum'][0]:s for s in sections}
    schema['definitions']=definitions
    schema['properties']['sections']=dict(type='array',minItems=3,maxItems=5,anyOf=[dict(type='array',
        items=[{'$ref':'#/definitions/'+name} for name in names],
        minItems=size,maxItems=size,additionalItems=False)
        for size in range(3,len(definitions)+1) for names in combinations(definitions,size)])
    return schema


def v3_research_envelope(alternatives):
    """Keep local writer references rooted in the complete generation schema."""
    from copy import deepcopy
    schema=deepcopy(dict(anyOf=alternatives));definitions={}
    for option in schema['anyOf']:
        params=option.get('properties',{}).get('action_input')
        if not isinstance(params,dict):continue
        for name,value in params.pop('definitions',{}).items():
            if name in definitions:raise ValueError('Conflicting research definitions')
            definitions[name]=value
    if definitions:schema['definitions']=definitions
    return schema


def _source_packet(source):
    result=asdict(source)
    for k in ('identity_json','anchors_json'): result[k]=json.loads(result[k])
    result['safe_line_pairs']=[list(x) for x in source.safe_line_pairs]
    result['omissions']=[list(x) for x in source.omissions]
    return result


def seal_snapshot(catalogue, collection, get_records_json, policy, reads, *, generation):
    """Seal already issued reads; caller ledger alone proves issuance authority."""
    validate_scan_policy(policy)
    if not 1<=len(reads)<=6: raise ValueError('Invalid read count')
    records=[]; seen=set()
    for key,view in reads:
        if (view.source_id,view.start) in seen or key.generation>=generation: raise ValueError('Unissued or duplicate page')
        seen.add((view.source_id,view.start))
        expected=build_page(catalogue,view.source_id,view.start,key)
        if expected!=view: raise ValueError('Read wire mismatch')
        scan_view(view,policy)
        records.append(dict(key=asdict(key),source_id=view.source_id,start=view.start,wire=json.loads(view.wire_json),wire_sha256=view.wire_sha256))
    packet=dict(v=3,binding_key=list(catalogue.binding_key),nonce=catalogue.nonce,policy=json.loads(policy.policy_json),
        catalogue=json.loads(catalogue.catalogue_json),catalogue_sha256=catalogue.catalogue_sha256,
        sources=[_source_packet(s) for s in catalogue.sources],collection=asdict(collection),get_records=json.loads(get_records_json),reads=records,generation=generation)
    packet['collection']['ignored_failure_ids']=list(collection.ignored_failure_ids)
    raw=canonical_v3(packet)
    views=canonical_v3([r['wire'] for r in records])
    return IssuedSnapshotV3(catalogue.binding_key,catalogue.nonce,catalogue.catalogue_sha256,generation,views,raw,_h(raw))


def resolve_v3(submitted: dict, issued_snapshot: IssuedSnapshotV3, collection) -> tuple[dict, list[dict]]:
    from jsonschema import Draft7Validator
    from types import SimpleNamespace
    from .work_research import _fact_evidence
    snapshot=issued_snapshot
    if _h(snapshot.replay_json)!=snapshot.manifest_sha256: raise ValueError('Replay manifest drift')
    packet=_load(snapshot.replay_json)
    if packet.get('v')!=3 or packet['binding_key']!=list(snapshot.binding_key) or packet['nonce']!=snapshot.nonce or packet['generation']!=snapshot.generation or packet['catalogue_sha256']!=snapshot.catalogue_sha256:
        raise ValueError('Foreign snapshot binding')
    original=asdict(collection); original['ignored_failure_ids']=list(collection.ignored_failure_ids)
    if packet['collection']!=original: raise ValueError('Original collection drift')
    # Restore the real configured SDK scanners from the sealed policy; no substitute scanner.
    from openjarvis.security.scanner import SecretScanner, PIIScanner
    factories={c.__module__+'.'+c.__qualname__:c for c in (SecretScanner,PIIScanner)}
    try: scanners=tuple(factories[d['name']]() for d in packet['policy']['scanners'])
    except KeyError as exc: raise ValueError('Unknown replay scanner backend') from exc
    policy=make_scan_policy(scanners,packet['policy']['mode'])
    if json.loads(policy.policy_json)!=packet['policy']: raise ValueError('Replay policy drift')
    binding=SimpleNamespace(**dict(zip(('request_id','session_id','task_id'),snapshot.binding_key)))
    cat=prepare_navigation(collection,binding,policy,get_records_json=canonical_v3(packet['get_records']),deadline=time.monotonic()+30)
    cat=replace(cat,nonce=snapshot.nonce)
    if cat.catalogue_sha256!=snapshot.catalogue_sha256 or json.loads(cat.catalogue_json)!=packet['catalogue'] or [_source_packet(s) for s in cat.sources]!=packet['sources']:
        raise ValueError('Safe source reconstruction drift')
    reads=packet['reads']
    if not 1<=len(reads)<=6 or canonical_v3([r['wire'] for r in reads])!=snapshot.views_json: raise ValueError('Issued views drift')
    issued={}; seen=set(); sequences=set(); dispatches=set(); adapters=set()
    for read in reads:
        key=PageKey(**read['key']); source_id=read['source_id']; start=read['start']
        if key.generation>=snapshot.generation or key.seq in sequences or key.dispatch_uuid in dispatches or key.adapter_uuid in adapters or (source_id,start) in seen:
            raise ValueError('Duplicate or unissued read')
        sequences.add(key.seq); dispatches.add(key.dispatch_uuid); adapters.add(key.adapter_uuid); seen.add((source_id,start))
        view=scan_view(build_page(cat,source_id,start,key),policy)
        if json.loads(view.wire_json)!=read['wire'] or view.wire_sha256!=read['wire_sha256']: raise ValueError('Issued page replay drift')
        for card in json.loads(view.cards_json):
            ref=card[0]
            if ref in issued: raise ValueError('Reference collision')
            issued[ref]=(card,view)
    if not Draft7Validator(v3_writer_schema()).is_valid(submitted):
        raise ValueError('Invalid v3 submitted schema')
    resolved=json.loads(canonical_v3(submitted)); bindings=[]; sources={s['source_id']:s for s in json.loads(collection.catalogue_json)}
    used=[]
    for section in resolved['sections']:
        sid=section['source_id']
        if sid in used or sid not in sources: raise ValueError('Duplicate or unknown source section')
        used.append(sid)
        for fact in section['facts']:
            ref=fact.pop('evidence_id')
            if ref not in issued: raise ValueError('Unknown or unissued reference')
            card,view=issued[ref]
            if view.source_id!=sid: raise ValueError('Foreign reference')
            _,kind,op,a,z,left,right=card
            fact.update(kind=kind,first_line=a,last_line=z)
            if kind=='code': fact['symbol']=op
            visible=dict(json.loads(view.wire_json)['lines'])
            _fact_evidence(fact,sources[sid],visible)
            source=sources[sid]
            binding_card={k:source[k] for k in ('source_id','final_url','decoded_body_sha256','read_call_id','request_id','session_id','task_id')}
            binding_card.update(evidence_id=ref,kind=kind,symbol=op,first_line=a,last_line=z,citation_first=left,citation_last=right,
                domain=next(s.domain for s in cat.sources if s.source_id==sid),view_id=view.view_id,view_json=view.wire_json.decode())
            bindings.append(binding_card)
    if len({sources[s]['dedupe_url'] for s in used})<3 or len({sources[s]['decoded_body_sha256'] for s in used})<3: raise ValueError('Three distinct sources required')
    return resolved,bindings


def render_v3(payload, sources_json, *, bindings):
    from .work_research import RenderedReport, bound_sources, _text, _escape, _fact_evidence
    sources=bound_sources(sources_json); lines=['# '+_escape(_text(payload['title'],200)),'']; evidence=[]; cited=[]
    index=0
    for section in payload['sections']:
        sid=section['source_id']; source=sources[sid]
        if sid in cited: raise ValueError('Duplicate section')
        lines+=['## '+_escape(_text(section['heading'],200)),source['final_url'],'']
        for fact in section['facts']:
            card=bindings[index]; index+=1
            if card['source_id']!=sid: raise ValueError('Foreign citation')
            view=json.loads(card['view_json']); visible=dict(view['lines'])
            support=_fact_evidence(fact,source,visible)
            left,right=card['citation_first'],card['citation_last']
            support.update(citation_first=left,citation_last=right,citation_text='\n'.join(visible[i] for i in range(left,right+1)),domain=card['domain'])
            evidence.append(support)
            label={'documented':'文档说明','code':'代码观察','limitation':'该处标注'}[support['kind']]
            lines.append(f"- {label}（{card['domain']} L{left}–L{right}，依据 L{support['first_line']}–L{support['last_line']}）"+_escape(support['claim']))
        cited.append(sid); lines.append('')
    if index!=len(bindings) or len(cited)<3 or len({sources[s]['dedupe_url'] for s in cited})<3 or len({sources[s]['decoded_body_sha256'] for s in cited})<3:
        raise ValueError('Invalid v3 rendering bindings')
    return RenderedReport('\n'.join(lines),tuple(cited),tuple(evidence))
