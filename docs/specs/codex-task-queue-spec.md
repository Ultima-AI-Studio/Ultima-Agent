# CodeX 开发任务队列规范（Codex Task Queue Spec）

- **版本**：v1.3 · 2026-10-16
- **性质**：强制（MUST）技术规格（对应 dev-conductor §13 任务生命周期 + §3 工单化开发；落点：`tasks/` 任务库本体）
- **适用范围**：主脑派发器、CodeX 类执行代理、审计轮、以及 MVP「查任务状态」（L7 队列管理）的数据口径来源
- **来源**：Top 阶段 codex-executor 实测（tasks.json / runs 六件套 / dispatch / master-audit-fix）+ 2026-10-16 主脑讨论（8 决策点：6/7/8 沿用已验证方案，1/2/4/5 本规范补强）

## 1. 目标与范围

- 定义「交给 CodeX 执行开发的任务队列」的存储形态、状态机、派发纪律、优先级/插队、依赖、重试与审计闭环。
- 本规范是任务库的**实现规格**（怎么实现）；任务库本体在 `tasks/` 目录（governance §3 写入权矩阵：任务执行器/立项人可写）。
- 本规范同时是 MVP 首场景「查任务状态」的**数据口径**——L2/L3 按本规范的字段与状态呈现，schema 变更必须先升本规范版本（M6-DOC）。

## 2. 目录与文件职责（沿用现有 tasks/ 骨架）

```
H:\UltimaAI\UltimaAgent\tasks\
├── tasks.json              # 任务库索引+状态快照（瘦身：只存索引字段，不存 goal 全文）
├── queue\
│   └── queue.md            # 待派发队列：排队任务 + 派发顺序（一次一主）
├── cards\
│   └── <task_id>\
│       └── task.md         # 单任务卡：goal/acceptance/dependsOn/receipt 全文
├── events\
│   └── <task_id>.jsonl     # 状态变更事件（追加式，审计可追溯）
├── runs\
│   └── <task_id>\          # 派发运行记录六件套：before/out/err/done/session/progress
└── archive\                # 归档区（只归档，不删除）
```

- **tasks.json 只存索引字段**：task_id / state / priority / dependsOn / parallelGroup / fileDomain / reasoningEffort / created_at / updated_at / terminal_reason / card_path。goal 全文与回执放 cards/<task_id>/task.md——防 Top 阶段 tasks.json 12.5MB 单文件膨胀的教训（lessons-log）。
- **events/ 状态事件追加式**：每次状态迁移追加一行 `{ts, from, to, reason, actor}`，禁止原地改写历史事件。
- **runs/ 六件套沿用 Top 验证形态**：`<task_id>.<ts>.<uuid>.{before,out,err,done,session,progress}`。
- **归档规则（M9 文件级保守）**：任务卡 / runs / events **永不自动删除**，只移动到 `archive/`；tasks.json 索引超过 1 万条时，已 COMPLETED/CANCELLED 条目自动归档索引项（文件本体不动）。

## 3. 任务卡字段（cards/<task_id>/task.md）

| 字段 | 必填 | 说明 |
|---|---|---|
| `task_id` | ✅ | 全局唯一：`<stage>-<模块>-<主题>`（例：s1-host-shell-bootstrap） |
| `goal` | ✅ | 做什么 + 禁止做什么（防顺手扩张，dev-conductor §5 任务级封闭） |
| `acceptance[]` | ✅ | 封闭验收清单（ACCEPT: 指令式，逐项可核对） |
| `dependsOn[]` | 依赖时 | 前置任务 id 列表（**仅填任务级 task_id；版本级前置一律写工单总卡，不写任务卡**，F3 修正见 §7） |
| `fileDomain[]` | ✅ | 允许写入的绝对路径域（M2 强制，越界=失败） |
| `priority` | ✅ | 0-100，默认 50；越大越先派 |
| `reasoningEffort` | ✅ | low / medium / high / ultra（dev-conductor §13.2；未声明默认 high，派发/收尾强制 low） |
| `category` + `skill` | ✅ | 专家技能路由（eng.code/ui/audit/…，M1 注册表；缺省不派发） |
| `receipt` | 完成时 | reviewReason / stdoutText / evidence / acceptance 逐项核对（M5 回执） |
| `retryCount` | ✅ | 重试计数，默认 0，上限 2 |

