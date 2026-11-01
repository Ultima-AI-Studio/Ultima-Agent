# UltimaAgent 工作能力交付实施计划

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task through the existing project queue. Steps use checkbox (`- [ ]`) syntax for tracking. Plan review and final technical audit remain independent sessions under G-TASKFLOW-001.

**Goal:** 将自然语言工作要求接入统一的工具执行、上下文、连续任务和结果核验链路，交付目标契约中的 E01—E08。

**Architecture:** 复用现有 OpenJarvis ReAct/工具/会话与 Ultima 编排、执行通道。工作请求统一进入智能体服务器；终端负责输入与呈现；先形成可交付文件的完整链路，再接上下文、持久状态和恢复。

**Tech Stack:** 当前 Windows/Python 执行环境、OpenJarvis、现有 Ollama 主脑、SQLite 会话、现有事件总线与产品宿主；Jarvis.ceo 作为已固定版本的组织方式参考。

**Spec:** [工作能力目标与验收契约 r2](../specs/jarvis-work-capability-contract-20261101.md)。用户已批准按序执行，原单 `wo-ultimaagent-20261101-0021` 已登记；r1 独立评审 REVISE 保留，本修订等待复核，T1 尚未开始。

## Global Constraints

- 保留用户已确认可用的 KWS 基线；本次不重选唤醒引擎。
- 不改变三层架构和单一主脑；不新增第二套 Agent 核心或并行工具注册表。
- 测试使用每轮隔离目录/会话库；不写真实任务队列、真实记忆或无关用户文件。
- 本地或云端模型共用工具授权与成果核验；保持现有 `/ask` 的 `query` 和回复字段向后兼容。
- 不改变现有暂停、Owner、冻结和发布门；正式执行前登记全局主表，遵守根规则的当前 WIP 上限。
- 技术阶段与 Owner 冻结分别报告；技术检查点 tag 使用明确阶段名，禁止提前打 `frozen`。

## Review Focus

1. 路径中包含空格、Unicode、大小写差异、相邻前缀目录、重解析点：只在批准目录内操作；归 T1。
2. 上下文抓取后用户切换窗口或改变选区：不能修改新目标；归 T2。
3. 两个会话都说“刚才那个文件”或记忆含外部指令：不能串任务或跳过记忆过滤；归 T3。
4. 写入已提交但响应丢失、进程恢复、取消与完成竞态：不能重放副作用或虚报回滚；归 T4。
5. 同一任务走文字/语音或本地/云端模型，工具授权和完成口径必须一致；归 T1/T5。

## 现状与实施决策

- 主入口为 `src/brain/agent_server.py::ask_once`，当前使用 `native_react` 和九个显式工具；`agent_client.py::ask_agent` 返回文本，缺少调用方可用的任务/成果结构。
- 当前 `ask_once` 在 `ask_full` 返回后补发工具事件，需把工作进度连接到真实执行时点。
- `interaction.py` 的云端聊天分支与本地工具路径分离，需要按工作任务统一入口。
- 会话与记忆基础已存在，但主入口使用 `context=False`，实际持久记忆写入需与 `MemoryWriteGate` 对齐。
- 采用“既有底座接通”的路线。整体移植 Mac 应用会扩大平台工作；另写任务核心会重复已有能力。若执行前证实底座接口不能满足某一用例，先提交该具体缺口再调整。
- T0—T5 是本次路线的局部步骤，不替换产品既有 M0—M6 里程碑。

## 接口与文件边界

T0 r2 评审冻结以下增量契约；它们是拟实现接口，当前代码尚未具备。实施 cwd 为 `C:/Users/Administrator/.codex/worktrees/jarvis-work-capability-longpaths/UltimaAgent`；解释器固定使用已核对的 `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe`，不向共享环境安装新依赖。

