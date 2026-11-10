"""Exercise E01 orchestration and real file validators with process/native boundaries replaced."""
import ast
import datetime as dt
import hashlib
import json
import os
import shutil
import uuid
from pathlib import Path
from types import SimpleNamespace

import pytest

import acceptance_backend as module
import acceptance_entry as entry
import package_io as io
from test_acceptance_entry import NOW, package, put

HERE = Path(__file__).resolve().parent
CANDIDATE = Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-e03-source13\UltimaAgent')
CASES = json.loads((CANDIDATE / 'src/brain/tests/fixtures/work_capability/acceptance-cases.json').read_bytes())


def backend(root, fault=None):
    calls = []
    if not (root / 'inputs/protected-baseline.json').exists():
        (root / 'inputs').mkdir(exist_ok=True)
        shutil.copyfile(HERE.parent / 'inputs/protected-baseline.json', root / 'inputs/protected-baseline.json')

    class Owned:
        def __init__(self, folder, env):
            self.folder = folder
            self.launchers = []
            self.known = {}
        def launch(self, argv, role):
            calls.append(('launch', role, argv))
            assert role in ('server', 'cli'), 'E01 must never launch a fixture or observer'
            proc = SimpleNamespace(returncode=1 if fault == 'exit' and role == 'cli' else 0,
                                   wait=lambda timeout: calls.append(('wait', timeout)))
            self.launchers.append({'role':role, 'proc':proc})
            if role == 'cli':
                task = '5bed49e8-a1e4-45bf-b18b-793ef702fdaa'
                call = '84f58580-4887-4781-a8b4-2cf47c00cf6b'
                output = self.folder / 'outputs' / task / 'summary.md'
                output.parent.mkdir(parents=True)
                content = '\n'.join(CASES['e01']['facts']) + '\n'
                output.write_bytes(content.encode('utf-8'))
                digest = hashlib.sha256(output.read_bytes()).hexdigest()
                identity = dict(request_id=entry.CASE, session_id=entry.CASE, task_id=task, call_id=call)
                write = dict(identity, tool_name='ultima_work_file_write', success=True, path=str(output), content=content)
                artifact = dict(identity, path=str(output), sha256=digest, verified=True)
                value = dict(request_id=entry.CASE, session_id=entry.CASE, task_id=task, status='succeeded',
                    artifacts=[artifact], tool_results=[write, {'tool_name':'ultima_work_file_write', 'success':True}],
                    trace=[{'type':'inference_end','data':{'model':entry.MODEL}},
                        {'type':'tool_call_start','data':{'tool':'ultima_work_file_write',
                            'arguments':{'path':'summary.md','content':content}}},
                        {'type':'tool_call_end','data':{'tool':'ultima_work_file_write','success':True}}])
                if fault == 'missing': output.unlink()
                if fault == 'tampered': output.write_text('changed after write', encoding='utf-8')
                if fault == 'hash': artifact['sha256'] = '0' * 64
                if fault == 'old-file': value['tool_results'] = []
                if fault == 'extra': (output.parent / 'unrelated.txt').write_text('extra', encoding='utf-8')
                if fault == 'identity': write['request_id'] = 'old-request'
                if fault == 'mutation': value['tool_results'].append(dict(identity, event='mutation.send'))
                if fault == 'model': value['trace'][0]['data']['model'] = 'unapproved-model'
                if fault == 'escape': artifact['path'] = str(self.folder / 'outside.txt')
                if fault == 'uuid': value['task_id'] = 'invalid-task-id'
                put(self.folder / 'cli.stdout', value)
            return proc
        def flush(self): calls.append(('flush',))
        def cleanup(self, port):
            calls.append(('cleanup', port))
            assert (self.folder / 'stop').exists()
            return {'status':'PASS'}

    namespace = dict(Path=Path, uuid=uuid, hashlib=hashlib, json=json, os=os, dt=dt,
                     load=io.load, save=put, no_reparse=io.safe_path, Owned=Owned,
                     utc=lambda:NOW)
    tree = ast.parse((HERE / 'controller.py').read_text(encoding='utf-8-sig'))
    names = {'require','timestamp','uuid_text','artifact_path','output_inventory','inventory_map',
             'reconcile_effects','read_artifacts','ids','sdk_tool_proof','mechanical','Case'}
    nodes = [node for node in tree.body if isinstance(node, (ast.FunctionDef,ast.ClassDef)) and node.name in names]
    assert {node.name for node in nodes} == names
    exec(compile(ast.Module(body=nodes,type_ignores=[]),'<actual controller file validators and Case>','exec'),namespace)
    old_ns = {'CLI_TIMEOUT':315}
    tree = ast.parse((HERE.parent / 'preparation-support/acceptance_adapter.py').read_text(encoding='utf-8-sig'))
    node = next(node for node in tree.body if isinstance(node,ast.FunctionDef) and node.name == 'wait_cli')
    exec(compile(ast.Module(body=[node],type_ignores=[]),'<actual wait_cli>','exec'),old_ns)
    old = SimpleNamespace(wait_cli=old_ns['wait_cli'])
    controller = SimpleNamespace(**{name:namespace[name] for name in names}, old=old, ROOT=CANDIDATE,
        fixture_command=lambda folder:['forbidden-test-fixture'],
        environment=lambda folder:{}, listener_owner=lambda port:[100],
        assert_listener=lambda *args:calls.append(('assert-listener',)),
        get_json=lambda url:{'ok':True,'model':entry.MODEL,'agent':'native_react'})
    harness = SimpleNamespace(CASES=CASES, wait_for=lambda predicate, seconds:predicate())
    native = module.AcceptanceBackend(root, controller=controller, harness=harness, port_picker=lambda:18759)
    return native, calls


