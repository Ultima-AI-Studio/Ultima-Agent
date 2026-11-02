"""Independent oracles for safe research navigation; no live sockets."""
import dataclasses
import hashlib
import importlib.util
import json
import socket
import time
from types import SimpleNamespace
import uuid
import pytest
from src.brain import work_research as research


@pytest.fixture(autouse=True)
def stable_navigation_entropy(monkeypatch):
    """Reproducible protocol fixtures; real production entropy is unchanged."""
    import itertools,secrets
    counter=itertools.count(1000)
    monkeypatch.setattr(uuid,'uuid4',lambda:uuid.UUID(int=next(counter)))
    monkeypatch.setattr(secrets,'token_bytes',lambda n:bytes(range(n)))


def nav():
    assert importlib.util.find_spec('src.brain.work_navigation'), 'v3 safe navigation module missing'
    from src.brain import work_navigation
    return work_navigation


def j(x):
    return json.dumps(x, sort_keys=True, ensure_ascii=False, allow_nan=False, separators=(',', ':')).encode()


def h(x):
    return hashlib.sha256(x).hexdigest()


@pytest.fixture(autouse=True)
def deny_network(monkeypatch):
    def denied(*a, **kw):
        raise AssertionError('live network forbidden')
    monkeypatch.setattr(socket.socket, 'connect', denied)
    monkeypatch.setattr(socket, 'getaddrinfo', denied)


def policy(mode='warn'):
    from openjarvis.security.scanner import SecretScanner, PIIScanner
    return nav().make_scan_policy((SecretScanner(), PIIScanner()), mode)


def fixture(texts=None, suffix='.md', html=False):
    texts = texts or ['Source one explains local usage.', 'Source two records its conditions.', 'Source three documents alternatives.']
    sources, records, attempts, trace = [], [], [], []
    binding = SimpleNamespace(request_id='request', session_id='session', task_id='task')
    ids = vars(binding)
    for i, text in enumerate(texts, 1):
        call = str(uuid.UUID(int=i))
        sdk = str(uuid.UUID(int=100+i))
        url = f'https://example.org/source{i}{suffix}'
        body = '<p>'+text+'</p><script>hidden()</script><style>hidden</style>' if html else text
        raw = dict(success=True, requested_url=url, final_url=url, dedupe_url=url, source_id=f'original{i}', fetched_at='fixed', status_code=200, content_type='text/html' if html else 'text/plain', truncated=False, body=body, text=text, decoded_body_sha256=h(body.encode()))
        sources.append(dict(raw, source_id=f'S{i}', adapter_source_id=raw['source_id'], read_call_id=call, **ids))
        records.append(dict(call_id=call, tool_name='ultima_work_http_get', success=True, result=raw, **ids))
        attempts.append(dict(sdk_call_id=sdk, adapter_call_id=call, tool_name='ultima_work_http_get', success=True, **ids))
        for kind in ('tool_call_start', 'tool_call_end'):
            data=dict(tool='ultima_work_http_get',arguments=dict(url=url)) if kind=='tool_call_start' else dict(tool='ultima_work_http_get',success=True,metadata=dict(records[-1]))
            trace.append(dict(sdk_call_id=sdk, type=kind, data=data, **ids))
    collection = research.ResearchCollection(json.dumps(sources), json.dumps(trace), json.dumps(attempts), (), 'question')
    return collection, binding, j(records)


def prepare(texts=None, **kw):
    c, b, records = fixture(texts, **kw)
    p = policy()
    return research.prepare_navigation(c, b, p, get_records_json=records, deadline=time.monotonic()+30), c, b, records, p


def key(seq=1):
    return nav().PageKey(1, seq, str(uuid.UUID(int=30+seq)), str(uuid.UUID(int=60+seq)))


