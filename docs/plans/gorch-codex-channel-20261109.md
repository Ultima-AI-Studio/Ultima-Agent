# G-ORCH 执行段替换为 Codex

> 日期：2026-11-09 ｜ 前置：`f426728c`（看板状态机组装完成）
> 性质：源码改装，非自研

---

## §0 一句话

流水线只有一条：**接单 → Codex 执行 → 回写 → 交复检**。

不设部门分工、不用官场称谓。通道号 1–6 只用于并发时区分各自的运行目录与看板标签，六个通道能力完全相同，接什么活由工单决定。

---

## §1 不动的东西

| 对象 | 处置 | 理由 |
|---|---|---|
| `_VALID_TRANSITIONS` 状态机 | **不动** | `Doing → Review` 已够用；调整它等于改 edict 的安全边界 |
| `AGENT_POLICY` 权限表 | **不动** | 六个执行位命令集本就无 `confirm` —— 正好是「执行段不裁决」 |
| `file_lock.py` | **不动** | 并发写已带锁 |
| `STATE_ORG_MAP` / `_AGENT_LABELS` 的**值** | **改（仅显示层）** | 官场称谓换成现代用语：分拣/规划/审批/已派发/执行中/复检/待确认/待受理 |
| `_ORG_AGENT_MAP` | **追加键，不删旧键** | 旧中文名仍能反查 agent id，历史任务数据不受影响 |
| `cmd_done` 内部文案 | **改（仅字符串）** | `→尚书省` 改为 `→复检`；判断逻辑一字未动 |

**逻辑零改动，显示层文案本地化。** 改的都是 `t['org']`、`flow_log` 的 `to`、`now` 这类给人看的值，没有任何判断分支受影响 —— 回归 16 条用例通过即为证。

---

## §2 一份执行通道 SOUL.md

路径 `agents/execution/SOUL.md`，**只有一份**，不再按职能拆六份。

| 节 | 内容 |
|---|---|
| 角色 | 执行通道，被派发段以 subagent 方式调用 |
| 首条约束 | **执行者是 Codex，不是你** —— 不写代码、不做验收判断、不裁决 |
| 核心职责 5 条 | 接单 → 更新看板 → 调 Codex → 完成后交复检 → 失败即标阻塞 |
| 边界 4 条 | 不改工单/主表、不 `confirm`、自检不算验收、不判断写域冲突 |
| 看板操作 | 接单/执行/完成/阻塞四段命令，全部走 CLI |
| 进展上报 | 三处必报 + `progress` 不改状态的提醒 |
| 状态名对照 | 代码状态 ↔ 中文含义 12 行对照表 |

**为什么不再按职能分六份**：六个通道做的是同一件事（把工单交给 Codex），差异只在并发占用的目录。写六份同构文档是重复，且会诱导「这个通道只接工程活」的误解——分工应该体现在工单里，不体现在角色卡上。

---

## §3 执行器 `scripts/gorch/codex_channel.py`

### 复用清单

| 能力 | 来源 | 怎么用 |
|---|---|---|
| Codex 可执行体解析 | `scripts/dispatch-work-order.py:143 resolve_codex_exe()` | 逻辑照搬：env → PATH → 四组 glob 按 mtime 取最新 |
| Codex 调用命令 | `scripts/dispatch-work-order.py:491-494`（已跑 11 轮） | `codex exec -a never -c model_reasoning_effort=... -m gpt-5.6-sol -C <dir> --sandbox danger-full-access --skip-git-repo-check --output-last-message <out> -`，去掉 `--json` 流式事件 |
| 看板回写 | `scripts/gorch/kanban_update.py`（edict 移植） | `state`/`flow`/`progress`/`done`/`block`，不直接读写 JSON |
| 并发写安全 | `scripts/gorch/file_lock.py` | 看板写入已带锁 |

### 流程

```
codex_channel.py --task <任务号> --channel <1-6> --prompt <工单> [--workdir <worktree>]

1. 读工单 → 空则拒（rc=2，任何看板动作之前）
2. state Doing（任务已在 Doing 时状态机拒绝，记 already_doing 后继续）
3. flow "通道N" "通道N" "▶️ 开始执行"
4. progress "接单✅|调Codex🔄|执行|自检|回写"
5. 起 Codex，prompt 从 stdin 喂入，输出落 run-dir
6. 成功 → progress 全✅ → done（Doing→Review，自带一条 →复检 的 flow）
   失败 → progress 标 🚫 → block（写退出码与末段日志）→ flow →派发段
7. 写 run-dir/codex-channel.json：channel / exit_code / 耗时 / prompt_sha256 / codex 路径
```

**为什么不额外写一条 flow**：`done` 命令内部已经写 `→复检`，执行器再写一条会在 `flow_log` 里出现两条去向相同的记录（实测发现并已去掉）。

---

## §4 多通道并发

| 项 | 做法 |
|---|---|
| 隔离五件套 | 独立 worktree / 独立分支 / 独立 run-dir / 独占写域 / 独立审计单，缺一不合法 |
| 通道标识 | `--channel 1..6`，写入 run-dir 名 `data/gorch/runs/<task>-ch<N>-<ts>` 与 flow 标签 |
| 写域冲突 | **不在执行器判断**，由派发段在拆解时切分；冲突应在拆解阶段被拦下 |
| worktree 成本 | `git worktree add --detach` 实测 24.8s / 35,824 文件；6 通道串行约 2.5 分钟，首次建好后复用 |

**并发瓶颈不在开几个 Codex，在拆解阶段写域切得干不干净** —— 此前实测结论，本阶段不变。

---

## §5 验收判据

| # | 判据 | 机检方式 | 结果 |
|---|---|---|---|
| V1 | SOUL.md 明确「执行者是 Codex」，且不含授予本通道写代码/改代码的语句 | 文本检索 `写代码` + 人工核对 | ✅ |
| V2 | 成功时看板 `Doing → Review` | 读 `tasks_source.json` | ✅ dry-run + 真跑 |
| V3 | 失败时落 `Blocked` 且 `block` 写明退出码 | 同上 | ✅ dry-run |
| V4 | 执行段不调 `confirm` | 静态 grep 零命中 | ✅ |
| V5 | 全程只写自己 run-dir 与看板 | 比对 worktree 状态 | ✅ 真跑隔离在临时目录 |
| V6 | 并发不丢条目 | 复用看板 8 进程并发用例 | ⚠️ 仅看板层，通道层未跑 |
| V7 | 看板可见文案无官场称谓 | grep 官职词，仅允许残留在 `_ORG_AGENT_MAP` 兼容键与注释 | ✅ |

> V1 原定「与 edict 原文逐字一致」，因改写为现代用语而废弃。逐字照抄 edict 的官场角色卡对本系统没有信息量，保留它等于保留噪音。

---

## §6 本方案不做的

- 不做部门职能分工 —— 分工写进工单，不写进角色卡
- 不引 OpenClaw 或任何 agent 运行时框架
- 不改状态机逻辑、不改 `AGENT_POLICY`、不改 `file_lock.py`
- 不做串行合并队列（Phase 2）
