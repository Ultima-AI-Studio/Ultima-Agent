# G-ORCH 从 edict 组装看板状态机（第一块地基）

> 日期：2026-11-09 ｜ 性质：源码组装，非自研 ｜ 来源仓库：`cft0808/edict`（~17,049★）
> 验证：`tests/test_gorch_kanban.py` 8 passed / 7.73s

---

## §1 一句话

从 edict 原样搬入 **3 个纯 Python 文件**（标准库 + 同目录依赖，零第三方包），改 **8 处**硬编码，落到我方 `scripts/gorch/` 与 `data/gorch/`，得到一套**可跑、可测、不可绕过**的任务状态机 + 并发安全看板。**未引入 OpenClaw**。

---

## §2 搬入清单

| 文件 | 来源 | 大小 | 改动 |
|---|---|---|---|
| `scripts/gorch/file_lock.py` | `edict/scripts/file_lock.py` | 4,072B | **零改动** |
| `scripts/gorch/utils.py` | `edict/scripts/utils.py` | 2,227B | 删 `get_openclaw_home()`；改模块说明 |
| `scripts/gorch/kanban_update.py` | `edict/scripts/kanban_update.py` | 41,526B | 6 处路径/环境变量 |
| `data/gorch/tasks_source.json` | 新建 | — | `[]` 初始看板 |
| `tests/test_gorch_kanban.py` | 新建 | — | 8 条验收用例 |

**依赖核查**：`kanban_update.py` 只 import `datetime / json / pathlib / sys / subprocess / logging / os / re`（全标准库）+ 同目录 `utils.python_bin`、`file_lock.atomic_json_*`。**无任何第三方包、无 OpenClaw 运行时依赖**。

---

## §3 改动了哪 8 处

| # | 位置 | 原值 | 改后 | 原因 |
|---|---|---|---|---|
| 1 | `_BASE` | `parent.parent` | `parent.parent.parent` | 指向 `UltimaAgent` 根 |
| 2 | 新增 `GORCH_DATA` | — | `_BASE/data/gorch`（可用 `GORCH_DATA` 环境变量覆盖） | 数据与 `data/evidence/` 隔离 |
| 3 | `TASKS_FILE` | `_BASE/data/tasks_source.json` | `GORCH_DATA/tasks_source.json` | 同上 |
| 4 | `_REFRESH_SIGNAL_FILE` | `_BASE/data/.refresh_pending` | `GORCH_DATA/.refresh_pending` | 同上 |
| 5 | `AUDIT_FILE` | `_BASE/data/audit_log.json` | `GORCH_DATA/audit_log.json` | 同上 |
| 6 | `TASK_MEMORY_DIR` | `_BASE/data/task_memory` | `GORCH_DATA/task_memory` | 同上 |
| 7 | `_trigger_refresh()` | 直接 fork 刷新脚本 | 前置 `if not REFRESH_SCRIPT.exists(): return` | 我方未部署 edict 看板 watcher |
| 8 | `_infer_agent_id_from_runtime()` | `OPENCLAW_AGENT_ID, OPENCLAW_AGENT, AGENT_ID` | `ULTIMA_AGENT_ID, AGENT_ID, OPENCLAW_*` | 换成我方身份标识，保留旧名兼容 |

---

## §4 状态机：12 态与我方八跳的映射

`_VALID_TRANSITIONS`（`kanban_update.py` 内置 fallback，edict 原文）：

```
Pending        → {Taizi, Cancelled}
Taizi          → {Zhongshu, Cancelled}
Zhongshu       → {Menxia, Cancelled, Blocked}
Menxia         → {Assigned, Zhongshu*, Cancelled}          *封驳回退
Assigned       → {Doing, Next, Blocked, Cancelled}
Next           → {Doing, Blocked, Cancelled}
Doing          → {Review, Done, Blocked, Cancelled}
Review         → {Done, Menxia*, Doing, Cancelled, PendingConfirm}   *复检退回
PendingConfirm → {Done, Review, Cancelled}
Blocked        → {Taizi, Zhongshu, Menxia, Assigned, Next, Doing, Review, Cancelled}
Done / Cancelled → 终态，不可再出
```

| 我方八跳 | 对应状态 | 说明 |
|---|---|---|
| ① 需求登记 | `Pending` | 主脑收旨，只登记不加工 |
| 主脑路由 | `Taizi` | 主脑分拣，无 confirm/delegate 权限 |
| ② 理解·方案 / ③ 拆解·工单 | `Zhongshu` | DeepSeek 同一角色两阶段 |
| Owner 确认 / DeepSeek 审议 | `Menxia` | 准奏→Assigned；封驳→回 Zhongshu |
| ④ 批准授权 / ⑤ 派发 | `Assigned` | 主脑回传授权条件后派发 |
| Codex 执行 | `Doing` | 只有执行位可 `done`/`block` |
| ⑥ DeepSeek 复检 | `Review` | 退回→Menxia；通过→Done 前必过确认 |
| ⑦ 判据审计 / ⑧ 冻结 | `Review→PendingConfirm→Done` | **完结被强制人工确认** |
| 异常退场 | `Blocked` | 可回 8 个状态任一 |

