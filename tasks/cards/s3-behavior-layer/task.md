# 任务卡：s3-behavior-layer
- **task_id**：s3-behavior-layer
- **标题**：悬浮球与组合窗口行为层（心跳/思考态/记忆可视化）
- **优先级**：70（P1）
- **reasoningEffort**：medium
- **category**：ui　**skill**：engineering
- **依赖**：s3-bus-kernel
- **登记核验**：已查注册表，l4-a2-orb-live 已实现（悬浮球双层渲染 + 组合窗口 A2UI 真机通过），本单为行为层补齐；依据 ADR-007/010、docs/plans/jarvis-reverse-architecture-20261026.md §4.2（域② 多模态界面）

## goal
行为层 M07/M08（把"有形态无行为"补齐为行为闭环）：
1. 心跳/思考态：悬浮球 idle 呼吸、思考中状态、聆听状态可视化映射（对应任务/语音/编排状态事件）；
2. 记忆可视化：记忆节点/关联点亮（对齐白龙马焦点栈记忆可视化理念，能力边界适度）；
3. 组合窗口场景编排：多场景（对话/任务/环境/长内容）组件树动态组装完善；
4. 主题令牌全量对齐（theme-standard）；状态事件全量映射；
5. AR/VR 接口预留（远期，仅接口登记）。

**禁止**：
- 禁止推翻已冻结悬浮球/组合窗口对外行为（增量兼容）；
- 禁止向 fileDomain 之外写文件。

## acceptance[]
- [ ] ACCEPT-1：心跳/思考/聆听三态可视化真机验证通过
- [ ] ACCEPT-2：记忆可视化（节点+关联点亮）验证通过
- [ ] ACCEPT-3：组合窗口多场景编排完善，既有场景回归不倒退
- [ ] ACCEPT-4：主题令牌对齐；状态事件全量映射
- [ ] ACCEPT-5：AR/VR 接口预留登记
- [ ] ACCEPT-6：回执完整

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src / data）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-27 | 初版：行为层（P1） |
