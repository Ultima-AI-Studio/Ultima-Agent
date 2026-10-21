"""Refresh the project display from the register while preserving approved freezes."""
from datetime import datetime, timezone
import importlib.util
import json
from pathlib import Path
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.card_contract import check_version_gates
SHARED = ROOT.parent / '_shared/queue'
spec = importlib.util.spec_from_file_location('register', SHARED / 'queue-status-gen.py')
register = importlib.util.module_from_spec(spec)
spec.loader.exec_module(register)
check_version_gates({'card_path': str(ROOT / 'tasks/cards/s1-task-intent-parse/task.md')}, ROOT / 'tasks')
register_before = (SHARED / 'global-queue-index.md').read_bytes()
rows = [r for r in register.read_items() if r['project'] == 'UltimaAgent']
assert len(rows) == len({r['id'] for r in rows}) == 10
labels = {'frozen': '已完成', 'pending': '待派发', 'executing': '执行中', 'audit': '待审核', 'blocked': '阻塞'}
target = ROOT / 'sync/product.json'
original = target.read_bytes()
data = json.loads(original.decode('utf-8-sig'))
v01 = data.get('version_freezes', {}).get('v0.1', data['version_freeze'])
assert v01['baseline_commit'] == '43ce13021f16f191bb36615ebb6c68465bf201fa'
orders = [{'id': r['id'], 'title': r['id'], 'status': labels[r['state']],
           'acceptance': '已审计闭环' if r['state'] == 'frozen' else '未验收',
           'note': r['reason'], 'audit_ref': '_shared/queue/global-queue-index.md'} for r in rows]
text_state = next(r['state'] for r in rows if r['id'] == 'wo-s1-task-text-loop')
stage = '阶段一 v0.1 已冻结；v0.3 文本闭环' + labels[text_state] + '；v0.2 仅已有音频离线复验'
if text_state == 'frozen':
    stage = '阶段一 v0.1 已冻结；v0.3 文本闭环W4通过、版本待Owner审批；v0.2 仅已有音频离线复验'
if (ROOT / 'tasks/queue/gates/v0.3-frozen.json').is_file():
    check_version_gates({'card_path': str(ROOT / 'tasks/cards/s1-window-dsl-schema/task.md')}, ROOT / 'tasks')
    stage = '阶段一 v0.1/v0.3 已冻结；v0.4待语音四IO依赖就绪；v0.2仅已有音频离线复验'
if data.get('work_orders') == orders and data.get('stage') == stage:
    print('UNCHANGED')
    raise SystemExit(0)
stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
out = ROOT / 'logs/supervised-state-sync' / stamp
out.mkdir(parents=True, exist_ok=False)
(out / 'product.before.json').write_bytes(original)
data.setdefault('historical_work_order_snapshots', []).append({'recorded_at': data.get('updated_at'), 'work_orders': data.get('work_orders', [])})
data.update(stage=stage, work_orders=orders, updated_at=datetime.now(timezone.utc).isoformat())
data['summary']['blocker'] = '；'.join(r['id'] + '：' + labels[r['state']] + '（' + r['reason'] + '）' for r in rows if r['state'] != 'frozen')
data['summary']['progress_basis'] = 'progress/score为历史值，不作本轮完成率凭据；实际以逐单证据和Owner冻结门为准'
assert target.read_bytes() == original and (SHARED / 'global-queue-index.md').read_bytes() == register_before
temp = target.with_name('product.supervised.tmp')
temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
temp.replace(target)
assert json.loads(target.read_text(encoding='utf-8')) == data
(out / 'receipt.json').write_text(json.dumps({'stage': stage, 'orders': len(orders), 'readback': True}, ensure_ascii=False, indent=2), encoding='utf-8')
print(json.dumps({'stage': stage, 'receipt': str(out / 'receipt.json')}, ensure_ascii=False))
