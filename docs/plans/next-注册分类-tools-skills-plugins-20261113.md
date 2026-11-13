# Next · 注册分类：Tools / Skill / 插件

> 状态：分类提案（待 Owner 确认）｜ 日期：2026-11-13
> 依据：R-11（基础能力 12 项）、R-15（两级结构）、R-17（六小模块组合）、R-25~R-31（Console 管理职责与清单归属）
> 上位：`docs/plans/plan-ultimaagent-next-rebuild-20261113.md`、`docs/specs/next-双域分离与开工设置规范.md`

---

## 一、先定判定标准（否则分类全凭手感）

| 类型 | 判据（四条全中才算） | 反例（不该注册成这个） |
|---|---|---|
| **Tool** | ①单一动作 ②确定性输入输出 ③无多步判断 ④可被编排直接调用 | 「帮我做一份方案」（多步、要判断）→ 不是 Tool |
| **Skill** | ①多步流程 ②带领域知识或判定标准 ③可复用、有触发条件 ④有验收口径 | 「读一个文件」（单步）→ 不是 Skill |
| **插件** | ①第三方或开源组件/通道适配 ②有独立生命周期（可装/可停/可换） ③可被替换而不改调用方 ④可能带外部依赖 | 「写日志」（内部实现）→ 不是插件 |
| **都不注册** | 模块内部实现：状态机、缓存、配置加载、日志、错误包装、探针上报 | 注册了只会让注册表膨胀，M1 查重失效 |

**命名规范**：`tool.<域>.<动作>` / `skill.<域>.<流程>` / `plugin.<类别>.<名>`（例：`tool.memory.recall`、`skill.voice.calibrate`、`plugin.tts.cv3`）。

---

## 二、逐模块分类表

### ① 感知与交互（终端 4IO / 输出呈现 / 交互循环 / 表达与总结）

| 子内容 | 归类 | ID / 说明 |
|---|---|---|
| 输入采集（麦/键/触） | Tool | `tool.io.capture` |
| 输出分发（屏/声/回执） | Tool | `tool.io.emit` |
| 锚点更新 | Tool | `tool.ui.anchor_update` |
| 面板渲染 | Tool | `tool.ui.panel_render` |
| 文本总结（多步改写/按风格收束） | Skill | `skill.text.summarize`（R-33 拍板：归 Skill，不归 Tool） |
| 交互循环（一次完整的收→判→做→回） | 不注册 | 模块内部主循环，不是可调用单元 |
| 渲染器（A2UI / WebView） | 插件 | `plugin.render.a2ui` / `plugin.render.webview`（可替换） |

### ② 语音（KWS / ASR / TTS / CV3 音色训练）

| 子内容 | 归类 | ID / 说明 |
|---|---|---|
| 唤醒状态查询 | Tool | `tool.voice.wake_status` |
| 说一句（TTS 播报） | Tool | `tool.voice.speak` |
| 听一次（录音→转写） | Tool | `tool.voice.listen_once` |
| 参数校准（跑基线、对齐阈值、出报告） | Skill | `skill.voice.calibrate`（多步 + 有验收判据） |
| CV3 音色训练（采样→训练→试听→冻结） | Skill | `skill.voice.cv3_train`（流程 + 冻结门） |
| KWS 引擎（sherpa-onnx） | 插件 | `plugin.kws.sherpa` |
| ASR 引擎（whisper / funasr 等） | 插件 | `plugin.asr.<name>` |
| TTS 引擎（CV3 / SAPI 兜底） | 插件 | `plugin.tts.cv3` / `plugin.tts.sapi` |
| 降噪/回声消除（APM） | 插件 | `plugin.dsp.apm` |
| 七态状态机 | 不注册 | 内部实现 |

### ③ 理解与决策（意图理解 / 领域知识与技能注册）

| 子内容 | 归类 | ID / 说明 |
|---|---|---|
| 意图分类（判性质：产出型/交互型） | Tool | `tool.intent.classify` |
| 路由决策（派给谁） | Tool | `tool.route.decide` |
| 能力清单查询（能不能做） | Tool | `tool.registry.lookup`（与 ⑤ 共用一个查询入口） |
| 意图黄金集评测（建集→跑分→定阈值） | Skill | `skill.intent.eval`（多步 + 阈值验收） |

### ④ 宿主、执行与编排（执行与外部接入 / 编排与组合窗口 / Console 任务中枢 / 进程治理）

