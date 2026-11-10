# T2 现有 Ollama 手动恢复与只读核验

工单wo-ultimaagent-20261101-0021。用户已授权一次恢复现有Ollama，工具启动服务被自动审批以`blocked by policy`拒绝，执行前即停止，助手启动次数0、自动重试0。用户随后确认“已手动启动Ollama”，由用户自己运行原ollama.exe serve；助手仅做只读核验。

2026-11-06北京时间11:24:07保存的恢复记录为PASS_RUNTIME_RECONCILIATION；12:01:58再次只读核验为PASS_READONLY_RUNTIME_READBACK：

- 原生服务版本0.32.15；当前qwen3-8b-uncensored:latest，digest `6d7230a923426bc1933879eb08a7dafc18e5fc0e7606c459ce98f16e0c7f9330`，本地manifest摘要匹配。
- 新Ollama PID5708，FILETIME134384089613599432；11434仅由此进程在loopback监听。绑定原可执行文件路径、父进程及命令摘要。
- 另外六个保护进程原身份保持：Brain17088/17136、ASR17916/36176、语音监听36004/35288。后查七个新基线身份均匹配。
- 官方语音只读状态ready/fresh/worker_ready/instance_lock_held均true，run_id仍为4bc8c05e36b246aa891e80e9ff865f72。没有现场音频功能重测。

恢复记录是新时点观察，不是原Ollama PID15264连续存活的证明。round3后的环境FAIL、旧快照及退出原因未知全部保留。只读检查没有下载、更新、推理、音频或新实际用例，不授予下一例authority。

恢复证据根：`data/evidence/jarvis-work-capability/T2/runtime-reconcile-20261106-after-round3/`。含restore-proposal.md、user-approval.json、manual-start-confirmation.json、restoration-result.json、protected-baseline-restored.json及原缺失观察。

后查收据：`data/evidence/jarvis-work-capability/T2/e03-source13-negative-20261106/verification/preparation-runtime-readback.json`。保护基线原恢复快照漏列展示字段created_utc；负例输入从已保存的FILETIME精确派生补齐并修正继承的旧candidate注释，7个核心进程身份字段没有变化，原恢复快照原样保留于history。该模式适配不改写原恢复证据。

项目仍为当前8B与候选269aca5：E03三正例3/3，负例待实际验证；随后同候选E01、8B E02。T2及后续T3—T5/Owner未通过。后续现场运行必须重新核验新鲜准入，不能把本报告当作永久健康证明。
