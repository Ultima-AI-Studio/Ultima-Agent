# G-ORCH 任务派发链第五轮收口报告（fail-open 第二轮）

- 日期：2026-11-09
- 提交：`0190b88c`（主体，4 文件 / 296+ / 86-）
- 基线：`ae7bde55`（第四轮修复 + 文档）
- 上游依据：第四轮 Codex 独立审计（`Temp\codex-r4-audit-last.md`，12,559 B / 121 行），判定「部分一致」
- 验收：两个 gorch 测试文件 **93 passed / 38.94 s**（基线 91，新增 3 条，1 条按真实回执形状改写）

## 一、为什么有这一轮

第四轮 Codex 审计给出两层结论：

- **已闭合**：1(a) 前置失败落记录、1(e) `run_all --dry-run` 不合并也不清理。
- **仍未闭合**：其余 8 条，并附 **Q1 八条新引入的 fail-open** 与 **Q3 九条最小修复清单**。

按既定四段式流程，第②环判「部分一致」即第③环前提未满足，因此回到第①环做第五轮自修。
本轮只做 Q3 清单里能在不动工单契约的前提下闭环的部分，涉及契约变更的留白并列明。

## 二、Q3 九条 → 本轮落地映射

| # | Q3 要求 | 落地位置 | 做法 | 状态 |
|---|---|---|---|---|
| 1 | 严格区分「未提供 `run_dirs`」与「显式空映射」 | `find_done_tasks` `:600` | `if run_dirs:` → `if run_dirs is not None:`；空映射走 invocation 模式，缺失/损坏/空一律阻断，不落回 glob | ✅ |
| 2 | 所有合并入口接收并校验 invocation / 精确 run-record | `merge(..., only_tasks=None)`、`run_all` | `run_all` 传 `only_tasks=ready` + `run_dirs`；`merge` 把 `only_tasks` 透给 `find_done_tasks` | ⚠️ 部分：独立 merge CLI 仍未强制 invocation |
| 3 | 删除 mtime 选「最新」的授权语义 | `find_done_tasks` 兜底分支 `:629-680` | 改按记录内 `started_at` 选；并列 `started_at` 的不同 invocation 直接阻断；无 `started_at` 才退化 mtime 并在 `selection` 标注弱判据；损坏记录不再 `continue` | ✅ |
| 4 | stale 只算本轮 ready、`done_no_merge` 移出 stale、独立 CLI stale 非零 | `run_all` `:1000` 附近、CLI `:1180` | `find_done_tasks(only_tasks=ready)`；`verified` 单列；`real_stale` 剔除 verified；CLI 返回 `0 if (merged and not failed and not stale) else 1` | ✅ |
| 5 | Cygwin 白名单整行 + 行尾约束 | `_CYGWIN_NOISE` `:70-74` | 三条正则各自 `^...\s*$`；合法前缀后挂任何多余文本都按真错误上报 | ✅ |
| 6 | 逐路径内容快照 + ignored + 指纹失败阻断 + 写域校验 | `worktree_state` `:70`、`fresh_changes`、`main` 产出段 | `-uall`；内容指纹优先、指纹相同不采信状态行差集；`ERR:*` 立即 blocked | ⚠️ 部分：ignored 产物、写域白名单未做 |
| 7 | cleanup 无论 rc 都先验 schema 再回读三处 | `cleanup` `:790-830` | rc=0 路径重写：`items` 归一 → `retained` → 回读「目录不存在 / 分支 absent / worktree 未登记」三处 → 三处全消失才 removed，否则 partial；`schema_ok` 一并落记录 | ✅ |
| 8 | `None`=全部 / `[]`=一个也不做；stale 判定前禁止 cleanup；回执 branch/target 必须存在且精确 | `find_done_tasks`、`merge`、`cleanup`、`run_all` | `tasks is not None` 全线替换 `if tasks`；`leftover`/`real_stale` 前置到 cleanup 之前；回执缺身份字段直接 failed | ✅ |
| 9 | per-card 例外受控 schema + `done_no_merge` 建为整链认可终态 | `run_all`、卡片解析器 | `done_no_merge` 已从 stale 摘出并单列 `verified_only`、不触发全批 cleanup；per-card 例外 schema 未动 | ⚠️ 部分 |

