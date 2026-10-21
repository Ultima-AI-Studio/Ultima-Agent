# 阶段一任务单元执行队列（Stage1 Unit Queue）

- **版本**：v1.4 · 2026-10-16
- **性质**：CodeX 逐单元推进的**排序依据**（执行顺序事实源，从工单一到工单八全量 110 单元 + 8 个主脑验收节点 W1-W8）
- **权威口径**：queue-spec v1.1（状态机/派发纪律/dependsOn 语义）· acceptance-checklist v2.0（验收 Gate，每 U 单元带 L1 对照列）· version-plan（v0.1→v1.0 版本依赖链）· 工单总卡（wo-*.md，版本前置唯一登记处）
- **两类节点**：① L1 工程单元 001-110 = **CodeX 执行**（逐单元写什么/验收/证据，完成→自检→回执三件套）；② 工单验收节点 W1-W8 = **主脑侧审计收口，非 CodeX 执行**——由主脑（豆包侧审计视角）读取 CodeX 落盘的回执/报告文档，逐项核对证据、审核、裁决 PASS/打回，用户拍板后进版本冻结门。**Brain 为未来产品模块，不参与本产品开发**
- **用法**：CodeX 按编号 **001-110 顺序**逐单元执行；单元全绿后**停下等主脑工单验收**（W1-W8），不越级往下跑；同版本内可并行工单见标注；版本组尾触发冻结门，全绿才打 tag
- **单元明细**：每单元"写什么/验收（逐项）/证据"见对应任务卡「任务单元（L1 执行层）」表，本队列只做排序导航不复制正文（防双源漂移）

## 0. 执行顺序总览（版本依赖链）

```
v0.1 环境基线（工单① ∥ 工单② 并行，各自 W2/W1 验收）──→ v0.2 语音 PoC（工单③，W3 验收）
                                          ↘ v0.3 文本闭环（工单④，W4 验收）──→ v0.4 组合窗口（工单⑤，W5 验收）
                                                                                    ↘ v1.0 MVP+封装+远程更新（工单⑥ ∥ 工单⑦ 并行 → 工单⑧ 依赖⑦ 安装包，W6/W7/W8 验收 + 四信号，依赖 v0.2+v0.4 冻结）→ stage1-v1.0-frozen
```

| 版本 | 工单 | 单元数 | 工单验收 | 冻结门 |
|---|---|---|---|---|
| v0.1 | ①队列引擎 35 + ②宿主壳 17 | 52 | W2（①）+ W1（②） | W1/W2 通过 → tag `v0.1-frozen` |
| v0.2 | ③语音 PoC | 7 | W3 | W3 通过 → tag `v0.2-frozen` |
| v0.3 | ④文本闭环 | 10 | W4 | W4 通过 → tag `v0.3-frozen` |
| v0.4 | ⑤组合窗口 | 12 | W5 | W5 通过 → tag `v0.4-frozen` |
| v1.0 | ⑥MVP 冻结 12 + ⑦工程封装 5 + ⑧远程更新 12 | 29 | W6 + W7 + W8 | W6/W7/W8 通过 + 四信号全绿 → tag `stage1-v1.0-frozen` |
| **合计** | **8 工单 / 25 卡** | **110** | **W1-W8** | **5 道** |

---

## 1. v0.1 环境基线（52 单元 · 工单①∥② 并行，工单②完成后工单③才可开工）

