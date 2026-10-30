"""CV3 TTS 桥接：经 runtime310 子进程执行 CosyVoice3 推理（P1 补建）。

设计要点：
- UltimaAgent 底座 venv（Py3.13）不装 torch/CosyVoice 重依赖；
- 每次合成经子进程调用 runtime310 python 执行内联推理脚本（脱机
  环境变量由脚本设置，零外部请求）；
- 输出 WAV 落到 UltimaAgent data/voice/ 写域，绝不写 Topo Backup；
- 模型与参考音频只读加载（参考音频 = CosyVoice 源码自带
  asset/zero_shot_prompt.wav，解决 prompt_wav 来源缺陷）；
- 进程结束后释放，不常驻。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import wave
from pathlib import Path

# 直跑入口（python tts.py）时保证 src 包可导入
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.brain.voice.resources import (
    CV3_MODEL_ROOT,
    COSYVOICE_SOURCE,
    CV3_RUNTIME_PYTHON,
    all_cv3_resources_ready,
)

# 写域 vendor（pkg_resources shim），注入推理子进程 PYTHONPATH
_VENDOR_DIR = Path(__file__).resolve().parent / "_vendor"

# CosyVoice 源码自带参考音频（zero-shot 音色参考，只读）
PROMPT_WAV = COSYVOICE_SOURCE / "asset" / "zero_shot_prompt.wav"

# 推理脚本（写入 write-domain 临时目录，随调用创建）
_INLINE_SCRIPT = r"""
import os, sys, json
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("HF_HUB_DISABLE_TELEMETRY", "1")
os.environ.setdefault("PYTHONNOUSERSITE", "1")

source = Path(r"{source}")
model = Path(r"{model}")
prompt_wav = Path(r"{prompt_wav}")
sys.path.insert(0, str(source))
sys.path.insert(0, str(source / "third_party" / "Matcha-TTS"))

import torch
torch.set_num_threads(1)
import numpy as np
import soundfile as sf
from cosyvoice.cli.cosyvoice import AutoModel

text = sys.argv[1]
out_wav = sys.argv[2]
if torch.cuda.is_available():
    device = "cuda"
else:
    device = "cpu"
    os.environ["CUDA_VISIBLE_DEVICES"] = ""

cosy = AutoModel(model_dir=str(model), load_trt=False, load_vllm=False, fp16=True)
prompt_text = "希望你以后能够做的比我还好呦。<|endofprompt|>"

speech = None
for block in cosy.inference_zero_shot(text, prompt_text, str(prompt_wav), stream=False, speed=1.0):
    speech = block["tts_speech"]
    break
if speech is None:
    raise RuntimeError("no speech block produced")
pcm = np.clip(speech.detach().cpu().numpy().reshape(-1), -1, 1)
_peak = float(np.abs(pcm).max()) if pcm.size else 0.0
if _peak > 0.0:
    _gain = min(0.85 / _peak, 10.0)
    _gain = max(_gain, 10 ** (4 / 20))
    if _gain > 1.0:
        pcm = np.clip(pcm * _gain, -1, 1)
sf.write(out_wav, pcm, cosy.sample_rate, subtype="PCM_16")
print(json.dumps({"ok": True, "wav": out_wav, "rate": cosy.sample_rate,
                  "seconds": len(pcm) / cosy.sample_rate, "device": device}))
