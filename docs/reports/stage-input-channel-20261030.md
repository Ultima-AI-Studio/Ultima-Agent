# UltimaAgent 语音输入通道升级阶段报告（2026-10-30）

- 工单：`wo-ultimaagent-20261030-0004`
- 执行端：Codex coding executor
- 专用解释器：`tools/venv-asr/Scripts/python.exe`（Python 3.13.16）
- 北极星：Jarvis；任意输入设备尽量零配置可用；语音仅在本机处理
- 执行状态：T0→T4 全绿；待主脑复核与冻结（Owner gate）

## Gate T0 · 输入设备自动探测

- [x] T0-C1 `enumerate_inputs()` 枚举输入端点并过滤“主声音捕获/声音映射器”等跟随系统端点。
- [x] T0-C2 静音探测返回 `ok=False`；异常设备 fail-closed，不使调用方崩溃。
- [x] T0-C3 有声探测按 `peak>0.01 && rms>0.002` 返回 `ok=True`，记录 `voiced_sec`。
- [x] T0-C4 L2 `device_index` 非空时跳过枚举和探测，进程内缓存来源 `l2`。
- [x] T0-C5 全静音返回 `None`；单设备最长 2 秒、总探测 15 秒（真机全静音路径 12.802 秒）。

真机结果：动态枚举到 USBAudio2.0 四端点（MME 44.1k/1ch、DirectSound 44.1k/1ch、WASAPI 48k/2ch、WDM-KS 48k/1ch）；其中前三个可打开，WDM-KS 返回 PortAudio `-9996` 并 fail-closed。专项测试 `7 passed`。

证据：

- `docs/reports/evidence/input-channel/t0-red.txt`
- `docs/reports/evidence/input-channel/t0-unit-tests.txt`
- `docs/reports/evidence/input-channel/t0-machine-probe.txt`
- `docs/reports/evidence/input-channel/t0-auto-select.txt`

## Gate T1 · 48k WASAPI 采集路径与共享降采样

- [x] T1-C1 动态选择 WASAPI 48k/2ch 端点，真机采集 3.0 秒并混为 1ch WAV；`peak=0.019714`、`rms=0.002033`，非静音。
- [x] T1-C2 `resample_to_16k()` 为唯一 sinc 实现；44.1k 输出与冻结旧实现逐值一致，48k 走精确 3:1 且长度正确。
- [x] T1-C3 双声道逐帧平均为单声道；`AudioCapture` 单测验证 48k/2ch 打开参数与混音输出。
- [x] T1-C4 MME 回切真机打开成功：44.1k/1ch、8820 帧→3200 帧、无 overflow；未改块时长、增益、噪声门或门控基线。

专项回归：`13 passed`；源码扫描确认窗口 sinc 公式仅存在于 `src/brain/voice/_resample.py`。

证据：

- `docs/reports/evidence/input-channel/t1-red.txt`
- `docs/reports/evidence/input-channel/t1-capture-red.txt`
- `docs/reports/evidence/input-channel/t1-capture-green.txt`
- `docs/reports/evidence/input-channel/t1-unit-tests.txt`
- `docs/reports/evidence/input-channel/t1-wasapi48k-capture.txt`
- `docs/reports/evidence/input-channel/t1-wasapi48k-3s.wav`
- `docs/reports/evidence/input-channel/t1-mme44k-regression.txt`

## Gate T2 · 44.1k vs 48k 离线 A/B

- [x] T2-C1 固定随机种子 20261030；8 正/8 负真实 WAV 路径存在且不重叠；KWS 固定 threshold=0.08、score=2.0、6 变体。
- [x] T2-C2 输出逐样本两路 hit/miss：正样本 44.1k=7/8、模拟 48k=7/8；负样本两路均 0/8，结论 PASS。
- [x] T2-C3 结论已追加到 `docs/specs/kws-wakeup-params-baseline.md` 第七节（2026-10-30 新条目）。

