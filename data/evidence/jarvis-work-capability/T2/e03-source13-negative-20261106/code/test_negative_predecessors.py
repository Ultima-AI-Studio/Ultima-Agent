"""Third-positive eligibility and restored-runtime bindings; all file I/O stays in tmp_path."""
import copy
import json
import shutil
from pathlib import Path

import pytest

import acceptance_entry as entry
from package_io import load, sha

INPUTS = Path(__file__).resolve().parents[1] / 'inputs'
VERDICTS = ('evidence_verdict', 'case_verdict', 'mechanical_verdict', 'facts_verdict',
            'target_verdict', 'file_verdict', 'final_claim_verdict', 'cleanup_verdict')


def put(path, value):
    path.write_text(json.dumps(value, ensure_ascii=False), encoding='utf-8')


@pytest.fixture
def material(tmp_path):
    shutil.copytree(INPUTS, tmp_path/'inputs')
    return tmp_path


def file(root, round_no, name):
    return root/'inputs'/('prior-round'+str(round_no))/(name+'.json')


def rebind(root):
    """Recompute receipt hashes after semantic mutation, without calling the validator."""
    bindings = []
    cumulative = []
    for n in (1, 2, 3):
        tp, rp, gp = (file(root,n,name) for name in ('terminal','review','registration'))
        terminal, review, registration = load(tp), load(rp), load(gp)
        review['terminal_sha256'] = sha(tp)
        review['preparation_manifest_sha256'] = terminal['package_manifest_sha256']
        review['product_result_sha256'] = terminal['product_result_sha256']
        if n == 2:
            review['authority_and_admission']['prior_round1'].update(
                {k:bindings[0][k] for k in ('terminal_sha256','review_sha256','registration_sha256')})
        put(rp, review)
        row = dict(case='e03-round'+str(n),candidate=entry.HEAD,sha256=sha(tp),review_sha256=sha(rp),
                   raw_overall=terminal['overall'],work_cli_count=terminal['work_cli_count'],case_verdict='PASS',
                   task_id=review['execution']['task_id'],finished_at=terminal['finished_at'])
        cumulative.append(row)
        registration.update(terminal_sha256=sha(tp),result_review_sha256=sha(rp))
        if n >= 2:
            registration.update(predecessor_registration_sha256=bindings[-1]['registration_sha256'],
                                same_candidate_terminal_bindings=copy.deepcopy(cumulative))
        put(gp, registration)
        bindings.append(dict(case='e03-round'+str(n),candidate=entry.HEAD,terminal_sha256=sha(tp),
                             review_sha256=sha(rp),registration_sha256=sha(gp)))
    return bindings


def mutate(root, n, name, field, value):
    p=file(root,n,name);d=load(p)
    target=d
    keys=field.split('.')
    for k in keys[:-1]:target=target[k]
    target[keys[-1]]=value;put(p,d)
    rebind(root)


def test_three_actual_distinct_passes_and_reconciled_runtime_are_required(material):
    actual=entry.predecessor_reviews(material)
    assert [x['case'] for x in actual] == ['e03-round1','e03-round2','e03-round3']
    assert actual[2]['terminal_sha256'] == sha(file(material,3,'terminal'))
    assert actual[2]['review_sha256'] == sha(file(material,3,'review'))
    assert actual[2]['registration_sha256'] == sha(file(material,3,'registration'))
    assert load(file(material,3,'review'))['environment_verdict'] == 'FAIL_POST_CASE_RUNTIME_ADMISSION_BLOCKED'
    assert not (material/'actual').exists()


@pytest.mark.parametrize('name,field,value', [
    ('terminal','mechanical','FAIL'),
    ('terminal','work_cli_count',2),
    ('review','candidate','old-candidate'),
    ('review','facts_verdict','FAIL'),
    ('review','target_verdict','FAIL'),
    ('review','file_verdict','FAIL'),
    ('review','cleanup_verdict','FAIL'),
    ('review','execution.model_digest','wrong-weight'),
    ('review','limits.actual_reruns_or_retries',1),
    ('review','credit.third_positive_credit_recommended',False),
    ('registration','acceptance_credit',False),
    ('registration','positive_passed',2),
    ('registration','negative_passed',True),
])
def test_third_receipt_ineligible_despite_consistent_hashes(material,name,field,value):
    mutate(material,3,name,field,value)
    with pytest.raises(ValueError):entry.predecessor_reviews(material)


@pytest.mark.parametrize('round_no', [2,3])
def test_coherently_rebound_duplicate_task_is_rejected(material,round_no):
    first_task=load(file(material,1,'review'))['execution']['task_id']
    mutate(material,round_no,'review','execution.task_id',first_task)
    with pytest.raises(ValueError,match='distinct tasks'):entry.predecessor_reviews(material)


@pytest.mark.parametrize('round_no', [2,3])
def test_coherently_rebound_backwards_actual_terminal_is_rejected(material,round_no):
    first_time=load(file(material,1,'terminal'))['finished_at']
    mutate(material,round_no,'terminal','finished_at',first_time)
    with pytest.raises(ValueError,match='chronology'):entry.predecessor_reviews(material)


@pytest.mark.parametrize('round_no', [2,3])
def test_missing_cumulative_terminal_row_is_rejected(material,round_no):
    p=file(material,round_no,'registration');d=load(p);d['same_candidate_terminal_bindings'].pop();put(p,d)
    # Round2 registration's hash is deliberately propagated into the third receipt.
    if round_no==2:
        p3=file(material,3,'registration');d3=load(p3);d3['predecessor_registration_sha256']=sha(p);put(p3,d3)
    with pytest.raises(ValueError):entry.predecessor_reviews(material)


@pytest.mark.parametrize('name,field,value', [
    ('runtime-reconciliation.json','status','FAIL_RUNTIME_RECONCILIATION'),
    ('runtime-reconciliation.json','native_version','unreviewed-version'),
    ('runtime-reconciliation.json','current_model.digest','wrong-weight'),
    ('runtime-reconciliation.json','actual_cases',1),
    ('runtime-reconciliation.json','model_inferences',1),
    ('runtime-reconciliation.json','other_six.0.match',False),
    ('protected-baseline.json','protected5.0.pid',15264),
    ('protected-baseline.json','protected5.1.command_line_sha256','changed-brain'),
    ('runtime-manual-confirmation.json','performed_by','unknown'),
])
def test_unreconciled_runtime_cannot_admit_despite_three_positives(material,name,field,value):
    p=material/'inputs'/name;d=load(p);target=d;keys=field.split('.')
    for key in keys[:-1]:target=target[int(key)] if isinstance(target,list) else target[key]
    if isinstance(target,list):target[int(keys[-1])]=value
    else:target[keys[-1]]=value
    put(p,d)
    if name=='runtime-reconciliation.json':
        bp=material/'inputs/protected-baseline.json';b=load(bp);b['runtime_reconciliation_sha256']=sha(p);put(bp,b)
    with pytest.raises(ValueError):entry.predecessor_reviews(material)


def test_missing_recovery_evidence_refuses_even_with_valid_three_passes(material):
    (material/'inputs/runtime-reconciliation.json').unlink()
    with pytest.raises((ValueError,FileNotFoundError)):entry.predecessor_reviews(material)
