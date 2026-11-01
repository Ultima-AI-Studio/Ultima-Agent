# 工单 wo-ultimaagent-20261101-0015 ｜ UltimaAgent ｜ 工程 ｜ ASR 纠错系统化（热词引导 + 近音映射独立化）

> 原单 ID：`wo-ultimaagent-20261101-0015` ｜ 显示标题：UltimaAgent｜工程｜ASR 纠错系统化（工单 F）
> 依据：G-DISPATCH-001 自主推进版 + G-TASKFLOW-001 ｜ 方案：`docs/plans/plan-voice-three-issues-20261101.md`（2026-11-01 定稿，Owner 拍板"整体派发"）
> 北极星：贾维斯（"水量天听/水天"类近音误识系统化收敛）
> 创建：2026-11-01 ｜ 状态：待派发

---

## 一、目标与范围

### 1.1 目标（Result）

ASR 识别跑偏（"查天气→水量天听/水天"类）**系统化收敛**：
1. **热词引导**：`src/brain/voice/asr.py` `initial_prompt`（L61）从只含任务管理词，扩充高频日常意图词（天气/时间/明天/今天/几点/温度/上海/日程等），从源头降低近音误识；
2. **近音映射独立化**：`interaction.py _normalize_utterance` 的 `_ASR_NEAR_HOMOPHONE` 硬编码 4 条迁出为独立可维护配置 `config/asr-normalize.json`，并扩充登记观测误识（含"水天→天气"类，逐条真机/离线验证后登记）；
3. **兜底保持**：`_FUZZY_*` 模糊意图词与编辑距离机制不动，近音纠错后的文本仍走既有意图规则。

### 1.2 范围冻结（边界，禁止越界）

- **只做**：asr.py initial_prompt 词表（单处修改）+ 近音映射配置化（interaction.py 对应段 + 新配置文件）+ 测试与证据。
- **禁止修改**：
  - ASR 模型 / faster-whisper 推理参数 / 采样链路 / daemon 主链；
  - 意图规则主结构（_FUZZY_* 关键词与判定逻辑仅保持，不重写）；
  - 不换识别引擎（sherpa ASR 备用链不动）；
  - voice_profile / KWS 基线 / UI 均不碰。

### 1.3 写域

| 文件 | 动作 | 说明 |
|---|---|---|
| `src/brain/voice/asr.py` | 修改 | `initial_prompt` L61 扩充天气/时间/日程类高频词 |
| `config/asr-normalize.json` | 新建 | 近音映射独立配置（含默认 4 条迁移 + 新增"水天"类） |
| `src/brain/interaction.py` | 修改 | `_normalize_utterance` 改读配置（保留默认兜底表） |
| 测试文件 | 新建/修改 | 注入"水量天听/水天"类 → 归一化断言 |
| `docs/reports/stage-asr-correction-20261101.md` + evidence/ | 新建 | 阶段报告与证据 |

---

## 二、DoR 就绪门

| # | 就绪项 | 判定 | 证据 |
|---|---|---|---|
| 1 | 验收 Gate 可判定 | ✅ 封闭清单（§四） | 注入用例/回归/映射可维护 |
| 2 | 无未决依赖 | ✅ 无（独立工单） | — |
| 3 | 写入域已声明 | ✅ §1.3 | — |
| 4 | 推理强度已声明 | ✅ T0 medium / T1 medium / T2 medium / T3 high / T4 low | — |
| 5 | 禁止项已写 | ✅ §1.2 | — |

---

## 三、执行步骤（T0→T4，逐 T Gate PASS 再进下一条）

### T0 环境盘点（medium）
- [ ] C1 读 `src/brain/voice/asr.py` L50-61 现状（faster-whisper 调用 + initial_prompt 原文），确认改动点。
- [ ] C2 读 `src/brain/interaction.py` L426-452（_normalize_utterance + _ASR_NEAR_HOMOPHONE）与 `_FUZZY_*` 兜底词，确认配置化接入方式。
- [ ] C3 离线注入基线：用现有音频/文本样例，验证"查天气"类误识现状与 initial_prompt 影响（有真机观测记录可引用 L33/L41 证据）。
- [ ] C4 证据落盘 `docs/reports/evidence/asr-correction/t0-env-probe.txt`。
- Gate：C1-C4 全绿 → T1。

