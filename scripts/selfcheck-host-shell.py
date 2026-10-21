"""Delivered one-command host selfcheck, independent of a PowerShell startup."""
import argparse
import ctypes
from ctypes import wintypes as W
from datetime import datetime, timezone
import hashlib
import json
import os
from pathlib import Path
import subprocess
import sys

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from tasks.queue_engine.windows_runtime import WindowMonitor

DOTNET = Path(r'C:\Users\Administrator\.dotnet\dotnet.exe')

class EnrichedWindows(list):
    def __init__(self):
        super().__init__()
        self.seen = set()
        self.user = ctypes.WinDLL('user32', use_last_error=True)
        self.user.GetWindowRect.argtypes = [W.HWND, ctypes.POINTER(W.RECT)]
        self.kernel = ctypes.WinDLL('kernel32', use_last_error=True)
        self.kernel.OpenProcess.argtypes = [W.DWORD, W.BOOL, W.DWORD]
        self.kernel.OpenProcess.restype = W.HANDLE
        self.kernel.QueryFullProcessImageNameW.argtypes = [W.HANDLE, W.DWORD, W.LPWSTR, ctypes.POINTER(W.DWORD)]
        self.kernel.CloseHandle.argtypes = [W.HANDLE]

    def append(self, item):
        rect = W.RECT()
        if not self.user.GetWindowRect(item['hwnd'], ctypes.byref(rect)):
            item['metadata_error'] = 'Window disappeared before geometry readback'
        else:
            item['rect'] = [rect.left, rect.top, rect.right, rect.bottom]
        handle = self.kernel.OpenProcess(0x1000, False, item['pid'])
        if handle:
            try:
                size = W.DWORD(32768)
                name = ctypes.create_unicode_buffer(size.value)
                if self.kernel.QueryFullProcessImageNameW(handle, 0, name, ctypes.byref(size)):
                    item['process_name'] = Path(name.value).name.lower()
            finally:
                self.kernel.CloseHandle(handle)
        key = (item['pid'], item['hwnd'], item['source'], tuple(item.get('rect', [])))
        if key not in self.seen:
            self.seen.add(key)
            super().append(item)

