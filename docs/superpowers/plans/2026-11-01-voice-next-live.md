# 新 KWS 实际监听与语音交互接入

用户授权：此前已要求实现切换；当前“我喊了你好问问没有回应”明确要求可实际唤醒。0019只完成离线技术证明，不能当作已上线。
目标：把已验证 WeKws 模型接入真实麦克风，喊“你好问问”后有即时听得见的反馈，并能采集后续指令交给现有ASR/交互/TTS。保持旧实现可回退，不再让用户猜哪个词生效。

写域：src/voice-next/新增 live.py、turn_worker.py、test_live.py、launch.py（如需）、README/requirements锁；config/voice-next/live.json；data/voice-next/（日志、状态、仅唤醒后指令WAV、提示音）；data/evidence/voice-next-live/；本计划/新工单/项目队列表与全局本登记行；docs/reports/voice-next-live-20261101.md。
禁止：不改旧daemon、原KWS阈值/词表、原voice-profile、ASR/TTS算法；不结束既有不相关进程；不重启机器；不上传录音；不改系统默认音频设备/音量；不接管其他项目。
允许：新监听使用麦克风与播放唤醒/应答音（用户正在要求实际喊醒）；只保存唤醒后的指令音频到新路径。模型与依赖只安装新环境。必要时仅启动已确认未运行的8756项目主脑服务，不重复启动。

架构：官方WeKws持续流KWS，新模型/新配置仅认你好问问；sounddevice连续回调采集，使用SoXR有状态重采样，输入块不能丢失后继续沿用旧模型缓存；无旧AGC和二次能量门控。原生采样率按指定物理设备/WASAPI打开，按名字+hostapi解析而非依赖易漂移的索引。输出指定LOFREE WASAPI。声学信号仅诊断，不虚报人声准确率。
唤醒反馈与命令：本地预生成简短提示，唤醒后立即播放。输入回调始终持续读取，播放期间只丢弃自身回声并重置处理状态。官方WebRTC VAD判段（16k PCM20ms，保留短指令前沿），有界等待/录音；串行处理单回合，忙时丢弃采集避免积压/自唤醒。
交互：旧venv-asr运行独立常驻子进程，复用原ASR与VoiceInteractionLoop，不在新环境装旧模型依赖；按JSON行IPC返回转写/应答与音频路径。新路径禁止通过旧换词协调器修改旧profile，明确固定新词。联调已证实旧CV3冷启动会让单次回复等待数分钟，且其ready_timeout不受reply_timeout约束。本轮新入口显式使用Windows本地SAPI作为冷启动降级，不启动旧CV3，保留原音色配置与实现；不让语音回复阻塞新KWS就绪。错误仍需有可听见的明确提示。所有工作进程只归属本服务；启动单实例OS锁，不删除既有锁。

T0：确认无旧语音进程/端口冲突，记录进程身份与设备枚举；独立计划评审exact SHA通过。
T1：先写失败测试，覆盖有状态分包/断流复位、WebRTC判段前沿与超时、会话不重叠和输入/输出设备选择，不以假KWS替代真实模型。
T2：实现CLI与常驻worker，离线合成样本穿过实际新消费循环，真实ASR+TTS接口至少验证时间指令；音频输出路径和错误回执可读。
T3：独立审计代码/测试与已有证据；通过后启动新监听，读取OS PID创建时间、单实例锁、状态心跳、真实采集回调/模型包计数和错误日志，不能只凭进程存活标记通过。
T4：声告入口已就绪，提供唯一当前唤醒词；真人唤醒是否成功必须等用户实际发声与日志命中确认，未观察到不得写PASS。提交/tag/推送与报告如实区分已运行、命中、ASR回复和真人质量。

指标：没有人工标注的召回/FPR/词尾延迟仍null。新环境预热后再开麦。输出实际设备名字、词、阈值、模型身份、ready时间与每次状态转移。不同时迁移ASR引擎。

修订2（实测裁决）：既有VoiceInteractionLoop会更新data/host/orb_command.json，列入必要交互写域；复用ASR/TTS调用产生的既有工作缓存%TEMP%/ultima-voice及既有data/logs下临时后台脚本亦属于兼容调用写域，不改模型/算法/凭据。原CV3联调自然结束，未执行进程终止；保留慢调用证据，不用其完成速度证明交互可用。

修订3（真人失败后的修复边界）：用户已授权的本机录音诊断证明实际语音存在，不能据短录音空窗判定硬件故障。允许修复新路径stream_runner.py中对官方运行时is_sublist的兼容绑定，并在test_stream_runner.py覆盖最后合法偏移；固定来源代码、模型权重与旧路径保持原样。新live.json允许为当前USB输入设固定input_gain与新KWS阈值，不使用动态AGC或旧路径参数。修复后必须先以本机已录真人片段通过实际重采样/分包链复验，并保留背景、非关键词与静音对照；独立复核后才重启本服务。单段样本只支持再次真人试用，不构成召回/FPR或远场质量验收。

修订4（连续流起点稳定性裁决）：三路同步录音电平一致，排除以API差异解释全部漏检。同一保存录音改变25ms级前导静音，WeKws仅4/12起点有命中，第二次发声漏检，判退当前真人入口。只读对照官方Sherpa原生KeywordSpotter（本机现成2025-12-20/3M、chunk16 fp32）时，两段真人录音各两次喊词在4种起点、1/10倍固定增益下均各命中2次，非关键词和静音无命中。该有限结果只用于选型和重新试用。
实施范围扩展：src/voice-next/kws_backend.py、test_kws_backend.py、bootstrap-live.ps1及live.py/README/依赖锁，config/voice-next/sherpa-kws.lock.json、keywords.txt和live.json；模型仅写models/voice-next/，下载缓存仅tools/voice-next/，保留已有WeKws源码/模型与失败证据。以官方归档/摘要校验新模型副本，不写旧模型目录。直接调用官方accept_waveform/is_ready/decode_stream/get_result与create_stream/reset_stream，不自研解码、特征或增益算法；新路径固定唯一显示词你好问问，词表只含普通话三声变调/轻声的发音形式，不连接旧profile或旧自适应阈值。常驻监听不加载Torch/WeKws；新模型状态复位仅调用官方流生命周期。
实施前先补会失败的适配回归；实施后真人两段均穿过实际48k重采样/有状态分包，复验12种起点、负对照、重置不残留事件和CPU实时预算；独立代码审计PASS后才重启本服务，再请用户做一次实时闭环。沿用SenseVoice/WebRTC VAD/SAPI和已审启动/IPC生命周期，其他禁改与真人质量指标null边界不变。
