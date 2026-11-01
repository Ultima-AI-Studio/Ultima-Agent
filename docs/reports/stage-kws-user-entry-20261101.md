# UltimaAgent KWS 唤醒词用户入口 + 持久化阶段报告

工单：`wo-ultimaagent-20261101-0014`（第二次派发，Owner 授权方案 B）

执行目录：`H:\UltimaAI\UltimaAgent`

验收解释器：`tools\venv-openjarvis\Scripts\python.exe`（Python 3.13.16）

## 结论

状态：阻塞（实现与验证完成；免代理 push 因外部网络不可达未完成）。

同步等待环已解除：意图层只做非阻塞提交；冻结 CLI 在后台事务线程运行；resident daemon 主线程继续执行既有 `HotReloadSpotter.maybe_reload()`，并把 profile/keywords reload 事件回送事务协调器。成功确认只在“首次 CLI reload → profile 保存并被 watcher 消费 → 二次 CLI reload → 最终读回”全部完成后进入既有 TTS 链。

未杀或重启 daemon。现网 PID 27820 的冻结 CLI 同 PID 热重载探针通过；由于禁止重启，运行中的旧解释器不能加载本次新源码，因此新闭环以 `VoiceInteractionLoop.handle_audio()` 完整路径等价注入验收，真实麦克风上的新代码留待下一次获准 daemon 生命周期验收。

## T0 环境与授权盘点

状态：PASS。

- 保留首次执行的草稿与证据，不 reset、不清理。
- `t1-blocker-review.txt` 保持原样，SHA256 为 `FEF2CB1507371110EFBB563134EED0FE6442C744C7E2EF5EF54B4975AF2A1F51`。
- 只扩大到方案 B 所需的 daemon reload/completion 通知、`VoiceInteractionLoop` 协调器、`InteractionLoop` 非阻塞入口及对应测试。
- `scripts/kws_reconfig.py` 与 `voice_profile.py` 保持只读；音频参数、设备操作、模型/ONNX/tokens、W6/HUD 不在写域。

证据：`evidence/kws-user-entry/t0-rerun-scope-probe.txt`。

## T1 方案 B 实现

状态：PASS。

### 解环结构

1. `InteractionLoop._try_wakeword_change()` 识别明确命令后调用 submitter，并立即返回 `唤醒词修改已提交`，不再同步执行 CLI，也不提前播报成功。
2. `WakewordChangeCoordinator` 在后台线程执行冻结 CLI；daemon 主线程返回 `wait_wakeup()` 后持续调用原有 `maybe_reload()`。
3. `HotReloadSpotter` 在 profile apply 与 keywords rebuild 成功/失败后产生事件；事件包含 PID、mtime 与 custom，防止旧事件误放行。
4. profile watcher 已消费目标 custom 的事件到达后，才允许二次 CLI；因此 watcher 不会在最终 CLI 后重新覆盖精确 `:2.0 #0.08` 行。
5. 事务完成后通过现有 `tts_synthesize()` 生成“唤醒词已改为 XX”或失败话术，daemon 复用既有异步播放链。

### 失败补偿

首次 CLI、profile save/apply、watcher 确认、二次 CLI、最终 profile 读回任一步失败，均恢复旧 custom，等待旧 profile watcher 确认，再用冻结 CLI 做最终收敛。失败只播报“唤醒词修改失败，请稍后再试”，不留下成功假象。

### 歧义拒绝

“唤醒词改成什么”“把唤醒词换成哪个”“把唤醒词改成星期五可以吗”“星期五可以吗”均拒绝提交，并引导“请明确说，把唤醒词改成某个名字”。

### 同 PID 探针

冻结 CLI 对当前既有状态执行 `--replace 贾维斯 星期五`：exit 0，`success=true`，`same_pid=true`，PID 前后均为 27820，StartTime 前后均为 2026-11-01 12:52:55；profile SHA256 前后相同。最终仍为 6 个贾维斯变体 + 星期五 + ULTIMA。

证据：`t1-scheme-b-rerun.txt`、`t1-live-same-pid-probe.txt`；首次阻塞证据 `t1-blocker-review.txt` 归档保留。

## T2 自动化与等价闭环

状态：PASS。

