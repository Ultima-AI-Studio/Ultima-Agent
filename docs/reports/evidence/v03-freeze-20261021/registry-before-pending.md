# Ultima 全局 Codex 队列主表（看门狗监察总表）

> 唯一权威：本表为**全项目 Codex 执行队列的全局汇总**，所有 Ultima 项目派给 Codex 的工单必须在本表登记一行（项目 + 工单 + 状态 + 冻结门 + 回执）。
> 建立：2026-10-19 ｜ 依据：Codex 外部执行端调用范式 v1.1（§3 队列三件套 → 全局登记）
> 各项目本地队列（`<项目>\tasks\queue\`）为明细源，本表只做状态聚合与 WIP 监察，不复制工单正文（防双源漂移）。
> 状态机：待派发 → 执行中 → 审计中 → 已冻结；**WIP 双层（2026-10-20 拍板）：每项目执行中 ≤1 + 全项目执行进程 ≤3；审计中 ≤1；一单一进程，禁止一包多单**。

## 一、全局队列总览

<!-- queue-summary:start -->
| 项目 | 工单数 | 待派发 | 登记执行中 | 待审计 | 阻塞 | 已完成/闭环 |
|---|---|---|---|---|---|---|
| UltimaConsole | 18 | 0 | 0 | 0 | 1 | 17 |
| UltimaAgent | 10 | 5 | 0 | 0 | 0 | 5 |
| UltimaSentinel | 13 | 1 | 1 | 0 | 2 | 9 |
| UltimaEngine | 0 | 0 | 0 | 0 | 0 | 0 |
| UltimaGold | 0 | 0 | 0 | 0 | 0 | 0 |
| UltimaRadar | 0 | 0 | 0 | 0 | 0 | 0 |
| UltimaScan | 0 | 0 | 0 | 0 | 0 | 0 |
| 合计 | 41 | 6 | 1 | 0 | 3 | 31 |
<!-- queue-summary:end -->

## 二、各项目队列明细（指针 + 状态摘要）

### UltimaConsole（17 单已完成/闭环 + v12-ui 待模拟器验收）
- 本地主表：`H:\UltimaAI\UltimaConsole\tasks\queue\console-queue-index.md`
- 状态镜像：`queue-status.json`（total=18 frozen=17 in_progress=0 audit=0 blocked=1）
- 冻结门：`docs\reports\stage-m1..m8.md` + `stage-v11-n1..n6.md` + `stage-ui-recheck.md` 全存在
- 最近闭环：v1.1-N6 悬浮球扫光动画（2026-10-19 Codex 回执全 Gate PASS，`v11-n6-frozen`）
- **当前阻塞（2026-10-21修复构建通过，模拟器验收未完成）**：`wo-console-v12-ui` UI 范式对齐修复（T0-T9 10/10 PASS + 回归 46/46 + 构建 PASS + 横竖屏截图在仓，stage-v12-ui.md；只核对不修复的 ui-recheck 已完成 32/32）

### UltimaAgent（8 开发工单 / 110 单元 + 2 审计工单）

- 当前：队列引擎W2与宿主W1已独立验收并完成内部工单tag；维护重启清除旧自检残留，正负向复验通过；v0.1已获Owner批准并冻结43ce130，后续6单仍等待各自版本门。旧真实派发失败记录保留。
- 本地主表：`H:\UltimaAI\UltimaAgent\tasks\queue\stage1-unit-queue.md`（v1.4）
- 结构：工单①-⑧（队列引擎/宿主壳/语音 PoC/文本闭环/组合窗口/MVP/工程封装/远程更新），CodeX 逐单元 001-110 推进，主脑 W1-W8 验收
- 冻结门：v0.1 → v0.2 → v0.3 → v0.4 → stage1-v1.0-frozen 共 5 道

### UltimaSentinel（10 工单）

- 最近派发已结束：2026-10-21 05:49–05:54（PID24852）；TU-2.0 与 TU-2.0.5 通过，TU-2.1 因真实离线复放包缺失 BLOCKED，TU-2.2~2.7未启动。最新证据：docs/reports/evidence/m2/TU-2.1/redispatch-2026-10-21T055352330/stage2-acceptance-receipt.json。上轮于 2026-10-20 22:04 因离线复放资源缺失停止，TU-2.2 至 TU-2.7 未启动。以下为历史记录。
- 本地主表：`H:\UltimaAI\UltimaSentinel\tasks\queue\index.md`
- 状态：M1 已冻结 / M2 已审计 / M2.1 已修订 / M-Plan 系列已审计修复 / **M0.5 已验收（2026-10-19 主脑签字 ACCEPTED，index.md v1.4）** / **M1a 已验收（2026-10-20 主脑签字：TU-1.1b/TU-1.2/TU-1.3/TU-1.4 全签，真实 PG+Redis 全量回归 92 passed/0 failed，stage-m1a.md §11）** / **M1b 已验收冻结签收（2026-10-20：TU-1.5~1.9 全完成 + 冒烟 PASS + issue-registry 8 项全部 CLOSED，stage1-acceptance.md 主脑批准签字）** / **M2a 历史阻塞回执（已于 2026-10-20 重派，见本地索引；历史记录：wo-m2a v1.2 拍板派发，TU-2.0 PASS、TU-2.0.5 因六类样本/truth 隔离/金标/RPC 资源未就绪如实 BLOCKED，未伪造冻结；受保护基线零回退；待资源到位从 TU-2.0.5 重派；回执 docs/reports/stage2-acceptance-receipt.json + 阻塞记录 evidence/m2/TU-2.0.5/blocked-2026-10-20.md）**
- 派发记录（2026-10-19）：dispatch-m1-prompt.txt 已生成，Codex 后台会话执行（gpt-5.6-sol · high · workspace-write）
- **TU-1.1 阻塞解除重派记录（2026-10-19 主脑审计 + 用户确认）**：42 合成夹具样本批准为机制验证集（`benchmark\manifest-m1.json` 审批人字段已签）；C02/C05/C10 批准受限宣称（capability-matrix-m1.md 已签）；新增 TU-1.1b 真实项目锚点样本单元（每类 ≥1，主脑逐类验收）；冻结重建由主脑本地补做回填 rebuild_status；wo-m1a 升 v1.3
- **TU-1.1b 验收与 TU-1.1c 派发记录（2026-10-19 主脑验收签字 + 用户确认）**：真实锚点续派 BLOCKED_AT_TU_1_1B_RULE_GATE（正例规范位置命中 3/7，C01/C03/C04/C08 漏报已核实）；主脑独立复核后签 C06/C07/C09（样本级，位置覆盖登记加强项）；wo-m1a 升 v1.4 新增 TU-1.1c 规则引擎升级单元（开发集开发、14 真实锚点独立重验、禁止调参）；dispatch-m1c-prompt.txt 已生成，Codex 后台派发中；每小时跟踪审查定时任务已重建
- **TU-1.1c 重验与 TU-1.1d 派发记录（2026-10-19 主脑汇总审查 + 用户确认）**：TU-1.1c 续派重验完成——C03 L7/C04 L217/C08 L28 规范位置命中、C06 不回退、C07 位置 3/4、C09 位置 4/4、负例 7/7、42 机制集 42/42；C01 L987 仍漏报（`.value()` 形态外部交互未枚举）→ BLOCKED_AT_1C_7_C01_CANONICAL_LOCATION；主脑独立复核属实，签 C03/C04/C08 升级验收；wo-m1a 升 v1.5 新增 TU-1.1d C01 专项修复单元；dispatch-m1d-prompt.txt 已生成，Codex 后台派发中；每小时跟踪审查定时任务「UltimaSentinel M1d 执行跟踪审查」已重建
- **TU-1.1d 验收与 TU-1.2~1.4 续派记录（2026-10-19 主脑复验收 + 用户确认）**：TU-1.1d 重验全绿——C01 `.value()` 形态枚举（1.2.0），L987 规范位置命中、L199 错位未复现、42/42 不回退、负例 7/7、三测试全绿；主脑独立复核后 C01 复验收签字，TU-1.1b 七类真实锚点验收全部完成；M1d 跟踪已停表；wo-m1a v1.5 续派 TU-1.2~1.4（结论聚合/持久化/调度一致性），dispatch-m1-continue-prompt.txt 已生成，Codex 后台执行中；每小时跟踪审查定时任务「UltimaSentinel M1 续派执行跟踪审查」已重建

### UltimaEngine / UltimaGold / UltimaRadar / UltimaScan（暂无队列）
- 未建 `tasks\queue\`：后续任何派 Codex 的工单，须先在本表登记 + 建项目本地队列，禁止绕过全局登记直接派单。

## 三、看门狗监察项

1. **状态合法性**：每项目工单状态 ∈ {待派发/执行中/审计中/已冻结}，无越界声明缺口。
2. **冻结门闭合**：状态为"已冻结"的工单，其阶段报告/冻结 tag 必须存在（Console 查 `docs\reports\stage-*`；Agent 查版本冻结 tag；Sentinel 查阶段报告）。
3. **阻塞与回执**：执行中超过合理窗口、回执缺失、阻塞项 → 异常上报。
4. **WIP 上限**：全项目合计登记执行中 ≤3、审计中 ≤1，超限提示暂停派单。
5. **登记完整性**：任何项目有 Codex 工单但未在本表登记 → 越界，提示补登记。

## 四、逐工单统计登记（统计唯一输入）

> frozen 表示已完成/验收/审计闭环，不额外宣称存在冻结 tag。executing 为队列登记状态，不代表实时进程数。更改工单状态后运行 queue-status-gen.py，汇总及 JSON 从此表计算。

<!-- queue-items:start -->
| 项目 | 工单 | 状态 | 依据/说明 |
|---|---|---|---|
| UltimaConsole | wo-console-m1 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-m2 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-m3 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-m4 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-m5 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-m6 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-m7 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-m8 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-v11-n1 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-v11-n2 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-v11-n3 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-v11-n4 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-v11-n5 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-v11-n6 | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-v11-ic | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-ui-recheck | frozen | 已完成/闭环 |
| UltimaConsole | wo-console-v12-ui | blocked | 代码门禁10/10、回归46/46、JDK21签名构建通过；模拟器IO-APIC panic，HypervisorPlatform已启用待重启复验；新构建视觉验收未闭合 |
| UltimaConsole | v11-datachannel | frozen | 已完成/闭环 |
| UltimaAgent | wo-agent-audit-s1-fix | frozen | 已审计闭环 |
| UltimaAgent | wo-agent-audit-s1 | frozen | 已审计闭环 |
| UltimaAgent | wo-s1-composite-window | pending | 等待 v0.3 冻结（文本闭环） |
| UltimaAgent | wo-s1-engineering-packaging | pending | 等待 v0.1 + v0.2 + v0.4 冻结；签名及安装环境前置见工单 |
| UltimaAgent | wo-s1-host-shell | frozen | 维护重启后W1独立第四轮通过，原59328已清除；内部tag wo-s1-host-shell-done；旧派发失败保留，Owner已批准v0.1-frozen |
| UltimaAgent | wo-s1-mvp-freeze | pending | 等待 v0.2 + v0.4 冻结（语音及组合窗口） |
| UltimaAgent | wo-s1-queue-engine | frozen | W2独立35项/62回归、真实卡及修正闭环、独立U01通过；内部tag wo-s1-queue-engine-done；非v0.1版本冻结 |
| UltimaAgent | wo-s1-remote-update | pending | 等待 v0.2 + v0.4 冻结及工单⑦安装包；发布仓库/凭证前置见工单 |
| UltimaAgent | wo-s1-task-text-loop | frozen | W4通过；Owner已批准v0.3-frozen固定731710a；原失败证据保留 |
| UltimaAgent | wo-s1-voice-poc | pending | Owner选择仅已有音频离线验证、继续文本闭环；短派发真实exit0已复核；语音实现/真机/W3未完成；wo-s1-voice-poc-20261021T041728559262Z |
| UltimaSentinel | M1 | frozen | 已验收/审计闭环 |
| UltimaSentinel | M2 | frozen | 已验收/审计闭环 |
| UltimaSentinel | M2.1 | frozen | 已验收/审计闭环 |
| UltimaSentinel | M0.5 | frozen | 已验收/审计闭环 |
| UltimaSentinel | M1a | frozen | 已验收/审计闭环 |
| UltimaSentinel | M1b | frozen | 已验收/审计闭环 |
| UltimaSentinel | M2a | blocked | 2026-10-21 05:54 复查后结束：TU-2.1 M2_OFFLINE_REPLAY_ARTIFACTS_NOT_READY；证据 redispatch-2026-10-21T055352330/stage2-acceptance-receipt.json |
| UltimaSentinel | M-Plan | frozen | 已验收/审计闭环 |
| UltimaSentinel | M-Plan2 | frozen | 已验收/审计闭环 |
| UltimaSentinel | M-Plan3 | frozen | 已验收/审计闭环 |
| UltimaSentinel | maint-pipeline | blocked | 本地实现/61项离线回归/代码复核完成；待真实PG/Redis/Celery/Docker补验与独立发布签收。维护报告 docs/reports/maintenance-pipeline-2026-10-21.md；非M2a后续通过 |
| UltimaSentinel | unified-planning | pending | 文档已交付，仅待Owner评审，禁止自动派发；三份v0.1草案/10需求/13候选工作包/19链接校验通过；docs/unification/2026-10-21/；原M2a仍blocked。不占现有审计WIP |
| UltimaSentinel | unified-work-order-planning | executing | 用户授权全部工单与任务单元规划；本轮仅编制及校验，不实施、不派发候选单 |
<!-- queue-items:end -->

