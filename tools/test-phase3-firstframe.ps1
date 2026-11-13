[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$hostExe = Join-Path $projectRoot "src/host-shell/UltimaAgent.HostShell/bin/Release/net8.0-windows10.0.19041.0/win-x64/UltimaAgent.HostShell.exe"
$timingPath = Join-Path $projectRoot "data/logs/startup-timing.json"
$statusPath = Join-Path $projectRoot "data/voice-next/status.json"
$evidenceRoot = Join-Path $projectRoot "docs/reports/evidence/installer-phase3"
$runToken = Get-Date -Format "yyyyMMdd-HHmmss"
$runtimeRoot = Join-Path $evidenceRoot "t7-runtime/$runToken"
$resultPath = Join-Path $evidenceRoot "t7-firstframe-runs.json"
$gatePath = Join-Path $evidenceRoot "t7-gate.txt"
$knownZombiePids = @(24988, 22572)
$consoleNames = @("conhost.exe", "cmd.exe", "powershell.exe", "pwsh.exe")
$results = [System.Collections.Generic.List[object]]::new()
$activeHosts = [System.Collections.Generic.List[System.Diagnostics.Process]]::new()
[System.IO.Directory]::CreateDirectory($runtimeRoot) | Out-Null

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class UltimaFirstFrameWindow {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
}
'@

function Get-ProjectPythonProcesses {
    $escapedRoot = [regex]::Escape($projectRoot)
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match "^python(w)?\.exe$" -and
        $_.CommandLine -match $escapedRoot -and
        $_.CommandLine -match "agent_server\.py|voice-next[\\/](launch|live|turn_worker)\.py"
    })
}

function Get-CountableHostPids {
    @(Get-CimInstance Win32_Process -Filter "Name = 'UltimaAgent.HostShell.exe'" | Where-Object {
        $_.ProcessId -notin $knownZombiePids
    } | ForEach-Object { [int]$_.ProcessId })
}

function Test-ProcessAlive([int]$processId) {
    $null -ne (Get-Process -Id $processId -ErrorAction SilentlyContinue)
}

function Read-JsonFile([string]$path) {
    if (-not (Test-Path -LiteralPath $path)) { return $null }
    try { Get-Content -LiteralPath $path -Raw | ConvertFrom-Json }
    catch { $null }
}

function Find-HostConsoleDescendants([int]$hostProcessId, [int[]]$consoleBaseline) {
    $snapshot = @(Get-CimInstance Win32_Process)
    $found = [System.Collections.Generic.List[object]]::new()
    foreach ($process in @($snapshot | Where-Object {
        $_.Name -in $consoleNames -and $_.ProcessId -notin $consoleBaseline
    })) {
        $parentId = [int]$process.ParentProcessId
        for ($depth = 0; $depth -lt 16 -and $parentId -ne 0; $depth++) {
            if ($parentId -eq $hostProcessId) {
                $found.Add($process)
                break
            }
            $parent = $snapshot | Where-Object ProcessId -eq $parentId | Select-Object -First 1
            if ($null -eq $parent) { break }
            $parentId = [int]$parent.ParentProcessId
        }
    }
    @($found)
}

function Wait-PidsGone([int[]]$processIds, [int]$timeoutSeconds = 3) {
    $deadline = [DateTime]::UtcNow.AddSeconds($timeoutSeconds)
    do {
        $alive = @($processIds | Where-Object { Test-ProcessAlive $_ })
        if ($alive.Count -eq 0) { return $true }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)
    return $false
}

