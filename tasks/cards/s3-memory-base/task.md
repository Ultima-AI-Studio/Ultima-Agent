# 任务卡：s3-memory-base
- **task_id**：s3-memory-base
- **标题**：记忆底座（分层记忆 + 本地向量 + 写入闸门）
- **优先级**：75（P1）
- **reasoningEffort**：medium
- **category**：memory　**skill**：engineering
- **依赖**：s3-bus-kernel、s3-guard-resident
- **登记核验**：已查注册表，ultima_memory 工具已存在（偏好最小记忆），本单升级为完整底座；依据 ADR-008、docs/plans/jarvis-reverse-architecture-20261026.md §4.2（域⑦ 长期记忆与学习）

## goal
记忆底座 M17（对齐 ADR-008 冻结基线，不推翻）：
1. 四层记忆结构落地：工作/声明式/程序式 + 设备档案与环境档案；
2. 本地向量检索（onnx 嵌入），Mem0 作为语义增强备选（PoC 失败再升级评估）；
3. 反思条目与遗忘边界；
4. 写入闸门：不可信内容不直接进长期记忆，事实与建议分离标注，条目可回溯可删除；
5. 记忆经总线供读（状态与记忆共享轴对接）。

**禁止**：
- 禁止推翻 ADR-008 冻结基线；
- 禁止不可信内容无闸门写入长期记忆；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：四层记忆结构可写入可检索可回溯
- [ ] ACCEPT-2：本地向量检索可用；Mem0 备选 PoC 结论落档
- [ ] ACCEPT-3：反思条目与遗忘边界规则生效
- [ ] ACCEPT-4：写入闸门拦截不可信内容；事实/建议分离标注
- [ ] ACCEPT-5：记忆经总线供读，跨模块一致
- [ ] ACCEPT-6：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：记忆底座（P1） |