> 桶名 2026-11-13 由「④ 执行与编排」扩为「④ 宿主、执行与编排」：把 **Shell 侧进程治理**（七道闸/任务点位，详见基线 §十五）与 **Middleware 执行端**并入本桶；Update/Lifecycle **不在此桶**，归「交付」模块。

| 子内容 | 归类 | ID / 说明 |
|---|---|---|
| CLI 执行 | Tool | `tool.exec.cli_run` |
| MCP 调用 | Tool | `tool.exec.mcp_call` |
| 计划单步推进 | Tool | `tool.plan.step` |
| 任务注册 | Tool | `tool.task.register` |
| 任务状态查询 | Tool | `tool.task.state` |
| 回执上报 | Tool | `tool.task.report` |
| 任务派发全流程（登记→派发→跟踪→回执→收口） | Skill | `skill.task.dispatch` |
| 方案拆解（产出型任务先出方案） | Skill | `skill.plan.decompose`（外脑侧执行） |
| 独立审计（对照验收清单复核） | Skill | `skill.audit.review` |
| MCP 客户端适配 | 插件 | `plugin.mcp.client` |
| 执行端适配（Codex / DeepSeek / 本地 8B） | 插件 | `plugin.executor.codex` / `.deepseek` / `.local8b` |
| Console 能力清单展示 | Tool | `tool.console.list_caps` |
| Console 启停/装卸 | Tool | `tool.console.toggle` |
| Manager 任务实施状态 | Tool | `tool.manager.task_status` |
| 探针发射与回收 | Tool | `tool.probe.emit` / `tool.probe.close` |
| 安装编排（装→校验→登记） | Skill | `skill.console.install_flow` |

### ⑤ 治理与约束（行为约束 / 范式引擎 / 权威源）

| 子内容 | 归类 | ID / 说明 |
|---|---|---|
| 规则校验（这次动作允不允许） | Tool | `tool.policy.check` |
| 权威源读取（取当前规则文本） | Tool | `tool.source.read` |
| 范式组装（把规则拼进运行时提示词） | Tool | `tool.paradigm.compose` |
| 规则评审（新增/修改规则走评审） | Skill | `skill.policy.review` |
| 冻结审核（四件对齐判定，出 PASS/FAIL 结论） | Skill | `skill.freeze.audit`（**由外脑执行**，R-34） |
| 冻结打 tag（审核 PASS 后执行、落地在本地） | Tool | `tool.freeze.tag`（**由主脑执行**，R-34：牵扯本地的动作都归主脑） |
| 规则文件本体 | 不注册 | 数据而非能力 |

### ⑥ 记忆与自学习（记忆与自学习）

| 子内容 | 归类 | ID / 说明 |
|---|---|---|
| 写入（仅接受 Core 已裁决的请求） | Tool | `tool.memory.write` |
| 检索 | Tool | `tool.memory.recall` |
| 习惯读取（每次交互必读） | Tool | `tool.habit.read` |
| 习惯更新 | Tool | `tool.habit.update` |
| 习惯抽取（从一轮或多轮对话提炼习惯） | Skill | `skill.habit.extract`（多步 + 防污染判据） |
| 温度分层调度（热/温/冷） | 不注册 | 内部实现（存储后端决定介质） |
| 存储后端（sqlite / 文件 / 向量库） | 插件 | `plugin.store.sqlite` / `plugin.store.file` / `plugin.store.vector` |

### ⑦ 外部能力（外脑 / 顾问）

**口径（R-61）：外部能力不是一个模块，是一个容器，下辖三个抽屉。** Skill 与插件都不再单独成层。

| 抽屉 | 子内容 | 归类 / ID |
|---|---|---|
| **能力库 Skill** | 产品策划 / 代码开发 / 方案撰写 / 代码审计 / 知识采集 / 顾问咨询 | Skill：`skill.plan.*`、`skill.code.*`、`skill.write.*`、`skill.audit.*`、`skill.kb.collect.*`、`skill.advise.consult` |
| **插件 Plugin** | 外脑通道适配、执行端适配器、MCP 客户端、采集浏览器档、存储后端 | 插件：`plugin.provider.<name>`、`plugin.executor.<name>`、`plugin.mcp.<name>`、`plugin.kb.browser`、`plugin.store.*` |
| **模型库 Provider** | 已配置好的大模型 API 列表（云端）＋ 可选本地第二模型 | 登记项（非能力）：`provider.<name>`；**主脑不在模型库列表**（受基线 §十六 管、**不可被 skill 指派**；**主脑可下拉替换**见 §二十三） |

