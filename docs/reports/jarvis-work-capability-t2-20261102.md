# UltimaAgent 工作能力 T2 停点报告

- 原单：`wo-ultimaagent-20261101-0021`；阶段键：`wo-ultimaagent-20261101-0021-t2`。
- 结论：**T2 BLOCKED / 真实验收 FAIL**。第 2/2 轮有界修复已用，未进入 T3—T5，原单未完成、无 Owner 验收或产品冻结。
- 最终被测源码：`10fec033343444168cf6fc9d41b63552a6b82727`。失败检查点名称为 `ultimaagent-work-capability-t2-blocked-20261102`；推送/远端解析以 checkpoint 回执为准。
- 新实现保留在 C 盘受管工作区 `codex/jarvis-work-capability`；原 H 盘产品代码与运行服务尚未切换。

## 最终用例结果

| 用例 | 最终候选的新鲜结果 | 验收结论 |
|---|---|---|
| E01 三材料生成文档 | 三轮 CLI0/succeeded；控制器重开全部文件、重算哈希与 15 项源码输入；三事实完整且无新增事实 | PASS 3/3 |
| E02 公开资料研究 | 第一轮 CLI2/needs_attention；SDK 搜索 1 次，GET 4 次，3 成功、1 项真实可选候选 HTTP404；模型报告参数错误，之后写出的文件还有无依据事实 | FAIL，立即停止 |
| E03 当前选区改写 | 此最终候选未启动；早期真实窗口诊断及焦点/选区负例保留，但不能冒充最终候选三轮通过 | NOT STARTED |
| E04—E08 | T3—T5 未启动 | NOT STARTED |

首轮模型把 `facts` 发成字符串，工具要求数组并返回失败。模型随后自行改成数组写入了研究文件；先前的报告工具错误仍按已批准规则阻断完成，没有因后续文件存在而清除失败。

控制器重新打开实际研究文件，原始字节 SHA256 为 `744796ff9991b9694499de09ba2d377c069c3357bf7f3d4364ed5fca82864cca`。正文声称 AgentManager 可以初始化 OpenAI；本轮真实抓取的 `agent-manager.ts` 第 52—54 行仅有未实现 TODO 和警告，没有创建 OpenAIProvider。部分 README 功能又归到了 AgentManager 引用之下，因此语义/来源验收同样失败。

文件仍保存在 `data/evidence/jarvis-work-capability/T2/20261102-10fec03/e02-round-1/outputs/39d8c368-396e-44cf-807d-f359a7abce08/research.md`，没有编辑产物来纠正答案，也不声称回滚。它不是合格交付物。

## 已完成的接线及审查

工作上下文采用按需采集、可信启动清单、窗口/进程创建身份、选区和时效核对，仅支持批准的标准 Edit 控件。真实替换后独立读回窗口；伴随文件还必须与实际替换内容全等，仅容许 CRLF/LF 差异。无条件焦点锁或通用桌面控制均未承诺。

研究模式复用已安装 OpenJarvis SDK1.0.4 的 ToolExecutor、ToolCall、ToolRegistry、WebSearchTool、HttpRequestTool、NativeReAct 和文件工具。搜索与有界 GET 成为模型起草之前的必要步骤；本轮不可变来源目录绑定正文、哈希和调用身份；模型通过结构化报告工具提交事实，后端仅绑定真实来源引用并委托 SDK 写文件。未新增 Agent 核心、检索引擎、工作流 DSL、依赖或 vendor 修改。

第一次独立审查发现选区 A/伴随文件 B 可分别验证成功的问题。修复 1 加入精确伴随一致性核验并经 fresh 独立复核。自然研究仍出现零 GET，修复 2 因此采用 SDK 必要前置及来源绑定；该代码也经 fresh 独立复核，未发现新的 Critical/Important。**代码复核通过不等于 T2 真实任务通过**，本轮仍以实际失败收门。

SDK WorkflowEngine 已作开源替代检查：其静态工具节点最后仍调用同一 ToolExecutor，无法省去动态候选与失败分类适配，故采用更窄的现有执行器接线。[研究执行补充契约](../specs/jarvis-work-research-execution-contract-20261102.md)记录了具体边界；冻结 r2 计划、契约、样本字节没有改写。

## 新鲜测试与历史准确性

最终候选覆盖测试 141 项、隔离旧工具兼容测试 8 项，合计 149 个不同测试身份，均为退出码 0、0 failure/error/skip，包含 T1 的全部 60 项身份。RED、中间失败和全部诊断轮次保留。8 项兼容运行有一条 anyio assert-rewrite warning；既有 voice-reference fallback 提示也保留，未更改语音配置来消除噪声。

旧兼容测试固定 H ROOT 的隔离缺口已在 T1 报告更正。此次 8 个原测试体不变，C 候选模块被明确预加载，测试 ROOT 指向本单证据沙箱，身份与 T1 逐项一致。原 T1 日志和不可变 tag 保留，不以补证抹掉旧运行事实。

非阻断已知项也保留：URL 正则会将紧邻的中文标点/说明吞入候选 URL，本轮第三个候选因此返回 404。该真实失败按精确调用身份标作可选探测失败；其他三个来源满足数量前提，但本轮仍因模型错误和事实不符失败。没有声称四个来源全部成功，也没有更改冻结句子隐藏这一问题。

## 证据、清理与状态

证据根：`H:/UltimaAI/UltimaAgent/data/evidence/jarvis-work-capability/T2/`。

- `controller-final-gate.json`：控制器物理读回、15 项源码摘要核对、真实失败原因及当前保护进程身份核验。
- `20261102-10fec03/final-stop.json`：全部原始路径、失败文件、实际调用、清理及停点。
- `fix-round-2/candidate-covering.xml`、`candidate-compat.xml`、`candidate-coverage-comparison.json`：149 项新鲜覆盖与身份对照。
- `review-e673e1f/`、`review-fix1-ad1621e/`、`review-fix2-10fec03/`：原意见、修复和独立复核，未覆写历史。
- `blocked-registration-readback.json`：项目与全局非可运行状态、Manager 权威刷新/独立读回，以及其他任务记录未变的证明。

原 brain 进程 492/37880 与语音进程 32856/18068 的 PID、创建时间和可执行文件在控制器最新读取中完全一致。自身候选 server/CLI/fixture 已退出；只清理了逐个证明 owner 不存在的本单专用 runtime 锁，保留旧内容和路径，不触动共享锁。无新录音、麦克风、播放、截图或生产代码切换。

项目队列将原单及 T2 阶段持久化为 FAILED（不可派发），全局工作流为 blocked。现有状态引擎的 BLOCKED 转换依赖实际重排队事件；API 修复次数已经在原单回执记录，不伪造重排队历史来满足该内部计数。T1 阶段仍为完成，其他任务记录不变。

## 后续决策材料

当前组合尚未满足高效可靠的研究交付，原因不能只凭一次结果归结为模型或接线的单一因素。现有 Ollama 接口已登记 `qwen2.5:14b`，SDK 也提供显式单次 model 参数。已准备[主脑受控对照提案](../plans/jarvis-work-model-comparison-proposal-20261102.md)，只比较同一失败样本、保持产品默认模型不变；该实验尚未执行。

停止依据为 [任务工作流 §4](H:/UltimaAI/_shared/paradigms/UltimaAI-任务工作流范式.md:90) 的“同一阶段进入有界修复（默认上限 2 次）”及本轮已登记边界。后续需要 Owner 对主脑策略/额外对照范围作明确处置，不能通过第三轮标题或新原单重置失败记录。
