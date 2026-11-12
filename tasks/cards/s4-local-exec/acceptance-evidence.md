# s4-local-exec 验收证据

- 日期：2026-10-27（Asia/Shanghai）
- 结论：COMPLETED
- 实现：本机执行通道 `src/brain/exec/channel.py`（M12）
- 约束：仅标准库 + UltimaAgent 自有模块（ctypes user32 窗口枚举、复用 environment_upgrade.scan_processes）；pywinauto 仅预留 register_control 接线点，未安装

## 实际命令与结果

1. `python -m unittest src.brain.exec.tests.test_exec_s4 -v`
   - `Ran 6 tests` → `OK`（ACCEPT-1~6）
2. 测试数据全落 tempfile，未污染真实库

## ACCEPT-1~6

| ID | 结果 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | 只读默认：write/exec/control 未授权全部 denied 且带 reason，审计 exec.denied 留痕 |
| ACCEPT-2 | PASS | 桌面窗口只读探测：EnumWindows 枚举可见顶层窗口（hwnd/title/pid 齐全）+ 进程扫描可用 |
| ACCEPT-3 | PASS | 白名单登记+注册实现后可执行（open_app→executed+re_observe）；未登记拒绝；已登记未注册实现拒绝（dynamic control 预留点） |
| ACCEPT-4 | PASS | 操作后重新观察接口：re_observe() 返回新快照（ts/window_count/process_count/fresh），perform 每次动作强制携带 |
| ACCEPT-5 | PASS | 审计留痕：exec.executed / exec.denied 均落盘，拒绝带 reason |
| ACCEPT-6 | PASS | 回执字段完整（action/decision/outcome/result/re_observe），decision.verdict=allow |

## 关键实现约束

- 闸门前置（只读默认）：list/read/observe 放行；write/exec/control 需白名单+征询+注册实现，三层缺一拒绝；
- 控制动作默认禁用：_controls 注册表默认空，第三方（pywinauto/UIA）可用时经 register_control 接线；
- 每次动作后强制 re_observe 新快照；
- 全部动作过 AppendOnlyAuditLog 留痕。
