"""Prepare reviewable W4 closeout without granting a version freeze."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.card_contract import check_version_gates
from tasks.queue_engine.dispatcher import process_identity
OUT = ROOT / 'docs/reports/evidence/text-loop-closeout-20261021'
review_dir = ROOT / 'docs/reports/evidence/w4-independent-20261021/round2-correction'
review = json.loads((review_dir / 'result-final.json').read_text(encoding='utf-8'))
assert review['verdict'] == 'PASS' and all(review['conditions'].values())
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
for path, expected in review['source-manifest'].items():
    assert sha(ROOT / path) == expected, path
v01 = json.loads((ROOT / 'docs/reports/evidence/v01-freeze-20261021/source-manifest.json').read_text(encoding='utf-8'))
assert all(sha(Path(path)) == expected for path, expected in v01.items())
seals = []
for directory in [review_dir.parent / 'round1', review_dir, ROOT / 'logs/text-loop-w4-repair-20261021']:
    pins = json.loads((directory / 'evidence-sha256.json').read_text(encoding='utf-8'))
    assert all(sha(directory / name) == expected for name, expected in pins.items())
    seals.append({'path': str(directory.relative_to(ROOT)), 'files': len(pins), 'manifest_sha256': sha(directory / 'evidence-sha256.json')})
run = ROOT / 'tasks/queue/runs/wo-s1-task-text-loop-20261021T044748126206Z'
done = json.loads((run / 'done.json').read_text())
session = json.loads((run / 'session.json').read_text())
assert done['exit_code'] == 0 and done['receipt_valid'] and not done['parent_lost']
assert process_identity(session['pid']) != session['identity']
old = ROOT / 'tasks/queue/runs/wo-s1-host-shell-20261021T023427316731Z/done.json'
assert json.loads(old.read_text())['exit_code'] == 125
check_version_gates({'card_path': str(ROOT / 'tasks/cards/s1-task-intent-parse/task.md')}, ROOT / 'tasks')
assert sha(ROOT / 'tasks/tasks.json') == '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570'
assert not (ROOT / 'tasks/queue/gates/v0.3-frozen.json').exists()
assert not subprocess.check_output(['git', 'tag', '--list', 'v0.3-frozen'], cwd=ROOT, creationflags=0x08000000).strip()
OUT.mkdir(parents=True, exist_ok=False)
copied = {}
def copy(source, relative):
    target = OUT / relative
    target.parent.mkdir(parents=True, exist_ok=True)
    with target.open('xb') as stream:
        stream.write(source.read_bytes())
    assert sha(target) == sha(source)
    copied[str(relative)] = sha(target)

for name in ['wo-s1-voice-poc-20261021T041728559262Z', 'wo-s1-task-text-loop-20261021T042417690879Z', run.name]:
    directory = ROOT / 'tasks/queue/runs' / name
    for part in ['done.json', 'final.json', 'session.json']:
        copy(directory / part, Path('runs') / name / part)
copy(ROOT / 'logs/voice-existing-audio-replay-20261021/result.json', Path('offline-audio-result.json'))
copy(ROOT / 'logs/voice-dispatch-preflight-20261021/result.json', Path('dispatch-preflight-result.json'))
copy(ROOT / 'tasks/queue/runs/wo-s1-voice-poc-20261021T041728559262Z/phase-review.json', Path('dispatch-preflight-review.json'))
repair = ROOT / 'logs/text-loop-w4-repair-20261021'
for source in sorted(repair.rglob('*')):
    if source.is_file():
        assert source.resolve().is_relative_to(repair.resolve())
        copy(source, Path('repair') / source.relative_to(repair))
for card in ['s1-task-intent-parse', 's1-task-queue-source', 's1-task-aggregate-report']:
    for filename in ['task.md', 'completion.md', 'landed-files.md', 'acceptance-evidence.md']:
        path = ROOT / 'tasks/cards' / card / filename
        with path.open('a', encoding='utf-8', newline='\n') as stream:
            stream.write('\n\n## W4 独立技术验收收口（2026-10-21）\n\n'
                '两项独立发现修正后通过：文本16/16、原独立检查49/49、额外正例95%；'
                '以 docs/reports/evidence/w4-independent-20261021/round2-correction/result-final.json 为最终裁决。'
                '本卡对应执行单元已独立验收；前文开发/修复待审记录作为历史保留。'
                'Owner尚未批准v0.3版本冻结，无v0.3-frozen；不启动后续工单。\n')
order = ROOT / 'tasks/queue/wo-s1-task-text-loop.md'
text = order.read_text(encoding='utf-8')
for value in ['全部 3 任务 PASS（T1-T3）', 'T↔U 映射核对：U12-U14 全部覆盖',
              '场景实测：20 任务 1 失败→只报异常并总结 PASS', '关联文档同步（docs/README 登记工单④）',
              '前置：v0.1 冻结（队列引擎可用）', '每任务回执三件套（I1）',
              '提交前自核闭环（§8）', '失败回执结构化（I3）；证据不明确 fail-closed（B1）', '开发与审计技能分离']:
    assert '- [ ] ' + value in text
    text = text.replace('- [ ] ' + value, '- [x] ' + value)
text = text.replace('语音链路（v0.2 已完）', '语音链路（独立工单③，Owner选择仅已有音频离线验证，真机门仍待完成）')
text += '\n## 2026-10-21 W4内部收口\n\nU12-U14及10个执行单元技术验收通过，证据见docs/reports/w4-text-loop-acceptance-20261021.md。版本标签项保持未勾选；Owner批准v0.3冻结前，工单⑤不得启动。\n'
order.write_text(text, encoding='utf-8')
for filename in ['tasks/queue/EXECUTION.md', 'tasks/queue/stage1-unit-queue.md']:
    path = ROOT / filename
    text = path.read_text(encoding='utf-8')
    text = text.replace('首轮开发退出0、进入独立W4审核，尚未批准v0.3冻结', '开发及修复均真实退出0，独立W4纠正核对通过，尚未批准v0.3冻结')
    text = text.replace('首轮开发退出0、待独立W4验收及Owner版本审批', '开发及修复均真实退出0，W4技术验收通过、待Owner版本审批')
    path.write_text(text, encoding='utf-8')
readme = ROOT / 'docs/README.md'
text = readme.read_text(encoding='utf-8')
text = text.replace('15 个顶层文件（2026-10-21复核；evidence子目录另计）',
                    f'{len(list((ROOT / "docs/reports").glob("*.md"))) + 1} 个顶层Markdown文件（含本轮冻结申请；evidence子目录另计）')
readme.write_text(text, encoding='utf-8')
result = {'at': datetime.now(timezone.utc).isoformat(), 'w4_technical_verdict': 'PASS',
    'review_final': str((review_dir / 'result-final.json').relative_to(ROOT)),
    'review_final_sha256': sha(review_dir / 'result-final.json'),
    'source-manifest': review['source-manifest'], 'v01_source_items_unchanged': len(v01),
    'sealed_evidence_valid': seals, 'old_dispatch_exit125_preserved': sha(old),
    'production_tasks_unchanged': True, 'owner_v03_approval': False, 'v03_freeze_created': False,
    'downstream_launched': False, 'copied_evidence': copied}
with (OUT / 'precommit-readback.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print(json.dumps({'w4': 'PASS', 'copied_files': len(copied), 'package': str(OUT)}, ensure_ascii=False))
