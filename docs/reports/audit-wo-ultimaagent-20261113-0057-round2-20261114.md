# wo-ultimaagent-20261113-0067 · 0057 执行结果独立审计（round 2）

> 审计对象：`wo-ultimaagent-20261113-0057`；执行方报告只作对照，不作为通过证据。
> 执行纪律：T1→T6；本文件是本单唯一新增文件。

## §1 结论

**有条件通过（修复后再冻结）**：0057 卡 11 编号实测为已堵 8／半堵 3／未堵 0，但 G-03/G-05/C-17 尚缺可消费契约要素（§4.2），原 0057 T6 有四个确定性 Gate 失败（§5.3），且 §25.11 L1763 与 §15.2.1 L571–585 构成 S-003 状态不可达矛盾（§6.2 #4）；完成这些有界修复前不得冻结。

## §2 审计基线（commit 与 diff 留证）

### 2.1 执行前、执行后对象

- 执行前对象取法：读取 `tasks/queue/runs/wo-ultimaagent-20261113-0057-20261113T152402246487Z/before.json` 的 `tree.base_sha`，实测为 `37e9cf28742dbfcc4b1f01d6a5eec1efa5f87b6e`。
- `dispatch-record.json` 没有冻结提交：原文片段为 `"freeze_commit": null`，且 `"dispatched_at": null`。
- 执行完成时 commit 取 run-local `done.json.end_sha`：`3ad0ea5521f0b309e8c53bafdad770132ad8ce36`；当前审计时 `HEAD=e453557d1540f702ffa01024d8e684911a206180`，用于记录审计时状态，不能替代 run-local after。
- 对象校验原始输出：

```text
37e9cf28742dbfcc4b1f01d6a5eec1efa5f87b6e    commit
3ad0ea5521f0b309e8c53bafdad770132ad8ce36    commit
HEAD                                        commit
```

重要限制：0057 没有独立提交。无论使用 run-local after `3ad0ea55…` 还是当前 `HEAD`，目标文件的 commit→commit diff 均无输出；0057 结果只存在于执行后工作树。故以下“实际 diff”使用派发前真实 commit 对当前工作树，不能把工作树冒充为 after commit。

### 2.2 执行后 Git 与基线实测

`git log --oneline -n 3`：

```text
e453557d docs(review): 0066 骨架评审不通过 — 队列写口双主/补偿落 BLOCKED 无迁移/Core 执行顺序重叠 三条经核实
b1a89e21 docs(review): 0065 归属评审有条件通过（M7/cancel_observe 改判），方案 v0.3 回写 §11 并修 U-01，0062 v1.1 改指针式
3dd890b4 chore(queue): 建 0065（Autoloop 模块归属评审）/0066（骨架设计评审）两卡并登记，队列 183→185
```

`git status --porcelain=v1` 与本审相关的精确条目（仓库另有大量既存脏项，不归本单）：

```text
 M docs/specs/next-感知交互参数基线-20261113.md
?? docs/reports/fix-wo-ultimaagent-20261113-0057.md
?? tasks/queue/wo-ultimaagent-20261113-0067--audit-0057-main-chain.md
```

基线当前实测：

```text
Lines=1792
Length=141820 bytes
SHA256=3FE9B80F25E0B75E42191C8C6343AF98EA4B51BA529457F97A48C9770A894C52
LastWriteTimeUtc=2026-11-13T15:37:00Z
```

### 2.3 实际 diff 全文

命令：

```powershell
& 'C:\Program Files\Git\cmd\git.exe' diff --unified=0 37e9cf28742dbfcc4b1f01d6a5eec1efa5f87b6e -- 'docs/specs/next-感知交互参数基线-20261113.md'
```

原始输出（两个 hunk 头全部保留；`git diff --numstat` 实测 `232  0`）：

