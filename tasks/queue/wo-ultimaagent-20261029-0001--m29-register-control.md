# Codex 工单 · UltimaAgent｜功能｜M29 登记控制面实现（工单编号核发 + 全局主表登记 + WIP 校验）

> 版本：v1.0 ｜ 状态：技术执行完成（T0–T3 Gate 全绿，待主脑复核；不代签 Owner 冻结/发布门）｜ 适用工具：Codex（`codex exec`，`-m gpt-5.6-sol`）
> 用法：按 T0→T3 顺序逐条执行，Gate 全绿才过，再进下一条。
> 范围依据：`H:\UltimaAI\INDEX.md`（G-TASKFLOW-001 / G-WO-NAME-001）+ `H:\UltimaAI\_shared\paradigms\UltimaAI-任务工作流范式.md` + `H:\UltimaAI\_shared\paradigms\UltimaAI-全局工单命名标准.md` + `H:\UltimaAI\_shared\paradigms\Codex-外部执行端调用范式.md`（执行适配器细则）+ `docs/INDEX.md`（项目引导索引）
> 登记：2026-10-29 ｜ 原单 ID：wo-ultimaagent-20261029-0001 ｜ 类型：功能

---

## 0. 范围冻结

**本阶段只做（M29 登记控制面）**：

1. `src/brain/orchestration/queue.py` 的 `TaskQueue.create()` 增加 **G-WO-NAME-001 工单编号核发**（`wo-<project-key>-<YYYYMMDD>-<NNNN>`，同日序号从 0001 递增，跨日重算；编号与日期按 Asia/Shanghai 首次登记，不随重试/跨日改变）；
2. 新增 **全局主表登记写回**：任务进入「排队/派发/执行中/审计/回执/冻结」关键状态时，写回 `H:\UltimaAI\_shared\queue\global-queue-index.md`（按项目行聚合更新，明细行可追加）；
3. 新增 **WIP 双层校验**（对齐 G-TASKFLOW-001 §6 与 Codex 范式 §3）：全项目合计执行中 ≤3、每项目执行中 ≤1、全项目独立审计 ≤1；超限时派发前拒绝并返回原因；
4. 配套单元测试 + 全量回归通过。

**本阶段不做**：不动 `orchestration/registry.py` 驻留机制；不改外部 `global-queue-index.md` 表头/状态机语义；不接入 DeepSeek 或其他执行适配器；不改 `task-queue.json` 既有历史数据格式（向后兼容）；不重命名既有工单 ID。

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `src/brain/orchestration/queue.py` | 编号核发对接 G-WO-NAME-001，单测通过 |
| T1 | `src/brain/orchestration/queue.py` + `_shared/queue/global-queue-index.md` | 全局主表写回，单测通过 |
| T2 | `src/brain/orchestration/queue.py` | WIP 双层校验，单测通过 |
| T3 | 总验收 | 全量单测 + 回归 + 证据落盘 |

---

## 2. 任务明细（每条 T 严格三段式）

