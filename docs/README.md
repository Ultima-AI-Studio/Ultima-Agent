# docs 知识文档根：权威文档清单（08-流程清单对应物）

范式先行，其余围绕范式展开。本文档是**全库文档的权威登记表**（新增文档必在此登记，M3 配套）——状态列 ✅ 已有 / ⚠️ 部分覆盖 / ❌ 缺口，优先级 P0（立项前）> P1（开发期）> P2（迭代期）。

## 目录职责

| 目录 | 职责 | 现有文件 |
|---|---|---|
| paradigms/ | 强制范式（MUST，不可违反） | 11 篇 |
| plans/ | 规划（能力/平台/路线/决策/技术推进） | 11 篇（含 scenarios/ 子目录） |
| specs/ | 技术规格（环境/注册表/契约/任务队列/执行参数契约） | 22 篇 |
| research/ | 调研资料库（竞品/工具链/动效/多端形态/机器人与具身/Agent 对照拆解/OpenJarvis 底座） | 16 篇 |
| references/ | 引用库（教训/沟通汇集/方案文档） | 3 篇 |
| reports/ | 审计/复盘报告 | 53 个顶层Markdown文件（含本轮冻结申请；evidence子目录另计） |

- KWS 语音唤醒落地（voice-kws-wake，P0，2026-10-27）：src/brain/voice/kws_listener.py（sherpa-onnx KeywordSpotter 流式唤醒「贾维斯/ULTIMA」→ VAD 对话回合 → TTS 回放 → 回到待唤醒；灵敏度 KWS_THRESHOLD 可调；单实例锁）；验收 	asks/cards/voice-kws-wake/acceptance-evidence.md + 
eceipt.json；tasks.json 37 项（32 COMPLETED + 5 TERMINATED）；真机听测登记为统一真机回归项（最后统一一点点测）。
## 2026-10-27 s7 记忆热度分层 + 整体审计登记

- s7-memory-temperature（主脑直接执行，2026-10-27）：`docs/plans/memory-temperature-tiering-20261027.md` 设计落盘（热/温/冷三档 + 短期/中期/长期时间三层映射 + 打断单元入记忆层，ADR-008 增量不推翻）；代码 `src/brain/memory/layers.py|vectors.py` + `src/brain/loop/brain_loop.py`；单测 `src/brain/tests/test_temperature_s7.py` 25/25 OK；验收 `tasks/cards/s7-memory-temperature/acceptance-evidence.md` + `receipt.json`；冻结参数零差异核对通过。
- 整体审计：`reports/audit-s7-20261027.md`（三态：通过，无 P0；P1=4 项既有测试失败已登记 + git 288 项未提交待拍板粒度；tasks.json 补登/queue.md 清理已闭环）。
- B 类修复：`reports/fix-b-audit-20261027.md`（4 项既有测试失败 + queue_source 缺 TERMINATED 产品缺陷 + 4 条 s4 任务时间倒置数据缺陷，全量 221 项测试全绿）。

## 2026-10-28 版本收口执行证据登记（工单⑥⑦⑧）

