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
4. ~~**真冲突证据只覆盖"两卡 + 新文件 add/add"**~~ —— **已补，见第五章**：三卡 A/B/C 证明
   B 冲突后 C 未被合并、已跟踪文件 modify/modify 冲突已实测、run record 与 merge 原始输出
   已入仓库（`docs/reports/evidence/gorch-conflict-verify-20261109/`）。
5. **第 4 跳（主脑回传授权条件）仍只有单测**；3 通道同轮并发未验；
   `wt remove` 180s 超时本轮又犯一次（目录已删但返回超时，与 L72 同源）。

## 五、按审计顺序补的三个场景（2026-11-09 晚）

三项按 Codex 第二轮审计第 4 条给的顺序执行：三卡 A/B/C → 已有跟踪文件 modify/modify → 证据入库。

### 5.1 三卡 A/B/C：证明 B 冲突后 C 未被合并

批次 `%TEMP%\gorch-tricard\`，三卡同轮并发：

| 卡 | 写什么 | 冲突角色 |
|---|---|---|
| `GORCH-TC-A`(ch1) | 新建 `docs/reports/gorch-tc-probe.md`（A 段） | 先合，成功 |
| `GORCH-TC-B`(ch2) | 新建**同一文件**（B 段） | 后合，撞 add/add |
| `GORCH-TC-C`(ch3) | 新建独立文件 `docs/reports/gorch-tc-c.md`（与 A/B 无写域重叠） | 排在 B 之后，应被停派 |

| 步 | 实测 |
|---|---|
| gate | 三张全 `可开工`，`stderr_diag` 均空 |
| provision | 三 worktree + 三分支（`gorch/GORCH-TC-A/B/C`） |
| execute | 三卡同轮并发（ch1/ch2/ch3），全部 `result=done`、`worktree_state=changed` |
| merge | A `squashed=true / removed=true` → 主线 **`de04e8d6`**（A 段 2 行）；B **rc=1** `CONFLICT (add/add)`；**C 既不在 `merged` 也不在 `failed`** |

**"B 冲突后 C 未动"的三条独立证据**（缺一条都不足以下结论）：

1. merge 输出里 `merged` 数组只有 A、`failed` 数组只有 B，C 没有任何条目
   （`break` 在 `batch_orchestrator.py:529` 生效，循环在 B 处终止）
2. 事后 `git branch --list 'gorch/GORCH-TC*'` 仍见 `gorch/GORCH-TC-C`，tip = `7fec8fb4`
   （= 执行前基线，说明它的改动从未被 squash 进任何提交）
3. 主线 `git cat-file -e HEAD:docs/reports/gorch-tc-c.md` → **128**（不存在）；
   而 C 的 worktree 里仍是 `?? docs/reports/gorch-tc-c.md`

B 的冲突现场（add/add）：`AA docs/reports/gorch-tc-probe.md`、`.git/worktrees/GORCH-TC-B/rebase-merge`
存在、文件内 `<<<<<<< HEAD`（A 段）/ `=======` / `>>>>>>> 913ebe89`（B 段）逐字可见。

### 5.2 已有跟踪文件 modify/modify

前两轮只覆盖"两个新文件 add/add"，本轮补最常见的"同一文件的第 N 行被两卡各改一次"：

- 基线：`docs/reports/gorch-mm-probe.md`（4 行）先提交进主线 `7fec8fb4`，两卡都只改**同一行** `line2`
- `GORCH-MM-A` → `line2: A`，`GORCH-MM-B` → `line2: B`

| 项 | 实测 |
|---|---|
| merge A | 成功 → 主线 `9f9d6b58`，文件内容 `line2: A` |
| merge B | **rc=1 `CONFLICT (content)`**——不是 add/add，是内容冲突 |
| B 现场 | `UU docs/reports/gorch-mm-probe.md`；`<<<<<<< HEAD / line2: A / ======= / line2: B / >>>>>>> d0386cec` |
| rebase 未完成态 | `.git/worktrees/GORCH-MM-B/rebase-merge` + `REBASE_HEAD` + `MERGE_MSG` 均存在 |
| 不依赖 wt 的复核 | `git merge-tree HEAD HEAD gorch/GORCH-MM-B` 报同一 hunk 冲突（`-line2: A / +line2: B`） |

两类冲突（新文件 add/add、已跟踪文件 modify/modify）现在各有一份实测现场。

### 5.3 证据载体入库

`docs/reports/evidence/gorch-conflict-verify-20261109/`，共 9 个文件：

| 文件 | 内容 |
|---|---|
| `tricard-call-sequence.log` | gate / provision / execute / merge 四步原始 JSON + 每步 rc，含 `target=codex/voice-fsmn-new-path` |
| `tricard-scene.txt` | git log、分支、C 未合并的三证、A 提交 stat、B 的 AA / rebase-merge / 冲突正文 |
| `GORCH-TC-{A,B,C}-codex-channel.json` | 三卡 run record（`worktree_state` / `worktree_changes` / `elapsed_sec` / `reason`） |
| `mm-call-sequence.log` / `mm-scene.txt` | modify/modify 两卡的同样四步与现场 |
| `GORCH-MM-{A,B}-codex-channel.json` | 两卡 run record |

这样审计可以从仓库内独立复核，不再依赖 `data\gorch\runs\`（工作区目录，随时可被清理）——
上一轮审计 `Get-ChildItem data\gorch\runs -Filter GORCH-CONFLICT*` 查不到东西，正是因为证据没入库。

### 5.4 本轮顺带复现的缺陷（登记，未修）

`wt remove` 180s 超时本轮**三次全中**（TC-B、TC-C、MM-B），但三次目录都已删除、
分支都按 `--delete-branch` 处理掉了。说明这不是偶发：在 Windows 上 `wt remove` 稳定超时，
编排层把超时当失败回传（fail-closed 正确），只是清理结果需要人工二次确认。已记入 L72/L77 同源缺陷，
**是否要改成"超时后复查目录与分支是否已消失再判成败"留待 Owner 裁**。

