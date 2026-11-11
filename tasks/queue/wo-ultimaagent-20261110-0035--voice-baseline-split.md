# Codex 工单 · 0035 v2.0 语音入口改判：E3 主线 + CV3 音色

> 版本：v2.0（2026-11-10 改判）｜状态：可开工｜适用工具：Codex
> 用法：按 T0→T6 顺序执行，每 T 的 Gate 全绿再进下一条。
> 范围依据：`tasks/queue/runs/_req-0035c-e3-main-cv3-voice.md`（需求）+ `tasks/queue/runs/wo-ultimaagent-20261110-0035c-e3-main-20261110T141257494Z/stages/decompose.md`（方案）+ `tasks/queue/runs/wo-ultimaagent-20261110-0035d-work-order-20261110T141648847Z/stages/work_order.md`（工单）
> **v2.0 是改判版，取代 v1.1（v1.1 的「A：E1 产品主线 + E3 实验线」已作废）**。改判依据：Owner 原话「E3 的测试我是测过的，好用。但是没有使用我们 E1 训练的声音。」——v1.1 的「E1 是唯一被真机验收过的链路」这一前提被否证。

---

## 0. 范围冻结

**本阶段只做（五个文档动作 + 一处代码）**：
- F1 新建 `docs/specs/voice-entry-authority-decision-20261110.md`（裁决记录，改判版）
- F2 新建 `docs/specs/voice-next-product-baseline.md`（产品基线 = E3 参数 + CV3 音色）
- F3 改 `docs/specs/kws-wakeup-params-baseline.md`（加「历史实现基线」抬头 + `PLAY_DEVICE` 26→24 + 适用范围 + 变更记录 + 待办）
- F4 新建 `docs/specs/voice-next-cv3-tts.md`（CV3 接入规格，**只出规格不出代码**）
- F5 改 `src/brain/voice/kws_listener.py`（**仅第 43 行值与同行注释**）
- F6 改 `docs/INDEX.md`（登记 F1/F2/F4 三份新文档）

**本阶段不做**：
- **不实现 CV3 接入代码**（F4 只出规格；`live.py` 一行不动，`sapi.ps1` 一行不动）
- 除 F5 那一行外，不改任何入口代码（`src/brain/voice/` 其余、`src/voice-next/` 全部、`data/logs/voice-listen-daemon.py` 一行都不动）
- 不改任何 KWS / ASR / VAD / 门控参数值（`keywords_threshold`、`keywords_score`、`num_trailing_blanks`、增益、门控、静音时长一律不动）
- 不让 `src/voice-next/` 任何文件 import torch，不新增 `import torch` 行
- 不把任何采样率写死进代码
- 不删除、不停用、不重命名、不归档任何入口
- 不新建 `docs/baselines/` 或 `docs/decisions/` 目录
- 不重启任何语音进程 / daemon
- 不把三项「待定」（`keywords_score` 2.0→1、`num_trailing_blanks` 8→1、`BEEP_SETTLE_SEC` 移除）写成确定性结论
- 不改 F3 除下列指定位置之外的任何内容；其余冻结值逐字保留
- `git add` 只用显式路径，**禁止 `git add -A`**（入场即有大量既有改动，2026-11-10 实测 `git status --porcelain` 为 **562 行**，其中 `docs/specs/` 下 23 条多为未跟踪文件；不得清理、不得 stash、不得 checkout）

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | — | 开工前指纹已记录，且 status 快照已落到临时文件供 T7 差分比对 |
| T1 | `docs/specs/voice-entry-authority-decision-20261110.md` | 推翻前提原话、两路残缺对照、改判结论、Q3/Q5 拍板、机检四行、边界声明齐备 |
| T2 | `docs/specs/voice-next-product-baseline.md` | 双向不越界声明齐、a–j 十项齐、三项待定标齐、CV3 段落与未验收声明齐 |
| T3 | `docs/specs/kws-wakeup-params-baseline.md` | 抬头改历史实现基线、`PLAY_DEVICE`=24 且带 44100Hz、变更记录与待办已加、其余冻结值零改动 |
| T4 | `docs/specs/voice-next-cv3-tts.md` | 形态/IPC/签名/超时/失败语义/生命周期/验收门槛七项齐，且**零代码块** |
| T5 | `src/brain/voice/kws_listener.py` | 第 43 行为 24、注释同步、`= 26` 命中 0、diff 变更行 ≤2、AST 通过 |
| T6 | `docs/INDEX.md` | 三份新文档各登记一行，diff 仅新增 3 行 |
| T7 | — | 总验收：status 差分确认恰新增 6 个路径，提交后 `show --stat` 恰 6 文件 |

