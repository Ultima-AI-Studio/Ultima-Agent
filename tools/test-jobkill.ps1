[CmdletBinding()]
param()

$ErrorActionPreference = 'Stop'
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot '..')).Path
$hostExe = Join-Path $projectRoot 'src\host-shell\UltimaAgent.HostShell\bin\Release\net8.0-windows10.0.19041.0\win-x64\UltimaAgent.HostShell.exe'
$statusPath = Join-Path $projectRoot 'data\voice-next\status.json'
$pidFile = Join-Path $projectRoot 'Data\logs\process-host-pids.json'
$runtimeEvidence = Join-Path $projectRoot 'docs\reports\evidence\installer-phase2\runtime'
$activeHosts = [System.Collections.Generic.List[System.Diagnostics.Process]]::new()
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class UltimaWindowTest {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
}
'@

function Assert-Criterion {
    param(
        [int]$Number,
        [bool]$Condition,
        [string]$Message
    )
    if (-not $Condition) {
        throw "CRITERION $Number FAIL: $Message"
    }
    Write-Output "CRITERION $Number PASS: $Message"
}

function Get-UltimaPythonProcesses {
    $escapedRoot = [regex]::Escape($projectRoot)
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match '^python(w)?\.exe$' -and
        $_.CommandLine -match $escapedRoot -and
        $_.CommandLine -match 'agent_server\.py|voice-next[\\/](launch|live|turn_worker)\.py'
    })
}

function Get-HostShellProcessIds {
    @(Get-Process -Name 'UltimaAgent.HostShell' -ErrorAction SilentlyContinue |
        ForEach-Object { [int]$_.Id })
}

function Get-VoiceStatus {
    if (-not (Test-Path -LiteralPath $statusPath)) {
        return $null
    }
    try {
        Get-Content -Raw -LiteralPath $statusPath | ConvertFrom-Json
    }
    catch {
        $null
    }
}

function Test-PidAlive {
    param([int]$ProcessId)
    $null -ne (Get-Process -Id $ProcessId -ErrorAction SilentlyContinue)
}

function Start-HostCase {
    param([bool]$CrashSelf)

    $baseline = @(Get-UltimaPythonProcesses | ForEach-Object { [int]$_.ProcessId })
    $baselineHosts = @(Get-HostShellProcessIds)
    $stage = "t8-$([Guid]::NewGuid().ToString('N'))"
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new($hostExe)
    $startInfo.UseShellExecute = $false
    $startInfo.WorkingDirectory = $projectRoot
    $startInfo.EnvironmentVariables['ULTIMA_PROJECT_ROOT'] = $projectRoot
    $startInfo.EnvironmentVariables['ULTIMA_USE_PROCESS_HOST'] = 'true'
    $startInfo.EnvironmentVariables['ULTIMA_HOST_EVIDENCE_DIR'] = $runtimeEvidence
    $startInfo.EnvironmentVariables['ULTIMA_HOST_STAGE'] = $stage
    $startInfo.EnvironmentVariables.Remove('ULTIMA_HOST_AUTO_EXIT_MS')
    if ($CrashSelf) {
        $startInfo.EnvironmentVariables['ULTIMA_HOST_CRASH_SELF'] = 'true'
    }
    else {
        $startInfo.EnvironmentVariables.Remove('ULTIMA_HOST_CRASH_SELF')
    }
    $hostProcess = [System.Diagnostics.Process]::Start($startInfo)
    $activeHosts.Add($hostProcess)

    [pscustomobject]@{
        Host = $hostProcess
        Baseline = $baseline
        BaselineHosts = $baselineHosts
        Stage = $stage
    }
}

function Wait-VoiceReady {
    param(
        [pscustomobject]$Case,
        [int]$Criterion,
        [int]$TimeoutSec = 300
    )
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    while ([DateTime]::UtcNow -lt $deadline) {
        $Case.Host.Refresh()
        if ($Case.Host.HasExited) {
            throw "CRITERION $Criterion FAIL: HostShell exited before voice readiness (exit=$($Case.Host.ExitCode))"
        }
        $processes = @(Get-UltimaPythonProcesses)
        $status = Get-VoiceStatus
        if ($processes.Count -ge 3 -and $null -ne $status -and
            $status.state -eq 'ready' -and $status.worker_ready -eq $true -and
            (Test-PidAlive ([int]$status.pid)) -and (Test-PidAlive ([int]$status.worker_pid))) {
            $owned = @($processes | Where-Object { $Case.Baseline -notcontains [int]$_.ProcessId } |
                ForEach-Object { [int]$_.ProcessId })
            $ownedHosts = @(Get-HostShellProcessIds | Where-Object { $Case.BaselineHosts -notcontains $_ })
            return [pscustomobject]@{
                Count = $processes.Count
                Owned = $owned
                Related = @($owned + $ownedHosts | Select-Object -Unique)
                Status = $status
            }
        }
        Start-Sleep -Milliseconds 200
    }
    throw "CRITERION $Criterion FAIL: voice readiness timed out after $TimeoutSec seconds"
}

