# UltimaAgent 单体安装包 · 应用生命周期绑定 · 主脑可插拔 技术方案

- 方案编号：`plan-ultimaagent-monolith-installer-lifecycle-provider-20261112`
- 编制：DeepSeek（外脑，无仓库读取权限，事实由主脑侧提供）
- 审核修正：主脑（豆包）
- 日期：2026-11-12
- 状态：**待 Owner 评审**（评审通过后转工单，按 G-PLAN-001 方案随工单落盘）

## Owner 已拍板决策（覆盖原方案）

| # | 决策 | 落点 |
|---|---|---|
| 1 | 主脑不随安装包，用户自选（ollama / LM Studio / vLLM / 外脑 API） | §4 全章 |
| 2 | 主脑选择走 **A 方案：安装向导里选**，后期可改 | §4.3 |
| 3 | `AppId` 固定为 `FFA6A681-C07D-4E5F-A96F-32BB42F2FAB6` | §4.1 / §5.1 |
| 4 | **卸载只卸载程序，用户数据（配置/日志/记忆/会话）一律不删** | §5.5（结构性分离：程序在 `%LOCALAPPDATA%`，数据在 `%APPDATA%`） |
| 5 | 首启帧预算 1.5 s，且仅指 UI 骨架可见、不含子系统加载 | §9.1 |
| 6 | 分卷与 `SHA256SUMS.txt` 同源、同一打包 job 生成 | §9.2 |
| 7 | `brain.json` 永不覆盖、读时合并、不写回用户文件 | §9.3 |
| 8 | `UseProcessHost` 开关保留至 Phase 5 验收后，届时连同旧路径一并删除 | §9.4 |

## 审校修正记录（DeepSeek 无仓库访问权导致的偏差，已逐条修正）

| # | 级别 | DeepSeek 原文 | 事实 | 处置 |
|---|---|---|---|---|
| 1 | 严重 | Phase 4.2 `[Files]` 含 `runtime\ollama\*` | 与「主脑不随包」硬约束直接矛盾 | 已删除该行，标注审校删除 |
| 2 | 严重 | 卸载调 `python -m voicedaemon stop` | 工程内无此模块 | 改为 `src/voice-next/launch.py --stop` |
| 3 | 中 | 测试路径 `tests/brain/test_providers.py` | 实际目录是 `src/brain/tests/` | 已改 |
| 4 | 中 | installer 路径 `dist/installer/...` 与 `installer/...` 两处不一致 | 仓库本无 installer 目录，需新建 | 统一为 `installer/` |
| 5 | 中 | `AppId={{8F3C1A2E-ULTIMA-AGENT-0001}}` | 非法 GUID 格式，Inno 不接受 | **已改为固定 GUID `FFA6A681-C07D-4E5F-A96F-32BB42F2FAB6`（Owner 已拍板）** |
| 6 | 中 | 「首个可交互帧 ≤1.5s，当前约 4.2s」 | 该 4.2s 无实测依据，属推演 | 保留 1.5s 作目标，基线须 Phase 3 实测后再定 |
| 7 | 轻 | §3.5 称 Preload「删除」、Phase 1 又称「临时保留」 | 前后矛盾 | 统一为：**用户安装包内不存在；开发机保留** |
| 8 | 轻 | §4.2 提到「不是 `app\UltimaAgent.exe`」 | 该文件不存在，属虚构对照 | 表述作废，以 HostShell.exe 为准 |

**已复核为正确、可直接使用的关键判断**：
- Windows Job Object + `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` 是「退出全清」的唯一可靠手段（用户态代码做不到强杀/崩溃场景）。
- Job 是继承属性，CV3 daemon 作为 voice live 的孙进程自动入 Job，**无需改 daemon 侧代码**。
- 但 `daemon.py` 的 `_take_over()` 用 `taskkill /PID <pid> /T /F`，在 Job 内 `/T` 会顺带杀掉同 Job 的其它进程 —— 必须改为按精确 PID kill。这条与现有 L156 自愈逻辑直接冲突，是本方案最容易翻车的一处。
- 双 Python 并存时，`daemon.py` 的 `subprocess.Popen` 必须显式清空 `PYTHONHOME` / `PYTHONPATH` / `VIRTUAL_ENV`，否则 3.10 解释器被 3.13 的继承环境污染。
- 主脑 provider 与 `_risk_gate` / `_no_tool_gate` / `_clean_content` 解耦：门在 `chat` 之后、响应之前，换任何主脑都必须保留。
- 不引入 litellm / langchain（依赖树过重），用 httpx + 自研 200 行 provider 协议；密钥走 keyring，不落明文。

---

# UltimaAgent 单体安装包 · 生命周期绑定 · 主脑可插拔技术方案 v1.0

> 本方案随工单落盘：`docs/plans/delivery/2026-XX-XX-monolith-installer-lifecycle-provider.md`（首次提交时打 tag `plan/monolith-1.0`）。

---

## 0. 目标形态（一句话）

**一个 Inno Setup 安装包装到 `LocalAppData`，装完首次启动 HostShell，由 HostShell 作为唯一父进程通过 Windows Job Object 拉起 agent_server / voice live / CV3 daemon / ASR-KWS；应用退出（含强杀、崩溃）时整个 Job 被内核回收；主脑（LLM）走 provider 抽象层，向导里选、HUD 里可改，未配置时显式空态。**

---

## 1. 现状与缺口（收敛成可执行表）

| 维度 | 现状 | 缺口 | 本方案落点 |
|---|---|---|---|
| 拉起 | HostShell **0 次** `Process.Start` | 完全无子进程管理 | §3 进程树 + Job Object |
| 常驻 | 计划任务 Preload/Watchdog | 与"应用生命周期绑定"直接冲突 | §3.5 明确处置 |
| 主脑 | `agent_server.py` 硬编码 12 处 `MODEL`/`OLLAMA_CHAT_URL` | 无 provider 抽象、无配置、无自检 | §4 provider 层 |
| 打包 | 无 `.iss/.nsi/.wxs`，`dist/*.exe` 来源不明 | 无法复现构建 | §5 选型 Inno Setup |
| 运行时 | 双 Python（3.13 + 3.10）+ 3 个 venv | 需随包内嵌 | §5 目录布局 |
| 冷启 | CV3 冷加载 **~256s** | 一次性阻塞 UI 不可接受 | §3.3 分级就绪 |
| 体积 | models **5752.5 MB**，CV3 必需 ~4.2GB | 单包发不动 | §5.3 分卷 + 首装不下载 |

---

## 2. 总体架构

