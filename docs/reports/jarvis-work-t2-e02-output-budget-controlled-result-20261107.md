# E02 输出预算对齐候选：单例结果与独立复核

候选0421a54cab572be013c3f7ad562e86406bfe8e52的唯一当前8B原题四来源研究已结束，独立结论 **FAIL_CONFIRMED**。没有交付research.md，E02仍0/3，T2/Owner未通过。本例表明将实际输出预算写入共享提示仍未解决这次交付失败；不能据此认定8B在原预算下绝对不可能，也不能把离线通过转为产品验收。

## 本次完成与结果

离线补修只改三个生产文件与两个测试文件，产品927项（924产品+3兼容）、入口346项及计划/产品/入口独审已完成。入口曾有decision_id缺项造成33通过/1错误，失败保留后修正绑定，受影响34项通过；原函数AST与额度门不改。准备项目7ee6b08、镜像06b138c及冻结候选tag均保留。

用户call_8b7f20b59b8d4855b50e36d5ccc115ba明确分配actual1/结果独审1/retry0。唯一entry1/CLI1实际运行：北京时间2026-11-07T23:30:08.921499+08:00至2026-11-07T23:31:07.333170+08:00，外层58.412497秒。公开回复“本次研究未交付。”，status=failed，error=Invalid native research response；research.md0、write0、ACK0。

search1/GET4成功；私有记录六次确认读取、五页visible，S1起行26/50/74/98、S2起20、S3起25。三来源证据资格已打开写入，但不等于原题覆盖；S4未inspect。顶层tool_results的inspect0与私有六读按各自观察层保留，没有将二者混算。

## 原生响应及证据边界

第7次原生请求HTTP200，首个拒绝谓词reason=done_reason，记录done=true、done_reason=length、eval_count=max_tokens=2048、prompt_eval_count=8932、content_chars=4349。generation7/receipt20绑定同一请求/响应。请求33716字节，SHA256 8d7524386e508dd356b3a394fd389061b31512d40317e8e88ae2db942a9c1d53；响应计数10418字节，SHA256 8d250dd55788a69f0860530389cf7b0037afb4151dfe16bdf3de5687ce940e75。

失败诊断v4为5884字节，SHA256 3e1a4747653e31545bf3995e03e3ebe286670a0f13c36c988a478247e4533aaa；complete=false/END=false/acceptance_credit0。完整响应正文未封存，不能确定具体字段、重复、思考、转义或JSON结构如何耗尽额度；响应字节数/字符数不证明内容。该候选的提示预算对齐在本次没有产生交付，不能推断后续校验本来会通过。

父d860b2a的72d7d71b-39a9-455a-b0b4-8823b3f24c00同样第7响应length/2048，无文件。两例完整失败均保留；它们不是当前候选两次重试，也不构成通过率或延迟基准。相同读取起点可以从各自诊断核对，根因范围仅限各自确证的首个拒绝谓词。

## 清理、时间与保护

应用native POST7、完成7；服务端真实生成启动总数未测量。原时限和预算不变：CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/root275/cleanup310/seal315；context16384；阶段256/2048。只用原qwen3-8b-uncensored及原摘要，无14B、UI/音频或生产服务操作。

原cleanup PASS：六个本例身份不在、18799关闭、日志闭合，事后只读核对相符。七保护身份在保存的运行边界及事后核对点一致，不声称连续存活。root witness eligible=false、observation_error=ValueError，时限资格保持UNOBSERVED_NEVER_TIMED_PASS；58.4秒这个观测不能升级为时限成功。

结果manifest 3ebd6811702ed9eb09beb1c2d2efe418a491bd9f0078b9ea51db507c38b47f61（56成员），独立结果审查SHA256 9df10f28380162fce709007a9f7c244427edeea3399eda88bf296b9fdbbb017b。无产物，事实、引用及原题覆盖未通过，接受信用0。准备169成员、76源码、1594输入和旧实际seal保留；15个无关文件不变。

## 当前边界与建议顺序

本次已分配的唯一实际和唯一独立复核均完成，剩余0，失败后结束本次序列，没有重试或新产品修改。建议下一步先审查输出结构诊断与交付方式：以这两份固定失败为输入，列明当前2048输出契约的必须字段、现有受限记录能够回答及不能回答的问题，再提出足以定位截断位置的最小观察方案；需要新的产品修改或真实回执时另行明确范围。本结果不授权下一例，也不提出扩大token预算、更换8B或放宽原题验收。

本地项目/UltimaDocs提交、tag及读回由verification/result-publication-readback.json与result-final-readback.json记录。此前远端push被自动审批以blocked by policy拒绝，本轮未重试。证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-output-budget-controlled-preparation-20261107-r1。
