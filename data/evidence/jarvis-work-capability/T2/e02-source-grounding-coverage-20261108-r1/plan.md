# E02 证据优先生成与来源读取余量实施计划

> **For agentic workers:** Use superpowers:executing-plans. Root implements inline; exact plan and final preparation reviews are independent. The user explicitly authorized offline review, minimal repair, necessary independent reviews and entry preparation; no repeated routine handoff permission is needed.

**Goal:** 修正原生生成时“先写断言后选证据”的可确证接口顺序，并在原六次读取内为尚未阅读的来源保留机会，准备保持全部原验收的下一候选。
**Architecture:** 继续使用官方 JSON Schema/GBNF 和现有 OpenJarvis。只在已有 sampler 投影中使用官方 allOf 有序组件，令证据ID先于claim生成；严格schema、参数名称、writer和渲染不变。共享选页schema在剩余读数不多于未覆盖来源数时仅开放未覆盖来源；最低三来源写入资格及自主选页仍保持。
**Tech Stack:** Python、jsonschema、HTTPX MockTransport、OpenJarvis；已冻结 llama.cpp b10488 Python/C++参考，不下载、安装或执行原生模型。
**Spec:** [已批准提案](H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-source-grounding-and-coverage-proposal-20261108.md)，用户call_3d33440cc40c401ea7a2cf11c8bc2bcf：“授权离线审查、最小补修、必要独审与入口准备（推荐）”。原单wo-ultimaagent-20261101-0021 / T2。

## Global Constraints

- 当前qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330；只用当前8B。
- 原题、原四来源corpus、三来源最低写入门、逐事实/准确引用/完整原题验收全部保持。受控corpus不等于真实互联网搜索通过；旧E01/E03信用不转移。
- CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒；context16384，messages+strict-schema32768/entity49152字节；输出最多2048及原较小阶段上限保持。
- 本轮actual/model/network/UI/audio/production-service操作0。新实际研究及结果复核另行明确分配；本轮必要计划/准备审查已授权，至多一个独立审计并行。
- 冻结父候选d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b及实际1496a844-668d-407a-a91b-89be246ba05b、完整research.md与FAIL_CONFIRMED均不改；保全更早失败、15个无关工作树文件和七个保护身份，不操作生产进程。
- 新候选C=C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-grounding-r1/UltimaAgent，分支codex/jarvis-e02-source-grounding-r1，由原生create_worktree创建；当前父候选工作树保持干净。
- N=H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-grounding-coverage-20261108-r1；P=同T2下e02-claim-generation-controlled-preparation-20261108-r1；B=同T2下e02-claim-generation-contract-20261108-r1。
- 不改J3排序序列化、证据卡/页权限、一次写入事务、END/读回/ACK、时钟/清理或原生拒绝门。没有自动重试、修复残缺JSON、按固定题目代写或关键词判真。
- 远端push此前被自动审批blocked by policy拒绝；本轮不重试或换通道。完成项目/UltimaDocs本地提交、tag和逐文件读回。

## 证据、备选与裁定

P的真实文档3节9条中只有第7条同时通过事实和引用；错误包括引用其他文件、合并超出锚点的陈述、将TODO泛化为当前接入状态。六次读取S1四页/S2一页/S3一页/S4零页；实际写入、END/读回/ACK成立，writer stop728和ACK stop31，内容验收失败。

接口顺序的确证：agent_server.py:429将请求经canonical_v3排序；原schema事实对象按claim/evidence_id排列。固定C++转换器使用ordered_json，在_build_object_rule中按properties输入顺序发出必需字段。仅修改Python字典插入顺序会被J3再次排序，不能改变实际生成顺序。直接改HTTP序列化或重命名字段会扩大原协议差异，本轮不采用。

N/exploration/receipt.json已用本次真实第7请求离线比较：将事实对象投影为allOf有序组件后，J3仍保留数组顺序；官方参考的8条事实规则全部从claim优先变成evidence_id优先，语法大小均14502字节，请求32699→33371字节，低于49152。没有导入产品、调用模型或网络。这证明参考表示与顺序，不能代替已安装原生二进制或模型效果验证。

采用最小有序投影：仅匹配现有封闭、必需字段恰为claim/evidence_id的事实对象，将其变为type=object、required=[evidence_id,claim]、minProperties=maxProperties=2，以及依次含单个properties/required的allOf组件。顶层不放additionalProperties:false，否则固定转换器会先进入普通object分支而忽略allOf。标准JSON Schema中两项required+maxProperties=2仍拒绝缺项、额外项和非对象；官方allOf转换也仅生成两字段。claim/ref各自约束不变，现有maxLength采样兼容投影及解码后严格校验保持。