function Close-HostWindow([System.Diagnostics.Process]$process) {
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        $process.Refresh()
        if ($process.MainWindowHandle -ne [IntPtr]::Zero) {
            return [UltimaFirstFrameWindow]::PostMessage(
                $process.MainWindowHandle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)
    return $false
}

function Invoke-ColdStart([int]$runNumber) {
    $baselinePython = @(Get-ProjectPythonProcesses | ForEach-Object { [int]$_.ProcessId })
    $baselineHosts = @(Get-CountableHostPids)
    $consoleBaseline = @(Get-CimInstance Win32_Process | Where-Object Name -in $consoleNames |
        ForEach-Object { [int]$_.ProcessId })
    $runEvidence = Join-Path $runtimeRoot "run-$runNumber"
    [System.IO.Directory]::CreateDirectory($runEvidence) | Out-Null

    $startInfo = [System.Diagnostics.ProcessStartInfo]::new($hostExe)
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.WorkingDirectory = $projectRoot
    $startInfo.EnvironmentVariables["ULTIMA_PROJECT_ROOT"] = $projectRoot
    $startInfo.EnvironmentVariables["ULTIMA_HOST_WRITE_ROOT"] = $projectRoot
    $startInfo.EnvironmentVariables["ULTIMA_USE_PROCESS_HOST"] = "true"
    $startInfo.EnvironmentVariables["ULTIMA_HOST_LIVE"] = "1"
    $startInfo.EnvironmentVariables["ULTIMA_HOST_WARM_RING"] = "1"
    $startInfo.EnvironmentVariables["ULTIMA_HOST_EVIDENCE_DIR"] = $runEvidence
    $startInfo.EnvironmentVariables.Remove("ULTIMA_HOST_STATUS_FILE")
    $startInfo.EnvironmentVariables.Remove("ULTIMA_HOST_AUTO_EXIT_MS")
    $process = [System.Diagnostics.Process]::Start($startInfo)
    $activeHosts.Add($process)
    Write-Host "RUN=$runNumber HOST_PID=$($process.Id) BASELINE_HOSTS=$($baselineHosts -join ',') BASELINE_PYTHON=$($baselinePython -join ',')"

    $timing = $null
    $readiness = $null
    $consoleDescendants = [System.Collections.Generic.HashSet[int]]::new()
    $visibleConsoleDescendants = [System.Collections.Generic.HashSet[int]]::new()
    $deadline = [DateTime]::UtcNow.AddSeconds(300)
    while ([DateTime]::UtcNow -lt $deadline) {
        $process.Refresh()
        if ($process.HasExited) { throw "Run $runNumber HostShell exited early with code $($process.ExitCode)." }
        foreach ($consoleProcess in @(Find-HostConsoleDescendants $process.Id $consoleBaseline)) {
            [void]$consoleDescendants.Add([int]$consoleProcess.ProcessId)
            $consoleRuntime = Get-Process -Id $consoleProcess.ProcessId -ErrorAction SilentlyContinue
            if ($null -ne $consoleRuntime -and $consoleRuntime.MainWindowHandle -ne [IntPtr]::Zero) {
                [void]$visibleConsoleDescendants.Add([int]$consoleProcess.ProcessId)
            }
        }
        $candidateTiming = Read-JsonFile $timingPath
        if ($null -ne $candidateTiming -and [int]$candidateTiming.pid -eq $process.Id -and
            $null -ne $candidateTiming.first_frame_ms) {
            $firstObservation = $null -eq $timing
            $timing = $candidateTiming
            if ($firstObservation) {
                Write-Host "RUN=$runNumber FIRST_FRAME_MS=$($timing.first_frame_ms) WINDOW_VISIBLE_MS=$($timing.window_visible_ms)"
            }
        }
        $candidateStatus = Read-JsonFile $statusPath
        if ($null -ne $candidateStatus -and
            ($candidateStatus.state -eq "ready" -or [int]$candidateStatus.warm_progress -eq 100) -and
            $null -ne $candidateStatus.pid -and
            (Test-ProcessAlive ([int]$candidateStatus.pid)) -and
            $baselinePython -notcontains [int]$candidateStatus.pid) {
            $readiness = $candidateStatus
        }
        if ($null -ne $timing -and $null -ne $readiness) { break }
        Start-Sleep -Milliseconds 100
    }
    if ($null -eq $timing) { throw "Run $runNumber did not publish first_frame_ms within 300 seconds." }
    if ($null -eq $readiness) { throw "Run $runNumber did not reach fresh voice ready/100 within 300 seconds." }
    $timingDeadline = [DateTime]::UtcNow.AddSeconds(5)
    while ($null -eq $timing.voice_ready_ms -and [DateTime]::UtcNow -lt $timingDeadline) {
        Start-Sleep -Milliseconds 100
        $candidateTiming = Read-JsonFile $timingPath
        if ($null -ne $candidateTiming -and [int]$candidateTiming.pid -eq $process.Id) {
            $timing = $candidateTiming
        }
    }
    if ($null -eq $timing.voice_ready_ms) { throw "Run $runNumber did not persist voice_ready_ms." }

    $ringScreenshot = @(Get-ChildItem -LiteralPath $runEvidence -Filter "warm-ring-*.png" -ErrorAction SilentlyContinue |
        Where-Object Name -notmatch "100" | Sort-Object LastWriteTime | Select-Object -First 1)
    if ($ringScreenshot.Count -ne 1) { throw "Run $runNumber did not capture a visible warm-ring screenshot." }
    if ($runNumber -eq 1) {
        [System.IO.File]::Copy($ringScreenshot[0].FullName, (Join-Path $evidenceRoot "t7-warm-ring-visible.png"), $true)
    }

    $ownedPython = @(Get-ProjectPythonProcesses | Where-Object {
        $baselinePython -notcontains [int]$_.ProcessId
    } | ForEach-Object { [int]$_.ProcessId })
    $ownedHosts = @(Get-CountableHostPids | Where-Object { $baselineHosts -notcontains $_ })
    $relatedPids = @($ownedPython + $ownedHosts | Select-Object -Unique)
    $closePosted = Close-HostWindow $process
    if (-not $closePosted) { throw "Run $runNumber could not post WM_CLOSE." }
    if (-not $process.WaitForExit(15000)) { throw "Run $runNumber HostShell did not exit after WM_CLOSE." }
    $residualGone = Wait-PidsGone $relatedPids 3
    if (-not $residualGone) {
        $alive = @($relatedPids | Where-Object { Test-ProcessAlive $_ })
        throw "Run $runNumber retained PIDs after 3 seconds: $($alive -join ',')."
    }
    if ($visibleConsoleDescendants.Count -ne 0) {
        throw "Run $runNumber displayed console windows from PIDs: $(@($visibleConsoleDescendants) -join ',')."
    }

    $record = [ordered]@{
        run = $runNumber
        host_pid = $process.Id
        excluded_zombie_pids = $knownZombiePids
        baseline_host_pids = $baselineHosts
        baseline_python_pids = $baselinePython
        t0_iso = $timing.t0_iso
        window_visible_ms = [int64]$timing.window_visible_ms
        first_frame_ms = [int64]$timing.first_frame_ms
        voice_ready_ms = [int64]$timing.voice_ready_ms
        ready_observed_at = (Get-Date).ToString("O")
        status_state = [string]$readiness.state
        warm_progress = [int]$readiness.warm_progress
        voice_pid = [int]$readiness.pid
        ring_screenshot = $ringScreenshot[0].FullName
        ring_screenshot_sha256 = (Get-FileHash -LiteralPath $ringScreenshot[0].FullName -Algorithm SHA256).Hash
        wm_close_posted = $closePosted
        related_pids = $relatedPids
        residual_pid_count_after_3s = 0
        console_descendant_process_pids = @($consoleDescendants)
        console_descendant_process_count = $consoleDescendants.Count
        visible_console_window_count = 0
    }
    Write-Host "RUN=$runNumber READY state=$($record.status_state) progress=$($record.warm_progress) voice_pid=$($record.voice_pid)"
    Write-Host "RUN=$runNumber WM_CLOSE=$closePosted RESIDUAL_PID_COUNT=0 CONSOLE_PROCESS_COUNT=$($record.console_descendant_process_count) VISIBLE_CONSOLE_WINDOW_COUNT=0"
    return [pscustomobject]$record
}

try {
    if (-not (Test-Path -LiteralPath $hostExe)) { throw "Release HostShell executable is missing: $hostExe" }
    foreach ($zombiePid in $knownZombiePids) {
        $zombie = Get-CimInstance Win32_Process -Filter "ProcessId = $zombiePid" -ErrorAction SilentlyContinue
        if ($null -eq $zombie -or [int]$zombie.ThreadCount -ne 0) {
            throw "Known zombie PID $zombiePid is absent or no longer a zero-thread zombie; baseline changed."
        }
    }
    for ($runNumber = 1; $runNumber -le 3; $runNumber++) {
        $results.Add((Invoke-ColdStart $runNumber))
    }
    $orderedFrames = @($results | ForEach-Object { [int64]$_.first_frame_ms } | Sort-Object)
    $median = $orderedFrames[1]
    $payload = [ordered]@{
        captured_at = (Get-Date).ToString("O")
        release_executable = $hostExe
        known_zombie_hostshell_pids_excluded = $knownZombiePids
        runs = @($results)
        first_frame_distribution_ms = @($results | ForEach-Object { [int64]$_.first_frame_ms })
        first_frame_median_ms = $median
        threshold_ms = 1500
        gate_pass = ($median -le 1500)
    }
    [System.IO.File]::WriteAllText(
        $resultPath,
        ($payload | ConvertTo-Json -Depth 8) + [Environment]::NewLine,
        [System.Text.UTF8Encoding]::new($false))
    $readyRunCount = @($results | Where-Object { $_.status_state -eq "ready" -or $_.warm_progress -eq 100 }).Count
    $closedRunCount = @($results | Where-Object wm_close_posted).Count
    $gateLines = @(
        "Gate T7 — three real cold starts",
        "RESULT_JSON=$resultPath",
        "FIRST_FRAME_DISTRIBUTION_MS=$([string]::Join(',', $payload.first_frame_distribution_ms))",
        "FIRST_FRAME_MEDIAN_MS=$median",
        "THRESHOLD_MS=1500",
        "READY_RUNS=$readyRunCount/3",
        "WM_CLOSE_RUNS=$closedRunCount/3",
        "RESIDUAL_PID_COUNT=0",
        "VISIBLE_CONSOLE_WINDOW_COUNT=0",
        "TRANSIENT_CONSOLE_PROCESS_NOTE=launch.py frozen-SHA legacy probe uses CREATE_NO_WINDOW; process IDs retained in result JSON",
        "RING_SCREENSHOT=$(Join-Path $evidenceRoot 't7-warm-ring-visible.png')",
        $(if ($median -le 1500) { "GATE T7: PASS" } else { "GATE T7: BLOCKED" })
    )
    [System.IO.File]::WriteAllLines($gatePath, $gateLines, [System.Text.UTF8Encoding]::new($false))
    $gateLines | ForEach-Object { Write-Output $_ }
    if ($median -gt 1500) { throw "T7 median first frame $median ms exceeds the 1500 ms hard threshold." }
    Write-Output "T7_FIRSTFRAME_PASS"
}
finally {
    foreach ($process in $activeHosts) {
        try {
            $process.Refresh()
            if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
        }
        catch { }
        $process.Dispose()
    }
}