"""


# ---------------------------------------------------------------------------
# sherpa-onnx 通道（P3 替换底座：MeloTTS 中文合成，离线，44100Hz 直出匹配 LOFREE 耳机）
# 进程内直接调用（venv-asr 同环境），模型全局缓存一次；import/资源缺失时静默回退 CosyVoice。
# ---------------------------------------------------------------------------
_SHERPA_MODEL_DIR = Path(__file__).resolve().parents[3] / "models" / "sherpa"
_SHERPA_MELO_DIR = _SHERPA_MODEL_DIR / "vits-melo-tts-zh_en"
_SHERPA_PIPER_DIR = _SHERPA_MODEL_DIR / "vits-piper-zh_CN-huayan-medium"

_TTS_SHERPA = None
_TTS_SHERPA_READY = None  # None=未探测 True/False=探测结果
_TTS_PIPER = None


def _piper_available() -> bool:
    """Piper 中文模型在位探测（音质干净，替代 Melo 的空间感）。"""
    try:
        return (
            (_SHERPA_PIPER_DIR / "zh_CN-huayan-medium.onnx").is_file()
            and (_SHERPA_PIPER_DIR / "tokens.txt").is_file()
            and (_SHERPA_PIPER_DIR / "espeak-ng-data").is_dir()
        )
    except Exception:
        return False


def _load_piper_tts():
    """加载（或取缓存）Piper 中文 TTS（vits 架构 + espeak-ng G2P）。失败抛 RuntimeError。"""
    global _TTS_PIPER
    if _TTS_PIPER is not None:
        return _TTS_PIPER
    try:
        import sherpa_onnx
    except Exception as exc:
        raise RuntimeError(f"sherpa_onnx import 失败: {exc}") from exc
    tts_cfg = sherpa_onnx.OfflineTtsConfig()
    tts_cfg.model.vits.model = str(_SHERPA_PIPER_DIR / "zh_CN-huayan-medium.onnx")
    tts_cfg.model.vits.tokens = str(_SHERPA_PIPER_DIR / "tokens.txt")
    tts_cfg.model.vits.data_dir = str(_SHERPA_PIPER_DIR / "espeak-ng-data")
    tts_cfg.model.num_threads = 2
    tts = sherpa_onnx.OfflineTts(tts_cfg)
    _TTS_PIPER = tts
    return tts


def _synthesize_piper(text: str, out_wav: Path) -> dict:
    """Piper 中文通道：干净音质合成 → PCM16 WAV（采样率随模型，22050Hz）。"""
    import numpy as np

    tts = _load_piper_tts()
    ga = tts.generate(_digits_to_chinese(text), sid=0, speed=1.0)
    sr = ga.sample_rate
    samples = np.asarray(ga.samples, dtype=np.float32)
    peak = float(np.abs(samples).max()) if samples.size else 0.0
    target_peak = 0.85
    if peak > 0.0:
        gain = min(target_peak / peak, 10.0)  # 最大 20dB
        gain = max(gain, 10 ** (4 / 20))  # 至少 +4dB
        if gain > 1.0:
            samples = samples * gain
        samples = np.clip(samples, -1.0, 1.0)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((samples * 32767).astype(np.int16).tobytes())
    return {"ok": True, "wav": str(out_wav), "rate": sr,
            "seconds": round(len(samples) / sr, 3), "device": "cpu",
            "engine": "sherpa-piper-tts"}


def _sherpa_tts_available() -> bool:
    """探测 sherpa TTS 通道可用性（sherpa_onnx 可 import 且 MeloTTS 模型文件在位）。"""
    global _TTS_SHERPA_READY
    if _TTS_SHERPA_READY is not None:
        return _TTS_SHERPA_READY
    try:
        import sherpa_onnx  # noqa: F401 - 可用性探测
        ok = (
            (_SHERPA_MELO_DIR / "model.onnx").is_file()
            and (_SHERPA_MELO_DIR / "tokens.txt").is_file()
            and (_SHERPA_MELO_DIR / "lexicon.txt").is_file()
            and (_SHERPA_MELO_DIR / "dict").is_dir()
        )
        _TTS_SHERPA_READY = ok
        return ok
    except Exception:
        _TTS_SHERPA_READY = False
        return False


def _load_sherpa_tts():
    """加载（或取缓存）MeloTTS 合成器。失败抛 RuntimeError。"""
    global _TTS_SHERPA
    if _TTS_SHERPA is not None:
        return _TTS_SHERPA
    try:
        import sherpa_onnx
    except Exception as exc:
        raise RuntimeError(f"sherpa_onnx import 失败: {exc}") from exc
    tts_cfg = sherpa_onnx.OfflineTtsConfig()
    tts_cfg.model.vits.model = str(_SHERPA_MELO_DIR / "model.onnx")
    tts_cfg.model.vits.tokens = str(_SHERPA_MELO_DIR / "tokens.txt")
    tts_cfg.model.vits.lexicon = str(_SHERPA_MELO_DIR / "lexicon.txt")
    tts_cfg.model.vits.dict_dir = str(_SHERPA_MELO_DIR / "dict")
    tts_cfg.model.num_threads = 2
    tts = sherpa_onnx.OfflineTts(tts_cfg)
    _TTS_SHERPA = tts
    return tts


_CN_DIGITS = {'0': '零', '1': '一', '2': '二', '3': '三', '4': '四',
              '5': '五', '6': '六', '7': '七', '8': '八', '9': '九'}


def _digits_to_chinese(text: str) -> str:
    """阿拉伯数字逐位转中文数字（Melo 词典忽略数字 OOV，避免读数缺失）。"""
    return ''.join(_CN_DIGITS.get(ch, ch) for ch in text)


def _synthesize_sherpa(text: str, out_wav: Path) -> dict:
    """sherpa 通道：MeloTTS 合成文本 → 44100Hz PCM16 WAV（与 LOFREE 耳机采样率直接匹配）。"""
    import numpy as np

    tts = _load_sherpa_tts()
    ga = tts.generate(_digits_to_chinese(text), sid=0, speed=1.0)
    sr = ga.sample_rate
    samples = np.asarray(ga.samples, dtype=np.float32)
    # 响度归一化：目标峰值 0.85（约 -1.4dB），最小可闻提升 4dB，最大增益 20dB 防底噪放大
    peak = float(np.abs(samples).max()) if samples.size else 0.0
    target_peak = 0.85
    if peak > 0.0:
        gain = min(target_peak / peak, 10.0)  # 最大 20dB
        gain = max(gain, 10 ** (4 / 20))  # 至少 +4dB
        if gain > 1.0:
            samples = samples * gain
        samples = np.clip(samples, -1.0, 1.0)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(sr)
        wf.writeframes((samples * 32767).astype(np.int16).tobytes())
    return {"ok": True, "wav": str(out_wav), "rate": sr,
            "seconds": round(len(samples) / sr, 3), "device": "cpu",
            "engine": "sherpa-melo-tts"}


def _render_script() -> Path:
    """将推理脚本渲染并写入写域临时目录，返回路径。"""
    import tempfile

    tmp = Path(tempfile.gettempdir()) / "ultima-voice"
    tmp.mkdir(parents=True, exist_ok=True)
    script = tmp / "tts_inline.py"
    content = _INLINE_SCRIPT.replace("{source}", str(COSYVOICE_SOURCE))
    content = content.replace("{model}", str(CV3_MODEL_ROOT))
    content = content.replace("{prompt_wav}", str(PROMPT_WAV))
    script.write_text(content, encoding="utf-8")
    return script


_PROBE_SCRIPT = r"""
import os, sys, json
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("PYTHONNOUSERSITE", "1")