- 工单⑥（MVP 冻结）：`tasks/queue/wo-s1-mvp-freeze.md`；三卡 confirm-loop（L7 征询闭环 3/3）/ credential-gate（L8 凭证中心 4/4）/ queue-adjust（队列调整 3/3）验收全绿回填，专项测试（test_interaction/test_interaction_orb/test_queue_source/test_credential_s3）全绿；总卡 §3 T1-T3 PASS 勾选。内部 tag `wo-s1-mvp-freeze-done` 待版本级联合收口时打。
- 工单⑦（工程封装）：`tasks/queue/wo-s1-engineering-packaging.md`；PK-01 EXE 封装、PK-02 安装包、PK-04 真实签名（Ed25519，篡改拒绝）、PK-05 对接更新通道（RU-12 真实发布 + T1 客户端拉取校验闭环一次成功）全 PASS；PK-03 依赖引导检测层真机闭环 + 模拟缺失分支 PASS，缺失分支真机净机静默引导待净机环境（本机无 VM/ISO，环境约束非代码缺陷）。证据 `reports/evidence/wo-s1-engineering-packaging/` + `dist/release-artifact-inventory.json`。
- 工单⑧（远程更新）：`tasks/queue/wo-s1-remote-update.md`；T1 通道库（RU-01~04：查版本/下载 SHA256/Ed25519 双签名验签/篡改拒绝）、T2 三触发+更新 UI（RU-05~08，25/25 单测全绿）、T3 发布端（RU-12 真实发布 GitHub Release v0.1.0 id 426454992，4 资产）。真实远端冒烟 `reports/evidence/wo-s1-remote-update-trigger/smoke-t1-t2-20261028.json` SMOKE_RESULT=PASS；实现 `src/update/`（channel/triggers/ui_server）+ `src/ui/update_page.html`。T1/T2 由主脑直做闭环（用户指令不派 Codex）。
- 版本级冻结门：工单⑥⑦⑧ 三方 DoD 中，⑥ 全绿、⑧ 全绿、⑦ 剩 PK-03 缺失分支真机净机验证（环境约束）；`stage1-v1.0-frozen` 共同 tag 待 PK-03 净机补验 + 四信号联合评估 + 文档同步齐备后由版本级触发。

## 2026-10-21 执行证据登记

- 工单①：`tasks/queue/wo-s1-queue-engine.md`；实现 `tasks/queue_engine/`；当前独立验收 `reports/w2-independent-acceptance-20261021.md` 第二轮，35项技术验收与62项回归全部通过，真实T1卡及修正子任务→父任务闭环已独立审计；证据 `reports/evidence/w2-20261021/round2/`。交叉环境门U01见 `reports/w1-independent-acceptance-20261021.md` 第一轮（宿主阶段PASS）。内部tag `wo-s1-queue-engine-done`已创建，全局工单已闭环；W1/W2已收口，Owner已批准v0.1冻结，tag `v0.1-frozen`固定43ce130，旧42项记录保留作历史证据。
- 工单②：`reports/w1-host-resume-20261021.md` 与 `reports/w1-independent-acceptance-20261021.md`；真实144/96/96DPI、原生显示、鼠标拖动及正式Python自检正负向证据已补齐，维护重启后旧PowerShell59328已清除，第四轮独立W1通过，内部tag `wo-s1-host-shell-done`建立；Owner已批准v0.1冻结。正式入口 `../scripts/selfcheck-host-shell.py`，原`.ps1`保留历史。
- 本轮目标修复：`reports/goal-repair-20261021.md`；补登记/执行/回收入口、修复计划依赖与状态漂移；操作说明 `../tasks/queue/EXECUTION.md`，完整验证见报告证据路径。
- 工单④：`reports/w4-text-loop-acceptance-20261021.md`；两项独立发现修正后，文本16项测试及独立49项检查全部通过；最终独立裁决 `reports/evidence/w4-independent-20261021/round2-correction/result-final.json`，第一轮失败原样保留。v0.3冻结申请 `reports/v03-freeze-approval-request-20261021.md` 已获Owner批准，实际v0.3-frozen固定731710a；工单⑤版本门已过，仍待语音四IO依赖。已有音频仅离线识别复验，不代表完整语音工单或v0.2通过。

## 文档体系状态与缺口（对照 dev-conductor 标准 18 项 + Ultima 特有）

### A. 标准文档体系

