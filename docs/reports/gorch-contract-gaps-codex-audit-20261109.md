# G-ORCH 契约缺口 · Codex 独立审计（只读，原文未编辑）

- 日期：2026-11-09
- 执行体：Codex CLI（`gpt-5.6-sol`，`model_reasoning_effort=high`，`--sandbox read-only`）
- 输入包：`Temp\gorch-codex-audit-package.md`（材料 A = DeepSeek 方案，材料 B = 豆包复核，+ 审计任务书）
- 实测：763.8s / 190,525 tokens / rc=0
- 本轮**未修改任何文件、未重跑测试**；文中「176 passed / 0 failed」是待保基线，不是本轮实测结果
- 性质：**独立第三方审计意见，不是决策**。采纳前需 Owner 拍板，采纳后按 G-TASKFLOW-001 转工单

---
本次只读审计的结论是：A 的核心方向有可取之处，但它把“批次任务 frontmatter”“冻结工单/卡”“看板状态”三个不同数据域混在了一起，原 7 步无法直接落地；B 的 4 个修正方向基本成立，但第 2、3、4 点仍需调整。最稳妥的合并方案是：保留 `status` / `result` 分域，未知状态继续整批 fail-closed；修复冻结门的空 ACC 短路；如果 Owner 批准“替代判据 waiver”，就把它接入现有 `gorch-manifest → verify-order → audit-work-order → freeze-work-order` 链，而不是另起测试执行链。

本轮没有修改任何文件；目标文件和 tests 的定向 `git status` 无输出。由于测试可能生成缓存、临时 worktree 或回执，本轮没有在只读任务中重跑测试，因此“176 passed / 0 failed”是待实施后必须保住的验收基线，不是本轮新实测结果。

# 一、代码核对结果

## A 的结论

