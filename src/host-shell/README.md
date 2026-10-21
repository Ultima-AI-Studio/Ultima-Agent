# UltimaAgent Host Shell

Windows 11 thin host implemented with WinUI 3 / .NET 8. The project owns terminal IO, rendering and protocol integration only; it contains no intent, orchestration, memory or model inference logic.

Build from the repository root:

```powershell
& scripts\host-shell-toolchain.ps1 -Tool dotnet -ToolArguments @(
  'build', 'src/host-shell/UltimaAgent.HostShell/UltimaAgent.HostShell.csproj',
  '-c', 'Release', '-r', 'win-x64'
)
```


## Prototype acceptance modes and limits

This work order produces a thin-host prototype, not a released product startup flow. Bare EXE launch displays the native placeholder. Formal acceptance modes use `ULTIMA_HOST_EVIDENCE_DIR` with a fresh directory and select `ULTIMA_HOST_WEBVIEW_TEST=1` or `ULTIMA_HOST_FLOATINGBALL_TEST=1`; `ULTIMA_HOST_AUTO_EXIT_MS` bounds unattended probes. These modes contain real WebView2 rendering and native-window behavior, not mocked UI. Normal product entry/voice-state binding belongs to later work.

Use the delivered `tools/python31313/python.exe -X utf8 scripts/selfcheck-host-shell.py` entry for build/launch/window/exit checks. It builds the C# tool in `scripts/HostSelfcheck`, observes the complete child process tree with WinEvent plus enumeration, and writes a fresh report, structured result, and source/artifact hashes under `logs/`. `--missing-runtime` runs a child-local negative check and must return FAIL/exit1. The original `.ps1` entry is retained as historical implementation; its PowerShell startup hung on this machine and is not the current recommended entry.

Real hardware acceptance now covers 144/96/96 DPI monitors, 270/180/180 physical pixels at 180 logical pixels, one-second holds and exact restoration. Final native window text/display and real mouse dragging were observed. Functional evidence does not close the whole order: a run-owned old PowerShell process remains unresolved, and final W1 administrative acceptance is pending. No version freeze or release is claimed.

For the hardware-only cross-DPI acceptance probe, set `ULTIMA_HOST_DPI_ACCEPTANCE=1` together with a fresh `ULTIMA_HOST_EVIDENCE_DIR`. This explicit mode moves the floating-ball `AppWindow` through the real display work areas, reads `GetDpiForWindow` and native window rectangles after layout stabilization, holds each placement for one second, and restores the original rectangle. It does not synthesize `WM_DPICHANGED` or change Windows display settings. The normal startup mode is unchanged.