---

## 2. 任务明细

### T0 · 开工前指纹
**文件**：无（只读采集；快照写入 `$env:TEMP`）
**写什么**：
1. 记录 `git -C H:\UltimaAI\UltimaAgent rev-parse HEAD`。
2. **把 status 快照落盘供 T7 差分用**：
   ```powershell
   git -C H:\UltimaAI\UltimaAgent status --porcelain | Set-Content -LiteralPath "$env:TEMP\0035-t0-status.txt" -Encoding utf8
   ```
   同时把内容完整粘贴进回执。**行数以实测为准（2026-11-10 实测 562 行，其中 `docs/specs/` 相关 23 条）；不得假定为任何固定数字，如实记录即可。入场已有大量既有改动，本单不碰、不清理。**
3. 记录 `docs/specs/kws-wakeup-params-baseline.md` 与 `src/brain/voice/kws_listener.py` 的 SHA256 与行数。
4. 记录 `rg -n 'PLAY_DEVICE' src/brain/voice/kws_listener.py` 输出（应命中第 43 行 `= 26`，及 L106/L111 调用点）。

**验收（Gate T0）**：
1. 四项指纹均已粘贴且非空
2. `$env:TEMP\0035-t0-status.txt` 存在（`Test-Path -LiteralPath "$env:TEMP\0035-t0-status.txt"` 返回 True）
3. `kws-wakeup-params-baseline.md` 行数**已实测并记录**：2026-11-10 实测为 **110 行** / 28,617 B / LF 换行 / 末尾有换行符。此处给定的是实测值，**不是要求你凑成某个数**——若你实测另有数值，以你的实测为准并在回执注明；**禁止补空行或删行凑数**
4. `kws_listener.py` 的 `PLAY_DEVICE` 常量行值为 **26**

**禁止**：`git stash`、`git checkout`、`git clean` 任何形式的工作树清理；修改任何文件。

### T1 · 裁决记录（改判版）
**文件**：`docs/specs/voice-entry-authority-decision-20261110.md`（新建）

**写什么**：
1. 标题：「语音入口权威裁决记录 2026-11-10（工单 0035 v2.0 改判版）」
2. **推翻前提**段，逐字引 Owner 原话：`E3 的测试我是测过的，好用。但是没有使用我们 E1 训练的声音。`，并说明它否证了 v1.1 的哪条前提。
3. **两路残缺对照表**（两列三行，至少覆盖：链路 / 音色 / 设备）：
   - E1 `src/brain/voice/kws_listener.py`：链路=旧链路；音色=**CV3（对）**；设备=`PLAY_DEVICE=26` 指向 Steam 虚拟声卡（**播不出去**）
   - E3 `src/voice-next/`：链路=新链路（**Owner 实测好用**）；音色=SAPI 系统语音（**非目标音色**）；设备=名字解析已解耦（对）
4. **改判结论**：产品主线 = E3；产品音色 = E1 的 CV3；目标形态 = E3 链路 + CV3 音色；E1/E2 不删、不停用、不归档，降为历史实现。
5. **Q3 拍板**：CV3 不可用时**降级 SAPI 并上报**——照常出声，但 `data/voice-next/status.json` 的 `tts_backend` 写 `sapi_fallback` 并记日志告警，**禁止静默降级**。
6. **Q5 拍板**：`PLAY_DEVICE` 最小修 `26`→`24`，只改常量值与同行注释，L106/L111 调用点不动；「设备应记端点身份而非整数」登记进 F3 待办。
7. **机检证据**（四行原文逐字）：
   ```
   idx=24  OUT  Windows WASAPI       44100  耳机 (POISON M@LOFREE)
   idx=26  OUT  Windows WASAPI       48000  扬声器 (Steam Streaming Microphone)
   idx=4   OUT  Windows MME          44100  耳机 (POISON M@LOFREE)
   idx=15  OUT  Windows DirectSound  44100  耳机 (POISON M@LOFREE)
   ```
   附机检时间 2026-11-10 与命令说明（`sd.query_devices()` + `query_hostapis()`，解释器 `tools\venv-voice-next`）。
8. **边界声明**：`本单只出规格、未实现 TTS`——CV3 实际接入实现属后续单，本单不宣称 E3 已具备 CV3 音色。