### T1 initial_prompt 扩充（medium）
- [ ] C1 扩充词表：天气、明天、今天、几点、温度、风、雨、雪、上海、时间、日程、任务、进度等高频意图词（按观测/常用度登记，控制在提示词长度上限内）。
- [ ] C2 离线验证：注入"查天气"类测试音频（TTS 合成或真机录）→ 转写正确率对比（扩充前后）；记录对比结果。
- Gate：扩充后"查天气"类近音误识率下降或持平不恶化；证据 `t1-prompt.txt`。

### T2 近音映射独立化 + 扩充（medium）
- [ ] C1 新建 `config/asr-normalize.json`：迁移默认 4 条（水量天听/水平听听清/水平听→天气、明天上海的这→明天上海的天气）+ 新增"水天→天气"等观测误识（逐条注明来源/验证状态）。
- [ ] C2 `_normalize_utterance` 改读配置（文件不存在/解析失败时回退内置默认表，不报错断链）。
- [ ] C3 注入用例断言：`查一下明天的水量天听` / `明天上海的水天` → 归一化为"天气"且下游意图=天气查询。
- [ ] C4 正常语句回归：时间/任务/闲聊语句不被误替换（"水田"类真实词不受影响——映射须整词/短语匹配，禁单字替换）。
- Gate：注入用例全过 + 正常语句零误伤；证据 `t2-normalize.txt`。

### T3 收口（high）
- [ ] C1 全量回归：`tools/venv-openjarvis/Scripts/python.exe -m pytest src -q` 全绿（工程验收必须用 venv-openjarvis 解释器）+ 语音专项绿。
- [ ] C2 冻结 tag：`git tag ultimaagent-asr-correction-20261101`（先 commit，`git rev-parse` 可解析）；**推送用免代理：`git -c http.proxy= -c https.proxy= -c http.https://github.com.proxy= push`**。
- [ ] C3 阶段报告 `docs/reports/stage-asr-correction-20261101.md`（Gate 证据 + 扩充前后对比 + 映射表来源登记）。
- Gate：C1-C3 全绿 → T4。

### T4 回执（low）
八字段（见 §五）。

---

## 四、验收口径（封闭清单，全绿才过）

| Gate | 判定 | 证据位置 |
|---|---|---|
| 机制 | initial_prompt 含扩充高频词；近音映射为独立配置且可追加 | t1-prompt.txt + t2-normalize.txt |
| 功能 | "水量天听/水天"类输入归一化天气且意图正确；正常语句零误伤 | t2-normalize.txt |
| 回归 | pytest 全量绿（venv-openjarvis）+ 专项绿 | t3/ |
| 冻结 | tag `ultimaagent-asr-correction-20261101` 存在且可解析 | git tag -l |

---

## 五、执行端回执（八字段，必填）

| 字段 | 值 |
|---|---|
| 链路号/工单号 | wo-ultimaagent-20261101-0015 |
| 执行端 | Codex（gpt-5.6-sol，codex exec） |
| 完成状态 | 已完成 / 阻塞 / 已终止（三选一） |
| 根因结论 | （一句话） |
| 产出路径 | src/brain/voice/asr.py、src/brain/interaction.py、config/asr-normalize.json、测试、stage 报告、evidence/ |
| 验收证据 | T0-C1~C4 / T1 / T2-C1~C4 / T3-C1~C3 逐条 PASS + pytest 摘要 + 扩充前后对比 |
| 越界声明 | 无=明确写"无"；含未动范围（ASR 模型/推理参数/daemon/意图规则主结构/UI） |
| 环境声明 | 真机：热词效果实测；如仅离线验证须写"仅离线预期，真机待验收" |

## 附：推理强度
T0 medium ｜ T1 medium ｜ T2 medium ｜ T3 high ｜ T4 low
