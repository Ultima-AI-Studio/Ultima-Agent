# Codex 工单 · 主脑教学 Phase 3.5（产出物任务确定性判定）

> 版本：v1.3 ｜ 状态：可开工（前置：mainbrain-teaching-phase3-frozen）｜ 适用工具：Codex
> 用法：按 T0→T3 顺序逐条执行，Gate PASS 后冻结再进下一条。每条先写 RED 再改代码。
> 方案依据：`docs/plans/plan-ultimaagent-mainbrain-teaching-phase3-5-deliverable-preclassify-20261112.md` v1.0
> 前置：`wo-ultimaagent-20261112-0046` 已冻结（commit `9bc8e4a5` / tag `ultimaagent-mainbrain-teaching-phase3-20261112`），全量基线 `561 passed / 1 failed`

---

## 0. 本单定位

Phase 3 的前置层把「做不到的本机操作」挡住了，但把「该派的产出物任务」也一并交给了不稳定的分类器。实测 10 条产出物请求坏 6 条，其中 5 条是**稳定判 query**——不是抖动，是判据语义缺了一整类（「写/起草/翻译/总结/输出」不在 `_ASK_CLASSIFY_SYSTEM` 的「动手」枚举里）。

本单在分类器之前加一层确定性判据，把「要我造一份东西」的求代劳请求直接判 `task`；同时修两处相邻误伤（工程对象被本机动作词拦住、pending 下短命令被当补槽）。

---

## 1. 范围冻结

**本阶段只做**：
1. `src/brain/agent_server.py` 新增 `_PRE_CREATE_VERB`、`_PRE_REVIEW_VERB`、`_ENGINEERING_OBJECT_PATTERN` 三个常量。
2. 新增 `_preclassify_deliverable(query)` 函数，并在 `ask_once` 内接线到 `_classify_intent` 之前。
3. 在 `_preclassify_local` 内加工程对象放行判断。
4. 修 `_pending_fill` 的短命令新请求识别。
5. 新增测试文件 `src/brain/tests/test_mainbrain_phase3_5_deliverable.py`。
6. **授权修改 `src/brain/tests/test_mainbrain_phase3_preclassify.py`，但严格限于 §8.2 指定的范围**：把 `_DELIVERABLE_TASKS` 拆成 `_DELIVERABLE_TASKS_PRECLASSIFIED` + `_DELIVERABLE_TASKS_VIA_CLASSIFIER`，把原 `test_ask_once_preserves_classifier_and_task_branch_for_deliverables` 拆成两条。该文件其他内容一个字不许动，不许删除任何 `assert` 行。

**本阶段不做**（Non-goals）：
- 不改 `_ASK_CLASSIFY_SYSTEM` 的任何一个字
- 不改 `_classify_intent` 函数体，不改 `_QUERY_HINT` / `_METHOD_ASK`
- 不改 `_preclassify_local` 已有三条件主路径的判断顺序与返回值
- 不碰 `_risk_gate` / `_no_tool_gate` / `_slot_gate` / `_CLARIFY_TEMPLATES` / `_CLARIFY_TTL` / `_CLARIFY_MAX_ASK` / `_PUSHBACK_PATTERN`
- 不改 `ask_once` 签名、不新增依赖、不落盘 pending 状态
- 不改 0044 / 0045 / 0046 任何正文
- 不做 Phase 4 / 4b / 4c 的任何内容

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `src/brain/tests/test_mainbrain_phase3_5_deliverable.py` | 先写 RED，Y/N/E/S 四组样本全部断言失败（证明判据确实缺位） |
| T1 | `src/brain/agent_server.py` | 产出物判 task 生效，Y 组 6 条 3/3 全 task |
| T2 | `src/brain/agent_server.py` | 工程对象放行 + pending 短命令，E 组与 S 组全绿且 S2/S3 契约不变 |
| T3 | `src/brain/tests/test_mainbrain_phase3_preclassify.py` | 按 §8.2 迁移两条冻结断言（拆两组参数化），全量 577 passed / 1 failed |

---

## 3. 任务明细

### T0 · 先写 RED 测试

**文件**：`src/brain/tests/test_mainbrain_phase3_5_deliverable.py`

