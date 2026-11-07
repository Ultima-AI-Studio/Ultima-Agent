# E02 后继提案：让选页预算支持来源覆盖，并诚实结束未交付任务

状态：基于一次真实回执的后继提案，尚未实施、尚未独立计划审查。原单 wo-ultimaagent-20261101-0021 / T2；不创建新单或重置历史。当前获批的一例研究及一次结果复核不自动授权本提案的产品修改或下一例运行。

## 目标与已取得的证据

当前候选 ee1bef61f04169c64978538dbc4ba799ef7be6c0，一例运行91406fa9-5952-4e3a-99af-a94c8857c8d3，35.683秒。search1、GET4、inspect6、write0、ACK0，无research.md，清理PASS。结果清单在data/evidence/jarvis-work-capability/T2/e02-native-http-controlled-preparation-20261107-r1/review/result-inputs/result-manifest.json，SHA256 8d1b3920f1b15e3deec3c0b380eeb9476a2701454a0aa4f7f8c34fe79c43641e。

6158字节v3诊断确认：六页均confirmed/visible；S1读取26、50、74、98、122共五页，S2读取20一页，仅两个有证据卡的来源。第七代chat响应HTTP200且validated_response=true，已完成7个native POST；请求实体21600字节，SHA256 b163dd845ad4dd2c5d274eb7710566cd4ec933f43d16299f240722df5c6f412f。诊断时剩余247.183454秒，写入时间准入仍开放。模型却用final_answer声称保存了research.md，实际没有写入。

冻结代码agent_server.py按三个不同有证据卡的来源开放writer，读满6次关闭inspect。因此从本次受信状态可重建：最终既不能继续读，也未开放写入，只剩用于拒绝的final_answer。该字段仍允许任意非空文本，错误的完成话术能通过响应schema；外层因缺immutable runtime proof正确拒绝接受。

这次并未复现原HTTP500。此时eligible=false，最后一代输出上限为256、仅final分支；不能据此证明上一轮复杂写入schema/2048上限下的原生解析问题已修复。原生HTTP请求、模板和模型兼容修复继续以实际回执为依据，本提案不修改它们。

## 最小修改方向

1. 在既有受控选页schema中联动“剩余读取次数”和“仍缺的不同来源数”。从已确认、在当前代可见的证据卡计算覆盖，含当前已确认待提升的页；仅在剩余额度恰好需要保留给未覆盖来源时，限制inspect的source_id为尚未覆盖且可用的来源。仍由8B选择相关来源和起始行，不预写事实、固定页序或代写文稿。不足以满足门时如实拒绝。
2. 未确认写入时，final_answer只能表示明确的未交付/拒绝；只有原写入、读回、可信proof和ACK准入通过，才允许完成确认。保留合法拒绝分支，不能把不足三个来源的情况强制推进writer，也不能靠字符串里出现文件名计交付。
3. 生成与独立重放共用同一有限schema构造，避免live与replay分叉。优先复用OpenJarvis现有inspect/write SDK工具及原JSON schema机制，不新增agent框架或变更模型。实际改动范围须在新候选计划审查时按源码确认。

## 离线验证设计

- 复现本次S1连续读取的状态：尚有两次读取但仍缺两个来源时，不能继续同源耗尽预算；读取新来源后，剩余一次仍能补齐第三来源。
- 覆盖计数只认已确认且带卡的页；无卡页、不可用来源、未确认/不可见页、重复来源和模型自报不能扩大写入资格。
- 有余量时保留合法同源补读；不得把三个来源误写成全部来源，也不得把覆盖数当作原题事实覆盖通过。
- 生成schema、重放预期schema及有效派发参数严格一致；旧成功分支、合法拒绝、输出扫描、预算、一次write和ACK保持。
- “未写却声称已保存”必须拒绝或转为明确未交付结果，不能通过completion或生成虚假runtime proof；保留原始失败证据。
- 使用现成MockTransport/SDK测试验证，准备独审与当前字节核验通过后才另行提出一次明确分配的实跑；历史339/706不替代新候选检查。

## 不变条件与验收

仅当前qwen3-8b-uncensored，永不14B。原题四来源、三来源事实门、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒及现有token/实体上限保持。保护七身份、语音链路和生产服务不操作。新隔离候选、新证据根，不改旧候选/旧失败；不延长截止，不给失败补跑，不从诊断文本拼接research.md。

真正验收仍要求research.md实际写入读回、可信运行证明、ACK、事实/引用/原题覆盖独审和清理；修复导航可达性本身没有交付信用。当前E02仍0/3，T2/Owner未通过。
