# G-ORCH 派发链路 fail-open 闭环（第四轮）· 2026-11-09

> 提交 `2a446b9a` · tag `gorch-r4-failopen-closeout-20261109` · 分支 `codex/voice-fsmn-new-path`
> 基线 `4d4df55f`（第三轮闭环文档）→ 上一版代码 `595ed52a`（第三轮闭环）
> 改动：4 文件 / 743+ / 104- · 验证：`90 passed in 37.57s`（两 gorch 测试文件）

## 一、为什么有这一轮

用户固定流程是「助手闭环 → Codex 独立审计 → 一致则 Codex 出修复实现 → 助手复审」。
第三轮 Codex 审计（`rc=0` / `699.3s` / `22523 bytes`）的结论是**「部分一致」而非「一致」**，
列出 6 类 10 条未闭合项——其中多条是助手上一版（`595ed52a`）自己引入的 fail-open。

因为第③环的前提「结论一致」没满足，助手改为**回到第①环自己再修一轮**：把审计 10 条
逐条落进源码，然后再交 Codex 做第四轮审计。本报告记录的就是这一轮。

## 二、10 条 → 修复映射

| # | 审计指出的 fail-open | 本轮落点 |
|---|---|---|
| 1a | 新执行在落 `codex-channel.json` 前失败（空 prompt/找不到执行体）→ 旧 done 仍是唯一真实记录 | `record` 在任何前置校验之前建立；新增 `_fail_early(code, reason)`，空工单（2）与找不到执行体（3）都先落一条 `result=blocked` 记录 |
| 1b | 新记录 JSON 损坏/半写入被 `continue` 静默跳过 → 回退旧 done | `find_done_tasks` 在 `run_dirs` 模式下：记录损坏 → `stale` 阻断（不再 `continue`） |
| 1c | glob 固定 `RUNS/<task>-ch*/`，但执行器允许任意 `--run-dir` → 新 blocked 漏匹配 | `execute` 逐任务显式 `--run-dir` 并把 `run_dir` 回传；`find_done_tasks(run_dirs=)` 只读本次登记的那条路径 |
| 1d | 「最新」靠 `st_mtime`，并列时依赖 glob 枚举顺序 | run 模式不再按 mtime 取最新，改由 invocation 绑定的 run-dir 决定 |
| 1e | `run --dry-run` 仍继续真实 merge / cleanup | `run_all(dry_run=True)` 在 execute 之后 `_stop('dry_run')`，不合并不清理 |
| 1f | `stale` 只进 `not_merged`、不算失败，`stopped_at` 仍 `done`、退出码 0 | `stale or leftover` → `_stop('merge')`；CLI `run` 退出码改为 `stopped_at == 'done'` |
| 2 | stderr 只审前 200 字符；噪声是子串白名单，真错误含 `cygheap` 就被吞 | `gate_check` 先全量逐行分类（`real_errs`），再展示前 3 行 + 「共 N 行真错误」；`_CYGWIN_NOISE` 改为整行锚定 `match` |
| 4 | 判据只有 porcelain 行集合：同文件续改误杀、`?? out/` 下新文件看不见、` M`→`M ` 只因 `git add` 就 fail-open；基线 `error/not_repo` 不阻断 | 新增 `worktree_fingerprint`（`diff_sha = sha256(git diff HEAD)` + 未跟踪路径集合 + 状态行）与 `fresh_changes`（内容级增量）；新增 `_BaselineUnusable`，基线 `error`／未放行的 `not_repo` 在起 Codex 前抛错阻断 |
| 7 | `wt_remove` 把 `TimeoutExpired` 转 `SystemExit`，cleanup 拿不到非零结果、回读永不执行；目录消失不查分支直接算成功；`_branch_exists` 不查 rc；不核对 `worktree list --porcelain` | `wt_remove` 超时返回 `CompletedProcess(returncode=-1)`；新增 `_branch_state`（`show-ref --verify`，rc 非 0/1 即 `unknown`）与 `_worktree_registered`；`cleanup` 改为三处回读，三处都消失才算 `removed`，半清理态与 `retained_unmerged` 一律 `partial` |
| 8 | `run_all`/`merge` 一串假成功：execute 非零照进 merge、merge 扫全批历史 done、`{"merged": false}` 记成功、无 ready 时 `steps` 缺 `merge` 键、冲突后清掉未尝试任务、target 到 merge 才动态读 | `run_all` 整段重写：开始时固定 `invocation` 与 `target`；execute 任一非零 `_stop('execute')`；`merge(tasks=ready ∩ done, run_dirs=...)`；要求 `merged is True` 且 branch/target 一致；cleanup 只清已确认合并成功的任务；`_stop` 统一补齐 merge/cleanup 骨架；`stopped_at` 覆盖 gate/provision/execute/dry_run/merge/cleanup/done |
| 6 | `no_change_allowed` 把 clean 执行记成普通可合并 `done` | 置 `mergeable=False`，终态 `done_no_merge`，`find_done_tasks` 不把它放进合并池 |

