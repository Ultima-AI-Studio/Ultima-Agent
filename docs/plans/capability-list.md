# 能力清单 L0–L10（Capability List）

- **版本**：v1.0 · 2026-10-16
- **性质**：规划文件（与 `docs/specs/registry.md` 能力注册互为镜像：本文件管"要建什么"，注册表管"已建什么"）
- **状态说明**：待建 / 建设中 / 部分迁移（引用 legacy-topo 按 M7 显式声明）

| 层 | 能力 | 关键内容 | 状态 |
|---|---|---|---|
| L0 | 终端四 IO | 语音进/出、文字进/出 + 渲染 + 网络协议（薄壳，不承载智能） | 待建（win 壳起步） |
| L1 | 意图理解 | 意图识别 + 隐含补全（今天=本地日/Top10/默认不打断） | 待建 |
| L2 | 领域知识与技能注册 | 每域内容清单、技能注册表（skill-dispatch） | 部分（注册表已建） |
| L3 | 执行与外部接入 | 数据源/设备/多模型/知识检索；key 不卡死四层 | 待建 |
| L4 | 编排与组合窗口 | scene-orchestrator、组件树 DSL、三层组装、尺寸自适应 | 待建 |
| L5 | 表达与总结 | 汇报三规则（结论先行/异常优先/按需下钻） | 待建 |
| L6 | 输出呈现 | 渲染器（薄壳）、语音汇报状态机（CV3） | 待建 |
| L7 | 交互循环 | 对话调整/征询/确认/任务队列管理 | 待建 |
| L8 | 行为约束与受控执行 | 安全/越界/凭证/解冻裁决（智能 vs 写死）、权限矩阵 | 待建 |
| L9 | 记忆与自学习 | 工作/声明式/程序式 + 反思、设备档案与环境档案 | 待建 |
| L10 | 范式引擎 | 7 环流程强制、范式检查（交互前完整走流程） | 已建（LangGraph 底座） |
| L10+ | **任务工作流范式（G-TASKFLOW-001）** | **所有任务统一走「登记→计划评审→执行→独立审计→有界修复→验收→冻结」；执行端无关（Codex/DeepSeek/未来模型=可替换执行适配器）；规划/开发/独立审查分离；越界 fail-closed；缺 tag=闭环未完成** | **2026-10-29 已登记为标准基础能力（m28）** |
| L10+ | **UltimaManager 任务控制面（m29）** | **全系任务管控：工单编号核发（G-WO-NAME-001）、全局队列主表登记（G-DISPATCH-001 自主推进版下为可选监督/审计工具）、接管/来源/授权与前置核验** | **2026-10-29 已登记为标准基础能力（m29）** |

## UltimaManager 任务控制面登记（2026-10-29，m29）

- **权威源**：`H:\UltimaAI\UltimaManager\docs\INDEX.md` + `sync/product.json` + `tasks/queue/index.md` + 全局主表 `_shared/queue/global-queue-index.md`
- **性质**：UltimaAgent 标准基础能力之一（组件注册表 `ultima-manager` + 能力清单 m29）——全系任务控制面工具，不是唯一派发中枢（G-DISPATCH-001 自主推进版生效后为可选监督/审计工具）
- **状态**：wo-manager-v01 已冻结（OWNER_RELEASED_AND_FROZEN，tag `wo-manager-v01-frozen-20261029`），不阻塞产品推进
- **职责边界**：编号核发（G-WO-NAME-001）/ 全局主表登记 / 接管·来源·授权·前置核验 / 正式编号核重登记
- **Agent 侧承载**：`src/brain/orchestration/`（L10 范式引擎）+ `src/brain/loop/`（m01 派发/接续回路）+ `src/brain/guardrails/`（m19 越界闸门）

## 任务工作流范式登记（2026-10-29，G-TASKFLOW-001）

