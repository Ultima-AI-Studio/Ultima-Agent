# 模块4 实施方案 · 多 Agent 编排层吸收 Manager 能力（G-PLAN-MA-001）

> 版本：v1.0 ｜ 状态：待 Owner 过目 → 过目后冻结 ｜ 类型：产出型方案（G-PLAN-001）
> 日期：2026-11-08 ｜ Owner 口径：**不是启用 WPF 版 UltimaManager，是让 UltimaAgent 自身具备该能力**
> 方案路径即本文件；配套工单 `wo-ultimaagent-20261108-0030` 引用本路径

---

## 0. 一句话结论

Manager 的**能力不缺、缺接线**；模块4 的**能力不缺、缺落地**。本方案不搬 Manager 的 3.4 万行代码，只搬它的**契约**（表结构 + 状态机 + 在跑判定语义），在 Agent 内建一套约 1,200 行的轻量台账，并补上 Manager 到不了的两块真空白：**活动级阶段解析**与 **A2UI 执行看板**。

---

## 1. 事实基线（全部为本次实测，非推断）

### 1.1 规范依据（既有，非本次新立决策）

| 来源 | 原文 | 意义 |
|---|---|---|
| `H:\UltimaAI\INDEX.md` L13 | 「UltimaManager（任务控制面）已登记为 **UltimaAgent 标准基础能力**（2026-10-29）：工单编号核发、全局队列主表登记、接管/来源/授权与前置核验」 | Manager 本就被定性为 Agent 的基础能力，本方案是这条规范的**真正落地** |
| 同 L7（G-DISPATCH-001 自主推进版） | 各项目自主派发 Codex；Manager 保留为可选监督/审计工具 | 内嵌后**不得**让 Agent 缺了就不能派发 |
| 北极星模块1 | `UltimaManager 全局工单登记接口：100% ✅` | 接口确已交付，实测成立（见 1.2） |

### 1.2 Manager 现状（实测）

| 项 | 实测值 |
|---|---|
| 服务 18766 | 无监听、无进程；`state\service-ready-0018.json` 停在 11-01 17:12 |
| 数据 | `H:\UltimaAI\data` 仅 `test-tmp`；Manager 目录递归与 `H:\UltimaAI` 过滤 `manager` 均**未找到任何 sqlite/db 文件** |
| 代码停更 | 最后改动 10-29 |
| 登记接口 | 真实存在：`POST /projects`、`POST /projects/{id}/goals`、`POST /projects/{id}/work-orders`；`server.py` L307 路由、L401 `do_POST`，带 HTTP 鉴权 capability、根目录边界校验、拒绝 shell 插值 |
| 0029 登记位置 | 仅 `_shared\queue\global-queue-index.md` L13976，**未走 18766** |

**结论**：一个 100% 完成的接口，当前调用量 0，数据库从未被创建 → 那 ✅ 是"交付完成"，不是"链路在用"。

### 1.3 Manager 后端的真实体量（决定能不能搬）

| 模块 | 行数 |
|---|---|
| technical_acceptance.py | 7,566 |
| policy_store.py | 3,163 |
| executor.py | 2,839 |
| store.py | 2,198 |
| takeover.py | 376 |
| contracts.py | 447 |
| **依赖链合计（11 模块，含 autonomy / codex_runtime / legacy / runtime）** | **34,152 行** |

`store.py` 不是独立文件：它 `from .executor`、`.policy_store`、`.technical_acceptance`、`.takeover`、`.contracts` 强耦合，二级依赖再引入 4 个模块。**原样"搬零件"不存在——只能整体搬体系。**

### 1.4 Agent 侧已有能力（决定哪些不用重做）

