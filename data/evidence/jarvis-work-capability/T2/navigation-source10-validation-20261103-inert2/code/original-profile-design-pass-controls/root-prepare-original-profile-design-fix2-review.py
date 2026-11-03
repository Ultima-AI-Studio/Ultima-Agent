"""Root-only byte/diff packaging; never imports product or executes a case."""
from pathlib import Path
import datetime
import difflib
import hashlib
import json
import subprocess
import sys

C = Path(__file__).resolve().parents[3]
W = Path(__file__).resolve().parent
V = Path('H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261103-inert2')
T = V.parent
NAMES = ['task-4-original-corpus-profile-design.md', 'task-4-original-corpus-profile-implementation-plan.md', 'task-4-original-corpus-profile-design-report.md']
BASE = ['3c1d396f688ad7829afea772623182cd0896266040eed9f9992dce38e16dc29a', '01ded01ce7fecd503b497c01ea6fab869671c32bf3e73a0d634a7c074cb5f138', 'ba3873a2e3b28ee8dc09e08d470ac162004a1914c9c12e059ab08de88c3f7df1']
SOURCE = '118ba152b007c30d358c8bc44c51aabe8ae820f0'

def sha(raw):
    return hashlib.sha256(raw).hexdigest()

def new(path, raw):
    with path.open('xb') as handle:
        handle.write(raw)

def newjson(path, value):
    new(path, (json.dumps(value, ensure_ascii=False, indent=2) + '\n').encode('utf-8'))

