# wo-ultimaagent-20261113-0064 · Autoloop 三单拆解执行报告

> 执行日期：2026-11-13 至 2026-11-14（Asia/Shanghai）  
> 工单：`wo-ultimaagent-20261113-0064`  
> 结果：自检 PASS；仅产卡与拆解/执行报告，未产实现  
> 交审状态：三张卡均为“待审卡”，尚未经过 Owner 与独立审计，不构成派发授权

## 1. 改动文件清单

本单新建以下交付文件：

1. `tasks/queue/wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md`
2. `tasks/queue/wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md`
3. `tasks/queue/wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md`
4. `docs/plans/next-autoloop-三单拆解-20261113.md`
5. `docs/reports/decompose-wo-ultimaagent-20261113-0064.md`

未修改工单卡 0064、方案 v0.3、基线、队列、tracker、现有工单或代码。

## 2. T1–T5 实际结果

| T | 实际结果 | 证据 |
|---|---|---|
| T1 | PASS | 拆解文档 §1–§3 已落盘；依据清单按派单要求合并为五行来源，冲突 a–f 均有“冲突→处置”，延后项与方案 §7 逐项一致。 |
| T2 | PASS | 0061 为“待审卡”；范围、任务、任务明细、DoR、写域、禁止项与粘贴模板齐备；每个 T 均有文件/写什么/Gate/禁止；必需机检断言已落卡。 |
| T3 | PASS | 0062 为“待审卡”；前置明确 0057∧0059 冻结并给可执行 readback；§27.1–§27.4 各有字段表、映射规则、负例；目标排除词仅以“不在本卡”形式出现。 |
| T4 | PASS | 0063 为“待审卡”；前置明确 0057 冻结后切；三值表、投影/解除、连续观测告警、四条 Gate、E-01 显式挂起与 `TBD-RUNTIME` 口径齐备。 |
| T5 | PASS | 拆解文档 §4–§8 已落盘；主文归属无重复、依赖图含三卡与 P2 准入、方案 §3/§4/§6 Gate 均已映射、三张卡的 INVEST 与 DoR 均有结论。 |

## 3. Gate 逐项结果

### Gate T1

- 依据表存在且非空：PASS。
- 冲突 a–f 均各占一行并有受限处置类型：PASS。
- 本批不做与方案 §7 表逐项一致：PASS。
- 额外发现并记录风险：方案文件首行显示 v0.1，而派单事实指定 v0.3；未越权修改源方案。

### Gate T2（0061）

- 必需章节存在：PASS。
- T1–T5 的文件/写什么/Gate/禁止字段齐备：PASS。
- 卡面未出现 `W_VOLATILE_COUNT_WRITTEN`：PASS（validator warnings 中无此代码）。
- normal/duplicate/orphan reconcile 断言、唯一写者搜索、reconcile 只读性、writer 重投幂等与 selftest 均已写入 Gate：PASS。
- 明确“不依赖 0057 冻结”：PASS。

### Gate T3（0062）

- §27.1–§27.4 均含字段表、映射规则、负例：PASS。
- `cancel_observe` 在卡内只命中一次，原文为“`cancel_observe` 不在本卡，落 §25.10，由 0063 负责”：PASS。
- 前置以队列 state、冻结 commit/tag 的独立读回步骤表达：PASS。
- 卡面未出现 `W_VOLATILE_COUNT_WRITTEN`：PASS。

### Gate T4（0063）

- 三值表覆盖 `running/not_running/unknown` 且逐值有判定条件：PASS。
- `unknown` 同时规定“不落 `CANCELLED`”和只投影 `CANCELLED_PENDING`：PASS。
- 解除规则与连续 `3` 轮人工告警均存在：PASS。
- G-25.10-A 至 G-25.10-D 齐备：PASS。
- 对外口径固定为“E-01 显式挂起”，真实运行判据标 `TBD-RUNTIME`：PASS。
- 写域明确为“§25.10 原文除新增外 diff 为空”：PASS。

### Gate T5

- 主文归属覆盖 M3、M4、M7、`session_id`、`cancel_observe`、writer，且各只有一处主文：PASS。
- 依赖图覆盖 0064、0061、0062、0063 与 P2 spike 准入关系：PASS。
- 方案 §3/§4/§6 Gate 覆盖映射无“未归属”行：PASS。
- 0061/0062/0063 的 Independent、Small、Testable 与 DoR 五项均有“通过＋理由”：PASS。
- 本报告含文件清单、Gate 结果、风险与越界声明：PASS。

