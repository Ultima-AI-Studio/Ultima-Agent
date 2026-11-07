# E02 写入阶段原生 HTTP 500：后续诊断提案

状态：PROPOSAL_ONLY。原工单 wo-ultimaagent-20261101-0021 / T2，当前产品候选 e40a55b40c223181040dbb6a09d0c4d2da5026cf。本文件不分配新的真实用例，不授权自动重试或修改冻结产品。

## 本例已经确认的事实

唯一实际 run 5e6ea89c-8e47-43a6-9480-7a11d72cabf5 用完本次分配。6 次确认读取依次为 S1:26、50、74、98，S2:20，S3:25；诊断中的 eligible_source_ids 为 S1/S2/S3。前 5 页已通过后续响应确认可见，第 6 页仍是 confirmed、未 promoted。第 7 次原生 chat 请求收到 HTTP 500，没有可信写入、ACK 或 research.md；产品公开回复为“本次研究未交付。”。

请求实体 31270 字节，SHA-256 f2fa2d8c6520f04ac22ed4563d66b722fb1686e5dab6cf4680daba62d8c786f1。send_reserved=true、transport_failed=true、validated_response=false；失败正文 downloaded/inspected/admitted/retained 均为 0。该诊断快照尚余 227.192952 秒，读取使用 6/6、原生请求 7/8。它证明 HTTP 错误发生，未证明 grammar、输出耗尽、上下文或运行器中的某一个根因。

冻结源码 src/brain/agent_server.py 的 exchange 在非 2xx 状态后立即拒绝；generate 会把已确认且未 promoted 的待处理页面纳入该代次资格判断。结合六读和三来源，可以重建该代次具备 writer 分支与 2048 输出上限，且不再有 inspect 分支。这是源码和受限回执的推导；完整请求正文没有保留，不能把推导写成捕获到的请求正文，也不能宣称模型已经确认阅读第 6 页。

## 建议顺序与最小范围

1. 先只读核对当前候选生成的 writer schema、SDK 请求契约、固定本机原生接口和现有错误证据获取路径，明确哪些事实可由封存材料直接确认、哪些仍缺失。重建物另存并注明“重建”，不能补入旧实际证据。
2. 如现存材料不足以判断原因，先提出最小诊断补充设计：只围绕写入阶段和对应原生错误，在原响应与总字节、时限、隐私边界内保留必要证据。当前“非 2xx 正文不读取”是冻结契约，任何变更必须明确列出并独立审查；不能悄悄放宽或把未经校验的错误内容当作模型回复。
3. 只有确证兼容缺口后才做针对性修改，并以离线负例/成功路径验证其行为。新候选必须保留来源预算联动、固定未交付终态、真实写入/ACK/事实引用门。
4. 需要新请求时，另准备该候选的具体入口与绑定，明确分配一例后才执行，随后独立复核首个结果。当前单例及结果复核额度均不重复使用，失败不自动重跑。

## 保持的边界与交付标准

仅当前 qwen3-8b-uncensored 与原摘要；原题、四来源、至少三来源证据门、CLI1/search1/GET4/inspect6/write1/ACK1/nativePOST8；service260/client300/root275/cleanup310/seal315 秒、context16384、messages+schema32768/entity49152 字节、原 256/2048 输出上限保持。无 UI、音频、生产服务启停、升级、安装或 14B。七保护身份和全部旧失败继续保留。

本例 HTTP 500 不能由调大预算、降低覆盖门或接受虚假完成来消除。E02 的通过仍要求真实 research.md、可信运行证据、写入读回、ACK、逐事实/引用及原题覆盖、原时限、清理和独立结果 PASS；当前为 0/3，T2/Owner 未通过，旧候选 E01/E03 信用不迁移。

证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-coverage-controlled-preparation-20261107-r1。结果以该根 review/result-inputs/result-manifest.json 和 independent-result-review.json 为准；本提案不是验收记录。
