# E02 source13 原资料外层执行入口准备计划

> **For agentic workers:** 当前 root 内联执行，使用 executing-plans；全部入口代码准备完成后做一次独立准备审查。不得派发实现子代理。本计划不签发实际 profile、模型或结果复核额度。

**Goal:** 复用已有受保护进程管理和原资料 profile，补齐独立准入、实际退出观察、两次文件读回的外层接线，最终交付可审阅的单例零推理执行提案。

**Architecture:** 冻结产品候选及已审查 profile 保持原字节。外层父进程持有单次分配、最早时钟、原生身份与退出观察；worker 仅执行原 profile；全新 reader 执行原纯重建、typed replay 和外部读回。现有 Owned 管理启动/清理；只增加身份与观察结果到既定 RootControls 接口的适配，不新增产品 Agent 循环或原生进程控制器。

**Tech Stack:** 现有 Windows/Python 3.13、OpenJarvis、pytest、项目受保护进程 helper；不安装依赖。证据根 E=`data/evidence/jarvis-work-capability/T2/e02-source13-root-entry-20261106`。

## 固定前置与范围

- 原单 wo-ultimaagent-20261101-0021，T2，持续目标 active。候选269aca511d88412dbb9c15d23911138469a37aa2；仅当前 qwen3-8b-uncensored，摘要6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。E01固定3/3、E03三正例和一负例通过；本准备不重跑这些案例。
- B=`T2/e02-source13-profile-binding-20261106`。B封存129项，manifest ec15aa82ee9ef72ff366c33eb997307e8151a97957eaa6d3f8544dc555424382；独审94eb752925b1f1644d1ab91f5762a9d8e3a2daba3d7f3a5b0fca1b22a84d40ce，root准备门PASS。557项属于 named run-stage.py；原固定 run_checks.py 另需一次明确收据。
- 原题774字节及d359dcde318278823ad1e9c48b70c604f0d614152c0b0ec26b88ca310821f61e、原四来源 corpus 9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002、人设、扫描器、SDK写入、END/ACK、输出research.md要求不变。零推理 profile 的协议脚本不构成8B研究能力。
- 保留全部旧失败、六轮旧profile修订、原预算耗尽和所有旧准备状态。允许一轮新外层接线实现及最多一次新差异审查修正，不修改旧profile算法、产品源码或历史记录；发现旧算法缺陷另记具体阻断，不借本任务开启旧第七轮。
- 当前仅文档、适配代码和离线契约；actual profile、真实产品CLI、模型、11434/资料HTTP/DNS、UI/音频、服务变更和实际结果复核均0。具体实际用例必须另有用户的一次分配，原E01额度不得继承。

## 已有组件与必要适配

| 能力 | 复用源 | 本次差异与限制 |
|---|---|---|
| 原资料执行/重建 | B/profile-preparation/profile.py及七方法adapter | 原字节不改；使用既定admit/readback签名 |
| 准确身份、Owned启动/清理 | E01 round3 code/controller.py与preparation-support/acceptance_adapter.py | 使用当前7身份和原PID/FILETIME/实际exe/父PID/命令摘要检查；不调用E01入口或模型检查函数 |
| 最早时钟与有界I/O | 原inert-revision2入口与harness Deadline/PrivateIO的已有规则 | 原275工作、310清理、315最终截止；不复用旧分配、5身份比较或旧RootInvocation终态格式 |
| 退出码观察 | CPython subprocess.py Windows的保留句柄wait/poll机制、现有process_times | 需要实际worker/reader的已核验句柄，不能把venv启动器PID/退出或worker声明替代实际身份；仅只读观察适配，终止仍由既有Owned负责 |
| 文件与准入记录 | 已有strict JSON、独占创建、no_reparse、哈希和closed schema | 固定新目录、固定记录名；不接受worker指定路径或自行提供的“verified”标志 |
| 导入环境 | B manifest与实际固定Python布局 | B的package_root已指向当前包，但import_path首项仍为旧包目录；必须在新的root manifest中显式绑定派生路径，不能隐式继承或把旧manifest宣称为完整新启动路径 |