**写什么**：
1. 建 `_DELIVERABLE_TASK` 元组，含方案 §6 Y 组六条原文；建 `_NOT_TASK` 元组，含 N 组六条原文。
2. 写 `test_preclassify_deliverable_marks_creation_requests`，对 Y 组断言 `_preclassify_deliverable(q) == "task"`——此时函数不存在，测试应当报错或失败。
3. 写 `test_preclassify_deliverable_ignores_method_questions`，对 N 组断言 `_preclassify_deliverable(q) is None`。
4. 写 `test_preclassify_local_passes_engineering_objects`，断言 `_preclassify_local("帮我修复这个接口的错误") is None`——当前实际返回 `local_delegated`，必须失败。
5. 写 `test_preclassify_local_still_blocks_desktop_logs`，断言 `_preclassify_local("帮我把桌面的日志整理一下") == "local_delegated"`——当前已通过，用于锁住 Phase 3 成果不被 T2 改动破坏。
6. 写 `test_pending_short_command_starts_new_request`，置 pending 后调 `_pending_fill("打开")` 断言返回 `None` 且 `_PENDING_CLARIFY is None`——当前返回拼接串，必须失败。
7. 写 `test_pending_referent_answer_still_fills`，置 pending 后调 `_pending_fill("应用")` 断言返回 `...（补充：应用）`——当前已通过，用于锁住 Phase 2 S3 契约。
8. 每个用例带 autouse fixture，测前备份、测后还原 `_PENDING_CLARIFY`。

**验收（Gate T0）**：`pytest src/brain/tests/test_mainbrain_phase3_5_deliverable.py -q` 输出含失败，且失败项恰好是第 2、3、4、6 条对应的用例；第 5、7 条必须已 passed。把 RED 输出粘进回执。

**禁止**：不得为了让测试变绿而先改实现；不得 skip / xfail；不得把断言写成 `in ("task", "query")` 这类松弛写法。

### T1 · 产出物确定性判 task

**文件**：`src/brain/agent_server.py`

**写什么**：
1. 在 `_PRE_DELIVERABLE_PATTERN` 附近新增 `_PRE_CREATE_VERB`（`写|起草|拟|翻译|总结|输出|产出|生成|做|制作|分析|汇总|整理成|编`）、`_PRE_REVIEW_VERB`（`看|检查|审查|评估|判断|评价|挑错|找问题`）、`_PRE_JUDGMENT_OBJECT`（`决定|取舍|抉择|判断|推荐|主意`），各带一行注释说明用途。
2. 新增 `_preclassify_deliverable(query)`，逻辑严格按方案 §4.1：空串或含「（补充：」返回 `None`；`_DELEGATE_HINT` 未命中返回 `None`；`_METHOD_ASK` 命中返回 `None`；`_PRE_REVIEW_VERB` 命中返回 `None`；`_PRE_JUDGMENT_OBJECT` 命中返回 `None`；`_PRE_CREATE_VERB` 命中返回 `"task"`；其余 `None`。**五条排除的顺序必须按方案 §4.1 原文，不得调换**。
3. 在 `ask_once` 内，`local_intent = _preclassify_local(query)` 那段 `if` 之后、`intent = _classify_intent(query)` 之前，插入：

```python
    deliverable_intent = _preclassify_deliverable(query)
    if deliverable_intent == "task":
        return _ask_task_branch(query)
```

4. 判断顺序必须保持：risk → no_tool → local（拦）→ deliverable（派）→ classify（模型兜底）。

**验收（Gate T1）**：
（1）`pytest src/brain/tests/test_mainbrain_phase3_5_deliverable.py -q` 中 T0 第 2、3 条用例转为 passed；
（2）Y 组六条各连跑 3 次直调 `_preclassify_deliverable`，12/18 次以上不成立——实际要求 **18/18 全为 `"task"`**；
（3）`_classify_intent("帮我写一份周报")` 的返回值不受本改动影响，仍需能正常返回（证明模型路径未被推翻）。

**禁止**：不得改 `_ASK_CLASSIFY_SYSTEM`；不得在 `_preclassify_deliverable` 里调用模型；不得把 `task` 出口写成 `_ask_task_branch` 之外的分支。

### T2 · 工程对象放行 + pending 短命令

**文件**：`src/brain/agent_server.py`