| A 项 | 判定 | 代码事实 |
|---|---|---|
| 1. 两个问题不同源、应分开处理 | **相符** | 空 ACC 问题位于冻结/审计链；状态词问题位于批次编排层。前者读取卡与审计回执，后者读取批次 frontmatter，回滚单元确实不同。 |
| 2a. “豁免不是免校验，而是替代校验” | **无法判定** | 这是政策选择，不是现有代码事实；而且基线只冻结了“四个 gate key 集合相等”，没有批准 waiver 语法。新增 waiver 属 L2，须 Owner 书面拍板：[基线 27–34 行](H:/UltimaAI/UltimaAgent/docs/reports/gorch-judgement-baseline-20261109.md:27)、[93–97 行](H:/UltimaAI/UltimaAgent/docs/reports/gorch-judgement-baseline-20261109.md:93)。 |
| 2b. waiver 写在“卡所在工单 frontmatter”，只改冻结门即可 | **不符** | `freeze-work-order.py` 读取的是审计中的卡路径和 `tasks/queue/<work_order>.md`，见 [369–388 行](H:/UltimaAI/UltimaAgent/scripts/freeze-work-order.py:369)、[401–409 行](H:/UltimaAI/UltimaAgent/scripts/freeze-work-order.py:401)；它不读取 `batch_orchestrator` 的批次 frontmatter。更关键的是，正常审计在无 ACC 时已经于 [audit-work-order.py:268–275](H:/UltimaAI/UltimaAgent/scripts/audit-work-order.py:268) 提前拒绝，因此只改冻结门无法形成可到达的 waiver 路径。 |
| 2c. 将 388 行改成 `if (...) and (gate_ids or ...)` | **不符** | 单改这个表达式仍不能定义空表时该比较哪些 key；若四个集合都空，仍不会拒绝。正确事实是当前 [freeze-work-order.py:384–391](H:/UltimaAI/UltimaAgent/scripts/freeze-work-order.py:384) 仅在 `gate_ids` 非空时比较，而空表必须先进入一个明确的“拒绝或有效 waiver”分支。 |
| 3. 批次 `waivers / cards <= 0.25` | **不符** | 当前冻结门显式只接受单卡：`len(receipt_cards) != 1` 即拒绝，见 [freeze-work-order.py:397–438](H:/UltimaAI/UltimaAgent/scripts/freeze-work-order.py:397)。不存在“整批冻结”聚合点；对单卡冻结套 25% 阈值时，一张 waiver 卡的比例恒为 100%，反而会让所有 waiver 永远失败。 |
| 4. 冻结时执行 `instead`，并绑定测试文件 blob SHA | **不符（实现结构）/无法判定（敏感性）** | 现有 verifier 已在被验 commit 的干净 worktree 中运行声明测试，并拒绝 0 个实际执行测试，见 [verify-order.py:873–906](H:/UltimaAI/UltimaAgent/scripts/verify-order.py:873)；冻结又会重新运行 verifier 并绑定 commit/tree，见 [freeze-work-order.py:224–244](H:/UltimaAI/UltimaAgent/scripts/freeze-work-order.py:224)、[298–321 行](H:/UltimaAI/UltimaAgent/scripts/freeze-work-order.py:298)。单独再绑测试文件 SHA 是重复状态。某测试是否真的对卡产出敏感，静态 SHA 和一次绿测都证明不了。 |
| 5a. `status` 与 `result` 不合并 | **相符** | 批次 `status` 在 [batch_orchestrator.py:42–44](H:/UltimaAI/UltimaAgent/scripts/gorch/batch_orchestrator.py:42)；派发回执写 `record['result']`，见 [codex_channel.py:203–228](H:/UltimaAI/UltimaAgent/scripts/gorch/codex_channel.py:203)。合并会混淆持久生命周期与单次执行结果。 |
| 5b. `blocked` 只归 `result` | **相符，但须限定数据域** | Codex channel 的确只写 `result = done/blocked`，没有写 frontmatter `status`：[codex_channel.py:220–227](H:/UltimaAI/UltimaAgent/scripts/gorch/codex_channel.py:220)。但看板另有独立的首字母大写 `state: Blocked`，见 [kanban_update.py:497–511](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:497)；这不是批次 `status`。 |
| 5c. `RESULT_CANON={done, blocked, failed}` 与现状一致 | **不符** | 当前 emitter 只产生 `done` 或 `blocked`，[codex_channel.py:221](H:/UltimaAI/UltimaAgent/scripts/gorch/codex_channel.py:221)；合并层只认可 `result == 'done'`，[batch_orchestrator.py:418–428](H:/UltimaAI/UltimaAgent/scripts/gorch/batch_orchestrator.py:418)。`failed` 是新提案，不是现存结果值。 |
| 5d. `status_map.py` 可成为全系统单一权威源，并让 `kanban_update` 也导入 | **不符** | ccpm 原函数仍是判定权威；Python 最多只能做映射适配。`kanban_update.py` 操作的是看板 `state` 和 todo `status`，不是批次 frontmatter `status`；强行导入同一 normalizer 会把不同状态域耦合。看板状态转换来自 `edict` 或 fallback，[kanban_update.py:334–354](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:334)，并在 [385–387 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:385) 实际判定。 |
| 6a. 原始 `next.sh` 会静默跳过任意非空、非 `open` 状态 | **相符** | [next.sh:19–22](H:/UltimaAI/UltimaAgent/scripts/gorch/ccpm/next.sh:19) 对所有非空、非 `open` 状态直接 `continue`，最后固定退出 0，[next.sh:49–60](H:/UltimaAI/UltimaAgent/scripts/gorch/ccpm/next.sh:49)。 |
| 6b. 当前 Python `next` 也沿用这一行为 | **不符** | Python `next_task()` 不执行 `next.sh`，而是先调用同一个 `gate_check()`，见 [batch_orchestrator.py:149–169](H:/UltimaAI/UltimaAgent/scripts/gorch/batch_orchestrator.py:149)。未知状态在 [126–128 行](H:/UltimaAI/UltimaAgent/scripts/gorch/batch_orchestrator.py:126) 直接 `SystemExit`，所以当前 `gate`、`next`、`provision` 都会在未知状态处整体失败。 |
| 6c. 未知状态只跳过该任务、其他任务继续 | **无法判定** | 这是 Owner 政策选择，不是现状。当前测试明确钉死整批 fail-closed：[test_gorch_batch_orchestrator.py:124–128](H:/UltimaAI/UltimaAgent/tests/test_gorch_batch_orchestrator.py:124)。 |
| 7. 以 `frozen_at < WAIVER_EPOCH` 过渡 | **不符** | 目标链中没有读取 `frozen_at`；冻结代码只用当前日期生成 tag 名，[freeze-work-order.py:478–480](H:/UltimaAI/UltimaAgent/scripts/freeze-work-order.py:478)。本轮全树定向搜索也未发现工单/卡上的 `frozen_at` 字段。 |
| 8. 7 步落地顺序与真实文件结构吻合 | **不符** | 它遗漏了必须修改的 `audit-work-order.py`；也没有把替代测试接到现有 `verify-order.py`；所谓 `next.sh` 包装层实际上不存在，因为 Python `next_task()` 直接调用 `gate_check()`；对 `kanban_update.py` 的归一化则跨错状态域。对应入口分别见 [audit-work-order.py:268–275](H:/UltimaAI/UltimaAgent/scripts/audit-work-order.py:268)、[verify-order.py:873–906](H:/UltimaAI/UltimaAgent/scripts/verify-order.py:873)、[batch_orchestrator.py:149–169](H:/UltimaAI/UltimaAgent/scripts/gorch/batch_orchestrator.py:149)。 |
| 9. 全目录 grep 会误报；SHA 会被无关格式化误伤 | **相符** | `kanban_update.py` 中确有大量合法的独立状态域字面量；而现有 commit/tree 绑定已覆盖测试文件版本，额外 blob SHA 只增加重复失效位。 |
| 10. 不改 ccpm 本体、不合并 `status/result`、不把 `blocked` 加入批次 status | **相符，且应保留** | 这与“ccpm 原函数只能接、只能映射”的约束一致。 |

