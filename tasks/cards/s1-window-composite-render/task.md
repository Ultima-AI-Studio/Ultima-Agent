# 任务卡：s1-window-composite-render

- **task_id**：s1-window-composite-render
- **stage**：S1（阶段一 v0.4）
- **标题**：积木组合窗口渲染（L4/L6：任意结果→组件树→窗口）
- **创建**：2026-10-16 · 主脑立项
- **M1 声明**：已查能力注册表（registry.md），无重复组件；本任务为组合窗口的核心渲染能力

## goal

实现积木组合窗口渲染：任意任务结果 → 组件树 → 组合成窗口呈现，窗口内容覆盖任务域清单 ≥90%。禁止：不实现 DSL 定义（T1 已完成，只消费）、不实现主题（T3）、不实现具体业务页（业务由 DSL 声明）。

## acceptance[]（封闭验收清单，逐项可核对）

- [ ] ACCEPT: 任意结果→组件树→窗口链路可用（L4/L6）
- [ ] ACCEPT: 窗口覆盖任务域清单 ≥90%（窗口截图对照域清单）
- [ ] ACCEPT: 窗口与语音同时交付（v0.3 聚合汇报 + 窗口双通道）

## dependsOn[]

- s1-window-dsl-schema（T1 DSL）

## fileDomain[]

- `H:\UltimaAI\UltimaAgent\src\window\`（渲染模块）
- `H:\UltimaAI\UltimaAgent\tasks\cards\s1-window-composite-render\`（任务卡自身）

## priority

- 50（默认）

## reasoningEffort

- ultra（组合渲染核心，跨技能：UI+逻辑编排，需评审背书）

## category + skill

- category: window · skill: eng.ui + eng.code 组合（主技能 eng.ui）

## receipt（完成时由 CodeX 回填）

- reviewReason: `READY_FOR_REVIEW`；`audit-1` 的四项发现已在同一 `phase=T2-text-core-only` 范围内修复并完成开发自检，等待新的独立复审；整卡保持 partial
- stdoutText: 六项复审回归先 RED 后 GREEN；窗口全量 61/61（旧 35 + 新 26）；T1 原 91 探针 91/91；冻结 guardrail exit 0
- evidence: `evidence/20261024T085613+0800/`（只含本 T2 第二开发轮新证据；未改旧 T1 或首轮 T2 证据）
- acceptance 逐项核对: 三项整卡 ACCEPT 均未勾选；CR-01 完整域、CR-02 原生窗口、CR-03 截图覆盖率、CR-04 双通道真机均仍待验收

## retryCount

- 2/2（本轮为 `audit-1=REVISE` 后最后一次有界开发修复；现仅提交独立复审，不自动开启更多开发轮次）

## T2-text-core-only 阶段回执（partial · 2026-10-24）

- 前置独立计划背书：`reports/queue-observer/workflow/t2/20261024T003445-84169f240563/endorse-0/review.json`，`status=PASS`；该 PASS 只授权本独立阶段，不代签 Owner 或完整 T2。
- 首轮实现独立复审：`reports/queue-observer/workflow/t2/20261024T003445-84169f240563/audit-1/review.json`，`status=REVISE`；本轮仅修复其超大整数错误泄漏、高深度递归栈泄漏、空 `styles` 静默接受与非法 Unicode 标量四项发现，不把该旧结论改写为 PASS。
- CR-01 core：新增有界 JSON 基本类型/文字结果到真实 A2UI v0.8 `Text/Row/Column/List` 扁平批次转换；转换完成后调用 T1 `validate_batch(..., final=True)`。纯文本、键值、列表、嵌套结构和实际 Brain 空生产队列文字已覆盖。
- CR-02 core：新增静态离线 HTML renderer；明确只支持 `Text/Row/Column/List/Card` 的 literal/explicit 子集。资源、action、binding、任意输入 styles、weight 和其他组件均显式拒绝；渲染前再次调用 T1 最终校验。
- 安全/边界：输入不变；转换与渲染均以显式栈支持公开配置内的高深度；超大整数先按精确十进制长度受限并安全转换；非法 Unicode 标量、循环、深度、条目、组件、文本、HTML 大小、非 JSON 类型及非有限数字均为确定性错误。空或非空输入 `styles` 均拒绝；T1 禁止内容显式映射为 `t1_validation_failed`。HTML 全量转义且可 UTF-8 编码，CSP 默认拒绝脚本、网络、资源、对象、frame 与表单动作。
- 真实闭环：只读调用现有 Brain 对生产 `tasks/tasks.json` 的明确查询，得到“当前任务库为空，共 0 个任务，没有当前异常。”，转 A2UI 后生成并解析静态 HTML；生产文件前后 SHA256 均为 `37517e5f3dc66819f61f5a7bb8ace1921282415f10551d2defa5c3eb0985b570`。
- 当前结论严格为 `T2-text-core-only partial / READY_FOR_REVIEW` 的开发回执，仍须新进程独立复审。没有完成 CR-01 全域、CR-02 WebView2/WinUI 原生窗口挂接、CR-03 ≥90% 截图、CR-04 窗口+语音双通道真机、T3 主题/悬浮球与语音四 IO、W5 或 Owner 门。

## 任务单元（L1 执行层）

| 单元 | 写什么 | 验收（逐项） | 证据 |
|---|---|---|---|
| CR-01 组件树消费 | 任意结果→组件树 | 转换可用 | 转换用例 |
| CR-02 渲染链路 | 组件树→窗口渲染 | 链路可用 | 运行输出 |
| CR-03 覆盖域清单 | 窗口覆盖任务域 ≥90% | 覆盖达标 | 截图对照 |
| CR-04 双通道交付 | 窗口+语音同时交付 | 双通道同时 | 真机记录 |