```diff
diff --git a/docs/specs/next-感知交互参数基线-20261113.md b/docs/specs/next-感知交互参数基线-20261113.md
index 536cf022..0801cbe3 100644
--- a/docs/specs/next-感知交互参数基线-20261113.md
+++ b/docs/specs/next-感知交互参数基线-20261113.md
@@ -576,0 +577 @@
+| `EXECUTING` | `CANCELLED` | D-01=A：取消级联已确认，或强杀回收已取得终止凭据 |
@@ -1534,0 +1536,231 @@ Console 若自己 `CreateProcess` 起看门狗，就成了**第二个父进程**
+## 二十五、主链可执行契约（wo-ultimaagent-20261113-0057）
+
+> 本章只闭合 Voice → Core → Memory → Console → Executor 的主链 ABI/SPI；不改 v1 冻结参数，不新增产品承诺。预算、容量与职责分别引用 §16.4、§17.2.3、`docs/specs/next-双域分离与开工设置规范.md` §11.3.1 的唯一现行口径。
+
+### 25.1 Voice ↔ Core 回合与播报信封（C-01）
+
+**`turn.envelope` 字段表（字段集合封闭，发送方不得夹带未登记字段）**
+
+| 字段 | 必填 | 来源 | 契约 |
+|---|---|---|---|
+| `turn_id` | 是 | Voice | 单回合唯一标识；同一回合重放保持不变 |
+| `session_id` | 是 | Voice / Core 会话管理 | 归属会话标识 |
+| `speaker` | 是 | Voice | 说话方标识 |
+| `asr_conf` | 是 | Voice | ASR 原始置信信息；Core 不改写 |
+| `intent` | 是 | Core | 结构化意图；进入三态判定前可为空值 |
+| `deadline` | 是 | Voice / Core | 绝对截止时刻；消费方不得延长 |
+| `cancel_token` | 是 | Core | 本回合取消令牌；沿链透传 |
+| `trace_id` | 是 | 既有观测链 | **引既有契约**：沿用 §21.4 与缺口复核 D3，不在本章重定义 |
+
+**`speak.request` / `speak.receipt` 成对信封**
+
+| 信封 | 字段集合 | 发送方 → 接收方 | 约束 |
+|---|---|---|---|
+| `speak.request` | `turn_id, text, profile, interruptible, duck, outcome` | Core → Voice | `text` 上限只引 §十六对应 profile；`duck` 为请求字段；`outcome` 固定为 `pending` |
+| `speak.receipt` | `turn_id, text, profile, interruptible, duck, outcome` | Voice → Core | 原样回带请求字段；`outcome` 回写 `completed/preempted/rejected` 之一，回执字段集合与请求一致 |
+
+抢占规则：更新的回合、当前回合的取消令牌或 §八的用户插话均可抢占；Voice 必须先执行既有停播、flush、cancel、回滚闸，再回 `preempted`。`duck` 只请求客户端执行既有媒体 duck 策略，不在本章重定比例或恢复时延。
+
+### 25.2 Core ↔ Memory 读写确认（C-18）
+
+| 契约 | 入参 | 出参 | 错误码 | 超时来源 | 幂等 |
+|---|---|---|---|---|---|
+| `mem.read` | `turn_id, session_id, query, deadline` | `items[], degraded` | 见本节错误码表 | 沿用调用信封 `deadline`；到期返回 `items=[]`、`degraded=true`，不得阻塞主链 | 同一 `turn_id + query` 重放只读，不产生写副作用 |
+| `mem.write` | `turn_id, memory_id, payload, deadline` | `write_version` | 见本节错误码表 | 沿用调用信封 `deadline` | 幂等键为 `turn_id + memory_id`；重试上限引 §21.6，达到既有门即停止重试 |
+| `mem.commit_ack` | `turn_id, memory_id, write_version, rollback_marker, deadline` | `committed, rollback_marker` | 见本节错误码表 | 沿用调用信封 `deadline` | 复用 `turn_id + memory_id`；重复确认返回同一写入版本与回滚标记 |
+
+`mem.commit_ack` 是写后确认：`committed=true` 才允许 Core 把该写入视为可见；失败或取消时必须回带 `rollback_marker`，供 §21.5 检查点回退定位，不声称撤销已经发生的外部副作用。
+
+| 错误码 | 唯一定义 | 处置 |
+|---|---|---|
+| `MEM_TIMEOUT` | 读写或确认超过信封截止时刻 | 读返回空且降级；写/确认保持未提交并按既有重试门处理 |
+| `MEM_WRITE_CONFLICT` | 同一幂等键对应的 payload 或版本不一致 | fail-closed，拒绝覆盖，保留原 receipt |
+| `MEM_FULL` | 当前登记卷不可写 | 处置只认 0058 已定稿的 §17.2.3，不在本章另定容量或无丢失承诺 |
+
+### 25.3 上下文装配唯一入口（G-03）
+
+**`context.compose` 是唯一装配入口**。任何调用方只能提交分区素材，不得自行拼接主脑 payload。输入总预算只取 0058 已定稿的 §16.4 公式 `input_budget(profile)`；§16.4 没有分区份额表，本章不虚构份额或预算数字，各分区只能在该次请求的动态总预算内参与截断。
+
+| 分区 | 内容来源 | 截断位次 |
+|---|---|---|
+| `system` | 已冻结的系统指令与运行边界 | 保留位；不可截断 |
+| `policy` | 治理⑤当前生效规则及版本引用 | 保留位；不可截断 |
+| `memory.hot` | Memory 按本轮查询返回的热记忆切片 | 第 4 位：按相关性从低到高移除 |
+| `habit` | Memory 中已确认且未撤销的习惯条目 | 第 3 位：先移除与当前意图最远的条目 |
+| `session.recent` | 当前会话最近回合 | 第 2 位：从最旧回合开始移除 |
+| `tool.schema` | 注册分类 §② 当前候选工具 schema | 第 1 位：先移除尾部非候选 schema，再裁剪说明文本 |
+| `user.turn` | 当前用户原始回合与结构化意图 | 保留位；不可截断 |
+
+截断严格按第 1→4 位执行；保留位仍不能装入动态总预算时，拒绝发送 payload 并必留事件 `context_over_budget`，事件至少含 profile、实际 token、预算与被裁分区，不把超预算静默改写成成功。
+
+**habit 唯一调用关系**：本入口每轮调用一次 `habit.read`，API 本体只引用 0059 的 §26.11；其他模块不得成为 caller。
+
+**外发前隐私裁剪**：目标为外部主脑时，按 §23.6 三闸先检查分区素材；标记为不可外发的治理规则内容与热记忆切片不得进入 payload。该裁剪发生在 tokenizer 计量之前，裁掉的内容不以摘要、编码或工具参数形式旁路外发。
+
+### 25.4 决策三态与 D-03 判定（G-04）
+
+**封闭枚举**：`clarify / proceed / refuse`。卡内写项曾使用 `execute`，但 Gate 明定本枚举为这三个值；本章以 Gate 的封闭集合为准，`proceed` 表示准许进入计划链，不新增第四值。
+
+| decision | 必填输出字段 | D-03 触发谓词 | 后续动作 |
+|---|---|---|---|
+| `clarify` | `decision, turn_id, missing_fields[], question, reason_code` | 未命中拒答，且必填槽缺失，或仍有互斥意图无法唯一选定 | 只发澄清问题，不建计划、不派发 |
+| `proceed` | `decision, turn_id, intent, slots, plan_handoff` | 未命中拒答，必填槽齐全且意图唯一 | 交 §25.5 建计划 |
+| `refuse` | `decision, turn_id, reason_code, user_message, policy_ref` | 命中当前生效策略的拒绝规则、§23.6 不可外发边界、poison guard，或既有高风险规则要求拒绝 | 不建计划；回传可审计的规则引用与面向用户说明 |
+
+D-03 裁定为上述确定性谓词，不引入未经实测的数值阈值；优先级固定为 `refuse > clarify > proceed`。输出字段缺失、枚举外取值或无法取得生效规则版本时一律 fail-closed，不得降格为放行。
+
+### 25.5 计划 schema 与步骤状态（H-01）
+
+**`plan.schema` 顶层字段（封闭集合 5 项）**
+
+| 字段 | 必填 | 契约 |
+|---|---|---|
+| `plan_id` | 是 | 计划唯一标识；重提同一计划时保持不变 |
+| `goal` | 是 | 已确认、可验收的目标陈述 |
+| `steps[]` | 是 | 非空有序步骤集合；元素只取下表字段 |
+| `budget_ref` | 是 | 指向 §16.4 动态预算与治理⑤用量规则的引用，不内嵌预算数字 |
+| `owner_turn` | 是 | 产生该计划的回合标识 |
+
+**`steps[]` 子字段（封闭集合 6 项）**
+
+| 字段 | 必填 | 契约 |
+|---|---|---|
+| `step_id` | 是 | 计划内唯一；依赖图引用此值 |
+| `tool` | 是 | 候选能力逻辑名；派发前解析为已登记工具标识 |
+| `args` | 是 | 必须通过所选工具 schema 校验的参数对象 |
+| `depends_on` | 是 | 仅引用同计划步骤；空数组表示无前置依赖；成环拒绝 |
+| `acceptance` | 是 | 可机检的完成判据与证据引用要求 |
+| `compensator` | 是 | 可逆副作用的补偿器引用；无副作用时显式为空值 |
+
+步骤状态是 plan 内部投影，不是第九种队列状态。每个步骤只允许以下五值，向 §15.2.1 八态投影时必须逐行命中；枚举外状态或缺映射一律拒绝。
+
+| 步骤状态 | 对应八态 | 投影条件 |
+|---|---|---|
+| `PENDING` | `QUEUED` | 依赖尚未全部完成 |
+| `READY` | `QUEUED` | 依赖已满足，尚未启动 |
+| `RUNNING` | `EXECUTING` | 已取得 run 并在执行 |
+| `DONE` | `SELF_CHECK` | 步骤 receipt 已齐，等待 acceptance 自检；计划通过后仍按八态后续门推进 |
+| `FAILED` | `FAILED` | 执行或 acceptance 失败；重试与阻塞只认 §21.6 |
+
+### 25.6 Console 计划交接（C-02）
+
+**`console.submit_plan` 请求**
+
+| 字段 | 必填 | 约束 |
+|---|---|---|
+| `plan` | 是 | 完整对象必须通过 §25.5 字段、依赖图和步骤状态校验 |
+| `idempotency_key` | 是 | 同一 `plan_id + owner_turn` 重提保持不变 |
+| `submitted_by` | 是 | 只接受职责表允许的 Core/主脑本地事务调用方 |
+
+**受理回执**
+
+| 字段 | 必填 | 约束 |
+|---|---|---|
+| `submission_id` | 是 | 本次受理记录标识 |
+| `plan_id` | 是 | 原样回带 |
+| `queue_state` | 是 | 首次受理只能为 `QUEUED` |
+| `accepted_at` | 是 | Console 受理时刻 |
+
+**拒绝码与回写 Core 字段**
+
+| 拒绝码 | 触发 | 回写字段 |
+|---|---|---|
+| `DOR_FAIL` | DoR、schema、依赖图或 acceptance 不完整 | `plan_id, reason_code, failed_fields[], retryable` |
+| `DUP_PLAN` | 同一计划标识对应不同内容，或已存在非幂等提交 | `plan_id, reason_code, existing_submission_id, retryable` |
+| `BUDGET_EXCEED` | 计划引用的预算在当前生效规则下不可受理 | `plan_id, reason_code, budget_ref, retryable` |
+
+拒绝后 Console 不落 `EXECUTING`，Core 根据结构化回写重新进入 §25.4；计划级取消只引用 §25.10，本节不定义传播逻辑。
+
+### 25.7 派发 ABI 与冻结时序（C-03，时序唯一主文）
+
+冻结时序只有一条：`prepare → policy.check → start → stream* → finalize`。任何副作用必须发生在 `policy.check` 返回结构化放行之后；拒绝、超时或无规则版本均不得进入 `start`。该治理 API 本体只引用 0059 §26.7，本节只锁调用点和先后关系。
+
+**`dispatch.request`**
+
+```json
+{
+  "plan_id": "",
+  "step_id": "",
+  "tool_id": "",
+  "args": {},
+  "idempotency_key": "",
+  "deadline": "",
+  "sandbox_profile": ""
+}
+```
+
+**`dispatch.run`**
+
+```json
+{
+  "run_id": "",
+  "pid": null,
+  "stdout_ref": "",
+  "stderr_ref": ""
+}
+```
+
+**`dispatch.receipt`**
+
+```json
+{
+  "exit": {},
+  "artifacts[]": [],
+  "side_effects[]": [],
+  "usage": {},
+  "idempotency_key": ""
+}
+```
+
+请求中的幂等值必须按 §25.9 生成，receipt 原样回带以便对账；run 只返回执行身份与标准流引用，完成事实只认 receipt。`deadline` 到期后不得开启新副作用，已发生项按 §25.10–§25.11 收口。
+
+### 25.8 执行器 SPI（C-05）
+
+| 动词 | 签名 | 出参 | 幂等要求 |
+|---|---|---|---|
+| `prepare` | `prepare(request) -> prepared` | 校验后的 `prepared`，含解析后的工具注册与沙箱引用 | 同一幂等值和请求摘要返回同一 prepared；冲突摘要拒绝 |
+| `start` | `start(prepared) -> run` | §25.7 的 run 对象 | 同一幂等值至多创建一个 run；重放返回既有 run |
+| `stream` | `stream(run_id, cursor) -> chunks[]` | 从 cursor 开始的有序增量块 | 相同 run 与 cursor 返回相同块，不推进服务端隐式游标 |
+| `cancel` | `cancel(run_id, cancel_token) -> cancel_ack` | 带 run、接收时刻和终止观察结果的确认 | 重放返回同一确认；ack 与强杀截止只认 D-02 / §25.10 |
+| `finalize` | `finalize(run_id) -> receipt` | §25.7 的最终 receipt | 同一 run 只能固化一个 receipt；重复调用返回原对象 |
+
+`tool_id` 命名规则为 `<provider>.<capability>.<name>@<major>`：各段只用登记表中的小写 ASCII 标识，major 必须与注册 schema 主版本一致。注册项必须带布尔标记 `requires_policy`；无论取值为何都执行 §25.7 的治理调用，false 只允许治理端返回“无需附加规则”的结构化放行，不构成旁路。
+
+工具 schema 来源只认注册分类 §② 的当前生效版本；执行器不得接受调用方内嵌的替代 schema。五个 SPI 签名保持跨平台，除 §25.7 已冻结的 run 身份字段外，不加入 Windows/Linux 专属句柄、路径或 Job 字段。
+
+### 25.9 幂等键与 receipt 账本（G-05）
+
+唯一公式：`operation_id = sha256(turn_id|step_id|tool_id|args_hash)`，其中 `args_hash = sha256(canonical_json(args))`；canonical JSON 必须使用 UTF-8、键名排序、无非语义空白，散列输出为小写十六进制。四个输入均不得省略、换序或二次拼接分隔符。
+
+可复算例：`args={}` → `args_hash=44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`；取 `turn_id=turn-001`、`step_id=step-01`、`tool_id=local.fs.read@1`，则散列原文为 `turn-001|step-01|local.fs.read@1|44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a`，结果 `operation_id=f35010535bebbfaf22f46e9f560bb923d17ccf2bc979cfe0b1624a4bd42b555c`。
+
+账本以 operation 标识为唯一键：首次调用写入请求摘要、run 与最终 receipt；再次命中且请求摘要一致时直接返回既有 receipt，不重放副作用；摘要不一致时报幂等冲突并拒绝覆盖。§21.6 只规定 retry/rework 上限，没有时间制保留期，因此本章不伪造时长；账本在关联 retry/rework 尚未终结时不得清理，具体静态保留期记 `TBD-G05-RETENTION`。
+
+### 25.10 统一取消映射（E-01，取消唯一主文）
+
+**IF D-01=A｜status=selected**：采用既有八态中的直接迁移；§15.2.1 仅补 `EXECUTING → CANCELLED` 一行，不新增状态。收到取消后先标记 `activity=cancelling` 供观测，随后按下表级联并凭 ack 或强杀终止凭据落既有终态。
+
+| 层级 | 取消触发 | ack 时限（D-02） | 终态表达 | 已 DONE 步骤处置 |
+|---|---|---|---|---|
+| `plan` | 用户/brain 取消当前计划，或 owner turn 的取消令牌触发 | 3s 内收齐仍在途 run 的 ack；缺 ack 即进入强杀 | 队列任务在级联闭合后迁移到 `CANCELLED` | 保留完成事实与 receipt，不重跑；有可逆副作用则交 §25.11 |
+| `step` | plan 级联，或当前步骤被显式取消 | 未启动项立即 ack；RUNNING 项 3s 内 ack | 不增第六个步骤状态：保持最后事实状态，另记 `cancel_outcome=cancelled`，向队列投影 `CANCELLED` | `DONE` 保持不变，只按副作用类别决定是否补偿 |
+| `run` | 所属 step 取消后调用执行器 `cancel` | 3s 内返回 cancel_ack；缺 ack 强杀，强杀信号后 3s 内须证明 `ActiveProcesses==0` | 固化 receipt，`exit.reason=cancelled` 并带终止证据 | 已 finalize 的 run 不重复取消，直接回既有 receipt |
+
+取消传播固定为 `plan → steps → run`；每一级 ack 都回带父标识、接收时刻、是否需补偿。强杀只作用于未确认终止的匹配 run 子树，不得扩大到其他计划或共享宿主。
+
+**IF D-01=B｜status=rejected**：只保留 `activity=cancelling` 再落 `CANCELLED` 会被 §15.2.1 的 fail-closed 迁移表拒绝；若绕到 `FAILED/BLOCKED` 又会篡改取消语义，故本案不生效，不得作为实现分支。
+
+### 25.11 副作用补偿（C-17）
+
+receipt 的 `side_effects[]` 每项必须且只能取以下一类；缺类别、类别外取值或可逆项缺补偿器均使 finalize 失败。
+
+| side_effect 类别 | 必填证据 | 取消/失败处置 |
+|---|---|---|
+| `reversible` | 副作用标识、before/after 引用、`compensator` | 逆依赖序调用 compensator；成功回写补偿 receipt |
+| `irreversible` | 副作用标识、外部事实引用、不可逆原因 | 不伪造回滚；停止后继步骤，保留事实并交人工/brain 裁决 |
+| `external_billing` | provider、账单/交易引用、金额与币种来源 | 停止后继扣费；有已登记退款 compensator 才自动调用，否则保留对账项并交人工/brain |
+
+补偿自身使用原 operation 标识派生的唯一补偿键，重复请求返回原补偿 receipt。任一必需补偿失败时，队列落 `BLOCKED`，记录唯一事件 `compensate_failed`，事件带原 run、失败补偿器、已完成补偿清单和人工释放要求；不得把部分补偿表述为原操作已撤销。
+
+---
```