function Wait-PidsGone {
    param(
        [int[]]$ProcessIds,
        [int]$TimeoutSec
    )
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    do {
        $alive = @($ProcessIds | Where-Object { Test-PidAlive $_ })
        if ($alive.Count -eq 0) {
            return $true
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)
    return $false
}

function Force-HostAndAssertJobCleanup {
    param(
        [pscustomobject]$Case,
        [int[]]$RelatedPids,
        [int]$Criterion
    )
    Stop-Process -Id $Case.Host.Id -Force
    $Case.Host.WaitForExit()
    $gone = Wait-PidsGone -ProcessIds $RelatedPids -TimeoutSec 3
    Assert-Criterion -Number $Criterion -Condition $gone -Message "HostShell force-kill reclaimed all new Host/Job PIDs within 3 seconds: $($RelatedPids -join ',')"
    Start-Sleep -Seconds 1
}

function Wait-CrashAndAssertCleanup {
    param(
        [pscustomobject]$Case,
        [int]$TimeoutSec = 300
    )
    $observed = [System.Collections.Generic.HashSet[int]]::new()
    $deadline = [DateTime]::UtcNow.AddSeconds($TimeoutSec)
    while ([DateTime]::UtcNow -lt $deadline) {
        foreach ($process in @(Get-UltimaPythonProcesses)) {
            $pidValue = [int]$process.ProcessId
            if ($Case.Baseline -notcontains $pidValue) {
                $null = $observed.Add($pidValue)
            }
        }
        foreach ($hostPid in @(Get-HostShellProcessIds)) {
            if ($Case.BaselineHosts -notcontains $hostPid) {
                $null = $observed.Add($hostPid)
            }
        }
        $Case.Host.Refresh()
        if ($Case.Host.HasExited) {
            $owned = @($observed)
            $enoughChildren = $owned.Count -ge 2
            Assert-Criterion -Number 4 -Condition $enoughChildren -Message "ULTIMA_HOST_CRASH_SELF started Job children before the real unhandled path"
            $failure = @(Get-ChildItem -LiteralPath $runtimeEvidence -Filter "$($Case.Stage)-failure-*.json" -ErrorAction SilentlyContinue |
                Sort-Object LastWriteTime -Descending | Select-Object -First 1)
            $failureRecord = if ($failure.Count -eq 1) { Get-Content -Raw -LiteralPath $failure[0].FullName | ConvertFrom-Json } else { $null }
            Assert-Criterion -Number 4 -Condition ($null -ne $failureRecord -and $failureRecord.code -eq 'UI_UNHANDLED') -Message 'runtime evidence proves the UI_UNHANDLED handler executed'
            $gone = Wait-PidsGone -ProcessIds $owned -TimeoutSec 3
            Assert-Criterion -Number 4 -Condition $gone -Message "UnhandledException reclaimed crash-run PIDs within 3 seconds: $($owned -join ',')"
            return
        }
        Start-Sleep -Milliseconds 100
    }
    throw "CRITERION 4 FAIL: ULTIMA_HOST_CRASH_SELF did not exit within $TimeoutSec seconds"
}

function Close-HostWindow {
    param([System.Diagnostics.Process]$HostProcess)
    $deadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        $HostProcess.Refresh()
        if ($HostProcess.MainWindowHandle -ne [IntPtr]::Zero) {
            return [UltimaWindowTest]::PostMessage($HostProcess.MainWindowHandle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
        }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)
    return $false
}

try {
    Assert-Criterion -Number 1 -Condition (Test-Path -LiteralPath $hostExe) -Message 'Release HostShell executable exists'

    $case1 = Start-HostCase -CrashSelf $false
    $ready1 = Wait-VoiceReady -Case $case1 -Criterion 1
    Assert-Criterion -Number 1 -Condition ($ready1.Count -ge 3) -Message "UltimaAgent Python process count is $($ready1.Count) (>=3)"
    Assert-Criterion -Number 1 -Condition ($ready1.Owned.Count -ge 2) -Message "Job run owns voice PIDs: $($ready1.Owned -join ',')"
    Force-HostAndAssertJobCleanup -Case $case1 -RelatedPids $ready1.Related -Criterion 2

    $case2 = Start-HostCase -CrashSelf $false
    $ready2 = Wait-VoiceReady -Case $case2 -Criterion 3
    Assert-Criterion -Number 3 -Condition ($ready2.Count -ge 3) -Message "second run reached $($ready2.Count) UltimaAgent Python processes"
    Force-HostAndAssertJobCleanup -Case $case2 -RelatedPids $ready2.Related -Criterion 3

    $crashCase = Start-HostCase -CrashSelf $true
    Wait-CrashAndAssertCleanup -Case $crashCase

    $normalCase = Start-HostCase -CrashSelf $false
    $normalReady = Wait-VoiceReady -Case $normalCase -Criterion 5
    $closePosted = Close-HostWindow -HostProcess $normalCase.Host
    Assert-Criterion -Number 5 -Condition $closePosted -Message 'WM_CLOSE posted to the real HostShell window'
    $normalExited = $normalCase.Host.WaitForExit(15000)
    Assert-Criterion -Number 5 -Condition $normalExited -Message 'HostShell exited through the window Closed path'
    $normalGone = Wait-PidsGone -ProcessIds $normalReady.Related -TimeoutSec 3
    Assert-Criterion -Number 5 -Condition $normalGone -Message 'normal-close Host/Job PIDs are gone'
    Assert-Criterion -Number 5 -Condition (-not (Test-Path -LiteralPath $pidFile)) -Message 'all ProcessHost pid files were cleaned'
    $finalStatus = Get-VoiceStatus
    Assert-Criterion -Number 5 -Condition ($null -ne $finalStatus -and $finalStatus.state -eq 'stopped') -Message 'status.json state is stopped'

    Write-Output 'TEST_JOBKILL_RESULT=PASS criteria=1,2,3,4,5'
    exit 0
}
catch {
    Write-Error $_
    exit 1
}
finally {
    foreach ($hostProcess in $activeHosts) {
        try {
            $hostProcess.Refresh()
            if (-not $hostProcess.HasExited) {
                Stop-Process -Id $hostProcess.Id -Force -ErrorAction SilentlyContinue
            }
        }
        catch {
        }
        $hostProcess.Dispose()
    }
}
