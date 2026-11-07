# E02 代码事实生成表达最小修复实施计划

> **For agentic workers:** Use superpowers:executing-plans. Root implements inline; independent exact plan and final preparation reviewers. Steps below run without another routine permission request under the user's explicit offline grant.

**Goal:** 消除当前代码事实采样表达允许任意文本先于绑定操作名生成的路径，保持原研究能力目标与全部验收，并准备后继受控入口。
**Architecture:** 继续使用官方schema/pattern转换、OpenJarvis和现有writer。在既有JSON字符串兼容投影中将精确operation固定到claim开头；同一共享阶段提示说明该生成形式。严格schema、事实验证、导航、一次写入/读回/ACK保持。只证明该前缀缺口收敛，不声称已解决重复、长尾、语义引用或真实交付。
**Tech Stack:** 既有Python、jsonschema、OpenJarvis、HTTPX MockTransport；本地冻结llama.cpp b10488 Python转换器仅用于离线参考。无安装、下载、native升级或新依赖。
**Spec:** [已批准提案](H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-claim-generation-contract-proposal-20261108.md)，用户call_5411de619a6c4de0bab414126a228c7d选择“授权离线补修、必要独审与入口准备（推荐）”。原单wo-ultimaagent-20261101-0021 / T2。

## Global Constraints

- 当前qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330；不使用14B或替换模型。
- 原题、原四来源corpus、至少三来源写入资格与完整原题验收保持；资格不能代替覆盖，受控资料不能代替真实联网门。
- CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/root275/cleanup310/seal315秒；context16384、messages+strict-schema32768/entity49152字节、输出256/2048与阶段较小上限保持。
- 本轮actual/model/network/UI/audio/production-service操作0；只做离线代码、测试、计划/准备独审与入口封存。新真实研究和其结果复核仍另行明确分配。
- 保留bf7f7a9及c4caa739-c466-44f3-866b-0c57ea8c5e40的FAIL_CONFIRMED及全部更早失败；原七保护身份不操作，15个无关工作树文件不改。
- 新worktree C:/Users/Administrator/.codex/worktrees/jarvis-e02-claim-generation-r1/UltimaAgent，分支codex/jarvis-e02-claim-generation-r1，父bf7f7a9cf0e4ba559c29daa388c00379d12d345a。
- N=H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-claim-generation-contract-20261108-r1；P=同T2下e02-output-structure-controlled-preparation-20261108-r1。旧封存文件不改，所有新证据在N与后继独立入口根。
- T2/Owner不通过；旧E01/E03信用不转到新候选。远端push此前自动审批blocked by policy，本轮不重试；本地提交/tag/镜像和读回照常完成。

## 证据和设计裁定

本次FULL正文3818字符明确在claim字符串中反复生成两句50/49次，随后length/2048拒绝；严格JSON未闭合，未写入。现有采样pattern允许先输出任意长JSON字符，再输出精确operation；此结构允许产生本次观察到的无操作名前缀。它不是重复的唯一内部原因证明。

离线exploration/receipt.json对Logger.info、Date.now、$run及Unicode操作名比较原表达、操作名开头表达和2000有限表达：共12次官方参考转换。前缀表达不接受先叙述后操作名，但仍接受过长尾部。有限表达只证明Python参考能转换，未证明原生二进制接受。

历史jarvis-work-native-schema-compatibility-addendum-20261102.md记录过char{1,2000}/char{1,1000}导致原生重复规则复杂度拒绝。当前固定C++转换器又优先处理pattern，简单恢复maxLength不构成限制证明。本轮不重新引入未经过原生兼容核验的大型有限重复，也不任意缩短事实、来源、输出或验收。保留原解码后maxLength=2000及原严格门；尾部与非代码自由字符串依然可能耗尽预算，必须在后续获分配单例中检验。

引用错配单独保留：S1融资背景卡、S2 TODO卡不能直接支持已捕获的UnifiedAgent泛述；名称约束不能证明语义蕴含。本轮没有确定新的发行/派发机械错误，不修改导航、卡发行或语义验收器。报告、入口提案和后续结果审核必须明确这一风险，不能以合法JSON或正确operation宣称事实通过。

