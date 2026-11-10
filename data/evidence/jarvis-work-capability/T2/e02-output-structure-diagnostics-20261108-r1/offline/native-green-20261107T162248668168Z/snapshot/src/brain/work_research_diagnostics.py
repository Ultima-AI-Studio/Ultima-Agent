"""Bounded, request-local failure evidence. Never an acceptance/runtime packet."""
from __future__ import annotations
import copy
import hashlib
import json
import re
from .work_navigation import canonical_v3

CAP = 16384
KIND = 'research_failure_diagnostic_v4'
LEGACY_KIND = 'research_failure_diagnostic_v3'
OUTPUT_KIND = 'research_failure_diagnostic_v5'
NATIVE_REASONS = frozenset(('extra_fields','model','done','done_reason','message_type','message_fields',
    'message_role','content_type','content_empty','prompt_eval_count','eval_count','completion_limit',
    'context_limit','total_duration','load_duration','prompt_eval_duration','eval_duration','created_at'))
BRANCHES = {'absent','action','unvalidated_response','final_before_write','write_without_ack','ack'}
HTTP_ROUTES = {('GET','/api/version','metadata'):'version',('GET','/api/tags','metadata'):'tags',('POST','/api/chat','chat'):'chat'}


def _require(value):
    if not value:raise ValueError('Invalid research failure diagnostic')


def _closed(value,fields):
    _require(type(value) is dict and set(value)==set(fields.split()))


def _count(value,limit):
    _require(type(value) is int and 0<=value<=limit)


def _digest(value):
    _require(type(value) is str and re.fullmatch('[0-9a-f]{64}',value) is not None)


def _source(value):
    _require(type(value) is str and re.fullmatch('S[1-5]',value) is not None)


def _validate_http(value,generations):
    if value is None:return
    _closed(value,'generation receipt_index route status send_reserved request_sha256 request_bytes downloaded inspected admitted retained transport_failed validated_response')
    _count(value['generation'],8);_require(1<=value['generation']<=generations)
    _count(value['receipt_index'],23)
    _require(value['route'] in ('version','tags','chat'))
    _digest(value['request_sha256']);_count(value['request_bytes'],2**63-1)
    for name in ('send_reserved','transport_failed','validated_response'):_require(type(value[name]) is bool)
    status=value['status']
    _require(status is None or (type(status) is int and 100<=status<=599))
    if value['downloaded'] is not None:_count(value['downloaded'],2**63-1)
    cap=65536 if value['route']=='chat' else 32768
    _count(value['inspected'],cap+1);_count(value['admitted'],cap);_count(value['retained'],cap)
    _require(value['retained']==value['admitted'] and value['inspected'] in (value['admitted'],value['admitted']+1))
    if value['downloaded'] is not None:_require(value['downloaded']>=value['admitted'])
    if value['route']!='chat':
        _require(value['request_bytes']==0 and value['request_sha256']==hashlib.sha256(b'').hexdigest())
    elif value['send_reserved']:_require(value['request_bytes']<=49152)
    if not value['send_reserved']:_require(status is None)
    if status is None:
        _require(value['transport_failed'] and value['downloaded'] is None and value['inspected']==value['admitted']==0)
    elif not 200<=status<300:
        _require(value['transport_failed'] and value['inspected']==value['admitted']==0)
    if value['validated_response']:
        _require(value['route']=='chat' and value['send_reserved'] and type(status) is int and 200<=status<300 and not value['transport_failed'])


