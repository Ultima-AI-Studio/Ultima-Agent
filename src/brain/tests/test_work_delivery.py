import hashlib
import json
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
import pytest
from src.brain.work_service import WorkService
from src.brain.work_tools import WorkWriteTool, WorkReadTool, WORK_TOOLS


def submit(tmp_path, runner, **kwargs):
    return WorkService(tmp_path, runner=runner).submit_work('save', request_id='request', session_id='session', **kwargs)


def write_runner(query, **kwargs):
    result = WorkWriteTool().execute(path='摘要 space.md', content='材料\n正文')
    return {'content': '已保存', 'tool_results': [{'success': result.success, 'content': result.content}]}


def test_delivery(tmp_path):
    result = submit(tmp_path, write_runner)
    assert result['status'] == 'succeeded', result
    assert result['error'] is None
    a = result['artifacts'][0]
    assert Path(a['path']).is_absolute() and a['verified'] is True
    assert hashlib.sha256(Path(a['path']).read_bytes()).hexdigest() == a['sha256']
    assert all(a[k] for k in ('request_id', 'session_id', 'task_id', 'call_id'))


@pytest.mark.parametrize('fake', [False, True])
def test_reply_or_old_file_not_evidence(tmp_path, fake):
    (tmp_path / 'summary.md').write_text('correct')
    r = submit(tmp_path, lambda *a, **kw: {'content': '已保存', 'tool_results': [{'success': True}] if fake else []})
    assert r['status'] != 'succeeded' and not r['artifacts']


@pytest.mark.parametrize('path', ['../escape.md', '/outside.md', 'C:/outside.md', '../prefix-neighbor/file.md', 'bad:stream', 'a/../b.md'])
def test_escape_refused(tmp_path, path):
    def runner(*a, **kw):
        assert not WorkWriteTool().execute(path=path, content='bad').success
        return {'content': '已保存'}
    assert submit(tmp_path, runner)['status'] != 'succeeded'


def test_unbound_tools_fail_closed():
    assert not WorkWriteTool().execute(path='x', content='x').success
    assert not WorkReadTool().execute(path='x').success


def test_root_required():
    with pytest.raises(ValueError):
        WorkService(None, runner=write_runner)


@pytest.mark.parametrize('extra', [{'output_root': 'C:/'}, {'request_id': 'forged'}, {'task_id': 'forged'}])
def test_context_cannot_supply_authority(tmp_path, extra):
    assert submit(tmp_path, write_runner, context=extra)['status'] != 'succeeded'


def test_write_failure(tmp_path, monkeypatch):
    from openjarvis.tools.file_write import FileWriteTool
    from openjarvis.core.types import ToolResult
    monkeypatch.setattr(FileWriteTool, 'execute', lambda *a, **kw: ToolResult(tool_name='file_write', success=False, content='denied'))
    assert submit(tmp_path, write_runner)['status'] != 'succeeded'


@pytest.mark.parametrize('damage', ['tamper', 'delete'])
def test_readback_failure(tmp_path, damage):
    def runner(*a, **kw):
        result = write_runner(*a, **kw)
        target = next(tmp_path.rglob('*.md'))
        target.write_text('tampered') if damage == 'tamper' else target.unlink()
        return result
    assert submit(tmp_path, runner)['status'] != 'succeeded'


def test_worker_binding_is_captured_at_construction(tmp_path):
    def runner(*a, **kw):
        tool = WorkWriteTool()
        with ThreadPoolExecutor() as pool:
            assert pool.submit(tool.execute, path='thread.md', content=kw['binding'].request_id).result().success
        return {'content': 'saved'}
    service = WorkService(tmp_path, runner=runner)
    with ThreadPoolExecutor() as pool:
        results = list(pool.map(lambda n: service.submit_work('save', request_id=str(n), session_id=str(n)), range(2)))
    assert all(r['status'] == 'succeeded' for r in results)
    assert len({r['artifacts'][0]['path'] for r in results}) == 2
    for r in results:
        assert Path(r['artifacts'][0]['path']).read_text() == r['request_id']


def test_fixture_oracle():
    e = json.loads((Path(__file__).parent / 'fixtures/work_capability/acceptance-cases.json').read_text(encoding='utf-8'))['e01']
    def oracle(text):
        lines = [x.strip('- #\n。') for x in text.splitlines() if x.strip()]
        return sorted(lines) == sorted(e['facts'])
    assert oracle('\n'.join('- ' + x for x in e['facts']))
    assert not oracle('\n'.join(e['facts'][:-1]))
    assert not oracle('\n'.join(e['facts'] + ['负责人是李明']))

