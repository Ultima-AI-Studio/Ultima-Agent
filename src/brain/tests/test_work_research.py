"""Research prerequisites exercise real SDK dispatch, registry, GET and file tools."""
import importlib.util
import json
from pathlib import Path
import pytest
from src.brain.work_service import WorkService

URLS=['https://example.com/source/'+str(i) for i in range(1,6)]


@pytest.fixture
def sdk_io(monkeypatch):
    import ddgs
    import httpx
    import socket
    calls=[]
    statuses={}
    monkeypatch.setattr(socket,'getaddrinfo',lambda *a,**kw:[(2,1,6,'',('93.184.216.34',443))])
    class Search:
        def text(self,query,max_results):
            calls.append(('search',query))
            return [dict(title='Document '+str(i),href=u,body='Discovery only') for i,u in enumerate(URLS,1)]
    monkeypatch.setattr(ddgs,'DDGS',Search)
    def get(method,url,**kw):
        calls.append(('get',url))
        assert method=='GET' and kw['follow_redirects'] is False and kw['timeout']==5
        return httpx.Response(statuses.get(url,200),headers={'content-type':'text/plain'},text='Fetched distinct body for '+url,request=httpx.Request(method,url))
    monkeypatch.setattr(httpx,'request',get)
    from src.brain.browser.channel import BrowserChannel
    return BrowserChannel(),calls,statuses


def submit(tmp_path,browser,runner,**context):
    return WorkService(tmp_path,runner=runner,browser_channel=browser).submit_work('Research a subject',request_id='r',session_id='s',context={'research':True,**context})


def report_payload(count=3):
    from src.brain.work_tools import _ACTIVE
    bound = _ACTIVE.get()
    cards = json.loads(bound[2].cards_json) if bound and bound[2].cards_json else {}
    sections = []
    for i in range(1,count+1):
        sid = f'S{i}'
        ref = next((k for k,c in cards.items() if c['source_id']==sid),'issued:'+sid)
        sections.append(dict(source_id=sid,heading=f'Section {i}',
                             facts=[dict(claim='A distinct fetched source',evidence_id=ref)]))
    return dict(path='research.md',title='Model title',sections=sections)


def write_report(payload=None):
    assert importlib.util.find_spec('src.brain.work_research'),'research adapter missing'
    from src.brain.work_tools import WorkResearchWriteTool
    result=WorkResearchWriteTool().execute(**(payload or report_payload()))
    assert result.success,result.content
    return {}


def test_required_reads_precede_even_an_immediate_final_answer(tmp_path,sdk_io):
    browser,calls,_=sdk_io
    def runner(*a,**kw):
        assert [kind for kind,_ in calls]==['search']+['get']*5
        assert 'Discovery only' not in a[0]
        assert 'ultima_work_research_write' in kw['tools']
        assert 'ultima_work_file_write' not in kw['tools']
        return {'content':'final answer without file'}
    r=submit(tmp_path,browser,runner)
    assert r['status']=='failed' and not r['artifacts'],r


def test_actual_report_write_cites_three_of_five_fetched_sources(tmp_path,sdk_io):
    browser,calls,_=sdk_io
    r=submit(tmp_path,browser,lambda *a,**kw:write_report())
    assert r['status']=='succeeded',r
    text=Path(r['artifacts'][0]['path']).read_text(encoding='utf8')
    assert all(u in text for u in URLS[:3]) and all(u not in text for u in URLS[3:])
    assert len(r['sources'])==3 and len(r['available_sources'])==5
    assert all(s['body'].endswith(s['final_url']) for s in r['sources'])
    assert len([e for e in r['trace'] if e.get('phase')=='research.preflight' and e['type']=='tool_call_start'])==6
    assert all(e['task_id']==r['task_id'] and e['sdk_call_id'] for e in r['trace'] if e.get('phase')=='research.preflight')


def test_optional_failed_probe_has_exact_ledger_identity(tmp_path,sdk_io):
    browser,_,statuses=sdk_io
    statuses[URLS[-1]]=404
    r=submit(tmp_path,browser,lambda *a,**kw:write_report())
    assert r['status']=='succeeded',r
    failures=[a for a in r['research_attempts'] if not a['success']]
    assert len(failures)==1 and failures[0]['adapter_call_id'] and failures[0]['sdk_call_id']
    assert any(x.get('call_id')==failures[0]['adapter_call_id'] and x['success'] is False for x in r['tool_results'])


@pytest.mark.parametrize('forgery',['same_tool','model_metadata'])
def test_failed_model_action_cannot_use_probe_waiver(tmp_path,sdk_io,forgery):
    browser,_,statuses=sdk_io
    statuses[URLS[-1]]=404
    def runner(*a,**kw):
        write_report()
        if forgery=='same_tool':
            from src.brain.work_tools import WorkGetTool
            assert not WorkGetTool().execute(url=URLS[-1]).success
            return {}
        from src.brain.work_tools import _ACTIVE
        records=_ACTIVE.get()[1].snapshot()
        failed=next(x for x in records if x.get('tool_name')=='ultima_work_http_get' and not x['success'])
        return {'tool_results':[dict(failed)]}
    r=submit(tmp_path,browser,runner)
    assert r['status']=='needs_attention',r


@pytest.mark.parametrize('fault',['insufficient','same_body','invalid','excess'])
def test_bad_collection_never_reaches_model_or_file(tmp_path,sdk_io,monkeypatch,fault):
    browser,calls,statuses=sdk_io
    data={}
    if fault=='insufficient': statuses.update({u:404 for u in URLS[2:]})
    if fault=='same_body':
        import httpx
        monkeypatch.setattr(httpx,'request',lambda method,url,**kw:httpx.Response(200,headers={'content-type':'text/plain'},text='same body',request=httpx.Request(method,url)))
    if fault=='invalid': data['source_urls']=['http://localhost/private']
    if fault=='excess': data['source_urls']=URLS+['https://example.com/six']
    r=submit(tmp_path,browser,lambda *a,**kw:pytest.fail('collection failed but model ran'),**data)
    assert r['status']=='failed' and not r['artifacts'],r
    assert not list(tmp_path.rglob('*.md'))


def test_real_executor_timeout_aborts_before_runner(tmp_path,sdk_io,monkeypatch):
    import concurrent.futures
    from openjarvis.tools import _stubs
    original=_stubs._TOOL_RUNNER.submit
    class TimedOut:
        def result(self,timeout):
            assert timeout==35
            raise concurrent.futures.TimeoutError()
        def cancel(self): return True
    def submit_tool(function,**params):
        return TimedOut() if function.__self__.tool_id=='ultima_work_http_get' else original(function,**params)
    monkeypatch.setattr(_stubs._TOOL_RUNNER,'submit',submit_tool)
    browser,_,_=sdk_io
    r=submit(tmp_path,browser,lambda *a,**kw:pytest.fail('timeout reached model'))
    assert r['status']=='failed' and not r['artifacts'],r
    assert any(e['type']=='tool_timeout' for e in r['trace'])


