# 工单 0026 审计加固 T2 与收口报告

- 工单：`wo-ultimaagent-20261108-0026`
- 阶段：T2 闭环测试、失败 case 归档与全量工程门
- 执行端：Codex
- 输入 SHA-256：`8c1e4a267b57d6058c978a06881cc0a14e3923df66de45808609e301a724cfb0`
- 解释器：`tools/venv-openjarvis/Scripts/python.exe`，Python 3.13.16

## 范围与结论

新增离线端到端闭环测试，真实串联确定性护栏、LangGraph 状态机、结构化回答
解析/校验、审计轨迹和四字段回执；外部模型请求仅在测试边界注入归档载荷。
建立失败 case 目录约定，并让 grounded=false 回归测试实际读取归档样例。

阶段结论：PASS。最终完整工程门为 1001 passed、0 failed、122 subtests
passed、36 warnings，exit 0；JUnit 合计 1123 tests，failures/errors/skipped
均为 0。

## T2 RED / GREEN 证据

- RED：`python -X utf8 -m unittest src.brain.tests.test_closed_loop_audit -v`
  返回 exit 1，5 个用例中 2 个失败。预期失败为 grounded=false 归档尚缺；
  另一个失败定位为测试用离线 embedding 未把“点个赞”识别为营销原型，导致
  正常回复被误判 `banned_semantic`。补齐测试替身词表后，正常闭环单测复测通过。
  完整输出：`tasks/queue/runs/wo-ultimaagent-20261108-0026/T2/red-test.log`。
- GREEN：同一闭环命令返回 exit 0，5/5 通过且无警告。完整输出：
  `tasks/queue/runs/wo-ultimaagent-20261108-0026/T2/green-test.log`。
- T0/T1/T2 与既有审计回归合跑：exit 0，38/38 通过。完整输出：
  `tasks/queue/runs/wo-ultimaagent-20261108-0026/T2/focused-regression.log`。

## 闭环覆盖

- 正常闭环：安全输入→护栏→工具证据→结构化回答→真实性/置信度校验→
  ReviewResult→5 条状态转换审计→ReceiptValidator 四字段校验。
- 注入拦截：注入文本在 guard 节点进入 error，后续节点未执行，审计记录
  `completed,error`。
- grounded=false：读取归档 case，生产真实性门拒绝；离线重答仍不 grounded
  后返回固定兜底，`degraded=true`。
- error/hold 回滚：保留已产生的 checkpoint/partial 输出，后续节点均未执行，
  最终审计分别记录 error/hold。

## 失败 case 归档

- 总约定：`data/evidence/failed-cases/README.md`
- 样例：`data/evidence/failed-cases/grounded-false-fallback-20261108/`
- 复测入口：
  `tools/venv-openjarvis/Scripts/python.exe -X utf8 -m unittest src.brain.tests.test_closed_loop_audit.TestClosedLoopAudit.test_grounded_false_archived_case_falls_back_offline -v`

## 完整工程门与失败历史

最终命令：

```powershell
tools\venv-openjarvis\Scripts\python.exe -X utf8 -m pytest src -q --disable-warnings --junitxml=<T2/full-engineering-gate.xml>
```

1. 首次命令组装错误：PowerShell 未展开内联 `Join-Path`，pytest 未运行测试，
   exit 4；日志保留为 `full-engineering-gate-attempt1-invocation-error.log`。
2. 首次真实全量：1000 passed、1 failed、122 subtests，exit 1；唯一失败为
   `TestC2Entry.test_jarvis_ask_real_inference` 的 `jarvis.exe ask` 返回 1。
3. 同一 Jarvis 命令原样诊断返回 `345`、exit 0；原失败测试定点复跑
   1/1 通过。
4. 最终重新执行完整全量：1001 passed、0 failed、122 subtests、36 warnings，
   exit 0，213.88 秒。独立 JUnit 回读为 1123 tests、0 failures、0 errors、
   0 skipped。最终 XML SHA-256：
   `4aaefe749610d12f2cc8a2ac2ebac8619fc74175f3f1ab85c4bfa9359834dd99`。

最终证据：`full-engineering-gate.log`、`full-engineering-gate.xml`、
`full-engineering-gate-readback.json`。失败尝试与定点复测均保留在同一 T2
证据目录，不以最终绿覆盖历史。

## 开源优先、越界与环境声明

未新增依赖。闭环测试复用 unittest、`unittest.mock`、tempfile、现有
LangGraph/guardrails/reply/receipt 组件；失败归档使用 JSON/Markdown。
未重启语音或 daemon，未改主脑模型/推理参数、生产默认行为、KWS/唤醒词
基线及 0016/0017 冻结语义；未暂存、回滚、stash 或覆盖其他在途改动。
T2 新增闭环测试本身不访问外网或真实模型；完整工程门按现有套件执行了本地
Jarvis 真实推理连通性测试。
