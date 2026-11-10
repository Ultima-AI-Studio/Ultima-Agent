# E02固定目标schema对齐：新候选准备

原工单wo-ultimaagent-20261101-0021 / T2。用户call_409cc146033c4184879042b1abac6383授权最小schema补修、必要独审、通过后一例当前8B原题四来源及一次结果复核；失败不重试。候选900b944165c0175b91492e3fe5b31d96aabdcd5c，基于6cb9284，独立工作区C:/Users/Administrator/.codex/worktrees/jarvis-e02-fixed-target-schema/UltimaAgent。

## 唯一产品改动

work_navigation.py::v3_writer_schema只改一行：path保留type:string/minLength1/maxLength2048，增加enum:[research.md]。原writer只接受research.md的条件不变，所有路径/引用/事实/扫描/END/ACK/读回/预算/时限和主错误行为不变。没有改写模型响应、扩大目录授权、改模型、提示或另建框架。

_research_sampler_schema原来只移除maxLength，会保留enum。新测试检查真实SDK mock transport发出的native format、strict_schema和sampler_schema三者均含同一个path enum；坏路径在native envelope验证处被拒，未派发writer，无文件或effect；合法research.md完整写入、ACK、外部SHA及来源读回成功。这里native响应为离线fixture，不是真实模型验收。

有效RED12失败/7通过：8个原schema接受的不可执行路径、3个原本到writer才失败的原生回复，以及缺失native enum；GREEN19。产品回归537=目标19+原诊断17+metadata43+研究178+navigation90+transport104+交付上下文86。保留两个原离线排除项：本地HTTP服务与cmd junction，均不计通过。原guard/Python SSRF离线fixture不变，OS包未测量。

新候选harness函数不变，仅重绑路径/候选/哈希。原238 harness用例和入口26/边界11/绑定14必须在新绑定通过，最终826项以封存readback为准。61来源、1551输入绑定。原P4/P1、保护基线、语料、模型manifest和旧失败保持；旧E01/E03信用仍属269aca5，新候选未实际回归。

## 工作区与保护核对

首次原生创建使用主仓库为source后停在creating，现有checkout虽可只读验证，但附加接口拒绝核验归属；该目录未写入或删除。改用当前已附加C5工作区为source创建独立名称，原生operation1953bae8-e0c5-42d7-a462-8194e1599757已completed且registrationError=null，才开始产品修改。原始operation0d662b62的登记问题不被伪称修复，资料保留。

北京时间2026-11-07 11:53的只读点核对，七个保护身份native/CIM/parent/命令摘要均与原基线一致；没有服务操作或模型调用。此观察不能替代实际入口的保护前后核验或连续存活证据。

## Review Focus

schema与writer都只允许research.md；native sampler和strict replay使用同一enum且没有改写响应；错误参数在派发前拒绝、合法完整链路保留；唯一现有产品源文件变化限于schema；原8B/语料/预算/时限/保护/清理门和所有历史失败不变。

当前没有actual authority或真实研究运行。E02/T2 NOT_PASSED。远端push仍受此前自动审批blocked by policy阻断，不重试或绕行。

## 离线超时记录

transport首轮在多个SDK测试组并行时触及原90秒离线上限，完成前未报断言失败，不计通过；保留transport-20261107T035752856026Z全部记录。按同一源码、同一guard、同一测试选择和原90秒上限单独复核运行，transport-20261107T040216631851Z完成104项，pytest64.48秒。并发负载是排查假设，未作OS级根因测量；该复核不改变实际研究次数或任何运行截止。537项产品回归只按每组最终完整绿色收据计数。

## 独立准备审查结果

PASS_PREPARATION_ONLY；manifest 68b6cd6ad14dcbc88e6f7730a33685fee7ea61923b86a61d63f0622f025dd316（454成员），review SHA256 2f8cdc35017c73bbc3833a516de870adde355caa2f45dbbb83e8038743fd1966。826项离线检查、1551绑定输入与61来源读回；实际入口尚未调用，按既有完整授权继续一例。
