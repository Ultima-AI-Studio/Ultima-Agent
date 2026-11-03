from pathlib import Path
import datetime
import hashlib
import json
import subprocess

C = Path(r'C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent')
H = Path(r'H:/UltimaAI/UltimaAgent')
M = Path(r'H:/UltimaAI/ultima-docs-repo')
V = H / 'data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261103-inert2'
receipt_path = V / 'publication-original-profile-root-interface-local.json'
receipt = json.loads(receipt_path.read_text('utf-8'))

def run(repo, args, data=None):
    p = subprocess.run(['git', '-C', str(repo), *args], input=data, capture_output=True)
    assert p.returncode == 0, p.stderr.decode('utf-8', 'replace')[:2000]
    return p.stdout

def sha(data):
    return hashlib.sha256(data).hexdigest()

net = ['-c', 'http.proxy=http://127.0.0.1:7897', '-c', 'http.https://github.com.proxy=http://127.0.0.1:7897', '-c', 'http.version=HTTP/1.1']
project_expected = {
    'refs/heads/' + receipt['branch']: receipt['project_commit'],
    'refs/heads/codex/jarvis-work-navigation-v3-source10': receipt['product_source_commit'],
    'refs/tags/' + receipt['evidence_tag'] + '^{}': receipt['project_commit'],
    'refs/tags/' + receipt['product_source_tag'] + '^{}': receipt['product_source_commit'],
}
mirror_expected = {
    'refs/heads/main': receipt['mirror_commit'],
    'refs/tags/' + receipt['evidence_tag'] + '^{}': receipt['mirror_commit'],
    'refs/tags/' + receipt['product_source_tag'] + '^{}': receipt.get('product_source_mirror_commit', receipt['mirror_commit']),
}
remote = {}
for label, repo, expected in [('project', C, project_expected), ('mirror', M, mirror_expected)]:
    raw = run(repo, [*net, 'ls-remote', 'origin', *expected])
    found = dict((ref, oid) for oid, ref in (line.split() for line in raw.decode('utf-8').splitlines()))
    assert all(found.get(ref) == oid for ref, oid in expected.items()), (label, found, expected)
    remote[label] = found

def read_blobs(repo, commit, expected):
    specs = [commit + ':' + path for path in expected]
    raw = run(repo, ['cat-file', '--batch'], ('\n'.join(specs) + '\n').encode('utf-8'))
    offset = 0
    checked = {}
    for path in expected:
        end = raw.index(b'\n', offset)
        head = raw[offset:end].split()
        assert len(head) == 3 and head[1] == b'blob', (path, head)
        size = int(head[2])
        body = raw[end + 1:end + 1 + size]
        assert len(body) == size and raw[end + 1 + size:end + 2 + size] == b'\n'
        digest = sha(body)
        assert expected[path] is None or digest == expected[path], path
        checked[path] = {'bytes': size, 'sha256': digest, 'git_oid': head[0].decode('ascii')}
        offset = end + size + 2
    assert offset == len(raw)
    return checked

assert not run(M, [*net, 'ls-remote', 'origin', 'refs/main']).strip(), 'Unexpected refs/main'

project_bytes = read_blobs(C, receipt['project_commit'], receipt['hashes'])
mirror_bytes = read_blobs(M, receipt['mirror_commit'], receipt['mirror_paths'])
source_paths = run(C, ['diff', '--name-only', '244d2120abcd6b8d7744f74a05bd22de46a2d3a5', receipt['product_source_commit']]).decode('utf-8').splitlines()
source_bytes = read_blobs(C, receipt['product_source_commit'], dict.fromkeys(source_paths))
expected_source_paths = {
    'docs/plans/jarvis-work-research-source-navigation-design-20261102.md',
    'docs/plans/jarvis-work-research-source-navigation-implementation-20261102.md',
    'docs/specs/jarvis-work-research-navigation-v3-20261102.md',
    'src/brain/agent_server.py', 'src/brain/work_navigation.py', 'src/brain/work_research.py',
    'src/brain/work_service.py', 'src/brain/work_tools.py', 'src/brain/tests/test_work_context.py',
    'src/brain/tests/test_work_navigation.py', 'src/brain/tests/test_work_research.py',
    'src/brain/tests/test_work_navigation_sdk.py', 'src/brain/tests/test_work_navigation_transport.py',
}
assert set(source_paths) == expected_source_paths, source_paths
advanced_mutable_snapshot = {}
for path in receipt['hashes']:
    current_raw = (H / path).read_bytes()
    if sha(current_raw) != receipt['hashes'][path] and path == 'data/evidence/jarvis-work-capability/T2/current-run.json':
        committed_raw = run(C, ['show', receipt['project_commit'] + ':' + path])
        before = json.loads(committed_raw)
        after = json.loads(current_raw)
        extra = {'source10_original_profile_capture_ruling', 'source10_original_profile_capture_ruling_sha256'}
        assert set(after) - set(before) == extra and not (set(before)-set(after))
        assert all(after[k] == value for k,value in before.items())
        assert after['source10_original_profile_capture_ruling_sha256'] == 'a34a0baa617ac68633f26f6c64ac9669eac2dfb27c842b768d55812439638a95'
        advanced_mutable_snapshot[path] = {'committed_sha256': sha(committed_raw), 'current_sha256': sha(current_raw), 'only_added_keys': sorted(extra), 'reason': 'ROOT_CAPTURE02_ruling_added_after_commit_before_readback;immutable_blob_verified'}
    else:
        assert sha(current_raw) == receipt['hashes'][path], path
for path in receipt['mirror_paths']:
    assert sha((M / path).read_bytes()) == receipt['mirror_paths'][path], path
out = V / 'publication-original-profile-root-interface-remote-readback.json'
with out.open('x', encoding='utf-8', newline='\n') as f:
    json.dump({'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(),
        'independent_process': True, 'local_receipt_sha256': sha(receipt_path.read_bytes()),
        'remote_refs': remote, 'project_blobs': project_bytes, 'mirror_blobs': mirror_bytes,
        'source_blobs': source_bytes, 'local_raw_bytes_match': not bool(advanced_mutable_snapshot), 'advanced_mutable_snapshot': advanced_mutable_snapshot,
        'semantics': 'Originalprofile design PASS fourclosed;sourceC118/SDK/prod preserved,current8Bonly. Fivefilecode/offlinecontracts preparation only,no originalprofile/runtime/DNS/network/model/T3grant;alloldfailures retained.',
        'model_calls': 0, 'unexpected_refs_main_absent': True}, f, ensure_ascii=False, indent=2)
    f.write('\n')
print(json.dumps({'receipt': str(out), 'sha256': sha(out.read_bytes()),
    'project_blobs_checked': len(project_bytes), 'mirror_blobs_checked': len(mirror_bytes),
    'source_blobs_checked': len(source_bytes), 'all_remote_refs_match': True}, ensure_ascii=False))