| # | 标准文档 | 对应物 | 状态 |
|---|---|---|---|
| 00 | 架构设计 | paradigms/architecture.md（三层模型，范式级） | ⚠️ 缺工程级：运行时模型/模块清单/演进路线（P1 收尾） |
| 01 | 接口契约 | specs/protocol-contract.md | ✅ |
| 02 | 数据模型 | specs/data-model.md | ✅ |
| 03 | 时序流程 | specs/sequencing.md | ✅ |
| 04 | 参数基线 | specs/parameter-baseline.md | ✅ |
| 05 | 验收规范 | paradigms/acceptance-spec.md | ✅ |
| 06 | 安全规范 | specs/security-spec.md | ✅ |
| 07 | 构建发布 | specs/build-release.md | ✅ |
| 08 | 流程清单 | project-flow.md + 本文档 | ✅ |
| 09 | 工程骨架 | README 目录树 + specs/environment-spec.md（§6 依赖锁定与安装流程） | ✅ |
| 10 | 协议规范 | specs/protocol-contract.md | ✅ |
| 11 | 枚举数值总表 | specs/enum-registry.md | ✅ |
| 12 | 运维自检 | specs/ops-selfcheck.md | ✅ |
| 13 | 术语依赖图 | specs/glossary-dependency.md | ✅ |
| 14 | ADR | plans/tech-decisions.md v1.2（ADR-001~010） | ✅ |
| 15 | 基线台账 | specs/baseline-ledger.md | ✅ |
| 16 | 功能范围 | plans/capability-list.md（L0-L10） | ✅ |
| 17 | 竞品对比 | specs/competitor-matrix.md（正式矩阵） | ✅ |
| 18 | Codex 工单 | tasks/work-order-template.md（模板落地） | ✅ |

### B. Ultima 特有应建

| 文档 | 说明 | 状态 |
|---|---|---|
| 通信协议契约 | 三层架构消息格式（并入 A-01/10） | ✅ specs/protocol-contract.md |
| 数据模型 | 记忆/任务/设备/凭证/配置存储（并入 A-02） | ✅ specs/data-model.md |
| 时序流程 | 运行时时序（并入 A-03） | ✅ specs/sequencing.md |
| 设备接入契约 | device-cluster 工程级接口（档案/凭证/命令） | ✅ specs/device-contract.md |
| 组件 DSL Schema | ui-kit 落地（组件注册数据结构 + DSL 定义） | ✅ specs/component-dsl-schema.md |
| API 契约（能力层对外） | L0-L10 能力暴露接口 | ✅ specs/api-contract.md |
| CodeX 任务队列 | 任务库存储/状态机/派发纪律/优先级插队/依赖环检测/审计闭环（MVP 查任务状态数据口径） | ✅ specs/codex-task-queue-spec.md |

## 补建顺序（已完成）

1. **P0 第一批（2026-10-16 完成）**：protocol-contract → baseline-ledger → sequencing → data-model → acceptance-spec → tech-decisions v1.1（ADR）
2. **P1+P2（2026-10-16 完成）**：security-spec / build-release / ops-selfcheck / device-contract / component-dsl-schema / api-contract / parameter-baseline / enum-registry / glossary-dependency / competitor-matrix / work-order-template / environment-spec §6 骨架整合
3. **剩余**：A-00 架构设计工程级补充（运行时模型/模块清单/演进路线，P1 收尾，可选项）

## 变更日志

