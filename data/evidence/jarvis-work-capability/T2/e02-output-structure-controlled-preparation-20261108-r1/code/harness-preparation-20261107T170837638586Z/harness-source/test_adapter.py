"""No real launch, kill, HTTP, product submission, model or qualification."""
import datetime as dt
import importlib.util
import json
from pathlib import Path
import sys
import types
import pytest


def observe_failure_exports(folder,monkeypatch):
    from src.brain.work_tools import WorkLedger
    from src.brain.work_service import WorkService
    monkeypatch.setattr(WorkLedger,'__init__',WorkLedger.__init__)
    monkeypatch.setattr(WorkLedger,'_freeze_runtime_inputs',WorkLedger._freeze_runtime_inputs)
    monkeypatch.setattr(WorkService,'submit_work',WorkService.submit_work)
    a.install_trusted_exports(folder)


@pytest.mark.parametrize('case',['quoted_write','escaped_boundary'])
def test_export_diagnostics_current_sampler_contract(tmp_path,monkeypatch,sdk_io,mock_jar,code_sources,case):
    import httpx,re
    from src.brain.tests.test_work_navigation_transport import navigation_reply
    from src.brain.tests.test_work_research import submit,RESTRICTED
    from src.brain.tests.test_work_sampler_json_strings import pattern
    from src.brain.tests.test_work_source_reference_schema import writer_schema
    from src.brain.work_navigation import canonical_v3
    from src.brain.work_research import verify_runtime_packet
    observe_failure_exports(tmp_path,monkeypatch)
    sent=[];send=httpx.Client.send;original_get=httpx.request
    def capture(client,request,*args,**kwargs):
        if request.url.path=='/api/chat':sent.append(bytes(request.content))
        return send(client,request,*args,**kwargs)
    monkeypatch.setattr(httpx.Client,'send',capture)
    source_text='client.run("中文", "\\\\")\nclient.stop()\n'
    def get(method,url,**kwargs):
        if url==code_sources[1]:
            return httpx.Response(200,headers={'content-type':'text/plain'},text=source_text,
                                  request=httpx.Request(method,url))
        return original_get(method,url,**kwargs)
    monkeypatch.setattr(httpx,'request',get)
    claim='可见 client.run 调用，参数含 "中文" 和反斜杠 \\。'
    raw_boundary=r'\u0061client.run';ref=[];response_body=[]
    def reply(body):
        value=json.loads(navigation_reply(body))
        if value.get('action')=='ultima_work_research_write':
            fact=value['action_input']['sections'][1]['facts'][0];ref.append(fact['evidence_id'])
            fact['claim']=claim if case=='quoted_write' else json.loads('"'+raw_boundary+'"')
            raw_claim=json.dumps(claim,ensure_ascii=False)[1:-1] if case=='quoted_write' else raw_boundary
            assert re.fullmatch(pattern(writer_schema(body['format']),ref[-1]),raw_claim)
            encoded=json.dumps(value,ensure_ascii=False)
            if case=='escaped_boundary':
                assert fact['claim']=='aclient.run'
                encoded=encoded.replace('"aclient.run"','"'+raw_boundary+'"')
                assert raw_boundary in encoded and json.loads(encoded)==value
            response_body.append(encoded)
            return encoded
        return json.dumps(value,ensure_ascii=False)
    reply.no_auto_navigation=True
    mock_jar[3].extend([reply]*5)
    result=submit(tmp_path/'outputs',sdk_io[0],mock_jar[1],source_urls=code_sources)
    ledger=RESTRICTED[result['task_id']]
    assert len(ref)==len(response_body)==1
    assert a.load(tmp_path/'service-first-result.json')==result
    exported=a.load(tmp_path/'trusted-export.json')
    if case=='quoted_write':
        assert result['status']=='succeeded',result['error']
        assert len(sent)==5 and len(result['artifacts'])==len(result['research_effects'])==1
        assert exported['complete'] is True and exported['END'] is True and exported['ack_admitted'] is True
        raw=a.read_completed(tmp_path,exported)['runtime']
        assert raw==(tmp_path/'trusted-runtime.raw').read_bytes()==ledger._runtime_final
        packet=json.loads(raw);wire=packet['wires'][-2]
        assert wire['strict_schema']!=wire['sampler_schema']
        assert re.fullmatch(pattern(writer_schema(wire['strict_schema']),ref[0]),claim)
        assert pattern(writer_schema(wire['strict_schema']),ref[0])!=pattern(writer_schema(wire['sampler_schema']),ref[0])
        assert wire['entity'].encode('utf8')==sent[-2]
        assert json.loads(sent[-2])['format']==wire['sampler_schema']
        assert wire['hashes']=={k:a.hashlib.sha256(v).hexdigest() for k,v in dict(
            messages=canonical_v3(wire['secured_messages']),strict=canonical_v3(wire['strict_schema']),
            sampler=canonical_v3(wire['sampler_schema']),entity=sent[-2]).items()}
        artifact=Path(result['artifacts'][0]['path']).read_bytes()
        assert a.hashlib.sha256(artifact).hexdigest()==result['artifacts'][0]['sha256']
        assert wire['secured_envelope']['action_input']['sections'][1]['facts'][0]['claim']==claim
        assert '可见 client.run 调用，参数含 "中文" 和反斜杠 \\\\。' in artifact.decode('utf8')
        verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,raw,
                              require_ack=True,runtime_inputs=ledger._runtime_inputs)
        assert not (tmp_path/'trusted-failure-diagnostic.raw').exists()
    else:
        assert result['status']=='failed' and result['content']=='本次研究未交付。'
        assert len(sent)==4 and not result['artifacts'] and not list((tmp_path/'outputs').rglob('research.md'))
        assert exported['complete'] is False and exported['END'] is False
        assert not (tmp_path/'trusted-runtime.raw').exists() and not getattr(ledger,'_runtime_final',None)
        path=tmp_path/'trusted-failure-diagnostic.raw';packet=a.load(path);last=packet['last_http']
        assert path.read_bytes()==ledger._failure_diagnostic and path.stat().st_size<=16384
        assert packet['branch']=='unvalidated_response' and packet['acceptance_credit']==0
        assert not packet['write_confirmed'] and not packet['ack_confirmed']
        assert last['generation']==len(sent) and last['status']==200 and last['validated_response'] is False
        assert last['request_sha256']==a.hashlib.sha256(sent[-1]).hexdigest() and last['request_bytes']==len(sent[-1])
        receipt=a.load(tmp_path/'trusted-failure-diagnostic.export.json')
        assert receipt['status']=='SAVED' and receipt['sha256']==a.sha(path)==result['research_diagnostic']['sha256']
        assert receipt['complete'] is False and receipt['END'] is False


@pytest.mark.parametrize('case',['reserved_read','six_read_refusal','false_completion'])
def test_failure_diagnostic_export_current_coverage_contract(tmp_path,monkeypatch,sdk_io,mock_jar,case):
    import httpx
    from src.brain.tests.test_work_source_coverage_budget import repeated_case
    from src.brain.tests.test_work_failure_diagnostics import early_case
    from src.brain.tests.test_work_research import submit,RESTRICTED
    observe_failure_exports(tmp_path,monkeypatch)
    sent=[];send=httpx.Client.send
    def capture(client,request,*args,**kwargs):
        if request.url.path=='/api/chat':sent.append(bytes(request.content))
        return send(client,request,*args,**kwargs)
    monkeypatch.setattr(httpx.Client,'send',capture)
    if case=='reserved_read':
        result,ledger=repeated_case(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,adaptive=False)
        reads,posts,validated=4,5,False
    elif case=='six_read_refusal':
        result,ledger=early_case(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,reads=6)
        reads,posts,validated=6,7,True
    else:
        mock_jar[3].append(json.dumps(dict(final_answer='已保存research.md')))
        result=submit(tmp_path/'outputs',sdk_io[0],mock_jar[1]);ledger=RESTRICTED[result['task_id']]
        reads,posts,validated=0,1,False
    assert result['status']=='failed' and result['content']=='本次研究未交付。'
    assert 'final_answer' not in json.dumps(result) and not list((tmp_path/'outputs').rglob('research.md'))
    path=tmp_path/'trusted-failure-diagnostic.raw';packet=a.load(path)
    assert path.read_bytes()==ledger._failure_diagnostic and path.stat().st_size<=16384
    assert packet['budget']['reads_used']==ledger._read_count==reads and len(sent)==posts
    assert packet['last_http']['generation']==posts and packet['last_http']['status']==200
    assert packet['last_http']['validated_response'] is validated
    assert packet['last_http']['request_sha256']==a.hashlib.sha256(sent[-1]).hexdigest()
    assert packet['last_http']['request_bytes']==len(sent[-1])
    assert not packet['write_confirmed'] and not packet['ack_confirmed'] and packet['acceptance_credit']==0
    assert a.load(tmp_path/'service-first-result.json')==result
    receipt=a.load(tmp_path/'trusted-failure-diagnostic.export.json')
    assert receipt['status']=='SAVED' and receipt['sha256']==a.sha(path)
    assert receipt['complete'] is False and receipt['END'] is False
    assert result['research_diagnostic']['sha256']==a.sha(path)
    assert a.load(tmp_path/'trusted-export.json')['complete'] is False
    if case=='six_read_refusal':
        assert packet['branch']=='final_before_write' and packet['final_answer']['text']=='本次研究未交付。'
        assert packet['eligible_source_ids']==['S1','S2','S3'] and all(p['visible'] for p in packet['pages'])
    else:
        assert packet['branch']=='unvalidated_response' and packet['final_answer'] is None
    if case=='reserved_read':
        assert packet['eligible_source_ids']==['S1'] and len(packet['pages'])==4
        assert packet['pages'][-1]['confirmed'] and not packet['pages'][-1]['visible']
    assert not getattr(ledger,'_runtime_final',None)


@pytest.mark.parametrize('fault',['http500','bad_json','scan'])
def test_failure_diagnostic_export_current_http_receipt(tmp_path,monkeypatch,sdk_io,mock_jar,fault):
    from src.brain.tests.test_work_http_failure_diagnostics import failing_exchange
    observe_failure_exports(tmp_path,monkeypatch)
    result,ledger,seen,consumed,closed=failing_exchange(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,fault=fault)
    assert result['status']=='failed'
    path=tmp_path/'trusted-failure-diagnostic.raw'
    assert path.read_bytes()==ledger._failure_diagnostic and path.stat().st_size<=16384
    packet=json.loads(path.read_bytes());last=packet['last_http']
    assert packet['kind']=='research_failure_diagnostic_v4'
    assert last['status']==(500 if fault=='http500' else 200)
    assert last['route']=='chat' and last['generation']==2 and last['receipt_index']==5
    assert last['request_sha256']==a.hashlib.sha256(seen[-1][1]).hexdigest()
    assert last['request_bytes']==len(seen[-1][1]) and last['validated_response'] is False
    assert packet['complete'] is False and packet['acceptance_credit']==0
    assert packet['write_confirmed'] is False and packet['ack_confirmed'] is False
    receipt=a.load(tmp_path/'trusted-failure-diagnostic.export.json')
    assert receipt['status']=='SAVED' and receipt['sha256']==a.sha(path)
    assert receipt['complete'] is False and receipt['END'] is False
    assert result['research_diagnostic']['sha256']==a.sha(path)
    assert a.load(tmp_path/'service-first-result.json')==result
    assert a.load(tmp_path/'trusted-export.json')['complete'] is False
    assert not list((tmp_path/'outputs').rglob('research.md'))
    assert b'syntheticsecret' not in path.read_bytes()
    if fault=='http500':assert not consumed and closed


def test_failure_diagnostic_export_real_sdk_failure_is_private_and_bounded(tmp_path,monkeypatch,sdk_io,mock_jar):
    from src.brain.tests.test_work_failure_diagnostics import early_case,FINAL
    observe_failure_exports(tmp_path,monkeypatch)
    result,ledger=early_case(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,reads=1)
    assert result['status']=='failed' and result['error']=='Missing nonempty immutable runtime proof'
    path=tmp_path/'trusted-failure-diagnostic.raw'
    assert path.exists(), 'failure observer discards the private diagnostic'
    assert path.read_bytes()==ledger._failure_diagnostic and path.stat().st_size<=16384
    receipt=a.load(tmp_path/'trusted-failure-diagnostic.export.json')
    assert receipt['status']=='SAVED' and receipt['sha256']==a.sha(path) and receipt['complete'] is False and receipt['END'] is False
    assert result['content']==FINAL and 'final_answer' not in json.dumps(result)
    assert a.load(tmp_path/'trusted-export.json')['complete'] is False
    assert not list((tmp_path/'outputs').rglob('research.md'))


@pytest.mark.parametrize('fault',['binding','digest','field','unsafe'])
def test_failure_diagnostic_export_rejects_changed_or_unsafe_packet(tmp_path,monkeypatch,sdk_io,mock_jar,fault):
    from src.brain.tests.test_work_failure_diagnostics import early_case
    from src.brain.work_navigation import canonical_v3
    result,ledger=early_case(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,reads=1)
    assert hasattr(a,'export_failure_diagnostic'), 'missing restricted failure export boundary'
    data=json.loads(ledger._failure_diagnostic)
    if fault=='binding':data['binding_sha256']='0'*64
    elif fault=='digest':result['research_diagnostic']['sha256']='0'*64
    elif fault=='field':data['unexpected']='source text'
    else:
        text='password = "syntheticsecret"';data['final_answer']=dict(text=text,length=len(text),sha256=a.hashlib.sha256(text.encode()).hexdigest())
    if fault!='digest':
        ledger._failure_diagnostic=canonical_v3(data)
        result['research_diagnostic']['sha256']=a.hashlib.sha256(ledger._failure_diagnostic).hexdigest()
        ledger._failure_diagnostic_summary=dict(result['research_diagnostic'])
    with pytest.raises(ValueError):a.export_failure_diagnostic(tmp_path,ledger,result)
    assert not (tmp_path/'trusted-failure-diagnostic.raw').exists()


def test_failure_diagnostic_export_disk_failure_cannot_replace_product_error(tmp_path,monkeypatch,sdk_io,mock_jar):
    from src.brain.tests.test_work_failure_diagnostics import early_case
    observe_failure_exports(tmp_path,monkeypatch)
    original=a.write_raw_new
    def fail(path,raw):
        if path.name=='trusted-failure-diagnostic.raw':raise OSError('private disk error')
        return original(path,raw)
    monkeypatch.setattr(a,'write_raw_new',fail)
    result,ledger=early_case(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,reads=1)
    assert result['status']=='failed' and result['error']=='Missing nonempty immutable runtime proof'
    path=tmp_path/'trusted-failure-diagnostic.export.json'
    assert path.exists(), 'missing bounded failure-export error status'
    assert a.load(path)['status']=='FAILED' and 'private disk error' not in path.read_text()
    assert a.load(tmp_path/'service-first-result.json')==result


def test_failure_diagnostic_export_never_creates_packet_when_capture_unavailable(tmp_path,monkeypatch,sdk_io,mock_jar):
    from src.brain.tests.test_work_failure_diagnostics import early_case
    observe_failure_exports(tmp_path,monkeypatch)
    def poison(response,ledger):ledger._runtime_wires=None
    result,ledger=early_case(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,reads=1,after=poison)
    path=tmp_path/'trusted-failure-diagnostic.export.json'
    assert path.exists(), 'missing explicit unavailable diagnostic status'
    assert a.load(path)['status']=='UNAVAILABLE' and not (tmp_path/'trusted-failure-diagnostic.raw').exists()
    assert result['error']=='Missing nonempty immutable runtime proof'


