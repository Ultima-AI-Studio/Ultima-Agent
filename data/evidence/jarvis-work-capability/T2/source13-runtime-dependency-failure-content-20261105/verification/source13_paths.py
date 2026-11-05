"""Bind the inherited covering/compatibility gates to the source13 checkout."""
import importlib
import json
import os
from pathlib import Path
import sys

import pytest

ROOT = Path(r"C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent").resolve()
SDK = Path(r"H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Lib\site-packages").resolve()
RUN = Path(os.environ['ULTIMA_SOURCE13_GATE_ROOT']).resolve()


@pytest.fixture(autouse=True)
def isolate_legacy_confirmation_embedding(request, monkeypatch):
    """This queue-state unit test assumes an allowed utterance, not a live embedder."""
    if (Path(request.node.path).resolve() != ROOT / 'src/brain/tests/test_interaction.py'
            or request.node.name != 'test_query_then_consult_then_confirm'):
        yield
        return
    from src.brain import interaction
    from src.brain.routing.intent_gate import IntentGate
    from src.brain.routing.config import ALLOW_PROTOTYPES, DENY_PROTOTYPES
    calls = []

    class ConfirmationEmbedding:
        def embed(self, texts):
            values = tuple(texts)
            calls.append(list(values))
            if values == (*ALLOW_PROTOTYPES, *DENY_PROTOTYPES):
                return [[1.0, 0.0] for _ in ALLOW_PROTOTYPES] + [[0.0, 1.0] for _ in DENY_PROTOTYPES]
            assert values == ('确认',), 'Unexpected embedding request in queue-state unit test'
            return [[1.0, 0.0]]

    gate = IntentGate(embedding_channel=ConfirmationEmbedding())
    monkeypatch.setattr(interaction, 'get_intent_gate', lambda: gate)
    yield
    (RUN / 'interaction-embedding-fixture.json').write_text(json.dumps({
        'test': request.node.nodeid, 'calls': calls,
        'scope': 'Controlled ALLOW embedding for confirmation; real IntentGate/state machine and all original assertions retained',
        'limitation': 'Does not verify live semantic embeddings, model availability, or production routing quality',
        'actual_model_calls': 0,
    }, ensure_ascii=False, indent=2) + '\n', encoding='utf8')
    assert calls == [list((*ALLOW_PROTOTYPES, *DENY_PROTOTYPES)), ['确认']]


@pytest.hookimpl(tryfirst=True)
def pytest_collection(session):
    if os.environ['ULTIMA_SOURCE13_GATE_MODE'] != 'compat':
        return
    # The socket/process guard is already installed by pytest_sessionstart.
    sys.path.insert(0, str(ROOT / 'src' / 'brain'))
    sys.path.insert(0, str(ROOT))
    from src.brain import agent_server
    import agent_tools_ultima
    import tasks.queue_engine
    module = importlib.import_module('src.brain.tests.test_agent_tools_extend')
    module.ROOT = RUN / 'compat-sandbox'
    (module.ROOT / 'data').mkdir(parents=True, exist_ok=False)
    unapproved = {str(Path(p).resolve()).casefold() for p in (
        'H:/UltimaAI/UltimaAgent', 'H:/UltimaAI/UltimaAgent/src/brain',
        'H:/UltimaAI/UltimaAgent/libs/base/openjarvis/src')}
    sys.path[:] = [p for p in sys.path if str(Path(p).resolve()).casefold() not in unapproved]
    paths = {'server': agent_server.__file__, 'agent_tools': agent_tools_ultima.__file__,
             'queue_engine': tasks.queue_engine.__file__, 'test_module': module.__file__}
    assert all(Path(p).resolve().is_relative_to(ROOT) for p in paths.values()), paths
    (RUN / 'compat-loaded-paths.json').write_text(
        json.dumps({**paths, 'test_root': str(module.ROOT)}, indent=2) + '\n', encoding='utf8')


@pytest.hookimpl(trylast=True)
def pytest_sessionfinish(session, exitstatus):
    paths = {n: str(Path(m.__file__).resolve()) for n, m in tuple(sys.modules.items())
             if getattr(m, '__file__', None)
             and (n.startswith('src.brain.') or n.startswith('openjarvis.')
                  or n in ('agent_server', 'agent_tools_ultima', 'work_tools', 'work_research',
                           'work_service', 'tasks.queue_engine'))}
    bad = {n: p for n, p in paths.items()
           if not Path(p).is_relative_to(SDK if n.startswith('openjarvis.') else ROOT)}
    (RUN / 'loaded-paths.json').write_text(
        json.dumps({'modules': paths, 'unexpected': bad, 'sys_path': sys.path}, indent=2) + '\n',
        encoding='utf8')
    if bad:
        session.exitstatus = 1
