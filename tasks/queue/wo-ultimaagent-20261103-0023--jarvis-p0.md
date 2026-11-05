# UltimaAgent｜架构·安全｜Jarvis 2.0 P0 三项落地

- **task_id**: wo-ultimaagent-20261103-0023
- **stage**: v0.5 配套（安全与语音加固；P0 三项最小改造版）
- original_work_order_id: wo-ultimaagent-20261103-0023
- revision: 1
- authorization: 用户 2026-11-03 确认"把 Jarvis 2.0 这三项能力做个工单加进去"（P0 三项，P1 不进本单）
- 状态：**ACCEPT WITH EXEMPTIONS（2026-11-05 主脑豁免裁决收口）**——首轮 PID 13684（BLOCKED/REVISE）→修复轮 PID 21280（2026-11-04 22:13→22:42）已完成；T0-T3 GREEN（KWS 已回正 2.0/8）；T4 全树 979/2/120，2 项失败=环境既有豁免（裁决 `data/evidence/jarvis-p0/T4/main-brain-exemption-ruling.json`）；Owner 真实体验=延期验收项（deferred）；冻结 tag=`ultimaagent-jarvis-p0-20261103`
- 计划：docs/plans/jarvis-open-source-refactor-plan-20261101.md（本单随方案落盘，P0 三项口径见 §3）
- 契约：本工单卡即契约；规划文档 §3/§5/§7/§8 为权威口径
- 草案检查点：无（本单方案由执行端分析细化，P0 口径已确认）

## goal

按规划文档 §3 落地 Jarvis 2.0 系 P0 三项最小改造版（MIT 逻辑层借鉴，Windows 等价实现）：
P0-1 Prompt 注入边界与四层优先级规则；P0-2 记忆写入 PoisonGuard；P0-3 语音链路 Windows 化（唤醒词模糊匹配 + 识别会话重启对策 + 转写后端可插拔，本地优先）。P1 四模块不在本单范围。技术方案由执行端（Codex）自行分析细化后按 G-TASKFLOW-001 执行。

## acceptance[]

- ACCEPT: P0-1 注入边界生效——5 组对抗用例（含注入指令、混淆编码）全部不越权；全大写指令与密钥样本不进上下文；语音内容保留比例 100%（不做任何补写）。
- ACCEPT: P0-2 PoisonGuard 生效——注入短语（多语词表）、密钥模式（sk-/sk-ant-/AIza/bearer/银行卡/SSN）、全大写指令三类样本 100% 拦截；正常会话记录 0 误杀（抽样 100 条复核）。
- ACCEPT: P0-3 语音链路 Windows 化——离线唤醒 + 本地转写（sherpa-onnx 优先）全链路可用；唤醒误触发率与 KWS 基线口径对比不劣化；切换转写后端不改上层代码；50s 会话重启对策落地。
- ACCEPT: 源码头加来源注释与 MIT 许可声明（jarvis-ai-assistant / DockWright），无 AGPL 内嵌。
- ACCEPT: 独立审计 + Owner 真实体验 + 冻结 tag + 产出与回滚说明全部齐备后才关闭本单。

## dependsOn[]

- 0017 约束栈（已冻结，白名单外拦截）
- KWS 语音参数基线（specs/kws-wakeup-params-baseline.md，唯一权威，改动前必读）
- 既有语音链路（KWS→ASR→8B→工具→TTS，v1 冻结中）

## fileDomain[]

- `H:/UltimaAI/UltimaAgent/src/brain`（prompt 处理侧）
- `H:/UltimaAI/UltimaAgent/src/voice` 或语音链路既有落位（转写抽象/唤醒容错）
- `H:/UltimaAI/UltimaAgent/src/memory` 或记忆写入既有落位（PoisonGuard）
- `H:/UltimaAI/UltimaAgent/docs`
- `H:/UltimaAI/UltimaAgent/tasks/queue/wo-ultimaagent-20261103-0023--jarvis-p0.md`
- `H:/UltimaAI/UltimaAgent/tasks/queue/runs/wo-ultimaagent-20261103-0023`
- `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-p0`

