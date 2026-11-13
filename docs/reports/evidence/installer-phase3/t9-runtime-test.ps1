param([switch]$ActionsOnly)

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$projectRoot = (Resolve-Path ".").Path
$hostExe = Join-Path $projectRoot "src/host-shell/UltimaAgent.HostShell/bin/Release/net8.0-windows10.0.19041.0/win-x64/UltimaAgent.HostShell.exe"
$evidenceRoot = Join-Path $projectRoot "docs/reports/evidence/installer-phase3"
$statePath = Join-Path $projectRoot "data/host/host-tasks-state.json"
$guardianEventsPath = Join-Path $projectRoot "data/logs/guardian-events.jsonl"
$taskManagerLogPath = Join-Path $projectRoot "data/logs/taskmanager-events.log"
$knownZombiePids = @(24988, 22572)
$consoleNames = @("conhost.exe", "cmd.exe", "powershell.exe", "pwsh.exe")
$visibleConsolePids = [System.Collections.Generic.HashSet[int]]::new()
$transientConsolePids = [System.Collections.Generic.HashSet[int]]::new()
$activeHosts = [System.Collections.Generic.List[System.Diagnostics.Process]]::new()

Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class UltimaTaskManagerWindow {
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
}
'@

function Write-InjectedState([string]$path, [string]$primaryStatus, [int]$revision) {
    $document = [ordered]@{
        schema = "ultimaagent-host-task-state/v1"
        generated_at = (Get-Date).ToString("O")
        tasks = @(
            [ordered]@{ task_id="agent-server"; name="Agent Server"; enabled=$true; status=$primaryStatus; pid=4101+$revision; restart_count=2+$revision; last_probe_at=(Get-Date).AddSeconds(-4).ToString("O"); last_result="injected-$primaryStatus"; cooldown_until=$(if($primaryStatus -eq "cooldown"){(Get-Date).AddMinutes(5).ToString("O")}else{$null}) },
            [ordered]@{ task_id="voice-launcher"; name="Voice Launcher"; enabled=$true; status="cooldown"; pid=5202; restart_count=1; last_probe_at=(Get-Date).AddSeconds(-12).ToString("O"); last_result="injected-cooldown"; cooldown_until=(Get-Date).AddMinutes(4).ToString("O") },
            [ordered]@{ task_id="probe-fixture"; name="Probe Fixture"; enabled=$true; status="error"; pid=$null; restart_count=7; last_probe_at=(Get-Date).AddSeconds(-31).ToString("O"); last_result="injected-error"; cooldown_until=$null }
        )
    }
    [System.IO.File]::WriteAllText($path, ($document | ConvertTo-Json -Depth 6), [Text.UTF8Encoding]::new($false))
}

function Write-Action([string]$path, [int]$sequence, [string]$kind, [string]$taskId, [object]$enabled) {
    $action = [ordered]@{ seq=$sequence; kind=$kind; task_id=$taskId }
    if ($enabled -is [bool]) { $action.enabled = [bool]$enabled }
    [System.IO.File]::WriteAllText($path, ($action | ConvertTo-Json -Compress), [Text.UTF8Encoding]::new($false))
}

function Get-ProjectPythonPids {
    $escapedRoot = [regex]::Escape($projectRoot)
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match "^python(w)?\.exe$" -and $_.CommandLine -match $escapedRoot -and
        $_.CommandLine -match "agent_server\.py|voice-next[\\/](launch|live|turn_worker)\.py"
    } | ForEach-Object { [int]$_.ProcessId })
}

function Get-AgentServerProcesses {
    $escapedRoot = [regex]::Escape($projectRoot)
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match "^python(w)?\.exe$" -and $_.CommandLine -match $escapedRoot -and
        $_.CommandLine -match "src[\\/]brain[\\/]agent_server\.py"
    })
}

function Get-HostPids {
    @(Get-CimInstance Win32_Process -Filter "Name = 'UltimaAgent.HostShell.exe'" | Where-Object {
        $_.ProcessId -notin $knownZombiePids
    } | ForEach-Object { [int]$_.ProcessId })
}

function Observe-ConsoleWindows([int]$hostProcessId) {
    $snapshot = @(Get-CimInstance Win32_Process)
    foreach ($candidate in @($snapshot | Where-Object Name -in $consoleNames)) {
        $parentId = [int]$candidate.ParentProcessId
        $descendant = $false
        for ($depth=0; $depth -lt 16 -and $parentId -ne 0; $depth++) {
            if ($parentId -eq $hostProcessId) { $descendant=$true; break }
            $parent = $snapshot | Where-Object ProcessId -eq $parentId | Select-Object -First 1
            if ($null -eq $parent) { break }
            $parentId = [int]$parent.ParentProcessId
        }
        if ($descendant) {
            [void]$transientConsolePids.Add([int]$candidate.ProcessId)
            $runtime = Get-Process -Id $candidate.ProcessId -ErrorAction SilentlyContinue
            if ($null -ne $runtime -and $runtime.MainWindowHandle -ne [IntPtr]::Zero) {
                [void]$visibleConsolePids.Add([int]$candidate.ProcessId)
            }
        }
    }
}

