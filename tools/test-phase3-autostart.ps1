[CmdletBinding()]
param()

$ErrorActionPreference = "Stop"
[Console]::OutputEncoding = [System.Text.UTF8Encoding]::new($false)
$projectRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$hostExe = Join-Path $projectRoot "src/host-shell/UltimaAgent.HostShell/bin/Release/net8.0-windows10.0.19041.0/win-x64/UltimaAgent.HostShell.exe"
$startupDirectory = [Environment]::GetFolderPath([Environment+SpecialFolder]::Startup)
$shortcutPath = Join-Path $startupDirectory "UltimaAgent.lnk"
$processLogPath = Join-Path $projectRoot "data/logs/process-host.log"
$screenshotPath = Join-Path $projectRoot "docs/reports/evidence/installer-phase3/t8-shortcut-launch-no-console.png"
$knownZombiePids = @(24988, 22572)
$consoleNames = @("conhost.exe", "cmd.exe", "powershell.exe", "pwsh.exe")
$activeProcesses = [System.Collections.Generic.List[System.Diagnostics.Process]]::new()

try {
    Add-Type -AssemblyName System.Drawing.Common
}
catch {
    Add-Type -AssemblyName System.Drawing
}
Add-Type -TypeDefinition @'
using System;
using System.Runtime.InteropServices;
public static class UltimaAutostartWindow {
    [StructLayout(LayoutKind.Sequential)]
    public struct RECT { public int Left, Top, Right, Bottom; }
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool GetWindowRect(IntPtr hWnd, out RECT rect);
    [DllImport("user32.dll")]
    public static extern bool SetForegroundWindow(IntPtr hWnd);
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool PrintWindow(IntPtr hWnd, IntPtr hdcBlt, uint flags);
    [DllImport("user32.dll", SetLastError = true)]
    public static extern bool PostMessage(IntPtr hWnd, uint msg, IntPtr wParam, IntPtr lParam);
}
'@

function Get-UltimaTaskNames {
    $schtasksPath = Join-Path $env:SystemRoot "System32/schtasks.exe"
    $query = @(& $schtasksPath /query /v /fo csv 2>&1)
    if ($LASTEXITCODE -ne 0) { throw "schtasks query failed with exit $LASTEXITCODE." }
    $csvLines = @($query | Where-Object { $_ -is [string] -and $_.TrimStart().StartsWith('"') })
    $rows = @((($csvLines -join [Environment]::NewLine) | ConvertFrom-Csv))
    if ($rows.Count -eq 0) { return @() }
    $nameProperty = $rows[0].PSObject.Properties.Name[1]
    @($rows | ForEach-Object { [string]($_.$nameProperty) } |
        Where-Object { $_ -match "^\\?UltimaAgent" } | Sort-Object -Unique)
}

function Get-ProjectPythonPids {
    $escapedRoot = [regex]::Escape($projectRoot)
    @(Get-CimInstance Win32_Process | Where-Object {
        $_.Name -match "^python(w)?\.exe$" -and $_.CommandLine -match $escapedRoot -and
        $_.CommandLine -match "agent_server\.py|voice-next[\\/](launch|live|turn_worker)\.py"
    } | ForEach-Object { [int]$_.ProcessId })
}

function Get-CountableHostPids {
    @(Get-CimInstance Win32_Process -Filter "Name = 'UltimaAgent.HostShell.exe'" | Where-Object {
        $_.ProcessId -notin $knownZombiePids
    } | ForEach-Object { [int]$_.ProcessId })
}

function Get-Descendants([int]$rootProcessId, [string[]]$names = @()) {
    $snapshot = @(Get-CimInstance Win32_Process)
    $descendants = [System.Collections.Generic.List[object]]::new()
    foreach ($candidate in $snapshot) {
        if ($names.Count -gt 0 -and $candidate.Name -notin $names) { continue }
        $parentId = [int]$candidate.ParentProcessId
        for ($depth = 0; $depth -lt 16 -and $parentId -ne 0; $depth++) {
            if ($parentId -eq $rootProcessId) {
                $descendants.Add($candidate)
                break
            }
            $parent = $snapshot | Where-Object ProcessId -eq $parentId | Select-Object -First 1
            if ($null -eq $parent) { break }
            $parentId = [int]$parent.ParentProcessId
        }
    }
    @($descendants)
}

