# Codex 外部执行端调用范式

> **上位工作流（G-TASKFLOW-001，2026-10-29 用户拍板）**：本范式是[UltimaAI 任务工作流范式](UltimaAI-任务工作流范式.md)的**执行适配器细则**——Codex 是当前默认执行端，替换为 DeepSeek API 或其他模型时只改适配层，任务处理与下发工作流（登记 → 计划评审 → 执行 → 独立审计 → 有界修复 → 验收 → 冻结）不变。

> **G-DISPATCH-001（2026-10-28 用户明确批准自主推进版，优先于本文旧派发职责描述）**：各项目自主推进开发，由项目方直接调用 Codex 执行；不再要求经 UltimaManager 统一准入（Manager 改为可选监督/审计工具，不阻塞产品推进）。**必须遵守规范队列底线**：工单三段式 + DoR 六项（含开源替代排查）+ 全局主表登记 + WIP 上限 + 冻结门 + 打 tag 铁律 + 回执必报；禁止绕过规范裸跑。铁律总纲见 `Ultima-工程铁律清单.md`。下文 CLI 参数、提示词及回执示例供各项目方自主派发时使用。原验收、预算、暂停与 Owner 冻结/发布门保留。详见[项目接入与任务队列派发范式](UltimaAI-项目接入与任务队列派发范式.md)。

> 版本：v1.7 ｜ 状态：批准生效 ｜ 适用范围：Ultima 全系产品（UltimaConsole / UltimaRadar / UltimaGold / UltimaEngine / UltimaAgent / UltimaScan / UltimaSentinel 等所有挂 Ultima 前缀项目）及后续新项目
> 唯一权威源：`H:\UltimaAI\_shared\paradigms\Codex-外部执行端调用范式.md`（镜像：ultima-docs-repo `docs/shared/`）
> 依据：本范式由 2026-10-19 UltimaConsole v1.1-N6 实战（Codex 会话 01a15071）验证后固化；v1.1 新增任务路由标准（2026-10-19 用户拍板）；**v1.2 新增派发执行环境（静默 + 精简 CODEX_HOME，2026-10-28 修复 Codex 派发弹窗后固化）**；**v1.3 新增打 tag 铁律（§6.1，2026-10-28 用户明确要求：每个关键修改或更新必须打 tag，防止进度偏差导致开发倒退）**；**v1.4 G-DISPATCH-001 改为各项目自主推进调用 Codex（2026-10-28 用户拍板，Manager 不再作为唯一派发中枢）**；**v1.5 对齐 G-TASKFLOW-001：本文定位为执行适配器细则，上位工作流见 UltimaAI-任务工作流范式（2026-10-29 用户拍板：以后替换 Codex API/DeepSeek API 均走同一套任务工作流）**；**v1.6 新增登记同步强制（2026-10-31 用户明确要求"以后再参与任务下发一定要走 UltimaAgent 的登记接口，否则它读不到做了哪些任务/更新"）：派发与状态变更必须在全局主表登记后主动触发 Manager 权威刷新（RuntimeAuthority.refresh），使新工单/新状态进入 Manager 18766 可读范围（UltimaAgent HUD 任务队列读 Manager API 的 items+legacy）**；**v1.7 新增开源优先硬边界（2026-11-01 用户明确要求"能用开源就不自研"落盘为硬边界）：DoR 由五项升六项（§4 新增"开源替代排查已附"），回执与验收同步新增开源替代排查项，工单与派发 prompt 强制携带；铁律全文见 `Ultima-工程铁律清单.md`（G-OSS-001）**。模型/工具链变化时按 §8 维护更新。

---

## 0. 定位与角色分工

