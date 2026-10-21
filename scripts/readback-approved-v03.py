"""Read back the approved freeze and finish its project metadata index."""
from datetime import datetime, timezone
import hashlib
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.card_contract import check_version_gates
BASE = '731710a80358b062d1064ccaf08f758483a9d958'
sha = lambda p: hashlib.sha256(p.read_bytes()).hexdigest()
gate = ROOT / 'tasks/queue/gates/v0.3-frozen.json'
approval = json.loads(gate.read_text(encoding='utf-8'))
assert approval['decision'] == 'PASS' and approval['approved_by'] == 'owner' and approval['authorization_text'] == '批准'
actual = subprocess.check_output(['git', 'rev-parse', 'v0.3-frozen^{}'], cwd=ROOT, creationflags=0x08000000).decode().strip()
assert actual == approval['baseline_commit'] == BASE
assert all(sha(ROOT / item['path']) == item['sha256'] for item in approval['evidence'])
manifest = json.loads((ROOT / 'docs/reports/evidence/v03-freeze-20261021/source-manifest.json').read_text(encoding='utf-8'))
assert len(manifest) == 10 and all(sha(ROOT / p) == h for p,h in manifest.items())
v01 = json.loads((ROOT / 'docs/reports/evidence/v01-freeze-20261021/source-manifest.json').read_text(encoding='utf-8'))
assert len(v01) == 36 and all(sha(Path(p)) == h for p,h in v01.items())
assert sha(ROOT / 'tasks/tasks.json') == '37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570'
for card in ['s1-window-dsl-schema', 's1-window-composite-render', 's1-window-theme-floatball']:
    check_version_gates({'card_path': str(ROOT / 'tasks/cards' / card / 'task.md')}, ROOT / 'tasks')
projection = ROOT / 'sync/product.json'
data = json.loads(projection.read_text(encoding='utf-8'))
assert data['version'] == '0.3.0' and data['version_freeze']['baseline_commit'] == BASE
assert data['version_freezes']['v0.1']['baseline_commit'] == '43ce13021f16f191bb36615ebb6c68465bf201fa'
assert 'pending_version_freeze' not in data and 'v0.1/v0.3 已冻结' in data['stage']
assert '- [x] 冻结基线标记：tag `v0.3-frozen`' in (ROOT / 'tasks/queue/wo-s1-task-text-loop.md').read_text(encoding='utf-8')
assert not (ROOT / 'tasks/queue/gates/v0.2-frozen.json').exists()
preflight = json.loads((ROOT / 'docs/reports/evidence/v03-freeze-20261021/v04-dispatch-preflight.json').read_text(encoding='utf-8'))
assert preflight['version_gate'] == 'PASS' and not preflight['full_order_ready'] and not preflight['dispatched']
# Keep the established LF JSON style; only serialization bytes change.
projection.write_text(json.dumps(data, ensure_ascii=False, indent=2) + '\n', encoding='utf-8', newline='\n')
assert json.loads(projection.read_text(encoding='utf-8')) == data
index = ROOT / 'docs/文档库索引.md'
marker = '## 2026-10-21 v0.3冻结确认'
original = index.read_text(encoding='utf-8')
assert marker not in original
with index.open('a', encoding='utf-8') as stream:
    stream.write('\n' + marker + '\n\nOwner已明确批准文本闭环候选731710a。实际v0.3-frozen固定731710a80358b062d1064ccaf08f758483a9d958；批准凭据tasks/queue/gates/v0.3-frozen.json；报告docs/reports/v03-freeze-approval-request-20261021.md。v0.4版本门通过，整单仍待s1-voice-four-io；不播放、不录音、未派发窗口整单。\n')
result = {'at': datetime.now(timezone.utc).isoformat(), 'gate': 'PASS', 'tag_commit': actual,
    'approval_sha256': sha(gate), 'approval_evidence_hashes_valid': True,
    'accepted_source_items_unchanged': len(manifest), 'v01_items_unchanged': len(v01),
    'production_tasks_unchanged': True, 'project_projection_readback': True,
    'v04_version_gate': 'PASS', 'v04_full_order_ready': False, 'downstream_launched': False,
    'voice_v02_pass_claimed': False, 'audio_played_or_recorded': False}
out = ROOT / 'docs/reports/evidence/v03-freeze-20261021/final-readback.json'
with out.open('x', encoding='utf-8') as stream:
    json.dump(result, stream, ensure_ascii=False, indent=2)
print(json.dumps(result, ensure_ascii=False))
