# UltimaAgent T2：R31 结果、输入诊断准备与验收归属纠正

日期：2026-11-05；原工单：`wo-ultimaagent-20261101-0021`。

**T2 未通过。R31 已失败并耗尽单例额度；本次完成的是只读证据核对与离线诊断代码准备，没有新增产品用例或模型调用。** 当前候选为 `7975e477665c02820fa235b73d203718bd33b2c9`，继续仅使用当前 `qwen3-8b-uncensored`，不切换 14B 或其他权重。

| 核对项 | 当前结论 |
|---|---|
| R31 实跑 | `FAIL / Frozen fixture mismatch`，在隔离 server/CLI 启动前停止 |
| R31 产品证据 | `work_cli_count=0`，`product_result_sha256=null`，无验收分 |
| R31 清理与保护边界 | cleanup PASS；boundaries PASS |
| 文本变化 | 初始 41 UTF-16 单元，冻结基线为空；同一控件收到一次记录为 `EM_REPLACESEL` 的 41→0 变化 |
| 输入来源 | **UNCONFIRMED**；用户无法确认当时是否输入，日志也不能确定发送者 |
| 当前候选 E03 | 复核到 5 份独立绑定的终态，均失败；1 次 CLI 提交；已核实正例通过 0，负例通过 0 |
| 本次离线验证 | 36 项针对性测试通过；没有运行真实 Windows 夹具或模型 |
| 运行保护 | 7 个受保护进程身份匹配；官方 voice-next 状态 ready、fresh，监听实例与 worker 身份匹配 |

R31 的 334 个封存对象和当前候选的 41 个源码文件均已重新核对哈希。其单例执行、旧终态与封存包保持不变。`verification/r31-readback.json` 记录原始证据路径及哈希，`verification/protected-readback.json` 记录本次运行身份读回；没有保存命令行明文或语音转写。

原审计中的 `programmatic` 是按消息编号分类，不能证明“外部程序修改”；`received_at_utc/qpc_ns` 在原窗口过程返回后采样，也不能当作消息入口时间。14 条键盘/IME 记录与文本变化共存，只能说明需要补充消息嵌套和来源枚举观察。Win32 来源枚举也不等于发送进程身份，硬件来源值还包括 UIAccess 注入。依据：[GetCurrentInputMessageSource](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-getcurrentinputmessagesource)、[INPUT_MESSAGE_ORIGIN_ID](https://learn.microsoft.com/en-us/windows/win32/api/winuser/ne-winuser-input_message_origin_id)、[InSendMessageEx](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-insendmessageex)。

本次在独立证据目录中准备了一个观察补丁：在两个自建测试 Edit 控件中，记录消息进入/返回时间、嵌套关系、输入来源枚举和跨线程发送标志；保持原消息参数、返回值和派发行为。补丁不记录按键值、正文、剪贴板或其他窗口内容。controller 要求观察记录完整、两个控件的探针齐全，并与原审计按控件/消息计数一致；不完整即拒绝放行。原产品候选、语音路径、测试文本和 60 秒门均未修改。

36 项测试覆盖顺序、嵌套、未知来源、观察失败、清理、字段限制、Win32 绑定形状和真实 controller 校验函数的拒绝路径。测试使用注入接口及隔离提取的函数，没有创建窗口；这不能证明 Windows 现场问题已解决。保留了各轮 RED/GREEN 输出；没有将历史 R31 的 177 项测试当作本补丁的验证结果。独立审查尚未进行。

验收归属纠正：`e03-source12-20261104-recovery5/actual/e03-round1` 的终态和独立审查文件，与 `e03-source10-20261103-recovery2` 的对应文件字节一致。原 authority 绑定的是 `118ba152b007c30d358c8bc44c51aabe8ae820f0`，不是当前 `7975e477...`。该历史 PASS 保留，但不能作为当前候选的第一轮通过。另一个 11 月 2 日三轮通过门绑定 `244d2120...` / 产品源码 `7c201a3a...`，同样属于历史版本。

当前计数来自 `e03-source12*/actual/*/terminal.json` 的逐案核对，排除了复制的历史目录；这是明确范围内的已核实计数，不是累计所有历史试验的次数。R31 自身被限定为诊断用途，即便通过也不产生验收分。后续正式验收必须从当前候选 E03 round1 起，完成同候选三轮正例与原负例，再做同候选 E01 回归，随后处理 E02；T2 出口未满足前不进入 T3—T5。

任务状态校正保留修改前 `current-run.json` 和工单/阶段记录的完整副本与哈希，旧失败不改写。全局队列中残留的“R30 executing”更新为与任务存储一致的 blocked；项目目标继续有效。状态校正不签发运行权限，也不把文档或测试计作产品验收。

下一步应先独立审查此观察补丁与验收归属纠正，再准备并审查一次有界的**夹具诊断**：复用初始化、置前台及冻结基线读取顺序，采集缺失的来源证据，不启动产品 server、CLI 或模型，不重置文本、不修改输入法设置。当前目录仅为补丁准备，没有该诊断的可执行发布包或新 authority；R31 的 `case_cap=1` 已消费，`retry_authorized=false`。

产出目录：`H:\UltimaAI\UltimaAgent\data\evidence\jarvis-work-capability\T2\e03-fixture-input-origin-20261105`。其中 `design.md`、`code/`、`verification/` 和 `preparation-manifest.json` 用于后续审查；manifest 只封存准备结果，不代表审查通过或执行授权。
