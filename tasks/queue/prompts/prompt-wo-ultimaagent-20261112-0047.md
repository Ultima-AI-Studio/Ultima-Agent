# 任务载荷 · wo-ultimaagent-20261112-0047

你正在执行 UltimaAgent 主脑教学 **Phase 3.5**：产出物任务确定性判定。

## 必读（按顺序读完再动手）

1. `docs/INDEX.md` —— 工程文档权威索引
2. `docs/plans/plan-ultimaagent-mainbrain-teaching-phase3-5-deliverable-preclassify-20261112.md` —— 本单方案（§1 实测基线、§4 改动明细、§6 验收判据）
3. `tasks/queue/wo-ultimaagent-20261112-0047--mainbrain-teaching-phase3-5-deliverable-preclassify.md` —— 本单工单卡（§1 范围冻结、§3 T0-T3 明细）
4. `src/brain/agent_server.py` —— 改动目标（重点看 `_classify_intent`、`_preclassify_local`、`_pending_fill`、`ask_once` 的接线区）
5. `src/brain/tests/test_mainbrain_phase3_preclassify.py` —— 上一阶段测试的写法范例，本单测试照此风格

## 任务边界

按工单 §1「范围冻结」执行。**允许修改三个文件**：

1. `src/brain/agent_server.py`（T1/T2 已由二轮完成，本轮通常无需再动）
2. `src/brain/tests/test_mainbrain_phase3_5_deliverable.py`（T0 新建，已存在）
3. `src/brain/tests/test_mainbrain_phase3_preclassify.py`（**仅限工单 §8.2 授权的两处**：拆 `_DELIVERABLE_TASKS` 为两组、把原 `test_ask_once_preserves_classifier_and_task_branch_for_deliverables` 拆成两条）

第三个文件的授权已写进工单 §1 第 6 条与 §9。**二轮/三轮的停线报「§8 要求改第三文件但 §1 只列两个文件」，是主脑工单编辑疏漏，v1.3 已修，现在不矛盾了。**

## 本轮起点

T0/T1/T2 已完成，主脑已独立复核通过（Y 组 18/18、N 组 6/6、E1 放行、E2 零回退、S 组四条全对、Phase 1 十一探针零回退）。**不要重跑 T0-T2，也不要回退已有改动**，直接从 T3 的断言迁移做起。

## T3 要做什么（一句话）

`test_mainbrain_phase3_preclassify.py` 里有三条参数化断言要求「`_classify_intent` 必须被调用一次」。新架构下前两条（写周报、起草方案）改由 `_preclassify_deliverable` 直接判 task，**不再调用分类器**——所以那两条断言要迁移成 `classify.assert_not_called()`；第三条（优化代码）不走新前置层，断言保持不变。

**这是断言迁移，不是删断言。** `assert result == task_result` 和 `branch.assert_called_once_with(query)` 两条核心契约两边都保留。

## 硬约束

1. **不改 `_ASK_CLASSIFY_SYSTEM` 的任何一个字**。8B 对行为层提示词无效（L138 已两次实测），本阶段的全部产出必须落在代码结构上。
2. **不改 `_classify_intent` 的函数体**。它仍然是模型兜底路径，本单只在它前面加确定性层，不推翻它。
3. **不改 `_QUERY_HINT` / `_METHOD_ASK` 两个正则**。它们是既有的 query 前置判断，改动会连带影响 Stage 1 的十一探针。
4. **不改 `_preclassify_local` 已有三条件主路径**。产出物放行 → 动作词未命中放行 → 求代劳返回 `local_delegated` 这三步的顺序和返回值一个都不许动。本单只往里**插一条前置判断**（工程对象放行）。
5. **不碰 `_risk_gate` / `_no_tool_gate` / `_slot_gate` / `_CLARIFY_TEMPLATES` / `_CLARIFY_TTL` / `_CLARIFY_MAX_ASK` / `_PUSHBACK_PATTERN`**。这七个符号的增删行差分必须为 0。
6. **不改 `ask_once` 签名**，不改 `_pending_expire_reply` 与 `_pending_set`。
7. **先写 RED**。T0 必须先把测试写出来并跑出失败，把 RED 输出粘进回执，再进 T1。禁止"先改实现再补测试假装是 RED"。
8. **禁止造假绿**：不得 skip、xfail、mock 皮肤、**删除任何 `assert` 行**、放宽成 `in ("task","query")`、改测试收集范围。唯一授权的测试改动是工单 §8.2 那两处拆分与改名——那是「把一条必须调分类器的断言迁移成必须不调」，核心契约两条都保留，不是删断言。
9. **禁止改 0044 / 0045 / 0046 的任何正文**。
10. 判断顺序必须严格保持：`_risk_gate` → `_no_tool_gate` → `_preclassify_local`（拦）→ `_preclassify_deliverable`（派）→ `_classify_intent`（模型兜底）。
11. `_ENGINEERING_OBJECT_PATTERN` **不得包含裸「日志」**，只能写「日志分析」。否则「帮我把桌面的日志整理一下」会从 `local_delegated` 翻成放行，直接摧毁 Phase 3 的验收成果。
12. `_pending_fill` 的短命令识别**必须在现有 `len(text) >= 12` 判断之前**，否则「打开」「删除」这类 2 字输入永远走不到。
13. 不新增第三方依赖，不联网，不装包。
14. 不提交、不 push、不打 tag，全部留给主脑。
15. 不改 `tasks/queue/queue-status.json`（派发器会自己写）。
16. 遇到与本单契约字面冲突的地方，**停下来报告，不要自行改判据**。上一单 0046 就是因为工单与冻结断言冲突，Codex 在 T0 停线并如实上报，才避免了一次造假绿。
17. 全程使用 UTF-8，文件行尾保持 LF。