### 1.1 工单② 宿主壳（17 单元 · U01-U05）

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-envcheck\task.md`（U01）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 001 | EN-01 | 9 项依赖逐一列出（项名/版本/路径） | 9 项全列出 | 检查表 |
| 002 | EN-02 | 每项 GREEN/RED 判定 | 状态标注齐全 | 检查表 |
| 003 | EN-03 | 检查表输出 logs/environment-check-<date>.md | 报告存在 | 文件核对 |
| 004 | EN-04 | 任一 RED → FAILED + 记录缺口 | 不静默通过 | 回执核对 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-winui3-init\task.md`（U02）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 005 | WI-01 | 创建 WinUI3 解决方案骨架 | 结构符合 architecture.md 分层 | 目录树 |
| 006 | WI-02 | 宿主壳项目依赖引用正确 | 引用无缺漏 | 构建输出 |
| 007 | WI-03 | App 类 + 主窗口占位 | 可运行、空主窗口显示 | 运行截图 |
| 008 | WI-04 | dotnet build 零错误零警告 | 构建全绿 | 构建输出 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-webview2\task.md`（U03）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 009 | WV-01 | WebView2 控件嵌入主窗口 | Runtime 初始化无异常 | 运行日志 |
| 010 | WV-02 | 加载空页/占位 HTML | 渲染成功 | 渲染截图 |
| 011 | WV-03 | WebMessage 往返一次成功 | 宿主↔Web 通信通 | 往返记录 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-floatingball\task.md`（U04）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 012 | FB-01 | 悬浮球窗口无边框、置顶 | 属性正确 | 截图 |
| 013 | FB-02 | 鼠标拖动 + 位置保持 | 拖动生效 | 真机截图 |
| 014 | FB-03 | 多 DPI 下位置不偏移 | 高 DPI 无偏移 | 真机测试 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-host-shell-selfcheck\task.md`（U05）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 015 | SC-01 | build→launch→window→exit 全链 | 全链 PASS | 自检输出 |
| 016 | SC-02 | 启动点 CREATE_NO_WINDOW/Hidden + 运行期窗口枚举全程计数 0 | 前台零弹窗（闪一下都不行，宿主 GUI 除外） | 窗口枚举输出 |
| 017 | SC-03 | 自检报告 logs/selfcheck-host-shell-<date>.md | 报告存在 | 文件核对 |

**→ W1 工单验收节点（主脑侧，非 CodeX）**：17 单元回执证据逐项核对 → 工单②总卡 DoD（总验收 + 文档同步）→ 裁决 PASS/打回 → 通过后并入 v0.1 冻结门

### 1.2 工单① 队列引擎（35 单元 · U06-U09）

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-storage\task.md`（U06）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 018 | ST-01 | 创建 cards/queue/events/runs/archive 五目录 | 五目录存在且可写 | 目录树 |
| 019 | ST-02 | 实现瘦身索引文件 | tasks.json 存在、仅索引字段 | 索引样例 |
| 020 | ST-03 | 11 个索引字段齐全 | task_id/state/priority/dependsOn/parallelGroup/fileDomain/reasoningEffort/created_at/updated_at/terminal_reason/card_path | 字段核对 |
| 021 | ST-04 | goal 全文存 cards/<task_id>/task.md | tasks.json 无 goal 全文 | grep 核对 |
| 022 | ST-05 | 状态事件追加写入 | 追加式、禁原地改写 | 事件文件样例 |
| 023 | ST-06 | before/out/err/done/session/progress | 六件套命名就绪 | 目录核对 |
| 024 | ST-07 | archive 只归档不删除 | archive/ 无自动删逻辑 | 代码核对 |
| 025 | ST-08 | 索引 >1 万条自动归档索引项 | 阈值逻辑存在且可触发 | 阈值测试 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-statemachine\task.md`（U07）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 026 | SM-01 | 八态枚举定义 | 八态枚举齐全 | 枚举核对 |
| 027 | SM-02 | QUEUED→EXECUTING→SELF-CHECK→AUDIT→COMPLETED | 单测全绿 | 单测输出 |
| 028 | SM-03 | FAILED→(retryCount<2)→QUEUED（~rN） | 修正重试正确 | 单测输出 |
| 029 | SM-04 | FAILED→(≥2)→BLOCKED | 超限转 BLOCKED | 单测输出 |
| 030 | SM-05 | CANCELLED（用户取消/被覆盖） | 取消可达 | 单测输出 |
| 031 | SM-06 | EXECUTING 直跳 COMPLETED 拒绝 | 非法迁移全拒并报错（含 EXECUTING→CANCELLED 覆盖） | 拦截用例 |
| 032 | SM-07 | 依赖方失败→被依赖方 BLOCKED | reason 记录"依赖 <id> 未完成" | 用例输出 |
| 033 | SM-08 | BLOCKED 解除仅人工/主脑裁决 | 无自动绕过上限 | 代码核对 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-dispatcher\task.md`（U08）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 034 | DI-01 | 默认一次一主，派发前检查闸门 | EXECUTING>1 时拒绝新派发 | 派发日志 |
| 035 | DI-02 | parallelGroup 组内并行，全队列 EXECUTING≤2 | 超限留 QUEUED+记录等待原因 | 并行用例 |
| 036 | DI-03 | 三重判定幂等防重派 | 探测失败按忙处理，宁可不派不重派 | 幂等用例 |
| 037 | DI-04 | 所有子进程启动点 CREATE_NO_WINDOW/pythonw/Hidden + 运行期窗口枚举全程计数 0 | 前台零弹窗（闪一下都不行） | 窗口枚举输出 |
| 038 | DI-05 | .pause-dispatch 标记时只读审计不派发 | 暂停生效 | 暂停用例 |
| 039 | DI-06 | 守护器=主脑子进程，父死降级只读静默+优雅退出 | 无主自治禁止 | 生命周期用例 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-priority-deps\task.md`（U08b）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 040 | PD-01 | 0-100 默认 50，越大越先派 | 语义正确 | 字段核对 |
| 041 | PD-02 | requeue --before <task_id> | 插到指定任务前生效 | 插队用例 |
| 042 | PD-03 | 同优先级按 created_at | FIFO 正确 | 排序用例 |
| 043 | PD-04 | 入队时 dependsOn DFS 环检测 | 有环拒绝入队+报环路径 | 环检测用例（A→B→C→A） |
| 044 | PD-05 | 依赖全 COMPLETED 才派发 | 未满足不派发 | 派发日志 |
| 045 | PD-06 | 插队/调优先级写 events（ts,from,to,reason,actor） | 留痕可查 | 事件日志 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-queue-engine-audit-e2e\task.md`（U09）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 046 | AU-01 | 回执三件套 reviewReason/stdoutText/evidence/acceptance | 回执结构完整 | 回执样例 |
| 047 | AU-02 | 缺回执不判 COMPLETED | 校验拦截生效 | 拦截用例 |
| 048 | AU-03 | 开发与审计技能分离 | 谁开发谁不自审 | 角色核对 |
| 049 | AU-04 | 落 logs/execution-reports/<task_id>/summary.json | 报告存在 | 文件核对 |
| 050 | AU-05 | 产物路径 vs fileDomain / 新组件 vs 注册表 / 报告完整性 | 三项核对可执行 | 审计输出 |
| 051 | AU-06 | 空任务库立项→派发→自检→审计→收尾 | 空库走通 PASS | 运行输出 |
| 052 | AU-07 | 证据不明确判 BLOCKED 留主脑 | 不猜测 PASS | 判定用例 |