function Start-HostForAutostart([string]$kind, [int]$autoExitMilliseconds) {
    $startInfo = [System.Diagnostics.ProcessStartInfo]::new($hostExe)
    $startInfo.WorkingDirectory = $projectRoot
    $startInfo.UseShellExecute = $false
    $startInfo.CreateNoWindow = $true
    $startInfo.EnvironmentVariables["ULTIMA_PROJECT_ROOT"] = $projectRoot
    $startInfo.EnvironmentVariables["ULTIMA_HOST_EXE"] = $hostExe
    $startInfo.EnvironmentVariables["ULTIMA_AUTOSTART_KIND"] = $kind
    $startInfo.EnvironmentVariables["ULTIMA_USE_PROCESS_HOST"] = "false"
    $startInfo.EnvironmentVariables["ULTIMA_HOST_AUTO_EXIT_MS"] = [string]$autoExitMilliseconds
    $process = [System.Diagnostics.Process]::Start($startInfo)
    $activeProcesses.Add($process)
    if (-not $process.WaitForExit(15000)) { throw "HostShell autostart-$kind action timed out." }
    if ($process.ExitCode -ne 0) { throw "HostShell autostart-$kind action exited $($process.ExitCode)." }
}

function Read-Shortcut {
    $shellType = [Type]::GetTypeFromProgID("WScript.Shell")
    $shell = [Activator]::CreateInstance($shellType)
    try {
        $shortcut = $shell.CreateShortcut($shortcutPath)
        try {
            [pscustomobject]@{
                TargetPath = [string]$shortcut.TargetPath
                WorkingDirectory = [string]$shortcut.WorkingDirectory
                WindowStyle = [int]$shortcut.WindowStyle
            }
        }
        finally { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shortcut) }
    }
    finally { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shell) }
}

function Capture-Window([IntPtr]$windowHandle, [string]$path) {
    $rect = [UltimaAutostartWindow+RECT]::new()
    if (-not [UltimaAutostartWindow]::GetWindowRect($windowHandle, [ref]$rect)) {
        throw "GetWindowRect failed."
    }
    $width = $rect.Right - $rect.Left
    $height = $rect.Bottom - $rect.Top
    if ($width -le 0 -or $height -le 0) { throw "HostShell window has invalid bounds." }
    $bitmap = [System.Drawing.Bitmap]::new($width, $height)
    $graphics = [System.Drawing.Graphics]::FromImage($bitmap)
    try {
        $deviceContext = $graphics.GetHdc()
        try {
            if (-not [UltimaAutostartWindow]::PrintWindow($windowHandle, $deviceContext, 2)) {
                throw "PrintWindow failed."
            }
        }
        finally { $graphics.ReleaseHdc($deviceContext) }
        $bitmap.Save($path, [System.Drawing.Imaging.ImageFormat]::Png)
    }
    finally {
        $graphics.Dispose()
        $bitmap.Dispose()
    }
}

function Wait-PidsGone([int[]]$processIds, [int]$seconds = 3) {
    $deadline = [DateTime]::UtcNow.AddSeconds($seconds)
    do {
        $alive = @($processIds | Where-Object { Get-Process -Id $_ -ErrorAction SilentlyContinue })
        if ($alive.Count -eq 0) { return $true }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $deadline)
    return $false
}

