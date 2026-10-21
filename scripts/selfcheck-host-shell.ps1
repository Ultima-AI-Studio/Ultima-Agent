[CmdletBinding()]
param(
    [string]$WorkspaceRoot = (Split-Path -Parent $PSScriptRoot),
    [string]$EvidenceDirectory = (Join-Path (Split-Path -Parent $PSScriptRoot) ('logs/selfcheck-host-shell-' + (Get-Date -Format 'yyyyMMddTHHmmssfff'))),
    [string]$ReportDate = (Get-Date -Format 'yyyy-MM-ddTHHmmssfff')
)

$ErrorActionPreference = 'Stop'
$ProgressPreference = 'SilentlyContinue'

Add-Type -TypeDefinition @'
using System;
using System.Collections.Concurrent;
using System.Collections.Generic;
using System.Diagnostics;
using System.Runtime.InteropServices;
using System.Text;
using System.Threading;

namespace UltimaHostSelfcheck
{
    public sealed class WindowObservation
    {
        public string Source { get; set; } = "";
        public uint EventType { get; set; }
        public long Handle { get; set; }
        public uint ProcessId { get; set; }
        public uint ParentProcessId { get; set; }
        public uint[] AncestorProcessIds { get; set; } = Array.Empty<uint>();
        public string ProcessName { get; set; } = "";
        public string ClassName { get; set; } = "";
        public int Left { get; set; }
        public int Top { get; set; }
        public int Right { get; set; }
        public int Bottom { get; set; }
        public DateTimeOffset ObservedAtUtc { get; set; }
    }

    public sealed class WindowMonitor : IDisposable
    {
        private const uint EventObjectCreate = 0x8000;
        private const uint EventObjectShow = 0x8002;
        private const uint WineventOutOfContext = 0;
        private const uint WmQuit = 0x0012;
        private const uint GaRoot = 2;
        private readonly ConcurrentQueue<WindowObservation> observations = new();
        private readonly ManualResetEventSlim ready = new(false);
        private readonly Thread thread;
        private WinEventDelegate callback;
        private uint threadId;

        public WindowMonitor()
        {
            callback = OnWinEvent;
            thread = new Thread(Run) { IsBackground = true, Name = "UltimaHostWindowMonitor" };
            thread.Start();
            if (!ready.Wait(TimeSpan.FromSeconds(5))) throw new TimeoutException("WinEvent monitor did not initialize.");
        }

        public WindowObservation[] GetEvents() => observations.ToArray();

        public static WindowObservation[] SnapshotVisibleTopLevel(string source)
        {
            List<WindowObservation> result = new();
            EnumWindows((window, state) =>
            {
                if (IsWindowVisible(window) && GetAncestor(window, GaRoot) == window)
                {
                    GetWindowThreadProcessId(window, out uint processId);
                    result.Add(NewObservation(source, 0, window, processId));
                }
                return true;
            }, IntPtr.Zero);
            return result.ToArray();
        }

        private void Run()
        {
            threadId = GetCurrentThreadId();
            PeekMessage(out _, IntPtr.Zero, 0, 0, 0);
            IntPtr hook = SetWinEventHook(EventObjectCreate, EventObjectShow, IntPtr.Zero, callback, 0, 0, WineventOutOfContext);
            if (hook == IntPtr.Zero)
            {
                ready.Set();
                return;
            }
            ready.Set();
            try
            {
                while (GetMessage(out Message message, IntPtr.Zero, 0, 0) > 0) { }
            }
            finally
            {
                UnhookWinEvent(hook);
            }
        }

        private void OnWinEvent(IntPtr hook, uint eventType, IntPtr window, int objectId, int childId, uint eventThread, uint eventTime)
        {
            if (window == IntPtr.Zero || objectId != 0 || !IsWindowVisible(window) || GetAncestor(window, GaRoot) != window) return;
            GetWindowThreadProcessId(window, out uint processId);
            observations.Enqueue(NewObservation("WinEvent", eventType, window, processId));
        }

