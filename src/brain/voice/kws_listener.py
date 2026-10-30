# -*- coding: utf-8 -*-
"""Ultima Agent 语音入口：关键词唤醒（KWS）→ 对话回合 → TTS 回放。

与 live_mic.py（MVP 常驻 VAD 监听）的区别：本脚本先做唤醒词检测，
只有喊出「贾维斯 / ULTIMA」后才进入对话回合（录音→ASR→桥接→TTS 回放），
回放结束回到待唤醒态，不常驻应答。

用法（venv-asr 解释器运行）：
  tools\\venv-asr\\Scripts\\python.exe src\\brain\\voice\\kws_listener.py
"""
import os
import sys
import threading
import time
import wave
from pathlib import Path

ROOT = Path(r"H:\UltimaAI\UltimaAgent")
sys.path.insert(0, str(ROOT))

import numpy as np
import sounddevice as sd
import sherpa_onnx

from src.brain.voice_loop import VoiceInteractionLoop
from src.brain.voice.tts import tts_synthesize
from src.brain.voice.asr import asr_transcribe

# ── 路径/设备（与 live_mic.py 一致，真机已验证） ──────────────────
REAL_QUEUE = ROOT / "tasks"
CMD_FILE = ROOT / "data" / "host" / "orb_command.json"
REPLY_DIR = ROOT / "data" / "voice"
MIC_DIR = ROOT / "data" / "voice" / "mic"
MIC_DIR.mkdir(parents=True, exist_ok=True)

SR = 16000            # ASR/KWS 采样率
MIC_DEVICE = 1        # 输入：1=惠普 USB 麦克风（系统名 USBAudio2.0，MME index=1）。2026-10-29 摄像头(Razer Kiyo=3)拔除后切换；实测 6s 录音 peak=0.1173 且 ASR 完整识别"贾维斯查一下今天的天气"，拾音正常
PLAY_DEVICE = 26      # 输出：26=耳机 (POISON M@LOFREE)（sounddevice WASAPI 索引）
GAIN = 30.0           # 对话回合录音增益
MIN_LEN = 0.5         # 最短有效语音（秒）
END_SIL = 1.2         # 结束静音（秒）
CHUNK = 0.1           # 轮询块（秒）
MAX_LEN = 8.0         # 单段录音上限（秒）
_MIN_THR = 0.0040     # 触发阈值下限
_BASELINE_FRAMES = 20

# ── KWS 模型（sherpa-onnx zipformer 中英 KWS；参数对齐 voice-listen-daemon 2026-10-26 调优） ──
_KWS_DIR = ROOT / "models" / "sherpa" / "kws" / "sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20"
_KWS_ARGS = dict(
    tokens=str(_KWS_DIR / "tokens.txt"),
    encoder=str(_KWS_DIR / "encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx"),
    decoder=str(_KWS_DIR / "decoder-epoch-13-avg-2-chunk-8-left-64.onnx"),
    joiner=str(_KWS_DIR / "joiner-epoch-13-avg-2-chunk-8-left-64.int8.onnx"),
    keywords_file=str(ROOT / "models" / "sherpa" / "kws" / "keywords.txt"),
    num_threads=2,
    max_active_paths=8,
    keywords_score=1.0,
    # 2026-10-29 对齐 daemon DEFECT-008：说完即报，不等静音帧确认（防"第一遍听不见"）
    num_trailing_blanks=0,
    provider="cpu",
)
# 唤醒灵敏度（对齐 daemon 调优 0.08；调低更灵敏/易误报，可用 KWS_THRESHOLD 覆盖）
KWS_THRESHOLD = float(os.environ.get("KWS_THRESHOLD", "0.08"))


def _env_on(name: str, default: str = "on") -> bool:
    return os.environ.get(name, default).strip().lower() in {"1", "true", "yes", "on"}


def _bounded_env(name: str, default: float, low: float, high: float) -> float:
    return min(max(float(os.environ.get(name, str(default))), low), high)


