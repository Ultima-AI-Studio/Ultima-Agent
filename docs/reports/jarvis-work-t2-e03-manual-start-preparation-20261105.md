# E03 显式开始交接准备

> 后续状态：本准备包已获新单例授权并运行一次，结果为 FAIL（副窗口光标变化、CLI 0），独立证据复核已完成，两项额度均耗尽。以下为准备阶段历史记录；当前结果见 `jarvis-work-t2-e03-manual-start-result-20261105.md`。

原工单 `wo-ultimaagent-20261101-0021`，当前阶段 T2。这是测试入口修订 r2，不是 E03 round2。当前产品候选仍为 `7975e477665c02820fa235b73d203718bd33b2c9`，模型仅使用现有 `qwen3-8b-uncensored`。

当前状态：离线修复已完成，准备包已封存，独立准备审查 PASS（无阻塞项）；没有新增实际用例或执行额度。E03 当前候选仍为正例 0/3、负例未通过，T2 仍 BLOCKED，完整 E01—E08 交付目标继续有效。

用户确认上次北京时间 20:19:45 测试激活时正在输入。原夹具曾连接前台输入线程，再把焦点转到已全选的样本中；该次前台线程对应持续存活的豆包进程。这证实交接时存在并发输入，但不能确定清空文本的 EM_REPLACESEL 发送者，也不能解释所有历史失败。上次案例仍是 FAIL、产品 CLI 0、没有 rewrite.md；一次实际运行和一次结果复核额度均已耗尽。

本次改动仅位于隔离验收包：两个测试窗口以不自动激活的方式显示，主窗口提供“开始测试”按钮；收到本窗口按钮通知且按键已释放后，才以普通 Windows 接口申请前台、核对焦点并选择原样本。移除了 AttachThreadInput。等待最多 15 秒，仍在原 20 秒夹具启动限制内；超时、停止、按键未释放或激活失败均在产品提交前结束。后续焦点离开自有测试窗口时不重新抢占。

准备验证：124 项离线测试通过（原 99 项加 25 项新回归）；14 个模块 AST 解析通过；41 个候选源码、7 个依赖和 1346 个 SDK 文件静态哈希匹配；两个固定候选工作树 tracked clean。真实鼠标点击和 Windows 前台权限尚未现场验证。保护快照显示 7/7 身份匹配，官方语音 ready/fresh；本轮未重启保护进程，未调用产品、模型或音频。

自动审批曾拦截“写入说明并执行导入探针”的组合命令，仅返回 `blocked by policy`。该命令未执行，导入探针未重试；本次绑定检查限于静态 AST、哈希和源码检查。复制的旧导入回执仅作历史证据。

准备包：`data/evidence/jarvis-work-capability/T2/e03-source12-manual-start-20261105-r2/`。
Manifest SHA-256：`a720ad4f77d56689321da3fb9cfbae557890f22607260b1e621b0819c7aec5a3`，54 项封存文件。
主要证据：`plan.md`、`provenance.json`、`verification/manual-start.diff`、`verification/green-final-manual-start.log`、`verification/static-readback.json`、`inputs/operator-concurrent-input-confirmation.json`。

下一步提案已写入 `verification/next-case-proposal.md`：准备包独审通过后，以新的单次授权运行一例当前 8B 的 E03 round1，并对这一次产出做一次只读独立复核。执行时由用户点击开始并暂停键盘输入，失败不重试。原 60 秒凭据新鲜度、120 秒准入和 300/1800/315 秒产品时限保持；之后仍按当前候选 E03 三轮与负例、同候选 E01、8B 的 E02、T3—T5 和 Owner 门推进。

本次参考的官方接口说明：[AttachThreadInput](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-attachthreadinput)、[SetForegroundWindow](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-setforegroundwindow)、[Extended Window Styles](https://learn.microsoft.com/en-us/windows/win32/winmsg/extended-window-styles)。API 文档支持交接方式选择，不构成现场验证。

独立准备审查回执：`independent-preparation-review.json`，SHA-256 `ab03cd2114ce3350c9cfbadcbbb4ae9a6f37d0cc7898cc33af305c6941c20ffd`。Reviewer 单独核对 54 项封存文件、14 模块 AST、41 项源码和 7 项依赖，以及真实字节差异和 RED/GREEN 日志；没有执行测试或 UI。1346 个 SDK 文件和当前保护/语音状态由 Root 的只读收据核对，未宣称 reviewer 也做了现场检查。

准备交付已形成项目与镜像检查点；提交、tag 和远端核对的实际结果以本包 `verification/sync-receipt.json` 为准。真实运行及事实验收仍待下一次单例授权。

同步异常：项目准备提交 `86c322ae399441308a8c79fdbb4ffee947e9813d`、镜像准备提交 `f8b7a8c4646fb2d121705ff2cbbb14fb7a918988` 及两仓本地 tag `ultimaagent-t2-e03-manual-start-20261105` 已完成。自动审批以 `blocked by policy` 拒绝推送与远端核对组合命令，命令未执行，未重试推送。随后只读 ls-remote 确认远端仍为之前的项目 `e06a1e8a`、镜像 `bb5e55e1`，没有新 tag；不能声称 GitHub 已同步。详见 `verification/sync-receipt.json`。