- **能力 × 模型是绑定关系，不是能力本身**：一对一、手动下拉换绑、无主备无自动切换；在途任务等本轮结束才切换（基线 §十八）。
- **预置 vs 扩展**：预置能力随安装包自带（**可停用、不可卸载**）；扩展能力由用户添加（可删）。
- **分配不注册**：主脑 ↔ 外脑指派由 `tool.route.decide` 依据能力的 `data_scope` 决定，指派动作本身不是能力。

### ⑧ 交付（Update / Lifecycle）

| 子内容 | 归类 | ID / 说明 |
|---|---|---|
| 检查更新 | Tool | `tool.update.check` |
| 应用更新 | Tool | `tool.update.apply` |
| 安装/升级/卸载执行 | Tool | `tool.install.run` |
| 发版验证（篡改拒收→回滚→自检） | Skill | `skill.release.verify` |
| 更新源适配 | 插件 | `plugin.updatesource.http` |
| 安装器 | 插件 | `plugin.installer.inno`（外部工具，不写进 src） |

---

## 三、插件分档（R-35）

| 档位 | 判据 | 插件 | 数量 | lifecycle（“任一可停”仅适用于 `disableable`） | 停用后是否可降级 |
|---|---|---|---|---|---|
| **必装** | 服务基础能力或交付本身 | `plugin.kws.sherpa`、`plugin.asr.<name>`、`plugin.tts.cv3`、`plugin.tts.sapi`、`plugin.dsp.apm`、`plugin.render.a2ui`、`plugin.render.webview`、`plugin.store.file`、`plugin.store.sqlite`、`plugin.updatesource.http`、`plugin.installer.inno` | 11 | `runtime_required`：`plugin.kws.sherpa`、`plugin.asr.<name>`、`plugin.tts.sapi`、`plugin.dsp.apm`、`plugin.render.a2ui`、`plugin.render.webview`、`plugin.store.sqlite`；`disableable`：`plugin.tts.cv3`、`plugin.store.file`、`plugin.updatesource.http`；`install_time_only`：`plugin.installer.inno` | `runtime_required` 停用后对应语音/渲染/存储主链不可用且健康门必须失败；`plugin.tts.cv3` 可降级 SAPI，`plugin.store.file` 停用仍走 SQLite，更新源停用后只失去在线更新；安装器仅安装/升级/卸载时需要 |
| **选装** | 只服务外部能力接线，或按条件启用 / 含风险能力 | `plugin.mcp.client`、`plugin.executor.codex`、`plugin.executor.deepseek`、`plugin.executor.local8b`、`plugin.provider.openai`、`plugin.provider.deepseek`、`plugin.provider.ollama`、`plugin.store.vector`（按记忆量阈值启用，v1.0 不装）、`plugin.host.windows_mcp`（含风险，默认关闭） | 9 | `disableable`：本行全部插件 | 全部可停：无外脑时只走本地 8B；无向量库时用 SQLite 全文；无 Windows MCP 时不能用电脑控制类能力 |

---

## 四、数量与结构结论

| 类型 | 数量 | 主要分布 |
|---|---|---|
| Tool | 约 23 个 | 集中在 ①③④⑤⑥⑧，全部是「单动作、可编排」 |
| Skill | 约 11 个 | 脚本类流程：语音校准/训练、派发/拆解/审计/冻结审核、规则评审、习惯抽取、文本总结、顾问、发版验证 |
| 插件 | 20 个（必装 11 / 选装 9） | 集中在 ② 引擎层、⑥ 存储层、④ 执行端/MCP、⑦ 供应商、⑧ 更新/安装、宿主层 |
| 不注册 | 若干 | 状态机、缓存、配置、日志、探针上报、主循环 |

**三条纪律**：

1. **能用开源绝不自研**：14 个插件里 11 个是现成开源（sherpa/whisper/APM/sqlite/向量库/Inno Setup…），只有执行端与供应商适配需要自写壳。
2. **插件必须可关**：任一插件停用后产品仍能跑（语音降级到 SAPI、存储降级到文件、外脑缺失只走本地）。
3. **Skill 由 Tool 组成，不反向依赖**：Skill 只能调 Tool，不能直接调另一 Skill（防链条失控）。

---

## 五、待 Owner 确认的点

1. ~~「文本总结」归 Tool 还是 Skill~~ → **已定：Skill**（R-33）
2. ~~冻结签证的签约主体~~ → **已定：外脑审、主脑打 tag、落本地**（R-34）
3. ~~插件是否再分必装/选装~~ → **已定：基础能力必装、外部能力选装**（R-35）
4. ~~`plugin.store.vector` 是否第三档~~ → **已定：归选装，按记忆量阈值启用**（R-36）
