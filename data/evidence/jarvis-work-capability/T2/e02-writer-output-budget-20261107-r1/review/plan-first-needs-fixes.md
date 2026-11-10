# E02 写入阶段输出预算对齐实施计划

> For agentic workers: use superpowers:executing-plans。主会话实施；独立精确计划审查、产品整包准备审查及最终受控入口准备审查，不派实施子代理。

**Goal:** 将当前请求的实际输出上限传入共享阶段提示，保持原题交付要求和原预算，完成新隔离候选的离线验证、独审及受控入口准备。
**Architecture:** 沿用OpenJarvis SDK和Ollama原生format/num_predict；只修改共享提示及生成、重放两处调用。严格schema、选择工具、事实/来源门、原生响应拒绝、写入/ACK和预算不变。
**Tech Stack:** 既有Python隔离解释器、pytest、httpx.MockTransport、JSON Schema及固定离线审计守卫。
**Spec:** docs/plans/jarvis-work-e02-writer-output-budget-alignment-proposal-20261107.md；用户call_4d19727901d9426786cc1f5fd01a3b64授权“离线补修、独审与入口准备”。

## Global Constraints

- 原单wo-ultimaagent-20261101-0021 / T2；原题四来源与完整原题验收保持。只用qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330，不用14B或更大模型。
- 父候选d860b2ab4e4d9974e33c96472e4ea15abb807280冻结保留；旧根N19=e02-native-rejection-controlled-preparation-20261107-r1。实际72d7d71b-39a9-455a-b0b4-8823b3f24c00 FAIL_CONFIRMED，result manifest 9cc9e1c9c38a5f23b9e5a0d72b52bd2558a720c99abea8b11148abde483523d6，独审237b8f3c5c96a0ba9db599c0bdb0cddbe8d8cf68361c323c269fb7a2bf74c41e，项目ae3b4e1/镜像c7193bb。该实际和复核均已消费，不重试。
- 新产品证据根N20=data/evidence/jarvis-work-capability/T2/e02-writer-output-budget-20261107-r1。最终入口新根N21=data/evidence/jarvis-work-capability/T2/e02-output-budget-controlled-preparation-20261107-r1。当前actual_case_allocation=result_review_allocation=model_calls=0。
- 使用原生managed worktree创建新隔离候选；旧worktree、旧实际、manifest及失败证据不改。分支codex/jarvis-e02-output-budget。产品写域仅下列四文件；不安装/下载/升级。
- CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384/messages+strict32768/entity49152、既有输出256/2048以及更小用户allowance保持。
- 无UI、音频或生产服务操作。七保护进程及15项无关已改文件按基线保全；允许固定元数据/身份只读核对，不作推理。离线守卫90秒每组、最多2并行，保留原受限冷导入与已有两项不适用排除。
- 不接受length为成功、不修补模型正文、不缩小原题、三来源/事实/引用门，不限定每源仅一条事实，不代替模型选页或写事实。完整响应正文缺失，不臆测哪段内容耗尽token。
- 新候选只有准备完成后另获明确单例分配才实跑。T2/T3—T5/Owner未通过；旧E01/E03信用不迁移。此前push自动审批blocked by policy，不重试或换通道。

## Task 1 — 产品提示与实际预算一致

**Files:**
- Modify: src/brain/work_navigation.py（v3_research_phase）。
- Modify: src/brain/agent_server.py（_ResearchEngine.generate非ACK阶段调用）。
- Modify: src/brain/work_research.py（verify_runtime_packet非ACK阶段重建调用）。
- Create: src/brain/tests/test_work_output_budget_guidance.py。

**Interfaces:** `v3_research_phase(report_schema, *, output_tokens: int) -> str`，output_tokens必须是type为int且1..2048。它只返回可信提示，不改传入schema。生成传入已经算出的limit；重放传入同一请求options.num_predict，并保留原精确options检查。ACK原指令及256上限不改。

