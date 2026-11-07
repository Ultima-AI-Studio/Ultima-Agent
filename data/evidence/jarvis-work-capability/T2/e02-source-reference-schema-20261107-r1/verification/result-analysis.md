本次有限诊断 `CODE_OPERATION_REQUIRED` 的42字符错误摘要与候选中唯一的 `A code claim must name its exact operation` 抛出处相符（work_research.py:329–332）。它是复合条件：代码证据的 operation symbol 必须是长度受限、格式有效的标识符，并且以原规定的精确边界出现在 claim 中。

`resolve_v3` 对当前检查到的事实先验证引用已发行及来源归属（work_navigation.py:519–521），然后从可信卡片注入 kind/symbol 并调用事实核验（522–526）。因此本次已经跨过该条事实的固定目标、引用存在和来源归属检查，失败发生在随后的代码事实契约检查。不能据此声称所有后续引用和事实都通过。

具体 claim、operation、source_id 和 evidence_id 未导出，复合条件中究竟哪一项失败也未知；不能断言遗漏了某个函数名。没有 research.md，无法将本次记录为可交付研究，更不能用离线857项通过替代真实验收。本次结果不构成对8B一般能力的结论。

静态读回：code-operation-contract-readback.json；结果manifest SHA256 95abc1e0d527386e08aeed33a176310e6ef51996ad544da3c2fb3b024658cf4f。本分析只读取已保存结果和冻结代码，没有执行产品、测试、模型或新网络请求；最终归因以独立结果复核为准。

独立结果复核已确认FAIL_CONFIRMED（review SHA256 a9f95a05a75375fcd72fee5fff6be9fe3013a15ed9a7393e858082ecc6ad6e30）。两个阻塞项为没有研究交付文件，以及trusted export/END/资格witness不完整。外层耗时短不能替代合格时限证明。两项作为真实验收失败保留，没有在本单例内追加修改或重跑。
