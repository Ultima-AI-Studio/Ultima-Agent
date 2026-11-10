# E02 原生拒绝诊断候选受控入口计划

> For agentic workers: use superpowers:executing-plans；主会话实施，独立精确计划审查和整包准备审查，不派实施子代理。

**Goal:** 将冻结候选d860b2a接入既有受控入口，验证新版诊断能随可信观察器导出，为原题、原四来源的当前8B单例准备具体提案。
**Architecture:** 复用N17的entry/bindings/adapter，全部函数和类保持，仅重绑候选、路径、完整源码和摘要；产品冻结。沿用原离线守卫，新增两项SDK MockTransport观察器联合检查。
**Spec:** 原单wo-ultimaagent-20261101-0021/T2持续目标、用户明确单例分配门及docs/reports/jarvis-work-t2-e02-native-response-rejection-diagnostics-preparation-20261107.md。

## 范围、输入与门

C15=C:/Users/Administrator/.codex/worktrees/jarvis-e02-native-rejection/UltimaAgent，HEAD d860b2ab4e4d9974e33c96472e4ea15abb807280，tag ultimaagent-e02-native-rejection-candidate-20261107。N18=e02-native-rejection-diagnostics-20261107-r1，manifest 5ecc68ffa1e4828c81d778a02e1ae9664bd692efbbd7073c9bc4ef13481fbf4b，准备独审b66d78f6eab63cbbfc03ff2f9cff884e1298ff842e8d612610d325c1dd2da3c7，publication 5fd086520e950b924f50be5dea9f19f9ac42878deab0914f9ef8433ea1a364e9。N18的909项为已封存历史，本轮不重跑、不重新累计；两项收口补充及其执行回执按原独审绑定保全。

旧入口N17=e02-json-string-controlled-preparation-20261107-r1，准备manifest ac1fba00bd3af0cb0e16a5736d8ac6c8ec3ffd1949b0383d0bdc7a2275c90b97；结果manifest 3a3bda952dbbfaf6c10537e3634549a9321248fcf2eb62bb2875001b538aca3b，结果独审762f6483fa2dff866d1fd6c3ec7d24fb90c3997d37bead205785d6ba91fa2cf7。唯一实际bc216374-f59c-4967-99f2-ded53a4ea49d为FAIL_CONFIRMED；HTTP200、原生校验拒绝、无research.md，具体谓词仍未知。旧单例及结果复核已消费，不复制或重发。

新根N19=data/evidence/jarvis-work-capability/T2/e02-native-rejection-controlled-preparation-20261107-r1。写域仅新根、项目本计划/报告、原单/t2/current-run与全局登记、UltimaDocs镜像；C15与所有旧证据根不改，不新建产品worktree。本轮actual_case_allocation=result_review_allocation=model_calls=0，无UI/音频/生产服务操作、安装、14B或真实用例重试。七保护身份及无关工作改动保全。

仅qwen3-8b-uncensored，摘要6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题四来源、三来源事实门、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384/messages+strict32768/entity49152、输出256/2048保持。既有120秒grant、一次消费、失败不重试门不变。E02仍0/3；旧E01/E03信用不迁移，T2/T3—T5/Owner门保持。

## Task 1 — 绑定与观察器验证

