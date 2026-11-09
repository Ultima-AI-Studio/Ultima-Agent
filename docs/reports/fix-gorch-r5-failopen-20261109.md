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


## 七、第五轮 Codex 独立审计的结论（2026-11-09）

- 命令与参数：`codex exec -m gpt-5.6-sol --sandbox read-only -a never`，输入为
  `Temp\gorch-r5-audit-prompt.md`，输出 `Temp\codex-r5-audit-last.md`
- 结果：`rc=0` / **792.3 s** / **12,026 B** / **186,585 tokens**
- 判定：**部分一致，不能当作完整闭环**（原文：「主路径的显式 run_dirs、ready 过滤、
  Cygwin 行级白名单、cleanup 三处回读及 tasks=None/[] 语义已收紧，但独立 merge 仍靠
  历史 glob/mtime 授权，内容/写域与 cleanup schema 未闭合，并新引入两类可把未完成
  任务记成功的 fail-open」）

### 7.1 逐条结果

已闭合（✅）：1(a) 前置失败落记录、1(e) dry-run、Q3-5 Cygwin 整行白名单、Q3-8
`tasks` 语义 / cleanup 时序 / 回执身份。

未闭合（⚠️）：Q3-1（fallback 里「损坏记录 + 旧 done」仍能授权）、Q3-2（merge 子命令
没有 `--run-dir`）、Q3-3（`started_at` 是未解析字符串、channel record 根本不写
`invocation`、无 `started_at` 时仍退 mtime）、Q3-4（`done_no_merge` 仍由 reason 子串
摘出，独立 merge 没有 verified-only 终态）、Q3-6（仍是整体 `git diff HEAD` 单哈希、
无 ignored/写域、**脏基线 `ERR:*` 未阻断**）、Q3-7（`schema_ok` 只记录不参与 removed
判定）。

反向恶化（❌）：Q3-9（`no_change_allowed`/`allow_non_repo` 仍由卡片自由字段直接授权；
`done_no_merge` 改用 reason 子串识别 → 新增成功误判路径）。

### 7.2 本轮新引入的三条 fail-open（必须先修）

1. **`done_no_merge` 的 reason 子串可伪装成功终态。** `find_done_tasks` 透传记录自身
   `reason`，`run_all` 用 `'done_no_merge' in str(reason)` 判 verified → 任何
   `result=blocked` 且 reason 里出现该文本的记录都会被当非合并成功终态，从 stale 与
   leftover 里剔除，最终可能 `stopped_at='done'`、`run` 返回 0。
2. **merge 未记录「调用前是否已是祖先」的前态。** 源分支在调用 `wt merge` **之前**
   就已经是 target 祖先时，`merge-base --is-ancestor` 返回 0 会直接判合入成功，
   即使 worktree 里的未提交内容根本没合进去；回执里的 `committed/squashed/rebased`
   完全未参与判定。
3. **任意无关进程推进 target 即可冒充本任务合入。** 只比较 target SHA 是否变化，
   不校验新 commit/tree 与本任务 source 是否存在关系。

### 7.3 审计给的 7 条最小修复清单

1. `done_no_merge` 改结构化终态：`find_done_tasks` 返回 `mergeable_done / verified_only /
   stale` 三组，只按 `data["result"] == "done_no_merge"` 精确判断，禁止 reason 文本推断；
   独立 merge CLI 在「仅 verified_only、无真实 stale」时返回成功但不调用 merge/cleanup。
2. merge 生效证明：调用前记录 target SHA 与 source ancestor 状态，禁止用「调用前已成立
   的 ancestor」或「任意 target tip 前进」单独证明本任务；最小安全做法是延后 source 删除，
   先验证本任务 source commit/tree 与 `target_after` 的确定关联再 cleanup，关联不上按
   failed 保留现场。
3. 删掉独立 merge 的 glob/mtime 授权：CLI 增加精确 `task=run_dir` 或 invocation manifest，
   校验 `task/invocation/run_dir/dry_run/result/mergeable`；若保留 fallback，任何损坏记录
   都阻断、严格解析 UTC `started_at`、要求 invocation 非空且唯一、同时间同 invocation
   多记录给确定性拒绝规则。
4. 内容闸改规范化逐路径快照（跟踪 + 未跟踪都记路径与内容哈希）；**脏基线指纹 `ERR:*`
   在调用 Codex 之前就 blocked**；明确枚举/拒绝 ignored 新产物；按可信任务 schema 校验
   所有变化路径都在授权写域内。
5. cleanup 把 schema 纳入成功条件：解析失败、空数组、非预期字段、`removed=false`、
   缺失或未知 `branch_outcome` 一律 partial；只有 schema 合法且目录 / 精确分支 /
   worktree 登记三处都明确消失才记 removed。
