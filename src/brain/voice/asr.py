"""CV3 ASR 桥接：经子进程执行语音识别（P1 补建 + P2 精度升级）。

识别引擎：
- 首选 faster-whisper（venv-asr，Python 3.13.16，本地缓存 medium 模型，
  中文精度远高于 whisper base；CTranslate2 CUDA 加速）；
- 兜底 openai-whisper（runtime310，whisper base 本地缓存）；
- 离线运行：模型下载被 HF_HUB_OFFLINE 阻断；缓存缺失时返回结构化错误
  而非半成品。
- 输出 JSON 结果，写域仅 UltimaAgent data/voice/。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import wave
from pathlib import Path

# 直跑入口（python asr.py）时保证 src 包可导入
if __package__ in (None, ""):
    sys.path.insert(0, str(Path(__file__).resolve().parents[3]))

from src.brain.voice.resources import CV3_RUNTIME_PYTHON
from src.brain.voice._resample import resample_to_16k

# 写域 vendor（pkg_resources shim），注入推理子进程 PYTHONPATH
_VENDOR_DIR = Path(__file__).resolve().parent / "_vendor"

# faster-whisper 后端（P2 精度升级）：独立 venv-asr + 本机缓存 large-v3 模型
_ASR_VENV_PYTHON = (
    Path(__file__).resolve().parents[3] / "tools" / "venv-asr" / "Scripts" / "python.exe"
)
_FASTER_WHISPER_MODEL = (
    Path.home()
    / ".cache" / "huggingface" / "hub"
    / "models--Systran--faster-whisper-large-v3" / "snapshots"
    / "edaa852ec7e145841d8ffdb056a99866b5f0a478"
)
# ctranslate2 依赖 CUDA 运行库（本机 torch/lib 提供 cublas64_12.dll）
_TORCH_LIB_DIR = (
    Path(__file__).resolve().parents[3]
    / "Topo Backup" / "C_Guixu" / "v0r3" / "cv3" / "TtsProbe"
    / "runtime310" / "python" / "Lib" / "site-packages" / "torch" / "lib"
)

_INLINE_FASTER_SCRIPT = r"""
import json, sys
from faster_whisper import WhisperModel

wav = sys.argv[1]
model_path = sys.argv[2]
model = WhisperModel(model_path, device="cuda", compute_type="float16")
# 指令域提示：约束中文识别朝向任务指令类短语（提升弱信号命中率）；
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
                  "model": "faster-whisper-large-v3", "wav": wav}))
"""

_INLINE_SCRIPT = r"""
import os, sys, json
from pathlib import Path

os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("PYTHONNOUSERSITE", "1")

wav = sys.argv[1]
model_name = sys.argv[2] if len(sys.argv) > 2 else "base"

import numpy as np
import soundfile as sf
import whisper

# whisper 的 load_audio 依赖系统 ffmpeg 命令行；本机无 ffmpeg，
# 用 soundfile 解码为 float32 ndarray 直接传入（whisper 支持 ndarray 输入）。
data, _sr = sf.read(wav, dtype="float32")
audio = np.ascontiguousarray(data, dtype=np.float32)

model = whisper.load_model(model_name)
result = model.transcribe(audio, language="zh", fp16=False)
text = (result.get("text") or "").strip()
print(json.dumps({"ok": True, "text": text, "language": result.get("language"),
                  "model": model_name, "wav": wav}))
