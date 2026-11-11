<#
.SYNOPSIS
    Replace a Windows venv's re-exec launcher with the base direct-run interpreter so
    detached subprocesses never create a visible console window, and make the venv
    self-contained by co-locating its runtime DLLs.

.DESCRIPTION
    The stdlib/uv venv launcher (python.exe ~253 KB, pythonw.exe ~249 KB) does not host
    the runtime itself. It CreateProcess-relaunches the base interpreter read from
    pyvenv.cfg. Under CREATE_NO_WINDOW|DETACHED_PROCESS the no-window flags are not
    propagated to that re-exec, so Windows allocates a visible conhost and the queue
    WindowMonitor flags VISIBLE_DESCENDANT_WINDOW.

    This script:
      1. reads the base interpreter directory from pyvenv.cfg (home key);
      2. backs up the original launchers once (*.venvlauncher.bak / *.venvwlauncher.bak);
      3. overwrites the venv launchers with the base direct-run interpreter;
      4. copies the runtime DLLs next to the interpreter so scheduled tasks (which do
         NOT inherit the interactive session's injected PATH) can start without
         0xC0000135 STATUS_DLL_NOT_FOUND;
      5. verifies venv semantics and a clean-PATH start.

    It is idempotent: re-running on an already-fixed venv changes nothing and still
    passes verification. Run it after (re)creating the venv, while no service is using
    the interpreter.

.PARAMETER VenvPath
    Path to the target venv. Defaults to tools\venv-openjarvis relative to the repo root.

.PARAMETER Verify
    Additionally run the project WindowMonitor window check (5 runs, expect 0 visible).

.EXAMPLE
    powershell -ExecutionPolicy Bypass -File scripts\fix-venv-launcher.ps1
    powershell -ExecutionPolicy Bypass -File scripts\fix-venv-launcher.ps1 -Verify
#>
[CmdletBinding()]
param(
    [string] $VenvPath = (Join-Path $PSScriptRoot "..\tools\venv-openjarvis"),
    [switch] $Verify
)

$ErrorActionPreference = "Stop"

$VenvPath = [IO.Path]::GetFullPath($VenvPath)
$scriptsDir = Join-Path $VenvPath "Scripts"
$cfgPath = Join-Path $VenvPath "pyvenv.cfg"

function Write-Step($m) { Write-Host "[fix-venv] $m" -ForegroundColor Cyan }
function Write-Ok($m)   { Write-Host "[fix-venv] $m" -ForegroundColor Green }

# 1. Locate the base interpreter via pyvenv.cfg ------------------------------------
if (-not (Test-Path -LiteralPath $cfgPath)) { throw "pyvenv.cfg not found: $cfgPath" }
$homeLine = Get-Content -LiteralPath $cfgPath | Where-Object { $_ -match "^\s*home\s*=" } | Select-Object -First 1
if (-not $homeLine) { throw "home key not found in pyvenv.cfg: $cfgPath" }
$baseDir = ($homeLine -split "=", 2)[1].Trim()
$basePython = Join-Path $baseDir "python.exe"
$basePythonw = Join-Path $baseDir "pythonw.exe"
if (-not (Test-Path -LiteralPath $basePython)) { throw "base python.exe not found: $baseDir" }
if (-not (Test-Path -LiteralPath $basePythonw)) { throw "base pythonw.exe not found: $baseDir" }
Write-Step "base interpreter: $baseDir"

# 2. Fail early with a clear message if a running service locks the files ----------
$venvPython = Join-Path $scriptsDir "python.exe"
$venvPythonw = Join-Path $scriptsDir "pythonw.exe"
foreach ($f in @($venvPython, $venvPythonw)) {
    if (-not (Test-Path -LiteralPath $f)) { throw "venv executable missing: $f" }
    try {
        $fs = [IO.File]::Open($f, "Open", "ReadWrite", "None")
        $fs.Close()
    } catch {
        throw "file is locked by a running process: $f. Stop the watchdog/agent_server (or run before starting services), then retry."
    }
}

# 3. Back up the original re-exec launchers once ----------------------------------
$basePyLen = (Get-Item -LiteralPath $basePython).Length
$curPyLen = (Get-Item -LiteralPath $venvPython).Length
if ($curPyLen -ne $basePyLen) {
    $bakPy = Join-Path $scriptsDir "python.exe.venvlauncher.bak"
    $bakPyw = Join-Path $scriptsDir "pythonw.exe.venvwlauncher.bak"
    if (-not (Test-Path -LiteralPath $bakPy)) { Copy-Item -LiteralPath $venvPython -Destination $bakPy }
    if (-not (Test-Path -LiteralPath $bakPyw)) { Copy-Item -LiteralPath $venvPythonw -Destination $bakPyw }
    Write-Step "backed up original launchers"
} else {
    Write-Step "launchers already replaced; backup left untouched"
}

# 4. Replace launchers with the direct-run interpreter ----------------------------
Copy-Item -LiteralPath $basePython -Destination $venvPython -Force
Copy-Item -LiteralPath $basePythonw -Destination $venvPythonw -Force
Write-Step "replaced launchers with direct-run interpreter"

# 5. Co-locate runtime DLLs so the venv is self-contained -------------------------
$dlls = @("python313.dll", "python3.dll", "vcruntime140.dll", "vcruntime140_1.dll")
foreach ($d in $dlls) {
    $src = Join-Path $baseDir $d
    if (Test-Path -LiteralPath $src) {
        Copy-Item -LiteralPath $src -Destination (Join-Path $scriptsDir $d) -Force
    } else {
        Write-Warning "runtime DLL not found in base, skipped: $d"
    }
}
Write-Step "co-located runtime DLLs"

# 6. Verify venv semantics ---------------------------------------------------------
$sem = & $venvPython -c "import sys; print(sys.prefix); print(sys.base_prefix); print(sys.executable)"
if ($sem[0].Trim() -ne $VenvPath) { throw "venv prefix mismatch: $($sem[0])" }
if ($sem[2].Trim() -ne $venvPython) { throw "venv executable mismatch: $($sem[2])" }
Write-Ok "venv semantics correct: prefix=$VenvPath"

# 7. Verify a clean-PATH (scheduled-task-like) start ------------------------------
$psi = New-Object System.Diagnostics.ProcessStartInfo
$psi.FileName = $venvPython
$psi.Arguments = '-c "import sys;print(''CLEAN_PATH_OK'')"'
$psi.UseShellExecute = $false
$psi.RedirectStandardOutput = $true
$psi.RedirectStandardError = $true
$psi.EnvironmentVariables["PATH"] = "C:\Windows\System32;C:\Windows"
$proc = [System.Diagnostics.Process]::Start($psi)
$cleanOut = $proc.StandardOutput.ReadToEnd().Trim()
$cleanErr = $proc.StandardError.ReadToEnd().Trim()
$proc.WaitForExit()
if ($proc.ExitCode -ne 0 -or $cleanOut -ne "CLEAN_PATH_OK") {
    throw "clean-PATH start failed rc=$($proc.ExitCode) err=$cleanErr"
}
Write-Ok "clean-PATH start works (self-contained, no injected PATH needed)"

# 8. Optional WindowMonitor check --------------------------------------------------
if ($Verify) {
    $repoRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot ".."))
    $probe = Join-Path $env:TEMP "fix-venv-window-check.py"
    @'
import os, subprocess, sys, time
from pathlib import Path
repo = Path(r"%REPO%")
sys.path.insert(0, str(repo))
from tasks.queue_engine.windows_runtime import WindowMonitor
flags = 0x08000000 | 0x00000008
exe = str(repo / "tools" / "venv-openjarvis" / "Scripts" / "python.exe")
visible = 0
for _ in range(5):
    mon = WindowMonitor(os.getpid()).start()
    p = subprocess.Popen([exe, "-c", "import time;time.sleep(0.7)"],
                         stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                         stderr=subprocess.DEVNULL, creationflags=flags, close_fds=True)
    p.wait()
    if mon.stop()["visible_windows"]:
        visible += 1
print("WINDOW_VISIBLE_RUNS=%d/5" % visible)
sys.exit(0 if visible == 0 else 1)
'@.Replace("%REPO%", $repoRoot) | Set-Content -LiteralPath $probe -Encoding ascii
    & $venvPython $probe
    if ($LASTEXITCODE -ne 0) { throw "window check failed" }
    Remove-Item -LiteralPath $probe -Force -ErrorAction SilentlyContinue
    Write-Ok "window check: 0/5 visible"
}

Write-Ok "done. venv is windowless and self-contained: $VenvPath"
