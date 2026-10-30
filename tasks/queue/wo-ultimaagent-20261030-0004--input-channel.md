# Codex 工单 · UltimaAgent｜功能｜语音输入通道升级（设备自动探测 + 48k WASAPI A/B）

> 版本：v1.1 ｜ 状态：已冻结（2026-10-30）｜ 适用工具：Codex（`codex exec`，`-m gpt-5.6-sol`）
> 用法：按 T0→T4 顺序逐条执行，Gate 全绿才过，再进下一条。
> 范围依据：`H:\UltimaAI\INDEX.md` + `H:\UltimaAI\_shared\paradigms\UltimaAI-任务工作流范式.md` + `docs/INDEX.md`
> 调研依据：`docs/specs/kws-wakeup-params-baseline.md`（设备/降采样冻结基线）+ 10-30 真机音频端点探测（`data/logs/probe_audio_endpoints_20261030.py`：USBAudio2.0 有 MME 44.1k/1ch、WASAPI 48k/2ch、WDM-KS 48k/1ch 四端点）
> 北极星：**贾维斯**（语音链路向"任意输入设备零配置可用"靠拢；隐私红线：语音不出本机）
> 登记：2026-10-30 ｜ 原单 ID：wo-ultimaagent-20261030-0004 ｜ 类型：功能

---

## 0. 范围冻结

**本阶段只做（语音输入通道升级）**：

1. **设备自动探测**：新增 `src/brain/voice/input_probe.py`——启动时枚举全部输入端点（sounddevice），逐个实测拾音（短录音 + 电平/能量判定，如 RMS>阈值或说话段能量），自动选中"真能收到声音"的设备；探测结果缓存供 daemon/kws_listener 使用；探测失败或全静音 → 回退 `voice-profile.json` 的 `input.device_index`（L2）或内置默认（L1）；
2. **48k WASAPI 通道 A/B**：daemon 从 MME 44.1k 单声道（index 1）增加 WASAPI 48k 双声道端点（本机 index 30）采集路径，48k→16k 走整数 3:1 降采样（保留 sinc 多相滤波精度，但目标比改为 48k→16k），与现有 44.1k→16k sinc 路径做离线 A/B：
   - 正样本：`data/voice/mic-regress/` 已有真实唤醒 wav（44.1k 采集）经 44.1k→16k 与 48k→16k（先上采样/重采样模拟）两路对比 KWS 命中；
   - 判据：48k 通道在正样本命中率 ≥ 44.1k 且零回归（负样本不新增误唤醒）；
3. **输入设备层接入 voice-profile**：`input.mode=auto` 走探测结果；`device_index` 非空走 L2 手动指定（跳过探测）；`prefer_wasapi48k=true` 且设备支持时优先 48k 通道（配合工单 0003 voice-profile，本工单只做探测与通道能力，不依赖 0003 完成即可独立验收）；
4. 配套单元测试 + 全量回归通过。

**本阶段不做**：不做 UI 设备选择页（W6 后续接）；不改 KWS 参数基线数值（阈值/score 仍归 `kws-wakeup-params-baseline.md`）；不做 16k 原生采集改造（设备驱动能力受限时仍走 44.1k/48k→16k）；不引入第三方音频库（仅 sounddevice 既有依赖）；不处理 TTS 通道。

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `src/brain/voice/input_probe.py`（新增） | 设备枚举+实测拾音单测全绿；全静音回退逻辑正确 |
| T1 | `data/logs/voice-listen-daemon.py`（修改：48k WASAPI 采集路径） | 48k 采集实测出声（录音 wav 非静音、声道/采样率正确） |
| T2 | 离线 A/B：44.1k vs 48k 降采样唤醒命中对比 | A/B 报告：48k ≥ 44.1k 命中率且零回归 |
| T3 | daemon 接入自动探测（启动选设备） | 启动日志确认探测选中设备；L2 device_index 优先 |
| T4 | 总验收 | 端到端实测 + 全量回归 + 证据落盘 |

---

## 2. 任务明细（每条 T 严格三段式）

