# UltimaAgent KWS 唤醒参数基线（权威单一来源）

- **文档定位**：UltimaAgent 语音入口（关键词唤醒 KWS）的参数、设备、阈值唯一权威基线。任何 KWS 相关调整必须先读本文件，禁止凭记忆或只改代码注释。
- **创建**：2026-10-29（固化 10-26/10-27 多轮真机调参结论 + 10-29 修复记录）
- **适用入口**：`src/brain/voice/kws_listener.py`（产品主入口）；历史 daemon `data/logs/voice-listen-daemon.py` 为同参数的第二实现，以本文件为准。

## 一、麦克风设备（关键，勿再漂移）

| 项 | 值 | 说明 |
|---|---|---|
| 有效输入设备 | **惠普 USB 麦克风**（系统名 USBAudio2.0，sounddevice **MME index=1**） | **2026-10-29 19:4x 实测（摄像头拔除后重新确认）**：6s 录音 peak=0.1173（说话段 2.0~4.5s），ASR 完整识别"贾维斯查一下今天的天气"。**历史"USBAudio2.0 无拾音（peak=0.0000）"结论作废**——当时用户未用该麦说话 |
| 已拔设备 | Razer Kiyo 摄像头麦（MME index=3） | 用户已于 2026-10-29 19:4x **拔除**，sounddevice 中已不存在；daemon 若仍锁 3 会 PortAudioError -9999 死循环（18:29:53 实测） |
| 废弃设备 | 设备 12（主声音捕获/跟随系统默认） | 实测收不到用户语音（peak=0.0000），不可靠 |
| kws_listener 常量 | `MIC_DEVICE = 1` | 2026-10-29 19:4x 从 3 改为 1（惠普麦） |
| daemon 常量 | `DEV_IN = 1` | 2026-10-29 19:4x 从 3 改为 1（惠普麦） |
| 输出设备 | `PLAY_DEVICE = 26`（耳机 POISON M@LOFREE，WASAPI） | TTS 回放 |

> **教训（2026-10-29 三次）**：① 同一台机器的麦克风设备配置曾存在于两个脚本（daemon 与 kws_listener），10-26 只修了 daemon，kws_listener 遗留 index=1 导致唤醒再次失败。② 写死设备常量会在"用户切换实际使用麦克风"（摄像头麦→耳机麦）时失效。③ **"跟随系统默认（设备12）"并非可靠方案**——实测默认端点收不到用户实际语音（可能指向耳机/虚拟设备），**必须以真机实测能收到语音的设备为准（Razer Kiyo=3），禁止凭空切换到"系统默认"**。设备常量统一以本文件为准，两处代码必须同值。

## 二、KWS 模型与唤醒词

| 项 | 值 |
|---|---|
| 模型 | `models/sherpa/kws/sherpa-onnx-kws-zipformer-zh-en-3M-2025-12-20`（zipformer transducer，chunk-8） |
| 唤醒词文件 | `models/sherpa/kws/keywords.txt`（**6 个「贾维斯」发音变体**，拼音音素级；含 ULTIMA 备选；2026-10-30 #133 从 2 行扩至 6 行） |
| 检测窗口 | 1.0s，重叠 0.3s |
| 采样率 | 16000 Hz（KWS 模型输入）。**采集侧（daemon）：44.1k 原生采集 + 窗口 sinc 多相滤波降采样 16k（2026-10-29 冻结）**——惠普麦 MME 驱动不支持 16k 打开（16k 流信号全零），故 44.1k 采集后高质量降采样；**禁止 np.interp 线性插值**（频谱混叠压低唤醒置信度，已 A/B 验证）。若未来 WASAPI 能以 16k 原生打开，优先原生并重测冻结 |

## 三、KWS 识别参数（sherpa KeywordSpotter，真机验证基线）

| 参数 | 值 | 说明 |
|---|---|---|
| `keywords_threshold` | **0.08（固定）** | 10-26 从 0.2→0.08；10-29 修复 kws_listener 动态阈值上浮问题，固定 0.08 与 daemon 一致 |
| `max_active_paths` | 8 | 容纳连读/快慢速变体 |
| `num_trailing_blanks` | **8（2026-10-30 0→8，见第七节）** | sherpa 文档：keywords 有重叠 token 时应调大（如 8）；6 变体高度重叠，0 导致间歇漏唤醒（08:21 三次强信号未命中实证） |
| `keywords_score` | **2.0（2026-10-30 #133 落地值真机回归回退；顶部汇总回写，与变更记录一致）** | 灵敏度主要承担参数：score 越高越易检出（官方漏检方向），threshold 红线不动的替代提级手段 |