source = Path(r"{source}")
model = Path(r"{model}")
prompt_wav = Path(r"{prompt_wav}")
sys.path.insert(0, str(source))
sys.path.insert(0, str(source / "third_party" / "Matcha-TTS"))

import torch
torch.set_num_threads(1)
import lightning.pytorch  # noqa: F401 - 验证 vendor shim 注入
import lightning.fabric  # noqa: F401
import numpy as np
import soundfile as sf
from cosyvoice.cli.cosyvoice import AutoModel  # 仅 import，不实例化

checks = {
    "torch": torch.__version__,
    "cuda": bool(torch.cuda.is_available()),
    "gpu": (torch.cuda.get_device_name(0) if torch.cuda.is_available() else None),
    "lightning": lightning.pytorch.__version__,
    "auto_model_import": True,
    "model_root": str(model),
    "model_exists": model.is_dir(),
    "prompt_wav": str(prompt_wav),
    "prompt_wav_exists": prompt_wav.is_file(),
}
print(json.dumps({"ok": True, "checks": checks}))
"""


def tts_probe(timeout: int = 120) -> dict:
    """探测链路（不加载模型权重）：验证子进程/vendor/CUDA/import 全通。"""
    if not all_cv3_resources_ready():
        raise RuntimeError("CV3 资源未就绪，拒绝探测")
    tmp = Path(__import__("tempfile").gettempdir()) / "ultima-voice"
    tmp.mkdir(parents=True, exist_ok=True)
    script = tmp / "tts_probe.py"
    content = _PROBE_SCRIPT.replace("{source}", str(COSYVOICE_SOURCE))
    content = content.replace("{model}", str(CV3_MODEL_ROOT))
    content = content.replace("{prompt_wav}", str(PROMPT_WAV))
    script.write_text(content, encoding="utf-8")

    env = dict(os.environ)
    env["PYTHONPATH"] = str(_VENDOR_DIR) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    proc = subprocess.run(
        [str(CV3_RUNTIME_PYTHON), "-X", "utf8", str(script)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    out_lines = (proc.stdout or "").strip().splitlines()
    last = out_lines[-1] if out_lines else ""
    if last.startswith("{"):
        try:
            return json.loads(last)
        except json.JSONDecodeError:
            pass
    raise RuntimeError(
        f"CV3 TTS 探测失败 exit={proc.returncode}\n"
        f"stdout尾: {out_lines[-3:] if out_lines else '空'}\n"
        f"stderr尾: {(proc.stderr or '').strip().splitlines()[-3:] if (proc.stderr or '').strip() else '空'}"
    )


# ---------------------------------------------------------------------------
# DEFECT-001 修复：TTS 极短文本近静音 → 文本扩展（根因）+ 合成后归一化（兜底）
# ---------------------------------------------------------------------------
# 根因实测（daemon 通道，CosyVoice3 zero-shot）：
#   "好"(1字) → 0.08s / orig_rms≈0.0（近全静音）
#   "好的"(2字) → 0.88s / orig_rms≈0.105（正常）
#   "好，收到。" → 1.68s / orig_rms≈0.133（正常）
# 结论：≤1 字超短文本模型几乎不产声；增益无法修复静音源，需文本扩展。
_DEFAULT_MIN_DURATION = 0.6      # 秒：低于此时长尾部补静音（前端播放可听）
_DEFAULT_TARGET_RMS = 0.12       # 归一化目标 RMS（0-1，对应 int16 ~3932）
_DEFAULT_RMS_FLOOR = 0.02        # 低于此 RMS 视为"近静音"，触发增益补偿
_MAX_GAIN = 20.0                 # 增益上限（近静音 RMS~0.006 可补到可听 0.12；clamp 防削顶）


def expand_tts_text(text: str) -> str:
    """DEFECT-001 文本扩展：≤1 字文本保留原字补确认后缀，保证模型正常发声。

    - 空文本原样返回；
    - 去空白后长度 ≤1（如"好/嗯/行/是"）：补"，收到。"后缀（语义不变）；
    - ≥2 字原样返回（实测正常发声概率高，不做任何改写）。
    """
    cleaned = text.strip()
    if not cleaned:
        return text
    if len(cleaned) <= 1:
        return f"{cleaned}，收到。"
    return text


def tts_output_is_near_silent(wav_path: str | Path) -> bool:
    """近静音判定（DEFECT-001）：RMS < 0.01 或 时长 < 0.3s。

    实测波动数据：正常发声（"好的"0.88s/RMS0.105、"好，收到。"1.28s/RMS0.089）；
    近静音（"稍等"0.04s/RMS0.0002、"好的"0.16s/RMS0.0003）。阈值居中可靠。
    读取异常视为近静音（触发重试）。
    """
    path = Path(wav_path)
    try:
        samples, rate, channels = _read_pcm16(path)
        rms = _rms_of(samples)
        seconds = len(samples) / rate / channels
        return rms < 0.01 or seconds < 0.3
    except Exception:
        return True


def _read_pcm16(path: Path) -> tuple[list[int], int, int]:
    """读取 PCM16 WAV（支持 mono/stereo），返回 (样本列表, 采样率, 声道数)。"""
    with wave.open(str(path), "rb") as wav:
        rate = wav.getframerate()
        channels = wav.getnchannels()
        sampwidth = wav.getsampwidth()
        if sampwidth != 2:
            raise ValueError(f"仅支持 PCM16（sampwidth=2），实际 {sampwidth}")
        frames = wav.getnframes()
        raw = wav.readframes(frames)
    import array

    samples = list(array.array("h", raw))
    return samples, rate, channels


def _write_pcm16(path: Path, samples: list[int], rate: int, channels: int) -> None:
    """写回 PCM16 WAV（保持采样率/声道数）。"""
    import array

    with wave.open(str(path), "wb") as wav:
        wav.setnchannels(channels)
        wav.setsampwidth(2)
        wav.setframerate(rate)
        wav.writeframes(array.array("h", samples).tobytes())


def _rms_of(samples: list[int]) -> float:
    """样本 RMS（0-1 归一化，int16 峰值 32767）。"""
    if not samples:
        return 0.0
    import math

    energy = sum(sample * sample for sample in samples) / len(samples)
    return math.sqrt(energy) / 32767.0


def normalize_tts_wav(
    wav_path: str | Path,
    *,
    min_duration: float = _DEFAULT_MIN_DURATION,
    target_rms: float = _DEFAULT_TARGET_RMS,
    rms_floor: float = _DEFAULT_RMS_FLOOR,
    max_gain: float = _MAX_GAIN,
) -> dict:
    """修复 TTS 极短文本近静音：低 RMS 增益补偿 + 最小时长静音 padding。

    Parameters
    ----------
    wav_path: 合成 WAV（PCM16）。就地归一化（写回原文件）。
    min_duration: 最小时长（秒），不足则尾部补静音。
    target_rms: 归一化目标 RMS（仅当原 RMS 低于 rms_floor 时触发放大）。
    rms_floor: "近静音"判定阈值。
    max_gain: 增益上限（防削顶/爆音）。

    Returns
    -------
    dict: 归一化统计（orig_rms/new_rms/orig_seconds/new_seconds/gain/padded/clipped）。
    无样本数据/文件损坏抛 ValueError。
    """
    path = Path(wav_path)
    samples, rate, channels = _read_pcm16(path)
    orig_rms = _rms_of(samples)
    orig_seconds = len(samples) / rate / channels  # 样本数÷采样率÷声道数=单声道时长

    gain = 1.0
    new_samples = list(samples)
    if orig_rms < rms_floor and orig_rms > 0:
        gain = min(target_rms / orig_rms, max_gain)
        new_samples = [max(-32767, min(32767, int(sample * gain))) for sample in samples]

    # 最小时长 padding（尾部静音）
    padded = False
    min_frames = int(min_duration * rate * channels)
    if len(new_samples) < min_frames:
        new_samples = new_samples + [0] * (min_frames - len(new_samples))
        padded = True

    # 削顶统计（增益后夹取导致）
    clipped = sum(1 for s in new_samples if abs(s) >= 32767)

    _write_pcm16(path, new_samples, rate, channels)
    new_rms = _rms_of(new_samples)
    new_seconds = len(new_samples) / rate / channels
    return {
        "normalized": True,
        "orig_rms": round(orig_rms, 4),
        "new_rms": round(new_rms, 4),
        "orig_seconds": round(orig_seconds, 3),
        "new_seconds": round(new_seconds, 3),
        "gain": round(gain, 3),
        "padded": padded,
        "clipped": clipped,
    }


def tts_synthesize(text: str, out_wav: str | Path, timeout: int = 300) -> dict:
    """合成文本为 WAV。返回结果 dict（含 ok/wav/rate/seconds/device/expanded/attempts）。

    前置：全部 CV3 资源就绪（否则抛 RuntimeError，避免半启动推理）。
    调校（T2）：常驻服务优先（模型热缓存），服务不可用回退冷启动子进程。
    修复（DEFECT-001）三层：
      ① 文本扩展：≤1 字文本补确认后缀（"好"→"好，收到。"，确定性修复）；
      ② 近静音检测 + 自动重试：CosyVoice 短文本输出不稳定（实测同文本
         "好的"一次 0.88s/RMS0.105、一次 0.16s/RMS0.0003），检测到近静音
         按「扩展→补句号→扩展补句号」顺序最多重试 3 次；
      ③ 合成后归一化兜底：低 RMS 增益 + 最小时长 padding。
    """
    effective_text = expand_tts_text(text)
    expanded = effective_text != text
    out = Path(out_wav)
    out.parent.mkdir(parents=True, exist_ok=True)

    # 重试候选序列（覆盖 1 字确定性静音 + 多字随机静音）
    candidates = [effective_text]
    if not expanded:
        candidates.append(f"{text}。")       # 原文补句号（句终语义不变）
    candidates.append(f"{effective_text}。")  # 扩展后仍静音 → 再补句号

    attempts: list[dict] = []
    for idx, candidate in enumerate(candidates):
        result = _synthesize_once(candidate, out, timeout)
        result["attempt"] = idx + 1
        result["attempt_text"] = candidate
        attempts.append(result)
        if result.get("ok") and not tts_output_is_near_silent(out):
            result["attempts"] = attempts
            return _finalize_synthesized(result, out, text, expanded, effective_text)
        if idx == len(candidates) - 1:
            # 全部尝试均近静音/失败：登记并返回最后一次结果（不抛错，由调用方/审计处置）
            result["attempts"] = attempts
            result["near_silent_all"] = True
            return _finalize_synthesized(result, out, text, expanded, effective_text)

    raise RuntimeError("不可达：candidates 非空")


def _synthesize_edge(text: str, out_wav: Path) -> dict:
    """edge-tts 通道：微软神经网络语音（晓晓，清晰无混响）→ MP3 合成后解码为 WAV（统一回复通道）。需联网。"""
    import asyncio
    import edge_tts

    mp3 = out_wav.with_suffix(".mp3")
    async def _run() -> None:
        c = edge_tts.Communicate(text, "zh-CN-XiaoxiaoNeural", rate="+0%")
        await c.save(str(mp3))

    asyncio.run(_run())
    if not mp3.is_file() or mp3.stat().st_size < 1024:
        raise RuntimeError("edge-tts 输出为空或异常")
    # MP3 解码 → 单声道 WAV（保持 reply 通道统一 wav，播放端 sounddevice 直放）
    import miniaudio
    import numpy as np
    import wave
    d = miniaudio.decode_file(str(mp3))
    samples = np.frombuffer(d.samples, dtype=np.int16)
    if d.nchannels == 2:
        samples = ((samples[0::2].astype(np.int32) + samples[1::2].astype(np.int32)) // 2).astype(np.int16)
    data = samples.astype(np.float32) / 32767.0
    peak = float(np.abs(data).max()) if data.size else 0.0
    target_peak = 0.85
    if peak > 0.0:
        gain = min(target_peak / peak, 10.0)
        gain = max(gain, 1.0)
        if gain > 1.0:
            samples = (np.clip(data * gain, -1.0, 1.0) * 32767.0).astype(np.int16)
    with wave.open(str(out_wav), "wb") as wf:
        wf.setnchannels(1)
        wf.setsampwidth(2)
        wf.setframerate(d.sample_rate)
        wf.writeframes(samples.tobytes())
    try:
        mp3.unlink()
    except OSError:
        pass
    return {"ok": True, "wav": str(out_wav), "rate": d.sample_rate, "seconds": 0.0,
            "device": "cloud", "engine": "edge-tts"}


def _synthesize_once(text: str, out_wav: Path, timeout: int) -> dict:
    """单次合成（edge-tts 联网首选 → Piper 本地 → sherpa-Melo 本地 → daemon → 冷启动兜底）。"""
    # edge-tts 首选：微软神经网络语音，音质干净无混响（对话玩具/设备主流方案）；失败回退本地
    try:
        edge_result = _synthesize_edge(text, out_wav)
        if edge_result.get("ok") and Path(edge_result["wav"]).is_file():
            return edge_result
    except Exception as exc:
        print(f"TTS edge unavailable, fallback local: {exc}")
    # Piper 次选（本地干净音质）；失败回退 Melo
    if _piper_available():
        try:
            piper_result = _synthesize_piper(text, out_wav)
            if piper_result.get("ok") and Path(out_wav).is_file():
                return piper_result
        except Exception as exc:
            print(f"TTS piper unavailable, fallback melo: {exc}")
    # sherpa-onnx Melo 次选（离线 44100Hz）；失败回退原链路
    if _sherpa_tts_available():
        try:
            sherpa_result = _synthesize_sherpa(text, out_wav)
            if sherpa_result.get("ok") and Path(out_wav).is_file():
                return sherpa_result
        except Exception as exc:
            print(f"TTS sherpa unavailable, fallback original: {exc}")
    # T2 调校：优先常驻服务（模型只加载一次，秒级推理）
    try:
        from src.brain.voice.daemon import daemon_tts_synthesize

        daemon_result = daemon_tts_synthesize(text, out_wav, timeout=timeout)
        if daemon_result is not None and daemon_result.get("ok"):
            return daemon_result
        if daemon_result is not None and not daemon_result.get("ok"):
            # 常驻已起但本次失败：显式记录，回退冷启动
            print(f"TTS daemon synthesize failed, fallback cold-start: {daemon_result.get('error')}")
    except Exception as exc:  # 常驻通道任何异常均回退冷启动，不影响主链路
        print(f"TTS daemon unavailable, fallback cold-start: {exc}")

    if not all_cv3_resources_ready():
        missing = [
            k for k, v in {
                "runtime310": CV3_RUNTIME_PYTHON.is_file(),
                "source": COSYVOICE_SOURCE.is_dir(),
                "model_root": CV3_MODEL_ROOT.is_dir(),
            }.items()
            if not v
        ]
        raise RuntimeError(f"CV3 资源未就绪，缺: {missing}")
    if not PROMPT_WAV.is_file():
        raise RuntimeError(f"参考音频缺失: {PROMPT_WAV}")

    script = _render_script()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_VENDOR_DIR) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    proc = subprocess.run(
        [str(CV3_RUNTIME_PYTHON), "-X", "utf8", str(script), text, str(out_wav)],
        capture_output=True,
        text=True,
        timeout=timeout,
        env=env,
        creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
    )
    # 解析最后一行 JSON（推理脚本 print 一行结果）
    out_lines = (proc.stdout or "").strip().splitlines()
    last = out_lines[-1] if out_lines else ""
    if last.startswith("{"):
        try:
            return json.loads(last)
        except json.JSONDecodeError:
            pass
    raise RuntimeError(
        f"CV3 TTS 失败 exit={proc.returncode}\n"
        f"stdout尾: {out_lines[-3:] if out_lines else '空'}\n"
        f"stderr尾: {(proc.stderr or '').strip().splitlines()[-3:] if (proc.stderr or '').strip() else '空'}"
    )


def _finalize_synthesized(result: dict, out_wav: str | Path,
                          original_text: str | None = None,
                          expanded: bool = False,
                          effective_text: str | None = None) -> dict:
    """合成结果统一出口：登记文本扩展 + 过 normalize_tts_wav 近静音归一化（DEFECT-001）。

    归一化失败不阻断主链路：登记 normalized=False + 原结果保留。
    """
    if original_text is not None:
        result["expanded"] = {
            "expanded": expanded,
            "original": original_text,
            "text": effective_text or original_text,
        }
    path = Path(out_wav)
    try:
        if path.is_file() and path.stat().st_size > 44:  # 有效 WAV（头+至少 1 样本）
            norm = normalize_tts_wav(path)
            result["normalized"] = norm
        else:
            result["normalized"] = {"normalized": False, "reason": "空/无效 WAV"}
    except Exception as exc:  # 归一化任何异常不阻断交付
        result["normalized"] = {"normalized": False, "reason": str(exc)}
    return result


if __name__ == "__main__":  # pragma: no cover - CLI 探测入口
    import argparse

    parser = argparse.ArgumentParser(description="CV3 TTS 单次合成/链路探测")
    parser.add_argument("text", nargs="?", default="")
    parser.add_argument(
        "--out",
        default=r"H:\UltimaAI\UltimaAgent\data\voice\tts_sample.wav",
    )
    parser.add_argument("--probe", action="store_true", help="链路探测（不加载模型）")
    args = parser.parse_args()
    if args.probe:
        result = tts_probe()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = tts_synthesize(args.text, args.out)
        print(json.dumps(result, ensure_ascii=False, indent=2))