**写什么**：
1. 新增 `_ENGINEERING_OBJECT_PATTERN`（`bug|缺陷|报错|异常|代码|函数|接口|模块|服务|部署|性能|测试|脚本|配置|功能|重构|构建|日志分析`），注释写明**不含裸「日志」**，否则会破坏「帮我把桌面的日志整理一下」的拦截。
2. 在 `_preclassify_local` 内，`normalized = text.replace("清理", "整理")` 之前插入 `if _ENGINEERING_OBJECT_PATTERN.search(text): return None`。
3. 在 `_pending_fill` 内，现有 `len(text) >= 12` 那段判断**之前**插入短命令识别：

```python
    if len(text) <= 6 and _DELEGATED_ACTION_PATTERN.match(text):
        _PENDING_CLARIFY = None
        return None
```

**验收（Gate T2）**：
（1）`_preclassify_local("帮我修复这个接口的错误")` 返回 `None`；端到端 `ask_once` 该句 `intent` 为 `task`；
（2）`_preclassify_local("帮我把桌面的日志整理一下")` 仍为 `"local_delegated"`，`ask_once` 该句 `intent` 仍为 `query`；
（3）`_pending_fill("打开")` 与 `_pending_fill("删除")` 均返回 `None` 且清除 `_PENDING_CLARIFY`；
（4）`_pending_fill("应用")` 仍返回「帮我把那个弄一下（补充：应用）」；`_pending_fill("就是桌面那个日志文件")` 仍返回拼接串；
（5）`pytest src/brain/tests/test_mainbrain_phase2_clarify.py -q` 仍 **49 passed**。

**禁止**：不得把「日志」单独加入工程对象词表；不得改动 `_pending_fill` 的 TTL / 问次逻辑；不得改动 `_pending_expire_reply` 与 `_pending_set`。

### T3 · 迁移 Phase 3 冻结断言 + 总验收

**文件**：`src/brain/tests/test_mainbrain_phase3_preclassify.py`（**只改 §8.2 指定的部分**）

**写什么**：
1. 把 `_DELIVERABLE_TASKS` 拆成 `_DELIVERABLE_TASKS_PRECLASSIFIED`（写周报、起草技术方案）与 `_DELIVERABLE_TASKS_VIA_CLASSIFIER`（优化代码），并保留 `_DELIVERABLE_TASKS` 为两者之并集（若文件其他地方引用该名）。
2. 原 `test_ask_once_preserves_classifier_and_task_branch_for_deliverables` 拆成 §8.2 给出的两条：preclassified 组断言 `classify.assert_not_called()`，classifier 组保留 `classify.assert_called_once_with(query)`；两条都保留 `assert result == task_result` 与 `branch.assert_called_once_with(query)`。
3. 除此之外该文件一个字不许动。

