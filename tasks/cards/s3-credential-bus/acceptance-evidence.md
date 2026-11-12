# s3-credential-bus 验收证据（M20 凭证中心接入总线）

- 工单：s3-credential-bus（凭证中心接入总线）
- 执行通道：主脑直接补做（Codex 派发通道网络层死路，与 s3-watchdog 同因）
- 实现：总线适配壳包 `execution\packages\credential\ultima.credential.center\0.1.0\` + 总线契约受控扩展（manifest.py）+ 验收测试
- 验收时间：2026-10-27

## 结论

| ACCEPT | 判定 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | 三类凭证经总线注册后，inject 服务器能力层返回明文（仅内存，memory_only=true），上下文只携带 keyId 引用；插件单元测试 + 真实总线调用链双验证 |
| ACCEPT-2 | PASS | DPAPI 密文落盘（store 文件无明文）；审计 JSONL 无明文（13 行事件，demo 值零泄露）；register/status/list 回执均无明文（redact 脱敏形 ***） |
| ACCEPT-3 | PASS | model:/channel:/device: 三类命名空间注册→状态→引用全链路通过（单元 + 真实总线双验证） |
| ACCEPT-4 | PASS | 既有凭证中心测试集 24/24 回归全绿（tools\python31313）；M2 回归 19/19、s3 guard 31/31 保持 |
| ACCEPT-5 | PASS | 本报告 + receipt.json 落盘并回读；tasks.json 置 COMPLETED |

## ACCEPT-1 证据（注入正常 + keyId 引用 + 明文不出本地）

真实总线调用链（BusKernel 内，guard/paradigm/credential 三插件全部 routing）：

```
register model:qwen2.5-14b True
register channel:feishu True
register device:pc-01 True
status: {"ok": true, "key_id": "model:qwen2.5-14b", "active": true, "state": "active", "label": "主凭证"}
list count: 5 no_plaintext: True
inject ok: True memory_only: True
unauthorized denied: True
```

- inject 返回明文仅出现在服务器能力层返回值（同进程内存），`memory_only=true`；
- 上下文/回执/状态只含 `key_id`（如 `model:qwen2.5-14b`），明文不出本地；
- 未声明 `cap:credential.inject` 的调用方（ultima.memory.lite）被总线授权闸门拒绝。

## ACCEPT-2 证据（用完不落盘 + 日志/回执脱敏）

- store 落盘：`test_store_on_disk_no_plaintext` —— 明文写库后读盘全文不包含明文（DPAPI 密文）；
- 审计留痕：`execution\packages\logs\credential-audit.jsonl` 13 行事件（register/inject/rotate），demo 明文零出现；审计路径与既有 guard/paradigm 同构；
- 回执脱敏：`test_register_receipt_redacted` —— 注册回执不含明文且含脱敏形 `***`；status/list 回执同样无明文；
- 测试隔离：验收测试注入独立临时凭证库/审计路径，运行后真实凭证库 `keys()==[]`（零污染）。

## ACCEPT-3 证据（三类凭证注册引用）

```
model:qwen2.5-14b  → sk-ultima-llm-demo-1   （外部大模型 key，model: 前缀）
channel:feishu     → tok-ultima-chan-demo-2 （渠道 token，channel: 前缀）
device:pc-01       → dev-ultima-demo-3      （设备凭证，device: 前缀）
```

注册→status（active）→inject 全链路通过；list 返回全部 keyId 且无明文；rotate 轮换保留 standby（四层凭证层机制未改动）。

## ACCEPT-4 证据（既有基线保持）

```
tools\venv-openjarvis\Scripts\python.exe -X utf8 src\brain\guardrails\tests\test_guardrails_s3.py → Ran 31 tests OK
tools\venv-openjarvis\Scripts\python.exe -X utf8 src\brain\guardrails\tests\test_guardrails_m2.py  → Ran 19 tests OK
tools\python31313\python.exe -X utf8 src\brain\tests\test_credentials.py                          → Ran 24 tests OK
tools\venv-openjarvis\Scripts\python.exe -X utf8 src\brain\guardrails\tests\test_credential_s3.py → Ran 17 tests OK
```

## ACCEPT-5 证据（回执完整）

本报告 + `receipt.json` 落盘并回读；`tasks\tasks.json` 中 s3-credential-bus 置 COMPLETED。

## 总线契约受控扩展（manifest.py）

| 项 | 变更 | 说明 |
|---|---|---|
| MODULE_RE | 域名单新增 `credential` | 允许 `ultima.credential.center` 模块 id |
| PERMISSION_RE | 新增 `credential.(register\|rotate\|status\|list\|inject)` | cap 能力 scope |
| DOMAIN_EXPOSES["L8"] | guard.check 基础上新增 5 个 credential.* | L8 域 API 契约 |
| INTERFACE_SIGNATURES | 新增 5 条 credential.* 签名 | 插件 entry 签名校验 |

既有项（intent/domain/guard/memory/paradigm 等）零改动；s3-guard-resident 测试 31/31 保持证明扩展未破坏驻留 fail-closed。

## 产出文件

- `execution\packages\credential\ultima.credential.center\0.1.0\module.json`（L8 域驻留声明 resident=true，exposes 5 接口，permissions 5 cap）
- `execution\packages\credential\ultima.credential.center\0.1.0\ultima_credential_center_v0_1_0\main.py`（GuardPolicy 同构适配壳：load/smoke/register/rotate/status/list/inject，惰性初始化）
- `execution\packages\credential\ultima.credential.center\0.1.0\ultima_credential_center_v0_1_0\__init__.py`
- `execution\server\ultima_bus\static_registry.json`（登记 ultima.credential.center）
- `execution\server\ultima_bus\manifest.py`（契约受控扩展，见上表）
- `src\brain\guardrails\tests\test_credential_s3.py`（17 项验收测试）
- 审计留痕 `execution\packages\logs\credential-audit.jsonl`

## 边界（未触碰）

- 未重写既有 CredentialCenter（DPAPI+四层凭证层+高危征询）任何逻辑；
- 未改动 guard/paradigm/intent/domain/memory 插件代码；
- 未向 fileDomain 之外写任何文件；
- 测试 demo 凭证已全部清理，真实凭证库零残留；
- 总线驻留判定（RESIDENT_DOMAINS L8/L10）与 fail-closed 逻辑未改，credential 与 guard 同域驻留、不可热卸载（PermissionDenied 已验证）。
