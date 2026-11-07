# E02来源与证据引用关联：契约对齐实施提案

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task after the user grants its scope. No implementer agents; only explicitly authorized independent review. Steps use checkbox syntax.

**Goal:** 在当前8B和现有SDK/JSON Schema机制内，让研究生成只选择与章节来源相符的、本请求可见的证据ID，保留原writer全部核验，推动真实研究交付。

**Architecture:** 复用现有阶段schema。按每个来源生成一个`anyOf`章节分支：固定`source_id`，该分支facts的`evidence_id`只枚举本来源可见卡片。模型调用、本地strict验证和独立runtime重放使用相同纯函数构造规则；不改写模型响应，不扩大writer权限，不另建研究框架。

**Tech Stack:** 当前Python、OpenJarvis NativeReAct、HTTPX/Ollama、现有Draft7 JSON Schema；不增依赖、不升级、不下载。

**Spec:** 原工单`H:/UltimaAI/UltimaAgent/tasks/queue/wo-ultimaagent-20261101-0021--work-capability.md`与T2阶段；前提案`H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-fixed-target-schema-alignment-proposal-20261107.md`；本提案下述原始证据和范围。此文为未实施的新范围，不是运行许可。

## 已知事实与归因限度

候选`900b944165c0175b91492e3fe5b31d96aabdcd5c`的唯一实跑`4fab6e08-5e5e-44d4-9ca5-3a1e75272938`，48.1012354秒，CLI1/search1/GET4，应用native POST尝试5，最终FAIL，无research.md。

安全诊断`FOREIGN_REFERENCE` / ValueError / 长度17 / SHA256 `d70d189223294e5dd10b6338b6ed27fb7d2da5a7ffc65aec0911f283e6e8056c`匹配唯一静态消息`Foreign reference`。在`work_navigation.py::resolve_v3`中，此条件位于`ref in issued`检查之后，具体是`view.source_id != section.source_id`。在`work_tools.py`中，固定research.md路径检查位于resolve_v3之前，因此本例已跨过原路径拒绝。实际引用ID、章节来源和证据所属来源未导出，具体值保持未知；不推断此前原因相同，也不推断其他事实内容已经合格。

结果manifest：`H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-fixed-target-schema-20261107-r1/review/result-inputs/result-manifest.json`，SHA256 `1970c8dfc91ac852883b518a7b3856ddaf4dc09d009223c594fd9c53363b09b2`。静态归因旁证`verification/reference-contract-readback.json`不属于原始44成员结果封存，应与原始诊断及候选代码分别核对。

当前schema分别接受任意`S[1-5]`和任意匹配`N3.[16位hex]`的证据ID，没有把两者的来源归属关系传给生成约束。提示已经要求使用确切witness；仅增加提示不能表达这个可执行约束。运行时的生成和重放各有一处schema/phase构造，必须一起对齐。

## 方案取舍

推荐按来源建立schema分支，使用现有`anyOf`和`enum`，同时收紧未发行ID与跨来源配对。保留原writer作为最终防线。

另一可行方向是继续只用通用schema并增强提示，但它仍会让生成器接受不可执行的来源/证据组合，所以不作为本提案首选。不采用事后改写source_id、替换证据ID或删除失败事实的路径；那会改变模型首结果与引用归属，超出原契约。以上为本提案的建议，尚未被用户选定或实施。

## Global Constraints

