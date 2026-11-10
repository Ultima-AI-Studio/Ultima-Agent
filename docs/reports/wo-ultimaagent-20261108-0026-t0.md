# 工单 0026 审计加固 T0 阶段报告

- 工单：`wo-ultimaagent-20261108-0026`
- 阶段：T0 标准化审计提示词
- 执行端：Codex
- 输入 SHA-256：`8c1e4a267b57d6058c978a06881cc0a14e3923df66de45808609e301a724cfb0`
- 解释器：`tools/venv-openjarvis/Scripts/python.exe`，Python 3.13.16

## 范围与结论

新增独立审计提示词、fail-closed 加载器、严格 JSON 适配器与单测。LLM
输出只使用既有 `blocker/major/minor`，并通过 `IndependentReviewer.gate()`
生成 `ReviewResult`；没有改动 `reviewer.py` 的角色、分级或交付门语义。

阶段结论：PASS。

## RED / GREEN 证据

- RED：`python -X utf8 -m unittest src.brain.guardrails.tests.test_audit_prompt -v`
  返回 exit 1，10 个测试因 `audit_prompt` 入口尚不存在而失败。完整输出：
  `tasks/queue/runs/wo-ultimaagent-20261108-0026/T0/red-test.log`。
- GREEN：同一命令返回 exit 0，10/10 通过。完整输出：
  `tasks/queue/runs/wo-ultimaagent-20261108-0026/T0/green-test.log`。
- 既有语义回归：新测试与 `test_audit_s3` 合跑，exit 0，28/28 通过。
  完整输出：
  `tasks/queue/runs/wo-ultimaagent-20261108-0026/T0/focused-regression.log`。

## 验收映射

- 独立角色：仅 `eng.audit` / `eng.security` 可加载与解析；`dev` 被拒。
- 证据纪律与固定输出：`independent-auditor.md` 规定只基于证据和严格
  `findings[severity/item/detail] + gate` JSON。
- fail-closed：缺失、空文件、非法 JSON、额外/重复字段、非法分级、gate
  冲突均拒绝。
- 既有 gate 复用：解析结果经 `IndependentReviewer` 生成 `ReviewResult`；
  LLM 声明 gate 与确定性 blocker 计算不一致时拒绝。

## 开源优先与越界声明

未新增依赖。JSON 解析与文件加载使用 Python 标准库，分级与交付门直接复用
现有 reviewer；引入模板引擎或第三方 JSON Schema 校验库只会扩大依赖面，
对本阶段固定小契约无收益。未改生产模型、推理参数、KWS/唤醒词基线、
daemon 或 0016/0017 冻结语义，未触碰其他在途改动。
