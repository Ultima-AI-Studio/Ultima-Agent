"""Concrete ROOT inert caller. Preparation/code PASS never grants allocation."""
import time
ENTRY_NS = time.monotonic_ns()  # First real same-host clock sample; precedes case I/O.
from pathlib import Path
import datetime as dt
import hashlib
import importlib.util
import json
import os
import stat
import sys

W = Path(__file__).resolve().parent
V = Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102')
PY = Path('H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe')
CANDIDATE = '118ba152b007c30d358c8bc44c51aabe8ae820f0'
CANDIDATE_SHA = 'cdfbfb059f889ef9e92221c503dffe2ca7fa08106ebf4968bcc26037f214be50'
HARNESS_SHA = '935b3e3b1f42790c6bd3d7ebd88164f4cc47a9de9a1703557f5da0c59806bcb5'
REVIEW_SHA = '7d1d239f7b83148b90d266b29579ce937d02aeb0071838d666d5aaf94803030c'
REVIEW_REPORT_SHA = '7e4ada38af9219d3a9edf4b8e629198407c6e130b563a9c6b5cbc9c08b7c983c'
RULING_SHA = '144be9bc0a63294f5fd4e75c7cbe06f8e2ad2d51df36d0b11896d2455a0b4d47'
MODEL = dict(alias='qwen3-8b-uncensored', digest='6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330', only_current8b=True)
SCHEDULE = dict(work_seconds=275, cleanup_seconds=310, outer_seconds=315, ruling_sha256=RULING_SHA)
PORT = 18765
SCOPE = dict(actual=False, model_calls=0, native11434=False, product_cli=0, external=0, UI=0, audio=0, mic=0, max_attempts=1, retry=0)
HISTORICAL = V.parent/'e03-resume-20261102/actual/e03-round1/boundaries.json'
HISTORICAL_SHA = 'ac89211e78de8be0bed9e756419584611cd361cf66980c86b228da1fae9f91ed'
FILES = {'root-inert-invocation.py', 'test_root_inert_invocation.py', 'inert-root-release-template.json', 'run-inert-root-caller-checks.py'}


def require(ok, message):
    if not ok:
        raise ValueError(message)


def no_reparse(path):
    path = Path(path)
    for part in [*reversed(path.parents), path]:
        try:
            info = part.lstat()
        except FileNotFoundError:
            continue
        require(not stat.S_ISLNK(info.st_mode) and not getattr(info, 'st_file_attributes', 0) & stat.FILE_ATTRIBUTE_REPARSE_POINT, 'Reparse path refused')
    return path


def raw(path):
    return no_reparse(path).read_bytes()


def sha_bytes(data):
    return hashlib.sha256(data).hexdigest()


def sha(path):
    return sha_bytes(raw(path))


def exists(path):
    return no_reparse(path).exists()


def decode(data):
    def pairs(items):
        result = {}
        for key, value in items:
            require(key not in result, 'Duplicate JSON key')
            result[key] = value
        return result
    def constant(value):
        raise ValueError('Nonfinite JSON')
    return json.loads(data.decode('utf8'), object_pairs_hook=pairs, parse_constant=constant)


def load(path):
    return decode(raw(path))


def save_new(path, value):
    # Never replace, unlink, recover or reopen an existing allocation object.
    with no_reparse(path).open('x', encoding='utf8', newline='\n') as stream:
        write_json(stream, value)


def write_json(stream, value):
    json.dump(value, stream, ensure_ascii=False, indent=2, allow_nan=False)
    stream.write('\n')
    stream.flush()
    os.fsync(stream.fileno())


def stamp(value):
    value = dt.datetime.fromisoformat(value.replace('Z', '+00:00'))
    require(value.tzinfo is not None, 'Timezone required')
    return value


def utc():
    return dt.datetime.now(dt.timezone.utc)


def early_call(label, function, *args):
    require(type(ENTRY_NS) is int and 0 <= ENTRY_NS <= time.monotonic_ns(), 'Genuine earlier clock origin required')
    if time.monotonic_ns() >= ENTRY_NS + 275_000_000_000:
        raise TimeoutError('Deadline admission: ' + label)
    result = function(*args)
    if time.monotonic_ns() > ENTRY_NS + 275_000_000_000:
        raise TimeoutError('Late return: ' + label)
    return result


