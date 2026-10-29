"""后台启动 Chrome headless 对四角壳真实数据模式截图，最多等待 N 秒。

Chrome 因 SSE 长连接不会自然退出，所以这里：
1. Start-Process 启动 chrome（headless=new, --screenshot）
2. 轮询截图文件是否生成且大小稳定
3. 超时后强制清理该 chrome 进程树
"""
import os
import signal
import subprocess
import sys
import time

CHROME = r"C:\Program Files\Google\Chrome\Application\chrome.exe"
URL = "file:///H:/UltimaAI/UltimaAgent/docs/previews/hud-live-four-corner/hud-live-four-corner.html?sse=8765"
OUT = r"H:\UltimaAI\UltimaAgent\docs\reports\evidence\sse-events-outlet\demo-four-corner-live.png"
WAIT = 40  # 秒

if os.path.exists(OUT):
    os.remove(OUT)

proc = subprocess.Popen(
    [CHROME, "--headless=new", "--disable-gpu", "--hide-scrollbars",
     "--window-size=1440,900", "--virtual-time-budget=6000",
     f"--screenshot={OUT}", URL],
    stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
)

try:
    deadline = time.time() + WAIT
    last_size = -1
    stable_since = 0.0
    while time.time() < deadline:
        if os.path.exists(OUT):
            size = os.path.getsize(OUT)
            if size > 0 and size == last_size:
                if stable_since == 0.0:
                    stable_since = time.time()
                if time.time() - stable_since >= 2:
                    print(f"截图完成: {OUT} size={size}")
                    break
            else:
                stable_since = 0.0
                last_size = size
        time.sleep(0.5)
    else:
        print("超时：截图文件未稳定")
        sys.exit(2)
finally:
    try:
        proc.terminate()
    except Exception:
        pass
    try:
        proc.kill()
    except Exception:
        pass
    # 清理该 chrome 进程树（--screenshot 模式会 fork 子进程）
    try:
        subprocess.run(["taskkill", "/PID", str(proc.pid), "/T", "/F"],
                       capture_output=True, timeout=10)
    except Exception:
        pass