        private static WindowObservation NewObservation(string source, uint eventType, IntPtr window, uint processId)
        {
            StringBuilder className = new(256);
            GetClassName(window, className, className.Capacity);
            GetWindowRect(window, out Rect rect);
            uint[] ancestors = GetProcessAncestors(processId);
            string processName = "";
            try { processName = Process.GetProcessById((int)processId).ProcessName; } catch { }
            return new WindowObservation
            {
                Source = source,
                EventType = eventType,
                Handle = window.ToInt64(),
                ProcessId = processId,
                ParentProcessId = ancestors.Length > 0 ? ancestors[0] : 0,
                AncestorProcessIds = ancestors,
                ProcessName = processName,
                ClassName = className.ToString(),
                Left = rect.Left,
                Top = rect.Top,
                Right = rect.Right,
                Bottom = rect.Bottom,
                ObservedAtUtc = DateTimeOffset.UtcNow
            };
        }

        private static uint[] GetProcessAncestors(uint processId)
        {
            Dictionary<uint, uint> parents = new();
            IntPtr snapshot = CreateToolhelp32Snapshot(0x00000002, 0);
            if (snapshot == new IntPtr(-1)) return Array.Empty<uint>();
            try
            {
                ProcessEntry entry = new() { Size = (uint)Marshal.SizeOf<ProcessEntry>() };
                if (Process32First(snapshot, ref entry))
                {
                    do { parents[entry.ProcessId] = entry.ParentProcessId; }
                    while (Process32Next(snapshot, ref entry));
                }
            }
            finally { CloseHandle(snapshot); }

            List<uint> result = new();
            uint current = processId;
            for (int depth = 0; depth < 16 && parents.TryGetValue(current, out uint parent) && parent != 0 && parent != current; depth++)
            {
                result.Add(parent);
                current = parent;
            }
            return result.ToArray();
        }

        public void Dispose()
        {
            if (threadId != 0) PostThreadMessage(threadId, WmQuit, IntPtr.Zero, IntPtr.Zero);
            thread.Join(TimeSpan.FromSeconds(5));
            ready.Dispose();
            GC.KeepAlive(callback);
        }

        private delegate void WinEventDelegate(IntPtr hook, uint eventType, IntPtr window, int objectId, int childId, uint eventThread, uint eventTime);
        private delegate bool EnumWindowsDelegate(IntPtr window, IntPtr state);
        [StructLayout(LayoutKind.Sequential)] private struct Point { public int X; public int Y; }
        [StructLayout(LayoutKind.Sequential)] private struct Rect { public int Left; public int Top; public int Right; public int Bottom; }
        [StructLayout(LayoutKind.Sequential)] private struct Message { public IntPtr Hwnd; public uint Value; public IntPtr WParam; public IntPtr LParam; public uint Time; public Point Pt; public uint Private; }
        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        private struct ProcessEntry
        {
            public uint Size; public uint Usage; public uint ProcessId; public IntPtr DefaultHeapId; public uint ModuleId;
            public uint Threads; public uint ParentProcessId; public int PriorityBase; public uint Flags;
            [MarshalAs(UnmanagedType.ByValTStr, SizeConst = 260)] public string ExeFile;
        }

        [DllImport("user32.dll")] private static extern IntPtr SetWinEventHook(uint min, uint max, IntPtr module, WinEventDelegate callback, uint process, uint thread, uint flags);
        [DllImport("user32.dll")] private static extern bool UnhookWinEvent(IntPtr hook);
        [DllImport("user32.dll")] private static extern int GetMessage(out Message message, IntPtr window, uint min, uint max);
        [DllImport("user32.dll")] private static extern bool PeekMessage(out Message message, IntPtr window, uint min, uint max, uint remove);
        [DllImport("user32.dll")] private static extern bool PostThreadMessage(uint thread, uint message, IntPtr wParam, IntPtr lParam);
        [DllImport("kernel32.dll")] private static extern uint GetCurrentThreadId();
        [DllImport("user32.dll")] private static extern bool EnumWindows(EnumWindowsDelegate callback, IntPtr state);
        [DllImport("user32.dll")] private static extern bool IsWindowVisible(IntPtr window);
        [DllImport("user32.dll")] private static extern IntPtr GetAncestor(IntPtr window, uint flags);
        [DllImport("user32.dll")] private static extern uint GetWindowThreadProcessId(IntPtr window, out uint processId);
        [DllImport("user32.dll", CharSet = CharSet.Unicode)] private static extern int GetClassName(IntPtr window, StringBuilder text, int count);
        [DllImport("user32.dll")] private static extern bool GetWindowRect(IntPtr window, out Rect rect);
        [DllImport("kernel32.dll")] private static extern IntPtr CreateToolhelp32Snapshot(uint flags, uint processId);
        [DllImport("kernel32.dll", CharSet = CharSet.Auto)] private static extern bool Process32First(IntPtr snapshot, ref ProcessEntry entry);
        [DllImport("kernel32.dll", CharSet = CharSet.Auto)] private static extern bool Process32Next(IntPtr snapshot, ref ProcessEntry entry);
        [DllImport("kernel32.dll")] private static extern bool CloseHandle(IntPtr handle);
    }
}
'@