独立复算：hunk 数为 2；目标文件净新增 232 行，其中 §15.2.1 迁移 1 行、§二十五 231 行。执行方 `final.json` 自述“两个 hunk”“+232/-0”仅作对照；与独立命令结果一致。

### 2.4 T1 Gate

- 九段标题：已按 §1→§9 建立。
- before/after commit 对象：均可解析为 `commit`；同时明确 after commit 不承载 0057 工作树改动。
- 实际 diff：两个 hunk 头与全文已留证；commit→commit 空差异也已留证。
- 当前行数与 SHA256：已实测。

`T1_GATE=PASS`

## §3 写入边界复核

### 3.1 口径与命令

0067 卡 T2 正文实际明示 14 个边界对象，另有 §15.2.1 的条件写入断言；其 Gate 写“12 项”与正文枚举不一致。本报告按实际清单逐项统计，不拿预期数覆盖实测。

主要命令：

```powershell
git diff --unified=0 37e9cf28742dbfcc4b1f01d6a5eec1efa5f87b6e -- docs/specs/next-感知交互参数基线-20261113.md
git rev-parse <before>:<path>; git rev-parse <run_end>:<path>; git hash-object -- <path>
Compare before.json.tree.changed_files with done.json.changed_files by path and sha256
Test-Path -LiteralPath 'H:\UltimaAI\UltimaAgentNext'
```