### T0 · 输入设备自动探测模块

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\voice\input_probe.py`（新增）
- `H:\UltimaAI\UltimaAgent\src\brain\tests\test_input_probe.py`（新增测试）

**写什么**：
1. `enumerate_inputs() -> list[dict]`：sounddevice 枚举输入端点（hostapi/name/index/max_input_channels/default_samplerate），排除"主声音捕获""声音映射器"等跟随系统类（历史实证不可靠，基线文档教训）；
2. `probe_device(index, seconds=2.0) -> dict`：短录音实测，返回 `{ok, peak, rms, voiced_sec}`；拾音判据：`peak > 0.01` 且 `rms > 0.002`（参考基线文档门控口径，不篡改基线数值本身）；
3. `auto_select(profile_input) -> int`：优先 `profile.device_index`（L2 非空直接返回）；否则枚举→逐个 probe→选第一个 `ok` 的设备；全失败返回 `None`（调用方回退内置默认）；
4. 探测耗时限制：每个设备 ≤2s，总探测 ≤15s；探测过程日志留痕（选中/跳过/失败原因）。

**验收（Gate T0）**：
- [x] 单测 ≥5：枚举过滤系统默认类；probe 静音→ok=False；probe 有音→ok=True；L2 优先；全失败→None；
- [x] 真机跑 `enumerate_inputs()` + `probe_device` 输出与 `probe_audio_endpoints_20261030.py` 一致（本机 USBAudio2.0 四个端点全部枚举到）；
- [x] `python -m pytest src/brain/tests/test_input_probe.py -q --disable-warnings` 全绿（Agent 专用解释器，见 T4）。

**禁止**：不硬编码设备 index（探测是唯一入口，L2 除外）；不引入第三方库；不修改基线门控数值常量定义处（探测判据另立，注释引用基线）。

---

### T1 · daemon 增加 48k WASAPI 采集路径

**文件**：
- `H:\UltimaAI\UltimaAgent\data\logs\voice-listen-daemon.py`（修改：采集层抽象，MME 44.1k / WASAPI 48k 双路径）
- `H:\UltimaAI\UltimaAgent\src\brain\voice\_resample.py`（如已存在则复用；否则抽取 resample 为共享模块，daemon 与 asr.py 同源——**禁止重复实现两套 sinc**）

**写什么**：
1. daemon 采集层抽象：`AudioCapture` 类，`open(device_index, hostapi, samplerate)` 按端点能力选通道——支持 48k 时用 48k（WASAPI index 30），否则 44.1k（MME index 1）；
2. 48k→16k 整数 3:1 降采样：复用现有 sinc 多相滤波（`_resample_16k` 改造为通用 `resample_to_16k(f32, sr_in)`，up/down 按输入采样率计算；48k 走 3:1，44.1k 走 441:160，冻结参数与现有一致）；
3. 声道处理：WASAPI 2ch 输入取单声道（混音平均或取首声道，注释说明选择）；48k 双声道录出的 wav 仍以 1ch 16k 喂 KWS/ASR（链路统一出口不变）；
4. 采集参数（块大小/静音判定/增益）与现有 44.1k 路径一致，仅采样率/端点不同——**不得顺带改增益或噪声门基线**。

**验收（Gate T1）**：
- [x] 真机实测：daemon 以 WASAPI 48k 端点采集 3s 录音，wav 非静音（peak/RMS 打印），采样率标注正确；
- [x] 单测 ≥3：resample_to_16k 44.1k 输入与现有输出一致（回归）；48k→16k 长度正确；2ch→1ch 混音正确；
- [x] 既有 44.1k MME 路径零回归（daemon 可回切 MME 采集）。

**禁止**：不新增第二套 sinc 实现（复用/抽取共享）；不改增益/噪声门/门控基线；不破坏 44.1k 路径。

---

### T2 · 44.1k vs 48k 降采样唤醒命中离线 A/B

**文件**：
- `H:\UltimaAI\UltimaAgent\data\logs\kws-44k-vs-48k-ab-20261030.py`（新增）
- `H:\UltimaAI\UltimaAgent\data\logs\kws-44k-vs-48k-ab-20261030.txt`（输出）

**写什么**：
1. 取 `data/voice/mic-regress/` 已有真实唤醒 wav（44.1k 采集）作为正样本集（≥8 个，含强弱信号）；负样本（环境音/无关说话，≥8 个）复用既有 A/B 负样本集（`probe_kws_variant_ab2.py` 同源）；
2. 每样本两路处理：①44.1k→16k sinc（现状基线）；②先 44.1k→48k（3 倍上采样，保持 sinc 精度）再 48k→16k（3:1）——模拟 48k 原生通道降采样质量；
3. KWS 命中判定与 `probe_kws_variant_ab2.py` 完全一致（threshold=0.08 固定、score=2.0、6 变体 keywords.txt）；
4. 输出对比表：每样本两路 hit/miss + 总命中率；结论：48k 路命中率 ≥ 44.1k 且负样本零误唤醒 → PASS；否则保持 44.1k 为默认并登记。

**验收（Gate T2）**：
- [x] A/B 脚本可复现（固定随机种子，路径全部存在）；
- [x] 输出 txt 含完整样本清单 + 两路命中表 + 结论行；
- [x] 结论写回基线文档第七节（新登记一条，日期 2026-10-30）。

**禁止**：不删除/覆盖既有 A/B 脚本与样本；不修改 KWS 参数（A/B 只在降采样通道维度对比）；样本集不新增伪造数据。

---

### T3 · daemon 启动自动探测接线

**文件**：
- `H:\UltimaAI\UltimaAgent\data\logs\voice-listen-daemon.py`（修改：启动时调用 input_probe）
- `H:\UltimaAI\UltimaAgent\src\brain\voice\kws_listener.py`（修改：同逻辑对齐）
- 单测并入 T0 测试文件

**写什么**：
1. daemon 启动流程：`auto_select(profile_input)` → 得到 device_index + hostapi + samplerate → 打开采集；探测失败回退内置默认（当前 index 1）；
2. 启动日志明确打印：`探测选中: idx=N hostapi=X sr=Y（来源: auto/l2/fallback）`；
3. L2 手动指定（profile.device_index 非空）→ 跳过探测直接使用，日志标注 `来源: l2`；
4. 探测与采集异常时进程不退出（记 error 续跑，沿用现有异常续跑结构）。

**验收（Gate T3）**：
- [x] 真机重启 daemon：启动日志出现探测选中行，采集出声正常；
- [x] 模拟 L2 指定（profile 临时写入 device_index）→ 跳过探测直接使用；
- [x] 探测失败回退（mock 全静音）→ 用内置默认启动不崩溃。

**禁止**：不硬编码探测结果缓存到磁盘（每启动重探测，探测开销 ≤15s 可接受）；不改基线参数。

---

### T4 · 总验收

**文件**：本工单（更新状态）+ `docs/reports/` 阶段报告 + 证据目录

**写什么**：
1. 全量单测回归：`H:\UltimaAI\UltimaAgent\tools\venv-asr\Scripts\python.exe -m pytest src -q --disable-warnings`（**ASR 专用解释器，禁止用系统 Python**）→ 全绿 + 无新增失败；
2. 端到端实测：daemon 自动探测启动 → 48k 通道采集 → KWS 唤醒 → ASR 识别完整闭环（WAV 注入或真机）；日志留痕设备来源；
3. 阶段报告 `docs/reports/stage-input-channel-20261030.md`：Gate 逐条核对（T0-C1~C5/T1-C1~C4/T2-C1~C3/T3-C1~C3/T4 全量），证据路径、越界声明（未动：UI 设备页/KWS 参数基线/TTS/第三方音频库）；
4. 证据落盘 `docs/reports/evidence/input-channel/`：探测输出、48k 录音样本、A/B 对比表、回归全量输出；
5. 回执 8 字段按 Codex 范式 §5 输出。

**验收（Gate T4）**：总验收清单全绿；阶段报告存在且逐项勾选；回执 8 字段齐全；越界声明如实。

---

## 3. 给编码代理的任务粘贴模板

```
T0 输入设备自动探测：已完成，Gate T0 全绿（9 项专项测试；真机枚举 USBAudio2.0 各 host API 端点；全静音路径 12.802s；L2 优先与回退通过）
T1 48k WASAPI 采集路径：已完成，Gate T1 全绿（真机 48k/2ch→1ch 录音 peak=0.019714、rms=0.002033；共享 sinc；MME 44.1k 回切通过）
T2 44.1k vs 48k 离线 A/B：已完成，Gate T2 全绿（8 正/8 负：两路正样本均 7/8，负样本均 0/8；结论已登记基线第七节）
T3 daemon 自动探测接线：已完成，Gate T3 全绿（真机启动 auto 选中 idx=30/WASAPI/48k；L2 跳过探测；全静音 fallback idx=1；无关后台进程未变化）
T4 总验收：已完成，专用解释器全量 749 passed + 120 subtests passed；48k WAV 注入 KWS 命中“贾维斯”且本地 ASR 输出“贾维斯查一下今天的天气。”；证据已落盘
```

---

## 4. 验收要点

- [x] 范围冻结内逐项完成（无越界：未动 UI 设备页/KWS 参数基线/TTS/第三方音频库）
- [x] 每 T 验收清单全绿 + 自证完整
- [x] 关联文档同步（A/B 结论登记 kws-wakeup-params-baseline.md 第七节；resample 共享模块注释同步 asr.py）
- [x] 阶段报告产出 → 主脑复核 → 冻结 tag（`wo-ultimaagent-20261030-0004-frozen-20261030`）

主脑复核通过：T0-T4 全绿（749 passed + 120 subtests）；A/B 判据满足（44.1k=7/8、48k=7/8，负样本 0/8）；越界声明无；阶段报告/证据 60 项 manifest/基线第七节登记均已核验。冻结 commit `13c697e` + tag `wo-ultimaagent-20261030-0004-frozen-20261030`。
