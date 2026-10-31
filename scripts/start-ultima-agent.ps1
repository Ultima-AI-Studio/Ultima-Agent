# ============================================================================
# Ultima Agent 一键启动器（本地常驻运行装配 v1）
# 作用：拉起 ollama LLM → agent_server(8756) → voice-listen-daemon(KWS/ASR/TTS)
#       → 打开四角壳界面（真数据模式，SSE=8756）
# 用法：powershell -ExecutionPolicy Bypass -File scripts\start-ultima-agent.ps1
# ============================================================================
param(
    [switch]$NoHud   # 仅启动服务，不打开四角壳界面
)

$root = "H:\UltimaAI\UltimaAgent"
$logDir = Join-Path $root "data\logs"
if (-not (Test-Path -LiteralPath $logDir)) { New-Item -ItemType Directory -Force -Path $logDir | Out-Null }

Write-Host "== Ultima Agent 一键启动 ==" -ForegroundColor Cyan

function Test-Port($port) {
    return [bool](Get-NetTCPConnection -LocalPort $port -State Listen -ErrorAction SilentlyContinue)
}

# ── 1. Ollama LLM（qwen3-8b-uncensored / 11434）──────────────────────────────────
if (Test-Port 11434) {
    Write-Host "[1/4] Ollama 已在运行 (11434)" -ForegroundColor Green
} else {
    Write-Host "[1/4] 启动 Ollama..." -ForegroundColor Yellow
    try {
        Start-Process -FilePath "ollama" -ArgumentList "serve" -WindowStyle Hidden -ErrorAction Stop
        Start-Sleep -Seconds 5
    } catch {
        Write-Host "      Ollama 启动命令失败（可能未在 PATH），尝试 ollama app..." -ForegroundColor DarkYellow
        try { Start-Process -FilePath "C:\Users\Administrator\AppData\Local\Programs\Ollama\ollama app.exe" -ErrorAction Stop } catch {}
    }
    if (-not (Test-Port 11434)) {
        Write-Host "      警告：11434 尚未就绪（Ollama 可能仍在启动中）" -ForegroundColor DarkYellow
    } else {
        Write-Host "      Ollama 就绪 (11434)" -ForegroundColor Green
    }
}

# ── 2. agent_server（SSE 出口 / 8756）────────────────────────────────────
if (Test-Port 8756) {
    Write-Host "[2/4] agent_server 已在运行 (8756)" -ForegroundColor Green
} else {
    Write-Host "[2/4] 启动 agent_server (8756)..." -ForegroundColor Yellow
    try {
        & (Join-Path $root "scripts\start-agent-server.ps1") 2>&1 | Out-Null
        Start-Sleep -Seconds 3
    } catch {
        Write-Host "      start-agent-server 调用失败: $_" -ForegroundColor Red
    }
    if (Test-Port 8756) {
        Write-Host "      agent_server 就绪 (8756)" -ForegroundColor Green
    } else {
        Write-Host "      8756 未就绪（看门狗 20s 周期会自动拉起，稍候即可）" -ForegroundColor DarkYellow
    }
}

# ── 3. voice-listen-daemon（KWS 唤醒 + ASR + TTS 回放）────────────────────
$voiceRunning = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'voice-listen-daemon' }
if ($voiceRunning) {
    Write-Host "[3/4] voice-listen-daemon 已在运行 (PID $($voiceRunning.ProcessId -join ','))" -ForegroundColor Green
} else {
    Write-Host "[3/4] 启动 voice-listen-daemon..." -ForegroundColor Yellow
    $pyAsr = Join-Path $root "tools\venv-asr\Scripts\pythonw.exe"
    if (-not (Test-Path -LiteralPath $pyAsr)) { $pyAsr = Join-Path $root "tools\venv-asr\Scripts\python.exe" }
    $daemon = Join-Path $root "data\logs\voice-listen-daemon.py"
    $outLog = Join-Path $logDir "voice-listen-daemon-out.log"
    $errLog = Join-Path $logDir "voice-listen-daemon-err.log"
    Start-Process -FilePath $pyAsr -ArgumentList @("-X","utf8",$daemon) `
        -WorkingDirectory $root -WindowStyle Hidden `
        -RedirectStandardOutput $outLog -RedirectStandardError $errLog
    Start-Sleep -Seconds 5
    $voiceNow = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'voice-listen-daemon' }
    if ($voiceNow) {
        Write-Host "      voice-listen-daemon 已拉起 (PID $($voiceNow.ProcessId -join ','))，KWS 模型加载约 30s 后进入监听" -ForegroundColor Green
    } else {
        Write-Host "      voice-listen-daemon 启动失败，详见 $errLog" -ForegroundColor Red
    }
}

# ── 4. 打开四角壳界面（原生壳 UltimaAgent.Hud.exe，SSE=8756 真数据）─────
if (-not $NoHud) {
    Write-Host "[4/4] 启动原生四角壳 UltimaAgent.Hud.exe..." -ForegroundColor Cyan
    $hudExe = Join-Path $root "dist\UltimaAgent.Hud\UltimaAgent.Hud.exe"
    if (Test-Path -LiteralPath $hudExe) {
        try { Start-Process -FilePath $hudExe -ErrorAction Stop }
        catch { Write-Host "      原生壳启动失败: $_" -ForegroundColor Red }
    } else {
        Write-Host "      未找到 $hudExe，回退浏览器打开四角壳 HTML" -ForegroundColor DarkYellow
        $hud = "file:///H:/UltimaAI/UltimaAgent/docs/previews/hud-live-four-corner/hud-live-four-corner.html"
        try { Start-Process $hud -ErrorAction Stop } catch { Start-Process "http://127.0.0.1:8756/health" }
    }
}

Write-Host ""
Write-Host "启动完成。唤醒词：贾维斯（KWS 就绪后即可语音对话）" -ForegroundColor Green
Write-Host "服务日志：$logDir" -ForegroundColor DarkGray
Write-Host "控制台关闭后服务仍在后台运行；如需停止全部服务，请使用任务栏托盘菜单「退出全部服务」。" -ForegroundColor DarkGray
