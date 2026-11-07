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