---

## §5 权限矩阵与铁律 §9 逐条对照

`AGENT_POLICY`（edict 原文，纯字典，未改）：

| 角色 | 允许命令 | 对照铁律 §9 |
|---|---|---|
| `taizi` | create, state, flow, progress, todo, memory, task-memo | **无 confirm、无 delegate** → §9-1「主脑不判不审不派」✓ |
| `zhongshu` | state, flow, progress, todo, memory, task-memo, delegate | 拆解 + 可委派 ✓ |
| `menxia` | state, flow, progress, todo, **confirm**, memory, task-memo | 审议 + 准奏权 ✓ |
| `shangshu` | state, flow, progress, todo, confirm, delegate, memory, task-memo, shared-memo | 派发 ✓ |
| 六部 + `libu_hr` | progress, todo, **done**, **block**, memory, task-memo, delegate-result | **无 confirm** → §9-3「Codex 不做审查裁决」✓ |

**结论**：edict 的角色权限划分与我方「主脑不判 / 外脑编排 / 执行端不裁决」**天然同构**，无需改造。

---

## §6 实测结果（8 项全绿）

| # | 用例 | 结果 |
|---|---|---|
| 1 | 合法全链 `Pending→Taizi→Zhongshu→Menxia→Assigned→Doing→Review` 逐跳放行 | PASS |
| 2 | `Taizi→Doing` 跳步被拒，状态不变 | PASS |
| 3 | `Review→Done` 被拦进 `PendingConfirm`，`confirm_by=menxia` | PASS |
| 4 | `confirm approve` → 落 `Done` | PASS |
| 5 | `confirm reject` → 退回 `Review` | PASS |
| 6 | 非 `PendingConfirm` 态执行 confirm 被拒 | PASS |
| 7 | **8 进程并发 create，9 条零丢失** | PASS |
| 8 | 执行端（`bingbu`）执行 `create` 越权 → exit 1 | PASS |

---

## §7 未搬入的部分（及原因）

| 未搬 | 原因 |
|---|---|
| **OpenClaw** | 是 edict 的**运行环境**不是 edict 的代码。引入等于再套一层别人家的框架，与「组装源码」相反。**已全局卸载（removed 508 packages，`openclaw.cmd` 已不存在）** |
| `edict/backend/`（FastAPI + Postgres + Redis） | 重依赖，我方看板用 JSON 文件足够；edict 自己也说两模式独立 |
| `install.ps1` / `install.sh` | 是「把 edict 装进 OpenClaw」的安装器，不适用 |
| `sync_from_openclaw_runtime.py` | 读 OpenClaw 运行时状态 |
| `refresh_live_data.py` | 我方看板刷新由自己控制，不需要定时 fork |
| `agents/*/SOUL.md`（12 份） | **可复用，但需改**：原文让 LLM 自己写代码（`bingbu/SOUL.md:9-13`），与「Codex 写码」冲突。留待下一步 |
| `agents.json` 权限矩阵 | 与上面的 `AGENT_POLICY` 重复，先不引入第二份权威 |

---

## §8 这块补上了什么

| 之前的缺口 | 现在 |
|---|---|
| 状态机是我方 `state_machine.py` 自写 8 态 | 换成 edict 12 态，含 `PendingConfirm` 人工确认门 |
| 流转非法跳转靠约定 | 代码层强制拒绝（`_VALID_TRANSITIONS`） |
| 多通道并发写队列零锁 | `file_lock.py` 原生 Windows `msvcrt` + tmpfile rename |
| 完结无强制确认 | `Review→Done` 必过 `PendingConfirm`，记 `confirm_by` |
| 无审计轨迹 | `audit_log.json` 记 5,000 条环形审计 |

---

## §9 局限（明写，不掩盖）

1. **本报告不是独立复核**：改码与验证同一手，属自证。正式验收仍待外脑 DeepSeek 接线。
2. 只验证了「状态机 + 看板 + 并发写」这一块，**八跳链路本身仍无一行接线**（8B 主脑未接入、DeepSeek 未接派发链、多 Codex 通道未开）。
3. `_infer_agent_id_from_runtime` 在不设 `ULTIMA_AGENT_ID` 时用**状态反推**身份（例如 Review 态反推成 `shangshu`），这是推断不是事实；正式运行必须显式设环境变量。
4. `flow_log` 只由 `flow` 命令写入，`state` 命令不改 `flow_log`——这是 edict 原设计（状态与流转分离），使用时两条命令都要调。
