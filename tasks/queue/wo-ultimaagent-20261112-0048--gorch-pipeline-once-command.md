# Codex 工单 · G-ORCH 全链路一条命令贯通（0048）

> 版本：v1.0 ｜ 状态：可开工（前置：gorch-chain-exists）｜ 适用工具：Codex
> 用法：按 T1→T6 顺序逐条执行，Gate PASS 后进下一条。每条先写 RED 再改代码。
> 方案依据：外脑三阶段产物 `tasks/queue/runs/req-gorch-pipeline-20261112/`（decompose.md / work_order.md / schedule.md，三阶段 verdict 均 COMPLETED）
> 前置：Phase 3.5 已冻结（commit `5746398a` / tag `ultimaagent-mainbrain-teaching-phase3-5-20261112`）；全量基线 `577 passed / 1 failed`；G-ORCH 六段脚本均已存在（见 §0）

---

## 0. 本单定位

G-ORCH 链路六段脚本**全部已在仓库中**（`orchestrate-order.py` 5163B / `dispatch-work-order.py` 41038B / `verify-order.py` 50898B / `audit-work-order.py` 26297B / `freeze-work-order.py` 36439B / `run-gorch.py` 6588B）。缺的不是链，是**链的自动衔接**：`run-gorch.py` 不派发（其 L10-13 原文：「⑤-⑥ live in `dispatch-work-order.py`」），`dispatch-work-order.py` 派完不回连。于是每次从需求到冻结要人肉分四段调用。

本单把这条链变成一条命令，并修掉链上两处会让结果不可信的具体缺陷（`done.json` 三洞 / `audit_passed` 假阴性）。

---

## 1. 范围冻结

**本单只做**：
1. 新建 `scripts/run-pipeline.py`：单入口，串 ①-④ → ⑤-⑥ → verify → ⑦ → ⑧，**只调用现有脚本，不重写任何判据**；含 `--requirement` / `--run-dir` / `--work-order` / `--card` / `--prompt` / `--dry-run` / `--skip-plan` / `--skip-dispatch` / `--skip-freeze` / `--evidence` / `--push` 共 11 个参数。
2. `scripts/dispatch-work-order.py`：修 `done.json` 三洞（list 型 status 不再抛异常且显式判定 / 工单号边界匹配 / 自检判据认全角冒号）。
3. `scripts/audit-work-order.py`：定位并修复 `audit_passed` 假阴性（两轮 Gate 全 PASS 却判 false）。
4. 新增测试：`tests/test_run_pipeline_dryrun.py`、`tests/test_done_status_list.py`、`tests/test_wo_id_boundary.py`、`tests/test_selfcheck_fullwidth_colon.py`、`tests/test_audit_passed_all_pass.py`。
5. `tasks/queue/queue-status.json`：登记本单 record（`records` 顶层键，state 用合法枚举）。
6. `docs/references/lessons-log.md`：追加 `audit_passed` 假阴性的定位结论（对应 L1078 之后）。

**本单不做**（Non-goals）：
- 不改 `verify-order.py` / `freeze-work-order.py` 的任何判据语义与门槛
- 不改 `audit-work-order.py` 的 Gate 判定口径（只允许修 `audit_passed` 的**聚合**推导）
- 不改 codex 调用参数（`-a never`、`model_reasoning_effort`、`exec` 形态）
- 不改 `src/brain/agent_server.py` 任何一行（Phase 3.5 冻结面）
- 不改 `run-gorch.py` 现有行为（新入口另建文件，不动既有调用方）
- 不改 `config/.env`，不打印任何密钥值
- 不新增定时任务、不重构、不顺手优化

---