样本标签裁决：历史负集中的 `listen-1793270105.wav`（旧 ASR“乔一斯”）和 `listen-1793270820.wav`（新鲜 ASR“小维思，今天天气怎么样”）存在唤醒词标签污染；本次不把 0105 当负样本，0820 作为弱正样本，并从同一既有 30 样本池补入两条本地 ASR 明确无唤醒词的负样本。未生成或伪造音频。

证据：

- `data/logs/kws-44k-vs-48k-ab-20261030.py`
- `data/logs/kws-44k-vs-48k-ab-20261030.txt`
- `docs/reports/evidence/input-channel/t2-kws-44k-vs-48k-ab.txt`
- `docs/reports/evidence/input-channel/t2-unit-tests.txt`
- `docs/reports/evidence/input-channel/t2-all-positive-scan.txt`
- `docs/reports/evidence/input-channel/t2-all-asr-wake-labels.txt`
- `docs/reports/evidence/input-channel/t2-negative-asr-labels.txt`

## Gate T3 · daemon / kws_listener 自动探测接线

- [x] T3-C1 真机仅重启匹配的 voice daemon：启动探测选中 WASAPI `idx=30`、48k/2ch，日志含 `来源: auto`；随后 KWS 流成功打开，强信号进入采集链路。
- [x] T3-C2 L2 `device_index=30` 实测跳过枚举/探测（枚举被设为失败断言仍成功），日志含 `来源: l2`。
- [x] T3-C3 mock 全静音（空枚举）实测回退内置 `idx=1`、MME 44.1k，日志含 `来源: fallback` 且正常返回描述符。

daemon 与 `kws_listener` 均在启动时只解析一次输入，后续采集复用同一描述符；48k 双声道统一混为单声道并走共享 48k→16k sinc。聚焦测试 `18 passed`。重启前后 `agent_server`（39892/29260）与 watchdog（11000/11896）PID、创建时间均未变化；仅停止旧 voice daemon 16636/36388 并启动 22844/27528。

证据：

- `docs/reports/evidence/input-channel/t3-resolve-red.txt`
- `docs/reports/evidence/input-channel/t3-resolve-green.txt`
- `docs/reports/evidence/input-channel/t3-focused-tests.txt`
- `docs/reports/evidence/input-channel/t3-daemon-startup.txt`
- `docs/reports/evidence/input-channel/t3-l2-skip.txt`
- `docs/reports/evidence/input-channel/t3-l2-profile-fixture.json`
- `docs/reports/evidence/input-channel/t3-fallback.txt`
- `docs/reports/evidence/input-channel/t3-processes-before.txt`
- `docs/reports/evidence/input-channel/t3-processes-after.txt`

## Gate T4 · 总验收

- [x] T4-C1 专用解释器最终全量 `pytest src -q --disable-warnings`：`749 passed, 36 warnings, 120 subtests passed`，耗时 120.03 秒；相对修复后新鲜基线 731 tests，新增 18 tests，零新增失败。
- [x] T4-C2 真机 daemon 启动自动选中 48k/2ch WASAPI；本地 WAV 注入生产 48k→16k 共享路径后 KWS 命中“贾维斯”，本地 ASR 输出“贾维斯查一下今天的天气。”，结论 PASS。
- [x] T4-C3 工单第 3 节模板、阶段报告、证据目录与本报告 8 字段回执均已回填。

证据：

- `docs/reports/evidence/input-channel/t4-full-pytest-src.txt`
- `docs/reports/evidence/input-channel/t4-full-pytest-src-preexisting-flake.txt`
- `docs/reports/evidence/input-channel/t4-unrelated-flake-reruns.txt`
- `docs/reports/evidence/input-channel/t4-preexisting-flake-file-metadata.txt`
- `docs/reports/evidence/input-channel/t4-preexisting-flake-hashes.txt`
- `docs/reports/evidence/input-channel/t4-e2e-wav-injection.py`
- `docs/reports/evidence/input-channel/t4-e2e-injected-48k.wav`
- `docs/reports/evidence/input-channel/t4-e2e-output.txt`
- `docs/reports/evidence/input-channel/t4-final-readback.txt`
- `docs/reports/evidence/input-channel/evidence-manifest-sha256.txt`