此排查采用现有开源和已有项目能力。新增部分是IF01/IF02B/IF02C要求的接口接线；不另造调度器、原生进程管理器、推理器或研究检索器。局部helper模块复用仍是可信代码机制，不宣称恶意Python或OS沙箱隔离。

## 运行结构与接口

1. 外层父进程的第一段可执行代码记录同机monotonic_ns。所有固定输入检查、分配消费、启动、清理、读回都继承这个origin；失败后没有新origin、第二次分配或自动重试。
2. 父进程读取固定root manifest、B准备门及未来独立review，检查未来用户授权记录；在启动worker前独占消费一个allocation。当前仅准备未签发模板，模板不得含可用的身份、签名或成功授权。
3. 用现有Owned启动隐藏worker。日志、握手和控制文件位于worker case之外；case必须空目录。父进程从Owned原生观察核对实际worker PID、FILETIME、exe、完整argv和父子关系，再持有同一实际进程的只读退出句柄。HELLO中的PID只是待比对值，不能建立身份。
4. 父进程独占封存worker admission。`worker_executable`按profile既有接口表示固定venv解释器调用角色；实际native exe单独来自父进程句柄/identity证据。两者不强制错误等同，也不能互相替代。
5. worker的具体RootControls.admit从固定的root-owned封闭记录构建IF01原有exact keys。核对分配已消费、当前B/root输入、7身份前置、模型摘要、原资料hash、SSRF实际正常分支与最早时钟；仅一次。无SDK/client的成功默认路径。
6. worker在设置固定cwd/派生sys.path并清除注入环境后调用原`run_profile(folder,pins,controls)`。其结果只称candidate；失败保留原first/failure-summary等证据。父进程观察实际退出、工作/清理截止与保护身份；worker自报时间和退出只能作为被核对对象。
7. 父进程确认worker已退出后启动干净reader。reader_root为空、canonical、非reparse，并与case及worker/control证据根互不包含。reader只读原case，副作用限定自己的scratch和root指定结果文件；不复用worker的sys.modules或SDK client。
8. reader的RootControls.readback独立读回root原allocation/admission和父进程退出/保护记录，使用其自己的同机时钟核对原315截止。两个调用返回同一组run/nonce/worker及五个文件hash，只有observed_at_ns可以前进；不再消费额度，不从first取origin、退出码或记录路径。
9. 原`read_profile`执行纯重建、typed replay、SDK文件外部读回及最终不可变检查。父进程在reader实际退出后复核两次观察、返回值、文件/输入hash、清理和7保护身份，并在原315秒内关闭最终门。只有外层最终候选结果可送独立结果复核，不能直接计E02。

IF01 admission/readback exact schema保持原定义；不要添加worker派生的pins.worker_admission或改方法签名。新root manifest明确列出base profile manifest hash、派生import_path规则、允许注入reader_root/worker_evidence_roots/ssrf_backend和全部控制源码hash；派生pins由固定root实现产生，不读取worker选择。其正确性是本轮独审内容，B旧manifest原字节及其旧声明不改。

## Task 1：固定检查入口与兼容性输入

**Files:** E/plan.md、E/inputs/{source-bindings.json,preparation-scope.json}、E/verification/；B/code下仅原固定runner独占新建的一次离线目录。

- [ ] 保存B准备门/独审/checkpoint、E01/E03登记、IF01/IF02B/IF02C、原deadline与当前Owned/7身份helper、固定Python标准库源码的路径与hash。所有来源只读，不导入产品或查询服务。
- [ ] 一次执行B当前已独审的`profile-preparation/run_checks.py --contracts`，使用固定Python `-I -B -X utf8`、无自动插件、隔离临时目录。它只启动已审查的pytest子进程，不提供profile/runtime入口。Expected：557精确标识/零失败错误跳过/输入包前后无漂移。保留原输出与退出；失败即停止该runner序列，不重试。
- [ ] 静态核对worker/reader所需pins、cwd、env、元数据模拟与原实际来源的区分。将旧import_path首项、新派生规则、venv调用角色和实际native身份列为下一步必测接口，不能登记“已实际启动兼容”。

