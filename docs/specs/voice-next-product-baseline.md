# UltimaAgent 语音产品基线（E3 `src/voice-next/`）

> 工单 0035 v2.0 建立

**本文件只约束 `src/voice-next/`（E3）**，也是 E3 参数的唯一权威说明。

**参数唯一载体是 `config/voice-next/live.json`**：`keyword` / `threshold` / `keywords_score` / `num_trailing_blanks` / `input` / `output` / `command_*` / `worker_timeout_seconds` / `input_gain` / `dsp` / `prompts` 全部落在该文件。代码内不得再写死这些值；改参只改该文件并同步本表。

**旧入口 E1/E2 已整体冻结归档到 `archive/voice-legacy-E1E2-20261111/`**：`src/brain/voice/kws_listener.py`、`data/logs/voice-listen-daemon.py`、`models/sherpa/kws/keywords.txt`、`scripts/kws_reconfig.py` 及历史参数基线 `docs/specs/kws-wakeup-params-baseline.md` 均在该目录内，**不约束本文件，也不得被现行代码引用**。

## E3 产品参数与行为

| 编号 | 项目 | 取值 | 依据 |
|---|---|---|---|
| （a） | 唤醒词 | `你好问问` | `src/voice-next/README.md:3` 说明实际监听固定使用该词。 |
| （b） | `keywords_threshold` | `0.25` | `src/voice-next/README.md:32` 记录新 KWS 阈值为官方默认工作点。 |
| （c） | `keywords_score` | `1` | E3 当前新链路取值；与 E1/E2 历史实现基线互不约束。 |
| （d） | `num_trailing_blanks` | `1` | E3 当前新链路取值；与 E1/E2 历史实现基线互不约束。 |
| （e） | 模型 | `models\voice-next` 独立副本 / chunk-16 | `src/voice-next/README.md:3,44` 记录 chunk16 与独立副本。 |
| （f） | 输入端点 | WASAPI 名字解析（`麦克风 (USBAudio2.0)`） | `src/voice-next/README.md:24` 原文说明按名字和 API 解析，不依赖旧设备索引。 |
| （g） | KWS 增益 | `dsp.auto_gain_control=true` 时由 APM AGC 承担电平，**不叠加**软件增益；AGC 关闭时回退 `input_gain=10` | `src/voice-next/README.md:32`；2026-11-11 改判，见变更记录 |
| （h） | 指令采集 | 上限 15s / 结束静音 0.8s / 等开口 5s | `src/voice-next/README.md:33` 的回合参数。 |
| （i） | 有效语音门控 | WebRTC VAD ≥5×20ms，无 peak/rms 门 | `src/voice-next/README.md:32-33`：无二次电平门控，VAD 以 20ms 判帧。 |
| （j） | 提示音静置 | 无 `BEEP_SETTLE_SEC`，仅播放后 0.15s sleep | E3 当前实现行为；不得外推为 E1/E2 取值。 |

## 三项待定

- `keywords_score` 2.0→1：**待定，本单不定性**；缺设计意图说明或实测召回对比。
- `num_trailing_blanks` 8→1：**待定，本单不定性**；缺说明是否随官方默认模型参数套用，或词尾延迟实测。
- `BEEP_SETTLE_SEC` 移除：**待定，本单不定性**；缺实测 0.15s 是否足以避免提示音残响被录入 KWS。

## CV3 音色

- 目标：接入 E1 那套 CV3 音色。
- 当前：SAPI（临时）；`src/voice-next/README.md:5` 原文为“新入口临时使用Windows本地SAPI语音：原CV3冷启动联调等待数分钟，因此本轮不启动CV3，原音色配置和源码保留。”
- 规格：见 `docs/specs/voice-next-cv3-tts.md`。本单只出规格不出实现；本单之后 E3 仍未具备 CV3 音色。

## 未验收声明

`src/voice-next/README.md:46` 原文：`合成样本是冒烟证据，不是远场稳定性证明`。

`src/voice-next/README.md:32` 原文：`稳定性仍需真人验收`。

因此，本文件建立的是产品基线与后续验收依据，不宣称 E3 已完成真人稳定性验收。

## 变更记录

