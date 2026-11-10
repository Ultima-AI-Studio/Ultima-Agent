"""Offline selected-path contracts. Synthetic doubles never qualify a runtime."""
import copy
import importlib.util
import json
from pathlib import Path
from types import SimpleNamespace
import pytest

HERE = Path(__file__).resolve().parent

CURRENT_SOURCE13 = '269aca511d88412dbb9c15d23911138469a37aa2'


def binding_adapter():
    spec = importlib.util.spec_from_file_location('source13_profile_adapter', HERE.parent / 'profile-adapter.py')
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.parametrize('candidate,accepted', [(CURRENT_SOURCE13, True), ('118ba152b007c30d358c8bc44c51aabe8ae820f0', False)], ids=['current', 'old'])
def test_source13_admission_candidate(candidate, accepted, tmp_path):
    p = implementation()
    pins = {key: 'a' * 64 for key in ('profile_manifest_sha256', 'candidate_manifest_sha256', 'corpus_sha256')}
    grant = admission_double(p, tmp_path, pins)
    grant['candidate'] = candidate
    if accepted:
        p.validate_admission(grant, tmp_path, pins)
    else:
        with pytest.raises(ValueError):
            p.validate_admission(grant, tmp_path, pins)


def test_source13_adapter_bound_candidate():
    adapter = binding_adapter()
    assert adapter.CANDIDATE == CURRENT_SOURCE13
    assert adapter.C == Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent')


@pytest.mark.parametrize('name', ['main', 'run_case', 'RootInvocation', 'actual_child_entry', 'inert_child_entry'])
def test_source13_adapter_has_no_legacy_entry(name):
    assert not hasattr(binding_adapter(), name)


def test_source13_adapter_current_inventory():
    adapter = binding_adapter()
    files = adapter.check_inputs()
    current = json.loads((HERE.parent / 'inputs/candidate-runtime-manifest.json').read_bytes())
    assert len(current['source_files']) == 57
    assert all(files[name] == digest for name, digest in current['source_files'].items())
    for component in current['sdk_components'].values():
        assert all(files[str(Path(component['root']) / name)] == digest for name, digest in component['files'].items())


@pytest.mark.parametrize('bad', ['hash', 'candidate', 'model', 'source', 'sdk'])
def test_source13_adapter_rejects_bad_runtime_manifest(bad, tmp_path, monkeypatch):
    import hashlib
    adapter = binding_adapter()
    current = json.loads((HERE.parent / 'inputs/candidate-runtime-manifest.json').read_bytes())
    if bad == 'candidate': current['candidate'] = '118ba152b007c30d358c8bc44c51aabe8ae820f0'
    if bad == 'model': current['model']['digest'] = 'b' * 64
    if bad == 'source': current['source_files'][next(iter(current['source_files']))] = 'b' * 64
    if bad == 'sdk':
        files = next(iter(current['sdk_components'].values()))['files']
        files[next(iter(files))] = 'b' * 64
    path = tmp_path / 'runtime.json'
    path.write_text(json.dumps(current), encoding='utf-8')
    monkeypatch.setattr(adapter, 'RUNTIME_MANIFEST', path)
    if bad != 'hash': monkeypatch.setattr(adapter, 'EXPECTED_MANIFEST_SHA', hashlib.sha256(path.read_bytes()).hexdigest())
    with pytest.raises(ValueError): adapter.check_inputs()


def test_source13_adapter_original_corpus():
    data = binding_adapter().corpus()
    assert len(data['query'].encode('utf-8')) == 774
    assert [len(row['body'].encode('utf-8')) for row in data['sources']] == [7236, 3252, 4643, 13559]


def test_source13_rootcontrols_remain_unconfigured(tmp_path):
    controls = implementation().RootControls()
    with pytest.raises(ValueError): controls.admit(tmp_path, {})
    with pytest.raises(ValueError): controls.readback(tmp_path, {})


def test_source13_adapter_sdk_import_origins():
    binding_adapter().check_import_origins()

def implementation():
    spec = importlib.util.spec_from_file_location('original_profile', HERE / 'profile.py')
    assert spec is not None and spec.loader is not None
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def ssrf_receipt_fixture(context,urls=None):
    import hashlib
    if urls is None:
        urls=[s['final_url'] for s in json.loads((HERE.parent.parent/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_bytes())['sources']]
    def row(phase,index=None):
        return dict(phase=phase,source_index=index,source_url_sha256=hashlib.sha256(urls[index-1].encode()).hexdigest() if index is not None else None,
            backend='python',baseline_passed=True,checker_entered=int(index is not None),returned_none=int(index is not None),
            returned_rejected=0,checker_raised=0,python_resolver_entries=int(index is not None),refused=0)
    indexes=[1,2,3,4,*[i for i in range(1,5) for _ in range(3)]] if context=='worker' else [1,2,3,4]
    return dict(context=context,records=[row('entry'),*[row('lookup',i) for i in indexes],row('close'),row('restored')],
        native_dns=None,native_cache=None,packets=None)


def good_counter_fixture():
    return dict(bootstrap=1,research_reserved=10,metadata_refused=0,owner_constructors=1,research_constructors=1,
        owner_client_count=1,research_client_count=1,distinct_clients=True,clients_closed=True,eager_clean=True,
        audit_clean=True,scope_clean=True,browser_refused=0,fixture_searches=1,fixture_GETs=4,sdk_searches=1,sdk_GETs=4,
        native_metadata=10,native_posts=5,native_completed=5,native_refused=0,sdk_inference_start=5,sdk_inference_end=5,
        owner_refused=0,research_refused=0,writer_constructor_matches=1,writer_attempts=1,writer_successes=1,
        observer_incomplete=False,ssrf=ssrf_receipt_fixture('worker'),ordinary_http=None,os_packets=None,native_activity=None)


def linked_writer_rows_fixture(reads):
    import uuid
    report,dispatch,file_id=[str(uuid.uuid4()) for _ in range(3)]
    ids=dict(report_call_id=report,dispatch_uuid=dispatch,file_call_id=file_id,seq=4,generation=4)
    def nav(seq,role,end=False):
        value=dict(kind='NAVIGATION',event='tool_call_end' if end else 'tool_call_start',tool_role=role,
            observed=True,returned=True,retained=True,sealed=False,caller_match=True,binding_match=True,
            permit=end,claimed=True if end else None,staged=end,confirmed=False if end else None,confirmed_after=True if end else None,
            success=True if end else None,result_match=True if end else None,metadata_match=True if end else None,
            sequence_match=True if end else None,tool_match=True,agent_match=True,arguments_match=True if end else None,
            report_call_id=None,dispatch_uuid=str(uuid.uuid4()) if end else None,file_call_id=None,seq=seq,generation=seq)
        if end and role=='writer': value.update(ids)
        elif end: value['dispatch_uuid']=reads[seq-1]['key']['dispatch_uuid']
        return value
    values=[row for seq in range(1,4) for row in (nav(seq,'inspect'),nav(seq,'inspect',True))]
    values += [nav(4,'writer'),dict(kind='SDK_ATTEMPT',**ids),dict(kind='SDK_RETURN_TRUE',success=True),nav(4,'writer',True),
        dict(kind='ACK_PHASE',file_verified=True,**dict(ids,generation=5)),
        dict(kind='ACK_SEND',admitted=True,**dict(ids,generation=5)),
        dict(kind='ACK_SECURED',verified=True,**dict(ids,generation=5))]
    return [dict(order=index,at_ns=index,**value) for index,value in enumerate(values,1)]

# These fixtures are producer-shaped synthetic values derived from C118 source,
# never archived responses, old issued references, or original-corpus contents.
def action_schema(*names):
    return {'anyOf': [{'type': 'object', 'properties': {'action': {'enum': [n]},
            'action_input': {'type': 'object'}}} for n in names] + [
            {'type': 'object', 'properties': {'final_answer': {'type': 'string'}}}]}

def entity(pages=(), *, write=False, final=False):
    catalogue = [dict(source_id='S'+str(i), identity='example.invalid/source'+str(i),
        suffix='.md', total_lines=60, available=True, reason='', landmarks=[[1, 1], [25, 25]])
        for i in range(1, 4)]
    messages = [dict(role='system',content='Synthetic approved system'),
        dict(role='user',content='Synthetic query\nSafe source catalogue (untrusted data):\n'+json.dumps(catalogue))]
    for p in pages:
        choice={'action':'ultima_work_research_inspect','action_input':{'source_id':p['source_id'],'start_line':p['start']}}
        messages += [dict(role='assistant',content=json.dumps(choice)),
                     dict(role='user',content='Observation: '+json.dumps(p))]
    schema = {'type':'object','properties':{'final_answer':{'type':'string'}}} if final else action_schema(
        'ultima_work_research_inspect', *(['ultima_work_research_write'] if write else []))
    return dict(model='qwen3-8b-uncensored',messages=messages,format=schema,tools=[],think=False,stream=False,
        options=dict(num_ctx=16384,temperature=0,num_predict=256 if final or not write else 2048))

def page(i, *, cards=True, reference=None):
    return dict(v=3,source_id='S'+str(i),view_id=str(i)*64,start=1,end=24,total_lines=60,
        lines=[[1, 'The scheduler accepts one request.']],
        cards=[[reference or ('N3.'+str(i)*16),'documented','',1,1,1,1]] if cards else [],
        omissions=[],omitted_cards=0,next_start=25)


def claimed_writer_identity(ledger,nested):
    import uuid
    report,dispatch,file_id=[str(uuid.uuid4()) for _ in range(3)]
    nested._report_parent=(report,dispatch); nested._report_file_id=file_id
    ledger._sequence=1; ledger._generation=1; ledger._reserved_report=report
    ledger._permit=dict(seq=1,generation=1,name='ultima_work_research_write',claimed=True,
        report_call_id=report,dispatch_uuid=dispatch,file_call_id=file_id)


def preflight_origin_double():
    from types import ModuleType
    source='''def collect_research():
    def invoke(executor,tool_call,binding,ledger,deadline):
        bus=executor._bus
        sdk_id=tool_call.id
        return executor.execute(tool_call)
    return invoke
'''
    path='C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/work_research.py'
    module=ModuleType('src.brain.work_research'); module.__file__=path
    exec(compile(source,path,'exec'),module.__dict__)
    return module,module.collect_research()


def runtime_mark_server_double():
    class Leaf:
        def generate(self):
            expected={'ack':True}
            return self.ledger._mark('generation',generation=5)
    class Transport:
        def exchange(self):
            ack=True; method='POST'; path='/api/chat'
            return self.ledger._mark('send',generation=5,receipt_index=0)
    class View:
        def generate(self):
            ack=True
            return self.ledger._mark('secured',generation=5)
    return SimpleNamespace(_NativeResearchLeaf=Leaf,_ResearchTransport=Transport,_ResearchEngineView=View)

def test_visible_choices():
    p = implementation()
    assert hasattr(p, 'next_reply'), 'T3 next_reply missing'
    seen = {'binding_key': ['request','session','task'], 'nonce':'a'*32}
    first = p.next_reply(entity(), seen)
    assert first == {'action':'ultima_work_research_inspect','action_input':{'source_id':'S1','start_line':1}}
    second = p.next_reply(entity([page(1)]), seen)
    assert second['action_input'] == {'source_id':'S2','start_line':1}
    value = p.next_reply(entity([page(1),page(2),page(3)],write=True), seen)
    assert value['action'] == 'ultima_work_research_write'
    assert value['action_input']['path'] == 'research.md'
    assert [s['source_id'] for s in value['action_input']['sections']] == ['S1','S2','S3']
    assert [s['facts'][0]['evidence_id'] for s in value['action_input']['sections']] == ['N3.'+str(i)*16 for i in range(1,4)]
    assert all(s['facts'][0]['claim'] == 'The scheduler accepts one request.' for s in value['action_input']['sections'])

@pytest.mark.parametrize('bad', ['duplicate', 'foreign', 'unseen_line', 'final_without_writer', 'no_cards_exhausted'])
def test_visible_choices_refuse(bad):
    p = implementation()
    assert hasattr(p, 'next_reply'), 'T3 next_reply missing'
    seen = {'binding_key':['request','session','task'],'nonce':'a'*32}
    pages = [page(1),page(2),page(3)]
    value = entity(pages,write=True)
    if bad == 'duplicate': value=entity([page(1),page(2,reference='N3.'+'1'*16),page(3)],write=True)
    if bad == 'foreign': pages[0]['source_id']='S5'; value=entity(pages,write=True)
    if bad == 'unseen_line': pages[0]['cards'][0][3:]=[2,2,2,2]; value=entity(pages,write=True)
    if bad == 'final_without_writer': value=entity(final=True)
    if bad == 'no_cards_exhausted':
        pages=[]
        for i in range(1,4):
            for start in (1,25):
                item=page(i,cards=False); item['start']=start; item['end']=start+23; item['next_start']=None; pages.append(item)
        value=entity(pages)
    with pytest.raises(ValueError): p.next_reply(value,seen)

def test_native_boundaries():
    p=implementation()
    assert hasattr(p,'MetadataBudget'), 'T3 shared MetadataBudget missing'
    budget=p.MetadataBudget()
    budget.reserve('owner','GET','/api/tags')
    for _ in range(7):
        budget.reserve('research','GET','/api/version'); budget.reserve('research','GET','/api/tags')
    budget.reserve('research','GET','/api/version')
    with pytest.raises(ValueError): budget.reserve('research','GET','/api/tags')
    assert budget.bootstrap == 1 and budget.research == 15 and budget.refused == 1
    with pytest.raises(ValueError): budget.reserve('owner','GET','/api/tags')


@pytest.mark.parametrize('mode',['no_card_advance','fresh_reference','code','unsafe_claim','missing_witness','read_cap','real_ack','failed_writer','foreign_ack'])
def test_visible_choices_extended(mode):
    import uuid
    p=implementation(); seen={'binding_key':['request','session','task'],'nonce':'a'*32}
    pages=[page(1),page(2),page(3)]
    if mode=='no_card_advance':
        result=p.next_reply(entity([page(1,cards=False)]),seen)
        assert result['action_input']=={'source_id':'S2','start_line':1}
        return
    if mode=='fresh_reference': pages[0]['cards'][0][0]='N3.abcdef0123456789'
    if mode=='code': pages[0]['cards'][0][1:3]=['code','enqueue']
    if mode=='unsafe_claim': pages[0]['lines'][0][1]='https://unsafe.invalid/path'
    if mode=='missing_witness': pages[0]['lines']=[]
    if mode=='read_cap':
        pages=[]
        for i in range(1,4):
            for start in (1,25):
                item=page(i,cards=False); item.update(start=start,end=start+23,next_start=None); pages.append(item)
        with pytest.raises(ValueError): p.next_reply(entity(pages),seen)
        return
    value=entity(pages,write=True)
    if mode=='missing_witness':
        with pytest.raises(ValueError,match='Visible card witness'): p.next_reply(value,seen)
        return
    if mode=='unsafe_claim':
        result=p.next_reply(value,seen)
        assert result['action']=='ultima_work_research_inspect' and result['action_input']['source_id']=='S1'
        assert result['action_input']['start_line']==25
        return
    result=p.next_reply(value,seen)
    if mode=='fresh_reference': assert result['action_input']['sections'][0]['facts'][0]['evidence_id']=='N3.abcdef0123456789'
    elif mode=='code': assert result['action_input']['sections'][0]['facts'][0]['claim']=='Observed enqueue'
    else:
        receipt=dict(path='C:/private/outputs/task/research.md',sha256='a'*64,protocol_version=3,
            report_call_id=str(uuid.uuid4()),file_call_id=str(uuid.uuid4()),replay_sha256='b'*64,runtime_sha256='c'*64,
            seq=8,generation=4,dispatch_uuid=str(uuid.uuid4()),adapter_uuid=str(uuid.uuid4()),binding=seen['binding_key'])
        ack=entity(pages,final=True)
        ack['messages'] += [dict(role='assistant',content=json.dumps(result)),dict(role='user',content='Observation: '+json.dumps(receipt))]
        if mode=='failed_writer': ack['messages'][-1]['content']='Observation: failed'
        elif mode=='foreign_ack': receipt['binding']=['old','session','task']; ack['messages'][-1]['content']='Observation: '+json.dumps(receipt)
        if mode=='real_ack': assert p.next_reply(ack,seen)=={'final_answer':'Saved research.md'}
        else:
            with pytest.raises(ValueError): p.next_reply(ack,seen)


@pytest.mark.parametrize('bad',[None,'order','origin','route','method','headers','schema','model','options','truncate','entity_cap','metadata_cap','post_cap'])
def test_native_boundaries_handler_stream(bad):
    import httpx
    p=implementation()
    assert hasattr(p,'handle_native'),'T3 native handler missing'
    seen={'binding_key':['request','session','task'],'nonce':'a'*32}
    metadata={'version':b'{"version":"0.32.15"}','tags':b'{"models":[]}'}
    def request(method,path,body=b'',origin='http://127.0.0.1:11434',headers=None):
        return httpx.Request(method,origin+path,content=body,headers=headers or {'content-type':'application/json','accept-encoding':'identity'})
    if bad in ('order','origin','route','method','headers','metadata_cap'):
        if bad=='metadata_cap': metadata['version']=b'x'*32769
        req=request('DELETE' if bad=='method' else 'GET','/api/tags' if bad=='order' else '/api/pull' if bad=='route' else '/api/version',
                    origin='https://foreign.invalid' if bad=='origin' else 'http://127.0.0.1:11434',
                    headers={'accept-encoding':'gzip'} if bad=='headers' else None)
        with pytest.raises(ValueError): p.handle_native(req,seen,metadata)
        return
    for path,key in (('/api/version','version'),('/api/tags','tags')):
        response=p.handle_native(request('GET',path),seen,metadata)
        assert response.is_stream_consumed is False and response.read()==metadata[key]
        response.close()
    value=entity(); value.update(truncate=False,shift=False)
    if bad=='schema': value['format']={'type':'string'}
    elif bad=='model': value['model']='foreign'
    elif bad=='options': value['options']['temperature']=1
    elif bad=='truncate': value['truncate']=True
    elif bad=='post_cap': seen['posts']=8
    raw=json.dumps(value).encode()
    if bad=='entity_cap': raw=b' '*49153
    before=bytes(raw); req=request('POST','/api/chat',raw)
    if bad is not None:
        with pytest.raises(ValueError): p.handle_native(req,seen,metadata)
    else:
        response=p.handle_native(req,seen,metadata)
        assert not response.is_stream_consumed
        outer=json.loads(response.read()); response.close()
        assert set(outer)=={'model','done','done_reason','message','prompt_eval_count','eval_count'}
        assert outer['message']['role']=='assistant' and json.loads(outer['message']['content'])['action']=='ultima_work_research_inspect'
        assert seen['posts']==1 and seen['completed']==1
    assert req.content==before


@pytest.mark.parametrize('mode',['quota','reserved_build_failure','header','overflow','projection'])
def test_native_boundaries_source_transport(mode,monkeypatch):
    """Pinned C118 transport source, real HTTPX MockTransport, no product import."""
    import ast
    import httpx
    import sys
    import threading
    from types import ModuleType
    p=implementation(); source=Path(__file__).parents[0]  # code path below is pinned in manifest
    source=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/agent_server.py')
    tree=ast.parse(source.read_text(encoding='utf8')); namespace={'json':json,'__name__':'src.brain.synthetic_transport','__package__':'src.brain'}
    nodes=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('_ResearchTransport','_research_sampler_schema')]
    exec(compile(ast.Module(body=nodes,type_ignores=[]),str(source),'exec'),namespace)
    if mode=='projection':
        strict={'type':'object','properties':{'x':{'type':'string','maxLength':3,'minLength':1}}}
        before=copy.deepcopy(strict); projected=namespace['_research_sampler_schema'](strict)
        assert strict==before and projected=={'type':'object','properties':{'x':{'type':'string','minLength':1}}}
        return
    tools=ModuleType('src.brain.work_tools'); tools.monotonic=lambda:100.0
    monkeypatch.setitem(sys.modules,'src.brain.work_tools',tools)
    ledger=SimpleNamespace(_lock=threading.RLock(),deadline=1000,_live=lambda:None,
        admit_ack=lambda:None,admit_report=lambda:None,_mark=lambda *a,**k:None)
    budget=p.MetadataBudget(); seen={'binding_key':['r','s','t'],'nonce':'a'*32}; counters={}; calls=[]
    metadata={'version':b'{"version":"0.32.15"}','tags':b'{"models":[]}'}
    def handler(request):
        calls.append((request.method,request.url.path))
        if mode=='header': return httpx.Response(200,headers={'content-length':'32769'},stream=httpx.ByteStream(b'never consumed'))
        if mode=='overflow': return httpx.Response(200,stream=httpx.ByteStream(b'x'*32769))
        return p.handle_native(request,seen,metadata)
    with httpx.Client(base_url='http://localhost:11434',transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b'{}')),
                      trust_env=False,follow_redirects=False) as owner:
        p._guard_client(owner,'owner',budget,None,{})
        owner.get('/api/tags')
        with httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(handler),trust_env=False,follow_redirects=False) as client:
            marker=RuntimeError('build failure')
            if mode=='reserved_build_failure':
                def build(*a,**k): raise marker
                client.build_request=build
            p._guard_client(client,'research',budget,None,counters,phase_state=seen)
            transport=namespace['_ResearchTransport'](client,ledger)
            if mode=='quota':
                value=entity(); value.update(truncate=False,shift=False); raw=json.dumps(value).encode()
                for _ in range(7):
                    assert transport.exchange('GET','/api/version','metadata')==metadata['version']
                    assert transport.exchange('GET','/api/tags','metadata')==metadata['tags']
                    transport.exchange('POST','/api/chat','chat',entity=raw)
                transport.exchange('GET','/api/version','metadata')
                with pytest.raises(ValueError): transport.exchange('GET','/api/tags','metadata')
                assert budget.bootstrap==1 and budget.research==15 and budget.refused==1
                assert transport.posts==7 and transport.completed==7 and transport.gets==15
                assert transport.receipts[-1]['send_reserved'] is False and transport.receipts[-1]['admission_error']=='ValueError'
                assert len(calls)==22 and seen['posts']==7
            else:
                with pytest.raises((RuntimeError,ValueError)) as raised: transport.exchange('GET','/api/version','metadata')
                receipt=transport.receipts[-1]
                assert budget.bootstrap==1 and budget.research==1
                if mode=='reserved_build_failure':
                    assert raised.value is marker and calls==[] and receipt['send_reserved'] is False
                elif mode=='header': assert receipt['inspected']==0 and receipt['admitted']==0
                else: assert receipt['inspected']==32769 and receipt['admitted']==receipt['retained']==32768
                assert receipt['peer_bytes'] is None and receipt['socket_bytes'] is None


@pytest.mark.parametrize('bad',['unknown_phase','wrong_route','phase_changed_after_build','reserved_build_failure'])
def test_native_boundaries_phase_before_build_send(bad):
    import httpx
    p=implementation(); state={'phase':'unknown' if bad=='unknown_phase' else 'version'}
    budget=p.MetadataBudget(); counters={}; calls=[]; marker=RuntimeError('prepared build failure')
    with httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b'{}')),
                      trust_env=False,follow_redirects=False) as client:
        build=client.build_request; send=client.send
        def original_build(*args,**kwargs):
            calls.append('build')
            if bad=='reserved_build_failure': raise marker
            return build(*args,**kwargs)
        def original_send(*args,**kwargs): calls.append('send'); return send(*args,**kwargs)
        client.build_request=original_build; client.send=original_send
        p._guard_client(client,'research',budget,None,counters,phase_state=state)
        if bad=='phase_changed_after_build':
            request=client.build_request('GET','/api/version'); state['phase']='tags'
            with pytest.raises(ValueError): client.send(request)
            assert calls==['build'] and budget.research==1
        elif bad=='reserved_build_failure':
            with pytest.raises(RuntimeError) as raised: client.build_request('GET','/api/version')
            assert raised.value is marker and calls==['build'] and budget.research==1
        else:
            with pytest.raises(ValueError): client.build_request('GET','/api/tags' if bad=='wrong_route' else '/api/version')
            assert calls==[] and budget.research==0

@pytest.mark.parametrize('bad',[None,'build_escape','build_userinfo','send_escape','send_path','send_method','send_userinfo','send_authority'])
def test_native_boundaries_issued_raw_target(bad):
    import httpx
    p=implementation(); budget=p.MetadataBudget(); counts={}; calls=[]
    with httpx.Client(base_url='http://127.0.0.1:11434',transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b'{}')),
                      trust_env=False,follow_redirects=False) as client:
        build=client.build_request; send=client.send
        def builder(*args,**kwargs): calls.append('build'); return build(*args,**kwargs)
        def sender(*args,**kwargs): calls.append('send'); return send(*args,**kwargs)
        client.build_request=builder; client.send=sender
        p._guard_client(client,'research',budget,None,counts,phase_state={'phase':'version'})
        if bad and bad.startswith('build_'):
            target='/api/%76ersion' if bad=='build_escape' else 'http://user@127.0.0.1:11434/api/version'
            with pytest.raises(ValueError): client.build_request('GET',target)
            assert calls==[] and budget.research==0 and counts['send_attempts']==0
        else:
            request=client.build_request('GET','/api/version')
            if bad=='send_escape': request.url=httpx.URL('http://127.0.0.1:11434/api/%76ersion')
            elif bad=='send_path': request.url=request.url.copy_with(path='/api/tags')
            elif bad=='send_method': request.method='POST'
            elif bad=='send_userinfo': request.url=request.url.copy_with(username='user')
            elif bad=='send_authority': request.url=request.url.copy_with(host='localhost')
            if bad is None:
                assert client.send(request).status_code==200 and calls==['build','send'] and counts['send_attempts']==1
            else:
                with pytest.raises(ValueError): client.send(request)
                assert calls==['build'] and counts['send_attempts']==0
            assert budget.research==1

@pytest.mark.parametrize('role',['owner','research'])
@pytest.mark.parametrize('bad',[None,'input_wrong','input_duplicate','client_wrong','builder_wrong','builder_duplicate'])
def test_native_boundaries_fixed_host_authority(role,bad):
    import httpx
    p=implementation(); budget=p.MetadataBudget(); counts={}; calls=[]
    host='localhost:11434' if role=='owner' else '127.0.0.1:11434'
    path='/api/tags' if role=='owner' else '/api/version'
    with httpx.Client(base_url='http://'+host,transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b'{}')),
                      trust_env=False,follow_redirects=False) as client:
        build=client.build_request; send=client.send
        def builder(*args,**kwargs):
            calls.append('build'); result=build(*args,**kwargs)
            if bad=='builder_wrong': result.headers['Host']='foreign.invalid'
            elif bad=='builder_duplicate': result.headers=httpx.Headers([*result.headers.multi_items(),('host',host)])
            return result
        def sender(*args,**kwargs): calls.append('send'); return send(*args,**kwargs)
        client.build_request=builder; client.send=sender
        p._guard_client(client,role,budget,None,counts,phase_state={'phase':'version'})
        if bad=='client_wrong': client.headers['Host']='foreign.invalid'
        headers={'Host':'foreign.invalid'} if bad=='input_wrong' else [('Host',host),('host',host)] if bad=='input_duplicate' else {}
        def perform(): return client.send(client.build_request('GET',path,headers=headers))
        if bad is None: assert perform().status_code==200 and calls==['build','send']
        else:
            with pytest.raises(ValueError): perform()
            assert 'send' not in calls and counts['send_attempts']==0
            assert calls==(['build'] if bad.startswith('builder_') else [])
        assert budget.bootstrap+budget.research==(0 if bad in ('input_wrong','input_duplicate','client_wrong') else 1)