| 角色 | 是谁 | 职责 |
|---|---|---|
| 交互与请求端 | 用户及助手 | 澄清目标、记录工单与入队请求、只读观察，不独立派发开发 |
| 唯一控制管理器 | UltimaManager（**2026-10-28 起改为可选监督/审计工具**，不再作为产品推进前置准入闸门） | 可选：项目监督、独立审计、状态聚合；不阻塞产品自主派发 |
| 执行端 | Codex（`codex exec` 非交互会话） | 照工单逐 T 执行，每 T 自证 Gate 证据，输出标准化回执 |
| 门禁 | 用户 | 只在立项/方案/发布/大变更门介入，不逐行盯实现 |

铁律：**各项目自主推进开发，直接调用 Codex，并遵守规范队列底线（工单三段式 + DoR 六项 + 全局登记 + WIP + 冻结门 + 打 tag 铁律 + 回执必报）**；**开源优先硬边界（G-OSS-001）：能用开源绝不自研，自研/自写模块开工前必须附开源替代排查结论**；规划、开发和独立审查分离；只有人类能完成原规定的 Owner 验收、冻结和发布批准。**每个关键修改或更新必须打 tag（§6.1），防止进度偏差导致开发倒退。** 铁律总纲见 `Ultima-工程铁律清单.md`。

---

## 0.1 任务路由标准（用户拍板 2026-10-19，全窗口统一执行）

| 任务类型 | 路由 | 说明 |
|---|---|---|
| **项目产出型**：报告 / 方案 / 审计 / 代码 / 文档整理等可写成封闭工单的任务 | **经 Manager 准入后派 Codex** | 交互端提交标准工单和必要上下文 → Manager 核对来源/权限/资源/预算后入队调配 → 独立验收审计 → 保留原人类门 |
| **交互型**：实时问答、现场决策确认、用户偏好确认、门禁拍板、需要多轮对话澄清 | **豆包直做** | 强制转 Codex 会增加补上下文的往返，此类任务豆包直接处理 |

规则：
1. 用户提出项目报告/方案/审计等产出需求时，先转为 Manager 入队请求；不得直接启动执行端。用户明确要求的控制面规则记录与交互确认可由当前助手办理。
2. 工单质量决定产出质量：豆包派单时把约束、上下文、验收标准写全（交接载荷见 §5）。
3. **本路由对所有会话窗口生效（新开窗口与旧工作窗口一律执行）**，由主脑在派单时声明路由归属。
4. 不确定归属时：能写成封闭工单且验收可判定的 → 产出型派 Codex；需要用户在场决策的 → 交互型豆包直做。

---

## 1. 模型版本（2026-10-19 实测可用清单）

| 用途 | 模型名 | 说明 |
|---|---|---|
| 默认主力（主体工程/诊断） | `gpt-5.6-sol` | 本次 N6 排查实际使用，workhorse |
| 架构级/高复杂度 | `gpt-5.6-terra` | 备用升级档 |
| 快速机械任务 | `gpt-reserve` | 低配快速档 |
| 独立评审/批评 | `codex-auto-review` | 自审/生成批评模式 |

硬约束：
- **config.toml 默认模型 `gpt-6.1-sol` 已从账户移除（报 not supported）**，派发必须显式 `-m <模型>`，禁止依赖默认。
- 模型可用性以 `codex models` 实测为准；变更后由主脑更新本表并走范式登记（§8）。

---

## 2. 调用方式（Windows 已验证命令形态）

```powershell
# 派发执行环境（强制）：先设精简 CODEX_HOME，再执行（详见 §2.1）
$env:CODEX_HOME = 'C:\Users\Administrator\.codex-cli'
cmd /c "codex.exe exec -m gpt-5.6-sol --dangerously-bypass-approvals-and-sandbox - < tasks\queue\dispatch-<工单号>-prompt.txt"
```

- codex.exe 绝对路径：`C:\Users\Administrator\AppData\Local\Programs\OpenAI\Codex\bin\codex.exe`（登录版，auth_mode=chatgpt）
- 工作目录：**项目根**（如 `H:\UltimaAI\UltimaConsole`），prompt 文件用相对路径
- 会话模型：`codex exec` 非交互；会话 originator 必须是 `codex_exec`（仅归档工单+同步状态 ≠ 派发，必须真正触发 exec 才算派发）

