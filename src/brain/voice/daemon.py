"""UltimaAgent 语音模型常驻服务（T2 流畅度调校）。

问题基线（T2 前测）：
- TTS 每次合成经子进程冷启动加载 CosyVoice fp16 模型：约 63s/次（×2 = 126s）；
- ASR 每次识别经子进程冷启动加载 faster-whisper medium：约 17.8s/次；
- 意图/队列/汇报/悬浮球合计 < 0.02s。关键路径总耗时约 144.6s，瓶颈全在模型冷加载。

调校方案：TTS 与 ASR 各自一个常驻子进程，模型只加载一次，
通过 stdin 逐行 JSON 请求 / stdout 逐行 JSON 回复的协议复用推理。
接口签名不变：tts_synthesize / asr_transcribe 走「常驻优先、冷启动兜底」。

写域：仅 H:\\UltimaAI\\UltimaAgent\\ 内；不写 Topo Backup；子进程隐藏窗口。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import threading
import time
from pathlib import Path

_BRAIN_ROOT = Path(__file__).resolve().parent  # src/brain/voice
# 直跑入口（python daemon.py）时保证 src 包可导入（与 tts.py/asr.py 同款惯例）
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))
_VOICE_TMP = Path(__import__("tempfile").gettempdir()) / "ultima-voice"
_VOICE_TMP.mkdir(parents=True, exist_ok=True)

# ── 常驻脚本：TTS（CosyVoice fp16 / runtime310）──────────────────────────
_TTS_DAEMON_SCRIPT = r"""
import os, sys, json, threading
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("PYTHONNOUSERSITE", "1")

source = Path(r"{source}")
model = Path(r"{model}")
sys.path.insert(0, str(source))
sys.path.insert(0, str(source / "third_party" / "Matcha-TTS"))

import torch
torch.set_num_threads(1)
import numpy as np
import soundfile as sf
from cosyvoice.cli.cosyvoice import AutoModel

device = "cuda" if torch.cuda.is_available() else "cpu"
if device == "cpu":
    os.environ["CUDA_VISIBLE_DEVICES"] = ""
print(json.dumps({"ready": True, "device": device}), flush=True)

cosy = AutoModel(model_dir=str(model), load_trt=False, load_vllm=False, fp16=True)
print(json.dumps({"loaded": True}), flush=True)

def synthesize(text: str, out_wav: str, prompt_wav: str, prompt_text: str) -> dict:
    speech = None
    for block in cosy.inference_zero_shot(text, prompt_text, str(prompt_wav),
                                          stream=False, speed=1.0):
        speech = block["tts_speech"]
        break
    if speech is None:
        raise RuntimeError("no speech block produced")
    pcm = np.clip(speech.detach().cpu().numpy().reshape(-1), -1, 1)
    sf.write(out_wav, pcm, cosy.sample_rate, subtype="PCM_16")
    return {"ok": True, "wav": out_wav, "rate": cosy.sample_rate,
            "seconds": len(pcm) / cosy.sample_rate, "device": device,
            "engine": "cv3"}

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
        if req.get("op") == "synthesize":
            result = synthesize(
                req["text"], req["out"], req["prompt_wav"], req["prompt_text"]
            )
            print(json.dumps(result), flush=True)
        elif req.get("op") == "ping":
            print(json.dumps({"ok": True, "pong": True}), flush=True)
        elif req.get("op") == "stop":
            print(json.dumps({"ok": True, "stopped": True}), flush=True)
            break
        else:
            print(json.dumps({"ok": False, "error": "unknown-op"}), flush=True)
    except Exception as exc:  # 逐条失败不杀进程
        print(json.dumps({"ok": False, "error": str(exc)}), flush=True)
"""

# ── 常驻脚本：ASR（faster-whisper medium / venv-asr，CUDA）────────────────
_ASR_DAEMON_SCRIPT = r"""
import json, sys, os
from pathlib import Path

model_path = sys.argv[1]
from faster_whisper import WhisperModel

