# 新中文语音入口

当前KWS直接使用Sherpa-ONNX官方Zipformer原生持续流接口（3M/2025-12-20，chunk16 fp32）。实际监听固定使用“你好问问”；旧profile的“幂幂”不控制新入口。
ASR继续复用现有本地SenseVoice；语义交互和悬浮球推送复用现有管线。
新入口临时使用Windows本地SAPI语音：原CV3冷启动联调等待数分钟，因此本轮不启动CV3，原音色配置和源码保留。

## 启动与状态

从项目根在PowerShell7运行（启动会使用麦克风，并播放就绪/唤醒提示和回复）：

```powershell
./src/voice-next/bootstrap-live.ps1
./tools/venv-voice-next/Scripts/python.exe ./src/voice-next/launch.py
./tools/venv-voice-next/Scripts/python.exe ./src/voice-next/launch.py --status
./tools/venv-voice-next/Scripts/python.exe ./src/voice-next/launch.py --stop
```

启动器只启动新监听；发现旧语音入口运行时拒绝并报告，不终止既有进程。
通过独立OS锁保证新监听单实例，停止请求绑定当前run_id，不按陈旧PID杀进程。
依赖只安装新venv；ASR常驻worker使用原venv-asr，避免合并两套模型依赖。
必要时仅补启动已确认8756未占用的项目主脑；不重复启动、不加载额外LLM模型进行预热。

听到“新语音入口已就绪”后，说“你好问问”；听到“在呢，请说”后再说指令，例如“现在几点”。
配置：config/voice-next/live.json。当前选定USBAudio2.0物理麦克风/WASAPI与LOFREE输出，以名字和API解析，不依赖旧设备索引。
状态：data/voice-next/status.json，包含PID/run_id、唯一生效词、真实设备、采集回调/模型包计数、心跳、最近唤醒和转写。
启动器只有在真实采集回调与模型包计数均递增、worker已预热且锁/心跳有效时才报告ready。
READY只证明运行入口就绪；真人唤醒成功必须有对应真实事件。

## 音频与回合

回调只做有界复制入队；SoXR跨块重采样到16k，官方KWS流由单线程持有；完整PCM16输入只喂一次，不补EOS或滑窗重放。断流/队列溢出统一重置。
无旧自动增益或二次电平门控。当前USB输入使用固定软件增益10倍、新KWS阈值0.25（官方默认工作点）；电平状态显示增益前原始输入。两段本机真人录音的多起点复验用于选型，稳定性仍需真人验收。忙时继续读取但丢弃回声，避免旧音频积压。
唤醒后本地即时提示；WebRTC VAD 20ms判帧、保留前沿、5秒等待开口/15秒总上限/0.8秒静音收尾。
只将唤醒后的指令WAV保存到data/voice-next/commands；不上传录音、不保存连续背景音。
新入口暂不支持通过旧换词协调器修改唤醒词，避免改旧profile却没有改新模型。

## 离线验证与保留的失败原型

```powershell
./tools/venv-voice-next/Scripts/python.exe -m pytest ./src/voice-next/test_kws_backend.py ./src/voice-next/test_live.py ./src/voice-next/test_stream_runner.py ./src/voice-next/test_turn_worker.py -q -p no:cacheprovider
./tools/venv-voice-next/Scripts/python.exe ./src/voice-next/stream_runner.py --wav <mono-pcm16-16000hz.wav> --output ./data/evidence/voice-next/result.json
```

新模型从官方归档下载到models/voice-next独立副本，以归档和四个运行文件SHA256锁定；依赖锁为requirements-live.lock.txt，实时入口不导入Torch。kws_backend.py只调用官方流生命周期和检测接口，不修改原生解码器；关键词发音遵循官方phone+ppinyin机制，只有三声变调和轻声变体，均显示同一词。未自研KWS/ASR/VAD算法。官方文档：https://k2-fsa.github.io/sherpa/onnx/kws/pretrained_models/index.html。
bootstrap.ps1与stream_runner.py保留WeKws离线原型及其锁定源码；该原型在真人分块起点测试中漏检，已退出实时入口。stream_runner.py命令仅测试该旧原型。
合成样本是冒烟证据，不是远场稳定性证明。无人工gold的召回/FPR/词尾延迟为null。