@pytest.mark.parametrize('change',[{'source_id':'S99'},{'source_id':'S2'},{'url':'https://evil.example/'},{'facts':['See https://unfetched.example/']},{'facts':['See www.unfetched.example']},{'facts':['See ftp://unfetched.example/']},{'facts':[]}])
def test_report_refuses_unbound_or_forged_citations(tmp_path,sdk_io,change):
    browser,_,_=sdk_io
    def runner(*a,**kw):
        from src.brain.work_tools import WorkResearchWriteTool
        data=report_payload(); data['sections'][0].update(change)
        if change.get('facts') and isinstance(change['facts'][0],str):
            data['sections'][0]['facts']=[dict(report_payload()['sections'][0]['facts'][0],claim=change['facts'][0])]
        assert not WorkResearchWriteTool().execute(**data).success
        return {}
    r=submit(tmp_path,browser,runner)
    assert r['status']=='failed' and not r['artifacts'],r


def test_source_candidates_are_data_and_combined_mutation_is_early_rejected(tmp_path,sdk_io):
    browser,calls,_=sdk_io
    r=submit(tmp_path,browser,lambda *a,**kw:pytest.fail('bad combination'),capture_current=True,replace_selection=True)
    assert r['status']=='failed' and calls==[],r


def test_unbound_report_writer_fails_without_file(tmp_path):
    assert importlib.util.find_spec('src.brain.work_research'),'research adapter missing'
    from src.brain.work_tools import WorkResearchWriteTool
    assert not WorkResearchWriteTool().execute(**report_payload()).success


def test_cli_source_urls_remain_candidate_data(monkeypatch,capsys):
    from src.brain import cli,agent_client
    def ask(*a,**kw):
        assert kw['context']=={'research':True,'source_urls':URLS[:3]}
        return {'status':'failed','error':'transport seam'}
    monkeypatch.setattr(agent_client,'ask_work',ask)
    args=['--work','--research','--request-id','r','--session-id','s','--json']
    for url in URLS[:3]: args+=['--source-url',url]
    assert cli.main(args+['Natural research request'])==2
    assert json.loads(capsys.readouterr().out)['status']=='failed'


def test_malformed_sdk_search_records_retain_raw_and_diagnostics(tmp_path,sdk_io,monkeypatch):
    import ddgs
    class Malformed:
        def text(self,*a,**kw): return [dict(title='line one\nline two',href=URLS[0],body='snippet')]
    monkeypatch.setattr(ddgs,'DDGS',Malformed)
    browser,_,_=sdk_io
    r=submit(tmp_path,browser,lambda *a,**kw:pytest.fail('malformed source hints reached model'))
    assert r['status']=='failed'
    search=next(x['result'] for x in r['tool_results'] if x.get('tool_name')=='ultima_work_web_search')
    assert search['body'] and search['parser_diagnostics'] and search['results']==[]


def test_mandatory_search_failure_cannot_be_waived(tmp_path,sdk_io,monkeypatch):
    from openjarvis.tools.web_search import WebSearchTool
    from openjarvis.core.types import ToolResult
    monkeypatch.setattr(WebSearchTool,'execute',lambda *a,**kw:ToolResult(tool_name='web_search',success=False,content='network unavailable'))
    browser,calls,_=sdk_io
    r=submit(tmp_path,browser,lambda *a,**kw:pytest.fail('failed search reached model'),source_urls=URLS[:3])
    assert r['status']=='failed' and not calls and 'Mandatory' in r['error'],r


def test_cross_request_catalogue_is_rejected(tmp_path,sdk_io):
    browser,_,_=sdk_io
    def runner(*a,**kw):
        from src.brain.work_tools import _ACTIVE,WorkBinding,bind_work,WorkResearchWriteTool
        binding,ledger,caps=_ACTIVE.get()
        foreign=WorkBinding(binding.root,binding.request_id,binding.session_id,'another-task')
        with bind_work(foreign,ledger,caps):
            assert not WorkResearchWriteTool().execute(**report_payload()).success
        return {}
    r=submit(tmp_path,browser,runner)
    assert r['status']=='failed' and not list(tmp_path.rglob('*.md'))


def test_report_independent_reopen_detects_changed_bytes(tmp_path,sdk_io,monkeypatch):
    from src.brain import work_service
    real=work_service.verify_artifacts
    def verify(binding,writes):
        artifacts=real(binding,writes)
        path=Path(artifacts[0]['path']); raw=path.read_bytes()
        path.write_bytes(raw.replace(b'\n',b'\r\n'))
        return artifacts
    monkeypatch.setattr(work_service,'verify_artifacts',verify)
    browser,_,_=sdk_io
    r=submit(tmp_path,browser,lambda *a,**kw:write_report())
    assert r['status']=='needs_attention' and 'readback' in r['error'],r


def test_native_react_uses_bound_report_with_real_sdk_collection(tmp_path,sdk_io,mock_jar):
    browser,calls,_=sdk_io
    _,runner,_,replies=mock_jar
    def authored(body):
        assert [kind for kind,_ in calls]==['search']+['get']*5
        return action(report_payload())
    replies.extend([authored,'{"final_answer":"saved"}'])
    r=submit(tmp_path,browser,runner)
    assert r['status']=='succeeded',r
    assert any(e.get('phase')=='research.compose' for e in r['trace'])


def test_preflight_budget_stops_before_starting_next_get(tmp_path,sdk_io,monkeypatch):
    from src.brain import work_research
    ticks=iter([0,0,121])
    monkeypatch.setattr(work_research.time,'monotonic',lambda:next(ticks))
    browser,calls,_=sdk_io
    r=submit(tmp_path,browser,lambda *a,**kw:pytest.fail('deadline reached model'))
    assert r['status']=='failed' and [kind for kind,_ in calls]==['search'],r


@pytest.mark.parametrize('bad',[True,'https://example.com/',[{'url':URLS[0]}],['https://user:password@example.com/']])
def test_source_url_schema_never_grants_authority(tmp_path,sdk_io,bad):
    browser,calls,_=sdk_io
    r=submit(tmp_path,browser,lambda *a,**kw:pytest.fail('invalid candidate reached model'),source_urls=bad)
    assert r['status']=='failed' and not calls and not r['artifacts'],r


