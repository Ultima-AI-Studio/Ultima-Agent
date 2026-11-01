# 工单 wo-ultimaagent-20261101-0018 ｜ UltimaAgent ｜ 工程 ｜ 语音链路开源对照修复（TTS 拼接 / 路由宽进 / 幂幂变体 / 动态换词 / ASR 升级）

> 原单 ID：`wo-ultimaagent-20261101-0018` ｜ 显示标题：UltimaAgent｜工程｜KWS+ASR+TTS 开源对照修复
> 依据：G-DISPATCH-001 自主推进版 + G-TASKFLOW-001 + G-PLAN-001（先方案后工单）
> 方案：`docs/reports/voice-stack-opensource-plan-20261101.md`（2026-11-01 定稿，Owner 拍板"推荐改一版，直接派工单"）
> 北极星：贾维斯（自然人机交互：一次唤醒、开口即答、回答完整准确）
> 基线收口：commit `8774f3c`（0014-0017 交付 + 云脑 + 时格式 + TTS 防护）
> 创建：2026-11-01 ｜ 状态：待派发

---

## 一、目标与范围

### 1.1 目标（Result）

按开源官方实现对照，修复真机三要点验收暴露的三个链路问题：

1. **TTS 漏句根治**：官方 `inference_zero_shot` 逐句 yield 多段，我们 `break` 只取第一段 → 改为收集全部段拼接，时间句式与长句合成完整。
2. **路由门宽进**：ABSTAIN（低相似度不确定）不再挡用户提问，放行给云脑/本地模型；只有 DENY（明确命中违禁/越界）才拒绝。
3. **唤醒成功率**："幂幂"补齐发音变体 + 逐词 boosting_score；换词链路统一到官方机制，消除双实现漂移。
4. **ASR 升级**：SenseVoice 升级 2025-09-09 int8 版 + 开启 ITN（数字/日期规范化），旧模型保留可回滚。

### 1.2 范围冻结（边界，禁止越界）

- **只做**：§1.3 写域表内文件的修改、对应测试、证据与阶段报告。
- **禁止修改**：
  - KWS 模型/onnx 本体、tokens.txt（只改 keywords 文本，且走 `scripts/kws_reconfig.py` 或官方校验，不手改模型文件）；
  - KWS 冻结基线数值（`docs/specs/kws-wakeup-params-baseline.md`：threshold 0.08 / num_trailing_blanks 8 / max_active_paths 8 / VAD 0.5s / 门控 0.4s 等）——**只可追加变更记录，不得改值**；
  - 感知层音频采集/增益/重采样链路（已收口，本单不碰）；
  - 本地 8B 主脑模型权重与 ollama 配置（模型层不动，只动编排）；
  - W6/HUD/四角壳 UI 布局与产品功能（搜→整理→右侧弹窗为独立工作项，本单不做）；
  - 不引入新的重型框架、不替换整体架构（只借鉴官方调用方式，不换控制器）。
- **已知漂移需申报**：`src/brain/voice/kws_listener.py` L60 `keywords_score=1.0` 与基线文档 score=2.0 不一致——T0 盘点核对后，在 T4 统一并在基线文档追加变更记录，不得静默改值。

### 1.3 写域