## 指定核对点

### 1. 388 行短路

**相符。** 当前确为：

- `gate_ids` 为空时不进入集合相等检查：[freeze-work-order.py:384–391](H:/UltimaAI/UltimaAgent/scripts/freeze-work-order.py:384)。
- 但正常审计链会更早拒绝空 ACC：[audit-work-order.py:268–275](H:/UltimaAI/UltimaAgent/scripts/audit-work-order.py:268)。

所以正确表述是：“冻结门存在可由手工/旧回执触发的独立 fail-open 缺口；标准审计路径目前 fail-closed。”不能说整个正常链路对空 ACC 都放行。

### 2. `VALID_STATUSES` 与 `is_done_status`

**不是同集。**

- `VALID_STATUSES` 是六个输入合法值：`open`、`in-progress`、`in_progress`、`closed`、`completed`、`done`，[batch_orchestrator.py:42–44](H:/UltimaAI/UltimaAgent/scripts/gorch/batch_orchestrator.py:42)。
- `is_done_status` 只认三个完成态：`closed`、`completed`、`done`，[ccpm/lib.sh:47–52](H:/UltimaAI/UltimaAgent/scripts/gorch/ccpm/lib.sh:47)。
- 冲突判定另只认 `in-progress`、`in_progress`，[ccpm/lib.sh:72–84](H:/UltimaAI/UltimaAgent/scripts/gorch/ccpm/lib.sh:72)。

因此 A 可以把六个原始值映射为三个规范值，但不能把 `is_done_status` 的三值集合说成完整合法状态集合。

### 3. `blocked` 究竟写在哪里

- 单次 Codex 派发失败：写入 `codex-channel.json` 的 `record['result'] = 'blocked'`，[codex_channel.py:220–227](H:/UltimaAI/UltimaAgent/scripts/gorch/codex_channel.py:220)。
- 看板阻塞：写入看板任务的 `t['state'] = 'Blocked'` 及 `t['block']`，[kanban_update.py:497–511](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:497)。
- 批次 Markdown 的 frontmatter `status`：当前合法集合不含 `blocked`，[batch_orchestrator.py:42–44](H:/UltimaAI/UltimaAgent/scripts/gorch/batch_orchestrator.py:42)。

所以“`blocked` 不是工单 `status`，而是回执 `result`”在批次编排数据域内成立；不能据此否认看板还有独立的 `state: Blocked`。

### 4. `kanban_update.py` 中字面量分类

参与判定的：