def _last_http(ledger,transport,wires):
    """Project trusted metadata only; never inspect a failed response body."""
    receipts=getattr(transport,'receipts',[])
    _require(type(receipts) is list and len(receipts)<=24)
    if not receipts:return None
    receipt=receipts[-1];index=len(receipts)-1
    _require(type(receipt) is dict and type(receipt['send_reserved']) is bool)
    route=HTTP_ROUTES[(receipt['method'],receipt['path'],receipt['kind'])]
    timeline=ledger._timeline
    _require(type(timeline) is list and len(timeline)<=256)
    events=[e for e in timeline if e['kind'] in ('send','admission_refused') and e.get('receipt_index')==index]
    _require(len(events)==1 and type(events[0]['receipt_index']) is int)
    event=events[0];generation=event['generation']
    _require(event['kind']==('send' if receipt['send_reserved'] else 'admission_refused'))
    validated=False
    if route=='chat':
        matching=[w for w in wires if w.get('generation')==generation]
        _require(len(matching)<=1)
        if matching:
            wire=matching[0]
            _require(type(wire['generation']) is int and wire['hashes']['entity']==receipt['entity_sha256'])
            validated=type(wire.get('secured_envelope')) is dict
    return dict(generation=generation,receipt_index=index,route=route,status=receipt.get('status'),
        send_reserved=receipt['send_reserved'],request_sha256=receipt['entity_sha256'],request_bytes=receipt['entity_bytes'],
        downloaded=receipt['downloaded'],inspected=receipt['inspected'],admitted=receipt['admitted'],retained=receipt['retained'],
        transport_failed=receipt['error'] is not None,validated_response=validated)


def _validate_native(value,last):
    if value is None:return
    _closed(value,'generation receipt_index request_sha256 response_sha256 response_bytes reason max_tokens done done_reason prompt_eval_count eval_count content_chars')
    _require(type(value['reason']) is str and value['reason'] in NATIVE_REASONS)
    _require(type(value['max_tokens']) is int and value['max_tokens'] in (256,2048))
    _require(value['done'] is None or type(value['done']) is bool)
    _require(type(value['done_reason']) is str and value['done_reason'] in ('stop','length','missing','other','type'))
    for k in ('prompt_eval_count','eval_count'):
        _require(value[k] is None or (type(value[k]) is int and -(2**63)<=value[k]<2**63))
    if value['content_chars'] is not None:_count(value['content_chars'],65536)
    _digest(value['request_sha256']);_digest(value['response_sha256'])
    _count(value['generation'],8);_count(value['receipt_index'],23);_count(value['response_bytes'],65536)
    _require(last is not None and last['route']=='chat' and last['send_reserved'] and not last['transport_failed']
        and type(last['status']) is int and 200<=last['status']<300 and not last['validated_response'])
    for k in ('generation','receipt_index','request_sha256'):_require(value[k]==last[k])
    _require(0<value['response_bytes']==last['admitted']==last['inspected']==last['retained'])


def _bound_native(transport,last,value):
    _validate_native(value,last)
    if value is not None:
        receipt=transport.receipts[-1]
        _require(value['response_sha256']==receipt['response_sha256'])
        _require(value['generation']==transport.generations)
    return copy.deepcopy(value)


def record_native_response_rejection(ledger,transport,raw_bytes,raw,max_tokens,reason,*,request_context=None):
    """Retain only a closed projection of a fully received, request-bound refusal."""
    _require(type(raw_bytes) is bytes and 0<len(raw_bytes)<=65536 and type(raw) is dict)
    def integer(value):return value if type(value) is int and -(2**63)<=value<2**63 else None
    done_reason=raw.get('done_reason')
    normalized=('missing' if 'done_reason' not in raw else 'type' if type(done_reason) is not str
        else done_reason if done_reason in ('stop','length') else 'other')
    message=raw.get('message');content=message.get('content') if type(message) is dict else None
    last=_last_http(ledger,transport,getattr(ledger,'_runtime_wires',[]))
    _validate_http(last,transport.generations)
    _require(last is not None)
    value=dict(generation=transport.generations,receipt_index=len(transport.receipts)-1,
        request_sha256=last['request_sha256'],response_sha256=hashlib.sha256(raw_bytes).hexdigest(),
        response_bytes=len(raw_bytes),reason=reason,max_tokens=max_tokens,
        done=raw.get('done') if type(raw.get('done')) is bool else None,done_reason=normalized,
        prompt_eval_count=integer(raw.get('prompt_eval_count')),eval_count=integer(raw.get('eval_count')),
        content_chars=len(content) if type(content) is str and len(content)<=65536 else None)
    ledger._native_response_rejection=_bound_native(transport,last,value)
    if request_context is not None:
        try:
            _closed(request_context,'entity strict_schema ack')
            ledger._output_structure=build_output_structure(raw,**request_context,max_tokens=max_tokens,
                scan=ledger._scan_output,native_record=ledger._native_response_rejection)
        except Exception:
            pass  # The original native refusal remains available as v4.


