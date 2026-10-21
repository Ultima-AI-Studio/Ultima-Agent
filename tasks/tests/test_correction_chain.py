import json
from pathlib import Path
import sys
import tempfile
import unittest

sys.path[:0] = [str(Path(__file__).resolve().parents[2]), str(Path(__file__).resolve().parent)]
from test_cli_execution import fixture_card
from tasks.queue_engine.audit import RecoveryManager
from tasks.queue_engine.dispatcher import Dispatcher
from tasks.queue_engine.storage import QueueStorage
from tasks.queue_engine.state_machine import StateMachine
from tasks.queue_engine.card_contract import validate_card


class CorrectionTests(unittest.TestCase):
    def test_actual_correction_card_holds_original_until_audit_and_bounds_retries(self):
        with tempfile.TemporaryDirectory() as raw:
            root = Path(raw)
            card = root / 'cards/example/task.md'
            card.parent.mkdir(parents=True)
            card.write_text(fixture_card(root), encoding='utf-8')
            task = dict(task_id='example', state='FAILED', priority=50, dependsOn=[],
                        parallelGroup=None, fileDomain=[raw], reasoningEffort='high',
                        created_at='2026-10-21', updated_at='2026-10-21',
                        terminal_reason='actual failure', card_path=str(card))
            storage = QueueStorage(root)
            storage.save_tasks([task])
            repair = RecoveryManager(storage)
            first = repair.create_correction('example', actor='brain', reason='修复已复现的问题')
            self.assertEqual('example~r1', first['task_id'])
            validate_card(first, root)
            tasks = storage.load_tasks()
            self.assertEqual(['example~r1'], tasks[0]['dependsOn'])
            validate_card(tasks[0], root)
            self.assertFalse(Dispatcher(storage).dispatch('example', [sys.executable, '-c', 'pass']).dispatched)
            self.assertTrue((root / 'archive/example~r1.parent-before.md').is_file())
            # A second explicit failure creates a distinct child and preserves all old evidence.
            machine = StateMachine(storage)
            running, _ = machine.transition(tasks[0], 'EXECUTING', actor='test', reason='isolated state exercise')
            failed, _ = machine.transition(running, 'FAILED', actor='test', reason='second failure')
            storage.save_tasks([failed, *tasks[1:]])
            second = repair.create_correction('example', actor='brain', reason='第二次修正')
            self.assertEqual('example~r2', second['task_id'])
            tasks = storage.load_tasks()
            running, _ = machine.transition(tasks[0], 'EXECUTING', actor='test', reason='isolated state exercise')
            failed, _ = machine.transition(running, 'FAILED', actor='test', reason='third failure')
            storage.save_tasks([failed, *tasks[1:]])
            exhausted = repair.create_correction('example', actor='brain', reason='不得绕过上限')
            self.assertEqual('BLOCKED', exhausted['state'])
            self.assertEqual(3, len(storage.load_tasks()))
            self.assertTrue(Path(first['card_path']).is_file())

    def test_correction_release_rejects_untrusted_actor(self):
        with tempfile.TemporaryDirectory() as raw:
            with self.assertRaises(ValueError):
                RecoveryManager(QueueStorage(raw)).create_correction('anything', actor='watchdog', reason='retry')


if __name__ == '__main__':
    unittest.main()
