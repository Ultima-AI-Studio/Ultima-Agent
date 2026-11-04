# T1 逐项修复说明

- 工单：`wo-ultimaagent-20261103-0025`
- run_id：`20261104T023556251345Z`
- 定点 GREEN：`11 passed in 9.35s`，退出码 0。
- 累计回归：`32 passed, 2 subtests passed in 9.63s`，退出码 0。

## 1. agent_server 用户问题边界

- 归因：断言更新。
- 变更：测试不再错误要求模型输入严格等于裸问题；改为严格验证一个格式化北京时间前缀、一个分隔空格、原问题完整后缀，同时验证 `message_in` 事件仍只包含裸用户问题。
- 生产代码：未改。
- RED：原节点退出 1，时间前缀与旧等值断言冲突。
- GREEN：点名节点通过；若前缀格式漂移、问题被改写/拼接，或事件泄漏前缀，测试会失败。

## 2. 确定性时间直答

- 归因：行为确认。
- 变更：修正 `_cn_hour(10)` 的越界条件；旧路由断言改为要求 `reason == "时间查询"`、答案为本地直答且 Agent/Verifier 均不调用；补 1/9/10/11/12 小时边界表。
- 生产默认：仍走 0020 已确认的确定性时间直答，未退回 Agent，未改模型或推理参数。
- RED：预实现门中命名节点和 10 点边界均为 `IndexError`。
- GREEN：命名节点及 5 个小时边界全部通过。

## 3. 生产队列只读投影

- 归因：行为确认。
- 变更：只读 reader 将 `tasks/...` repo-relative 路径相对任务库父目录解析，其他相对路径仍相对任务库；合法边界从单一 `tasks/cards` 扩为整个 `tasks` 任务库；标题先读既有 `- **标题**:`，否则兼容工单卡 H1。库外路径继续 fail-closed。
- 生产数据：`tasks/tasks.json` 未修改，T0 与 T1 后 SHA256 均为 `4FFDF9AD06FFE55B5E47FC8E9410C0F6BB18B77BA43308DAC59D09068E167CE1`。
- RED：生产节点为 `card_path 越出任务卡目录`；新增 queue/stage 卡契约亦失败。
- GREEN：生产库 `ok=True, total=46`；`voice-136-pseudo-streaming` 仍为 `QUEUED` 且 `terminal_reason=None`；库外路径拒绝测试通过。

## 4. voice-next discontinuity reset

- 归因：环境依赖。
- 变更：不改 `live.py` 或测试 fake；把现有 lock 的 `soxr==1.1.0` 同步到完整门专用 `tools/venv-openjarvis`。前两次 uv 离线解析均退出 1 且未改环境；根因是 registry 离线索引不提供已解包 cache 版本。随后按既有 bootstrap 的官方 PyPI 路径精确安装，退出 0；import readback 为 soxr 1.1.0 / libsoxr 0.1.3-14-ga66f3ee。
- 生产默认：未改 KWS/唤醒词/阈值/采样率/增益；未启动 voice-next；未打开麦克风或播放；未停止/重启 daemon。
- RED：`ModuleNotFoundError: No module named 'soxr'`。
- GREEN：真实 `soxr.ResampleStream` 被创建两次，spotter reset 两次，framers pending 清空且 generation 对齐断言通过。

