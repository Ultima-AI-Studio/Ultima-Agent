"""One reviewed E03 round1 entry; no default release or self-approved facts."""
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
CASE = 'e03-round1'
SCOPE = 'e03-round1-acceptance'
PYTHON = Path(r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe')
RUNTIME_FILES = {'code/acceptance_entry.py', 'code/acceptance_backend.py', 'code/package_io.py',
                 'code/fixture_manual_start.py',
                 'code/controller.py', 'code/fixture_adapter.py', 'code/fixture_input_origin.py',
                 'code/source_candidate_guard.py', 'preparation-support/acceptance_adapter.py',
                 'inputs/protected-baseline.json', 'inputs/candidate-runtime-manifest.json'}
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


def verify_package(root):
    root = safe_path(root)
    manifest = load(child(root, 'manifest.json'))
    require(manifest.get('schema') == 1 and manifest.get('scope') == SCOPE
            and manifest.get('case') == CASE and manifest.get('package_root') == str(root), 'Package scope/root mismatch')
    require(manifest.get('candidate') == HEAD and manifest.get('candidate_manifest_sha256') == CANDIDATE_MANIFEST
            and manifest.get('model') == MODEL and manifest.get('digest') == DIGEST, 'Package candidate/model mismatch')
    require(manifest.get('python_executable') == str(PYTHON) and type(manifest.get('case_cap')) is int
            and manifest['case_cap'] == 1 and manifest.get('retry_authorized') is False, 'Package interpreter/cap mismatch')
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
    return sha(root/'manifest.json')


def reviewed_package(root):
    digest = verify_package(root)
    path = child(root, 'release/independent-review.json')
    review = load(path)
    require(review.get('reviewer') == 'root-independent' and review.get('verdict') == 'PASS'
            and review.get('scope') == 'e03-round1-acceptance-package'
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
    require(authority['scope'] == SCOPE and authority['case'] == CASE, 'Only original round1 scope allowed')
    require(authority['candidate'] == HEAD and authority['candidate_manifest_sha256'] == CANDIDATE_MANIFEST
            and authority['model'] == MODEL and authority['digest'] == DIGEST, 'Authority candidate/model mismatch')
    require(authority['manifest_sha256'] == manifest_hash and authority['review_sha256'] == review_hash, 'Authority package/review mismatch')
    require(all(type(authority[key]) is int and authority[key] == value
                for key, value in (('case_cap',1),('product_cli_cap',1),('audio_actions',0)))
            and authority['retry_authorized'] is False and authority['acceptance_credit'] is False
            and authority['prior_reviews'] == [], 'Single round1 allocation required')
    require(isinstance(authority['user_authorization'], str) and authority['user_authorization'].strip(), 'User authorization missing')
    proof_path = child(root, authority['proof_path'])
    require(proof_path.parent == root/'release/preflight' and proof_path.suffix == '.json', 'Canonical proof path required')
    require(sha(proof_path) == authority['proof_sha256'], 'Native proof hash mismatch')
    proof = load(proof_path)
    check_admission_time(authority, proof, now)
    assert_proof(root, proof)
    folder = child(root, 'actual/' + CASE)
    if not active and folder.exists():
        raise FileExistsError('Single round1 allocation already consumed')
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
        require(validate_release(root, utcnow(), active=True) == admission, 'Active release changed before CLI')
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
    if type(count) is not int or count not in (0,1): errors.append({'stage':'scope','error':'CLI cap violated'})
    if review and count != 1: errors.append({'stage':'scope','error':'Mechanical review without exactly one CLI'})
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
