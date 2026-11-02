# T2 E02 当前 8B 研究接口复核

工单 wo-ultimaagent-20261101-0021。T2 执行中，E02 仍失败。**已定位两个不同的停止点**。source9 生成了完整的写入请求，但引用与论断不匹配，重复来源触发写前拒绝。未进入产品的逐来源 r2 前缀则把“弃用本来源”作为一次合法工具结果执行完成。二者均未交付文件。将同一段角色说明再改写一次，不能区分这两个问题。

## 实际输入、生成和副作用

以下 T 指 H 工程的 data/evidence/jarvis-work-capability/T2。analysis.json 列出精确包路径、哈希和字段，SDK 行号均对应实际安装目录。

|路径|任务与给模型的消息|原生响应、SDK 分派与交付|
|---|---|---|
|E01 / E03，同一产品源码|E01 用户给出松林、Markdown、日期三事实和 summary.md。E03 指令要求改写选区并保存相同改写，provider 把选区、窗口与采集信息作为 material 交给 WorkService。普通路径由 SDK 生成含实际工具说明的 system、工作请求 user，执行后的 observation 进入后续 turn。可用文件工具；E03 另有受限替换。每请求最多 10 turn，工作额度 2048。消息结构来自源码，普通路径无逐 POST 原始 wire。|E01 三次各 2 个完成推理、1 次写；E03 三次各 3 个完成推理、2 次工具。外部重开六个文件，E03 对应实际窗口内容；失焦和选区变化的真实 provider 拒写另行通过。6 CLI、15 完成推理、9 完成工具，native starts 未知。证据 E03/E01 actual/*/{argv,product-result,independent-review}.json（正例）及 e01-e03-current-candidate-result.json。|
|source9 产品整篇生成|原主题与四个固定 URL，一次受控搜索、四个成功 GET，冻结正文哈希和读取身份。SDK 原 system 在研究 view 中被替换为研究指令及完整 writer 参数 schema，user 保留原请求、权限根、四源编号材料、身份和卡表。只暴露报告 writer 或 final 拒绝。工具由 SDK 解析 action 分派，原生 tools=[]。|原生单 POST，16384 上下文／2048 输出额度，实际 13888／1615 tokens、200 stop。5 节全 S1、22 条论断、6 张 README 卡；对应位置完整支持论断的 URL 为 0，区分两项目及说明执行条件的覆盖失败。写工具拒绝重复来源，CLI 2，无文件、ack、外部成功读回。受控整篇不是已通过的历史 293 项源码回归。|
|S2 单源前缀|冻结 GET 回放，独立实验 stage 能力，无 writer。|同一模型加载分配 CUDA 缓冲失败，原生 500，零模型答复。S2 不进入事实判断。|
|S3 / S4 单源前缀|实际 SDK history 的 ReAct system 与原查询被实验 view 换成两条 prepared 消息：system 含 stage schema 与局部任务，user 为原问题、来源身份、逐行原文和短整数卡号。S4 把问题显式命名 background_original_query，仅在一条相关局部论断也写不出时才可 unused。实际材料 110/367 行、15/48 卡，均全见。|真实 200 stop，2928/94 与 7320/79 tokens，在 16384/480、温度 0、单 turn 内返回带正确 token 的 stage/unused。两次均经原始和 secured 校验、SDK 成功的内存 stage、调用方 END 及确认，之后才因零 facts 未过前缀门。SDK 单轮耗尽符合设计；无 writer、ack 或文件，事实正确性无样本，局部覆盖失败。|

**定位。** C 的 src/brain/work_service.py:60–99,132–135 和 agent_server.py:217–296,305–331,376–428,436–468 区分收集、研究 view、guard 及 request-owned leaf。普通路径调用同一 ask_full，不走该 view。安装 SDK 的 sdk.py:271、agents/native_react.py:225–286,304–360、agents/_stubs.py:198,265、security/guardrails.py:167–219、tools/_stubs.py:213,381,452 分别负责组装消息、生成、解析、权限/执行和事件。实验前缀改的是研究输入和能力集，见 preparation-r2/run_stage_prefix.py:377–433 及 local-role-preparation-r2/run_local_role_core.py，实际以 outcome.json 的 sdk_history → raw_messages → secured_messages → wire[-1] → raw_envelope/secured_envelope → sdk_result/timeline 为准。r2 设计 SHA b1290ae6…21d17d7 的独审仅批准设计质量，未实现其完整收集至写入流程。

## 可以证明到哪一步

* **PROVED · 形状与语义有两个门。** work_research.py:454–490 的每个数组项分别约束 source_id 与该源 evidence_id，却允许不同行都取 S1。渲染器再检查去重。旧包 review-source9-controlled-r1/review.md 对 6 处实际引用逐项核原文；S1 的下载/构建等行段不支持供应商切换，S2 的 OpenAI TODO 不能当作已实现。仅在 sampler 强制不同键仍允许三源各写错。
* **PROVED · 实际安全投影和预算。** 整篇所引 S1 行未遭篡改，S2 L45 的 loopback 被脱敏且未被引用。S3/S4 raw、secured、wire 消息逐值相等；sampler 仅移除三个字符串 maxLength，完整 schema 在 system 及收包检查仍在。事实分支需要 stage_token、1–4 个 claim/ref/ranges，每条 1–3 个 1–8 行补段。unused 与整项 final 拒绝是不同分支。两次 wire 均无截断、移窗、流式或思考标志开启。S3 原话 “insufficient to fully answer” 针对全题；S4 原话 “No relevant claims can be made from this source.”。收到的是弃用动作，无证据显示 facts 曾在 SDK 或 guard 中丢失。
* **PROVED · 锚点偏差可具体指出。** work_research.py:235–295,351–405 对 TS 使用完整调用语句的词法见证。S3 的 15 个实际 symbol 全是 Logger、console 或 Date.now，没有直接的 this.toolRegistry.execute、this.provider.generateText。命名卡中操作的规则迫使作者讲清执行/回退时绕经日志锚点；卡 9、13 附加上下文仍可表达局部事实。反例是 S4 卡 45 直接指到 self._executor.execute L352，允许的三段足以覆盖 guard 分支、执行和 observation。Jarvis.ceo 的 donor 是 akshayaggarwal99/jarvis-ai-assistant@bec50ef…，S4 是独立 OpenJarvis 底座，无二者集成的直接证据。
* **HYPOTHESIS / UNKNOWN。** 当控制分支、调用和返回值成为可直接引用的证据单元时，作者或能更准确表达机制。没有配对数据可把弃用归因于卡密度、角色、预算或模型能力；S3/S4 同时换了材料和措辞。E01/E03 证实可在小材料上执行有副作用的工具，没有验证跨源归属。未发现足以解释两次弃用的消息丢失、角色倒置、伪造身份或无合法事实分支。

## 两条待评审路线

1. **按语法结构发放机制证据（建议先审表达能力）。** 在产品整篇单 author/write 形态内，针对支持的源语言，从通用语法结构提取同一函数内条件、调用和局部结果的原始行范围，不能证明关联的保留独立片段。向作者提供中性的请求内引用，允许一个论断绑定多处有关证据；保留代码操作见证和模型自写论断；章节用服务端校验的不同源槽，仍允许不采用来源。服务只绑定原行、ID 和字节，不生成主题结论。README/TODO 保留种类，不把条件分支或动态调用推成实装或跨项目集成。与 r3/r4 的单锚邻行及 r2 的同样锚点加手填补段不同，改变的是**能以哪个核心操作和分支为证据**。需要版本化内部卡表、writer、重开规则及历史兼容，公共 E02 不变。风险为 JS/TS 解析覆盖、不可达分支、投影大小；若固定依赖不能安全解析，报告不支持并停止，不能把日志重新标为执行。安装 SDK BaseTool.spec/execute（tools/_stubs.py:137–153）及现有 WorkResearchWriteTool（work_tools.py:299 起）支持有界参数与一次受限写。
2. **请求内只读证据导航。** 保留已收集的不可变目录与原始卡，由同一个 NativeReAct 通过受限 inspect 工具选择源/函数窗口，返回带出处的原文作为 observation，再决定继续查阅或授权一次报告。所见范围与请求、GET 和 hash 绑定，禁止发起其他读取。它改变的是何时、由谁选上下文，既非按源固定生成 N 段也非整篇一次塞入材料，能用交互记录定位“未查／已查但误引”。仍可能选错源，且旧卡的表达瓶颈仍在。需修订当前首次只能 writer/refuse 的私有协议、turn/deadline 和 ledger 的能力切换；原 writer 和验证保持。SDK core/registry.py:33,121、NativeReAct.run:329–356 和 ToolExecutor.execute 可复用。此轮不建议并行投入。

## 最小未来判别（提案，未执行）

先只回答“通用新证据单元能否直接覆盖旧表遗漏的核心操作，同时拒绝假关联”。冻结上述 S3/S4 原始字节和 S2 注释/警告作负对照，预注册独立盲评 rubric（代码真实调用及其控制条件、另一路径、两项目身份），在隔离区离线对比旧表和一个版本化候选表。不向产品或模型提供人工获胜行号、样本特判、期望报告或金标 ID。候选输出须逐项重建原行/来源、覆盖两种语言各一条有条件机制及替代路径，拒绝注释伪调用、跨函数错配、脱敏/遗漏行和跨源拼接；双侧记录全部输出。限一次离线批、30 分钟、0 POST、0 网络费、0 写产品文件；不能表示或不能排除负例即停止。它只检验表示能力，不能预言模型采用或真实文件成功。

离线通过也不自动放行。若独审另行批准单候选，最小实际判别为原受控 E02 整篇首轮，同一固定查询/四源和同一 8B，换已登记的内部表示，1 CLI、最多 2 POST（author 一次、实际写完才 ack 一次），单一原始 260 秒工作时限，外层 315 秒封口；最多 1 次报告写，0 重试。首个缺失/不实论断、引用不支持、来源少于 3、混淆项目或缺失执行条件/替代路径、非真实写入/外部重开哈希不符均判失败；部分写/超时记录 needs_attention 并隔离，不重放。单轮通过只支持该接口组合在该样本可行。原 E02 仍需同候选连续三轮、另行真实联网和独立事实核验；变更候选须重跑 E01/E03 与负例。工单后续门不变。

## 封口

只读照核 source21 的 21 项工作树字节及 C HEAD 244d2120abcd6b8d7744f74a05bd22de46a2d3a5。只新增本报告、analysis.json 和指定 W 报告。模型固定为 qwen3-8b-uncensored，完整 digest 在 JSON。source9 9/9、已关闭逐来源组 3/4、第四次及 S1 无放行；source10 未放行。无新模型或 SDK 实例、外部请求、运行器、测试、产品/队列/默认值改动或 UI/语音操作。本复核没有发布设计、候选或预算。

## 补充复核 · TypeScript 接收者在候选构造时丢失

**PROVED（静态源码推导）。** 对封存 S3 L71–74 的普通调用语句 `const result = await this.toolRegistry.execute(…);`，候选生成器与完整语句验证器对同一调用构造了不同的操作名。

1. 产品 `src/brain/work_research.py:223–234` 对 .ts 使用 TypeScriptLexer，保留非空白 token 的原始类型、拼写与行号。安装版 `pygments/lexers/javascript.py:140,156–175` 的 TS root 在专用规则后显式 inherit；该处的调用表达式不匹配前置的类型注解等规则。`pygments/lexer.py:609–641,711–720` 说明继承位置及按序匹配。JS root 在普通标识符规则前把 this、super 标为 Keyword，点是 Punctuation，成员名是 Name.Other（javascript.py:55–60,80–94,118）。`pygments/token.py:28–32,65–67` 说明 Keyword 不属于 Name。
2. work_research.py:392–400 从后接左括号的成员 execute 向左拼接，跨点只接受 Name。因此候选是 toolRegistry.execute，丢失 this。_js_statement_anchor（351–365）把这个拼写交给 _js_support。对上述完整语句，前一有效 token 是分号，const 赋值及 await 符合 header，末尾分号闭合；完整 header 的 callee 是 this.toolRegistry.execute。237–265,272–301 最终比较不等，无法为这条语句签发其真实操作的 code 卡。S3 L97 的 this.provider.generateText 同理。普通成员调用 super.method 在相同词法前提下也会丢失前缀；此处未提供 super 的历史实例。独立的 if 条件、复合表达式、可选链等还受完整语句规则限制，不能从这一步推断也会获卡。
3. 产品 reference_cards 在 work_research.py:410–438 生成候选后才做上限挑选。实验 preparation-r2/run_stage_prefix.py:137–138 复用相同 _js_tokens/_anchors，实际 S3 outcome.json 的 15 个批准 symbol 只有日志/计时。它记录原始正文与最终卡表，没有逐 token 轨迹或每个候选拒绝原因；以上逐步归因是对该精确语句的源码推导。S4 的 Python 卡 45 已有完整 self._executor.execute，仍得到 unused。该缺陷可解释特定 TS 操作为何不能作为直接锚点，不能据此推断弃用原因、修复后事实得分或 E02 文件交付结果。

**更小的判别。** 在通用结构提取之前，优先考虑一次另批的离线对照：冻结原 lexer 和原 S3、S4，其他选择、验证、48 卡及权限规则全不变，仅在隔离候选中允许 dotted callee 的最左段取词法上确为 Keyword 的 this/super。针对普通 JS/TS 成员、this/super 成员及变量接收者保留完整 token 与全量候选/最终卡表，验证所签见证的完整操作与原行、来源和哈希逐一一致；加入注释、字符串、类型声明、跨行断裂或非成员关键字等拒绝样本。已有 S4 和其他无关见证按原文坐标/种类/操作比较，另查排序插入后 ID 变化及旧协议重开兼容，不能用手工卡号作金标。只承认新规则为 S3 显示至少一个此前缺失的核心调用、负例零误签且无无关语义回归；否则停止，记录拒绝层。独立人工 rubric 只用于验后，禁止输入模型或作为产品特例。一批、30 分钟、0 POST、0 外部费用、无产品写入，不交付模型事实判分或 E02 文件。未实施、未导入或运行 lexer、未分配额度。根控制器的依赖清点仅在限定范围发现 lark 1.3.1，四个 TypeScript 编译器路径均未找到；这条判别不需要引入新 parser。

**UNKNOWN。** 接收者识别修正是否足以扩大最终发给模型的实用证据、是否同时改变其他卡的排序/选择、作者是否采用新卡并写出有依据的条件和替代路径。后两层仍须分别取得证据。source21 与 C HEAD 保留，原 R2 两文件哈希见补充 JSON。