function Get-DevelopmentProcessSnapshot {
    $pattern = '^(codex|codex-app-server|codex-exec-server|python|pythonw|node|dotnet|ollama|brain|watchdog)$'
    @(Get-Process -ErrorAction SilentlyContinue | Where-Object ProcessName -Match $pattern | ForEach-Object {
        try {
            [ordered]@{
                name = $_.ProcessName
                pid = $_.Id
                startTimeUtc = $_.StartTime.ToUniversalTime().ToString('o')
            }
        } catch { }
    } | Sort-Object name, pid)
}

function Add-VisibleSnapshot([System.Collections.Generic.List[object]]$Collection, [string]$Source) {
    foreach ($item in [UltimaHostSelfcheck.WindowMonitor]::SnapshotVisibleTopLevel($Source)) {
        $Collection.Add($item)
    }
}

function Invoke-HiddenBuild([string]$Dotnet, [string]$Project, [string]$LogPath, [System.Collections.Generic.List[object]]$Snapshots) {
    $info = [Diagnostics.ProcessStartInfo]::new($Dotnet)
    $info.UseShellExecute = $false
    $info.CreateNoWindow = $true
    $info.WindowStyle = [Diagnostics.ProcessWindowStyle]::Hidden
    $info.RedirectStandardOutput = $true
    $info.RedirectStandardError = $true
    foreach ($argument in @('build', $Project, '-c', 'Release', '-r', 'win-x64', '--no-restore', '-v', 'minimal')) {
        [void]$info.ArgumentList.Add($argument)
    }
    $info.WorkingDirectory = $WorkspaceRoot
    $process = [Diagnostics.Process]::Start($info)
    $stdoutTask = $process.StandardOutput.ReadToEndAsync()
    $stderrTask = $process.StandardError.ReadToEndAsync()
    $maxMainWindowHandle = 0
    while (-not $process.HasExited) {
        $process.Refresh()
        $maxMainWindowHandle = [Math]::Max($maxMainWindowHandle, $process.MainWindowHandle.ToInt64())
        Add-VisibleSnapshot $Snapshots 'build-poll'
        Start-Sleep -Milliseconds 25
    }
    $process.WaitForExit()
    $stdout = $stdoutTask.GetAwaiter().GetResult()
    $stderr = $stderrTask.GetAwaiter().GetResult()
    [IO.File]::WriteAllText($LogPath, $stdout + $stderr, [Text.UTF8Encoding]::new($false))
    [ordered]@{ exitCode = $process.ExitCode; processId = $process.Id; maxMainWindowHandle = $maxMainWindowHandle; stdout = $stdout; stderr = $stderr }
}

$WorkspaceRoot = (Resolve-Path -LiteralPath $WorkspaceRoot).Path
[void][IO.Directory]::CreateDirectory($EvidenceDirectory)
$EvidenceDirectory = (Resolve-Path -LiteralPath $EvidenceDirectory).Path
$project = Join-Path $WorkspaceRoot 'src/host-shell/UltimaAgent.HostShell/UltimaAgent.HostShell.csproj'
$dotnet = 'C:\Users\Administrator\.dotnet\dotnet.exe'
$exe = Join-Path $WorkspaceRoot 'src/host-shell/UltimaAgent.HostShell/bin/Release/net8.0-windows10.0.19041.0/win-x64/UltimaAgent.HostShell.exe'
$buildLog = Join-Path $EvidenceDirectory 't5-build.log'
$runtimePath = Join-Path $EvidenceDirectory 't5-runtime.json'
$windowEvidencePath = Join-Path $EvidenceDirectory 't5-floating-ball-ready.json'
$reportPath = Join-Path $WorkspaceRoot "logs/selfcheck-host-shell-$ReportDate.md"
$jsonPath = Join-Path $WorkspaceRoot "logs/selfcheck-host-shell-$ReportDate.json"
if ((Test-Path -LiteralPath $runtimePath) -or (Test-Path -LiteralPath $windowEvidencePath)) { throw 'Use a fresh evidence directory; previous runtime receipts must not be overwritten.' }
$startedAt = [DateTimeOffset]::UtcNow
$beforeProcesses = Get-DevelopmentProcessSnapshot
$baseline = [UltimaHostSelfcheck.WindowMonitor]::SnapshotVisibleTopLevel('baseline')
$baselineHandles = @{}; foreach ($window in $baseline) { $baselineHandles[[long]$window.Handle] = $true }
$snapshots = [System.Collections.Generic.List[object]]::new()
$monitor = [UltimaHostSelfcheck.WindowMonitor]::new()
$hostProcess = $null
$hostHandle = 0L
$hostExitCode = $null
$failure = $null

