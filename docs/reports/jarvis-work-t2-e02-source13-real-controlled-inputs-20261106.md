# 当前8B真实研究首例：输入绑定检查点

原单 wo-ultimaagent-20261101-0021 / T2。上一轮零推理接线单例及独立结果复核PASS已完成。当前已完成真实研究首例准备的Task1：输入绑定与复用对账；真实运行入口和独立准备审查尚未完成，没有实跑或模型调用额度。E02/T2仍未通过。

## 本次完成

- 新输入清单绑定1544个文件，含当前候选269aca5的57份产品文件、当前8B摘要、原题四来源、E01/E03正式登记、七保护身份、零推理结果和独审，以及原真实研究harness和deadline ruling。
- 旧实际harness的31个产品文件与当前候选逐项对照，5个不同：work_context.py、work_service.py及三份相关测试。研究入口和SourceNavigation已经存在，不需要重写产品Agent。
- 旧harness有71个测试函数身份，已登记待保留；它仍指向旧候选且只核验5个保护身份，不能原样实跑。当前E01 helper具备7身份、parent/命令摘要与CIM精度规则，下一任务复用它。
- 14项输入绑定检查通过；RED的37个错误来自尚未实现的绑定接口（含参数子例），原日志保留。GREEN只导入标准库，没有SDK、产品、网络或子进程操作；固定测试runner自身只启动一个隔离测试解释器。
- 拒绝错误候选/工作区、官方或其他8B/14B、摘要漂移、改变原corpus、放宽预算、布尔冒充整数、缺失/变化文件、相对路径、五身份基线或把Mock接线计作真实研究。

输入manifest SHA-256：5badf78414d3cb6a13145b98dbc1e3fa0ce08e4e5f79fc2948244e2118f16121。证据目录：H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e02-source13-real-controlled-preparation-20261106。本地tag：ultimaagent-t2-e02-source13-real-inputs-20261106，仅标记输入检查点，绝非实际运行准入。

## 下一步

按计划Task2在新目录适配原实际研究harness，保持真实模型transport，只替换原受控搜索/GET，并用已有SDK产物做离线读回兼容验证。随后Task3连接原RootInvocation、完成离线负例与独立准备审查，再提出可审阅的真实8B单例执行包。保持原275/310/315秒时限、8次native POST上限及失败不重试。

E01同候选3/3和E03三正一负PASS保留。当前KWS、语音、生产服务及模型默认值未改；没有使用新实际运行/结果复核分配。远端push仍受此前自动审批blocked by policy阻断，本轮不重试或绕行。
