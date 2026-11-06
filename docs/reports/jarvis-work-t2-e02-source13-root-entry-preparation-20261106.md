# E02 source13 外层入口准备记录

原工单 `wo-ultimaagent-20261101-0021`，阶段 T2。本记录只覆盖当前入口的离线实现与准备审查，不授予实际运行权限。

## 当前结论

E01 固定样本三轮实际交付及独立复核均通过；E03 同候选三正例和一负例通过。E02 外层入口修复后的源码已按用户新增授权完成一次只读独立复核，结论仍为 **NEEDS_FIXES**，有一项 Important：HELLO 等待未持续保留后续身份查询及尚未登记成员的清理余量。已有修复只关闭了部分 R1，不能因 **83/83 离线检查通过**而登记准备通过。当前门为 **NOT_READY_CLEANUP_HANDOFF**，E02/T2/T3–T5/Owner 仍未通过。

产品候选固定 `269aca511d88412dbb9c15d23911138469a37aa2`，模型仅 `qwen3-8b-uncensored`，摘要 `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`。冻结产品源码、B 包 profile 和 SDK 字节保持。

## 具体实现与验证

入口在 `data/evidence/jarvis-work-capability/T2/e02-source13-root-entry-20261106/code`，共八个源码/测试文件：父进程入口、准入与读回控制、原生退出观察、严格文件记录、三份测试及固定离线 runner。

- 父进程独占消费一次分配，从最早 monotonic 时钟继承 275／310／315 秒截止，独立记录工作返回与清理结果文件的出现时间。
- 复用已接受的 Owned 启动/清理 helper。实际 worker/reader 的完整 argv、父子关系及原生身份通过后，才保留该进程只读句柄观察退出；启动器退出不代替实际 worker 退出。
- 从固定原始记录构建 `WorkerControls.admit` 与两次 `ReaderControls.readback`；worker 无权提供 origin、根路径或退出结论。新 reader 重新打开文件、调用原纯重建与读回入口；外层机械成功仍只标记 `PENDING_RESULT_REVIEW`。
- 当前完整 83 项由 28 项原生观察/适配、36 项控制记录、19 项入口检查组成。最后一次完整运行 45.87 秒，零失败/错误/跳过；所有被绑定来源及测试时源码前后不变。修复前 81 项及原固定 B runner 的 557 项另有独立收据，不混成产品验收数量。
- 保留全部 16 组定向 RED/GREEN 与失败证据。一次新 reader 合成夹具导入失败来自测试模块未注册到 `sys.modules`，修正夹具注册后通过；不是产品或现场运行结果。R1 新增 worker/reader 挂起两项，修复前均复现残留，修复后均通过，随后完整 83 项通过。
- 实际 `read_profile` 消费新的 ReaderControls 的定向检查使用原合成纯重建夹具；其扫描器与 typed-runtime 替身明确保留。此项证明接口兼容，不能证明当前设备的原生执行或真实研究能力。

本轮原生 worker/profile、模型、资料 HTTP、DNS、UI、音频和服务变更均未执行。测试的 Python 审计拒绝记录为空；OS 范围活动未测量，不能据此宣称整台电脑没有相关活动。七个保护身份只有既往保存基线，本轮没有刷新生产运行状态；未来实际入口必须重新逐项核验。

## 已记录的接口裁定

