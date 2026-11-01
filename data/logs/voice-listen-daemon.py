# -*- coding: utf-8 -*-
"""常驻语音监听 daemon（唤醒词模式）：KWS 唤醒 → VAD 采集 → ASR(large-v3) → 桥接 → 悬浮球推送 → TTS 回放（LOFREE）。

用法（venv-asr python 后台运行）：
    pythonw voice-listen-daemon.py
交互节奏：
    [待唤醒] 流式 KWS 只响应唤醒词「贾维斯」（背景声不触发）→ 命中后进入指令采集
    [指令] 说话即停，语音结束后静音 1.2s 判定结束，最长 15s → ASR → 桥接 → 推送 → TTS 回放 → 回待唤醒
循环不退出；每轮结果写 JSON 到 voice-listen.log；异常捕获续跑。
"""
import sys, json, time, traceback, threading, os, queue
from dataclasses import dataclass, field
from pathlib import Path

try:
    sys.stdout.reconfigure(encoding="utf-8")
except (AttributeError, ValueError):
    pass
ROOT = Path(r"H:\UltimaAI\UltimaAgent")
sys.path.insert(0, str(ROOT))

from src.brain.voice._resample import mix_to_mono, resample_to_16k
from src.brain.voice.input_probe import resolve_input
from src.brain.voice.voice_profile import load_profile

LOG = ROOT / "data" / "logs" / "voice-listen.log"
OUT_DIR = ROOT / "data" / "voice" / "mic-regress"
OUT_DIR.mkdir(parents=True, exist_ok=True)
SR = 44100
SR_KWS = 16000
DEV_IN = 1     # 仅作探测失败/全静音时的内置回退；正常入口必须走 voice-profile + 自动探测
DEV_OUT = 5    # LOFREE 耳机 (POISON M@LOFREE)
MAX_SECONDS = 15.0
CHUNK = 1600
QUIET_AFTER_SPEECH = 1.2  # 2026-10-30 #132 回正基线（10-29 19:5x 曾 1.2→3.0 防"停顿组织指令被掐断"；本次回正同时补两段语义保护：静置期/未开口不判说完，见 collect()。3.0→1.2 省 ~1.8s/次，最终由 #134 VAD 断句(0.5s)接管）
BEEP_SETTLE_SEC = 1.2  # 静置期：语音引导"在呢，请说"阻塞播完(≈1.7s)后，再留 1.2s 防音箱残响被当语音；用户听到引导后开口的指令完整保留
ENERGY_TH = 0.008
KWS_MODEL = ROOT / "models" / "sherpa" / "kws" / "sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20"
KWS_KEYWORDS = ROOT / "models" / "sherpa" / "kws" / "keywords.txt"
VOICE_PROFILE = ROOT / "config" / "voice-profile.json"
ASR_RERUN_INTERVAL_SEC = 1.0
ASR_TIMEOUT_SEC = 600.0
_LOG_LOCK = threading.Lock()
_PLAYING = threading.Event()  # 播放互斥：播放期间暂停 KWS 采集，避免输出/输入并发欠载


@dataclass(frozen=True)
class AudioFrame:
    """One capture-thread frame with its monotonic acquisition timestamp."""

    captured_at: float
    data: object
    sample_rate: int


@dataclass
class CaptureState:
    frames: list = field(default_factory=list)
    sample_rate: int = SR
    started_at: float | None = None
    ended_at: float | None = None
    read_times: list[float] = field(default_factory=list)
    error: str | None = None


@dataclass
class RecognitionState:
    wav_path: Path | None = None
    asr: dict | None = None
    intermediate_asr: dict | None = None
    degraded: bool = False
    error: str | None = None
    rerun_count: int = 0


@dataclass
class CollectionResult:
    wav_path: Path | None
    asr: dict | None
    intermediate_asr: dict | None
    degraded: bool
    error: str | None
    rerun_count: int
    read_intervals_ms: tuple[float, ...]
    capture_thread_alive: bool
    recognition_thread_alive: bool


def log(msg: str) -> None:
    line = json.dumps({"t": time.strftime("%Y-%m-%d %H:%M:%S"), "msg": msg}, ensure_ascii=False)
    try:
        with _LOG_LOCK:
            with open(LOG, "a", encoding="utf-8") as f:
                f.write(line + "\n")
    except Exception:
        pass


def make_spotter():
    import sherpa_onnx
    return sherpa_onnx.KeywordSpotter(
        tokens=str(KWS_MODEL / "tokens.txt"),
        encoder=str(KWS_MODEL / "encoder-epoch-13-avg-2-chunk-8-left-64.int8.onnx"),
        decoder=str(KWS_MODEL / "decoder-epoch-13-avg-2-chunk-8-left-64.onnx"),
        joiner=str(KWS_MODEL / "joiner-epoch-13-avg-2-chunk-8-left-64.onnx"),
        keywords_file=str(KWS_KEYWORDS),
        num_threads=2,
        sample_rate=SR_KWS,
        max_active_paths=8,
        keywords_score=2.0,  # 2026-10-30 #133 提级 3.0 → 10-30 真机回归 08:09~08:10 五次强信号未命中（score 3.0 对「贾维斯」偏严，白龙马 3.0 系"小白龙"实测不适用），回退 2.0；离线 A/B 2.0/3.0 正负样本无差异（probe_kws_variant_ab2.py）
        keywords_threshold=0.08,  # 2026-10-30 #132 回正基线红线（10-29 19:2x 曾调低 0.04 补快语速召回；灵敏度改由 keywords_score 提级承担，见 #133）
        num_trailing_blanks=8,  # 2026-10-30 10-30 真机回归：score 2.0 下 08:21~08:22 三次强信号未命中（peak 0.0347~0.0432）才命中，间歇性漏唤醒。keywords.txt 6 个「贾维斯」变体 token 高度重叠（贾四声/贾一声/维轻声/斯轻声/吞尾音），sherpa-onnx 文档明确「keywords 有重叠 token 时应调大该值（如 8）」；0→8 按官方建议补变体间区分（见 kws-wakeup-params-baseline.md 第七节 2026-10-30 登记第 4 条）
        provider="cpu",
    )