## 2. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T1 | `scripts/dispatch-work-order.py` + `tests/test_done_status_list.py` | 洞1 反测绿：list 型 status 不抛异常且显式判定；原 bug 可复现 |
| T2 | `scripts/dispatch-work-order.py` + `tests/test_wo_id_boundary.py` | 洞2 反测绿：`wo-orb-w7` 不命中 `wo-orb-w7x`；边界内命中 |
| T3 | `scripts/dispatch-work-order.py` + `tests/test_selfcheck_fullwidth_colon.py` | 洞3 反测绿：`- 自检：PASS` 判 PASS；修复前判 FAIL |
| T4 | `scripts/audit-work-order.py` + `tests/test_audit_passed_all_pass.py` + `docs/references/lessons-log.md` | 反测绿：两轮全 PASS ⇒ `audit_passed=true`；一 FAIL ⇒ false；定位结论已落盘 |
| T5 | `scripts/run-pipeline.py` + `tests/test_run_pipeline_dryrun.py` | `--dry-run` 输出命令拼装、零写操作；四个跳过/证据开关对称可用；停链与 blocked 语义有单测覆盖 |
| T6 | `tasks/queue/queue-status.json` + `tasks/queue/runs/rehearsal-0048/` | **负路径**：演练 steps 顺序完整 + verify 如实拒绝 + verify 失败即停（不进 audit）+ 0047 **源**目录零改动；队列登记 + render exit 0；新测试 18 passed + `src/brain/tests`+`orchestration` 577 passed / 1 failed |

---

## 3. 任务明细

### T1 · 洞1 list 型 status
**文件**：`scripts/dispatch-work-order.py`（唯一消费 `status` 的调用点）、`tests/test_done_status_list.py`
**写什么**：
1. 定位 `status in {…}` 那一处并对 list 型 status 显式分支判定，不再依赖 `valid_payload` 短路。
2. 该调用点补 `try/except`，异常不得打崩派发器。
3. 反测：构造 `{"status": ["ok"]}`，断言修复前抛 `unhashable type: 'list'`、修复后返回明确判定（不得静默吞）。
**验收（Gate T1）**：反测绿且能复现原 bug；`python -c` 直接跑该函数确认不抛。
**禁止**：不改 `valid_payload` 的其他分支、不动 receipt 其他字段。

### T2 · 洞2 工单号边界匹配
**文件**：`scripts/dispatch-work-order.py`、`tests/test_wo_id_boundary.py`
**写什么**：
1. 把 `if work_order not in text` 改为边界感知匹配，分隔符类取「非 `[A-Za-z0-9_-]`」。
2. 反测：text 只含 `wo-orb-w7x` 时 `wo-orb-w7` 不命中；text 含独立 `wo-orb-w7` 时命中。
**验收（Gate T2）**：两向反测均绿。
**禁止**：不改工单号本身的格式校验规则。

### T3 · 洞3 自检全角冒号
**文件**：`scripts/dispatch-work-order.py`、`tests/test_selfcheck_fullwidth_colon.py`
**写什么**：
1. 自检判据正则同时接受半角 `:` 与全角 `：`。
2. 反测：`- 自检：PASS` 判 PASS；对修复前正则判 FAIL 留痕。
**验收（Gate T3）**：反测绿。
**禁止**：不放宽到「任意位置出现 PASS 即通过」。

### T4 · audit_passed 假阴性
**文件**：`scripts/audit-work-order.py`、`tests/test_audit_passed_all_pass.py`、`docs/references/lessons-log.md`
**写什么**：
1. 先用两轮 Gate T0-T4 各 5/5 PASS 的 fixture 复现 `audit_passed=false`。
2. 定位到具体聚合表达式并修掉。
3. 反测：全 PASS ⇒ true；一 FAIL ⇒ false。
4. lessons-log 在 L1078 之后追加定位结论（现象/根因/修法/反测）。
**验收（Gate T4）**：两条反测绿、定位结论已落盘。
**禁止**：**若复现证明 bug 在 Gate 判定本体而非 `audit_passed` 聚合，停链 BLOCKED 上报，不得自行豁免本单 §1 边界。**