def start(native, root):
    folder = root / 'actual' / entry.CASE
    folder.mkdir(parents=True)
    native.inspected = True
    native.start(folder)


def test_e01_real_file_readback_uses_no_ui_and_keeps_original_deadlines(tmp_path):
    native, calls = backend(tmp_path)
    start(native, tmp_path)
    assert calls == []
    review = native.product(lambda:calls.append(('revalidate',)), lambda:calls.append(('admit-cli',)))
    assert review == {'mechanical':'PASS','facts':'PENDING_ROOT_INDEPENDENT_REVIEW'}
    native.effects()
    assert native.close()['status'] == native.audit()['status'] == 'PASS'
    launches = [row for row in calls if row[0] == 'launch']
    assert [row[1] for row in launches] == ['server','cli']
    server, cli = [row[2] for row in launches]
    assert '--work-target-policy' not in server
    assert not {'--current-window','--replace-selection','--research'} & set(cli)
    assert cli[-1] == CASES['e01']['request'] + '\n' + '\n'.join(CASES['e01']['facts'])
    assert server[server.index('--work-output-root')+1] == str(native.folder / 'outputs')
    assert '--isolated' in server and ('wait',315) in calls
    argv = io.load(native.folder / 'argv.json')
    assert {k:argv[k] for k in ('CLI_timeout','SDK_timeout','controller_wait')} == {
        'CLI_timeout':300,'SDK_timeout':1800,'controller_wait':315}
    assert argv['overrides'] == [] and native.cli_count == 1
    assert calls.index(('revalidate',)) < calls.index(('admit-cli',)) < calls.index(launches[-1])
    assert calls[calls.index(launches[-1])-1] == ('admit-cli',)
    assert io.load(native.folder / 'mechanical-inputs.json')['windows'] is None
    assert io.load(native.folder / 'external-artifacts.json')[0]['external_sha256'] == native.context.result['artifacts'][0]['sha256']
    with pytest.raises(ValueError): native.product(lambda:None,lambda:None)
    assert len([row for row in calls if row[:2] == ('launch','cli')]) == 1


@pytest.mark.parametrize('fault', ['missing','tampered','hash','old-file','extra','identity','mutation','model','exit','escape','uuid'])
def test_e01_failed_delivery_is_not_mechanical_pass_and_cleanup_still_runs(tmp_path, monkeypatch, fault):
    gate, authority, proof = package(tmp_path, monkeypatch)
    native, calls = backend(tmp_path, fault)
    native.inspected = True
    native.inspect = lambda:proof
    result = gate.run_once(tmp_path, backend_factory=lambda root:native)
    assert result['overall'] == 'FAIL' and result['acceptance_credit'] is False
    assert result['work_cli_count'] == 1
    assert ('cleanup',18759) in calls and result['cleanup']['status'] == 'PASS'
    assert len([row for row in calls if row[:2] == ('launch','cli')]) == 1