device = "cuda"
model = WhisperModel(model_path, device=device, compute_type="float16")
print(json.dumps({"loaded": True, "device": device}), flush=True)

for line in sys.stdin:
    line = line.strip()
    if not line:
        continue
    try:
        req = json.loads(line)
        if req.get("op") == "transcribe":
            wav = req["wav"]
            # 指令域提示：约束中文识别朝向任务指令类短语（与冷启动脚本 asr.py 参数对齐）；
            # 关闭 previous_text 串扰，避免上段文本污染本次识别。
            segments, info = model.transcribe(
                wav,
                language="zh",
                beam_size=5,
                initial_prompt="以下是中文语音指令。常用指令：查询任务状态、优先处理一号任务、插队、好的、确认、取消。",
                condition_on_previous_text=False,
            )
            text = " ".join(s.text.strip() for s in segments).strip()
            print(json.dumps({"ok": True, "text": text, "language": info.language,
                              "model": "faster-whisper-large-v3", "wav": wav}), flush=True)
        elif req.get("op") == "ping":
            print(json.dumps({"ok": True, "pong": True}), flush=True)
        elif req.get("op") == "stop":
            print(json.dumps({"ok": True, "stopped": True}), flush=True)
            break
        else:
            print(json.dumps({"ok": False, "error": "unknown-op"}), flush=True)
    except Exception as exc:
        print(json.dumps({"ok": False, "error": str(exc)}), flush=True)
