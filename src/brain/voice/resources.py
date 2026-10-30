"""CV3 语音链路：只读资源路径解析与探活（P1 补建）。

集中登记 environment-spec v1.4 已验证的 CV3 资源路径（只读引用，
绝不写入备份区）。提供探活函数，供 TTS/ASR 桥接层启动前校验。
"""

from __future__ import annotations

from pathlib import Path

# 只读资源根（Topo Backup 备份区，environment-spec v1.4 登记）
TOPO_BACKUP_ROOT = Path(r"H:\UltimaAI\UltimaAgent\Topo Backup\C_Guixu")

# CV3 推理运行库（Python 3.10.22 独立运行时）
CV3_RUNTIME_PYTHON = (
    TOPO_BACKUP_ROOT
    / r"v0r3\cv3\TtsProbe\runtime310\python\python.exe"
)

# CV3 模型目录（VOICE_041 QA models，75/75 哈希校验通过）
CV3_MODEL_ROOT = (
    TOPO_BACKUP_ROOT
    / r"source\guixu-v1.04.00-phase6.3.02-cross-platform-matrix\apps\desktop-host-winui\qa\VOICE_041_V0_20261010_R1\models"
)

# CosyVoice3 源码（推理导入路径）
COSYVOICE_SOURCE = (
    TOPO_BACKUP_ROOT
    / r"v0r3\cv3\TtsProbe\source\CosyVoice-074ca6dc9e80a2f424f1f74b48bdd7d3fea531cc"
)

# 关键模型文件（CosyVoice3 必需）
CV3_REQUIRED_FILES = (
    "cosyvoice3.yaml",
    "llm.pt",
    "flow.pt",
    "hift.pt",
    "speech_tokenizer_v3.onnx",
)

# ASR 模型（sherpa-onnx sensevoice / whisper 备选）
ASR_MODEL_DIRS = (
    "sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2024-07-17",
    "sherpa-onnx-qwen3-asr-0.6B-int8-2026-03-25",
)


def check_cv3_resources() -> dict[str, bool]:
    """探活 CV3 推理必需资源（不加载模型，只校验路径与关键文件）。"""
    report = {
        "runtime310_python": CV3_RUNTIME_PYTHON.is_file(),
        "cosyvoice_source": COSYVOICE_SOURCE.is_dir(),
        "model_root": CV3_MODEL_ROOT.is_dir(),
    }
    for name in CV3_REQUIRED_FILES:
        report[f"model:{name}"] = (CV3_MODEL_ROOT / name).is_file()
    report["asr:sensevoice_dir"] = (CV3_MODEL_ROOT / ASR_MODEL_DIRS[0]).is_dir()
    report["asr:qwen3_dir"] = (CV3_MODEL_ROOT / ASR_MODEL_DIRS[1]).is_dir()
    return report


def all_cv3_resources_ready() -> bool:
    """全部必需资源就绪判定（运行时桥接前置门）。"""
    report = check_cv3_resources()
    required = [
        "runtime310_python",
        "cosyvoice_source",
        "model_root",
    ]
    required += [f"model:{n}" for n in CV3_REQUIRED_FILES]
    return all(report.get(k, False) for k in required)


def asr_model_path(which: str = "sensevoice") -> Path | None:
    """返回 ASR 模型目录绝对路径；不存在返回 None。"""
    if which == "qwen3":
        p = CV3_MODEL_ROOT / ASR_MODEL_DIRS[1]
    else:
        p = CV3_MODEL_ROOT / ASR_MODEL_DIRS[0]
    return p if p.is_dir() else None
