# 候选 6d758d9 的 E02 单例执行提案（准备阶段，尚未分配）

原工单wo-ultimaagent-20261101-0021 / T2；产品候选6d758d9c3961f156a062e349ec4a949e2ee7a9a9；本准备根e02-json-string-controlled-preparation-20261107-r1。本轮按持续目标准备新候选入口，保留用户已明确的单例分配门；持续目标本身不生成本例分配。当前actual_case_allocation=0、result_review_allocation=0；本文件不是运行授权，不会自动创建grant或启动产品。

## 待明确分配的唯一范围

准备包独审PASS及本地发布读回后，请用户明确分配：
- 一例当前qwen3-8b-uncensored的原题、原四来源受控研究。
- 一次针对该例首个结果的只读独立事实、引用、覆盖和协议复核。
- 失败不重试；该例无论结果如何均消费本次额度；没有第二例、换模型或加预算授权。

模型digest固定6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原题原文：

查询Jarvis.ceo桌面端的任务架构与现有开源接入，整理带来源的文档保存为research.md。请实际搜索并阅读相关官方资料，可参考这些固定版本源码：https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/README.md, https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/src/core/agent-manager.ts, https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/src/agents/unified-agent.ts，以及现有执行底座的官方源码 https://raw.githubusercontent.com/open-jarvis/OpenJarvis/0eb7811df96cf139e6bd6d7fcc9b5cc4ff1418ff/src/openjarvis/agents/native_react.py。

四个完整来源使用既有受控corpus，SHA2569e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002。搜索/GET返回固定资料；模型回答由原SDK/HTTPX真实调用本机8B，不由harness供应或代写。本例不冒充真实互联网搜索验收。原正常SSRF分支可能对raw.githubusercontent.com做受限DNS。

## 原预算与入口

CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315秒；context16384；messages+schema32768/entity49152字节；输出最多2048（既有阶段较小上限保持）；retry0。原RootInvocation时钟、身份核对、隔离端口18799、模型11434、清理和父子进程准入保持。

唯一入口为本根code/entry.py，固定解释器H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe，参数-I -B -X utf8，不接收覆盖参数。只有controller收到明确单例答复、核对exact manifest/独审、本地发布及当前输入后，才生成TTL<=120秒的新鲜release/user-allocation.json。不能复制旧grant，不能使用本轮actual0准备消息签发actual1，也不能把harness-approval当运行权。入口先排他消费再运行，失败不回补。

实际写域仅本根release/controller-authority/controller-ledger/native-preflight/actual/E02-controlled-1及后续review/verification。清理只限核实为本例创建的新进程；七个保护进程不操作。无UI/音频、生产服务启停、安装下载或14B；无需暂停键鼠。

准备通过并取得明确单例分配后，唯一命令为：

```powershell
& 'H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe' -I -B -X utf8 'H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-json-string-controlled-preparation-20261107-r1/code/entry.py'
```

当前产品保留读取预算/来源覆盖联动与固定“本次研究未交付。”终态，并将代码事实的原生采样约束投影为合法 JSON 字符串语法；解码后的严格约束保持。入口不为模型选页或代写。生成与重放仍须使用当前候选相同 schema，三来源覆盖仅打开写入资格，不代表回答原题。

## 请求回执与接受口径

HTTP失败时保留当前产品v3私有诊断：代次、固定路由、真实HTTP状态、请求实体SHA/字节数、send_reserved和有界接收计数。500正文不读取；200后坏JSON/schema/扫描失败保持状态200但不标validated。私有回执须经过原adapter导出、绑定和摘要核验；不能从模型文本或旧日志补造状态。

第一结果无论成败均封存、独立复核。成功须同时满足research.md、可信runtime proof、写入读回、ACK、逐事实/引用、原题覆盖、原时限、清理和结果独审PASS；最多新候选受控1/3，T2/Owner不提前通过。失败保持FAIL并据确证回执决定是否另提最小兼容修复，不自动补修或重跑。上一 N15 的 5e6ea89c-8e47-43a6-9480-7a11d72cabf5 失败与 N16 的 781 项离线通过均不迁移成当前实际信用。原生二进制和真实 8B 对新投影的行为尚未实际验证。

## 准备状态

本文件随准备包封存；审查结果、输入摘要、本地提交/tag/镜像读回分别由独立回执和最终就绪读回提供。准备阶段没有release、actual或controller-authority目录。本轮远端同步仍受此前自动审批blocked by policy阻断，不重试或换通道。