基线 diff 的完整输出已在 §2.3 留证；改变坐标只有 `@@ -576,0 +577 @@` 与 `@@ -1534,0 +1536,231 @@`。因此不落在这两个 hunk 的既有章节与附录均无行级修改。

### 3.2 边界逐项判定

| # | 边界对象 | 判定 | 坐标、原文片段与独立证据 |
|---:|---|---|---|
| 1 | §14.1 | **未改（成立）** | 现行标题在基线 L435：`### 14.1 T8 存储后端`；两个实际 hunk 均不覆盖 L435–469。 |
| 2 | §16.2 | **未改（成立）** | L745：`### 16.2 运行参数`；实际 hunk 不覆盖 L745–774。 |
| 3 | §16.4 | **未改（成立）** | L784：`### 16.4 运行态回读`；实际 hunk 不覆盖 L784–810。0058 已有动态预算正文属于执行前基线，不是 0057 改动。 |
| 4 | §16.5 | **未改（成立）** | L812：`### 16.5 三层规则归属`；实际 hunk 不覆盖 L812–820。 |
| 5 | §17.2.3 | **未改（成立）** | L914：`#### 17.2.3 存储卷与扩容`；实际 hunk 不覆盖 L914–943。 |
| 6 | §二十六（未写） | **未改（成立）** | `rg -n '^## 二十六'` 命中 0；§25.11 后 L1767 直接进入 `## 附录 A`，没有 §26 正文。 |
| 7 | 详解页 `docs/tracker/next-基础能力架构-20261113.html` | **未改（成立）** | Git blob：before=`810ea278…`、run-end=`810ea278…`、当前=`810ea278…`，三者相同。 |
| 8 | 架构树 `docs/tracker/北极星架构树.html` | **未改（成立）** | Git blob：before=`4d5bb259…`、run-end=`4d5bb259…`、当前=`4d5bb259…`，三者相同。 |
| 9 | 注册分类 `docs/plans/next-注册分类-tools-skills-plugins-20261113.md` | **未改（成立）** | Git blob：before=`51415617…`、run-end=`51415617…`、当前=`51415617…`，三者相同。 |
| 10 | 双域规范 `docs/specs/next-双域分离与开工设置规范.md` | **未改（成立）** | Git blob：before=`675d0d3f…`、run-end=`675d0d3f…`、当前=`675d0d3f…`，三者相同。 |
| 11 | 附录 A | **未改（成立）** | L1767 标题仍为 `## 附录 A · 变更记录（全量）`；第二 hunk 恰在附录前结束，diff 中没有附录新增行。注意：0057 卡 T6 要求“附录 A 恰 1 行”，所以“未改”同时构成其 Gate 缺口，详见 §5。 |
| 12 | 代码 | **未改（成立）** | before/done 脏项快照中的既有代码类文件哈希逐项不变，例如 `profile.py=b29069ce…`、`test_profile.py=ed6a69e8…`；done 只新增三条 dirty 路径：基线、`tasks/queue/index.md`、`tasks/queue/queue-status.json`，没有新增代码路径。 |
| 13 | 队列状态／索引 | **被改（越界）** | before 快照无这两条 dirty 路径，done 新增 `tasks/queue/index.md=51344cb0…`、`queue-status.json=b57f73de…`。运行快照中 0057 从 `state: pending, dispatched_at: null` 变为 `state: executing, dispatched_at: 2026-11-13T15:24:02.698255+00:00`，note 也改为真实派发记录。该变化可解释为派发器状态流转，但“文件未改”的字面声明不成立，审计不能替执行方消除越界事实。 |
| 14 | `H:\UltimaAI\UltimaAgentNext` 工程域 | **无法判定** | 按禁令只执行路径存在性判断，`Test-Path=False`；未进入、未枚举、未读取该路径。当前不存在不能证明执行期间从未写入后又删除，故不得判“未改”。 |

边界实际统计：**未改（成立）12／被改（越界）1／无法判定1**。

### 3.3 §15.2.1 条件写入断言

该项是 D-01=A 的授权内条件写入，不纳入上表“未改”边界三态。独立 diff 只有一条：

```diff
@@ -576,0 +577 @@
+| `EXECUTING` | `CANCELLED` | D-01=A：取消级联已确认，或强杀回收已取得终止凭据 |
```

结论：**一致；实测新增 1 行**。该行坐标为现行基线 §15.2.1 L577，且相邻行没有串联改动。

### 3.4 T2 Gate

- 实际清单：14 个边界对象全部判定；§15.2.1 条件断言另列，遗漏 0。
- 哈希／blob／diff／运行快照证据：逐项给出；没有引用执行方自述作为证明。
- §15.2.1：新增行数实测为 1，与 D-01=A 一致。
- 队列边界出现 1 项字面越界，Next 工程域 1 项无法判定；这是被审结果，不影响本审 T2“逐项判定且证据齐全”的完成度 Gate。

`T2_GATE=PASS`

## §4 11 条 BLOCKER 覆盖判定

