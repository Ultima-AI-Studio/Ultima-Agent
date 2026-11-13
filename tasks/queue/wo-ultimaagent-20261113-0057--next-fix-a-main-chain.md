# Codex 工单 · wo-ultimaagent-20261113-0057（修复 A：主链闭合）

> 版本：v1.3（按 0060 第 3 轮打回修订）｜ 状态：待重审 ｜ 执行端：Codex ｜ 推理强度：high
> 覆盖：C-01、G-03、G-04、H-01、C-02、C-03、C-05、G-05、E-01、C-17、C-18（11 条）
> **执行序**：本单在 0058 之后执行（0058 先定 §16.4 预算公式），不得与 0058/0059 并发。

---

## 0. 现状校准与裁决项

| 事实 | 值 |
|---|---|
| 来源 | 0056 净新增 36 条中的 11 条 |
| 唯一主文归属 | composer 主文＝本单 §25.3；dispatch 时序主文＝本单 §25.7；取消映射主文＝本单 §25.10 |
| 不写 | §16.4 预算公式（0058）；policy API（0059）；habit API（0059） |

**待 Owner 裁决项（未裁决前对应 Gate 判 SKIP，不得自行填值）**

| 编号 | 裁决内容 | 影响 T |
|---|---|---|
| D-01 | 取消实现形态：A 新增 `EXECUTING→CANCELLED` 迁移 / B `activity=cancelling`＋终态 `CANCELLED` | T5 |
| D-02 | 强杀时限（秒） | T5 |
| D-03 | 决策三态判定阈值（clarify/refuse 的触发线） | T2 |

---

## 0.1 裁定授权（2026-11-13 Owner 授权，优先于本单所有"待 Owner 裁决／未裁决判 SKIP"表述）

Owner 明确：技术取值不必逐个由本人拍板，**交执行端在执行阶段补全并落依据**。因此：

1. **D-01／D-02／D-03 由本单执行者自行裁定**，不再"未裁决即 SKIP"；本单内相关分支改为**裁定并写依据后按 PASS/FAIL 判**。
2. **裁定优先级**：既有裁决（R-56~R-80、§十五 八态、§二十一 超时/重试既有值）＞ 可复现实测 ＞ 保守默认（不动八态、不改 v1 冻结参数、不新增承诺）＞ 本单提案。
3. **每条 D 写三件事**：选中案、依据、影响面。
4. **禁止**编造未实测数值；**不解除**"不改 v1 冻结参数""不新增产品承诺"两条硬边界。
5. 确需实测而无条件时写 `TBD-<D编号>`＋附录 A 一行，其余照常完成。

**保守取向建议（非强制）**：D-01 优先不改八态（若 `activity` 表达可落终态则取 B，否则取 A 且仅加 1 行迁移）｜D-02 直接引 §二十一 既有超时，不新定｜D-03 优先复用 §16 既有 decision 阈值，缺则按"槽位缺失→clarify、命中毒化/高风险→refuse"落最小规则。

---

## 1. 范围冻结

**只做**：基线新增 §二十五（§25.1–§25.11），11 条契约；同步详解页 §03/§04 对应小节、架构树"任务编排/上下文"2 个节点 desc。

**不做**：不实现代码；不改任何数值（预算公式归 0058）；不定义 policy.check / habit.* 的 API 本体（归 0059）；不新增八态以外状态（除非 D-01 选 A）。

**执行时写入域（allowlist，越界即失败）**：
1. `docs/specs/next-感知交互参数基线-20261113.md`：仅新增 §二十五 ＋ 附录 A 一行。
2. **条件写入**：`§15.2.1`，仅当 D-01 选 A 时新增一条迁移行（`EXECUTING → CANCELLED`），其他任何改动禁止。
3. `docs/tracker/next-基础能力架构-20261113.html`：仅 §03、§04 两小节的契约摘要行。
4. `docs/tracker/北极星架构树.html`：仅"任务编排""上下文装配"两节点 `desc`。

---

## 2. 任务清单

| 任务 | 关闭 | 产出 | 机检锚点 |
|---|---|---|---|
| T1 | C-01、C-18 | §25.1 信封、§25.2 Core↔Memory | 字段集合比对＋错误码唯一性计数 |
| T2 | G-03、G-04 | §25.3 composer（唯一主文）、§25.4 三态 | composer 全文仅 1 处定义＋三态枚举 3 值 |
| T3 | H-01、C-02 | §25.5 plan schema、§25.6 submit_plan | plan 字段集合＋状态映射到八态 |
| T4 | C-03、C-05 | §25.7 dispatch（时序主文）、§25.8 SPI | 三段 schema 字段集合＋时序 5 步 |
| T5 | G-05、E-01、C-17 | §25.9 幂等、§25.10 取消、§25.11 补偿 | 幂等键公式可复算＋取消映射表全覆盖 |
| T6 | 总验收 | 自证 | 11 编号→章节 allowlist 表齐 |

---

## 3. 任务明细（三段式）

### T1 · 对话信封与记忆确认（C-01、C-18）