def test_v3_canonical_identity_replay():
    n = nav()
    assert n.canonical_v3({'z':'汉字','a':[True,None,1]}) == j({'z':'汉字','a':[True,None,1]})
    for bad in (1.0, float('nan'), {'x':'\ud800'}, {1:'key'}, (1,), {'x':b'bytes'}):
        with pytest.raises((ValueError, TypeError)): n.canonical_v3(bad)
    cat, *_ = prepare()
    page = n.build_page(cat, 'S1', 1, key())
    wire = json.loads(page.wire_json)
    identity = json.loads(cat.sources[0].identity_json)
    expected = h(j(['view3',cat.nonce,list(cat.binding_key),identity,1,1,1,key().dispatch_uuid,key().adapter_uuid]))
    assert page.view_id == expected
    ref, kind, op, a, z, left, right = wire['cards'][0]
    pairs = wire['lines']
    assert ref == 'N3.'+h(j(['card3',expected,kind,op,a,z,left,right,h(j(pairs)),h(j(pairs))]))[:16]
    for changed in (dataclasses.replace(cat,nonce='a'*32),dataclasses.replace(cat,binding_key=('other','session','task'))):
        assert n.build_page(changed,'S1',1,key()).view_id != expected
    assert n.build_page(cat,'S1',1,key(2)).view_id != expected
    for field in ('dispatch_uuid','adapter_uuid'):
        changed=dataclasses.replace(key(),**{field:str(uuid.UUID(int=999))})
        assert n.build_page(cat,'S1',1,changed).view_id != expected
    with pytest.raises(ValueError): n.build_page(cat,'S1',1,dataclasses.replace(key(),dispatch_uuid=key().dispatch_uuid.upper().replace('-', '')))


@pytest.mark.parametrize('mode',['block','warn','redact'])
def test_v3_line_security_projection(mode):
    n = nav()
    text = 'Safe 文本\r\npassword = "syntheticsecret"\nSafe tail.'
    c,b,r = fixture([text,'Other safe source.','Another safe source.','Fourth safe source.'])
    cat = research.prepare_navigation(c,b,policy(mode),get_records_json=r,deadline=time.monotonic()+30)
    source = cat.sources[0]
    assert 'syntheticsecret' not in repr(source)
    if mode == 'block': assert not source.available
    else:
        assert dict(source.safe_line_pairs) == {1:'Safe 文本',3:'Safe tail.'}
        page = json.loads(n.build_page(cat,'S1',1,key()).wire_json)
        assert page['omissions'] == [[2,2,'security']]
        assert all(not (card[5] <= 2 <= card[6]) for card in page['cards'])


@pytest.mark.parametrize('suffix',['','.md','.rst','.txt','.htm','.html','.adoc','.ts','.py','.unknown'])
def test_v3_html_suffix_and_renderable_availability(suffix):
    n = nav()
    c,b,r = fixture(suffix=suffix, html=True)
    if suffix in ('.ts','.py','.unknown'):
        with pytest.raises(ValueError,match='three'): research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)
    else:
        cat = research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)
        page = n.build_page(cat,'S1',1,key())
        assert b'hidden' not in page.wire_json
        assert json.loads(page.wire_json)['cards'][0][1] == 'documented'
        assert cat.sources[0].domain == 'extracted-text'


@pytest.mark.parametrize('fault',['body','projection','get','truncated','duplicate','coordinates','raw_html_secret'])
def test_v3_provenance_rejects_before_composition(fault):
    n=nav()
    c,b,r=fixture(html=fault in ('projection','raw_html_secret'))
    sources=json.loads(c.catalogue_json); records=json.loads(r)
    if fault=='body': sources[0]['decoded_body_sha256']='0'*64
    elif fault=='projection': sources[0]['text']='forged'
    elif fault=='get': records[0]['result']['body']='forged'
    elif fault=='truncated':
        sources[0]['truncated']=True; records[0]['result']['truncated']=True
    elif fault=='duplicate':
        sources[1]['dedupe_url']=sources[0]['dedupe_url']
    elif fault=='coordinates':
        sources[0]['body']=sources[0]['text']='unsupported\u2028separator'; sources[0]['decoded_body_sha256']=h(sources[0]['body'].encode())
        records[0]['result'].update({k:sources[0][k] for k in ('body','text','decoded_body_sha256')})
    else:
        sources[0]['body'] += '<!-- password = "syntheticsecret" -->'; sources[0]['decoded_body_sha256']=h(sources[0]['body'].encode())
        records[0]['result'].update({k:sources[0][k] for k in ('body','decoded_body_sha256')})
    if fault!='get':
        records[0]['result'].update({k:sources[0][k] for k in ('body','text','decoded_body_sha256')})
    trace=json.loads(c.trace_json)
    for i,record in enumerate(records): trace[i*2+1]['data']['metadata']['result']=dict(record['result'])
    c=dataclasses.replace(c,catalogue_json=json.dumps(sources),trace_json=json.dumps(trace))
    with pytest.raises(ValueError): research.prepare_navigation(c,b,policy(),get_records_json=j(records),deadline=time.monotonic()+30)


