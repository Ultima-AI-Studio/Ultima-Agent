import importlib.util
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

ROOT = Path(__file__).resolve().parents[2]
spec = importlib.util.spec_from_file_location('host_selfcheck_entry', ROOT / 'scripts/selfcheck-host-shell.py')
entry = importlib.util.module_from_spec(spec)
spec.loader.exec_module(entry)

class FailureReceipts(unittest.TestCase):
    def check_failure(self, monitor, build=None):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            project = root / 'scripts/HostSelfcheck'
            project.mkdir(parents=True)
            (project / 'HostSelfcheck.csproj').write_text('<Project />')
            (root / 'src/host-shell/UltimaAgent.HostShell').mkdir(parents=True)
            evidence = root / 'logs/run'
            with patch.object(entry, 'ROOT', root), patch.object(entry, 'WindowMonitor', return_value=monitor), \
                 patch.object(entry.subprocess, 'run', return_value=build) as run, \
                 patch.object(entry.sys, 'argv', ['selfcheck', '--evidence', str(evidence)]):
                self.assertEqual(entry.main(), 1)
                result = json.loads((evidence / 'entry-result.json').read_text(encoding='utf-8'))
                self.assertEqual(result['status'], 'FAIL')
                self.assertTrue(result['error'])
                self.assertTrue((evidence / 'report.md').exists())
                return run.call_count

    def test_unavailable_monitor_writes_failure_without_launch(self):
        class MissingMonitor:
            def start(self):
                raise RuntimeError('hook unavailable')
        self.assertEqual(self.check_failure(MissingMonitor()), 0)

    def test_monitor_stop_error_retains_failure_receipt(self):
        class BrokenMonitor:
            thread = object()
            pids = {1}
            samples = 2
            def start(self):
                return self
            def stop(self):
                raise RuntimeError('observer failed')
        class FailedBuild:
            returncode = 1
        self.assertEqual(self.check_failure(BrokenMonitor(), FailedBuild()), 1)

if __name__ == '__main__':
    unittest.main()