6. `no_change_allowed` / `allow_non_repo` 不再信任任务 Markdown 自由字段，改从编排方
   签发的 invocation manifest / 受控白名单读取并做严格布尔 schema 校验；卡片自身声明
   只能算「请求」，不能算「授权」。
7. 补最小回归用例：fallback「损坏记录 + 旧 done」、显式 `run_dirs={}`、`started_at`
   并列/非法/空 invocation、blocked reason 含 `done_no_merge`、调用前已是 ancestor、
   无关 target 前进、脏基线指纹 ERR、ignored/越权路径、cleanup schema 非法但三处已消失。
   现有的 3 条新用例只覆盖了「缺身份回执 / 双重否定 / 执行后指纹 ERR」。

### 7.4 该审计对「93 passed」的口径声明

原文：「按约束本轮未运行 pytest；"93 passed"仅是提交方主张，不作为本次静态审计的
独立通过证据。」——只读沙箱跑不了 pytest 是既定限制，测试通过与否仍以本地实跑为准。

### 7.5 下一步（r6）划分

- **可立即修（5 项）**：7.2 的三条新 fail-open、cleanup schema 纳入成功条件、
  独立 merge 强制 `--run-dir`（含 fallback 损坏记录阻断 + 严格 UTC `started_at` 解析）。
  另加「脏基线 `ERR:*` 调 Codex 前就阻断」这一小改。
- **需要 Owner 定口径（2 项）**：授权写域白名单（Q3-6 剩余）、per-card 例外改由
  manifest 授权（Q3-9）。两项都会改变工单灰度与派发规则。


## 八、r6 实现闭环（第五轮审计 7 条清单逐条落地）

> 本轮授权依据（Owner 原话）：「你说的可以直接修的 5 项就可以修了。然后需要我定的
> 口径就是明确的要表达的是，我不希望在任务执行过程当中参与到任务的授权或者审批。
> 至于授权写域白名单，如果是我任务审核的 agent 来执行的话我就批准通过。你说的另一个
> 从卡片自由字段改为编排方授权也是同样的原则」——授权的判断源在 agent 层（编排方签发、
> 审计方复核），人只在阶段门介入，不在执行期逐次点头。

### 8.1 两条需要 Owner 定口径的事项：落定形态

| 事项 | r6 之前 | r6 落定 |
|---|---|---|
| 写域白名单（Q3-6 剩余） | 不存在 | 卡片 frontmatter 的 `writes` 只算**请求**；编排方 `grant_invocation()` 在派发时签发 `RUNS/_invocations/<invocation>.json`；执行端用 `--manifest` 读取，越域即 blocked、不写 done |
| per-card 例外（Q3-9） | 直接读卡片自由字段 `no_change_allowed` / `allow_non_repo` | 同一条路径：卡片字段按请求处理（`REQUEST_KEYS`，旧名 `LEGACY_REQUEST_KEYS` 同样按请求对待）；授权值只从 manifest 读，缺条目 / 类型不符 / 两布尔非严格 bool 一律 fail-closed |
| 自相矛盾 | 无判定 | 卡片同时声明 `writes` 与 `no_change_allowed` → 编排方**拒绝签发**，落进 manifest 的 `blocked`；`run_all` 把该卡从 ready 剔除，无剩余任务即停在 gate |
| 「人在执行期审批」 | 无 | 不设。manifest 的 `policy` 字段逐字记录：卡片只能提请求；授权只由编排方在派发时签发；执行端只读本清单，不读卡片自由字段；人不在执行过程中审批 |

### 8.2 七条清单的落地位置（逐条对齐 §7.3）

1. **结构化终态**：`find_done_tasks` 的 `stale[task]` 带上 `result`；`run_all` 的 `verified`
   只认 `probe_stale[t]['result'] == 'done_no_merge'`，不再由 reason 子串摘出。
2. **merge 生效证明**：`merge()` 调 `wt_merge` **前**记 `src_before` 与
   `merge-base --is-ancestor branch target` 结果（`pre_anc`）；调后三条同时成立才算合入：
   target tip 前进 + `is-ancestor rc==0` + `(not pre_anc or src_moved)`。`merged` 条目带
   `source_sha_before/after`、`pre_ancestor`；失败文案改为「wt 报成功但 git 侧未证明本次合入…」。
3. **删 glob/mtime 授权**：`merge` CLI 新增 `--run-dir TASK=PATH`（`nargs='*'`），不带即
   `rc=2` 并提示改用 `run`；fallback 整段重写——损坏记录即阻断、`started_at` 必须可解析为
   UTC、`invocation` 非空、`started_at` 并列（含同一 invocation 多条）即阻断，全无记录返回
   「无真实执行记录」。
