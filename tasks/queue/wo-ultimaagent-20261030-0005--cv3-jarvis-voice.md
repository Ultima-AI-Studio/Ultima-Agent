# Codex 工单 · UltimaAgent｜功能｜CV3 贾维斯音色（voice 段 + TTS 本地优先通道）

> 版本：v1.1 ｜ 状态：已冻结（2026-10-30，主脑复核通过，tag `wo-ultimaagent-20261030-0005-frozen-20261030`）｜ 适用工具：Codex（`codex exec`，`-m gpt-5.6-sol`）
> 用法：按 T0→T4 顺序逐条执行，Gate 全绿才过，再进下一条。
> 范围依据：`H:\UltimaAI\INDEX.md` + `H:\UltimaAI\_shared\paradigms\UltimaAI-任务工作流范式.md` + `docs/INDEX.md`
> 调研依据：10-30 CV3 贾维斯音色实测（`data/voice/jarvis-ref/`：参考音频 `jarvis_voice_ref_pcm16.wav` 7.93s/24k/单声道，CV3 冷启动合成英文 5.0s 转写可懂、中文 10.4s 正常发声；链路资源全绿）
> 北极星：**贾维斯**（语音链路向"贾维斯音色本地可用"靠拢；隐私红线：语音不出本机，云端仅调研不作主链路）
> 登记：2026-10-30 ｜ 原单 ID：wo-ultimaagent-20261030-0005 ｜ 类型：功能

---

## 0. 范围冻结

**本阶段只做（CV3 贾维斯音色接入 voice-profile + TTS 本地优先）**：

1. **voice-profile 增加 `voice` 段**：`config/voice-profile.json`（及 `src/brain/voice/voice_profile.py` 的 DEFAULT_PROFILE / `_L2_FIELDS` / `validate_profile` / `load_profile`）新增：
   - `voice.engine`：默认 `cv3`（本地 CosyVoice3 零样本克隆）；
   - `voice.ref_audio`：默认 `data/voice/jarvis-ref/jarvis_voice_ref_pcm16.wav`（L1 内置贾维斯音色参考，已实测可用）；L2 可覆盖为任意干净单人参考音频；缺失/损坏回退内置默认；
   - `voice.prompt_text`：默认 `null`（用 CosyVoice 内置 prompt_text）；L2 可覆盖；
2. **tts.py PROMPT_WAV 动态装载**：`PROMPT_WAV` 不再写死 `COSYVOICE_SOURCE/asset/zero_shot_prompt.wav`，改为合成时从 `load_profile()` 的 `voice.ref_audio` 解析；`daemon.py` 引用的 `PROMPT_WAV`（`from src.brain.voice.tts import PROMPT_WAV`）同源生效（改 tts.py 一处即同步 daemon 通道）；参考音频缺失时回退 CosyVoice 自带默认（链路永不因音色文件缺失而断）；
3. **TTS 本地优先通道**：`_synthesize_once` 优先级链从「edge-tts（联网）→ Piper → Melo → daemon → 冷启动 CV3」调整为「daemon(CV3) → 冷启动 CV3 → Piper → Melo → edge-tts（显式降级兜底，可经 profile 禁用）」，符合隐私红线（语音不出本机）；Piper/Melo 保留作为 CV3 不可用时的本地降级；
4. 配套单元测试 + 全量回归通过。

**本阶段不做**：不做 SFT 训练/微调（零样本克隆已满足）；不换模型版本（CV3 冻结）；不接云端调优（隐私红线）；不做 W6 语音管理 UI（后续接）；不改 KWS/ASR 参数基线数值；不引入第三方配置库（仅标准库 json/pathlib）；不改 ASR 通道。

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `config/voice-profile.json`（修改）+ `src/brain/voice/voice_profile.py`（修改） | voice 段装载单测全绿：默认 ref_audio 存在、L2 覆盖生效、缺失回退内置、L3 优先 |
| T1 | `src/brain/voice/tts.py`（修改）+ `src/brain/voice/daemon.py`（核对同步） | PROMPT_WAV 动态解析实测：profile.ref_audio 生效、缺失回退内置、daemon 通道同源 |
| T2 | `src/brain/voice/tts.py`（修改：`_synthesize_once` 优先链） | 本地优先实测：CV3 不可用时 Piper/Melo 降级；edge-tts 降级兜底可禁用 |
| T3 | `src/brain/tests/test_voice_voice.py`（新增测试） | 单测全绿：装载/回退/优先链/禁用 edge |
| T4 | 总验收 | 端到端实测（真机合成中英样本）+ 全量回归 + 证据落盘 |

---

## 2. 任务明细（每条 T 严格三段式）

### T0 · voice-profile 增加 voice 段

