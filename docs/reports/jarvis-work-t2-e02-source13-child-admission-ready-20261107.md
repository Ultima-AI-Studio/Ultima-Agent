# E02子进程准入补修：离线与独立准备审查通过

原单wo-ultimaagent-20261101-0021 / T2，当前8B与产品269aca5。272项离线检查、独立准备审查及封存字节读回通过。用户call_42e3d2dd124f406cb3ccebd14a9b1c0f已授权审查通过后一例真实研究及一次结果复核，当前尚未签发/消费运行记录。

准备manifest ae432a96ae7ede18da792d89dfe75fc3d3d7887e51761508aa03ce3f2e255353（130成员）；独审 H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-child-admission-20261107-r1\review\independent-preparation-review.json，SHA256 32cded1fcfdb61b0706f93e7f63a984fb20ce8830e44fa161609c8b816042c76。

# 子进程准入最小补修：待独立准备审查

真实前例在clearance的Owned发现阶段失败。短暂PID的原生身份未落盘，其具体归属仍未证明。已确认的代码冲突是：actual child在领取clearance前调用admit→check_native_baseline→validate_protected_members→process_snapshot，后者生成PowerShell辅助进程，违背仅允许既定launcher/base的后代门。用实际admit调用链的受控OS观察回归获得RED：child-no-subprocess失败，其余16项通过；未改旧运行的根因结论。

最小补修只将native身份共同检查提取出来。check_native_baseline(child=True)用于actual/inert子端纯原生核验；父端默认完整核验及实际CLI前的完整核验不变。共享P4/P1、Owned、清理、原生模型transport、产品与入口均未改。authority、父时钟、源文件/模型哈希、证明时效、七成员精确绑定、clearance唯一消费均保留。

当前272项离线检查通过：原harness219（精确case ID与71函数保留）+新实际admit边界17+身份/transport边界10+入口26。首轮完整测试触及90秒，未产出JUnit/完成回执；只读进程快照确认当时无本例Python残留，该轮不计为RED或PASS。另一个新增fixture缺少scope.json造成17项setup失败，保留后补齐fixture。有效RED为1失败16通过，GREEN17通过。为保留原90秒离线上限，原测试按明确函数分为79与140两组，聚合case集合与旧219项完全一致，无跳过或遗漏。离线runner新增超时原始输出留存，实际275/310/315门不动。

原172/190包与实际失败/独审保持；1544输入绑定、9项无关工作区文件逐字核对。测试scratch仍保留本机；正式清单封存源码、快照、日志、JUnit、审计和回执，不以临时测试产物当真实交付。冷导入守卫及测试中的Python SSRF、稳定UUID4只用于离线，真实child未替换模型回答。

Review Focus：1 child是否仍能产生准入辅助进程；2父端parent/命令/CIM和七身份是否完整且在CLI前执行；3原生proof/authority/clock时效及唯一次clearance是否保留；4未知后代/PID复用/清理不确定是否仍失败关闭；5离线分组是否保留原全部case、原90秒上限和原实际时限。独审须逐项核对，不能用272项测试代替判断。

原短暂PID真实归属、真实8B事实质量、Rust DNS及实时清理只有后续单例能提供证据；准备没有这些信用。用户已授条件单例，审查PASS后直接执行，不重复询问。失败停止且保留所有原始记录。

实际执行提案：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-child-admission-20261107-r1\execution-proposal.md。新包仅修验收框架准入职责，未改产品。当前E02/T2仍未通过；准备PASS不增加研究信用。远端push仍受既有自动审批blocked by policy阻断，本次仅本地提交/tag与镜像。
