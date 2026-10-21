"""Reconcile project display with registered work orders, without claiming execution."""
import argparse
import hashlib
import importlib.util
import json
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SHARED = ROOT.parent / '_shared' / 'queue'


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--apply', action='store_true')
    args = parser.parse_args()
    spec = importlib.util.spec_from_file_location('queue_register', SHARED / 'queue-status-gen.py')
    register = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(register)
    rows = [row for row in register.read_items() if row['project'] == 'UltimaAgent']
    if len(rows) != 10 or len({row['id'] for row in rows}) != 10:
        raise ValueError('Expected ten distinct registered Agent orders; refusing partial reconciliation')
    target = ROOT / 'sync' / 'product.json'
    original = target.read_bytes()
    data = json.loads(original.decode('utf-8-sig'))
    labels = {'frozen': '已完成', 'pending': '待派发', 'executing': '执行中',
              'audit': '待审核', 'blocked': '阻塞'}
    orders = [{'id': row['id'], 'title': row['id'], 'status': labels[row['state']],
               'acceptance': '已审计闭环' if row['state'] == 'frozen' else '未验收',
               'note': row['reason'], 'audit_ref': '_shared/queue/global-queue-index.md'}
              for row in rows]
    if data.get('work_orders') == orders:
        print('UNCHANGED: registered work orders already reconciled')
        return
    stamp = datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ')
    backup = ROOT / 'logs' / 'state-reconciliation' / stamp
    backup.mkdir(parents=True, exist_ok=False)
    (backup / 'product.before.json').write_bytes(original)
    data.setdefault('historical_work_order_snapshots', []).append({
        'recorded_at': data.get('updated_at'), 'work_orders': data.get('work_orders', [])})
    data.update(stage='阶段一 v0.1 开发与验收', work_orders=orders,
                updated_at=datetime.now(timezone.utc).isoformat())
    summary = data.setdefault('summary', {})
    summary.update(deviation='有',
                   deviation_desc='历史待设计记录已与实际阶段一工单对齐；登记状态不等于实时执行状态。',
                   blocker='；'.join(f"{row['id']}：{labels[row['state']]}（{row['reason']}）"
                                    for row in rows if row['state'] != 'frozen')
                           or '登记工单均已闭环；版本冻结仍以实际Owner审批及tag为准。',
                   progress_basis='progress/score 为旧记录，未经本轮实测重算，不作完成率凭据')
    candidate = json.dumps(data, ensure_ascii=False, indent=2) + '\n'
    (backup / 'product.candidate.json').write_text(candidate, encoding='utf-8')
    if args.apply:
        if target.read_bytes() != original:
            raise RuntimeError('Concurrent project-state update; refusing overwrite')
        temporary = target.with_name('product.' + stamp + '.tmp')
        temporary.write_text(candidate, encoding='utf-8')
        temporary.replace(target)
        if json.loads(target.read_text(encoding='utf-8')) != data:
            raise RuntimeError('Independent readback mismatch')
    receipt = {'applied': args.apply, 'backup': str(backup), 'orders': len(orders),
               'before_sha256': hashlib.sha256(original).hexdigest(),
               'after_sha256': hashlib.sha256(target.read_bytes()).hexdigest()}
    (backup / 'receipt.json').write_text(json.dumps(receipt, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(receipt, ensure_ascii=False))


if __name__ == '__main__':
    main()
