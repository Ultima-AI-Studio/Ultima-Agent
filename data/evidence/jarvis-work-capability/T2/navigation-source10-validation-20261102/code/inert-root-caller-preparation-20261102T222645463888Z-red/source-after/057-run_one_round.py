"""Controller-released single round using the existing acceptance entry."""
from pathlib import Path
import argparse
import hashlib
import json
import os
import subprocess
import sys

CHECKOUT = Path(r'C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent')


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--authority', required=True, type=Path)
    parser.add_argument('--run-root', required=True, type=Path)
    parser.add_argument('--round', required=True, type=int, choices=(1, 2, 3))
    args = parser.parse_args()
    authority = json.loads(args.authority.read_text(encoding='utf-8-sig'))
    head = subprocess.check_output(['git', 'rev-parse', 'HEAD'], cwd=CHECKOUT, text=True).strip()
    assert authority['mode'] == 'controlled_corpus' and authority['execute'] is True
    assert authority['candidate'] == head and authority['round'] == args.round
    assert Path(authority['run_root']).resolve() == args.run_root.resolve()
    for filename, expected in authority['harness_sha256'].items():
        assert hashlib.sha256(Path(filename).read_bytes()).hexdigest() == expected
    for filename, expected in authority['candidate_sha256'].items():
        assert hashlib.sha256((CHECKOUT / filename).read_bytes()).hexdigest() == expected
    if args.round > 1:
        review = Path(authority['previous_independent_review'])
        assert hashlib.sha256(review.read_bytes()).hexdigest() == authority['previous_review_sha256']
        assert json.loads(review.read_text(encoding='utf-8-sig'))['verdict'] == 'PASS'
    args.run_root.mkdir(parents=True, exist_ok=False)
    os.environ['ULTIMA_CORPUS_WIRE_ROOT'] = str(args.run_root / 'wire')
    sys.path.insert(0, str(CHECKOUT))
    import corpus_hook
    data, calls = corpus_hook.install()
    from src.brain.tests import work_context_acceptance as acceptance
    original_launch = acceptance.launch
    original_save = acceptance.save

    def save(path, value):
        if Path(path).name == 'receipt.json':
            value = dict(value, proof='controlled_corpus', corpus_sha256=corpus_hook.CORPUS_SHA)
        return original_save(path, value)

    def launch(argv, *a, **kw):
        if argv[:2] == ['-m', 'src.brain.agent_server']:
            argv = [str(Path(corpus_hook.__file__).resolve()), *argv[2:]]
        elif argv[:2] == ['-m', 'src.brain.cli']:
            assert argv[-1] == data['query'], 'Natural E02 request changed'
        return original_launch(argv, *a, **kw)

    acceptance.launch = launch
    acceptance.save = save
    result = acceptance.round_case('e02', args.run_root / ('e02-round-' + str(args.round)))
    receipt_path = args.run_root / ('e02-round-' + str(args.round)) / 'receipt.json'
    if receipt_path.exists():
        receipt = json.loads(receipt_path.read_text(encoding='utf-8-sig'))
        actual = {s['final_url']: s['decoded_body_sha256'] for s in receipt.get('available_sources', [])}
        expected = {s['final_url']: s['decoded_body_sha256'] for s in data['sources']}
        assert actual == expected, 'Controlled fetched corpus changed'
    (args.run_root / 'controller-outcome.json').write_text(json.dumps({
        'mode': 'controlled_corpus', 'candidate': head, 'round': args.round,
        'fixture_sha256': corpus_hook.CORPUS_SHA, 'result': result,
        'parent_external_fixture_reads': calls,
        'semantic_verdict': 'PENDING_INDEPENDENT_REVIEW'}, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(result, ensure_ascii=False))
    return 0 if result.get('status') == 'succeeded' and result.get('external_verified') else 1


if __name__ == '__main__':
    raise SystemExit(main())
