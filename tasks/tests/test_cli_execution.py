import contextlib
import io
import json
import sys
import tempfile
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
from tasks.queue_engine.cli import main
from tasks.queue_engine.storage import QueueStorage
from tasks.queue_engine.audit import RecoveryManager


def fixture_card(root, version='v0.1'):
    return f'''# Test task
- **task_id**：example
- **stage**：S1（阶段一 {version}）
- **M1 声明**：isolated integration fixture
## goal
Run a harmless isolated fixture.
## acceptance[]
- [ ] ACCEPT: structured result
## dependsOn[]
- 无
## fileDomain[]
- `{root}`
## priority
- 50
## reasoningEffort
- high
## category + skill
- category: system; skill: eng.code
## receipt
- reviewReason: pending
- stdoutText: pending
- evidence: pending
## retryCount
- 0
'''


class CliExecutionTests(unittest.TestCase):
    def run_result(self, output, exit_code=0, paused=False, version='v0.1'):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = root / 'card.md'
            card.write_text(fixture_card(root, version), encoding='utf-8')
            task = dict(task_id='example', state='QUEUED', priority=50,
                        dependsOn=[], parallelGroup=None, fileDomain=[raw],
                        reasoningEffort='high', created_at='2026-10-21',
                        updated_at='2026-10-21', terminal_reason=None, card_path=str(card))
            QueueStorage(root).save_tasks([task])
            if paused:
                (root / '.pause-dispatch').touch()
            with contextlib.redirect_stdout(io.StringIO()):
                code = main(['--root', raw, 'run', 'example', '--', sys.executable,
                             '-c', f'print({output!r});raise SystemExit({exit_code})'])
            return code, QueueStorage(root).load_tasks()[0]['state']

    def test_exit_zero_without_business_proof_is_blocked(self):
        self.assertEqual((2, 'BLOCKED'), self.run_result('plain output'))

    def test_business_failure_does_not_pass(self):
        self.assertEqual((2, 'FAILED'), self.run_result('{"business_success":false}'))

    def test_nonzero_exit_overrides_success_text(self):
        self.assertEqual((2, 'FAILED'), self.run_result('{"business_success":true}', 7))

    def test_chinese_business_receipt_is_utf8(self):
        self.assertEqual((0, 'AUDIT'), self.run_result('{"business_success":true,"message":"中文验收回执"}'))

    def test_pause_leaves_real_task_queued(self):
        self.assertEqual((2, 'QUEUED'), self.run_result('{"business_success":true}', paused=True))

    def test_text_task_cannot_bypass_unfrozen_v01(self):
        self.assertEqual((2, 'QUEUED'), self.run_result('{"business_success":true}', version='v0.3'))

    def test_invalid_card_rejected_even_if_file_exists(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = root / 'card.md'
            card.write_text('unrelated existing file', encoding='utf-8')
            task = dict(task_id='example', state='QUEUED', priority=50,
                        dependsOn=[], parallelGroup=None, fileDomain=[raw],
                        reasoningEffort='high', created_at='2026-10-21',
                        updated_at='2026-10-21', terminal_reason=None, card_path=str(card))
            spec = root / 'task.json'
            spec.write_text(json.dumps(task), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(2, main(['--root', raw, 'enqueue', str(spec)]))
            self.assertEqual([], QueueStorage(root).load_tasks())

    def test_index_dependency_must_match_card(self):
        from tasks.queue_engine.card_contract import validate_card
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = root / 'card.md'
            card.write_text(fixture_card(root), encoding='utf-8')
            with self.assertRaisesRegex(ValueError, 'fileDomain'):
                validate_card(dict(task_id='example', card_path=str(card), dependsOn=['hidden'],
                                   fileDomain=[raw], priority=50, reasoningEffort='high'), root)

    def test_requeue_priority_change_remains_executable(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = root / 'card.md'
            card.write_text(fixture_card(root), encoding='utf-8')
            task = dict(task_id='example', state='QUEUED', priority=50,
                        dependsOn=[], parallelGroup=None, fileDomain=[raw],
                        reasoningEffort='high', created_at='2026-10-21',
                        updated_at='2026-10-21', terminal_reason=None, card_path=str(card))
            storage = QueueStorage(root)
            storage.save_tasks([task, dict(task, task_id='target', priority=80)])
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(['--root', raw, 'requeue', 'example', '--before',
                                         'target', '--reason', 'explicit priority change']))
                self.assertEqual(0, main(['--root', raw, 'run', 'example', '--', sys.executable,
                                         '-c', 'print(\'{"business_success":true}\')']))
            self.assertEqual('AUDIT', storage.load_tasks()[0]['state'])

    def test_missing_completion_keeps_capacity_reserved(self):
        from tasks.queue_engine.dispatcher import Dispatcher
        with tempfile.TemporaryDirectory() as raw:
            storage = QueueStorage(raw)
            task = dict(task_id='orphan', state='EXECUTING', priority=50,
                        dependsOn=[], parallelGroup=None, fileDomain=[raw],
                        reasoningEffort='high', created_at='2026-10-21',
                        updated_at='2026-10-21', terminal_reason=None, card_path='card.md')
            candidate = dict(task, task_id='next', state='QUEUED')
            storage.save_tasks([task, candidate])
            paths = storage.create_run_artifacts('orphan')
            paths['session'].write_text('{"pid":2147483647}', encoding='utf-8')
            recovered, _ = RecoveryManager(storage).recover_finished_run('orphan')
            self.assertEqual('EXECUTING', recovered['state'])
            RecoveryManager(storage).block_nonterminal_closeout()
            self.assertEqual('EXECUTING', storage.load_tasks()[0]['state'])
            self.assertFalse(Dispatcher(storage).dispatch('next', [sys.executable, '-c', 'pass']).dispatched)

    def test_malformed_done_fails_closed_instead_of_crashing(self):
        with tempfile.TemporaryDirectory() as raw:
            storage = QueueStorage(raw)
            task = dict(task_id='bad', state='EXECUTING', priority=50,
                        dependsOn=[], parallelGroup=None, fileDomain=[raw],
                        reasoningEffort='high', created_at='2026-10-21',
                        updated_at='2026-10-21', terminal_reason=None, card_path='card.md')
            storage.save_tasks([task])
            paths = storage.create_run_artifacts('bad')
            paths['session'].write_text('{"pid":2147483647}', encoding='utf-8')
            paths['done'].write_text('[]', encoding='utf-8')
            recovered, _ = RecoveryManager(storage).recover_finished_run('bad')
            self.assertEqual('BLOCKED', recovered['state'])

    def test_real_command_reaches_audit_without_self_approval(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = root / 'card.md'
            card.write_text(fixture_card(root), encoding='utf-8')
            task = dict(task_id='example', state='QUEUED', priority=50,
                        dependsOn=[], parallelGroup=None, fileDomain=[raw],
                        reasoningEffort='high', created_at='2026-10-21',
                        updated_at='2026-10-21', terminal_reason=None,
                        card_path=str(card))
            spec = root / 'task.json'
            spec.write_text(json.dumps(task), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(0, main(['--root', raw, 'enqueue', str(spec)]))
                self.assertEqual(0, main(['--root', raw, 'run', 'example', '--',
                                        sys.executable, '-c',
                                        'print(\'{"business_success":true}\')']))
                self.assertEqual(2, main(['--root', raw, 'run', 'example', '--',
                                        sys.executable, '-c', 'raise Exception()']))
            self.assertEqual('AUDIT', QueueStorage(root).load_tasks()[0]['state'])
            self.assertEqual(1, len(list((root / 'runs/example').glob('*.done'))))

    def test_enqueue_missing_card_never_creates_task(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            task = dict(task_id='missing', state='QUEUED', priority=50,
                        dependsOn=[], parallelGroup=None, fileDomain=[raw],
                        reasoningEffort='high', created_at='2026-10-21',
                        updated_at='2026-10-21', terminal_reason=None,
                        card_path='missing.md')
            spec = root / 'task.json'
            spec.write_text(json.dumps(task), encoding='utf-8')
            with contextlib.redirect_stdout(io.StringIO()):
                self.assertEqual(2, main(['--root', raw, 'enqueue', str(spec)]))
            self.assertEqual([], QueueStorage(root).load_tasks())


if __name__ == '__main__':
    unittest.main()
