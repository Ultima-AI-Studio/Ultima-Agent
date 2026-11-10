"""Focused regression for R1; imports only the pure metadata reconciliation helper."""
from pathlib import Path
import copy
import importlib.util
import json
import unittest

N = Path(__file__).resolve().parents[1]
spec = importlib.util.spec_from_file_location('completion_aliases', N / 'review/reconcile_completion_aliases.py')
fix = importlib.util.module_from_spec(spec)
spec.loader.exec_module(fix)

class CompletionAliasesTests(unittest.TestCase):
    def setUp(self):
        self.state = json.loads((N / 'inputs/previous-current-run.json').read_bytes())
        self.state.update(phase=fix.PHASE, active_candidate=fix.HEAD,
            preparation_test_count=346,
            preparation_review_receipt=str(N / 'review/independent-preparation-review.json'),
            next_work='Explicitly allocate one case and one result review on the concrete proposal before actual execution',
            actual_case_allocation_remaining=0, result_review_allocation_remaining=0,
            live_gate_released=False, next_stage_released=False, t2='NOT_PASSED', owner_gate='NOT_PASSED')

    def test_review_and_test_count_use_current_preparation(self):
        result = fix.reconcile(self.state)
        self.assertEqual(result['preparation_review_path'], self.state['preparation_review_receipt'])
        self.assertEqual(result['preparation_tests_passed'], 346)

    def test_next_action_waits_for_current_proposal_without_old_offline_plan(self):
        result = fix.reconcile(self.state)
        self.assertEqual(result['next_action'], self.state['next_work'])
        self.assertIsNone(result['next_offline_plan'])

    def test_local_tag_and_sync_point_to_current_readback(self):
        result = fix.reconcile(self.state)
        self.assertEqual(result['local_checkpoint_tag'], fix.TAG)
        self.assertEqual(result['preparation_sync']['local_tag'], fix.TAG)
        self.assertEqual(result['preparation_sync']['publication_receipt'], str(N / 'verification/publication-readback.json'))
        self.assertFalse(result['preparation_sync']['remote_synced'])
        self.assertFalse(result['preparation_sync']['new_push_attempted'])
        self.assertFalse(result['remote_sync']['remote_synced'])
        self.assertEqual(result['remote_sync']['status'], 'EXISTING_AUTOMATIC_APPROVAL_BLOCK')

    def test_only_named_aliases_change_and_old_values_remain_explicit_history(self):
        result = fix.reconcile(self.state)
        self.assertEqual(result.get(fix.HISTORY), {k:self.state[k] for k in fix.KEYS})
        for key, value in self.state.items():
            if key not in fix.KEYS:
                self.assertEqual(result[key], value, key)
        self.assertEqual(set(result) - set(self.state), {fix.HISTORY})

    def test_input_actual_history_and_gates_remain_unchanged(self):
        before = copy.deepcopy(self.state)
        result = fix.reconcile(self.state)
        self.assertEqual(self.state, before)
        self.assertEqual(result['last_actual_result'], before['last_actual_result'])
        self.assertEqual(result['actual_case_allocation_remaining'], 0)
        self.assertFalse(result['live_gate_released'])

    def test_refuses_other_phase_candidate_actual_allocation_or_repeated_application(self):
        for key, value in [('phase','OLD'), ('active_candidate','other'),
            ('actual_case_allocation_remaining',1), ('result_review_allocation_remaining',1),
            ('live_gate_released',True), ('next_stage_released',True), (fix.HISTORY,{})]:
            with self.subTest(key=key):
                changed = dict(self.state, **{key:value})
                with self.assertRaises(AssertionError):
                    fix.reconcile(changed)

if __name__ == '__main__':
    unittest.main(verbosity=2)
