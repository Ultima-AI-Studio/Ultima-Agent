# UltimaAgent 工作能力改造 T1 文件交付链

- 原单：`wo-ultimaagent-20261101-0021`；阶段执行键：`wo-ultimaagent-20261101-0021-t1`。原单继续开放，T2—T5 与 Owner 最终验收尚未完成。
- 结论：T1 技术门 PASS。独立审查：spec compliance PASS、code quality Approved；Critical 0、Important 0、Minor 3。
- 被测试和审查的代码：`2e0682c2d4b0a79928fd3d8ad2325d017015f7fd`；基线 `6b70aa6f9223829682ec995fecc7d51952a3e717`。阶段检查点仅补充本文和证据，产品源码与被测试候选一致。
- 实施位置：受管工作区 `C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent`，分支 `codex/jarvis-work-capability`。原 H 盘运行代码与服务尚未切换。

## 实际交付

新增 WorkService、受限文件工具适配和成果核验器，通过已有 `/ask` 的显式 work 模式以及 `cli --work` 进入同一执行服务。可信输出根来自服务启动配置，每个请求由服务器生成 UUID 目录。请求文本、上下文和模型参数不能扩大写域。

实际复用 OpenJarvis SDK 1.0.4 的 Jarvis.ask_full、NativeReAct、ToolRegistry、ToolExecutor 和 FileWriteTool/FileReadTool。两个文件别名在无参构造时捕获不可变请求绑定，线程安全 ledger 留下真实调用；核验器仅消费本轮写入记录，重新打开文件比较内容并计算原始字节 SHA256。模型声称“已保存”、旧文件、工具失败或读回不符均不能得到 succeeded。

保留旧 `/ask` 和 ask_agent 行为。工作失败不转为云聊天，不因风格检查重新执行写入。隔离服务有独立端口、锁、SDK 运行存储，不启动生产 HUD/update 线程。本阶段工作工具仅四个，不开放真实任务队列、记忆或子代理工具。

## 验证与全部尝试

| 验证 | 新鲜结果 |
|---|---|
| 实现前 RED | 缺失 work_service 导致预期失败；原日志/JUnit 保留 |
| 同一候选集成与兼容回归 | 60 passed，0 failures、0 errors、0 skipped；实际 NativeReAct、别名与 SDK 文件工具，仅在确定性测试替换推理输入 |
| 初始真实模型三轮 | 本机代理误转发 Ollama，三轮失败并准确返回失败，原日志保留 |
| 同一候选 warm 三请求 | 候选子进程设置 NO_PROXY=localhost,127.0.0.1 后三轮成功；共享候选进程和配置根，单请求 UUID 目录独立 |
| 严格三轮 | 每轮新进程、新 runtime 根、新 outputs 根；CLI 均退出 0，产品均 succeeded |
| 外部成果核验 | 控制器和独立审查者分别重开三份文件，哈希一致；三事实完整，无新增事实 |

严格三轮实际服务 PID 为 10004、38788、19836，均通过自己持有的子进程句柄清理，端口监听随后为空。原 brain 进程 492/37880 与语音进程 32856/18068 的 PID、创建时间和命令在前后完全一致。8756 是原服务端口，不被当作进程号处理。

第二、三轮模型使用 Markdown 标题、列表和字段冒号，原逐行完全相等 oracle 因此返回 false，使编排脚本最终退出 1；这不是产品 CLI 退出码。冻结 r2 明确允许措辞变化并按事实验收。保留原判定，另记完整正文语义审查，没有为筛选逐字相同输出而重跑。另一次严格脚本在首轮后因空监听列表被误当 PowerShell 错误而中断，记录同样保留。

## 证据与独立审查

证据根：`H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T1/native-api-20261101T155037Z`。

- `candidate-regression.log/xml`：候选提交之后的 60 项新鲜回归。
- `strict-per-round-roots-r2/round-1..3/receipt.json`：每轮真实模型/工具轨迹、实际身份、根目录、CLI 结果、外部字节读回和清理。
- `controller-strict-readback.json`：控制器独立读回与完整正文判读。
- `review/t1-independent-review.md/json`：独立代码与产物审查，绑定代码候选。
- `strict-orchestration-notes.json` 与全部原始轮次：失败和 oracle 限制保留。
- 阶段目录中的 `t1-gate.json` 与 `evidence-manifest.json`：门禁和证据摘要；重建基线仍需 T0 的运行输入快照与清单。

## 后续与边界

三项 Minor 随下一阶段相关文件的增量处理并回归：样本 oracle 接受合法标题/字段格式且继续拒绝缺事实与新增事实；文件工具公布的 mode schema 收窄为已实现的 write；未知 HTTP 字段的拒绝回执保留请求关联身份。

NO_PROXY 仅作用于候选子进程，未更改全局代理、模型或原服务。启动中的 voice-reference fallback 提示属于既有语音配置噪声，不是回归测试警告。无新依赖安装、vendor 改动、录音、麦克风、播放或截图操作；未改真实记忆和无关用户文件。

T1 不宣称窗口控制、连续任务、取消/恢复或语音工作验收已经完成。下一阶段 T2 仍须 E01—E03、受控资料回放和真实联网、专用测试窗口和焦点变化负例全部通过；之后才能进入 T3。

## T2 发现的历史兼容测试隔离补证

后续逐项比对回归时发现，T1 的 `test_agent_tools_extend.py` 八项旧测试固定 ROOT 为 H 盘项目，并注入 H 源码搜索路径，合成队列/记忆使用 H/data 下的 TemporaryDirectory。因此不能将那八项历史运行描述为全部限制在本单证据目录内。它们操作的是合成临时存储；不等于生产队列或真实记忆变更。原测试文件及 agent_tools_ultima 模块在 T0 快照、H 和 C 三处的字节哈希完全一致；原日志和不可变 T1 tag 保留。

T2 已用证据目录内的隔离包装重跑八个原测试体，绑定 C 候选模块实际路径并逐项对照身份，八项通过；最终候选的 149 个不同测试身份覆盖了原 T1 全部 60 项。补证见 `data/evidence/jarvis-work-capability/T2/t1-compat-isolation-correction.json` 及 T2 阶段报告。没有删除未知历史目录，也未改写旧回执；T2 自身的研究真实验收仍失败，不能以该补证宣称整体完成。