@pytest.mark.parametrize('path',['../escape.md','C:/outside.md'])
def test_report_nested_writer_keeps_existing_path_boundary(tmp_path,sdk_io,path):
    browser,_,_=sdk_io
    def runner(*a,**kw):
        from src.brain.work_tools import WorkResearchWriteTool
        data=report_payload(); data['path']=path
        assert not WorkResearchWriteTool().execute(**data).success
        return {}
    r=submit(tmp_path,browser,runner)
    assert r['status']=='failed' and not r['artifacts'],r


def test_sdk_false_file_success_is_not_report_completion(tmp_path,sdk_io,monkeypatch):
    from openjarvis.tools.file_write import FileWriteTool
    from openjarvis.core.types import ToolResult
    monkeypatch.setattr(FileWriteTool,'execute',lambda *a,**kw:ToolResult(tool_name='file_write',success=True,content='claimed saved'))
    browser,_,_=sdk_io
    r=submit(tmp_path,browser,lambda *a,**kw:write_report())
    assert r['status']=='needs_attention' and not r['artifacts'],r


def test_optional_probe_does_not_waive_unexpected_adapter_error(tmp_path,sdk_io,monkeypatch):
    browser,_,_=sdk_io
    original=browser.fetch_public
    def broken(url):
        if url==URLS[0]: raise RuntimeError('unexpected adapter bug')
        return original(url)
    monkeypatch.setattr(browser,'fetch_public',broken)
    called=[]
    r=submit(tmp_path,browser,lambda *a,**kw:called.append(True) or {})
    assert r['status']=='failed' and not called,r


@pytest.mark.parametrize('source_count',[3,5])
def test_native_react_first_messages_include_nested_report_schema(tmp_path,sdk_io,mock_jar,source_count):
    browser,calls,_=sdk_io
    _,runner,bodies,replies=mock_jar
    replies.append('{"final_answer":"capture only; no file delivery"}')
    result=submit(tmp_path,browser,runner,source_urls=URLS[:source_count])
    first_messages = [(m['role'],m['content']) for m in bodies[0]['messages']]
    assert [kind for kind,_ in calls]==['search']+['get']*source_count
    assert result['status']=='failed' and not result['artifacts']
    assert not list(tmp_path.rglob('*.md'))
    system=next(content for role,content in first_messages if role=='system')
    # Inspect the actual first inference input built by real NativeReAct,
    # not WorkResearchWriteTool.spec.parameters or a mocked formatter.
    assert 'Full argument schema (JSON):\n' in system
    raw=system.split('Full argument schema (JSON):\n',1)[1].split('\nEnd argument schema.',1)[0]
    schema=json.loads(raw)
    section=schema['properties']['sections']
    assert section['type']=='array'
    alternatives=section['items']['anyOf']
    assert [a['properties']['source_id']['enum'][0] for a in alternatives]==['S'+str(i) for i in range(1,source_count+1)]
    for alt in alternatives:
        facts=alt['properties']['facts']
        assert facts['type']=='array' and facts['items']['type']=='object'
        assert set(facts['items']['required'])=={'claim','evidence_id'}



@pytest.fixture
def mock_jar(tmp_path,monkeypatch):
    import socket
    import httpx
    from openjarvis import Jarvis
    from openjarvis.core.config import JarvisConfig
    from openjarvis.engine.ollama import OllamaEngine
    from src.brain import agent_server
    monkeypatch.setattr(socket.socket,'connect',lambda *a: pytest.fail('real network'))
    monkeypatch.setenv('OPENJARVIS_HOME',str(tmp_path/'sdk'))
    bodies,answers=[],[]
    def handle(request):
        model = 'qwen3-8b-uncensored'
        if request.url.path == '/api/version':
            return httpx.Response(200,json={'version':'0.32.15'})
        if request.url.path == '/api/tags':
            return httpx.Response(200,json={'models':[{'name':model+':latest','digest':
                '6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'}]})
        assert request.url.path=='/api/chat'
        body = json.loads(request.content)
        bodies.append(body)
        reply=answers.pop(0)
        if callable(reply): reply=reply(body)
        if isinstance(reply,httpx.Response): return reply
        if 'issued:' in reply:
            alternatives=body['format']['anyOf'][0]['properties']['action_input']['properties']['sections']['items']['anyOf']
            for alt in alternatives:
                fields=alt['properties']
                reply=reply.replace('issued:'+fields['source_id']['enum'][0],fields['facts']['items']['properties']['evidence_id']['enum'][0])
        return httpx.Response(200,json={'model':model,'done':True,'done_reason':'stop','prompt_eval_count':25,
                              'eval_count':10,'message':{'role':'assistant','content':reply}})
    host='http://127.0.0.1:11434'
    raw=OllamaEngine(host=host)
    raw._client.close()
    def client():
        return httpx.Client(base_url=host,transport=httpx.MockTransport(handle),trust_env=False)
    raw._client=client()
    monkeypatch.setattr(agent_server,'_research_client',client,raising=False)
    monkeypatch.setattr(agent_server,'_research_manifest_digest',lambda:agent_server._RESEARCH_DIGEST,raising=False)
    cfg=JarvisConfig(); cfg.telemetry.enabled=False; cfg.analytics.enabled=False
    cfg.security.audit_log_path=str(tmp_path/'audit.db')
    cfg.security.capabilities.enabled=True
    cfg.agent.max_turns=5
    jar=Jarvis(config=cfg,engine_key='ollama',model=agent_server.MODEL)
    monkeypatch.setattr('openjarvis.sdk.get_engine',lambda *a:('ollama',raw))
    monkeypatch.setattr(agent_server,'_jars',jar)
    jar._ensure_engine()
    try:
        yield jar,agent_server._run_work_agent,bodies,answers
    finally:
        jar.close()


def test_source6_nested_action_and_final_only(tmp_path, sdk_io, mock_jar):
    _, runner, bodies, replies = mock_jar
    replies.extend([action(report_payload()), '{"final_answer":"saved"}'])
    result = submit(tmp_path, sdk_io[0], runner, text='original scope')
    assert result['status'] == 'succeeded', result['error']
    author, ack = bodies
    assert isinstance(author['format'], dict)
    assert author['format']['anyOf'][0]['properties']['action']['enum'] == ['ultima_work_research_write']
    assert ack['format']['required'] == ['final_answer']
    for body in bodies:
        assert body['truncate'] is False and body['shift'] is False and body['think'] is False
        assert body['options']['num_ctx'] == 16384 and body['options']['temperature'] == 0
        assert 'original scope' in str(body['messages'][1:])
        assert 'Final Answer:' not in body['messages'][0]['content']
    record = next(t['result'] for t in result['tool_results'] if t.get('call_id') and t['tool_name']=='ultima_work_research_write')
    assert record['protocol_version'] == 2
    assert len(record['bindings']) == 3