class HotReloadSpotter:
    """Keep the old spotter alive unless a full replacement builds successfully."""

    def __init__(self, factory=make_spotter):
        self._factory = factory
        self.spotter = factory()
        self._keywords_mtime_ns = self._mtime(KWS_KEYWORDS)
        self._profile_mtime_ns = self._mtime(VOICE_PROFILE)
        self._failed_keywords_mtime_ns = None
        self._reload_events = queue.SimpleQueue()

    @staticmethod
    def _mtime(path: Path) -> int:
        try:
            return path.stat().st_mtime_ns
        except OSError:
            return -1

    def maybe_reload(self):
        profile_mtime = self._mtime(VOICE_PROFILE)
        if profile_mtime != self._profile_mtime_ns:
            self._profile_mtime_ns = profile_mtime
            profile_custom = None
            try:
                from src.brain.voice.voice_profile import apply_to_daemon, load_profile

                profile = load_profile()
                profile_custom = profile["wakeword"].get("custom")
                profile_applied = apply_to_daemon(profile)
                if not profile_applied:
                    log("voice-profile 变更同步失败，保留旧 spotter")
                self._reload_events.put({
                    "type": "profile_applied",
                    "success": bool(profile_applied),
                    "mtime_ns": profile_mtime,
                    "pid": os.getpid(),
                    "custom": profile_custom,
                })
            except Exception:
                log("voice-profile 变更同步异常，保留旧 spotter: " + traceback.format_exc()[-300:])
                self._reload_events.put({
                    "type": "profile_applied",
                    "success": False,
                    "mtime_ns": profile_mtime,
                    "pid": os.getpid(),
                    "custom": profile_custom,
                })

        keywords_mtime = self._mtime(KWS_KEYWORDS)
        if keywords_mtime in {self._keywords_mtime_ns, self._failed_keywords_mtime_ns}:
            return self.spotter
        old = self.spotter
        try:
            replacement = self._factory()
            replacement.create_stream()  # fully initialize before swapping
        except Exception:
            self._failed_keywords_mtime_ns = keywords_mtime
            log("KWS keywords 热重载失败，保留旧 spotter: " + traceback.format_exc()[-300:])
            self._reload_events.put({
                "type": "keywords_reloaded",
                "success": False,
                "mtime_ns": keywords_mtime,
                "pid": os.getpid(),
            })
            return old
        self.spotter = replacement
        self._keywords_mtime_ns = keywords_mtime
        self._failed_keywords_mtime_ns = None
        log(f"KWS keywords 热重载成功 pid={os.getpid()} mtime_ns={keywords_mtime}")
        self._reload_events.put({
            "type": "keywords_reloaded",
            "success": True,
            "mtime_ns": keywords_mtime,
            "pid": os.getpid(),
        })
        return replacement

    def drain_reload_events(self) -> list[dict]:
        events = []
        while True:
            try:
                events.append(self._reload_events.get_nowait())
            except queue.Empty:
                return events


class AudioCapture:
    """Open one physical endpoint at 44.1/48 kHz and expose mono int16 frames."""

    def __init__(self, sounddevice_module=None):
        self._sd = sounddevice_module
        self._stream = None
        self._active_stream = None
        self.device_index: int | None = None
        self.hostapi = "unknown"
        self.samplerate = SR
        self.channels = 1

    def open(self, device_index: int, hostapi: str | None, samplerate: int | None):
        if self._sd is None:
            import sounddevice as sd

            self._sd = sd
        device = self._sd.query_devices(device_index)
        native_rate = int(round(float(device.get("default_samplerate") or SR)))
        requested_rate = int(samplerate) if samplerate else native_rate
        self.samplerate = 48000 if requested_rate == 48000 else SR
        max_channels = int(device.get("max_input_channels", 0))
        if max_channels <= 0:
            raise ValueError(f"device {device_index} has no input channels")
        self.channels = 2 if self.samplerate == 48000 and max_channels >= 2 else 1
        self.device_index = int(device_index)
        self.hostapi = hostapi or "unknown"
        self._stream = self._sd.InputStream(
            device=self.device_index,
            samplerate=self.samplerate,
            channels=self.channels,
            dtype="int16",
        )
        return self

    def __enter__(self):
        if self._stream is None:
            raise RuntimeError("AudioCapture.open() must be called before entering")
        self._active_stream = self._stream.__enter__()
        return self

    def __exit__(self, exc_type, exc, traceback_obj):
        try:
            if self._stream is not None:
                return self._stream.__exit__(exc_type, exc, traceback_obj)
        finally:
            self._active_stream = None
        return None

    def read(self, frames: int):
        if self._active_stream is None:
            raise RuntimeError("AudioCapture is not active")
        import numpy as np

        data, overflowed = self._active_stream.read(frames)
        mono = mix_to_mono(np.asarray(data, dtype=np.float32))
        mono_i16 = np.clip(np.rint(mono), -32768, 32767).astype(np.int16).reshape(-1, 1)
        return mono_i16, overflowed