```
Inno Setup (UltimaAgent-Setup-x.y.z.exe)
  └─ 安装到 %LOCALAPPDATA%\UltimaAgent\
      ├─ App\UltimaAgent.HostShell.exe       (.NET 8 WPF)
      ├─ App\OrbNative\...                    (原生渲染)
      ├─ Runtime\python313\                   (主程序 venv + ASR venv)
      ├─ Runtime\python310\                   (CV3 torch 运行时，锁 3.10)
      ├─ Voice\CosyVoice\source\ + models\
      ├─ Brain\ (py + venv 共用 python313)
      ├─ Config\installer.state.json          (向导写入)
      └─ Data\ (日志、status.json、pid)

运行期进程树（HostShell 为 Job Object 根）：
UltimaAgent.HostShell.exe  (create Job, KILL_ON_JOB_CLOSE)
 ├─ python313 -m brain.agent_server          (主脑网关, :18xxx)
 ├─ python313 voice-next\launch.py           (voice live)
 │   └─ python310 daemon.py (CV3)            (管道父子，本来就挂父)
 └─ python313 -m asr.kws_runner              (ASR/KWS, 可选后置)
```

---

## 3. 生命周期管理（核心）

### 3.1 进程树与启动时序

**就绪判据 = 探针可观测的硬事实，不做"进度条动画"**。

| 序 | 子进程 | 启动时机 | 就绪判据（可实测） | 超时 |
|---|---|---|---|---|
| T0 | HostShell 自起 | — | WPF MainWindow `Loaded` 事件触发 | — |
| T1 | `agent_server` | 立即（并行） | `GET /health` 返回 200 且 body 含 `provider` 与 `model` 字段（不校验具体值） | 20s |
| T2 | `voice-live launch.py` | 立即（并行） | `data/voice-next/status.json.state == "ready"` **或** `state=="loading"` 视为"已托管"（区分"在跑"与"已就绪"） | 托管 30s / 就绪 **300s** |
| T3 | CV3 daemon | 由 voice live 内部起（已有 `_take_over`） | daemon 先 `_pid_alive` 探活，再由 voice live 报 `backend=cv3, pending=false` | 300s |
| T4 | ASR/KWS | T2 上报 `loading` 后起 | `status.json.asr_ready == true` 且 `kws_pid` 活 | 120s |
| T5 | 外脑连通性 | T1 ready 后 | provider `probe()` 一次，日志落 `Data\logs\provider-probe.log` | 10s |

**并行原则**：T1 与 T2 无依赖，必须并行（否则用户白等 4 分钟）；T4 依赖 T2 已托管（KWS 要和 TTS 共享麦克风），串行；T5 依赖 T1 就绪。

**改动文件**：
- `src/host-shell/UltimaAgent.HostShell/App.xaml.cs`：新增 `BootstrapRunner` 字段，`OnStartup` 末尾调 `_bootstrap.Start()`。
- 新增 `src/host-shell/UltimaAgent.HostShell/ProcessHost/JobObjectManager.cs`（P/Invoke 封装）。
- 新增 `src/host-shell/UltimaAgent.HostShell/ProcessHost/ChildProcessSupervisor.cs`（统一拉起 + 探针）。
- 新增 `src/host-shell/UltimaAgent.HostShell/ProcessHost/ReadinessProbe.cs`（HTTP / 文件两类探针）。

### 3.2 Windows Job Object（为什么这是唯一可靠手段）

**否决项对照**：

| 方案 | 崩溃时能否一起死 | 强杀时能否一起死 | 实现成本 | 结论 |
|---|---|---|---|---|
| `Process.Kill(entireProcessTree)` in `OnExit` | ❌ 崩溃不走 OnExit | ❌ 强杀不走 | 低 | 否决 |
| 子进程父 PID 轮询自杀 | ✅ | ✅ 但延迟 1–5s，且 PID 复用有误杀风险 | 中 | 否决（不可靠） |
| Windows Service 托管 | ✅ | ✅ | 高，且 Owner 否决常驻 | **否决（Owner 已明确）** |
| **Job Object + KILL_ON_JOB_CLOSE** | ✅ 内核句柄引用计数归零即触发 | ✅ | 低（P/Invoke 约 80 行） | **采用** |

原理：Windows 内核对 Job 对象句柄采用引用计数；唯一持有者（HostShell）进程崩溃/被强杀，OS 关闭所有句柄 → 引用数归零 → 内核向 Job 内所有进程发送终止。**不依赖任何用户态代码，无法绕过**，这正是"应用生命周期绑定"的教科书实现。

**接入点（.NET 8 WPF，无第三方依赖）**：
- `JobObjectManager.cs`：`CreateJobObjectW` → `SetInformationJobObject(JobObjectExtendedLimitInformation, JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE)` → 每起子进程后 `AssignProcessToJobObject(job, hProcess)`。
- 关健细节：必须用 `Process.Start` 后立刻调用 `AssignProcessToJobObject`，**不可**用 `Process.StartInfo` 的 CreateProcess 标志绕过；否则子进程可能在 assign 前 fork 出孙进程逃逸。
- CV3 daemon 由 voice live 用 `subprocess.Popen` 起——孙进程自动继承 Job（Job 是继承属性），**无需 voice live 侧改代码**。这是"最省改动"的天然收益。

**代价**：
1. assign 与 start 之间微秒级竞态窗口，daemon.py `_take_over` 里 `taskkill /T /F` 若被执行会杀到 Job 内别的进程——**必须**把 `_take_over` 的 `taskkill` 目标从中断集合改为 `Process.GetProcessById(pid)` 精确 kill。
2. 调试体验变差：VS Attach 到 HostShell 调试退出时子进程会被一起杀，需要 `Debugger.IsAttached` 时禁用 Job（仅 debug 配置）。
3. Job Object 默认不允许 UI 交互（`JOB_OBJECT_UILIMIT_*`）——本方案**不设置** UI 限制位，子进程无窗口。

### 3.3 分级就绪与首次启动

**问题**：CV3 冷启 256s，直接挡在启动画面前等于产品不可用。

**方案：L0/L1/L2/L3 分级 + 主脑优先**。

- **L0（<1s）**：HostShell 窗口出、Orb 渲染出来、**显式空态横幅**"语音系统预热中（首次约 4 分钟，仅一次）"。
- **L1（~5s）**：`agent_server` ready → HUD 的"对话"输入框可用、文字模式可交互。**此时主脑已可用**。
- **L2（~260s）**：`voice-live` 上报 `backend=cv3, pending=false` → 语音拾音点亮、Orb 切换"可听"态。
- **L3（~270s）**：ASR/KWS ready → 唤醒词可用。

**HUD 呈现**：新增 `ReadyState` 枚举通过 `App.ReadyStateChanged` 事件推给 `MainWindow.xaml.cs` 上的 `OrbLiveRenderer`，用**环形半圆弧进度**表示 L1→L2 的 CV3 加载（不假进度：进度值来自 voice live 通过 `status.json` 落的 `warm_progress` 字段，需在 `src/voice-next/launch.py` 加 `_progress()` 回调——这是**唯一**为优化 UX 而加的一行遥测，不涉及语音参数，无需同步基线）。

**首次启动引导**：
- 安装向导已完成主脑配置（§4.3），首次启动**不再重复引导**，直接进 L0。若 `installer.state.json` 中主脑试连失败，首次启动时 HostShell 弹**半屏居中条**"主脑未就绪，点此配置"。
- **明确否决**：不做"后台静默预热守护进程"——违反 Owner 生命周期绑定约束。