@pytest.mark.parametrize('stage', ['runtime_verify', 'structure_scan', 'member_preserve'])
def test_export_diagnostics_identifies_stage_without_dynamic_text(tmp_path, monkeypatch, stage):
    from src.brain import work_research
    sentinel='SYNTHETIC_PRIVATE_PAYLOAD_'+'x'*200
    failure=ValueError(sentinel)
    ledger=types.SimpleNamespace(_runtime_final=b'{}',_binding=None,issued_snapshot=None,
        _collection=None,_runtime_inputs=None,_policy=types.SimpleNamespace(scanners=()))
    def fail(*args,**kwargs):raise failure
    monkeypatch.setattr(work_research,'verify_runtime_packet',fail if stage=='runtime_verify' else lambda *a,**k:None)
    monkeypatch.setattr(a,'validate_export_structure',fail if stage=='structure_scan' else lambda *a:None)
    monkeypatch.setattr(a,'preserve_completed_members',fail if stage=='member_preserve' else lambda *a:None)
    with pytest.raises(ValueError) as raised:a.export_completed(tmp_path,ledger,{})
    assert raised.value is failure
    path=tmp_path/'trusted-export.diagnostic.json'
    assert path.exists(), 'export failure lacks a bounded diagnostic'
    raw=path.read_text('utf8');diagnostic=json.loads(raw)
    assert diagnostic['stage']==stage and diagnostic['error_type']=='ValueError'
    assert diagnostic['message_characters']==len(sentinel)
    assert sentinel not in raw and 'SYNTHETIC_PRIVATE' not in raw
    assert diagnostic['frames'] and all(frame['file'] in ('adapter.py','work_research.py','work_navigation.py') for frame in diagnostic['frames'])
    assert diagnostic['complete'] is False and diagnostic['END'] is False
    assert not list(tmp_path.glob('trusted-*.raw')) and not (tmp_path/'trusted-export.json').exists()


def test_export_diagnostics_failed_write_preserves_original_exception(tmp_path,monkeypatch):
    from src.brain import work_research
    failure=ValueError('original-private-message');calls=[]
    ledger=types.SimpleNamespace(_runtime_final=b'{}',_binding=None,issued_snapshot=None,_collection=None,_runtime_inputs=None)
    def fail(*args,**kwargs):raise failure
    def unavailable(*args):calls.append(args[0]);raise OSError('disk-private-message')
    monkeypatch.setattr(work_research,'verify_runtime_packet',fail)
    monkeypatch.setattr(a,'save_new',unavailable)
    with pytest.raises(ValueError) as raised:a.export_completed(tmp_path,ledger,{})
    assert raised.value is failure
    assert calls==[tmp_path/'trusted-export.diagnostic.json']


@pytest.mark.parametrize('message', ['z'*5000, None])
def test_export_diagnostics_bounds_unknown_exception_messages(tmp_path,monkeypatch,message):
    from src.brain import work_research
    failure=RuntimeError(message);ledger=types.SimpleNamespace(_runtime_final=b'{}',_binding=None,
        issued_snapshot=None,_collection=None,_runtime_inputs=None)
    def fail(*args,**kwargs):raise failure
    monkeypatch.setattr(work_research,'verify_runtime_packet',fail)
    with pytest.raises(RuntimeError):a.export_completed(tmp_path,ledger,{})
    path=tmp_path/'trusted-export.diagnostic.json';assert path.exists()
    diagnostic=a.load(path)
    assert diagnostic['message_sha256'] is None and path.stat().st_size<4096


def test_export_diagnostics_success_keeps_original_result(tmp_path,monkeypatch):
    from src.brain import work_research
    ledger=types.SimpleNamespace(_runtime_final=b'{}',_binding=None,issued_snapshot=None,
        _collection=None,_runtime_inputs=None,_policy=types.SimpleNamespace(scanners=()))
    marker=object();monkeypatch.setattr(work_research,'verify_runtime_packet',lambda *a,**k:None)
    monkeypatch.setattr(a,'validate_export_structure',lambda *a:None)
    monkeypatch.setattr(a,'preserve_completed_members',lambda *a:marker)
    assert a.export_completed(tmp_path,ledger,{}) is marker
    assert not (tmp_path/'trusted-export.diagnostic.json').exists()


def test_export_diagnostics_saved_native_metadata_full_mock_chain(tmp_path,monkeypatch,sdk_io,mock_jar):
    import httpx
    metadata=json.loads((a.C/'src/brain/tests/fixtures/native_metadata_0_32_15.json').read_bytes())
    send=httpx.Client.send;observed=[]
    def recorded(client,request,**kwargs):
        if request.url.path in ('/api/version','/api/tags'):
            observed.append(request.url.path)
            key='version' if request.url.path=='/api/version' else 'tags'
            return httpx.Response(200,stream=httpx.ByteStream(json.dumps(metadata[key]).encode('utf8')),request=request)
        return send(client,request,**kwargs)
    monkeypatch.setattr(httpx.Client,'send',recorded)
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch)
    assert result['status']=='succeeded' and len(observed)==10
    assert a.load(tmp_path/'trusted-export.json')['complete'] is True
    assert not (tmp_path/'trusted-export.diagnostic.json').exists()


@pytest.mark.parametrize('field',['context_length','embedding_length'])
@pytest.mark.parametrize('value',[0,4096,2**63-1,True,-1,2**63,None,'4096',1.5,{},[]])
def test_export_diagnostics_model_lengths_have_exact_integer_domain(tmp_path,monkeypatch,sdk_io,mock_jar,field,value):
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    packet=json.loads(ledger._runtime_final)
    tags=json.loads(packet['wires'][0]['identity']['tags_response'])
    tags['models'][0].setdefault('details',{})[field]=value
    packet['wires'][0]['identity']['tags_response']=json.dumps(tags)
    if type(value) is int and 0<=value<2**63:
        a.validate_export_structure(packet,ledger._policy.scanners)
    else:
        with pytest.raises(ValueError,match='Producer model detail'):
            a.validate_export_structure(packet,ledger._policy.scanners)

spec=importlib.util.spec_from_file_location('source10_adapter',Path(__file__).with_name('adapter.py'))
a=importlib.util.module_from_spec(spec); spec.loader.exec_module(a)
with a.candidate_import_path():
    from src.brain.tests.test_work_research import sdk_io,mock_jar,stable_navigation_entropy
    from src.brain.tests.test_work_navigation_transport import genuine_navigation
    from src.brain.tests.test_work_code_claim_schema import code_sources

@pytest.fixture(autouse=True)
def canonical_unit_entropy(stable_navigation_entropy,monkeypatch):
    # The product's unit fixture supplies stable entropy but emits version-0
    # UUIDs. The real external reader correctly requires canonical UUID4.
    import itertools,uuid
    counter=itertools.count(1000)
    monkeypatch.setattr(uuid,'uuid4',lambda:uuid.UUID(int=next(counter),version=4))

@pytest.fixture(autouse=True)
def offline_ssrf(monkeypatch):
    # Test-only fallback: sdk_io supplies deterministic getaddrinfo. Rust DNS
    # bypasses Python audit hooks, so it must not run in this offline suite.
    from openjarvis.security import ssrf
    monkeypatch.setattr(ssrf, 'check_ssrf', ssrf._check_ssrf_python)

def protected_fixture(folder,monkeypatch,p4,identities):
    """Current seven-row schema; only these unit fixture bytes are synthetic."""
    import hashlib
    rows=[dict(key,parent_pid=900,command_line_sha256=hashlib.sha256(('protected '+str(key['pid'])).encode('utf-16le')).hexdigest()) for key in identities]
    path=folder/'protected-fixture.json'
    a.save_new(path,dict(protected5=rows[:5],protected_listener_pair=rows[5:],protected_process_count=7))
    monkeypatch.setattr(a,'PROTECTED_BASELINE',path)
    monkeypatch.setattr(p4,'protected',lambda:identities)
    return {key['pid']:dict(ProcessId=key['pid'],CreationFileTime=key['created_filetime'],ParentProcessId=900,CommandLine='protected '+str(key['pid'])) for key in identities}

def synthetic_bundle(folder,sdk_io,mock_jar,monkeypatch,*,write=True):
    from dataclasses import asdict
    from src.brain.tests import test_work_research as fixtures
    monkeypatch.setattr(fixtures,'URLS',fixtures.URLS[:4])
    try:
        result,ledger=genuine_navigation(folder/'outputs',sdk_io,mock_jar)
    except AssertionError:
        # Failure-only summaries: no report/prompt/result or credential payloads.
        import ast,hashlib
        literal_errors=set()
        for name in ('work_tools.py','work_navigation.py','work_research.py'):
            tree=ast.parse((a.C/'src/brain'/name).read_text('utf8'))
            for node in ast.walk(tree):
                if (isinstance(node,ast.Call) and isinstance(node.func,ast.Name)
                        and node.func.id in ('ValueError','RuntimeError') and node.args
                        and isinstance(node.args[0],ast.Constant) and isinstance(node.args[0].value,str)):
                    literal_errors.add(node.args[0].value)
        def error_summary(value):
            value=str(value or '')
            return dict(label=value if value in literal_errors else 'redacted_or_empty',
                sha256=hashlib.sha256(value.encode('utf8')).hexdigest(),characters=len(value))
        ledgers=[]
        for observed in list(fixtures.RESTRICTED.values())[-2:]:
            records=[]
            for record in observed.snapshot()[-8:]:
                records.append(dict(tool=record.get('tool_name'),success=record.get('success'),
                    error=error_summary(record.get('error')),error_type=record.get('error_type'),
                    result_present='result' in record,seq=record.get('seq')))
            events=[]
            staged=getattr(observed,'_staged',{})
            for raw in getattr(observed,'_runtime_events',[])[-2:]:
                event=json.loads(raw); data=event.get('data',{})
                events.append(dict(type=event.get('type'),tool=data.get('tool'),
                    success=data.get('success'),agent=data.get('agent'),
                    staged_links=[dict(seq=seq,confirmed=node.get('confirmed'),
                        result_equal=data.get('result')==node.get('content'),
                        metadata_equal=data.get('metadata')==node.get('metadata'))
                        for seq,node in list(staged.items())[-4:]]))
            expected=getattr(observed,'_expected',None) or {}
            ledgers.append(dict(first_failure=error_summary(observed.first_failure),
                permit_present=observed._permit is not None,
                expected={key:expected.get(key) for key in ('seq','name','generation','ended')},
                records=records,events=events))
        print('SYNTHETIC_FIXTURE_FAILURE_CONTEXT '+json.dumps(ledgers,sort_keys=True))
        raise
    sources=json.loads(ledger._collection.catalogue_json)
    monkeypatch.setattr(a,'corpus',lambda:dict(query='Research a subject',sources=sources))
    result['marker']='first'
    if write:
        a.save_new(folder/'service-first-result.json',result)
        a.save_new(folder/'runtime-inputs.json',asdict(ledger._runtime_inputs))
        a.export_completed(folder,ledger,result)
    return result,ledger

def documents():
    now=dt.datetime.now(dt.timezone.utc)
    authority=dict(schema=11,kind='source10_execution',issuer='root',case='E02-controlled-1',candidate='bf7f7a9cf0e4ba559c29daa388c00379d12d345a',candidate_manifest_sha256='2d405a84d02b55daaf9430f62b52c254fd81dc87a87747ff3613459b236b026e',issued_at=now.isoformat(),expires_at=(now+dt.timedelta(seconds=90)).isoformat(),budgets=dict(cli=1,search=1,GET=4,inspect=6,write=1,ACK=1,native_POST=8,service_seconds=260,client_seconds=300,outer_seconds=315,retry=0),native_precision='FILETIME100ns',actual=True,schedule=dict(work_seconds=275,cleanup_seconds=310,outer_seconds=315,ruling_sha256='144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'),parent_timing=dict(origin_ns=100,clock_domain=a.CLOCK_DOMAIN,run_id='test',parent_identity={}))
    ledger=dict(schema=11,released_case='E02-controlled-1',consumed=['E02-controlled-1'],attempts=1,retry=0)
    return authority,ledger,now

@pytest.mark.parametrize('mutation',['candidate','budget','baseline','expired','kind','schema','model','source','defaults','hash','retry'])
def test_adapter_rejects_wrong_candidate_budget_and_baseline(mutation):
    authority,ledger,now=documents()
    a.validate_documents(authority,ledger,now)
    if mutation=='candidate': authority['candidate']='source9'
    elif mutation=='budget': authority['budgets']['native_POST']=9
    elif mutation=='baseline': authority['native_precision']='legacy-CIM-ticks'
    elif mutation=='expired': authority['expires_at']=(now-dt.timedelta(seconds=1)).isoformat()
    elif mutation=='kind': authority['kind']='source10_harness_preparation_only'
    elif mutation=='schema': ledger['schema']=2
    elif mutation=='model': authority['model']='other'
    elif mutation=='source': authority['candidate_manifest_sha256']='0'*64
    elif mutation=='defaults': authority['overrides']=['max_turns=20']
    elif mutation=='hash': authority['candidate']='0'*40
    elif mutation=='retry': ledger['consumed'].append('E02-controlled-2')
    with pytest.raises(ValueError): a.validate_documents(authority,ledger,now)

def test_pinned_import_rejects_cached_acceptance_adapter(monkeypatch):
    sentinel=types.ModuleType('acceptance_adapter'); sentinel.__file__=__file__
    monkeypatch.setitem(sys.modules,'acceptance_adapter',sentinel)
    with pytest.raises(ValueError,match='cached'): a.load_p4()
    assert sys.modules['acceptance_adapter'] is sentinel