**文件**：基线 §25.1、§25.2；详解页 §03
**写什么**：
1. `turn.envelope` 字段表：`turn_id`、`session_id`、`speaker`、`asr_conf`、`intent`、`deadline`、`cancel_token`、`trace_id`。**`trace_id` 只写"沿用既有 trace 契约（引基线 §21.4 与缺口复核 D3）"，不重定义**。
2. `speak.request` / `speak.receipt` 成对定义：播报文本上限**引 §十六 profile**，不另定值；抢占规则；`duck` 请求字段。
3. Core↔Memory：`mem.read`（超时→返回空并降级，不阻塞）、`mem.write`（幂等键＝`turn_id + memory_id`；重试上限引 §21.6）、`mem.commit_ack`（写后确认＋回滚标记）。
4. 错误码表：`MEM_TIMEOUT`／`MEM_WRITE_CONFLICT`／`MEM_FULL`（后者处置指向 0058 的 §17 定稿，不在此定策略）。

**验收（Gate T1）**：
1. 信封字段表恰好 8 行，字段名与本清单逐字一致（脚本比对字段集合）。
2. speak 请求与回执字段名互为子集，无孤立字段。
3. 三契约各含「入参／出参／错误码／超时来源／幂等」五列，缺列即失败。
4. `trace_id` 只出现在 §25.1 字段表 1 行、且该行含"引既有契约"字样；本单新增段落内**不得出现 `trace_id` 的类型/覆盖面定义行**（脚本按行正则 `trace_id\s*[:：]\s*` 计数＝0）。

**禁止**：重定义 trace 字段；写死播报字数/超时秒数。

### T2 · 上下文装配（唯一主文）与决策三态（G-03、G-04）

**文件**：基线 §25.3、§25.4；详解页 §04
**写什么**：
1. `context.compose` 为**唯一装配入口**，分段七区：`system`／`policy`／`memory.hot`／`habit`／`session.recent`／`tool.schema`／`user.turn`，每区给"内容来源＋截断位次"，**预算只写"由 §16.4 公式给出 input_budget（0058 产出），本区取其中一份额，份额表见 §16.4"**，不在此写数字。
2. 截断顺序表（先丢 `tool.schema` 尾部 → `session.recent` 最旧 → …）与事件 `context_over_budget`（必留）。
3. **hab.it 唯一 caller 声明**：`context.compose` 每轮调 `habit.read`（API 本体在 0059 §26.11，本单只声明调用关系）。
4. 隐私裁剪：外部主脑调用前，`policy` 与 `memory.hot` 中标记为不可外发区不得进入 payload（引 §23.6 三闸）。
5. 三态 `execute`／`clarify`／`refuse`：各给输出结构与必填字段；**判定阈值写 `D-03` 占位**，裁决后回填。

**验收（Gate T2）**：
1. 全文 `context.compose` 的定义段出现次数＝1；出现"第二处 composer"即失败（脚本计数）。
2. 七区分区名逐字出现且各有"来源＋截断位次"两列。
3. `habit.read` 的 caller 声明恰好 1 处，且指向 §26.11。
4. 三态枚举恰好 3 个值；`D-03` 占位符存在；**全文不含 `视情况`、`合理`、`适当`**（脚本判定）。

**禁止**：写任何预算数字；把压缩算法写进本 T。

### T3 · 计划编排与计划交接（H-01、C-02）

**文件**：基线 §25.5、§25.6；架构树"任务编排"desc
**写什么**：
1. `plan.schema`：`plan_id`、`goal`、`steps[]`（`step_id`、`tool`、`args`、`depends_on`、`acceptance`、`compensator`）、`budget_ref`、`owner_turn`。
2. 步骤状态机 5 态 `PENDING/READY/RUNNING/DONE/FAILED` ＋ **映射表：每态→八态之一**（`RUNNING→EXECUTING`、`FAILED→FAILED` 等），未列映射即拒。
3. `console.submit_plan`：请求、受理回执、拒绝码 `DOR_FAIL`／`DUP_PLAN`／`BUDGET_EXCEED`，拒绝后回写 Core 的字段。
4. **取消**：本 T 只写"计划级取消见 §25.10"，不定义传播逻辑。

**验收（Gate T3）**：
1. plan **顶层字段 5 个**（`plan_id/goal/steps[]/budget_ref/owner_turn`）＋ `steps[]` **子字段 6 个**（`step_id/tool/args/depends_on/acceptance/compensator`），逐字一致（脚本比对）。
2. 步骤 5 态每态都有一行八态映射；映射值只能取自基线 §15.2.1 的八个 code（脚本比对枚举）。
3. `submit_plan` 三段（请求/回执/拒绝码 3 个）齐全。
4. 架构树该节点 `desc` 含 `§25.5`。

**禁止**：在这里重复取消传播规则；新增任务状态。

### T4 · 派发时序（主文）与执行器 SPI（C-03、C-05）