def test_source6_double_report_is_one_mutation(tmp_path, sdk_io):
    def twice(*a, **kw):
        write_report()
        from src.brain.work_tools import WorkResearchWriteTool
        second = WorkResearchWriteTool().execute(**dict(report_payload(), path='second.md'))
        assert not second.success
        return {}
    result = submit(tmp_path, sdk_io[0], twice)
    assert result['status'] == 'needs_attention'
    assert not list(tmp_path.rglob('second.md'))


def test_source6_only_bound_tool_and_frozen_capture(tmp_path, sdk_io):
    capture = {'available':True,'selection':'before','provenance':'original'}
    class Provider:
        def capture_work_context(self):
            return capture
        def release(self, value):
            pass
    browser = sdk_io[0]
    fetch = browser.fetch_public
    def mutate(url):
        capture['selection'] = 'after'
        return fetch(url)
    browser.fetch_public = mutate
    def inspect(prompt, **kw):
        assert kw['tools'] == ['ultima_work_research_write']
        assert 'before' in prompt and 'after' not in prompt and 'original' in prompt
        return write_report()
    result = WorkService(tmp_path, runner=inspect, browser_channel=browser, context_provider=Provider()).submit_work(
        'topic', request_id='r',session_id='s', context={'capture_current':True,'research':True})
    assert result['status'] == 'succeeded', result['error']


@pytest.mark.parametrize('remaining,ok', [(55,True),(54.9,False)])
def test_source6_admission_boundary(monkeypatch, remaining, ok):
    from src.brain import work_tools
    ledger = work_tools.WorkLedger()
    ledger.deadline = 260
    monkeypatch.setattr(work_tools, 'monotonic', lambda: 260-remaining, raising=False)
    if ok:
        ledger.admit_report()
    else:
        with pytest.raises(ValueError, match='deadline'):
            ledger.admit_report()


def action(payload):
    return json.dumps({'action':'ultima_work_research_write','action_input':payload})


def test_r4a_wire_scope(tmp_path,sdk_io,mock_jar):
    jar,runner,bodies,replies=mock_jar
    base=jar._engine
    final='{"final_answer":"done"}'
    replies.extend([final,action(report_payload()),final,final])
    jar.ask_full('ordinary before',agent='native_react',tools=['calculator'],context=False)
    result=submit(tmp_path,sdk_io[0],runner)
    jar.ask_full('ordinary after',agent='native_react',tools=['calculator'],context=False)
    assert result['status']=='succeeded',result['error']
    assert [type(b.get('format')) for b in bodies]==[type(None),dict,dict,type(None)]
    assert jar._engine is base and type(base._inner).__name__=='GuardrailsEngine'
    assert all(b['model']=='qwen3-8b-uncensored' for b in bodies)
    assert 'ultima_work_research_write' in bodies[1]['messages'][0]['content']
    assert 'calculator' not in bodies[1]['messages'][0]['content']
    assert sum(e['type']=='inference_end' for e in result['trace'])==2
    assert Path(result['artifacts'][0]['path']).is_file()


@pytest.mark.parametrize('invalid',['{"action":"calculator","action_input":{},"final_answer":"x"}',
                                    '{"final_answer":"1","final_answer":"2"}',
                                    '{"action":"calculator","action_input":"{}"}',
                                    '{"final_answer":NaN}','{"final_answer":','Final Answer: saved'])
def test_r4a_bad_final_after_write(tmp_path,sdk_io,mock_jar,invalid):
    _,runner,_,replies=mock_jar
    replies.extend([action(report_payload()),invalid])
    result=submit(tmp_path,sdk_io[0],runner)
    assert result['status']=='needs_attention' and not result['artifacts']
    assert any(e['type']=='inference_end' for e in result['trace'])
    write=next(x for x in result['tool_results'] if x.get('tool_name')=='ultima_work_file_write' and x['success'])
    assert Path(write['path']).read_text(encoding='utf8')==write['content']


def test_r4a_stop_on_rejection(tmp_path,sdk_io,mock_jar):
    _,runner,bodies,replies=mock_jar
    broken=report_payload()
    broken['sections'][-1]['facts']=[]
    replies.extend([action(broken),action(report_payload()),'{"final_answer":"done"}'])
    r=submit(tmp_path,sdk_io[0],runner)
    assert r['status']=='failed' and not list(tmp_path.rglob('research.md'))
    assert len(bodies)==1 and len(replies)==2
    starts=[e for e in r['trace'] if e['type']=='tool_call_start' and e.get('phase')=='research.compose']
    assert len(starts)==0
    assert not any(x.get('file_call_id') for x in r.get('research_effects',[]))


def test_r4a_unknown_dispatch(tmp_path,sdk_io,mock_jar):
    _,runner,bodies,replies=mock_jar
    replies.extend(['{"action":"missing_tool","action_input":{}}',action(report_payload()),'{"final_answer":"saved"}'])
    r=submit(tmp_path,sdk_io[0],runner)
    assert len(bodies)==1 and r['status']=='failed'
    assert not list(tmp_path.rglob('research.md'))


def test_r4b_candidate_boundaries(sdk_io):
    from src.brain.work_research import candidate_inputs
    explicit='https://example.com/资料，中文'
    target='https://example.com/资料/a%EF%BC%8Cb.ts'
    query,urls=candidate_inputs('查看 '+target+'，以及 https://sample.org/b?q=a,b&x=1。', [explicit])
    assert urls==[explicit,target,'https://sample.org/b?q=a,b&x=1']
    assert '以及' in query
    with pytest.raises(ValueError):
        candidate_inputs('read http://localhost/no，继续',[])


@pytest.mark.parametrize('n',[3,4,5])
def test_r4b_projection(n):
    from src.brain import work_research
    data=''.join('assigned_'+str(i)+' = create("value")\n' for i in range(1000))
    pack=work_research.source_pack([{'source_id':'S'+str(i),'text':data} for i in range(n)])
    assert len(pack)<=24000
    for item in json.loads(pack):
        lines=dict(item['lines'])
        assert item['omitted'] and lines[1].startswith('assigned_0') and 500 not in lines and 1000 in lines