@pytest.mark.parametrize('failure',['timeout','nonzero','invalidJSON','partialpacket','missingEND','cleanup','finalboundary','transientextra'])
def test_adapter_first_failure_retained_and_no_next_case(tmp_path,monkeypatch,failure,sdk_io,mock_jar):
    first,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch)
    p4=a.load_p4()
    protected=[dict(pid=pid,created_filetime=100,exe=sys.executable) for pid in range(51,58)]
    protected_rows=protected_fixture(tmp_path,monkeypatch,p4,protected)
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100,exe=sys.executable))
    monkeypatch.setattr(p4,'process_times',lambda proc:(100,0))
    monkeypatch.setattr(p4,'process_snapshot',lambda *args,**kwargs:dict(protected_rows))
    monkeypatch.setattr(p4,'terminate_owned',lambda key:None)
    monkeypatch.setattr(p4,'listener_owner',lambda port:[7891])
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    if failure in ('partialpacket','missingEND'):
        export=a.load(tmp_path/'trusted-export.json')
        if failure=='partialpacket': export['members']['runtime']['sha256']='0'*64
        else: export['END']=False
        (tmp_path/'trusted-export.json').write_text(json.dumps(export),encoding='utf8')
    pin_reads=[]
    def pins():
        pin_reads.append(1)
        return {'drift':'changed'} if failure=='finalboundary' and len(pin_reads)>=3 else {}
    monkeypatch.setattr(a,'check_inputs',pins)
    if failure=='transientextra':
        save=a.save_new
        def transient(path,value):
            save(path,value)
            if Path(path).name=='accepted-effects.json': (tmp_path/'outputs'/first['task_id']/'transient.md').write_bytes(b'known transient effect')
        monkeypatch.setattr(a,'save_new',transient)
    launches=[]
    class Proc:
        def __init__(self,cli):
            self.pid=7892 if cli else 7891; self.returncode=2 if cli and failure=='nonzero' else 0
        def wait(self,timeout=None):
            if failure=='timeout' and timeout and timeout>3: raise TimeoutError('CLI timeout')
            if failure=='transientextra' and timeout and timeout<=3: (tmp_path/'outputs'/first['task_id']/'transient.md').unlink(missing_ok=True)
            return self.returncode
    def launch(argv,env,out,err):
        launches.append(argv)
        if '--research' in argv: out.write('{broken' if failure=='invalidJSON' else json.dumps(first)); out.flush()
        return Proc('--research' in argv)
    # Patch only the actual launcher boundary; real P4 Owned.launch/discover/cleanup execute.
    root=a.C
    monkeypatch.syspath_prepend(str(root))
    from src.brain.tests import work_context_acceptance as helper
    monkeypatch.setattr(helper,'launch',launch)
    if failure=='cleanup':
        monkeypatch.setattr(p4,'terminate_owned',lambda key: (_ for _ in ()).throw(OSError('cleanup blocked')))
        monkeypatch.setattr(p4,'process_snapshot',lambda *args,**kwargs:dict(protected_rows) | {pid:dict(ProcessId=pid,CreationFileTime=100,ParentProcessId=0,CommandLine='') for pid in (7891,7892)})
    baseline=dict(candidate=a.CANDIDATE,precision='FILETIME100ns',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),protected=protected)
    context=dict(folder=tmp_path,port=18799,request_id='r',session_id='s',baseline=baseline,authority={},ledger={})
    result=a.execute_case(context,p4)
    assert len(launches)<=2
    assert result['work_cli_attempts']==1
    assert result['actual_native_start_count'] is None
    assert result['overall']=='FAIL'
    assert result['next_case'] is False
    expected={'timeout':'CLI timeout','nonzero':'CLI nonzero','invalidJSON':'Expecting property name','partialpacket':'Export member digest','missingEND':'Missing complete packet or END','cleanup':'cleanup terminate_owned: cleanup blocked','finalboundary':'final-boundary: Input drift','transientextra':'pre-cleanup-effects: Observed pre-cleanup output drift'}
    assert expected[failure] in result['first_failure']
    if failure=='cleanup': assert result['cleanup']['status']=='FAIL' and any(e.get('effects_unknown') for e in result['errors'])
    else: assert result['cleanup']['status']=='PASS'
    if failure=='transientextra':
        assert a.load(tmp_path/'accepted-effects.json')!=a.load(tmp_path/'pre-cleanup-effects.json')
        assert a.load(tmp_path/'accepted-effects.json')==a.load(tmp_path/'post-cleanup-effects.json')
    if failure not in ('timeout','invalidJSON'):
        assert json.loads((tmp_path/'product-result.json').read_text('utf8'))['marker']=='first'
    with pytest.raises(FileExistsError): a.execute_case(context,p4)
    assert len(launches)<=2

def test_adapter_reuses_owned_cleanup_and_retains_unknown_effect(tmp_path,monkeypatch):
    p4=a.load_p4()
    monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100+pid,exe=sys.executable))
    monkeypatch.setattr(p4,'process_snapshot',lambda *args,**kwargs:{5:dict(ParentProcessId=4,CommandLine='unknown')})
    owned=p4.Owned(tmp_path,{})
    owned.known[4]=dict(identity=dict(pid=4,created_filetime=104,exe=sys.executable),role='server',argv=[],parent=0)
    killed=[]; monkeypatch.setattr(p4,'terminate_owned',lambda key:killed.append(key))
    result=owned.cleanup()
    assert result['status']=='FAIL'
    assert not killed
    assert any(e.get('discovery')=='unknown-nested-descendant' for e in result['errors'])

@pytest.mark.parametrize('section',['source_files','sdk22','policy','model'])
def test_real_manifest_detects_input_hash_drift(monkeypatch,section):
    m=a.load(a.INPUTS_PATH)
    path=(next(iter(m['source_files'])) if section=='source_files' else a.SDK_SOURCES[0] if section=='sdk22' else next(p for p in m['files'] if p.endswith('jarvis-work-8b-model-policy-20261102.md')) if section=='policy' else m['model_manifest_path'])
    def changed(candidate):return b'changed' if candidate==Path(path) else candidate.read_bytes()
    monkeypatch.setattr(a.bindings,'load_inputs',lambda ignored:a.bindings.validate(m,read_bytes=changed))
    with pytest.raises(ValueError,match='Input bytes changed'): a.check_inputs()

def test_missing_or_preparation_authority_never_constructs_owned(monkeypatch):
    p4=a.load_p4(); constructed=[]
    monkeypatch.setattr(p4,'Owned',lambda *args:constructed.append(args))
    monkeypatch.setattr(a,'load_p4',lambda:p4)
    with pytest.raises(FileNotFoundError): a.run_case(a.V/'controller-authority'/f'{a.CASE}.json',a.V/'controller-ledger.json')
    with pytest.raises(ValueError): a.run_case(a.V/'inputs/scope.json',a.V/'controller-ledger.json')
    assert not constructed

@pytest.mark.parametrize('precision,drift',[('legacy-CIM',0),('FILETIME100ns',1),('FILETIME100ns',0)])
def test_native_baseline_requires_exact_integer_filetime(tmp_path,monkeypatch,precision,drift):
    protected=[dict(pid=p,created_filetime=100000001+p,exe='python') for p in range(1,8)]
    proof=dict(precision=precision,candidate=a.CANDIDATE,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),protected=protected)
    p4=a.load_p4()
    rows=protected_fixture(tmp_path,monkeypatch,p4,protected)
    monkeypatch.setattr(p4,'process_snapshot',lambda *args,**kwargs:rows)
    monkeypatch.setattr(p4,'identity',lambda pid:dict(protected[pid-1],created_filetime=protected[pid-1]['created_filetime']+drift))
    if precision=='FILETIME100ns' and drift==0: assert a.check_native_baseline(proof,p4)==protected
    else:
        with pytest.raises(ValueError): a.check_native_baseline(proof,p4)

@pytest.mark.parametrize('complete,end',[(False,False),(True,False)])
def test_real_export_reader_rejects_partial_or_missing_end(tmp_path,monkeypatch,complete,end):
    monkeypatch.syspath_prepend(str(a.C))
    a.save_new(tmp_path/'trusted-export.json',dict(complete=complete,END=end))
    a.save_new(tmp_path/'runtime-inputs.json',{})
    with pytest.raises(ValueError,match='END'): a.verify_exports(tmp_path,{},a.load_p4())

def test_original_browser_fixture_preserves_bodies_without_native_send_observer(monkeypatch):
    import ddgs,httpx,socket
    original_send=httpx.Client.send
    with monkeypatch.context() as scope:
        scope.setattr(ddgs,'DDGS',ddgs.DDGS); scope.setattr(httpx,'request',httpx.request); scope.setattr(socket,'getaddrinfo',socket.getaddrinfo)
        a.install_browser_fixture()
        assert httpx.Client.send is original_send
        sources=a.corpus()['sources']; hits=ddgs.DDGS().text(a.corpus()['query'])
        assert [h['href'] for h in hits]==[s['final_url'] for s in sources]
        for source in sources:
            response=httpx.request('GET',source['final_url'],follow_redirects=False,timeout=5)
            assert response.content==source['body'].encode('utf8')
        with pytest.raises(OSError): socket.getaddrinfo('other.example',443)

def test_runtime_inputs_captured_at_real_freeze_before_packet_exists(tmp_path,monkeypatch):
    monkeypatch.syspath_prepend(str(a.C))
    from src.brain.work_tools import WorkLedger,WorkBinding
    from src.brain.work_service import WorkService
    # Restore definitions after observing them in this isolated unit process.
    monkeypatch.setattr(WorkLedger,'__init__',WorkLedger.__init__)
    monkeypatch.setattr(WorkLedger,'_freeze_runtime_inputs',WorkLedger._freeze_runtime_inputs)
    monkeypatch.setattr(WorkService,'submit_work',WorkService.submit_work)
    a.install_trusted_exports(tmp_path)
    ledger=WorkLedger(); ledger._binding=WorkBinding(tmp_path,'r','s','t'); ledger._navigation=types.SimpleNamespace(binding_key=('r','s','t')); ledger.deadline=260.25
    ledger._freeze_runtime_inputs('trusted original prompt',None)
    saved=a.load(tmp_path/'runtime-inputs.json')
    assert saved==dict(prompt='trusted original prompt',binding_key=['r','s','t'],root=str(tmp_path),allowance=2048,deadline='260.25')
    assert not hasattr(ledger,'_runtime_final')
    with pytest.raises(ValueError): ledger._freeze_runtime_inputs('packet-derived forgery',None)
    assert a.load(tmp_path/'runtime-inputs.json')==saved

def test_inert_requires_separate_concrete_authority():
    prep=a.load(a.V/'inputs/scope.json')
    with pytest.raises(ValueError,match='Separate'): a.validate_inert_documents(prep,dt.datetime.now(dt.timezone.utc))

@pytest.mark.parametrize('failure',['hash','bytes','extra','escape','none'])
def test_real_external_readback_validates_hash_bytes_inventory_and_root(tmp_path,failure):
    p4=a.load_p4(); task='12345678-1234-4234-8234-123456789abc'
    folder=tmp_path; output=folder/'outputs'/task; output.mkdir(parents=True)
    path=output/'research.md'; path.write_bytes(b'original report')
    result=dict(task_id=task,artifacts=[dict(path=str(path),sha256=a.sha(path))])
    if failure=='hash': result['artifacts'][0]['sha256']='0'*64
    elif failure=='bytes': path.write_bytes(b'tampered report')
    elif failure=='extra': (output/'extra.txt').write_bytes(b'extra effect')
    elif failure=='escape': result['artifacts'][0]['path']=str(folder/'outside.md')
    if failure=='none': assert a.verify_readback(folder,result,p4,'original report')[0]['text']=='original report'
    else:
        with pytest.raises(ValueError): a.verify_readback(folder,result,p4,'original report')

# Deadline correction: real P4 algorithms, caller-local clocks and I/O only.
class Clock:
    def __init__(self): self.value=1000000000000
    def __call__(self): return self.value
    def advance(self,seconds): self.value+=int(seconds*1000000000)

def test_deadline_preclaim_charged_parent_no_rebase():
    clock=Clock(); budget=a.Deadline(clock=clock); origin=budget.origin_ns
    clock.advance(12)
    assert budget.remaining_ns()==263000000000
    budget.adopt_parent(dict(origin_ns=origin-1000000000,clock_domain=a.CLOCK_DOMAIN,run_id=budget.run_id))
    assert budget.origin_ns==origin-1000000000
    with pytest.raises(ValueError): budget.adopt_parent(dict(origin_ns=clock(),clock_domain=a.CLOCK_DOMAIN,run_id=budget.run_id))

@pytest.mark.parametrize('offset,admitted',[(274999999999,True),(275000000000,False),(275000000001,False)])
def test_deadline_strict_admission_inclusive_return(offset,admitted):
    clock=Clock(); budget=a.Deadline(clock=clock); clock.value=budget.origin_ns+offset
    if admitted: budget.pre('work')
    else:
        with pytest.raises(TimeoutError): budget.pre('work')
    clock.value=budget.origin_ns+275000000000; budget.post('work')

def test_private_snapshot_timeouts_decrease_late_return_and_restore(monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4(); original=p4.subprocess; calls=[]
    def checkout(argv,**kwargs):
        calls.append((argv,kwargs['timeout'])); clock.advance(8); return b'[]'
    monkeypatch.setattr(original,'check_output',checkout)
    clock.advance(255)
    with a.PrivateIO(p4,budget) as io:
        p4.process_snapshot(); p4.process_snapshot()
        with pytest.raises(TimeoutError): p4.process_snapshot()
    assert [round(x[1]) for x in calls]==[15,12,4]
    assert p4.subprocess is original

def test_real_popen_identity_wait_clipping_and_restoration():
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4()
    import subprocess
    proc=object.__new__(subprocess.Popen); proc._handle=object(); handle=proc._handle
    calls=[]
    def wait(timeout=None): calls.append(timeout); return 0
    proc.wait=wait
    owned=types.SimpleNamespace(launchers=[dict(proc=proc)])
    with a.PrivateIO(p4,budget) as io:
        io.wrap_waits(owned); assert proc._handle is handle
        clock.advance(274); proc.wait(timeout=300)
    assert proc.wait is wait and calls==[1.0]

@pytest.mark.parametrize('seconds,entered',[(9.999999999,False),(10,True),(11,True)])
def test_termination_full_ten_second_admission(monkeypatch,seconds,entered):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); calls=[]
    # Admission boundary test; separate native test below exercises original P1.
    monkeypatch.setattr(p4,'terminate_owned',lambda key:calls.append(key))
    clock.value=budget.origin_ns+310000000000-int(seconds*1000000000)
    with a.PrivateIO(p4,budget) as io:
        if entered: p4.terminate_owned(dict(pid=7))
        else:
            with pytest.raises(TimeoutError): p4.terminate_owned(dict(pid=7))
    assert bool(calls)==entered

@pytest.mark.parametrize('code,closed',[(10061,True),(111,111 in {a.errno.ECONNREFUSED,10061}),(10060,False),(0,False)])
def test_private_port_probe_requires_definitive_refusal(monkeypatch,code,closed):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); probes=[]
    class Probe:
        def __init__(self): self.closed=False; probes.append(self)
        def settimeout(self,value): pass
        def connect_ex(self,address): return code
        def close(self): self.closed=True
    monkeypatch.setattr(p4.socket,'socket',Probe)
    with a.PrivateIO(p4,budget) as io:
        probe=p4.socket.socket(); probe.settimeout(1)
        try: probe.connect_ex(('127.0.0.1',18799))
        finally: probe.close()
        assert io.port_closed is closed
    assert probes[0].closed

@pytest.mark.parametrize('offset,expected',[(314999999999,True),(315000000000,True),(315000000001,False)])
def test_enclosing_witness_timely_exact315_late_and_permanent(offset,expected):
    clock=Clock(); budget=a.Deadline(clock=clock)
    observer=a.TimingObservation(budget)
    clock.value=budget.origin_ns+offset
    witness=observer.finish('digest',dict(cleanup=True,closed=True,pins=True,protected=True,readback=True))
    assert witness['eligible'] is expected
    with pytest.raises(ValueError): observer.finish('digest',dict(cleanup=True,closed=True,pins=True,protected=True,readback=True))

class NativeFunction:
    def __init__(self,function): self.function=function
    def __call__(self,*args): return self.function(*args)

def native_kernel(monkeypatch,p4,active,clock,wait_seconds=0):
    calls=[]
    def opened(access,inherit,pid): calls.append(('open',access,pid)); return pid+1000
    def times(handle,*values):
        for item in values: item._obj.dwLowDateTime=0; item._obj.dwHighDateTime=0
        values[0]._obj.dwLowDateTime=1000000+int(handle)-1000
        return 1
    def image(handle,flags,buffer,size): buffer.value=sys.executable; return 1
    def terminate(handle,code): calls.append(('terminate',int(handle)-1000)); active.discard(int(handle)-1000); return 1
    def wait(handle,milliseconds): calls.append(('wait',milliseconds)); clock.advance(wait_seconds); return 0
    kernel=types.SimpleNamespace(**{name:NativeFunction(func) for name,func in dict(OpenProcess=opened,CloseHandle=lambda h:calls.append(('close',h)),GetProcessTimes=times,QueryFullProcessImageNameW=image,TerminateProcess=terminate,WaitForSingleObject=wait).items()})
    monkeypatch.setattr(p4.old.C,'WinDLL',lambda *args,**kwargs:kernel)
    return kernel,calls