try {
    $build = Invoke-HiddenBuild $dotnet $project $buildLog $snapshots
    if ($build.exitCode -ne 0) { throw "Build failed with exit code $($build.exitCode)." }
    if (-not (Test-Path -LiteralPath $exe)) { throw "Host executable missing after build: $exe" }

    $launch = [Diagnostics.ProcessStartInfo]::new($exe)
    $launch.UseShellExecute = $false
    $launch.WorkingDirectory = Split-Path $exe
    $launch.Environment['ULTIMA_HOST_EVIDENCE_DIR'] = $EvidenceDirectory
    $launch.Environment['ULTIMA_HOST_STAGE'] = 't5'
    $launch.Environment['ULTIMA_HOST_AUTO_EXIT_MS'] = '6500'
    $launch.Environment['ULTIMA_HOST_FLOATINGBALL_TEST'] = '1'
    $launch.Environment['ULTIMA_HOST_FLOATINGBALL_CAPTURE_PATH'] = (Join-Path $EvidenceDirectory 't5-floating-ball.png')
    $hostProcess = [Diagnostics.Process]::Start($launch)
    $windowDeadline = [DateTime]::UtcNow.AddSeconds(20)
    while ([DateTime]::UtcNow -lt $windowDeadline -and -not $hostProcess.HasExited) {
        Add-VisibleSnapshot $snapshots 'host-poll'
        if (Test-Path -LiteralPath $runtimePath) {
            $runtime = Get-Content -Raw -LiteralPath $runtimePath | ConvertFrom-Json
            $hostHandle = [long]$runtime.mainWindowHandle
            if ($hostHandle -ne 0) { break }
        }
        Start-Sleep -Milliseconds 25
    }
    if ($hostHandle -eq 0) { throw 'Host GUI window did not appear within 20 seconds.' }

    while (-not $hostProcess.HasExited -and [DateTime]::UtcNow -lt $windowDeadline.AddSeconds(10)) {
        Add-VisibleSnapshot $snapshots 'host-poll'
        Start-Sleep -Milliseconds 25
    }
    if (-not $hostProcess.HasExited) { throw 'Host did not auto-exit within the selfcheck deadline.' }
    $hostExitCode = $hostProcess.ExitCode
    if ($hostExitCode -ne 0) { throw "Host exited with $hostExitCode." }
    if (-not (Test-Path -LiteralPath $windowEvidencePath)) { throw 'Final floating-ball runtime evidence was not produced.' }
}
catch {
    $failure = $_.Exception.Message
}
finally {
    if ($hostProcess -and -not $hostProcess.HasExited) {
        [void]$hostProcess.CloseMainWindow()
        if (-not $hostProcess.WaitForExit(2000)) { $hostProcess.Kill($true); $hostProcess.WaitForExit() }
    }
    $monitor.Dispose()
}