- 小写 `completed` 是 todo 子状态：完成数统计在 [243–248 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:243)，并在 `cmd_done` 中阻断未完成 todo，[458–465 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:458)。
- 小写 `in-progress/completed/not-started` 是 todo 合法值和单一进行中约束，[656–681 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:656)、[690–707 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:690)。
- 首字母大写 `Done/Blocked/Doing/Review` 等是看板状态机，定义于 [341–353 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:341)，判定于 [385–387 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:385)。
- `Done` 还参与高风险确认转换，[359–364 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:359)。

只是展示或命令/事件标签的：

- `STATE_ORG_MAP` 中的 `Done → 完成`、`Blocked → 阻塞` 是展示映射，[77–82 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:77)。
- 小写 `done` 在命令权限集合、CLI 分派和审计事件中是操作名，不是批次 status，例如 [174–181 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:174)、[488–494 行](H:/UltimaAI/UltimaAgent/scripts/gorch/kanban_update.py:488)。

因此 B 说“看板内必然有合理字面量”是对的，但将它们概括为“只是展示”不准确：其中相当一部分真实参与看板/todo 判定，只是属于另一个状态域。

### 5. A 的 7 步与文件结构

**整体不符。** 最少缺三处接线：

1. 无 ACC 当前先在 `audit-work-order.py` 被拒，必须处理审计入口。
2. 替代测试应复用 `verify-order.py` 的干净 commit、JUnit、非零实际执行测试回执，而不是让 freeze 再造一套 runner。
3. Python `next` 没有包装或执行 `next.sh`；未知状态策略应在 `gate_check()` 及其所有调用者上统一。

此外，`is_task_file()` 只接受纯数字文件名，[ccpm/lib.sh:5–14](H:/UltimaAI/UltimaAgent/scripts/gorch/ccpm/lib.sh:5)，`list_task_files()` 只遍历 `.claude/epics/*/*.md`，[24–34 行](H:/UltimaAI/UltimaAgent/scripts/gorch/ccpm/lib.sh:24)；Python `gate_check()` 则直接枚举批次目录全部 `*.md`，[batch_orchestrator.py:71–83](H:/UltimaAI/UltimaAgent/scripts/gorch/batch_orchestrator.py:71)。两者的枚举域本来就不相同。

关于“14 份”：当前树没有定义这 14 份的选择规则。本轮看到 `tasks/queue/*.md` 共 74 份、`tasks/cards/**/task.md` 共 94 份，而 `data/gorch/handoff/**/batch/*.md` 仅 1 份。故“14 份”的具体 ID 集合在本仓当前状态下**无法独立判定**，必须先给出权威 selector 或固定清单。

# 二、B 的 4 处修正是否成立

1. **砍掉测试文件 blob SHA：成立。**

   当前 verifier 已在 `end_sha` 的干净 worktree 中执行测试，冻结又绑定并复核 HEAD/tree；测试文件版本已经被 commit/tree 覆盖。额外 blob SHA 是重复状态，增加格式化误伤而没有增加新的信任边界。调整方式不是“freeze 再跑一次任意 pytest”，而是让 waiver 引用现有 verifier 已执行并形成结构化回执的精确测试目标。

2. **“对卡产出敏感”须人工复核：成立但需调整。**

   原则成立：一次绿测无法证明因果敏感性。但 B 的 `pytest ... -k not_a_real_test` 示例不适用于本仓门：当前命令契约只接受测试路径/精确 node，额外收集选项会被拒，[verify-order.py:295–302](H:/UltimaAI/UltimaAgent/scripts/verify-order.py:295)、[test_verify_order.py:433–438](H:/UltimaAI/UltimaAgent/tests/test_verify_order.py:433)；而 0 个实际执行测试也会在 [verify-order.py:894–901](H:/UltimaAI/UltimaAgent/scripts/verify-order.py:894) 被拒。真实剩余漏洞应表述为：“一个确实执行但与卡产出无关、永远为绿的测试仍可骗过 waiver。”

3. **全目录 grep 不能作为判据：成立但需调整。**

   `kanban_update.py` 的字面量不只是展示，还有 todo 和看板状态机判定。正确做法不是“展示允许、判定禁止直写”，而是按数据域限定：批次 frontmatter status 的判定只在 batch adapter/ccpm 对照测试里收紧；看板 `state`、todo `status`、回执 `result` 各自保留自己的词表和测试。