### 2.1 参数铁律（每条都是踩坑结论）

| 规则 | 说明 |
|---|---|
| `- < 文件` 喂 stdin | 直接命令行传参会被当 stdin 卡死；必须把派发 prompt 写成文件用 `- <` 输入 |
| 显式 `-m` | 默认模型已失效（§1），不传必报 not supported |
| 沙箱 | 本机存在 helper 缺失 / SID 解析失败（`CodexSandboxOffline 1332`）时，配合用户完全访问授权使用 `--dangerously-bypass-approvals-and-sandbox`；有正常沙箱环境的机器不得滥用 |
| 后台执行 | 长任务用 `run_in_background` 挂起，轮询回执，不阻塞主脑 |
| **精简 CODEX_HOME（强制）** | 派发必须设 `CODEX_HOME=C:\Users\Administrator\.codex-cli`（该目录仅含 model 配置 + auth，**无插件 / MCP / notify / desktop**）。禁止用桌面应用配置 `~\.codex` 直接派发，否则 Codex 启动会拉起 desktop-commander / cua-repl / rea / xcodebuild 等 MCP 子进程并弹窗；队列引擎已在 `run_worker.py` 注入此变量，手工派发须自行设置 |
| **窗口静默（强制）** | Codex CLI 必须 ≥ **0.159.2**（官方修复 Windows 子进程弹窗，现装 **0.165.0**）。派发全程不得出现终端窗口：主进程用 `CREATE_NO_WINDOW\|DETACHED_PROCESS`（派发器已内置），子进程由新版隐藏启动。验证方法：派发后进程树可见窗口应为 0（EnumWindows + IsWindowVisible 巡检） |
| 登录版与 API 版 | API key（sk-proj-*）版受配额限制会 Quota exceeded，须用 ChatGPT 账号登录版；模型 `gpt-6.1-sol` 在 ChatGPT 账号下不可用，用 `gpt-5.6-sol` |

### 2.2 派发 prompt 文件（`tasks\queue\dispatch-<工单号>-prompt.txt`）必含内容

1. **引导索引**：首段强制引用 `docs/INDEX.md` —— "先读项目引导索引 INDEX.md，按其权威源地图定位规范，再执行工单"（INDEX 缺失=DoR 不满足，禁止派发）
2. 扮演声明：`Act as the Ultima coding executor`
3. 工单路径：`tasks/queue/wo-<工单号>.md`
4. 执行顺序：按 T0→Tn 逐条，Gate PASS 再进下一条
5. 证据落盘：每 T 记录 Gate 证据到 `docs/reports/stage-<阶段>.md` + `docs/reports/evidence/<阶段>/`
6. 回执字段：根因结论 / 产出路径 / 验收证据 / 越界声明（无=明确写"无"）
7. 临时文件：执行完由主脑清理（dispatch prompt 不入仓）
8. **开源替代排查结论（G-OSS-001，2026-11-01 新增）**：凡工单含实现/算法/自写模块，必须附"开源替代排查"结论（排查过的现成开源件及采用/弃用理由）；无自研=明确写"无"。格式见 `Ultima-工程铁律清单.md` §8

---

## 3. 队列方式（工单队列三件套 + 全局登记）

| 件 | 路径 | 职责 |
|---|---|---|
| 工单文件 | `tasks/queue/wo-<product>-<阶段>.md` | 三段式工单（模板 `_shared\templates\工单模板.md`），逐 T 可执行 |
| 队列主表 | `tasks/queue/<product>-queue-index.md` | **项目级唯一权威**：每张工单状态/任务数/前置冻结/验收门/closeout |
| 状态镜像 | `tasks/queue/queue-status.json` | `queue-status-gen.py` 生成：total/frozen/in_progress/blocked/wip |
| **全局主表（2026-10-19 新增）** | `_shared\queue\global-queue-index.md` | **全项目监察总表**：所有项目派 Codex 的工单必须登记一行（项目+工单+状态+冻结门+回执），看门狗巡检此表；只聚合状态不复制正文（防双源漂移） |

