# E02固定目标schema对齐：单例结果

原工单wo-ultimaagent-20261101-0021 / T2。用户call_409cc146033c4184879042b1abac6383授权的最小补修、必要独审、一例当前8B原题四来源研究和一次独立结果复核均已完成。本例未通过，当前候选0/3；独审FAIL_CONFIRMED。E02/T2仍未通过。原单例已结束，未重试、未分配下一例。

## 交付的最小修复

候选900b944165c0175b91492e3fe5b31d96aabdcd5c，基于6cb9284。work_navigation.py只改一行：path保留string长度约束，增加enum:[research.md]。原writer精确目标检查及引用、事实、END、ACK、读回、目录权限和时限不变；没有改写模型响应或扩大目录授权。新增19项测试：旧schema RED12失败/7通过，新schema GREEN19，验证SDK传入native format与strict replay同一enum、错误参数派发前拒绝、合法写入/ACK/读回完整。

826项离线检查通过：产品537、harness238、输入/入口/边界51。两项原HTTP/junction集成排除不计通过。transport首轮90秒超时证据保留，原源码和原90秒上限隔离复核104通过，pytest64.48秒；不改实际研究截止。准备manifest 68b6cd6ad14dcbc88e6f7730a33685fee7ea61923b86a61d63f0622f025dd316，独审PASS，项目93b02260c5c2930cd1d46418ce343c37116dd137 / 镜像1eeba102e03b76644bdfa92ed52ec0d8e7b807a8，本地提交/tag/读回后才签发本例。

## 唯一实跑与独立复核

run 4fab6e08-5e5e-44d4-9ca5-3a1e75272938；UTC 2026-11-07T04:11:13.1842323+00:00 至 2026-11-07T04:12:01.2887606+00:00，外层48.1012354秒。原终态FAIL，产品status=failed，error=Unlinked or failed END。CLI尝试1，受控search成功1、GET成功4、可用来源4；应用native POST尝试5。真实原生总启动计数未测量，保存为None。

安全writer诊断：{"stage": "research.write", "reason_code": "FOREIGN_REFERENCE", "error_type": "ValueError", "error_text_length": 17, "error_text_sha256": "d70d189223294e5dd10b6338b6ed27fb7d2da5a7ffc65aec0911f283e6e8056c"}。不能仅凭旧失败或缺失字段推断当前/历史错误原因，具体事实和可交付性以独立结果审查为准。

本例FOREIGN_REFERENCE与唯一静态消息Foreign reference的长度17及SHA一致；resolve_v3先确认ref已在issued中，再因view.source_id与章节source_id不一致拒绝。因此已跨过research.md路径检查，当前失败是已发行证据的来源归属与章节标注不一致。具体evidence_id和两端source_id未导出，保持未知，不称为未发行ID，也不猜是哪一份来源。没有研究文件，不能称其他事实已经合格。

本例不构成对8B一般能力的结论，N4历史写入失败的具体原因仍未知。独审的两项important发现均保留为未交付与当前引用归属拒绝；不会用准备PASS盖过它们，也不在已耗尽的单例范围追加产品修改或重跑。

没有 research.md 交付。

结果manifest 1970c8dfc91ac852883b518a7b3856ddaf4dc09d009223c594fd9c53363b09b2（44成员），独审SHA256 a1d3701e82b961c65535a7fa2bc4efda427a0422b8fe647e07359c5dcdd1f4e8。审查原文位于H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-fixed-target-schema-20261107-r1\review\independent-result-review.json；审查未新增测试或产品/模型调用。

## 保护、清理和信用边界

原cleanup=PASS，只读核对七个保护身份相符=True，已登记本例原生身份仍存在数=0。点观察不等于连续存活；后续观察不提升原终态或旧失败。没有UI、音频或生产服务操作，没有14B、下载或更改默认模型。

原CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/rootwork275/cleanup310/seal315秒保持。全部旧失败留存，旧候选269aca5的E01/E03信用不转移。当前候选受控通过0/3，仍需后续同候选规定例数、真实联网及当前候选E01/E03和T2出口门；本例不等于产品总验收。

当前一次实际例及一次复核额度均0；本授权范围完成。后续例或超出本schema补修的变更没有分配。已准备未实施提案H:\UltimaAI\UltimaAgent\docs\plans\jarvis-work-e02-source-reference-schema-alignment-proposal-20261107.md：使用现有anyOf/enum，按source限定本请求可见evidence_id，并对齐生成、本地strict验证与独立runtime重放；原writer归属和事实门保持，不改写模型结果。它需要新范围，不属于本例的已实施内容。

本地提交/tag及UltimaDocs镜像；远端push此前自动审批拒绝blocked by policy，本轮没有重试或绕行。
