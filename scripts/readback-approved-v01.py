"""Read back the real freeze and update only its project display metadata."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.card_contract import check_version_gates

def main():
    package = ROOT / 'docs/reports/evidence/v01-freeze-20261021'
    approval_path = ROOT / 'tasks/queue/gates/v0.1-frozen.json'
    approval = json.loads(approval_path.read_text(encoding='utf-8'))
    actual = subprocess.check_output(['git', '-C', str(ROOT), 'rev-parse', 'v0.1-frozen^{}'], creationflags=0x08000000).decode().strip()
    assert actual == approval['baseline_commit'] == '43ce13021f16f191bb36615ebb6c68465bf201fa'
    assert approval['approved_by'] == 'owner' and approval['decision'] == 'PASS'
    for item in approval['evidence']:
        assert hashlib.sha256((ROOT / item['path']).read_bytes()).hexdigest() == item['sha256']
    for card in ['s1-voice-cv3-wiring', 's1-task-intent-parse']:
        check_version_gates({'card_path': str(ROOT / 'tasks/cards' / card / 'task.md')}, ROOT / 'tasks')
    projection = ROOT / 'sync/product.json'
    original = projection.read_bytes()
    (package / 'product.before-freeze-stage.json').write_bytes(original)
    data = json.loads(original.decode('utf-8-sig'))
    data['stage'] = '阶段一 v0.1 已冻结；v0.2/v0.3 待派发'
    data['version_freeze'] = {'version': 'v0.1', 'state': '已冻结', 'tag': 'v0.1-frozen',
                              'baseline_commit': actual, 'approval': 'tasks/queue/gates/v0.1-frozen.json'}
    data['updated_at'] = datetime.now(timezone.utc).isoformat()
    assert projection.read_bytes() == original
    temp = projection.with_name('product.freeze-update.tmp')
    temp.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
    temp.replace(projection)
    assert json.loads(projection.read_text(encoding='utf-8')) == data
    result = {'at': data['updated_at'], 'gate': 'PASS', 'tag_commit': actual, 'evidence_hashes_valid': True,
              'v02_v03_gate_checks': 'PASS', 'projection_readback': True,
              'source_code_changed_by_freeze': False, 'downstream_launched': False}
    with (package / 'final-readback.json').open('x', encoding='utf-8') as stream:
        json.dump(result, stream, indent=2)
    print(json.dumps(result))

if __name__ == '__main__':
    main()