def validate_failure_diagnostic(raw,binding_key):
    """Closed data-only decoder for restricted exporters, not delivery verification."""
    _require(type(raw) is bytes and 0<len(raw)<=CAP)
    def pairs(items):
        value=dict(items);_require(len(value)==len(items));return value
    p=json.loads(raw,object_pairs_hook=pairs)
    _require(canonical_v3(p)==raw)
    _require(type(p) is dict and p.get('kind') in (LEGACY_KIND,KIND,OUTPUT_KIND))
    fields='kind complete acceptance_credit binding_sha256 branch final_answer pages read_requests eligible_source_ids write_confirmed ack_confirmed budget last_http'
    _closed(p,fields+(' native_response' if p['kind']!=LEGACY_KIND else '')
        +(' output_structure' if p['kind']==OUTPUT_KIND else ''))
    _require(p['complete'] is False and type(p['acceptance_credit']) is int and p['acceptance_credit']==0)
    _require(p['binding_sha256']==hashlib.sha256(canonical_v3(list(binding_key))).hexdigest())
    _require(p['branch'] in BRANCHES)
    for name in ('write_confirmed','ack_confirmed'):_require(type(p[name]) is bool)
    final=p['final_answer']
    if final is not None:
        _closed(final,'text length sha256')
        _require(type(final['text']) is str and final['text'].strip() and 0<len(final['text'])<=1000)
        _require(type(final['length']) is int and final['length']==len(final['text']))
        _require(final['sha256']==hashlib.sha256(final['text'].encode('utf8')).hexdigest())
    _require(type(p['pages']) is list and len(p['pages'])<=6)
    eligible=set()
    for page in p['pages']:
        _closed(page,'source_id requested_start range confirmed visible view_sha256 cards')
        _source(page['source_id']);_count(page['requested_start'],2**31-1);_require(page['requested_start']>0)
        _require(type(page['range']) is list and len(page['range'])==2)
        for number in page['range']:_count(number,2**31-1)
        _require(page['requested_start']==page['range'][0]<=page['range'][1])
        _digest(page['view_sha256'])
        for name in ('confirmed','visible'):_require(type(page[name]) is bool)
        _require(type(page['cards']) is list and len(page['cards'])<=8)
        for card in page['cards']:
            _closed(card,'id kind anchor context')
            _require(type(card['id']) is str and re.fullmatch(r'N3\.[0-9a-f]{16}',card['id']) is not None)
            _require(card['kind'] in ('documented','code','limitation'))
            for key in ('anchor','context'):
                _require(type(card[key]) is list and len(card[key])==2)
                for number in card[key]:_count(number,2**31-1)
            a,z=card['anchor'];left,right=card['context']
            _require(page['range'][0]<=left<=a<=z<=right<=page['range'][1])
        if page['confirmed'] and page['cards']:eligible.add(page['source_id'])
    _require(p['eligible_source_ids']==sorted(eligible))
    _require(type(p['read_requests']) is list and len(p['read_requests'])<=6)
    for request in p['read_requests']:
        _closed(request,'source_id start_line');_source(request['source_id']);_count(request['start_line'],2**31-1);_require(request['start_line']>0)
    b=p['budget'];_closed(b,'reads_used reads_limit read_bytes native_posts native_posts_limit completed_posts generations deadline_remaining_microseconds write_admission_open')
    _require(type(b['reads_limit']) is int and b['reads_limit']==6 and type(b['native_posts_limit']) is int and b['native_posts_limit']==8)
    for key,limit in [('reads_used',6),('read_bytes',18432),('native_posts',8),('completed_posts',8),('generations',64)]:_count(b[key],limit)
    _require(b['completed_posts']<=b['native_posts'] and len(p['pages'])<=b['reads_used'])
    _validate_http(p['last_http'],b['generations'])
    if p['kind']!=LEGACY_KIND:
        _validate_native(p['native_response'],p['last_http'])
        if p['native_response'] is not None:_require(p['branch'] in ('unvalidated_response','write_without_ack'))
    if p['kind']==OUTPUT_KIND:
        _validate_output_structure(p['output_structure'],p['native_response'],p['last_http'])
        _require(p['output_structure']['request']['ack']==p['write_confirmed'])
    remaining_us=b['deadline_remaining_microseconds']
    _require(type(remaining_us) is int and -(2**63)<=remaining_us<2**63)
    _require(type(b['write_admission_open']) is bool and b['write_admission_open']==(remaining_us>=55000000))
    _require(not p['ack_confirmed'] or p['write_confirmed'])
    _require((p['branch']=='ack')==p['ack_confirmed'])
    _require(p['branch']!='write_without_ack' or (p['write_confirmed'] and not p['ack_confirmed']))
    _require(p['branch']!='final_before_write' or (final is not None and not p['write_confirmed']))
    _require(final is None or p['branch'] in ('final_before_write','ack'))
    return p


