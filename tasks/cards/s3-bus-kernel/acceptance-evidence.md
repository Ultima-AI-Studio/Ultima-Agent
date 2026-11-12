# s3-bus-kernel 验收证据

- 日期：2026-10-27（Asia/Shanghai）
- 结论：READY_FOR_REVIEW
- 实现边界：能力插件总线内核位于 `execution/server/ultima_bus/`；三份试点位于 `execution/packages/`；仓库根 `ultima_bus/` 仅提供 `python -m ultima_bus` 入口转发。
- 冻结组件：未修改 L4/L8 对外实现；`ultima.intent.rule` 只适配并复用 `src.brain.intent.parse_task_status_intent`。

## 实际命令与结果

1. `python -m unittest discover -s execution/server/tests -v`
   - `Ran 9 tests in 16.908s`
   - `OK`
   - `INTENT_ADAPTER_CHECKS passed=49 failed=0`
2. `python -m unittest src.brain.tests.test_intent -v`
   - `Ran 4 tests in 0.001s`
   - `OK`
   - `INTENT_METRIC matched=16 total=16 rate=100.00%`
3. `python -m compileall -q execution/server/ultima_bus execution/packages ultima_bus`
   - exit code `0`
4. `python -m ultima_bus bus load ultima.intent.rule`
   - `routing@0.1.0`
5. `python -m ultima_bus bus load ultima.domain.skill`
   - `routing@0.1.0`
6. `python -m ultima_bus bus load ultima.memory.lite`
   - `routing@0.1.0`
7. `python -m ultima_bus bus status`
   - `healthy=true`，默认同步超时 `10.0s`，冒烟上限 `30.0s`，三插件均 routing。
8. 独立读取 `data/plugin-bus-state.json`、`logs/plugin-bus.jsonl`、`sync/plugin-ops.jsonl`
   - `STATE_MODULES=3 ROUTING_MODULES=3`
   - intent/domain/memory 生命周期均为 `loading>ready>routing`
   - `OPS_COMPLETE=3/3`，每条均含 source/ts/module_id/from_version/to_version/result/reason。
9. `git diff --check -- docs/specs/protocol-contract.md docs/specs/registry.md`
   - exit code `0`

## ACCEPT-1~8

| ID | 结果 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | 测试逐项注入缺字段、非法 SemVer、路径级权限、跨域 exposes；均拒绝，返回并追加记录 `error_reason`。 |
| ACCEPT-2 | PASS | 严格验证七段正常迁移；跳迁抛 `E-409`；每段均收到 KP-006 并写 `lifecycle.transition` JSONL。 |
| ACCEPT-3 | PASS | KP-001 正常调用；超时返回 `E-504`+degraded；KP-002 接单、KP-005 回传；相同 reqId 返回同一 Future；KP-003 发布转 KP-004 派发。 |
| ACCEPT-4 | PASS | `direct_call` 及插件源码直接 import/dynamic loading 检查均 fail-closed，并写 `audit.plugin.direct-*`/`audit.plugin.dynamic-code.denied`。 |
| ACCEPT-5 | PASS | 失败冒烟保持旧 routing 并写 rollback；成功蓝绿原子转移后排空旧版；成功回滚到上一稳定版；保留最多 3 版且不清理当前 routing。 |
| ACCEPT-6 | PASS | list/load/unload/switch/rollback/status 六命令均真实子进程执行；根目录和 `execution/server` 两入口均可用；非法回滚结构化返回 E-404。 |
| ACCEPT-7 | PASS | intent/domain/memory 完成注册→加载→冒烟→routing→调用；生产态状态及三条 `plugin-ops.jsonl` 已独立回读。 |
| ACCEPT-8 | PASS | `receipt.json` 含 reviewReason/stdoutText/evidence/landed_files/acceptance，并在最终步骤进行 JSON 与路径回读。 |

## 关键实现约束

- 仅静态登记的模块可注册；仅登记清单入口可 import。
- 文件状态、运行日志与操作日志写入前均校验仍位于 `H:/UltimaAI/UltimaAgent`。
- 权限仅接受 `cap:`、`dev:`、`cred:` scope；路径级权限被拒绝。
- protocol-contract 已按 ADR-011 升至信封 v2 并登记 KP-001~006。