if ($hostProcess -and $hostProcess.HasExited) { $hostExitCode = $hostProcess.ExitCode }
$events = @($monitor.GetEvents())
$allObserved = @($events) + @($snapshots)
$newObserved = @($allObserved | Where-Object { -not $baselineHandles.ContainsKey([long]$_.Handle) })
$runtime = $null
if (Test-Path -LiteralPath $runtimePath) { $runtime = Get-Content -Raw -LiteralPath $runtimePath | ConvertFrom-Json }
$hostId = if ($hostProcess) { [uint32]$hostProcess.Id } else { 0 }
$allowedHostWindows = @($newObserved | Where-Object {
    $isMainWindow = [long]$_.Handle -eq $hostHandle -and [uint32]$_.ProcessId -eq $hostId
    $isWebViewSurface = $_.ProcessName -eq 'msedgewebview2' -and @($_.AncestorProcessIds) -contains $hostId -and
        $_.Left -ge $runtime.rect.Left -and $_.Top -ge $runtime.rect.Top -and
        $_.Right -le $runtime.rect.Right -and $_.Bottom -le $runtime.rect.Bottom
    $isMainWindow -or $isWebViewSurface
})
$allowedKeys = @{}; foreach ($item in $allowedHostWindows) { $allowedKeys["$($item.Handle)|$($item.ProcessId)"] = $true }
$unexpectedWindows = @($newObserved | Where-Object { -not $allowedKeys.ContainsKey("$($_.Handle)|$($_.ProcessId)") } | Sort-Object Handle, ProcessId, Source -Unique)
$afterProcesses = Get-DevelopmentProcessSnapshot
$afterByIdentity = @{}; foreach ($item in $afterProcesses) { $afterByIdentity["$($item.name)|$($item.pid)|$($item.startTimeUtc)"] = $true }
$preserved = @($beforeProcesses | Where-Object { $afterByIdentity.ContainsKey("$($_.name)|$($_.pid)|$($_.startTimeUtc)") })
$missing = @($beforeProcesses | Where-Object { -not $afterByIdentity.ContainsKey("$($_.name)|$($_.pid)|$($_.startTimeUtc)") })
$newDevelopmentProcesses = @($afterProcesses | Where-Object {
    $key = "$($_.name)|$($_.pid)|$($_.startTimeUtc)"
    -not (@($beforeProcesses | ForEach-Object { "$($_.name)|$($_.pid)|$($_.startTimeUtc)" }) -contains $key)
})

$buildPassed = $null -ne $build -and $build.exitCode -eq 0 -and $build.stdout -match '0 个警告' -and $build.stdout -match '0 个错误'
$runtimeEvents = @()
$eventPath = Join-Path $EvidenceDirectory 't5-events.jsonl'
if (Test-Path -LiteralPath $eventPath) { $runtimeEvents = @(Get-Content -LiteralPath $eventPath | Where-Object { $_.Trim() } | ForEach-Object { $_ | ConvertFrom-Json }) }
$failureEvents = @($runtimeEvents | Where-Object status -eq 'FAIL')
$feature = $null
if (Test-Path -LiteralPath $windowEvidencePath) { $feature = Get-Content -Raw -LiteralPath $windowEvidencePath | ConvertFrom-Json }
$featurePassed = $null -ne $feature -and $feature.status -eq 'FLOATING_BALL_READY' -and
    $feature.processId -eq $hostId -and $feature.mainWindowHandle -eq $hostHandle -and
    $feature.borderless -eq $true -and $feature.topmost -eq $true -and
    (Test-Path -LiteralPath $feature.screenshotPath)
if ($featurePassed) { $featurePassed = (Get-FileHash -LiteralPath $feature.screenshotPath -Algorithm SHA256).Hash.ToLowerInvariant() -eq $feature.screenshotSha256 }
$failureFree = $failureEvents.Count -eq 0 -and $null -ne $runtime -and $runtime.status -eq 'WINDOW_READY' -and $runtime.processId -eq $hostId
$windowPassed = $hostHandle -ne 0 -and $featurePassed -and $failureFree
$exitPassed = $hostExitCode -eq 0
$zeroPopupPassed = $unexpectedWindows.Count -eq 0 -and $build.maxMainWindowHandle -eq 0
$processPreservationPassed = $missing.Count -eq 0
$passed = $null -eq $failure -and $buildPassed -and $windowPassed -and $exitPassed -and $zeroPopupPassed -and $processPreservationPassed

