# UltimaAgent｜集成｜Jarvis 工作能力逐阶段交付

- **task_id**: wo-ultimaagent-20261101-0021
- **stage**: v0.4（复用既有 M1 底座；本单局部阶段 T0—T5）
- original_work_order_id: wo-ultimaagent-20261101-0021
- revision: 2
- authorization: 用户“那按顺序开始推进吧”；批准按已提交的工作能力契约与计划顺序执行，保留最终 Owner 验收和发布门。
- 状态：T2仍BLOCKED。单次夹具诊断已COMPLETE/UNCHANGED且额度耗尽，无验收分。当前7975候选E03 round1入口fix1已封存（manifest a4fdb70c…31ea43d），99项离线测试PASS；首次独审的清理和提交过期两项P1已由同一reviewer闭合PASS。7个保护身份匹配、官方语音ready/fresh；未签发新authority，未启动本轮产品/模型/UI。等待一例当前8B正式round1范围确认；原60秒凭据新鲜度、120秒准入及300/1800/315秒产品时限保持。当前正例0/负例0，其后E03剩余正例/负例、同候选E01、8B E02和T3—T5/Owner门均保留。
- 计划：docs/plans/jarvis-work-capability-delivery-plan-20261101.md
- 契约：docs/specs/jarvis-work-capability-contract-20261101.md
- 草案检查点：ultimaagent-jarvis-work-plan-draft-20261101 @ f6eb808348302cec55bddcf44ee03f5b5736c4d9

## goal

按 R01—R08/E01—E08 顺序实现统一工作任务链路。先完成 T0 基线、固定样本和独立计划评审，再执行 T1 文件交付；后续阶段保留各自出口门。T0 完成不能冒充原单完成。

## acceptance[]

- ACCEPT: T0 固定样本、必要输入哈希、实际源码/运行差异、开源替代排查和精确写域齐备；独立新会话评审绑定同一方案 SHA256。
- ACCEPT: T1 真实 Agent 调用受限文件工具，独立读回核验，E01 连续三轮；旧接口兼容；禁止只凭回复报告完成。
- ACCEPT: T2—T5 按关联契约逐项实现 E02—E08；前序用例持续回归，失败不跳级。
- ACCEPT: 最终独立审计、Owner 真实体验、冻结 tag、产出与回滚说明全部齐备后才关闭原单。

## dependsOn[]

- 无（复用已存在的 v0.3-frozen 门与 voice-next 已确认基线，保持旧 0018/0019/0020 状态）

## fileDomain[]

- `C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent/src/brain`
- `C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent/docs`
- `H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability`
- `H:/UltimaAI/UltimaAgent/tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md`
- `H:/UltimaAI/UltimaAgent/tasks/queue/runs/wo-ultimaagent-20261101-0021`

## priority

- 80

## reasoningEffort

- high

## category + skill

- 集成；executing-plans、test-driven-development、verification-before-completion；T0 规划和独立计划评审分会话。

## receipt

- data/evidence/jarvis-work-capability/T0/input-baseline.json
- 各阶段记录原单/阶段/run_id、输入哈希、执行端、真实退出、证据、越界声明和开源选择。

## retryCount

- 0；审计 REVISE 最多两轮，继承本单失败历史和修订，不新建原单重置额度。

## 写什么与禁止

1. T0 只固定当前材料与执行计划，不编写产品实现；T1 仅按评审通过的精确文件清单实现。
2. 复用现有 SDK 工具、ReAct、SessionStore 和 Ultima 通道；适配代码必须说明现成替代选择。
3. 测试使用隔离目录和会话库。禁止写生产记忆/真实用户文件；禁止改 KWS、换唤醒词、重启现有语音进程。
4. 禁止安装未列入计划的依赖、增加后台感知/主动提醒、跳过前序验收、伪造完成或冻结。

## 开源替代排查

| 子功能 | 现成件 | 采用与理由 |
|---|---|---|
| 任务推理与工具循环 | 已安装 OpenJarvis native_react、ToolRegistry、ToolResult | 采用；不另写 Agent 循环 |
| 文件读写与范围约束 | OpenJarvis FileReadTool/FileWriteTool | 采用；仅在产品接口补授权绑定与成果核验 |
| 会话持久化 | OpenJarvis SessionStore、现有 Ultima memory gate | 采用；补实际调用路径接入 |
| 工作上下文 | 现有 Environment/LocalExecChannel/BrowserChannel，Jarvis.ceo ContextDetector 设计 | 优先接通既有接口；Mac 原生 API 不复制到 Windows |
| 组织方式参考 | Jarvis.ceo bec50ef6 | 采用任务分流、提供商抽象和会话取消思路，逐路径验证实际能力 |
| 最小产品接线 | 本计划 work_service/work_tools/work_verifier | 属产品接线与交付体验适配；不重写上述开源能力。T0 独立评审需核实必要性 |
## 2026-11-02 当前停点补记（原目标与验收不变）

