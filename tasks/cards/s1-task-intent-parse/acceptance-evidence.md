# 验收证据

## 失败测试

- 命令：`H:\UltimaAI\UltimaAgent\tools\python31313\python.exe -X utf8 src\brain\tests\test_intent.py -v`
- 预期失败：`ModuleNotFoundError: No module named 'src.brain.intent'`，见 `logs/intent-parse-test-2026-10-21-failing.txt`。

## 开发自检通过

- 同命令最终结果：`Ran 3 tests`，`OK`，见 `logs/intent-parse-test-2026-10-21.md`。
- 正例：16/16，识别率 100%，包含礼貌问法、中文标点、显式请求和限定的隐含状态问法。
- 负例：12/12 保持静默，包含空输入、普通陈述、明确否定、引用命令和条件讨论。
- 命中结果固定 `scope=all`；未命中结果 `should_interrupt=false`。

判定：开发自检通过；独立 W4 尚未执行。

## W4 修复证据追加

- RED：`logs/text-loop-w4-repair-20261021/red-intent-v2.txt`、`logs/text-loop-w4-repair-20261021/red-no-read-v2.txt`。
- GREEN：`logs/text-loop-w4-repair-20261021/green-intent.txt`、`logs/text-loop-w4-repair-20261021/green-no-read.txt`。
- 全套与独立脚本复跑：`logs/text-loop-w4-repair-20261021/green-text-suite.txt`、`logs/text-loop-w4-repair-20261021/independent-review-rerun/independent-results.json`。
- 独立签署状态：`independent_w4_completed=false`。


## W4 独立技术验收收口（2026-10-21）

两项独立发现修正后通过：文本16/16、原独立检查49/49、额外正例95%；以 docs/reports/evidence/w4-independent-20261021/round2-correction/result-final.json 为最终裁决。本卡对应执行单元已独立验收；前文开发/修复待审记录作为历史保留。Owner尚未批准v0.3版本冻结，无v0.3-frozen；不启动后续工单。
