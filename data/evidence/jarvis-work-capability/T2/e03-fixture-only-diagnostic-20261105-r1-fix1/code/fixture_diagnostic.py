"""Single-use, manifest-bound fixture diagnostic. No product or model dispatch."""
from __future__ import annotations

import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import stat
import sys
import time

HEAD = '7975e477665c02820fa235b73d203718bd33b2c9'
CASE = 'fixture-origin-01'
SCOPE = 'fixture-only-diagnostic'
PYTHON_EXECUTABLE = Path(r'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe')
AUTH_FIELDS = {'schema', 'issuer', 'scope', 'case', 'candidate', 'manifest_sha256',
               'review_sha256', 'case_cap', 'retry_authorized', 'acceptance_credit',
               'model_requests', 'product_cli_requests', 'audio_actions', 'issued_at',
               'expires_at', 'user_authorization'}
RUNTIME_FILES = {'code/fixture_diagnostic.py', 'code/native_bridge.py', 'code/controller.py',
                 'code/fixture_adapter.py', 'code/fixture_input_origin.py',
                 'code/source_candidate_guard.py', 'preparation-support/acceptance_adapter.py',
                 'inputs/protected-baseline.json'}


def require(value, message):
    if not value:
        raise ValueError(message)


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def load(path):
    def unique(pairs):
        value = {}
        for key, item in pairs:
            require(key not in value, 'Duplicate JSON key')
            value[key] = item
        return value
    raw = Path(path).read_bytes()
    require(0 < len(raw) <= 4 * 1024 * 1024, 'JSON size invalid')
    return json.loads(raw.decode('utf-8-sig'), object_pairs_hook=unique)


def safe_path(path):
    path = Path(path).absolute()
    require('..' not in path.parts, 'Traversal forbidden')
    for item in (path, *path.parents):
        try:
            attributes = item.lstat()
        except FileNotFoundError:
            require(not item.is_symlink(), 'Reparse path forbidden')
            continue
        require(not item.is_symlink() and not getattr(attributes, 'st_file_attributes', 0)
                & stat.FILE_ATTRIBUTE_REPARSE_POINT, 'Reparse path forbidden')
    return path


def child(root, relative):
    require(isinstance(relative, str) and relative and '\\' not in relative and ':' not in relative
            and all(part not in ('', '.', '..') for part in relative.split('/')), 'Noncanonical package path')
    return safe_path(root.joinpath(*relative.split('/')))


def save_new(path, value):
    with Path(path).open('x', encoding='utf-8', newline='\n') as stream:
        stream.write(json.dumps(value, ensure_ascii=False, indent=2) + '\n')
        stream.flush()
        os.fsync(stream.fileno())


def validate_authority(authority, manifest_hash, review, now):
    require(isinstance(authority, dict) and set(authority) == AUTH_FIELDS, 'Authority fields invalid')
    require(authority['schema'] == 1 and authority['issuer'] == 'root', 'Root authority required')
    require(authority['scope'] == SCOPE and authority['case'] == CASE, 'Only one fixture diagnostic allowed')
    require(authority['candidate'] == HEAD and authority['manifest_sha256'] == manifest_hash,
            'Authority candidate/package mismatch')
    require(type(authority['case_cap']) is int and authority['case_cap'] == 1
            and authority['retry_authorized'] is False and authority['acceptance_credit'] is False,
            'Single-use diagnostic cap required')
    require(all(type(authority[key]) is int and authority[key] == 0
                for key in ('model_requests', 'product_cli_requests', 'audio_actions')), 'Runtime scope expanded')
    require(isinstance(authority['user_authorization'], str) and authority['user_authorization'].strip(),
            'Explicit new user authorization missing')
    require(review.get('reviewer') == 'root-independent' and review.get('verdict') == 'PASS'
            and review.get('scope') == 'fixture-only-diagnostic-package'
            and review.get('manifest_sha256') == manifest_hash, 'Matching independent package review required')
    issued = dt.datetime.fromisoformat(authority['issued_at'])
    expires = dt.datetime.fromisoformat(authority['expires_at'])
    require(issued.tzinfo is not None and expires.tzinfo is not None and now.tzinfo is not None,
            'Timezone-aware authority times required')
    require(issued <= now < expires and 0 < (expires-issued).total_seconds() <= 600,
            'Authority expired, future-dated or overlong')
    return CASE


def verify_package(root):
    root = safe_path(root)
    manifest_path = child(root, 'manifest.json')
    manifest = load(manifest_path)
    require(manifest.get('schema') == 1 and manifest.get('scope') == SCOPE
            and manifest.get('candidate') == HEAD and manifest.get('acceptance_credit') is False,
            'Package scope mismatch')
    require(manifest.get('package_root') == str(root), 'Package relocation forbidden')
    require(manifest.get('python_executable') == str(PYTHON_EXECUTABLE), 'Package interpreter mismatch')
    paths = set()
    for entry in manifest['files']:
        require(set(entry) == {'path', 'bytes', 'sha256'} and entry['path'] not in paths,
                'Manifest entry invalid or duplicated')
        path = child(root, entry['path'])
        require(path.is_file() and path.stat().st_size == entry['bytes'] and sha(path) == entry['sha256'],
                'Sealed file mismatch: ' + entry['path'])
        paths.add(entry['path'])
    require(RUNTIME_FILES <= paths, 'Runtime dependencies omitted')
    found = {path.relative_to(root).as_posix() for directory in ('code', 'preparation-support')
             for path in (root/directory).glob('*.py')}
    require(found == {path for path in paths if path.endswith('.py')
                     and path.split('/')[0] in ('code', 'preparation-support')}, 'Unsealed Python module')
    return sha(manifest_path)


