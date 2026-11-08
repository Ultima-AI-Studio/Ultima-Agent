# UltimaAgent｜审计阶段门硬化（分阶段派发 + 每阶段独立复核）

- **task_id**: wo-ultimaagent-20261108-0027
- **stage**: 模块3 单 Agent 主干加固·审计门（接续 0026）
- original_work_order_id: wo-ultimaagent-20261108-0027
- revision: 1
- authorization: 用户 2026-11-08 明确指令「可以」——批准将「分阶段派发 + 每阶段独立复核」立单；起因是 0026 实证发现执行端自判阶段门、自写回执、自改看板。
- 状态：pending（**等 0026 收口后再派发**，遵守「每项目执行中 ≤1」WIP）
- 契约：本工单卡即契约；方案见 `docs/plans/audit-stage-gate-plan-20261108.md`（G-PLAN-0027，不可变口径）。
- 关联现状（已核查，执行端先复验再动手）：
  - `src/brain/guardrails/reviewer.py`：`IndependentReviewer` 仅校验 role 字符串 ∈ {eng.audit, eng.security}，**同进程可自建审计角色自证**。
  - `src/brain/guardrails/receipt.py`：`ReceiptValidator` 只校验四字段齐全 + evidence 路径存在 + result ∈ {PASS, FAIL}，**不校验结论由谁产生**。
  - 0026 实证：`tasks/queue/runs/wo-ultimaagent-20261108-0026/T0/receipt.json` 由 codex 自写并自判三条 acceptance=全 PASS；commit `46adbd1f`（作者 codex）自行把看板 level3 改为 100% ✅。
  - 主脑事后独立复跑 T0 确认真实通过（10/10 OK），说明问题不在产出质量，而在**流程无独立监督**。

## goal

把"独立审计"从约定变成机制：让写代码的进程与判绿灯的进程**物理分离**，并把"阶段是否可放行"变成可机检的门，而不是执行端的自述。

1. **阶段门执行器**：新增可机检的 stage gate，未拿到合规独立复核结论则拒绝放行下一阶段（fail-closed）。
2. **复核结论规范化**：定义独立复核结论文件格式，复用现有 ReviewResult / ReceiptValidator 结构，禁止执行端自写。
3. **流程与演练**：派发模板改为单阶段派发 + 前置门校验；用 0026 真实产出做一次端到端独立复核演练，并证明反例会拦截。

## acceptance[]

- ACCEPT T0：新增 `src/brain/guardrails/stage_gate.py`，提供 `check_stage(work_order, stage, evidence_root)`，内部复用 `ReceiptValidator` 校验结论文件完整性、复用 `ReviewResult` 语义判 `blocker`；返回 `StageGateResult(passed, reasons[])`。fail-closed：文件缺失 / 非法 JSON / 角色非 eng.audit|eng.security / blocker>0 / `checked` 为空或缺少「测试复跑」「写域核对」两项，一律不放行。
- ACCEPT T0：新增单测（unittest），至少覆盖 1 个放行正例 + 4 个拦截反例（缺文件、非法 JSON、blocker>0、角色=dev）；断言为真异常/真布尔，禁止 `assertTrue(True)` 式空断言。
- ACCEPT T1：发布独立复核结论文件规范（建议 `data/evidence/<work_order>/<stage>/independent-review.json`，字段 = ReceiptValidator 四字段 + ReviewResult 的 `ok/role/blocker/major/minor/checked/findings`），并在 `docs/specs/` 落一份规范文档，明确「该文件只能由复核会话写，执行端不得写入」「执行 commit 与复核 commit 分开，复核 commit 前缀 `[audit]`」。
- ACCEPT T1：派发脚本模板硬化——每次只派一个 T；启动前调用 `stage_gate.check_stage(上一阶段)`，未过即拒绝启动；载荷中明确「本阶段不得自行宣布全局完成、不得改看板百分比（看板回写权归主脑）」。
- ACCEPT T2：用 0026 的 T0/T1 真实产出做端到端演练，产出一份合规 `independent-review.json`（复核内容须含**独立复跑测试 + 写域核对 + 断言抽查**三项实际动作及其原始输出路径），`stage_gate` 判 PASS；演练记录落 `docs/reports/`。
- ACCEPT T2：反例演练——构造缺文件 / blocker>0 / 角色=dev 三种情形，证明派发脚本或 gate 拒绝放行，记录真实输出。
- ACCEPT 全量：专用解释器 `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe`（3.13.16）跑全量工程门 0 failed（按实际计数）；新增用例真实通过，禁止删测试或弱化断言凑绿。
- ACCEPT 边界：**不改 `reviewer.py` / `receipt.py` 既有语义**（0026 正在引用）；不做自动调度器（本期只做门 + 模板）；不碰模块4 多 Agent 编排；不重启 daemon、不改模型参数与 KWS 基线。

