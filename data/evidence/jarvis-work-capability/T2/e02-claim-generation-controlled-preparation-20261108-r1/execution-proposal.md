# 候选 d8f8d97 的 E02 单例执行提案（准备阶段，尚未分配）

原工单wo-ultimaagent-20261101-0021 / T2；产品候选d8f8d97cd0147ffc6f45746ffd1ec80bc4d48b2b；本准备根e02-claim-generation-controlled-preparation-20261108-r1。本轮按用户call_5411de619a6c4de0bab414126a228c7d明确授权的离线补修计划Task3准备冻结候选入口，保留用户已明确的单例分配门；持续目标本身不生成本例分配。当前actual_case_allocation=0、result_review_allocation=0；本文件不是运行授权，不会自动创建grant或启动产品。

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
& 'H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe' -I -B -X utf8 'H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-claim-generation-controlled-preparation-20261108-r1/code/entry.py'
```

当前产品保留读取预算/来源覆盖联动与固定“本次研究未交付。”终态，并将代码事实的原生采样约束投影为合法 JSON 字符串语法；解码后的严格约束保持。共享阶段提示现在接收该请求实际num_predict，生成与独立重放共同核对。提示紧凑JSON、简短标题及精确原子事实，但保留完整原题信息与引用；实际预算、严格schema、来源/事实门不变。ACK原指令保持。入口不为模型选页或代写。生成与重放仍须使用当前候选相同 schema，三来源覆盖仅打开写入资格，不代表回答原题。

## 请求回执与接受口径

当前候选在原生拒绝处可输出闭合v5私有诊断：同请求flags/options及strict/sampler摘要、content/thinking类型和长度摘要、完整content严格JSON状态和受限错误位置、完整JSON的schema/结构计数。thinking和未知字段值不留正文；安全扫描后优先FULL，原16384字节诊断上限不足时使用带偏移和省略计数的EXCERPTS，策略拒绝则OMITTED_POLICY。编码预算或诊断异常时保留原v4，不删除旧证据；v3/v4仍可读。所有字段绑定同一实际请求和原始响应字节SHA/长度。length仍拒绝，不修复残缺JSON，不从片段执行工具。原响应65536字节上限、公共摘要、500正文不读取及原失败语义保持；本诊断只覆盖已能解析外层JSON的原生拒绝。私有回执经原adapter观察器导出，写后ACK拒绝保留已写入事实；诊断不等于完整runtime、END或交付。

第一结果无论成败均封存、独立复核。成功须同时满足research.md、可信runtime proof、写入读回、ACK、逐事实/引用、原题覆盖、原时限、清理和结果独审PASS；最多新候选受控1/3，T2/Owner不提前通过。失败保持FAIL并据确证回执决定是否另提最小兼容修复，不自动补修或重跑。上一实际c4caa739-c466-44f3-866b-0c57ea8c5e40保持FAIL_CONFIRMED：第7次HTTP200，done_reason=length、eval_count=max_tokens=2048，未交付research.md/write/ACK/runtime END。完整3818字符正文证实两个短句重复50/49次，JSON在pos1339处未闭合，并存在独审发现的引用错配与未读S4风险。新候选仅要求代码claim先输出精确operation再描述该语句可支持的事实，移除operation之前的任意长前缀。严格schema、writer、引用/事实/覆盖门和原预算保持；后缀及非代码字符串仍可能重复，不能推断已解决截断或保证2048内完成。N34的1004项离线检查和本入口350项检查不转为实际信用；本例仍按完整原题交付验收。

## 准备状态

本文件随准备包封存；审查结果、输入摘要、本地提交/tag/镜像读回分别由独立回执和最终就绪读回提供。准备阶段没有release、actual或controller-authority目录。本轮远端同步仍受此前自动审批blocked by policy阻断，不重试或换通道。

## 本轮离线边界与待核验项

本轮准备没有模型调用、网络请求、UI/音频或生产服务操作。运行态为PENDING_FRESH_ACTUAL_PREFLIGHT；保存的旧原生版本、模型及七保护身份回执仅供历史追溯，不能证明当前运行态。只有明确分配本例后，原run_released才在同一原始时钟内重新核对全部保护身份、原生监听归属和元数据/模型摘要，以及原adapter隔离端口门。任一检查失败即终止本次单例，不绕过、不重试、不操作受保护进程。现有默认模型及语音链路不因本提案修改。