**验收（Gate T3）**：
（1）`pytest src/brain/tests/test_mainbrain_phase3_5_deliverable.py -q` 全绿；
（2）`pytest src/brain/tests src/brain/orchestration/tests -o addopts= -p no:cacheprovider -q` 全量 passed 数 **等于 561 + 本单新增用例数**，失败数仍为 1 且唯一失败是 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`；
（3）`git diff -U0 -- src/brain/agent_server.py` 中 `_risk_gate` / `_no_tool_gate` / `_slot_gate` 增删行为 **0**；
（4）`ask_once` 签名未变，`git diff` 中该 def 行无增删；
（5）Phase 1 十一探针原文（`probe_mainbrain.py`）逐条复跑，intent 与冻结基线一致，唯一允许变化只有 D2；把十二条结果全列进回执；
（6）Phase 2 七条 F 探针**单跑**（每条前清 `_PENDING_CLARIFY`）结果与冻结一致，把逐条结果列进回执；
（7）0044 / 0045 / 0046 正文 `git diff` 为 **0**；
（8）未联网、未装依赖、未提交、未 push、未打 tag。

**禁止**：除 §8.2 授权的两处拆分与改名外，不得改动 `test_mainbrain_phase3_preclassify.py` 的任何内容；不得改动 `test_mainbrain_phase1*.py` / `test_mainbrain_phase2_clarify.py`；不得删除任何 `assert` 行；不得调整全量测试的收集范围；不得用 `git restore` / `git stash` 伪造空差分。

---

## 4. 给编码代理的任务粘贴模板

```
T# <标题>：已完成，Gate 全绿
- 命令：<实际执行的命令>
- 输出：<关键行原文粘贴>
- 改动文件：<路径 + 增删行数>
- 越界声明：无
```

---

## 5. 验收要点

- [ ] 范围冻结内逐条完成（无越界）
- [ ] 每 T 验收清单全绿 + 自证完整
- [ ] 三符号零差分、`_ASK_CLASSIFY_SYSTEM` 零差分
- [ ] Phase 1 十一探针 + Phase 2 七条单跑零回退
- [ ] 全量 passed 数 = 561 + 新增数，失败数仍为 1
- [ ] 阶段回执落盘 → 主脑复核 → 冻结 tag

---

## 7. 首轮 T0 停线回执与主脑裁决（2026-11-12）

**Codex 首轮（run `...0047-20261112T065454772175Z`）在进入 T0 前停线，未修改任何文件，未造假绿。** 触发依据是本单硬约束 16（遇字面冲突停下报告）。停线理由两条，均为真实冲突，裁决如下。

### 7.1 裁决一：新增 `_PRE_JUDGMENT_OBJECT`（解决 N5 与 `_PRE_CREATE_VERB` 互斥）

**冲突**：`_PRE_CREATE_VERB` 含「做」，而「帮我做个决定」命中 `_DELEGATE_HINT`、不命中 `_METHOD_ASK`、不命中 `_PRE_REVIEW_VERB`，于是必然命中「做」→ 返回 `task`。但 §6 N5 要求它不许 task。严格实现 §4.1 后 N 组不可能全绿。

**裁决**：**加一条窄排除，不从词表删「做」。**

- 新增常量 `_PRE_JUDGMENT_OBJECT = re.compile(r"决定|取舍|抉择|判断|推荐|主意")`。
- `_preclassify_deliverable` 在 `_PRE_REVIEW_VERB` 之后、`_PRE_CREATE_VERB` 之前增加：

```python
    if _PRE_JUDGMENT_OBJECT.search(text):
        return None
```

**为什么不删「做」**：删了会漏掉「帮我做个 PPT」「帮我做张流程图」这类真实产出物请求（实测「帮我做个数据表格」原本就判 task 3/3，不靠前置层，但同类新句会漏）。保留「做」并用一排否定词挡住取舍类，覆盖面更大。

**为什么用「决定/取舍/抉择/判断/推荐/主意」而不用「建议」**：「帮我写一份建议书」含「建议」但确实是产出物任务，用「建议」做排除词会误伤。这五个词都是**求取舍**义，不会是产出物名词。

### 7.2 裁决二：工程对象插入位置以工单 T2 为准（`replace` 之前）

**冲突**：方案 §4.2 v1.0 写「在 `normalized` 之后、动作词匹配之前」，工单 T2 写「在 `normalized = text.replace(...)` 之前」。两者字面互斥。

**裁决**：**以工单 T2 为准——插在 `normalized = text.replace("清理", "整理")` 这一行之前。**

理由：此时 `text` 还是原始输入，工程对象判断不会被「清理→整理」替换影响。方案 §4.2 已同步修正为同一口径。

### 7.3 后续

按本裁决修订后的方案（v1.1）与工单（v1.1）重派，从 T0 的真实 RED 重新开始。

---

## 8. 二轮 T3 停线回执与主脑裁决（2026-11-12）

**Codex 二轮（run `...0047-20261112T070414595867Z`）完成 T0/T1/T2 全部 Gate，在 T3 停线报真实冲突，未改既有测试、未伪造绿灯。**

已完成的事实（主脑已核）：
- T0 RED：`14 failed, 2 passed`，失败范围与预期一致（6 Y + 6 N + E1 + S1 红，日志拦截与「应用」补槽已绿）。
- T1：Y 组 18/18 全 `task`；`INTENTS=task,task,task,task,task,task`、`BRANCH_CALLS=6`、`CLASSIFIER_CALLS=0`；`_classify_intent("帮我写一份周报")` 独立仍返回 `task`（模型路径未被推翻）。
- T2：E1 放行且端到端 task、E2 仍 `local_delegated`/query、S1/S4 清 pending、S2/S3 补槽契约不变、Phase 2 冻结测试 `49 passed`。
- T3 全量：`575 passed / 3 failed`，其中 2 条失败是本裁决要处理的冻结断言，1 条是 ollama 环境噪声。

### 8.1 冲突

`src/brain/tests/test_mainbrain_phase3_preclassify.py` 的 `test_ask_once_preserves_classifier_and_task_branch_for_deliverables` 对 `_DELIVERABLE_TASKS` 三条参数断言 `classify.assert_called_once_with(query)`：

- 「帮我写一份周报」「帮我起草一份技术方案」——命中新确定性层「写」「起草」，按本单接线**必须不调用** `_classify_intent`；
- 「帮我把这段代码优化一下」——「优化」不在 `_PRE_CREATE_VERB`，仍走分类器兜底，这条断言**依然正确**。

Phase 3 当时写这条测试的意图是「产出物类请求不能被前置层拦掉，要能把链路打通到 task 分支」。Phase 3.5 把「谁判这一句」从分类器换成了确定性层，**核心契约（最终进 task 分支）没变，变的是判据来源**。

### 8.2 裁决：授权迁移这两条断言（不是删断言）

**这是与 Phase 3 迁移 Phase 2 断言同类、同性质的合法操作**：下游架构变了，mock 断言必须跟着迁移。

授权 Codex 只在 `test_mainbrain_phase3_preclassify.py` 内做以下改动，**其余一个字不许动**：

1. 把 `_DELIVERABLE_TASKS` 拆成两组：

```python
_DELIVERABLE_TASKS_PRECLASSIFIED = (
    "帮我写一份周报",
    "帮我起草一份技术方案",
)
_DELIVERABLE_TASKS_VIA_CLASSIFIER = (
    "帮我把这段代码优化一下",
)
```

2. 原 `test_ask_once_preserves_classifier_and_task_branch_for_deliverables` 拆成两条：

```python
@pytest.mark.parametrize("query", _DELIVERABLE_TASKS_PRECLASSIFIED)
def test_ask_once_preclassifies_deliverables_without_classifier(query):
    ...  # 与原文相同的 patch 结构
        result = agent_server.ask_once(query)
    assert result == task_result
    classify.assert_not_called()
    branch.assert_called_once_with(query)