@pytest.mark.parametrize('headers',[[('Host','foreign.invalid')],[('Host','127.0.0.1:11434'),('host','127.0.0.1:11434')]])
def test_native_boundaries_handler_fixed_host(headers):
    import httpx
    p=implementation(); seen={}
    request=httpx.Request('GET','http://127.0.0.1:11434/api/version',headers=[('content-type','application/json'),('accept-encoding','identity'),*headers])
    with pytest.raises(ValueError): p.handle_native(request,seen,{'version':b'{}'})
    assert seen.get('metadata_handled',0)==0


@pytest.mark.parametrize('role',['owner','research'])
@pytest.mark.parametrize('source',['request','client','empty'])
def test_real_factory_private_query_sources(role,source):
    import httpx
    p=implementation(); budget=p.MetadataBudget(); counts={}; calls=[]
    host='localhost:11434' if role=='owner' else '127.0.0.1:11434'
    path='/api/tags' if role=='owner' else '/api/version'
    with httpx.Client(base_url='http://'+host,transport=httpx.MockTransport(lambda r:httpx.Response(200,content=b'{}')),
                      trust_env=False,follow_redirects=False) as client:
        build=client.build_request; send=client.send
        def builder(*args,**kwargs): calls.append('build'); return build(*args,**kwargs)
        def sender(*args,**kwargs): calls.append('send'); return send(*args,**kwargs)
        client.build_request=builder; client.send=sender
        p._guard_client(client,role,budget,None,counts,phase_state={'phase':'version'})
        if source=='client': client.params={'injected':'client'}
        params={'injected':'request'} if source=='request' else {}
        def perform(): return client.send(client.build_request('GET',path,params=params))
        if source=='empty':
            assert perform().status_code==200 and calls==['build','send'] and budget.bootstrap+budget.research==1
        else:
            with pytest.raises(ValueError): perform()
            assert calls==[] and budget.bootstrap==budget.research==0 and counts['send_attempts']==0

@pytest.mark.parametrize('raised', [False, True])
def test_observe_writer_loss(raised, tmp_path, monkeypatch):
    """Break: bypassing ctor interception conflates negative return and raise."""
    import sys
    import threading
    from types import ModuleType
    p=implementation()
    assert hasattr(p,'observe_writer'), 'T4 observer missing'
    tools=ModuleType('src.brain.work_tools')
    result=SimpleNamespace(success=False,content='same')
    error=ValueError('same')
    constructor_calls=[]; physical=[]
    class SDK:
        def execute(self,**params):
            physical.append(params)
            if raised: raise error
            return result
    def factory(*args,**kwargs):
        constructor_calls.append((args,kwargs))
        return SDK()
    tools.FileWriteTool=factory
    binding=SimpleNamespace(root=tmp_path,request_id='r',session_id='s',task_id='t')
    ledger=SimpleNamespace(_lock=threading.RLock(),_binding=binding,_caller=threading.get_ident(),
        _enrolled={},_runtime_events=[],_permit=None,_staged={},_expected=None,_sealed=False,first_failure=None,
        _sequence=0,_generation=0)
    ledger.close_enrollment=lambda:None
    ledger.observe_navigation=lambda event,**kwargs:None
    ledger.seal=lambda reason:None
    allowed=[str(binding.root)]
    class Nested:
        _binding=binding
        _ledger=ledger
        _report_parent=('report','dispatch')
        _report_file_id='file'
        def execute(self,**params):
            sdk=tools.FileWriteTool(allowed_dirs=allowed)
            return sdk.execute(**params)
    nested=Nested()
    claimed_writer_identity(ledger,nested)
    ledger._enrolled['ultima_work_research_write']=SimpleNamespace(_writer=nested,ledger=ledger,binding=binding)
    monkeypatch.setitem(sys.modules,'src.brain.work_tools',tools)
    journal=p.WriterJournal()
    saved=nested.execute
    with p.observe_writer(ledger,journal):
        ledger.close_enrollment()
        if raised:
            with pytest.raises(ValueError) as caught: nested.execute(path='research.md',content='synthetic')
            assert caught.value is error
        else: assert nested.execute(path='research.md',content='synthetic') is result
    assert tools.FileWriteTool is factory
    assert len(constructor_calls)==1 and constructor_calls[0][1]['allowed_dirs'] is allowed
    assert len(physical)==1
    assert journal.constructor_matches==1
    assert [row['kind'] for row in journal.rows if row['kind'].startswith('SDK_')] == [
        'SDK_ATTEMPT', 'SDK_RAISED' if raised else 'SDK_RETURN_FALSE']
    assert 'same' not in json.dumps(journal.rows)


@pytest.fixture
def writer_contract(tmp_path,monkeypatch):
    import threading
    import sys
    from types import ModuleType
    p=implementation(); tools=ModuleType('src.brain.work_tools'); constructor_calls=[]; physical=[]
    result=SimpleNamespace(success=True,content='not diagnostic')
    class SDK:
        def execute(self,**params): physical.append(params); return result
    def factory(*args,**kwargs): constructor_calls.append((args,kwargs)); return SDK()
    tools.FileWriteTool=factory
    binding=SimpleNamespace(root=tmp_path,request_id='r',session_id='s',task_id='t')
    ledger=SimpleNamespace(_lock=threading.RLock(),_binding=binding,_caller=threading.get_ident(),
        _enrolled={},_runtime_events=[],_permit=None,_staged={},_expected=None,_sealed=False,first_failure=None,
        _sequence=0,_generation=0,_navigation=SimpleNamespace(binding_key=('r','s','t')))
    ledger.close_enrollment=lambda:None; ledger.observe_navigation=lambda event,**kwargs:None
    def seal(reason): ledger._sealed=True; ledger._permit=None; ledger.first_failure=ledger.first_failure or reason
    ledger.seal=seal; ledger.snapshot=lambda:[]
    state={'allowed':[str(binding.root)],'preintent':False}
    class Nested:
        _binding=binding; _ledger=ledger; _report_parent=('report','dispatch'); _report_file_id='file'
        def execute(self,**params):
            if state['preintent']: raise ValueError('pre intent secret')
            return tools.FileWriteTool(allowed_dirs=state['allowed']).execute(**params)
    nested=Nested(); claimed_writer_identity(ledger,nested)
    ledger._enrolled['ultima_work_research_write']=SimpleNamespace(_writer=nested,ledger=ledger,binding=binding)
    monkeypatch.setitem(sys.modules,'src.brain.work_tools',tools)
    return SimpleNamespace(p=p,tools=tools,factory=factory,ledger=ledger,binding=binding,nested=nested,
        constructor_calls=constructor_calls,physical=physical,result=result,state=state)


@pytest.mark.parametrize('bad',['unmarked_spec','unmarked_same_directory','path_item','other_string','extra_item','wrong_ledger','wrong_parent','repeat','preintent'])
def test_observe_writer_loss_constructor_contract(bad,writer_contract):
    f=writer_contract; journal=f.p.WriterJournal()
    saved=f.nested.execute; close=f.ledger.close_enrollment; navigation=f.ledger.observe_navigation; seal=f.ledger.seal
    with f.p.observe_writer(f.ledger,journal):
        f.ledger.close_enrollment()
        if bad.startswith('unmarked'):
            obj=f.tools.FileWriteTool() if bad=='unmarked_spec' else f.tools.FileWriteTool(allowed_dirs=f.state['allowed'])
            assert type(obj).__name__=='SDK' and journal.constructor_matches==0
        else:
            if bad=='path_item': f.state['allowed']=[f.binding.root]
            elif bad=='other_string': f.state['allowed']=[str(f.binding.root/'other')]
            elif bad=='extra_item': f.state['allowed']=[str(f.binding.root),str(f.binding.root)]
            elif bad=='wrong_ledger': f.nested._ledger=object()
            elif bad=='wrong_parent': f.nested._report_parent=None
            elif bad=='preintent': f.state['preintent']=True
            if bad=='repeat':
                assert f.nested.execute(path='research.md',content='private') is f.result
            with pytest.raises(ValueError): f.nested.execute(path='research.md',content='private')
            assert len(f.physical)==(1 if bad=='repeat' else 0)
            if bad not in ('repeat','preintent'): assert journal.incomplete is True
    assert f.tools.FileWriteTool is f.factory and f.ledger.close_enrollment is close
    assert f.ledger.observe_navigation is navigation and f.ledger.seal is seal
    assert f.nested.execute==saved and 'private' not in json.dumps(journal.rows)


@pytest.mark.parametrize('bad',[None,'foreign_report','foreign_dispatch','foreign_file','unclaimed','changed_inside_factory'])
def test_observe_writer_loss_claimed_parent_ids(bad,writer_contract):
    import uuid
    f=writer_contract; p=f.p; journal=p.WriterJournal(); foreign=str(uuid.uuid4())
    if bad=='foreign_report': f.nested._report_parent=(foreign,f.nested._report_parent[1])
    elif bad=='foreign_dispatch': f.nested._report_parent=(f.nested._report_parent[0],foreign)
    elif bad=='foreign_file': f.nested._report_file_id=foreign
    elif bad=='unclaimed': f.ledger._permit['claimed']=False
    elif bad=='changed_inside_factory':
        factory=f.tools.FileWriteTool
        def changed(*args,**kwargs):
            result=factory(*args,**kwargs); f.nested._report_file_id=foreign; return result
        f.tools.FileWriteTool=changed
    with p.observe_writer(f.ledger,journal):
        f.ledger.close_enrollment()
        if bad is None: assert f.nested.execute(path='research.md',content='synthetic') is f.result
        else:
            with pytest.raises(ValueError): f.nested.execute(path='research.md',content='synthetic')
    assert len(f.physical)==(1 if bad is None else 0)
    if bad is not None: assert journal.incomplete is True


@pytest.mark.parametrize('kind',['tool_call_end','tool_timeout','tool_call_start'])
def test_observe_writer_loss_pre_loss_navigation(kind,writer_contract):
    f=writer_contract; ledger=f.ledger
    ledger._sequence=1; ledger._generation=1
    ledger._expected={'name':'ultima_work_research_write','seq':1,'generation':1}
    ledger._permit={'seq':1,'name':'ultima_work_research_write','claimed':True}
    ledger._staged={1:{'content':'staged private','metadata':{'arguments':{'path':'research.md'}},'confirmed':False}}
    event=SimpleNamespace(event_type=SimpleNamespace(value=kind),timestamp=1.0,
        data={'tool':'ultima_work_research_write','agent':'native_react','success':True,'result':object(),'metadata':object()})
    def lost(event,**kwargs): ledger.seal('unsafe private payload'); return None
    ledger.observe_navigation=lost
    journal=f.p.WriterJournal()
    with f.p.observe_writer(ledger,journal):
        result=ledger.observe_navigation(event,caller_id=ledger._caller,binding_key=('r','s','t'))
        assert result is None
    rows=[row for row in journal.rows if row['kind']=='NAVIGATION']
    assert len(rows)==1 and rows[0]['observed'] is True and rows[0]['retained'] is False
    assert rows[0]['claimed'] is True and rows[0]['staged'] is True and rows[0]['caller_match'] is True
    assert rows[0]['result_match'] is None and rows[0]['metadata_match'] is None
    assert ledger._permit is None and not any(word in json.dumps(journal.rows) for word in ('private','payload'))


@pytest.mark.parametrize('stage',['not_reached','sdk_false','sdk_raise','missing_end','failed_end','ack_absent','export_after_first'])
def test_failure_strata(stage,writer_contract):
    f=writer_contract; p=f.p
    assert hasattr(p,'failure_summary'),'T4 bounded failure summary missing'
    journal=p.WriterJournal(); first={'status':'failed','error':'private product cause'}
    if stage=='sdk_false': journal.add('SDK_RETURN_FALSE',success=False)
    if stage=='sdk_raise': journal.add('SDK_RAISED',error_type='ValueError')
    if stage=='missing_end': journal.add('SDK_RETURN_TRUE',success=True)
    if stage=='failed_end': journal.add('NAVIGATION',event='tool_call_end',observed=True,retained=False,success=False)
    if stage=='ack_absent': journal.add('SDK_RETURN_TRUE',success=True)
    summary=p.failure_summary(journal,f.ledger,first,stage)
    assert summary['product_status']=='failed' and summary['released_members']==[]
    assert summary['sdk_success'] is (False if stage=='sdk_false' else True if stage in ('missing_end','ack_absent') else None)
    assert summary['sdk_exception_type']==('ValueError' if stage=='sdk_raise' else None)
    assert summary['ack'] is None and summary['file_present'] is None
    assert 'private' not in json.dumps(summary)
    assert summary['file_record_count']==0 and summary['report_record_count']==0
    assert summary['first_product_error']['sha256']==p.digest(first['error'].encode())
    assert summary['first_product_error']['bytes']==len(first['error'].encode())


def quarantine_fixture(source_inputs=None):
    import uuid
    import hashlib
    binding=[str(uuid.uuid4()) for _ in range(3)]; ids=dict(zip(('request_id','session_id','task_id'),binding))
    clean='controlled source discovery'; originals=[]
    for i in range(1,5):
        body=('Controlled body '+str(i)) if i<4 else 'z'*13001
        originals.append(dict(final_url=f'https://raw.githubusercontent.com/org/repo/pin/file{i}.txt',
            content_type='text/plain',body=body,decoded_body_sha256=hashlib.sha256(body.encode()).hexdigest()))
    if source_inputs is not None:
        originals=[{key:source[key] for key in ('final_url','content_type','body','decoded_body_sha256')} for source in source_inputs]
    hints=[dict(title=f'Retained official source {i}',url=s['final_url'],snippet='Controlled source discovery; read the full body.') for i,s in enumerate(originals,1)]
    search=dict(success=True,engine='duckduckgo',query=clean,body='\n\n---\n\n'.join(f"### {h['title']}\nSource: {h['url']}\nSummary: {h['snippet']}" for h in hints),
        results=hints,parser_diagnostics=[],fetched_at='2026-11-03T01:02:03.004Z')
    calls=[]; trace=[]; attempts=[]; catalogue=[]; records=[]
    for index in range(5):
        name='ultima_work_web_search' if index==0 else 'ultima_work_http_get'
        params={'query':clean,'max_results':5} if index==0 else {'url':originals[index-1]['final_url']}
        if index==0: result=search
        else:
            s=originals[index-1]
            result=dict(success=True,requested_url=s['final_url'],final_url=s['final_url'],dedupe_url=s['final_url'],source_id=uuid.uuid4().hex,
                fetched_at='2026-11-03T01:02:03.004Z',status_code=200,content_type='text/plain',truncated=False,
                body=s['body'],text=s['body'],decoded_body_sha256=s['decoded_body_sha256'])
        sdk_id=str(uuid.uuid4()); adapter_id=str(uuid.uuid4())
        record=dict(call_id=adapter_id,tool_name=name,success=True,**ids,result=result)
        metadata=dict(record,arguments=copy.deepcopy(params)); view=dict(result)
        if index:
            view.pop('body'); view['text']=view['text'][:12000]; view['observation_truncated']=len(result['text'])>12000
        content=json.dumps(view,ensure_ascii=False)[:10240]
        events=[dict(type='tool_call_start',timestamp=100.0+index*2,data=dict(tool=name,arguments=params,agent=binding[2])),
            dict(type='tool_call_end',timestamp=101.0+index*2,data=dict(tool=name,agent=binding[2],success=True,latency=0.1,result=content,metadata=metadata))]
        calls.append(dict(sdk_call_id=sdk_id,adapter_call_id=adapter_id,tool_name=name,arguments=params,events=events,record=record))
        attempts.append(dict(sdk_call_id=sdk_id,adapter_call_id=adapter_id,tool_name=name,optional=bool(index),success=True,deadline_monotonic=1000.0,**ids))
        trace.extend(dict(phase='research.preflight',type=e['type'],timestamp=e['timestamp'],data=e['data'],sdk_call_id=sdk_id,**ids) for e in events)
        if index:
            records.append(record); catalogue.append(dict(result,adapter_source_id=result['source_id'],source_id='S'+str(index),read_call_id=adapter_id,**ids))
    collection=dict(catalogue_json=json.dumps(catalogue,ensure_ascii=False),trace_json=json.dumps(trace,ensure_ascii=False),
        attempts_json=json.dumps(attempts,ensure_ascii=False),ignored_failure_ids=[],search_query=clean)
    canonical=lambda v:json.dumps(v,ensure_ascii=False,sort_keys=True,separators=(',',':')).encode()
    policy=dict(v=3,scanners=[dict(name='synthetic.Scanner',source_sha256='a'*64,backend='builtins.NoneType',backend_sha256=None,patterns='None')],
        mode='redact',extractor='b'*64,navigation_sha256='c'*64,witness_sha256='d'*64,python='3.13.1',htmlparser='e'*64,
        witness='source9-unchanged',serialization='J3',paging=[262144,1024,4096,3072,24,8,8],render='issued-page-v3')
    policy_hash=hashlib.sha256(canonical(policy)).hexdigest(); safe_sources=[]; safe_catalogue=[]
    for i,s in enumerate(catalogue,1):
        available=i<4
        identity=[s['source_id'],s['final_url'],s['dedupe_url'],s['read_call_id'],s['decoded_body_sha256'],s['decoded_body_sha256'],'raw',policy_hash]
        safe_sources.append(dict(source_id=s['source_id'],identity_json=identity,domain='raw',suffix='.txt',total_lines=1,
            safe_line_pairs=[[1,s['text']]],omissions=[],anchors_json=[[1,1,'documented','']],available=available,reason='' if available else 'unrenderable'))
        safe_catalogue.append(dict(source_id=s['source_id'],identity=s['final_url'].removeprefix('https://'),suffix='.txt',total_lines=1,
            available=available,reason='' if available else 'unrenderable',landmarks=[[1,1]] if available else []))
    wire=dict(v=3,source_id='S1',view_id='f'*64,start=1,end=1,total_lines=1,lines=[[1,originals[0]['body']]],
        cards=[['N3.'+'1'*16,'documented','',1,1,1,1]],omissions=[],omitted_cards=0,next_start=None)
    read=dict(key=dict(generation=1,seq=1,dispatch_uuid=str(uuid.uuid4()),adapter_uuid=str(uuid.uuid4())),source_id='S1',start=1,
              wire=wire,wire_sha256=hashlib.sha256(canonical(wire)).hexdigest())
    replay=dict(v=3,binding_key=binding,nonce='a'*32,policy=policy,catalogue=safe_catalogue,catalogue_sha256=hashlib.sha256(canonical(safe_catalogue)).hexdigest(),
        sources=safe_sources,get_records=records,reads=[read],generation=4)
    return SimpleNamespace(originals=originals,query=clean+' '+' '.join(s['final_url'] for s in originals),clean=clean,binding=binding,calls=calls,collection=collection,replay=replay)


def original_work_prompt(query,root,catalogue_json):
    import ast
    path=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/work_service.py')
    tree=ast.parse(path.read_text(encoding='utf8'))
    klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='WorkService')
    method=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='submit_work')
    statements=[]
    for node in ast.walk(method):
        if isinstance(node,ast.Assign) and any(isinstance(target,ast.Name) and target.id in ('delivery_tool','prompt') for target in node.targets):
            statements.append(copy.deepcopy(node))
        elif isinstance(node,ast.If):
            updates=[child for child in node.body if isinstance(child,ast.AugAssign) and isinstance(child.target,ast.Name) and child.target.id=='prompt']
            if updates:
                selected=copy.deepcopy(node); selected.body=copy.deepcopy(updates); selected.orelse=[]; statements.append(selected)
    assert len(statements)==5
    statements.sort(key=lambda n:n.lineno)
    namespace=dict(query=query,root=root,context={'research':True},captured=None,navigation=SimpleNamespace(catalogue_json=catalogue_json),json=json)
    exec(compile(ast.Module(body=statements,type_ignores=[]),str(path),'exec'),namespace)
    return namespace['prompt']


@pytest.mark.parametrize('mutation',[None,'start_extra','metadata_extra','hint','search_body','error','error_type','mime','status_bool',
    'receipt_order','nonfinite','replay_extra','read_extra','get_extra','body_byte','crlf','missing_capture','forged_expectations',
    'poisoned_policy','poisoned_source','poisoned_read','poisoned_empty_reads','catalogue_key_order','trace_key_order','attempt_key_order','self_chosen_deadline'])
def test_collection_quarantine(mutation):
    p=implementation()
    assert hasattr(p,'FixtureExpectations') and hasattr(p,'validate_collection'),'T4 independent pure collection validator missing'
    f=quarantine_fixture()
    expected=p.FixtureExpectations(f.originals,f.query,f.clean,f.binding,f.calls,f.replay,collection_deadline=1000.0)
    collection=copy.deepcopy(f.collection); replay=copy.deepcopy(f.replay)
    trace=json.loads(collection['trace_json']); attempts=json.loads(collection['attempts_json']); catalogue=json.loads(collection['catalogue_json'])
    if mutation=='start_extra': trace[0]['data']['secret']='unapproved'
    elif mutation=='metadata_extra': trace[1]['data']['metadata']['taint']='unapproved'
    elif mutation=='hint': trace[1]['data']['metadata']['result']['results'][0]['snippet']='changed'
    elif mutation=='search_body': trace[1]['data']['metadata']['result']['body']='changed'
    elif mutation in ('error','error_type'): attempts[0][mutation]='unapproved'
    elif mutation=='mime': catalogue[0]['content_type']='text/html'
    elif mutation=='status_bool': catalogue[0]['status_code']=True
    elif mutation=='receipt_order': attempts[1],attempts[2]=attempts[2],attempts[1]
    elif mutation=='nonfinite': trace[0]['timestamp']=float('nan')
    elif mutation=='replay_extra': replay['unapproved']='secret'
    elif mutation=='read_extra': replay['reads']=[{'unapproved':'secret'}]
    elif mutation=='get_extra': replay['get_records'][0]['unexpected']='secret'
    elif mutation=='body_byte': catalogue[0]['body']='x'+catalogue[0]['body'][1:]
    elif mutation=='crlf': catalogue[0]['body']+='\r\n'
    elif mutation=='missing_capture': expected=p.FixtureExpectations(f.originals,f.query,f.clean,f.binding,[],f.replay,collection_deadline=1000.0)
    elif mutation=='forged_expectations': expected={'verified':True}
    elif mutation=='catalogue_key_order': catalogue[0]=dict(reversed(list(catalogue[0].items())))
    elif mutation=='trace_key_order': trace[0]=dict(reversed(list(trace[0].items())))
    elif mutation=='attempt_key_order': attempts[0]=dict(reversed(list(attempts[0].items())))
    elif mutation=='self_chosen_deadline':
        for attempt in attempts: attempt['deadline_monotonic']=2000.0
    elif type(mutation) is str and mutation.startswith('poisoned_'):
        if mutation=='poisoned_policy': replay['policy']['unexpected']='unapproved'
        elif mutation=='poisoned_source': replay['sources'][0]['unexpected']='unapproved'
        elif mutation=='poisoned_read': replay['reads'][0]['key']['unexpected']='unapproved'
        else: replay['reads']=[]
        expected=p.FixtureExpectations(f.originals,f.query,f.clean,f.binding,f.calls,replay,collection_deadline=1000.0)
    collection.update(trace_json=json.dumps(trace,ensure_ascii=False),attempts_json=json.dumps(attempts,ensure_ascii=False),catalogue_json=json.dumps(catalogue,ensure_ascii=False))
    replay['collection']=copy.deepcopy(collection)
    collection_raw=json.dumps(collection,ensure_ascii=False).encode(); replay_raw=json.dumps(replay,ensure_ascii=False).encode()
    if mutation is None:
        assert p.validate_collection(collection_raw,replay_raw,expected) is None
        full=json.loads(collection['trace_json'])[-1]['data']['metadata']['result']
        outward=json.loads(collection['trace_json'])[-1]['data']['result']
        assert len(full['body'])==13001 and len(outward)==10240
    else:
        with pytest.raises(ValueError): p.validate_collection(collection_raw,replay_raw,expected)


@pytest.mark.parametrize('mode',[None,'other_task','other_bus','other_tool','missing_record','duplicate_record','raised',
    'foreign_bus_first','foreign_origin','deadline_drift'])
def test_replay_tamper_preflight_capture(mode,monkeypatch,tmp_path):
    import sys
    import threading
    from types import ModuleType
    p=implementation()
    assert hasattr(p,'PreflightCapture') and hasattr(p,'observe_preflight'),'CAPTURE02 boundary missing'
    f=quarantine_fixture(); binding=SimpleNamespace(root=tmp_path,**dict(zip(('request_id','session_id','task_id'),f.binding)))
    record_delegations=[]; ledger=SimpleNamespace(_lock=threading.RLock(),record=lambda record:record_delegations.append(record))
    capture=p.PreflightCapture(ledger,binding); calls=[]; error=ValueError('not diagnostic')
    origin,invoke=preflight_origin_double(); monkeypatch.setitem(sys.modules,'src.brain.work_research',origin)
    foreign_id=__import__('uuid').uuid4().hex
    class Bus:
        def __init__(self): self.handlers={}
        def subscribe(self,kind,callback): self.handlers.setdefault(kind,[]).append(callback)
        def unsubscribe(self,kind,callback): self.handlers[kind].remove(callback)
        def emit(self,event):
            for callback in list(self.handlers.get(event.event_type.value,[])): callback(event)
    bus=Bus(); wrong=Bus()
    events=ModuleType('openjarvis.core.events'); events.EventType=SimpleNamespace(TOOL_CALL_START='tool_call_start',TOOL_CALL_END='tool_call_end',TOOL_TIMEOUT='tool_timeout')
    tools=ModuleType('src.brain.work_tools'); tools._ACTIVE=SimpleNamespace(get=lambda:(binding,ledger,None))
    results=[]
    class Executor:
        def __init__(self,bus,agent): self._bus=bus; self._agent_id=agent
        def execute(self,call):
            calls.append(call)
            if mode=='raised': raise error
            offset=1 if mode=='foreign_bus_first' and len(calls)>1 else 0
            original=f.calls[len(calls)-1-offset]
            if mode not in ('missing_record',):
                ledger.record(original['record'])
                if mode=='duplicate_record': ledger.record(original['record'])
            for raw in original['events']:
                event=SimpleNamespace(event_type=SimpleNamespace(value=raw['type']),timestamp=raw['timestamp'],data=raw['data'])
                assert 'sdk_call_id' not in event.data
                self._bus.emit(event)
            result=SimpleNamespace(success=True,metadata=dict(original['record'],arguments=original['arguments']))
            results.append(result); return result
    stubs=ModuleType('openjarvis.tools._stubs'); stubs.ToolExecutor=Executor
    monkeypatch.setitem(sys.modules,'src.brain.work_tools',tools); monkeypatch.setitem(sys.modules,'openjarvis.core.events',events)
    monkeypatch.setitem(sys.modules,'openjarvis.tools._stubs',stubs)
    execute=Executor.execute; record=ledger.record
    if mode=='other_bus': capture.bus=bus
    with p.observe_preflight(ledger,capture):
        if mode=='foreign_bus_first':
            Executor(wrong,binding.task_id).execute(SimpleNamespace(id=str(__import__('uuid').UUID(foreign_id)),name=f.calls[0]['tool_name'],arguments=json.dumps(f.calls[0]['arguments'])))
        for original in f.calls if mode not in ('other_task','other_bus','other_tool','raised') else f.calls[:1]:
            call=SimpleNamespace(id=original['sdk_call_id'],name='unrelated' if mode=='other_tool' else original['tool_name'],arguments=json.dumps(original['arguments']))
            executor=Executor(wrong if mode=='other_bus' else bus,'other' if mode=='other_task' else binding.task_id)
            if mode=='raised':
                with pytest.raises(ValueError) as raised: invoke(executor,call,binding,ledger,1000.0)
                assert raised.value is error
            elif mode=='foreign_origin': assert executor.execute(call) is results[-1]
            else: assert invoke(executor,call,binding,ledger,1001.0 if mode=='deadline_drift' and original is f.calls[-1] else 1000.0) is results[-1]
            assert not any(bus.handlers.values()) and not any(wrong.handlers.values())
    assert Executor.execute is execute and ledger.record is record
    assert len(calls)==(1 if mode in ('other_task','other_bus','other_tool','raised') else 6 if mode=='foreign_bus_first' else 5)
    if mode in (None,'foreign_bus_first'):
        observed=capture.finish()
        assert len(observed)==5 and observed[0]['sdk_call_id']==f.calls[0]['sdk_call_id']
        assert observed==f.calls and len(record_delegations)==(6 if mode=='foreign_bus_first' else 5)
    elif mode in ('other_task','other_bus','other_tool','foreign_origin'):
        assert capture.calls==[]
    else:
        with pytest.raises(ValueError): capture.finish()


