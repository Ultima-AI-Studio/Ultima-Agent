# 任务卡：s1-host-shell-envcheck

- **task_id**：s1-host-shell-envcheck
- **stage**：S1（阶段一 v0.1）
- **标题**：环境门 9 项核对（开工前置正式化）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为 environment-spec §6 的就绪核对

## goal

按 environment-spec §6 核对 9 项环境依赖（.NET SDK / Python / CV3 权重与运行库 / 构建工具链 / WebView2 Runtime 等），输出就绪检查表，按 environment-spec §7.1 的宿主阶段门标记开工通过；九项全局依赖仍逐项如实记录。禁止：不安装/不修改任何环境（只核对记录，安装属前置环境门已完成）、不进入宿主壳代码编写（T2）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 9 项核对项逐一列出（项名 + 版本/路径 + 状态）
- [x] ACCEPT: 宿主阶段强制门全部 GREEN（任一宿主门不绿 → FAILED；语音/管线留在各自原工单强制验收，未验证项如实记录）
- [x] ACCEPT: 就绪检查表输出落盘（logs/environment-check-<date>.md）

## dependsOn[]

- （无，本任务为工单②首任务）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\logs\`（检查表落点）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-envcheck\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- low（机械核对 + 落盘）

## category + skill

- category: host-shell · skill: eng.infra（运维工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: 用户于 2026-10-21 授权修复续行后，项目隔离补齐 Python 3.13.13 与 CV3 兼容层，修正迁移路径，并以真实 WinUI/WebView2、TTS/ASR、派发/审计及 DPAPI 只读 smoke 复验；九项均有明确 PASS 证据。
- stdoutText: T1 修复复检完成，9 GREEN / 0 RED，Gate PASS；允许按顺序进入 T2。
- evidence: `logs/environment-check-2026-10-21.md`；`docs/reports/evidence/stage1-host-shell/T1-envcheck.md`；`acceptance-evidence.md`
- acceptance 逐项核对: 九项枚举 PASS；九项全绿 PASS；检查表落盘 PASS。

## receiptHistory

- 2026-10-20：3 GREEN / 6 RED，Gate FAILED / BLOCKED；原三件套已保留为 `*-20261020-blocked.md`，原检查表保留于 `logs/environment-check-2026-10-20.md`。

## retryCount

- 1（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| EN-01 核对项枚举 | 9 项依赖逐一列出（项名/版本/路径） | 9 项全列出 | 检查表 |
| EN-02 状态判定 | 每项 GREEN/RED 判定 | 状态标注齐全 | 检查表 |
| EN-03 就绪报告落盘 | 检查表输出 logs/environment-check-<date>.md | 报告存在 | 文件核对 |
| EN-04 缺口上报 | 任一 RED → FAILED + 记录缺口 | 不静默通过 | 回执核对 |

## 2026-10-21 Owner 阶段门批准

按 environment-spec §7.1 执行；本轮历史九项仍已实测 9 GREEN/0 RED，不回写历史失败记录。

## 2026-10-21 W1 恢复追加证据

- 修改前源码、脚本、五卡副本及 SHA-256：`logs/w1-host-resume-20261021T024845Z/before/`。
- 修改前后台进程 PID、创建时间、命令行基线：`before/process-baseline.json`；本轮未重启或终止其他开发任务。
- 本节只追加 W1 恢复证据，不改变原环境门结论，不表示 W1 或 Owner 冻结。
