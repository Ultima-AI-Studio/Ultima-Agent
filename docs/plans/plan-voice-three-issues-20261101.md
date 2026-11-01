# UltimaAgent 三问题攻坚方案（KWS 入口 / ASR 纠错 / 回答约束）

> 方案：2026-11-01 豆包主脑（Owner 拍板："这三个问题能解决掉就先把这三个解决掉；感知层不再深挖，用现有声音链路往前推进"）
> 上游规则：G-TASKFLOW-001 + G-PLAN-001（先方案后工单，方案随单落盘）+ G-DISPATCH-001（登记全局主表 + UltimaManager 登记）
> 北极星：贾维斯 ｜ 现状基线：0009 completed（KWS 改词 CLI）、0010 completed（主脑 qwen3-8b-uncensored）、工单 C/D 方案已落盘未派发
> 结论先行：**三问题 = 三个新/更新工单（E/F + C/D 更新），全部可独立派发、独立验收；感知层音频栈不再深挖（已收口），声音链路用现状推进。**

---

## 〇、三问题现状核验结论（2026-11-01 代码核实）

| 问题 | 现状（已核验） | 缺口 |
|---|---|---|
| ① KWS 唤醒词可改且能记住 | 工单 0009 已完成：`scripts/kws_reconfig.py`（--add/--replace/--list/--validate + 热重载 + 自动化验证），tag `ultimaagent-kws-wakeword-reconfig-20261031` | **无用户入口**（只有 CLI，用户要"能修改"=语音命令/UI）；**"记住"未持久化**（0009 范围冻结不碰 voice_profile.py，改词未写回 profile custom）；当前 `voice-profile.json custom=null` 但 `keywords.txt` 含"查天气"行，**双源不一致** |
| ② ASR 识别跑偏（"水天/水量天听"类） | `asr.py` 已有 `initial_prompt`（L61）但只注入任务管理词（任务状态/优先处理/插队/确认/取消），**无天气/时间类高频词**；`interaction.py _normalize_utterance` 硬编码近音映射 4 条（水量天听→天气等），覆盖不全 | ASR 侧热词引导缺日常意图词；近音映射表硬编码、不可维护、未登记"水天"类新误识 |
| ③ 回答内容约束 | 工单 C/D 方案已落盘 `docs/plans/reply-constraint-implementation-plan-20261031.md`（意图路由门 + 约束解码 {reply_text,confidence,grounded} + 校验器） | **C/D 从未派发**；方案内模型引用为 qwen2.5:14b（现已换 qwen3-8b-uncensored），需更新实测对象 |

---

## 一、工单 E（新增）｜KWS 唤醒词用户入口 + 持久化

**拟命名**：`wo-ultimaagent-<日期>-<NNNN>--kws-wakeword-user-entry.md`

### 目标
1. **用户入口**：语音交互层新增"换唤醒词"意图命令（如"把唤醒词改成星期五"）→ 调用 `kws_reconfig.py` 改词 + 热重载 + 播报确认（"唤醒词已改为星期五"）；HUD/W6 语音管理页设置项（后续，本单不强制 UI）。
2. **持久化"记住"**：改词结果写回 `voice-profile.json` 的 `wakeword.custom`（复用 `voice_profile.save_user_override` 公开接口），daemon 重启后 `load_profile` 自动应用——**profile 成为唯一权威源**。
3. **一致性收敛**：核对并收敛当前双源不一致（profile custom=null vs keywords.txt 含"查天气"），明确来源后回填或清理，落盘记录。

### 范围冻结
- 只做：interaction 路由层新增意图分支 + save_user_override 调用 + 一致性核对 + 测试。
- 禁止修改：KWS 模型/tokens/全局参数基线（kws-wakeup-params-baseline.md 数值零漂移）；voice_profile.py 既有逻辑（只调公开接口）；daemon 音频栈；不做 W6 UI 大改。

### 验收口径
- 语音说"把唤醒词改成 XX" → 改词生效（新词可唤醒）+ 播报确认 + 日志可见热重载 pid 不变；
- 重启 daemon 后新唤醒词仍生效（profile 持久化）；改回"贾维斯"恢复默认；
- profile 与 keywords.txt 一致性核对记录落盘；pytest 全绿（venv-openjarvis）。

---

## 二、工单 F（新增）｜ASR 纠错系统化（热词引导 + 映射独立化）