def test_v3_final_fit_and_omissions():
    n=nav()
    text='\n'.join(['First operation documented.','"\\汉'*2000]+[f'Line {i} meaningful.' for i in range(3,40)])
    cat,*_=prepare([text,'Other document.','Third document.'])
    assert len(cat.catalogue_json)<=4096
    page=n.build_page(cat,'S1',1,key()); wire=json.loads(page.wire_json)
    assert len(page.wire_json)<=3072 and wire['end']==24 and wire['next_start']==25
    assert [2,2,'size'] in wire['omissions'] and 2 not in dict(wire['lines'])
    assert len(wire['cards'])<=8
    for _,_,_,a,z,l,r in wire['cards']:
        assert z-a<8 and r-l<8 and all(i in dict(wire['lines']) for i in range(l,r+1))
    with pytest.raises(ValueError): n.build_page(cat,'S1',True,key())
    with pytest.raises(ValueError): n.build_page(cat,'S1',40,key())


@pytest.mark.parametrize('text',['','x'*262145,'\n'.join(['line']*1025),'x'*6000,'password = "syntheticsecret"'])
def test_v3_three_renderable_sources_required(text):
    c,b,r=fixture([text,'Other safe source.','Third safe source.'])
    with pytest.raises(ValueError,match='three'): research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)


def test_v2_archival_bytes_unchanged_and_fresh_requires_v3():
    n=nav(); c,b,r=fixture()
    before=(research.source_pack(json.loads(c.catalogue_json)),research.reference_cards(c.catalogue_json))
    cat=research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)
    assert before==(research.source_pack(json.loads(c.catalogue_json)),research.reference_cards(c.catalogue_json))
    for version in (None,2,4):
        record=dict(call_id='report',request_id=b.request_id,session_id=b.session_id,task_id=b.task_id,result=dict(file_call_id='file',payload_json='{}'))
        if version is not None: record['result']['protocol_version']=version
        with pytest.raises(ValueError,match='protocol|version|snapshot'):
            research.verify_research_artifacts(b,[dict(call_id='file')],[record],c.catalogue_json,required_version=3)


def test_v3_policy_and_sealed_replay():
    n=nav(); cat,c,b,r,p=prepare()
    n.validate_scan_policy(p,p)
    with pytest.raises(ValueError): n.validate_scan_policy(dataclasses.replace(p,scanners=tuple(reversed(p.scanners))),p)
    reads=[n.build_page(cat,f'S{i}',1,key(i)) for i in range(1,4)]
    snapshot=n.seal_snapshot(cat,c,r,p,tuple(zip([key(i) for i in range(1,4)],reads)),generation=2)
    submitted=dict(path='research.md',title='Research',sections=[dict(source_id=f'S{i}',heading=f'Source {i}',facts=[dict(claim='The document describes local behavior.',evidence_id=json.loads(reads[i-1].wire_json)['cards'][0][0])]) for i in range(1,4)])
    resolved, bindings=n.resolve_v3(submitted,snapshot,c)
    rendered=n.render_v3(resolved,c.catalogue_json,bindings=bindings)
    assert len(bindings)==3 and 'extracted-text' not in rendered.content and 'raw L' in rendered.content
    for bad in ('N3.'+'0'*16,'old.1',json.loads(reads[1].wire_json)['cards'][0][0]):
        forged=json.loads(json.dumps(submitted)); forged['sections'][0]['facts'][0]['evidence_id']=bad
        with pytest.raises(ValueError): n.resolve_v3(forged,snapshot,c)
    with pytest.raises(ValueError): n.resolve_v3(submitted,dataclasses.replace(snapshot,nonce='f'*32),c)
    with pytest.raises(ValueError): n.resolve_v3(submitted,dataclasses.replace(snapshot,replay_json=snapshot.replay_json+b' '),c)


