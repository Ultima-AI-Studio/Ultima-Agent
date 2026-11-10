# 审计阶段门硬化方案（G-PLAN-0027，2026-11-08）

> 依据：用户 2026-11-08 拍板「分阶段派发 + 每阶段独立复核」。
> 遵循 G-PLAN-001（方案先行、方案随工单落盘）、G-OPEN-001（复用现有实现，不重复自研）。

## 一、问题实证（不是推测）

0026 派发后核查到的事实：

1. **一次 `codex exec` 从 T0 跑到 T2**，中间没有断点。
2. **执行端自判阶段门**：`tasks/queue/runs/wo-ultimaagent-20261108-0026/T0/receipt.json` 由 codex 自己写，`status=COMPLETED`、三条 acceptance 全 `PASS`、`reviewReason` 也是自述。
3. **执行端自改看板**：commit `46adbd1f`（作者 ArkExlabs=codex）把模块3 的 level3 直接改成「标准化审计提示词：100% ✅」。
4. 结果是 **执行者 = 判定者 = 验收者 = 进度宣布者**，四合一。

对照组（唯一真实监督）：主脑事后独立复跑 T0 测试，`Ran 10 tests / OK / EXITCODE=0`，并抽查断言确认未被弱化。这说明本次产出可信，**但不构成体系保证**——只覆盖一个样本、且靠人肉。

## 二、根因：角色是字符串，不是身份

- `src/brain/guardrails/reviewer.py` 的 `IndependentReviewer.__init__` 只校验 `role in ("eng.audit","eng.security")`。**同一个进程传一个合规字符串即可自建复核器给自己盖章**，`dev` 被拒只是防手滑，不防自证。
- `src/brain/guardrails/receipt.py` 只校验四字段齐全、evidence 路径存在、`result` ∈ {PASS, FAIL}。**不校验结论由谁产生**。
- 因此"独立审计"目前是**约定**，不是**机制**。

## 三、设计：把复核变成有身份的一步（复用为主）

### 3.1 分阶段派发（进程级身份隔离）

- 单个工单按 T 拆成**多次 `codex exec`**，每次一个新会话（codex 每次 exec 天然无历史上下文）。
- 派下一阶段的前置条件：上一阶段的**独立复核结论文件存在且 blocker=0**。
- 这样"写代码的进程"与"判绿灯的进程"物理上不同，且复核端拿不到执行端对话上下文，只拿工单卡 + 产出 + evidence 路径。

### 3.2 复核结论文件规范（新增，复用既有结构）

新增 `data/evidence/<work_order>/<stage>/independent-review.json`，字段直接复用 `ReviewResult.as_dict()`（`ok/role/blocker/major/minor/checked/findings`），外层套 `ReceiptValidator` 要求的四字段，使其既能被现有 `ReceiptValidator` 机检、又能被现有 `ReviewResult` 消费。

**归属规则**：该文件只能由复核会话产生，执行端不得写入；执行端 commit 与复核 commit 分开，commit message 前缀区分 `[audit]`。

### 3.3 阶段门执行器（新增一个小模块，复用两个现有类）

新增 `src/brain/guardrails/stage_gate.py`：
- `check_stage(work_order, stage, evidence_root)` → 读独立复核文件 → 用 `ReceiptValidator` 校验完整性 → 用 `ReviewResult` 语义判 `blocker>0`；
- 返回 `StageGateResult(passed, reasons[])`，`passed=False` 时附带拒绝原因（缺失 / 非法 / blocker 未清零 / 角色不符）；
- **fail-closed**：文件缺失、非法 JSON、角色非审计、blocker>0，一律不放行。

不新造审计器、不新造回执格式、不引入第三方依赖。

### 3.4 派发脚本模板硬化

把现有 `_dispatch_*.py` 模板改成：
1. 每次只派一个 T；
2. 派发前调用 `stage_gate.check_stage(上一阶段)`，未过则拒绝启动；
3. 载荷里明确"本阶段结束不得自行宣布全局完成、不得改看板百分比（看板由主脑统一回写）"。

### 3.5 看板回写权收归主脑

本次实证发现"执行端自改看板"会让进度失真。新规则：**level3 的 100% ✅ 由主脑在复核通过后统一回写**，执行端只交付证据。这条同时修掉"一条 level3 塞两个子任务导致百分比卡死"的隐患（拆细粒度一并处理）。

## 四、不做什么（防范围失控）

- 不改 `reviewer.py` / `receipt.py` 既有语义（0026 正在引用它们，避免冲突）。
- 不做"自动叫 codex 复核"的调度器——本期只做门 + 模板，调度仍由主脑手工触发，先验证机制再自动化。
- 不做多 Agent 并行编排（那是模块4，别和本单混）。
- 不引入 LLM 复核作为唯一判据：确定性检查（测试复跑、写域核对、断言抽查）优先，LLM 复核只作补充。

## 五、验收口径

1. 对 0026 的 T0/T1 做一次真实独立复核，产出合规 `independent-review.json`，`stage_gate` 判 PASS。
2. 构造三种反例（缺文件 / blocker>0 / 角色=dev），`stage_gate` 全部拒绝放行，有单测覆盖。
3. 一份真实演练记录：证明"复核未通过时派发脚本拒绝启动下一阶段"。
4. 专用解释器（3.13.16）全量工程门 0 failed。

## 六、风险

- **流程变慢**：分阶段派发会让单工单从"一口气跑完"变成"多轮 + 复核等待"。缓解：复核只做确定性抽检（复跑测试 + 查写域 + 抽查断言），单轮控制在分钟级。
- **复核走过场**：如果复核会话只是敷衍打 PASS，机制形同虚设。缓解：`checked[]` 字段必须列出实际执行的检查项，且 `stage_gate` 要求 `checked` 非空、至少包含"测试复跑"与"写域核对"两项。