def sha(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()

def contained(rect, outer):
    return rect[0] >= outer['Left'] and rect[1] >= outer['Top'] and rect[2] <= outer['Right'] and rect[3] <= outer['Bottom']

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--evidence', type=Path)
    parser.add_argument('--missing-runtime', action='store_true', help='Negative check: child-local nonexistent WebView2 runtime directory')
    args = parser.parse_args()
    evidence = args.evidence or ROOT / 'logs' / ('selfcheck-host-shell-' + datetime.now(timezone.utc).strftime('%Y%m%dT%H%M%S%fZ'))
    evidence = evidence.resolve()
    evidence.mkdir(parents=True, exist_ok=False)
    project = ROOT / 'scripts/HostSelfcheck/HostSelfcheck.csproj'
    host_root = ROOT / 'src/host-shell/UltimaAgent.HostShell'
    source_files = [Path(__file__), *project.parent.glob('*.cs'), project]
    source_files += [path for path in host_root.rglob('*') if path.is_file() and not {'bin', 'obj'} & set(path.relative_to(host_root).parts)]
    source_before = {str(path): sha(path) for path in source_files}
    (evidence / 'source-before.json').write_text(json.dumps(source_before, indent=2), encoding='utf-8')
    env = dict(os.environ, DOTNET_CLI_UI_LANGUAGE='en-US', DOTNET_CLI_TELEMETRY_OPTOUT='1')
    if args.missing_runtime:
        missing_runtime = evidence / 'intentionally-absent-webview2-runtime'
        assert not missing_runtime.exists()
        env['WEBVIEW2_BROWSER_EXECUTABLE_FOLDER'] = str(missing_runtime)
    monitor = WindowMonitor(os.getpid())
    monitor.observations = EnrichedWindows()
    error = None
    code = 1
    audit = {'method': 'WinEvent CREATE..SHOW plus process-tree window enumeration', 'observed_pids': [], 'samples': 0, 'visible_windows': []}
    try:
        monitor.start()
        with (evidence / 'selfcheck-tool-build.log').open('wb') as output:
            build = subprocess.run([str(DOTNET), 'build', str(project), '-c', 'Release', '-v', 'minimal',
                                    '-p:UseSharedCompilation=false'], cwd=ROOT, env=env,
                                   stdout=output, stderr=subprocess.STDOUT, timeout=120, creationflags=0x08000000)
        if build.returncode:
            raise RuntimeError('Selfcheck tool build failed; see selfcheck-tool-build.log')
        tool = project.parent / 'bin/Release/net8.0-windows10.0.19041.0/HostSelfcheck.dll'
        with (evidence / 'selfcheck.stdout.log').open('wb') as out, (evidence / 'selfcheck.stderr.log').open('wb') as err:
            result = subprocess.run([str(DOTNET), str(tool), str(ROOT), str(evidence)], cwd=ROOT, env=env,
                                    stdout=out, stderr=err, timeout=180, creationflags=0x08000000)
        code = result.returncode
    except Exception as exc:
        error = f'{type(exc).__name__}: {exc}'
    finally:
        if hasattr(monitor, 'thread'):
            try:
                audit = monitor.stop()
            except Exception as exc:
                error = (error + '; ' if error else '') + f'Monitor failure: {type(exc).__name__}: {exc}'
                audit = {'method': 'WinEvent CREATE..SHOW plus process-tree window enumeration',
                         'observed_pids': sorted(monitor.pids), 'samples': monitor.samples,
                         'visible_windows': list(monitor.observations), 'error': str(exc)}
    probe_path = evidence / 'result.json'
    probe = json.loads(probe_path.read_text(encoding='utf-8')) if probe_path.exists() else {}
    host = probe.get('chain', {}).get('launch', {}).get('processId')
    hwnd = probe.get('chain', {}).get('window', {}).get('mainWindowHandle')
    native = probe.get('zeroExtraWindows', {})
    owned = native.get('allRunOwnedWindows', [])
    render_pids = {row['ProcessId'] for row in owned if row['ProcessName'].lower() == 'msedgewebview2'
                   and host in row.get('AncestorProcessIds', [])}
    rects = native.get('hostRectHistory', [])
    unexpected = []
    for row in audit['visible_windows']:
        main = row['pid'] == host and row['hwnd'] == hwnd
        surface = (row['pid'] in render_pids and row.get('process_name') == 'msedgewebview2.exe'
                   and row.get('rect') and any(contained(row['rect'], outer) for outer in rects))
        if not (main or surface):
            unexpected.append(row)
    source_after = {str(path): sha(path) for path in source_files}
    artifacts = [path for path in (host_root / 'bin/Release/net8.0-windows10.0.19041.0/win-x64').glob('UltimaAgent.HostShell.*') if path.is_file()]
    passed = code == 0 and probe.get('status') == 'PASS' and not error and not unexpected and source_after == source_before
    final = {'status': 'PASS' if passed else 'FAIL', 'exit_code': 0 if passed else 1,
             'entry': str(Path(__file__).resolve()), 'probe_exit_code': code, 'error': error,
             'probe_result': str(probe_path), 'window_audit': audit, 'unexpected_windows': unexpected,
             'source_manifest': source_after, 'sources_unchanged_during_build_and_run': source_after == source_before,
             'artifact_manifest': {str(path): sha(path) for path in artifacts},
             'owner_freeze_approved': False}
    (evidence / 'entry-result.json').write_text(json.dumps(final, ensure_ascii=False, indent=2), encoding='utf-8')
    report = evidence / 'report.md'
    with report.open('a', encoding='utf-8') as stream:
        stream.write(f'\n正式scripts入口复核：{final["status"]}；WinEvent与枚举样本{audit["samples"]}，额外窗口{len(unexpected)}。源码与产物哈希见entry-result.json。\n')
    (ROOT / 'logs' / f'selfcheck-host-shell-{evidence.name}.md').write_text(report.read_text(encoding='utf-8'), encoding='utf-8')
    print(json.dumps({'status': final['status'], 'evidence': str(evidence), 'unexpected_windows': len(unexpected), 'error': error}, ensure_ascii=False))
    return final['exit_code']

if __name__ == '__main__':
    raise SystemExit(main())