def _project(ledger):
    from .work_tools import monotonic
    wires=getattr(ledger,'_runtime_wires',[])
    _require(type(wires) is list and len(wires)<=8)
    transport=getattr(ledger,'_runtime_transport',None)
    generations=getattr(transport,'generations',0)
    last=wires[-1] if wires else {}
    current=bool(last and last.get('generation')==generations and type(last.get('secured_envelope')) is dict)
    envelope=last['secured_envelope'] if current else {}
    write=any(s.get('confirmed') is True and s.get('view') is None for s in ledger._staged.values())
    ack=type(getattr(ledger,'_runtime_final',None)) is bytes and bool(ledger._runtime_final)
    final=None
    if current and set(envelope)=={'final_answer'}:
        value=envelope['final_answer']
        _require(type(value) is str and value.strip() and len(value)<=1000)
        ledger._scan_output(value)
        final=dict(text=value,length=len(value),sha256=hashlib.sha256(value.encode('utf8')).hexdigest())
    branch=('ack' if ack else 'write_without_ack' if write else 'final_before_write' if final is not None
        else 'action' if current else 'unvalidated_response' if generations else 'absent')
    if branch=='write_without_ack':final=None
    pages=[]
    for _,staged in sorted(ledger._staged.items()):
        view=staged.get('view')
        if view is None:continue
        cards=json.loads(view.cards_json)
        pages.append(dict(source_id=view.source_id,requested_start=staged['metadata']['arguments']['start_line'],range=[view.start,view.end],
            confirmed=staged['confirmed'],visible=staged['promoted'],view_sha256=view.wire_sha256,
            cards=[dict(id=c[0],kind=c[1],anchor=c[3:5],context=c[5:7]) for c in cards]))
    requests=[]
    for raw in ledger._runtime_events:
        event=json.loads(raw);data=event['data']
        if event['type']=='tool_call_start' and data.get('tool')=='ultima_work_research_inspect':
            requests.append(dict(source_id=data['arguments']['source_id'],start_line=data['arguments']['start_line']))
    remaining=ledger.deadline-monotonic()
    numerator,denominator=remaining.as_integer_ratio()
    remaining_us=numerator*1000000//denominator
    last_http=_last_http(ledger,transport,wires)
    native=_bound_native(transport,last_http,getattr(ledger,'_native_response_rejection',None))
    return dict(kind=KIND,complete=False,acceptance_credit=0,binding_sha256=hashlib.sha256(canonical_v3(list(ledger._navigation.binding_key))).hexdigest(),
        branch=branch,final_answer=final,pages=pages,read_requests=requests,last_http=last_http,native_response=native,
        eligible_source_ids=sorted({p['source_id'] for p in pages if p['confirmed'] and p['cards']}),write_confirmed=write,ack_confirmed=ack,
        budget=dict(reads_used=ledger._read_count,reads_limit=6,read_bytes=ledger._read_bytes,native_posts=getattr(transport,'posts',0),native_posts_limit=8,
            completed_posts=getattr(transport,'completed',0),generations=generations,deadline_remaining_microseconds=remaining_us,write_admission_open=remaining>=55))