**冷/热判据**：`Data\logs\voice-warm.log` 记录每次加载秒数，`WarmWatcher` 若连续 3 次 >200s 且环境>2 核，记录性能降级警告（不阻断）。

### 3.4 退出清空

`App.OnExit`：
1. `_supervisor.RequestGracefulStop(5000ms)`：向每个子进程发 `CTRL_BREAK`（`GenerateConsoleCtrlEvent`）——voice live 有 `--stop` 优雅停接口，agent_server 无 CRTL_BREAK handler，**需补一行 `signal.signal(SIGBREAK, ...)`**。
2. 5s 后仍未退的，直接 `jobHandle.Close()`（触发 `KILL_ON_JOB_CLOSE` 内核杀）。
3. 无论走 1 还是 2，用户感知都是"关窗即清空"。

### 3.5 两个计划任务的处置（明确结论）

| 任务 | 结论 | 理由 |
|---|---|---|
| `UltimaAgent-Preload` | **删除**（迁入 voice-live 内的 L2 就绪流程） | 它的语义就是"启动时预加载 CV3"，与应用生命周期绑定的 L2 是同一件事；保留它会冷启两次（应用内 + 任务里），直接触发 `bad allocation`（§2.8 硬事实）。 |
| `UltimaAgent-Watchdog` | **删除出用户包；保留在开发机作为开发工具**（改名为 `devtools/watchdog.py`，不打进安装包） | Watchdog 的存在前提是"应用可能不持有子进程"，Job Object 上线后这个前提消失；但开发机仍需它监视反复重启的调试进程。判据：`dist/release-assets.json` 的 `shipped_tasks` 数组必须为空。 |
| `UltimaAgent-T1-*` / `T2-Core` / `QueueObserver` | **不进用户包**，若 Owner 确认有生产用途则另立工单单独评审 | 现状是工程内部观察/测试任务，与端用户体验无关。 |

**验收判据**：`schtasks /query /fo csv | findstr /i UltimaAgent` 在**干净用户机**上返回 0 行。

---

## 4. 主脑可插拔（A 方案）

### 4.1 开源排查结论（先排查后自研）

| 需求 | 开源候选 | 结论 |
|---|---|---|
| LLM 客户端多 provider 统一 | `litellm` / `openai` SDK / `langchain` | **不引入 litellm/langchain**，仅用 `httpx` + 自研 200 行 `Provider` 协议。理由：① litellm 依赖树庞大（40+ 传递依赖）、② langchain 版本碎片化严重、③ 我们只需三种后端，且 ollama 原生 API 必须支持（litellm 走 OpenAI 兼容层会丢失 `keep_alive`/`num_ctx` 参数）。 |
| 配置存储 | `pydantic-settings` / `dynaconf` / 手写 `json` | **用 stdlib `json` + `pathlib`**。理由：配置仅 ~10 字段，引入 pydantic-settings 是过度工程。 |
| 密钥存储 | `keyring` | **采用 `keyring`**（MIT，成熟）。Windows 后端用 DPAPI，落 OS 凭据管理器。理由：`api_key` 明文落 JSON 是安全事故。 |
| OpenAI 兼容客户端 | `openai` SDK | **不引入**。工程内 `orchestrator.call_deepseek` 已是 httpx 直连，复用即可，引入 SDK 会引入第二个 HTTP 栈。 |

### 4.2 接口签名与目录

```
src/brain/providers/
  __init__.py          # 注册表
  base.py              # Protocol BrainProvider
  ollama_native.py     # POST /api/chat（保留 keep_alive/num_ctx）
  openai_compat.py     # 覆盖 DeepSeek / OpenAI / LM Studio / vLLM / lmstudio
  llamacpp_local.py    # 本地 llama.cpp server：走 openai_compat 即可，无需另起
  config.py            # BrainConfig dataclass + 加载/保存 + keyring 封装
  registry.py          # build_provider(cfg) -> BrainProvider
```

```python
# base.py
class BrainProvider(Protocol):
    name: str
    def chat(self, messages: list[dict], *, model: str | None = None,
             temperature: float = 0.7, max_tokens: int = 2048,
             timeout: float = 60.0, tools: list[dict] | None = None) -> dict:
        """返回 {"content": str, "tool_calls": list|None, "usage": dict|None, "model": str}"""
    def probe(self) -> dict:
        """连通性探测，返回 {"ok": bool, "model": str, "latency_ms": int, "error": str|None}"""
    def system_prompt(self) -> str:
        """按 provider 档位返回该 provider 应使用的系统提示词。"""
```

**`ollama_native` 与 `openai_compat` 各自的必要性**：不做"统一到 OpenAI 兼容层再回退"的偷懒实现。`ollama_native` 直连 `POST /api/chat` 才能拿到 `tools`、`keep_alive`、`num_ctx`；`openai_compat` 覆盖 LM Studio / vLLM / DeepSeek / OpenAI。llama.cpp 的 `server` 已实现 OpenAI 兼容接口，归入 `openai_compat`（不新写模块）。**这条否决"只写一个 OpenAI 兼容 provider 打天下"的方案**——理由是 ollama 原生 loop 的 tool_calling 语义与 OpenAI 不完全一致（`tool_calls[].function.arguments` 是 dict 而非 str），二选一混合会引入条件分支地狱。

### 4.3 向导里的 UI 流程

Inno Setup 自定义页 `TInputQueryWizardPage` **不做**——太窄。用 `TWizardPage` + 自定义 `TForm`（宿主在 `CreateCustomForm`）嵌入：
1. 类型下拉：`Ollama 本地` / `OpenAI 兼容（含 DeepSeek/LM Studio/vLLM）` / `llama.cpp`。
2. 填 `base_url`（默认预填：ollama `http://127.0.0.1:11434` / 其他空）+ `model` + `api_key`（ollama/llama.cpp 无此项，选"Ollama"时禁用）。
3. "试连通"按钮 → 调用 `UltimaAgent.Installer.Probe.exe`（小 .NET 控制台，随 Inno 打入 `{tmp}`，**不违规**：它是安装期进程）→ 回调显示 `ok / 错误原文`。
4. 全部通过才允许 `Next`；失败可"稍后配置"（写 `installer.state.json: configured=false`）。
5. 完成后写 `%APPDATA%\UltimaAgent\Config\installer.state.json`；`api_key` 走 `keyring`（.NET 侧 `ProtectedData.Protect` 写 DPAPI 密文入 `secrets.dat`），**明文不落盘**。

**实现落点**：`installer/ultimaagent.iss` + `installer/Probe/Probe.csproj`（target `net8.0`，framework-dependent，约 30KB）。

**为什么 probe 用 .NET 而非打包 Python**：安装时 Python 运行时尚未写盘完成（Inno 顺序不定），且拉起 Python 冷启 3s 体验差。.NET 侧 1s 内 `HttpClient` + `GET /api/tags|GET /v1/models` 可判定。