@pytest.mark.parametrize('bad',[None,'relative','inside_case','inside_worker','nonempty','noncanonical','missing_roots','proxy','host','fail_open','raised',
    'models_override','config_override','xdg_data_override'])
def test_replay_tamper_reader_scratch(bad,tmp_path,monkeypatch):
    from contextlib import contextmanager
    p=implementation()
    assert hasattr(p,'reader_scope'),'IF02 reader isolation missing'
    worker=tmp_path/'worker'; worker.mkdir(); case=worker/'case'; case.mkdir(); (case/'closed').write_bytes(b'immutable')
    reader=tmp_path/'reader'; reader.mkdir(); package=tmp_path/'package'; package.mkdir()
    pins=dict(reader_root=str(reader),worker_evidence_roots=[str(worker)],package_root=str(package),
        import_path=list(p.sys.path),candidate_root=str(tmp_path),model_digest=p.MODEL_DIGEST,files={})
    monkeypatch.chdir(package); seen=[]; error=RuntimeError('primary')
    for key in list(p.os.environ):
        if key.upper() in ('OLLAMA_HOST','OLLAMA_API_KEY','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP',
                'OPENJARVIS_HOME','XDG_CACHE_HOME','OPENJARVIS_SSRF_FAIL_OPEN') or key.upper().endswith('_PROXY'):
            monkeypatch.delenv(key)
    if bad=='relative': pins['reader_root']='relative'
    elif bad=='inside_case': pins['reader_root']=str(case/'reader')
    elif bad=='inside_worker': pins['reader_root']=str(worker/'reader')
    elif bad=='nonempty': (reader/'old').write_bytes(b'old')
    elif bad=='noncanonical': pins['reader_root']=str(reader/'..'/'reader')
    elif bad=='missing_roots': pins.pop('worker_evidence_roots')
    elif bad=='proxy': monkeypatch.setenv('https_proxy','')
    elif bad=='host': monkeypatch.setenv('OLLAMA_HOST','')
    elif bad=='fail_open': monkeypatch.setenv('OPENJARVIS_SSRF_FAIL_OPEN','')
    elif bad=='models_override': monkeypatch.setenv('OLLAMA_MODELS','')
    elif bad=='config_override': monkeypatch.setenv('OPENJARVIS_CONFIG','')
    elif bad=='xdg_data_override': monkeypatch.setenv('XDG_DATA_HOME','')
    monkeypatch.setattr(p.sys,'addaudithook',lambda audit:seen.append('audit'))
    @contextmanager
    def eager(pins,audit):
        seen.append('eager')
        for key,leaf in (('OPENJARVIS_HOME','home'),('XDG_CACHE_HOME','cache'),('TMP','tmp'),('TEMP','temp')):
            assert p.os.environ.get(key)==str(reader/leaf)
        audit['eager']={'clean':True}; audit['metadata_charged']=0
        yield {'owner':SimpleNamespace(_client=SimpleNamespace(is_closed=True))}
    monkeypatch.setattr(p,'own_ollama_types',eager)
    before=dict(p.os.environ); path_before=list(p.sys.path)
    def perform():
        with p.reader_scope(case,pins) as scope:
            assert scope['audit'].denied=={} and scope['eager_audit']['metadata_charged']==0
            assert set(x.name for x in reader.iterdir())=={'home','cache','tmp','temp'}
            if bad=='raised': raise error
    if bad is None: perform()
    elif bad=='raised':
        with pytest.raises(RuntimeError) as raised: perform()
        assert raised.value is error
    else:
        with pytest.raises(ValueError): perform()
        assert seen==[]
    assert dict(p.os.environ)==before and p.sys.path==path_before and (case/'closed').read_bytes()==b'immutable'
    assert list(case.iterdir())==[case/'closed']


def restricted_service_handler_source():
    """Pinned research verifier branch and unchanged product catch/seal/effects AST."""
    import ast
    import hashlib
    files=json.loads((HERE/'manifest.json').read_bytes())['files']
    source=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/work_service.py')
    assert hashlib.sha256(source.read_bytes()).hexdigest()==files[str(source)]
    cls=next(n for n in ast.parse(source.read_text(encoding='utf8')).body if isinstance(n,ast.ClassDef) and n.name=='WorkService')
    submit=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='submit_work')
    original=next(n for n in submit.body if isinstance(n,ast.Try))
    validation=next(n for n in original.body if isinstance(n,ast.If) and any(isinstance(i,ast.ImportFrom)
        and i.module=='work_research' and any(a.name=='verify_research_artifacts' for a in i.names) for i in n.body))
    handler=original.handlers[0]
    assert len(original.handlers)==1 and isinstance(handler.body[0],ast.If)
    assert any(isinstance(n,ast.Call) and isinstance(n.func,ast.Attribute) and n.func.attr=='seal' for n in ast.walk(handler.body[0]))
    status=next(n for n in handler.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.IfExp)
        and isinstance(n.value.body,ast.Constant) and n.value.body.value=='needs_attention')
    assert handler.body.index(status)>0
    success=next(n for n in original.body if isinstance(n,ast.Assign) and isinstance(n.value,ast.Constant) and n.value.value=='succeeded')
    assignment=ast.parse('records,research_effects=outcome').body[0]
    setup=ast.parse('ledger,result,binding,context,capabilities,outcome=_prepare_service(self,query)').body[0]
    fn=ast.FunctionDef(name='submit_work',args=ast.arguments(posonlyargs=[],args=[ast.arg(arg=n)
        for n in ('self','query')],kwonlyargs=[],kw_defaults=[],defaults=[]),
        body=[setup,assignment,ast.Try(body=[copy.deepcopy(validation),copy.deepcopy(success)],handlers=[copy.deepcopy(handler)],orelse=[],finalbody=[]),
              ast.Return(value=ast.Name(id='result',ctx=ast.Load()))],decorator_list=[])
    env={'__package__':'src.brain'}
    exec(compile(ast.fix_missing_locations(ast.Module(body=[fn],type_ignores=[])),str(source),'exec'),env)
    tools_source=source.with_name('work_tools.py')
    assert hashlib.sha256(tools_source.read_bytes()).hexdigest()==files[str(tools_source)]
    ledger_cls=next(n for n in ast.parse(tools_source.read_text(encoding='utf8')).body if isinstance(n,ast.ClassDef) and n.name=='WorkLedger')
    seal=next(n for n in ledger_cls.body if isinstance(n,ast.FunctionDef) and n.name=='seal')
    exec(compile(ast.Module(body=[copy.deepcopy(seal)],type_ignores=[]),str(tools_source),'exec'),env)
    return env['submit_work'],env['seal']


@pytest.mark.parametrize('mode',[None,'export_raise','ack_export_raise','runtime_mismatch','duplicate_ledger',
    'terminal_failed_lost_end','terminal_raised_lost_end','terminal_failed_no_end','terminal_failed_no_ack',
    'terminal_raised_no_ack','terminal_failed_negative','terminal_raised_negative','terminal_failed_lost_outcome','terminal_raised_lost_outcome',
    'terminal_attention_no_ack','terminal_export_lost_end','terminal_export_lost_outcome','terminal_export_negative',
    'terminal_failed_complete_ack','terminal_attention_complete_ack','terminal_failed_negative_complete_ack',
    'terminal_catch_attention_export_ok','terminal_catch_attention_export_raise','terminal_catch_failed_export_ok',
    'terminal_catch_failed_export_raise','terminal_catch_pre_ack_false'])
def test_replay_tamper_submission_boundaries(mode,tmp_path,monkeypatch):
    import ast
    import sys
    import threading
    import uuid
    from types import ModuleType
    from dataclasses import make_dataclass,asdict
    p=implementation()
    assert hasattr(p,'observe_submission'),'T4 submission callback integration missing'
    f=quarantine_fixture(); binding=SimpleNamespace(root=tmp_path/'outputs'/f.binding[2],**dict(zip(('request_id','session_id','task_id'),f.binding)))
    tools=ModuleType('src.brain.work_tools'); services=ModuleType('src.brain.work_service')
    Runtime=make_dataclass('RuntimeInputs',[(key,object) for key in ('prompt','binding_key','root','allowance','deadline')])
    catching=type(mode) is str and mode.startswith('terminal_catch_')
    product_marker=ValueError('post ACK product validation failed')
    source_handler,source_seal=restricted_service_handler_source() if catching else (None,None)
    class Ledger:
        def __init__(self):
            self._lock=threading.RLock(); self._records=[]; self.deadline=1000.0
            self._runtime_events=[]; self._permit=None; self._staged={}; self._enrolled={}; self._expected=None
            self._sealed=False; self._sequence=0; self._generation=0; self._caller=threading.get_ident(); self.first_failure=None
        def record(self,value): self._records.append(value)
        def snapshot(self): return list(self._records)
        def _prepare_navigation(self,binding,catalogue,collection,get_records_json,policy):
            self._binding=binding; self._navigation=catalogue; self._policy=policy
        def _freeze_runtime_inputs(self,prompt,max_tokens):
            self._runtime_inputs=Runtime(prompt,self._navigation.binding_key,str(self._binding.root),2048 if max_tokens is None else max_tokens,repr(self.deadline))
        def _read_port(self,instance):
            def read(args):
                item=f.replay['reads'][0]; return json.dumps(item['wire'],sort_keys=True,ensure_ascii=False,separators=(',',':')),dict(item['key'],binding=f.binding)
            return read
        def freeze_for_write(self,generation): return SimpleNamespace(generation=generation)
        def close_enrollment(self): pass
        def observe_navigation(self,*args,**kwargs):
            if mode=='ack_export_raise' or (type(mode) is str and mode.startswith('terminal_')):
                self._staged[self._sequence]['confirmed']=True; self._runtime_events.append('original END retained'); self._permit=None
        def seal(self,reason): self._sealed=True
        def _mark(self,kind,**kwargs): return 1
        def outcome_snapshot(self): return self._source_outcome
    if catching: Ledger.seal=source_seal
    tools.WorkLedger=Ledger
    def sdk_factory(**kwargs):
        return SimpleNamespace(execute=lambda **params:SimpleNamespace(success='_negative' not in mode and '_pre_ack_false' not in mode))
    tools.FileWriteTool=sdk_factory if type(mode) is str and mode.startswith('terminal_') else object
    current=[None]; tools._ACTIVE=SimpleNamespace(get=lambda:(binding,current[0],None))
    origin,invoke=preflight_origin_double(); monkeypatch.setitem(sys.modules,'src.brain.work_research',origin)
    if catching:
        def verify_research_artifacts(*args,**kwargs): raise product_marker
        origin.verify_research_artifacts=verify_research_artifacts
    class Bus:
        def __init__(self): self.handlers={}
        def subscribe(self,k,fn): self.handlers.setdefault(k,[]).append(fn)
        def unsubscribe(self,k,fn): self.handlers[k].remove(fn)
        def emit(self,e):
            for fn in list(self.handlers.get(e.event_type.value,[])): fn(e)
    bus=Bus(); stubs=ModuleType('openjarvis.tools._stubs'); events=ModuleType('openjarvis.core.events')
    events.EventType=SimpleNamespace(TOOL_CALL_START='tool_call_start',TOOL_CALL_END='tool_call_end',TOOL_TIMEOUT='tool_timeout')
    class Executor:
        def __init__(self): self._bus=bus; self._agent_id=binding.task_id
        def execute(self,call):
            original=next(c for c in f.calls if c['sdk_call_id']==call.id)
            current[0].record(original['record'])
            for e in original['events']: bus.emit(SimpleNamespace(event_type=SimpleNamespace(value=e['type']),timestamp=e['timestamp'],data=e['data']))
            return SimpleNamespace(success=True,metadata=original['record'])
    stubs.ToolExecutor=Executor
    result=dict(status='running' if catching else 'needs_attention' if type(mode) is str and 'attention' in mode else 'failed',**dict(zip(('request_id','session_id','task_id'),f.binding))); marker=RuntimeError('export private cause')
    class Service:
        def submit_work(self,query):
            ledger=Ledger(); current[0]=ledger
            if mode=='duplicate_ledger': Ledger()
            for call in f.calls: invoke(Executor(),SimpleNamespace(id=call['sdk_call_id'],name=call['tool_name'],arguments=json.dumps(call['arguments'])),binding,ledger,1000.0)
            nav=SimpleNamespace(binding_key=tuple(f.binding),nonce=f.replay['nonce'],catalogue_json=p.canonical(f.replay['catalogue']),catalogue_sha256=f.replay['catalogue_sha256'])
            collection=SimpleNamespace(**f.collection); policy=SimpleNamespace(policy_json=p.canonical(f.replay['policy']))
            ledger._prepare_navigation(binding,nav,collection,json.dumps(f.replay['get_records']).encode(),policy)
            ledger._freeze_runtime_inputs(original_work_prompt(query,binding.root,nav.catalogue_json),None)
            if mode=='runtime_mismatch': ledger._runtime_inputs.root='C:/foreign'
            ledger._read_port(None)({'source_id':'S1','start_line':1}); ledger.freeze_for_write(4)
            # Installed exporter sees no completed packet, preserving failed first result.
            ledger.issued_snapshot=None
            if type(mode) is str and mode.startswith('terminal_'):
                binding.root.mkdir(parents=True,exist_ok=True)
                class Nested:
                    _binding=binding; _ledger=ledger
                    def execute(self,**params): return tools.FileWriteTool(allowed_dirs=[str(binding.root)]).execute(**params)
                nested=Nested(); claimed_writer_identity(ledger,nested)
                ledger._sequence=ledger._generation=4; ledger._permit.update(seq=4,generation=4)
                ledger._enrolled['ultima_work_research_write']=SimpleNamespace(_writer=nested,ledger=ledger,binding=binding)
                ledger._expected={'name':'ultima_work_research_write'}
                metadata=dict(report_call_id=nested._report_parent[0],dispatch_uuid=nested._report_parent[1],file_call_id=nested._report_file_id,arguments={'path':'research.md'})
                ledger._staged[4]={'content':'same','metadata':metadata,'confirmed':False}
                journal=captures[0]['journal']; add=journal.add
                if mode.endswith(('_lost_end','_lost_outcome')):
                    def lost(kind,**fields):
                        if kind==('SDK_RETURN_TRUE' if mode.endswith('_lost_outcome') else 'NAVIGATION'): raise OSError('diagnostic row lost')
                        return add(kind,**fields)
                    journal.add=lost
                ledger.close_enrollment(); nested.execute(path='research.md',content='synthetic writer')
                if not mode.endswith(('_no_end','_negative')) and '_pre_ack_false' not in mode:
                    event=SimpleNamespace(event_type=SimpleNamespace(value='tool_call_end'),data=dict(tool='ultima_work_research_write',agent='native_react',success=True,result='same',metadata=metadata))
                    ledger.observe_navigation(event,caller_id=ledger._caller,binding_key=f.binding)
                if mode.endswith('_complete_ack') or (catching and '_pre_ack_false' not in mode):
                    for cls,method in ((scope['server']._NativeResearchLeaf,'generate'),(scope['server']._ResearchTransport,'exchange'),(scope['server']._ResearchEngineView,'generate')):
                        obj=cls(); obj.ledger=ledger; getattr(obj,method)()
                if mode.startswith('terminal_raised_'): raise marker
                if mode.startswith('terminal_export_'): ledger._runtime_final=b'{}'; ledger.issued_snapshot=object()
                if catching:
                    ledger._runtime_final=None if '_pre_ack_false' in mode else b'{}'
                    ledger.issued_snapshot=object() if ledger._runtime_final else None
                    committed='attention' in mode or '_pre_ack_false' in mode
                    ledger._source_outcome=([dict(tool_name='ultima_work_file_write',success=committed,may_have_committed=committed)] if committed else [],[])
                    result.update(artifacts=[],available_sources=[],error=None)
                    return ledger,result,binding,{'research':True},SimpleNamespace(research_json=collection.catalogue_json),ledger._source_outcome
            if mode=='ack_export_raise':
                ids={name:str(uuid.uuid4()) for name in ('report_call_id','dispatch_uuid','file_call_id')}
                metadata=dict(ids,arguments={'path':'research.md'})
                ledger._sequence=ledger._generation=4; ledger._expected={'name':'ultima_work_research_write'}
                ledger._navigation=nav; ledger._permit={'seq':4,'claimed':True}
                ledger._staged[4]={'content':'same','metadata':metadata,'confirmed':False}
                event=SimpleNamespace(event_type=SimpleNamespace(value='tool_call_end'),data=dict(tool='ultima_work_research_write',agent='native_react',success=True,result='same',metadata=metadata))
                ledger.observe_navigation(event,caller_id=ledger._caller,binding_key=f.binding)
                for cls,method in ((scope['server']._NativeResearchLeaf,'generate'),(scope['server']._ResearchTransport,'exchange'),(scope['server']._ResearchEngineView,'generate')):
                    obj=cls(); obj.ledger=ledger; getattr(obj,method)()
            if mode in ('export_raise','ack_export_raise'): ledger._runtime_final=b'{}'; ledger.issued_snapshot=object()
            return result
    if catching:
        source_handler.__globals__['_prepare_service']=Service.submit_work
        Service.submit_work=source_handler
    services.WorkService=Service
    for name,module in (('src.brain.work_tools',tools),('src.brain.work_service',services),('openjarvis.tools._stubs',stubs),('openjarvis.core.events',events)):
        monkeypatch.setitem(sys.modules,name,module)
    adapter_path=binding_adapter().LEGACY; tree=ast.parse(adapter_path.read_text(encoding='utf8'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='install_trusted_exports')
    def save_new(path,value):
        with path.open('xb') as stream: stream.write(json.dumps(value,ensure_ascii=False).encode())
    export_first_bytes=[]
    def export(*args):
        export_first_bytes.append((tmp_path/'service-first-result.json').read_bytes())
        if catching and mode.endswith('_export_ok'): return None
        raise marker
    namespace=dict(asdict=asdict,require=p.require,save_new=save_new,export_completed=export)
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(adapter_path),'exec'),namespace)
    adapter=SimpleNamespace(install_trusted_exports=namespace['install_trusted_exports'])
    originals=(Ledger.__init__,Ledger._freeze_runtime_inputs,Ledger._prepare_navigation,Service.submit_work,Executor.execute)
    scope=dict(adapter=adapter,server=runtime_mark_server_double(),seen={},inputs={'query':f.query,'sources':f.originals},browser={'search_query':f.clean},cleanup={'errors':[]})
    captures=[]
    def perform():
        with p.observe_submission(scope,tmp_path) as captured:
            captures.append(captured)
            assert Service().submit_work(f.query) is result
        return captured
    if type(mode) is str and mode.startswith('terminal_'):
        raised=mode.startswith('terminal_raised_')
        exported=mode.startswith('terminal_export_') or (catching and mode.endswith('_export_raise'))
        if raised or exported:
            with pytest.raises(RuntimeError) as caught: perform()
            assert caught.value is marker
        else: perform()
        journal=captures[0]['journal']; first=None if raised else json.loads((tmp_path/'service-first-result.json').read_bytes())
        summary=p.failure_summary(journal,current[0],first,'submission')
        expected='sdk_false' if catching and '_pre_ack_false' in mode else 'service_result' if catching else 'unknown' if mode.endswith(('_lost_end','_lost_outcome')) else 'missing_end' if mode.endswith('_no_end') else 'sdk_false' if '_negative' in mode else 'service_result' if mode.endswith('_complete_ack') else 'ack_absent'
        assert summary['stage']==expected
        assert summary['observation_complete'] is (not mode.endswith(('_lost_end','_lost_outcome')))
        if mode.endswith(('_lost_end','_lost_outcome','_negative')): assert summary['terminal_missing'] is None
        assert journal.first_failure_stage==('sdk_false' if '_negative' in mode or '_pre_ack_false' in mode else None)
        assert summary['released_members']==[]
        if mode.endswith('_complete_ack'): assert summary['ack_verified'] is True
        assert summary['submission_exception_type']==('RuntimeError' if raised else None)
        assert summary['export_exception_type']==('RuntimeError' if exported else None)
        assert summary['submission_status']==(None if raised else result['status'])
        assert summary['product_status']==(None if raised else result['status'])
        if raised: assert not (tmp_path/'service-first-result.json').exists()
        else: assert first==result
        if exported: assert export_first_bytes==[(tmp_path/'service-first-result.json').read_bytes()]
        if catching:
            assert first['status']==('needs_attention' if 'attention' in mode or '_pre_ack_false' in mode else 'failed')
            seal=next(row for row in journal.rows if row['kind']=='SEAL')
            if '_pre_ack_false' in mode:
                assert summary['ack_verified'] is None and summary['first_negative_kind']=='SDK_RETURN_FALSE'
            else:
                ack=next(row for row in journal.rows if row['kind']=='ACK_SECURED')
                assert seal['order']>ack['order'] and summary['ack_verified'] is True
                assert seal['service_handler'] is True
                assert summary['first_negative_order']==seal['order'] and summary['first_negative_at_ns']==seal['at_ns']
                assert summary['seal_cause']==dict(bytes=len(str(product_marker).encode()),sha256=p.digest(str(product_marker).encode()))
                assert first['error']==str(product_marker) and export_first_bytes==[(tmp_path/'service-first-result.json').read_bytes()]
        if '_negative' in mode:
            negative=next(row for row in journal.rows if row['kind']=='SDK_RETURN_FALSE')
            assert summary['first_negative_order']==negative['order']
    elif mode is None:
        captured=perform()
        assert captured['preflight'].finish()==f.calls and len(captured['reads'])==1 and captured['write_generation']==4
        assert captured['runtime_inputs']['binding_key']==f.binding
        assert (tmp_path/'preflight-observations.json').is_file() and (tmp_path/'profile-observations.json').is_file()
    elif mode in ('export_raise','ack_export_raise'):
        with pytest.raises(RuntimeError) as raised: perform()
        assert raised.value is marker
        summary=p.failure_summary(captures[0]['journal'],current[0],result,'submission')
        assert summary['stage']=='export_after_first'
        assert summary['export_exception_type']=='RuntimeError' and summary['submission_exception_type'] is None
        assert summary['submission_status']=='failed' and captures[0]['journal'].first_failure_stage is None
        if mode=='ack_export_raise':
            assert summary['ack_attempted'] is summary['ack_admitted'] is summary['ack_verified'] is True
            assert summary['writer_end_confirmed'] is True
    else:
        with pytest.raises(ValueError): perform()
    assert (Ledger.__init__,Ledger._freeze_runtime_inputs,Ledger._prepare_navigation,Service.submit_work,Executor.execute)==originals
    if mode not in ('duplicate_ledger',) and not (type(mode) is str and mode.startswith('terminal_raised_')):
        assert json.loads((tmp_path/'service-first-result.json').read_bytes())==result
    assert not any(bus.handlers.values())


