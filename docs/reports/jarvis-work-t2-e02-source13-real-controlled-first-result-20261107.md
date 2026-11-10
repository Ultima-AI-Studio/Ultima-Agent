# E02真实研究首例：启动阶段失败，独立复核确认

原工单wo-ultimaagent-20261101-0021 / T2，产品候选269aca511d88412dbb9c15d23911138469a37aa2，仅当前qwen3-8b-uncensored。用户授权call_b6e0642029e54a15a9ca4e3452940d0a的一次入口及一次结果复核均已完成；没有重跑。E02受控通过数仍0/3，E02/T2、后续阶段与Owner均未通过；E01同候选3/3及E03三正一负已通过记录保留。

## 本次实际发生了什么

- 运行号7530ef7f-ad0b-4151-bf2f-800c54ac9449；北京时间2026-11-07 00:57:22.3185703—00:57:36.6360901，外层耗时14.3149605秒，入口退出码1。
- 已通过当前8B摘要、七个保护身份与端口准入，并启动一组隔离server的Python启动器/原生解释器。研究CLI提交次数0；没有product-result.json或research.md。因此尚未形成可交付的真实8B研究，也没有可以逐条复核的研究事实。
- 原始terminal与root-outcome均为FAIL；first_failure为clearance original discovery: Owned discovery ambiguity。首次研究调用之前，进程核验遇到PID27096的QueryFullProcessImageNameW错误31；精确PID复查时已消失，原快照却仍有其后代PID38020，故保留未知身份并拒绝继续。
- 清理结果原样保留FAIL。已登记的启动器25540、原生解释器34368及仅观察的conhost27788在清理记录中已不存在，18799关闭；这不能消除未确认后代造成的清理失败。
- 原始application_native_POST_attempts、actual_native_start_count均为null，未擅改为0。未采集全系统网络或连续存活证据。14.3秒结束不等于时限门通过，root witness eligible=false。

## 保护与独立复核

运行前后boundary字节相同，七个原生身份一致；后续只读快照再次确认原生创建时间、exe、CIM身份、parent及命令摘要一致，Ollama端口11434仍属于PID5708，本例已确认身份均无残留。后来观测到PID38020对应的Codex node_repl.exe创建于本例结束之后，属于新的PID实例，未获得本例清理权，未被结束。后续观察不追改原清理FAIL，也不声称连续监测。

独立报告：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-real-controlled-preparation-20261107-r1\review\independent-result-review.json，SHA256 0b21020dc84468c6fe93366756826c6c4e911bd38a10b30fd79d3ae1e9377d98，结论FAIL_CONFIRMED。审查实际产物与证据，不另跑测试或模型；结果信用为false。

结果manifest：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-real-controlled-preparation-20261107-r1\review\result-inputs\result-manifest.json，SHA256 3620d929324ef1b496e407e655e991852bb077862909efc58216e7e1c63908c0；准备190成员、依赖1544成员、原失败准备172成员及9项无关工作区文件读回均保持原字节。原始运行记录与独审分别保留，旧准备PASS不替代本次实际FAIL。结果登记：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-real-controlled-preparation-20261107-r1\review\result-registration.json。

## 下一步及边界

下一步应处理验收框架的子进程准入/观察顺序。静态源码中，actual child在consume_clearance前调用admit→check_native_baseline→validate_protected_members→process_snapshot，后者会创建PowerShell查询；父端Owned又会拒绝原生解释器下面未登记的后代。该路径是需定点验证的设计冲突；因为本例没有保存短暂PID27096的完整身份，不能断言它就是这条PowerShell查询，也不能将问题归因于模型、音频或用户操作。

具体恢复提案见H:\UltimaAI\UltimaAgent\docs\plans\jarvis-work-e02-source13-child-admission-recovery-proposal-20261107.md。提案不修改本封存包、不签发新实际调用；后续只能在新隔离候选补修，保持原门和全部失败。一次实跑与一次结果复核额度均0，不复用本授权。

执行端：当前root主会话；独审独立上下文。环境：原Windows、当前8B、本地受控四来源；无UI、音频或生产服务操作。只清理本例已确认的新身份；未知身份未获终止权。远端push仍受此前自动审批blocked by policy阻断，本次不重试、不绕行；仅本地提交/tag及UltimaDocs逐字镜像。
