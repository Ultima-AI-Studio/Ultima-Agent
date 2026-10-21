# 落地文件清单

- NEW_FILE `tools/python31313/**`：Python.org 官方 3.13.13 x64 项目隔离运行时。
- NEW_FILE `tools/_downloads/python-3.13.13-embed-amd64.zip`：官方安装源，SHA-256 已校验。
- NEW_FILE `tools/cv3-runtime-overlay/**`：仅本项目使用的 `setuptools 75.6.0` 兼容叠加层。
- NEW_FILE `scripts/host-shell-toolchain.ps1`：显式固定 .NET 8.0.425 / Python 3.13.13 的无窗口包装器。
- NEW_FILE `logs/host-shell-repair-20261021T061613/probes/**`：WinUI/WebView2、模型完整性和 TTS 临时探测代码及构建侧效应。
- NEW_FILE `logs/host-shell-repair-20261021T061613/{result.json,webview-render.png,model-integrity.json,asr-smoke.json,tts-smoke.json,tts-smoke.wav,task-pipeline-probe.json,credential-vault-probe.json}`：真实运行证据。
- NEW_FILE `logs/environment-check-2026-10-21.md`：九项全绿复检表。
- MODIFY_FILE `docs/specs/environment-spec.md`：仅修正事实路径、实测版本、安装与验证记录（v1.4）。
- MOVE_FILE `completion.md` / `landed-files.md` / `acceptance-evidence.md` → `*-20261020-blocked.md`：保留历史失败三件套。
- MODIFY_FILE `tasks/cards/s1-host-shell-envcheck/task.md`：回填本轮 PASS receipt 与历史指针。
- NEW_FILE `docs/reports/evidence/stage1-host-shell/T1-envcheck.md`：T1 Gate 证据。
- NEW_FILE `docs/reports/stage1-host-shell-20261021.md`：本工单阶段报告（T1 先行落盘）。

未修改 `_shared`、`docs/INDEX.md`、全局队列、冻结架构/ADR/语音方案或其他工单。


## 重启后最终证据

- `docs/reports/evidence/w1-post-reboot-closeout-20261021/`：维护、正负向、源/产物绑定及清理证据副本。
- `docs/reports/evidence/w1-independent-20261021/round4-post-reboot/`：独立验收。
- 本任务产品实现未在本轮变更，旧文件和失败证据保留。