@pytest.fixture
def pure_reconstruction(monkeypatch,tmp_path,request):
    """Actual pinned pure producer routines with explicit no-finding scanner doubles."""
    import sys
    import time
    from types import ModuleType
    p=implementation()
    source_inputs=None
    if getattr(request,'param',None)=='original':
        source_inputs=json.loads((HERE.parent.parent/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_bytes())['sources']
    f=quarantine_fixture(source_inputs)
    root=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain')
    loaded={}
    for name,file in (('src.brain.work_research','work_research.py'),('src.brain.work_navigation','work_navigation.py')):
        module=ModuleType(name); module.__file__=str(root/file); module.__package__='src.brain'
        monkeypatch.setitem(sys.modules,name,module)
        exec(compile((root/file).read_text(encoding='utf8'),str(root/file),'exec'),module.__dict__)
        loaded[name]=module
    class Scanner:
        def scan(self,text): return SimpleNamespace(clean=True)
        def redact(self,text): return text
    scanners=ModuleType('openjarvis.security.scanner'); scanners.SecretScanner=Scanner; scanners.PIIScanner=Scanner
    monkeypatch.setitem(sys.modules,'openjarvis.security.scanner',scanners)
    nav=loaded['src.brain.work_navigation']; research=loaded['src.brain.work_research']
    policy=nav.make_scan_policy((Scanner(),Scanner()),'redact')
    binding=SimpleNamespace(root=tmp_path/'outputs'/f.binding[2],**dict(zip(('request_id','session_id','task_id'),f.binding)))
    collection=research.ResearchCollection(**dict(f.collection,ignored_failure_ids=()))
    cat=nav.prepare_navigation(collection,binding,policy,get_records_json=p.canonical(f.replay['get_records']),deadline=time.monotonic()+30)
    import uuid
    reads=[]; issued=[]; sections=[]
    for i in range(1,4):
        entry=json.loads(cat.catalogue_json)[i-1]; start=entry['landmarks'][0][0] if entry['landmarks'] else 1
        key=nav.PageKey(i,i,str(uuid.uuid4()),str(uuid.uuid4())); view=nav.scan_view(nav.build_page(cat,'S'+str(i),start,key),policy)
        wire=json.loads(view.wire_json)
        reads.append(dict(key=dict(generation=i,seq=i,dispatch_uuid=key.dispatch_uuid,adapter_uuid=key.adapter_uuid),
            source_id='S'+str(i),start=start,wire=wire,wire_sha256=view.wire_sha256)); issued.append((key,view))
        if source_inputs is None:
            card=wire['cards'][0]; lines=dict(wire['lines'])
            claim='Observed '+card[2] if card[1]=='code' else next(lines[n] for n in range(card[3],card[4]+1) if p._claim_text(lines[n]))
            sections.append(dict(source_id='S'+str(i),heading='S'+str(i),facts=[dict(claim=claim,evidence_id=card[0])]))
    snapshot=nav.seal_snapshot(cat,collection,p.canonical(f.replay['get_records']),policy,issued,generation=4)
    action=dict(path='research.md',title='Controlled profile',sections=sections)
    rendered=None
    if source_inputs is None:
        resolved,bindings=nav.resolve_v3(action,snapshot,collection); rendered=nav.render_v3(resolved,collection.catalogue_json,bindings=bindings)
    pre=dict(format=1,binding=f.binding,root=str(binding.root),calls=f.calls,collection_deadline=1000.0,
        query_sha256=p.digest(f.query.encode()),search_query=f.clean,policy=json.loads(policy.policy_json),nonce=cat.nonce,catalogue_sha256=cat.catalogue_sha256)
    observations=dict(format=1,complete=True,preflight_sha256='a'*64,runtime_inputs_sha256='b'*64,reads=reads,write_generation=4,
        writer_rows=linked_writer_rows_fixture(reads),observer_incomplete=False)
    return SimpleNamespace(p=p,f=f,pre=pre,observations=observations,snapshot=snapshot,binding=binding,nav=nav,research=research,
        inputs={'query':f.query,'sources':f.originals},action=action,rendered=rendered)


@pytest.mark.parametrize('bad',[None,'policy','wire','nonce','query','missing_capture','generation'])
def test_replay_tamper_independent_pure_rebuild(bad,pure_reconstruction):
    r=pure_reconstruction; p=r.p
    assert hasattr(p,'rebuild_expectations'),'T4 independent reconstruction missing'
    pre=copy.deepcopy(r.pre); observations=copy.deepcopy(r.observations)
    if bad=='policy': pre['policy']['mode']='warn'
    elif bad=='wire': observations['reads'][0]['wire']['lines'][0][1]='different'
    elif bad=='nonce': pre['nonce']='b'*32
    elif bad=='query': pre['query_sha256']='c'*64
    elif bad=='missing_capture': pre['calls']=[]
    elif bad=='generation': observations['write_generation']=True
    if bad is None:
        expected=p.rebuild_expectations(pre,observations,r.inputs)
        assert type(expected) is p.FixtureExpectations
        # No quarantined replay was an input to reconstruction.
        assert p.validate_collection(json.dumps(r.f.collection).encode(),r.snapshot.replay_json,expected) is None
    else:
        with pytest.raises(ValueError): p.rebuild_expectations(pre,observations,r.inputs)


@pytest.mark.parametrize('pure_reconstruction',['original'],indirect=True)
@pytest.mark.parametrize('tamper',[False,True])
def test_collection_quarantine_original_trace_bound(tamper,pure_reconstruction):
    r=pure_reconstruction; p=r.p
    assert [len(source['body'].encode('utf8')) for source in r.f.originals]==[7236,3252,4643,13559]
    assert len(r.f.collection['trace_json'])>65536
    baseline=json.loads(r.snapshot.replay_json); independent=copy.deepcopy(baseline); independent.pop('collection')
    expected=p.FixtureExpectations(r.f.originals,r.f.query,r.f.clean,r.f.binding,r.f.calls,independent,collection_deadline=1000.0)
    collection=copy.deepcopy(r.f.collection); replay=copy.deepcopy(baseline)
    if tamper:
        trace=json.loads(collection['trace_json']); original=trace[3]['data']['metadata']['result']['body']
        trace[3]['data']['metadata']['result']['body']='X'+original[1:]
        collection['trace_json']=json.dumps(trace,ensure_ascii=False); replay['collection']=copy.deepcopy(collection)
        with pytest.raises(ValueError): p.validate_collection(p.canonical(collection),p.canonical(replay),expected)
    else: assert p.validate_collection(p.canonical(collection),r.snapshot.replay_json,expected) is None


def test_replay_tamper_actual_collect_origin(pure_reconstruction,monkeypatch):
    import sys
    import threading
    from types import ModuleType
    r=pure_reconstruction; p=r.p; f=r.f; records=[]; independent_sdk_ids=[]
    ledger=SimpleNamespace(_lock=threading.RLock(),record=lambda value:records.append(value),snapshot=lambda:list(records))
    binding=r.binding; tools=ModuleType('src.brain.work_tools'); tools._ACTIVE=SimpleNamespace(get=lambda:(binding,ledger,None))
    monkeypatch.setitem(sys.modules,'src.brain.work_tools',tools)
    class Bus:
        def __init__(self): self.handlers={}
        def subscribe(self,key,fn): self.handlers.setdefault(key,[]).append(fn)
        def unsubscribe(self,key,fn): self.handlers[key].remove(fn)
        def publish(self,kind,data,timestamp):
            event=SimpleNamespace(event_type=SimpleNamespace(value=kind),data=data,timestamp=timestamp)
            for fn in list(self.handlers.get(kind,[])): fn(event)
    events=ModuleType('openjarvis.core.events'); events.EventBus=Bus
    events.EventType=SimpleNamespace(TOOL_CALL_START='tool_call_start',TOOL_CALL_END='tool_call_end',TOOL_TIMEOUT='tool_timeout')
    registry=ModuleType('openjarvis.core.registry'); registry.ToolRegistry=SimpleNamespace(create=lambda name:SimpleNamespace(name=name))
    types=ModuleType('openjarvis.core.types'); types.ToolCall=lambda **kwargs:SimpleNamespace(**kwargs)
    stubs=ModuleType('openjarvis.tools._stubs')
    class Executor:
        def __init__(self,tools,*,bus,agent_id): self._bus=bus; self._agent_id=agent_id
        def execute(self,call):
            index=len(independent_sdk_ids); independent_sdk_ids.append(call.id); original=f.calls[index]
            ledger.record(original['record'])
            for event in original['events']: self._bus.publish(event['type'],event['data'],event['timestamp'])
            return SimpleNamespace(success=True,metadata=original['record'])
    stubs.ToolExecutor=Executor
    for name,module in (('openjarvis.core.events',events),('openjarvis.core.registry',registry),('openjarvis.core.types',types),('openjarvis.tools._stubs',stubs)):
        monkeypatch.setitem(sys.modules,name,module)
    monkeypatch.setattr(r.research,'candidate_inputs',lambda query,urls:(f.clean,[s['final_url'] for s in f.originals]))
    capture=p.PreflightCapture(ledger,binding)
    with p.observe_preflight(ledger,capture):
        collection=r.research.collect_research(f.query,[],binding=binding,ledger=ledger,capabilities=None)
    observed=capture.finish()
    assert [call['sdk_call_id'] for call in observed]==independent_sdk_ids
    assert all(attempt['deadline_monotonic']==capture.deadline for attempt in json.loads(collection.attempts_json))
    assert all('sdk_call_id' not in event['data'] for call in observed for event in call['events'])


@pytest.mark.parametrize('mode',[None,'self_controls','first_error','first_shape','final_error','final_ref_drift','final_time_backwards',
    'collection_drift','runtime_missing','partial_export','forged_type','during_replay_drift','extra_output','missing_ack',
    'missing_clock','mutated_clock','deadline_boundary','deadline_late','wrong_run','wrong_nonce','wrong_pid','wrong_creation','worker_time','actual_v2',
    'runtime_bool','runtime_allowance','runtime_prompt','mutable_readback_hash','mutable_readback_time',
    'empty_writer_rows','missing_writer_end','mismatched_writer_end','unconfirmed_writer_end','ack_unknown','writer_row_foreign_id',
    'journal_trailing_start','journal_duplicate_start','journal_missing_start','journal_unknown_event','journal_start_bad_id',
    'journal_start_bool_seq','journal_start_float_generation','journal_end_float_seq','journal_ack_float_seq',
    'journal_start_bad_boolean','journal_start_bad_nullable','journal_inspect_out_of_order','worker_ssrf_wrong_source',
    'journal_inspect_foreign_dispatch','journal_inspect_swapped_dispatch','journal_inspect_writer_dispatch','root_ssrf_backend_mismatch'])
def test_replay_tamper_read_profile_gate(mode,pure_reconstruction,tmp_path,monkeypatch):
    from contextlib import contextmanager
    r=pure_reconstruction; p=r.p
    assert hasattr(p,'read_profile'),'T4 independent reader entry missing'
    case=tmp_path/'case'; case.mkdir(); artifact=case/'outputs'/r.f.binding[2]/'research.md'; artifact.parent.mkdir(parents=True)
    artifact.write_bytes(r.rendered.content.encode('utf8')); events=[]
    runtime_inputs=dict(prompt=original_work_prompt(r.f.query,artifact.parent,p.canonical(json.loads(r.snapshot.replay_json)['catalogue'])),
        binding_key=r.f.binding,root=str(artifact.parent),allowance=2048,deadline='1000.0')
    if mode=='runtime_bool': runtime_inputs['allowance']=True
    elif mode=='runtime_allowance': runtime_inputs['allowance']=1
    elif mode=='runtime_prompt': runtime_inputs['prompt']='changed private prompt'
    product=dict(status='succeeded',**dict(zip(('request_id','session_id','task_id'),r.f.binding)),artifacts=[dict(path=str(artifact),sha256=p.digest(artifact.read_bytes()))])
    pre=copy.deepcopy(r.pre); pre['root']=str(artifact.parent); observations=copy.deepcopy(r.observations)
    identity=next(row for row in observations['writer_rows'] if row['kind']=='SDK_ATTEMPT')
    runtime_packet=dict(execution=dict(files=[dict(call_id=identity['file_call_id'],report_call_id=identity['report_call_id'],
        dispatch_uuid=identity['dispatch_uuid'],success=True,tool_name='ultima_work_file_write')],
        effects=[dict(report_call_id=identity['report_call_id'],file_call_id=identity['file_call_id'],dispatch_id=identity['dispatch_uuid'],state='completed')]),
        wires=[{}, {'secured_envelope':{'action_input':r.action}}, {'generation':5,'secured_envelope':{'final_answer':'Saved research.md'}}],transport={'posts':5})
    writer_end=next(row for row in observations['writer_rows'] if row.get('tool_role')=='writer' and row.get('event')=='tool_call_end')
    writer_start=next(row for row in observations['writer_rows'] if row.get('tool_role')=='writer' and row.get('event')=='tool_call_start')
    if mode=='empty_writer_rows': observations['writer_rows']=[]
    elif mode=='missing_writer_end': observations['writer_rows']=[row for row in observations['writer_rows'] if row['kind']!='NAVIGATION']
    elif mode=='mismatched_writer_end': writer_end['metadata_match']=False
    elif mode=='unconfirmed_writer_end': writer_end['confirmed_after']=False
    elif mode=='ack_unknown': observations['writer_rows']=[row for row in observations['writer_rows'] if not row['kind'].startswith('ACK_')]
    elif mode=='writer_row_foreign_id': writer_end['file_call_id']=str(__import__('uuid').uuid4())
    elif mode=='journal_trailing_start': observations['writer_rows'].append(copy.deepcopy(writer_start))
    elif mode=='journal_duplicate_start': observations['writer_rows'].insert(6,copy.deepcopy(writer_start))
    elif mode=='journal_missing_start': observations['writer_rows'].remove(writer_start)
    elif mode=='journal_unknown_event': writer_start['event']='foreign_event'
    elif mode=='journal_start_bad_id': writer_start['report_call_id']='not-a-uuid'
    elif mode=='journal_start_bool_seq': observations['writer_rows'][0]['seq']=True
    elif mode=='journal_start_float_generation': writer_start['generation']=4.0
    elif mode=='journal_end_float_seq': writer_end['seq']=4.0
    elif mode=='journal_ack_float_seq': observations['writer_rows'][-1]['seq']=4.0
    elif mode=='journal_start_bad_boolean': writer_start['caller_match']=1
    elif mode=='journal_start_bad_nullable': writer_start['claimed']=False
    elif mode=='journal_inspect_out_of_order': observations['writer_rows'][0],observations['writer_rows'][1]=observations['writer_rows'][1],observations['writer_rows'][0]
    elif mode=='journal_inspect_foreign_dispatch': observations['writer_rows'][1]['dispatch_uuid']=str(__import__('uuid').uuid4())
    elif mode=='journal_inspect_swapped_dispatch':
        observations['writer_rows'][1]['dispatch_uuid'],observations['writer_rows'][3]['dispatch_uuid']=observations['writer_rows'][3]['dispatch_uuid'],observations['writer_rows'][1]['dispatch_uuid']
    elif mode=='journal_inspect_writer_dispatch': observations['writer_rows'][1]['dispatch_uuid']=identity['dispatch_uuid']
    if mode and mode.startswith('journal_'):
        for order,row in enumerate(observations['writer_rows'],1): row.update(order=order,at_ns=order)
    def save(name,value): (case/name).write_bytes(p.canonical(value))
    save('runtime-inputs.json',runtime_inputs); save('service-first-result.json',product); save('preflight-observations.json',pre)
    observations.update(preflight_sha256=p.digest((case/'preflight-observations.json').read_bytes()),runtime_inputs_sha256=p.digest((case/'runtime-inputs.json').read_bytes()))
    save('profile-observations.json',observations)
    blobs={'runtime':p.canonical(runtime_packet),'views':r.snapshot.views_json,'replay':r.snapshot.replay_json,'collection':p.canonical(r.f.collection)}
    if mode=='collection_drift': blobs['collection']=b'{}'
    members={}
    for role,raw in blobs.items():
        name='trusted-'+role+'.raw'; (case/name).write_bytes(raw); members[role]=dict(name=name,bytes=len(raw),sha256=p.digest(raw))
    from dataclasses import asdict
    snapshot_fields=asdict(r.snapshot); snapshot_fields.pop('views_json'); snapshot_fields.pop('replay_json')
    exported=dict(format=2,complete=mode!='partial_export',END=True,members=members,ack_admitted=mode!='missing_ack',issued_snapshot=snapshot_fields,native_POST_attempts=5)
    save('trusted-export.json',exported)
    if mode=='runtime_missing': (case/'runtime-inputs.json').unlink()
    if mode=='extra_output': (artifact.parent/'extra.txt').write_bytes(b'extra')
    files={str(path.relative_to(case)).replace('\\','/'):{'bytes':path.stat().st_size,'sha256':p.digest(path.read_bytes())} for path in case.rglob('*') if path.is_file()}
    save('closed-index.json',dict(format=1,files=files))
    first=dict(format=1,status='candidate',run_id=r.f.binding[0],entry_nonce=r.f.binding[1],worker_pid=123,
        worker_creation_filetime=456,product_status='succeeded',first_product_sha256=p.digest((case/'service-first-result.json').read_bytes()),
        closed_index_sha256=p.digest((case/'closed-index.json').read_bytes()),observations_sha256=p.digest((case/'profile-observations.json').read_bytes()),
        runtime_inputs_sha256=p.digest((case/'runtime-inputs.json').read_bytes()) if (case/'runtime-inputs.json').exists() else 'b'*64,
        work_returned_ns=10,cleanup_closed_ns=20,sealed_ns=30,counters=good_counter_fixture(),error_type=None,secondary_errors=[],released_members=[])
    first['counters']['ssrf']=ssrf_receipt_fixture('worker',[s['final_url'] for s in r.inputs['sources']])
    if mode=='worker_ssrf_wrong_source': first['counters']['ssrf']['records'][1]['source_url_sha256']='f'*64
    save('profile-first-result.json',first)
    class Controls(p.RootControls):
        def __init__(self):
            self.calls=0
            self._admission=dict(origin_ns=1000,work_deadline_ns=1000+275*10**9,cleanup_deadline_ns=1000+310*10**9,
                seal_deadline_ns=1000+315*10**9,run_id=r.f.binding[0],entry_nonce=r.f.binding[1],worker_pid=123,worker_creation_filetime=456)
            if mode=='missing_clock': self._admission=None
            elif mode=='mutated_clock': self._admission['seal_deadline_ns']+=1
            elif mode=='wrong_run': self._admission['run_id']=r.f.binding[2]
            elif mode=='wrong_nonce': self._admission['entry_nonce']=r.f.binding[2]
            elif mode=='wrong_pid': self._admission['worker_pid']+=1
            elif mode=='wrong_creation': self._admission['worker_creation_filetime']+=1
        def readback(self,folder,reference):
            self.calls+=1; events.append('root'+str(self.calls))
            assert folder==case and reference is first
            if mode==('first_error' if self.calls==1 else 'final_error'): raise ValueError('Root private refusal')
            admission=self._admission
            p.require(type(admission) is dict,'Private Root admission unavailable')
            for field,seconds in (('work_deadline_ns',275),('cleanup_deadline_ns',310),('seal_deadline_ns',315)):
                p.require(admission[field]==admission['origin_ns']+seconds*10**9,'Private Root original clock corrupt')
            for field,value in dict(run_id=r.f.binding[0],entry_nonce=r.f.binding[1],worker_pid=123,worker_creation_filetime=456).items():
                p.require(admission[field]==value,'Private Root identity mismatch')
            now=admission['origin_ns']+(100 if self.calls==1 else 300)*10**9
            if self.calls==2 and mode in ('deadline_boundary','deadline_late'): now=admission['seal_deadline_ns']+(1 if mode=='deadline_late' else 0)
            p.require(now<=admission['seal_deadline_ns'],'Root independently observed final expiry')
            p.require('observed_at_ns' not in reference,'Worker clock is comparison-only')
            result=dict(run_id=first['run_id'],entry_nonce=first['entry_nonce'],worker_pid=123,worker_creation_filetime=456,
                python_exit_code=0,observed_at_ns=now,first_result_sha256=p.digest((case/'profile-first-result.json').read_bytes()),
                closed_index_sha256=first['closed_index_sha256'],expectations_sha256=first['observations_sha256'],runtime_inputs_sha256=first['runtime_inputs_sha256'],protected_after_sha256='e'*64)
            if mode=='first_shape': result['worker_exit_claim']=0
            if self.calls==2 and mode=='final_ref_drift': result['protected_after_sha256']='f'*64
            if self.calls==2 and mode=='final_time_backwards': result['observed_at_ns']=99
            if mode in ('mutable_readback_hash','mutable_readback_time'):
                if self.calls==1: self._shared=result
                else:
                    if mode=='mutable_readback_hash': result['protected_after_sha256']='f'*64
                    else: result['observed_at_ns']=self._shared['observed_at_ns']-1
                    self._shared.clear(); self._shared.update(result)
                return self._shared
            return result
    controls=Controls()
    if mode=='worker_time':
        first['observed_at_ns']=1000+100*10**9
        save('profile-first-result.json',first)
    @contextmanager
    def reader(folder,pins): events.append('reader'); yield {}
    monkeypatch.setattr(p,'reader_scope',reader)
    @contextmanager
    def ssrf(pins,urls,*,counters=None):
        counters.update(observations=ssrf_receipt_fixture('reader',urls)['records'])
        yield counters
    monkeypatch.setattr(p,'reader_ssrf',ssrf)
    monkeypatch.setattr(p,'original_inputs',lambda adapter,pins:r.inputs)
    p4_path=tmp_path/'p4.py'; p4_path.write_bytes(b'synthetic pinned helper')
    p4=SimpleNamespace(__file__=str(p4_path))
    def verify(folder,result,helper,*,readonly):
        events.append('typed_replay'); assert readonly is True and helper is p4 and result==product
        if mode=='during_replay_drift': (case/'trusted-runtime.raw').write_bytes(b'drift')
        inventory=[dict(path=str(path),sha256=p.digest(path.read_bytes())) for path in artifact.parent.iterdir()]
        return dict(native_POST_attempts=True if mode=='forged_type' else 5,inventory=inventory)
    adapter=SimpleNamespace(verify_exports=verify)
    if mode=='actual_v2':
        import ast
        import sys
        from types import ModuleType
        from dataclasses import make_dataclass
        tools=ModuleType('src.brain.work_tools')
        tools.WorkBinding=make_dataclass('Binding',[(key,object) for key in ('root','request_id','session_id','task_id')])
        tools.ResearchRuntimeInputs=make_dataclass('Runtime',[(key,object) for key in ('prompt','binding_key','root','allowance','deadline')])
        monkeypatch.setitem(sys.modules,'src.brain.work_tools',tools)
        native_packet=runtime_packet
        def typed(binding,snapshot,collection,raw,*,require_ack,runtime_inputs):
            events.append('typed_replay')
            assert type(binding) is tools.WorkBinding and type(runtime_inputs) is tools.ResearchRuntimeInputs
            assert require_ack is True and snapshot.replay_json==r.snapshot.replay_json and raw==blobs['runtime']
            return native_packet
        monkeypatch.setattr(r.research,'verify_runtime_packet',typed)
        source=binding_adapter().LEGACY; tree=ast.parse(source.read_text(encoding='utf8'))
        selected=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in ('verify_exports','read_completed','verify_readback')]
        p4.uuid_text=lambda value:value
        p4.artifact_path=lambda folder,task,path:Path(path)
        p4.output_inventory=lambda folder:[dict(path=str(artifact),sha256=p.digest(artifact.read_bytes()))]
        namespace=dict(Path=Path,json=json,hashlib=__import__('hashlib'),CAP=p.CAP,require=p.require,strict_json=p.strict_json,
            load=lambda path:p.strict_json(path.read_bytes()),read_raw=p.bounded_read,
            reconcile_results=lambda left,right:p.require(left==right,'First result mismatch'),corpus=lambda:{'sources':r.f.originals},
            validate_export_structure=lambda packet,scanners:p.require(packet is native_packet and len(scanners)==2,'Typed scanner validation'),
            output_inventory=lambda folder,helper:helper.output_inventory(folder))
        exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),'exec'),namespace)
        # Pinned V2 readonly hydration/replay/render/reopen source; the full
        # runtime-packet verifier is an explicit double, never runtime proof.
        adapter=SimpleNamespace(verify_exports=namespace['verify_exports'])
    monkeypatch.setattr(p,'load_adapter',lambda pins:adapter)
    monkeypatch.setattr(p,'make_service',lambda *args:pytest.fail('reader constructed service'))
    monkeypatch.setattr(p,'OwnerHTTPXFacade',lambda *args:pytest.fail('reader constructed owner'))
    pins={'p4_path':str(p4_path),'files':{str(p4_path):p.digest(p4_path.read_bytes())},'ssrf_backend':'rust' if mode=='root_ssrf_backend_mismatch' else 'python'}
    result=p.read_profile(case,first,p4,controls={'verified':True} if mode=='self_controls' else controls,pins=pins)
    if mode in (None,'deadline_boundary','actual_v2'):
        assert result['status']=='candidate_mechanical_verified' and len(result['released_members'])==4, result
        assert result['ack_attempted'] is result['ack_admitted'] is result['ack_verified'] is True
        assert result['ssrf']['context']=='reader' and result['ssrf']['native_dns'] is result['ssrf']['native_cache'] is result['ssrf']['packets'] is None
        assert events==['root1','reader','typed_replay','root2'] and controls.calls==2
    else:
        assert result['status']=='failed' and result['released_members']==[]
        if mode in ('self_controls','first_error','first_shape'): assert 'typed_replay' not in events
    assert (case/'profile-first-result.json').read_bytes()==p.canonical(first)


@pytest.mark.parametrize('mode',[None,'failed_result','needs_attention_result','export_raised','service_raised','cleanup_raised','first_and_cleanup','audit_caught','observer_incomplete','backend_mismatch'])
def test_failure_strata_worker_entry(mode,tmp_path,monkeypatch):
    exercise_worker_entry(mode,tmp_path,monkeypatch)


