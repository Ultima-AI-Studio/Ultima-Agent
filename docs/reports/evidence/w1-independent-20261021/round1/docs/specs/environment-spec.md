# 环境需求清单（Environment Spec）

- **版本**：v1.4 · 2026-10-21
- **性质**：技术规格（开发/运行所需环境基线）；关联 dev-conductor"环境门"（环境准备=首个工单，未就绪不进开发）与 project-flow 阶段①前置
- **口径**：已确定基线 → 待评估依赖（TD 挂起）→ 平台前瞻；待评估项不硬编版本，评估后冻结回填

## 1. 开发环境（阶段一 · Windows 基线）

| 项 | 需求 | 说明 | 状态 |
|---|---|---|---|
| 操作系统 | Windows 11（x64） | 宿主壳开发与运行（阶段一首站） | ✅ 已具备 |
| .NET SDK | 8.0.425 | 已装于 `C:\Users\Administrator\.dotnet`；用户 PATH 第 1 项已是该目录。旧进程可能继承旧 PATH，本项目以 `scripts/host-shell-toolchain.ps1` 显式固定 SDK | ✅ 已装·空壳实编通过 |
| Visual Studio 2022 | 含 WinUI 3 / Windows App SDK 构建工具链 | Build Tools `17.14.41`；配合缓存的 Windows App SDK `1.8.260921001` 已完成 x64 实编 | ✅ 已验证 |
| Python | 3.13.13（x64） | 能力层跨平台运行时；项目隔离于 `H:\UltimaAI\UltimaAgent\tools\python31313`，不改变其他项目/全局 Python | ✅ 已装·版本实测 |
| Git | 2.55.0 | 版本管理（M6–M8 配套） | ✅ 已装 |
| Node.js | LTS（按需） | 工具链（若用到） | 按需 |

## 2. 运行时环境（阶段一）

| 项 | 需求 | 说明 | 状态 |
|---|---|---|---|
| WebView2 运行时 | 最新稳定版 | Evergreen Runtime `155.0.4283.62`；WinUI 3 隐藏样例已真实初始化、渲染、截图并完成 WebMessage 往返 | ✅ 已验证 |
| CV3 语音（推理） | 模型权重 + 推理环境 | CosyVoice3 全套（llm.pt / flow.pt / hift.pt / speech_tokenizer_v3 / CosyVoice-BlankEN）+ sherpa-onnx ASR/VAD/KWS 位于 `H:\UltimaAI\UltimaAgent\Topo Backup\C_Guixu\source\guixu-v1.04.00-phase6.3.02-cross-platform-matrix\apps\desktop-host-winui\qa\VOICE_041_V0_20261010_R1\models`；75 个 manifest 文件、3,653,036,664 bytes 哈希全匹配 | ✅ 已验证完整性与推理 |
| CV3 语音（兼容运行库） | 固定 Python 3.10 运行库 | 只读引用 `H:\UltimaAI\UltimaAgent\Topo Backup\C_Guixu\v0r3\cv3\TtsProbe\runtime310\python`（Python 3.10.22）；缺失的 `setuptools 75.6.0` 仅叠加于本项目 `tools\cv3-runtime-overlay`，未改备份运行库 | ✅ 已验证 |
| 语音管线 | TD-03 评估后冻结 | Pipecat / LiveKit 候选；CV3 集成方式未定 | 待评估 |
| 任务管线 | 执行器/派发器/审计回执 | 本轮仅验证已有真实 Codex 派发会话、事件流、可执行接口及既有审计完成回执；未实现或启动工单①队列引擎 | ✅ smoke 通过 |
| 凭证中心 | 本地加密凭证库 | `_shared\vault\vault.ps1` + DPAPI CurrentUser 加密文件；`list` 只读解密验证退出 0，未读取/输出凭证正文 | ✅ 已验证 |

## 3. 待评估依赖（TD 挂起，评估后冻结回填）

| 项 | 候选 | 影响环境 | 状态 |
|---|---|---|---|
| 记忆底座（TD-02） | Cognee / MemLayer / agentmemory / Mem0 / Zep / Letta / 自研 | 向量库/知识图谱存储需求（磁盘/内存/可选 GPU） | 待评估 |
| 本地模型通道 | GPT4All 类 / 云端 API | GPU 或云端凭证；算力主机部署形态 | 待评估 |
| 组合窗口 UI 协议（TD-01） | A2UI / 自研 | 渲染器依赖（WebView2 或原生） | 待评估 |

## 4. 硬件基线（算力主机）

| 项 | 基线建议 | 说明 |
|---|---|---|
| CPU | 8 核+ | 能力层/编排/执行 |
| 内存 | 32GB+ | 本地模型 + 记忆 + 多任务 |
| GPU | 可选（本地推理时建议 NVIDIA 8GB+） | 本地 LLM/CV3 推理 |
| 磁盘 | 工作区 + 模型权重（H 盘可用 5.5TB） | Ultima 工作区在 H:\Ultima Agent |
| 设备 | NAS/传感器/空调（阶段二+） | 设备集群接入（device-cluster） |

## 5. 平台前瞻（阶段二/三）

| 阶段 | 环境需求 |
|---|---|
| 阶段二 macOS | 宿主抽象层（IO/渲染跨平台接口）+ macOS 壳工程（Xcode 或跨平台栈）；能力层零改动 |
| 阶段三 Linux 自研 | Linux 发行版 + 内核裁剪/驱动/自启/安全工具链；系统层研发环境 |