**→ W2 工单验收节点（主脑侧，非 CodeX）**：35 单元回执证据逐项核对 → 工单①总卡 DoD（总验收 + 文档同步）→ 裁决 PASS/打回 → 通过后进 v0.1 冻结门

**→ 冻结门 v0.1**：W1 + W2 均通过 + 环境门全绿 + 文档同步 → tag `v0.1-frozen`

---

## 2. v0.2 语音链路 PoC（7 单元 · 工单③，依赖 v0.1 冻结）

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-voice-cv3-wiring\task.md`（U10）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 053 | CV-01 | CosyVoice3 文本→音频 | 合成成功、可播放 | 音频文件+日志 |
| 054 | CV-02 | sherpa-onnx 音频→文本 | 识别成功 | 识别日志 |
| 055 | CV-03 | 静音切分有效 | 边界定位准确 | 切分输出 |
| 056 | CV-04 | 合成→播放→识别→文本闭环 | 闭环一次成功 | 往返日志 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-voice-four-io\task.md`（U11）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 057 | IO-01 | 语音捕获→识别→文字 | 文字意图可识别 | 演示记录 |
| 058 | IO-02 | 文字→意图→响应 | 中转正确 | 链路日志 |
| 059 | IO-03 | 响应→固定音色合成输出 | 语音出闭环 | 音频输出 |

**→ W3 工单验收节点（主脑侧，非 CodeX）**：7 单元回执证据逐项核对 → 工单③总卡 DoD → 裁决 PASS/打回 → 通过后进冻结门