def exercise_worker_entry(mode,tmp_path,monkeypatch):
    """Worker orchestration only, using explicit private-scope/service doubles."""
    from contextlib import contextmanager
    import sys
    import uuid
    from types import ModuleType
    p=implementation()
    assert hasattr(p,'run_profile'),'T4 one-shot worker entry missing'
    original=json.loads((HERE.parent.parent/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_bytes())
    folder=tmp_path/'case'; folder.mkdir(); order=[]; calls=[]
    grant=admission_double(p,folder,{key:'a'*64 for key in ('profile_manifest_sha256','candidate_manifest_sha256','corpus_sha256')})
    # This scope double emits Python SSRF observations; Root independently pins
    # that backend. The mismatch mode deliberately keeps the generic Rust grant.
    if mode!='backend_mismatch': grant['ssrf_backend']='python'
    primary=ValueError('private original cause'); secondary=OSError('private secondary close')
    audit=p.WorkerAudit(); budget=p.MetadataBudget(); budget.bootstrap=1; budget.research=10
    class Bus:
        def __init__(self): self.handlers={}
        def subscribe(self,kind,fn): self.handlers.setdefault(kind,[]).append(fn)
        def unsubscribe(self,kind,fn): self.handlers[kind].remove(fn)
        def emit(self,kind):
            for fn in list(self.handlers.get(kind,[])): fn(SimpleNamespace(event_type=SimpleNamespace(value=kind),data={}))
    bus=Bus(); events=ModuleType('openjarvis.core.events'); events.EventType=SimpleNamespace(INFERENCE_START='inference_start',INFERENCE_END='inference_end')
    monkeypatch.setitem(sys.modules,'openjarvis.core.events',events)
    owner_client=SimpleNamespace(is_closed=False); research_client=SimpleNamespace(is_closed=False)
    p4=SimpleNamespace(); adapter=SimpleNamespace(load_p4=lambda:p4)
    scope=dict(server=SimpleNamespace(),adapter=adapter,p4=None,owner=None,counters={'owner':{'handled':1,'refused':0,'construct_attempts':1},'research':{'send_attempts':15,'refused':0,'construct_attempts':1}},
        budget=budget,persona={},eager={'owner':SimpleNamespace(_client=object())},eager_audit={'eager':{'clean':True}},
        audit=audit,controls=object(),grant=grant,seen={'posts':5,'completed':5,'refused':0,'metadata_handled':10},
        clients=[owner_client,research_client],submitted=False,cleanup={'errors':[]},
        owner_facade=SimpleNamespace(client=owner_client,raw_owner=object()),
        browser={'searches':1,'GETs':4,'sdk_searches':1,'sdk_GETs':4,'refused':0,'dns':{'observations':ssrf_receipt_fixture('worker')['records']}})
    @contextmanager
    def private(folder,pins,admission):
        order.append('scope')
        try: yield scope
        finally:
            order.append('cleanup'); owner_client.is_closed=research_client.is_closed=True
            scope['clean']=not bool(audit.denied)
            if mode in ('cleanup_raised','first_and_cleanup'): raise secondary
    monkeypatch.setattr(p,'private_scope',private)
    journal=p.WriterJournal(); journal.constructor_matches=1; journal.add('SDK_ATTEMPT'); journal.add('SDK_RETURN_TRUE',success=True)
    journal.incomplete=mode=='observer_incomplete'
    if mode in ('work_boundary','work_late','cleanup_boundary','cleanup_late','seal_boundary','seal_late','setup_expired'):
        clocks=[grant['work_deadline_ns']-2,grant['work_deadline_ns']-1,grant['cleanup_deadline_ns']-1,grant['seal_deadline_ns']-1]
        field=1 if mode.startswith('work') else 2 if mode.startswith('cleanup') else 3
        clocks[field]=grant[('work_deadline_ns','cleanup_deadline_ns','seal_deadline_ns')[field-1]]+(1 if mode.endswith('late') else 0)
        if mode=='setup_expired': clocks=[grant['work_deadline_ns']+1,grant['cleanup_deadline_ns']-1,grant['seal_deadline_ns']-1]
        monkeypatch.setattr(p.time,'monotonic_ns',lambda:clocks.pop(0))
    @contextmanager
    def observed(scope,folder):
        order.append('capture'); yield {'journal':journal}
        if mode=='export_raised': raise primary
    monkeypatch.setattr(p,'observe_submission',observed)
    monkeypatch.setattr(p,'original_inputs',lambda adapter,pins:original)
    class Service:
        def submit_work(self,query,**kwargs):
            calls.append((query,kwargs)); order.append('submit')
            if mode in ('service_raised','first_and_cleanup'): raise primary
            for _ in range(5): bus.emit('inference_start'); bus.emit('inference_end')
            if mode=='audit_caught':
                try: audit('socket.connect',())
                except ValueError: pass
            result=dict(status='failed' if mode=='failed_result' else 'needs_attention' if mode=='needs_attention_result' else 'succeeded',task_id=str(uuid.uuid4()),
                request_id=kwargs['request_id'],session_id=kwargs['session_id'])
            (folder/'service-first-result.json').write_bytes(p.canonical(result))
            return result
    def make(scope,folder): scope['owner']=SimpleNamespace(_bus=bus); return Service()
    monkeypatch.setattr(p,'make_service',make)
    def perform(): return p.run_profile(folder,{},object())
    if mode=='setup_expired':
        with pytest.raises(ValueError): perform()
        assert calls==[] and (folder/'profile-first-result.json').is_file()
        assert json.loads((folder/'profile-first-result.json').read_bytes())['status']=='failed'
        return
    if mode=='seal_late':
        with pytest.raises(ValueError): perform()
        assert not (folder/'profile-first-result.json').exists() and (folder/'service-first-result.json').exists()
        with pytest.raises(ValueError): perform()
        assert len(calls)==1
        return
    if mode in ('export_raised','service_raised','cleanup_raised','first_and_cleanup','work_boundary','work_late'):
        with pytest.raises((ValueError,OSError)) as raised: perform()
        if mode not in ('work_boundary','work_late'): assert raised.value is (secondary if mode=='cleanup_raised' else primary)
        first=json.loads((folder/'profile-first-result.json').read_bytes()); assert first['status']=='failed'
        if mode=='cleanup_raised':
            assert json.loads((folder/'failure-summary.json').read_bytes())['stage']=='cleanup'
    else:
        first=perform()
        assert first['status']==('candidate' if mode in (None,'cleanup_boundary','seal_boundary') else 'failed')
    assert len(calls)==1 and calls[0][0]==original['query'] and calls[0][1]['context']=={'research':True}
    assert order.index('capture')<order.index('submit')<order.index('cleanup')
    assert first['released_members']==[] and (folder/'closed-index.json').is_file()
    assert first['counters']['ssrf']['context']=='worker'
    assert first['counters']['ssrf']['native_dns'] is first['counters']['ssrf']['native_cache'] is first['counters']['ssrf']['packets'] is None
    if mode=='first_and_cleanup': assert first['secondary_errors']==['OSError']
    if mode not in (None,'cleanup_boundary','seal_boundary'):
        assert (folder/'failure-summary.json').is_file()
        assert 'private original cause' not in (folder/'failure-summary.json').read_text(encoding='utf8')
        if mode=='needs_attention_result':
            assert first['status']=='failed' and first['product_status']=='needs_attention'
            assert json.loads((folder/'failure-summary.json').read_bytes())['product_status']=='needs_attention'
    before=(folder/'profile-first-result.json').read_bytes()
    with pytest.raises(ValueError): perform()
    assert len(calls)==1 and (folder/'profile-first-result.json').read_bytes()==before
    assert not any(bus.handlers.values())


@pytest.mark.parametrize('mode',['not_reached','positive','negative_file','raised_file','failed_end'])
def test_failure_strata_physical_file(mode,writer_contract):
    f=writer_contract; p=f.p; journal=p.WriterJournal(); marker=ValueError('private writer failure'); raw=b'Observed physical bytes\r\n'
    factory=f.tools.FileWriteTool
    def physical_factory(*args,**kwargs):
        sdk=factory(*args,**kwargs)
        def execute(**params):
            (f.binding.root/'research.md').write_bytes(raw)
            if mode=='raised_file': raise marker
            f.result.success=mode!='negative_file'
            return f.result
        sdk.execute=execute; return sdk
    f.tools.FileWriteTool=physical_factory
    with p.observe_writer(f.ledger,journal):
        f.ledger.close_enrollment()
        if mode=='raised_file':
            with pytest.raises(ValueError) as raised: f.nested.execute(path='research.md',content='ignored')
            assert raised.value is marker
        elif mode!='not_reached': assert f.nested.execute(path='research.md',content='ignored') is f.result
        if mode=='failed_end': journal.add('NAVIGATION',event='tool_call_end',success=False,observed=True,retained=False)
    summary=p.failure_summary(journal,f.ledger,{'status':'failed'},'failed_end' if mode=='failed_end' else 'sdk_raise' if mode=='raised_file' else 'sdk_false')
    assert summary['file_present'] is (None if mode=='not_reached' else True)
    assert summary['file_sha256']==(None if mode=='not_reached' else p.digest(raw))
    assert summary['file_bytes']==(None if mode=='not_reached' else len(raw))
    assert summary['ack'] is None and summary['released_members']==[]
    assert 'Observed physical' not in json.dumps(summary)


@pytest.mark.parametrize('bad',[None,'tool','agent','arguments','caller','binding'])
def test_observe_writer_loss_linkage(bad,writer_contract):
    f=writer_contract; ledger=f.ledger; p=f.p; journal=p.WriterJournal()
    ledger._sequence=2; ledger._generation=2
    ledger._expected={'name':'ultima_work_research_write','seq':2,'generation':2}
    ledger._permit={'seq':2,'name':'ultima_work_research_write','claimed':True}
    metadata={'arguments':{'path':'research.md'},'report_call_id':'private invalid id','file_call_id':'private invalid id'}
    ledger._staged={2:{'content':'same','metadata':metadata,'confirmed':False}}
    data=dict(tool='other' if bad=='tool' else 'ultima_work_research_write',agent='other' if bad=='agent' else 'native_react',
        success=True,result='same',metadata=copy.deepcopy(metadata))
    if bad=='arguments': data['metadata']['arguments']['path']='other'
    event=SimpleNamespace(event_type=SimpleNamespace(value='tool_call_end'),data=data,timestamp=1.0); delegated=[]
    def navigation(original,**kwargs): delegated.append((original,kwargs)); return event
    ledger.observe_navigation=navigation; caller=ledger._caller+1 if bad=='caller' else ledger._caller
    binding=('other','s','t') if bad=='binding' else ('r','s','t')
    with p.observe_writer(ledger,journal): assert ledger.observe_navigation(event,caller_id=caller,binding_key=binding) is event
    row=next(row for row in journal.rows if row['kind']=='NAVIGATION')
    assert row['seq']==2 and row['generation']==2 and row['sequence_match'] is True
    assert row['tool_match'] is (bad!='tool') and row['agent_match'] is (bad!='agent')
    assert row['arguments_match'] is (bad!='arguments') and row['caller_match'] is (bad!='caller')
    assert row['binding_match'] is (bad!='binding')
    assert row['report_call_id'] is None and row['file_call_id'] is None
    assert len(delegated)==1 and delegated[0][0] is event and 'private invalid' not in json.dumps(journal.rows)


def test_observe_writer_loss_actual_callback_drop(writer_contract):
    import ast
    import copy
    from types import MethodType
    f=writer_contract; p=f.p; ledger=f.ledger
    path=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/work_tools.py')
    tree=ast.parse(path.read_text(encoding='utf8')); klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='WorkLedger')
    node=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='observe_navigation')
    namespace=dict(json=json,copy=copy,threading=__import__('threading'))
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(path),'exec'),namespace)
    ledger.observe_navigation=MethodType(namespace['observe_navigation'],ledger)
    ledger._sequence=1; ledger._generation=1; ledger._sealed=True
    ledger._permit={'seq':1,'claimed':True}; ledger._staged={1:{'content':'same','metadata':{},'confirmed':False}}
    ledger._expected={'name':'ultima_work_research_write'}
    def live(): raise ValueError('sealed')
    ledger._live=live; ledger._scan_output=lambda data:None
    event=SimpleNamespace(event_type=SimpleNamespace(value='tool_call_end'),timestamp=1.0,
        data=dict(tool='ultima_work_research_write',agent='native_react',success=True,result=object(),metadata=object()))
    journal=p.WriterJournal()
    with p.observe_writer(ledger,journal):
        assert ledger.observe_navigation(event,caller_id=ledger._caller,binding_key=('r','s','t')) is None
    row=next(row for row in journal.rows if row['kind']=='NAVIGATION')
    assert row['claimed'] is True and row['staged'] is True and row['observed'] is True and row['retained'] is False
    assert ledger._permit is None and ledger._runtime_events==[]


@pytest.mark.parametrize('boundary',['sdk_return','sdk_raise','navigation'])
def test_observe_writer_loss_diagnostic_failure_preserves_product(boundary,writer_contract,monkeypatch):
    f=writer_contract; p=f.p; journal=p.WriterJournal(); marker=RuntimeError('original identity'); calls=[]
    def diagnostic(*args,**kwargs): raise ValueError('diagnostic storage failure')
    monkeypatch.setattr(journal,'add',diagnostic)
    if boundary=='navigation':
        def original(event,**kwargs): calls.append(event); raise marker
        f.ledger.observe_navigation=original
    else:
        factory=f.tools.FileWriteTool
        def source(*args,**kwargs):
            sdk=factory(*args,**kwargs)
            def execute(**params):
                calls.append(params)
                if boundary=='sdk_raise': raise marker
                return f.result
            sdk.execute=execute; return sdk
        f.tools.FileWriteTool=source
    with p.observe_writer(f.ledger,journal):
        f.ledger.close_enrollment()
        if boundary=='sdk_return': assert f.nested.execute(path='research.md',content='safe') is f.result
        else:
            with pytest.raises(RuntimeError) as raised:
                if boundary=='navigation': f.ledger.observe_navigation(SimpleNamespace(event_type=SimpleNamespace(value='tool_call_end'),data={}),caller_id=f.ledger._caller,binding_key=('r','s','t'))
                else: f.nested.execute(path='research.md',content='safe')
            assert raised.value is marker
    assert len(calls)==1 and journal.incomplete is True


@pytest.mark.parametrize('outcome',['secured_export_failure','end_dropped','secured_mark_raised'])
def test_observe_writer_loss_ack_observation(outcome,writer_contract):
    f=writer_contract; p=f.p; journal=p.WriterJournal(); source=runtime_mark_server_double()
    assert hasattr(p,'observe_runtime_marks'),'R05 bounded actual ACK marker observer missing'
    ledger=f.ledger; calls=[]; marker=RuntimeError('original marker failure')
    ledger._sequence=4; ledger._generation=4; ledger._permit.update(seq=4,generation=4)
    parent=f.nested._report_parent; metadata=dict(report_call_id=parent[0],dispatch_uuid=parent[1],file_call_id=f.nested._report_file_id,
        arguments={'path':'research.md'})
    ledger._expected={'name':'ultima_work_research_write'}
    ledger._staged={4:{'content':'same','metadata':metadata,'confirmed':False}}
    def navigation(event,**kwargs):
        if outcome=='end_dropped': ledger.seal('Unlinked or failed END'); return None
        ledger._staged[4]['confirmed']=True; ledger._runtime_events.append('retained'); ledger._permit=None
    ledger.observe_navigation=navigation
    def mark(kind,**fields):
        calls.append((kind,fields))
        if outcome=='secured_mark_raised' and kind=='secured': raise marker
        return 'same marker result'
    ledger._mark=mark
    event=SimpleNamespace(event_type=SimpleNamespace(value='tool_call_end'),data=dict(tool='ultima_work_research_write',agent='native_react',success=True,result='same',metadata=metadata))
    with p.observe_runtime_marks(ledger,journal,source),p.observe_writer(ledger,journal):
        ledger.close_enrollment(); assert f.nested.execute(path='research.md',content='synthetic') is f.result
        ledger.observe_navigation(event,caller_id=ledger._caller,binding_key=('r','s','t'))
        if outcome!='end_dropped':
            leaf=source._NativeResearchLeaf(); leaf.ledger=ledger
            transport=source._ResearchTransport(); transport.ledger=ledger
            view=source._ResearchEngineView(); view.ledger=ledger
            assert leaf.generate()=='same marker result' and transport.exchange()=='same marker result'
            if outcome=='secured_mark_raised':
                with pytest.raises(RuntimeError) as raised: view.generate()
                assert raised.value is marker
            else: assert view.generate()=='same marker result'
    summary=p.failure_summary(journal,ledger,{'status':'succeeded' if outcome=='secured_export_failure' else 'failed'},'export_after_first' if outcome=='secured_export_failure' else 'submission')
    if outcome=='secured_export_failure':
        assert summary['ack_attempted'] is summary['ack_admitted'] is summary['ack_verified'] is True
        assert summary['ack'] is True and summary['stage']=='export_after_first'
        assert len(calls)==3
    elif outcome=='end_dropped':
        assert summary['ack_attempted'] is summary['ack_admitted'] is summary['ack_verified'] is None
        assert summary['stage']=='failed_end' and summary['seal_cause']['sha256']==p.digest(b'Unlinked or failed END')
    else: assert summary['ack_verified'] is None and summary['ack_admitted'] is True


@pytest.mark.parametrize('unknown',[False,True])
def test_observe_writer_loss_first_seal_latched(unknown,writer_contract):
    f=writer_contract; p=f.p; journal=p.WriterJournal(); permit=dict(f.ledger._permit)
    first=object() if unknown else 'first seal reason'
    with p.observe_writer(f.ledger,journal):
        f.ledger.seal(first)
        assert f.ledger._permit is None
        f.ledger.seal('later seal reason')
    expected=None if unknown else dict(bytes=len(first.encode()),sha256=p.digest(first.encode()))
    assert journal.seal_cause==expected and journal.seal_observed is True
    assert journal.seal_identity=={name:permit[name] for name in ('report_call_id','dispatch_uuid','file_call_id','seq','generation')}
    seals=[row for row in journal.rows if row['kind']=='SEAL']
    assert len(seals)==2 and seals[0]['secondary'] is False and seals[1]['secondary'] is True
    assert seals[0]['identity']==journal.seal_identity and seals[1]['identity'] is None
    summary=p.failure_summary(journal,f.ledger,{'status':'failed'},'submission')
    assert summary['seal_identity']==journal.seal_identity and summary['seal_cause']==expected


@pytest.mark.parametrize('outcome',['no_end','dropped_end','no_ack','stage_spoof'])
def test_failure_strata_terminal_observed_absence(outcome,writer_contract):
    f=writer_contract; p=f.p; journal=p.WriterJournal(); ledger=f.ledger
    first={'status':'failed','error':'immutable original product failure'}; original=p.canonical(first)
    if outcome!='stage_spoof':
        metadata=dict(report_call_id=f.nested._report_parent[0],dispatch_uuid=f.nested._report_parent[1],
            file_call_id=f.nested._report_file_id,arguments={'path':'research.md'})
        ledger._expected={'name':'ultima_work_research_write'}
        ledger._staged[ledger._sequence]={'content':'same','metadata':metadata,'confirmed':False}
        def navigation(event,**kwargs):
            if outcome=='dropped_end': ledger.seal('lost original END'); return None
            ledger._staged[ledger._sequence]['confirmed']=True; ledger._runtime_events.append('retained'); ledger._permit=None
        ledger.observe_navigation=navigation
        with p.observe_writer(ledger,journal):
            ledger.close_enrollment(); assert f.nested.execute(path='research.md',content='safe') is f.result
            if outcome!='no_end':
                event=SimpleNamespace(event_type=SimpleNamespace(value='tool_call_end'),data=dict(tool='ultima_work_research_write',agent='native_react',success=True,result='same',metadata=metadata))
                ledger.observe_navigation(event,caller_id=ledger._caller,binding_key=('r','s','t'))
    summary=p.failure_summary(journal,ledger,first,'missing_end' if outcome=='stage_spoof' else 'submission')
    assert summary['stage']=={'no_end':'missing_end','dropped_end':'failed_end','no_ack':'ack_absent','stage_spoof':'not_reached'}[outcome]
    assert summary['ack_attempted'] is summary['ack_admitted'] is summary['ack_verified'] is None
    if outcome=='dropped_end':
        seal=next(row for row in journal.rows if row['kind']=='SEAL')
        assert summary['first_negative_order']==seal['order'] and summary['first_negative_at_ns']==seal['at_ns']
    elif outcome in ('no_end','no_ack'):
        assert summary['terminal_missing']==('writer_END' if outcome=='no_end' else 'ACK_SECURED')
        assert summary['first_negative_order'] is summary['first_negative_at_ns'] is None
    assert p.canonical(first)==original and summary['first_product_error']['sha256']==p.digest(first['error'].encode())


@pytest.mark.parametrize('raised',[False,True])
def test_observe_writer_loss_seal_atomic_original(raised,writer_contract):
    import threading
    f=writer_contract; p=f.p; ledger=f.ledger; journal=p.WriterJournal()
    start=threading.Event(); competitor_done=threading.Event(); calls=[]; result=object(); marker=RuntimeError('original seal failure')
    def original(reason):
        calls.append(reason)
        if reason=='A':
            owned=ledger._lock._is_owned(); start.set()
            if not owned: assert competitor_done.wait(2),'competitor did not acquire released seal lock'
        with ledger._lock:
            ledger.first_failure=ledger.first_failure or reason; ledger._permit=None; ledger._sealed=True
        if reason=='A' and raised: raise marker
        return result
    ledger.seal=original
    def competitor():
        if start.wait(2):
            original('B'); competitor_done.set()
    thread=threading.Thread(target=competitor); thread.start()
    try:
        with p.observe_writer(ledger,journal):
            if raised:
                with pytest.raises(RuntimeError) as caught: ledger.seal('A')
                assert caught.value is marker
            else: assert ledger.seal('A') is result
    finally:
        start.set(); thread.join(3)
    assert not thread.is_alive() and competitor_done.is_set() and calls.count('A')==calls.count('B')==1
    assert ledger.first_failure=='A' and journal.seal_cause['sha256']==p.digest(ledger.first_failure.encode())


@pytest.mark.parametrize('mode',['navigation_row_failure','journal_cap','ack_row_failure','open_window'])
def test_failure_strata_incomplete_observation_unknown(mode,writer_contract):
    f=writer_contract; p=f.p; ledger=f.ledger; journal=p.WriterJournal(); original_add=journal.add
    metadata=dict(report_call_id=f.nested._report_parent[0],dispatch_uuid=f.nested._report_parent[1],
        file_call_id=f.nested._report_file_id,arguments={'path':'research.md'})
    ledger._expected={'name':'ultima_work_research_write'}
    ledger._staged[ledger._sequence]={'content':'same','metadata':metadata,'confirmed':False}
    def navigation(event,**kwargs):
        ledger._staged[ledger._sequence]['confirmed']=True; ledger._runtime_events.append('retained'); ledger._permit=None
    ledger.observe_navigation=navigation; ledger._mark=lambda *args,**kwargs:None
    def add(kind,**fields):
        if (mode=='navigation_row_failure' and kind=='NAVIGATION') or (mode=='ack_row_failure' and kind=='ACK_PHASE'):
            raise OSError('diagnostic sink failed')
        return original_add(kind,**fields)
    journal.add=add; product={'status':'failed','error':'original first error'}; saved=p.canonical(product)
    with p.observe_writer(ledger,journal):
        ledger.close_enrollment(); assert f.nested.execute(path='research.md',content='safe') is f.result
        if mode=='journal_cap':
            ledger.seal('known first negative')
            while len(journal.rows)<256: journal.add('DIAGNOSTIC')
        if mode=='open_window':
            summary=p.failure_summary(journal,ledger,product,'submission')
        else:
            event=SimpleNamespace(event_type=SimpleNamespace(value='tool_call_end'),data=dict(tool='ultima_work_research_write',agent='native_react',success=True,result='same',metadata=metadata))
            ledger.observe_navigation(event,caller_id=ledger._caller,binding_key=('r','s','t'))
            if mode=='ack_row_failure':
                server=runtime_mark_server_double(); leaf=server._NativeResearchLeaf(); leaf.ledger=ledger
                with p.observe_runtime_marks(ledger,journal,server): leaf.generate()
    if mode!='open_window': summary=p.failure_summary(journal,ledger,product,'submission')
    assert summary['stage']=='unknown' and summary['terminal_missing'] is None and summary['observation_complete'] is False
    assert summary['ack_verified'] is None and p.canonical(product)==saved
    if mode=='journal_cap':
        first=next(row for row in journal.rows if row['kind']=='SEAL')
        assert summary['first_negative_order']==first['order'] and summary['first_negative_at_ns']==first['at_ns']


@pytest.mark.parametrize('bad',[None,'missing_pid','wrong_pid','creation','nonce','exit_bool','worker_exit','index_hash','expectations_hash',
    'missing_bootstrap','bool_bootstrap','denied_route','eager_dirty','unknown_paths','missing_counts','extra_counts','inference_mismatch',
    'metadata_budget','writer_unknown','late_observation','secondary','unclosed','late_worker_order',
    'ssrf_missing','ssrf_native','ssrf_float_count','ssrf_wrong_context','ssrf_phase_order'])
def test_observation_gate(bad):
    import uuid
    p=implementation()
    assert hasattr(p,'observation_gate'),'T5 closed candidate predicate missing'
    first=dict(format=1,status='candidate',run_id=str(uuid.uuid4()),entry_nonce=str(uuid.uuid4()),worker_pid=123,worker_creation_filetime=456,
        product_status='succeeded',first_product_sha256='a'*64,closed_index_sha256='b'*64,observations_sha256='c'*64,runtime_inputs_sha256='d'*64,
        work_returned_ns=10,cleanup_closed_ns=20,sealed_ns=30,counters=good_counter_fixture(),error_type=None,secondary_errors=[],released_members=[])
    observed=dict(run_id=first['run_id'],entry_nonce=first['entry_nonce'],worker_pid=123,worker_creation_filetime=456,python_exit_code=0,
        observed_at_ns=100,first_result_sha256='e'*64,closed_index_sha256='b'*64,expectations_sha256='c'*64,runtime_inputs_sha256='d'*64,protected_after_sha256='f'*64)
    hashes={key:observed[key] for key in ('first_result_sha256','closed_index_sha256','expectations_sha256','runtime_inputs_sha256')}
    previous=None
    if bad=='missing_pid': observed.pop('worker_pid')
    elif bad=='wrong_pid': observed['worker_pid']+=1
    elif bad=='creation': observed['worker_creation_filetime']+=1
    elif bad=='nonce': observed['entry_nonce']=str(uuid.uuid4())
    elif bad=='exit_bool': observed['python_exit_code']=False
    elif bad=='worker_exit': observed.pop('python_exit_code'); first['python_exit_code']=0
    elif bad=='index_hash': observed['closed_index_sha256']='a'*64
    elif bad=='expectations_hash': observed['expectations_sha256']='a'*64
    elif bad=='missing_bootstrap': first['counters']['bootstrap']=0
    elif bad=='bool_bootstrap': first['counters']['bootstrap']=True
    elif bad=='denied_route': first['counters']['native_refused']=1
    elif bad=='eager_dirty': first['counters']['eager_clean']=False
    elif bad=='unknown_paths': first['counters']['scope_clean']=None
    elif bad=='missing_counts': first['counters'].pop('sdk_GETs')
    elif bad=='extra_counts': first['counters']['unaccounted_path']=0
    elif bad=='inference_mismatch': first['counters']['sdk_inference_end']=4
    elif bad=='metadata_budget': first['counters']['research_reserved']=16
    elif bad=='writer_unknown': first['counters']['writer_successes']=None
    elif bad=='late_observation': previous=dict(observed,observed_at_ns=101)
    elif bad=='secondary': first['secondary_errors']=['OSError']
    elif bad=='unclosed': first['counters']['clients_closed']=False
    elif bad=='late_worker_order': first['work_returned_ns']=21
    elif bad=='ssrf_missing': first['counters'].pop('ssrf')
    elif bad=='ssrf_native': first['counters']['ssrf']['native_dns']=0
    elif bad=='ssrf_float_count': first['counters']['ssrf']['records'][1]['checker_entered']=1.0
    elif bad=='ssrf_wrong_context': first['counters']['ssrf']['context']='reader'
    elif bad=='ssrf_phase_order':
        rows=first['counters']['ssrf']['records']; rows[0],rows[-2]=rows[-2],rows[0]
    if bad is None: assert p.observation_gate(first,observed,hashes,expected_backend='python') is None
    else:
        with pytest.raises(ValueError): p.observation_gate(first,observed,hashes,previous,expected_backend='python')


@pytest.mark.parametrize('mode',['work_boundary','work_late','cleanup_boundary','cleanup_late','seal_boundary','seal_late'])
def test_observation_gate_worker_deadlines(mode,tmp_path,monkeypatch):
    exercise_worker_entry(mode,tmp_path,monkeypatch)


def test_observation_gate_submit_after_setup_deadline(tmp_path,monkeypatch):
    exercise_worker_entry('setup_expired',tmp_path,monkeypatch)


@pytest.mark.parametrize('argv',[[],['--runtime'],['--contracts','--runtime'],['--contracts','test_profile.py']])
def test_observation_gate_runner_arguments(argv,monkeypatch):
    path=HERE/'run_checks.py'
    assert path.exists(),'T5 fixed contract runner missing'
    spec=importlib.util.spec_from_file_location('offline_checks',path); runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    monkeypatch.setattr(runner.subprocess,'run',lambda *a,**k:pytest.fail('invalid argv spawned a child'))
    assert runner.main(argv)==2


@pytest.mark.parametrize('bad',[None,'missing','extra','duplicate','failed','dependency_drift','member_drift',
    'pytest_injection','python_injection','late_raw_hash_failure','parent_not_isolated'])
def test_observation_gate_runner_closed_suite(bad,tmp_path,monkeypatch):
    import xml.etree.ElementTree as ET
    path=HERE/'run_checks.py'; assert path.exists(),'T5 fixed contract runner missing'
    spec=importlib.util.spec_from_file_location('offline_checks',path); runner=importlib.util.module_from_spec(spec); spec.loader.exec_module(runner)
    package=tmp_path/'package'; package.mkdir(); dependency=tmp_path/'frozen'; dependency.write_bytes(b'frozen')
    members={}
    for name in ('profile.py','test_profile.py','run_checks.py','README.md'):
        (package/name).write_bytes(name.encode()); members[name]=__import__('hashlib').sha256(name.encode()).hexdigest()
    manifest=dict(runtime_released=False,files={str(dependency):__import__('hashlib').sha256(b'frozen').hexdigest()},members=members,
        test_ids=['test_profile.py::test_synthetic_contract'])
    (package/'manifest.json').write_text(json.dumps(manifest),encoding='utf8')
    monkeypatch.setattr(runner,'HERE',package); monkeypatch.setattr(runner,'EVIDENCE_ROOT',tmp_path/'code')
    monkeypatch.setattr(runner,'sys',SimpleNamespace(executable=str(runner.PY),version='synthetic parent Python',
        flags=SimpleNamespace(dont_write_bytecode=1,utf8_mode=1,optimize=0,isolated=0 if bad=='parent_not_isolated' else 1)))
    monkeypatch.setattr(runner,'load_profile',implementation)
    if bad=='pytest_injection':
        monkeypatch.setenv('PYTEST_ADDOPTS','-p injected_plugin --pyargs injected_tests')
        monkeypatch.setenv('PYTEST_PLUGINS','injected_plugin')
        (tmp_path/'conftest.py').write_text('raise RuntimeError("ancestor conftest must not execute")',encoding='utf8')
        (tmp_path/'pytest.ini').write_text('[pytest]\naddopts = -p injected_plugin\n',encoding='utf8')
    elif bad=='python_injection':
        monkeypatch.setenv('PYTHONPATH',str(tmp_path/'foreign'))
        monkeypatch.setenv('PYTHONHOME',str(tmp_path/'foreign'))
        monkeypatch.setenv('PYTHONUSERBASE',str(tmp_path/'foreign'))
    original_sha=runner.sha
    if bad=='late_raw_hash_failure':
        def digest(raw):
            if raw==b'synthetic offline child': raise OSError('late raw hash failure')
            return original_sha(raw)
        monkeypatch.setattr(runner,'sha',digest)
    calls=[]
    def child(argv,**kwargs):
        calls.append((argv,kwargs)); assert argv[:8]==[str(runner.PY),'-B','-X','utf8','-I','-m','pytest','-q']
        assert argv[8]=='test_profile.py' and kwargs['cwd']==package and kwargs['env']['PYTEST_DISABLE_PLUGIN_AUTOLOAD']=='1'
        if bad in ('pytest_injection','python_injection'):
            if bad=='python_injection': assert '-I' in argv,'Isolate user-site/startup and current-directory Python import paths'
            assert all(key not in kwargs['env'] for key in ('PYTEST_ADDOPTS','PYTEST_PLUGINS','PYTHONPATH','PYTHONHOME','PYTHONUSERBASE'))
            assert '--noconftest' in argv and '--import-mode=importlib' in argv
            config=Path(argv[argv.index('-c')+1]); assert config.parent==Path(next(a.split('=',1)[1] for a in argv if a.startswith('--junitxml='))).parent
            assert config.read_text(encoding='utf8')=='[pytest]\n'
            assert '--confcutdir='+str(package) in argv
            assert '--rootdir='+str(package) in argv
        junit=Path(next(a.split('=',1)[1] for a in argv if a.startswith('--junitxml=')))
        root=ET.Element('testsuites'); suite=ET.SubElement(root,'testsuite')
        if bad!='missing':
            case=ET.SubElement(suite,'testcase',classname='test_profile',name='test_synthetic_contract')
            if bad=='failed': ET.SubElement(case,'failure',message='synthetic')
        if bad in ('extra','duplicate'): ET.SubElement(suite,'testcase',classname='test_profile',name='test_extra' if bad=='extra' else 'test_synthetic_contract')
        ET.ElementTree(root).write(junit,encoding='utf8')
        if bad=='dependency_drift': dependency.write_bytes(b'drift')
        if bad=='member_drift': (package/'test_profile.py').write_bytes(b'drift')
        return SimpleNamespace(returncode=1 if bad=='failed' else 0,stdout=b'synthetic offline child',stderr=b'')
    monkeypatch.setattr(runner.subprocess,'run',child)
    code=runner.main(['--contracts'])
    assert code==(0 if bad in (None,'pytest_injection','python_injection') else 1) and len(calls)==(0 if bad=='parent_not_isolated' else 1)
    receipts=list((tmp_path/'code').glob('profile-preparation-*/receipt.json')); assert len(receipts)==1
    receipt=json.loads(receipts[0].read_bytes())
    assert receipt['original_profile_runs']==0 and receipt['expected_count']==(None if bad=='parent_not_isolated' else 1) and receipt['exit_code']==code


