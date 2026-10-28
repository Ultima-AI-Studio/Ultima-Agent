# 任务卡：s13-host-abstraction
- **task_id**：s13-host-abstraction
- **标题**：宿主抽象层（M25 前置 · ADR-001 四 IO+渲染+协议）
- **优先级**：70（P1）
- **reasoningEffort**：medium
- **category**：brain　**skill**：engineering
- **依赖**：ADR-001（已冻结三层架构）、ADR-004（已冻结 Python 3.13 跨平台基线）、s3-env-cognition（已验收）
- **登记核验**：已查注册表，无重复；依据 docs/plans/roadmap.md Next「宿主抽象层（macOS 跨平台验证地基）」+ tasks/queue/stage2-batch-plan.md（S13 工单：iOS 变体冻结仅做抽象层）

## goal
宿主抽象层（跨平台验证地基）：
1. **宿主接口定义**：HostIO / HostRenderer / HostEvents 三组 Protocol（四 IO + 渲染 + 协议，对齐 ADR-001），零 Windows API 依赖（ADR-004 跨平台基线）；
2. **Windows 宿主适配**：文件契约实现（IO outbox/inbox、渲染 orb_command/window_tree、事件 events），与既有 HostOrbPusher 契约同构（seq 递增、幂等覆盖、空指令拒绝），现有壳零行为倒退；
3. **CompositeHost 聚合**：能力层单一入口 + 就绪自检（fail-closed 前预检）。

**禁止**：
- 禁止在抽象层引入业务智能（宿主薄壳定位，ADR-001）；
- 禁止调用 Windows API / ctypes（ADR-004 跨平台）；
- 禁止实现多端本体（M25 已冻结，仅做抽象）；
- 禁止改动既有 HostOrbPusher 行为契约。

## acceptance[]
- [x] ACCEPT-1：三组宿主接口（IO/渲染/事件）存在且 runtime_checkable
- [x] ACCEPT-2：Windows 文件契约适配与既有契约同构（seq 递增/幂等/空指令拒绝）
- [x] ACCEPT-3：CompositeHost 聚合透传 + 就绪自检正确
- [x] ACCEPT-4：适配器零 Windows API 依赖（纯标准库/文件系统）
- [x] ACCEPT-5：venv-openjarvis 全量测试全绿（既有功能零回归）
- [x] ACCEPT-6：回执完整（含变更登记）

## fileDomain[]
- `H:/UltimaAI/UltimaAgent`（src/host、src/host/tests、tasks/cards/s13-host-abstraction）

## 变更登记
| 版本 | 日期 | 变更 |
|---|---|---|
| v1.0 | 2026-10-24 | 初版：宿主抽象层（四 IO+渲染+协议 抽象 + Windows 文件契约适配） |
