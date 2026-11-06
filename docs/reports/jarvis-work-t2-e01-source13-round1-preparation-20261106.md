# 同候选E01 round1文件交付回归准备

工单wo-ultimaagent-20261101-0021；产品候选269aca511d88412dbb9c15d23911138469a37aa2，模型qwen3-8b-uncensored/digest6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。当前E03三正例及一负例已实际通过并独审登记；T2仍未通过。本报告仅交付下一步E01 round1准备，真实E01结果尚不存在。

本包208项隔离离线检查全部PASS，零失败/错误/跳过；进程与socket检查记录allowed0/denied0/open0。89文件manifest为a19bbdb66b68eca4d2d5d8642dba781dccb1659341d38d1cb881deb0a925518a。独立准备审查PASS，0待修项；尚无E01 release、authority、preflight或actual目录，真实CLI/产品模型/音频操作均0。

只修改验收接入程序。冻结产品、controller库及acceptance_adapter原字节保持；复用原有隔离Agent服务、OpenJarvis/工作CLI和文件校验。E01不启动测试窗口，不采集前台或选区，不带current-window/replace-selection/research参数，也无需用户点击开始按钮。固定材料来自候选内版本化acceptance-cases.json：项目代号松林、Markdown文档、截止日期2026年11月8日，固定文件summary.md。

入口先核对同候选E03三正例和负例的原terminal、独立review、登记及负例原证据。负例事实字段保留NOT_APPLICABLE，不伪造生成事实PASS。缺前置、混候选、失败复核、链或计数不一致以及未封存依赖均在native backend创建前拒绝。四份资格不代替E01实际验收。

一个E01请求只能提交一次CLI，失败不重试。仍用原60秒proof、120秒authority、CLI300秒/SDK1800秒/controller315秒；隔离服务就绪和最终监听身份检查之后，紧接CLI前再次检查原proof/authority，不刷新旧proof。固定可信output_root及服务生成的请求UUID目录，实际SDK工具写入记录、服务核验、外部文件打开读回、原始字节摘要和完整输出集合分别核对；收尾前再次收集副作用，清理本轮owned身份，事实终态继续等待独立复核。

离线替身只替换进程/native边界。真实入口、Case.effects、artifact_path、read_artifacts、mechanical、inventory和effects核对函数参与测试。覆盖过期准入不发CLI、缺文件、文件篡改、旧文件无本轮写入、哈希/请求身份矛盾、越界路径、额外产物、意外选区修改、模型不符、CLI退出非零，以及机械通过后文件又变化。离线合成文件不计为实际产品成果。

所有RED和中间失败永久保留：新增前置34项先失败再通过；旧接入尝试fixture启动被E01边界测试拒绝。适配父测试时发现旧case、目录和三项前置数量断言，按新E01一CLI及准确四份E03资格修正，全部失败日志/JSON/XML仍在verification。最终有效套件为e01-final-green3，共208项。父负例255项不混记为本轮新跑；6个不适用UI测试模块未纳入E01套件，逐模块映射见verification/test-scope-map.json；485/8产品回归仅校验历史绑定，未重跑。

57源码文件、7依赖文件、4组件共1346个SDK文件、候选HEAD和跟踪树已只读核验，父准备/结果141个封存文件未变。保护身份沿用用户手动恢复后的7身份基线，旧Ollama缺失和恢复记录保留；本次离线检查不证明运行服务持续健康，后续真实准入仍需重新取得有效proof。无fixture时通用effects中的windows_unknown不作窗口失败或现场观察证据；底层推理总数、断连后生成行为仍未知。

证据根：data/evidence/jarvis-work-capability/T2/e01-source13-round1-20261106。执行计划：docs/plans/jarvis-work-e01-source13-round1-plan-20261106.md。独立准备审查已通过；项目/镜像本地检查点完成后，只等待一例E01 round1及一次只读独立事实复核的具体分配。旧候选E01成功不计入本候选；其后仍须round2/round3与当前8B的E02，T2出口、T3—T5及Owner均未放行。

远端推送此前被自动审批以blocked by policy拦截，本轮未改通道重试，不声称远端已同步。

独立reviewer为/root/review_e01_source13_round1_entry，完整回执SHA 7793da71e425ace74f65a330e951f46c52bf261e4acef0dc32bba5192f9751ff；八项未裁定范围均作为限制接受，见verification/review-disposition.json，不扩为现场或T2通过。

北京时间13:19:53，root另做只读时点检查：七保护身份全部匹配、11434监听owner匹配、Ollama0.32.15及当前8B摘要匹配、官方语音ready/fresh且身份/run_id匹配。收据verification/preparation-runtime-readback.json；只查询进程/状态和模型元数据，未推理、未重启、未做音频功能验证，该记录不能代替下次准入proof。

本地tag为`ultimaagent-t2-e01-source13-round1-prep-20261106`；项目/镜像commit和逐字节读回以verification/local-checkpoint.json为准。执行提案在同证据根execution-proposal.md。此前E03负例结果已本地锚定：项目c4c21b5、镜像4163190，tag ultimaagent-t2-e03-source13-negative-result-20261106。当前产品候选保持269aca5；E01实际0/3，T2尚未通过。
