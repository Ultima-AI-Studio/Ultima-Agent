"""SSE 演示服务直连验证：请求 /events 读前若干帧（3s 超时），打印收到的帧类型。"""
import json
import sys
import urllib.request

url = "http://127.0.0.1:8765/events?client_id=hud-corner&last_event_id="
req = urllib.request.Request(url, headers={"Accept": "text/event-stream"})
try:
    with urllib.request.urlopen(req, timeout=3) as resp:
        print("HTTP", resp.status, resp.headers.get("Content-Type"))
        buf = b""
        frames = []
        deadline = 0
        while len(frames) < 12:
            chunk = resp.read(1)
            if not chunk:
                break
            buf += chunk
            if buf.endswith(b"\n\n"):
                frame = buf.decode("utf-8", "replace")
                buf = b""
                frames.append(frame)
                lines = frame.splitlines()
                evt = next((l[7:] for l in lines if l.startswith("event:")), "?")
                data = next((l[6:] for l in lines if l.startswith("data:")), "")
                try:
                    payload = json.loads(data)
                    print(f"frame#{len(frames)} event={evt} type={payload.get('type')} data_keys={list(payload.get('data',{}).keys())[:6]}")
                except Exception:
                    print(f"frame#{len(frames)} event={evt} raw={data[:100]}")
except Exception as exc:
    print("SSE 直连失败:", exc)
    sys.exit(1)
