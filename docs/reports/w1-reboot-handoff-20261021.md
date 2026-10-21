# W1 维护重启与续验交接 · 2026-10-21

用户直接授权：“允许在维护窗口重启 Windows，之后继续复验并收口 W1”。这不是v0.1冻结批准。当前功能U01-U05已独立通过，整单W1仍因旧自检pwsh59328（创建身份134370250506523457）未真实退出而阻塞；W2内部tag已建立，20份核心源/测试清单不可漂移。

## 维护安排

脚本 `scripts/w1-maintenance-restart.py` 先保存开机时间估计、实际Codex角色、Git提交及全局队列副本，并在共享队列与产品tasks下建立带独有token的`.pause-dispatch`。原有暂停标记保留。维护证据目录 `logs/maintenance/w1-restart-20261021/`；before.json记录token与每个标记归属/哈希。arm后隐藏助手延迟60秒，重新检查无实际exec/用途不明进程、无登记executing、暂停标记未改变，才调用Windows正常重启。没有/f；未保存应用可能阻止正常重启。记录请求不代表已经重启，必须以新开机基线确认。

已登记本聊天heartbeat `windows-ultimaagent-w1`（15分钟续验），在Codex可运行时继续。若Windows登录后Codex未自动恢复，需用户打开Codex；不改变自动登录或安全设置。不要重复发起重启。

## 重启后执行顺序

1. 先读docs/INDEX.md与独立W1第三轮报告、w1-root-followup-20261021.md。比较本次before.json开机时间估计与当前GetTickCount64估计，确认实际重启发生；记录新的boot/进程身份，不能要求重启前所有PID保持不变。
2. 查询旧59328创建身份已消失；若PID复用，不结束新进程。确认维护暂停标记token与before.json相同，并保护其他项目正在恢复的任务。
3. 从正式 `tools/python31313/python.exe -X utf8 scripts/selfcheck-host-shell.py` 执行全新正向，再以`--missing-runtime`执行负向。检查0warn/0error、真实进程路径、源码前后/EXE/DLL哈希、额外窗口0、原生退出；正向exit0/PASS，负向exit1/FAIL。保留失败轮。
4. 核对W2 round2的20份核心源码未变；按最新源与产物绑定证据进行独立W1收口。旧真实派发exit125/receipt_validfalse/BLOCKED原样保留，不能补写成该次成功。
5. W1通过后补五卡/工单/权威文档登记，在共享锁内更新全局工单与队列统计、sync/product.json，创建内部tag `wo-s1-host-shell-done`。所有结论须有独立回读。
6. 仅删除本维护实际创建且token/哈希匹配的暂停标记；不要删原有暂停。W1/W2完整通过后才提交v0.1冻结审批，未获Owner审批前不创建v0.1-frozen或Owner PASS、不派发冻结门后工单/远端发布。
7. 在完成或必须人工处理的阻断后停用本次heartbeat，避免反复验收/派发。状态无变化时保持安静。

不将未重启、用户登录未恢复、桌面未解锁或只见进程启动解释为验收通过。

补充：维护准备时通用process_identity(59328)返回null，但直接内核GetProcessTimes仍读到原创建身份，exitCode1、wait258、exitTime0。null不能作为旧进程消失证据；复验须直接内核创建时间+等待状态、原生枚举交叉核对。直接核对保存于 `logs/w1-host-resume-20261021T024845Z/after/root-maintenance-preflight-process-state.json`。