| 文件 | 动作 | 说明 |
|---|---|---|
| `src/brain/voice/tts.py` | 修改 | T1：去 `break`，收集全部 yield 段 `torch.cat(dim=1)`，保留峰值归一化 |
| `src/brain/routing/intent_gate.py` | 修改 | T2：ABSTAIN 语义改为"放行不确定"，决策出口区分 DENY/ABSTAIN |
| `src/brain/interaction.py` | 修改 | T2：`_route_before_agent` 中 ABSTAIN → return None 放行；DENY 才返回拒绝 |
| `models/sherpa/kws/keywords.txt` | 经工具写 | T3：幂幂变体 + 逐词 score（走 kws_reconfig / 官方校验，不手改） |
| `scripts/kws_reconfig.py` | 只读/按需扩展 | T3：确认能否写拼音变体与逐词 score；如需扩展先申报 |
| `src/brain/voice/kws_listener.py` | 修改 | T4：统一换词/热重载链路，评估官方 create_stream 动态机制；修 score 漂移 |
| `config/voice-profile.json` | 运行期写回 | T3：wakeword 变体/参数同步 |
| `src/brain/voice/asr.py` | 修改 | T5：新模型路径 + use_itn=1，旧模型保留回滚 |
| `models/sherpa/`（新模型目录） | 新建 | T5：下载 sense-voice int8 2025-09-09 |
| 测试文件 | 新建/修改 | 各 T 对应单测与回归 |
| `docs/reports/stage-voice-stack-fix-20261101.md` + evidence/ | 新建 | 阶段报告与证据 |
| `docs/specs/kws-wakeup-params-baseline.md` | 追加记录 | 仅追加变更记录（score 漂移/变体），不改冻结值 |

---

## 二、DoR 就绪门

| # | 就绪项 | 判定 | 证据 |
|---|---|---|---|
| 1 | 验收 Gate 可判定 | ✅ 封闭清单（§四） | 完整性/宽进/唤醒/ASR/回归 |
| 2 | 无未决依赖 | ✅ 基线已收口 commit 8774f3c | git log 可查 |
| 3 | 写入域已声明 | ✅ §1.3 | — |
| 4 | 推理强度已声明 | ✅ T0 medium / T1-T6 medium / T7 high / T8 low | — |
| 5 | 禁止项已写 | ✅ §1.2 | — |

---

## 三、执行步骤（T0→T8，逐 T Gate PASS 再进下一条）

### T0 环境盘点（medium）
- [ ] C1 读 `src/brain/voice/tts.py` 全文，定位 `_INLINE_SCRIPT` 中 `for block in cosy.inference_zero_shot(...): speech = block["tts_speech"]; break` 行号与后续峰值归一化逻辑，确认 tts_speech 张量时间轴维度。
- [ ] C2 读 `src/brain/routing/intent_gate.py`（RoutingConfig / route / 决策类型 ALLOW/DENY/ABSTAIN）与 `interaction.py` 的 `_route_before_agent`，确认 ABSTAIN 当前直接返回"我没听清"的接线点。
- [ ] C3 读 `src/brain/voice/kws_listener.py`（create_stream / reload_keywords / L60 keywords_score）与 `scripts/kws_reconfig.py`（四子命令、score/threshold 参数、能否写拼音变体），核对 `keywords.txt` 现状。
- [ ] C4 读 `src/brain/voice/asr.py`（_load_sherpa_asr / _run_sherpa / OfflineRecognizer 配置），确认当前 use_itn 参数与模型路径写法。
- [ ] C5 漂移核对：kws_listener keywords_score=1.0 vs 基线文档 2.0，记录差异并给出统一建议（申报，不静默改）。
- [ ] C6 证据落盘 `docs/reports/evidence/voice-stack-fix/t0-env-probe.txt`。
- Gate：C1-C6 全绿 → T1。

### T1 TTS 分句拼接修复（medium）
- [ ] C1 改 `tts.py`：移除只取第一段的 `break`，循环收集 `inference_zero_shot` 全部 yield block 的 `tts_speech`，用 `torch.cat(segments, dim=1)` 沿时间轴拼接（空结果/单段兜底保持原行为）。
- [ ] C2 保留原峰值归一化逻辑（L127-133），对拼接后的完整张量统一归一化，不改变输出采样率（24k）与 wav 封装。
- [ ] C3 单测：mock 多段 yield（≥2 段）→ 断言输出为拼接结果、时长=各段之和、无段丢失；单段/空输入兜底断言。
- [ ] C4 离线合成验证：时间句式"现在是下午四点二十四分，星期日。"合成音频时长 ≥4.8s（此前漏句仅 1.2-2.3s），保存证据 wav。
- Gate：C1-C4 全绿，证据 `t1-tts.txt` + wav → T2。

