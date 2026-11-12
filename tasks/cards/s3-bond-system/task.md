# 任务卡：s3-bond-system
- **task_id**：s3-bond-system
- **标题**：羁绊系统（关系档位 + 关系事实 + 身份人格）
- **优先级**：55（P2）
- **reasoningEffort**：low
- **category**：persona　**skill**：engineering
- **依赖**：s3-memory-base
- **登记核验**：已查注册表，无重复组件；依据 docs/plans/form-expansion-plan-20261024.md §3（阶段二羁绊系统）、docs/plans/jarvis-reverse-architecture-20261026.md §4.2（域⑥ 情感与身份）

## goal
羁绊系统 M18（默认贾维斯式专业距离，亲密档由用户主动开放）：
1. SOUL/MEMORY/USER 档案组织；
2. 关系档位：默认档=贾维斯式专业距离（克制、朋友般可靠）；亲密档=用户主动开放后启用（称呼/口吻/互动温度升级）；
3. 关系事实可回溯；称呼/口吻持久化；
4. 不模拟疲劳/无聊边界固化（诚实边界）；
5. 跨形态共享同一状态轴（预留）。

**禁止**：
- 禁止默认亲密化（必须用户主动开放）；
- 禁止模拟疲劳/无聊等不诚实表达；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：三档案组织落地，关系事实可回溯
- [ ] ACCEPT-2：默认档为专业距离，亲密档需用户显式开放
- [ ] ACCEPT-3：称呼/口吻持久化生效
- [ ] ACCEPT-4：疲劳/无聊模拟被禁止（边界固化）
- [ ] ACCEPT-5：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：羁绊系统（P2） |