## dependsOn[]

- wo-ultimaagent-20261108-0026（必须收口，才可派发本单，避免 WIP 冲突与文件争用）
- `src/brain/guardrails/reviewer.py`、`receipt.py`（复用，不改语义）
- G-TASKFLOW-001 工作流、G-PLAN-0027 方案

## fileDomain[]

- `H:/UltimaAI/UltimaAgent/src/brain/guardrails/stage_gate.py`（新增）
- `H:/UltimaAI/UltimaAgent/src/brain/guardrails/tests/test_stage_gate.py`（新增）
- `H:/UltimaAI/UltimaAgent/docs/specs/independent-review-contract.md`（新增）
- `H:/UltimaAI/UltimaAgent/docs/plans/audit-stage-gate-plan-20261108.md`（方案，只读引用）
- `H:/UltimaAI/UltimaAgent/docs/reports/wo-ultimaagent-20261108-0027-*.md`（演练报告）
- `H:/UltimaAI/UltimaAgent/data/evidence/wo-ultimaagent-20261108-0027/`（演练证据与复核结论）
- `H:/UltimaAI/UltimaAgent/tasks/queue/wo-ultimaagent-20261108-0027--audit-stage-gate.md` 与 `tasks/queue/runs/wo-ultimaagent-20261108-0027*`
- **禁止触碰**：`docs/tracker/北极星上线任务清单.html`（看板回写权已收归主脑）、`src/brain/guardrails/reviewer.py`、`receipt.py`、任何 0026 写域文件

## priority

- 90（高于常规功能单：它决定后续所有工单结论是否可信）

## reasoningEffort

- high

## category + skill

- 工程治理 / 流程硬化；test-driven-development、verification-before-completion；复用优先，禁止另造审计体系。

## receipt

- 各阶段落 `data/evidence/wo-ultimaagent-20261108-0027/<T>/`；回执满足 `receipt.py` 四字段；本次首次提供**独立复核结论** `independent-review.json`（按本单 T1 规范），证明结论非自证。

## retryCount

- 0；审计 REVISE 最多两轮。

## 写什么与禁止

1. 先复验现状（读 `reviewer.py`、`receipt.py`、0026 的 `T0/receipt.json` 与 `T0/green-test.log`），确认"角色字符串 ≠ 身份"这一缺口成立，再按 T0→T1→T2 RED→GREEN。
2. **复用优先**：结论文件格式直接复用 `ReviewResult.as_dict()` + `ReceiptValidator`，禁止新造第二套审计数据结构；确需新增依赖先出开源替代排查表（G-OPEN-001）。
3. **本单自身也受门约束**：每个 T 完成后必须产出独立复核结论并过 `stage_gate` 才进入下一 T；若本单执行端跳过自门，视为未完成。
4. **看板禁止改**：`docs/tracker/北极星上线任务清单.html` 的百分比由主脑在复核通过后统一回写，执行端一律不得自行宣布进度。
5. 隔离在途改动：工作区存在其他线未提交修改（.superpowers/、data/evidence/jarvis-work-*、0021、tasks.json、docs/tracker/_backup 与 _shots 等），`git add` 必须精确到本单写域文件，**严禁 `git add -A`、`-u`、`.` 或通配**。
6. 每 T 完成后精确暂存本单文件并 commit（信息标注"工单 0027 审计门 T0/T1/T2"）；最终打 tag `ultimaagent-audit-stage-gate-20261108` 并免代理 push（`git -c http.proxy= -c https.proxy= -c http.https://github.com.proxy= push`）；push 失败登记 evidence 不回滚提交。
7. 18766 管理接口当前离线，登记以全局主表为准，不阻塞执行。