## 环境与执行裁决

- 基线命令按工单指定改用 `venv-asr` 后发现其缺 pytest 与主工程依赖。已在该 venv 安装 pytest 9.2.0；测试进程通过临时 `PYTHONPATH` 只读复用仓库 OpenJarvis 源码和既有 `venv-openjarvis` site-packages，执行器仍是指定 `venv-asr/Scripts/python.exe`。修复后新鲜基线为 `731 passed, 120 subtests passed`。
- 当前仓库为 dirty `main`，包含大量用户既有改动/未跟踪文件。本工单不清理、不回滚、不覆盖范围外内容；全部校验采用精确路径与定向 diff。
- T1 非静音样本使用仓库既有 `wake-prompt.wav` 作为本地声学刺激，播放增益 2.0；未合成 TTS、未联网，音频未离开本机。
- T4 端到端采用工单明确允许的 WAV 注入：真机自动探测/48k 流打开为实测，KWS→ASR 为既有真实麦克风 WAV 的本地离线注入，不把 WAV 注入表述为现场真人口述。
- 最终收尾曾捕获一次范围外既有竞态：`test_preference_p2.py::test_upsert_idempotent` 因生产代码把两次连续时间戳都截断至毫秒而偶发相等；10 次独立复跑中 4 次复现。相关文件自 2026-10-25 起未改且不属于本工单，故未越界修复；失败输出单独保留，随后未改代码的最终完整套件为 749/749 全绿。

## 8 字段回执

- 工单号：`wo-ultimaagent-20261030-0004`
- 执行端：Codex coding executor（`H:\UltimaAI\UltimaAgent` 当前工作区）
- 完成状态：T0→T4 Gate 全绿；技术执行完成，待主脑复核/冻结，未自行创建 frozen tag。
- 根因结论：旧链路依赖易漂移的固定设备 index，且 16k 原生打开不受当前 USB 麦驱动支持，导致设备拔插或端点变化后采集全零；修复为有界真机探测 + L2/内置回退 + 44.1/48k 原生采集 + 唯一共享 sinc 降采样。
- 产出路径：`src/brain/voice/input_probe.py`、`src/brain/voice/_resample.py`、`data/logs/voice-listen-daemon.py`、`src/brain/voice/kws_listener.py`、`data/logs/kws-44k-vs-48k-ab-20261030.py`、本报告及 `docs/reports/evidence/input-channel/`。
- 验收证据：T0 真机端点/时限；T1 48k 非静音 WAV 与 MME 回切；T2 8 正+8 负 A/B PASS；T3 auto/l2/fallback 与安全重启；T4 `749 passed` 和 KWS→ASR PASS，详见各 Gate 证据清单。
- 越界声明：无。未动范围清单：W6 UI 设备选择页、16k 原生采集改造、KWS threshold/score 基线数值、增益/噪声门/门控基线、TTS 产品通道、第三方音频库、云端语音主链路；未停止/重启 agent_server 或 watchdog。
- 环境声明：设备枚举、探测、48k/2ch 非静音采集、MME 回切及 daemon 48k 打开为本机真机实测；KWS→ASR 总闭环为本机既有真实录音 WAV 离线注入（非现场真人口述）；云端未参与。

## 越界声明（最终）

无。未动 W6 UI 设备选择页、16k 原生采集改造、KWS threshold/score 基线数值、增益/噪声门/门控基线、TTS 产品通道、第三方音频库、云端语音主链路；未停止 agent_server/watchdog。T3 仅按验收要求重启了精确匹配的 voice daemon，并保留重启前后进程证据。