状态流转：`待准入 → 等待调配 → 执行中 → 配置验收 → 独立审计 → 技术阶段通过 → 原 Owner 门 → 已冻结`；技术阶段通过不等于自动冻结。

硬约束：
- **派单模型（2026-10-20 用户拍板）**：**一张工单 = 一次 `codex exec` = 一个独立进程/会话**（`dispatch-<工单号>-prompt.txt` 独立文件）；**禁止"一包多单"**（一个会话内串行塞多张工单）。工单内部 T0→Tn 仍在该进程内顺序执行。
- **WIP 双层上限（2026-10-20 用户拍板，替代全局 ≤2）**：**每项目执行中 ≤1**（同项目不并发，防抢改同一批文件）+ **全项目执行中进程 ≤3**（本机资源安全线）；**审计中 ≤1 不变**。跨项目工单可同时开独立进程并行。
- 前置冻结门：未冻结不进下一阶段；`mN-frozen` tag/阶段报告 `docs/reports/stage-mN.md` 缺失=冻结门未闭合
- 队列主表是唯一权威，queue-status.json 只是其镜像，改状态先改主表再重新生成
- **派单前必须先在全局主表登记**（项目/工单/状态三要素），禁止绕过全局登记直接派 Codex；没有本地队列的项目（Engine/Gold/Radar/Scan 等）派单时同步补建 `tasks\queue\`
- **登记后必须触发 Manager 权威刷新（2026-10-31 用户拍板，v1.6 新增）**：全局主表登记（派发/状态变更/收口）后，必须主动执行一次 `RuntimeAuthority.refresh(store)`（等价于服务启动导入，见 §9.1），否则 UltimaAgent/HUD 读不到新工单与新状态。Manager 的 `legacy_records` 是快照，仅在服务启动或存在候选 stage 的调度轮才刷新；只登记不刷新 = 界面侧读不到，视为登记未闭环。

---

## 4. 派单方式（DoR 就绪门，六项全绿才派）

1. **验收 Gate 可判定**：每条 pass/fail 有固定输入/唯一期望/证据位置
2. **无未决依赖**：前置冻结 tag 存在
3. **写入域已声明**：各 T 精确到文件路径
4. **推理强度已声明**：high 主体工程 / medium 规则 / low 机械
5. **禁止项已写**：每条 T 有明确"禁止"清单
6. **开源替代排查已附（2026-11-01 新增，G-OSS-001）**：凡含实现/算法/自写模块的工单，必须附"开源替代排查"结论（现成开源件名称/版本/采用或弃用理由），未附 = DoR 不满足，禁止派发。格式见 `Ultima-工程铁律清单.md` §8；无自研=明确写"无"

工单三段式细则（防 AI 自行发挥）：**文件**精确到路径 / **写什么**逐条可执行编号 / **验收**封闭清单全绿才过 / **禁止**明确不做什么。

---

## 5. 交接载荷与回执

派发即交接，必须携带：目标端（Codex）/ 工单引用 / 上一步结论与证据指针 / 本端边界清单（允许/禁止）/ 期望输出结构（回执字段）/ 指令 / 验收门。

执行端回执必报字段：

| 字段 | 说明 |
|---|---|
| 链路号/工单号 | 追踪标识 |
| 执行端 | 谁做的 |
| 完成状态 | 已完成 / 阻塞 / 已终止 |
| 根因结论 | 问题根因一句话（诊断类必填） |
| 产出路径 | 改动文件 + 报告 + 证据目录 |
| 验收证据 | 构建/连拍/像素测量/日志输出摘要 |
| 越界声明 | 无=明确写"无"；含未动范围（冻结 UI/未发布/未打 tag） |
| 环境声明 | 模拟器 vs 真机：真机未验证必须写"仅真机预期"，禁止冒充已验证 |
| 开源替代排查 | 本单自研/自写模块清单 + 每模块"为何不用现成库"说明（无自研=明确写"无"） |

---

## 6. 验收与闭环（Manager 组织，原 Owner 门保留）

1. 读阶段报告 `docs/reports/stage-<v>-<n>.md`：Gate 逐条核对（T0-C1/C2、T1-C1/C2、Tn 全 PASS）
2. 核证据目录 `docs/reports/evidence/<阶段>/` 存在且与报告路径一致
3. 技术验收与独立审计通过后记录阶段通过；需要冻结时，只有取得原规定的 Owner 批准和实际冻结证据后才能登记 `<tag>-frozen`，再生成状态镜像。
4. commit + push GitHub（修复源码 + 报告 + 证据 + 主表 + queue-status）
5. 三端同步（§7）
6. 验证截图不污染主仓（fab-* 等过程截图不入仓，evidence 正式证据入仓）
7. **开源替代排查验收（2026-11-01 新增，G-OSS-001）**：凡自研/自写模块，验收必须核对"为何不用现成库"说明（可一句话，但必须写）；答不上来/说明不成立 = 打回重做，不得收口。

---

## 6.1 打 tag 铁律（2026-10-28 用户明确要求，全系强制）

> 目的：防止进度偏差导致开发倒退。每个关键修改或更新必须在 git 中留 tag 锚点，让"当前真实进度"可被任意时刻核验、可回滚。

**适用对象（每项完成即打）**：

| 节点 | tag 命名示例 | 谁打 |
|---|---|---|
| 版本冻结 | `v0.1.0` / `v1.2.0`（SemVer） | 主脑（Owner 批准后） |
| 阶段/工单冻结 | `m8-frozen` / `v11-n6-frozen` / `stage1-v1.0-frozen` | 主脑（验收通过后） |
| 系列收口 | `m2-series-frozen` | 主脑（批次全冻结后） |
| **关键修改/修复闭环** | `<product>-<节点>-<日期>` 或复用上述冻结 tag | 执行端 + 主脑双确认 |

**规则**：
1. **关键修改 = 改了核心代码/配置/队列/范式/数据结构，或涉及版本/接口/冻结边界的任何改动**；小范围纯文档、注释、证据落盘可不打独立 tag，但须随所在工单冻结 tag 一并锚定。
2. **先打 tag 再宣称完成**：回执/报告宣称"已完成/已闭环/已冻结"时，对应 git tag 必须已存在（`git tag -l` 可查），缺 tag = 闭环未完成。
3. **tag 与 commit 一一对应**：每个 tag 指向具体 commit SHA（`git rev-parse <tag>` 可解析），tag 缺失 SHA 或指向漂移 = 异常。
4. **tag 命名唯一**：同一节点不得重复/覆盖 tag；重打必须 `-f` 并登记原因，禁止静默覆盖历史锚点。
5. **看门狗/审计校验点**：阶段报告、冻结声明、回执中出现的 tag 全部可解析、指向正确 commit；发现"声称冻结但无 tag"即判定冻结门未闭合。
6. 跨端同步：tag 随 commit 推 GitHub/Gitee（`git push --tags`），App/远端读取进度以 tag 为准。
7. **默认自动执行（2026-10-28 用户明确拍板，全产品生效）**：所有 Ultima 产品（Console/Radar/Gold/Sentinel/Scan/Agent/Engine/Admin/Manager 等）的关键修改或更新，完成即自动打 tag 并推送（`git tag <节点> && git push --tags`），**无需逐次向用户询问确认**；属默认动作的一部分。

---

## 6.2 Manager 权威刷新命令（v1.6 新增，登记后必跑）

> 目的：全局主表（唯一事实源）→ Manager `legacy_records`（快照，18766 API 供给 UltimaAgent HUD 任务队列）。只登记不刷新，界面侧读不到。刷新是**只读镜像**：不改审批/派发/调度，不产生新工单，仅同步全局主表最新行状态。

```powershell
# 触发一次权威刷新（等价服务启动导入；需 Python 能 import manager.*，用 Manager 仓解释器）
$env:PYTHONPATH='H:\UltimaAI\UltimaManager\src'
python -B -X utf8 -c "import sys; sys.path.insert(0, r'H:\UltimaAI\UltimaManager\src'); from manager.store import Store; from manager.runtime import RuntimeAuthority; s = Store(r'C:\Users\Administrator\AppData\Local\UltimaManager\manager.db'); a = RuntimeAuthority();
try:
    with a.locked():
        snap = a.refresh(s)
    print('REFRESH_OK imported=', snap.registry_rows, 'native=', snap.native_actors)