- 任务卡必须写「已查注册表，无重复」（M1）。
- 工单级任务按 `tasks/work-order-template.md` 生成（范围冻结/任务清单/总验收/DoD）。

## 4. 状态机（在现有定义上补中间态）

现有：`QUEUED → EXECUTING → COMPLETED/FAILED → BLOCKED`；修正 `~rN`。
本规范补为。**状态全集共 8 态（八态）**：QUEUED / EXECUTING / SELF-CHECK / AUDIT / COMPLETED / FAILED / BLOCKED / CANCELLED。**文档表述统一用"八态"**（N2 修正：任务卡标题/验收清单/本 §4 三处对齐，不再使用"七态/七阶段状态机"指代状态枚举；"七阶段"仅指 dev-conductor §13 任务生命周期七阶段，两者不同义）：

```
                    ┌──→ SELF-CHECK ──→ AUDIT ──→ COMPLETED（AUDIT 未 PASS 不许 COMPLETED，M5）
QUEUED ──→ EXECUTING ──┤
                    └──→ FAILED ──→（retryCount<2）→ QUEUED（修正 ~rN）／（≥2）→ BLOCKED
CANCELLED（用户取消 / 被新版本覆盖，M6 覆盖链）
依赖方 FAILED/BLOCKED → 被依赖方自动 BLOCKED（reason 记录）
```

- **非法迁移拦截**：状态只能按上图迁移；如 EXECUTING 直接跳 COMPLETED、AUDIT 未过跳 COMPLETED，由派发/审计脚本拦截报错。
- **SELF-CHECK**：执行代理自检（编译/测试/acceptance 逐项核对，dev-conductor §13 ⑤）。
- **AUDIT**：独立审计（开发与审计技能分离，M5；核对路径/重复/回执/版本，M4）。
- **BLOCKED 解除**：只允许人工/主脑裁决后转 QUEUED 或 CANCELLED，不允许自动重试绕过上限。
- **BLOCKED 转人工处置流程（F4 定稿，操作步骤）**：① 任务 retryCount≥2 或依赖方 BLOCKED → 自动转 BLOCKED（reason 记录根因）→ ② 主脑/人工裁决根因（判断修正任务是否可解）→ ③ 可解：生成修正任务（~rN）重新入队（人工置 QUEUED，retryCount 重置按新任务计）；不可解：转 CANCELLED 并登记 lessons-log → ④ 全程留审计 event（`{ts, from=BLOCKED, to=QUEUED/CANCELLED, reason, actor=human/brain}`），禁止脚本自动解除上限。

- **展示口径：当前状态与历史事件分离（N4 固化，Top 教训）**：任务"当前状态"**只读 tasks.json 索引的 state 单值**；FAILED/BLOCKED 是历史事件，只存在于 events/<task_id>.jsonl 与 runs/ 留痕，**不残留为可见的当前状态**——任务修复后必须经状态机显式迁移回 QUEUED 并最终到终态，不允许"曾经失败/阻断"挂在当前展示上让人看不懂。任何展示/汇报只呈现当前状态；历史事件仅在下钻/审计日志可见（与 AR-02「只报异常、不逐条念」同一聚合哲学）。
- **无悬空终态检查（审计轮 MUST，N5 固化）**：审计时核查任务库——**不存在停留在失败/冻结却无后续事件的悬空记录**；每条任务必须走到终态（COMPLETED 或 CANCELLED），未达终态 → 报警并转 BLOCKED 留主脑处置。语义是"队列看门狗自清理"：**不是删记录（M8 留痕），而是保证每条记录都走到终态**；清理的对象是悬空状态，不是历史。

## 5. 派发纪律（串行闸门 + 并行组上限 + 无窗口）