### 4.1 编号口径

0056 的原始 11 条 BLOCKER 是：`C-01/C-02/C-03/C-05/E-01/E-02/E-04/G-03/G-05/G-08/H-01`（0056 L176–197）。0057 卡的 11 编号则是：`C-01/C-18/G-03/G-04/H-01/C-02/C-03/C-05/G-05/E-01/C-17`（0057 卡 L3–4、L57–64）。两者不是同一集合：0057 纳入了原为 HIGH 的 `C-18/G-04/C-17`，而原 BLOCKER `E-02/E-04/G-08` 归 0058。以下分开判读，最终“11 条覆盖分布”只统计 0057 卡的 11 编号。

### 4.2 0057 卡 11 编号逐条判定

| 编号 | 0056 原始缺口 | §25 坐标与可 grep 判据原文 | 判定 | 独立理由／残余 |
|---|---|---|---|---|
| C-01 | 0056 L193：`Voice↔Core 对话交接断链` | §25.1 L1542：`turn.envelope 字段表（字段集合封闭`；L1559–1560：`speak.request`/`speak.receipt` 同一字段集合 | **已堵** | 8 字段、方向、抢占与回执 outcome 都有封闭可执行判据；`rg -n 'turn\.envelope|speak\.receipt'` 可命中。 |
| C-18 | 0056 L209：`Core↔Memory 失败/确认断链` | §25.2 L1566–1570：`入参 / 出参 / 错误码 / 超时来源 / 幂等` 五列；L1576–1578 三错误码 | **已堵** | `mem.read/write/commit_ack` 均给五列，且 `committed=true` 与 `rollback_marker` 有确认语义。 |
| G-03 | 0056 L176：`上下文装配契约缺失` | §25.3 L1582：`context.compose 是唯一装配入口`；L1584–1592 七分区；L1594 `context_over_budget` | **半堵** | 已补唯一入口、来源、截断、预算与隐私，但没有 `context.compose` 的请求字段、返回字段或 compose receipt；下游无法仅按现文实现调用 ABI。标题与分区表不能替代入出参契约。 |
| G-04 | 0056 L177（原 HIGH）：`澄清/拒答决策缺失` | §25.4 L1602：`封闭枚举：clarify / proceed / refuse`；L1604–1610 逐态必填字段与确定性谓词 | **已堵** | 三态封闭、字段可校验、优先级 `refuse > clarify > proceed` 且缺字段 fail-closed。 |
| H-01 | 0056 L183：`任务编排节点为空壳` | §25.5 L1614：`plan.schema 顶层字段（封闭集合 5 项）`；L1624：`steps[] 子字段（封闭集合 6 项）`；L1637–1643 五态投影 | **已堵** | plan/step 字段、依赖、acceptance、compensator 引用与状态投影均可做集合检查。补偿调用 ABI 的残余归 C-17，不重复扣 H-01。 |
| C-02 | 0056 L194：`Core→Console 计划交接断链` | §25.6 L1647：`console.submit_plan 请求`；L1655 `受理回执`；L1668–1670 `DOR_FAIL/DUP_PLAN/BUDGET_EXCEED` | **已堵** | 请求、受理、拒绝与结构化回写齐，首次受理状态固定为 `QUEUED`。 |
| C-03 | 0056 L195：`Console→Middleware dispatch ABI 缺失` | §25.7 L1676：`prepare → policy.check → start → stream* → finalize`；L1678–1712 三段 JSON | **已堵** | request/run/receipt 三段字段可抽取，receipt 回带幂等键；完成事实只认 receipt。 |
| C-05 | 0056 L197：`executor/tool SPI 缺失` | §25.8 L1719–1725：`prepare/start/stream/cancel/finalize` 五行签名与幂等要求 | **已堵** | 五动词都有签名、出参与重放行为。Middleware→Shell 的 OS 进程桥是 0056-C-04，不把另一缺口重复算到 C-05。 |
| G-05 | 0056 L178：`工具幂等/重放去重缺失` | §25.9 L1733：`operation_id = sha256(turn_id\|step_id\|tool_id\|args_hash)`；L1737：`TBD-G05-RETENTION` | **半堵** | 公式、canonical JSON、命中回旧 receipt 与冲突拒绝均成立，独立复算也得到 `f3501053…b555c`；但静态保留期仍是 TBD，账本何时可安全清理没有 executable oracle，跨清理窗口的重放去重不能闭合。 |
| E-01 | 0056 L184：`运行中取消不可达` | §25.10 L1741：`IF D-01=A｜status=selected`；L1745–1747 plan/step/run 三行；§15.2.1 L577 `EXECUTING → CANCELLED` | **已堵** | 取消触发、3s ack、强杀凭据、终态与 DONE 处置齐；直接迁移已进入 fail-closed 表。 |
| C-17 | 0056 L208（原 HIGH）：`执行部分副作用无补偿契约` | §25.11 L1755：`side_effects[] 每项必须且只能取以下一类`；L1759–1761 三类处置；L1763 `补偿 receipt` | **半堵** | 已有分类、证据、逆序原则、补偿键与失败事件，但没有 `compensator` 调用签名，也没有补偿 receipt 的字段集合/错误码；“成功回写补偿 receipt”仍不足以下游实现接口。 |

0057 卡 11 编号实际分布：**已堵 8／半堵 3／未堵 0**；未判定 0。

### 4.3 0056 原始 BLOCKER 中归 0058 的三项

| 编号 | 0056 原始定义 | 当前坐标 | 本单处理 |
|---|---|---|---|
| E-02 | 0056 L185：`4000 输入+512 输出超过 n_ctx=4096` | §16.4.1 L786–803 已有动态预算裁定 | **不在本单范围，不计入本单判定**；归 0058。 |
| E-04 | 0056 L187：`全卷满时“排队不丢+审计照写”不可能` | §17.2.3 L918–924 已有 B 案裁定 | **不在本单范围，不计入本单判定**；归 0058。 |
| G-08 | 0056 L181：`原子更新/回滚缺失` | §25.1–§25.11 无 staging/A-B 槽/首启健康门主文 | **不在本单范围，不计入本单判定**；归 0058，不能因 §25 有标题而算覆盖。 |

将 0056 原始 11 BLOCKER 按本单范围复算：本单内 8 条为 **已堵 6／半堵 2／未堵 0**，另 3 条明确不计入。

### 4.4 与执行方自述的差异（仅对照）

执行方 `final.json` 自述“11 条 BLOCKER 全部一一闭合”，这里只作对照，不作通过证据。独立逐条 grep 与接口要素复核后，`G-03/G-05/C-17` 均只有标题/主体规则而缺完整可消费要素，改判 **半堵**；因此与执行方自述不一致。

### 4.5 T3 Gate

- 0057 范围 11 编号：逐条判定，遗漏 0；三项范围外原 BLOCKER 逐条标明不计入。
- 所有“已堵”均附基线内可 `rg` 命中的判据原文；三项“半堵”逐条写明缺项。
- 独立判定与执行方自述存在 3 条差异，且证据不依赖执行方报告。

`T3_GATE=PASS`

## §5 每 T Gate 可机检性

### 5.1 判定口径

