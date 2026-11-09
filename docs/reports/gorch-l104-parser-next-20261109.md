# G-ORCH 判据门收紧 + 选单接线 · 执行报告

- 日期：2026-11-09
- 范围：按 Owner 采纳的组合「B 为主 + A 只接 next.sh」执行一轮
  - **B**：修 `scripts/gorch_contract.py`，给 4 类畸形行配机检拒绝测试
  - **A**：只补接 ccpm `next.sh` 的选单动作
- 不含：L1-02（`verify-order.py` 解释器唯一性）、L1-03（`test_verify_order.py` 合成 XML 计数）——留给审计工单 01 的后续轮

---

## 一、结论

1. **L1-04 已闭环**（判据为"畸形行必须被看见或被拒"，不是"必须报错"）。四类畸形行现在：① 缩进卡行**被正确读出**；② 缺分隔符、③ 非整数门 ID、④ 无编号门 ID **全部 REFUSE**。
2. **选单动作已接**。`batch_orchestrator next <batch>` 复用 `gate_check`（判定仍来自 ccpm 原函数 `unmet_deps` / `active_conflicts`），只补"选出一个"。
3. **过程中查出两个新洞，均未擅自改**，登记待 Owner 裁决（见 §五）。
4. 回归：**176 passed / 0 failed**；真实工单 **14 份 × 2 解析器 = 28 次调用，0 误伤**。

---

## 二、四类畸形行：修前 / 修后

| # | 输入 | 修前 | 修后 | 为什么这样算对 |
|---|---|---|---|---|
| ① | `  \| T1 s1-host-shell-envcheck \| ...`（缩进卡行） | `order_cards` 返回 `[]`（漏掉） | 返回 `['s1-host-shell-envcheck']`（**读出**） | 缩进是合法嵌套表格（标题/列表下的表），缩进不是单元格内容。拒绝它会误伤真实工单——这属于"没进视野"，不是"读不出" |
| ② | `\| T2s1-host-envcheck \| x \|`（任务号与卡号无分隔） | 返回 `[]`（当"不命名卡"） | `ValueError: ... not separated by whitespace` | T 号紧跟一个卡形状，无法判断是"没有卡"还是"卡写坏了"，必须拒 |
| ③ | `\| ACC-1x \| 判据 \| 方法 \|` | `acc_rows` 返回 1 行（被当合法门，与 `ACC-1` 比对） | `ValueError: ... not a whole ACC-<digits> id` | 前缀匹配让 `ACC-1x` 冒充 `ACC-1`，一个判据会顶掉另一个 |
| ④ | `\| ACC-X \| 判据 \| 方法 \|` | 返回 0 行（静默漏） | `ValueError: ... not a whole ACC-<digits> id` | 门没有名字就无法被审，漏掉等于这张卡少一个门 |

**这里修正了审计报告里我自己写的验收口径。** 审计 §六 工单 01 原写"4 类畸形行 4/4 REFUSE"，实际应为 **1 类必须读出 + 3 类必须 REFUSE**。① 若也拒绝，会把"嵌在标题下的合法表格"判成非法，属于用错误方式通过判据。

---

## 三、代码改动

### 3.1 `scripts/gorch_contract.py`（113 → 约 165 行）

| 项 | 改法 |
|---|---|
| 块收集 | `_blocks` 改为 `line.strip().startswith("|")`。原实现只收 `startswith("|")`，缩进行在进任何正则之前就被丢掉 |
| 任务行识别 | `_TASK_CELL = ^T\d+(?![0-9])(.*)$`，`(?![0-9])` 防 `T1` 匹配进 `T10`；组 1 是任务号之后的全部内容 |
| 缺分隔 | 组 1 非空且首字符非空白，且内容以 `s1`/`orb-w` 开头 → REFUSE；否则按"不命名卡"跳过（不扩大误伤面） |
| 门 ID | `_ACC_ID = ^ACC-\d+$`（全匹配、锚定）；`_ACC_LOOKS = ^ACC[-_]`（不区分大小写）——首格"像门但不是整门"→ REFUSE |
| 保留 | 跨表同卡合并、表内重复拒绝、三列非空、重复门 ID 拒绝，全部原样 |

### 3.2 `tests/test_order_contract.py`（6 → 10 条）

新增 4 条，覆盖"必须读出"与"必须拒绝"两类：

- `test_an_indented_card_row_is_read_rather_than_dropped`
- `test_a_malformed_card_row_is_refused_even_when_indented`
- `test_a_task_id_that_runs_into_the_card_reference_is_refused`
- `test_a_gate_id_that_is_not_a_whole_acc_number_is_refused`（`ACC-1x` 与 `ACC-X` 各一次）

### 3.3 `scripts/gorch/batch_orchestrator.py`（加 `next` 子命令）

- 新增 `next_task(batch_dir)`：调 `gate_check`，取第一个 `可开工`，其余连同 `verdict` / `unmet_deps` / `active_conflicts` 一并交出。
- CLI 新增 `next <batch_dir>`；有下一单 exit 0，没有 exit 1（调用方要能区分"没有下一单"与"跑完了"）。
- **没有改任何判定逻辑**：判定仍是 ccpm 的 `unmet_deps` / `active_conflicts` / `frontmatter_field`。

### 3.4 `tests/test_gorch_batch_orchestrator.py`（40 → 42 条）

- `test_next_returns_the_first_ready_task_and_reports_the_rest`
- `test_next_is_none_when_nothing_is_ready`

---

## 四、验证证据

### 4.1 单元 / 回归测试（`venv-openjarvis` 解释器，`-o addopts=`）