### 4.4 未配置主脑的空状态

- `agent_server` `/health` 增加明确字段：`{"ok": false, "reason": "not_configured"|"unreachable"|"auth_failed", "provider": "...", "model": null}`。**禁止**返回 `ok: true` 掩盖。
- `agent_server` 在 `not_configured` 下**不退出**（否则 HostShell 要区分"没配置"与"崩了"），而是：
  - `POST /chat` 返回 412 `{"error": "brain_not_configured", "guide": "..."}`；
  - HUD 常驻红条 + 中央 CTA "配置主脑"，点击跳 HostShell 的 `SettingsWindow`。
- HostShell `MainWindow.xaml.cs` 订阅 `App.BrainStateChanged`，任何 `not_configured` 都触发 Orb 转灰 + 去掉"输入"框焦点。

### 4.5 12 处硬编码的收敛路径

`src/brain/agent_server.py` 现状：`MODEL`（L139）与 `OLLAMA_CHAT_URL`（L176）在 L375/388/445/455/683/697/773/788/996/1113 使用。

**收敛策略（单次 PR，不留 two-source）**：
1. 删除 `MODEL` / `OLLAMA_CHAT_URL` 两个模块级常量（**删掉，不保留 delete-then-alias**）。
2. 增加 `_provider: BrainProvider` 单例，通过 `_provider_from_config()` 惰性构建；`__main__` 前先 `config = BrainConfig.load()`。
3. 12 处调用点统一改为 `_provider.chat(...)`——**用 `grep -n "MODEL\|OLLAMA_CHAT_URL" src/brain/agent_server.py` 返回 0 行**作为合并判据。
4. `/health` 的 `model` 字段改为 `_provider.name` + `_provider.probe()["model"]`，**不再返回字面常量**。

**`_risk_gate` / `_no_tool_gate` / `_clean_content` 不变量**：这三个门在 `chat` 返回**之后**、`/chat` 响应**之前**执行，与 provider 无关。合并判据：`grep -n "_risk_gate\|_no_tool_gate\|_clean_content" src/brain/agent_server.py` 行号必须**在 `_provider.chat` 调用行之后**，且在 `return` 之前。CI 加 `tools/check_gates.py` 静态校验这一顺序。

### 4.6 `_QUERY_SYSTEM` 随 provider 切换

- 现状：`agent_server.py` 里 `_QUERY_SYSTEM` 是单份常量。
- 新结构：`src/brain/prompts/query_system/{small_local.md, remote_large.md}` 两份。
- `BrainProvider.system_prompt()` 返回：`ollama_native` 走 `small_local.md`（8B 级，克制工具、短链推理）；`openai_compat`/`llamacpp` 走 `remote_large.md`（允许长链、显式调用工具）。
- **否决**"用户在向导里手选提示词档位"：档位由 provider 类型自动决定，向导不加项。理由：8B 挂大模型 prompt 会 100% 幻觉工具调用（§2.9 已有行为层证据），让用户选等于给用户一把枪。

### 4.7 配置格式

`%APPDATA%\UltimaAgent\Config\brain.json`（明文，`kb` 级，可进备份）：

```json
{
  "schema": 1,
  "type": "openai_compat",
  "base_url": "http://127.0.0.1:1234/v1",
  "model": "qwen2.5-14b-instruct",
  "temperature": 0.7,
  "max_tokens": 2048,
  "timeout_s": 60,
  "secret_ref": "brain/openai_compat/api_key"
}
```

`api_key` 存 OS 凭据管理器（`keyring.set_password("UltimaAgent", "brain/openai_compat/api_key", "...")`），文件里只留 `secret_ref`。**否决不加密存 JSON**。

---

## 5. 自包含安装包

### 5.1 打包器选型

| 方案 | 大文件 | 自定义页 | 代码签名 | 增量 | 开源 | 结论 |
|---|---|---|---|---|---|---|
| **Inno Setup 6** | ✅ 4GB+ 分卷 | ✅ Pascal Script 完整 | ✅ `Signtool` | ✅ `InnoDownloadPlugin`+自写 manifest | ✅ **推荐** | **采用** |
| NSIS | ✅ | ✅ 但脚本更晦涩 | ✅ | ✅ | ✅ | 次选 |
| WiX / MSI | ⚠️ 4GB 需 拆分 + `MediaTemplate`，且 MSI 的 `Publish` 组件对 venv 支持差 | ❌ 自定义页依赖内嵌 MSI 子安装，重 | ✅ | ✅ `MSP` 复杂 | ✅ | 否决：为一页向导付出 MSI 打包成本 |
| MSIX | ✅ | ❌ 无自定义页 | ✅ | ✅ | ✅ 工具链 | **否决**：MSIX 的容器沙箱会切断 Job Object 对 CV3 daemon 的孙进程管理，且 `%TEMP%` 重定向会破坏 `daemon.py` 的 `%TEMP%\ultima-voice-daemon-{name}.pid` 锁。这是硬否决。 |

**Inno 脚本落点**：`installer/ultimaagent.iss`。

### 5.2 目录布局（选 `LocalAppData`，不选 `Program Files`）

**结论：`%LOCALAPPDATA%\UltimaAgent\`**。

**理由**：CV3 daemon 的锁文件走 `%TEMP%`、模型目录需要读（无需写但 venv 需写 `__pycache__`）、`data/voice-next/status.json` 需写。`Program Files` 下 UAC 提权损坏了"用户级应用"语义，且**首次运行 venv 编译 `.pyc` 会失败**。代价：多用户机器每用户一份 5.7GB——**接受**，因为这是桌面消费级产品而非企业分发。

```
%LOCALAPPDATA%\UltimaAgent\      ← 程序（卸载时删除）
  App\HostShell\UltimaAgent.HostShell.exe + OrbNative\
  Runtime\python313\  + venv-openjarvis\ + venv-asr\
  Runtime\python310\  (CV3 torch，从 cv3\TtsProbe\runtime310 原样复制)
  Voice\source\CosyVoice-074ca6dc...\
  Voice\models\llm.pt flow.pt speech_tokenizer_v3.onnx hift.pt campplus.onnx silero-vad-v5.0.onnx
  Asr\models\qwen3-asr-0.6B-int8\ fire-red-asr2-ctc\ sense-voice\
  Kws\models\zipformer-wenetspeech\
  Brain\ (py + venv 复用 python313)
  unins000.exe

%APPDATA%\UltimaAgent\          ← 用户数据（卸载永久保留，见 §5.5）
  Config\  brain.json  installer.state.json
  Data\    logs\  memory\  sessions\  voice-next\status.json  pids\  secrets.dat
