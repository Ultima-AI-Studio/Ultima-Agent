import importlib.util
from pathlib import Path
import tempfile
import unittest
import sys
import json
import subprocess
import time
from unittest import mock

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tasks.queue_engine.dispatcher import DispatchLock

ROOT = Path(__file__).resolve().parents[2]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class DispatchContracts(unittest.TestCase):
    def test_recovery_fence_rejects_changed_run_state_or_reservation(self):
        dispatch=module('dispatch_fence_test','dispatch-work-order.py')
        import re
        row=re.match(r'(blocked) (run-new) (reservation-new)','blocked run-new reservation-new')
        class Match:
            def group(self,index):
                return 'blocked' if index==1 else 'run-new reservation-new'
        for expected_state,expected_run,reservation in [('audit','run-new','reservation-new'),('blocked','run-old','reservation-new'),('blocked','run-new','reservation-old')]:
            with self.assertRaises(RuntimeError):
                dispatch.check_recovery_fence(Match(),expected_state,expected_run,reservation)
    def test_owned_job_close_stops_worker_and_child_without_touching_other_process(self):
        dispatch = module('dispatch_job_test', 'dispatch-work-order.py')
        with tempfile.TemporaryDirectory() as raw:
            evidence = Path(raw)/'child.txt'
            code = 'import subprocess,sys,time;from pathlib import Path;sys.stdin.readline();p=subprocess.Popen([sys.executable,"-c","import time;time.sleep(60)"]);Path(sys.argv[1]).write_text(str(p.pid));time.sleep(60)'
            worker = subprocess.Popen([sys.executable, '-c', code, str(evidence)], stdin=subprocess.PIPE, creationflags=0x08000000)
            unrelated = subprocess.Popen([sys.executable, '-c', 'import time;time.sleep(60)'], creationflags=0x08000000)
            def cleanup(process):
                if process.poll() is None:
                    process.kill()
                process.wait(timeout=5)
            self.addCleanup(cleanup, unrelated)
            self.addCleanup(cleanup, worker)
            job = dispatch.OwnedJob(worker)
            try:
                worker.stdin.write(b'go\n')
                worker.stdin.close()
                deadline = time.monotonic()+5
                while (not evidence.exists() or not evidence.stat().st_size) and time.monotonic()<deadline:
                    time.sleep(.01)
                self.assertTrue(evidence.exists())
                child = int(evidence.read_text())
            finally:
                job.close()
                worker.wait(timeout=5)
            self.assertIsNotNone(worker.wait(timeout=5))
            deadline = time.monotonic()+5
            while dispatch.process_identity(child) is not None and time.monotonic()<deadline:
                time.sleep(.01)
            self.assertIsNone(dispatch.process_identity(child))
            self.assertIsNone(unrelated.poll(), 'Other processes must remain alive')
            unrelated.kill()
            unrelated.wait(timeout=5)
    def test_state_preserves_other_rows_and_crlf_when_replace_is_denied(self):
        dispatch = module('dispatch_windows_replace', 'dispatch-work-order.py')
        with tempfile.TemporaryDirectory() as raw:
            dispatch.SHARED = Path(raw)
            run = Path(raw)/'run-123'
            run.mkdir()
            path = Path(raw)/'global-queue-index.md'
            other = '| Other | unchanged | pending | exact bytes |\r\n'
            path.write_bytes(('<!-- queue-items:start -->\r\n'+other+
                '| UltimaAgent | wo-s1-host-shell | executing | run-123 |\r\n<!-- queue-items:end -->\r\n').encode())
            (Path(raw)/'queue-status-gen.py').write_text('pass\n')
            with mock.patch.object(Path, 'replace', side_effect=PermissionError('Windows reader denies DELETE sharing')):
                dispatch.state('wo-s1-host-shell', 'blocked', 'paused', run, expected='executing', expected_run='run-123')
            result = path.read_bytes()
            self.assertIn(other.encode(), result)
            self.assertIn(b'| blocked | paused |\r\n', result)
            self.assertNotIn(b'\r\r\n', result)

    def run_isolated_dispatch(self, other_audit=False,recovery_fence=False,stale=False,pause_during=False):
        dispatch = module('dispatch_worker_integration', 'dispatch-work-order.py')
        temporary = tempfile.TemporaryDirectory()
        self.addCleanup(temporary.cleanup)
        root = Path(temporary.name)
        shared = root/'shared'
        shared.mkdir()
        dispatch.ROOT, dispatch.SHARED = root, shared
        order = 'wo-s1-host-shell'
        (root/'tasks/queue').mkdir(parents=True)
        card = root/'tasks/cards/s1-unit'
        card.mkdir(parents=True)
        (card/'task.md').write_text('- **stage** v0.4\n')
        (root/'tasks/queue'/f'{order}.md').write_text('| T1 s1-unit | test |\n')
        expected_run='wo-s1-host-shell-20261024T000000Z'
        reason=('wo-s1-host-shell-20261024T010000Z' if stale else expected_run)+' reservation-123' if recovery_fence else 'continuation'
        (shared/'global-queue-index.md').write_text('<!-- queue-items:start -->\n'+
            ('| Other | another | audit | must retain audit slot |\n' if other_audit else '')+
            f'| UltimaAgent | {order} | blocked | {reason} |\n<!-- queue-items:end -->\n')
        (shared/'queue-status-gen.py').write_text('pass\n')
        prompt = root/'prompt.txt'
        prompt.write_text(f'docs/INDEX.md {order}')
        fake = root/'fake_worker.py'
        fake.write_text('import sys,json\nfrom pathlib import Path\n'+
            'sys.path.insert(0, '+repr(str(ROOT))+')\n'+
            'from tasks.queue_engine.dispatcher import DispatchLock\n'+
            'sys.stdin.read()\nfinal=Path(sys.argv[sys.argv.index("--output-last-message")+1])\n'+
            'try:\n with DispatchLock(Path('+repr(str(shared))+')/".engineering-dispatch.lock"):\n  available=True\n'+
            'except RuntimeError:\n available=False\n'+
            'e=final.parent/"worker-lock-probe.json"\ne.write_text(json.dumps({"available":available}))\n'+
            (('Path('+repr(str(root/'tasks/.pause-dispatch'))+').write_text("user pause")\nimport time\ntime.sleep(1)\n') if pause_during else '')+
            'final.write_text(json.dumps({"work_order":'+repr(order)+',"status":"READY_FOR_REVIEW","evidence":[str(e)],"landed_files":[]}))\n')
        real_popen = subprocess.Popen
        class Guardian:
            pid = 123
            def wait(self, timeout=None):
                return 0
        def popen(command, **kwargs):
            if command[0] == 'fake-codex':
                return real_popen([sys.executable, str(fake), *command[1:]], **kwargs)
            return Guardian()
        argv=['dispatch', '--order', order, '--prompt', str(prompt), '--repair', '--execute']
        if recovery_fence:
            argv+=['--expected-run',expected_run,'--expected-state','blocked','--expected-reservation','reservation-123']
        with mock.patch.object(dispatch.native, 'codex_processes', return_value=[]), \
             mock.patch.object(dispatch, 'check_version_gates'), \
             mock.patch.object(dispatch.shutil, 'which', return_value='fake-codex'), \
             mock.patch.object(dispatch.subprocess, 'Popen', side_effect=popen), \
             mock.patch.object(sys, 'argv', argv):
            # state() uses subprocess.run too; keep real Popen for the mirror generator.
            original = dispatch.state
            def state(*args, **kwargs):
                with mock.patch.object(dispatch.subprocess, 'Popen', real_popen):
                    return original(*args, **kwargs)
            with mock.patch.object(dispatch, 'state', side_effect=state):
                code = dispatch.main()
        runs = list((root/'tasks/queue/runs').iterdir())
        return code, runs[0], shared

    def test_recovery_cli_fence_allows_only_original_reservation(self):
        code,run,shared=self.run_isolated_dispatch(recovery_fence=True)
        self.assertEqual(0,code)
        self.assertEqual('audit',json.loads((run/'done.json').read_text())['state'])
        self.assertEqual('reservation-123',json.loads((run/'session.json').read_text())['engineering_reservation'])

    def test_runtime_pause_closes_only_owned_worker_before_final(self):
        code,run,shared=self.run_isolated_dispatch(pause_during=True)
        self.assertEqual(2,code)
        self.assertTrue((run/'pause-stop.json').exists())
        self.assertFalse((run/'final.json').exists())
        self.assertEqual('blocked',json.loads((run/'done.json').read_text())['state'])

    def test_recovery_cli_fence_refuses_changed_run_before_spawn(self):
        with self.assertRaises(RuntimeError):
            self.run_isolated_dispatch(recovery_fence=True,stale=True)

    def test_shared_lock_available_to_other_project_while_worker_runs(self):
        code, run, shared = self.run_isolated_dispatch()
        self.assertTrue(json.loads((run/'worker-lock-probe.json').read_text())['available'],
                        'Worker must not hold global admission lock for its lifetime')
        self.assertEqual(0, code)
        with DispatchLock(shared/'.engineering-dispatch.lock'):
            pass

    def test_existing_other_audit_slot_is_not_stolen_on_completion(self):
        code, run, shared = self.run_isolated_dispatch(other_audit=True)
        self.assertEqual(2, code)
        self.assertEqual('blocked', json.loads((run/'done.json').read_text())['state'])
        self.assertIn('| Other | another | audit |', (shared/'global-queue-index.md').read_text())
    def test_profile_value_never_hides_actual_exec(self):
        native = module('native_review_test', 'inspect-native-environment.py')
        self.assertEqual({'role': 'exec', 'project': 'H:\\UltimaAI\\UltimaAgent'},
                         native.parse_role(['codex.exe', '--profile', 'app-server', 'exec', '-C', 'H:\\UltimaAI\\UltimaAgent', '-']))

    def test_prompt_is_not_parsed_as_command_or_project_option(self):
        native = module('native_review_prompt', 'inspect-native-environment.py')
        self.assertEqual({'role': 'exec', 'project': None},
                         native.parse_role(['codex.exe', 'exec', '--', '-C', 'app-server']))

    def test_unknown_option_fails_closed(self):
        native = module('native_review_unknown', 'inspect-native-environment.py')
        self.assertEqual('unknown', native.parse_role(['codex.exe', '--unrecognized', 'exec'])['role'])

    def test_duplicate_or_outside_register_rejected(self):
        dispatch = module('dispatch_register_test', 'dispatch-work-order.py')
        with tempfile.TemporaryDirectory() as raw:
            dispatch.SHARED = Path(raw)
            path = dispatch.SHARED / 'global-queue-index.md'
            row = '| UltimaAgent | wo-s1-host-shell | blocked | pending evidence |\n'
            start, end = '<!-- queue-items:start -->\n', '<!-- queue-items:end -->\n'
            path.write_text(start + row + end, encoding='utf-8')
            self.assertEqual('blocked', dispatch.registered('wo-s1-host-shell')[1].group(1))
            path.write_text(start + row + row + end, encoding='utf-8')
            with self.assertRaises(ValueError):
                dispatch.registered('wo-s1-host-shell')
            path.write_text(row + start + end, encoding='utf-8')
            with self.assertRaises(ValueError):
                dispatch.registered('wo-s1-host-shell')

    def test_changed_state_or_run_cannot_be_overwritten(self):
        dispatch = module('dispatch_compare_test', 'dispatch-work-order.py')
        with tempfile.TemporaryDirectory() as raw:
            dispatch.SHARED = Path(raw)
            path = dispatch.SHARED / 'global-queue-index.md'
            path.write_text('<!-- queue-items:start -->\n| UltimaAgent | wo-s1-host-shell | frozen | later decision |\n<!-- queue-items:end -->\n', encoding='utf-8')
            before = path.read_bytes()
            with self.assertRaises(RuntimeError):
                dispatch.state('wo-s1-host-shell', 'executing', 'old action', Path(raw), expected='blocked')
            with self.assertRaises(RuntimeError):
                dispatch.state('wo-s1-host-shell', 'audit', 'old finish', Path(raw), expected='frozen', expected_run='old-run')
            self.assertEqual(before, path.read_bytes())


if __name__ == '__main__':
    unittest.main()