**验收（Gate T1，全绿才过）**：
1. `Test-Path -LiteralPath 'H:\UltimaAI\UltimaAgent\docs\specs\voice-entry-authority-decision-20261110.md'` → True
2. `rg -c -- 'E3 的测试我是测过的' <file>` ≥ 1
3. `rg -c -- 'sapi_fallback' <file>` ≥ 1
4. 四行机检各命中 1 次：`rg -c -- 'idx=24' <file>` ≥1、`idx=26` ≥1、`idx=4` ≥1、`idx=15` ≥1
5. `rg -c -- '本单只出规格' <file>` ≥ 1
6. `rg -c -- '降级' <file>` ≥ 1 且同段含 `禁止静默`
7. 文件内不出现 `docs/baselines/`、`docs/decisions/`

**禁止**：写实现代码；改任何参数值；重开 Q3/Q5 结论；声称 E3 已具备 CV3 音色。

### T2 · 产品基线新建
**文件**：`docs/specs/voice-next-product-baseline.md`（新建）

**写什么**：
1. 标题：「UltimaAgent 语音产品基线（E3 `src/voice-next/`）」+ 副标题「工单 0035 v2.0 建立」
2. 双向不越界声明，两条各自独立成行：
   - `**本文件只约束 `src/voice-next/`（E3）**：不约束 `src/brain/voice/kws_listener.py`（E1）与 `data/logs/voice-listen-daemon.py`（E2）。`
   - `**E1/E2 的取值以 `docs/specs/kws-wakeup-params-baseline.md`（历史实现基线）为准，且该文件取值不约束本文件。**`
3. a–j 十项表（每项一行，含「取值」与「依据」两列）：
   - （a）唤醒词 `你好问问`
   - （b）`keywords_threshold` 0.25
   - （c）`keywords_score` 1
   - （d）`num_trailing_blanks` 1
   - （e）模型 `models\voice-next` 独立副本 / chunk-16
   - （f）输入端点 WASAPI 名字解析（`麦克风 (USBAudio2.0)`）
   - （g）KWS 增益 固定 `input_gain=10`，无自适应
   - （h）指令上限 15s / 结束静音 0.8s / 等开口 5s
   - （i）有效语音门控 WebRTC VAD ≥5×20ms，无 peak/rms 门
   - （j）无 `BEEP_SETTLE_SEC`，仅播放后 0.15s sleep
4. 三项待定，每项一行，**必须含字样 `待定，本单不定性`**，并写明缺什么证据：
   - `keywords_score` 2.0→1：缺设计意图说明或实测召回对比
   - `num_trailing_blanks` 8→1：缺说明是否随官方默认模型参数套用，或词尾延迟实测
   - `BEEP_SETTLE_SEC` 移除：缺实测 0.15s 是否足以避免提示音残响被录入 KWS
5. **CV3 音色段**：目标=接 E1 那套 CV3；当前=SAPI（临时）；规格见 `docs/specs/voice-next-cv3-tts.md`（本单只出规格不出实现）。
6. 未验收声明，引 `src/voice-next/README.md` 原文：`合成样本是冒烟证据，不是远场稳定性证明`、`稳定性仍需真人验收`。
7. 变更记录节（表头 + 2026-11-10 首条「据 0035 v2.0 改判建立」）。

**验收（Gate T2，全绿才过）**：
1. `Test-Path` → True
2. 十个编号（a）–（j）各命中 ≥1（回执中逐项列出对应行号）
3. `rg -c -- '只约束' <file>` ≥ 1 且 `rg -c -- '不约束本文件' <file>` ≥ 1
4. `rg -c -- '待定，本单不定性' <file>` ≥ 3，且三项名称各自出现在所在标注行内
5. `rg -c -- '合成样本是冒烟证据' <file>` ≥ 1 且 `rg -c -- '稳定性仍需真人验收' <file>` ≥ 1
6. `rg -c -- 'CV3' <file>` ≥ 2
7. `rg -c -- '数值已定|确认为设计差异|确认为漂移' <file>` = 0

**禁止**：定性三项待定值；把 F3 的历史取值当成本入口现行值；声称 E3 已验收或已具备 CV3 音色；删除未验收声明。

### T3 · 历史基线改造
**文件**：`docs/specs/kws-wakeup-params-baseline.md`（改，入场实测 110 行 / 28,617 B）