def test_original_p1_primitive_overrun_closes_handle_and_never_later_succeeds(monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); active={77}
    kernel,calls=native_kernel(monkeypatch,p4,active,clock,wait_seconds=11)
    key=p4.identity(77); original=p4.old.terminate_owned
    clock.value=budget.origin_ns+299500000000
    with a.PrivateIO(p4,budget) as io:
        with pytest.raises(TimeoutError,match='Late'): p4.terminate_owned(key)
        assert io.events[-1]['entered'] and io.events[-1]['returned'] and io.events[-1]['late']
    assert ('wait',10000) in calls and calls[-1][0]=='close'
    assert p4.old.terminate_owned is original
    assert not a.TimingObservation(budget).finish('digest',dict(cleanup=True,closed=True,pins=True,protected=True,readback=True))['eligible']

def test_original_p1_identity_mismatch_never_terminates(monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); active={77}
    _,calls=native_kernel(monkeypatch,p4,active,clock)
    key=dict(p4.identity(77),created_filetime=1)
    with a.PrivateIO(p4,budget):
        with pytest.raises(ValueError,match='identity mismatch'): p4.terminate_owned(key)
    assert not any(call[0]=='terminate' for call in calls)

@pytest.mark.parametrize('count',[2,4,7])
def test_real_p4_cleanup_native_snapshot_and_original_termination(tmp_path,monkeypatch,count):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); active=set(range(10,10+count))
    _,calls=native_kernel(monkeypatch,p4,active,clock)
    monkeypatch.setattr(p4,'protected',lambda:[])
    observed=[]
    def checkout(argv,**kwargs):
        observed.append((argv,kwargs['timeout'])); clock.advance(.1)
        return json.dumps([dict(ProcessId=pid,CreationFileTime=p4.identity(pid)['created_filetime'],ParentProcessId=0,CommandLineBase64='') for pid in sorted(active)]).encode('ascii')
    monkeypatch.setattr(p4.subprocess,'check_output',checkout)
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    owned=p4.Owned(tmp_path,{})
    for pid in active: owned.known[pid]=dict(identity=p4.identity(pid),role='server',argv=[],parent=0)
    with a.PrivateIO(p4,budget) as io: result=io.cleanup(owned,18799)
    assert result['status']=='PASS' and result['port_definitively_closed']
    assert len([c for c in calls if c[0]=='terminate'])==count
    assert not active and observed
    assert all(x[1]<=15 for x in observed)

def test_launch_registration_failure_retains_possible_effect_and_wraps_wait(tmp_path,monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4()
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100,exe=sys.executable)); monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.syspath_prepend(str(a.C))
    from src.brain.tests import work_context_acceptance as helper
    import subprocess
    proc=object.__new__(subprocess.Popen); proc.pid=999; proc._handle=object(); handle=proc._handle; proc.wait=lambda timeout=None:0
    original_wait=proc.wait
    monkeypatch.setattr(helper,'launch',lambda *args:proc)
    # Real discover fails at the OS snapshot boundary after original registration.
    monkeypatch.setattr(p4.subprocess,'check_output',lambda *args,**kwargs: (_ for _ in ()).throw(OSError('snapshot unavailable')))
    owned=p4.Owned(tmp_path,{})
    with a.PrivateIO(p4,budget) as io:
        with pytest.raises(OSError): io.launch(owned,['-B','script'],'server')
        assert proc.wait is not original_wait and proc._handle is handle
        assert io.launch_attempts[0]['possible_live_effect'] and len(owned.launchers)==1
    assert proc.wait is original_wait
    for stream in owned.logs: stream.close()

def test_launch_failure_before_registration_retains_unknown_live_effect(tmp_path,monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4()
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100,exe=sys.executable)); monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.syspath_prepend(str(a.C))
    from src.brain.tests import work_context_acceptance as helper
    monkeypatch.setattr(helper,'launch',lambda *args: (_ for _ in ()).throw(OSError('creation outcome unknown')))
    owned=p4.Owned(tmp_path,{})
    with a.PrivateIO(p4,budget) as io:
        with pytest.raises(OSError): io.launch(owned,['-B','script'],'server')
        assert not owned.known and io.launch_attempts[0]['possible_live_effect']
    for stream in owned.logs: stream.close()

def test_readiness_late_listener_cannot_dispatch(monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4(); proofs=[]
    def listener(port): clock.advance(31); return [1]
    monkeypatch.setattr(p4,'listener_owner',listener); monkeypatch.setattr(p4,'assert_listener',lambda *args:proofs.append(args))
    with pytest.raises(TimeoutError,match='Late listener'): a.ready_listener(p4,None,18799,[],budget)
    assert not proofs

@pytest.mark.parametrize('failure',['missing_snapshot','log_close','socket_timeout'])
def test_cleanup_uncertainty_is_never_pass(tmp_path,monkeypatch,failure):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4()
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100,exe=sys.executable)); monkeypatch.setattr(p4,'protected',lambda:[])
    count=[]
    def checkout(*args,**kwargs):
        count.append(1)
        if failure=='missing_snapshot' and len(count)>1: raise OSError('snapshot missing')
        return b'[]'
    monkeypatch.setattr(p4.subprocess,'check_output',checkout)
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return 10060 if failure=='socket_timeout' else a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    owned=p4.Owned(tmp_path,{})
    if failure=='log_close':
        class BadLog:
            closed=False
            def close(self): raise OSError('close failed')
        owned.logs=[BadLog()]
    with a.PrivateIO(p4,budget) as io: result=io.cleanup(owned,18799)
    assert result['status']=='FAIL'

def test_private_bindings_shared_identity_survives_two_exception_scopes():
    import subprocess,time,socket
    p4=a.load_p4(); original=(subprocess.check_output,time.monotonic,time.sleep,socket.socket,p4.old.terminate_owned)
    for _ in range(2):
        fresh=a.load_p4(); saved=(fresh.subprocess,fresh.time,fresh.socket,fresh.terminate_owned,fresh.save)
        with pytest.raises(RuntimeError):
            with a.PrivateIO(fresh,a.Deadline()): raise RuntimeError('scope failure')
        assert saved==(fresh.subprocess,fresh.time,fresh.socket,fresh.terminate_owned,fresh.save)
        assert original==(subprocess.check_output,time.monotonic,time.sleep,socket.socket,p4.old.terminate_owned)

@pytest.mark.parametrize('missing,late',[('none',False),('seal-index.json',False),('data',False),('none',True)])
def test_root_observes_closed_package_after_return_no_missing_or_late_promotion(tmp_path,missing,late):
    clock=Clock(); invocation=a.RootInvocation(clock=clock); b=invocation.budget; p4=a.load_p4()
    required={'attempt.json','argv-roundtrip.json','native-argv.json','native-argv.raw','listener.json','owned-tree.json','cleanup.json','protected-before.json','protected-after.json','server.stdout','server.stderr'}
    def entry():
        b.phase='seal'
        for name in required: a.save_new(tmp_path/name,{})
        terminal=dict(kind='inert',folder=str(tmp_path),run_id=b.run_id,overall='READY_FOR_ROOT_TIMING_WITNESS',cleanup=dict(status='PASS',port_definitively_closed=True,logs_closed=True),errors=[])
        a.save_new(tmp_path/'terminal.json',terminal); a.seal_index(tmp_path,b,p4)
        if missing=='seal-index.json': (tmp_path/'seal-index.json').unlink()
        if missing=='data': (tmp_path/'native-argv.raw').unlink()
        clock.value=b.origin_ns+(315000000001 if late else 314999999999)
        return terminal
    observed=invocation.call(entry)
    assert observed['witness']['eligible'] is False  # Empty member objects are never substantive proof.
    assert observed['witness']['observed_ns']==clock()
    with pytest.raises(ValueError): invocation.call(lambda:observed['result'])

def test_missing_witness_or_uncertain_proof_never_eligible():
    for key in ('cleanup','closed','pins','protected','readback'):
        proof=dict(cleanup=True,closed=True,pins=True,protected=True,readback=True); proof.pop(key)
        assert not a.TimingObservation(a.Deadline()).finish('digest',proof)['eligible']
    assert not a.TimingObservation(a.Deadline()).finish(None,dict(cleanup=True,closed=True,pins=True,protected=True,readback=True))['eligible']

def test_client_at_work_cutoff_retains_first_result_but_cannot_validate_or_pass(tmp_path,monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4(); processes=[]
    monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.setattr(p4,'identity',lambda pid:dict(pid=pid,created_filetime=100,exe=sys.executable))
    monkeypatch.setattr(p4,'process_times',lambda proc:(100,0))
    def checkout(argv,**kwargs): return '7891' if 'Get-NetTCPConnection' in argv[-1] else b'[]'
    monkeypatch.setattr(p4.subprocess,'check_output',checkout)
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    monkeypatch.setattr(a,'check_inputs',lambda:{})
    monkeypatch.setattr(a,'check_native_baseline',lambda *args:[])
    monkeypatch.syspath_prepend(str(a.C))
    from src.brain.tests import work_context_acceptance as helper
    class Proc:
        returncode=0
        def __init__(self,pid): self.pid=pid; self._handle=object()
        def wait(self,timeout=None):
            if self.pid==7892 and timeout>3: clock.value=budget.cutoff_ns('work')
            return 0
    def launch(argv,env,out,err):
        proc=Proc(7892 if '--research' in argv else 7891); processes.append(proc)
        if '--research' in argv: out.write(json.dumps(dict(status='succeeded',marker='first',request_id='r',session_id='s'))); out.flush()
        return proc
    monkeypatch.setattr(helper,'launch',launch)
    context=dict(folder=tmp_path,port=18799,request_id='r',session_id='s',baseline={},authority={},ledger={},budget=budget)
    result=a.execute_case(context,p4)
    assert result['overall']=='FAIL' and result['work_cli_attempts']==1
    assert 'Deadline' in result['first_failure']
    assert result['effective_client_seconds']==275
    assert a.load(tmp_path/'product-result.json')['marker']=='first'
    assert (tmp_path/'first-product.raw').exists()
    assert result['timing_eligibility']=='UNOBSERVED_NEVER_TIMED_PASS'

def test_cleanup_discovers_later_matching_child_without_count_truncation(tmp_path,monkeypatch):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); active={10,11}
    _,calls=native_kernel(monkeypatch,p4,active,clock)
    monkeypatch.setattr(p4,'protected',lambda:[])
    argv=['-B','samecase']; command=json.dumps([sys.executable,*argv])
    monkeypatch.setattr(p4,'argv_parse',lambda text:json.loads(text))
    monkeypatch.setattr(p4,'process_times',lambda proc:(1000010,0))
    def checkout(argv,**kwargs):
        import base64
        return json.dumps([dict(ProcessId=pid,CreationFileTime=p4.identity(pid)['created_filetime'],ParentProcessId=10 if pid==11 else 0,CommandLineBase64=base64.b64encode(command.encode('utf-16-le')).decode('ascii')) for pid in sorted(active)]).encode('ascii')
    monkeypatch.setattr(p4.subprocess,'check_output',checkout)
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    proc=types.SimpleNamespace(pid=10,wait=lambda timeout=None:0)
    owned=p4.Owned(tmp_path,{})
    owned.launchers=[dict(proc=proc,identity=p4.identity(10),argv=argv,role='server')]
    owned.known[10]=dict(identity=p4.identity(10),argv=argv,role='server',parent=0)
    with a.PrivateIO(p4,budget) as io: result=io.cleanup(owned,18799)
    assert result['status']=='PASS' and 11 in owned.known
    assert len([c for c in calls if c[0]=='terminate'])==2

@pytest.mark.parametrize('failure',['nested','drift'])
def test_private_cleanup_unknown_nested_or_reused_identity_never_authorizes_kill(tmp_path,monkeypatch,failure):
    clock=Clock(); budget=a.Deadline(clock=clock); budget.phase='cleanup'; p4=a.load_p4(); active={11,12} if failure=='nested' else {11}
    kernel,calls=native_kernel(monkeypatch,p4,active,clock)
    monkeypatch.setattr(p4,'protected',lambda:[])
    monkeypatch.setattr(p4.subprocess,'check_output',lambda *args,**kwargs:json.dumps([dict(ProcessId=pid,CreationFileTime=p4.identity(pid)['created_filetime'],ParentProcessId=11 if pid==12 else 0,CommandLineBase64='') for pid in sorted(active)]).encode('ascii'))
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    owned=p4.Owned(tmp_path,{})
    owned.known[11]=dict(identity=p4.identity(11),argv=[],role='server',parent=0)
    if failure=='drift': owned.known[11]['identity']['created_filetime']-=1
    with a.PrivateIO(p4,budget) as io: result=io.cleanup(owned,18799)
    assert result['status']=='FAIL'
    assert (12 if failure=='nested' else 11) in active
    assert ('terminate',12 if failure=='nested' else 11) not in calls

def test_clipped_wait_preserves_timeout_exception_and_private_sleep_overshoot(monkeypatch):
    import subprocess
    clock=Clock(); budget=a.Deadline(clock=clock); p4=a.load_p4()
    proc=types.SimpleNamespace(_handle=object())
    def wait(timeout=None): raise subprocess.TimeoutExpired('unchanged command',timeout)
    proc.wait=wait
    fake_time=types.SimpleNamespace(monotonic=lambda:clock()/1000000000,sleep=lambda seconds:clock.advance(seconds+1))
    monkeypatch.setattr(p4,'time',fake_time)
    with a.PrivateIO(p4,budget) as io:
        io.wrap_waits(types.SimpleNamespace(launchers=[dict(proc=proc)]))
        with pytest.raises(subprocess.TimeoutExpired) as caught: proc.wait(timeout=3)
        assert caught.value.timeout==3 and caught.value.cmd=='unchanged command'
        clock.value=budget.cutoff_ns()-1000000000
        with pytest.raises(TimeoutError,match='Late'): p4.time.sleep(2)
    assert proc.wait is wait and p4.time is fake_time

def test_fix1_h05_unrelated_protected_five_rejected(monkeypatch):
    p4=a.load_p4(); unrelated=[dict(pid=p,created_filetime=100+p,exe='python') for p in range(1,6)]
    monkeypatch.setattr(p4,'identity',lambda pid:unrelated[pid-1])
    monkeypatch.setattr(p4,'protected',lambda:[dict(pid=p,created_filetime=100+p,exe='python') for p in range(11,16)])
    proof=dict(precision='FILETIME100ns',candidate=a.CANDIDATE,recorded_at=dt.datetime.now(dt.timezone.utc).isoformat(),protected=unrelated)
    with pytest.raises(ValueError,match='protected member'): a.check_native_baseline(proof,p4)

def test_fix1_h06_alternate_interpreter_same_flags_rejected(monkeypatch):
    monkeypatch.setattr(sys,'executable','C:/other/python.exe')
    with pytest.raises(ValueError,match='interpreter'): a.check_inputs()

