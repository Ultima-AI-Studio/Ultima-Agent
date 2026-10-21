import json
import os
from pathlib import Path
import subprocess
import sys
import time
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[2]), str(Path(__file__).resolve().parent)]
import test_audit_e2e as fixtures
from tasks.queue_engine.dispatcher import Dispatcher, BACKGROUND_CREATION_FLAGS
from tasks.queue_engine.priority_deps import QueuePlanner
from tasks.queue_engine.audit import RecoveryManager


class W2Regressions(unittest.TestCase):
    def setUp(self):
        self.f = fixtures.AuditE2ETests('test_no_receipt_is_blocked_and_never_completed')
        self.f.setUp()

    def tearDown(self):
        self.f.tearDown()

    def real_auditable_run(self):
        QueuePlanner(self.f.storage).enqueue(self.f.task())
        artifact = self.f.task_root / 'artifact.txt'
        artifact.write_text('verified fixture result', encoding='utf-8')
        dispatcher = Dispatcher(self.f.storage)
        decision = dispatcher.dispatch('e2e', [sys.executable, '-c', 'print(\'{"business_success":true}\')'])
        dispatcher.take_process(decision.pid).wait(timeout=10)
        recovery = RecoveryManager(self.f.storage)
        recovery.recover_finished_run('e2e')
        task = recovery.finish_self_check_from_run('e2e')
        return task, self.f.receipt(artifact), self.f.summary()

    def test_unrelated_acceptance_cannot_pass(self):
        task, receipt, summary = self.real_auditable_run()
        receipt['acceptance'] = {'unrelated': True}
        self.assertNotEqual('PASS', self.f.audit_engine.audit(task, receipt, summary, auditor_skill='eng.audit').verdict)

    def test_same_principal_cannot_self_audit(self):
        task, receipt, summary = self.real_auditable_run()
        summary['developer_id'] = summary['auditor_id']
        self.assertNotEqual('PASS', self.f.audit_engine.audit(task, receipt, summary, auditor_skill='eng.audit').verdict)

    def test_wrong_order_cannot_pass(self):
        task, receipt, summary = self.real_auditable_run()
        summary['work_order'] = 'wrong-order'
        self.assertNotEqual('PASS', self.f.audit_engine.audit(task, receipt, summary, auditor_skill='eng.audit').verdict)

    def test_tree_evidence_covers_worker_and_grandchild(self):
        QueuePlanner(self.f.storage).enqueue(self.f.task())
        grandchild = "import time;time.sleep(.35)"
        child = ('import subprocess,sys;'
                 f'p=subprocess.Popen([sys.executable,"-c",{grandchild!r}],creationflags={BACKGROUND_CREATION_FLAGS});'
                 'p.wait();print(\'{"business_success":true}\')')
        dispatcher = Dispatcher(self.f.storage)
        result = dispatcher.dispatch('e2e', [sys.executable, '-c', child])
        dispatcher.take_process(result.pid).wait(timeout=10)
        done = json.loads(result.run_paths['done'].read_text(encoding='utf-8'))
        progress = json.loads(result.run_paths['progress'].read_text(encoding='utf-8'))
        self.assertEqual(0, done['exit_code'])
        observed = done['window_audit']['observed_pids']
        self.assertIn(result.pid, observed)
        self.assertIn(progress['worker_pid'], observed)
        self.assertGreaterEqual(len(observed), 3)
        self.assertEqual([], done['window_audit']['visible_windows'])

    def test_actual_guardian_pauses_and_exits_after_parent_loss(self):
        root = str(Path(__file__).resolve().parents[2])
        marker = self.f.task_root / '.pause-dispatch'
        guard_pid = self.f.task_root / 'guard.pid'
        done = self.f.task_root / 'never.done'
        code = ('import os,sys,time,subprocess;from pathlib import Path;'
                f'sys.path.insert(0,{root!r});'
                'from tasks.queue_engine.dispatcher import process_identity;'
                f'p=subprocess.Popen([sys.executable,{str(Path(root)/"tasks/queue_engine/guardian.py")!r},str(os.getpid()),str(process_identity(os.getpid())),{str(marker)!r},{str(done)!r}],creationflags={BACKGROUND_CREATION_FLAGS});'
                f'Path({str(guard_pid)!r}).write_text(str(p.pid));time.sleep(.2);os._exit(0)')
        parent = subprocess.run([sys.executable, '-c', code], capture_output=True,
                                creationflags=BACKGROUND_CREATION_FLAGS, timeout=10)
        self.assertEqual(0, parent.returncode, parent.stderr)
        from tasks.queue_engine.dispatcher import process_identity
        deadline = time.monotonic() + 5
        while time.monotonic() < deadline and (not marker.exists() or process_identity(int(guard_pid.read_text())) is not None):
            time.sleep(.05)
        self.assertTrue(marker.is_file())
        self.assertIsNone(process_identity(int(guard_pid.read_text())))
        self.assertEqual('read-only', json.loads(marker.read_text())['mode'])


if __name__ == '__main__':
    unittest.main()
