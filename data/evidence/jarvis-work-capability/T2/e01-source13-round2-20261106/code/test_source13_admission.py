"""Admission rejects the observed missing lazy dependency before any live call."""
import hashlib
import json

import pytest

import source_candidate_guard as guard


def runtime(tmp_path, *, dependency=True, pin_dependency=True):
    root = tmp_path / 'repo'
    files = {
        'src/brain/agent_server.py':
            'import importlib\ndef _ensure_tools_registered():\n    importlib.import_module(".agent_tools_ultima", __package__)\n',
        'src/brain/agent_tools_ultima.py': '',
        'src/brain/exec/channel.py': 'from ..environment_upgrade import scan_processes\n',
        'src/brain/environment.py': 'class EnvironmentSnapshot: pass\n',
    }
    if dependency:
        files['src/brain/environment_upgrade.py'] = 'from .environment import EnvironmentSnapshot\ndef scan_processes(): pass\n'
    pins = set()
    for name, text in files.items():
        path = root / name
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text, encoding='utf8')
        if pin_dependency or name != 'src/brain/environment_upgrade.py':
            pins.add(path.resolve())
    return root.resolve(), pins


@pytest.mark.parametrize('dependency,pinned,expected', [
    (False, False, 'unresolved project runtime import src.brain.environment_upgrade'),
    (True, False, 'unbound project runtime import src/brain/environment_upgrade.py'),
])
def test_missing_or_unpinned_lazy_exec_dependency_rejected_before_launch(tmp_path, dependency, pinned, expected):
    root, pins = runtime(tmp_path, dependency=dependency, pin_dependency=pinned)
    with pytest.raises(guard.CandidateError, match=expected):
        guard._verify_work_agent_dynamic_imports(root, pins)


def test_pinned_lazy_exec_dependency_and_original_registration_are_accepted(tmp_path):
    root, pins = runtime(tmp_path)
    guard._verify_work_agent_dynamic_imports(root, pins)


@pytest.mark.parametrize('candidate', ['7975e477665c02820fa235b73d203718bd33b2c9', None])
def test_historical_or_unbound_test_receipt_cannot_admit_new_candidate(tmp_path, candidate):
    path = tmp_path / 'receipt.json'
    path.write_text(json.dumps(dict(candidate=candidate, counts=dict(tests=485, failures=0, errors=0, skipped=0),
                                    exit_code=0, source_unchanged=True)), encoding='utf8')
    with pytest.raises(guard.CandidateError, match='receipt candidate mismatch'):
        guard._verify_receipt(str(path), hashlib.sha256(path.read_bytes()).hexdigest(), 'covering', 485)


def test_current_candidate_receipt_is_accepted(tmp_path):
    path = tmp_path / 'receipt.json'
    path.write_text(json.dumps(dict(candidate=guard.EXPECTED_CANDIDATE,
                                    counts=dict(tests=485, failures=0, errors=0, skipped=0),
                                    exit_code=0, source_unchanged=True)), encoding='utf8')
    guard._verify_receipt(str(path), hashlib.sha256(path.read_bytes()).hexdigest(), 'covering', 485)