@pytest.mark.parametrize('fault',['flags','identity','attempt','replay','none'])
def test_fix1_h01_one_use_native_child_clearance(tmp_path,monkeypatch,fault):
    clock=Clock(); b=a.Deadline(clock=clock); p4=a.load_p4()
    key=dict(pid=77,created_filetime=123,exe=sys.executable)
    monkeypatch.setattr(p4,'identity',lambda pid:key)
    context=dict(folder=tmp_path,port=18799,budget=b,mode='inert',authority={},request_id='r',session_id='s')
    a.save_new(tmp_path/'attempt.json',dict(parent_timing=b.timing()))
    argv=a.inert_argv(tmp_path,18799)
    root=dict(pid=1,created_filetime=122,exe=str(a.PY))
    record=dict(mode='inert',folder=str(tmp_path),timing=b.timing(),argv=argv,attempt_sha256=a.sha(tmp_path/'attempt.json'),authority_sha256='authority',launcher_identity=root,base_identity=key,members=[dict(identity=root,role='server',parent=0),dict(identity=key,role='server',parent=1)])
    a.save_new(tmp_path/'child-clearance.json',record)
    a.write_raw_new(tmp_path/'child-clearance.ready',b'')
    supplied=list(argv)
    if fault=='flags': supplied.remove('--runtime-root')
    elif fault=='identity': monkeypatch.setattr(p4,'identity',lambda pid:dict(key,created_filetime=124))
    elif fault=='attempt': (tmp_path/'attempt.json').write_text('{}')
    elif fault=='replay': a.save_new(tmp_path/'child-clearance.consumed.json',{})
    if fault=='none': assert a.consume_clearance(context,p4,supplied,'authority')==key
    else:
        with pytest.raises((ValueError,FileExistsError)): a.consume_clearance(context,p4,supplied,'authority')

@pytest.mark.parametrize('rows',['empty','subset','parent','none'])
def test_fix1_h04_native_member_set_not_vacuous(tmp_path,monkeypatch,rows):
    p4=a.load_p4(); root=dict(pid=1,created_filetime=101,exe=sys.executable); child=dict(pid=2,created_filetime=102,exe=sys.executable)
    monkeypatch.setattr(p4,'identity',lambda pid:{1:root,2:child}[pid]); monkeypatch.setattr(p4,'argv_parse',lambda text:json.loads(text)); monkeypatch.setattr(p4,'process_times',lambda proc:(101,0))
    argv=['-B','script']; owned=types.SimpleNamespace(known={1:dict(identity=root,role='server',parent=0),2:dict(identity=child,role='server',parent=1)},launchers=[dict(proc=types.SimpleNamespace(pid=1),identity=root,argv=argv,role='server')])
    snapshot={1:dict(ParentProcessId=0,CommandLine=json.dumps([sys.executable,*argv])),2:dict(ParentProcessId=99 if rows=='parent' else 1,CommandLine=json.dumps([sys.executable,*argv]))}
    if rows=='empty': snapshot={}
    elif rows=='subset': snapshot.pop(1)
    listener=dict(identity=child,argv=argv,role='server')
    if rows=='none': assert a.validate_native_members(owned,p4,snapshot,listener,argv)['live_pids']==[1,2]
    else:
        with pytest.raises(ValueError): a.validate_native_members(owned,p4,snapshot,listener,argv)

def test_fix1_h12_socket_timeout_reclipped_at_connect(monkeypatch):
    clock=Clock(); b=a.Deadline(clock=clock); b.phase='cleanup'; clock.value=b.cutoff_ns()-1000000000
    p4=a.load_p4(); waits=[]
    class Probe:
        def __init__(self): clock.advance(.8)
        def settimeout(self,value): waits.append(value)
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    with a.PrivateIO(p4,b) as io:
        probe=p4.socket.socket(); probe.settimeout(1)
        try: probe.connect_ex(('127.0.0.1',18799))
        finally: probe.close()
    assert waits[-1]==pytest.approx(.2)

def test_fix1_h12_setup_overrun_cannot_admit_connect_and_still_closes(monkeypatch):
    clock=Clock(); b=a.Deadline(clock=clock); b.phase='cleanup'; clock.value=b.cutoff_ns()-1000000000
    p4=a.load_p4(); connected=[]; closed=[]
    class Probe:
        def settimeout(self,value): clock.advance(.6)
        def connect_ex(self,address): connected.append(address); return a.errno.ECONNREFUSED
        def close(self): closed.append(True)
    monkeypatch.setattr(p4.socket,'socket',Probe)
    with a.PrivateIO(p4,b):
        probe=p4.socket.socket(); probe.settimeout(1)
        try:
            with pytest.raises(TimeoutError): probe.connect_ex(('127.0.0.1',18799))
        finally: probe.close()
    assert not connected and closed

@pytest.mark.parametrize('field',['request_id','session_id','task_id','status','artifacts','none'])
def test_fix1_h13_service_cli_invariants(field):
    first=dict(request_id='r',session_id='s',task_id='t',status='succeeded',artifacts=[dict(path='p',sha256='h',verified=True)])
    service=json.loads(json.dumps(first))
    if field!='none': service[field]=[] if field=='artifacts' else 'different'
    if field=='none': a.reconcile_results(first,service)
    else:
        with pytest.raises(ValueError,match='service/CLI'): a.reconcile_results(first,service)

def test_fix1_h08_first_cause_cleanup_then_boundary_never_replaced():
    b=a.Deadline(); errors=[]
    a.record_failure(b,errors,'cleanup','returned FAIL',effects_unknown=True)
    a.record_failure(b,errors,'final-boundary','later drift')
    assert b.failure=='cleanup: returned FAIL' and errors[0]['effects_unknown']

def test_fix1_h14_observer_late_first_read_stops_following_io(tmp_path,monkeypatch):
    clock=Clock(); invocation=a.RootInvocation(clock=clock); b=invocation.budget; reads=[]
    def read(path): reads.append(path); clock.value=b.cutoff_ns('seal')+1; return {}
    monkeypatch.setattr(a,'load',read)
    outcome=invocation.call(lambda:dict(folder=str(tmp_path)))
    assert len(reads)==1 and not outcome['witness']['eligible']

def test_fix1_genuine_synthetic_export_and_external_readback(tmp_path,monkeypatch,sdk_io,mock_jar):
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch)
    verified=a.verify_exports(tmp_path,result,a.load_p4())
    assert verified['native_POST_attempts']==5 and len(verified['inventory'])==1
    assert a.read_completed(tmp_path,a.load(tmp_path/'trusted-export.json'))['runtime']==ledger._runtime_final

@pytest.mark.parametrize('size',[3*1024*1024,4*1024*1024])
def test_fix1_h07_sizable_and_max_safe_raw_representation(tmp_path,monkeypatch,sdk_io,mock_jar,size):
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    empty=json.dumps(dict(events=[],padding=''),separators=(',',':')).encode()
    raw=json.dumps(dict(events=[],padding='a'*(size-len(empty))),separators=(',',':')).encode()
    # Representation unit after a safe-completion boundary; this padded packet
    # is not claimed to be a valid product replay. The genuine companion above is.
    a.preserve_completed_members(tmp_path,raw,ledger.issued_snapshot,ledger._collection,result,5)
    exported=a.load(tmp_path/'trusted-export.json')
    assert len(raw)==size and a.read_completed(tmp_path,exported)['runtime']==raw
    assert (tmp_path/'trusted-export.json').stat().st_size<4096

def test_fix1_h07_unsafe_completed_values_never_exported(tmp_path,monkeypatch,sdk_io,mock_jar):
    from src.brain.work_navigation import canonical_v3
    from src.brain.tests.test_work_navigation_transport import escaped_scanner_fixture,escaped_envelope,rewrite_response
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    packet=json.loads(ledger._runtime_final); value=dict(final_answer=escaped_scanner_fixture()); encoded=escaped_envelope(value)
    assert all(s.scan(encoded).clean for s in ledger._policy.scanners)
    assert any(not s.scan(value['final_answer']).clean for s in ledger._policy.scanners)
    rewrite_response(packet,len(packet['wires'])-1,value,encoded)
    ledger._runtime_final=canonical_v3(packet)
    with pytest.raises(ValueError,match='Unsafe native evidence string'): a.export_completed(tmp_path,ledger,result)
    assert not list(tmp_path.glob('trusted-*.raw'))

@pytest.mark.parametrize('fault',['remove','replace','extra'])
def test_fix1_h03_closed_output_drift_rejected(tmp_path,fault):
    p4=a.load_p4(); task='12345678-1234-4234-8234-123456789abc'; output=tmp_path/'outputs'/task; output.mkdir(parents=True)
    path=output/'research.md'; path.write_bytes(b'accepted')
    result=dict(task_id=task,artifacts=[dict(path=str(path),sha256=a.sha(path))]); accepted=p4.output_inventory(tmp_path)
    if fault=='remove': path.unlink()
    elif fault=='replace': path.write_bytes(b'changed')
    else: (output/'extra.md').write_bytes(b'extra')
    with pytest.raises(ValueError,match='output drift'): a.validate_final_outputs(tmp_path,result,accepted,p4)

@pytest.mark.parametrize('which',['harness','approval','authority','baseline'])
def test_fix1_h09_late_operational_drift_rejected(tmp_path,monkeypatch,which):
    paths=[]
    for name in ('harness','approval','authority','baseline'):
        path=tmp_path/name; path.write_text(name); paths.append(path)
    monkeypatch.setattr(a,'check_inputs',lambda:{})
    monkeypatch.setattr(a,'operational_paths',lambda mode:paths)
    budget=a.Deadline(); admitted=dict(mode='inert',pins=a.operational_pins('inert',budget))
    (tmp_path/which).write_text('late drift')
    with pytest.raises(ValueError,match='pin drift'): a.compare_operational_pins(admitted,budget)

def test_fix1_h06_cached_sdk_import_origin_rejected(monkeypatch):
    fake=types.ModuleType('openjarvis.agents.native_react'); fake.__file__='C:/unapproved/native_react.py'
    monkeypatch.setitem(sys.modules,'openjarvis.agents.native_react',fake)
    with pytest.raises(ValueError,match='Import origin'): a.check_import_origins()

@pytest.mark.parametrize('fault',['harness','input','addition','none'])
def test_fix1_h10_driver_drift_fails_even_with_pytest_zero(tmp_path,monkeypatch,fault):
    spec=importlib.util.spec_from_file_location('driver_control',Path(__file__).with_name('run_checks.py'))
    driver=importlib.util.module_from_spec(spec); spec.loader.exec_module(driver)
    here=tmp_path/'harness'; here.mkdir(); input_file=tmp_path/'input'; input_file.write_bytes(b'original')
    for source in Path(__file__).parent.iterdir():
        if source.is_file(): (here/source.name).write_bytes(source.read_bytes())
    (tmp_path/'verification').mkdir()
    (tmp_path/'verification/offline_pytest.py').write_bytes((a.V/'verification/offline_pytest.py').read_bytes())
    monkeypatch.setattr(driver,'HERE',here); monkeypatch.setattr(driver,'V',tmp_path)
    monkeypatch.setattr(driver,'snapshot',lambda:{str(input_file):driver.digest(input_file)})
    monkeypatch.setattr(sys,'argv',['run_checks.py','adapter'])
    def pytest_process(*args,**kwargs):
        if fault=='harness': (here/'README.md').write_bytes(b'changed')
        elif fault=='input': input_file.write_bytes(b'changed')
        elif fault=='addition': (here/'seventh.txt').write_bytes(b'extra')
        return types.SimpleNamespace(returncode=0,stdout=b'controlled pytest success',stderr=b'')
    monkeypatch.setattr(driver.subprocess,'run',pytest_process)
    status=driver.main(); receipt=a.load(next((tmp_path/'code').glob('harness-preparation-*/receipt.json')))
    assert (status==0)==(fault=='none') and receipt['pytest_exit_code']==0
    assert receipt['exit_code']==status

def test_fix1_h11_import_path_restored_on_failure():
    original=list(sys.path)
    with pytest.raises(ValueError):
        with a.candidate_import_path():
            assert sys.path[0]==str(a.C); raise ValueError('injected')
    assert sys.path==original

