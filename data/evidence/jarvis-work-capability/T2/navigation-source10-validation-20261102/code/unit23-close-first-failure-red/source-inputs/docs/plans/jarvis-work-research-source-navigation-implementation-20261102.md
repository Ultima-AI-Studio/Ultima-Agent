# T2 E02 Source Navigation v3 Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking. 本下属计划不授权实现或新建代理；执行方式及 change-domain 由 root 后续具体裁定。

**Goal:** 在原 wo-ultimaagent-20261101-0021/T2 内，让同一个 8B NativeReAct 作者检查已采集来源的安全窗口，再以真正可见的 v3 引用交付一次文件。

**Architecture:** 保留 WorkService、SDK ToolRegistry/NativeReAct/worker、GuardrailsEngine/InstrumentedEngine 和实际 FileWriteTool。一个专门的纯数据模块承载安全投影、页面与可重放记录；WorkLedger 持有请求内权限和状态；现有 research engine view 校验完整历史、阶段 schema 与 native transport。保持历史 v2 重开路径，fresh research 只写 v3。

**Tech Stack:** Python、已安装 OpenJarvis 1.0.4、jsonschema Draft7、Pygments/现有 Python AST witness、HTTPX 公共 streaming API、Ollama typed ChatRequest；不新增依赖。

**Spec:** `H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-research-source-navigation-design-20261102.md`，SHA256 `41998861f1a0eeaad1800f61d19642656b0e19fa4b74dcf0e79366d6dc4c0eef`；归档 `T/source-navigation-design-20261102/revision-3/design.md`。独立 review-3 SPEC/QUALITY PASS `f6ddd91cfe4fed313a249d2a82402abad66ec4fbec16dd58912180c7268a6198`。本计划是该固定设计的执行细化；设计数值、原始固定问题、四来源和事实要求仍为权威。

## Global Constraints

- 保留用户已确认可用的 KWS 基线；本次不重选唤醒引擎。
- 不改变三层架构和单一主脑；不新增第二套 Agent 核心或并行工具注册表。
- 测试使用每轮隔离目录/会话库；不写真实任务队列、真实记忆或无关用户文件。
- 本地或云端模型共用工具授权与成果核验；保持现有 `/ask` 的 `query` 和回复字段向后兼容。
- 不改变现有暂停、Owner、冻结和发布门；正式执行前登记全局主表，遵守根规则的当前 WIP 上限。
- 技术阶段与 Owner 冻结分别报告；技术检查点 tag 使用明确阶段名，禁止提前打 `frozen`。

