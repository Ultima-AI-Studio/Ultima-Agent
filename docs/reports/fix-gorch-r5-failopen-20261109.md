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


## 九、第六轮 Codex 独立审计结论（r6 交付后的复核）

审计执行：`gorch-r6-audit.py`，只读沙箱、`-a never`、`-m gpt-5.6-sol`、reasoning=high。
耗时 **810.3s**，输出 **17,450 B**，**127,146 tokens**，rc=0（`codex-r6-audit-status.json`）。

### 9.1 总判定

**部分一致。** 原文：「结构化终态、merge 的基本三条件、独立 merge 强制 `--run-dir`、
执行前脏基线错误阻断、cleanup schema 已落到实际判定；但严格 UTC、逐路径/ignored 写域校验、
manifest 唯一授权源均未闭合，并且 r6 新增了可证明的写域 fail-open 与授权拒签流程误杀，
因此不能判一致。」

### 9.2 逐条复核（11 条：6 ✅ / 4 ❌ / 1 ⚠️）

| # | 断言 | 判定 | 审计给出的关键证据 |
|---|---|---|---|
| 1 | verified 只按 `result=='done_no_merge'` | ✅ | `batch_orchestrator.py:767/1211/1426`；活动代码已无 reason 子串判定（`:1208` 仅历史注释） |
| 2 | merge 三条件 + `pre_anc` 前置取得 | ✅ | `:916/919/980/985/1001` 顺序正确；但前态查询失败被折叠成 `pre_anc=False`（见 9.3-4） |
| 3 | 预已祖先 / 无关 target 推进能被拒 | ✅ | `:983/985` + 用例 `test_gorch_batch_orchestrator.py:1172/1196` |
| 4 | 无 `--run-dir` 即 rc=2；fallback 无 mtime | ✅ | `:1337/1402/819`；但 `:791` 仍留未使用 `mtime` 字段、`:730` docstring 失实 |
| 5 | fallback 四类异常全阻断 | ❌ | `_utc_ts`（`:692`）对无时区值 `replace(tzinfo=UTC)` → **并非严格 UTC**；同一 invocation 多条不同时间不判不唯一；有效 JSON 但根节点非 dict 会在 `data.get` 崩溃（`:708`） |
| 6 | 执行前 `ERR:*` 在 run_codex 前阻断 | ✅ | `codex_channel.py:463/479/487` + 用例断言 `called==0` |
| 7 | `_fresh_paths` / `_outside_scope` 边界正确 | ❌ | 先 `strip()` 吃掉 porcelain 首空格；`fnmatch` 的 `*` 跨 `/`（`scripts/gorch/*.py` 可跨子目录）；rename 只留目标、源删除不校验（`:188/190/195/199/213/218`） |
| 8 | changed 越域即失败、不写 done | ❌ | 脏基线同路径内容变化只生成无路径的 `~ …` 汇总，被 `_fresh_paths` 丢弃 → `outside=[]` → 仍写 done（`:166/191/530/533/535/603`）；`status --porcelain -uall` 未带 `--ignored`（`:79`） |
| 9 | cleanup schema 参与 removed 判定 | ✅ | `:1071/1077/1086/1094/1101/1107`；`bool(items)` 已堵 `all([])` |
| 10 | 授权只从 manifest 读 | ❌ | 不传 manifest 时 `load_authorizations` 返回 `source='cli'`（`codex_channel.py:235/238`），主流程仍采纳 CLI flag（`:412`）→ 存在自授权入口 |
| 11 | 15 条用例覆盖 9 类 | ⚠️ | 数量确为 15（batch 11 + channel 4）且断言行为；未覆盖严格 UTC、CLI 缺 `--run-dir`、路径层级/反斜杠/通配边界、ignored、脏基线同路径越域、全/部分拒签 |

### 9.3 审计点出的 8 条新问题（含 2 条"成功判失败"）

1. **脏基线同路径越域修改可判成功**（`codex_channel.py:166/191/530/601`）。
2. **ignored 越域写不可见**（`codex_channel.py:79/132`）。
3. **rename 的域外源路径删除被忽略**（`codex_channel.py:199`）。
4. **merge 前态查询失败被当"前态不是祖先"**（`batch_orchestrator.py:853/917/985`）：
   `pre_anc = rc_pre == 0`，取证失败（None/128）时 `not pre_anc` 仍为真 → 可通过。
5. **显式 run-dir 未核对 run-record 身份**（`batch_orchestrator.py:745-765`）：
   不校验 `data['task']==task` / invocation / 记录内 `run_dir` → B 的 done 可映射给 A。
6. **不传 manifest 仍可自行签发例外**（`codex_channel.py:235/412`）。
7. **合法 tracked 修改可能被误杀**（`codex_channel.py:190`）：` M docs/…` 丢首空格 →
   路径变 `M docs/…` → 误判越域。
8. **拒签流程两条确定误杀/崩溃**：
   (a) 全部拒签时 `_stop`（`:1161`）在定义（`:1165`）之前被调用 → 局部名未绑定；
   (b) 部分拒签时 `run_all` 过滤了 ready（`:1158`），但 `execute` 又自行跑 gate 重建全部
   ready（`:467`），已拒签任务无 manifest 条目 → `:492` 抛错，连已授权任务也不能执行。

### 9.4 审计给的下一步最小清单

**可直接改**：逐路径内容指纹（`worktree_fingerprint:114` 改 `git status -z`、覆盖 tracked/
untracked/需监管 ignored）｜`_fresh_paths` 保留 rename 两端、去掉破坏首空格的 `strip()`｜
`_outside_scope` 改按路径段匹配（`*` 不跨 `/`）｜`_utc_ts` 拒绝无时区/非零 offset，fallback
同 invocation 多条即阻断，清理 `mtime` 字段与失实 docstring｜merge 前态 `rc_pre` 只允许 0/1
且 source/target SHA 非空｜`find_done_tasks` 精确分支校验 task/run_dir/invocation｜
移除无 manifest 的 CLI 自授权｜`_stop` 定义前移、`execute` 接收已过滤的授权集合｜
补严格 UTC / run-record 错绑 / tracked·ignored·rename·跨层通配 / CLI 缺 `--run-dir` /
全·部分拒签 的行为用例。

**需 Owner 定口径（3 项）**：
1. 手工调用 `codex_channel` 是否允许 CLI 自授权（若允许，"授权只从 manifest 读"必须限定为
   orchestrated 模式，且明确它不是可信生产入口）。
2. merge 是否必须证明"由本次调用造成"，还是只需"调用窗口内 source 成为 target 祖先"
   （当前排除不了另一进程在同一窗口合入同一 source）。
3. cleanup 在"调用前已三处消失"或 `wt remove` 非零但三处随后消失时，是否可不要求合法
   cleanup schema（当前 `:1031`、`:1054` 仍直接记 removed）。

### 9.5 审计对 pytest 的口径

原文：「本轮未运行 pytest，严格遵守约束。`108 passed / 39.12s` 只是提交方主张，
不是本轮独立复验结论。」——与前几轮一致，测试通过与否以本地实跑为准。

### 9.6 结论去向

- 第②环（Codex 独立审计）在本轮已跑，**未达成一致** → 按四段式流程，第③环
  （"让 Codex 出修复实现"）前提不成立，应回第①环做 **r7**。
- r7 的输入 = §9.4 的 8 条可直改 + 3 条口径；其中 3 条口径与「授权归 agent、人不参与
  执行期审批」并不冲突（属实现层收紧），但仍需 Owner 一句话确认形态。

## 十、r7 实现闭环（对应 §9 的 4 ❌ / 1 ⚠️ / 八条新问题 / 三条口径）

> 本轮只做四段式流程的第①环（助手自修）：把 §9 判为缺口的部分落到代码与用例。
> 是否与审计一致，由第七轮 Codex 复核，本报告不代下结论。

### 10.1 三条口径的落定形态

| 口径 | 落定形态 | 证据 |
|---|---|---|
| ① 手工调用 `codex_channel` 不允许 CLI 自授权 | `load_authorizations` 在无 `--manifest` 时直接置 `problem`（退出码 2）；`main()` 删掉整段 CLI 采纳逻辑，`--no-change-allowed` / `--allow-non-repo` 只写进 `record['ignored_cli_flags']` 留痕，实际取值一律以清单为准 | `codex_channel.py`（`load_authorizations`、`main()`）、`test_no_manifest_rejects_cli_self_authorization`、`test_cli_flag_without_grant_still_blocks` |
| ② merge 必须证明「由本次调用造成」 | 调用前先取 `target_sha`、`src_before`、`rc_pre` 三项；`target_sha` 取不到 → `SystemExit`（fail-closed），`src_before` 为空或 `rc_pre ∉ {0,1}` → 记 failed 并停止后续分支。判定仍为「target tip 前进 ∧ 源已是 target 祖先 ∧（调用前已是祖先时源 tip 必须变过）」 | `batch_orchestrator.py`（`merge()`）、`test_merge_rejects_when_pre_state_probe_fails` |
| ③ cleanup 两条豁免要独立证据 | 两条豁免条目在 `note` 之外新增 `evidence`：`dir_exists` / `branch_state` / `worktree_registered` /（超时那条另有 `wt_returncode`）/ `exemption`（`pre_absent` 或 `rc_zero_not_required`）/ `readback`。回读值分别来自目录、`_branch_state`、`_worktree_registered` 三处，不再凭 rc 或一句说明记成功 | `cleanup()`、`test_cleanup_pre_absent_three_way_records_evidence`、`test_cleanup_timeout_exemption_records_evidence` |

### 10.2 11 项复核逐条落地

| # | 第六轮结论 | r7 处置 | 用例 |
|---|---|---|---|
| ① | ✅ | 未动（`_stop` 前移只影响行号） | — |
| ② | ✅ 但前态查询失败被折成 `pre_anc=False` | 取证失败改 fail-closed（见口径②） | `test_merge_rejects_when_pre_state_probe_fails` |
| ③ | ✅ | 未动 | r6 两条保留 |
| ④ | ✅ 遗留 `:791` mtime、`:730` docstring 失实 | fallback 条目去掉 `mtime` 字段；docstring 改写为「严格 UTC + invocation 唯一性」 | — |
| ⑤ | ❌ `_utc_ts` 无时区 `replace(tzinfo=UTC)`、同 invocation 多条不判、根节点非 dict 崩 | `dt.tzinfo is None` 或 `utcoffset() != timedelta(0)` 一律返 None（只接受严格 UTC）；fallback 增 `dup_inv` 检测，同 invocation 多条即阻断；根节点非 dict 在 `data.get` 之前拦下 | `test_utc_ts_requires_strict_utc`、`test_run_dirs_rejects_non_dict_root`、`test_fallback_rejects_duplicate_invocation` |
| ⑥ | ✅ | 未动 | r6 两条保留 |
| ⑦ | ❌ 写域解析三处 | `_STATE_PREFIX` 只剥「两字符状态 + 一个空格」，不再用 `strip()` 吃掉路径首空格；`_scope_match` 改自写正则（`*`→`[^/]*`、`**`→`.*`、`?`→`[^/]`，其余 `re.escape`，`fullmatch` 或 `fullmatch(rx + '/.*')`）；rename 的 `' -> '` 两端都保留 | `test_state_prefix_keeps_leading_space_path`、`test_scope_star_does_not_cross_separator`、`test_rename_checks_both_ends` |
| ⑧ | ❌ 脏基线同路径变化被丢、`status` 未带 `--ignored` | `_status_rows` 改 `git status --porcelain -z -uall --ignored`，NUL 切分，`!!` 收进 `ignored` 且计入 `paths`；`worktree_fingerprint` 改逐路径 sha256 摘要（超 8MiB 用 `BIG:<size>:<mtime>`，读失败 `ERR:<errno>`）；`fresh_changes` 判「新路径 ∪ 同路径摘要变」 | `test_same_path_content_change_is_fresh`、`test_ignored_path_outside_scope_blocks`、`test_staging_only_is_not_fresh` |
| ⑨ | ✅ | 未动 | r6 一条保留 |
| ⑩ | ❌ CLI 自授权入口 | 见口径① | 同口径① |
| ⑪ | ⚠️ 用例数量对但未覆盖 9 类场景 | 新增 20 条（batch 11 / channel 9），见 10.4 | — |

### 10.3 八条新问题

| # | 新问题 | 处置 | 用例 |
|---|---|---|---|
| 1 | 脏基线同路径越域可判成功 | 逐路径内容摘要 + `fresh_changes` 同路径摘要变即算新增 | `test_same_path_content_change_is_fresh` |
| 2 | ignored 越域写不可见 | `--ignored` 纳入状态行，`ignored` 集合同时进 `paths` 参与写域校验 | `test_ignored_path_outside_scope_blocks` |
| 3 | rename 域外源删除被忽略 | `_fresh_paths` 把 rename 两端都产出，两端都要过 `write_scope` | `test_rename_checks_both_ends` |
| 4 | merge 前态查询失败被当「前态不是祖先」 | `src_before` / `rc_pre` 取证失败即 fail-closed，记 failed 并停后续 | `test_merge_rejects_when_pre_state_probe_fails` |
| 5 | 显式 run-dir 未核对 run-record 身份（B 的 done 可映射给 `A=PATH_TO_B`） | 四道校验全部前置于 `dry_run` 判断：根节点非 dict / `task` 不符 / `run_dir` basename 不符 / `invocation` 为空 | `test_run_dirs_rejects_record_of_another_task`、`test_run_dirs_rejects_record_without_invocation`、`test_run_dirs_rejects_non_dict_root` |
| 6 | 不传 manifest 仍可自签例外 | 见口径① | `test_no_manifest_rejects_cli_self_authorization` |
| 7 | 合法 tracked 修改被误杀（首空格被 `strip()` 吃掉） | `_STATE_PREFIX` + `_norm_path`（只剥真正的 `./`，不再 `lstrip('./')`） | `test_state_prefix_keeps_leading_space_path`、`test_hidden_dir_path_is_not_truncated` |
| 8 | 拒签流程两条误杀/崩溃 | `_stop` 定义前移到 `if refused:` 之前；`execute(..., tasks=None)` 只收窄不扩张，`run_all` 传 `tasks=ready`，已拒签任务不再被重建进 ready | `test_run_all_returns_gate_when_all_grants_refused`、`test_execute_does_not_restore_refused_tasks` |

