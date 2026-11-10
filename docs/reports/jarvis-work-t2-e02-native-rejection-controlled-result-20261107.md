# E02 原生拒绝诊断候选：唯一实际结果与独立复核

候选 d860b2ab4e4d9974e33c96472e4ea15abb807280 的唯一当前8B原题四来源研究结束，独立结果 **FAIL_CONFIRMED**。本次没有交付research.md，E02仍0/3，T2/Owner未通过。诊断已确证本例首个拒绝条件为done_reason=length，eval_count达到该请求2048 token上限；诊断成功不计交付通过。

## 结果与确证范围

公开回复“本次研究未交付。”，status=failed，error=Invalid native research response。search1/GET4成功；私有诊断确认六次读取，前五页visible=true，第六页confirmed=true但visible=false。S1/S2/S3有证据资格，读取起行依次26、50、74、98、20、25。上层tool_results的inspect0和私有诊断六读分别记录；三来源资格不证明原题覆盖。write0、ACK0、research.md0，没有成功runtime/END或事实、引用交付。

第7次/chat请求HTTP200，v4诊断记录reason=done_reason、done=true、done_reason=length、eval_count=max_tokens=2048、prompt_eval_count=8888、content_chars=3798。当前checked_native_response在done_reason必须为stop的分支拒绝该响应。请求和响应摘要与同一generation7、receipt20绑定；这确证本例触发的首个拒绝谓词，没有放宽或绕过原校验。

完整响应正文未保存；content_chars和token计数不能证明具体字段、思考、重复、转义或JSON结构消耗了额度，也不能证明后续校验一定通过。不能追认N17旧失败同因。下一步不凭空修补或截取正文，不接受length为成功。

## 时间、回执和保护

run 72d7d71b-39a9-455a-b0b4-8823b3f24c00；明确用户分配 call_92c748ab12e24ba7a135ebd26783263f。唯一entry1、work CLI1、retry0；北京时间2026-11-07T22:42:26.024231+08:00至2026-11-07T22:43:36.648009+08:00，外层70.624772秒。应用native POST7/完成7，服务端实际生成启动总数未测量。root witness的eligible=false、observation_error=ValueError；时限资格仍为UNOBSERVED_NEVER_TIMED_PASS，不能把耗时小于上限的失败用例升级成计时PASS。

请求33395字节，SHA256 bc2299bb736f1c1b425c4289f454c47da1bb97d2621624f9a10ce4f03e74bb58；响应接收9663字节，SHA256 c03d2a9b4e4f7cef38e562c067aade3c5eff9c778cc2803e2b7a37917b9a4597；这些摘要不等于保留了完整正文。失败诊断5879字节，SHA256 6665c1d8a43fca043ac9f2e525b5d7f70136b1ad59787b293393be218cc35f79，kind=v4，complete=false/END=false/acceptance_credit0。预算快照reads6/6、nativePOST7/8、剩213.123479秒，原预算未改变。

原cleanup PASS，登记的六个本例进程身份消失、18799关闭、日志关闭；之后只读核对再次确认本例身份不在。七个保护进程在运行边界及之后核对点身份相符，仅代表这些核对点，不宣称连续存活。本轮无UI、音频或生产服务操作，只用原qwen3-8b-uncensored摘要，未安装、下载或更换模型。

## 独立复核及接续

结果manifest 9cc9e1c9c38a5f23b9e5a0d72b52bd2558a720c99abea8b11148abde483523d6，56成员；独立结果复核SHA256 237b8f3c5c96a0ba9db599c0bdb0cddbe8d8cf68361c323c269fb7a2bf74c41e。无产物，事实、引用和原题覆盖未通过，接受信用0。当前准备346项及6项登记修复检查没有重跑或转为实际信用；旧候选E01/E03信用不迁移，全部旧失败保持。

本次实际1与独立结果复核1已消费，剩余0。后续提案：H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-writer-output-budget-alignment-proposal-20261107.md。先在新隔离候选中把实际输出预算传入共享写入阶段提示，保持原题和完整JSON、事实/引用、来源/证据、写入/ACK及原时限要求；离线验证和独审完成后，另行明确分配新单例。此有限提示对齐尚未证明能让当前8B在原预算内交付，本次不自动补修或重跑。

本地项目与UltimaDocs的commit/tag及逐字节读回见verification/result-publication-readback.json。此前Git push被自动审批以blocked by policy拒绝，本轮没有重试。证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-rejection-controlled-preparation-20261107-r1。