@pytest.mark.parametrize('suffix,body,first,last,symbol,ok',[
    ('ts','return await this.queue.dispatch(item);',1,1,'this.queue.dispatch',True),
    ('ts','const out = await this.client.send(\n  item,\n  flags\n);',1,4,'this.client.send',True),
    ('js','let sink = new Writer(item);',1,1,'Writer',True),
    ('py','def run(self):\n    return self.queue.dispatch(item)',2,2,'self.queue.dispatch',True),
    ('ts','// new Writer(item);',1,1,'Writer',False),
    ('ts','const txt = "new Writer(item)";',1,1,'Writer',False),
    ('js','const txt = ' + chr(96) + 'new Writer(item)' + chr(96) + ';',1,1,'Writer',False),
    ('ts','const rx = /Writer\\(item\\)/;',1,1,'Writer',False),
    ('ts','Logger.warning("new Writer(item)");',1,1,'Writer',False),
    ('ts','declare function Writer(item: Item): Writer;',1,1,'Writer',False),
    ('ts','const a = await this.sink.dispatch(\n item\n);',1,2,'this.sink.dispatch',False),
    ('ts','const a = await this.sink.dispatch(item);',1,1,'dispatch',False),
    ('rb','Writer(item)',1,1,'Writer',False),
    ('ts','// not actually invoked\nconst w = new Writer(item);',1,1,'Writer',False),
])
def test_r4b_code_witness(suffix,body,first,last,symbol,ok):
    from src.brain.work_research import render_research_report
    sources=[]
    payload=report_payload()
    for i in range(1,4):
        sources.append(dict(source_id='S'+str(i),final_url='https://example.com/'+str(i)+'.'+suffix,
                            dedupe_url=str(i),decoded_body_sha256=str(i),text=body,body=body,
                            read_call_id='read'+str(i),request_id='r',session_id='s',task_id='t',
                            content_type='text/plain'))
        payload['sections'][i-1]['facts']=[dict(kind='code',claim='Delegates to '+symbol,
                                                first_line=first,last_line=last,symbol=symbol)]
    if ok:
        report=render_research_report(payload,json.dumps(sources))
        assert report.evidence[0]['text']==('\n'.join(body.splitlines()[first-1:last]))
    else:
        with pytest.raises(ValueError):
            render_research_report(payload,json.dumps(sources))


def test_r4b_partial_write(tmp_path,sdk_io,monkeypatch):
    from openjarvis.tools.file_write import FileWriteTool
    from openjarvis.core.types import ToolResult
    def partial(self,path,**kw):
        Path(path).write_bytes(b'partial')
        return ToolResult(tool_name='file_write',success=False,content='test SDK error after open')
    monkeypatch.setattr(FileWriteTool,'execute',partial)
    r=submit(tmp_path,sdk_io[0],lambda *a,**kw:write_report())
    assert r['status']=='needs_attention' and not r['artifacts']
    effect=next(x for x in r['research_effects'] if x.get('file_call_id'))
    assert effect['task_id']==r['task_id'] and effect['report_call_id']
    assert Path(effect['path']).read_bytes()==b'partial'


@pytest.mark.parametrize('stage',['before_intent','after_intent','r5_between_snapshots'])
def test_r4b_late_report(tmp_path,sdk_io,mock_jar,monkeypatch,stage):
    import concurrent.futures
    import threading
    from openjarvis.tools import _stubs
    from openjarvis.tools.file_write import FileWriteTool
    from src.brain.work_tools import WorkResearchWriteTool
    _,runner,bodies,replies=mock_jar
    entered=threading.Event()
    release=threading.Event()
    target=FileWriteTool if stage=='after_intent' else WorkResearchWriteTool
    name='execute' if stage=='after_intent' else 'run'
    real=getattr(target,name)
    def delayed(*args,**kw):
        entered.set()
        assert release.wait(10)
        return real(*args,**kw)
    monkeypatch.setattr(target,name,delayed)
    real_submit=_stubs._TOOL_RUNNER.submit
    actual=[]
    def dispatch(function,**kw):
        future=real_submit(function,**kw)
        if function.__self__.tool_id!='ultima_work_research_write': return future
        actual.append(future)
        class Expired:
            def result(self,timeout):
                assert entered.wait(3)
                raise concurrent.futures.TimeoutError()
            def cancel(self): return future.cancel()
        return Expired()
    monkeypatch.setattr(_stubs._TOOL_RUNNER,'submit',dispatch)
    if stage=='r5_between_snapshots':
        # Deliver the actual SDK timeout response. On reading the compose error,
        # allow the original worker to finish before the service handles it.
        original_runner=runner
        class TimeoutResponse(dict):
            def __getitem__(self,key):
                if key=='compose_error':
                    release.set()
                    actual[0].result(timeout=5)
                return super().__getitem__(key)
        def runner(*args,**kwargs):
            return TimeoutResponse(original_runner(*args,**kwargs))
    replies.extend([action(report_payload()),'{"final_answer":"no file"}'])
    try:
        r=submit(tmp_path,sdk_io[0],runner)
        assert r['status']=='needs_attention' and len(bodies)==1
        effect=r['research_effects'][0]
        assert effect['state']=='timed_out'
        if stage=='r5_between_snapshots':
            assert actual[0].done() and Path(effect['path']).is_file()
            terminal=[x for x in r['tool_results'] if x.get('call_id') and x.get('tool_name')=='ultima_work_file_write']
            assert [x['call_id'] for x in terminal]==([effect['file_call_id']] if effect.get('file_call_id') else [])
        else:
            assert bool(effect.get('file_call_id'))==(stage=='after_intent')
        snapshot=json.dumps(r,sort_keys=True)
        other=submit(tmp_path,sdk_io[0],runner)
        assert other['task_id']!=r['task_id'] and not other.get('research_effects')
    finally:
        release.set()
        if actual: actual[0].result(timeout=5)
    assert json.dumps(r,sort_keys=True)==snapshot
    assert Path(effect['path']).read_text(encoding='utf8').startswith('# Model title')
    assert not list((tmp_path/other['task_id']).glob('*.md'))



@pytest.mark.parametrize('backend',[None,'other'])
def test_r4_unresolved_backend_refuses_before_inference(tmp_path,sdk_io,mock_jar,backend):
    jar,runner,bodies,_=mock_jar
    jar._resolved_engine_key=backend
    r=submit(tmp_path,sdk_io[0],runner)
    assert r['status']=='failed' and 'Unsupported structured research' in r['error']
    assert not bodies and not list(tmp_path.rglob('research.md'))


@pytest.mark.parametrize('first,last',[(True,1),(1,False),(0,1),(2,1),(1,9),(1001,1001),(500,500)])
def test_r4_invalid_or_invisible_span(tmp_path,sdk_io,first,last):
    from src.brain.work_research import _fact_evidence, _source_view
    src=dict(text=''.join('description line '+str(i)+'\n' for i in range(1000)),source_id='S1')
    visible=dict(_source_view(src,5)['lines'])
    with pytest.raises(ValueError,match='Invalid or omitted'):
        _fact_evidence(dict(kind='documented',claim='A fact',first_line=first,last_line=last),src,visible)


