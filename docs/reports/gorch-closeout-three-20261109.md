# G-ORCH 收口三项验证报告（2026-11-09）

> 目的：把上一轮判定为"不能按八连全绿验收"的三个缺陷收掉，并留下可复核的实测证据。
> 三项分别是：判定闸不把 stderr 噪声当失败、执行段 done 不只看退出码、真冲突批次跑通。

## 一、三项改动

### 1）判定闸：stderr 只作诊断，不进判定（L77）

`scripts/gorch/batch_orchestrator.py` 的 `gate_check()` 删掉了原来的：

```python
if r.stderr.strip():
    raise SystemExit(f'ccpm 判定出现错误输出 ...')
```

替换为 `stderr_diag = r.stderr.strip()[:200]`，写进每行 `rows` 的 `stderr_diag` 字段。
判定契约收缩为三条：**退出码 + stdout 三标记（STATUS/UNMET/CONFLICTS）+ 状态可归**。

- 退出码非 0 仍 fail-closed（原逻辑保留，这是正确强信号）
- 标记缺失仍 fail-closed
- 未知状态（`status_map.normalize_status` 返回 None）仍 fail-closed

理由：git-bash/cygwin 在 fork 受限时会往 stderr 写 `fork: retry` / `cygheap read copy failed`
之类的噪声，此时退出码与三条标记都完好。原来"stderr 非空即拒"会把一次偶发噪声放大成
**整批拒派**，无人值守跑批时会误伤。

### 2）执行段：done 必须有 worktree 实变更

`scripts/gorch/codex_channel.py` 新增 `worktree_state(workdir)`，返回四态：

| 返回值 | 含义 | 对 done 的影响 |
|---|---|---|
| `changed` | 有改动，detail 是 `git status --porcelain` 首段 | 不影响，正常 done |
| `clean` | 一个字节都没动 | **改判 blocked**：判空产出，不写 done |
| `not_repo` | 不是 git 工作树，无从校验 | 不改判（保持只看退出码，记入 record 供审计） |
| `error` | git 查不动（不存在/超时/status 失败） | **改判 blocked**，fail-closed |

实现：先 `git rev-parse --is-inside-work-tree`（timeout 30s），再 `git status --porcelain`
（timeout 180s），两者都带 `creationflags=_NO_WINDOW`。
产出校验**只在退出码已为 0 时追加**，不覆盖退出码非 0 的原生错误原因。
`record` 新增 `worktree_state` / `worktree_changes` 两字段；失败 reason 优先用产出校验结论。

### 3）真冲突批次

这一项不是改代码，是补一个从没验过的场景：**两张卡改同一个文件**。

## 二、验证证据

### 测试

| 文件 | 结果 | 新增用例 |
|---|---|---|
| `tests/test_gorch_batch_orchestrator.py` | **45 passed / 27.59s** | 3 条：stderr 噪声不拒、退出码非 0 仍拒、噪声+标记缺失仍拒 |
| `tests/test_gorch_codex_channel.py` | **10 passed / 10.49s** | 2 条：`worktree_state` clean→changed、非 git 目录判 not_repo |
| 三文件回归（改动前基线） | 53 passed / 10.63s | — |
| `py_compile` 两文件 | rc=0 | — |

### 真冲突批次（`%TEMP%\gorch-conflict\`）

两卡：`GORCH-CONFLICT-A`（ch1）、`GORCH-CONFLICT-B`（ch2），
**都新建 `docs/reports/gorch-conflict-probe.md`**，内容不同（A 段 / B 段），
`conflicts_with` 均为空（否则第二张永远派不出去，撞不到 merge 冲突）。

| 段 | 实测 |
|---|---|
| gate | 两张都 `可开工`，`stderr_diag` 均为空 |
| provision | 两个 worktree + 两个分支建成 |
| execute | A `done` **210.5s** / B `done` **191.3s**，并发（started 同一秒 12:03:35 UTC） |
| 产出校验 | 两卡 `worktree_state=changed`，`worktree_changes` 都是 `?? docs/reports/gorch-conflict-probe.md` |
| merge A | `squashed=true` / `rebased=false` / `removed=true`，主线新增 `d07644ad`（2 insertions = A 段） |
| merge B | **rc=1**，`CONFLICT (add/add): Merge conflict in docs/reports/gorch-conflict-probe.md`，后续分支停止不自动继续 |

### 冲突现场（关键：是不是真停下了、现场在不在）

| 检查 | 实测 |
|---|---|
| B 的源 worktree 状态 | `AA docs/reports/gorch-conflict-probe.md`（add/add 冲突未解决） |
| rebase 未完成态 | `.git/worktrees/GORCH-CONFLICT-B/rebase-merge` **存在** |
| 冲突标记 | `<<<<<<< HEAD`（A 段） / `=======` / `>>>>>>> 8afe32a8`（B 段），逐字可见 |
| A 的 worktree/分支 | 已回收、分支已删 |
| 清理 | `rebase --abort` 后 `cleanup --delete-branch`；`wt remove` 报 180s 超时但目录已删，`git worktree list`/`branch` 均无残留 |

**结论**：merge 撞真冲突时确实停下、不自动继续，rebase 现场留在源 worktree，符合代码注释与
提示文案的预期。这条路径此前只有文案、没有实测，现在有实测。

## 三、对八连的补强

| 跳 | 收口前 | 收口后 |
|---|---|---|
| 判定闸（第 5/6 跳的前置） | stderr 噪声 → 整批拒派 | 噪声只留诊断，判定看退出码+三标记 |
| 7 执行·写码/自检/提交 | 退出码 0 即可 done | 还要有 worktree 实变更，空产出改判 blocked |
| 8 审议·复检 / merge | 只验过写入域不重叠 | 真冲突路径已验：停下 + 留现场 |

## 四、仍然存在的缺口（本轮未动）

1. **`not_repo` 是弱化项**：workdir 不是 git 工作树时不改判，仍只看退出码。属有意保留
   （`--dry-run` 与手工用法不能被一刀切），但这条路径在无人值守场景下仍是盲区。
2. **第 4 跳（主脑回传授权条件）仍只有单测**，未与真实需求串跑。
3. **3 通道同轮并发未验**（只验过 2 通道）。
4. **`wt remove` 180s 超时**：本次清理又撞到一次（目录已删、返回超时）。与 L72 同源，
   建议后续把 remove 也纳入独立超时预算 + 事后探现场。
5. 3 条稳定红仍在 `tests/test_orchestrate_order.py`（本轮未触碰该文件，也未做回退验证）。
