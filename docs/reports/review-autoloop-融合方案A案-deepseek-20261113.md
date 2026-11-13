# DeepSeek 独立评审 · 融合方案 A 案（M1 进首批）

> 评审对象：`docs/plans/next-autoloop-融合实施方案-20261113.md` §6 决策点 A vs B
> 评审通道：DeepSeek API（deepseek-chat）｜时间：2026-11-13 23:42
> 说明：外部独立评审**原文**，未经删改。

---

## 结论

**A 不成立（按现文），但可修成立。** 现文 A 的 `unknown` 只是把 E-01 从"取消表没覆盖"改名为"取消表多一个观测值"，没有定义它如何被判定、由谁写、写在哪、Gate 怎么机检——这恰好是 E-01 的实质缺口。修法见第二点，改完 A 成立。落地位置选 **(a) 切小单改 §25.10**，不是 (b)。A 相对 B 的真实增量只封住 E-01 的"没在跑"半段，"不知道在不在跑"半段封不住，代价偏高但可接受——前提是 `unknown` 被定义成**判定结果**而非**状态**。

---

## 一、A 是否成立

**不成立，是改名。** 理由：

1. **`unknown` 没有判定主体和判定时点。** 现文只说"语义＝没在跑/不知道在不在跑"，但取消链路里谁在什么时刻、依据什么证据判出 `unknown`？没有。§25.10 表里每一级都有 ack 时限和强杀凭据，`unknown` 却没有任何凭据口径——它就成了一个无法机检的标签。
2. **`unknown` 与 `cancel_outcome=cancelled` 的关系未定义。** step 层已用 `cancel_outcome` 承载"不增状态"的取消事实；`unknown` 若也挂在 run/step 上，两者是并列、互斥还是覆盖？不写清就是第二个 `cancel_outcome`，制造双源。
3. **Gate 落不了地。** 作者自己说"不补 unknown，E-01 的 Gate 落不了地"，但补了 `unknown` 之后 Gate 长什么样，方案里一个字没有。没有 Gate 的 `unknown` 等于没补。
4. **与 §25.10 已冻结口径的边界没划。** 3s ack / 强杀 / `ActiveProcesses==0` 是"在跑"的判据；`unknown` 是"不在跑或判不了"的判据，两者在时间轴上如何交接（ack 超时→强杀→`ActiveProcesses==0` 证明失败→`unknown`？还是 ack 前就 `unknown`？）完全空白。

**改法**：把 `unknown` 定义为**取消链路在 ack 窗口内对 run 运行态的观测判定结果**，有明确判定条件（见第二点），它才从"改名"变成"补洞"。

---

## 二、可直接落 §27.4 的条文（三段式）

> **§27.4 M1 会话字段与取消观测值 `unknown`**

**（1）字段/状态定义**

- 对话信封新增一等字段 `session_id`（字符串，非空，与 `claim_id` 正交，不替代）。
- 取消链路新增观测值 `cancel_observe ∈ {running, not_running, unknown}`，**仅挂在 run 层**，不进入八态状态机，不改 §15.2.1 状态图。
- `unknown` 语义严格限定为：**在 3s ack 窗口结束时，既未收到 cancel_ack，也未取得 `ActiveProcesses==0` 强杀凭据**。它是"证据缺失"的判定结果，不是"可能没在跑"的猜测。
- `not_running` 语义：取消触发时该 run 无活动进程且无在途 ack 义务（即"没在跑"）。

**（2）映射规则**

- 取消触发 → 先置 `activity=cancelling`（沿用 §25.10）→ 3s 内收 ack：
  - 收到 ack → `cancel_observe=running`，按 §25.10 表落 `CANCELLED`。
  - 无 ack → 强杀 → 3s 内 `ActiveProcesses==0` 成立 → `cancel_observe=running`，落 `CANCELLED`。
  - 无 ack 且强杀后 3s 内 `ActiveProcesses==0` **不成立** → `cancel_observe=unknown`，run 保持最后事实状态，**不落 `CANCELLED`**，向队列投影 `CANCELLED_PENDING`（队列侧标记，非八态）。
  - 取消触发时即无活动进程 → `cancel_observe=not_running`，直接落 `CANCELLED`，不占 ack 窗口。