def open_audio_capture(
    device_index: int | None = None,
    hostapi: str | None = None,
    samplerate: int | None = None,
) -> AudioCapture:
    """Build a capture using endpoint capabilities instead of a fixed device format."""
    import sounddevice as sd

    if device_index is None:
        selected = select_input_config()
        device_index = int(selected["index"])
        hostapi = str(selected["hostapi"])
        samplerate = int(round(float(selected["default_samplerate"])))
    index = int(device_index)
    device = sd.query_devices(index)
    if hostapi is None:
        try:
            hostapi = str(sd.query_hostapis()[int(device["hostapi"])]["name"])
        except (IndexError, KeyError, TypeError):
            hostapi = "unknown"
    native_rate = int(round(float(device.get("default_samplerate") or SR)))
    return AudioCapture(sd).open(index, hostapi, samplerate or native_rate)


def select_input_config() -> dict:
    """Resolve the L2 profile or bounded automatic probe exactly once at startup."""
    profile = load_profile()
    return resolve_input(profile.get("input"), DEV_IN, log_fn=log)


def _dispatch_wakeword_notifications(loop, spotter_manager: HotReloadSpotter) -> None:
    for event in spotter_manager.drain_reload_events():
        loop.notify_wakeword_reload(event)
    completion = loop.poll_wakeword_completion()
    if completion is None:
        return
    log("wakeword-change completion: " + json.dumps(completion, ensure_ascii=False))
    reply = completion.get("reply_wav")
    if reply and Path(reply).is_file():
        threading.Thread(target=_play_safe, args=(Path(reply),), daemon=True).start()
        log("wakeword-change async-play: " + str(reply))


def wait_wakeup(spotter_manager: HotReloadSpotter, input_config: dict, loop=None) -> str | None:
    """待唤醒态：44.1/48k 采集 → 共享降采样 16k → KWS（增益基线不变）。
    2026-10-29 修复：MME 驱动不支持以 16000Hz 打开惠普麦（USBAudio2.0），
    16k 流信号全零导致"喊不醒"；改为 44.1k 原生采集后插值降采样喂 KWS。
    返回命中关键词名；异常返回 None。"""
    import numpy as np
    spotter = spotter_manager.spotter
    stream_obj = spotter.create_stream()
    env_log = time.time()
    prev_gain = 1.0
    TARGET = 0.6     # 增益目标峰值
    NOISE_GATE = 0.0015  # 低于此视为静音，不放大
    MAX_GAIN = 30.0
    IDLE_GAIN = 4.0     # 静音期基础放大：唤醒词开头即有电平，避免第一遍听不到
    VOICE_START = 0.008  # 语音起始判定：静音→有声 跳变瞬时切满增益
    WAKE_ACT_PEAK = 0.003  # 语音活动电平下限（近窗口确认用）
    WAKE_ACT_MIN = 1       # 近 5 块中至少 1 块达到活动电平即可（"贾维斯"仅 0.3~0.6s，加密后可能仅 1-2 块达峰；0.003 门槛已过滤噪声）
    peak_ring: list[float] = []  # 近 1s（5 块）原始 peak 环形窗口
    diag_log = 0.0
    with open_audio_capture(
        int(input_config["index"]),
        str(input_config["hostapi"]),
        int(round(float(input_config["default_samplerate"]))),
    ) as stream:
        kws_chunk = int(round(stream.samplerate * 0.2))
        log(
            f"KWS 采集打开: idx={stream.device_index} hostapi={stream.hostapi} "
            f"sr={stream.samplerate} input_ch={stream.channels} output_ch=1"
        )
        while True:
            if _PLAYING.is_set():
                time.sleep(0.05)  # 播放期间不读采集流：输入/输出并发是长回复欠载根因（L31）
                continue
            replacement = spotter_manager.maybe_reload()
            if loop is not None:
                _dispatch_wakeword_notifications(loop, spotter_manager)
            if replacement is not spotter:
                spotter = replacement
                stream_obj = spotter.create_stream()
                peak_ring.clear()
                log("KWS 流已切换到热重载 spotter")
            data, _ = stream.read(kws_chunk)
            f32 = data.astype(np.float32).reshape(-1) / 32768.0
            peak = np.abs(f32).max()
            peak_ring.append(peak)
            if len(peak_ring) > 5:
                peak_ring.pop(0)
            now = time.time()
            if now - env_log >= 15:
                env_log = now
                log(f"kws 环境电平: peak={peak:.4f} gain={prev_gain:.1f}")
            # 2026-10-29 19:5x 诊断：强信号但KWS无结果时打日志（每5s一条），
            # 区分"没收到音"vs"收到音但KWS没识别"。
            if peak >= 0.005 and now - diag_log >= 5:
                diag_log = now
                log(f"kws 强信号未命中: peak={peak:.4f} ring={[f'{p:.4f}' for p in peak_ring]}")
            if peak >= NOISE_GATE:
                target_gain = min(TARGET / max(peak, 1e-6), MAX_GAIN)
                if prev_gain <= IDLE_GAIN + 0.5 and peak >= VOICE_START:
                    gain = target_gain  # 语音起始跳变：瞬时满增益，唤醒词第一字不失真
                else:
                    gain = prev_gain * 0.3 + target_gain * 0.7  # 平滑爬升
            else:
                gain = prev_gain * 0.5 + IDLE_GAIN * 0.5  # 静音期保持基础放大，不回落 1.0
            prev_gain = gain
            f32 = f32 * gain
            stream_obj.accept_waveform(SR_KWS, resample_to_16k(f32, stream.samplerate))
            while spotter.is_ready(stream_obj):
                spotter.decode_stream(stream_obj)
                r = spotter.get_result(stream_obj)
                if r != "":
                    # 2026-10-29 有效命中确认：近 1s 窗口（5 块）内 ≥2 块原始 peak ≥
                    # WAKE_ACT_PEAK 才视为真实唤醒。真实语音连续多块（弱语音亦满足），
                    # 环境噪音误报多为单块瞬时。命中日志的 peak 是语音结束后的静音块，
                    # 单块门控会误杀真实命中（10-26 验证命中 peak≈0.0000~0.0034），故不用单块门控。
                    active = sum(1 for p in peak_ring if p >= WAKE_ACT_PEAK)
                    if active < WAKE_ACT_MIN:
                        spotter.reset_stream(stream_obj)
                        log(f"kws 误报抑制: {r} active={active}/5 peak_ring={[f'{p:.4f}' for p in peak_ring]}（语音活动不足，忽略）")
                        continue
                    spotter.reset_stream(stream_obj)
                    log(f"wakeup: 命中 {r} peak={peak:.4f} gain={gain:.1f} active={active}/5")
                    # 2026-10-29 19:2x 唤醒反馈：阻塞播放引导语"在呢，请说"（用户听到人声即知系统
                    # 已醒、随后开口说指令），播完再进 collect()。不用后台线程：否则音箱回声被
                    # USB 麦拾到，采集把引导声当语音、用户听到引导才开口反而错位。
                    beep = OUT_DIR / "wake-prompt.wav"
                    if not beep.is_file():
                        beep = OUT_DIR / "wake-beep.wav"  # 原 mp3 缺失导致唤醒后无提示音，用户误以为"没唤醒"
                    if not beep.is_file():
                        beep = OUT_DIR / "wake-beep.mp3"
                    if beep.is_file():
                        try:
                            play_wav(beep)
                        except Exception:
                            log("提示音播放失败: " + traceback.format_exc()[-200:])
                    return r
    return None