**写什么**：
1. **文档定位（第 3 行一带）**改为「历史实现基线（E1/E2）」。
2. **顶部（第 5 行之后）追加一行**：
   ```
   **本文所辖入口已降为历史实现**：产品主线见 `docs/specs/voice-next-product-baseline.md`。本文取值不约束该主线，该主线取值亦不约束本文。
   ```
3. **第 16 行**：
   - 原：`` | 输出设备 | `PLAY_DEVICE = 26`（耳机 POISON M@LOFREE，WASAPI） | TTS 回放 | ``
   - 新：`` | 输出设备 | `PLAY_DEVICE = 24`（耳机 POISON M@LOFREE，WASAPI 44100Hz） | TTS 回放 | ``
4. **变更记录（第 110 行之后）追加一行**，日期 `2026-11-10`，内容须含：
   - 标题：`PLAY_DEVICE` 顶部摘要回写 24（机检裁决）
   - 四行机检原文（逐字，同 T1 第 7 条）
   - 结论：POISON 耳机在 WASAPI 栈下为 idx=24（44100Hz）；idx=26 为 Steam 虚拟声卡（48000Hz）
   - 旧值 26 表述为**「已被取代」**；第 106 行既有勘误记录**原样保留**
   - 同批修正代码 `src/brain/voice/kws_listener.py:43` 26→24（T5），使文档与代码同值
5. **待办追加一行**：`设备应记端点身份（名字+采样率+驱动栈）而非整数索引——同一副 POISON 耳机在 MME / DirectSound / WASAPI 三栈下索引分别为 4 / 15 / 24，为实证。本单不改，留作后续。`

**验收（Gate T3，全绿才过）**：
1. `rg -c -- '历史实现基线' <file>` ≥ 1
2. `rg -c -- 'voice-next-product-baseline.md' <file>` ≥ 1
3. `rg -n -- 'PLAY_DEVICE' <file>` → 摘要行含 `24` 且含 `44100Hz`
4. `rg -c -- '2026-11-10' <file>` ≥ 1
5. `rg -c -- '已被取代' <file>` ≥ 1
6. `git diff -U0 -- docs/specs/kws-wakeup-params-baseline.md` 的**删除行**中，出现的参数行只允许是 `PLAY_DEVICE = 26` 那一条；不得出现 `keywords_threshold`、`keywords_score`、`num_trailing_blanks`、`max_active_paths`、`MIC_DEVICE`、`DEV_IN`、`BEEP_SETTLE_SEC`、`np.interp` 任何一条
7. 第 106 行既有勘误文字未出现在 diff 的删除行中
8. 文档行数 ≥ 110（相对 T0 记录的入场实测值只增不减）

**禁止**：改任何冻结参数值；改第 16 行以外的摘要行；改写第 106 行既有记录；重排表格；把 26 写成「被删除」。

### T4 · CV3 接入规格
**文件**：`docs/specs/voice-next-cv3-tts.md`（新建）

**写什么**：
1. 标题：「E3 接入 CV3 音色技术规格（工单 0035 v2.0）」+ 一句话定位：本文件只出规格，**不含实现代码**。
2. **形态结论**：常驻预热 worker，独立进程跑在 `tools\venv-openjarvis\Scripts\python.exe`（有 torch）；E3 主进程只经 IPC 传参，**不 import torch**。否决理由各一句：单次子进程（冷启动数分钟不可忍）、本地 HTTP 服务（引入端口依赖，收益不抵）。
3. **IPC 协议字段表**：`text`（必填）、`path`（必填）、`voice_id`（可选，缺省 `CV3`）、`sample_rate`（可选，缺省 `None` = 交由 `play()` 的 soxr 重采样）。
4. **接口签名**：`synthesize(text, path, *, voice_id=None, sample_rate=None)`，保持向后兼容——现有调用点零改动。
5. **超时与失败返回码**：给出具体数值（如单次合成超时上限、worker 崩溃的返回码分类）。
6. **失败语义**：CV3 不可用 → 降级 SAPI，`status.json` 的 `tts_backend` 写 `sapi_fallback` + 日志告警；**禁止静默降级**。
7. **worker 生命周期**：预热时机（启动即预热 / 首轮前预热，二选一并给依据）、保活机制、超时回收、kill 与重启策略。
8. **验收门槛**：机检部分 = wav 存在 + 有 CV3 生成日志/模型指纹证据；人工部分 = 音色由 Owner 听。说明为何不能纯机检（无 gold 数据、嵌入相似度无阈值）。
9. 明确`本单只出规格、不写实现代码`。