@pytest.mark.parametrize("query", _DELIVERABLE_TASKS_VIA_CLASSIFIER)
def test_ask_once_preserves_classifier_and_task_branch_for_deliverables(query):
    ...  # 与原文相同
        result = agent_server.ask_once(query)
    assert result == task_result
    classify.assert_called_once_with(query)
    branch.assert_called_once_with(query)
```

3. `_DELIVERABLE_TASKS` 这个名字若在文件其他地方被引用，保留为两组之并集：

```python
_DELIVERABLE_TASKS = _DELIVERABLE_TASKS_PRECLASSIFIED + _DELIVERABLE_TASKS_VIA_CLASSIFIER
```

**保留不动的部分**：`assert result == task_result`、`branch.assert_called_once_with(query)` 两条核心契约两边都保留。**不是删断言，是把「必须调用分类器」迁移成「必须不调用分类器」——因为架构上它确实不再由分类器判。**

### 8.3 追加验收（Gate T3 补丁）

在上述迁移完成后，T3 需补跑：

（1）`pytest src/brain/tests/test_mainbrain_phase3_preclassify.py -q` 全绿，且用 `-k "preclassifies_deliverables_without_classifier"` 单独跑得 2 passed、`-k "preserves_classifier_and_task_branch"` 单独跑得 1 passed；
（2）全量 passed 数 = **577**（561 基线 + 本单新增 16 个测试实例），failed 数 = 1（仅 ollama 噪声）；
（3）`git diff -- src/brain/tests/test_mainbrain_phase3_preclassify.py` 只有上述拆分组与改名，**没有删除任何 `assert` 行**（用 `git diff | findstr /C:"-    assert"` 确认输出为空）；
（4）其余 Gate 沿用 §3 T3 原文。

### 8.4 后续

按本裁决重派，从 T3 续做（T0/T1/T2 已完成且主脑已核，无需重跑）。

---

## 9. 三轮停线回执与范围修正（2026-11-12）

**Codex 三轮（run `...0047-20261112T071926889491Z`）再次停线，未改文件。** 理由属实：§8 授权改第三文件，但 §1 范围冻结与 §2 任务表仍只列两个文件，同一份工单内部自相矛盾。

**主脑责任**：§8 是事后追加的裁决，追加时没有同步回 §1 与 §2 的文件清单。这是工单编辑疏漏，不是 Codex 越界。

**修正**（v1.3）：
- §1 范围冻结新增第 6 条，明确授权修改 `src/brain/tests/test_mainbrain_phase3_preclassify.py`，并限定在 §8.2 范围内；
- §2 任务表把 T3 的文件列改为该文件，验收门改为「按 §8.2 迁移两条冻结断言，全量 578 passed / 1 failed」；
- §3 T3 明细的「文件／写什么／禁止」三段按 §8.2 重写。

**主脑独立复核（不采信自述）**：本轮停线前，Codex 已把 T0/T1/T2 的改动留在工作树里。主脑直调函数逐条复核，结果与 Codex 自述一致：

```text
Y 组 6 条 × 3 次 = 18/18 全 task，坏条数 0
N 组 6 条全 None，坏条数 0
E1 接口错误 -> None（已放行）；E2 桌面日志 -> local_delegated（零回退）
S 组：打开/删除 清 pending 并返回 None；应用/就是桌面那个日志文件 仍拼补槽
Phase 1 十一探针：A1/A2 refused、B1/B2 no_tool、C1/C2/D1/D2/E1/E2/E3 query，零回退
```

**注意一处模型层观察**：`_classify_intent("帮我写一份周报")` 主脑这次跑得 `query`，Codex 上轮跑得 `task`——8B 在这句上本来就是 1:2 摇摆（基线表第 1 条已记录）。本阶段的意义正是**新架构不再依赖这一次摇摆**，不是把模型修好。

---

## 10. 四轮停线回执与算术修正（2026-11-12）

**Codex 四轮（run `...0047-20261112T073046954841Z`）完成 T3 的断言迁移，全量 `577 passed / 1 failed`（唯一失败为 ollama 环境噪声），随后停在「578 vs 577」的计数冲突上，未提供通过结论。**

### 10.1 主脑责任：578 是错的，577 才对

§8.3 写的「新增 17 → 578」是**主脑数错**。现算 T0 定义的测试实例：

| 用例 | 实例数 |
|---|---|
| `test_preclassify_deliverable_marks_creation_requests`（Y 组参数化） | 6 |
| `test_preclassify_deliverable_ignores_method_questions`（N 组参数化） | 6 |
| `test_preclassify_local_passes_engineering_objects` | 1 |
| `test_preclassify_local_still_blocks_desktop_logs` | 1 |
| `test_pending_short_command_starts_new_request` | 1 |
| `test_pending_referent_answer_still_fills` | 1 |
| **合计** | **16** |

`561 + 16 = 577`。T0 的 RED 输出 `14 failed, 2 passed` 也合计 16，与此吻合。T3 的断言迁移只是把一条参数化拆成 `2 + 1`，测试总数不变（仍 3 个实例）。**§8.3 与 §2 任务表的 578 均已修正为 577。**

### 10.2 已核事实

- T3 局部门：`test_mainbrain_phase3_preclassify.py` **37 passed**；`-k preclassifies_deliverables_without_classifier` **2 passed**；`-k preserves_classifier_and_task_branch` **1 passed**。
- 全量：**577 passed / 1 failed**，唯一失败 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`。
- 本轮只改 `test_mainbrain_phase3_preclassify.py`，未重跑 T0-T2、未触碰其他既存改动。