def test_r4_projected_html_evidence(tmp_path,sdk_io,monkeypatch):
    import httpx
    from src.brain import work_service
    def get(method,url,**kw):
        return httpx.Response(200,headers={'content-type':'text/html'},text='<p>Visible listing '+url+'</p>',
                              request=httpx.Request(method,url))
    monkeypatch.setattr(httpx,'request',get)
    r=submit(tmp_path,sdk_io[0],lambda *a,**kw:write_report())
    assert r['status']=='succeeded'
    record=next(t for t in r['tool_results'] if t.get('tool_name')=='ultima_work_research_write')
    evidence=record['result']['evidence'][0]
    assert evidence['text']==r['sources'][0]['text'] and '<p>' not in evidence['text']
    assert evidence['request_id']==r['request_id'] and evidence['read_call_id']==r['sources'][0]['read_call_id']


def test_r4_limitations_are_local_claims():
    from src.brain.work_research import _fact_evidence
    body='if (key) {\n // TODO: wire transport\n Logger.warning("not implemented");\n}'
    src=dict(text=body,body=body,source_id='S1',final_url='https://example.com/file.ts',
             decoded_body_sha256='test',read_call_id='read',request_id='r',session_id='s',task_id='t')
    visible=dict(enumerate(body.splitlines(),1))
    for i in (2,3):
        support=_fact_evidence(dict(kind='limitation',claim='Branch records a limitation',
                                    first_line=i,last_line=i),src,visible)
        assert support['text']==visible[i]
    with pytest.raises(ValueError,match='documentation'):
        _fact_evidence(dict(kind='documented',claim='Fully implemented',first_line=2,last_line=2),src,visible)


def test_r4_max_turns_after_committed_write(tmp_path,sdk_io,mock_jar):
    jar,runner,bodies,replies=mock_jar
    jar.config.agent.max_turns=1
    replies.append(action(report_payload()))
    r=submit(tmp_path,sdk_io[0],runner)
    assert r['status']=='needs_attention' and len(bodies)==1 and not r['artifacts']
    assert 'final envelope' in r['error'] and len(list(tmp_path.rglob('research.md')))==1


def test_r4_research_exception_does_not_leak_to_ordinary(tmp_path,sdk_io,mock_jar):
    jar,runner,bodies,replies=mock_jar
    replies.extend(['not json','{"final_answer":"normal"}'])
    assert submit(tmp_path,sdk_io[0],runner)['status']=='failed'
    jar.ask_full('ordinary',agent='native_react',tools=['calculator'],context=False)
    assert isinstance(bodies[0]['format'],dict) and 'format' not in bodies[1]


def test_r4_exact_named_symbol_and_explicit_failure():
    from src.brain.work_research import _fact_evidence
    body='const x = new Writer(item);\nthrow new Error("missing");'
    src=dict(text=body,body=body,source_id='S1',final_url='https://example.com/file.ts',
             decoded_body_sha256='test',read_call_id='read',request_id='r',session_id='s',task_id='t')
    visible=dict(enumerate(body.splitlines(),1))
    with pytest.raises(ValueError,match='exact operation'):
        _fact_evidence(dict(kind='code',claim='Uses AnotherWriter',symbol='Writer',first_line=1,last_line=1),src,visible)
    assert _fact_evidence(dict(kind='limitation',claim='This branch throws',first_line=2,last_line=2),src,visible)['text']==visible[2]


def r5_witness(suffix,body,first,last,symbol='queue.dispatch',projection=None):
    import hashlib
    from src.brain.work_research import source_pack, _fact_evidence
    source=dict(source_id='S1',final_url='https://example.com/queue.'+suffix,
                text=body if projection is None else projection,body=body,
                decoded_body_sha256=hashlib.sha256(body.encode()).hexdigest(),
                read_call_id='read',request_id='r',session_id='s',task_id='t')
    lines=dict(json.loads(source_pack([source]))[0]['lines'])
    return _fact_evidence(dict(kind='code',claim='Calls '+symbol,symbol=symbol,
                               first_line=first,last_line=last),source,lines)


@pytest.mark.parametrize('suffix',['js','mjs','cjs','ts'])
@pytest.mark.parametrize('opening',['class Queue {','const queue = {'])
def test_r5_method_header_is_not_a_call(suffix,opening):
    with pytest.raises(ValueError):
        r5_witness(suffix,opening+'\n  dispatch(item)\n  /* method body */\n  { return item; }\n}',2,2,'dispatch')


@pytest.mark.parametrize('body,symbol',[
    ('interface Queue {\n  dispatch(item)\n  : void;\n}', 'dispatch'),
    ('const run = () => {\n  return queue.dispatch(item)\n    .then(done);\n}', 'queue.dispatch'),
    ('function run() {\n  queue.dispatch(item)\n    (other);\n}', 'queue.dispatch'),
])
def test_r5_incomplete_statement(body,symbol):
    with pytest.raises(ValueError):
        r5_witness('ts',body,2,2,symbol)


@pytest.mark.parametrize('suffix,body',[
    ('py','# head\f# note\nx = queue.dispatch(item)'),
    ('js','// heading\u2028// note\nconst x = queue.dispatch(item);'),
])
def test_r5_comment_cannot_prove_call_on_different_line(suffix,body):
    with pytest.raises(ValueError):
        r5_witness(suffix,body,2,2)


def test_r5_extracted_html_text_cannot_prove_a_source_statement():
    with pytest.raises(ValueError):
        r5_witness('js','<p>queue.dispatch(item);</p>',1,1,projection='queue.dispatch(item);')


@pytest.mark.parametrize('newline',['\n','\r\n'],ids=['lf','crlf'])
@pytest.mark.parametrize('suffix,lines',[
    ('js',['async function run() {','  return await queue.dispatch(','    item);','}']),
    ('ts',['async function run() {','  const x = await queue.dispatch(','    item);','}']),
    ('py',['async def run():','    return await queue.dispatch(','        item)']),
])
def test_r5_complete_statement_and_raw_identity(newline,suffix,lines):
    import hashlib
    body=newline.join(lines)
    with pytest.raises(ValueError):
        r5_witness(suffix,body,2,2)
    evidence=r5_witness(suffix,body,2,3)
    assert evidence['text']=='\n'.join(lines[1:3])
    assert evidence['decoded_body_sha256']==hashlib.sha256(body.encode()).hexdigest()


def test_r5_completed_report_includes_sdk_result_and_effect(tmp_path,sdk_io,mock_jar):
    _,runner,bodies,replies=mock_jar
    replies.extend([action(report_payload()),'{"final_answer":"done"}'])
    returned_sdk=[]
    def observe(*args,**kwargs):
        response=runner(*args,**kwargs)
        returned_sdk.extend(response['tool_results'])
        return response
    r=submit(tmp_path,sdk_io[0],observe)
    assert r['status']=='succeeded' and len(bodies)==2
    assert returned_sdk and [t for t in r['tool_results'] if not t.get('call_id')]==returned_sdk
    effect,=r['research_effects']
    assert effect['state']=='completed' and effect['task_id']==r['task_id']
    for tool,key in [('ultima_work_file_write','file_call_id'),('ultima_work_research_write','report_call_id')]:
        terminal,=[t for t in r['tool_results'] if t.get('tool_name')==tool and t.get('call_id')]
        assert terminal['success'] and terminal['call_id']==effect[key]
    assert effect['path']==r['artifacts'][0]['path']