**→ 冻结门 v0.2**：W3 通过 + 真机链路通 → tag `v0.2-frozen`

---

## 3. v0.3 任务场景闭环·文本（10 单元 · 工单④，依赖 v0.1 冻结）

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-task-intent-parse\task.md`（U12）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 060 | IN-01 | "查任务状态"类意图识别 | 识别率 ≥90% | 用例测试 |
| 061 | IN-02 | 无明确指令不主动插话 | 行为正确 | 场景测试 |
| 062 | IN-03 | 测试输出 logs/intent-parse-test-<date>.md | 报告存在 | 文件核对 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-task-queue-source\task.md`（U13）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 063 | QS-01 | 任务域清单列全（六态+异常） | 清单无缺漏 | 清单核对 |
| 064 | QS-02 | 从队列引擎读真实状态 | 非硬编码 | 读取核对 |
| 065 | QS-03 | 字段同 queue-spec §10 | 无漂移 | 对照核对 |
| 066 | QS-04 | legacy-topo 只读引用 | 仅参考不拷贝 | 代码核对 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-task-aggregate-report\task.md`（U14）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 067 | AR-01 | 任务域按逻辑编排 | 编排合理 | 代码核对 |
| 068 | AR-02 | 20 任务 1 失败→只报异常并总结 | 不逐条念 | 场景实测 |
| 069 | AR-03 | 异常项可展开详情 | 下钻可用 | 场景测试 |

**→ W4 工单验收节点（主脑侧，非 CodeX）**：10 单元回执证据逐项核对 → 工单④总卡 DoD → 裁决 PASS/打回 → 通过后进冻结门

**→ 冻结门 v0.3**：W4 通过 + 文本闭环 PASS → tag `v0.3-frozen`

---

## 4. v0.4 组合窗口 + 悬浮球（12 单元 · 工单⑤，依赖 v0.3 冻结）

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-window-dsl-schema\task.md`（U15）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 070 | DS-01 | 组件树 DSL 语法落盘 | 语法文档存在 | 文档核对 |
| 071 | DS-02 | component-dsl-schema 校验规则 | schema 完整 | 文档核对 |
| 072 | DS-03 | 合法组件树通过 | 校验通过 | 校验用例 |
| 073 | DS-04 | 非法树拒绝、无死页面 | 校验拒绝 | 校验用例 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-window-composite-render\task.md`（U16，ultra 需评审背书）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 074 | CR-01 | 任意结果→组件树 | 转换可用 | 转换用例 |
| 075 | CR-02 | 组件树→窗口渲染 | 链路可用 | 运行输出 |
| 076 | CR-03 | 窗口覆盖任务域 ≥90% | 覆盖达标 | 截图对照 |
| 077 | CR-04 | 窗口+语音同时交付 | 双通道同时 | 真机记录 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-window-theme-floatball\task.md`（U17）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 078 | TF-01 | 图波主题 v1 落地 | theme-standard tokens 生效 | 样式核对 |
| 079 | TF-02 | 倾听/思考/说话/待命四状态 | 四状态齐全 | 定义核对 |
| 080 | TF-03 | 悬浮球四状态绑定正确 | 切换正确 | 真机记录 |
| 081 | TF-04 | 窗口+语音同时交付 | 同时交付 | 真机记录 |

**→ W5 工单验收节点（主脑侧，非 CodeX）**：12 单元回执证据逐项核对 → 工单⑤总卡 DoD → 裁决 PASS/打回 → 通过后进冻结门

**→ 冻结门 v0.4**：W5 通过 + 组合窗口 PASS → tag `v0.4-frozen`

---