- [ ] 原单/全局登记、DoR五项、原目标原文与preparation-only决定落盘；独立精确计划PASS后实施。
- [ ] 仅复制N17的code两文件、harness六文件、tests四文件与明确列出的离线runner；不复制actual、release、controller-authority、native-preflight、consumed、grant、controller-ledger或实际执行脚本。
- [ ] source_files由N17完整74项映射到C15，与N18完整75项及candidate-freeze顶层38项取并集，预期75，逐项匹配N18 current-inputs及当前磁盘。不得只用顶层38项；更新当前runtime/input manifests，删除旧runtime-manifest角色，保留原题/model/corpus/budgets/protected/previous_plumbing。绑定N18 manifest/review/publication及已审补充，不假设新输入总数与旧入口相同。
- [ ] entry/bindings/adapter所有函数与类AST必须与N17相同，仅候选、路径、输入/scope/direct-decision摘要常量变化。当前目标决定actual0，必须被实际准入门拒绝；不得生成实际授权。
- [ ] harness/test_adapter.py仅将当前产出kind预期v3改为v4，新增test_export_diagnostics_current_native_refusal两个参数case：six_reads和ack_after_write。复用已冻结产品的native_refusal测试助手，在安装当前adapter.install_trusted_exports后，经真实SDK MockTransport调用链取得实际构造的HTTP实体和响应字节。
- [ ] six_reads：六读后第7次POST的2048相位故意返回done_reason=length；要求产品failed、公开未交付、无research.md/write/ACK，导出的v4原因done_reason、六页/三来源、请求/响应SHA/长度/generation/receipt_index与真实测试交换对应。
- [ ] ack_after_write：三读、一次写入后第5次POST的256相位返回同一拒绝；要求needs_attention、write_without_ack、write_confirmed=true、ack=false，文件与已提交效果保留。两者均要求原始诊断与导出字节相等、公开摘要绑定、export SAVED/complete=false/END=false/credit0，缺少完整成功runtime，不将诊断当验收结果。
- [ ] 两项归原export-green选择器；保留全部旧quoted_write/escaped_boundary、HTTP500、来源覆盖和失败导出负例，不改harness分片函数或90秒上限。没有新产品行为，不伪造旧RED；N18已封存RED/GREEN保留。
- [ ] 具体execution-proposal包含新候选、唯一命令、原题四来源/预算/退出清理要求、请求一例真实研究和一次只读独立结果复核，明确失败不重试。此时仍不创建grant/authority/actual。

## Task 2 — 准备验证与交付

- [ ] 固定最终绑定与测试字节，运行base-a/base-b/recovery/export-green/failure-export-green五组及bindings/entry/boundary三组。沿用隔离解释器、90秒、至多2并行和审计守卫；按JUnit身份去重，预期346项而非把N18旧909累计进来，以真实回执为准。每组源码/快照/审计/日志/结果逐项核验。
- [ ] 只读验证N18封存953成员、完整输入1580与75源码、两补充/回执、C15 HEAD/tag/clean；N17准备/结果/旧输入及更早失败链保全。对当前15项其他已改文件建立只读基线并排除暂存；只读观察七保护身份、固定版本/模型元数据、隔离端口，不能称连续存活或模型推理验证。
- [ ] 封存manifest并独立整包准备审查。PASS后生成只代表准备的harness-approval，调用read_ready核对；缺少实际grant时read_release仍拒绝，不调用run_once，不生成真实release/authority。
- [ ] 项目报告、原单/状态别名、UltimaDocs镜像本地commit/tag并逐字节读回；新报告明确LF，通用preparation指针、active_preparation与next_work全部指向当前包；last_actual_result原字节意义保持。前轮收口问题不可重复制造。
- [ ] 准备完成后向用户呈现可审阅的单例提案，只有明确分配后才能创建短时grant并调用真实入口。此前push被自动审批blocked by policy，本轮不重试或换通道。

## Review Focus

1. 完整75源码必须由旧完整清单和冻结新增项推导，所有新输入摘要及N18补充绑定正确，产品始终d860b2a clean。
2. entry/bindings/adapter函数/类保持；持续目标的actual0不能冒充新grant；准备approval/read_ready不能授予真实执行。
3. 新测试必须通过当前已安装观察器真实导出v4，核对实际MockTransport请求与响应字节；2048读取后拒绝与256写后ACK拒绝的效果区分准确，不能把诊断当完整runtime/END。
4. 346预期须由真实新鲜回执去重证明；旧344/909、N17旧失败及N18准备分别保全，不移入实际验收信用，不修改原预算或既有负例断言。
5. 准备状态、通用指针、报告、镜像和tag读回必须一致；真实拒绝谓词、当前8B事实交付、连续存活和T2出口仍未证明。

## 执行裁定

持续目标已授权必要离线接续及项目规定独审，不重复询问可逆准备。采用现有Windows守卫与保留型ledger；Task2消费Task1最终字节，先完成本包再请求单例。沿用已审开源SDK路径，不另建执行器，不替模型选页或代写。
