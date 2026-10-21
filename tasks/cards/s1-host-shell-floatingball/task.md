# 任务卡：s1-host-shell-floatingball

- **task_id**：s1-host-shell-floatingball
- **stage**：S1（阶段一 v0.1）
- **标题**：悬浮球占位窗口（可拖动）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为悬浮球占位实现（四状态绑定属 v0.4 U17）

## goal

实现悬浮球占位窗口：无边框置顶、鼠标可拖动、常驻桌面不干扰。禁止：不实现四状态动画（v0.4 U17）、不实现语音交互（v0.2）、不实现小组件（v0.4 U15/U16）。

## acceptance[]（封闭验收清单，逐项可核对）

- [x] ACCEPT: 悬浮球窗口显示（无边框、置顶）
- [x] ACCEPT: 鼠标拖动生效（拖动后位置保持）
- [x] ACCEPT: 真机截图可证

## dependsOn[]

- s1-host-shell-webview2（T3 渲染层就绪）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\host-shell\`（悬浮球窗口代码）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-floatingball\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- medium（窗口属性 + 拖动逻辑）

## category + skill

- category: host-shell · skill: eng.ui（UI 工程师）

## receipt（完成时由 CodeX 回填）

- reviewReason: T4 三项封闭验收均由真实 Presenter 状态、物理鼠标输入、DPI 量化与像素截图证明，提交监督端 W1 独立验收
- stdoutText: PASS — 无边框/置顶；真实鼠标拖动 `(-160,-100)`；松手后 1 秒位置漂移 `(0,0)`；144 DPI 下 180 逻辑像素=`270×270` 物理像素
- evidence: `logs/host-shell-repair-20261021T061613/t4-build.log`、`t4-floating-ball-ready.json`、`t4-drag-evidence.json`、`t4-floating-ball.png`
- acceptance 逐项核对: FB-01 PASS；FB-02 PASS；FB-03 PASS

## retryCount

- 2（编译器歧义自修；WebMessage 拖动改为系统非客户区 Caption 拖动并修正 Presenter 证据口径）

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| FB-01 无边框置顶 | 悬浮球窗口无边框、置顶 | 属性正确 | 截图 |
| FB-02 拖动逻辑 | 鼠标拖动 + 位置保持 | 拖动生效 | 真机截图 |
| FB-03 DPI 缩放适配 | 多 DPI 下位置不偏移 | 高 DPI 无偏移 | 真机测试 |

## 2026-10-21 W1 恢复追加证据

- 新增仅 `ULTIMA_HOST_DPI_ACCEPTANCE=1` 启用的真实硬件仪器；正常启动和默认产品模式不变。
- 首次复现即通过，未进入 FloatingBall 产品配置修复分支：`logs/w1-host-resume-20261021T024845Z/t2-initial-reproduction-attempt3/t2-initial-dpi-acceptance.json`。
- 最终复验：`t3-dpi-final/t3-dpi-dpi-acceptance.json`。DISPLAY3 实测 144 DPI/270×270 物理，DISPLAY2/1 实测 96 DPI/180×180；三处逻辑尺寸均 180×180，Caption 拖动区同步，每处保持 1 秒漂移 0，恢复漂移 0。
- 移动仅使用宿主自身 `AppWindow.Move`；未伪造 `WM_DPICHANGED`，未改变系统 DPI/显示设置。最终真实鼠标拖动仍由 root 复核，本节不自批 W1。


## 2026-10-21 维护重启后独立收口

Owner授权维护重启已实际完成；原59328创建身份已不存在，原生枚举与直接内核查询交叉确认，系统清理门解除。正式入口新正向PASS/exit0、缺Runtime负向FAIL/exit1，0警告/0错误、额外窗口0、当前开机后的后台身份保留。独立第四轮验收允许工单内部收口；最终证据见 `docs/reports/evidence/w1-post-reboot-closeout-20261021/` 与 `docs/reports/w1-independent-acceptance-20261021.md`。旧派发exit125/BLOCKED和历次失败保留。内部tag为wo-s1-host-shell-done；v0.1仍待Owner单独审批。