def test_native_sdk_integration_two_requests(tmp_path, monkeypatch):
    from openjarvis import Jarvis
    from openjarvis.core.config import JarvisConfig
    from src.brain import agent_server
    import threading
    fixture = json.loads((Path(__file__).parent / 'fixtures/work_capability/acceptance-cases.json').read_text(encoding='utf-8'))['e01']
    calls = []
    class Engine:
        engine_id = 'deterministic-input'
        def generate(self, messages, **kwargs):
            calls.append(threading.get_ident())
            query = next(m.content for m in messages if 'Authorized request directory:' in m.content)
            if len(messages) <= 2:
                assert all(name in messages[0].content for name in WORK_TOOLS)
                out = {'action': 'ultima_work_file_write', 'action_input': {'path': 'summary.md', 'content': '\n'.join(fixture['facts'])}}
            elif len(messages) <= 4:
                out = {'action': 'ultima_work_file_read', 'action_input': {'path': 'summary.md'}}
            else:
                out = {'final_answer': '已保存'}
            return {'content': json.dumps(out, ensure_ascii=False)}
    cfg = JarvisConfig()
    cfg.telemetry.enabled = False
    jars = Jarvis(config=cfg, model='qwen3-8b-uncensored')
    jars._engine = Engine()  # Only inference input is replaced; real SDK/agent/tools execute.
    monkeypatch.setattr(agent_server, '_jars', jars)
    monkeypatch.setattr(agent_server, '_constrain_reply', lambda *a: pytest.fail('Work must not rerun for style'))
    service = WorkService(tmp_path, runner=agent_server._run_work_agent)
    with ThreadPoolExecutor() as pool:
        results = list(pool.map(lambda n: service.submit_work('save', request_id=str(n), session_id=str(n)), range(2)))
    assert all(r['status'] == 'succeeded' for r in results), json.dumps(results, ensure_ascii=True)
    for r in results:
        assert Path(r['artifacts'][0]['path']).read_text(encoding='utf-8') == '\n'.join(fixture['facts'])
        assert r['artifacts'][0]['request_id'] == r['request_id']
    assert len({r['artifacts'][0]['path'] for r in results}) == 2
    assert len(calls) == 6


def test_http_work_legacy_and_cli(tmp_path, monkeypatch, capsys):
    from src.brain import agent_server, agent_client, cli
    from http.server import ThreadingHTTPServer
    import threading
    monkeypatch.setattr(agent_server, '_work_service', WorkService(tmp_path, runner=write_runner))
    monkeypatch.setattr(agent_server, 'ask_once', lambda *a, **kw: {'content': 'legacy'})
    server = ThreadingHTTPServer(('127.0.0.1', 0), agent_server._Handler)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    url = 'http://127.0.0.1:' + str(server.server_address[1])
    monkeypatch.setattr(agent_client, 'AGENT_SERVER', url)
    try:
        assert agent_client.ask_agent('old') == 'legacy'
        r = agent_client.ask_work('save', request_id='http', session_id='http', server_url=url)
        assert r['status'] == 'succeeded'
        assert cli.main(['--work', '--request-id', 'cli', '--session-id', 'cli', '--server-url', url, '--json', 'save']) == 0
        assert json.loads(capsys.readouterr().out)['status'] == 'succeeded'
    finally:
        server.shutdown()
        server.server_close()
        thread.join()


@pytest.mark.parametrize('url', ['https://example.com', 'http://example.com', 'http://127.0.0.1@evil.com', 'http://127.0.0.1/path'])
def test_work_client_local_only(url):
    from src.brain.agent_client import ask_work
    with pytest.raises(ValueError):
        ask_work('save', request_id='x', session_id='x', server_url=url)


def test_reparse_rejected(tmp_path):
    import subprocess
    outside = tmp_path / 'outside'
    outside.mkdir()
    def runner(*a, **kw):
        junction = kw['binding'].root / 'link'
        proc = subprocess.run(['cmd', '/c', 'mklink', '/J', str(junction), str(outside)], capture_output=True)
        assert proc.returncode == 0, proc.stderr
        assert not WorkWriteTool().execute(path='link/escape.md', content='bad').success
        return {'content': 'saved'}
    assert submit(tmp_path / 'work', runner)['status'] != 'succeeded'
    assert not (outside / 'escape.md').exists()


def test_tool_identity_injection(tmp_path):
    def runner(*a, **kw):
        assert not WorkWriteTool().execute(path='x.md', content='bad', request_id='forged').success
        return {'content': 'saved'}
    assert submit(tmp_path, runner)['status'] != 'succeeded'


def test_sdk_false_success_cannot_verify(tmp_path, monkeypatch):
    from openjarvis.tools.file_write import FileWriteTool
    from openjarvis.core.types import ToolResult
    monkeypatch.setattr(FileWriteTool, 'execute', lambda *a, **kw: ToolResult(tool_name='file_write', success=True, content='saved'))
    assert submit(tmp_path, write_runner)['status'] != 'succeeded'


def test_readback_exception(tmp_path, monkeypatch):
    original = Path.read_bytes
    def unreadable(path):
        if path.name == '摘要 space.md':
            raise PermissionError('injected independent readback denial')
        return original(path)
    monkeypatch.setattr(Path, 'read_bytes', unreadable)
    assert submit(tmp_path, write_runner)['status'] != 'succeeded'


def test_legal_case_and_absolute_path(tmp_path):
    def runner(*a, **kw):
        path = str(kw['binding'].root / '合法 Space.MD').upper()
        assert WorkWriteTool().execute(path=path, content='unicode').success
        assert WorkReadTool().execute(path=path).content == 'unicode'
        return {'content': 'saved'}
    assert submit(tmp_path, runner)['status'] == 'succeeded'


def test_explicit_interaction_work_never_cloud_or_style(tmp_path, monkeypatch):
    from src.brain.interaction import InteractionLoop
    from src.brain import agent_client
    monkeypatch.setattr(agent_client, 'ask_work', lambda *a, **kw: {'status': 'failed', 'error': 'denied'})
    monkeypatch.setattr(InteractionLoop, '_try_cloud_fallback', lambda *a: pytest.fail('no cloud'))
    monkeypatch.setattr(InteractionLoop, '_try_agent_fallback', lambda *a, **kw: pytest.fail('no conversational retry'))
    loop = object.__new__(InteractionLoop)
    assert loop.handle_work('save', request_id='r', session_id='s')['status'] == 'failed'