## 5. v1.0 MVP 冻结（12 单元 · 工单⑥，依赖 v0.2+v0.4 冻结）

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-mvp-confirm-loop\task.md`（U18）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 082 | CL-01 | 交付后征询"你觉得怎么样？" | 触发正确 | 场景实测 |
| 083 | CL-02 | 调整请求→重呈现 | 重呈现生效 | 场景实测 |
| 084 | CL-03 | 调整请求确认后才执行 | 不静默改 | 场景实测 |
| 085 | CL-04 | 越界请求返回需授权提示 | 拒绝正确 | 场景实测 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-mvp-queue-adjust\task.md`（U19）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 086 | QA-01 | 展示队列（字段口径同 queue-spec） | 展示正确 | 用例输出 |
| 087 | QA-02 | 调整 priority 生效 | 生效 | 调整用例 |
| 088 | QA-03 | requeue --before 生效 | 插队生效 | 插队用例 |
| 089 | QA-04 | 操作写 audit event | 留痕可查 | 事件日志 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-mvp-credential-gate\task.md`（U20，eng.security ultra 需评审背书）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 090 | CG-01 | 读操作无副作用 | 只读安全 | 用例输出 |
| 091 | CG-02 | 写操作需授权 | 凭证闭环 | 凭证测试 |
| 092 | CG-03 | 非授权操作拒绝 100% | 全拒 | 越界用例 |
| 093 | CG-04 | 拒绝时如实反馈"未授权" | 不假装成功 | 场景实测 |

**→ W6 工单验收节点（主脑侧，非 CodeX）**：12 单元回执证据逐项核对 → 工单⑥总卡 DoD → 裁决 PASS/打回 → 通过后进项目级冻结门

---

## 6. v1.0 工程封装与安装包（5 单元 · 工单⑦，与工单⑥ 并行；工单⑧ 的上游，依赖 v0.1+v0.2+v0.4 冻结）

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-engineering-packaging\task.md`（U21）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 094 | PK-01 | 工程文件 → 自包含单文件 EXE（零依赖可双击运行） | 零依赖双击运行成功；窗口枚举：宿主 GUI 可见、其余计数 0（零弹窗 N7） | 运行实测 |
| 095 | PK-02 | 产品安装包（MSI/Inno Setup，版本资源/图标/开始菜单/卸载项） | 可双击安装、快捷方式存在、卸载项存在且可卸 | 安装/卸载实测 |
| 096 | PK-03 | WebView2 运行时检测与静默安装 | 缺失时静默安装零弹窗（窗口枚举 0）；已有则跳过 | 引导实测 |
| 097 | PK-04 | 安装包签名（与工单⑧ RU-03/RU-11 同钥） | 签名可验、篡改拒绝（硬性）；无公钥 fail-closed 不判通过（B1） | 签名验证 |
| 098 | PK-05 | 安装包即更新资产，与工单⑧ 发布/拉取链路闭环 | 发布工具上传 + 客户端拉取校验闭环一次成功 | 端到端闭环记录 |

**→ W7 工单验收节点（主脑侧，非 CodeX）**：5 单元回执证据逐项核对 → 工单⑦总卡 DoD（总验收 + 文档同步）→ 裁决 PASS/打回 → 通过后进项目级冻结门

---

## 7. v1.0 远程更新与发布通道（12 单元 · 工单⑧，原工单⑦ 顺延；依赖工单⑦ 安装包 + v0.2+v0.4 冻结）

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-remote-update-channel\task.md`（U22）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 099 | RU-01 | GitHub Releases API 查最新版本 + 资产地址（公开仓库匿名） | 返回正确版本与资产 | 查询实测 |
| 100 | RU-02 | 下载更新资产，哈希校验 | 下载完整、哈希一致 | 下载记录 |
| 101 | RU-03 | 客户端内置公钥验证 manifest+包签名 | 篡改/伪造 → 拒绝执行 | 篡改用例 |
| 102 | RU-04 | 替换前保留上一版本快照；失败自动回滚 | 失败回滚到上一版本 | 回滚用例 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-remote-update-trigger\task.md`（U23）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 103 | RU-05 | 启动时查 latest，有新版提示/静默更新 | 触发正确 | 启动实测 |
| 104 | RU-06 | 设置页"检查更新"按钮 | 点击触发更新检查 | 点击实测 |
| 105 | RU-07 | 服务端强制版本号 > 当前 → 无条件后台更新 | 强制更新生效 | 强制用例 |
| 106 | RU-08 | 设置页入口 + 更新中/完成/失败状态 | 状态展示正确、零弹窗 | 截图核对 |