"""


# ---------------------------------------------------------------------------
# sherpa-onnx 通道（P3 替换底座：SenseVoice 中文识别，离线，CER 7-10% < whisper ~20%）
# 进程内直接调用（live_mic 运行于 venv-asr，sherpa-onnx 已装同环境），
# 模型全局缓存一次，规避子进程冷启动；import/资源缺失时静默回退原链路。
# ---------------------------------------------------------------------------
_SHERPA_MODEL_DIR = Path(__file__).resolve().parents[3] / "models" / "sherpa"
_SHERPA_SENSE_DIR = _SHERPA_MODEL_DIR / "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-2024-07-17"
_SHERPA_VAD_ONNX = _SHERPA_MODEL_DIR / "silero_vad.onnx"
_SHERPA_SR = 16000

_ASR_RECOGNIZER = None
_ASR_VAD = None
_ASR_SHERPA_READY = None  # None=未探测 True/False=探测结果


def _sherpa_asr_available() -> bool:
    """探测 sherpa 通道可用性（sherpa_onnx 可 import 且模型文件在位）。"""
    global _ASR_SHERPA_READY
    if _ASR_SHERPA_READY is not None:
        return _ASR_SHERPA_READY
    try:
        import sherpa_onnx  # noqa: F401 - 可用性探测
        ok = (
            (_SHERPA_SENSE_DIR / "model.int8.onnx").is_file()
            and (_SHERPA_SENSE_DIR / "tokens.txt").is_file()
            and _SHERPA_VAD_ONNX.is_file()
        )
        _ASR_SHERPA_READY = ok
        return ok
    except Exception:
        _ASR_SHERPA_READY = False
        return False


def _load_sherpa_asr():
    """加载（或取缓存）SenseVoice 识别器 + Silero VAD。失败抛 RuntimeError。"""
    global _ASR_RECOGNIZER, _ASR_VAD
    if _ASR_RECOGNIZER is not None and _ASR_VAD is not None:
        return _ASR_RECOGNIZER, _ASR_VAD
    try:
        import sherpa_onnx
    except Exception as exc:
        raise RuntimeError(f"sherpa_onnx import 失败: {exc}") from exc

    rec = sherpa_onnx.OfflineRecognizer.from_sense_voice(
        model=str(_SHERPA_SENSE_DIR / "model.int8.onnx"),
        tokens=str(_SHERPA_SENSE_DIR / "tokens.txt"),
        num_threads=2,
        sample_rate=_SHERPA_SR,
        feature_dim=80,
        use_itn=True,
        debug=False,
    )
    vad_config = sherpa_onnx.VadModelConfig()
    s = sherpa_onnx.SileroVadModelConfig()
    s.model = str(_SHERPA_VAD_ONNX)
    s.threshold = 0.35      # 弱信号 USB 麦：默认 0.5 偏严，降到 0.35 提高检出
    s.min_silence_duration = 0.25
    s.min_speech_duration = 0.25
    s.window_size = 512
    vad_config.silero_vad = s
    vad_config.sample_rate = _SHERPA_SR
    vad = sherpa_onnx.VoiceActivityDetector(vad_config, buffer_size_in_seconds=60)
    _ASR_RECOGNIZER, _ASR_VAD = rec, vad
    return rec, vad


def _run_sherpa(wav: Path) -> dict:
    """sherpa 通道：WAV → VAD 精切语音段 → SenseVoice 离线识别。

    2026-10-30 修复（用户真机"查天气"被识别为"茶天天"）：
    原实现整段直识别，弱信号短指令（peak≈0.04）被前导静音/提示音残响污染，
    整段喂入 →"茶天天"（08:22:16 实证 wav 语音区 0.4~1.56s，前 0.4s 为残响/静音）。
    离线 A/B（asr-fine-ab-20261030.py，真机 wav 回归）：
    - 整段直识别：int8→"茶天天"、fp32→"茶天天天"（均错）
    - VAD 精切（min_silence=0.25/min_speech=0.2 + 0.05s 边余量）：int8/fp32 全部 →"查天气。" ✅
    结论：Silero VAD 分段能力正常（daemon 侧已实证 vad-probe），旧注释
    "VAD 不产分段"为过时结论，删除；弱信号短指令必须先精切再识别。
    """
    import numpy as np
    import sherpa_onnx

    rec, _ = _load_sherpa_asr()
    with wave.open(str(wav), "rb") as wf:
        fr = wf.getframerate()
        raw = wf.readframes(wf.getnframes())
    pcm = np.frombuffer(raw, dtype=np.int16).astype(np.float32) / 32767.0
    if fr != _SHERPA_SR:
        # 2026-10-29 降采样算法修复（L20 同源）：原 np.interp 线性插值频谱混叠，
        # 44.1k 弱信号下 SenseVoice 把"查一下珠海天气"识别成"查一下庭。"（天气路由 miss）。
        # 统一走 voice._resample 单一窗口 sinc 多相滤波实现（daemon 同源），
        # 离线 A/B：sinc→"查一下武海天气。"（含关键词可命中路由）vs linear→"查一下庭。"。
        pcm = resample_to_16k(pcm, fr)

    # VAD 精切语音段（2026-10-30）：弱信号指令必须先去掉前导静音/残响再识别。
    # 参数来自 asr-fine-ab-20261030.py 最优组：threshold=0.35、min_silence=0.25、
    # min_speech=0.2、window=512，段边界外扩 0.05s 防切掉字首辅音。
    vad_config = sherpa_onnx.VadModelConfig()
    s = sherpa_onnx.SileroVadModelConfig()
    s.model = str(_SHERPA_VAD_ONNX)
    s.threshold = 0.35
    s.min_silence_duration = 0.25
    s.min_speech_duration = 0.2
    s.window_size = 512
    vad_config.silero_vad = s
    vad_config.sample_rate = _SHERPA_SR
    vad = sherpa_onnx.VoiceActivityDetector(vad_config, buffer_size_in_seconds=60)
    # 必须按 window_size(512) 分块喂入（2026-10-30 实证）：一次性喂入整段时
    # VAD 前端段错切为尾部碎段（start=31616/0.26s → 识别"。"）；分块喂入正确
    # 切出主语音段（start=7040/1.23s → "查天气。"）。与 daemon collect()/A-B 脚本一致。
    for i in range(0, len(pcm), 512):
        vad.accept_waveform(pcm[i:i + 512])
    vad.flush()
    if not vad.empty():
        # 取首个语音段（短指令场景仅一段；VAD 已静音 0.25s 判定段结束）。
        # 注意：vad.pop() 会清空 seg.samples（daemon 侧已实证），这里只 front 不 pop。
        seg = vad.front
        samples = np.asarray(seg.samples, dtype=np.float32)
        if len(samples) > 0:
            margin = int(0.05 * _SHERPA_SR)
            lo = max(0, seg.start - margin)
            hi = min(len(pcm), seg.start + len(samples) + margin)
            pcm = pcm[lo:hi]

    # 弱信号自适应增益：SenseVoice 对峰值 <0.05 输入偏差大（历史实测「更快乐。」类
    # 错识别），统一归一化到 0.3 目标峰值后再识别，弱麦（RMS 0.003~0.008）不再依赖
    # 上游 GAIN 后置；强信号不动。
    peak = float(np.abs(pcm).max()) if len(pcm) else 0.0
    if 0.0 < peak < 0.05:
        pcm = pcm * min(0.3 / peak, 30.0)
        pcm = np.clip(pcm, -1.0, 1.0)

    stream = rec.create_stream()
    stream.accept_waveform(_SHERPA_SR, pcm)
    rec.decode_stream(stream)
    text = stream.result.text.strip()
    return {"ok": bool(text), "text": text, "language": "zh",
            "model": "sherpa-sense-voice-int8", "wav": str(wav)}


def _render_script() -> Path:
    import tempfile

    tmp = Path(tempfile.gettempdir()) / "ultima-voice"
    tmp.mkdir(parents=True, exist_ok=True)
    script = tmp / "asr_inline.py"
    script.write_text(_INLINE_SCRIPT, encoding="utf-8")
    return script


def _run_faster_whisper(wav: Path) -> dict:
    """首选后端：faster-whisper medium（venv-asr + 本机缓存模型，CUDA）。

    失败时抛 RuntimeError，由调用方决定是否回退 whisper base。
    """
    if not _ASR_VENV_PYTHON.is_file():
        raise RuntimeError(f"venv-asr 解释器缺失: {_ASR_VENV_PYTHON}")
    if not _FASTER_WHISPER_MODEL.is_dir():
        raise RuntimeError(f"faster-whisper medium 模型缓存缺失: {_FASTER_WHISPER_MODEL}")

    import tempfile

    tmp = Path(tempfile.gettempdir()) / "ultima-voice"
    tmp.mkdir(parents=True, exist_ok=True)
    script = tmp / "asr_faster_inline.py"
    script.write_text(_INLINE_FASTER_SCRIPT, encoding="utf-8")

    # ctranslate2 需要 cublas64_12.dll；把 torch/lib（CUDA 运行库所在目录）加进 PATH
    env = dict(os.environ)
    if _TORCH_LIB_DIR.is_dir():
        env["PATH"] = str(_TORCH_LIB_DIR) + os.pathsep + env.get("PATH", "")

    proc = subprocess.run(
        [str(_ASR_VENV_PYTHON), "-X", "utf8", str(script), str(wav), str(_FASTER_WHISPER_MODEL)],
        capture_output=True,
        text=True,
        timeout=600,
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
        f"faster-whisper 失败 exit={proc.returncode}\n"
        f"stdout尾: {out_lines[-3:] if out_lines else '空'}\n"
        f"stderr尾: {(proc.stderr or '').strip().splitlines()[-3:] if (proc.stderr or '').strip() else '空'}"
    )


def _run_whisper_legacy(wav: Path, model: str = "base", timeout: int = 300) -> dict:
    """兜底后端：openai-whisper（runtime310，base 模型本地缓存）。"""
    script = _render_script()
    env = dict(os.environ)
    env["PYTHONPATH"] = str(_VENDOR_DIR) + (
        os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
    )
    proc = subprocess.run(
        [str(CV3_RUNTIME_PYTHON), "-X", "utf8", str(script), str(wav), model],
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
        f"CV3 ASR 失败 exit={proc.returncode}\n"
        f"stdout尾: {out_lines[-3:] if out_lines else '空'}\n"
        f"stderr尾: {(proc.stderr or '').strip().splitlines()[-3:] if (proc.stderr or '').strip() else '空'}"
    )


def asr_transcribe(wav_path: str | Path, model: str = "auto", timeout: int = 600) -> dict:
    """转写 WAV 为文本。返回 dict（含 ok/text/language/model/wav）。

    model="auto"：首选 faster-whisper medium（CUDA），失败自动回退
    whisper base（legacy 兜底）；model 为其他值时走 legacy openai-whisper。
    调校（T2）：常驻服务优先（模型热缓存），服务不可用回退冷启动子进程。
    """
    wav = Path(wav_path)
    if not wav.is_file():
        raise FileNotFoundError(f"音频不存在: {wav}")
    if model == "auto":
        # 识别主链路切换（2026-10-27 Owner 拍板，按 10-26 调研结论）：
        # sherpa-onnx SenseVoice（离线，中文 CER 7-10% < faster-whisper ~20%，
        # 专治弱信号/噪声）升级为首选；faster-whisper medium（daemon 热缓存）降为兜底。
        # 弱信号补偿：_run_sherpa 内置自适应增益（SenseVoice 对 <0.05 峰值偏差大的
        # 历史问题，由增益归一化解决，不依赖 GAIN 后置）。
        if _sherpa_asr_available():
            try:
                result = _run_sherpa(wav)
                if result.get("ok") and result.get("text"):
                    return result
                if result.get("ok") and not result.get("text"):
                    print(f"ASR sherpa empty text, fallback daemon: {wav.name}")
            except Exception as exc:
                print(f"ASR sherpa unavailable, fallback daemon: {exc}")

        # 兜底1：常驻 faster-whisper medium（daemon 热缓存）
        try:
            from src.brain.voice.daemon import daemon_asr_transcribe

            daemon_result = daemon_asr_transcribe(wav, timeout=timeout)
            if daemon_result is not None and daemon_result.get("ok"):
                return daemon_result
            if daemon_result is not None and not daemon_result.get("ok"):
                print(f"ASR daemon transcribe failed, fallback cold-start: {daemon_result.get('error')}")
        except Exception as exc:  # 常驻通道任何异常均回退，不影响主链路
            print(f"ASR daemon unavailable, fallback cold-start: {exc}")

        # 兜底2：faster-whisper 冷启动 → legacy whisper base
        try:
            return _run_faster_whisper(wav)
        except RuntimeError as faster_error:
            return _run_whisper_legacy(wav, "base", timeout)
    return _run_whisper_legacy(wav, model, timeout)


def asr_probe(timeout: int = 120) -> dict:
    """探测 ASR 链路（不加载模型）：验证子进程/vendor/whisper import。"""
    script_src = r"""
