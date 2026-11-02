# Source10 code unit 1 — implement now

Read first: requirements with exact values. Original main order T2. Plan gate SPEC/QUALITY PASS a65a30ec/de12df7f; approved design H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-research-source-navigation-design-20261102.md SHA41998861f1a0eeaad1800f61d19642656b0e19fa4b74dcf0e79366d6dc4c0eef is binding. Read its exact safety/page/canonical/replay semantics; this brief provides your full task and global constraints, do not read the entire subordinate plan or accumulated history.

## Execution ruling

Root code-only authority: H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/root-code-only-authority.json SHA0ec6abcddd133dc1ba88bb3adc643bbfb3915a39ef3d1064ca65796c74196fbb. Current C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent now NEW branch codex/jarvis-work-navigation-v3-source10 at BASE244d2120abcd6b8d7744f74a05bd22de46a2d3a5. Work only here. Existing linked worktree; do not create another/switch refs. H production HEAD0a31d84, protected5, KWS/audio/voice/ordinary paths untouched. No subagents. No models (including current8B), actual11434, external network, audio/UI, dependency installs, shared SDK/default/queue/memory/old-evidence edits, push/tag/production integration. Follow TDD and karpathy-guidelines; current Task1 only, no Task2/3 code.

Review F1 Minor was exact one-line name erratum, verified by root. Latest subordinate plan a8419b77, archived r2 a0683169 untouched; actual SDK builder is openjarvis.cli.ask._build_tools via ToolRegistry lookup. It is consumed only in later Task2. All approved architecture/limits unchanged.

Root copied TWO approved docs byte-exact into C/docs/plans (untracked); include these exact files in your final unit1 commit alongside your four explicit Files below: jarvis-work-research-source-navigation-design-20261102.md SHA41998861; jarvis-work-research-source-navigation-implementation-20261102.md SHAa8419b77. Do not edit them. No broad staging, resets/cleans or unrelated file changes. Original frozen5 files and work_verifier.py are read-only. Original source21 manifest immutable; only this task allowed paths may change in source10.

## Global Constraints (verbatim)

- 保留用户已确认可用的 KWS 基线；本次不重选唤醒引擎。
- 不改变三层架构和单一主脑；不新增第二套 Agent 核心或并行工具注册表。
- 测试使用每轮隔离目录/会话库；不写真实任务队列、真实记忆或无关用户文件。
- 本地或云端模型共用工具授权与成果核验；保持现有 `/ask` 的 `query` 和回复字段向后兼容。
- 不改变现有暂停、Owner、冻结和发布门；正式执行前登记全局主表，遵守根规则的当前 WIP 上限。
- 技术阶段与 Owner 冻结分别报告；技术检查点 tag 使用明确阶段名，禁止提前打 `frozen`。

附加固定边界：当前和未来仅 `qwen3-8b-uncensored`，digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`；永不采用 14B/更大/其他权重、fallback、下载或默认值变更。E01/E03 source9 三轮及 negatives 保留，E02/T2 NOT_PASSED，T3 关闭。source9 9/9、prefix 3/4、offline 1/1 均封闭；source10 为单独候选记账，本文没有分配任何 source/model/actual 预算。


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


## Fresh baseline and exact verification

V=H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102; code receipts only in V/code NEW stage folders. Root freshly ran historical six-file suite: 285 PASS, 0fail/error/skip; actual loaded product paths C and SDK H site-packages all checked. Legacy compatibility safe copy: 8 PASS. Thus new baseline293 actual, unlike old historical293. Read V/code/baseline/{receipt.json,stdout.log,loaded-paths.json} and V/code/baseline-compat/{compat-receipt.json,stdout.log,stderr.log}. Compat has one preexisting PytestAssertRewriteWarning anyio from preload and one missing optional voice reference fallback diagnostic; record them accurately, do not modify voice/SDK/default to suppress them or call output pristine. Six-file suite output clean.

Use fixed H interpreter H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -B -X utf8. V/code/run_code_tests.py is a minimal root-created one-shot pytest runner: preserves exact -m pytest command, NEW basetemp/JUnit/env/temp/cache directories, records stdout/stderr/receipts and candidate/SDK loaded-path checks. Read it; do not modify. It is not a native/process/actual harness. It has no model/network authority. Run it with NEW stages unit1-red, unit1-green and unit1-covering; keep all first failures, use new suffixes after further changes rather than overwrite.

Commands from C (PowerShell):
& 'H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe' -B -X utf8 'H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/run_code_tests.py' unit1-red src/brain/tests/test_work_navigation.py
& 'H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe' -B -X utf8 'H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/navigation-source10-validation-20261102/code/run_code_tests.py' unit1-green src/brain/tests/test_work_navigation.py
Before commit run unit1-covering with the six original files plus test_work_navigation.py: src/brain/tests/test_work_research.py src/brain/tests/test_work_context.py src/brain/tests/test_work_delivery.py src/brain/tests/test_agent_server_sse.py src/brain/browser/tests/test_browser_channel_s3.py src/brain/tests/test_interaction.py src/brain/tests/test_work_navigation.py. This is the scoped project regression suite; do not run bare repository pytest touching unrelated live modules/queues. Compat need not repeat during pure-data unit absent a new compatibility concern; final full candidate will repeat safely. New navigation tests deny live sockets except in-process mock transport if needed; real configured SDK scanners/lexer and temporary files remain real, not a no-op scanner or expectation derived by code under test.

Actual SDK is H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Lib/site-packages/openjarvis; C/libs/base/openjarvis is not installed runtime. Source6 pinned in T/e03-resume-20261102/preparation/sdk-sources.json. Existing v2 helpers and witness semantics are in src/brain/work_research.py; extraction policy exact source src/brain/browser/channel.py. Do not fix deferred TS this/super defect. No new semantic oracle/parser or custom security framework. Keep module focused within approved design; escalate concrete interface/size conflicts to root rather than silently change contracts.

Before implementing production code, write meaningful behavioral assertions, run RED and record why it is feature-missing failure rather than typo/API-name error. Keep original RED log; run focused covering tests after changes. Commit only exact six paths (four task files plus the two byte-exact root doc copies), with maintenance.auto=false, gc.auto=0, core.autocrlf=false; current shared normal index must remain empty after commit. No push/tag.

## Report

Full report: C:\Users\Administrator\.codex\worktrees\jarvis-work-capability-longpaths\UltimaAgent\.superpowers\sdd\jarvis-work-capability-delivery-plan-20261101\task-2-navigation-code-unit1-report.md. Include status, exact commits BASE..HEAD, files, concrete behavior/interfaces for next task, RED/GREEN/covering argv+logs+JUnit+counts/hashes, loaded-path validation, all failures/warnings/concerns, tests catching specific mutations, and self-review. Return <=15 lines DONE/DONE_WITH_CONCERNS/NEEDS_CONTEXT/BLOCKED, commit(s), test counts and concerns. Root owns task reviewer; never dispatch helpers/reviewers. Do not claim E02/T2 or model/actual success; those remain unpassed/unallocated.
