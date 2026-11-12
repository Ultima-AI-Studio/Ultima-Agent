# 主脑教学 Phase 3.5 · 产出物任务确定性判定

> 版本：v1.1 ｜ 日期：2026-11-12 ｜ 前置：Phase 3 已冻结（tag `ultimaagent-mainbrain-teaching-phase3-20261112` / commit `9bc8e4a5`）
> 依据：Phase 3 工单 0046 §9.9 遗留项 1、2；Phase 2 方案 §7「Phase 5」原规划

---

## 0. 一句话

Phase 3 解决了「该拦的挡住了」，本阶段解决它的另一面：**该派的活要派出去**。

Phase 3 的前置层把求代劳类请求挡住后，产出物类请求被放行给 `_classify_intent`，而分类器把「帮我写一份周报」「帮我起草一份技术方案」稳定判成 query——用户说要干一件活，主脑回「您需要什么格式」。这不是模型抖动，是**判据语义覆盖不全**。

---

## 1. 实测基线（2026-11-12，直调函数，非推演）

### 1.1 产出物任务：`_classify_intent` 各跑 3 次

| # | 输入 | 结果 | 判定 |
|---|---|---|---|
| 1 | 帮我写一份周报 | `{task:1, query:2}` | ❌ 摇摆 |
| 2 | 帮我起草一份技术方案 | `{query:3}` | ❌ 稳定不派 |
| 3 | 帮我写一段产品介绍 | `{query:3}` | ❌ 稳定不派 |
| 4 | 帮我拟一份会议纪要 | `{task:3}` | ✅ |
| 5 | 帮我做个数据表格 | `{task:3}` | ✅ |
| 6 | 帮我翻译这段英文 | `{query:3}` | ❌ 稳定不派 |
| 7 | 帮我分析一下这次活动的转化数据 | `{task:3}` | ✅ |
| 8 | 帮我总结一下今天的会议内容 | `{query:3}` | ❌ 稳定不派 |
| 9 | 帮我输出一份测试计划 | `{query:3}` | ❌ 稳定不派 |
| 10 | 给我写一封邮件草稿 | `{task:3}` | ✅ |

**10 条坏 6 条**，且坏的那 6 条中 5 条是 `query:3` **稳定错误**——不是随机抖动，跑多少次都一样。

### 1.2 规律（关键，决定了修法）

把结果按动词分类，界限极其清晰：

| 动词 | 结果 | 是否在 `_ASK_CLASSIFY_SYSTEM` 的「动手」枚举里 |
|---|---|---|
| 拟 / 做 / 分析 | `task` | 「制作」在内，「分析」也不在但模型认 |
| 写 / 起草 / 翻译 / 总结 / 输出 | `query` | **全部不在** |

`_ASK_CLASSIFY_SYSTEM`（L868-873）原文把「动手」限定为：

> 改代码、修功能、开发、制作、设计、接入、优化

**「写文档 / 起草方案 / 翻译 / 总结 / 输出」一个都没进这个枚举。** 8B 严格按字面匹配：命中枚举的判「动手」，没命中的判「回答」。所以「做个数据表格」因为沾了「制作」而通过，「写一份周报」因为「写」不在表里而被判成「回答」。

这不是提示词写得不够好，是**判据的语义覆盖面本身缺了一整类**。按主线原则（代码结构性改造，不调提示词——L138 已两次证明行为层提示词对 8B 无效），本阶段用确定性前置层在分类器之前判掉这一类，不碰提示词。

### 1.3 工程对象被前置层误拦

`_preclassify_local` 实测（`None` = 放行，`local_delegated` = 拦截）：

| 输入 | 结果 | 判定 |
|---|---|---|
| 帮我改一下这个bug | `None` | ✅ |
| 帮我修复这个接口的错误 | `local_delegated` | ❌ **真误拦** |
| 帮我重构这段代码 | `None` | ✅ |
| 帮我加一个功能 | `None` | ✅ |
| 帮我改一下这个配置 | `None` | ✅ |
| 帮我删掉这段代码 | `None` | ✅ |

只有第 2 条被拦。原因在 `_CLAIM_ACTIONS` 的词表细节：里面是「改好」不是「改」，是「修复」。「改一下」匹配不到「改好」所以漏过，「修复」精确命中所以被拦。**同一个意思，两种处置，取决于词表里恰好有哪个词形。**

