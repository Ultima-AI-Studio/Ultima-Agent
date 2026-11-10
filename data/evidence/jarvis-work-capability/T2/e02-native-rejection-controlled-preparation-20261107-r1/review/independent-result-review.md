# E02 首个实际结果独立复核

结论：**FAIL_CONFIRMED**，接受信用 **0**。本审查不授权任何再次实际运行，retry=0；本例与本次结果复核额度均已消费。

候选 d860b2ab4e4d9974e33c96472e4ea15abb807280；run 72d7d71b-39a9-455a-b0b4-8823b3f24c00。独审 /root/review_e02_native_rejection_actual_result，仅只读文件和源码，未运行测试、目标导入、模型、网络、进程检查或服务操作。

独立重算：结果 manifest 56/56、actual seal 31/31、准备 manifest 159/159、源码 75/75、输入 1590/1590、准入固定输入 1603/1603，差异均为 0。结果 manifest SHA256 为 9cc9e1c9c38a5f23b9e5a0d72b52bd2558a720c99abea8b11148abde483523d6。

- 授权与消费：明确用户分配、120秒TTL内消费、ledger单次、固定解释器和唯一entry一致。模型名及digest与固定8B一致，未做新的运行验证。
- 事实、引用、原题覆盖：均未通过。公开产品/服务 failed，错误 Invalid native research response，明确“本次研究未交付。”无可审查的最终研究文档。search1/GET4仅证明取材；6页confirmed、5页visible和S1/S2/S3资格不能替代覆盖，S4未inspect。
- 写入与ACK：write0、ACK未确认、research.md0、artifacts和写入效果为空。complete=false、END=false，没有完整runtime接受证据。
- 时限：entry观测耗时70.624772秒，未增加原预算；但root witness eligible=false、observation_error=ValueError，timing_eligibility=UNOBSERVED_NEVER_TIMED_PASS，不授予及时成功信用。
- 清理：封存原cleanup PASS，四个登记Python与两个仅观察conhost身份均消失；后续封存观察再次证实六身份缺席、18799无监听者。child准入、消费身份、argv与run时钟一致。该结论针对保存的观察时点。
- 保护：七个PID/创建时间/exe在准入、前后边界及closeout观察一致，前后边界原字节相同。不能声称生产连续可用或连续监测。

原生拒绝：5879字节v4诊断SHA256 6665c1d8a43fca043ac9f2e525b5d7f70136b1ad59787b293393be218cc35f79与公开摘要及export一致。第7代、receipt20、HTTP200、请求33395字节SHA bc2299bb736f1c1b425c4289f454c47da1bb97d2621624f9a10ce4f03e74bb58，在last_http与native_response绑定相同。受限字段 reason=done_reason、done=true、done_reason=length、eval_count=max_tokens=2048、prompt_eval_count=8888、content_chars=3798；响应9663字节SHA c03d2a9b4e4f7cef38e562c067aade3c5eff9c778cc2803e2b7a37917b9a4597。运行绑定哈希已独立重算，与产品/服务请求身份吻合。

静态检查确认 agent_server 在 checked_native_response 拒绝时捕获受限投影，发生在内部envelope解析前；work_research 首个命中谓词为 done_reason != stop；diagnostics 将generation、receipt、请求SHA和响应SHA/字节数绑定到末次transport。adapter核对公开摘要、请求身份后导出。只确认本例首个外层拒绝条件；完整请求/响应正文未封存，不能独立从完整正文重算其SHA、推断内部JSON、事实内容或token分配，更不能倒推N17同因。

准备manifest与PASS独审摘要保持原值；旧失败及离线346+6不转为实际接受信用。E02/T2/Owner不因此通过，无自动修复、重试或追加运行。
