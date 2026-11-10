# UltimaAgent 架构文档

> 依据：`H:\UltimaAI\ULTIMA-STANDARD.md`（Ultima AI Studio 产品顶层架构标准 v1.0）
> 更新：2026-11-10 ｜ 状态：阶段一已冻结（v0.1–v0.4）；ORB 冻结至 W8；**唯一未闭合项为语音真机门**。本文区分目标架构与实际实现。

## 身份
面向个人的桌面智能助手，按 `plans/product-plan.md` v2.3 与已冻结 PRD 推进。首场景为“查任务状态”，通过文字或语音输入读取真实任务状态，返回异常优先的汇报及动态组合窗口。工程开发用的看门狗、Codex 派发和 Console 汇总是开发基础设施，不是本产品的全部功能，也不由未来产品 Brain 自行开发本产品。

## 目标运行时（已批准，尚未全量实现）

- Windows 薄宿主负责输入输出、浮球、WebView2 渲染和协议通信。
- 智能端负责 L0-L10 能力编排、意图理解、真实队列状态读取、汇报、安全确认和记忆。
- 语音链路与文本链路在 v0.1 后分别验收；组合窗口消费结果和状态；安装与更新在 v1.0 联合收口。
- 设备接入按阶段扩展，首阶段不增加未批准的平台或完整设备能力。

产品数据流：文字/语音 → 意图解析 → 任务域映射 → 真实队列状态 → 异常优先聚合 → A2UI 组合窗口/语音 → 确认或待命。

## 目录结构（对齐范本）
```
UltimaAgent/
├── README.md            ✓
├── docs/                ✓（17 个一级条目：decisions/paradigms/reports/references/specs/tracker 等）
│   ├── architecture.md  ✓（本文档）
│   └── reports/         ✓ stage/审计/竞品报告
├── src/                 ✓ 9 模块 291 文件 / 48,388 行（brain 34,125／window 4,062／host-shell 3,936 等）
├── scripts/             ✓ 56 个 .py（派发/审计/冻结/编排/看门狗）
├── tasks/queue/         ✓ 工单卡 + queue_engine + runs 证据
└── sync/product.json    ✓
```

## 工程推进数据流（与产品运行时分开）
主脑登记工单与前置门 → 单工单 Codex 执行 → 真实回执 → 自检 → 主脑独立审计 W1-W8 → 用户版本冻结。看门狗监察及 Console 汇总读取登记与回执，不替代独立验收。

## 当前状态（2026-11-10，按实物核对）

> 核对口径：`tasks/queue/gates/` + `git tag` + `tasks/queue/runs/` 实物。文档描述与实物冲突时以实物为准（见 `docs/references/lessons-log.md` L103）。

**阶段一（S1）工单已全部冻结**
- W1 宿主：tag `wo-s1-host-shell-done`
- W2 队列引擎：tag `wo-s1-queue-engine-done`（35 项技术验收 + 62 项回归）
- 文本闭环：tag `wo-s1-task-text-loop-done`
- 版本冻结：`v0.1-frozen` / `v0.2-frozen` / `v0.3-frozen` / `v0.4-frozen`；凭据 `tasks/queue/gates/v0.1-frozen.json`、`v0.3-frozen.json`

**ORB 系列（已冻结至 W8）**
- `wo-orb-w6-frozen-20261110` / `wo-orb-w7-frozen-20261110` / `wo-orb-w8-frozen-20261110`

**GORCH 工程治理链（2026-11-09 → 11-10）**
- 契约 / 槽位 / 桥接 / 审计 / 判词口径 / r4–r17 逐轮 failopen 收口均已冻结。
- 当前 HEAD `8a95634f`（队列式工单进入审计与冻结，并修正判词解析），tag `gorch-card-form-unify-20261110`。

**唯一明确未闭合项：语音真机门**
- `tasks/queue/EXECUTION.md` 载明：Owner 选择先仅已有音频离线验证、继续文本；**不播放、不录音、不采集麦克风，语音工单及真机门尚未完成**。

**执行入口**
- `tasks/queue/EXECUTION.md`。产品队列 CLI 不等于跨项目工程自动调度服务。

**已知文档漂移（本文档自身曾发生）**
- 2026-10-21 版「W1/W2 尚未闭合」已过时：W1/W2 是两张工单编号且均已冻结。修正见 L103。

## 历史审计（2026-10-18，不代表本轮验收）
- 评分：78/100（基本合规）
- 结论：报告/工单齐全；缺产品特化数据流文档（已列入后续补）