| 测试文件 | 结果 |
|---|---|
| `test_order_contract.py` | **10 passed** |
| `test_gorch_batch_orchestrator.py` | **42 passed** |
| `test_freeze_binding.py` + `test_dispatch_receipt_contract.py` + `test_audit_checklist.py` + `test_audit_slot_age.py` + `test_codex_resolution.py` | **50 passed**（59.44s） |
| `test_gorch_codex_channel.py` + `test_gorch_bridge.py` + `test_gorch_kanban.py` + `test_gorch_merge_timeout.py` + `test_gorch_slot_adapter.py` + `test_run_gorch.py` | **74 passed**（15.82s） |
| **合计** | **176 passed / 0 failed** |

### 4.2 真实工单无误伤（收紧不得把真工单判坏）

14 份真实文档（`wo-s1-host-shell.md`、`wo-s1-queue-engine.md` ×2、`wo-orb-w7-oversight`、7 份 stage 报告、2 份独立验收、`review.md`、`WO-README.md`）× `order_cards` + `acc_rows` = **28 次调用，0 次 ValueError**。

其中 `wo-s1-host-shell.md` 的 5 张卡集合与旧版逐字一致：

```
['s1-host-shell-envcheck', 's1-host-shell-winui3-init', 's1-host-shell-webview2',
 's1-host-shell-floatingball', 's1-host-shell-selfcheck']
```

### 4.3 `next` 子命令五状态实测（真实 ccpm 判定，5 任务批次）

| 任务 | status / 声明 | verdict | 期望 |
|---|---|---|---|
| A-open | `open` | 可开工 | ✅ |
| B-waitdep | `open` + `depends_on: [A-open]` | 等待依赖（`unmet=[A-open]`） | ✅ |
| C-running | `in-progress` | 非开放状态 | ✅ |
| D-conflict | `open` + `conflicts_with: [C-running]` | 等待冲突解除（`conflicts=[C-running]`） | ✅ |
| E-closed | `closed` | 非开放状态 | ✅ |

`next` = `A-open`，退出码 0。另一批次仅含 `in-progress` 任务 → `next: null`，退出码 1。

---

## 五、两个新洞（**未改**，登记待裁）

### 5.1 判据表缺失 = 冻结门空转（fail-open）

`scripts/freeze-work-order.py:388`：

```python
if gate_ids and (declared_gates != gate_ids or r1 != gate_ids or r2 != gate_ids):
```

`gate_ids` 为空（卡上没有 ACC 表）时直接跳过"每个门都被审过"的检查。

实测：**14 份真实文档里 0 份含 `ACC` 字样**（`grep -c ACC` 命中 0），旧版 `acc_rows` 同样返回 0 行——说明这条路径从来没被真实工单触发过。也就是说"每门必审"这道门，在真实工单上是空转的。

- 为什么没改：改成"无 ACC 表即拒绝冻结"会让**所有现存工单**无法冻结，属阻断性变更，需要 Owner 先定"卡是否必须声明判据表"。
- 建议：在工单 01 里加一条判据——"卡必须有 ≥1 个 ACC 门，或有显式 `no_gates: <理由>` 豁免"，二者都没有则拒绝冻结。

### 5.2 `status: blocked` 会让整批判定失败（fail-closed，但状态词缺一格）

`batch_orchestrator.py:43` `VALID_STATUSES` 不含 `blocked`。实测一个 `status: blocked` 的任务：

```
ccpm 读到未知状态 blocked-one.md: 'blocked'，fail-closed 不派发
```

`gate` / `next` / `provision` 会因此整批拒绝。而 `codex-channel.json` 的运行时回执用的是 `done` / `blocked`——两套状态词在这里正面对撞。

- 为什么没改：`VALID_STATUSES` 是"什么算合法状态"的口径，加 `blocked` 是放宽判定，需要 Owner 拍板；而且它与 §5.1 是同一类问题（状态词三套并存）。
- 建议：定一份唯一状态词表（建议以 ccpm 的 `open/in-progress/closed` 为骨、把 `blocked` 与 `done` 映射进去），`VALID_STATUSES` 与 `kanban_update.py` 一起对表。

---

## 六、边界与未做

| 项 | 状态 |
|---|---|
| L1-02 `verify-order.py:318/321`（接受 `python3`、`Scripts` 下任意层级） | **未动**，留工单 01 |
| L1-03 `test_verify_order.py:485`（仍是合成 XML 计数） | **未动**，留工单 01 |
| `next.sh` 脚本原文 | **未改一字**；本仓不可直接运行（`list_task_files()` 只认 `.claude/epics/<纯数字>.md`），接的是判定语义 |
| `next.sh` 与本地的一处口径差异 | `next.sh` 把**空 status** 当候选；本地按 `VALID_STATUSES` 当未知状态拒绝（更严）。已在代码注释写明 |
| ACC 表 fail-open（§5.1） | 登记，未改 |
| `blocked` 状态词（§5.2） | 登记，未改 |

---

## 七、审计声明

- 检查范围：`scripts/gorch_contract.py`、`tests/test_order_contract.py`、`scripts/gorch/batch_orchestrator.py`、`tests/test_gorch_batch_orchestrator.py`、`scripts/gorch/ccpm/next.sh`（只读）、`scripts/gorch/ccpm/lib.sh`（只读）、14 份真实文档（只读）
- 证据方式：修前探针复现 4/4、修后探针复测、旧版对照（`git show HEAD:` 取旧源码同文件跑）、真实工单 28 次调用、176 条测试、`next` 五状态实测 + 两个边界批次
- 未覆盖：L1-02 / L1-03 的实测（不在本轮范围）；ACC 表在**未来**工单上的表现（现存工单 0 份含 ACC）
- 结论不超过上述范围
