# Source10 code unit 1 — DRAFT, not a release

Not dispatched. Root must first confirm independent plan gate and supply a concrete code-only authority plus fresh baseline receipts. This draft only extracts the approved-design task; it allocates no code/model/actual authority.

C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent is existing isolation; current HEAD244 before future branch. Requirements below are copied exactly from current subordinate plan a0683169, design41998861 is binding. Read only the task and design relevant sections, not accumulated history. No subagents. Fixed H python -B -X utf8, no dependencies or SDK modifications, no native model/network/UI/audio/production calls.

## Global Constraints

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

