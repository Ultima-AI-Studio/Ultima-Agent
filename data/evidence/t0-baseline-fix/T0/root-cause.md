# T0 四项 RED 复现与根因结论

- 工单：`wo-ultimaagent-20261103-0025`
- run_id：`20261104T023556251345Z`
- 执行端：Codex CLI / GPT-5.6-sol
- 解释器：`tools/venv-openjarvis/Scripts/python.exe`，Python 3.13.16
- 隔离：每项使用 `data/evidence/t0-baseline-fix/T0/<case>/tmp` 与独立 pytest cache；未读写麦克风、未播放音频、未停止或重启现有进程。

## 1. agent_server 用户问题边界

- RED：退出码 1，`1 failed in 81.91s`。
- 现场：`Jarvis.ask_full` 实收 `[当前时间：YYYY-MM-DD HH:MM 星期X（北京时间）] 第一问`，旧断言要求严格等于 `第一问`。
- 根因：0020 已确认的时间上下文注入是现行行为；事件总线仍记录裸用户问题，模型输入将时间事实与原问题以单个空格显式分隔。旧测试把“用户问题不被系统 prompt 拼接”误写成“模型输入不得带任何有界上下文”。
- 归因：**断言更新**（行为确认后对齐）；不改 `agent_server` 生产行为。
- 证据：`01-agent-question-separate/pytest.log`、`01-agent-question-separate/junit.xml`。

## 2. 确定性时间直答

- RED：退出码 1，`1 failed in 0.58s`。
- 现场：当前北京时间 10 点调用 `_cn_hour(10)`，代码对长度 10 的 `_CN_DIGITS` 取索引 10，抛出 `IndexError`；即使避开 10 点，旧测试仍错误要求 `reason == "Agent 回答"` 且 Agent 被调用。
- 根因：0020 的现行基线是本地确定性时间直答，不应进入 Agent；同时小时中文格式器存在 10 点边界错误，导致该能力在 10:xx 真实不可用。
- 归因：**行为确认**（保留并修复确定性直答，断言随之更新）；不得回退到 Agent 自由回答。
- 证据：`02-time-intent/pytest.log`、`02-time-intent/junit.xml`。

## 3. 生产队列只读投影

- RED：退出码 1，`1 failed in 0.70s`。
- 现场：`tasks/tasks.json` 可按 UTF-8/JSON 直接读取，SHA256 前后不变；`read_queue_status` fail-closed 为 `card_path 越出任务卡目录`。
- 根因：reader 只接受 `tasks/cards/<task_id>/task.md`，但生产索引合法包含 `tasks/queue/*.md` 和 `tasks/queue/stages/.../*.md`；另一个 repo-relative `tasks/queue/...` 被错误地相对 `tasks/` 拼成 `tasks/tasks/queue/...`。这是 reader 与生产索引布局不兼容，不是文件权限或 JSON 损坏。
- 归因：**行为确认**（生产索引布局为输入事实，修只读 reader）；禁止修改 `tasks/tasks.json` 来绕过测试，继续以哈希证明不变异。
- 证据：`03-queue-source/pytest.log`、`03-queue-source/junit.xml`。

## 4. voice-next discontinuity reset

- RED：退出码 1，`1 failed in 0.36s`。
- 现场：`Resident.reset_audio()` 在创建真实 `soxr.ResampleStream` 时抛 `ModuleNotFoundError: soxr`，尚未进入 framers/model cache 断言。
- 根因：voice-next 的既有依赖锁已含 `soxr==1.1.0`，隔离 `tools/venv-voice-next` 也已安装；完整工程门指定的 `tools/venv-openjarvis` 环境缺少该既有锁定依赖。
- 归因：**环境依赖**；按既有 lock 同步 `soxr==1.1.0`，不改 KWS、采样率、阈值、增益、唤醒词或 daemon。
- 证据：`04-discontinuity-reset/pytest.log`、`04-discontinuity-reset/junit.xml`、`open-source-alternatives.md`。