### 1.4 对照组（不许误判成 task，实测全部正确）

| 输入 | 结果 |
|---|---|
| 什么是市盈率 | `query` ✅ |
| 怎么写周报 | `query` ✅（`_METHOD_ASK` 生效） |
| 周报一般写什么 | `query` ✅ |
| 你会写代码吗 | `query` ✅ |
| 帮我看看这份报告有什么问题 | `query` ✅ |

### 1.5 pending 下短命令被当补槽

挂起「帮我把那个弄一下」后，`_pending_fill` 实测：

| 轮 2 输入 | 当前结果 | 应该 |
|---|---|---|
| 打开 | `帮我把那个弄一下（补充：打开）` | ❌ 这是新请求 |
| 删除 | `帮我把那个弄一下（补充：删除）` | ❌ 这是新请求 |
| 应用 | `帮我把那个弄一下（补充：应用）` | ✅ 有效补槽 |
| 就是桌面那个日志文件 | `帮我把那个弄一下（补充：就是桌面那个日志文件）` | ✅ 有效补槽 |

根因在 `_pending_fill` 的新请求识别条件：`len(text) >= 12 and (帮我|请你|麻烦|把|将) and 动作词`。「打开」「删除」只有 2 字，三条全部不满足，于是掉进补槽分支。拼出来的串 `combined_query != None` 会让槽位门被强制跳过（`ask_once` L1328），直接进分类器判 task 派单——**问了一圈「哪个」，用户说「打开」，主脑派了个没有宾语的活。**

---

## 2. 病灶清单

| 编号 | 病灶 | 影响 | 严重度 |
|---|---|---|---|
| **P1** | 产出物创作（写/起草/翻译/总结/输出）稳定判 query | 用户说要干活，主脑回「您需要什么格式」，活干不成 | **高** |
| **P2** | 「修复 + 工程对象」被前置层误拦 | 该派的技术活被挡成「做不到」 | 中 |
| **P3** | pending 下含动作词的短命令被当补槽 | 拼出无语义的请求直接派单 | 中 |

---

## 3. 范围冻结

**本阶段只做**：
1. 新增 `_preclassify_deliverable(query)`，在 `_preclassify_local` 之后、`_classify_intent` 之前接线；命中产出物创作则确定性返回 `task`。
2. 新增 `_ENGINEERING_OBJECT_PATTERN`，在 `_preclassify_local` 内先判：命中工程对象词则放行（返回 `None`），不让本机动作词词表误伤技术任务。
3. 修 `_pending_fill` 的新请求识别：含动作词且长度 ≤6 的短命令判为新请求，清除 pending。

**本阶段不做**（Non-goals）：
- 不改 `_ASK_CLASSIFY_SYSTEM` 的任何一个字（提示词路线，L138 已证无效）
- 不改 `_classify_intent` 的函数体、不改它的 `_QUERY_HINT` / `_METHOD_ASK` 两个前置判断
- 不改 `_preclassify_local` 已有的三条件主路径（产出物放行 → 动作词未命中放行 → 求代劳返回 local_delegated）
- 不碰 `_risk_gate` / `_no_tool_gate` / `_slot_gate` / `_CLARIFY_TEMPLATES` / `_CLARIFY_TTL` / `_CLARIFY_MAX_ASK`
- 不做主动回报节奏、不做多任务拆分（Phase 4）
- 不做 E1 人称错误、X4 翻译反问、`/health` provider_note（Phase 4b/4c）
- 不新增依赖、不改 `ask_once` 签名、不落盘 pending 状态

---

## 4. 改动明细

### 4.1 改动一：产出物确定性判 task

新增常量与函数：

