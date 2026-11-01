# Ultima Agent 智能体服务器启动脚本
# 用法：powershell -ExecutionPolicy Bypass -File scripts\start-agent-server.ps1 [-Restart]
param(
    [switch]$Restart
)

$root = "H:\UltimaAI\UltimaAgent"
$py = Join-Path $root "tools\venv-openjarvis\Scripts\python.exe"
$server = Join-Path $root "src\brain\agent_server.py"
$logDir = Join-Path $root "data\logs"
$log = Join-Path $logDir "agent-server.log"
$outLog = Join-Path $logDir "agent-server-out.log"
$url = "http://127.0.0.1:8756/health"

if (-not (Test-Path -LiteralPath $py)) {
    Write-Error "底座 venv 不存在：$py"
    exit 1
}
if (-not (Test-Path -LiteralPath $server)) {
    Write-Error "服务器脚本不存在：$server"
    exit 1
}
if (-not (Test-Path -LiteralPath $logDir)) {
    New-Item -ItemType Directory -Force -Path $logDir | Out-Null
}

$existing = Get-NetTCPConnection -LocalPort 8756 -State Listen -ErrorAction SilentlyContinue
if ($existing) {
    if (-not $Restart) {
        Write-Output "服务器已在运行（PID $($existing.OwningProcess)），无需启动。"
        exit 0
    }
    Stop-Process -Id $existing.OwningProcess -Force
    Start-Sleep -Seconds 2
}

$argList = @("-X", "utf8", $server)
# web_search 底座：本机外网 you.com API 不可达（WinError 10060），30s 工具硬超时会在 fallback 前掐掉请求；
# 指定可达的 duckduckgo 引擎直连，避免 you.com 挂起耗尽超时预算（2026-11-01 实测）。
$env:OPENJARVIS_WEB_SEARCH_ENGINE = "duckduckgo"
Start-Process -FilePath $py -ArgumentList $argList -WorkingDirectory $root -WindowStyle Hidden -RedirectStandardError $log -RedirectStandardOutput $outLog

Start-Sleep -Seconds 5
try {
    $health = Invoke-RestMethod -Uri $url -TimeoutSec 10
    Write-Output "服务器已就绪：model=$($health.model) agent=$($health.agent) tools=$($health.tools.Count)"
    exit 0
} catch {
    Write-Error "服务器启动失败，请检查日志：$log"
    exit 1
}