def release_check(release):
    fixed = dict(schema=1, kind='source10_inert_root_release', issuer='root', released=True,
                 candidate=CANDIDATE, candidate_manifest_sha256=CANDIDATE_SHA,
                 harness_manifest_sha256=HARNESS_SHA, harness_review_sha256=REVIEW_SHA,
                 harness_review_report_sha256=REVIEW_REPORT_SHA, schedule=SCHEDULE,
                 model_policy=MODEL, scope=SCOPE, port=PORT,
                 run_scope='one-new-inert-root-invocation')
    dynamic = {'issued_at', 'expires_at', 'caller_manifest_sha256', 'approval_sha256', 'caller_review_sha256', 'caller_review_report_sha256'}
    require(set(release) == set(fixed) | dynamic, 'Exact ROOT release fields required')
    # Exact JSON scalar types: False/0 and True/1 are not interchangeable.
    for key, value in fixed.items():
        require(json.dumps(release[key], sort_keys=True) == json.dumps(value, sort_keys=True), 'ROOT release binding: ' + key)
    for key in dynamic - {'issued_at', 'expires_at'}:
        value = release[key]
        require(isinstance(value, str) and len(value) == 64 and all(c in '0123456789abcdef' for c in value), 'ROOT digest required: ' + key)
    issued, expires = stamp(release['issued_at']), stamp(release['expires_at'])
    require(issued <= utc() < expires and 0 < (expires-issued).total_seconds() <= 120, 'Stale ROOT release')


def check_controls(release, call):
    manifest_raw = call('caller manifest', raw, W/'inert-root-caller-manifest.json')
    require(sha_bytes(manifest_raw) == release['caller_manifest_sha256'], 'Caller manifest drift')
    manifest = decode(manifest_raw)
    require(manifest['candidate'] == CANDIDATE and set(manifest['files']) == FILES, 'Exact caller package required')
    for name, digest in manifest['files'].items():
        require(call('caller raw pin', sha, W/name) == digest, 'Caller source drift: ' + name)
    for path, digest in manifest['dependencies'].items():
        require(call('dependency pin', sha, Path(path)) == digest, 'Pinned dependency drift: ' + path)
    require(call('candidate pin', sha, V/'source10-candidate-manifest.json') == CANDIDATE_SHA, 'Candidate drift')
    require(call('harness pin', sha, V/'harness/manifest.json') == HARNESS_SHA, 'Harness manifest drift')
    harness = call('harness manifest read', load, V/'harness/manifest.json')
    require(set(harness['files']) == {'adapter.py', 'test_adapter.py', 'headless_proof.py', 'README.md', 'run_checks.py'}, 'Exact harness package')
    for name, digest in harness['files'].items():
        require(call('harness source pin', sha, V/'harness'/name) == digest, 'Harness source drift')
    approval_raw = call('ROOT approval', raw, V/'harness-approval.json')
    require(sha_bytes(approval_raw) == release['approval_sha256'], 'Current approval digest mismatch')
    approval = decode(approval_raw)
    expected = dict(reviewer='root-independent', overall='PASS', candidate=CANDIDATE,
                    manifest_sha256=HARNESS_SHA, candidate_manifest_sha256=CANDIDATE_SHA,
                    review_sha256=REVIEW_SHA, review_report_sha256=REVIEW_REPORT_SHA,
                    caller_manifest_sha256=release['caller_manifest_sha256'],
                    caller_review_sha256=release['caller_review_sha256'],
                    caller_review_report_sha256=release['caller_review_report_sha256'],
                    caller_spec='PASS', caller_quality='APPROVED', model_policy=MODEL)
    require(all(approval.get(k) == v for k, v in expected.items()), 'ROOT approval must cover current harness AND caller')
    for name, key in [('verdict.json', 'caller_review_sha256'), ('review.md', 'caller_review_report_sha256')]:
        require(call('caller independent review pin', sha, V/'inert-root-caller-review'/name) == release[key], 'Caller review drift')
    review = call('caller verdict', load, V/'inert-root-caller-review/verdict.json')
    require(review.get('spec') == 'PASS' and review.get('quality') == 'APPROVED' and review.get('caller_manifest_sha256') == release['caller_manifest_sha256'], 'Caller independent verdict required')
    return harness