裁定：已批准提案中的“允许输出经原strict复核”指继续经过原严格门，并非采样正则本身可取代strict。合法JSON转义可能在解码后形成非法词边界或控制字符，原拒绝门须保留。该兼容性上界既有，不能包装成全部输出必然可写。

## Review Focus

1. 精确operation中的美元、点、Unicode必须保持；原来可先写说明的格式在严格验收仍合法，新的采样形式只限制生成，不重写旧writer语义。Task1包含格式迁移与边界反例。
2. JSON引号、反斜杠、控制字符、Unicode转义必须仍由完整序列化和strict校验处理；禁止从截断片段写入。Task1包含转义和无写入反例。
3. 2000有限重复只通过参考转换，不能悄悄加回原生schema或宣称原生性能/2048适配。Task1检查公式，Task2记录官方参考能力与限制。
4. 完整题目、来源/证据映射、原8POST预算、共享生成/重放和ACK不能因提示对齐漂移。Task2运行覆盖组与已有实际SDK离线文件路径。
5. 引用错配与未读S4是尚未闭合的实际风险；新候选准备PASS不能作为实际研究PASS。Task2、Task3的报告/入口与当前状态明确保留0/3和未分配。

### Task 1: 固定代码事实的生成起点并保持JSON兼容

**Files:** 修改src/brain/agent_server.py、src/brain/work_navigation.py；新建src/brain/tests/test_work_claim_generation_contract.py；修改src/brain/tests/test_work_sampler_json_strings.py中与新生成形式直接冲突的测试期望，保留原用途；N/verification、N/exploration与本计划ledger。

**Interfaces:** 保持_research_code_claim_sampler_pattern(pattern)、_research_sampler_schema(schema)和v3_research_phase(report_schema, *, output_tokens)签名。精确operation提取与规范性校验不改。复用现有JSON字符J、边界B、点后边界D，把输出从`^(J*B)?op(BJ*|\.(DJ*)?)?$`缩为`^op(BJ*|\.(DJ*)?)?$`。不引入新语法、有限大重复或外部采样器。共享提示要求代码claim以证据卡精确operation开头，后接该语句可支持的原子说明；其余提示与预算保持。

- [ ] 在新候选保留旧源码，使用原审计守卫建立focused baseline；记录同一解释器、argv、源码SHA、退出码与无网络/模型证据。
- [ ] 写test_prefix_cannot_precede_bound_operation：独立字面量“概述。Logger.info 记录初始化。”在旧strict合法、旧sampler合法，新sampler应拒绝；“Logger.info 记录初始化。”应保留。Logger.info/Date.now/$run/a中.bé均覆盖。另加入与本次长前缀形状相同的合成样例，标记其非真实模型输出，不能补写原截断JSON。
- [ ] 写正负边界测试：op裸值和合法标点/序列化引号/反斜杠/中文仍可生成；xop、parent.op、op.child、非法raw JSON拒绝；以转义伪装边界或缺operation经原strict不得写入。新格式不改变旧strict接受“可见 op 调用”的能力。
- [ ] 写请求/共享提示契约测试：观察真实leaf的HTTPX MockTransport请求，代码生成指令与新采样形式一致，原num_predict、模型、source/ref、严格schema保持。先跑RED，失败必须来自旧无界前缀与旧提示行为，保留日志。
- [ ] 实施两个生产文件的最小修改，迁移旧字符串测试：左侧说明现在应被采样拒绝；原序列化边界覆盖移至右侧，旧strict验收仍可接受原合法表达；SDK引用中文/反斜杠正例改为operation开头。不要删掉原负例用途。
- [ ] 运行`run_product_checks.py contract-green`及`json-green`。Expected:新测试及迁移的JSON兼容用途PASS；无产品launch、模型或网络。原strict未修改，旧未知pattern仍fail closed。

### Task 2: 覆盖回归、冻结和独立准备审核