$result = [ordered]@{
    status = $(if ($passed) { 'PASS' } else { 'FAIL' })
    startedAtUtc = $startedAt.ToString('o')
    completedAtUtc = [DateTimeOffset]::UtcNow.ToString('o')
    chain = [ordered]@{
        build = @{ passed = $buildPassed; exitCode = $build.exitCode; processId = $build.processId; createNoWindow = $true; windowStyle = 'Hidden'; maxMainWindowHandle = $build.maxMainWindowHandle }
        launch = @{ passed = $windowPassed; processId = $(if ($hostProcess) { $hostProcess.Id } else { $null }); useShellExecute = $false }
        window = @{ passed = $windowPassed; mainWindowHandle = $hostHandle; productGuiIsOnlyAllowedWindow = $true }
        exit = @{ passed = $exitPassed; exitCode = $hostExitCode; mode = 'ULTIMA_HOST_AUTO_EXIT_MS=6500' }
    }
    zeroPopup = [ordered]@{
        passed = $zeroPopupPassed
        method = 'WinEvent EVENT_OBJECT_CREATE..SHOW plus 25ms top-level visible-window enumeration'
        baselineVisibleWindowCount = $baseline.Count
        winEventCount = $events.Count
        enumerationSampleCount = $snapshots.Count
        allowedHostObservationCount = $allowedHostWindows.Count
        allowedWindowRule = 'host HWND, plus msedgewebview2 descendant surfaces geometrically contained inside the host window'
        unexpectedVisibleWindowCount = $unexpectedWindows.Count
        unexpectedVisibleWindows = $unexpectedWindows
    }
    processPreservation = [ordered]@{
        passed = $processPreservationPassed
        selection = 'process names only: Codex/Python/Node/dotnet/Ollama/Brain/Watchdog; no command lines or credential bodies read'
        before = $beforeProcesses
        after = $afterProcesses
        preservedCount = $preserved.Count
        missing = $missing
        newAfter = $newDevelopmentProcesses
    }
    files = [ordered]@{
        project = $project
        executable = $exe
        executableSha256 = $(if (Test-Path $exe) { (Get-FileHash -Algorithm SHA256 -LiteralPath $exe).Hash.ToLowerInvariant() } else { $null })
        buildLog = $buildLog
        runtimeEvidence = $runtimePath
        windowEvidence = $windowEvidencePath
        scriptSha256 = (Get-FileHash -Algorithm SHA256 -LiteralPath $PSCommandPath).Hash.ToLowerInvariant()
    }
    featurePassed = $featurePassed
    failureFree = $failureFree
    failureEvents = $failureEvents
    failure = $failure
}
[IO.File]::WriteAllText($jsonPath, ($result | ConvertTo-Json -Depth 12), [Text.UTF8Encoding]::new($false))
$executableHash = $result['files']['executableSha256']
$selfcheckScriptHash = $result['files']['scriptSha256']

$report = @"
# Host Shell Selfcheck — $ReportDate

- Decision: **$($result.status)**
- Build: $(if ($buildPassed) { 'PASS — exit 0; compiler diagnostics retained in build log' } else { 'FAIL' })
- Launch: $(if ($windowPassed) { "PASS — PID $($hostProcess.Id)" } else { 'FAIL' })
- Window: $(if ($windowPassed) { "PASS — HWND $hostHandle" } else { 'FAIL' })
- Exit: $(if ($exitPassed) { 'PASS — exit 0' } else { "FAIL — exit $hostExitCode" })
- Zero popup: $(if ($zeroPopupPassed) { "PASS — unexpected visible windows 0; WinEvent events $($events.Count); enumeration samples $($snapshots.Count)" } else { "FAIL — unexpected visible windows $($unexpectedWindows.Count)" })
- Background process preservation: $(if ($processPreservationPassed) { "PASS — $($preserved.Count)/$($beforeProcesses.Count) identities unchanged" } else { "FAIL — missing $($missing.Count) identities" })

## Launch discipline

- Build: `UseShellExecute=false`, `CreateNoWindow=true`, `WindowStyle=Hidden`, stdout/stderr redirected.
- Host: `UseShellExecute=false`; its product GUI is the sole allowed visible window.
- Runtime audit: WinEvent `EVENT_OBJECT_CREATE..EVENT_OBJECT_SHOW` plus 25 ms top-level visible-window enumeration.
- Credentials: no credential body or process command line was read or persisted.

## Evidence

- JSON: $jsonPath
- Build log: $buildLog
- Runtime: $runtimePath
- Final window: $windowEvidencePath
- EXE SHA-256: $executableHash
- Script SHA-256: $selfcheckScriptHash

This is executor selfcheck evidence only. W1 remains an independent supervisor decision.
"@
[IO.File]::WriteAllText($reportPath, $report, [Text.UTF8Encoding]::new($false))

Write-Output "HOST_SHELL_SELFCHECK=$($result.status)"
Write-Output "BUILD_EXIT=$($build.exitCode) HOST_PID=$($hostProcess.Id) HWND=$hostHandle HOST_EXIT=$hostExitCode"
Write-Output "UNEXPECTED_VISIBLE_WINDOWS=$($unexpectedWindows.Count) WINEVENTS=$($events.Count) ENUM_SAMPLES=$($snapshots.Count)"
Write-Output "BACKGROUND_IDENTITIES=$($preserved.Count)/$($beforeProcesses.Count)"
Write-Output "REPORT=$reportPath"
if (-not $passed) { exit 1 }
exit 0
