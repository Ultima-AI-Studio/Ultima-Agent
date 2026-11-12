# 任务卡：s3-bus-kernel
- **task_id**：s3-bus-kernel
- **标题**：总线内核与统一总线（能力注册表热插拔 + KP 三流路由）
- **优先级**：90（P0）
- **reasoningEffort**：medium
- **category**：core　**skill**：engineering
- **依赖**：无（中枢第一批）
- **登记核验**：已查注册表，无重复组件；依据 docs/plans/jarvis-reverse-architecture-20261026.md §3.3.2/§3.3.3、docs/specs/plugin-bus-spec.md

## goal
实现中枢地基：总线内核 M02 + 统一总线 M03（对齐 ADR-011 冻结规范，不另造体系）：
1. 能力注册表：module.json 十项清单协议（module_id/name/version/capability_domain/entry/exposes/deps/config_schema/permissions/hooks），字段缺失拒绝注册；
2. 生命周期状态机：registered→loading→ready→routing→disabling→disabled→unloading→unloaded，状态不可跳迁，每次迁移发事件+写追加日志；
3. 统一总线三流：KP-001 同步调用（10s 超时可配）、KP-002 异步+KP-005 回传（reqId 防重）、KP-003/004 事件发布订阅、KP-006 生命周期广播；插件间禁止直连；
4. 蓝绿切换与回滚：新版 ready 冒烟（30s 上限）→路由转移→旧版排空卸载；失败自动回滚；保留最近 3 版本；
5. CLI 入口 `python -m ultima_bus`：list/load/unload/switch/rollback/status；
6. 试点三插件最小件（intent/domain/memory）走通注册→加载→冒烟→路由→调用全链路；
7. 写域保护：产物仅落 fileDomain；操作留痕 sync/plugin-ops.jsonl。

**禁止**：
- 禁止绕过清单校验加载；禁止路径级文件白名单；
- 禁止插件直连插件；禁止动态加载未登记代码；
- 禁止改动既有 L4/L8 已冻结组件对外行为（迁移须回归）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：清单十项字段缺失/非法 → 拒绝注册并记 error_reason
- [ ] ACCEPT-2：生命周期状态机逐态可验证，无跳迁；每迁移有事件+追加日志
- [ ] ACCEPT-3：KP-001 同步调用正常；KP-002/005 异步回传带 reqId 防重；超时返回 E-5xx 降级不拖垮总线
- [ ] ACCEPT-4：插件直连被拦截并记审计项
- [ ] ACCEPT-5：蓝绿切换冒烟失败自动回滚，旧版可继续 routing；3 版本保留可回滚
- [ ] ACCEPT-6：CLI 六命令可用且行为正确
- [ ] ACCEPT-7：试点三插件注册→路由→调用端到端通过；plugin-ops.jsonl 留痕完整
- [ ] ACCEPT-8：回执完整——receipt 含 reviewReason/stdoutText/evidence/acceptance

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / scripts / sync / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：总线内核与统一总线（P0 中枢第一批） |