## priority

- 85

## reasoningEffort

- high

## category + skill

- 架构·安全 / 集成；executing-plans、test-driven-development、verification-before-completion；方案分析 + 分阶段执行。

## receipt

- data/evidence/jarvis-p0/ 各阶段记录原单/阶段/run_id、输入哈希、执行端、真实退出、证据、越界声明和开源选择。

## retryCount

- 0；审计 REVISE 最多两轮，继承本单失败历史和修订，不新建原单重置额度。

## 写什么与禁止

1. 先分析细化技术方案（读规划文档 §3/§5/§7/§8），分阶段执行；M1（P0-1/P0-2 纯逻辑层，可并行）→ M2（P0-3 语音链路 Windows 化）。
2. 规则/算法逐行借鉴 MIT 源码（jarvis-ai-assistant prompts.ts / DockWright MemoryPoisonGuard.swift / WakeWordDetector.swift），改写为 Ultima 术语并加来源注释与 MIT 许可声明；AGPL（neuromcp 引擎）不内嵌。
3. 语音链路改动前必须先读 specs/kws-wakeup-params-baseline.md；已冻结语音参数不得来回突变，验收以 KWS 基线口径回归对比。
4. 禁止改主脑模型与推理参数；禁止改生产默认；禁止重启现有语音进程；禁止改 0016/0017 已冻结语义。
5. 禁止安装未列入计划的依赖、增加后台感知/主动提醒、跳过前序验收、伪造完成或冻结。P1 四模块、neuromcp 工具脚本不在本单范围。

## 开源替代排查

| 子功能 | 现成件 | 采用与理由 |
|---|---|---|
| Prompt 分层规则 | jarvis-ai-assistant src/prompts/prompts.ts（MIT，bec50ef6） | 采用；逐行可抄，改写 Ultima 术语 |
| 记忆写入过滤 | DockWright Core/Memory/MemoryPoisonGuard.swift（MIT） | 采用；Python 等价实现落地 |
| 唤醒词容错 | DockWright WakeWordDetector.swift（MIT，Levenshtein） | 采用；阈值 <0.35 口径 |
| 转写后端抽象 | jarvis src/transcription 6 类后端目录（MIT） | 采用；本地 sherpa-onnx 优先 + 云端可插拔 |
| 识别会话重启 | Apple 60s 上限等价工程对策 | Windows 侧按音频会话超时处理 50s 重启 |
| 平台 API | Win32 键盘钩子 / WASAPI / UIAutomation | 平台映射表先行，小步验证 |

## 2026-11-03 建卡补记

- 用户 2026-11-03 明确"把 Jarvis 2.0 这三项能力做个工单加进去"→ P0 三项建卡 0023；P1 四模块不进入本单（待 P0 验收后再议）。
- 未决事项已按规划文档口径默认：语音后端=sherpa-onnx 本地优先；记忆自愈调度不属 P0-2 范围；neuromcp 不进本单。
- 当前 0022（中间层 v1）执行中，WIP 一单一进程 → 本单登记 pending，待 0022 收尾后派发。
- 18766 UltimaManager 服务离线，登记走全局主表，待服务恢复后由主脑补登接口。

## 2026-11-04 主脑裁决（REVISE 修复授权）

- **首轮终态**：run 20261104T060115840819Z（PID 13684）返回 BLOCKED/REVISE，未 commit/tag/push（HEAD 仍 34ac0c79）。两轮独立审计额度已用完；第二轮=Critical remediation PASS / overall REVISE。
- **主脑实测核验**（全部属实）：
  1. T3 绑定缺口：kws_listener.py `score=1.0/trailing=0` vs 权威基线 `2.0/8`=历史漂移，非本单引入；运行中语音进程=voice-listen-daemon.py（已对齐 2.0/8），回正 kws_listener 不影响运行进程。
  2. T4 全树 1 failed = `test_preference_p2.py:52` 毫秒时间戳竞态=既有非本单（0025 a2/a3、0022 已记录，概率性），本单未弱化代码。
  3. Owner 真实体验缺失——用户 2026-11-04 确认"真实体验当前不可用"。
