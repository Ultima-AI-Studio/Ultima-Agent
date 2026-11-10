# E03 source13 焦点与选区变化负例准备

> **For agentic workers:** Use superpowers:executing-plans inline. One whole-package independent preparation review after implementation; preserve the evidence workspace.

**Goal:** 在同候选三轮正例已通过、现有8B服务经用户手动恢复并只读核验后，准备一个包含焦点变化和选区变化两个场景的E03负例包，证明变化后拒绝写入。
**Architecture:** 复用现有Case.negative、WorkContextProvider及原生双窗口夹具；不改产品源码或自建执行器。负例入口绑定三轮原终态/独审/登记与新的运行环境观察，实际路径不启动Agent服务器或工作CLI、不调用模型；每个实际替换尝试前重新核对准入及期限。
**Tech Stack:** 既有Python、pytest、Win32适配、SHA-256及标准库；不加依赖。
**Spec:** docs/specs/jarvis-work-capability-contract-20261101.md R04/R05/R08、E03；docs/plans/jarvis-work-capability-delivery-plan-20261101.md T2及原工单。

## Global Constraints

候选269aca511d88412dbb9c15d23911138469a37aa2；仅qwen3-8b-uncensored，digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330，原生版本0.32.15。前三轮固定正例3/3保持，原terminal/环境FAIL不改写。用户手动启动的新Ollama PID5708与其他6原保护身份另行绑定，不声称原PID15264持续存活。产品默认/KWS/语音、全部旧失败不改。

本计划只释放离线准备、一次技术准备审查和本地文档检查点。实际负例及其结果复核均为0分配；没有release/actual目录，不可运行现场用例。旧15秒手动开始、20秒fixture、60秒proof、120秒authority等期限不放宽。负例product_cli_cap=0、model_requests=0、audio=0、case_cap=1、retry=false。人手点击开始后暂停输入的交接保持；只允许两个owned测试窗口发生预定焦点/选区控制变化，禁止文本替换和产物写入。

写域：本计划、新证据根e03-source13-negative-20261106、运行恢复证据根runtime-reconcile-20261106-after-round3、原工单/T2/current-run及原全局登记行、报告和文档镜像。候选工作树源码只读，父包只读。

## Review Focus

1. round3的case PASS与后续environment FAIL并存，只有明确的新恢复观察与新基线可解除新入口环境阻断；不得删除旧FAIL或借零推理省略保护检查。
2. 三轮资格必须为同候选、不同task、顺序递增且绑定各自terminal/review/registration；不由累计数或相同产物hash替代。新增一致重绑定的重复task/逆序时间及缺累计行反例，覆盖原PREP-M1。
3. 负例不能走原正例服务器/CLI路径，任何非零CLI、非空输出集或mutation.send必须失败；拒绝原因需来自真实产品目标校验。
4. 在焦点变化及选区变化后、每次替换尝试前都检查同一authority/proof时限；准入失败不能被当作预期目标拒绝而计PASS。
5. 捕获、改变、拒绝、后读回或释放失败均保留已观察部分及缺失原因，并执行owned清理/闭合审计；零变更不是未运行场景的PASS。

## Task 1: 绑定三轮与恢复后的基线

**Files:** code/acceptance_entry.py、code/source_candidate_guard.py；inputs/prior-round3三原件、inputs/runtime-reconciliation.json、runtime-manual-confirmation.json、runtime-user-approval.json和protected-baseline.json；新code/test_negative_predecessors.py及测试fixture。
**Interfaces:** predecessor_reviews(root)保留前两轮校验，扩展第三轮及三项有序绑定；verify_package/validate_release核对新负例scope、零CLI、运行恢复摘要和三项authority prior_reviews。

- [ ] 核对父包56封存与三轮原件；复制必要代码/输入，保留原保护快照；读取用户手动恢复及新的7身份基线。Expected:原件字节一致、无release/actual。
- [ ] 先写拒绝行为测试：第三轮事实/目标/文件/清理或链绑定不合格、漏依赖、重复task、逆序时间、缺累计行、恢复记录/基线不一致、旧正例scope及非零CLI cap。Expected:对父实现观察到新规则未生效的FAIL，禁止语法/导入错误冒充RED。
- [ ] 最小实现三轮资格及新环境绑定；保留两个实际独审schema，不改原收据。Expected:新增测试GREEN，拒绝发生于native/backend构造前。

## Task 2: 零推理原生拒写路径

**Files:** code/acceptance_backend.py、code/controller.py的Case.negative最小回调接线；code/test_acceptance_backend.py、test_acceptance_entry.py及新增test_negative_scenarios.py。
**Interfaces:** backend.product(revalidate,admit_cli)保留既有入口签名，但负例不提交CLI；Case.negative(baseline,before_attempt=...)在每个场景目标已改变后、调用replace_selection前执行准入回调。negative-evidence.json与pre-cleanup-effects.json是负例必须保留的结果文件。

- [ ] 先写新路径RED：两个场景必须实际覆盖、0CLI/0模型服务器、变化后每次准入、期限失效停止、预期拒绝与其他错误区分、sent marker/文件/文本改变拒绝、失败仍清理。用真实被测函数，仅在native/进程/网络边界使用离线替身。
- [ ] 复用Case.negative并增加最小before_attempt回调；入口固定e03-negative，终态hash绑定negative-evidence及effects，要求CLI恰为0，事实仍等待独审。Expected:GREEN，fake native只证明离线行为。
- [ ] 跑当前包完整离线套件及Python I/O guard。保留通用准入、手动开始、闭合审计、清理和来源校验；仅将正例专属提交假设改为负例的零调用要求，说明任何不再适用的父测试，原父包191项记录不改。Expected:全绿/guard零访问；不跑现场/模型/音频，不重复未改产品485/8回归。

## Task 3: 封存与准备独审

- [ ] 核对57源码/7依赖/1346SDK、原回归绑定和恢复快照；保存diff、测试命令与结果、原件provenance、未解决限制，封存manifest。Expected:候选未变，恢复观察仅是保存时点，实际前仍须fresh proof。
- [ ] 一次fresh独立全包准备审查；逐项裁定findings/declines，有Important只一次有界修正并RED/GREEN，不增新现场授权。
- [ ] 原单/状态/报告镜像与明确路径本地提交/tag；保留全部失败。此前启动服务及Git推送自动审批block均如实记录，不换通道绕过。实际负例提案最后提交，只包含一个由两个场景构成的负例和一次只读结果复核。

Ruling: 延用用户持续推进与既定inline方法直接完成离线技术准备；不重复询问实施方式，保留真实单例权限。代价：准备PASS不等于现场拒写通过。
Ruling: 永久保留证据根作为工作区，替代技能默认删除临时工作区；原历史不可删除。
Ruling: 本负例是目标变化拒写验证，复用原冻结原生产品guard方案，零推理不缩减需求；E01/E02真实8B任务另按原门执行。