1. 未来原正常 SSRF 分支可能对 `raw.githubusercontent.com` 做受限 DNS；提案必须明确披露并取得该范围授权，不能称为完全无网络。准备期间仍为零 DNS。
2. B manifest 原字节不改，由新 root manifest 显式派生当前 profile 目录的 `import_path` 首项；其余位置保持原固定路径。绑定不符即拒绝。
3. 复用原 Deadline/PrivateIO 与当前 Owned，仅对 CIM `CreationFileTime` 和没有 TCP listener 的 profile 做明确兼容；不新增进程终止控制器。原时限及精确身份要求保持。
4. 父进程以原服务结果文件证明工作返回，以原 profile 结果文件证明清理已完成。后者在 310 秒内可见是保守充分条件：可能拒绝内部清理及时、封存稍晚出现的运行；不额外发放时间。
5. R1 修复按原 Owned 的 CIM、终止、等待与最终证明调用预留清理余量，并在启动、身份确认、每次等待前检查。常见两个已登记成员预留 132 秒、四个成员预留 214 秒；原 315 秒最大时限不变，但有效等待和 reader 启动窗口会提前关闭。这会增加保守失败，不能宣称完整保留了消费者可用的 275／310 秒窗口。异常进程树与 OS/I/O 故障仍可能失败，不承诺无条件清理成功。
6. 原 IF01 明确要求具体集成修复在运行前重新审查。本轮一次独审及一次修复已使用；原独审报告保持 NEEDS_FIXES，root 只登记修复测试通过，不冒充新的独立 PASS，也不复用旧哈希签发运行权限。

R1 的新增测试复用未修改的 `Owned.cleanup` 源码 AST 和原 `Deadline/PrivateIO`，只将 OS 进程效果和时钟设为合成调用。两类挂起场景均验证完整 10 秒终止准入、已登记成员消失、日志关闭、最终仍在原 315 秒内。此证据仍不是本机实际原生运行证明。

## 证据与下一步

证据根：`H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-root-entry-20261106`。

- 修复包 manifest：284 项，SHA-256 `2975e0f947be408baaa4222f8dd9fd4fbd1cb481adf005f38ea1bc4d8b91c3aa`。
- 当前运行输入 manifest：37 项，SHA-256 `6658149a128fe10c50f4b197a9a7cef8133bb16434e1ada4897b523def31bba8`；另由 B manifest 校验原 1,461 项依赖。
- 当前完整检查收据：`offline/review-r1-full-green/receipt.json`；逐阶段及修复复核：`verification/review-r1-fix-readback.json`。旧 227 项包完整保存于 `history/reviewed-83312d5`，没有覆盖失败。
- 准备审查检查点：commit `83312d5f9573ff9cce2a9e331ce70e84e483888c`，tag `ultimaagent-t2-e02-source13-root-entry-review-20261106`。
- 原独审报告：`review/independent-preparation-review.json`，SHA-256 `c3a9977b7374e36b4bbaba21b4e1d794af84520523174f70237f2aa5ffa4c042`。结论 NEEDS_FIXES；六项未裁定范围已逐项记入 `verification/root-review-disposition.json`，均未升级为实际证明。
- 具体单例提案：`execution-proposal.md`。实际分配、结果复核分配、release 仍为零，E01 round3 已消费的授权不得继承。

本次新增只读复核报告为 `review/independent-fixed-source-review.json`，SHA-256 `3a9e31a89858bfe083f028a7a66ca482da4ef50acdbb41303134c48bcec0d450`。复核重新核对 284 项包文件和 37 项运行输入，零差异；没有运行测试、进程、profile、模型、网络、UI、音频或服务操作。

反例是：HELLO 接近 origin 182 秒才到达时，父进程仅按约 132 秒清理余量判断仍可继续；随后两次各最多 15 秒的身份查询把余量降至约 103 秒，而清理加最终证明可能需要 127 秒。事后的余量检查无法补回已花掉的时间。若该次查询才发现解释器子进程，之前按已知成员数量计算还会低估清理范围。当前新增两项挂起测试使用立即出现的 HELLO 和不耗时的资格替身，因此没有覆盖此反例。

下一步的具体补修范围已写入 `docs/plans/jarvis-work-e02-source13-cleanup-handoff-fix-plan-20261106.md`：持续保留尚未完成的资格查询和预期角色成员余量，先补延迟 HELLO／慢资格查询／迟登记成员反例，再修最小接线并做必要独立准备复核。本次授权只有只读复核，未据此修改执行源码或扩大实跑权限。所有实际 profile、模型与结果复核分配仍为零。

远端同步仍保留此前自动审批 `blocked by policy` 阻断；本轮不重试或改用其他通道。本地提交/tag 与文档镜像状态分别记录，不宣称远端已同步。