def test_v3_complete_wire_security_check():
    n=nav(); cat,*_=prepare(); p=policy()
    view=n.build_page(cat,'S1',1,key())
    assert n.scan_view(view,p)==view
    wire=json.loads(view.wire_json); wire['metadata']='password = "syntheticsecret"'
    raw=j(wire)
    with pytest.raises(ValueError,match='Unsafe'): n.scan_view(dataclasses.replace(view,wire_json=raw,wire_sha256=h(raw)),p)


def test_v3_get_end_linkage_is_required():
    n=nav(); c,b,r=fixture()
    events=json.loads(c.trace_json)
    events[1]['data']['success']=False
    c=dataclasses.replace(c,trace_json=json.dumps(events))
    with pytest.raises(ValueError,match='GET'): research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)


@pytest.mark.parametrize('count',[1023,1024,1025])
def test_v3_line_count_cap(count):
    c,b,r=fixture(['\n'.join(['plain']*count),'Second source.','Third source.'])
    if count>1024:
        with pytest.raises(ValueError,match='three'): research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)
    else:
        cat=research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)
        assert cat.sources[0].total_lines==count


@pytest.mark.parametrize('size',[262143,262144,262145])
def test_v3_decoded_byte_cap(size):
    text='Header\n\n'+'x'*(size-8)
    c,b,r=fixture([text,'Second source.','Third source.'])
    if size>262144:
        with pytest.raises(ValueError,match='three'): research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)
    else:
        cat=research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)
        assert cat.sources[0].available


@pytest.mark.parametrize('count',[23,24,25])
def test_v3_page_position_cap_and_zero_card_read(count):
    n=nav(); cat,*_=prepare(['\n'.join(['line']*count),'Second source.','Third source.'])
    page=json.loads(n.build_page(cat,'S1',1,key()).wire_json)
    assert page['end']==min(24,count)
    source=dataclasses.replace(cat.sources[0],anchors_json=b'[]')
    blank=n.build_page(dataclasses.replace(cat,sources=(source,)+cat.sources[1:]),'S1',1,key())
    assert json.loads(blank.wire_json)['lines'] and json.loads(blank.cards_json)==[]


@pytest.mark.parametrize('count',[7,8,9])
def test_v3_card_cap(count):
    n=nav(); cat,*_=prepare(['\n'.join([f'call{i}()' for i in range(count)]),'second()','third()'],suffix='.py')
    page=json.loads(n.build_page(cat,'S1',1,key()).wire_json)
    assert len(page['cards'])==min(count,8)
    assert page['omitted_cards']==max(0,count-8)


def test_v3_hash_identity_mutations_and_collision(monkeypatch):
    n=nav(); cat,*_=prepare(); view=n.build_page(cat,'S1',1,key())
    source=cat.sources[0]; identity=json.loads(source.identity_json); identity[5]='f'*64
    changed=dataclasses.replace(source,identity_json=j(identity))
    assert n.build_page(dataclasses.replace(cat,sources=(changed,)+cat.sources[1:]),'S1',1,key()).view_id!=view.view_id
    changed=dataclasses.replace(source,safe_line_pairs=((1,'Changed line.'),))
    mutated=n.build_page(dataclasses.replace(cat,sources=(changed,)+cat.sources[1:]),'S1',1,key())
    assert mutated.cards_json!=view.cards_json
    changed=dataclasses.replace(source,anchors_json=j([[1,1,'documented',''],[1,1,'documented','']]))
    with pytest.raises(ValueError,match='collision'): n.build_page(dataclasses.replace(cat,sources=(changed,)+cat.sources[1:]),'S1',1,key())


def test_v3_inconsistent_redaction_and_residuals(monkeypatch):
    from openjarvis.security.scanner import SecretScanner
    n=nav(); c,b,r=fixture(['Safe\npassword = "syntheticsecret"\nTail','Other','Third'])
    original=SecretScanner.redact
    def disagree(self,text):
        return original(self,text) if '\n' not in text else 'changed whole document'
    monkeypatch.setattr(SecretScanner,'redact',disagree)
    with pytest.raises(ValueError,match='three'): research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)
    monkeypatch.setattr(SecretScanner,'redact',lambda self,text:text)
    with pytest.raises(ValueError,match='three'): research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)