def _substantive_closed_witness_fixture(tmp_path,monkeypatch,fault,observer_port=None):
    import base64,os
    from collections import OrderedDict
    original_v=a.V; original_here=a.HERE
    virtual=tmp_path/'virtual-root'; here=virtual/'harness'; here.mkdir(parents=True)
    for source in original_here.iterdir():
        if source.is_file(): (here/source.name).write_bytes(source.read_bytes())
    (virtual/'inputs').mkdir()
    (virtual/'inputs/scope.json').write_bytes((original_v/'inputs/scope.json').read_bytes())
    monkeypatch.setattr(a,'V',virtual); monkeypatch.setattr(a,'HERE',here)
    package=a.load(here/'manifest.json')
    package['files']={name:a.sha(here/name) for name in package['files']}
    (here/'manifest.json').write_text(json.dumps(package),encoding='utf8')
    a.save_new(virtual/'harness-approval.json',dict(reviewer='root-independent',overall='PASS',manifest_sha256=a.sha(here/'manifest.json')))
    clock=Clock(); invocation=a.RootInvocation(clock=clock); b=invocation.budget
    folder=virtual/'inert'/b.run_id; folder.mkdir(parents=True)
    p4=a.load_p4(); active=set(); _,calls=native_kernel(monkeypatch,p4,active,clock)
    protected=[p4.identity(pid) for pid in range(51,58)]
    protected_rows=protected_fixture(virtual,monkeypatch,p4,protected)
    monkeypatch.setattr(p4,'process_times',lambda proc:(1000001,0))
    monkeypatch.setattr(p4,'argv_parse',lambda text:json.loads(text))
    monkeypatch.setattr(a,'load_p4',lambda:p4)
    authority=dict(kind='source10_inert_qualification',folder=str(folder),port=18799,parent_timing=b.timing())
    a.save_new(virtual/'inert-authority.json',authority)
    baseline=dict(protected=protected,candidate=a.CANDIDATE,precision='FILETIME100ns',recorded_at=dt.datetime.now(dt.timezone.utc).isoformat())
    a.save_new(virtual/'inert-native-baseline.json',baseline)
    argv=a.inert_argv(folder,18799); snapshot_live=[True]; http_calls=[]
    command=json.dumps([str(a.PY),*argv])
    def checkout(cmd,**kwargs):
        if 'Get-NetTCPConnection' in cmd[-1]: return '2' if snapshot_live[0] else '[]'
        rows=[dict(ProcessId=pid,CreationFileTime=p4.identity(pid)['created_filetime'],ParentProcessId=0 if pid==1 else 1,CommandLineBase64=base64.b64encode(command.encode('utf-16-le')).decode('ascii')) for pid in (1,2)] if snapshot_live[0] else []
        rows.extend(dict(row,CommandLineBase64=base64.b64encode(row['CommandLine'].encode('utf-16le')).decode('ascii')) for row in protected_rows.values())
        requested={int(value) for value in a.re.findall(r'ProcessId=(\d+)',cmd[-1])}
        if requested: rows=[row for row in rows if row['ProcessId'] in requested]
        return json.dumps(rows).encode('ascii')
    monkeypatch.setattr(p4.subprocess,'check_output',checkout)
    class Probe:
        def settimeout(self,value): pass
        def connect_ex(self,address): return a.errno.ECONNREFUSED
        def close(self): pass
    monkeypatch.setattr(p4.socket,'socket',Probe)
    class Response:
        def __enter__(self): return self
        def __exit__(self,*args): pass
        def read(self): return b'{"inert":true}'
    class Opener:
        def open(self,url,timeout): http_calls.append((url,timeout)); clock.advance(.001); return Response()
    monkeypatch.setattr(p4.urllib.request,'build_opener',lambda *args:Opener())
    def entry():
        admitted=a.admitted_record('inert',folder,18799,authority,baseline,b)
        a.save_new(folder/'admission.json',admitted)
        a.save_new(folder/'attempt.json',dict(parent_timing=b.timing()))
        owned=p4.Owned(folder,{}); b.owned=owned
        proc=types.SimpleNamespace(pid=1,wait=lambda timeout=None:0)
        owned.launchers=[dict(proc=proc,identity=p4.identity(1),argv=argv,role='server')]
        owned.known[1]=dict(identity=p4.identity(1),argv=argv,role='server',parent=0)
        owned.logs=[open(folder/'server.stdout','w'),open(folder/'server.stderr','w')]
        context=dict(mode='inert',folder=folder,port=18799,budget=b)
        with a.PrivateIO(p4,b) as io:
            a.issue_clearance(context,p4,owned,argv,a.sha(virtual/'inert-authority.json'))
            identity=p4.identity
            with monkeypatch.context() as child:
                child.setattr(p4,'identity',lambda pid:identity(2) if pid==os.getpid() else identity(pid))
                a.consume_clearance(context,p4,argv,a.sha(virtual/'inert-authority.json'))
            listener=dict(port=18799,identity=identity(2),role='server',argv=argv)
            a.save_new(folder/'listener.json',listener)
            a.record_native_members(folder,p4,owned,argv,b)
            a.observe_inert_exchange(folder,p4,owned,argv,18799,b)
            a.save_new(folder/'argv-roundtrip.json',dict(question=a.corpus()['query'],argv=argv[4:]))
            for name in ('protected-before.json','protected-after.json'): a.save_new(folder/name,protected)
            for name in ('boundary-before.json','boundary-after.json'): a.save_new(folder/name,dict(pins=admitted['pins'],protected=protected))
            snapshot_live[0]=False
            cleanup=io.cleanup(owned,18799)
        if fault=='protected-empty': (folder/'protected-after.json').write_text('[]')
        elif fault=='native-subset':
            malformed=a.load(folder/'native-members.json'); malformed['snapshot'].pop('1')
            (folder/'native-members.json').write_text(json.dumps(malformed))
        elif fault=='cleanup-subset':
            malformed=a.load(folder/'cleanup.json'); malformed['processes'].pop()
            (folder/'cleanup.json').write_text(json.dumps(malformed))
        elif fault=='missing-exchange': (folder/'inert-exchange.json').unlink()
        elif fault=='no-parent-exchange': del b.inert_exchange
        elif fault=='empty-task-directory': (folder/'outputs/unexpected-task').mkdir(parents=True)
        elif fault in ('wrong-endpoint','wrong-listener','wrong-response','nonboolean-response','late-exchange'):
            malformed=a.load(folder/'inert-exchange.json')
            if fault=='wrong-endpoint': malformed['endpoint']='http://127.0.0.1:11434/inert'
            elif fault=='wrong-listener': malformed['listener']['identity']['pid']=999
            elif fault=='wrong-response': malformed['response']=dict(inert=False)
            elif fault=='nonboolean-response': malformed['response']=dict(inert=1)
            else: malformed['after_ns']=b.cutoff_ns('work')+1
            (folder/'inert-exchange.json').write_text(json.dumps(malformed))
        b.phase='seal'
        terminal=dict(kind='inert',folder=str(folder),run_id=b.run_id,timing=b.timing(),overall='READY_FOR_ROOT_TIMING_WITNESS',cleanup=cleanup,errors=[],first_failure=None)
        a.save_new(folder/'terminal.json',terminal); a.seal_index(folder,b,p4)
        if observer_port is not None:
            if 'remaining' in observer_port:
                clock.value=b.cutoff_ns()-int(observer_port['remaining']*1e9)
            install_delayed_port(p4,clock,observer_port)
            observer_port['saved_bindings']={key:getattr(p4,key) for key in ('socket','time','subprocess','terminate_owned','save')}
        return terminal
    outcome=invocation.call(entry)
    if b.failure: print('CLOSED_WITNESS_FAILURE '+b.failure)
    if observer_port is not None:
        assert all(getattr(p4,key) is value for key,value in observer_port['saved_bindings'].items())
    expected=(fault=='none') if observer_port is None else observer_port['eligible']
    assert outcome['witness']['eligible']==expected,outcome['witness']
    if fault=='none' and expected:
        assert http_calls==[(f'http://127.0.0.1:18799/inert',2)]
        assert outcome['witness']['seal_index_sha256']==a.sha(folder/'seal-index.json')
        assert outcome['witness']['member_hashes'] and outcome['witness']['kind']=='inert'

@pytest.mark.parametrize('fault',['none','protected-empty','native-subset','cleanup-subset','missing-exchange','wrong-endpoint','wrong-listener','wrong-response','nonboolean-response','late-exchange','no-parent-exchange','empty-task-directory'])
def test_fix1_h02_substantive_closed_witness_positive_and_faults(tmp_path,monkeypatch,fault):
    _substantive_closed_witness_fixture(tmp_path,monkeypatch,fault)

@pytest.mark.parametrize('fault',['missing-isolated','port','extra-policy','duplicate','none'])
def test_fix1_h01_actual_child_entry_dispatch_is_canonical_once(tmp_path,monkeypatch,fault):
    import ddgs,httpx,socket
    from src.brain.work_tools import WorkLedger
    from src.brain.work_service import WorkService
    clock=Clock(); b=a.Deadline(clock=clock); p4=a.load_p4(); key=dict(pid=77,created_filetime=123,exe=str(a.PY))
    monkeypatch.setattr(p4,'identity',lambda pid:key)
    context=dict(mode='actual',folder=tmp_path,port=18799,budget=b,request_id='r',session_id='s')
    a.save_new(tmp_path/'attempt.json',dict(parent_timing=b.timing()))
    argv=a.candidate_argv(context)[0]
    root=dict(pid=1,created_filetime=122,exe=str(a.PY))
    a.save_new(tmp_path/'child-clearance.json',dict(mode='actual',folder=str(tmp_path),timing=b.timing(),argv=argv,attempt_sha256=a.sha(tmp_path/'attempt.json'),authority_sha256='authority',launcher_identity=root,base_identity=key,members=[dict(role='server',identity=root,parent=0),dict(role='server',identity=key,parent=1)]))
    a.write_raw_new(tmp_path/'child-clearance.ready',b'')
    supplied=list(argv)
    if fault=='missing-isolated': supplied.remove('--isolated')
    elif fault=='port': supplied[supplied.index('--port')+1]='11434'
    elif fault=='extra-policy': supplied+=['--work-target-policy','unapproved.json']
    elif fault=='duplicate': supplied+=['--child-server',str(tmp_path)]
    calls=[]; old_args=list(sys.argv); old_paths=list(sys.path)
    for obj,name in ((ddgs,'DDGS'),(httpx,'request'),(socket,'getaddrinfo'),(WorkLedger,'__init__'),(WorkLedger,'_freeze_runtime_inputs'),(WorkService,'submit_work')):
        monkeypatch.setattr(obj,name,getattr(obj,name))
    def dispatched(name,**kwargs): calls.append((name,list(sys.argv)))
    if fault=='none':
        a.actual_child_entry(context,p4,supplied,'authority',dispatch=dispatched)
        assert calls==[('src.brain.agent_server',['src.brain.agent_server',*argv[6:]])]
        with pytest.raises(FileExistsError): a.actual_child_entry(context,p4,supplied,'authority',dispatch=dispatched)
        assert len(calls)==1
    else:
        with pytest.raises(ValueError): a.actual_child_entry(context,p4,supplied,'authority',dispatch=dispatched)
        assert not calls and not (tmp_path/'child-clearance.consumed.json').exists()
    assert sys.argv==old_args and sys.path==old_paths

def test_fix2_h01_two_native_base_siblings_refuse_clearance_without_truncation(tmp_path,monkeypatch):
    import base64
    clock=Clock(); b=a.Deadline(clock=clock); p4=a.load_p4(); active={1,2,3}
    native_kernel(monkeypatch,p4,active,clock)
    monkeypatch.setattr(p4,'protected',lambda:[]); monkeypatch.setattr(p4,'process_times',lambda proc:(1000001,0)); monkeypatch.setattr(p4,'argv_parse',json.loads)
    argv=['-B','script']; command=json.dumps([sys.executable,*argv])
    monkeypatch.setattr(p4.subprocess,'check_output',lambda *args,**kwargs:json.dumps([dict(ProcessId=pid,CreationFileTime=p4.identity(pid)['created_filetime'],ParentProcessId=0 if pid==1 else 1,CommandLineBase64=base64.b64encode(command.encode('utf-16-le')).decode()) for pid in (1,2,3)]).encode('ascii'))
    owned=p4.Owned(tmp_path,{})
    owned.launchers=[dict(proc=types.SimpleNamespace(pid=1),identity=p4.identity(1),argv=argv,role='server')]
    owned.known[1]=dict(identity=p4.identity(1),role='server',parent=0,argv=argv)
    a.save_new(tmp_path/'attempt.json',{})
    with a.PrivateIO(p4,b):
        with pytest.raises(ValueError,match='unique native base'): a.issue_clearance(dict(folder=tmp_path,budget=b,mode='inert'),p4,owned,argv,'authority')
    assert set(owned.known)=={1,2,3} and not (tmp_path/'child-clearance.json').exists()

@pytest.mark.parametrize('consumer',['launcher','other','base'])
def test_fix2_h01_only_intended_base_can_consume(tmp_path,monkeypatch,consumer):
    clock=Clock(); b=a.Deadline(clock=clock); p4=a.load_p4()
    root=dict(pid=1,created_filetime=101,exe=str(a.PY)); base=dict(pid=2,created_filetime=102,exe=str(a.PY)); other=dict(pid=3,created_filetime=103,exe=str(a.PY))
    monkeypatch.setattr(p4,'identity',lambda pid:dict(launcher=root,other=other,base=base)[consumer])
    context=dict(mode='inert',folder=tmp_path,port=18799,budget=b); argv=a.inert_argv(tmp_path,18799)
    a.save_new(tmp_path/'attempt.json',{})
    a.save_new(tmp_path/'child-clearance.json',dict(mode='inert',folder=str(tmp_path),timing=b.timing(),argv=argv,authority_sha256='authority',attempt_sha256=a.sha(tmp_path/'attempt.json'),launcher_identity=root,base_identity=base,members=[dict(identity=root,role='server',parent=0),dict(identity=base,role='server',parent=1)]))
    a.write_raw_new(tmp_path/'child-clearance.ready',b'')
    if consumer=='base': assert a.consume_clearance(context,p4,argv,'authority')==base
    else:
        with pytest.raises(ValueError,match='native'): a.consume_clearance(context,p4,argv,'authority')

def test_fix2_n02_actual_post_clearance_setup_cannot_start_product(tmp_path,monkeypatch):
    import ddgs,httpx,socket
    from src.brain.work_tools import WorkLedger
    from src.brain.work_service import WorkService
    clock=Clock(); b=a.Deadline(clock=clock); p4=a.load_p4(); root=dict(pid=1,created_filetime=101,exe=str(a.PY)); base=dict(pid=2,created_filetime=102,exe=str(a.PY))
    monkeypatch.setattr(p4,'identity',lambda pid:base)
    context=dict(mode='actual',folder=tmp_path,port=18799,budget=b,request_id='r',session_id='s'); argv=a.candidate_argv(context)[0]
    a.save_new(tmp_path/'attempt.json',{})
    a.save_new(tmp_path/'child-clearance.json',dict(mode='actual',folder=str(tmp_path),timing=b.timing(),argv=argv,authority_sha256='authority',attempt_sha256=a.sha(tmp_path/'attempt.json'),launcher_identity=root,base_identity=base,members=[dict(identity=root,role='server',parent=0),dict(identity=base,role='server',parent=1)]))
    a.write_raw_new(tmp_path/'child-clearance.ready',b'')
    for obj,name in ((ddgs,'DDGS'),(httpx,'request'),(socket,'getaddrinfo'),(WorkLedger,'__init__'),(WorkLedger,'_freeze_runtime_inputs'),(WorkService,'submit_work')): monkeypatch.setattr(obj,name,getattr(obj,name))
    prepare=a.install_trusted_exports
    def delayed(folder): prepare(folder); clock.value=b.cutoff_ns('work')+1
    monkeypatch.setattr(a,'install_trusted_exports',delayed); called=[]
    with pytest.raises(TimeoutError,match='child product startup'): a.actual_child_entry(context,p4,argv,'authority',dispatch=lambda *args,**kwargs:called.append(True))
    assert not called and (tmp_path/'child-clearance.consumed.json').exists()

@pytest.mark.parametrize('where',['top','wire','transport','event'])
def test_fix2_n01_coherent_unchecked_member_never_raw_export(tmp_path,monkeypatch,sdk_io,mock_jar,where):
    from src.brain.work_navigation import canonical_v3
    from src.brain.work_research import verify_runtime_packet
    from src.brain.tests.test_work_navigation_transport import escaped_scanner_fixture
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    packet=json.loads(ledger._runtime_final); secret=escaped_scanner_fixture()
    target=packet if where=='top' else packet['wires'][-1] if where=='wire' else packet['transport'] if where=='transport' else json.loads(packet['events'][-1])
    target['unchecked_extra']=secret
    if where=='event': packet['events'][-1]=json.dumps(target,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    raw=canonical_v3(packet)
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,raw,require_ack=True,runtime_inputs=ledger._runtime_inputs)
    ledger._runtime_final=raw
    with pytest.raises(ValueError): a.export_completed(tmp_path,ledger,result)
    assert not list(tmp_path.glob('trusted-*.raw'))

def test_fix2_n01_clock_named_unchecked_metadata_has_no_numeric_exemption(tmp_path,monkeypatch,sdk_io,mock_jar):
    from src.brain.work_navigation import canonical_v3
    from src.brain.work_research import verify_runtime_packet
    from src.brain.tests.test_work_navigation_transport import escaped_scanner_fixture
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    packet=json.loads(ledger._runtime_final)
    packet['execution']['files'][0]['result']=json.dumps(dict(timeline=[dict(at=escaped_scanner_fixture())]))
    raw=canonical_v3(packet)
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,raw,require_ack=True,runtime_inputs=ledger._runtime_inputs)
    ledger._runtime_final=raw
    with pytest.raises(ValueError,match='Unsafe export decoded value'): a.export_completed(tmp_path,ledger,result)
    assert not list(tmp_path.glob('trusted-*.raw'))

def test_fix2_h14_first_directory_overrun_stops_iteration_and_further_io(tmp_path,monkeypatch):
    import os
    clock=Clock(); invocation=a.RootInvocation(clock=clock); b=invocation.budget; p4=a.load_p4(); opened=[]; advanced=[]; closed=[]; late_stats=[]; late_hashes=[]
    real_scan=os.scandir; real_stat=os.stat; real_sha=a.sha
    class Iterator:
        def __init__(self,raw): self.raw=raw
        def __iter__(self): return self
        def __next__(self): advanced.append(True); return next(self.raw)
        def close(self): closed.append(True); self.raw.close()
        def __enter__(self): return self
        def __exit__(self,*args): self.close()
    def scan(path):
        opened.append(str(path)); raw=real_scan(path)
        if len(opened)==1: clock.value=b.cutoff_ns('seal')+1
        return Iterator(raw)
    def stat(*args,**kwargs):
        if clock()>b.cutoff_ns('seal'): late_stats.append(args[0])
        return real_stat(*args,**kwargs)
    def hashed(path):
        if clock()>b.cutoff_ns('seal'): late_hashes.append(path)
        return real_sha(path)
    b.phase='seal'; (tmp_path/'later-directory').mkdir(); a.save_new(tmp_path/'later-directory/member.json',{})
    monkeypatch.setattr(os,'scandir',scan); monkeypatch.setattr(os,'stat',stat); monkeypatch.setattr(a,'sha',hashed)
    with pytest.raises(TimeoutError): a.guarded_files(tmp_path,b)
    assert len(opened)==1
    assert not advanced and not late_stats and not late_hashes and closed

