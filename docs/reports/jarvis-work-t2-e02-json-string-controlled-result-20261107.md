# E02 JSON 字符串候选：唯一实际结果与独立复核

候选 6d758d9c3961f156a062e349ec4a949e2ee7a9a9 的一例当前8B受控研究已经结束，独立结果 **FAIL_CONFIRMED**。本次未交付research.md，E02仍0/3，T2/Owner未通过。本次第7次原生请求返回HTTP200，随后被原生响应校验拒绝；这只说明本次未重现上一例HTTP500，不能宣称整体兼容已修复。

## 结果与确证边界

公开content为“本次研究未交付。”，status=failed，error=Invalid native research response。没有写入、ACK或可信成功runtime proof。六次确认读取依次为S1起行26/50/74/98、S2起行20、S3起行25；S1/S2/S3具备证据资格，前五页visible=true，第六页confirmed=true但visible=false。三来源资格不等于原题覆盖或事实交付；上层tool_results只返回search1/GET4，inspect0与私有诊断的六读分别记录，不相互替代。

源码已把稳定错误定位到src/brain/work_research.py:561-572的checked_native_response。该函数对字段集合、模型身份、done/done_reason、message结构/角色/内容、token计数、时长及created_at使用同一拒绝标签。现有证据不能判定具体触发了哪项；不能直接称为length截断、内部JSON、工具schema或模型能力问题。响应接收计数8328字节，不等于结果包保存了可复核的完整响应正文；失败私有诊断没有原生拒绝项。

## 请求、时限与保护

run bc216374-f59c-4967-99f2-ded53a4ea49d；用户明确分配 call_6f04750fa3644cc39ce356ff25b1ca6b。唯一入口调用1，retry0；2026-11-07T12:02:02.224568+00:00至2026-11-07T12:03:19.923657+00:00，外层77.700792秒。应用native POST7，完成7，服务器实际生成启动总数未测量。

最后generation7/chat/status200，send_reserved=true，transport_failed=false，validated_response=false。请求33390字节，SHA256 5df7beb8defa890600d66d64a0b438b32dfa85bd0bea2f2c3ca52379188a6da4；downloaded/inspected/admitted/retained均8328。诊断5494字节，SHA256 ba5a830752dc9e4663e800a5b24fe1aa13b09c2960ae807695d591c91dc46304。预算快照reads6/6、nativePOST7/8、剩209.818649秒，不能据此把失败用例升为计时PASS。原预算、当前qwen3-8b-uncensored及摘要、原题四来源保持。

原cleanup PASS，登记六个本例进程身份消失，18799关闭，日志关闭。七个保护身份在运行边界及之后只读核对点相符，仅代表核对点；不宣称连续存活。没有UI、音频或生产服务操作。旧N15 run5e6ea89c-8e47-43a6-9480-7a11d72cabf5的HTTP500失败和全部依赖封存保留，当前失败也不改写。

## 独立复核与接续

结果manifest 3a3bda952dbbfaf6c10537e3634549a9321248fcf2eb62bb2875001b538aca3b，56成员；独立结果复核SHA256 762f6483fa2dff866d1fd6c3ec7d24fb90c3997d37bead205785d6ba91fa2cf7。无产物，事实/引用/原题覆盖不能通过；接受信用0。准备344项及历史N16的781项不重复运行，不替代实际验收，旧候选E01/E03信用不迁移。

本次实际1与只读独立复核1均已消费，剩余0，不重试。后续提案jarvis-work-e02-native-response-rejection-diagnostics-proposal-20261107.md：先离线补原生响应拒绝的固定原因码和受限标量/摘要，再按确证原因做最小修改。冻结产品本轮不再修改，不放宽done_reason/token/事实/预算门，不换14B，不自动补发模型调用。新候选若需实际，仍须完成准备后明确分配单例。

项目与UltimaDocs的本地commit/tag和逐字节读回由verification/result-publication-readback.json记录。远端push此前遭自动审批blocked by policy，本轮不重试。证据根：H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/e02-json-string-controlled-preparation-20261107-r1。