**文件**：
- `H:\UltimaAI\UltimaAgent\config\voice-profile.json`（修改，追加 voice 段；若当前文件无此段）
- `H:\UltimaAI\UltimaAgent\src\brain\voice\voice_profile.py`（修改：DEFAULT_PROFILE / `_L2_FIELDS` / `validate_profile`）

**写什么**：
1. `DEFAULT_PROFILE` 增加：
   ```json
   "voice": {
     "engine": "cv3",
     "ref_audio": "data/voice/jarvis-ref/jarvis_voice_ref_pcm16.wav",
     "prompt_text": null
   }
   ```
2. `_L2_FIELDS["voice"] = {"engine", "ref_audio", "prompt_text"}`；
3. `validate_profile` 校验：`engine` 合法值 `{"cv3","edge"}`（默认 cv3）；`ref_audio` 非空 str（可为相对 ROOT 路径或绝对路径），文件不存在 → 回退内置默认（记 warning 不炸）；`prompt_text` 可为 null 或非空 str；
4. `load_profile` 返回的 profile 必须含 voice 段（L3→L2→L1 回退语义与其他段一致）。

**验收（Gate T0）**：
- [ ] 单测 ≥5：默认 voice 段存在且 ref_audio 指向真实文件；L2 engine/ref_audio 覆盖生效；ref_audio 缺失回退内置；L3 覆盖 L2；损坏 JSON 回退内置；
- [ ] `H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -c "from src.brain.voice.voice_profile import load_profile; p=load_profile(); print(p['voice'])"` 输出含 engine=cv3 与默认 ref_audio。

**禁止**：不引入第三方库；不改 voice-profile.json 现有 persona/wakeword/style/input 段内容；不硬编码新绝对路径（ref_audio 用相对 ROOT 或从 profile 读）。

---

### T1 · tts.py PROMPT_WAV 动态装载（daemon 同源）

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\voice\tts.py`（修改）
- `H:\UltimaAI\UltimaAgent\src\brain\voice\daemon.py`（核对，不需改则记录）

**写什么**：
1. `PROMPT_WAV` 从模块级常量改为函数/解析逻辑：新增 `resolve_prompt_wav(profile=None) -> Path`——优先 `load_profile()["voice"]["ref_audio"]`（相对路径按 ROOT 解析），文件存在则返回；否则回退 `COSYVOICE_SOURCE / "asset" / "zero_shot_prompt.wav"`；
2. `_render_script()` / `tts_probe()` 中的 `{prompt_wav}` 渲染改用 `resolve_prompt_wav()` 结果；
3. `daemon.py` 的 `_tts_daemon()` 中 `from src.brain.voice.tts import PROMPT_WAV` 改为 `resolve_prompt_wav`（保持同源），脚本渲染一致；
4. 合成路径不改（`inference_zero_shot(text, prompt_text, prompt_wav)` 调用不变，只换 prompt_wav 来源）；`prompt_text` 同样从 `profile["voice"]["prompt_text"]` 读取，null 时用现写死值。

**验收（Gate T1）**：
- [ ] 单测 ≥4：默认 profile → resolve 返回贾维斯参考音频；profile.ref_audio 指向不存在文件 → 回退内置；绝对路径 ref_audio 生效；prompt_text null/覆盖两态正确；
- [ ] 实测：用 T0 后 profile 跑 `tts_synthesize`（或复用 `data/voice/jarvis-ref/cv3_jarvis_probe.py` 思路），确认合成音频音色参考来自贾维斯样本（时长/RMS 正常、非静音）。

**禁止**：不删除 CosyVoice 内置 prompt_wav 回退路径；不改变 `inference_zero_shot` 参数结构；不引入新依赖。

---

### T2 · TTS 本地优先通道（隐私红线）

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\voice\tts.py`（修改：`_synthesize_once` 优先级链）

**写什么**：
1. `_synthesize_once` 优先级链改为：
   1. daemon（CV3 常驻，模型热缓存）→ 2. 冷启动 CV3 → 3. Piper → 4. Melo → 5. edge-tts（联网兜底，仅当 `profile["voice"]["engine"] != "cv3"` 或显式允许时启用；`engine=cv3` 且本地链路可用时跳过 edge）；
2. `engine=cv3` 且 CV3 资源不可用（`all_cv3_resources_ready()` False）→ 走 Piper/Melo 本地降级，不抛错；
3. edge-tts 保留实现但不作首选；提供开关（`voice.engine` 或新增 `allow_edge` 布尔，默认 False）；
4. 合成前统一 `resolve_prompt_wav()` 取值（与 T1 一致）。