**验收（Gate T4，全绿才过）**：
1. `Test-Path` → True
2. `rg -c -- 'synthesize(text, path, \*, voice_id=None, sample_rate=None)' <file>` ≥ 1
3. `rg -c -- '不 import torch' <file>` ≥ 1
4. `rg -c -- 'sapi_fallback' <file>` ≥ 1
5. IPC 四字段 `text`、`path`、`voice_id`、`sample_rate` 各命中 ≥1
6. `rg -c -- '^```python' <file>` = 0（规格文档不得含 python 代码块）
7. `rg -c -- '不写实现' <file>` ≥ 1

**禁止**：写任何实现代码；把采样率写死进代码；主张主进程 import torch；重开 Q3 结论。

### T5 · 代码常量修正（仅一行）
**文件**：`src/brain/voice/kws_listener.py`（**仅第 43 行**）

**写什么**：
1. 第 43 行：
   - 原：`PLAY_DEVICE = 26      # 输出：26=耳机 (POISON M@LOFREE)（sounddevice WASAPI 索引）`
   - 新：`PLAY_DEVICE = 24      # 输出：24=耳机 (POISON M@LOFREE)（sounddevice WASAPI 索引，44100Hz）；idx=26 为 Steam 虚拟声卡，勿用`
2. 不新增常量、不改变量名、不动 L106 / L111 调用点。

**验收（Gate T5，全绿才过）**：
1. `rg -n -- 'PLAY_DEVICE' src/brain/voice/kws_listener.py` → 常量行为 24；两处调用点（`sd.query_devices(PLAY_DEVICE)`、`sd.play(audio, rate, device=PLAY_DEVICE)`）保持不变
2. `rg -c -- 'PLAY_DEVICE = 26' src/brain/voice/kws_listener.py` = 0
3. `git diff -U0 -- src/brain/voice/kws_listener.py` 显示变更行 ≤ 2（原行删 + 新行增）
4. AST 语法校验通过（**只校验语法，不导入模块**，避免初始化音频设备）：
   ```powershell
   & 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -c "import ast; p=r'H:\UltimaAI\UltimaAgent\src\brain\voice\kws_listener.py'; ast.parse(open(p,encoding='utf-8').read()); print('AST_OK')"
   ```
   期望输出 `AST_OK`
5. `rg -c -- '44100' src/brain/voice/kws_listener.py` 的增量只来自新增注释，不得出现在代码逻辑里

**禁止**：改 `keywords_threshold` / `keywords_score` / `num_trailing_blanks` / 增益 / 门控 / 静音时长任何一处；改调用点；把采样率写死进逻辑；重启 daemon 或语音进程；运行任何会初始化音频设备的脚本。

### T6 · 索引登记
**文件**：`docs/INDEX.md`

**写什么**：
1. 按既有条目的字段与列数格式，为下列三份新文档各登记一行：
   - `docs/specs/voice-entry-authority-decision-20261110.md`
   - `docs/specs/voice-next-product-baseline.md`
   - `docs/specs/voice-next-cv3-tts.md`

**验收（Gate T6，全绿才过）**：
1. `rg -c -- 'voice-entry-authority-decision-20261110' docs/INDEX.md` = 1
2. `rg -c -- 'voice-next-product-baseline' docs/INDEX.md` = 1
3. `rg -c -- 'voice-next-cv3-tts' docs/INDEX.md` = 1
4. `git diff -U0 -- docs/INDEX.md` 仅新增 3 行，无删除行、无其他改动
5. 新增三行的列数与相邻既有条目一致（回执中并排粘贴相邻行作对照）

**禁止**：改动既有条目；重排、批量格式化、重新排序索引；新建索引分节。

### T7 · 总验收
**验收（Gate T7，全绿才过）**：
1. **差分断言（不得用「status 恰 N 条」这种绝对断言，见 L104）**：
   ```powershell
   git -C H:\UltimaAI\UltimaAgent status --porcelain | Set-Content -LiteralPath "$env:TEMP\0035-t7-status.txt" -Encoding utf8
   Compare-Object (Get-Content -LiteralPath "$env:TEMP\0035-t0-status.txt") (Get-Content -LiteralPath "$env:TEMP\0035-t7-status.txt")
   ```
   期望：**恰好 6 条 `=>`（右侧独有，即本单新增/变更的 6 个路径）**，且**无 `<=`（左侧独有，即原有改动未被触碰）**。
