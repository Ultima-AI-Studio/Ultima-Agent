"""E01 round2 may consume only a fully reviewed same-candidate first round."""
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
    shutil.copytree(INPUTS, tmp_path/'inputs')
    return tmp_path


def rebind(root):
    folder = root/'inputs/prior-e01-round1'
    terminal, review, registration = (load(folder/(name+'.json')) for name in ('terminal','review','registration'))
    review.update(terminal_sha256=sha(folder/'terminal.json'),
                  preparation_manifest_sha256=terminal['package_manifest_sha256'],
                  product_result_sha256=terminal['product_result_sha256'])
    put(folder/'review.json',review)
    registration.update(terminal_sha256=sha(folder/'terminal.json'),result_review_sha256=sha(folder/'review.json'))
    registration['same_candidate_e01_terminal_bindings'][0].update(
        terminal_sha256=sha(folder/'terminal.json'),review_sha256=sha(folder/'review.json'),finished_at=terminal['finished_at'])
    put(folder/'registration.json',registration)


def test_round2_scope_requires_five_ordered_credentials(material):
    assert entry.CASE == 'e01-round3' and entry.SCOPE == 'e01-round3-acceptance'
    bindings = entry.first_e01_predecessor_reviews(material)
    assert [row['case'] for row in bindings] == ['e03-round1','e03-round2','e03-round3','e03-negative','e01-round1']
    assert bindings[-1]['registration_sha256'] == sha(material/'inputs/prior-e01-round1/registration.json')


@pytest.mark.parametrize('name',['terminal','review','registration'])
def test_missing_e01_first_round_cannot_be_ignored(material,name):
    (material/'inputs/prior-e01-round1'/(name+'.json')).unlink()
    with pytest.raises((ValueError,FileNotFoundError)):
        entry.first_e01_predecessor_reviews(material)


@pytest.mark.parametrize('name,field,value',[
    ('terminal','candidate','old'),('terminal','scope','e03-round1-acceptance'),
    ('terminal','overall','FAIL'),('terminal','mechanical','FAIL'),
    ('terminal','acceptance_credit',True),('terminal','work_cli_count',True),
    ('terminal','work_cli_count',2),('terminal','retry_authorized',True),
    ('terminal','cleanup.status','FAIL'),('terminal','errors',[{'error':'failure retained'}]),
    ('review','reviewer','root'),('review','scope','e01-round1-acceptance-package'),
    ('review','facts_verdict','FAIL'),('review','file_verdict','FAIL'),
    ('review','final_claim_verdict','FAIL'),('review','cleanup_verdict','FAIL'),
    ('review','target_verdict','PASS'),('review','independent_from_preparation_reviewer',False),
    ('review','no_new_facts.verdict','FAIL'),
    ('review','execution.model','unapproved-model'),('review','execution.model_digest','0'*64),
    ('review','execution.work_cli_launches',2),('review','execution.automatic_retry_recorded',True),
    ('review','recommendation.acceptance_credit_recommended',False),
    ('registration','facts','FAIL'),('registration','acceptance_credit',False),
    ('registration','positive_passed',0),('registration','positive_required',2),
    ('registration','same_candidate_e01_terminals',2),
    ('registration','E03_prerequisite_registration_sha256','0'*64),
    ('registration','artifact_sha256','0'*64),('registration','current_case_work_cli_count',0),
])
def test_ineligible_first_round_stops_after_consistent_rehash(material,name,field,value):
    path = material/'inputs/prior-e01-round1'/(name+'.json')
    data = load(path)
    target = data
    keys = field.split('.')
    for key in keys[:-1]: target = target[key]
    target[keys[-1]] = value
    put(path,data)
    rebind(material)
    with pytest.raises(ValueError): entry.first_e01_predecessor_reviews(material)


def test_e01_first_round_cannot_predate_completed_e03_chain(material):
    path = material/'inputs/prior-e01-round1/terminal.json'
    data = load(path)
    data['finished_at'] = load(material/'inputs/prior-negative/terminal.json')['finished_at']
    put(path,data)
    rebind(material)
    with pytest.raises(ValueError): entry.first_e01_predecessor_reviews(material)


def test_registration_cannot_substitute_another_task(material):
    folder = material/'inputs/prior-e01-round1'
    other_task = load(material/'inputs/prior-round3/review.json')['execution']['task_id']
    review = load(folder/'review.json');review['execution']['task_id'] = other_task;put(folder/'review.json',review)
    registration = load(folder/'registration.json');registration['task_id'] = other_task
    registration['same_candidate_e01_terminal_bindings'][0]['task_id'] = other_task
    put(folder/'registration.json',registration);rebind(material)
    with pytest.raises(ValueError): entry.first_e01_predecessor_reviews(material)