def warmup() -> None:
    """完整链路冷启动预热（2026-10-30 扩展：ASR + Agent(14B) + TTS 三段）。

    用户真机反馈（19:40/19:41 两轮）：唤醒/识别/意图/回复全对，但重启后首轮
    elapsed=68.19s（全链路冷启动）、热机 18.17s 仍不可接受，体感"答应了却没动静"。
    此前仅预热 ASR（5.9s）。现按用户同意扩展为完整链路预热：
      ① ASR large-v3 daemon（原有，synth-query.wav 样本）；
      ② Agent agent_server 8756：health + 一次"查询任务状态"级轻量 ask（触发 14B
         首 token 加载，避免首轮 Agent 推理冷启动）；
      ③ TTS 按 profile engine 预热：sherpa → MeloTTS 模型加载 + 一次短文本合成；
         cv3 → daemon TTS ensure_started + 一次合成。预热样本落到 tools/ 探针域，
         不进入 reply 队列、不触发播放。
    """
    t0 = time.time()
    log("warmup: 完整链路冷启动预热开始…")

    # ① ASR 预热（原有）
    from src.brain.voice.asr import asr_transcribe
    sample = ROOT / "data" / "voice" / "mic-regress" / "synth-query.wav"
    if sample.is_file():
        r = asr_transcribe(sample)
        log(f"warmup[asr]: ok={r.get('ok')} text={r.get('text')!r} daemon={r.get('daemon')} 耗时={time.time()-t0:.1f}s")
    else:
        log(f"warmup[asr]: 无预热样本（{sample}），跳过")

    # ② Agent 14B 预热（agent_server=8756，agent_client 常量；勿用 8080）
    try:
        from src.brain.agent_client import ask_agent, agent_healthy
        healthy = agent_healthy()
        if healthy:
            reply = ask_agent("查询任务状态。", max_tokens=64)
            log(f"warmup[agent]: healthy=True reply={reply[:40]!r} 耗时={time.time()-t0:.1f}s")
        else:
            log(f"warmup[agent]: agent_server(8756) 不可达，跳过 Agent 预热")
    except Exception as exc:
        log(f"warmup[agent]: 预热失败 {str(exc)[:120]}")

    # ③ TTS 预热（按 profile engine）
    try:
        from src.brain.voice.tts import tts_synthesize
        from src.brain.voice.voice_profile import load_profile
        engine = (load_profile().get("voice") or {}).get("engine", "cv3")
        warm_wav = ROOT / "tools" / "_warmup_tts.wav"
        r = tts_synthesize("好的，收到。", warm_wav, timeout=300)
        log(f"warmup[tts]: engine={engine} ok={r.get('ok')} out={r.get('wav')!r} "
            f"rate={r.get('rate')} engine_used={r.get('engine')} 耗时={time.time()-t0:.1f}s")
    except Exception as exc:
        log(f"warmup[tts]: 预热失败 {str(exc)[:120]}")

    log(f"warmup: 完成，总耗时={time.time()-t0:.1f}s")


def _make_vad():
    """#134 Silero VAD（sherpa-onnx 集成）：替代固定静音 QUIET_AFTER_SPEECH 判段。
    2026-10-30 实装：OVOS 用 silence_seconds=0.5s 判段，我们用 min_silence_duration=0.5 对齐；
    VAD 是模型级静音判定，比能量阈值更能区分停顿/呼吸/环境音，且段提交即知语音已结束，
    不再等固定 1.2s。asr.py 第 191 行旧注释"VAD 不产分段"为过时结论（探针实测见
    data/logs/vad-probe-20261030.py：真实录音 empty=False、start=9312）。"""
    import sherpa_onnx
    vad_config = sherpa_onnx.VadModelConfig()
    s = sherpa_onnx.SileroVadModelConfig()
    s.model = str(ROOT / "models" / "sherpa" / "silero_vad.onnx")
    s.threshold = 0.35
    s.min_silence_duration = 0.5   # 静音 0.5s 判段结束（对齐 OVOS silence_seconds=0.5）
    s.min_speech_duration = 0.25
    s.window_size = 512
    vad_config.silero_vad = s
    vad_config.sample_rate = SR_KWS
    return sherpa_onnx.VoiceActivityDetector(vad_config, buffer_size_in_seconds=60)