### 10.4 用例与实跑

- 新增 20 条：`test_gorch_codex_channel.py` 9 条（无 manifest 拒签 / CLI 开关不构成授权 / ignored 越域 / `*` 不跨 `/` / rename 两端 / 首空格路径 / 同路径内容变化 / 仅暂存不算新增 / 隐藏目录不被截断），`test_gorch_batch_orchestrator.py` 11 条（严格 UTC / run-record 身份 3 条 / dup invocation / merge 前态取证 / merge CLI 必须带 run-dir / 全拒签返回 gate / execute 不收窄回吐 / cleanup 证据 2 条）。
- 实跑（仓库根、专用解释器、`-o addopts=`、`-p no:cacheprovider`）：
  - 单跑 `tests/test_gorch_codex_channel.py` → **36 passed / 11.25s**
  - 单跑 `tests/test_gorch_batch_orchestrator.py` → **92 passed / 31.36s**
  - 两文件合跑 → **128 passed / 42.18s**（r6 基线 108 passed / 39.12s）
- 四个文件 `py_compile` 全部 ok。

### 10.5 仍未闭合（诚实边界）

1. `done_no_merge` 的终态名与三分组（`mergeable_done` / `verified_only` / `stale`）仍未书面落定，牵动契约 v1.3；本轮不动它。
2. `run_all` 改动后**未用真实批次重跑**：旧卡 `GORCH-RUN-A/B` 会因「无新增」判 blocked，需换任务名后另跑一轮；冲突形态全链仍只有单测，`#9` 冲突恢复路径未实现。
3. 八跳第 4 跳（主脑回传授权条件）仍只有单测，未进 `run_all`。
4. 口径②的「本次调用造成」仍建立在 SHA 比较与时序上：同一窗口内若有第三方进程以**同一 source** 推进 target，理论上仍可能误判——彻底分离需要 git 侧事务级证据，本轮不做。
5. `_status_rows` 的 ignored 条目上限 4000，超出即 `ERR:ignored>4000` 阻断（宁可拒也不静默）。
6. 本报告所有测试数字均为提交方本地实跑，非审计方独立复验；第七轮审计若同样不跑 pytest，仍需按「主张」对待。

## 十一、第七轮 Codex 独立审计（判定：不一致）

> 审计对象：`1e041843`（代码）+ `5dfdf61f`（文档），HEAD/tag `gorch-r7-failopen-closeout-20261109`。
> 严格只读，**未运行 pytest**。耗时 **882.0s / 24,336B / 144,283 tokens**。
> 仓库身份由审计方只读核验：分支 `codex/voice-fsmn-new-path`，HEAD 与 tag 均指向
> `5dfdf61f`，六个被审文件无工作区修改，代码提交统计确为 4 文件 / `+649 / -150`。

### 11.1 总判定原文

> 「**不一致。** r7 确实闭合了严格 UTC、无 manifest 拒签、merge 前态查询失败、拒签任务回流
> execute 等部分问题，但真实 rename 解析仍丢源路径、显式 run-record 身份校验不完整、
> cleanup 证据值反写，而且生产执行记录根本未写 `invocation`，会使正常 `run_all` 在执行成功后
> 仍被 merge 阶段拒绝。」

### 11.2 复核表（判定均引自审计原文的行号）

| 编号 | 结论 | 审计给出的证据与要点 |
|---|---|---|
| A⑤ 严格 UTC / 重复 invocation / 非 dict 根 | ❌ | 前两项已闭合（`batch_orchestrator.py:715`、`:719`、`:853`）；但非 dict 只在显式 `run_dirs` 的 `:774` 拦下，fallback 在 `:817` 解析后直接于 `:821`、`:825` 调 `data.get`，JSON 数组仍会崩；用例 `:1320` 只覆盖显式路径 |
| A⑦ 写域解析三处 | ❌ | `*` 不跨 `/` 已修（`codex_channel.py:271–286`）；但真实 `-z` rename 在 `:84` 遇第二路径直接 `i += 1` 丢弃、`:87` 只存目标，`_fresh_paths`（`:251`）期待的 `' -> '` 文本在结构化数据里根本不存在；用例 `:669` 是手造字符串。另 `_norm_path`（`:232`）仍 `strip()`，会改写首尾空格文件名 |
| A⑧ 脏基线同路径 / ignored / status 参数 | ⚠️ | `--porcelain -z -uall --ignored`（`:58–66`）、ignored 进 `paths`（`:180–191`）、同路径摘要不同算 fresh（`:217–219`）都已落地；但 `BIG:size:int(mtime)` 与 `ERR:errno`（`:160–165`）不是内容指纹，脏基线下同摘要仍可漏检 |
| A⑩ CLI 自授权入口 | ✅ | `:313–317` 无 manifest 即 `problem`；`main()` `:486–499` 只取 manifest；用例 `:591–614` 同时断 `blocked` 与 `called['n'] == 0` |
| A⑪ 用例数量与强度 | ❌ | 静态数 36 + 92 = 128，§10 所列新增名都在；但多条只测 helper：rename 只喂箭头字符串（`:672`）、run-record helper 人工补了生产端没写的 `invocation`（`:398–411`）、cleanup 用例在 `:1456` 断言了相反的语义 |
| 口径① 禁止 CLI 自授权 | ✅ | 授权值只来自 `codex_channel.py:498–499` 的 `auth` |
| 口径② merge 须证明本次造成 | ❌ | 终判据 `batch_orchestrator.py:1041–1043` 仍是「target 前进 + 调后为祖先 + 必要时 source 移动」；调用前非祖先时，第三方在窗口内合入同一 source 同样满足三项；代码也没用 wt 回执 `committed/squashed/rebased` 证因果 |
| 口径③ cleanup 豁免写回读值 | ❌ | 三处确实分别回读（`batch_orchestrator.py:1115–1117`），但超时豁免把 `wt_gone = not wt_path.is_dir()` 写成 `evidence['dir_exists'] = wt_gone`（`:1125`）——目录已消失时记录反为 `True`，且用例 `:1456` 固化了这个错值 |

B 组（第六轮八条新问题）：B1 ⚠️（同 A⑧ 的 `BIG/ERR`）、B2 ✅（4000 条是硬阻断不是放行）、B3 ❌（同 A⑦）、B4 ✅、B5 ❌（`run_dir` 缺失即放行、只比 basename、`invocation` 只验非空不验等于本次、`mergeable` 完全未验）、B6 ✅、B7 ✅（但首空格仍被 `_norm_path.strip()` 改写）、B8 ✅（但部分拒签仍会被 `provision()` 重建，见 N5）。

### 11.3 七条新引入问题

| 编号 | 严重度 | 问题 | 为什么 |
|---|---|---|---|
| N1 | **严重** | 生产 `codex-channel.json` 不写 `invocation`（`codex_channel.py:461–465`、落盘 `:679–687`），消费端却强制要求非空（`batch_orchestrator.py:792–795`） | 生产者—消费者契约断裂：正常 `run_all` 即使 execute 返回 0，也会在 merge 阶段被判 stale → 全链误杀 |
| N2 | 高 | `_digest` 用 `BIG:size:int(mtime)` / `ERR:errno` 代替内容摘要（`codex_channel.py:160–165`），`fresh_changes` 只比字符串（`:218–219`） | 脏基线里域外大文件在同一秒等长改写，摘要不变；只要同时有一条域内 fresh，整体仍可 `done` → 写域 fail-open |
| N3 | 高 | `wt_merge` 注释明说默认 cleanup 会删 worktree 与分支（`batch_orchestrator.py:631–637`），但成功后仍用可能已删的分支名做 `merge-base` 与 `src_after`（`:1038–1043`） | wt 正常 squash 后删 source 时 `rc_anc≠0`、`src_after` 为空 → 真成功被判 failed；「调用前已是祖先时强制 src_moved」同样误杀 |
| N4 | 中 | `_norm_path` 仍 `strip()`（`:232`）；`_scope_match` 先做纯字符串 `startswith(p + '/')`（`:269`） | 首尾空格文件名被改写；`docs/../outside` 因前缀命中被接受；无绝对路径 / drive / `..` 拒绝 |
| N5 | 中 | `run_all` 剔除拒签任务（`:1237–1239`）后仍无过滤调 `provision(batch_dir)`（`:1248`），`provision` 自己重跑 gate 为全部 ready 建 worktree（`:287–297`） | 部分拒签时，未授权任务仍被建 worktree/分支；反向问题是 CLI `execute --manifest <子集>` 无 `tasks`，会在 `:496–498` 整批误杀 |
| N6 | 中 | `load_authorizations` 解析后未验根节点即 `data.get`（`codex_channel.py:323`、`:327`）；`_load_grants` 同（`:450–453`） | 合法 JSON 数组 manifest 抛未捕获 `AttributeError`，不是预期的 blocked/SystemExit，审计记录缺失 |
| N7 | 中 | 超时豁免的 `dir_exists` 反写（`batch_orchestrator.py:1125` + 用例 `:1456`） | 生成与现场相反的审计证据，下游按字段消费会把「已消失」读成「仍存在」 |

审计同时排除了两个误报方向：`base_fp is None`（基线 clean）把执行后全部 `paths` 视为新增是合理的（`:536–541` 证明只在 `base_kind == clean` 时成立），剩余风险是并发进程在采样窗口写同一 worktree；ignored 超 4000 条是硬阻断（`:184–186` + `:595–600`），属误杀/DoS 而非 fail-open。

### 11.4 文档与代码一致性（审计结论）

**文档说改了但代码没做到**：§10.2 的「根节点非 dict 在 `data.get` 前拦下」只对显式 `run_dirs` 成立；§10.2 的「不再 `strip()` 吃首空格、rename 两端都保留」与实际不符；§10.3 的「四道 run-record 身份校验」实际缺 `run_dir` 必填、`invocation` 等值、`mergeable`；§10.1 的 cleanup evidence 超时那条值相反；§10.1 把口径②写成「落定形态」，而 §10.5 又承认窗口误判仍在（审计指出这两处自相矛盾）。

**代码有、文档没写**：生产记录不写 `invocation` 的契约冲突；`BIG/ERR` 不是内容证明；部分拒签仍被 `provision` 重建；manifest 根非对象仍崩；`codex_channel` 的 `:308`、`:444–447` 帮助与 docstring 仍写「无清单时手工回退」，与实际实现相反。

**文档准确的部分**：§10.4 静态数量 36/92/128 与新增 20 个用例名核验一致；L83 的默认清单写法、`lstrip('./')` 与超时用例描述与代码一致；§10.5 的三条保留说明准确。审计注明 `11.25s / 31.36s / 42.18s` 无法由只读源码确认。

### 11.5 需 Owner 拍板三条（审计原话归纳）

1. **merge 因果证明方式**：现有 SHA 时序判据排除不了同窗口第三方合入同一 source。候选：合并全程独占锁 / 能绑定具体 invocation 的 wt 事务回执 / reflog 与执行产出 commit 的精确对应。单纯「窗口前后 SHA 变化」不满足口径②。
2. **调用前 source 已是 target 祖先时的 squash 语义**：若 wt 允许把未提交内容直接 squash 到 target 并删除 source ref，「source tip 必须移动且调后仍可按名查祖先」会误杀。需明确接受哪种证据（目标新增 commit/tree、wt 的 `squashed/committed` 回执、还是强制 source 先落 commit 并保留到复核完成）。
3. **「编排方签发 manifest」的可信边界**：当前任何调用者可自建 JSON 后传 `--manifest`，只满足「有 manifest」，没证明「是编排方签的」。若「签发」含来源真实性，需规定受控目录、manifest hash/nonce 或签名。

### 11.6 结论去向

- 第②环（Codex 独立审计）判 **不一致** → 第③环（让 Codex 出修复实现）前提不成立 → 回第①环做 **r8**。
- r8 输入 = 11.3 的 N1–N7（全部可直改）+ A⑤/A⑦/A⑪/B5 的挂载点补强（用例必须打到真实解析层与真实生产者，而不是 helper）+ 11.5 的三条口径待 Owner 拍板。
- 诚实说明：N1 是 r7 自身引入的契约断裂（生产端不写 `invocation`，消费端却强制要求），r7 的「128 passed」并未覆盖它——现有用例用 `write_run()` 人工注入该字段，正好掩盖了这个缺口。
## 十二、r8 实现闭环（第七轮审计「不一致」→ 逐条回修）

### 12.1 可直改八条的落地位置

