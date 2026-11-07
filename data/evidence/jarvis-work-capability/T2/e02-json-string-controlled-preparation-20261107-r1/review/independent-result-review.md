# 独立结果复核：FAIL_CONFIRMED

审查者 root-independent；候选 6d758d9c3961f156a062e349ec4a949e2ee7a9a9；run bc216374-f59c-4967-99f2-ded53a4ea49d。结果清单 SHA256：3a3bda952dbbfaf6c10537e3634549a9321248fcf2eb62bb2875001b538aca3b。

本次首个唯一结果确认失败。验收信用 0，E02 0/3、T2、Owner 均未通过；本例实际额度与结果独审额度均已消费、剩余 0，不重试。旧 E01/E03 信用不迁移。授权原问答、release grant/consumed、唯一调用回执与独审登记相互绑定。byte-readback 的 review_remaining1 是独审消费前快照，不能作为当前剩余额度。

独立逐项重算 56 个结果成员、234 个准备成员、31 个实际 seal 成员、1579 个输入绑定、旧 N15 准备189/结果56 个成员的 SHA-256，均无差异。准备独审、当前模型与控制器绑定一致。publication-readback 记录项目62109ad4032bdce452f1d4f910aab79d2f9211b6、镜像091d1dcbdbae53c48e5f65fff4740378624cda60。这里只读回执，不运行 Git。344 项离线检查只属于历史准备。

CLI 题目与冻结 corpus.query 完全一致，runtime prompt 保含原题及四个固定来源，另附交付指令与来源目录。模型仍为 qwen3-8b-uncensored，digest 6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330。原限额 cli1/search1/GET4/inspect6/write1/ACK1/POST8、service260/client300/work275/cleanup310/outer315 秒不变。唯一入口调用起止 12:02:02.224568Z—12:03:19.923657Z，77.70079229999101 秒；这不是按时交付通过。

根结果与 terminal FAIL，产品 failed，公开文字“本次研究未交付。”，错误 Invalid native research response。research.md 数量0、artifacts为空、write_confirmed=false、ack_confirmed=false、final_answer=null。因此文档交付、事实引用和原题覆盖不能通过或验证。

搜索1、GET4成功。5494字节失败诊断的 SHA256 ba5a830752dc9e4663e800a5b24fe1aa13b09c2960ae807695d591c91dc46304 与导出和产品引用一致，binding SHA256 与 request/session/task 三元组独立核对一致。诊断有6次 confirmed reads、5页 visible、eligible S1/S2/S3，无S4读取页；上层tool_results inspect0不能解释为没有读取。应用POST7、completed7，不是服务器实际推理启动次数。

最后 generation7/chat/receipt20：HTTP200，transport_failed=false，validated_response=false；请求33390字节、SHA256 5df7beb8defa890600d66d64a0b438b32dfa85bd0bea2f2c3ca52379188a6da4；downloaded/inspected/admitted/retained各8328。8328是计数，不是已保存响应正文。剩余209818649微秒，reads6/6、POST7/8；尚有时间不构成继续请求授权。

源码 work_research.py:561-572 的 checked_native_response 合并检查外层字段集合、模型、done/done_reason、message键/role/content、token计数、duration和created_at类型。agent_server.py:428-436 在外层JSON解析后调用该函数，随后才进行ChatResponse及内层JSON/schema校验。该稳定错误支持“外层原生响应校验拒绝”的范围；无法从标签分辨具体谓词。不能认定截断、JSON解析失败或内层schema错误，也不能用HTTP200证明输出合法或语义成功。失败导出未保存最后响应正文，本复核未读共享日志或回填冻结凭据。

原cleanup PASS；owned六身份在清理记录消失，closeout无匹配身份，18799在记录核对点关闭/无监听。closeout中PID35956已有其他身份，因此只断言原身份不在，不断言该PID为空。七保护身份与边界及closeout完全一致；这些是离散核对点，不是连续存活证明。

旧e40a55b的run5e6ea89c-8e47-43a6-9480-7a11d72cabf5及HTTP500失败证据仍原样保留。本次HTTP200只描述本次观察，不能宣称整个原生兼容永久修复。

下一步最小离线调查方向：静态逐项映射 checked_native_response 的拒绝谓词、输出cap和现有诊断字段，明确未来独立授权修改若要定位原因所需的最小有界谓词证据。保持本失败包不可变，不补猜响应正文，不自动重跑，不换14B，不放宽预算。本次未运行测试、目标导入、模型、网络、runtime查询、UI、音频或服务操作，仅exclusive-create本JSON和MD。