### T5 · 单入口 run-pipeline.py
**文件**：`scripts/run-pipeline.py`（新建）、`tests/test_run_pipeline_dryrun.py`
**写什么**：
1. 参数：`--requirement` / `--run-dir` / `--work-order` / `--card` / `--prompt` / `--dry-run` / `--skip-plan` / `--skip-dispatch` / `--skip-freeze` / `--evidence` / `--push`。
2. 顺序：`orchestrate-order.py` → `dispatch-work-order.py --dry-run-dor` → `--execute` → `verify-order.py` → `audit-work-order.py` → `freeze-work-order.py`。
3. 停链：任一环节非 0 exit 即停，后续不跑；verify 不过不审计、审计不过不冻结（沿用 run-gorch 铁律）。
4. **blocked 必须区分两种**：读 `done.json` 的 `receipt_valid` 与 `state`，`receipt_valid=false` 判 `blocked-for-invalid-receipt`（真失败），`receipt_valid=true` 且等审计名额判 `paused-for-audit-slot`（不算失败）。**不得只看 exit code。**
5. 证据：`<run-dir>/pipeline.json` 复用 run-gorch 的 `steps` 结构，每步含 `step / exit_code / stdout / stderr`，另加 `outcome / reason`。
6. `--dry-run`：只打印每条命令的 argv，零写操作。
7. `--skip-freeze` / `--skip-plan` / `--skip-dispatch` 三个跳过开关**必须对称实现**，语义与 `run-gorch.py --skip-freeze` 一致：跳过则写 `outcome: "audited"`，不创建 tag。
8. **参数契约以现有脚本的真实接口为准**（已核实，不得再猜）：`verify-order.py` 接受 `--work-order` / `--run-dir` / `--profile`，读 `<run-dir>/done.json`、写 `<run-dir>/verify.json`；`audit-work-order.py` 接受 `--work-order` / `--card` / `--evidence` / `--run-dir`，写 `<run-dir>/audit.json`。**两者的输入输出都绑定 `--run-dir`，`--evidence` 只是 audit 的附加证据清单，不是输入源替代。**
**验收（Gate T5）**：`--dry-run` 输出可读且 `git status --porcelain` 无新增改动；blocked 两分支各有单测。
**禁止**：不重写 verify/audit/freeze 逻辑；不引入新依赖。