- 0014 专项：`16 passed in 0.46s`。
- voice-profile + reload 专项：`14 passed in 0.76s`。
- 合并 voice 专项：`38 passed in 1.16s`。
- 全量最终 fresh：`852 passed, 36 warnings, 120 subtests passed in 197.95s`，exit 0。
- JUnit：`evidence/kws-user-entry/t2/full-pytest-rerun.xml`，SHA256 `06EB0DFFB770C25514DF9A3E35DCFED1F1DC0327938C8215ED34EECDBE86C1A5`。

完整路径测试从 `VoiceInteractionLoop.handle_audio()` 注入“把唤醒词改成星期五”，覆盖 InteractionLoop 提交、两次 CLI 回执、profile 持久化/readback、watcher 交错、最终一致、成功 TTS；并分别注入首次 CLI、profile save、二次 CLI 与 watcher timeout 故障，验证补偿与失败播报。

前两次全量运行分别遇到共享工作树中的 mainbrain 并行变化和 PreferenceStore 毫秒时间戳碰撞；失败节点均 fresh 复核通过，本单未改旁路模块。最终完整 fresh 运行全绿，作为正式 Gate。

证据：`evidence/kws-user-entry/t2/rerun-verification-summary.txt`。

## T3 冻结与边界

状态：BLOCKED（冻结与本地 Git Gate PASS；远端 push Gate BLOCKED）。

- 冻结基线 SHA256 仍为 `3EC3C892C43BB18ED1A0AE07FAFD0817FE72D3C774224FF77258C7AB5E9F30EE`；本单未修改或暂存该文件。
- runtime 数值保持：SR 44100、SR_KWS 16000、DEV_IN 1、DEV_OUT 5、QUIET_AFTER_SPEECH 1.2、ENERGY_TH 0.008、score 2.0、threshold 0.08、trailing blanks 8。
- daemon PID 27820 未被杀或重启。
- 模型、ONNX、tokens、音频设备/音量/增益、W6/HUD 均未改。
- 本地 commit 与 tag 已创建并可解析，但三次免代理连通检查均失败：两次 Git 直连 `github.com:443` 约 21 秒超时，`Test-NetConnection github.com:443=False`。
- 新阻塞根因是执行环境没有到 GitHub 443 的直接 TCP 连通性；需恢复直连后重派 push，或由 Owner 明确授权使用代理（偏离本单“免代理推送”冻结要求）。

证据：`evidence/kws-user-entry/t3-rerun-baseline-review.txt`、`evidence/kws-user-entry/t3-push-blocker.txt`。

## 真机验收边界

已实测当前 daemon 的同 PID 热重载；已用等价注入完整覆盖新代码的“改词 → reload 确认 → profile watcher → 二次 reload → TTS → 持久化”闭环。因本次明确禁止重启 daemon，PID 27820 仍运行启动时加载的旧 Python 模块，无法在不重启/不注入进程的前提下执行新 callback 源码。因此真实麦克风上的新实现声明为“下一次获准 daemon 生命周期待验收”，不把同 PID CLI 探针冒充新语音入口真机验收。

## T4 八字段回执

| 字段 | 值 |
|---|---|
| 链路号/工单号 | wo-ultimaagent-20261101-0014 |
| 执行端 | Codex（coding executor） |
| 完成状态 | 阻塞 |
| 根因结论 | 代码根因已由方案 B 解环；收口新阻塞为执行环境无法直连 github.com:443，免代理 push 未完成。 |
| 产出路径 | `src/brain/interaction.py`、`src/brain/voice_loop.py`、`data/logs/voice-listen-daemon.py`、`src/brain/tests/test_kws_user_entry.py`、本报告及 evidence |
| 验收证据 | T0/T1/T2 与 T3 本地 Gate PASS；0014=16 passed；voice-profile/reload=14 passed；全量=852 passed；PID 27820 same-PID reload success；T3 push blocker 见证据 |
| 越界声明 | 无；未改 CLI/voice_profile 实现、音频参数/设备、KWS 模型/ONNX/tokens、W6/HUD，未杀/重启 daemon |
| 环境声明 | 当前 daemon 同 PID 热重载实测；新代码以完整路径等价注入验收，真实麦克风待下一次获准 daemon 生命周期验收 |

授权请求：请恢复到 `github.com:443` 的直接网络后重派 push，或明确授权使用代理完成推送。
