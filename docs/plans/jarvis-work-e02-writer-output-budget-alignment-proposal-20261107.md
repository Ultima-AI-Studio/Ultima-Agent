# E02 写入输出与既有预算对齐：后续最小提案

原单 wo-ultimaagent-20261101-0021 / T2；冻结候选 d860b2ab4e4d9974e33c96472e4ea15abb807280。本文只提出后续离线补修范围，没有修改产品或分配新的实际用例。

## 已确证的本例边界

唯一实际 run 72d7d71b-39a9-455a-b0b4-8823b3f24c00，用户分配 call_92c748ab12e24ba7a135ebd26783263f。第7次原生请求返回 HTTP200；受限 v4 回执记录 reason=done_reason、done=true、done_reason=length、eval_count=max_tokens=2048、prompt_eval_count=8888、content_chars=3798。请求33395字节，SHA256 bc2299bb736f1c1b425c4289f454c47da1bb97d2621624f9a10ce4f03e74bb58；响应接收9663字节，SHA256 c03d2a9b4e4f7cef38e562c067aade3c5eff9c778cc2803e2b7a37917b9a4597。诊断5879字节，SHA256 6665c1d8a43fca043ac9f2e525b5d7f70136b1ad59787b293393be218cc35f79，结果manifest 9cc9e1c9c38a5f23b9e5a0d72b52bd2558a720c99abea8b11148abde483523d6。

这确定了本例原生响应的首个拒绝谓词。完整响应正文未保留，不能认定某个字段、重复文字、转义、思考文本或内部JSON结构耗尽了额度，也不能追认旧候选失败同因。本例没有write、ACK或research.md，E02仍0/3；独立结果结论与事实边界以同根review/independent-result-review.json为准。

## 静态发现与建议范围

当前agent_server.py已按阶段设置num_predict，写入资格开放时上限2048、其他阶段256。work_navigation.py的v3_research_phase生成通用原子事实及来源指令，没有接收本次实际输出上限。work_research.py的独立重放调用同一提示函数。既有原生format、num_predict、SDK、安全扫描与重放机制均可继续使用。

建议在新隔离候选中只做以下离线补修：

1. 将本次实际输出上限传入共享阶段提示函数，在已具备写入资格的阶段明确：预算覆盖整个JSON对象与所有来源章节，使用紧凑JSON、简短标题和准确的原子事实；保留回答原题所需的信息及引用，避免复述原文或加入契约外的说明。
2. 生成与独立重放使用同一函数、同一实际上限，核对请求实体及messages/schema预算。预计产品触点仅work_navigation.py、agent_server.py、work_research.py及对应既有回归测试；若发现需要改变接口或接受域，先提出新范围。
3. 定点RED→GREEN验证输出上限正确传递、256/2048阶段边界、同一生成/重放提示、伪造预算或旧提示拒绝，以及完整写入/ACK与length拒绝路径。原事实、来源、证据配对、页读取、scanner和失败“未交付”回归继续保持。
4. 保留既有严格schema的章节/事实范围及三来源门，不预设每源仅一条事实，不删除原题的架构与开源接入要求。模型仍自行选择事实和证据；离线替身只能验证机制，不能作为当前8B已交付的证据。

此项提示对齐是针对已确证输出耗尽的有限干预，尚未证明能让当前8B在原预算内交付。不得把length视为成功，不得补括号、截取或修补模型正文后写入，也不得增加token、请求数、时间或切换模型。若原题在这些条件下仍无法完成，应如实保留失败，而不是缩小原题换取通过。

## 执行与验收边界

后续范围仅最小离线补修、必要回归、独立准备审查及新候选入口绑定。准备就绪后另行请求明确的一例实际研究和一次结果复核；本提案不授权自动重跑。只用当前qwen3-8b-uncensored及原摘要，原题四来源、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8、service260/client300/root275/cleanup310/seal315秒、context16384/messages+strict32768/entity49152与原输出上限保持。

无UI、音频、生产服务操作、安装下载或14B；保留七保护身份、全部历史失败、旧候选与标签。最终仍以research.md、写入读回、ACK、原题事实/引用/覆盖、原时限、清理及独立结果PASS为接受条件。当前候选E01/E03未重新验收，旧信用不迁移，T2/Owner未通过。