@pytest.mark.parametrize('late',[False,True])
def test_fix2_n02_inert_post_clearance_setup_cannot_start_listener(tmp_path,monkeypatch,late):
    clock=Clock(); b=a.Deadline(clock=clock); p4=a.load_p4()
    root=dict(pid=1,created_filetime=101,exe=str(a.PY)); base=dict(pid=2,created_filetime=102,exe=str(a.PY)); monkeypatch.setattr(p4,'identity',lambda pid:base)
    context=dict(mode='inert',folder=tmp_path,port=18799,budget=b); argv=a.inert_argv(tmp_path,18799)
    a.save_new(tmp_path/'attempt.json',{})
    a.save_new(tmp_path/'child-clearance.json',dict(mode='inert',folder=str(tmp_path),timing=b.timing(),argv=argv,authority_sha256='authority',attempt_sha256=a.sha(tmp_path/'attempt.json'),launcher_identity=root,base_identity=base,members=[dict(role='server',identity=root,parent=0),dict(role='server',identity=base,parent=1)]))
    a.write_raw_new(tmp_path/'child-clearance.ready',b'')
    saved=a.save_new
    def delayed(path,value):
        saved(path,value)
        if Path(path).name=='argv-roundtrip.json' and late: clock.value=b.cutoff_ns('work')+1
    monkeypatch.setattr(a,'save_new',delayed); constructed=[]; closed=[]
    class Server:
        def __init__(self,*args): constructed.append(args)
        def handle_request(self): (tmp_path/'stop').touch()
        def server_close(self): closed.append(True)
    if late:
        with pytest.raises(TimeoutError,match='inert child listener startup'): a.inert_child_entry(context,p4,argv,'authority',constructor=Server)
        assert not constructed and not closed and 'inert child listener startup' in b.failure
    else:
        a.inert_child_entry(context,p4,argv,'authority',constructor=Server); assert constructed and closed
    assert (tmp_path/'child-clearance.consumed.json').exists()

def test_fix2_n03_equal_pre_cleanup_inventory_positive(tmp_path):
    p4=a.load_p4(); output=tmp_path/'outputs'; output.mkdir(); (output/'research.md').write_bytes(b'accepted')
    accepted=p4.output_inventory(tmp_path)
    assert a.compare_pre_cleanup(accepted,p4.output_inventory(tmp_path),p4) is None

@pytest.mark.parametrize('variant',['duplicate','entity'])
def test_fix3_f1_exact_coherent_metadata_counter_never_published(tmp_path,monkeypatch,sdk_io,mock_jar,variant):
    from src.brain.work_navigation import canonical_v3
    from src.brain.work_research import verify_runtime_packet
    from src.brain.tests.test_work_navigation_transport import escaped_scanner_fixture
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    sentinel=escaped_scanner_fixture(); assert any(not s.scan(sentinel).clean for s in ledger._policy.scanners)
    packet=json.loads(ledger._runtime_final)
    packet['execution']['files'][0]['result']=('{"slot":'+json.dumps(sentinel)+',"slot":"safe"}' if variant=='duplicate' else json.dumps(dict(nested=dict(entity=sentinel))))
    raw=canonical_v3(packet)
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,raw,require_ack=True,runtime_inputs=ledger._runtime_inputs)
    ledger._runtime_final=raw; published=[]
    monkeypatch.setattr(a,'preserve_completed_members',lambda *args:published.append(args[1]))
    with pytest.raises(ValueError): a.export_completed(tmp_path,ledger,result)
    assert not published and not list(tmp_path.glob('trusted-*.raw'))

def test_fix3_f2_observation_ack_is_genuine_scanned_prose(tmp_path,monkeypatch,sdk_io,mock_jar):
    from dataclasses import asdict
    from src.brain.work_navigation import canonical_v3
    from src.brain.work_research import verify_runtime_packet
    from src.brain.tests.test_work_navigation_transport import rewrite_response
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    answer='Observation: the report is complete.'
    assert all(s.scan(answer).clean for s in ledger._policy.scanners)
    packet=json.loads(ledger._runtime_final); value=dict(final_answer=answer)
    rewrite_response(packet,len(packet['wires'])-1,value,canonical_v3(value).decode())
    raw=canonical_v3(packet)
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,raw,require_ack=True,runtime_inputs=ledger._runtime_inputs)
    ledger._runtime_final=raw; result['content']=answer
    a.save_new(tmp_path/'service-first-result.json',result); a.save_new(tmp_path/'runtime-inputs.json',asdict(ledger._runtime_inputs))
    a.export_completed(tmp_path,ledger,result)
    assert a.verify_exports(tmp_path,result,a.load_p4())['native_POST_attempts']==5

@pytest.mark.parametrize('data_count',[256,257])
def test_fix3_f2_data_member_cap_writer_observer_agree(tmp_path,data_count):
    p4=a.load_p4(); b=a.Deadline(); b.phase='seal'
    for index in range(data_count): (tmp_path/f'data-{index:03}.txt').write_bytes(b'data')
    if data_count==257:
        with pytest.raises(ValueError): a.seal_index(tmp_path,b,p4)
        assert not (tmp_path/'seal-index.json').exists()
    else:
        a.seal_index(tmp_path,b,p4)
        observed=a.guarded_files(tmp_path,b,reserve_index=True)
        assert len(observed)==257 and len(a.load(tmp_path/'seal-index.json')['files'])==256

@pytest.mark.parametrize('raw',['{"x":0,"x":1}','{"outer":[{"x":"first","x":"last"}]}',r'{"a":1,"\u0061":2}'])
def test_fix3_f1_strict_duplicate_decoder_at_each_depth(raw):
    with pytest.raises(ValueError,match='Duplicate export JSON member'): a.strict_json(raw)

def test_fix3_f1_duplicate_actual_timeout_json_boundary_never_published(tmp_path,monkeypatch,sdk_io,mock_jar):
    from src.brain.work_navigation import canonical_v3
    from src.brain.work_research import verify_runtime_packet
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    packet=json.loads(ledger._runtime_final); receipt=packet['transport']['receipts'][-1]
    receipt['timeout_json']='{"connect":123,'+receipt['timeout_json'][1:]
    raw=canonical_v3(packet)
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,raw,require_ack=True,runtime_inputs=ledger._runtime_inputs)
    ledger._runtime_final=raw; published=[]
    monkeypatch.setattr(a,'preserve_completed_members',lambda *args:published.append(args[1]))
    with pytest.raises(ValueError,match='Duplicate export JSON member'): a.export_completed(tmp_path,ledger,result)
    assert not published and not list(tmp_path.glob('trusted-*.raw'))

@pytest.mark.parametrize('lookalike',['nested','suffix','other'])
def test_fix3_f2_index_reservation_never_exempts_other_data(tmp_path,lookalike):
    b=a.Deadline(); b.phase='seal'
    for index in range(256): (tmp_path/f'data-{index:03}.txt').write_bytes(b'data')
    a.save_new(tmp_path/'seal-index.json',{})
    if lookalike=='nested':
        (tmp_path/'nested').mkdir(); a.save_new(tmp_path/'nested/seal-index.json',{})
    elif lookalike=='suffix':
        a.save_new(tmp_path/'seal-index.json.extra',{})
    else: a.save_new(tmp_path/'other-index.json',{})
    with pytest.raises(ValueError,match='data member cap'): a.guarded_files(tmp_path,b,reserve_index=True)

@pytest.mark.parametrize('effect',['absent','empty-root','empty-task','file'])
def test_fix3_f2_inert_no_descendants_includes_empty_directories(tmp_path,effect):
    root=tmp_path/'outputs'; b=a.Deadline(); b.phase='seal'
    if effect!='absent': root.mkdir()
    if effect=='empty-task': (root/'unexpected-task').mkdir()
    elif effect=='file': (root/'unexpected.md').write_bytes(b'effect')
    assert a.no_output_descendants(root,b)==(effect in ('absent','empty-root'))

@pytest.mark.parametrize('variant',['digits','nested-digits','integer','bool','null','list','peer','latency','tag-family'])
def test_fix4_f1_producer_types_before_publication(tmp_path,monkeypatch,sdk_io,mock_jar,variant):
    import hashlib
    from src.brain.work_navigation import canonical_v3
    from src.brain.work_research import verify_runtime_packet
    from src.brain.tests.test_work_navigation_transport import escaped_scanner_fixture
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    sentinel=escaped_scanner_fixture()
    assert str(int(sentinel))==sentinel and any(not s.scan(sentinel).clean for s in ledger._policy.scanners)
    packet=json.loads(ledger._runtime_final)
    file=packet['execution']['files'][0]
    assert type(file['result']) is str
    if variant=='peer':
        packet['transport']['receipts'][-1]['peer_bytes']=int(sentinel)
    elif variant=='latency':
        event=json.loads(packet['events'][-1]); event['data']['latency']={'unissued':int(sentinel)}
        packet['events'][-1]=json.dumps(event,sort_keys=True,ensure_ascii=False,separators=(',',':'),allow_nan=False)
    elif variant=='tag-family':
        identity=packet['wires'][-1]['identity']
        tags=json.loads(identity['tags_response']); tags['models'][0]['details']['family']=int(sentinel)
        body=canonical_v3(tags); identity['tags_response']=body.decode()
        receipt=packet['transport']['receipts'][-2]
        delta=len(body)-receipt['admitted']
        for key in ('downloaded','inspected','retained','admitted'): receipt[key]+=delta
        packet['transport']['admitted']['metadata']+=delta
        receipt['response_sha256']=hashlib.sha256(body).hexdigest()
    else:
        file['result']={'digits':int(sentinel),'nested-digits':{'unissued':int(sentinel)},
                        'integer':7,'bool':True,'null':None,'list':[]}[variant]
    raw=canonical_v3(packet)
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,raw,require_ack=True,runtime_inputs=ledger._runtime_inputs)
    ledger._runtime_final=raw; published=[]
    monkeypatch.setattr(a,'preserve_completed_members',lambda *args:published.append(True))
    with pytest.raises(ValueError,match='Producer'): a.export_completed(tmp_path,ledger,result)
    assert not published and not list(tmp_path.glob('trusted-*.raw'))

@pytest.mark.parametrize('nested',[False,True])
def test_fix4_f1_archived_reviewer_packet(tmp_path,monkeypatch,nested):
    from src.brain.work_tools import WorkBinding,ResearchRuntimeInputs
    from src.brain.work_navigation import IssuedSnapshotV3,canonical_v3
    from src.brain.work_research import ResearchCollection,verify_runtime_packet
    from src.brain.tests.test_work_navigation_transport import escaped_scanner_fixture
    from openjarvis.security.scanner import SecretScanner,PIIScanner
    archive=Path('H:\\UltimaAI\\UltimaAgent\\data\\evidence\\jarvis-work-capability\\T2\\navigation-source10-validation-20261102\\code\\harness-preparation-20261102T215807022506Z\\temp\\test_fix1_genuine_synthetic_ex0')
    exported=a.load(archive/'trusted-export.json'); blobs=a.read_completed(archive,exported)
    snapshot=exported['issued_snapshot']; snapshot['binding_key']=tuple(snapshot['binding_key'])
    snapshot=IssuedSnapshotV3(**snapshot,views_json=blobs['views'],replay_json=blobs['replay'])
    inputs=a.load(archive/'runtime-inputs.json'); inputs['binding_key']=tuple(inputs['binding_key'])
    binding=WorkBinding(Path(inputs['root']),*inputs['binding_key'])
    ledger=types.SimpleNamespace(_binding=binding,issued_snapshot=snapshot,_runtime_inputs=ResearchRuntimeInputs(**inputs),
        _collection=ResearchCollection(**a.strict_json(blobs['collection'])),_policy=types.SimpleNamespace(scanners=(SecretScanner(),PIIScanner())))
    published=[]
    monkeypatch.setattr(a,'preserve_completed_members',lambda *args:published.append(True))
    ledger._runtime_final=blobs['runtime']
    # work_research source hash is part of the scanner policy. This preserved
    # old packet must not earn current-candidate credit after a product fix.
    with pytest.raises(ValueError,match='Runtime scanner policy drift'):
        a.export_completed(tmp_path,ledger,{})
    assert not published
    packet=a.strict_json(blobs['runtime']); value=int(escaped_scanner_fixture())
    packet['execution']['files'][0]['result']={'unissued':value} if nested else value
    ledger._runtime_final=canonical_v3(packet)
    with pytest.raises(ValueError,match='Runtime scanner policy drift'):
        verify_runtime_packet(binding,snapshot,ledger._collection,ledger._runtime_final,require_ack=True,runtime_inputs=ledger._runtime_inputs)
    with pytest.raises(ValueError,match='Runtime scanner policy drift'):
        a.export_completed(tmp_path,ledger,{})
    assert not published and not list(tmp_path.glob('trusted-*.raw'))


@pytest.mark.parametrize('nested',[False,True])
def test_recovery_current_candidate_packet(tmp_path,monkeypatch,sdk_io,mock_jar,nested):
    from src.brain.work_navigation import canonical_v3
    from src.brain.work_research import verify_runtime_packet
    from src.brain.tests.test_work_navigation_transport import escaped_scanner_fixture
    result,ledger=synthetic_bundle(tmp_path,sdk_io,mock_jar,monkeypatch,write=False)
    published=[]
    monkeypatch.setattr(a,'preserve_completed_members',lambda *args:published.append(True))
    a.export_completed(tmp_path,ledger,result)
    assert published==[True]
    published.clear()
    packet=a.strict_json(ledger._runtime_final);value=int(escaped_scanner_fixture())
    packet['execution']['files'][0]['result']={'unissued':value} if nested else value
    ledger._runtime_final=canonical_v3(packet)
    verify_runtime_packet(ledger._binding,ledger.issued_snapshot,ledger._collection,ledger._runtime_final,require_ack=True,runtime_inputs=ledger._runtime_inputs)
    with pytest.raises(ValueError,match='Producer'):a.export_completed(tmp_path,ledger,result)
    assert not published and not list(tmp_path.glob('trusted-*.raw'))


# Port revision: an actual wait-dependent refusal, never a constant-success socket.
PORT_REFUSAL_DELAY = 2.0139454

def install_delayed_port(p4,clock,scenario):
    probes=scenario.setdefault('probes',[])
    class DelayedProbe:
        def __init__(self):
            self.timeouts=[]; self.connects=[]; self.closed=False; self.close_count=0
            probes.append(self); clock.advance(scenario.get('setup',0))
        def settimeout(self,value): self.timeout=value; self.timeouts.append(value)
        def connect_ex(self,address):
            self.connects.append(dict(address=address,timeout=self.timeout,start=clock()))
            wait=min(self.timeout,PORT_REFUSAL_DELAY); clock.advance(wait)
            clock.advance(scenario.get('overrun',0))
            if scenario.get('error'): raise OSError('mocked port error')
            return scenario.get('code',10061 if wait>=PORT_REFUSAL_DELAY else 10035)
        def close(self): self.closed=True; self.close_count+=1
    p4.socket=types.SimpleNamespace(socket=DelayedProbe)
    return probes