def capture_failure(ledger):
    """Freeze once after failure; return only public metadata, never private text."""
    with ledger._lock:
        if hasattr(ledger,'_failure_diagnostic_summary'):return copy.deepcopy(ledger._failure_diagnostic_summary)
        if ledger._navigation is None:return None
        summary=dict(status='UNAVAILABLE',reason='DIAGNOSTIC_CAPTURE_FAILED',complete=False,acceptance_credit=0)
        try:
            packet=_project(ledger)
            snapshot=getattr(ledger,'_output_structure',None)
            if snapshot is not None:
                try:
                    enriched=attach_output_structure(packet,snapshot,ledger._scan_output)
                    validate_failure_diagnostic(canonical_v3(enriched),ledger._navigation.binding_key)
                    packet=enriched
                except Exception:
                    pass
            ledger._scan_output(packet)
            raw=canonical_v3(packet)
            validate_failure_diagnostic(raw,ledger._navigation.binding_key)
            ledger._failure_diagnostic=raw
            summary=dict(status='CAPTURED',kind=packet['kind'],sha256=hashlib.sha256(raw).hexdigest(),branch=packet['branch'],
                pages=len(packet['pages']),reads_used=packet['budget']['reads_used'],write_confirmed=packet['write_confirmed'],
                ack_confirmed=packet['ack_confirmed'],complete=False,acceptance_credit=0)
        except Exception:
            pass
        ledger._failure_diagnostic_summary=copy.deepcopy(summary)
        return copy.deepcopy(summary)


_NATIVE_BINDING='generation receipt_index request_sha256 response_sha256 response_bytes content_chars max_tokens'
_MESSAGE_FIELDS={'role','content','thinking','tool_calls','images'}
_PATH_FIELDS={'action','action_input','path','title','sections','source_id','heading','facts','claim','evidence_id','final_answer','OTHER'}
_SCHEMA_KEYWORDS={'type','enum','required','additionalProperties','minItems','maxItems','minLength','maxLength','pattern','anyOf','oneOf','allOf','additionalItems','OTHER'}
_JSON_ERRORS={'UNTERMINATED_STRING','EXPECTED_VALUE','EXPECTED_DELIMITER','JSON_SYNTAX','STRICT_JSON_REJECTED'}


def _text_measure(value,exists=True):
    kind=('missing' if not exists else 'string' if type(value) is str else 'null' if value is None
        else 'boolean' if type(value) is bool else 'number' if type(value) in (int,float)
        else 'array' if type(value) is list else 'object' if type(value) is dict else 'other')
    out=dict(type=kind,chars=None,bytes=None,sha256=None)
    if kind=='string':
        out['chars']=len(value)
        try:
            data=value.encode('utf8');out.update(bytes=len(data),sha256=hashlib.sha256(data).hexdigest())
        except UnicodeError:pass
    return out


def _parse_content(content):
    from .agent_server import _strict_json
    try:return _strict_json(content),None
    except json.JSONDecodeError as exc:
        kind={'Unterminated string starting at':'UNTERMINATED_STRING','Expecting value':'EXPECTED_VALUE',
            "Expecting ',' delimiter":'EXPECTED_DELIMITER'}.get(exc.msg,'JSON_SYNTAX')
        return None,dict(kind=kind,pos=exc.pos,line=exc.lineno,column=exc.colno)
    except ValueError:return None,dict(kind='STRICT_JSON_REJECTED',pos=None,line=None,column=None)


def _shape(value):
    if type(value) is not dict:return None
    args=value.get('action_input')
    if type(args) is not dict:return None
    length=lambda v:len(v) if type(v) is str else None
    sections=args.get('sections');out=[]
    for section in sections[:5] if type(sections) is list else []:
        section=section if type(section) is dict else {};facts=section.get('facts')
        claims=[length(f.get('claim')) if type(f) is dict else None for f in facts[:6]] if type(facts) is list else []
        out.append(dict(heading_chars=length(section.get('heading')),facts_total=len(facts) if type(facts) is list else None,
            claim_chars=claims,complete=type(facts) is list and len(facts)<=6 and all(v is not None for v in claims)))
    return dict(title_chars=length(args.get('title')),sections_total=len(sections) if type(sections) is list else None,
        sections=out,complete=type(sections) is list and len(sections)<=5 and all(s['complete'] for s in out))