def checked_import(name, path, digest):
    require(name not in sys.modules, 'Unexpected cached module: ' + name)
    data = raw(path)
    require(sha_bytes(data) == digest, 'Import source drift: ' + name)
    spec = importlib.util.spec_from_file_location(name, path)
    module = importlib.util.module_from_spec(spec)
    # Execute precisely the bytes just checked, without a pyc fallback or second read.
    exec(compile(data, str(path), 'exec'), module.__dict__)
    return module


def load_harness(harness):
    require('adapter' not in sys.modules and 'headless_proof' not in sys.modules, 'Unexpected cached harness modules')
    previous = list(sys.path)
    try:
        adapter = checked_import('adapter', V/'harness/adapter.py', harness['files']['adapter.py'])
        sys.modules['adapter'] = adapter
        headless = checked_import('headless_proof', V/'harness/headless_proof.py', harness['files']['headless_proof.py'])
        require(headless.a is adapter, 'Headless adapter identity mismatch')
        return adapter, headless
    finally:
        # No shared module replacement; our temporary import binding is scoped.
        sys.modules.pop('adapter', None)
        sys.path[:] = previous


def exact_native(current, expected):
    for members in (current, expected):
        require(type(members) is list and len(members) == 5, 'Exact protected five required')
        require(all(type(x) is dict and set(x) == {'pid', 'created_filetime', 'exe'} and
                    type(x['pid']) is int and x['pid'] > 0 and
                    type(x['created_filetime']) is int and x['created_filetime'] > 0 and
                    type(x['exe']) is str and bool(x['exe']) for x in members), 'Exact native scalar types required')
        require(len({x['pid'] for x in members}) == 5, 'Duplicate protected member')
    require({x['pid']: x for x in current} == {x['pid']: x for x in expected}, 'Historical exact native identity drift')