只投影事实对象；不改section或公开参数结构。证据ID自身已绑定来源分支，选中ID后再生成claim，但这不证明自然语言蕴含。源码提示已包含精确锚点、TODO不是实现、区分项目和完整题目，不能仅重复原提示宣称内容修复。

选页采用机会保留而非扩大验收：原minimum_missing=max(0,3-len(covered))及失败条件不变。令unseen为可信available中未具有可见非空证据卡的来源；当unseen非空且remaining<=len(unseen)时source_id枚举只允许unseen，否则保持available。这样四来源非空场景最多先重复同一来源三次，五来源最多两次；已有空页或不充分历史也尽量把剩余机会给未覆盖来源。页号始终由模型决定，不按原题硬编码、排序或替模型查找证据。

仍允许三来源满足最低资格后写入或拒绝；不要求每次研究都引用所有可用来源，也不把全来源访问误判为完整原题。该修改只堵住“继续消耗重复页、使其他来源连阅读机会也没有”的预算路径。完整题目是否得到回答仍须实际结果独审。

## Review Focus

1. allOf不能丢失必需字段、原ref枚举、code pattern、对额外字段的拒绝或误遍历示例/const中的业务数据。Task1以独立字面量与旧投影等价比较覆盖这些情况。
2. J3排序后顺序必须仍有效；完整writer envelope的官方参考转换、实际请求字节上限及原生兼容限制必须一并记录。Task1和Task2检查真实保存请求，不能只检查Python字典。
3. 3–5来源、空证据页、重复ID、反序available、剩余0/1/2、已经不可能覆盖全部的历史仍保持原三来源最低门、拒绝能力和六读上限。Task1覆盖这些输入，不自动选择页号。
4. SDK阶段与重放必须从同一共享schema重建；连同哈希一致篡改读取枚举或有序投影也不能通过。Task2保留原篡改负例及实际SDK模拟写入/读回/ACK。
5. 证据优先不等于语义可信：本次九条判定与完整原题缺口独立保留，合法schema不得获得事实信用。Task2、Task3报告/入口保留该风险、0/3和actual0，不通过删除事实、题目或降低标准取得通过。

### Task 1: 最小生成投影与读取余量修复

**Files:** 修改src/brain/agent_server.py、src/brain/work_navigation.py；新建src/brain/tests/test_work_evidence_first_generation.py；更新src/brain/tests/test_work_sampler_json_strings.py中的pattern提取/投影断言、test_work_source_coverage_budget.py的早期限制/完整SDK期望、test_work_research.py中旧“只删除maxLength”的结构断言。只改与新表示直接冲突的断言，保留原测试用途。N/verification与exploration为离线工具和证据。

**Interfaces:** _research_sampler_schema(schema)签名保持，事实投影在原子节点约束转换后执行；v3_phase_inspect_schema(base,available,visible,used)签名及原基础权限保持；v3_research_phase(report_schema,*,output_tokens)增加证据ID优先生成和分配未覆盖来源机会的说明。生成与重放已共用这些函数，work_research.py无需改动。

- [ ] 用既有审计守卫、解释器-I -B -X utf8运行针对父源码的json/coverage baseline，保存新日志和源码摘要；没有生产入口或模型请求。
- [ ] 写test_fact_projection_preserves_closed_object_contract：现有文档、评论和代码事实分支均为有序allOf；引用ID和claim缺一、出现extra、错误ID、错误类型均拒绝；旧maxLength兼容含义保持，strict输入不变。旧源码应因没有allOf失败。
- [ ] 写test_canonical_request_keeps_reference_before_claim及对应完整SDK MockTransport请求断言：经过实际canonical_v3后仍有allOf的evidence_id/claim顺序；输出参数仍是原claim/evidence_id对象，不新增解析变换或重写工具参数。
- [ ] 写test_source_reserve_begins_before_fourth_same_source_read：四来源、前三次S1后枚举仅S2/S3/S4；五来源两次S1后仅剩余来源；剩余预算少于未覆盖数时仍保留可达到原三来源的阅读机会；三来源既有行为不变。对缺卡、重复引用、错误source/used的原拒绝测试保持。
- [ ] 先跑上述RED，保留旧行为导致的失败；实施窄投影及choices判定两项改动，shared提示说明真实生成顺序。旧JSON转义与code精确operation测试继续使用相同pattern，只让测试读取allOf内对应属性。
- [ ] 验证GREEN：新focused、json、coverage、旧claim契约通过。早期同来源违规在写入前拒绝，六读自适应模拟覆盖未读来源后write/ACK及独立重放成功；不新增网络/模型/产品启动。

