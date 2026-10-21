# docs 知识文档根：权威文档清单（08-流程清单对应物）

范式先行，其余围绕范式展开。本文档是**全库文档的权威登记表**（新增文档必在此登记，M3 配套）——状态列 ✅ 已有 / ⚠️ 部分覆盖 / ❌ 缺口，优先级 P0（立项前）> P1（开发期）> P2（迭代期）。

## 目录职责

| 目录 | 职责 | 现有文件 |
|---|---|---|
| paradigms/ | 强制范式（MUST，不可违反） | 11 篇 |
| plans/ | 规划（能力/平台/路线/决策） | 7 篇（含 scenarios/ 子目录） |
| specs/ | 技术规格（环境/注册表/契约/任务队列） | 20 篇 |
| references/ | 调研借鉴（工具链/竞品/动画/教训） | 5 篇 |
| reports/ | 审计/复盘报告 | 15 个顶层文件（2026-10-21复核；evidence子目录另计） |

## 2026-10-21 执行证据登记

- 工单①：`tasks/queue/wo-s1-queue-engine.md`；实现 `tasks/queue_engine/`；当前独立验收 `reports/w2-independent-acceptance-20261021.md` 第二轮，35项技术验收与62项回归全部通过，真实T1卡及修正子任务→父任务闭环已独立审计；证据 `reports/evidence/w2-20261021/round2/`。交叉环境门U01见 `reports/w1-independent-acceptance-20261021.md` 第一轮（宿主阶段PASS）。工单内部标记待行政收口，版本冻结仍待W1与Owner审批；旧42项记录保留作历史证据。
- 工单②：`reports/stage1-host-shell-20261021.md`；环境与自检通过，桌面/DPI和W1待验收。
- 本轮目标修复：`reports/goal-repair-20261021.md`；补登记/执行/回收入口、修复计划依赖与状态漂移；操作说明 `../tasks/queue/EXECUTION.md`，完整验证见报告证据路径。

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
