# v0.1 冻结审批材料（Owner已批准，已冻结）

本次提交范围：阶段一v0.1环境与承载底座，即工单①队列引擎与工单②宿主壳。不包含后续语音/文本/组合窗口/安装更新完成声明。

| 审批依据 | 证据与结论 |
|---|---|
| W2 | 独立35项验收、62项回归、真实卡及修正子任务→父任务闭环；20份核心源码未变；内部tag wo-s1-queue-engine-done |
| W1 | 独立第四轮技术及系统清理门通过，U01-U05覆盖；内部tag wo-s1-host-shell-done |
| 维护重启 | 新旧开机基线已对比，旧59328创建身份消失；直接内核查询与原生枚举一致；Default输入桌面可用 |
| 正式自检 | w1-post-reboot-final-positive-20261021T0400 PASS/exit0；final-negative-20261021T0401缺Runtime按预期FAIL/exit1；额外窗口0、后台身份保留 |
| 产物绑定 | 0warning/0error，源码运行前后一致，实际进程路径、EXE/DLL与独立清单核对一致 |
| 既有功能 | 真实144/96/96DPI、180逻辑尺寸、位置保持/恢复；原生窗口和真实鼠标拖动已有独立证据 |
| 队列状态 | 两单完成状态、项目镜像及统计已按监督验收同步；旧执行失败回执没有改写 |

## 已知运行限制与历史失败

真实工程派发适配器已接入并经独立代码检查；原host工单Codex进程完成文件后卡在update_plan，监督核验后结束，原done仍为exit125/receipt_valid=false/BLOCKED。本次工单完成依据为后续独立验收与监督收口，不把旧运行伪写成成功，也不宣称已证明长期无人值守Codex连续派发。该限制在冻结审查中保留。

审批证据入口：`w1-independent-acceptance-20261021.md`第四轮、`w2-independent-acceptance-20261021.md`第二轮、`evidence/w1-post-reboot-closeout-20261021/`及两个实际内部tag。

Owner于2026-10-21明确批准：“批准按当前基线冻结 v0.1”。已登记tasks/queue/gates/v0.1-frozen.json并创建v0.1-frozen，固定获批基线43ce13021f16f191bb36615ebb6c68465bf201fa。原提交材料已独占保存于evidence/v01-freeze-20261021/approved-request.md；本次是版本冻结授权，后续工单尚未派发，未远端发布。