def test_observation_gate_parent_launch_isolated():
    text=(HERE/'README.md').read_text(encoding='utf8')
    command=next(line for line in text.splitlines() if line.startswith('& H:/') and 'run_checks.py' in line)
    assert 'python.exe -I -B -X utf8' in command,'The parent must isolate startup before running the script'


@pytest.mark.parametrize('bad',[None,'archive','version','tags','model'])
def test_guard_before_metadata_role(bad,tmp_path):
    p=implementation()
    assert hasattr(p,'metadata_inputs'),'Pinned mock metadata role decoder missing'
    archive=Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/candidate-fixwave1-covering/temp/test_v3_native_react_observati0/runtime-replay.json')
    identity=json.loads(archive.read_bytes())['wires'][0]['identity']
    # Only the approved metadata identity strings enter this new synthetic fixture.
    source={'wires':[{'identity':dict(identity),'response':'must not enter selected inputs'}]}
    if bad=='version': source['wires'][0]['identity']['version_response']+=' '
    elif bad=='tags': source['wires'][0]['identity']['tags_response']+=' '
    elif bad=='model': source['wires'][0]['identity']['local_manifest_sha256']='a'*64
    path=tmp_path/'metadata.json'; path.write_bytes(json.dumps(source).encode())
    pins={'metadata_archive_path':str(path),'files':{str(path):p.digest(path.read_bytes())}}
    if bad=='archive': path.write_bytes(b'{}')
    if bad is None:
        metadata=p.metadata_inputs(pins)
        assert set(metadata)=={'version','tags'} and all(type(value) is bytes for value in metadata.values())
        assert p.digest(metadata['version'])=='daac797f978a0cae19be6b37370789f092f91123d9afa5463481633a4cbe33c6'
        assert p.digest(metadata['tags'])=='15543e65c72332ba5590dcdc1955c033978a5f001984c965ce26104838565e11'
        assert 'must not enter' not in repr(metadata)
    else:
        with pytest.raises(ValueError): p.metadata_inputs(pins)


def test_observation_gate_sealed_package_inputs():
    p=implementation(); pins=p.read_pins(HERE/'manifest.json')
    assert pins['role']=='ORIGINAL_PROFILE_CODE_PREPARATION' and pins['runtime_released'] is False
    assert pins['model_digest']==p.MODEL_DIGEST and Path(pins['package_root'])==HERE
    assert set(pins['metadata'])=={'version','tags'} and pins['tags_bytes']==pins['metadata']['tags']
    assert pins['owner_origin']=='http://localhost:11434' and pins['research_origin']=='http://127.0.0.1:11434'
    assert pins['test_ids'] and len(set(pins['test_ids']))==len(pins['test_ids'])

@pytest.mark.parametrize('admission',[None,{}, {'verified':True}])
def test_guard_before_constructor_and_restore(admission,tmp_path):
    p=implementation()
    assert hasattr(p,'private_scope'), 'T1 private_scope missing'
    with pytest.raises((TypeError,ValueError)):
        with p.private_scope(tmp_path,{},admission):
            pytest.fail('self-certified admission exposed selected clients')

@pytest.mark.parametrize('event',['socket.connect','socket.__new__','socket.getaddrinfo','subprocess.Popen','os.system'])
def test_uncovered_selected_path_fails_closed(event):
    p=implementation()
    assert hasattr(p,'WorkerAudit'), 'T1 early worker audit missing'
    audit=p.WorkerAudit()
    with pytest.raises(ValueError): audit(event,())
    assert audit.denied=={event:1}
    assert audit.ordinary_http is None and audit.os_packets is None

def test_eager_default_client(tmp_path,monkeypatch):
    import httpx
    import sys
    p=implementation()
    assert hasattr(p,'own_ollama_types'), 'T1 eager type owner missing'
    pkg=tmp_path/'ollama'; pkg.mkdir()
    code='''import httpx
class Client:
    def __init__(self):
        self._client=httpx.Client(base_url='http://127.0.0.1:11434',follow_redirects=True)
    def close(self): self._client.close()
    def chat(self): return self._client.send(self._client.build_request('GET','/api/tags'))
    embed=chat
    pull=chat
_client=Client()
chat=_client.chat
embed=_client.embed
pull=_client.pull
for name in ('generate','embeddings','push','create','delete','list','copy','show','ps','web_search','web_fetch','systemone'):
    setattr(Client,name,Client.chat)
    globals()[name]=getattr(_client,name)
'''
    path=pkg/'__init__.py'; path.write_text(code,encoding='utf8')
    monkeypatch.syspath_prepend(str(tmp_path))
    import hashlib
    pins={'files':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()},'ollama_origin':str(path)}
    original=httpx.Client
    audit={}
    try:
        with pytest.raises(ValueError,match='eager'):
            with p.own_ollama_types(pins,audit) as state:
                assert state['owner']._client.is_closed
                assert state['import_sends']==0
                retained=state['module'].chat
                with pytest.raises(ValueError): retained()
                assert state['refused_sends']==1
        assert httpx.Client is original
        assert audit['metadata_charged']==0
        with pytest.raises(ValueError):
            with p.own_ollama_types(pins,{}): pass
    finally:
        for name in list(sys.modules):
            if name=='ollama' or name.startswith('ollama.'): sys.modules.pop(name,None)

def test_guard_before_constructor_and_restore_owner():
    import httpx
    p=implementation()
    assert hasattr(p,'_guard_client'), 'T1 real instance boundary missing'
    budget=p.MetadataBudget(); calls=[]; counters={}
    def handler(request):
        calls.append((request.method,request.url.path))
        return httpx.Response(200,stream=httpx.ByteStream(b'{"models":[]}'))
    original=httpx.Client
    with httpx.Client(base_url='http://localhost:11434',transport=httpx.MockTransport(handler),trust_env=False,follow_redirects=False) as client:
        assert p._guard_client(client,'owner',budget,handler,counters) is client
        assert client.get('/api/tags').status_code==200
        with pytest.raises(ValueError): client.get('/api/tags')
        with pytest.raises(ValueError): client.post('/api/chat')
    assert calls==[('GET','/api/tags')]
    assert budget.bootstrap==1 and counters['send_attempts']==1 and httpx.Client is original

@pytest.fixture(scope='session',autouse=True)
def interpreter_receipt(record_testsuite_property):
    import sys
    import importlib.metadata
    record_testsuite_property('interpreter',sys.executable)
    record_testsuite_property('python',sys.version)
    record_testsuite_property('import_path',json.dumps(sys.path,ensure_ascii=False))
    for package in ('pytest','httpx','openjarvis'):
        record_testsuite_property(package,importlib.metadata.version(package))

@pytest.mark.parametrize('failure',[None,'native','engine','server','inside','owner_bad_origin',
    'caught_denial','close','inside_close','guard_install'])
def test_real_factory_guard_before_constructor_and_restore_installers(failure,tmp_path,monkeypatch):
    from contextlib import contextmanager
    import hashlib
    import httpx
    import sys
    p=implementation()
    assert hasattr(p,'private_scope'), 'T1 scope missing'
    events=[]; clients=[]; origin='http://localhost:11434'
    case=tmp_path/'case'; case.mkdir()
    adapter_path=tmp_path/'adapter.py'
    adapter_path.write_text('def check_inputs(): pass\ndef check_import_origins(): pass\n',encoding='utf8')
    native=SimpleNamespace(load_system_prompt_override=object())
    engine=owner_constructor_double()
    server=SimpleNamespace(_jars=None,_research_client=object(),_isolated=False,_runtime_root=tmp_path/'before')
    initial_runtime=server._runtime_root; primary=RuntimeError('first product cause'); close_error=OSError('secondary')
    observed={}; guarded_clients=[]
    saved_guard=p._guard_client
    def installing_guard(client,*args,**kwargs):
        guarded_clients.append(client)
        if failure=='guard_install': raise primary
        return saved_guard(client,*args,**kwargs)
    monkeypatch.setattr(p,'_guard_client',installing_guard)
    original_loader=native.load_system_prompt_override
    original_research=server._research_client
    class Controls(p.RootControls):
        def admit(self,folder,pins): events.append('root'); return admission_double(p,folder,pins)
    saved_admission=p.validate_admission
    def validated(*args): events.append('shape'); return saved_admission(*args)
    monkeypatch.setattr(p,'validate_admission',validated)
    monkeypatch.setattr(p,'check_persona',lambda *args: {'synthetic':True})
    monkeypatch.setattr(sys,'addaudithook',lambda hook:events.append('audit'))
    @contextmanager
    def eager(pins,audit):
        events.append('eager')
        yield {}
    monkeypatch.setattr(p,'own_ollama_types',eager)
    @contextmanager
    def browser(*args): yield {'refused':0}
    monkeypatch.setattr(p,'browser_scope',browser)
    original_import=p.importlib.import_module
    def imported(name):
        if name=='httpx': return httpx
        for label,obj in [('native',native),('engine',engine),('server',server)]:
            if name=={'native':'openjarvis.agents.native_react','engine':'openjarvis.engine.ollama','server':'src.brain.agent_server'}[label]:
                events.append(label)
                if failure==label: raise RuntimeError(label)
                if label=='server':
                    for key,leaf in (('OPENJARVIS_HOME','home'),('XDG_CACHE_HOME','cache'),('TMP','temp'),('TEMP','temp'),('TMPDIR','temp')):
                        assert p.os.environ.get(key)==str(case/leaf) and (case/leaf).is_dir()
                    native.load_system_prompt_override=object()
                    raw=engine.OllamaEngine(host='http://127.0.0.1:11434' if failure=='owner_bad_origin' else None)
                    client=raw._client
                    clients.append(client)
                    assert client.get('/api/tags').status_code==200
                return obj
        return original_import(name)
    monkeypatch.setattr(p.importlib,'import_module',imported)
    pins={'files':{str(adapter_path):hashlib.sha256(adapter_path.read_bytes()).hexdigest()},
          'candidate_root':str(tmp_path),'adapter':str(adapter_path),'research_origin':'http://127.0.0.1:11434',
          'tags_bytes':b'{"models":[]}','metadata':{},'owner_origin':origin,
          'package_root':str(tmp_path),'import_path':list(sys.path),'model_digest':p.MODEL_DIGEST}
    pins.update({key:'a'*64 for key in ('profile_manifest_sha256','candidate_manifest_sha256','corpus_sha256')})
    monkeypatch.chdir(tmp_path)
    for key in list(p.os.environ):
        if key.upper() in ('OLLAMA_HOST','OLLAMA_API_KEY','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP',
                'OPENJARVIS_HOME','XDG_CACHE_HOME','TMP','TEMP','TMPDIR','OPENJARVIS_SSRF_FAIL_OPEN') or key.upper().endswith('_PROXY'):
            monkeypatch.delenv(key)
    bootstrap_environment=dict(p.os.environ)
    def perform():
        with p.private_scope(case,pins,Controls()) as scope:
            observed['scope']=scope
            assert scope['server'] is server
            assert server._research_client is not original_research
            research_client=server._research_client()
            assert (research_client.base_url.scheme,research_client.base_url.host,research_client.base_url.port,research_client.base_url.path,research_client.base_url.query,research_client.base_url.fragment)==('http','127.0.0.1',11434,'/',b'','')
            assert (clients[0].base_url.scheme,clients[0].base_url.host,clients[0].base_url.port,clients[0].base_url.path,clients[0].base_url.query,clients[0].base_url.fragment)==('http','localhost',11434,'/',b'','')
            assert research_client is not clients[0] and research_client._transport is not clients[0]._transport
            assert scope['budget'].bootstrap==1 and scope['budget'].research==0
            assert events.index('audit')<events.index('server')
            if failure in ('close','inside_close'):
                original_close=clients[0].close
                def broken_close(): original_close(); raise close_error
                clients[0].close=broken_close
            if failure=='caught_denial':
                with pytest.raises(ValueError): clients[0].get('/api/pull')
            if failure=='inside_close': raise primary
            if failure=='inside': raise RuntimeError('inside')
    if failure is None: perform()
    elif failure=='owner_bad_origin':
        with pytest.raises(ValueError,match='Owner constructor contract'): perform()
    elif failure in ('caught_denial','close'):
        with pytest.raises(ValueError): perform()
        assert observed['scope']['clean'] is False
    elif failure in ('inside_close','guard_install'):
        with pytest.raises(RuntimeError) as raised: perform()
        assert raised.value is primary
        if failure=='inside_close':
            assert observed['scope']['clean'] is False
            assert observed['scope']['cleanup']['errors']==['OSError']
    else:
        with pytest.raises(RuntimeError,match=failure): perform()
    assert native.load_system_prompt_override is original_loader
    assert engine.httpx is httpx and server._research_client is original_research
    assert server._isolated is False and server._runtime_root is initial_runtime
    assert all(client.is_closed for client in guarded_clients)
    assert dict(p.os.environ)==bootstrap_environment
    assert events[:4]==['root','shape','audit','eager']

@pytest.mark.parametrize('change',[None,'body','mime','order','query','old_request_id'])
def test_original_input_binding(change):
    p=implementation()
    assert hasattr(p,'original_inputs'),'T2 original input binder missing'
    root=HERE.parent.parent
    corpus_path=root/'source6-native-reference/controlled-corpus-inputs/corpus.json'
    readback_path=root/'navigation-source10-validation-20261102/original-controlled-corpus-readback.json'
    corpus=json.loads(corpus_path.read_text(encoding='utf8'))
    readback=json.loads(readback_path.read_text(encoding='utf8'))
    pins={'corpus_path':str(corpus_path),'corpus_sha256':'9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002',
          'readback_path':str(readback_path),'readback_sha256':'7b1410b78d53e06ba865018a7360df19601aaf46a1bfc250650062657e632035'}
    changed=copy.deepcopy(corpus)
    if change=='body':
        text=changed['sources'][0]['body']; changed['sources'][0]['body']=('X' if text[0]!='X' else 'Y')+text[1:]
    if change=='mime': changed['sources'][0]['content_type']='text/html'
    if change=='order': changed['sources'][0],changed['sources'][1]=changed['sources'][1],changed['sources'][0]
    if change=='query': changed['query']='X'+changed['query'][1:]
    if change=='old_request_id': changed['request_id']='44cdf22a-7f2d-486d-84ef-ac758fe990cc'
    adapter=SimpleNamespace(corpus=lambda:changed)
    if change:
        with pytest.raises(ValueError): p.original_inputs(adapter,pins)
    else:
        value=p.original_inputs(adapter,pins)
        assert len(value['query'].encode('utf8'))==774
        assert [len(s['body'].encode('utf8')) for s in value['sources']]==[7236,3252,4643,13559]

@pytest.mark.parametrize('value',['1','TRUE','YeS','','unexpected'])
def test_ssrf_baseline_present(value):
    p=implementation()
    assert hasattr(p,'check_ssrf_baseline'),'T2 SSRF baseline missing'
    env={'openjarvis_ssrf_fail_open':value}
    before=dict(env)
    with pytest.raises(ValueError): p.check_ssrf_baseline(env,expected_backend='python',pins={})
    assert env==before

def test_real_factory_contract(tmp_path,monkeypatch):
    import sys
    from types import ModuleType
    p=implementation()
    assert hasattr(p,'make_service'),'T2 service composition missing'
    events=[]; owner=object(); callback=object(); preparer=object()
    server=SimpleNamespace(_run_work_agent=callback,_prepare_research_navigation=preparer)
    def factory(): events.append('get_jarvis'); return owner
    server.get_jarvis=factory
    service_module=ModuleType('src.brain.work_service'); browser_module=ModuleType('src.brain.browser.channel')
    browser=object(); browser_module.BrowserChannel=lambda:browser
    def service(*args,**kwargs):
        events.append((args,kwargs)); return owner
    service_module.WorkService=service
    monkeypatch.setitem(sys.modules,'src.brain.work_service',service_module)
    monkeypatch.setitem(sys.modules,'src.brain.browser.channel',browser_module)
    scope={'server':server,'owner':None}
    assert p.make_service(scope,tmp_path) is owner
    assert events==['get_jarvis',((tmp_path/'outputs',),dict(runner=callback,browser_channel=browser,research_preparer=preparer))]
    assert scope['owner'] is owner

@pytest.mark.parametrize('outcome',['blocked','none','raised'])
@pytest.mark.parametrize('context',['worker','reader'])
def test_ssrf_baseline_absent_and_unchanged_verdict(context,outcome,tmp_path,monkeypatch):
    import hashlib
    import socket
    import sys
    from types import ModuleType
    p=implementation()
    assert hasattr(p,'guarded_ssrf'),'T2 transparent SSRF boundary missing'
    site=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages')
    source=site/'openjarvis/security/ssrf.py'
    spec=importlib.util.spec_from_file_location('synthetic_ssrf_'+context,source)
    ssrf=importlib.util.module_from_spec(spec); spec.loader.exec_module(ssrf)
    bridge=ModuleType('openjarvis._rust_bridge'); bridge.__file__=str(site/'openjarvis/_rust_bridge.py'); bridge.RUST_AVAILABLE=False
    bridge.get_rust_module=lambda: (_ for _ in ()).throw(AssertionError('Unexpected synthetic Rust branch'))
    sdk_http=ModuleType('openjarvis.tools.http_request'); sdk_http.check_ssrf=ssrf.check_ssrf
    monkeypatch.setitem(sys.modules,'openjarvis._rust_bridge',bridge)
    monkeypatch.setitem(sys.modules,'openjarvis.tools.http_request',sdk_http)
    original=ssrf.check_ssrf; calls=[]; error=RuntimeError('synthetic resolver failure')
    def resolver(*args,**kwargs):
        calls.append((args,kwargs))
        if outcome=='raised': raise error
        if outcome=='none': return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))]
        raise socket.gaierror('synthetic no-DNS')
    monkeypatch.setattr(socket,'getaddrinfo',resolver)
    pins={'files':{str(Path(m.__file__).resolve()):hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (bridge,ssrf)},
          '_rust_bridge':bridge,'_ssrf_module':ssrf,'_check_ssrf_original':original,'_python_ssrf_original':ssrf._check_ssrf_python}
    before=dict(__import__('os').environ)
    result=p.check_ssrf_baseline({},expected_backend='python',pins=pins)
    assert result=={'fail_open_present':False,'backend':'python','native_dns':None,'native_cache':None,'packets':None}
    counts={}; url='https://raw.githubusercontent.com/synthetic/source'
    with p.guarded_ssrf(pins,{'ssrf_backend':'python'},[url],counts) as checked:
        with pytest.raises(ValueError): checked(url+'-unadmitted')
        assert calls==[]
        if outcome=='raised':
            with pytest.raises(RuntimeError) as caught: checked(url)
            assert caught.value is error
        elif outcome=='none': assert checked(url) is None
        else: assert checked(url)=='Could not resolve host (blocked, fail-closed): raw.githubusercontent.com'
        assert sdk_http.check_ssrf is checked
        with pytest.raises(ValueError): socket.getaddrinfo('raw.githubusercontent.com',443)
    expected_counts={'entered':1,'python_resolver':1,'refused':2}
    if outcome=='raised': expected_counts['raised']=1
    else: expected_counts.update(returned=1,**({'none':1} if outcome=='none' else {'rejected':1}))
    assert {key:value for key,value in counts.items() if key!='observations'}==expected_counts
    assert hasattr(p,'ssrf_receipt'),'R16 bounded SSRF context/phase/source receipt missing'
    counts.update(native_dns=0,native_cache=0,packets=0)
    receipt=p.ssrf_receipt(counts,context)
    assert receipt['context']==context and receipt['native_dns'] is receipt['native_cache'] is receipt['packets'] is None
    rows=receipt['records']; lookup=next(row for row in rows if row['source_index']==1)
    assert lookup['phase']=='lookup' and lookup['backend']=='python' and lookup['source_url_sha256']==p.digest(url.encode())
    assert lookup['checker_entered']==1 and lookup['python_resolver_entries']==1
    assert lookup['returned_none']==(1 if outcome=='none' else 0)
    assert lookup['returned_rejected']==(1 if outcome=='blocked' else 0) and lookup['checker_raised']==(1 if outcome=='raised' else 0)
    assert [row['phase'] for row in rows if row['phase']!='lookup']==['entry','resolver','close','restored']
    assert all(row['baseline_passed'] is True for row in rows if row['phase'] in ('entry','close','restored'))
    assert sdk_http.check_ssrf is original and ssrf.check_ssrf is original and socket.getaddrinfo is resolver
    assert dict(__import__('os').environ)==before

def test_real_factory_actual_source_default_origin(tmp_path,monkeypatch):
    """Executing pinned constructor/selection source with synthetic dependencies
    catches silently normalizing the actual default owner origin to research URL.
    """
    import ast
    import os
    from types import ModuleType
    import sys
    site=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages/openjarvis')
    engine_tree=ast.parse((site/'engine/ollama.py').read_text(encoding='utf8'))
    cls=next(n for n in engine_tree.body if isinstance(n,ast.ClassDef) and n.name=='OllamaEngine')
    init=next(n for n in cls.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    default=next(n.value.value for n in cls.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='_DEFAULT_HOST' for t in n.targets))
    calls=[]
    namespace={'httpx':SimpleNamespace(Client=lambda **kwargs:calls.append(kwargs) or object()),'os':SimpleNamespace(environ={})}
    exec(compile(ast.Module(body=[init],type_ignores=[]),str(site/'engine/ollama.py'),'exec'),namespace)
    Engine=type('SelectedEngine',(),{'_DEFAULT_HOST':default,'__init__':namespace['__init__']})
    discovery=ast.parse((site/'engine/_discovery.py').read_text(encoding='utf8'))
    make=next(n for n in discovery.body if isinstance(n,ast.FunctionDef) and n.name=='_make_engine')
    env={'EngineRegistry':SimpleNamespace(get=lambda name:Engine),'_HOST_MAP':{'ollama':'ollama_host'},
         'JarvisConfig':object,'InferenceEngine':object}
    exec(compile(ast.Module(body=[make],type_ignores=[]),str(site/'engine/_discovery.py'),'exec'),env)
    result=env['_make_engine']('ollama',SimpleNamespace(engine=SimpleNamespace(ollama_host='')))
    assert result._host=='http://localhost:11434'
    assert calls==[{'base_url':'http://localhost:11434','timeout':1800.0}]
    assert result._host!='http://127.0.0.1:11434'

def test_real_factory_source_get_jarvis_untouched_arguments(tmp_path,monkeypatch):
    import ast
    import sys
    from dataclasses import dataclass,field
    from types import ModuleType
    source=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/agent_server.py')
    tree=ast.parse(source.read_text(encoding='utf8'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='get_jarvis')
    @dataclass
    class Flag: enabled: bool=True
    @dataclass
    class Agent:
        context_from_memory: bool=True
        max_turns: int=10
        system_prompt: str=''
        system_prompt_path: str=''
    @dataclass
    class Security:
        enabled: bool=True
        mode: str='redact'
        secret_scanner: bool=True
        pii_scanner: bool=True
        scan_input: bool=True
        scan_output: bool=True
        rate_limit_enabled: bool=True
        audit_log_path: str='inherited/audit.db'
    @dataclass
    class Config:
        telemetry: Flag=field(default_factory=Flag)
        analytics: Flag=field(default_factory=Flag)
        agent: Agent=field(default_factory=Agent)
        security: Security=field(default_factory=Security)
    config_module=ModuleType('openjarvis.core.config'); config_module.JarvisConfig=Config
    monkeypatch.setitem(sys.modules,'openjarvis.core.config',config_module)
    calls=[]; instance=object(); registered=[]
    def jarvis(**kwargs): calls.append(kwargs); return instance
    namespace={'_jars':None,'_isolated':True,'_runtime_root':tmp_path,'Jarvis':jarvis,
               'ENGINE_KEY':'ollama','MODEL':'qwen3-8b-uncensored','_ensure_tools_registered':lambda:registered.append(True)}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),namespace)
    factory=namespace['get_jarvis']
    assert factory() is instance and factory() is instance
    assert registered==[True] and len(calls)==1
    assert set(calls[0])=={'config','engine_key','model'}
    assert calls[0]['engine_key']=='ollama' and calls[0]['model']=='qwen3-8b-uncensored'
    conf=calls[0]['config']
    assert conf.telemetry.enabled is False and conf.analytics.enabled is False and conf.agent.context_from_memory is False
    assert conf._config_dir==tmp_path and conf.security.audit_log_path==str(tmp_path/'sdk-security-audit_log_path')
    assert conf.agent.max_turns==10 and conf.agent.system_prompt==''
    assert conf.security.mode=='redact' and all(getattr(conf.security,n) is True for n in
        ('enabled','secret_scanner','pii_scanner','scan_input','scan_output','rate_limit_enabled'))

@pytest.mark.parametrize('mode',['localhost','127','other_host','scanner_order','missing_rate','missing_audit','capability','missing_input'])
def test_real_factory_source_security_wrappers(mode,monkeypatch):
    import ast
    import sys
    from types import ModuleType
    source=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/agent_server.py')
    tree=ast.parse(source.read_text(encoding='utf8'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_checked_research_security')
    Engine=type('OllamaEngine',(),{}); Guard=type('GuardrailsEngine',(),{}); Instrument=type('InstrumentedEngine',(),{})
    Secret=type('SecretScanner',(),{}); PII=type('PIIScanner',(),{})
    for name,attrs in {
        'openjarvis.engine.ollama':{'OllamaEngine':Engine},
        'openjarvis.security.guardrails':{'GuardrailsEngine':Guard},
        'openjarvis.security.scanner':{'SecretScanner':Secret,'PIIScanner':PII},
        'openjarvis.telemetry.instrumented_engine':{'InstrumentedEngine':Instrument},
        'src.brain.work_navigation':{'make_scan_policy':lambda scanners,mode:(tuple(type(s).__name__ for s in scanners),mode)},
    }.items():
        module=ModuleType(name); module.__dict__.update(attrs); monkeypatch.setitem(sys.modules,name,module)
    raw=Engine(); raw._host='http://localhost:11434' if mode!='127' else 'http://127.0.0.1:11434'
    if mode=='other_host': raw._host='http://elsewhere.invalid:11434'
    raw._client=SimpleNamespace(base_url=raw._host+'/')
    bus=object(); guard=Guard(); guard._engine=raw; guard._bus=bus
    guard._scanners=[Secret(),PII()]; guard._scan_input=True; guard._scan_output=True; guard._mode=SimpleNamespace(value='redact')
    outer=Instrument(); outer._inner=guard; outer._bus=bus
    conf=SimpleNamespace(enabled=True,secret_scanner=True,pii_scanner=True,scan_input=True,scan_output=True,
                         mode='redact',rate_limit_enabled=True,capabilities=SimpleNamespace(enabled=False))
    owner=SimpleNamespace(_engine=outer,_bus=bus,config=SimpleNamespace(security=conf),_audit_logger=object(),
                          _capability_policy=None,_rate_limiter=object())
    if mode=='scanner_order': guard._scanners.reverse()
    if mode=='missing_rate': owner._rate_limiter=None
    if mode=='missing_audit': owner._audit_logger=None
    if mode=='capability': conf.capabilities.enabled=True
    if mode=='missing_input': guard._scan_input=False
    env={'_RESEARCH_ORIGIN':'http://127.0.0.1:11434','os':SimpleNamespace(environ={}), '__package__':'src.brain'}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),env)
    if mode in ('localhost','127'):
        assert env['_checked_research_security'](owner)==(('SecretScanner','PIIScanner'),'redact')
    else:
        with pytest.raises(ValueError): env['_checked_research_security'](owner)

