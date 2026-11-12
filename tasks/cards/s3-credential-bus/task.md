# 任务卡：s3-credential-bus
- **task_id**：s3-credential-bus
- **标题**：凭证中心接入总线
- **优先级**：80（P0）
- **reasoningEffort**：medium
- **category**：security　**skill**：engineering
- **依赖**：s3-bus-kernel
- **登记核验**：已查注册表，l8-credential-center 已实现（DPAPI+四层凭证层+高危征询，单测 24/24），本单为总线注入对接；依据 docs/specs/security-spec.md §1

## goal
凭证中心 M20 接入总线（只做对接，不重写已冻结实现）：
1. 凭证经服务器能力层调用，keyId 引用进上下文，明文不出本地；对外 key 永不进前端/宿主壳；
2. 总线注入对接：能力插件经闸门后由凭证中心注入明文，用完不落盘；
3. 四层凭证轮换机制保留；日志/回执/源码不落明文；
4. 扩展：支持外部大模型 key、渠道 token、设备凭证三类（cred:<keyId> scope）。

**禁止**：
- 禁止凭证明文出现在日志/回执/前端/源码；
- 禁止降低既有验收基线（单测 24/24 + M2 回归 19/19）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：插件经闸门后凭证注入正常，keyId 引用、明文不出本地
- [ ] ACCEPT-2：用完不落盘；日志/回执脱敏（无明文）
- [ ] ACCEPT-3：三类凭证（大模型 key/渠道 token/设备凭证）可注册可引用
- [ ] ACCEPT-4：既有凭证中心测试集回归全绿
- [ ] ACCEPT-5：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：凭证中心接总线（P0） |