## 三、本轮最重要的一个实测（不是 Q3 条目）

第四轮把「`wt merge --format json` 回执里 `merged is True`」当成合并成功判据。实测（临时仓库
`Temp\wtprobe-r4`，2026-11-09）：

```
$ wt merge --format json -y --no-hooks
{
  "branch": "feat/probe",
  "target": "main",
  "committed": false,
  "squashed": false,
  "rebased": false,
  "removed": false
}
```

**回执里没有 `merged` 字段。** 这意味着第四轮那条判据会让**每一次合并都被判失败**——
一个"加了更严的判据、实际把整条链打死"的反向错误，第四轮静态审计不可能看出来。

本轮替换为两层判据：

1. **回执身份**：`branch`、`target` 必须存在（缺失即 failed 并停止），且归一化后与请求精确匹配；
2. **git 侧复核**：`git merge-base --is-ancestor <branch> <target>` 返回 0，**或**
   `target` tip 相对「上一次成功合并后的基线」前进，二者成立其一才算合入。
   为此新增两个只读辅助 `_git_out(args, timeout=60)` 与 `_ref_sha(ref)`（在 `ROOT` 下跑）。

这条也解释了为什么必须"实测工具契约"而不是"照着工具名字猜字段"。

## 四、验收

- 命令：`tools\venv-openjarvis\Scripts\python.exe -m pytest -o addopts= -p no:cacheprovider tests\test_gorch_batch_orchestrator.py tests\test_gorch_codex_channel.py -q`
- 结果：**93 passed / 38.94 s**
- 新增/改写的用例：
  - `test_merge_rejects_receipt_without_identity`（回执缺 `branch`/`target` → failed，原 `merged=false` 用例按真实回执形状改写）
  - `test_merge_rejects_when_git_shows_no_merge`（wt 说成功、git 侧既非祖先又没推进 → failed）
  - `test_fingerprint_read_failure_blocks`（`diff_sha=ERR:128` → blocked）
  - `test_cygwin_noise_lines_still_pass` 样本按整行正则校正（原样本行本就是"前缀+多余文本"，现在应判真错误）

## 五、仍未闭合（4 项，全部涉及工单契约，需 Owner 定口径）

1. **写域白名单**（Q3 #6）：要给"任务允许改哪些路径"建授权写域并校验越域。这会改变工单灰度与派发规则，不是纯代码修正。
2. **ignored 产物**：`git status --porcelain` 看不到 `.gitignore` 内的产物。当前口径是"ignored 不算产出"，
   若要算，需要工单侧显式声明期望产物路径。
3. **per-card 例外受控 schema**（Q3 #9）：现在卡片里写 `no_change_allowed: true` / `allow_non_repo: true`
   仍能开例外。要收紧到"受控 schema + 授权来源"，属契约变更。
4. **独立 merge CLI 强制 invocation**（Q3 #2 剩余）：CLI 仍可用 `--batch-dir` 走兜底 glob 路径
   （已改为 `started_at` 选最新 + 并列阻断），但没强制要求 `--run-dir`。

## 六、给下一轮审计的提示

- 判「合并是否生效」现在依赖两条 git 事实，不再依赖 wt 的自述字段；如果 `_ref_sha` 取不到（git 报错），
  会落到 `rc_anc != 0 and not progressed` → failed（fail-closed），不是静默通过。
- `cleanup` 的三处回读里，`_worktree_registered` 返回 `None`（查询失败）**不会**被当成 False，
  只会计 partial —— 这一点是本轮特意保留的：不确定 ≠ 干净。
- 测试桩已统一到真实回执形状（`{'branch','target','committed','removed'}`），不再用 `{'merged': True}`。