卡：`H:\UltimaAI\UltimaAgent\tasks\cards\s1-remote-update-publisher\task.md`（U24，eng.security ultra 需评审背书）

| 序 | 单元 | 写什么 | 验收 | 证据 |
|---|---|---|---|---|
| 107 | RU-09 | 点发布 → 打 tag→构建→manifest→签名→上传→宣告 全链路 | 一次成功 | 发布实测 |
| 108 | RU-10 | manifest 生成（版本/哈希/强制位） | 字段齐全 | manifest 样例 |
| 109 | RU-11 | 发布端私钥签名 manifest + 包 | 客户端公钥可验 | 签名验证 |
| 110 | RU-12 | GitHub Release 上传成功 + 可选宣告强制版本 | 上传成功、宣告生效 | 发布记录 |

**→ W8 工单验收节点（主脑侧，非 CodeX）**：12 单元回执证据逐项核对 → 工单⑧总卡 DoD → 裁决 PASS/打回 → 通过后进项目级冻结门

**→ 冻结门 v1.0**：W6（工单⑥）+ W7（工单⑦）+ W8（工单⑧）均通过 + 项目级四信号全绿（闭环率 ≥80% / 覆盖 ≥90% / 越界拦截 100% / 诚实边界 100%）→ tag `stage1-v1.0-frozen`

---

## 8. 变更登记

| 版本 | 日期 | 变更 |
|---|---|---|
| v1.4 | 2026-10-16 | 工单⑦ 顺延重编号（用户决定：工程封装与安装包独立为工单⑦，原工单⑦ 远程更新顺延为工单⑧）：新增 U21（PK-01~05，094-098）；远程更新 U22-U24（RU-01~12，099-110，原 094-105 顺延 +5）；合计 8 工单/25 卡/110 单元/W1-W8；v1.0 门改为「⑥+⑦+⑧ 全绿 + 四信号」 |
| v1.3 | 2026-10-16 | N4-N7 微调（随工单⑦ 模拟评估落地）：零弹窗下钻单元验收（RU-02/04/07 窗口枚举计数 0；发布工具 RU-09/12 工程端口径=工具可带控制台但更新链路不得弹窗）；manifest schema 单一权威（specs/update-manifest-schema.md，N5）；查询失败/无网络静默降级口径（RU-01/05/06/07，N6）；N7 文档同步与 reports 计数修正（docs/README v2.9） |
| v1.2 | 2026-10-16 | 新增工单⑦ 远程更新与发布通道（U21-U23，12 单元 094-105），与工单⑥ 同属 v1.0 冻结门（W6+W7）；合计 7 工单/24 卡/105 单元/W1-W7；v1.0 门改为「⑥+⑦ 全绿 + 四信号」 |
| v1.1 | 2026-10-16 | 插入 6 个主脑验收节点 W1-W6（每工单单元全绿后停下等主脑收口）；明确执行者口径：主脑 = 豆包侧审计视角（读取 CodeX 落盘回执/报告 → 核对证据 → 审核 → 裁决 PASS/打回）+ 用户拍板，**Brain 为未来产品模块不参与本产品开发**；冻结门改为 W 节点通过后触发 |
| v1.0 | 2026-10-16 | 初版：工单一至工单六全量 93 单元排序（001-093），按版本依赖链 v0.1→v1.0 分组；每单元含写什么/验收/证据（导航到任务卡，不复制正文）；版本前置一律指向工单总卡（F3 语义） |


## 2026-10-21 当前验收状态

W2独立35项/62回归通过；W1维护后独立第四轮通过，两个内部工单tag已建立。Owner已明确批准v0.1冻结，实际v0.1-frozen固定43ce130，批准凭据tasks/queue/gates/v0.1-frozen.json已登记。工单④文本闭环已实际派发，开发及修复均真实退出0，W4技术验收通过且Owner已批准v0.3-frozen固定731710a；语音仅短派发预检与已有音频离线复验通过，完整工单/W3未完成。旧W1/W2证据见docs/reports/w1-independent-acceptance-20261021.md及w2-independent-acceptance-20261021.md；后续当前状态以全局逐工单登记为准。
