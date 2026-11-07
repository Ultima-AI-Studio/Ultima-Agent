# E02代码事实契约对齐：单例结果

原工单wo-ultimaagent-20261101-0021 / T2。用户call_99e734b15417466b92af3e8e85fdc3ea授权的补修、必要独审、一例当前8B原题四来源研究和一次只读独立结果复核均已完成。本例未通过，当前候选0/3；独审FAIL_CONFIRMED。E02/T2仍未通过，单例已结束，无重试和下一例分配。

## 实现与准备

候选1ecd75d061fd20e78c790c506cac76847f8e63bf，基于冻结a0d21eb。可信可见卡片按source/evidence/operation生成精确代码事实约束，generation和独立runtime replay重建相同schema/phase；不提前promotion、不改写模型回答。原research.md、事实/代码证据/重复来源、END/ACK/两次读回与时限门保留。新增28项产品回归，另3项使用官方b10488参考转换器核对兼容性；参考转换不代替实际原生采样证明。准备详情见jarvis-work-t2-e02-code-claim-preparation-20261107.md。

最终888项离线检查：产品594及官方转换3、harness238、绑定16/入口26/边界11。两项HTTP/junction离线排除不计通过，全部先前失败和中途测试失败保留。准备manifest b3ed0d8550943db83a0044f291e7990885959618865ea25adcfde16229858f28；独审PASS后完成项目ed8f430618fdb5935418f397c46dac28f38498af/镜像1307a2546c6db4ae9444be98f7c6d2304b2b556c本地提交、tag和读回，才签发唯一实际例。

## 实际结果

run dbd70fd7-ecb3-42d7-a6b0-097422e85f5f；UTC 2026-11-07T05:50:17.3074171+00:00 至 2026-11-07T05:51:24.0413633+00:00，外层66.7321982秒。原终态FAIL，CLI status=failed，error=HTTP Error 500: Internal Server Error。首次服务结果status=succeeded，error=None。CLI尝试1；服务保存的受控search成功1、GET成功4、可用来源4；export失败观察器记录应用native POST尝试5。原生总启动计数未测量，保存为None。

原byte-readback只读取CLI错误包，缺字段导致search/GET/available派生为0、nativePOST为null；这些不能解释为没有工作。原文件保持不变，补充只读核对service-result-readback.json（SHA88f8836827f7c82d2b01b91edcf45bfe29fb994f4413d53aaebe0ab520996db7）明确两层观察并用已封存服务/导出记录纠正汇总。原终态不升级。

有限writer诊断：null。

### 已证明的进展

本次确实写出research.md，2843字节，SHA256 f371c551b10ce3ffb443aba70b3bd3c7f8ca4e3f6d0652309eb35cf3ca11f0d9，与首次服务保存的artifact一致。服务status=succeeded、error=null、写入effect=completed，保存的受控search1/GET4、可用来源4、引用来源3；导出失败观察器native_POST_attempts=5。全局原生启动/推理次数未测量。这些是文件生成和保存观察的进展，不是完整交付通过。

### 协议失败与归因边界

install_trusted_exports先保存service-first-result，再调用export_completed；该链抛ValueError，保存trusted-export.failure.json后重抛，HTTP入口返回500。外层CLI错误包缺request/session，于是验收框架终态记录First result request/session mismatch。这个后续错误不能解释为原服务使用了错误身份。

具体失败函数、分支、拒绝值和异常文字均UNKNOWN_NOT_SAVED。export_completed包含runtime重放、结构/解码值验证和成员保存，现有证据不足以指认正则、PII、某字段或事实错误为导出原因。失败回执complete=false/END=false表示导出未成立，不证明服务内部从未到达END/ACK。所需runtime/views/replay/collection导出缺失，root witness不eligible，不能记时间门PASS或受控研究PASS。

### 逐事实与任务目标复核

