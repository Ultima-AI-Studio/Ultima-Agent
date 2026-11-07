# E02 6d758d9 受控入口准备完成

原工单 wo-ultimaagent-20261101-0021 / T2。冻结产品候选 6d758d9c3961f156a062e349ec4a949e2ee7a9a9 已接入现有受控入口，本轮实际用例0、结果复核分配0、模型调用0。E02仍0/3，T2/Owner未通过；旧候选E01/E03信用不迁移。

复用 N15 的 entry、bindings、adapter，全部函数与类 AST 保持一致，仅重绑候选、路径和摘要。完整源码74项、输入1579项，check_inputs含三项入口绑定共1582项。清单由N15继承73项与N16顶层37项映射并集产生，逐项匹配N16 current-inputs及当前磁盘。产品HEAD/tag与工作区clean已核对。

新增两项安装原导出观察器的SDK MockTransport联合验证：合法中文、引号及反斜杠代码事实完成工具写入、文件摘要读回、ACK和导出包严格重放；raw sampler允许但解码后违反操作名边界的内容被严格校验拒绝，无research.md或完整runtime/END，公开明确未交付。两项均核对实际构造的HTTP实体摘要与可信回执；没有真实模型或事实验收信用。

本轮344项去重离线PASS：adapter五组原始285项、去重283项，以及入口34/绑定16/边界11共61项。原90秒分片及离线审计守卫保持，源码快照/回执/审计/JUnit均核验。首次新增正例把原始反斜杠与Markdown转义后的文本直接比较，出现1项测试断言失败；产品当时已成功写入。首次五组回执完整保留，修正测试为同时验证原始语义和转义后的文档文本，再对最终harness字节重跑五组；通过的三组标准库源码不变，未重复运行或累计。产品N16的781项（775产品+6参考）仅为冻结历史基线，本轮未重跑或重新累计。新入口未实现新的产品行为，也未重复制造旧RED。

精确计划PASS_PLAN_ONLY，整包PASS_PREPARATION_ONLY。manifest ac1fba00bd3af0cb0e16a5736d8ac6c8ec3ffd1949b0383d0bdc7a2275c90b97，234成员；独立准备审查SHA256 8070e7efeb011181c9c9e9a2d92041303ece9e90d7df95baeb6ff3597aaf92a2。harness-approval仅绑定准备审查；read_ready通过，缺少grant时read_release拒绝，run_once未调用。准备根没有release/actual/controller-authority/native-preflight。

只读检查点 2026-11-07T11:48:40.026690+00:00：七保护身份、Ollama0.32.15、当前qwen3-8b-uncensored摘要及18799空闲相符，仅代表该时点。N16封存956成员/输入1576项、N15封存准备189/结果56及旧输入1575项、九个无关文件均保持。上一实际5e6ea89c-8e47-43a6-9480-7a11d72cabf5的HTTP500和未交付仍为FAIL_CONFIRMED，不改写或复用额度。

当前8B、原题四来源、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒以及上下文/字节/输出预算均保持。真实8B交付、原生GBNF二进制行为、三来源事实/原题覆盖和连续存活尚未获本候选实际证明。

下一步按 execution-proposal.md 明确分配一例当前8B原题四来源受控研究及一次只读独立结果复核后，才生成短时且一次消费的grant。失败不重试；无UI/音频/生产服务操作。项目/UltimaDocs本地提交、tag及逐文件读回由 verification/publication-readback.json 记录；此前远端push被自动审批以blocked by policy拒绝，本轮不重试。

证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-json-string-controlled-preparation-20261107-r1