附加固定边界：当前和未来仅 `qwen3-8b-uncensored`，digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`；永不采用 14B/更大/其他权重、fallback、下载或默认值变更。E01/E03 source9 三轮及 negatives 保留，E02/T2 NOT_PASSED，T3 关闭。source9 9/9、prefix 3/4、offline 1/1 均封闭；source10 为单独候选记账，本文没有分配任何 source/model/actual 预算。

## Review Focus

1. 同一安全 HTML 在不同后缀、无卡页面或全脱敏 页面不得错误授予写权限；Task 1 `test_v3_html_suffix_and_renderable_availability`。
2. SDK START 不携带对象指针、worker 不继承 ContextVar，第二个同参实例/吞异常订阅者不得取得 permit；Task 2 `test_v3_enrolled_identity_and_nonraising_observer`。
3. 第三次 inspect 的观察在本轮 sampler 可临时计数，但 raw/secured/完整历史任一失败均不能签发引用；Task 3 `test_v3_provisional_third_card_no_promotion_on_failure`。
4. HTTPX 大块预读/close 异常不得被记成 cap+1 下载或退款；Task 3 `test_v3_download_inspection_admission_are_distinct`。
5. write intent 后超时、ACK 或读回失败必须保留 needs_attention 和晚到 effect，禁止重复写；Task 2/3 `test_v3_intent_race_and_ack_failure_preserve_effect`。

## 范围、基线与执行前门

缩写：C=`C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent`；H=`H:/UltimaAI/UltimaAgent`；T=`H/data/evidence/jarvis-work-capability/T2`；I=`T/navigation-implementation-plan-20261102`。以下命令内 H/T 应替换为上述绝对路径；PowerShell 变量在命令节给出。当前 C HEAD=`244d2120abcd6b8d7744f74a05bd22de46a2d3a5`，生产 H HEAD=`0a31d84169ba8e151ec2f9a2c6fea958804daa5b`。本次只写计划/analysis/report，未创建候选、未执行测试。

root 已核实 C 是 linked worktree、非 submodule，tracked clean/index empty，当前在 `codex/jarvis-work-capability` 的 C244。依 `using-git-worktrees` Step0，已有隔离时不再创建另一个 worktree；root 放行后才在现有 C=`C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent` 从 `244d2120abcd6b8d7744f74a05bd22de46a2d3a5` 创建 NEW `codex/jarvis-work-navigation-v3-source10` 分支。保留原 branch/ref 与历史 source9 snapshots，H 生产仍 `0a31d84169ba8e151ec2f9a2c6fea958804daa5b`。本次不执行 branch/worktree 操作。执行前核对 C244 tracked/index、H HEAD、历史 source21 manifest、SDK 源 hash、模型默认配置/manifest、既有独立评审及冻结输入；未授权漂移中止并交 root。

允许产品改动的完整清单：

- 新增 `src/brain/work_navigation.py`；修改 `src/brain/work_research.py`、`work_tools.py`、`work_service.py`、`agent_server.py`。
- 新增 `src/brain/tests/test_work_navigation.py`、`test_work_navigation_sdk.py`、`test_work_navigation_transport.py`；修改 `src/brain/tests/test_work_research.py`。`work_verifier.py` 只读复用 `verify_artifacts(binding,write_candidates)`，不改通用文件判断。
- 新增 `docs/specs/jarvis-work-research-navigation-v3-20261102.md`，仅登记此设计的 v3 接口/替代范围与 sealed packet 字段。候选需逐字复制本 approved design 与本 implementation plan 到相同 `docs/plans/` 路径；文档复制不修改其内容。
- 验证适配代码/测试/argv/env/receipt/manifest 只在 NEW `T/navigation-source10-validation-20261102/` 下创建，不纳入产品。不得编辑旧 P4/控制样本/历史 evidence。

保留 `native-read-budget-source9/frozen-inputs.json` 的五项原始 hash：evidence protocol `d641bd1a…`、execution contract `ae721d8b…`、capability contract `99ebc2de…`、delivery plan `78d6d0e2…`、acceptance-cases.json `e8d8c0e7…`，执行者使用原 JSON 的完整值。另保留 reference v2 文档/样本及历史 source21 snapshot/manifest 的全部原始字节与 hash；历史快照不变不等于要求实现后的候选产品 hash 仍等于 source9。未来 source10 仅允许本计划 allowlist 中经放行的文件改变，并生成单独的 candidate expected-hash manifest/commit；未改文件仍须匹配基线，新增/修改文件绑定新 hash，不能覆写旧 source21 manifest 或以新计划覆盖历史权限。每次任务提交精确路径，无 `git add .`、push、tag、生产切换。

## 静态确认的集成位置

`WorkService.submit_work` 现有 collection 在 63–78 行，fresh cards/source_pack 在 73–96 行，最终 verifier 在 132–135 行；全部 fresh 入口切换到 v3。`work_tools.py` 的 `WorkCapabilities`/`WorkLedger`/`bind_work`、writer 299 行及 nested writer 保留结构。`agent_server.py` `_borrow_research` 305 行、view 335 行、`_run_work_agent` 431 行与 startup WorkService 1104 行承担请求本地 wiring。

已读取安装 SDK `sdk.py::ask_full/_run_agent`、`cli/ask.py::_build_tools`：只接受名称列表，通用名称执行 `tool_cls()`，不能传 tool object 或 engine=。现有 shallow-copy Jarvis._engine + InstrumentedEngine._inner + GuardrailsEngine._engine 的 checked borrow 保留。`security/scanner.py` 实际接口为 `scan(text)->ScanResult.findings`、`redact(text)->str`，不是虚构 inspect API。`tools/_stubs.py` START 只有 tool/arguments/agent，END 有 success/result/metadata；SDK caller 发布，worker 执行，END result 截断上限10240字符，v3 完整结果另限3072 UTF-8 bytes，因而不能依赖截断文本恢复证据。SDK agent 标识是 `native_react`，不能当请求 UUID。

### Task 1：安全投影、最终页面、canonical v3 及重放（独立纯数据单元）

**Files:** Create `src/brain/work_navigation.py`、`src/brain/tests/test_work_navigation.py`、v3 spec；Modify `src/brain/work_research.py`（wrapper/版本分派，保留所有 v2 算法）。

**Interfaces（新增项目接口，不是 SDK API）：**

- 新模块只在顶层导入 stdlib；不导入 work_tools/agent_server。`BindingKey = tuple[str,str,str]`，数据类均 frozen；集合使用 tuple/bytes，禁止冻结 dataclass 内藏可变 dict。
- `ScanPolicy(scanners:tuple[object,...], mode:str, policy_json:bytes, policy_sha256:str)`：可信准备持有的实际配置 scanner 顺序/后端版本/hash；不进入 inspector。每次 preparation 检验 scanner 配置，composition borrow 再核对同一对象/顺序及 policy。
- `SourceV3(source_id:str, identity_json:bytes, domain:str, suffix:str, total_lines:int, safe_line_pairs:tuple[tuple[int,str],...], omissions:tuple[tuple[int,int,str],...], anchors_json:bytes, available:bool, reason:str)`；identity_json 包含设计 U 全字段，raw body 不在此类。
- `CatalogueV3(binding_key:BindingKey, nonce:str, policy_sha256:str, sources:tuple[SourceV3,...], catalogue_json:bytes, catalogue_sha256:str)`；safe only。nonce 一次生成32小写hex。原 `ResearchCollection` 和本次 GET ledger 冻结为受限的 `collection_json:bytes` 与 `get_records_json:bytes`，writer/replay 持有，不出现在 inspector。
- `PageKey(generation:int, seq:int, dispatch_uuid:str, adapter_uuid:str)`；`ViewV3(view_id:str, source_id:str, start:int, end:int, wire_json:bytes, wire_sha256:str, cards_json:bytes)`。
- `canonical_v3(value:object)->bytes` 实现 J 的精确限制；`build_page(catalogue:CatalogueV3, source_id:str, start_line:int, key:PageKey)->ViewV3`；`v3_writer_schema()->dict` 返回固定有界 schema，无 ref 枚举。
- `work_research.prepare_navigation(collection,binding,scanners:ScanPolicy,*,get_records_json:bytes,deadline:float)->CatalogueV3` 在函数内导入新模块，复用本文件 `_anchors/_python_witnesses/_js_tokens/_fact_evidence`；新模块通过函数内 import 调用这些原 helpers，模块初始化时无反向依赖。
- `IssuedSnapshotV3(binding_key:BindingKey, nonce:str, catalogue_sha256:str, generation:int, views_json:bytes, replay_json:bytes, manifest_sha256:str)`；`resolve_v3(submitted:dict, issued_snapshot:IssuedSnapshotV3, collection:ResearchCollection)->tuple[dict,list[dict]]`（resolved payload/ordered bindings）。`verify_research_artifacts(..., require_reference=False, required_version:int|None=None, issued_snapshot:IssuedSnapshotV3|None=None)` 增加 keyword；生产 fresh 必传3+snapshot。`required_version=None` 只允许显式历史调用保留 v2/原 unversioned reopening；未知 version 一律拒绝，不能自动 downgrade。

- [ ] **RED：先登记 v3 spec 并写断言。** `test_v3_canonical_identity_replay`：独立 J/H oracle 计算 view/ref，改 nonce/B/U/seq/UUID/行字节均改变；拒绝 floats、surrogate、非规范 UUID、碰撞；未知/旧/外国/未签发/跨窗口 ref 均拒绝。`test_v2_archival_bytes_unchanged_and_fresh_requires_v3` 保留 source9 source_pack、ordinal/card/render visibility 与历史 receipt 字节，fresh required_version=3 遇 v2/unversioned 失败。
- [ ] **RED：写安全/页面具体断言。** `test_v3_line_security_projection` 用真正配置 scanner 覆盖 BLOCK/WARN/REDACT、多行 secret/Unicode/CRLF/LF/混合分隔符、全段/逐行 redaction 不一致/残余 findings，脏行不出文本、label、anchor。`test_v3_html_suffix_and_renderable_availability`：相同 HTML 在 extensionless/.html 可出 documented card，在 .ts/.py/.unknown 无卡；所有 documented 后缀逐一参数化；script/style 隐藏，projection hash 漂移失败，raw HTML finding 整源 unavailable。all-redacted/oversize/empty/unrenderable 少于三可用源→zero POST。
- [ ] **RED：写边界断言。** `test_v3_final_fit_and_omissions` 覆盖256KiB、1024行、4096目录、3072观察、24行、8卡的 ±1 与 escaping；先 omission metadata，完整行不切断，最终 trimming 丢弃不完整 anchor/citation、稳定 omission counts；全部 legal starts existence test 使用相同 renderer/fixed-width IDs，目录不泄露获胜页/偏好。只返回行也计 read、零 card。源重复 URL/body、GET mismatch、GET truncated、unsupported coordinates 按设计 unavailable/abort 区分。
- [ ] 运行下方 `unit1-red` 命令，预期因 v3 接口尚未存在而失败；保存首个失败，不以旧 v2 PASS 代替 RED。
- [ ] **GREEN：实现上述接口。** 检验完整原 GET linkage/body/projection hash，精确复现 BrowserChannel HTMLParser 与 `" ".join(parts)`，绑定 extractor `9d7cab4749f27dbc08f1b246e03c8a6f8a059acb74692802a1326216e00ef86d` 与 Python/HTMLParser 身份。code 仍原 witness 和完整 statement；this/super defect 不修。页面按(first,last,kind,symbol)，8行 contiguous citation，gap 截断，不做事实/相关性选择。所有公开字符串与完整序列化观察扫描通过才可返回。
- [ ] 运行 `unit1-green`；要求全部断言绿、独立重放与 v2 字节对照通过，再提交精确三产品/测试/spec路径：`git commit -m "feat: add canonical research navigation views"`。

### Task 2：请求 enrollment、permit、writer 与 service binding（真实 SDK worker 单元）

**Files:** Modify `work_tools.py`、`work_service.py`、`work_research.py`（验证调用）；Create `test_work_navigation_sdk.py`；Modify `test_work_research.py` 的 fresh 测试 fixture/调用。只在 agent_server 添加下一段定义的 preparer 与 startup wiring，不提前替换 engine loop。

**Interfaces：**

- `WorkService.__init__(..., research_preparer=None)` 新增 keyword，普通 work 不调用；显式 research 未配置则 fail closed。实际 startup 注入 `agent_server._prepare_research_navigation(collection,*,binding,ledger)->CatalogueV3`。该回调在 `_ask_lock` 与 ledger 原 deadline 下取得 `get_jarvis()`、ensure_engine、复用 `_checked_research_security(owner)->ScanPolicy` 检查现有实际 wrapper/config/scanners，然后调用 Task1 prepare；不会建立 native client 或发 metadata。callback 输入 collection 是服务已冻结的本次对象，GET records 来自 ledger，不接受 model/context 提供 scanners。测试真实构造同类 SDK wrapper，替换底层推理/transport，不能把 scanner 换成 no-op。
- `WorkCapabilities` 增加 `navigation:CatalogueV3|None=None`（使用 TYPE_CHECKING/延迟注解），`research_json` 保存 writer 专用原 collection；fresh `cards_json=None`。service 冻结原 query、用户 context、capture_json、collection 与 GET 记录，清 browser/provider/replace 的 composition 能力，公开 available_sources/trace 仅安全目录/摘要，原始正文仅原受限证据域。先准备后编 prompt，prompt 仅 safe catalogue、原安全问题和授权目录，无 v2 source_pack/预签发 cards。
- `_checked_research_security` 是现 `_borrow_research` 检查的项目本地提取，返回实际 guard scanner tuple+policy（不实例化第二套 scanner、不改 scanner settings）；`_borrow_research` 重检身份/策略保持一致。callback 与 borrow 之间的任何配置变更封闭失败。
- `WorkLedger` 的单个现有 RLock 保护 navigation state：binding、caller ID、enrollment flag、精确 enrolled object refs、generation/seq、expected action digest、single permit、dispatch/adapter IDs、staged/issued ordered views、seen starts、6次 read计数/18432总字节、write frozen snapshot/intent/effect、first failure、sealed flag。保留普通 work 的现 record/outcome API。
- 新方法 `open_enrollment(binding,caller_id)->None`、`enroll(name:str,instance:object)->None`、`close_enrollment()->None`；`expect(seq:int,name:str,args_hash:str)->None`；`claim(seq:int,name:str,args_hash:str,adapter_id:str,*,instance:object)->str` 返回 dispatch UUID；`confirm_end(seq:int,event:object)->None`；`promote_visible(generation:int,wire_hash:str)->None`；`freeze_for_write(generation:int)->IssuedSnapshotV3`；`seal(reason:str)->None`。新增 `observe_navigation(event,*,caller_id:int,binding_key:BindingKey)->None` 为不向 SDK 抛异常的 callback，内部异常先 seal+invalid permit。返回值/命名由后任务直接消费。
- `WorkInspectTool(BaseTool)` 注册 `ultima_work_research_inspect`，零参数 `__init__` 只捕获 safe CatalogueV3、narrow read capability/私有对象身份，不继承保留 raw caps 的 `_CapabilityTool`。`execute(**params)->ToolResult` claim后 build_page；metadata 写 seq/dispatch_uuid/adapter_uuid/binding，stage完整 bytes，不直接 issue；timeout5秒。
- `WorkResearchWriteTool` 零参数构造时 enroll exact object，并在同 caller 构造 nested `WorkWriteTool`；captured writer 的 execute 使用 v3 claim/已冻结 snapshot/单 reservation；禁止 direct bound invoke 绕 START。完整 render+checked_path+<=3072结果预检都在 intent前；固定用例 path预绑定 `research.md`。现 nested SDK FileWriteTool(allowed_dirs=[root]) 真写一次，结果 protocol_version=3，绑定 submitted/resolved/ordered bindings/view/replay/report+file IDs/byte hash；不提供 public file tool。普通 work 原路径不变。

- [ ] **RED：** `test_v3_service_preparer_uses_checked_configured_scanners` 断言 service collection只做一次、清collection能力、callback看到相同GET records/冻结capture，scan policy变化拒绝；未配置 callback零compose。`test_v3_enrolled_identity_and_nonraising_observer` 用真实 openjarvis.cli.ask._build_tools（经 ToolRegistry lookup）/ToolExecutor worker：两工具恰好各构造一次；worker无 `_ACTIVE` 仍可由captured能力执行；unbound/第二实例/duplicate enrollment/跳过callback/订阅者抛异常/错误START agent或args/重复START/metadata失配/缺END/late END都零permit或封闭，零文件调用。START 没有对象字段，不能伪造比较；permit真正对象检查在worker claim。
- [ ] **RED：** `test_v3_inspector_has_only_safe_capability` 检查 inspector 实例无raw/browser/provider/path/writer，参数仅 source_id/start_line、额外字段拒绝；6次尝试包括invalid/重复，7次拒绝，不返还byte/read计数。`test_v3_writer_real_io_and_external_bytes` 用 real SDK FileWriteTool，外部独立 pathlib.read_bytes+hash 等于独立 oracle render，恰一write；错误path/ref/issuer/source/URL/window/未读/少三源/重复body均zero SDK file调用。
- [ ] **RED：** `test_v3_intent_race_and_ack_failure_preserve_effect` 在intent前/后通过线程 barrier 控制 seal/deadline，真实worker跨线程，前者零写，后者保留effect/needs_attention，late结果独立登记、不覆盖first failure，不重试。缺END、false file success、wrong bytes同样失败；同/异请求并发不串权。
- [ ] 运行 `unit2-red`，预期缺少 enrollment/preparer/inspect 或旧 direct writer 被新断言拒绝。保留旧 suite 每个negative目的：fresh测试通过真实 SDK chain取得ref，不再 `report_payload` 读 cards_json 或直接 writer；历史 v2测试明确隔离只readback，不可为保持旧测试引入fresh v2分支。
- [ ] **GREEN：** 实现 service/callback/ledger/tools。Task2 尚无 engine时，SDK测试用真实 ToolExecutor消费 ledger.expect/测试确认的投影记录，不声称完整产品成功；service端到端成功由Task3完成。历史 witness/renderer测试仍可单独测v2，fresh直接调用writer测试必须改成拒绝断言或真实dispatch。
- [ ] 运行 `unit2-green` 和已完成Task1，验证登记/真实SDK IO/原negative目的保留后精确提交：`git commit -m "feat: bind research inspector and writer permits"`。

### Task 3：完整 SDK conversation、阶段/历史、bounded native transport（集成单元）

**Files:** Modify `agent_server.py`、`work_service.py`（fresh version3最终verify）、`work_tools.py`（仅所需阶段接线）、`test_work_research.py`；Create `test_work_navigation_transport.py`；扩展Task2 SDK测试的完整链。

**Interfaces：** 保留 `_run_work_agent(query,*,binding,tools,max_tokens=None)`、`_borrow_research(owner,binding,ledger,caps,prompt)`、`_ResearchEngineView.generate(messages,**kwargs)`、`_NativeResearchLeaf.generate(messages,*,model,temperature,max_tokens,response_format)`。view在第一次generate前关闭enrollment，要求两精确对象，核对当前SDK max_turns足够容纳六read/write/ACK（不足则拒绝，不修改全局默认）；`_run_work_agent` 在 bind_work/ask_lock 内 open_enrollment，单次 `jars.ask_full(query,agent='native_react',tools=['ultima_work_research_inspect','ultima_work_research_write'],context=False,max_tokens=allowance)`。调用后及finally seal、close own client/unsubscribe；不关闭 borrowed owner。

view每次分配单调generation，保留完整SDK system、原query、assistant action及`USER 'Observation: '+content` history。pin system/template/persona/mainbrain/两tool descriptions/absent exemplars及完整optional fields；只一次替换设计固定prefix（prefix SHA `f1ac2c27009f1759da22b3dfc6f301d0912ba8370f1dd3964433421910474621`，template `a062f71243cd4986a2f2034cf3946912196fd4f4499394815cb0d3a1c522579b`）。不能继续现代码用protocol覆盖整个system。阶段schema只inspect/refuse，三distinct visible source后write可用，read-limit后write/refuse，write确认/独立文件verify后final-only ACK；只本轮已确认pending observation可临时参与sampler资格，不提前issue。secured writer返回后freeze；worker实际dispatch前必须已promote。current action选inspect时仍允许，只要未freeze/read cap；writer-capable turn对inspect也按write-capable output budget2048验证。

leaf在真实 guard扫描输入之后校验全secured message dict与phase expected，保留四hash（secured messages/strict schema/sampler/entity）。typed request一次J序列化，`client.build_request(...,content=bytes)`验证prepared content/options后对同一request `client.send(request,stream=True)`；raw完整输出验证后由view校验secured输出等价，二者均成功才ledger.promote_visible。raw仅进入受限safe replay packet，unsafe失败仅safe digest/counter，不持久化secret。无SDK/tool_executor修改。

- [ ] **RED：** `test_v3_native_react_observation_driven_chain` 真实 NativeReAct/registry/worker/events/guard/scanner/SDK FileWriteTool，一层scripted inference+HTTP transport替换。脚本从真实secured catalogue与观察选择下一source/start、从实际行构造claim和返回ref，不预装S1/S2/S3答案。独立oracle从fixture原字节/原坐标核对三distinct claims、GET→dispatch→view→wire→write→ACK→外部bytes。参数化catalogue顺序、fixture短文本、GET/session ID/nonce，断言相应source attribution/claim/ref改变；stale handle、伪观察、旧text、少第三卡触发reject或独立语义oracle失败。3安全HTML和mixed docs/code亦正向。
- [ ] **RED：** `test_v3_provisional_third_card_no_promotion_on_failure` 对本轮observation、早期assistant/system/role/optional字段/options/schema/nonce/view单独改动，skip guard、截短history、secured redaction/raw成功secured失败、incomplete raw JSON、unknown fields、错误tool/final全部zero promotion与zero新增dispatch。`test_v3_template_prefix_preserves_sdk_policy` exact一次替换、保留技能/两工具/persona/mainbrain，conflictingoverride/未知模板/extra exemplar zero first POST；普通ask原template不变。
- [ ] **RED：** `test_v3_download_inspection_admission_are_distinct` 在真实HTTPX streaming transport边界给4096底层块，remaining512：observed download增4096，inspected增513，admitted512，retained<=512；每response finally只累计一次。非2xx/encoding/Content-Length失败零application body消费但记录observable count；partial read/close异常、metadata失败/过期、connect/write/partialsend保留原generation/POST reservation、不refund、无promotion。unknown counter/peer总量明确null，不声称network cap+1。
- [ ] **RED：** `test_v3_envelopes_deadlines_and_effects` 参数化32,768 prompt+strict bytes、49,152/393,216 POST bytes、metadata32,768/524,288、chat65,536/524,288、6 reads/8POST/16GET、token+512/output<=16384、55秒边界和260秒入口deadline；metadata后/send前/return后/dispatch/readback/ACK重检。prewrite output<=256，write-capable<=2048，ACK<=256；prewrite read min(180,R-55)，ACK min(25,R)，connect/write/pool/metadata<=25按剩余裁剪。partial/timeout/late write/ACK失败保留needs_attention，first error不被close error覆盖，零retry。拒绝overflow/compaction，不把cached prompt_eval_count当全context证明。
- [ ] 运行 `unit3-red`，应暴露现view覆盖system、单writer/v2、response.content无界读取、无promotion链等断言失败。保留首RED log。
- [ ] **GREEN：** 实现phase/history/transport并接回Task2。sdk源码hash集合复制 `T/e03-resume-20261102/preparation/sdk-sources.json` 的六文件基线并增加实际使用registry/cli ask/guard/scanner/runtime/file tool/events源hash；review时锁定，不改SDK。seal exactsafe packet：GET/projection/nonce/policy/template/pages/omissions/cards/dispatch/END args+metadata/generation/times/raw+secured envelopes/wire/hash manifest，replay重算逐项后独立render+read bytes。service/ACK fresh verifier显式required_version=3，不用 v2 `_source_view`/窗口union恢复。
- [ ] 运行 `unit3-green`，完整SDK正反链绿，再运行全部回归与preservation；由独立review审完整candidate，封存commit+SDK/input/env/command/log/JUnit/receipt/hash快照后才可能申请actual。精确提交：`git commit -m "feat: integrate bounded native research navigation"`。

## 统一命令、RED/GREEN receipts 与旧测试保存

以下仅为未来执行命令，当前未运行。候选release后设置PowerShell `$py='H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe'`，`$candidate='C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent'`，`$r='H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code'`。cd `$candidate`。每次stage必须独占NEW目录；保存完整argv/env/import-path/source hash/退出码、stdout stderr、JUnit及receipt，不覆盖RED。

沿用source9 suite隔离规则：TEMP/TMP/TMPDIR/OPENJARVIS_HOME/XDG_CACHE_HOME/HF_HOME/TORCH_HOME/MPLCONFIGDIR/NUMBA_CACHE_DIR各指向`$r/<stage>-env/<key>`；HF_HUB_OFFLINE=1、HF_HUB_DISABLE_TELEMETRY=1、NO_PROXY localhost/127.0.0.1/::1；候选路径在sys.path首并验证已加载产品路径。新navigation测试禁外部和实际11434连接，仅真实SDK+mock transport；原SSE/delivery保留其原ephemeral loopback用途。

精确pytest argv模板：

```powershell
& $py -B -X utf8 -m pytest src/brain/tests/test_work_navigation.py -q -p no:cacheprovider "--basetemp=$r/unit1-red-temp" "--junitxml=$r/unit1-red.xml"
& $py -B -X utf8 -m pytest src/brain/tests/test_work_navigation.py -q -p no:cacheprovider "--basetemp=$r/unit1-green-temp" "--junitxml=$r/unit1-green.xml"
& $py -B -X utf8 -m pytest src/brain/tests/test_work_navigation.py src/brain/tests/test_work_navigation_sdk.py -q -p no:cacheprovider "--basetemp=$r/unit2-red-temp" "--junitxml=$r/unit2-red.xml"
& $py -B -X utf8 -m pytest src/brain/tests/test_work_navigation.py src/brain/tests/test_work_navigation_sdk.py -q -p no:cacheprovider "--basetemp=$r/unit2-green-temp" "--junitxml=$r/unit2-green.xml"
& $py -B -X utf8 -m pytest src/brain/tests/test_work_navigation.py src/brain/tests/test_work_navigation_sdk.py src/brain/tests/test_work_navigation_transport.py -q -p no:cacheprovider "--basetemp=$r/unit3-red-temp" "--junitxml=$r/unit3-red.xml"
& $py -B -X utf8 -m pytest src/brain/tests/test_work_navigation.py src/brain/tests/test_work_navigation_sdk.py src/brain/tests/test_work_navigation_transport.py -q -p no:cacheprovider "--basetemp=$r/unit3-green-temp" "--junitxml=$r/unit3-green.xml"
```

baseline与最终full命令都覆盖真实历史六文件：`test_work_research.py test_work_context.py test_work_delivery.py test_agent_server_sse.py browser/tests/test_browser_channel_s3.py test_interaction.py`（均加`src/brain/`）；完整命令如下，baseline不包含尚未创建的三new files，final另加已列三new files：

```powershell
& $py -B -X utf8 -m pytest src/brain/tests/test_work_research.py src/brain/tests/test_work_context.py src/brain/tests/test_work_delivery.py src/brain/tests/test_agent_server_sse.py src/brain/browser/tests/test_browser_channel_s3.py src/brain/tests/test_interaction.py -q -p no:cacheprovider "--basetemp=$r/baseline-temp" "--junitxml=$r/baseline.xml"
& $py -B -X utf8 -m pytest src/brain/tests/test_work_research.py src/brain/tests/test_work_context.py src/brain/tests/test_work_delivery.py src/brain/tests/test_agent_server_sse.py src/brain/browser/tests/test_browser_channel_s3.py src/brain/tests/test_interaction.py src/brain/tests/test_work_navigation.py src/brain/tests/test_work_navigation_sdk.py src/brain/tests/test_work_navigation_transport.py -q -p no:cacheprovider "--basetemp=$r/full-temp" "--junitxml=$r/full.xml"
```

兼容8项必须独立安全launcher，不能裸跑legacy against H：从 `T/native-read-budget-source9/run_compat.py` 复制到NEW `$r/run_compat.py`，只将checkout/evidence改为candidate/$r，保持预加载、排除H路径、`test_agent_tools_extend.ROOT=$r/compat-sandbox`与import断言。命令 `& $py -B -X utf8 "$r/run_compat.py"`，`compat.xml/compat-loaded-paths.json/compat-receipt.json`。baseline也独立NEW `baseline-compat`副本，以免覆盖。旧293=source9 covering285+compat8，仅历史；本候选真实count由新JUnit计算，保留原280 suite-qualified identities与新增13目的，不删/skip/xfail。fresh测试机械fixture改造允许名字保留、目的增严，保存AST diff/identity映射、旧v2独立replay对照。zero tests now。

### Task 4：独立candidate review后的小适配与分门验证（不属于代码三个unit）

**Files:** NEW `T/navigation-source10-validation-20261102/harness/{adapter.py,test_adapter.py,run_checks.py,headless_proof.py,README.md,manifest.json}`、NEW `code/` receipts、NEW将来actual各轮目录；只读 `T/e03-resume-20261102/preparation-r4/controller.py` 与对应manifest/reviews。不得改旧P4或另造native controller。

**Interfaces:** 小 adapter 复用 P4 `Owned(folder,env).launch(argv,role)/discover()/cleanup(port=None)`、`assert_listener(owned,port,server_argv)`、原受信 authority/source/native proof校验与输出 inventory/first result retention。P4通过P1 `acceptance_adapter.identity(pid)`取得native GetProcessTimes，launcher的`process_times(proc)`使用Popen retained handle；`cleanup`通过原`terminate_owned`重开并复核身份，不得声称所有后代一直由retained handle控制。P4 controller SHA `8b8fb6fdf4868b3bb8cea61daaf402e5336f86167d0be84e04c455586d98706f`，manifest `d3d49198d8e544ac5335f404163b98fb3b92333cb85ee81d3508a7b22eda47b1`。新增 `run_case(authority_path:Path,ledger_path:Path)->dict` 仅映射原E02固定问题/四受控来源、candidate启动argv、v3 packet/外部readback及8POST计数；不能调用P4 execute去运行错误E03 case，也不能把原P4 source_check绑定直接当source10许可。adapter明确source10 manifest/原T2 ledger schema扩展，由root独立审批；owned primitives自身不变。

- [ ] **先静态准备与review：** 精确hash pin P4 helper及依赖，只导入其无side-effect定义，单独审adapter新authority映射、候选argv/隔离root/受控ports/packet封存、first-result保留与native100ns身份读法。原legacy CIM ticks/精度不可与native FILETIME精确相等比较；如需native baseline，单独NEW收集并绑定本次run，旧baseline永不重写。未知父/子/creation身份不授予kill，保留unknown；不杀共享Ollama或无关进程。
- [ ] **RED→GREEN deterministic harness tests：** `test_adapter_rejects_wrong_candidate_budget_and_baseline`、`test_adapter_first_failure_retained_and_no_next_case`、`test_adapter_reuses_owned_cleanup_and_retains_unknown_effect` 参数化source/hash/default/model/nativeprecision/authority过期/CLI超时/nonzero/invalidJSON/partialpacket/missingEND/readback/cleanup失败；断言不自动下个case，原product result与overall独立，未确认native starts不能报0。命令 `& $py -B -X utf8 "$r/../harness/run_checks.py" adapter`，driver保存精确pytest argv，JUnit `harness/adapter.xml`、receipt/log。只mock实际launch/transport；不能计actual合格。
- [ ] **另行release inert harness qualification：** `& $py -B -X utf8 "$r/../harness/headless_proof.py"` 使用原P4 ownership/loopback/cleanup与纯惰性listener，无产品问答/模型/外网/UI，验证source10原E02 query完整argv roundtrip、owned redirector/base/listener identity、原P4身份复核/cleanup、端口关闭、protected before/after相同、315秒outer封存。该命令同样当前未授权运行；如果无法复用P4无新controller实现native精度，停在concern交root，不用历史CIM伪证通过。
- [ ] **candidate+harness双独立审查与snapshot sealing：** 全three-unit commit、allowlist diff、SDK hashes、模板/默认值、历史source21 snapshot/manifest与frozen5/oldartifact preservation、独立source10 expected-hash manifest及allowlist差异、code/full/compat与harness receipts确认，无未决blocker；model/actual仍false，root单独决定首次allocation。不得用“测试通过”预填Owner或T2 PASS。
- [ ] **仅root新分配后actual首例：** 原controlled E02固定问题与原四来源，最多1CLI、1search/4GET、6inspect、1write、1ACK、8native POST starts、260service/300client/315outer，0retry。发起命令 `& $py -B -X utf8 "$r/../harness/adapter.py" --case E02-controlled-1`，adapter只读root签发具体authority/ledger，首次result不可覆盖。收完整真实secured/wire/raw/END/replay包、外部真实research.md bytes/hash、事实/条件/替代/两项目归属及原题覆盖独立审查；任何失败/缺确认/超时/副作用差异立即停止，不自动nextcase。
- [ ] **原验收仍必需：** 首例若完全相同fixture/candidate及独立证据通过才可计入三轮；后两轮各自root allocation/review，任何candidate改动重启same-candidate三轮要求，历史失败继续保留。另行真实免费search/GET联网验证≥3去重来源、引用事实与文件；再fresh同candidate E01/E03+negatives、原T2独立review；后续E04–E08/Owner/release不由此开启。不得以脚本positive代替8B理解、以controlled代替realnetwork、以source9 E01/E03替代candidate回归。

## 自审与交付状态

设计§1 wiring→Task2/3；§2安全/HTML/页→Task1；§3 enrollment/issuance/write/replay/v2→Task1/2/3；§4 schema/history/transport/budget→Task3；原P4/acceptance→Task4。五项Review Focus都有具名测试/owner；引用signature仅在前任务定义后消费，无未定义SDK API；纯数据类型避免import cycle。测试按失败原因与真实SDK/独立fixture oracle区分，不增加模型事实评分器。三个代码unit加单独验证任务，没有机械scaffold review unit；实施体量保持在固定设计边界内。

当前仅静态读取/普通hash/文档写入；没有product/SDK/scanner/lexer/HTTPX runtime import，没有测试/模型/网络/进程实验，无subagent。implementation/source10/model/actual/T3 release全部false。待root独立plan review与具体执行裁定。运行语义未知项保留：8B实际导航/理解、真实SDK安全history大小、deadline晚到effects、native precision新baseline与harness适配资格。它们是后续证据门，不是允许改协议或放宽预算的理由。