| # | 第七轮审计要求 | r8 落地 | 证据位置（符号名） |
|---|---|---|---|
| 1 | `load_authorizations` 回传 manifest 级 `invocation`/`target`，并在记录创建时写入；补「真实产出可被 `find_done_tasks(run_dirs=...)` 消费」测试 | 回传 `manifest`/`invocation`/`target`；`main()` 建 record 时写三项并在授权后覆盖 | `codex_channel.load_authorizations`、`codex_channel.main` 的 record 构造段；用例 `test_record_carries_manifest_identity`、`test_find_done_tasks_consumes_real_producer_record` |
| 2 | 显式 run-record 身份校验改全：根节点对象、`task` 精确相等、`run_dir` 必填且绝对路径相等、`invocation` 等值、`dry_run is False`、`result == 'done'`、`mergeable is True`；不得只比 basename | 七项逐条前置，任一不满足即进 `stale`；选定最新记录后再复核 `mergeable` | `batch_orchestrator.find_done_tasks` 显式分支、fallback 分支；用例 `test_run_dirs_rejects_record_without_run_dir`、`test_run_dirs_rejects_run_dir_pointing_elsewhere` |
| 3 | `-z` 解析把 rename/copy 的目标与随后源路径都纳入结构化 row/path；**测试直接构造 NUL 序列喂解析层** | `_status_rows` 保留 `('SRC', src)` 行；`_fresh_paths` 支持 `SRC ` 前缀并兼容旧展示形态 **（已作废：r9 已删该兼容，见 §13.4 / §14.2）** | `codex_channel._status_rows`、`_fresh_paths`；用例 `test_status_rows_keeps_rename_source_from_real_nul`、`test_status_rows_rename_source_is_in_fingerprint_paths` |
| 4 | 改流式 SHA-256；任何读错误使整份 fingerprint 明确不可用，执行前/后统一 fail-closed | `_digest` 全程分块 sha256、读失败返回 `None`；`worktree_fingerprint` 任一 `paths` 值为 `None` 即整份 `ERR:digest:<path>` | `codex_channel._digest`、`worktree_fingerprint`；用例 `test_digest_read_error_invalidates_whole_fingerprint` |
| 5 | 保留文件名首尾空格、只剥精确 `./`；写域前拒绝绝对 / drive / UNC / 任何 `..` 段；scope pattern 同样做 repo-relative 校验 | `_norm_path` 去掉 `strip()` 只剥 `./`；新增 `_repo_relative_safe`；`_scope_match` 双侧先过合法性检查，`_outside_scope` 遇不合法直接判越域 | `codex_channel._norm_path`、`_repo_relative_safe`、`_scope_match`、`_outside_scope`；用例 `test_norm_path_keeps_edge_spaces_and_hidden_dirs`、`test_scope_check_rejects_parent_traversal` |
| 6 | `dir_exists: not wt_gone`，用例断言 `False` | 已改（r8 前段）；用例两处断言 `False` | `batch_orchestrator.cleanup` 的超时豁免段；用例 `dir_exists is False` 两处 |
| 7 | `provision()` 增加 `tasks` 收窄并在 `run_all` 传过滤后的 ready；CLI `execute --manifest` 收窄或加 `--tasks` | `provision(batch_dir, tasks=None)` / `execute(..., tasks=None)`；`run_all` 传 `tasks=ready`；CLI 两者都加 `--tasks`；`execute` 拿回 grants 后再收窄一层 | `provision`、`execute`、`run_all`、`main()` 的 `--tasks`；用例 `test_provision_tasks_narrows_out_unauthorized` |
| 8 | 三处读 manifest / run-record 统一先验根节点为对象 | `load_authorizations`、`_load_grants`、fallback 分支均先验 `isinstance(data, dict)`，否则 problem / stale（不再抛 `AttributeError`） | `codex_channel.load_authorizations`、`batch_orchestrator._load_grants`、`find_done_tasks` fallback |

### 12.2 口径② merge 因果证明：本轮落定形态

r7 只有布尔 `proven`，说不清「凭什么算本次造成」。r8 改成**分级证据 + 合并锁**，并把用了哪一级写进 `merged` 条目（`proof` / `source_tree_before` / `target_tree_after`）：

| 级别 | 判据 | 强度 |
|---|---|---|
| `ff` | target tip 前进 且 `merge-base --is-ancestor <src_before> <target>` rc=0 且（调用前不是祖先 或 源 tip 移动过） | 历史图直接可核；「调用前已是祖先」时必须看到源 tip 变动，否则是合了老提交 |
| `tree` | target tip 前进 且 调用后 target 的 tree 与调用前源分支的 tree 完全相同 | 内容逐字节可核，不依赖分支名是否还在（覆盖 wt squash 后删 source 的 N3 场景） |
| `wt_receipt` | target tip 前进 且 wt 回执 `committed`/`squashed`/`rebased` 为真 | 最弱：wt 自报。只在 A/B 都不成立时兜底——未提交产出经 wt 提交后 squash，源旧 tip 的 tree 与结果 tree 本就不同，不给 C 会把合法 squash 判死 |

同时新增 `_MergeLock`：按 repo+target 取本机文件锁（Windows `msvcrt.locking` / POSIX `flock`，非阻塞，占用即 `SystemExit` fail-closed），把同仓 gorch 的合并窗口串行化。锁目录按 `RUNS.parent/'locks'` 在运行时计算，便于测试隔离。

> **r9 更正**：本段写于 r8，锁只包住 `wt_merge()`，前后取证在锁外（第八轮审计 N8）。r9 已把整段取证收进同一把锁，`ff` 档也改了 `pre_anc` 时的核验对象（N9）——以 **§13.1** 为准。下文「不约束外部 git/其他工具」这句仍然成立。

**边界（必须写明）**：这把锁只约束本工程的 gorch 进程，**不约束外部 git/其他工具**在窗口内推进同一 target。因此 A/B/C 都不是「唯一因果」的严格证明，只是「本次动作确有可核证据 + 同仓不并发」。真正的严格证明需要 wt 提供能绑定 invocation 的事务回执（或 reflog 与产出 commit 的精确对应），当前 `wt merge --format json` 只有 `branch/target/committed/squashed/rebased/removed`，没有该字段。本项仍属第七轮审计 11.5 第 1 条的「需口径」，本轮按可机检最强形态落地，**未取得 Owner 书面拍板**。

### 12.3 测试

- 合跑：`139 passed / 40.63s`（r7 为 128 passed / 42.18s；r8 新增 10 条，另含工作区先前新增的 rename 两条）。
- 命令：`tools\venv-openjarvis\Scripts\python.exe -m pytest tests/test_gorch_batch_orchestrator.py tests/test_gorch_codex_channel.py -o addopts= -p no:cacheprovider -q`（cwd 仓库根、PATH 前置 Git）。
- r8 新增 10 条：`test_record_carries_manifest_identity`、`test_scope_check_rejects_parent_traversal`、`test_norm_path_keeps_edge_spaces_and_hidden_dirs`、`test_digest_read_error_invalidates_whole_fingerprint`、`test_provision_tasks_narrows_out_unauthorized`、`test_run_dirs_rejects_record_without_run_dir`、`test_run_dirs_rejects_run_dir_pointing_elsewhere`、`test_merge_proves_tree_equivalence_when_source_ref_gone`、`test_merge_falls_back_to_wt_receipt_after_uncommitted_squash`、`test_find_done_tasks_consumes_real_producer_record`。
- 这些用例的挂载点是**真实层**：rename 走 `_status_rows` 的 NUL 解析、记录身份走 `merge`/`find_done_tasks` 入口、生产者—消费者走 `codex_channel.main()` 真实落盘后由 `find_done_tasks(run_dirs=...)` 消费，不是只测 helper。**（已作废：此整片断言不成立，见下一行的 r9 更正与 §14.4 的逐条标注）**
  - **r9 更正（第八轮审计 N12）**：上面这句对 proof 两条不成立——`test_merge_proves_tree_equivalence_when_source_ref_gone` 与 `test_merge_falls_back_to_wt_receipt_after_uncommitted_squash` 是**全桩化**（`_git_out`/`_ref_sha` 都替身）。r9 保留桩化但把断言收紧到具体档位与字段，逐条标注见 **§13.3**。
- 静态计数（按 `^def test_` 实测）：batch 92 → 98、channel 36 → 41，合计 **139**；其中 r8 新增 10 条（batch 6 + channel 4），channel 另含本轮前段新增/改造的 2 条 rename 用例。

### 12.4 文档一致性修正

第七轮审计 11.4 点名的五处「文档说改了但代码没做到」，r8 已按代码为准修正对应实现；本报告 §10.1–§10.3 的旧描述**以本章为准**，不再作为 r7 实现状态的依据。（**r9 更正**：第八轮审计判定本章自身也有「声明强于实现」五处，故 §10–§12 的实况一律以 **§13** 为准。）原 §10 保留为历史轮次记录，不回溯改写（避免掩盖当时的真实状态）。

### 12.5 仍未闭合 / 残余风险

1. **口径② 严格性**：见 12.2 边界——外部 git 不受锁约束；无 wt 事务回执。
2. **口径③（manifest 签发可信边界）**：仍未实现受控目录 / hash / nonce / 签名。当前只保证「有清单、且清单内容被逐项校验」，不保证「是编排方签的」。任何能写文件并传 `--manifest` 的调用者仍可自签发。属 11.5 第 3 条待口径。
3. **真实批次复跑**：旧卡 `GORCH-RUN-A/B` 会因「无新增」判 blocked，需换新任务名；本轮未跑真实全链，`run_all` 的 `tasks` 收窄只有单测覆盖。
4. **`base_fp is None` 的并发采样窗口**：执行前后各采一次，第三方在窗口内写同一 worktree 仍不可区分（审计已认定该口径可接受，残余风险保留）。
5. **`done_no_merge` 终态命名与三分组**（`mergeable_done / verified_only / stale`）未做完备形态。

### 12.6 结论去向

- r8 交第八轮 Codex 独立审计（第②环），判据入口：12.1 的八条、12.2 的三级证据、12.3 的用例挂载点、12.4 的文档一致性、12.5 的残余声明。
- 若第八轮仍判「不一致」，继续 r9；用户指令为长任务模式，直到审计判「一致」才停。

## 十三、r9 实现闭环（第八轮审计「不一致」→ 逐条回修）

### 13.1 可直改六条 + N2 复发的落地位置

| # | 第八轮审计要求 | r9 落地 | 证据位置（符号名 / 用例） |
|---|---|---|---|
| N8 | `_MergeLock` 必须覆盖完整取证窗口 | `target_sha = _ref_sha(resolved_target)` 从循环外移进 `with _MergeLock(resolved_target):` 块首；`src_before` / `src_tree` / `target_tree_before` / `pre_anc` / `wt_merge()` / 回执解析 / `rc_anc` / `sha_after` / `src_after` / `top_tree` / proof 判定 / `merged.append` **全在同一 with 内** | `batch_orchestrator.merge()` 的 `with` 块；用例 `test_merge_lock_is_exclusive` **（r10 更正：本行「`merged.append` 全在同一 with 内」在 r9 提交时并不成立——`failed.append` / `merged.append` 仍在 `with` 外（第八轮审计已点名）；r10 已整段移进 `with`，该声明自 r10 起为真）** |
| N9 | 三档 proof 都可错误归因 | ① 新增三档**共同前置** `content_changed`：`target_tree_before` 与 `top_tree` 必须不同——空提交、revert 回同一 tree 不再算「合进去了」；② `ff` 档在 `pre_anc=True` 时**不再**用旧 `src_before` 查 `merge-base`（那恒为真），改核 `src_after` 新 tip；③ `wt_receipt` 沿用 r8 已有的 branch/target 严格等值校验（回执身份不符即 `SystemExit`） | `merge()` 的 proof 段；`merged[]` 新增 `target_tree_before`；用例 `test_merge_rejects_when_only_stale_proof_candidates`、`test_merge_proves_tree_equivalence_when_source_ref_gone`、`test_merge_falls_back_to_wt_receipt_after_uncommitted_squash` |
| N10 | `dry_run` 用 truthy、invocation 等值可选、CLI 可缺 | `dry_run is not False` / `result != 'done'` / `mergeable is not True` / `invocation` 非空且 `== expect_invocation` 四项全部**前置**到 `entries.append` 之前（进 broken），选定「最新记录」后才验的老写法整段删除；`run_dirs` 模式不给 `expect_invocation` 直接 `SystemExit`；CLI `merge --invocation` 改 `required=True` | `find_done_tasks` 入口守卫 / 显式分支 / fallback 分支；`main()` 的 merge 子命令；用例 `test_run_dirs_mode_requires_expected_invocation`、`test_run_dirs_rejects_foreign_invocation`、`test_merge_rejects_record_without_strict_dry_run`、`test_merge_cli_requires_invocation` |
| N11 | `_fresh_paths` 用字符串前缀猜格式 | 删模块常量 `_STATE_PREFIX`；`_fresh_paths` 只接受**纯路径**，逐个 `_norm_path` 后交 `_repo_relative_safe`，判非法即 fail-closed；不再剥 `SRC ` / `?? ` / ` M ` 前缀 | `codex_channel._fresh_paths`；用例 `test_fresh_paths_takes_pure_paths_only`、`test_src_prefixed_real_filename_is_not_rewritten` |
| N12 | 测试覆盖声明强于实际 | 新增 8 条（见 13.3）；`test_merge_lock_is_exclusive` 真起第二进程争锁；生产者—消费者用例改传 `expect_invocation='inv-prod'`（与生产侧写入值一致），不再靠默认值蒙过 | `tests/test_gorch_batch_orchestrator.py`、`tests/test_gorch_codex_channel.py` 的 r9 段 **（r10 更正：本行「真起第二进程争锁」在 r9 提交时并不成立——`test_merge_lock_is_exclusive` 是**同进程**第二个 `_MergeLock` 实例；r10 另增 `test_merge_lock_is_exclusive_across_processes` 起真子进程持锁，原用例保留）** |
| N2 复发 | `_digest` 把所有 `OSError` 当 ABSENT | `except FileNotFoundError: return 'ABSENT'`；其余 `except OSError: return None`（整份指纹判不可用）；`is_file()` 同样包 `OSError → None` | `codex_channel._digest`；用例 `test_digest_stat_error_is_not_absent` |
| D 段 | 看板写「未提交（工作区在制）」与实际 HEAD 不符 | 随本笔 r9 文档提交一并改为实际提交号 | 看板 r8 条目 |

### 13.2 需口径五条：仍未拍板，r9 不改语义

1. **merge 严格因果证明**：外部 git / 其他工具不受本进程锁约束；`wt merge --format json` 仍无能绑定 invocation 的事务字段。r9 只把「本工程内的窗口」收干净，不等于「唯一因果」。
2. **调用前 source 已是 target 祖先时的 squash 语义**：r9 改成核「新 tip 进没进」，语义仍需 Owner 确认（若 wt 允许把未提交内容 squash 到 target 并删掉 source ref，`src_after` 会为空，此时只剩 `tree` / `wt_receipt` 两档）。
3. **manifest 签发可信边界**：仍未做受控目录 / hash / nonce / 签名。
4. **manifest `target` 是否必须绑定一次独立 merge**：未落。
5. **`wt_receipt` 能否作最终兜底**：r9 保留其为第三档，且要求 target 内容真变；是否接受仍待拍板。

第七轮 11.5 的三条（第 1、2、3 项）在本节仍全部成立，未取得 Owner 书面批准。

### 13.3 测试与静态计数