KWS_VAD_GATE = _env_on("KWS_VAD_GATE")
KWS_VAD_ENERGY = _bounded_env("KWS_VAD_ENERGY", 0.005, 0.001, 0.05)
KWS_PRE_FILTER = _env_on("KWS_PRE_FILTER")
KWS_THRESH_MIN = _bounded_env("KWS_THRESH_MIN", 0.05, 0.0, 1.0)
KWS_THRESH_MAX = _bounded_env("KWS_THRESH_MAX", 0.15, 0.0, 1.0)
if KWS_THRESH_MIN > KWS_THRESH_MAX:
    raise ValueError("KWS_THRESH_MIN must not exceed KWS_THRESH_MAX")
_REARM_ENV = os.environ.get("KWS_REARM_THRESHOLD")
KWS_REARM_THRESHOLD = float(_REARM_ENV) if _REARM_ENV is not None else None

# ── 唤醒段自动增益（对齐 voice-listen-daemon 2026-10-26 调优） ──
# 解决弱电平 USB 麦（USBAudio2.0 约 0.007）唤醒词开头听不到的问题
_IDLE_GAIN = 4.0      # 静音期基础放大：唤醒词开头即有电平，避免第一遍听不到
_NOISE_GATE = 0.0015  # 低于此视为静音，不放大
_TARGET = 0.6         # 增益目标峰值
_MAX_GAIN = 30.0
_VOICE_START = 0.008  # 静音→有声跳变瞬时切满增益，唤醒词第一字不失真

loop = VoiceInteractionLoop(REAL_QUEUE, CMD_FILE, REPLY_DIR)


def _play_reply_wav(path: Path) -> None:
    """播放 TTS 生成的 WAV（设备采样率适配，与 live_mic.py 同逻辑）。"""
    with wave.open(str(path), "rb") as wf:
        rate = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    audio = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0
    target = int(sd.query_devices(PLAY_DEVICE)["default_samplerate"])
    if rate != target:
        idx = np.linspace(0, len(audio) - 1, int(len(audio) * target / rate))
        audio = np.interp(idx, np.arange(len(audio)), audio).astype(np.float32)
        rate = target
    sd.play(audio, rate, device=PLAY_DEVICE)
    sd.wait()


def warmup() -> None:
    """预热 TTS + ASR（首轮对话不卡冷启动）。

    2026-10-27 性能修复：原实现串行阻塞在主线程（TTS 合成 + ASR 识别 +
    KWS 构造三模型先后加载），启动瞬间 CPU 拉满；现由 main 放到后台线程，
    不阻塞进入 KWS_READY 监听态，失败不影响主流程。
    """
    try:
        warm = REPLY_DIR / "warmup-kws.wav"
        tts = tts_synthesize("查询任务状态", warm)
        if tts.get("ok"):
            r = asr_transcribe(warm)
            print(f"WARMUP_DONE asr_ok={r.get('ok')} text={r.get('text')!r}", flush=True)
        else:
            print(f"WARMUP_TTS_FAIL {tts}", flush=True)
    except Exception as exc:
        print(f"WARMUP_FAIL {exc!r}", flush=True)


