# 派发载荷 · wo-ultimaagent-20261112-0045

## 必读（按顺序，读完再动手）

1. `docs/INDEX.md` —— 权威文档总索引，确认本次改动落在既有治理体系中
2. `tasks/queue/wo-ultimaagent-20261112-0045--mainbrain-teaching-phase2-clarify.md` —— 工单卡（唯一执行依据）
3. `docs/plans/plan-ultimaagent-mainbrain-teaching-phase2-20261112.md` —— 方案，**第 1 节是 7 条 F 探针的原始实测输出，是本单的事实基线，必须逐条读完**
4. `docs/references/lessons-log.md` 的 **L138 / L157 / L165 / L166** —— 为什么本单不做提示词调优、为什么出口改动必须先跑既有契约测试
5. 前置单回执：`tasks/queue/wo-ultimaagent-20261112-0044--mainbrain-teaching-phase1.md` 的 §5-§7 —— Phase 1 已冻结了什么，本单**不得回退**任何一条

## 差事

按工单卡 **T0 → T1 → T2 → T3** 顺序执行。**每完成一个 T，先跑该 T 的 Gate，全绿才进下一个 T。任何 Gate 未过，停下来在回执里写明卡在哪，不要跳序、不要"先做完再补测"。**

## 硬约束（违反即作废，不接受事后补救）

1. **四项改动全部落代码层**，不许用"改提示词让模型自觉"的方式替代。L138/L157 已证明对 8B 无效。
2. **不改** `_risk_gate` / `_no_tool_gate` 任何正则或话术——A/B 两类已 100% 生效，动它只有风险。
3. **不改** `_classify_intent` 的模型调用与判据本身（必须保留 `disable_thinking=False`，L140 已证明关思考会返回空串）。本单只在分类**之后**加槽位门，不把分类器改成直接返回 clarify。
4. **不改** `MAINBRAIN_SYSTEM_PROMPT` 与 `docs/specs/mainbrain-rules-baseline.md`。
5. **零回退 Phase 1**：`_claim_clean`、`_SERVILE_TAIL_PATTERN`（两分支）、`_is_too_short`（`minimum=2`）、`_DIAGNOSE_DIRECTIONS`、`_ask_query_branch` 入口的求代劳短路，全部原样保留；Phase 1 的既有测试断言一律不得修改。
6. **不引入**新依赖，只用标准库 `re` / `time` / `datetime`。
7. **状态不落盘**：`_PENDING_CLARIFY` 只在进程内存，不写文件、不入库、不进 `EVENT_BUS`。
8. **`ask_once` 签名不变**（`query, max_tokens=None`），不得新增必填参数。
9. **不碰** `src/voice-next/**`、`src/brain/voice/**`、`src/host-shell/**`、`UltimaAgent.Hud/**`、`installer/`。
10. **不改** `tasks/queue/queue-status.json`（派发器写入的本单状态流转除外）。
11. **禁止** `git add -A`（仓库常态有数百未跟踪文件）。提交按路径精确 add。
12. **不联网、不装依赖。**
13. **不得用** `git restore` / `git stash` / 操作 index 制造「queue-status 干净」的假象。

## 判据要窄，别为了过门把功能改坏

槽位门最大的风险是**误伤正常派单**。工单卡写死了四条反向样本，必须逐条跑：

- 「帮我把桌面的日志整理一下」→ `_slot_gate` 必须返回 `None`（宾语「桌面的日志」具体）
- 「帮我把 D:\logs\a.log 重命名成 b.log」→ 必须返回 `None`（有路径）
- 「1+1等于几」→ 必须返回 `None`
- 「什么是市盈率」→ 必须返回 `None`

同样，澄清话术**不得**变成服务性反问（那是 Phase 1 已修掉的 P4），也不得保留「你再说一遍」式推回。

## 起跑点

T0 先写测试到 RED，再实现到 GREEN。不要先改实现再补测试——槽位判据的精度完全依赖"先把什么样的句子算缺槽位定义清楚"。

## 验收口径提醒

全量回归的基线是 Phase 1 冻结时的 **475 passed / 1 failed**（唯一失败为 `test_connectivity_m6.py::TestC1Environment::test_ollama_has_brains` 的 ollama-not-in-PATH 环境噪声）。本单**不得新增任何其他失败**；该条噪声在前后应同样存在。
