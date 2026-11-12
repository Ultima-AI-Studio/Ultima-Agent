# s3-watchdog 验收证据（M22 看门狗）

- 工单：s3-watchdog（看门狗与循环防护）
- 执行通道：主脑直接补做（Codex 派发通道网络层死路：chatgpt.com 直连 403 / 走代理 SSL 失败，workspace routing discovery 无法完成）
- 实现：`scripts\watchdog-loopguard.py`（单文件独立进程，pythonw 零弹窗）
- 验收时间：2026-10-27

## 结论

| ACCEPT | 判定 | 证据 |
|---|---|---|
| ACCEPT-1 | PASS | selftest 五项判定全部命中（repeat_call / pingpong / poll_budget / turn_timeout / stream_idle = true） |
| ACCEPT-2 | PASS | 8756 无监听 → watchdog 自动拉起 agent_server（PID 22712，health ok，model=qwen2.5:14b，agent=native_react，tools=9） |
| ACCEPT-3 | PASS | 连续 3 次拉起失败 → 事件 agent_start_stopped(fail_count=3, cooldown_sec=300)，日志"停止本轮重试，冷却300秒"，不无限循环 |
| ACCEPT-4 | PASS | 构造 5 分钟窗口 3 条 error → fuse_triggered + fuse_rollback_dryrun（回滚命令构造正确，dry-run 不改真实总线） |
| ACCEPT-5 | PASS | 守护进程独立（watchdog PID 10920 独立于 agent_server PID 22712） |
| ACCEPT-6 | PASS | 计划任务已注册（UltimaAgent-Watchdog，At logon time，Interactive only，Run As Administrator）；运行期 pythonw 窗口句柄全部为 0（零弹窗） |
| ACCEPT-7 | PASS | watchdog.log 与 watchdog-events.jsonl 留痕完整：watchdog_started / agent_start_attempt / agent_started / agent_start_stopped / fuse_triggered / fuse_rollback_dryrun / autostart_installed / watchdog_selftest |
| ACCEPT-8 | PASS | 本报告 + receipt.json 落盘并回读 |

## ACCEPT-1 证据（构造用例自测）

命令：`python scripts\watchdog-loopguard.py --selftest`

```
selftest: repeat_call=true pingpong=true poll_budget=true turn_timeout=true stream_idle=true  pass=true
```

五项规则：
- 重复调用：窗口 10 秒内同 key 两次 call_start → repeat_call
- 乒乓：A/B 交替 ≥6 次且仅两个唯一值 → pingpong
- 轮询预算：60 秒内 poll 超过 50 次 → poll_budget
- 回合超时：turn_start 后任意事件到来已超 300 秒 → turn_timeout（即时判定，不等 turn_end）
- 流式空闲：turn 内 stream_chunk 间隔超 30 秒 → stream_idle

修正记录：首轮 selftest 2 项未命中（pingpong 首尾相等判定错误、turn_timeout 只查 turn_end），修正后 5/5 通过。

## ACCEPT-2 证据（真实拉起）

- 启动前：8756 无监听
- watchdog 启动后 5 秒内：日志"agent_server 不健康，尝试拉起" + 事件 agent_start_attempt
- 50 秒后回读：8756 监听 PID=22712；GET /health → model=qwen2.5:14b agent=native_react tools=9

## ACCEPT-3 证据（连续失败停止）

测试钩子：`--launch-script data\test-tmp\watchdog-fail-launch.ps1`（故意 exit 1）+ `--health-url http://127.0.0.1:9/health`（假端点，不碰真实服务）

事件流三次 agent_start_attempt 后：
```
{"event_type":"agent_start_stopped","payload":{"fail_count":3,"cooldown_sec":300}}
日志：ERROR 连续3次拉起失败，停止本轮重试，冷却300秒
```

## ACCEPT-4 证据（总线熔断联动）

测试钩子：`--bus-log data\test-tmp\fuse-test-bus.jsonl`（构造 5 分钟内 3 条 execution.error）+ `--dry-rollback`

```
{"event_type":"fuse_triggered","payload":{"module_id":"ultima.intent.rule","error_count":3,"window_sec":300}}
{"event_type":"fuse_rollback_dryrun","payload":{"module_id":"ultima.intent.rule","would_exec":"python -m ultima_bus bus rollback ultima.intent.rule"}}
```

生产态熔断行为：统计 `logs\plugin-bus.jsonl` 内三模块（ultima.intent.rule / ultima.domain.skill / ultima.memory.lite）5 分钟窗口 error 事件 ≥3 次 → 执行 `python -m ultima_bus bus rollback <module_id>`，事件 fuse_rollback_exec 留痕。验收用 dry-run 防改真实总线状态。

## ACCEPT-5 证据（独立进程）

watchdog（pythonw PID 10920）与 agent_server（PID 22712）为两个独立进程；watchdog 停止不影响 agent_server，agent_server 崩溃由 watchdog 拉起。

## ACCEPT-6 证据（自启注册与零弹窗）

- `python scripts\watchdog-loopguard.py --install` → 事件 autostart_installed
- schtasks 回读：TaskName=\UltimaAgent-Watchdog，Status=Ready，Schedule Type=At logon time，Logon Mode=Interactive only，Run As User=Administrator
- 窗口枚举：运行中 pythonw 进程 MainWindowHandle 全部为 0（无可见窗口，满足零弹窗纪律）

## 关键参数（冻结基线）

| 参数 | 值 | 说明 |
|---|---|---|
| CHECK_INTERVAL | 20 s | 守护检查间隔 |
| LAUNCH_FAIL_LIMIT | 3 | 连续拉起失败停止阈值 |
| LAUNCH_COOLDOWN | 300 s | 停止后冷却，冷却结束允许下一轮 |
| FUSE_WINDOW | 300 s | 熔断统计窗口（5 分钟） |
| FUSE_ERROR_LIMIT | 3 | 窗口内 error 次数阈值 |
| REPEAT_WINDOW / LIMIT | 10 s / 2 次 | 重复调用判定 |
| PINGPONG_MIN | 6 | 乒乓交替次数阈值 |
| POLL_BUDGET / WINDOW | 50 次 / 60 s | 轮询预算 |
| TURN_TIMEOUT | 300 s | 单回合超时 |
| STREAM_IDLE | 30 s | 流式空闲超时 |

## 产出文件

- `scripts\watchdog-loopguard.py`（主交付，含测试钩子 --launch-script / --bus-log / --dry-rollback / --loop-events / --health-url / --selftest / --install / --uninstall）
- `data\logs\watchdog.log`（滚动日志）
- `data\logs\watchdog-events.jsonl`（结构化事件留痕）
- `data\test-tmp\watchdog-fail-launch.ps1`（ACCEPT-3 证据，可保留）
- `data\test-tmp\fuse-test-bus.jsonl`（ACCEPT-4 证据，可保留）
- 循环事件流输入契约：`data\logs\loop-events.jsonl`（业务侧写入 call_start / call_end / poll / turn_start / turn_end / stream_chunk，watchdog 增量读并判定）

## 边界（未触碰）

- 未修改语音 daemon 与悬浮球进程管理；
- 未引入第三方守护软件；
- 未改动既有总线/意图/记忆插件代码；
- 回滚联动在生产态仅在熔断条件满足时执行，验收过程全程 dry-run。