# ── KWS 唤醒监听 ────────────────────────────────────────────────
class KwsListener:
    """流式关键词唤醒：**持续流**检测（对齐 voice-listen-daemon 10-26 真机验证命中路径）。

    2026-10-29 结构修复：原实现为"1s 窗口拼好→create_stream() 重建→一次性喂入+input_finished"，
    与 sherpa KWS 的流式模型语义不符（daemon 是 create_stream() 一次创建 → 0.2s 块持续
    accept_waveform → 持续 decode_stream → 命中 reset_stream 继续），导致模型判定不命中。
    现改为与 daemon 完全一致的持续流结构，保留自动增益与唤醒后对话流程。
    唤醒段自动增益（daemon 调优迁移）：静音期 IDLE_GAIN 基础放大 + 语音起始瞬时满增益 + 平滑爬升。"""

    def __init__(self, threshold: float = KWS_THRESHOLD):
        self._threshold = threshold
        self._reload_lock = threading.RLock()
        args = dict(_KWS_ARGS)
        args["keywords_threshold"] = threshold
        self.kws = sherpa_onnx.KeywordSpotter(**args)
        # 持续流：一次创建，逐块喂入，命中 reset 继续（daemon 10-26 验证路径）
        self._stream = self.kws.create_stream()
        self._chunk = int(0.2 * SR)   # 0.2s 块（daemon kws_chunk=3200 @16k）
        self._prev_gain = 1.0
        self._base_threshold = min(max(threshold, KWS_THRESH_MIN), KWS_THRESH_MAX)
        self._noise_energy = KWS_VAD_ENERGY
        self._pending_activity = False
        self._keywords = tuple(
            line.strip() for line in Path(_KWS_ARGS["keywords_file"]).read_text(encoding="utf-8").splitlines()
            if line.strip()
        )
        self._keywords_mtime_ns = self._keyword_mtime()
        self._failed_keywords_mtime_ns: int | None = None
        self.skip_vad_count = 0
        self.pre_filter_skip_count = 0
        self.pre_filter_pass_count = 0
        self.inference_count = 0

    @staticmethod
    def _keyword_mtime() -> int:
        try:
            return Path(_KWS_ARGS["keywords_file"]).stat().st_mtime_ns
        except OSError:
            return -1

    def reload_keywords(self) -> bool:
        """Build a replacement spotter first, then atomically swap it in."""
        args = dict(_KWS_ARGS)
        args["keywords_threshold"] = self._threshold
        try:
            replacement = sherpa_onnx.KeywordSpotter(**args)
            replacement_stream = replacement.create_stream()
            keywords = tuple(
                line.strip()
                for line in Path(_KWS_ARGS["keywords_file"]).read_text(encoding="utf-8").splitlines()
                if line.strip()
            )
        except Exception as exc:
            print(f"KWS_RELOAD_FAILED {exc!r}", flush=True)
            return False
        with self._reload_lock:
            self.kws = replacement
            self._stream = replacement_stream
            self._keywords = keywords
            self._keywords_mtime_ns = self._keyword_mtime()
            self._failed_keywords_mtime_ns = None
        print(f"KWS_RELOADED pid={os.getpid()} keywords={len(keywords)}", flush=True)
        return True

    def maybe_reload_keywords(self) -> bool:
        """Reload once when the keyword file mtime changes."""
        current = self._keyword_mtime()
        if current in {self._keywords_mtime_ns, self._failed_keywords_mtime_ns}:
            return False
        if self.reload_keywords():
            return True
        self._failed_keywords_mtime_ns = current
        return False

    @staticmethod
    def _log_count(event: str, count: int, detail: str = "") -> None:
        if count == 1 or count % 10 == 0:
            suffix = f" {detail}" if detail else ""
            print(f"{event} count={count}{suffix}", flush=True)

    def _detect(self, samples: np.ndarray) -> str:
        """持续流喂入一块（0.2s），命中返回关键词；未命中返回空串。
        对齐 daemon 10-26 验证路径：accept_waveform → is_ready 循环 decode_stream → get_result。"""
        with self._reload_lock:
            self.inference_count += 1
            self._stream.accept_waveform(SR, samples)
            while self.kws.is_ready(self._stream):
                self.kws.decode_stream(self._stream)
                result = self.kws.get_result(self._stream)
                if result != "":
                    self.kws.reset_stream(self._stream)
                    return result
        return ""

    @staticmethod
    def _pre_filter_passes(samples: np.ndarray, rms: float) -> tuple[bool, float]:
        if len(samples) < 2 or rms < KWS_VAD_ENERGY:
            return False, 0.0
        signs = np.signbit(samples)
        zcr = float(np.count_nonzero(signs[1:] != signs[:-1]) / (len(samples) - 1))
        return 0.005 <= zcr <= 0.45, zcr

    def _next_gain(self, peak: float) -> float:
        """daemon 自动增益：噪声门 + 语音起始跳变 + 平滑爬升（对齐 2026-10-26 调优）。"""
        if peak >= _NOISE_GATE:
            target_gain = min(_TARGET / max(peak, 1e-6), _MAX_GAIN)
            if self._prev_gain <= _IDLE_GAIN + 0.5 and peak >= _VOICE_START:
                gain = target_gain  # 语音起始跳变：瞬时满增益，唤醒词第一字不失真
            else:
                gain = self._prev_gain * 0.3 + target_gain * 0.7  # 平滑爬升
        else:
            gain = self._prev_gain * 0.5 + _IDLE_GAIN * 0.5  # 静音期保持基础放大，不回落 1.0
        self._prev_gain = gain
        return gain

    def feed(self, block: np.ndarray):
        """喂一块音频（float32 16k 单声道），自动增益后持续流喂入 KWS，命中返回关键词字符串，否则返回 None。
        对齐 daemon wait_wakeup 结构：不再做 1s 窗口拼接/重建流/REARM 二次确认。"""
        # sounddevice 返回 (N,1) 二维数组；sherpa accept_waveform 需要一维 (N,)
        if block.ndim > 1:
            block = block.flatten()
        block = block.astype(np.float32, copy=False)
        raw_rms = float(np.sqrt(np.mean(block ** 2))) if len(block) else 0.0
        if raw_rms >= KWS_VAD_ENERGY:
            self._pending_activity = True
        peak = float(np.abs(block).max())
        block = block * self._next_gain(peak)
        hit = self._detect(block)
        self._pending_activity = False
        if hit != "":
            self.pre_filter_pass_count += 1
            self._log_count("PRE_FILTER_PASS", self.pre_filter_pass_count, f"rms={raw_rms:.6f}")
            return hit
        return None


