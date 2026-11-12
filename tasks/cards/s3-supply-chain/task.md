# 任务卡：s3-supply-chain
- **task_id**：s3-supply-chain
- **标题**：供应链闸门
- **优先级**：75（P0）
- **reasoningEffort**：low
- **category**：security　**skill**：engineering
- **依赖**：s3-bus-kernel
- **登记核验**：已查注册表，无重复组件；依据 docs/specs/plugin-bus-spec.md §13、docs/specs/security-spec.md §3

## goal
供应链闸门 M23：
1. 依赖白名单登记（module_id/版本/来源）；
2. License 审查（不采 GPL 底座）+ 依赖 CVE 扫描；
3. 第三方插件准入：Owner 批准 + 独立安全审查；
4. 版本锁定 vendor 进仓库（升级走 M3 评审与蓝绿回滚）；
5. 未审查模块拒绝加载。

**禁止**：
- 禁止未审查模块加载；禁止 GPL 底座；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：白名单登记机制生效，未登记依赖被拒
- [ ] ACCEPT-2：License 审查规则生效（GPL 拒绝样例验证）
- [ ] ACCEPT-3：CVE 扫描接入，发现高危阻断加载
- [ ] ACCEPT-4：第三方准入流程可验证（批准+审查留痕）
- [ ] ACCEPT-5：版本锁定 vendor 落地
- [ ] ACCEPT-6：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / scripts / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：供应链闸门（P0） |
