# 当前 Qwen3 8B 的 schema 兼容修复与真实验收结果

2026-11-02，原单 `wo-ultimaagent-20261101-0021`。**兼容缺口已修复、代码复核通过；真实研究任务仍 FAIL，T2 blocked。** 本次按用户确认继续当前 Qwen3 8B，没有切换或对照14B，T3—T5未放行。

## 本次实际做了什么

实际服务/推理事件的模型名为 `qwen3-8b-uncensored`，Ollama清单标为Qwen3 8.2B/Q4_K_M，并与已登记abliterated标签同digest。它不等同于已证明官方原版权重。只说明本单实际使用的模型身份，未改变生产默认配置。

确认已安装OpenJarvis的工具描述仅展示顶层参数，嵌套的facts数组类型、items和请求内source_id枚举未送入NativeReAct。原失败至少含明确接线问题，不能直接归因为8B能力不足。使用现有ToolSpec.description附上完整当前JSON Schema，保留vendor、参数字典、验证器、来源、renderer、权限、模型和验收门。

候选源码 `610005e61187463681c7499c0e8fbba399f0c2eb`，父提交 `afbbe3e4616d1f322ebc55705750014a4db2867f`。仅work_tools.py四行、test_work_research.py三十三行。原两次失败及blocked检查点保留；这是控制器明确的一次兼容例外，累计修复3=默认2+例外1，不重置工单、次数，不冒充Owner新增批准。

## 验证结果

| 项目 | 新鲜证据 | 结论 |
|---|---|---|
| 真实NativeReAct首条消息，3/5来源 | 修复前2例因缺schema失败，修复后2例通过 | 接口缺口已修复 |
| 相关覆盖回归及隔离旧兼容 | 143+8=151个独立测试身份，覆盖全部60个T1身份，0失败/错误/跳过 | PASS；既有警告保留 |
| fresh scoped代码审查 | I3 ADDRESSED，无新增Critical/Important | CODE PASS |
| 唯一实际E02 round1 | 当前8B/NativeReAct，真实search1、GET4：3成功、1个保留optional404 | 真实运行完成，但任务FAIL |
| 机械验收 | 首次report参数JSON末尾缺facts数组闭括号，标准json.loads在char2029同样失败；同次Agent后来成功写文件，但首错仍fatal | needs_attention，CLI2 |
| 语义验收 | 生成文档称AgentManager可用OpenAI初始化；S2实际52—54行是TODO/警告，没有创建provider | FAIL |
| 后续门 | 未进行第二次E02、E01/E03新候选三轮及窗口负例，未进入T3—T5 | 未放行 |

原旧facts:string错误本次没有复现；本次失败精确为非法JSON。原始inference_end记录finish_reason=stop，独立标准解析确认错误来自实际输出，不把它写成超时或仅SDK解析问题。一个请求内部的后续工具调用不是外层重跑；没有挑选后来的成功覆盖前面的失败。

真实写出的失败任务文件已由实现者、控制器和独立审查分别物理重开，2243字节与成功SDK FileWrite ledger一致，SHA256 `cd54c3471bbbe50caa3ca72708332e9321db36feb35f2b598a9fc74e7a5f50bf`。位置：`H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/20261102-610005e/e02-round-1/outputs/9b50bb05-4bb6-47d2-b96c-42fdf3229157/research.md`。产品artifacts=[]不代表没有副作用；文件按失败产物保留，没有编辑答案或声称回滚。

## 当前交付状态与接续边界

T0/T1先前技术门保持通过；本次没有重做它们，也不能把旧T1三轮冒充新候选完整回归门。T2现在仍blocked，原单未完成。151项测试与CODE PASS只证明所覆盖的接线和约束，不能替代真实工作的正确性。当前证据不足以证明开放任务成功率，也不足以断言换更大模型必然解决。

单次兼容例外已收口，不授权继续换提示词抽取成功、修更多问题或换模型。后续需要对结构化工具调用与事实来源约束形成新的明确处置，并绑定同一原单、当前源码、保留的失败历史与原验收条件。14B提案保留为未批准、未执行的备选，旧提案的10fec03基线不能直接当成当前候选试验授权。

项目T2索引EXECUTING→FAILED，全局blocked，Manager已独立读回；真实队列重入事件只有1次，不伪造事件凑BLOCKED枚举条件。FAILED不可派发；其他45项项目记录和其他全局行保持。原四个brain/voice/turn进程的PID、创建时间、可执行路径一致；本轮自有进程全退出，仅在确认owner已不存在后清理一个自身隔离runtime锁。没有录音、播放、麦克风或生产/KWS切换。

代码和元数据检查点计划名：`ultimaagent-work-schema-gate-blocked-20261102`；远端解析和镜像证明以本次checkpoint receipt为准，不把本报告当作推送成功证据。

## 可复核证据

- 诊断与一次例外裁定：`data/evidence/jarvis-work-capability/T2/schema-prompt-diagnosis/`。
- RED/GREEN/151回归、候选、真实运行放行及控制面停点：`data/evidence/jarvis-work-capability/T2/schema-compatibility-exception/`。
- 独立代码与实际产物审查：`data/evidence/jarvis-work-capability/T2/review-schema-610005e/`。
- 唯一实际运行、原始推理/工具记录、总回执及清理：`data/evidence/jarvis-work-capability/T2/20261102-610005e/`。
- 旧停点继续保留：[T2修复2/2历史](jarvis-work-capability-t2-20261102.md)。
