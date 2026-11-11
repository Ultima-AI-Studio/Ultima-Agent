# Codex 工单 · 0038 SuperAgent 调度器整合为本地自动化 tools

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：Codex
> 链路：`wo-ultimaagent-20261111-0038`
> 执行端：Codex（独立任务通道，自主产出整合设计与 PoC，不经主脑判断）
> 前置：无（独立设计单，不依赖任何未冻结前置）
> 方案依据：`docs/plans/plan-ultimaagent-superagent-scheduler-tools-20261111.md`
> 锁定 revision：`c9ecfb7a56e2335ec7bb6404faa9a9f8213b3a30`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`
> 用法：按 T0→T4 顺序执行，每 T 的 Gate 全绿再进下一条，禁止跳序。

---

## 0. 本单定位

本单做的是**把工单之间的「手动调度」设计成自动 tools**，不是推进任何具体业务任务，也不是一次性重写整个系统。

背景事实（可直接引用，无需重新发现）：现有系统单工单内部已自动，缺的是「上一单完成 → 自动取下一单 → 派发」的常驻循环；仓内 `scripts/` 老脚本链与 `tasks/queue_engine/` 模块引擎双轨并存、状态枚举不一致；DeepSeek Super Agent 原型（`research/dsh-superagent-prototype`，MIT，TS）已含 Pass 调度、效果队列、Ticket 状态机等成熟蓝图，2026-11-03 已结论「借鉴重写、不整仓拼装」。

本单产出 = 整合设计文档 + 最小 PoC + 分阶段落地计划。

---

## 1. 范围冻结

**本阶段只做**

1. 以代码为准盘点 dsh 调度相关组件与本地 `queue_engine`、`dispatch-work-order.py` 的真实职责与接口。
2. 给出逐组件 TS→Python、dsh→本地的差距判定（复用 / 新写 / 改造），并给出双轨收敛方案。
3. 设计自动化 tools 的形态、公开接口契约、状态映射、自动接力主循环、失败恢复与名额兜底。
4. 实现一个不接入正式链路的最小 PoC，在夹具上演示自动接力闭环，并配可回归测试。
5. 给出分阶段落地计划，每阶段带可机检 Gate 与回滚策略。

**本阶段不做（Non-goals）**

1. 不整仓引入 dsh，不引入 Node/TypeScript 运行时，不改 dsh 源码。
2. 不把 PoC 接入正式派发链路、不替换 `dispatch-work-order.py`、不改其现有行为。
3. 不改 `tasks/queue/queue-status.json` 任何业务数据，不重写存量工单状态，不做存量任务重梳理。
4. 不改 `scripts/verify-order.py`、`verify-mechanism-change.py`、`freeze-work-order.py`、`validate_work_order.py`。
5. 不破坏已冻结语音链路（KWS→ASR→8B→TTS）与 OpenJarvis 验收基础。
6. 不联网、不装第三方依赖（仅可用 `libs/wheels` 离线源），不 `git add -A`。

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `tasks/queue/runs/<本单 run>/component-facts.md`（新增） | 组件事实清单与代码逐一对账，无遗漏无臆测 |
| T1 | 同上文件追加差距段 | 每个 dsh 组件给出复用/新写/改造判定，可证伪 |
| T2 | `tasks/queue/runs/<本单 run>/tools-contract.md`（新增） | 接口契约与状态映射完整，无新增并行枚举 |
| T3 | 同上文件追加循环与恢复段 | 自动接力、失败恢复、名额兜底设计齐全 |
| T4 | `tasks/queue_engine/auto_relay_poc.py`（新增）+ `scripts/tests/test_auto_relay_poc.py`（新增）+ 本卡回填位 | 夹具上自动接力闭环可复现，测试全绿 |

---

## 3. 任务明细

### T0 · 现状盘点（只读）

**文件**：`tasks/queue/runs/<本单 run>/component-facts.md`（run 目录由派发器给出，不得自造）

**写什么**：

1. 逐个精读 dsh 调度相关源码：`src/app/passes.ts`、`src/core/part.ts`、`src/app/effects.ts`、`src/app/outbox.ts`、`src/core/tickets.ts`、`src/core/stage.ts`、`src/core/assignments.ts`、`src/core/intake.ts`、`src/infra/health.ts`。
2. 逐个精读本地件：`tasks/queue_engine/` 的 `state_machine.py`、`priority_deps.py`、`dispatcher.py`、`storage.py`、`run_worker.py`、`receipt_contract.py`，以及 `scripts/dispatch-work-order.py` 的状态机与名额逻辑。
3. 每个组件填四栏：职责 / 输入输出 / 持久化方式 / 触发方式，具体到函数名与字段。
4. 单列一张「双轨现状表」：老脚本链与 queue_engine 各自覆盖了哪些环节、状态枚举如何对应。

**验收（Gate T0）**：

- dsh 组件条目数 == 上面列出的 9 个文件，本地组件条目数 == 上面列出的 7 个，逐一对账，多一条少一条都不合格。
- 每条四栏非空，且函数名/字段名能在源码中 grep 命中；贴出至少 3 处 grep 命中输出为证。
- 双轨现状表必须明确指出「没有任何常驻循环驱动 queue_engine」，并贴出全仓 grep `while True`/daemon 的实际输出证明。

**禁止**：不得按文件名或文档描述推断职责，必须读函数体；不得写「待定」「视情况」。

---

### T1 · 差距与复用判定

**文件**：`tasks/queue/runs/<本单 run>/component-facts.md`（追加「差距判定」段）

**写什么**：

1. 对每个 dsh 组件，给出本地落点三选一：直接复用（指明本地函数）/ 新写（给出 Python 模块与函数签名草案）/ 改造（指明改哪个文件、改什么）。
2. 给出双轨收敛建议：保留哪一套作为权威，另一套如何封存或退役，存量调用如何迁移，给出推荐与至少一个反方取舍。
3. 标出无法可靠判定的组件，标 `unverifiable` 并写明缺什么证据，不允许猜。

**验收（Gate T1）**：

- 判定条目数 == dsh 组件数（9），每个组件恰有一个判定；「复用」项必须贴出本地函数的文件:行号并附 grep 命中输出，「新写/改造」项必须给出「构造输入→预期输出」断言，断言不成立即不合格。
- 双轨收敛建议必须包含明确的状态枚举归并方案，证明不会产生第三个枚举；若做不到，该条判不合格。
- 每个 `unverifiable` 条目必须附一条可执行取证命令（git/grep/读文件）并在本 T 内实际执行，贴出命令输出；未附命令或未执行的条目计数 == 0 才合格。

**禁止**：不得默认「全部新写」，凡本地已有同能力件必须先判复用并说明。

---

### T2 · tools 形态与接口契约

**文件**：`tasks/queue/runs/<本单 run>/tools-contract.md`

**写什么**：

1. 在「常驻无窗服务 / queue-engine 子命令 / 可调用模块」三种形态中给推荐与理由，说明如何与现有 `dispatch-work-order.py`、`queue_engine` 共存或收敛。
2. 定义公开接口：启动、停止、状态查询、选单、接力触发、重试，每个接口给签名、入参、返回、错误码。
3. 定义持久化位置与 `queue-status.json` 的权威关系（谁是唯一写入者、如何防并发覆盖）。
4. 给出 dsh Ticket 状态 ↔ queue_engine 八态（QUEUED/EXECUTING/SELF_CHECK/AUDIT/COMPLETED/FAILED/BLOCKED/CANCELLED）的完整映射表。
5. 明确人工门边界：BLOCKED 释放、发布、独立审计停等人，其余自动。

**验收（Gate T2）**：

- 接口清单覆盖「启动/停止/状态/选单/接力/重试」六项，缺一不可，每个接口都有可机检的成功与失败输入。
- 状态映射表对 queue_engine 八态每个都有唯一去向，且不出现新枚举名；grep 设计稿确认无第三个状态集合。
- 人工门边界必须与 `state_machine.py` 现有 `BLOCKED may be released only by human or brain` 一致，贴出该源码行为证。

**禁止**：不得设计成绕过 `state_machine` 直接写状态；不得让 tools 成为 `queue-status.json` 的第二个并发写入者。

---

### T3 · 自动接力循环、失败恢复与名额兜底

**文件**：`tasks/queue/runs/<本单 run>/tools-contract.md`（追加「循环与恢复」段）

**写什么**：

1. 主循环逻辑：节拍泵（参考 passes/part）、选单（`priority_deps` + 依赖门）、派发、回执、审计、冻结、回到选单，画出每步的判定与分支。
2. 失败恢复：超时、暂停、parent_lost、回执无效、派发失败的处理，重试次数与退避，幂等键，以及「不重复已完成外部副作用」的恢复语义。
3. 名额兜底：无 run 的 audit 单如何处理——用记录时间字段算等待时长，仍算不出则标无效持有、不计入名额；给出判定流程。
4. 给出主脑可介入的显式入口（覆盖自动选单），说明默认不启用。

**验收（Gate T3）**：

- 循环每条分支都有终止条件，不存在无界空转；贴出对每个异常分支的输入→预期状态表。
- 名额兜底必须可证伪：构造「无 run 的 audit 单」，断言其要么算出非空时长、要么被标无效持有，二者必居其一，否则该条不合格。
- 幂等可复现：构造同一回执连续投递 2 次，断言持久化记录计数 == 1 且状态与仅投递 1 次完全一致，贴出两次运行输出；计数 != 1 或状态不一致即不合格。

**禁止**：不得用「自动重试直到成功」这类无界策略；不得让无 run audit 单永久占位。

---

### T4 · 最小 PoC、落地计划与回填

**文件**：`tasks/queue_engine/auto_relay_poc.py`（新增，独立 POC，不被任何正式入口 import）+ `scripts/tests/test_auto_relay_poc.py`（新增）+ 本卡回填位

**写什么**：

1. PoC 用夹具（不依赖真实 Codex、不联网）实现：一个 QUEUED 任务被选中 → 模拟派发完成 → 自动选择下一个 QUEUED 任务，验证接力顺序与依赖门。
2. 测试覆盖：正常接力、依赖未满足不跳单、失败重试到上限转 BLOCKED、无 run audit 单不永久占位，各 ≥1 条。
3. 给出分阶段落地计划：阶段顺序、每阶段可机检 Gate、回滚策略、与存量工单的隔离方式。
4. 回填本卡「回执」段。

**验收（Gate T4）**：

- `& H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests/test_auto_relay_poc.py -o addopts= -p no:cacheprovider -q` 全绿，贴完整输出。
- 全量 `scripts/tests` 回归全绿（基线 104 passed，只许增加用例不许减少通过数），贴输出。
- 反向验证：把 PoC 选单逻辑改回「不自动接力」，对应测试必红、exit 非 0，恢复后转绿，贴输出。
- grep 确认无正式入口 import `auto_relay_poc`，证明 PoC 不影响现网行为。

**禁止**：不得让 PoC 调用真实付费接口或真实 Codex；不得把 PoC 挂进开机自启或看门狗。

---

## 4. 总验收

1. T0–T3 设计文档齐全，每个判定有代码证据或可证伪条件，无「我觉得」。
2. PoC 测试全绿，反向验证已做，且 PoC 与正式链路物理隔离。
3. 双轨收敛与状态归并方案明确，不产生第三个状态枚举。
4. 名额兜底、幂等、失败恢复均有可复现验证。
5. 数据未动：`git diff HEAD -- tasks/queue/queue-status.json` 为空。
6. 分阶段落地计划每阶段 Gate 可机检、可回滚。

---

## 5. 禁止清单

1. 不得引入 Node/TS 运行时或整仓拼装 dsh，不得改 dsh 源码。
2. 不得改 `queue-status.json` 业务数据或重写存量工单状态。
3. 不得改 `verify-order.py` / `verify-mechanism-change.py` / `dispatch-work-order.py` / `freeze-work-order.py` / `validate_work_order.py`。
4. 不得把 PoC 接入正式链路、开机自启或看门狗。
5. 不得联网安装依赖；不得 `git add -A`，提交必须显式列路径。
6. 不得用无界重试或让无 run audit 单永久占位。

---

## 回执（执行端填写）

- run 目录：（待填）
- 设计文档：（待填路径）
- PoC 与测试：（待填）
- pytest 结果：（待填，含全量回归与反向验证）
- 落地计划：（待填）
- 已知限制 / unverifiable：（待填）
