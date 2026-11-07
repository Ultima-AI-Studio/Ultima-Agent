# E02 单次实际结果独立复核

结论：**FAIL_CONFIRMED**。原单 wo-ultimaagent-20261101-0021 / T2；reviewer=root-independent。

候选 `ee1bef61f04169c64978538dbc4ba799ef7be6c0`；run_id `91406fa9-5952-4e3a-99af-a94c8857c8d3`。
结果清单 SHA256 `8d1b3920f1b15e3deec3c0b380eeb9476a2701454a0aa4f7f8c34fe79c43641e`。

结果60/60、准备149/149、输入1567、候选源码68、actual seal31全部逐项哈希一致；raw与CLI相同且解析为product，service/product与runtime输入身份一致；诊断canonical bytes、binding摘要及final文本摘要吻合。未借主会话摘要代替原始文件。

实际入口1次，35.6828925秒，retry0；search1/GET4/inspect6/write0/ACK0，native POST7且completed7。没有research.md或成果artifact、ACK、非空immutable runtime proof；原产品返回“本次任务未完成。”和Missing nonempty immutable runtime proof，root FAIL。原始final声称“已整理…保存为research.md”，与写入事实冲突，不能当交付。没有文档可逐事实和引用审计，原题交付覆盖不通过；不能把缺产物记成事实正确率通过。

6158字节v3诊断直接确认final_before_write；6页均confirmed、visible；S1读取26/50/74/98/122，S2读取20，仅S1/S2有合格cards。S3统一Agent与S4 OpenJarvis执行底座虽GET可用，却没有inspect。剩余247.183454秒且write_admission_open=true只表示时间准入，不表示满足三来源门。

冻结源码agent_server.py:570-615和work_research.py:788-817重建表明：第6次读取后inspect分支消失，eligible需要至少3个不同有cards来源，当前write分支不存在，剩下自由文本final_answer，输出上限<=256。该自由文本允许不真实完成话术，外层交付验证正确fail-closed。WorkInspectTool.parameters（work_tools.py:675-692）为固定S1..S5，缺少剩余读取预算与未覆盖来源的动态约束。这里的相位/schema/256判断属于源码重建，并非完整请求实体抓包。

最后HTTP回执generation7/index20/chat/status200/validated=true，request_bytes21600，SHA256 `b163dd845ad4dd2c5d274eb7710566cd4ec933f43d16299f240722df5c6f412f`。它仅证明本次该响应状态与验证结果。旧N11 eligible S1/S2/S3，原生日志有2048 tokens和HTTP500；本次final-only相位不能证明较复杂写入schema/2048相位已恢复，也不能据此宣布历史500根因修复。

原数量上限未超，原模型、四来源和预算保持；但root witness eligible=false、terminal_sha256=null及UNOBSERVED_NEVER_TIMED_PASS不得升级为限时交付PASS。原清理回执PASS、6个本例身份缺席、端口关闭、日志关闭；boundary前后相同，sealed readonly-closeout在09:18:37.723031至09:18:40.152890 UTC记录7个保护身份相同。本reviewer没有查询任何进程，不声称连续存活或事后升级清理。

已核对封存首次错误：validate_failure_diagnostic(packet)参数错误导致TypeError，保存seal-attempt1.py与failure.json；finish_seal_allocated_result.py改用raw bytes和product/runtime绑定进行校验，排他写入后续封存文件。该修正发生在真实例结束后的封存环节；无第二次产品运行或证据覆盖。reviewer仅阅读脚本，不执行helper。

N12清单808与当前输入1568、N11清单2501、结果49、native补充4、旧依赖1563均哈希一致，旧清单及独审绑定一致；旧失败保全。339离线检查属于上轮，本次没有重跑或迁移验收信用。

仅建议另提读取预算与来源覆盖联动，以及证据不足时诚实拒绝的终态约束。不能降低三来源/事实/预算门，不能强写两来源，也不能为强写而关闭拒绝。历史写入相位兼容性需独立的新授权验证，本次不修产品、不重试。

实际额度1已消费、结果独审1已消费，剩余均0。acceptance_credit=0；E02/T2/Owner均NOT_PASSED。reviewer tests_run=0、model_calls=0、actual_runs=0、process_queries=0。仅写本JSON与本Markdown两文件。
