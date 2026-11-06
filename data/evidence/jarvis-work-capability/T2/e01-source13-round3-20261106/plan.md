# 同候选E01 round3文件交付回归准备计划

> For agentic workers: use superpowers:executing-plans inline, followed by one fresh whole-package preparation reviewer. Permanent evidence. This plan allocates no round3 actual case or result review.

Goal: 当前候选269aca5的E01 round2经本次独立事实复核并正式登记后，准备同候选第3轮真实文件交付。完成三轮要求必须各有新任务、新写入、独立结果复核和累计登记；离线测试、前轮文件和单轮事实PASS不能替代。

Spec: 原jarvis-work-capability-contract-20261101.md的E01及R01/R02/R03/R05/R08；T2出口仍要求E01—E03齐全。E03固定三正例及目标变化负例已有证据，E02仍未通过。本计划不重审前序事实或跳进T3。

Architecture: 复制已审round2入口到独立e01-source13-round3-20261106证据根，仅切换当前case/scope/root并增加已登记round2作为前置。保持冻结产品269aca511d88412dbb9c15d23911138469a37aa2和现有隔离server/CLI/文件核验，不新增产品能力、底座、依赖或模型。

Constraints: 仅qwen3-8b-uncensored，digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330，Ollama0.32.15；原7保护身份、KWS/语音和默认配置保持。60秒proof、120秒authority、CLI300/SDK1800/controller315；一CLI、失败不重试、零UI/音频。版本化三条材料和summary.md不改，输出须在本轮可信根与服务生成的新UUID中。

Task1: round2事实独审和登记未完成前，仅允许本计划和只读分析，不建立第3轮资格或开始实现。完成后字节复制round2原始terminal、独立review、root登记；保留round1与E03四份资格及恢复基线。累计必须恰好两个同候选E01正例，任务UUID不同、时间递增，文件摘要/调用/独审和每条累计绑定一致。按实际收据字段校验，不改写独审报告以适配代码。

Task2: 在新的入口将六份资格绑定到e01-round3/e01-round3-acceptance的manifest和authority。新增校验只针对E01 round2资格与两轮累计链；适度复用既有E01校验以免复制漂移，原round1拒绝语义不得减弱。缺失凭据、复核FAIL、旧候选/模型、credit错误、替换UUID、倒序时间、缺累计行、摘要或前置hash矛盾均须在native backend创建前拒绝。

Task3: 先写并记录新增拒绝行为RED，再最小接线至GREEN。原252项适用测试保留，明确记录当前case/path及完整前置数从5变6的转换。新增旧round2授权拒绝、缺封存依赖和完整重算hash后的不合格结果在backend之前被拒绝的集成测试。运行本包完整隔离离线套件；不重跑历史产品485/8，不调用旧900秒harness或任何模型/音频。

Task4: 核对57源码/7依赖/1346 SDK、前序prep/result封存与所有副本原件；封存manifest。一次fresh独立准备审查覆盖完整包和差异，Important按有界修复处理。最终提交前时钟复查、服务与外部实际读回、副作用核验及清理保持；机械成功终态仍等待独立事实复核。

Task5: 计划/准备报告同步UltimaDocs，完成本地commit/tag和字节读回，再提交一次当前8B E01 round3及一次只读独立结果复核的具体提案。此前远端push自动审批拒绝保留，不重试或换通道。准备PASS不授予实跑、E01整体、E02、T2出口或Owner通过。

Ruling: 用户持续推进授权覆盖本计划及前置通过后的离线准备；最近单例授权只涵盖round2和一次结果复核。round3实际调用模型及结果复核均未分配。本计划不改验收或清除失败，所有历史证据继续保留。
