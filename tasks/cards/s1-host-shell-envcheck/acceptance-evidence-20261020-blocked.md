# 验收证据

## Gate

- 判定：`FAILED / BLOCKED`
- 计数：`3 GREEN / 6 RED`
- 权威证据：`logs/environment-check-2026-10-20.md`

## acceptance[] 逐项核对

- PASS：九项均已列出项名、版本/路径/证据与状态。
- FAIL：未达到九项全部 GREEN；.NET PATH、Python 锁定版本、WebView2 样例加载、CV3 模型、CV3 smoke、任务管线 smoke 为 RED。
- PASS：检查表已落 `logs/environment-check-2026-10-20.md`。

## 关键原始结果摘要

- `git --version` → `git version 2.55.0.windows.3`
- 裸 `dotnet --version` → 未找到 SDK，退出码 `-2147450725`
- `C:\Users\Administrator\.dotnet\dotnet.exe --version` → `8.0.425`
- `python --version` → `Python 3.13.16`
- WebView2 Runtime 目录版本 → `155.0.4283.60`、`155.0.4283.62`
- 规范登记的 CV3 模型目录 → 不存在

T1 禁止修改环境，因此本轮没有可授权的自修；后续任务未执行。

## I3 结构化失败回执

- 失败命令/动作：从项目根执行裸 `dotnet --version`，验证规范锁定的 .NET SDK PATH。
- 错误原文：`No .NET SDKs were found.`；`The application '--version' does not exist or is not a managed .dll or .exe.`；进程退出码 `-2147450725`。
- 根因判断：PATH 首个 `dotnet` 为 `C:\Program Files\dotnet\dotnet.exe`，该安装没有 SDK；SDK 8.0.425 实际位于 `C:\Users\Administrator\.dotnet`，故裸命令解析错位。其余 RED 还包括 Python 锁定版本漂移、WebView2 未做样例加载、CV3 登记路径缺失及无真实 smoke、任务管线无可运行 smoke。
- 下一步计划：由主脑另行授权环境修复或修订环境基线；至少修复 .NET PATH、拍板 Python 版本、恢复/登记 CV3 模型、补真实 WebView2/CV3/任务管线 smoke，再重新派发 T1。T1 当前禁止安装或修改环境，因此本进程不越权处理。

## §8 自核记录

- 第 1 次自核：发现落地清单缺 I1 文件动作前缀，且 I3 四段式不够明确。
- 第 1 次自修：补齐 `NEW_FILE/MODIFY_FILE` 前缀与“失败动作/错误原文/根因/下一步”四段式。
- 自核结论：回执结构已闭合；任务 acceptance 因 6 项 RED 仍未全绿，按 fail-closed 提交 BLOCKED 回执。
