# G-ORCH 六部执行体替换为 Codex 通道

> 日期：2026-11-09 ｜ 前置：`f426728c`（看板状态机组装完成）
> 性质：源码改装，非自研 ｜ 依据：edict `agents/<dept>/SOUL.md` 实测原文

---

## §0 一句话

edict 的六部是「让 LLM 自己写代码」的角色，我方要的是「Codex 写代码」。**角色名、权限、看板命令全部不动**，只做两件事：①把六部 SOUL.md 的执行段改写为「调 Codex」；②加一个通道执行器，替六部去调 Codex 并回写看板。

---

## §1 为什么不动 `AGENT_POLICY` 和状态机

| 顾虑 | 实测结论 |
|---|---|
| 改角色名要不要改权限表？ | **不用**。`AGENT_POLICY` 六个执行位（`hubu`/`libu`/`bingbu`/`xingbu`/`gongbu`/`libu_hr`）命令集完全相同：`progress/todo/done/block/memory/task-memo/delegate-result`，**没有 `confirm`** —— 正好是「执行端不裁决」 |
| 六部名字带部门语义，会误导吗？ | **不会**。保留原名 = 零改代码；语义在 SOUL.md 里重写即可（六部 → Codex 通道 1~6） |
| 需要新增状态吗？ | **不需要**。`Doing`（执行中）→ `Review`（复检）已够用 |

**结论**：改 SOUL.md + 加执行器，代码层零改动。

---

## §2 六部 SOUL.md 实测结构（六份同构）

逐字比对 `bingbu` 与 `hubu`：**只有「专业领域」和「语气」两段不同**，其余五段完全一致。

| 段 | 内容 | 改造 |
|---|---|---|
| ① 角色 + subagent 定位 | 「你是兵部尚书，以 subagent 方式被尚书省调用」 | 改为「你是 Codex 通道 N」 |
| ② 专业领域 | 各不同（工程/数据/法务/财务/后勤/人事） | **删除**，改为「可执行尚书省派发的任意工单」 |
| ③ 核心职责 4 条 | 接任务→更新看板→执行→上报 | 保留，第 3 条「执行任务」改为「起 Codex 执行」 |
| ④ 看板操作 CLI | `state`/`flow`/`progress`/`todo` | **保留原文**（这是与看板通信的唯一合法通道） |
| ⑤ 合规要求 | 三种情况必须更新看板 | **保留原文** |
| ⑥ 实时进展上报 | 四个时点 + 示例 | **保留原文**，补充「Codex 每完成一步由执行器代报」 |
| ⑦ 语气 | 各不同 | 删除 |

**关键保留**：④⑤⑥ 三段是 edict 的「看板契约」，一字不改 —— 这是它能被组装的原因，改了就变成自研。

---

## §3 通道执行器 `scripts/gorch/codex_channel.py`

### 复用清单（不自研）

| 能力 | 来源 | 怎么用 |
|---|---|---|
| Codex 可执行体解析 | 我方 `scripts/dispatch-work-order.py:143 resolve_codex_exe()` | **直接复用**（多路解析：env → PATH → 四组 glob，按 mtime 取最新） |
| Codex 调用命令 | 我方 `run-review-v11.ps1`（已跑 11 轮） | `codex exec -a never -c model_reasoning_effort=high -m gpt-5.6-sol -C <dir> --sandbox danger-full-access --skip-git-repo-check --output-last-message <out> -` |
| 看板回写 | 已组装好的 `scripts/gorch/kanban_update.py` | `state`/`flow`/`progress`/`todo`/`done`/`block` 六个子命令 |
| 并发写安全 | 已组装好的 `scripts/gorch/file_lock.py` | 看板写入已带锁 |

### 执行流程

```
codex_channel.py --task <任务号> --dept <部门> --prompt <工单文件> --run-dir <通道目录>

1. 自检：设 ULTIMA_AGENT_ID=<部门>，确认 AGENT_POLICY 允许（六部只允许 progress/todo/done/block）
2. state  <task> Doing    "<部门>开始执行"
3. flow   <task> "<部门>" "<部门>" "▶️ 开始执行"
4. progress <task> "正在调用 Codex 执行工单" "接单✅|调Codex🔄|执行中|自检|回写"
5. resolve_codex_exe() → subprocess 起 codex exec，prompt 从 stdin 喂入
6. exit 0 → done <task> <产出路径> "<摘要>"  + flow "✅ 完成"
   exit ≠0 → block <task> "<退出码与末段 stderr>" + flow "🚫 阻塞"
7. 全过程写 <run-dir>/codex-channel.json（exit_code / 耗时 / prompt_sha256 / out 路径）
```

### 为什么执行器要独立于 SOUL.md

SOUL.md 是**给 LLM 读的提示词**，只有在 agent 框架里才生效。我方已卸载 OpenClaw，没有 agent 框架 —— 所以执行体必须是脚本。SOUL.md 在这套系统里的作用降级为**角色说明文档 + 未来接入 agent 框架时的现成提示词**。

---

## §4 多通道并发（用户要的部分）

| 通道 | 部门名（代码不动） | 隔离五件套 |
|---|---|---|
| 1 | `hubu` | 独立 worktree / 独立分支 / 独立 run-dir / 独占写域 / 独立审计单 |
| 2 | `libu` | 同上 |
| 3 | `bingbu` | 同上 |
| 4 | `xingbu` | 同上 |
| 5 | `gongbu` | 同上 |
| 6 | `libu_hr` | 同上 |

**并发瓶颈不在开几个 Codex，而在拆解阶段写域切得干不干净**（此前实测结论）。执行器本身不判断写域冲突，只在 `--write-scope` 参数里接收尚书省给的写域清单，启动前校验 worktree 是否干净。

**worktree 成本实测**：`git worktree add --detach` 24.8s / 35,824 文件。6 通道串行创建约 2.5 分钟，建议首次创建后复用，不每单重建。

---

## §5 验收判据（先定，后施工）

| # | 判据 | 机检方式 |
|---|---|---|
| V1 | 六部 SOUL.md 的 ④⑤⑥ 三段与 edict 原文逐字一致 | diff 比对（除角色名替换外零差异） |
| V2 | 执行器调 Codex 成功时，看板 `state` 从 `Doing` 推进到 `Review` | 读 `tasks_source.json` |
| V3 | Codex 失败时，看板落 `Blocked` 且 `block` 字段写明退出码 | 同上 |
| V4 | 执行器不调用 `confirm`（无裁决权） | 静态 grep `confirm` 零命中 |
| V5 | 单通道执行全程仅写自己 run-dir 与看板 | 比对 worktree 状态 |
| V6 | 并发 2 通道同时执行，看板无丢条目 | 复用 `test_gorch_kanban.py::test_concurrent_create_no_loss` 模式 |

---

## §6 本方案不做的

- 不做「六部专业分工」——Codex 不区分领域，分工进入工单内容而非角色
- 不引 OpenClaw 或其替代 agent 框架
- 不改 `AGENT_POLICY`、不改状态机、不改 `file_lock.py`
- 不在本阶段做串行合并队列（那是 Phase 2）