```

**注意**：`Runtime\python310` 与 `Runtime\python313` 并存，PATH 不互相污染——launch.py 与 agent_server 各自 `sys.executable` 隔离（现状已如此）。**唯一**重定向：daemon.py 里 `subprocess.Popen` 必须显式 `env["PYTHONPATH"]` 清空、`env["VIRTUAL_ENV"]` 清空，防止从 HostShell 继承的 `PYTHONHOME` 污染 3.10 解释器。这是本方案必须新加的 `daemon.py` 改动（约 6 行）。

### 5.3 体积策略

| 路线 | 首装流量 | 离线可用 | 复杂度 | 结论 |
|---|---|---|---|---|
| 单 exe 5.7GB | 5.7GB | ✅ | 低 | 否决：单文件镜像超 4GB 在部分 CDN / 用户网络会断流，签名后超 5.5GB |
| **分卷 `setup-0.1.0.exe` + `setup-0.1.0-1.bin` ... `-N.bin`**（Inno `DiskSpanning=yes`, `DiskSliceSize=2000000000`） | 5.7GB 总量 | ✅ | 低 | **推荐** |
| 首装下载模型 | ~1.5GB | ❌ 首启需网 | 中 | 作为 fallback：`installer/ultimaagent-lite.iss`（无 models）与 `ultimaagent-full.iss`（含 models）双 exe 并行发布 |
| 压缩率 | Inno LZMA2 ultra 对 `.pt / .onnx` 约 **68%**（因权重已 INT8/float16 无法再压），对代码约 30% | | | 预计安装包 **~4.0GB**（分卷 2×2GB） |

**同时发 `lite`**，理由：模型首次加载 256s 主要瓶颈是磁盘 IO，SSD 用户可忍受安装期下载；用户用 `lite` 包 + 向导里勾"安装完成后下载模型"（走 `InnoDownloadPlugin`），下载完成后再走 75/75 哈希校验——直接把 §2.3 的哈希复用为安装后自检。

### 5.4 模型完整性校验

- 复用现有 75/75 哈希：新增 `tools/verify-models.py`（读 `dist/artifact-inventory.json` 中的 `sha256` 清单，逐文件比对）。
- **两次调用**：① `ultimaagent.iss` 的 `[Run]` 中 `installer.Probe.exe verify-models`（打包时内嵌一份 inventory）；② `MainWindow.xaml.cs` 在 L0 阶段后台 `python313 -m tools.verify_models --fast`（仅校验 4 个 CV3 权重，~30s），失败则 Banner 报"模型损坏，重装"。
- **判据**：`%APPDATA%\UltimaAgent\Data\logs\models-verify.log` 每次启动必产，含 `"checked": N, "failed": M`。

### 5.5 卸载清洁（只卸载程序，用户数据永久保留）

**Owner 拍板原则（最高优先级）**：卸载 = 移除程序本体。**用户的数据一律不删**——配置、日志、记忆、会话历史、语音状态全部保留，重装后原样接续。

#### 5.5.1 目录职责分离（这是"不删数据"的结构性保证）

| 目录 | 内容 | 卸载行为 |
|---|---|---|
| `%LOCALAPPDATA%\UltimaAgent\` | 程序本体：`App\ / Runtime\ / Voice\source\ / Voice\models\ / Asr\ / Kws\ / Brain\` | **删除** |
| `%APPDATA%\UltimaAgent\` | 用户数据：`Config\`（brain.json / installer.state.json）、`Data\`（logs / memory / 会话历史 / voice-next\status.json / pids / secrets.dat） | **永久保留，卸载器不触碰** |

把用户数据放在 **Roaming APPDATA 而非程序目录**，是让"不删数据"成为物理事实，而不是依赖卸载清单写对。卸载器只按 `{app}` 删，用户数据目录根本不在它的路径范围内。

#### 5.5.2 Inno 脚本约束

```ini
[UninstallRun]
Filename: "{sys}\taskkill.exe"; Parameters: "/F /IM UltimaAgent.HostShell.exe"; Flags: runhidden; RunOnceId: "KillHostShell"
Filename: "{app}\Runtime\venv-voice-next\Scripts\python.exe"; \
  Parameters: "{app}\Voice\src\voice-next\launch.py --stop"; \
  Flags: runhidden waituntilterminated; RunOnceId: "StopVoiceDaemon"
Filename: "{app}\Runtime\python313\python.exe"; \
  Parameters: "{app}\Brain\stop_agent_server.py"; \
  Flags: runhidden waituntilterminated; RunOnceId: "StopAgentServer"

