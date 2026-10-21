# v0.1 冻结审批材料（准备中，尚未提交审批）

Owner 授权顺序：W2独立验收→宿主剩余修复与W1→真实工程工单派发接入→两门通过后提交v0.1冻结审批。

| 前置 | 当前证据 | 状态 |
|---|---|---|
| W2 独立技术验收 | w2-independent-acceptance-20261021.md 第二轮；35项通过，62项回归无失败；原始失败保留 | 技术通过 |
| 队列引擎源码基线 | 本地 Git `e77f417a17802601655096db0fef3224450e2abf`；20个源码/测试文件与独立清单逐字节一致 | 内部tag wo-s1-queue-engine-done已创建，全局工单闭环 |
| W1 宿主环境及运行 | w1-independent-acceptance-20261021.md第三轮：U01-U05功能通过；真实144/96/96DPI、270/180/180物理像素、180逻辑尺寸、保持/恢复均通过 | 功能通过，系统清理门阻塞 |
| 原生桌面及鼠标 | logs/w1-final-native-2026-10-21T03-08-13-206Z/；logs/w1-final-mouse-20261021T0313/；最终构建深色/中文可见，真实鼠标移动90像素，24秒无漂移 | 已独立复核 |
| 正式自检交付 | scripts/selfcheck-host-shell.py + scripts/HostSelfcheck；logs/w1-delivered-selfcheck-verified-path-positive-20261021T0324与negative-20261021T0325；源码前后及EXE/DLL哈希一致、实际进程路径正确 | 正向PASS/exit0，缺Runtime负向FAIL/exit1，额外窗口0 |
| W1系统清理 | 旧自检pwsh59328，创建身份134370250506523457；WaitForSingleObject=258、exitCode=1、exitTime=0；同句柄精确TerminateProcess返回AccessDenied5 | 未确认退出，整单W1 BLOCKED |
| 工程派发接入 | 本地Git 80c72f3；scripts/dispatch-work-order.py独立审查及5项测试通过；真实PID17252完成报告后卡在update_plan，核验身份后定向结束；done exit125、receipt_valid=false、BLOCKED | 已实际接入并保留失败闭合，尚无成功业务收口 |
| W1/W2内部工单tag | W2内部tag已存在；宿主tag待系统清理门及整单独立验收 | W1未创建；未创建v0.1-frozen |
| Owner版本决定 | 本文准备中，不代表审批 | 尚未请求/未批准 |

## 提交条件

- W1独立逐项通过，包含真实144/96DPI、鼠标拖动、最终构建原生显示、退出与后台进程保护证据。
- W2源码哈希与已接受版本一致；任何后续引擎改动须重新独立验收。
- 工程派发真实进程结束且有结构化回执、运行记录、登记状态独立回读，不能仅凭进程曾启动判通过。
- 形成最终源码/产物/证据哈希与本地Git提交；补内部工单tag，不把内部tag当作Owner版本冻结。
- 本文更新为“待Owner审批”后才提交。批准前不创建 `v0.1-frozen`，不生成Owner通过凭据，不启动依赖此门的语音/文本工单。

当前剩余实质阻塞是旧自检pwsh内核残留。需独立解决，或在获准维护窗口重启后确认消失，再从正式入口复验及独立签署W1；不能用任务管理器命令曾返回成功代替真实退出。全局W2闭环/W1阻塞及项目镜像已同步，见logs/stage1-gate-sync-20261021T032426412442Z/。旧派发失败回执保留，root补验不改写其退出码。

审批范围仅为阶段一v0.1环境与承载底座；不包含尚未实现的语音/文本/组合窗口/安装更新完成声明。不执行远端发布或创建公开仓库。