import os, sys, json
os.environ.setdefault("HF_HUB_OFFLINE", "1")
os.environ.setdefault("TRANSFORMERS_OFFLINE", "1")
os.environ.setdefault("PYTHONNOUSERSITE", "1")
import whisper  # 仅 import，不 load_model
import torch
print(json.dumps({"ok": True, "whisper": whisper.__version__ if hasattr(whisper, "__version__") else "imported",
                  "torch": torch.__version__, "cuda": bool(torch.cuda.is_available())}))
"""
    tmp = Path(__import__("tempfile").gettempdir()) / "ultima-voice"
    tmp.mkdir(parents=True, exist_ok=True)
    script = tmp / "asr_probe.py"
    script.write_text(script_src, encoding="utf-8")

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
        f"CV3 ASR 探测失败 exit={proc.returncode}\n"
        f"stdout尾: {out_lines[-3:] if out_lines else '空'}\n"
        f"stderr尾: {(proc.stderr or '').strip().splitlines()[-3:] if (proc.stderr or '').strip() else '空'}"
    )


if __name__ == "__main__":  # pragma: no cover - CLI 探测入口
    import argparse

    parser = argparse.ArgumentParser(description="CV3 ASR 单次转写/链路探测")
    parser.add_argument("wav", nargs="?", default="")
    parser.add_argument("--model", default="auto")
    parser.add_argument("--probe", action="store_true", help="链路探测（不加载模型）")
    args = parser.parse_args()
    if args.probe:
        result = asr_probe()
        print(json.dumps(result, ensure_ascii=False, indent=2))
    else:
        result = asr_transcribe(args.wav, args.model)
        print(json.dumps(result, ensure_ascii=False, indent=2))
