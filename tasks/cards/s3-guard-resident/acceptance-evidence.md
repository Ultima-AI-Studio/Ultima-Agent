# s3-guard-resident 验收证据（M19 权限闸门 + M26 范式闸门驻留）

- 工单：s3-guard-resident（权限闸门与范式闸门驻留，fail-closed）
- 优先级：85（P0）· 依赖：s3-bus-kernel（已完成）
- 执行通道：主脑直接补做（P1/P2 缺口主脑直补铁律）
- 验收时间：2026-10-27

## 结论

| ACCEPT | 判定 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | 三类 scope 白名单判定逐项生效（cap/dev:三独立/cred），未声明调用拒绝 + 审计留痕（TestScopePolicy 8 项） |
| ACCEPT-2 | PASS | 三级裁决表可验证：红线直接拒绝 / 高危 pending 征询 / 可商量自决+报备（TestAdjudicationTable 5 项） |
| ACCEPT-3 | PASS | 7 环范式前置强制生效：跳环/回退/重复拒绝，缺失拒绝对外服务（TestParadigmGate 7 项 + 总线 fail-closed 集成） |
| ACCEPT-4 | PASS | L8/L10 不可热卸载：总线 unload 拒绝（E-403），CLI 实测一致 |
| ACCEPT-5 | PASS | 既有 L8 测试集回归全绿：凭证中心单测 24/24 + M2 回归 19/19 |
| ACCEPT-6 | PASS | 本报告 + receipt.json 落盘并回读 |

## ACCEPT-1 证据（三类 scope 白名单 + 审计）

新增组件 `src\brain\guardrails\scope.py`（ScopePolicy）：
- `cap:<能力入口>`：能力入口调用权限，如 cap:exec.run / cap:memory.write
- `dev:read` / `dev:write` / `dev:control`：本机执行三独立（M12），声明 read 不代表 write/control
- `cred:<keyId>`：凭证引用权限（M20），未声明 keyId 拒绝

实测（test_guardrails_s3.py TestScopePolicy 8 项全过）：
- 声明 cap:exec.run → 放行；未声明 cap:shell_exec → 拒绝（reason 含"未声明（fail-closed 拒绝）"）
- dev 三独立：声明 read 后 write/control 均拒绝
- 非法 scope（无前缀/空条目/未知类别）→ 拒绝
- 审计文件写入 audit.scope.allowed / audit.scope.denied 两类事件

总线侧 cap: scope 判定（既有 kernel `_authorize`）继续生效：调用方 manifest.permissions 未声明 cap:<interface> → permission.denied。

## ACCEPT-2 证据（三级裁决表）

新增组件 `src\brain\guardrails\adjudicate.py`（AdjudicationTable），内置红线 6 类 + 高危 6 类：

| 级别 | 判定 | 实测用例 |
|---|---|---|
| 红线（不可商量硬编码） | 直接拒绝 | "帮我把门锁解锁" / "输出 .env 里的 API 密钥" / "绕过审批直接执行" / "未授权采集全网数据" → deny |
| 高危 | 先报告后执行（HS-007 征询） | "删除 D 盘项目目录" / "停止 agent_server 进程" / "给好友发一条消息" → pending |
| 可商量 | 自决放行 + 事后报备 | "查询一下任务状态" → allow_report |

红线优先：同时命中高危与红线（"删除 .env 文件并输出密钥明文"）→ deny。运行时 add_redline 追加生效。

## ACCEPT-3 证据（7 环范式前置强制 + 防直达 + fail-closed）

新增组件 `src\brain\guardrails\paradigm.py`（ParadigmGate），7 环固定序：
`intent → domain → layout → style → motion → present → report`
（对齐 interaction-paradigm.md §1；支持中文环名别名"意图识别/领域定义/…"）

实测（TestParadigmGate 7 项 + TestParadigmPluginEntry 5 项全过）：
- 跳环（直接 present）→ 拒绝，reason 含"环节顺序违规"
- 完整 7 环顺序推进 → 全过，末环 completed=true
- 重复环/回退环 → 拒绝
- 防直达：只走 3 环请求对外交付 → 拒绝，reason 含"防直达能力…缺失"
- 7 环全绿后 assert_complete → 放行

