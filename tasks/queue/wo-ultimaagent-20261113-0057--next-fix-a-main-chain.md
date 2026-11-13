# Codex 工单 · wo-ultimaagent-20261113-0057（修复 A：主链闭合）

> 版本：v1.0 ｜ 状态：待审计（先审卡，审过再执行）｜ 执行端：Codex ｜ 推理强度：high
> 来源：`docs/reports/audit-wo-ultimaagent-20261113-0056.md` §5 与 §7
> 本单负责 11 条：C-01、G-03、G-04、H-01、C-02、C-03、C-05、G-05、E-01、C-17、C-18

---

## 0. 现状校准

| 事实 | 值 |
|---|---|
| 审计结论 | 不通过，BLOCKER 11 / HIGH 22 / MED 3 |
| 主链最短路径（§7 第 1 条） | C-01 → G-03/H-01/C-02 → C-03/C-05 → G-05/E-01/C-17 |
| 本单范围 | 上述 9 条 ＋ G-04（决策三态）＋ C-18（Core↔Memory 失败确认）＝11 条 |
| 不属本单 | E-02/E-04 等值冲突（0058）、跨域面与交付链（0059） |

本单只补**契约与状态定义**，不写实现代码、不定数值、不新增能力。

---

## 1. 范围冻结

**只做**：在基线新增一章"§二十五 主链契约（对话／装配／计划／派发／执行／取消／补偿）"，逐条写死 11 条契约；同步详解页对应小节与树对应节点描述。
**不做**：不实现代码；不改 `n_ctx`、并发、超时等任何数值（值冲突归 0058）；不新增状态（八态不改，取消用子态或既有 `CANCELLED` 的可达化，方案须二选一并说明）；不碰 Console/Memory 之外模块。

**执行时写入域**：`docs/specs/next-感知交互参数基线-20261113.md`（仅新增 §二十五 与附录 A 一行）、`docs/tracker/next-基础能力架构-20261113.html`（对应小节）、`docs/tracker/北极星架构树.html`（对应节点 desc）。

---

## 2. 任务清单

| 任务 | 关闭发现 | 产出 | 验收门 |
|---|---|---|---|
| T1 | C-01、C-18 | §25.1 对话交接 ＋ §25.2 Core↔Memory | 信封字段齐、失败码齐、写幂等有定义 |
| T2 | G-03、G-04 | §25.3 上下文装配 ＋ §25.4 决策三态 | 唯一装配点、分区预算、三态判定条件可判 |
| T3 | H-01、C-02 | §25.5 计划 schema ＋ §25.6 计划交接 | 步骤状态机闭合、拒绝与回写路径齐 |
| T4 | C-03、C-05 | §25.7 派发 ABI ＋ §25.8 执行器 SPI | 请求/运行/回执三段齐、五动词齐 |
| T5 | G-05、E-01、C-17 | §25.9 幂等 ＋ §25.10 取消 ＋ §25.11 补偿 | 幂等键唯一性、取消可达、补偿可重放 |
| T6 | 总验收 | 自证清单 | 11/11 有落点、有判据、无夹带值 |

---

## 3. 任务明细（三段式）

### T1 · 对话交接与记忆确认（C-01、C-18）

**文件**：基线 §25.1、§25.2；详解页 §03（理解与决策）
**写什么**：
1. 定义 `turn.envelope`：`turn_id`、`session_id`、`speaker`（user/agent）、`asr_conf`、`intent`、`deadline`、`cancel_token`、`trace_id`；写明谁生成、谁消费、生命周期到哪结束。
2. 定义 `speak.request` / `speak.receipt`：播报文本上限的来源（引 §十六 profile，不另定值）、`duck` 请求、被新 turn 抢占时的处置。
3. 定义 Core↔Memory 三组契约：`mem.read`（同步、超时、降级返回空而非阻塞）、`mem.write`（幂等键＝`turn_id`＋`memory_id`、失败码、重试上限引 §21.6）、`mem.commit_ack`（写后确认与回滚标记）。
4. 失败码表：`MEM_TIMEOUT`、`MEM_WRITE_CONFLICT`、`MEM_FULL`（引 0058 E-04 的处置，不在本单定策略）。

**验收（Gate T1）**：信封字段 8 项全列且标注生成方/消费方；speak 请求-回执成对；Core↔Memory 三契约各含入参、出参、错误码、超时、幂等；每个字段能指到基线现有章节或本单新增行。
**禁止**：新增枚举值（八态不动）；写死数值（一律引既有裁决或写"按 §X 回读"）。

### T2 · 上下文装配与决策三态（G-03、G-04）

**文件**：基线 §25.3、§25.4
**写什么**：
1. `context.compose` 为**唯一装配入口**（其他模块不得自拼 prompt）；列分区：`system`／`policy`／`memory.hot`／`habit`／`session.recent`／`tool.schema`／`user.turn`，每区给预算口径（**总和受 §十六 4000 约束，具体切分由 N 系实测填，本单只定结构与截断顺序**）。
2. 截断顺序与优先级（先丢哪区、保留哪区）、超预算必留事件 `context_over_budget`。
3. 隐私裁剪：外部主脑调用前按 §23.6 三闸过滤，列出被裁剪区不得进入 payload。
4. `decision` 三态：`execute`／`clarify`／`refuse`，各给判定条件与输出结构（clarify 必须带具体问题；refuse 必须带原因码）。