| 能力 | 真实文件 | 状态 |
|---|---|---|
| 编排状态机 + 审批门 + 审计 | `src\brain\orchestration\engine.py`（`LangGraphStateMachine` / `ApprovalGate`，M4 里程碑 2026-10-25 验收 PASS，10/10 测试） | ✅ 已有，不复建 |
| 全局队列登记 | `src\brain\orchestration\queue.py`（461 行，`GlobalQueueRegistrar`） | ✅ 已有 md 主表写入，缺 SQLite 侧 |
| 审计留痕 | `src\brain\orchestration\audit.py`（AuditTrail / AuditRecord / JSONL） | ✅ 已有 |
| 驻留标记 | `src\brain\orchestration\registry.py` | ✅ 已有 |
| A2UI 校验与渲染 | `src\window\a2ui_validator.py`(20,874B)、`active_renderer.py`(19,977B)、`combo_a2ui.py`、`result_to_a2ui.py`、`component_directory.json` | ✅ 链路完备 |
| 消息总线 | `ultima_bus\__init__.py`(368B) + `__main__.py`(48B) | ⚠️ **空壳** |
| 依赖 | venv 内 `langgraph`=已装、`manager`=未装、`fastapi`=未装 | 内嵌不能靠 pip |

### 1.5 三层判定（本方案的唯一依据）

| 层 | Manager 现状 | 判定 | 本方案做什么 |
|---|---|---|---|
| 登记 + 状态机 | 代码齐、schema 全、过独立评审 | **能力在、链路断** | 取契约，Agent 内轻量实现 |
| 活动级阶段语义（"正在写报告"） | 只到 stage/state/PID/耗时 | **真缺口** | 新写阶段解析器 |
| 展示层 | WPF（C# .NET8），Agent 是 PySide6 + A2UI | **真缺口（形态不对）** | 新写 A2UI 看板页 |

---

## 2. 目标与范围冻结

### 2.1 本方案要做（In-scope）

