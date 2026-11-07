# E02 ee1bef6 受控入口准备完成

本轮按用户“为新候选准备受控入口和绑定；明确分配单例后，再取得真实请求回执，据此决定原生兼容修复”执行。准备工作、离线检查及独立准备审查已完成。当前实际分配0、实际运行0、模型调用0；真实请求回执尚未取得，E02仍0/3，T2/Owner未通过。

产品候选 ee1bef61f04169c64978538dbc4ba799ef7be6c0 保持冻结且工作树干净。本轮复用N11受控入口，重绑68个当前源文件、1567个输入文件，完整check_inputs核对1570项。原题/四来源、当前qwen3-8b-uncensored摘要6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330、七保护身份、原时钟和清理保持。

入口增加已证实必要的范围检查：直接用户消息必须明确分配严格整数actual1/review1/retry0。原实现在准备消息被包装成grant时未验证其范围，RED产生25个预期失败断言；补修后准备消息在消费前被拒绝、不触及run_released，明确授权的合成正例保留。只修改entry的这一条件，adapter/bindings函数与类AST保持，产品源码未改。

当前新执行339项去重离线检查PASS：入口34、绑定16、边界11、adapter278（五组原始280、重复2）。完整SDK MockTransport与原导出入口覆盖HTTP500、200坏JSON和扫描拒绝：请求摘要、代次、路由和v3私有回执相符；500不读取正文，200失败不误标validated；原首个错误、16KiB上限、write/ACK及零验收信用保持。N12的706项只是已封存产品基线，未计为本轮新执行。模拟回执不算真实原生请求证明。

计划审查PASS_PLAN_ONLY；整包独审PASS_PREPARATION_ONLY。manifest SHA256 01d1c12f63e19d7ea72020a28fad3f2a4ba1496aaa31ccbd6112a245919ec7cb（149成员）；独审SHA256 92c9eb76aa4a51c788797f44b7f1837dd13f3913ecd90d7c4547c55a46d0f7d9。harness-approval仅绑定准备审查，read_ready已读回；read_release在无grant时拒绝。本轮无release、actual或controller-authority目录，无UI/音频/生产服务操作。

北京时间2026-11-07 17:06:53只读核对七个保护身份一致、Ollama0.32.15、当前8B摘要一致、18799空闲；只代表该核对点。N12/N11封存、前例失败及9无关文件逐字节保全，旧PASS信用不迁移。前例be79869f…仍FAIL_CONFIRMED，无research.md，清理PASS、retry0。

待明确分配的单例见同证据根execution-proposal.md：当前8B原题四来源一次受控研究，加一次只读独立结果复核，失败不重试。CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒；context16384、messages+schema32768/entity49152字节、输出上限2048保持。无需暂停键鼠。只在真实答复后生成与本manifest/独审绑定、TTL<=120秒的一次grant。

后续先封存首个真实请求和结果，独立复核状态、证据和交付；再依据确证问题决定原生兼容修复。未确证原因前不改模型/请求协议/预算，也不把准备通过当作E02通过。

项目与UltimaDocs以本地提交/tag及publication-readback.json读回收口。远端push此前被自动审批以blocked by policy拒绝，本轮不重试；remote_synced=false。

证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-http-controlled-preparation-20261107-r1