- `unknown` 的解除：下一轮对账（`reconcile-inbox.py`）或下一次取消重试取得 `ActiveProcesses==0` 凭据后，转 `running` 并落 `CANCELLED`；连续 N 轮（建议 3）仍 `unknown` → 升级为人工介入告警，**不自动改队列**（沿用 §3.1 第 5 条对账只读原则）。
- 与 D-01=A 的关系：`EXECUTING → CANCELLED` 直接迁移不变；`unknown` 是迁移**未完成**时的观测值，不构成第三条迁移边。

**（3）Gate**

- G-27.4-a：构造"ack 超时 + 强杀后 `ActiveProcesses!=0`"用例，断言 `cancel_observe==unknown` 且 run 状态**未**变为 `CANCELLED`，队列投影为 `CANCELLED_PENDING`。
- G-27.4-b：构造"取消时无活动进程"用例，断言 `cancel_observe==not_running` 且直接落 `CANCELLED`，不占 3s 窗口。
- G-27.4-c：构造 `unknown` 连续 3 轮对账用例，断言第 3 轮产生人工告警且队列状态未被脚本改动。
- G-27.4-d：断言八态状态图 diff 为空（`unknown` 未进状态机）。

---

## 三、落地位置裁决

**选 (a)：切小单改 §25.10。** 理由：

1. §25.10 尚未提交、未冻结，此刻改是**最低成本窗口**；一旦冻结再改要开变更单，成本翻倍。
2. `unknown` 的判定条件与 §25.10 的 3s ack / 强杀 / `ActiveProcesses==0` 口径**强耦合**，写在 §27.4 再指针引用会造成"判据在 §25.10、观测值在 §27.4"的跨节依赖，审计时两处对不上就是新双源。
3. (b) 指针引用的风险：§27.4 是 M1 会话字段的主文，把取消观测值塞进去会让 §27.4 变成"会话字段 + 取消语义"的混合节，违反方案 §4 的"一节一机制"。

**风险**：切小单会多一轮 0057 的返工审计（约半天）；若 0057 作者与 0062 作者不同人，需明确写域交接。可接受。

---

## 四、A 相对 B 的真实增量

**封得住**：E-01 的"没在跑"半段——`not_running` 直接落 `CANCELLED`，取消表不再对"取消时已无进程"的 run 无定义。这是 E-01 里最容易触发、也最容易机检的一段。

**封不住**：E-01 的"不知道在不在跑"半段——`unknown` 只是把"不知道"显式化并挂起，**没有解决**"不知道"本身。真正的解法需要进程级探活（pid/容器句柄/宿主侧 `ActiveProcesses` 的可靠来源），这超出 M1 范围，属 v1.1。所以 A 是把"静默留洞"改成"显式挂起 + 告警"，不是把洞填上。

**代价**：多约 15 行条文、4 条 Gate、1 轮 0057 返工审计 + 1 轮 0062 审计。**值**——因为 E-01 是 11 条 BLOCKER 里唯一的取消类，显式挂起比静默留洞在审计上可辩护；但**不值**如果作者把 `unknown` 宣传成"已解 E-01"，那是过度承诺。

---

## 五、结论一句

**A 但需改条件**：`unknown` 必须定义为"3s ack 窗口结束且强杀后 `ActiveProcesses==0` 不成立"的**判定结果**（含 `not_running` 对照值、解除规则、4 条 Gate），落地切小单改 §25.10 而非写 §27.4；改完 A 成立，且对外只能称"E-01 显式挂起"，不得称"已解"。