def _record_utterance(thr: float):
    """能量 VAD 录音一段语音（对话回合用），返回 WAV 路径。"""
    print("LISTENING_UTTERANCE ...", flush=True)
    frames = []
    talking = False
    sil = 0.0
    peak = 0.0
    while True:
        block = sd.rec(int(SR * CHUNK), samplerate=SR, channels=1, dtype="float32", device=MIC_DEVICE)
        sd.wait()
        rms = float(np.sqrt(np.mean(block ** 2)))
        peak = max(peak, rms)
        if not talking and rms > thr:
            talking = True
            frames.append(block)
        elif talking:
            frames.append(block)
            if rms > thr * 0.4:
                sil = 0.0
            else:
                sil += CHUNK
                if sil >= END_SIL:
                    break
    if not frames:
        return None
    if len(frames) * CHUNK > MAX_LEN:
        frames = frames[: int(MAX_LEN / CHUNK)]
    data = np.concatenate(frames)
    if len(data) < SR * MIN_LEN:
        print(f"TOO_SHORT peak={peak:.4f}", flush=True)
        return None
    data = np.clip(data * GAIN, -1.0, 1.0)
    pcm = (data.flatten() * 32767).astype(np.int16)
    wav = MIC_DIR / f"kws-{int(time.time())}.wav"
    with wave.open(str(wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(SR)
        wf.writeframes(pcm.tobytes())
    print(f"CAPTURED {wav.name} dur={len(data) / SR:.2f}s peak={peak:.4f}", flush=True)
    return wav


def _calibrate_threshold() -> float:
    """采集 2 秒背景噪声基线，阈值=基线×3 且不低于 _MIN_THR。"""
    levels = []
    for _ in range(_BASELINE_FRAMES):
        blk = sd.rec(int(SR * CHUNK), samplerate=SR, channels=1, dtype="float32", device=MIC_DEVICE)
        sd.wait()
        levels.append(float(np.sqrt(np.mean(blk ** 2))))
    base = float(np.percentile(levels, 40))
    thr = max(base * 3.0, _MIN_THR)
    print(f"CALIBRATE baseline={base:.4f} thr={thr:.4f} device={sd.default.device}", flush=True)
    return thr


def _single_instance() -> None:
    """单实例原子锁：同脚本已有存活进程时立即退出（防双开抢麦）。

    增强：锁内 PID 存活才视为占用；锁内 PID 已死视为残留并清理；
    创建竞争失败时重读锁再判定；进程退出时删除锁（atexit）。
    """
    import atexit
    import ctypes
    import tempfile

    lock = Path(tempfile.gettempdir()) / "ultima-kws-listener.pid"
    kernel32 = ctypes.windll.kernel32

    def _holder_alive() -> bool:
        try:
            old = int(lock.read_text().strip())
            h = kernel32.OpenProcess(0x1000, False, old)
            if h:
                kernel32.CloseHandle(h)
                return True
            return False
        except Exception:
            return False

    def _cleanup() -> None:
        # 仅当锁内容为本进程 PID 时才删除（防误删持锁者的锁）
        try:
            if lock.read_text().strip() == str(os.getpid()):
                lock.unlink(missing_ok=True)
        except Exception:
            pass

    atexit.register(_cleanup)

    if _holder_alive():
        print("EXIT_ALREADY_RUNNING", flush=True)
        sys.exit(0)
    # 残留死锁清理后重建
    try:
        lock.unlink(missing_ok=True)
    except Exception:
        pass
    try:
        fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        # 竞争失败：重读判定（若对方已死则抢占）
        if _holder_alive():
            print("EXIT_ALREADY_RUNNING", flush=True)
            sys.exit(0)
        try:
            lock.unlink(missing_ok=True)
            fd = os.open(str(lock), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
            os.write(fd, str(os.getpid()).encode())
            os.close(fd)
        except Exception:
            print("EXIT_ALREADY_RUNNING", flush=True)
            sys.exit(0)


def _heartbeat() -> None:
    """心跳刷新锁文件（主循环每轮调用，确保锁内容为当前存活 PID）。"""
    import tempfile

    lock = Path(tempfile.gettempdir()) / "ultima-kws-listener.pid"
    try:
        fd = os.open(str(lock), os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except Exception:
        pass


def main() -> None:
    _single_instance()
    if "--no-warmup" not in sys.argv:
        # 预热放后台线程：TTS/ASR 模型加载不阻塞进入监听态（启动峰值削峰）
        threading.Thread(target=warmup, daemon=True).start()

    listener = KwsListener(threshold=KWS_THRESHOLD)
    print(f"KWS_READY threshold={KWS_THRESHOLD} 说「贾维斯」唤醒", flush=True)
    while True:
        try:
            # 待唤醒态：持续流 InputStream（daemon 10-26 验证结构），命中后退出流
            with sd.InputStream(device=MIC_DEVICE, samplerate=SR, channels=1, dtype="int16") as mic:
                while True:
                    listener.maybe_reload_keywords()
                    data, _ = mic.read(listener._chunk)
                    f32 = data.astype(np.float32).reshape(-1) / 32768.0
                    _heartbeat()
                    hit = listener.feed(f32)
                    if hit:
                        print(f"WAKE_HIT {hit!r}", flush=True)
                        break
            # 唤醒后（已退出采集流）：校准（安静期）→ 录对话 → ASR → 桥接 → 回放
            time.sleep(0.3)
            thr = _calibrate_threshold()
            wav = _record_utterance(thr)
            if wav is None:
                print("WAKE_NO_UTTERANCE", flush=True)
                continue
            r = loop.handle_audio(wav)
            resp = r.get("response") or {}
            print(
                f"RESULT ok={r.get('ok')} stage={r.get('stage')} "
                f"text={r.get('text')!r} reason={resp.get('reason')} "
                f"seq={(r.get('pushed') or {}).get('seq')} "
                f"state={(r.get('pushed') or {}).get('state')} err={r.get('error')}",
                flush=True,
            )
            if r.get("reply_wav") and Path(r["reply_wav"]).is_file():
                _play_reply_wav(Path(r["reply_wav"]))
            print("KWS_BACK_TO_WAKE", flush=True)
        except KeyboardInterrupt:
            break
        except Exception as exc:
            print(f"ERR {exc!r}", flush=True)
            time.sleep(1)


if __name__ == "__main__":
    main()