### T0 · 工单编号核发对接 G-WO-NAME-001

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\orchestration\queue.py`（修改）
- `H:\UltimaAI\UltimaAgent\src\brain\orchestration\tests\`（新增/修改测试）

**写什么**：
1. 在 `TaskQueue.create()` 增加正式编号生成逻辑：格式 `wo-<project-key>-<YYYYMMDD>-<NNNN>`；`project-key` 默认 `ultimaagent`（可配置参数传入）；`YYYYMMDD` = Asia/Shanghai 首次登记日期（8 位数字）；`NNNN` = 同项目同日期序号，从 `0001` 起 4 位递增，跨日/跨日重试重算，同日不重复、不截断；
2. 保留 `task_id` 字段承载正式编号（历史 UUID 数据读入时兼容，不做批量迁移）；`create()` 增加 `project_key: str = "ultimaagent"` 参数；
3. 序号源：读本地 `task-queue.json` 中当日已用编号（同项目+同日期前缀）取最大 +1；文件不存在或为空时从 0001 起；
4. 失败语义：编号生成失败（如并发抢号检测到同日同号）抛 `OrchestratorError`，不静默降级。

**验收（Gate T0）**：
- [ ] 新增单测 ≥3：①同日多任务编号 0001/0002/0003 递增；②跨日重算从 0001；③编号格式正则 `^wo-[a-z]+-\d{8}-\d{4}$` 全匹配；
- [ ] 既有单测零回归（`python -m pytest src/brain/orchestration/tests -q --disable-warnings` 全绿）；
- [ ] 历史 UUID task_id 数据读入不报错（向后兼容）。

**禁止**：不改 `task-queue.json` 历史数据；不用 uuid 作正式编号；不引入第三方库。

---

### T1 · 全局主表登记写回

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\orchestration\queue.py`（修改，新增登记模块或函数）
- `H:\UltimaAI\_shared\queue\global-queue-index.md`（运行时写回目标；本工单只实现写回逻辑，不手动改表）
- `H:\UltimaAI\UltimaAgent\src\brain\orchestration\tests\`（新增测试）

**写什么**：
1. 新增 `GlobalQueueRegistrar`（可在 queue.py 内或独立模块 `src/brain/orchestration/global_queue.py`）：职责=按状态写回全局主表；
2. 触发点：任务进入「排队/派发/执行中/审计/回执/冻结」状态时调用（`enqueue`/`advance`/`complete` 中串接）；
3. 写回规则（对齐 Codex 范式 §3"全局主表只聚合状态不复制正文"）：
   - 项目行（如 `| UltimaAgent | ... |`）：更新工单数/登记执行中/待审计/阻塞/已完成 列，保持表头与既有行格式一致（对齐 `_shared/queue/queue-status-gen.py` 生成的汇总口径）；
   - 明细行：可在主表对应项目区追加一行 `| UltimaAgent | <工单ID> | <状态> | 说明 |`（状态 ∈ 待派发/执行中/审计中/已冻结，说明一句依据）；
   - 写回失败（文件锁/不存在）：记录 warning 不静默吞错，任务状态照常推进（全局表为聚合视图，不能因写失败阻塞主流程）；
4. 路径：全局主表路径可配置（默认 `H:\UltimaAI\_shared\queue\global-queue-index.md`），校验路径在 `H:\UltimaAI\_shared\queue\` 内（防越界写任意路径）。

**验收（Gate T1）**：
- [ ] 新增单测 ≥3：①排队触发项目行+明细行写回（用临时文件模拟全局主表）；②状态流转时主表状态值正确更新；③路径越界（非 `_shared/queue/` 下）拒绝写回并抛错；
- [ ] 既有单测零回归；
- [ ] 写回格式与 `_shared/queue/queue-status-gen.py` 输出口径一致（表头列序相同）。

**禁止**：不复制工单正文到全局主表（只聚合状态）；不改 `queue-status-gen.py`；不写 `_shared/queue/` 之外的任何路径。

---

### T2 · WIP 双层校验

**文件**：
- `H:\UltimaAI\UltimaAgent\src\brain\orchestration\queue.py`（修改）
- `H:\UltimaAI\UltimaAgent\src\brain\orchestration\tests\`（新增测试）

**写什么**：
1. 新增 WIP 校验逻辑（对齐 G-TASKFLOW-001 §6 + Codex 范式 §3）：
   - 全项目合计执行中 ≤3（读全局主表各项目"登记执行中"列求和）；
   - 每项目执行中 ≤1（本项目主表中该项目执行中数）；
   - 全项目独立审计/计划评审 ≤1；
2. 触发点：`enqueue`（入排队）与 `advance` 到「派发/执行中」前校验；超限返回拒绝原因（`OrchestratorError` 或结构化返回），不自动续跑；
3. 容量读取源：全局主表项目行（通过 T1 的 Registrar 读接口），读取失败时按 fail-open 记 warning 并允许继续（全局表可能暂不可用，不阻塞本地任务）——**注意：此处为容量检查辅助，越界保护仍按 fail-closed 执行**；
4. 返回结构：`{"allowed": bool, "reason": str, "current_executing": int, "max_executing": int}` 便于调用方展示。

**验收（Gate T2）**：
- [ ] 新增单测 ≥3：①全项目执行中=3 时第 4 单拒绝；②本项目执行中=1 时同项目第 2 单拒绝；③审计=1 时新审计拒绝；未超限时放行；
- [ ] 既有单测零回归。

**禁止**：不改全局 WIP 上限值（≤3/≤1/≤1 为冻结基线，本工单只实现校验）；不做"一包多单"支持。

---

### T3 · 总验收

**文件**：本工单（更新状态）+ `docs/reports/` 阶段报告 + 证据目录

**写什么**：
1. 全量单测回归：`H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest src -q --disable-warnings`（Agent 专用解释器，禁止用系统 Python312）→ 全绿 + 无新增失败；
2. 阶段报告 `docs/reports/stage-m29-register-control.md`：Gate 逐条核对（T0-C1~C3/T1-C1~C3/T2-C1~C3/T3 全量），证据路径、越界声明（无=明确写"无"）；
3. 证据落盘 `docs/reports/evidence/m29-register-control/`：新增单测输出、全量回归摘要、主表写回样例（临时文件）粘贴；
4. 回执 8 字段按 Codex 范式 §5 输出。

**验收（Gate T3）**：总验收清单全绿；阶段报告存在且逐项勾选；回执 8 字段齐全；越界声明如实。

---

## 3. 给编码代理的任务粘贴模板

```
T0 工单编号核发：已完成，Gate T0 全绿（附单测输出）
T1 全局主表登记：已完成，Gate T1 全绿（附写回样例）
T2 WIP 双层校验：已完成，Gate T2 全绿（附拒绝样例）
T3 总验收：<命令输出摘要>（全量回归 N passed）
```

---

## 4. 验收要点

- [x] 范围冻结内逐项完成（无越界：未动 registry.py 驻留机制 / 未改全局表头语义 / 未动既有工单 ID）
- [x] 每 T 验收清单全绿 + 自证完整
- [x] 关联文档同步（范式引用一致）
- [ ] 阶段报告产出 → 主脑复核 → 冻结 tag（报告已产出；主脑复核/Owner 冻结不代签）
