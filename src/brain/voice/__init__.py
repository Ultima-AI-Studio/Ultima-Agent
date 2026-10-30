"""P1 语音链路（CV3）封装包。

ADR-005/ADR-009 冻结基线：CosyVoice3 合成（TTS）+ sherpa-onnx/whisper
识别（ASR），本地推理，零外部模型请求。

关键事实（environment-spec v1.4 已验证）：
- CV3 推理运行库 = runtime310（Python 3.10.22 + torch 2.3.1+cu121），
  位于 Topo Backup 备份区（只读引用，绝不修改）；
- 模型目录 = VOICE_041 QA models（CosyVoice3 全套 + sherpa-onnx
  ASR/VAD/KWS + whisper），哈希已校验 75/75；
- UltimaAgent 底座 venv（Python 3.13）不装 CV3 重依赖，
  推理经独立子进程（runtime310 python）桥接。

本包职责：对外提供统一 TTS/ASR 接口，内部管理推理子进程与
只读资源路径解析。写域仅 H:\\UltimaAI\\UltimaAgent\\。
"""
