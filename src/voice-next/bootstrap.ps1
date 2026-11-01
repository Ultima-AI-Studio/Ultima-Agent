# Reproducible offline-proof environment; never starts microphone or playback.
$ErrorActionPreference = 'Stop'
$taskRoot = [IO.Path]::GetFullPath((Join-Path $PSScriptRoot '..\..'))
$toolRoot = Join-Path $taskRoot 'tools\voice-next'
$sourceRoot = Join-Path $toolRoot 'source'
$environmentRoot = Join-Path $taskRoot 'tools\venv-voice-next'
$modelRoot = Join-Path $taskRoot 'models\voice-next\wekws-wenwen-fsmn-ctc'

function Confirm-Download([string]$Url, [string]$Path, [string]$Sha256) {
    if (-not (Test-Path -LiteralPath $Path)) {
        New-Item -ItemType Directory -Force -Path (Split-Path $Path) | Out-Null
        Invoke-WebRequest -Uri $Url -Proxy $null -TimeoutSec 120 -OutFile $Path
    }
    if ((Get-FileHash -LiteralPath $Path -Algorithm SHA256).Hash.ToLowerInvariant() -ne $Sha256.ToLowerInvariant()) {
        throw "Checksum mismatch; preserved for inspection: $Path"
    }
}

$archives = @(
    @{ Repo='wekws'; Commit='6a45aeb994dd81c0969ff877a5a7c46d60ed0c86'; File='wekws-6a45aeb.zip'; Hash='2a5167a20c9679e8b8a2656ea295fb4e25aa21601e1be04cab3c725409c0eaf6' },
    @{ Repo='wenet'; Commit='1a94771df418325fd335b0b53776f83d74a8111d'; File='wenet-1a94771.zip'; Hash='801d8b70210629ffe9b3696d7beddde58437bb370c3cd5f4b71eb570e9894c53' }
)
foreach ($archive in $archives) {
    $zipPath = Join-Path $toolRoot $archive.File
    Confirm-Download "https://codeload.github.com/wenet-e2e/$($archive.Repo)/zip/$($archive.Commit)" $zipPath $archive.Hash
    Expand-Archive -LiteralPath $zipPath -DestinationPath $sourceRoot -Force
}

New-Item -ItemType Directory -Force -Path $modelRoot | Out-Null
$modelLock = Join-Path $taskRoot 'config\voice-next\model.lock.json'
foreach ($entry in (Get-Content -LiteralPath $modelLock -Raw | ConvertFrom-Json)) {
    if ($entry.Type -ne 'blob') { continue }
    $destination = [IO.Path]::GetFullPath((Join-Path $modelRoot $entry.Path))
    if (-not $destination.StartsWith($modelRoot + '\', [StringComparison]::OrdinalIgnoreCase)) {
        throw 'Model path escapes isolated directory'
    }
    Confirm-Download "https://www.modelscope.cn/models/thuduj12/kws_wenwen_fsmn_ctc/resolve/$($entry.Revision)/$($entry.Path)" $destination $entry.Sha256
}
Copy-Item -LiteralPath $modelLock -Destination (Join-Path $modelRoot 'upstream-files.json') -Force

# Use unchanged upstream tokenizer modules without importing the unrelated ASR CLI.
$wenet = Join-Path $sourceRoot 'wenet-1a94771df418325fd335b0b53776f83d74a8111d'
$tokenizer = Join-Path $toolRoot 'tokenizer-only'
foreach ($packagePart in @('wenet', 'wenet\text', 'wenet\utils')) {
    $packageDir = Join-Path $tokenizer $packagePart
    New-Item -ItemType Directory -Force -Path $packageDir | Out-Null
    Set-Content -LiteralPath (Join-Path $packageDir '__init__.py') -Value '# Tokenizer-only packaging; algorithms copied unchanged from pinned WeNet.' -Encoding utf8
}
foreach ($module in @('wenet\text\char_tokenizer.py', 'wenet\text\base_tokenizer.py', 'wenet\utils\file_utils.py')) {
    Copy-Item -LiteralPath (Join-Path $wenet $module) -Destination (Join-Path $tokenizer $module) -Force
}
Copy-Item -LiteralPath (Join-Path $wenet 'LICENSE') -Destination (Join-Path $tokenizer 'LICENSE') -Force

# Change proxy variables only for this setup process, restoring them on exit.
$proxyNames = @('HTTP_PROXY','HTTPS_PROXY','ALL_PROXY')
$savedProxy = @{}
try {
    foreach ($proxyName in $proxyNames) {
        $savedProxy[$proxyName] = [Environment]::GetEnvironmentVariable($proxyName, 'Process')
        [Environment]::SetEnvironmentVariable($proxyName, $null, 'Process')
    }
    $python = Join-Path $environmentRoot 'Scripts\python.exe'
    if (-not (Test-Path -LiteralPath $python)) {
        & uv venv --python (Join-Path $taskRoot 'tools\venv-openjarvis\Scripts\python.exe') $environmentRoot
        if ($LASTEXITCODE -ne 0) { throw 'Failed to create isolated environment' }
    }
    & uv pip install --python $python --index-url https://pypi.org/simple -r (Join-Path $PSScriptRoot 'requirements.lock.txt')
    if ($LASTEXITCODE -ne 0) { throw 'Isolated dependency installation failed' }
} finally {
    foreach ($proxyName in $proxyNames) {
        [Environment]::SetEnvironmentVariable($proxyName, $savedProxy[$proxyName], 'Process')
    }
}
Write-Output 'Isolated WeKws offline-proof environment ready. Production voice service unchanged.'