- [ ] 登记原单/全局表、DoR五项、精确用户授权及父失败绑定；独立计划PASS后才创建新候选并实施。
- [ ] 在新测试中先做RED：输出预算1/32/256/2048、bool/非整数/越界拒绝、schema不变；SDK实际MockTransport请求中的256/2048及更小allowance与提示数字一致；有效写入+ACK的重放通过；将提示预算改成其他值或移除新增预算指令并重算实体摘要，独立重放仍拒绝。
- [ ] 沿用固定隔离解释器及离线guard执行budget-red。Expected: 新行为断言失败，0 collection/setup error；记录父源码及失败回执，不伪造真实8B结果。
- [ ] 最小实现上述签名与两处调用。保留原提示逐句内容，在完整参数schema之前追加“Response budget: {output_tokens} tokens for the entire JSON object.”及紧凑JSON、简短标题、精确原子事实、保留原题信息/引用、闭合完整对象的指引。明确不要输出markdown包裹或契约外解释；不设置新的事实数/章节数或内容上限。
- [ ] budget-green通过后运行同最终源码的完整既有受控研究回归：native/json/coverage/http/failure/metadata/write-diagnostics/target/reference/claim/unique/grounding/research两分片/navigation/transport/delivery，保留v3/v4观察器兼容组。Expected: 所有适用测试通过，按JUnit身份去重；测试数从回执推导，不累计父909。
- [ ] 验证length仍拒绝并明确未交付、写后ACK拒绝保留效果、严格schema与原生options未变；现有边界与真实SDK模拟链不放宽。确认changed_files精确为上述四项。
- [ ] 冻结新候选commit/tag，完整源码由N19完整75项映射再加入新测试，预期76；逐项绑定当前输入。父完整75及1590输入、旧结果56/actual seal31、N18及更早失败保持。
- [ ] 封存N20产品准备包并独立审查。Expected: PASS_PREPARATION_ONLY，actual/model0。项目及UltimaDocs报告/计划本地提交/tag、精确字节读回；通用状态指针及LF规则一致。

## Task 2 — 复用受控入口并准备具体单例提案

**Consumes:** Task1冻结candidate、76项完整源码、产品准备manifest及独审、完整依赖绑定。
**Produces:** N21独立封存的entry/bindings/adapter、准备审查和具体execution-proposal；不产生真实grant/authority/actual。

- [ ] 仅复制N19的入口/绑定两文件、harness六文件、四项标准库测试与明确离线runner，重绑新候选/路径/摘要。核心entry/bindings/adapter全部函数与类AST保持；旧授权、release、actual、controller-ledger及实际执行脚本不复制。
- [ ] 用N19完整75项与Task1完整76项的并集生成source_files；不得退化为顶层源码子集。原题、corpus、model、budget、protected与previous_plumbing不变；新输入总数动态核验。
- [ ] 保留原当前v4的six_reads/ack_after_write观察器检查与其他完整负例。运行固定最终绑定的五组harness及bindings/entry/boundary三组，预期346去重项，以fresh回执为准；不将产品回归再计为入口测试。
- [ ] 封存N21并做整包独立准备审查，核对产品PASS、原生预算提示、当前输入、无actual授权。PASS后harness-approval/read_ready通过，缺失grant的read_release必须拒绝；不调用run_once。
- [ ] 项目/镜像报告、提案及原单/全局状态本地commit/tag并读回；将全部通用preparation指针、测试数、下一步、local tag指向当前包，保留历史actual。若收口模板残留旧值，在本包封存前修正并做定点检查，保留旧失败审查。
- [ ] 最终交付具体原题四来源单例提案，保持原预算/失败不重试及一次独立结果复核门。此时actual0/model0，不把离线完成称为8B研究交付。

## Review Focus

1. 更小allowance、256读取/ACK、2048写入阶段的实际num_predict与提示完全一致；不能仅把“2048”硬编码到所有阶段。
2. 生成与独立重放共享提示；被篡改或缺少预算指令的旧提示即使实体摘要重算仍应被拒绝。原options/时钟/身份检查不变。
3. 紧凑指引不得改变schema接受域、来源/事实数量范围、原题覆盖要求或让宿主生成内容；已有多事实与引用链保留，缺证据仍拒绝。
4. length、v3/v4失败回执、写入/ACK及未交付边界不变；真实8B输出改善仍未知，已消费实际不可重试。
5. 新产品76全量源码、当前入口完整绑定与fresh去重回执、状态/报告/镜像/标签一致；准备PASS与实际分配严格分离，旧失败/无关改动/七保护身份保全。

## 执行裁定

用户已经批准具体提案、离线执行方式和必要独审，不重复技能handoff确认。沿用现有Windows保留型证据ledger和固定依赖，不安装或清理旧worktree；创建新worktree由冻结父候选要求决定。已有guard回归覆盖本改动，裸全仓测试中可能触发模型/网络/UI的用例不运行；按原明确排除和隔离分片保留其限制。Task2消费Task1最终hash，产品冻结后不为了入口测试改变产品。
