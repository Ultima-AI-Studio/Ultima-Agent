# E02来源与证据schema对齐：单例结果

原工单wo-ultimaagent-20261101-0021 / T2。用户call_33506a697ec545c6b2a396ff83086672授权的补修、必要独审、一例当前8B原题四来源研究和一次只读独立结果复核均已完成。本例未通过，当前候选0/3；独审FAIL_CONFIRMED。E02/T2仍未通过，单例已结束，无重试和下一例分配。

## 实现与准备

候选a0d21ebf167c41a76410075f7a92f1680926213f，基于900b944。现有anyOf/enum按本请求可信可见source_id约束evidence_id；generation与独立runtime replay重建相同schema/phase，保持confirmed pending页时序。原research.md、归属/事实/重复来源、END/ACK/读回和时限门保留，生产不改写模型回答。新增29项测试；原诊断fixture在合法schema后注入resolver故障保留原覆盖。准备详情见jarvis-work-t2-e02-source-reference-preparation-20261107.md。

最终857项离线检查：产品566、harness238、绑定16/入口26/边界11。两项HTTP/junction离线排除不计通过，全部先前失败和中途测试失败保留。准备manifest 1cd281cf72510b099759f000c1b4aab96e815154b71de03f402ed50d13c07f75；独审PASS后完成项目1e1d06f6536b4daa18b0968ccce046bd854230d8/镜像98788aca098b766d1c2f3a228b1e3deac308026f本地提交、tag和读回，才签发唯一实际例。

## 实际结果

run dc3dbef6-ef60-4ba6-8d54-79c9c93d99df；UTC 2026-11-07T05:06:08.7007667+00:00 至 2026-11-07T05:06:52.1507524+00:00，外层43.4456879秒。原终态FAIL，产品status=failed，error=Unlinked or failed END。CLI尝试1，受控search成功1、GET成功4、可用来源4；应用native POST尝试4。原生总启动计数未测量，保存为None。

有限writer诊断：{"stage": "research.write", "reason_code": "CODE_OPERATION_REQUIRED", "error_type": "ValueError", "error_text_length": 42, "error_text_sha256": "b577a36cbea9c8b39ba76e2b324ea4d08c17c11baaf5fa26612325718559096b"}。

本次有限诊断 `CODE_OPERATION_REQUIRED` 的42字符错误摘要与候选中唯一的 `A code claim must name its exact operation` 抛出处相符（work_research.py:329–332）。它是复合条件：代码证据的 operation symbol 必须是长度受限、格式有效的标识符，并且以原规定的精确边界出现在 claim 中。

`resolve_v3` 对当前检查到的事实先验证引用已发行及来源归属（work_navigation.py:519–521），然后从可信卡片注入 kind/symbol 并调用事实核验（522–526）。因此本次已经跨过该条事实的固定目标、引用存在和来源归属检查，失败发生在随后的代码事实契约检查。不能据此声称所有后续引用和事实都通过。

具体 claim、operation、source_id 和 evidence_id 未导出，复合条件中究竟哪一项失败也未知；不能断言遗漏了某个函数名。没有 research.md，无法将本次记录为可交付研究，更不能用离线857项通过替代真实验收。本次结果不构成对8B一般能力的结论。

静态读回：code-operation-contract-readback.json；结果manifest SHA256 95abc1e0d527386e08aeed33a176310e6ef51996ad544da3c2fb3b024658cf4f。本分析只读取已保存结果和冻结代码，没有执行产品、测试、模型或新网络请求；最终归因以独立结果复核为准。

独立结果复核已确认FAIL_CONFIRMED（review SHA256 a9f95a05a75375fcd72fee5fff6be9fe3013a15ed9a7393e858082ecc6ad6e30）。两个阻塞项为没有研究交付文件，以及trusted export/END/资格witness不完整。外层耗时短不能替代合格时限证明。两项作为真实验收失败保留，没有在本单例内追加修改或重跑。


没有 research.md 交付。

结果manifest 95abc1e0d527386e08aeed33a176310e6ef51996ad544da3c2fb3b024658cf4f（44成员）；独审H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source-reference-schema-20261107-r1\review\independent-result-review.json，SHA256 a9f95a05a75375fcd72fee5fff6be9fe3013a15ed9a7393e858082ecc6ad6e30。审查未运行新测试、产品或模型。

## 保护与边界

本例前只读记录现有Ollama11464取代已退出5708，父进程/可执行文件/命令摘要、版本0.32.15和8B摘要相同，其余六身份一致；用户说明没有主动重启，启动来源未知。旧基线保留，新七身份基线按固定路径和SHA绑定，没有服务控制。

原cleanup=PASS，事后七保护身份相符=True，已登记本例原生身份仍存在数=0。点观察不能证明连续存活，不提升旧终态。无UI、音频、14B、下载或生产服务操作；默认模型不变。

原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8，service260/client300/rootwork275/cleanup310/seal315秒保持。当前候选受控0/3；旧269aca5的E01/E03信用不转移。当前一次运行和一次结果复核额度均0，不能宣告E02/T2/Owner总验收。

已准备未实施后续提案：H:\UltimaAI\UltimaAgent\docs\plans\jarvis-work-e02-code-claim-contract-alignment-proposal-20261107.md；没有分配新实际例。

本轮执行裁决：保留所有工作区和旧证据（代价为存储）；测试区分token估算与字节门且不改产品上限（超限继续失败关闭）；诊断fixture改在resolver边界注入以保留原覆盖（由17项原诊断回归核对）；仅只读重绑已运行服务身份（若再漂移则入口拒绝，连续存活不计）；离线准备不给真实研究信用，独审未覆盖的OS全流量、全局原生计数和总体验收保持未知。

远端push此前自动审批拒绝blocked by policy；本轮未重试或绕行。