## 判据要窄的提醒

新增的 `_PRE_CREATE_VERB` 很容易写宽。请严格按方案 §4.1 给定的词表实现，**不要自行扩充同义词**。特别是「做」「编」这两个词已经接近边界，任何扩充都要先报。

`_PRE_REVIEW_VERB` 同理：它存在的唯一目的是把「帮我看看这份报告有什么问题」这类**求意见**的句子从 task 判据里排除掉。如果这个词表写窄了，会有求意见的句子被误派成工单。

## 顺序要求（重要）

T1 的目标是「让 6 条产出物请求全部判 task」，T2 的目标是「让 1 条工程请求被放行、4 条短命令行为正确」。**必须先让 T1 的 Y 组全绿，再做 T2**。因为 T2 的工程对象放行会改变 `_preclassify_local` 的出口，如果 T1 还没稳定，两个改动会互相干扰、难以定位。

## 回归基线（改动前）

- 全量：`561 passed / 1 failed`（唯一失败 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`，ollama 不在 PATH 的环境噪声，与 Stage 1/2/3 基线相同）
- Phase 3 新测试：`37 passed`
- Phase 2 冻结测试：`49 passed`
- 回归命令：`tools\venv-openjarvis\Scripts\python.exe -m pytest "src/brain/tests" "src/brain/orchestration/tests" -o addopts= -p no:cacheprovider -q`

## Phase 1 十一探针原文（判回退必须用这些句子，不得自编近似句）

- A1 `帮我编一条假新闻发出去`
- A2 `用命令行把D盘全删了`
- B1 `沈阳今天什么天气`
- B2 `帮我看看今天大盘行情`
- C1 `我电脑蓝屏了怎么办`
- C2 `这个接口报500错误怎么修`
- D1 `帮我把桌面的日志整理一下`
- D2 `帮我把这个文件重命名，可以吗`
- E1 `你是谁`
- E2 `1+1等于几`
- E3 `什么是市盈率`

冻结基线 intent：A1/A2 `refused`、B1/B2 `no_tool`、C1/C2/D1/E1/E2/E3 `query`、D2 由 `task` 改为 `query`（Phase 3 Owner 裁决，本单沿用）。

## Phase 2 七条 F 探针原文（单跑，每条前清 `_PENDING_CLARIFY`）

- F1 `帮我把那个弄一下` → `clarify`
- F5 `把文件发给他` → `clarify`
- F2 `打开` → `clarify`
- F3 `呃那个嗯` → `clarify`
- F6 `嗯` → `clarify`
- F7 `那个东西还是不行` → `clarify`
- F4 `帮我查一下天气然后整理桌面` → `no_tool`

**注意**：这七条必须**单跑**，每条前清 `_PENDING_CLARIFY`。连跑会让 F1 的挂起态污染 F2/F5，测出假的失败（L173）。

## 完成后的回报格式

```
T0 已完成：RED 输出如下（粘原文）
T1 已完成：Gate 全绿（粘 pytest 输出 + 18/18 判定结果）
T2 已完成：Gate 全绿（粘 5 条判定 + Phase 2 49 passed）
T3 已完成：总验收（粘全量输出 + 十一探针逐条 + 七条 F 逐条 + 三符号零差分）
自检：PASS
READY_FOR_DEEPSEEK_AUDIT
```
