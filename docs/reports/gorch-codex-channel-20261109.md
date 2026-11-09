# 执行段替换为 Codex · 结果报告

> 日期：2026-11-09 ｜ 前置 `f426728c`（看板状态机组装完成）
> 本报告取代同日早前按 edict「六部」框架写的那版；那版把官场称谓一并搬了进来，已作废。

---

## §0 结论

执行段换成了 Codex，形态是一条流水线：**接单 → Codex 执行 → 回写 → 交复检**。不设部门分工，不用官场称谓。

- 执行器 `scripts/gorch/codex_channel.py`：真跑通过（见 §3）
- 角色说明 `agents/execution/SOUL.md`：一份，现代公司用语
- 看板显示层：官场称谓换成流水线用语，**状态机逻辑一字未动**
- 回归：`test_gorch_kanban.py` + `test_gorch_codex_channel.py` 共 **16 passed / 18.78s**

---

## §1 形态

流水线只关心四件事，不问"这是哪个部门"：

```
派发段 ──工单(含写域/验收门)──▶ 执行通道 ──调 Codex──▶ Codex
                                      ◀──产出+自检──┘
                                      ──done(Doing→Review)──▶ 复检段
```

通道号 1–6 只用于并发时区分 `run-dir` 与看板标签，**不承载职能语义**。六个通道能力相同，接什么活由工单决定。

---

## §2 改了什么

### 2.1 代码（逻辑零改动，仅显示层）

`scripts/gorch/kanban_update.py` 改了 15 处，全部是**给人看的字符串**，没有任何判断分支被触及：

| 位置 | 原值 | 新值 |
|---|---|---|
| `STATE_ORG_MAP`（11 项） | 太子/中书省/门下省/尚书省 | 分拣/规划/审批/已派发/排队/执行中/复检/待确认/待受理 |
| `_AGENT_LABELS` | main→太子、libu→礼部… | 分拣、规划、审批、派发、执行1–执行6 |
| `_ORG_AGENT_MAP` | 仅旧中文名 | **追加**新显示名，旧键全保留（历史数据仍可反查） |
| `create` 默认 remark | `下旨：{title}` | `创建：{title}` |
| `create` 的 flow `from` | `皇上` | `Owner` |
| `cmd_done` 的 `to` + remark | `→尚书省` | `→复检` |

**未改动**：`_VALID_TRANSITIONS`、`HIGH_RISK_TRANSITIONS`、`CONFIRM_AUTHORITY`、`AGENT_POLICY`、`cmd_done` 的状态判断、`file_lock.py`。

### 2.2 角色说明

- 删除：早前按六部抄的 6 份 `agents/gorch/<dept>/SOUL.md`（`git rm`）
- 新增：`agents/execution/SOUL.md` 一份，现代公司用语

### 2.3 执行器

`codex_channel.py` 的 `--dept` 改为 `--channel 1-6`，flow 标签从"兵部"变为"通道N"，记录字段 `dept` → `channel`。同时去掉成功分支里冗余的第二条 flow（`done` 自己已经写 `→复检`）。

---

## §3 实测

| # | 场景 | 结果 |
|---|---|---|
| 1 | dry-run 成功（`--channel 1`） | `state=Review`，`org=复检`，`flow` 三条：`Owner→待受理`、`通道1→通道1`、`通道1→复检` |
| 2 | dry-run 失败（`--channel 5`） | `state=Blocked`，`block="Codex 退出码 1：[dry-run] 未真实执行 Codex"` |
| 3 | 重复接单（任务已在 Doing） | 状态机拒绝被记为 `already_doing` 后继续，不中断 |
| 4 | 空工单 | rc=2，看板保持 `Doing` 未被推进 |
| 5 | **真实 Codex**（`--channel 2`，隔离目录） | 见下 |

| 5 | **真实 Codex**（`--channel 2`，隔离目录 `%TEMP%\gorch-live-2`） | `exit_code=0`，耗时 **143.7s**，`state=Review`，`org=复检`。回读产物：`hello.txt` 真实存在、**6 字节**、内容 `hello` —— 不是只看 exit 0 |

`codex-channel.json` 实录：`prompt_sha256=9a669a10…af61`、`codex` 为 WindowsApps 下的绝对路径、`workdir` 为隔离临时目录、`already_doing=true`、起止时间完整。

---

## §4 本轮修正的错误

三处，都是我自己造出来的，记录在此：

1. **把 edict 角色卡按摘要重述成"契约等价"**。原文 96 行被我压成 68 行，删掉「subagent 执行完直接返回」、`24h 审计预警`、`libu_hr 负责人事`、4 个上报时点、命令完整参考 5 处有功能的原文，又加了 4 处原文没有的铁律。**更糟的是：删掉「libu_hr 负责人事」之后，我在报告里写「libu_hr 定位未定」——删了证据再说证据不明。**
2. **把 `libu` 当成了"吏部"**。edict 原文是 `libu` = **礼部**，`libu_hr` = 吏部。凭摘要记忆写错，读原文才发现。
3. 上一版报告把 dry-run 和真跑三条并列呈现。dry-run 是自证（我让它成功它就成功），只有真跑算数。

---

## §5 判据

| # | 判据 | 结果 |
|---|---|---|
| V1 | SOUL.md 明确「执行者是 Codex」，不授予本通道写代码/改代码 | ✅ |
| V2 | 成功时 `Doing → Review` | ✅ dry-run + 真跑 |
| V3 | 失败时 `Blocked` 且 `block` 写明退出码 | ✅ dry-run |
| V4 | 执行段不调 `confirm` | ✅ 静态 grep 零命中 |
| V5 | 全程只写自管 run-dir 与看板 | ✅ 真跑隔离在临时目录 |
| V6 | 并发不丢条目 | ⚠️ 仅看板层（8 进程零丢失），通道层未跑 |
| V7 | 看板可见文案无官场称谓 | ✅ grep 仅剩 `_ORG_AGENT_MAP` 兼容键与注释 |

V1 原定「与 edict 原文逐字一致」，已废弃——按用户要求改为现代用语后，逐字判据不再成立。逐字照抄官场角色卡对本系统没有信息量。

---

## §6 局限

1. **通道层并发未跑**。六通道同时开工要六个独立 worktree，实测每个 24.8s / 35,824 文件。本轮只做单通道 + 看板层并发。
2. **`--dry-run` 是自证工具**。它证明流程走位正确，不证明 Codex 能干活；两者证据性质不同，本报告已分开陈述。
3. **`libu_hr` 与 `qintianjian` 的角色定位**：`libu_hr` 原文明确是人事/培训/Agent 管理，不是写码；`qintianjian` 未在 `agents.json` 权限矩阵内。两者都不在本次"执行段"范围内，未纳入。
4. **未打 tag**。按铁律，没 tag 不报完成；本轮交付「已实施 + 已验证」，冻结待验收。