> **⚠ 阈值机制红线（2026-10-29 修复）**：kws_listener 曾把固定阈值改成"动态自适应"（安静环境阈值上浮至 ~0.15），导致弱电平唤醒词（peak 0.006~0.05）被拒——**"按了参数调了却还不灵"的根因**。动态阈值逻辑已移除（`_adjust_threshold` 现为 no-op），检测与 rearm 均固定 0.08。**禁止再引入任何会改变有效阈值的自适应逻辑。**

## 四、唤醒段自动增益（采集侧，真机验证基线）

| 参数 | 值 | 说明 |
|---|---|---|
| `IDLE_GAIN` | 4.0 | 静音期基础放大（唤醒词开头即有电平，防第一遍听不到） |
| `NOISE_GATE` | 0.0015 | 低于此视为静音，不放大 |
| `TARGET` | 0.6 | 增益目标峰值 |
| `MAX_GAIN` | 30.0 | 增益上限 |
| `VOICE_START` | 0.008 | 静音→有声跳变判定，瞬时切满增益 |
| 平滑爬升系数 | 0.3 / 0.7 | prev×0.3 + target×0.7 |

## 五、指令采集与门控（唤醒后）

| 参数 | 值 | 说明 |
|---|---|---|
| `GAIN` | 30.0 | 对话回合录音增益 |
| `MIN_LEN` | 0.5s | 最短有效语音 |
| `END_SIL` | 1.2s | 结束静音（**#134 后降级为能量兜底**：主判段为 Silero VAD min_silence=0.5s，VAD 段提交即说完；此值仅 VAD 漏检时能量路径兜底触发） |
| `MAX_LEN` | 8.0s | 单段录音上限 |
| 有效语音门控 | 块峰值>**0.01** 累计≥**0.4s** 且 rms≥**0.002** | 防 whisper 幻觉补全；**2026-10-29 从 1.0s/0.008 放宽**：用户喊"贾维斯"后接短指令（如"查天气"仅 0.6~0.7s）被 1.0s 门槛卡掉导致"没反应"；0.4s 可覆盖三字短指令，仍过滤环境碎音。**2026-10-30 回写 0.015/0.005→0.01/0.002（惠普麦低电平适配，见第七节）** |
| 采集能量阈值 | 0.01 | 10-26 从 0.004 上调 |
| `BEEP_SETTLE_SEC` | **1.2s（2026-10-30 回写：daemon 保持 1.2，防提示音残响安全垫，与变更记录一致；基线 1.0 时曾"喊完立刻退出"）** | **2026-10-29 新增**：提示音（LOFREE 音箱"叮"）被同一麦克风（Razer Kiyo）采回，会触发"检测到语音"→ 提示音一停 1.2s 即判定说话结束直接退出（用户"喊完立刻退出、不等我说话"）。静置期内音频只收帧不做语音判定，等提示音残响平息 |

## 六、链路与验证证据

```
Razer Kiyo(3) → KWS 0.08 固定阈值命中「贾维斯」→ 提示音 → 指令采集(门控)
 → ASR(SenseVoice/sherpa) → InteractionOrbBridge → 悬浮球推送 → edge-tts 回放 → 回待唤醒
```

历史真机验证记录（详见 docs/reports/l7-voice-entry-acceptance-20261025.md）：
- 10-26 16:55：三次"贾维斯"全部命中（threshold 0.12 生效），用户确认灵敏度达标
- 10-26 17:08-17:09：全链路闭环（命中→指令→ASR→推送→回放），用户确认"这回可以了"
- 10-26 17:27：DEFECT-010 修复后连续 8 次单次命中即唤醒
- 10-29 09:00：修复设备漂移（MIC_DEVICE 1→3）+ 阈值固定 0.08，KWS 日志确认监听就绪

## 七、变更记录

