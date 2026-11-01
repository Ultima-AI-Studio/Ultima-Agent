# 今日攻坚目标卡 ｜ 2026-11-01 ｜ KWS / ASR / TTS 三块收口

> 状态：执行中（定版于 2026-11-01，用户指令："今天就定一个明确的目标，把 KWS、ASR、TTS 今天无论如何要尽快收掉，推进到下一个工作项目"）
> 北极星锚定：感知层随时在场 + 回答不瞎说（贾维斯最低闭环）

## 一、目标（一句话）

**今天（2026-11-01）内把 KWS / ASR / TTS 三块问题全部收口**：四个攻坚工单（0014-0017）全部 completed、真机验收通过、冻结 tag 落位，随后推进到下一个工作项目。

## 二、三块问题 → 工单映射

| 问题域 | 工单 | 收口判定 |
|---|---|---|
| KWS 唤醒词可改+持久化记住 | 0014（E）KWS 用户入口+持久化 | 语音改词生效 + 热重载 + 播报确认 + profile 持久化 + 一致性收敛；tag ultimaagent-kws-user-entry-20261101 |
| ASR 识别跑偏（水量天听/水天类） | 0015（F）ASR 纠错系统化 | initial_prompt 扩充 + 近音映射独立化 + 扩充；真机"查天气"类正确率对比；tag ultimaagent-asr-correction-20261101 |
| TTS 回复内容约束（防瞎回答） | 0016（C）路由门+校验器+主脑规则 + 0017（D）约束解码 | 域外不可信输入被拦（ALLOW/DENY/ABSTAIN）+ banned 语义化/≤2 句/grounded + 规则恒加载 + 结构化输出 {reply_text,confidence,grounded}；tag 两个 |

## 三、派发决策（0017 并行，不再空等）

- 0014/0015/0016 已于 2026-11-01 12:42 启动（PID 33244/25596/23504），进程存活、无致命 stderr。
- **0017 于 2026-11-01 本卡定版后立即并行启动**（用户"无论如何尽快收掉"指令优先于串行依赖的保守安排）。
- 并行安全边界：0017 的 T0（ollama format/grammar 能力实测）完全独立，先行执行；T1/T2 接入 schema 与 reply_verifier 时若 0016 已落地即用现成接口，未就绪则按工单 D 降级路径（grounded 接口留 schema 不阻塞），不产生写域冲突（0016 写 src/brain/routing/，0017 写 src/brain/reply/，唯一共享交互点是校验器接口，以降级路径规避）。
- 0017 工单内"依赖 0016 出口稳定后派发"备注按本卡覆盖为"并行派发，T2 降级规避"。

## 四、今日验收口径（全部满足才算收口）

1. 全局登记：0014/0015/0016/0017 = completed（_shared/queue/global-queue-index.md）。
2. 八字段回执四份齐（tasks/queue/runs/ 或工单卡侧），完成状态=已完成。
3. 全量回归 pytest 全绿（tools/venv-openjarvis/Scripts/python.exe，Python 3.13.16）。
4. 四个冻结 tag 存在且 git rev-parse 可解析（kws-user-entry / asr-correction / reply-constraint-routing / reply-constraint-structured），免代理 push 远端。
5. 真机验收三条：改唤醒词→说新词能唤醒+重启仍生效；说"查天气"不再被"水量天听"带偏；诱导/域外提问不再瞎回答（兜底话术或 DENY）。
6. 北极星清单勾选推进：KWS 入口+持久化、ASR 纠错系统化、意图路由门、回答约束、双模型实测相关项 → 勾选后进入下一工作项目。

## 五、不达标时的升级线（今天内闭环）

- 17:00 前：三单无回执 → 读 runs/out.jsonl 定位卡点，必要时向执行端补载荷推进，不静默等待。
- 任一单阻塞：读 err.log + final.json 判断根因 → 有界修复（补工单/补载荷）→ 重派；不跨天。
- 真机验收若受 daemon/音频栈外围影响：按冻结原则登记已知问题打 tag，功能验收以单测+日志证据收口，不无限深挖。

## 六、收口后动作

- 阶段报告四份（stage-kws-user-entry / stage-asr-correction / stage-reply-constraint-c / stage-reply-constraint-d）齐。
- lessons-log 登记本次派发与降级决策（0017 并行 + 降级规避）。
- 向用户交付收口结论 → 用户拍板下一工作项目。