- **权威源**：`H:\UltimaAI\_shared\paradigms\UltimaAI-任务工作流范式.md`（v1.0，Owner 拍板建立；镜像 UltimaDocs `docs/shared/paradigms/`，tag `gtaskflow-001-registered-20261029`）
- **性质**：UltimaAgent 标准基础能力之一（组件注册表 `task-workflow-paradigm` + 能力清单 m28）——不是新的规划项，是跨产品强制的任务处理工作流
- **执行适配器**（可替换，不改变工作流）：Codex CLI（当前默认，细则见 Codex-外部执行端调用范式 v1.5）/ Codex API / DeepSeek API / 未来模型
- **实战验证**：UltimaManager 工作流（plan → plan review → develop → audit → bounded repair → approval → frozen）全量 239+120 复绿；自审计哨兵正确拦截未登记写域并闭环
- **Agent 侧承载**：`src/brain/orchestration/`（L10 范式引擎）+ `src/brain/loop/`（m01 主脑决策回路）+ `src/brain/guardrails/`（m19 越界闸门 / m21 审计留痕）

## 已识别缺口（Top 阶段教训 → Ultima 必补）

1. **L1/L5/L7 显性化**：Top 没有独立的意图层/表达层/交互循环层——补。
2. **L8 解冻裁决**：不可商量（安全/协议/宿主边界）→ 硬编码；可商量（风格/延迟/个性化）→ 智能体自决。裁决表随范式冻结。
3. **voice-trainer**：音色训练环境与模型接线（CV3）独立成能力。
4. **设备建模**：NAS/传感器/空调档案 + 可控性判定（device-cluster）。
5. **环境认知**：硬件/磁盘/文件/应用扫描（启动即熟悉）。

## 借鉴点映射（调研详见 docs/research/github-research.md + github-research-ultima-tools.md）

| 借鉴 | 映射能力 |
|---|---|
| OS-Symphony 架构（domain/context/exec/status + Search-as-a-Tool） | L1/L2/L3/L10 |
| OS-Copilot FRIDAY | L2/L9 |
| OpenUI（defineComponent + Zod） | L4/ui-kit |
| Home Assistant Assist（设备接入·任务工程） | 设备层/L3 |
| Open Interpreter / Goose / OpenClaw（CLI 沙箱执行） | L8 |
| Glances / LibreHardwareMonitor（硬件/系统监控数据） | 环境认知 |
| shadcn/ui（技能给编码智能体消费） | ui-kit/L4 |
| VP0/tessl/emil-kowalski/Mico/ChatGPT dots（动效） | L4 动效/motion-director |
| **Google A2UI（声明式 UI 协议，预批准组件目录）** | **L4/ui-kit 组件树基底（建议直接采用）** |
| **Pipecat / LiveKit（实时语音编排管线）** | **L0/L6 语音进出（建议采用 Pipecat）** |
| **Copilot Agent Skills 开放标准（skills/SKILL.md + gh skill）** | **L2 技能注册（对齐开放标准）** |
| **pywinauto（MS UI Automation）** | **L3/环境认知 本机操作执行通道（直接采用）** |
| **HA 实体模型（QNAP/Synology/TrueNAS 集成）** | **设备层 设备档案=entity 概念** |
| **Cognee/MemLayer/agentmemory/Mem0/Zep/Letta** | **L9 记忆底座（选型对比）** |
| **CrewAI / LangGraph / agentkanban** | **L4 编排状态管理参考** |
| **OpenJarvis / Open Felix / Personal Jarvis / GPT4All** | **对标：本地助手功能面 + 本地模型通道** |
| **Grok Bot 0.18（b-nnett/grok-bot-0.18-reconstructed）** | **L3 Codex 直连执行端（s6-codex-plugin 已抄入：凭证+401 刷新+SSE+工具循环）** |

## s6-codex-plugin 抄入登记（2026-10-27）

- **来源**：b-nnett/grok-bot-0.18-reconstructed（只读参考，archived）
- **抄入**：`src/brain/exec/codex_provider.py`（CodexProvider + make_codex_executor）+ `tests/test_codex_provider.py`（16 项）
- **功能**：读 `~/.codex/auth.json`（chatgpt 模式四字段校验）→ Responses API 直连（`chatgpt.com/backend-api/codex/responses`）→ SSE 流式 → function_call 工具循环（maxSteps=8）→ usage 累计 → 401 自动刷新回写 → 六字段 execution_report（与 external_executor 同构）
- **接线**：`BrainLoop(executor=make_codex_executor())` 注入位预留，默认不切换 s5 DeepSeek
- **红线**：Codex 执行走 M19 裁决；token 仅内存不落日志；工具调用 M21 留痕；只抄 Codex 分支（不抄 Cursor/OpenRouter/Electron/Docker/云端 box）
- **验证**：venv-openjarvis 下全量 184 项 OK（16 项新增全绿，无回归）
