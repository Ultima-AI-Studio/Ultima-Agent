# source13 E03 round3 单例准备实施计划

> **For agentic workers:** Use superpowers:executing-plans inline; one fresh whole-package preparation reviewer after implementation. Preserve the existing evidence workspace.

**Goal:** 以同候选前两轮独立实际PASS为前置，准备第三轮单例入口，保留连续三轮及负例的原验收要求。
**Architecture:** 复用已通过round2的实际执行/夹具/清理路径，入口仍为单一固定case。保留round1检查，增加round2原终态、独立结果和累计登记的哈希与语义校验，authority必须按顺序绑定两轮。旧结果只作前置资格，不充作第三轮成果。
**Tech Stack:** 现有Python/pytest、标准库JSON和SHA-256、既有Win32适配；不安装依赖。
**Spec:** docs/specs/jarvis-work-capability-contract-20261101.md（r2）及docs/plans/jarvis-work-capability-delivery-plan-20261101.md T2。

## Global Constraints

原工单wo-ultimaagent-20261101-0021。候选269aca511d88412dbb9c15d23911138469a37aa2；仅当前qwen3-8b-uncensored，digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。KWS/语音/生产进程、全部旧失败、原样本、完整选区、副窗口及最终事实要求不变。15秒开始、20秒夹具启动、60秒proof、120秒准入、CLI300/SDK1800/controller315秒时限不变。

写域仅本计划、新证据根data/evidence/jarvis-work-capability/T2/e03-source13-round3-20261106、报告、原单/T2/current-run、原全局登记行及文档镜像。新根是隔离的验收准备工作区；不写旧包或候选源码。当前目标已恢复active；前两轮实际和结果复核分配均已消耗，本计划只释放离线准备及原技术门要求的一次只读全包准备审查，不签发第三轮实跑authority。

## Review Focus

1. round1与round2独审JSON的execution字段不同，必须验证各自实际格式，不篡改原收据以迎合解析器；用合成完整收据覆盖两种格式。
2. 有两条PASS却是重复轮次/旧候选/错误哈希时应在native构造前拒绝；覆盖第二轮语义、缺依赖及链错绑反例。
3. round2累计登记必须确实绑定这两份终态及独审，前轮registration哈希也相符；覆盖漏记/重复/顺序及前置hash错误。
4. authority不得漏掉或交换两轮、使用旧round2作用域或复用已消费case；保留原独占与时限测试并追加第二轮authority绑定反例。
5. 离线fake native不证明真实第三轮窗口、事实、清理或语音体验；审查必须明确不授予actual/result-review、E03整组、T2或Owner通过。

## Task 1: 前置证据、测试与最小实现

**Files:** 新根code/acceptance_entry.py、code/source_candidate_guard.py、code/test_acceptance_entry.py、code/test_acceptance_backend.py、继承的code/test_round2_predecessor.py及新增code/test_round3_predecessors.py；固定inputs/prior-round1与prior-round2各三收据；其余后端/夹具/适配字节复用。
**Interfaces:** predecessor_review(root)继续验证round1并返回原绑定；新增predecessor_reviews(root)返回按round1、round2排序的两个绑定。verify_package和validate_release调用新列表检查；CASE=e03-round3，SCOPE=e03-round3-acceptance。

- [ ] 校验parent51封存文件，复制code/inputs/support和测试执行器，不复制release/actual。保存两轮原收据字节、路径和SHA，以及原状态快照。
- [ ] 先调整离线测试材料为两轮实际schema，追加test_round3_predecessors.py：正确两轮允许一次模拟；round2未独审、facts/final_claim失败、旧候选/错误轮次/终态失败、缺三依赖、累计条目重复/顺序错/hash错、旧round2authority及漏/错第二绑定均拒绝，断言native尚未构造且无actual目录。
- [ ] 用verification/run-entry-tests.py predecessors-red code/test_round3_predecessors.py观察RED。Expected:新round2语义/链校验反例失败，不得出现导入/语法错误；原已拒绝的authority类可保持通过。
- [ ] 实现最小双前轮核验。round1规则保留；round2检查raw PENDING且机械/清理/审计/保护PASS、独审八verdict、同runtime/model/digest、CLI1且无重试、原终态/独审hash、累计positive2/required3/CLI2/不同case和task以及顺序。只改入口轮次及guard的新manifest路径。
- [ ] 同一新增测试GREEN，然后以code目录运行全部继承与新增离线入口测试。Expected:全部PASS，I/O guard允许/拒绝均0；原153项行为保留，只改轮次和两轮测试材料；通过后不重复测试。

## Task 2: 封存、独审与本地检查点

- [ ] 静态读回与diff核对，校验51父包封存、六前轮来源副本、57源码/7依赖/1346SDK，以及原485/8回归收据绑定；不重复产品回归、模型、UI或音频。
- [ ] 封存全包manifest、报告和单例提案；纯--verify只读文件，不构造native。原始terminal始终保持PENDING，不回写PASS。
- [ ] 根据原技术门及executing-plans执行一次全包只读独立准备审查。逐项裁定范围限制；如有Important/Critical仅一次有界修正，先RED后GREEN，不放宽验收。
- [ ] 报告镜像、明确路径提交并打本地tag，检查commit/tag与封存字节。此前push自动审批blocked by policy，不重试或绕过。
- [ ] 提案只包含同候选第三轮单例和一次只读结果复核；后续负例、E01、8B E02、T3—T5/Owner保持原序与独立门。

Ruling: 沿用原批准的执行方法与技术审查门，在持续目标范围内直接完成离线准备，不重复询问方案执行方式；保留真实单例分配边界。代价是准备PASS不能替代第三轮实跑。
Ruling: 新证据根作为plan workspace并永久保留，替代清理临时SDD目录；代价为审计文件占用磁盘。