- 合跑：**147 passed / 47.90s**（r8 为 139 passed / 40.63s）。
- 命令：`tools\venv-openjarvis\Scripts\python.exe -m pytest tests/test_gorch_batch_orchestrator.py tests/test_gorch_codex_channel.py -o addopts= -p no:cacheprovider -q`（cwd 仓库根、PATH 前置 Git）。
- 静态计数（`^def test_` 实测）：batch 98 → **104**、channel 41 → **43**，合计 **147**。
- r9 新增 8 条：
  - batch：`test_run_dirs_mode_requires_expected_invocation`、`test_run_dirs_rejects_foreign_invocation`、`test_merge_rejects_record_without_strict_dry_run`、`test_merge_lock_is_exclusive`、`test_merge_rejects_when_only_stale_proof_candidates`、`test_merge_cli_requires_invocation`
  - channel：`test_digest_stat_error_is_not_absent`、`test_src_prefixed_real_filename_is_not_rewritten`
- 因语义收紧而**改语义**的既有用例：`test_state_prefix_keeps_leading_space_path` → 更名 `test_fresh_paths_takes_pure_paths_only`；`test_status_rows_keeps_rename_source_from_real_nul` 的路径取自结构化 `rows`（不再拼「状态码+空格+路径」再交给解析层去剥）；`test_merge_cli_requires_run_dir` 补 `--invocation`；4 条 `find_done_tasks` 负向用例的 payload 补 `dry_run` / `mergeable`，`test_find_done_tasks_only_reads_this_invocation` 的 `reason` 断言改为「身份项先判否」（blocked 记录不再进候选池，也不再透传记录里的 reason 文案）。
- **桩化边界（如实标注）**：`run_all` 串行、冲突停批、`refs/heads/` 前缀、tree 等价、wt 回执兜底这 5 条仍是桩（`wt_merge` 与 `_git_out` 替身）；其中前 3 条走 `mod` fixture 默认桩（r9 让 `rev-parse` 的 tree 随调用递增，以适配新增的前态 tree 取证），后 2 条各自定制 tree 序列。`test_merge_lock_is_exclusive`、生产者—消费者用例打真实层（真文件锁 / 真 `codex_channel.main()` 落盘）。

### 13.4 对 §12 声明的收敛（第八轮 D 段点名五处）

- **§12.1 #3 作废**：该行写「`_fresh_paths` 支持 `SRC ` 前缀并兼容旧展示形态」——r9 已删掉这条兼容，理由是「按前缀猜格式」本身就是 N11 的 fail-open 根因。现在解析层直接产出 `('SRC', path)` 结构化行，下游只拿纯路径。
- **§12.2 收敛**：「锁把同仓 gorch 合并窗口串行化」只在 r9 之后成立（r8 只锁 `wt_merge()` 一句），且始终只约束**本工程 gorch 进程**。
- **§12.3 收敛**：删去「全部打在真实层」的整片断言，改为 13.3 的逐条标注（5 条桩 / 2 条真实层）。
- **§12.4 收敛**：§10–§12 的实况一律以 §13 为准；§12 自身也含过期声明。
- **§12.5 补漏**：漏记的四项（锁范围、`stat → ABSENT`、路径前缀碰撞、run-record 非严格身份）已在 13.1 逐条列出。

### 13.5 残余风险（r9 后仍存在）

1. 13.2 的 5 条口径未拍板。
2. 外部 git 不受锁约束；wt 无 invocation 级事务回执 → 因果证明上限未变。
3. `target_tree_before` 取不到时 `content_changed` 恒为假，整条 proof 降级为 `failed`（fail-closed，但会把「取证失败」和「没合进去」归到同一出口）。
4. 真实批次未重跑 `run_all`（旧卡会被「无新增」判 blocked，需换任务名）；冲突形态全链仍只有单测。
5. `done_no_merge` 三分组（`mergeable_done / verified_only / stale`）未落。

> **r10 补记（第九轮审计 D 段点名本节漏记五项）**：以下五项在 r9 时确实存在，r10 已逐条修掉——
> ① 工作区侧 ` R` / ` C` 的源路径被当成状态行（能放行越域写）；② `fresh_changes` 只遍历 after 集，
> 基线里消失的域外路径不可见；③ `refs/heads/x` 与 `x` 是两把锁（ref 别名可绕锁）；④ `pre_anc`
> 查可变分支名、`rc_anc` 查 `src_before`，两者不是同一个冻结 ref；⑤ cleanup 目录探针只有
> `is_dir()` 两态，不可读会被记成「已清理」。修法与证据见 **§14.2**。

### 13.6 结论去向

- r9 交**第九轮 Codex 独立只读审计**（第②环），判据入口：13.1 六条 + N2 复发、13.3 的覆盖与桩化标注、13.4 的声明收敛、13.5 的残余声明。
- 若第九轮仍判「不一致」，继续 r10；用户指令为长任务模式，直到审计判「一致」才停。


## 十四、r10 实现闭环（第九轮审计「不一致」→ 逐条回修）

### 14.1 第九轮审计判定

第九轮 Codex 独立只读审计（`gpt-5.6-sol`、`high`、read-only、896.8s / 38,686B）判**不一致**，给出三个高优反例和一批点名项：

1. **高** `_status_rows` 只查 `code[:1]`：工作区侧合法的 ` R` / ` C` 处理不了，紧随的裸源路径被当成下一条状态行、`item[3:]` 截掉前三字符 → 域外源删除伪装成域内路径，**能放行越域写**（不只是误杀）。构造：未暂存 rename `zzzdocs/secret.md → docs/x.md` 产生 ` R docs/x.md\0zzzdocs/secret.md\0`。
2. **高** `fresh_changes` 只遍历 after 集，`b_paths - a_paths` 完全被忽略 → 任务把基线里的域外脏文件恢复成 HEAD、再顺手改一个域内文件即可过写域检查落 `done`。
3. **高** `_MergeLock.__init__` 拿未归一化的 `resolved_target` 造锁文件名 → `main` 与 `refs/heads/main` 得到两把锁，两个 gorch 可同时进入同一 target 的取证窗口。
4. 其余点名：`merged.append` 在锁外（与 §13/看板「全在同一 with 内」不符）；`test_merge_lock_is_exclusive` 不是第二进程；`test_merge_rejects_record_without_strict_dry_run` 只覆盖 `dry_run=None`；`test_find_done_tasks_only_reads_this_invocation` 的 reason 断言退化成「非空即过」；`pre_anc`（查可变 `branch`）与 `rc_anc`（查 `src_before`）不是同一 ref；`target_tree_before` 取不到时不在 `wt_merge` 前停；cleanup 目录探针 `is_dir()` 两态；`_digest` 的 `is_file()==False` 仍返 `ABSENT`（普通目录/特殊文件与「不存在」共用值）；`_scope_match` 对 pattern 仍 `.strip()`。
5. D 段：静态计数 104/43/147 与文档一致；5 条桩化用例可对应；L85 五坑均能在代码/测试里找到事实；但 §12.1 #3 旧行仍原样说 `_fresh_paths` 支持 `SRC ` 前缀、§12.3「挂载点在真实层」旧句仍在、§13.5 未记上述五项漏记风险。

### 14.2 可直改九条的落地位置

| # | 审计要求 | r10 落地 | 证据位置（符号名 / 用例） |
|---|---|---|---|
| 1 | XY 两位都要认 R/C | `if any(ch in ('R','C') for ch in code[:2]) and i < len(parts)`；注释写明 ` R`/` C` 场景与「截前三字符」的后果 | `codex_channel._status_rows`；用例 `test_status_rows_handles_worktree_side_rename` |
| 2 | 基线消失路径进 fresh | `fresh |= {p for p in b_paths if p not in a_paths}`；basis 文案改「逐路径内容指纹差分 + 消失路径回补」 | `codex_channel.fresh_changes`；用例 `test_fresh_changes_counts_vanished_baseline_path` |
| 3 | 锁键归一化 | `safe = re.sub(..., _norm_ref(target) or 'target')`；注释写明 `main` vs `refs/heads/main` 两把锁 | `_MergeLock.__init__`；用例 `test_merge_lock_key_normalizes_ref_prefix` |
| 4 | `pre_anc` 用冻结 SHA | `rc_pre` 改查 `src_before`（`src_before` 为空时不发命令、直接走取证失败出口） | `merge()`；三条 merge 负向用例的桩补 `rev-parse ^{tree}` |
| 5 | 前态 tree 取不到要在 `wt_merge` 前停 | 新增 `if not target_tree_before:` → `failed.append`（「合并前取证失败：target 前态 tree 取不到（…），未执行合并，fail-closed」）+ `break`，位置在 `pre_anc = (rc_pre == 0)` 之前、`wt_merge()` 之前 | `merge()`；用例 `test_merge_does_not_run_wt_when_target_tree_unavailable`（断言 `wt_merge` 调用计数为 0） |
| 6 | append 回 `with` | `if not progressed or not proven:` 起到 `'target_sha_after'` 整段（含 `failed.append` / `break` / `merged.append`）整体缩进 4 格，进 `with _MergeLock(...)` | `merge()`（行号随 r10 漂移，按符号定位） |
| 7 | 真第二进程锁 + 严格类型反例 | 新增 `test_merge_lock_is_exclusive_across_processes`（子进程持锁、父进程抢即 `SystemExit`）；新增参数化 `test_merge_rejects_loose_json_types`，覆盖 `dry_run ∈ {None, 0, 1, "true"}`、`mergeable ∈ {0, 1, "true"}`；原 `test_merge_lock_is_exclusive` 保留为同进程重入用例 | `tests/test_gorch_batch_orchestrator.py` r10 段 |
| 8 | cleanup 三态 | 新增 `_path_state(p)`：`FileNotFoundError → absent`、其他 `OSError → unknown`、`S_ISDIR → exists`；cleanup 三处（入口 / 超时分支 / rc=0 分支）改用 `dir_state`，`unknown` 不再参与「已清理」豁免，reason 文案改「目录状态=」，两处 `evidence` 增 `dir_state` | `batch_orchestrator._path_state` / `cleanup()`；两条既有 cleanup 用例断言改「目录状态=exists」 |
| 9 | 文档与看板更正 | 本节 + §12.1 #3 / §12.3 作废标注（行内直标）+ §13.1 两处提前声明的更正 + §13.5 补记五项 + L86 + 看板 r9/r10 条目 | 本报告 / `docs/references/lessons-log.md` / `docs/tracker/北极星上线任务清单.html` |

### 14.3 需口径七条（第九轮新增，仍未拍板）

1. **严格因果证明**的最终形态（独占锁之外，是否要求 reflog 与产出 commit 精确对应 / 可绑定 invocation 的事务回执）。
2. `content_changed` 是否要排除「history-only 合入」（例如只把 target 指向一个已有 tree 的旧 commit）。
3. 调用前 source 已是祖先、且 source 被 wt 删掉时，接受哪一级证据（`tree` / `wt_receipt`）。
4. manifest 的**来源真实性**（谁能签、怎么证明是编排方签的）。
5. manifest 的 `target` 是否必须绑定一次独立 `merge`。
6. fallback 路径的历史扫描是否直接删除（当前 CLI 只强制 `--run-dir`，无则 rc=2，但兜底 glob 仍在）。
7. 前后采样的并发窗口（第三方在同窗口写同一 worktree）能否接受。

连同第七轮 3 条 + 第八轮 2 条（严格因果、预已祖先 squash 语义、manifest 签发边界、manifest target 绑定、wt_receipt 兜底），**合计 12 条口径仍无 Owner 书面批准**。r10 只改实现，不改这些语义。

> **r11 去重更正（第十轮审计 D 段）**：上面「12 条」是**重复计数**。本节第 1/3/4/5 条与上一段列的 5 条是同一语义（严格因果、预已祖先 squash、manifest 来源、manifest target、wt_receipt），按唯一语义本节只有 **3 条新增**（history-only 合入、fallback 历史扫描、前后采样窗口），本节 + 前两轮合计应为 **5 + 3 = 8 类**。第十轮审计再提 10 条，其中 6 条属这 8 类的重述，**真新增 4 条**（预已祖先且 source 被删时接受哪级证据、write scope 是否也限操作类型、授权 pattern 边缘空格语义、永久 `unknown` 的运维出口）。按唯一语义合计 **12 类**（构成 8 + 4，不是 5 + 7），每条仍**无 Owner 书面批准**。

> **r12 更正（第十一轮审计 D.3）**：本段的「8 + 4」自身也重复——第十轮那 4 条里的第 ⑨ 条「调用前已祖先且 source 被删时接受哪级证据」与「前两轮 5 类」中的「预已祖先 squash 语义」是同一类；按本段自己的文本，唯一语义应为 **8 + 3 = 11 类**，不是 12。除非能点名真正独立的第 4 类，否则计数以 **11** 为准。**去重的只是归类，不是待裁条目数**：待裁清单仍逐条列出，「需口径」7 条见 §16.5。

### 14.4 测试与静态计数

- 合跑：**159 passed / 49.58s**（r9 为 147 passed / 47.90s）。
- 命令：`tools\venv-openjarvis\Scripts\python.exe -m pytest tests/test_gorch_batch_orchestrator.py tests/test_gorch_codex_channel.py -o addopts= -p no:cacheprovider -q`（cwd 仓库根、PATH 前置 Git）。
- 静态计数（`^def test_` 实测）：batch 104 → **108**、channel 43 → **45**；含 1 个 `@pytest.mark.parametrize`（展开 7 例），执行条目 147 → **159**（+12）。
- r10 新增 6 条函数（batch 4 / channel 2）：
  - batch：`test_merge_lock_is_exclusive_across_processes`、`test_merge_lock_key_normalizes_ref_prefix`、`test_merge_does_not_run_wt_when_target_tree_unavailable`、`test_merge_rejects_loose_json_types`（参数化 7 例）
  - channel：`test_status_rows_handles_worktree_side_rename`、`test_fresh_changes_counts_vanished_baseline_path`
- 因实现收紧而**改断言/改桩**的既有用例 5 条：`test_cleanup_reports_failure_without_force`、`test_cleanup_timeout_with_residual_worktree_still_fails` 的 `目录还在=True` → `目录状态=exists`；`test_merge_rejects_preexisting_ancestor_without_source_move`、`test_merge_rejects_unrelated_target_advance`、`test_merge_rejects_when_git_shows_no_merge` 的 `_git_out` 桩补 `rev-parse → tree`（此前恒 `(1,'')`，新守卫会先于原判据触发）。断言被削弱的 `test_find_done_tasks_only_reads_this_invocation` 钉回 `result == 'blocked'` + `reason == '本轮失败'` 两处精确值。
- **桩化边界（如实标注）**：跨进程锁打真实层（真子进程 + 真 `msvcrt` 文件锁）；锁键归一打真实层（真锁文件路径 + 真争锁）；`_path_state` 打真实层（真 `os.stat`）；其余 merge 负向用例仍桩 `_git_out` / `_ref_sha` / `wt_merge`（不桩化的代价是每次跑真 `wt`，与 r9 同一边界）。

