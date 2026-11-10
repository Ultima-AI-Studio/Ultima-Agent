# 工单 wo-ultimaagent-20261110-0033 · 卡形态统一（队列式工单进审计与冻结）

> 状态：可开工 ｜ 前置：无（独立于 0030 的 T4–T7）｜ 通道：B
> 范围依据：`docs/INDEX.md`、`scripts/order_naming.py`、`scripts/gorch_contract.py`

## 0. 范围冻结

**只做**：让 `audit-work-order.py` 与 `freeze-work-order.py` 接受 `tasks/queue/*.md` 队列式工单；门抽取支持「验收（Gate Tn）」段落；放宽卡与证据的注入阈值。

**不做**：不改 `dispatch-work-order.py`（已修）；不把卡迁进 `tasks/cards`；不动 0030 的 `dc651d6f` 与 T0–T2 冻结产物；不改命名契约；不改全局登记表状态。

## 1. 任务清单

| 任务 | 文件 | 验收门 |
|---|---|---|
| T0 | `scripts/gorch_contract.py` | 新增 `stage_gates()`，能从「验收（Gate Tn）」段抽门 |
| T1 | `scripts/audit-work-order.py` | 接受队列式卡，ACC 缺失时回落 `stage_gates` |
| T2 | `scripts/freeze-work-order.py` | 零卡工单不再被 refuse |
| T3 | （实证，无代码改动） | 对 0030 真跑审计，产出 `audit.json` 且非 blocked |
| T4 | `scripts/tests/` | 既有基线不退化 |

## 2. 任务明细

### T0 · 门抽取扩展

**文件**：`scripts/gorch_contract.py`

**写什么**：
1. 新增 `stage_gates(card_text: str) -> list[dict]`，扫描形如 `**验收（Gate T3）**：` 的段落，收集其后的 `- ` 条目并合并为一条 criterion；
2. 返回 `[{"id": "Gate T3", "criterion": <合并文本>, "how": "作者在阶段报告里逐条自证"}]`，按编号升序；
3. `acc_rows()` 行为保持不变，`stage_gates` 只在新调用点使用。

**验收（Gate T0）**：
- `stage_gates` 可导入；
- 对 0030 卡调用返回 8 条（Gate T0–T7）；
- `acc_rows` 对 0030 卡仍返回空列表（既有语义未变）。

**禁止**：不改 `acc_rows` 的既有语义与去重/重复 id 判定。

### T1 · audit 接受队列式卡

**文件**：`scripts/audit-work-order.py`

**写什么**：
1. `gates()`：先 `acc_rows`，为空则 `stage_gates`，两者均空才 blocked；
2. `_card_id()`：卡位于 `tasks/queue/` 时，id 取文件名去掉 `.md` 后缀；`tasks/cards/<id>/task.md` 形态保持原行为；
3. 卡注入阈值 4000 → 16000 字符，证据 6000 → 12000 字符，`incomplete` 判定同步调整；
4. `_waiver_for`、`authority` 字段、`audit.json` 结构、两轮判定逻辑均不动。

**验收（Gate T1）**：
- 用 0030 卡调用 `gates()` 返回 ≥1 门；
- `_card_id` 对 `tasks/queue/<order>--<slug>.md` 返回文件名 stem，不抛错；
- `audit.json` 仍写在与 `--run-dir` 同目录。

**禁止**：不改 DeepSeek 调用方式与 `passed = pass1 and pass2 and visible` 判据。

### T2 · freeze 接受队列式卡

**文件**：`scripts/freeze-work-order.py`

**写什么**：
1. `order_cards` 为空时，不再 `refuse("the order references no card")`，改为绑定工单卡本身（路径 + sha256）；
2. `receipt_cards` 为空时允许通过，并把工单卡记作被审对象；
3. 卡位于 `tasks/queue/` 时按 `order_naming.resolve_card_path` 解析后比对，不再强制 `tasks/cards/<id>/task.md`。

**验收（Gate T2）**：
- 对 0030 的 `done.json`（`cards: []`）调用不再返回 `the order references no card`；
- 有卡的卡式工单（s1 系列）行为不变。

**禁止**：不放松“冻结必须 `audit_passed is True`”这一条件。

### T3 · 实证 0030

**文件**：无代码改动，只跑命令。

**写什么**：
1. 跑 `tools\venv-openjarvis\Scripts\python.exe scripts/audit-work-order.py --work-order wo-ultimaagent-20261108-0030 --card tasks/queue/wo-ultimaagent-20261108-0030--m4-orchestration-ledger.md --run-dir tasks/queue/runs/wo-ultimaagent-20261108-0030-20261110T101704476104Z --evidence <3 个 T3 产物>`
2. 回填 `audit_passed` 与逐门结果。

**验收（Gate T3）**：
- 命令不再返回 `blocked`；
- `run 目录/audit.json` 生成且 `gates` 含 `Gate T3`；
- 两轮 DeepSeek 都有 `model` 与 `response` 字段。

**禁止**：不得为“让它过”而放宽任何判定；PASS 与 FAIL 都算通过本门，只有 blocked 算失败。

### T4 · 回归

**验收（Gate T4）**：
- `tools\venv-openjarvis\Scripts\python.exe -m pytest scripts/tests -o addopts= -p no:cacheprovider -q`，失败数不超过既有基线 6 条；
- 新增用例覆盖 `stage_gates` 解析、队列式卡 `_card_id`、freeze 零卡三条路径。

## 3. 回执要求

- `changed_files` 逐条列出，与“写什么”一一对应；
- 显式声明“未改动 `dispatch-work-order.py`、未改动 0030 的 `dc651d6f` 与 T0–T2”；
- T3 的 `audit.json` 路径与 `audit_passed` 原样回填。