| 日期 | 变更 | 原因 |
|---|---|---|
| 2026-10-26 | 阈值 0.2→0.12、增益目标 0.5→0.6、爬升 0.3/0.7、噪声门 0.002→0.0015 | 用户反馈唤醒灵敏度不足（DEFECT-007/008） |
| 2026-10-26 | 设备切 Razer Kiyo（daemon DEV_IN=3）；IDLE_GAIN=4.0、VOICE_START=0.008 | USBAudio2.0 硬件无拾音；静音后第一遍听不见（DEFECT-007/010） |
| 2026-10-27 | 参数迁入 kws_listener.py（阈值仍误为动态） | 10-27 审计发现调优未迁移 |
| 2026-10-29 | **MIC_DEVICE 1→3（kws_listener 同步）**；**阈值固定 0.08（移除动态上浮）** | 真机实测唤醒失败：设备漂移 + 动态阈值上浮至 0.15 拒收弱电平语音 |
| 2026-10-29 | **DEV_IN/MIC_DEVICE 3→12（跟随系统默认麦克风）** | 用户戴 BlackShark V2 Pro 耳机说话，声音进耳麦；摄像头麦（固定 3）收不到，拾音电平仅基线 1/10 致唤醒迟钝。设备 12=主声音捕获驱动，自动跟随 Windows 默认输入 |
| 2026-10-29 | **DEV_IN/MIC_DEVICE 12→3（回滚锁定）** | 实测设备 12 收不到用户语音（peak=0.0000）而设备 3 正常（17:52:03 成功 ASR"今天天气怎么样"）；"跟随系统默认"不可靠，**以真机实测能收到语音的设备为准** |
| 2026-10-29 | **指令门控 1.0s/0.008 → 0.4s/0.005**；**新增 BEEP_SETTLE_SEC=1.0s 提示音静置期** | 用户反馈①喊"贾维斯查天气"没反应（短指令 0.6~0.7s 被 1.0s 门槛卡掉）；②喊完立刻退出不等说话（提示音被同一麦克风采回触发语音判定，提示音停 1.2s 即结束）。修复：门槛放宽 + 静置期只收帧不判定 |
| 2026-10-29 | **DEV_IN/MIC_DEVICE 3→1（Razer Kiyo → 惠普 USB 麦 USBAudio2.0）** | 用户拔除摄像头（Razer Kiyo 随之消失），daemon 锁 3 导致 -9999 死循环。实测设备 1（MME-USBAudio2.0）6s 录音 peak=0.1173、ASR 完整识别，确认为惠普麦。**修正历史错误结论：USBAudio2.0 并非无拾音** |
| 2026-10-29 | **44.1k→16k 降采样：np.interp 线性插值 → 窗口 sinc 多相滤波（方案 A，冻结）** | 用户反馈"贾维斯"仍需喊两遍。调研发现：daemon 为兼容惠普麦 MME 驱动（不支持 16k 打开）被迫 44.1k 采集，但 np.interp 线性插值产生频谱混叠压低 KWS 置信度。离线 A/B（30 真实唤醒样本 × 2 阈值）：linear 6/60=10.0% vs sinc 8/60=13.3%，sinc 相对提升 33% 且零回归。**已改 daemon `_resample_16k()` 为窗口 sinc（up=160/down=441、Blackman 窗 half=32、cutoff=8k/44.1k），冻结此算法**。注意：基线"禁止 44.1k→16k 插值"红线指禁止**线性插值**劣质降采样；sinc 多相滤波为高质量降采样，是 MME 限制下的正确替代。若未来能用 WASAPI 以 16k 原生打开惠普麦，仍优先原生 16k（届时需重测冻结）。 |
| 2026-10-30 | **daemon `keywords_threshold` 0.04→0.08（回正基线红线）** | #132 参数对齐。10-29 19:2x 曾调低 0.04（用户"贾维斯"语速快/短促置信度不足）；本次回正固定红线 0.08，灵敏度损失由 #133 keywords_score 提级（1.0→3.0 A/B）承担。 |
| 2026-10-30 | **daemon `QUIET_AFTER_SPEECH` 3.0→1.2（回正基线 END_SIL）** | #132 参数对齐。10-29 19:5x 曾 1.2→3.0（用户停顿组织指令被掐断）；本次回正 1.2 同时确认 collect() 两段语义保护在位（静置期只收帧不判语音 + spoken 前置才判说完，停顿窗口不判说完），省 ~1.8s/次。最终由 #134 VAD 断句（0.5s）接管。**真机回归重点观察：提示音残响是否触发 spoken 误判（若复现掐断，转 #134 VAD 处理）。** |
| 2026-10-30 | **daemon `BEEP_SETTLE_SEC` 保持 1.2（基线 1.0，微漂移不硬回正）** | #132 对齐结论：1.2 为防提示音残响被当语音的安全垫（基线 1.0 时曾出现"喊完立刻退出"），保留 1.2 不冒险缩回。 |
| 2026-10-30 | **daemon `keywords_score` 1.0→3.0（提级承担 #132 阈值回正的灵敏度损失）** | #133 KWS 补发音变体+score A/B。白龙马实测 score=3 召回 13/17 vs 2.0 的 9/17；离线 A/B（`data/logs/probe_kws_variant_ab2.py`，threshold=0.08 固定、sinc 重采样）：V0(2行)/V1(6行) × score{1,2,3} 在 4 正样本全命中（零回归）、8 负样本零误唤醒（零误触发）。**score=3.0 为提级落地值；真机 A/B 观察：若误唤醒增多（背景/指令词触发），回退 2.0 并登记。** |
| 2026-10-30 | **keywords.txt 2 行→6 行（「贾维斯」补 5 个发音变体）** | #133 对齐白龙马 6 变体写法（尾音弱化/声调变/吞音/连读）：标准 `j iǎ w éi s ī` + `j ià w éi s ī`（贾四声）、`j iā w éi s ī`（贾一声）、`j iǎ w ei s ī`（维轻声）、`j iǎ w éi s i`（斯轻声）、`j iǎ w éi s`（吞尾音）；ULTIMA 行保留。全部音素经 tokens.txt 校验在位（245 tokens）。离线 A/B 零回归零误触发；**真机验证发音变体是否提升非标准发音召回（快读/东北口音场景）。** |
| 2026-10-30 | **collect() 判段：固定静音 1.2s → Silero VAD 流式断句（#134 实装）** | 审计结论"VAD 断句 P0"。用 sherpa-onnx 集成 Silero VAD（silero_vad.onnx，threshold=0.35、min_silence=0.5s 对齐 OVOS silence_seconds、min_speech=0.25s、window=512）替代 QUIET_AFTER_SPEECH 固定静音判段：VAD 段提交=语音结束+0.5s 静音，比固定 1.2s 快 ~0.7s/次。保留 #132 两段语义保护（settle_until 静置期只收帧不判语音+VAD 段亦不提交、未开口不判完）+ 能量阈值兜底（QUIET_AFTER_SPEECH 1.2 保留为兜底）+ 最短语音门控（VAD 段时长<0.4s 拒绝）。回放验证（vad-segment-replay-20261030.py）：3 个真实样本全部正确分段（段数=1，唤醒词不误断）。asr.py 旧注释"VAD 不产分段"为过时结论（探针实测已产段）。**真机回归重点：0.6s 短指令"查天气"须正常识别；10-29 停顿组织指令场景不得被 0.5s 静音掐断（若掐断调高 min_silence_duration）。** |
| 2026-10-30 | **ASR GPU provider A/B：不落地 provider="cuda"（#135 评估结论）** | 审计"先测再定"。实测（`data/logs/asr-gpu-ab-20261030.py`）：pip 版 sherpa-onnx 2.0.0 **未编译 GPU 支持**（session.cc 提示 `Please compile with -DSHERPA_ONNX_ENABLE_GPU=ON. Available providers: CPUExecutionProvider. Fallback to cpu!`），provider="cuda" 静默回退 CPU；CPU 推理已百毫秒级（5 样本 70~241ms，SenseVoice int8 小模型），瓶颈不在推理。**结论：当前包 GPU 无增益、白付模型创建开销（942ms），不改 provider**；若日后换带 GPU 编译的 sherpa-onnx 构建再重测。faster-whisper 兜底通道本身已走 CUDA（device="cuda"，float16）。 |
| 2026-10-30 | **daemon `keywords_score` 3.0→2.0（#133 落地值真机回归回退）** | 用户复现"喊两遍才应"（与 10-29 同症状）。真机日志 08:09:56~08:10:59 **五次"强信号未命中"**（peak 0.0177~0.0248，用户在喊）仅一次命中——score=3.0 对「贾维斯」偏严（白龙马 3.0 系"小白龙"实测值，不适用本唤醒词）。离线 A/B 已证 2.0/3.0 正负样本无差异（`probe_kws_variant_ab2.py`），回退 2.0 召回更稳。**真机回归重点：单次唤醒即应，且不新增误唤醒。** |
| 2026-10-30 | **collect() 静置期修正：只收帧 → 收帧+喂 VAD（不判段不判能量）** | 用户复现"查天气无回复"。真机日志 08:10:04 开始采集 → 08:10:19 空（15s 超时）：用户听提示音后立刻说 0.6s 短指令"查天气"，整句落在 `settle_until`（BEEP_SETTLE_SEC=1.2s）静置期——原实现静置期只收帧**不喂 VAD**，VAD 从未看到语音 → 15s 无段空采集。修正：静置期也 `vad.accept_waveform`（语音帧进 VAD 缓存，段在语音结束+0.5s 静音后才产出，天然越过静置期）；另防提示音残响段先产出导致整轮误判——VAD 段 <0.4s 跳过继续等真正语音段。**真机回归重点："贾维斯"→提示音→立刻说"查天气"须完整识别。** |
| 2026-10-30 | **collect() VAD 段取值顺序修正：先 `seg.samples` 取值再 `vad.pop()`** | 用户复现"查天气无回复"（唤醒已一遍命中）。真机日志 08:16:42 `TypeError: unsupported operand type(s) for /: 'list' and 'int'` → collect() 崩溃 → 空采集。实测（vad-seg-type-probe）：`SpeechSegment.samples` 是**段 PCM 数组**（list，len 正常时如 29792 ≈1.86s），但 **`vad.pop()` 后 `seg.samples` 被清空为 `[]`**——原实现 pop 后再算 `samples/SR_KWS` 即 TypeError 或 len=0。修正：pop 前先取值 `samples = seg.samples`，`vad_sec = len(samples)/SR_KWS`。离线回放（vad-segment-replay-fixed，3 样本×3 前置静音 0/0.8/2.0s）：9 组全部 ACCEPT（段 0.9~1.57s），无 SKIP 无崩溃。**真机回归重点：提示音后立刻"查天气"须完整识别。** |
| 2026-10-30 | **daemon `num_trailing_blanks` 0→8（KWS 重叠变体区分）** | 用户复现"喊三遍才应"。真机日志 08:21:56/08:22:03/08:22:10 **三次强信号未命中**（peak 0.0347/0.0351/0.0432，人在喊）到 08:22:11 才命中。score=2.0 下 08:23/08:24 又两次一遍命中——间歇性漏唤醒，非 score 单调问题（离线 A/B 已证 2.0/3.0 无差异）。keywords.txt 6 个「贾维斯」变体 token 高度重叠（贾四声/贾一声/维轻声/斯轻声/吞尾音），sherpa-onnx 文档明确：**「keywords 有重叠 token 时应调大 num_trailing_blanks（如 8）」**。0→8 按官方建议补变体间 blank 区分，防重叠路径误归并。**真机回归重点：任意变体发音一遍即应，且不新增误唤醒。** |
| 2026-10-30 | **asr.py `_run_sherpa` 加 VAD 精切（去前导静音/残响再识别）** | 用户复现"查天气"被答成茶叶。真机日志 08:22:16 captured wav（sec=2.25 peak=0.0398）→ sherpa 整段识别"茶天天。"被 Agent 直接采用。离线 A/B（`asr-fine-ab-20261030.py`，真机 wav 回归）：整段直识别 int8→"茶天天"、fp32→"茶天天天"（全错）；**VAD 精切（min_silence=0.25/min_speech=0.2 + 0.05s 边余量）后 int8/fp32 全部 →"查天气。" ✅**。对照 08:23 强信号（peak=0.2749）同链路识别"查一下今天的天气"正确——弱信号 + 前导 0.4s 残响/静音污染是组合根因。asr.py 旧注释"VAD 不产分段"为过时结论（daemon 侧 vad-probe 已产段），删除；`_run_sherpa` 先 VAD 精切再识别，弱信号自适应增益保留在精切后。**真机回归重点：弱麦喊"查天气"须识别为天气查询（不得再答茶叶）。** |
| 2026-10-30 | **输入通道 44.1k→16k vs 模拟 44.1k→48k→16k A/B：48k 通道 PASS，可在能力可用时优先** | 工单 `wo-ultimaagent-20261030-0004` 固定 `threshold=0.08`、`score=2.0`、6 个「贾维斯」变体，对 8 个真实正样本（含强/弱发音）和 8 个本地 ASR 确认无唤醒词负样本运行 `data/logs/kws-44k-vs-48k-ab-20261030.py`。结果：44.1k 正样本 **7/8=87.5%**、48k 正样本 **7/8=87.5%**；两路负样本均 **0/8 误唤醒**，48k 新增误唤醒 0。结论：`prefer_wasapi48k=true` 时可优先能力匹配的 48k WASAPI 端点；48k→16k 使用共享整数 3:1 sinc，44.1k→16k 继续使用共享 441:160 sinc。A/B 只改变降采样通道，不改 KWS/增益/门控基线。完整表见 `data/logs/kws-44k-vs-48k-ab-20261030.txt`。 |
| 2026-10-30 | **基线汇总一致性收敛（#136 前置裁定，工单 0007 T0 受阻触发）** | 0007 T0 只读核对发现三处"实现/追加记录演进后权威汇总未回写"，主脑裁定现行真机基线并回写顶部汇总：① 门控 0.015/0.005→**0.01/0.002**——daemon 为惠普麦低电平适配显式下调（rms=0.0019 被 0.005 门槛卡掉→"唤醒成功但无有效语音"，`voice-listen-daemon.py` 442-448 行注释为证，变更当时未记录，本次补记）；② `keywords_score` 3.0→**2.0**——变更记录第 96 行落地值回退，顶部汇总回写；③ `BEEP_SETTLE_SEC` 1.0→**1.2**——变更记录第 91 行保持值，顶部汇总回写。**裁决：0.002 / 2.0 / 1.2 为冻结权威值；0007 载荷按此重冻结，Codex 从 T0 重跑。** |
| 2026-10-30 | **伪流式实装 + 竞态修复完成；第五派 A1 真麦硬件/驱动静音受阻，待恢复后真机验收（#136）** | `voice-listen-daemon.py` 已落地采集线程 + 识别线程 + `queue.Queue`/`stop_event`、整段 ASR 1s 节流、final 终跑、中间结果隔离、异常/600s 超时串行回退，以及所有线程共用的模块级日志锁；加锁回归 T1-T3 确定性 Gate 6/6 PASS。主脑已纠偏四派“物理距离未确认”归因；第五派按 A1 用同一 USB 麦的 WASAPI 30（48 kHz）独立采集 3.0s，并由 WASAPI 24 完整回放夹具，输入两通道 peak/rms 均为 0.0。依工单明确分支判为硬件/驱动层静音并停止，未消耗一次 daemon 重启授权，运行进程仍未加载工作树日志锁，T4 3+3 与非空下降量未执行，故**不代表 Owner 已冻结或阶段验收已通过**。未改任何 KWS/ASR/VAD/TTS 参数值。 |
| 2026-10-30 | **#136 真机验收 PASS：T4 3+3 首字延迟对比齐（短 +4s / 长 +4s），L26 日志锁回归零新增损坏，可冻结（#136）** | 卡点根因链：① 旧夹具 t4-query-short.wav 内容不含可匹配「贾维斯」发音（离线 KWS 直喂 peak=0.744 hits=[]，非设备/传播问题）；② 改用产品链路 CV3 合成标准唤醒音频（`data/voice/t4-wake-short.wav`）真机即命中；③ 长指令 12s CV3 版真机零命中 → 归因「贾维斯」后无静音确认窗，重构夹具为「短音频前 1.6s 唤醒词 + 0.8s 静音 + Melo 指令正文」（`t4-wake-long.wav` 9.39s）后 3/4 命中（1 次偶发未命中 = #133 score=2.0 已知现象）。**T4 3+3（输出 idx4 POISON，物理耦合布置）**：短 ×3 = 18:39:41/18:43:19/18:45:53，首字 +4s、complete +7s、degraded=False；长 ×3 = 19:00:38/19:03:58/19:06:06，首字 +4s、complete +10s、degraded=False。**L26 日志锁回归**：日志 3209 行唯一损坏行 #2453（16:18:16）为修复前历史遗留，修复后 756 行新增零损坏。daemon 工作树哈希 `3AFEAA9537B0DD4D03CE9C7AE54A3B69FAAC7D456AA209B08CA249D78BA67D19`（含 `_LOG_LOCK`）；未改任何 KWS/ASR/VAD/TTS 参数值。证据：`docs/reports/evidence/pseudo-streaming-20261030/a4-kws-rootcause.md`。**待 Owner 打冻结 tag。** |
| 2026-10-30 | **TTS 音色换回 sherpa MeloTTS 44100Hz 女声（与 KWS 提示音同源）；完整链路三段预热（ASR/Agent 8756/TTS）** | Owner 真机反馈（19:40/19:41 两轮）：「KWS 提示音是以前的女声、TTS 是 CV3 克隆声，不一致；贾维斯克隆音怪异，建议换回去」。① `config/voice-profile.json` voice.engine `cv3`→`sherpa`（换回与 wake-prompt.wav 同源的 MeloTTS 44100Hz 女声）；`voice_profile.py` 引擎白名单扩为 {cv3,edge,sherpa,piper}；`tts.py` 增加显式本地引擎直达（sherpa/piper/edge 短路，cv3 保持冻结链）。② `voice-listen-daemon.py` warmup() 扩为完整链路三段预热：ASR（2.4s）+ Agent 8756 health+ask（31.9s，首 token 加载）+ TTS 按 engine 预热（累计 37.8s），监听 20:01:43 恢复。**agent_server 端口=8756（agent_client.py L16）**。验证：sherpa 直达合成 ok=True rate=44100 engine=sherpa-melo-tts。本项不属 KWS 参数基线，登记为 TTS 音色/预热变更；0005 CV3 冻结降级为可用非默认，详见 `stage-cv3-jarvis-voice-20261030.md` 后续变更节。 |
| 2026-10-30 | **输出设备解析修复：MME idx4 → WASAPI idx24（POISON 44100Hz），消除播放期采集并发欠载** | Owner 真机反馈「天气回复后半段断断续续」（20:27 回合 reply-349.wav 4.45s 44100Hz）。wav 波形健康无丢帧（50ms 块能量连续、10ms 全零仅 1.08-1.11/1.81-1.82/2.74-2.76s 且与 Melo 旧回复 reply-40/42/77/85 特征一致）→ 根因定位播放层：`resolve_out_device()` 按设备枚举顺序名字匹配命中 **MME idx4**（POISON 44100），播放线程（sd.play 阻塞 + sd.wait）与 KWS 采集线程（MME idx1 输入流）**同 hostapi 并发**，采集满负荷时 MME 输出缓冲欠载 → 长回复后半段断续（短提示音不显现）。修复：`resolve_out_device` 优先 **WASAPI 输出**（idx24 POISON 44100Hz，与 MME 输入流不同驱动栈解耦），回退链 = WASAPI POISON → 任意 hostapi POISON → 系统默认输出。**基线 PLAY_DEVICE=26 已漂移勘误**：当前 idx=26 为 WASAPI "扬声器 (Steam Streaming Microphone)" 48000Hz，WASAPI 下 POISON 耳机实为 **idx=24（44100Hz）**；daemon 新实例 PID 27164 预热完成、监听 20:35:00 恢复。**真机回归重点：长回复（天气等）全段连贯无断续，且播放期间唤醒不退化。** |
| 2026-10-30 | **播放/采集互斥收口：播放期暂停 KWS 采集（_PLAYING 事件）+ POISON 端点音量恢复 100%** | 第二轮真机复测（20:38-39）：唤醒一遍命中✅，但问时间长回复"前半段正常→声音越来越小→杂音→无声"。取证：reply-350.wav（44100/5.24s）波形健康无丢帧（50ms 能量连续、RMS 前 4912/中 4021/后 3342 正常尾音）→ 播放层问题；**POISON 输出端点音量实测 0.315（31.5%）**，L27 恢复 100% 后再次被拉低（"越来越小"最直接解释）；播放期间（20:38:53-59）KWS 采集流仍满负荷并发（20:38:54 重开），WASAPI idx24 解耦后 CPU/总线竞争未根除 → 长回复后半段欠载。修复：① probe-endpoint-volume4 恢复 POISON 端点 vol=1.0 unmuted；② daemon 播放加 **_PLAYING 互斥**（`_play_safe` 置位/finally 清除，`wait_wakeup` 检测到播放中 sleep(0.05) 跳过采集 read）→ **播放期采集零并发**。daemon 第 6 次重启（PID 2464，20:45:15 监听恢复，warmup 44.9s）。代价：播放期（≤6s）不可唤醒，播完即恢复。**真机回归：长回复（时间/天气）全段连贯无衰减无杂音。** |
| 2026-10-30 | **意图路由收窄（interaction.py，不属 KWS 参数但关联"答非所问"真机反馈）：天气直达前移 1.4 + 征询/确认仅待确认态拦截 + 纯征询/确认短句非待确认态静默 + ASR 近音纠错映射** | Owner 三连反馈「KWS 触发不灵敏 / ASR 解析不清晰 / 回答内容不精准」。根因链（22:14 轮完整取证）：ASR final 正确（"给我看一下明天上海的天气怎么样。"）却被 `_CONSULT_INTENT`（含"怎么样"）在天气直达之前拦截 → 误触发 L7 队列征询话术，且把 21:07 轮遗留 last_summary"水量天听"（ASR 近音误识，intermediate"水平听听清"→final"水量天听"）套进话术引用 → 观感=回答不精准。修复：① 天气直达整体前移至 handle() 1.4（调整指令后、子智能体/征询/确认前）；② `_CONFIRM_INTENT`/`_CONSULT_INTENT` 拦截加 `and self.phase == _PENDING_CONFIRM`；③ 新增 2b——非待确认态命中征询/确认且不含查询动作词（`_QUERY_ACTION_RE`）的纯短句提前静默（防漏 14B 兜底自由发挥）；④ `_normalize_utterance` 近音映射（水量天听/水平听听清/水平听→天气、明天上海的这→明天上海的天气）。验证：探针 5 例全绿 + pytest 28 passed（test_consult_without_result_stays_idle 恢复绿）。daemon 第 7 次重启（22:37:34 监听恢复，warmup asr 4.2s/agent 11.0s/tts 18.5s）。**真机回归重点：说"明天上海的天气怎么样"直接答天气（不再征询）；无上轮结果时"你觉得怎么样"静默。** 注意：KWS 参数值未改（threshold=0.08/score=2.0/6 变体冻结中）。 |
| 2026-11-01 | **自定义唤醒词 星期五 → 幂幂（Owner 指令）；本地 TTS 主音色 sherpa → CV3 杨幂（Owner 指令，反转 10-30 否决）** | Owner 最新指令：① 唤醒词改为"幂幂"（杨幂的幂，两字，走 0014 用户入口链：`save_user_override(wakeword.custom="幂幂")` → 原子替换 keywords.txt → daemon 同 PID 热重载，14:19:19 两次 `KWS keywords 热重载成功 pid=27820`）；词表现为 6 贾维斯变体 + `m ì m ì @幂幂` + ULTIMA，`kws_reconfig.py --list` 实证 8 行。② 本地 TTS 主音色切 CV3：`voice-profile.json` voice.engine `sherpa`→`cv3`、ref_audio → `data/voice/yangmi-ref/yangmi_cv3_full_s6_v54.wav`（CV3 训练最新产物 4.02s/24k/单声道）、prompt_text = ASR 转写「你好，我是你的语音助手，今天有什么可以帮你的吗。<\|endofprompt\|>」（faster-whisper medium 转写，置信 1.0，与 0008 测试语一致）；tts.py cv3 冻结链 zero-shot 合成验证 ok（daemon 常驻链 cuda 24k 2.64s，`data/voice/tts-cv3-yangmi-probe.wav`）。**KWS 参数值未改（threshold=0.08/score=2.0/6 变体冻结中）；TTS 音色变更另登记 voice-profile 变更记录。真机验收重点：说"幂幂"一遍即唤醒，杨幂音色回复自然。** |
