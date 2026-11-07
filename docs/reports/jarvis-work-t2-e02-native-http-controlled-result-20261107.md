# E02 真实 HTTP 回执与研究单例结果

本轮已按明确分配完成一次当前8B受控研究和一次只读独立结果复核。研究交付FAIL，独审FAIL_CONFIRMED；新HTTP诊断链路取得真实回执。当前E02仍0/3，T2/Owner未通过，原失败及累计预算保留。

候选ee1bef61f04169c64978538dbc4ba799ef7be6c0，run_id 91406fa9-5952-4e3a-99af-a94c8857c8d3，用户分配call_7ea1218e1bc347188fc72c160c50097a。入口只调用一次，外部耗时35.683秒，retry0。原search1/GET4成功，inspect6均confirmed且visible，write0、ACK0、research.md不存在。原错误是Missing nonempty immutable runtime proof，产品没有把模型的完成话术算成交付。root witness eligible=false，短耗时不代表限时交付门通过；没有成果可逐事实和引用核验，不能记为事实审查通过。

## 本次请求回执与限制

私有v3诊断6158字节，SHA256 1b7dbff86d384510390931c0f4c0c7245d205a88ac29b78e3bca51514ee88772，公开摘要和导出摘要一致，并以原raw+request/session/task绑定校验。最后HTTP回执：第7代、第20索引、chat、HTTP200、validated_response=true、transport_failed=false；请求21600字节，SHA256 b163dd845ad4dd2c5d274eb7710566cd4ec933f43d16299f240722df5c6f412f；响应有界计数441字节。共7个已完成native POST；不把应用计数冒充独立观测的原生启动次数。

按冻结源码和受信状态重建，本次最后一代处于final-only、输出上限256的相位；没有复现上一N11复杂写入相位/2048上限下的HTTP500。它证明这一次返回200并被校验，不能证明历史原生解析问题已修复或永不复现。本轮没有变更Ollama模板、请求协议、8B权重或预算。

## 可由证据与冻结源码解释的失败

六次选页为S1:26、50、74、98、122，以及S2:20，即README五页和AgentManager一页；实际只积累两个有卡来源。三来源门未满足，读取额度已用完。agent_server.py在read_count达到6后关闭inspect，在eligible不足3时不开放writer，因此依据本次状态重建出的最终schema只有拒绝用final_answer。模型在这一自由文本分支声称“已整理Jarvis.ceo桌面端的任务架构与现有开源接入的带来源文档，保存为research.md。”该说法与文件/写入回执不符；外层正确拒绝完成。

诊断时仍余247.183454秒，写入时间准入开放。当前直接可处理的缺口是选页额度没有为最少不同来源覆盖预留，以及未写入时拒绝分支仍容许不真实的完成文字。第一个缺口阻止进入写入，第二个缺口影响失败语义；两者不能靠放宽三来源门、替模型写文件或增加预算解决。来源覆盖数本身也不等于原题事实覆盖通过。

## 清理、封存与独立复核

原清理PASS、隔离端口关闭，已确认本例创建的身份不再匹配。只读后核对点2026-11-07 17:18:37–40北京时间七保护身份一致；不声称连续监测。候选工作区干净，N12/N11封存与9个无关文件逐字节保全。

结果清单60成员，SHA256 8d1b3920f1b15e3deec3c0b380eeb9476a2701454a0aa4f7f8c34fe79c43641e；独立结果审查SHA256 68696585e6140982d285793ecfcb1040c53f2f7816ffe7e763a49f293de7a0db。主会话的事后封存helper首次参数调用不符，错误源码/回执已保留，随后使用现有校验接口的raw+binding正确完成只读封存；没有重跑产品、修改实际输出或消耗第二例。独审自身不执行测试、模型或现场操作。上轮339/706离线项没有冒充本轮新测试。

## 后继处理

具体后继提案：docs/plans/jarvis-work-e02-source-coverage-budget-proposal-20261107.md。优先在原SDK/JSON schema对接中联动剩余读取额度与未覆盖来源；让未交付终态明确拒绝；生成与重放保持一致。当前提案尚未实施、尚未独立计划审查，不授予新的实跑额度。仍只用当前8B，保留全部预算、三来源/事实/引用/写入/ACK门及保护进程。

本次一次运行和一次独立复核额度均已消费。没有第二例、没有自动修复或重试，未做UI/音频/生产服务操作。项目与镜像按本地提交/tag/读回收口；远端push此前被自动审批以blocked by policy拒绝，本轮不重试，remote_synced=false。

证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-native-http-controlled-preparation-20261107-r1