## 6. 依赖锁定与安装流程（工程骨架整合）

- 目录树：见工作区 README（权威目录登记处）。
- 依赖锁定：Python `requirements.lock`（能力层）、.NET SDK 8.0.425（宿主壳，用户目录安装）、前端/工具链按需锁定。
- 安装流程（阶段一）：
  1. 环境门复检（§7 清单）→ 未就绪项按项安装；
  2. .NET PATH 修复（OPEN-06）：用户 PATH 已将 `C:\Users\Administrator\.dotnet` 置前；本项目包装器显式固定该路径，避免长驻旧进程继承旧 PATH；
  3. CV3 模型引用登记（OPEN-10）：显式引用已迁移到 H 盘备份区的 QA models；CV3 固定使用兼容 Python 3.10.22，不与能力层 Python 3.13.13 混用；
  4. WebView2 运行时确认（OPEN-08）+ 样例真实初始化/渲染/WebMessage 往返；
  5. 任务管线 smoke test 仅核对真实已有派发事件流与审计回执，不在本工单重建工单①引擎。
- 就绪检查按 §7.1 阶段门执行；§7 保留项目依赖盘点，不再把语音/队列引擎验收设为宿主壳前置。

## 7. 就绪检查清单（环境门 · DoD）

- [x] Windows 11 + Git 可用（`git --version` → 2.55.0）✅
- [x] .NET SDK 8.0.425 可编译 WinUI 3 x64 空壳（Windows App SDK `1.8.260921001`；0 error / 0 warning）✅
- [x] Python 3.13.13 x64 可用（项目隔离工具链包装器实测）✅
- [x] WebView2 Runtime `155.0.4283.62` 可用（真实初始化 + HTML 渲染截图 + WebMessage 往返）✅
- [x] CV3 推理模型已下载完整（CosyVoice3 + sherpa-onnx ASR/VAD/KWS；manifest 75/75 哈希匹配）✅
- [x] CV3 推理 smoke test 通过（固定文本本地 TTS 2.88 秒非静音 WAV；保存 WAV 本地 ASR 非空转写；外部推理请求 0、费用 ¥0）✅
- [x] 任务管线可运行（当前真实派发事件流 + Codex CLI + 既有审计完成回执只读 smoke；未代做工单①）✅
- [x] 凭证中心可用（DPAPI CurrentUser 只读解密/list 验证；未输出凭证正文）✅
- [x] TD-01/02/03 已登记并冻结为 ADR-007/008/009，不阻塞基线✅

## 7.1 分阶段环境门（2026-10-21 Owner 直接批准）

授权原文：用户对“宿主壳验收 .NET/WinUI/WebView2；语音与任务管线分别在原对应工单保留强制验收”的方案回复“允许按阶段拆分”。

| 阶段/工单 | 阻断该阶段的强制门 | 不得混淆的证据 |
|---|---|---|
| 工单② 宿主壳 T1→T2 | Windows/Git 前提；.NET SDK 8.0.425 与 WinUI3 真实构建；WebView2 Runtime 真实初始化、渲染及双向通信 | 不因 CV3 或工单①产物尚未验收而阻断壳开发 |
| 工单③ 语音 PoC | 已登记模型/运行库、完整性校验、真实 TTS/ASR smoke 及该工单原全部 Gate | 此次环境 smoke 不代替语音产品链路/质量/时延验收 |
| 工单① 队列引擎 | 项目 Python 3.13.13、实际派发/执行/审计/回执/恢复与该工单原全部 Gate | 本次 Codex 派发和既有审计回执可读不等于队列引擎完成 |

- §7 九项盘点和历史 3 GREEN/6 RED 均保留；本轮实际已获得 9 GREEN/0 RED，不将批准解释为删除未完成检查。
- 凭证、安全、版本与 ADR 约束继续适用于各自使用场景；未豁免、不改锁定版本。
- 工单①和②仍可按原依赖图并行，阶段之间按各自冻结门衔接；本轮只执行工单②。

## 8. 变更日志

| 版本 | 日期 | 变更内容 |
|---|---|---|
| v1.0 | 2026-10-16 | 初版：Windows 阶段一基线 + TD 待评估依赖 + 硬件基线 + 环境门清单 |
| v1.1 | 2026-10-16 | 实测回填：.NET SDK 8.0.425（PATH 待修）/ Python 3.13.13 / Git 2.55 / CV3 推理模型已完整（CosyVoice3+sherpa-onnx，VOICE_041 QA）；训练环境未装留待办 |
| v1.2 | 2026-10-16 | 工程骨架整合：新增 §6 依赖锁定与安装流程（依赖锁定/安装四步/就绪检查 DoD） |
| v1.3 | 2026-10-16 | OPEN-06/07 闭环：.NET PATH 已修复（用户 PATH 置顶 .dotnet）；CV3 训练环境确认已装（runtime310 内嵌 Python 3.10.22 全依赖 OK，路径登记） |
| v1.4 | 2026-10-21 | 工单②修复续行实测回填：项目隔离 Python 3.13.13；H 盘模型与 CV3 Python 3.10.22 兼容运行库新路径；WinUI/WebView2、TTS/ASR、派发/审计与 DPAPI vault 真实 smoke 全绿；保留旧进程 PATH 漂移事实并以项目包装器规避。 |
| v1.5 | 2026-10-21 | Owner 直接批准按阶段拆分环境门，新增 §7.1；保留九项历史与本轮真实证据，语音/任务管线在原对应工单仍强制验收。 |