@pytest.mark.parametrize('mode',['inert','actual'])
@pytest.mark.parametrize('scenario',[
    dict(name='sufficient',remaining=10,setup=0,eligible=True,effective=3),
    dict(name='clipped-sufficient',remaining=2.5,setup=0,eligible=True,effective=2.5),
    dict(name='clipped-unknown',remaining=2,setup=0,eligible=False,effective=2),
    dict(name='exact-cutoff',remaining=PORT_REFUSAL_DELAY,eligible=False,closed=True,effective=PORT_REFUSAL_DELAY),
    dict(name='setup-sufficient',remaining=10,setup=.8,eligible=True,effective=2.2),
    dict(name='setup-unknown',remaining=10,setup=1.1,eligible=False,effective=1.9),
    dict(name='zero-before-connect',remaining=10,setup=3,eligible=False,effective=None),
    dict(name='phase-expired-before-hint',remaining=2,setup=2,eligible=False,effective=None),
    dict(name='10035',remaining=10,code=10035,eligible=False,effective=3),
    dict(name='10060',remaining=10,code=10060,eligible=False,effective=3),
    dict(name='open',remaining=10,code=0,eligible=False,effective=3),
    dict(name='other',remaining=10,code=12345,eligible=False,effective=3),
    dict(name='missing',remaining=10,code=None,eligible=False,effective=3),
    dict(name='error',remaining=10,error=True,eligible=False,effective=3),
    dict(name='late-phase',remaining=2.5,overrun=1,eligible=False,effective=2.5),
    dict(name='late-private-cap',remaining=10,overrun=1.1,eligible=False,effective=3),
],ids=lambda v:v['name'])
def test_port_rev2_real_cleanup_delayed_refusal(tmp_path,monkeypatch,mode,scenario):
    scenario=dict(scenario); clock=Clock(); b=a.Deadline(clock=clock); b.phase='cleanup'
    b.admitted=dict(mode=mode); p4=a.load_p4(); active=set()
    native_kernel(monkeypatch,p4,active,clock)
    p4.protected=lambda:[]
    p4.subprocess=types.SimpleNamespace(check_output=lambda *args,**kwargs:b'[]',CREATE_NO_WINDOW=0)
    probes=install_delayed_port(p4,clock,scenario)
    saved={key:getattr(p4,key) for key in ('socket','time','subprocess','terminate_owned','save')}
    owned=p4.Owned(tmp_path,{})
    owned.known[1]=dict(identity=p4.identity(1),role='server',argv=[],parent=0)
    clock.value=b.cutoff_ns()-int(scenario['remaining']*1e9)
    with a.PrivateIO(p4,b) as io:
        result=io.cleanup(owned,18799)
        assert (result['status']=='PASS') is scenario['eligible'],result
        assert io.port_closed is scenario.get('closed',scenario['eligible'])
        if scenario.get('code',10035) in (10035,10060,12345,None) and not scenario.get('error') and not scenario.get('overrun') and scenario['effective'] is not None and b.remaining_ns()>0:
            # Original P4's any-nonzero verdict is insufficient for strict eligibility.
            original=a.load(tmp_path/'cleanup.json')
            assert original['status']=='PASS' and original['port_closed'] is True
        if b.remaining_ns()<=0:
            assert not (tmp_path/'cleanup.json').exists()
            assert b.failure # completed proof cannot admit a following save
    assert all(getattr(p4,key) is value for key,value in saved.items())
    assert len(probes)==1 and probes[0].closed
    connects=probes[0].connects
    assert len(connects)==(scenario['effective'] is not None)
    assert probes[0].close_count==1
    if not connects:
        assert probes[0].timeouts==[] # expired construction admits no raw hint
    if connects:
        assert connects[0]['timeout']==pytest.approx(scenario['effective'])
        assert probes[0].timeouts[0]==1 # immutable original P4 hint

@pytest.mark.parametrize('scenario',[
    dict(name='sufficient',eligible=True,effective=3),
    dict(name='clipped-sufficient',remaining=2.5,eligible=True,effective=2.5),
    dict(name='clipped-unknown',remaining=2,eligible=False,effective=2),
    dict(name='exact-cutoff',remaining=PORT_REFUSAL_DELAY,eligible=False,effective=PORT_REFUSAL_DELAY),
    dict(name='zero-before-connect',setup=3,eligible=False,effective=None),
    dict(name='phase-expired-before-hint',remaining=2,setup=2,eligible=False,effective=None),
    dict(name='late-phase',remaining=2.5,overrun=1,eligible=False,effective=2.5),
    dict(name='setup-sufficient',setup=.8,eligible=True,effective=2.2),
    dict(name='setup-unknown',setup=1.1,eligible=False,effective=1.9),
    dict(name='10035',code=10035,eligible=False,effective=3),
    dict(name='10060',code=10060,eligible=False,effective=3),
    dict(name='open',code=0,eligible=False,effective=3),
    dict(name='error',error=True,eligible=False,effective=3),
    dict(name='late-private-cap',overrun=1.1,eligible=False,effective=3),
],ids=lambda v:v['name'])
def test_port_rev2_real_substantive_observer_delayed_refusal(tmp_path,monkeypatch,scenario):
    scenario=dict(scenario)
    _substantive_closed_witness_fixture(tmp_path,monkeypatch,'none',observer_port=scenario)
    probe,=scenario['probes']
    assert probe.closed and len(probe.connects)==(scenario['effective'] is not None)
    assert probe.close_count==1
    if not probe.connects:
        assert probe.timeouts==[] # mandatory scope close despite hint-before-try
    if probe.connects:
        assert probe.connects[0]['timeout']==pytest.approx(scenario['effective'])


def child_admission_fixture(tmp_path,monkeypatch,child):
    """Real admit/native validation; replace only OS observations and package setup."""
    p4=a.load_p4(); budget=a.Deadline()
    identities=[dict(pid=100+i,created_filetime=100000+i,exe=str(a.PY)) for i in range(7)]
    rows=protected_fixture(tmp_path,monkeypatch,p4,identities)
    parent=dict(pid=9000,created_filetime=90000,exe=str(a.PY))
    native={key['pid']:dict(key) for key in identities}; native[parent['pid']]=parent
    monkeypatch.setattr(p4,'identity',lambda pid:native[pid])
    queries=[]
    def snapshot(pids=None):
        queries.append(pids)
        # The former child path invokes this boundary and would create an
        # unregistered PowerShell descendant before clearance. Never launch it.
        if child: raise AssertionError('child admission attempted a subprocess-backed process snapshot')
        return rows
    monkeypatch.setattr(p4,'process_snapshot',snapshot)
    monkeypatch.setattr(p4,'listener_owner',lambda port:[])
    monkeypatch.setattr(a,'load_p4',lambda:p4)
    (tmp_path/'inputs').mkdir()
    (tmp_path/'inputs/scope.json').write_bytes((a.V/'inputs/scope.json').read_bytes())
    monkeypatch.setattr(a,'V',tmp_path)
    # Source/package/metadata checks have independent retained coverage; keep
    # the complete authority, hash, age, native and parent binding path real.
    monkeypatch.setattr(a,'package_check',lambda p4:None)
    monkeypatch.setattr(a,'check_import_origins',lambda:None)
    monkeypatch.setattr(a,'operational_pins',lambda mode,budget:{'offline-package':'bound'})
    authority,ledger,now=documents()
    authority['parent_timing']=dict(origin_ns=budget.origin_ns,run_id=budget.run_id,
        clock_domain=a.CLOCK_DOMAIN,parent_identity=parent)
    folder=tmp_path/'actual/E02-controlled-1'
    if child:
        folder.mkdir(parents=True); a.save_new(folder/'attempt.json',dict(case='E02-controlled-1'))
    (tmp_path/'controller-authority').mkdir(); (tmp_path/'native-preflight').mkdir()
    ledger_path=tmp_path/'controller-ledger.json'; a.save_new(ledger_path,ledger)
    a.save_new(tmp_path/'harness-approval.json',dict(fixture='already independently covered'))
    proof=a.load(a.T/'e02-source13-real-controlled-preparation-20261107-r1/native-preflight/E02-controlled-1.json')
    proof.update(recorded_at=now.isoformat(),protected=identities,candidate=a.CANDIDATE)
    proof_path=tmp_path/'native-preflight/E02-controlled-1.json'; a.save_new(proof_path,proof)
    authority.update(ledger_sha256=a.sha(ledger_path),approval_sha256=a.sha(tmp_path/'harness-approval.json'),
        native_preflight_sha256=a.sha(proof_path),folder=str(folder),port=18799)
    authority_path=tmp_path/'controller-authority/E02-controlled-1.json';a.save_new(authority_path,authority)
    return dict(p4=p4,budget=budget,authority=authority,authority_path=authority_path,ledger_path=ledger_path,
        proof=proof,proof_path=proof_path,native=native,identities=identities,rows=rows,queries=queries,folder=folder)


@pytest.mark.parametrize('child',[True,False],ids=['child-no-subprocess','parent-full-snapshot'])
def test_recovery_full_admit_observation_role(tmp_path,monkeypatch,child):
    f=child_admission_fixture(tmp_path,monkeypatch,child)
    context,p4=a.admit(f['authority_path'],f['ledger_path'],child=child,budget=f['budget'])
    assert context['folder']==f['folder'] and context['mode']=='actual'
    assert context['baseline']['protected']==f['identities']
    assert context['budget'].origin_ns==f['authority']['parent_timing']['origin_ns']
    assert f['queries']==([] if child else [[100,101,102,103,104,105,106]])
    assert not (f['folder']/'child-clearance.consumed.json').exists()


@pytest.mark.parametrize('child',[True,False])
@pytest.mark.parametrize('fault',['expired','precision','missing-listener','changed-native','wrong-parent','changed-proof-hash'])
def test_recovery_full_admit_rejects_drift_before_dispatch(tmp_path,monkeypatch,child,fault):
    f=child_admission_fixture(tmp_path,monkeypatch,child)
    if fault=='expired': f['proof']['recorded_at']=(dt.datetime.now(dt.timezone.utc)-dt.timedelta(seconds=61)).isoformat()
    elif fault=='precision': f['proof']['precision']='milliseconds'
    elif fault=='missing-listener': f['proof']['protected']=f['identities'][:-1]
    elif fault=='changed-native': f['native'][106]['created_filetime']+=1
    elif fault=='wrong-parent': f['native'][9000]=dict(f['native'][9000],created_filetime=1)
    elif fault=='changed-proof-hash': f['proof']['unexpected']='not bound'
    # Only these synthetic fixture files are rewritten; the real admission
    # validator must reject the faulty proof or live native observation.
    f['proof_path'].write_text(json.dumps(f['proof']),encoding='utf8')
    if fault!='changed-proof-hash':
        f['authority']['native_preflight_sha256']=a.sha(f['proof_path'])
        f['authority_path'].write_text(json.dumps(f['authority']),encoding='utf8')
    with pytest.raises(ValueError):
        a.admit(f['authority_path'],f['ledger_path'],child=child,budget=f['budget'])
    assert not (f['folder']/'child-clearance.consumed.json').exists()
    assert not (f['folder']/'product-result.json').exists()


@pytest.mark.parametrize('fault',['parent','command','cim-created'])
def test_recovery_parent_still_rejects_full_protected_snapshot_drift(tmp_path,monkeypatch,fault):
    f=child_admission_fixture(tmp_path,monkeypatch,False)
    if fault=='parent': f['rows'][106]['ParentProcessId']+=1
    elif fault=='command': f['rows'][106]['CommandLine']='unbound command'
    else: f['rows'][106]['CreationFileTime']+=1000
    with pytest.raises(ValueError):
        a.admit(f['authority_path'],f['ledger_path'],budget=f['budget'])
    assert len(f['queries'])==1
    assert not f['folder'].exists()


@pytest.mark.parametrize('case',['six_reads','ack_after_write'])
def test_export_diagnostics_current_native_refusal(tmp_path,monkeypatch,sdk_io,mock_jar,case):
    from src.brain.tests.test_work_native_response_diagnostics import native_refusal
    observe_failure_exports(tmp_path,monkeypatch)
    ack=case=='ack_after_write'
    result,ledger,sent,responses=native_refusal(tmp_path/'outputs',sdk_io,mock_jar,monkeypatch,reads=6,ack=ack)
    raw=(tmp_path/'trusted-failure-diagnostic.raw').read_bytes();packet=json.loads(raw)
    receipt=a.load(tmp_path/'trusted-failure-diagnostic.export.json')
    assert raw==ledger._failure_diagnostic and len(raw)<=16384
    assert packet['kind']=='research_failure_diagnostic_v4'
    assert result['research_diagnostic']['kind']==packet['kind']
    assert receipt['sha256']==result['research_diagnostic']['sha256']==a.hashlib.sha256(raw).hexdigest()
    assert receipt['status']=='SAVED' and receipt['bytes']==len(raw)
    assert receipt['complete'] is False and receipt['END'] is False and receipt['acceptance_credit']==0
    assert a.load(tmp_path/'service-first-result.json')==result
    assert result['error']=='Invalid native research response' and not result['artifacts']
    assert not (tmp_path/'trusted-runtime.raw').exists() and not getattr(ledger,'_runtime_final',None)
    exported=a.load(tmp_path/'trusted-export.json')
    assert exported['complete'] is False and exported['END'] is False
    native=packet['native_response'];last=packet['last_http'];generation=5 if ack else 7
    assert native['reason']=='done_reason' and native['done_reason']=='length'
    assert native['max_tokens']==(256 if ack else 2048)
    assert native['generation']==last['generation']==generation==len(sent)
    assert native['receipt_index']==last['receipt_index']==3*generation-1
    assert native['request_sha256']==last['request_sha256']==a.hashlib.sha256(sent[-1]).hexdigest()
    assert native['response_sha256']==a.hashlib.sha256(responses[-1]).hexdigest()
    assert native['response_bytes']==last['admitted']==len(responses[-1])
    assert last['status']==200 and last['send_reserved'] and not last['validated_response'] and not last['transport_failed']
    assert packet['eligible_source_ids']==['S1','S2','S3']
    assert packet['complete'] is False and packet['acceptance_credit']==0 and not packet['ack_confirmed']
    assert exported['native_POST_attempts']==packet['budget']['native_posts']==generation
    files=list((tmp_path/'outputs').rglob('research.md'))
    if ack:
        assert result['status']=='needs_attention' and packet['branch']=='write_without_ack' and packet['write_confirmed']
        assert packet['budget']['reads_used']==3 and len(files)==1 and files[0].read_bytes()
        assert len(result['research_effects'])==1 and result['research_effects'][0]['state']=='completed'
        assert Path(result['research_effects'][0]['path']).resolve()==files[0].resolve()
    else:
        assert result['status']=='failed' and result['content']=='本次研究未交付。'
        assert packet['branch']=='unvalidated_response' and not packet['write_confirmed']
        assert packet['budget']['reads_used']==6 and len(packet['pages'])==6
        assert sum(page['confirmed'] for page in packet['pages'])==6
        assert sum(page['visible'] for page in packet['pages'])==5
        assert not files and not result.get('research_effects')
