# 同候选E01 round2文件交付回归准备计划

> For agentic workers: use superpowers:executing-plans inline, then one fresh whole-package preparation review. Permanent evidence; no actual round2 allocation in this plan.

Goal: 当前候选269aca5的E01 round1实际产物经独立事实复核并正式登记后，准备同候选round2。E01要求三轮新鲜真实交付；不能用相同文件摘要、旧候选或离线套件替代。本计划仅允许离线准备。

Spec: jarvis-work-capability-contract-20261101.md的E01/R01/R02/R03/R05/R08及同候选三轮要求；T2出口必须E01—E03齐全。E03现有三正例和目标变化负例已登记，本计划不重新审判其事实。

Architecture: 精确复制已审E01 round1入口到独立round2证据目录，保持产品269aca511d88412dbb9c15d23911138469a37aa2、现有隔离Agent服务器、真实工作CLI和文件核验。只增round1前置资格，并把当前case/scope及证据根切换round2。不新增产品功能、Agent框架、模型或依赖。

Constraints: 仅qwen3-8b-uncensored，digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330；Ollama0.32.15，原7保护身份。60秒proof、120秒authority、CLI300/SDK1800/controller315；一CLI、失败不重试、零UI/音频。summary.md及三条原材料来自版本化夹具，可信输出根+服务生成新UUID；不改默认模型、KWS/语音或真实记忆。

Task1: round1独审/登记完成前，仅做此计划和只读分析。完成后复制原terminal、独立review、登记到新包，绑定同候选/当前8B、实际一CLI、机械/事实/文件/最终声明/清理、产物摘要及累计E01正例1/3。保留E03四份前置及恢复基线。先写缺失、混候选、复核FAIL、无credit、摘要矛盾和时间逆序的失败测试，再最小接线；在native backend创建前拒绝。

Task2: 只切换到e01-round2/e01-round2-acceptance和新证据根，authority必须绑定全部五份资格。旧scope、前轮actual/release、扩额和过期准入均拒绝。原提交前最后时钟检查、实际写入/独立读回、收尾前副作用核对和清理不改。事实终态继续等待独审；不能预填round2通过。

Task3: 原208项适用语义完整继承，记录当前case、完整前置数量及路径的转换；新增前置行为先RED后GREEN。运行本包完整隔离离线套件，禁止直接启动旧900秒通用harness。未改产品485/8只核对绑定，不重复运行模型或音频。保留全部失败和测试映射。

Task4: 核对57源码/7依赖/1346SDK及E03/E01前置原件，封存manifest，一次fresh独立准备review。Important按有界修复处理；无新的实际用例或结果复核额度。

Task5: 计划/报告同步UltimaDocs，明确路径本地commit/tag及字节读回；然后才提交一次当前8B E01 round2及一次只读独立结果复核的具体分配。此前Git push自动审批拒绝保持，不换通道重试。准备PASS不授予round2现场、E01整体、E02、T2出口或Owner通过。

Ruling: 持续目标授权覆盖下一步离线准备；最近单例授权仅为round1及一次结果复核，不延伸为round2实跑。前置事实审查未完成时不建立round2资格或启动实现。代价：必须等待本轮独审真实完成。
