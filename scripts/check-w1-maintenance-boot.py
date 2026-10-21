"""Read-only boot comparison; a successful shutdown request is not restart proof."""
from datetime import datetime, timezone, timedelta
import ctypes
import hashlib
import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
evidence = ROOT / 'logs/maintenance/w1-restart-20261021'
before = json.loads((evidence / 'before.json').read_text(encoding='utf-8'))
kernel = ctypes.WinDLL('kernel32', use_last_error=True)
kernel.GetTickCount64.restype = ctypes.c_ulonglong
uptime = kernel.GetTickCount64()
now = datetime.now(timezone.utc)
boot = now - timedelta(milliseconds=uptime)
old_boot = datetime.fromisoformat(before['boot_time_estimate_utc'])
markers = []
for marker in before['dispatch_markers']:
    path = Path(marker['path'])
    markers.append({'path': str(path), 'exists': path.is_file(),
                    'unchanged': path.is_file() and hashlib.sha256(path.read_bytes()).hexdigest() == marker['sha256']})
result = {'at_utc': now.isoformat(), 'uptime_ms': uptime, 'boot_time_estimate_utc': boot.isoformat(),
          'previous_boot_estimate_utc': old_boot.isoformat(), 'boot_difference_seconds': (boot-old_boot).total_seconds(),
          'restart_verified': (boot-old_boot).total_seconds() > 30, 'markers': markers}
target = evidence / ('boot-check-' + now.strftime('%Y%m%dT%H%M%S%fZ') + '.json')
target.write_text(json.dumps(result, indent=2), encoding='utf-8')
print(json.dumps(result))