### 14.5 对 §13 两处「提前声明」的更正

- **§13.1 N8「`merged.append` 全在同一 with 内」**：r9 提交时**不成立**（`failed.append` / `merged.append` 在 1267/1287，已在 `with` 退栈之后）。r10 把整段移进 `with`，该声明**自 r10 起为真**。
- **§13.1 N12「`test_merge_lock_is_exclusive` 真起第二进程争锁」**：r9 提交时**不成立**（同进程第二个 `_MergeLock` 实例）。r10 另增真跨进程用例，原用例保留。
- 这两处都是「声明跑在实现前面」，第九轮审计判为假声明。r10 的处理是**把实现补上**，而不是把声明删掉。

### 14.6 残余风险（r10 后仍存在）

1. 14.3 的 7 条（连同前两轮 5 条）口径未拍板。
2. 外部 git / 其他工具不受锁约束；`wt merge --format json` 仍无能绑定 invocation 的事务字段 → 因果证明上限未变。
3. `_scope_match` 对授权 pattern 仍 `.strip()`（审计口径③残余）；`_digest` 的 `is_file()==False` 仍返回 `ABSENT`（普通目录 / 特殊文件与「不存在」共用值）——两项均在本次可直改清单之外，未改。
4. fallback 的 invocation 等值仍是条件式（`expect_invocation` 为空时退化为「只验非空」）；CLI 已强制 `merge --invocation`，但直接 `import merge()` 可绕。
5. 真实批次未重跑 `run_all`（旧卡会被「无新增」判 blocked，需换任务名）；冲突形态全链仍只有单测；`done_no_merge` 三分组未落；八跳第 4 跳仍未进 `run_all`。

> **r11 补记（第十轮审计 D 段：本节 r10 漏记三项）**：① 锁键 `re.sub(r'[^0-9A-Za-z._-]','_')` 会把 `feature/a` 与 `feature_a` 压成同一文件名，两个不同 target 互相阻塞——**假互斥**（可用性误杀，非安全 fail-open）；② `_path_state` 用 `S_ISDIR` 判 absent，把**存在的普通文件**记成不存在，与 branch absent + 登记 false 组合即「路径还在却记已清理」的 cleanup fail-open；③ 永久 `unknown` 只有 fail-closed、没有运维出口（不会自动转 removed，也没有人工 override/隔离路径）。其中 ①② 已在 r11 修（见 §15.2），③ 仍属待拍板口径（见 §15.5）。

### 14.7 结论去向

- r10 交**第十轮 Codex 独立只读审计**（第②环），判据入口：14.1 的三高反例与点名项、14.2 九条落地、14.4 的覆盖与桩化标注、14.5 的两处更正、14.6 的残余声明。
- 若第十轮仍判「不一致」，继续 r11；用户指令为长任务模式，直到审计判「一致」才停。

## 十五、r11 实现闭环（第十轮审计「不一致」→ 可直改七条）

### 15.1 第十轮审计判定

第十轮 Codex 独立只读审计（`gpt-5.6-sol`、`high`、read-only、917.6s / 46,623B / 326 行）判**不一致**：

1. r9 三条核心高风险反例（XY R/C 两位、消失路径回补、锁键短名/全名统一）判**已修**。
2. 但出现**一条新的 cleanup fail-open**：`_path_state` 把存在的普通文件判成 `absent`（`os.stat` 成功、`S_ISDIR=False` 时返回 `'absent'`）。worktree 路径被普通文件占据 + branch absent + registration false 时，入口豁免把它记成 removed。
3. 同类问题在 channel 侧：`_digest` 对存在的**非普通文件**仍返 `'ABSENT'`——目录、symlink、submodule 与「不存在」共用一个值。
   （**r12 更正**：这句对 symlink 说得**过宽**。r10/r11 的 `is_file()` / `p.stat()` 都**跟随** symlink，所以「link 指向一个普通文件」时实际是**哈希目标内容**，并非一律 `ABSENT`；`ABSENT` 只成立于 dangling link、目录、特殊文件。r12 已改为 `os.lstat` + `LINK:<sha256(readlink 文本)>`，见 §16.2 第 2 条。）
4. **锁键碰撞误杀**：`re.sub` 把 `feature/a` 与 `feature_a` 映射成同一个锁文件，两个不同 target 的 gorch 互相阻塞；`_norm_ref` 只剥精确小写 `refs/heads/`。
5. **cleanup evidence 三种 schema**：`dir_state` 未取代 `dir_exists`（两者并存），rc=0 成功移除条目**根本没有 evidence**。
6. **merge 取证失败与冲突混档**：前态 tree 失败的 `failed` 被 `run_all` 一律写进 `kept_for_conflict`，note 写「可能为冲突」，返回结构无 `retryable`/`kind`。
7. 测试/证据/文档不一致：三条 proof 负向用例是**多原因失败**（前后同 tree 本身也能让用例变红）；B4 只测普通 paths、未构造 vanished ignored；§14.3 重复计数（按唯一语义 8 类而非 12 条）；§14.6 漏记三项；看板 r10 仍写「进行中」且缺提交号与 tag；r8 行仍称 `run_dir`「必填且绝对路径相等」。

E 段给出**可直改 7 条 + 需口径 10 条**。本轮只做可直改 7 条，口径不改语义。

### 15.2 可直改七条的落地位置

| # | 审计要求（严重度） | r11 落地 | 证据位置（符号/用例） |
|---|---|---|---|
| 1 | 高：`_path_state` 非目录不得返 absent | 新增第四态 `wrong_type`：`FileNotFoundError → absent`、其他 `OSError → unknown`、`S_ISDIR → exists`、其余 → `wrong_type`；cleanup 三处消费点都不把 `wrong_type` 当已清理（入口 `if dir_state != 'exists'` → 走 skipped；超时/rc=0 分支 `wt_gone = (dir_state=='absent')`） | `_path_state`；用例 `test_path_state_distinguishes_regular_file_and_unknown`、`test_cleanup_rejects_regular_file_at_worktree_path` |
| 2 | 高：`_digest` 存在非普通文件不得等于 ABSENT | `stat` 结果直接判类型：非 `S_ISREG` 返 `'TYPE:dir' / 'TYPE:link' / 'TYPE:other'`（可比较，类型变则摘要变）；仍只有 `FileNotFoundError` 返 `ABSENT`、读失败返 `None` | `codex_channel._digest`；用例 `test_digest_reports_non_regular_type` |
| 3 | 中：锁键改无碰撞键 | 锁文件名 = 可读前缀（`re.sub` 结果截 40 字符）+ `sha256(_norm_ref(target))[:16]`；归一后相同 → 同锁，不同 → 不同锁 | `_MergeLock.__init__`；用例 `test_merge_lock_keys_do_not_collide_for_distinct_refs`、`test_merge_lock_distinct_targets_do_not_block`（原 `test_merge_lock_key_normalizes_ref_prefix` 继续验 `main` ≡ `refs/heads/main`） |
| 4 | 中：统一 cleanup evidence schema | 三个 removed 出口（`pre_absent` / `rc_zero_not_required` / `rc_zero_confirmed`）写**同一组 6 key**：`dir_state / branch_state / worktree_registered / wt_returncode / exemption / readback`；删除 `dir_exists`；rc=0 成功条目补 `evidence` | `cleanup()`；用例 `test_cleanup_evidence_schema_is_uniform`（三出口 key 集相等）+ 两条既有 evidence 用例改断言 `dir_state` 与 key 集 |
| 5 | 中：加强测试覆盖 | 新增 vanished **ignored**、已暂存 `R `/`C ` rename、`_path_state` 普通文件/unknown、锁键碰撞/异键不互斥、三出口 schema、run_all 取证失败分档；两条 proof 负向用例给**前后不同 tree**，把失败原因隔离到用例名所称的那一个判据 | 见 15.3 清单 |
| 6 | 中：merge `failed` 增 `kind`，取证失败不入 `kept_for_conflict` | 五处 `failed.append` 加 `kind`：前态取证失败= `evidence_failure`、`wt merge` 非零= `merge_conflict`、回执缺 branch/target 与未证明合入= `proof_failure`；`run_all` 拆 `kept_for_conflict` / `kept_for_evidence` 两个列表，note 写失败类别并声明「取证失败未执行合并、可直接重试」 | `merge()` / `run_all()`；用例 `test_run_all_keeps_evidence_failure_out_of_conflict`、`test_merge_does_not_run_wt_when_target_tree_unavailable` 补 `kind` 断言 |
| 7 | 低：文档与看板 | 本节 + §14.3 去重更正 + §14.6 三项补记 + L87 + 看板 r10 收口（提交号/tag）+ r11 条目 + r8 行 `run_dir` 表述修正 | 本报告 / `lessons-log.md` / `北极星上线任务清单.html` |

> **r12 更正（第十一轮审计 D 段对本节表述的点名）**：
> 1. **第 2 条「`TYPE:link` 覆盖 symlink」表述过宽**：r11 的 `p.stat()` 跟随 symlink，live link 实际按**目标内容**哈希，只有 dangling link 才落 `TYPE:link`——三类 link 语义并不统一。r12 改 lstat + `LINK:<sha256(readlink 文本)>`（§16.2 第 2 条）。
> 2. **第 3 条「归一后相同 → 同锁，不同 → 不同锁」不符合截断哈希的数学性质**：`sha256(...)[:16]` 仍有碰撞可能。正确表述是「归一后相同 → 同一把锁；不同 → 高度可分（64-bit 碰撞概率），**不是**绝对不碰撞」（§16.5 第 2 条把该等级列为待裁口径）。
> 3. **第 6 条「五处 `failed.append` 加 `kind`」字面成立，但不能读成「所有失败已分档」**：r11 仍有 **5 处** `raise SystemExit` 绕开 `failed` 与 `kind`——① target SHA 取不到；② `wt` 回执不可解析；③ 回执非对象；④ 回执 `branch` 与请求不一致；⑤ 回执 `target` 与请求不一致。r12 已把五处全部改为结构化 `failed` + `break`（①→`evidence_failure`，②–⑤→`proof_failure`，见 §16.2 第 3 条）。**r13 更正**：本节原写「三处」，是把②③④⑤折叠成「回执身份不一致」一项，与基线 `0c414494` 的实际行数不符（第十二轮审计 D-3 点名）。
> 4. **第 4 条只统一了 evidence 内层**：`removed` 条目**外层**仍三种形状（`pre_absent` 无 `result/schema_ok`、rc 非零无 `result/schema_ok`、rc=0 无 `raw_tail`），按外层键读的 consumer 会 `KeyError`。r12 已补齐（§16.2 第 6 条）。
> 5. **第 5 条的 R/C 说明无需改**：r11 新增的是 `R `（已暂存 rename），` C `/` R`（工作区侧）是 r10 就有的；原文「新增 vanished ignored / 已暂存 `R ` rename」已区分，无误。

### 15.3 测试与静态计数

- 合跑：**168 passed / 48.12s**（r10 为 159 passed / 49.58s）。
- 命令与 r10 相同：`tools\venv-openjarvis\Scripts\python.exe -m pytest tests/test_gorch_batch_orchestrator.py tests/test_gorch_codex_channel.py -o addopts= -p no:cacheprovider -q`（cwd 仓库根、PATH 前置 Git）。
- 静态计数（`^def test_` 实测）：batch 108 → **114**、channel 45 → **48**；含 1 个 `@pytest.mark.parametrize`（展开 7 例），执行条目 159 → **168**（+9）。
- r11 新增 9 条函数：
  - batch（6）：`test_path_state_distinguishes_regular_file_and_unknown`、`test_cleanup_rejects_regular_file_at_worktree_path`、`test_cleanup_evidence_schema_is_uniform`、`test_merge_lock_keys_do_not_collide_for_distinct_refs`、`test_merge_lock_distinct_targets_do_not_block`、`test_run_all_keeps_evidence_failure_out_of_conflict`
  - channel（3）：`test_digest_reports_non_regular_type`、`test_fresh_changes_counts_vanished_ignored_path`、`test_status_rows_handles_staged_rename_target_first`
- 因实现收紧而改断言/改桩的既有用例 5 条：`test_cleanup_pre_absent_three_way_records_evidence`、`test_cleanup_timeout_exemption_records_evidence`（`dir_exists` → `dir_state` + key 集）；`test_merge_rejects_preexisting_ancestor_without_source_move`、`test_merge_rejects_unrelated_target_advance`（`_git_out` 桩按 rev-parse 实参给前态/后态**不同** tree，隔离 ancestor 条件）；`test_merge_does_not_run_wt_when_target_tree_unavailable` 补 `kind` 断言。
- **桩化边界（如实标注）**：`_path_state` / `_digest` / 锁键都打真实层（真 `os.stat`、真目录与普通文件、真锁文件路径与真争锁）；merge 负向用例仍桩 `_git_out` / `_ref_sha` / `wt_merge`；`run_all` 用例桩 `gate_check` / `provision` / `execute` / `cleanup`，只走真实 `run_all` 分支与 `merge` 入口。

### 15.4 对 §14 的更正

- **§14.2 第 8 条「cleanup 三态」**：r10 交付时是 exists/absent/unknown **三态**，把存在的非目录记 absent——该条**当时就不完整**。r11 改为四态（+`wrong_type`），本报告与看板按四态表述。
- **§14.3 口径重复计数**：已在原处加 r11 更正（唯一语义 8 类，第十轮真新增 4 类，合计 12 类）。
- **§14.6 漏记三项**：已在原处补记（锁键误杀、普通文件记 absent、unknown 无运维出口）。

### 15.5 残余风险（r11 后仍存在）