T0/T1技术门通过；T2最后候选10fec03在2/2有界修复后真实E02失败。E01PASS3，E03此候选未启动，T3—T5未进入。149项测试通过不代表实际工作验收。原单与T2阶段索引FAILED/不可派发，全局blocked；所有历史继承、不新增原单重置次数。证据与后续决策材料见docs/reports/jarvis-work-capability-t2-20261102.md。生产服务、已接受KWS和默认主脑未切换；模型对照提案尚未执行，等待Owner明确范围决定。


## 2026-11-02 单次兼容例外接续（不修改验收与历史）

上段为历史停点。SDK 实际首轮工具描述遗漏嵌套参数 schema 已由零推理诊断确认，控制器在原用户目标内作一次手动兼容例外裁定，并真实转移 T2 FAILED→QUEUED→EXECUTING，全局 executing/Manager 已读回。仅授权既有双文件补丁，累计修复3（默认2+例外1）；不声称 Owner 新批准，不换当前 8B，不开启 14B，不切生产。先 RED/GREEN 与全新独立复审，再单次 E02；失败即停本次例外。裁定与证据：data/evidence/jarvis-work-capability/T2/schema-prompt-diagnosis/compatibility-exception-authorization.json。

## 单次兼容例外结束

610005e：151回归及fresh代码复核通过，唯一E02实际机械/语义FAIL，needs_attention/CLI2。首错为非法JSON，原facts:string本次未复现；S2 OpenAI已实现断言仍错。此例外结束，无第二轮/新修复/换模型授权；T2索引FAILED/不可派发、全局blocked/Manager读回，T3—T5未放行。最新报告docs/reports/jarvis-work-schema-compatibility-result-20261102.md，原历史保留。

## 用户明确继续后的架构前置复核

用户现要求继续。原3次失败/blocked检查点和累计数保留，控制器仅恢复同一T2的架构诊断与方案预审，下一次源码修复累计第4，累计上限5由本轮控制器限定，不是重置额度或冒充Owner批准。当前8B、不切14B，不改验收；代码需精确方案与独立审查先通过。依据data/evidence/jarvis-work-capability/T2/architecture-resume-20261102/resume-disposition.json。T3—T5尚未放行。

## 第4次源码修复放行

r3方案7fe32a4b独立PASS，设计检查点c6bcc3c/ultimaagent-work-t2-r4-plan-pass-20261102远端已核验。源码仅按明确四文件/测试/哈希元数据/新内部证据协议范围RED/GREEN，当前8B不换。实现端/root/implement_work_capability_t2_r4，source-repair4-release.json为具体放行回执；不得自动启动真实模型、UI或后续阶段。

## 源码修复5（最后有界轮）

针对review-r4-30b6b14的I1—I3，按fix-round-5/controller-release.json和同一r3设计修正调用声明判别、引用坐标及同一响应快照。不是重置原单或增加模型/权限，不自动开启真实运行。旧源码30b6b14及code-revise tag已推送。fresh执行者/root/implement_work_capability_t2_r5，完成后仅fresh scoped复核。


## 源码5真实门收口

b6ab85b代码独审通过，217唯一测试通过；唯一当前8B原题E02机械和语义FAIL，无合格文件。报告见docs/reports/jarvis-work-t2-r5-result-20261102.md。累计源码5/控制器上限5已到，T2真实状态机收门BLOCKED，其他45条记录不变。只读结构裁定继续，源码/模型推理/后续阶段未放行；原单与失败历史保持。


## 无写入诊断最终收口

当前8B额外诊断预算4/4已用完，原行号与引用编号两种接口在原题及独立材料上均未通过参数与事实/引文/覆盖联合门。原始输出无截断/SDK改写，模型和39输入未变。独立盲评后才解组，控制器不以标题单独推断项目集成。T2继续BLOCKED；累计源码5/上限5、原单及失败历史不改，无源码6/模型下载切换/14B/T3—T5放行。新模型版本选择提案等待用户选择；选官方8B后按该提案受限下载并至多4次隔离比较，不改生产默认。


