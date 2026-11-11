# ============================================================================
# Ultima Agent 任务栏托盘（本地常驻运行装配 v1）
# 功能：托盘图标 + 菜单（打开四角壳 / 打开日志 / 退出全部服务 / 退出托盘）
# 运行：powershell -ExecutionPolicy Bypass -File scripts\ultima-agent-tray.ps1
#       或由桌面快捷方式 / 开机自启以隐藏窗口方式拉起
# 说明：托盘本体常驻，被杀后需重新拉起；「退出全部服务」停止 agent_server
#      + voice-listen-daemon（保留 ollama 与看门狗计划任务）。
# ============================================================================
$ErrorActionPreference = "SilentlyContinue"

Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$root = "H:\UltimaAI\UltimaAgent"
$logDir = Join-Path $root "data\logs"
$hudUrl = "file:///H:/UltimaAI/UltimaAgent/docs/previews/hud-live-four-corner/hud-live-four-corner.html"

# ── 图标：用 Pillow 生成一个 16x16 托盘图标（无 pystray 依赖）────────────
$icoPath = Join-Path $env:TEMP "ultima-agent-tray.ico"
$py = Join-Path $root "tools\venv-openjarvis\Scripts\python.exe"
$genCode = @'
from PIL import Image, ImageDraw
img = Image.new("RGBA", (16,16), (0,0,0,0))
d = ImageDraw.Draw(img)
# 外圈（青蓝盾形）+ 内芯（亮蓝）
d.ellipse([1,1,14,14], outline=(0,229,255,255), width=2)
d.ellipse([4,4,11,11], fill=(0,160,255,255))
img.save(r"__ICO__", format="ICO", sizes=[(16,16)])
'@
$genCode = $genCode.Replace("__ICO__", $icoPath.Replace("\", "\\"))
& $py -X utf8 -c $genCode 2>&1 | Out-Null

$trayIcon = New-Object System.Windows.Forms.NotifyIcon
$trayIcon.Text = "Ultima Agent"
if (Test-Path -LiteralPath $icoPath) {
    $trayIcon.Icon = [System.Drawing.Icon]::new($icoPath)
} else {
    $trayIcon.Icon = [System.Drawing.SystemIcons]::Application
}
$trayIcon.Visible = $true

# ── 菜单 ────────────────────────────────────────────────────────────────
$menu = New-Object System.Windows.Forms.ContextMenuStrip

$miOpenHud = New-Object System.Windows.Forms.ToolStripMenuItem
$miOpenHud.Text = "打开四角壳界面"
$miOpenHud.Add_Click({ Start-Process $hudUrl })

$miLogs = New-Object System.Windows.Forms.ToolStripMenuItem
$miLogs.Text = "打开日志目录"
$miLogs.Add_Click({ Start-Process $logDir })

$miStatus = New-Object System.Windows.Forms.ToolStripMenuItem
$miStatus.Text = "查看服务状态"
$miStatus.Add_Click({
    $lines = @()
    $p8756 = Get-NetTCPConnection -LocalPort 8756 -State Listen -ErrorAction SilentlyContinue
    if ($p8756) { $lines += "agent_server: 运行中 (PID $($p8756.OwningProcess))" } else { $lines += "agent_server: 未运行" }
    $p11434 = Get-NetTCPConnection -LocalPort 11434 -State Listen -ErrorAction SilentlyContinue
    if ($p11434) { $lines += "Ollama LLM: 运行中 (11434)" } else { $lines += "Ollama LLM: 未运行" }
    $v = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'voice-listen-daemon' }
    if ($v) { $lines += "语音监听: 运行中 (PID $($v.ProcessId -join ','))" } else { $lines += "语音监听: 未运行" }
    $w = Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'watchdog-loopguard' }
    if ($w) { $lines += "看门狗: 运行中 (PID $($w.ProcessId -join ','))" } else { $lines += "看门狗: 未运行" }
    [System.Windows.Forms.MessageBox]::Show(($lines -join "`n"), "Ultima Agent 服务状态")
})

$miStopAll = New-Object System.Windows.Forms.ToolStripMenuItem
$miStopAll.Text = "退出全部服务"
$miStopAll.Add_Click({
    $res = [System.Windows.Forms.MessageBox]::Show(
        "确认停止 Ultima Agent 全部服务？（agent_server + 语音监听，保留 Ollama）",
        "退出全部服务", [System.Windows.Forms.MessageBoxButtons]::OKCancel,
        [System.Windows.Forms.MessageBoxIcon]::Warning)
    if ($res -ne [System.Windows.Forms.DialogResult]::OK) { return }
    # 停止 agent_server（8756 监听者）
    Get-NetTCPConnection -LocalPort 8756 -State Listen -ErrorAction SilentlyContinue |
        ForEach-Object { Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue }
    # 停止语音入口实例（唯一入口 voice-next/live.py）
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'voice-next\\live\.py' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    # 停掉相关的 ASR/TTS 常驻子进程（ultima-voice daemon）
    Get-CimInstance Win32_Process | Where-Object { $_.CommandLine -match 'ultima-voice|daemon_asr|daemon_tts' } |
        ForEach-Object { Stop-Process -Id $_.ProcessId -Force -ErrorAction SilentlyContinue }
    Start-Sleep -Seconds 2
    [System.Windows.Forms.MessageBox]::Show("服务已停止。", "Ultima Agent")
})

$miExit = New-Object System.Windows.Forms.ToolStripMenuItem
$miExit.Text = "退出托盘"
$miExit.Add_Click({
    $trayIcon.Visible = $false
    $trayIcon.Dispose()
    [System.Windows.Forms.Application]::Exit()
})

$menu.Items.Add($miOpenHud) | Out-Null
$menu.Items.Add($miLogs) | Out-Null
$menu.Items.Add($miStatus) | Out-Null
$menu.Items.Add((New-Object System.Windows.Forms.ToolStripSeparator)) | Out-Null
$menu.Items.Add($miStopAll) | Out-Null
$menu.Items.Add($miExit) | Out-Null
$trayIcon.ContextMenuStrip = $menu

# 双击托盘 = 打开四角壳
$trayIcon.Add_MouseDoubleClick({
    if ($_.Button -eq [System.Windows.Forms.MouseButtons]::Left) { Start-Process $hudUrl }
})

# ── 事件循环 ────────────────────────────────────────────────────────────
[System.Windows.Forms.Application]::Run()