4. **内容闸 + 脏基线**：`codex_channel` 在执行前基线判定之后、`not_repo` 判定之前新增：
   `diff_sha` 以 `ERR:` 开头 → `_BaselineUnusable`（调 Codex **之前**就 blocked）；
   `changed` 分支按 manifest 的 `write_scope` 校验本次新增路径，越域即 `ok=False`，
   `guard_reason` 写明条数与授权值，并把 `write_scope_check` 落进 record。
5. **cleanup schema**：`schema_ok` 收紧为「非空 + 元素全 dict + 每条 `branch_outcome` 为非空
   str」；新增 `unexpected`（outcome 不在 `REMOVED_OUTCOMES={'deleted'}`）；判定顺序改为
   retained → 非 schema_ok → unexpected → 三处消失才记 removed。
6. **per-card 例外迁 manifest**：实现为 `grant_invocation()` / `_load_grants()` /
   `load_authorizations()` / `execute(manifest=)`；`run_all` 在 gate 之后、provision 之前签发
   并写 `steps['authorizations'] = {manifest, refused, tasks}`。
7. **回归用例**：新增 15 条，覆盖清单点名的 9 类，见 §8.4。

### 8.3 `wt remove` 回执实测（补 §三 的 merge 实测）

临时仓库 `wtprobe-r5`：`wt remove <branch> --format json -y --no-hooks` 输出是**数组**：

```
[{"kind":"worktree","branch":"feat/rm2","path":"C:/…/wtprobe-r5.feat-rm2",
  "branch_outcome":"deleted","branch_checked_out_at":null}]
```

**没有 `removed` 字段**（与 `wt merge` 无 `merged` 字段同一类坑）。可信成功值只有
`branch_outcome == "deleted"`；其余值（如 `retained_unmerged`）一律按 partial 处理。

### 8.4 验收（本轮实跑，不是主张）

- 命令：`tools\venv-openjarvis\Scripts\python.exe -m pytest
  tests/test_gorch_batch_orchestrator.py tests/test_gorch_codex_channel.py -o addopts= -p no:cacheprovider -q`
- 结果：**108 passed / 39.12s**（batch 81 + channel 27）。
- 新增 15 条用例，逐条对应审计点名项：
  `损坏记录 + 旧 done`、`显式 run_dirs={}`、`started_at 非法`、`空 invocation`、
  `started_at 并列（同 invocation 多条）`、`调用前已是 ancestor 且源未动`、`无关 target 前进`、
  `cleanup schema 非法但三处已消失`、`reason 含 done_no_merge 被当终态`、
  `脏基线 ERR（Codex 调用次数=0）`、`越域路径 blocked`、`域内路径 done（正例）`、
  `manifest 缺本任务`、`manifest 拒签（writes + no_change_allowed 矛盾）`、
  `manifest 写入 write_scope/enforced`。
- 测试自净：fixture 默认把 `RUNS` 指到 `tmp_path`，跑测不再向仓库
  `data/gorch/runs/_invocations` 堆文件（跑测前后该目录文件数均为 0，实测）。

### 8.5 仍未闭合（交给 Owner / 下一轮）

- `done_no_merge` 的**终态名与状态机口径**未书面落定（会牵动契约 v1.3）。
- 执行前 worktree 是否必须 clean：本轮取「允许脏基线 + 内容级指纹 + 基线 ERR 阻断」，
  审计主张「拒绝复用脏基线、进显式恢复流程」，两者口径仍不同。
- 独立 merge CLI 是否保留（现已强制 `--run-dir`）。
- `run_all` 改动后**未用真实批次重跑**全链（旧卡 `GORCH-RUN-A/B` 会因「无新增」判 blocked，
  重跑需换新任务名）。
- `wt merge` 无 `merged` / `wt remove` 无 `removed` 尚未写进规范文档固定为契约基线。

### 8.6 给第六轮审计的提示

1. 本轮 pytest 为本地实跑，**108 passed / 39.12s**，可直接作为通过证据复核。
2. 重点复核三处新语义：(a) merge 三段式证明里「预已祖先 + 源未动」的判定；
   (b) `_outside_scope` 的目录前缀与 `*` 匹配边界（`docs/` 与 `docs/reports/` 的包含关系、
   Windows 反斜杠归一）；(c) manifest 拒签后 `run_all` 的 gate 停止路径。
3. 已知未做：`git status --porcelain` 不列 ignored 文件，故 ignored 新产物既不会进 fresh、
   也永远不会被写域校验拦住——审计点名的「明确枚举/拒绝 ignored 新产物」仍未实现。
   `allow_non_repo` 在非 git 目录下的等价收紧也未覆盖。
