[CmdletBinding()]
param(
    [Parameter(Mandatory = $true, Position = 0)]
    [ValidateSet('dotnet', 'python')]
    [string]$Tool,

    [Parameter(Position = 1, ValueFromRemainingArguments = $true)]
    [string[]]$ToolArguments
)

$ErrorActionPreference = 'Stop'
$projectRoot = Split-Path -Parent $PSScriptRoot
$executables = @{
    dotnet = 'C:\Users\Administrator\.dotnet\dotnet.exe'
    python = Join-Path $projectRoot 'tools\python31313\python.exe'
}
$executable = $executables[$Tool]
if (-not (Test-Path -LiteralPath $executable -PathType Leaf)) {
    throw "Pinned $Tool executable is missing: $executable"
}

$startInfo = [System.Diagnostics.ProcessStartInfo]::new()
$startInfo.FileName = $executable
$startInfo.WorkingDirectory = $projectRoot
$startInfo.UseShellExecute = $false
$startInfo.CreateNoWindow = $true
$startInfo.WindowStyle = [System.Diagnostics.ProcessWindowStyle]::Hidden
$startInfo.RedirectStandardOutput = $true
$startInfo.RedirectStandardError = $true
foreach ($argument in $ToolArguments) {
    [void]$startInfo.ArgumentList.Add($argument)
}

$process = [System.Diagnostics.Process]::new()
$process.StartInfo = $startInfo
[void]$process.Start()
$stdoutTask = $process.StandardOutput.ReadToEndAsync()
$stderrTask = $process.StandardError.ReadToEndAsync()
$process.WaitForExit()
$stdout = $stdoutTask.GetAwaiter().GetResult()
$stderr = $stderrTask.GetAwaiter().GetResult()
if ($stdout) { [Console]::Out.Write($stdout) }
if ($stderr) { [Console]::Error.Write($stderr) }
exit $process.ExitCode
