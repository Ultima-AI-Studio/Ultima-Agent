# E02 读取后写入的来源章节唯一性补修

本文件是 jarvis-work-e02-failure-state-and-handoff-plan-20261107.md 的 Task3/4 实施补充，沿用当前会话用户“先补齐失败时的最终分支和选页诊断，再针对证据修复‘读取到交付’的衔接。”的授权。只处理诊断证据支持的接口缺口；主会话顺序实现，必要独立计划/准备/结果审查。本文件不分配额外诊断重试；后继候选最多一例补修后验证。

## 证据及限度

诊断候选22653fb，运行963f8bf5-1a85-49ce-ae9f-19d503b9ff65，外层58.3623722秒，第一结果FAIL，product error为Unlinked or failed END。诊断原文5188字节，SHA256 bf8efb945255dcff31ace9dceee48d69d8450b28f0636c79a86812812a1a65dc；结果manifest SHA256 083bdd6aea562acf27276b3896a6931284588ee51664580c2b61129301ffc02d。

- 可信分支为action；没有final_answer；六页均confirmed/visible。S1读取26、53、92、121起点，S2读取20，S3读取25；三个来源都有卡片，S4未读取。读取分配偏重README是观察事实，不能把它直接认定为这次写入错误的原因。
- 发生一次失败research_write；research_failure=INVALID_SOURCE_SECTION，原错误长度35、SHA256 7e9599d0c2918550861b8aa0402844d74269fa7bbddddb57b5c4497294bf463e，与源码固定字串Duplicate or unknown source section完全一致。
- 七次应用POST已完成，失败快照剩余229.489735秒。无research.md、写入确认或ACK。public tool_results没有inspect记录，不能据此断言没读取；可信六页回执说明已读取。
- 当前phase schema按每个章节独立anyOf绑定S1/S2/S3及其卡片，却未约束跨章节的source_id唯一；resolve_v3保留唯一性检查。已确认三来源存在且action通过该phase校验，因此“重复章节”有强控制流依据；原写入参数未留存，不能声称看到具体重复来源或内容，也不回填N9的失败原因。
- 诊断结果须先独立复核；若独审否定依据，不实施推测修复或消耗后继验证例。没有文稿时事实和原题覆盖均不可评估。

## 最小设计与选择

选择是主会话在既定目标内的实现决定。保持原sections数组、字段、3至5来源范围及每章1至6事实，生成阶段增加来源唯一性，避免模型给出通过前置schema却必被writer拒绝的参数。

候选方式：仅增加提示不能落实严格契约；uniqueItems只排除完全相同对象，不能排除同source_id不同标题/事实；生成后合并/删章节会改写模型提交内容，不能采用。采用原JSON Schema/官方grammar已有的tuple items及本地definitions/$ref，列举可见来源的3至5项子集，每个子集按source_id排序，每个位置只允许一个来源。最多五来源、16个有界子集。共享每来源章节定义，避免重复展开卡片使schema体积成倍增加；不引入远端引用、依赖或新服务。

v3_phase_writer_schema保留全部证据/operation约束，为每来源建立一次定义，sections的各合法子集使用定长tuple引用它。v3_research_phase仅补充“一来源一章、同来源多页的事实合并到该章、按照来源ID顺序输出”的通用契约说明，不注入题目答案、页面选择或文稿。

因为writer schema嵌在原action envelope内，本地JSONPointer必须绑定整个schema根。新增小型纯函数统一包裹alternatives并把writer的definitions提升到envelope根；生成与独立重放共同调用。保留standalone writer schema供phase说明与测试验证。只允许本地固定定义，helper不执行引用或网络操作。ACK envelope和尚未满足三来源的阶段保持原结构。

resolve_v3/render_v3、_fact_evidence、文件事务、扫描器、诊断模块、失败/ACK协议全部保持。无后处理替换、强制无依据成文或增加读/模型次数。合法3/4/5来源子集均可选择；不足依据仍允许明确拒绝。选页与语义质量不在本补修中伪造通过。

## 执行及验证

1. 独审本设计及诊断结论后，从22653fb新建后继隔离候选jarvis-e02-unique-sections；旧候选已实跑，不能修改其字节。新证据根e02-unique-sections-20261107-r1。先RED：可信可见来源下，两个同source_id但不同heading/fact的章节在旧phase被允许，而writer拒绝；覆盖完整SDK MockTransport路径。
2. GREEN最小修改预计work_navigation.py的phase schema/通用phase/小型envelope helper，以及agent_server.py与work_research.py两处封装调用。必要测试结构适配应仍检查原来源—卡片、operation和重放防伪契约，不能删除原断言来通过。
3. 验证各3/4/5来源子集可写，重复、未知来源、外来源证据、越序、增减tuple项均在dispatch前拒绝；无卡片页不授予来源；成功write+ACK+独立重放仍成立；篡改定义/引用/tuple/阶段仍被拒。先写失败用例再实现。
4. 用现有封存官方grammar参考实现转换含本地$ref与tuple的完整envelope，先resolve_refs且allow_fetch=false，保留原不支持lookaround负例、最大卡片/长operation字节门。测试普通3/4/5来源和当前诊断页形状的完整请求大小；原32768/49152门不变，不截断schema或放宽cap来通过。参考转换不冒充本机二进制证明。
5. 运行受影响产品完整回归及harness/绑定/入口/边界检查，去重计数、原两项HTTP/junction排除保持。绑定新源文件与当前依赖，独立准备PASS后本地提交/tag/UltimaDocs镜像读回。
6. 只读核对原七保护身份、Ollama0.32.15和当前8B摘要。仅准备PASS且输入未漂移后，按原题四来源分配一次后继验证，预消费、失败不重试。第一结果封存并独立事实/覆盖/协议复核，然后更新原工单。通过最多新候选受控1/3；失败保留原因和未交付状态。

原预算：CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒；context16384；retry0。只用qwen3-8b-uncensored，digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330；原题/四来源不变。无UI、音频、生产服务操作、下载更新或14B。旧E01/E03信用不转移。旧文件/失败证据/无关工作区保持。远端push此前自动审批blocked by policy，本轮不重试，只做本地提交/tag/镜像。
