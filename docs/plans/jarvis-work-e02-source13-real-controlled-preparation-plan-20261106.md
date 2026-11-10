# E02 当前 8B 真实受控研究首例准备计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. 当前 root 内联实现；准备完成后由独立 reviewer 审查。Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** 在已接受的 source13 产品上，准备一例真正调用当前 8B 的原题研究入口，使事实、引用、实际文件和独立读回可以按原 E02 合同验收。

**Architecture:** 复用原 SourceNavigation、真实 SDK、产品 `src.brain.cli --work --research` 和隔离 `agent_server --work-research`；只在验证目录适配旧实际研究 harness 的候选绑定、七个保护身份和 root 调用。保留受控四来源的搜索/GET 夹具，不使用模拟模型响应。已通过的零推理包保持原字节。

**Tech Stack:** 现有 Python / OpenJarvis / Ollama / HTTPX；不安装、不更新依赖，不修改冻结产品。

**Spec:** `docs/specs/jarvis-work-capability-contract-20261101.md`，`docs/plans/jarvis-work-e02-source13-reentry-plan-20261106.md` 第5—6步，以及已冻结的 Source Navigation v3 设计与原 deadline ruling。

## Global Constraints

- 原单 `wo-ultimaagent-20261101-0021` / T2；本计划细化已接受的重新准入计划，不新建工单、不重置历史失败或修订次数。
- 产品候选 `269aca511d88412dbb9c15d23911138469a37aa2`；当前模型 `qwen3-8b-uncensored`，digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`。不用14B、更大或其他权重，不修改默认配置。
- 原 corpus SHA256 `9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002`：原题、四来源、完整原始正文和事实要求保持。
- 原预算：CLI1、search1、GET4、inspect6、write1、ACK1、native_POST8、service260秒、client300秒；root work275 / cleanup310 / seal315秒；retry0。不改变模型读取与输出预算，不把局部检查变成运行计时起点。
- E01同候选3/3及E03三正一负记录保留。E02仍须真实受控连续三轮、另一次真实联网且至少三条去重来源；本计划仅准备首例，不承诺后续例自动分配。
- 七个保护进程、已接受KWS/语音和生产服务不操作。未来单例只管理新建隔离测试进程；目前不启动任何服务/监听，不请求11434，不推理，不请求资料网络。
- 新写域 `data/evidence/jarvis-work-capability/T2/e02-source13-real-controlled-preparation-20261106`，下称 N。所有历史包和失败只读；review/release/actual不放进稳定准备manifest。
- 当前仅离线准备，实际用例与结果复核分配均0。具体源码、离线证据、独审、提案、提交/tag/镜像完成后，再申请新的真实单例和独立结果复核。原零推理授权已耗尽。

## Review Focus

1. 旧118ba候选、旧五进程基线或其他模型被误当作当前输入：Task1拒绝旧绑定，Task2明确七身份及parent/命令摘要。
2. 模拟模型响应混入真实研究：Task2核对实际child只安装浏览器夹具与观察器，原生模型客户端/transport不被替换。
3. 字符串JSON事件顺序或SDK版本差异使有效文件无法读回：Task2以本次真实SDK接线产物复放验证，保留字节和值检查；不删断言换绿。
4. 旧父时钟或过期授权被重复用来运行：Task3在原RootInvocation外签发具体一次分配并独占消费，保留275/310/315边界及全部失败。
5. 进程/输出不干净却计为成功：Task3保留原Owned清理、原始terminal、完整导出和两次独立读回；事实审查由实际产物决定，不看模型自评。

## Task 1: 当前输入绑定与复用对账

**Files:** N/inputs/input-manifest.json；N/code/bindings.py；N/tests/test_bindings.py；N/verification/setup_inputs.py；N/verification/run_binding_checks.py。

**Interfaces:** `bindings.validate(value: dict, *, read_bytes: Callable[[Path], bytes]) -> dict` 对闭合字段、当前候选/模型/原corpus/预算/准备范围和逐文件哈希核验；`bindings.load_inputs(path: Path) -> dict` 读固定清单并调用同一核验。返回原dict，不签发运行权。

- [ ] 保留新鲜输入清单：当前产品/SDK/模型依赖、E01/E03登记、零推理结果及独审、原harness与deadline ruling、当前7身份基线。核对所有现存源文件并记录旧实际harness至当前候选的差异。
- [ ] RED：`test_rejects_wrong_candidate`、`test_rejects_model_or_digest_change`、`test_rejects_corpus_change`、`test_rejects_relaxed_budget`、`test_rejects_actual_or_retry`、`test_rejects_missing_or_changed_binding`。成功fixture必须包含模型和corpus的实际哈希映射，不用空清单。
- [ ] 实现只用标准库的绑定模块；不导入产品/SDK，不发起任何服务请求。旧5身份或旧候选只作历史来源，不能给当前输入授权。
- [ ] 运行 `python.exe -I -B -X utf8 N/verification/run_binding_checks.py green`，保留RED和GREEN；读取真实输入清单通过，记录原harness测试函数身份和需适配位置。

## Task 2: 复用实际研究 harness

**Files:** N/harness/adapter.py、test_adapter.py、run_checks.py、headless_proof.py、README.md；N/verification/replay_plumbing.py。

**Interfaces:** 保留旧 `candidate_argv(context)`、`actual_child_entry(...)`、`execute_case(context,p4)`、`RootInvocation`、`verify_exports(...)`；`check_inputs()`通过Task1清单核验。`load_p4()`使用已接受的 `e01-source13-round3-20261106/code/controller.py` 及其固定support，不执行其旧E03入口。

- [ ] 从 `navigation-source10-validation-20261103-inert2/harness` 复制到N，不动旧包。记录逐文件差异和原测试函数身份。
- [ ] 仅适配当前候选路径/摘要、已接受的P4/P1 helper来源，以及七个保护身份。原测试中绑定旧候选/五身份的fixture随契约更新，保留测试身份。
- [ ] RED：遗漏任一listener身份、parent或命令摘要漂移均拒绝；fixture只替换资料搜索/GET，不能替换Ollama/HTTPX模型响应；真实模型事件不得由Mock计数满足。
- [ ] 用固定零推理通过记录中的原始packet与文件做离线 `verify_exports` 复放；此为解析兼容证明，明确不增加真实推理或验收次数。必要JSON键序适配须与当前SDK producer逐项比较，不能忽略字段或字节差异。
- [ ] 运行原harness离线契约及新增负例，留存每次结果；不重复运行已通过的完整产品或零推理用例。

## Task 3: 一次真实入口、封存与独审

**Files:** N/code/entry.py、test_entry.py；N/execution-proposal.md；N/manifest.json；N/review/independent-preparation-review.json；项目结果报告与镜像。

**Interfaces:** `entry.run_once(root: Path) -> dict` 仅接受当前manifest绑定的显式user allocation；先独占消费，再创建原 `RootInvocation`，在同一父时钟下签发原格式authority/ledger并调用 `adapter.run_case(...)`。没有有效分配时零启动、零请求；结果原样保全并另存外层时钟裁定，不修改原terminal。

- [ ] RED：缺独审、包漂移、错误candidate/digest、已消费/过期授权、不同parent identity或clock origin均在首次启动前拒绝；模拟入口调用两次时仅第一例可能进入。
- [ ] 实现最小root连接。固定一次产品CLI；原生模型最多8次POST，不重试；新增测试不得使用真实11434。复用原时限和清理，不增加UI、音频、服务操作或产品写域。
- [ ] 原时限边界、失败产物保全、Owned清理及源码保留回归通过后，封存稳定准备字节，使用一次新的独立准备review。没有准备PASS不能发布实际运行提案。
- [ ] 准备具体首例命令、写域、原题、原四来源和事实检查表；本地提交/tag及UltimaDocs逐字镜像，再申请一例真实8B受控研究及一次结果复核。不得沿用零推理的授权编号。

## 当前已核实的复用事实

实际研究CLI、server研究模式、SourceNavigation、原预算和RootInvocation均已有源码；不是重新实现产品Agent。旧实际harness仍绑定118ba候选和5个保护身份，不能原样启动。当前E01 helper已提供7身份、parent/命令摘要和CIM精度规则，优先复用。零推理通过只解除了SDK接线障碍，尚未证明真实8B的事实和引用质量。

执行方式沿用当前root内联；本计划是已授权目标和重新准入计划的具体准备细化，不要求重复选择执行方式。新模型实际调用仍按既有单例分配门处理。远端push的既有自动审批阻断单独保留，不重试绕行。
