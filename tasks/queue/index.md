# UltimaAgent 项目队列主表

> 唯一权威：本表为 UltimaAgent 项目 Codex 执行队列的**项目级唯一权威汇总**；明细源 = `tasks/queue/<工单文件>`；状态聚合镜像 = `queue-status.json`。
> 建立：2026-10-29（M29 工单派发时补建）｜ 依据：Codex 外部执行端调用范式 §3（工单队列三件套）
> 状态机：待派发 → 执行中 → 审计中 → 已冻结；WIP 双层（每项目执行中 ≤1 + 全项目执行进程 ≤3；审计中 ≤1）；一单一进程，禁止一包多单。

## 一、项目队列总览

| 工单 | 任务数 | 待派发 | 执行中 | 待审计 | 阻塞 | 已完成/闭环 |
|---|---|---|---|---|---|---|
| wo-ultimaagent-20261029-0001 | 4 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261029-0002 | 5 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261030-0003 | 5 | 0 | 0 | 0 | 1 | 0 |
| wo-ultimaagent-20261030-0006 | 3 | 1 | 0 | 0 | 0 | 0 |
| wo-ultimaagent-20261030-0004 | 5 | 1 | 0 | 0 | 0 | 0 |
| wo-ultimaagent-20261030-0005 | 5 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261030-0007 | 5 | 0 | 1 | 0 | 0 | 0 |
| wo-ultimaagent-20261031-0008 | 6 | 0 | 1 | 0 | 0 | 0 |
| wo-ultimaagent-20261031-0009 | 5 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261031-0010 | 5 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261031-0011 | 4 | 0 | 0 | 0 | 0 | 1 |
| wo-ultimaagent-20261031-0012 | 4 | 0 | 1 | 0 | 0 | 0 |

## 二、明细