1. **口径 12 类**（唯一语义，见 §14.3 更正）全部无 Owner 书面批准——本轮只改实现，不改语义。
2. **外部 git / 其他工具不受锁约束**；`wt merge --format json` 仍无能绑定 invocation 的事务字段 → 「本次造成」的因果上限未变。
3. `_digest` 对目录只记 `'TYPE:dir'`：目录**内部**文件增删在指纹里仍不可见（`status -uall` 通常列到文件级，但若 Git 折叠成目录条目，就只剩类型摘要）。这是本条修复引入的**新残余**，如实记；要彻底覆盖需对目录做递归列表摘要，代价与噪声都高，未做。
4. `_scope_match` 对授权 pattern 仍 `.strip()`（口径项，未改）。
5. fallback 的 invocation 等值仍是条件式（`expect_invocation` 为空时退化为「只验非空」）；CLI 已强制 `merge --invocation`，但直接 `import merge()` 可绕。
6. 永久 `unknown` 只有 fail-closed，无自动出口与人工 override（口径项）。
7. 真实批次仍未重跑 `run_all`；冲突形态全链只有单测；`done_no_merge` 三分组未落；八跳第 4 跳仍未进 `run_all`。

### 15.6 结论去向

- r11 交**第十一轮 Codex 独立只读审计**（第②环），判据入口：15.1 的七条可直改、15.2 落地表、15.3 计数与桩化边界、15.4 三处更正、15.5 残余声明。
- 若第十一轮仍判「不一致」，继续 r12；用户指令为长任务模式，直到审计判「一致」才停。


## 十六、r12 实现闭环（第十一轮审计「不一致」→ 可直改八条）

### 16.1 第十一轮审计判定

第十一轮 Codex 独立只读审计（`gpt-5.6-sol`、`high`、`--sandbox read-only`、`1014.6s / 44,735B / 393 行 / 209,792 tokens`）判**不一致**。身份核验全对（`HEAD=0c414494`、tag deref 同 SHA、`0c414494^=d2640d95`、`d2640d95^=09903f1c`、两提交 `+283/−27` 与 `+77/−2` 吻合），但审计明确声明**未跑 pytest / py_compile / python / wt**：`168 passed` 只按历史声明处理，远端 push/tag 未验证。

A 段 16 项：A⑤/A⑦/A⑧/A⑩ 仍成立；A⑪ **部分成立**（普通文件已是 `wrong_type`，但 dangling symlink 经 `os.stat` 抛 `FileNotFoundError` 落 `absent`）；口径①②③ 仍成立；B1–B3、B5、B6 仍成立；**B4 已修**；**B7 已修但只限 evidence 内层**（`removed` 外层仍三形状）；B8 仍成立。

E 段给出**可直改 8 条 + 需口径 7 条**。本轮只做可直改 8 条，口径一条不动。

### 16.2 可直改八条的落地位置

| # | 审计要求（严重度） | r12 落地 | 证据位置（符号/用例） |
|---|---|---|---|
| 1 | 高：cleanup 对 symlink / dangling fail-open | `_path_state` 由 `os.stat` 改 `os.lstat`（不跟随）：`S_ISDIR` 才 `exists`，**所有 symlink 形态**（link→file / link→dir / dangling）一律落 `wrong_type`；`FileNotFoundError → absent`、其它 `OSError → unknown` 保持不变。**边界（r13 更正）**：junction 的 `lstat` 仍报目录（`islnk=False / isdir=True / 0o40777`），因此落 `exists` 走正常 `wt remove` —— 不是 `wrong_type`，详见 §16.3 的实测记录 | `batch_orchestrator._path_state`（**以 `def _path_state(` 函数名锚定**，r14 实测 `:1395`；此前两轮写的行号均已漂移，不再引用，见 L90）；用例 `test_path_state_distinguishes_regular_file_and_unknown`（补 link 段）、`test_cleanup_treats_any_symlink_as_wrong_type`（r13 加 `os.stat` dangling 桩，见 §17.4） |
| 2 | 高：`_digest` 的 symlink 语义 | 先 `os.lstat`；`S_ISLNK → 'LINK:' + sha256(readlink 文本)`（dangling 不再 `ABSENT`，retarget 会变摘要）；其余非 `S_ISREG` 折成 `TYPE:dir` / `TYPE:other`（去掉 `link` 分支，link 不再被 `TYPE:` 折叠） | `codex_channel._digest`；用例 `test_digest_symlink_uses_link_summary_not_absent`、`test_digest_link_retarget_changes_summary`、`test_digest_reports_non_regular_type`（普通文件改 `^[0-9a-f]{64}$` 断言） |
| 3 | 高：merge 的 `SystemExit` 绕开 `kind` | 5 处 `raise SystemExit` 全改结构化 `failed.append(...)` + `break`：target SHA 取不到 → `evidence_failure`；`wt` 回执不可解析 / 非对象 / `branch` 不一致 / `target` 不一致 → `proof_failure`。编程错误（`AttributeError` 等）仍照旧抛出，不吞成业务失败 | `merge()`（原 1128 / 1207 / 1221 / 1238 / 1241 五处）；用例 `test_merge_fails_closed_on_unparsable_json`（改断言 `failed`）、`test_merge_receipt_identity_mismatch_is_proof_failure`、`test_merge_records_not_attempted_after_failure` |
| 4 | 中：`proof_failure` / 未知 kind 误归冲突 | `run_all` 的 `failed` 分档由二分改**四分流** `buckets = {merge_conflict, evidence_failure, proof_failure, unknown}`，未知 kind 单列 `kept_for_unknown` 并 fail-closed（既不并进 conflict，也不当可继续） | `run_all()`；用例 `test_run_all_keeps_proof_failure_out_of_conflict`、`test_run_all_keeps_unknown_kind_separate` |
| 5 | 中：首失败后任务无归属 | `merge(..., trace=None)` 可选回传 `attempted` / `not_attempted`（保持既有四元返回不变，CLI 与旧测试无需改）；`run_all` 写进 `steps['merge']['attempted']` 与 `not_attempted_after_failure`，并带进 `merge` 段 note | `merge()` / `run_all()`；用例 `test_merge_records_not_attempted_after_failure`（三任务、首条 `evidence_failure` → `attempted=['1']`、`not_attempted=['2','3']`） |
| 6 | 中：`removed` **外层** key 仍分裂 | 三个 removed 出口外层固定同一组 10 key：`task / branch / worktree / branch_outcomes / result / schema_ok / wt_remove_rc / raw_tail / note / evidence`；缺值显式 `None` / 空串（`wt_remove_rc` 可空、`wt_returncode` 仍在 evidence 内且可空） | `cleanup()`；用例 `test_cleanup_evidence_schema_is_uniform`（三出口**外层** key 集相等 + `{result, schema_ok, wt_remove_rc, raw_tail} ⊆ keys`） |
| 7 | 中：status NUL 项缺格式先验 | `_status_rows` 加格式先验：`len(item) < 4 or item[2] != ' '` → 整份 `False`（调用方转 `ERR:status`）；rename/copy 缺源项（`i >= len(parts)` 或末位空串）同样 `False`。**不对裸 source 套状态项语法**（合法文件名可任意开头） | `codex_channel._status_rows`；用例 `test_status_rows_rejects_malformed_item`（`R?path` / 短项 / rename 缺源三种） |
| 8 | 低：文档与看板更正 | 本节 + §14.3 改 11 类 + §15.1 / §15.2 / §15.3 就地更正 + L88 + 看板 r11 收口（`d2640d95` / `0c414494` / tag）+ r12 条目 | 本报告 / `lessons-log.md` / `北极星上线任务清单.html` |

### 16.3 测试与静态计数

- 合跑：**176 passed / 47.21s**（r11 为 168 passed / 48.12s）。
- 命令同 r11：`tools\venv-openjarvis\Scripts\python.exe -m pytest tests/test_gorch_batch_orchestrator.py tests/test_gorch_codex_channel.py -o addopts= -p no:cacheprovider -q`（cwd 仓库根、PATH 前置 Git）。
- 静态计数（`^def test_` 实测）：batch 114 → **119**、channel 48 → **51**；含 1 个 `@pytest.mark.parametrize`（展开 7 例），执行条目 168 → **176**（+8）。
- r12 新增 8 条函数：
  - batch（5）：`test_cleanup_treats_any_symlink_as_wrong_type`、`test_merge_records_not_attempted_after_failure`、`test_run_all_keeps_proof_failure_out_of_conflict`、`test_run_all_keeps_unknown_kind_separate`、`test_merge_receipt_identity_mismatch_is_proof_failure`
  - channel（3）：`test_digest_symlink_uses_link_summary_not_absent`、`test_digest_link_retarget_changes_summary`、`test_status_rows_rejects_malformed_item`
- 因实现收紧而**改桩/改断言**的既有用例 **5 条**（r13 更正：原写 3 条，漏了后两条，第十二轮审计 C/D 段点名）：① `test_path_state_distinguishes_regular_file_and_unknown`（桩点由 `os.stat` 迁到 `os.lstat` 并补 link 段）；② `test_digest_stat_error_is_not_absent`（原桩 `pathlib.Path.stat`，改 `os.lstat` 后该桩不再命中——不改就会变成**假通过**）；③ `test_merge_fails_closed_on_unparsable_json`（`pytest.raises(SystemExit)` → 断言 `failed[0]['kind'] == 'proof_failure'`）；④ `test_cleanup_evidence_schema_is_uniform`（断言从「只查内层」收紧到「外层 10 key 相等」）；⑤ `test_digest_reports_non_regular_type`（断言从固定 `TYPE:link` 改正则式的 64 位十六进制摘要）。
- **桩化边界（如实标注）**：
  - **打真实层**：`_path_state` 的 `os.lstat`（真目录 / 真普通文件 / 真不存在）、`_digest` 的普通文件分支（真文件 + 真 hex 断言）、`_status_rows` 的格式先验（真 `-z` 串）、`run_all` 的四分流与 `cleanup()` 的 key 集（真 `cleanup` 三出口）。
  - **桩化**：全部 symlink 语义（`os.lstat` / `os.readlink` 用桩）。原因**实测**：本机普通权限下 `os.symlink` 大面积失败——file link 报 `FileExistsError [WinError 183]`、dir link 与 dangling 报 `OSError [WinError 87]`，建不出任何 link。用桩覆盖的是「lstat 报 `S_IFLNK` 之后的分支」，**不**覆盖「Windows 建 link 后 lstat 的真实返回值」。
  - **junction 实测（补充事实）**：`New-Item -ItemType Junction` 可成功建，但 junction 的 `os.lstat` 返回 **`islnk=False / isdir=True / mode 0o40777`**（`os.stat` 同样报目录）→ junction 会落 `exists` 并走正常 `wt remove` + 回读，**不会**被记 `absent`，因此不构成本轮修点的 fail-open；但「junction 能否被 `wt remove` 清掉、是否该算残留」未验证，列为 §16.5 第 5 条。
  - merge 负向用例仍桩 `_git_out` / `_ref_sha` / `wt_merge`（与 r10/r11 同一边界，不桩化就要每次跑真 `wt`）。

### 16.4 对 §15 的更正

- **§15.2 第 2 条「`TYPE:link` 覆盖 symlink」**：过宽，已就地更正（live link 走目标内容哈希，只有 dangling 落 `TYPE:link`）。
- **§15.2 第 3 条「不同 → 不同锁」**：不符合截断哈希性质，已就地更正为「高度可分、非绝对不碰撞」。
- **§15.2 第 6 条「五处 append 有 kind」**：不能读成「所有失败已分档」，已就地补记 5 处 `SystemExit`（target SHA / 回执不可解析 / 回执非对象 / branch 不一致 / target 不一致；原文写「三处」是折叠计数，r14 更正）。
- **§15.2 第 4 条「统一 evidence schema」**：只统一了内层，外层三形状，已就地补记。
- **§15.3「既有用例 3 条」**：原句实际列了 5 个函数名，数字写错，已改 **5 条**。
- **§14.3「12 类」**：按本节自身文本应为 **11 类**（8 + 3），已就地更正。

### 16.5 残余风险（r12 后仍存在）

1. **口径 11 类**（唯一语义，见 §14.3 更正）全部无 Owner 书面批准——本轮只改实现，不改语义。
2. **第十一轮「需口径」7 条**同样无批准：① symlink 指纹语义（取证 link 对象 vs 解析目标内容）；② 目录 / submodule 指纹（维持 `TYPE:dir` 靠 `-uall` vs 递归 manifest hash）；③ 锁键碰撞保证等级（接受 64-bit vs 完整 SHA-256）；④ `proof_failure` 现场语义（单列 vs 并入并改名 `kept_for_merge_failure`）；⑤ 第三方 Git 并发窗口；⑥ 永久 `unknown` / `wrong_type` 的运维出口；⑦ fallback invocation 策略。r12 对 ①②③⑥ 都只做了**当前实现内的收口**（`LINK:` 摘要、`TYPE:other`、64-bit 键、`kept_for_unknown` 单列），没有替 Owner 选语义。
3. **symlink 语义的取证边界**：`LINK:<sha256(readlink 文本)>` 只证明「link 对象与其指向文本没变」，**不**证明目标内容没变；目标若在 Git 可见集合内会由自身路径另行取证，若目标在域外则只能靠这条摘要。这是本轮引入的**新残余**，如实记。
4. **`TYPE:other` 仍折叠 FIFO / socket / device**：三者共用一个值，同一路径从 FIFO 换成 socket 摘要不变（属 §16.5 第 2 条口径项，未改）。
5. **junction / reparse 未验证清理**：见 §16.3 实测——落 `exists` 后由 `wt remove` 处理，能否真的删掉、删不掉会不会回读成 `exists` 形成永久 skipped，未用真实批次验证。
6. **`wt_remove_rc` 与 `evidence.wt_returncode` 仍 None/int 混用**：外层统一成 nullable 后，两处语义重叠（一个在 evidence 内、一个在外层），未合并（避免破坏既有 consumer）。
7. **外部 git / 其他工具不受锁约束**；`wt merge --format json` 无 invocation 级事务字段 → 「本次造成」的因果上限未变。
8. **`_scope_match` 的 `.strip()` 与 fallback 条件式 invocation 仍未改**（口径项）。
9. **真实批次仍未重跑 `run_all`**；冲突形态全链只有单测；`done_no_merge` 三分组未落；八跳第 4 跳仍未进 `run_all`。
10. **文档侧仍有历史遗留**：第十轮审计全文（`codex-r10-audit-last.md`，46,623B）尚未入库成 docs 提交；本轮 §16 亦只入本报告，未单独出 `fix-*.md`。