except Exception as e:
    print('REFRESH_FAIL', type(e).__name__, str(e))"
```

验证（刷新后必查）：GET `http://127.0.0.1:18766/api/v1/tasks?project_id=<产品>`（Bearer 鉴权，token 从 Manager `CredentialStore` 读取），确认目标工单在 `legacy[]` 中且 `registry_state` 为最新状态（executing/completed 等）。`agent_server.py` `_manager_active_tasks()` 读 items+legacy，其中 `registry_state ∈ {executing, in_progress, running, develop, plan, plan_review, audit}` 的行会显示到 UltimaAgent HUD 左下角任务队列。

---

## 7. 同步通道（队列状态三端一致）

| 端 | 位置 | 方式 |
|---|---|---|
| GitHub 正式仓 | `Ultima-AI-Studio/<product>` | git push（主） |
| Gist | `ArkExlabs/<gist-id>/raw/queue-status.json` | 免 token 公开读取通道（App 读取用） |
| Gitee 镜像 | `Ultima-AI-Studio/ultimaconsole-sync` (master) | `sync-queue.py` 或 git clone+push |
| docs 镜像 | `H:\UltimaAI\ultima-docs-repo` → `Ultima-AI-Studio/ultima-docs` | 公共文档/范式推送 |

已知缺陷（sync-queue.py，未修）：Gitee contents GET 遇空 list 崩溃、文件不存在需 POST 创建（PUT 强制 sha）、token 须放 query。**Gitee 首建/异常时备用通道 = git clone + push（已验证可用）**。
凭证规则：token 不写入范式/工单/仓库明文，存本机环境变量或 git 凭据管理器。

