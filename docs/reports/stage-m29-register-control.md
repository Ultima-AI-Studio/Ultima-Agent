# M29 登记控制面阶段报告

> 工单：`wo-ultimaagent-20261029-0001`
> 执行日期：2026-10-29（Asia/Shanghai）
> 技术结论：T0→T3 封闭 Gate 全绿；本报告不代签 Owner 冻结/发布门。

## Gate T0 · 工单编号核发

- [x] T0-C1：同日编号 `0001/0002/0003` 递增，跨日从 `0001` 重算。
- [x] T0-C2：格式全匹配 `^wo-[a-z]+-\d{8}-\d{4}$`，Asia/Shanghai 日期入号。
- [x] T0-C3：历史 UUID `task_id` 读取兼容；并发抢号通过独占锁 fail-closed 为 `OrchestratorError`。
- 证据：[`t0-numbering-tests.txt`](evidence/m29-register-control/t0-numbering-tests.txt)。

## Gate T1 · 全局主表登记

- [x] T1-C1：`enqueue/advance/complete` 串接 Registrar，项目汇总行与明细行在临时主表正确更新。
- [x] T1-C2：状态流转映射 `pending/executing/audit/frozen`，与 `queue-status-gen.py` 的统计口径一致。
- [x] T1-C3：目标路径越出配置的 `_shared/queue/` 授权根即拒绝；表不可用时 warning 且不阻断本地状态。
- 证据：[`t1-global-registrar-tests.txt`](evidence/m29-register-control/t1-global-registrar-tests.txt) / [`t1-temporary-global-table-sample.md`](evidence/m29-register-control/t1-temporary-global-table-sample.md)。

## Gate T2 · WIP 双层校验

- [x] T2-C1：全项目执行中为 3 时第 4 单拒绝。
- [x] T2-C2：同项目执行中为 1 时第 2 单拒绝。
- [x] T2-C3：全项目审计中为 1 时新审计拒绝；未超限返回结构化放行结果。
- 证据：[`t2-wip-tests.txt`](evidence/m29-register-control/t2-wip-tests.txt)。

## Gate T3 · 总验收

- [x] 指定解释器运行 `python.exe -m pytest src -q --disable-warnings`，退出码 0。
- [x] 全量结果：`679 passed, 37 warnings, 120 subtests passed`。
- [x] 阶段报告、T0–T3 证据与临时主表样例已落盘。
- [x] 真实 `global-queue-index.md` 未在测试中写入；仅记录读取校验 SHA-256。
- 证据：[`t3-full-regression.txt`](evidence/m29-register-control/t3-full-regression.txt)。

## 范围与环境声明

- 越界声明：无。未改 `orchestration/registry.py`，未改真实全局主表内容/表头/状态机，未改 `queue-status-gen.py`，未接入 DeepSeek，未改历史 `task-queue.json`，未重命名既有工单 ID。
- 环境声明：Windows 本机自动化单测；使用 `tools/venv-openjarvis/Scripts/python.exe` (Python 3.13)。该 venv 初始缺少 pytest，已在同一指定 venv 安装 pytest 9.2.0；未使用系统 Python312。无真机/UI/外部服务验证需求。