@pytest.mark.parametrize('change',[None,'persona_byte','template_byte','second_persona','conflicting_loader'])
def test_real_factory_persona_source_assembly(change,monkeypatch):
    import ast
    import __future__
    import hashlib
    import re
    import sys
    from types import ModuleType
    p=implementation()
    assert hasattr(p,'check_persona'),'T2 original persona verifier missing'
    root=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent')
    source=root/'src/brain/agent_server.py'
    tree=ast.parse(source.read_text(encoding='utf8'))
    names={'_read_required_prompt','_load_mainbrain_system_prompt','_install_mainbrain_system_prompt'}
    funcs=[n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name in names]
    sdk=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages/openjarvis/agents/native_react.py')
    sdk_tree=ast.parse(sdk.read_text(encoding='utf8'))
    template=next(n.value.value for n in sdk_tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='REACT_SYSTEM_PROMPT' for t in n.targets))
    native=ModuleType('openjarvis.agents.native_react'); native.REACT_SYSTEM_PROMPT=template
    original=lambda name:None; native.load_system_prompt_override=original
    klass=next(n for n in sdk_tree.body if isinstance(n,ast.ClassDef) and n.name=='NativeReActAgent')
    init=next(n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name=='__init__')
    init_env={}
    exec(compile(ast.Module(body=[init],type_ignores=[]),str(sdk),'exec',flags=__future__.annotations.compiler_flag),init_env)
    native.NativeReActAgent=type('NativeReActAgent',(),{'__init__':init_env['__init__']})
    agents=ModuleType('openjarvis.agents'); agents.native_react=native
    monkeypatch.setitem(sys.modules,'openjarvis.agents',agents)
    monkeypatch.setitem(sys.modules,'openjarvis.agents.native_react',native)
    env={'Path':Path,'re':re,'JARVIS_PERSONA_PATH':root/'libs/base/openjarvis/configs/openjarvis/prompts/personas/jarvis.md',
         'MAINBRAIN_RULES_PATH':root/'docs/specs/mainbrain-rules-baseline.md'}
    exec(compile(ast.Module(body=funcs,type_ignores=[]),str(source),'exec'),env)
    assembled=env['_load_mainbrain_system_prompt']()
    assert len(assembled.encode('utf8'))==2479
    assert hashlib.sha256(assembled.encode('utf8')).hexdigest()=='4b7f250424db22e5b9f14ec9f28051c7633dbf207ab4f7a3a1c52ace0d3ed357'
    env['MAINBRAIN_SYSTEM_PROMPT']=assembled
    full=env['_install_mainbrain_system_prompt']()
    server=SimpleNamespace(MAINBRAIN_SYSTEM_PROMPT=assembled,NATIVE_REACT_SYSTEM_PROMPT=full)
    try:
        if change=='persona_byte': server.MAINBRAIN_SYSTEM_PROMPT='X'+assembled[1:]
        if change=='template_byte': native.REACT_SYSTEM_PROMPT='X'+template[1:]
        if change=='second_persona': server.NATIVE_REACT_SYSTEM_PROMPT+='\n\n'+assembled
        if change=='conflicting_loader': native.load_system_prompt_override=lambda name:'different'
        if change:
            with pytest.raises(ValueError): p.check_persona(server,native)
        else:
            result=p.check_persona(server,native)
            assert result['persona_bytes']==2479 and result['template_sha256']=='a062f71243cd4986a2f2034cf3946912196fd4f4499394815cb0d3a1c522579b'
            native.load_few_shot_exemplars=lambda name:None
            stubs=ModuleType('openjarvis.tools._stubs')
            stubs.build_tool_descriptions=lambda tools:'Synthetic tool descriptions'
            descriptions=ModuleType('openjarvis.tools.description_loader')
            descriptions.get_tool_description_override=lambda name:None
            monkeypatch.setitem(sys.modules,'openjarvis.tools._stubs',stubs)
            monkeypatch.setitem(sys.modules,'openjarvis.tools.description_loader',descriptions)
            view=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='_ResearchEngineView')
            system=next(n for n in view.body if isinstance(n,ast.FunctionDef) and n.name=='_system')
            runtime=dict(MAINBRAIN_SYSTEM_PROMPT=assembled,NATIVE_REACT_SYSTEM_PROMPT=full)
            exec(compile(ast.Module(body=[system],type_ignores=[]),str(source),'exec'),runtime)
            fake_view=SimpleNamespace(ledger=SimpleNamespace(_enrolled={
                'ultima_work_research_inspect':object(),'ultima_work_research_write':object()}))
            original_system,secured_system=runtime['_system'](fake_view)
            assert original_system.count(assembled)==secured_system.count(assembled)==1
            assert '# Using Skills' in original_system and '# Using Skills' in secured_system
            assert 'Synthetic tool descriptions' in original_system
            assert original_system!=secured_system
    finally:
        native.load_system_prompt_override=original

def browser_doubles(monkeypatch):
    """Real producer/candidate source around synthetic SDK execution dependencies."""
    import ast
    import __future__
    import hashlib
    import socket
    import sys
    from datetime import datetime,timezone
    from types import ModuleType
    p=implementation(); root=HERE.parent.parent
    corpus=json.loads((root/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_text(encoding='utf8'))
    site=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages')
    ddgs=ModuleType('ddgs'); ddgs.DDGS=object
    monkeypatch.setitem(sys.modules,'ddgs',ddgs)
    ssrf_path=site/'openjarvis/security/ssrf.py'
    spec=importlib.util.spec_from_file_location('synthetic_browser_ssrf',ssrf_path)
    ssrf=importlib.util.module_from_spec(spec); spec.loader.exec_module(ssrf)
    bridge=ModuleType('openjarvis._rust_bridge'); bridge.__file__=str(site/'openjarvis/_rust_bridge.py')
    bridge.RUST_AVAILABLE=False; bridge.get_rust_module=lambda:None
    monkeypatch.setitem(sys.modules,'openjarvis._rust_bridge',bridge)
    monkeypatch.setitem(sys.modules,'openjarvis.security.ssrf',ssrf)
    dns=[]
    def normal_resolver(*args,**kwargs):
        dns.append((args,kwargs)); return [(socket.AF_INET,socket.SOCK_STREAM,6,'',('93.184.216.34',443))]
    monkeypatch.setattr(socket,'getaddrinfo',normal_resolver)
    http=ModuleType('openjarvis.tools.http_request'); http.check_ssrf=ssrf.check_ssrf
    search=ModuleType('openjarvis.tools.web_search')
    import httpx
    calls=[]
    class Http:
        def _request_following_redirects(self,method,url,**kwargs):
            return httpx.request(method,url,follow_redirects=False,**kwargs)
        def execute(self,**params):
            calls.append(('http',params))
            reason=http.check_ssrf(params['url'])
            if reason: raise ValueError(reason)
            response=self._request_following_redirects(params['method'],params['url'],headers=params['headers'],timeout=params['timeout'])
            return SimpleNamespace(success=True,content=response.text,metadata=dict(status_code=response.status_code,content_type=response.headers['content-type'],truncated=False))
    http.HttpRequestTool=Http
    search_tree=ast.parse((site/'openjarvis/tools/web_search.py').read_text(encoding='utf8'))
    search_class=next(n for n in search_tree.body if isinstance(n,ast.ClassDef) and n.name=='WebSearchTool')
    selected=[n for n in search_class.body if isinstance(n,ast.FunctionDef) and n.name in ('_extract_url','_duckduckgo_search')]
    env={}; exec(compile(ast.Module(body=selected,type_ignores=[]),str(site/'openjarvis/tools/web_search.py'),'exec',flags=__future__.annotations.compiler_flag),env)
    class Search:
        _extract_url=env['_extract_url']
        _duckduckgo_search=env['_duckduckgo_search']
        def __init__(self,*,engine): self._engine=engine
        def execute(self,**params):
            calls.append(('search',params))
            return SimpleNamespace(success=True,content=self._duckduckgo_search(params['query'],params['max_results']))
    search.WebSearchTool=Search
    monkeypatch.setitem(sys.modules,'openjarvis.tools.http_request',http)
    monkeypatch.setitem(sys.modules,'openjarvis.tools.web_search',search)
    adapter_path=binding_adapter().LEGACY; tree=ast.parse(adapter_path.read_text(encoding='utf8'))
    install=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='install_browser_fixture')
    env={'corpus':lambda:corpus,'socket':socket,'require':p.require}
    exec(compile(ast.Module(body=[install],type_ignores=[]),str(adapter_path),'exec'),env)
    adapter=SimpleNamespace(corpus=lambda:copy.deepcopy(corpus),install_browser_fixture=env['install_browser_fixture'])
    channel_path=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/browser/channel.py')
    tree=ast.parse(channel_path.read_text(encoding='utf8'))
    selected=[n for n in tree.body if isinstance(n,(ast.FunctionDef,ast.ClassDef)) and n.name in ('_now_iso','BrowserChannel')]
    class Gate:
        def __init__(self,*args): pass
        def allow(self,*args): return True,'allowed'
    env={'Path':Path,'RedlineGate':Gate,'datetime':datetime,'timezone':timezone,'json':json}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(channel_path),'exec',flags=__future__.annotations.compiler_flag),env)
    pins={'corpus_path':str(root/'source6-native-reference/controlled-corpus-inputs/corpus.json'),
        'corpus_sha256':'9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002',
        'readback_path':str(root/'navigation-source10-validation-20261102/original-controlled-corpus-readback.json'),
        'readback_sha256':'7b1410b78d53e06ba865018a7360df19601aaf46a1bfc250650062657e632035',
        'files':{str(Path(m.__file__).resolve()):hashlib.sha256(Path(m.__file__).read_bytes()).hexdigest() for m in (bridge,ssrf)},
        '_rust_bridge':bridge,'_ssrf_module':ssrf,'_check_ssrf_original':ssrf.check_ssrf,'_python_ssrf_original':ssrf._check_ssrf_python}
    return p,dict(adapter=adapter,grant={'ssrf_backend':'python'},counters={}),pins,env['BrowserChannel'],calls,dns,http,search,ddgs,normal_resolver

@pytest.mark.parametrize('bad',[None,'url_search','empty_headers','fifth_path','other_host','unscoped_dns','search_again','GET_again'])
def test_real_factory_browser_resolver_alias(bad,monkeypatch):
    import httpx
    import socket
    p,scope,pins,Browser,calls,dns,http,search,ddgs,resolver=browser_doubles(monkeypatch)
    assert hasattr(p,'browser_scope'),'T2 browser fixture boundary missing'
    saved=(httpx.request,ddgs.DDGS,socket.getaddrinfo,http.HttpRequestTool.execute,search.WebSearchTool.execute,http.check_ssrf)
    with p.browser_scope(scope,pins) as state:
        browser=Browser()
        urls=state['urls']; query=state['search_query']
        if bad in ('url_search','empty_headers','fifth_path','other_host','unscoped_dns'):
            before=len(calls); before_dns=len(dns)
            with pytest.raises(ValueError):
                if bad=='url_search': browser.search_public(query+' '+urls[0])
                elif bad=='empty_headers': http.HttpRequestTool().execute(url=urls[0],method='GET',headers={},timeout=5)
                elif bad=='fifth_path': browser.fetch_public(urls[0]+'-other')
                elif bad=='other_host': browser.fetch_public('https://other.invalid/source')
                else: socket.getaddrinfo('raw.githubusercontent.com',443)
            assert len(calls)==before and len(dns)==before_dns
            if bad in ('fifth_path','other_host','unscoped_dns'):
                assert state['dns']['refused']==1
            elif bad=='empty_headers':
                assert state['refused']==1
        else:
            result=browser.search_public(query)
            assert result['engine']=='duckduckgo' and [r['url'] for r in result['results']]==urls
            for url,source in zip(urls,scope['adapter'].corpus()['sources']):
                fetched=browser.fetch_public(url)
                assert fetched['body']==source['body'] and fetched['content_type']=='text/plain'
            assert [name for name,_ in calls]==['search','http','http','http','http']
            assert state['searches']==1 and state['GETs']==4
            assert all(args[0]=='raw.githubusercontent.com' for args,_ in dns)
            assert state['native_dns'] is None and state['native_packets'] is None
            if bad:
                with pytest.raises(ValueError):
                    if bad=='search_again': browser.search_public(query)
                    else: browser.fetch_public(urls[0])
    assert (httpx.request,ddgs.DDGS,socket.getaddrinfo,http.HttpRequestTool.execute,search.WebSearchTool.execute,http.check_ssrf)==saved

@pytest.mark.parametrize('phase',['installer','alias'])
def test_real_factory_browser_partial_restore(phase,monkeypatch):
    import httpx
    import socket
    p,scope,pins,Browser,calls,dns,http,search,ddgs,resolver=browser_doubles(monkeypatch)
    assert hasattr(p,'browser_scope'),'T2 browser fixture boundary missing'
    module=pins['_ssrf_module']; defining=module.check_ssrf
    error=RuntimeError('synthetic fixture install failure')
    if phase=='installer':
        install=scope['adapter'].install_browser_fixture
        def partial(): install(); raise error
        scope['adapter'].install_browser_fixture=partial
    else: http.check_ssrf=lambda url:None
    saved=(httpx.request,ddgs.DDGS,socket.getaddrinfo,http.HttpRequestTool.execute,search.WebSearchTool.execute,http.check_ssrf)
    with pytest.raises(RuntimeError if phase=='installer' else ValueError) as caught:
        with p.browser_scope(scope,pins): pytest.fail('partial installation admitted')
    if phase=='installer': assert caught.value is error
    assert module.check_ssrf is defining
    assert (httpx.request,ddgs.DDGS,socket.getaddrinfo,http.HttpRequestTool.execute,search.WebSearchTool.execute,http.check_ssrf)==saved
    assert calls==[] and dns==[]

@pytest.mark.parametrize('context',['worker','reader'])
@pytest.mark.parametrize('drift',['backend','branch_type','bridge_origin','defining_origin','checker_identity','python_identity','rust_ok','rust_export_identity','rust_extension_origin'])
def test_ssrf_baseline_backend_identity_before_lookup(context,drift,monkeypatch,tmp_path):
    import hashlib
    from types import ModuleType
    p,scope,pins,Browser,calls,dns,http,search,ddgs,resolver=browser_doubles(monkeypatch)
    assert hasattr(p,'check_ssrf_baseline'),'T2 SSRF backend baseline missing'
    bridge=pins['_rust_bridge']; ssrf=pins['_ssrf_module']; expected='python'
    if drift=='backend': bridge.RUST_AVAILABLE=True
    if drift=='branch_type': bridge.RUST_AVAILABLE=1
    if drift=='bridge_origin': bridge.__file__=str(tmp_path/'foreign-bridge.py')
    if drift=='defining_origin': ssrf.__file__=str(tmp_path/'foreign-ssrf.py')
    if drift=='checker_identity': ssrf.check_ssrf=lambda url:None
    if drift=='python_identity': ssrf._check_ssrf_python=lambda url:None
    if drift.startswith('rust_'):
        expected='rust'; bridge.RUST_AVAILABLE=True
        root=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages/openjarvis_rust')
        extension_path=next(root.glob('*.pyd')).resolve()
        rust=ModuleType('openjarvis_rust'); rust.__file__=str(root/'__init__.py')
        extension=ModuleType('openjarvis_rust.openjarvis_rust'); extension.__file__=str(extension_path)
        operation=lambda url:(_ for _ in ()).throw(AssertionError('baseline must not invoke backend'))
        rust.check_ssrf=operation; extension.check_ssrf=operation; rust.openjarvis_rust=extension
        bridge.get_rust_module=lambda:rust
        pins.update(_rust_ssrf_original=operation,_rust_extension=extension,rust_extension_origin=str(extension_path))
        for path in (Path(rust.__file__).resolve(),extension_path): pins['files'][str(path)]=hashlib.sha256(path.read_bytes()).hexdigest()
        if drift=='rust_export_identity': extension.check_ssrf=lambda url:None
        if drift=='rust_extension_origin': extension.__file__=bridge.__file__
    if drift=='rust_ok':
        result=p.check_ssrf_baseline({},expected_backend=expected,pins=pins)
        assert result['backend']=='rust' and result['native_dns'] is None
    else:
        with pytest.raises(ValueError): p.check_ssrf_baseline({},expected_backend=expected,pins=pins)
    assert calls==[] and dns==[]


@pytest.mark.parametrize('context',['worker','reader'])
@pytest.mark.parametrize('when',['entry','close_zero_lookup','close_after_lookup','close_primary'])
def test_ssrf_baseline_scope_entry_close(context,when,monkeypatch):
    from contextlib import contextmanager
    p,scope,pins,Browser,calls,dns,http,search,ddgs,resolver=browser_doubles(monkeypatch)
    bridge=pins['_rust_bridge']; counts={}; marker=RuntimeError('original primary')
    url=scope['adapter'].corpus()['sources'][0]['final_url']
    if context=='reader':
        monkeypatch.setattr(p,'ssrf_bindings',lambda supplied:pins)
        cm=p.reader_ssrf(dict(pins,ssrf_backend='python'),[url])
    else: cm=p.guarded_ssrf(pins,{'ssrf_backend':'python'},[url],counts)
    if when=='entry': bridge.RUST_AVAILABLE=True
    def exercise():
        with cm as checked:
            if context=='reader': checked=pins['_ssrf_module'].check_ssrf
            if when=='close_after_lookup': assert checked(url) is None
            if when!='entry': bridge.RUST_AVAILABLE=True
            if when=='close_primary': raise marker
    if when=='close_primary':
        with pytest.raises(RuntimeError) as raised: exercise()
        assert raised.value is marker
        if context=='worker': assert counts['baseline_close_failed']==1 and counts['refused']>=1
    else:
        with pytest.raises(ValueError): exercise()
    assert len(dns)==(1 if when=='close_after_lookup' else 0)
    assert pins['_ssrf_module'].check_ssrf is pins['_check_ssrf_original'] and http.check_ssrf is pins['_check_ssrf_original']

@pytest.mark.parametrize('old',[None,'corpus_hook','run_one_round','aliased_hook'])
def test_real_factory_preloaded_old_hooks(old,monkeypatch):
    import sys
    from types import ModuleType
    p=implementation()
    assert hasattr(p,'check_preloaded'),'T2 selected import/old hook fence missing'
    helpers=[str(HERE.parent.parent/'source6-native-reference/controlled-corpus-inputs/corpus_hook.py'),
             str(HERE.parent.parent/'source6-native-reference/controlled-corpus-inputs/run_one_round.py')]
    pins={'forbidden_helpers':helpers}
    if old is not None:
        module=ModuleType(old); module.__file__=helpers[0] if old=='aliased_hook' else helpers[1]
        monkeypatch.setitem(sys.modules,old,module)
        with pytest.raises(ValueError): p.check_preloaded(pins)
    else: p.check_preloaded(pins)


def test_ssrf_baseline_reader_entry_failure_receipt(monkeypatch):
    p,scope,pins,Browser,calls,dns,http,search,ddgs,resolver=browser_doubles(monkeypatch)
    monkeypatch.setattr(p,'ssrf_bindings',lambda supplied:pins)
    pins['_rust_bridge'].RUST_AVAILABLE=True; counts={}
    urls=[s['final_url'] for s in scope['adapter'].corpus()['sources']]
    with pytest.raises(ValueError):
        with p.reader_ssrf(dict(pins,ssrf_backend='python'),urls,counters=counts): pytest.fail('dirty baseline entered reader body')
    receipt=p.ssrf_receipt(counts,'reader')
    assert len(receipt['records'])==1
    row=receipt['records'][0]
    assert row['phase']=='entry' and row['backend']=='rust' and row['baseline_passed'] is False and row['refused']==1
    assert row['checker_entered']==row['python_resolver_entries']==0 and row['source_index'] is None
    assert receipt['native_dns'] is receipt['native_cache'] is receipt['packets'] is None and dns==[]


@pytest.fixture
def actual_ssrf_chain(monkeypatch):
    """Pinned pure canonicalizer/BrowserChannel/SDK guards; no SDK constructor or DNS."""
    import ast
    import __future__
    import httpx
    import os
    import time
    import re
    from urllib.parse import urlsplit,urlunsplit
    p,scope,pins,Browser,calls,dns,http,search,ddgs,resolver=browser_doubles(monkeypatch)
    sdk_path=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages/openjarvis/tools/http_request.py')
    tree=ast.parse(sdk_path.read_text(encoding='utf8'))
    sdk=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='HttpRequestTool')
    methods=[n for n in sdk.body if isinstance(n,ast.FunctionDef) and n.name in ('execute','_request_following_redirects')]
    constants=[n for n in tree.body if isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id in ('_MAX_RESPONSE_BYTES','_MAX_REDIRECTS','_ALLOWED_METHODS') for t in n.targets)]
    error=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='_SSRFRedirectError')
    cls=ast.ClassDef(name='HttpRequestTool',bases=[],keywords=[],body=methods,decorator_list=[])
    module=ast.fix_missing_locations(ast.Module(body=[*constants,error,cls],type_ignores=[]))
    http.__dict__.update(httpx=httpx,os=os,time=time,ToolResult=lambda **kwargs:SimpleNamespace(**kwargs),logger=SimpleNamespace(debug=lambda *args:None))
    exec(compile(module,str(sdk_path),'exec',flags=__future__.annotations.compiler_flag),http.__dict__)
    source=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/work_research.py')
    nodes=ast.parse(source.read_text(encoding='utf8')).body
    selected=[n for n in nodes if (isinstance(n,ast.FunctionDef) and n.name in ('canonical_url','candidate_inputs'))
              or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='URL_PATTERN' for t in n.targets))]
    env=dict(re=re,urlsplit=urlsplit,urlunsplit=urlunsplit)
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),'exec'),env)
    with p.browser_scope(scope,pins) as observed:
        query,urls=env['candidate_inputs'](scope['adapter'].corpus()['query'],[])
        assert urls==observed['urls']
        browser=Browser(); browser.search_public(query)
        for url in urls: assert browser.fetch_public(url)['success'] is True
    receipt=p.ssrf_receipt(observed['dns'],'worker')
    assert len(dns)==16 and [row['source_index'] for row in receipt['records'] if row['phase']=='lookup']==[1,2,3,4,1,1,1,2,2,2,3,3,3,4,4,4]
    assert observed['sdk_GETs']==observed['GETs']==4
    return SimpleNamespace(p=p,receipt=receipt,urls=urls)


@pytest.mark.parametrize('bad',[None,'missing','extra','order','source','old_four','phase','backend'])
def test_ssrf_baseline_actual_sixteen_chain(bad,actual_ssrf_chain):
    r=actual_ssrf_chain; value=copy.deepcopy(r.receipt); rows=value['records']
    if bad=='missing': rows.pop(1)
    elif bad=='extra': rows.insert(2,copy.deepcopy(rows[1]))
    elif bad=='order': rows[1],rows[2]=rows[2],rows[1]
    elif bad=='source': rows[5]['source_index']=2
    elif bad=='old_four': value['records']=[rows[0],*rows[1:5],*rows[-2:]]
    elif bad=='phase': rows[0],rows[-2]=rows[-2],rows[0]
    elif bad=='backend': rows[6]['backend']='rust'
    def validate():
        r.p.validate_ssrf_receipt(value,'worker',complete=True,expected_backend='python')
        r.p.ssrf_source_links(value,r.urls)
    if bad is None: validate()
    else:
        with pytest.raises(ValueError): validate()

@pytest.mark.parametrize('bad',[None,'fifth_path','other_host'])
def test_original_input_canonical_before_search(bad,monkeypatch):
    import ast
    import re
    from urllib.parse import urlsplit,urlunsplit
    p,scope,pins,Browser,calls,dns,http,search,ddgs,resolver=browser_doubles(monkeypatch)
    source=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/work_research.py')
    tree=ast.parse(source.read_text(encoding='utf8'))
    selected=[n for n in tree.body if (isinstance(n,ast.FunctionDef) and n.name in ('canonical_url','candidate_inputs'))
              or (isinstance(n,ast.Assign) and any(isinstance(t,ast.Name) and t.id=='URL_PATTERN' for t in n.targets))]
    env={'re':re,'urlsplit':urlsplit,'urlunsplit':urlunsplit}
    exec(compile(ast.Module(body=selected,type_ignores=[]),str(source),'exec'),env)
    original=env['canonical_url']; entered=[]
    def observed(value): entered.append(value); return original(value)
    env['canonical_url']=observed
    with p.browser_scope(scope,pins) as state:
        query=scope['adapter'].corpus()['query']; urls=state['urls']
        if bad:
            candidate=urls[0]+'-other' if bad=='fifth_path' else 'https://other.invalid/source'
            with pytest.raises(ValueError): env['candidate_inputs'](query,[candidate])
            assert entered==[candidate] and calls==[] and dns==[]
            assert state['dns']['refused']==1
        else:
            cleaned,candidates=env['candidate_inputs'](query,[])
            assert entered==urls and candidates==urls and cleaned==state['search_query']
            assert len(dns)==4 and calls==[] and state['searches']==0
            result=Browser().search_public(cleaned)
            assert result['query']==cleaned and state['searches']==1

