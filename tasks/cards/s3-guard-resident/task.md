# 任务卡：s3-guard-resident
- **task_id**：s3-guard-resident
- **标题**：权限闸门与范式闸门驻留（fail-closed）
- **优先级**：85（P0）
- **reasoningEffort**：medium
- **category**：security　**skill**：engineering
- **依赖**：s3-bus-kernel
- **登记核验**：已查注册表，L8 越界拦截已实现（CapabilityPolicy+NeMoScanner），本单为迁入总线驻留；依据 docs/plans/jarvis-reverse-architecture-20261026.md §3.6.2、docs/specs/plugin-bus-spec.md §5.4、docs/specs/security-spec.md §2

## goal
权限闸门 M19 + 范式闸门 M26 迁入总线并驻留：
1. M19 权限闸门：scope 三类权限矩阵（cap:<能力入口>/dev:read/write/control 三独立/cred:<keyId>），清单声明+闸门逐次判定，未声明调用拒绝并记审计；
2. 裁决表内置：不可商量硬编码红线（越权文件读写/远程开锁/持械/绕过审批/泄露凭证明文/未授权全网采集）直接拒绝；可商量事项自决+事后报备；高危事项先报告后执行（HS-007 征询）；
3. M26 范式闸门：7 环流程强制检查、防直达能力、流程合规校验；
4. 驻留保护：L8/L10 不可热卸载/禁用；启动缺失二者 fail-closed 拒绝对外服务；
5. 与既有 L8 实现（CapabilityPolicy/HazardGate）合并对齐，不另造体系。

**禁止**：
- 禁止闸门可被旁路；禁止绕过范式直达能力；
- 禁止降低既有 L8 验收基线（单测 24/24 与 M2 回归 19/19 须保持）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：三类 scope 白名单判定逐项生效，未声明调用拒绝+审计留痕
- [ ] ACCEPT-2：裁决表三类规则可验证（构造红线/可商量/高危用例）
- [ ] ACCEPT-3：7 环范式前置检查强制生效，缺失时拒绝对外服务（fail-closed 验证）
- [ ] ACCEPT-4：L8/L10 不可热卸载（执行 unload/disable 被拒）
- [ ] ACCEPT-5：既有 L8 测试集回归全绿（24/24 + M2 19/19）
- [ ] ACCEPT-6：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / scripts / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：闸门驻留（P0） |