def test_v3_policy_pins_actual_rules_and_extractor():
    n=nav(); p=policy(); data=json.loads(p.policy_json)
    from pathlib import Path
    assert data['navigation_sha256']==h(Path(n.__file__).read_bytes())
    assert data['witness_sha256']==h(Path(research.__file__).read_bytes())
    assert data['extractor']==h(Path(n.__file__).with_name('browser').joinpath('channel.py').read_bytes())


def test_v3_middle_window_replay_does_not_use_v2_visibility():
    n=nav()
    text='\n'.join(f'Documentation row {i}: records local conditions and alternatives.' for i in range(1,1001))
    cat,c,b,r,p=prepare([text,'Second distinct source.','Third distinct source.'])
    assert 501 not in dict(research._source_view(json.loads(c.catalogue_json)[0],3)['lines'])
    pages=[n.build_page(cat,'S1',501,key(1)),n.build_page(cat,'S2',1,key(2)),n.build_page(cat,'S3',1,key(3))]
    snapshot=n.seal_snapshot(cat,c,r,p,tuple(zip([key(i) for i in range(1,4)],pages)),generation=2)
    payload=dict(path='research.md',title='Title',sections=[dict(source_id=f'S{i}',heading=f'Heading {i}',facts=[dict(claim='The source describes conditions.',evidence_id=json.loads(pages[i-1].cards_json)[0][0])]) for i in range(1,4)])
    resolved,bindings=n.resolve_v3(payload,snapshot,c)
    assert 'raw L501' in n.render_v3(resolved,c.catalogue_json,bindings=bindings).content
    for field in ('wire_sha256','wire','key'):
        packet=json.loads(snapshot.replay_json)
        if field=='wire_sha256': packet['reads'][0][field]='0'*64
        elif field=='wire': packet['reads'][0][field]['lines'][0][1]='forged line'
        else: packet['reads'][0][field]['seq']=99
        raw=j(packet)
        forged=dataclasses.replace(snapshot,replay_json=raw,manifest_sha256=h(raw))
        with pytest.raises(ValueError): n.resolve_v3(payload,forged,c)


def test_v3_existence_checks_later_legal_starts_without_hint():
    n=nav()
    text='\n'.join(['x'*4000]*25+['','Available late paragraph.'])
    cat,*_=prepare([text,'Second source.','Third source.'])
    assert cat.sources[0].available
    assert not json.loads(n.build_page(cat,'S1',1,key()).cards_json)
    assert json.loads(n.build_page(cat,'S1',27,key()).cards_json)
    assert b'winning' not in cat.catalogue_json and b'preferred' not in cat.catalogue_json


@pytest.mark.parametrize('delta',[-1,0,1])
def test_v3_exact_page_serialized_byte_boundary(delta):
    n=nav(); cat,*_=prepare()
    source=dataclasses.replace(cat.sources[0],anchors_json=b'[]',safe_line_pairs=((1,''),))
    cat=dataclasses.replace(cat,sources=(source,)+cat.sources[1:])
    empty=json.loads(n.build_page(cat,'S1',1,key()).wire_json)
    overhead=len(j(empty))
    text='x'*(3072-overhead+delta)
    source=dataclasses.replace(source,safe_line_pairs=((1,text),))
    wire=json.loads(n.build_page(dataclasses.replace(cat,sources=(source,)+cat.sources[1:]),'S1',1,key()).wire_json)
    if delta<=0:
        assert dict(wire['lines'])[1]==text and len(j(wire))==3072+delta
    else:
        assert wire['lines']==[] and wire['omissions']==[[1,1,'size']]


