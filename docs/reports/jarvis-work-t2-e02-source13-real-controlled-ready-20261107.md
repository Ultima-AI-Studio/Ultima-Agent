# 当前8B真实受控研究首例：准备通过，等待新单例分配

原单wo-ultimaagent-20261101-0021 / T2。零推理接线及其独立结果复核已通过并消耗完原单例额度。当前已完成真正使用当前8B的首例准备：270项离线检查、整个准备包的独立只读审查和当前字节读回通过。没有运行本例，E02/T2仍未通过。

产品固定269aca511d88412dbb9c15d23911138469a37aa2；模型qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题、四来源、8次native POST上限及275/310/315秒保留，KWS/语音/生产配置未改。

## 已完成

- 输入绑定14项；原harness219项（71测试函数全部保留）；七身份/真实transport边界10项；先前SDK原始产物只读复放1项；一次性入口26项，合计270。5次完整适配回归的失败与最终PASS分别保存，未删除或挪用验收信用。
- 入口只接受本manifest绑定的新显式用户分配，先独占消费，再建立原RootInvocation父时钟并做实时七身份和模型准入；接入已有产品CLI、SourceNavigation及原生SDK模型调用。失败不重试。
- 原独审发现PREP-I01：Windows清单路径与入口必需项表示不一致。原172成员包及NEEDS_FIXES报告保持原字节；本候选只统一实际清单生产函数为正斜杠，补充直接使用该函数的RED→GREEN回归，并用完整新封存包在临时夹具做只读准入验证。入口及全部harness运行源码与原独审字节相同。
- 独审修正确认：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-real-controlled-preparation-20261107-r1\review\independent-preparation-review.json，SHA256 e3e3e46391243ae02f3eb9a131f4dd9c836713091c95fd872448b233480d934f。结论PASS_PREPARATION_ONLY，承接原整包审查并核对本次有界修正及新绑定；审查者未调用模型或产品、未追加测试。当前无待处理问题。
- 准备manifest 224faf544e895624dd02e542e4fb4fd26d487c095377c8b81b8bda0c4e65b544，190个成员；harness manifest c90437e780770e1cf3d743735e30d316e45722b90b6ea1ea8cb76d88bbf7daab。本地tag ultimaagent-t2-e02-source13-real-ready-20261107只标记准备就绪。

## 明确的验证限制与裁定

离线SDK单测采用SDK的Python SSRF检查和固定DNS，避免RustDNS绕过Python网络审计；实际child保留原SDK行为。固定测试熵只用于可重复的离线SDK夹具，并显式生成合法UUID4，真实随机UUID、扫描器与外部读回规则未改。测试不证明真实模型的事实质量、原生RustDNS行为或生产随机ID质量；未来必须按原门实跑。

每项裁定及失败根因见harness准备报告与计划ledger。未测系统包数保持null，未把Mock六次POST计为真实推理。零推理包和全部1544绑定输入在最终读回中保持原字节。

## 下一步

按[execution-proposal.md](H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-real-controlled-preparation-20261107-r1\execution-proposal.md)申请一例当前8B的E02-controlled-1和一次只读独立结果复核。此例无UI或音频操作；最多一次，失败停住。机械通过必须再审查research.md事实、来源归属和引用，才可能计为受控1/3；之后还需其余受控例与真实联网验收。当前分配与结果复核额度均0，harness-approval不替代用户分配。

E01当前候选3/3、E03三正一负PASS保留。远端同步仍受此前自动审批blocked by policy阻断，本次未重试；仅报告本地提交/tag及UltimaDocs字节镜像完成，不声称GitHub已同步。
