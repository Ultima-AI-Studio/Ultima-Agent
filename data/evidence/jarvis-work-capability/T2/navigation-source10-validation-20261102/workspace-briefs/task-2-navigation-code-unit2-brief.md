# Source10 code unit2 — implement now

U1 independent SPEC/QUALITY gate and root BASE/interface readback completed. Original main T2; same approved design41998861 and code-only authority. Model/actual/T3 remain false. No subagents. This final brief provides the full task plus actual U1 interfaces/commit and root rulings.

## Global Constraints

- 保留用户已确认可用的 KWS 基线；本次不重选唤醒引擎。
- 不改变三层架构和单一主脑；不新增第二套 Agent 核心或并行工具注册表。
- 测试使用每轮隔离目录/会话库；不写真实任务队列、真实记忆或无关用户文件。
- 本地或云端模型共用工具授权与成果核验；保持现有 `/ask` 的 `query` 和回复字段向后兼容。
- 不改变现有暂停、Owner、冻结和发布门；正式执行前登记全局主表，遵守根规则的当前 WIP 上限。
- 技术阶段与 Owner 冻结分别报告；技术检查点 tag 使用明确阶段名，禁止提前打 `frozen`。

附加固定边界：当前和未来仅 `qwen3-8b-uncensored`，digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`；永不采用 14B/更大/其他权重、fallback、下载或默认值变更。E01/E03 source9 三轮及 negatives 保留，E02/T2 NOT_PASSED，T3 关闭。source9 9/9、prefix 3/4、offline 1/1 均封闭；source10 为单独候选记账，本文没有分配任何 source/model/actual 预算。


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


## Root rulings to carry into final brief

- Real SDK name builder is openjarvis.cli.ask._build_tools with real ToolRegistry lookup, as corrected latest plan a8419b77. No nonexistent ToolRegistry method or object/engine injection.
- build_page keeps pure-data signature/Catalogue safe-only. The trusted request-local narrow read operation owns actual ScanPolicy and calls scan_view(view,policy) on final actual serialized bytes before any staging/SDK result. Inspector captures only safe catalogue+narrow callable. No scanner/raw caps/global registry in inspector. Fixed-width preparation stand-ins prove renderability, not later wire safety. Verify U1 returned helper exact contract before implementation.
- Standard research target basename is trusted server choice research.md under fresh request root, fixed before generation; no new natural-language filename parser or context/model authority. Reject mismatched writer path, and later harness externally verifies exact basename.
- Visible writer ToolResult.content includes compact path receipt within3072 UTF8 bytes; full submitted/resolved/bindings/replay remain restricted ledger/packet and are linked by exact IDs/hashes. Do not duplicate unbounded report payload into visible observation. Follow exact binding design.
- Ordinary work/selection delivery retains behavior; v2 only explicitly historical readback. Partial units are not product passes and service full success is U3.
- Root baseline covering285+compat8 actual passed before modifications; compat old anyio warning/optionalvoice fallback accurately recorded. NEW results must be derived from receipts, no stale count as current pass.

- Trusted policy propagation: `_prepare_research_navigation(collection,*,binding,ledger)` still returns CatalogueV3 exactly. Before return it must configure the request ledger once with that catalogue, actual ScanPolicy and frozen restricted collection/GET bytes through a private trusted preparation step. This is not a model/tool parameter. The later narrow read port can call build_page+scan_view with this policy while inspector retains no policy/raw caps. Borrow rechecks the same scanner objects/order/config/policy. Do not add a second scanner set, global registry or mutable fields to CatalogueV3 to bridge this interface. Exact private method name can follow minimal local style; report it for U3 consumption.
- Current actual source9 `_borrow_research` and installed GuardrailsEngine recognize only configured SecretScanner/PIIScanner order. U1 replay supporting these default scanner identities is consistent with current checked product; unknown or changed scanner/backend/config fails closed, never silently substituted.


## Actual upstream gate and execution

U1 reviewed clean at BASE494e544788c287defbf1208967444e733df5501a on existing C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent branch codex/jarvis-work-navigation-v3-source10. Final review V/review-unit1-2/verdict.json90d57d47 SPEC/QUALITYPASS, only nonce Minor fixed. Root unit1-result.json is UNIT_ONLY, E02/T2notpassed. Root will tag/push immutable494 separately and publish H evidence with private index, not touch your C/index. No branch/worktree changes by you.

Your exact allowed paths: src/brain/work_tools.py, src/brain/work_service.py, src/brain/work_research.py, src/brain/agent_server.py, src/brain/tests/test_work_navigation_sdk.py, src/brain/tests/test_work_research.py. You may append concrete runtime interface documentation to the already new docs/specs/jarvis-work-research-navigation-v3-20261102.md if necessary, preserving existing obligations. Do not change work_navigation.py/its tests, generic verifier or approved plan copies. Concrete upstream bug needs root context, not silent extra-path change.

Read actual U1 public contracts from V/code/unit1-public-interfaces.json (at e0, same signatures now494) plus source as needed. make_scan_policy(tupleactualscanners,mode)->ScanPolicy; validate_scan_policy(policy,expected=None); prepare_navigation(...get_records_json:bytes,deadline:float)->safe Catalogue; build_page and scan_view; seal_snapshot(catalogue,collection,get_records_json,policy,reads,*,generation) only pure data; resolve_v3,render_v3 and required_version+issued_snapshot verifier. Full U1 author report W/task-2-navigation-code-unit1-report.md and v3spec describe boundaries; do not read whole subordinate plan. WorkNavigation module root imports stdlib only.

Invariants needed by U3: configure trusted raw evidence+policy once before returning Catalogue from preparer; exact epoch-enrolled tools on SDK caller; no ContextVar lookup on worker; narrow final-safe read/stage port; one permit per validated START; immutable END linkage; no promotion from synthetic/failed/missing/late data; atomic live-seal/deadline check at actual file intent; one reservation/write; freeze exact issued set for writer. Final render and all decoded author/public strings must pass actual captured configured policy before intent, including escaped JSON fields, and compact visible receipt must fit3072 before any file effect. Keep full restricted receipt/replay in ledger with hash linkage, not oversized visible tool result. Use current Guardrails policy, no custom security backend/framework.

Task2 is a real SDK ToolExecutor/worker/service unit, not complete NativeReAct phase integration (Task3). Tests may drive the trusted ledger methods with explicit staged/confirmed fixtures to isolate that boundary; label that evidence and independently read actual file bytes. Never bypass permits using direct writer success, never pretend fixture confirmation is observed native wire, and never introduce fresh v2 fallback/skip/xfail to keep old tests green. Original test_work_research.py65 named functions and their negative purposes must remain; static identity inventory at I/root-research-test-static-inventory.json and original293 JUnit identities recorded in I/root-historical-test-and-sdk-inputs.json. Preserve unchanged old test assertions unless a fresh protocol fixture must change, report an explicit purpose mapping.

Unit1 latest targeted235 passes on494; full341 applies e0 before nonce correction, not rerun on494. Baseline legacy compat8 passed before U1 only, known anyio warning/optionalvoice fallback retained. NEW count from your actual JUnit; no additive/stale count claim.

## Commands and evidence

Use fixed H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8 and read-only V/code/run_code_tests_v2.py60f6ea3d. NEW stage unit2-red then unit2-green, covering src/brain/tests/test_work_navigation.py src/brain/tests/test_work_navigation_sdk.py. Real registry via openjarvis.cli.ask._build_tools, ToolExecutor/worker/events/actual configured guard scanners/real FileWriteTool; replace only inference/network transport where necessary, use real isolated tempfile roots. New tests deny live11434/external connects; preserve original SSE ephemeral loopback purpose in full regression. Controlled clock/randomness/barriers for deterministic contract tests are okay; no replacing SDK registries/executors/guards/file tools with fake success.

Before commit run NEW unit2-covering with original six regression files plus completed navigation+SDK tests: src/brain/tests/test_work_research.py src/brain/tests/test_work_context.py src/brain/tests/test_work_delivery.py src/brain/tests/test_agent_server_sse.py src/brain/browser/tests/test_browser_channel_s3.py src/brain/tests/test_interaction.py src/brain/tests/test_work_navigation.py src/brain/tests/test_work_navigation_sdk.py. Root v2 runner captures argv/env/raw before/after bytes, JUnit/logs/paths. No duplicate broad runs unless new changes/failure justify. Preserve first RED and every failure, use suffixes, no overwrite. Run exact staged-path diff-check, then commit only allowed paths with maintenance.auto=false/gc.auto=0/core.autocrlf=false; normal index empty after. No push/tag by you.

No SDK/vendor/defaults/dependencies/queue/globalmemory/oldartifact/KWS/production/model/network/UI/audio/subagent changes. All existing code-only constraints apply. If the apparent Task2/3 boundary cannot keep the scoped real tests sound without premature loop implementation, escalate the concrete interface/test conflict rather than weaken/skip tests or invent fake product success.

## Report

Write W/task-2-navigation-code-unit2-report.md: status; exact BASE..HEAD commits/files; actual exposed interfaces/state invariants for U3; RED/GREEN/full argv/output/receipts/hashes; real SDK file readback/provenance/negative-purpose map; unchanged inputs/loaded paths/whitespace and all warnings/failures; self-review/concerns. Root owns independent task review. Return <=15 lines with DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED, commits, counts and concerns. Model/native actual/T3 success remains unclaimed.

Path aliases: V=H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102; I=H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-implementation-plan-20261102; W=C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent/.superpowers/sdd/jarvis-work-capability-delivery-plan-20261101.
