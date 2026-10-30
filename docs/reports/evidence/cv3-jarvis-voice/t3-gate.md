# T3 Gate 证据

- 命令：`tools/venv-openjarvis/Scripts/python.exe -m pytest src/brain/tests/test_voice_voice.py -q --disable-warnings`
- 最终结果：`37 passed in 0.70s`；JUnit XML 独立读回 `37 tests / 0 failures / 0 errors / 0 skipped`。
- 要求：≥8 passed；实际：37 passed。
- 测试边界：仅 mock 与临时 profile/音频占位文件，不真实加载 CV3 权重，不调用 edge-tts。