2. 六个路径逐一对上：`docs/specs/voice-entry-authority-decision-20261110.md`（新增）、`docs/specs/voice-next-product-baseline.md`（新增）、`docs/specs/kws-wakeup-params-baseline.md`（改）、`docs/specs/voice-next-cv3-tts.md`（新增）、`src/brain/voice/kws_listener.py`（改）、`docs/INDEX.md`（改）。
3. `rg -c -- 'import torch' src/voice-next` 相对 T0 无新增。
4. `docs/decisions/` **入场即已存在**（2026-11-10 实测 `Test-Path` = True），本单只要求**不在其中新增或修改任何文件**（`git status --porcelain -- docs/decisions` 相对 T0 无新增）；`docs/baselines/` 须仍不存在（入场实测 `Test-Path` = False）。**不得删除已存在的 `docs/decisions/`。**
5. 提交（显式路径，禁 `-A`）：
   ```powershell
   git -C H:\UltimaAI\UltimaAgent -c user.name='ArkExlabs' -c user.email='ArkExlabs@users.noreply.github.com' add docs/specs/voice-entry-authority-decision-20261110.md docs/specs/voice-next-product-baseline.md docs/specs/kws-wakeup-params-baseline.md docs/specs/voice-next-cv3-tts.md src/brain/voice/kws_listener.py docs/INDEX.md
   git -C H:\UltimaAI\UltimaAgent commit -F <msgfile>
   git -C H:\UltimaAI\UltimaAgent show --stat
   ```
   `show --stat` 须显示**恰 6 个文件**。

**禁止**：删除/停用/归档任何入口；改 KWS/ASR/VAD/门控参数值；采样率写死；`git add -A`；`git stash`/`checkout`/`clean`。

---

## 3. 残留风险

1. **本单不含 CV3 实现**：F4 只出规格，`live.py` 与 `sapi.ps1` 未动。E3 在本单之后**仍然是 SAPI 音色**，改判只是把方向与规格落定。「E3 已换成 CV3」属后续单的事，本单不得宣称。
2. 同一设备跨驱动栈索引不同（MME=4 / DirectSound=15 / WASAPI=24），他机或重装驱动后 24 可能失效；F3 只记录本次机检事实，治本靠 T3 登记的「记端点身份」待办。
3. 三项待定未定性，E3 的声学行为仍不可断言。
4. 产品基线与历史基线两份文档存在未来同步漂移风险，「互不越界」目前仅靠人工遵守（一致性扫描器本单未建）。
5. **T5 未做真机回归**：改后 E1 的 TTS 是否真的从耳机出声，尚未验证。E1 已降历史，该验证归后续清理单，本单不宣称 E1 已恢复可用。
6. `data/logs/` 下守护脚本与入场既有的 562 行改动同处工作树，误提交风险靠显式路径纪律 + T0/T7 差分断言控制。

---

## 4. 给编码代理的任务粘贴模板

```
T0 已完成：HEAD=<sha>；status 入场 <N> 行（已落 $env:TEMP\0035-t0-status.txt）；baseline <N> 行（入场实测 110）SHA256=<sha256>；kws_listener PLAY_DEVICE=26（第43行）
T1 已完成，Gate 全绿：文件已建；Owner 原话命中；sapi_fallback 命中；idx=24/26/4/15 四行各 1；「本单只出规格」命中；无自拟目录
T2 已完成，Gate 全绿：a–j 十项行号 <列出>；双向声明各≥1；待定标注 3 处；README 两句原文命中；确定性结论词 0 命中
T3 已完成，Gate 全绿：历史实现基线抬头已加；PLAY_DEVICE=24 且带 44100Hz（第 16 行）；变更记录含 2026-11-10 / 已被取代；待办已加；删除行仅 PLAY_DEVICE=26 一条；第 106 行原样保留；行数 111→<N>
T4 已完成，Gate 全绿：签名命中；不 import torch 命中；sapi_fallback 命中；IPC 四字段齐；python 代码块 0
T5 已完成，Gate 全绿：第 43 行=24，注释含「idx=26 为 Steam 虚拟声卡，勿用」；= 26 命中 0；diff 变更行 2；调用点未动；AST_OK
T6 已完成，Gate 全绿：三文件名各命中 1；diff 仅新增 3 行
T7 总验收：Compare-Object 输出 <粘贴>（期望恰 6 条 =>、0 条 <=）；commit <sha>；show --stat 恰 6 文件
越界声明：无
```
