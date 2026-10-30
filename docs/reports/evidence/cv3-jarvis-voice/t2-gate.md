# T2 Gate 证据

- RED：优先链测试首次运行 5 failed；明确捕获旧行为先调用 edge 以及缺失冷启动 helper。
- GREEN：优先链、edge 禁用及结果序列化测试完成后，累计 `20 passed`。
- 真实命令：`tools/venv-openjarvis/Scripts/python.exe` 调用 `tts_synthesize('本地优先链路验证。', ...)`。
- 真实结果：`engine=cv3`、`daemon=true`、`device=cuda`、`seconds=7.2`、`rate=24000`、`attempt=1`。
- 音频统计：原始 RMS 0.0338，无增益、无 padding、无削顶。
- 隐私：默认 profile 为 cv3；真实调用未进入 edge-tts。

