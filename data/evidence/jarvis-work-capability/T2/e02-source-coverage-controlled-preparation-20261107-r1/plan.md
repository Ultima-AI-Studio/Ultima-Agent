# E02 来源覆盖候选受控入口与绑定计划

> For agentic workers: use superpowers:executing-plans；主会话实施，独立计划与整包准备审查。

**Goal:** 将已封存的 e40a55b 来源覆盖候选接入现有 E02 受控入口，准备原题四来源的真实 8B 验证；未明确分配单例前保持 actual=0。
**Architecture:** 复用 N13 已审查的 entry/bindings/adapter 及标准离线守卫，只重绑候选、源码清单、证据根和必要摘要。产品代码冻结。补齐当前未交付契约的导出兼容测试，不引入新执行器或另一个验收标准。
**Spec:** 原单 wo-ultimaagent-20261101-0021 的持续目标、用户“明确分配单例后”约束，以及 jarvis-work-t2-e02-source-coverage-budget-repair-20261107.md 的接续项。

## 范围与边界

同原单/T2，不新建原工单。产品 C13=C:/Users/Administrator/.codex/worktrees/jarvis-e02-source-coverage/UltimaAgent，HEAD e40a55b40c223181040dbb6a09d0c4d2da5026cf。N14=e02-source-coverage-budget-20261107-r1，manifest 2e6fd25cfb671552c7be87ce51b4d0fcc4b0216c65a1c042e5005b2aca7e0dd8，独审 e59a105ff83691a4e13ed522b9aff268045733ee35f8ed5a24aab93215ec8fc9；746 项为已封存历史产品基线，本轮不重新计数为新执行。

旧受控入口 N13=e02-native-http-controlled-preparation-20261107-r1；唯一实际 91406fa9-5952-4e3a-99af-a94c8857c8d3 为 FAIL_CONFIRMED、无 research.md、无重试，其实际及结果复核额度已消费。新证据根 N15=data/evidence/jarvis-work-capability/T2/e02-source-coverage-controlled-preparation-20261107-r1，仅写本根的代码/输入/测试/证据、项目计划/报告/原单状态和文档镜像，不改任何旧证据或产品 worktree。

仅当前 qwen3-8b-uncensored，摘要 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题四来源、三来源事实/覆盖门、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384/messages+schema32768/entity49152、256/2048输出帽保持。七保护身份、原P4/P1辅助器不改；无UI/音频/服务操作/安装/14B。本轮actual_case_allocation=0/result_review_allocation=0/model_calls=0。

E01/E03 在旧候选的通过证据保持，不转移为 e40a55b 的同候选信用；最终 T2 出口仍须对最终候选完成原 E01—E03 门，E02 未过不进入 T3—T5 或 Owner 冻结。本次入口准备不是该出口。

## Task 1 — 来源绑定与当前导出契约

- [ ] 保存持续目标原文、来源哈希与 preparation-only 范围；原单/全局队列登记和 DoR；精确计划独审 PASS 后实施。
- [ ] 只复制 N13 源文件：code/entry.py、bindings.py，harness 原六文件，原四测试文件与必要离线 runner。绝不复制 actual/release/controller-authority/native-preflight/consumed/分配或执行脚本。
- [ ] 将输入清单中的旧产品路径改绑 C13，完整加入 N14 冻结 source_sha256；绑定 N14 manifest/独审/publication；移除旧 runtime-manifest 角色并创建当前清单。保持原模型、题目、来源、时限、protected baseline、previous_plumbing 等其他字段逐项相等。
- [ ] adapter、bindings、entry 的函数/类 AST 与 N13 保持相同，仅路径、候选、输入摘要等常量允许重绑。保留严格直接消息 actual1/review1/retry0、120秒新鲜度、一次排他消费及旧授权拒绝门。当前目标消息的两个 allocation 明确为0。
- [ ] RED：在当前 C13 上执行复制的 failure-export 分片，保留旧断言“FINAL不出现在公开结果”与新合法固定文案冲突的失败回执。GREEN：仅改成公开 content 等于固定未交付文案，同时不存在私有 final_answer 对象；16KiB、绑定、摘要、未写入/零信用断言保留。
- [ ] 增加当前 adapter.install_trusted_exports 完整 SDK MockTransport 联合检查：第五次同源请求被拒且只耗四读；合法六读后主动未交付；虚假已保存文本未校验、不进入私有final。逐例核对服务首回执/公开文案/私有原始包/导出摘要/原始HTTP请求绑定，不凭模拟成功字符串授予交付信用。
- [ ] 执行提案列出当前候选、唯一入口命令、原题四来源、原预算、一次研究+一次只读独立结果复核、失败不重试；不生成任何真实 grant/authority 或 actual 目录。

## Task 2 — 离线验证、审查和发布

- [ ] 绑定、入口和现场边界标准库负例在原拒绝网络/进程守卫下执行；adapter 全分片及新增导出接口在原审计守卫下执行。保留每次源码快照/JUnit/审计/回执，去重统计；产品746项仅验证封存字节，不重跑未修改产品。
- [ ] 校验 N14/N13/N12/N11 封存/实际失败及九个无关文件，C13 clean HEAD/tag；只读核对七身份、当前8B元数据和隔离端口。只声明核对点状态。
- [ ] 封存当前准备 manifest，独立整包审查。PASS 后生成只代表准备的 harness-approval 并运行只读 read_ready 校验；无分配时 run_once 仍拒绝。准备 approval 不授予真实研究权限。
- [ ] 项目报告/原单/UltimaDocs 镜像本地 commit/tag/readback；不重试此前被自动审批 blocked by policy 拒绝的远端 push。原实际失败与E02 0/3保留，不能把离线通过算产品通过。
- [ ] 准备完成后呈现具体执行提案，取得单例及独立结果复核的明确分配后，才进入真实请求环节。此次不主动生成 allocation，不推断持续目标等于已分配该单例。

## Review Focus

核对函数体不变、唯一变化为当前绑定与测试契约；来源覆盖行为来自冻结产品，不由验收器替模型补写。验证完整源码清单包括新来源覆盖测试，旧candidate/manifest/预算/模型/protected/授权均拒绝；持续目标不能成为实跑grant。公开固定未交付文案合法，私有final对象仍不可泄漏。新联合测试必须通过实际安装的导出观察器取得请求绑定、页面计数和零交付信用；不能替换成手工拼包。旧失败、当前产品746项与本轮新检查分别报告；无真实语义、原生grammar/HTTP500解决、连续存活或T2出口信用。

## 执行裁定

持续目标已授权必要接续准备、离线验证与独审，不再询问这些可逆准备动作。明确单例分配门来自用户此前指令并保留。产品已有隔离封存，不新建/安装/清理产品worktree；使用既有Windows原生ledger及守卫替代通用Bash工作区脚本，保留全部证据。Task2依赖Task1最终绑定和测试字节，必须待这些字节固定后再收集最终分片回执。