### T6 · 只读全链演练 + 登记与回归
**文件**：`tasks/queue/queue-status.json`、`tasks/queue/runs/rehearsal-0048/`（新建演练目录）
**写什么**：
1. 把 0047 已冻结 run `tasks/queue/runs/wo-ultimaagent-20261112-0047-20261112T073046954841Z` **整体复制**到新建的 `tasks/queue/runs/rehearsal-0048/`（源目录只读，复制是允许的——本卡不要求"不复制"，只要求源零改动）。
2. 在 `rehearsal-0048/` 内跑 `run-pipeline.py --skip-plan --skip-dispatch --skip-freeze --run-dir tasks/queue/runs/rehearsal-0048 --work-order wo-ultimaagent-20261112-0047 --card <0047卡路径> --evidence <0047产物>`，确认 verify → audit 走通、⑧ 被正确跳过（`outcome: "audited"`）。
3. 队列登记本单 record（`records` 顶层键，state `pending` 或 `audit`，纯 LF 2 空格）。
4. 跑 `scripts/render-queue-views.py` 至 exit 0。
5. 全量：`tools\venv-openjarvis\Scripts\python.exe -m pytest "src/brain/tests" "src/brain/orchestration/tests" -o addopts= -p no:cacheprovider -q`。
**验收（Gate T6）**：演练 `pipeline.json` 里 steps 顺序完整；`git status --porcelain` 显示 **0047 源目录零改动**（复制属允许操作）；队列 diff 为纯新增；render exit 0；全量 ≥ 577 passed / 1 failed（唯一失败仍是 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains`）。
**禁止**：不修改、不删除、不在 0047 **源** run 目录内任何文件。

---

## 4. 验收自检

- [ ] T1-T3 三条反测各自能复现原 bug 并在修复后转绿
- [ ] T4 两条反测绿（全 PASS⇒true / 一 FAIL⇒false），lessons-log 已追加
- [ ] T5 `--dry-run` 零写操作，blocked 两分支各有单测
- [ ] T6 只读演练 steps 完整、`--skip-freeze` 生效、render exit 0、全量 ≥ 577/1
- [ ] 越界声明：无越界（或明确列出）
- [ ] 改动文件清单与 §1 只做六条一一对应

---

## 5. 风险与停链点

| 风险 | 触发条件 | 处置 |
|---|---|---|
| R1 | T4 复现证明 bug 在 Gate 判定本体 | 停链 BLOCKED 上报，不自行扩权 |
| R2 | T5 blocked 两分支无法用 `done.json` 字段区分 | 停链上报，不退回 exit code 猜测 |
| R3 | 跑测试写出 `src/brain/__pycache__` 触及冻结面 | 记录为读缓存副产物，不修改该模块源码；在越界声明里如实写明 |
| R4 | `ConvertTo-Json` 或整体重写 queue-status | 禁止；用精确文本编辑，render 后自查 diff 行数 |

---

## 6. 主脑（顾问）裁决记录

### 6.1 A7「真实小工单」裁决

外脑在 decompose 里明确声明 A7 它无法决定（它无仓库读取能力，判断不了哪张小修真实且仍开放），work_order 却自行填了「以本单 §3.2 三洞修复作为端到端验证工单」——**这是循环依赖：链尚未修好，却要用它自己来验证它自己**。

**裁决**：端到端验证拆成两段。
- **本单（段1）**：只读全链演练——用 0047 已冻结的 run 做载体，跑 `--skip-plan --skip-dispatch` 到 verify → audit → freeze，证明链的拼装、停链、跳过逻辑正确。**封闭在本单内，不依赖任何新工单。**
- **下一单 0049（段2）**：链跑通后，用一张**真实独立的低风险小工单**做首次全自动端到端。载体定为「`/health` 的 `provider_note` 与实际行为不一致」的文案修正（实测：`provider_configured=false` 却提示「主脑未配置，/ask 将无法作答」，而实链路正常作答）。该缺陷真实、极低风险、独立于本单。

### 6.2 外脑提出的其余歧义采纳情况

| 编号 | 外脑提出的歧义 | 采纳 |
|---|---|---|
| A1 | 新建文件 vs 扩展 run-gorch | 采纳「新建 `run-pipeline.py`」：不动既有调用方，回归风险为零 |
| A2/A3 | `blocked` 需区分 slot 等待与回执无效 | 采纳，写入 §3 T5 第 4 条：必须读 `done.json` 的 `receipt_valid`/`state`，不得只看 exit code |
| A4 | T4 若命中 Gate 本体则停链 | 采纳，写入 §3 T4 禁止项与 §5 R1 |
| A5 | 洞2 的分隔符类 | 采纳「非 `[A-Za-z0-9_-]`」 |
| A6 | 洞1 list status 的判定 | 采纳「显式判 invalid，不静默吞、不强转 normalise」 |
| A7 | 真实小工单无法在此决定 | 采纳，见 §6.1 |
| A8 | 测试可能写 `src/brain/__pycache__` | 采纳，见 §5 R3：如实记录副产物，不改源码 |
| A9 | 577 是下限不是等式 | 采纳，§3 T6 写「≥ 577 passed」 |
| A10 | `pipeline.json` schema | 采纳，§3 T5 第 5 条冻结字段集 |

### 6.3 与外脑产物的差异（本卡相对 `work_order.md` 的改动）

1. 任务表由外脑的 5 列（`# / 任务 / 前置 / 产出 / 验收`）压成工程模板要求的**三列**（任务 / 文件 / 验收门）——外脑原表过不了 `--dry-run-dor`。
2. 补 `> 版本：` `> 前置：` `> 方案依据：` 三行卡片头（外脑原稿只有正文）。
3. A7 由「用本单自己」改为 §6.1 的两段拆分。
4. 外脑 T1/T2/T3 三洞合并为并列 T1/T2/T3 三任务（原稿是 T2/T3/T4，因 T1 已被单入口占用，编号顺延）。
5. 新增 §6 记录裁决与外脑歧义采纳，作为决策可追溯。

