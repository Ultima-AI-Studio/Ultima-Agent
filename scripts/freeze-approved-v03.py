"""Apply the Owner's explicit approval to the submitted W4 baseline only."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
BASE = '731710a80358b062d1064ccaf08f758483a9d958'
TAG = 'v0.3-frozen'
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.dispatcher import DispatchLock
from tasks.queue_engine.card_contract import check_version_gates
spec = importlib.util.spec_from_file_location('adapter', ROOT / 'scripts/dispatch-work-order.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, timeout=30, creationflags=0x08000000)
def edit(relative, pairs):
    path = ROOT / relative
    before = path.read_bytes()
    newline = '\r\n' if before.count(b'\r\n') > before.count(b'\n') * .8 else '\n'
    text = before.decode('utf-8').replace('\r\n', '\n')
    for old, new in pairs:
        assert old in text, (relative, old)
        text = text.replace(old, new)
    assert path.read_bytes() == before
    path.write_text(text, encoding='utf-8', newline=newline)

def main():
    assert git('rev-parse', 'wo-s1-task-text-loop-done').decode().strip() == BASE
    review_path = ROOT / 'docs/reports/evidence/w4-independent-20261021/round2-correction/result-final.json'
    review = json.loads(review_path.read_text(encoding='utf-8'))
    assert review['verdict'] == 'PASS' and all(review['conditions'].values())
    for relative, expected in review['source-manifest'].items():
        assert sha(ROOT / relative) == expected
        assert hashlib.sha256(git('show', BASE + ':' + relative)).hexdigest() == expected
    v01_manifest_path = ROOT / 'docs/reports/evidence/v01-freeze-20261021/source-manifest.json'
    v01_manifest = json.loads(v01_manifest_path.read_text(encoding='utf-8'))
    assert len(v01_manifest) == 36 and all(sha(Path(p)) == h for p,h in v01_manifest.items())
    assert git('rev-parse', 'v0.1-frozen^{}').decode().strip() == '43ce13021f16f191bb36615ebb6c68465bf201fa'
    for folder in ['round1', 'round2-correction']:
        directory = ROOT / 'docs/reports/evidence/w4-independent-20261021' / folder
        pins = json.loads((directory / 'evidence-sha256.json').read_text(encoding='utf-8'))
        assert all(sha(directory / path) == digest for path,digest in pins.items())
    assert sha(ROOT / 'tasks/tasks.json') == '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570'
    assert not git('tag', '--list', TAG).strip()
    gate = ROOT / 'tasks/queue/gates/v0.3-frozen.json'
    assert not gate.exists()
    check_version_gates({'card_path': str(ROOT / 'tasks/cards/s1-task-intent-parse/task.md')}, ROOT / 'tasks')
    package = ROOT / 'docs/reports/evidence/v03-freeze-20261021'
    with DispatchLock(adapter.SHARED / '.engineering-dispatch.lock'):
        assert not any(p['role'] in {'exec','unknown'} and (not p['project'] or Path(p['project']).resolve() == ROOT) for p in adapter.native.codex_processes())
        package.mkdir(exist_ok=False)
        request = ROOT / 'docs/reports/v03-freeze-approval-request-20261021.md'
        (package / 'approved-request.md').write_bytes(request.read_bytes())
        (package / 'accepted-technical-report.md').write_bytes((ROOT / 'docs/reports/w4-text-loop-acceptance-20261021.md').read_bytes())
        (package / 'source-manifest.json').write_text(json.dumps(review['source-manifest'], indent=2), encoding='utf-8', newline='\n')
        evidence_paths = [package / 'approved-request.md', package / 'accepted-technical-report.md', package / 'source-manifest.json', review_path,
            ROOT / 'docs/reports/evidence/w4-independent-20261021/round2-correction/cli-window-observation.json',
            ROOT / 'docs/reports/evidence/text-loop-closeout-20261021/administrative-readback.json']
        at = datetime.now(timezone.utc).isoformat()
        approval = {'gate': TAG, 'decision': 'PASS', 'approved_by': 'owner', 'approved_at': at,
            'authorization_text': '批准', 'approval_context': '用户对v0.3候选731710a冻结申请的明确批准',
            'baseline_commit': BASE, 'internal_tag': 'wo-s1-task-text-loop-done',
            'scope': '工单④U12-U14文本闭环，10执行单元；不包含完整语音/组合窗口/发布',
            'evidence': [{'path': p.relative_to(ROOT).as_posix(), 'sha256': sha(p)} for p in evidence_paths],
            'remote_release': False, 'audio_playback_authorized': False, 'microphone_capture_authorized': False,
            'known_limits': ['语音W3/v0.2未完成', '旧引擎首次回归偶发失败日志保留，未宣称根治']}
        with gate.open('x', encoding='utf-8') as stream:
            json.dump(approval, stream, ensure_ascii=False, indent=2)
        git('tag', '-a', TAG, BASE, '-m', 'Owner-approved-v0.3-baseline-731710a;receipt-sha256=' + sha(gate))
        assert git('rev-parse', TAG + '^{}').decode().strip() == BASE
        for card in ['s1-window-dsl-schema', 's1-window-composite-render', 's1-window-theme-floatball']:
            check_version_gates({'card_path': str(ROOT / 'tasks/cards' / card / 'task.md')}, ROOT / 'tasks')
        preflight = {'at': at, 'work_order': 'wo-s1-composite-window', 'version_gate': 'PASS',
            'v03_tag_commit': BASE, 'full_order_ready': False,
            'unresolved_dependency': {'task': 's1-window-theme-floatball', 'dependsOn': 's1-voice-four-io', 'completed': False},
            'evidence': 'tasks/cards/s1-window-theme-floatball/task.md dependsOn；语音工单仅预检与已有音频复验，尚无完整实现及W3通过',
            'acceptance_kept': 'CR-04/TF-04窗口与语音同时交付真机门保留，不以离线识别代替',
            'owner_constraint': '仅已有音频离线验证，不播放、不采集麦克风', 'dispatched': False}
        (package / 'v04-dispatch-preflight.json').write_text(json.dumps(preflight, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
        _, match, _ = adapter.registered('wo-s1-task-text-loop')
        adapter.state('wo-s1-task-text-loop', 'frozen', 'W4通过；Owner已批准v0.3-frozen固定731710a；原失败证据保留', package, expected=match.group(1))
        _, match, _ = adapter.registered('wo-s1-composite-window')
        assert match.group(1) == 'pending'
        adapter.state('wo-s1-composite-window', 'pending', 'v0.3-frozen已获Owner批准；整单派发前检查发现T3依赖s1-voice-four-io尚未完成；保留双通道真机验收与不播放/不采集限制，未派发', package, expected='pending')
    edit('docs/reports/v03-freeze-approval-request-20261021.md', [
        ('**待Owner批准；尚未创建v0.3-frozen或Owner通过凭据。**', '**Owner已批准，v0.3已冻结。** 2026-10-21用户明确回复“批准”；原申请已保存于evidence/v03-freeze-20261021/approved-request.md。'),
        ('Owner如批准此候选，才创建v0.3-frozen及包含实际批准原文、候选提交和证据哈希的Owner回执。批准后工单⑤方可进入派发前检查；本轮没有启动工单⑤，没有远程发布。',
         '已创建v0.3-frozen，固定获批候选731710a80358b062d1064ccaf08f758483a9d958；Owner凭据为tasks/queue/gates/v0.3-frozen.json。工单⑤版本前置检查已通过，但T3仍依赖未完成的语音四IO，整单未派发；窗口+语音真机门保留，没有远程发布。')])
    edit('docs/plans/version-plan.md', [
        ('**版本**：v1.2 · 2026-10-21','**版本**：v1.3 · 2026-10-21'),
        ('v0.3文本闭环W4通过、待Owner冻结', 'v0.3文本闭环已获Owner批准并冻结'),
        ('| v0.3 | 技术验收通过、待冻结 | W4两项问题修正后独立49/49，文本16/16；待Owner批准v0.3冻结，未启动v0.4 |',
         '| v0.3 | **已冻结** | Owner于2026-10-21批准；v0.3-frozen固定731710a；工单⑤仍待T3语音四IO依赖 |')])
    with (ROOT / 'docs/plans/version-plan.md').open('a', encoding='utf-8') as stream:
        stream.write('\n| v1.3 | 2026-10-21 | Owner批准v0.3候选731710a并冻结；v0.4版本门通过，但整单仍待T3语音四IO前置。 |\n')
    edit('docs/specs/registry.md', [
        ('**版本**：v1.3 · 2026-10-21', '**版本**：v1.4 · 2026-10-21'),
        ('W4技术验收通过；16项文本测试、49项独立检查；v0.3待Owner冻结', 'W4通过；16项文本测试、49项独立检查；Owner已批准v0.3-frozen固定731710a')])
    with (ROOT / 'docs/specs/registry.md').open('a', encoding='utf-8') as stream:
        stream.write('\n| v1.4 | 2026-10-21 | Owner批准v0.3文本闭环冻结731710a，不扩大为完整语音或组合窗口通过。 |\n')
    edit('tasks/queue/wo-s1-task-text-loop.md', [('- [ ] 冻结基线标记：tag `v0.3-frozen`', '- [x] 冻结基线标记：tag `v0.3-frozen`'),
        ('版本标签项保持未勾选；Owner批准v0.3冻结前，工单⑤不得启动。', 'Owner已批准v0.3冻结731710a；工单⑤版本门已通过，整单仍待语音四IO依赖就绪。')])
    edit('tasks/acceptance-checklist.md', [('**版本**：v2.1 · 2026-10-21','**版本**：v2.2 · 2026-10-21'),
        ('| 未冻结，待Owner批准 | docs/reports/w4-text-loop-acceptance-20261021.md |', '| v0.3-frozen（Owner已批准731710a） | docs/reports/w4-text-loop-acceptance-20261021.md |')])
    with (ROOT / 'tasks/acceptance-checklist.md').open('a', encoding='utf-8') as stream:
        stream.write('\n| v2.2 | 2026-10-21 | Owner批准v0.3冻结731710a，验收结果及旧失败记录保持不变。 |\n')
    edit('docs/README.md', [('v0.3冻结申请 `reports/v03-freeze-approval-request-20261021.md`，待Owner批准。', 'v0.3冻结申请 `reports/v03-freeze-approval-request-20261021.md` 已获Owner批准，实际v0.3-frozen固定731710a；工单⑤版本门已过，仍待语音四IO依赖。')])
    edit('docs/reports/w4-text-loop-acceptance-20261021.md', [
        ('v0.3 版本冻结仍待 Owner 批准。', 'Owner于2026-10-21明确回复“批准”，v0.3现已冻结于731710a。'),
        ('v0.3未打版本冻结标签，未代签Owner；组合窗口及其他后续工单尚未启动。', 'Owner实际批准后已创建v0.3-frozen及批准凭据；工单⑤版本门通过，但仍待语音四IO依赖，组合窗口及其他后续工单尚未启动。')])
    edit('tasks/queue/EXECUTION.md', [('尚未批准v0.3冻结。','Owner现已批准v0.3冻结731710a。')])
    edit('tasks/queue/stage1-unit-queue.md', [('W4技术验收通过、待Owner版本审批', 'W4技术验收通过且Owner已批准v0.3-frozen固定731710a')])
    for card in ['s1-task-intent-parse','s1-task-queue-source','s1-task-aggregate-report']:
        with (ROOT / 'tasks/cards' / card / 'task.md').open('a', encoding='utf-8') as stream:
            stream.write('\n## Owner版本决定（2026-10-21）\n\n用户对候选731710a明确回复“批准”。v0.3-frozen固定731710a80358b062d1064ccaf08f758483a9d958；凭据tasks/queue/gates/v0.3-frozen.json。前文待审批段落为历史记录。\n')
    projection = ROOT / 'sync/product.json'
    before = projection.read_bytes()
    (package / 'product.before.json').write_bytes(before)
    data = json.loads(before.decode('utf-8'))
    old_v01 = data['version_freeze']
    assert old_v01['version'] == 'v0.1'
    current = {'version': 'v0.3','state': '已冻结','tag': TAG,'baseline_commit': BASE,'approval': 'tasks/queue/gates/v0.3-frozen.json'}
    data['version_freezes'] = {'v0.1': old_v01, 'v0.3': current}
    data['version_freeze'] = current
    data['version'] = '0.3.0'
    data.pop('pending_version_freeze', None)
    projection.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
    subprocess.run([sys.executable, str(ROOT / 'scripts/sync-supervised-development-state.py')], cwd=ROOT, check=True, capture_output=True, creationflags=0x08000000)
    for item in approval['evidence']:
        assert sha(ROOT / item['path']) == item['sha256']
    assert git('rev-parse', TAG + '^{}').decode().strip() == BASE
    assert all(sha(ROOT / p) == h for p,h in review['source-manifest'].items())
    readback = {'at': at,'gate': TAG,'baseline_commit': BASE,'tag_commit': git('rev-parse', TAG + '^{}').decode().strip(),
        'owner_approval_sha256': sha(gate),'accepted_source_items': 10,'v01_items_unchanged':36,
        'approval_evidence_hashes_valid':True,'v04_version_gate':'PASS','v04_full_order_ready':False,
        'downstream_launched':False,'audio_played_or_recorded':False,'remote_release':False,
        'projection_version':json.loads(projection.read_text(encoding='utf-8'))['version']}
    (package / 'readback.json').write_text(json.dumps(readback, ensure_ascii=False, indent=2), encoding='utf-8', newline='\n')
    print(json.dumps(readback, ensure_ascii=False))

if __name__ == '__main__':
    main()
