# 派发载荷 · wo-ultimaagent-20261112-0044

## 必读（按顺序，读完再动手）

1. `docs/INDEX.md` —— 权威文档总索引，确认本次改动落在既有治理体系中
2. `tasks/queue/wo-ultimaagent-20261112-0044--mainbrain-teaching-phase1.md` —— 工单卡（唯一执行依据）
3. `docs/plans/plan-ultimaagent-mainbrain-teaching-phase1-20261112.md` —— 方案，**第 2 节是 11 条探针的原始实测输出，是本单的事实基线，必须逐条读完**
4. `docs/references/lessons-log.md` 的 **L138 / L157** —— 为什么本单不做提示词调优（行为层约束对 8B 无效，已两次实测）

## 差事

按工单卡 **T0 → T1 → T2 → T3 → T4** 顺序执行。**每完成一个 T，先跑该 T 的 Gate，全绿才进下一个 T。任何 Gate 未过，停下来在回执里写明卡在哪，不要跳序、不要"先做完再补测"。**

## 硬约束（违反即作废，不接受事后补救）

1. **四项改动全部落代码层**，不许用"改提示词让模型自觉"的方式替代。L138/L157 已证明对 8B 无效。
2. **不改** `_risk_gate` / `_no_tool_gate` 任何正则或话术——A/B 两类已 100% 生效，动它只有风险。
3. **不改** `MAINBRAIN_SYSTEM_PROMPT` 与 `docs/specs/mainbrain-rules-baseline.md`。query / diagnose 分支只**追加**新 system 块，现有文本一字不动。
4. **必须保留** `disable_thinking=False`。L140 已证明关思考会让 qwen3 在极短判定上返回空串，整条逻辑会静默降级。
5. **不引入**新依赖，只用标准库 `re` / `datetime`。
6. **不碰** `src/voice-next/**`、`src/brain/voice/**`、`src/host-shell/**`、`UltimaAgent.Hud/**`、`installer/`。
7. **不改** `tasks/queue/queue-status.json`（派发器写入的本单状态流转除外）。
8. **禁止** `git add -A`（仓库常态有数百未跟踪文件）。提交按路径精确 add。
9. **不联网、不装依赖。**
10. **不得用 `git restore` / `git stash` / 操作 index 制造「queue-status 干净」的假象。**

## 判据要窄，别为了过门把功能改坏

四类病各有明确的正例与反向验证。**判据过宽会误伤正常回答**，工单卡里已写死反向验证条目，必须逐条跑：

- 「删除文件前要先备份」→ **不得**被 `_claim_clean` 改写
- 「这个方案已经改好了吗」→ **不得**被 `_claim_clean` 改写（是疑问，不是完成态声明）
- 「帮我把这个怎么弄一下」→ **必须**判 `task`（含代劳指向）
- 「如何备份数据库」→ **必须**判 `query`（纯方法求问）

## 起跑点

T0 先写测试到 RED，再实现到 GREEN。不要先改实现再补测试——本单四类病的判据都依赖"先定义清楚什么样算病"。