**验收（Gate T2）**：
- [ ] 单测 ≥3：engine=cv3 且 CV3 就绪 → 不调 edge（mock 断言）；CV3 不可用 → Piper/Melo；engine=edge 显式 → 允许 edge；
- [ ] 实测（专用解释器）：真机合成一句话，结果 dict 的 `engine` 字段为 cv3/piper/melo 之一（本地），非 edge。

**禁止**：不删除 edge-tts 代码（可禁用不可删，保留用户显式启用能力）；不改变 Piper/Melo 实现；不把云端通道设为首选。

---

### T3 · 单元测试

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\tests\test_voice_voice.py`（新增）

**写什么**：
覆盖 T0-T2 全部验收点：voice 段装载/回退/L2/L3、resolve_prompt_wav 三态、优先链 mock 断言、edge 禁用开关、daemon 同源（resolve 一致）。测试不真实调 CV3 推理（重型），用 mock/临时 profile 文件验证逻辑。

**验收（Gate T3）**：
- [ ] `H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest src/brain/tests/test_voice_voice.py -q --disable-warnings` 全绿（≥8 passed）。

**禁止**：不真实加载 CV3 模型（测试时长控制）；不改动其他测试文件。

---

### T4 · 总验收

**文件**：本工单（更新状态）+ `docs/reports/` 阶段报告 + 证据目录

**写什么**：
1. 全量单测回归：`H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest src -q --disable-warnings`（**Agent 专用解释器，禁止用系统 Python**）→ 全绿 + 无新增失败（0003 已登记 2 个范围外既有失败不在本工单修复范围，如实声明）；
2. 端到端实测：真机合成中文句（"先生，有什么可以为您效劳？"）与英文句（"At your service, sir."）各一段 → 均非近静音、时长正常、result 含 engine 字段（cv3）；转写验证中文可懂（允许英音口音）；
3. 阶段报告 `docs/reports/stage-cv3-jarvis-voice-20261030.md`：Gate 逐条核对（T0-C1~C5/T1-C1~C4/T2-C1~C3/T3≥8/T4 全量），证据路径、越界声明（未动：SFT/模型版本/云端调优/W6 UI/KWS 基线/ASR 通道）；
4. 证据落盘 `docs/reports/evidence/cv3-jarvis-voice/`：单测输出、合成样本 wav（或路径引用 `data/voice/jarvis-ref/`）、转写输出、回归全量输出；
5. 回执 8 字段按 Codex 范式 §5 输出。

**验收（Gate T4）**：总验收清单全绿；阶段报告存在且逐项勾选；回执 8 字段齐全；越界声明如实。

---

## 3. 给编码代理的任务粘贴模板

```
T0 voice 段入 profile：已完成；6 项 Gate 测试由 RED→GREEN，默认读回为 cv3 + 指定 Jarvis ref + prompt_text null
T1 PROMPT_WAV 动态装载：已完成；动态 ref/prompt、缺失回退、daemon/cold 同源；T4 补齐内置 Jarvis 音频/文字稿配对回归
T2 本地优先链：已完成；daemon→cold CV3→Piper→Melo→显式 edge，默认 cv3 禁用 edge；真机 engine=cv3
T3 单测：已完成；专用解释器 37 passed（要求 ≥8）
T4 总验收：已完成；真机本地 CV3 中英样本与离线转写通过；全量 XML 906/906、0 failures、0 errors；fresh-context 终审 4 个 Important 已一次有界修复；证据见阶段报告
```

---

## 4. 验收要点

- [x] 范围冻结内逐项完成（无越界：未动 SFT/模型版本/云端调优/W6 UI/KWS 基线/ASR 通道）
- [x] 每 T 验收清单全绿 + 自证完整
- [x] 关联文档同步（voice 段写入 docs/specs；音色实测结论回填）
- [x] 阶段报告产出 → 主脑复核 → 冻结 tag（`wo-ultimaagent-20261030-0005-frozen-20261030`）

---

## 5. 冻结回填（主脑，2026-10-30）

- 执行端：Codex 三派（PID 21828，run_dir `20261030T141936364043Z`；首派 11764 网络失败留证、二派 26236 T4 收尾 OOM 留证）
- final-message：正常产出，T0→T4 全闭合，状态"技术执行完成"（未冒充冻结）
- 主脑复核：906 tests / 0 failures / 0 errors / 0 skipped（195.007s）；真机 CV3 daemon/CUDA 中英合成非近静音、离线转写逐字命中（zh 0.935059 / en 0.970703）；4 个 Important 一次有界修复 RED→GREEN（专项 37 passed）；越界声明无；变更范围仅工单声明路径
- 冻结：commit + tag `wo-ultimaagent-20261030-0005-frozen-20261030`；全局主表/本地 queue/index 三处登记 0005=frozen
