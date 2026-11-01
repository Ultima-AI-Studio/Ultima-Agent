# 能力 / 组件 / 技能注册表（Registry）

- **版本**：v2.9 · 2026-10-27
- **用途**：防重复开发（强制标准 M1：立项/开发前必查本表）；登记一切已有能力、组件与技能
- **登记规则**：新增能力/组件/技能必须先在此登记，未登记不得使用；删除/合并需审计确认并留痕
- **v1.1 变更（2026-10-16）**：登记「任务队列引擎」组件（codex-task-queue-spec v1.0）

## 一、技能注册（Skill Registry）

| 技能 ID | 角色 | 职责边界 | 适用任务类型 | 产出标准 | 验收口径 |
|---|---|---|---|---|---|
| `eng.code` | 智能工程师 | 写代码/修 bug/重构/单元自检 | code | 源码落 fileDomain | 编译通过+自检+回执 |
| `eng.ui` | UI 工程师 | 组件/界面/动效实现 | ui | 组件/页面按积木规格 | 视觉核对+交互可用 |
| `eng.audit` | 审计工程师 | 一致性/质量/回执核对/修正任务 | audit | 审计结论+修正任务 | 偏差全部闭环 |
| `eng.security` | 安全工程师 | 越界/权限/凭证/漏洞核查 | security | 安全报告+加固 | 高危项清零 |
| `eng.arch` | 架构工程师 | 分层/接口/选型/依赖 | arch | 架构方案+依赖图 | 评审通过+落规格 |
| `eng.database` | 数据库工程师 | 建模/存储/查询/迁移 | database | 模型+迁移脚本 | 数据校验通过 |
| `eng.test` | 测试工程师 | 验证/回归/验收证据 | test | 测试报告 | 验收项全过 |
| `eng.infra` | 运维工程师 | 部署/环境/守护/日志/设备集群 | infra | 部署/运行状态 | 服务可用 |
| `eng.voice` | 语音/多媒体 | 语音链路/音色/音频/CV3 接线 | voice | 链路验证+证据 | 真机验证报告 |
| `eng.docs` | 文档工程师 | 范式/规格/纪要/调研落盘 | docs | 文档落盘 | 回读一致+可追溯 |
| `eng.generic` | 通用执行器 | 兜底/无法判定任务 | generic | 按任务卡产出 | 按 acceptance |

## 二、能力注册（Capability Registry，L0–L10 骨架，逐步细化）

> 状态以 UA-ALIGNMENT-20261025 对齐调校报告为准（2026-10-25）：已实现层为真实代码 + 测试/真机证据；"部分"层为已建核心未上壳或缺子项。

| 层 | 能力 | 状态 | 落点（实际） |
|---|---|---|---|
| L0 | 语音入口/出口 + 文字入口/出口（终端四 IO） | 已实现（语音 CV3 真机闭环 P1；文字 cli 冻结） | src/brain/voice/ + src/brain/cli.py + src/host-shell/ |
| L1 | 意图理解（含隐含补全） | 已实现（窄规则引擎，INTENT_METRIC 16/16） | src/brain/intent.py |
| L2 | 领域知识与技能注册 | 已实现（任务域 11 技能驻留，白名单双模式） | src/brain/skills/ |
| L3 | 执行与外部接入（数据源/设备/多模型） | 已实现（队列只读源 + 环境快照） | src/brain/queue_source.py + src/brain/environment.py |
| L4 | 编排与组合窗口（scene-orchestrator + 组件树 DSL） | **已实现（转换/校验/离线渲染核心 + 壳常驻事件循环已接线 A2）** | src/window/ + src/host-shell/OrbLiveRenderer.cs + src/brain/display/host_pusher.py |
| L5 | 表达与总结（汇报范式三规则） | 已实现（结论先行/聚合/下钻） | src/brain/reporter.py |
| L6 | 输出呈现（渲染 + 语音汇报状态机） | 已实现（ORB 六态+emotionId+WebGL2 壳验收；TTS 汇报真机） | src/brain/display/ + src/host-shell/ |
| L7 | 交互循环（对话调整/征询/队列管理） | **已实现（单测 15/15 全绿，真实链路验证通过）** | src/brain/interaction.py（InteractionLoop：征询闭环/优先级调整/插队/异步三拍）；src/brain/cli.py（--loop 模式）；验收见 docs/reports/l7-interaction-acceptance-20261025.md |
| L8 | 行为约束与受控执行（安全/越界/凭证） | **已实现（越界拦截 CapabilityPolicy+NeMoScanner；凭证中心 DPAPI 加密+四层凭证层；高危征询 HazardGate；单测 24/24+M2 回归 19/19）** | src/brain/guardrails/（policy.py/scanner.py/credentials.py/hazard.py/registry.py）；验收见 reports/l8-credential-center-acceptance-20261025.md |
| L9 | 记忆与自学习（工作/声明式/程序式 + 反思） | 已实现（偏好最小记忆 Mem0+PreferenceStore；完整自学习后置） | src/brain/memory/ |
| L10 | 范式引擎（7 环流程/范式检查） | 已实现（LangGraphStateMachine 注册底座 RouterPolicyRegistry） | src/brain/orchestration/ |