**文件**：基线 §25.7、§25.8
**写什么**：
1. **冻结时序** `prepare → policy.check → start → stream* → finalize`，并写明"任何副作用必须发生在 `policy.check` 之后"；`policy.check` 的 API 本体归 0059 §26.7，本单只锁时序与调用点。
2. 三段报文：`dispatch.request`（`plan_id/step_id/tool_id/args/idempotency_key/deadline/sandbox_profile`）→ `dispatch.run`（`run_id/pid/stdout_ref/stderr_ref`）→ `dispatch.receipt`（`exit`、`artifacts[]`、`side_effects[]`、`usage`、`idempotency_key` 五字段，其中 `idempotency_key` 回带以便对账）。
3. SPI 五动词 `prepare/start/stream/cancel/finalize`，每动词给签名与幂等要求。
4. `tool_id` 命名规则与 `requires_policy` 标记；schema 来源引注册分类 §②。

**验收（Gate T4）**：
1. 时序 5 步逐字出现且顺序正确（脚本按序匹配）。
2. 三段报文各附 ```json 围栏���段（字段名可脚本抽取比对），无围栏即失败。
3. 五动词各有一行签名；`idempotency_key` 在 request 与 receipt 两处都出现。
4. 全文不出现"工具可绕过 dispatch 直连"的表述。

**禁止**：在 SPI 里塞平台相关字段；在此定义 policy 规则内容。

### T5 · 幂等、取消（统一映射）、补偿（G-05、E-01、C-17）

**文件**：基线 §25.9–§25.11
**写什么**：
1. 幂等：`operation_id = sha256(turn_id|step_id|tool_id|args_hash)`（给出复算示例一行），命中即返回既有 receipt；账本保留期引 §21.6。
2. **统一取消映射表**（唯一主文）：`plan → steps → run` 三级，每级给取消触发、ack 时限（引 D-02）、终态、已 DONE 步骤处置；取消形态二选一由 **D-01** 决定，本 T 写两个"待裁决块"但**不得同时生效**（用 `IF D-01=A/B` 标记）。
3. 补偿：`side_effects` 三类（`reversible`／`irreversible`／`external_billing`），可逆项必须有 `compensator`；补偿失败进 `BLOCKED` 并留事件 `compensate_failed`。

**验收（Gate T5）**：
1. `operation_id` 公式含 4 个输入且可复算（脚本按公式算 1 例比对）。
2. 取消映射表 3 行（plan/step/run）齐全；`IF D-01=` 字样出现 2 处（A/B 块）；未裁决时 Gate 判 SKIP 并在报告标注。
3. 三类 side_effect 逐字出现，每类有一行处置；`compensate_failed` 出现 1 次。
4. 若 D-01=A，则 §15.2.1 新增迁移恰好 1 行（脚本 diff 计数＝1）；若 B，则 §15 无改动。

**禁止**：同时让 A/B 两案生效；写死强杀秒数；在 T3/T4 重复取消规则。

### T6 · 总验收

**文件**：自证（报告内）
**验收（Gate T6）**：
1. 附**固定 allowlist 表**：11 个编号 → 章节号 ＋（如涉及）HTML 节点 `name` 字段值，一一对应，行数＝11。
2. 脚本核对：**放行集合＝§二十五 ∪ {附录 A 恰 1 行} ∪ {D-01 选 A 时 §15.2.1 的 1 行迁移}**；新增行必须全部落在该集合内（集合外任何行即失败）；`§15.2.1` 变更行数 ∈ {0,1} 且与 D-01 一致。
3. 详解页改动行数 ≤ 6（§03/§04 各 ≤3）；架构树 `desc` 改动节点数＝2。
4. 全文编号无跳号：§25.1–§25.11 连续。

**禁止**：借修复扩范围；把未裁决项写成已定值。

---

## 4. 开源替代排查

不引依赖。若需参考 ABI 形态，仅"参考形态不引库"：MCP、OpenAI function schema、LiteLLM。

---

## 5. 粘贴模板

```
T1｜§25.1/25.2｜8字段/三契约五列/trace引既有
T2｜§25.3/25.4｜composer=1处/七分区/三态+D-03占位/含糊词0
T3｜§25.5/25.6｜顶层5+子字段6/5态映射八态/三段齐
T4｜§25.7/25.8｜时序5步/schema围栏3段/五动词
T5｜§25.9-25.11｜幂等式可复算/取消3行+D-01两案/补偿三类
T6｜11/11 allowlist齐；diff合规；§25连续
```

---

## 6. 修订记录

| 版本 | 时间 | 变更 |
|---|---|---|
| v1.0 | 2026-11-13 | 首建 |
| v1.1 | 2026-11-13 | 按 0060 打回：composer/dispatch/取消各定唯一主文；删`视情况`；阈值改 D-03 占位；取消 A/B 交 D-01；扩写域仅条件允许 §15.2.1 一行；补 T6 allowlist 与机检锚点 |
| v1.2 | 2026-11-13 | 按 0060-r2 打回：T3 改"顶层 5＋子字段 6"；T4 receipt 补 `idempotency_key` 与 Gate 对齐；T6 全称 diff 门加 §15.2.1 条件例外；T1 `trace_id` 补段落/次数/正则 |
| v1.3 | 2026-11-13 | 按 0060-r3 打回：任务表 T4 改"5 步"；T6 放行集合补附录 A 1 行；粘贴模板改"顶层 5＋子字段 6" |
