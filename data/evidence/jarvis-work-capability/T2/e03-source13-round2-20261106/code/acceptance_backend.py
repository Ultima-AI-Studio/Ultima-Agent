"""Reuse the reviewed native fixture, product CLI and mechanical/effect checks."""
from __future__ import annotations

import hashlib
import importlib
import json
import os
from pathlib import Path
import socket
import sys

from acceptance_entry import CASE, DIGEST, MODEL, SCOPE, utcnow
from package_io import load, require, safe_path, save_new
from fixture_manual_start import validate_handoff


def pick_port():
    with socket.socket() as sock:
        sock.bind(('127.0.0.1',0))
        return sock.getsockname()[1]


class AcceptanceBackend:
    def __init__(self, root, *, controller=None, harness=None, port_picker=pick_port, model_manifest=None):
        self.root = safe_path(root)
        if controller is None:
            controller = importlib.import_module('controller')
            bindings = ((controller,'code/controller.py'),(controller.old,'preparation-support/acceptance_adapter.py'),
                        (controller.candidate_guard,'code/source_candidate_guard.py'),(controller.fixture_audit,'code/fixture_adapter.py'),
                        (importlib.import_module('fixture_manual_start'),'code/fixture_manual_start.py'))
            for module, relative in bindings:
                require(Path(module.__file__).resolve() == (self.root/relative).resolve(), 'Unexpected runtime import: '+relative)
            origin = sys.modules['fixture_input_origin']
            require(Path(origin.__file__).resolve() == (self.root/'code/fixture_input_origin.py').resolve(), 'Unexpected origin import')
        self.controller = controller
        self.controller.old.PROTECTED_BASELINE = self.root/'inputs/protected-baseline.json'
        self.baseline = load(self.controller.old.PROTECTED_BASELINE)
        self.model_manifest = Path(model_manifest) if model_manifest else (
            Path(os.environ.get('OLLAMA_MODELS') or Path.home()/'.ollama/models')/'manifests/registry.ollama.ai/library'/MODEL/'latest')
        self.harness, self.port_picker = harness, port_picker
        self.context = self.folder = self.fixture = self.baseline_rows = self.expected_effects = None
        self.inspected = False

    @property
    def cli_count(self):
        return self.context.cli_count if self.context is not None else 0

    def _protected(self):
        c = self.controller
        expected = c.old.protected_entries(self.baseline)
        identities = c.protected(); by_pid = {row['pid']:row for row in identities}
        require(len(expected) == len(identities) == 7 and set(by_pid) == {row['pid'] for row in expected}, 'Protected inventory mismatch')
        snapshot = c.process_snapshot(pids=sorted(by_pid)); result = []
        for row in expected:
            identity = by_pid[row['pid']]
            require(identity['exe'].lower() == row['exe'].lower() and identity['created_filetime'] == row['created_filetime'], 'Protected identity mismatch')
            live = snapshot.get(row['pid'])
            require(live is not None and live['ParentProcessId'] == row['parent_pid'], 'Protected parent mismatch')
            require(c.snapshot_identity_matches(identity,live), 'Protected CIM identity mismatch')
            command_hash = hashlib.sha256(live['CommandLine'].encode('utf-16le')).hexdigest()
            require(command_hash == row['command_line_sha256'], 'Protected command mismatch')
            result.append(dict(identity,parent_pid=live['ParentProcessId'],command_line_sha256=command_hash))
        return result

    def inspect(self):
        require(os.environ.get('OLLAMA_HOST','http://localhost:11434') in
                ('http://localhost:11434','http://127.0.0.1:11434'), 'Local model only')
        c = self.controller
        source = c.candidate_guard.verify_current_candidate()
        protected = self._protected()
        listeners = set(c.listener_owner(11434))
        require(listeners == {protected[0]['pid']}, 'Protected native listener mismatch')
        version = c.get_json('http://127.0.0.1:11434/api/version')
        tags = c.get_json('http://127.0.0.1:11434/api/tags')
        manifest = safe_path(self.model_manifest).read_bytes()
        c.old.metadata_valid({'ok':True,'model':MODEL,'agent':'native_react'},version,tags,manifest)
        self.inspected = True
        return {'schema':1,'scope':SCOPE,'recorded_at':utcnow().isoformat(),'source':source,
                'model':{'model':MODEL,'digest':DIGEST,'version':version,
                         'tags_sha256':hashlib.sha256(json.dumps(tags,sort_keys=True).encode()).hexdigest(),
                         'manifest_sha256':hashlib.sha256(manifest).hexdigest()},
                'protected_processes':protected,'listener_pid':protected[0]['pid']}

    def _check_baseline(self, rows):
        require(isinstance(rows,list) and len(rows) == 2, 'Two baseline windows required')
        texts = [self.harness.CASES['e03']['text'],'UNRELATED OWNED FIXTURE — DO NOT CHANGE']
        for index, (row, target, text) in enumerate(zip(rows,self.fixture['targets'],texts)):
            require(all(row[key] == target[key] for key in self.controller.IDENTITY), 'Baseline target identity mismatch')
            require(row['text'] == text, 'Frozen fixture mismatch')
            expected = (0,len(text.encode('utf-16le'))//2) if index == 0 else (0,0)
            require((row['start_utf16'],row['end_utf16']) == expected, 'Frozen fixture selection mismatch')

    def start(self, folder):
        require(self.inspected, 'Read-only preflight must precede fixture start')
        self.folder = safe_path(folder)
        require(self.folder == self.root/'actual'/CASE, 'Exact case folder required')
        c = self.controller
        if self.harness is None:
            sys.path.insert(0,str(c.ROOT))
            self.harness = importlib.import_module('src.brain.tests.work_context_acceptance')
            require(Path(self.harness.__file__).resolve() == (c.ROOT/'src/brain/tests/work_context_acceptance.py').resolve(), 'Unexpected candidate harness')
        self.context = c.Case(CASE,self.folder,c.environment(self.folder))
        self.context.owned.launch(c.fixture_command(self.folder),'fixture')
        self.harness.wait_for(lambda:(self.folder/'fixture.json').exists(),20)
        self.context.owned.discover()
        fixture = load(self.folder/'fixture.json')
        owner = self.context.owned.known.get(fixture['pid'])
        require(owner and owner['role'] == 'fixture' and len(fixture['targets']) == 2
                and all(t['pid'] == fixture['pid'] and t['process_created_filetime'] == owner['identity']['created_filetime']
                        for t in fixture['targets']), 'Actual fixture owner mismatch')
        self.fixture = fixture
        validate_handoff(load(self.folder/'manual-start.json'),fixture)
        c.validate_fixture_readback(fixture,load(self.folder/'fixture-initial-readback.json'),self.harness.CASES['e03']['text'])
        self.context.fixture_ready = True
        audit = c.validate_fixture_audit(self.folder/'fixture-events.jsonl',fixture,require_closed=False)
        save_new(self.folder/'fixture-audit-live-preflight.json',audit)
        self.baseline_rows = self.context.observe('baseline')
        self._check_baseline(self.baseline_rows)

    def product(self, revalidate, admit_cli):
        require(self.context is not None and self.context.fixture_ready and self.baseline_rows is not None, 'Verified fixture required')
        c, context, folder = self.controller, self.context, self.folder
        require(context.cli_count == 0, 'Only one CLI submission allowed')
        context.port = self.port_picker()
        server_argv = ['-B','-m','src.brain.agent_server','--port',str(context.port),'--runtime-root',str(folder/'runtime'),
                       '--work-output-root',str(folder/'outputs'),'--isolated','--work-target-policy',str(folder/'policy.json')]
        context.owned.launch(server_argv,'server')
        def ready():
            if not c.listener_owner(context.port): return False
            c.assert_listener(context.owned,context.port,server_argv)
            health = c.get_json(f'http://127.0.0.1:{context.port}/health')
            require(health.get('ok') is True and health.get('model') == MODEL and health.get('agent') == 'native_react', 'Isolated health mismatch')
            return health
        save_new(folder/'isolated-health.json',self.harness.wait_for(ready,30))
        cli_argv = ['-B','-m','src.brain.cli','--work','--current-window','--replace-selection','--request-id',CASE,
                    '--session-id',CASE,'--server-url',f'http://127.0.0.1:{context.port}','--json',c.old.E03_QUERY]
        save_new(folder/'argv.json',{'server':server_argv,'cli':cli_argv,'max_turns':10,'work_max_tokens':2048,
                                    'CLI_timeout':300,'SDK_timeout':1800,'controller_wait':315,'overrides':[]})
        revalidate()
        c.assert_listener(context.owned,context.port,server_argv)
        context.command()
        self.baseline_rows = context.observe('dispatch-baseline')
        self._check_baseline(self.baseline_rows)
        admit_cli()
        context.cli_count += 1
        cli = context.owned.launch(cli_argv,'cli')
        c.old.wait_cli(cli,folder); context.owned.flush()
        context.result = load(folder/'cli.stdout')
        save_new(folder/'product-result.json',context.result)
        require(cli.returncode == 0, 'Nonzero CLI exit; generation may continue')
        events = [x for x in context.result.get('trace',[]) if x.get('type') == 'inference_end']
        require(1 <= len(events) <= 10 and all(x.get('data',{}).get('model') == MODEL for x in events), 'Completed inference proof missing')
        artifacts = c.read_artifacts(folder,context.result)
        windows = context.observe('final-windows'); inventory = c.output_inventory(folder)
        save_new(folder/'mechanical-inputs.json',{'artifacts':artifacts,'baseline':self.baseline_rows,'windows':windows,'outputs':inventory})
        review = c.mechanical(CASE,folder,context.result,artifacts,self.baseline_rows,windows,inventory)
        self.expected_effects = {'outputs':inventory,'windows':windows,'cli_count':1}
        save_new(folder/'accepted-effects.json',self.expected_effects)
        save_new(folder/'mechanical-review.json',review)
        return review

    def effects(self):
        if self.context is None:
            value = {'status':'NO_CONTEXT_STARTED','cli_count':0,'outputs':[],'windows':None}
            if self.folder is not None: save_new(self.folder/'pre-cleanup-effects.json',value)
            return value
        value = self.context.effects()
        if self.expected_effects is not None:
            self.controller.reconcile_effects(self.expected_effects,value)
        return value

    def close(self):
        if self.context is None: return {'status':'PASS','reason':'No owned context was started'}
        stop_error = None
        try: safe_path(self.folder/'stop').touch()
        except Exception as exc: stop_error = type(exc).__name__ + ': ' + str(exc)
        result = self.context.owned.cleanup(self.context.port)
        return dict(result,status='FAIL',stop_error=stop_error) if stop_error else result

    def audit(self):
        require(self.fixture is not None, 'No verified owned fixture audit')
        return self.controller.validate_fixture_audit(self.folder/'fixture-events.jsonl',self.fixture,require_closed=True)