### Task 2: 真实失败资料保全、回归与独立准备审查

**Files:** Task1候选文件；N/inputs、offline、verification、review及本计划ledger；报告/工单/t2/current-run/全局登记和UltimaDocs镜像。

**Interfaces:** 复用B的product_pytest.py审计守卫、90秒分组runner、accepted-dependency-pins和既有相关回归。新证据只写N；P的67成员实际manifest、394准备成员及B的1434成员保持。

- [ ] 将P实际产物、九条独立判定和六页/请求摘要作为有出处的负例资料保全；不让controller改成一份“正确答案”。写清字段顺序或有效ID不证明事实，尚未证明修复模型错引。
- [ ] 追加官方参考检查：在J3 roundtrip后比较原/新完整sampler语法事实字段顺序、literal结构限制、语法大小和真实保存请求字节；allow_fetch=false。代码/评论/文档分支、source/ref绑定、同名业务属性/const/examples均覆盖。无需重跑原生服务。
- [ ] 运行最终适用产品组：新focused、contract/json/claim/reference/unique/coverage/transport/navigation/research-a/research-b/grounding/target/write-diagnostics/http-diagnostics/failure/native/metadata/structure/budget/delivery和保存包兼容；不新增旧delivery两项以外的排除。每组90秒，最多两个离线子进程；统一按最终源码和node-id去重，不把历史失败并入通过数。
- [ ] 保存真实父候选、P实际/准备、B产品准备、依赖和15个无关文件的逐字节保全读回；冻结新候选本地commit/tag，封存完整输入与RED/GREEN/最终回归manifest。
- [ ] 一次整包独立准备审查，涵盖Review Focus和事实信用边界。必要修复限同一确证缺口并保留失败记录；重新绑定精确修复版本，不能自审代替独审。
- [ ] 项目和UltimaDocs本地提交/tag并逐文件读回。交付表述为“生成顺序与阅读机会契约已修复、真实研究质量仍待新单例验证”，E02 0/3。

### Task 3: 冻结候选的受控入口准备

**Files:** 新根H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-grounding-controlled-preparation-20261108-r1及对应入口计划、报告、镜像和队列记录。

**Interfaces:** 复用P原入口/adapter/bindings，保持函数AST、单例消费、清理、时限和v3/v4/v5证据导出；仅更新候选与精确输入/manifest/独审绑定。

- [ ] 入口计划独审后，进行原350项用途的离线入口/绑定/边界检查及必要准备复核。来源/模型/预算原值不变，旧失败保留，candidate信用从0开始。
- [ ] 不创建release、controller-authority或actual，不探测生产服务。运行态标为PENDING_FRESH_ACTUAL_PREFLIGHT，旧保护身份记录仅作历史基线。
- [ ] 封存、项目/镜像本地提交/tag、最终读回；准备具体单例执行提案，但实际与结果复核额度仍0。用户明确分配后，原入口在原时钟内核验新鲜运行态再发出唯一请求。

## Self-review and execution rulings

三任务覆盖已批准离线范围；Task3只消费Task2冻结结果，不引用浮动候选。两生产文件保持原接口，shared replay无需改，三个既有测试仅迁移与新表示/选择范围直接相关的断言。新增证据文件本身不获得验收信用。

裁定：采用官方allOf数组顺序而不改J3、重命名字段或自造解析器；maxProperties=2与两项required证明标准schema的封闭语义。参考转换通过不是当前原生二进制通过；必要实际兼容验证留给明确分配的唯一后继请求。

裁定：读取只改善机会分配，不把“全部available”升级为新的写入强制门，因此维持既有三来源成功/拒绝能力与完整原题独立验收。模型仍可能过早写入或选择不相关页，这些真实风险必须保留，不能称已经解决研究质量。

裁定：用户已批准具体提案内的离线审查、最小修复、必要独审及入口准备，沿用root inline，无需再次询问常规实施方式。保留技能ledger，通用安装/全仓测试由原守卫与适用组替代；不重试此前被自动审批拒绝的删除或远端推送。
