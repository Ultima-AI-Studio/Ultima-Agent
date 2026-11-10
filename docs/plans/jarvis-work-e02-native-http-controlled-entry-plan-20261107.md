# E02 新候选受控入口与输入绑定实施计划

> For agentic workers: use superpowers:executing-plans；主会话实施，独立计划评审及整包准备审查。

**Goal:** 为已封存产品候选 ee1bef61f04169c64978538dbc4ba799ef7be6c0 准备可审查的单例入口和绑定，未明确分配之前无法运行。
**Architecture:** 源码复用已审查N11受控入口/adapter，重绑到C12及新证据根N13；产品源码冻结。实跑分配是准备完成后的独立输入，不由本轮准备指令推导。
**Tech Stack:** 既有Python、原受控harness与离线审计守卫；不安装依赖。
**Spec:** 用户本轮“为新候选准备受控入口和绑定；明确分配单例后，再取得真实请求回执，据此决定原生兼容修复。”以及docs/reports/jarvis-work-t2-e02-native-http-diagnostics-preparation-20261107.md。

## 范围与原门

原单wo-ultimaagent-20261101-0021 / T2。产品C12=C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent，HEAD ee1bef6，工作区已隔离且干净；本轮不改该候选。新证据根N13=data/evidence/jarvis-work-capability/T2/e02-native-http-controlled-preparation-20261107-r1；仅写新入口、输入、测试、回执、项目计划/报告、原工单和文档镜像。

仅qwen3-8b-uncensored，digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题/四来源、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384、messages+schema32768/entity49152字节、输出2048、retry0保持。七保护身份及既有P4/P1辅助器保持。无14B、产品变更、UI、音频、安装、服务操作或新实际例。本轮actual_case_allocation=0、result_review_allocation=0、model_calls=0。

N12离线候选包manifest26977820632f6dbac4bafa286533c48eb883907129ae6a2bb04e5beb7d2c3298、独审855a3d8eaf6dc60512ae86e099df23d5ed66b9e2dd572ab6aebb61b175a7be1e及706项检查作为已验证的产品基线，不能重报成本轮重新执行。N11实际例be79869f…仍FAIL_CONFIRMED，清理PASS、retry0，旧结果和旧源码不改。历史E01/E03不转移。

## Review Focus

1. 当前“先准备”消息不能被包装成实跑grant：加入直接消息分配范围的负例，未分配时不能消费或触及run_released。
2. 旧候选/旧manifest/旧grant/改变预算/模型/保护身份不能通过新绑定：沿用绑定和边界全套离线负例。
3. HTTP500私有回执必须来自当前候选并与请求实体匹配，200坏JSON须保持状态200且未validated：通过完整SDK MockTransport及原adapter导出入口验证。
4. 新manifest及独审未通过、grant缺失/过期/重复或含额外时钟覆盖时不得发包：原入口全套负例及一次消费门保持。
5. 准备回归与真实接受不能混用：不复制actual/release/controller-authority或旧PASS信用；原失败与无关文件逐字节核对。

## Task 1 — 重绑与准备指令防误用

**Files:** N13/code/{entry.py,bindings.py}、harness原六文件、inputs/*、tests/*、verification/*。产品源码不写。
**Interfaces:** 保持read_ready/read_release/run_once、adapter.RootInvocation/run_case及原clock/cleanup函数接口；新增限定在read_release直接消息分支的范围检查。

- [ ] 记录本轮原文、内容摘要和actual0范围；保存N12/N11 predecessor与原工单状态，登记原0021行与DoR。复制N11 source-only文件，不复制任何authority、release或actual。
- [ ] 生成新candidate-runtime-manifest/input-manifest，逐文件绑定C12及新增HTTP测试；保留同一题目、模型manifest、依赖、原保护baseline和时限。绑定N12产品基线清单与独审；旧adapter函数体必须保持相同，仅路径/候选/绑定摘要常量重置。
- [ ] RED：在临时fixture中把本轮准备消息包装为actual1 grant，旧read_release会只按消息身份接受；新增测试要求拒绝，并证明run_once不消费、不触及released边界。保留原明确单例授权的正例，使用合成测试决策字段，不伪造现场授权。
- [ ] GREEN最小修复：直接消息匹配还需decision.actual_case_allocation、result_review_allocation为严格整数1，retry为严格整数0；缺字段、0、bool或多例不通过。新本轮decision字段均0，故不能授权实跑。未来独立call_答复方式沿用原closed grant、当前manifest/review、120秒新鲜度和一次排他消费，未获真实用户答复不生成grant。
- [ ] 完成可供审批的execution-proposal.md：固定C12、原题四来源、原预算、唯一入口命令、失败不重试、一次独立结果复核。当前不生成release/user-allocation.json、consumed.json、controller-authority或实际输出目录；不复制旧自动签发实跑脚本。

## Task 2 — 离线核验、独审和本地交付

- [ ] 在原守卫下执行绑定/入口/现场边界的标准库负例；完整adapter分片回归及新HTTP导出场景，去重计数。保留RED及每组源码快照、JUnit/audit/receipt。只验证现成接口，不重跑未修改的700项产品回归；核验其封存字节仍相同。
- [ ] 新HTTP导出场景调用当前产品SDK MockTransport及N13 adapter.install_trusted_exports；500不读正文、请求摘要匹配，200坏JSON不标validated，private raw v3与公开摘要/文件摘要相符，原失败/零验收信用保留。
- [ ] 只读核对原七身份、版本0.32.15、当前8B摘要及隔离端口；对N12/N11封存成员、旧输入、C12清洁HEAD和9无关文件核验。只说明核对点状态。
- [ ] 封存准备manifest，独立reviewer只读审查整个绑定/入口包；PASS后签发仅代表准备的harness-approval，再以read_ready只读验证当前包。审批文件不授予actual权限；未创建release时run_once仍拒绝。
- [ ] 项目文档/原工单/UltimaDocs镜像本地提交、tag、逐字节读回。远端此前自动审批blocked by policy，不绕过。本轮E02仍0/3、T2/Owner未通过。
- [ ] 准备全部完成后呈现具体单例范围；只有用户明确分配一次当前8B原题四来源研究及一次结果独审后，才在后续运行环节生成新鲜grant。该环节不是本轮已获授权内容。

## DoR与执行裁定

用户来源、目标/写域、验收/禁止、依赖证据、原单/队列五项齐全后进入执行。独立审查WIP<=1。既有产品候选已隔离，本轮仅新验收根，所以不额外新建或修改产品worktree。为审计保留本计划ledger和旧证据；不执行技能默认的安装、全仓UI/音频测试或删除工作区。真实预算不变，离线用例不计入真实单例或研究信用。
