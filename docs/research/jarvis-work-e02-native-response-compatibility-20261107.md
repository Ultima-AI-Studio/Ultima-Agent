# 当前 8B 原生响应兼容性只读核对

本记录由当前源码、当前模型元数据、一次只读版本/身份核对和固定版本官方源码组成；没有生成调用、重试、服务操作或新现场用例。

| 接缝 | 本地事实 | 上游依据与判断 |
| --- | --- | --- |
| 实际版本和身份 | verification/runtime-readiness.json：2026-11-07T08:29:29.501933Z，Ollama 0.32.15；原七保护身份匹配，11434归属原受保护PID；当前8B manifest摘要6d7230a9…c7f9330 | 当前核对点证据，不主张连续存活；未更新/重启服务。 |
| 模型模板 | research/model/metadata-readback.json：GGUF v3、Qwen3 8B Abliterated；内置模板4168字节、SHA256 a55ee1b1660128b7098723e0abcd92caa0788061051c62d51cbe87d9cf1974d8；manifest只有一个model layer | 按固定版gguf.h读取前5933038字节元数据，未读取tensor。整份5GB权重没有重新哈希，记录的blob digest来自既有manifest；文件stat读取前后相同。 |
| think | agent_server.py已有think=false；模板末尾在enable_thinking=false时生成空think块再开始正文 | llama_server.go的llamaServerChatTemplateKwargs把think.Bool传为enable_thinking。支持禁用参数，不支持“产品漏传禁用参数”的判断。 |
| format | 产品将严格schema经既有采样投影后传入NativeRequest.format；工具列表为空；stream=false、temperature=0 | llamaServerChatResponseFormat把JSON对象转为type=json_schema及json_schema.schema。接口形状相容；没有据此新增strict字段或删除约束。 |
| 原生执行路径 | 前例冻结日志显示llama-server task261及peg-native输出解析告警 | Ollama固定版llama_server.go区分Go模板/completion与GGUF/v1/chat/completions路径；本地单model layer和冻结日志支持后者。未逐字证明安装二进制等于上游源码。 |
| schema与响应解析 | 前例离线参考grammar转换通过，却在原生第七次响应失败 | 固定版LLAMA_CPP_VERSION为b10488；chat-auto-parser-generator.cpp同时组合schema grammar与reasoning/parser；chat.cpp的common_chat_peg_parse在不能消费预期格式时告警并抛错。离线Python参考转换不是原生C++解析证明。 |
| 状态回执缺口 | _ResearchTransport.exchange在异常前记录response.status_code、request摘要和计数；work_research_diagnostics._project未导出transport.receipts | 确证遗漏，可仅补诊断投影。原生错误正文当前不读取；本补修保持不读取。 |

前例独审结果为 FAIL_CONFIRMED，无 research.md。冻结补充日志中六次HTTP200后一次500，末代生成2048 tokens；局部内容伴随未闭合JSON、页文和think标记。它与本例时间及5个证据ID相关，但不是产品请求绑定的HTTP回执，不能反推出确切模板/schema/parser根因，也不能用作事实或文稿。2048未超出既定输出上限，不构成提高上限的依据。

当前可执行的最小修改只有“可信HTTP回执 → 失败诊断”接缝。未确证新的请求参数/采样契约不兼容，因此保持请求构造、模型、schema、原预算和完整严格校验。原生响应解析根因仍未解决；新增离线fixture不能代替下一次真实请求证据，也不能补造前例没有导出的回执。

固定版官方来源及本地SHA见research/upstream/provenance.json：
- https://github.com/ollama/ollama/blob/v0.32.15/llm/llama_server.go
- https://github.com/ollama/ollama/blob/v0.32.15/LLAMA_CPP_VERSION
- https://github.com/ggml-org/llama.cpp/blob/b10488/common/chat-auto-parser-generator.cpp
- https://github.com/ggml-org/llama.cpp/blob/b10488/common/chat.cpp
- https://github.com/ggml-org/llama.cpp/blob/b10488/ggml/include/gguf.h