- 只用`qwen3-8b-uncensored`，digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`；不用14B、不改默认、不增推理次数。
- 原题与原四来源corpus SHA256 `9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002`保持。
- 原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8，service260/client300/rootwork275/cleanup310/seal315秒；一次新例需独立准备PASS与新范围分配，失败不重试。
- 无UI、音频或生产服务操作；七个保护身份、完整旧失败、无关工作区修改、原SSRF/清理/时限/请求字节门保持。
- 新候选从900b944隔离建立；不修改当前封存候选或已有证据；旧269aca5的E01/E03信用不转移。
- 文件目标仍为research.md；事实文本仍由8B生成；事实支持、去重、至少三份不同来源、END、ACK、落盘与外部读回原门保持。schema对齐不能保证事实质量或实跑通过。
- 本提案不执行任何新测试、产品或模型调用。远端push此前自动审批blocked by policy，不重试或绕行。

## Task 1: 同一来源引用schema与独立重放对齐

**Files（均在授权后新建的隔离候选内）:**

- Modify: `src/brain/work_navigation.py`：增加纯映射构造函数、扩展schema可选约束参数；保留现有resolve_v3拒绝条件。
- Modify: `src/brain/agent_server.py`：从本请求可见reads构造阶段schema和phase中的同一schema文本。
- Modify: `src/brain/work_research.py`：从验证后的`visible=reads[:index]`重建同样schema和phase文本；不能信任模型自带或wire自报的映射。
- Create: `src/brain/tests/test_work_source_reference_schema.py`；仅在必要处调整现有mock fixture读取完整schema的方式，不改变测试目的。

**Interfaces:**

- 建议`v3_source_reference_map(visible: tuple[tuple[str, bytes], ...]) -> dict[str, tuple[str, ...]]`：输入为经过现有可信读取/扫描和阶段控制的`(source_id, cards_json)`，输出按来源及ID排序的映射；验证来源/卡片格式，跨来源ID碰撞拒绝，空卡片不给选择权；不从model/tool_results接收映射。
- 扩展`v3_writer_schema(source_refs: dict[str, tuple[str, ...]] | None = None) -> dict`：None保留静态工具注册和原结构校验用途；有映射时生成按来源关联的章节分支。实际可写阶段与runtime重放必须显式提供同一可信可见集合，不可回退到无约束schema。
- live可见集合沿用现有规则：已issued的views，加上本轮已confirmed但尚未promoted的pending view；不提前promote，不纳入未confirmed或其他请求资料。重放保持原时序，只用该阶段已可见的reads切片。
- 消费者仍是原SDK/native response_format、Draft7Validator和原writer；produces为固定research.md、章节来源与证据集合关联的schema。静态工具spec的注册协议与原writer事实验证不替换。

- [ ] RED：用合法S1/S2/S3卡片构造“把S1的证据ID放入S2章节”的payload，证明当前通用schema仍接受；另有同来源有效组合、未发行ID、外请求ID、空卡片和重复ID归属冲突用例。断言坏参数在writer派发前拒绝、无文件或effect。
- [ ] 最小实现以上三个产品文件，schema分支只限制来源和证据选择；保持claim、heading、title等原字段与边界。动态schema和phase文本通过同一局部对象构造；不增加新的模型轮次。
- [ ] GREEN：实际SDK mock transport记录的native format、strict_schema、sampler_schema均包含相同来源分支和各自证据enum；合法三来源完成写入、ACK、SHA读回和runtime replay。修改wire中归属、移除分支、偷加外请求ID、篡改phase文本必须被重放拒绝。
- [ ] 验证第三个confirmed pending view可正确进入当前阶段schema且原失败不promotion测试保持；没有第三份可见来源时不提供writer选项。相同来源多页合并使用可见卡片，跨请求映射不能串用。
- [ ] 通过原guard运行上述用例及受影响研究/navigation/transport/diagnostics/delivery回归；对最大6次读取、原最多来源/卡片组合核对32768/49152字节门和原输出budget，超限失败关闭，不静默删schema或扩大上限。原HTTP/junction离线排除仍不计通过。
- [ ] 候选commit/tag、61来源基础上的新增来源与输入哈希重绑；harness/runtime控制函数保持原行为，完成绑定/入口/边界回归、封存、必要独立准备审查与本地提交/tag/镜像读回。

## Task 2: 条件单例和结果复核

**Consumes:** Task1的冻结候选、准备manifest、独审PASS及新的明确单例分配。当前没有这些新许可。

- [ ] 仅新范围授权且准备PASS后，用原唯一入口、原题四来源、当前8B运行一次。保留首结果与原始证据；失败不重试。
- [ ] 一次只读独立结果复核：有文件则逐事实/来源检查，并核验SDK packet、ACK、外部读回、时限与清理；没有则确认失败原因及归因限度。
- [ ] 按实际结果登记、提交/tag/镜像。成功最多新候选受控1/3，不能宣布E02或T2通过；一次实际和复核额度用完后没有隐含的下一例许可。

## Review Focus

1. 同一evidence_id不得通过任何schema分支匹配另一source；最终writer归属检查保留。
2. pending第三页的可见性与confirmed/promotion顺序保持，不能提前借用未确认或未来页。
3. 新请求、重排来源、同来源多页与证据碰撞：只用本次可信可见集合，不从模型输入反向补齐。
4. runtime重放独立重建映射、schema和phase，不只比较自报wire的两个相同错误副本。
5. 原上下文字节/输出/次数/清理/时限与事实语义门保持，schema增大不能被静默截断，也不能因此冒充交付通过。

## 自检与当前状态

设计只处理已定位的来源-证据配对契约，覆盖生成/本地校验/重放三处；具体未知ID不被填造。RED/错误派发、合法链路、pending与跨请求、字节门均有对应检查。未实现、未建新候选、未分配新实际例；须新范围后再执行。

## 2026-11-07 新范围已授权

用户call_33506a697ec545c6b2a396ff83086672已批准本提案的补修、离线回归、必要独审、PASS后一例原题四来源当前8B研究及一次结果复核；失败不重试。以上未实施/未授权文字记录提案提出时的状态，以本次接续为准。

## 执行补充：保护身份只读核对

本轮发现原Ollama PID5708已退出，现有PID11464由同一父进程24608启动，版本0.32.15、当前8B摘要、可执行文件和命令摘要相同，其余六个保护身份一致。用户call_bf5fa9f4197e4118b2aab2d505c6ae66答复没有主动关闭、重启或更新；应用日志记载启动与旧PID清理，启动来源仍未知。只读保存旧基线与新七身份基线，新基线仅用于本候选，必须固定路径及SHA并经准备独审；入口原native/CIM/parent/command/端口保护检查保持。没有服务操作、模型调用或连续存活断言。
