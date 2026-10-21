"""Close the accepted engineering order; submit a separate pending Owner freeze."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.dispatcher import DispatchLock
from tasks.queue_engine.card_contract import check_version_gates
spec = importlib.util.spec_from_file_location('adapter', ROOT / 'scripts/dispatch-work-order.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
OUT = ROOT / 'docs/reports/evidence/text-loop-closeout-20261021'
review_path = ROOT / 'docs/reports/evidence/w4-independent-20261021/round2-correction/result-final.json'
review = json.loads(review_path.read_text(encoding='utf-8'))
assert review['verdict'] == 'PASS'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
def git(*args):
    return subprocess.check_output(['git', *args], cwd=ROOT, creationflags=0x08000000).decode('utf-8').strip()
candidate = git('rev-parse', 'HEAD')
assert candidate.startswith('731710a')
for relative, expected in review['source-manifest'].items():
    assert sha(ROOT / relative) == expected
    blob = subprocess.check_output(['git', 'show', candidate + ':' + relative], cwd=ROOT, creationflags=0x08000000)
    assert hashlib.sha256(blob).hexdigest() == expected
check_version_gates({'card_path': str(ROOT / 'tasks/cards/s1-task-intent-parse/task.md')}, ROOT / 'tasks')
assert not git('tag', '--list', 'v0.3-frozen')
assert not (ROOT / 'tasks/queue/gates/v0.3-frozen.json').exists()
with DispatchLock(adapter.SHARED / '.engineering-dispatch.lock'):
    processes = adapter.native.codex_processes()
    assert not any(p['role'] in {'exec', 'unknown'} and (not p['project'] or Path(p['project']).resolve() == ROOT) for p in processes)
    _, match, _ = adapter.registered('wo-s1-task-text-loop')
    assert match.group(1) == 'audit' and 'wo-s1-task-text-loop-20261021T044748126206Z' in match.group(2)
    assert not git('tag', '--list', 'wo-s1-task-text-loop-done')
    git('tag', 'wo-s1-task-text-loop-done', candidate)
    assert git('rev-parse', 'wo-s1-task-text-loop-done') == candidate
    adapter.state('wo-s1-task-text-loop', 'frozen',
        f'W4内部技术验收通过，内部tag wo-s1-task-text-loop-done={candidate[:7]}；v0.3版本冻结待Owner批准，工单⑤仍未解锁；独立49/49、文本16/16、CLI额外窗口0',
        OUT, expected='audit', expected_run='wo-s1-task-text-loop-20261021T044748126206Z')
subprocess.run([sys.executable, str(ROOT / 'scripts/sync-supervised-development-state.py')], cwd=ROOT, check=True,
               capture_output=True, creationflags=0x08000000)
projection = ROOT / 'sync/product.json'
data = json.loads(projection.read_text(encoding='utf-8'))
data['pending_version_freeze'] = {'version': 'v0.3', 'state': '待Owner批准',
    'baseline_commit': candidate, 'internal_tag': 'wo-s1-task-text-loop-done',
    'request': 'docs/reports/v03-freeze-approval-request-20261021.md'}
projection.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
request = ROOT / 'docs/reports/v03-freeze-approval-request-20261021.md'
with request.open('x', encoding='utf-8', newline='\n') as stream:
    stream.write(f'''# v0.3文本闭环冻结审批申请

**待Owner批准；尚未创建v0.3-frozen或Owner通过凭据。**

申请冻结候选提交：`{candidate}`。内部工单标签 `wo-s1-task-text-loop-done` 指向同一提交，仅表示W4技术验收通过。

范围为工单④的U12-U14、10个执行单元：任务查询窄规则、真实产品任务库八态只读状态源、异常优先聚合、明确ID下钻与文字CLI。生产任务库仍为空；20项19完成1失败场景由隔离真实库合法迁移验证。

独立纠正最终裁决：`evidence/w4-independent-20261021/round2-correction/result-final.json`，文本16/16、独立检查49/49、额外正例19/20=95%；三类CLI实际窗口事件与枚举观测额外可见窗口0。两项首轮问题及先失败后通过证据均保留；协调端又复跑16项文本测试通过。

技术收口报告：`w4-text-loop-acceptance-20261021.md`。完整本地接入回执和修复证据：`evidence/text-loop-closeout-20261021/`。实际源码与测试10文件的SHA256在最终独立裁决source-manifest中，并与候选提交Git对象逐项比对。

既有v0.1保持43ce130，36项冻结源码及生产tasks.json哈希未变。旧宿主退出125回执与旧引擎首次61/62失败日志原样保留；旧引擎随后完整及独立62/62通过，但首次失败根因未唯一判定，本申请不宣称根治该旧执行路径问题。

语音仅已有合成文件离线识别复验，未播放、未录音、未采集麦克风，不包含完整语音工单/W3或v0.2验收；组合窗口、语音汇报、队列调整、安装包与远程发布均不在本次冻结范围。

Owner如批准此候选，才创建v0.3-frozen及包含实际批准原文、候选提交和证据哈希的Owner回执。批准后工单⑤方可进入派发前检查；本轮没有启动工单⑤，没有远程发布。
''')
order = (ROOT / 'tasks/queue/wo-s1-task-text-loop.md').read_text(encoding='utf-8')
assert '- [ ] 冻结基线标记：tag `v0.3-frozen`' in order
assert all('W4 独立技术验收收口' in (ROOT / 'tasks/cards' / card / file).read_text(encoding='utf-8')
    for card in ['s1-task-intent-parse', 's1-task-queue-source', 's1-task-aggregate-report']
    for file in ['task.md', 'completion.md', 'landed-files.md', 'acceptance-evidence.md'])
assert json.loads(projection.read_text(encoding='utf-8'))['pending_version_freeze']['baseline_commit'] == candidate
assert not git('tag', '--list', 'v0.3-frozen')
result = {'at': datetime.now(timezone.utc).isoformat(), 'w4_internal_order': 'CLOSED',
    'baseline_commit': candidate, 'internal_tag': 'wo-s1-task-text-loop-done',
    'source_git_blobs_match_independent_manifest': 10, 'owner_v03': 'AWAITING_APPROVAL',
    'v03_tag_absent': True, 'v03_owner_receipt_absent': True, 'version_checkbox_remains_open': True,
    'cards_12_files_closed': True, 'global_order_state': 'frozen (internal order only)',
    'project_projection_readback': True, 'request_sha256': sha(request), 'review_final_sha256': sha(review_path),
    'no_active_project_exec': True, 'downstream_started': False, 'remote_release': False}
with (OUT / 'administrative-readback.json').open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False))
