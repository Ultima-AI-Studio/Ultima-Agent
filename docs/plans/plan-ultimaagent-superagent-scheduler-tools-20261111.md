# 方案 · SuperAgent 调度器整合为本地自动化 tools（2026-11-11）

> 状态：主脑已定方向，随工单 0038 落盘
> 对应工单：`tasks/queue/wo-ultimaagent-20261111-0038--superagent-scheduler-tools.md`
> 通道：独立任务通道（Codex 独立产出整合设计，主脑不参与判据定夺）
> 锁定 revision：`c9ecfb7a56e2335ec7bb6404faa9a9f8213b3a30`

## 1. 问题

现有任务系统是「半自动」：单工单内部（执行、门禁、回执、状态校验、超时熔断、进程树清理）已经自动；但**工单之间的调度仍靠人**——挑单、触发派发、触发审计/冻结、BLOCKED 释放都要人手敲命令。仓内没有任何常驻进程把「上一单完成 → 取下一单 → 派发」这个循环跑起来。

同时存在双轨：`scripts/` 下的独立脚本链（实际在用）与 `tasks/queue_engine/` 下的模块化引擎（八态状态机、规划器、派发器，零件齐全但未接成常驻），两者状态枚举不一致，是「乱」的结构性来源之一。

## 2. 目标

把 DeepSeek Super Agent 原型里的调度设计，落地为一个可接入现有任务系统的 **Python 自动化 tools**，让工单之间的调度自动、可信、可恢复；人只在门禁处介入。

本单产出定位为**整合设计 + 最小 PoC + 分阶段落地计划**，不是一次性全量实现。

## 3. 设计依据（现成件，不从零发明）

| 能力 | dsh 原型（TS，只读参考） | 本地可复用件 |
|---|---|---|
| 调度节拍循环 | `src/app/passes.ts`、`src/core/part.ts` | 待实现为 Python 主循环 |
| 效果队列/重试/退避 | `src/app/effects.ts` | `queue_engine` 存储 + 待设计队列表 |
| 回执不丢 | `src/app/outbox.ts` | `receipt_contract.py` |
| Ticket 状态机 | `src/core/tickets.ts`、`stage.ts` | `queue_engine/state_machine.py`（八态） |
| 派发/恢复 | `src/core/assignments.ts`、`intake.ts` | `queue_engine/dispatcher.py`、`priority_deps.py` |
| 健康注册 | `src/infra/health.ts` | 看门狗 `watchdog-loopguard.py` |
| 图状态机/持久化/审批中断 | — | `libs/orchestration/langgraph`（已入库） |

## 4. tools 形态（要求 Codex 在设计中明确并给取舍）

- 形态候选：常驻无窗 Python 服务 / `queue-engine` 子命令 / 可被主脑调用的模块。必须给出推荐与理由，并说明如何与现有 `dispatch-work-order.py`、`queue_engine` 共存或收敛。
- 必须定义：启停接口、状态查询接口、选单规则、自动接力触发条件、失败重试与幂等、持久化位置、与 `queue-status.json` 的权威关系。
- 必须给出状态映射：dsh Ticket 状态 ↔ `queue_engine` 八态，且不允许出现两套并存的新枚举。

## 5. 边界（硬约束）

1. 不整仓拼装 dsh：它是 TypeScript/Node 且绑 dsh 平台，禁止引入 Node 运行时；只做概念级 Python 重写（沿用 2026-11-03 排查结论，MIT 许可允许）。
2. 不破坏已冻结的语音链路（KWS→ASR→8B→TTS）与 OpenJarvis 验收基础。
3. 人工门保留：BLOCKED 释放、发布、独立审计仍需 human/brain，调度过程自动但不取消门禁。
4. 本单不直接改 `queue-status.json` 业务数据、不重写存量工单状态；存量任务重梳理是后续独立一单。
5. 不引入第三方联网依赖，优先 `libs/wheels` 离线源；不 `git add -A`。
6. 名额兜底要纳入设计：无 run 的 audit 单不得永久占位（要么用记录时间算时长，要么标无效持有）。

## 6. 交付要求

1. 现状盘点与组件事实清单（以代码为准，不凭文档反推）。
2. TS→Python、dsh→本地的逐组件差距与复用/新写/改造判定。
3. tools 接口契约与状态映射。
4. 自动接力主循环 + 失败恢复 + 名额兜底设计。
5. 最小 PoC：在夹具上演示「上一单完成 → 自动取下一 QUEUED 单 → 派发」闭环，并附可复现命令与输出。
6. 分阶段落地计划，每阶段带可机检 Gate 与回滚策略。

## 7. 已知风险

- 双轨收敛方向若选错，会产生第三个混乱源；要求设计中明确老脚本链的封存/退役路径。
- 部分历史单缺机器可读证据，自动调度对这类单只能标 `unverifiable`，不允许猜状态。
- 自动接力的选单规则若纯靠优先级，可能与主脑意图冲突；要求保留 brain 可介入的显式入口。