- **串行闸门（沿用 B2，project-flow ③）**：默认一次只派一个，派发前检查闸门。
- **并行组**：`parallelGroup` 组内任务允许并行，但**全队列同时 EXECUTING ≤ 2**；超限任务留在 QUEUED 并记录等待原因。
- **幂等防重派（M9-C2 三重判定）**：派发前检查①派发进程在跑 ②执行会话在跑 ③有活跃 run → 本轮不派；**探测失败默认按"忙"处理，宁可不派也不重派**。
- **零弹窗（ops-selfcheck §3 零弹窗绝对纪律 MUST）**：所有派发/看门狗/探活子进程启动点强制 CREATE_NO_WINDOW / pythonw / Hidden 包装；**任务全程前台零弹窗——任何窗口闪一下都不行**（不限控制台，含一切 GUI 窗口闪现）；验收按运行期窗口枚举（全程计数 0，宿主 GUI 除外）。
- **暂停开关（M9-B3）**：存在 `.pause-dispatch` 标记时只读审计、不派发。
- **守护器生命周期（M9-C3）**：守护器必须是主脑子进程，父死即降级只读静默+失联标记+优雅退出；禁止无主自治。

## 6. 优先级与插队

- `priority`（0-100，默认 50）：**插队/调整只作用于 QUEUED 任务**，不打断 EXECUTING（正在跑的让它跑完）。
- 操作：`requeue --before <task_id>`（插到指定任务前）；同优先级按 created_at FIFO。
- **插队/调优先级必须写 audit event 留痕**（events/<task_id>.jsonl：{ts, from, to, reason, actor}），审计可追溯。
- 用户侧（MVP 查任务状态 L7）：提供「查看队列 / 调整优先级 / 插队」能力，数据与字段口径同本规范。

## 7. 依赖与环检测

- `dependsOn[]` 沿用现有定义；**语义收紧（F3 修正，单元级模拟证实范围扩大）**：`dependsOn[]` 仅填**任务级 task_id**（本队列内其他任务的 task_id），**禁止填版本级前置**（如"v0.1 冻结"）——版本级前置一律登记在工单总卡（wo-*.md 的依赖链），不写任务卡；版本冻结门由派发器按工单总卡执行，不由任务卡 dependsOn 承担。
- **入队环检测（强制）**：入队时对 dependsOn 跑 DAG 环检测（DFS），有环 → 拒绝入队并报出环路径。
- 派发条件：依赖全部 COMPLETED 才派发；依赖方 FAILED/BLOCKED → 被依赖方自动 BLOCKED（reason 记录"依赖 <task_id> 未完成"），不空等。

## 8. 重试与失败（沿用已验证）

- 每任务最多重试 **2 次**（~rN 修正，retryCount 递增），超过转 BLOCKED。
- 失败审计：语义判断失败原因是否已解决；仍失败 → master-audit-fix 生成修正任务回任务库继续重试。
- CANCELLED / 已被覆盖任务（M6 覆盖链登记 ARCHIVED）跳过重试。

## 9. 审计闭环（沿用已验证 + M5 强制）

- 任务完成必须回执（M5）：**reviewReason / stdoutText / evidence / acceptance 逐项核对**；无回执不判 COMPLETED。
- 审计独立于开发（谁开发谁不能自审）；审计输出 PASS 或修正任务。
- 执行报告落 `logs/execution-reports/<task_id>/summary.json`（work-order-template 归档规则）；**summary.json 必须含 `version` 字段（格式 `S1/v0.x`，M8 对齐，N3 修正）**——无 version 字段的报告视为无效，审计不采信。
- **ultra 单元评审背书（F2 固化，强制）**：reasoningEffort=ultra 的单元交付前必须独立评审签字（开发与审计技能分离，dev-conductor §14.2）；签字记录进回执 evidence（占位格式：`reviewed_by=<auditor>, verdict=PASS/REVISE, ts=<...>`）；无背书签字不判 COMPLETED。
- 审计轮必须核对（M4）：产物路径 vs fileDomain、新组件 vs 注册表、报告完整性。

## 10. 报告语言标准（给人看的报告 · 中文化 MUST）

