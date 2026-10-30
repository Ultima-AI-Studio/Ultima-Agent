# Codex 工单 · UltimaAgent｜架构｜多层级覆盖 voice-profile（人设/唤醒词/回答风格/输入设备统一配置）

> 版本：v1.1 ｜ 状态：**已冻结**（T0-T3 PASS、T4 阻塞经 0006 清障转绿；2026-10-30 冻结 commit 12330ea + tag wo-ultimaagent-20261030-0003-frozen-20261030）｜ 适用工具：Codex（`codex exec`，`-m gpt-5.6-sol`）
> 用法：按 T0→T4 顺序逐条执行，Gate 全绿才过，再进下一条。
> 范围依据：`H:\UltimaAI\INDEX.md` + `H:\UltimaAI\_shared\paradigms\UltimaAI-任务工作流范式.md` + `H:\UltimaAI\_shared\paradigms\UltimaAI-全局工单命名标准.md` + `docs/INDEX.md`
> 调研依据：`docs/research/jarvis-persona-research-20261030.md`（贾维斯人设现成方案调研）+ `docs/specs/kws-wakeup-params-baseline.md`（KWS/ASR 参数冻结基线）
> 北极星：**贾维斯**（UltimaAgent 一切调整向贾维斯靠拢；默认人设固定 Jarvis，允许 L2 用户覆盖）
> 登记：2026-10-30 ｜ 原单 ID：wo-ultimaagent-20261030-0003 ｜ 类型：架构

---

## 0. 范围冻结

**本阶段只做（多层级覆盖 voice-profile 架构）**：

1. 新增 `H:\UltimaAI\UltimaAgent\config\voice-profile.json`（或 `data\config\voice-profile.json`，二选一，与 `docs/INDEX.md` 目录约定一致）：统一装载 L1 内置默认 / L2 用户覆盖 / L3 运行期覆盖，覆盖字段：
   - `persona`：默认 `jarvis`（内置人设兜底文件路径），`override`（L2 用户人设文件，缺失回退 jarvis）；
   - `wakeword`：`words`（内置 6 变体，同 keywords.txt）、`custom`（L2 用户自定义称呼，写入后同步更新 keywords.txt 并支持 daemon 热重载）；
   - `style`：`mode`（默认 `efficient-jarvis`：高效简洁 + 管家克制）、`banned_phrases`（默认含"关注、点赞、订阅、点个关注"等营销话术黑名单）、`max_sentences`（默认 2 句）；
   - `input`：`mode`（默认 `auto` 自动探测）、`device_index`（L2 手动指定，优先于 auto）、`prefer_wasapi48k`（默认 true，配合工单 0004）；
2. 新增配置装载模块 `src/brain/voice/voice_profile.py`（或并入现有 voice 模块）：`load_profile()` 按 L3→L2→L1 回退装载，任何层缺失不得报错（回退默认）；`save_user_override()` 写 L2；`apply_to_daemon()` 将唤醒词/风格应用到运行中 daemon（热重载，不重启进程）；
3. **回答风格约束接入 agent 兜底**（`src/brain/interaction.py` `_try_agent_fallback` 或 jarvis.md 人设文件）：默认人设加载 `libs/base/openjarvis/configs/openjarvis/prompts/personas/jarvis.md`，追加三条硬约束——只答事实不发明；禁止营销/引导关注点赞话术；单次回答 ≤2 句短句（语音场景）；
4. **唤醒词可修改闭环**：改 `voice-profile.json` 的 `wakeword.custom` → 装载模块同步写 `models/sherpa/kws/keywords.txt` → daemon 热重载生效（无需重启）→ `interaction.py` `_WAKE_ECHO_ONLY` 词根正则同步更新；
5. 配套单元测试 + 全量回归通过。

**本阶段不做**：不做 W6 语音管理 UI 页（UI 后续接）；不做云端 ASR 主链路（隐私红线：语音不出本机）；不改 KWS 参数基线数值本身（阈值/score 仍归 `kws-wakeup-params-baseline.md` 管）；不做 TTS 音色克隆样本库；不引入第三方配置库（仅标准库 json）。

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `config/voice-profile.json`（新增）+ `src/brain/voice/voice_profile.py`（新增） | 装载回退单测全绿：L1 默认存在、L2 override 生效、L3 优先、缺文件不炸 |
| T1 | `src/brain/voice/voice_profile.py`（热重载）+ daemon 接线 | 唤醒词热重载实测：改 custom → keywords.txt 同步更新 → 运行中 daemon 生效（不重启） |
| T2 | jarvis.md 人设 + 三条硬约束（interaction.py 兜底接线） | 实测"查天气"类回答无营销话术、≤2 句；人设加载失败回退 jarvis |
| T3 | 回答后过滤（banned_phrases 命中拦截） | 单测：含"关注/点赞"的回答被过滤/替换；正常回答不受影响 |
| T4 | 总验收 | 端到端实测 + 全量回归 + 证据落盘 |

---

## 2. 任务明细（每条 T 严格三段式）

### T0 · voice-profile.json + 装载模块（L1/L2/L3 回退）