**验收（Gate T2）**：全仓"唯一装配入口"写法唯一（不出现第二处 composer）；七分区齐且各有预算口径与截断位次；三态判定条件可写成 pass/fail（禁"视情况"）。
**禁止**：自行定 4000 的切分数字；把压缩实现写进本单（压缩归 0059）。

### T3 · 计划编排与计划交接（H-01、C-02）

**文件**：基线 §25.5、§25.6；架构树"任务编排"节点 desc
**写什么**：
1. `plan.schema`：`plan_id`、`goal`、`steps[]`（`step_id`、`tool`、`args`、`depends_on`、`acceptance`、`compensator`）、`budget`、`owner_turn`。
2. 步骤状态机：`PENDING → READY → RUNNING → DONE | FAILED | CANCELLED`，未列迁移一律拒（fail-closed）。
3. `console.submit_plan`：请求体、受理回执、拒绝码（`DOR_FAIL`／`DUP_PLAN`／`BUDGET_EXCEED`）、拒绝后回写 Core 的字段。
4. 计划级取消：取消传播到 steps 的规则与已 DONE 步骤的处置。

**验收（Gate T3）**：schema 字段齐且每字段有类型与来源；步骤状态机枚举与迁移表齐；submit_plan 请求/回执/拒绝码各 3 项齐；架构树该节点 desc 指向 §25.5。
**禁止**：让该节点继续以"仅名称"存在；引入第二套任务状态（必须映射八态）。

### T4 · 派发 ABI 与执行器 SPI（C-03、C-05）

**文件**：基线 §25.7、§25.8
**写什么**：
1. `dispatch.request`（`plan_id`、`step_id`、`tool_id`、`args`、`idempotency_key`、`deadline`、`sandbox_profile`）→ `dispatch.run`（`run_id`、`pid`、`stdout/stderr 流句柄`）→ `dispatch.receipt`（`exit`、`artifacts`、`side_effects[]`、`usage`）。
2. 执行器 SPI 五动词：`prepare`／`start`／`stream`／`cancel`／`finalize`，每动词给入参出参与幂等要求。
3. 工具注册：`tool_id` 命名、`schema` 来源（引注册分类 §②）、`requires_policy` 标记。

**验收（Gate T4）**：三段报文各字段齐；五动词全部有签名与语义；`idempotency_key` 从 turn 到 receipt 全程可追；任一工具不得绕过 dispatch 直连执行。
**禁止**：把 Console 写成第二个父进程；在 SPI 里塞平台相关字段。

### T5 · 幂等、取消、补偿（G-05、E-01、C-17）

**文件**：基线 §25.9、§25.10、§25.11
**写什么**：
1. 幂等：`operation_id = hash(turn_id, step_id, tool_id, args_hash)`；重放命中返回既有 receipt，不重复执行；账本保留期与清理条件。
2. 取消：运行中取消的两案二选一并说明取舍——**A 案**：八态内 `EXECUTING→CANCELLED` 加迁移（改 §15.2.1）；**B 案**：`activity` 增 `cancelling` 子值、终态仍 `CANCELLED`。必须选一，**不得同时保留**；选定后写 ack、强杀时限、终态票据。
3. 补偿：`side_effects` 分类（可逆／不可逆／外部计价），可逆项必须有 `compensator`；补偿失败进 `BLOCKED` 并留事件。

**验收（Gate T5）**：幂等键计算式可复算；取消方案唯一且迁移表闭合（或无不可达状态）；补偿三类清单齐、每类给失败处置；三处都能指到条文。
**禁止**：同时写两套取消方案；把"取消"写成"停止轮询"这种含糊表述。

### T6 · 总验收

**文件**：本单自证粘贴（写入报告，不新增文档）
**验收（Gate T6）**：11 条发现逐条有章节落点与判据；新增章节编号连续、附录 A 记一行；基线 diff 仅在 §二十五 与附录 A；树/详解页改动只限 desc 与对应小节；无任何新数值。
**禁止**：借修复之名扩范围（如顺手改 E-02 的预算值）。

---

## 4. 开源替代排查

契约设计不引第三方库。若 T4 需要参考现成 ABI 形态，仅允许"参考形态、不引依赖"，候选：MCP 规范（模型上下文协议）、OpenAI function-calling schema、LiteLLM 工具注册。**不做选型结论。**

---

## 5. 粘贴模板

```
T1 完成｜§25.1/§25.2｜信封8字段齐、speak成对、mem三契约齐
T2 完成｜§25.3/§25.4｜唯一compose、七分区、三态可判
T3 完成｜§25.5/§25.6｜schema齐、步骤状态机闭合、submit_plan三段齐
T4 完成｜§25.7/§25.8｜dispatch三段、SPI五动词、idempotency可追
T5 完成｜§25.9-25.11｜幂等式可复算、取消方案唯一(A/B)、补偿三类
T6 总验收｜11/11 有落点有判据；无新数值；越界=无
```

---

## 6. 修订记录

| 版本 | 时间 | 变更 |
|---|---|---|
| v1.0 | 2026-11-13 | 首建，承接 0056 主链 11 条 |