```python
# 创造类动作词：产出物创作的最小动词集。
# 与 _PRE_DELIVERABLE_PATTERN（产出物名词：方案/报告/代码/文档/表格/计划）互补：
# 前者判「在造东西」，后者判「造的是什么」。
_PRE_CREATE_VERB = re.compile(r"写|起草|拟|翻译|总结|输出|产出|生成|做|制作|分析|汇总|整理成|编")

# 只「看/检查/审查/评估」的不是产出物创作，是求意见，必须留给模型回答。
_PRE_REVIEW_VERB = re.compile(r"看|检查|审查|评估|判断|评价|挑错|找问题")

# 「做个决定」「推荐几个方案」是求取舍意见，不是一个可派出去的产出物。
# 「做」在 _PRE_CREATE_VERB 里，单靠它会把「帮我做个决定」判成 task，
# 所以这一条是必需的窄排除，不是可选优化。
_PRE_JUDGMENT_OBJECT = re.compile(r"决定|取舍|抉择|判断|推荐|主意")

def _preclassify_deliverable(query: str) -> str | None:
    """识别"要我造一份东西"的求代劳请求，确定性判 task，绕开被枚举不全的分类器。"""
    text = (query or "").strip()
    if not text or "（补充：" in text:
        return None
    if not _DELEGATE_HINT.search(text):
        return None
    if _METHOD_ASK.search(text):
        return None
    if _PRE_REVIEW_VERB.search(text):
        return None
    if _PRE_JUDGMENT_OBJECT.search(text):
        return None
    if _PRE_CREATE_VERB.search(text):
        return "task"
    return None
```

四条排除的理由，逐条对应实测或契约：
- `_DELEGATE_HINT` 必须命中 —— 「你会写代码吗」不含，不能被判成要干活；
- `_METHOD_ASK` 必须不命中 —— 「怎么写周报」是问方法，实测已正确判 query，不能翻；
- `_PRE_REVIEW_VERB` 必须不命中 —— 「帮我看看这份报告有什么问题」是要意见，实测正确判 query，不能翻；
- `_PRE_JUDGMENT_OBJECT` 必须不命中 —— 「帮我做个决定」命中「做」但不是产出物，靠这一条挡住（0047 首轮 Codex 停线指出，属必需排除项）。

接线位置：`ask_once` 内，紧跟 `_preclassify_local` 的 `if` 之后、`_classify_intent` 之前。命中即走与 `task` 分支相同的出口 `_ask_task_branch(query)`。

### 4.2 改动二：工程对象不被本机动作词误伤

新增常量：

```python
# 工程对象词：出现这些词，说明是能派出去的技术活，不是本机 GUI/文件操作。
# 不含裸「日志」——「帮我把桌面的日志整理一下」必须仍被前置层拦住（Phase 3 成果）。
_ENGINEERING_OBJECT_PATTERN = re.compile(
    r"bug|缺陷|报错|异常|代码|函数|接口|模块|服务|部署|性能|测试|脚本|配置|功能|重构|构建|日志分析"
)
```

在 `_preclassify_local` 内插入，位置是 **`normalized = text.replace("清理", "整理")` 这一行之前**（此时 `text` 还是原始输入，工程对象判断不受清理/整理替换影响）：

```python
    if _ENGINEERING_OBJECT_PATTERN.search(text):
        return None
```

> 位置口径以本句为准。v1.0 初稿曾写成「normalized 之后」，与工单 T2 的「replace 之前」字面矛盾（0047 首轮 Codex 停线指出），已在此统一为 **replace 之前**。

效果：**「帮我修复这个接口的错误」由 `local_delegated` 改判为放行**，交给分类器判 task；同时「帮我把桌面的日志整理一下」不含工程对象词，仍被拦。

### 4.3 改动三：pending 下短命令判为新请求

`_pending_fill` 内，在现有新请求识别之前插入：

```python
    # 含动作词且很短（≤6 字）的是新命令，不是补槽。
    # 「打开」「删除」这种本身就是一个完整祈使句，拼进原请求只会造出无语义的串；
    # 「应用」「就是桌面那个日志文件」不含动作词，仍是有效补槽（Phase 2 S2/S3 契约不变）。
    if len(text) <= 6 and _DELEGATED_ACTION_PATTERN.match(text):
        _PENDING_CLARIFY = None
        return None
```

---

## 5. 边界与风险