def build_output_structure(raw,entity,strict_schema,ack,max_tokens,scan,*,native_record):
    """Observe already received data; never repair it or dispatch its contents."""
    from .agent_server import _strict_json,_research_sampler_schema
    from jsonschema import Draft7Validator
    _require(type(entity) is bytes and 0<len(entity)<=49152 and type(ack) is bool)
    request=_strict_json(entity.decode('utf8'));sampler=_research_sampler_schema(strict_schema)
    _require(request['format']==sampler and request['options']['num_predict']==max_tokens)
    binding={k:native_record[k] for k in _NATIVE_BINDING.split()}
    _require(hashlib.sha256(entity).hexdigest()==binding['request_sha256'])
    actions=set();sources=set();refs=set()
    def visit(node):
        if type(node) is dict:
            for name,spec in node.get('properties',{}).items():
                values=spec.get('enum',[]) if type(spec) is dict else []
                if name=='action':actions.update(values)
                if name=='source_id':sources.update(values)
                if name=='evidence_id':refs.update(values)
            for child in node.values():visit(child)
        elif type(node) is list:
            for child in node:visit(child)
    visit(strict_schema)
    req=dict(sha256=binding['request_sha256'],bytes=len(entity),ack=ack,options=request['options'],
        flags={k:request[k] for k in ('think','stream','truncate','shift')},
        strict_sha256=hashlib.sha256(canonical_v3(strict_schema)).hexdigest(),strict_bytes=len(canonical_v3(strict_schema)),
        sampler_sha256=hashlib.sha256(canonical_v3(sampler)).hexdigest(),sampler_bytes=len(canonical_v3(sampler)),
        allowed_actions=sorted(actions),source_ids=sorted(sources),evidence_ids_count=len(refs))
    message=raw.get('message');obj=message if type(message) is dict else {}
    content=obj.get('content');measure=_text_measure(content,'content' in obj)
    role=obj.get('role');role=('missing' if 'role' not in obj else 'assistant' if role=='assistant'
        else 'other' if type(role) is str else 'type')
    msg=dict(type=_text_measure(message,'message' in raw)['type'],known_fields=sorted(set(obj)&_MESSAGE_FIELDS),
        unknown_fields=len(set(obj)-_MESSAGE_FIELDS),role=role,content=measure,
        thinking=_text_measure(obj.get('thinking'),'thinking' in obj))
    info=dict(status='NON_STRING',error=None,schema_valid=None,schema_error=None,branch=None,shape=None)
    evidence=dict(mode='UNAVAILABLE',fragments=[],omitted_chars=measure['chars'])
    if type(content) is str and measure['bytes'] is not None:
        info['status']='UNAVAILABLE'
        try:
            value,error=_parse_content(content)
            if error:info.update(status='INVALID',error=error)
            else:
                issue=next(Draft7Validator(strict_schema).iter_errors(value),None)
                issue_view=None
                if issue is not None:
                    issue_view=dict(keyword=issue.validator if issue.validator in _SCHEMA_KEYWORDS else 'OTHER',
                        path=[v if type(v) is int and 0<=v<=65536 else v if type(v) is str and v in _PATH_FIELDS else 'OTHER'
                            for v in list(issue.absolute_path)[:12]])
                branch=({'ultima_work_research_write':'write','ultima_work_research_inspect':'inspect'}.get(value.get('action'),'other')
                    if type(value) is dict else 'other')
                if type(value) is dict and set(value)=={'final_answer'}:branch='final'
                info.update(status='COMPLETE',schema_valid=issue is None,schema_error=issue_view,branch=branch,shape=_shape(value))
        except (ValueError,TypeError,RecursionError):pass
        try:
            scan(content)
            evidence=dict(mode='FULL',fragments=[dict(start=0,end=len(content),text=content)],omitted_chars=0)
        except Exception:evidence=dict(mode='OMITTED_POLICY',fragments=[],omitted_chars=len(content))
    elif type(content) is str:info['status']='UNAVAILABLE'
    return dict(native_binding=binding,request=req,message=msg,json=info,evidence=evidence)


def _validate_measure(value):
    _closed(value,'type chars bytes sha256')
    _require(value['type'] in ('missing','string','null','boolean','number','array','object','other'))
    if value['type']!='string':_require(all(value[k] is None for k in ('chars','bytes','sha256')));return
    _count(value['chars'],65536)
    if value['bytes'] is None:_require(value['sha256'] is None);return
    _count(value['bytes'],65536);_digest(value['sha256'])
    _require(value['chars']<=value['bytes']<=value['chars']*4)