function Start-TaskManagerHost([string]$evidenceDirectory, [string]$injectedState, [string]$actionFile, [int]$autoExitMilliseconds) {
    [System.IO.Directory]::CreateDirectory($evidenceDirectory) | Out-Null
    $startInfo = [Diagnostics.ProcessStartInfo]::new($hostExe)
    $startInfo.WorkingDirectory = $projectRoot
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.EnvironmentVariables["ULTIMA_PROJECT_ROOT"] = $projectRoot
    $startInfo.EnvironmentVariables["ULTIMA_HOST_WRITE_ROOT"] = $projectRoot
    $startInfo.EnvironmentVariables["ULTIMA_USE_PROCESS_HOST"] = "true"
    $startInfo.EnvironmentVariables["ULTIMA_AUTOSTART_KIND"] = "none"
    $startInfo.EnvironmentVariables["ULTIMA_HOST_TASK_MANAGER"] = "1"
    $startInfo.EnvironmentVariables["ULTIMA_HOST_EVIDENCE_DIR"] = $evidenceDirectory
    if ($injectedState) { $startInfo.EnvironmentVariables["ULTIMA_HOST_TASK_STATE_FILE"] = $injectedState }
    else { $startInfo.EnvironmentVariables.Remove("ULTIMA_HOST_TASK_STATE_FILE") }
    if ($actionFile) { $startInfo.EnvironmentVariables["ULTIMA_HOST_TASK_MANAGER_ACTION_FILE"] = $actionFile }
    else { $startInfo.EnvironmentVariables.Remove("ULTIMA_HOST_TASK_MANAGER_ACTION_FILE") }
    if ($autoExitMilliseconds -gt 0) { $startInfo.EnvironmentVariables["ULTIMA_HOST_AUTO_EXIT_MS"] = [string]$autoExitMilliseconds }
    else { $startInfo.EnvironmentVariables.Remove("ULTIMA_HOST_AUTO_EXIT_MS") }
    $process = [Diagnostics.Process]::Start($startInfo)
    $activeHosts.Add($process)
    return $process
}

function Wait-ForFile([string]$path, [int]$hostProcessId, [int]$seconds=20) {
    $deadline=[DateTime]::UtcNow.AddSeconds($seconds)
    while([DateTime]::UtcNow -lt $deadline) {
        Observe-ConsoleWindows $hostProcessId
        if(Test-Path -LiteralPath $path) { return }
        Start-Sleep -Milliseconds 100
    }
    throw "Timed out waiting for $path"
}

function Read-StateTask([string]$taskId) {
    if(-not(Test-Path -LiteralPath $statePath)){return $null}
    try { (Get-Content -LiteralPath $statePath -Raw | ConvertFrom-Json).tasks | Where-Object task_id -eq $taskId | Select-Object -First 1 }
    catch { $null }
}

function Get-NewEvent([int]$startLine, [string]$kind, [string]$detailPattern="") {
    if(-not(Test-Path -LiteralPath $guardianEventsPath)){return $null}
    foreach($line in @(Get-Content -LiteralPath $guardianEventsPath | Select-Object -Skip $startLine)) {
        try {
            $event=$line|ConvertFrom-Json
            if($event.kind -eq $kind -and ([string]$event.detail -match $detailPattern)){return $event}
        } catch { }
    }
    return $null
}

function Wait-ForCondition([scriptblock]$condition, [int]$hostProcessId, [int]$seconds, [string]$failure) {
    $deadline=[DateTime]::UtcNow.AddSeconds($seconds)
    while([DateTime]::UtcNow -lt $deadline) {
        Observe-ConsoleWindows $hostProcessId
        $value=& $condition
        if($null -ne $value -and $value -ne $false){return $value}
        Start-Sleep -Milliseconds 100
    }
    throw $failure
}

