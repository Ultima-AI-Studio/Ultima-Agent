# E02 代码事实生成候选：单例结果与独立复核

原工单 wo-ultimaagent-20261101-0021 / T2；冻结候选 d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b。本次唯一当前 8B 受控研究实际生成并写入 research.md，读回和 ACK 成立；独立结论 **FAIL_CONFIRMED**，因为事实引用和完整原题覆盖失败。E02 仍 0/3，T2/Owner 未通过。本报告保留真实产物，不把内容失败误写成“未生成文件”。

## 已完成的实际链路

用户问题 call_c910dd9e4819410492607baac9ed63bf 分配 actual1 / result review1 / retry0。run 1496a844-668d-407a-a91b-89be246ba05b，北京时间 2026-11-08T12:11:46.176024+08:00 至 2026-11-08T12:13:01.717384+08:00；外层耗时 75.541365 秒。原入口仅调用一次、CLI一次；应用原生 POST8、完成8。服务端实际生成启动总数未测量，保持 null。模型 qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。

第7次 writer HTTP 响应 done_reason=stop、eval_count=728，原输出上限2048；第8次 ACK stop、eval_count=31，阶段上限256。八次均 stop。本例没有出现上一例的 length/2048 截断；这只证明本例完成，不能从单例推断重复问题已稳定解决。

产品 status=succeeded；可信导出 complete/END/ack_admitted 均成立。实际报告分派1、文件写入1、接受副作用1。顶层两条 research_write 成功行分别是 SDK 摘要与带 call_id 的账本记录，不是两次写入；seq7、同一 dispatch、嵌套 file_call 与唯一 effect 一致。

- [实际生成的 research.md（事实验收未通过）](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-claim-generation-controlled-preparation-20261108-r1/actual/E02-controlled-1/outputs/1d0a6ed0-90c3-4a31-8d57-4d592bf1e5a4/research.md)，2458字节，3节9条事实；SHA256 ac34309cd889594ef4569020d1ac922290aba38fa8285e82748d549925785e0f。
- [独立逐事实复核](H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-claim-generation-controlled-preparation-20261108-r1/review/independent-result-review.md)；JSON SHA256 065d3f6fa910976672f01c02850d0c52f1f34567ccaa295451e427efbe0bb9af，Markdown SHA256 fcbb6812680107f7e64597cf5ba35b8da821cf6c39df5469c62ca05ffdaeb84d。

## 内容失败的确证

九条陈述中仅第7条 Date.now 查询开始时间的局部事实及引用通过；其余8条存在错引、所引范围不足或实现上下文遗漏。这不等同于“八条全是假话”：有些结论在完整源码中可得到支持，但本报告指定的引用不能支持它们。

| 陈述 | 独审确证问题 |
| --- | --- |
| 1、2 | 把模型名称和双击 Fn 等不同位置内容合并到较窄的单一证据卡；所引范围不足。 |
| 3、5、6 | 分别把 unified-agent 工具调用、日志、OpenJarvis 行为挂到 README 或 AgentManager TODO 的无关证据卡。 |
| 4 | TODO确实存在，但据此描述 Gemini 仍待未来接入，遗漏同版本 AgentManager L48–51 已构造 GeminiProvider 的代码。 |
| 8、9 | 单处日志调用被扩成初始化与查询全过程的广泛结论，并重复占用正文。 |

原题要求任务架构与现有开源接入，产物没有连贯说明 AgentManager、provider、UnifiedAgent、ToolRegistry 的执行关系与回退路径，也没有正确区分 Jarvis.ceo 参考项目与现有 OpenJarvis 执行底座。不能从本资料断言 Jarvis.ceo 本身接入了 OpenJarvis。

search1/GET4；inspect6的分布为 S1四页（26–49、53–76、92–115、121–144）、S2一页（20–43）、S3一页（25–48），S4 inspect0。S4下载成功不等于实际阅读；目录导航提示不是事实证据。三来源只满足写入最低资格，不满足原题覆盖。本次仍为固定受控corpus验证，不代替真实互联网搜索验收。

## 原约束、时限与保护

原预算 CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒；context16384；输出最多2048，较小阶段上限保持。没有重试、换模型、加预算或修改产品默认值，没有UI、音频、生产服务操作。

原terminal的 timing_eligibility=UNOBSERVED_NEVER_TIMED_PASS 和 PENDING_ROOT_INDEPENDENT_REVIEW 原样保留，不改封存终态。独审使用绑定本run、terminal哈希、seal及38成员的外层 root witness：eligible=true，closed/cleanup/pins/protected/readback均true；最终运行事件及74.2462801秒的root观测处在原截止内。原时限证据成立，不能只凭75.54秒墙钟得出此结论。

清理PASS：本例六个身份均退出、18799端口关闭、日志闭合；原边界及事后保存观测点七个保护身份相符。上述结论仅覆盖保存的观测点，不保证持续存活或报告时实时状态。

## 登记与下一步

本次一例及一次结果独审已全部消费，剩余0，不释放下一例。结果manifest ab388abe9d994ee56b985c14183d14e2af3530a499de4cfe116a8c1a2315dddf，67成员；394准备成员、78源码pin及1602输入保持，1004产品准备检查/350入口检查是既有离线准备，本次没有重跑或转为实际信用。旧失败及旧E01/E03历史保留，不将旧候选通过信用转移到当前候选。

下一步[具体提案](H:/UltimaAI/UltimaAgent/docs/plans/jarvis-work-e02-source-grounding-and-coverage-proposal-20261108.md)围绕逐来源证据表达与题目覆盖，先核对真实选页、证据卡和生成表达，再确定最小改动。现有提示已包含“精确锚点、TODO不是实现、区分项目、完整原题”等约束；不能只重复提示后宣布修好，也不能把schema合法当语义可信。提案未实施、未独审，没有新的产品或实跑授权。

结果与本提案镜像至 UltimaDocs；本地提交/tag和逐文件读回见 verification/result-publication-readback.json、result-final-readback.json。result-source-analysis.json是封存后根controller只读补充，未加入原67成员manifest，另随本次发布保留。远端push此前被自动审批以blocked by policy拒绝；本轮不重试或换通道，本地归档不等于远端同步。

证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-claim-generation-controlled-preparation-20261108-r1。
