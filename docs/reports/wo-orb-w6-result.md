# WO-ORB-W6 编排层设施补齐执行结果

- 工单：`wo-orb-w6`
- 执行端：Codex
- 执行日期：2026-11-08
- 性质：repair 续行；保留上一轮已通过实现，本轮不重写代码
- 自检结论：`PASS`（仅为 Codex 自检，不替代 DeepSeek 独立审计）

## 1. 改动清单

| 文件 | 产出 |
|---|---|
| `src/brain/orchestrator.py` | DeepSeek ②拆解、③工单、④排程 stage 的独立调用、九字段落盘、限定重试与 fail-closed |
| `src/brain/sentinel.py` | ⑤常驻监工心跳、三判据连续异常、恢复事件与单例锁 |
| `tests/test_orchestrator.py` | 外脑调用、独立 system、九字段、重试边界、失败落盘及密钥不落盘的全 mock 单测 |
| `tests/test_sentinel.py` | 正常、进程消失、仅两 tick、第三 tick 异常、恢复和单例锁单测 |
| `tests/test_orchestrator_sentinel_integration.py` | 假 run 目录下 stage 落盘与三 tick 异常事件联调 |
| `docs/reports/wo-orb-w6-result.md` | 本执行结果与验收证据 |

## 2. 验收证据

固定解释器：

```text
H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe
```

修正后的 `tests/` 全量门（2026-11-08 fresh 复跑）：

```powershell
H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe -m pytest tests/ -o addopts= -q
```

结果：

```text
..............                                                           [100%]
14 passed in 0.22s
exit code 0
```

逐项自检：

- T1 `orb-w6-orchestrator`：任务卡 acceptance 7/7 所覆盖测试均在本次全量门中通过；HTTP 被 mock，未调用真实 DeepSeek API。
- T2 `orb-w6-sentinel`：任务卡 acceptance 7/7 所覆盖测试均在本次全量门中通过；进程身份被打桩，未杀进程。
- 联调：假 run 目录完成 3 tick，断言 `heartbeat.jsonl` 为 3 行，且 `anomaly.json` 的 `kind` 为 `exit-anomaly`、`consecutive` 为 3。
- 全量收集边界严格为 `tests/`；未运行仓库根收集。上一轮根收集失败的根因是历史目录 `Topo Backup` 被 pytest 收集并产生 3,430 个 errors，不是本单实现失败。

## 3. 越界声明

- 无本单越界改动。
- 未改 `state_machine.py`、`dispatcher.py`、`dispatch-work-order.py`、看板或 `tasks.json`。
- 未修改工单与两张任务卡，未触碰派发链，未写入或持久化 `DEEPSEEK_API_KEY`。
- 未运行真实 DeepSeek 请求，未打 tag。
- 工作区存在大量本单开工前已有的其他改动和未跟踪文件；本单仅精确提交上表六个文件，不纳入任何无关路径。

## 4. 遗留项

- ⑦独立审计与⑧整体审计仍按冻结方案由 DeepSeek/人工链路后续执行；Codex 自检不构成验收，也无 tag 权限。
- 真实 DeepSeek API 冒烟为 T2 可选项，本次依硬约束未执行。
- orchestrator 接入实际派发链、sentinel 挂载 run 目录及启用常驻运行不在本工单范围内；本单仅交付冻结方案规定的两个设施模块及测试。