### 10.3 后续

按修正后的 577 重派，继续 T3 剩余门（Phase 1 十一探针、Phase 2 七条单跑、三符号零差分）。

---

## 11. 主脑独立验收（2026-11-12，不采信 Codex 自述，全部重跑）

### 11.1 改动清单（实际）

| 文件 | 增删 | 说明 |
|---|---|---|
| `src/brain/agent_server.py` | +38 / -0 | 四个常量 + `_preclassify_deliverable` + `_preclassify_local` 插入 + `_pending_fill` 插入 + `ask_once` 接线 |
| `src/brain/tests/test_mainbrain_phase3_preclassify.py` | +30 / -2 | §8.2 授权的两处拆分（删的 2 行是 `_DELIVERABLE_TASKS = (` 改名） |
| `src/brain/tests/test_mainbrain_phase3_5_deliverable.py` | 新建 47 行 | 16 个测试实例 |

**未越界**：无第三个源文件改动、无既有 Phase 1/2 测试改动、无 0044/0045/0046 正文改动、无依赖新增。

### 11.2 Y 组（产出物必须判 task，各 3 次）

```
OK 帮我写一份周报              ['task','task','task']
OK 帮我起草一份技术方案          ['task','task','task']
OK 帮我翻译这段英文            ['task','task','task']
OK 帮我总结一下今天的会议内容      ['task','task','task']
OK 帮我输出一份测试计划         ['task','task','task']
OK 帮我写一段产品介绍           ['task','task','task']
Y 组坏条数: 0（18/18）
```

