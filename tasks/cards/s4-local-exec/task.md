# 任务卡：s4-local-exec
- **task_id**：s4-local-exec
- **标题**：本机执行通道（M12）：桌面控制 + 闸门前置 + 只读默认
- **优先级**：70（P1）
- **reasoningEffort**：medium
- **category**：core　**skill**：engineering
- **依赖**：s3-guard-resident、s3-bus-kernel
- **登记核验**：已查注册表与产品对齐报告（product-alignment-20261027.md 缺口 N2）；本机执行通道当前缺失（无 pywinauto/UIA 控制层）；环境认知扫描（s3-env-cognition）只读通道可复用；依赖约束 = 仅标准库 + UltimaAgent 自有模块，不引入未审批第三方依赖。

## goal
建立本机执行通道（M12），对齐"只读默认 + 闸门前置 + 操作后重新观察"：
1. 动作分类闸门：list/read 类只读动作放行；write/exec/control 类动作需白名单登记 + 高危征询，未授权一律拒绝；
2. 桌面窗口只读探测：ctypes user32 枚举顶层窗口/进程/可读属性（无第三方依赖）；
3. 进程/文件只读通道：复用 environment_upgrade 扫描能力，控制动作默认禁用（dynamic control 注册点预留，第三方可用时才启用）；
4. 操作后重新观察接口：action → re-observe 循环（每次动作后强制重新观察）；
5. 全部动作过总线审计留痕（拒绝动作带 reason）。

**禁止**：
- 禁止绕过闸门执行写操作/控制动作；
- 禁止引入未审批第三方依赖（pywinauto 仅预留注册点，不安装）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：只读默认——未授权控制动作一律拒绝（write/exec/control 全拒）
- [ ] ACCEPT-2：桌面窗口只读探测可用（枚举窗口/进程/属性）
- [ ] ACCEPT-3：白名单登记后可执行动作；未登记拒绝
- [ ] ACCEPT-4：操作后重新观察接口存在并返回新快照
- [ ] ACCEPT-5：审计留痕（动作/拒绝带 reason）
- [ ] ACCEPT-6：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：本机执行通道（M12，P1） |