| 工单 | 状态 | 依据/说明 |
|---|---|---|
| wo-ultimaagent-20261029-0001 | 已冻结 | M29 登记控制面（编号核发 + 全局主表 + WIP）；T0-T3 Gate 全绿（专项 12 passed / 编排回归 32 passed / 全量 679 passed + 120 subtests）；提交 b4d282d + tag wo-ultimaagent-20261029-0001-closed-20261029；2026-10-29 主脑独立审计通过 |
| wo-ultimaagent-20261029-0002 | 已冻结 | SSE /events 事件出口（HUD 四角壳真实数据源）；T0-T4；2026-10-29 登记，用户明确要求补 SSE 出口；2026-10-29 派发 codex gpt-5.6-sol PID 10892；独立验收复核 PASS + 四角壳真数据模式端到端演示验收通过 + Owner 确认冻结；tag wo-ultimaagent-20261029-0002-frozen-20261029 |
| wo-ultimaagent-20261030-0003 | 阻塞 | 多层级覆盖 voice-profile（L1 内置默认=贾维斯 / L2 voice-profile.json / L3 运行期覆盖；唤醒词热重载；回答风格三硬约束）；T0-T3 PASS、T4 BLOCKED（2 个范围外既有失败：HUD 冻结哈希漂移 + tasks.json QUEUED 缺 terminal_reason 致 fail-closed）；2026-10-30 登记；派发 codex gpt-5.6-sol PID 18480（已结束）；工单卡 tasks/queue/wo-ultimaagent-20261030-0003--voice-profile.md；清障交 0006 |
| wo-ultimaagent-20261030-0006 | 待派发 | 0003 T4 阻塞清理（HUD 冻结哈希重冻结 + 队列读取容缺）；T0-T2；2026-10-30 登记；优先派发（清障后再推 0004/0005）；工单卡 tasks/queue/wo-ultimaagent-20261030-0006--t4-clear.md |
| wo-ultimaagent-20261030-0004 | frozen | 语音输入通道升级（设备自动探测 + 48k WASAPI A/B）；T0-T4；2026-10-30 登记；冻结 tag wo-ultimaagent-20261030-0004-frozen-20261030；工单卡 tasks/queue/wo-ultimaagent-20261030-0004--input-channel.md |
| wo-ultimaagent-20261030-0005 | frozen | CV3 贾维斯音色（voice 段 + TTS 本地优先）；T0-T4；2026-10-30 登记；三派 PID 21828 收尾（首派 11764 网络失败留证、二派 26236 T4 收尾 OOM 留证）；主脑复核 906/0 + 真机中英转写命中 + 4 Important 一次修复；冻结 tag wo-ultimaagent-20261030-0005-frozen-20261030；工单卡 tasks/queue/wo-ultimaagent-20261030-0005--cv3-jarvis-voice.md |
| wo-ultimaagent-20261030-0007 | executing | 双线程伪流式（采集∥识别，1s 重跑节流 + 说完终跑 + 异常回退）；T0-T4；2026-10-30 登记；源任务卡 voice-136-pseudo-streaming（tasks.json QUEUED）；写域 data/logs/voice-listen-daemon.py + 基线变更记录追加 #136（不改值）；工单卡 tasks/queue/wo-ultimaagent-20261030-0007--pseudo-streaming.md；首派 26832 受阻 T0 → 主脑裁定收敛（门控 0.01/0.002、score 2.0、BEEP 1.2）→ 二派 7264 T4 硬件回放 OOM 留证 → 三派 17132 T0-T3 全绿、T4 物理耦合受阻（async-play 竞态 L26）→ Owner 拍板物理耦合+竞态修复进冻结门 → 四派 39480：A 竞态修复完成（_LOG_LOCK）、C 记录更新完成，T4 耦合标定 0 命中受阻；主脑复核纠偏：根因为运行 daemon 23588 MME 采集退化（16:36 起环境电平恒 0 + CPU 满载，L25 同型）非物理距离 → 五派修复重测中 |
| wo-ultimaagent-20261031-0008 | executing | GPT-SoVITS V3 few-shot 微调训练（杨幂 MOV 音色，LoRA 路线）；T0-T5；2026-10-31 登记；多轮重派（T1 人工听读定稿 A/C 段 → T2 重入 PASS → T3 TCPStore 端口 10013 → MASTER_ADDR/PORT 固定绕随机端口）执行中；冻结门=tag ultimaagent-gptsovits-v3-fewshot-20261031 |
| wo-ultimaagent-20261031-0009 | completed | KWS 唤醒词动态改词自动化验证闭环（scripts/kws_reconfig.py 四子命令）；T0-T3 全 PASS；commit e6ee286 + tag ultimaagent-kws-wakeword-reconfig-20261031 已推远端 |
| wo-ultimaagent-20261031-0010 | completed | 主脑模型降档 qwen2.5:14b → qwen3-8b 无审查版（内存实降 4.1GB）；T0-T3 全 PASS；commit 69d46c0+09a7abc + tag ultimaagent-mainbrain-qwen3-8b-20261031 已推远端 |
| wo-ultimaagent-20261031-0011 | completed | HUD 四角壳 8 锚点布局改造；T0/T1/T2-C1~C5/C7 全 PASS；commit 5cdfca3 + 报告 e00d927 + tag ultimaagent-hud-8anchor-20261031（本地=远端）；T3 八字段回执已交 |
| wo-ultimaagent-20261031-0012 | executing | HUD 天气组件接入（#hud-weather 纯文本占位 → 官方 Meteocons Monochrome 动画图标 + cyan 辉光 + 降水细分映射）；T0-T3；2026-10-31 登记；工单卡 tasks/queue/wo-ultimaagent-20261031-0012--hud-weather-component.md；派发载荷 dispatch-wo-ultimaagent-20261031-0012-prompt.txt；2026-10-31 派发 codex gpt-5.6-sol PID 24736（静默后台）；冻结门=tag ultimaagent-weather-component-20261031 |