- `WorkService(output_root: Path | None, *, runner: Callable[..., dict])`：由可信服务启动配置构造；根未配置立即失败。服务端生成 UUID 请求目录，request_id/session_id 只作标识，不直接用于拼接路径。
- `WorkService.submit_work(query: str, *, request_id: str, session_id: str, context: dict | None = None, max_tokens: int | None = None) -> dict`：由 `src/brain/work_service.py` 接入现有 Agent。返回 `request_id/session_id/task_id/status/content/artifacts/error/tool_results`；失败原因是字符串或 null。每个文件 artifact 含绝对 `path`、原始字节 `sha256`、`verified` 及 request/session/task/call 四类关联身份。
- `ask_work(query: str, *, request_id: str, session_id: str, context: dict | None = None, max_tokens: int | None = None, server_url: str = AGENT_SERVER) -> dict`：客户端向现有 `/ask` 发送 `mode="work"`。服务地址只允许本机回环。保留原 `ask_agent(query, max_tokens=None) -> str` 和无 mode 请求的旧行为。
- 任务状态采用现有契约可映射的 `queued/running/succeeded/failed/cancelled/needs_attention`，状态转换和取消提交点在 T0 评审固定。`succeeded` 要求成果核验通过。
- 工作模式只列 `calculator`、`think`、`ultima_work_file_write`、`ultima_work_file_read` 四个工具；不把真实任务调整、记忆、技能写入或子代理工具带进 T1。
- 两个别名沿用 SDK ToolRegistry/ToolResult，不修改 vendor、不覆盖原注册名。SDK 以无参构造器创建别名：构造时捕获不可变 `WorkBinding` 与请求内线程安全 ledger，实例 execute 再调用 SDK `FileWriteTool(allowed_dirs=[request_root])`/FileReadTool。不能等到 execute 的工作线程里才读取调用线程 ContextVar；无绑定拒绝。
- SDK 当前丢弃 ToolResult.metadata；适配器将真实调用的身份、路径、写入内容和成功结果同步写入本轮 ledger，同时正常返回 ToolResult。`verify_artifacts(binding, write_candidates)` 在 `work_verifier.py` 只消费本轮记录并重新打开文件；不扫描目录或解析模型回复寻找成果。
- 未配置根、越界、工具失败、无本轮写入、读回失败或内容不符均不能 succeeded；状态不明进入 needs_attention，不重放副作用。合法 HTTP 处理的 ok=true 不代表任务成功。T1 不宣称取消或持久恢复已实现。
- WorkService 不走纯云聊天兜底，呈现/风格校验失败不重新执行 Agent。默认继续使用当前本地主脑；云聊设置不能改变工作工具与授权路径，未支持的工作模型明确报不可用。
- 现有 `/ask` 接受显式工作 mode 和身份字段，根字段不能扩权。任务查询和取消接口在 T4 前按现有 API/消息契约评审登记。
- `src/brain/cli.py` 新增 `--work --request-id --session-id --server-url --json`，与旧 --agent 分开；结构化工作非 succeeded 返回非零退出码。
- `agent_server.main(argv=None)` 新增可信启动参数 `--port --runtime-root --work-output-root --isolated`。隔离启动使用独立锁和运行目录，不启动生产 HUD/update 后台任务；默认旧启动行为保持。业务执行仍为同一 WorkService，不建立测试专用保存分支。

集成测试统一包含以下成果断言；各阶段补充其用例中的失败行为，而非只检查返回文本：

```python
assert result["status"] == "succeeded"
assert result["error"] is None
artifact = result["artifacts"][0]
assert Path(artifact["path"]).is_absolute()
assert artifact["verified"] is True
assert hashlib.sha256(Path(artifact["path"]).read_bytes()).hexdigest() == artifact["sha256"]
```

写入失败、读回不符或目标失效时断言 `status != "succeeded"`；不把该示例当作已经存在的可执行测试。

### T0 固定目标与现状

**Files:** 本计划、关联目标契约；新增 `tasks/queue/<按规范登记的正式工单文件>`；测试夹具目录 `src/brain/tests/fixtures/work_capability/`。

**Interfaces:** 消费用户需求、当前代码与两个来源仓库的固定版本；产出已评审的 R/E/T 对照、精确写域、测试输入和基线回执。

- [ ] 对照当前代码确认 E01—E08 每条是已有、部分接通还是缺失；历史报告只作为定位线索。
- [ ] 把样本文本、预期事实、受控网页资料、测试窗口和输出目录写成固定夹具；记录目标契约 SHA256。
- [ ] 记录当前 commit、依赖版本、主脑配置和 KWS 受保护文件哈希；核对上层方案与协议的实际版本归属，尚未进入版本管理的必要输入先建立快照与哈希。使用既有测试结果采集方式，不开启新录音。
- [ ] 按现有流程登记工单，写清目标/写什么/验收/禁止、依赖、预算和暂停门；独立计划评审绑定精确修订和哈希。
- [ ] 出口：全部 R 编号有 E 用例和阶段归属、每个阶段有写域与真实验收命令、无“待定后再写”的执行项。未达成不得开始 T1。

### T1 交付第一条完整工作链

**Files:** 新增 `src/brain/work_service.py`、`src/brain/work_tools.py`、`src/brain/work_verifier.py`；修改 `agent_server.py`、`agent_client.py`、`interaction.py`、`cli.py`；新增 `src/brain/tests/test_work_delivery.py`。本阶段不实现 T2—T5 模块。

