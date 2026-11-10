"""One E01 file-delivery entry, bound to the completed same-candidate E03 group."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import sys
import uuid

from package_io import child, load, require, safe_path, save_new, sha

HEAD = '269aca511d88412dbb9c15d23911138469a37aa2'
CANDIDATE_MANIFEST = '957669cb3463eab549df80f0b8fc6345c244daa2f613925abe8622d0aab3d9d3'
MODEL = 'qwen3-8b-uncensored'
DIGEST = '6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330'
CASE = 'e01-round2'
SCOPE = 'e01-round2-acceptance'
PYTHON = Path(r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe')
RUNTIME_FILES = {'code/acceptance_entry.py', 'code/acceptance_backend.py', 'code/package_io.py',
                 'code/fixture_manual_start.py',
                 'code/controller.py', 'code/fixture_adapter.py', 'code/fixture_input_origin.py',
                 'code/source_candidate_guard.py', 'preparation-support/acceptance_adapter.py',
                 'inputs/protected-baseline.json', 'inputs/candidate-runtime-manifest.json',
                 'inputs/prior-round1/terminal.json', 'inputs/prior-round1/review.json',
                 'inputs/prior-round1/registration.json',
                 'inputs/prior-round2/terminal.json', 'inputs/prior-round2/review.json',
                 'inputs/prior-round2/registration.json',
                 'inputs/prior-round3/terminal.json', 'inputs/prior-round3/review.json',
                 'inputs/prior-round3/registration.json', 'inputs/runtime-reconciliation.json',
                 'inputs/runtime-user-approval.json', 'inputs/runtime-manual-confirmation.json',
                 'inputs/protected-baseline-before-recovery.json',
                 'inputs/prior-negative/terminal.json', 'inputs/prior-negative/review.json',
                 'inputs/prior-negative/registration.json', 'inputs/prior-negative/result-manifest.json',
                 'inputs/prior-negative/negative-evidence.json',
                 'inputs/prior-e01-round1/terminal.json', 'inputs/prior-e01-round1/review.json',
                 'inputs/prior-e01-round1/registration.json'}
AUTH_FIELDS = {'schema', 'issuer', 'scope', 'case', 'candidate', 'candidate_manifest_sha256',
               'model', 'digest', 'manifest_sha256', 'review_sha256', 'proof_path', 'proof_sha256',
               'case_cap', 'product_cli_cap', 'audio_actions', 'retry_authorized', 'acceptance_credit',
               'prior_reviews', 'user_authorization', 'issued_at', 'expires_at'}
PROTECTED_FIELDS = ('pid', 'created_filetime', 'exe', 'parent_pid', 'command_line_sha256')


def utcnow():
    return dt.datetime.now(dt.timezone.utc)


def timestamp(value):
    require(isinstance(value, str), 'Timestamp string required')
    result = dt.datetime.fromisoformat(value)
    require(result.tzinfo is not None, 'Timezone-aware timestamp required')
    return result


def check_admission_time(authority, proof, now):
    issued, expires = timestamp(authority['issued_at']), timestamp(authority['expires_at'])
    require(issued <= now < expires and 0 < (expires-issued).total_seconds() <= 120, 'Expired or expanded admission')
    require(0 <= (now-timestamp(proof['recorded_at'])).total_seconds() <= 60, 'Stale or future native proof')


def predecessor_review(root):
    terminal_path = child(root, 'inputs/prior-round1/terminal.json')
    review_path = child(root, 'inputs/prior-round1/review.json')
    registration_path = child(root, 'inputs/prior-round1/registration.json')
    terminal, review, registration = (load(path) for path in (terminal_path, review_path, registration_path))
    require(all(row.get('case') == 'e03-round1' and row.get('candidate') == HEAD
                for row in (terminal, review, registration)), 'Predecessor case/candidate mismatch')
    require(terminal.get('scope') == 'e03-round1-acceptance'
            and terminal.get('overall') == 'PENDING_FACT_REVIEW'
            and terminal.get('mechanical') == 'PASS'
            and terminal.get('facts') == 'PENDING_ROOT_INDEPENDENT_REVIEW'
            and terminal.get('acceptance_credit') is False and terminal.get('errors') == []
            and type(terminal.get('work_cli_count')) is int and terminal['work_cli_count'] == 1
            and all(terminal.get(key, {}).get('status') == 'PASS' for key in ('cleanup', 'audit', 'boundaries')),
            'Predecessor raw terminal not eligible')
    require(review.get('reviewer') == 'root-independent' and review.get('scope') == 'e03-round1-result-review'
            and all(review.get(key) == 'PASS' for key in ('evidence_verdict', 'case_verdict', 'mechanical_verdict',
                    'facts_verdict', 'target_verdict', 'file_verdict', 'final_claim_verdict', 'cleanup_verdict'))
            and review.get('candidate_runtime_manifest_sha256') == CANDIDATE_MANIFEST
            and review.get('preparation_manifest_sha256') == terminal.get('package_manifest_sha256')
            and review.get('product_result_sha256') == terminal.get('product_result_sha256'),
            'Predecessor independent result not eligible')
    execution = review.get('execution', {})
    require(execution.get('model') == MODEL and execution.get('model_digest') == DIGEST
            and type(execution.get('work_cli_launches')) is int and execution['work_cli_launches'] == 1
            and execution.get('automatic_retry_recorded') is False, 'Predecessor execution mismatch')
    terminal_hash, review_hash = sha(terminal_path), sha(review_path)
    require(review.get('terminal_sha256') == terminal_hash
            and registration.get('terminal_sha256') == terminal_hash
            and registration.get('result_review_sha256') == review_hash, 'Predecessor receipt hash mismatch')
    require(all(registration.get(key) == 'PASS' for key in ('case_verdict', 'facts', 'delivery', 'final_claim'))
            and registration.get('acceptance_credit') is True and registration.get('negative_passed') is False
            and all(type(registration.get(key)) is int and registration[key] == value for key, value in
                    (('E03_credit', 1), ('same_candidate_terminals', 1), ('cumulative_work_cli_count', 1),
                     ('current_case_work_cli_count', 1), ('positive_passed', 1), ('positive_required', 3))),
            'Predecessor registration not eligible')
    return dict(case='e03-round1', candidate=HEAD, terminal_sha256=terminal_hash,
                review_sha256=review_hash, registration_sha256=sha(registration_path))


def first_two_predecessor_reviews(root):
    first = predecessor_review(root)
    folder = 'inputs/prior-round2/'
    terminal_path, review_path, registration_path = (child(root, folder+name)
        for name in ('terminal.json', 'review.json', 'registration.json'))
    terminal, review, registration = (load(path) for path in (terminal_path, review_path, registration_path))
    require(all(row.get('case') == 'e03-round2' and row.get('candidate') == HEAD
                for row in (terminal, review, registration)), 'Predecessor round2 case/candidate mismatch')
    require(terminal.get('scope') == 'e03-round2-acceptance'
            and terminal.get('overall') == 'PENDING_FACT_REVIEW'
            and terminal.get('mechanical') == 'PASS'
            and terminal.get('facts') == 'PENDING_ROOT_INDEPENDENT_REVIEW'
            and terminal.get('acceptance_credit') is False and terminal.get('errors') == []
            and type(terminal.get('work_cli_count')) is int and terminal['work_cli_count'] == 1
            and terminal.get('retry_authorized') is False
            and type(terminal.get('audio_actions')) is int and terminal['audio_actions'] == 0
            and all(terminal.get(key, {}).get('status') == 'PASS' for key in ('cleanup', 'audit', 'boundaries')),
            'Predecessor round2 raw terminal not eligible')
    require(review.get('reviewer') == 'root-independent' and review.get('scope') == 'e03-round2-result-review'
            and all(review.get(key) == 'PASS' for key in ('evidence_verdict', 'case_verdict', 'mechanical_verdict',
                    'facts_verdict', 'target_verdict', 'file_verdict', 'final_claim_verdict', 'cleanup_verdict'))
            and review.get('candidate_runtime_manifest_sha256') == CANDIDATE_MANIFEST
            and review.get('preparation_manifest_sha256') == terminal.get('package_manifest_sha256')
            and review.get('product_result_sha256') == terminal.get('product_result_sha256'),
            'Predecessor round2 independent result not eligible')
    execution = review.get('execution', {})
    admission, limits = review.get('authority_and_admission', {}), review.get('limits', {})
    require(execution.get('model') == MODEL and execution.get('model_digest') == DIGEST
            and type(execution.get('work_cli_count')) is int and execution['work_cli_count'] == 1
            and admission.get('retry_authorized') is False
            and type(limits.get('actual_reruns_or_retries')) is int and limits['actual_reruns_or_retries'] == 0,
            'Predecessor round2 execution mismatch')
    terminal_hash, review_hash = sha(terminal_path), sha(review_path)
    require(review.get('terminal_sha256') == terminal_hash
            and registration.get('terminal_sha256') == terminal_hash
            and registration.get('result_review_sha256') == review_hash,
            'Predecessor round2 receipt hash mismatch')
    require(all(registration.get(key) == 'PASS' for key in ('case_verdict', 'facts', 'delivery', 'final_claim'))
            and registration.get('acceptance_credit') is True and registration.get('negative_passed') is False
            and all(type(registration.get(key)) is int and registration[key] == value for key, value in
                    (('E03_credit', 1), ('same_candidate_terminals', 2), ('cumulative_work_cli_count', 2),
                     ('current_case_work_cli_count', 1), ('positive_passed', 2), ('positive_required', 3))),
            'Predecessor round2 registration not eligible')
    prior = admission.get('prior_round1', {})
    require(prior.get('candidate_matches') is True and prior.get('binding_verified') is True
            and type(prior.get('eligible_prior_positive_count')) is int and prior['eligible_prior_positive_count'] == 1
            and type(prior.get('required_positive_count')) is int and prior['required_positive_count'] == 3
            and all(prior.get(key) == first[key] for key in ('terminal_sha256','review_sha256','registration_sha256'))
            and registration.get('predecessor_registration_sha256') == first['registration_sha256'],
            'Predecessor round2 prior credential mismatch')
    second = dict(case='e03-round2', candidate=HEAD, terminal_sha256=terminal_hash,
                  review_sha256=review_hash, registration_sha256=sha(registration_path))
    rows = registration.get('same_candidate_terminal_bindings')
    require(isinstance(rows, list) and len(rows) == 2
            and registration.get('consecutive_positive_cases') == ['e03-round1','e03-round2'],
            'Predecessor consecutive chain missing')
    first_terminal = load(child(root, 'inputs/prior-round1/terminal.json'))
    first_review = load(child(root, 'inputs/prior-round1/review.json'))
    task_ids = [first_review.get('execution', {}).get('task_id'), execution.get('task_id')]
    require(all(isinstance(task, str) and task for task in task_ids) and len(set(task_ids)) == 2,
            'Predecessor distinct tasks required')
    finished = [first_terminal.get('finished_at'), terminal.get('finished_at')]
    require(timestamp(finished[0]) < timestamp(finished[1]), 'Predecessor chronology invalid')
    for index, binding in enumerate((first, second)):
        row = rows[index]
        require(isinstance(row, dict) and row.get('case') == binding['case'] and row.get('candidate') == HEAD
                and row.get('sha256') == binding['terminal_sha256'] and row.get('review_sha256') == binding['review_sha256']
                and row.get('raw_overall') == 'PENDING_FACT_REVIEW' and row.get('case_verdict') == 'PASS'
                and type(row.get('work_cli_count')) is int and row['work_cli_count'] == 1
                and row.get('task_id') == task_ids[index] and row.get('finished_at') == finished[index],
                'Predecessor cumulative binding mismatch')
    return [first, second]



def reconciled_runtime(root):
    old_path = child(root, 'inputs/protected-baseline-before-recovery.json')
    baseline_path = child(root, 'inputs/protected-baseline.json')
    recovery_path = child(root, 'inputs/runtime-reconciliation.json')
    old, baseline, recovery = (load(p) for p in (old_path, baseline_path, recovery_path))
    manual = load(child(root, 'inputs/runtime-manual-confirmation.json'))
    approval = load(child(root, 'inputs/runtime-user-approval.json'))
    require(recovery.get('status') == 'PASS_RUNTIME_RECONCILIATION'
            and recovery.get('native_version') == '0.32.15'
            and recovery.get('current_model') == {'name':MODEL+':latest','digest':DIGEST}
            and recovery.get('model_manifest_sha256') == DIGEST
            and recovery.get('old_environment_failure_preserved') is True
            and recovery.get('proof_is_point_in_time_only') is True
            and recovery.get('next_case_authority_issued') is False
            and all(type(recovery.get(k)) is int and recovery[k] == 0 for k in
                    ('assistant_service_start_count','automatic_retries','model_inferences','actual_cases','audio_actions')),
            'Runtime reconciliation is not eligible')
    require(manual.get('performed_by') == 'user'
            and isinstance(manual.get('source'), str) and manual['source']
            and approval.get('assistant_service_start_count') == 0
            and approval.get('automatic_retries') == 0,
            'Runtime operator confirmation missing')
    require(baseline.get('predecessor_baseline_sha256') == sha(old_path)
            and baseline.get('runtime_reconciliation_sha256') == sha(recovery_path),
            'Restored baseline evidence binding mismatch')
    before = old.get('protected5', []) + old.get('protected_listener_pair', [])
    after = baseline.get('protected5', []) + baseline.get('protected_listener_pair', [])
    require(len(before) == len(after) == 7 and before[0].get('role') == after[0].get('role') == 'ollama',
            'Runtime protected inventory mismatch')
    fields = PROTECTED_FIELDS
    require(all(type(row.get('pid')) is int and type(row.get('created_filetime')) is int
                and row['pid'] > 0 and row['created_filetime'] > 0 for row in after)
            and len({row['pid'] for row in after}) == 7, 'Runtime protected identities invalid')
    require(before[0]['pid'] != after[0]['pid']
            and baseline.get('replaced_identity', {}).get('old_pid') == before[0]['pid']
            and baseline.get('replaced_identity', {}).get('new_pid') == after[0]['pid']
            and all(recovery.get('new_ollama_identity', {}).get(k) == after[0].get(k) for k in fields),
            'Restored Ollama identity mismatch')
    observed = recovery.get('other_six')
    require(isinstance(observed,list) and len(observed) == 6, 'Runtime other-six observations missing')
    for index, (old_row, new_row) in enumerate(zip(before[1:],after[1:])):
        row = observed[index]
        require(row.get('match') is True and row.get('active') is True
                and all(old_row.get(k) == new_row.get(k) == row.get(k) for k in fields),
                'Non-Ollama protected identity changed')
    listeners = recovery.get('listener_observation', {}).get('listeners')
    require(isinstance(listeners,list) and listeners
            and all(x.get('OwningProcess') == after[0]['pid'] and x.get('LocalPort') == 11434
                    and x.get('LocalAddress') in ('127.0.0.1','::1') for x in listeners)
            and baseline.get('ollama_listener') == listeners
            and baseline.get('ollama_listener_owner_match') is True, 'Restored native listener mismatch')
    voice = recovery.get('voice', {})
    require(voice == baseline.get('voice_listener_status') and voice.get('state') == 'ready'
            and all(voice.get(k) is True for k in ('ready','fresh','worker_ready','instance_lock_held'))
            and all(voice.get(k) == old.get('voice_listener_status', {}).get(k) for k in ('pid','worker_pid','run_id')),
            'Protected voice status mismatch')
    require(timestamp(recovery['recorded_at']) <= timestamp(baseline['captured_at_utc']),
            'Runtime recovery chronology invalid')
    return recovery


def three_positive_predecessor_reviews(root):
    previous = first_two_predecessor_reviews(root)
    paths = [child(root, 'inputs/prior-round3/'+name+'.json') for name in ('terminal','review','registration')]
    terminal, review, registration = (load(p) for p in paths)
    require(all(row.get('case') == 'e03-round3' and row.get('candidate') == HEAD
                for row in (terminal,review,registration)), 'Predecessor round3 case/candidate mismatch')
    require(terminal.get('scope') == 'e03-round3-acceptance'
            and terminal.get('overall') == 'PENDING_FACT_REVIEW'
            and terminal.get('mechanical') == 'PASS'
            and terminal.get('facts') == 'PENDING_ROOT_INDEPENDENT_REVIEW'
            and terminal.get('acceptance_credit') is False and terminal.get('errors') == []
            and type(terminal.get('work_cli_count')) is int and terminal['work_cli_count'] == 1
            and terminal.get('retry_authorized') is False
            and type(terminal.get('audio_actions')) is int and terminal['audio_actions'] == 0
            and all(terminal.get(k, {}).get('status') == 'PASS' for k in ('cleanup','audit','boundaries')),
            'Predecessor round3 raw terminal not eligible')
    require(review.get('reviewer') == 'root-independent' and review.get('scope') == 'e03-round3-result-review'
            and all(review.get(k) == 'PASS' for k in ('evidence_verdict','case_verdict','mechanical_verdict',
                    'facts_verdict','target_verdict','file_verdict','final_claim_verdict','cleanup_verdict'))
            and review.get('candidate_runtime_manifest_sha256') == CANDIDATE_MANIFEST
            and review.get('preparation_manifest_sha256') == terminal.get('package_manifest_sha256')
            and review.get('product_result_sha256') == terminal.get('product_result_sha256')
            and review.get('credit', {}).get('third_positive_credit_recommended') is True,
            'Predecessor round3 independent result not eligible')
    execution = review.get('execution', {})
    require(execution.get('model') == MODEL and execution.get('model_digest') == DIGEST
            and type(execution.get('work_cli_count')) is int and execution['work_cli_count'] == 1
            and review.get('authority_and_admission', {}).get('retry_authorized') is False
            and type(review.get('limits', {}).get('actual_reruns_or_retries')) is int
            and review['limits']['actual_reruns_or_retries'] == 0, 'Predecessor round3 execution mismatch')
    th, rh = sha(paths[0]), sha(paths[1])
    require(review.get('terminal_sha256') == th and registration.get('terminal_sha256') == th
            and registration.get('result_review_sha256') == rh
            and registration.get('predecessor_registration_sha256') == previous[-1]['registration_sha256'],
            'Predecessor round3 receipt hash mismatch')
    require(all(registration.get(k) == 'PASS' for k in ('case_verdict','facts','delivery','final_claim'))
            and registration.get('acceptance_credit') is True and registration.get('negative_passed') is False
            and all(type(registration.get(k)) is int and registration[k] == value for k,value in
                    (('E03_credit',1),('same_candidate_terminals',3),('cumulative_work_cli_count',3),
                     ('current_case_work_cli_count',1),('positive_passed',3),('positive_required',3))),
            'Predecessor round3 registration not eligible')
    third = dict(case='e03-round3',candidate=HEAD,terminal_sha256=th,review_sha256=rh,registration_sha256=sha(paths[2]))
    bindings = previous + [third]
    terminals = [load(child(root,'inputs/prior-round'+str(n)+'/terminal.json')) for n in (1,2,3)]
    reviews = [load(child(root,'inputs/prior-round'+str(n)+'/review.json')) for n in (1,2,3)]
    tasks = [x.get('execution', {}).get('task_id') for x in reviews]
    require(all(isinstance(x,str) and x for x in tasks) and len(set(tasks)) == 3,
            'Predecessor distinct tasks required')
    times = [timestamp(x.get('finished_at')) for x in terminals]
    require(times[0] < times[1] < times[2], 'Predecessor chronology invalid')
    rows = registration.get('same_candidate_terminal_bindings')
    require(isinstance(rows,list) and len(rows) == 3
            and registration.get('consecutive_positive_cases') == [x['case'] for x in bindings],
            'Predecessor consecutive three-round chain missing')
    for index, (row, binding) in enumerate(zip(rows,bindings)):
        require(isinstance(row,dict) and row.get('case') == binding['case'] and row.get('candidate') == HEAD
                and row.get('sha256') == binding['terminal_sha256'] and row.get('review_sha256') == binding['review_sha256']
                and row.get('raw_overall') == 'PENDING_FACT_REVIEW' and row.get('case_verdict') == 'PASS'
                and type(row.get('work_cli_count')) is int and row['work_cli_count'] == 1
                and row.get('task_id') == tasks[index] and row.get('finished_at') == terminals[index]['finished_at'],
                'Predecessor round3 cumulative binding mismatch')
    require(review.get('environment_verdict') in ('PASS','FAIL_POST_CASE_RUNTIME_ADMISSION_BLOCKED'),
            'Predecessor environment disposition unknown')
    recovery = reconciled_runtime(root)
    require(times[2] < timestamp(recovery['recorded_at']), 'Recovery must follow the round3 result')
    return bindings


def e03_predecessor_reviews(root):
    bindings = three_positive_predecessor_reviews(root)
    folder = 'inputs/prior-negative/'
    paths = {name: child(root, folder+name+'.json') for name in
             ('terminal', 'review', 'registration', 'result-manifest', 'negative-evidence')}
    terminal, review, registration, manifest = (load(paths[name]) for name in
        ('terminal', 'review', 'registration', 'result-manifest'))
    require(all(row.get('case') == 'e03-negative' and row.get('candidate') == HEAD
                for row in (terminal, review, registration, manifest)), 'Negative predecessor case/candidate mismatch')
    require(terminal.get('scope') == 'e03-negative-acceptance'
            and terminal.get('overall') == 'PENDING_FACT_REVIEW' and terminal.get('mechanical') == 'PASS'
            and terminal.get('facts') == 'PENDING_ROOT_INDEPENDENT_REVIEW'
            and terminal.get('acceptance_credit') is False and terminal.get('errors') == []
            and terminal.get('retry_authorized') is False
            and all(type(terminal.get(k)) is int and terminal[k] == 0
                    for k in ('work_cli_count', 'model_requests', 'audio_actions'))
            and all(terminal.get(k, {}).get('status') == 'PASS' for k in ('cleanup', 'audit', 'boundaries')),
            'Negative predecessor raw terminal not eligible')
    require(review.get('reviewer') == 'root-independent' and review.get('scope') == 'e03-negative-result-review'
            and all(review.get(k) == 'PASS' for k in ('verdict', 'case_verdict', 'mechanical_verdict',
                    'behavior_verdict', 'target_verdict', 'file_verdict', 'cleanup_verdict', 'environment_verdict'))
            and review.get('candidate_runtime_manifest_sha256') == CANDIDATE_MANIFEST
            and review.get('preparation_manifest_sha256') == terminal.get('package_manifest_sha256')
            and review.get('acceptance_credit_recommended') is True and review.get('findings') == [],
            'Negative predecessor independent result not eligible')
    facts = review.get('facts_scope', {})
    require(facts.get('status') == 'NOT_APPLICABLE' and facts.get('generated_content_present') is False
            and facts.get('generated_content_facts_verdict') is None,
            'Negative predecessor cannot claim generated facts PASS')
    counts = review.get('execution_counts', {})
    require(type(counts.get('actual_negative_cases')) is int and counts['actual_negative_cases'] == 1
            and all(type(counts.get(k)) is int and counts[k] == 0 for k in
                    ('work_cli_count', 'agent_server_launches', 'model_requests', 'audio_actions',
                     'mutation_sends', 'native_write_attempts', 'product_output_files', 'reruns_or_retries_recorded')),
            'Negative predecessor execution mismatch')
    terminal_hash, review_hash, manifest_hash = (sha(paths[name]) for name in ('terminal', 'review', 'result-manifest'))
    evidence_hash = sha(paths['negative-evidence'])
    require(review.get('terminal_sha256') == registration.get('terminal_sha256') == manifest.get('terminal_sha256') == terminal_hash
            and registration.get('result_review_sha256') == review_hash
            and review.get('result_manifest_sha256') == registration.get('result_manifest_sha256') == manifest_hash
            and terminal.get('negative_result_sha256') == review.get('negative_result_sha256') == evidence_hash
            and manifest.get('scope') == 'e03-negative-actual-result'
            and manifest.get('preparation_manifest_sha256') == terminal.get('package_manifest_sha256'),
            'Negative predecessor receipt hash mismatch')
    rows = manifest.get('files', [])
    for name, original in [('terminal', 'terminal.json'), ('negative-evidence', 'negative-evidence.json')]:
        matches = [row for row in rows if row.get('path') == 'actual/e03-negative/'+original]
        require(len(matches) == 1 and matches[0].get('sha256') == sha(paths[name])
                and matches[0].get('bytes') == paths[name].stat().st_size, 'Negative predecessor result binding missing')
    require(registration.get('E03') == 'PASS_CURRENT_CANDIDATE_FIXED_CORPUS'
            and all(registration.get(k) == 'PASS' for k in ('case_verdict', 'behavior', 'target', 'file', 'cleanup'))
            and registration.get('facts') == 'NOT_APPLICABLE_NO_GENERATED_CONTENT'
            and registration.get('acceptance_credit') is True and registration.get('negative_passed') is True
            and registration.get('predecessor_registration_sha256') == bindings[-1]['registration_sha256']
            and all(type(registration.get(k)) is int and registration[k] == value for k, value in
                    (('negative_case_credit', 1), ('positive_passed', 3), ('positive_required', 3),
                     ('negative_cases_passed', 1), ('negative_cases_required', 1), ('same_candidate_terminals', 4),
                     ('current_case_work_cli_count', 0), ('cumulative_work_cli_count', 3))),
            'Negative predecessor registration not eligible')
    positive_rows = registration.get('positive_terminal_bindings')
    require(isinstance(positive_rows, list) and len(positive_rows) == 3, 'Negative predecessor positive chain missing')
    for index, (row, binding) in enumerate(zip(positive_rows, bindings), 1):
        prior_terminal = load(child(root, 'inputs/prior-round'+str(index)+'/terminal.json'))
        prior_review = load(child(root, 'inputs/prior-round'+str(index)+'/review.json'))
        require(all(row.get(k) == binding[k] for k in binding)
                and row.get('task_id') == prior_review['execution']['task_id']
                and row.get('finished_at') == prior_terminal['finished_at'] and row.get('case_verdict') == 'PASS'
                and type(row.get('work_cli_count')) is int and row['work_cli_count'] == 1,
                'Negative predecessor positive binding mismatch')
    negative_binding = registration.get('negative_terminal_binding', {})
    require(negative_binding.get('case') == 'e03-negative' and negative_binding.get('terminal_sha256') == terminal_hash
            and negative_binding.get('review_sha256') == review_hash
            and negative_binding.get('finished_at') == terminal.get('finished_at')
            and timestamp(positive_rows[-1]['finished_at']) < timestamp(terminal['finished_at']),
            'Negative predecessor chronology or terminal binding mismatch')
    return bindings + [dict(case='e03-negative', candidate=HEAD, terminal_sha256=terminal_hash,
                           review_sha256=review_hash, registration_sha256=sha(paths['registration']))]


def predecessor_reviews(root):
    bindings = e03_predecessor_reviews(root)
    paths = [child(root, 'inputs/prior-e01-round1/'+name+'.json')
             for name in ('terminal', 'review', 'registration')]
    terminal, review, registration = (load(path) for path in paths)
    require(all(row.get('case') == 'e01-round1' and row.get('candidate') == HEAD
                for row in (terminal, review, registration)), 'E01 predecessor case/candidate mismatch')
    require(terminal.get('scope') == 'e01-round1-acceptance'
            and terminal.get('overall') == 'PENDING_FACT_REVIEW' and terminal.get('mechanical') == 'PASS'
            and terminal.get('facts') == 'PENDING_ROOT_INDEPENDENT_REVIEW'
            and terminal.get('acceptance_credit') is False and terminal.get('errors') == []
            and terminal.get('retry_authorized') is False
            and type(terminal.get('work_cli_count')) is int and terminal['work_cli_count'] == 1
            and type(terminal.get('audio_actions')) is int and terminal['audio_actions'] == 0
            and all(terminal.get(k, {}).get('status') == 'PASS' for k in ('cleanup', 'audit', 'boundaries')),
            'E01 predecessor raw terminal not eligible')
    require(review.get('reviewer') == 'root-independent' and review.get('scope') == 'e01-round1-result-review'
            and all(review.get(k) == 'PASS' for k in ('verdict', 'evidence_verdict', 'case_verdict',
                'mechanical_verdict', 'facts_verdict', 'file_verdict', 'final_claim_verdict',
                'cleanup_verdict', 'environment_verdict'))
            and review.get('target_verdict') == review.get('ui_target_scope') == 'NOT_APPLICABLE'
            and review.get('independent_from_preparation_reviewer') is True
            and review.get('no_new_facts', {}).get('verdict') == 'PASS' and review.get('findings') == [],
            'E01 predecessor independent result not eligible')
    execution, recommendation = review.get('execution', {}), review.get('recommendation', {})
    require(execution.get('model') == MODEL and execution.get('model_digest') == DIGEST
            and execution.get('native_version') == '0.32.15'
            and execution.get('request_id') == execution.get('session_id') == 'e01-round1'
            and execution.get('automatic_retry_recorded') is False and execution.get('fixture_started') is False
            and all(type(execution.get(k)) is int and execution[k] == value for k, value in
                (('work_cli_launches', 1), ('actual_case_count', 1), ('reviewer_reruns', 0),
                 ('completed_sdk_write_calls', 1), ('audio_actions_recorded', 0), ('ui_actions_recorded', 0))),
            'E01 predecessor execution mismatch')
    events = execution.get('completed_inference_end_events')
    require(type(events) is int and 1 <= events <= 10
            and recommendation.get('acceptance_credit_recommended') is True
            and recommendation.get('case_candidate') == HEAD
            and all(type(recommendation.get(k)) is int and recommendation[k] == value for k, value in
                (('current_case_positive_credit', 1), ('positive_passed_by_this_case', 1), ('positive_required', 3))),
            'E01 predecessor credit recommendation mismatch')
    th, rh = sha(paths[0]), sha(paths[1])
    require(review.get('terminal_sha256') == registration.get('terminal_sha256') == th
            and registration.get('result_review_sha256') == rh
            and review.get('candidate_runtime_manifest_sha256') == registration.get('candidate_manifest_sha256') == CANDIDATE_MANIFEST
            and review.get('preparation_manifest_sha256') == registration.get('preparation_manifest_sha256') == terminal.get('package_manifest_sha256')
            and review.get('product_result_sha256') == registration.get('product_result_sha256') == terminal.get('product_result_sha256')
            and review.get('result_evidence_manifest_sha256') == registration.get('result_manifest_sha256')
            and isinstance(review.get('artifact_sha256'), str) and len(review['artifact_sha256']) == 64
            and review['artifact_sha256'] == registration.get('artifact_sha256'),
            'E01 predecessor receipt hash mismatch')
    require(registration.get('scope') == 'E01_CURRENT_CANDIDATE_POSITIVE_CHAIN'
            and all(registration.get(k) == 'PASS' for k in ('case_verdict', 'facts', 'delivery', 'final_claim', 'cleanup'))
            and registration.get('target') == 'NOT_APPLICABLE_NO_UI'
            and registration.get('acceptance_credit') is True and registration.get('E01') == 'PARTIAL_1_OF_3'
            and registration.get('E03') == 'PASS_CURRENT_CANDIDATE_FIXED_CORPUS'
            and registration.get('E03_prerequisite_registration_sha256') == bindings[-1]['registration_sha256']
            and all(type(registration.get(k)) is int and registration[k] == value for k, value in
                (('E01_credit', 1), ('positive_passed', 1), ('positive_required', 3), ('same_candidate_e01_terminals', 1),
                 ('cumulative_work_cli_count', 1), ('current_case_work_cli_count', 1),
                 ('cumulative_completed_inference_events', events), ('current_case_completed_inference_events', events))),
            'E01 predecessor registration not eligible')
    task = execution.get('task_id')
    require(isinstance(task, str) and str(uuid.UUID(task)) == task and registration.get('task_id') == task,
            'E01 predecessor task identity invalid')
    old_tasks = [load(child(root, 'inputs/prior-round'+str(n)+'/review.json'))['execution']['task_id']
                 for n in (1, 2, 3)]
    negative = load(child(root, 'inputs/prior-negative/terminal.json'))
    require(task not in old_tasks and timestamp(negative['finished_at']) < timestamp(terminal['finished_at']),
            'E01 predecessor distinct task or chronology invalid')
    rows = registration.get('same_candidate_e01_terminal_bindings')
    require(isinstance(rows, list) and len(rows) == 1 and rows[0] == dict(
        case='e01-round1', candidate=HEAD, terminal_sha256=th, review_sha256=rh, task_id=task,
        finished_at=terminal['finished_at'], case_verdict='PASS', work_cli_count=1,
        completed_inference_events=events, artifact_sha256=review['artifact_sha256']),
        'E01 predecessor cumulative binding mismatch')
    return bindings + [dict(case='e01-round1', candidate=HEAD, terminal_sha256=th,
                           review_sha256=rh, registration_sha256=sha(paths[2]))]


def verify_package(root):
    root = safe_path(root)
    manifest = load(child(root, 'manifest.json'))
    require(manifest.get('schema') == 1 and manifest.get('scope') == SCOPE
            and manifest.get('case') == CASE and manifest.get('package_root') == str(root), 'Package scope/root mismatch')
    require(manifest.get('candidate') == HEAD and manifest.get('candidate_manifest_sha256') == CANDIDATE_MANIFEST
            and manifest.get('model') == MODEL and manifest.get('digest') == DIGEST, 'Package candidate/model mismatch')
    require(manifest.get('python_executable') == str(PYTHON) and type(manifest.get('case_cap')) is int
            and manifest['case_cap'] == 1 and manifest.get('retry_authorized') is False, 'Package interpreter/cap mismatch')
    require(type(manifest.get('product_cli_cap')) is int and manifest['product_cli_cap'] == 1
            and type(manifest.get('audio_actions')) is int and manifest['audio_actions'] == 0
            and manifest.get('fixture_required') is False, 'E01 requires one CLI and no fixture/audio')
    require(type(manifest.get('proof_max_age_seconds')) is int and manifest['proof_max_age_seconds'] == 60
            and type(manifest.get('admission_max_seconds')) is int and manifest['admission_max_seconds'] == 120
            and manifest.get('product_timeouts') == {'CLI':300, 'SDK':1800, 'controller_wait':315},
            'E01 original admission and product deadlines required')
    paths = set()
    for row in manifest['files']:
        require(set(row) == {'path', 'bytes', 'sha256'} and row['path'] not in paths, 'Package entry invalid')
        path = child(root, row['path'])
        require(path.is_file() and path.stat().st_size == row['bytes'] and sha(path) == row['sha256'],
                'Sealed dependency drift: ' + row['path'])
        paths.add(row['path'])
    require(RUNTIME_FILES <= paths, 'Runtime dependency omitted')
    found = {f.relative_to(root).as_posix() for directory in ('code', 'preparation-support')
             for f in (root/directory).glob('*.py')}
    require(found == {p for p in paths if p.endswith('.py') and p.split('/')[0] in ('code', 'preparation-support')},
            'Unsealed Python module')
    predecessor_reviews(root)
    return sha(root/'manifest.json')


def reviewed_package(root):
    digest = verify_package(root)
    path = child(root, 'release/independent-review.json')
    review = load(path)
    require(review.get('reviewer') == 'root-independent' and review.get('verdict') == 'PASS'
            and review.get('scope') == SCOPE + '-package'
            and review.get('manifest_sha256') == digest and review.get('candidate') == HEAD,
            'Matching independent package review required')
    return digest, sha(path)


def assert_proof(root, proof):
    require(isinstance(proof, dict) and proof.get('schema') == 1 and proof.get('scope') == SCOPE, 'Native proof scope mismatch')
    source, model = proof.get('source', {}), proof.get('model', {})
    require(source.get('candidate') == HEAD and source.get('candidate_manifest_sha256') == CANDIDATE_MANIFEST
            and source.get('model_digest') == DIGEST and source.get('code_gate') == 'PASS', 'Native proof source mismatch')
    require(model.get('model') == MODEL and model.get('digest') == DIGEST
            and model.get('manifest_sha256') == DIGEST and model.get('version') == {'version':'0.32.15'}
            and isinstance(model.get('tags_sha256'), str) and len(model['tags_sha256']) == 64, 'Native proof model mismatch')
    baseline = load(child(root, 'inputs/protected-baseline.json'))
    expected = baseline['protected5'] + baseline['protected_listener_pair']
    actual = proof.get('protected_processes')
    require(len(expected) == 7 and isinstance(actual, list) and len(actual) == 7, 'Protected proof inventory mismatch')
    for recorded, sealed in zip(actual, expected):
        require(set(recorded) == set(PROTECTED_FIELDS), 'Protected proof fields mismatch')
        require(all(recorded[key] == sealed[key] for key in PROTECTED_FIELDS if key != 'exe')
                and recorded['exe'].lower() == sealed['exe'].lower(), 'Protected proof identity mismatch')
    require(proof.get('listener_pid') == expected[0]['pid'], 'Native proof listener mismatch')


def validate_release(root, now, *, active=False):
    root = safe_path(root)
    manifest_hash, review_hash = reviewed_package(root)
    authority = load(child(root, 'release/authority.json'))
    require(set(authority) == AUTH_FIELDS and authority['schema'] == 1 and authority['issuer'] == 'root', 'Authority fields invalid')
    require(authority['scope'] == SCOPE and authority['case'] == CASE, 'Only E01 round1 scope allowed')
    require(authority['candidate'] == HEAD and authority['candidate_manifest_sha256'] == CANDIDATE_MANIFEST
            and authority['model'] == MODEL and authority['digest'] == DIGEST, 'Authority candidate/model mismatch')
    require(authority['manifest_sha256'] == manifest_hash and authority['review_sha256'] == review_hash, 'Authority package/review mismatch')
    require(all(type(authority[key]) is int and authority[key] == value
                for key, value in (('case_cap',1),('product_cli_cap',1),('audio_actions',0)))
            and authority['retry_authorized'] is False and authority['acceptance_credit'] is False
            and authority['prior_reviews'] == predecessor_reviews(root), 'Single E01 allocation with completed E03 required')
    require(isinstance(authority['user_authorization'], str) and authority['user_authorization'].strip(), 'User authorization missing')
    proof_path = child(root, authority['proof_path'])
    require(proof_path.parent == root/'release/preflight' and proof_path.suffix == '.json', 'Canonical proof path required')
    require(sha(proof_path) == authority['proof_sha256'], 'Native proof hash mismatch')
    proof = load(proof_path)
    check_admission_time(authority, proof, now)
    assert_proof(root, proof)
    folder = child(root, 'actual/' + CASE)
    if not active and folder.exists():
        raise FileExistsError('Single E01 allocation already consumed')
    require(not active or folder.is_dir(), 'Active allocation missing')
    names = {p.name for p in folder.parent.iterdir()} if folder.parent.exists() else set()
    require(names == ({CASE} if active else set()), 'Unexpected actual-case state')
    return {'authority':authority, 'proof':proof, 'manifest_sha256':manifest_hash}


def make_backend(root, factory):
    if factory is None:
        require(sys.dont_write_bytecode and not sys.flags.optimize, 'Use unoptimized Python -B')
        require(os.path.normcase(os.path.abspath(sys.executable)) == os.path.normcase(str(PYTHON)), 'Use pinned original interpreter')
        from acceptance_backend import AcceptanceBackend
        factory = AcceptanceBackend
    return factory(root)


def assert_same_live(proof, live):
    require(all(live.get(key) == proof.get(key) for key in ('source','model','protected_processes','listener_pid')), 'Live proof drift')


def write_preflight(root, *, backend_factory=None):
    root = safe_path(root)
    reviewed_package(root)
    require(not (root/'actual').exists(), 'Actual allocation already exists')
    backend = make_backend(root, backend_factory)
    proof = backend.inspect()
    assert_proof(root, proof)
    directory = child(root, 'release/preflight'); directory.mkdir(exist_ok=True)
    path = child(root, 'release/preflight/' + uuid.uuid4().hex + '.json')
    save_new(path, proof)
    return {'proof_path':path.relative_to(root).as_posix(), 'proof_sha256':sha(path), 'actual_allocation_created':False}


def run_once(root, *, backend_factory=None):
    root = safe_path(root)
    admission = validate_release(root, utcnow())
    backend = make_backend(root, backend_factory)
    assert_same_live(admission['proof'], backend.inspect())
    require(validate_release(root, utcnow()) == admission, 'Release changed during inspection')
    folder = child(root, 'actual/' + CASE)
    folder.parent.mkdir(exist_ok=True); folder.mkdir(exist_ok=False)
    save_new(folder/'admission.json', dict(admission, consumed=True, started_at=utcnow().isoformat(), retry_authorized=False))
    errors, review = [], None
    effects = cleanup = audit = boundaries = None

    def revalidate():
        current = validate_release(root, utcnow(), active=True)
        require(current == admission, 'Active release changed')
        assert_same_live(admission['proof'], backend.inspect())
        require(validate_release(root, utcnow(), active=True) == admission, 'Active release changed during inspection')

    def admit_cli():
        require(validate_release(root, utcnow(), active=True) == admission, 'Active release changed before CLI submission')
        # File reads may themselves take time. Sample again after all binding
        # checks, without refreshing the original proof or running native I/O.
        check_admission_time(admission['authority'], admission['proof'], utcnow())

    try:
        backend.start(folder)
        review = backend.product(revalidate, admit_cli)
        require(review.get('mechanical') == 'PASS' and review.get('facts') == 'PENDING_ROOT_INDEPENDENT_REVIEW', 'Mechanical review incomplete')
    except Exception as exc:
        errors.append({'stage':'execute', 'type':type(exc).__name__, 'error':str(exc)})
    finally:
        for stage, callback in (('effects',backend.effects),('cleanup',backend.close),('audit',backend.audit)):
            try:
                value = callback()
                if stage == 'effects': effects = value
                elif stage == 'cleanup': cleanup = value
                else: audit = value
                if stage != 'effects': require(value.get('status') == 'PASS', stage + ' incomplete')
            except Exception as exc:
                errors.append({'stage':stage, 'type':type(exc).__name__, 'error':str(exc)})
        try:
            assert_same_live(admission['proof'], backend.inspect())
            require(verify_package(root) == admission['manifest_sha256'], 'Sealed package changed during case')
            boundaries = {'status':'PASS'}
        except Exception as exc:
            errors.append({'stage':'boundaries','type':type(exc).__name__,'error':str(exc)})
    count = backend.cli_count
    if type(count) is not int or not 0 <= count <= 1 or (review is not None and count != 1):
        errors.append({'stage':'scope','error':'E01 requires one CLI, with no retry or extra submission'})
    hashes = {}
    for name in ('product-result.json','pre-cleanup-effects.json'):
        try:
            path = child(root, 'actual/' + CASE + '/' + name)
            hashes[name] = sha(path) if path.is_file() else None
        except Exception as exc:
            hashes[name] = None
            errors.append({'stage':'evidence','file':name,'error':str(exc)})
    if review and not all(hashes.values()): errors.append({'stage':'evidence','error':'Required result/effects receipt missing'})
    result = {'schema':1, 'scope':SCOPE, 'case':CASE, 'candidate':HEAD,
              'package_manifest_sha256':admission['manifest_sha256'],
              'overall':'PENDING_FACT_REVIEW' if review and not errors else 'FAIL',
              'mechanical':(review or {}).get('mechanical','FAIL'), 'facts':'PENDING_ROOT_INDEPENDENT_REVIEW',
              'acceptance_credit':False, 'work_cli_count':count, 'actual_native_start_count':None,
              'audio_actions':0, 'retry_authorized':False, 'errors':errors,
              'cleanup':cleanup, 'audit':audit, 'boundaries':boundaries,
              'product_result_sha256':hashes['product-result.json'],
              'effects_sha256':hashes['pre-cleanup-effects.json'],
              'finished_at':utcnow().isoformat()}
    save_new(folder/'terminal.json', result)
    return result


def main():
    parser = argparse.ArgumentParser()
    action = parser.add_mutually_exclusive_group(required=True)
    for name in ('verify','preflight','run'): action.add_argument('--'+name, action='store_true')
    args = parser.parse_args(); root = Path(__file__).resolve().parents[1]
    if args.verify: result = {'manifest_sha256':verify_package(root), 'package_verified':True}
    elif args.preflight: result = write_preflight(root)
    else: result = run_once(root)
    print(json.dumps(result, ensure_ascii=False))
    return 2 if result.get('overall') == 'FAIL' else 0


if __name__ == '__main__':
    raise SystemExit(main())
