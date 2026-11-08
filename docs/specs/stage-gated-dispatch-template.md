# 单阶段门控派发模板

版本：1.0（工单 `wo-ultimaagent-20261108-0027` T1）

此模板供人工派发控制面复用。它只规定单阶段载荷和前置门，不实现自动调度器，
不触碰模块4 多 Agent 编排。

## 1. 派发前置检查

一次只允许派发一个 `TARGET_STAGE`。除首阶段外，启动前必须对
`PREVIOUS_STAGE` 调用 `stage_gate.check_stage`：

```python
import json
from pathlib import Path

from src.brain.guardrails.stage_gate import check_stage

WORK_ORDER = "<work_order>"
PREVIOUS_STAGE = "<previous_stage>"
EVIDENCE_ROOT = Path("data/evidence")

decision = check_stage(WORK_ORDER, PREVIOUS_STAGE, EVIDENCE_ROOT)
print(json.dumps(
    {"passed": decision.passed, "reasons": decision.reasons},
    ensure_ascii=False,
))
if not decision.passed:
    raise SystemExit(2)
```

控制面必须先保存这次真实输出和退出码，再决定是否启动新会话。返回
`passed=False` 时必须拒绝启动，完整保留 `reasons`；不得绕过、降级或用历史
PASS 替代当前结论。首阶段没有上一阶段，只核对工单依赖和 WIP 约束，不伪造
前置门结果。

## 2. 可复制的单阶段载荷

```text
# 工单 <work_order> / <target_stage> 单阶段派发

你是本阶段执行端。本次只执行 <target_stage>，不得进入后续阶段。

必读：
1. <work-order-card>
2. <immutable-plan>
3. 本阶段引用的现有实现与证据

前置门：
- previous_stage: <previous_stage-or-N/A>
- gate evidence: <current-gate-output-path-or-N/A>
- 只有当前 gate 的 passed=true 才允许启动本阶段。

交付：
- 只修改本阶段授权写域；测试先 RED 后 GREEN；保留全部失败与重跑历史。
- 产出本阶段 receipt.json 后停止，等待独立复核会话。
- independent-review.json 只能由独立复核会话写入，执行端不得写入或修改。
- git 只精确暂存本阶段文件，禁止 git add -A、git add -u、git add . 或通配。

禁止：
- 本阶段不得自行宣布工单全局完成。
- 不得修改看板百分比；看板回写权归主脑。
- 不得把执行端自测冒充独立复核，不得跳过 stage_gate 启动下一阶段。
```

## 3. 阶段结束后的控制面动作

1. 确认执行 commit 只含本阶段授权写域。
2. 另起无执行对话上下文的复核会话；该会话按
   `docs/specs/independent-review-contract.md` 执行并单独提交 `[audit]` commit。
3. 对刚生成的结论重新调用 `check_stage(WORK_ORDER, TARGET_STAGE,
   EVIDENCE_ROOT)`。
4. `passed=True` 才可生成下一个单阶段载荷；否则停止派发并返回全部 reasons。
5. 最后一阶段通过也只代表各阶段门完成；全局完成声明和看板更新仍由主脑执行。

## 4. 拒绝输出最小格式

```json
{
  "work_order": "<work_order>",
  "requested_stage": "<target_stage>",
  "previous_stage": "<previous_stage>",
  "started": false,
  "exit_code": 2,
  "reasons": ["<StageGateResult.reasons 原文>"]
}
```

拒绝记录必须引用本次前置门原始输出，不得只写“未通过”。
