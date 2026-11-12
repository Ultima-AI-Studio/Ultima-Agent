# s3-audit-trail 验收证据（M21 审计留痕 + 独立复核框架）

- 工单：s3-audit-trail（审计留痕与独立复核框架）
- 执行通道：主脑直接补做（Codex 派发通道网络层死路，与 s3-watchdog/s3-credential-bus 同因）
- 规范基线：`docs\specs\plugin-bus-spec.md` §10.2（只追加不修改、记录带 时间戳+会话ID+来源+事件类型+载荷引用、敏感字段脱敏、按会话/时间/来源/事件类型检索）、`docs\specs\sequencing.md` §3（时序含「审计（独立视角，dev 不自证清白）→ 收尾（回执+归档）」）
- 验收时间：2026-10-27

## 结论

| ACCEPT | 判定 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | AppendOnlyAuditLog 追加写 + 按会话/时间/来源/事件类型检索 + SHA-256 链强校验（改写/删除/插入即 fail）；legacy 兼容存量无链行，篡改检测依然有效 |
| ACCEPT-2 | PASS | ReceiptValidator 机检顶层字段 + 四字段（reviewReason/stdoutText/evidence/acceptance）+ evidence 路径存在性 + kind 白名单 + acceptance id/result/evidence；对 s3-credential-bus 真实回执复核 0 问题 |
| ACCEPT-3 | PASS | IndependentReviewer 仅 eng.audit/eng.security 可实例化（dev 抛 ReviewError 拒自证清白），分级 blocker/major/minor，blocker 清零才过交付门；真实复核 s3-credential-bus 回执 gate PASS |
| ACCEPT-4 | PASS | 违规三项全部记审计并可检索：未声明调用→audit.permission.denied（真实总线 11 条）、热插拔驻留拒绝→audit.resident.unload.denied（真实触发）、违规直连→audit.plugin.direct-import.denied（真实触发）；顺带修复总线直连检测缺陷（原逻辑只比顶层包名导致永不触发） |
| ACCEPT-5 | PASS | 本报告 + receipt.json 落盘并回读（ReceiptValidator 复核通过）；tasks.json 置 COMPLETED |

## ACCEPT-1 证据（追加式日志可检索 + 改写被拒）

`src\brain\guardrails\audit_log.py`（AppendOnlyAuditLog）：

- append 只追加（open "a"），每条记录带 `ts`（毫秒 ISO）/`session_id`/`source`/`event_type`/`payload` + `_prev`/`_hash`（SHA-256 链）；
- query 按 session_id/source/event_type/since/until 五维过滤检索；
- verify() 逐行重建链：任意一行被改（hash-mismatch）/删除/插入（prev-link-broken）即 fail；存量无 `_hash` 行按 legacy 跳过并计数，但一旦其后有带链行，篡改仍被后续行 `_prev`/hash 失配检出（无盲区）；
- 测试 `test_rewrite_detected` / `test_delete_detected` 实证改写与删除均被检出（fail + 定位到行号）。

## ACCEPT-2 证据（回执四字段完整可核对）

`src\brain\guardrails\receipt.py`（ReceiptValidator，`base` 参数以项目根解析相对证据路径）：

- 顶层 work_order/status 必填；四字段 reviewReason/stdoutText/evidence/acceptance 缺一即 issue；
- evidence 逐项核对 path 存在性、kind 白名单（report/manifest/code/config/test/log/data）、summary 非空；
- acceptance 逐项核对 id/result(PASS|FAIL)/evidence；
- 实证：对 `tasks\cards\s3-credential-bus\receipt.json` 真实复核 → ok=True、0 issues；缺失字段/缺失证据路径/缺失文件三组反例全部按预期 fail。

## ACCEPT-3 证据（独立复核角色分离 + 分级结论）

`src\brain\guardrails\reviewer.py`（IndependentReviewer）：