1. 从 Manager `store.py` 提取 5 张核心表的结构契约，冻结为 Agent 侧 schema 基线（对齐，不复制实现）。
2. 在 `src\brain\ledger\` 新建轻量 SQLite 台账，实现工单登记、状态流转、CAS、事务。
3. 登记台**双写**：已有 `GlobalQueueRegistrar` 写 `global-queue-index.md` + 新 ledger 写 SQLite，同一工单号；**ledger 失败不阻断派发**。
4. 新写**活动级阶段解析器**，从 `tasks\queue\runs\<wo>\dispatch.out.log` 事件推出"整理补丁 / 运行验证 / 正在写报告 / 等待模型"等活动级阶段。
5. 新写 **A2UI 执行看板页**，字段对齐 Manager `ExecutionRow` 的 14 项，替掉北极星 HTML 的手填区块数据源。
6. 审批门接 ledger：`ApprovalGate` 决策落 `approvals` + `events`。
7. 降级与自愈：ledger 不可用→只写 md；恢复后按 md 对账补登。

### 2.2 本方案明确不做（Non-goals，硬边界）

1. **不启用 WPF 版 UltimaManager 桌面端**，不为其补功能、不打包、不维护。
2. **不搬运 Manager 的 34,152 行后端代码**，不做全量 vendoring，不改 `H:\UltimaAI\UltimaManager` 目录内任何文件。
3. **不恢复 18766 常驻服务**作为派发链路必备环节；18766 若将来恢复，仅作外部兼容入口。
4. **不把 Manager 变成"必须存在"的依赖**；Agent 缺 ledger 时仍能正常派发。
5. 不改 M4 已验收的 LangGraph 条件边语义（审批门 fail-closed 行为）。
6. 不重写 `GlobalQueueRegistrar` 现有 md 主表格式与工单号规则。
7. 本阶段不改北极星 HTML 的数据源（只提供数据接口，切换留到 T7 评估）。

---

## 3. 关键设计决策（本方案唯一需要 Owner 知晓的取舍）

### 3.1 内嵌方式三选一

| 方式 | 复用度 | 引入体量 | 分叉风险 | 判断 |
|---|---|---|---|---|
| A. 全量 vendoring（把 11 模块复制进 Agent） | 高 | **34,152 行** | 高（无同步机制，Manager 修 bug 需手工再搬） | **否** |
| B. 目录挂载 import（sys.path 指 `UltimaManager\src`，进程内 `from manager.store import Store`） | 高 | 0 行 | 低 | 备选 |
| C. **契约复用 + 轻量实现**（取 schema/状态机/语义，Agent 内重写约 1,200 行） | 中高 | **约 1,200 行** | 无 | **✅ 选此** |

**选 C 的三条理由**：

1. **体量**：A 会把 3.4 万行塞进一个完成度 67% 的主干，等于让 Agent 变成 Manager 的宿主，主进程单点风险陡增；这恰是"启用了 Manager"，与 Owner 口径相反。
2. **规范**：INDEX L13 定义的是"**基础能力**"，能力 = 契约 + 语义 + 字段，不是"整套代码"。
3. **可持续**：B 的 0 行最省，但 Agent 从此依赖 `H:\UltimaAI\UltimaManager` 目录存在且不被重构，属跨项目路径耦合；C 无此依赖。

**C 的代价**（必须写明）：延迟重写、与 Manager 实现不同步。缓解措施——schema 与状态取值**逐字段对齐**（T0 冻结），Manager 若将来恢复，两边同 schema 可直接对账互通，不产生两套口径。

### 3.2 契约基线（从 `store.py` 实测提取，13 表）

核心 5 表：

| 表 | 字段数 | 关键字段 |
|---|---|---|
| `work_orders` | 14 | project_id / work_order_id / goal_id / title / category / **state** / revision / source_hash / write_scope_json / acceptance_json / idle_reason / reservation / version / created_at / updated_at |
| `runs` | 26 | 上述主键 + stage_id / run_id / **phase** / state / source_hash / cwd / allowed_write_roots_json / evidence_dir / reservation / created_at(REAL) / **pid** / **process_identity** / exit_code / **started_at** / finished_at / receipt_status / receipt_evidence_json / review_findings_json / delivery_source_hash / acceptance_result_json / transport_facts_json |
| `stages` | — | stage 级状态机（set_stage_state） |
| `approvals` | — | 审批决策留痕 |
| `events` | — | 事件流（add_event） |

**"是否真在跑"的判定（与 Manager `ExecutionBoard` 一致，不得改）**：
`state == "running"` **且** `pid > 0` **且** `process_identity` 非空 → 三者同时成立才算在跑；耗时按 `started_at` 自动算，不由人填。

### 3.3 与既有能力的接线关系

```
派发（项目自主，G-DISPATCH-001）
   └─ GlobalQueueRegistrar（已有 queue.py 461 行）→ global-queue-index.md
   └─ LedgerRegistrar（新，T2）→ ledger.sqlite （失败=degraded，不阻断）
                                   ↑
编排（已有 orchestration/engine.py）      │
   ├ LangGraphStateMachine ─ T1/T5 状态回写 ┘
   └ ApprovalGate ─────────── T5 审批决策落 approval
                                   ↓
