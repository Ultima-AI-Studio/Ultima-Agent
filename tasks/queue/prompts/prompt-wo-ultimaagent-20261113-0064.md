# 派发载荷 · wo-ultimaagent-20261113-0064（拆解：Autoloop 三单）

工单号：`wo-ultimaagent-20261113-0064`
工单卡：`tasks/queue/wo-ultimaagent-20261113-0064--autoloop-three-order-decomposition.md`
先读 `docs/INDEX.md` 定位权威源，再读本单卡，然后按 T1→T5 顺序执行。

## 本单做什么

把 `docs/plans/next-autoloop-融合实施方案-20261113.md`（v0.3）拆成 **3 张可执行工单卡**，并产一份拆解报告：

- **0061**：P0「唯一写入口三件套」——`tasks/queue/inbox/` ＋ `scripts/queue-writer.py`（唯一写者）＋ `scripts/reconcile-inbox.py`（只读对账）＋ `claim_id` 字段。不改基线。
- **0062**：P1「§二十七 三机制」——M3 指令数据分离、M4 跳数＋扇出熔断、M7 卡片 ask.key 幂等、§27.4 仅 `session_id`。
- **0063**：§25.10 补 `cancel_observe ∈ {running, not_running, unknown}`，含解除规则与四条 Gate。

## 硬约束（违反即失败）

1. **只产卡，不产实现**：不写代码、不建目录、不改基线、不改队列、不改 tracker。
2. **状态只能写「待审卡」**：三张卡由 Owner 与独立审计过 0060 式审卡后才派发，你不要自称可开工。
3. **禁止写死计数**：卡面不得出现「恰好 N 行／处／列／个」，DoR 会以 `W_VOLATILE_COUNT_WRITTEN` 直接拒派（0057、0058 都踩过）。
4. **同一契约只许一处主文**：`cancel_observe` 只在 0063／§25.10；0062 里只能以「不在本卡」的形式提及。
5. 不改 v1 冻结参数（`config/voice-next/live.json`）、不新增产品承诺。
6. 禁 commit／push／tag，禁调 18766，禁碰 `H:\UltimaAI\UltimaAgentNext`。

## 事实前提（不要重新判断）

- 0057：state=`audit`，自检 PASS、`READY_FOR_OWNER_REVIEW`，**未冻结**。所以 0063 的前置写成「0057 冻结后切」。
- 0058：已执行、已提交、已 tag。
- 0059：未执行，16 条是封闭清单，**不许重拆、不许缩范围**。
- §二十五 归 0057；§二十六 归 0059；§二十七 空、可用。

## 写入域（越界即失败）

1. `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md`
2. `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md`
3. `tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md`
4. `docs/plans/next-autoloop-三单拆解-20261113.md`
5. `docs/reports/decompose-wo-ultimaagent-20261113-0064.md`

## 执行纪律

1. **每完成一个 T 立刻落盘**（卡或报告章节写完就保存），再进下一个；撞时限保已落盘部分。
2. 引用方案条款时写清「方案 §X.Y」，便于复核；不要复述 DeepSeek 三份文本，只引用结论落成条文。
3. 允许你在拆解中发现方案漏洞——写进报告的「冲突清单／风险」栏，不要自作主张改方案。
4. 完成后回执须含：工单号、`自检: PASS`、一行 `READY_FOR_DEEPSEEK_AUDIT`、以及 4 文件路径与 `validate_work_order.py` 的真实输出。
