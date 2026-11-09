# G-ORCH 收口三项验证报告（2026-11-09）

> 目的：把上一轮判定为"不能按八连全绿验收"的三个缺陷收掉，交给 Codex 独立审计，
> 并按审计结论做了一轮加固。三项分别是：判定闸不把 stderr 噪声当失败、
> 执行段 done 不只看退出码、真冲突批次跑通。

## 一、三项改动（含审计后加固）

### 1）判定闸：只放行 cygwin 噪声，其余 stderr 仍 fail-closed（L77）

初版只把"stderr 非空即拒"整段删掉，改成 `stderr_diag` 纯诊断。**第二轮审计判定这是漏判**：
实际执行串是 `printf 'STATUS:%s' "$(frontmatter_field …)"`，命令替换内部的失败不会传成外层
退出码。审计实测复现：

```text
STATUS:open
UNMET:
grep: other.md: Permission denied
CONFLICTS:
outer_rc=0
```

`active_conflicts` 里 grep 报错 → `other_status` 空 → 活跃冲突不入输出 → 三标记齐全 + rc=0
→ 有冲突的卡被判"可开工"。即"删掉 stderr 硬拒"这一步把通用 fail-closed 一起丢了。

加固后的契约是双向的：

- **bash 串**（`batch_orchestrator.py` `gate_check`）：`set -o pipefail` + 三个函数先各自赋值、
  失败即 `exit 71/72/73`，再打印标记。函数内部非零能传到外层退出码。
- **stderr 判定**：`_CYGWIN_NOISE` 白名单只覆盖 fork 噪声（`fork: retry` / `cygheap` /
  `dofork` / `child_copy` / `Resource temporarily unavailable` / `^\s*\d+\s*[main]`），
  命中则降级为诊断；**其余任何 stderr 行一律 `SystemExit`**。

判定契约最终为：退出码 + stdout 三标记 + 状态可归 + **stderr 无非白名单内容**。

### 2）执行段：done 必须有 worktree 实变更

`codex_channel.py` 新增 `worktree_state(workdir)` 四态：

| 返回值 | 含义 | 初版对 done | 审计后 |
|---|---|---|---|
| `changed` | 有改动 | 不影响 | 不影响 |
| `clean` | 一字节未动 | 改判 blocked | 不变（**纯验证卡会被误伤，见遗留 1**） |
| `not_repo` | 非 git 工作树 | 不改判 | **改判 blocked**，除显式 `--allow-non-repo` |
| `error` | git 查不动 | 改判 blocked | 不变 |

审计指出的绕过路径（`execute()` 只验 workdir 是目录 → 普通目录跑 codex 退出 0 →
`not_repo` 放行 → `result=done` → `find_done_tasks` → `merge` 接受）已堵：
批量路径默认 fail-closed，手工无仓库场景必须显式 `--allow-non-repo` 并在 record 留痕。

另补：失败原因现在落进 `record['reason']`（此前只在看板与 stdout 有，run 记录里查不到，
不符"证据载体"要求）。

### 3）merge 授权：dry-run 不算数

审计第 3 条：`execute --dry-run` 直接 `ok=True` → `kanban done` → `result=done`，
而 `find_done_tasks()` 只认 `result=='done'`，所以 dry-run 能生成合并授权。
已在 `find_done_tasks()` 排除 `dry_run` 记录。

## 二、验证证据

### 测试

| 文件 | 初版 | 加固后 | 说明 |
|---|---|---|---|
| `tests/test_gorch_batch_orchestrator.py` | 45 passed | **46 passed** | 新增"真错误 + 三标记齐全必拒"反例 |
| `tests/test_gorch_codex_channel.py` | 10 passed | **14 passed** | 新增主流程级 4 条（clean→blocked、changed→done、not_repo 默认拒、显式放行） |
| 两文件合计 | 55 | **60 passed / 37.91s** | — |