def _validate_output_structure(value,native,last):
    _require(native is not None and last is not None)
    _closed(value,'native_binding request message json evidence')
    binding=value['native_binding'];_closed(binding,_NATIVE_BINDING)
    _require(binding=={k:native[k] for k in _NATIVE_BINDING.split()})
    req=value['request']
    _closed(req,'sha256 bytes ack options flags strict_sha256 strict_bytes sampler_sha256 sampler_bytes allowed_actions source_ids evidence_ids_count')
    _require(req['sha256']==native['request_sha256'] and type(req['bytes']) is int and req['bytes']==last['request_bytes'])
    _require(type(req['ack']) is bool and 0<req['bytes']<=49152)
    _closed(req['flags'],'think stream truncate shift');_require(all(v is False for v in req['flags'].values()))
    options=req['options'];_closed(options,'num_ctx num_predict temperature')
    _require(type(options['num_ctx']) is int and options['num_ctx']==16384)
    _require(type(options['num_predict']) is int and options['num_predict']==native['max_tokens'])
    _require(type(options['temperature']) in (int,float) and options['temperature']==0)
    for key in ('strict','sampler'):
        _digest(req[key+'_sha256']);_count(req[key+'_bytes'],49152);_require(req[key+'_bytes']>0)
    _require(type(req['allowed_actions']) is list and len(req['allowed_actions'])<=2)
    _require(all(type(x) is str and x in ('ultima_work_research_inspect','ultima_work_research_write') for x in req['allowed_actions']))
    _require(req['allowed_actions']==sorted(set(req['allowed_actions'])))
    _require(not req['ack'] or req['allowed_actions']==[])
    _require(type(req['source_ids']) is list and len(req['source_ids'])<=5)
    for sid in req['source_ids']:_source(sid)
    _require(req['source_ids']==sorted(set(req['source_ids'])));_count(req['evidence_ids_count'],48)
    msg=value['message'];_closed(msg,'type known_fields unknown_fields role content thinking')
    _require(msg['type'] in ('missing','string','null','boolean','number','array','object','other'))
    _require(type(msg['known_fields']) is list and len(msg['known_fields'])<=5 and all(type(x) is str and x in _MESSAGE_FIELDS for x in msg['known_fields']))
    _require(msg['known_fields']==sorted(set(msg['known_fields'])));_count(msg['unknown_fields'],65536)
    _require(msg['role'] in ('missing','assistant','other','type'))
    for key in ('content','thinking'):
        _validate_measure(msg[key]);_require((key in msg['known_fields'])==(msg[key]['type']!='missing'))
    content=msg['content'];_require(content['chars']==native['content_chars'])
    info=value['json'];_closed(info,'status error schema_valid schema_error branch shape')
    _require(info['status'] in ('COMPLETE','INVALID','NON_STRING','UNAVAILABLE'))
    if info['status']=='COMPLETE':
        _require(content['type']=='string' and content['bytes'] is not None and info['error'] is None)
        _require(type(info['schema_valid']) is bool and info['branch'] in ('write','inspect','final','other'))
        _require((info['schema_error'] is None)==info['schema_valid'])
    else:
        _require(all(info[k] is None for k in ('schema_valid','schema_error','branch','shape')))
        _require((info['error'] is not None)==(info['status']=='INVALID'))
        if info['status']=='NON_STRING':_require(content['type']!='string')
    if info['error'] is not None:
        error=info['error'];_closed(error,'kind pos line column');_require(error['kind'] in _JSON_ERRORS)
        _require(content['type']=='string')
        if error['kind']=='STRICT_JSON_REJECTED':_require(all(error[k] is None for k in ('pos','line','column')))
        else:
            _count(error['pos'],content['chars'])
            for key in ('line','column'):_count(error[key],content['chars']+1);_require(error[key]>0)
    if info['schema_error'] is not None:
        issue=info['schema_error'];_closed(issue,'keyword path')
        _require(issue['keyword'] in _SCHEMA_KEYWORDS and type(issue['path']) is list and len(issue['path'])<=12)
        _require(all((type(x) is int and 0<=x<=65536) or (type(x) is str and x in _PATH_FIELDS) for x in issue['path']))
    shape=info['shape']
    def nullable_count(v):
        if v is not None:_count(v,65536)
    if shape is not None:
        _closed(shape,'title_chars sections_total sections complete')
        nullable_count(shape['title_chars']);nullable_count(shape['sections_total'])
        _require(type(shape['complete']) is bool and type(shape['sections']) is list)
        _require(len(shape['sections'])==(min(shape['sections_total'],5) if shape['sections_total'] is not None else 0))
        for section in shape['sections']:
            _closed(section,'heading_chars facts_total claim_chars complete')
            nullable_count(section['heading_chars']);nullable_count(section['facts_total'])
            _require(type(section['complete']) is bool and type(section['claim_chars']) is list)
            _require(len(section['claim_chars'])==(min(section['facts_total'],6) if section['facts_total'] is not None else 0))
            for length in section['claim_chars']:nullable_count(length)
            _require(section['complete']==(section['facts_total'] is not None and section['facts_total']<=6 and all(v is not None for v in section['claim_chars'])))
        _require(shape['complete']==(shape['sections_total'] is not None and shape['sections_total']<=5 and all(s['complete'] for s in shape['sections'])))
    evidence=value['evidence'];_closed(evidence,'mode fragments omitted_chars')
    _require(evidence['mode'] in ('FULL','EXCERPTS','OMITTED_POLICY','OMITTED_BUDGET','UNAVAILABLE'))
    _require(type(evidence['fragments']) is list and len(evidence['fragments'])<=3)
    count=0;end=0
    for fragment in evidence['fragments']:
        _closed(fragment,'start end text');_require(content['type']=='string' and content['bytes'] is not None)
        _count(fragment['start'],content['chars']);_count(fragment['end'],content['chars'])
        _require(end<=fragment['start']<=fragment['end'] and type(fragment['text']) is str)
        _require(len(fragment['text'])==fragment['end']-fragment['start']);fragment['text'].encode('utf8')
        count+=len(fragment['text']);end=fragment['end']
    _require(evidence['omitted_chars']==(None if content['chars'] is None else content['chars']-count))
    if evidence['mode']=='FULL':
        _require(len(evidence['fragments'])==1 and evidence['omitted_chars']==0)
        fragment=evidence['fragments'][0];_require(fragment['start']==0 and fragment['end']==content['chars'])
        _require(_text_measure(fragment['text'])==content)
    elif evidence['mode']=='EXCERPTS':
        _require(len(evidence['fragments'])>0 and type(evidence['omitted_chars']) is int and evidence['omitted_chars']>0)
        _require(all(f['end']>f['start'] for f in evidence['fragments']))
    else:_require(not evidence['fragments'])