### T2 路由门宽进（medium）
- [ ] C1 改 `intent_gate.py`：保留 DENY（明确命中违禁/越界规则）拒绝语义；ABSTAIN（low_similarity/不确定）语义改为"不阻断、放行下游"，决策对象携带可区分标记。
- [ ] C2 改 `interaction.py` `_route_before_agent`：ALLOW → return None 放行；**ABSTAIN → return None 放行**（进入后续云脑/本地模型链路）；仅 DENY → 返回拒绝话术。
- [ ] C3 确认放行后链路顺序不变（时间/天气/云脑 5.8/本地 8B），云脑异常仍静默降级本地。
- [ ] C4 单测：注入"今天有什么新闻？"（此前 low_similarity 0.336 被挡）→ 断言不再返回"我没听清"、进入下游；DENY 类输入仍被拒；ALLOW 类回归不变。
- Gate：C1-C4 全绿，证据 `t2-route.txt` → T3。

### T3 幂幂变体 + 逐词 score（medium）
- [ ] C1 用官方机制校验候选音素变体（`m ì m ì` 基线 + `m í m i` / `m í m ì` / `m ì m i` / `m í m`），经 sherpa-onnx text2token/CLI 校验合法后再写入，**禁止凭猜测写音素**。
- [ ] C2 逐词参数：基线行与变体按方案加 `:boosting_score`（常用 2.5，短变体 `m í m` 3.0），写入走 `kws_reconfig.py`；若其不支持拼音变体/逐词 score，先申报扩展点再改。
- [ ] C3 同步 `config/voice-profile.json` wakeword 段（custom=幂幂、变体/score 记录），`keywords.txt` 与 profile 对齐，双源一致。
- [ ] C4 基线文档 `kws-wakeup-params-baseline.md` 追加变体与 score 变更记录（只追加，不改冻结参数）。
- [ ] C5 单测：多发音变体离线 KWS 断言可命中；keywords/profile 一致性断言；回归 6 贾维斯变体与 ULTIMA 行不受影响。
- Gate：C1-C5 全绿，证据 `t3-keywords.txt` → T4。

### T4 换词链路统一 + 动态机制（medium）
- [ ] C1 对照官方 `python-api-examples/keyword-spotter.py`：`create_stream("... @词面")` 支持 per-stream 关键词（'/' 分隔多词），评估在 kws_listener 换词/热重载中的适用性（持续 stream 不可中途改词，动态词用于新建 stream）。
- [ ] C2 统一换词路径：消除 kws_listener 与 daemon 双实现分叉，热重载保留同 PID（不杀守护进程），给出唯一调用链并落盘说明。
- [ ] C3 处理 T0-C5 申报的 score 漂移：按基线统一 keywords_score（如确认应为 2.0 则修正并在基线文档记录变更原因），不得静默改。
- [ ] C4 单测：模拟换词 → 新 stream/spotter 命中新词、旧词失效、PID 不变；失败回滚路径断言。
- Gate：C1-C4 全绿，证据 `t4-reload.txt` → T5。

### T5 ASR 升级 + ITN（medium）
- [ ] C1 下载 `sherpa-onnx-sense-voice-zh-en-ja-ko-yue-int8-2025-09-09` 到 `models/sherpa/`（优先 ModelScope 镜像，次 HuggingFace；记录下载来源与校验文件完整性）。
- [ ] C2 改 `asr.py`：新模型路径 + 开启 `use_itn=1`（以安装版 sherpa-onnx 真实参数名为准，先验证参数存在），旧 2024-07-17 模型保留、配置可一键回滚。
- [ ] C3 离线识别验证：数字/日期句式（如"二零二六年十一月一日三点五十二分"）ITN 输出规范；与旧模型同音频对比，CER 不劣化。
- [ ] C4 单测：ITN 断言、模型加载/回滚断言、VAD 精切链路回归。
- Gate：C1-C4 全绿，证据 `t5-asr.txt` → T6。

