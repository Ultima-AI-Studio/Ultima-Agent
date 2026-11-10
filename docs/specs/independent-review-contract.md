# 独立复核结论契约

版本：1.0（工单 `wo-ultimaagent-20261108-0027` T1）

## 1. 目的与边界

阶段执行端和阶段判定端必须是两个物理分离的会话。阶段执行端只交付代码、
测试、运行证据和 `receipt.json`；独立复核会话读取这些产物并独立执行确定性
检查，随后才可写入复核结论：

```text
data/evidence/<work_order>/<stage>/independent-review.json
```

`independent-review.json` **只能由独立复核会话写入或修改，执行端不得写入、
补写、修正或代签**。执行 commit 与复核 commit 必须分开；复核 commit message
必须以 `[audit]` 开头。

本契约不宣称 Git author 字段或 `role` 字符串本身能够证明进程身份。会话隔离、
派发顺序和复核 commit 的产生者由派发控制面保证；`stage_gate` 负责对落盘结论
做 fail-closed 的结构、证据与结论语义机检。本期不实现自动调度器。

## 2. 路径与解析基准

- `<work_order>` 必须与文件中的 `work_order` 完全一致。
- `<stage>` 是被复核的单阶段标识，例如 `T0`、`T1`、`T2`。
- 文件编码为 UTF-8，根节点必须是 JSON object。
- `evidence[].path` 相对调用 `check_stage` 时传入的 `evidence_root` 解析。
  标准根为仓库下的 `data/evidence`，因此示例路径形如
  `wo-example/T0/audit-test-rerun.log`。

## 3. 顶层字段

结论文件同时复用 `ReceiptValidator` 与 `ReviewResult`，不得另造第二套审计
数据结构。

| 字段 | 类型 | 规则 |
|---|---|---|
| `work_order` | string | 非空，且等于目录中的 `<work_order>` |
| `status` | string | 独立复核完成后写 `COMPLETED` |
| `reviewReason` | string | 非空，说明审查范围、结论和关键依据 |
| `stdoutText` | string | 非空，摘要记录真实命令、计数与退出码 |
| `evidence` | array | `ReceiptValidator` 证据列表；每项含 `path`、合法 `kind`、非空 `summary`，路径必须存在 |
| `acceptance` | array | 每项含非空 `id`、`result`、`evidence`；`result` 只能为 `PASS` 或 `FAIL` |
| `ok` | boolean | 必须与 `ReviewResult` 的 blocker 语义一致；只有 `blocker == 0` 才能为 `true` |
| `role` | string | 只能为 `eng.audit` 或 `eng.security` |
| `blocker` | non-negative integer | 必须等于 `findings` 中 `severity=blocker` 的实际数量；大于 0 时门拒绝 |
| `major` | non-negative integer | 必须等于 `findings` 中 `severity=major` 的实际数量 |
| `minor` | non-negative integer | 必须等于 `findings` 中 `severity=minor` 的实际数量 |
| `checked` | array[string] | 非空；每项写明实际动作和原始输出路径，至少包含“测试复跑”和“写域核对” |
| `findings` | array[object] | 复用 `Finding`：`role`、`severity`、`item`、`detail` |

`findings[].severity` 只能为 `blocker`、`major`、`minor`；
`findings[].role` 必须等于顶层 `role`；`item` 必须是非空字符串，`detail`
必须是字符串。`blocker`、`major`、`minor` 由 `ReviewResult.as_dict()` 重新计算，
声明计数与计算计数不一致时门拒绝。

`checked` 必须陈述真实完成的动作，不得把计划、历史日志或执行端自测写成
独立复核。T2 演练还必须含“断言抽查”，并为三项动作分别给出原始输出路径。

## 4. 完整示例

```json
{
  "work_order": "wo-example",
  "status": "COMPLETED",
  "reviewReason": "独立复跑与写域核对均通过，无 blocker。",
  "stdoutText": "7 tests passed; forbidden path hits: 0; exit 0.",
  "evidence": [
    {
      "path": "wo-example/T0/audit-test-rerun.log",
      "kind": "log",
      "summary": "独立复跑原始输出"
    },
    {
      "path": "wo-example/T0/audit-write-domain.log",
      "kind": "log",
      "summary": "写域核对原始输出"
    }
  ],
  "acceptance": [
    {
      "id": "AUDIT-T0",
      "result": "PASS",
      "evidence": "测试与写域核对均通过。"
    }
  ],
  "ok": true,
  "role": "eng.audit",
  "blocker": 0,
  "major": 0,
  "minor": 0,
  "checked": [
    "测试复跑: wo-example/T0/audit-test-rerun.log",
    "写域核对: wo-example/T0/audit-write-domain.log"
  ],
  "findings": []
}
```

存在 blocker 时，`ok` 必须为 `false`，对应 acceptance 必须为 `FAIL`，并在
`findings` 中保留具体 blocker。不得为了放行删除失败证据或把 blocker 降级。

## 5. 阶段提交与放行顺序

1. 执行会话只完成一个阶段，精确提交该阶段授权写域和执行回执。
2. 新的独立复核会话复跑测试、核对执行 commit 写域、抽查断言/产物。
3. 复核会话写原始输出与 `independent-review.json`，精确提交，commit message
   以 `[audit]` 开头。
4. 派发端调用：

   ```python
   from pathlib import Path
   from src.brain.guardrails.stage_gate import check_stage

   result = check_stage("wo-example", "T0", Path("data/evidence"))
   if not result.passed:
       raise SystemExit(f"refuse dispatch: {result.reasons}")
   ```

5. 只有 `passed=True` 且 `reasons=[]` 才能启动下一阶段。缺文件、非法 JSON、
   非审计角色、blocker 未清零、`checked` 为空或缺少规定检查项均拒绝放行。

执行会话不得自行宣布工单全局完成，也不得修改看板百分比；全局结论和看板
回写权属于主脑。