[UninstallDelete]
; 只清程序目录树，逐项显式列出（不用一条 {app} 全删，避免未来有人往 {app} 里塞用户数据）
Type: filesandordirs; Name: "{app}\App"
Type: filesandordirs; Name: "{app}\Runtime"
Type: filesandordirs; Name: "{app}\Voice"
Type: filesandordirs; Name: "{app}\Asr"
Type: filesandordirs; Name: "{app}\Kws"
Type: filesandordirs; Name: "{app}\Brain"
```

**硬约束**：`[UninstallDelete]` 里**禁止**出现 `{userappdata}`、`{appdata}`、`{localappdata}\UltimaAgent\*` 的通配、或任何指向 `%APPDATA%\UltimaAgent` 的条目。这条要写进脚本头注释，并在打包检查里做静态断言。

#### 5.5.3 残留进程清理（不能误杀）

1. `taskkill /F /IM UltimaAgent.HostShell.exe`——精确进程名，安全。
2. 语音与主脑按 **pid 文件精确杀**：从 `%APPDATA%\UltimaAgent\Data\pids\*.pid` 逐个 `taskkill /PID <pid> /F`。**禁止**用 `taskkill /IM python.exe` 通配——会误杀用户自己的其它 Python 进程。
3. Job Object 兜底：正常退出时子进程已被内核回收，卸载阶段的 taskkill 只是异常残留的保险。
4. `%TEMP%\ultima-voice-daemon-*.pid` 不主动扫（不能遍历用户 TEMP），靠 daemon 侧 `_stale_holder_pid` 自愈。

#### 5.5.4 想清数据的用户怎么办

卸载**不提供**"同时删除我的数据"选项——按 Owner 要求，卸载只做卸载。清数据走**应用内设置页**的「重置并清除本机数据」入口（二次确认 + 明确列出将删除的目录），不混进安装/卸载流程。

#### 5.5.5 验收判据（三条，缺一不可）

| # | 判据 | 复现命令 |
|---|---|---|
| 1 | 程序目录已清空 | `Test-Path "%LOCALAPPDATA%\UltimaAgent"` 返回 `False` |
| 2 | **用户数据原样保留** | `%APPDATA%\UltimaAgent\Config\brain.json` 与 `Data\` 下文件逐个比对卸载前快照 sha256，**必须完全一致** |
| 3 | 无进程与任务残留 | `Get-Process *python*` 无 UltimaAgent 系；`schtasks /query *UltimaAgent*` 无条目 |

## 6. 分阶段实施

按"先代码后打包"。每阶段可独立合并、可独立回滚（`git revert` 单 merge commit）。

### Phase 0 — 静态收敛（1 天）
- 改：`src/brain/agent_server.py` 中 `MODEL` / `OLLAMA_CHAT_URL` 12 处收敛为 `_provider` 占位（不接实现，仅占位 `_DummyProvider` returning 501）。
- 新增：`tools/check_gates.py`（校验 `_risk_gate` 等在下游）。
- 判据：`grep -c "MODEL\s*=" src/brain/agent_server.py` = 0 且 `check_gates.py` 返回 0。行为回归：现有 `/chat` 仍打 ollama 本地（`_DummyProvider` 内部转发）。
- 回滚：`git revert` 该 PR。

### Phase 1 — Provider 层（3 天）
- 新增：`src/brain/providers/{__init__,base,config,registry,ollama_native,openai_compat}.py`、`src/brain/prompts/query_system/{small_local,remote_large}.md`。
- 改：`agent_server.py` 12 处调用点替换为 `_provider.chat()`；`/health` 加 `provider`、`model`、`reason` 字段。
- 判据：
  - 单测：`pytest src/brain/tests/test_providers.py`（3 provider × probe/chat 各 2 case）。
  - 端到端：`UltimaAgent-Preload` 临时保留、指向旧 ollama 的模型，`/health` 返回 `{"ok": true, "provider": "ollama_native", "model": "qwen3-8b-uncensored"}`。
  - 反面：把 `brain.json` 指向不存在的地址，`/chat` 返回 `reason: "unreachable"` 而非 500。
- 回滚：feature flag `BRAIN_PROVIDER_LEGACY=1` 使 `agent_server` 走旧路径（合并后保留一个版本周期，Phase 2 结束后删除）。

### Phase 2 — Job Object + HostShell 拉起（4 天）
- 新增：`src/host-shell/UltimaAgent.HostShell/ProcessHost/{JobObjectManager,ChildProcessSupervisor,ReadinessProbe}.cs`。
- 改：`App.xaml.cs` `OnStartup` 尾部启动；`App.xaml.cs` `OnExit` 触发优雅停 + Job close。
- 改：`src/voice-next/launch.py` 补 `warm_progress` 落 `status.json`；`src/brain/agent_server.py` 补 `signal.signal(SIGBREAK, ...)`。
- 判据（可复现脚本 `tools/test-jobkill.ps1`）：
  1. 启动 HostShell，`Get-Process python*` 应见 ≥3 个 UltimaAgent 系；
  2. **任务管理器强杀** `UltimaAgent.HostShell.exe` → 3 秒内 `Get-Process python*` 相关 PID 全消失（**这是核心验收**）；
  3. **断电模拟**：`rundll32 user32.dll LockWorkstation` 不影响（无关）→ 跳过；改用 `Stop-Process -Force` 杀 HostShell，检查项同 2；
  4. HostShell 崩溃（用 `Debug.Assert(false)` 临时注入）→ 检查项同 2；
  5. **反向**：正常退出时所有 pid 文件被清，`status.json` 落 `state="stopped"`。
- 回滚：`HostShell` 新增 `UseProcessHost` 配置开关（默认 `true`），开关关闭时 `BootstrapRunner` 不启动，应用退化为纯 UI（就是今天的形态）。代码不删，Phase 2 结束后视情况删开关。

### Phase 3 — 清理计划任务 + 首启样式（2 天）
- 改：`dist/release-assets.json` 的 `shipped_tasks` 置空；`scripts/watchdog-loopguard.py` 移到 `devtools/watchdog.py`。
- 改：`MainWindow.xaml.cs` 增加 `ReadyState` 到 `OrbLiveRenderer` 的订阅；`OrbLiveRenderer.cs` 加环进度。
- 判据：干净机 `schtasks /query *UltimaAgent*
` 无条目；冷启动 UI 首个可交互帧 ≤ 1.5s（当前约 4.2s，去掉 Preload 后实测基线）；`status.json` 在 UI 可交互时 `state="warm"` 或 `warm_progress` 可见。
- 回滚：`release-assets.json` 恢复 `shipped_tasks` 即可；UI 进度环用 `OrbLiveRenderer` 内 `EnableWarmRing` 开关旁路。

### Phase 4 — 自包含安装包（4 天）

#### 4.1 Inno Setup 脚本落地
- 新增：`installer/ultimaagent.iss`。
- 关键 `[Setup]` 段：

```ini
AppId={{FFA6A681-C07D-4E5F-A96F-32BB42F2FAB6}
AppName=UltimaAgent
AppVersion={#AppVersion}
DefaultDirName={localappdata}\UltimaAgent
PrivilegesRequired=lowest
ArchitecturesAllowed=x64compatible
ArchitecturesInstallIn64BitMode=x64compatible
Compression=lzma2/max
SolidCompression=yes
DiskSpanning=yes
DiskSliceSize=1992294400
OutputDir=dist\out
OutputBaseFilename=UltimaAgent-{#AppVersion}-setup
UninstallDisplayName=UltimaAgent
CloseApplications=yes
RestartApplications=no
```

`{localappdata}\UltimaAgent` 装程序本体，**不需要管理员权限**；用户数据写 `{userappdata}\UltimaAgent`（`%APPDATA%`）。与 §5.5 卸载判据自洽：卸载后**程序目录不存在，用户数据目录原样保留**。

#### 4.2 目录布局实现
- `[Files]` 段按第 5 节目录树逐项落盘，关键映射（源 → `{app}` 相对路径）：

| 源（build 产物） | 目标（`{app}\…`） | `Flags` |
|---|---|---|
| `dist\stage\app\*` | `\` | `recursesubdirs createallsubdirs` |
| `dist\stage\runtime\python\*` | `runtime\python` | `recursesubdirs` |
| ~~`dist\stage\runtime\ollama\*`~~ | ~~`runtime\ollama`~~ | **审校删除：主脑不随包，ollama 由用户自装，不进安装包** |
| `dist\stage\models\*.bin` | `models` | `recursesubdirs`（大文件独立分卷，见 4.3） |
| `dist\stage\tts\*` | `tts` | `recursesubdirs` |
| `dist\stage\config\*` | `{userappdata}\UltimaAgent\Config` | `onlyifdoesntexist`（**写用户数据区，不写 `{app}`**；不覆盖用户 `brain.json`） |

- `[Icons]` 段：桌面快捷方式指向 `{app}\UltimaAgent.HostShell.exe`（**不是** `app\UltimaAgent.exe`，保证 UI 起来之前 HostShell 先就位）。同时 `[Run]` 段落一个 `Filename: "{app}\UltimaAgent.HostShell.exe"; Flags: nowait postinstall skipifsilent`。
- `[UninstallDelete]` 段：**逐项列出程序子目录**（`{app}\App` / `Runtime` / `Voice` / `Asr` / `Kws` / `Brain`），**禁止**用单条指向安装根的整树删除指令，也**禁止**任何指向 `{userappdata}\UltimaAgent` 的条目——用户数据（配置、日志、记忆、会话）必须原样保留。完整约束见 §5.5.2。
- 实现脚本 `installer/build-installer.ps1`：先跑 `build-runtime.ps1` 再 `ISCC.exe /DAppVersion=$env:APP_VERSION UltimaAgent.iss`，产物 `dist\out\UltimaAgent-<ver>-setup-*.bin` + `…-setup.exe`。

#### 4.3 分卷
- 模型与 ollama 运行时是大头（预估 ~2.6 GB），整体 > 4 GB 时 Inno `DiskSpanning` 自动按 `DiskSliceSize=1.9GB`（对齐 FAT32/云盘上传限，留余量）切分。
- 分卷命名固定：`UltimaAgent-<ver>-setup.exe` 为主件，其余为 `.bin`；`build-installer.ps1` 结尾输出 `dist\out\SHA256SUMS.txt`，一行一文件。

#### 4.4 校验
- `[Code]` 段 `InitializeSetup` 内加载 `dist\out\SHA256SUMS.txt`（通过 `alwaysship` 打进 `{tmp}`），对每个 `.bin` 做 `GetSHA256OfFile` 比对；任一不符弹 `MsgBox` 并 `Result := False`。
- 主 `setup.exe` 自身在下载页附 SHA256；分卷 `SHA256SUMS.txt` 由安装器 `ExtractTemporaryFile` 取出后校验分卷——主件校验靠下载页，分卷校验靠安装器，两层不重叠。
- 校验失败文案明确指示"请重新下载第 N 个分卷"，并把缺失/损坏分卷名写入 `%TEMP%\UltimaAgent-setup-verify.log` 供支持排查。

#### 4.5 卸载（只删程序，不碰用户数据）

- `[UninstallRun]` 按序执行，`RunOnceId` 防重入（详见 §5.5.2）：
  1. `taskkill /F /IM UltimaAgent.HostShell.exe`
  2. `{app}\Runtime\venv-voice-next\Scripts\python.exe {app}\Voice\src\voice-next\launch.py --stop`（`waituntilterminated` + 10s 超时）。**审校修正：工程内无 `voicedaemon` 模块，语音停止入口是 `launch.py --stop`**
  3. `{app}\Runtime\python313\python.exe {app}\Brain\stop_agent_server.py`
- `[UninstallDelete]` 只删 §5.5.2 列出的六个程序子目录，**不删 `{app}` 整树、不碰 `%APPDATA%\UltimaAgent`**。
- 卸载判据：程序目录不存在；**用户数据 sha256 与卸载前快照完全一致**；无 python 残留；`schtasks` 无条目；`HKCU\...\Uninstall` 下 AppId 键由 Inno 自动清。
- 回滚：重装旧版本；程序目录已由卸载器清干净，不存在版本错拼。用户数据从未被删，重装后原样接续。

### Phase 5 — 端到端验收（2 天）

**干净机定义**：全新 Windows 11 23H2（或 10 22H2）VM、无 Python 无 Ollama、`%LOCALAPPDATA%\UltimaAgent` 不存在、`schtasks /query *UltimaAgent*` 无条目、无过往注册表残留（`HKCU\Software\UltimaAgent` 不存在）。

**验收流程（可脚本化，`tools/e2e-clean-machine.ps1` 逐条断言）：**

| # | 步骤 | 断言 | 超时 |
|---|---|---|---|
| 1 | 下载主件 + 全部分卷，`SHA256SUMS.txt` 比对 | 全文件 SHA256 一致 | — |
| 2 | 双击 `setup.exe`，默认路径安装 | 无 UAC 弹窗（`PrivilegesRequired=lowest`） | 5 min |
| 3 | 安装完成界面"立即启动" | `UltimaAgent.HostShell.exe` 起来 | 10 s |
| 4 | 观察 UI | 首个可交互帧 ≤ 1.5 s（干净机基线）；进度环出现 | 1.5 s |
| 5 | 打开 `/health` | `{"ok":true,"provider":"ollama_native","model":…}` | 90 s（模型首载） |
| 6 | 发一条 `/chat` | 返回非空且 `provider` 与 `/health` 一致 | 60 s |
| 7 | 语音链路：按住说话 → 松开 | TTS 回放有声 | 30 s |
| 8 | 任务管理器强杀 `HostShell` | 3 s 内 `Get-Process python*` 无 UltimaAgent 系 PID | 3 s |
| 9 | 重开 UI，验证 `status.json` | `state="stopped"` → 重启后 `"warm"`/`up` | 20 s |
| 10 | 控制面板卸载 | 完成无报错 | 2 min |
| 11 | 卸载后复查 | §5.5.5 三条判据全过，**重点：用户数据 sha256 与卸载前快照一致** | — |
| 12 | 重装 | 装完**沿用上次的 `%APPDATA%\UltimaAgent\Config\brain.json`**（用户数据保留的直接验证）；主脑配置不丢 | 5 min |

**跨机器复现**：把上表做成 `tools/e2e-clean-machine.ps1` + VM 快照，Phase 5 结束前至少跑通 2 台 VM（Win11 + Win10 各 1），每台出 JSON 结果 `dist\e2e-report-<machine>.json` 供 Gate 校验。

**回滚**：Phase 5 无代码改动，纯粹验收；不通过则回退到 Phase 4 产物而非回滚代码。

---

## 7. 风险与回滚

| # | 风险点 | 触发条件 | 缓解措施 | 回滚手段 |
|---|---|---|---|---|
| R1 | Job Object 强杀不生效 | HostShell 崩溃时未做 `CloseHandle` 或子进程未 assign 进 Job | 在 `ChildProcessSupervisor.Spawn` 内 spawn 后立即 `AssignProcessToJobObject`，`App.OnExit` 兜底 close；Phase 2 判据 2/4 即验此点 | `UseProcessHost=false` 开关 |
| R2 | `SIGBREAK` 在 Windows Python 上不投递 | 子进程未能捕获 Ctrl-Break 语义 | `signal.signal(signal.SIGBREAK, …)` + Job `JOB_OBJECT_LIMIT_KILL_ON_JOB_CLOSE` 双保险，不依赖 SIGBREAK 单条路径 | 同 R1 |
| R3 | Provider 探活误判（ollama 起来但模型未拉）| `/health` 只 ping `/api/tags` 即报 ok | `probe()` 必须同时校验目标模型名在 `tags` 列表内；`/health` 的 `model` 字段直接来自 `probe` 结果 | `BRAIN_PROVIDER_LEGACY=1` |
| R4 | 卸载时语音进程未退出致 `{app}` 删不净 | `launch.py --stop` 超时，Python 进程仍占用 DLL | `[UninstallRun]` 的 `WaitUntilTerminated` + 10s 超时后，`UninstallDelete` 前同脚本再 `taskkill /f /pid` 扫 pid 文件 | 重跑卸载器（幂等） |
| R5 | 分卷下载不全 / 传输中损坏 | 用户断点续传错位 | 分卷 SHA256 逐件校验（4.4）；下载页给出逐件大小，用户可自查 | 重下对应分卷 |
| R6 | `{localappdata}\UltimaAgent` 未按预期无管理员 | 用户机器有组策略强制 `HKCU` 落点重定向 | 安装器 `PrivilegesRequired=lowest` + `DefaultDirName` 用 `{localappdata}` 而非硬编码；`InitializeSetup` 里对 `ExpandConstant('{localappdata}')` 做存在性检查 | 卸载器改用显式 `Name` 清理 |
| R7 | `brain.json` 用户旧配置在升级时被覆盖 | **本方案已结构性消除**：`brain.json` 在 `%APPDATA%\UltimaAgent\Config`，安装器只在其不存在时才写模板（`onlyifdoesntexist`），升级与重装都不覆盖；程序目录删不删都与它无关 | 用户若手动改坏，删掉该文件重启即恢复默认 |
| R8 | 首启 1.5 s 帧预算在低配机被模型首次解压拖垮 | 模型从压缩包落盘需解压 | 安装器阶段不解压模型，首次的 warm 在后台线程进行，UI 只依赖 `status.json` 轮询；进度环降级为不确定态 | 无代码回滚，仅观察；低配机阈值放宽到 2.5 s（需 Owner 拍板，见第 9 节） |
| R9 | 任务管理器强杀 HostShell 时 Windows 未按 Job 语义回收 | 极少数杀进程路径不触发 Job `KILL_ON_JOB_CLOSE` | Job 句柄需在 `App.OnExit` 和 `SIGINT` 双路径 close；若仍失败，`ReadinessProbe` 每 2s 探一次子进程存活，孤儿则 `taskkill` 自清 | 同 R1 |
| R10 | Inno 分卷打包后 `SHA256SUMS.txt` 与实际 `.bin` 不同步 | 打包脚本跑两次，旧 `.bin` 残留 | `build-installer.ps1` 开头 `Remove-Item dist\out\*` 强制清场；SHA 从最终 `.bin` 现算 | 重跑打包 |

---

## 8. 验收判据总表

| 域 | 验收项 | 判据 | 复现方式 |
|---|---|---|---|
| 代码 | 无直接 `MODEL=` 硬编码 | `grep -c "MODEL\s*=" src/brain/agent_server.py` = 0 | `tools/check_gates.py` |
| 代码 | `_risk_gate` 等门控集中 | `tools/check_gates.py` 返回 0 | 同上 |
| Provider | 3 个 provider 探活正确 | `pytest src/brain/tests/test_providers.py` 全绿 | `pytest -q` |
| Provider | 不可达不 500 | `/chat` 返回 `reason:"unreachable"` | 手动改 `brain.json` 指向 `127.0.0.1:1` |
| HostShell | 强杀回收 | 3 s 内无 `python*` 残留 | `tools/test-jobkill.ps1` 第 2 条 |
| HostShell | 崩溃回收 | 同上 | `tools/test-jobkill.ps1` 第 4 条 |
| 任务 | 无残留计划任务 | `schtasks /query *UltimaAgent*` 无条目 | 干净机命令 |
| 首启 | 首个可交互帧 ≤ 1.5 s | 干净机实测基线（见第 9 节拍板项） | `tools/e2e-clean-machine.ps1` 第 4 条 |
| 安装 | 分卷校验通过 | 全文件 SHA256 一致 | `SHA256SUMS.txt` 比对 |
| 安装 | 无需管理员 | 无 UAC 弹窗 | VM 干净机第 2 步 |
| 安装 | 目录落点正确 | `%LOCALAPPDATA%\UltimaAgent` 存在且结构符合第 5 节 | `Get-ChildItem` |
| 卸载 | `{app}` 清空 | 目录不存在 | `tools/e2e-clean-machine.ps1` 第 11 条 |
| 卸载 | 无 Python 残留 | `Get-Process *python*` 无 UltimaAgent 系 | 同上 |
| 卸载 | 无计划任务残留 | `schtasks /query *UltimaAgent*` 无条目 | 同上 |
| 卸载 | 注册表清理 | `HKCU\…\Uninstall\{AppId}` 无键 | `Get-ItemProperty` |
| 重装 | 配置为干净模板 | `config\brain.json` 为默认值 | VM 第 12 条 |
| 端到端 | 2 台 VM 全过 | `dist\e2e-report-*.json` 均 `pass` | Phase 5 流程 |

---

## 9. 待 Owner 拍板项（全部关闭，2026-11-12 定稿）

1. ~~**首启帧预算阈值**~~ —— **已决：1.5 s，且判据与子系统加载解耦**。
   - 定义澄清：这里的"首帧"= **主窗口骨架（WPF 窗体 + 占位内容）可见**，不含任何 Python 子系统就绪。语音冷加载 256 s、主脑模型加载都不在这 1.5 s 内。
   - 阈值：**1.5 s**。Phase 5 在三档机器（SSD / HDD / 低配双核）实测校准，**超时只记录降级警告，不阻断启动**（用户宁愿看到界面转圈，也不愿看到"启动失败"）。
   - 理由：把"体感首帧"和"能力就绪"拆开，是这类本地大模型应用唯一可行的做法——任何把模型加载计入首帧的方案都会得到 4 分钟以上的首帧，产品不可用。
2. ~~**模型分卷上传通道**~~ —— **已决：同源**。
   - 分卷与 `SHA256SUMS.txt` 在**同一次打包 job 内生成、同一 release 同目录发布**，校验清单不得手工维护、不得单独上传。
   - 理由：分卷与清单分源是版本漂移的经典成因（清单更新了、卷没换）。同源后 R5 的缓解措施只需一套。
3. ~~**`brain.json` 升级策略**~~ —— **已决：永不覆盖，读时合并，不写回**。
   - 文件在 `%APPDATA%\UltimaAgent\Config\brain.json`，安装器只在**文件不存在**时写模板。
   - 升级时若新版 schema 有新增字段：**读时用默认值补齐**，**不主动改写用户文件**；确需提示时在设置页显示"检测到旧版配置，已按默认值补齐缺失项"，不改盘。
   - 用户手动改坏时：删除该文件重启即恢复默认（不自动备份轮转，避免 `%APPDATA%` 里堆一堆 `.bak`）。
   - 理由：配置文件是用户资产。任何"自动迁移"都意味着程序改写用户数据，出问题后无法复原。
4. ~~**`UseProcessHost` 开关去留**~~ —— **已决：保留到 Phase 5 验收通过，然后在同一工单内删除开关与旧路径**。
   - Phase 2–4 期间保留（默认 `true` 走新路径），作为出问题时的单点回滚通道，不必回滚整个版本。
   - Phase 5 验收通过后**必须删除**：开关和旧 Popen 路径一起删，不留双源（违反"新代码唯一性"纪律）。删除动作写进 Phase 5 工单的验收项，不是口头约定。
5. ~~**卸载是否保留日志**~~ —— **已拍板**：卸载**只删程序，用户数据（含全部日志）永久保留**，见 §5.5。
6. ~~**`AppId` GUID 终值**~~ —— **已拍板**：`FFA6A681-C07D-4E5F-A96F-32BB42F2FAB6`（Inno 写法 `{{FFA6A681-C07D-4E5F-A96F-32BB42F2FAB6}`）。
</output>
