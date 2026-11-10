# 方案：工单契约机器可校验化 + 通用冻结门（模块2 P1 + P2）

> 版本：v1.0 ｜ 日期：2026-11-08 ｜ 状态：待工单 0031 执行 ｜ 依据 G-PLAN-001（方案随单落盘）
> 上游依据：`docs/reports/audit-module12-20261108.md` 模块2 P1/P2 缺口
> 关联：本文档与 `tasks/queue/wo-ultimaagent-20261108-0031--m2-workorder-contract.md` 成对存在

---

## 1. 背景与判定

2026-11-08 对模块1/模块2 的独立审计结论是：**模块2「G-TASKFLOW-001 工单契约规范」文档级成立、代码级部分成立，但缺机器可校验契约**。一句话总结是"100% 是人工流程完备，不是系统自动能力完备"。

主脑复核（同日）确认该结论成立，并把模块2 从 100% 降级为 67%，其中新增一条明确缺口：

> 机器可校验契约 `work-order.schema.json` + `validate_work_order.py`：**0%**

本次要把这个 0% 补上，并把冻结门从"版本专用硬编码脚本"提升为"通用入口"。

---

## 2. 现状取证（2026-11-08 实测）

| 事实 | 取证 | 含义 |
|---|---|---|
| `tasks/queue_engine/card_contract.py::validate_card` 只管 `tasks/cards/` 老体系 | 源码 L14-47，校验 `**task_id**` / `goal` / `acceptance[]` / `dependsOn[]` / `fileDomain[]` / `M1` 声明 | 与 `tasks/queue/wo-*.md` 是两套格式，后者无任何机器校验 |
| 队列里实际派发的是 `wo-*.md` 卡 | `tasks/queue/` 下 0030 卡 14,797 B，六段结构 | 正在跑的这套工单不受任何校验 |
| 冻结门是两个硬编码脚本 | `scripts/freeze-approved-v01.py` 10,021 B、`v03.py` 13,039 B，内部写死 `BASELINE`/`TAG`/`expected_tags`/证据目录 | 每冻结一个版本就要复制一份脚本改常量，无通用入口 |
| 有回读脚本但未被冻结门统一调用 | `readback-approved-v01.py` 2,469 B、`readback-approved-v03.py` 4,019 B | 回读能力存在但未纳入标准流程 |
| 18766 登记接口未部署 | `Test-NetConnection 127.0.0.1:18766` → False；登记实际由 `GlobalQueueRegistrar` 写 md | 与本次无关，但同属"规范文本与实际运行时脱节"，本方案不处理 |

---

## 3. 目标与非目标

**目标**

1. `docs/specs/work-order.schema.json`：把 `wo-*.md` 工单卡的**结构**固化为 JSON Schema（draft 2020-12），并配套人读契约 `docs/specs/work-order-contract.md`。
2. `scripts/validate_work_order.py`：一条命令校验任意 `wo-*.md` 卡，输出封闭结论（PASS/FAIL + 错误清单 + JSON 报告），可用作 DoR 闸门与 CI 钩子。
3. 派发前 DoR 硬门：`scripts/dispatch-work-order.py` 派发前强制调用校验，不合格拒绝派发；`--skip-dor` 逃生阀必须留痕。
4. `scripts/freeze_work_order.py`：把 v01/v03 两个硬编码冻结脚本抽象成参数化通用入口，行为口径与前两者对齐。

**非目标（本方案不做）**

- 不改 `tasks/cards/` 老体系的 `validate_card`，两套体系并存，互不影响。
- 不恢复 18766 常驻服务，不把登记接口纳入 DoR。
- 不真正打 tag：通用冻结门本期只交付实现 + dry-run 验证，实打 tag 由主脑/Owner 在验收后执行。
- 不重排已有工单卡格式（存量卡作为正向回归样本，若与 schema 冲突，以"schema 兼容存量"为原则调整 schema，不改卡）。
- 不动 `docs/tracker/北极星上线任务清单.html` 与 `scripts/tracker-live.py`（主脑专属写权）。
- 不动 `H:\UltimaAI\UltimaManager`（只读参照）。
- 不动 0030 已验收的 `src\brain\orchestration\ledger\**`。

---

## 4. 设计

### 4.1 schema 分四层

| 层 | 字段 | 校验强度 |
|---|---|---|
| L1 头部 | `title`（必须 `# Codex 工单 · ` 前缀）、`version`、`status`、`tool` | 必填；`status` 枚举受限 |
| L2 锁定 | `link`（工单号）、`prereq`、`workdir`、`revision`、`usage`、`plan_ref`、`runtime` | 条件必填：有 worktree 的必须给 `workdir`+`revision`；产出型必须给 `plan_ref`（G-PLAN-001） |
| L3 骨架 | `## 0. 范围冻结`（含"只做"+"不做"两节）、`## 1. 任务清单`（表格）、`## 2. 任务明细` | 三段齐全；"不做"为空即 FAIL（防范围无边界） |
| L4 明细 | 每个 `### T# · 标题` 四段：`**文件**`、`**写什么**`、`**验收（Gate T#）**`、`**禁止**` | 四段缺一即 FAIL；`文件` 段不得含"实现XX模块"这类无路径表述 |