> 注：能力层迁移自 Top 阶段成果时，在此登记"来源 legacy-topo + 版本"，按 M7 显式引用。

## 三、组件注册（Component Registry，随 ui-kit 建立逐步登记）

| 组件 ID | 类型 | 规格依据 | 状态 | 落点 |
|---|---|---|---|---|
| `task-queue-engine` | 任务队列引擎 | specs/codex-task-queue-spec.md v1.3 | W2独立35项/62回归及U01已通过；Owner已批准v0.1-frozen，基线43ce130 | tasks/queue_engine/（存储/状态/派发/守护/进程树观测/审计/修正）；tasks/queue_engine/cli.py（操作入口）；execution/server 的 L7 接线尚未实现 |
| `task-status-text-loop` | 任务查询文字闭环（S1/v0.3） | wo-s1-task-text-loop；queue-spec v1.3 §4/10/11 | W4通过；16项文本测试、49项独立检查；Owner已批准v0.3-frozen固定731710a | src/brain/（窄规则意图、八态只读源、异常聚合、ID下钻、CLI）；完整L0-L10及execution/server接线仍待后续阶段 |
| `l7-interaction-loop` | L7 交互循环（征询闭环/队列调整/异步三拍） | product-plan v2.3 §6 B1；product-alignment-20261025 | 单测 15/15 全绿；真实链路验证通过；验收见 reports/l7-interaction-acceptance-20261025.md | src/brain/interaction.py（InteractionLoop）+ src/brain/cli.py（--loop）；复用 tasks/queue_engine/priority_deps.py QueuePlanner 官方写通道；征询载体=悬浮球（l7-orb-bridge 接线）；语音入口接线待做 |
| `l7-orb-bridge` | L7 悬浮球征询载体（InteractionLoop↔OrbStateMachine 映射 + prompt 征询文本通道） | product-plan v2.3 §6 L7；用户拍板「征询载体=悬浮球」；HS-005 orb.render 契约 | 桥接器单测 13/13 全绿；真实链路验证 9 项通过；L7 回归 15/15；orb.html JS 语法检查通过；验收见 reports/l7-orb-bridge-acceptance-20261025.md | src/brain/interaction_orb.py（InteractionOrbBridge）+ src/brain/interaction.py（reason 语义标签）+ host-shell Assets/orb.html（prompt 显示通道）；壳侧常驻事件循环已并入 L4 A2 上壳 |
| `l4-a2-orb-live` | L4 A2 组合窗口壳侧常驻事件循环（brain→壳 文件 IPC + WebView2 推送） | product-alignment-20261025 L4=A2；HS-005 orb.render 契约扩展（seq+prompt） | 壳构建 0 错误 0 警告；pusher 单测 10/10；真机 LIVE 端到端 5/5 指令全送达（含 prompt）；验收见 reports/l4-a2-orb-live-acceptance-20261025.md | src/host-shell/OrbLiveRenderer.cs（轮询 250ms）+ src/brain/display/host_pusher.py（HostOrbPusher 落盘 seq 递增）；窗口形态复用 OrbWindowConfig；⑤语音入口直接复用此链路 |
| `l8-credential-center` | L8 凭证中心（DPAPI 加密 + 四层凭证层 + 高危征询） | security-spec §1 凭证中心（强制）；product-plan L8 | 单测 24/24 全绿；真实回环验证通过；M2 回归 19/19；验收见 reports/l8-credential-center-acceptance-20261025.md | src/brain/guardrails/credentials.py（CredentialCenter）+ hazard.py（HazardGate）；审计 append-only credential_audit.jsonl |
| `l7-voice-entry` | L7 语音入口闭环（STT→桥接→悬浮球推送→TTS 回放） | product-alignment-20261025 ⑤ L7 语音入口接线；HS-005 orb.render 契约 | 单测 8/8 OK；真实链路端到端全通（faster-whisper 精确识别「查询任务状态」→ 桥接 talking → 推送 seq=6 → 回放 218KB 非静音）；验收见 reports/l7-voice-entry-acceptance-20261025.md | src/brain/voice_loop.py（VoiceInteractionLoop）；复用 asr.py/tts.py/interaction_orb.py/host_pusher.py |
| `ultima-plugin-bus` | 能力插件总线（ADR-011）：L1-L10 能力插件热插拔运行时 | ADR-011；specs/plugin-bus-spec.md v1.0 | s3-bus-kernel 已实现，待独立评审 | execution/server/ultima_bus/（清单/注册表/生命周期/依赖/事件/日志/CLI/回滚）；试点插件落 execution/packages/ |
| `ultima.intent.rule` | L1 规则意图试点插件 | api-contract v1.0 `intent.parse`；ADR-011 | v0.1.0 已实现，复用冻结 v0.3 行为，待独立评审 | execution/packages/intent/ultima.intent.rule/ |
| `ultima.domain.skill` | L2 技能领域试点插件 | api-contract v1.0 `domain.resolve`；ADR-011 | v0.1.0 最小件已实现，待独立评审 | execution/packages/domain/ultima.domain.skill/ |
| `ultima.memory.lite` | L9 轻量记忆试点插件 | api-contract v1.0 `memory.read/write`；ADR-011 | v0.1.0 进程内最小件已实现，待独立评审 | execution/packages/memory/ultima.memory.lite/ |
| `ultima-a2ui-v08-window-catalog` | A2UI v0.8 协议与组件 schema 目录 | ADR-007；specs/component-dsl-schema.md v2.2；官方 commit `059b8d34874f96c0395dbfe23e6cc8b41cdb0f87` | T1 schema 已登记；标准静态 5 组件、控件 5 组件与 Ultima 7 组件 renderer 已 active（s4-a2ui-renderer 20261027） | src/window/a2ui_validator.py；src/window/component_directory.json；src/window/vendor/a2ui-v0.8/；src/window/offline_renderer.py；src/window/active_renderer.py |
| `Text` / `Image` / `Row` / `Column` / `List` / `Card` | A2UI 标准文本/资源/布局组件 schema | A2UI v0.8 standard catalog（本地固定缓存） | registered，Text/Row/Column/List/Card 已 active（offline_renderer.py 静态安全渲染）；Image 仅接受 `asset:local` 受控本地引用、renderer 未实现（非 active） | Ultima catalog 内引用官方 props schema；静态渲染：src/window/offline_renderer.py |
| `Button` / `Slider` / `TextField` / `Modal` / `AudioPlayer` | A2UI 标准控件组件 schema | A2UI v0.8 standard catalog（本地固定缓存） | registered，已 active（active_renderer.py）；action 事件回调化不执行真实副作用；AudioPlayer 仅接受 `asset:local` 受控本地引用、渲染禁用占位不播放 | Ultima catalog 内引用官方 props schema；renderer：src/window/active_renderer.py |
| `Video` | A2UI 标准视频资源 schema（仅协议校验） | A2UI v0.8 standard catalog（本地固定缓存） | standard catalog 批次可校验；仅接受 `asset:local` 受控本地引用；未登记 Ultima renderer、非 active、不播放 | src/window/vendor/a2ui-v0.8/standard_catalog_definition.json；src/window/a2ui_validator.py |
| `UltimaWindow` / `UltimaSwitch` / `UltimaProgress` / `UltimaListCard` / `UltimaOrb` / `UltimaSensorCard` / `UltimaStatusTag` | Ultima 自定义组件 schema | 独立 catalog ID `urn:ultima-agent:a2ui:v0.8:window-catalog:v1` | registered，已 active（active_renderer.py 安全渲染，白名单 props、无任意样式注入）；不得作为官方 standard catalog 属性 | src/window/component_directory.json；props/tokenRefs/renderer/registered 状态完整；renderer：src/window/active_renderer.py |
| `task-workflow-paradigm` | **任务工作流范式组件（G-TASKFLOW-001，标准基础能力）** | `_shared/paradigms/UltimaAI-任务工作流范式.md` v1.0（2026-10-29 Owner 拍板建立） | **已登记为标准基础能力**：所有任务统一走「登记→计划评审→执行→独立审计→有界修复→验收→冻结」，执行端无关（Codex/DeepSeek/未来模型均为可替换执行适配器）；规划/开发/独立审查分离；越界 fail-closed；缺 tag=闭环未完成 | 权威源：`H:\UltimaAI\_shared\paradigms\UltimaAI-任务工作流范式.md`；执行适配器细则：Codex-外部执行端调用范式 v1.5；Agent 侧经 src/brain/orchestration/（L10 范式引擎）与 src/brain/loop/（m01 主脑决策回路）承载；验收依据：UltimaManager 实战验证（plan→plan review→develop→audit→bounded repair→approval→frozen）+ 2026-10-29 全量 239+120 复绿 |
| `ultima-manager` | **UltimaManager 任务控制面组件（标准基础能力，全系任务管控）** | `H:\UltimaAI\UltimaManager\`（产品根；sync/product.json + tasks/queue/index.md + docs/INDEX.md 权威） | **已登记为标准基础能力**：全系任务管控工具——工单编号核发（G-WO-NAME-001）、全局队列主表登记（G-DISPATCH-001 自主推进版下保留为可选监督/审计工具）、接管/来源/授权与前置核验、正式编号核重登记；不阻塞产品推进（各项目自主派发 Codex） | 权威源：`H:\UltimaAI\UltimaManager\docs\INDEX.md` + `_shared\queue\global-queue-index.md`；全局规则：G-DISPATCH-001（自主推进）+ G-WO-NAME-001（工单命名）；状态：wo-manager-v01 已冻结（OWNER_RELEASED_AND_FROZEN，tag wo-manager-v01-frozen-20261029）；Agent 侧承载：src/brain/orchestration/（L10）+ src/brain/loop/（m01 派发/接续回路） |
| `ultima-console-standard-hub` | **Ultima Console 标准管理中枢组件（标准基础能力，全系标准入口）** | `_shared/paradigms/UltimaAI-Console标准管理中枢范式.md` v1.0（2026-10-29 Owner 拍板建立） | **已登记为标准基础能力**：全系标准管理中枢——标准注册表（任务工作流/工单命名/执行端调用/队列登记/产品接入CMS/服务器资产/能力注册）+ 版本基线打 tag 铁律 + 审计入口；Agent 任务执行第一步=读 Console 标准注册表；只管理标准不派发任务（派发仍走 G-DISPATCH-001 自主推进 + Manager 可选监督） | 权威源：`H:\UltimaAI\_shared\paradigms\UltimaAI-Console标准管理中枢范式.md`；与 m28（任务工作流）/ m29（Manager 控制面）组合为 Agent 标准执行闭环；Agent 侧承载：src/brain/loop/（m01 标准读取前置） |
| `ultima-wallet-core` | **UltimaWallet 资产管理核心插件（标准基础能力，多链资产管理）** | `H:\UltimaAI\UltimaWallet\docs\INDEX.md` + `docs\ultima-wallet-core-scheme.md`（方案 v1.0 冻结）+ `docs\integration-standard.md`（接入标准 v1.0） | **已登记为 Ultima Agent 插件**：多链资产管理核心组件（原生库/SDK）——资产展示 + 发送（签名转账）+ 接收（地址/收款码）；EVM+BTC+Solana 三链；内核统一调配 + 可插拔模块（无用模块物理拆除）；FFI 契约 v0.1.0（9 操作+2 事件）+ 四套 SDK（C#/TS/Kotlin/Swift）；私钥永不跨 FFI（只走句柄）、签名先预览后确认；**UI 创建：由 Ultima Agent 统一执行，样式强制引用 `_shared/paradigms/Ultima-UI样式范式.md`（深色板 #0F1420，禁止自造色）**；Windows DLL+C# SDK 实测可用 | 权威源：`H:\UltimaAI\UltimaWallet\docs\INDEX.md`（执行入口）+ `integration-standard.md`（宿主接入 5 步/安全基线/限流冻结基线）；状态：v0.1 全量审计通过（16 项 PASS，报告 docs/reports/audit-v0.1.md）；M0-M3/L3-SDK 全部 frozen（tag m0-frozen~l3-sdk-frozen）；Agent 侧承载：经 FFI/SDK 层接入（宿主 UI 完全解耦） |

## 四、登记与查询规则

- 开发前：读本表 → 确认无重复 → 任务卡写"已查注册表，无重复"（M1）。
- 开发后：新 package/组件/技能回填本表，版本号 + 落点路径必须填全。
- 审计轮：核对"新产物 vs 注册表"是否重复/漏登（M4）。

## 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.3 | 2026-10-21 | 登记任务查询文本闭环组件与实际src/brain落点，仅覆盖工单④的窄文字场景，不把能力骨架全层标为完成。 |

| v1.4 | 2026-10-21 | Owner批准v0.3文本闭环冻结731710a，不扩大为完整语音或组合窗口通过。 |
| v1.5 | 2026-10-21 | 登记 A2UI v0.8 T1 协议/schema 与独立 Ultima catalog；仅 schema registered，所有 renderer 非 active，T2/T3 未开始。 |
| v1.6 | 2026-10-24 | T1 独立审查修复：规格更新至 v2.2，Image/AudioPlayer 资源定位收紧为受控 `asset:local` 正向白名单；注册状态仍非 active。 |
| v1.7 | 2026-10-24 | T1 最新独立审查修复：standard catalog 的 Video.url 纳入同一 `asset:local` 正向白名单；仅协议校验，未登记 renderer、非 active。 |
| v1.8 | 2026-10-25 | 登记能力插件总线组件（ADR-011）：`ultima-plugin-bus` 规格冻结（plugin-bus-spec v1.0），落点 execution/server/ultima_bus/ + execution/packages/，工单待排不占队列。 |
| v1.9 | 2026-10-25 | 新增执行参数契约规格（TD-05 待评估，execution-param-contract v0.1-draft）：影响 work-order-template v1.1（执行参数块）/ protocol-contract（信封加 execution_params+execution_report）/ acceptance-spec（Gate 可运行断言）；非组件不登组件表，登记留痕。 |
| v2.0 | 2026-10-25 | 登记 OpenJarvis 底座引入（TD-06 已采纳，base-adoption-plan v1.0）：Apache 2.0、Python 3.10+、五原语、8 注册表机制；作为服务器侧能力层运行时底座 vendor 进 UltimaAgent 目录；替换件（L8/L9/L10）实现其 ABC + 注册接入；待工单审计后冻结 ADR-012。 |
| v2.1 | 2026-10-25 | 能力层状态回填（依据 UA-ALIGNMENT-20261025）：L0/L1/L2/L3/L5/L6/L9/L10 已实现；L4 部分（核心已建、壳渲染待接线）；L8 部分（越界拦截已实现、凭证中心缺失）；L7 未实现（MVP 必含缺口，待工单）。落点更新为实际路径。 |
| v2.2 | 2026-10-25 | L7 交互循环已实现：能力层 L7 回填「已实现（单测 15/15 全绿，真实链路验证通过）」，落点 src/brain/interaction.py + cli.py（--loop）；组件注册新增 `l7-interaction-loop`（验收见 reports/l7-interaction-acceptance-20261025.md）。 |
| v2.3 | 2026-10-25 | L8 凭证中心（缺口 B2）已实现：能力层 L8 状态更新为「已实现（越界拦截+凭证中心+高危征询）」，落点 guardrails/credentials.py + hazard.py；组件注册新增 `l8-credential-center`（验收见 reports/l8-credential-center-acceptance-20261025.md）。 |
| v2.4 | 2026-10-25 | L7 悬浮球征询载体接线完成：InteractionResponse 新增 reason 语义标签；新增 InteractionOrbBridge（映射+prompt 征询文本）；orb.html 增补 prompt 显示通道；组件注册新增 `l7-orb-bridge`（验收见 reports/l7-orb-bridge-acceptance-20261025.md）。 |
| v2.5 | 2026-10-25 | DEFECT-001 修复完成（TTS 极短文本近静音）：三层修复（文本扩展 + 近静音检测重试 + 归一化兜底），落点 src/brain/voice/tts.py（expand_tts_text/tts_output_is_near_silent/normalize_tts_wav/_synthesize_once）；单测 18/18 + 真实合成 5 文本全 PASS；验收见 reports/defect001-tts-acceptance-20261025.md。 |
| v2.6 | 2026-10-25 | L4 A2 组合窗口上壳完成：能力层 L4 状态更新为「已实现（核心+壳常驻事件循环已接线 A2）」；组件注册新增 `l4-a2-orb-live`（brain→壳 文件 IPC：HostOrbPusher seq 递增 + OrbLiveRenderer 250ms 轮询推送）；壳构建 0 错误 0 警告 + 真机 LIVE 端到端 5/5 指令全送达；验收见 reports/l4-a2-orb-live-acceptance-20261025.md。 |
| v2.7 | 2026-10-25 | L7 语音入口接线完成：新增 VoiceInteractionLoop 闭环编排（ASR→InteractionOrbBridge→HostOrbPusher→TTS 回放），落点 src/brain/voice_loop.py；组件注册新增 `l7-voice-entry`；单测 8/8 + 真实链路端到端全通（faster-whisper 精确识别「查询任务状态」→ 桥接 talking → 推送 seq=6 → 回放 218KB 非静音）；验收见 reports/l7-voice-entry-acceptance-20261025.md。 |
| v2.8 | 2026-10-27 | 登记贾维斯逆向架构落地工单队列（s3 批次 17 单，QUEUED，依据 docs/plans/jarvis-reverse-architecture-20261026.md §4.3 推进顺序）：`ultima-plugin-bus`（ADR-011）状态更新为"工单已排→s3-bus-kernel"；其余 16 单均为既有组件升级/接线（L8 凭证中心→s3-credential-bus、L9 记忆→s3-memory-base、任务队列引擎→s3-orchestrator、l7-voice-entry→s3-voice-fullchain、l4-a2-orb-live→s3-behavior-layer 等）或新登记组件（看门狗 M22→s3-watchdog、闸门驻留 M19/M26→s3-guard-resident、审计 M21→s3-audit-trail、供应链 M23→s3-supply-chain、环境认知 M16→s3-env-cognition、浏览器 M13→s3-browser-channel、检索增强 M14→s3-websearch-upgrade、羁绊 M18→s3-bond-system、心跳 M27→s3-heartbeat、渠道 M24→s3-ime-bridge、设备档案 M15→s3-device-profile）；任务卡落 tasks/cards/s3-*/task.md。 |
| v2.9 | 2026-10-27 | s3-bus-kernel 实现登记：能力插件总线内核及 intent/domain/memory 三份 v0.1.0 试点插件进入待独立评审。 |
| v3.0 | 2026-10-29 | **登记任务工作流范式为标准基础能力（G-TASKFLOW-001）**：所有任务统一走「登记→计划评审→执行→独立审计→有界修复→验收→冻结」，执行端无关（Codex/DeepSeek/未来模型可替换，工作流不变）；组件注册新增 `task-workflow-paradigm`；权威源 `_shared/paradigms/UltimaAI-任务工作流范式.md` v1.0（Owner 拍板建立，镜像 UltimaDocs gtaskflow-001-registered-20261029）；执行适配器细则=Codex-外部执行端调用范式 v1.5。 |
| v3.1 | 2026-10-29 | **登记 UltimaManager 为标准基础能力组件（`ultima-manager`）**：全系任务控制面工具——工单编号核发（G-WO-NAME-001）、全局队列主表登记（G-DISPATCH-001 自主推进版下为可选监督/审计工具）、接管/来源/授权与前置核验；wo-manager-v01 已冻结（OWNER_RELEASED_AND_FROZEN，tag wo-manager-v01-frozen-20261029），不阻塞产品推进；Agent 侧承载 src/brain/orchestration/ + src/brain/loop/。 |
| v3.2 | 2026-10-29 | **登记 Ultima Console 标准管理中枢为标准基础能力组件（`ultima-console-standard-hub`，m30）**：全系标准管理中枢——标准注册表 + 版本基线打 tag 铁律 + 审计入口；Agent 任务执行第一步=读 Console 标准注册表；只管理标准不派发任务；权威源 `_shared/paradigms/UltimaAI-Console标准管理中枢范式.md` v1.0；与 m28（任务工作流）/ m29（Manager 控制面）组合为 Agent 标准执行闭环。 |
| v3.3 | 2026-10-29 | **登记 UltimaWallet 为 Ultima Agent 插件（`ultima-wallet-core`，m31）**：多链资产管理核心组件（原生库/SDK）——资产展示 + 发送 + 接收，EVM+BTC+Solana 三链；FFI 契约 v0.1.0（9 操作+2 事件）+ 四套 SDK；私钥永不跨 FFI、签名先预览后确认；v0.1 全量审计通过（16 项 PASS），M0-M3/L3-SDK 全部 frozen；Windows DLL+C# SDK 实测可用；Agent 侧经 FFI/SDK 层接入（宿主 UI 解耦）。 |
| v3.4 | 2026-10-29 | **m31 补充 UI 创建规则**：需要创建 UI 时，由 Ultima Agent 统一执行样式创建，强制引用 `_shared/paradigms/Ultima-UI样式范式.md`（深色板 #0F1420，禁止自造色）；宿主 UI 不自行发明样式。 |
