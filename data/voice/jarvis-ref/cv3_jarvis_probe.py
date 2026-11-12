"""CV3 贾维斯音色验证脚本：monkey-patch PROMPT_WAV → 新参考音频，走 CV3 冷启动合成。

- 复用 tts.py 的 CV3 子进程推理（runtime310），不经 edge/piper/sherpa/daemon 优先链；
- 输出 WAV 落 data/voice/jarvis-ref/，验证换音色链路；
- 仅本地推理（HF_HUB_OFFLINE=1），不联网。
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
from pathlib import Path

# 直跑入口：保证 src 包可导入
sys.path.insert(0, r"H:\UltimaAI\UltimaAgent")

import src.brain.voice.tts as tts

# 关键：把模块级 PROMPT_WAV 指向新参考音频（而非 CosyVoice 自带默认音色）
REF_WAV = Path(r"H:\UltimaAI\UltimaAgent\data\voice\jarvis-ref\jarvis_voice_ref_pcm16.wav")
assert REF_WAV.is_file(), f"参考音频缺失: {REF_WAV}"
tts.PROMPT_WAV = REF_WAV

TEXT = sys.argv[1] if len(sys.argv) > 1 else "先生，有什么可以为您效劳？"
OUT = Path(r"H:\UltimaAI\UltimaAgent\data\voice\jarvis-ref\jarvis_cv3_out.wav")

if not tts.all_cv3_resources_ready():
    raise RuntimeError("CV3 资源未就绪，拒绝验证")

script = tts._render_script()  # 渲染时取 monkey-patch 后的 PROMPT_WAV
env = dict(os.environ)
env["PYTHONPATH"] = str(tts._VENDOR_DIR) + (
    os.pathsep + env["PYTHONPATH"] if env.get("PYTHONPATH") else ""
)
print(f"prompt_wav -> {REF_WAV}")
print(f"text       -> {TEXT}")
print(f"runtime    -> {tts.CV3_RUNTIME_PYTHON}")
proc = subprocess.run(
    [str(tts.CV3_RUNTIME_PYTHON), "-X", "utf8", str(script), TEXT, str(OUT)],
    capture_output=True,
    text=True,
    timeout=600,
    env=env,
    creationflags=getattr(subprocess, "CREATE_NO_WINDOW", 0),
)
out_lines = (proc.stdout or "").strip().splitlines()
last = out_lines[-1] if out_lines else ""
if last.startswith("{"):
    result = json.loads(last)
    print(json.dumps(result, ensure_ascii=False, indent=2))
    if result.get("ok") and OUT.is_file():
        # 近静音检查
        silent = tts.tts_output_is_near_silent(OUT)
        norm = tts.normalize_tts_wav(OUT)
        print(f"near_silent={silent} normalized={json.dumps(norm, ensure_ascii=False)}")
        print(f"FINAL: {OUT}")
else:
    print(f"exit={proc.returncode}")
    print("stdout尾:", out_lines[-3:] if out_lines else "空")
    print("stderr尾:", (proc.stderr or "").strip().splitlines()[-3:] if (proc.stderr or "").strip() else "空")
    raise SystemExit(1)
