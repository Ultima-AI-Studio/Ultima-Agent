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
    return dict(path='research.md',title='Model title',sections=[dict(source_id='S'+str(i),heading='Section '+str(i),facts=['Model-generated fact '+str(i)]) for i in range(1,count+1)])


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


def test_native_react_uses_bound_report_with_real_sdk_collection(tmp_path,sdk_io,monkeypatch):
    from openjarvis import Jarvis
    from openjarvis.core.config import JarvisConfig
    from src.brain import agent_server
    browser,calls,_=sdk_io
    class Engine:
        engine_id='deterministic-inference-only'
        def generate(self,messages,**kw):
            assert [kind for kind,_ in calls]==['search']+['get']*5
            action={'action':'ultima_work_research_write','action_input':report_payload()} if len(messages)<=2 else {'final_answer':'saved'}
            return {'content':json.dumps(action)}
    config=JarvisConfig(); config.telemetry.enabled=False
    jar=Jarvis(config=config,model='qwen3-8b-uncensored'); jar._engine=Engine()
    monkeypatch.setattr(agent_server,'_jars',jar)
    r=submit(tmp_path,browser,agent_server._run_work_agent)
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
def test_native_react_first_messages_include_nested_report_schema(tmp_path,sdk_io,monkeypatch,source_count):
    from openjarvis import Jarvis
    from openjarvis.core.config import JarvisConfig
    from src.brain import agent_server
    browser,calls,_=sdk_io
    first_messages=[]
    class CaptureEngine:
        engine_id='first-message-capture-only'
        def generate(self,messages,**kwargs):
            assert not first_messages
            first_messages.extend((message.role.value,message.content) for message in messages)
            return {'content':json.dumps({'final_answer':'capture only; no file delivery'})}
    config=JarvisConfig(); config.telemetry.enabled=False
    jar=Jarvis(config=config,model='qwen3-8b-uncensored'); jar._engine=CaptureEngine()
    monkeypatch.setattr(agent_server,'_jars',jar)
    result=submit(tmp_path,browser,agent_server._run_work_agent,source_urls=URLS[:source_count])
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
    nested=section['items']['properties']
    assert nested['facts']['type']=='array' and nested['facts']['items']['type']=='string'
    assert nested['source_id']['enum']==['S'+str(i) for i in range(1,source_count+1)]
