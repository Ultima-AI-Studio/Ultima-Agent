# E02 来源预算联动候选：唯一实际结果与独立复核

候选 e40a55b40c223181040dbb6a09d0c4d2da5026cf 的一次真实当前 8B 受控研究已完成，独立结果为 **FAIL_CONFIRMED**。本例没有交付 research.md，E02 仍 0/3，T2/Owner 未通过。读取预算与来源覆盖联动、公开“未交付”文案均得到本例证据支持；端到端研究仍被原生 HTTP 500 阻断。

## 本例观察到的变化

原预算仍为六次读取。实际顺序是 S1 的 26、50、74、98 行起页，随后 S2 的 20 行起页和 S3 的 25 行起页。诊断记录六次确认读取、S1/S2/S3 三个具备证据卡的来源。前五页 visible=true，第六页 confirmed=true 但 visible=false：后续请求失败，没有把该页提升为已通过响应确认可见。不能据此宣称模型已确认阅读第六页，更不能把来源资格当作已完成原题的事实覆盖。

旧例六读仅有 S1/S2，本例保留四次同源读取后，余下两次用于未覆盖来源，达到了三来源写入资格。冻结源码与可信前缀可重建第七代为 writer/未交付分支、无 inspect 分支，输出上限 2048；完整请求正文没有保留，这些属于源码重建。该请求实际返回 HTTP 500。

产品公开 content 精确为“本次研究未交付。”，status=failed、error=Research HTTP status。没有写入/ACK/research.md，也没有可信成功 runtime proof；私有 final_answer 为空。事实、引用和原题交付覆盖均不可按报告产物验收，零接受信用保留。

## 真实请求与预算

run 5e6ea89c-8e47-43a6-9480-7a11d72cabf5；用户分配 call_95815376c4ef4b3499fc52d9fdbdf0df；入口一次、重试零。执行区间 2026-11-07T10:53:00.674263+00:00 至 2026-11-07T10:53:59.095175+00:00，外层耗时 58.421717 秒。应用记录 native POST 7 次、完成 6 次；最后一次 generation=7、chat、HTTP500、send_reserved=true、transport_failed=true、validated_response=false。

最后请求实体 31270 字节，SHA-256 f2fa2d8c6520f04ac22ed4563d66b722fb1686e5dab6cf4680daba62d8c786f1。错误正文 downloaded/inspected/admitted/retained 均为0。受限诊断 SHA-256 cab42b1b7161f51cd38fdd8db085b1fec612410c453eab02b4304ea7a6936464，5481字节，branch=unvalidated_response。预算快照 reads_used=6/6、native_posts=7/8、尚余227.192952秒。该值排除了该快照下的时限耗尽，不能解释 HTTP500 的内部原因；短耗时不是计时验收 PASS。

上层失败 product.tool_results 仅含搜索1/GET4，没有已返回的 inspect 条目；六读次数来自绑定的私有诊断，二者分别保留，不能把上层列表的0误报成没有读取。未测量服务器实际生成开始总数，不用应用计数冒充。

## 独立复核、保护与保全

结果 manifest e0fc7084754d492d7166e219e2596b15f5f2562783721e9ca80a85c2c9168b5a，56成员；独立复核 3cc6b1eb5c31440658f306bbdd1e589210d8a7f4f874bc5cc98063cc7a181854，FAIL_CONFIRMED。准备 manifest 与342项离线检查只证明准备；产品746项是先前封存基线，本例和结果 reviewer 均没有重跑测试。旧候选 E01/E03 通过不迁移至当前候选。

原清理回执 PASS，登记的六个本例进程身份均已消失、隔离端口关闭、日志关闭。七保护身份在实际边界和随后只读核对点相符，不宣称连续存活。未操作 UI/音频或生产服务，未更换8B或原预算。旧实际91406fa9-5952-4e3a-99af-a94c8857c8d3及N14/N13/N12/N11封存保持，当前失败也不覆盖。结果复核为只读，无额外模型或实际调用。

## 接续

本次实际1与结果复核1均已消费，剩余0，失败不重试。下一步见 jarvis-work-e02-native-writer-http500-diagnostics-proposal-20261107.md：先核对写入阶段原生请求与可取得的错误证据，仅根据确证问题设计最小兼容修改。当前状态码和请求摘要不能证明 grammar/解析、上下文、输出或运行器中的任何单一根因。未取得新授权前不修改冻结产品或发起新模型请求。

当前结果和提案同步至项目 docs 与 UltimaDocs，本地 commit/tag/逐字节读回由 result-publication-readback.json 单独记录。此前远端 push 被自动审批以 blocked by policy 拒绝，本轮没有重试。证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-source-coverage-controlled-preparation-20261107-r1。