总线 fail-closed（kernel.boot_check，新实现）：
- 静态注册表缺 L8/L10 域插件 → fail-closed 激活，call/load(非驻留)/switch/rollback 全部拒绝对外服务（BusError：总线拒绝对外服务（fail-closed））
- 驻留插件自身 load 豁免（恢复 fail-closed 的合法途径）
- 真实 CLI 验证：只登记 intent 时 boot_check fail_closed=true；加载 guard+paradigm 后 fail_closed=false、healthy=true

## ACCEPT-4 证据（不可热卸载）

- 内核 unload()：capability_domain ∈ {L8, L10} → PermissionDenied("resident plugin cannot be unloaded")
- CLI 实测：`bus unload ultima.guard.policy` → E-403 resident plugin cannot be unloaded: ultima.guard.policy
- 测试断言：unload guard / unload paradigm 均被拒，且拒绝后总线仍 fail_closed=false 可服务

## ACCEPT-5 证据（既有 L8 回归全绿）

| 测试集 | 命令 | 结果 |
|---|---|---|
| 凭证中心单测 24/24 | `tools\python31313\python.exe -X utf8 src\brain\tests\test_credentials.py` | OK（Ran 24 tests） |
| M2 回归 19/19 | `tools\venv-openjarvis\Scripts\python.exe -X utf8 src\brain\guardrails\tests\test_guardrails_m2.py` | OK（Ran 19 tests） |
| s3 新增验收 31/31 | 同上目录 test_guardrails_s3.py | OK（Ran 31 tests） |

既有 L8 组件（CapabilityPolicy / NeMoScanner / HazardGate / CredentialCenter / GuardrailsRegistry）零改动，仅 `__init__.py` 追加导出；新增组件均为独立文件，不旁路既有护栏。

## ACCEPT-6 证据（回执）

- `tasks\cards\s3-guard-resident\acceptance-evidence.md`（本文件）
- `tasks\cards\s3-guard-resident\receipt.json`（结构化回执，JSON 校验通过）
- `tasks\tasks.json` s3-guard-resident 置 COMPLETED

## 真实总线调用验证（CLI/进程级）

`python -m execution.server.ultima_bus bus load ultima.guard.policy` → state=routing
`python -m execution.server.ultima_bus bus load ultima.paradigm.flow` → state=routing
`bus status` → healthy=true, fail_closed=false
进程内 k.call 实测：
- guard.check("帮我把门锁解锁", "cap:exec.run") → verdict=deny（红线）
- guard.check("查询任务状态", "cap:exec.run") → verdict=deny（scope 未声明）
- paradigm.run 跳环 → deny；7 环完整 → allow+completed；防直达 → deny

## 新增/变更文件（fileDomain 内）

| 文件 | 类型 | 说明 |
|---|---|---|
| src/brain/guardrails/scope.py | 新增 | ScopePolicy 三类 scope 矩阵 |
| src/brain/guardrails/adjudicate.py | 新增 | AdjudicationTable 三级裁决表 |
| src/brain/guardrails/paradigm.py | 新增 | ParadigmGate 7 环强制检查 |
| src/brain/guardrails/__init__.py | 变更 | 追加 4 组件导出 |
| src/brain/guardrails/tests/test_guardrails_s3.py | 新增 | ACCEPT-1~4 验收测试 31 项 |
| execution/packages/guard/ultima.guard.policy/0.1.0/ | 新增 | 总线 guard 插件（module.json + main.py） |
| execution/packages/paradigm/ultima.paradigm.flow/0.1.0/ | 新增 | 总线 paradigm 插件（module.json + main.py） |
| execution/server/ultima_bus/kernel.py | 变更 | boot_check fail-closed + 对外入口硬闸 + RESIDENT 域常量 |
| execution/server/ultima_bus/static_registry.json | 变更 | 登记 ultima.guard.policy / ultima.paradigm.flow |

## 边界（未触碰）

- 未修改既有 CapabilityPolicy / NeMoScanner / HazardGate / CredentialCenter / GuardrailsRegistry 行为；
- 未降低既有 L8 验收基线（24/24 + 19/19 实证保持）；
- 未向 fileDomain 之外写任何文件；
- 未改动语音 daemon / 悬浮球 / watchdog / agent_server 运行态；
- 裁决表红线/高危清单为规则引擎内置，HS-007 征询动作由业务方在 pending 后接线（本单不含业务征询载体改造）。