def main():
    assert len(sys.argv) == 5, 'design_sha plan_sha report_sha report_bytes'
    expected = sys.argv[1:4]
    report_size = int(sys.argv[4])
    assert subprocess.check_output(['git', '-C', str(C), 'rev-parse', 'HEAD'], text=True).strip() == SOURCE
    assert not subprocess.check_output(['git', '-C', str(C), 'status', '--porcelain', '--untracked-files=no'], text=True).strip()
    prior = json.loads((V / 'original-profile-design-review-2/verdict.json').read_bytes())
    assert prior['spec'] == 'FAIL' and prior['quality'] == 'NEEDS_FIXES'
    paths_changed = {str(W / n).replace('\\', '/') for n in NAMES}
    held = {}
    for path, digest in prior['reviewed_hashes'].items():
        p = Path(path)
        if str(p).replace('\\', '/') in paths_changed:
            continue
        assert sha(p.read_bytes()) == digest, ('held binding drift', path)
        held[str(p)] = digest
    files, diff = {}, []
    for name, old_sha, new_sha in zip(NAMES, BASE, expected):
        old = (V / 'code/original-profile-design-r4' / name).read_bytes()
        current = (W / name).read_bytes()
        assert sha(old) == old_sha and sha(current) == new_sha, name
        if name == NAMES[2]:
            assert len(old) == 14918 and len(current) == report_size and current.startswith(old)
            assert len(current) > len(old), 'missing append-only fix report'
        files[name] = {'sha256': new_sha, 'bytes': len(current)}
        diff.extend(difflib.unified_diff(old.decode('utf-8').splitlines(keepends=True), current.decode('utf-8').splitlines(keepends=True), fromfile='R4/' + name, tofile='fix2/' + name, n=10))
    archive = V / 'code/original-profile-design-r5'
    archive.mkdir(exist_ok=False)
    for name in NAMES:
        new(archive / name, (W / name).read_bytes())
    newjson(archive / 'seal.json', {'schema_version': 1, 'scope': 'DESIGN_FIX2_ONLY', 'files': files, 'base_report_prefix_bytes': 14918, 'base_report_prefix_sha256': BASE[2]})
    diff_path = W / 'task-4-original-corpus-profile-design-fix2-review-diff.patch'
    new(diff_path, ''.join(diff).encode('utf-8'))
    package = W / 'task-4-original-corpus-profile-design-fix2-review-package.txt'
    parts = ['Original design FIX2 only: complete corrected documents, followed by exact R4-to-fix2 diff.\n']
    for name in NAMES:
        parts.extend(['\nFILE ' + str(W / name) + '\n', (W / name).read_text(encoding='utf-8')])
    parts.extend(['\nEXACT FIX DIFF\n', diff_path.read_text(encoding='utf-8')])
    new(package, ''.join(parts).encode('utf-8'))
    proof = V / 'original-profile-design-fix2-root-readback.json'
    newjson(proof, {'schema_version': 1, 'utc': datetime.datetime.now(datetime.timezone.utc).isoformat(), 'scope': 'DESIGN_FIX2_BYTE_READBACK_ONLY', 'candidate': SOURCE, 'held_bindings': held, 'files': files, 'archive': str(archive), 'report_prefix_bytes': 14918, 'report_prefix_sha256': BASE[2], 'diff': str(diff_path), 'diff_sha256': sha(diff_path.read_bytes()), 'package': str(package), 'package_sha256': sha(package.read_bytes()), 'code_preparation_released': False, 'runtime_released': False, 'model_calls': 0, 'T2': 'NOT_PASSED'})
    inputs = W / 'task-4-original-corpus-profile-design-fix2-review-inputs.json'
    required = [W / n for n in NAMES] + [package, diff_path, proof, V / 'original-profile-design-review-2/review.md', V / 'original-profile-design-review-2/verdict.json', W / 'task-4-original-corpus-profile-design-fix2-brief.md']
    newjson(inputs, {'schema_version': 1, 'scope': 'DESIGN_FIX2_REVIEW_INPUTS', 'hashes': {str(p): sha(p.read_bytes()) for p in required}, 'execution_released': False})
    brief = W / 'task-4-original-corpus-profile-design-fix2-rereview-brief.md'
    new(brief, f'''# Original profile design FIX2 scoped independent re-review

Read original design-review brief for binding requirements, then the original review-1 Findings OP-D01..04 verbatim and the original design-fix2 brief. Only review remaining OP-D03 constructor-selector fix and new regressions introduced by this exact diff. Hold OP-D01/02/04 closed. Do not repeat unrelated source/harness/caller/candidate review. Neither report intent nor a future test proves runtime behavior.

Complete corrected design/plan/report and exact R4-to-fix2 diff: {package}. Companion hashes {inputs}. Root byte proof {proof}; R4 archive retains all three files and original14918/ba3873a2 report prefix. Validate named source interfaces for the four fixes. No imports/tests/network/DNS/model/profile/process/UI/audio/Git or subagents. Source C118/SDK/harness/caller and all original failures remain immutable. Pure source/hash reads and NEW review output only.

For remaining OP-D03, inspect the actual Path binding/string-valued allowed_dirs constructor interface and test requirement. Report ADDRESSED or NOT_ADDRESSED with source evidence. Hold OP-D01/02/04 closed; report new fix regressions only. Flag new Critical/Important breakage only in corrected design. Preserve permanent current8B, original query774/four bodies/persona/scanners, zero actualHTTP/inference with DNS02 source-host allowance, metadata TOTAL16 including health1, real SDK write-END-ACK/readback, one-shot Root identity/exit/clock and closed readback by315. No product/code/runtime/model release.

Write NEW {V / 'original-profile-design-review-3'}/review.md and verdict.json plus identical W/task-4-original-corpus-profile-design-fix2-review-report.md. Machine schema_version1,scope ORIGINAL_PROFILE_DESIGN_FIX2_REVIEW,candidate C118,design_sha256,plan_sha256,report_sha256,spec PASS/FAIL,quality APPROVED/NEEDS_FIXES,spec_verdict=spec,quality_verdict=quality,findings[],dispositions{{OP-D01:...,OP-D02:...,OP-D03:...,OP-D04:...}},reviewed_hashes,code_preparation_released=false,runtime_released=false,model_calls=0,T2=NOT_PASSED. Human spec+quality, each disposition, exact source evidence, cannot-verify/runtime limits. Return compact verdict/findings/paths/hashes. Reviewer never implements.
'''.encode('utf-8'))
    state = json.loads((T / 'current-run.json').read_bytes())
    state.update(phase='E02_NAVIGATION_SOURCE10_ORIGINAL_PROFILE_DESIGN_FIX2_REVIEW', active_profile_design_agent=None, active_review_agent='/root/review_original_corpus_profile_design', source10_original_profile_design_status='FIX2_PENDING_SCOPED_REVIEW', source10_original_profile_design_sha256=expected[0], source10_original_profile_plan_sha256=expected[1], source10_original_profile_design_report_sha256=expected[2], source10_original_profile_design_fix2_root_proof_sha256=sha(proof.read_bytes()), source10_original_profile_design_fix2_review_brief_sha256=sha(brief.read_bytes()))
    (T / 'current-run.json').write_text(json.dumps(state, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    print(json.dumps({'held_bindings': len(held), 'files': files, 'root_proof': str(proof), 'root_proof_sha256': sha(proof.read_bytes()), 'brief_sha256': sha(brief.read_bytes()), 'package_bytes': package.stat().st_size}))

if __name__ == '__main__':
    main()