## 4. `validate_work_order.py` 真实输出

执行命令：

```powershell
python scripts\validate_work_order.py tasks\queue\wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md --json
python scripts\validate_work_order.py tasks\queue\wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md --json
python scripts\validate_work_order.py tasks\queue\wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md --json
```

0061：

```json
{
  "status": "PASS",
  "card": "tasks\\queue\\wo-ultimaagent-20261113-0061--autoloop-p0-single-writer.md",
  "order": "wo-ultimaagent-20261113-0061",
  "errors": [],
  "warnings": [
    {
      "code": "W_LEGACY_PROFILE",
      "line": 1,
      "message": "存量卡使用 legacy-queue 兼容 profile"
    }
  ],
  "schema": "H:\\UltimaAI\\UltimaAgent\\docs\\specs\\work-order.schema.json"
}
```

0062：

```json
{
  "status": "PASS",
  "card": "tasks\\queue\\wo-ultimaagent-20261113-0062--autoloop-p1-contracts.md",
  "order": "wo-ultimaagent-20261113-0062",
  "errors": [],
  "warnings": [
    {
      "code": "W_LEGACY_PROFILE",
      "line": 1,
      "message": "存量卡使用 legacy-queue 兼容 profile"
    }
  ],
  "schema": "H:\\UltimaAI\\UltimaAgent\\docs\\specs\\work-order.schema.json"
}
```

0063：

```json
{
  "status": "PASS",
  "card": "tasks\\queue\\wo-ultimaagent-20261113-0063--autoloop-p2-cancel-observe.md",
  "order": "wo-ultimaagent-20261113-0063",
  "errors": [],
  "warnings": [
    {
      "code": "W_LEGACY_PROFILE",
      "line": 1,
      "message": "存量卡使用 legacy-queue 兼容 profile"
    }
  ],
  "schema": "H:\\UltimaAI\\UltimaAgent\\docs\\specs\\work-order.schema.json"
}
```

说明：三张卡按硬约束使用“待审卡”，而当前 structured-v1 schema 的状态枚举不含该值，因此 validator 按 legacy-queue 兼容 profile 读取并给出 `W_LEGACY_PROFILE`。三张卡均为 `PASS`，`errors` 为空，且没有 `W_VOLATILE_COUNT_WRITTEN`；本单未越权修改 validator/schema 来消除兼容提示。

## 5. 依赖与状态声明

- 0061：不依赖 0057 冻结；仍须 Owner＋独立审计通过后才可派发。
- 0062：仅在 0057 与 0059 均冻结且凭据独立读回成立后执行。
- 0063：仅在 0057 冻结且 `freeze_commit` 或冻结 tag 可验证后执行。
- P2 spike：前置为 0061 完成＋0062 定稿；不在本批。
- 0059 的封闭清单没有重拆或缩范围。

## 6. 越界声明与风险

越界写入：**无**。本次写操作只落在工单 allowlist 的五个 Markdown 文件；未写代码、未建目录、未改基线、未改队列、未改 tracker、未改 v1 冻结参数，未访问 `H:\UltimaAI\UltimaAgentNext`，未调用 18766，未 commit/push/tag。

仓库在本单开始前即存在大量其他已修改/未跟踪内容；本单未清理、覆盖或归因这些用户/后台工作。最终范围核验只针对上述五个 allowlist 路径，并保留预存工作树不动。

待 Owner/独立审计关注：

1. 方案文件版本头与派单指定版本不一致；需由权威源维护者确认，不应由 0064 越权修订。
2. structured-v1 schema 暂不接受“待审卡”，导致兼容 profile warning；这不是卡面内容失败，也不应在本单扩域修 schema。
3. 0063 的 E-01 真实运行闭合项仍为 `TBD-RUNTIME`；静态审卡通过不能替代 Next 实现后的运行证据。

## 7. 本单自证

- 文件清单：见 §1。
- Gate 逐项结果：见 §2–§3。
- 越界声明：见 §6，结论为“无”。
- 依赖声明：见 §5。
- 无编造数值：卡面未写易变环境计数；语义阈值均来自方案权威条款。
- 未碰禁写域：见 §6。
- 报告落盘路径：`docs/reports/decompose-wo-ultimaagent-20261113-0064.md`。

READY_FOR_DEEPSEEK_AUDIT

