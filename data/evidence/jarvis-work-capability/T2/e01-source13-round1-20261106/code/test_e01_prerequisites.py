"""E01 must consume four qualified same-candidate E03 results, without native I/O."""
import json
import shutil
from pathlib import Path

import pytest

import acceptance_entry as entry
from package_io import load, sha

INPUTS = Path(__file__).resolve().parents[1] / 'inputs'


def put(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


@pytest.fixture
def material(tmp_path):
    shutil.copytree(INPUTS, tmp_path / 'inputs')
    return tmp_path


def rebind(root):
    folder = root / 'inputs/prior-negative'
    terminal, review, registration, manifest = (load(folder / name) for name in
        ('terminal.json', 'review.json', 'registration.json', 'result-manifest.json'))
    terminal['negative_result_sha256'] = sha(folder / 'negative-evidence.json')
    put(folder / 'terminal.json', terminal)
    manifest['terminal_sha256'] = sha(folder / 'terminal.json')
    for row in manifest['files']:
        local = {'actual/e03-negative/terminal.json': 'terminal.json',
                 'actual/e03-negative/negative-evidence.json': 'negative-evidence.json'}.get(row['path'])
        if local:
            row.update(sha256=sha(folder / local), bytes=(folder / local).stat().st_size)
    put(folder / 'result-manifest.json', manifest)
    review.update(terminal_sha256=sha(folder / 'terminal.json'),
                  negative_result_sha256=sha(folder / 'negative-evidence.json'),
                  result_manifest_sha256=sha(folder / 'result-manifest.json'))
    put(folder / 'review.json', review)
    registration.update(terminal_sha256=sha(folder / 'terminal.json'),
                        result_review_sha256=sha(folder / 'review.json'),
                        result_manifest_sha256=sha(folder / 'result-manifest.json'))
    registration['negative_terminal_binding'].update(
        terminal_sha256=sha(folder / 'terminal.json'), review_sha256=sha(folder / 'review.json'),
        finished_at=terminal['finished_at'])
    put(folder / 'registration.json', registration)


def test_e01_scope_and_complete_four_case_prerequisite(material):
    assert entry.CASE == 'e01-round1' and entry.SCOPE == 'e01-round1-acceptance'
    result = entry.predecessor_reviews(material)
    assert [row['case'] for row in result] == ['e03-round1', 'e03-round2', 'e03-round3', 'e03-negative']
    assert result[-1]['registration_sha256'] == sha(material / 'inputs/prior-negative/registration.json')


@pytest.mark.parametrize('name', ['terminal', 'review', 'registration', 'result-manifest', 'negative-evidence'])
def test_missing_negative_input_cannot_be_ignored(material, name):
    (material / 'inputs/prior-negative' / (name + '.json')).unlink()
    with pytest.raises((FileNotFoundError, ValueError)):
        entry.predecessor_reviews(material)


@pytest.mark.parametrize('name,field,value', [
    ('terminal', 'candidate', 'old'),
    ('terminal', 'case', 'e03-round1'),
    ('terminal', 'overall', 'FAIL'),
    ('terminal', 'mechanical', 'FAIL'),
    ('terminal', 'acceptance_credit', True),
    ('terminal', 'work_cli_count', True),
    ('terminal', 'model_requests', 1),
    ('terminal', 'errors', [{'error': 'preserved failure'}]),
    ('review', 'reviewer', 'root'),
    ('review', 'scope', 'e03-negative-acceptance-package'),
    ('review', 'verdict', 'FAIL'),
    ('review', 'behavior_verdict', 'FAIL'),
    ('review', 'target_verdict', 'FAIL'),
    ('review', 'file_verdict', 'FAIL'),
    ('review', 'cleanup_verdict', 'FAIL'),
    ('review', 'environment_verdict', 'FAIL'),
    ('review', 'facts_scope.status', 'PASS'),
    ('review', 'facts_scope.generated_content_present', True),
    ('review', 'acceptance_credit_recommended', False),
    ('review', 'execution_counts.reruns_or_retries_recorded', 1),
    ('registration', 'acceptance_credit', False),
    ('registration', 'negative_cases_passed', 0),
    ('registration', 'same_candidate_terminals', 3),
    ('registration', 'E03', 'PENDING'),
    ('registration', 'predecessor_registration_sha256', '0' * 64),
])
def test_semantically_ineligible_negative_is_rejected_after_rebinding(material, name, field, value):
    path = material / 'inputs/prior-negative' / (name + '.json')
    data = load(path)
    target = data
    keys = field.split('.')
    for key in keys[:-1]:
        target = target[key]
    target[keys[-1]] = value
    put(path, data)
    rebind(material)
    with pytest.raises(ValueError):
        entry.predecessor_reviews(material)


@pytest.mark.parametrize('index,field,value', [(0, 'review_sha256', '0' * 64),
    (1, 'task_id', 'duplicate'), (2, 'candidate', 'old')])
def test_negative_registration_must_bind_actual_qualified_positives(material, index, field, value):
    path = material / 'inputs/prior-negative/registration.json'
    data = load(path)
    data['positive_terminal_bindings'][index][field] = value
    put(path, data)
    with pytest.raises(ValueError):
        entry.predecessor_reviews(material)
