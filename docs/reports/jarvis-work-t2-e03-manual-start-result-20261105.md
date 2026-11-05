# E03 显式开始单例结果与独立复核

原工单 `wo-ultimaagent-20261101-0021`，T2。当前候选 `7975e477665c02820fa235b73d203718bd33b2c9`，仅当前 `qwen3-8b-uncensored`。本次用户授权的一例 E03 round1 和一次只读独立结果复核均已完成并耗尽，没有重跑。

**案例 FAIL；独立证据复核 PASS；产品事实与 rewrite.md 不可评价。** 主窗口的显式开始和焦点交接在本例成功，后续副窗口光标变化触发原保护检查，流程在 CLI 工作请求提交前停止。不能将准备审查、成功交接或保留原文计作产品完成。

| 检查项 | 实际结果 |
|---|---|
| 开始按钮 | 6.170398 秒内接受，按键已释放，窗口和按钮身份匹配 |
| 焦点交接 | 两次 activation 均 PASS，没有 AttachThreadInput |
| 主窗口 | 原文 41 UTF-16 单元保持，三次快照选区均 `[0,41]` |
| 副窗口 | 原文 39 UTF-16 单元保持，选区从 `[0,0]` 变为 `[39,39]` |
| 停止位置 | `Frozen fixture selection mismatch`；isolated server 已启动，CLI 提交次数 0 |
| 产品交付 | 没有 product-result、rewrite.md 或输出文件；事实不可评价 |
| 清理与保护 | cleanup/audit/boundaries PASS；9 个原自有/仅观察身份均消失，7 个保护身份匹配，官方语音 ready/fresh |

日志在北京时间 20:58:47（开始后约 3.22 秒）记录副窗口的 `WM_LBUTTONDOWN` 祖先，以及嵌套 `WM_SETFOCUS`。用户随后确认“点击过其他位置或窗口”，与测试期间存在鼠标操作相符。该回复未指定确切落点，日志也未记录完整光标变化过程，因此不扩大为所有消息或旧失败的确定归因。先前主窗口清空现象在这一次没有复现。

提示上的不足也应记录：按钮文字只强调“暂停键盘输入”；本次结果说明，后续受控用例必须明确要求点击开始后同时暂停鼠标点击、键盘输入和窗口切换，直到收到结束通知。原文本、选区和副窗口保护门保持；本轮不为了通过而放宽门，也不启动第二次用例。

独立 reviewer 核对 54 项封存文件和 46 项结果证据、authority/proof/admission 绑定及原始 UTF-8 文本，未发现证据修正项。其结论为 `facts=NOT_EVALUABLE_NO_PRODUCT_OUTPUT`，另存收据；原 terminal 中的待事实复核字段保持原样。`input_events=0` 只针对主审计记录类别，不能表述为“无鼠标或焦点活动”；共享模型服务的整体推理计数仍未知。

证据目录：`data/evidence/jarvis-work-capability/T2/e03-source12-manual-start-20261105-r2/`。

- 准备 manifest：`a720ad4f77d56689321da3fb9cfbae557890f22607260b1e621b0819c7aec5a3`。
- 单例 terminal：`5e01990413eb6697b1287b3ae3ee86da3dc77a4c995fa7e8ffe778b59bdd969d`。
- 结果证据 manifest：`63f02e369782af47d15de1cd64ca126ac4f26cff8dc2bff7e8643a32027624be`。
- 独立结果收据：`independent-result-review.json`；补充用户事实：`inputs/operator-post-start-click-confirmation.json`。
- 保护复核：`verification/post-case-protected-readback.json`；逐窗口读回：`verification/manual-start-result-readback.json`。

当前候选累计 7 份失败终态，累计工作 CLI 提交仍为 1；本次新增 CLI 0。正例 0/3、负例未通过；T2 仍 BLOCKED，E03 完整门、同候选 E01、当前 8B 的 E02、T3—T5 和 Owner 门保持。完整交付目标仍 active。下一次实际用例须另行分配；本次授权及用户鼠标操作确认均不授予重试。

同步限制：项目与 UltimaDocs 镜像本地记录、提交和 tag 单独保留。此前自动审批以 `blocked by policy` 拦截推送组合命令；只读远端核对显示仍为旧分支头。本次结果没有另行重试推送，GitHub 尚未同步，不能声称云端已交付。此前被拦截的独立导入探针同样未重试；随后这一次获授权的正式入口预检及运行按原流程完成。

独立结果收据 SHA-256：`7b33ed024b766828f108b73430aa86417dbbcc71020c980e732ef14c5d5e2df3`。用户鼠标确认属于 Root 记录的补充证据，不冒充 reviewer 已复核的 46 文件集合。