| 日期 | 变更 |
|---|---|
| 2026-11-10 | 据 0035 v2.0 改判建立。 |
| 2026-11-11 | **（g）改判 + 新增输入侧 DSP**：接入 `pywebrtc-audio` 0.2.0（WebRTC APM），采集链路前接 10ms 帧化 NS+AGC+AEC，配置落在 `config/voice-next/live.json` 的 `dsp` 段。**AGC 开启时不再叠加 `input_gain=10`**（AGC 上限 15dB 与原 10 倍放大叠加必削波），`input_gain=10` 降为「AGC 关闭」的回退值；AEC 开启时播放期不再暂停采集，`play()` 回灌 16k far 参考，播放期数据只过 DSP 不进 KWS/VAD。新增 `src/voice-next/apm_dsp.py`（`PlaybackReference` + `ApmChain`）与 `test_apm_dsp.py`（10 项）。离线受控验证：纯净回声消除 99.8%、回声+噪声 89.2%；播放声与真人声共存时 AEC 后播放声消失且用户原话可识别。**真机唤醒率与 `stream_delay_ms` 标定仍未验证。** |
| 2026-11-11 | **新增（k）TTS 后端**：`tts_backend ∈ {cv3, windows-sapi-fallback}`，由 `src/voice-next/turn_worker.py` 持有的常驻 daemon（名 `tts-voice-next`）提供，`voice_loop.tts_synthesize` 改指向 `synthesize_reply`（CV3 优先、SAPI 兜底，不再整模块替换成 SAPI）。**新增（l）提示音文本权威源**：4 句提示音文案落在 `config/voice-next/live.json` 的 `prompts` 段，`live.py` 缺失即启动失败（fail-closed），worker 预热成功后用克隆音色重写 `data/voice-next/prompts/*.wav`（`os.replace` 原子替换）。`serve(prewarm=)` 为预热开关，**pytest 必须 `prewarm=False`**。真机实测：`tts_warm_seconds=32.8`、提示音 4 项全重写为 24kHz。**目标音色是否即 Owner 期望尚未听辨确认；§6 健康探针与强杀回收未实现（见 `voice-next-cv3-tts.md` §8）。** |
| 2026-11-11 | **新增（m）语音回复句数上限**：`config/voice-profile.json` 的 `style.max_sentences` 由 2 改为 4（真机反馈「回答内容范围太小」）。该值此前只登记在历史报告 `docs/reports/stage-reply-constraint-c-20261101.md`（0003 基线），无当前权威登记，本行补齐。生效链：`voice_profile.filter_reply` 与 `routing.reply_verifier` 均按句截断到该值；`load_profile()` 无缓存，改配置即时生效；`agent_server.py` 的 `REPLY_MAX_SENTENCES` 是模块加载时读一次，**改完必须重启 agent_server**（本轮已重启，pid 4500→24344，看门狗 `watchdog-loopguard.py` 负责 8756 拉起）。合法区间 1..10，越界回退默认。**注意：本参数只放宽回复长度，不改变规则表话题覆盖面。** |
| 2026-11-11 | **（n）已处置 · 回答链路改为本地优先 + 本地模型统一 8B**：`src/brain/interaction.py` 的调用顺序由「云端外脑优先 → 本地 agent」改为「**本地 agent 优先 → 云端兜底**」（`_try_agent_fallback` 先试，仅当本地不可达/返回空时才调 `_try_cloud_fallback`）。同时 `src/brain/orchestration/engine.py` 的 `_model_keys` 由 `("qwen3-8b-uncensored", "qwen2.5:14b", "qwen2.5:7b")` 收为 `("qwen3-8b-uncensored",)`，`select_model()` 对任意复杂度一律返回 8B——**14B 自此不再参与任何模型路由**（仅在注释中保留「14B 已停用」说明）。代码内 25 处「14B」表述同步校正为 8B。验证：`src/brain` + `orchestration` 共 443 passed；`test_connectivity_m6.py::test_ollama_has_brains` 仍依赖会话 PATH 内的 `ollama`，本会话 PATH 被替换时呈假阴性，补 PATH 后通过。 |
| 2026-11-11 | **新增（o）开机预加载**：`src/voice-next/preload.py` + 计划任务 `UltimaAgent-Preload`（AtLogOn + 延迟 60s，pythonw 无窗，工作目录 `H:\UltimaAI\UltimaAgent`）。顺序：等 `127.0.0.1:11434`（240s，Ollama 常晚于登录就绪）→ 等 WASAPI 输入/输出端点按 `config/voice-next/live.json` 的 `name_contains` 与 `hostapi` 含 wasapi 枚举齐全（150s）→ 调 `launch.py --wait 150`（该脚本自身会 `ensure_agent` 起 8756 并 DETACHED 起 `live.py`，后者 `serve(prewarm=True)` 已自带 CV3 预热，故不需要另造预热通路）→ **`_probe_agent` 用一次真实 `/ask` 验证本地 8B 真的能答**（失败则再 launch 一次并重探）。结果写 `data/voice-next/preload.json`、日志 `data/voice-next/preload.log`。实测：ollama 0.0s、端点 0.2s（input 30 / output 24）、launch 0.2s、探针 11.8s、`ok=true`。**探针判据是有无文本回复，不是答案质量**（质量兜底的「这个问题我暂时无法可靠回答。」也记为链路通）。 |
| 2026-11-11 | **新增（p）语音回复长度口径（调研，未改参数）**：见 `docs/reports/stage-reply-brevity-research-20261111.md`。业界主约束是**朗读时长**而非句数：单条 <15 秒、比同内容文本短 60–70%、人脑只持有 8–10 秒口语信息（Bluejay）；640 字符截断、建议 <300（Google）；默认 1 句 / 要细节 2 句（Smallest AI）；一到两次呼吸读完（Alexa）。结论：`max_sentences=4` 按中文估约 20–30 秒，**仍超业界 15 秒线**，但**不可直接砍回 1–2**（会复现「范围太小」）；正确方向是「句数 + 估算秒数」双口径 + 按意图分级 + 去列表/编号/URL 清洗，且 `_try_agent_fallback` 重试提示词仍写「不得超过两句」，需与新口径同步。**本轮只出调研，未改任何参数。** |
| 2026-11-11 | **（q）旧入口物理剥离 + 词源单一化**：E1/E2 六个入口文件、旧换词 CLI（`scripts/kws_reconfig.py` 与其测试）、旧词表与旧参数基线全部 `git mv` 进 `archive/voice-legacy-E1E2-20261111/`（另有两份冻结回归测试随载体搬入，判据未删，见该目录 README）。四处硬编码唤醒词收口到 `live.json`：`kws_backend.py`（删 `keyword!='你好问问'` 断言、`keywords_score`/`num_trailing_blanks` 改读配置）、`live.py`（提示音文案 `{keyword}` 占位展开）、`turn_worker.py`（固定回复改读配置）、`stream_runner.py`（`--keyword` 默认改读配置）。`voice_loop.py` 的默认换词事务改为 fail-closed（原实现指向已归档 CLI 且写死「贾维斯」）。`voice_profile.py` 的 `DEFAULT_WAKE_WORDS` 清空、`DEFAULT_WAKE_ECHO_ROOTS` 改为只取 `live.json` 的 keyword；`config/voice-profile.json` 的 `wakeword.words`/`custom` 同步清空；`interaction.py` 人设自称由「幂幂」改为「问问」。验证：`get_wake_echo_roots()==('你好问问',)`；brain+orchestration 420 passed / 1 failed（`test_ollama_has_brains` 为会话 PATH 假阴性）；`src/voice-next` 43 passed。 |
| 2026-11-11 | **（r）补齐（q）遗留的二源通道（本轮实测暴露）**：`grep` + 运行时探针确认（q）之后仍有三条活通道能产出第二种唤醒词/人设结果，已全部收口。① **词表重建通道**：`voice_profile._keyword_lines()` 原会无条件追加 `_ULTIMA_KEYWORD`（`AH1 L T IH0 M AH0 @ULTIMA`）并写回 `models/sherpa/kws/keywords.txt`；该文件已归档，但目录仍在、`apply_to_daemon()` 的 `mkdir(parents=True)` 会把它重新造出来 —— 现 `_keyword_lines()` 恒返回 `None`、`apply_to_daemon()` 恒返回 `False` 并打错日志，旧路径不再可能生成第二份词表。② **L2 写盘通道**：`_L2_FIELDS` 原含 `"wakeword": {"custom"}`，`save_user_override({"wakeword":…})` 会写进 `config/voice-profile.json` 成为第二源 —— 现移除该项，且带实质值的 wakeword override 直接拒绝（返回 `False`，配置文件逐字节不变）。③ **人设双源**：云端 DeepSeek 分支（`interaction.py::_CLOUD`）自带一句内联人设「你是'问问'…（贾维斯风格）」，与本地分支的 `load_persona()`（读 `libs/base/openjarvis/configs/openjarvis/prompts/personas/jarvis.md`）并行 —— 同一问题走不同分支会出现两种自称；现云端分支改为读同一个 `load_persona()`，内联副本删除。另：`KEYWORDS_PATH` 由归档路径改指唯一源 `config/voice-next/keywords.txt`；`_ULTIMA_KEYWORD` 常量与随之变成死代码的 `_custom_keyword_line` / `_phonemize_with_asr_runtime`（含 `import subprocess`）一并删除。验证：`KEYWORDS_PATH` 指向 `config/voice-next/keywords.txt` 且存在；`apply_to_daemon()` 返回 `False` 且 `models/sherpa/kws/keywords.txt` 未被重建；`save_user_override({"wakeword":…})` 返回 `False` 且配置逐字节不变；`echo_roots==('你好问问',)`、`wakeword=={'words': [], 'custom': None}`；`load_persona()` 首行为 `You are Jarvis — the local AI assistant…` 且不含「贾维斯/幂幂」。**回归**：brain+orchestration **421 passed / 1 failed**（仅 `test_ollama_has_brains` 会话 PATH 假阴性）；`src/voice-next` **43 passed**。`test_save_ignores_non_l2_fields` 原断言「wakeword 不被写入」，因规则从「忽略」升级为「拒绝」，拆为原用例（非 L2 字段不写）+ 新增 `test_save_rejects_wakeword_override`（拒绝且配置不变），判据只增不减。 |
