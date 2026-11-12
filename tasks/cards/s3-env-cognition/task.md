# 任务卡：s3-env-cognition
- **task_id**：s3-env-cognition
- **标题**：环境认知（硬件/磁盘/应用/网络全量扫描 + 档案持久化）
- **优先级**：70（P1）
- **reasoningEffort**：low
- **category**：env　**skill**：engineering
- **依赖**：s3-bus-kernel
- **登记核验**：已查注册表，ultima_env_snapshot 工具已存在，本单为全量升级；依据 capability-list 已识别缺口第 5 条、docs/plans/jarvis-reverse-architecture-20261026.md §4.2（域⑤ 环境认知）

## goal
环境认知 M16：
1. 硬件/磁盘/应用/网络/进程全量扫描（Glances/LibreHardwareMonitor 借鉴，不绑定 Windows 独有）；
2. 扫描结果基线比对与档案持久化（设备档案入共享轴）；
3. 体检场景汇报链路（结论先行/异常优先）；
4. 与 agent_server 工具表整合（env_snapshot 升级或替换）。

**禁止**：
- 禁止扫描范围越界（仅本机认知，不采集用户隐私外数据）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：五类扫描逐项可用且结果结构化
- [ ] ACCEPT-2：基线比对可产出差异；档案持久化可检索
- [ ] ACCEPT-3：体检汇报链路（结论先行/异常优先）验证通过
- [ ] ACCEPT-4：与工具表整合后原环境快照行为不倒退
- [ ] ACCEPT-5：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：环境认知（P1） |
