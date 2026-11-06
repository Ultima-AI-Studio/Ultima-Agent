# E03 source13 round3 准备结果

原工单wo-ultimaagent-20261101-0021；执行端Codex主线程，原目标已由用户恢复active。当前候选269aca511d88412dbb9c15d23911138469a37aa2，当前社区8B及digest保持；前两轮各自实际与独立结果PASS，连续正例2/3、负例尚未通过，E03整组/T2仍未通过。

当前状态：第三轮准备包已封存，191项离线入口检查、纯文件校验及独立准备审查均PASS。独审有1项非阻断测试覆盖建议，已按Minor保留；没有第三轮actual或实跑authority，没有新的模型、UI或音频操作。

## 入口变化与证据

计划：docs/plans/jarvis-work-e03-source13-round3-plan-20261106.md。新准备根：data/evidence/jarvis-work-capability/T2/e03-source13-round3-20261106。基包为同候选已实际通过的round2，旧包与原始收据保持。

入口固定e03-round3，保留round1原检查，并加入round2资格和累计两轮链核验。round1独审记录使用work_cli_launches/automatic_retry_recorded，round2使用work_cli_count及authority/limits无重试证据；新入口按实际格式读取，未改写原收据。authority必须精确绑定按round1、round2顺序排列的终态、独审和登记哈希。累计登记中的case、candidate、task_id、终态与独审哈希、完成时间和前轮registration必须互相对应；不由两条PASS字样推断连续两轮成立。

产品执行代码未改。11个父包Python模块字节一致，涉及执行后端、controller、夹具及适配；5个父文件有变更，分别为入口、guard的manifest位置和3个测试模块，新增1个测试模块。固定样本、完整选区、副窗口、手动点击与持续提示、清理边界保持；15秒开始、20秒夹具、60秒proof、120秒准入及CLI300/SDK1800/controller315秒限制未调整。

新增38项检查：第二轮旧候选/错误轮次/未独审/事实或完成声明失败/终态异常、缺依赖、累计链重复或错绑、任务与时间不一致、漏/错第二authority绑定等，均在native构造前拒绝。保留153项既有行为，按轮次与前置材料调整测试，合计191项。

首次RED为32FAIL/6PASS，其中一项构造spy返回None，在漏掉第二绑定时出现AttributeError；修正测试spy为返回已有fake Backend后、产品入口尚未改动时再次RED，仍32FAIL/6PASS且errors0，缺失拒绝明确呈现DID NOT RAISE。随后最小实现：GREEN38PASS，完整191PASS/15.40秒。四次运行及source-before/after、XML、日志均保存；I/O guard允许0、拒绝0，无模型/音频。fake native与Python拦截不代表全机原生I/O监测。

静态读回17个Python模块，父包51封存文件、六份前轮原件/副本、57源码/7依赖/1346SDK哈希均一致。原485项工作回归及8项兼容测试的收据和源码绑定保持，本次没有重新运行产品回归；其既有默认SDK home/真实语义路由限制继续保留。保存的保护基线仅用于后续准入比较，本次离线准备没有查询现场服务或声明当前语音状态。

56文件manifest SHA-256：968f69a1bb4a5f72ef0776ec4c234c20e9af79d46d7236de01d271b637776a21。运行manifest SHA-256：957669cb3463eab549df80f0b8fc6345c244daa2f613925abe8622d0aab3d9d3。入口纯--verify已用两轮真实只读输入通过；该路径不创建native backend。

## 独立审查

`/root/review_e03_source13_round3_entry`完成一次只读全包准备审查，verdict PASS；56项封存、父包51项、六份前轮来源副本、57源码/7依赖/1346SDK及191测试证据核对一致。完整收据`independent-preparation-review.json`，SHA-256 `53b55db7a3472747567c47237f6bcd8982ca5b7524c739faa10eff15f182ff73`。

Critical/Important均0，Minor1：`code/test_round3_predecessors.py:85-86`的同task/倒序时间样本只改累计登记行，实际通过“行与凭据不匹配”分支被拒绝，没有直接覆盖同时重新绑定所有相关hash的重复task/倒序terminal；另建议补一例缺失累计行。独审确认实际不同task及时间顺序检查存在，本次未发现放行错误。控制器按实际影响维持Minor、不阻断，并保留到未来相关测试调整；不为提升诊断覆盖修改已封存候选或重复实跑。

控制器逐项接受九项不予判定范围，记录在`verification/review-disposition.json`及`review-completion-ledger.md`。原两轮事实只作资格凭据，未重新花费结果复核；第三轮真实窗口/事实/文件/清理、现场模型/保护状态、语音/Owner、全机I/O、485/8新执行及原兼容边界、完整E03、E01/E02/T2后续、远端同步均仍需各自证据。此次准备PASS不增加验收分。

## 范围裁定与后续

依原技术门和持续目标，准备及一次全包技术审查在已授权范围内继续；本计划没有复用前两轮已经耗尽的实际与结果复核分配。既有证据根作为隔离plan workspace永久保留，代价为磁盘空间；不删除历史。未变产品的485/8回归采用原执行及当前哈希绑定，代价是不能称为本次新执行。

下一实际提案仅一次第三轮和一次只读独立结果复核，当前8B、一次CLI、失败不重试。按钮出现后15秒内只点一次开始，随后暂停鼠标、键盘与切窗直到结束；运行前仍需新鲜候选、7保护身份及模型证明。第三轮实际独审PASS后还需E03负例、同候选E01、当前8B E02，满足T2出口后才进入T3—T5/Owner。

本次round3准备包尚未推送。提交前发现另一执行方已新增两次仅修改北极星看板的提交（5f287c86、b254aed9），本轮保留。GitHub只读核对确认项目仓库round2结果tag已可访问，其报告blob与本地一致；UltimaDocs同名tag仍返回404。因此旧项目成果已有外部同步，镜像及本次新准备包仍分开记为未同步。此前本轮执行方的推送组合命令遭自动审批blocked by policy拒绝，本轮未重试或绕过；读回见verification/external-state-reconciliation.json。本地检查点tag为`ultimaagent-t2-e03-source13-round3-prep-20261106`；项目及镜像commit/tag读回另记verification/local-checkpoint.json。