- 构造仅允许 `eng.audit` / `eng.security`，`dev` 与任意其他角色实例化即抛 ReviewError（开发执行器不得自证清白）；
- add_finding 分级 blocker/major/minor，非法级（如 critical）抛错；
- gate()：blocker>0 → FAIL（不进交付门），清零 → PASS（可携带 major/minor 观察项）；
- 内置检查助手：check_files_exist / check_no_plaintext（正则命中=blocker）/ check_json_valid；
- 实证（真实产物复核）：eng.security 复核 s3-credential-bus 回执 → 明文扫描 0 命中、JSON 合法、gate PASS（blocker 0）。

## ACCEPT-4 证据（违规项全部记审计）

真实总线（BusKernel）三类违规事件全部触发并检索到：

```
audit.permission.denied            → 11 条（未声明调用：ultima.memory.lite 调 credential.inject 被闸门拒绝）
audit.resident.unload.denied       → 真实触发（热插拔卸载 ultima.credential.center 被驻留拒绝）
audit.plugin.direct-import.denied  → 真实触发（构造 ultima.guard.violation-demo 源码 import ultima.guard.policy，load 审计拒绝）
```

顺带修复：`execution\server\ultima_bus\kernel.py::_audit_imports` 原逻辑 `imported & registered_roots` 只比较顶层包名（全部为 `ultima`），跨模块直连实际永不触发；改为按完整 module_id 前缀判定（`target == rid or target.startswith(rid+".")`，插件自引用放行），直连违规从此可被审计记录。该修复不动契约（不新增接口/签名），回归 31/19/17/24/18 全绿。

## ACCEPT-5 证据（回执完整）

本报告 + `receipt.json` 落盘并经 ReceiptValidator 复核通过；`tasks\tasks.json` 中 s3-audit-trail 置 COMPLETED（含 terminal_reason）。

## 审计留痕演示（可检索示例）

`data\audit\audit-trail-s3.jsonl`（AppendOnlyAuditLog 实际写入）：

```
audit.delivery.receipt     source=ultima.audit.trail   ACCEPT-2 回执复核
audit.review.gate          source=eng.security         复核 s3-credential-bus 回执 gate PASS
audit.violation.direct     source=ultima.guard.violation-demo 直连拒绝事件
```

query（session/时间/来源/事件类型）与 verify（链完整）均验证通过。

## 产出文件

- `src\brain\guardrails\audit_log.py`（追加式 hash 链审计日志）
- `src\brain\guardrails\receipt.py`（回执四字段校验器）
- `src\brain\guardrails\reviewer.py`（独立复核框架）
- `src\brain\guardrails\__init__.py`（扩展导出 15 个新符号）
- `src\brain\guardrails\tests\test_audit_s3.py`（18 项验收测试）
- `execution\server\ultima_bus\kernel.py`（_audit_imports 直连检测修复，仅此一处改动）
- `data\audit\audit-trail-s3.jsonl`（审计留痕演示日志）

## 回归基线（修改 kernel 后全量保持）

```
tools\venv-openjarvis\Scripts\python.exe -X utf8 src\brain\guardrails\tests\test_guardrails_s3.py → Ran 31 tests OK
tools\venv-openjarvis\Scripts\python.exe -X utf8 src\brain\guardrails\tests\test_guardrails_m2.py  → Ran 19 tests OK
tools\venv-openjarvis\Scripts\python.exe -X utf8 src\brain\guardrails\tests\test_credential_s3.py → Ran 17 tests OK
tools\python31313\python.exe -X utf8 src\brain\tests\test_credentials.py                          → Ran 24 tests OK
tools\venv-openjarvis\Scripts\python.exe -X utf8 src\brain\guardrails\tests\test_audit_s3.py     → Ran 18 tests OK
```

## 边界（未触碰）

- 未重写既有 kernel._log/_audit 总线日志（沿用四字段 JSONL，新增独立 hash 链审计层供强校验）；
- 未改动 manifest.py 契约、static_registry、guard/paradigm/credential 插件代码；
- 未向 fileDomain 之外写任何文件；
- 测试全部使用独立临时目录（data\test-tmp\audit-s3），零污染真实库/日志。