@pytest.mark.parametrize('fault',['version','digest','manifest','credential','wrapper','origin','raw-coercion','duplicate','nonfinite',
                                  'native-tool','length','model','empty','overflow','ack-overflow'])
def test_source6_native_boundary(tmp_path,sdk_io,mock_jar,monkeypatch,fault):
    import httpx
    from src.brain import agent_server
    jar,runner,bodies,replies=mock_jar
    original=agent_server._research_client
    paths=[]
    def issued():
        client=original()
        get=client.get
        def metadata(path):
            paths.append(path)
            if fault=='version' and path=='/api/version' or fault=='digest' and path=='/api/tags':
                return httpx.Response(200,json={'version':'0.32.14','models':[]},request=httpx.Request('GET','http://test'))
            return get(path)
        client.get=metadata
        return client
    monkeypatch.setattr(agent_server,'_research_client',issued)
    if fault=='manifest': monkeypatch.setattr(agent_server,'_research_manifest_digest',lambda:'changed',raising=False)
    if fault=='credential': monkeypatch.setenv('OLLAMA_API_KEY','')
    if fault=='origin': monkeypatch.setattr(jar._engine._inner._engine,'_host','http://localhost:11433')
    if fault=='wrapper': monkeypatch.setattr(jar._engine._inner,'_engine',object())
    native=dict(model='qwen3-8b-uncensored',done=True,done_reason='stop',prompt_eval_count=100,eval_count=10,
                message=dict(role='assistant',content='{"final_answer":"ok"}'))
    if fault=='raw-coercion': native['done']=1
    if fault=='native-tool': native['message']['tool_calls']=[{'function':{'name':'tool'}}]
    if fault=='length': native['done_reason']='length'
    if fault=='model': native['model']='wrong'
    if fault=='empty': native['message']['content']=' '
    entity=json.dumps(native)
    if fault=='duplicate': entity='{"done":false,'+entity[1:]
    if fault=='nonfinite': entity='{"extension":1e999,'+entity[1:]
    if fault=='ack-overflow': replies.append(action(report_payload()))
    replies.append(httpx.Response(400 if 'overflow' in fault else 200,content=entity))
    r=submit(tmp_path,sdk_io[0],runner,text='漢'*2500)
    assert r['status']==('needs_attention' if fault=='ack-overflow' else 'failed')
    expected=0 if fault in ('version','digest','manifest','credential','origin','wrapper') else 2 if fault=='ack-overflow' else 1
    assert len(bodies)==expected
    if expected:
        assert paths==['/api/version','/api/tags']*expected
        assert all(b['truncate'] is False and b['shift'] is False for b in bodies)
        assert '漢'*2500 in bodies[0]['messages'][1]['content']
    assert len(list(tmp_path.rglob('research.md')))==int(fault=='ack-overflow')
    assert not any(e['type']=='inference_end' for e in r['trace'] if e.get('phase')=='research.compose') or fault=='ack-overflow'


@pytest.mark.parametrize('stage',['after-action','worker','pre-intent','equal'])
def test_source6_real_admission(tmp_path,sdk_io,mock_jar,monkeypatch,stage):
    from src.brain import work_tools,work_service
    _,runner,bodies,replies=mock_jar
    now=[0]
    monkeypatch.setattr(work_service,'monotonic',lambda:0)
    monkeypatch.setattr(work_tools,'monotonic',lambda:now[0])
    now[0]=205 if stage=='equal' else 204
    def authored(body):
        if stage=='after-action': now[0]+=24
        return action(report_payload())
    if stage=='worker':
        original=work_tools.WorkResearchWriteTool.run
        def delayed(*a,**k):
            now[0]=205.1
            return original(*a,**k)
        monkeypatch.setattr(work_tools.WorkResearchWriteTool,'run',delayed)
    if stage=='pre-intent':
        original=work_tools.checked_path
        def delayed(binding,path):
            resolved=original(binding,path)
            if isinstance(path,str) and path.endswith('research.md') and Path(path).is_absolute():
                now[0]=205.1
            return resolved
        monkeypatch.setattr(work_tools,'checked_path',delayed)
    replies.extend([authored,'{"final_answer":"saved"}'])
    r=submit(tmp_path,sdk_io[0],runner)
    assert r['status']==('succeeded' if stage=='equal' else 'failed'),r['error']
    assert len(bodies)==(2 if stage=='equal' else 1)
    if stage!='equal':
        assert not any(e.get('file_call_id') for e in r.get('research_effects',[]))
        assert not list(tmp_path.rglob('research.md'))


@pytest.mark.parametrize('gate',['policy','rate'])
def test_source6_executor_denies_before_write(tmp_path,sdk_io,mock_jar,monkeypatch,gate):
    jar,runner,bodies,replies=mock_jar
    checked=[]
    def deny(*args):
        checked.append(args)
        return False if gate=='policy' else (False,10)
    monkeypatch.setattr(jar._capability_policy if gate=='policy' else jar._rate_limiter,'check',deny)
    replies.append(action(report_payload()))
    r=submit(tmp_path,sdk_io[0],runner)
    assert checked and r['status']=='failed' and len(bodies)==1
    assert not list(tmp_path.rglob('research.md'))


@pytest.mark.parametrize('stage',['input','output','oversize','expanded'])
def test_source6_secured_material(tmp_path,sdk_io,mock_jar,monkeypatch,stage):
    jar,runner,bodies,replies=mock_jar
    material='private@example.test'
    if stage=='oversize': material='x'*80000
    if stage=='expanded':
        monkeypatch.setattr(jar._engine._inner._scanners[0],'redact',lambda s:'x'*80000)
    replies.extend([action(report_payload()),'{"final_answer":"contact private@example.test"}'])
    r=submit(tmp_path,sdk_io[0],runner,text=material)
    if stage in ('oversize','expanded'):
        assert not bodies and r['status']=='failed'
    else:
        assert r['status']=='succeeded'
        assert all(material not in b['messages'][1]['content'] and 'REDACTED' in b['messages'][1]['content'] for b in bodies)
        assert material not in r['content'] and 'REDACTED' in r['content']