4. **不能用 `frozen_at < WAIVER_EPOCH`：成立但需调整。**

   `frozen_at` 当前不存在，且时间阈值会制造永久隐式豁免。B 的显式 ID 白名单比 epoch 好，但“测试运行时动态扫描并生成白名单”仍会让新脏数据自动加入。若真需要白名单，必须是实施时一次性生成并提交的静态快照，并有断言禁止新增；不过我的最终推荐是根本不设运行时历史豁免，见下文。

# 三、A 和 B 都漏了什么

1. **正常审计器已经拒绝空 ACC。**  
   影响：waiver 不能只接 freeze；不改 `audit-work-order.py` 就没有正常可达路径。

2. **冻结门是显式单卡门，不存在整批 waiver 聚合点。**  
   影响：25% 比例无法在现有边界实现，并会把单卡 waiver 恒算成 100%。

3. **Python `next` 不执行 `next.sh`，且两者枚举文件的规则不同。**  
   影响：所谓“在 next.sh 包装层补偿”找错了接线点，无法保证 `gate/next/provision/execute` 一致。

4. **跳过未知状态可能破坏冲突安全性。**  
   影响：`active_conflicts()` 只把 `in-progress/in_progress` 视为活动；若一个未知状态任务其实正在执行，跳过它后，另一个 `conflicts_with` 它的 open 任务可能被错误派发。

5. **当前仓库无法从代码或目录规则复现“现存 14 份”的 ID 集合。**  
   影响：任何 epoch、白名单或“14 份零误伤”测试在没有权威选择规则前都无法写成稳定断言。

# 四、最终方案（合并版）

前置口径：空 ACC 的“存在性要求”和 waiver 都超出当前基线的 L0-05 集合相等判据，应先作为 L2 由 Owner 书面批准；批准后仍保持两问题分开提交、分开回滚。

## 第 1 步：建立 Python 状态适配层，不碰看板

**类型：中性**

新增 `scripts/gorch/status_map.py`，但明确它是“Python 适配层”，不是取代 ccpm 的全系统权威源：

- 规范 status：`open`、`in-progress`、`closed`。
- 输入别名：`in_progress → in-progress`，`completed/done → closed`。
- 当前 result：只登记真实 emitter 已产生的 `done/blocked`；暂不凭空加入 `failed`。
- `blocked` 对 batch status 归一结果为未知。
- `kanban_update.py` 不导入此模块。

可机检判据：

- 六个现有 raw status 归一后，`gate_check()` 的 ready/non-ready 结果与改动前完全一致。
- 对六个 raw status 逐一调用原 ccpm 真值：完成态只命中 `closed/completed/done`；活动冲突只命中 `in-progress/in_progress`。
- `normalize_status('blocked') is None`。
- `codex_channel` 只写 `result`，且值属于 `{done, blocked}`，不写 `status`。
- `kanban_update` 的看板和 todo 测试结果不变。

回滚点：移除 Python adapter 导入，恢复当前 `VALID_STATUSES`；ccpm 和看板均未动。

## 第 2 步：未知状态继续整批 fail-closed，并统一所有入口

**类型：中性（固化现状）**

不采纳 A 的“跳过单任务”。`gate_check()` 继续对缺失/未知 status 拒绝；`next`、`provision`、`execute` 都通过同一个 `gate_check()` 获得一致结果。

可机检判据：

- 构造 `status: blocked` 与一个无关 `status: open` 同批：`gate`、`next`、`provision`、`execute` 全部非零/抛出拒绝。
- 拒绝信息包含未知任务 ID 和原始状态值。
- 拒绝发生在任何 `wt_switch`、channel 子进程或工作目录创建前。
- 不产生 `skipped_unknown_status`，也不派发其余 open 任务。
- 现有 unknown/missing status 测试继续成立。

回滚点：若只调整了结构化错误输出，可回滚输出格式；不能回滚为静默跳过。

## 第 3 步：把 waiver 放进现有 `gorch-manifest`，不用批次 frontmatter

**类型：中性**

不采纳 A 的 YAML frontmatter 位置。扩展现有 `<!-- gorch-manifest ... -->` JSON，增加可选字段：

```json
"gate_waivers": [
  {
    "card": "s1-parser",
    "because": "纯文档搬运，无独立行为门",
    "instead": "tests/test_parser.py::test_indent"
  }
]
```