- **裁决**：授权有界修复轮（不再拉第三轮独立审计，修复后由主脑验收）。范围仅两项：
  1. kws_listener.py 回正权威基线 `keywords_score=2.0` / `num_trailing_blanks=8`（改前必读基线文档；注释引用基线；不改 threshold=0.08；不重启语音进程）。
  2. 全树 venv-openjarvis 重跑：test_preference_p2 竞态按既有豁免（不弱化代码、记录豁免证据）；失败项超出竞态则如实报告、不豁免。
- **Owner 真实体验=延期验收项（deferred）**：真机验证另行安排；冻结 tag 与阶段报告/回执明确标注遗留，不宣称完整 V1 冻结。
- **收口条件（主脑验收）**：修复轮全树绿（或仅竞态豁免）+ 本单写域 commit + tag `ultimaagent-jarvis-p0-20261103` + 免代理 push + T5 回执更新（标注体验遗留）。

## 2026-11-05 主脑豁免裁决（T4 环境既有失败，收口授权）

- **用户拍板**：2026-11-05 选择 **A｜按环境既有失败豁免收口**（备选 B「补 PATH + 真推理改走 8B 重跑」未采纳，避免改测试代码再拉一轮）。
- **修复轮结果**：run 20261104T141335097160Z（PID 21280，2026-11-04 22:13:35→22:42:30）已退出，run 4 件齐全。KWS 已实测回正（`score=2.0` / `num_trailing_blanks=8` / `threshold=0.08` 不变，含基线注释引用）；`T3/gate.json`=GREEN，语音测试组 8 passed。T4 全树 `tools/venv-openjarvis/Scripts/python.exe -m pytest src -q` exit=1：**979 passed / 2 failed / 120 subtests passed**。
- **两项 T4 失败复核定性（均环境既有，非本单代码）**：
  1. `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`：`FileNotFoundError [WinError 2]`——测试子进程 PATH 不含 Ollama 安装目录；执行端进程内修正 PATH 后 `ollama list` exit=0，但未落到 pytest 子进程。
  2. `TestC2Entry::test_jarvis_ask_real_inference`：`jarvis ask` exit 1，Ollama HTTP 500 / llama-server `cudaMalloc failed: out of memory`（KV cache 2,818,572,288 字节）。qwen2.5:14b（~9GB）+KV 2.82GB ≈ 11.8GB 需求 > 12GB 卡可用（诊断时 free 10,453 MiB；当前实测 free 9,116 MiB）。14B 按 2026-11-02 裁定仅留库、不作运行候选；backend 默认 `memory_llm_model=qwen2.5:14b` 为历史遗留。
- **首轮对照证据**：同两项在首轮 `T4/full-green3-junit.xml` 中均无 failure 标签（time=0.062 / 24.418，即 PASS）；本轮代码仅改 kws_listener 参数回正 + P0-3 接线，与两项连通性测试零交叉 → 环境差异/波动，非本单回归。
- **裁决**：T4 按「环境既有失败豁免」收口。执行端 BLOCKED 守门记录保留不改（`T4/gate.json`、T5 回执原判留痕）；主脑裁决另档 `data/evidence/jarvis-p0/T4/main-brain-exemption-ruling.json`。
- **环境债（另立专项单，不占本单额度）**：DEBT-ENV-01 测试环境注入 Ollama PATH（或测试内自备）；DEBT-ENV-02 真推理测试改 8B 或按显存容量前置跳过。
- **竞态项**：`test_preference_p2` 毫秒时间戳竞态本轮未触发，不属本次豁免范围。
- **收口执行**：本单写域 commit + tag `ultimaagent-jarvis-p0-20261103` + 免代理 push；全局主表 0023 置 frozen/done；北极星清单同步；0024 按 WIP 重派。
- **Owner 真实体验**：仍为 deferred；tag/阶段报告/T5 回执均标注该遗留，不宣称完整 V1 冻结。

