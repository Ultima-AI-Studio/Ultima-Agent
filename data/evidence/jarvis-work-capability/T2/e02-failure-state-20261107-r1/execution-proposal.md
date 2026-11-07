# 已授权失败状态诊断单例

原工单 wo-ultimaagent-20261101-0021 / T2，候选 22653fb77445bad4f5b9d9ae789cd35972dcc984。本会话最新用户消息为“先补齐失败时的最终分支和选页诊断，再针对证据修复‘读取到交付’的衔接。”；准确原始标点与内容以 inputs/direct-user-decision.json 为准，文件 SHA256 3b52b8b54fd33d51af69a995a49df270a9f0f33062c64c547b646bc35b0ff6e5。该记录精确绑定用户原文及已独审计划，decision_id 为本地内容哈希，不是平台消息 ID。

本根只分配诊断目的的一例，不是补修后验收例。准备独审 PASS、本地提交/tag/镜像读回及只读运行身份核对通过后，使用唯一入口 code/entry.py 一次，失败不重试。后续修复验证只有在本例证据明确指出可修复原因、新候选完成必要准备独审后，才能在新的证据根另行分配最多一例；不以本根重试替代。

仅当前 qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题：查询Jarvis.ceo桌面端的任务架构与现有开源接入，整理带来源的文档保存为research.md。请实际搜索并阅读相关官方资料，可参考这些固定版本源码：https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/README.md, https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/src/core/agent-manager.ts, https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/src/agents/unified-agent.ts，以及现有执行底座的官方源码 https://raw.githubusercontent.com/open-jarvis/OpenJarvis/0eb7811df96cf139e6bd6d7fcc9b5cc4ff1418ff/src/openjarvis/agents/native_react.py。

四完整来源 corpus SHA256 9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002。search/GET 使用原受控资料，当前模型经原 SDK/HTTPX 实际调用，回答不可替换；本例不充当真实联网验收。CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒；retry0；context16384、messages+schema32768/entity49152字节门保持。正常 SSRF 分支可能对 raw.githubusercontent.com 做受限 DNS。

新增内容仅为失败观察：可信 ledger 在原锁下冻结一次不超过16384字节的封闭诊断，包含经过扫描的有限最终回复、分支、选页/卡片坐标、确认状态和原预算计数。public result 只追加摘要；私有原文仅独占创建到本例受保护证据域。诊断丢失或导出失败不能替代原 product error，也不能产生 runtime proof、ACK、END 或通过信用。write_admission_open 只表示当时剩余时间达到原55秒门槛，不授予执行能力；已封存失败仍不可写。

分配 TTL≤120秒，绑定当前 manifest、准备独审、候选及模型；预消费一例、一结果独审、零重试。实际写域限本根 release/controller-authority/controller-ledger/native-preflight/actual/E02-controlled-1 和后续 review/verification。清理只限本例核实的新进程。七保护身份沿用 e02-source-reference-schema-20261107-r1/inputs/protected-baseline.json，SHA256 1b7e945e9ce52e44b8b384fc5e3911b77b7da4d80beeba615f341bf3e923fce5；身份漂移不绕过。

无论成功失败，封存第一结果并进行一次只读独立复核，随后按可信证据判断衔接修复。成功仍必须满足 research.md、可信 SDK packet、ACK、两次外部读回、逐事实引用、原题覆盖、原时限、清理及独立结果 PASS。诊断完整不等于 E02 通过；最多当前新候选受控1/3。旧 E01/E03 信用不转移，T2/Owner门不提前通过。无 UI、音频、生产服务操作，不下载模型，不使用14B，不重试被自动审批拒绝的远端推送。