**Files:** Task1的五个候选文件；N/inputs、offline、verification、review、计划和报告；原工单/t2/current-run/全局登记；UltimaDocs文档镜像。

**Interfaces:** 复用原product_pytest.py审计守卫和90秒分组runner；accepted-dependency-pins不改。生成与重放调用同一采样函数和同一阶段提示；当前输入清单映射到新根，既有依赖与corpus摘要不动。

- [ ] 在allow_fetch=false下让固定官方Python转换器转换实际新pattern及完整writer envelope，保存grammar字节/SHA与参考转换耗时。Expected:无原raw JSON通配缺口、无新增大有限重复、entity仍受原上限；明确没有执行原生二进制或模型。
- [ ] 运行原完整相关产品组：contract/json/claim/reference/unique/coverage/transport/navigation/research-a/research-b/grounding/target/write-diagnostics/http-diagnostics/failure/native/metadata/structure/budget/delivery与保存包兼容。沿用原delivery两项不适用排除、90秒分片，不新增跳过。Expected:同最终源码全部PASS，按node-id去重；失败保留并只修本缺口。
- [ ] 保留本次引用错配诊断与原文卡/来源对应作为验收负例资料；不写“命中关键词就等于事实正确”的机械通过测试。后继真实结果必须再次逐事实独审。
- [ ] 对父候选、P准备/结果manifest、原实际seal、依赖及15个无关文件逐字节保全；冻结新候选提交/tag，封存计划/来源/RED/GREEN/完整回归和输入manifest。当前actual/model0、E02 0/3。
- [ ] 一次独立准备审查覆盖整条分支、计划Review Focus、证据限制和精确manifest。重要缺口按同一范围RED/GREEN修复并完成必要精确复核；不自动扩大写域或实跑额度。
- [ ] 项目与镜像本地提交/tag，验证git对象与磁盘字节一致；报告必须保留尾部与非代码自由字符串、引用及覆盖的未证实风险，不能称“8B研究已修好”。

### Task 3: 为冻结候选准备受控入口

**Files:** 新根H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-claim-generation-controlled-preparation-20261108-r1及对应入口计划/报告/镜像/队列登记。

**Interfaces:** 复用P的code/entry.py、bindings、adapter与既有350项入口检查用途；仅更新明确候选/路径/manifest/独审/当前输入摘要，保持原函数AST与deadline/清理/authority语义。当前v5导出处理无需新增协议。

- [ ] 新入口计划先独立审查；绑定本轮冻结候选、原四来源/模型/预算与七保护基线，保留全部旧失败。
- [ ] 离线绑定、入口、边界和导出回归，保留相同去重口径；失败证据不覆写。Expected:输入与隔离写域、v3/v4/v5拒绝/导出规则、单例消费与不重试门正确。
- [ ] 封存入口manifest并完成必要独立准备审核；不创建release/authority/actual，不连接模型或生产服务。
- [ ] 项目与镜像本地提交/tag和最终读回，形成可审查的单例执行提案。清楚写明只减少代码claim的任意前缀，实际截断、引用与完整交付仍待验证；实际额度0，用户另行明确分配后才可发出新请求。

## Self-review and execution rulings

Spec覆盖：授权范围为离线修复、必要独审和入口准备；三任务分别提供产品表达、保全和后继入口，不包含实际例。所有签名维持现有调用；Task3使用Task2冻结manifest，不引用浮动工作区。

裁定：鉴于原生有限重复失败证据，本轮落实已确认的操作名前缀缺口，保留其余自由字符串风险，未选择任意更小事实长度。代价是新候选仍可能在尾部/其他字段耗尽原预算；真实验收不放宽。

裁定：此计划在已批准的具体提案内细化最小差异，沿用root inline执行和必要独审，无需重复请求日常离线步骤许可。保留所有技能ledger副本；先前自动审批拒绝过清理动作，本轮不重试删除、远端推送或换通道。技能通用安装/全仓运行要求由原隔离审计守卫和适用产品组替代，避免音频/服务副作用。
