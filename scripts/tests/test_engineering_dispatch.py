import importlib.util
from pathlib import Path
import tempfile
import unittest

ROOT = Path(__file__).resolve().parents[2]


def module(name, filename):
    spec = importlib.util.spec_from_file_location(name, ROOT / 'scripts' / filename)
    loaded = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(loaded)
    return loaded


class DispatchContracts(unittest.TestCase):
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