## 用户选择当前社区8B，接续接口修复

2026-11-02用户明确“继续当前社区修改版8B：先修正研究工具接口”。官方8B对照提案未选、不执行。保留旧源码5/控制器上限5及诊断4次全失败；同原单恢复接口设计与真实SDK MockTransport预审，无源码或模型推理放行。下一源码累计6，控制器本次限含一次独立代码审查修正在内最多新增两候选到7，不重置历史；模型权重/生产默认/KWS/后续阶段不变。见data/evidence/jarvis-work-capability/T2/interface-resume-20261102/resume-disposition.json。


## 逐来源设计r2已复审，真实门仍未通过

2026-11-02：源码9候选7c201a3a代码293项/独审PASS，原生超限资格PASS；唯一受控E02完整回复结构与事实均FAIL，0文件，0/3成功。源9累计2POST（负例1+E02一次），失败全部保留。用户明确继续当前社区8B并先审新的逐来源设计，14B提案未选/0POST。新设计b1290ae6独立SPEC/QUALITY PASS253bf87c，r1三问题已关闭；本轮仅设计审查，拟议S2一次只读前缀及剩余三来源检查尚未放行，源码10、生产集成、T3—T5仍关闭。T2状态BLOCKED，原单未完成，累计源码9/限9与真实重入计数2保持。见docs/plans/jarvis-work-per-source-research-design-20261102.md及docs/reports/jarvis-work-per-source-design-review-20261102.md。

## 2026-11-04 有界恢复 source12/r13（单例已消费）

用户授权的一次恢复轮次已按顺序执行：source12候选 7975e477665c02820fa235b73d203718bd33b2c9；r13准备包由 root-independent 独立审查 PASS；控制器级case scope固定为 e03-round2、整数case_cap=1。只启动一次 CLI，本次无重试。

CLI成功捕获批准的主fixture与完整41 UTF-16选区，但本地 qwen3-8b-uncensored 加载期间 Ollama HTTP 500：llama-server无法分配350060544字节CUDA_Host buffer并退出。没有完成推理/工具调用、没有改写、没有输出文件或 rewrite.md。baseline.json 与 pre-cleanup-windows.json 哈希相同；第二个非目标窗口保持不变。独立结果复核为 CONFIRMED_FAIL / NOT_ACCEPTED：facts=NOT_EVALUATED，mechanical=FAIL，target=PASS，file=FAIL，cleanup=PASS，boundaries=PASS；actual_native_start_count=null，不得当作0。

本轮代码竞态/焦点测试42项与控制器包129项通过；此前T2计划门仍为84 passed、2项既有E02研究失败。本次未能验证选区改写修复，T2继续BLOCKED，T3—T5未放行。当前恢复授权已消费；不启动新用例、不切14B、不改生产语音/KWS或默认模型。

证据根：data/evidence/jarvis-work-capability/T2/e03-source12-20261104-recovery5/。准备审查：review/independent-review.md；结果复核：actual/e03-round2/independent-review.md（SHA-256 47708e3cf2f6dd6beddb10c2f30409e4f02c5ed09dabdeeda58c069b2401c1e4）；终端SHA-256 dea1eae1f68e980fdd36c0ee747731a6430a8581ab725e4673049fa50ff8c107；单例release、execution receipt及保护边界收据在verification/和actual/e03-round2/。
## 2026-11-04 recovery6 R16/R17 补记（原工单和验收门不变）

R16准备包经root-independent审查PASS，因Windows PowerShell默认编码读取UTF-8授权JSON失败，在预检与release前退出；完整包保存在`data/evidence/jarvis-work-capability/T2/e03-source12-20261104-recovery6-fixture-r16-reviewed-prelaunch-failclosed/`。R17修复UTF-8读取后，准备包独立审查PASS并只签发一次E03 round2 recovery-diagnostic authority/release。

该唯一R17启动随后在产品用例目录创建前失败：固定`preparation/controller.py`仍读取旧`review/independent-review.md`，而R17 approval绑定`review/independent-review-r17.md`；两份审查文件SHA分别为`20239698263e07bb686bdaf97301a081e8ff544a620255b63a0f5cd31961eaa0`与`a4baef589766d920c54916600866a4b7a9febe27c72f09e418222964980d1b8d`，控制器的`Current review mismatch`校验因此拒绝。控制器先校验authority，再创建case目录；该检查发生在fixture/server/CLI路径之前。外层Windows PowerShell把Python stderr作为NativeCommandError处理并以1退出，完整traceback未保留。