def summarize_observations(rows):
    summaries = []
    for row in rows:
        raw = row['text'].encode('utf-16le')
        allowed = ('hwnd', 'control_hwnd', 'pid', 'process_created_filetime', 'start_utf16', 'end_utf16')
        summaries.append(dict({key: row[key] for key in allowed if key in row},
                              utf16_units=len(raw)//2, sha256_utf16le=hashlib.sha256(raw).hexdigest()))
    return summaries


def execute_claimed(root, authority, backend, *, clock=time.monotonic):
    """Internal orchestrator. run_once verifies authority before constructing backend."""
    root = safe_path(root)
    folder = child(root, 'actual/' + CASE)
    if folder.exists():
        raise FileExistsError('Single diagnostic allocation already consumed')
    before = backend.preflight()  # Read-only; no admitted case or window yet.
    folder.parent.mkdir(exist_ok=True)
    folder.mkdir(exist_ok=False)  # Atomic single-use claim, retained on every failure.
    save_new(folder/'admission.json', {'scope': SCOPE, 'case': CASE, 'authority': authority,
                                      'protected_before': before, 'consumed': True,
                                      'started_at_utc': dt.datetime.now(dt.timezone.utc).isoformat(),
                                      'retry_authorized': False, 'acceptance_credit': False})
    started = clock()
    errors = []
    observation = {'phenomenon': 'UNKNOWN', 'baseline_summaries': []}
    cleanup = boundaries = audit = {'status': 'NOT_RUN'}
    try:
        backend.start(folder)
        observation = backend.capture()
    except Exception as exc:
        errors.append({'stage': 'capture', 'error_type': type(exc).__name__, 'error': str(exc)})
    finally:
        for name, function in (('cleanup', backend.close),
                               ('boundaries', lambda: backend.postflight(before)),
                               ('audit', backend.audit)):
            try:
                result = function()
            except Exception as exc:
                result = {'status': 'FAIL', 'error_type': type(exc).__name__, 'error': str(exc)}
            if name == 'cleanup': cleanup = result
            elif name == 'boundaries': boundaries = result
            else: audit = result
    elapsed = clock()-started
    late = elapsed > 60
    complete = (not errors and not late and not backend.deadline_triggered
                and observation['phenomenon'] in ('TEXT_CHANGED', 'UNCHANGED')
                and all(item.get('status') == 'PASS' for item in (cleanup, boundaries, audit)))
    result = dict(schema=1, scope=SCOPE, case=CASE, candidate=HEAD,
                  diagnostic_status='COMPLETE' if complete else 'INCOMPLETE',
                  phenomenon=observation['phenomenon'] if complete else 'UNKNOWN',
                  observed_text_state=observation['phenomenon'], baseline_summaries=observation['baseline_summaries'],
                  cleanup=cleanup, boundaries=boundaries, audit=audit, errors=errors,
                  elapsed_seconds=elapsed, deadline_exceeded=late,
                  fixture_stop_watchdog_triggered=backend.deadline_triggered,
                  product_acceptance='NOT_EVALUATED', acceptance_credit=False,
                  model_requests=0, product_cli_requests=0, audio_actions=0, retry_authorized=False)
    result['actual_native_start_count'] = None  # Shared daemon activity is not measured here.
    result['finished_at_utc'] = dt.datetime.now(dt.timezone.utc).isoformat()
    save_new(folder/'terminal.json', result)
    return result


def run_once(root, *, now=None, backend_factory=None):
    root = safe_path(root)
    manifest_hash = verify_package(root)
    authority_path = child(root, 'release/authority.json')
    review_path = child(root, 'release/independent-review.json')
    authority, review = load(authority_path), load(review_path)
    require(authority.get('review_sha256') == sha(review_path), 'Review receipt hash mismatch')
    validate_authority(authority, manifest_hash, review, now or dt.datetime.now(dt.timezone.utc))
    if child(root, 'actual/' + CASE).exists():
        raise FileExistsError('Single diagnostic allocation already consumed')
    if backend_factory is None:
        require(sys.dont_write_bytecode and not sys.flags.optimize, 'Use unoptimized Python -B')
        require(os.path.normcase(os.path.abspath(sys.executable))
                == os.path.normcase(str(PYTHON_EXECUTABLE)), 'Use the pinned original interpreter')
        from native_bridge import NativeBridge
        backend_factory = NativeBridge
    return execute_claimed(root, authority, backend_factory(root))


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--verify', action='store_true')
    parser.add_argument('--run', action='store_true')
    args = parser.parse_args()
    require(args.verify != args.run, 'Choose --verify or --run')
    root = Path(__file__).resolve().parents[1]
    if args.verify:
        print(json.dumps({'manifest_sha256': verify_package(root), 'execution_released': False}))
        return 0
    result = run_once(root)
    print(json.dumps({key: result[key] for key in ('diagnostic_status', 'phenomenon', 'product_acceptance')}))
    return 0 if result['diagnostic_status'] == 'COMPLETE' else 2


if __name__ == '__main__':
    raise SystemExit(main())