### 16.6 结论去向

- r12 交**第十二轮 Codex 独立只读审计**（第②环），判据入口：16.1 的判定摘要、16.2 八条落地表、16.3 计数与桩化/实测边界、16.4 六处更正、16.5 十条残余。
- 若第十二轮仍判「不一致」，继续 r13；用户指令为长任务模式，直到审计判「一致」才停。

### 17. 第十三轮（r13）：第十二轮审计「不一致」的收口

#### 17.1 判定与身份

第十二轮 Codex 独立只读审计（`rc=0` / 1026.8s / 16,679B / 239 行 / 153,699 tokens）判**不一致**，
命中口径 ①（八条有未真正落地）与 ③（文档与实现矛盾）。身份链全对（HEAD `135d2f56`、
tag deref 同 SHA、`135d2f56^=597d52b2`、`597d52b2^=0c414494`、两段 numstat 与声明一致）。

A 段结论：5 条 ✅（`_digest` / 五处 SystemExit / 四分流 / attempted / 外层 10 key）、
3 条 ⚠️（#1 reparse 文字过宽、#7 非末位空 rename source 反例、#8 文档矛盾）。
故 r13 只做 **E1 四条 + D 段六处文档更正**，口径项一律不动。

#### 17.2 E1 四条落地

| # | 审计条目 | 落地 | 位置 |
|---|---|---|---|
| 1 | 非末位空 rename source 被接受 | 源路径检查由「仅末位空串」改「**任何**空 source 或缺失即整份失败」，删掉 `if src:` 的静默丢弃 | `codex_channel._status_rows`（rename 分支 `if i >= len(parts) or not parts[i]: return False`） |
| 2 | `-z` 输出缺最终 NUL 仍被接受 | 解析前检查：非空输出必须 `endswith('\0')`，否则整份 `False`（截断流不再当完整结果） | `codex_channel._status_rows` 入口 |
| 3 | 空 targets 早退不清 trace | 早退前把 `trace['attempted'] / ['not_attempted']` 归零（调用方复用 dict 时不读陈旧值） | `batch_orchestrator.merge` 的 `if not targets:` 分支 |
| 4 | `run_all` cleanup 外层 key 不统一 | `_stop()` 的 `setdefault` 与「正常完成」分支都补齐 `kept_for_evidence / kept_for_proof / kept_for_unknown`（四档全空） | `batch_orchestrator.run_all`（`_stop` 内置 cleanup 缺省 + 末尾 `steps['cleanup']`） |

#### 17.3 文档六处更正（D 段）

1. §16.2 #1：`全部 symlink/reparse → wrong_type` 收窄为「所有 **symlink** 形态 → wrong_type；
   junction 因 lstat 报目录落 `exists`」。与 §16.3 的实测记录不再自相矛盾。
2. §16.2 #1 的 `_path_state` 位置改为 **函数名锚定**（`def _path_state(`），不再写行号：连续三轮记录的行号与实测都不一致，每次都是在函数之前插代码所致（第十三轮审计 D-2 点名，教训见 L90）。
3. §15.2 第 3 条「r11 仍有三处 `raise SystemExit`」更正为 **5 处**并逐条列出
   （target SHA / 不可解析 / 非对象 / branch 不一致 / target 不一致）。
4. `lessons-log.md` L88 标题「六个坑」更正为「**七个坑**」（正文一直是 1–7 七项）。
5. §16.3「改桩/改断言 3 条既有用例」更正为 **5 条**并补列
   `test_cleanup_evidence_schema_is_uniform` 与 `test_digest_reports_non_regular_type`。
6. 看板 r12 条目：去掉「所有 link/reparse → wrong_type」与同句 junction `exists` 的内部矛盾、
   「3 条既有用例」改 5 条，并补齐 `597d52b2` / `135d2f56` / r12 tag 与「第十二轮审计判不一致 → r13」。

#### 17.4 测试

- 合跑 **182 passed / 47.90s**（r12 为 176 / 47.21s）。静态函数计数 batch **123** + channel **53**；
  其中 1 个 parametrize 展开 7 例，故 `--collect-only` = 129 + 53 = 182。
- 新增 6 条函数（batch 4 / channel 2）：
  `test_merge_target_sha_missing_is_evidence_failure`（①②③④⑤ 五个结构化出口里此前无回归的第 1 个）、
  `test_merge_receipt_not_object_is_proof_failure`（第 3 个）、
  `test_merge_receipt_target_mismatch_is_proof_failure`（第 5 个）、
  `test_merge_empty_targets_resets_trace`（E1-3）、
  `test_status_rows_rejects_empty_rename_source_in_middle`（E1-1 的真实反例串）、
  `test_status_rows_rejects_output_without_trailing_nul`（E1-2，含一条合法对照）。
- 加强 1 条既有用例：`test_cleanup_treats_any_symlink_as_wrong_type` 追加 `os.stat` 桩
  （对 placeholder 抛 `FileNotFoundError`，即 dangling link 走 stat 的真实行为）+ 直接断言
  `_path_state == 'wrong_type'`。这样若实现退回 r11 的 `os.stat`，`absent` 会让 cleanup 记
  `removed`，用例必红 —— 消除审计 C 段指出的「改不改探针都绿」的假通过。
- **桩化边界仍如实保留**：symlink 语义全部桩化（本机 `os.symlink` 三种形态 WinError 183/87 全失败），
  junction 的 `lstat` 实测仍报目录；审计侧（只读沙箱）无临时目录，`pytest` 测试体从未被独立执行，
  182 passed 属本机实测证据、不是审计复现结果。

#### 17.5 残余（r13 后仍存在）

- **E2 需口径 7 条**（`LINK:` 取证范围 / 目录与 submodule 摘要 / 锁键 64-bit 与完整 SHA-256 /
  `proof_failure` 是否单列 / 第三方 Git 并发窗口 / 永久 `unknown·wrong_type` 运维出口 /
  fallback invocation 策略）全无 Owner 书面批准；审计已明确不计入「不一致」。
- 仍未改：`TYPE:other` 折叠 FIFO/socket/device；`wt_remove_rc` 与 evidence 内 `wt_returncode` 语义重叠；
  `_scope_match` 对授权 pattern 仍 `.strip()`；junction 的真实 `wt remove` 行为未验收；
  `run_all` 未用真实批次复跑；八跳第 4 跳只有单测；`main`（`d1e51eb3`）未与工作分支合流。
- 第十二轮审计仍**未执行** `pytest` 测试体 / `py_compile` / `wt` / 真实 symlink 与 junction —
  独立复跑能力受只读沙箱限制，这一点不随轮次改善。

#### 17.6 结论去向

r13 已把第十二轮审计的 E1 四条与 D 段六处全部收口，测试自测 182/47.90s。
按四段式流程，下一步是**第十三轮 Codex 独立只读审计**（第②环），
判定口径仍为「8 条是否落地 + 有无新 fail-open + 文档与实现是否一致」，口径项不作阻断理由。

### 18. 第十四轮（r14）：第十三轮审计「不一致」的收口

第十三轮审计（`rc=0` / 718.3s / 15,304B / 176 行 / 154,999 tokens）判**不一致**，
命中口径 ①③，未命中 ②④：

- **①**：D-2 未真正落地——`_path_state` 在 r13 之后又因插行漂到 `:1395`，
  报告与看板仍写旧行号（与实测差 6 行）。
- **③**：同一报告一处写「5 处」而另一处仍写「三处」（折叠计数），全文不闭合；
  另 E1-4 缺直接回归断言（撤掉 `_stop` / 正常完成分支的新增键，现有断言仍可能全绿）。

r14 四项（均为文档与测试，不动实现）：

| # | 条目 | 落地 |
|---|---|---|
| 1 | 行号漂移 | 报告 §16.2 #1 与 §17.3、看板 r13 行全部改为 **函数名锚定**（`def _path_state(`，r14 实测 `:1395`），不再写会漂的行号 |
| 2 | 另一处的「三处」 | 改为 **5 处**并逐条列出，与该节首处、§16.2 #3 统一 |
| 3 | E1-4 回归 | `test_run_all_without_ready_has_merge_key` 加 **cleanup 六键同构**断言（覆盖 `_stop` 的 `setdefault`）；新增 `test_run_all_normal_completion_cleanup_has_all_keepers` 覆盖**正常完成分支**（`stopped_at=done`，四档 `kept_for_*` 全空、六键齐全）；合跑 **183 passed / 49.24s** |
| 4 | 验证债务 | 真实 junction `wt remove` / 真实批次 `run_all` 仍属未验收项，保留在 §17.5 与 §18.1，不作为本轮改动 |

#### 18.1 仍未覆盖（与 §17.5 同源，逐轮不变）

审计方（只读沙箱）无法复跑全部测试体（无可写临时目录），之前只做了 `--collect-only`
（r13 时 batch 129 + channel 53 = 182）与新增 channel 两条的独立执行（2 passed / 0.03s）；
`py_compile`、真实 `wt`、真实 symlink/junction、真实批次 `run_all` 均未执行。
本机 r14 实测 **183 passed / 49.24s**（batch 124 + channel 53 def，parametrize 展开 7 例 → collect 130 + 53 = 183），属实施侧证据、不是审计复现结果。

### 19. 第十四轮 Codex 独立只读审计：**一致**

`rc=0` / 631.0s / 11,366B / 128 行（全文 `Temp\codex-r14-audit-last.md`）。
身份核验 8 项全对（分支、HEAD `f80f0f11`、tag 解引用同 SHA、tag type `tag`、
`f80f0f11^=53d072c0`、`53d072c0^=21d7f954`、两段 numstat 与声明一致）。

| 段 | 内容 | 判定 |
|---|---|---|
| A | 三条声明逐条落地（函数名锚定 / 五处统一 / 六键同构） | 3/3 ✅ |
| B | 新增风险（`CLEANUP_KEYS` 是否自证式假绿、桩是否伪造不可达状态） | 4 条全部排除 |
| C | 测试覆盖真实性（真实 `run_all` 控制层 + 撤键敏感） | 通过，1 个非阻断缺口 |
| D | 文档/看板一致性（上一轮点名三条闭合 + 无新增矛盾） | ✅ |
| E1 | 可直改 4 条 | 不阻断 |
| E2 | 需口径 7 条 | 原样保留，不计入判定 |

审计方用只读内存探针**实际跑了真实 `run_all` 控制流**（这是前几轮没能做到的）：
无 ready 路径 `stopped_at='gate'`、正常完成路径 `stopped_at='done'`，两处 cleanup 六键齐全且全空；
并**分别撤掉 `kept_for_evidence` / `kept_for_proof` / `kept_for_unknown`** 后，
`set(cleanup) == CLEANUP_KEYS` 均变 `False` —— 即 r13 的补键一旦回退，r14 断言必红。
新鲜 `--collect-only` 亦实测 **183 collected**，与报告/看板一致。

#### 19.1 审计留下的非阻断缺口（E1）

1. **未闭合保留分支缺直接回归**（`real_stale or leftover` 那一路，`batch_orchestrator.py:1717`
   区段）：目前只靠 AST + 代码审查保证六键同构，没有像 `_stop` / 正常完成那样做集合相等断言。
2. 正常完成用例里的 `find_done_tasks` 桩是**冗余桩**（`write_run` 生成的真实形状本就能通过真实
   consumer 校验），可去掉以收窄桩面。
3. `183 passed / 49.24s` 仍是实施侧回执，缺可在可写环境复跑的新鲜回执。
4. 真实 junction `wt remove`、真实批次 `run_all` 属既存验证债务。

以上四条**均不阻断**「一致」判定，登记为下一轮（若继续）的输入。

## 20. r15：E1 四项闭合 + 七条口径交 Codex 定稿

> 起点 `3d08ca7c`（r14 审计判「一致」）。用户要求「未闭合项继续做完、七条口径按最优方案推进，
> 拿不准就把选择权交给 Codex」，本节即该轮的执行记录。

### 20.1 测试层（E1-1 / E1-2）

| 项 | 动作 | 结果 |
|---|---|---|
| E1-1 未闭合保留分支 | 新增 `test_run_all_unclosed_leftover_keeps_all_keepers`：`find_done_tasks` 返回空 → `leftover=['1']` → 走 `real_stale or leftover` 分支 | `set(cleanup) == CLEANUP_KEYS` 成立；**并断言未闭合时 `cleanup` 从未被调用**（`cleaned == []`），现场必须留证据 |
| E1-2 冗余桩 | 删除正常完成用例里的 `find_done_tasks` 桩 | `write_run` 的真实形状（`run_dir` 绝对路径 / `invocation` / `mergeable=True` / `dry_run=False`）直接过真实 consumer，用例仍绿 |

**撤键即红（实测，非推断）**：临时把未闭合分支的 `kept_for_evidence` / `kept_for_proof` /
`kept_for_unknown` 三键删掉后跑该用例 —— `1 failed`（`set(cleanup)` 少了三键）；从备份恢复后
`1 passed`，`git diff --stat` 对 `batch_orchestrator.py` 为空。至此 `run_all` 的**四个** cleanup
构造点全部有集合相等断言。

### 20.2 新鲜回执（E1-3）

- 定向三例：`3 passed, 1.57s`（gate 早退 / 正常完成 / 未闭合保留）
- 全量：**184 passed / 61.19s**（r14 183 / 49.24s；+1 为新增用例，耗时升高是本机负载）

### 20.3 真实 junction `wt remove`（E1-4 前半）

证据：`docs/reports/evidence/gorch-r15-junction-20261109/README.md`。三条实测结论：

1. `wt remove -f` 在 junction 上是**删链接不删目标**：junction 被删，目标目录 `.git` 与
   `sentinel.txt` 完好；
2. 回执里的 `▲ Discarding uncommitted changes (--force): ?? sentinel.txt` 是**误报**——
   它跟随 junction 把目标里的文件算成"被丢弃"，实际只删了链接。任何把该字段当「已丢数据」的
   取证都会读错，只能以「删除后目录是否存在」为事实源；