本次没有case目录、terminal、product-result或rewrite.md。代码控制流表明没有到达CLI启动；terminal中的`work_cli_count`与`actual_native_start_count`仍为null，因为没有terminal/运行计数收据。R17本地8B元数据预检为GET-only且未推理。五个保护进程的身份与预检基线匹配。R17的一次性authority已消费，不重跑；T2仍冻结，T3—T5未放行，生产语音/KWS和默认模型未改。

证据：准备manifest SHA-256 `1fcb1738fefa8bcbe99d85114f84d2770dc5bbb944863df8db5ad7e99099d242`；R17独立审查 JSON `20c04bc61c79ebfa6ec0e3e65eab2ef2a65fa7b6149cbfae174d470428c36917`；执行收据 `verification/controller-execution-r17.json`；根因对照 `verification/controller-execution-r17-adjudication.json`；T2队列冻结读回 `verification/t2-queue-block-r17.json`。继续真实验收需先修正controller审查路径绑定、修复runner对native stderr的捕获，再由用户重新授权一例新隔离诊断。
## 2026-11-04 R22/R23 缓存门恢复状态

R22准备manifest SHA-256 `75632ea7bfaf699678dc8f2e15ec37c0308e2d614db3d21c00a8eba159f3734b` 的root-independent准备审查为FAIL/NEEDS_FIXES（review JSON SHA-256 `0e387c06a85d8658c46ac57ebcaadc957b8acc281740a3570b1e2dfeb9cc099c`）：当前候选工作树根及 `src/brain` 下有两处 `.pytest_cache`，R22封存/核验/运行门未检查该缓存。R22失败证据与之前R9/R20/R21失败全部保留；本次没有approval、ledger、native preflight、authority、release、execution或`actual/e03-round2`。

R23工作包仍是草案，candidate `7975e477665c02820fa235b73d203718bd33b2c9` 与产品源码/夹具不变；finalizer、verifier、runner已加入 `.pytest_cache` 拒绝检查，Python 11个文件及PowerShell 2个脚本语法PASS。缓存删除凭据列出两目录、6个文件及SHA-256，状态 `PENDING_USER_CLEANUP`。尝试清除目录被本机自动策略以 `blocked by policy` 拒绝，故尚未封存/独立复审；没有执行模型预检或产品用例。当前授权仅允许在新包审查PASS后运行一次8B E03 round2 recovery-diagnostic，且不授予验收分。

T2仍BLOCKED。后续仍按原序完成E03三轮与负例、同候选E01回归，再以当前8B处理E02；T2出口未满足前不进入T3—T5。R13、R16/R17及此前所有失败条目作为历史保留，不以本草案、语法检查或文档更新代替产品验收。

## 2026-11-04 R26 当前恢复结果

R26准备 manifest `ff318d8f2f24e6708318a831cc0a32e15bba8583c889d0207767aaeef7f73957` 经root-independent review PASS；活动授权已绑定当前R9 fixture recovery回复，R25 PID-reuse与sealed-receipt两项阻塞已在准备包复核中关闭。只运行一次 E03 round2，execution receipt显示 runner COMPLETED / exit 2，但产品终态 FAIL：初始fixture readback 41 UTF-16正确，冻结基线在同 HWND/PID 上读到“、”单字符，因此 `Frozen fixture mismatch` 在server/CLI启动前触发。`work_cli_count=0`，`product_result_sha256=null`，`facts=PENDING_ROOT_INDEPENDENT_REVIEW`。cleanup因 `QueryFullProcessImageName` 失败和 `Owned discovery ambiguity` 为FAIL；最终7条进程清理记录均 absent，protected boundaries PASS。该新单例额度已消耗，无重试/验收分；T2仍blocked。细节见 `docs/reports/jarvis-work-t2-e03-recovery26-result-20261104.md` 和证据目录 `data/evidence/jarvis-work-capability/T2/e03-source12-20261104-recovery26-runtime-and-pid-bindings/`。

## 2026-11-05 R31结果与当前候选验收归属校正