@pytest.mark.parametrize('change',[None,0,1,2,3,4,5,6,7,'config','policy_error','client_error'])
def test_real_factory_source_borrow_identity_and_results(change):
    import ast
    from copy import deepcopy
    source=Path('C:/Users/Administrator/.codex/worktrees/jarvis-e03-source13/UltimaAgent/src/brain/agent_server.py')
    tree=ast.parse(source.read_text(encoding='utf8'))
    node=next(n for n in tree.body if isinstance(n,ast.FunctionDef) and n.name=='_borrow_research')
    raw=SimpleNamespace(_client=object()); guard=SimpleNamespace(_engine=raw); outer=SimpleNamespace(_inner=guard)
    conf=SimpleNamespace(mode='redact',scan_input=True,scan_output=True)
    owner=SimpleNamespace(_engine=outer,config=SimpleNamespace(security=conf),_audit_logger=object(),_capability_policy=None,_rate_limiter=object())
    identity=(outer,guard,raw,raw._client,conf,owner._audit_logger,owner._capability_policy,owner._rate_limiter)
    events=[]; policy=object(); client=object(); error=RuntimeError('synthetic borrow boundary')
    ledger=SimpleNamespace(_security_identity=identity,_security_config=deepcopy(conf),_check_policy=lambda value:events.append(('policy',value)))
    if type(change) is int:
        altered=list(identity); altered[change]=object(); ledger._security_identity=tuple(altered)
    if change=='config': ledger._security_config.mode='block'
    def checked(value):
        assert value is owner
        if change=='policy_error': raise error
        return policy
    def get_client():
        events.append(('client',))
        if change=='client_error': raise error
        return client
    class View:
        def __init__(self,*args): self.inner=args[0]; self.args=args; events.append(('view',))
    class Leaf:
        def __init__(self,got_client,got_ledger):
            assert got_client is client and got_ledger is ledger
            self.wire_records=[]; self.transport=object()
    binding=object(); caps=object(); prompt='synthetic prompt'
    env={'_checked_research_security':checked,'_research_client':get_client,'_ResearchEngineView':View,'_NativeResearchLeaf':Leaf}
    exec(compile(ast.Module(body=[node],type_ignores=[]),str(source),'exec'),env)
    if change is not None:
        with pytest.raises(RuntimeError if change in ('policy_error','client_error') else ValueError) as caught:
            env['_borrow_research'](owner,binding,ledger,caps,prompt)
        if change in ('policy_error','client_error'): assert caught.value is error
        if change!='client_error': assert ('client',) not in events
    else:
        view,returned=env['_borrow_research'](owner,binding,ledger,caps,prompt)
        assert returned is client and view.args[1:]==(binding,ledger,caps,prompt)
        assert view.inner is not outer and view.inner._inner is not guard
        assert owner._engine is outer and guard._engine is raw
        assert view.leaf.guard is view.inner._inner
        assert ledger._runtime_wires is view.leaf.wire_records and ledger._runtime_transport is view.leaf.transport
        assert ledger._runtime_prompt==prompt and events==[('policy',policy),('view',),('client',)]

@pytest.mark.parametrize('mode',['success','failed_result','raised','old_request','changed_query'])
def test_real_factory_original_submission_once(mode):
    import uuid
    p=implementation()
    assert hasattr(p,'_submit_original'),'T2 original one-shot submit boundary missing'
    inputs=json.loads((HERE.parent.parent/'source6-native-reference/controlled-corpus-inputs/corpus.json').read_text(encoding='utf8'))
    if mode=='old_request': inputs['request_id']='00000000-0000-4000-8000-000000000001'
    if mode=='changed_query': inputs['query']='X'+inputs['query'][1:]
    calls=[]; result={'status':'failed' if mode=='failed_result' else 'succeeded'}
    error=RuntimeError('synthetic submission failure')
    class Service:
        def submit_work(self,*args,**kwargs):
            calls.append((args,kwargs))
            if mode=='raised': raise error
            return result
    scope={'submitted':False,'grant':{'run_id':str(uuid.uuid4()),'entry_nonce':str(uuid.uuid4()),'work_deadline_ns':p.time.monotonic_ns()+275*10**9}}
    service=Service()
    if mode in ('old_request','changed_query'):
        with pytest.raises(ValueError): p._submit_original(scope,service,inputs)
        assert calls==[]
    elif mode=='raised':
        with pytest.raises(RuntimeError) as caught: p._submit_original(scope,service,inputs)
        assert caught.value is error
    else:
        assert p._submit_original(scope,service,inputs) is result
    assert scope['submitted'] is True
    with pytest.raises(ValueError): p._submit_original(scope,service,inputs)
    if mode not in ('old_request','changed_query'):
        assert len(calls)==1
        args,kwargs=calls[0]
        assert args==(inputs['query'],)
        assert set(kwargs)=={'request_id','session_id','context'} and kwargs['context']=={'research':True}
        assert kwargs['context']['research'] is True
        request,session=kwargs['request_id'],kwargs['session_id']
        for value in (request,session): assert str(uuid.UUID(value))==value and uuid.UUID(value).version==4
        assert len({request,session,scope['grant']['run_id'],scope['grant']['entry_nonce']})==4

_EAGER_ALIASES=('generate','chat','embed','embeddings','pull','push','create','delete','list','copy','show','ps','web_search','web_fetch','systemone')

@pytest.fixture
def eager_fixture(tmp_path,monkeypatch):
    import hashlib
    import sys
    from types import ModuleType
    probe=ModuleType('eager_probe')
    probe.delegated=[]; probe.clients=[]; probe.constructor_attempts=[]; probe.close_attempts=[]
    probe.constructor_error=ValueError('synthetic constructor failure')
    probe.import_error=ValueError('synthetic import failure')
    probe.close_error=ValueError('synthetic close failure')
    monkeypatch.setitem(sys.modules,'eager_probe',probe)
    monkeypatch.syspath_prepend(str(tmp_path))
    def build(variant='clean'):
        package=tmp_path/'ollama'; package.mkdir(exist_ok=True)
        code='''import httpx
import eager_probe as probe
VARIANT=__VARIANT__
ALIASES=__ALIASES__
class Client:
    def __init__(self):
        probe.constructor_attempts.append(True)
        if VARIANT=='constructor': raise probe.constructor_error
        def handler(request):
            probe.delegated.append((request.method,request.url.path))
            return httpx.Response(200,content=b'{}')
        class Opaque(httpx.BaseTransport):
            def handle_request(self,request): raise AssertionError('opaque transport must never delegate')
            def close(self):
                probe.transport_closed=True
                if VARIANT=='opaque_close': raise probe.close_error
        transport=Opaque() if VARIANT.startswith('opaque') else httpx.MockTransport(handler)
        self._client=httpx.Client(base_url='http://127.0.0.1:11434',follow_redirects=True,transport=transport)
        probe.clients.append(self._client)
    def close(self):
        probe.close_attempts.append(True)
        if VARIANT=='close': raise probe.close_error
        self._client.close()
    def operation(self,*args,**kwargs):
        return self._client.request('POST','/api/chat')
for name in ALIASES: setattr(Client,name,Client.operation)
_client=Client()
for name in ALIASES: globals()[name]=getattr(_client,name)
if VARIANT=='import': raise probe.import_error
for name in (('chat','embed','pull') if VARIANT=='all_import' else (VARIANT[7:],) if VARIANT.startswith('import_') else ()):
    try: globals()[name](model='synthetic')
    except ValueError: pass
'''.replace('__VARIANT__',repr(variant)).replace('__ALIASES__',repr(_EAGER_ALIASES))
        path=package/'__init__.py'; path.write_text(code,encoding='utf8')
        return {'files':{str(path):hashlib.sha256(path.read_bytes()).hexdigest()},'ollama_origin':str(path)},probe
    try:
        yield build
    finally:
        for name in list(sys.modules):
            if name=='ollama' or name.startswith('ollama.'): sys.modules.pop(name,None)

def test_eager_default_client_clean_early_close(eager_fixture):
    import httpx
    p=implementation(); pins,probe=eager_fixture(); audit={}
    constructor=httpx.Client
    with p.own_ollama_types(pins,audit) as state:
        assert state['owner']._client is probe.clients[0]
        assert state['owner']._client.is_closed
        assert state['import_sends']==state['refused_sends']==0
        assert probe.delegated==[] and len(probe.constructor_attempts)==1
        assert all(getattr(state['module'],name).__self__ is state['owner'] for name in _EAGER_ALIASES)
    assert audit['eager']['clean'] is True and audit['eager']['closed'] is True
    assert audit['eager']['early_closed'] is True and audit['eager']['cleanup_closed'] is True
    assert audit['eager']['constructors']==1 and audit['metadata_charged']==0
    assert httpx.Client is constructor and probe.delegated==[]


@pytest.mark.parametrize('variant',['opaque','opaque_close'])
def test_eager_default_client_reader_mock_fence(variant,eager_fixture):
    import httpx
    p=implementation(); pins,probe=eager_fixture(variant); audit={}
    if variant=='opaque':
        with p.own_ollama_types(pins,audit) as state:
            assert type(state['owner']._client._transport) is httpx.MockTransport
            assert state['owner']._client.is_closed and probe.transport_closed is True
        assert audit['eager']['clean'] is True
    else:
        with pytest.raises(ValueError) as raised:
            with p.own_ollama_types(pins,audit): pytest.fail('failed transport close exposed eager types')
        assert raised.value is probe.close_error and audit['eager']['clean'] is False
    assert probe.delegated==[] and audit['metadata_charged']==0

@pytest.mark.parametrize('operation',['chat','embed','pull'])
def test_eager_default_client_retained_alias_one_refusal(operation,eager_fixture):
    import httpx
    p=implementation(); pins,probe=eager_fixture(); audit={}; constructor=httpx.Client
    with pytest.raises(ValueError,match='eager'):
        with p.own_ollama_types(pins,audit) as state:
            retained=getattr(state['module'],operation)
            with pytest.raises(ValueError): retained(model='synthetic')
            assert state['refused_sends']==1 and probe.delegated==[]
    assert audit['eager']['clean'] is False and audit['eager']['later_attempts']==1
    assert audit['metadata_charged']==0 and httpx.Client is constructor

@pytest.mark.parametrize('variant',['import_chat','import_embed','import_pull','all_import'])
def test_eager_default_client_import_window_refusal(variant,eager_fixture):
    import httpx
    p=implementation(); pins,probe=eager_fixture(variant); audit={}; constructor=httpx.Client
    with pytest.raises(ValueError):
        with p.own_ollama_types(pins,audit): pytest.fail('import-window send admitted')
    assert probe.delegated==[]
    assert all(client.is_closed for client in probe.clients)
    assert audit['eager']['clean'] is False
    assert audit['eager']['import_attempts']==(3 if variant=='all_import' else 1)
    assert audit['eager']['pinned_send_calls']==0 and audit['metadata_charged']==0
    assert httpx.Client is constructor

@pytest.mark.parametrize('variant',['constructor','import','close'])
def test_eager_default_client_failure_first_cause(variant,eager_fixture):
    import httpx
    p=implementation(); pins,probe=eager_fixture(variant); audit={}; constructor=httpx.Client
    with pytest.raises(ValueError) as caught:
        with p.own_ollama_types(pins,audit): pytest.fail('failed initializer/close admitted')
    assert caught.value is getattr(probe,variant+'_error')
    assert audit['eager']['clean'] is False
    assert all(client.is_closed for client in probe.clients)
    assert audit['eager']['early_closed'] is None
    assert audit['eager']['first_error_type']=='ValueError'
    assert probe.delegated==[] and audit['metadata_charged']==0 and httpx.Client is constructor


def owner_constructor_double():
    import ast
    import httpx
    from types import ModuleType
    path=Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages/openjarvis/engine/ollama.py')
    tree=ast.parse(path.read_text(encoding='utf8'))
    klass=next(n for n in tree.body if isinstance(n,ast.ClassDef) and n.name=='OllamaEngine')
    selected=[n for n in klass.body if isinstance(n,ast.FunctionDef) and n.name in ('__init__','health')]
    module=ModuleType('synthetic_owner_engine'); module.__file__=str(path)
    module.__dict__.update(httpx=httpx,os=SimpleNamespace(environ={}))
    exec(compile(__import__('ast').Module(body=selected,type_ignores=[]),str(path),'exec'),module.__dict__)
    Engine=type('OllamaEngine',(),{'_DEFAULT_HOST':'http://localhost:11434',
        '__init__':module.__dict__['__init__'],'health':module.__dict__['health']})
    module.OllamaEngine=Engine
    return module

@pytest.mark.parametrize('bad',[None,'unrelated_call','wrong_class','wrong_host','wrong_timeout','second_owner','unbound','changed_owner','second_tags'])
def test_guard_before_owner_constructor_binding(bad):
    import httpx
    p=implementation()
    assert hasattr(p,'OwnerHTTPXFacade'),'T1 pinned raw-owner constructor facade missing'
    module=owner_constructor_double(); original=httpx.Client; budget=p.MetadataBudget(); counters={}; clients=[]
    facade=p.OwnerHTTPXFacade(module,httpx,budget,b'{"models":[]}',counters,clients)
    module.httpx=facade
    try:
        if bad in ('unrelated_call','wrong_class','wrong_host','wrong_timeout'):
            with pytest.raises(ValueError):
                if bad=='unrelated_call': facade.Client(base_url='http://localhost:11434',timeout=1800.0)
                elif bad=='wrong_class': type('OtherOwner',(module.OllamaEngine,),{})()
                elif bad=='wrong_host': module.OllamaEngine(host='http://127.0.0.1:11434')
                else: module.OllamaEngine(timeout=25)
            assert clients==[] and budget.bootstrap==0
        else:
            raw=module.OllamaEngine()
            assert facade.raw_owner is raw and raw._client is facade.client is clients[0]
            assert counters['construct_attempts']==1 and counters.get('handled',0)==0
            if bad=='second_owner':
                with pytest.raises(ValueError): module.OllamaEngine()
                assert len(clients)==1 and budget.bootstrap==0
            elif bad in ('unbound','changed_owner'):
                raw._client=None if bad=='unbound' else object()
                with pytest.raises(ValueError): clients[0].get('/api/tags')
                assert budget.bootstrap==0 and counters.get('handled',0)==0
            else:
                assert raw.health() is True
                assert budget.bootstrap==1 and counters['handled']==1
                if bad=='second_tags':
                    with pytest.raises(ValueError): raw._client.get('/api/tags')
                    assert counters['handled']==1
        if bad is not None: assert counters['refused']>=1
        assert httpx.Client is original
    finally:
        module.httpx=httpx
        for client in clients: client.close()
    assert all(client.is_closed for client in clients)

@pytest.mark.parametrize('bad',['unknown_get','unknown_model','foreign_host','direct_send','changed_transport','redirect','proxy','trust_env','async'])
def test_uncovered_selected_path_private_client(bad):
    import httpx
    p=implementation(); calls=[]; counters={}; budget=p.MetadataBudget()
    def handler(request): calls.append(request.url.path); return httpx.Response(200,content=b'{}')
    role='research' if bad=='unknown_model' else 'owner'
    origin='http://127.0.0.1:11434' if role=='research' else 'http://localhost:11434'
    cls=httpx.AsyncClient if bad=='async' else httpx.Client
    kwargs=dict(base_url=origin,transport=httpx.MockTransport(handler),follow_redirects=False,trust_env=bad=='trust_env')
    if bad=='proxy': kwargs['proxy']='http://proxy.invalid:80'
    client=cls(**kwargs)
    saved_transport=client._transport
    try:
        if bad in ('proxy','trust_env','async'):
            with pytest.raises(ValueError): p._guard_client(client,role,budget,handler,counters)
        else:
            p._guard_client(client,role,budget,handler,counters,phase_state={'phase':'chat'} if role=='research' else None)
            with pytest.raises(ValueError):
                if bad=='unknown_get': client.get('/api/pull')
                elif bad=='unknown_model': client.post('/api/chat',content=b'{"model":"forbidden"}')
                elif bad=='foreign_host': client.get('https://other.invalid/api/tags')
                elif bad=='direct_send': client.send(httpx.Request('GET',origin+'/api/tags'))
                elif bad=='changed_transport':
                    client._transport=httpx.MockTransport(handler); client.get('/api/tags')
                else: client.get('/api/tags',follow_redirects=True)
        assert calls==[] and counters['refused']>=1
    finally:
        replacement=client._transport; client._transport=saved_transport
        if replacement is not saved_transport: replacement.close()
        if bad=='async':
            coroutine=client.aclose()
            with pytest.raises(StopIteration): coroutine.send(None)
        else: client.close()

def test_uncovered_selected_path_audit_caught_is_dirty():
    p=implementation()
    assert hasattr(p,'audit_closeout'),'T1 audit closure predicate missing'
    audit=p.WorkerAudit()
    # Simulate the SDK swallowing the immediate denial. The closure stays dirty.
    try: audit('socket.connect',())
    except ValueError: pass
    result=p.audit_closeout(audit)
    assert result['clean'] is False and result['denied']=={'socket.connect':1}
    assert result['ordinary_http'] is None and result['os_packets'] is None and result['native_activity'] is None


@pytest.mark.parametrize('bad',[None,'self_dict','extra','missing','same_nonce','uuid1','pid','creation_bool',
    'future','expired','renewed','executable','root','candidate','model','scope','consumed_bool','retry',
    'http','endpoint','inference','fail_open','backend','hash','pin'])
def test_guard_before_admission_closed(bad,tmp_path,monkeypatch):
    import os
    import uuid
    p=implementation(); origin=10**12
    monkeypatch.setattr(p.time,'monotonic_ns',lambda:origin+1)
    pins={key:'a'*64 for key in ('profile_manifest_sha256','candidate_manifest_sha256','corpus_sha256')}
    grant={key:'a'*64 for key in p._ADMISSION_FIELDS}
    grant.update(run_id=str(uuid.uuid4()),entry_nonce=str(uuid.uuid4()),worker_pid=os.getpid(),
        worker_creation_filetime=1,origin_ns=origin,work_deadline_ns=origin+275*10**9,
        cleanup_deadline_ns=origin+310*10**9,seal_deadline_ns=origin+315*10**9,
        case_root=str(tmp_path),worker_executable=str(p.PY),candidate=p.CANDIDATE,model_digest=p.MODEL_DIGEST,
        scope='ORIGINAL_CORPUS_ZERO_INFERENCE_PROFILE',consumed=1,max_submissions=1,retry=0,
        actual_http_allowed=0,actual_11434_allowed=0,actual_inference_allowed=0,
        ssrf_fail_open_present=False,ssrf_backend='rust')
    changes={'same_nonce':('entry_nonce',grant['run_id']),'uuid1':('run_id',str(uuid.uuid1())),
        'pid':('worker_pid',os.getpid()+1),'creation_bool':('worker_creation_filetime',True),
        'future':('origin_ns',origin+2),'expired':('work_deadline_ns',origin),
        'renewed':('seal_deadline_ns',origin+316*10**9),'executable':('worker_executable','C:/other/python.exe'),
        'root':('case_root',str(tmp_path/'other')),'candidate':('candidate','other'),'model':('model_digest','b'*64),
        'scope':('scope','other'),'consumed_bool':('consumed',True),'retry':('retry',1),
        'http':('actual_http_allowed',1),'endpoint':('actual_11434_allowed',1),'inference':('actual_inference_allowed',1),
        'fail_open':('ssrf_fail_open_present',True),'backend':('ssrf_backend','auto'),
        'hash':('allocation_sha256','A'*64),'pin':('corpus_sha256','b'*64)}
    if bad in changes: key,value=changes[bad]; grant[key]=value
    elif bad=='extra': grant['self_verified']=True
    elif bad=='missing': grant.pop('allocation_sha256')
    elif bad=='self_dict': grant={'verified':True}
    if bad is None: p.validate_admission(grant,tmp_path,pins)
    else:
        with pytest.raises(ValueError): p.validate_admission(grant,tmp_path,pins)


def admission_double(p,folder,pins):
    import uuid
    origin=p.time.monotonic_ns()
    grant={key:'a'*64 for key in p._ADMISSION_FIELDS}
    grant.update(run_id=str(uuid.uuid4()),entry_nonce=str(uuid.uuid4()),worker_pid=p.os.getpid(),
        worker_creation_filetime=1,origin_ns=origin,work_deadline_ns=origin+275*10**9,
        cleanup_deadline_ns=origin+310*10**9,seal_deadline_ns=origin+315*10**9,
        case_root=str(folder),worker_executable=str(p.PY),candidate=p.CANDIDATE,model_digest=p.MODEL_DIGEST,
        scope='ORIGINAL_CORPUS_ZERO_INFERENCE_PROFILE',consumed=1,max_submissions=1,retry=0,
        actual_http_allowed=0,actual_11434_allowed=0,actual_inference_allowed=0,
        ssrf_fail_open_present=False,ssrf_backend='rust')
    grant.update({key:pins[key] for key in ('profile_manifest_sha256','candidate_manifest_sha256','corpus_sha256')})
    return grant


@pytest.mark.parametrize('bad',[None,'cwd','path','startup','host','key','proxy','pythonpath','home',
    'cache','temp','fail_open','model','nonempty','symlink','models_override','config_override','xdg_data_override'])
def test_guard_before_bootstrap_environment(bad,tmp_path,monkeypatch):
    import sys
    p=implementation()
    assert hasattr(p,'validate_bootstrap'),'T1 bootstrap validation missing'
    package=tmp_path/'package'; package.mkdir(); folder=tmp_path/'case'; folder.mkdir()
    pins=dict(package_root=str(package),import_path=[str(package)],model_digest=p.MODEL_DIGEST)
    monkeypatch.chdir(package); monkeypatch.setattr(sys,'path',[str(package)])
    env={}
    injected={'host':'OLLAMA_HOST','key':'OLLAMA_API_KEY','proxy':'https_proxy','pythonpath':'PYTHONPATH',
              'home':'OPENJARVIS_HOME','cache':'XDG_CACHE_HOME','temp':'TMP','fail_open':'openjarvis_ssrf_fail_open',
              'models_override':'OLLAMA_MODELS','config_override':'OPENJARVIS_CONFIG','xdg_data_override':'XDG_DATA_HOME'}
    if bad in injected: env[injected[bad]]=''
    elif bad=='cwd': monkeypatch.chdir(tmp_path)
    elif bad=='path': sys.path.append(str(tmp_path/'foreign'))
    elif bad=='startup': monkeypatch.setitem(sys.modules,'sitecustomize',SimpleNamespace())
    elif bad=='model': pins['model_digest']='b'*64
    elif bad=='nonempty': (folder/'old').write_bytes(b'old')
    elif bad=='symlink': pins['package_root']=str(package/'..'/'package')
    before=dict(env)
    if bad is None: p.validate_bootstrap(folder,pins,environ=env)
    else:
        with pytest.raises(ValueError): p.validate_bootstrap(folder,pins,environ=env)
    assert env==before


@pytest.mark.parametrize('bad',[None,'empty_members','extra_member','traversal','member_drift','dependency_drift','self_member'])
def test_guard_before_manifest_members(bad,tmp_path):
    import hashlib
    import json
    p=implementation(); members={}
    for name in ('profile.py','test_profile.py','run_checks.py','README.md'):
        (tmp_path/name).write_bytes(name.encode()); members[name]=hashlib.sha256(name.encode()).hexdigest()
    dependency=tmp_path/'dependency'; dependency.write_bytes(b'frozen')
    manifest={'runtime_released':False,'files':{str(dependency):hashlib.sha256(b'frozen').hexdigest()},'members':members}
    if bad=='empty_members': manifest['members']={}
    elif bad=='extra_member': members['extra.py']='a'*64; (tmp_path/'extra.py').write_bytes(b'x')
    elif bad=='traversal': members['../profile.py']=members.pop('profile.py')
    elif bad=='member_drift': (tmp_path/'profile.py').write_bytes(b'changed')
    elif bad=='dependency_drift': dependency.write_bytes(b'changed')
    elif bad=='self_member': members['manifest.json']='a'*64
    path=tmp_path/'manifest.json'; path.write_text(json.dumps(manifest),encoding='utf8')
    if bad is None:
        actual=p.read_pins(path)
        assert actual['profile_manifest_sha256']==hashlib.sha256(path.read_bytes()).hexdigest()
    else:
        with pytest.raises(ValueError): p.read_pins(path)


def test_uncovered_selected_path_dns_audit_wrong_host():
    p=implementation(); audit=p.WorkerAudit(); token=p._DNS.set(True)
    try:
        with pytest.raises(ValueError): audit('socket.getaddrinfo',('other.invalid',443,0,0,0))
    finally: p._DNS.reset(token)
    assert audit.denied=={'socket.getaddrinfo':1}
    assert p.audit_closeout(audit)['clean'] is False


@pytest.mark.parametrize('bad',['pin','env','cwd','import_path','cache','not_empty','self_admission'])
def test_guard_before_scope_rejection_precedes_import(bad,tmp_path,monkeypatch):
    p=implementation(); folder=tmp_path/'case'; folder.mkdir(); package=tmp_path/'package'; package.mkdir()
    source=tmp_path/'source'; source.write_bytes(b'frozen')
    pins=dict(files={str(source):p.digest(b'frozen')},package_root=str(package),import_path=list(p.sys.path),
        model_digest=p.MODEL_DIGEST,owner_origin='http://localhost:11434',research_origin='http://127.0.0.1:11434',
        profile_manifest_sha256='a'*64,candidate_manifest_sha256='a'*64,corpus_sha256='a'*64)
    monkeypatch.chdir(package)
    for key in list(p.os.environ):
        if key.upper() in ('OLLAMA_HOST','OLLAMA_API_KEY','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP',
                'OPENJARVIS_HOME','XDG_CACHE_HOME','TMP','TEMP','TMPDIR','OPENJARVIS_SSRF_FAIL_OPEN') or key.upper().endswith('_PROXY'):
            monkeypatch.delenv(key)
    calls=[]
    monkeypatch.setattr(p.importlib,'import_module',lambda name:calls.append(name))
    monkeypatch.setattr(p.sys,'addaudithook',lambda hook:calls.append('audit'))
    class Controls(p.RootControls):
        def admit(self,folder,pins): return admission_double(p,folder,pins)
    admission=Controls()
    if bad=='pin': source.write_bytes(b'drift')
    elif bad=='env': monkeypatch.setenv('OLLAMA_HOST','')
    elif bad=='cwd': monkeypatch.chdir(tmp_path)
    elif bad=='import_path': pins['import_path']=[]
    elif bad=='cache': monkeypatch.setitem(p.sys.modules,'ollama',SimpleNamespace())
    elif bad=='not_empty': (folder/'old').write_bytes(b'old')
    elif bad=='self_admission': admission={'verified':True}
    with pytest.raises(ValueError):
        with p.private_scope(folder,pins,admission): pytest.fail('rejected entry exposed SDK')
    assert calls==[] and list(folder.iterdir())==([] if bad!='not_empty' else [folder/'old'])


@pytest.mark.parametrize('role',['worker','reader'])
def test_real_sdk_cold_import(role,tmp_path):
    """No eager fixture or warmed platform: the original SDK runs in a new PID."""
    import os
    import subprocess
    p=implementation()
    forbidden={'OLLAMA_HOST','OLLAMA_API_KEY','OLLAMA_MODELS','PYTHONPATH','PYTHONHOME','PYTHONSTARTUP',
        'OPENJARVIS_HOME','OPENJARVIS_CONFIG','XDG_DATA_HOME','XDG_CACHE_HOME','TMP','TEMP','TMPDIR','OPENJARVIS_SSRF_FAIL_OPEN'}
    env={k:v for k,v in os.environ.items() if k.upper() not in forbidden and not k.upper().endswith('_PROXY')}
    result=tmp_path/'result.json'
    command=[str(p.PY),'-I','-B','-X','utf8',str(HERE.parent/'cold/cold_import_probe.py'),role,str(tmp_path/'cold'),str(result)]
    run=subprocess.run(command,env=env,cwd=HERE,capture_output=True,timeout=45,creationflags=subprocess.CREATE_NO_WINDOW)
    (tmp_path/'stdout.txt').write_bytes(run.stdout);(tmp_path/'stderr.txt').write_bytes(run.stderr)
    assert result.exists(),run.stderr.decode('utf-8','replace')
    value=json.loads(result.read_bytes())
    assert run.returncode==0 and value['outcome']=='PASS',value
    assert value['pid']!=os.getpid() and value['platform_cache_cold'] and value['real_sdk_not_preloaded']
    assert value['real_types_and_early_close'] and value['boundary_stopped'] and value['eager_audit']['eager']['clean']
    assert value['research_submissions']==value['model_calls']==value['profile_invocations']==0
    assert value['audit_events'] and set(value['audit_events'])=={'socket.gethostname'}
    assert value['refused_io']==[] and value['runtime_authority'] is False


@pytest.mark.parametrize('event',['socket.gethostname_extra','socket.gethostname.exfiltrate'])
def test_hostname_exception_is_exact(event):
    p=implementation();audit=p.WorkerAudit()
    with pytest.raises(ValueError):audit(event,())
    assert audit.denied=={event:1}