**Interfaces:** 实现上述 `submit_work`/`ask_work`；复用 SDK 文件读写工具，在 Ultima 注册表中增加限域适配；由服务端读回核验产出。

- [ ] 先写 E01 失败测试：模型只说“已保存”、预放正确旧文件但本轮无写入、工具假成功/缺候选、写入拒绝、读回异常、写后篡改均不得成功；路径穿越、绝对越界、相邻前缀、重解析点、身份注入与根扩权必须拒绝，正常空格/Unicode/合法大小写可用。
- [ ] 运行 `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -m pytest src/brain/tests/test_work_delivery.py -q`，确认失败来自缺失工作链而非环境问题。
- [ ] 实现实际 Agent → 受限文件工具 → 独立读回 → 成果回复。沿用现有执行器，不用测试专用快捷分支代替产品路径；工作请求的本地/云端分支进入同一授权执行服务。
- [ ] 确定性集成测试使用实际 NativeReAct、实际注册别名、SDK 文件工具与临时文件系统，仅替换推理引擎输入；验证两请求经 SDK 工作线程执行不串绑定，工作失败不回退云聊或因风格校验再次写入。独立样本 oracle 必须能拒绝缺事实和新增事实，产品核验器不硬编码样本。
- [ ] 运行同一测试命令并验证旧 `/ask`/`ask_agent` 兼容性；再从真实产品文字入口完成 E01 三轮，外部读回每个文件。
- [ ] 出口：E01 全绿、绝对路径和内容核验可读回、执行失败不会被包装成成功；独立审查后记录技术检查点。

T1 回归命令的 argv 固定为共享解释器、`-m pytest src/brain/tests/test_work_delivery.py src/brain/tests/test_agent_server_sse.py src/brain/tests/test_agent_tools_extend.py src/brain/tests/test_interaction.py -q`，cwd 使用上述隔离工作区；回执记录实际退出码与 JUnit 路径。

三轮 live 从同一候选启动 `-m src.brain.agent_server --port 18757 --runtime-root <本轮证据>/runtime --work-output-root <本轮证据>/outputs --isolated`，再调用真实 `-m src.brain.cli --work --request-id e01-round-N --session-id e01-round-N --server-url http://127.0.0.1:18757 --json <固定E01请求>`。N 为1至3，每轮使用新隔离目录；固定请求和事实读取版本化夹具。外部进程重新读文件并核对原始字节摘要，再独立审查三事实与无新增事实，保留全部轮次。

### T2 接通当前工作对象与资料工具

**Files:** 新增 `src/brain/work_context.py`、`src/brain/tests/test_work_context.py`；修改 `environment.py`、`exec/channel.py`、`browser/channel.py`、`work_service.py` 及必要工具适配。外部平台依赖仅在 T0 已批准时加入。

**Interfaces:** `capture_work_context() -> dict` 返回窗口标识、标题、可用选区/页面、来源与采集时间；`validate_work_target(context: dict) -> bool` 在修改前检查身份与新鲜度。数据传入 T1 的 `context`。

- [ ] 写 E02/E03 及焦点切换失败测试：来源与正文对应；错误窗口/旧选区不得写入；不可读取时明确呈现缺失。
- [ ] 运行 `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -m pytest src/brain/tests/test_work_context.py src/brain/tests/test_work_delivery.py -q`，确认新增用例先失败。
- [ ] 优先接已有环境、浏览器与执行通道；仅补完成目标窗口/选区所需的 Windows 适配。按需采集，工具返回的网页/选区作为数据进入任务。
- [ ] 运行同一命令；在专用测试窗口完成 E03，在真实搜索与写入路径完成 E02；回放和真实环境结果分开记录。
- [ ] 出口：E01—E03 全绿，窗口身份、内容来源、资料引用和文件产出均有证据；冻结本阶段技术检查点。

### T3 接通连续任务与明确偏好

**Files:** 新增 `src/brain/work_sessions.py`、`src/brain/tests/test_work_sessions.py`；修改 `work_service.py`、`agent_tools_ultima.py` 的实际记忆写入适配、`memory/gate.py` 的必要接入；复用 SDK SessionStore，不修改独立底座源码。

**Interfaces:** 以 SDK `SessionStore.get_or_create/save_message` 为存储基础，保存任务与已核验 artifact 的关联；仅为当前会话选择工作对象。明确偏好写入统一经过现有过滤门。