---

## 8. 故障预案（全部为本次实测处置）

| 故障现象 | 处置 |
|---|---|
| `model not supported`（默认模型失效） | 查可用模型 → 显式 `-m gpt-5.6-sol` |
| helper `codex-windows-sandbox-setup.exe` program not found | 补 PATH；仍失败走 bypass（见下） |
| `CodexSandboxOffline: 1332`（SID 解析失败） | 用户完全访问授权下 `--dangerously-bypass-approvals-and-sandbox` |
| 参数未传入卡 stdin | `- < dispatch-<id>-prompt.txt` 喂文件 |
| 长时间无回执 | 先确认是否真正触发 exec（会话 originator=codex_exec）；只归档+同步≠派发 |
| 执行端报"无法处理" | 升级回主脑（一次一主），不自行换路 |
| 派发弹出一堆终端窗口 | Codex 版本过旧（<0.159.2）或未用精简 CODEX_HOME → `codex update` 升级至 ≥0.165.0，且派发设 `CODEX_HOME=C:\Users\Administrator\.codex-cli`（无插件/MCP/notify）；修复后进程树可见窗口应为 0 |

---

## 9. 维护与登记

- 本范式为跨项目硬约束；模型清单、命令形态、故障预案变更必须经主脑更新并在此登记，旧版归档只读。
- 登记入口：`H:\UltimaAI\_shared\paradigms\Ultima-范式存档总纲.md`（本范式已登记）。
- 同步：本地权威（`_shared\paradigms\`）→ docs 镜像（ultima-docs-repo `docs/shared/`）→ GitHub。
- 每个挂 Ultima 前缀的项目每次派 Codex 都必须符合本范式；项目级差异只能加约束，不能删减。