**文件**：
- `H:\UltimaAI\UltimaAgent\config\voice-profile.json`（新增；若 config 目录约定冲突则用 `data/config/`，按 docs/INDEX.md）
- `H:\UltimaAI\UltimaAgent\src\brain\voice\voice_profile.py`（新增）
- `H:\UltimaAI\UltimaAgent\src\brain\tests\test_voice_profile.py`（新增测试）

**写什么**：
1. `voice-profile.json` 结构（含默认值）：
   ```json
   {
     "persona": { "name": "jarvis", "override": null },
     "wakeword": { "words": ["j iǎ w éi s ī", ...6变体同keywords.txt], "custom": null },
     "style": { "mode": "efficient-jarvis", "banned_phrases": ["关注", "点赞", "订阅", "点个关注"], "max_sentences": 2 },
     "input": { "mode": "auto", "device_index": null, "prefer_wasapi48k": true }
   }
   ```
2. `load_profile(runtime_overrides: dict | None = None)`：返回合并后 profile；优先级 L3（runtime）> L2（json 中 override/custom/device_index 非空）> L1（内置默认）；任何文件缺失/JSON 损坏 → 返回纯内置默认 dict（不抛异常，记 warning）；
3. `save_user_override(overrides: dict)`：只写 L2 字段，保留其余；写失败返回 False 不炸链路；
4. `validate_profile(p)`：字段存在性校验，非法值回退默认。

**验收（Gate T0）**：
- [ ] 单测 ≥6：①无文件→内置默认；②损坏 JSON→内置默认；③L2 override 生效；④L3 覆盖 L2；⑤save 后 reload 保留；⑥字段缺失回退默认；
- [ ] `python -m pytest src/brain/tests/test_voice_profile.py -q --disable-warnings` 全绿（Agent 专用解释器，见 T4）。

**禁止**：不引入第三方库（仅标准库 json/pathlib/logging）；不修改 KWS 参数基线数值；不硬编码绝对路径（用 ROOT 常量）。

---

### T1 · 唤醒词热重载（custom → keywords.txt → daemon 生效）

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\voice\voice_profile.py`（修改：apply_to_daemon）
- `H:\UltimaAI\UltimaAgent\src\brain\voice\kws_listener.py`（修改：监听 keywords.txt 变更或提供 reload 入口）
- `H:\UltimaAI\UltimaAgent\data\logs\voice-listen-daemon.py`（修改：热重载支持，守护进程模式）
- `H:\UltimaAI\UltimaAgent\src\brain\interaction.py`（修改：`_WAKE_ECHO_ONLY` 词根从 profile 读取，不硬编码"贾维斯/乔维斯"）
- `H:\UltimaAI\UltimaAgent\src\brain\tests\test_voice_wakeword_reload.py`（新增测试）

**写什么**：
1. `apply_to_daemon()`：将 `wakeword.custom`（或 words 全集）写入 `models/sherpa/kws/keywords.txt`（保持 6 变体 + custom 追加、ULTIMA 行保留），触发 daemon 侧 `KeywordSpotter` 重建（kws_listener 暴露 `reload_keywords()`；daemon 监听文件 mtime 变化自动重建）；
2. daemon 热重载实现：检测 keywords.txt 变更 → 重建 spotter（替换全局实例，旧流安全弃用）；重载失败保留旧 spotter 并记 error（不退出进程）；
3. `interaction.py`：`_WAKE_ECHO_ONLY` 与词根列表从 `load_profile()` 的 wakeword 动态生成（default 含"贾维斯/乔维斯"，custom 追加），去除硬编码字符串；
4. 热重载不打断正在进行的采集回合（当前回合用旧 spotter 收尾）。

**验收（Gate T1）**：
- [ ] 单测 ≥4：改 custom→keywords.txt 同步；mtime 触发重建；重载失败保留旧实例；交互词根动态生成；
- [ ] 实测（专用解释器）：起 daemon → 修改 profile custom → 不重启进程，日志确认 spotter 重建 + 新词可命中（WAV 注入或真机）；
- [ ] 既有唤醒回归不破坏（基线文档 6 变体仍可命中）。

**禁止**：不硬编码新绝对路径；不通过杀进程方式实现热重载；不改基线参数数值。

---

### T2 · jarvis.md 人设 + 三条硬约束接入

**文件**：
- `H:\UltimaAI\UltimaAgent\libs\base\openjarvis\configs\openjarvis\prompts\personas\jarvis.md`（修改：追加硬约束段）
- `H:\UltimaAI\UltimaAgent\src\brain\interaction.py`（修改：`_try_agent_fallback` 前按 profile.persona 装载）
- `H:\UltimaAI\UltimaAgent\src\brain\tests\test_persona_constraints.py`（新增测试）

**写什么**：
1. jarvis.md 在 CONSTRAINTS 段追加：
   ```
   - ONLY answer facts present in the provided data or the user's actual question. Never invent.
   - NEVER include marketing, promotion, or engagement content (no follow/like/subscribe asks, no recommendations to visit channels).
   - Keep spoken replies to 2 short sentences max (voice scenario). No filler.
   ```
   （保留原忠诚/英伦克制/尊称人格，不破坏北极星）
2. `interaction.py` `_try_agent_fallback`：调用前确认加载 persona（jarvis 默认；`profile.persona.override` 非空时加载 override 文件，失败回退 jarvis）；agent 回答后过 `banned_phrases` 过滤（命中→替换为安全短句"收到。"或重试一次）；
3. persona 文件读取失败 → 回退 jarvis 内置模板（不能因人设文件缺失导致 agent 无约束裸奔）。

**验收（Gate T2）**：
- [ ] 单测 ≥4：persona 正常加载；override 存在时优先；override 缺失回退 jarvis；回答含 banned 词被拦截；
- [ ] 实测（起 agent_server + interaction）：问"查天气"回复 ≤2 句且无营销话术；随机闲聊无"关注/点赞"类引导。

**禁止**：不删除 jarvis 原人格描述；不新增英文营销性引导；不绕过 banned 过滤直接放行 agent 原文。

---

### T3 · 回答后过滤（banned_phrases 兜底）

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\voice\voice_profile.py`（修改：filter_reply）
- `H:\UltimaAI\UltimaAgent\src\brain\tests\test_reply_filter.py`（新增测试）

