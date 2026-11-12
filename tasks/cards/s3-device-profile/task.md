# 任务卡：s3-device-profile
- **task_id**：s3-device-profile
- **标题**：设备档案层（HA 实体映射 + 可控性三独立 + 适配器框架）
- **优先级**：50（P2）
- **reasoningEffort**：low
- **category**：iot　**skill**：engineering
- **依赖**：s3-env-cognition
- **登记核验**：已查注册表，无现有通道；依据 capability-list 借鉴点表 HA 实体模型行、docs/plans/form-expansion-plan-20261024.md §2.2⑤

## goal
设备档案层 M15（本期建框架与档案，实操接入后置阶段三）：
1. 设备档案模型（DeviceProfile/Controlability/DeviceCred/Reading 四实体，对齐 data-model）；
2. HA 实体映射与可控性三独立判定（可读/可写/可控制分别判定）；
3. MCP 适配器框架（能力插件不直连 MCP，换 server 只改配置）；
4. 设备发现→档案→凭证→可控性前置检查链；
5. 单协议试点（后续铺开，不可达设备如实报告）。

**禁止**：
- 禁止设备误控（可控性判定前置）；
- 禁止一次性全量接入协议（先试点）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：四实体档案模型落地可读写
- [ ] ACCEPT-2：可控性三独立判定用例验证
- [ ] ACCEPT-3：MCP 适配器框架可挂总线；能力插件不直连 MCP
- [ ] ACCEPT-4：前置检查链（发现→档案→凭证→可控性）生效
- [ ] ACCEPT-5：单协议试点验证（如实报告不可达项）
- [ ] ACCEPT-6：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：设备档案层（P2） |
