# 工单 0015 ASR 纠错系统化阶段报告

> 工单：`wo-ultimaagent-20261101-0015`
> 执行端：Codex（codex exec）
> 日期：2026-11-01
> 状态：收口中（T3-C1/C2 本地冻结完成；push 待执行）

## 范围与边界

- 写域：`src/brain/voice/asr.py`、`src/brain/interaction.py`、`config/asr-normalize.json`、本单测试、本文与 `docs/reports/evidence/asr-correction/`。
- 保持不动：ASR 模型、faster-whisper 推理参数、采样链路、daemon 主链、`_FUZZY_*` 关键词与判定结构、sherpa 备用链、voice profile、KWS 基线、UI。
- 工程验收解释器：`tools/venv-openjarvis/Scripts/python.exe`，实测 Python 3.13.16。

## Gate 记录

### T0 环境盘点 — PASS

- C1 PASS：确认 faster-whisper 调用为 CUDA/float16、`language="zh"`、`beam_size=5`、`condition_on_previous_text=False`；旧 `initial_prompt` 仅含任务管理词。
- C2 PASS：确认 `_normalize_utterance` 内硬编码 4 条近音映射；`_FUZZY_*` 兜底结构只读保留。
- C3 PASS：固定文本注入复现“水量天听”已修正、“水天”未覆盖、“水田”不误伤；定位 21:07/22:14 两条真机 WAV 与日志。
- C4 PASS：证据见 `docs/reports/evidence/asr-correction/t0-env-probe.txt`。
- 音频冷启动附注：旧 prompt 的 fresh faster-whisper 尝试因 `mkl_malloc` 内存分配失败，没有产出转写；该失败保留为事实，不计作 T1 对比结果。

### T1 initial_prompt 扩充 — PASS

- 高频主题扩充为天气、今天、明天、几点、时间、温度、风、雨、雪、上海、日程、任务、进度，并保留原任务管理词。
- prompt 从 43 字增至 88 字；未修改模型、device/compute_type、language、beam_size 或 previous-text 参数。
- 两条固定真机 WAV 的 fresh faster-whisper 天气关键词正确率为 `1/2 (50%) -> 1/2 (50%)`，持平不恶化；T2 可兜底样本 A 的历史真机“水量天听”转写，但 fresh 的“聊天镜”未登记、仍未解决。
- 证据：`docs/reports/evidence/asr-correction/t1-prompt.txt`。

### T2 近音映射独立化与扩充 — PASS

- 新建 `config/asr-normalize.json`，5 条均登记来源与验证状态，禁止单字映射。
- 缺文件/坏 JSON/坏 schema 回退内置默认 4 条，不报错断链。
- 两个指定近音样例均归一化后进入 `reason=天气查询`；“水田”与“水天一色”不误伤。
- 与 0016 兼容：孤立“水量天听”仍 ABSTAIN；仅有明确天气上下文的已登记纠错进入确定性天气路径。
- 专项：`30 passed in 4.83s`。
- 证据：`docs/reports/evidence/asr-correction/t2-normalize.txt`。

### T3 收口 — C1/C2 PASS，C3 push 待执行

- Fresh 全量命令：`tools/venv-openjarvis/Scripts/python.exe -m pytest src -q`。
- fresh-context review 修复后的最终完整运行：`858 passed, 36 warnings, 120 subtests passed in 178.25s`。
- 0017 首次阻塞用例 `test_agent_server_keeps_user_question_separate` 已随主线提交 `5ef3ec3` 修复，本轮全量通过。
- 本次收口前两次完整运行均为 `1 failed, 851 passed, 120 subtests`，唯一失败是既有 memory 测试 `TestPreferenceStore.test_upsert_idempotent`：两次紧邻写入落在同一毫秒。独立复现 10 次为 8 pass / 2 fail；未修改外域 memory 代码。第三次审查前完整 fresh 为 852 passed，审查修复后的最终完整 fresh 为 858 passed；过程均在 `t3/gate.txt` 如实登记。
- 0015 专项初次复核为 `11 passed`；fresh review 发现带查询词的“水天一色”误伤后，新增 6 个负向断言，实测 `6 failed` 后最小修复为 `17 passed`。
- 0015 专项 + 0016 兼容/交互最终合并回归：`36 passed in 9.01s`。
- 近音行为：带天气上下文的“查一下明天的水量天听”“明天上海的水天”进入确定性天气路径；孤立“水量天听”保持 ABSTAIN；“水田”“水天一色”以及带“看/问/今天”的成语句不变、不触发天气。
- 证据：`docs/reports/evidence/asr-correction/t3/full-pytest.txt` 与 `t3/gate.txt`。
- 本地冻结：commit `c0f0c7bb4d35b4a26fe0935e21ba97c1a450eb07`（`工单 0015 ASR 纠错系统化`）；tag `ultimaagent-asr-correction-20261101` 独立解析到同一 commit。
- push：待以免代理命令推送 main 与 tag，结果随后回填。

### T4 八字段回执 — 本地冻结完成，push 待回填

- 回执文件：`docs/reports/evidence/asr-correction/t4-receipt.txt`。
- 当前回执已记录实际 commit/tag，但不提前宣称 push 成功；推送后按实际结果回填。网络失败时以 `t3-push-blocker.txt` 为阻塞证据，不回滚或重写本地提交。

## 扩充前后对比

固定真实 WAV fresh 对比为 `1/2 (50%) -> 1/2 (50%)`，持平不恶化；详见 `t1-prompt.txt`。不把首次内存失败或历史真机日志冒充新 prompt 结果。T2 仅兜底历史“水量天听”误识，不宣称覆盖 fresh 的“聊天镜”。

## 映射表来源登记

| from | to | 来源 | 状态 |
|---|---|---|---|
| 水量天听 | 天气 | 21:07 final，voice-listen.log:3933 | 真机观测 |
| 水平听听清 | 天气 | 21:07 intermediate，voice-listen.log:3930 | 真机观测 |
| 水平听 | 天气 | 既有内置表迁移 | 离线回归 |
| 明天上海的这 | 明天上海的天气 | 22:14 中间观测迁移 | 离线回归 |
| 水天 | 天气 | 工单 0015 Owner 观测 | 离线注入；天气上下文限定 |
