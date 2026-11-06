# 同候选E01 round1文件交付回归准备计划

> For agentic workers: use superpowers:executing-plans inline, one fresh whole-package preparation review. Keep permanent evidence; no new live case without its concrete allocation.

Goal: E03当前候选三正例和目标变化负例全部独审登记后，准备同候选269aca5的E01 round1，验证当前8B能够真正交付summary.md。此计划只允许离线准备；没有E01模型调用或实际用例分配。

Architecture: 复用已审独立入口控制、现有Case/Owned、隔离Agent服务器和工作CLI、机械核验及外部文件读回。接线E01现成分支，不新增Agent框架、不改产品源码或默认模型；不启动窗口夹具。不得直接用旧通用harness的900秒CLI等待。

Spec: jarvis-work-capability-contract-20261101.md R01/R02/R03/R05/R08及E01；delivery-plan T2要求本候选E01—E03全绿。三轮核心模型通过必须同候选，先准备round1，后续round2/round3仍需各自新鲜交付证据，旧候选成功不混算。

约束：只用qwen3-8b-uncensored/digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330，Ollama0.32.15，7保护身份、KWS/语音不改。60秒proof/120秒authority；CLI300秒/SDK1800秒/controller315秒；一个CLI、失败不重试、0音频；E01无UI/麦克风/真实记忆。前置E03负例仍须独审及登记，当前计划不预填其PASS。

Task1：将E03三个正例及负例原terminal/review/registration和恢复基线绑定到新E01包。负例没有生成内容，按真实behavior/target/no-output/cleanup独审schema验资格，不伪造facts PASS。先写未合格前置、遗漏依赖、混候选、旧scope、过期proof/authority及扩额拒绝测试，观察RED后最小实现；拒绝必须在backend/native构造前。

Task2：接入现成E01路径。新Case只创建隔离运行目录；不launch fixture、不采集当前窗口、CLI不带current-window/replace-selection/research。读取冻结acceptance-cases.json的原request与三facts，启动既有隔离server，核对health/监听owner及8B，在真实CLI提交前重验同一authority/proof。固定summary.md产物、真实SDK工具记录、服务读回和外部读回及完整清理；终态事实保持等待独审。失败/断连/缺产物不能显示完成。

Task3：行为测试在原生/进程/模型边界用离线替身，真实被测入口/文件核验函数不stub。覆盖无UI、正确固定请求/参数/超时、服务器准备后准入过期不发CLI、错误或缺产物失败且清理、scope不能走负例路径。只运行本包完整隔离离线套件；未改产品485/8只核对绑定，不擅自跑可能触发模型/音频的全产品入口。父测试仅保留适用语义并记录转换，不把不适用UI断言算成已验。

Task4：核对57源码/7依赖/1346SDK及前置原件、清晰说明测试与真实验收区别；封存新manifest，由一次fresh独立reviewer全包只读审查。Important按有界修复规则处理，保留全部失败；不消耗实际结果复核。

Task5：计划/报告镜像、本地明确路径commit/tag和字节读回完成后，再提交一个E01 round1及一次独立事实结果复核的具体分配提案。此前自动审批Git push拒绝不换通道重试。计划本身不签发E01 authority或准入，不放行E02/T2出口/T3—T5/Owner。

Review Focus: (1) E03前置必须真实完整，不能把focus重新观察冒充focus拒写或完整替换；(2) E01无窗口/音频副作用，但保护检查保持；(3) 固定材料和可信输出根不能由模型改变；(4) source/model/时限/one-CLI必须在实际提交点仍有效；(5) 写入及独立读回、清理、事实复核分别计证据，不以退出0替代交付。

Ruling: 沿用户持续目标先做下一步离线准备，不请求重复实施方式；当前新授权只覆盖E03负例及其结果复核，E01实际分配仍为0。代价：准备完成不等于E01通过。