function Close-Host([Diagnostics.Process]$process, [int[]]$baselinePython, [int[]]$baselineHosts) {
    $process.Refresh()
    if($process.MainWindowHandle -eq [IntPtr]::Zero){throw "Task manager window handle is unavailable."}
    if(-not[UltimaTaskManagerWindow]::PostMessage($process.MainWindowHandle,0x0010,[IntPtr]::Zero,[IntPtr]::Zero)){throw "WM_CLOSE failed."}
    if(-not$process.WaitForExit(15000)){throw "HostShell did not exit after WM_CLOSE."}
    $deadline=[DateTime]::UtcNow.AddSeconds(3)
    do {
        $remaining=@((Get-ProjectPythonPids|Where-Object{$baselinePython -notcontains $_}) + (Get-HostPids|Where-Object{$baselineHosts -notcontains $_}) | Select-Object -Unique)
        if($remaining.Count -eq 0){return}
        Start-Sleep -Milliseconds 100
    } while([DateTime]::UtcNow -lt $deadline)
    throw "HostShell left related PIDs after three seconds: $($remaining -join ',')"
}

try {
    if (-not $ActionsOnly) {
        $renderDir=Join-Path $evidenceRoot "t9-render-states-accepted"
        $injectedPath=Join-Path $renderDir "injected-state.json"
        [System.IO.Directory]::CreateDirectory($renderDir)|Out-Null
        Write-InjectedState $injectedPath "running" 1
        $renderBaselinePython=@(Get-ProjectPythonPids);$renderBaselineHosts=@(Get-HostPids)
        $renderHost=Start-TaskManagerHost $renderDir $injectedPath "" 0
        "RENDER_HOST_PID=$($renderHost.Id)"
        foreach($entry in @(@("running",1),@("cooldown",2),@("error",3))) {
            $status=[string]$entry[0];$ordinal=[int]$entry[1]
            if($ordinal -gt 1){Write-InjectedState $injectedPath $status $ordinal}
            $screenshot=Join-Path $renderDir "taskmanager-state-$ordinal-$status.png"
            Wait-ForFile $screenshot $renderHost.Id 25
            "STATE_SCREENSHOT status=$status sha256=$((Get-FileHash -LiteralPath $screenshot -Algorithm SHA256).Hash)"
        }
        Close-Host $renderHost $renderBaselinePython $renderBaselineHosts
        "RENDER_CLOSE_RESIDUAL=0"
        Start-Sleep -Seconds 8
    }
    else {
        Start-Sleep -Seconds 3
    }

    $actionDir=Join-Path $evidenceRoot "t9-actions-coherent-final"
    $actionFile=Join-Path $actionDir "action.json"
    [System.IO.Directory]::CreateDirectory($actionDir)|Out-Null
    $actionBaselinePython=@(Get-ProjectPythonPids);$actionBaselineHosts=@(Get-HostPids)
    $eventStart=if(Test-Path -LiteralPath $guardianEventsPath){@(Get-Content -LiteralPath $guardianEventsPath).Count}else{0}
    $taskLogStart=if(Test-Path -LiteralPath $taskManagerLogPath){@(Get-Content -LiteralPath $taskManagerLogPath).Count}else{0}
    $actionHost=Start-TaskManagerHost $actionDir "" $actionFile 0
    "ACTION_HOST_PID=$($actionHost.Id)"
    $null=Wait-ForCondition { if(Test-Path -LiteralPath $taskManagerLogPath){Get-Content -LiteralPath $taskManagerLogPath|Select-Object -Skip $taskLogStart|Where-Object{$_ -match 'SNAPSHOT_PUSH'}|Select-Object -First 1} } $actionHost.Id 60 "Task manager did not publish its first live snapshot."
    $sequence=0
    $initialAgentState=Read-StateTask "agent-server"
    if($null-ne$initialAgentState -and -not[bool]$initialAgentState.enabled){
        $sequence++
        Write-Action $actionFile $sequence "set-enabled" "agent-server" $true
        $null=Wait-ForCondition { Get-NewEvent $eventStart "set_enabled" "enabled=true" } $actionHost.Id 20 "Initial enable normalization did not reach Guardian events."
        "INITIAL_ENABLED_NORMALIZATION=True"
    }
    $agent=Wait-ForCondition { Get-AgentServerProcesses|Select-Object -First 1 } $actionHost.Id 30 "Agent server did not start."
    $beforeRestart=Read-StateTask "agent-server"

    $sequence++
    Write-Action $actionFile $sequence "restart" "agent-server" $null
    $restartEvent=Wait-ForCondition { Get-NewEvent $eventStart "restart" "taskmanager manual restart" } $actionHost.Id 20 "Restart click did not reach Guardian events."
    $restartState=Wait-ForCondition { $task=Read-StateTask "agent-server";if($null-ne$task -and [int]$task.restart_count -gt [int]$beforeRestart.restart_count){$task} } $actionHost.Id 20 "Restart count did not refresh."
    $restartShot=Join-Path $actionDir "taskmanager-action-restart-agent-server.png"
    Wait-ForFile $restartShot $actionHost.Id 20
    "RESTART_EVENT kind=$($restartEvent.kind) detail=$($restartEvent.detail) restart_count=$($restartState.restart_count) screenshot_sha256=$((Get-FileHash -LiteralPath $restartShot -Algorithm SHA256).Hash)"

    $sequence++
    Write-Action $actionFile $sequence "set-enabled" "agent-server" $false
    $disabledEvent=Wait-ForCondition { Get-NewEvent $eventStart "set_enabled" "enabled=false" } $actionHost.Id 20 "Disable click did not reach Guardian events."
    $disabledSkipStart=@(Get-Content -LiteralPath $guardianEventsPath).Count
    $disableShot=Join-Path $actionDir "taskmanager-action-set-enabled-false-agent-server.png"
    Wait-ForFile $disableShot $actionHost.Id 20
    $agentToKill=Wait-ForCondition { Get-AgentServerProcesses|Select-Object -First 1 } $actionHost.Id 10 "No agent server was available for the disabled-kill test."
    $killedPid=[int]$agentToKill.ProcessId
    Stop-Process -Id $killedPid -Force
    $null=Wait-ForCondition { if($null-eq(Get-Process -Id $killedPid -ErrorAction SilentlyContinue)){"gone"} } $actionHost.Id 5 "Disabled agent server did not exit."
    $disabledSkip=Wait-ForCondition { Get-NewEvent $disabledSkipStart "disabled_skip" "guardian restart disabled" } $actionHost.Id 25 "Guardian did not record a post-disable disabled_skip."
    $unexpectedAgent=@(Get-AgentServerProcesses)
    if($unexpectedAgent.Count -ne 0){throw "Guardian relaunched disabled agent server: $($unexpectedAgent.ProcessId -join ',')"}
    "DISABLED_KILL pid=$killedPid disabled_event=$($disabledEvent.detail) guardian_event=$($disabledSkip.kind) relaunched=0 screenshot_sha256=$((Get-FileHash -LiteralPath $disableShot -Algorithm SHA256).Hash)"

    $reenableEventStart=@(Get-Content -LiteralPath $guardianEventsPath).Count
    $sequence++
    Write-Action $actionFile $sequence "set-enabled" "agent-server" $true
    $enabledEvent=Wait-ForCondition { Get-NewEvent $reenableEventStart "set_enabled" "enabled=true" } $actionHost.Id 20 "Enable click did not reach Guardian events."
    $enableShot=Join-Path $actionDir "taskmanager-action-set-enabled-true-agent-server.png"
    Wait-ForFile $enableShot $actionHost.Id 20
    $guardianRestart=Wait-ForCondition { Get-NewEvent $reenableEventStart "restart" "guardian health failure" } $actionHost.Id 35 "Guardian did not restore the re-enabled agent server."
    $recoveredAgent=Wait-ForCondition { Get-AgentServerProcesses|Select-Object -First 1 } $actionHost.Id 15 "Re-enabled agent server did not recover."
    "REENABLED event=$($enabledEvent.detail) guardian_restart=$($guardianRestart.detail) recovered_pid=$($recoveredAgent.ProcessId) screenshot_sha256=$((Get-FileHash -LiteralPath $enableShot -Algorithm SHA256).Hash)"

    $stableConsoles=@(Get-CimInstance Win32_Process|Where-Object Name -in $consoleNames|Where-Object { $candidate=$_;$snapshot=@(Get-CimInstance Win32_Process);$parent=[int]$candidate.ParentProcessId;$found=$false;for($depth=0;$depth-lt 16 -and $parent-ne 0;$depth++){if($parent-eq$actionHost.Id){$found=$true;break};$parentObject=$snapshot|Where-Object ProcessId -eq $parent|Select-Object -First 1;if($null-eq$parentObject){break};$parent=[int]$parentObject.ParentProcessId};$found })
    "TRANSIENT_CONSOLE_PROCESS_COUNT=$($transientConsolePids.Count)"
    "STABLE_CONSOLE_DESCENDANT_COUNT=$($stableConsoles.Count)"
    "VISIBLE_CONSOLE_WINDOW_COUNT=$($visibleConsolePids.Count)"
    if($stableConsoles.Count -ne 0 -or $visibleConsolePids.Count -ne 0){throw "T9 console-window gate failed."}

    Close-Host $actionHost $actionBaselinePython $actionBaselineHosts
    "ACTION_CLOSE_RESIDUAL=0"
    "T9_RUNTIME_PASS"
}
finally {
    foreach($process in $activeHosts){try{$process.Refresh();if(-not$process.HasExited){Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue}}catch{};$process.Dispose()}
}
