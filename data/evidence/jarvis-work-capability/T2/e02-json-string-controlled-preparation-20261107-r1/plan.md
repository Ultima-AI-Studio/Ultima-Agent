# E02 JSON 字符串候选受控入口与绑定计划

> For agentic workers: use superpowers:executing-plans；主会话实施，独立精确计划及整包准备审查。

**Goal:** 将冻结候选6d758d9接入现有E02受控入口，为当前8B的真实研究准备可执行、可核验的单例提案。
**Architecture:** 复用N15入口/bindings/adapter与原守卫，仅重绑路径、候选、完整源码和必要摘要；产品冻结。新增两项已安装导出观察器的SDK联合检查，确认sampler与strict区别能经原回执链保存；不写新执行器、不改验收器语义。
**Spec:** 原单wo-ultimaagent-20261101-0021/T2持续目标、用户“明确分配单例后”约束，以及docs/reports/jarvis-work-t2-e02-json-string-sampler-preparation-20261107.md的接续项。

## 全局约束与输入

C14=C:/Users/Administrator/.codex/worktrees/jarvis-e02-json-string-projection/UltimaAgent，HEAD 6d758d9c3961f156a062e349ec4a949e2ee7a9a9，tag ultimaagent-e02-json-string-candidate-20261107。N16=e02-native-pattern-json-20261107-r1，manifest a8a65256c90f96c8fcac5b6126633bd9e95d135a1cc079fcc1c1523cba28ff95，独审69c7dd6725bf8a1c2542a899ecf77c3415f1cee57ffca7cdc61f928174be40e6，publication d97f2a33d4751321c839dd11c7bba23ee01e8ed12ba4836f112404990e09eb1b。其781项（775产品+6参考）为冻结历史基线，本轮只读验证，不计为新测试。

旧入口N15=e02-source-coverage-controlled-preparation-20261107-r1。唯一实际5e6ea89c-8e47-43a6-9480-7a11d72cabf5已FAIL_CONFIRMED；结果manifest e0fc7084754d492d7166e219e2596b15f5f2562783721e9ca80a85c2c9168b5a，独审3cc6b1eb5c31440658f306bbdd1e589210d8a7f4f874bc5cc98063cc7a181854。原实际/结果独审均已消费。

新根N17=data/evidence/jarvis-work-capability/T2/e02-json-string-controlled-preparation-20261107-r1。写域仅本根、项目计划/报告、原单/t2/current-run与全局登记、UltimaDocs镜像；C14和所有旧根不改。只使用当前qwen3-8b-uncensored，摘要6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题四来源和至少三来源事实门、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384/messages+strict-schema32768/entity49152、输出256/2048保持。七保护身份、原P4/P1、non2xx正文零读取不变。

本轮actual_case_allocation=0/result_review_allocation=0/model_calls=0；无UI/音频/生产服务操作/安装/14B。E02仍0/3；E01/E03旧候选信用不迁移，最终候选须满足原同候选门，不进入T3—T5或Owner。

## Task 1 — 精确绑定与当前观察器联合检查

- [ ] 原单/全局登记、DoR、原目标原文及preparation-only范围落盘；精确计划独审PASS后实施。本计划使用既有冻结工作区，不创建新产品worktree。
- [ ] 只复制N15 code/entry.py、bindings.py，harness六文件，tests四文件、必要离线runner。绝不复制actual/release/controller-authority/native-preflight/consumed、已分配凭据或执行脚本。
- [ ] source_files=将N15完整73项映射到C14，与N16 candidate-freeze的37项取并集；预期74项，逐项匹配N16 current-inputs和当前磁盘，不能用37项顶层快照代替完整清单。创建当前runtime manifest、输入manifest；删除旧runtime-manifest角色，加入当前runtime及N16 manifest/review/publication摘要。模型/题目/四来源/budgets/protected/previous_plumbing逐项不变。
- [ ] adapter、bindings、entry全部函数/类AST与N15相同；只允许候选、路径、输入摘要、scope/direct-decision摘要常量重绑。保持原120秒、显式actual1/review1/retry0和一次消费门。本目标消息的actual/review均0，不能被当实跑grant。
- [ ] harness/test_adapter.py新增 test_export_diagnostics_current_sampler_contract，参数quoted_write/escaped_boundary。安装adapter.install_trusted_exports后调用实际SDK MockTransport。quoted_write使用对应测试源码中确有的中文/引号/反斜杠代码事实，经sampler raw-body、原decoded strict、工具写入/hash读回/ACK/replay；从导出的trusted-runtime.raw核对strict与sampler不同且各自哈希/实际HTTP实体绑定正确。
- [ ] escaped_boundary送出可被raw sampler接纳但解码后操作名边界非法的文本；要求原strict拒绝，无research.md、无完整runtime/END；公开“未交付”，私有failure诊断及实际请求摘要对应。两类均不授予真实模型/语义验收信用。既有来源覆盖、HTTP500、私有导出负例不删不降。
- [ ] 新test属于已有export-green分片；不改变harness run_checks函数或分片上限。原N15修复后的断言已正确，不重复制造旧RED；本轮是冻结产品的入口重绑定与联合验证，没有新的产品行为实现。
- [ ] 具体execution-proposal列当前候选/唯一命令、原题四来源、原预算、实际一次+独立结果一次、失败不重试。准备阶段不创建真实grant、authority或actual目录。

## Task 2 — 新鲜准备验证与本地冻结

- [ ] 最终绑定/测试字节固定后运行：base-a/base-b/recovery/export-green/failure-export-green及bindings/entry/boundary三组标准库检查；原90秒和离线审计守卫保持，逐分片源码/快照/JUnit/审计回执去重统计。Expected: 全部PASS；781旧产品检查不重新累计。
- [ ] 只读核对N16清单/输入/候选tag及N15实际失败/历史链/九无关文件；读取七保护身份、当前8B版本摘要、隔离端口。Expected: 检查点匹配，不能声称连续存活或native语义通过。
- [ ] 封存manifest，独立整包准备审查；PASS后签发仅代表准备的harness-approval并调用read_ready读回。无release时run_once仍拒绝，不能以准备approval代替用户单例分配。
- [ ] 报告/原单/状态别名/UltimaDocs镜像本地commit/tag及逐文件读回；新增报告用LF，保留所有冻结证据字节。远端此前自动审批blocked by policy，本轮不重试。
- [ ] 完整入口准备好后呈现具体提案，明确分配一例后才运行真实请求及独立结果复核。本计划不预先消耗或自动补发额度。

## Review Focus

完整源码清单74项必须来自继承清单与冻结增量并集，不能只看顶层37项；产品始终6d758d9 clean。入口/bindings/adapter函数体保持，当前原目标决定actual0不得成为grant。quoted_write必须由已安装observer真实导出并严格replay，sampler不得替代strict；escaped_boundary应证明未交付且请求摘要绑定。fresh计数与N16历史781分开，不声称原生GBNF二进制/实际8B/事实/连续存活/T2出口通过。审查和只读metadata不能花掉后续用户实际额度。

## 执行裁定

持续目标已授权必要接续准备及项目规定的独立审查，无需重复询问可逆准备；明确单例分配门来自用户原指令并保留。Windows使用原生ledger/既有审计守卫，保留证据，不安装、不清理旧worktree。Task2消费Task1最终绑定字节，必须在最终测试与封存后按同一manifest独审。
