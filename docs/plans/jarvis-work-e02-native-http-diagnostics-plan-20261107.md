# E02 原生响应兼容性与受限 HTTP 诊断实施计划

> For agentic workers: use superpowers:executing-plans，主会话顺序实施；必要独立计划和代码审查，不派实施子代理。

**Goal:** 核对当前 8B 原生响应接缝，并补齐现有可信 HTTP receipt 到失败诊断的缺口。
**Architecture:** 复用现有 transport receipts 与 ledger timeline，新增封闭、只读、零验收信用的诊断投影。只修复已由源码或保存证据证明的问题。
**Tech Stack:** 现有 Python、HTTPX、JSON Schema、OpenJarvis/Ollama；不新增依赖。
**Spec:** docs/plans/jarvis-work-e02-native-response-compatibility-followup-20261107.md，以及 inputs/direct-user-decision.json 中本轮用户指令。

## 范围与冻结

原单 wo-ultimaagent-20261101-0021 / T2。前例 be79869f-10e5-4c0d-96a9-144cd5967c12 已 FAIL_CONFIRMED：119.564 秒、六页 confirmed/五页 visible、无文稿；retry0、清理通过、七身份在核对点一致。其全部源码/证据冻结。新候选 C:/Users/Administrator/.codex/worktrees/jarvis-e02-http-diagnostics/UltimaAgent，基于 2b42b3e19516154a26cbc895a3d9e69fabb07ab2；本计划旁证据根 e02-native-http-diagnostics-20261107-r1。

只用 qwen3-8b-uncensored，manifest SHA256 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330；永不使用14B。保留 CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384、messages+schema32768/entity49152字节、输出2048、retry0。当前授权实际例0、模型调用0；无UI、音频、生产服务操作、安装或模型下载。只读官方固定版本源码获取和版本/身份核对属于兼容性调查。后续实际例必须另有明确分配，不把本计划当作 authority。

## 已知依据与限制

源码已设置 think=false / stream=false / temperature=0。当前 GGUF 内置模板包含 enable_thinking=false 分支，manifest 无另一个模板层；只读解析元数据，未读取 tensor、未全量重哈希5GB权重。Ollama v0.32.15 源码把 think 传为 chat_template_kwargs.enable_thinking，把对象 format 传为 JSON schema；其原生 GGUF chat 路径还经过 llama-server 响应解析，与离线参考 grammar 转换不同。固定上游版本并不证明安装二进制字节相同。

前例冻结日志关联第七次HTTP500与 peg-native 解析告警，但缺少请求绑定 transport 导出，不能确定模板/schema/parser的具体原因。transport.exchange 已记录真实 status/request SHA/counters；capture_failure 未投影这些字段，这是可直接修复的缺口。没有确证的接口不兼容，不改请求格式、模板、token上限或约束，不从局部输出拼接报告。

## Review Focus

1. HTTP200但坏JSON/schema/扫描失败不能误报响应已验证；新增真实SDK MockTransport测试。
2. 最后一代在发包前拒绝或此前receipt残留，不能假称有HTTP响应；timeline绑定与null场景测试。
3. HTTP500响应正文含私密字串或超大内容，仍不读正文、不改变原错误；流fixture验证。
4. metadata失败与chat失败必须区分，generation来自本次可信send/admission事件；版本/tags/聊天测试。
5. 诊断冻结后transport变化、伪造字段、计数越界不产生验收信用；closed decoder、冻结、扫描失败测试。

## Task 1 — 兼容性证据及有界诊断

**Files:** 只修改新候选 src/brain/work_research_diagnostics.py，src/brain/tests/test_work_failure_diagnostics.py；新增 src/brain/tests/test_work_http_failure_diagnostics.py。证据和守卫运行器写入新证据根；项目计划/报告、原工单、镜像允许更新。
**Interfaces:** validate_failure_diagnostic(raw,binding_key) 与 capture_failure(ledger) 签名保持；私有kind提升 research_failure_diagnostic_v3；公开摘要保持原字段。

- [ ] 固定官方源码/当前模型metadata来源、SHA、大小和读取边界；形成兼容性矩阵。使用既有只读核对方法检查七个保护身份、原生版本及模型摘要；不变更服务。
- [ ] 先写新测试并保存RED：HTTP500仍返回原 Research HTTP status；诊断增加 last_http；200坏JSON/overflow/扫描失败分别保留实际状态；无正文泄漏或write/ACK信用。
- [ ] 新增 last_http=null 或封闭对象：generation、receipt_index、route(version/tags/chat)、status(null或100..599整数)、send_reserved、request_sha256、request_bytes、downloaded(null或非负整数)、inspected、admitted、retained、transport_failed、validated_response。generation从最后receipt对应的唯一send/admission_refused timeline事件取得；不猜测或从模型文本抽取。路由只接受现有固定method/path/kind三元组，失败即整体诊断UNAVAILABLE，原失败保留。
- [ ] decoder拒绝额外字段/任意URL/正文/异常文本、bool冒充数字、非法路由/status/计数及明显矛盾组合。计数使用整数：request/downloaded上限2**63-1；inspected<=单域cap+1，admitted/retained<=单域cap（metadata32768/chat65536）；admitted==retained且inspected为admitted或admitted+1；未send无status/body计数；non2xx必须transport_failed且无admitted/inspected。last_http存在时generation为1..8且<=budget.generations、receipts<=24及零起始receipt_index为0..23。validated_response只表示chat secured_envelope存在，必须已send/2xx/无transport错误；绝不表示事实或交付通过。
- [ ] validated_response须同时匹配wire.generation、wire.hashes.entity与receipt请求摘要，并存在secured_envelope字典；不能仅因为同一代有旧wire就认定验证通过。timeline最多256条；仅接受对应receipt_index的一个send或一个admission_refused事件，并核对事件kind与send_reserved一致。
- [ ] 不修改transport发包、body读取、原请求构造、schema/重放、写入或验收门。新增数据仍扫描、CAP16384、冻结一次、complete=false/credit0；GET metadata receipt保留空实体摘要，send_reserved表示发包前已预留，不冒称网络送达。
- [ ] 同一守卫下GREEN并运行失败诊断、传输、研究、导航、交付及schema相关现有回归。使用现有隔离Python和审计钩子，禁止网络/model/UI/process操作；全局真实包数不声称由Python audit完全证明。新证据保留每组源码快照、stdout/stderr、junit、audit和receipt，不覆盖RED。
- [ ] 若兼容性调查证明额外接口缺口，先在本计划附明确依据与最小测试，经独立复核再修改；没有证据则明确记录未修复原生解析原因，不为了“修复”重复已设置参数。

## Task 2 — 独立审查、封存及准确交付

- [ ] 新计划先独立只读审查通过；整个候选完成后独立只读准备审查。必要有界补修只处理意见，保留旧结果；不消耗新实际例。
- [ ] 保存当前文件/依赖绑定与清单，核验冻结前例及无关文件保持；只提交明确路径，在候选、项目文档及 UltimaDocs 本地提交/tag并读回。此前push自动审批阻断，不绕过或重复尝试。
- [ ] 原工单/当前状态登记当前离线候选和review；E02继续0/3，T2/Owner未通过，历史E01/E03不迁移。本轮model_calls=0/actual_cases=0，前例失败与清理身份结果保持独立。