@pytest.mark.parametrize('deadline', ['proof','authority'])
def test_server_health_delay_can_expire_original_admission_without_cli(tmp_path, monkeypatch, deadline):
    gate, authority, proof = package(tmp_path, monkeypatch)
    if deadline == 'authority':
        authority['expires_at'] = (NOW+dt.timedelta(seconds=1)).isoformat()
        put(tmp_path / 'release/authority.json',authority)
    native, calls = backend(tmp_path)
    native.inspected = True
    native.inspect = lambda:proof
    original = native.harness.wait_for
    def slow_health(predicate, seconds):
        result = original(predicate,seconds)
        monkeypatch.setattr(gate,'utcnow',lambda:NOW+dt.timedelta(seconds=61 if deadline == 'proof' else 2))
        return result
    native.harness.wait_for = slow_health
    result = gate.run_once(tmp_path, backend_factory=lambda root:native)
    assert result['overall'] == 'FAIL' and result['work_cli_count'] == 0
    assert not any(row[:2] == ('launch','cli') for row in calls)
    assert ('cleanup',18759) in calls


def test_uninspected_start_cannot_launch_any_process(tmp_path):
    native, calls = backend(tmp_path)
    folder = tmp_path / 'actual' / entry.CASE
    folder.mkdir(parents=True)
    with pytest.raises(ValueError,match='preflight'): native.start(folder)
    assert calls == []


def test_unexpected_fixture_evidence_is_rejected(tmp_path):
    native, calls = backend(tmp_path)
    start(native,tmp_path)
    put(native.folder/'fixture.json', {'unexpected':True})
    with pytest.raises(ValueError): native.audit()


def test_complete_e01_entry_retains_real_file_and_pending_fact_review(tmp_path, monkeypatch):
    gate, authority, proof = package(tmp_path, monkeypatch)
    native, calls = backend(tmp_path)
    native.inspected = True
    native.inspect = lambda:proof
    result = gate.run_once(tmp_path, backend_factory=lambda root:native)
    assert result['overall'] == 'PENDING_FACT_REVIEW' and result['mechanical'] == 'PASS'
    assert result['facts'] == 'PENDING_ROOT_INDEPENDENT_REVIEW' and result['acceptance_credit'] is False
    assert result['product_result_sha256'] == io.sha(native.folder/'product-result.json')
    assert result['audit']['scope'] == 'E01_NO_UI' and result['work_cli_count'] == 1
    assert io.load(native.folder/'accepted-effects.json')['windows'] is None


@pytest.mark.parametrize('deadline', ['proof','authority'])
def test_final_listener_inspection_delay_is_checked_before_cli(tmp_path, monkeypatch, deadline):
    gate, authority, proof = package(tmp_path, monkeypatch)
    if deadline == 'authority':
        authority['expires_at'] = (NOW+dt.timedelta(seconds=1)).isoformat()
        put(tmp_path/'release/authority.json',authority)
    native, calls = backend(tmp_path)
    native.inspected = True
    native.inspect = lambda:proof
    checks = []
    def delayed_listener(*args):
        checks.append(True)
        if len(checks) == 2:
            monkeypatch.setattr(gate,'utcnow',lambda:NOW+dt.timedelta(seconds=61 if deadline=='proof' else 2))
    native.controller.assert_listener = delayed_listener
    result = gate.run_once(tmp_path, backend_factory=lambda root:native)
    assert result['overall'] == 'FAIL' and result['work_cli_count'] == 0
    assert not any(row[:2] == ('launch','cli') for row in calls)
    assert ('cleanup',18759) in calls


def test_change_after_mechanical_readback_fails_final_effects(tmp_path, monkeypatch):
    gate, authority, proof = package(tmp_path, monkeypatch)
    native, calls = backend(tmp_path)
    native.inspected = True
    native.inspect = lambda:proof
    original = native.product
    def tamper_after_acceptance(revalidate, admit_cli):
        result = original(revalidate, admit_cli)
        Path(native.context.result['artifacts'][0]['path']).write_text('later mutation',encoding='utf-8')
        return result
    native.product = tamper_after_acceptance
    result = gate.run_once(tmp_path, backend_factory=lambda root:native)
    assert result['overall'] == 'FAIL' and any(row['stage']=='effects' for row in result['errors'])
    assert ('cleanup',18759) in calls