## 三、三处设计取舍（与审计口径不同，需 Owner 认）

1. **执行前 worktree 是否必须 clean**：审计主张「拒绝复用脏基线，进显式恢复流程」；
   本轮选择「允许脏基线 + 内容级指纹 + 基线不可读即阻断」。理由是 `wt merge` 本身会把
   工作区改动卷进 squash（并备份到 `refs/wt-backup/<branch>`），强行要求 clean 会让
   现有的全链批次直接跑不起来。指纹方案同样堵住了「既有脏项算本轮新增」这条 fail-open。
2. **`done_no_merge` 是契约变更**：新增了一个非合并终态名。审计第 6 条要求「纯验证任务
   独立非合并终态」，但状态名由助手拟定，需 Owner 落定。
3. **`wt_remove` 超时语义**：改为结构化返回（`returncode=-1`）而不是抛异常，让 cleanup
   能统一走「rc 非 0 → 回读三处」的路径。

## 四、验证

- `py_compile`：两个模块均通过。
- `pytest -o addopts= -p no:cacheprovider tests\test_gorch_batch_orchestrator.py tests\test_gorch_codex_channel.py`
  → **90 passed in 37.57s**（batch 68 + codex_channel 22）。
- 新增 / 替换用例 20 条，逐一对应上表判据，含正反例：
  内容级指纹（同状态行内容变化 / 未跟踪目录新增）、基线 `error` 与 `not_repo` 阻断、
  空工单仍落 blocked 记录、stderr 第 200 字符之后的真错误、`cygheap` 整行锚定双向、
  `_branch_state` 三态、`wt_remove` 超时结构化返回、半清理态 / 三处全消失 / 分支查询
  `unknown`、`retained_unmerged` 不计成功、本 invocation 绑定与损坏记录阻断、
  `done_no_merge` 不可合并、`merged false` 计失败、execute 非零即停、dry-run 不合并不
  清理、无 ready 时 `steps` 键完整。
- 本轮自查另补一处：`wt merge` 的 JSON 里 branch/target 可能带 `refs/heads/` 前缀，
  直接字符串比对会把「合成功、只是写法不同」误判为目标不符 → 加 `_norm_ref` 归一化。

## 五、仍未闭合（本报告如实登记，不宣称完成）

1. **八跳第 4 跳（主脑回传授权条件）仍未进 `run_all`**，链路仍止于 cleanup——审计第 8 条
   已明确这阻塞八跳真跑。
2. **冲突形态的全链未真跑**：`run` 遇 `CONFLICT` 时 `keep` + `stopped_at='merge'` 只有单测；
   上一次真跑是三卡/MM 的 `wt merge` 冲突（证据在 `evidence/gorch-conflict-verify-20261109/`）。
3. **#9 冲突恢复路径未实现**（`rebase --continue/--abort` 的编排化）。
4. **修复后未重跑全链真跑**：`run_all` 已整段重写，尚未用真实批次验证
   `stopped_at='done'` + `EXIT=0`；且旧卡 `GORCH-RUN-A/B` 会因「无新增」判 blocked，需换新任务名。
5. **`main`（`d1e51eb3`）与工作分支未合流**，以哪条为准待 Owner 拍板。
6. **3 条稳定红**（`tests/test_orchestrate_order.py`）未定性。
7. **per-card 开关**的 frontmatter 解析仍是宽松手写解析器，无 schema / 授权校验（审计 #6 后半）。

## 六、第四轮 Codex 审计

见下一章（审计完成后追加）：结论、逐条判定、是否出新引入 fail-open、最小修复清单。