`instead` 必须是一个精确 pytest path/node，不允许 `-k`、额外选项或自由命令；这样可直接复用现有命令契约。

解析器放在 `gorch_contract.py`，由 verifier、audit、freeze 共用；不能分别再写三份正则/JSON 逻辑。

可机检判据：

- 无 `gate_waivers` 的现有 manifest 解析结果保持不变。
- 同一卡 0 条或超过 1 条 waiver，在空 ACC 分支均拒绝。
- 非空 ACC 卡若同时声明 waiver，拒绝，避免两套判据竞争。
- `card` 必须等于工单引用的单卡 ID。
- `because`、`instead` 必须为非空字符串。
- `instead` 必须解析为 `tests/` 下规范路径或精确 node；路径逃逸、`-k`、参数、多个 target 均拒绝。
- 畸形 manifest 整体拒绝，不静默丢字段。

回滚点：移除可选字段解析；此时所有空 ACC 卡进入下一步的严格拒绝，不回到 fail-open。

## 第 4 步：将替代测试绑定到现有 verifier 回执

**类型：收紧**

不在 freeze 里另造测试 runner。要求 waiver 的 `instead`：

- 必须是工单 manifest 中唯一一条对应的 accepted command target；
- 必须由现有 `verify-order.py` 在被验 commit 的干净 worktree 中执行；
- JUnit 必须显示至少一个实际执行测试；
- failures/errors 均为 0；
- freeze 的 fresh verifier rerun 必须再次得到同一成功结果。

可机检判据：

- 不存在的 node 在运行前被拒。
- waiver target 未出现在 accepted commands 中时拒绝。
- 一个命令混入其他 target 时拒绝，避免“别的测试兜底”。
- 0 executed、全 skipped、失败、错误、超时、无 JUnit 回执均拒绝。
- 测试文件或产出在 verified commit 之后发生变化时，现有 HEAD/tree/dirty-tree 绑定继续拒绝。
- 不增加独立 blob SHA 字段。

回滚点：撤销 waiver 与 verifier 的关联；空 ACC 仍由下一步严格拒绝，现有有 ACC 工单不受影响。

## 第 5 步：先修复冻结门的空集合短路

**类型：收紧**

在 `freeze-work-order.py` 明确执行：

- `gate_ids` 非空：无条件要求 `gate_ids == declared_gates == r1 == r2`。
- `gate_ids` 为空且没有通过 verifier 的有效 waiver：直接拒绝。
- 不再以 `if gate_ids and ...` 作为存在性开关。

可机检判据：

- 无 ACC、无 waiver，即使伪造 `audit_passed=true` 且在三处写入任意 PASS gate，也不得创建 tag。
- 有 ACC 时，顶层/任一轮多 gate、少 gate、异名 gate 均拒绝。
- 四集合完全相等且非空的既有成功用例保持通过。
- 拒绝理由区分“卡无 ACC/无 waiver”和“gate 集合不相等”。

回滚点：这是新的安全基线，不允许回滚到旧 388 行短路。后续 waiver 功能如有问题，应回滚到“所有空 ACC 一律拒绝”。

## 第 6 步：让有效 waiver 通过 audit 与 freeze

**类型：放宽**

这是相对于当前 `audit-work-order.py`“空 ACC 一律拒绝”的定向放宽，仅对第 3、4 步验证完成的 waiver 生效。

审计器为 waiver 产生一个独立且确定的审计 key，例如 `WAIVER:<card-id>`；两轮仍须对该 key 给出 PASS，freeze 再要求：

- 顶层 waiver key；
- round1 `per_gate`；
- round2 `per_gate`；
- 经 verifier 证明的 waiver key；

四者完全相等。冻结 tag receipt 同时写入 `card/because/instead` 和对应 fresh verify check，不能只写一个布尔值。

可机检判据：

- 合法 waiver、实际执行测试、两轮一致 PASS 时才允许 freeze。
- 任一轮缺失、FAIL、key 不一致、测试回执失效时拒绝。
- waiver 内容在 audit 后改变时，基于 order/card/verify 的绑定使 freeze 拒绝。
- 同一 waiver 不能服务多个卡；当前单卡限制继续保留。
- 有 ACC 的卡仍走原 ACC 路径，waiver 不能覆盖或削弱 ACC。