- **可机检**：对象、扫描范围、阈值／集合和 oracle 足够明确，可用确定性命令直接判 PASS/FAIL。
- **半机检**：可自动抽取一部分，但“定义段／占位状态／涉及哪些 HTML 节点”等仍缺精确 oracle，需要人工解释。
- **不可机检**：缺夹具、阈值、扫描范围或 oracle 到无法形成稳定脚本。

### 5.2 24 个 Gate 子项逐条判定

| Gate 子项 | 原口径摘要 | 判定 | 对应命令／缺口 | 本次实际结果 |
|---|---|---|---|---|
| T1.1 | 信封 8 字段逐字一致 | **可机检** | 解析 §25.1 首表第一列，与固定集合做 set equality | PASS：8 字段齐。 |
| T1.2 | speak 请求/回执字段互为子集 | **可机检** | 解析两行字段集合，断言 A⊆B 且 B⊆A | PASS：两边均为 6 字段。 |
| T1.3 | 三 Memory 契约具五列 | **可机检** | 解析 §25.2 表头和三数据行，断言五列非空 | PASS。 |
| T1.4 | trace 行数 1、冒号重定义 0 | **可机检** | §25 范围 `trace_id` 行计数与正则 `trace_id\s*[:：]\s*` | PASS：`1/0`。 |
| T2.1 | composer 定义段次数 1 | **半机检** | `rg` 可数 `context.compose`，但“定义段”没有 AST/正则定义；同词的引用与定义无法纯计数区分。改造：规定唯一标题或固定声明语法 | 窄口径 PASS：§25 中字面命中 1。 |
| T2.2 | 七区各有来源＋截断位次 | **可机检** | 解析 §25.3 表格，固定 7 名集合＋两列非空 | PASS。 |
| T2.3 | habit caller 仅一处且指 §26.11 | **可机检** | §25 范围 `habit.read` 计数=1，同一行匹配 `§26.11` | PASS：`1`。 |
| T2.4 | 三态、D-03 占位、禁含糊词 | **半机检** | 三态与禁词可扫；但“D-03 占位符”无固定 token，且 §0.1 又授权裁定后回填。改造：固定 `TBD-D-03` 或把 Gate 改为“占位/裁定二选一且 status 明确” | 三态与禁词 PASS（禁词 0）；占位由裁定取代，需人工应用 §0.1 优先级。 |
| T3.1 | plan 顶层5＋step子字段6 | **可机检** | 解析两张表第一列，与固定集合比对 | PASS。 |
| T3.2 | 五态逐行映射到八态 | **可机检** | 解析 §25.5 五行并与 §15.2.1 code 集合比对 | PASS。 |
| T3.3 | submit 请求/回执/三拒绝码 | **可机检** | 三标题存在＋拒绝码固定集合 | PASS。 |
| T3.4 | 架构树节点 desc 含 `§25.5` | **可机检** | `rg -n '§25\.5' docs/tracker/北极星架构树.html` 并限定 `name=任务编排` 节点 | **FAIL**：命中 0；L201 desc 仍为“多步任务规划与执行顺序控制”。 |
| T4.1 | 五步时序逐字且顺序正确 | **可机检** | 固定序列字符串或有序 token 扫描 | PASS。 |
| T4.2 | 三段 JSON 围栏与字段集合 | **可机检** | Markdown fenced-block parser＋JSON 解析＋固定集合比对 | PASS：字段数 `7/4/5`。 |
| T4.3 | 五动词签名＋幂等键两处 | **可机检** | 解析 SPI 表五行；request/receipt JSON key 集合包含幂等键 | PASS。 |
| T4.4 | 禁止“工具可绕过 dispatch 直连” | **可机检** | 对 §25 做固定禁句／等价禁句词表扫描 | PASS：固定禁句 0。 |
| T5.1 | 四输入公式＋复算 1 例 | **可机检** | 提取 canonical 输入，用 SHA-256 重算 | PASS：独立复算 `f3501053…b555c`。 |
| T5.2 | 取消三行＋A/B 两块 | **可机检** | 表行集合 `plan/step/run`；`IF D-01=` 计数=2，status 恰一 selected | PASS：三行，A/B 各一。 |
| T5.3 | 三类副作用＋事件 1 次 | **可机检** | 表行固定集合；`compensate_failed` 计数=1 | PASS：事件 1。 |
| T5.4 | D-01=A 时 §15.2.1 仅加1行 | **可机检** | `git diff --unified=0` 限定 §15.2.1，新增行计数=1且文本精确 | PASS：实测 1 行。 |
| T6.1 | 11 行 allowlist＋涉及的 HTML node name | **半机检** | 11 行与章节可解析，但“如涉及”没有给编号→节点固定映射，执行方可把全部写成“不适用”。改造：卡内冻结每个涉及编号的 node name 集合 | **FAIL**：执行报告虽有 11 行，但 HTML/架构树节点均写“不适用”，与 T1/T2/T3 的 tracker 要求冲突。 |
| T6.2 | 新增行只落允许集合，附录 A 恰1行 | **可机检** | diff hunk 按章节边界归类；§15.2.1 条件计数；附录新增计数 | **FAIL**：§15.2.1=1、§25=231，但附录 A 新增=0。 |
| T6.3 | 详解页≤6行、架构树 desc 节点=2 | **可机检** | `git diff --numstat`＋HTML node diff 解析 | **FAIL**：两 tracker 的 diff 均为空；详解页 0≤6，但架构树改动节点 0≠2。 |
| T6.4 | §25.1–§25.11 连续 | **可机检** | 提取标题编号，与 `1..11` 比对 | PASS：11 节连续。 |

实际统计：**可机检 21／半机检 3／不可机检 0**；合计 24，遗漏 0。

### 5.3 `T6_GATE=PASS` 自洽性

执行方报告 L205 的 ``T6_GATE=PASS`` 仅作对照。可机检性本身没有“不可机检”项，故不存在“拿不可机检项硬判 PASS”的冲突；但其**实际 Gate 结果仍不自洽**：T3.4、T6.1、T6.2、T6.3 均有确定性 FAIL。尤其 0057 卡 T6 明定附录 A 恰 1 行、架构树 desc 节点数=2，而独立 diff 实测分别为 0 与 0；执行方以“本轮禁止写 tracker／不改附录”自行缩窄了已批准卡的验收范围，不能据此宣告 T6 PASS。

### 5.4 T4 Gate

- T1～T6 的 24 个子项全部判定，遗漏 0；三类计数可由表格复算。
- 3 个半机检项逐条写明缺少的 oracle 与改造方向；不可机检为 0。
- 执行方 `T6_GATE=PASS` 与四个实测 FAIL 的冲突已定位。

`T4_GATE=PASS`

## §6 跨节一致性

### 6.1 §25 内部引用

脚本按 §25.1–§25.11 标题维护当前源节，并抽取正文正则 `§25\.(\d+)`；共得到 13 次引用、10 个唯一引用对。目标标题均真实存在。

