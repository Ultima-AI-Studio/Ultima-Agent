"""Narrow bridge to existing fixture/observer/owned cleanup; no product calls."""
from __future__ import annotations

import hashlib
import importlib
from pathlib import Path
import sys
import threading

from fixture_diagnostic import CASE, HEAD, load, require, safe_path, summarize_observations


class NativeBridge:
    def __init__(self, root, *, controller=None, harness=None, timer_factory=threading.Timer):
        self.root = safe_path(root)
        if controller is None:
            controller = importlib.import_module('controller')
            require(Path(controller.__file__).resolve() == (self.root/'code/controller.py').resolve(),
                    'Unexpected controller import')
        self.controller = controller
        self.baseline_path = self.root/'inputs/protected-baseline.json'
        self.baseline = load(self.baseline_path)
        # Process-local data binding only; no old package file is written.
        self.controller.old.PROTECTED_BASELINE = self.baseline_path
        self.harness = harness
        self.timer_factory = timer_factory
        self.context = self.folder = self.timer = self.fixture = None
        self.deadline_triggered = False
        self.watchdog_error = None
        self.preflight_verified = False

    def _protected(self):
        expected = self.controller.old.protected_entries(self.baseline)
        identities = self.controller.protected()
        by_pid = {row['pid']: row for row in identities}
        require(len(expected) == len(identities) == 7
                and set(by_pid) == {row['pid'] for row in expected}, 'Protected inventory mismatch')
        snapshot = self.controller.process_snapshot(pids=sorted(by_pid))
        result = []
        for row in expected:
            identity = by_pid[row['pid']]
            require(identity['exe'].lower() == row['exe'].lower()
                    and identity['created_filetime'] == row['created_filetime'], 'Protected identity mismatch')
            live = snapshot.get(row['pid'])
            require(live is not None and live['ParentProcessId'] == row['parent_pid'], 'Protected parent mismatch')
            require(self.controller.snapshot_identity_matches(identity, live), 'Protected CIM identity mismatch')
            command_hash = hashlib.sha256(live['CommandLine'].encode('utf-16le')).hexdigest()
            require(command_hash == row['command_line_sha256'], 'Protected command mismatch')
            result.append(dict(identity, parent_pid=live['ParentProcessId'], command_line_sha256=command_hash))
        return result

    def preflight(self):
        # The legacy controller also verifies its own code/inputs.json. This
        # package seals those dependencies in verify_package; retain the full
        # pinned candidate guard without borrowing another package's inputs.
        candidate = self.controller.candidate_guard.verify_current_candidate()
        require(candidate['candidate'] == HEAD, 'Candidate changed')
        protected = self._protected()
        self.preflight_verified = True
        return protected

    def _watchdog_stop(self):
        self.deadline_triggered = True
        try:
            safe_path(self.folder/'stop').touch()
        except Exception as exc:
            self.watchdog_error = type(exc).__name__ + ': ' + str(exc)

    def start(self, folder):
        require(self.preflight_verified, 'Read-only preflight must precede fixture start')
        self.folder = safe_path(folder)
        if self.harness is None:
            sys.path.insert(0, str(self.controller.ROOT))
            self.harness = importlib.import_module('src.brain.tests.work_context_acceptance')
        self.context = self.controller.Case(CASE, self.folder, self.controller.environment(self.folder))
        self.timer = self.timer_factory(30, self._watchdog_stop)
        self.timer.daemon = True
        self.timer.start()
        # The only explicit execution role this bridge can launch.
        self.context.owned.launch(['-B', str(self.root/'code/fixture_adapter.py'),
                                   '--fixture', str(self.folder), '--candidate-root', str(self.controller.ROOT)],
                                  'fixture')

    def capture(self):
        self.harness.wait_for(lambda: (self.folder/'fixture.json').exists(), 20)
        self.context.owned.discover()
        fixture = load(self.folder/'fixture.json')
        owner = self.context.owned.known.get(fixture['pid'])
        require(owner and owner['role'] == 'fixture' and len(fixture['targets']) == 2
                and all(target['pid'] == fixture['pid']
                        and target['process_created_filetime'] == owner['identity']['created_filetime']
                        for target in fixture['targets']), 'Fixture owner mismatch')
        self.fixture = fixture
        initial = load(self.folder/'fixture-initial-readback.json')
        self.controller.validate_fixture_readback(fixture, initial, self.harness.CASES['e03']['text'])
        self.context.fixture_ready = True
        self.controller.validate_fixture_audit(self.folder/'fixture-events.jsonl', fixture, require_closed=False)
        # Same observer command, startup and Win32 read sequence as R31.
        rows = self.context.observe('baseline')
        require(len(rows) == 2 and all(all(row[key] == target[key] for key in self.controller.IDENTITY)
                                      for row, target in zip(rows, fixture['targets'])), 'Observed fixture identity mismatch')
        expected = [self.harness.CASES['e03']['text'], 'UNRELATED OWNED FIXTURE — DO NOT CHANGE']
        summaries = summarize_observations(rows)
        for summary, row, text in zip(summaries, rows, expected):
            summary['matches_expected_text'] = row['text'] == text
        return {'phenomenon': 'UNCHANGED' if all(item['matches_expected_text'] for item in summaries) else 'TEXT_CHANGED',
                'baseline_summaries': summaries}

    def close(self):
        if self.context is None:
            return {'status': 'FAIL', 'reason': 'No owned context was initialized'}
        stop_error = None
        try:
            safe_path(self.folder/'stop').touch()
            if self.timer is not None:
                self.timer.cancel()
        except Exception as exc:
            stop_error = type(exc).__name__ + ': ' + str(exc)
        try:
            scope_valid = self.context.port is None and self.context.cli_count == 0
            result = self.context.owned.cleanup(None)
        finally:
            if self.timer is not None:
                self.timer.cancel()
        if stop_error or self.watchdog_error or not scope_valid:
            result = dict(result, status='FAIL', stop_error=stop_error, watchdog_error=self.watchdog_error,
                          product_scope_valid=scope_valid)
        return result

    def postflight(self, before):
        candidate = self.controller.candidate_guard.verify_current_candidate()
        require(candidate['candidate'] == HEAD, 'Candidate changed during diagnostic')
        after = self._protected()
        require(after == before, 'Protected processes changed')
        return {'status': 'PASS', 'protected_processes': after}

    def audit(self):
        require(self.fixture is not None, 'No verified fixture to audit')
        return self.controller.validate_fixture_audit(self.folder/'fixture-events.jsonl', self.fixture,
                                                       require_closed=True)