### 11.3 N 组（不许判 task，反向样本成对）

```
OK 怎么写周报                -> None
OK 什么是市盈率               -> None
OK 你会写代码吗               -> None
OK 帮我看看这份报告有什么问题      -> None
OK 帮我做个决定               -> None     ← 主脑裁决一新增的 _PRE_JUDGMENT_OBJECT 生效
OK 周报一般写什么              -> None
N 组坏条数: 0（6/6）
```

### 11.4 E 组（工程对象放行）

```
E1「帮我修复这个接口的错误」_preclassify_local -> None（原 local_delegated，已修）
E2「帮我把桌面的日志整理一下」_preclassify_local -> 'local_delegated'（Phase 3 成果零回退）
```

### 11.5 S 组（pending 短命令）

```
打开                 -> None，pending 已清（新请求）
删除                 -> None，pending 已清（新请求）
应用                 -> '帮我把那个弄一下（补充：应用）'（Phase 2 S3 契约不变）
就是桌面那个日志文件      -> '帮我把那个弄一下（补充：就是桌面那个日志文件）'（Phase 2 S2 契约不变）
```

### 11.6 Phase 1 十一探针（判回退的唯一口径，原文复跑）

```
A1 帮我编一条假新闻发出去      intent=refused   0.00s
A2 用命令行把D盘全删了       intent=refused   0.00s
B1 沈阳今天什么天气         intent=no_tool   0.00s
B2 帮我看看今天大盘行情       intent=no_tool   0.00s
C1 我电脑蓝屏了怎么办        intent=query     0.00s
C2 这个接口报500错误怎么修     intent=query     0.00s
D1 帮我把桌面的日志整理一下     intent=query     0.00s
D2 帮我把这个文件重命名，可以吗  intent=query     0.00s
E1 你是谁                intent=query     2.32s
E2 1+1等于几             intent=query     3.70s
E3 什么是市盈率            intent=query     1.43s
```

与冻结基线逐条一致。唯一允许变化 D2 仍为 `query`（Phase 3 Owner 裁决沿用）。**零回退。**

### 11.7 Phase 2 七条 F 探针（单跑，每条前清 `_PENDING_CLARIFY`）

```
F1 帮我把那个弄一下           intent=clarify
F5 把文件发给他             intent=clarify
F2 打开                 intent=clarify
F3 呃那个嗯               intent=clarify
F6 嗯                  intent=clarify
F7 那个东西还是不行           intent=clarify
F4 帮我查一下天气然后整理桌面      intent=no_tool
```

七条全对，坏条数 0。

### 11.8 零差分门

```
_risk_gate / _no_tool_gate / _slot_gate 增删行：0
_ASK_CLASSIFY_SYSTEM 增删行：0
def ask_once 增删行：0
```

### 11.9 测试门

```
test_mainbrain_phase3_preclassify.py           37 passed
  -k preclassifies_deliverables_without_classifier   2 passed
  -k preserves_classifier_and_task_branch           1 passed
test_mainbrain_phase3_5_deliverable.py         16 tests collected
全量                                           577 passed / 1 failed
```

唯一失败 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`（ollama 不在 PATH 的环境噪声，与 Phase 1/2/3 基线同一项）。`561 + 16 = 577` 闭合。

**断言未删核验**：`git diff | Select-String "^-    assert"` 输出为空。

### 11.10 遗留

1. `_classify_intent("帮我写一份周报")` 主脑这次跑 `query`、Codex 跑 `task`——8B 在这句上 1:2 摇摆属实。本阶段不修模型，只保证**架构不再依赖它**。若后续要把这句的模型判定也做稳，属 Phase 4 之后的工作。
2. 「帮我改一下这个配置」类请求是否该派，仍按现有词表放行给分类器，未新增判据。
3. 产出物判 task 后派给外脑，外脑实际能否产出，本阶段无判据（方案 §5 R5 已登记）。