def test_source6_reference_membership_and_readback(tmp_path,sdk_io):
    from src.brain.work_tools import _ACTIVE,WorkResearchWriteTool
    from src.brain.work_research import reference_cards,resolve_references
    def check(*a,**kw):
        _,_,caps=_ACTIVE.get()
        table=reference_cards(caps.research_json)
        payload=report_payload()
        foreign=json.loads(caps.research_json)
        for source in foreign: source['task_id']='other'
        foreign_cards=reference_cards(json.dumps(foreign))
        assert set(foreign_cards).isdisjoint(table)
        import jsonschema
        for key in ('not-issued',next(iter(foreign_cards)),next(k for k,c in table.items() if c['source_id']=='S2')):
            data=json.loads(json.dumps(payload))
            data['sections'][0]['facts'][0]['evidence_id']=key
            with pytest.raises(jsonschema.ValidationError):
                resolve_references(data,table,caps.research_json)
        return write_report()
    result=submit(tmp_path,sdk_io[0],check)
    assert result['status']=='succeeded',result['error']

@pytest.mark.parametrize('fault',['unknown-version','missing-version','altered-submission','altered-binding','body','url'])
def test_source6_reopen_validates_reference_protocol(tmp_path,sdk_io,fault):
    from src.brain.work_tools import WorkBinding
    from src.brain.work_research import verify_research_artifacts
    result=submit(tmp_path,sdk_io[0],lambda *a,**kw:write_report())
    assert result['status']=='succeeded'
    artifact,=result['artifacts']
    binding=WorkBinding(Path(artifact['path']).parent,'r','s',result['task_id'])
    record=next(r for r in result['tool_results'] if r.get('tool_name')=='ultima_work_research_write')
    receipt=record['result']
    if fault=='unknown-version': receipt['protocol_version']=999
    if fault=='missing-version': receipt.pop('protocol_version')
    if fault=='altered-submission':
        original=json.loads(receipt['submitted_json'])
        original['sections'][0]['facts'][0]['claim']='Changed prose'
        receipt['submitted_json']=json.dumps(original)
    if fault=='altered-binding': receipt['bindings'][0]['citation_first']+=1
    if fault=='body': result['available_sources'][0]['body']+=' changed'
    if fault=='url': result['available_sources'][0]['final_url']='https://example.com/other'
    from jsonschema import ValidationError
    with pytest.raises((ValueError,ValidationError)):
        verify_research_artifacts(binding,[artifact],[record],json.dumps(result['available_sources']),require_reference=True)

def test_source6_lock_wait_uses_entry_deadline(tmp_path,sdk_io,mock_jar,monkeypatch):
    from src.brain import agent_server
    _,runner,bodies,_=mock_jar
    waits=[]
    class Busy:
        def acquire(self,timeout):
            waits.append(timeout)
            return False
    monkeypatch.setattr(agent_server,'_ask_lock',Busy())
    r=submit(tmp_path,sdk_io[0],runner)
    assert r['status']=='failed' and 'deadline' in r['error'] and not bodies
    assert len(waits)==1 and 0 < waits[0] <= 205

@pytest.mark.parametrize('allowance', [-1, -999, 0, True, 12.5, '15'])
def test_source7_refuses_invalid_allowance_before_native_generation(tmp_path, sdk_io, mock_jar, allowance):
    _, runner, bodies, replies = mock_jar
    replies.append('{"final_answer":"refusal"}')
    result = WorkService(tmp_path, runner=runner, browser_channel=sdk_io[0]).submit_work(
        'Research a subject', request_id='r', session_id='s', context={'research':True}, max_tokens=allowance)
    assert result['status']=='failed' and not bodies
    assert 'positive integer' in result['error']
    assert not result.get('research_effects')


@pytest.mark.parametrize('allowance,expected', [(None,[2048,512]),(32,[32,32]),(8192,[4096,512])])
def test_source7_bounded_native_author_and_ack(tmp_path, sdk_io, mock_jar, allowance, expected):
    _, runner, bodies, replies = mock_jar
    replies.extend([action(report_payload()),'{"final_answer":"saved"}'])
    result = WorkService(tmp_path, runner=runner, browser_channel=sdk_io[0]).submit_work(
        'Research a subject', request_id='r',session_id='s',context={'research':True},max_tokens=allowance)
    assert result['status']=='succeeded', result['error']
    assert [b['options']['num_predict'] for b in bodies]==expected


@pytest.mark.parametrize('allowance', [True, 12.5, '15'])
def test_source7_http_research_refuses_coercion(monkeypatch, allowance):
    import io
    from types import SimpleNamespace
    from src.brain import agent_server
    body=json.dumps(dict(mode='work',query='topic',context={'research':True},max_tokens=allowance)).encode()
    replies=[]
    handler=SimpleNamespace(path='/ask', headers={'Content-Length':str(len(body))},rfile=io.BytesIO(body),
                            _send_json=lambda status,result: replies.append((status,result)))
    monkeypatch.setattr(agent_server,'_work_service',None)
    agent_server._Handler.do_POST(handler)
    assert replies[0][0]==400


@pytest.mark.parametrize('suffix',['js','ts'])
@pytest.mark.parametrize('statement,kind,operation',[
    ('const result =\n  queue.dispatch(item);','code','queue.dispatch'),
    ('const result =\n  logger.warn(item);','limitation','logger.warn'),
    ('throw new\n  TypeError(item);','limitation','TypeError'),
])
def test_source7_split_prefix_issued_and_reopened(tmp_path,sdk_io,monkeypatch,suffix,statement,kind,operation):
    import httpx
    from src.brain.work_research import _js_support
    from src.brain.work_tools import WorkResearchWriteTool
    code='https://example.com/example.'+suffix
    urls=[code,*URLS[:2]]
    def fetch(method,url,**kw):
        text=statement if url==code else 'Document '+url
        return httpx.Response(200,headers={'content-type':'text/plain'},text=text,request=httpx.Request(method,url))
    monkeypatch.setattr(httpx,'request',fetch)
    def write(*a,**kw):
        tool=WorkResearchWriteTool()
        refs=[(k,v) for k,v in tool.cards.items() if v['source_id']=='S1' and v['kind']==kind]
        assert len(refs)==1
        key,card=refs[0]
        assert (card['first_line'],card['last_line'])==(1,2)
        payload=report_payload()
        payload['sections'][0]['facts']=[dict(evidence_id=key,claim='Observed '+operation)]
        assert tool.execute(**payload).success
        return {}
    r=submit(tmp_path,sdk_io[0],write,source_urls=urls)
    assert r['status']=='succeeded',r['error']
    rec=next(t['result'] for t in r['tool_results'] if t.get('tool_name')=='ultima_work_research_write')
    assert rec['evidence'][0]['text']==statement
    assert Path(r['artifacts'][0]['path']).read_text(encoding='utf8').find('Observed '+operation)>=0
    assert not _js_support(statement,2,2,kind,operation,'.'+suffix)
