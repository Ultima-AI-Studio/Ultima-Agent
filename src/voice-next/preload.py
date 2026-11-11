"""开机预加载：等 Ollama 与音频端点就绪后，拉起 agent_server 与语音监听（含 CV3 语音预热）。

由计划任务 `UltimaAgent-Preload` 在用户登录后触发，用 pythonw 无窗运行。
- Ollama：等 11434 端口可连（模型服务通常晚于登录就绪）
- 音频端点：等 WASAPI 的输入/输出端点被枚举（开机初期驱动可能尚未加载）
- 拉起：调 launch.py，由它 ensure agent_server(8756) 并启动 live.py；live.py 的 worker 会
  在 serve(prewarm=True) 下预热 CV3，并把 4 句提示音重写成克隆音色
- live.py 自身 DETACHED 常驻，本脚本执行完即退出

结果写入 `data/voice-next/preload.json` 与 `data/voice-next/preload.log`。
"""
from __future__ import annotations

import json
import socket
import subprocess
import time
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
DATA = ROOT / "data/voice-next"
CONFIG = ROOT / "config/voice-next/live.json"
PY = ROOT / "tools/venv-voice-next/Scripts/python.exe"


def _stamp() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%S")


def _log(message: str) -> None:
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        with (DATA / "preload.log").open("a", encoding="utf-8") as handle:
            handle.write(f"{_stamp()} {message}\n")
    except OSError:
        pass


def _write(payload: dict) -> None:
    try:
        DATA.mkdir(parents=True, exist_ok=True)
        (DATA / "preload.json").write_text(
            json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8"
        )
    except OSError as exc:
        _log(f"write preload.json failed: {exc}")


def _wait_port(host: str, port: int, timeout: float) -> dict:
    started = time.monotonic()
    while time.monotonic() - started < timeout:
        try:
            with socket.create_connection((host, port), timeout=1):
                return {"ok": True, "seconds": round(time.monotonic() - started, 1)}
        except OSError:
            time.sleep(2)
    return {"ok": False, "error": "port not ready", "seconds": round(time.monotonic() - started, 1)}


def _endpoint_names() -> dict:
    spec = json.loads(CONFIG.read_text(encoding="utf-8"))
    return {
        "input": spec["input"]["name_contains"],
        "output": spec["output"]["name_contains"],
    }


def _wait_endpoints(timeout: float) -> dict:
    """等 WASAPI 输入/输出端点出现；开机初期驱动可能尚未枚举设备。"""
    started = time.monotonic()
    try:
        names = _endpoint_names()
    except (OSError, ValueError, KeyError) as exc:
        return {"ok": False, "error": f"config: {exc}"}
    try:
        import sounddevice as sd
    except Exception as exc:  # noqa: BLE001 - 记录后交给调用方判定
        return {"ok": False, "error": f"sounddevice: {exc}"}

    found: dict[str, int | None] = {}
    while time.monotonic() - started < timeout:
        devices = list(sd.query_devices())
        hostapis = list(sd.query_hostapis())
        found = {"input": None, "output": None}
        for direction, needle in names.items():
            for index, device in enumerate(devices):
                api_name = str(hostapis[device["hostapi"]]["name"]).lower()
                if "wasapi" not in api_name or needle.lower() not in str(device["name"]).lower():
                    continue
                channels = (
                    device["max_input_channels"]
                    if direction == "input"
                    else device["max_output_channels"]
                )
                if channels > 0:
                    found[direction] = index
                    break
        if found["input"] is not None and found["output"] is not None:
            return {"ok": True, "seconds": round(time.monotonic() - started, 1), **found}
        time.sleep(3)
    return {
        "ok": False,
        "error": "endpoints not enumerated",
        "seconds": round(time.monotonic() - started, 1),
        **found,
    }


def _run_launch(wait: float) -> dict:
    started = time.monotonic()
    _log("launch.py start")
    try:
        completed = subprocess.run(
            [
                str(PY),
                "-X",
                "utf8",
                str(Path(__file__).with_name("launch.py")),
                "--wait",
                str(int(wait)),
            ],
            cwd=ROOT,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=wait + 40,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
    except (OSError, subprocess.SubprocessError) as exc:
        _log(f"launch.py failed: {type(exc).__name__}: {exc}")
        return {"ok": False, "error": f"{type(exc).__name__}: {exc}"}
    payload: dict = {"ok": completed.returncode == 0, "exit_code": completed.returncode}
    for stream, label in ((completed.stdout, "stdout"), (completed.stderr, "stderr")):
        text = (stream or "").strip()
        if not text:
            continue
        payload[label] = text[-1200:]
        _log(f"launch.py {label}: {text[-400:]}")
    payload["seconds"] = round(time.monotonic() - started, 1)
    return payload


def _probe_agent(timeout: float = 120) -> dict:
    """探针：确认本地 8B 真的能回答（端口通不代表引擎可用）。

    agent_server 的引擎是懒探测的，ollama 尚未就绪时首次请求会报
    “No inference engine available”；这里用一次真实提问把这条链路打穿。
    """
    started = time.monotonic()
    opener = urllib.request.build_opener(urllib.request.ProxyHandler({}))
    body = json.dumps({"query": "你好"}).encode("utf-8")
    request = urllib.request.Request(
        "http://127.0.0.1:8756/ask",
        data=body,
        headers={"Content-Type": "application/json; charset=utf-8"},
        method="POST",
    )
    elapsed = lambda: round(time.monotonic() - started, 1)  # noqa: E731
    try:
        with opener.open(request, timeout=timeout) as response:
            payload = json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        return {
            "ok": False,
            "seconds": elapsed(),
            "code": exc.code,
            "error": exc.read().decode("utf-8", "replace")[:300],
        }
    except Exception as exc:  # noqa: BLE001 - 记录后由调用方判定
        return {"ok": False, "seconds": elapsed(), "error": f"{type(exc).__name__}: {exc}"}
    reply = str(payload.get("content", "")).strip()
    return {"ok": bool(reply), "seconds": elapsed(), "reply": reply[:60]}


def main() -> int:
    result: dict = {"started_at": _stamp(), "steps": {}}
    _log("preload start")

    result["steps"]["ollama"] = _wait_port("127.0.0.1", 11434, 240)
    _log(f"ollama: {result['steps']['ollama']}")

    result["steps"]["endpoints"] = _wait_endpoints(150)
    _log(f"endpoints: {result['steps']['endpoints']}")

    if result["steps"]["endpoints"].get("ok"):
        result["steps"]["launch"] = _run_launch(150)
        result["steps"]["agent_probe"] = _probe_agent()
        _log(f"agent_probe: {result['steps']['agent_probe']}")
        if not result["steps"]["agent_probe"].get("ok"):
            # 引擎未就绪时再走一次 launch（它会 ensure_agent，把 8756 拉回健康）
            _log("agent probe failed; retrying launch once")
            result["steps"]["launch_retry"] = _run_launch(90)
            result["steps"]["agent_probe_retry"] = _probe_agent()
            _log(f"agent_probe_retry: {result['steps']['agent_probe_retry']}")
    else:
        result["steps"]["launch"] = {"ok": False, "skipped": "endpoints unavailable"}
        _log("launch skipped: endpoints unavailable")

    probe = result["steps"].get("agent_probe_retry") or result["steps"].get("agent_probe") or {}
    result["finished_at"] = _stamp()
    result["ok"] = bool(result["steps"].get("launch", {}).get("ok")) and bool(probe.get("ok"))
    _write(result)
    _log(f"preload done ok={result['ok']}")
    print(json.dumps(result, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
