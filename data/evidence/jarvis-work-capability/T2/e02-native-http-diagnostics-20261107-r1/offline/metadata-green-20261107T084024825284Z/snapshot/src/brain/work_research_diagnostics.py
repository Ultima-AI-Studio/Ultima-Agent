"""Bounded, request-local failure evidence. Never an acceptance/runtime packet."""
from __future__ import annotations
import copy
import hashlib
import json
import re
from .work_navigation import canonical_v3

CAP = 16384
KIND = 'research_failure_diagnostic_v3'
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


def validate_failure_diagnostic(raw,binding_key):
    """Closed data-only decoder for restricted exporters, not delivery verification."""
    _require(type(raw) is bytes and 0<len(raw)<=CAP)
    def pairs(items):
        value=dict(items);_require(len(value)==len(items));return value
    p=json.loads(raw,object_pairs_hook=pairs)
    _require(canonical_v3(p)==raw)
    _closed(p,'kind complete acceptance_credit binding_sha256 branch final_answer pages read_requests eligible_source_ids write_confirmed ack_confirmed budget last_http')
    _require(p['kind']==KIND and p['complete'] is False and type(p['acceptance_credit']) is int and p['acceptance_credit']==0)
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
    return dict(kind=KIND,complete=False,acceptance_credit=0,binding_sha256=hashlib.sha256(canonical_v3(list(ledger._navigation.binding_key))).hexdigest(),
        branch=branch,final_answer=final,pages=pages,read_requests=requests,last_http=_last_http(ledger,transport,wires),
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
            ledger._scan_output(packet)
            raw=canonical_v3(packet)
            validate_failure_diagnostic(raw,ledger._navigation.binding_key)
            ledger._failure_diagnostic=raw
            summary=dict(status='CAPTURED',kind=KIND,sha256=hashlib.sha256(raw).hexdigest(),branch=packet['branch'],
                pages=len(packet['pages']),reads_used=packet['budget']['reads_used'],write_confirmed=packet['write_confirmed'],
                ack_confirmed=packet['ack_confirmed'],complete=False,acceptance_credit=0)
        except Exception:
            pass
        ledger._failure_diagnostic_summary=copy.deepcopy(summary)
        return copy.deepcopy(summary)
