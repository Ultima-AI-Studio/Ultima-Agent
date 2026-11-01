#requires -Version 7.0
# Prepare the isolated native KWS runtime without opening audio devices.
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$taskLock = Get-Content -LiteralPath (Join-Path $taskRoot 'config\voice-next\sherpa-kws.lock.json') -Raw | ConvertFrom-Json
$modelParent = Join-Path $taskRoot 'models\voice-next'
$modelDir = [IO.Path]::GetFullPath((Join-Path $taskRoot $taskLock.model_dir))
if (-not $modelDir.StartsWith($modelParent + '\', [StringComparison]::OrdinalIgnoreCase)) {
    throw 'Model destination escapes the new voice directory'
}
$archive = Join-Path $taskRoot ('tools\voice-next\' + $taskLock.name + '.tar.bz2')
New-Item -ItemType Directory -Force -Path (Split-Path $archive), $modelParent | Out-Null
if (-not (Test-Path -LiteralPath $archive)) {
    Invoke-WebRequest -Uri $taskLock.archive.url -Proxy $null -TimeoutSec 120 -OutFile $archive
}
if ((Get-FileHash -LiteralPath $archive -Algorithm SHA256).Hash.ToLowerInvariant() -ne $taskLock.archive.sha256) {
    throw 'Official archive checksum mismatch; file preserved for inspection'
}
& tar -xjf $archive -C $modelParent
if ($LASTEXITCODE -ne 0) { throw 'Model extraction failed' }
foreach ($entry in $taskLock.files.PSObject.Properties) {
    $path = [IO.Path]::GetFullPath((Join-Path $modelDir $entry.Name))
    if (-not $path.StartsWith($modelDir + '\', [StringComparison]::OrdinalIgnoreCase)) { throw 'Manifest path escapes model directory' }
    if ((Get-FileHash -LiteralPath $path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $entry.Value) {
        throw "Model checksum mismatch: $($entry.Name)"
    }
}
$python = Join-Path $taskRoot 'tools\venv-voice-next\Scripts\python.exe'
$proxyNames = @('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY')
$savedProxy = @{}
try {
    foreach ($proxyName in $proxyNames) {
        $savedProxy[$proxyName] = [Environment]::GetEnvironmentVariable($proxyName, 'Process')
        [Environment]::SetEnvironmentVariable($proxyName, $null, 'Process')
    }
    if (-not (Test-Path -LiteralPath $python)) {
        & uv venv --python (Join-Path $taskRoot 'tools\venv-openjarvis\Scripts\python.exe') (Split-Path (Split-Path $python))
        if ($LASTEXITCODE -ne 0) { throw 'Isolated environment creation failed' }
    }
    & uv pip install --python $python --index-url https://pypi.org/simple -r (Join-Path $PSScriptRoot 'requirements-live.lock.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Live dependency installation failed' }
} finally {
    foreach ($proxyName in $proxyNames) {
        [Environment]::SetEnvironmentVariable($proxyName, $savedProxy[$proxyName], 'Process')
    }
}
Write-Output 'Native streaming KWS prepared. Run launch.py to open microphone and playback.'