| 版本 | 日期 | 变更内容 |
|---|---|---|
| v1.0 | 2026-10-16 | 初版：权威文档清单 + 缺口矩阵（对照 dev-conductor 18 项 + Ultima 特有）+ 补建顺序 |
| v1.1 | 2026-10-16 | P0/P1/P2 全量补齐：18 项标准 + 6 项特有全部落地（A-00 工程级架构补充留 P1 收尾） |
| v1.2 | 2026-10-16 | 登记 references/top-agent-journey.md（Top Agent 全程沟通汇集，只汇集不分析） |
| v1.3 | 2026-10-16 | 新增 reports/ 目录登记：top-agent-progress-analysis-20261016.md（推进过程分析总结与改进方案） |
| v1.4 | 2026-10-16 | 分析报告改进方案 I1~I17 全量固化进范式：acceptance-spec §6 执行红线（I1-I3）、project-flow ④分段上报（I4）、governance M6 覆盖链（I5）、ui-kit §6 原型评审清单（I11）、interaction §7 闭环预演（I12）；governance v1.2 / acceptance-spec v1.1 / project-flow v1.1 / ui-kit v1.1 / interaction v1.1 |
| v1.5 | 2026-10-16 | 新增 reports/watchdog-management-review-20261016.md（三代看门狗复盘：A/B/C/D/E 五组 15 条经验 + Ultima 落地建议 8 项） |
| v1.6 | 2026-10-16 | ops-selfcheck v1.1 新增 §3 全程无窗口纪律（MUST）：所有子进程启动点强制 CREATE_NO_WINDOW / pythonw / Hidden 包装（派发/看门狗/探活全程静默） |
| v1.7 | 2026-10-16 | watchdog 复盘 8 项落地建议全量固化：governance v1.3 新增 M9 守护器运行纪律（A1/B3/C1/C2/D1/D2/自清理边界）、acceptance-spec v1.2 §6 补 B1 判定 fail-closed、project-flow v1.2 ③派发补 B2 串行闸门、ops-selfcheck v1.2 补 A2 重启根因门 + C4 进程识别规范 |
| v1.8 | 2026-10-16 | governance v1.4 新增 M9-C3 生命周期绑定（防孤岛）：守护器必须为主脑子进程，父死即降级只读静默+失联标记+优雅退出，正常关闭先停守护器再退主脑 |
| v1.9 | 2026-10-16 | ops-selfcheck v1.3 新增 C3 关闭顺序自检项（governance M9-C3 配套）：先停守护器再退主脑；宿主异常退出守护器不得独立存活 |
| v2.0 | 2026-10-16 | 新增 M10 教训持续捕获：governance v1.5 新增 M10（触发即登记/审计扫描/复发检测/维度兜底/教训⇄范式联动）、新建 lessons-log.md 教训库（L01~L13）、ops-selfcheck v1.4 新增教训扫描项 |
| v2.1 | 2026-10-16 | 全量文档结构化审计修复：① 目录职责数字同步（paradigms 10 / plans 5+scenarios / specs 16 / references 4）② A-14 tech-decisions 升 v1.2（ADR-001~010）③ ui-kit-standard / interaction-paradigm / watchdog 报告头部版本号同步至变更日志（v1.1）④ product-plan 头部同步 v2.3（标题/版本行/journey 索引三处对齐）⑤ baseline-ledger OPEN-11 关闭原因版本修正 v1.2 ⑥ scenarios/ 场景文件标记待建 |
| v2.2 | 2026-10-16 | 登记 reports/docs-structure-audit-20261016.md（全量文档结构化审计报告：7 处漂移修复 + 1 处缺口登记，参数/引用/计划衔接验证通过） |
| v2.3 | 2026-10-16 | 新增版本计划体系：specs/version-plan-spec.md（版本计划标准：版本号语义/四件套/生命周期四态/冻结门/启动引导对齐）+ plans/version-plan.md（阶段一 v0.1→v1.0 实例）；sequencing v1.1 启动时序补版本定位步（防旧版/新版错位） |
| v2.4 | 2026-10-16 | version-plan-spec 升 v1.1：§5.1 新增文档新旧隔离纪律（强制）——跨版本/主题必须新开文件、更新三步一体、正文只留当前版、三处一致性强制（头部版本=变更日志=正文），防新旧混放 |
| v2.5 | 2026-10-16 | 文档新旧隔离纪律全局挂载：governance 升 v1.6（M6 新增 M6-DOC 文档版单一现行版本）+ ops-selfcheck 升 v1.5（新增文档新旧隔离检查 MUST）+ lessons-log 升 v1.1（新增 L14，M10-⑤ 双向联动回填） |
| v2.6 | 2026-10-16 | 登记 specs/codex-task-queue-spec.md（CodeX 开发任务队列规范 v1.0：存储沿用 tasks/ 骨架+防膨胀、状态机补 SELF-CHECK/AUDIT/CANCELLED、派发纪律/优先级插队/依赖环检测/审计闭环；MVP 查任务状态数据口径） |
| v2.7 | 2026-10-16 | 登记 tasks/acceptance-checklist.md（阶段一开发任务验收对照清单 v1.0：20 单元 + 5 冻结门 + 项目级 §8 四信号，目标/证据/结论三列制；CodeX 照单执行 + 主脑审计共用） |
| v2.8 | 2026-10-16 | 范式挂接两个执行 Skill（M3 变更流程，评审 Owner）：① acceptance-spec v1.3 新增 §7 结果反推法 + §8 提交前自核闭环 + §9 执行 Skill 引用（engineering-standard）② project-flow v1.3 ③④⑤⑥⑦ 挂接 engineering-standard ③ skill-dispatch v1.1 eng.audit 挂接 project-governance-audit ④ governance v1.7 M4 挂接 project-governance-audit（治理体检执行）；范式定义"是什么"，Skill 定义"怎么做" |
| v2.9 | 2026-10-16 | 登记工单⑦ 系列（N7 文档同步修正）：① 工单⑦ 远程更新与发布通道（tasks/queue/wo-s1-remote-update.md + 3 张任务卡 + 队列 v1.2 094-105 单元 + 验收清单 v1.6→v1.8）② 报告 reports/stage1-simulation-l1-w7-20261016.md（工单⑦ 12 单元模拟：10 通过/2 阻塞环境前置，F5/N4-N7）③ 规范 specs/update-manifest-schema.md（manifest 单一权威，N5 落地）；④ 修正目录职责表计数（paradigms 11 / plans 7 / specs 20 / references 5 / reports 10 个文件，替换过时数字 10/5/17/4/3） |
| v3.0 | 2026-10-16 | 工单⑦⑧ 顺延重编号登记（用户决定：工程封装与安装包独立为工单⑦，原工单⑦ 远程更新顺延为工单⑧）：① 新工单⑦ 工程封装（tasks/queue/wo-s1-engineering-packaging.md + cards/s1-engineering-packaging/task.md，U21，PK-01~05，094-098）② 原工单⑦ 顺延工单⑧（wo-s1-remote-update.md v1.1：U22-U24，RU-01~12，099-110，依赖工单⑦ 安装包）③ 队列 v1.3→v1.4（8 工单/25 卡/110 单元/W1-W8）④ 验收清单 v1.9→v2.0（24 U/110 L1，v1.0 门=⑥+⑦+⑧）⑤ build-release.md v1.0→v1.1 补工程封装规范 §2.1 |
| v3.1 | 2026-10-21 | 更新工单①当前证据为W2第二轮35项/62回归及真实卡闭环，登记U01独立宿主环境门结论；保留旧报告，不代作版本审批。 |
| v3.3 | 2026-10-24 | 四轮调研统一落盘：新增 5 篇详细调研（state-machine-thinking / audio-visualizer-spec / desktop-companion / ar-vr-hud / robotics-embodied，均含架构/技术栈/参数/实施方法/来源）；research/ 3→8 篇；README 索引 v1.0→v1.1（补 5 篇 + 后续调研方向登记表 6 项） |
| v3.4 | 2026-10-24 | 新增形态拓展分阶段方案：docs/plans/form-expansion-plan-20261024.md（1.0 五大能力底座 + 阶段二羁绊系统[可配置距离档位] + 阶段三多设备联动 L0-L4 + 阶段四具身延展 OpenGo 路线；Owner 确认）；plans/ 7→8 篇 |
| v3.5 | 2026-10-24 | 执行状态综合分析后队列调整（Owner 确认）：① queue.md 重写为调整后派发顺序（composite-window 待 Manager 接管→v0.4→engineering-packaging→mvp-freeze→remote-update→ORB w1-w5→1.0 能力底座四单）② voice-poc 登记为受限验收（文本侧通过、语音真机/W3 后置）③ 新增 4 张 1.0 能力底座工单申请（数据形态/子智能体调用/Skill 学习/插件接入 MCP，request-ultimaagent-capability-*.md，后置不插队）④ work-order-naming-plan 补充 4 条映射 |
| v3.6 | 2026-10-25 | 新增能力插件总线规格并冻结：① specs/plugin-bus-spec.md v1.0（ADR-011，L1-L10 能力插件热插拔总线，v0.1 审计打回→v0.2 修订→复审通过→Owner 拍板）② tech-decisions v1.3 登记 ADR-011 ③ registry v1.8 登记 ultima-plugin-bus 组件 ④ 工单待排不占队列（queue.md 未动）；specs/ 20→21 篇 |
| v3.7 | 2026-10-25 | Agent 对照拆解 + 执行参数契约落盘：① 新增调研 docs/research/agent-loop-param-benchmark-20261025.md（Japlos 视频任务逻辑/UIUX + OpenJarvis 源码参数级拆解，结论=四个结构性缺口）；research/ 8→9 篇 ② 新增规格 docs/specs/execution-param-contract.md v0.1-draft（同一契约两场景：开发时静态工单 + 运行时 14B 调用外部模型下发/回传参数；四段输出协议；验收机检化；落盘映射待派工单）；specs/ 21→22 篇 ③ research README v1.1→v1.2 |
| v3.8 | 2026-10-25 | OpenJarvis 底座方案落盘（TD-06 已采纳）：① 新增调研 docs/research/openjarvis-base-adoption-20261025.md（五原语事实基线/与 L1-L10 映射/缺口六方向可拔插模块清单/底座偏移评估）；research/ 9→10 篇 ② 新增方案 docs/plans/base-adoption-plan-20261025.md（拿来即用→卡住才改→全通全绿→适配调校四阶段 + 插拔纪律 + 工单规划）；plans/ 8→9 篇 ③ tech-decisions v1.4→v1.5（TD-06）④ registry v1.9→v2.0 ⑤ research README v1.2→v1.3 ⑥ 工单已整理未派发（待审计 + Manager 接管） |
| v3.9 | 2026-10-25 | 底座审计留档：① 新增审计报告 docs/reports/base-adoption-audit-20261025.md（11 份产物 Gate 判定全 PASS·P0 清零·待派发）；reports/ 顶层文件 23→24 ② 5 张工单申请卡全部就位 tasks/queue/（walking-skeleton/guardrail/memory/verify/polish），等 Manager 接管 |
| v4.0 | 2026-10-25 | 技术推进方案落盘：新增 docs/plans/tech-progression-plan-20261025.md（拼装全景+接线范式+里程碑 M0-M6+调试纪律+风险对策）；plans/ 9→10 篇 |
| v4.1 | 2026-10-27 | 记忆热度分层补设计落盘（Owner 拍板）：① 新增 docs/plans/memory-temperature-tiering-20261027.md（热/温/冷三档 + 短期/中期/长期时间三层映射 + 升降级规则 + 打断单元入记忆层；ADR-008 增量不推翻）；plans/ 10→11 篇 ② 排工单 s7-memory-temperature（cards/s7-memory-temperature/task.md + queue/wo-s7-memory-temperature.md，P1，队列登记） |
| v4.2 | 2026-10-27 | 完整审计 + 10-27 后期产物登记：① 完整审计 docs/reports/audit-full-20261027.md（53 文件 184 项测试 OK、无 P0、P1=权威清单登记已闭环、KWS 锁修复两项[atexit 仅删自己锁+心跳]）② 补登报告：reports/capability-vs-jarvis-20261027.md（能力清单 vs 贾维斯目标对比）、reports/audit-codex-plugin-20261027.md（GrokBot Codex 插件抄入审计）、reports/product-alignment-s5-20261027.md（S5 产品目标对齐，含待办路由）③ 计数校正：reports 顶层 24→53、research 10→16 ④ 调研（research/README 已登记）：venom-symbiote-research-20261025、grok-bot-orb-reconstructed-20261027、grok-bot-codex-architecture-20261027 |

当前维护后证据登记：`reports/evidence/w1-post-reboot-closeout-20261021/`；冻结审查材料 `reports/v01-freeze-approval-request-20261021.md`（Owner已批准）。

## 2026-10-27
- ASR 主链路切换 SenseVoice（docs/reports/asr-sensevoice-switch-20261027.md）
- 性能/死机问题审计与修复：三处跨进程单实例守卫（daemon/agent_server/watchdog）+ kws 预热后台化，实测单实例守卫生效、daemon_asr 归零（docs/reports/performance-process-audit-20261027.md）