**拟命名**：`wo-ultimaagent-<日期>-<NNNN>--asr-correction-systematic.md`

### 目标
1. **ASR 热词引导**：`asr.py` `initial_prompt` 扩充高频日常意图词（天气/时间/明天/上海/几点/温度/风/任务/进度等），从源头降低"查天气→水量天听"类近音误识；验证 faster-whisper 对该 prompt 的响应。
2. **近音映射独立化 + 扩充**：`_ASR_NEAR_HOMOPHONE` 从代码硬编码迁出为独立可维护配置（`config/asr-normalize.json` 或 data 表），扩充登记观测误识（含"水天"类：水天→天气、水田→水田不动、水平听听清→天气 等，逐条真机/离线验证后登记）。
3. **兜底保持**：`_FUZZY_*` 模糊意图词 + 编辑距离机制不动，近音纠错后的文本仍走既有意图规则。

### 范围冻结
- 只做：initial_prompt 词表（asr.py 单处修改）+ 归一化映射配置化 + 测试 + 证据。
- 禁止修改：ASR 模型/采样链路/daemon 主链；意图规则主结构（仅配置化不改判定逻辑）；不换识别引擎。

### 验收口径
- 注入"查一下明天的水量天听/水天"类测试音频/文本 → 归一化为"天气"且意图=天气查询；
- 正常语句（时间/任务/闲聊）回归不受影响；
- 映射表为独立配置、可追加条目；pytest 全绿（venv-openjarvis）。

---

## 三、工单 C + D（更新后派发）｜回答约束栈

沿用 `docs/plans/reply-constraint-implementation-plan-20261031.md` 方案，**派发前更新两处**：
1. 实测/接入对象：`qwen2.5:14b` → `qwen3-8b-uncensored`（工单 D 的 `scripts/probe_ollama_format.py` 实测对象、agent_server.py 接入点）；
2. 范围冻结里的模型引用同步更新（不引入云端意图 API、不换推理栈的底线不变）。

**依赖**：工单 C 先行（意图路由门 + 校验器升级，入口+出口闭环止血）；工单 D 依赖 C 出口稳定后做（约束解码硬约束）。

### 验收口径（沿用原方案）
- 路由门命中 DENY/ABSTAIN → 未进 Agent（日志可见 routing 标记 + 兜底话术）；
- "查天气/时间"正常回答不受影响；"水量天听"类不可信输入被拦；
- D：agent 输出恒为合法 JSON {reply_text,confidence,grounded}；非法输出走降级不裸播；
- pytest 全绿 + 专项全绿；冻结 tag。

---

## 四、派发顺序与登记

| 序 | 工单 | 依赖 | 备注 |
|---|---|---|---|
| 1 | E（KWS 入口+持久化） | 无 | 0009 已完成，补入口闭环 |
| 2 | F（ASR 纠错系统化） | 无 | 独立，收益立现 |
| 3 | C（意图路由+校验器） | 无 | 约束栈止血层 |
| 4 | D（约束解码） | C | 依赖 C 出口稳定 |

派发时按 G-DISPATCH-001：核对 WIP 双层上限（每项目执行中 ≤1）+ 登记全局主表 `tasks/queue/index.md` + 走 UltimaManager 登记接口；执行端 Codex（gpt-5.6-sol）。

## 五、范围冻结总则（本方案全部工单共用）

- **感知层不再深挖**：daemon 音频栈（音量/并发/耦合）已收口，不再迭代；声音链路用现状（sherpa 44100Hz）往前推进；
- 不改模型权重/推理参数（约束栈 D 仅做 format 约束解码实测接入）；
- 不换推理栈、不引入云端意图 API（隐私红线）；
- CV3 音色克隆（0008 训练中）与本方案解耦，不阻塞、不依赖。

## 六、依据

- 工单 0009/0010/0013 状态：`tasks/queue/index.md`（2026-11-01 读取）
- KWS 改词机制：`src/brain/voice/voice_profile.py`（custom/apply_to_daemon/save_user_override）+ `scripts/kws_reconfig.py` + `test_voice_wakeword_reload.py` 6 测试
- ASR 现状：`src/brain/voice/asr.py` L54-61（initial_prompt）+ `src/brain/interaction.py` L426-452（_normalize_utterance）
- 回答约束：`docs/plans/reply-constraint-implementation-plan-20261031.md`
