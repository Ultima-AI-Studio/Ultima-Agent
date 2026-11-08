# 候选 43da3f0 的 E02 单例执行提案（准备阶段，尚未分配）

原工单wo-ultimaagent-20261101-0021 / T2；产品候选43da3f014a763b8ea3963872a8f1ce8ebea77531；本准备根e02-source-grounding-controlled-preparation-20261108-r1。本轮按用户call_3d33440cc40c401ea7a2cf11c8bc2bcf明确授权的离线补修计划Task3准备冻结候选入口，保留用户已明确的单例分配门；持续目标本身不生成本例分配。当前actual_case_allocation=0、result_review_allocation=0；本文件不是运行授权，不会自动创建grant或启动产品。

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
& 'H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe' -I -B -X utf8 'H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-grounding-controlled-preparation-20261108-r1/code/entry.py'
```

当前产品保留读取预算/来源覆盖联动与固定“本次研究未交付。”终态，并将代码事实的原生采样约束投影为合法 JSON 字符串语法；解码后的严格约束保持。共享阶段提示现在接收该请求实际num_predict，生成与独立重放共同核对。提示紧凑JSON、简短标题及精确原子事实，但保留完整原题信息与引用；实际预算、严格schema、来源/事实门不变。ACK原指令保持。入口不为模型选页或代写。生成与重放仍须使用当前候选相同 schema，三来源覆盖仅打开写入资格，不代表回答原题。

## 请求回执与接受口径

当前候选在原生拒绝处可输出闭合v5私有诊断：同请求flags/options及strict/sampler摘要、content/thinking类型和长度摘要、完整content严格JSON状态和受限错误位置、完整JSON的schema/结构计数。thinking和未知字段值不留正文；安全扫描后优先FULL，原16384字节诊断上限不足时使用带偏移和省略计数的EXCERPTS，策略拒绝则OMITTED_POLICY。编码预算或诊断异常时保留原v4，不删除旧证据；v3/v4仍可读。所有字段绑定同一实际请求和原始响应字节SHA/长度。length仍拒绝，不修复残缺JSON，不从片段执行工具。原响应65536字节上限、公共摘要、500正文不读取及原失败语义保持；本诊断只覆盖已能解析外层JSON的原生拒绝。私有回执经原adapter观察器导出，写后ACK拒绝保留已写入事实；诊断不等于完整runtime、END或交付。

第一结果无论成败均封存、独立复核。成功须同时满足research.md、可信runtime proof、写入读回、ACK、逐事实/引用、原题覆盖、原时限、清理和结果独审PASS；最多新候选受控1/3，T2/Owner不提前通过。失败保持FAIL并据确证回执决定是否另提最小兼容修复，不自动补修或重跑。上一实际1496a844-668d-407a-a91b-89be246ba05b保持FAIL_CONFIRMED：research.md确已写入/END/读回/ACK，9条事实只有第7条同时满足事实与所选引用；S4未inspect，原题任务架构/接入覆盖未通过。新候选用官方allOf有序组件让evidence_id先于claim生成，并在六读内为未读来源保留机会。原strict、writer参数、三来源最低写入资格、完整原题和所有预算保持。字段顺序不是事实蕴含证明，模型仍可能选错页、过早写入或写出不受引用支持的事实；密集多来源卡片可能触发原32768字节strict prompt拒绝。1022项产品/兼容/参考与350项入口离线检查都不转为实际信用。本例须按完整原题验收。

## 准备状态

本文件随准备包封存；审查结果、输入摘要、本地提交/tag/镜像读回分别由独立回执和最终就绪读回提供。准备阶段没有release、actual或controller-authority目录。本轮远端同步仍受此前自动审批blocked by policy阻断，不重试或换通道。

## 本轮离线边界与待核验项

本轮准备没有模型调用、网络请求、UI/音频或生产服务操作。运行态为PENDING_FRESH_ACTUAL_PREFLIGHT；保存的旧原生版本、模型及七保护身份回执仅供历史追溯，不能证明当前运行态。只有明确分配本例后，原run_released才在同一原始时钟内重新核对全部保护身份、原生监听归属和元数据/模型摘要，以及原adapter隔离端口门。任一检查失败即终止本次单例，不绕过、不重试、不操作受保护进程。现有默认模型及语音链路不因本提案修改。

## 保全说明

准备期间一个不属于产品/模型/依赖输入的看板HTML持续变化；原始与观察快照及首份NEEDS_FIXES审查均保留。此文件不写入或暂存，只报告变化；其他14个无关文件和全部产品/依赖/历史证据保持严格摘要核对。该例外不改变运行态核验、模型输入或验收标准。