3. `_path_state` 对 junction 永远返回 `exists`（`os.lstat` 报 `islnk False / isdir True / 0o40777`），
   **永不落 `wrong_type`**——这正是 E2 口径 ⑥ 需要只读出口的直接依据。

### 20.4 七条口径（E2）：由 Codex 复核定稿

裁决书：`docs/decisions/pd-20261109-gorch-e2-七条口径裁决.md`（含 §9 复核原文摘要）。
Codex 复核（17,177B / 103 行）结论：**「足以作为规范口径」**，同时指出工程侧草案 **4 处事实错误**：

| # | 草案 | 实际 |
|---|---|---|
| ① | `_path_digest` | 函数名是 `_digest(workdir, rel)` |
| ④ | 「三档 keeper」 | kind 三值，但 keeper 是**四个桶**（conflict/evidence/proof/unknown） |
| ⑤ | 「B = 合并前全树 clean 门」 | 不存在 clean-tree 门；前后双采样**已存在**于 `_MergeLock` 内 |
| ⑦ | 「glob + mtime 兜底」 | 只剩 glob，mtime 授权已删（改为严格 UTC `started_at` 取最新） |

最终口径（摘要）：① 只证明 link 对象与指向文本（域外目标**明确不在**证明范围）；② 目录用
**稳定排序 + 长度分隔**的条目名集合哈希，**禁止跟随 reparse/junction**，submodule 记 gitlink OID +
已检出 HEAD；③ 128 bit + **迁移期双锁**（旧 16-hex 先、新 32-hex 后，失败释放）；④ 维持三 kind
四桶；⑤ 双采样只算**观察性证明**，要硬因果须 `update-ref` 的 expected-old CAS；⑥ 新增**只读**
`doctor`，不自动删；⑦ 删除非显式 glob 分支，统一 `run-dir + invocation`。

### 20.5 本节未完成项（如实登记）

- **真实批次 `run_all`**（E1-4 后半）未跑成：`git clone --depth 1 --single-branch` 在本仓
  （30 万+ 未跟踪文件）上 5 分钟未完成且 `HEAD` 损坏（`fatal: your current branch appears to be
  broken`）；在主仓直接跑会向已推送分支写入探针提交。下一步改用 `git worktree add` 作载体
  （共享 objects，秒级建立，且分支独立）。
- 七条口径的**实现**尚未开始，按 §3 顺序（⑤ → ⑦ → ③ → ② → ⑥ → ④ → ①）排下一轮。

## 21. r15 第二轮：E2 七条口径全部落代码（⑤⑦③②⑥④①）

> 起点 `6e434119`（E1 四项 + 裁决书已推）。本节收口 §20.5 的「实现尚未开始」。
> 口径依据：`docs/decisions/pd-20261109-gorch-e2-七条口径裁决.md` §2 与 Codex 复核原文
> （`Temp\codex-r15-ruling-last.md`，17,177B / 103 行）。**全程未回抛用户拍板**。

### 21.1 逐项落地形态

| 项 | 实现 | 关键取舍 |
|---|---|---|
| ⑤ 第三方并发 | 新增 `_ref_update_from(ref, new_sha)`：**事后**读 target reflog，取「把 ref 推到 `new_sha` 那一跳」所绑定的旧值（要求 selector 与行位置一致、下一跳 +1；缺失 / 跳号 / 中间行不可解析 → `unknown`），与锁内基线 `target_sha` 比对；相等记 `causal='reflog-consistent'`，不等即 `proof_failure`；不可读 → `causal='observational'` | 双采样降级为**异常检测**；**不加** clean-tree 门（Codex ⑤ 明确否决）；不写 temp ref（避免崩溃残留）——但**这不等于原子 CAS**，回读不绑定写者，见 §21.2 |
| ⑦ fallback invocation | `find_done_tasks` 删非显式 glob 分支 −108 行；`run_dirs is None` / 缺 `expect_invocation` 双守卫 fail-closed；`merge` 同拒 | 旧签名单测一次性迁移（19 红 → 全绿），非逻辑 bug |
| ③ 锁键 | `_MergeLock` 重写：`sha256(norm_target)[:32]` 为主键、`[:16]` 保留旧键；迁移期双锁（先旧后新） | 单把未持有的旧锁无约束力；真正危险是**新旧各持一把同时放行** |
| ② 目录/子仓 | `_dir_digest`：`scandir` 直接条目名 + 长度分隔哈希、不递归；目录内 reparse 只记 `R`；**路径自身是 reparse 时** `_digest` 返 `REPARSE:dir`、不 `scandir`；`worktree_fingerprint` 识 gitlink `160000` | junction 的危害不是「SHA 随机」而是把**可变域外目标**纳入采样；只挡子条目会漏掉"传进来的就是链接" |
| ⑥ doctor | 只读 `doctor(batch_dir)` + 子命令，输出四态/三态/登记/run 记录/三条只读复核命令 | 卡片状态必须 `is_file()`——`_path_state` 对文件一律 `wrong_type`（实测红一次后改） |
| ④ 三 kind / 四桶 | `MERGE_FAILURE_KINDS` / `CLEANUP_UNCLOSED_BUCKETS` 单源常量 + `_CLEANUP_KEY_FOR`（bucket→`kept_for_*` 唯一映射）+ `cleanup_schema()` 唯一构造函数，`run_all` 四处构造点全部改调 helper | AST 契约：`run_all` 内禁手写 `kept_for_*`、helper ≥4 处调用、未知桶 KeyError——旧契约只看常量值，挡不住键名漂移 |
| ① LINK 边界 | 补「指向文本不变、目标内容变」用例，docstring 明写**预期边界** | 域外目标仍属 §16 残余，不许宣称「已覆盖」 |

### 21.2 ⑤ 为什么本轮**没有**做原子 CAS（差异清单）

裁决原文是「temp ref + `git update-ref <target> <candidate> <expected-old-sha>` 原子 CAS」。
本轮落地的是**事后 reflog 回读**，两者不等价，差别五条：

1. **不绑定写者**：reflog 只记 `(old, new, actor 显示名, 时间, 消息)`，不记 invocation id。
   第三方恰好从同一基线把 target 推到同一候选时，回读同样得到 `old == 基线`——无法据此宣称
   「这是本任务的写入」。所以代码只记 `causal='reflog-consistent'`，**不出现** `cas`。
2. **排除不了 ABA**：`old → X → 原值 → X` 的往复在 reflog 里留多条记录，只看「new 那一跳」
   不足以证明期间无人写过；真 CAS 由 git 在 ref 更新瞬间做比较，是原子的。
3. **日志缺口**：`core.logAllRefUpdates=false`、reflog 被 `git reflog expire` / GC 清理，或
   `wt merge` 一次写多次 ref 时，回读只能落到 `unknown` 或读到中间 old。
4. **非 ff 无 actor**：强制更新只说明 old/new OID，不说明谁推的。
5. **顺序依赖**：回读发生在合并之后，失败只能「保留现场 + 判 `proof_failure`」，不能阻止写入。

真 CAS 需要「wt 不直接写 target」的架构变更（本进程以 candidate 做
`update-ref <target> <candidate> <expected-old>`，失败即回滚并记 `proof_failure`），
已列为待办（见 §21.5）。在它落地之前，代码与文档一律只称 `reflog-consistent` / `observational`。

**负例（三档全绿仍判死）**：`test_merge_flags_third_party_race_as_proof_failure`——wt 回执身份
正确、target 前进、`ff_ok` 成立，只要回读旧值 ≠ 基线，即判 `proof_failure` 并保留现场。
配套 `test_ref_update_from_requires_adjacent_selector` 三条反例（首行无 selector / 跳号 /
中间行 malformed）全部只允许 `unknown`；正例 `test_merge_reflog_consistent_never_labelled_cas`
显式断言 `'cas' not in {causal}`。


### 21.3 额外实测缺陷：MSYS fork 诊断被当「真错误」

三文件全量连续两次各抖红 1 例，报「ccpm 判定出现错误输出 … （共 N 行真错误）」。
三种真实 MSYS 行（实测）：

```
0 [main] bash 7095 dofork: child -1 - forked process 25912 died unexpectedly, retry 0, exit code 0xC000012D, errno 11
0 [main] tr (12144) child_copy: cygheap read copy failed, 0x0..0x800800C5C0, done 0, windows pid 12144, Win32 error 299
0 [main] bash 1130 dofork: child -1 - CreateProcessW failed for 'C:\Program Files\Git\bin\..\usr\bin\bash.exe', errno 11
```

根因：旧 `_CYGWIN_NOISE` 逐条**整行锚定尾部形态**，一旦 `errno` / pid / 路径变化就追不上，
一次 fork 抖动把整批判红。改为三层规则：

- `_MSYS_DIAG`：`^\s*\d+\s*\[main\]\s+\S+\s+(?:\(\d+\)\s+|\d+\s+)?…(?:fork|dofork|child_copy|…):`
  —— 命中即视为**来自 MSYS 运行时**（这只说明来源，不说明语义安全）；
- `_MSYS_PURE`（r16 起为**白名单**，整行 `$` 锚定）：只认实测纯运行时尾部——`dofork: child -1
  - forked process N died unexpectedly[, retry N][, exit code 0x…][, errno N]`、
  `dofork: child -1 - CreateProcessW failed for '<path>'[, errno N]`、
  `child_copy: cygheap read|write copy failed, …`，外加老式 `fork: retry: Resource temporarily
  unavailable`；
- `_BIZ_FAIL`（双保险，命中即真错误）：`permission denied|access is denied|no such file|not found|
  not a git repository|fatal:|cannot open|cannot create|cannot lock|could not lock|unable to |
  corrupt|bad object|invalid path|error:|failed to |must be run in a work tree`。

未命中白名单的尾部**一律判真错误**（fail-closed）。r15b 审计实测七例曾被旧「业务词表反向排除」
全部漏放成噪声：`could not lock config file .git/config: File exists`、`bad object deadbeef`、
`index file corrupt`、`cannot lock ref refs/heads/main`、`unable to write new index file`、
`invalid path aux`、`error: failed to push some refs`——现全部进 `gate_check` 层负例。

依据：业务程序（bash/sh/git）自己的报错不走 `[main]` 前缀。用例覆盖：三种实测运行时形态放行
（含 retry / exit code / errno 尾部）、长格式尾部挂业务文本仍拒、无前缀的
`bash: fork: Permission denied` 仍拒、审计七例业务尾部逐一在 `gate_check` 层判真错误。


### 21.4 验证（终态）

| 阶段 | 结果 |
|---|---|
| ⑦ 完成 | 两文件 136 / 三文件 189 |
| ③ 完成 | 三文件 192 / 54.63s |
| ② 完成 | 单文件 56 / 13.41s |
| ⑥ 后 | 196 + 1 红（doctor 卡片状态，已修） |
| ④①⑥ 后 | 200 + 1 红（MSYS 抖动误判） |
| MSYS 修复后 | `-k cygwin` 6 passed；全量 **203 passed / 43.12s** |
| ⑤ 落地后 | ⑤ 定向 4 passed；全量 **207 passed / 42.72s** |
| r16 回修后 | 定向 31 passed；digest/fingerprint 13 passed；全量 **221 passed / 52.99s** |

`git status --short` 中另有大量与本轮无关的改动（历史报告/脚本/`tasks/*` 等），
**不入本轮提交**；本轮只 add 下列 5 个文件：
`scripts/gorch/batch_orchestrator.py`、`scripts/gorch/codex_channel.py`、
`tests/test_gorch_batch_orchestrator.py`、`tests/test_gorch_codex_channel.py`、
`tests/test_gorch_merge_timeout.py`。

### 21.5 仍未完成（如实登记）

- **真实批次 `run_all`**（E1-4 后半）仍未跑成，结论同 §20.5：改用 `git worktree add` 作载体，
  不在主仓直接跑（会向已推送分支写探针提交）。
- 第十 / 十二 / 十三 / 十四轮审计全文仍只在 `Temp`，未入库成 docs 提交。
- ⑤ 若改为 `update-ref` 直接接管合并写入（绕过 wt），需再引入 candidate 事务与临时 ref 生命周期。

### 21.6 r16 回修（r15b 审计判「不一致」后的收敛）

第二轮 Codex 只读审计（`codex-r15b-audit-last.md`，854.5s / 19,069B）判 ①⑥⑦ 一致、
**②③④⑤ 不一致**，另有 MSYS 真 fail-open 七例与四份文档过强声明。本轮据此改：

| 审计项 | 改动 | 用例 |
|---|---|---|
| ② 根 reparse | `_digest` 目录分支先判 `st_file_attributes & FILE_ATTRIBUTE_REPARSE_POINT` → `REPARSE:dir`，绝不 `scandir` | 新增「路径自身是 junction」真用例（域外增删条目摘要恒定） |
| ③ 异常释放 | `_acquire` 把 `open()` 移入 `try`，`OSError → SystemExit('…无法打开…fail-closed')`；`__enter__` 由只捕 `SystemExit` 改为捕 `BaseException`，先 `_release_all()` 再原样抛出 | 新增 primary `open` 抛 `PermissionError` 后 legacy 可被另一实例立即重取 |
| ④ 真单源 | `_CLEANUP_KEY_FOR` + `cleanup_schema()`；`run_all` 四处手写键全部改 `**cleanup_schema(...)` | AST：`run_all` 内禁 `kept_for_` 字面量、helper ≥4 处调用；未知桶 `KeyError` |
| ⑤ 因果表述 | `causal` 由 `cas` 改 `reflog-consistent`；`_ref_update_from` 加 selector 相邻性校验；`proof_failure` 文案改「reflog 回读不一致」 | selector 三反例 + 一对正例；改名用例断言永不出 `cas` |
| MSYS fail-open | `_is_cygwin_noise` 由「业务词表反向排除」改为**纯运行时白名单** `_MSYS_PURE` + `_BIZ_FAIL` 双保险，未识别尾部一律真错误 | 审计七例参数化进 `gate_check` 层负例；三种实测运行时形态放行对照 |

全量：**221 passed / 52.99s**（r15 终态 207 → 净 +14）。
**仍未做**：真 CAS（需 wt 不写 target 的架构变更）；⑤ 的超 12 跳 / 选择性过期 / 多次写 ref /
非 ff 负例；真实批次 `run_all`（E1-4 后半）。