**外脑未产出的部分**：`work_order.md` 中门 6 的状态行、§4 验收自检、§5 风险表均由主脑补全——外脑三阶段只到工单骨架，卡片级细则需本层补齐。

### 6.4 首轮停线裁决（Codex 于 run `...T080458976981Z` 报出）

**报的问题**：T5 参数清单没有 `--skip-freeze`，但 T6 明确要求调用它；同时 T5 把 `pipeline.json` 写入 `<run-dir>`，T6 又禁止改动指定的 0047 run 目录。

**判定：这是本卡的真矛盾，主脑认责。** L174 已记「工单事后追加裁决必须同步回范围冻结与任务表」，本卡这次是**同一节内的自相矛盾**——T5 参数与 T6 用法对不上，属 L174 同族缺陷。

**裁决**：
1. §3 T5 参数清单补齐 `--skip-freeze` / `--evidence`，并新增第 7、8 条：三个跳过开关必须对称实现（跳过则写 `outcome: "audited"`、不建 tag）；`--evidence` 透传给 audit，允许产物在外部位。
2. §3 T6 改为**新建演练目录** `tasks/queue/runs/rehearsal-0048/` 承载 `pipeline.json`，0047 run 只作 `--evidence` 只读引用（不复制、不改写）。Gate 增加「`git status --porcelain` 显示 0047 run 目录零改动」。
3. §1「本单只做」第 1 条同步为「新建 `scripts/run-pipeline.py`：单入口…含 `--skip-plan/--skip-dispatch/--skip-freeze/--evidence` 四个跳过与外部证据参数」。

### 6.5 本次三处一致性自查

按 L174，追加裁决后必须回核三处：§1 范围冻结（已同步，见 §6.4 第 3 条）、§2 任务清单（T5/T6 行验收门描述与新参数一致）、§3 任务明细（已重写 T5 第 1/7/8 条与 T6 全文）。三处一致。

### 6.6 第二轮停线裁决（Codex 于同 run 的 msg 12 报出）

**报的问题（三条，全部成立）**：
1. 本卡要求 `--run-dir rehearsal-0048` 只承载新证据、0047 仅经 `--evidence` 只读且「不复制」——但 `verify-order.py`（L671/L1011）只从 `--run-dir` 读 `done.json` 并写回 `verify.json`，`audit-work-order.py`（L566）也写回 `audit.json`。于是指向 rehearsal 没有 `done.json` 必然失败；指向 0047 会写进 0047；复制又违反本卡写的「不复制」。
2. T5 的 CLI 缺 `--work-order` / `--card` / `--prompt`，而下游 verify/audit/freeze 全都需要它们。
3. `--evidence` 被本卡当成「输入源替代」，实际它只是 audit 的附加证据清单。

**判定：全部是本卡的错，主脑认责。** 这是同一单的第三次自相矛盾，且与前两次同类（L174 同族：裁决写了但没对照下游脚本的真实接口）。

**裁决**：
1. §3 T5 参数补 `--work-order` / `--card` / `--prompt` 三个（下游必需），并新增第 8 条**冻结下游真实接口**：verify 接受 `--work-order/--run-dir/--profile`、读 `<run-dir>/done.json` 写 `<run-dir>/verify.json`；audit 接受 `--work-order/--card/--evidence/--run-dir`、写 `<run-dir>/audit.json`；两者都绑定 `--run-dir`，`--evidence` 不是输入源替代。
2. §3 T6 改为**整体复制** 0047 run 到 `rehearsal-0048/` 后在副本上跑（源只读、副本可写），删除原「不复制」限制；Gate 改为验「0047 **源**目录零改动」。
3. §1 只做第 1 条同步补齐 `--work-order/--card/--prompt`。

### 6.7 三处一致性再自查（第二轮回核）

§1 第 1 条参数清单 / §2 T5 行验收门 / §3 T5 第 1 与第 8 条 —— 三处参数集合现已一致：`--requirement, --run-dir, --work-order, --card, --prompt, --dry-run, --skip-plan, --skip-dispatch, --skip-freeze, --evidence, --push`（共 11 个）。
§2 T6 行 / §3 T6 全文 / §5 R3 —— 均已改为「复制到 rehearsal，源零改动」。