"""


class VoiceDaemon:
    """单个常驻推理子进程：行协议（stdin 请求 / stdout 回复），幂等启动。

    崩溃自愈：进程不存在时下次调用自动重启；就绪超时可配。
    线程安全：锁保护请求-回复配对（子进程串行处理）。
    """

    def __init__(self, name: str, script: str, python: Path, args: list[str],
                 env: dict[str, str] | None = None, ready_timeout: float = 300.0):
        self.name = name
        self.script = script
        self.python = python
        self.args = list(args)
        self.env = dict(os.environ)
        if env:
            self.env.update(env)
        self.ready_timeout = ready_timeout
        self._proc: subprocess.Popen | None = None
        self._lock = threading.Lock()
        self._started_at: float | None = None

    @property
    def alive(self) -> bool:
        if self._proc is None:
            return False
        if self._proc.poll() is not None:
            return False
        return True

    def _write_script(self) -> Path:
        script_path = _VOICE_TMP / f"daemon_{self.name}.py"
        script_path.write_text(self.script, encoding="utf-8")
        return script_path

    # ── 跨进程单实例（2026-10-27 性能修复）────────────────────────────────
    # 原实现单例是"进程内"（_ASR_DAEMON/_TTS_DAEMON 全局），不同宿主进程
    # （kws_listener / agent_server / 测试进程）各自拉自己的 daemon 子进程，
    # 每个都驻留一份 large-v3/CosyVoice 大模型 → 每次测试进程累积、机器被吃满。
    # 现加锁文件：已有同名 daemon 存活时不再重复拉起（调用方走冷启动兜底）。
    def _lock_path(self) -> Path:
        return Path(__import__("tempfile").gettempdir()) / f"ultima-voice-daemon-{self.name}.pid"

    def _global_holder_alive(self) -> bool:
        """锁文件 pid 存活即视为已有同名 daemon 驻留（不重复拉起）。"""
        import ctypes

        try:
            old = int(self._lock_path().read_text().strip())
            kernel32 = ctypes.windll.kernel32
            h = kernel32.OpenProcess(0x1000, False, old)
            if h:
                kernel32.CloseHandle(h)
                return True
        except Exception:
            pass
        return False

    def _claim_global(self, pid: int) -> None:
        """拉起成功后登记 pid 到锁文件（供其他宿主识别）。"""
        try:
            self._lock_path().write_text(str(pid), encoding="utf-8")
        except Exception:
            pass

    def _release_global(self, pid: int) -> None:
        """终止后删除锁（仅当锁内容==本进程持有的 daemon pid，防误删他人锁）。"""
        try:
            lock = self._lock_path()
            if lock.read_text().strip() == str(pid):
                lock.unlink(missing_ok=True)
        except Exception:
            pass

    def _launch(self) -> subprocess.Popen:
        script_path = self._write_script()
        proc = subprocess.Popen(
            [str(self.python), "-X", "utf8", str(script_path), *self.args],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            encoding="utf-8",
            env=self.env,
            creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
        )
        self._proc = proc
        self._started_at = time.time()
        self._claim_global(proc.pid)
        return proc

    def ensure_started(self) -> bool:
        """确保进程存活且模型就绪（就绪 = 收到 {loaded} 标记，即模型已加载完成）。

        关键：不能只等 {ready}（启动标记）——脚本在模型加载完成前不会进入
        请求循环，提前返回会造成请求-回复串线。加载期间阻塞等待，超时终止。
        跨进程单实例：已有其他宿主持有同名 daemon 时不重复拉起，返回 False
        （调用方走冷启动兜底，一次性进程用后即退，不再 N 份驻留）。
        """
        with self._lock:
            if self.alive:
                return True
            if self._global_holder_alive():
                return False
            proc = self._launch()
            deadline = time.time() + self.ready_timeout
            while time.time() < deadline:
                line = proc.stdout.readline() if proc.stdout else ""
                if not line:
                    break
                try:
                    marker = json.loads(line.strip())
                except json.JSONDecodeError:
                    continue
                if marker.get("loaded"):
                    return True
                if marker.get("error"):
                    return False
            # 超时/EOF 未就绪：终止并报错
            self._stop_locked()
            return False

    def request(self, payload: dict, timeout: float = 300.0) -> dict:
        """发送一条请求并等待对应回复。进程失活时自动重启再发。"""
        with self._lock:
            if not self.alive and not self.ensure_started():
                return {"ok": False, "error": "daemon-not-ready"}
            proc = self._proc
            assert proc is not None and proc.stdin is not None and proc.stdout is not None
            line = json.dumps(payload, ensure_ascii=False)
            proc.stdin.write(line + "\n")
            proc.stdin.flush()
            # 读回复（串行协议：一条请求一条回复）
            reply = proc.stdout.readline()
            if not reply:
                return {"ok": False, "error": "daemon-read-eof"}
            try:
                return json.loads(reply.strip())
            except json.JSONDecodeError:
                return {"ok": False, "error": f"daemon-bad-json: {reply.strip()[:200]}"}

    def _stop_locked(self) -> None:
        if self._proc is None:
            return
        pid = self._proc.pid
        try:
            if self._proc.stdin is not None:
                self._proc.stdin.write(json.dumps({"op": "stop"}) + "\n")
                self._proc.stdin.flush()
        except Exception:
            pass
        try:
            self._proc.terminate()
        except Exception:
            pass
        try:
            self._proc.wait(timeout=5)
        except Exception:
            try:
                self._proc.kill()
            except Exception:
                pass
        self._proc = None
        self._release_global(pid)

    def stop(self) -> None:
        with self._lock:
            self._stop_locked()


# ── 全局单例 ──────────────────────────────────────────────────────────────
_TTS_DAEMON: VoiceDaemon | None = None
_ASR_DAEMON: VoiceDaemon | None = None


def _tts_daemon() -> VoiceDaemon | None:
    global _TTS_DAEMON
    if _TTS_DAEMON is None:
        from src.brain.voice.resources import (
            COSYVOICE_SOURCE,
            CV3_MODEL_ROOT,
            CV3_RUNTIME_PYTHON,
        )
        from src.brain.voice.tts import _VENDOR_DIR

        env = {"PYTHONPATH": str(_VENDOR_DIR)}
        script = _TTS_DAEMON_SCRIPT.replace("{source}", str(COSYVOICE_SOURCE))
        script = script.replace("{model}", str(CV3_MODEL_ROOT))
        _TTS_DAEMON = VoiceDaemon("tts", script, CV3_RUNTIME_PYTHON, [], env=env)
    return _TTS_DAEMON


def _asr_daemon() -> VoiceDaemon | None:
    global _ASR_DAEMON
    if _ASR_DAEMON is None:
        from src.brain.voice.asr import (
            _ASR_VENV_PYTHON,
            _FASTER_WHISPER_MODEL,
            _TORCH_LIB_DIR,
        )

        env = {}
        if _TORCH_LIB_DIR.is_dir():
            env["PATH"] = str(_TORCH_LIB_DIR) + os.pathsep + os.environ.get("PATH", "")
        _ASR_DAEMON = VoiceDaemon(
            "asr", _ASR_DAEMON_SCRIPT, _ASR_VENV_PYTHON,
            [str(_FASTER_WHISPER_MODEL)], env=env,
        )
    return _ASR_DAEMON


def daemon_tts_synthesize(
    text: str,
    out_wav: str | Path,
    timeout: float = 300.0,
    profile: dict | None = None,
) -> dict | None:
    """经常驻服务合成；服务不可用返回 None（调用方走冷启动兜底）。"""
    daemon = _tts_daemon()
    if daemon is None:
        return None
    try:
        from src.brain.voice.tts import resolve_prompt_pair
        from src.brain.voice.voice_profile import load_profile

        loaded = load_profile() if profile is None else profile
        prompt_wav, prompt_text = resolve_prompt_pair(loaded)
        if not daemon.ensure_started():
            return None
        result = daemon.request(
            {
                "op": "synthesize",
                "text": text,
                "out": str(out_wav),
                "prompt_wav": str(prompt_wav),
                "prompt_text": prompt_text,
            },
            timeout=timeout,
        )
        if result.get("ok"):
            result["daemon"] = True
        return result
    except Exception:
        return None


def daemon_asr_transcribe(wav: str | Path, timeout: float = 600.0) -> dict | None:
    """经常驻服务识别；服务不可用返回 None（调用方走冷启动兜底）。"""
    daemon = _asr_daemon()
    if daemon is None:
        return None
    try:
        if not daemon.ensure_started():
            return None
        result = daemon.request({"op": "transcribe", "wav": str(wav)}, timeout=timeout)
        if result.get("ok"):
            result["daemon"] = True
        return result
    except Exception:
        return None


def daemon_health() -> dict:
    """双服务健康状态（审计/诊断用）。"""
    status: dict = {}
    for name, fn in (("tts", _tts_daemon), ("asr", _asr_daemon)):
        daemon = fn()
        if daemon is None:
            status[name] = {"alive": False, "reason": "not-initialized"}
            continue
        try:
            if not daemon.alive:
                status[name] = {"alive": False, "reason": "not-running"}
                continue
            reply = daemon.request({"op": "ping"}, timeout=10)
            status[name] = {"alive": True, "ping": reply.get("ok", False)}
        except Exception as exc:
            status[name] = {"alive": False, "reason": str(exc)}
    return status


def stop_all() -> dict:
    """停止全部常驻服务（进程清理用）。"""
    result = {}
    for name in ("tts", "asr"):
        daemon = _tts_daemon() if name == "tts" else _asr_daemon()
        if daemon is not None:
            daemon.stop()
        result[name] = "stopped"
    return result


if __name__ == "__main__":  # pragma: no cover - 诊断入口
    import argparse

    parser = argparse.ArgumentParser(description="UltimaAgent 语音常驻服务管理")
    parser.add_argument("action", choices=["health", "stop", "warmup"],
                        help="health=探活 / stop=停止 / warmup=预热")
    args = parser.parse_args()
    if args.action == "health":
        print(json.dumps(daemon_health(), ensure_ascii=False, indent=2))
    elif args.action == "stop":
        print(json.dumps(stop_all(), ensure_ascii=False))
    elif args.action == "warmup":
        print(json.dumps({"tts": _tts_daemon().ensure_started() if _tts_daemon() else False,
                          "asr": _asr_daemon().ensure_started() if _asr_daemon() else False},
                         ensure_ascii=False))