独立报告SHA256 2837c364862c80d18000c6c8d5aafee934aaf62d667785202e445f1cf717992e，结论FAIL_CONFIRMED；14条事实全部核对。

- 5条获支持：文稿L19、L20、L25、L26、L27。L27源码仅记录query前50字符，不能扩大为完整query日志。
- 2条部分支持或有关键限制：L17所引行仅支持Logger.debug，不能同时支持Logger.info；L18所引TODO注释确实存在，但实际源码L48–51已有GeminiProvider分支，不能据此断言运行时只支持Ollama，也未验证provider运行能力。
- 7条不被所引行支持：README部分L6–11共6条，引到HTML、徽章或视频等无关行；L16引用singleton构造，无法支撑provider初始化与多provider的复合结论。部分事实在别处可能成立，不能替这份输出补引文。
- 题目覆盖不足：正文主要罗列日志和时间戳，没有充分梳理singleton/provider/tool-registry/query路由关系；第四份OpenJarvis资料虽已取得却未用于说明现有底座边界。不能从这些资料推断Jarvis.ceo已集成OpenJarvis。

因此，证据导出与研究事实/题目覆盖是两个独立阻塞项。只修HTTP500不能使现有文稿成为合格研究。

### 本轮出口与下一步目标

本次授权的一次运行与一次只读独立复核已用完，失败不重试；受控0/3、E02/T2/Owner NOT_PASSED。N8候选、文稿、原始失败和独审全部保留。P2计数层次问题已通过追加service-result-readback.json和纠正最终汇总处理，原终态和原byte-readback不改。

下一步应先围绕三项目标准备离线诊断和方案审查：保存安全且有限的导出失败原因；让结论与所引资料逐条对应；让研究覆盖原题中的架构及开源接入边界。继续当前8B，保持原时限、来源与验收要求；本轮没有实施这些新修复，也没有分配下一例。


已落盘的候选文稿（本例失败，不作为验收交付）：
- H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-code-claim-schema-20261107-r1\actual\E02-controlled-1\outputs\8163c3dc-dee1-42ae-9288-2c1e8af14387\research.md；SHA256 f371c551b10ce3ffb443aba70b3bd3c7f8ca4e3f6d0652309eb35cf3ca11f0d9

结果manifest 6974d755a36c5ec5bed02f931bc8270809909225958478d2b7d39cef311b32a0（45成员）；独审H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-code-claim-schema-20261107-r1\review\independent-result-review.json，SHA256 2837c364862c80d18000c6c8d5aafee934aaf62d667785202e445f1cf717992e。审查未运行新测试、产品或模型。

## 保护与边界

本例直接复用上一候选已独审的七身份基线，固定路径和SHA不变。本轮准备及实际前后只读核验现有身份；Ollama11464在上一轮已替代5708，启动来源仍未知，不归因于用户或本轮，也未进行服务控制。

原cleanup=PASS，事后七保护身份相符=True，已登记本例原生身份仍存在数=0。点观察不能证明连续存活，不提升旧终态。无UI、音频、14B、下载或生产服务操作；默认模型不变。

原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8，service260/client300/rootwork275/cleanup310/seal315秒保持。当前候选受控0/3；旧269aca5的E01/E03信用不转移。当前一次运行和一次结果复核额度均0，不能宣告E02/T2/Owner总验收。

本例失败后当前序列结束；后续修复或新例需另行明确范围，不在本次额度内重跑。

本轮执行裁决：保留旧候选、工作区和证据（代价为存储）；用官方支持的分组/字符类/分支表达原operation边界，既有事实门保持（长输入可能仍被原预算拒绝，不扩限）；离线准备不计真实研究信用；全局原生计数、持续存活、OS全流量及E02/T2总体验收保持未测量或未通过。初始RED、官方格式断言失败与离线命令拼写错误均保留，不计最终通过数。

远端push此前自动审批拒绝blocked by policy；本轮未重试或绕行。
