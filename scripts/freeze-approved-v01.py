"""Record the explicit Owner decision and freeze exactly the submitted baseline."""
from datetime import datetime, timezone, timedelta
import hashlib
import importlib.util
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASELINE = '43ce13021f16f191bb36615ebb6c68465bf201fa'
TAG = 'v0.1-frozen'
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.dispatcher import DispatchLock
from tasks.queue_engine.card_contract import check_version_gates

def git(*args):
    return subprocess.check_output(['git', '-C', str(ROOT), *args], timeout=60, creationflags=0x08000000)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def main():
    assert git('rev-parse', 'HEAD').decode().strip() == BASELINE, 'Submitted baseline changed'
    assert not git('diff', '--name-only').strip(), 'Tracked worktree changed'
    assert not git('diff', '--cached', '--name-only').strip(), 'Staged changes present'
    assert not git('tag', '--list', TAG).strip(), 'Do not overwrite an existing freeze'
    expected_tags = {'wo-s1-host-shell-done': 'a416acf201a17eaabfa0aeae6a5144d0787a3a92',
                     'wo-s1-queue-engine-done': 'e77f417a17802601655096db0fef3224450e2abf'}
    for tag, commit in expected_tags.items():
        assert git('rev-parse', tag + '^{}').decode().strip() == commit
    w1_dir = ROOT / 'docs/reports/evidence/w1-independent-20261021/round4-post-reboot'
    w1 = json.loads((w1_dir / 'result.json').read_text(encoding='utf-8'))
    admin = json.loads((w1_dir / 'administrative-final-readback-v2.json').read_text(encoding='utf-8'))
    assert admin['status'] == 'INTERNAL_ORDER_CLOSED' and all(admin['checks'].values())
    approved = dict(w1['source_manifest'])
    w2_dir = ROOT / 'docs/reports/evidence/w2-20261021/round2'
    w2 = json.loads((w2_dir / 'independent-readback.json').read_text(encoding='utf-8'))
    assert w2['all_technical_pass'] is True and w2['final_rows'] == 35
    for path, digest in json.loads((w2_dir / 'source-manifest.json').read_text(encoding='utf-8')).items():
        p = Path(path)
        if p.is_relative_to(ROOT / 'tasks/queue_engine') or p.is_relative_to(ROOT / 'tasks/tests'):
            approved[path] = digest
    for path, expected in approved.items():
        p = Path(path)
        assert sha(p) == expected, path
        assert hashlib.sha256(git('show', BASELINE + ':' + p.relative_to(ROOT).as_posix())).hexdigest() == expected, path
    shared = ROOT.parent / '_shared/queue'
    with DispatchLock(shared / '.engineering-dispatch.lock'):
        package = ROOT / 'docs/reports/evidence/v01-freeze-20261021'
        package.mkdir(exist_ok=False)
        request = ROOT / 'docs/reports/v01-freeze-approval-request-20261021.md'
        (package / 'approved-request.md').write_bytes(request.read_bytes())
        (package / 'source-manifest.json').write_text(json.dumps(approved, indent=2), encoding='utf-8')
        at = datetime.now(timezone.utc).isoformat()
        evidence_paths = [package / 'approved-request.md', package / 'source-manifest.json',
                          w1_dir / 'result.json', w1_dir / 'administrative-final-readback-v2.json',
                          w2_dir / 'independent-readback.json', ROOT / 'docs/reports/w2-independent-acceptance-20261021.md']
        evidence = [{'path': str(p.relative_to(ROOT)).replace('\\', '/'), 'sha256': sha(p)} for p in evidence_paths]
        approval = {'gate': TAG, 'decision': 'PASS', 'approved_by': 'owner', 'approved_at': at,
                    'authorization_text': '批准按当前基线冻结 v0.1', 'baseline_commit': BASELINE,
                    'internal_tags': expected_tags, 'evidence': evidence,
                    'scope': 'v0.1 environment and host/queue baseline', 'remote_release': False,
                    'known_limit': 'Historical real Codex dispatch exited125/BLOCKED; retained, not rewritten as success'}
        gate = ROOT / 'tasks/queue/gates' / (TAG + '.json')
        gate.parent.mkdir(exist_ok=True)
        with gate.open('x', encoding='utf-8') as stream:
            json.dump(approval, stream, ensure_ascii=False, indent=2)
        git('tag', '-a', TAG, BASELINE, '-m', 'Owner approved v0.1 baseline 43ce130; approval receipt tasks/queue/gates/v0.1-frozen.json sha256=' + sha(gate))
        assert git('rev-parse', TAG + '^{}').decode().strip() == BASELINE
        gate_checks = []
        for card in ['s1-voice-cv3-wiring', 's1-task-intent-parse']:
            check_version_gates({'card_path': str(ROOT / 'tasks/cards' / card / 'task.md')}, ROOT / 'tasks')
            gate_checks.append(card)
        version = ROOT / 'docs/plans/version-plan.md'
        text = version.read_text(encoding='utf-8')
        text = text.replace('**版本**：v1.0 · 2026-10-16', '**版本**：v1.1 · 2026-10-21')
        text = text.replace('**状态**：阶段一（Windows 端到端闭环）· v0.1 进行中', '**状态**：阶段一（Windows 端到端闭环）· v0.1 已冻结，v0.2/v0.3 尚未派发')
        text = text.replace('| v0.1 | **进行中** | 环境基线 |', '| v0.1 | **已冻结** | Owner 2026-10-21批准；tag `v0.1-frozen` → `43ce130`；冻结凭据tasks/queue/gates/v0.1-frozen.json |')
        text += '\n| v1.1 | 2026-10-21 | Owner明确批准v0.1当前基线；创建v0.1-frozen固定43ce130，登记W1/W2独立验收与门凭据；后续工单仅解除此前置，不自动派发。 |\n'
        version.write_text(text, encoding='utf-8')
        text = request.read_text(encoding='utf-8')
        text = text.replace('# v0.1 冻结审批材料（待Owner审批，尚未批准）', '# v0.1 冻结审批材料（Owner已批准，已冻结）')
        text = text.replace('请Owner决定是否批准v0.1冻结。只有收到明确批准后，才登记Owner PASS凭据并创建v0.1-frozen；当前不创建这些、不派发依赖冻结门的后续工单、不远端发布。维护重启授权不作为版本冻结授权。',
                            'Owner于2026-10-21明确批准：“批准按当前基线冻结 v0.1”。已登记tasks/queue/gates/v0.1-frozen.json并创建v0.1-frozen，固定获批基线43ce13021f16f191bb36615ebb6c68465bf201fa。原提交材料已独占保存于evidence/v01-freeze-20261021/approved-request.md；本次是版本冻结授权，后续工单尚未派发，未远端发布。')
        request.write_text(text, encoding='utf-8')
        docs = ROOT / 'docs/README.md'
        text = docs.read_text(encoding='utf-8').replace('W1/W2已收口，版本冻结待Owner审批', 'W1/W2已收口，Owner已批准v0.1冻结，tag `v0.1-frozen`固定43ce130')
        text = text.replace('版本冻结待Owner审批。正式入口', 'Owner已批准v0.1冻结。正式入口').replace('（待Owner决定）', '（Owner已批准）')
        docs.write_text(text, encoding='utf-8')
        index = ROOT / 'docs/文档库索引.md'
        text = index.read_text(encoding='utf-8').replace('v0.1 待Owner冻结审批', 'v0.1 已冻结').replace('版本冻结待Owner', 'v0.1已获Owner批准')
        text = text.replace('已准备提交Owner决定；尚无Owner PASS及v0.1-frozen', 'Owner已批准；实际v0.1-frozen固定43ce130，PASS凭据已登记')
        index.write_text(text, encoding='utf-8')
        execution = ROOT / 'tasks/queue/EXECUTION.md'
        text = execution.read_text(encoding='utf-8').replace('Owner实际审批前，不越过 v0.1 冻结门。', 'Owner已明确批准，v0.1冻结门已通过；v0.2/v0.3可进入派发前检查，本次未启动后续工单。')
        execution.write_text(text, encoding='utf-8')
        registry = shared / 'global-queue-index.md'
        original = registry.read_text(encoding='utf-8')
        (package / 'global-queue.before.md').write_text(original, encoding='utf-8')
        text = original.replace('v0.1提交Owner审批', 'v0.1已获Owner批准并冻结43ce130')
        text = text.replace('旧派发失败保留，v0.1待Owner审批', '旧派发失败保留，Owner已批准v0.1-frozen')
        for order in ['wo-s1-voice-poc', 'wo-s1-task-text-loop']:
            pattern = r'^\| UltimaAgent \| ' + order + r' \| pending \| [^\n]*\|$'
            text, count = re.subn(pattern, '| UltimaAgent | ' + order + ' | pending | v0.1-frozen已获Owner批准并核验；等待逐单派发前检查，未启动 |', text, count=1, flags=re.M)
            assert count == 1, order
        assert registry.read_text(encoding='utf-8') == original
        registry.write_text(text, encoding='utf-8')
        subprocess.run([sys.executable, str(shared / 'queue-status-gen.py')], check=True, capture_output=True, timeout=20, creationflags=0x08000000)
        subprocess.run([sys.executable, str(ROOT / 'scripts/reconcile-project-state.py'), '--apply'], check=True, capture_output=True, timeout=20, creationflags=0x08000000)
        readback = {'at': at, 'gate': TAG, 'baseline_commit': BASELINE, 'tag_commit': git('rev-parse', TAG + '^{}').decode().strip(),
                    'approval_sha256': sha(gate), 'approved_source_count': len(approved), 'next_stage_gate_checks_passed': gate_checks,
                    'downstream_launched': False, 'remote_release': False}
        (package / 'readback.json').write_text(json.dumps(readback, ensure_ascii=False, indent=2), encoding='utf-8')
    git('add', '--', 'scripts/freeze-approved-v01.py', 'tasks/queue/gates/v0.1-frozen.json',
        'docs/plans/version-plan.md', 'docs/reports/v01-freeze-approval-request-20261021.md', 'docs/README.md',
        'docs/文档库索引.md', 'tasks/queue/EXECUTION.md', str(package.relative_to(ROOT)))
    git('commit', '-m', 'Record-Owner-approved-v0.1-freeze-at-43ce130')
    for item in evidence:
        assert sha(ROOT / item['path']) == item['sha256']
    assert git('rev-parse', TAG + '^{}').decode().strip() == BASELINE
    print(json.dumps({**readback, 'metadata_commit': git('rev-parse', 'HEAD').decode().strip()}, ensure_ascii=False))

if __name__ == '__main__':
    main()
