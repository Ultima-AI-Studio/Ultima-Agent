# Task 3 补充：直接用户消息的授权接线

主计划 SHA256 49cb8554759c1c6cea5346e49865f18d2c92f521f780092d9676957b281fab1e；同一原工单/阶段/单例范围。

已有 read_release 把 question_id 限定为 call_ 前缀。本次用户直接说“按建议的顺序继续推进”，不是工具选择回复；不能伪造 call ID 或要求用户重复已给授权。

写域：N9/code/entry.py、N9/tests/test_entry.py、N9/inputs/direct-user-decision.json。只扩展授权来源的表示，单例数量、截止、候选/manifest/review 绑定、消费规则不变。

先 RED：本次直接消息记录的唯一 decision_id 和完全相同 answer 应可通过既有 read_release 其余所有校验；相似/空消息、错误标识、改动后的决策文件、旧调用及过期授权均拒绝。

实现：将用户原文、所承接建议、已接受范围（有界诊断/引用与覆盖修复、必要独审、准备 PASS 后一次当前8B原题四来源及一次结果复核、retry0）写入 direct-user-decision.json。decision_id 为 user-message:sha256:<该用户原文 UTF8 摘要>，该值只标识本会话人类原文，不声称是平台消息ID。文件 SHA 固定在 entry.py，封存入准备 manifest。读取后只在本例的 decision_id/answer 与固定文件完全匹配时接受直接消息；原 call_ 分支不变，零推理旧 grant 仍拒绝。不得把普通文件文字当作新授权；本文件只是对已见人类消息的工程绑定。

GREEN 后与入口完整回归、准备包独审一起核对。该补充不增加模型调用、不解除独审和运行准入要求，不授后续轮次或生产服务操作。