回滚点：关闭 waiver 分支，恢复“空 ACC 一律拒绝”；已有 ACC 路径不变。

## 第 7 步：历史兼容只做解析回归，不做运行时隐式豁免

**类型：中性**

不采纳 `WAIVER_EPOCH`，也不推荐生产路径中的永久 ID 白名单。已经冻结的历史 tag 不会因新代码被追溯失效；若历史工单将来重新冻结，则应补 ACC 或显式 waiver。

待 Owner 给出权威 14-ID 集合后，将其作为静态测试 fixture：

- 逐份解析工单、卡引用和现有 manifest；
- 断言无解析误伤；
- 断言 fixture 不会由运行时扫描自动扩张；
- 不断言这些无 ACC 历史工单可以重新 freeze。

可机检判据：

- 14 个固定 ID 全部解析成功。
- 扫描发现第 15 个候选时测试失败并要求 Owner 决策，而不是自动加入。
- 全量现有测试最终仍为 176 passed / 0 failed。
- ccpm 原函数文件哈希或行为真值测试不变。

回滚点：移除兼容 fixture/test，不影响生产判定；不存在需要关闭的运行时过渡分支。

## 不采纳的项目

- **不采纳 25% waiver 比例**：当前冻结边界是单卡，没有合法聚合点。
- **不采纳测试文件 blob SHA**：verified commit/tree 已覆盖它。
- **不采纳 `-k` 表达式**：现有测试命令契约只接受规范路径/精确 node。
- **不采纳让 `kanban_update.py` 使用 batch status normalizer**：属于不同状态域。
- **不采纳未知状态跳过**：可能破坏依赖/冲突安全，且造成 `gate` 与执行入口语义分裂。
- **不采纳 `frozen_at` epoch 或动态增长白名单**：字段不存在，且会形成永久隐式放行。
- **不采纳 `blocked_by` 字段**：当前没有调用者或 ccpm 语义消费它，属于未证明必要的新 schema。
- **不采纳尚未产生的 `result: failed`**：等真实 emitter/consumer 需要时另立契约。

## 机检覆盖不到的边界

- waiver 指向的测试是否真的对该卡产出敏感，**这一层靠人工复核**；机器只能证明“精确目标确实执行且通过”。
- `because` 是否足以证明该卡不适合写 ACC，**这一层靠人工复核**。
- 两轮模型审计是否真正独立、审计文件是否由可信第三方生成，**这一层靠人工治理/信任域**；基线已明确冻结门不是 maker-checker 或防篡改证明。
- “现存 14 份”究竟是哪 14 份，**这一层先由 Owner 给出权威集合或选择规则**，机器才能钉成固定 fixture。
- waiver 的长期使用是否过多，机器可以统计但不能自动决定合理阈值；若需要治理，建议报告数量供 Owner 审阅，而不是在当前单卡冻结门硬塞 25% 比例。

# 五、需要 Owner 拍板的点

1. **推荐批准“显式替代判据 waiver”为新的 L2，但采用现有 manifest/verifier/audit/freeze 链。**  
   理由：它保留“豁免不是免检”的原则，又避免另造 runner、SHA 状态位和批次 frontmatter 解析器。

2. **推荐未知 status 继续整批拒绝，不跳过单任务。**  
   理由：一个未知任务可能影响依赖或冲突安全；当前四个执行入口已经共享 `gate_check()`，保持 fail-closed 最一致。

3. **推荐禁止批次 `status: blocked`，并暂不增加 `blocked_by`。**  
   理由：失败事实已有 `result: blocked` 和看板 `state: Blocked` 两个明确位置；新增未被 ccpm 消费的字段只会形成第三套半有效状态。

4. **推荐不设运行时历史豁免，也不设关闭日期。**  
   理由：历史冻结 tag 无需追溯重验；未来重新冻结时补 ACC/waiver 即可，因此不存在需要永久保留或日后关闭的放宽分支。

5. **推荐 Owner 明确给出“14 份”的固定 ID 集合或可复现选择规则。**  
   理由：当前仓库目录本身推不出 14 这个集合，未固定边界就无法证明“14 份解析 0 误伤”。

