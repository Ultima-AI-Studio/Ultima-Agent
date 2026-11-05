# E03 持续操作提示准备完成

原工单 `wo-ultimaagent-20261101-0021`，当前仍在 T2。产品候选 `7975e477665c02820fa235b73d203718bd33b2c9`，仅当前 `qwen3-8b-uncensored`；E01—E08 和后续 T3—T5、Owner 交付目标保持。

本轮完成的是测试提示修订及独立准备审查，没有新增实际用例。上一轮显式开始成功，随后副窗口光标改变，案例在 CLI 提交前 FAIL；用户确认点击过其他位置。该次用例和独立结果复核均已耗尽，当前正例 0/3、负例未通过，T2 仍 BLOCKED。

开始按钮改为“开始测试（结束前请勿点击、输入或切换窗口）”。两个原有测试窗口都增加持续提示“测试期间请勿点击、输入或切换窗口，等待结束通知。”，在开始按钮消失后仍保留。提示位于原文和按钮下方；窗口高度从 280 增至 320，原文控件、按钮区域、窗口标题、位置、宽度及产品目标策略保持。

提示使用非交互的 STATIC 子控件。微软文档规定新子窗口默认位于同级窗口 Z 顺序底部，因此提示与按钮采用不同显示区域，避免依赖相互覆盖；新增提示使用独立子控件 ID1002。[CreateWindowExW](https://learn.microsoft.com/en-us/windows/win32/api/winuser/nf-winuser-createwindowexw)、[Static Control Styles](https://learn.microsoft.com/en-us/windows/win32/controls/static-control-styles)。

代码差异只有三个文件：`fixture_adapter.py` 增加提示和垂直空间，`fixture_manual_start.py` 更新按钮文字，现有测试模拟区分顶层窗口与子提示。124 项原有离线回归全部通过（6.91 秒）；14 模块 AST、41 源码、7 依赖及 1346 SDK 文件哈希核对通过，两个固定候选工作树无 tracked 变化。原焦点、选区、副窗口、审计、清理、事实与时限门没有放宽，没有重置光标或屏蔽用户输入。

独立准备审查 PASS，没有 Critical/Important/Minor 发现。Reviewer 独立核对 31 项封存文件、准确差异、14 模块 AST、41 源码及 7 依赖；测试结果来自本轮日志，SDK 全量哈希和运行进程状态由 Root 另行核对。7 个保护身份匹配，官方语音 ready/fresh。真实显示、字体/DPI 和后续产品行为尚未现场验证。

证据目录：`data/evidence/jarvis-work-capability/T2/e03-source12-input-guidance-20261105-r3/`。
准备 manifest：`0195699e7fe521d9aaa5da8ec01bedb53533cdc3a2364ea42496f142f6d07352`。
核心证据：`provenance.json`、`verification/guidance.diff`、`verification/guidance-final-tests.log`、`verification/static-readback.json`、`independent-preparation-review.json`。

下一例提案已具体准备：相同 8B、相同三条事实、一次 E03 round1，随后一次独立产出复核，失败不重试。点击开始后同时暂停鼠标、键盘和窗口切换，直到结束通知。新实际额度尚未授予；准备审查、旧授权和鼠标操作确认都不能代替新单例授权。

本轮按原工单完成项目和 UltimaDocs 本地镜像、提交和 tag 检查点，实际提交记录见包内 `verification/local-checkpoint.json`。远端同步仍受此前自动审批拒绝影响；被拒动作仅返回 `blocked by policy`，推送和独立导入探针均未重试，本轮未声称 GitHub 已同步。旧失败和保护边界完整保留。

独立准备审查收据 SHA-256：`d9cff9cdfddebadcde427de48374554b7a29413c1107878f4d2bed604186d013`。