def run():
    inv = None
    consumed = False
    outcome = None
    first_cause = None
    release = None
    claim_sha = None
    def call(label, function, *args):
        return inv.budget.call(label, function, *args) if inv else early_call(label, function, *args)
    def consume():
        nonlocal consumed
        with no_reparse(V/'inert-root-release.consumed.json').open('x', encoding='utf8', newline='\n') as stream:
            consumed = True  # Exclusive creation is consumption, even if close/post fails.
            write_json(stream, dict(release_sha256=sha_bytes(release_raw), origin_ns=ENTRY_NS,
                                    consumed_at=utc().isoformat(), attempts=1, retry=0))
    try:
        release_raw = call('ROOT release read', raw, V/'inert-root-release.json')
        release = decode(release_raw)
        call('ROOT release admission', release_check, release)
        # Claim is outside the future case root. Any subsequent failure is final.
        call('exclusive ROOT allocation consumption', consume)
        claim_sha = call('consumption immutable raw pin', sha, V/'inert-root-release.consumed.json')
        for name in ('inert-authority.json', 'inert-native-baseline.json', 'inert-root-result.json'):
            require(not call('canonical existence', exists, V/name), 'Existing canonical object: ' + name)
        harness = check_controls(release, call)
        a, headless = call('checked harness import', load_harness, harness)
        inv = a.RootInvocation()
        inv.budget.adopt_parent(dict(clock_domain=a.CLOCK_DOMAIN, run_id=inv.budget.run_id, origin_ns=ENTRY_NS))
        call('revalidate release before native entry', release_check, release)
        folder = V/'inert'/inv.budget.run_id
        require(not call('new inert folder check', exists, folder), 'Existing inert attempt')
        require(call('ROOT release immutable', sha, V/'inert-root-release.json') == sha_bytes(release_raw), 'Release changed after consumption')
        p4 = call('pinned original P4 definitions', a.load_p4)
        call('original package check', a.package_check, p4)
        call('source/SDK/helper pins', a.check_inputs)
        call('source import origins', a.check_import_origins)
        require(call('historical precise native pin', sha, HISTORICAL) == HISTORICAL_SHA, 'Historical native proof drift')
        expected = call('historical precise native proof', load, HISTORICAL)['protected5']
        protected = call('fresh original protected native identities', p4.protected)
        exact_native(protected, expected)
        call('fresh native member validation', a.validate_protected_members, protected, p4)
        parent_timing = call('same ROOT native parent timing', inv.parent_timing)
        with a.PrivateIO(p4, inv.budget):
            require(not call('fixed inert port unused', p4.listener_owner, PORT), 'Controlled inert port occupied')
        baseline = dict(precision='FILETIME100ns', candidate=CANDIDATE, recorded_at=utc().isoformat(), protected=protected)
        call('native baseline validation', a.check_native_baseline, baseline, p4)
        call('exclusive canonical native baseline', save_new, V/'inert-native-baseline.json', baseline)
        now = utc()
        authority = dict(schema=11, kind='source10_inert_qualification', issuer='root', actual=False,
                         model_calls=0, native11434=False, candidate=CANDIDATE,
                         candidate_manifest_sha256=CANDIDATE_SHA, approval_sha256=release['approval_sha256'],
                         native_baseline_sha256=call('baseline raw binding', sha, V/'inert-native-baseline.json'),
                         issued_at=now.isoformat(), expires_at=min(now+dt.timedelta(seconds=120), stamp(release['expires_at'])).isoformat(),
                         run_id=inv.budget.run_id, folder=str(folder), port=PORT, schedule=SCHEDULE,
                         parent_timing=parent_timing)
        call('existing inert schema validator', a.validate_inert_documents, authority, utc())
        call('exclusive canonical inert authority', save_new, V/'inert-authority.json', authority)
        check_controls(release, call)
        call('final ROOT release freshness', release_check, release)
        require(call('final ROOT release raw pin', sha, V/'inert-root-release.json') == sha_bytes(release_raw), 'Release drift')
        require(call('final consumption raw pin', sha, V/'inert-root-release.consumed.json') == claim_sha, 'Consumption drift')
        # Sole released entry; existing RootInvocation owns all substantive proof.
        inv.budget.pre('one inert invocation')
        outcome = inv.call(headless.run_inert)
        # Extra ROOT controls are immutable, separately pinned; never edit its witness.
        check_controls(release, lambda label, function, *args: function(*args))
        require(sha(V/'inert-root-release.json') == sha_bytes(release_raw), 'Release drift after observation')
        require(sha(V/'inert-root-release.consumed.json') == claim_sha, 'Consumption drift after observation')
    except Exception as exc:
        first_cause = dict(type=type(exc).__name__, message=str(exc))
    if not consumed:
        if first_cause:
            raise ValueError(first_cause['message'])
        raise ValueError('Allocation was not consumed')
    # Adjudication may be persisted later. Actual observation remains untouched.
    witness = outcome.get('witness') if isinstance(outcome, dict) else None
    eligible = bool(first_cause is None and isinstance(witness, dict) and witness.get('eligible') is True and witness.get('permanent') is True)
    if not eligible and first_cause is None:
        first_cause = dict(type='IneligibleObservation', message=(getattr(inv.budget, 'failure', None) if inv else None) or 'Missing, failed, or late trusted observation')
    record = dict(kind='source10_inert_root_adjudication', outcome=outcome, first_cause=first_cause,
                  overall='ELIGIBLE_FOR_ROOT_REVIEW' if eligible else 'PERMANENT_FAIL',
                  effects='see original returned result and witness' if outcome else 'unknown',
                  persistence_started_at=utc().isoformat(), persistence_started_monotonic_ns=time.monotonic_ns(),
                  origin_ns=ENTRY_NS, attempts=1, retry=0, actual=False, model_calls=0,
                  T2='NOT_PASSED', T3='CLOSED', Owner='CLOSED', production='CLOSED')
    save_new(V/'inert-root-result.json', record)
    return record


def main():
    require(not sys.argv[1:] and Path(sys.executable).resolve() == PY.resolve() and
            sys.flags.dont_write_bytecode and sys.flags.utf8_mode == 1 and not sys.flags.optimize,
            'Fixed H Python -B -X utf8; no arguments or optimization')
    record = run()
    print(json.dumps(record, ensure_ascii=False))
    return 0 if record['overall'] == 'ELIGIBLE_FOR_ROOT_REVIEW' else 2


if __name__ == '__main__':
    raise SystemExit(main())
