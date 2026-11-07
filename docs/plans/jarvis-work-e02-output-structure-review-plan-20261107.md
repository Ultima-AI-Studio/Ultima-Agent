# E02 输出结构与交付方式只读审查计划

原工单：wo-ultimaagent-20261101-0021 / T2。对象为冻结候选 0421a54cab572be013c3f7ad562e86406bfe8e52，以及上一个候选 d860b2ab4e4d9974e33c96472e4ea15abb807280 的已封存失败。本计划对应用户“审查输出结构与交付方式，明确需要补充的截断证据，再确定代码改动”。

本轮由当前控制器做只读审查并记录提案，不冒充 root-independent 独立审查；不分配产品实跑或结果独审。上一例及其独审均已消费，失败历史保留。

## 目标与顺序

1. 重新核对两次原生拒绝回执及其封存哈希，区分已收到 HTTP 响应、原生校验、JSON 结构、工具调用、文件、ACK 和事实验收。
2. 从冻结源码追踪输出 schema、采样 schema、消息、响应验证、研究写入和 SDK 交付边界；核对本地已接入开源代码，不导入或启动产品。
3. 比较单次完整 JSON、增量组织、流式传输与最终文件提交的代价。用原预算计算可行性，不把“更短”或“生成到文件”直接当根因修复。
4. 列出最小充分的截断证据、采集位置、受限保存与拒绝语义，以及证据到代码改动的判定表。证据不够的改动只列为条件方案。
5. 报告、证据清单和当前状态本地提交、镜像、打 tag、读回。远端维持此前自动审批阻断状态，不重试或换通道。

## 不变量

- 当前 qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330；仅 8B。
- 原题、原四来源与完整事实/引用/覆盖/文件验收保持；E02/T2 仍未通过。三来源只是写入资格。
- CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/rootwork275/cleanup310/seal315 秒；context16384；messages+schema32768/entity49152 字节；原阶段输出上限 256/2048；retry0。
- 本轮 product_changes=0、actual_case_allocation=0、model_calls=0、independent_review_allocation=0。无模型、服务、UI、音频或外部请求操作。不触碰旧冻结包和 15 个无关改动文件。

## 写域与交付

- 新证据根：data/evidence/jarvis-work-capability/T2/e02-output-structure-review-20261107-r1/；只允许本轮范围记录、输入摘要、只读分析脚本、分析结果与本地发布读回。
- 本计划、对应 docs/reports/jarvis-work-t2-e02-output-structure-review-20261107.md、审查形成的 docs/plans/jarvis-work-e02-output-structure-diagnostics-proposal-20261107.md，及相同原工单/current-run/全局登记的审查状态；不重置真实执行次数或更改验收结论。
- UltimaDocs 对应 plans/reports 镜像与本地 tag；按精确路径提交，不批量收录其他改动。
- 验证以文件哈希、源码行号、原结果封存、预算算术和发布读回为准。本轮不为只读文档重复跑产品测试；离线分析不计真实验收信用。

验收：能说明“已知什么、缺什么、在哪采、什么证据才支持什么改动”，且未把第二次 length 拒绝推断成具体字段截断或模型能力结论。推理强度 high。
