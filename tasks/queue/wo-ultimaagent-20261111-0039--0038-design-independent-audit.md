# DeepSeek 独立审计工单 · 0039 对 0038 自动接力 tools 设计做独立可靠性审计

> 版本：v1.0 ｜ 状态：可开工 ｜ 适用工具：DeepSeek（经 `scripts/audit-work-order.py` 直调，HTTP API，非 codex 进程）
> 链路：`wo-ultimaagent-20261111-0039`
> 执行端：DeepSeek（独立只读审计，不经主脑判断、不沿用 Codex 自审；maker-checker 中的 checker）
> 前置：无（独立审计单，不依赖未冻结前置；被审对象 0038 已提交并推送）
> 方案依据：本卡即审计任务书（审计类单，无独立方案文档）
> 锁定 revision：`a04ce94b`
> 工作目录锁定：`H:\UltimaAI\UltimaAgent`
> 用法：按 ACC 表逐条独立判定，每条输出 PASS/FAIL 与证据，禁止照抄 0038 自述。

---

## 0. 本单定位

本单是 maker-checker 的 checker：0038 由 Codex 设计并实现隔离 PoC（maker），本单由不同执行端 DeepSeek 独立审，确认设计可靠后才允许进入正式落地。目标不是验证「Codex 有没有按卡做」，而是从反方向找设计与实现的缺陷，避免把未经独立验证的自动循环接进真实派发。

审计纪律：

1. 只基于随附的真实代码/文档字节判定，不接受结论性自述；每条结论必须能落到 `文件:行号` 或具体反例。
2. 找不到反例且证据充分才 PASS；证据不足、判不出、对象缺失一律 FAIL（fail-closed），不得用「基本可以」放行。
3. 本单只读：不改任何被审文件，不写 `queue-status.json` 业务数据，不联网、不装依赖。

---

## 1. 审计范围与证据

被审对象（0038 产物，全部作为 evidence 随附）：

- 0038 工单卡（含回执）：`tasks/queue/wo-ultimaagent-20261111-0038--superagent-scheduler-tools.md`
- 设计文档：`tasks/queue/runs/wo-ultimaagent-20261111-0038-20261111T041337063347Z/tools-contract.md`、`.../component-facts.md`
- PoC 与测试：`tasks/queue_engine/auto_relay_poc.py`、`scripts/tests/test_auto_relay_poc.py`
- 主脑方案：`docs/plans/plan-ultimaagent-superagent-scheduler-tools-20261111.md`
- 真实依赖源码（核对设计声明是否属实）：`tasks/queue_engine/state_machine.py`、`tasks/queue_engine/priority_deps.py`

Non-goals：不重新做 T0 全量盘点；不审 0038 之外的工单；不直接修改代码；不评价队列数据。

---

## 2. 独立审计门（ACC 表）

| 门 | 审查项（判什么） | 判定方式（怎么判 / FAIL 条件） |
|---|---|---|
| ACC-1 | 主循环有界性：每条分支是否都有终止或上界，是否存在无界空转、死循环、活锁；步数上限在 PoC 代码里是否真实生效，而非仅文档声明 | 通读 `auto_relay_poc.py` 循环与步数控制，给出关键判断的 `文件:行号`；找到任一可无限执行或无终止保证的路径即 FAIL |
| ACC-2 | fail-closed 真实性：证据不足、依赖未满足、异常输入时，选单/状态机是否真的拒绝而非静默当成功 | 主动构造「信息缺失 / 依赖未满足 / 异常」路径并追踪 PoC 行为；找到一条异常或缺证据路径被静默当成功即 FAIL |
| ACC-3 | 状态映射唯一性：八态是否每个都有唯一去向、无第三套枚举；PoC 是否复用 `QueueState` 而非自定义状态集合 | 对照 `state_machine.py` 与 PoC 的状态使用，grep 状态名；出现未登记的新状态名，或同一状态存在两个互相矛盾去向即 FAIL |
| ACC-4 | 失败恢复与幂等：重试上限/退避是否成立；中断重启是否会重复已完成的外部副作用；同一回执重复投递是否只生效一次 | 沿恢复路径读代码并构造重复投递场景；发现可超上限重试、重复执行外部副作用、或重复投递产生 >1 条记录即 FAIL |
| ACC-5 | 名额兜底：无 run 的 audit 单是否真的不再永久占位（要么算出非空等待时长，要么标无效持有） | 在 PoC 逻辑上构造「无 run audit 单」追踪其名额计算；该单仍被永久计入名额、两种出路都不成立即 FAIL |
| ACC-6 | PoC 与设计一致性：PoC 实现的接口/状态/循环是否与 `tools-contract.md` 一致；有无「设计写了 PoC 没实现」或「PoC 实现了设计没声明」 | 逐条比对设计条目与 PoC 实现，列出双向差异；发现任一不一致项即 FAIL |
| ACC-7 | 测试有效性（防假通过）：6 个用例是否真的断言关键行为而非只测桩/helper；删除某个关键保护（步数上限/幂等/依赖门）后是否至少一条测试变红 | 读 `test_auto_relay_poc.py` 的断言与夹具依赖；存在关键行为无测试覆盖，或测试不依赖被测实现即可通过即 FAIL |
| ACC-8 | 隔离性与事实准确：PoC 是否真的不被正式入口 import、不挂自启、不调真实 Codex/付费接口；`component-facts.md` 对真实组件的关键判定是否与所给源码一致 | 用所给源码核对事实判定，并检查 PoC 外部调用点；发现正式入口引用/自启/真实外部调用，或关键事实与源码不符即 FAIL |

---

## 3. 输出要求

1. 逐门输出 `ACC-n: PASS/FAIL - 证据`，证据含 `文件:行号` 或反例构造与其预期/实际结果；空证据的 PASS 不成立。
2. 任一 FAIL 即整体不通过；列出全部缺陷并标严重级（P0 阻塞落地 / P1 落地前必修 / P2 建议），只给问题与判定，不给修复代码。
3. 若判 PASS，逐条写明「已尝试哪些反例、为何不成立」，不得只写「未发现问题」。
4. 审计结论由 `audit-work-order.py` 写入本单 run 目录的 `audit.json`，并绑定所判对象的 sha256。

---

## 4. 禁止

1. 不得照抄 0038 卡/回执的结论；不得用「文档说已实现」代替读代码。
2. 不得修改任何被审文件或 `queue-status.json`；不得联网、不装第三方依赖。
3. 不得在证据不足时给 PASS；不得把「判不出」标成通过。
4. 不得扩大审计范围到 0038 之外的工单或数据。
