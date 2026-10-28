# 任务卡：s1-remote-update-trigger

- **task_id**：s1-remote-update-trigger
- **stage**：S1（阶段一 v1.0）
- **工单**：工单⑧（wo-s1-remote-update，原工单⑦ 顺延）· U23
- **标题**：三触发（启动自检/手动检查/静默强制）+ 更新 UI
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为远程更新的触发链路与用户界面；更新资产 = 工单⑦（工程封装）安装包

## goal

实现三种更新触发：启动自检（启动时查 latest，有新版提示/静默更新）、手动检查（设置页"检查更新"按钮）、静默强制（服务端强制版本号 > 当前 → 无条件后台更新）；并实现更新 UI（设置页入口、更新中/完成/失败状态展示）。全程零弹窗（后台静默更新）。禁止：不实现发布端（T3）、不实现通道基础库（T1，本层只接需求）、任何前台弹窗。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 启动自检 PASS（启动时查 latest，有新版正确提示）
- [x] ACCEPT: 手动检查 PASS（设置页"检查更新"按钮触发）
- [x] ACCEPT: 静默强制 PASS（服务端强制版本号 > 当前 → 无条件后台更新）
- [x] ACCEPT: 更新 UI PASS（设置页入口、更新中/完成/失败状态正确展示）
- [x] ACCEPT: 全程零弹窗（前台零弹窗绝对纪律 N7，闪一下都不行）

## dependsOn[]

- s1-remote-update-channel（通道基础库就绪后接线；版本级前置 v0.2+v0.4 冻结登记于工单总卡 wo-s1-remote-update.md）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\update\`（触发链路接线）
- `H:\UltimaAI\UltimaAgent\src\ui\`（设置页更新入口，DSL 组件）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-remote-update-trigger\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- high（三触发状态机 + 零弹窗强制）

## category + skill

- category: system + ui · skill: eng.code + eng.ui（设置页入口）

## receipt（完成时由 CodeX 回填）

- reviewReason: 主脑直做（用户指令"由你完成，不需要我参与"），不派 Codex；三触发状态机 + 零弹窗纪律经单测与冒烟核验
- stdoutText: 25/25 单测全绿（含 T2 触发 10 用例 + UI 服务桥 4 用例）；真实 Release 冒烟 PASS；更新 UI 页 src/ui/update_page.html + 服务桥 src/update/ui_server.py 可运行
- evidence: 三触发场景实测 + 更新 UI 状态展示（tests/test_update_triggers.py、test_update_ui_server.py、smoke JSON）
- acceptance 逐项核对: 5/5 全绿（见上）

## retryCount

- 0（上限 2，超限转 BLOCKED）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| RU-05 启动自检 | 启动时查 latest，有新版提示/静默更新 | 触发正确；查询失败/无网络 → 静默降级不打扰、记日志、不误报新版（N6） | 启动实测 |
| RU-06 手动检查 | 设置页"检查更新"按钮 | 点击触发更新检查；查询失败/无网络 → 静默降级不打扰、记日志、不误报新版（N6） | 点击实测 |
| RU-07 静默强制 | 服务端强制版本号 > 当前 → 无条件后台更新 | 强制更新生效；查询失败/无网络 → 静默降级不打扰、记日志、不误报新版（N6）；运行期窗口枚举计数 0（零弹窗 N7） | 强制用例 |
| RU-08 更新 UI | 设置页入口 + 更新中/完成/失败状态 | 状态展示正确、零弹窗 | 截图核对 |