### T6 全量自动化验证（medium）
- [ ] C1 全量回归：`tools/venv-openjarvis/Scripts/python.exe -m pytest src -q` 全绿（工程验收必须用 venv-openjarvis，禁止默认 Python312）。
- [ ] C2 语音专项：tts / routing / kws / asr / voice-profile 相关测试全绿。
- [ ] C3 真机离线闭环断言：唤醒（多变体）→ 提问（含新闻类开放问题）→ 完整合成回答，逐环节证据落盘。
- [ ] C4 记录实际数据：合成时长、ASR 转写逐字命中、路由决策类型，不填预期值。
- Gate：C1-C4 全绿，证据 `t6-regression.txt` → T7。

### T7 收口（high）
- [ ] C1 冻结基线核对：`kws-wakeup-params-baseline.md` 冻结值零变动（仅追加记录）；保护对象（KWS 模型/感知层/8B 权重）零改动核对。
- [ ] C2 git：`git add` 仅本单写域文件（**禁止 -A/-u**），commit 标注「工单 0018 语音链路开源对照修复」；tag `ultimaagent-voice-stack-fix-20261101`，`git rev-parse` 可解析。
- [ ] C3 免代理推送：`git -c http.proxy= -c https.proxy= -c http.https://github.com.proxy= push` + `push --tags`；失败如实留证，不伪造。
- [ ] C4 阶段报告 `docs/reports/stage-voice-stack-fix-20261101.md`：各 T Gate 证据 + 测试摘要 + 真机离线结果 + 越界/漂移处理记录。
- Gate：C1-C4 全绿 → T8。

### T8 回执（low）
八字段（见 §五）。

---

## 四、验收口径（封闭清单，全绿才过）

| Gate | 判定 | 证据位置 |
|---|---|---|
| TTS 完整性 | 时间句式/多段句合成完整，时长 ≥4.8s，ASR 转写逐字命中，无漏段 | t1 + wav |
| 路由宽进 | 新闻类开放问题不再被"我没听清"挡、进入下游；DENY 仍拒绝；ALLOW 回归 | t2 |
| 唤醒成功率 | 幂幂多发音变体离线均可命中；贾维斯/ULTIMA 行不受影响；keywords/profile 一致 | t3 |
| 换词统一 | 唯一换词链路、热重载同 PID、score 漂移按基线处理并记录 | t4 |
| ASR 升级 | 新 int8 模型加载、ITN 数字/日期规范、CER 不劣化、旧模型可回滚 | t5 |
| 回归 | venv-openjarvis 全量 pytest 绿 + 语音专项绿 | t6 |
| 冻结 | tag `ultimaagent-voice-stack-fix-20261101` 存在可解析、推送留证 | t7 |

---

## 五、执行端回执（八字段，必填）

| 字段 | 值 |
|---|---|
| 链路号/工单号 | wo-ultimaagent-20261101-0018 |
| 执行端 | Codex（gpt-5.6-sol，codex exec，danger-full-access） |
| 完成状态 | 已完成 / 阻塞 / 已终止（三选一） |
| 根因结论 | （一句话：TTS 调用方式 / 路由编排 / 变体不足 / ASR 版本） |
| 产出路径 | tts.py、intent_gate.py、interaction.py、kws_listener.py、asr.py、keywords、测试、stage 报告、evidence/ |
| 验收证据 | T0-C1~C6 / T1-T6 逐条 PASS + pytest 摘要 + 真机离线断言 |
| 越界声明 | 无=明确写"无"；含未动范围（KWS 模型/冻结参数/感知层/8B 权重/UI 产品功能） |
| 环境声明 | 真机离线实测项与仅离线预期项分开写；真机三要点待 Owner 现场验收须注明 |

## 附：推理强度
T0 medium ｜ T1 medium ｜ T2 medium ｜ T3 medium ｜ T4 medium ｜ T5 medium ｜ T6 medium ｜ T7 high ｜ T8 low
