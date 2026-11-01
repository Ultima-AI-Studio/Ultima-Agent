# 中文持续流 KWS 独立验证路径

当前实现：WeKws 官方 FSMN-CTC 持续流运行时 + 其配套中文预训练权重。
默认测试词为“你好问问”，固定测试阈值 0.5；未校准为产品默认值。
旧语音服务、幂幂配置和原 KWS 参数保持不变。当前入口仅支持离线 WAV，不启动麦克风或播放。

## 环境

从项目根在 PowerShell 7 运行：

```powershell
./src/voice-next/bootstrap.ps1
./tools/venv-voice-next/Scripts/python.exe -m pytest ./src/voice-next/test_stream_runner.py -q
./tools/venv-voice-next/Scripts/python.exe ./src/voice-next/stream_runner.py --wav <mono-pcm16-16000hz.wav> --output ./data/evidence/voice-next/result.json
```

bootstrap 需要本机 uv 与既有 tools/venv-openjarvis Python 解释器。依赖仅安装到新环境。
固定源码和模型按锁文件校验 SHA256；缺少下载或校验失败即停止，不回退旧引擎。
WeNet 仅使用未改动的三个 tokenizer/文件工具模块，避免导入整个 ASR 命令行和无关依赖；保留上游许可证。

## 流式边界

- 每包为 300ms PCM，跨包保留官方音频、特征、模型与解码缓存。
- 模型前端、模型、CTC 解码与检测全部调用官方实现；词表转换复用官方 FSMN recipe。
- 包结果可在文件结束前产生，不靠 EOS、句末 VAD 或 ASR 文字匹配触发。
- 每个文件前后调用 reset_all 完全隔离会话；末尾未满足特征上下文的数据不会通过补造音频强行终结。
- 支持的模型 token 不等于所有自定义词都已验证；“幂幂”未验收。

## 验证含义

人工合成的正样本重复重放仅是冒烟测试；接口单测和合成静音不能证明真人召回、背景误唤醒或远场质量。
报告分别记录包处理耗时、模型事件和音频输入进度。事件自报时间不是人工标注的词尾延迟。
没有人工 gold 的质量指标为 null。CPU 实时处理能力与用户实际响应时间分开判断。

下一门：固定词真人音频和自然背景声评测，然后接入真实采集与交互；通过后再迁移 ASR。
未经实测不宣称达到小爱 L05C，也不自动切换生产入口。