@pytest.mark.parametrize('delta',[-1,0,1])
def test_v3_exact_mandatory_catalogue_byte_boundary(delta):
    n=nav(); cat,c,b,r,p=prepare()
    mandatory=json.loads(cat.catalogue_json)
    for entry in mandatory: entry['landmarks']=[]
    padding=4096-len(j(mandatory))+delta
    sources=json.loads(c.catalogue_json); records=json.loads(r); trace=json.loads(c.trace_json)
    for i,source in enumerate(sources):
        extra=padding//3+(i<padding%3)
        old=source['final_url']; new=old[:-3]+'a'*extra+'.md'
        for field in ('requested_url','final_url','dedupe_url'): source[field]=new
        records[i]['result'].update({field:new for field in ('requested_url','final_url','dedupe_url')})
        trace[i*2]['data']['arguments']['url']=new
        trace[i*2+1]['data']['metadata']['result']=dict(records[i]['result'])
    c=dataclasses.replace(c,catalogue_json=json.dumps(sources),trace_json=json.dumps(trace))
    if delta>0:
        with pytest.raises(ValueError,match='Mandatory'): research.prepare_navigation(c,b,p,get_records_json=j(records),deadline=time.monotonic()+30)
    else:
        out=research.prepare_navigation(c,b,p,get_records_json=j(records),deadline=time.monotonic()+30)
        assert len(out.catalogue_json)==4096+delta
        assert all(not entry['landmarks'] for entry in json.loads(out.catalogue_json))


def test_v3_fresh_artifact_reopening_and_tamper(tmp_path):
    n=nav(); cat,c,b,r,p=prepare()
    from src.brain.work_tools import WorkBinding
    binding=WorkBinding(tmp_path,b.request_id,b.session_id,b.task_id)
    pages=[n.build_page(cat,f'S{i}',1,key(i)) for i in range(1,4)]
    snapshot=n.seal_snapshot(cat,c,r,p,tuple(zip([key(i) for i in range(1,4)],pages)),generation=2)
    submitted=dict(path='research.md',title='Title',sections=[dict(source_id=f'S{i}',heading=f'Section {i}',facts=[dict(claim='The source records local behavior.',evidence_id=json.loads(pages[i-1].cards_json)[0][0])]) for i in range(1,4)])
    resolved,bindings=n.resolve_v3(submitted,snapshot,c)
    rendered=n.render_v3(resolved,c.catalogue_json,bindings=bindings)
    path=tmp_path/'research.md'; path.write_bytes(rendered.content.encode())
    artifact=dict(call_id='file',path=str(path),sha256=h(path.read_bytes()))
    record=dict(call_id='report',**vars(b),result=dict(protocol_version=3,file_call_id='file',submitted_json=json.dumps(submitted),payload_json=json.dumps(resolved),bindings=bindings,cited_source_ids=list(rendered.cited_source_ids),evidence=list(rendered.evidence)))
    assert len(research.verify_issued_research_artifacts(binding,[artifact],[record],c.catalogue_json,issued_snapshot=snapshot))==3
    path.write_bytes(b'tampered')
    with pytest.raises(ValueError,match='readback'): research.verify_issued_research_artifacts(binding,[artifact],[record],c.catalogue_json,issued_snapshot=snapshot)


def test_v3_incomplete_python_is_unavailable_without_aborting_other_sources():
    c,b,r=fixture(["'''",'one()','two()','three()'],suffix='.py')
    cat=research.prepare_navigation(c,b,policy(),get_records_json=r,deadline=time.monotonic()+30)
    assert not cat.sources[0].available and sum(s.available for s in cat.sources)==3


def test_v3_nonce_preserves_all_sixteen_random_bytes_once(monkeypatch):
    import secrets
    calls=[]
    def random_bytes(size):
        calls.append(size)
        assert size==16
        return b'\x00\x01\x02\x03\x04\x05\x06\x07\x08\x09\x0a\x0b\x0c\x0d\x0e\x0f'
    monkeypatch.setattr(secrets,'token_bytes',random_bytes)
    cat,*_=prepare()
    assert cat.nonce=='000102030405060708090a0b0c0d0e0f'
    assert calls==[16]


def test_v3_placeholder_renderability_does_not_expose_or_certify_wire(monkeypatch):
    """Controlled SHA primitive forces a valid rare metadata shape; real scanners remain."""
    n=nav(); original=n._h
    def controlled(raw):
        return '5138343572083543'+'a'*48 if raw.startswith(b'["card3",') else original(raw)
    monkeypatch.setattr(n,'_h',controlled)
    cat,*rest=prepare()
    assert sum(s.available for s in cat.sources)==3
    assert b'N3.' not in cat.catalogue_json
    page=n.build_page(cat,'S1',1,key())
    assert json.loads(page.cards_json)[0][0]=='N3.5138343572083543'
    with pytest.raises(ValueError,match='Unsafe complete observation'):
        n.scan_view(page,rest[-1])
