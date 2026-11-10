# Codex 工单 · 阶段4（多 Agent 编排层 · Agent 自持台账与看板）

> 版本：v1.0 ｜ 状态：可开工（前置：0029 收口 + 本方案 Owner 过目）｜ 适用工具：Codex
> 用法：按 T0→T7 顺序逐条执行，Gate PASS 后冻结再进下一条。
> 方案依据：`docs/plans/agent-m4-orchestration-ledger-plan-20261108.md`（G-PLAN-001，方案随单落盘）
> 执行端：`H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe`（Python 3.13.16），禁止默认 Python312

---

## 0. 阶段4 范围冻结

**本阶段只做**

1. 从 Manager `store.py` 提取 5 张核心表结构，冻结为 Agent 侧契约基线。
2. 在 `src\brain\ledger\` 新建约 1,200 行轻量 SQLite 台账（登记 / 状态流转 / CAS / 事务）。
3. 登记台双写：`GlobalQueueRegistrar`（md 主表）+ 新 ledger（SQLite），**ledger 失败不阻断派发**。
4. 新写活动级阶段解析器：从 `dispatch.out.log` 推"整理补丁 / 运行验证 / 正在写报告 / 等待模型"。
5. 新写 A2UI 执行看板页，字段对齐 Manager `ExecutionRow` 14 项。
6. `ApprovalGate` 决策落 ledger（approvals + events）。
7. 降级与对账补登。

**本阶段不做（Non-goals）**

- 不启用 WPF 版 UltimaManager 桌面端，不为其补功能、不打包。
- **不搬运 Manager 的 34,152 行后端代码**，不做全量 vendoring，**不修改 `H:\UltimaAI\UltimaManager` 下任何文件**（只读参照）。
- 不恢复 18766 常驻服务作为派发链路必备环节。
- 不让 ledger 变成硬依赖：缺 ledger 时 Agent 仍能正常派发。
- 不改 M4 已验收的 LangGraph 条件边语义（审批门 fail-closed 行为），不改 `queue.py` 的 md 主表格式与工单号规则。
- 不补 `ultima_bus` 消息总线（另立单）。
- 本阶段不改 `docs\tracker\北极星上线任务清单.html` 的数据源（该看板由主脑直接维护，已另接 `scripts\tracker-live.py` 采集；执行端不得改动该文件与采集脚本）。

---

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `docs\specs\ledger-schema-contract.md` | 5 表全字段与 Manager store.py 脚本比对 0 差异 |
| T1 | `src\brain\ledger\{__init__,schema.sql,store}.py` + tests | pytest ≥8 用例全绿 |
| T2 | `src\brain\ledger\registrar.py`、`src\brain\orchestration\queue.py`（小改） | 双写成功 + 故障下不阻断派发 |
| T3 | `src\brain\ledger\stage_parser.py` + tests | 0029 真实日志产出阶段时间线，覆盖 ≥6 类事件 |
| T4 | `src\window\combo_board.py`、`docs\specs\board-a2ui-contract.md` | a2ui_validator 通过 + 14 字段渲染 |
| T5 | `src\brain\orchestration\engine.py`（小改）、ledger approvals 写入 | hold→approvals 有记录；M4 原 10 测试仍绿 |
| T6 | `src\brain\ledger\health.py` + tests | 故障注入全绿 + 对账补登 0 遗漏 |
| T7 | 总验收 | 全量 pytest + 双场景 + stage4-frozen |

---

## 2. 任务明细

### T0 · 台账契约冻结

**文件**：`docs\specs\ledger-schema-contract.md`（新建）

**写什么**：
1. 从 `H:\UltimaAI\UltimaManager\src\manager\store.py` 提取 `projects / goals / work_orders / stages / runs / approvals / events` 七表 DDL 原文（其中 `work_orders` 14 字段、`runs` 26 字段必须逐字保留字段名、类型、NOT NULL、默认值、PRIMARY KEY、FOREIGN KEY）。
2. 记录来源：文件路径 + 提取时的 `git -C H:\UltimaAI\UltimaManager rev-parse --short HEAD`（若该目录非 git 仓库则记录文件 mtime）。
3. 定义"在跑"三要素：`state == "running" && pid > 0 && process_identity 非空`，写明三者缺一即非运行中，禁止改为人工填写。
4. 列出 state 枚举取值（从 store.py 中 `set_stage_state` / `cas_work_order` 的合法取值提取），标明哪些属 Agent 侧必须实现、哪些不实现。
5. 写 `scripts\ledger_schema_check.py`（新建）：解析契约 md 的字段表 vs 解析 Manager `store.py` 的 `CREATE TABLE` 块，逐字段输出差异清单，退出码 0=一致 / 1=有差异。

**验收（Gate T0）**：
- 契约文档含 7 表，`work_orders` 14 字段、`runs` 26 字段齐全，字段名与源文件逐字一致。
- 运行 `python -B scripts\ledger_schema_check.py` 输出 `0 differences`，exit 0。
- 文档写明来源 revision/mtime 与"在跑"三要素。

**禁止**：修改 `UltimaManager` 下任何文件；凭记忆补字段；把 Manager 的非必要表（handoffs / continuation_contracts / interventions / plans / external_actors / legacy_records）写成必须实现。

---

### T1 · 轻量台账 store

**文件**：`src\brain\ledger\__init__.py`、`src\brain\ledger\schema.sql`、`src\brain\ledger\store.py`、`src\brain\ledger\tests\test_ledger_store.py`

**写什么**：
1. `schema.sql` 按 T0 契约落 5 表 DDL（`work_orders / stages / runs / approvals / events`），字段与 T0 一致；不含 Manager 的其余 8 表。
2. `store.py` 提供 `LedgerStore(path)`，用 `sqlite3`（仅标准库 + `json` / `pathlib` / `contextlib` / `typing`），实现：
   - `put_work_order(project_id, work_order_id, goal_id, title, category, state, write_scope, acceptance, ...)`
   - `get_work_order(project_id, work_order_id)`
   - `cas_work_order(project_id, work_order_id, expected_version, **fields)` —— 版本号乐观锁，冲突抛 `VersionConflict`（不吞）
   - `put_run(...)` / `update_run_process(project_id, work_order_id, stage_id, run_id, pid, process_identity, state)` / `finish_run(..., exit_code, finished_at)`
   - `list_runs(project_id=None, work_order_id=None, state=None)`
   - `add_approval(...)` / `add_event(event_type, message, **fields)`
   - `transaction()` 上下文管理器
3. `__init__.py` 导出上述公共符号。
4. WAL 模式 + `PRAGMA foreign_keys=ON`；`close()` 幂等。
5. 测试覆盖：CAS 冲突、并发写（两线程各写一单）、幂等 put、事务回滚、`update_run_process` 三要素校验（pid 缺失时不允许置 running）。

**验收（Gate T1）**：
- `python -B -m pytest src\brain\ledger\tests -o addopts=` 全绿，用例 ≥8。
- `python -B -c "from src.brain.ledger import LedgerStore"` 导入成功。
- 建库后 `sqlite3` 校验：5 表存在，`work_orders` 列数 = T0 契约列数。

**禁止**：引入第三方依赖；复制 Manager 源文件；写超过 1,500 行；把 Manager 的 8 张非必要表也建出来。

---

### T2 · 双写登记台（保留降级）

**文件**：`src\brain\ledger\registrar.py`（新建）、`src\brain\orchestration\queue.py`（小改）

**写什么**：
1. `registrar.py` 实现 `LedgerRegistrar.register(work_order)`：写 `work_orders` + `events`，返回 `RegisterResult(status: "ok"|"degraded", reason)`。
2. 在 `queue.py` 的 `GlobalQueueRegistrar` 写完 md 主表**之后**，附加一次 ledger 写；用 `try/except Exception` 包裹，**任何 ledger 异常只记录并返回 degraded，绝不向上抛、绝不阻断后续派发**。
3. 同一个工单号（`wo-<project-key>-<YYYYMMDD>-<NNNN>`）在两处保持一致；md 格式与工单号规则**不做任何改动**。
4. 降级路径：`ledger` 目录不存在 / db 只读 / 表缺失 → 全部归 degraded，md 主表照常写。
5. 增加环境开关 `ULTIMA_LEDGER_DISABLED=1` 可整体关闭 ledger 写。

**验收（Gate T2）**：
- 正常路径：登记一个测试工单，md 主表有该行 **且** `work_orders` 有同号记录。
- 故障注入（db 路径指向只读目录 / 删除表）：登记仍返回成功、md 主表仍有该行、结果为 `degraded`，**不抛异常**。
- `ULTIMA_LEDGER_DISABLED=1` 时完全不写 ledger，md 照常。

**禁止**：改 md 主表列格式；改工单号生成规则；把 ledger 失败升级为派发失败；在 `queue.py` 内写业务逻辑（逻辑放 registrar）。

---

### T3 · 活动级阶段解析器

**文件**：`src\brain\ledger\stage_parser.py`、`src\brain\ledger\tests\test_stage_parser.py`

**写什么**：
1. 读 `tasks\queue\runs\<work_order_id>\dispatch.out.log`（实际路径以 0029 为样例实测确认），**逐行 `json.loads`**，坏行跳过并计数（不抛）。
2. 建立"事件类型 → 活动阶段"映射（证据驱动，不做语义推断）：
   - 写文件 / 打补丁类事件 → `整理补丁`
   - 执行命令 / 跑测试类事件 → `运行验证`
   - 生成报告 / 写 markdown 类事件 → `正在写报告`
   - 等待模型响应 / token 流式类事件 → `等待模型响应`
   - 会话开始 / 任务接收 → `接收任务`
   - 结束 / 完成 → `收尾`
   - 其余 → `other`（原样保留触发事件名，供人工判读）
3. 输出 `list[StagePoint(ts, phase, activity, source_event, confidence)]`，并汇总为 `(当前阶段, 各阶段耗时)`。
4. `confidence`：直接字段命中=high，关键词匹配=medium，未知=low；禁止把 low 当成 high 展示。
5. 不调用任何模型、不联网、不依赖 `dispatch.out.log` 之外的输入。

**验收（Gate T3）**：
- 用 0029 的真实日志跑，输出阶段时间线与各阶段耗时，覆盖事件类别 ≥6。
- 坏行（非 JSON）注入测试：不抛异常，计数正确。
- 未知事件归 `other` 且保留原事件名。
- pytest 全绿。

**禁止**：用模型/LLM 推断阶段；硬编码某条工单的绝对路径；把 `other` 伪装成正常阶段；忽略解析失败计数。

---

### T4 · A2UI 执行看板页

**文件**：`src\window\combo_board.py`（新建）、`docs\specs\board-a2ui-contract.md`（新建）

**写什么**：
1. 契约文档固定 14 个展示字段（对齐 Manager `ExecutionRow`）：`ProjectId / ProjectName / WorkOrderId / RunId / StageId / TaskTitle / PhaseLabel / StateLabel / ElapsedLabel / ProcessLabel / IsConfirmedActive / SelectionKey / Identity / AccessibleLabel`。
2. 数据源：`LedgerStore.list_runs()` + T3 阶段解析器（`PhaseLabel` 取活动级阶段，`StateLabel` 取 runs.state）。
3. 在跑判定**必须**用三要素：`state=="running" && pid>0 && process_identity 非空`；缺一 `IsConfirmedActive=False`，`ElapsedLabel` 显示"—"。
4. 耗时由 `started_at` 自动算（不手填），单位中文（"55 分钟"）。
5. 三态着色：运行中 / 排队中 / 已完成；空数据态显示"暂无执行中任务"而不是空白。
6. 界面走 A2UI DSL 生成，**窗口/容器尺寸由内容算出，不写死像素**；复用 `a2ui_validator.py` 校验、`active_renderer.py` 渲染。
7. 提供 `scripts\shot-board.py`：注入 0029 样例数据（或真实数据）渲染并截图落 `artifacts\board\`。

**验收（Gate T4）**：
- `a2ui_validator` 校验通过，0 违规。
- 注入 0029 数据：14 字段全部渲染出非空值（`RunId`/`ProcessLabel` 允许"未提供"但不留空）。
- 三要素破坏测试：把 `pid` 置 0 → `IsConfirmedActive` 变 False，耗时显示"—"。
- 空数据态正确显示占位文案。
- 截图落盘，人工可见字段完整。

**禁止**：手绘像素级布局；写死窗口尺寸；用人工填写的状态代替三要素判定；把看板做成需要联网/模型的页面。

---

### T5 · 审批门接线

**文件**：`src\brain\orchestration\engine.py`（小改）、ledger `approvals` 写入

**写什么**：
1. `ApprovalGate.require(node)` / `approve(node, approver)` 决策后，向 ledger 写一条 `approvals`（节点 / 决策 / 审批人 / 时间 / 工单号）+ 一条 `events`。
2. `hold` 时把对应 run 的 `state` 标 `blocked`（不改 LangGraph 条件边逻辑）。
3. ledger 不可用时静默降级（只写审计 JSONL），**不得**影响审批门本身行为。
4. 保持 M4 已验收语义：hold → 条件边 → END，后续节点不执行。

**验收（Gate T5）**：
- hold 场景：`approvals` 有记录、run 标 blocked、后续节点未执行。
- approve 场景：继续执行且 `approvals` 记录审批人。
- **M4 原 10 项测试仍全绿**（`test_orchestration_m4.py`）。
- ledger 关闭时审批门行为完全不变。

**禁止**：修改 LangGraph 条件边（M4 排障记录明确：节点内 hold 不阻断）；把审批人写成固定 "system" 而无记录。

---

### T6 · 降级与对账自愈

**文件**：`src\brain\ledger\health.py`、`src\brain\ledger\tests\test_health.py`

**写什么**：
1. `check()`：db 存在性 / 可写性 / 5 表完整性 / 最近事件新鲜度 → 返回 `(healthy: bool, reasons: list)`。
2. `reconcile()`：解析 `_shared\queue\global-queue-index.md` 的工单行，与 `work_orders` 对账；**md 有、ledger 无 → 补登**；ledger 有、md 无 → 只报告不删除。
3. 启动自检：Agent 主流程启动时调 `check()`，不健康则整体置 degraded（派发照常）。
4. 补登有条数上限（默认 200/次），防一次性拉爆；超出只报告。

**验收（Gate T6）**：
- 故障注入（只读 db / 删表 / db 不存在）三种场景 `check()` 均返回 False 且给出可读原因。
- 对账场景：md 有 3 单、ledger 只有 1 单 → 补登 2 单，结果与 md 一致。
- pytest 全绿。

**禁止**：删除 ledger 中 md 没有的记录；无上限全量补登；把不健康状态写成抛异常阻断主流程。

---

### T7 · 总验收

**文件**：无新增（全量验证）

**写什么**：
1. 全量回归：`python -B -m pytest src\brain\ledger src\brain\orchestration -o addopts=` 全绿（含 M4 原 10 项）。
2. 双场景：(a) 0029 真实日志 + 真实 md 主表；(b) 空库冷启动。
3. 契约复核：`python -B scripts\ledger_schema_check.py` exit 0。
4. 产出阶段报告 `docs\reports\m4-ledger-stage4-20261108.md`，含验收清单逐项结果 + 改动文件清单 + 越界声明 + 测试输出。
5. 冻结 tag：`stage4-ledger-frozen-20261108`。
6. 明确记录：北极星 HTML 数据源**本阶段未切换**，留待下阶段评估。

**验收（Gate T7）**：
- 所有 Gate T0–T6 证据齐。
- 全量测试全绿、契约比对 0 差异。
- 越界声明明确写"未修改 UltimaManager 任何文件"。
- tag 已打且推送结果记录（无远端则写明"本地 tag only"）。

---

## 3. 给编码代理的任务粘贴模板

```
T# <标题>：已完成，Gate 全绿
- 改动文件：<逐条>
- 验收命令与输出：<粘贴>
- 越界声明：无 / <具体>
总验收：<命令输出摘要>
```

---

## 4. 验收要点

- [ ] 范围冻结内逐项完成（无越界，尤其未动 UltimaManager 目录）
- [ ] 每 T 验收清单全绿 + 自证完整
- [ ] 契约文档与源码逐字段一致（脚本可复现）
- [ ] 降级路径真实可用（故障注入通过，不是"预计可用"）
- [ ] 阶段报告产出 → 复核 → 冻结 tag
- [ ] 全量测试用 `venv-openjarvis\Scripts\python.exe` + `-o addopts=`