| 编号 | 风险 | 处置 |
|---|---|---|
| R1 | `_PRE_CREATE_VERB` 里的「做」「编」过宽，可能把「帮我做个决定」判成 task | 保留 `_PRE_REVIEW_VERB`+`_METHOD_ASK` 双排除；实测样本必须包含「帮我做个决定」类反向样本 |
| R2 | `_ENGINEERING_OBJECT_PATTERN` 含「配置」「服务」，可能放行本该拦的本机操作 | 保留裸「日志」不进词表；「帮我把桌面日志整理一下」作为硬反向样本 |
| R3 | `_pending_fill` 短命令规则可能误伤 Phase 2 的 S3「应用」补槽 | 「应用」不含动作词，规则不命中；S3 用例必须在测试中保留并全绿 |
| R4 | 新增 `task` 出口后，`_claim_clean` 与未来态承诺剥离是否覆盖 task 分支出口 | task 分支话术是固定的 `_ASK_ACK_TEXT`，不含完成态声明，无需额外清洗；需在测试中断言出口文案 |
| R5 | 产出物判 task 后派给外脑，但外脑未必真能产出 | 本阶段只负责「该派的派出去」，产出质量属外脑职责，不在本阶段判据内 |

---

## 6. 验收判据（机检，可复现）

**Y 组 —— 产出物必须判 task 且真派单**
- Y1「帮我写一份周报」连跑 3 次，3/3 `intent=task`，且 `_ask_task_branch` 被调用
- Y2「帮我起草一份技术方案」3/3 `task`
- Y3「帮我翻译这段英文」3/3 `task`
- Y4「帮我总结一下今天的会议内容」3/3 `task`
- Y5「帮我输出一份测试计划」3/3 `task`
- Y6「帮我写一段产品介绍」3/3 `task`

**N 组 —— 不许误判成 task（反向样本，成对给出）**
- N1「怎么写周报」`query`
- N2「什么是市盈率」`query`
- N3「你会写代码吗」`query`
- N4「帮我看看这份报告有什么问题」`query`（求意见，不是产出）
- N5「帮我做个决定」`_preclassify_deliverable` 返回 `None`（前置层不许判 task）；端到端 `intent` 允许 `query` 或 `clarify`，**不许 `task`**
- N6「周报一般写什么」`query`

**E 组 —— 工程对象放行**
- E1「帮我修复这个接口的错误」`_preclassify_local` 返回 `None`，端到端 `task`
- E2「帮我把桌面的日志整理一下」仍 `local_delegated`（Phase 3 硬反向样本，零回退）

**S 组 —— pending 短命令**
- S1 挂起后输入「打开」→ 清除 pending，走新请求路径，最终 `clarify`（不是派单）
- S2 挂起后输入「应用」→ 仍为补槽，拼成 `...（补充：应用）`（Phase 2 契约）
- S3 挂起后输入「就是桌面那个日志文件」→ 仍为补槽（Phase 2 契约）
- S4 挂起后输入「删除」→ 清除 pending，走新请求路径

**R 组 —— 零回退**
- Phase 1 十一探针原文（`probe_mainbrain.py`）intent 与冻结基线一致，唯一允许变化仍只有 D2
- Phase 2 七条 F 探针**单跑**（每条前清 `_PENDING_CLARIFY`）结果与冻结一致
- `_risk_gate` / `_no_tool_gate` / `_slot_gate` 增删行差分 **0**
- 全量回归：基线 `561 passed / 1 failed`（唯一 ollama-not-in-PATH 环境噪声），本阶段新增测试后 passed 数应等于 `561 + 新增数`

---

## 7. 后续（不在本方案内）

- **Phase 4**：多任务拆分（F4 复合请求）+ 主动回报节奏
- **Phase 4b**：模型层反问（X4 类）+ E1 人称错误
- **Phase 4c**：`/health` 的 `provider_note` 文案校准

---

## 8. 变更记录

| 日期 | 版本 | 变更 |
|---|---|---|
| 2026-11-12 | v1.0 | 初版。基于 Phase 3 工单 0046 §9.9 遗留项 1、2 与 20 条实测样本（10 产出物 ×3 次、6 工程对象、5 对照、4 短命令） |
| 2026-11-12 | v1.1 | 采纳 0047 首轮 Codex 停线报告：新增 `_PRE_JUDGMENT_OBJECT` 窄排除（解 N5 与「做」互斥）；工程对象插入位置统一为 `replace` 之前 |
