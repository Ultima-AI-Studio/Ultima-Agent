"""Bounded research collection/rendering around installed SDK tools, not an Agent."""
from dataclasses import dataclass
import hashlib
import json
import re
import time
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


URL_PATTERN=re.compile(r'https?://[^\s<>"\x27]+')


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


def render_research_report(payload,sources_json):
    if not isinstance(payload,dict) or set(payload)!={'path','title','sections'}:
        raise ValueError('Report requires only path, title and sections')
    sources=bound_sources(sources_json)
    title=_text(payload['title'],200)
    sections=payload['sections']
    if not isinstance(sections,list) or not 3<=len(sections)<=5:
        raise ValueError('Report needs three to five source sections')
    lines=['# '+_escape(title),'']; cited=[]
    for section in sections:
        if not isinstance(section,dict) or set(section)!={'source_id','heading','facts'}:
            raise ValueError('A source section requires only source_id, heading and facts')
        source_id=section['source_id']
        if not isinstance(source_id,str) or source_id not in sources or source_id in cited:
            raise ValueError('Unknown, duplicate or unbound source ID')
        facts=section['facts']
        if not isinstance(facts,list) or not 1<=len(facts)<=6: raise ValueError('Source section requires one to six facts')
        lines+=['## '+_escape(_text(section['heading'],200)),sources[source_id]['final_url'],'']
        lines+=['- '+_escape(_text(fact,2000)) for fact in facts]
        lines.append(''); cited.append(source_id)
    if len({sources[s]['dedupe_url'] for s in cited})<3 or len({sources[s]['decoded_body_sha256'] for s in cited})<3:
        raise ValueError('Report requires three distinct cited source URL/body identities')
    return RenderedReport('\n'.join(lines),tuple(cited))


def verify_research_artifacts(binding,artifacts,report_records,sources_json):
    from .work_tools import checked_path
    source_map=bound_sources(sources_json,binding)
    if not report_records: raise ValueError('No successful bound research report write')
    reports={r['result']['file_call_id']:r for r in report_records}
    cited=set()
    for artifact in artifacts:
        record=reports.get(artifact['call_id'])
        if not record or any(record.get(k)!=getattr(binding,k) for k in ('request_id','session_id','task_id')):
            raise ValueError('Research artifact has no current report-to-file call linkage')
        rendered=render_research_report(json.loads(record['result']['payload_json']),sources_json)
        raw=checked_path(binding,artifact['path']).read_bytes()
        if hashlib.sha256(raw).hexdigest()!=artifact['sha256'] or raw.decode('utf8').replace('\r\n','\n')!=rendered.content.replace('\r\n','\n'):
            raise ValueError('Research rendered report independent readback mismatch')
        if list(rendered.cited_source_ids)!=record['result']['cited_source_ids']:
            raise ValueError('Research citation receipt mismatch')
        cited.update(rendered.cited_source_ids)
    if len(cited)<3: raise ValueError('Research has fewer than three actually cited fetched sources')
    return [source_map[s] for s in source_map if s in cited]