### 6.8 T6 演练实测结论与验收口径修正（第三轮裁决，主脑自裁）

**实测事实（0047 run 复制到 `rehearsal-0048/` 后实跑）**：
- `pipeline.json`：`outcome=verify-failed`，steps 顺序正确（plan / dispatch-dor / dispatch 三步均 `skipped=true` 且带 reason，verify `exit_code=2`），**⑧ freeze 未触发**（铁律生效）。
- `verify.json`：17 checks，6 项 blocking_failures —— `receipt_valid=False` / `receipt_names_itself` / `terminal_state_legal(state=blocked)` / `tree_unchanged(21 条重算后树不同)` / `order_manifest` / `declared_command_plan`。**全部是真实事实，不是误报**。
- 0047 **源**目录 `git status --porcelain` 为空 —— 零改动达成。

**关键判定：T6 的「verify → audit 走通」在只读演练下结构上不可达。**
`verify-order.py` 的 `tree_unchanged` 要求 done.json 记录的 `tree_oid` 与当前工作树一致。任何历史 run 的 done.json 都记录着当时的树，当前工作区必然不同，因此**只读演练必然 verify-failed**，audit 永远接不上。0047 的 `receipt_valid=false` 只是加速了这个结论，不是唯一原因。

**裁决**：
1. T6 验收门改为**负路径验证**：`pipeline.json` 的 steps 顺序完整 + verify 如实拒绝 + verify 失败即停不进入 audit + 0047 源目录零改动。这四项已全部实测通过。
2. **audit 正路径明确移交 0049**（首次真实全自动），因为只有真实新单的 done.json 才可能 `tree_unchanged` 通过。
3. 这是本卡第六处自我修正：原 §3 T6 写「确认 verify → audit 走通」，前提假设错误。

### 6.9 验收口径修正与 Codex 越界盘点

**验收口径修正（原写错）**：
- 原 §3 T6 写「全量 ≥ 577 passed / 1 failed」。实测 `src/brain/tests` + `src/brain/orchestration/tests` = **577 passed / 1 failed**，未回退；但这 577 **不含本单新增的 18 个测试**（它们在 `tests/` 根目录，属 `pytest.ini` 的 `testpaths`，与 `test_verify_order.py` / `test_run_gorch.py` 同族）。
- 修正为双口径：① 新增 5 个测试文件单跑 **18 passed**；② `src/brain/tests + orchestration` **577 passed / 1 failed**（唯一失败仍是 ollama 环境噪声）。
- 基线对照（`git worktree` 到 `c886307d`）证据：同一组三个测试文件在基线为 **3 failed / 32 passed**，当前为 **1 failed / 34 passed** —— 本单不仅无回归，还**修好了 2 个既有失败**（`test_receipt_contract.py::test_real_w6_receipts_map_to_their_explicit_terminal_state` 的两个参数化用例，正是 T1 list 型 status 修复的直接效果）。剩余 1 个失败（`test_audit_checklist.py::test_summary_substring_cannot_pass_a_failing_line`）基线即存在，非本单引入。
- `tests/` 目录整体 487 passed / 26 failed 属既有债务；两个 validator 失败卡是 `wo-...-0029--e02-offline-minimal-repair.md`（缺 plan_ref）与 `wo-...-0035--voice-baseline-split.md`（E_GATE_CONTRADICTION），均与本单无关；**本单 0048 卡通过 validator，未进失败列表**。

**Codex 越界点（1 处，方向正确，已补进卡）**：
- `run-pipeline.py` L182 自行加了 `if not args.evidence: parser.error("--evidence must name at least one audit artifact")`。而下游 `audit-work-order.py` 的 `--evidence` 是 `nargs="*" default=[]`，**允许为空**。这是「比下游更严」的自加约束，方向是 fail-closed，故保留；但属于卡未写明的行为，现补进 §3 T5 第 1 条注记。