审计第 5 条原话是"5 条里只有 1 条真钉新契约，2 条只验 helper，删掉挂载仍会过"。
本轮补的 4 条是**主流程级**：mock 外部 Codex 与看板，直接断言 `result` / `worktree_state`
/ `reason`，删掉 `codex_channel.py` 的产出校验挂载后这些用例会红。

### 真冲突批次（`%TEMP%\gorch-conflict\`）

两卡 `GORCH-CONFLICT-A`(ch1) / `GORCH-CONFLICT-B`(ch2)，**都新建
`docs/reports/gorch-conflict-probe.md`**（A 段 / B 段），`conflicts_with` 均空。

| 段 | 实测 |
|---|---|
| gate | 两张都 `可开工`，`stderr_diag` 均空 |
| provision | 两 worktree + 两分支建成 |
| execute | A `done` **210.5s** / B `done` **191.3s**，started 同一秒（12:03:35 UTC） |
| 产出校验 | 两卡 `worktree_state=changed`，`worktree_changes` = `?? docs/reports/gorch-conflict-probe.md` |
| merge A | `squashed=true` / `rebased=false` / `removed=true`，主线 `d07644ad`（2 insertions = A 段） |
| merge B | **rc=1**，`CONFLICT (add/add): Merge conflict in docs/reports/gorch-conflict-probe.md` |

### 冲突现场

| 检查 | 实测 |
|---|---|
| B 的源 worktree | `AA docs/reports/gorch-conflict-probe.md` |
| rebase 未完成态 | `.git/worktrees/GORCH-CONFLICT-B/rebase-merge` 存在 |
| 冲突标记 | `<<<<<<< HEAD`（A 段） / `=======` / `>>>>>>> 8afe32a8`（B 段） |
| A 的 worktree/分支 | 已回收、分支已删 |
| 独立复核 | `git merge-tree ddfb842b d07644ad 8afe32a8` 直接输出 `added in both` + 两段内容（审计自己也跑过） |

## 三、对八连的补强

| 跳 | 收口前 | 现在 |
|---|---|---|
| 判定闸（5/6 跳前置） | stderr 噪声 → 整批拒派；真错误也能被吞 | 噪声放行、真错误必拒、三标记齐全仍 fail-closed |
| 7 执行·写码/自检/提交 | 退出码 0 即 done | 还要 worktree 有实变更；查不动就拒；非仓库路径默认拒 |
| merge 授权 | dry-run 也算 done | dry-run 不进合并池 |
| 8 审议·复检 / merge | 只验过写入域不重叠 | 真冲突实测过一次：停下、留现场 |

## 四、仍存在的缺口（按审计结论登记，未在本轮动）

1. **`clean` 会误伤合法零改动任务**（纯验证卡、只靠 `last-message.md` 回结论的报告卡）。
   审计建议引入显式产出策略（`changes_required` / `no_change_allowed` 写进 record）。
   这是契约变更，需 Owner 定口径后再动。
2. **`changed` 只认"有没有改"，不认"改的是不是该改的"**：无执行前基线快照、无写入域，
   幂等复用脏 worktree 时会把旧改动当本次成果。
3. **`find_done_tasks()` 仍会跳过较新的 blocked 去找更旧的 done**（现有测试把它钉成预期）。
   意味着任务重跑失败后，仍可能按上一次成功合并。是否改为"只认最新记录"需 Owner 裁。
4. **真冲突证据只覆盖"两卡 + 新文件 add/add"**：不能证明"冲突后后续分支停派"
   （B 已是末项）、没覆盖 modify/modify、run record 与 `wt merge` 原始输出仍未入库。
   审计给的补齐顺序：三卡 A/B/C 真跑 → 已有跟踪文件 modify/modify → 证据载体入库。
   报告的结论因此限定为"实测一次两分支 add/add 冲突并观察到 rc=1 与未完成 rebase 现场"。
5. **第 4 跳（主脑回传授权条件）仍只有单测**；3 通道同轮并发未验；
   `wt remove` 180s 超时本轮又犯一次（目录已删但返回超时，与 L72 同源）。