| 引用对 | 源坐标与片段 | 目标坐标 | 判定 |
|---|---|---|---|
| §25.4 → §25.5 | L1607：`交 §25.5 建计划` | §25.5 L1612 | **一致** |
| §25.6 → §25.5 | L1651：`plan 必须通过 §25.5` | §25.5 L1612 | **一致** |
| §25.6 → §25.4 | L1672：`重新进入 §25.4` | §25.4 L1600 | **一致** |
| §25.6 → §25.10 | L1672：`计划级取消只引用 §25.10` | §25.10 L1739 | **一致** |
| §25.7 → §25.9 | L1715：`幂等值必须按 §25.9 生成` | §25.9 L1731 | **一致** |
| §25.7 → §25.10 | L1715：`按 §25.10–§25.11 收口` | §25.10 L1739 | **一致** |
| §25.7 → §25.11 | L1715：同上 | §25.11 L1753 | **一致** |
| §25.8 → §25.7 | L1722/L1725/L1727/L1729：run、receipt、治理调用与身份字段均引 §25.7 | §25.7 L1674 | **一致** |
| §25.8 → §25.10 | L1724：`ack 与强杀截止只认 D-02 / §25.10` | §25.10 L1739 | **一致** |
| §25.10 → §25.11 | L1745：`有可逆副作用则交 §25.11` | §25.11 L1753 | **一致** |

内部引用统计：**一致 10／矛盾 0／无锚点 0**；断链 0。

### 6.2 六组跨节关系

| # | 关系 | 两侧坐标与原文片段 | 判定 | 影响／让位建议 |
|---:|---|---|---|---|
| 1 | §25.3 composer ↔ §16.4 预算公式 | §25.3 L1582：`输入总预算只取…§16.4 公式 input_budget(profile)`；§16.4.1 L790–792：`input_budget(profile) = n_ctx - max_output(profile) - template_overhead` | **一致** | §25.3 只消费动态总预算并定义截断顺序，没有重写数值或公式。 |
| 2 | §25.7 dispatch 时序 ↔ §26.7 policy API | §25.7 L1676：`API 本体只引用 0059 §26.7`；当前基线 §25.11 L1763 后在 L1767 直接进入附录 A，`rg '^## 二十六'` 命中 0 | **无锚点** | 时序调用点存在，但请求/响应/规则版本 API 不存在；§26.7 未来只能补 API 本体并让位给 §25.7 的时序。 |
| 3 | §25.10 取消 ↔ §15.2.1 迁移表 | §25.10 L1741：`IF D-01=A｜status=selected`；§15.2.1 L577：`EXECUTING → CANCELLED`，门禁为取消级联确认或强杀终止凭据 | **一致** | 传播表、终止凭据与 fail-closed 迁移行语义对齐。 |
| 4 | §25.11 补偿失败 ↔ §15.2.1 迁移表 | §25.11 L1763：`任一必需补偿失败时，队列落 BLOCKED`；§15.2.1 L571–585：未列迁移拒绝，仅 `FAILED→BLOCKED` 且 `retryCount ≥2`，冻结门又限定源态 `QUEUED` | **矛盾** | 补偿可能发生于 EXECUTING/CANCELLED/FAILED 链，现文没有合法直达 BLOCKED 的源态。状态机主文 §15.2.1 应优先；§25.11 应明确先落 `FAILED` 并满足门禁，或 Owner 新裁一条合法迁移。此即 S-003。 |
| 5 | §25.5 plan schema ↔ §22 任务库 | §25.5 L1614–1643 定义 `plan_id/steps[]` 与五个步骤态；§22.2 L1315–1318 的任务库四级主轴是 `项目→工单卡→任务→运行实例`，且只走八态 | **无锚点** | 两边不直接矛盾，但 §22 没有 plan/step 在 task store 的持久化层级、索引键或生命周期映射；无法判定计划是卡内任务、独立对象还是仅瞬时载荷。建议 §22 只补 plan/step 指针映射，不新建第二任务索引。 |
| 6 | §25.2 记忆确认 ↔ §17 记忆三库 | §25.2 L1568–1570 使用 `mem.read/mem.write/mem.commit_ack`；§17.1 L855–861 将用户记忆入口固定为 `mem`，并与 `kb/exp` 分开 | **一致** | §25.2 的 `mem.*` 明确落用户记忆域，没有把 kb/exp 混检；`MEM_FULL` 又让位于 §17.2.3 容量主文。 |

六组统计：**一致 3／矛盾 1／无锚点 2**。

### 6.3 `TBD-G05-RETENTION`

结论：**仍存在**。§25.9 L1737 原文为：`§21.6 只规定 retry/rework 上限，没有时间制保留期…具体静态保留期记 TBD-G05-RETENTION`。§21.6 L1248–1257 确实只有 `retryCount/reworkCount` 与 BLOCKED 门，没有账本保留时长；因此该 TBD 未被消解，且是 §4 中 G-05 判“半堵”的直接依据。

### 6.4 T5 Gate

- §25 内部 10 个唯一引用对逐条核对，断链 0。
- 六组跨节关系全部使用固定三态判定；矛盾项给出双方坐标与让位建议。
- `TBD-G05-RETENTION` 已确认仍存在。

`T5_GATE=PASS`

## §7 与 0066 三条冲突的关系

| 冲突 | 0066 原定义与坐标 | 与 §25 的独立关系 | 定性 |
|---|---|---|---|
| S-001 · Core 执行顺序 | 0066 L117：架构树 L201 的 Core“多步任务规划与执行顺序控制”与基线 §19.2 L1112 的 Console“派发／调度／优先级／依赖”双主 | §25.5 L1631 只给 `depends_on` 计划约束，没有裁定运行期排序权归谁；该冲突在 0057 前已存在，0057 没有制造第二句，但也没有收口 | **0057 未覆盖** |
| S-002 · 队列写口 | 0066 L118：§14.3 L510 “只由状态机写”与 §19.3 L1127 Console“只读写八态”冲突 | §25.6 L1661 只在受理回执回带 `queue_state=QUEUED`，没有声明谁持久写；既有双主仍在，0057 未新增 writer 也未消歧 | **0057 未覆盖** |
| S-003 · 补偿落 BLOCKED 无迁移 | 0066 L119：补偿失败终态与 fail-closed 表不可达 | **明确落在 §25.11 L1763**：`任一必需补偿失败时，队列落 BLOCKED`；而 §15.2.1 L571–585 没有 EXECUTING/CANCELLED→BLOCKED，只有带门禁的 FAILED→BLOCKED | **0057 引入** |

定性统计：**0057 引入 1／0057 未覆盖 2／与 0057 无关 0**。S-003 确认位于 §25.11 L1763。

## §8 未决与遗留

| 未决／遗留 | 承担方 | 关闭条件 |
|---|---|---|
| U-01 · S-003 补偿失败如何合法进入 BLOCKED | Owner＋N-02 状态机负责人 | 在“先落 FAILED 并满足既有门”与“新增合法迁移”中裁一项；同步 §15.2.1、§25.11 与负例测试。 |
| U-02 · G-03 compose ABI 半堵 | N-01/Core | 为 `context.compose` 补封闭请求字段、返回字段、错误/超预算结果与幂等/trace 关系；不得另立第二入口。 |
| U-03 · `TBD-G05-RETENTION` | Owner＋N-02/N-13 | 在 §25.9 与 §22 只留一处静态保留期及清理 oracle；重放窗口内不得清账。 |
| U-04 · C-17 compensator/receipt 半堵 | N-02/Middleware executor | 补 `compensator` 调用签名、补偿 receipt 字段与错误码；与 §25.7 receipt 对账。 |
| U-05 · §26.7 policy API 无锚点 | 0059／N-14 | §26.7 落请求、响应、规则版本与拒绝码；调用时点让位给 §25.7。 |
| U-06 · plan 与 Task Store 无锚点 | N-13/Console | §22 补 `plan_id/step_id` 的存储指针与生命周期映射，仍只用现有 `tasks.json` 索引。 |
| U-07 · 0057 卡 Gate 未按批准范围闭合 | 后续有界修复单 | 架构树“任务编排”desc 含 §25.5；按卡同步两个 tracker 节点；附录 A 新增恰 1 行；重新跑原卡 T3.4/T6.1/T6.2/T6.3。 |
| U-08 · 队列写入归因与 Next 工程域证据 | 派发器维护方／Owner | 队列状态变化若属系统动作，应在卡中显式列豁免并给 writer receipt；Next 域因禁访问只能由有权限的独立审计提供不可变写入日志。 |

