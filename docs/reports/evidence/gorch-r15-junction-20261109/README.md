# G-ORCH r15 · 真实 junction `wt remove` 验收（2026-11-09）

> 目的：闭合第十四轮审计 E1-4 的「真实 junction `wt remove`」验证债务。
> 环境：Windows，`wt.exe` = `H:\UltimaAI\_vendor\worktrunk-bin\wt.exe`，git 2.5x（Git for Windows）。
> 形式：临时仓（`%TEMP%\gorch-junc-r15`，已清理），不触碰 `H:\UltimaAI\UltimaAgent`。

## 1. 构造（为什么要这样造）

`cleanup` 判「worktree 还在不在」靠 `_path_state` 的四态；Windows junction 在 `os.lstat` 下
**不是 symlink**（`islnk=False`、`isdir=True`、`mode=0o40777`），所以会被判 `exists`。
真实的风险形态是：worktree 目录被删除后，在**同一个登记路径**上放一个 junction 指向别处 ——
git 仍认为 worktree 在该路径，`cleanup` 也认为它在，于是会调 `wt remove`。

```
git init -b main  →  空提交  →  git worktree add wt/JOB1 -b job1
Rename-Item wt/JOB1 → wt/JOB1_real            # 登记路径腾空
cmd /c mklink /J wt/JOB1 wt/JOB1_real         # 登记路径被 junction 占据
echo sentinel > wt/JOB1_real/sentinel.txt     # 制造"脏 worktree"
```

`os.lstat(wt/JOB1)` 实测：`islnk False / isdir True / 0o40777` → `_path_state` 返回 `exists`。

## 2. 结果一：不带 `--force`

```
wt -C <repo> remove job1 --foreground --format json -y --no-hooks
rc=1   elapsed=0.5s
✗ Cannot remove worktree: job1 has uncommitted changes
  ?? sentinel.txt
↳ ... or to lose uncommitted changes, run wt remove --force job1
```

- wt **跟随 junction**进入了目标目录，读到了 `JOB1_real/sentinel.txt` 这个未跟踪文件；
- 于是按「worktree 脏」拒绝删除；
- 现场不变：`JOB1`（Junction）与 `JOB1_real` 都在，`git worktree list` 仍列出 `wt/JOB1`。

## 3. 结果二：带 `--force`（`cleanup --force` 的真实路径）

```
wt -C <repo> remove job1 --foreground --format json -y --no-hooks -f
rc=0   elapsed=1s
◎ Removing job1 worktree...
▲ Discarding uncommitted changes (--force):
  ?? sentinel.txt
✓ Removed job1 worktree (--force) & branch (same commit as main, _) (1 file · 0 B)
[ { "kind": "worktree", "branch": "job1",
    "path": ".../wt/JOB1", "branch_outcome": "deleted",
    "branch_checked_out_at": null } ]
```

删除后核对：

| 对象 | 结果 |
|---|---|
| `wt/JOB1`（junction 本身） | **已删除** |
| `wt/JOB1_real`（junction 指向的真实目录） | **完好保留**（`.git`、`sentinel.txt` 都在） |
| `git worktree list` | 只剩 repo，登记已清 |
| 分支 `job1` | 已删（`branch_outcome="deleted"`） |

## 4. 结论（三条，都进规范）

1. **`wt remove -f` 对 junction 是「删链接不删目标」**：目标目录内容未被递归删除。这是本次
   实测到的安全边界，推翻「junction 会被当作真实 worktree 连带删目标内容」的担忧。
2. **回执里的「Discarding uncommitted changes」是误报**：它把 junction 目标里的 `sentinel.txt`
   算成了被丢弃的改动，实际只删了链接。任何把该字段当「已丢数据」的取证都会读错，只能
   以「删除后目录是否存在」为事实源。
3. **`_path_state` 对 junction 永远返回 `exists`，永不落 `wrong_type`**：所以「junction 被当作
   正常 worktree」这条路径真实存在，且只由 wt 自身的行为兜底。运维层需要一个只读出口把
   「登记路径是 reparse point」这件事显式报出来（对应 E2 口径 ⑥ 的建议）。

## 5. 未覆盖

- 未验证 `wt merge`（不是 remove）在 junction 场景下的行为；
- 未验证 junction 指向**不存在**目标（dangling junction）时 `_path_state` 与 wt 的组合行为；
- 未在真实 G-ORCH `cleanup()` 里跑这条链路（本次是直接调 `wt`，与 `wt_remove` 的参数完全一致）。