T2真实工作验收仍BLOCKED。最新R31单例已消费且FAIL：初始41 UTF-16，冻结基线为空，server/CLI前停止（work_cli_count=0）；cleanup与protected boundaries PASS，输入来源无法确认。已完成输入来源观察补丁的离线准备（36项测试），未新增实跑/模型调用，独立审查未进行。已纠正跨候选验收归属：source12目录内round1 PASS来自旧118ba候选；当前7975候选已核实正例0、负例0，后续验收须从round1开始。当前8B、生产语音/KWS及历史失败保持，E01/E02和T3—T5未放行。报告：`docs/reports/jarvis-work-t2-e03-r31-diagnosis-20261105.md`。

## 2026-11-05 输入来源补丁独审闭合

T2仍BLOCKED。R31已FAIL且单例耗尽：41 UTF-16初始文本随后变空，server/CLI前停止，cleanup与boundaries PASS；输入来源无法确认。输入来源诊断补丁首次独审发现ORIGIN-PREFIX-01，最小修订后同一reviewer限定复核PASS（fix1 manifest c6cf3099…735c2），42项离线测试通过；现场根因尚未查明。旧候选PASS不得计入当前7975：独立核对5份失败终态、1次CLI，当前正例0/负例0。下一步准备仅夹具诊断wrapper；没有新运行额度，不启动产品/模型。正式验收从当前E03 round1开始，随后同候选E01再E02；仅当前8B，T3—T5未放行。报告：`docs/reports/jarvis-work-t2-e03-input-origin-review-20261105.md`。

## 2026-11-05 夹具诊断程序及有条件授权

T2仍BLOCKED。单次夹具诊断程序已准备，87项离线测试PASS，manifest c9fa33fa…c7f7b9f4；用户已授权一次独审，通过后运行一次fixture-origin-01。当前仅获有条件授权，独审/新authority/现场运行尚未完成；不调用产品、模型或音频，失败不重试，无验收分。R31失败及其耗尽额度保留；输入来源补丁的独审闭合PASS保留。当前7975候选正例0/负例0，正式E03仍从round1开始，其后同候选E01、E02；仅当前8B，T3—T5未放行。报告：`docs/reports/jarvis-work-t2-fixture-only-preparation-20261105.md`。

## 2026-11-05 单次夹具诊断完成，未复现清空

T2仍BLOCKED。用户授权的一次夹具诊断已完成：R1独审P1来源接口缺陷在fix1修正，同一reviewer闭合PASS（manifest c0af805d…837eb4fb），90项离线测试通过。fixture-origin-01仅运行一次，COMPLETE/UNCHANGED，10.704秒；41/39 UTF-16文本哈希保持，未见EM_REPLACESEL，cleanup/audit/boundaries PASS，七个保护身份和语音ready/fresh保持。额度1/1耗尽，不重试，无产品/模型/音频调用或验收分；R31间歇原因仍未知。下一步准备当前7975候选E03 round1正式验收包，需其自身独审/authority和原门；当前正例0/负例0，其后同候选E01、8B的E02；T3—T5未放行。报告：docs/reports/jarvis-work-t2-fixture-only-result-20261105.md。

## 2026-11-05 当前候选 E03 round1 正式入口准备

T2仍BLOCKED。上轮单次夹具诊断已COMPLETE/UNCHANGED且额度耗尽，未获产品验收分。本轮当前7975候选正式E03 round1入口已封存（manifest 7078209f…8781eb0d），92项离线测试和真实依赖只读导入/来源检查PASS；等待独立包审查，未签发authority、未运行产品/模型/UI。原60秒门为预检凭据新鲜度，120秒准入和CLI/SDK/controller 300/1800/315秒保持。当前正例0/负例0，其后仍须E03三轮与负例、同候选E01、当前8B的E02；T3—T5未放行。

## 2026-11-05 正式round1入口fix1独审闭合

T2仍BLOCKED。单次夹具诊断已COMPLETE/UNCHANGED且额度耗尽，无验收分。当前7975候选E03 round1入口fix1已封存（manifest a4fdb70c…31ea43d），99项离线测试PASS；首次独审的清理和提交过期两项P1已由同一reviewer闭合PASS。7个保护身份匹配、官方语音ready/fresh；未签发新authority，未启动本轮产品/模型/UI。等待一例当前8B正式round1范围确认；原60秒凭据新鲜度、120秒准入及300/1800/315秒产品时限保持。当前正例0/负例0，其后E03剩余正例/负例、同候选E01、8B E02和T3—T5/Owner门均保留。

报告：docs/reports/jarvis-work-t2-e03-round1-entry-20261105.md。准备包独审不构成实际用例authority或事实验收；基包NEEDS_FIXES和全部旧失败仍保留。