try {
    if (-not (Test-Path -LiteralPath $hostExe)) { throw "Release HostShell executable is missing." }
    $tasksBefore = @(Get-UltimaTaskNames)
    "TASKS_BEFORE_COUNT=$($tasksBefore.Count)"

    Start-HostForAutostart "none" 500
    if (Test-Path -LiteralPath $shortcutPath) { throw "The none mode did not remove the shortcut." }

    Start-HostForAutostart "shortcut" 700
    if (-not (Test-Path -LiteralPath $shortcutPath)) { throw "Install did not create $shortcutPath." }
    $shortcut = Read-Shortcut
    "SHORTCUT_TARGET=$($shortcut.TargetPath)"
    "SHORTCUT_WORKING_DIRECTORY=$($shortcut.WorkingDirectory)"
    "SHORTCUT_WINDOW_STYLE=$($shortcut.WindowStyle)"
    if ([IO.Path]::GetFullPath($shortcut.TargetPath) -ne [IO.Path]::GetFullPath($hostExe)) { throw "Shortcut target mismatch." }
    if ([IO.Path]::GetFullPath($shortcut.WorkingDirectory) -ne [IO.Path]::GetFullPath($projectRoot)) { throw "Shortcut working directory mismatch." }
    if ($shortcut.WindowStyle -ne 1) { throw "Shortcut WindowStyle is not normal (1)." }

    Start-HostForAutostart "shortcut" 700
    $shortcutCount = @(Get-ChildItem -LiteralPath $startupDirectory -Filter "UltimaAgent*.lnk").Count
    "IDEMPOTENT_SHORTCUT_COUNT=$shortcutCount"
    if ($shortcutCount -ne 1) { throw "Repeated Install created $shortcutCount shortcuts." }

    $baselineHosts = @(Get-CountableHostPids)
    $baselinePython = @(Get-ProjectPythonPids)
    $logStart = if (Test-Path -LiteralPath $processLogPath) { @(Get-Content -LiteralPath $processLogPath).Count } else { 0 }
    $shellApplication = New-Object -ComObject Shell.Application
    try {
        $startupFolder = $shellApplication.NameSpace($startupDirectory)
        $shortcutItem = $startupFolder.ParseName("UltimaAgent.lnk")
        if ($null -eq $shortcutItem) { throw "Explorer could not resolve UltimaAgent.lnk." }
        $shortcutItem.InvokeVerb("open")
    }
    finally { [void][Runtime.InteropServices.Marshal]::FinalReleaseComObject($shellApplication) }

    $launchedHostPid = $null
    $deadline = [DateTime]::UtcNow.AddSeconds(15)
    while ([DateTime]::UtcNow -lt $deadline -and $null -eq $launchedHostPid) {
        $launchedHostPid = @(Get-CountableHostPids | Where-Object { $baselineHosts -notcontains $_ } | Select-Object -First 1)
        if ($launchedHostPid.Count -eq 0) { $launchedHostPid = $null; Start-Sleep -Milliseconds 100 }
        else { $launchedHostPid = [int]$launchedHostPid[0] }
    }
    if ($null -eq $launchedHostPid) { throw "Explorer activation did not create HostShell." }
    "EXPLORER_HOST_PID=$launchedHostPid"
    $launchedProcess = Get-Process -Id $launchedHostPid
    $activeProcesses.Add($launchedProcess)

    $observedVisibleConsole = [System.Collections.Generic.HashSet[int]]::new()
    $logLine = $null
    $deadline = [DateTime]::UtcNow.AddSeconds(15)
    while ([DateTime]::UtcNow -lt $deadline -and $null -eq $logLine) {
        foreach ($consoleProcess in @(Get-Descendants $launchedHostPid $consoleNames)) {
            $runtime = Get-Process -Id $consoleProcess.ProcessId -ErrorAction SilentlyContinue
            if ($null -ne $runtime -and $runtime.MainWindowHandle -ne [IntPtr]::Zero) {
                [void]$observedVisibleConsole.Add([int]$consoleProcess.ProcessId)
            }
        }
        if (Test-Path -LiteralPath $processLogPath) {
            $logLine = @(Get-Content -LiteralPath $processLogPath | Select-Object -Skip $logStart |
                Where-Object { $_ -match "started pid=|adopted=existing" } | Select-Object -First 1)
            if ($logLine.Count -eq 0) { $logLine = $null }
        }
        Start-Sleep -Milliseconds 100
    }
    if ($null -eq $logLine) { throw "Explorer-launched HostShell did not start the ProcessHost chain." }
    "PROCESS_HOST_EVENT=$logLine"

    $stableDeadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        $stableConsoles = @(Get-Descendants $launchedHostPid $consoleNames)
        foreach ($consoleProcess in $stableConsoles) {
            $runtime = Get-Process -Id $consoleProcess.ProcessId -ErrorAction SilentlyContinue
            if ($null -ne $runtime -and $runtime.MainWindowHandle -ne [IntPtr]::Zero) {
                [void]$observedVisibleConsole.Add([int]$consoleProcess.ProcessId)
            }
        }
        if ($stableConsoles.Count -eq 0) { break }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $stableDeadline)
    "STABLE_CONSOLE_DESCENDANT_COUNT=$($stableConsoles.Count)"
    "VISIBLE_CONSOLE_WINDOW_COUNT=$($observedVisibleConsole.Count)"
    if ($stableConsoles.Count -ne 0) { throw "Console descendants remained at acceptance time." }
    if ($observedVisibleConsole.Count -ne 0) { throw "A visible console window appeared." }

    $windowDeadline = [DateTime]::UtcNow.AddSeconds(10)
    do {
        $launchedProcess.Refresh()
        if ($launchedProcess.MainWindowHandle -ne [IntPtr]::Zero) { break }
        Start-Sleep -Milliseconds 100
    } while ([DateTime]::UtcNow -lt $windowDeadline)
    if ($launchedProcess.MainWindowHandle -eq [IntPtr]::Zero) { throw "Explorer HostShell window did not become visible." }
    Capture-Window $launchedProcess.MainWindowHandle $screenshotPath
    "SCREENSHOT=$screenshotPath SHA256=$((Get-FileHash -LiteralPath $screenshotPath -Algorithm SHA256).Hash)"

    $ownedPython = @(Get-ProjectPythonPids | Where-Object { $baselinePython -notcontains $_ })
    $relatedPids = @($ownedPython + $launchedHostPid | Select-Object -Unique)
    $closePosted = [UltimaAutostartWindow]::PostMessage(
        $launchedProcess.MainWindowHandle, 0x0010, [IntPtr]::Zero, [IntPtr]::Zero)
    if (-not $closePosted) { throw "WM_CLOSE failed for Explorer HostShell." }
    if (-not $launchedProcess.WaitForExit(15000)) { throw "Explorer HostShell did not exit after WM_CLOSE." }
    if (-not (Wait-PidsGone $relatedPids 3)) { throw "Explorer HostShell left ProcessHost PIDs behind." }
    "EXPLORER_WM_CLOSE=True RESIDUAL_PID_COUNT=0"

    Start-HostForAutostart "none" 500
    $residualShortcuts = @(Get-ChildItem -LiteralPath $startupDirectory -Filter "UltimaAgent*.lnk" -ErrorAction SilentlyContinue)
    "SHORTCUTS_AFTER_REMOVE=$($residualShortcuts.Count)"
    if ($residualShortcuts.Count -ne 0) { throw "Remove left UltimaAgent startup shortcuts." }

    $tasksAfter = @(Get-UltimaTaskNames)
    "TASKS_AFTER_COUNT=$($tasksAfter.Count)"
    if ($tasksAfter.Count -ne $tasksBefore.Count -or $tasksAfter.Count -ne 0) {
        throw "Scheduled task count changed: before=$($tasksBefore.Count), after=$($tasksAfter.Count)."
    }
    "AUTOSTART_RESULT=PASS"
    exit 0
}
catch {
    "AUTOSTART_RESULT=FAIL reason=$($_.Exception.Message -replace '\s+', '-')"
    exit 1
}
finally {
    foreach ($process in $activeProcesses) {
        try {
            $process.Refresh()
            if (-not $process.HasExited) { Stop-Process -Id $process.Id -Force -ErrorAction SilentlyContinue }
        }
        catch { }
        $process.Dispose()
    }
}
