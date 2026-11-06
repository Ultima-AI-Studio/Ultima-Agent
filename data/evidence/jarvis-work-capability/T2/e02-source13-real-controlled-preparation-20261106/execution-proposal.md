# 当前8B真实受控研究首例执行提案

仅在本包独立准备审查PASS、且用户明确分配一例真实8B研究及一次独立结果复核后生效。此前零推理授权已经用完；本文件不签发新运行权。

## 目标与输入

原工单wo-ultimaagent-20261101-0021 / T2 / E02-controlled-1。产品候选269aca511d88412dbb9c15d23911138469a37aa2；仅qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。沿用原题和四份完整受控来源，不改默认模型。

原题：查询Jarvis.ceo桌面端的任务架构与现有开源接入，整理带来源的文档保存为research.md。请实际搜索并阅读相关官方资料，可参考这些固定版本源码：https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/README.md, https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/src/core/agent-manager.ts, https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/src/agents/unified-agent.ts，以及现有执行底座的官方源码 https://raw.githubusercontent.com/open-jarvis/OpenJarvis/0eb7811df96cf139e6bd6d7fcc9b5cc4ff1418ff/src/openjarvis/agents/native_react.py。

固定来源：
- https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/README.md
- https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/src/core/agent-manager.ts
- https://raw.githubusercontent.com/akshayaggarwal99/jarvis-ai-assistant/bec50ef6e615707613c4fa22c8bd6afc3cc93152/src/agents/unified-agent.ts
- https://raw.githubusercontent.com/open-jarvis/OpenJarvis/0eb7811df96cf139e6bd6d7fcc9b5cc4ff1418ff/src/openjarvis/agents/native_react.py

corpus SHA256：9e7cdfe6ed7874d22d1657692a103df19d4f763cdbc8eb92e6ec5925b05cd002。

## 唯一拟执行命令

```powershell
& 'H:\UltimaAI\UltimaAgent\tools\venv-openjarvis\Scripts\python.exe' -I -B -X utf8 'H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-real-controlled-preparation-20261106\code\entry.py'
```

新授权到达后才创建release/user-allocation.json，绑定本manifest、独审报告、新问题编号和原答复；执行前120秒内生成，实际例1、结果独审1、retry0。entry先独占写consumed.json，再创建原RootInvocation，完成实时七身份与模型摘要准入。缺授权、缺准备PASS、漂移或重复消费均不进入产品调用。harness-approval只是准备审查记录，不能替代新用户分配。

入口只创建隔离测试server与一例产品CLI，真实模型调用既有本地Ollama；不启动/停止生产服务，不操作UI、音频或麦克风。隔离server的固定端口18799占用时拒绝，不换端口重试。只管理本例新建进程，七个保护身份必须保持。准备阶段尚未重新查询生产进程，未来以执行入口的实时校验为准。

## 原预算与写域

CLI1、search1、GET4、inspect6、write1、ACK1、native_POST8；service260秒、client300秒；从同一父时钟计算work275 / cleanup310 / seal315秒。父时钟先于preflight和authority，未重置。资料搜索/GET使用原受控全文夹具；模型transport使用真实SDK/HTTPX，绝不使用Mock回答。运行可能沿原SDK SSRF分支对raw.githubusercontent.com进行DNS查询；本例不是另一次真实联网来源验收。

新写域仅本目录下release、controller-authority、native-preflight、controller-ledger.json、actual/E02-controlled-1及随后独立结果review。产品输出应为actual/E02-controlled-1/outputs/<task-id>/research.md。所有旧失败、零推理包和冻结产品保持原字节。失败封存后结束，不重跑。

## 判定与限制

必须拿到真实产品首结果、完整SDK packet、原四来源/引用绑定、一次写入与ACK、文件哈希及两次读回、Owned清理和同父时钟终态。机械通过仍只是PENDING_ROOT_INDEPENDENT_REVIEW；独立事实复核逐条检查research.md陈述与具体来源、Jarvis.ceo与OpenJarvis归属是否区分、有无无依据内容。不能只凭模型自评、测试或文件存在宣布通过。

该例至多获得受控研究1/3；E02完整门仍需同候选连续3例及另一次真实联网至少3条去重来源。E01/E03已通过记录不挪用为E02信用。T2、后续阶段及Owner保持原门。

已完成离线检查269项：14输入、219原harness、10身份/transport、1原始SDK产物只读复放、25入口；原71测试函数全部保留。测试中的Python SSRF/DNS与固定UUID4只用于离线测试，实际child不继承。生产随机ID曾在一个离线随机夹具触发PII扫描，真实运行的行为仍待实证。

远端push仍因此前自动审批blocked by policy未同步；本次不重试绕行。准备包通过后先做本地提交/tag和UltimaDocs逐字镜像，再申请新的实跑额度。