展示（新，T4）A2UI 看板页 ← runs.phase/runs.state + 阶段解析器(T3)
```

---

## 4. 写域（文件级，禁止超出）

### 4.1 新建

| 路径 | 作用 |
|---|---|
| `docs\specs\ledger-schema-contract.md` | T0 冻结的 5 表契约基线（含来源行号） |
| `src\brain\ledger\__init__.py` | 包导出 |
| `src\brain\ledger\schema.sql` | 5 表 DDL（对齐 Manager） |
| `src\brain\ledger\store.py` | 轻量台账（put/lists/CAS/事务） |
| `src\brain\ledger\registrar.py` | 双写登记台（md + sqlite） |
| `src\brain\ledger\stage_parser.py` | 活动级阶段解析器 |
| `src\brain\ledger\health.py` | 降级与对账补登 |
| `src\brain\ledger\tests\` | 各 T 单元测试 |
| `src\window\combo_board.py` | A2UI 看板页（内容驱动布局，不写死尺寸） |
| `docs\specs\board-a2ui-contract.md` | 看板 14 字段与三态着色契约 |

### 4.2 改（仅小改，改前落备份）

| 路径 | 改什么 | 边界 |
|---|---|---|
| `src\brain\orchestration\queue.py` | `GlobalQueueRegistrar` 增加可选的 ledger 双写调用 | 不改 md 格式、不改工单号规则 |
| `src\brain\orchestration\engine.py` | `ApprovalGate` 决策外抛事件给 ledger | 不改 LangGraph 条件边语义 |

### 4.3 硬禁止写域

`H:\UltimaAI\UltimaManager\**`（只读参照）、`北极星上线任务清单.html`（本阶段不改数据源）、`ultima_bus\**`（本阶段不补总线，另立单）

---

## 5. 验收口径

| 项 | 通过标准 |
|---|---|
| 契约一致性 | `ledger-schema-contract.md` 与 `UltimaManager\src\manager\store.py` 逐字段脚本比对，5 表全字段 0 差异 |
| 台账正确性 | pytest ≥ 8 用例全绿（CAS 冲突、并发写、幂等、事务回滚） |
| 双写与降级 | ledger 故障注入下派发成功、md 正常、状态标记 `degraded`；恢复后对账补登 0 遗漏 |
| 阶段解析 | 用 0029 真实 `dispatch.out.log`（实测 512 条事件）跑，产出阶段时间线；覆盖 ≥6 类事件，未知归 other，不吞异常 |
| 看板 | `a2ui_validator` 通过；注入 0029 数据渲染出 14 字段；三态着色正确；"在跑"三要素缺一即不算运行中 |
| 审批门 | hold → `approvals` 有记录且 ledger 标 blocked；approve 后继续；审计 JSONL 对应行存在 |
| 回归 | M4 既有 10 项测试仍全绿（审批门 fail-closed 未被破坏） |
| 测试解释器 | 一律 `H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe`，`-o addopts=` 覆盖 |

---

## 6. 风险与缓解

| 风险 | 影响 | 缓解 |
|---|---|---|
| 契约漂移（Manager 后续再改 schema） | 两套口径 | T0 记录来源 revision；schema 变更需重跑 T0 比对 |
| 主进程单点（ledger 挂了看板空） | 可视化中断 | T6 降级：ledger 不可用→看板退化为 md 主表 + 进程表兜底 |
| 阶段解析误判 | 显示错误活动 | 只做"证据驱动"映射（事件类型→阶段），不做语义推断；未知事件保留 other 并原样展示触发事件 |
| 工程量（7 个 T） | 交付周期长 | T0→T2 先出底座（可独立验收），T3→T4 出缺口，T5→T6 出治理；三门控可分批派发 |

---

## 7. 时序建议

1. **前置**：0029 收口（报告 + final-message 落盘）。
2. **本方案**：Owner 过目 → 冻结 tag `agent-m4-ledger-plan-frozen-20261108`。
3. **派发**：T0→T2 一批（底座，可独立验收）；T3→T4 一批（真缺口）；T5→T6 一批（治理）。
4. **后置**：T7 总验收 → `stage4-ledger-frozen` tag → 评估北极星 HTML 数据源切换。

---

## 8. 引用

- `H:\UltimaAI\INDEX.md` L7 / L13（G-DISPATCH-001 自主推进版、Manager 能力登记）
- `H:\UltimaAI\UltimaAgent\docs\milestones\M4-orchestration-20261025.md`（编排层已验收基线）
- `H:\UltimaAI\UltimaManager\src\manager\store.py`（13 表 schema 来源）
- `H:\UltimaAI\UltimaManager\src\UltimaManager.Desktop\ExecutionBoard.cs`（14 字段与在跑判定来源）
- `H:\UltimaAI\UltimaManager\docs\api-v1.md`（登记端点语义）
- `H:\UltimaAI\_shared\queue\global-queue-index.md` L13976（0029 实登记位置）