**跨层一致性校验**（schema 之外由 validator 执行，这是 schema 表达不了的）

- `## 1. 任务清单` 的 T 集合 == `## 2. 任务明细` 的 T 集合
- T 编号连续（T0..Tn 无跳号）
- 每条 Gate 文本非空且含可验证动词（pytest / 命令 / 差异 / PASS 等），禁止"预计通过""代码质量好"
- `status` ∈ {`可开工`, `排队中`, `待开工`, `已冻结`, `已完成`}；派发门额外要求 ∈ {`可开工`, `排队中`}
- 若声明 `revision`，必须是 40 位或 7-40 位十六进制

### 4.2 validator 接口

```
python scripts/validate_work_order.py <card.md> [--json] [--strict]
```

- 退出码：`0` = PASS（可含 warning）；`1` = FAIL
- `--json` 输出 `{"status":"PASS|FAIL","card":"...","order":"...","errors":[...],"warnings":[...],"schema":"docs/specs/work-order.schema.json"}`
- `--strict` 把 warning 升为 error（用于冻结门前置）
- 纯本地、无网络、无副作用，可被任意脚本 import（暴露 `validate(card_path, strict=False) -> Report`）

### 4.3 DoR 接线点

`scripts/dispatch-work-order.py::main()` 在解析出工单号后、真正起进程前插入：

```
report = validate_work_order.validate(card_path, strict=False)
if report.status != "PASS" and not args.skip_dor:
    print(json) → exit 2（拒绝派发，打印全部 errors）
```

- `--skip-dor` 放行，但必须把 `dor_skipped: true` + `dor_errors[]` 写进 `dispatch-record.json`，事后可审计
- 不改变现有派发流程其余行为（lock、run 目录、codex 参数、状态机）

### 4.4 通用冻结门

```
python scripts/freeze_work_order.py --order wo-xxx --baseline <sha> --tag <tag> \
       --evidence "<glob>" [--gate-json <path>] [--dry-run] [--approve-text "<原文>"]
```

校验链（与 v01/v03 同口径）：

1. `HEAD == --baseline`
2. 无 tracked 改动、无 staged 改动
3. `--tag` 未存在
4. `--evidence` 命中的文件全部存在，且其中 `*.json` 若含 `status`/`all_*pass` 字段必须为 PASS/True
5. 生成 `tasks/queue/gates/<tag>.json`（含 order、baseline、evidence 的 sha256、approved_by、approved_at、scope、known_limit）
6. `--dry-run`：只打印将执行的动作与 gate JSON 内容，不写文件、不打 tag

实打 tag 行为：`git tag -a <tag> <baseline> -m "<message 含 gate json sha256>"`，且打完后 `rev-parse <tag>^{}` 必须等于 baseline。

---

## 5. 验收判据（封闭）

| 判据 | 合格线 |
|---|---|
| 存量正向回归 | `tasks/queue/` 下全部现存 `wo-*.md`（≥6 张）跑 validator 全部 PASS |
| 负向拦截 | 4 类负样本（缺"不做"节 / T 表与明细 T 集合不一致 / 明细缺 `**禁止**` / status 非派发态）全部 FAIL 且错误定位到具体行 |
| DoR 硬门 | 拿负样本走 `dispatch-work-order.py` 被拒（exit 2）且未产生 run 目录 |
| 逃生阀留痕 | `--skip-dor` 能放行且 `dispatch-record.json` 含 `dor_skipped:true` |
| 冻结门 dry-run | 对 0030 的 worktree 跑 `--dry-run` 输出完整 gate JSON，且**未写入任何文件、未打 tag**（`git tag --list` 前后一致） |
| 冻结门口径对齐 | 关键校验项与 v01/v03 一一对应（HEAD/工作树/tag/revision/gate json），逐项在报告里列对照 |
| 不回归 | 0030 的 31 项 ledger 测试仍全绿；无删除测试；无放宽断言 |

---

## 6. 风险与回退

| 风险 | 处置 |
|---|---|
| schema 与存量卡冲突 | 以兼容存量为先，调 schema 不调卡；冲突项记入报告 |
| DoR 硬门误伤紧急派发 | 提供 `--skip-dor`，且强制留痕，不静默 |
| 冻结门被误用真打 tag | 默认 `--dry-run`？否：默认不打 tag，必须显式给 `--tag` + 不给 `--dry-run` 才打；本期验收只用 dry-run |
| 基线缺未提交文件导致全量 pytest 红 | 工单限定测试范围并如实声明，不伪报全量绿 |

---

## 7. 交付物清单

1. `docs/specs/work-order.schema.json`
2. `docs/specs/work-order-contract.md`（人读契约 + 与老 `card_contract` 的边界说明）
3. `scripts/validate_work_order.py`
4. `scripts/freeze_work_order.py`
5. `scripts/dispatch-work-order.py`（小改：DoR 接线 + `--skip-dor`）
6. `tests/test_validate_work_order.py`、`tests/test_freeze_work_order.py`
7. `docs/reports/wo-ultimaagent-20261108-0031-result.md`（含正负样本矩阵、v01/v03 口径对照、dry-run 证据）