**写什么**：
1. `filter_reply(text, profile) -> str`：命中 `banned_phrases` 任一 → 返回 `"收到。"`（或截断到命中前一句）；未命中 → 原文；空输入 → 空；
2. 过滤在 agent 兜底与规则表回复统一出口调用（interaction 层，保证所有语音回答都过）；
3. `max_sentences` 截断：按 `。！？` 切句，超 2 句截到第 2 句（不拆半句）。

**验收（Gate T3）**：
- [ ] 单测 ≥4：命中 banned→替换；未命中→原文；超句→截断；空→空；
- [ ] 边界：句子中间含"点赞"（如"这个功能给个赞"）不误杀（按上下文黑名单短语精确匹配，可配正则）。

**禁止**：不误杀正常问答；不过度截断关键信息（天气结果等短句不受影响）。

---

### T4 · 总验收

**文件**：本工单（更新状态）+ `docs/reports/` 阶段报告 + 证据目录

**写什么**：
1. 全量单测回归：`H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest src -q --disable-warnings`（**Agent 专用解释器，禁止用系统 Python**）→ 全绿 + 无新增失败；
2. 端到端实测：起 agent_server + daemon → ①默认配置启动（L1 全生效）；②改 voice-profile custom 称呼 → 热重载 → 新称呼唤醒（WAV 注入）；③"查天气"回答 ≤2 句无营销话术；④persona override 缺失回退 jarvis；
3. 阶段报告 `docs/reports/stage-voice-profile-20261030.md`：Gate 逐条核对（T0-C1~C6/T1-C1~C4/T2-C1~C4/T3-C1~C4/T4 全量），证据路径、越界声明（未动：W6 UI/云端 ASR/参数基线数值/TTS 克隆/第三方配置库）；
4. 证据落盘 `docs/reports/evidence/voice-profile/`：单测输出、热重载实测、回复过滤样例、回归全量输出；
5. 回执 8 字段按 Codex 范式 §5 输出。

**验收（Gate T4）**：总验收清单全绿；阶段报告存在且逐项勾选；回执 8 字段齐全；越界声明如实。

---

## 3. 给编码代理的任务粘贴模板

```
T0 voice-profile.json+装载模块：已完成，Gate T0 全绿（8 passed：回退/覆盖/优先级/保存回读）
T1 唤醒词热重载：已完成，Gate T1 全绿（6 passed；中文 custom 经指定 ASR 解释器转换；同 PID custom→keywords.txt→spotter 重建；新词与原词 WAV 均命中）
T2 jarvis 人设+三硬约束：已完成，Gate T2 全绿（19 passed，含 T0/T1 回归；本地 agent_server 实测无营销话术、≤2 句、回退 jarvis）
T3 回答后过滤：已完成，Gate T3 全绿（29 passed；banned 拦截/超句截断/事实性表述不误杀）
T4 总验收：已通过（经 0006 清障转绿：HUD 冻结哈希重冻结 f336fd77、队列读取容缺；全量 731 passed + 120 subtests / 0 failed，修复前 2 failed 清零）；2026-10-30 冻结 commit 12330ea + tag wo-ultimaagent-20261030-0003-frozen-20261030；清障证据 docs/reports/stage-0003-t4-clear-20261030.md + evidence/t4-clear/
```

---

## 4. 验收要点

- [ ] 范围冻结内逐项完成（无越界：未动 W6 UI/云端 ASR/参数基线/TTS 克隆/第三方库）
- [ ] 每 T 验收清单全绿 + 自证完整
- [ ] 关联文档同步（voice-profile 结构写入 docs/specs；人设调研结论回填 jarvis.md）
- [ ] 阶段报告产出 → 主脑复核 → 冻结 tag（`wo-ultimaagent-20261030-0003-frozen-<date>`）