> 原则（用户定稿）：**报告是给人看的，不是给程序员/工程师看的**。审计报告、状态汇报、执行摘要一律中文直白表达；失败就是失败、冻结就是冻结、通过就是通过，禁止用工程英文单词堆砌。

- **状态中文映射（全项目统一用语）**：

| 工程态（内部字段） | 报告用语（中文） |
|---|---|
| QUEUED | 排队中 |
| EXECUTING | 执行中 |
| SELF-CHECK | 自检中 |
| AUDIT | 审计中 |
| COMPLETED | 已完成（通过） |
| FAILED | 失败 |
| BLOCKED | 冻结 |
| CANCELLED | 已取消 |
| PASS / FAIL / Freeze Gate | 通过 / 失败 / 冻结门 |

- **规则**：
  1. 报告正文不使用 FAILED / BLOCKED / PASS 等英文状态词；技术名首次出现时可加中文括号备注一次（如"任务已冻结（BLOCKED）"），此后只用中文。
  2. 直白表达不绕弯：失败就写失败、冻结就写冻结、通过就写通过；不写"异常状态""非通过态"等含糊说法。
  3. 上下文区分：版本级闸门叫"冻结门"，任务级状态叫"冻结/失败/通过"，报告中不混用。
  4. 本标准为审计检查项：报告出现未加备注的工程英文状态词 → 打回重写。

## 11. 与 MVP「查任务状态」的关系

- MVP 首场景 L2/L3 读本队列：总数 / COMPLETED / FAILED / BLOCKED / QUEUED / EXECUTING 按 §4 状态机统计。
- 队列字段即展示口径：task_id / title_zh / state / priority / 耗时 / terminal_reason。
- 本规范变更必须同步升版本并登记变更日志（M6-DOC 三处一致），防止 L2/L3 与队列 schema 漂移。

## 12. 变更日志

| 版本 | 日期 | 变更内容 | 授权人 |
|---|---|---|---|
| v1.0 | 2026-10-16 | 初版：8 决策点落盘——存储形态沿用 tasks/ 骨架+防膨胀（正文外置/索引瘦身/事件追加/归档）、状态机补 SELF-CHECK/AUDIT/CANCELLED、派发纪律（串行闸门+并行组 EXECUTING≤2+幂等防重派+无窗口）、priority 插队、依赖环检测、重试≤2/BLOCKED、审计闭环（M5 回执）；6/7/8 沿用 Top 已验证方案 | Owner |
| v1.3 | 2026-10-16 | §5 无窗口条款升级对齐 ops-selfcheck §3"零弹窗绝对纪律"（N7）：前台任何弹窗闪一下都不行（不限控制台，含一切 GUI 窗口闪现），验收按运行期窗口枚举全程计数 0（宿主 GUI 除外） |
| v1.2 | 2026-10-16 | Top 教训固化（评审 Owner）：① §4 补展示口径 N4——当前状态只读索引 state 单值，FAILED/BLOCKED 历史事件只进留痕不残留为可见状态，修复后必须显式迁移回并走到终态 ② §4 补无悬空终态检查 N5——审计轮 MUST 核查无"停留在失败/冻结却无后续事件"的悬空记录，每条任务必达终态（不删记录、保证闭环）③ 新增 §10 报告语言标准——报告一律中文直白表达（失败=失败、冻结=冻结、通过=通过），状态中文映射表 + 禁工程英文状态词 + 违反打回 | Owner |
| v1.1 | 2026-10-16 | 单元级模拟修正落盘（评审 Owner，依据 stage1-simulation-l1-20261016.md）：① §3/§7 dependsOn 语义收紧——仅填任务级 task_id，版本级前置一律写工单总卡（F3，范围扩大至 5 卡）② §4 状态表述统一"八态"（N2，区分七阶段生命周期）③ §4 补 BLOCKED 转人工处置四步流程（F4 定稿）④ §9 summary.json 强制 version 字段（N3，M8 对齐）⑤ §9 补 ultra 单元评审背书强制步骤（F2 固化） | Owner |
