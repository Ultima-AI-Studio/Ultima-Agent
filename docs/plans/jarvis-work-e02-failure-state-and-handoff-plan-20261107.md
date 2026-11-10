# E02 失败终态、选页诊断与读取交付衔接计划

> 使用 superpowers:executing-plans，由主会话顺序实现，独立 reviewer 审查计划、准备包及实际结果。

**Goal:** 保存失败时可信的最终分支和选页轨迹，再依据证据修复读取到交付的具体缺口。
**Architecture:** 复用现有 WorkLedger、原生 SDK/HTTPX 记录、扫描策略和独立重放。失败诊断是受限旁路回执，不能充当最终 runtime proof、写入产物或成功 ACK。优先新增小模块承载投影，不重构 Agent 循环。
**Tech Stack:** 当前 Python/OpenJarvis/Ollama、pytest、Windows 隔离 worktree。
**Spec:** docs/specs/jarvis-work-capability-contract-20261101.md r2；前置诊断提案 docs/plans/jarvis-work-e02-early-final-diagnostic-proposal-20261107.md。
**Authorization:** 本会话用户明确要求“先补齐失败时的最终分支和选页诊断，再针对证据修复‘读取到交付’的衔接。”据此推进必要实现、离线验证、独立审查和有界验证，不重复询问同一范围。实际验证用途最多两段：诊断取证一次；只有证据支持具体修复、修复准备独审通过后，再验证一次。每段不同冻结候选、独立证据根，各一次且不自动重跑；诊断不明确则不盲修、不使用第二段额度。这不是给旧失败追加重试。

## Global Constraints

- 原工单 wo-ultimaagent-20261101-0021 / T2；主会话执行 WIP1，独立审计 WIP1。所有旧候选、旧失败和旧证据原位保留。
- 新候选 jarvis-e02-failure-state 从 9e2716a6bc8dc1a51218257b89a581f968d8444a 建立。旧路径已被证据哈希绑定，不能就地改写；这是保留绑定证据所需的新隔离，而非丢弃旧工作区。
- 只用 qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330；不使用14B，不下载/更新依赖，不改生产默认。
- 原题和原四完整来源，corpus SHA256 9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002。受控来源验证不代表真实联网验收。
- 每例 CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8，service260/client300/rootwork275/cleanup310/seal315秒，retry0；原32768/49152字节、context16384门保持。
- 原七保护身份基线保持；运行前只读核对，漂移不能绕过。无生产服务控制、UI、音频操作。旧E01/E03信用不转移，T2/Owner门不提前通过。
- 诊断根 data/evidence/jarvis-work-capability/T2/e02-failure-state-20261107-r1；必要修复使用独立后继候选和证据根，不能改动已实跑候选。
- 本地提交/tag/UltimaDocs镜像、读回。远端push此前被自动审批 blocked by policy 拒绝，不重试或换通道。

## Task 1: 失败诊断的可信投影

Files: 新 src/brain/work_research_diagnostics.py；work_service.py 的失败附加回执；必要时 agent_server.py 的受信阶段标记；新 test_work_failure_diagnostics.py。

- [ ] RED：原SDK MockTransport读取后正常提前final、成功write+ACK、异常中断。原失败状态/错误/工具计数保持，失败新增最终分支和六页以内的轨迹，成功不产生失败诊断。
- [ ] 仅从可信账本/已验证secured envelope投影，不接受SDK/model自报的诊断。保留final_before_write、write_without_ack、ack、action、unvalidated/absent的区别。不得把未确认响应解释为已确认final。
- [ ] 最终原文仅在原schema、扫描、类型与1000字符界限全部满足时保留在受限诊断；公开回执仅有限状态/计数和诊断摘要。异常原文、源码、prompt、实体/全部历史、环境变量、headers均不进入回执。超限/扫描异常关闭内容保留，不覆盖原失败。
- [ ] 选页最多6项：受信source_id、请求起点、实际范围、确认/可见状态、view哈希、最多8个证据ID与锚点范围；不复制正文。区分请求与成功页、已确认与未确认，不把无card页计为合格来源。
- [ ] 预算记录只投影已有计数与当时状态，包含原读/写/POST界限和剩余写入准入信息。诊断总JSON≤16384字节，按原锁冻结一次；后续晚到事件不得修改已冻结bytes。
- [ ] GREEN：完整SDK路径、敏感文本、扫描器失效/超长/伪造SDK字段、未确认页/回复、晚到数据、无导航前置失败、诊断自身失败；保持首失败、不重试、不产生成功proof或文件。

## Task 2: 诊断导出、封存与一次取证

- [ ] 在新harness失败分支导出固定名字的受限诊断；校验关闭shape、≤16384、binding、摘要和固定complete=false/credit0，不升级旧trusted-export协议。保存失败不可掩盖产品首结果。
- [ ] 产品受影响回归、harness/绑定/入口/边界检查；保留原两项HTTP/junction排除，去重统计；新文件纳入输入固定哈希。必要独审通过后本地提交/tag/镜像并读回。
- [ ] 只读核对七身份/当前8B和原版本，按最新用户消息精确绑定一次诊断用途的原题四来源实跑。只有准备PASS才签发短期一例authority，预消费、原时限保持。
- [ ] 封存首结果、诊断、清理并做一次独立结果复核。产品FAIL仍记FAIL；诊断完整只说明具备定位依据，不给E02信用。

## Task 3: 依据证据的最小衔接修复

- [ ] 先写可证实原因及不确定项：具体选页、合格来源/卡片、最后分支/原文及预算。无法判定则停止实际序列，报告缺失证据，不追加同候选运行。
- [ ] 仅针对证据支持的问题形成小补修设计并独审。在后继隔离候选先RED复现，再GREEN最小修复；不加入夹具答案，不强迫无依据交付，不增加读取/模型次数，不降事实或引用门。
- [ ] 无依据提前final可保留为明确未交付；若存在可证实编排错误则修其原因。不得将正常拒绝转换为成功。

## Task 4: 修复验证与结果归档

- [ ] 仅在Task3有明确修复且离线/独审通过后，执行第二用途的一次同题四来源当前8B验证并独立复核；不自动重跑，不额外扩展来源/模型/预算。
- [ ] 结果、事实、覆盖、导出/ACK、原时限、清理分别记录；原工单更新、本地提交/tag/镜像读回。通过最多该新候选1/3；失败保持E02/T2未通过。

## Review Focus

- 诊断来源必须可信；SDK或模型注入的research_diagnostic字段不得作为来源。
- 失败诊断与最终成功proof有明确结构和权限隔离，不可被重放验收误接受。
- 诊断器不能调用新网络/模型、延长deadline、持锁等待晚到worker或改变原错误。
- final回答和operation等自由文本受扫描与大小限制；公开回复不暴露受限诊断正文。
- 历史未保存的final/选页仍未知；新例证据不回填旧例原因。语义与整体项目验收保持独立。