def attach_output_structure(packet,snapshot,scan):
    """Fit a failure-only projection without deleting any original v4 evidence."""
    _validate_output_structure(snapshot,packet['native_response'],packet['last_http'])
    def pack(value):
        candidate=dict(packet,kind=OUTPUT_KIND,output_structure=value)
        scan(candidate)
        scan(''.join(f['text'] for f in value['evidence']['fragments']))
        return candidate if len(canonical_v3(candidate))<=CAP else None
    result=pack(snapshot)
    if result is not None:return result
    if snapshot['evidence']['mode']!='FULL':return packet
    content=snapshot['evidence']['fragments'][0]['text'];size=len(content)
    position=(snapshot['json']['error'] or {}).get('pos')
    for width in (1024,512,256,128,64,0):
        spans=[]
        if width:
            spans=[(0,min(size,width)),(max(0,size-2*width),size)]
            if position is not None:spans.append((max(0,position-width//2),min(size,position+width//2)))
        merged=[]
        for start,end in sorted(spans):
            if end<=start:continue
            if merged and start<=merged[-1][1]:merged[-1][1]=max(merged[-1][1],end)
            else:merged.append([start,end])
        value=copy.deepcopy(snapshot)
        fragments=[dict(start=a,end=z,text=content[a:z]) for a,z in merged]
        omitted=size-sum(z-a for a,z in merged)
        value['evidence']=dict(mode='OMITTED_BUDGET' if not fragments else 'EXCERPTS' if omitted else 'FULL',
            fragments=fragments,omitted_chars=omitted)
        try:result=pack(value)
        except Exception:
            value['evidence']=dict(mode='OMITTED_POLICY',fragments=[],omitted_chars=size);result=pack(value)
        if result is not None:return result
    return packet