def _call_asr_with_timeout(asr_fn, wav_path: Path, timeout: float) -> dict:
    """Run one whole-buffer ASR attempt without letting it hold the recognizer forever."""
    box: dict = {}

    def invoke() -> None:
        try:
            box["result"] = asr_fn(wav_path)
        except BaseException as exc:  # transported back to the recognition thread
            box["error"] = exc

    worker = threading.Thread(target=invoke, name="pseudo-stream-asr-call", daemon=True)
    worker.start()
    worker.join(max(0.0, timeout))
    if worker.is_alive():
        raise TimeoutError(f"ASR timeout after {timeout:.3f}s")
    if "error" in box:
        raise box["error"]
    result = box.get("result")
    if not isinstance(result, dict):
        raise TypeError(f"ASR result must be dict, got {type(result).__name__}")
    return result


def _write_asr_snapshot(frames, sample_rate: int, output_dir: Path) -> Path:
    """Write the recognizer-owned cumulative buffer for an intermediate rerun."""
    import numpy as np
    import wave

    output_dir.mkdir(parents=True, exist_ok=True)
    path = output_dir / f".pseudo-stream-{os.getpid()}-{threading.get_ident()}.wav"
    audio = np.concatenate(frames, axis=0).astype(np.int16, copy=False)
    with wave.open(str(path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio.reshape(-1).tobytes())
    return path


def _capture_worker(
    input_config: dict,
    audio_queue: queue.Queue,
    stop_event: threading.Event,
    state: CaptureState,
    *,
    capture_factory,
    max_seconds: float,
) -> None:
    """Capture only: read the microphone and enqueue timestamped frames."""
    try:
        with capture_factory(
            int(input_config["index"]),
            str(input_config["hostapi"]),
            int(round(float(input_config["default_samplerate"]))),
        ) as stream:
            state.sample_rate = int(stream.samplerate)
            capture_chunk = max(1, int(round(CHUNK * state.sample_rate / SR)))
            state.started_at = time.monotonic()
            log(
                f"pseudo-stream capture start: sr={state.sample_rate} chunk={capture_chunk} "
                f"thread={threading.current_thread().name}"
            )
            while time.monotonic() - state.started_at < max_seconds and not stop_event.is_set():
                read_started = time.monotonic()
                data, _ = stream.read(capture_chunk)
                captured_at = time.monotonic()
                state.read_times.append(read_started)
                state.frames.append(data)
                audio_queue.put(AudioFrame(captured_at, data, state.sample_rate))
            state.ended_at = time.monotonic()
    except BaseException:
        state.error = traceback.format_exc()[-500:]
        log("pseudo-stream capture exception: " + state.error)
    finally:
        audio_queue.put(None)


def _recognition_worker(
    audio_queue: queue.Queue,
    stop_event: threading.Event,
    state: RecognitionState,
    *,
    vad_factory,
    asr_fn,
    output_dir: Path,
    beep_settle_sec: float,
    retry_interval: float,
    asr_timeout: float,
    deadline: float,
) -> None:
    """Consume queued audio, segment with VAD, and rerun whole-buffer ASR at most once/s."""
    import numpy as np

    frames = []
    vad = vad_factory()
    spoken = False
    speech_started_at = None
    last_speech_at = None
    first_frame_at = None
    last_frame_at = None
    last_submit_at = None
    sample_rate = SR
    final_vad_sec = 0.0

    def submit(*, final: bool) -> None:
        if not frames or state.degraded:
            return
        remaining = deadline - time.monotonic()
        if remaining <= 0:
            raise TimeoutError(f"recognition thread exceeded {asr_timeout:.1f}s")
        if final:
            wav_path = state.wav_path
        else:
            wav_path = _write_asr_snapshot(frames, sample_rate, output_dir)
        if wav_path is None:
            return
        try:
            result = _call_asr_with_timeout(asr_fn, wav_path, min(asr_timeout, remaining))
            state.rerun_count += 1
            if final:
                if not result.get("ok") or not str(result.get("text") or "").strip():
                    raise RuntimeError(f"final ASR invalid: {result!r}")
                state.asr = result
                log(f"pseudo-stream final run: count={state.rerun_count} text={result.get('text')!r}")
            elif result.get("ok") and str(result.get("text") or "").strip():
                state.intermediate_asr = result
                log(f"pseudo-stream intermediate: count={state.rerun_count} text={result.get('text')!r}")
        finally:
            if not final:
                try:
                    wav_path.unlink(missing_ok=True)
                except OSError:
                    pass

    def degrade(exc: BaseException) -> None:
        state.degraded = True
        state.error = f"{type(exc).__name__}: {exc}"
        log("pseudo-stream degraded, serial fallback required: " + state.error)

    try:
        finished = False
        while not finished:
            item = audio_queue.get()
            if item is None:
                try:
                    vad.flush()
                except AttributeError:
                    pass
                finished = True
                if last_frame_at is None:
                    break
            else:
                frame = item
                frames.append(frame.data)
                sample_rate = frame.sample_rate
                last_frame_at = frame.captured_at
                if first_frame_at is None:
                    first_frame_at = frame.captured_at
                    last_submit_at = first_frame_at
                f32 = frame.data.astype(np.float32).reshape(-1) / 32767.0
                peak = float(np.abs(f32).max()) if f32.size else 0.0
                vad.accept_waveform(resample_to_16k(f32, sample_rate))
                if frame.captured_at >= first_frame_at + beep_settle_sec and peak >= ENERGY_TH:
                    if not spoken:
                        spoken = True
                        speech_started_at = frame.captured_at
                    last_speech_at = frame.captured_at

            if first_frame_at is None:
                continue
            now = last_frame_at or first_frame_at
            if now >= first_frame_at + beep_settle_sec:
                while not vad.empty():
                    seg = vad.front
                    samples = seg.samples
                    vad.pop()
                    vad_sec = len(samples) / SR_KWS
                    if vad_sec < 0.4:
                        log(f"vad 段过短跳过(残响): sec={vad_sec:.2f}，继续等语音段")
                        continue
                    final_vad_sec = vad_sec
                    if not spoken:
                        spoken = True
                        speech_started_at = now
                    log(f"vad 段提交: start={seg.start} samples={len(samples)} sec={vad_sec:.2f} 说完判定")
                    finished = True
                    stop_event.set()
                    break
            if not finished and spoken and last_speech_at is not None:
                if now - last_speech_at >= QUIET_AFTER_SPEECH:
                    log(f"能量兜底判定说完: last_speech_at={last_speech_at:.2f}")
                    finished = True
                    stop_event.set()
            if (
                not finished
                and not state.degraded
                and spoken
                and last_submit_at is not None
                and now - last_submit_at >= retry_interval
            ):
                try:
                    submit(final=False)
                except BaseException as exc:
                    degrade(exc)
                last_submit_at = now

        state.wav_path = _finalize(
            frames,
            speech_started_at,
            last_frame_at or first_frame_at or time.monotonic(),
            spoken,
            vad_sec=final_vad_sec,
            sample_rate=sample_rate,
            output_dir=output_dir,
        )
        if state.wav_path is not None and not state.degraded:
            try:
                submit(final=True)
            except BaseException as exc:
                degrade(exc)
    except BaseException as exc:
        degrade(exc)


def collect(
    input_config: dict,
    *,
    capture_factory=open_audio_capture,
    vad_factory=_make_vad,
    asr_fn=None,
    output_dir: Path = OUT_DIR,
    beep_settle_sec: float = BEEP_SETTLE_SEC,
    retry_interval: float = ASR_RERUN_INTERVAL_SEC,
    asr_timeout: float = ASR_TIMEOUT_SEC,
    max_seconds: float = MAX_SECONDS,
) -> CollectionResult:
    """Run capture and whole-buffer pseudo-stream recognition concurrently."""
    if asr_fn is None:
        from src.brain.voice.asr import asr_transcribe

        asr_fn = asr_transcribe
    audio_queue: queue.Queue = queue.Queue()
    stop_event = threading.Event()
    capture_state = CaptureState()
    recognition_state = RecognitionState()
    deadline = time.monotonic() + asr_timeout
    recognition_thread = threading.Thread(
        target=_recognition_worker,
        name="voice-recognition",
        args=(audio_queue, stop_event, recognition_state),
        kwargs={
            "vad_factory": vad_factory,
            "asr_fn": asr_fn,
            "output_dir": Path(output_dir),
            "beep_settle_sec": beep_settle_sec,
            "retry_interval": retry_interval,
            "asr_timeout": asr_timeout,
            "deadline": deadline,
        },
        daemon=True,
    )
    capture_thread = threading.Thread(
        target=_capture_worker,
        name="voice-capture",
        args=(input_config, audio_queue, stop_event, capture_state),
        kwargs={"capture_factory": capture_factory, "max_seconds": max_seconds},
        daemon=True,
    )
    recognition_thread.start()
    capture_thread.start()
    capture_thread.join(max_seconds + 5.0)
    recognition_thread.join(max(0.0, deadline - time.monotonic()) + 0.1)
    if capture_thread.is_alive():
        stop_event.set()
        capture_state.error = capture_state.error or "capture thread join timeout"
    if recognition_thread.is_alive():
        stop_event.set()
        recognition_state.degraded = True
        recognition_state.error = f"recognition thread timeout after {asr_timeout:.1f}s"
        log("pseudo-stream degraded, serial fallback required: " + recognition_state.error)
    if capture_state.error:
        recognition_state.degraded = True
        recognition_state.error = "; ".join(filter(None, (recognition_state.error, capture_state.error)))
    if recognition_state.wav_path is None and capture_state.frames:
        recognition_state.wav_path = _finalize(
            capture_state.frames,
            capture_state.started_at,
            capture_state.ended_at or time.monotonic(),
            True,
            sample_rate=capture_state.sample_rate,
            output_dir=Path(output_dir),
        )
    intervals = tuple(
        round((b - a) * 1000.0, 3)
        for a, b in zip(capture_state.read_times, capture_state.read_times[1:])
    )
    log(
        f"pseudo-stream complete: degraded={recognition_state.degraded} "
        f"reruns={recognition_state.rerun_count} reads={len(capture_state.read_times)} "
        f"max_read_interval_ms={max(intervals, default=0.0):.3f}"
    )
    return CollectionResult(
        wav_path=recognition_state.wav_path,
        asr=recognition_state.asr,
        intermediate_asr=recognition_state.intermediate_asr,
        degraded=recognition_state.degraded,
        error=recognition_state.error,
        rerun_count=recognition_state.rerun_count,
        read_intervals_ms=intervals,
        capture_thread_alive=capture_thread.is_alive(),
        recognition_thread_alive=recognition_thread.is_alive(),
    )


def _finalize(
    frames,
    speech_started_at,
    now,
    spoken,
    vad_sec: float = 0.0,
    sample_rate: int = SR,
    output_dir: Path = OUT_DIR,
) -> Path | None:
    """采集收尾：门控 → 增益 → 写 wav。与 #132/#133 一致，抽出来供 VAD 与能量双路径共用。
    vad_sec>0 时以 VAD 段时长为准判最短语音（VAD 权威），否则用能量起止窗。"""
    import numpy as np
    import wave
    if not spoken:
        return None
    if vad_sec > 0:
        if vad_sec < 0.4:
            log(f"VAD 段过短：{vad_sec:.2f}s < 0.4s，回待唤醒")
            return None
    elif speech_started_at and now - speech_started_at < 0.4:
        return None
    audio = np.concatenate(frames, axis=0)
    f32 = audio.astype(np.float32).reshape(-1) / 32767.0
    peak = np.abs(f32).max()
    # 2026-10-29 19:4x 惠普麦电平校准：USB 麦克风原始电平偏低（说话 peak≈0.03，
    # 而 Razer Kiyo 时≈0.35），门控阈值从 0.015/0.005 下调至 0.01/0.002，
    # 否则 rms=0.0019 被 0.005 门槛卡掉 → "唤醒成功但无有效语音"。
    bl = sample_rate // 10  # 100ms
    voiced = [float(np.abs(f32[i * bl:(i + 1) * bl]).max() > 0.01) for i in range(len(f32) // bl)]
    voiced_sec = sum(voiced) * 0.1
    rms = float(np.sqrt((f32 ** 2).mean()))
    if voiced_sec < 0.4 or rms < 0.002:
        log(f"指令无有效语音：voiced={voiced_sec:.1f}s rms={rms:.4f} peak={peak:.4f}，回待唤醒")
        return None
    # 2026-10-29 19:4x 采集段自动增益：惠普麦电平低，直接写原始 int16 给 ASR 识别率差；
    # 按峰值归一化增益（目标 0.6、上限 30，与唤醒段同策略），改善 ASR 识别。
    gain = min(0.6 / max(peak, 1e-6), 30.0)
    f32_g = f32 * gain
    audio_g = np.clip(f32_g * 32767.0, -32768, 32767).astype(np.int16)
    output_dir.mkdir(parents=True, exist_ok=True)
    wav_path = output_dir / f"listen-{time.time_ns()}.wav"
    with wave.open(str(wav_path), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sample_rate)
        wf.writeframes(audio_g.tobytes())
    log(f"captured: {wav_path.name} sec={round(len(audio)/sample_rate,2)} sr={sample_rate} peak={peak:.4f} gain={gain:.1f} voiced={voiced_sec:.1f}s rms={rms:.4f}")
    return wav_path


def resolve_out_device() -> int:
    """动态解析输出设备：优先 WASAPI 下的 LOFREE/POISON 耳机，其次任意 hostapi 名称匹配，
    最后系统默认输出。

    2026-10-30 后半段断续修复：此前按设备枚举顺序名字匹配，命中 MME idx4（POISON 44100）——
    播放线程（sd.play 阻塞）与 KWS 采集线程（MME idx1 输入流）同 hostapi 并发，
    采集满负荷时 MME 输出缓冲欠载 → 长回复"后半段断断续续"（20:27 真机 round reply-349 复现，
    wav 波形健康无丢帧，停顿与 Melo 旧回复一致，根因在播放层并发）。
    改优先 WASAPI（idx24 POISON 44100Hz，与 MME 输入流不同驱动栈，消除欠载；
    且符合基线"输出走 WASAPI"意图）。回退链：WASAPI POISON → 任意 hostapi POISON → 系统默认。
    """
    import sounddevice as sd
    try:
        devices = sd.query_devices()
        # ① WASAPI 输出（优先，避免 MME 同栈输入/输出并发欠载）
        for i, d in enumerate(devices):
            if d["max_output_channels"] > 0 and d["name"] and (
                "LOFREE" in d["name"].upper() or "POISON" in d["name"].upper()
            ):
                try:
                    ha = sd.query_hostapis()[d["hostapi"]]["name"]
                except (IndexError, KeyError, TypeError):
                    ha = "unknown"
                if "WASAPI" in ha:
                    log(f"输出设备解析: idx={i} name={d['name']} hostapi={ha} sr={d['default_samplerate']:.0f}")
                    return i
        # ② 任意 hostapi 名称匹配回退
        for i, d in enumerate(devices):
            if d["max_output_channels"] > 0 and d["name"] and (
                "LOFREE" in d["name"].upper() or "POISON" in d["name"].upper()
            ):
                log(f"输出设备解析(非WASAPI回退): idx={i} name={d['name']}")
                return i
        # 无 LOFREE：用系统默认输出
        defidx = sd.default.device[1]
        if defidx is None or defidx < 0:
            for i, d in enumerate(devices):
                if d["max_output_channels"] > 0 and d["name"]:
                    log(f"输出设备解析(默认回退): idx={i} name={d['name']}")
                    return i
            return 0
        log(f"输出设备解析(系统默认): idx={defidx}")
        return defidx
    except Exception:
        return DEV_OUT


def play_wav(path: Path) -> None:
    """按扩展名播放：mp3 用 miniaudio 解码后 sounddevice 播放（动态解析输出设备），wav 直放。"""
    import sounddevice as sd
    import numpy as np
    out_dev = resolve_out_device()
    if path.suffix.lower() == ".mp3":
        import miniaudio
        d = miniaudio.decode_file(str(path))
        samples = np.frombuffer(d.samples, dtype=np.int16)
        if d.nchannels == 2:
            samples = ((samples[0::2].astype(np.int32) + samples[1::2].astype(np.int32)) // 2).astype(np.int16)
        sd.play(samples, d.sample_rate, device=out_dev)
        sd.wait()
        return
    import wave
    with wave.open(str(path), "rb") as wf:
        fr = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    samples = np.frombuffer(raw, dtype=np.int16)
    sd.play(samples, fr, device=out_dev)
    sd.wait()


def _play_safe(path: Path) -> None:
    """后台线程安全播放：异常只记录，不打断主循环。播放期间置 _PLAYING 暂停 KWS 采集（L31 互斥）。"""
    try:
        _PLAYING.set()
        play_wav(path)
        log("played: " + str(path))
    except Exception:
        log("play 失败: " + traceback.format_exc()[-300:])
    finally:
        _PLAYING.clear()


def _handle_collection_result(loop, collection: CollectionResult) -> dict:
    """Use the successful final pseudo-stream ASR exactly once, or run the serial fallback."""
    if collection.wav_path is None:
        return {"ok": False, "stage": "input", "error": "指令采集为空"}
    if collection.degraded or collection.asr is None:
        log(
            "pseudo-stream serial fallback: "
            + (collection.error or "final recognition result unavailable")
        )
        return loop.handle_audio(collection.wav_path)

    # VoiceInteractionLoop owns bridge/push/TTS and imports asr_transcribe as a
    # module binding.  Replace only that binding for this single-threaded main
    # handoff, then restore it in finally; the TTS path remains untouched.
    import src.brain.voice_loop as voice_loop_module

    original_asr = voice_loop_module.asr_transcribe

    def precomputed_asr(_wav_path):
        return collection.asr

    voice_loop_module.asr_transcribe = precomputed_asr
    try:
        return loop.handle_audio(collection.wav_path)
    finally:
        voice_loop_module.asr_transcribe = original_asr


def main() -> None:
    log(f"daemon 启动（pid={os.getpid()}，唤醒词模式：贾维斯）")
    # 2026-10-29 19:5x 单实例锁：原子创建锁文件（O_CREAT|O_EXCL），
    # 双实例同时启动时只有一个能建锁成功，杜绝"双实例抢麦克风→采集静默"（19:25 实锤 21920/27192 双跑）
    _LOCK_FILE = ROOT / "data" / "logs" / "voice-listen-daemon.lock"
    try:
        fd = os.open(str(_LOCK_FILE), os.O_CREAT | os.O_EXCL | os.O_WRONLY)
        os.write(fd, str(os.getpid()).encode())
        os.close(fd)
    except FileExistsError:
        # 锁已存在：检查旧 pid 是否存活；存活则退出，死锁则接管
        try:
            old_pid = int(_LOCK_FILE.read_text().strip())
            os.kill(old_pid, 0)
            log(f"检测到已有 daemon 实例(pid={old_pid})在运行，本实例退出")
            return
        except (ValueError, OSError):
            try:
                _LOCK_FILE.write_text(str(os.getpid()))
                log(f"接管失效锁（旧实例已退出），pid={os.getpid()}")
            except Exception:
                pass
    except Exception:
        pass  # 锁失败不阻塞主流程

    input_config = select_input_config()

    try:
        spotter_manager = HotReloadSpotter()
        log("KWS 模型加载完成")
    except Exception:
        log("KWS 加载失败，回退常驻监听: " + traceback.format_exc()[-400:])
        spotter_manager = None
    try:
        warmup()
    except Exception:
        log("warmup 失败: " + traceback.format_exc()[-400:])
    from src.brain.voice_loop import VoiceInteractionLoop
    loop = VoiceInteractionLoop(
        queue_root=ROOT / "tasks",
        command_file=ROOT / "data" / "orb" / "orb_command.json",
        reply_dir=OUT_DIR,
    )
    log("监听循环开始：请说「贾维斯」唤醒（USB 麦克）")
    while True:
        try:
            if spotter_manager is not None:
                hit = wait_wakeup(spotter_manager, input_config, loop)
                if hit is None:
                    continue
            log("唤醒成功，开始采集指令…")
            collection = collect(input_config)
            wav = collection.wav_path
            if wav is None:
                log("指令采集为空，回待唤醒")
                continue
            log("speech: 开始处理 " + wav.name)
            t0 = time.time()
            result = _handle_collection_result(loop, collection)
            dt = time.time() - t0
            log(json.dumps({
                "round": True, "elapsed_s": round(dt, 2),
                "asr": result.get("text"),
                "stage": result.get("stage"),
                "ok": result.get("ok"),
                "reason": (result.get("response") or {}).get("reason"),
                "reply": result.get("response", {}).get("text", "")[:200],
                "pushed_state": (result.get("pushed") or {}).get("state"),
                "pushed_seq": (result.get("pushed") or {}).get("seq"),
            }, ensure_ascii=False))
            reply = result.get("reply_wav")
            if reply and Path(reply).is_file():
                # 2026-10-29 19:5x 播放改后台线程：原来阻塞式播放使整轮 30~40s 内无法再次
                # 唤醒，且回复生成(14B+TTs)后才播，用户等太久以为"没反应"。
                # 现在 handle_audio 返回后立即回待唤醒，播放由线程异步完成。
                threading.Thread(target=_play_safe, args=(Path(reply),), daemon=True).start()
                log("async-play: " + str(reply))
        except KeyboardInterrupt:
            log("daemon 停止（键盘中断）")
            break
        except Exception:
            log("循环异常续跑: " + traceback.format_exc()[-500:])


if __name__ == "__main__":
    main()