冻结前最小闭环：U-01/U-02/U-03/U-04/U-07 必须关闭；U-05/U-06 若仍未落正文，至少保持明确 `无锚点`，不得冒充已闭合。

## §9 自证

### 9.1 本审 T1→T6 Gate

| T | 本审 Gate 证据 | 结论 |
|---|---|---|
| T1 | before=`37e9cf…`、run-end=`3ad0ea…`、当前 HEAD=`e453557…` 均可解析；实际工作树 diff 两 hunk、`+232/-0`；基线 1792 行、SHA256 `3FE9B80…94C52` | PASS |
| T2 | 14 个实际边界对象逐项判定，另核 §15.2.1；边界分布 12/1/1，§15.2.1 实测新增 1 行 | PASS |
| T3 | 0057 卡 11 编号逐条有判定，已堵 8／半堵 3／未堵 0；0058 三项明确不计入 | PASS |
| T4 | 原卡 24 个 Gate 子项逐条判定，可机检 21／半机检 3／不可机检 0；原 `T6_GATE=PASS` 冲突已定位 | PASS |
| T5 | §25 内部 10 个唯一引用对断链 0；六组跨节 3/1/2；TBD 保留期仍存在 | PASS |
| T6 | 九段齐、三冲突定性齐、未决责任与关闭条件齐、回读 8 条、越界声明逐项齐；结论与冻结建议一致 | PASS |

说明：本表的 T1～T6 是 **0067 审计工作自身的完成度 Gate**；§5.3 指出的 FAIL 是 **被审 0057 原卡的实际 Gate**，两者不可混写。

### 9.2 关键命令与原始输出摘要

```text
git cat-file -t 37e9cf… = commit
git cat-file -t 3ad0ea… = commit
git cat-file -t HEAD      = commit
git diff --numstat 37e9cf… -- <baseline> = 232  0
hunks = @@ -576,0 +577 @@ ; @@ -1534,0 +1536,231 @@
section25_headings=11
context_compose=1; habit_read=1; trace_id_lines=1; trace_redefine=0
vague_words=0; if_d01=2; compensate_failed=1
tracker diff numstat = <empty>; tree §25.5 hit = 0
Test-Path H:\UltimaAI\UltimaAgentNext = False（仅存在性判断）
```

### 9.3 抽检回读（8 条）

| # | 坐标 | 原文回读 | 审计结论 |
|---:|---|---|---|
| R1 | 基线 §15.2.1 L577 | `EXECUTING → CANCELLED`，门禁为级联确认或强杀终止凭据 | **一致**：D-01=A 新增恰 1 行。 |
| R2 | 基线 §25.3 L1582–1598 | `context.compose 是唯一装配入口`，有七区/截断/隐私，但无请求/返回表 | **一致**：支持 G-03 半堵。 |
| R3 | 基线 §25.9 L1737 | `具体静态保留期记 TBD-G05-RETENTION` | **一致**：支持 G-05 半堵且 TBD 仍存在。 |
| R4 | 基线 §25.11 L1755–1763 | 三类副作用与失败事件存在，但无 compensator 签名/receipt 字段表 | **一致**：支持 C-17 半堵。 |
| R5 | 基线 §25.11 L1763 vs §15.2.1 L571–585 | `落 BLOCKED` vs fail-closed 迁移无合法来源直达 | **矛盾**：支持 S-003，且 S-003 在 §25.11。 |
| R6 | 架构树 L201/L283 | 两个“任务编排”desc 均不含 `§25.5` | **一致**：原卡 T3.4 FAIL，tracker 同步未做。 |
| R7 | 基线附录 A L1767 起 | 第二 diff hunk 在附录前结束，附录新增行 0 | **一致**：原卡 T6.2 的“附录 A 恰1行”FAIL。 |
| R8 | run 快照 queue-status | 0057 从 `pending/dispatched_at=null` 变为 `executing/2026-11-13T15:24:02.698255+00:00` | **一致**：队列状态确被改；归因可解释但字面“未改”不成立。 |

### 9.4 越界声明与最终只读核验

以下先声明 **本审 0067 的写入边界**，再保留 §3 对被审 0057 的越界结论：

- 基线：**未改（成立）**。本审开始与最终复核 SHA256 均为 `3FE9B80F25E0B75E42191C8C6343AF98EA4B51BA529457F97A48C9770A894C52`；其 `M` 状态是本审开始前既存的 0057 工作树结果。
- 0057 卡：**未改（成立）**。最终 SHA256 `D6BF2A9C342DF39EC94DCF17787DE2BAFA566C5AEC6ECEA54DC739EFB5BF5576`，LastWriteTimeUtc `2026-11-13T15:23:53.7691594Z`；本审未写。
- 0058 执行报告（0067 卡所称“0058 报告”）：**未改（成立）**。SHA256 `D3CABCD0C04F3B88C489314360A95ED8CC2B69DF5F20A800659EF484F1F391C3`，LastWriteTimeUtc `2026-11-13T15:18:18.2471632Z`。
- 0057 执行报告：**未改（成立）**；只用 `rg` 对照 `T6_GATE=PASS`，SHA256 `F74FEAADD351905140D00BC046DE0EAB9B3BA8D5733662D2CEB535F76985C6DD`。
- 队列／tracker：**未改（成立）**（就本审 0067 而言）；未调用队列写接口。被审 0057 运行期队列文件确有变化，已在 §3 判 **被改（越界）**，两种时间范围不混淆。两个 tracker 的 before/run-end/current blob 分别保持 `810ea278…` 与 `4d5bb259…`。
- 代码：**未改（成立）**。本审没有实现、格式化或测试写入；before/done 既存代码脏项哈希一致。
- 0067 本单卡：**未改（成立）**；SHA256 `47AD66F939AF64CFBC68B810E82E081374DCA291BCA3C9AE7C839865C03CB083`。
- 唯一写入：新增本报告 `docs/reports/audit-wo-ultimaagent-20261113-0057-round2-20261114.md`；未执行 `git add/commit/tag/push`。
- 禁区：未进入、未枚举、未读取、未写入 `H:\UltimaAI\UltimaAgentNext`；仅 `Test-Path=False`。未调用 18766 或外部登记接口。

### 9.5 最终一致性

- 结论等级“有条件通过（修复后再冻结）”与 3 条半堵、4 个原卡 Gate FAIL、1 个跨节矛盾自洽。
- 冻结建议不是宣布冻结；本审不改基线、不更新队列、不打 tag。
- 九段标题顺序为 §1→§9；抽检回读 8 条，满足不少于 5 条。

T6_GATE=PASS
FREEZE_RECOMMENDATION=修复后再冻结
