# UltimaAgent 命名统一盘点（2026-11-13）

> 性质：只读盘点（0054 执行期间并行完成，未改动任何文件）。
> 状态：待 Owner 拍板改名范围后立项工单；本盘点即「旧名→新名」映射表的底稿。
> 原则：只改**活代码与活目录**；历史冻结证据与上游源码副本一律不改（M7 归档区不可写）。

## 一、已合规（不动）

| 对象 | 现名 | 说明 |
|---|---|---|
| C# 工程 ×4 | `UltimaAgent.HostShell` / `UltimaAgent.Hud` / `UltimaAgent.OrbHost` / `UltimaAgent.OrbNative` | AssemblyName 与 RootNamespace 均已规范 |
| 安装包 | `UltimaAgent-Setup-0.1.0.exe` | dist 发布面已规范 |
| 工单前缀 | `wo-ultimaagent-*` | 队列面已规范 |
| 新计划文档 | `plan-ultimaagent-*.md` | 2026-11-10 后新文档已统一 |
| python 职责目录 | `src/{brain,host,middleware,memory,update,window}` | 自研职责命名，无上游痕迹 |

## 二、需要改（活代码/活目录，按风险从低到高）

### A. 文档门面（低风险）
1. 根 `README.md` 标题 `# Ultima-Agent`：连字符写法与产品统一称谓不一致；应统一为 `UltimaAgent`（正文首句已自称 Ultima Agent 客户端）。顺手补组织标识 `ULTIMA AI STUDIO` 与品牌标语「极致造物，定义终局」。
2. 根目录 `_readme_local_backup.md`：M6 违例（旧版散放现行区），应归档至 docs/archive/ 或删除。

### B. 内部代号脚本（中风险）
3. `scripts/run-gorch.py`、`scripts/gorch_contract.py`、`docs/plans/gorch-*.md`（3 份活引用）：`gorch` 为编排器内部代号，语义不自明；建议 `UltimaAgent.Orchestrator` 或并入 dispatch 体系命名。**先确认 gorch 是否仍在活链路上**，若已停用则直接归档。
4. `scripts/` 中 w1/w2/s1 生命周期脚本（~15 个）：阶段代号命名，若对应工单已冻结则移入 devtools/。

### C. 迭代号目录（高风险，需全量引用清扫）
5. `src/voice-next/` 与 `tools/{venv-voice-next, voice-next}`：`voice-next` 是迭代代号非职责名，建议 `UltimaAgent.Voice` / `tools/venv-voice`。引用面：csproj、launch.py 调用方、config/voice-next/、派发器、冻结文档引用。
6. `tools/venv-openjarvis/`：**唯一携带上游拼装名的活目录**（openjarvis 为拼装来源项目名）。它是全工程专用解释器（Python 3.13.16），引用极广：队列派发器、全部验收脚本、多份冻结工单、KWS 基线文档、甚至用户侧路径偏好。改名成本最高，必须一次改透（git mv + 全仓引用清扫 + 渲染器自检 + 重建 launch 配置），建议单独成 T。
7. `tools/venv-asr/`：泛用职责名，可保留或并入 voice 域统一为 `tools/venv-asr`（不改亦可）。

### D. 分支名（技术痕迹）
8. 分支 `codex/voice-fsmn-new-path`：带上游模型选型痕迹（fsmn）。建议在 0054 冻结打 tag 后合并回主线分支（如 `main` 或 `codex/ultimaagent-installer`），旧分支留痕不删。

## 三、明确不改（历史证据，M7）

- `docs/plans/jarvis-work-*.md` 约 90 份：**jarvis 是已废弃的过程代号**，这些是冻结的过程证据，改名破坏追溯链；在权威文档（docs/INDEX.md）登记一句「jarvis-work = 历史过程代号，对应 UltimaAgent 早期工单」即可。
- `docs/research/sources/`（ovos-core、whisper-openai 等）：上游源码副本天然带原名，保留。
- `data/` 运行态、`tasks/queue/runs/` 历史目录：运行证据不改。
- 快照/证据文件名（t1-gate.txt 等）：验收证据不改。

## 四、附录一：悬浮球（orb/combo）重复实现盘点（2026-11-13 补）

实测判定（sln 与引用扫描）：

| 实现 | 位置 | 状态 |
|---|---|---|
| `OrbBallRenderer.cs` + `Assets/orb.html` | HostShell 内 | **活**——旧版静态测试样式，`ULTIMA_HOST_ORB_TEST=1` 触发 |
| `OrbLiveRenderer.cs` | HostShell 内 | **活**——正式 live 路径，`ULTIMA_HOST_LIVE=1` 触发 |
| `ComboWindowRenderer.cs` + `Assets/combo.html` | HostShell 内 | **活**——combo 路径，`ULTIMA_HOST_COMBO=1` 触发 |
| `UltimaAgent.OrbHost/`（WinForms+自带 orb.html） | host-shell 下 | **死**——不在 sln，不参与编译 |
| `UltimaAgent.OrbNative/`（原生 Win32） | host-shell 下 | **死**——不在 sln，不参与编译 |
| `src/window/{active_renderer,offline_renderer,combo_orchestrator}.py` | python 侧 | 旧 python 渲染线，活链路未见直接调用 |

问题本质：同一能力（悬浮球）至少 6 套并存，其中 2 套是死的整个工程、1 套旧样式靠环境变量与正式版混在同一个 HostShell 里——M1（重复开发）/M6（旧版混入现行区）双重违例。0054 期间"频繁唤起旧样式"即测试链用 `ULTIMA_HOST_ORB_TEST` 拉起 `orb.html` 旧样式所致，属工单既定行为（卡面明令不动 orb.html 视觉），不是 worker 越界。

**新增高危发现**：`src/brain/bootstrap.py` 直接 `from openjarvis.core.registry import ...`（L102/L135 等）——上游拼装名已进入** import 层活代码**，不只是 venv 目录名。命名统一若只改目录名不改 import，等于没改。

**收敛建议**（挂到 0055 或独立 006 模块重构波）：
- 活线收敛为 `OrbLiveRenderer`（+未来四角壳/任务面板走同一 WebView2 通道）；`OrbBallRenderer`/orb.html 降为 devtools 测试夹具。
- `UltimaAgent.OrbHost`、`UltimaAgent.OrbNative` 两个死工程整体归档（不删，移归档区）。
- `src/window/*.py` 判定去留；`openjarvis.*` import 逐个吸收为 `src.brain.*` 或隔离进适配层。

## 五、建议的执行形态

- 0054 冻结后开一张 0055「命名统一」工单：A 段（README/归档）+ B 段（gorch 归档裁定）先做；C 段（voice-next、venv-openjarvis 两项重命名）各自独立 T、全量引用清扫 + 构建零警告 + 渲染器自检作 Gate；D 段分支收敛随下次冻结 tag 顺带完成。
- 每项改名落一份映射表进本文件附录，作为唯一权威源（M1/M6 配套）。
