# DeepSeek Super-agent 参考架构调研（dsh-superagent-prototype）

> 调研：2026-11-01 豆包主脑 ｜ 对象：deepseek-ai/dsh-superagent-prototype（2026-10-31 公布）+ 理念文《Super-agent 设计探索》
> 结论先行：**不能直接用于 UltimaAgent（研究原型、Node 栈、面向研发协作、无语音、官方声明非正式产品）；但架构理念是目前与北极星"贾维斯"最同频的外部参考，Router/Worker 分层、observe/auto 主动性、事件-工单模型可直接借鉴，与 OpenClaw 同属"参考架构"定位。**

---

## 1. 是什么

- 2026-10-31 晚 DeepSeek Harness 团队公布：一套《Super-agent 设计探索》理念文 + 公开代码仓库 dsh-superagent-prototype。
- 官方声明：**研究原型**，经公开发布所需改编，与内部版本及长文实现不完全相同，**部分设计尚未落地，不是 DeepSeek 正式产品**。
- 技术栈：基于 DeepSeek Harness（dsh，"一切皆插件"、Cordis 插件体系，Node/npx），以插件组合包形式运行。
- 当前形态：面向**研发协作**——围绕一个 GitHub 仓库工作，可接入飞书。
- 目标概括：连续、高效、主动、持久；核心指标 = **人的注意力成本**（消息/通知/提问/面板元素都是注意力成本）。

## 2. 核心架构（已核验）

| 层/对象 | 职责 |
|---|---|
| Router（主会话） | 判断候选事件、接受和分派工作、跨任务协调 |
| Worker（执行会话） | 读原始材料、判断任务范围、实现修改并验证（内部可调子 Agent） |
| Ticket（工单） | 记录一项获准工作的输入、进展、交付状态 |
| Trigger（事件） | 一条消息、评论或状态变化 |
| Thread（讨论线程） | 一组按时间排列的相关事件 |
| Subscription（订阅） | 把讨论线程后续事件送到相关工单（连续协作的关键） |

- **主动性分级**：off / observe（默认：评估候选，正面判断仅记录"本来会接单"，实际不开工单）/ auto（匹配启用规则后接单）。明确授权请求三模式下均可执行。
- **长任务**：>5s 前台 Shell 命令转后台作业，Worker 后续推理可接收新输入；后台完成后唤醒继续。
- **并发保留名额**：人工跟进/状态请求占用保留名额，避免被普通工作挤占。
- **持久恢复**：保留会话/目录/订阅/待处理输入；重启后恢复派工并附恢复说明（如"提交已推送仅回执丢失"则不再重做）；先记录后执行 + 持久队列重试。
- **面板优先**：先展示待回答/待审阅/受阻/失败，再给健康/历史/负载——"现在有什么需要我"。
- **边界**：收到上下文 ≠ 获得新授权；不同平台账号不自动合并身份；授权与操作系统权限分离（公开实现无安全沙箱，官方建议独立系统账号）。
- 实验数字：任务完成中位数 12.4min / p95 15.7min——官方口径"主要评价调度与协作，不能直接推导真实编码质量或生产提效比例"。

## 3. 对 UltimaAgent 的评估

### 不能直接用（4 条硬理由）
1. **研究原型**：公布 1 天，官方明示"部分设计尚未落地、非正式产品"，做生产基座风险极高。
2. **技术栈错配**：Node/Cordis 插件体系，与 UltimaAgent 原生 Windows Python 语音栈（KWS/ASR/TTS/CV3）嫁接成本高，与 OpenClaw 同类问题。
3. **领域错配**：面向研发协作（GitHub+飞书事件驱动），不是语音个人助手；**无 KWS/ASR/TTS 任何语音能力**。
4. **授权模型不匹配**：授权基于仓库/平台事件，非"人机语音对话"场景。

### 非常有用（理念与北极星最同频）
- "确认任务后安静工作；有可用结果/需要决策/无法完成时才发言；需人回答的问题结构化单独提出；未完成成果明确标未完成" —— 几乎就是贾维斯"不打扰与反馈闭环"原则的工程化。
- 核心指标"人的注意力成本" —— 与 UltimaAgent"不打扰"验收线同一度量。

### 可借鉴点（映射到北极星清单）
| 借鉴点 | 落到 UltimaAgent |
|---|---|
| Router/Worker 分层 | 未来"主脑 + 能力层路由"的细化模板 |
| observe→auto 主动性分级 | HUD"不打扰"的工程实现路径（先观察记录、后放开接单） |
| Trigger/Thread/Ticket/Subscription 对象模型 | 记忆分层/跨轮上下文的连续协作模型 |
| 面板"现在有什么需要我" | HUD 桌面形态的信息优先级设计 |
| 后台作业 + 恢复说明 + 持久队列 | harness 10 模式中的可恢复会话/有界迭代落点 |
| 授权与执行权限分离 | 工具权限范围化（harness 清单项） |

## 4. 定位结论

- OpenClaw 与 DeepSeek Super-agent **同属"参考架构"，只借鉴不替换**（与北极星定位原则一致）。
- 两者互补：OpenClaw 强在"本地网关+多渠道+工具"，Super-agent 强在"任务协调+主动性分级+注意力设计"。
- **未来关联**：若 UltimaAgent 走"本地 DeepSeek 大模型"路线（如 DeepSeek V4 系），DeepSeek Harness 生态是天然对接点，届时重新评估可复用性。

## 5. 参考

- 腾讯云解读：https://cloud.tencent.com/developer/article/2773284
- 新浪科技：http://tech.sina.com.cn/csj/2026-11-01/doc-inixepty4335109.shtml
- GitHub：https://github.com/deepseek-ai/dsh-superagent-prototype
- DeepSeek Harness：https://www.deepseek.com/harness/en/ ｜ https://github.com/deepseek-ai/deepseek-harness