## Task 2：最小外层接线与离线契约

**Files:** E/code/{entry.py,controls.py,native_observation.py,package_io.py,test_controls.py,test_entry.py,test_native_observation.py,run_checks.py}，E/inputs及verification。只在E新增；B/旧profile/产品/SDK不改。

**Interfaces:** `WorkerControls.admit(folder,pins)`、`ReaderControls.readback(folder,first)`；root调用既有`run_profile`/`read_profile`。新native适配只接受已核验的Owned身份及root固定记录，保持句柄到退出观察；不得增加任意PID终止或后台扫描入口。

- [ ] 先用合成时钟、进程句柄和文件夹写明确行为RED：无分配拒绝、重复消费拒绝、不同候选/输入/实际身份拒绝、过期时钟拒绝、5代替7身份拒绝、worker声明退出拒绝。
- [ ] 补齐父进程单次消费、实际身份握手、固定worker/reader路由和root-owned控制记录；所有不完整观察默认失败。清理只对既有Owned已登记身份，父PID关系单独不授予终止权。
- [ ] 用合成进程/句柄证明启动器成功但worker失败、身份重用、句柄未signaled却有退出值、晚于截止、第二次readback漂移、reader退出失败等均不通过。用真实profile consumer函数和原schema检查派生pins及两次readback；不用纯自制consumer替代。
- [ ] 导入路径派生必须精确列明并先检验固定stdlib/site-packages来源。SDK/client在admit前不得暴露；测试模拟环境恢复、干净reader、case不可变、结果文件不进入worker闭包及当前正常SSRF分支。
- [ ] 跑必要定向GREEN和一次完整新入口离线检查；保留所有失败、命令、JUnit、执行前后源码hash。不得启动实际worker/profile/reader/native观察或模型来代替离线契约。

## Task 3：独审、检查点和具体单例提案

**Files:** E/manifest.json、E/review/、E/execution-proposal.md、项目报告及UltimaDocs镜像、原工单状态。

- [ ] 封存当前输入、代码与测试证据；一次只读独立准备审查，明确旧source10/inert结论不能替代当前集成。重点审查派生import_path、句柄/角色映射、首个clock、7身份、双读回以及原315秒内最终退出。
- [ ] 仅新接线差异允许一次限定修正；原profile算法问题记录另行处理，旧修复预算不重开。
- [ ] 独审和root处置通过后本地提交/tag、镜像逐字读回，再给用户具体一次零推理profile及一次只读结果复核提案。提案列原题/四来源、唯一实际调用、原时限、保护进程、无模型/网络/UI/音频、失败不重试和清理范围。
- [ ] 仅用户分配到达后才签发实际authority。即使该零推理单例通过，也不计8B研究三轮或真实联网来源事实验收；E02/T2/T3—T5/Owner原门保留。

## 当前裁定与停止条件

用户持续推进原目标的授权覆盖此明确离线准备，沿用root内联实现及最终独审。实际运行与结果复核必须有新分配。现有证据长期保存，不执行skill的默认清理；不重复无关产品回归。本计划与B独审未裁定项衔接，不把准备通过解释为实际集成通过。

若固定runner失败、需要改变旧profile算法、不能用已有进程/标准库能力证明实际worker退出、或无法保持原时限，先保存具体缺口并停止相应序列；不可删断言、放宽时限、换模型、使用旧authority或脚本代写研究答案来填补。远端push已有自动审批blocked by policy阻断，保持本地检查点，不换通道绕过。
