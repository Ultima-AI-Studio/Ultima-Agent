$ErrorActionPreference = "Stop"

$projectRoot = (Resolve-Path ".").Path
$exePath = Join-Path $projectRoot "src/host-shell/UltimaAgent.HostShell/bin/Release/net8.0-windows10.0.19041.0/win-x64/UltimaAgent.HostShell.exe"
$evidenceRoot = Join-Path $projectRoot "docs/reports/evidence/installer-phase3"
$orbLogPath = Join-Path $projectRoot "data/logs/orb-live-loop.txt"
$consoleNames = @("conhost.exe", "cmd.exe", "powershell.exe", "pwsh.exe")
$consoleBefore = @(Get-CimInstance Win32_Process | Where-Object Name -In $consoleNames | Select-Object -ExpandProperty ProcessId)
$newConsole = [System.Collections.Generic.HashSet[uint32]]::new()
$hostConsole = [System.Collections.Generic.HashSet[uint32]]::new()
$activeHostPids = [System.Collections.Generic.HashSet[uint32]]::new()
$consoleDetails = [System.Collections.Generic.List[string]]::new()

function Write-Status([string]$path, [string]$state, [int]$progress) {
    $json = @{ state = $state; warm_progress = $progress } | ConvertTo-Json -Compress
    [System.IO.File]::WriteAllText($path, $json + [Environment]::NewLine)
}

function Observe-ConsoleProcesses {
    $snapshot = @(Get-CimInstance Win32_Process)
    $snapshot | Where-Object {
        $_.Name -In $consoleNames -and $_.ProcessId -notin $consoleBefore
    } | ForEach-Object {
        $process = $_
        if ($newConsole.Add([uint32]$process.ProcessId)) {
            $consoleDetails.Add("pid=$($process.ProcessId) parent=$($process.ParentProcessId) name=$($process.Name) command=$($process.CommandLine)")
        }
        $parentId = [uint32]$process.ParentProcessId
        for ($depth = 0; $depth -lt 16 -and $parentId -ne 0; $depth++) {
            if ($activeHostPids.Contains($parentId)) {
                [void]$hostConsole.Add([uint32]$process.ProcessId)
                break
            }
            $parent = $snapshot | Where-Object ProcessId -eq $parentId | Select-Object -First 1
            if ($null -eq $parent) { break }
            $parentId = [uint32]$parent.ParentProcessId
        }
    }
}

function Start-Orb([string]$statusPath, [string]$evidenceDir, [bool]$enabled, [int]$exitMilliseconds) {
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new($exePath)
    $startInfo.WorkingDirectory = $projectRoot
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.Environment["ULTIMA_HOST_LIVE"] = "1"
    $startInfo.Environment["ULTIMA_USE_PROCESS_HOST"] = "false"
    $startInfo.Environment["ULTIMA_HOST_STATUS_FILE"] = $statusPath
    $startInfo.Environment["ULTIMA_HOST_EVIDENCE_DIR"] = $evidenceDir
    $startInfo.Environment["ULTIMA_HOST_LIVE_SECONDS"] = "3"
    $startInfo.Environment["ULTIMA_HOST_AUTO_EXIT_MS"] = [string]$exitMilliseconds
    $startInfo.Environment["ULTIMA_PROJECT_ROOT"] = $projectRoot
    $startInfo.Environment["ULTIMA_HOST_WRITE_ROOT"] = $projectRoot
    $startInfo.Environment["ULTIMA_HOST_WARM_RING"] = $(if ($enabled) { "1" } else { "0" })
    return [System.Diagnostics.Process]::Start($startInfo)
}

function Wait-ForFile([string]$path, [int]$seconds = 12) {
    $deadline = [DateTime]::UtcNow.AddSeconds($seconds)
    while ([DateTime]::UtcNow -lt $deadline) {
        Observe-ConsoleProcesses
        if (Test-Path -LiteralPath $path) { return }
        Start-Sleep -Milliseconds 100
    }
    throw "Timed out waiting for $path"
}

$onDir = Join-Path $evidenceRoot "t6-runtime-final-on"
$offDir = Join-Path $evidenceRoot "t6-runtime-final-off"
[System.IO.Directory]::CreateDirectory($onDir) | Out-Null
[System.IO.Directory]::CreateDirectory($offDir) | Out-Null
$onStatus = Join-Path $onDir "injected-status.json"
$offStatus = Join-Path $offDir "injected-status.json"

Write-Status $onStatus "warming" 25
$onProcess = Start-Orb $onStatus $onDir $true 6500
[void]$activeHostPids.Add([uint32]$onProcess.Id)
"ON_HOST_PID=$($onProcess.Id)"
foreach ($progress in @(25, 50, 75)) {
    if ($progress -ne 25) { Write-Status $onStatus "warming" $progress }
    $screenshot = Join-Path $onDir "warm-ring-$progress.png"
    Wait-ForFile $screenshot
    $hash = (Get-FileHash -Algorithm SHA256 -LiteralPath $screenshot).Hash
    "WARM_SCREENSHOT progress=$progress path=$screenshot sha256=$hash"
}
Write-Status $onStatus "ready" 100
$readyScreenshot = Join-Path $onDir "warm-ring-100.png"
Wait-ForFile $readyScreenshot
"WARM_SCREENSHOT progress=100 state=ready path=$readyScreenshot sha256=$((Get-FileHash -Algorithm SHA256 -LiteralPath $readyScreenshot).Hash)"
if (-not $onProcess.WaitForExit(12000)) { throw "Warm-ring host did not exit cleanly." }
"ON_HOST_EXIT=$($onProcess.ExitCode)"

$offLogStart = if (Test-Path -LiteralPath $orbLogPath) { @(Get-Content -LiteralPath $orbLogPath).Count } else { 0 }
Write-Status $offStatus "warming" 50
$offProcess = Start-Orb $offStatus $offDir $false 9000
[void]$activeHostPids.Add([uint32]$offProcess.Id)
"OFF_HOST_PID=$($offProcess.Id)"
$offScreenshot = Join-Path $offDir "a2-live-final.png"
Wait-ForFile $offScreenshot
"OFF_SCREENSHOT path=$offScreenshot sha256=$((Get-FileHash -Algorithm SHA256 -LiteralPath $offScreenshot).Hash)"
if (-not $offProcess.WaitForExit(12000)) { throw "Warm-ring-off host did not exit cleanly." }
"OFF_HOST_EXIT=$($offProcess.ExitCode)"

$onWarmEvents = @(Select-String -LiteralPath $orbLogPath -Pattern "WARM_PUSH" | Select-Object -Last 4)
$onWarmEvents | ForEach-Object { "EVENT=$($_.Line)" }
$offLogWarmCount = @((Get-Content -LiteralPath $orbLogPath | Select-Object -Skip $offLogStart) | Select-String -Pattern "WARM_PUSH").Count
"OFF_WARM_PUSH_COUNT=$offLogWarmCount"
"NEW_CONSOLE_PIDS=$([string]::Join(',', @($newConsole | Sort-Object)))"
$consoleDetails | ForEach-Object { "NEW_CONSOLE_DETAIL=$_" }
"HOST_DESCENDANT_CONSOLE_PIDS=$([string]::Join(',', @($hostConsole | Sort-Object)))"

if ($onProcess.ExitCode -ne 0 -or $offProcess.ExitCode -ne 0) { throw "A T6 HostShell run failed." }
if ($hostConsole.Count -ne 0) { throw "T6 HostShell spawned a console-window process." }
"T6_RUNTIME_PASS"