- [ ] 写 E04/E05 失败测试：跨轮定位正确文件、不同会话隔离、同名多候选时不误写；合成密钥和外部指令不能进入长期偏好。
- [ ] 运行 `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -m pytest src/brain/tests/test_work_sessions.py src/brain/tests/test_work_delivery.py src/brain/tests/test_work_context.py -q`，确认新增用例失败。
- [ ] 在真实调用路径注入有界历史与当前任务，接通现有记忆入口；避免只创建会话 ID 却不参与推理和执行。
- [ ] 运行同一命令；通过新客户端连接及隔离测试服务重启验证持久化，生产语音进程保持不动。
- [ ] 出口：E01—E05 全绿，“刚才那份文档”可连续修改、跨会话不串任务、过滤覆盖实际写入；记录技术检查点。

### T4 完成失败处理 取消与安全恢复

**Files:** 修改 `work_service.py`、`work_sessions.py`、`work_tools.py`、`events/bus.py` 和 `events/journal.py` 的必要钩子；新增 `src/brain/tests/test_work_recovery.py`；按既有流程更新相关 API/消息契约。

**Interfaces:** 任务查询和取消接入既有服务；请求身份用于去重，真实工具执行回调发布进度。复用现有编排审计和任务状态，避免新增独立调度进程。

- [ ] 写 E06/E07 失败测试：响应丢失重试、写入前后终止、取消/完成竞态、迟到结果、工具返回成功但读回失败。
- [ ] 运行 `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -m pytest src/brain/tests/test_work_recovery.py src/brain/tests/test_work_delivery.py src/brain/tests/test_work_context.py src/brain/tests/test_work_sessions.py -q`，确认新增失败符合预期。
- [ ] 给重试分类：只读操作最多两次；有副作用操作先检查幂等记录和成果，状态不明时保留需处理状态。取消确认阻止后续提交，已完成动作如实记录。
- [ ] 接真实开始/结束/核验事件；运行同一命令，并在隔离工作进程中执行真实终止与恢复测试，读回文件与任务状态。
- [ ] 出口：E01—E07 全绿，失败不伪报完成，取消/恢复不重复写入；记录技术检查点。

### T5 从产品入口验收并交付

**Files:** 修改产品已有文字入口、`interaction.py`、`agent_client.py`、相关宿主状态呈现；必要时修改 `scripts/start-ultima-agent.ps1`、`scripts/ultima-agent-tray.ps1` 的服务接线；新增 `src/brain/tests/test_work_product_entry.py` 和阶段报告。

**Interfaces:** 各入口适配 `ask_work` 的结构化结果；工作进度、成果链接和失败原因取同一任务状态。保持已接受 KWS 的引擎、词表和参数。

- [ ] 写 E08 入口测试：文字与语音发送同一类工作请求并保留会话/任务身份；服务不可用时明确报失败；旧回复或错误成果不能被当成新结果。
- [ ] 运行 `H:/UltimaAI/UltimaAgent/tools/venv-openjarvis/Scripts/python.exe -m pytest src/brain/tests/test_work_product_entry.py -q`，确认新增用例失败后接线并重跑。
- [ ] 运行 T1—T5 全部测试命令及现有受影响回归门；在真实产品界面完成全部固定用例，核心模型任务连续三轮，不能用测试入口替代宿主入口。
- [ ] 按契约生成全部回执、轨迹和产出清单；外部读回文件，比较受保护 KWS 文件哈希，核验运行版本与候选 commit 一致。
- [ ] 进入独立技术审计；按既有最多两轮有界修复规则处理失败。Owner 现场确认语音工作任务与交付体验后才能记录最终验收。
- [ ] 出口：打实际冻结 tag 并核验远端解析，交付启动/恢复/回滚说明和已知限制；发布按现有独立发布门办理。

## 每阶段如何防偏移

实施者开工前读同一契约和本阶段任务；结束时提交“需求编号、变更文件、用例结果、真实产出、遗留问题、候选 commit”的回执。独立审查先看成果和目标覆盖，再看代码与测试。

任何必需用例失败、写域扩大、来源变化或依赖缺失，都留在当前阶段处理。新增能力先说明它解决哪个当前验收失败；与 E01—E08 无关的功能不并入本轮。历史失败保留，不能靠改测试预期或缩减用例获得 PASS。

## 本次规划交付与后续动作

当前原单已经登记，隔离输入已按哈希补齐，改造前文字接口/工具回归14项通过。r1 独立计划评审返回 REVISE；r2 纳入可信根绑定、SDK线程/metadata接线、真实文字入口、候选启动隔离及失败口径。保留原意见，复核精确 r2 摘要通过后只启动 T1；前序固定用例持续回归。
