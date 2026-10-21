"""Supervisory phase review: validate short dispatch, then defer voice per Owner."""
from datetime import datetime, timezone
import hashlib
import importlib.util
import json
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.dispatcher import DispatchLock, process_identity
from tasks.queue_engine.card_contract import check_version_gates
spec = importlib.util.spec_from_file_location('dispatch_adapter', ROOT / 'scripts/dispatch-work-order.py')
adapter = importlib.util.module_from_spec(spec)
spec.loader.exec_module(adapter)
run = ROOT / 'tasks/queue/runs/wo-s1-voice-poc-20261021T041728559262Z'
done = json.loads((run / 'done.json').read_text())
session = json.loads((run / 'session.json').read_text())
final = json.loads((run / 'final.json').read_text(encoding='utf-8'))
phase = json.loads((ROOT / 'logs/voice-dispatch-preflight-20261021/result.json').read_text(encoding='utf-8'))
assert done['exit_code'] == 0 and done['receipt_valid'] and not done['parent_lost']
assert process_identity(session['pid']) != session['identity']
assert final['status'] == 'READY_FOR_REVIEW' and not final['scope_violation']
assert phase['voice_t1_t2_completed'] is False and phase['audio_recording_executed'] is False and phase['audio_playback_executed'] is False
manifest = json.loads((ROOT / 'docs/reports/evidence/v01-freeze-20261021/source-manifest.json').read_text(encoding='utf-8'))
assert all(hashlib.sha256(Path(p).read_bytes()).hexdigest() == h for p, h in manifest.items())
check_version_gates({'card_path': str(ROOT / 'tasks/cards/s1-task-intent-parse/task.md')}, ROOT / 'tasks')
assert json.loads((ROOT / 'tasks/tasks.json').read_text(encoding='utf-8-sig')) == []
review = {'at': datetime.now(timezone.utc).isoformat(), 'phase_verdict': 'PASS',
          'actual_codex_exit': 0, 'worker_identity_gone': True,
          'frozen_source_hashes_unchanged': len(manifest), 'production_task_count': 0,
          'voice_order_completed': False, 'voice_owner_direction': '仅已有音频离线验证；继续文本闭环；不播放、不录音',
          'next_order': 'wo-s1-task-text-loop'}
with DispatchLock(adapter.SHARED / '.engineering-dispatch.lock'):
    with (run / 'phase-review.json').open('x', encoding='utf-8') as stream:
        json.dump(review, stream, ensure_ascii=False, indent=2)
    adapter.state('wo-s1-voice-poc', 'pending',
        'Owner选择仅已有音频离线验证、继续文本闭环；短派发真实exit0已复核；语音实现/真机/W3未完成；' + run.name,
        run, expected='audit', expected_run=run.name)
print(json.dumps(review, ensure_ascii=False))
